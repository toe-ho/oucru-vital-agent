"""Unit tests for storage_service: path traversal rejection and save/read roundtrip."""

import hashlib
from pathlib import Path
from unittest.mock import patch

import pytest

from app.core.errors import AppError
from app.services.storage_service import delete_file, read_file, save_file


@pytest.fixture
def storage_root(tmp_path: Path) -> Path:
    return tmp_path


def _patch_storage(storage_root: Path):
    """Patch settings.storage_root to use tmp_path."""
    return patch("app.services.storage_service.settings.storage_root", str(storage_root))


# --- Path traversal rejection ---

@pytest.mark.parametrize("bad_name", ["../secret.txt", "../../etc/passwd", "sub/../../evil"])
def test_save_file_rejects_path_traversal(storage_root: Path, bad_name: str):
    with _patch_storage(storage_root):
        with pytest.raises(AppError) as exc_info:
            save_file(b"data", bad_name, "uploads")
        assert exc_info.value.status_code == 400
        assert exc_info.value.error_code == "InvalidFilename"


@pytest.mark.parametrize("bad_name", ["sub/file.txt", "a/b"])
def test_save_file_rejects_slash_in_filename(storage_root: Path, bad_name: str):
    with _patch_storage(storage_root):
        with pytest.raises(AppError) as exc_info:
            save_file(b"data", bad_name, "uploads")
        assert exc_info.value.status_code == 400


# --- Successful save and read roundtrip ---

def test_save_and_read_roundtrip(storage_root: Path):
    content = b"hello waveform"
    expected_checksum = hashlib.sha256(content).hexdigest()

    with _patch_storage(storage_root):
        uri, checksum = save_file(content, "signal.edf", "uploads")
        assert checksum == expected_checksum
        assert Path(uri).exists()

        retrieved = read_file(uri)
        assert retrieved == content


def test_delete_file_removes_file(storage_root: Path):
    content = b"to be deleted"
    with _patch_storage(storage_root):
        uri, _ = save_file(content, "temp.edf", "uploads")
        assert Path(uri).exists()
        delete_file(uri)
        assert not Path(uri).exists()


def test_delete_file_is_noop_for_missing(storage_root: Path):
    with _patch_storage(storage_root):
        # Should not raise even if the file doesn't exist
        delete_file(str(storage_root / "nonexistent.edf"))


def test_read_file_raises_404_for_missing(storage_root: Path):
    with _patch_storage(storage_root):
        with pytest.raises(AppError) as exc_info:
            read_file(str(storage_root / "missing.edf"))
        assert exc_info.value.status_code == 404
        assert exc_info.value.error_code == "FileNotFound"
