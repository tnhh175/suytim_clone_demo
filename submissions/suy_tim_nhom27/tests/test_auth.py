from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from src.gateway.authorization import Actor, require_case_access
from src.gateway.routers.auth import router, verify_password


_SEEDED_DOCTOR_HASH = (
    "pbkdf2_sha256$600000$c3V5dGltLWRlbW8tZG9jdG9y$"
    "n51i+8XHfNP98jCWGcjOH13tHQ/ogUe/P9ez8roAdZE="
)
_DOCTOR_ID = UUID("00000000-0000-4000-8000-000000000001")
_NURSE_ID = UUID("00000000-0000-4000-8000-000000000002")
_PHARMACIST_ID = UUID("00000000-0000-4000-8000-000000000003")
_ADMIN_ID = UUID("00000000-0000-4000-8000-000000000004")
_CASE_ID = UUID("10000000-0000-4000-8000-000000000001")


class FakeCursor:
    def __init__(self, rows=()):
        self._rows = list(rows)

    def fetchone(self):
        return self._rows[0] if self._rows else None

    def fetchall(self):
        return list(self._rows)


class FakeConnection:
    def __init__(self, pool):
        self.pool = pool

    def execute(self, sql, params=()):
        normalized = " ".join(sql.lower().split())
        if normalized.startswith("select id as user_id, password_hash, active from app_user"):
            user = self.pool.users.get(params[0])
            return FakeCursor([{
                "user_id": user["id"],
                "password_hash": user["password_hash"],
                "active": user["active"],
            }] if user else [])
        if normalized.startswith("select role_code from user_role"):
            return FakeCursor([{"role_code": role} for role in self.pool.roles.get(params[0], [])])
        if normalized.startswith("select permission_code from user_permission"):
            return FakeCursor([{"permission_code": permission} for permission in self.pool.permissions.get(params[0], [])])
        if normalized.startswith("insert into auth_session"):
            user_id, token_hash, expires_at = params
            self.pool.sessions[token_hash] = {
                "user_id": user_id,
                "expires_at": expires_at,
                "revoked_at": None,
            }
            return FakeCursor()
        if normalized.startswith("select u.id as user_id, u.username, u.active"):
            session = self.pool.sessions.get(params[0])
            if session is None:
                return FakeCursor()
            user = next(item for item in self.pool.users.values() if item["id"] == session["user_id"])
            return FakeCursor([{
                "user_id": user["id"],
                "username": user["username"],
                "active": user["active"],
                "session_unexpired": session["expires_at"] > datetime.now(timezone.utc),
                "revoked_at": session["revoked_at"],
            }])
        if normalized.startswith("update auth_session"):
            token_hash, user_id = params
            session = self.pool.sessions.get(token_hash)
            if session and session["user_id"] == user_id and session["revoked_at"] is None:
                session["revoked_at"] = datetime.now(timezone.utc)
            return FakeCursor()
        if normalized.startswith("select owner_id from patient_case"):
            owner_id = self.pool.cases.get(params[0])
            return FakeCursor([{"owner_id": owner_id}] if owner_id is not None else [])
        if normalized.startswith("select 1 from case_access"):
            case_id, user_id, scopes = params
            allowed = any(
                cid == case_id and uid == user_id and scope in scopes
                for cid, uid, scope in self.pool.case_access
            )
            return FakeCursor([(1,)] if allowed else [])
        raise AssertionError(f"Unexpected SQL in test fake: {sql}")


class FakePool:
    def __init__(self):
        self.users = {
            "doctor_demo": {
                "id": _DOCTOR_ID, "username": "doctor_demo",
                "password_hash": _SEEDED_DOCTOR_HASH, "active": True,
            },
            "nurse_demo": {
                "id": _NURSE_ID, "username": "nurse_demo",
                "password_hash": _SEEDED_DOCTOR_HASH, "active": True,
            },
            "pharmacist_demo": {
                "id": _PHARMACIST_ID, "username": "pharmacist_demo",
                "password_hash": _SEEDED_DOCTOR_HASH, "active": True,
            },
            "admin_demo": {
                "id": _ADMIN_ID, "username": "admin_demo",
                "password_hash": _SEEDED_DOCTOR_HASH, "active": True,
            },
        }
        self.roles = {
            _DOCTOR_ID: ["doctor"], _NURSE_ID: ["nurse"],
            _PHARMACIST_ID: ["pharmacist"], _ADMIN_ID: ["admin"],
        }
        self.permissions = {_DOCTOR_ID: ["rule.approve"]}
        self.sessions = {}
        self.cases = {_CASE_ID: _DOCTOR_ID}
        self.case_access = {
            (_CASE_ID, _NURSE_ID, "nursing"),
            (_CASE_ID, _PHARMACIST_ID, "medsafety"),
            # Even an accidental admin assignment must not grant clinical access.
            (_CASE_ID, _ADMIN_ID, "clinical"),
        }

    @contextmanager
    def connection(self):
        yield FakeConnection(self)


def client_for(pool):
    app = FastAPI()
    app.state.pool = pool
    app.include_router(router)
    return TestClient(app)


def login(client, username="doctor_demo"):
    response = client.post(
        "/api/v1/auth/token",
        json={"username": username, "password": "DemoOnly!2026"},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def test_seed_password_hash_verifies_and_rejects_wrong_or_malformed_values():
    assert verify_password("DemoOnly!2026", _SEEDED_DOCTOR_HASH)
    assert not verify_password("wrong", _SEEDED_DOCTOR_HASH)
    assert not verify_password("DemoOnly!2026", "plain-text-password")
    assert not verify_password("DemoOnly!2026", "pbkdf2_sha256$999999999$YQ==$YQ==")


def test_login_me_logout_stores_only_token_hash_and_revokes_session():
    pool = FakePool()
    client = client_for(pool)
    token = login(client)

    assert token not in pool.sessions
    import hashlib
    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    assert token_hash in pool.sessions
    assert client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}).json() == {
        "user_id": str(_DOCTOR_ID),
        "username": "doctor_demo",
        "role": "doctor",
        "permissions": ["rule.approve"],
    }

    assert client.post("/api/v1/auth/logout", headers={"Authorization": f"Bearer {token}"}).json() == {"status": "revoked"}
    assert client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}).status_code == 401


def test_expired_and_inactive_sessions_are_rejected():
    pool = FakePool()
    client = client_for(pool)
    token = login(client)
    import hashlib
    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    pool.sessions[token_hash]["expires_at"] = datetime.now(timezone.utc) - timedelta(seconds=1)
    assert client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}).status_code == 401

    fresh_token = login(client)
    pool.users["doctor_demo"]["active"] = False
    assert client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {fresh_token}"}).status_code == 401


def test_login_rejects_wrong_password_unknown_account_and_client_role():
    pool = FakePool()
    client = client_for(pool)
    assert client.post("/api/v1/auth/token", json={"username": "doctor_demo", "password": "wrong"}).status_code == 401
    assert client.post("/api/v1/auth/token", json={"username": "nobody", "password": "wrong"}).status_code == 401
    assert client.post("/api/v1/auth/token", json={
        "username": "doctor_demo", "password": "DemoOnly!2026", "role": "admin",
    }).status_code == 422


def test_selected_role_is_checked_before_creating_a_session():
    pool = FakePool()
    client = client_for(pool)
    credentials = {"username": "doctor_demo", "password": "DemoOnly!2026"}
    response = client.post("/api/v1/auth/token", json={**credentials, "selected_role": "admin"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Thông tin đăng nhập không hợp lệ"
    assert not pool.sessions
    assert client.post("/api/v1/auth/token", json={**credentials, "selected_role": "unknown"}).status_code == 422
    assert not pool.sessions
    assert client.post("/api/v1/auth/token", json={**credentials, "selected_role": "doctor"}).status_code == 200
    assert len(pool.sessions) == 1


def test_case_access_checks_existence_role_and_assigned_scope():
    pool = FakePool()
    with pool.connection() as conn:
        # A doctor owns this case and has the clinical scope by the SRS rule.
        require_case_access(conn, Actor(_DOCTOR_ID, "doctor_demo", "doctor", frozenset()), _CASE_ID, {"clinical"})
        require_case_access(conn, Actor(_NURSE_ID, "nurse_demo", "nurse", frozenset()), _CASE_ID, {"nursing"})
        require_case_access(conn, Actor(_PHARMACIST_ID, "pharmacist_demo", "pharmacist", frozenset()), _CASE_ID, {"medsafety"})

        with pytest.raises(HTTPException) as denied_scope:
            require_case_access(conn, Actor(_NURSE_ID, "nurse_demo", "nurse", frozenset()), _CASE_ID, {"clinical"})
        assert denied_scope.value.status_code == 403

        with pytest.raises(HTTPException) as denied_admin:
            require_case_access(conn, Actor(_ADMIN_ID, "admin_demo", "admin", frozenset()), _CASE_ID, {"clinical"})
        assert denied_admin.value.status_code == 403

        with pytest.raises(HTTPException) as not_found:
            require_case_access(conn, Actor(_ADMIN_ID, "admin_demo", "admin", frozenset()), uuid4(), {"clinical"})
        assert not_found.value.status_code == 404
