from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Callable

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.session import get_db
from app.exceptions import ForbiddenError, UnauthorizedError
from app.models.user import User, UserRole, Role

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token", auto_error=False)


async def get_current_user(
    token: str | None = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    if not token:
        raise UnauthorizedError()
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
        user_id: str | None = payload.get("sub")
        if not user_id:
            raise UnauthorizedError()
    except JWTError:
        raise UnauthorizedError("Invalid token")

    import uuid
    user = await db.get(User, uuid.UUID(user_id))
    if not user or not user.is_active:
        raise UnauthorizedError("User not found or inactive")
    return user


async def _get_user_role_names(user: User, db: AsyncSession) -> list[str]:
    result = await db.execute(
        select(Role.name)
        .join(UserRole, UserRole.role_id == Role.id)
        .where(UserRole.user_id == user.id)
    )
    return [row[0] for row in result.all()]


def require_roles(*roles: str) -> Callable:
    async def dependency(
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ) -> User:
        user_roles = await _get_user_role_names(current_user, db)
        if not any(r in user_roles for r in roles):
            raise ForbiddenError(f"Required role(s): {list(roles)}")
        return current_user
    return dependency
