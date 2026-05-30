"""Assessment orchestration service: job creation, background execution, result retrieval."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path

import yaml
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session_factory
from app.core.errors import AppError
from app.models.recording_models import AssessmentJob, Recording
from app.models.segment_models import Segment
from app.schemas.assessment_schemas import (
    AssessJobRequest,
    AssessJobResponse,
    EffectiveSegmentResult,
    JobResultsResponse,
)
from app.services.assessment_runner import run_deterministic_assessment


def _load_config() -> dict:
    """Load backend/config.yaml; return empty dict on failure."""
    config_path = Path(__file__).parent.parent.parent / "config.yaml"
    try:
        with open(config_path) as fh:
            return yaml.safe_load(fh) or {}
    except Exception:  # noqa: BLE001
        return {}


async def create_assessment_job(
    db: AsyncSession,
    request: AssessJobRequest,
    user_id: uuid.UUID,
) -> AssessmentJob:
    """Validate recording ownership and insert a queued AssessmentJob."""
    result = await db.execute(
        select(Recording).where(
            Recording.id == request.recording_id,
            Recording.deleted_at.is_(None),
        )
    )
    recording = result.scalar_one_or_none()
    if recording is None:
        raise AppError(404, "RecordingNotFound", f"Recording {request.recording_id} not found.")
    if recording.created_by != user_id:
        raise AppError(403, "Forbidden", "You do not own this recording.")

    job = AssessmentJob(
        recording_id=request.recording_id,
        status="queued",
        parameters={
            "window_duration_seconds": request.window_duration_seconds,
            "overlap_seconds": request.overlap_seconds,
            "signal_column": request.signal_column,
            "sampling_rate": request.sampling_rate,
            "metrics": request.metrics,
            "notes": request.notes,
        },
        processed_segments=0,
        created_by=user_id,
    )
    db.add(job)
    await db.flush()
    return job


async def run_assessment(job_id: uuid.UUID, db_session_factory=None) -> None:
    """Background task: run full deterministic pipeline, then optional agent interpretation."""
    factory = db_session_factory or async_session_factory
    async with factory() as db:
        try:
            result = await db.execute(select(AssessmentJob).where(AssessmentJob.id == job_id))
            job = result.scalar_one_or_none()
            if job is None:
                return

            job.status = "processing"
            job.started_at = datetime.now(timezone.utc)
            job.current_step = "loading"
            db.add(job)
            await db.commit()

            rec_result = await db.execute(
                select(Recording).where(Recording.id == job.recording_id)
            )
            recording = rec_result.scalar_one_or_none()
            if recording is None:
                raise AppError(404, "RecordingNotFound", "Recording missing.")

            config = _load_config()
            params = job.parameters or {}

            job.current_step = "assessing"
            db.add(job)
            await db.flush()

            await run_deterministic_assessment(
                job=job,
                recording=recording,
                db=db,
                signal_column=params.get("signal_column", "ecg"),
                sampling_rate=int(params.get("sampling_rate", 250)),
                config=config,
            )

            # Optional agent interpretation — failure must NOT fail the job
            agent_interp = await _try_agent_interpretation(job, db)

            job.status = "completed"
            job.completed_at = datetime.now(timezone.utc)
            job.current_step = "completed"
            job.progress_pct = 100
            db.add(job)
            await db.commit()

            # Auto-generate report after completion — failure must NOT fail the job
            await _try_generate_report(job, agent_interp, factory)

        except Exception as exc:  # noqa: BLE001
            try:
                await db.rollback()
                async with factory() as err_db:
                    err_result = await err_db.execute(
                        select(AssessmentJob).where(AssessmentJob.id == job_id)
                    )
                    err_job = err_result.scalar_one_or_none()
                    if err_job:
                        err_job.status = "failed"
                        err_job.error_message = str(exc)
                        err_job.current_step = "error"
                        err_db.add(err_job)
                        await err_db.commit()
            except Exception:  # noqa: BLE001
                pass


async def _try_agent_interpretation(
    job: AssessmentJob, db: AsyncSession
) -> dict | None:
    """Attempt LLM interpretation; swallow all failures silently. Returns interp dict or None."""
    try:
        from app.agent.agent_orchestrator import AgentOrchestrator, OllamaHealthChecker
        from app.core.settings import settings

        available = await OllamaHealthChecker.is_available(settings.ollama_base_url)
        if not available:
            return None

        seg_result = await db.execute(
            select(Segment).where(Segment.assessment_job_id == job.id)
        )
        segments = list(seg_result.scalars().all())

        job_summary = {
            "recording_id": str(job.recording_id),
            "total_segments": job.total_segments or 0,
            "accepted": sum(1 for s in segments if s.classification == "accept"),
            "rejected": sum(1 for s in segments if s.classification == "reject"),
            "metrics_summary": {},
        }
        segment_summaries = [
            {
                "segment_id": str(s.id),
                "segment_number": s.segment_number,
                "classification": s.classification,
                "failed_metrics": [],
            }
            for s in segments
        ]

        orchestrator = AgentOrchestrator(settings)
        return await orchestrator.interpret_assessment(job_summary, segment_summaries)

    except Exception:  # noqa: BLE001
        return None


async def _try_generate_report(
    job: AssessmentJob, agent_interp: dict | None, factory
) -> None:
    """Auto-generate a report after job completion; swallow all failures silently."""
    try:
        from app.services.report_service import generate_report

        system_user_id = job.created_by or uuid.UUID(int=0)
        async with factory() as db:
            await generate_report(db, job.id, system_user_id, agent_interp)
            await db.commit()
    except Exception:  # noqa: BLE001
        pass


async def get_job_results(db: AsyncSession, job_id: uuid.UUID) -> JobResultsResponse:
    """Load job + segments, derive effective_classification, compute summary."""
    result = await db.execute(select(AssessmentJob).where(AssessmentJob.id == job_id))
    job = result.scalar_one_or_none()
    if job is None:
        raise AppError(404, "JobNotFound", f"Assessment job {job_id} not found.")

    seg_result = await db.execute(
        select(Segment)
        .where(Segment.assessment_job_id == job_id)
        .order_by(Segment.segment_number)
    )
    segments = list(seg_result.scalars().all())

    effective_segments = [
        EffectiveSegmentResult(
            id=s.id,
            segment_number=s.segment_number,
            start_time=s.start_time,
            end_time=s.end_time,
            classification=s.classification,
            quality_score=s.quality_score,
            sqi_summary=s.sqi_summary,
            effective_classification=s.classification,  # no active override yet
        )
        for s in segments
    ]

    accepted = sum(1 for s in segments if s.classification == "accept")
    rejected = sum(1 for s in segments if s.classification == "reject")
    uncomputable = sum(1 for s in segments if s.classification == "uncomputable")
    total = len(segments)
    acceptance_rate = round(accepted / total * 100, 1) if total else 0.0

    if total == 0:
        verdict = "no_segments"
    elif acceptance_rate >= 60:
        verdict = "acceptable"
    else:
        verdict = "poor_quality"

    summary = {
        "accepted_count": accepted,
        "rejected_count": rejected,
        "uncomputable_count": uncomputable,
        "total_segments": total,
        "acceptance_rate_pct": acceptance_rate,
        "verdict": verdict,
    }

    return JobResultsResponse(
        job=AssessJobResponse.model_validate(job),
        segments=effective_segments,
        summary=summary,
    )
