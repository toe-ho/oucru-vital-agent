"""JWT validation and role-guard FastAPI dependencies."""

from typing import Annotated
from uuid import UUID

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.errors import AppError
from app.core.settings import settings
from app.models.user_models import Role, User, UserRole

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token", auto_error=False)


def decode_jwt(token: str) -> dict:
    """Decode and validate a JWT, returning the payload dict."""
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        return payload
    except JWTError as exc:
        raise AppError(401, "InvalidToken", "Could not validate credentials.") from exc


async def get_current_user(
    token: Annotated[str | None, Depends(oauth2_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """Decode JWT and load the corresponding User from the database."""
    if not token:
        raise AppError(401, "MissingToken", "Authentication token required.")

    payload = decode_jwt(token)
    user_id: str | None = payload.get("sub")
    if not user_id:
        raise AppError(401, "InvalidToken", "Token subject missing.")

    result = await db.execute(select(User).where(User.id == UUID(user_id)))
    user = result.scalar_one_or_none()
    if user is None or user.status != "active":
        raise AppError(401, "UserNotFound", "User not found or inactive.")
    return user


async def _load_user_role_names(db: AsyncSession, user_id: UUID) -> list[str]:
    """Return list of role name strings for a user (active roles only)."""
    result = await db.execute(
        select(Role.name)
        .join(UserRole, UserRole.role_id == Role.id)
        .where(UserRole.user_id == user_id, UserRole.deleted_at.is_(None))
    )
    return list(result.scalars().all())


def require_roles(*roles: str):
    """Return a dependency that raises 403 if the current user lacks all specified roles."""

    async def _guard(
        current_user: Annotated[User, Depends(get_current_user)],
        db: Annotated[AsyncSession, Depends(get_db)],
    ) -> User:
        user_roles = await _load_user_role_names(db, current_user.id)
        if not any(r in user_roles for r in roles):
            raise AppError(403, "Forbidden", f"Requires one of roles: {list(roles)}")
        return current_user

    return _guard
