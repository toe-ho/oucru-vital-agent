"""Integration tests for report generation endpoints using SQLite in-memory DB."""

from __future__ import annotations

import pathlib
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import JSON, Column, MetaData, Table, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.core.database import Base
from app.models.recording_models import AssessmentJob, Recording
from app.models.segment_models import Segment

_FIXTURES = pathlib.Path(__file__).parent.parent / "fixtures"
_ECG_CSV = _FIXTURES / "sample_ecg.csv"


# ---------------------------------------------------------------------------
# SQLite in-memory setup
# ---------------------------------------------------------------------------

def _sqlite_meta() -> MetaData:
    src = Base.metadata
    dst = MetaData()
    for tbl in src.tables.values():
        cols = []
        for col in tbl.columns:
            col_type = JSON() if isinstance(col.type, JSONB) else col.type
            server_default = text("CURRENT_TIMESTAMP") if col.server_default is not None else None
            cols.append(Column(col.name, col_type, primary_key=col.primary_key,
                               nullable=col.nullable, server_default=server_default))
        Table(tbl.name, dst, *cols)
    return dst


def _make_engine():
    return create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )


async def _create_tables(engine):
    meta = _sqlite_meta()
    async with engine.begin() as conn:
        await conn.run_sync(meta.create_all)


def _make_factory(engine):
    return async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
async def sqlite_factory():
    engine = _make_engine()
    await _create_tables(engine)
    factory = _make_factory(engine)
    yield factory
    await engine.dispose()


@pytest.fixture
def fake_user_id():
    return uuid.uuid4()


@pytest.fixture
async def completed_job(sqlite_factory, fake_user_id):
    """Insert a completed AssessmentJob with one Segment."""
    now = datetime.now(timezone.utc)
    async with sqlite_factory() as db:
        rec = Recording(
            id=uuid.uuid4(), filename="test.csv", original_filename="test.csv",
            file_format="csv", signal_type="ecg", sampling_rate=250.0,
            duration_seconds=30.0, status="uploaded",
            created_by=fake_user_id, created_at=now, updated_at=now,
        )
        db.add(rec)
        await db.flush()

        job = AssessmentJob(
            id=uuid.uuid4(), recording_id=rec.id, status="completed",
            processed_segments=1, total_segments=1,
            started_at=now, completed_at=now,
            created_by=fake_user_id,
        )
        db.add(job)
        await db.flush()

        seg = Segment(
            id=uuid.uuid4(), assessment_job_id=job.id, recording_id=rec.id,
            segment_number=1, start_time=0.0, end_time=30.0, duration=30.0,
            classification="accept", quality_score=0.9,
        )
        db.add(seg)
        await db.commit()
    return job


# ---------------------------------------------------------------------------
# Helper: build app
# ---------------------------------------------------------------------------

def _build_app(sqlite_factory, fake_user_id):
    from app.main import app
    from app.auth.auth_dependencies import get_current_user
    from app.core.database import get_db

    fake_user = MagicMock()
    fake_user.id = fake_user_id
    fake_user.status = "active"

    async def _override_db():
        async with sqlite_factory() as session:
            yield session

    app.dependency_overrides[get_db] = _override_db
    app.dependency_overrides[get_current_user] = lambda: fake_user
    return app


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_generate_report_returns_201(sqlite_factory, completed_job, fake_user_id):
    """POST /api/reports/generate must return 201 with a report summary."""
    app = _build_app(sqlite_factory, fake_user_id)
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(
                "/api/reports/generate",
                json={"assessment_job_id": str(completed_job.id)},
            )
        assert resp.status_code == 201, resp.text
        body = resp.json()
        assert "id" in body
        assert body["assessment_job_id"] == str(completed_job.id)
        assert body["json_schema_version"] == "1.0"
        assert body["is_stale"] is False
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_report_detail_includes_content_json(sqlite_factory, completed_job, fake_user_id):
    """GET /api/reports/{id} must return content_json with schema_version and summary."""
    app = _build_app(sqlite_factory, fake_user_id)
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # First generate a report
            gen_resp = await client.post(
                "/api/reports/generate",
                json={"assessment_job_id": str(completed_job.id)},
            )
            assert gen_resp.status_code == 201, gen_resp.text
            report_id = gen_resp.json()["id"]

            # Fetch report detail
            detail_resp = await client.get(f"/api/reports/{report_id}")
        assert detail_resp.status_code == 200, detail_resp.text
        body = detail_resp.json()
        assert body["id"] == report_id
        content = body["content_json"]
        assert content is not None
        assert content["schema_version"] == "1.0"
        assert "summary" in content
        assert "segments" in content
        assert content["assessment_job_id"] == str(completed_job.id)
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_freshness_endpoint_returns_is_stale_false_initially(
    sqlite_factory, completed_job, fake_user_id
):
    """GET /api/reports/{id}/freshness must return is_stale=False for a new report."""
    app = _build_app(sqlite_factory, fake_user_id)
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            gen_resp = await client.post(
                "/api/reports/generate",
                json={"assessment_job_id": str(completed_job.id)},
            )
            assert gen_resp.status_code == 201, gen_resp.text
            report_id = gen_resp.json()["id"]

            freshness_resp = await client.get(f"/api/reports/{report_id}/freshness")
        assert freshness_resp.status_code == 200, freshness_resp.text
        body = freshness_resp.json()
        assert "is_stale" in body
        assert body["is_stale"] is False
        assert "report_generated_at" in body
    finally:
        app.dependency_overrides.clear()
