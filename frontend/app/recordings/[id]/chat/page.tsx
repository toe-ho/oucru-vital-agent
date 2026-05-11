"use client";

import { useState, useRef, useEffect } from "react";
import { useParams } from "next/navigation";
import { sendChat } from "@/services/chat";
import type { MessageResponse } from "@/types/api";

const SUGGESTED_QUESTIONS = [
  "What was the overall quality verdict?",
  "Which segments were rejected?",
  "Why was the signal quality poor?",
  "What are the recommendations?",
];

export default function ChatPage() {
  const { id } = useParams<{ id: string }>();
  const [messages, setMessages] = useState<MessageResponse[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [conversationId, setConversationId] = useState<string | undefined>();
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function send(text: string) {
    if (!text.trim()) return;
    const userMsg: MessageResponse = {
      message_id: `user-${Date.now()}`,
      role: "user",
      content: text,
      sources: [],
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);
    try {
      const resp = await sendChat({ recording_id: id, conversation_id: conversationId, message: text });
      if (!conversationId) setConversationId(resp.conversation_id);
      setMessages((prev) => [
        ...prev,
        {
          message_id: resp.assistant_message_id,
          role: "assistant",
          content: resp.response,
          sources: resp.sources,
          created_at: new Date().toISOString(),
        },
      ]);
    } catch (e: unknown) {
      setMessages((prev) => [
        ...prev,
        {
          message_id: `err-${Date.now()}`,
          role: "assistant",
          content: "Sorry, I could not answer that right now.",
          sources: [],
          created_at: new Date().toISOString(),
        },
      ]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="max-w-2xl mx-auto flex flex-col h-[80vh]">
      <h1 className="text-xl font-bold text-brand-900 mb-4">Chat about this recording</h1>

      <div className="flex-1 overflow-y-auto space-y-3 bg-white border rounded-lg p-4 shadow-sm mb-3">
        {messages.length === 0 && (
          <p className="text-gray-400 text-sm">Ask a question about the recording&apos;s quality assessment.</p>
        )}
        {messages.map((m) => (
          <div
            key={m.message_id}
            className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}
          >
            <div
              className={`max-w-[80%] px-4 py-2.5 rounded-2xl text-sm ${
                m.role === "user"
                  ? "bg-brand-900 text-white rounded-br-sm"
                  : "bg-gray-100 text-gray-800 rounded-bl-sm"
              }`}
            >
              {m.content}
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex justify-start">
            <div className="bg-gray-100 text-gray-500 px-4 py-2.5 rounded-2xl rounded-bl-sm text-sm animate-pulse">
              Thinking…
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      <div className="flex flex-wrap gap-2 mb-3">
        {SUGGESTED_QUESTIONS.map((q) => (
          <button
            key={q}
            onClick={() => send(q)}
            className="px-3 py-1.5 bg-brand-100 text-brand-900 rounded-full text-xs font-medium hover:bg-brand-700 hover:text-white transition-colors"
          >
            {q}
          </button>
        ))}
      </div>

      <form
        onSubmit={(e) => { e.preventDefault(); send(input); }}
        className="flex gap-2"
      >
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask about the quality assessment…"
          className="flex-1 border border-gray-300 rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-brand-700"
        />
        <button
          type="submit"
          disabled={!input.trim() || loading}
          className="px-5 py-2.5 bg-brand-900 text-white rounded-lg text-sm font-medium disabled:opacity-40"
        >
          Send
        </button>
      </form>
    </div>
  );
}
