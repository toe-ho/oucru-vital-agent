"""Segment, SqiResult, and SegmentOverrideEvent ORM models."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Segment(Base):
    __tablename__ = "segments"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    assessment_job_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("assessment_jobs.id", ondelete="CASCADE"), nullable=False
    )
    recording_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("recordings.id", ondelete="CASCADE"), nullable=False
    )
    segment_number: Mapped[int] = mapped_column(nullable=False)
    start_time: Mapped[float | None]
    end_time: Mapped[float | None]
    duration: Mapped[float | None]
    classification: Mapped[str] = mapped_column(String(16), nullable=False, default="pending")
    quality_score: Mapped[float | None]
    sqi_summary: Mapped[dict | None] = mapped_column(JSONB)

    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
    created_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))

    sqi_results: Mapped[list["SqiResult"]] = relationship(back_populates="segment")
    override_events: Mapped[list["SegmentOverrideEvent"]] = relationship(back_populates="segment")

    __table_args__ = (
        CheckConstraint(
            "classification IN ('accept','reject','pending','uncomputable')",
            name="ck_segment_classification",
        ),
        UniqueConstraint("assessment_job_id", "segment_number", name="uq_segment_job_number"),
    )


class SqiResult(Base):
    __tablename__ = "sqi_results"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    segment_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("segments.id", ondelete="CASCADE"), nullable=False
    )
    metric_name: Mapped[str] = mapped_column(String(64), nullable=False)
    metric_category: Mapped[str] = mapped_column(String(32), nullable=False)
    metric_value: Mapped[float | None]
    threshold_min: Mapped[float | None]
    threshold_max: Mapped[float | None]
    passed: Mapped[bool | None] = mapped_column(Boolean)

    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
    created_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))

    segment: Mapped["Segment"] = relationship(back_populates="sqi_results")

    __table_args__ = (
        CheckConstraint(
            "metric_category IN ('statistical','signal_processing','cardiac',"
            "'hrv_time','hrv_frequency','waveform','nonlinear','clinical')",
            name="ck_sqi_metric_category",
        ),
        UniqueConstraint("segment_id", "metric_name", name="uq_sqi_segment_metric"),
    )


class SegmentOverrideEvent(Base):
    __tablename__ = "segment_override_events"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    segment_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("segments.id", ondelete="CASCADE"), nullable=False
    )
    recording_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("recordings.id", ondelete="CASCADE"), nullable=False
    )
    assessment_job_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("assessment_jobs.id", ondelete="CASCADE"), nullable=False
    )
    label: Mapped[str] = mapped_column(String(8), nullable=False)
    reason_category: Mapped[str | None] = mapped_column(String(64))
    note: Mapped[str | None] = mapped_column(Text)
    supersedes_override_event_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("segment_override_events.id")
    )
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
    created_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)

    segment: Mapped["Segment"] = relationship(back_populates="override_events")

    __table_args__ = (
        CheckConstraint("label IN ('accept','reject')", name="ck_override_label"),
    )
