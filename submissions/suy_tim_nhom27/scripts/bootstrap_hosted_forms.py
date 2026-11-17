"""Provision a new, dedicated PostgreSQL 16+ database for the hosted demo."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory

import psycopg
from psycopg import sql

from seed_form_demo import ROOT, prepare


SCHEMA = "d3_form_hosted"


def restrict_runtime(admin_dsn: str) -> None:
    """Grant the hosted routes their DML privileges and remove runtime owner access."""
    with psycopg.connect(admin_dsn, connect_timeout=10) as conn:
        conn.execute("SELECT pg_advisory_xact_lock(hashtext('suytim_hosted_forms_bootstrap'))")
        owner = conn.execute("""
            SELECT pg_get_userbyid(nspowner) FROM pg_namespace WHERE nspname = %s
        """, (SCHEMA,)).fetchone()
        if owner != ("hf_demo_owner",):
            raise SystemExit("Expected a dedicated d3_form_hosted schema owned by hf_demo_owner.")
        conn.execute("SET LOCAL ROLE hf_demo_owner")
        conn.execute("SET LOCAL search_path TO d3_form_hosted")
        conn.execute("GRANT USAGE ON SCHEMA d3_form_hosted TO hf_demo_runtime")
        conn.execute("""
            GRANT SELECT ON app_user, role, user_role, user_permission, form_access TO hf_demo_runtime
        """)
        conn.execute("""
            GRANT SELECT, INSERT, UPDATE ON auth_session, form_field, form_patient, form_visit
            TO hf_demo_runtime
        """)
        conn.execute("GRANT SELECT, UPDATE ON form_catalog TO hf_demo_runtime")
        conn.execute("""
            GRANT SELECT, INSERT ON form_field_history, form_patient_alias, form_patient_history,
                form_history, form_import_preset, form_import_batch TO hf_demo_runtime
        """)
        conn.execute("GRANT SELECT, USAGE ON SEQUENCE form_patient_code_seq TO hf_demo_runtime")
        conn.execute("RESET ROLE")
        conn.execute("REVOKE hf_demo_owner FROM hf_demo_runtime")


def password(name: str) -> str:
    value = os.environ.get(name, "")
    if not 20 <= len(value) <= 128 or not value.strip():
        raise SystemExit(f"{name} must contain a unique generated password (20–128 characters).")
    return value


def bootstrap(admin_dsn: str) -> None:
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
    restrict_runtime(admin_dsn)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--restrict-runtime", action="store_true",
                        help="remove owner access from an already initialized hosted database")
    args = parser.parse_args()
    admin_dsn = os.environ["BOOTSTRAP_DATABASE_URL"]
    if args.restrict_runtime:
        restrict_runtime(admin_dsn)
    else:
        bootstrap(admin_dsn)


if __name__ == "__main__":
    main()
