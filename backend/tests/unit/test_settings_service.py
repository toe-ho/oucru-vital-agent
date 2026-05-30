"""Unit tests for settings_service using an in-memory SQLite async DB.

SQLite does not support PostgreSQL JSONB. We create a minimal SQLite-compatible
Setting model and patch it into settings_service for the duration of the tests.
"""

import uuid
from unittest.mock import patch

import pytest
from sqlalchemy import JSON, String, UniqueConstraint
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


# ---------------------------------------------------------------------------
# SQLite-compatible Setting replica (JSON instead of JSONB, no FK columns)
# ---------------------------------------------------------------------------

class _TestBase(DeclarativeBase):
    pass


class _Setting(_TestBase):
    """Mirrors app.models.settings_models.Setting with SQLite-safe types."""

    __tablename__ = "settings"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    key: Mapped[str] = mapped_column(String(128), nullable=False)
    value: Mapped[dict | None] = mapped_column(JSON)
    category: Mapped[str] = mapped_column(String(32), nullable=False, default="sqi")
    description: Mapped[str | None] = mapped_column(String(500))
    deleted_at: Mapped[str | None] = mapped_column(default=None)
    updated_by: Mapped[uuid.UUID | None] = mapped_column(default=None)

    __table_args__ = (UniqueConstraint("key", name="uq_setting_key_active"),)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
async def db_session():
    engine = create_async_engine(TEST_DATABASE_URL)
    async with engine.begin() as conn:
        await conn.run_sync(_TestBase.metadata.create_all)

    factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with factory() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(_TestBase.metadata.drop_all)
    await engine.dispose()


async def _add(db: AsyncSession, key: str, value: dict) -> _Setting:
    s = _Setting(key=key, value=value)
    db.add(s)
    await db.flush()
    return s


# ---------------------------------------------------------------------------
# Tests — patch `Setting` inside settings_service to use our SQLite model
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_by_key_returns_existing(db_session):
    await _add(db_session, "sqi_thresholds", {"snr": {"min": 8.0}})
    with patch("app.services.settings_service.Setting", _Setting):
        from app.services.settings_service import get_setting_by_key
        result = await get_setting_by_key(db_session, "sqi_thresholds")
    assert result is not None
    assert result.key == "sqi_thresholds"
    assert result.value == {"snr": {"min": 8.0}}


@pytest.mark.asyncio
async def test_get_by_key_returns_none_for_missing(db_session):
    with patch("app.services.settings_service.Setting", _Setting):
        from app.services.settings_service import get_setting_by_key
        result = await get_setting_by_key(db_session, "nonexistent")
    assert result is None


@pytest.mark.asyncio
async def test_update_setting_changes_value(db_session):
    await _add(db_session, "sqi_thresholds", {"snr": {"min": 8.0}})
    actor_id = uuid.uuid4()
    with patch("app.services.settings_service.Setting", _Setting):
        from app.services.settings_service import update_setting
        updated = await update_setting(db_session, "sqi_thresholds", {"snr": {"min": 10.0}}, actor_id)
    assert updated.value == {"snr": {"min": 10.0}}
    assert updated.updated_by == actor_id


@pytest.mark.asyncio
async def test_update_setting_raises_for_missing_key(db_session):
    with patch("app.services.settings_service.Setting", _Setting):
        from app.services.settings_service import update_setting
        with pytest.raises(KeyError, match="nonexistent"):
            await update_setting(db_session, "nonexistent", {}, uuid.uuid4())
