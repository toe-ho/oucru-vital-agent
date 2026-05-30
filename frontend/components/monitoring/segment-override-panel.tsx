'use client';

import { useState } from "react";
import { useCreateOverride } from "@/lib/queries/override-queries";
import { useAuth } from "@/lib/auth-context";
import { ClassificationBadge } from "@/components/ui/classification-badge";

const REASON_CATEGORIES = [
  "artifact",
  "noise",
  "lead_off",
  "motion",
  "clinical_override",
  "other",
] as const;

interface SegmentOverridePanelProps {
  segmentId: string;
  aiClassification: string;
  effectiveClassification: string;
  onOverrideCreated: () => void;
}

export function SegmentOverridePanel({
  segmentId,
  aiClassification,
  effectiveClassification,
  onOverrideCreated,
}: SegmentOverridePanelProps) {
  const { user } = useAuth();
  const canOverride = user?.role === "reviewer" || user?.role === "admin";

  const [label, setLabel] = useState<"accept" | "reject">("accept");
  const [reasonCategory, setReasonCategory] = useState<string>(REASON_CATEGORIES[0]);
  const [note, setNote] = useState("");

  const { mutate, isPending, isSuccess, error, reset } = useCreateOverride();

  if (!canOverride) return null;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (note.length < 10) return;
    mutate(
      { segmentId, label, reason_category: reasonCategory, note },
      {
        onSuccess: () => {
          setNote("");
          onOverrideCreated();
        },
      }
    );
  };

  return (
    <div className="rounded-lg border border-gray-200 bg-white p-4">
      <h3 className="mb-3 text-sm font-semibold text-gray-800">Override Classification</h3>

      <div className="mb-4 flex items-center gap-4 text-xs">
        <div>
          <span className="text-gray-500">AI: </span>
          <ClassificationBadge classification={aiClassification} />
        </div>
        <div>
          <span className="text-gray-500">Effective: </span>
          <ClassificationBadge classification={effectiveClassification} effective />
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-3">
        <div>
          <label className="block text-xs font-medium text-gray-700">New Label</label>
          <select
            value={label}
            onChange={(e) => { reset(); setLabel(e.target.value as "accept" | "reject"); }}
            className="mt-1 block w-full rounded-md border border-gray-300 px-2 py-1.5 text-sm"
          >
            <option value="accept">Accept</option>
            <option value="reject">Reject</option>
          </select>
        </div>

        <div>
          <label className="block text-xs font-medium text-gray-700">Reason</label>
          <select
            value={reasonCategory}
            onChange={(e) => setReasonCategory(e.target.value)}
            className="mt-1 block w-full rounded-md border border-gray-300 px-2 py-1.5 text-sm"
          >
            {REASON_CATEGORIES.map((r) => (
              <option key={r} value={r}>{r.replace(/_/g, " ")}</option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-xs font-medium text-gray-700">
            Note <span className="text-gray-400">(min 10 chars)</span>
          </label>
          <textarea
            value={note}
            onChange={(e) => setNote(e.target.value)}
            rows={3}
            minLength={10}
            required
            placeholder="Describe the reason for this override…"
            className="mt-1 block w-full rounded-md border border-gray-300 px-2 py-1.5 text-sm"
          />
          {note.length > 0 && note.length < 10 && (
            <p className="mt-0.5 text-xs text-red-500">
              {10 - note.length} more character{10 - note.length !== 1 ? "s" : ""} required
            </p>
          )}
        </div>

        {error && (
          <p className="text-xs text-red-600">Error: {(error as Error).message}</p>
        )}
        {isSuccess && (
          <p className="text-xs text-green-600">Override saved successfully.</p>
        )}

        <button
          type="submit"
          disabled={isPending || note.length < 10}
          className="w-full rounded-md bg-indigo-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
        >
          {isPending ? "Saving…" : "Save Override"}
        </button>
      </form>
    </div>
  );
}
