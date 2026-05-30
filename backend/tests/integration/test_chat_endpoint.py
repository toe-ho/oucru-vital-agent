"""Integration tests for the chat API endpoints.

Uses SQLite in-memory DB + patched auth. Ollama is mocked.
"""

from __future__ import annotations

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
from app.models.recording_models import Recording


# ---------------------------------------------------------------------------
# SQLite helpers (mirrors test_assessment_pipeline.py pattern)
# ---------------------------------------------------------------------------

def _sqlite_metadata() -> MetaData:
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


def _make_factory(engine):
    return async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


@pytest.fixture
async def sqlite_factory():
    engine = _make_engine()
    meta = _sqlite_metadata()
    async with engine.begin() as conn:
        await conn.run_sync(meta.create_all)
    factory = _make_factory(engine)
    yield factory
    await engine.dispose()


@pytest.fixture
def fake_user_id():
    return uuid.uuid4()


@pytest.fixture
async def sample_recording(sqlite_factory, fake_user_id):
    now = datetime.now(timezone.utc)
    rec = Recording(
        id=uuid.uuid4(),
        filename="test_ecg.csv",
        original_filename="test_ecg.csv",
        file_format="csv",
        signal_type="ecg",
        sampling_rate=250.0,
        duration_seconds=30.0,
        channel_count=1,
        status="completed",
        created_by=fake_user_id,
        created_at=now,
        updated_at=now,
    )
    async with sqlite_factory() as db:
        db.add(rec)
        await db.commit()
    return rec


def _build_app(sqlite_factory, fake_user_id):
    from app.main import app
    from app.auth.auth_dependencies import get_current_user
    from app.core.database import get_db

    fake_user = MagicMock()
    fake_user.id = fake_user_id
    fake_user.status = "active"

    async def _db_override():
        async with sqlite_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_db] = _db_override
    app.dependency_overrides[get_current_user] = lambda: fake_user
    return app


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_chat_returns_assistant_message(sqlite_factory, sample_recording, fake_user_id):
    """POST /api/chat must return a ChatMessageResponse with role='assistant'."""
    app = _build_app(sqlite_factory, fake_user_id)

    with patch("app.api.chat_router._orchestrator") as mock_orch:
        mock_orch.chat = AsyncMock(return_value="The acceptance rate is 80%.")

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(
                "/api/chat",
                json={"recording_id": str(sample_recording.id), "message": "What is the quality?"},
            )

    app.dependency_overrides.clear()
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["role"] == "assistant"
    assert "content" in body
    assert len(body["content"]) > 0
    assert "conversation_id" in body


@pytest.mark.asyncio
async def test_chat_creates_conversation_on_first_message(sqlite_factory, sample_recording, fake_user_id):
    """First message to a recording must create a new Conversation row."""
    from sqlalchemy import select
    from app.models.report_models import Conversation

    app = _build_app(sqlite_factory, fake_user_id)

    with patch("app.api.chat_router._orchestrator") as mock_orch:
        mock_orch.chat = AsyncMock(return_value="Test response.")

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(
                "/api/chat",
                json={"recording_id": str(sample_recording.id), "message": "Hello"},
            )

    app.dependency_overrides.clear()
    assert resp.status_code == 200, resp.text

    async with sqlite_factory() as db:
        result = await db.execute(
            select(Conversation).where(Conversation.recording_id == sample_recording.id)
        )
        conversations = result.scalars().all()

    assert len(conversations) >= 1


@pytest.mark.asyncio
async def test_chat_missing_recording_returns_404(sqlite_factory, fake_user_id):
    """POST /api/chat with a non-existent recording_id must return 404."""
    app = _build_app(sqlite_factory, fake_user_id)

    with patch("app.api.chat_router._orchestrator") as mock_orch:
        mock_orch.chat = AsyncMock(return_value="Should not reach here.")

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(
                "/api/chat",
                json={"recording_id": str(uuid.uuid4()), "message": "Hello"},
            )

    app.dependency_overrides.clear()
    assert resp.status_code == 404
    assert resp.json()["error"] == "RecordingNotFound"
