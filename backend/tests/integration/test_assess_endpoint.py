"""Integration tests for assessment endpoints."""
import uuid
from unittest.mock import patch, AsyncMock

import pytest
import pytest_asyncio


@pytest.mark.asyncio
async def test_health_returns_200(async_client):
    resp = await async_client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"


@pytest.mark.asyncio
async def test_trigger_assessment_requires_auth(async_client):
    resp = await async_client.post("/api/assess", json={"recording_id": str(uuid.uuid4())})
    assert resp.status_code in (401, 403)


@pytest.mark.asyncio
async def test_get_job_status_not_found(async_client):
    fake_id = str(uuid.uuid4())
    resp = await async_client.get(f"/api/assessment-jobs/{fake_id}")
    assert resp.status_code in (401, 404)


@pytest.mark.asyncio
async def test_get_job_status_malformed_uuid(async_client):
    resp = await async_client.get("/api/assessment-jobs/not-a-uuid")
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_get_results_not_found(async_client):
    fake_id = str(uuid.uuid4())
    resp = await async_client.get(f"/api/assessment-jobs/{fake_id}/results")
    assert resp.status_code in (401, 404)


@pytest.mark.asyncio
async def test_get_logs_not_found(async_client):
    fake_id = str(uuid.uuid4())
    resp = await async_client.get(f"/api/assessment-jobs/{fake_id}/logs")
    assert resp.status_code in (401, 404)
