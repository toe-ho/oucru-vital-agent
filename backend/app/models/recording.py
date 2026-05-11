from __future__ import annotations

from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import AuditMixin, Base, UUIDPrimaryKeyMixin


class Recording(Base, UUIDPrimaryKeyMixin, AuditMixin):
    __tablename__ = "recordings"

    filename: Mapped[str] = mapped_column(String(512), nullable=False)
    storage_uri: Mapped[str] = mapped_column(Text, nullable=False)
    signal_type: Mapped[str] = mapped_column(String(10), nullable=False)  # "ecg" | "ppg"
    sampling_rate: Mapped[int] = mapped_column(Integer, nullable=False)
    file_format: Mapped[str] = mapped_column(String(20), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    duration_seconds: Mapped[float | None] = mapped_column(nullable=True)
    checksum_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)

    subject_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    device_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # uploaded | processing | completed | failed | deleted
    status: Mapped[str] = mapped_column(String(20), default="uploaded", nullable=False)

    assessment_jobs: Mapped[list] = relationship("AssessmentJob", back_populates="recording")
    conversations: Mapped[list] = relationship("Conversation", back_populates="recording")
