"""Pydantic v2 schemas for Chat endpoints."""

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ChatMessageRequest(BaseModel):
    """Request body for sending a chat message."""

    recording_id: uuid.UUID
    message: str = Field(min_length=1)
    conversation_id: Optional[uuid.UUID] = None
    assessment_job_id: Optional[uuid.UUID] = None
    report_id: Optional[uuid.UUID] = None


class ChatMessageResponse(BaseModel):
    """Public representation of a single ChatMessage."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    conversation_id: uuid.UUID
    role: str
    content: str
    sources: Optional[list] = None
    created_at: datetime


class ConversationResponse(BaseModel):
    """Public representation of a Conversation with its messages."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    recording_id: uuid.UUID
    assessment_job_id: Optional[uuid.UUID] = None
    report_id: Optional[uuid.UUID] = None
    title: Optional[str] = None
    created_at: datetime
    messages: list[ChatMessageResponse] = []
