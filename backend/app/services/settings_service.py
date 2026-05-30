"""CRUD operations for the Setting model."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.settings_models import Setting


async def get_all_settings(db: AsyncSession) -> list[Setting]:
    """Return all non-deleted settings."""
    result = await db.execute(select(Setting).where(Setting.deleted_at.is_(None)))
    return list(result.scalars().all())


async def get_setting_by_key(db: AsyncSession, key: str) -> Setting | None:
    """Return a single setting by key, or None if not found."""
    result = await db.execute(
        select(Setting).where(Setting.key == key, Setting.deleted_at.is_(None))
    )
    return result.scalar_one_or_none()


async def update_setting(
    db: AsyncSession, key: str, value: dict, updated_by: uuid.UUID
) -> Setting:
    """Update a setting's value by key; raises KeyError if not found."""
    setting = await get_setting_by_key(db, key)
    if setting is None:
        raise KeyError(f"Setting '{key}' not found.")
    setting.value = value
    setting.updated_by = updated_by
    await db.flush()
    return setting
