import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies import get_current_user, require_roles
from app.exceptions import NotFoundError, ValidationError
from app.models.agent_log import AgentLog
from app.models.assessment import AssessmentJob
from app.models.recording import Recording
from app.models.segment import Segment
from app.models.user import User
from app.services.assessment_service import create_job

router = APIRouter(tags=["assessments"])


@router.post("/assess", status_code=202)
async def trigger_assessment(
    body: dict,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "researcher")),
):
    recording_id = uuid.UUID(body["recording_id"])
    config = body.get("config", {})

    rec = await db.get(Recording, recording_id)
    if not rec or rec.deleted_at:
        raise NotFoundError(f"Recording {recording_id} not found")
    if rec.status not in ("uploaded", "completed", "failed"):
        raise ValidationError(f"Recording status '{rec.status}' is not eligible for assessment")

    job = await create_job(recording_id, config, current_user.id, db)

    from app.agent.orchestrator import run_assessment
    background_tasks.add_task(
        run_assessment,
        job_id=job.id,
        recording_id=recording_id,
        file_path=rec.storage_uri,
        signal_type=rec.signal_type,
        sampling_rate=rec.sampling_rate,
        subject_id=rec.subject_id,
    )

    return {
        "assessment_job_id": str(job.id),
        "recording_id": str(recording_id),
        "status": "queued",
        "estimated_duration_seconds": 45,
    }


@router.get("/assessment-jobs/{job_id}")
async def get_job_status(
    job_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    job = await db.get(AssessmentJob, job_id)
    if not job:
        raise NotFoundError(f"Assessment job {job_id} not found")

    resp = {
        "assessment_job_id": str(job.id),
        "recording_id": str(job.recording_id),
        "status": job.status,
    }
    if job.status == "processing":
        resp["progress"] = {
            "current_stage": job.current_stage,
            "segments_processed": job.processed_segments or 0,
            "total_segments": job.total_segments,
            "progress_pct": job.progress_pct or 0,
        }
    elif job.status == "completed":
        resp["started_at"] = job.started_at.isoformat() if job.started_at else None
        resp["completed_at"] = job.completed_at.isoformat() if job.completed_at else None
        resp["total_segments"] = job.total_segments
        resp["processed_segments"] = job.processed_segments
    return resp


@router.get("/assessment-jobs/{job_id}/results")
async def get_results(
    job_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    job = await db.get(AssessmentJob, job_id)
    if not job:
        raise NotFoundError(f"Assessment job {job_id} not found")
    if job.status not in ("completed", "failed"):
        raise ValidationError(f"Assessment is not completed (status: {job.status})")

    segments = (await db.execute(
        select(Segment)
        .where(Segment.assessment_job_id == job_id)
        .order_by(Segment.segment_number)
    )).scalars().all()

    accepted = sum(1 for s in segments if s.classification == "accept")
    rejected = len(segments) - accepted

    return {
        "assessment_job_id": str(job.id),
        "recording_id": str(job.recording_id),
        "status": job.status,
        "signal_type": None,
        "assessed_at": job.completed_at.isoformat() if job.completed_at else None,
        "summary": {
            "total_segments": len(segments),
            "accepted": accepted,
            "rejected": rejected,
            "uncomputable": 0,
            "acceptance_rate": round(accepted / len(segments), 3) if segments else 0,
            "overall_quality_score": job.acceptance_rate,
            "verdict": job.overall_verdict,
        },
        "segments": [_seg_summary(s) for s in segments],
        "agent_interpretation": job.agent_interpretation,
        "escalated": job.escalated,
    }


@router.get("/assessment-jobs/{job_id}/logs")
async def get_logs(
    job_id: uuid.UUID,
    stage: str | None = None,
    tool: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    job = await db.get(AssessmentJob, job_id)
    if not job:
        raise NotFoundError(f"Assessment job {job_id} not found")

    q = select(AgentLog).where(AgentLog.assessment_job_id == job_id).order_by(AgentLog.step_number)
    if stage:
        q = q.where(AgentLog.stage == stage)
    if tool:
        q = q.where(AgentLog.tool_called == tool)

    logs = (await db.execute(q)).scalars().all()
    return {
        "assessment_job_id": str(job_id),
        "recording_id": str(job.recording_id),
        "total_steps": len(logs),
        "logs": [_log_entry(log) for log in logs],
    }


def _seg_summary(s: Segment) -> dict:
    return {
        "segment_id": str(s.id),
        "segment_number": s.segment_number,
        "start_time": s.start_time,
        "end_time": s.end_time,
        "classification": s.classification,
        "quality_score": s.quality_score,
        "sqi_summary": s.sqi_summary,
    }


def _log_entry(log: AgentLog) -> dict:
    return {
        "step": log.step_number,
        "timestamp": log.timestamp.isoformat(),
        "stage": log.stage,
        "tool_called": log.tool_called,
        "input_summary": str(log.input_params)[:200] if log.input_params else None,
        "output_summary": log.output_summary,
        "reasoning": log.reasoning,
        "duration_ms": log.duration_ms,
        "success": log.success,
    }
