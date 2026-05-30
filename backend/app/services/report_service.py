"""Report generation, retrieval, and listing service."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.report_models import Report
from app.models.segment_models import SqiResult
from app.services import audit_service
from app.services.assessment_service import get_job_results
from app.services.report_rendering_service import render_html, render_pdf


async def generate_report(
    db: AsyncSession,
    job_id: uuid.UUID,
    user_id: uuid.UUID,
    agent_interp: dict | None = None,
) -> Report:
    """Generate and persist a Report for a completed assessment job."""
    results = await get_job_results(db, job_id)
    job_data = results.job
    summary = results.summary

    # Build per-segment detail with failed metrics
    segments_detail = []
    for seg in results.segments:
        sqi_result = await db.execute(
            select(SqiResult).where(
                SqiResult.segment_id == seg.id,
                SqiResult.passed == False,  # noqa: E712
            )
        )
        failed_metrics = [r.metric_name for r in sqi_result.scalars().all()]
        segments_detail.append(
            {
                "segment_number": seg.segment_number,
                "start_time": seg.start_time,
                "end_time": seg.end_time,
                "classification": seg.classification,
                "quality_score": seg.quality_score,
                "failed_metrics": failed_metrics,
            }
        )

    generated_at = datetime.now(timezone.utc)

    content_json = {
        "schema_version": "1.0",
        "recording_id": str(job_data.recording_id),
        "assessment_job_id": str(job_id),
        "generated_at": generated_at.isoformat(),
        "summary": {
            "accepted": summary.get("accepted_count", 0),
            "rejected": summary.get("rejected_count", 0),
            "uncomputable": summary.get("uncomputable_count", 0),
            "total": summary.get("total_segments", 0),
            "acceptance_rate_pct": summary.get("acceptance_rate_pct", 0.0),
            "verdict": summary.get("verdict", "unknown"),
        },
        "segments": segments_detail,
        "agent_interpretation": agent_interp,
        "limitations": [
            "Single-channel MVP",
            "EDF/WFDB not supported",
        ],
        "skipped_steps": [],
    }

    content_html = render_html(content_json, is_stale=False)

    # Attempt PDF render (optional — skip silently if WeasyPrint missing)
    pdf_path: str | None = None
    import tempfile, os  # noqa: E401

    try:
        tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
        tmp.close()
        success = render_pdf(content_html, tmp.name)
        pdf_path = tmp.name if success else None
        if not success:
            os.unlink(tmp.name)
    except Exception:  # noqa: BLE001
        pdf_path = None

    report = Report(
        recording_id=job_data.recording_id,
        assessment_job_id=job_id,
        title=f"Assessment Report — Job {job_id}",
        content_json=content_json,
        content_html=content_html,
        pdf_file_path=pdf_path,
        json_schema_version="1.0",
        generated_at=generated_at,
        created_by=user_id,
    )
    db.add(report)
    await db.flush()

    await audit_service.log_event(
        db,
        actor_user_id=user_id,
        action="report_generated",
        entity_type="report",
        entity_id=report.id,
        details={"assessment_job_id": str(job_id)},
    )
    return report


async def get_report(db: AsyncSession, report_id: uuid.UUID) -> Report | None:
    """Load a single Report by ID."""
    result = await db.execute(
        select(Report).where(Report.id == report_id, Report.deleted_at.is_(None))
    )
    return result.scalar_one_or_none()


async def list_reports_for_recording(
    db: AsyncSession, recording_id: uuid.UUID
) -> list[Report]:
    """Return all non-deleted reports for a recording, newest first."""
    result = await db.execute(
        select(Report)
        .where(Report.recording_id == recording_id, Report.deleted_at.is_(None))
        .order_by(Report.generated_at.desc())
    )
    return list(result.scalars().all())
