import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies import get_current_user
from app.exceptions import NotFoundError
from app.models.recording import Recording
from app.models.user import User
from app.services.file_service import get_waveform_samples

router = APIRouter(prefix="/recordings", tags=["recordings"])


@router.get("")
async def list_recordings(
    signal_type: str | None = None,
    status: str | None = None,
    limit: int = Query(default=50, le=200),
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = select(Recording).where(Recording.deleted_at.is_(None))
    if signal_type:
        q = q.where(Recording.signal_type == signal_type)
    if status:
        q = q.where(Recording.status == status)

    total = await db.scalar(select(func.count()).select_from(q.subquery()))
    items = (await db.execute(q.offset(offset).limit(limit).order_by(Recording.created_at.desc()))).scalars().all()

    return {
        "items": [_rec_summary(r) for r in items],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/{recording_id}")
async def get_recording(
    recording_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    rec = await db.get(Recording, recording_id)
    if not rec or rec.deleted_at:
        raise NotFoundError(f"Recording {recording_id} not found")

    return {
        "recording_id": str(rec.id),
        "filename": rec.filename,
        "signal_type": rec.signal_type,
        "sampling_rate": rec.sampling_rate,
        "file_format": rec.file_format,
        "duration_seconds": rec.duration_seconds,
        "status": rec.status,
        "subject_id": rec.subject_id,
    }


@router.get("/{recording_id}/waveform")
async def get_waveform(
    recording_id: uuid.UUID,
    start: float = 0.0,
    end: float | None = None,
    downsample: int = Query(default=10000, gt=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    rec = await db.get(Recording, recording_id)
    if not rec or rec.deleted_at:
        raise NotFoundError(f"Recording {recording_id} not found")

    if end is not None and start >= end:
        from app.exceptions import ValidationError
        raise ValidationError("start must be less than end")

    return await get_waveform_samples(rec, start=start, end=end, downsample=downsample)


def _rec_summary(r: Recording) -> dict:
    return {
        "recording_id": str(r.id),
        "filename": r.filename,
        "signal_type": r.signal_type,
        "status": r.status,
        "uploaded_at": r.created_at.isoformat(),
    }
