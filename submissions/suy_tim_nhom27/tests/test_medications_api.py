from __future__ import annotations

from contextlib import contextmanager
from datetime import date
from uuid import UUID, uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.gateway.authorization import Actor, get_current_actor
from src.gateway.routers.medications import build_medications_router


DOCTOR_ID = UUID("00000000-0000-4000-8000-000000000001")
NURSE_ID = UUID("00000000-0000-4000-8000-000000000002")
PHARMACIST_ID = UUID("00000000-0000-4000-8000-000000000003")
ADMIN_ID = UUID("00000000-0000-4000-8000-000000000004")
PATIENT_ID = UUID("00000000-0000-4000-8000-000000000005")
CASE_ID = UUID("10000000-0000-4000-8000-000000000001")
ENCOUNTER_ID = UUID("20000000-0000-4000-8000-000000000001")


class Cursor:
    def __init__(self, rows=()):
        self.rows = list(rows)

    def fetchone(self):
        return self.rows[0] if self.rows else None

    def fetchall(self):
        return list(self.rows)


class FakeDatabase:
    def __init__(self, *, pharmacist_access=True, revision=7):
        self.pharmacist_access = pharmacist_access
        self.revision = revision
        self.medications = []
        self.sql = []

    @contextmanager
    def connection(self):
        yield self

    def execute(self, sql, params=()):
        normalized = " ".join(sql.lower().split())
        self.sql.append((normalized, params))
        if normalized.startswith("select e.id, e.case_id, e.status, c.revision"):
            if params[0] != ENCOUNTER_ID:
                return Cursor()
            return Cursor([{
                "id": ENCOUNTER_ID,
                "case_id": CASE_ID,
                "status": "open",
                "revision": self.revision,
            }])
        if normalized.startswith("select id, case_id from encounter"):
            if params[0] != ENCOUNTER_ID:
                return Cursor()
            return Cursor([{"id": ENCOUNTER_ID, "case_id": CASE_ID}])
        if normalized.startswith("select owner_id from patient_case"):
            return Cursor([{"owner_id": DOCTOR_ID}] if params[0] == CASE_ID else [])
        if normalized.startswith("select 1 from case_access"):
            case_id, user_id, scopes = params
            allowed = (
                self.pharmacist_access
                and case_id == CASE_ID
                and user_id == PHARMACIST_ID
                and "medsafety" in scopes
            )
            return Cursor([{"?column?": 1}] if allowed else [])
        if normalized.startswith("select id, encounter_id, ingredient_code, dose, dose_unit, route,"):
            return Cursor(self.medications)
        if normalized.startswith("insert into medication("):
            (
                encounter_id,
                ingredient_code,
                dose,
                dose_unit,
                route,
                frequency_per_day,
                kind,
                starts_on,
                ends_on,
                instructions,
                recorded_by,
            ) = params
            row = {
                "id": uuid4(),
                "encounter_id": encounter_id,
                "ingredient_code": ingredient_code,
                "dose": dose,
                "dose_unit": dose_unit,
                "route": route,
                "frequency_per_day": frequency_per_day,
                "kind": kind,
                "starts_on": starts_on or date(2026, 10, 8),
                "ends_on": ends_on,
                "instructions": instructions,
            }
            self.medications.append(row)
            self.revision += 1  # emulate the schema's medication_revision trigger
            self.inserted_recorded_by = recorded_by
            self.insert_sql = normalized
            return Cursor([row])
        raise AssertionError(f"Unexpected SQL in fake: {sql}")


def make_client(monkeypatch, role="doctor", *, pharmacist_access=True, revision=7):
    database = FakeDatabase(pharmacist_access=pharmacist_access, revision=revision)
    user_ids = {
        "doctor": DOCTOR_ID,
        "nurse": NURSE_ID,
        "pharmacist": PHARMACIST_ID,
        "admin": ADMIN_ID,
        "patient": PATIENT_ID,
    }
    actor = Actor(user_ids[role], f"{role}_demo", role, frozenset())
    import src.gateway.routers.medications as medications_module

    monkeypatch.setattr(
        medications_module,
        "staff_connection",
        lambda request, current_actor: request.app.state.fake_database.connection(),
    )
    app = FastAPI()
    app.state.fake_database = database
    app.include_router(build_medications_router())
    app.dependency_overrides[get_current_actor] = lambda: actor
    return TestClient(app), database


def test_pharmacist_reads_only_assigned_medsafety_scope(monkeypatch):
    client, database = make_client(monkeypatch, "pharmacist")
    medication_id = UUID("41000000-0000-4000-8000-000000000001")
    database.medications.append({
        "id": medication_id,
        "encounter_id": ENCOUNTER_ID,
        "ingredient_code": "synthetic_drug_a",
        "dose": 1.5,
        "dose_unit": "mg",
        "route": "oral",
        "frequency_per_day": 1,
        "kind": "current",
        "starts_on": date(2026, 10, 8),
        "ends_on": None,
        "instructions": "Synthetic fixture",
    })
    response = client.get(f"/api/v1/encounters/{ENCOUNTER_ID}/medications")
    assert response.status_code == 200
    assert response.json() == [{
        "id": str(medication_id),
        "encounter_id": str(ENCOUNTER_ID),
        "ingredient_code": "synthetic_drug_a",
        "dose": 1.5,
        "dose_unit": "mg",
        "route": "oral",
        "frequency_per_day": 1,
        "kind": "current",
        "starts_on": "2026-10-08",
        "ends_on": None,
        "instructions": "Synthetic fixture",
    }]
    assert any("from medication" in sql for sql, _ in database.sql)
    denied_write = client.post(
        f"/api/v1/encounters/{ENCOUNTER_ID}/medications",
        json={
            "expected_revision": 7,
            "ingredient_code": "synthetic_drug_a",
            "dose": 1,
            "dose_unit": "mg",
            "route": "oral",
            "frequency_per_day": 1,
            "kind": "current",
        },
    )
    assert denied_write.status_code == 403

    denied_client, _ = make_client(monkeypatch, "pharmacist", pharmacist_access=False)
    denied = denied_client.get(f"/api/v1/encounters/{ENCOUNTER_ID}/medications")
    assert denied.status_code == 403


def test_doctor_creates_manual_medication_with_token_actor_and_revision(monkeypatch):
    client, database = make_client(monkeypatch)
    response = client.post(
        f"/api/v1/encounters/{ENCOUNTER_ID}/medications",
        json={
            "expected_revision": 7,
            "ingredient_code": "synthetic_drug_a",
            "dose": 2,
            "dose_unit": "mg",
            "route": "oral",
            "frequency_per_day": 2,
            "kind": "current",
            "instructions": "  Chỉ dùng cho hồ sơ demo.  ",
        },
    )
    assert response.status_code == 201
    result = response.json()
    assert result["ingredient_code"] == "synthetic_drug_a"
    assert result["instructions"] == "Chỉ dùng cho hồ sơ demo."
    assert result["starts_on"] == "2026-10-08"
    assert database.inserted_recorded_by == DOCTOR_ID
    assert database.revision == 8
    assert "prescription_id" not in database.insert_sql
    assert "medication_schedule" not in database.insert_sql


def test_doctor_write_rejects_stale_revision(monkeypatch):
    client, database = make_client(monkeypatch, revision=8)
    response = client.post(
        f"/api/v1/encounters/{ENCOUNTER_ID}/medications",
        json={
            "expected_revision": 7,
            "ingredient_code": "synthetic_drug_a",
            "dose": 1,
            "dose_unit": "mg",
            "route": "oral",
            "frequency_per_day": 1,
            "kind": "proposed",
        },
    )
    assert response.status_code == 409
    assert database.medications == []


@pytest.mark.parametrize(
    "override",
    [
        {"ingredient_code": "not valid"},
        {"dose": 0},
        {"dose": "Infinity"},
        {"dose_unit": "tablet"},
        {"route": "intramuscular"},
        {"frequency_per_day": 25},
        {"kind": "recommended"},
        {"starts_on": "2026-10-10", "ends_on": "2026-10-09"},
        {"unexpected": "field"},
    ],
)
def test_invalid_medication_fields_return_422(monkeypatch, override):
    client, database = make_client(monkeypatch)
    body = {
        "expected_revision": 7,
        "ingredient_code": "synthetic_drug_a",
        "dose": 1,
        "dose_unit": "mg",
        "route": "oral",
        "frequency_per_day": 1,
        "kind": "current",
    }
    body.update(override)
    response = client.post(f"/api/v1/encounters/{ENCOUNTER_ID}/medications", json=body)
    assert response.status_code == 422
    assert database.medications == []


@pytest.mark.parametrize("role", ["admin", "patient", "nurse"])
def test_nonclinical_roles_cannot_read_or_write_medications(monkeypatch, role):
    client, database = make_client(monkeypatch, role)
    url = f"/api/v1/encounters/{ENCOUNTER_ID}/medications"
    assert client.get(url).status_code == 403
    assert client.post(url, json={
        "expected_revision": 7,
        "ingredient_code": "synthetic_drug_a",
        "dose": 1,
        "dose_unit": "mg",
        "route": "oral",
        "frequency_per_day": 1,
        "kind": "current",
    }).status_code == 403
    assert database.medications == []
