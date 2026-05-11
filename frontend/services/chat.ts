import client from "./api-client";
import type { ChatResponse, ConversationResponse, MessageResponse } from "@/types/api";

export async function createConversation(body: {
  recording_id: string;
  assessment_job_id?: string;
  title?: string;
}): Promise<ConversationResponse> {
  const res = await client.post<ConversationResponse>("/conversations", body);
  return res.data;
}

export async function getMessages(
  conversationId: string
): Promise<{ conversation_id: string; messages: MessageResponse[] }> {
  const res = await client.get(`/conversations/${conversationId}/messages`);
  return res.data;
}

export async function sendMessage(
  conversationId: string,
  message: string
): Promise<ChatResponse> {
  const res = await client.post<ChatResponse>(
    `/conversations/${conversationId}/messages`,
    { message }
  );
  return res.data;
}

export async function sendChat(body: {
  recording_id: string;
  assessment_job_id?: string;
  conversation_id?: string;
  message: string;
}): Promise<ChatResponse> {
  const res = await client.post<ChatResponse>("/chat", body);
  return res.data;
}
