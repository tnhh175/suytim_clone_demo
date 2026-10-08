"""Shared PostgreSQL pool and scoped connection helpers for the demo gateway."""
from __future__ import annotations

from contextlib import contextmanager
import os
from typing import Iterator, TYPE_CHECKING

from fastapi import HTTPException, Request
from psycopg import Connection
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

if TYPE_CHECKING:
    from .authorization import Actor


def create_pool(database_url: str | None = None) -> ConnectionPool | None:
    """Create a lazy pool; the app lifespan owns opening and closing it."""
    dsn = database_url if database_url is not None else os.getenv("DATABASE_URL")
    if not dsn:
        return None
    return ConnectionPool(
        conninfo=dsn,
        min_size=1,
        max_size=int(os.getenv("DB_POOL_MAX_SIZE", "8")),
        timeout=3.0,
        open=False,
        kwargs={
            "application_name": "suytim_hospital_demo",
            "row_factory": dict_row,
        },
    )


def _pool_for(request: Request) -> ConnectionPool:
    pool: ConnectionPool | None = getattr(request.app.state, "pool", None)
    if pool is None:
        raise HTTPException(status_code=503, detail="Cơ sở dữ liệu demo chưa được cấu hình")
    return pool


@contextmanager
def staff_connection(request: Request, actor: "Actor") -> Iterator[Connection]:
    """Yield a transaction-scoped table-owner connection with a trusted actor.

    API role and case-scope checks must run before repository work. The SET LOCAL
    statements are transaction-scoped and cannot leak through the connection pool.
    """
    with _pool_for(request).connection() as conn:
        conn.execute("SET LOCAL ROLE hf_demo_owner")
        conn.execute(
            "SELECT set_config('app.user_id', %s, true)",
            (str(actor.user_id),),
        )
        yield conn


@contextmanager
def portal_connection(request: Request, actor: "Actor") -> Iterator[Connection]:
    """Yield a transaction as the restricted patient portal role under its own identity."""
    with _pool_for(request).connection() as conn:
        conn.execute("SET LOCAL ROLE hf_patient_portal")
        conn.execute(
            "SELECT set_config('app.user_id', %s, true)",
            (str(actor.user_id),),
        )
        yield conn


@contextmanager
def plain_connection(request: Request) -> Iterator[Connection]:
    """Yield an ordinary runtime connection for authentication/session queries."""
    with _pool_for(request).connection() as conn:
        yield conn


def check_pool(pool: ConnectionPool | None) -> bool:
    if pool is None:
        return False
    try:
        with pool.connection() as conn:
            conn.execute("SELECT 1").fetchone()
        return True
    except Exception:
        return False
