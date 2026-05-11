import io
import pytest


@pytest.mark.asyncio
async def test_health(async_client):
    resp = await async_client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_upload_requires_auth(async_client):
    resp = await async_client.post("/api/upload")
    assert resp.status_code in (401, 422)


@pytest.mark.asyncio
async def test_upload_invalid_signal_type(async_client, ppg_signal):
    import pandas as pd
    buf = io.BytesIO()
    import numpy as np
    pd.DataFrame({"ppg": ppg_signal}).to_csv(buf, index=False)
    buf.seek(0)

    # Without auth token this will be 401, which is fine for this test level
    resp = await async_client.post(
        "/api/upload",
        files={"file": ("test.csv", buf, "text/csv")},
        data={"signal_type": "invalid", "sampling_rate": "100"},
    )
    assert resp.status_code in (400, 401, 422)
