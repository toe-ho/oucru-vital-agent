"""Settings API endpoints for reading and updating application thresholds."""

from typing import Annotated

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.auth_dependencies import get_current_user, require_roles
from app.core.database import get_db
from app.core.errors import AppError
from app.models.user_models import User
from app.services import audit_service, settings_service

router = APIRouter()

_THRESHOLDS_KEY = "sqi_thresholds"


@router.get("/thresholds")
async def get_thresholds(
    _current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    """Return the sqi_thresholds setting (any authenticated role)."""
    setting = await settings_service.get_setting_by_key(db, _THRESHOLDS_KEY)
    if setting is None:
        raise AppError(404, "SettingNotFound", f"Setting '{_THRESHOLDS_KEY}' not found.")
    return {"key": setting.key, "value": setting.value, "category": setting.category}


@router.put("/thresholds")
async def update_thresholds(
    body: dict,
    request: Request,
    current_user: Annotated[User, Depends(require_roles("admin"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    """Update sqi_thresholds (admin only). Writes an audit event."""
    try:
        setting = await settings_service.update_setting(
            db, _THRESHOLDS_KEY, body, current_user.id
        )
    except KeyError as exc:
        raise AppError(404, "SettingNotFound", str(exc)) from exc

    await audit_service.log_event(
        db,
        actor_user_id=current_user.id,
        action="update_setting",
        entity_type="setting",
        entity_id=setting.id,
        details={"key": _THRESHOLDS_KEY},
        request_id=request.headers.get("x-request-id"),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    return {"key": setting.key, "value": setting.value, "category": setting.category}
