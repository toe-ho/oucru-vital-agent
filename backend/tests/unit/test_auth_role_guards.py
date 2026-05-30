"""Unit tests for require_roles dependency."""

import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from app.auth.auth_dependencies import require_roles
from app.core.errors import AppError


def _make_user(status: str = "active") -> SimpleNamespace:
    """Return a lightweight mock user (avoids SQLAlchemy instrumentation)."""
    return SimpleNamespace(id=uuid.uuid4(), email="test@example.com", status=status)


async def _call_guard(guard_fn, user, role_names: list[str]):
    """Call the inner closure returned by require_roles with mocked dependencies."""
    with patch(
        "app.auth.auth_dependencies._load_user_role_names",
        new=AsyncMock(return_value=role_names),
    ):
        return await guard_fn(current_user=user, db=AsyncMock())


@pytest.mark.asyncio
async def test_require_roles_passes_when_user_has_matching_role():
    user = _make_user()
    result = await _call_guard(require_roles("admin", "researcher"), user, ["researcher"])
    assert result is user


@pytest.mark.asyncio
async def test_require_roles_raises_403_when_user_lacks_roles():
    user = _make_user()
    with pytest.raises(AppError) as exc_info:
        await _call_guard(require_roles("admin"), user, ["readonly"])
    assert exc_info.value.status_code == 403
    assert exc_info.value.error_code == "Forbidden"


@pytest.mark.asyncio
async def test_require_roles_multiple_allowed_passes_any():
    user = _make_user()
    result = await _call_guard(require_roles("admin", "reviewer"), user, ["reviewer"])
    assert result is user


@pytest.mark.asyncio
async def test_require_roles_raises_403_for_empty_role_list():
    user = _make_user()
    with pytest.raises(AppError) as exc_info:
        await _call_guard(require_roles("admin"), user, [])
    assert exc_info.value.status_code == 403
