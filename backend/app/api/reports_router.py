"""REST endpoints for report generation, retrieval, and export."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.responses import HTMLResponse, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.auth_dependencies import get_current_user
from app.core.database import get_db
from app.core.errors import AppError
from app.models.user_models import User
from app.schemas.report_schemas import ReportDetail, ReportSummary
from app.services import report_freshness_service, report_service

router = APIRouter(tags=["reports"])


@router.post("/generate", response_model=ReportSummary, status_code=status.HTTP_201_CREATED)
async def generate_report(
    body: dict,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ReportSummary:
    """Generate a report for a completed assessment job."""
    job_id_raw = body.get("assessment_job_id")
    if not job_id_raw:
        raise AppError(400, "MissingField", "assessment_job_id is required.")
    try:
        job_id = uuid.UUID(str(job_id_raw))
    except ValueError as exc:
        raise AppError(400, "InvalidField", "assessment_job_id must be a valid UUID.") from exc

    report = await report_service.generate_report(db, job_id, current_user.id)
    await db.commit()
    return ReportSummary(
        id=report.id,
        recording_id=report.recording_id,
        assessment_job_id=report.assessment_job_id,
        title=report.title,
        json_schema_version=report.json_schema_version,
        generated_at=report.generated_at,
        is_stale=False,
        created_at=report.created_at,
    )


@router.get("/{report_id}", response_model=ReportDetail)
async def get_report(
    report_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ReportDetail:
    """Fetch full report detail including content_json and staleness flag."""
    report = await report_service.get_report(db, report_id)
    if report is None:
        raise AppError(404, "ReportNotFound", f"Report {report_id} not found.")
    is_stale = await report_freshness_service.is_report_stale(db, report)
    return ReportDetail(
        id=report.id,
        recording_id=report.recording_id,
        assessment_job_id=report.assessment_job_id,
        title=report.title,
        json_schema_version=report.json_schema_version,
        generated_at=report.generated_at,
        is_stale=is_stale,
        created_at=report.created_at,
        content_json=report.content_json,
        content_html=report.content_html,
    )


@router.get("/{report_id}/freshness")
async def get_report_freshness(
    report_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    """Return freshness status for a report."""
    report = await report_service.get_report(db, report_id)
    if report is None:
        raise AppError(404, "ReportNotFound", f"Report {report_id} not found.")
    return await report_freshness_service.get_freshness_status(db, report)


@router.get("/{report_id}/export/html", response_class=HTMLResponse)
async def export_report_html(
    report_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> HTMLResponse:
    """Export the report as an HTML page."""
    report = await report_service.get_report(db, report_id)
    if report is None:
        raise AppError(404, "ReportNotFound", f"Report {report_id} not found.")
    is_stale = await report_freshness_service.is_report_stale(db, report)
    from app.services.report_rendering_service import render_html

    html = render_html(report.content_json or {}, is_stale=is_stale)
    return HTMLResponse(content=html)


@router.get("/{report_id}/export/pdf")
async def export_report_pdf(
    report_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Response:
    """Export the report as a PDF. Returns 501 if WeasyPrint is not installed."""
    report = await report_service.get_report(db, report_id)
    if report is None:
        raise AppError(404, "ReportNotFound", f"Report {report_id} not found.")

    try:
        import weasyprint  # type: ignore  # noqa: F401
    except ImportError:
        raise AppError(501, "WeasyPrintUnavailable", "PDF export requires WeasyPrint.")

    import tempfile
    from app.services.report_rendering_service import render_html, render_pdf

    is_stale = await report_freshness_service.is_report_stale(db, report)
    html = render_html(report.content_json or {}, is_stale=is_stale)

    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp_path = tmp.name

    success = render_pdf(html, tmp_path)
    if not success:
        raise AppError(500, "PdfRenderFailed", "Failed to render PDF.")

    import os

    with open(tmp_path, "rb") as fh:
        pdf_bytes = fh.read()
    os.unlink(tmp_path)

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="report-{report_id}.pdf"'},
    )
