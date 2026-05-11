from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import AuditMixin, Base, UUIDPrimaryKeyMixin


class AssessmentJob(Base, UUIDPrimaryKeyMixin, AuditMixin):
    __tablename__ = "assessment_jobs"

    recording_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("recordings.id", ondelete="CASCADE"), nullable=False
    )
    # queued | processing | completed | failed | cancelled
    status: Mapped[str] = mapped_column(Text, default="queued", nullable=False)

    # Snapshot of the request config (segment_duration, rule_dict, etc.)
    parameters: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    total_segments: Mapped[int | None] = mapped_column(Integer, nullable=True)
    processed_segments: Mapped[int | None] = mapped_column(Integer, nullable=True)
    progress_pct: Mapped[float | None] = mapped_column(nullable=True)
    current_stage: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Final verdict
    overall_verdict: Mapped[str | None] = mapped_column(Text, nullable=True)
    acceptance_rate: Mapped[float | None] = mapped_column(nullable=True)
    escalated: Mapped[bool] = mapped_column(default=False, nullable=False)
    escalation_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    agent_interpretation: Mapped[str | None] = mapped_column(Text, nullable=True)

    recording: Mapped = relationship("Recording", back_populates="assessment_jobs")
    segments: Mapped[list] = relationship("Segment", back_populates="assessment_job")
    reports: Mapped[list] = relationship("Report", back_populates="assessment_job")
    agent_logs: Mapped[list] = relationship("AgentLog", back_populates="assessment_job")
    conversations: Mapped[list] = relationship("Conversation", back_populates="assessment_job")
