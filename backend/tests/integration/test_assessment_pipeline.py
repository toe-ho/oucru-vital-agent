"""Integration tests for the assessment pipeline.

Uses SQLite in-memory (aiosqlite) + real signal fixture file.
Auth and background tasks are patched/called directly.
"""

from __future__ import annotations

import pathlib
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from sqlalchemy import JSON, Table, Column, MetaData, text
from sqlalchemy.dialects.postgresql import JSONB

from app.core.database import Base
from app.models.log_models import AgentLog, AuditEvent
from app.models.recording_models import AssessmentJob, Recording
from app.models.segment_models import Segment, SegmentOverrideEvent, SqiResult
from app.models.user_models import Role, User, UserRole

_FIXTURES = pathlib.Path(__file__).parent.parent / "fixtures"
_ECG_CSV = _FIXTURES / "sample_ecg.csv"


def _sqlite_compatible_metadata() -> MetaData:
    """Build a fresh MetaData where JSONB → JSON and server_default → SQLite CURRENT_TIMESTAMP.

    This avoids mutating the global Base.metadata used by other tests.
    """
    src = Base.metadata
    dst = MetaData()
    for tbl in src.tables.values():
        cols = []
        for col in tbl.columns:
            col_type = JSON() if isinstance(col.type, JSONB) else col.type
            # Preserve server_default for timestamp cols using SQLite-compatible syntax
            server_default = None
            if col.server_default is not None:
                server_default = text("CURRENT_TIMESTAMP")
            new_col = Column(
                col.name,
                col_type,
                primary_key=col.primary_key,
                nullable=col.nullable,
                server_default=server_default,
            )
            cols.append(new_col)
        # Skip FK/unique constraints — SQLite doesn't need them for tests
        Table(tbl.name, dst, *cols)
    return dst


# ---------------------------------------------------------------------------
# In-memory SQLite engine factory
# ---------------------------------------------------------------------------

def _make_sqlite_engine():
    return create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )


async def _create_tables(engine):
    meta = _sqlite_compatible_metadata()
    async with engine.begin() as conn:
        await conn.run_sync(meta.create_all)


def _make_session_factory(engine):
    return async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
async def sqlite_factory():
    engine = _make_sqlite_engine()
    await _create_tables(engine)
    factory = _make_session_factory(engine)
    yield factory
    await engine.dispose()


@pytest.fixture
async def db_session(sqlite_factory):
    async with sqlite_factory() as session:
        yield session


@pytest.fixture
def fake_user_id():
    return uuid.uuid4()


@pytest.fixture
async def sample_recording(db_session, fake_user_id):
    """Insert a minimal Recording row pointing at the ECG fixture file."""
    now = datetime.now(timezone.utc)
    rec = Recording(
        id=uuid.uuid4(),
        filename="sample_ecg.csv",
        original_filename="sample_ecg.csv",
        file_format="csv",
        signal_type="ecg",
        sampling_rate=250.0,
        duration_seconds=30.0,
        channel_count=1,
        file_size_bytes=int(_ECG_CSV.stat().st_size),
        storage_uri=str(_ECG_CSV),
        status="uploaded",
        created_by=fake_user_id,
        created_at=now,
        updated_at=now,
    )
    db_session.add(rec)
    await db_session.commit()
    return rec


# ---------------------------------------------------------------------------
# Helper: build app with overridden DB + auth
# ---------------------------------------------------------------------------

def _build_app(sqlite_factory, fake_user_id):
    from app.main import app
    from app.core.database import get_db
    from app.auth.auth_dependencies import get_current_user

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
async def test_create_job_returns_202_with_job_id(sqlite_factory, sample_recording, fake_user_id):
    """POST /api/assess must return 202 with a valid job id."""
    app = _build_app(sqlite_factory, fake_user_id)

    # Prevent the background task from actually running during this test
    with patch("app.api.assessment_router.run_assessment", new_callable=AsyncMock):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.post(
                "/api/assess/",
                json={
                    "recording_id": str(sample_recording.id),
                    "window_duration_seconds": 30,
                    "overlap_seconds": 0,
                    "signal_column": "ecg",
                    "sampling_rate": 250,
                },
            )

    app.dependency_overrides.clear()
    assert resp.status_code == 202, resp.text
    body = resp.json()
    assert "id" in body
    assert body["status"] == "queued"
    assert uuid.UUID(body["id"])  # valid UUID


@pytest.mark.asyncio
async def test_run_assessment_creates_segments_and_sqi_results(
    sqlite_factory, sample_recording, fake_user_id
):
    """run_assessment() should create Segment and SqiResult rows in DB."""
    from app.services.assessment_service import create_assessment_job, run_assessment
    from app.schemas.assessment_schemas import AssessJobRequest

    async with sqlite_factory() as db:
        request = AssessJobRequest(
            recording_id=sample_recording.id,
            window_duration_seconds=30,
            overlap_seconds=0,
            signal_column="ecg",
            sampling_rate=250,
        )
        job = await create_assessment_job(db, request, fake_user_id)
        await db.commit()
        job_id = job.id

    # Run full pipeline with real ECG fixture
    await run_assessment(job_id, sqlite_factory)

    async with sqlite_factory() as db:
        seg_result = await db.execute(
            select(Segment).where(Segment.assessment_job_id == job_id)
        )
        segments = list(seg_result.scalars().all())

    assert len(segments) >= 1, "At least one segment must be created"

    # Verify SQI results exist for first segment
    async with sqlite_factory() as db:
        sqi_result = await db.execute(
            select(SqiResult).where(SqiResult.segment_id == segments[0].id)
        )
        sqi_rows = list(sqi_result.scalars().all())

    assert len(sqi_rows) >= 1, "SQI results must exist for each segment"


@pytest.mark.asyncio
async def test_job_results_returns_summary_with_counts(
    sqlite_factory, sample_recording, fake_user_id
):
    """get_job_results must return a summary dict with accepted/rejected counts."""
    from app.services.assessment_service import create_assessment_job, get_job_results, run_assessment
    from app.schemas.assessment_schemas import AssessJobRequest

    async with sqlite_factory() as db:
        request = AssessJobRequest(
            recording_id=sample_recording.id,
            window_duration_seconds=30,
            overlap_seconds=0,
            signal_column="ecg",
            sampling_rate=250,
        )
        job = await create_assessment_job(db, request, fake_user_id)
        await db.commit()
        job_id = job.id

    await run_assessment(job_id, sqlite_factory)

    async with sqlite_factory() as db:
        results = await get_job_results(db, job_id)

    summary = results.summary
    assert "accepted_count" in summary
    assert "rejected_count" in summary
    assert "uncomputable_count" in summary
    assert "total_segments" in summary
    assert "acceptance_rate_pct" in summary
    assert "verdict" in summary
    assert summary["total_segments"] >= 1
    # All counts must be non-negative integers
    assert summary["accepted_count"] >= 0
    assert summary["rejected_count"] >= 0
    assert summary["uncomputable_count"] >= 0
