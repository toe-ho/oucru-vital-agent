from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies import get_current_user
from app.exceptions import NotFoundError
from app.models.assessment import AssessmentJob
from app.models.recording import Recording
from app.models.segment import Segment
from app.models.user import User

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary")
async def dashboard_summary(
    days: int = Query(default=30, gt=0),
    signal_type: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    since = datetime.now(timezone.utc) - timedelta(days=days)

    total = await db.scalar(select(func.count()).select_from(Recording).where(Recording.deleted_at.is_(None)))

    q = (
        select(AssessmentJob)
        .where(AssessmentJob.status == "completed", AssessmentJob.completed_at >= since)
        .order_by(AssessmentJob.completed_at.desc())
        .limit(20)
    )
    recent_jobs = (await db.execute(q)).scalars().all()

    alerts = []
    for job in recent_jobs:
        if job.acceptance_rate is not None and job.acceptance_rate < 0.4:
            alerts.append({
                "alert_id": f"alert-{job.id}",
                "type": "low_quality",
                "severity": "high",
                "recording_id": str(job.recording_id),
                "assessment_job_id": str(job.id),
                "message": f"Acceptance rate {job.acceptance_rate:.1%} — flagged for review.",
                "created_at": job.completed_at.isoformat() if job.completed_at else None,
                "acknowledged": False,
            })

    return {
        "total_recordings": total,
        "period_days": days,
        "recent_assessments": [
            {
                "recording_id": str(j.recording_id),
                "assessment_job_id": str(j.id),
                "assessed_at": j.completed_at.isoformat() if j.completed_at else None,
                "acceptance_rate": j.acceptance_rate,
                "verdict": j.overall_verdict,
            }
            for j in recent_jobs
        ],
        "quality_trends": [],
        "alerts": alerts,
    }


@router.get("/timeline/{job_id}")
async def timeline(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    import uuid
    try:
        jid = uuid.UUID(job_id)
    except ValueError:
        raise NotFoundError(f"Assessment job {job_id} not found")

    job = await db.get(AssessmentJob, jid)
    if not job:
        raise NotFoundError(f"Assessment job {job_id} not found")

    segments = (await db.execute(
        select(Segment).where(Segment.assessment_job_id == jid).order_by(Segment.segment_number)
    )).scalars().all()

    return {
        "assessment_job_id": str(jid),
        "recording_id": str(job.recording_id),
        "total_segments": len(segments),
        "timeline": [
            {
                "segment_number": s.segment_number,
                "start_time": s.start_time,
                "end_time": s.end_time,
                "classification": s.classification,
                "quality_score": s.quality_score,
            }
            for s in segments
        ],
    }
