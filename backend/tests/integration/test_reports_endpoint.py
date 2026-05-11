"""Integration tests for reports endpoints."""
import uuid

import pytest


@pytest.mark.asyncio
async def test_generate_report_requires_auth(async_client):
    resp = await async_client.post(
        "/api/reports/generate",
        json={"assessment_job_id": str(uuid.uuid4()), "format": "json"},
    )
    assert resp.status_code in (401, 403)


@pytest.mark.asyncio
async def test_get_report_not_found(async_client):
    fake_id = str(uuid.uuid4())
    resp = await async_client.get(f"/api/reports/{fake_id}")
    assert resp.status_code in (401, 404)


@pytest.mark.asyncio
async def test_get_report_malformed_uuid(async_client):
    resp = await async_client.get("/api/reports/not-a-uuid")
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_generate_report_invalid_format(async_client):
    resp = await async_client.post(
        "/api/reports/generate",
        json={"assessment_job_id": str(uuid.uuid4()), "format": "docx"},
    )
    assert resp.status_code in (401, 403, 422)


@pytest.mark.asyncio
async def test_upload_endpoint_rejects_invalid_file_type(async_client):
    import io
    data = {"signal_type": "ppg", "sampling_rate": "100"}
    files = {"file": ("test.exe", io.BytesIO(b"fake"), "application/octet-stream")}
    resp = await async_client.post("/api/upload", data=data, files=files)
    assert resp.status_code in (401, 422)


@pytest.mark.asyncio
async def test_upload_endpoint_missing_required_fields(async_client):
    import io
    files = {"file": ("test.csv", io.BytesIO(b"ppg\n0.1\n0.2"), "text/csv")}
    resp = await async_client.post("/api/upload", files=files)
    assert resp.status_code in (401, 422)
