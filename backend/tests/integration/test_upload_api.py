"""Integration tests for single-file upload endpoint."""

import json
import pathlib
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

_FIXTURES = pathlib.Path(__file__).parent.parent / "fixtures"
_ECG_CSV = _FIXTURES / "sample_ecg.csv"

_META = json.dumps({
    "signal_type": "ecg",
    "sampling_rate": 250,
    "signal_column": "ecg",
})


def _mock_user():
    user = MagicMock()
    user.id = uuid.uuid4()
    user.status = "active"
    return user


def _make_app_with_sqlite(tmp_path):
    """Return a FastAPI app wired to an in-memory SQLite DB."""
    import os
    os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{tmp_path}/test.db"

    # Reload settings so DATABASE_URL is picked up
    import importlib
    import app.core.settings as _s
    _s.settings.database_url = f"sqlite+aiosqlite:///{tmp_path}/test.db"

    from app.main import app as fastapi_app
    return fastapi_app


@pytest.fixture()
def mock_deps(tmp_path):
    """Patch auth + DB + storage so tests run without Postgres."""
    fake_user = _mock_user()
    storage_uri = str(tmp_path / "recordings" / "sample_ecg.csv")

    with (
        patch("app.api.recordings_router.get_current_user", return_value=fake_user),
        patch("app.core.database.get_db") as mock_get_db,
        patch("app.services.storage_service.save_file",
              return_value=(storage_uri, "abc123")) as _mock_save,
        patch("app.services.audit_service.log_event", new_callable=AsyncMock),
    ):
        # Provide a minimal async DB session that flushes/commits silently
        fake_session = AsyncMock()
        fake_session.flush = AsyncMock()
        fake_session.add = MagicMock()

        async def _get_db_override():
            yield fake_session

        mock_get_db.return_value = _get_db_override()

        from app.main import app
        app.dependency_overrides[
            __import__("app.core.database", fromlist=["get_db"]).get_db
        ] = _get_db_override
        app.dependency_overrides[
            __import__("app.auth.auth_dependencies", fromlist=["get_current_user"]).get_current_user
        ] = lambda: fake_user

        yield app

        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_single_upload_returns_201(mock_deps, tmp_path):
    """Uploading a valid ECG CSV must return HTTP 201 with a recording body."""
    from app.models.recording_models import Recording

    fake_recording = MagicMock(spec=Recording)
    fake_recording.id = uuid.uuid4()
    fake_recording.filename = "sample_ecg.csv"
    fake_recording.original_filename = "sample_ecg.csv"
    fake_recording.file_format = "csv"
    fake_recording.signal_type = "ecg"
    fake_recording.sampling_rate = 250.0
    fake_recording.duration_seconds = 30.0
    fake_recording.channel_count = 1
    fake_recording.file_size_bytes = 12345
    fake_recording.checksum_sha256 = "abc123"
    fake_recording.storage_uri = str(tmp_path / "sample_ecg.csv")
    fake_recording.status = "uploaded"
    fake_recording.subject_id = None
    fake_recording.device_id = None
    from datetime import datetime, timezone
    fake_recording.created_at = datetime.now(timezone.utc)

    with patch(
        "app.api.recordings_router.ingest_recording",
        new_callable=AsyncMock,
        return_value=fake_recording,
    ):
        async with AsyncClient(
            transport=ASGITransport(app=mock_deps), base_url="http://test"
        ) as client:
            with open(_ECG_CSV, "rb") as fh:
                resp = await client.post(
                    "/api/recordings/upload",
                    files={"file": ("sample_ecg.csv", fh, "text/csv")},
                    data={"meta": _META},
                )

    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert "id" in body


@pytest.mark.asyncio
async def test_upload_unsupported_format_returns_400(mock_deps, tmp_path):
    """Uploading a .txt file must return HTTP 400 UnsupportedFormat."""
    txt_file = tmp_path / "signal.txt"
    txt_file.write_text("col1\n1\n2\n3\n")

    async with AsyncClient(
        transport=ASGITransport(app=mock_deps), base_url="http://test"
    ) as client:
        with open(txt_file, "rb") as fh:
            resp = await client.post(
                "/api/recordings/upload",
                files={"file": ("signal.txt", fh, "text/plain")},
                data={"meta": _META},
            )

    assert resp.status_code == 400
    assert resp.json().get("error") == "UnsupportedFormat"


@pytest.mark.asyncio
async def test_upload_missing_signal_column_returns_400(mock_deps, tmp_path):
    """Uploading a CSV without the declared signal_column must return 400."""
    bad_csv = tmp_path / "bad.csv"
    # 30 s worth of rows but wrong column name
    import numpy as np
    import pandas as pd
    df = pd.DataFrame({"timestamp": np.arange(7500) / 250, "wrong_col": np.zeros(7500)})
    df.to_csv(bad_csv, index=False)

    meta_bad = json.dumps({
        "signal_type": "ecg",
        "sampling_rate": 250,
        "signal_column": "ecg",  # not present in file
    })

    async with AsyncClient(
        transport=ASGITransport(app=mock_deps), base_url="http://test"
    ) as client:
        with open(bad_csv, "rb") as fh:
            resp = await client.post(
                "/api/recordings/upload",
                files={"file": ("bad.csv", fh, "text/csv")},
                data={"meta": meta_bad},
            )

    assert resp.status_code == 400
    assert resp.json().get("error") == "MissingSignalColumn"
