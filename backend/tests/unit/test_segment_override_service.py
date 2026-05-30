"""Unit tests for segment override service logic."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


def _make_override_event(
    event_id=None,
    segment_id=None,
    label="accept",
    supersedes=None,
) -> MagicMock:
    event = MagicMock()
    event.id = event_id or uuid.uuid4()
    event.segment_id = segment_id or uuid.uuid4()
    event.label = label
    event.supersedes_override_event_id = supersedes
    event.created_at = datetime.now(timezone.utc)
    return event


@pytest.mark.asyncio
async def test_get_active_override_returns_none_when_empty():
    """get_active_override returns None when no events exist for segment."""
    from app.services.segment_override_service import get_active_override

    db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    db.execute = AsyncMock(return_value=mock_result)

    result = await get_active_override(db, uuid.uuid4())
    assert result is None


@pytest.mark.asyncio
async def test_create_override_sets_ai_classification_unchanged():
    """Creating an override does not mutate the segment's classification field."""
    seg_id = uuid.uuid4()
    recording_id = uuid.uuid4()
    job_id = uuid.uuid4()
    user_id = uuid.uuid4()

    # Segment with fixed AI classification
    segment_classification = "reject"

    db = AsyncMock()
    # No active override exists
    no_active_result = MagicMock()
    no_active_result.scalars.return_value.all.return_value = []

    # flush and log_event are no-ops
    db.execute = AsyncMock(return_value=no_active_result)
    db.flush = AsyncMock()
    db.add = MagicMock()

    with patch("app.services.segment_override_service.audit_service.log_event", new_callable=AsyncMock):
        from app.services.segment_override_service import create_override

        event = await create_override(
            db=db,
            segment_id=seg_id,
            recording_id=recording_id,
            assessment_job_id=job_id,
            label="accept",
            reason_category="clinical_review",
            note="Segment looks acceptable on manual review",
            user_id=user_id,
        )

    # The AI classification string is unchanged (we never touch segments table)
    assert segment_classification == "reject"
    # Override event has the new label
    assert event.label == "accept"


@pytest.mark.asyncio
async def test_second_override_supersedes_first():
    """A second override event should reference the first via supersedes_override_event_id."""
    seg_id = uuid.uuid4()
    first_id = uuid.uuid4()
    first_event = _make_override_event(event_id=first_id, segment_id=seg_id, label="accept")

    db = AsyncMock()
    # First call to get_active_override returns the first event
    active_result = MagicMock()
    active_result.scalars.return_value.all.return_value = [first_event]
    db.execute = AsyncMock(return_value=active_result)
    db.flush = AsyncMock()
    db.add = MagicMock()

    created_events = []

    def capture_add(obj):
        created_events.append(obj)

    db.add.side_effect = capture_add

    with patch("app.services.segment_override_service.audit_service.log_event", new_callable=AsyncMock):
        from app.services.segment_override_service import create_override

        event = await create_override(
            db=db,
            segment_id=seg_id,
            recording_id=uuid.uuid4(),
            assessment_job_id=uuid.uuid4(),
            label="reject",
            reason_category="poor_signal",
            note="Re-reviewed and signal quality is insufficient",
            user_id=uuid.uuid4(),
        )

    assert event.supersedes_override_event_id == first_id


@pytest.mark.asyncio
async def test_effective_classification_uses_override_label():
    """get_effective_classification returns the active override label when one exists."""
    seg_id = uuid.uuid4()
    active_event = _make_override_event(segment_id=seg_id, label="reject")

    db = AsyncMock()
    active_result = MagicMock()
    active_result.scalars.return_value.all.return_value = [active_event]
    db.execute = AsyncMock(return_value=active_result)

    from app.services.segment_override_service import get_effective_classification

    result = await get_effective_classification(db, seg_id, ai_classification="accept")
    assert result == "reject"
