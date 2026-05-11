import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies import get_current_user
from app.exceptions import NotFoundError
from app.models.segment import Segment
from app.models.sqi_result import SQIResult
from app.models.user import User

router = APIRouter(tags=["segments"])


@router.get("/assessment-jobs/{job_id}/segments/{segment_id}")
async def get_segment_detail(
    job_id: uuid.UUID,
    segment_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    seg = await db.scalar(
        select(Segment).where(Segment.id == segment_id, Segment.assessment_job_id == job_id)
    )
    if not seg:
        raise NotFoundError(f"Segment {segment_id} not found in job {job_id}")

    sqi_rows = (await db.execute(
        select(SQIResult).where(SQIResult.segment_id == segment_id)
    )).scalars().all()

    sqi_values = {r.metric_name: r.metric_value for r in sqi_rows}
    failed_rules = [
        {
            "metric": r.metric_name,
            "value": r.metric_value,
            "threshold": r.threshold_min if not r.passed and r.metric_value is not None and r.threshold_min is not None and r.metric_value < r.threshold_min else r.threshold_max,
            "operator": "min" if r.threshold_min is not None and r.metric_value is not None and r.metric_value < r.threshold_min else "max",
            "description": f"{r.metric_name} outside threshold",
        }
        for r in sqi_rows if r.passed is False
    ]

    return {
        "segment_id": str(seg.id),
        "assessment_job_id": str(job_id),
        "recording_id": str(seg.recording_id),
        "segment_number": seg.segment_number,
        "start_time": seg.start_time,
        "end_time": seg.end_time,
        "classification": seg.classification,
        "quality_score": seg.quality_score,
        "sqi_values": sqi_values,
        "failed_rules": failed_rules,
    }
