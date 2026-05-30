"""Pydantic v2 schemas for Recording endpoints."""

import uuid
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class RecordingUploadMeta(BaseModel):
    """Metadata submitted alongside a signal file upload."""

    signal_type: Literal["ecg", "ppg"]
    sampling_rate: int = Field(gt=0)
    signal_column: str
    subject_id: Optional[str] = None
    device_id: Optional[str] = None
    notes: Optional[str] = None


class RecordingResponse(BaseModel):
    """Public representation of a persisted Recording row."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    filename: str
    original_filename: str
    file_format: str
    signal_type: str
    sampling_rate: Optional[float]
    duration_seconds: Optional[float]
    channel_count: int
    file_size_bytes: Optional[int]
    checksum_sha256: Optional[str]
    storage_uri: Optional[str]
    status: str
    subject_id: Optional[str]
    device_id: Optional[str]
    created_at: datetime


class BatchUploadResponse(BaseModel):
    """Result of a batch upload — successful recordings + per-file errors."""

    recordings: list[RecordingResponse]
    errors: list[dict]


class FileInspectResponse(BaseModel):
    """Auto-detected metadata from a signal file, returned before full upload."""

    columns: list[str]
    numeric_columns: list[str]
    detected_signal_column: Optional[str]
    detected_signal_type: Optional[Literal["ecg", "ppg"]]
    detected_sampling_rate: Optional[int]
