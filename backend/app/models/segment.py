from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Float, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDPrimaryKeyMixin


class Segment(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "segments"

    assessment_job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("assessment_jobs.id", ondelete="CASCADE"), nullable=False
    )
    recording_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("recordings.id", ondelete="CASCADE"), nullable=False
    )

    segment_number: Mapped[int] = mapped_column(Integer, nullable=False)
    start_time: Mapped[float] = mapped_column(Float, nullable=False)
    end_time: Mapped[float] = mapped_column(Float, nullable=False)

    # accept | reject | pending | uncomputable
    classification: Mapped[str] = mapped_column(nullable=False, default="pending")
    quality_score: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Denormalized snapshot for fast dashboard queries
    sqi_summary: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    # Rules that caused rejection
    failed_rules: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)

    created_at: Mapped[datetime] = mapped_column(nullable=False)

    assessment_job: Mapped = relationship("AssessmentJob", back_populates="segments")
    sqi_results: Mapped[list] = relationship("SQIResult", back_populates="segment")
