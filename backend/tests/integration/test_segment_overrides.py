"""Integration tests for segment override endpoints using SQLite in-memory DB."""

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
from app.models.segment_models import Segment, SegmentOverrideEvent
from app.models.user_models import Role, User, UserRole

_FIXTURES = pathlib.Path(__file__).parent.parent / "fixtures"
_ECG_CSV = _FIXTURES / "sample_ecg.csv"


# ---------------------------------------------------------------------------
# SQLite in-memory setup (same pattern as test_assessment_pipeline.py)
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
async def sample_segment(sqlite_factory, fake_user_id):
    """Insert Recording + AssessmentJob + Segment rows."""
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
            processed_segments=1, created_by=fake_user_id,
        )
        db.add(job)
        await db.flush()

        seg = Segment(
            id=uuid.uuid4(), assessment_job_id=job.id, recording_id=rec.id,
            segment_number=1, start_time=0.0, end_time=30.0, duration=30.0,
            classification="accept", quality_score=0.85,
        )
        db.add(seg)
        await db.commit()
    return seg


# ---------------------------------------------------------------------------
# Helper: get the exact _guard callable used in the override POST route
# ---------------------------------------------------------------------------

def _get_role_dependency():
    """Return the exact require_roles._guard closure from POST /{segment_id}/overrides."""
    from app.main import app

    for route in app.routes:
        if (
            hasattr(route, "path")
            and route.path == "/api/segments/{segment_id}/overrides"
            and "POST" in getattr(route, "methods", [])
        ):
            # Walk dependant.dependencies to find the _guard closure
            for dep in route.dependant.dependencies:
                name = getattr(dep.call, "__qualname__", "")
                if "require_roles" in name:
                    return dep.call
    raise RuntimeError("Could not locate require_roles._guard dependency on POST /api/segments/{segment_id}/overrides")


# ---------------------------------------------------------------------------
# Helper: build app with SQLite + overridden auth
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
async def test_unauthorized_override_returns_403(sqlite_factory, sample_segment, fake_user_id):
    """A user without reviewer/admin role cannot POST an override (403)."""
    from app.main import app
    from app.core.database import get_db
    from app.auth.auth_dependencies import get_current_user

    fake_user = MagicMock()
    fake_user.id = fake_user_id
    fake_user.status = "active"

    async def _override_db():
        async with sqlite_factory() as session:
            yield session

    # Override the role guard with a function that always denies
    role_dep = _get_role_dependency()

    def _deny():
        from app.core.errors import AppError
        raise AppError(403, "Forbidden", "Requires one of roles: ['reviewer', 'admin']")

    app.dependency_overrides[get_db] = _override_db
    app.dependency_overrides[get_current_user] = lambda: fake_user
    app.dependency_overrides[role_dep] = _deny

    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(
                f"/api/segments/{sample_segment.id}/overrides",
                json={"label": "reject", "reason_category": "bad_signal",
                      "note": "This segment has poor signal quality"},
            )
        assert resp.status_code == 403, resp.text
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_reviewer_can_create_override(sqlite_factory, sample_segment, fake_user_id):
    """A reviewer can POST an override and get 201 back."""
    from app.main import app
    from app.core.database import get_db
    from app.auth.auth_dependencies import get_current_user

    fake_user = MagicMock()
    fake_user.id = fake_user_id
    fake_user.status = "active"

    async def _override_db():
        async with sqlite_factory() as session:
            yield session

    # Override the role guard to pass through (simulate reviewer)
    role_dep = _get_role_dependency()

    def _allow():
        return fake_user

    app.dependency_overrides[get_db] = _override_db
    app.dependency_overrides[get_current_user] = lambda: fake_user
    app.dependency_overrides[role_dep] = _allow

    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(
                f"/api/segments/{sample_segment.id}/overrides",
                json={
                    "label": "reject",
                    "reason_category": "poor_signal",
                    "note": "Manually reviewed and signal is too noisy",
                },
            )
        assert resp.status_code == 201, resp.text
        body = resp.json()
        assert body["label"] == "reject"
        assert body["segment_id"] == str(sample_segment.id)
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_override_history_append_only(sqlite_factory, sample_segment, fake_user_id):
    """Creating two overrides results in two events in history (append-only)."""
    from app.main import app
    from app.core.database import get_db
    from app.auth.auth_dependencies import get_current_user

    fake_user = MagicMock()
    fake_user.id = fake_user_id
    fake_user.status = "active"

    async def _override_db():
        async with sqlite_factory() as session:
            yield session

    role_dep = _get_role_dependency()

    def _allow():
        return fake_user

    app.dependency_overrides[get_db] = _override_db
    app.dependency_overrides[get_current_user] = lambda: fake_user
    app.dependency_overrides[role_dep] = _allow

    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            r1 = await client.post(
                f"/api/segments/{sample_segment.id}/overrides",
                json={"label": "reject", "reason_category": "noise",
                      "note": "First override: signal too noisy for analysis"},
            )
            assert r1.status_code == 201, r1.text

            r2 = await client.post(
                f"/api/segments/{sample_segment.id}/overrides",
                json={"label": "accept", "reason_category": "re_review",
                      "note": "Second override: re-reviewed and acceptable"},
            )
            assert r2.status_code == 201, r2.text

            history_resp = await client.get(f"/api/segments/{sample_segment.id}/overrides")
        assert history_resp.status_code == 200, history_resp.text
        history = history_resp.json()
        assert len(history) == 2, f"Expected 2 override events, got {len(history)}"
        labels = [e["label"] for e in history]
        assert "reject" in labels
        assert "accept" in labels
    finally:
        app.dependency_overrides.clear()
