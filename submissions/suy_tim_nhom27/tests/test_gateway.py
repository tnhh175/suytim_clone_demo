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


def test_contract_and_sql():
    root = Path(__file__).resolve().parents[1]
    spec = yaml.safe_load((root / "api/openapi.yaml").read_text(encoding="utf-8"))
    assert spec == create_app().openapi()
    assert spec["openapi"] == "3.0.3"
    validate(spec)
    assert "/api/v1/patient/appointments" in spec["paths"]
    assert "/api/v1/encounters/{encounter_id}/medications" in spec["paths"]
    for sql_name in (
        "schema.sql",
        "seed.sql",
        "portal_permissions.sql",
        "migrations/001_result_integrity.sql",
    ):
        parse_sql((root / "database" / sql_name).read_text(encoding="utf-8"))
