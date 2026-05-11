from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies import get_current_user, require_roles
from app.exceptions import ValidationError
from app.models.user import User
from app.services.settings_service import get_thresholds, update_thresholds

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("/thresholds")
async def get_thresholds_endpoint(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    thresholds = await get_thresholds(db)
    return {"thresholds": thresholds}


@router.put("/thresholds")
async def update_thresholds_endpoint(
    body: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("admin")),
):
    thresholds = body.get("thresholds", {})
    if not thresholds:
        raise ValidationError("thresholds object must not be empty")

    for metric, rules in thresholds.items():
        min_v = rules.get("min")
        max_v = rules.get("max")
        if min_v is not None and max_v is not None and min_v > max_v:
            raise ValidationError(f"min > max for metric '{metric}'")

    updated = await update_thresholds(thresholds, current_user.id, db)
    return {
        "status": "updated",
        "metrics_updated": list(updated.keys()),
    }
