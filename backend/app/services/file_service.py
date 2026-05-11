"""File upload validation, storage, and waveform downsampling."""
from __future__ import annotations

import hashlib
import uuid
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.recording import Recording

ALLOWED_EXTENSIONS = {".csv", ".parquet", ".edf", ".txt", ".hea", ".dat"}
MAX_FILE_SIZE = 500 * 1024 * 1024  # 500 MB


async def validate_and_store(
    file: UploadFile,
    signal_type: str,
    sampling_rate: int,
    user_id: uuid.UUID,
    db: AsyncSession,
    subject_id: str | None = None,
    device_id: str | None = None,
    notes: str | None = None,
) -> Recording:
    if signal_type not in ("ecg", "ppg"):
        from app.exceptions import ValidationError
        raise ValidationError("signal_type must be 'ecg' or 'ppg'")

    if sampling_rate <= 0:
        from app.exceptions import ValidationError
        raise ValidationError("sampling_rate must be positive")

    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        from app.exceptions import ValidationError
        raise ValidationError(f"Unsupported file format '{suffix}'. Use: {ALLOWED_EXTENSIONS}")

    content = await file.read()

    if len(content) > MAX_FILE_SIZE:
        from app.exceptions import ValidationError
        raise ValidationError("File exceeds 500 MB limit")

    checksum = hashlib.sha256(content).hexdigest()

    storage_uri = await _write_file(content, file.filename or "upload", checksum)

    # Estimate duration from file size (rough heuristic; updated after loading)
    duration_seconds = None

    rec = Recording(
        filename=file.filename or "upload",
        storage_uri=storage_uri,
        signal_type=signal_type,
        sampling_rate=sampling_rate,
        file_format=suffix.lstrip("."),
        file_size_bytes=len(content),
        checksum_sha256=checksum,
        duration_seconds=duration_seconds,
        subject_id=subject_id,
        device_id=device_id,
        notes=notes,
        status="uploaded",
        created_by=user_id,
    )
    db.add(rec)
    await db.commit()
    await db.refresh(rec)
    return rec


async def _write_file(content: bytes, filename: str, checksum: str) -> str:
    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)
    dest = upload_dir / f"{checksum[:16]}_{filename}"
    dest.write_bytes(content)
    return str(dest)


async def get_waveform_samples(
    recording: Recording,
    start: float = 0.0,
    end: float | None = None,
    downsample: int = 10000,
) -> dict:
    from app.tools.signal_loader import load_signal_file
    import numpy as np
    from scipy.signal import resample

    loaded = load_signal_file(
        recording.storage_uri,
        column=recording.signal_type,
        fs=recording.sampling_rate,
    )

    fs = recording.sampling_rate
    signal = np.array(loaded["signal"] if isinstance(loaded["signal"], list) else list(loaded["signal"].values())[0])

    start_idx = int(start * fs)
    end_idx = int(end * fs) if end is not None else len(signal)
    end_idx = min(end_idx, len(signal))
    slice_ = signal[start_idx:end_idx]

    original_length = len(slice_)
    if original_length > downsample:
        resampled = resample(slice_, downsample)
        downsampled = True
    else:
        resampled = slice_
        downsampled = False

    return {
        "recording_id": str(recording.id),
        "signal_type": recording.signal_type,
        "sampling_rate": fs,
        "start_time": start,
        "end_time": end or round(len(signal) / fs, 2),
        "channels": [{"name": recording.signal_type.upper(), "data": resampled.tolist()}],
        "downsampled": downsampled,
        "original_length": original_length,
        "returned_length": len(resampled),
    }
