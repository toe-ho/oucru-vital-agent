from __future__ import annotations

from datetime import datetime

from sqlalchemy import String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import AuditMixin, Base, UUIDPrimaryKeyMixin


class Setting(Base, UUIDPrimaryKeyMixin, AuditMixin):
    __tablename__ = "settings"

    key: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    value: Mapped[dict] = mapped_column(JSONB, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
