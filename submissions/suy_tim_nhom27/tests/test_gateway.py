from __future__ import annotations

from pathlib import Path

import yaml
from fastapi.testclient import TestClient
from openapi_spec_validator import validate
from pglast import parse_sql

from src.gateway.main import create_app


def test_app_serves_demo_assets_and_fails_closed_without_database():
    with TestClient(create_app()) as client:
        page = client.get("/")
        assert page.status_code == 200
        assert "Synthetic Data" in page.text
        assert client.get("/health").status_code == 503
        response = client.post(
            "/api/v1/auth/token",
            json={"username": "doctor_demo", "password": "DemoOnly!2026"},
        )
        assert response.status_code == 503


def test_documented_origin_and_explicit_dev_server_cors_preflight():
    with TestClient(create_app()) as client:
        page = client.get("/", headers={"host": "127.0.0.1:8000"})
        assert page.status_code == 200
        preflight = client.options(
            "/api/v1/auth/token",
            headers={
                "Origin": "http://127.0.0.1:5173",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "authorization,content-type",
            },
        )
        assert preflight.status_code == 200
        assert preflight.headers["access-control-allow-origin"] == "http://127.0.0.1:5173"

    root = Path(__file__).resolve().parents[1]
    web = (root / "web/app.js").read_text(encoding="utf-8")
    readme = (root / "README.md").read_text(encoding="utf-8")
    assert "http://127.0.0.1:8000" in readme
    assert '|| location.origin' in web
    assert '"/api/v1/auth/logout"' in web
    assert "item.recorded_at || item.created_at || item.occurred_at" in web
    assert "expected_revision: Number(state.selectedCase && state.selectedCase.revision)" in web
    logout_body = web[web.index("async function logout"):web.index('$("#logoutButton").addEventListener')]
    request_at = logout_body.index('apiRequest("/api/v1/auth/logout"')
    assert request_at < logout_body.index('endSession("Đã đăng xuất khỏi phiên demo.")', request_at)
    assert "Không thể xác nhận thu hồi phiên trên máy chủ" in logout_body


def test_contract_and_sql():
    root = Path(__file__).resolve().parents[1]
    spec = yaml.safe_load((root / "api/openapi.yaml").read_text(encoding="utf-8"))
    assert spec == create_app().openapi()
    assert spec["openapi"] == "3.0.3"
    validate(spec)
    assert "/api/v1/patient/appointments" in spec["paths"]
    assert "/api/v1/encounters/{encounter_id}/medications" in spec["paths"]
    assert "/api/v1/cases/{case_id}/history" in spec["paths"]
    assert "/api/v1/cases/{case_id}/export" in spec["paths"]
    module_schema = spec["components"]["schemas"]["ModuleResultOut"]["properties"]
    for field in ("phenotype", "stage", "course"):
        assert module_schema[field].get("type") != "null"
        assert module_schema[field].get("nullable") is True
    for sql_name in (
        "schema.sql",
        "seed.sql",
        "portal_permissions.sql",
        "migrations/001_result_integrity.sql",
    ):
        parse_sql((root / "database" / sql_name).read_text(encoding="utf-8"))
