import asyncio
import sys
from pathlib import Path
from unittest.mock import AsyncMock, patch

import numpy as np
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.main import app
from app.models.base import Base
from app.db.session import get_db

TEST_DATABASE_URL = "postgresql+asyncpg://oucru:oucru@localhost:5432/oucru_test"

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = async_sessionmaker(test_engine, expire_on_commit=False)


@pytest_asyncio.fixture(scope="session", autouse=True)
async def create_tables():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db():
    async with TestSessionLocal() as session:
        async with session.begin():
            yield session
            await session.rollback()


@pytest_asyncio.fixture
async def async_client(db):
    app.dependency_overrides[get_db] = lambda: db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()


@pytest.fixture
def ppg_signal():
    t = np.linspace(0, 30, 3000)
    hr_hz = 70 / 60
    return (0.6 * np.sin(2 * np.pi * hr_hz * t) + 0.05 * np.random.randn(3000)).tolist()


@pytest.fixture
def ecg_signal():
    t = np.linspace(0, 30, 15000)
    hr_hz = 70 / 60
    return (0.8 * np.sin(2 * np.pi * hr_hz * t) + 0.02 * np.random.randn(15000)).tolist()


@pytest.fixture
def mock_ollama():
    mock_result = {
        "assessment_complete": True,
        "overall_verdict": "acceptable",
        "acceptance_rate": 0.82,
        "key_findings": ["Good signal quality throughout"],
        "flagged_segments": [],
        "recommendations": ["Continue monitoring"],
        "escalate": False,
        "escalation_reason": None,
    }
    import json
    with patch("smolagents.CodeAgent.run", return_value=json.dumps(mock_result)):
        yield mock_result
