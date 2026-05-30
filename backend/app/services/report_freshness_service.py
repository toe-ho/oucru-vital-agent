"""Report freshness detection: checks if overrides were applied after report generation."""

from __future__ import annotations

import uuid
from datetime import timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.report_models import Report
from app.models.segment_models import Segment, SegmentOverrideEvent


async def is_report_stale(db: AsyncSession, report: Report) -> bool:
    """Return True if any SegmentOverrideEvent for this job was created after report.generated_at."""
    if report.generated_at is None or report.assessment_job_id is None:
        return False

    # Get all segment IDs belonging to this assessment job
    seg_result = await db.execute(
        select(Segment.id).where(Segment.assessment_job_id == report.assessment_job_id)
    )
    segment_ids = [row[0] for row in seg_result.all()]
    if not segment_ids:
        return False

    # Check for any override event after report generation
    generated_at = report.generated_at
    # Make timezone-aware for comparison if naive
    if generated_at.tzinfo is None:
        generated_at = generated_at.replace(tzinfo=timezone.utc)

    override_result = await db.execute(
        select(SegmentOverrideEvent.id)
        .where(
            SegmentOverrideEvent.segment_id.in_(segment_ids),
            SegmentOverrideEvent.created_at > generated_at,
        )
        .limit(1)
    )
    return override_result.scalar_one_or_none() is not None


async def get_freshness_status(db: AsyncSession, report: Report) -> dict:
    """Return freshness metadata dict with is_stale flag and timestamps."""
    if report.assessment_job_id is None:
        return {
            "is_stale": False,
            "report_generated_at": report.generated_at.isoformat() if report.generated_at else None,
            "latest_override_at": None,
        }

    seg_result = await db.execute(
        select(Segment.id).where(Segment.assessment_job_id == report.assessment_job_id)
    )
    segment_ids = [row[0] for row in seg_result.all()]

    latest_override_at = None
    if segment_ids:
        from sqlalchemy import func as sql_func

        latest_result = await db.execute(
            select(sql_func.max(SegmentOverrideEvent.created_at)).where(
                SegmentOverrideEvent.segment_id.in_(segment_ids)
            )
        )
        latest_override_at = latest_result.scalar_one_or_none()

    stale = await is_report_stale(db, report)

    return {
        "is_stale": stale,
        "report_generated_at": report.generated_at.isoformat() if report.generated_at else None,
        "latest_override_at": latest_override_at.isoformat() if latest_override_at else None,
    }
