"""Database-backed stub evaluations, rule workflow, and audit reads.

The demo deliberately does not evaluate clinical criteria. Rule content is
versioned and its schema/hash workflow can be exercised, while every evaluation
module remains ``mock_not_evaluated`` and has no recommendations.
"""
from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from psycopg import Error as PsycopgError

from ..authorization import (
    Actor,
    get_current_actor,
    require_case_access,
    require_permission,
    require_role,
)
from ..database import staff_connection

ModuleName = Literal["diagnosis", "lab_test", "treatment", "medsafety"]
STUB_RULE_VERSION = "STUB-0.1"
STUB_MESSAGE = "Chưa thực hiện đánh giá lâm sàng; dữ liệu này chỉ dùng cho demo."


class ApiModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class EvaluationCreate(ApiModel):
    encounter_id: UUID
    expected_revision: int = Field(ge=1)
    modules: list[ModuleName] = Field(min_length=1, max_length=4)

    @model_validator(mode="after")
    def unique_modules(self) -> "EvaluationCreate":
        if len(self.modules) != len(set(self.modules)):
            raise ValueError("Duplicate module")
        return self


class DecisionCreate(ApiModel):
    action: Literal["accepted", "adjusted", "rejected"]
    reason: str | None = Field(default=None, max_length=500)
    adjustment_details: dict[str, Any] | None = None

    @model_validator(mode="after")
    def validate_decision(self) -> "DecisionCreate":
        if self.action in {"adjusted", "rejected"} and not (self.reason and self.reason.strip()):
            raise ValueError("Reason required for adjusted/rejected")
        if self.action == "adjusted":
            if not self.adjustment_details:
                raise ValueError("adjusted requires non-empty adjustment_details")
        elif self.adjustment_details is not None:
            raise ValueError("adjustment_details is only valid for adjusted")
        return self


class RuleCreate(ApiModel):
    code: str = Field(pattern=r"^[A-Z][A-Z0-9_-]{2,59}$")
    module: ModuleName
    source_ref: str = Field(min_length=1, max_length=300)
    content: dict[str, Any] = Field(default_factory=dict)
    required_fields: list[str] = Field(default_factory=list, max_length=100)

    @field_validator("source_ref")
    @classmethod
    def nonblank_source(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("source_ref must not be blank")
        return value

    @field_validator("content")
    @classmethod
    def json_object_only(cls, value: dict[str, Any]) -> dict[str, Any]:
        try:
            json.dumps(value, ensure_ascii=False, allow_nan=False)
        except (TypeError, ValueError):
            raise ValueError("content must be a JSON object") from None
        return value

    @field_validator("required_fields")
    @classmethod
    def unique_required_fields(cls, value: list[str]) -> list[str]:
        if len(value) != len(set(value)):
            raise ValueError("Duplicate required field")
        if any(not field or len(field) > 60 for field in value):
            raise ValueError("Invalid required field")
        return value


class RuleApproval(ApiModel):
    approval_ref: str = Field(min_length=1, max_length=300)
    expected_content_hash: str = Field(pattern=r"^[a-f0-9]{64}$")

    @field_validator("approval_ref")
    @classmethod
    def nonblank_approval_ref(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("approval_ref must not be blank")
        return value


class ModuleResultOut(ApiModel):
    module: ModuleName
    status: Literal["mock_not_evaluated"] = "mock_not_evaluated"
    message: str = STUB_MESSAGE
    missing_fields: list[str] = Field(default_factory=list)
    clinical_recommendations: list[Any] = Field(default_factory=list)
    phenotype: None = None
    stage: None = None
    course: None = None
    suggested_tests: list[Any] = Field(default_factory=list)
    treatment_strategies: list[str] = Field(default_factory=list)


class EvaluationOut(ApiModel):
    id: UUID
    case_id: UUID
    encounter_id: UUID
    input_revision: int
    rule_version: str = STUB_RULE_VERSION
    mode: Literal["stub"] = "stub"
    results: list[ModuleResultOut]
    created_at: datetime


class DecisionOut(ApiModel):
    id: UUID
    evaluation_id: UUID
    doctor_id: UUID
    action: Literal["accepted", "adjusted", "rejected"]
    reason: str | None
    adjustment_details: dict[str, Any] | None
    created_at: datetime
    mode: Literal["stub"] = "stub"


class RuleOut(ApiModel):
    id: UUID
    code: str
    version: int
    module: ModuleName
    source_ref: str
    content_hash: str
    content: dict[str, Any]
    required_fields: list[str]
    status: Literal["draft", "tested", "approved", "active", "retired"]
    test_status: Literal["not_run", "schema_passed"]
    approval_ref: str | None


class RuleTestOut(ApiModel):
    rule_id: UUID
    content_hash: str
    result: Literal["schema_passed"] = "schema_passed"
    clinical_validation: Literal["not_performed"] = "not_performed"


class AuditEventOut(ApiModel):
    id: UUID
    actor_id: UUID | None
    actor_kind: Literal["user", "system"]
    action: str
    entity_type: str
    entity_id: UUID
    created_at: datetime


def _db_failure(error: PsycopgError, *, conflict: str = "Dữ liệu xung đột với trạng thái hiện tại") -> HTTPException:
    """Translate database errors into safe API messages without exposing SQL."""
    state = getattr(error, "sqlstate", None)
    primary = getattr(getattr(error, "diag", None), "message_primary", "") or ""
    message = primary.lower()
    if state == "23505":
        return HTTPException(status_code=409, detail=conflict)
    if state in {"23503", "23514", "P0001"}:
        if "stale evaluation" in message or "stale" in message:
            return HTTPException(status_code=409, detail="Đánh giá đã cũ; hãy đánh giá lại")
        if "access" in message or "doctor clinical" in message:
            return HTTPException(status_code=403, detail="Không có quyền truy cập dữ liệu")
        return HTTPException(status_code=409, detail=conflict)
    if state and state.startswith("08"):
        return HTTPException(status_code=503, detail="Cơ sở dữ liệu demo tạm thời không sẵn sàng")
    return HTTPException(status_code=500, detail="Không thể hoàn tất thao tác với dữ liệu demo")


def _rule_out(row: dict[str, Any]) -> RuleOut:
    required_fields = row.get("required_fields") or []
    status = row["status"]
    return RuleOut(
        id=row["id"],
        code=row["code"],
        version=row["version"],
        module=row["module"],
        source_ref=row["source_ref"],
        content_hash=row["content_hash"],
        content=row["content"] or {},
        required_fields=list(required_fields),
        status=status,
        test_status="not_run" if status == "draft" else "schema_passed",
        approval_ref=row.get("approval_ref"),
    )


def _evaluation_result(row: dict[str, Any], modules: list[str]) -> EvaluationOut:
    # Never copy recommendations, diagnoses, or other clinical results from SQL.
    # The route itself only persists stub rows; this response stays fail-closed if
    # an unrelated writer has left unexpected child rows behind.
    return EvaluationOut(
        id=row["id"],
        case_id=row["case_id"],
        encounter_id=row["encounter_id"],
        input_revision=row["input_revision"],
        created_at=row["created_at"],
        results=[ModuleResultOut(module=module) for module in modules],
    )


def _evaluation_header(conn: Any, evaluation_id: UUID, *, lock_case: bool = False) -> dict[str, Any] | None:
    lock_clause = " FOR UPDATE OF c" if lock_case else ""
    return conn.execute(
        """
        SELECT v.id, v.encounter_id, v.input_revision, v.requested_by, v.mode, v.created_at,
               e.case_id, c.revision AS current_revision
        FROM evaluation AS v
        JOIN encounter AS e ON e.id = v.encounter_id
        JOIN patient_case AS c ON c.id = e.case_id
        WHERE v.id = %s
        """ + lock_clause,
        (evaluation_id,),
    ).fetchone()


def _evaluation_modules(conn: Any, evaluation_id: UUID) -> list[str]:
    rows = conn.execute(
        """
        SELECT m.module, m.status, m.rule_version_id,
               EXISTS (SELECT 1 FROM recommendation AS r WHERE r.module_result_id = m.id) AS has_recommendations,
               EXISTS (SELECT 1 FROM result_missing_field AS f WHERE f.module_result_id = m.id) AS has_missing_fields
        FROM module_result AS m
        WHERE m.evaluation_id = %s
        ORDER BY m.module
        """,
        (evaluation_id,),
    ).fetchall()
    if not rows:
        raise HTTPException(status_code=409, detail="Đánh giá thiếu kết quả module")
    if any(
        row["status"] != "mock_not_evaluated"
        or row["rule_version_id"] is not None
        or row["has_recommendations"]
        or row["has_missing_fields"]
        for row in rows
    ):
        raise HTTPException(status_code=409, detail="Đánh giá chứa kết quả ngoài chế độ stub")
    return [row["module"] for row in rows]


def _load_evaluation(conn: Any, header: dict[str, Any], modules: list[str]) -> EvaluationOut:
    return _evaluation_result(header, modules)


def build_rules_router() -> APIRouter:
    router = APIRouter()

    @router.post("/api/v1/evaluations", response_model=EvaluationOut, status_code=201, tags=["Evaluation"])
    def create_evaluation(
        body: EvaluationCreate,
        request: Request,
        actor: Actor = Depends(get_current_actor),
    ) -> EvaluationOut:
        require_role(actor, {"doctor", "pharmacist"})
        if actor.role == "pharmacist" and any(module != "medsafety" for module in body.modules):
            raise HTTPException(status_code=403, detail="Dược sĩ chỉ được gọi module MedSafety")
        scope = "clinical" if actor.role == "doctor" else "medsafety"

        try:
            with staff_connection(request, actor) as conn:
                encounter = conn.execute(
                    """
                    SELECT e.id, e.case_id, e.status, e.occurred_at, c.revision
                    FROM encounter AS e
                    JOIN patient_case AS c ON c.id = e.case_id
                    WHERE e.id = %s
                    FOR UPDATE OF c
                    """,
                    (body.encounter_id,),
                ).fetchone()
                if encounter is None:
                    raise HTTPException(status_code=404, detail="Không tìm thấy lượt khám")
                require_case_access(conn, actor, encounter["case_id"], {scope})
                if encounter["status"] == "cancelled":
                    raise HTTPException(status_code=409, detail="Không thể đánh giá lượt khám đã hủy")
                if encounter["revision"] != body.expected_revision:
                    raise HTTPException(status_code=409, detail="Dữ liệu đã thay đổi; hãy tải lại trước khi đánh giá")

                observations = conn.execute(
                    """
                    SELECT COALESCE(
                        jsonb_agg(
                            jsonb_build_object(
                                'code', o.code,
                                'value', COALESCE(to_jsonb(o.value_number), to_jsonb(o.value_boolean), to_jsonb(o.value_text)),
                                'status', o.status,
                                'observed_at', o.observed_at,
                                'source', o.source
                            ) ORDER BY o.observed_at, o.id
                        ), '[]'::jsonb
                    ) AS items
                    FROM observation AS o
                    WHERE o.encounter_id = %s
                    """,
                    (body.encounter_id,),
                ).fetchone()["items"]
                medications = conn.execute(
                    """
                    SELECT COALESCE(
                        jsonb_agg(
                            jsonb_build_object(
                                'ingredient_code', m.ingredient_code,
                                'dose', m.dose,
                                'dose_unit', m.dose_unit,
                                'route', m.route,
                                'frequency_per_day', m.frequency_per_day,
                                'kind', m.kind,
                                'starts_on', m.starts_on,
                                'ends_on', m.ends_on
                            ) ORDER BY m.id
                        ), '[]'::jsonb
                    ) AS items
                    FROM medication AS m
                    WHERE m.encounter_id = %s
                    """,
                    (body.encounter_id,),
                ).fetchone()["items"]
                snapshot = {
                    "encounter_id": str(body.encounter_id),
                    "case_id": str(encounter["case_id"]),
                    "input_revision": encounter["revision"],
                    "modules": body.modules,
                    "observations": observations,
                    "medications": medications,
                }
                inserted = conn.execute(
                    """
                    INSERT INTO evaluation(encounter_id, input_revision, input_snapshot, requested_by, mode)
                    VALUES (%s, %s, %s::jsonb, %s, 'stub')
                    RETURNING id, encounter_id, input_revision, created_at
                    """,
                    (
                        body.encounter_id,
                        encounter["revision"],
                        json.dumps(snapshot, ensure_ascii=False, allow_nan=False, default=str),
                        actor.user_id,
                    ),
                ).fetchone()
                for module in body.modules:
                    conn.execute(
                        """
                        INSERT INTO module_result(evaluation_id, module, status, message)
                        VALUES (%s, %s, 'mock_not_evaluated', %s)
                        """,
                        (inserted["id"], module, STUB_MESSAGE),
                    )
                return _evaluation_result(
                    {
                        **inserted,
                        "case_id": encounter["case_id"],
                    },
                    body.modules,
                )
        except HTTPException:
            raise
        except PsycopgError as error:
            raise _db_failure(error, conflict="Không thể tạo đánh giá với trạng thái dữ liệu hiện tại") from None

    @router.get("/api/v1/evaluations/{evaluation_id}", response_model=EvaluationOut, tags=["Evaluation"])
    def get_evaluation(
        evaluation_id: UUID,
        request: Request,
        actor: Actor = Depends(get_current_actor),
    ) -> EvaluationOut:
        require_role(actor, {"doctor", "pharmacist"})
        try:
            with staff_connection(request, actor) as conn:
                header = _evaluation_header(conn, evaluation_id)
                if header is None:
                    raise HTTPException(status_code=404, detail="Không tìm thấy đánh giá")
                if header["mode"] != "stub":
                    raise HTTPException(status_code=409, detail="Không hỗ trợ đọc kết quả ngoài chế độ demo")
                scope = "clinical" if actor.role == "doctor" else "medsafety"
                require_case_access(conn, actor, header["case_id"], {scope})
                modules = _evaluation_modules(conn, evaluation_id)
                if actor.role == "pharmacist" and any(module != "medsafety" for module in modules):
                    raise HTTPException(status_code=403, detail="Dược sĩ chỉ được xem kết quả MedSafety")
                return _load_evaluation(conn, header, modules)
        except HTTPException:
            raise
        except PsycopgError as error:
            raise _db_failure(error) from None

    @router.post(
        "/api/v1/evaluations/{evaluation_id}/decisions",
        response_model=DecisionOut,
        status_code=201,
        tags=["Decision"],
    )
    def create_decision(
        evaluation_id: UUID,
        body: DecisionCreate,
        request: Request,
        actor: Actor = Depends(get_current_actor),
    ) -> DecisionOut:
        require_role(actor, {"doctor"})
        try:
            with staff_connection(request, actor) as conn:
                header = _evaluation_header(conn, evaluation_id, lock_case=True)
                if header is None:
                    raise HTTPException(status_code=404, detail="Không tìm thấy đánh giá")
                require_case_access(conn, actor, header["case_id"], {"clinical"})
                if header["mode"] != "stub":
                    raise HTTPException(status_code=409, detail="Không hỗ trợ quyết định cho đánh giá ngoài chế độ demo")
                if header["input_revision"] != header["current_revision"]:
                    raise HTTPException(status_code=409, detail="Đánh giá đã cũ; hãy đánh giá lại")
                row = conn.execute(
                    """
                    INSERT INTO clinical_decision(
                        evaluation_id, doctor_id, action, reason, adjustment_details
                    )
                    VALUES (%s, %s, %s, %s, %s::jsonb)
                    RETURNING id, evaluation_id, doctor_id, action, reason, adjustment_details, created_at
                    """,
                    (
                        evaluation_id,
                        actor.user_id,
                        body.action,
                        body.reason,
                        json.dumps(body.adjustment_details, ensure_ascii=False, allow_nan=False)
                        if body.adjustment_details is not None
                        else None,
                    ),
                ).fetchone()
                return DecisionOut(**row)
        except HTTPException:
            raise
        except PsycopgError as error:
            raise _db_failure(error, conflict="Đã có quyết định hoặc đánh giá không còn hợp lệ") from None

    @router.get("/api/v1/rule-versions", response_model=list[RuleOut], tags=["Rules"])
    def list_rule_versions(
        request: Request,
        limit: int = Query(default=100, ge=1, le=200),
        actor: Actor = Depends(get_current_actor),
    ) -> list[RuleOut]:
        if actor.role != "admin":
            require_permission(actor, "rule.approve")
        try:
            with staff_connection(request, actor) as conn:
                rows = conn.execute(
                    """
                    SELECT r.id, r.code, r.version, r.module, r.source_ref, r.content_hash,
                           r.content, r.status, a.approval_ref,
                           COALESCE(
                             (SELECT jsonb_agg(f.field_code ORDER BY f.field_code)
                              FROM rule_required_field AS f WHERE f.rule_version_id = r.id),
                             '[]'::jsonb
                           ) AS required_fields
                    FROM rule_version AS r
                    LEFT JOIN rule_approval AS a ON a.rule_version_id = r.id
                    ORDER BY r.code, r.version DESC, r.id
                    LIMIT %s
                    """,
                    (limit,),
                ).fetchall()
                return [_rule_out(row) for row in rows]
        except PsycopgError as error:
            raise _db_failure(error) from None

    @router.post("/api/v1/rule-versions", response_model=RuleOut, status_code=201, tags=["Rules"])
    def create_rule_version(
        body: RuleCreate,
        request: Request,
        actor: Actor = Depends(get_current_actor),
    ) -> RuleOut:
        require_role(actor, {"admin"})
        try:
            content_json = json.dumps(body.content, ensure_ascii=False, allow_nan=False)
            with staff_connection(request, actor) as conn:
                content_hash = conn.execute(
                    "SELECT encode(sha256(convert_to((%s::jsonb)::text, 'UTF8')), 'hex') AS content_hash",
                    (content_json,),
                ).fetchone()["content_hash"]
                version = conn.execute(
                    "SELECT COALESCE(MAX(version), 0) + 1 AS next_version FROM rule_version WHERE code = %s",
                    (body.code,),
                ).fetchone()["next_version"]
                row = conn.execute(
                    """
                    INSERT INTO rule_version(
                        code, version, module, source_ref, content_hash, content, status, created_by
                    )
                    VALUES (%s, %s, %s, %s, %s, %s::jsonb, 'draft', %s)
                    RETURNING id, code, version, module, source_ref, content_hash, content, status
                    """,
                    (
                        body.code,
                        version,
                        body.module,
                        body.source_ref,
                        content_hash,
                        content_json,
                        actor.user_id,
                    ),
                ).fetchone()
                for field_code in body.required_fields:
                    conn.execute(
                        "INSERT INTO rule_required_field(rule_version_id, field_code) VALUES (%s, %s)",
                        (row["id"], field_code),
                    )
                return _rule_out({**row, "required_fields": body.required_fields, "approval_ref": None})
        except HTTPException:
            raise
        except PsycopgError as error:
            raise _db_failure(error, conflict="Phiên bản quy tắc hoặc trường bắt buộc không hợp lệ") from None

    @router.post(
        "/api/v1/rule-versions/{rule_id}/test",
        response_model=RuleTestOut,
        tags=["Rules"],
    )
    def test_rule_version(
        rule_id: UUID,
        request: Request,
        actor: Actor = Depends(get_current_actor),
    ) -> RuleTestOut:
        require_role(actor, {"admin"})
        try:
            with staff_connection(request, actor) as conn:
                row = conn.execute(
                    "SELECT id, status, content_hash FROM rule_version WHERE id = %s FOR UPDATE",
                    (rule_id,),
                ).fetchone()
                if row is None:
                    raise HTTPException(status_code=404, detail="Không tìm thấy quy tắc")
                if row["status"] != "draft":
                    raise HTTPException(status_code=409, detail="Chỉ bản nháp mới được kiểm tra schema")
                invalid_field = conn.execute(
                    """
                    SELECT f.field_code
                    FROM rule_required_field AS f
                    LEFT JOIN observation_type AS o ON o.code = f.field_code
                    WHERE f.rule_version_id = %s AND o.code IS NULL
                    LIMIT 1
                    """,
                    (rule_id,),
                ).fetchone()
                if invalid_field is not None:
                    raise HTTPException(status_code=409, detail="Quy tắc tham chiếu trường không hợp lệ")
                conn.execute("UPDATE rule_version SET status = 'tested' WHERE id = %s", (rule_id,))
                return RuleTestOut(rule_id=row["id"], content_hash=row["content_hash"])
        except HTTPException:
            raise
        except PsycopgError as error:
            raise _db_failure(error, conflict="Không thể kiểm tra quy tắc ở trạng thái hiện tại") from None

    @router.post(
        "/api/v1/rule-versions/{rule_id}/approve",
        response_model=RuleOut,
        tags=["Rules"],
    )
    def approve_rule_version(
        rule_id: UUID,
        body: RuleApproval,
        request: Request,
        actor: Actor = Depends(get_current_actor),
    ) -> RuleOut:
        if actor.role == "admin":
            raise HTTPException(status_code=403, detail="Quản trị viên không được phê duyệt quy tắc")
        require_permission(actor, "rule.approve")
        try:
            with staff_connection(request, actor) as conn:
                row = conn.execute(
                    """
                    SELECT id, code, version, module, source_ref, content_hash, content, status
                    FROM rule_version WHERE id = %s FOR UPDATE
                    """,
                    (rule_id,),
                ).fetchone()
                if row is None:
                    raise HTTPException(status_code=404, detail="Không tìm thấy quy tắc")
                if row["status"] != "tested":
                    raise HTTPException(status_code=409, detail="Chỉ quy tắc đã kiểm tra schema mới được phê duyệt")
                if row["content_hash"] != body.expected_content_hash:
                    raise HTTPException(status_code=409, detail="Hash không khớp với nội dung đã kiểm tra")
                conn.execute(
                    """
                    INSERT INTO rule_approval(
                        rule_version_id, approval_ref, approved_content_hash, approved_at, recorded_by
                    ) VALUES (%s, %s, %s, now(), %s)
                    """,
                    (rule_id, body.approval_ref, row["content_hash"], actor.user_id),
                )
                approved = conn.execute(
                    "UPDATE rule_version SET status = 'approved' WHERE id = %s RETURNING status",
                    (rule_id,),
                ).fetchone()
                fields = conn.execute(
                    "SELECT field_code FROM rule_required_field WHERE rule_version_id = %s ORDER BY field_code",
                    (rule_id,),
                ).fetchall()
                return _rule_out(
                    {
                        **row,
                        "status": approved["status"],
                        "approval_ref": body.approval_ref,
                        "required_fields": [item["field_code"] for item in fields],
                    }
                )
        except HTTPException:
            raise
        except PsycopgError as error:
            raise _db_failure(error, conflict="Quy tắc chưa được phê duyệt hoặc đã thay đổi") from None

    @router.post(
        "/api/v1/rule-versions/{rule_id}/activate",
        response_model=RuleOut,
        tags=["Rules"],
    )
    def activate_rule_version(
        rule_id: UUID,
        request: Request,
        actor: Actor = Depends(get_current_actor),
    ) -> RuleOut:
        require_role(actor, {"admin"})
        try:
            with staff_connection(request, actor) as conn:
                row = conn.execute(
                    """
                    SELECT id, code, version, module, source_ref, content_hash, content, status
                    FROM rule_version WHERE id = %s FOR UPDATE
                    """,
                    (rule_id,),
                ).fetchone()
                if row is None:
                    raise HTTPException(status_code=404, detail="Không tìm thấy quy tắc")
                if row["status"] != "approved":
                    raise HTTPException(status_code=409, detail="Chỉ quy tắc đã được phê duyệt mới được kích hoạt")
                # Replace the active version atomically; the partial unique index
                # guarantees at most one active version for a rule code.
                conn.execute(
                    "SELECT id FROM rule_version WHERE code = %s AND status = 'active' FOR UPDATE",
                    (row["code"],),
                ).fetchall()
                conn.execute(
                    "UPDATE rule_version SET status = 'retired' WHERE code = %s AND status = 'active'",
                    (row["code"],),
                )
                active = conn.execute(
                    "UPDATE rule_version SET status = 'active' WHERE id = %s RETURNING status",
                    (rule_id,),
                ).fetchone()
                approval = conn.execute(
                    "SELECT approval_ref FROM rule_approval WHERE rule_version_id = %s",
                    (rule_id,),
                ).fetchone()
                fields = conn.execute(
                    "SELECT field_code FROM rule_required_field WHERE rule_version_id = %s ORDER BY field_code",
                    (rule_id,),
                ).fetchall()
                return _rule_out(
                    {
                        **row,
                        "status": active["status"],
                        "approval_ref": approval["approval_ref"] if approval else None,
                        "required_fields": [item["field_code"] for item in fields],
                    }
                )
        except HTTPException:
            raise
        except PsycopgError as error:
            raise _db_failure(error, conflict="Chỉ quy tắc đã phê duyệt mới được kích hoạt") from None

    @router.get("/api/v1/audit-events", response_model=list[AuditEventOut], tags=["Audit"])
    def list_audit_events(
        request: Request,
        limit: int = Query(default=50, ge=1, le=200),
        before: datetime | None = Query(default=None),
        actor: Actor = Depends(get_current_actor),
    ) -> list[AuditEventOut]:
        require_role(actor, {"admin"})
        try:
            with staff_connection(request, actor) as conn:
                rows = conn.execute(
                    """
                    SELECT id, actor_id, actor_kind, action, entity_type, entity_id, created_at
                    FROM audit_event
                    WHERE (%s::timestamptz IS NULL OR created_at < %s)
                    ORDER BY created_at DESC, id DESC
                    LIMIT %s
                    """,
                    (before, before, limit),
                ).fetchall()
                return [AuditEventOut(**row) for row in rows]
        except PsycopgError as error:
            raise _db_failure(error) from None

    return router
