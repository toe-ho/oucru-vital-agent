"""Service for persisting and querying AgentLog rows."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.log_models import AgentLog


async def persist_log(
    db: AsyncSession,
    assessment_job_id: uuid.UUID,
    recording_id: uuid.UUID,
    step_number: int,
    stage: str,
    tool_called: str | None,
    input_params: dict | None,
    output_summary: str | None,
    reasoning: str | None,
    duration_ms: int | None,
    status: str,
    error_detail: str | None,
    created_by: uuid.UUID | None,
) -> AgentLog:
    """Insert an AgentLog row.

    Handles UNIQUE(assessment_job_id, step_number) collisions by incrementing
    step_number until an unused slot is found (max 100 attempts).
    """
    attempt_step = step_number
    for _ in range(100):
        log = AgentLog(
            assessment_job_id=assessment_job_id,
            recording_id=recording_id,
            step_number=attempt_step,
            stage=stage,
            tool_called=tool_called,
            input_params=input_params,
            output_summary=output_summary,
            reasoning=reasoning,
            duration_ms=duration_ms,
            status=status,
            error_detail=error_detail,
            created_by=created_by,
        )
        db.add(log)
        try:
            await db.flush()
            return log
        except IntegrityError:
            await db.rollback()
            attempt_step += 1

    # Last-resort fallback with random step to avoid infinite retry
    log = AgentLog(
        assessment_job_id=assessment_job_id,
        recording_id=recording_id,
        step_number=attempt_step + uuid.uuid4().int % 10000,
        stage=stage,
        tool_called=tool_called,
        input_params=input_params,
        output_summary=output_summary,
        reasoning=reasoning,
        duration_ms=duration_ms,
        status=status,
        error_detail=error_detail,
        created_by=created_by,
    )
    db.add(log)
    await db.flush()
    return log


async def get_logs_for_job(db: AsyncSession, assessment_job_id: uuid.UUID) -> list[AgentLog]:
    """Return all AgentLog rows for a given assessment job, ordered by step_number."""
    result = await db.execute(
        select(AgentLog)
        .where(AgentLog.assessment_job_id == assessment_job_id)
        .order_by(AgentLog.step_number)
    )
    return list(result.scalars().all())
