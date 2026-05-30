"""Recording and AssessmentJob ORM models."""

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Recording(Base):
    __tablename__ = "recordings"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_format: Mapped[str] = mapped_column(String(16), nullable=False)
    signal_type: Mapped[str] = mapped_column(String(8), nullable=False)
    sampling_rate: Mapped[float | None]
    duration_seconds: Mapped[float | None]
    channel_count: Mapped[int] = mapped_column(Integer, default=1)
    file_size_bytes: Mapped[int | None]
    checksum_sha256: Mapped[str | None] = mapped_column(String(64))
    storage_uri: Mapped[str | None] = mapped_column(String(500))
    subject_id: Mapped[str | None] = mapped_column(String(128))
    device_id: Mapped[str | None] = mapped_column(String(128))
    notes: Mapped[str | None] = mapped_column(Text)
    agent_summary: Mapped[dict | None] = mapped_column(JSONB)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="uploaded")

    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now(), nullable=False
    )
    deleted_at: Mapped[datetime | None]
    created_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    updated_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    deleted_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))

    assessment_jobs: Mapped[list["AssessmentJob"]] = relationship(back_populates="recording")

    __table_args__ = (
        CheckConstraint(
            "file_format IN ('edf','csv','parquet','wfdb')", name="ck_recording_format"
        ),
        CheckConstraint("signal_type IN ('ecg','ppg')", name="ck_recording_signal_type"),
        CheckConstraint(
            "status IN ('uploaded','processing','completed','failed')",
            name="ck_recording_status",
        ),
    )


class AssessmentJob(Base):
    __tablename__ = "assessment_jobs"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    recording_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("recordings.id", ondelete="CASCADE"), nullable=False
    )
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="queued")
    current_step: Mapped[str | None] = mapped_column(String(64))
    progress_pct: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    total_segments: Mapped[int | None]
    processed_segments: Mapped[int] = mapped_column(Integer, default=0)
    parameters: Mapped[dict | None] = mapped_column(JSONB)
    error_message: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime | None]
    completed_at: Mapped[datetime | None]

    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now(), nullable=False
    )
    deleted_at: Mapped[datetime | None]
    created_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    updated_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    deleted_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))

    recording: Mapped["Recording"] = relationship(back_populates="assessment_jobs")

    __table_args__ = (
        CheckConstraint(
            "status IN ('queued','processing','completed','failed','cancelled')",
            name="ck_job_status",
        ),
    )
