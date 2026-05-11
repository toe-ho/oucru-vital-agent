from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import AuditMixin, Base, UUIDPrimaryKeyMixin


class Conversation(Base, UUIDPrimaryKeyMixin, AuditMixin):
    __tablename__ = "conversations"

    recording_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("recordings.id", ondelete="CASCADE"), nullable=False
    )
    assessment_job_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("assessment_jobs.id", ondelete="SET NULL"), nullable=True
    )
    report_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("reports.id", ondelete="SET NULL"), nullable=True
    )
    title: Mapped[str | None] = mapped_column(Text, nullable=True)

    recording: Mapped = relationship("Recording", back_populates="conversations")
    assessment_job: Mapped = relationship("AssessmentJob", back_populates="conversations")
    messages: Mapped[list] = relationship("ChatMessage", back_populates="conversation")


class ChatMessage(Base, UUIDPrimaryKeyMixin, AuditMixin):
    __tablename__ = "chat_messages"

    conversation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False
    )
    role: Mapped[str] = mapped_column(Text, nullable=False)  # user | assistant
    content: Mapped[str] = mapped_column(Text, nullable=False)
    sources: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)

    conversation: Mapped[Conversation] = relationship("Conversation", back_populates="messages")
