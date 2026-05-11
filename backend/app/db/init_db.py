from __future__ import annotations

import json
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.settings import Setting
from app.models.user import Role


DEFAULT_ROLES = ["admin", "researcher", "reviewer", "readonly"]

DEFAULT_SETTINGS = {
    "sqi_thresholds": {
        "mean_hr": {"min": 40, "max": 200},
        "sdnn": {"min": 7.93, "max": 676},
        "rmssd": {"min": 5.0, "max": 300},
        "pnn50": {"min": 0.0, "max": 1.0},
        "kurtosis": {"min": -1.5, "max": 10.0},
        "skewness": {"min": -3.0, "max": 3.0},
        "snr": {"min": 8.0, "max": None},
        "lf_hf_ratio": {"min": 0.2, "max": 5.0},
    },
    "segmentation_config": {
        "window_duration_seconds": 30,
        "overlap": 0.0,
        "split_type": 0,
    },
}


async def seed_roles(db: AsyncSession) -> None:
    from sqlalchemy import select

    for name in DEFAULT_ROLES:
        existing = await db.scalar(select(Role).where(Role.name == name))
        if not existing:
            db.add(Role(name=name))
    await db.commit()


async def seed_settings(db: AsyncSession) -> None:
    from sqlalchemy import select

    for key, value in DEFAULT_SETTINGS.items():
        existing = await db.scalar(select(Setting).where(Setting.key == key))
        if not existing:
            db.add(Setting(key=key, value=value))
    await db.commit()
