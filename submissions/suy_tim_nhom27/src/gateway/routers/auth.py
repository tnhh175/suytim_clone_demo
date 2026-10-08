from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import BaseModel, ConfigDict, Field

from ..authorization import Actor, _bearer, _actor_from_session, get_current_actor


class LoginPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    username: str = Field(min_length=1, max_length=80)
    password: str = Field(min_length=1, max_length=200)


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
_SESSION_TTL_SECONDS = 3600
_DUMMY_SALT = b"hospital-demo-missing-account"


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


@router.post("/token", response_model=TokenResponse)
def login(body: LoginPayload, request: Request) -> TokenResponse:
    pool = _pool(request)
    with pool.connection() as conn:
        row = conn.execute(
            "SELECT id, password_hash, active FROM app_user WHERE username = %s",
            (body.username,),
        ).fetchone()
        if row is None:
            _burn_password_verification(body.password)
            raise HTTPException(status_code=401, detail="Thông tin đăng nhập không hợp lệ")

        user_id, password_hash, active = row
        password_matches = verify_password(body.password, password_hash)
        if not password_matches or not active:
            raise HTTPException(status_code=401, detail="Thông tin đăng nhập không hợp lệ")

        # Verify role cardinality and load permission claims from the database.
        actor = _actor_from_session(conn, user_id, body.username)
        token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=_SESSION_TTL_SECONDS)
        conn.execute(
            "INSERT INTO auth_session (user_id, token_hash, expires_at) VALUES (%s, %s, %s)",
            (actor.user_id, token_hash, expires_at),
        )
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
