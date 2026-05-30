"""Integration tests for batch-upload endpoint."""

import json
import pathlib
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import numpy as np
import pandas as pd
import pytest
from httpx import ASGITransport, AsyncClient

_FIXTURES = pathlib.Path(__file__).parent.parent / "fixtures"
_ECG_CSV = _FIXTURES / "sample_ecg.csv"
_PPG_CSV = _FIXTURES / "sample_ppg.csv"

_META = json.dumps({
    "signal_type": "ecg",
    "sampling_rate": 250,
    "signal_column": "ecg",
})


def _fake_user():
    u = MagicMock()
    u.id = uuid.uuid4()
    u.status = "active"
    return u


def _fake_recording(name: str = "sample_ecg.csv") -> MagicMock:
    from app.models.recording_models import Recording
    r = MagicMock(spec=Recording)
    r.id = uuid.uuid4()
    r.filename = name
    r.original_filename = name
    r.file_format = "csv"
    r.signal_type = "ecg"
    r.sampling_rate = 250.0
    r.duration_seconds = 30.0
    r.channel_count = 1
    r.file_size_bytes = 10000
    r.checksum_sha256 = "deadbeef"
    r.storage_uri = f"/tmp/{name}"
    r.status = "uploaded"
    r.subject_id = None
    r.device_id = None
    r.created_at = datetime.now(timezone.utc)
    return r


@pytest.fixture()
def mock_deps(tmp_path):
    """Override auth, DB, storage, and audit for integration tests."""
    fake_user = _fake_user()
    fake_session = AsyncMock()
    fake_session.flush = AsyncMock()
    fake_session.add = MagicMock()

    async def _get_db_override():
        yield fake_session

    from app.auth.auth_dependencies import get_current_user
    from app.core.database import get_db
    from app.main import app

    app.dependency_overrides[get_db] = _get_db_override
    app.dependency_overrides[get_current_user] = lambda: fake_user

    with patch("app.services.audit_service.log_event", new_callable=AsyncMock):
        yield app

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_batch_upload_two_files_returns_both(mock_deps, tmp_path):
    """Batch uploading two valid files must return two recordings."""
    rec1 = _fake_recording("sample_ecg.csv")
    rec2 = _fake_recording("sample_ppg.csv")

    call_count = 0

    async def _side_effect(db, file, meta, user_id):
        nonlocal call_count
        call_count += 1
        return rec1 if call_count == 1 else rec2

    meta_ppg = json.dumps({
        "signal_type": "ppg",
        "sampling_rate": 250,
        "signal_column": "ppg",
    })

    with patch(
        "app.api.recordings_router.ingest_recording",
        side_effect=_side_effect,
    ):
        async with AsyncClient(
            transport=ASGITransport(app=mock_deps), base_url="http://test"
        ) as client:
            with open(_ECG_CSV, "rb") as ecg_fh, open(_PPG_CSV, "rb") as ppg_fh:
                resp = await client.post(
                    "/api/recordings/batch-upload",
                    files=[
                        ("files", ("sample_ecg.csv", ecg_fh, "text/csv")),
                        ("files", ("sample_ppg.csv", ppg_fh, "text/csv")),
                    ],
                    data={"meta": _META},
                )

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert len(body["recordings"]) == 2
    assert body["errors"] == []


@pytest.mark.asyncio
async def test_batch_upload_exceeding_50_returns_400(mock_deps, tmp_path):
    """Sending 51 files must be rejected with HTTP 400 TooManyFiles."""
    # Build 51 tiny in-memory CSV files
    t = np.arange(7500) / 250
    sig = np.sin(2 * np.pi * t)
    df = pd.DataFrame({"timestamp": t, "ecg": sig})
    csv_path = tmp_path / "dummy.csv"
    df.to_csv(csv_path, index=False)

    files = []
    handles = []
    for i in range(51):
        fh = open(csv_path, "rb")
        handles.append(fh)
        files.append(("files", (f"file_{i}.csv", fh, "text/csv")))

    try:
        async with AsyncClient(
            transport=ASGITransport(app=mock_deps), base_url="http://test"
        ) as client:
            resp = await client.post(
                "/api/recordings/batch-upload",
                files=files,
                data={"meta": _META},
            )
    finally:
        for fh in handles:
            fh.close()

    assert resp.status_code == 400, resp.text
    assert resp.json().get("error") == "TooManyFiles"
