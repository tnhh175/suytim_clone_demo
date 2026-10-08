from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.gateway.authorization import Actor
from src.gateway.patient_portal import build_patient_portal_router


PATIENT_ID = UUID("00000000-0000-4000-8000-000000000005")
CASE_ID = UUID("10000000-0000-4000-8000-000000000001")
DOCTOR_ID = UUID("00000000-0000-4000-8000-000000000001")
ACTOR = Actor(PATIENT_ID, "patient_demo", "patient", frozenset())


class Cursor:
    def __init__(self, row=None, rows=None):
        self._row = row
        self._rows = rows or []

    def fetchone(self):
        return self._row

    def fetchall(self):
        return self._rows


class FakeConnection:
    def __init__(self):
        self.calls = []

    def execute(self, query, params=()):
        compact = " ".join(query.split())
        self.calls.append((compact, params))
        if "portal_case_id()" in compact:
            return Cursor({"case_id": CASE_ID})
        if compact.startswith("INSERT INTO appointment"):
            return Cursor({
                "id": uuid4(),
                "case_id": params[0],
                "doctor_id": params[1],
                "slot_at": params[2],
                "reason": params[3],
                "status": "requested",
                "encounter_id": None,
                "created_at": datetime.now(timezone.utc),
            })
        if compact.startswith("UPDATE medication_reminder"):
            return Cursor({
                "id": params[1],
                "status": params[0],
                "responded_at": datetime.now(timezone.utc),
            })
        return Cursor(rows=[])


def client_for(actor=ACTOR):
    conn = FakeConnection()

    @contextmanager
    def connection_provider(request, current_actor):
        assert current_actor.user_id == actor.user_id
        yield conn

    app = FastAPI()
    app.include_router(
        build_patient_portal_router(
            actor_dependency=lambda: actor,
            connection_provider=connection_provider,
        )
    )
    return TestClient(app), conn


def test_patient_appointment_uses_server_bound_case_not_client_case_id():
    client, conn = client_for()
    response = client.post(
        "/api/v1/patient/appointments",
        json={
            "doctor_id": str(DOCTOR_ID),
            "slot_at": (datetime.now(timezone.utc) + timedelta(days=2)).isoformat(),
            "reason": "Tái khám demo",
        },
    )
    assert response.status_code == 201
    assert response.json()["case_id"] == str(CASE_ID)
    insert = next(call for call in conn.calls if call[0].startswith("INSERT INTO appointment"))
    assert insert[1][0] == CASE_ID
    assert insert[1][-1] == PATIENT_ID


def test_patient_cannot_submit_another_case_id():
    client, conn = client_for()
    response = client.post(
        "/api/v1/patient/appointments",
        json={
            "case_id": str(uuid4()),
            "doctor_id": str(DOCTOR_ID),
            "slot_at": (datetime.now(timezone.utc) + timedelta(days=2)).isoformat(),
            "reason": "Tái khám demo",
        },
    )
    assert response.status_code == 422
    assert not conn.calls


def test_patient_measurement_requires_a_value_and_paired_blood_pressure():
    client, conn = client_for()
    response = client.post(
        "/api/v1/patient/measurements",
        json={"observed_at": datetime.now(timezone.utc).isoformat()},
    )
    assert response.status_code == 422
    response = client.post(
        "/api/v1/patient/measurements",
        json={
            "observed_at": datetime.now(timezone.utc).isoformat(),
            "systolic_bp": 120,
        },
    )
    assert response.status_code == 422
    assert not conn.calls


def test_staff_role_cannot_use_patient_portal():
    client, conn = client_for(Actor(DOCTOR_ID, "doctor_demo", "doctor", frozenset()))
    response = client.get("/api/v1/patient/appointments")
    assert response.status_code == 403
    assert not conn.calls


def test_reminder_response_only_sends_allowed_status_transition():
    client, conn = client_for()
    reminder_id = uuid4()
    response = client.patch(
        f"/api/v1/patient/reminders/{reminder_id}",
        json={"status": "taken"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "taken"
    update = next(call for call in conn.calls if call[0].startswith("UPDATE medication_reminder"))
    assert update[0] == "UPDATE medication_reminder SET status = %s WHERE id = %s AND status = 'pending' RETURNING id, status, responded_at"
    assert update[1] == ("taken", reminder_id)
