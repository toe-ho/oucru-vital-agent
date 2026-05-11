from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies import get_current_user, require_roles
from app.models.user import User
from app.services.file_service import validate_and_store

router = APIRouter(prefix="/upload", tags=["upload"])


@router.post("", status_code=201)
async def upload_recording(
    file: UploadFile = File(...),
    signal_type: str = Form(...),
    sampling_rate: int = Form(...),
    subject_id: str | None = Form(default=None),
    device_id: str | None = Form(default=None),
    notes: str | None = Form(default=None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "researcher")),
):
    rec = await validate_and_store(
        file=file,
        signal_type=signal_type,
        sampling_rate=sampling_rate,
        user_id=current_user.id,
        db=db,
        subject_id=subject_id,
        device_id=device_id,
        notes=notes,
    )
    return {
        "recording_id": str(rec.id),
        "filename": rec.filename,
        "status": rec.status,
        "metadata": {
            "signal_type": rec.signal_type,
            "sampling_rate": rec.sampling_rate,
            "file_format": rec.file_format,
            "file_size_bytes": rec.file_size_bytes,
            "duration_seconds": rec.duration_seconds,
            "subject_id": rec.subject_id,
            "device_id": rec.device_id,
            "uploaded_at": rec.created_at.isoformat(),
        },
    }
