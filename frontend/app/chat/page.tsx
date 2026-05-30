'use client';

import { useState } from "react";
import Link from "next/link";
import { useRecordings } from "@/lib/queries/recording-queries";
import ChatbotPanel from "@/components/chat/chatbot-panel";
import type { Recording } from "@/lib/types";

export default function ChatPage() {
  const [selectedId, setSelectedId] = useState<string>("");
  const { data, isLoading } = useRecordings(1);
  const recordings: Recording[] = data?.items ?? [];

  return (
    <main className="min-h-screen bg-gray-50 p-6">
      <div className="mx-auto max-w-4xl space-y-4">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Quality Assistant</h1>
            <p className="text-sm text-gray-500">
              Ask questions about any recording assessment.
            </p>
          </div>
          <Link
            href="/dashboard"
            className="rounded-lg border border-gray-200 bg-white px-4 py-2 text-sm text-gray-600 hover:bg-gray-50"
          >
            ← Dashboard
          </Link>
        </div>

        {/* Recording selector */}
        <div className="rounded-lg border border-gray-200 bg-white p-4">
          <label
            htmlFor="recording-select"
            className="mb-1 block text-xs font-medium text-gray-600"
          >
            Select Recording
          </label>
          {isLoading ? (
            <p className="text-sm text-gray-400">Loading recordings…</p>
          ) : (
            <select
              id="recording-select"
              value={selectedId}
              onChange={(e) => setSelectedId(e.target.value)}
              className="w-full rounded-lg border border-gray-200 px-3 py-2 text-sm outline-none focus:border-blue-400"
            >
              <option value="">— choose a recording —</option>
              {recordings.map((rec) => (
                <option key={rec.id} value={rec.id}>
                  {rec.filename} ({rec.signal_type.toUpperCase()},{" "}
                  {rec.status})
                </option>
              ))}
            </select>
          )}
        </div>

        {/* Chat panel */}
        {selectedId ? (
          <div className="h-[560px]">
            <ChatbotPanel recordingId={selectedId} />
          </div>
        ) : (
          <div className="flex h-48 items-center justify-center rounded-lg border border-dashed border-gray-300 bg-white">
            <p className="text-sm text-gray-400">
              Select a recording above to start chatting.
            </p>
          </div>
        )}
      </div>
    </main>
  );
}
