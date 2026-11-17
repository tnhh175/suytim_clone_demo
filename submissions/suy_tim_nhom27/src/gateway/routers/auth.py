from __future__ import annotations

import base64
import hashlib
import hmac
import os
import secrets
import threading
import time
from collections import deque
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import BaseModel, ConfigDict, Field, field_validator
from psycopg.errors import UniqueViolation

from ..authorization import Actor, _VALID_ROLES, _bearer, get_current_actor


class LoginPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    username: str = Field(min_length=1, max_length=80)
    password: str = Field(min_length=1, max_length=200)
    selected_role: Literal["doctor", "nurse", "pharmacist", "patient", "admin"] | None = None


class RegistrationPayload(BaseModel):
    """Public signup only creates a fresh synthetic patient, never a staff actor."""

    model_config = ConfigDict(extra="forbid")
    username: str = Field(min_length=3, max_length=80, pattern=r"^[A-Za-z0-9][A-Za-z0-9_.-]{2,79}$")
    password: str = Field(min_length=12, max_length=128)
    age: int = Field(ge=0, le=120, strict=True)
    sex: Literal["male", "female", "unknown"] = "unknown"

    @field_validator("username", mode="before")
    @classmethod
    def trim_username(cls, value):
        return value.strip() if isinstance(value, str) else value

    @field_validator("password")
    @classmethod
    def reject_blank_password(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Mật khẩu không được chỉ gồm khoảng trắng")
        return value


class RegistrationResponse(BaseModel):
    username: str
    role: Literal["patient"] = "patient"


class AttemptWindow:
    """Bounded rolling window shared by all clients of one app instance."""

    def __init__(self, per_client: int, total: int, detail: str):
        self.lock = threading.Lock()
        self.attempts: deque[tuple[float, str]] = deque()
        self.per_client = per_client
        self.total = total
        self.detail = detail

    def check(self, client: str) -> None:
        with self.lock:
            now = time.monotonic()
            while self.attempts and self.attempts[0][0] <= now - 60:
                self.attempts.popleft()
            if len(self.attempts) >= self.total or sum(ip == client for _, ip in self.attempts) >= self.per_client:
                raise HTTPException(status_code=429, detail=self.detail, headers={"Retry-After": "60"})
            self.attempts.append((now, client))


class RegistrationLimiter(AttemptWindow):
    def __init__(self):
        super().__init__(8, 64, "Đã thử đăng ký nhiều lần. Thử lại sau một phút.")


class LoginLimiter(AttemptWindow):
    def __init__(self):
        super().__init__(12, 48, "Đã thử đăng nhập nhiều lần. Thử lại sau một phút.")
        self.slots = threading.BoundedSemaphore(2)

    @contextmanager
    def attempt(self, client: str):
        if not self.slots.acquire(blocking=False):
            raise HTTPException(
                status_code=429,
                detail="Đang xử lý nhiều lượt đăng nhập. Thử lại sau.",
                headers={"Retry-After": "1"},
            )
        try:
            self.check(client)
            yield
        finally:
            self.slots.release()


def _client_host(request: Request) -> str:
    # Use the ASGI server's client address after its trusted proxy handling.
    return request.client.host if request.client else "unknown"


class TokenResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int = 3600


class ActorResponse(BaseModel):
    user_id: str
    username: str
    role: str
    permissions: list[str]


class LogoutResponse(BaseModel):
    status: Literal["revoked"] = "revoked"


router = APIRouter(prefix="/api/v1/auth", tags=["Identity"])
registration_router = APIRouter(prefix="/api/v1/auth", tags=["Identity"])
_SESSION_TTL_SECONDS = 3600
_DUMMY_SALT = b"hospital-demo-missing-account"
LOGIN_RESPONSES = {
    429: {
        "description": "Vượt giới hạn số lượt đăng nhập hoặc số lượt xử lý đồng thời",
        "headers": {"Retry-After": {"schema": {"type": "integer"}, "description": "Số giây trước khi thử lại"}},
        "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Error"}}},
    },
}


def verify_password(password: str, encoded_hash: str) -> bool:
    """Verify seed-compatible pbkdf2_sha256$iterations$salt$digest strings."""

    try:
        algorithm, iterations_text, salt_text, digest_text = encoded_hash.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        iterations = int(iterations_text)
        if not 1 <= iterations <= 2_000_000:
            return False
        salt = base64.b64decode(salt_text + "=" * (-len(salt_text) % 4), validate=True)
        expected = base64.b64decode(digest_text + "=" * (-len(digest_text) % 4), validate=True)
        if not salt or not expected or len(expected) > 64:
            return False
        candidate = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations, len(expected))
        return hmac.compare_digest(candidate, expected)
    except (AttributeError, UnicodeError, ValueError, TypeError):
        return False


def _burn_password_verification(password: str) -> None:
    # Keep nonexistent usernames close to the normal password verification path.
    hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), _DUMMY_SALT, 600_000, 32)


def _pool(request: Request):
    pool = getattr(request.app.state, "pool", None)
    if pool is None:
        raise HTTPException(status_code=503, detail="Cơ sở dữ liệu chưa sẵn sàng")
    return pool


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 600_000, 32)
    return "pbkdf2_sha256$600000$" + base64.b64encode(salt).decode("ascii") + "$" + base64.b64encode(digest).decode("ascii")


@registration_router.post(
    "/register", response_model=RegistrationResponse, status_code=201,
    responses={409: {"description": "Tên đăng nhập đã được sử dụng"}, 429: {"description": "Vượt giới hạn đăng ký demo"}, 503: {"description": "Cơ sở dữ liệu hoặc bác sĩ phụ trách chưa sẵn sàng"}},
)
def register(body: RegistrationPayload, request: Request) -> RegistrationResponse:
    # The limiter is initialized by create_app; standalone router users must opt
    # into the same bounded limiter rather than disabling the public guard.
    limiter = getattr(request.app.state, "registration_limiter", None)
    if limiter is None:
        raise HTTPException(status_code=503, detail="Đăng ký demo chưa được cấu hình")
    limiter.check(_client_host(request))
    owner_username = os.getenv("HF_REGISTRATION_DOCTOR_USERNAME", "doctor_demo")
    encoded_hash = hash_password(body.password)
    try:
        with _pool(request).connection() as conn:
            # Existing runtime membership grants SET but not inherited table-owner
            # rights. Elevation is transaction-local, as in the clinical repository.
            conn.execute("SET LOCAL ROLE hf_demo_owner")
            owner = conn.execute(
                """SELECT u.id FROM app_user u
                   WHERE u.username = %s AND u.active
                     AND EXISTS (SELECT 1 FROM user_role r WHERE r.user_id = u.id AND r.role_code = 'doctor')
                     AND NOT EXISTS (SELECT 1 FROM user_role r WHERE r.user_id = u.id AND r.role_code <> 'doctor')
                   FOR SHARE OF u""",
                (owner_username,),
            ).fetchone()
            if owner is None:
                raise HTTPException(status_code=503, detail="Bác sĩ phụ trách hồ sơ demo chưa được cấu hình hợp lệ")
            user = conn.execute(
                "INSERT INTO app_user (username, password_hash) VALUES (%s, %s) RETURNING id",
                (body.username, encoded_hash),
            ).fetchone()
            conn.execute("INSERT INTO user_role (user_id, role_code) VALUES (%s, 'patient')", (user["id"],))
            profile = conn.execute(
                """INSERT INTO patient_case (synthetic_code, age, sex, owner_id)
                   VALUES (%s, %s, %s, %s) RETURNING id""",
                ("SYN-" + secrets.token_hex(10).upper(), body.age, body.sex, owner["id"]),
            ).fetchone()
            conn.execute("INSERT INTO patient_account (user_id, case_id) VALUES (%s, %s)", (user["id"], profile["id"]))
    except UniqueViolation as exc:
        if exc.diag.constraint_name == "app_user_username_key":
            raise HTTPException(status_code=409, detail="Tên đăng nhập đã được sử dụng. Chọn tên khác.") from None
        raise
    return RegistrationResponse(username=body.username)


@router.post("/token", response_model=TokenResponse, responses=LOGIN_RESPONSES)
def login(body: LoginPayload, request: Request) -> TokenResponse:
    limiter = getattr(request.app.state, "login_limiter", None)
    if limiter is None:
        raise HTTPException(status_code=503, detail="Đăng nhập chưa được cấu hình")
    with limiter.attempt(_client_host(request)):
        return _login(body, _pool(request))


def _login(body: LoginPayload, pool) -> TokenResponse:
    with pool.connection() as conn:
        row = conn.execute(
            "SELECT id AS user_id, password_hash, active FROM app_user WHERE username = %s",
            (body.username,),
        ).fetchone()

    # PBKDF2 uses CPU without holding a connection for either account path.
    if row is None:
        _burn_password_verification(body.password)
        raise HTTPException(status_code=401, detail="Thông tin đăng nhập không hợp lệ")
    if not verify_password(body.password, row["password_hash"]) or not row["active"]:
        raise HTTPException(status_code=401, detail="Thông tin đăng nhập không hợp lệ")

    token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    expires_at = datetime.now(timezone.utc) + timedelta(seconds=_SESSION_TTL_SECONDS)
    allowed_roles = [body.selected_role] if body.selected_role else sorted(_VALID_ROLES)
    # Check the verified account and its current single role at the insertion snapshot.
    with pool.connection() as conn:
        session = conn.execute(
            """
            INSERT INTO auth_session (user_id, token_hash, expires_at)
            SELECT u.id, %s, %s
            FROM app_user AS u
            WHERE u.id = %s AND u.username = %s AND u.password_hash = %s AND u.active
              AND (SELECT min(role_code) FROM user_role WHERE user_id = u.id
                   HAVING count(*) = 1) = ANY(%s::text[])
            RETURNING user_id
            """,
            (token_hash, expires_at, row["user_id"], body.username, row["password_hash"], allowed_roles),
        ).fetchone()
        if session is None:
            raise HTTPException(status_code=401, detail="Thông tin đăng nhập không hợp lệ")
    return TokenResponse(access_token=token)


@router.post("/logout", response_model=LogoutResponse)
def logout(
    request: Request,
    actor: Actor = Depends(get_current_actor),
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> LogoutResponse:
    if credentials is None:
        raise HTTPException(status_code=401, detail="Token không hợp lệ")
    token_hash = hashlib.sha256(credentials.credentials.encode("utf-8")).hexdigest()
    with _pool(request).connection() as conn:
        conn.execute(
            """
            UPDATE auth_session
            SET revoked_at = now()
            WHERE token_hash = %s AND user_id = %s AND revoked_at IS NULL
            """,
            (token_hash, actor.user_id),
        )
    return LogoutResponse()


@router.get("/me", response_model=ActorResponse)
def me(actor: Actor = Depends(get_current_actor)) -> ActorResponse:
    return ActorResponse(
        user_id=str(actor.user_id),
        username=actor.username,
        role=actor.role,
        permissions=sorted(actor.permissions),
    )
