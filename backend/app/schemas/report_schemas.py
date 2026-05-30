"""Pydantic v2 schemas for Report and SegmentOverride endpoints."""

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ReportSummary(BaseModel):
    """Lightweight report representation for list views."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    recording_id: uuid.UUID
    assessment_job_id: uuid.UUID | None
    title: str | None
    json_schema_version: str
    generated_at: datetime | None
    is_stale: bool = False
    created_at: datetime


class ReportDetail(ReportSummary):
    """Full report with content fields."""

    content_json: dict | None
    content_html: str | None


class OverrideCreateRequest(BaseModel):
    """Request body for creating a segment override."""

    label: Literal["accept", "reject"]
    reason_category: str = Field(min_length=3)
    note: str = Field(min_length=10)


class OverrideResponse(BaseModel):
    """Public representation of a SegmentOverrideEvent."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    segment_id: uuid.UUID
    recording_id: uuid.UUID
    label: str
    reason_category: str | None
    note: str | None
    supersedes_override_event_id: uuid.UUID | None
    created_at: datetime
    created_by: uuid.UUID


class FeedbackCandidateRequest(BaseModel):
    """Request to propose a clinical threshold change based on an override."""

    source_override_event_id: uuid.UUID
    proposed_threshold_key: str
    proposed_value: dict
    rationale: str
