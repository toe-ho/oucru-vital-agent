"""REST endpoints for the grounded chatbot."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.agent_orchestrator import AgentOrchestrator
from app.auth.auth_dependencies import get_current_user
from app.core.database import get_db
from app.core.errors import AppError
from app.core.settings import settings
from app.models.user_models import User
from app.schemas.chat_schemas import (
    ChatMessageRequest,
    ChatMessageResponse,
    ConversationResponse,
)
from app.services import chat_service

router = APIRouter(tags=["chat"])

# Module-level orchestrator instance (shared across requests)
_orchestrator = AgentOrchestrator(settings)


@router.post("", response_model=ChatMessageResponse)
async def send_chat_message(
    request: ChatMessageRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ChatMessageResponse:
    """Send a message and receive a grounded assistant response."""
    from app.models.recording_models import Recording
    from sqlalchemy import select

    rec_result = await db.execute(
        select(Recording).where(
            Recording.id == request.recording_id,
            Recording.deleted_at.is_(None),
        )
    )
    if rec_result.scalar_one_or_none() is None:
        raise AppError(404, "RecordingNotFound", f"Recording {request.recording_id} not found.")

    return await chat_service.send_message(db, request, current_user.id, _orchestrator)


@router.get("/conversations/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ConversationResponse:
    """Fetch a conversation and all its messages."""
    conv = await chat_service.get_conversation(db, conversation_id)
    if conv is None:
        raise AppError(404, "ConversationNotFound", f"Conversation {conversation_id} not found.")
    return ConversationResponse.model_validate(conv)
