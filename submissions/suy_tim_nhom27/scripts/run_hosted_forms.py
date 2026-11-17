"""Start only the forms demo behind the hosting provider's HTTPS proxy."""
from __future__ import annotations

import os
from pathlib import Path
import sys

import psycopg
from psycopg.conninfo import make_conninfo
import uvicorn


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main() -> None:
    database_url = make_conninfo(
        os.environ["DATABASE_URL"], options="-csearch_path=d3_form_hosted", connect_timeout=10,
    )
    with psycopg.connect(database_url) as conn:
        if conn.info.user != "hf_demo_runtime":
            raise SystemExit("DATABASE_URL must log in as hf_demo_runtime.")
        if conn.execute("SELECT pg_has_role(current_user, 'hf_demo_owner', 'MEMBER')").fetchone()[0]:
            raise SystemExit("Run bootstrap_hosted_forms.py --restrict-runtime before starting this version.")
        conn.execute("SELECT 1 FROM app_user LIMIT 1")
        conn.execute("SELECT revision FROM form_catalog WHERE id = 1").fetchone()

    from src.gateway.main import create_app

    app = create_app(database_url=database_url, forms_only=True)
    app.state.restricted_forms_runtime = True
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", "8080")))


if __name__ == "__main__":
    main()
