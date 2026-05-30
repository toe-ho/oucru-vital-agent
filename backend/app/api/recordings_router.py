"""REST endpoints for signal recording upload, batch upload, and retrieval."""

import io
import json
import uuid
from pathlib import Path
from typing import Annotated

import pandas as pd
from fastapi import APIRouter, Depends, Form, Request, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.auth_dependencies import get_current_user
from app.core.database import get_db
from app.core.errors import AppError
from app.models.recording_models import Recording
from app.models.user_models import User
from app.models.recording_models import AssessmentJob
from app.schemas.assessment_schemas import AssessJobResponse
from app.schemas.recording_schemas import (
    BatchUploadResponse,
    FileInspectResponse,
    RecordingResponse,
    RecordingUploadMeta,
)
from app.schemas.report_schemas import ReportSummary
from app.services import audit_service
from app.services.recording_ingestion_service import ingest_recording
from app.services import report_service

router = APIRouter(tags=["recordings"])

_MAX_BATCH_FILES = 50


def _parse_meta(meta_json: str) -> RecordingUploadMeta:
    """Parse JSON string into RecordingUploadMeta; raise 400 on failure."""
    try:
        return RecordingUploadMeta.model_validate(json.loads(meta_json))
    except Exception as exc:
        raise AppError(400, "InvalidMeta", f"Could not parse meta JSON: {exc}") from exc


_ECG_KEYWORDS = {"ecg", "lead", "ekg", "cardiac"}
_PPG_KEYWORDS = {"ppg", "spo2", "pleth", "ir", "red"}
_TIME_KEYWORDS = {"timestamp", "time", "t", "datetime", "elapsed"}


def _detect_signal_type(col_name: str) -> str | None:
    lower = col_name.lower()
    if any(k in lower for k in _ECG_KEYWORDS):
        return "ecg"
    if any(k in lower for k in _PPG_KEYWORDS):
        return "ppg"
    return None


def _infer_sampling_rate(df: pd.DataFrame) -> int | None:
    time_col = next(
        (c for c in df.columns if c.lower() in _TIME_KEYWORDS and pd.api.types.is_numeric_dtype(df[c])),
        None,
    )
    if time_col is None:
        return None
    intervals = df[time_col].dropna().diff().dropna()
    if intervals.empty or intervals.median() <= 0:
        return None
    return int(round(1.0 / intervals.median()))


@router.post("/inspect", response_model=FileInspectResponse, status_code=status.HTTP_200_OK)
async def inspect_file(
    file: UploadFile,
    _current_user: Annotated[User, Depends(get_current_user)],
) -> FileInspectResponse:
    """Parse an uploaded file and return auto-detected column / signal metadata.

    Does not persist anything — intended to be called before the real upload
    so the UI can pre-fill the form fields.
    """
    ext = Path(file.filename or "").suffix.lower()
    if ext not in {".csv", ".parquet"}:
        raise AppError(400, "UnsupportedFormat", f"Unsupported extension '{ext}'.")

    content = await file.read()
    try:
        df = pd.read_csv(io.BytesIO(content)) if ext == ".csv" else pd.read_parquet(io.BytesIO(content))
    except Exception as exc:
        raise AppError(400, "UnparsableFile", f"Could not parse file: {exc}") from exc

    all_cols = list(df.columns)
    numeric_cols = [c for c in all_cols if pd.api.types.is_numeric_dtype(df[c])]

    # Best-guess signal column: first numeric col whose name hints at ecg/ppg, else first numeric
    signal_col: str | None = next(
        (c for c in numeric_cols if _detect_signal_type(c) is not None),
        numeric_cols[0] if numeric_cols else None,
    )

    detected_type: str | None = _detect_signal_type(signal_col) if signal_col else None

    return FileInspectResponse(
        columns=all_cols,
        numeric_columns=numeric_cols,
        detected_signal_column=signal_col,
        detected_signal_type=detected_type,  # type: ignore[arg-type]
        detected_sampling_rate=_infer_sampling_rate(df),
    )


@router.post("/upload", response_model=RecordingResponse, status_code=status.HTTP_201_CREATED)
async def upload_recording(
    request: Request,
    file: UploadFile,
    meta: Annotated[str, Form()],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> RecordingResponse:
    """Upload a single signal file (CSV or Parquet)."""
    parsed_meta = _parse_meta(meta)
    recording = await ingest_recording(db, file, parsed_meta, current_user.id)

    await audit_service.log_event(
        db,
        actor_user_id=current_user.id,
        action="recording_uploaded",
        entity_type="recording",
        entity_id=recording.id,
        request_id=request.headers.get("x-request-id"),
        ip_address=request.client.host if request.client else None,
    )
    return RecordingResponse.model_validate(recording)


@router.post("/batch-upload", response_model=BatchUploadResponse, status_code=status.HTTP_200_OK)
async def batch_upload_recordings(
    request: Request,
    files: list[UploadFile],
    meta: Annotated[str, Form()],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> BatchUploadResponse:
    """Upload up to 50 signal files in one request.

    Per-file validation errors are collected without aborting the batch.
    """
    if len(files) > _MAX_BATCH_FILES:
        raise AppError(
            400,
            "TooManyFiles",
            f"Batch limit is {_MAX_BATCH_FILES} files; received {len(files)}.",
        )

    parsed_meta = _parse_meta(meta)
    recordings: list[RecordingResponse] = []
    errors: list[dict] = []

    for upload_file in files:
        try:
            recording = await ingest_recording(db, upload_file, parsed_meta, current_user.id)
            await audit_service.log_event(
                db,
                actor_user_id=current_user.id,
                action="recording_uploaded",
                entity_type="recording",
                entity_id=recording.id,
                request_id=request.headers.get("x-request-id"),
                ip_address=request.client.host if request.client else None,
            )
            recordings.append(RecordingResponse.model_validate(recording))
        except AppError as exc:
            errors.append(
                {
                    "filename": upload_file.filename,
                    "error_code": exc.error_code,
                    "detail": exc.detail,
                }
            )

    return BatchUploadResponse(recordings=recordings, errors=errors)


@router.get("", response_model=list[RecordingResponse])
async def list_recordings(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    skip: int = 0,
    limit: int = 20,
) -> list[RecordingResponse]:
    """List recordings created by the current user (paginated)."""
    result = await db.execute(
        select(Recording)
        .where(Recording.created_by == current_user.id, Recording.deleted_at.is_(None))
        .order_by(Recording.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    rows = result.scalars().all()
    return [RecordingResponse.model_validate(r) for r in rows]


@router.get("/{recording_id}/reports", response_model=list[ReportSummary])
async def list_reports_for_recording(
    recording_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[ReportSummary]:
    """List all reports for a recording."""
    reports = await report_service.list_reports_for_recording(db, recording_id)
    return [
        ReportSummary(
            id=r.id,
            recording_id=r.recording_id,
            assessment_job_id=r.assessment_job_id,
            title=r.title,
            json_schema_version=r.json_schema_version,
            generated_at=r.generated_at,
            is_stale=False,
            created_at=r.created_at,
        )
        for r in reports
    ]


@router.get("/{recording_id}/jobs", response_model=list[AssessJobResponse])
async def list_jobs_for_recording(
    recording_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[AssessJobResponse]:
    """List all assessment jobs for a recording, newest first."""
    result = await db.execute(
        select(AssessmentJob)
        .where(AssessmentJob.recording_id == recording_id)
        .order_by(AssessmentJob.created_at.desc())
    )
    jobs = result.scalars().all()
    return [AssessJobResponse.model_validate(j) for j in jobs]


@router.get("/{recording_id}", response_model=RecordingResponse)
async def get_recording(
    recording_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> RecordingResponse:
    """Fetch a single recording by ID (404 if not found or deleted)."""
    result = await db.execute(
        select(Recording).where(
            Recording.id == recording_id,
            Recording.deleted_at.is_(None),
        )
    )
    recording = result.scalar_one_or_none()
    if recording is None:
        raise AppError(404, "RecordingNotFound", f"Recording {recording_id} not found.")
    return RecordingResponse.model_validate(recording)
