'use client';

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { get, post } from "@/lib/api-client";

export interface ChatMessageResponse {
  id: string;
  conversation_id: string;
  role: "user" | "assistant" | "system";
  content: string;
  sources: string[] | null;
  created_at: string;
}

export interface ConversationResponse {
  id: string;
  recording_id: string;
  assessment_job_id: string | null;
  report_id: string | null;
  title: string | null;
  created_at: string;
  messages: ChatMessageResponse[];
}

export interface SendMessagePayload {
  recording_id: string;
  message: string;
  conversation_id?: string;
  assessment_job_id?: string;
  report_id?: string;
}

export function useSendMessage() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: SendMessagePayload) =>
      post<ChatMessageResponse>("/api/chat", payload),
    onSuccess: (data) => {
      queryClient.invalidateQueries({
        queryKey: ["conversation", data.conversation_id],
      });
    },
  });
}

export function useConversation(conversationId: string | null) {
  return useQuery<ConversationResponse>({
    queryKey: ["conversation", conversationId],
    queryFn: () =>
      get<ConversationResponse>(`/api/chat/conversations/${conversationId}`),
    enabled: Boolean(conversationId),
  });
}
