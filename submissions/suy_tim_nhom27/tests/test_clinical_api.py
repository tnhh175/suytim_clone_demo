from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from types import SimpleNamespace
from typing import Any
from uuid import UUID

import pytest
from fastapi import FastAPI, HTTPException, Request
from fastapi.testclient import TestClient

from gateway.clinical import build_clinical_router

DOCTOR_A = UUID("00000000-0000-4000-8000-000000000001")
DOCTOR_B = UUID("00000000-0000-4000-8000-000000000002")
NURSE = UUID("00000000-0000-4000-8000-000000000003")
ADMIN = UUID("00000000-0000-4000-8000-000000000004")
CASE_1 = UUID("10000000-0000-4000-8000-000000000001")
CASE_2 = UUID("10000000-0000-4000-8000-000000000002")
CASE_3 = UUID("10000000-0000-4000-8000-000000000003")
ENCOUNTER_1 = UUID("20000000-0000-4000-8000-000000000001")
ENCOUNTER_2 = UUID("20000000-0000-4000-8000-000000000002")
OBS_1 = UUID("30000000-0000-4000-8000-000000000001")
NOW = datetime(2026, 10, 8, 9, tzinfo=timezone.utc)


class Cursor:
    def __init__(self, rows: list[dict[str, Any]]):
        self.rows = rows

    def fetchone(self):
        return self.rows[0] if self.rows else None

    def fetchall(self):
        return self.rows


@dataclass
class Actor:
    user_id: UUID
    role: str


class FakeDatabase:
    """Small DB-API fake that interprets the router's SQL against synthetic rows."""

    def __init__(self):
        self.cases = {
            CASE_1: dict(id=CASE_1, synthetic_code="SYN-CASE-1", age=75, sex="female", owner_id=DOCTOR_A, revision=3),
            CASE_2: dict(id=CASE_2, synthetic_code="SYN-CASE-2", age=80, sex="male", owner_id=DOCTOR_B, revision=2),
            CASE_3: dict(id=CASE_3, synthetic_code="SYN-CASE-3", age=68, sex="unknown", owner_id=DOCTOR_B, revision=1),
        }
        self.case_access = {(CASE_1, NURSE, "nursing"), (CASE_2, DOCTOR_A, "clinical")}
        self.encounters = {
            ENCOUNTER_1: dict(id=ENCOUNTER_1, case_id=CASE_1, occurred_at=NOW),
            ENCOUNTER_2: dict(id=ENCOUNTER_2, case_id=CASE_2, occurred_at=NOW),
        }
        self.observation_types = {
            "systolic_bp": dict(code="systolic_bp", value_kind="number", unit="mmHg", min_value=Decimal("0"), max_value=None),
            "ef": dict(code="ef", value_kind="number", unit="%", min_value=Decimal("0"), max_value=Decimal("100")),
            "dyspnea": dict(code="dyspnea", value_kind="boolean", unit=None, min_value=None, max_value=None),
            "frailty": dict(code="frailty", value_kind="text", unit=None, min_value=None, max_value=None),
        }
        self.notes = []
        self.observations = {
            OBS_1: dict(id=OBS_1, encounter_id=ENCOUNTER_1, code="systolic_bp", value_number=Decimal("120"),
                        value_boolean=None, value_text=None, status="present", observed_at=NOW,
                        source="manual_synthetic", recorded_by=NURSE),
        }
        self.departments = {DOCTOR_A: "cardiology", DOCTOR_B: "geriatrics"}

    def execute(self, sql: str, params: tuple[Any, ...] = ()) -> Cursor:
        statement = " ".join(sql.split()).lower()
        if statement.startswith("select c.id, c.synthetic_code"):
            if "c.owner_id = %s" in statement:
                user_id, assigned_user, scope = params
                rows = [row for row in self.cases.values() if row["owner_id"] == user_id or (row["id"], assigned_user, scope) in self.case_access]
            else:
                user_id, scope = params
                rows = [row for row in self.cases.values() if (row["id"], user_id, scope) in self.case_access]
            return Cursor(sorted(rows, key=lambda row: row["synthetic_code"]))
        if statement.startswith("insert into patient_case"):
            code, age, sex, owner = params
            if any(row["synthetic_code"] == code for row in self.cases.values()):
                return Cursor([])
            row = dict(id=UUID("10000000-0000-4000-8000-000000000004"), synthetic_code=code, age=age, sex=sex, owner_id=owner, revision=1)
            self.cases[row["id"]] = row
            return Cursor([row])
        if statement.startswith("select revision from patient_case"):
            row = self.cases.get(params[0])
            return Cursor([{"revision": row["revision"]}] if row else [])
        if statement.startswith("select id, synthetic_code, age, sex, owner_id, revision from patient_case"):
            row = self.cases.get(params[0])
            return Cursor([row] if row else [])
        if statement.startswith("select department_code from app_user"):
            return Cursor([{"department_code": self.departments[params[0]]}] if params[0] in self.departments else [])
        if statement.startswith("insert into encounter"):
            case_id, occurred_at, department, doctor_id = params
            encounter_id = UUID(f"20000000-0000-4000-8000-{len(self.encounters) + 1:012d}")
            row = dict(id=encounter_id, case_id=case_id, occurred_at=occurred_at)
            self.encounters[encounter_id] = row
            self.cases[case_id]["revision"] += 1
            return Cursor([row])
        if statement.startswith("select case_id from encounter"):
            row = self.encounters.get(params[0])
            return Cursor([{"case_id": row["case_id"]}] if row else [])
        if statement.startswith("select id, case_id, occurred_at from encounter where id = %s and case_id = %s"):
            row = self.encounters.get(params[0])
            return Cursor([row] if row and row["case_id"] == params[1] else [])
        if statement.startswith("select id, case_id, occurred_at from encounter where case_id = %s"):
            rows = [row for row in self.encounters.values() if row["case_id"] == params[0]]
            return Cursor(rows)
        if statement.startswith("select id, case_id, occurred_at from encounter where id = %s"):
            row = self.encounters.get(params[0])
            return Cursor([row] if row else [])
        if statement.startswith("select code, value_kind, unit, min_value, max_value from observation_type"):
            row = self.observation_types.get(params[0])
            return Cursor([row] if row else [])
        if statement.startswith("select id from encounter where id = %s and case_id = %s"):
            row = self.encounters.get(params[0])
            return Cursor([{"id": row["id"]}] if row and row["case_id"] == params[1] else [])
        if statement.startswith("select o.id, o.code from observation o join encounter"):
            observation_id, encounter_id, case_id = params
            row = self.observations.get(observation_id)
            encounter = self.encounters.get(encounter_id)
            return Cursor([{"id": row["id"], "code": row["code"]}] if row and row["encounter_id"] == encounter_id and encounter and encounter["case_id"] == case_id else [])
        if statement.startswith("select id, encounter_id, kind, content, recorded_at from clinical_note"):
            return Cursor([{key: row[key] for key in ("id", "encounter_id", "kind", "content", "recorded_at")}
                           for row in self.notes if row["encounter_id"] == params[0]])
        if statement.startswith("insert into clinical_note"):
            encounter_id, kind, content, recorded_by = params
            note_id = UUID("40000000-0000-4000-8000-%012d" % (len(self.notes) + 1))
            row = dict(id=note_id, encounter_id=encounter_id, kind=kind, content=content, recorded_by=recorded_by, recorded_at=NOW)
            self.notes.append(row)
            case_id = self.encounters[encounter_id]["case_id"]
            self.cases[case_id]["revision"] += 1
            return Cursor([{key: row[key] for key in ("id", "encounter_id", "kind", "content", "recorded_at")}])
        if statement.startswith("select o.id, o.encounter_id, o.code, o.value_number"):
            rows = []
            for row in self.observations.values():
                if row["encounter_id"] == params[0]:
                    rows.append({**row, "value_kind": self.observation_types[row["code"]]["value_kind"],
                                 "unit": self.observation_types[row["code"]]["unit"]})
            return Cursor(rows)
        if statement.startswith("insert into observation"):
            (encounter_id, code, number, boolean, text, status, observed_at, source, recorded_by) = params
            observation_id = UUID(f"30000000-0000-4000-8000-{len(self.observations) + 1:012d}")
            row = dict(id=observation_id, encounter_id=encounter_id, code=code, value_number=number,
                       value_boolean=boolean, value_text=text, status=status, observed_at=observed_at,
                       source=source, recorded_by=recorded_by)
            self.observations[observation_id] = row
            case_id = self.encounters[encounter_id]["case_id"]
            self.cases[case_id]["revision"] += 1
            return Cursor([row])
        if statement.startswith("update observation"):
            (code, number, boolean, text, status, observed_at, source, recorded_by, observation_id, encounter_id) = params
            row = self.observations.get(observation_id)
            if not row or row["encounter_id"] != encounter_id:
                return Cursor([])
            row.update(code=code, value_number=number, value_boolean=boolean, value_text=text, status=status,
                       observed_at=observed_at, source=source, recorded_by=recorded_by)
            case_id = self.encounters[encounter_id]["case_id"]
            self.cases[case_id]["revision"] += 1
            return Cursor([row])
        raise AssertionError(f"Unexpected query in API test: {sql}")


class ApiContext:
    def __init__(self, actor: Actor):
        self.actor = actor
        self.db = FakeDatabase()
        app = FastAPI()
        app.state.actor = actor
        app.state.db = self.db

        def actor_dependency(request: Request):
            return request.app.state.actor

        @contextmanager
        def connection_provider(request: Request, _actor: Actor):
            yield request.app.state.db

        def case_access_checker(conn: FakeDatabase, actor: Actor, case_id: UUID, allowed_scopes: list[str]):
            row = conn.cases.get(case_id)
            if row is None:
                raise HTTPException(status_code=404, detail="Không tìm thấy ca")
            scope = allowed_scopes[0]
            permitted = (
                actor.role == "doctor" and scope == "clinical" and
                (row["owner_id"] == actor.user_id or (case_id, actor.user_id, scope) in conn.case_access)
            ) or (
                actor.role == "nurse" and scope == "nursing" and
                (case_id, actor.user_id, scope) in conn.case_access
            )
            if not permitted:
                raise HTTPException(status_code=403, detail="Không có quyền ca")

        app.include_router(build_clinical_router(
            actor_dependency=actor_dependency,
            connection_provider=connection_provider,
            case_access_checker=case_access_checker,
        ))
        self.client = TestClient(app)


def context(role: str) -> TestContext:
    user_id = {"doctor": DOCTOR_A, "nurse": NURSE, "admin": ADMIN}[role]
    return ApiContext(Actor(user_id, role))


def test_case_and_encounter_access_uses_assigned_scopes():
    doctor = context("doctor")
    listed = doctor.client.get("/api/v1/cases")
    assert listed.status_code == 200
    assert {row["id"] for row in listed.json()} == {str(CASE_1), str(CASE_2)}
    assert doctor.client.get(f"/api/v1/cases/{CASE_2}").status_code == 200
    assert doctor.client.get(f"/api/v1/cases/{CASE_3}").status_code == 403
    assert doctor.client.get(f"/api/v1/encounters/{ENCOUNTER_2}").status_code == 200

    nurse = context("nurse")
    assert {row["id"] for row in nurse.client.get("/api/v1/cases").json()} == {str(CASE_1)}
    assert nurse.client.get(f"/api/v1/cases/{CASE_1}/encounters").status_code == 200
    assert nurse.client.get(f"/api/v1/cases/{CASE_2}").status_code == 403
    assert nurse.client.get(f"/api/v1/encounters/{ENCOUNTER_2}").status_code == 403
    assert nurse.client.get(f"/api/v1/encounters/{UUID(int=999)}").status_code == 404

    admin = context("admin")
    assert admin.client.get("/api/v1/cases").status_code == 403
    assert admin.client.get(f"/api/v1/cases/{CASE_1}").status_code == 403


def test_observation_create_revision_and_case_encounter_isolation():
    nurse = context("nurse")
    payload = {
        "code": "systolic_bp", "value": 118, "unit": "mmHg", "status": "present",
        "observed_at": "2026-10-08T09:10:00Z", "source": "manual_synthetic",
    }
    url = f"/api/v1/encounters/{ENCOUNTER_1}/observations"
    stale = nurse.client.post(url + "?expected_revision=2", json=payload)
    assert stale.status_code == 409
    assert len(nurse.db.observations) == 1

    created = nurse.client.post(url + "?expected_revision=3", json=payload)
    assert created.status_code == 201, created.text
    result = created.json()
    assert result["value"] == 118.0
    assert result["unit"] == "mmHg"
    assert "diagnosis" not in result and "clinical_recommendations" not in result
    assert nurse.db.cases[CASE_1]["revision"] == 4

    # A valid case access does not authorize an observation from another encounter.
    isolated = context("doctor")
    wrong_pair = isolated.client.put(
        f"/api/v1/cases/{CASE_1}/encounters/{ENCOUNTER_2}/observations/{OBS_1}?expected_revision=3",
        json=payload,
    )
    assert wrong_pair.status_code == 404
    assert isolated.client.get(f"/api/v1/encounters/{ENCOUNTER_2}/observations").json() == []


def test_observation_update_checks_revision_and_catalog_type_without_inference():
    nurse = context("nurse")
    url = f"/api/v1/cases/{CASE_1}/encounters/{ENCOUNTER_1}/observations/{OBS_1}"
    payload = {
        "code": "dyspnea", "value": True, "unit": None, "status": "present",
        "observed_at": "2026-10-08T09:15:00Z", "source": "manual_synthetic",
    }
    wrong_unit = {**payload, "code": "systolic_bp", "value": 123, "unit": "kPa"}
    rejected = nurse.client.put(url + "?expected_revision=3", json=wrong_unit)
    assert rejected.status_code == 422
    assert nurse.db.observations[OBS_1]["code"] == "systolic_bp"

    updated = nurse.client.put(url + "?expected_revision=3", json=payload)
    assert updated.status_code == 200, updated.text
    result = updated.json()
    assert result["code"] == "dyspnea" and result["value"] is True
    assert "diagnosis" not in result and "clinical_recommendations" not in result
    assert nurse.db.cases[CASE_1]["revision"] == 4
    stale = nurse.client.put(url + "?expected_revision=3", json=payload)
    assert stale.status_code == 409
    assert len(nurse.db.observations) == 1

    missing = {**payload, "status": "unknown", "value": True}
    assert nurse.client.put(url + "?expected_revision=4", json=missing).status_code == 422
    assert nurse.client.get(f"/api/v1/encounters/{ENCOUNTER_1}/observations").json()[0]["value"] is True


def test_nursing_observation_allowlist_and_scoped_notes():
    nurse = context("nurse")
    outside_nursing = {
        "code": "ef", "value": 55, "unit": "%", "status": "present",
        "observed_at": "2026-10-08T09:10:00Z", "source": "manual_synthetic",
    }
    create_denied = nurse.client.post(
        f"/api/v1/encounters/{ENCOUNTER_1}/observations?expected_revision=3", json=outside_nursing
    )
    assert create_denied.status_code == 403
    assert len(nurse.db.observations) == 1
    update_denied = nurse.client.put(
        f"/api/v1/cases/{CASE_1}/encounters/{ENCOUNTER_1}/observations/{OBS_1}?expected_revision=3",
        json=outside_nursing,
    )
    assert update_denied.status_code == 403
    assert nurse.db.observations[OBS_1]["code"] == "systolic_bp"
    other_id = UUID("30000000-0000-4000-8000-000000000002")
    nurse.db.observations[other_id] = dict(
        id=other_id, encounter_id=ENCOUNTER_1, code="ef", value_number=Decimal("55"),
        value_boolean=None, value_text=None, status="present", observed_at=NOW,
        source="manual_synthetic", recorded_by=DOCTOR_A,
    )
    rewrite_existing = nurse.client.put(
        f"/api/v1/cases/{CASE_1}/encounters/{ENCOUNTER_1}/observations/{other_id}?expected_revision=3",
        json={**outside_nursing, "code": "systolic_bp", "value": 121, "unit": "mmHg"},
    )
    assert rewrite_existing.status_code == 403
    assert nurse.db.observations[other_id]["code"] == "ef"

    exam_as_nurse = nurse.client.post(
        f"/api/v1/encounters/{ENCOUNTER_1}/notes?expected_revision=3",
        json={"kind": "examination", "content": "Ghi nhận chăm sóc"},
    )
    assert exam_as_nurse.status_code == 403
    nursing_note = nurse.client.post(
        f"/api/v1/encounters/{ENCOUNTER_1}/notes?expected_revision=3",
        json={"kind": "nursing", "content": "Theo dõi chăm sóc tổng hợp."},
    )
    assert nursing_note.status_code == 201, nursing_note.text
    assert nursing_note.json()["kind"] == "nursing"
    assert nurse.client.get(f"/api/v1/encounters/{ENCOUNTER_1}/notes").json()[0]["content"] == "Theo dõi chăm sóc tổng hợp."
    stale_note = nurse.client.post(
        f"/api/v1/encounters/{ENCOUNTER_1}/notes?expected_revision=3",
        json={"kind": "nursing", "content": "Ghi nhận cũ."},
    )
    assert stale_note.status_code == 409
    assert len(nurse.db.notes) == 1

    doctor = context("doctor")
    nursing_as_doctor = doctor.client.post(
        f"/api/v1/encounters/{ENCOUNTER_2}/notes?expected_revision=2",
        json={"kind": "nursing", "content": "Ghi nhận chăm sóc."},
    )
    assert nursing_as_doctor.status_code == 403
    exam = doctor.client.post(
        f"/api/v1/encounters/{ENCOUNTER_2}/notes?expected_revision=2",
        json={"kind": "examination", "content": "Khám giả lập, chưa kết luận."},
    )
    assert exam.status_code == 201, exam.text
    assert exam.json()["kind"] == "examination"


def test_case_and_encounter_create_are_doctor_scoped_and_revision_checked():
    doctor = context("doctor")
    created_case = doctor.client.post("/api/v1/cases", json={"age": 77, "sex": "female"})
    assert created_case.status_code == 201, created_case.text
    case = created_case.json()
    assert case["synthetic_code"].startswith("SYN-")
    assert case["owner_id"] == str(DOCTOR_A)
    assert case["revision"] == 1
    assert "diagnosis" not in case

    duplicate = doctor.client.post(
        "/api/v1/cases", json={"synthetic_code": "SYN-CASE-1", "age": 77, "sex": "female"}
    )
    assert duplicate.status_code == 409

    encounter = doctor.client.post(
        f"/api/v1/cases/{CASE_1}/encounters?expected_revision=3",
        json={"occurred_at": "2026-10-08T10:00:00Z"},
    )
    assert encounter.status_code == 201, encounter.text
    assert encounter.json()["case_id"] == str(CASE_1)
    assert doctor.db.cases[CASE_1]["revision"] == 4
    stale = doctor.client.post(
        f"/api/v1/cases/{CASE_1}/encounters?expected_revision=3",
        json={"occurred_at": "2026-10-08T10:30:00Z"},
    )
    assert stale.status_code == 409
    assert len(doctor.db.encounters) == 3

    nurse = context("nurse")
    denied = nurse.client.post(
        f"/api/v1/cases/{CASE_1}/encounters?expected_revision=3",
        json={"occurred_at": "2026-10-08T11:00:00Z"},
    )
    assert denied.status_code == 403
