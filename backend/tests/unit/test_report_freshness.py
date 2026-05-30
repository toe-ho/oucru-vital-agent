"""Unit tests for report freshness detection."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


def _make_report(generated_at: datetime, assessment_job_id=None) -> MagicMock:
    report = MagicMock()
    report.generated_at = generated_at
    report.assessment_job_id = assessment_job_id or uuid.uuid4()
    return report


@pytest.mark.asyncio
async def test_report_not_stale_when_no_overrides():
    """A report with no override events after generated_at is not stale."""
    from app.services.report_freshness_service import is_report_stale

    job_id = uuid.uuid4()
    seg_id = uuid.uuid4()
    generated_at = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    report = _make_report(generated_at, job_id)

    db = AsyncMock()
    # First execute: returns segment IDs
    seg_row_mock = MagicMock()
    seg_row_mock.all.return_value = [(seg_id,)]
    # Second execute: no override events found (returns None)
    override_row_mock = MagicMock()
    override_row_mock.scalar_one_or_none.return_value = None

    db.execute = AsyncMock(side_effect=[seg_row_mock, override_row_mock])

    result = await is_report_stale(db, report)
    assert result is False


@pytest.mark.asyncio
async def test_report_stale_when_override_after_generated_at():
    """A report is stale when an override was created after generated_at."""
    from app.services.report_freshness_service import is_report_stale

    job_id = uuid.uuid4()
    seg_id = uuid.uuid4()
    override_id = uuid.uuid4()
    generated_at = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    report = _make_report(generated_at, job_id)

    db = AsyncMock()
    seg_row_mock = MagicMock()
    seg_row_mock.all.return_value = [(seg_id,)]
    override_row_mock = MagicMock()
    override_row_mock.scalar_one_or_none.return_value = override_id  # found an override

    db.execute = AsyncMock(side_effect=[seg_row_mock, override_row_mock])

    result = await is_report_stale(db, report)
    assert result is True
