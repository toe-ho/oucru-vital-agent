"""Chat service: conversation management and message dispatch."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.report_models import ChatMessage, Conversation
from app.schemas.chat_schemas import ChatMessageRequest, ChatMessageResponse
from app.services.chat_grounding_service import retrieve_context


async def get_or_create_conversation(
    db: AsyncSession,
    recording_id: uuid.UUID,
    user_id: uuid.UUID,
    assessment_job_id: Optional[uuid.UUID] = None,
    report_id: Optional[uuid.UUID] = None,
) -> Conversation:
    """Return existing conversation (within 24h) or create a new one."""
    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
    result = await db.execute(
        select(Conversation)
        .where(
            Conversation.recording_id == recording_id,
            Conversation.created_by == user_id,
            Conversation.created_at >= cutoff,
            Conversation.deleted_at.is_(None),
        )
        .order_by(Conversation.created_at.desc())
        .limit(1)
    )
    existing = result.scalar_one_or_none()
    if existing is not None:
        return existing

    conv = Conversation(
        recording_id=recording_id,
        assessment_job_id=assessment_job_id,
        report_id=report_id,
        title=f"Chat for recording {recording_id}",
        created_by=user_id,
    )
    db.add(conv)
    await db.flush()
    return conv


async def send_message(
    db: AsyncSession,
    request: ChatMessageRequest,
    user_id: uuid.UUID,
    orchestrator,
) -> ChatMessageResponse:
    """Persist user message, call LLM, persist and return assistant message."""
    conv = await get_or_create_conversation(
        db,
        recording_id=request.recording_id,
        user_id=user_id,
        assessment_job_id=request.assessment_job_id,
        report_id=request.report_id,
    )

    # Persist user message
    user_msg = ChatMessage(
        conversation_id=conv.id,
        role="user",
        content=request.message,
        created_by=user_id,
    )
    db.add(user_msg)
    await db.flush()

    # Retrieve grounding context
    context = await retrieve_context(
        db,
        recording_id=request.recording_id,
        assessment_job_id=request.assessment_job_id,
        report_id=request.report_id,
    )

    # Generate assistant reply
    assistant_content = await orchestrator.chat(context, request.message)

    # Build sources list
    sources: list = [str(request.recording_id)]
    if request.assessment_job_id:
        sources.append(str(request.assessment_job_id))

    # Persist assistant message
    assistant_msg = ChatMessage(
        conversation_id=conv.id,
        role="assistant",
        content=assistant_content,
        sources=sources,
        created_by=user_id,
    )
    db.add(assistant_msg)
    await db.flush()

    return ChatMessageResponse(
        id=assistant_msg.id,
        conversation_id=conv.id,
        role="assistant",
        content=assistant_content,
        sources=sources,
        created_at=assistant_msg.created_at,
    )


async def get_conversation(
    db: AsyncSession, conversation_id: uuid.UUID
) -> Optional[Conversation]:
    """Load a conversation with its messages eagerly."""
    result = await db.execute(
        select(Conversation)
        .where(Conversation.id == conversation_id, Conversation.deleted_at.is_(None))
        .options(selectinload(Conversation.messages))
    )
    return result.scalar_one_or_none()
