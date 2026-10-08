from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
from uuid import UUID, uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.gateway.authorization import Actor, get_current_actor
from src.gateway.routers.rules import build_rules_router


DOCTOR_ID = UUID("00000000-0000-4000-8000-000000000001")
ADMIN_ID = UUID("00000000-0000-4000-8000-000000000004")
PHARMACIST_ID = UUID("00000000-0000-4000-8000-000000000003")
CASE_ID = UUID("10000000-0000-4000-8000-000000000001")
ENCOUNTER_ID = UUID("20000000-0000-4000-8000-000000000001")
NOW = datetime(2026, 10, 8, 12, tzinfo=timezone.utc)


class Cursor:
    def __init__(self, rows=()):
        self.rows = list(rows)

    def fetchone(self):
        return self.rows[0] if self.rows else None

    def fetchall(self):
        return list(self.rows)


class FakeDatabase:
    """Small SQL boundary fake for route/authorization behavior tests."""

    def __init__(self):
        self.case_revision = 4
        self.evaluations = {}
        self.module_results = {}
        self.decisions = {}
        self.rules = {}
        self.approvals = {}
        self.case_access = {(CASE_ID, PHARMACIST_ID, "medsafety")}
        self.sql = []

    @contextmanager
    def connection(self):
        yield self

    def execute(self, sql, params=()):
        normalized = " ".join(sql.lower().split())
        self.sql.append((normalized, params))

        if normalized.startswith("select e.id, e.case_id, e.status, e.occurred_at, c.revision"):
            if params[0] != ENCOUNTER_ID:
                return Cursor()
            return Cursor([{
                "id": ENCOUNTER_ID,
                "case_id": CASE_ID,
                "status": "open",
                "occurred_at": NOW,
                "revision": self.case_revision,
            }])
        if normalized.startswith("select owner_id from patient_case"):
            return Cursor([{"owner_id": DOCTOR_ID}] if params[0] == CASE_ID else [])
        if normalized.startswith("select 1 from case_access"):
            case_id, user_id, scopes = params
            allowed = any(
                case_id == cid and user_id == uid and scope in scopes
                for cid, uid, scope in self.case_access
            )
            return Cursor([{"?column?": 1}] if allowed else [])
        if normalized.startswith("select coalesce(") and " as items" in normalized:
            return Cursor([{"items": []}])
        if normalized.startswith("insert into evaluation("):
            evaluation_id = uuid4()
            encounter_id, revision, snapshot_json, requested_by = params
            self.evaluations[evaluation_id] = {
                "id": evaluation_id,
                "encounter_id": encounter_id,
                "input_revision": revision,
                "requested_by": requested_by,
                "mode": "stub",
                "created_at": NOW,
                "case_id": CASE_ID,
                "snapshot": json.loads(snapshot_json),
            }
            self.module_results[evaluation_id] = []
            return Cursor([{
                "id": evaluation_id,
                "encounter_id": encounter_id,
                "input_revision": revision,
                "created_at": NOW,
            }])
        if normalized.startswith("insert into module_result("):
            evaluation_id, module, _message = params
            self.module_results[evaluation_id].append(module)
            return Cursor()
        if normalized.startswith("select v.id, v.encounter_id, v.input_revision, v.requested_by"):
            evaluation_id = params[0]
            row = self.evaluations.get(evaluation_id)
            if row is None:
                return Cursor()
            return Cursor([{
                key: row[key]
                for key in ("id", "encounter_id", "input_revision", "requested_by", "mode", "created_at", "case_id")
            } | {"current_revision": self.case_revision}])
        if normalized.startswith("select v.id from evaluation as v join encounter as e"):
            return Cursor([
                {"id": row["id"]}
                for row in sorted(self.evaluations.values(), key=lambda item: str(item["id"]))
                if row["case_id"] == params[0] and row["mode"] == "stub"
            ])
        if normalized.startswith("select d.id, d.evaluation_id, d.doctor_id, d.action, d.reason"):
            return Cursor([row for row in self.decisions.values() if row["evaluation_id"] in self.evaluations])
        if normalized.startswith("select id, synthetic_code, age, sex, owner_id, revision from patient_case"):
            return Cursor([{
                "id": CASE_ID, "synthetic_code": "SYN-DEMO-001", "age": 75,
                "sex": "female", "owner_id": DOCTOR_ID, "revision": self.case_revision,
            }] if params[0] == CASE_ID else [])
        if normalized.startswith("select m.module, m.status, m.rule_version_id"):
            return Cursor([{
                "module": module,
                "status": "mock_not_evaluated",
                "rule_version_id": None,
                "has_recommendations": False,
                "has_missing_fields": False,
            } for module in self.module_results.get(params[0], [])])
        if normalized.startswith("insert into clinical_decision("):
            evaluation_id, doctor_id, action, reason, adjustment_json = params
            if evaluation_id in self.decisions:
                raise UniqueViolation()
            decision_id = uuid4()
            row = {
                "id": decision_id,
                "evaluation_id": evaluation_id,
                "doctor_id": doctor_id,
                "action": action,
                "reason": reason,
                "adjustment_details": json.loads(adjustment_json) if adjustment_json else None,
                "created_at": NOW,
            }
            self.decisions[evaluation_id] = row
            return Cursor([row])
        if normalized.startswith("select encode(sha256(convert_to((%s::jsonb)::text"):
            content = json.loads(params[0])
            # The route obtains its hash from PostgreSQL. This fake only supplies
            # a deterministic value so the API can prove it passes the reviewed hash.
            pg_json = json.dumps(content, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            return Cursor([{"content_hash": hashlib.sha256(pg_json.encode()).hexdigest()}])
        if normalized.startswith("select coalesce(max(version), 0) + 1"):
            versions = [row["version"] for row in self.rules.values() if row["code"] == params[0]]
            return Cursor([{"next_version": max(versions, default=0) + 1}])
        if normalized.startswith("insert into rule_version("):
            code, version, module, source_ref, content_hash, content_json, created_by = params
            rule_id = uuid4()
            row = {
                "id": rule_id,
                "code": code,
                "version": version,
                "module": module,
                "source_ref": source_ref,
                "content_hash": content_hash,
                "content": json.loads(content_json),
                "status": "draft",
                "created_by": created_by,
            }
            self.rules[rule_id] = row
            return Cursor([row])
        if normalized.startswith("insert into rule_required_field"):
            rule_id, field_code = params
            self.rules[rule_id].setdefault("required_fields", []).append(field_code)
            return Cursor()
        if normalized.startswith("select id, status, content_hash from rule_version"):
            row = self.rules.get(params[0])
            return Cursor([row] if row else [])
        if normalized.startswith("select f.field_code from rule_required_field"):
            return Cursor()
        if normalized.startswith("update rule_version set status = 'tested'"):
            self.rules[params[0]]["status"] = "tested"
            return Cursor()
        if normalized.startswith("select id, code, version, module, source_ref, content_hash, content, status from rule_version"):
            row = self.rules.get(params[0])
            return Cursor([row] if row else [])
        if normalized.startswith("insert into rule_approval("):
            rule_id, approval_ref, content_hash, recorded_by = params
            row = {
                "approval_ref": approval_ref,
                "approved_content_hash": content_hash,
                "recorded_by": recorded_by,
            }
            self.approvals[rule_id] = row
            return Cursor()
        if normalized.startswith("update rule_version set status = 'approved'"):
            self.rules[params[0]]["status"] = "approved"
            return Cursor([{"status": "approved"}])
        if normalized.startswith("select field_code from rule_required_field"):
            fields = self.rules[params[0]].get("required_fields", [])
            return Cursor([{"field_code": field} for field in fields])
        if normalized.startswith("select id from rule_version where code = %s and status = 'active'"):
            return Cursor([
                {"id": row["id"]}
                for row in self.rules.values()
                if row["code"] == params[0] and row["status"] == "active"
            ])
        if normalized.startswith("update rule_version set status = 'retired'"):
            for row in self.rules.values():
                if row["code"] == params[0] and row["status"] == "active":
                    row["status"] = "retired"
            return Cursor()
        if normalized.startswith("update rule_version set status = 'active'"):
            self.rules[params[0]]["status"] = "active"
            return Cursor([{"status": "active"}])
        if normalized.startswith("select approval_ref from rule_approval"):
            row = self.approvals.get(params[0])
            return Cursor([{"approval_ref": row["approval_ref"]}] if row else [])
        if normalized.startswith("select id, actor_id, actor_kind, action, entity_type, entity_id, created_at from audit_event"):
            return Cursor()
        raise AssertionError(f"Unexpected SQL in fake: {sql}")


class UniqueViolation(Exception):
    sqlstate = "23505"


def make_client(monkeypatch, role="doctor", permissions=(), database=None):
    database = database or FakeDatabase()
    actor_id = {"doctor": DOCTOR_ID, "admin": ADMIN_ID, "pharmacist": PHARMACIST_ID}[role]
    actor = Actor(actor_id, f"{role}_demo", role, frozenset(permissions))
    import src.gateway.routers.rules as rules_module

    monkeypatch.setattr(
        rules_module,
        "staff_connection",
        lambda request, current_actor: request.app.state.fake_database.connection(),
    )
    app = FastAPI()
    app.state.fake_database = database
    app.include_router(build_rules_router())
    app.dependency_overrides[get_current_actor] = lambda: actor
    return TestClient(app), database


def test_evaluation_is_persisted_as_stub_and_pharmacist_scope_is_limited(monkeypatch):
    client, database = make_client(monkeypatch)
    response = client.post("/api/v1/evaluations", json={
        "encounter_id": str(ENCOUNTER_ID),
        "expected_revision": 4,
        "modules": ["diagnosis", "lab_test", "treatment", "medsafety"],
    })
    assert response.status_code == 201
    result = response.json()
    assert result["mode"] == "stub"
    assert {item["status"] for item in result["results"]} == {"mock_not_evaluated"}
    assert all(item["clinical_recommendations"] == [] for item in result["results"])
    assert all(item["phenotype"] is None and item["suggested_tests"] == [] for item in result["results"])
    assert database.module_results[UUID(result["id"])] == ["diagnosis", "lab_test", "treatment", "medsafety"]
    fetched = client.get(f"/api/v1/evaluations/{result['id']}")
    assert fetched.status_code == 200
    assert all(item["clinical_recommendations"] == [] for item in fetched.json()["results"])

    pharmacist_client, _ = make_client(monkeypatch, "pharmacist")
    denied = pharmacist_client.post("/api/v1/evaluations", json={
        "encounter_id": str(ENCOUNTER_ID),
        "expected_revision": 4,
        "modules": ["diagnosis"],
    })
    assert denied.status_code == 403
    allowed = pharmacist_client.post("/api/v1/evaluations", json={
        "encounter_id": str(ENCOUNTER_ID),
        "expected_revision": 4,
        "modules": ["medsafety"],
    })
    assert allowed.status_code == 201


def test_case_history_and_export_are_clinical_scope_only(monkeypatch):
    client, database = make_client(monkeypatch)
    created = client.post("/api/v1/evaluations", json={
        "encounter_id": str(ENCOUNTER_ID), "expected_revision": 4, "modules": ["diagnosis", "medsafety"],
    })
    assert created.status_code == 201
    evaluation_id = UUID(created.json()["id"])
    decision = client.post(f"/api/v1/evaluations/{evaluation_id}/decisions", json={
        "action": "rejected", "reason": "Synthetic demo decision",
    })
    assert decision.status_code == 201

    history = client.get(f"/api/v1/cases/{CASE_ID}/history")
    assert history.status_code == 200
    assert len(history.json()) == 1
    assert {row["module"] for row in history.json()[0]["results"]} == {"diagnosis", "medsafety"}
    export = client.get(f"/api/v1/cases/{CASE_ID}/export")
    assert export.status_code == 200
    assert export.json()["case"]["id"] == str(CASE_ID)
    assert len(export.json()["evaluations"]) == 1
    assert export.json()["decisions"][0]["reason"] == "Synthetic demo decision"

    pharmacist, _ = make_client(monkeypatch, role="pharmacist", database=database)
    assert pharmacist.get(f"/api/v1/cases/{CASE_ID}/history").status_code == 403
    assert pharmacist.get(f"/api/v1/cases/{CASE_ID}/export").status_code == 403


def test_evaluation_rejects_rule_linkage_and_decision_requires_adjustment_details(monkeypatch):
    client, database = make_client(monkeypatch)
    body = {
        "encounter_id": str(ENCOUNTER_ID),
        "expected_revision": 4,
        "modules": ["diagnosis"],
    }
    assert client.post("/api/v1/evaluations", json={**body, "rule_version_id": str(uuid4())}).status_code == 422
    evaluation = client.post("/api/v1/evaluations", json=body).json()
    decision_url = f"/api/v1/evaluations/{evaluation['id']}/decisions"
    assert client.post(decision_url, json={"action": "adjusted", "reason": "adjust"}).status_code == 422
    assert client.post(decision_url, json={
        "action": "adjusted", "reason": "adjust", "adjustment_details": {},
    }).status_code == 422
    adjusted = client.post(decision_url, json={
        "action": "adjusted",
        "reason": "Synthetic workflow adjustment",
        "adjustment_details": {"note": "Demo only"},
    })
    assert adjusted.status_code == 201
    assert adjusted.json()["adjustment_details"] == {"note": "Demo only"}
    assert len(database.decisions) == 1


def test_stale_revision_blocks_decision(monkeypatch):
    client, database = make_client(monkeypatch)
    evaluation = client.post("/api/v1/evaluations", json={
        "encounter_id": str(ENCOUNTER_ID),
        "expected_revision": 4,
        "modules": ["diagnosis"],
    }).json()
    database.case_revision = 5
    response = client.post(
        f"/api/v1/evaluations/{evaluation['id']}/decisions",
        json={"action": "accepted"},
    )
    assert response.status_code == 409
    assert not database.decisions


def test_rule_hash_test_and_approval_require_separate_permission_and_matching_hash(monkeypatch):
    admin, database = make_client(monkeypatch, "admin")
    created = admin.post("/api/v1/rule-versions", json={
        "code": "DEMO_RULE",
        "module": "diagnosis",
        "source_ref": "Synthetic schema fixture",
        "content": {"label": "Demo only"},
        "required_fields": ["ef"],
    })
    assert created.status_code == 201
    rule = created.json()
    assert rule["status"] == "draft"
    assert len(rule["content_hash"]) == 64
    assert admin.post(f"/api/v1/rule-versions/{rule['id']}/test").status_code == 200

    admin_approval = admin.post(f"/api/v1/rule-versions/{rule['id']}/approve", json={
        "approval_ref": "approval-1", "expected_content_hash": rule["content_hash"],
    })
    assert admin_approval.status_code == 403

    no_permission, _ = make_client(monkeypatch, "doctor", database=database)
    assert no_permission.post(f"/api/v1/rule-versions/{rule['id']}/approve", json={
        "approval_ref": "approval-1", "expected_content_hash": rule["content_hash"],
    }).status_code == 403

    approver, _ = make_client(monkeypatch, "doctor", {"rule.approve"}, database=database)
    mismatch = approver.post(f"/api/v1/rule-versions/{rule['id']}/approve", json={
        "approval_ref": "approval-1", "expected_content_hash": "0" * 64,
    })
    assert mismatch.status_code == 409

    approved = approver.post(f"/api/v1/rule-versions/{rule['id']}/approve", json={
        "approval_ref": "approval-1", "expected_content_hash": rule["content_hash"],
    })
    assert approved.status_code == 200
    assert approved.json()["status"] == "approved"
    assert database.approvals[UUID(rule["id"])]["approved_content_hash"] == rule["content_hash"]

    activated = admin.post(f"/api/v1/rule-versions/{rule['id']}/activate")
    assert activated.status_code == 200
    assert activated.json()["status"] == "active"


def test_audit_is_admin_only_and_returns_only_ordered_metadata(monkeypatch):
    client, database = make_client(monkeypatch, "admin")
    assert client.get("/api/v1/audit-events?limit=12").status_code == 200
    query = next(sql for sql, _ in database.sql if sql.startswith("select id, actor_id, actor_kind, action, entity_type"))
    assert "order by created_at desc, id desc" in query
    assert "limit %s" in query

    doctor, _ = make_client(monkeypatch, "doctor")
    assert doctor.get("/api/v1/audit-events").status_code == 403
