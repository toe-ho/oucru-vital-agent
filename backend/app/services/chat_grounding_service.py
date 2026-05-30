"""Retrieves grounding context for chat — summary data only, no raw arrays."""

from __future__ import annotations

import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.recording_models import AssessmentJob, Recording
from app.models.report_models import Report
from app.models.segment_models import Segment, SqiResult
from app.services.segment_override_service import get_effective_classification

_MAX_SEGMENTS = 50


async def retrieve_context(
    db: AsyncSession,
    recording_id: uuid.UUID,
    assessment_job_id: Optional[uuid.UUID] = None,
    report_id: Optional[uuid.UUID] = None,
) -> dict:
    """Build grounding context dict for the chat prompt.

    Never returns raw waveform arrays; only summary statistics and metadata.
    Truncates segments to max 50 to keep prompt size manageable.
    """
    recording_info = await _load_recording(db, recording_id)
    if recording_info is None:
        return {"recording": None, "job_summary": None, "segments": [], "failed_metric_counts": {}, "has_overrides": False, "report_title": None}

    job_summary, segments_ctx, has_overrides = await _load_job_data(db, recording_id, assessment_job_id)
    report_title = await _load_report_title(db, report_id)

    return {
        "recording": recording_info,
        "job_summary": job_summary,
        "segments": segments_ctx,
        "failed_metric_counts": _count_failed_metrics(segments_ctx),
        "has_overrides": has_overrides,
        "report_title": report_title,
    }


async def _load_recording(db: AsyncSession, recording_id: uuid.UUID) -> dict | None:
    result = await db.execute(
        select(Recording).where(Recording.id == recording_id, Recording.deleted_at.is_(None))
    )
    rec = result.scalar_one_or_none()
    if rec is None:
        return None
    return {
        "id": str(rec.id),
        "filename": rec.filename,
        "signal_type": rec.signal_type,
        "sampling_rate": rec.sampling_rate,
        "duration_seconds": rec.duration_seconds,
        "status": rec.status,
    }


async def _load_job_data(
    db: AsyncSession,
    recording_id: uuid.UUID,
    assessment_job_id: Optional[uuid.UUID],
) -> tuple[dict | None, list[dict], bool]:
    """Returns (job_summary, segments_ctx, has_overrides)."""
    job = await _resolve_job(db, recording_id, assessment_job_id)
    if job is None:
        return None, [], False

    result = await db.execute(
        select(Segment)
        .where(Segment.assessment_job_id == job.id)
        .order_by(Segment.segment_number)
        .limit(_MAX_SEGMENTS)
    )
    segments = list(result.scalars().all())

    segments_ctx: list[dict] = []
    has_overrides = False

    for seg in segments:
        effective = await get_effective_classification(db, seg.id, seg.classification)
        if effective != seg.classification:
            has_overrides = True

        failed_metrics = await _get_failed_metric_names(db, seg.id)
        segments_ctx.append({
            "segment_number": seg.segment_number,
            "start_time": seg.start_time,
            "end_time": seg.end_time,
            "ai_classification": seg.classification,
            "effective_classification": effective,
            "quality_score": seg.quality_score,
            "failed_metrics": failed_metrics,
        })

    total = len(segments_ctx)
    accepted = sum(1 for s in segments_ctx if s["effective_classification"] == "accept")
    rejected = sum(1 for s in segments_ctx if s["effective_classification"] == "reject")
    uncomputable = sum(1 for s in segments_ctx if s["effective_classification"] == "uncomputable")
    rate = round(accepted / total * 100, 1) if total else 0.0
    verdict = "no_segments" if total == 0 else ("acceptable" if rate >= 60 else "poor_quality")

    job_summary = {
        "status": job.status,
        "total_segments": total,
        "accepted": accepted,
        "rejected": rejected,
        "uncomputable": uncomputable,
        "acceptance_rate_pct": rate,
        "verdict": verdict,
    }
    return job_summary, segments_ctx, has_overrides


async def _resolve_job(
    db: AsyncSession,
    recording_id: uuid.UUID,
    assessment_job_id: Optional[uuid.UUID],
) -> AssessmentJob | None:
    if assessment_job_id is not None:
        r = await db.execute(select(AssessmentJob).where(AssessmentJob.id == assessment_job_id))
        return r.scalar_one_or_none()
    # Fall back to latest completed job
    r = await db.execute(
        select(AssessmentJob)
        .where(
            AssessmentJob.recording_id == recording_id,
            AssessmentJob.status == "completed",
        )
        .order_by(AssessmentJob.created_at.desc())
        .limit(1)
    )
    return r.scalar_one_or_none()


async def _get_failed_metric_names(db: AsyncSession, segment_id: uuid.UUID) -> list[str]:
    r = await db.execute(
        select(SqiResult.metric_name).where(
            SqiResult.segment_id == segment_id,
            SqiResult.passed.is_(False),
        )
    )
    return list(r.scalars().all())


async def _load_report_title(
    db: AsyncSession, report_id: Optional[uuid.UUID]
) -> str | None:
    if report_id is None:
        return None
    r = await db.execute(select(Report.title).where(Report.id == report_id))
    return r.scalar_one_or_none()


def _count_failed_metrics(segments_ctx: list[dict]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for seg in segments_ctx:
        for metric in seg.get("failed_metrics", []):
            counts[metric] = counts.get(metric, 0) + 1
    return counts
