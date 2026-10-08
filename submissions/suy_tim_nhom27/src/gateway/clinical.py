from __future__ import annotations

from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Any, Callable, Literal
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import AwareDatetime, BaseModel, ConfigDict, Field


class _Input(BaseModel):
    model_config = ConfigDict(extra="forbid")


class CaseCreate(_Input):
    synthetic_code: str | None = Field(default=None, pattern=r"^SYN-[A-Z0-9-]{1,24}$")
    age: int = Field(ge=0, le=120)
    sex: Literal["male", "female", "unknown"]


class CaseOut(_Input):
    id: UUID
    synthetic_code: str
    age: int
    sex: Literal["male", "female", "unknown"]
    owner_id: UUID
    revision: int


class EncounterCreate(_Input):
    occurred_at: AwareDatetime


class EncounterOut(_Input):
    id: UUID
    case_id: UUID
    occurred_at: AwareDatetime


class ObservationWrite(_Input):
    code: str = Field(min_length=1, max_length=60, pattern=r"^[a-z][a-z0-9_]*$")
    value: Any = None
    unit: str | None = Field(default=None, max_length=40)
    status: Literal["present", "not_measured", "unknown"]
    observed_at: AwareDatetime
    source: Literal["manual_synthetic", "mock_his", "mock_lis", "mock_pacs", "mock_emr"]


class ObservationOut(_Input):
    id: UUID
    encounter_id: UUID
    code: str
    value: Any = None
    unit: str | None = None
    status: Literal["present", "not_measured", "unknown"]
    observed_at: AwareDatetime
    source: Literal["manual_synthetic", "mock_his", "mock_lis", "mock_pacs", "mock_emr"]


def _scope_for(actor: Any) -> str:
    role = getattr(actor, "role", None)
    if role == "doctor":
        return "clinical"
    if role == "nurse":
        return "nursing"
    raise HTTPException(status_code=403, detail="Vai trò không có quyền xem dữ liệu lâm sàng")


def _case_out(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": row["id"],
        "synthetic_code": row["synthetic_code"],
        "age": row["age"],
        "sex": row["sex"],
        "owner_id": row["owner_id"],
        "revision": row["revision"],
    }


def _encounter_out(row: dict[str, Any]) -> dict[str, Any]:
    return {"id": row["id"], "case_id": row["case_id"], "occurred_at": row["occurred_at"]}


def _observation_out(row: dict[str, Any], value_kind: str, unit: str | None) -> dict[str, Any]:
    value: Any = None
    if row["status"] == "present":
        if value_kind == "number":
            number = row["value_number"]
            value = float(number) if number is not None else None
        elif value_kind == "boolean":
            value = row["value_boolean"]
        else:
            value = row["value_text"]
    return {
        "id": row["id"],
        "encounter_id": row["encounter_id"],
        "code": row["code"],
        "value": value,
        "unit": unit,
        "status": row["status"],
        "observed_at": row["observed_at"],
        "source": row["source"],
    }


def _validate_observation(body: ObservationWrite, catalog: dict[str, Any]) -> tuple[Decimal | None, bool | None, str | None]:
    if body.status != "present":
        if body.value is not None or body.unit is not None:
            raise HTTPException(status_code=422, detail="Chỉ số chưa đo phải có value và unit là null")
        return None, None, None

    kind = catalog["value_kind"]
    if kind == "number":
        if isinstance(body.value, bool) or not isinstance(body.value, (int, float, Decimal)):
            raise HTTPException(status_code=422, detail="Mã chỉ số này cần giá trị số")
        try:
            number = Decimal(str(body.value))
        except (InvalidOperation, ValueError):
            raise HTTPException(status_code=422, detail="Giá trị số không hợp lệ") from None
        if not number.is_finite():
            raise HTTPException(status_code=422, detail="Giá trị số không hữu hạn")
        if body.unit != catalog["unit"]:
            raise HTTPException(status_code=422, detail="Đơn vị không khớp với danh mục chỉ số")
        minimum = catalog["min_value"]
        maximum = catalog["max_value"]
        if minimum is not None and number < Decimal(str(minimum)):
            raise HTTPException(status_code=422, detail="Giá trị nằm ngoài miền biểu diễn của chỉ số")
        if maximum is not None and number > Decimal(str(maximum)):
            raise HTTPException(status_code=422, detail="Giá trị nằm ngoài miền biểu diễn của chỉ số")
        return number, None, None

    if body.unit is not None:
        raise HTTPException(status_code=422, detail="Mã chỉ số này không dùng đơn vị")
    if kind == "boolean":
        if type(body.value) is not bool:
            raise HTTPException(status_code=422, detail="Mã chỉ số này cần giá trị đúng/sai")
        return None, body.value, None
    if kind == "text":
        if not isinstance(body.value, str):
            raise HTTPException(status_code=422, detail="Mã chỉ số này cần giá trị văn bản")
        return None, None, body.value
    raise HTTPException(status_code=422, detail="Danh mục mã chỉ số không hợp lệ")


def _catalog_row(conn: Any, code: str) -> dict[str, Any]:
    row = conn.execute(
        """SELECT code, value_kind, unit, min_value, max_value
             FROM observation_type WHERE code = %s""",
        (code,),
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=422, detail="Mã chỉ số không có trong danh mục")
    return row


def _lock_case_revision(conn: Any, case_id: UUID, expected_revision: int) -> None:
    row = conn.execute(
        "SELECT revision FROM patient_case WHERE id = %s FOR UPDATE",
        (case_id,),
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy ca")
    if row["revision"] != expected_revision:
        raise HTTPException(status_code=409, detail="Ca đã thay đổi; hãy tải lại trước khi ghi")


def _write_query(conn: Any, query: str, params: tuple[Any, ...]) -> Any:
    try:
        return conn.execute(query, params)
    except Exception as exc:
        # Do not return raw database diagnostics to the client.
        sqlstate = getattr(exc, "sqlstate", None)
        if sqlstate == "23505":
            raise HTTPException(status_code=409, detail="Dữ liệu đã tồn tại") from None
        if sqlstate in {"23503", "23514", "22P02", "22003", "22007"}:
            raise HTTPException(status_code=422, detail="Dữ liệu không hợp lệ") from None
        raise


def build_clinical_router(
    *,
    actor_dependency: Callable[..., Any] | None = None,
    connection_provider: Callable[..., Any] | None = None,
    case_access_checker: Callable[..., Any] | None = None,
) -> APIRouter:
    """Create the SQL-backed clinical router; optional collaborators support isolated API tests."""
    if actor_dependency is None or connection_provider is None or case_access_checker is None:
        from .authorization import get_current_actor, require_case_access
        from .database import staff_connection

        actor_dependency = actor_dependency or get_current_actor
        connection_provider = connection_provider or staff_connection
        case_access_checker = case_access_checker or require_case_access

    router = APIRouter(prefix="/api/v1")

    @router.get("/cases", response_model=list[CaseOut], tags=["Cases"])
    def list_cases(request: Request, actor: Any = Depends(actor_dependency)):
        scope = _scope_for(actor)
        user_id = actor.user_id
        with connection_provider(request, actor) as conn:
            if scope == "clinical":
                rows = conn.execute(
                    """SELECT c.id, c.synthetic_code, c.age, c.sex, c.owner_id, c.revision
                         FROM patient_case c
                        WHERE c.owner_id = %s OR EXISTS (
                          SELECT 1 FROM case_access ca
                           WHERE ca.case_id = c.id AND ca.user_id = %s AND ca.access_scope = %s
                        )
                        ORDER BY c.synthetic_code""",
                    (user_id, user_id, scope),
                ).fetchall()
            else:
                rows = conn.execute(
                    """SELECT c.id, c.synthetic_code, c.age, c.sex, c.owner_id, c.revision
                         FROM patient_case c
                        WHERE EXISTS (
                          SELECT 1 FROM case_access ca
                           WHERE ca.case_id = c.id AND ca.user_id = %s AND ca.access_scope = %s
                        )
                        ORDER BY c.synthetic_code""",
                    (user_id, scope),
                ).fetchall()
        return [_case_out(row) for row in rows]

    @router.post("/cases", response_model=CaseOut, status_code=201, tags=["Cases"])
    def create_case(body: CaseCreate, request: Request, actor: Any = Depends(actor_dependency)):
        if getattr(actor, "role", None) != "doctor":
            raise HTTPException(status_code=403, detail="Chỉ bác sĩ được tạo hồ sơ ca")
        code = body.synthetic_code or f"SYN-{uuid4().hex[:20].upper()}"
        with connection_provider(request, actor) as conn:
            row = _write_query(
                conn,
                """INSERT INTO patient_case (synthetic_code, age, sex, owner_id)
                   VALUES (%s, %s, %s, %s)
                   ON CONFLICT (synthetic_code) DO NOTHING
                   RETURNING id, synthetic_code, age, sex, owner_id, revision""",
                (code, body.age, body.sex, actor.user_id),
            ).fetchone()
            if row is None:
                raise HTTPException(status_code=409, detail="Mã ca đã tồn tại")
        return _case_out(row)

    @router.get("/cases/{case_id}", response_model=CaseOut, tags=["Cases"])
    def get_case(case_id: UUID, request: Request, actor: Any = Depends(actor_dependency)):
        scope = _scope_for(actor)
        with connection_provider(request, actor) as conn:
            case_access_checker(conn, actor, case_id, [scope])
            row = conn.execute(
                """SELECT id, synthetic_code, age, sex, owner_id, revision
                     FROM patient_case WHERE id = %s""",
                (case_id,),
            ).fetchone()
            if row is None:
                raise HTTPException(status_code=404, detail="Không tìm thấy ca")
        return _case_out(row)

    @router.get("/cases/{case_id}/encounters", response_model=list[EncounterOut], tags=["Cases"])
    def list_encounters(case_id: UUID, request: Request, actor: Any = Depends(actor_dependency)):
        scope = _scope_for(actor)
        with connection_provider(request, actor) as conn:
            case_access_checker(conn, actor, case_id, [scope])
            rows = conn.execute(
                """SELECT id, case_id, occurred_at
                     FROM encounter WHERE case_id = %s
                    ORDER BY occurred_at DESC, id""",
                (case_id,),
            ).fetchall()
        return [_encounter_out(row) for row in rows]

    @router.post("/cases/{case_id}/encounters", response_model=EncounterOut, status_code=201, tags=["Cases"])
    def create_encounter(
        case_id: UUID,
        body: EncounterCreate,
        request: Request,
        expected_revision: int = Query(ge=1),
        actor: Any = Depends(actor_dependency),
    ):
        if getattr(actor, "role", None) != "doctor":
            raise HTTPException(status_code=403, detail="Chỉ bác sĩ được tạo lượt khám")
        scope = _scope_for(actor)
        with connection_provider(request, actor) as conn:
            case_access_checker(conn, actor, case_id, [scope])
            _lock_case_revision(conn, case_id, expected_revision)
            staff = conn.execute(
                "SELECT department_code FROM app_user WHERE id = %s AND active",
                (actor.user_id,),
            ).fetchone()
            if staff is None or not staff["department_code"]:
                raise HTTPException(status_code=422, detail="Tài khoản bác sĩ chưa được gán khoa")
            row = _write_query(
                conn,
                """INSERT INTO encounter (case_id, occurred_at, department_code, doctor_id)
                   VALUES (%s, %s, %s, %s)
                   RETURNING id, case_id, occurred_at""",
                (case_id, body.occurred_at, staff["department_code"], actor.user_id),
            ).fetchone()
        return _encounter_out(row)

    @router.get("/encounters/{encounter_id}", response_model=EncounterOut, tags=["Cases"])
    def get_encounter(encounter_id: UUID, request: Request, actor: Any = Depends(actor_dependency)):
        scope = _scope_for(actor)
        with connection_provider(request, actor) as conn:
            parent = conn.execute(
                "SELECT case_id FROM encounter WHERE id = %s",
                (encounter_id,),
            ).fetchone()
            if parent is None:
                raise HTTPException(status_code=404, detail="Không tìm thấy lượt khám")
            case_access_checker(conn, actor, parent["case_id"], [scope])
            row = conn.execute(
                "SELECT id, case_id, occurred_at FROM encounter WHERE id = %s AND case_id = %s",
                (encounter_id, parent["case_id"]),
            ).fetchone()
            if row is None:
                raise HTTPException(status_code=404, detail="Không tìm thấy lượt khám")
        return _encounter_out(row)

    @router.get(
        "/encounters/{encounter_id}/observations",
        response_model=list[ObservationOut],
        tags=["Clinical data"],
    )
    def list_observations(encounter_id: UUID, request: Request, actor: Any = Depends(actor_dependency)):
        scope = _scope_for(actor)
        with connection_provider(request, actor) as conn:
            parent = conn.execute(
                "SELECT case_id FROM encounter WHERE id = %s",
                (encounter_id,),
            ).fetchone()
            if parent is None:
                raise HTTPException(status_code=404, detail="Không tìm thấy lượt khám")
            case_access_checker(conn, actor, parent["case_id"], [scope])
            rows = conn.execute(
                """SELECT o.id, o.encounter_id, o.code, o.value_number, o.value_boolean,
                          o.value_text, o.status, o.observed_at, o.source,
                          t.value_kind, t.unit
                     FROM observation o
                     JOIN observation_type t ON t.code = o.code
                    WHERE o.encounter_id = %s
                    ORDER BY o.observed_at DESC, o.id""",
                (encounter_id,),
            ).fetchall()
        return [_observation_out(row, row["value_kind"], row["unit"]) for row in rows]

    @router.post(
        "/encounters/{encounter_id}/observations",
        response_model=ObservationOut,
        status_code=201,
        tags=["Clinical data"],
    )
    def create_observation(
        encounter_id: UUID,
        body: ObservationWrite,
        request: Request,
        expected_revision: int = Query(ge=1),
        actor: Any = Depends(actor_dependency),
    ):
        scope = _scope_for(actor)
        with connection_provider(request, actor) as conn:
            parent = conn.execute(
                "SELECT case_id FROM encounter WHERE id = %s",
                (encounter_id,),
            ).fetchone()
            if parent is None:
                raise HTTPException(status_code=404, detail="Không tìm thấy lượt khám")
            case_id = parent["case_id"]
            case_access_checker(conn, actor, case_id, [scope])
            _lock_case_revision(conn, case_id, expected_revision)
            encounter = conn.execute(
                "SELECT id FROM encounter WHERE id = %s AND case_id = %s",
                (encounter_id, case_id),
            ).fetchone()
            if encounter is None:
                raise HTTPException(status_code=404, detail="Không tìm thấy lượt khám trong ca")
            catalog = _catalog_row(conn, body.code)
            number, boolean, text = _validate_observation(body, catalog)
            row = _write_query(
                conn,
                """INSERT INTO observation
                     (encounter_id, code, value_number, value_boolean, value_text,
                      status, observed_at, source, recorded_by)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                   RETURNING id, encounter_id, code, value_number, value_boolean,
                             value_text, status, observed_at, source""",
                (
                    encounter_id,
                    body.code,
                    number,
                    boolean,
                    text,
                    body.status,
                    body.observed_at,
                    body.source,
                    actor.user_id,
                ),
            ).fetchone()
        return _observation_out(row, catalog["value_kind"], catalog["unit"])

    @router.put(
        "/cases/{case_id}/encounters/{encounter_id}/observations/{observation_id}",
        response_model=ObservationOut,
        tags=["Clinical data"],
    )
    def update_observation(
        case_id: UUID,
        encounter_id: UUID,
        observation_id: UUID,
        body: ObservationWrite,
        request: Request,
        expected_revision: int = Query(ge=1),
        actor: Any = Depends(actor_dependency),
    ):
        scope = _scope_for(actor)
        with connection_provider(request, actor) as conn:
            case_access_checker(conn, actor, case_id, [scope])
            _lock_case_revision(conn, case_id, expected_revision)
            existing = conn.execute(
                """SELECT o.id
                     FROM observation o
                     JOIN encounter e ON e.id = o.encounter_id
                    WHERE o.id = %s AND o.encounter_id = %s AND e.case_id = %s
                    FOR UPDATE OF o""",
                (observation_id, encounter_id, case_id),
            ).fetchone()
            if existing is None:
                raise HTTPException(status_code=404, detail="Không tìm thấy chỉ số trong lượt khám của ca")
            catalog = _catalog_row(conn, body.code)
            number, boolean, text = _validate_observation(body, catalog)
            row = _write_query(
                conn,
                """UPDATE observation
                      SET code = %s, value_number = %s, value_boolean = %s, value_text = %s,
                          status = %s, observed_at = %s, source = %s, recorded_by = %s
                    WHERE id = %s AND encounter_id = %s
                    RETURNING id, encounter_id, code, value_number, value_boolean,
                              value_text, status, observed_at, source""",
                (
                    body.code,
                    number,
                    boolean,
                    text,
                    body.status,
                    body.observed_at,
                    body.source,
                    actor.user_id,
                    observation_id,
                    encounter_id,
                ),
            ).fetchone()
            if row is None:
                raise HTTPException(status_code=404, detail="Không tìm thấy chỉ số")
        return _observation_out(row, catalog["value_kind"], catalog["unit"])

    return router
