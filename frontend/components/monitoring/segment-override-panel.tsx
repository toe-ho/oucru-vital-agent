'use client';

import { useState } from "react";
import { useCreateOverride } from "@/lib/queries/override-queries";
import { useAuth } from "@/lib/auth-context";
import { ClassificationBadge } from "@/components/ui/classification-badge";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

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
  // Preserve existing RBAC role-gating exactly — only reviewer/admin can override
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
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm">Override Classification</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="mb-4 flex items-center gap-4 text-xs">
          <div className="flex items-center gap-1.5">
            <span className="text-muted-foreground">AI:</span>
            <ClassificationBadge classification={aiClassification} />
          </div>
          <div className="flex items-center gap-1.5">
            <span className="text-muted-foreground">Effective:</span>
            <ClassificationBadge classification={effectiveClassification} effective />
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-3">
          <div>
            <label htmlFor="override-label" className="block text-xs font-medium text-foreground mb-1">New Label</label>
            <select
              id="override-label"
              value={label}
              onChange={(e) => { reset(); setLabel(e.target.value as "accept" | "reject"); }}
              className="w-full rounded-md border border-input bg-background px-2 py-1.5 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            >
              <option value="accept">Accept</option>
              <option value="reject">Reject</option>
            </select>
          </div>

          <div>
            <label htmlFor="override-reason" className="block text-xs font-medium text-foreground mb-1">Reason</label>
            <select
              id="override-reason"
              value={reasonCategory}
              onChange={(e) => setReasonCategory(e.target.value)}
              className="w-full rounded-md border border-input bg-background px-2 py-1.5 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            >
              {REASON_CATEGORIES.map((r) => (
                <option key={r} value={r}>{r.replace(/_/g, " ")}</option>
              ))}
            </select>
          </div>

          <div>
            <label htmlFor="override-note" className="block text-xs font-medium text-foreground mb-1">
              Note <span className="text-muted-foreground">(min 10 chars)</span>
            </label>
            <Textarea
              id="override-note"
              value={note}
              onChange={(e) => setNote(e.target.value)}
              rows={3}
              minLength={10}
              required
              placeholder="Describe the reason for this override…"
            />
            {note.length > 0 && note.length < 10 && (
              <p className="mt-0.5 text-xs text-reject">
                {10 - note.length} more character{10 - note.length !== 1 ? "s" : ""} required
              </p>
            )}
          </div>

          {error && <p className="text-xs text-reject">Error: {(error as Error).message}</p>}
          {isSuccess && <p className="text-xs text-accept">Override saved successfully.</p>}

          <Button type="submit" className="w-full" disabled={isPending || note.length < 10}>
            {isPending ? "Saving…" : "Save Override"}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
