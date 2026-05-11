"""Create jobs, persist segments + SQI results, log agent steps."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent_log import AgentLog
from app.models.assessment import AssessmentJob
from app.models.recording import Recording
from app.models.segment import Segment
from app.models.sqi_result import SQIResult


async def create_job(recording_id: uuid.UUID, parameters: dict, user_id: uuid.UUID, db: AsyncSession) -> AssessmentJob:
    job = AssessmentJob(
        recording_id=recording_id,
        status="queued",
        parameters=parameters,
        created_by=user_id,
    )
    db.add(job)

    rec = await db.get(Recording, recording_id)
    if rec:
        rec.status = "processing"

    await db.commit()
    await db.refresh(job)
    return job


async def update_job_progress(
    job_id: uuid.UUID,
    processed: int,
    total: int | None,
    stage: str,
    db: AsyncSession,
) -> None:
    job = await db.get(AssessmentJob, job_id)
    if not job:
        return
    job.processed_segments = processed
    if total is not None:
        job.total_segments = total
    job.current_stage = stage
    job.status = "processing"
    if not job.started_at:
        job.started_at = datetime.now(timezone.utc)
    if total and total > 0:
        job.progress_pct = round(processed / total * 100, 1)
    await db.commit()


async def persist_segments_and_sqi(
    job_id: uuid.UUID,
    recording_id: uuid.UUID,
    windows: list[dict],
    rule_dict: dict,
    db: AsyncSession,
) -> list[Segment]:
    now = datetime.now(timezone.utc)
    segments = []

    for w in windows:
        seg = Segment(
            assessment_job_id=job_id,
            recording_id=recording_id,
            segment_number=w["window_idx"] + 1,
            start_time=w["start_sec"],
            end_time=w["end_sec"],
            classification=w["classification"],
            quality_score=w["sqi_score"],
            sqi_summary=w.get("metrics", {}),
            failed_rules=w.get("failed_rules", []),
            created_at=now,
        )
        db.add(seg)
        segments.append(seg)

    await db.flush()

    sqi_rows = []
    for seg, w in zip(segments, windows):
        for metric_name, metric_value in w.get("metrics", {}).items():
            thr = rule_dict.get(metric_name, {})
            sqi_rows.append({
                "id": uuid.uuid4(),
                "segment_id": seg.id,
                "metric_name": metric_name,
                "metric_value": float(metric_value) if metric_value is not None else None,
                "threshold_min": thr.get("min"),
                "threshold_max": thr.get("max"),
                "passed": _check_passes(metric_value, thr),
                "created_at": now,
            })

    if sqi_rows:
        await db.execute(insert(SQIResult), sqi_rows)

    await db.commit()
    return segments


def _check_passes(value, thr: dict) -> bool | None:
    if value is None:
        return None
    v = float(value)
    min_t = thr.get("min")
    max_t = thr.get("max")
    if min_t is not None and v < min_t:
        return False
    if max_t is not None and v > max_t:
        return False
    return True


async def log_agent_step(job_id: uuid.UUID, step_data: dict, db: AsyncSession) -> None:
    from sqlalchemy import select, func

    count_result = await db.scalar(
        select(func.count()).select_from(AgentLog).where(AgentLog.assessment_job_id == job_id)
    )
    step_num = (count_result or 0) + 1

    log = AgentLog(
        assessment_job_id=job_id,
        step_number=step_num,
        timestamp=datetime.now(timezone.utc),
        stage=step_data.get("stage", "unknown"),
        tool_called=step_data.get("tool_called"),
        input_params=step_data.get("input_params"),
        output_summary=step_data.get("output_summary"),
        reasoning=step_data.get("reasoning"),
        duration_ms=step_data.get("duration_ms"),
        success=step_data.get("success", True),
        error_detail=step_data.get("error_detail"),
    )
    db.add(log)
    await db.commit()


async def finalize_job(job_id: uuid.UUID, state: dict, db: AsyncSession) -> None:
    job = await db.get(AssessmentJob, job_id)
    if not job:
        return

    is_error = state.get("current_stage") == "error"
    job.status = "failed" if is_error else "completed"
    job.completed_at = datetime.now(timezone.utc)
    job.overall_verdict = state.get("overall_verdict")
    job.acceptance_rate = state.get("acceptance_rate")
    job.escalated = state.get("escalate", False)
    job.escalation_reason = state.get("escalation_reason")
    job.agent_interpretation = state.get("agent_interpretation")
    job.current_stage = state.get("current_stage")

    rec = await db.get(Recording, job.recording_id)
    if rec:
        rec.status = "failed" if is_error else "completed"

    await db.commit()
