"""CRUD for settings table with in-memory threshold cache."""
from __future__ import annotations

_threshold_cache: dict = {}


def get_threshold_cache() -> dict:
    return _threshold_cache


def invalidate_threshold_cache() -> None:
    global _threshold_cache
    _threshold_cache = {}


async def get_thresholds(db) -> dict:
    from sqlalchemy import select
    from app.models.settings import Setting

    setting = await db.scalar(select(Setting).where(Setting.key == "sqi_thresholds"))
    if setting:
        global _threshold_cache
        _threshold_cache = setting.value
        return setting.value

    from app.config import agent_config
    return agent_config.sqi_thresholds


async def update_thresholds(thresholds: dict, user_id, db) -> dict:
    from sqlalchemy import select
    from app.models.settings import Setting
    import uuid
    from datetime import datetime, timezone

    setting = await db.scalar(select(Setting).where(Setting.key == "sqi_thresholds"))
    if setting:
        setting.value = thresholds
        setting.updated_by = user_id
    else:
        db.add(Setting(key="sqi_thresholds", value=thresholds, created_by=user_id))

    await db.commit()
    invalidate_threshold_cache()
    return thresholds
