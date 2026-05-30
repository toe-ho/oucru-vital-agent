"""REST endpoints for assessment job creation, status polling, and result retrieval."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.auth_dependencies import get_current_user
from app.core.database import async_session_factory, get_db
from app.core.errors import AppError
from app.models.log_models import AgentLog
from app.models.segment_models import Segment, SqiResult
from app.models.user_models import User
from app.schemas.assessment_schemas import (
    AgentLogEntry,
    AssessJobRequest,
    AssessJobResponse,
    JobResultsResponse,
    SegmentResult,
)
from app.services.assessment_service import (
    create_assessment_job,
    get_job_results,
    run_assessment,
)
from app.services.agent_log_service import get_logs_for_job

router = APIRouter(tags=["assessment"])


@router.post("/", response_model=AssessJobResponse, status_code=202)
async def create_assessment(
    request: AssessJobRequest,
    background_tasks: BackgroundTasks,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AssessJobResponse:
    """Create an assessment job and start background processing."""
    job = await create_assessment_job(db, request, current_user.id)
    await db.commit()
    background_tasks.add_task(run_assessment, job.id, async_session_factory)
    return AssessJobResponse.model_validate(job)


@router.get("/{job_id}", response_model=AssessJobResponse)
async def get_assessment_status(
    job_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AssessJobResponse:
    """Poll the status of an assessment job."""
    from app.models.recording_models import AssessmentJob
    result = await db.execute(select(AssessmentJob).where(AssessmentJob.id == job_id))
    job = result.scalar_one_or_none()
    if job is None:
        raise AppError(404, "JobNotFound", f"Assessment job {job_id} not found.")
    return AssessJobResponse.model_validate(job)


@router.get("/{job_id}/results", response_model=JobResultsResponse)
async def get_assessment_results(
    job_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> JobResultsResponse:
    """Return full results with segments and summary for a completed job."""
    return await get_job_results(db, job_id)


@router.get("/{job_id}/logs", response_model=list[AgentLogEntry])
async def get_assessment_logs(
    job_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[AgentLogEntry]:
    """Return agent execution logs for a job, ordered by step_number."""
    logs = await get_logs_for_job(db, job_id)
    return [AgentLogEntry.model_validate(log) for log in logs]


@router.get("/{job_id}/segments/{segment_id}", response_model=SegmentResult)
async def get_segment_detail(
    job_id: uuid.UUID,
    segment_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SegmentResult:
    """Return detail for a single segment including SQI results."""
    result = await db.execute(
        select(Segment).where(
            Segment.id == segment_id,
            Segment.assessment_job_id == job_id,
        )
    )
    segment = result.scalar_one_or_none()
    if segment is None:
        raise AppError(404, "SegmentNotFound", f"Segment {segment_id} not found in job {job_id}.")
    return SegmentResult.model_validate(segment)
