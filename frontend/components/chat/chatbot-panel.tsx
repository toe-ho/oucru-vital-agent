'use client';

import { useRef, useState } from "react";
import { Send } from "lucide-react";
import { useSendMessage, type ChatMessageResponse } from "@/lib/queries/chat-queries";
import { CitationChips } from "./citation-chips";
import { Stat } from "@/components/ui/stat";
import { cn } from "@/lib/utils";

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

// Exact voice/tone templates from branding/03
const REFUSAL_NO_DATA =
  "I don't have data for that recording in this assessment.";
const REFUSAL_SCOPE =
  "That's a clinical judgment outside my scope. I can show the SQI evidence.";
const LLM_FALLBACK =
  "Generated with rule-based classification (assistant unavailable).";

function MessageBubble({ msg }: { msg: ChatMessageResponse }) {
  const isUser = msg.role === "user";
  const isRefusal =
    msg.content === REFUSAL_NO_DATA || msg.content === REFUSAL_SCOPE;
  const isFallback = msg.content.startsWith(LLM_FALLBACK);

  return (
    <div className={cn("flex mb-3", isUser ? "justify-end" : "justify-start")}>
      <div
        className={cn(
          "max-w-[80%] rounded-lg px-4 py-2 text-sm leading-relaxed",
          isUser
            ? "bg-primary text-primary-foreground"
            : "bg-muted text-foreground border border-border"
        )}
      >
        {/* Replace numeric sequences with Stat */}
        <p>{msg.content}</p>

        {/* LLM fallback banner */}
        {isFallback && (
          <p className="mt-1.5 text-[10px] text-muted-foreground border-t border-border/50 pt-1">
            {LLM_FALLBACK}
          </p>
        )}

        {/* Refusal styling */}
        {isRefusal && (
          <p className="mt-1 text-[10px] text-muted-foreground italic">
            Ask about SQI evidence or quality metrics.
          </p>
        )}

        {/* Citation chips */}
        {!isUser && msg.sources && msg.sources.length > 0 && (
          <CitationChips sources={msg.sources} />
        )}
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

  const msgCount = localMessages.length;

  return (
    <div className="flex h-full flex-col rounded-lg border border-border bg-card">
      {/* Header — "Vital Agent" brand name */}
      <div className="border-b border-border px-4 py-3">
        <h2 className="text-sm font-semibold text-foreground">Vital Agent</h2>
        <p className="text-xs text-muted-foreground">Ask questions about this recording</p>
      </div>

      {/* Messages */}
      <div
        className="flex-1 overflow-y-auto p-4"
        aria-live="polite"
        aria-label="Conversation"
        role="log"
      >
        {msgCount === 0 && (
          <div className="space-y-2">
            <p className="text-xs text-muted-foreground mb-3">Suggested questions:</p>
            {SUGGESTED_QUESTIONS.map((q) => (
              <button
                key={q}
                onClick={() => handleSend(q)}
                className="block w-full rounded-lg border border-border bg-muted/50 px-3 py-2 text-left text-xs text-foreground hover:bg-brand-ink hover:border-primary/30 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
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
            <div className="rounded-lg bg-muted border border-border px-4 py-2">
              <span className="inline-flex gap-1 text-muted-foreground text-sm" aria-label="Thinking…">
                <span className="animate-bounce">.</span>
                <span className="animate-bounce [animation-delay:0.15s]">.</span>
                <span className="animate-bounce [animation-delay:0.3s]">.</span>
              </span>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Message count for screen readers */}
      <span className="sr-only" aria-live="polite">
        {msgCount > 0 ? `${msgCount} messages in conversation` : ""}
      </span>

      {/* Input composer */}
      <div className="border-t border-border p-3">
        <div className="flex gap-2">
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSend(inputValue)}
            placeholder="Ask about signal quality…"
            disabled={isPending}
            aria-label="Message input"
            className="flex-1 rounded-lg border border-input bg-background px-3 py-2 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:opacity-50"
          />
          <button
            onClick={() => handleSend(inputValue)}
            disabled={isPending || !inputValue.trim()}
            aria-label="Send message"
            className="rounded-lg bg-primary px-3 py-2 text-primary-foreground hover:bg-brand-hover disabled:opacity-40 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          >
            <Send className="h-4 w-4" aria-hidden="true" />
          </button>
        </div>
      </div>
    </div>
  );
}
