"""Orchestrate file validation, storage, and Recording row creation."""

import io
import uuid
from pathlib import Path

import pandas as pd
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.recording_models import Recording
from app.schemas.recording_schemas import RecordingUploadMeta
from app.services import storage_service
from app.services.file_validation_service import validate_upload_file


def _parse_dataframe(content: bytes, filename: str) -> pd.DataFrame:
    ext = Path(filename).suffix.lower()
    if ext == ".parquet":
        return pd.read_parquet(io.BytesIO(content))
    return pd.read_csv(io.BytesIO(content))


def _derive_file_format(filename: str) -> str:
    ext = Path(filename).suffix.lower().lstrip(".")
    return ext  # "csv" or "parquet"


async def ingest_recording(
    db: AsyncSession,
    file: UploadFile,
    meta: RecordingUploadMeta,
    user_id: uuid.UUID,
) -> Recording:
    """Validate, store, and persist a single signal recording.

    Steps:
    1. Validate file (raises AppError on failure).
    2. Save bytes via storage_service.
    3. Parse dataframe to derive duration and channel count.
    4. Insert Recording row with status='uploaded'.
    5. Return the saved Recording.
    """
    original_filename = file.filename or "unknown"

    # 1. Validate — returns raw bytes to avoid double-reading
    content = await validate_upload_file(file, meta)

    # 2. Persist to storage
    storage_uri, checksum = storage_service.save_file(
        content, original_filename, subfolder="recordings"
    )

    # 3. Derive signal metadata
    df = _parse_dataframe(content, original_filename)
    duration_seconds = len(df) / meta.sampling_rate
    channel_count = 1  # MVP: single channel

    # 4. Build and persist ORM row
    recording = Recording(
        filename=original_filename,
        original_filename=original_filename,
        file_format=_derive_file_format(original_filename),
        signal_type=meta.signal_type,
        sampling_rate=float(meta.sampling_rate),
        duration_seconds=duration_seconds,
        channel_count=channel_count,
        file_size_bytes=len(content),
        checksum_sha256=checksum,
        storage_uri=storage_uri,
        subject_id=meta.subject_id,
        device_id=meta.device_id,
        notes=meta.notes,
        status="uploaded",
        created_by=user_id,
        updated_by=user_id,
    )
    db.add(recording)
    await db.flush()  # populate id; caller's get_db commits on success
    return recording
