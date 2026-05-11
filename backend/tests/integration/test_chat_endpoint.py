"""Integration tests for chat endpoints."""
import uuid

import pytest


@pytest.mark.asyncio
async def test_chat_requires_auth(async_client):
    resp = await async_client.post(
        "/api/chat",
        json={"recording_id": str(uuid.uuid4()), "message": "What is the quality?"},
    )
    assert resp.status_code in (401, 403)


@pytest.mark.asyncio
async def test_chat_missing_recording_id_rejected(async_client):
    resp = await async_client.post("/api/chat", json={"message": "Hello"})
    assert resp.status_code in (401, 422)


@pytest.mark.asyncio
async def test_chat_malformed_recording_id(async_client):
    resp = await async_client.post(
        "/api/chat",
        json={"recording_id": "not-a-uuid", "message": "test"},
    )
    assert resp.status_code in (401, 422)


@pytest.mark.asyncio
async def test_conversations_list_requires_auth(async_client):
    resp = await async_client.get("/api/conversations")
    assert resp.status_code in (401, 403, 404)


@pytest.mark.asyncio
async def test_create_conversation_requires_auth(async_client):
    resp = await async_client.post(
        "/api/conversations",
        json={"recording_id": str(uuid.uuid4()), "title": "Test"},
    )
    assert resp.status_code in (401, 403)
