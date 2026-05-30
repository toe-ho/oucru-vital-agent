"""REST endpoints for segment override creation, history, and effective classification."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.auth_dependencies import get_current_user, require_roles
from app.core.database import get_db
from app.core.errors import AppError
from app.models.segment_models import Segment
from app.models.user_models import User
from app.schemas.report_schemas import OverrideCreateRequest, OverrideResponse
from app.services import segment_override_service

router = APIRouter(tags=["segment-overrides"])


async def _load_segment(db: AsyncSession, segment_id: uuid.UUID) -> Segment:
    """Load a Segment by ID or raise 404."""
    result = await db.execute(select(Segment).where(Segment.id == segment_id))
    segment = result.scalar_one_or_none()
    if segment is None:
        raise AppError(404, "SegmentNotFound", f"Segment {segment_id} not found.")
    return segment


@router.post(
    "/{segment_id}/overrides",
    response_model=OverrideResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_override(
    segment_id: uuid.UUID,
    body: OverrideCreateRequest,
    current_user: Annotated[User, Depends(require_roles("reviewer", "admin"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> OverrideResponse:
    """Create a new override event for a segment. Requires reviewer or admin role."""
    segment = await _load_segment(db, segment_id)

    event = await segment_override_service.create_override(
        db=db,
        segment_id=segment_id,
        recording_id=segment.recording_id,
        assessment_job_id=segment.assessment_job_id,
        label=body.label,
        reason_category=body.reason_category,
        note=body.note,
        user_id=current_user.id,
    )
    await db.commit()
    return OverrideResponse.model_validate(event)


@router.get("/{segment_id}/overrides", response_model=list[OverrideResponse])
async def list_override_history(
    segment_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[OverrideResponse]:
    """Return the full override history for a segment (append-only audit trail)."""
    await _load_segment(db, segment_id)
    events = await segment_override_service.get_override_history(db, segment_id)
    return [OverrideResponse.model_validate(e) for e in events]


@router.get("/{segment_id}/effective-classification")
async def get_effective_classification(
    segment_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    """Return the effective classification, considering active overrides."""
    segment = await _load_segment(db, segment_id)
    active = await segment_override_service.get_active_override(db, segment_id)
    effective = active.label if active else segment.classification
    return {
        "ai_classification": segment.classification,
        "effective_classification": effective,
        "has_active_override": active is not None,
    }
