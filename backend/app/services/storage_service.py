"""Local filesystem storage service with path-traversal protection."""

import hashlib
from pathlib import Path

from app.core.errors import AppError
from app.core.settings import settings


def _safe_filename(filename: str) -> None:
    """Reject filenames that attempt path traversal."""
    if ".." in filename or "/" in filename or "\\" in filename:
        raise AppError(400, "InvalidFilename", "Filename contains invalid characters.")


def _checksum(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def save_file(file_content: bytes, filename: str, subfolder: str) -> tuple[str, str]:
    """Save bytes to STORAGE_ROOT/subfolder/filename.

    Returns:
        (storage_uri, checksum_sha256)
    """
    _safe_filename(filename)
    dest_dir = Path(settings.storage_root) / subfolder
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_path = dest_dir / filename
    dest_path.write_bytes(file_content)
    storage_uri = str(dest_path)
    return storage_uri, _checksum(file_content)


def read_file(storage_uri: str) -> bytes:
    """Read and return the raw bytes at storage_uri."""
    path = Path(storage_uri)
    if not path.exists():
        raise AppError(404, "FileNotFound", f"No file at: {storage_uri}")
    return path.read_bytes()


def delete_file(storage_uri: str) -> None:
    """Delete the file at storage_uri (no-op if already missing)."""
    path = Path(storage_uri)
    if path.exists():
        path.unlink()
