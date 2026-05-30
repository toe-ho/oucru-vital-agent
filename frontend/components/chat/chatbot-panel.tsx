'use client';

import { useRef, useState } from "react";
import {
  useSendMessage,
  type ChatMessageResponse,
} from "@/lib/queries/chat-queries";

interface Props {
  recordingId: string;
  assessmentJobId?: string;
  reportId?: string;
}

const SUGGESTED_QUESTIONS = [
  "Why was the recording rejected?",
  "What is the overall quality verdict?",
  "Which metric failed most often?",
  "How many segments were accepted?",
];

function MessageBubble({ msg }: { msg: ChatMessageResponse }) {
  const isUser = msg.role === "user";
  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"} mb-3`}>
      <div
        className={`max-w-[80%] rounded-lg px-4 py-2 text-sm leading-relaxed ${
          isUser
            ? "bg-blue-600 text-white"
            : "bg-gray-100 text-gray-800 border border-gray-200"
        }`}
      >
        {msg.content}
      </div>
    </div>
  );
}

export default function ChatbotPanel({ recordingId, assessmentJobId, reportId }: Props) {
  const [inputValue, setInputValue] = useState("");
  const [localMessages, setLocalMessages] = useState<ChatMessageResponse[]>([]);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const { mutate: sendMessage, isPending } = useSendMessage();

  const handleSend = (text: string) => {
    const trimmed = text.trim();
    if (!trimmed || isPending) return;

    const userMsg: ChatMessageResponse = {
      id: crypto.randomUUID(),
      conversation_id: conversationId ?? "",
      role: "user",
      content: trimmed,
      sources: null,
      created_at: new Date().toISOString(),
    };
    setLocalMessages((prev) => [...prev, userMsg]);
    setInputValue("");

    sendMessage(
      {
        recording_id: recordingId,
        message: trimmed,
        conversation_id: conversationId ?? undefined,
        assessment_job_id: assessmentJobId,
        report_id: reportId,
      },
      {
        onSuccess: (response) => {
          setConversationId(response.conversation_id);
          setLocalMessages((prev) => [...prev, response]);
          setTimeout(() => bottomRef.current?.scrollIntoView({ behavior: "smooth" }), 50);
        },
      }
    );
  };

  return (
    <div className="flex h-full flex-col rounded-lg border border-gray-200 bg-white">
      {/* Header */}
      <div className="border-b border-gray-100 px-4 py-3">
        <h2 className="text-sm font-semibold text-gray-800">Quality Assistant</h2>
        <p className="text-xs text-gray-500">Ask questions about this recording</p>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4">
        {localMessages.length === 0 && (
          <div className="space-y-2">
            <p className="text-xs text-gray-500 mb-3">Suggested questions:</p>
            {SUGGESTED_QUESTIONS.map((q) => (
              <button
                key={q}
                onClick={() => handleSend(q)}
                className="block w-full rounded-lg border border-gray-200 bg-gray-50 px-3 py-2 text-left text-xs text-gray-700 hover:bg-blue-50 hover:border-blue-200 transition-colors"
              >
                {q}
              </button>
            ))}
          </div>
        )}
        {localMessages.map((msg) => (
          <MessageBubble key={msg.id} msg={msg} />
        ))}
        {isPending && (
          <div className="flex justify-start mb-3">
            <div className="rounded-lg bg-gray-100 border border-gray-200 px-4 py-2">
              <span className="inline-flex gap-1 text-gray-400 text-sm">
                <span className="animate-bounce">.</span>
                <span className="animate-bounce [animation-delay:0.15s]">.</span>
                <span className="animate-bounce [animation-delay:0.3s]">.</span>
              </span>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="border-t border-gray-100 p-3">
        <div className="flex gap-2">
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSend(inputValue)}
            placeholder="Ask about signal quality…"
            disabled={isPending}
            className="flex-1 rounded-lg border border-gray-200 px-3 py-2 text-sm outline-none focus:border-blue-400 focus:ring-1 focus:ring-blue-100 disabled:opacity-50"
          />
          <button
            onClick={() => handleSend(inputValue)}
            disabled={isPending || !inputValue.trim()}
            className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-40 transition-colors"
          >
            Send
          </button>
        </div>
      </div>
    </div>
  );
}
