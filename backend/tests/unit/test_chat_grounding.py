"""Unit tests for chat_grounding_service."""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_recording(recording_id=None):
    rec = MagicMock()
    rec.id = recording_id or uuid.uuid4()
    rec.filename = "test_ecg.csv"
    rec.signal_type = "ecg"
    rec.sampling_rate = 250.0
    rec.duration_seconds = 30.0
    rec.status = "completed"
    rec.deleted_at = None
    return rec


def _make_job(recording_id=None, status="completed"):
    job = MagicMock()
    job.id = uuid.uuid4()
    job.recording_id = recording_id or uuid.uuid4()
    job.status = status
    return job


def _make_segment(job_id=None, number=1, classification="accept"):
    seg = MagicMock()
    seg.id = uuid.uuid4()
    seg.assessment_job_id = job_id or uuid.uuid4()
    seg.segment_number = number
    seg.start_time = float((number - 1) * 30)
    seg.end_time = float(number * 30)
    seg.classification = classification
    seg.quality_score = 0.85
    return seg


def _db_returning(*rows):
    """Build a mock db that returns given rows from .execute()."""
    db = AsyncMock()

    call_results = []
    for row_group in rows:
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = row_group[0] if len(row_group) == 1 else None
        mock_result.scalars.return_value.all.return_value = list(row_group)
        mock_result.scalars.return_value.one_or_none = MagicMock(
            return_value=row_group[0] if len(row_group) == 1 else None
        )
        call_results.append(mock_result)

    db.execute = AsyncMock(side_effect=call_results)
    return db


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_retrieve_context_returns_recording_info():
    """retrieve_context must include filename, signal_type, sampling_rate."""
    from unittest.mock import patch

    rec_id = uuid.uuid4()
    rec = _make_recording(rec_id)
    job = _make_job(rec_id)

    # DB call order: recording lookup, job lookup, segments, failed SQI metrics
    db = AsyncMock()
    results = []

    # recording
    r1 = MagicMock()
    r1.scalar_one_or_none.return_value = rec
    results.append(r1)
    # job (latest completed)
    r2 = MagicMock()
    r2.scalar_one_or_none.return_value = job
    results.append(r2)
    # segments
    seg = _make_segment(job.id, number=1, classification="accept")
    r3 = MagicMock()
    r3.scalars.return_value.all.return_value = [seg]
    results.append(r3)
    # override events for get_effective_classification
    r4 = MagicMock()
    r4.scalars.return_value.all.return_value = []
    results.append(r4)
    # failed SQI metrics
    r5 = MagicMock()
    r5.scalars.return_value.all.return_value = []
    results.append(r5)
    # report title (no report_id)
    # Not called since report_id=None

    db.execute = AsyncMock(side_effect=results)

    from app.services.chat_grounding_service import retrieve_context
    ctx = await retrieve_context(db, rec_id)

    assert ctx["recording"] is not None
    assert ctx["recording"]["filename"] == "test_ecg.csv"
    assert ctx["recording"]["signal_type"] == "ecg"
    assert ctx["recording"]["sampling_rate"] == 250.0
    assert ctx["job_summary"] is not None
    assert ctx["job_summary"]["total_segments"] == 1


@pytest.mark.asyncio
async def test_retrieve_context_truncates_to_50_segments():
    """retrieve_context must cap segments at 50 via DB LIMIT."""
    from app.services.chat_grounding_service import _MAX_SEGMENTS
    assert _MAX_SEGMENTS == 50


@pytest.mark.asyncio
async def test_no_fabricated_values_in_context():
    """Context values must come from DB objects, not hardcoded strings."""
    rec_id = uuid.uuid4()
    rec = _make_recording(rec_id)
    # Use unique values to verify they pass through unchanged
    rec.filename = "unique_ecg_file_xyz.csv"
    rec.sampling_rate = 512.0
    rec.duration_seconds = 120.5

    db = AsyncMock()
    results = []

    r1 = MagicMock()
    r1.scalar_one_or_none.return_value = rec
    results.append(r1)
    # No completed job — returns None
    r2 = MagicMock()
    r2.scalar_one_or_none.return_value = None
    results.append(r2)

    db.execute = AsyncMock(side_effect=results)

    from app.services.chat_grounding_service import retrieve_context
    ctx = await retrieve_context(db, rec_id)

    # Values must match exactly what came from DB
    assert ctx["recording"]["filename"] == "unique_ecg_file_xyz.csv"
    assert ctx["recording"]["sampling_rate"] == 512.0
    assert ctx["recording"]["duration_seconds"] == 120.5
    # No job means null summary
    assert ctx["job_summary"] is None
    assert ctx["segments"] == []
