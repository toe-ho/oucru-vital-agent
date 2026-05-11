from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import AuditMixin, Base, UUIDPrimaryKeyMixin


class Report(Base, UUIDPrimaryKeyMixin, AuditMixin):
    __tablename__ = "reports"

    assessment_job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("assessment_jobs.id", ondelete="CASCADE"), nullable=False
    )
    recording_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("recordings.id", ondelete="CASCADE"), nullable=False
    )

    # generating | completed | failed
    status: Mapped[str] = mapped_column(Text, default="generating", nullable=False)
    format: Mapped[str] = mapped_column(Text, nullable=False)  # json | html | pdf

    # Canonical source — HTML and PDF are always derived from this
    content_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    content_html: Mapped[str | None] = mapped_column(Text, nullable=True)
    pdf_file_path: Mapped[str | None] = mapped_column(Text, nullable=True)

    include_waveform_plots: Mapped[bool] = mapped_column(default=True, nullable=False)

    assessment_job: Mapped = relationship("AssessmentJob", back_populates="reports")
