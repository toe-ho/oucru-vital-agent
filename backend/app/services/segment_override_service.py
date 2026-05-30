"""Segment override CRUD: create, query active override, effective classification."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.segment_models import SegmentOverrideEvent
from app.services import audit_service


async def get_active_override(
    db: AsyncSession, segment_id: uuid.UUID
) -> SegmentOverrideEvent | None:
    """Return the newest override that has NOT been superseded, or None."""
    # Active = exists no other event that references this one as superseded
    all_result = await db.execute(
        select(SegmentOverrideEvent)
        .where(SegmentOverrideEvent.segment_id == segment_id)
        .order_by(SegmentOverrideEvent.created_at.desc())
    )
    events = list(all_result.scalars().all())
    if not events:
        return None

    # Collect IDs that are referenced as superseded by another event
    superseded_ids = {
        e.supersedes_override_event_id
        for e in events
        if e.supersedes_override_event_id is not None
    }

    for event in events:
        if event.id not in superseded_ids:
            return event
    return None


async def get_effective_classification(
    db: AsyncSession, segment_id: uuid.UUID, ai_classification: str
) -> str:
    """Return active override label if one exists, else the original AI classification."""
    active = await get_active_override(db, segment_id)
    return active.label if active is not None else ai_classification


async def create_override(
    db: AsyncSession,
    segment_id: uuid.UUID,
    recording_id: uuid.UUID,
    assessment_job_id: uuid.UUID,
    label: str,
    reason_category: str,
    note: str,
    user_id: uuid.UUID,
) -> SegmentOverrideEvent:
    """Insert a new SegmentOverrideEvent, chaining from the current active override."""
    current_active = await get_active_override(db, segment_id)

    event = SegmentOverrideEvent(
        segment_id=segment_id,
        recording_id=recording_id,
        assessment_job_id=assessment_job_id,
        label=label,
        reason_category=reason_category,
        note=note,
        supersedes_override_event_id=current_active.id if current_active else None,
        created_by=user_id,
    )
    db.add(event)
    await db.flush()

    await audit_service.log_event(
        db,
        actor_user_id=user_id,
        action="segment_overridden",
        entity_type="segment",
        entity_id=segment_id,
        details={
            "label": label,
            "reason_category": reason_category,
            "override_event_id": str(event.id),
        },
    )
    return event


async def get_override_history(
    db: AsyncSession, segment_id: uuid.UUID
) -> list[SegmentOverrideEvent]:
    """Return all override events for a segment, oldest first."""
    result = await db.execute(
        select(SegmentOverrideEvent)
        .where(SegmentOverrideEvent.segment_id == segment_id)
        .order_by(SegmentOverrideEvent.created_at.asc())
    )
    return list(result.scalars().all())
