import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies import get_current_user, require_roles
from app.exceptions import NotFoundError, ValidationError
from app.models.assessment import AssessmentJob
from app.models.conversation import ChatMessage, Conversation
from app.models.recording import Recording
from app.models.user import User

router = APIRouter(tags=["chat"])


@router.post("/conversations", status_code=201)
async def create_conversation(
    body: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "researcher", "reviewer")),
):
    recording_id = uuid.UUID(body["recording_id"])
    rec = await db.get(Recording, recording_id)
    if not rec:
        raise NotFoundError(f"Recording {recording_id} not found")

    conv = Conversation(
        recording_id=recording_id,
        assessment_job_id=uuid.UUID(body["assessment_job_id"]) if body.get("assessment_job_id") else None,
        report_id=uuid.UUID(body["report_id"]) if body.get("report_id") else None,
        title=body.get("title"),
        created_by=current_user.id,
    )
    db.add(conv)
    await db.commit()
    await db.refresh(conv)

    return {
        "conversation_id": str(conv.id),
        "recording_id": str(conv.recording_id),
        "assessment_job_id": str(conv.assessment_job_id) if conv.assessment_job_id else None,
        "title": conv.title,
        "created_at": conv.created_at.isoformat(),
    }


@router.get("/conversations/{conversation_id}/messages")
async def get_messages(
    conversation_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from sqlalchemy import select
    conv = await db.get(Conversation, conversation_id)
    if not conv:
        raise NotFoundError(f"Conversation {conversation_id} not found")

    msgs = (await db.execute(
        select(ChatMessage)
        .where(ChatMessage.conversation_id == conversation_id)
        .order_by(ChatMessage.created_at)
    )).scalars().all()

    return {
        "conversation_id": str(conversation_id),
        "messages": [
            {"message_id": str(m.id), "role": m.role, "content": m.content,
             "sources": m.sources, "created_at": m.created_at.isoformat()}
            for m in msgs
        ],
    }


@router.post("/conversations/{conversation_id}/messages")
async def send_message(
    conversation_id: uuid.UUID,
    body: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "researcher", "reviewer")),
):
    conv = await db.get(Conversation, conversation_id)
    if not conv:
        raise NotFoundError(f"Conversation {conversation_id} not found")

    message = body.get("message", "").strip()
    if not message:
        raise ValidationError("message must not be empty")

    user_msg = ChatMessage(
        conversation_id=conversation_id,
        role="user",
        content=message,
        sources=[],
        created_by=current_user.id,
    )
    db.add(user_msg)
    await db.flush()

    response_text, sources = await _run_chat_agent(message, conv, db)

    assistant_msg = ChatMessage(
        conversation_id=conversation_id,
        role="assistant",
        content=response_text,
        sources=sources,
        created_by=current_user.id,
    )
    db.add(assistant_msg)
    await db.commit()

    return {
        "conversation_id": str(conversation_id),
        "user_message_id": str(user_msg.id),
        "assistant_message_id": str(assistant_msg.id),
        "response": response_text,
        "sources": sources,
    }


@router.post("/chat")
async def one_shot_chat(
    body: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "researcher", "reviewer")),
):
    recording_id = uuid.UUID(body["recording_id"])
    message = body.get("message", "").strip()
    if not message:
        raise ValidationError("message must not be empty")

    conv_id = body.get("conversation_id")
    if conv_id:
        conv = await db.get(Conversation, uuid.UUID(conv_id))
    else:
        rec = await db.get(Recording, recording_id)
        if not rec:
            raise NotFoundError(f"Recording {recording_id} not found")
        conv = Conversation(
            recording_id=recording_id,
            assessment_job_id=uuid.UUID(body["assessment_job_id"]) if body.get("assessment_job_id") else None,
            created_by=current_user.id,
        )
        db.add(conv)
        await db.flush()

    return await send_message.__wrapped__(conv.id, {"message": message}, db, current_user) if hasattr(send_message, "__wrapped__") else {
        "conversation_id": str(conv.id),
        "response": await _run_chat_agent_simple(message, conv, db),
        "sources": [],
    }


async def _run_chat_agent(message: str, conv: Conversation, db) -> tuple[str, list]:
    """Run the agent in chat mode with conversation context."""
    try:
        from app.agent.tool_registry import ALL_TOOLS
        from app.agent.prompts.system_prompt import SYSTEM_PROMPT as system_prompt
        from app.config import agent_config
        from smolagents import CodeAgent, OllamaModel

        job_context = ""
        if conv.assessment_job_id:
            job = await db.get(AssessmentJob, conv.assessment_job_id)
            if job:
                job_context = (
                    f"The user is asking about assessment job {job.id}.\n"
                    f"Signal: {job.recording_id}, Verdict: {job.overall_verdict}, "
                    f"Acceptance rate: {job.acceptance_rate:.1%}.\n"
                    f"Agent interpretation: {job.agent_interpretation or 'N/A'}\n"
                )

        task = f"{job_context}\nUser question: {message}\n\nAnswer concisely using the available data."

        model = OllamaModel(model_id=agent_config.model, url=agent_config.base_url)
        agent = CodeAgent(tools=ALL_TOOLS, model=model, max_steps=5, verbose=False)
        import asyncio
        result = await asyncio.wait_for(asyncio.to_thread(agent.run, task), timeout=60)
        return str(result), []
    except Exception as e:
        return f"I was unable to answer that question right now. Error: {type(e).__name__}", []


async def _run_chat_agent_simple(message: str, conv: Conversation, db) -> str:
    text, _ = await _run_chat_agent(message, conv, db)
    return text
