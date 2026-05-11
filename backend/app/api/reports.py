import uuid

from fastapi import APIRouter, BackgroundTasks, Depends
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies import get_current_user, require_roles
from app.exceptions import NotFoundError, ValidationError
from app.models.assessment import AssessmentJob
from app.models.report import Report
from app.models.user import User

router = APIRouter(prefix="/reports", tags=["reports"])


@router.post("/generate", status_code=202)
async def generate_report(
    body: dict,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "researcher")),
):
    job_id = uuid.UUID(body["assessment_job_id"])
    format_ = body.get("format", "json")
    include_plots = body.get("include_waveform_plots", True)

    if format_ not in ("json", "html", "pdf"):
        raise ValidationError("format must be 'json', 'html', or 'pdf'")

    job = await db.get(AssessmentJob, job_id)
    if not job:
        raise NotFoundError(f"Assessment job {job_id} not found")
    if job.status != "completed":
        raise ValidationError(f"Assessment job must be completed (current: {job.status})")

    from app.models.report import Report
    report = Report(
        assessment_job_id=job_id,
        recording_id=job.recording_id,
        status="generating",
        format=format_,
        include_waveform_plots=include_plots,
        created_by=current_user.id,
    )
    db.add(report)
    await db.commit()
    await db.refresh(report)

    from app.services.report_service import generate_report as svc_generate
    background_tasks.add_task(svc_generate, job_id, format_, include_plots, current_user.id, db.__class__())

    return {
        "report_id": str(report.id),
        "assessment_job_id": str(job_id),
        "recording_id": str(job.recording_id),
        "status": "generating",
        "format": format_,
    }


@router.get("/{report_id}")
async def get_report(
    report_id: uuid.UUID,
    format: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    report = await db.get(Report, report_id)
    if not report:
        raise NotFoundError(f"Report {report_id} not found")

    if report.status == "generating":
        return {"report_id": str(report_id), "status": "generating"}

    fmt = format or report.format

    if fmt == "pdf" and report.pdf_file_path:
        return FileResponse(
            report.pdf_file_path,
            media_type="application/pdf",
            filename=f"quality-report-{report.recording_id}.pdf",
        )

    if fmt == "html":
        return {
            "report_id": str(report.id),
            "recording_id": str(report.recording_id),
            "assessment_job_id": str(report.assessment_job_id),
            "format": "html",
            "generated_at": report.created_at.isoformat(),
            "content_html": report.content_html,
        }

    return {
        "report_id": str(report.id),
        "recording_id": str(report.recording_id),
        "assessment_job_id": str(report.assessment_job_id),
        "format": "json",
        "generated_at": report.created_at.isoformat(),
        "content_json": report.content_json,
    }
