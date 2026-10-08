"""Signup unit checks and opt-in real PostgreSQL integration checks.

The integration checks retain uniquely named synthetic identities in an isolated
QA database because patient_account links are intentionally immutable.
"""
from contextlib import contextmanager
from concurrent.futures import ThreadPoolExecutor
import os
from uuid import uuid4

import psycopg
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from pydantic import ValidationError

from src.gateway.main import create_app
from src.gateway.routers.auth import RegistrationLimiter, RegistrationPayload, hash_password, verify_password

PASSWORD = "SyntheticOnly!2026"


def payload(username=None, **extra):
    return {"username": username or "qa_" + uuid4().hex[:20], "password": PASSWORD, "age": 70, "sex": "unknown", **extra}


def test_hashes_use_unique_salts_and_existing_verifier():
    first, second = hash_password(PASSWORD), hash_password(PASSWORD)
    assert first != second
    assert first.split("$")[1] == "600000"
    assert verify_password(PASSWORD, first) and verify_password(PASSWORD, second)
    assert not verify_password("incorrect", first)


@pytest.mark.parametrize("change", [
    {"username": "x"}, {"username": "invalid name"}, {"password": "short"},
    {"password": " " * 12}, {"age": -1}, {"age": 121}, {"age": True},
    {"age": 70.5}, {"sex": "invalid"}, {"role": "admin"}, {"owner_id": str(uuid4())},
    {"case_id": str(uuid4())}, {"active": False}, {"permission": "rule.approve"},
])
def test_registration_schema_rejects_invalid_or_privileged_input(change):
    with pytest.raises(ValidationError):
        RegistrationPayload(**payload(**change))


def test_username_is_trimmed_and_preserves_case():
    assert RegistrationPayload(**payload(username="  Qa.Patient  ")).username == "Qa.Patient"


def test_unconfigured_database_is_503_without_sensitive_echo():
    with TestClient(create_app(database_url="")) as client:
        response = client.post("/api/v1/auth/register", json=payload())
    assert response.status_code == 503
    assert PASSWORD not in response.text


def test_limiter_is_bounded_and_expires(monkeypatch):
    now = [100.0]
    monkeypatch.setattr("src.gateway.routers.auth.time.monotonic", lambda: now[0])
    limiter = RegistrationLimiter()
    for _ in range(8): limiter.check("one")
    with pytest.raises(HTTPException) as exc: limiter.check("one")
    assert exc.value.status_code == 429 and exc.value.headers["Retry-After"] == "60"
    for number in range(56): limiter.check(str(number))
    with pytest.raises(HTTPException): limiter.check("overflow")
    assert len(limiter.attempts) == 64
    now[0] += 61
    limiter.check("one")
    assert len(limiter.attempts) == 1


@pytest.fixture
def db_client():
    dsn = os.getenv("HF_REGISTRATION_TEST_DATABASE_URL")
    if not dsn: pytest.skip("Set HF_REGISTRATION_TEST_DATABASE_URL to a disposable QA database")
    database = psycopg.conninfo.conninfo_to_dict(dsn).get("dbname", "")
    assert "qa" in database.lower(), "Registration checks persist synthetic identities; use a QA database"
    app = create_app(database_url=dsn)
    with TestClient(app) as client:
        yield client, app


def rows(app, sql, params=()):
    with app.state.pool.connection() as conn:
        conn.execute("SET LOCAL ROLE hf_demo_owner")
        return conn.execute(sql, params).fetchall()


def auth(client, username):
    response = client.post("/api/v1/auth/token", json={"username": username, "password": PASSWORD})
    assert response.status_code == 200
    return {"Authorization": "Bearer " + response.json()["access_token"]}


def test_real_signup_login_isolation_and_logout(db_client):
    client, app = db_client
    first, second = payload(), payload()
    for body in (first, second):
        result = client.post("/api/v1/auth/register", json=body)
        assert result.status_code == 201
        assert result.json() == {"username": body["username"], "role": "patient"}
    profiles = rows(app, """SELECT u.username, u.password_hash, pa.case_id, c.owner_id, c.synthetic_code, c.age, c.sex
        FROM app_user u JOIN patient_account pa ON pa.user_id=u.id JOIN patient_case c ON c.id=pa.case_id
        WHERE u.username = ANY(%s)""", ([first["username"], second["username"]],))
    assert len(profiles) == 2 and profiles[0]["case_id"] != profiles[1]["case_id"]
    assert profiles[0]["password_hash"] != profiles[1]["password_hash"]
    assert all(row["synthetic_code"].startswith("SYN-") and row["age"] == 70 for row in profiles)
    one, two = auth(client, first["username"]), auth(client, second["username"])
    assert client.get("/api/v1/auth/me", headers=one).json()["role"] == "patient"
    for collection in ("appointments", "measurements", "prescriptions", "reminders"):
        assert client.get("/api/v1/patient/" + collection, headers=one).json() == []
        assert client.get("/api/v1/patient/" + collection, headers=two).json() == []
    measurement = client.post("/api/v1/patient/measurements", headers=one, json={"observed_at": "2026-10-08T08:00:00Z", "weight_kg": 61})
    assert measurement.status_code == 201
    assert len(client.get("/api/v1/patient/measurements", headers=one).json()) == 1
    assert client.get("/api/v1/patient/measurements", headers=two).json() == []
    for endpoint in ("cases", "rule-versions", "audit-events"):
        assert client.get("/api/v1/" + endpoint, headers=one).status_code == 403
    assert client.post("/api/v1/auth/logout", headers=one).status_code == 200
    assert client.get("/api/v1/auth/me", headers=one).status_code == 401


def test_real_concurrent_duplicate_has_one_identity(db_client):
    client, app = db_client
    body = payload()
    with ThreadPoolExecutor(max_workers=2) as workers:
        responses = list(workers.map(lambda _: client.post("/api/v1/auth/register", json=body), range(2)))
    assert sorted(result.status_code for result in responses) == [201, 409]
    assert len(rows(app, "SELECT id FROM app_user WHERE username=%s", (body["username"],))) == 1
    assert len(rows(app, "SELECT pa.* FROM patient_account pa JOIN app_user u ON u.id=pa.user_id WHERE u.username=%s", (body["username"],))) == 1


def test_real_invalid_owner_creates_nothing(db_client, monkeypatch):
    client, app = db_client
    body = payload()
    monkeypatch.setenv("HF_REGISTRATION_DOCTOR_USERNAME", "patient_demo")
    before = rows(app, "SELECT count(*) AS count FROM patient_case")[0]["count"]
    assert client.post("/api/v1/auth/register", json=body).status_code == 503
    assert rows(app, "SELECT id FROM app_user WHERE username=%s", (body["username"],)) == []
    assert rows(app, "SELECT count(*) AS count FROM patient_case")[0]["count"] == before


def test_real_late_database_failure_rolls_back_every_signup_write(db_client):
    client, app = db_client
    body = payload()
    original_pool = app.state.pool
    before = rows(app, "SELECT count(*) AS count FROM patient_case")[0]["count"]
    class FailingConnection:
        def __init__(self, conn): self.conn = conn
        def execute(self, sql, params=()):
            if "INSERT INTO patient_account" in sql: raise psycopg.OperationalError("Injected isolated QA write failure")
            return self.conn.execute(sql, params)
    class FailingPool:
        @contextmanager
        def connection(self):
            with original_pool.connection() as conn: yield FailingConnection(conn)
    app.state.pool = FailingPool()
    try:
        assert client.post("/api/v1/auth/register", json=body).status_code == 503
    finally:
        app.state.pool = original_pool
    assert rows(app, "SELECT id FROM app_user WHERE username=%s", (body["username"],)) == []
    assert rows(app, "SELECT count(*) AS count FROM patient_case")[0]["count"] == before
