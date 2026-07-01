"""
JWT Auth Middleware + RBAC Dependency Injection
All protected routes use require_role() dependency.
"""

import uuid
from typing import Annotated

from app.database import get_db
from app.models.user import User
from app.utils.security import decode_token, is_token_blacklisted
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

security = HTTPBearer(auto_error=False)


class CurrentUser:
    """Parsed JWT payload + DB user object"""

    def __init__(self, user: User):
        self.user = user
        self.id = user.id
        self.email = user.email
        self.role = user.role.name
        self.department_id = user.department_id
        self.is_active = user.is_active


async def _get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
    db: AsyncSession = Depends(get_db),
) -> CurrentUser:
    """
    Core auth dependency: validates JWT and loads user from DB.
    Raises 401 for any authentication failure.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if credentials is None:
        raise credentials_exception

    token = credentials.credentials
    try:
        payload = decode_token(token)
    except JWTError:
        raise credentials_exception

    # Verify token type
    if payload.get("type") != "access":
        raise credentials_exception

    # Check token blacklist
    jti = payload.get("jti")
    if jti and await is_token_blacklisted(jti):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id_str = payload.get("sub")
    try:
        user_id = uuid.UUID(user_id_str)
    except (ValueError, TypeError):
        raise credentials_exception

    # Load user from DB with role (eager load)
    result = await db.execute(
        select(User)
        .where(User.id == user_id)
        .join(User.role)
        .options(
            __import__("sqlalchemy.orm", fromlist=["joinedload"]).joinedload(User.role),
            __import__("sqlalchemy.orm", fromlist=["joinedload"]).joinedload(User.department),
        )
    )
    user = result.scalar_one_or_none()

    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated. Contact administrator.",
        )

    return CurrentUser(user)


# ─── Public dependency: any authenticated user ─────────────────────────────────
async def get_current_user(
    current: Annotated[CurrentUser, Depends(_get_current_user)],
) -> CurrentUser:
    return current


# ─── Role-based dependency factory ────────────────────────────────────────────
def require_role(allowed_roles: list[str]):
    """
    Factory: returns a FastAPI dependency that enforces role access.

    Usage:
        @router.get("/admin-only")
        async def admin_endpoint(user = Depends(require_role(["admin"]))):
            ...
    """
    async def role_checker(
        current: Annotated[CurrentUser, Depends(_get_current_user)],
    ) -> CurrentUser:
        if current.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role(s): {', '.join(allowed_roles)}",
            )
        return current

    return role_checker


# ─── Convenience aliases ───────────────────────────────────────────────────────
require_student = require_role(["student"])
require_staff = require_role(["staff", "admin"])
require_admin = require_role(["admin"])
require_staff_or_student = require_role(["student", "staff", "admin"])
