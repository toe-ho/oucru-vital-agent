"""Validate uploaded signal files before ingestion."""

import io
from pathlib import Path

import pandas as pd
from fastapi import UploadFile

from app.core.errors import AppError
from app.schemas.recording_schemas import RecordingUploadMeta

_SUPPORTED_EXTENSIONS = {".csv", ".parquet"}
_MAX_FILE_SIZE_BYTES = 100 * 1024 * 1024  # 100 MB
_MIN_DURATION_SECONDS = 5.0


def _check_extension(filename: str) -> str:
    """Return lowercased extension or raise 400."""
    ext = Path(filename).suffix.lower()
    if ext not in _SUPPORTED_EXTENSIONS:
        raise AppError(
            400,
            "UnsupportedFormat",
            f"Unsupported file extension '{ext}'. Allowed: {sorted(_SUPPORTED_EXTENSIONS)}",
        )
    return ext


def _check_path_traversal(filename: str) -> None:
    """Raise 400 if filename contains path traversal sequences."""
    if ".." in filename or "/" in filename or "\\" in filename:
        raise AppError(400, "InvalidFilename", "Filename contains invalid path characters.")


def _read_dataframe(content: bytes, ext: str) -> pd.DataFrame:
    """Parse bytes into a DataFrame; raise 400 on failure."""
    if not content:
        raise AppError(400, "EmptyFile", "Uploaded file is empty.")
    try:
        if ext == ".csv":
            return pd.read_csv(io.BytesIO(content))
        return pd.read_parquet(io.BytesIO(content))
    except Exception as exc:
        raise AppError(400, "UnparsableFile", f"Could not parse file: {exc}") from exc


def _check_signal_column(df: pd.DataFrame, signal_column: str) -> None:
    """Raise 400 if signal_column is absent or non-numeric."""
    if signal_column not in df.columns:
        raise AppError(
            400,
            "MissingSignalColumn",
            f"Column '{signal_column}' not found. Available: {list(df.columns)}",
        )
    if not pd.api.types.is_numeric_dtype(df[signal_column]):
        raise AppError(
            400,
            "NonNumericSignalColumn",
            f"Column '{signal_column}' must contain numeric values.",
        )


def _check_duration(df: pd.DataFrame, sampling_rate: int) -> None:
    """Raise 400 if derived duration is below the minimum."""
    duration = len(df) / sampling_rate
    if duration < _MIN_DURATION_SECONDS:
        raise AppError(
            400,
            "SignalTooShort",
            f"Derived duration {duration:.2f}s is below minimum {_MIN_DURATION_SECONDS}s.",
        )


async def validate_upload_file(file: UploadFile, meta: RecordingUploadMeta) -> bytes:
    """Validate file and return its bytes. Raises AppError(400) on any violation.

    Checks (in order):
    1. Filename path-traversal
    2. Extension whitelist
    3. File size limit
    4. Parseable content
    5. Signal column presence and numeric dtype
    6. Minimum duration
    """
    _check_path_traversal(file.filename or "")
    ext = _check_extension(file.filename or "")

    content = await file.read()
    if len(content) > _MAX_FILE_SIZE_BYTES:
        raise AppError(
            400,
            "FileTooLarge",
            f"File size {len(content)} bytes exceeds 100 MB limit.",
        )

    df = _read_dataframe(content, ext)
    _check_signal_column(df, meta.signal_column)
    _check_duration(df, meta.sampling_rate)

    return content
