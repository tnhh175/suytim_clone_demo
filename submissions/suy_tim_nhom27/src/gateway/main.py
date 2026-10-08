from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator

import psycopg
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from psycopg_pool import ConnectionPool, PoolTimeout

from .clinical import build_clinical_router
from .database import check_pool, create_pool
from .patient_portal import build_patient_portal_router
from .routers.auth import router as auth_router
from .routers.medications import build_medications_router
from .routers.rules import build_rules_router


def create_app(
    database_url: str | None = None,
    pool: ConnectionPool | None = None,
) -> FastAPI:
    owned_pool = pool if pool is not None else create_pool(database_url)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        app.state.pool = owned_pool
        if owned_pool is not None:
            owned_pool.open(wait=True, timeout=10.0)
        try:
            yield
        finally:
            if owned_pool is not None:
                owned_pool.close()

    app = FastAPI(
        title="Nhóm 27 — Demo quản lý bệnh viện",
        version="0.2.0",
        description=(
            "Demo dùng dữ liệu synthetic và PostgreSQL. Bốn module lâm sàng luôn "
            "mock_not_evaluated; không cung cấp chẩn đoán, khuyến nghị hay đơn thuốc lâm sàng."
        ),
        lifespan=lifespan,
    )
    app.state.pool = owned_pool
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173"],
        allow_methods=["GET", "POST", "PUT", "PATCH"],
        allow_headers=["Authorization", "Content-Type"],
    )

    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
        fields = sorted({".".join(str(part) for part in error["loc"]) for error in exc.errors()})
        return JSONResponse(
            status_code=422,
            content={"detail": "Dữ liệu không hợp lệ: " + ", ".join(fields)},
        )

    @app.exception_handler(psycopg.Error)
    async def database_error(request: Request, exc: psycopg.Error) -> JSONResponse:
        sqlstate = exc.sqlstate
        if sqlstate == "23505":
            status, detail = 409, "Dữ liệu bị trùng hoặc xung đột trạng thái"
        elif sqlstate in {"23503", "23514", "P0001", "22003", "22007", "22008"}:
            status, detail = 422, "Dữ liệu không thỏa điều kiện lưu trữ"
        else:
            status, detail = 503, "Cơ sở dữ liệu demo tạm thời không sẵn sàng"
        return JSONResponse(status_code=status, content={"detail": detail})

    @app.exception_handler(PoolTimeout)
    async def pool_timeout(request: Request, exc: PoolTimeout) -> JSONResponse:
        return JSONResponse(
            status_code=503,
            content={"detail": "Cơ sở dữ liệu demo tạm thời không sẵn sàng"},
        )

    @app.get("/health", tags=["System"])
    def health() -> dict[str, str]:
        if not check_pool(app.state.pool):
            raise HTTPException(status_code=503, detail="Cơ sở dữ liệu demo chưa sẵn sàng")
        return {"status": "ok", "mode": "stub", "persistence": "postgres"}

    app.include_router(auth_router)
    app.include_router(build_clinical_router())
    app.include_router(build_medications_router())
    app.include_router(build_rules_router())
    app.include_router(build_patient_portal_router())

    from .spec import contract

    app.openapi = lambda: contract(app)

    web_root = Path(__file__).resolve().parents[2] / "web"
    if web_root.is_dir():
        app.mount("/", StaticFiles(directory=web_root, html=True), name="web")

    return app


app = create_app()
