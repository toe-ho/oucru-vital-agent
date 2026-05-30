"""Seed script: inserts default roles and settings if they don't already exist."""

import asyncio

from sqlalchemy import select

from app.core.database import async_session_factory
from app.models.settings_models import Setting
from app.models.user_models import Role

_ROLES = ["admin", "researcher", "reviewer", "readonly"]

_DEFAULT_SETTINGS = [
    {
        "key": "sqi_thresholds",
        "category": "sqi",
        "description": "SQI metric acceptance thresholds",
        "value": {
            "snr": {"min": 8.0, "max": None},
            "kurtosis": {"min": -1.5, "max": 10.0},
            "perfusion_index": {"min": 0.5, "max": None},
            "zero_crossing_rate": {"min": None, "max": 0.5},
            "skewness": {"min": -2.0, "max": 2.0},
        },
    },
    {
        "key": "segmentation_config",
        "category": "segmentation",
        "description": "Default signal segmentation parameters",
        "value": {
            "window_duration_seconds": 30,
            "overlap_seconds": 0,
            "split_type": "time",
            "min_segment_duration": 5,
        },
    },
    {
        "key": "agent_config",
        "category": "agent",
        "description": "AI agent runtime configuration",
        "value": {
            "max_steps": 20,
            "model": "qwen3:8b",
            "base_url": "http://ollama:11434",
            "temperature": 0.1,
            "timeout_seconds": 300,
        },
    },
]


async def seed() -> None:
    async with async_session_factory() as db:
        # Seed roles
        for role_name in _ROLES:
            result = await db.execute(select(Role).where(Role.name == role_name))
            if result.scalar_one_or_none() is None:
                db.add(Role(name=role_name, description=f"Built-in {role_name} role"))
                print(f"  [seed] Created role: {role_name}")

        # Seed settings
        for cfg in _DEFAULT_SETTINGS:
            result = await db.execute(
                select(Setting).where(
                    Setting.key == cfg["key"], Setting.deleted_at.is_(None)
                )
            )
            if result.scalar_one_or_none() is None:
                db.add(
                    Setting(
                        key=cfg["key"],
                        category=cfg["category"],
                        description=cfg["description"],
                        value=cfg["value"],
                    )
                )
                print(f"  [seed] Created setting: {cfg['key']}")

        await db.commit()
        print("[seed] Done.")


if __name__ == "__main__":
    asyncio.run(seed())
