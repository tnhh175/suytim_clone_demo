"""Provision a new, dedicated PostgreSQL 16+ database for the hosted demo."""
from __future__ import annotations

import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory

import psycopg
from psycopg import sql

from seed_form_demo import ROOT, prepare


SCHEMA = "d3_form_hosted"


def password(name: str) -> str:
    value = os.environ.get(name, "")
    if not 20 <= len(value) <= 128 or not value.strip():
        raise SystemExit(f"{name} must contain a unique generated password (20–128 characters).")
    return value


def main() -> None:
    admin_dsn = os.environ["BOOTSTRAP_DATABASE_URL"]
    runtime, admin, doctor = (
        password(name)
        for name in ("HF_RUNTIME_PASSWORD", "HF_ADMIN_PASSWORD", "HF_DOCTOR_PASSWORD")
    )
    if len({runtime, admin, doctor}) != 3:
        raise SystemExit("Use distinct passwords for PostgreSQL, Admin and Doctor.")

    with psycopg.connect(admin_dsn, autocommit=True, connect_timeout=10) as conn:
        if conn.info.server_version < 160000:
            raise SystemExit("PostgreSQL 16 or newer is required.")
        with conn.transaction():
            conn.execute("SELECT pg_advisory_xact_lock(hashtext('suytim_hosted_forms_bootstrap'))")
            occupied = conn.execute("""
                SELECT EXISTS (
                    SELECT 1 FROM pg_namespace
                    WHERE nspname NOT IN ('public', 'information_schema')
                      AND nspname !~ '^pg_'
                ) OR EXISTS (
                    SELECT 1 FROM pg_class
                    WHERE relnamespace = 'public'::regnamespace
                ) OR EXISTS (
                    SELECT 1 FROM pg_roles
                    WHERE rolname IN ('hf_demo_owner', 'hf_demo_runtime')
                )
            """).fetchone()[0]
            if occupied:
                raise SystemExit("Bootstrap requires a new dedicated PostgreSQL instance and empty database.")
            conn.execute("CREATE ROLE hf_demo_owner NOLOGIN")
            conn.execute(sql.SQL("CREATE ROLE hf_demo_runtime LOGIN NOINHERIT PASSWORD {}").format(
                sql.Literal(runtime)
            ))
            conn.execute("GRANT hf_demo_owner TO CURRENT_USER")
            conn.execute("GRANT hf_demo_owner TO hf_demo_runtime WITH INHERIT FALSE, SET TRUE")
            conn.execute(sql.SQL("GRANT CREATE ON DATABASE {} TO hf_demo_owner").format(
                sql.Identifier(conn.info.dbname)
            ))
            conn.execute("REVOKE CREATE ON SCHEMA public FROM PUBLIC")
            conn.execute("GRANT USAGE, CREATE ON SCHEMA public TO hf_demo_owner")
        conn.execute("SET ROLE hf_demo_owner")
        conn.execute("SET search_path TO public")
        conn.execute((ROOT / "database/schema.sql").read_text(encoding="utf-8"))

    # prepare() uses the same catalog, migrations and synthetic fixtures as the local demo.
    with TemporaryDirectory(prefix="suytim-bootstrap-") as directory:
        credentials_file = Path(directory) / "local-data" / "hosted-credentials.json"
        credentials_file.parent.mkdir(mode=0o700)
        credentials_file.write_text(json.dumps({
            "synthetic": True,
            "schema": SCHEMA,
            "accounts": {
                "admin": {"username": "forms_admin", "password": admin},
                "doctor": {"username": "forms_doctor", "password": doctor},
            },
        }), encoding="utf-8")
        prepare(admin_dsn, SCHEMA, credentials_file)


if __name__ == "__main__":
    main()
