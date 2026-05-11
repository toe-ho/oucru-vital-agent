"""Build content_json, render HTML via Jinja2, convert to PDF via WeasyPrint."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path

from jinja2 import Environment, FileSystemLoader
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.assessment import AssessmentJob
from app.models.recording import Recording
from app.models.report import Report
from app.models.segment import Segment

TEMPLATES_DIR = Path(__file__).parent.parent / "templates"


async def generate_report(
    job_id: uuid.UUID,
    format: str,
    include_waveform_plots: bool,
    user_id: uuid.UUID,
    db: AsyncSession,
) -> Report:
    job = await db.get(AssessmentJob, job_id)
    if not job:
        from app.exceptions import NotFoundError
        raise NotFoundError(f"Assessment job {job_id} not found")

    report = Report(
        assessment_job_id=job_id,
        recording_id=job.recording_id,
        status="generating",
        format=format,
        include_waveform_plots=include_waveform_plots,
        created_by=user_id,
    )
    db.add(report)
    await db.commit()
    await db.refresh(report)

    try:
        content_json = await _build_content_json(job, db)
        report.content_json = content_json

        if format in ("html", "pdf"):
            html = _render_html(content_json)
            report.content_html = html

        if format == "pdf":
            pdf_path = await _render_pdf(html, str(report.id))
            report.pdf_file_path = pdf_path

        report.status = "completed"
    except Exception as e:
        report.status = "failed"
        raise

    await db.commit()
    await db.refresh(report)
    return report


async def _build_content_json(job: AssessmentJob, db: AsyncSession) -> dict:
    rec = await db.get(Recording, job.recording_id)
    segments = (await db.execute(
        select(Segment).where(Segment.assessment_job_id == job.id).order_by(Segment.segment_number)
    )).scalars().all()

    accepted = sum(1 for s in segments if s.classification == "accept")
    rejected = sum(1 for s in segments if s.classification == "reject")
    total = len(segments)

    timeline = [
        {
            "segment_number": s.segment_number,
            "start_time": s.start_time,
            "end_time": s.end_time,
            "classification": s.classification,
            "quality_score": s.quality_score,
        }
        for s in segments
    ]

    flagged_segments = [
        {
            "segment_number": s.segment_number,
            "start_time": s.start_time,
            "end_time": s.end_time,
            "quality_score": s.quality_score,
            "failed_rules": s.failed_rules,
        }
        for s in segments if s.classification == "reject"
    ]

    return {
        "summary": {
            "recording_id": str(job.recording_id),
            "assessment_job_id": str(job.id),
            "filename": rec.filename if rec else "unknown",
            "signal_type": rec.signal_type if rec else "unknown",
            "assessed_at": job.completed_at.isoformat() if job.completed_at else None,
            "total_segments": total,
            "accepted": accepted,
            "rejected": rejected,
            "acceptance_rate": round(accepted / total, 3) if total else 0,
            "overall_verdict": job.overall_verdict,
        },
        "timeline": timeline,
        "flagged_segments": flagged_segments,
        "agent_interpretation": job.agent_interpretation or "",
        "recommendations": [],
        "confidence": "low" if job.escalated else "high",
        "skipped_steps": [],
        "limitations": ["AI interpretation unavailable"] if "fallback" in (job.agent_interpretation or "") else [],
    }


def _render_html(content_json: dict) -> str:
    env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)), autoescape=True)
    template = env.get_template("report.html.j2")
    return template.render(**content_json)


async def _render_pdf(html: str, report_id: str) -> str:
    from weasyprint import HTML as WeasyHTML
    from app.config import settings

    pdf_dir = Path(settings.upload_dir) / "reports"
    pdf_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = pdf_dir / f"report-{report_id}.pdf"
    WeasyHTML(string=html).write_pdf(str(pdf_path))
    return str(pdf_path)
