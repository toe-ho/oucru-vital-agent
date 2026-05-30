"""Pydantic v2 schemas for Assessment Job endpoints."""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class AssessJobRequest(BaseModel):
    """Request body for creating an assessment job."""

    recording_id: uuid.UUID
    window_duration_seconds: int = Field(default=30, gt=0)
    overlap_seconds: int = Field(default=0, ge=0)
    signal_column: str
    sampling_rate: int = Field(gt=0)
    metrics: Optional[list[str]] = None
    notes: Optional[str] = None


class AssessJobResponse(BaseModel):
    """Public representation of an AssessmentJob row."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    recording_id: uuid.UUID
    status: str
    current_step: Optional[str]
    progress_pct: Optional[Decimal]
    total_segments: Optional[int]
    processed_segments: int
    error_message: Optional[str]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime


class SegmentResult(BaseModel):
    """Public representation of a Segment row."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    segment_number: int
    start_time: Optional[float]
    end_time: Optional[float]
    classification: str
    quality_score: Optional[float]
    sqi_summary: Optional[dict]


class EffectiveSegmentResult(SegmentResult):
    """Segment result with effective classification (may differ from DB after overrides)."""

    effective_classification: str


class JobResultsResponse(BaseModel):
    """Full results for a completed assessment job."""

    job: AssessJobResponse
    segments: list[EffectiveSegmentResult]
    summary: dict


class AgentLogEntry(BaseModel):
    """Public representation of an AgentLog row."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    step_number: int
    stage: str
    tool_called: Optional[str]
    output_summary: Optional[str]
    reasoning: Optional[str]
    duration_ms: Optional[int]
    status: str
