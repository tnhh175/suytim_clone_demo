from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Collection
from uuid import UUID

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer


@dataclass(frozen=True, slots=True)
class Actor:
    """Identity resolved from a live database session, never from request data."""

    user_id: UUID
    username: str
    role: str
    permissions: frozenset[str]


_bearer = HTTPBearer(auto_error=False)
_ROLE_SCOPES: dict[str, frozenset[str]] = {
    "doctor": frozenset({"clinical"}),
    "nurse": frozenset({"nursing"}),
    "pharmacist": frozenset({"medsafety"}),
}
_VALID_SCOPES = frozenset({"clinical", "nursing", "medsafety"})
_VALID_ROLES = frozenset({"doctor", "nurse", "pharmacist", "admin", "patient"})


def _unauthorized() -> HTTPException:
    return HTTPException(
        status_code=401,
        detail="Token không hợp lệ hoặc đã hết hạn",
        headers={"WWW-Authenticate": "Bearer"},
    )


def _actor_from_session(conn: Any, user_id: UUID, username: str) -> Actor:
    role_rows = conn.execute(
        "SELECT role_code FROM user_role WHERE user_id = %s ORDER BY role_code",
        (user_id,),
    ).fetchall()
    roles = [row[0] for row in role_rows]
    # The API contract has one active role per account. Fail closed if the
    # database has zero, duplicate, or unsupported role assignments.
    if len(roles) != 1 or roles[0] not in _VALID_ROLES:
        raise _unauthorized()
    permission_rows = conn.execute(
        "SELECT permission_code FROM user_permission WHERE user_id = %s ORDER BY permission_code",
        (user_id,),
    ).fetchall()
    permissions = frozenset(row[0] for row in permission_rows)
    return Actor(
        user_id=user_id,
        username=username,
        role=roles[0],
        permissions=permissions,
    )


def get_current_actor(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> Actor:
    """Resolve bearer session to its server-side actor; rejects expired/revoked sessions."""

    if credentials is None or credentials.scheme.lower() != "bearer":
        raise _unauthorized()
    pool = getattr(request.app.state, "pool", None)
    if pool is None:
        raise HTTPException(status_code=503, detail="Cơ sở dữ liệu chưa sẵn sàng")

    import hashlib

    token_hash = hashlib.sha256(credentials.credentials.encode("utf-8")).hexdigest()
    with pool.connection() as conn:
        row = conn.execute(
            """
            SELECT u.id, u.username, u.active, s.expires_at, s.revoked_at
            FROM auth_session AS s
            JOIN app_user AS u ON u.id = s.user_id
            WHERE s.token_hash = %s
            """,
            (token_hash,),
        ).fetchone()
        if row is None:
            raise _unauthorized()
        user_id, username, active, expires_at, revoked_at = row
        # Compare against the database clock to avoid host clock skew.
        valid = conn.execute(
            "SELECT (%s::timestamptz > now())",
            (expires_at,),
        ).fetchone()[0]
        if not active or revoked_at is not None or not valid:
            raise _unauthorized()
        return _actor_from_session(conn, user_id, username)


def require_role(actor: Actor, allowed_roles: Collection[str]) -> None:
    if actor.role not in allowed_roles:
        raise HTTPException(status_code=403, detail="Không đúng vai trò")


def require_permission(actor: Actor, permission_code: str) -> None:
    if permission_code not in actor.permissions:
        raise HTTPException(status_code=403, detail="Không có quyền thực hiện thao tác")


def require_case_access(
    conn: Any,
    actor: Actor,
    case_id: UUID | str,
    allowed_scopes: Collection[str],
) -> None:
    """Require an allowed staff scope; existence is checked first to preserve 404/403 semantics.

    Doctors may access their own case with the clinical scope, as specified by the SRS;
    other staff must have an explicit matching row in case_access. Admin and patient
    roles never gain staff access through this helper.
    """

    try:
        case_uuid = case_id if isinstance(case_id, UUID) else UUID(str(case_id))
    except (TypeError, ValueError, AttributeError):
        raise HTTPException(status_code=404, detail="Không tìm thấy ca") from None

    case_row = conn.execute(
        "SELECT owner_id FROM patient_case WHERE id = %s",
        (case_uuid,),
    ).fetchone()
    if case_row is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy ca")

    role_scopes = _ROLE_SCOPES.get(actor.role, frozenset())
    requested = frozenset(scope for scope in allowed_scopes if scope in _VALID_SCOPES)
    eligible_scopes = sorted(role_scopes.intersection(requested))
    if not eligible_scopes:
        raise HTTPException(status_code=403, detail="Không có quyền truy cập ca")

    access_row = conn.execute(
        """
        SELECT 1
        FROM case_access
        WHERE case_id = %s
          AND user_id = %s
          AND access_scope = ANY(%s::varchar[])
        LIMIT 1
        """,
        (case_uuid, actor.user_id, eligible_scopes),
    ).fetchone()
    is_clinical_owner = (
        actor.role == "doctor"
        and "clinical" in eligible_scopes
        and str(case_row[0]) == str(actor.user_id)
    )
    if access_row is None and not is_clinical_owner:
        raise HTTPException(status_code=403, detail="Không có quyền truy cập ca")
