'use client';

import { useState } from "react";
import { cn } from "@/lib/utils";
import type { SegmentResult } from "@/lib/types";

// Use token class names — no raw status hex
const BLOCK_COLOR: Record<string, string> = {
  accept: "bg-accept",
  reject: "bg-reject",
  uncomputable: "bg-uncomputable",
  pending: "bg-muted-foreground/40",
};

// Indigo for selection/hover — never a verdict color (branding rule)
const SELECTED_RING = "ring-2 ring-primary ring-offset-1";

interface SegmentTimelineProps {
  segments: SegmentResult[];
  selectedSegmentId?: string;
  onSelect: (id: string) => void;
}

interface TooltipState {
  segmentId: string;
  x: number;
  y: number;
}

export function SegmentTimeline({ segments, selectedSegmentId, onSelect }: SegmentTimelineProps) {
  const [tooltip, setTooltip] = useState<TooltipState | null>(null);

  if (!segments.length) {
    return <p className="text-sm text-muted-foreground">No segments available.</p>;
  }

  return (
    <div className="relative">
      <div
        className="flex h-8 w-full overflow-x-auto rounded-md border border-border"
        aria-label="Segment timeline"
      >
        {segments.map((seg) => {
          const classification = seg.ai_classification;
          const isSelected = seg.segment_id === selectedSegmentId;
          const blockColor = BLOCK_COLOR[classification] ?? "bg-muted";

          return (
            <button
              key={seg.segment_id}
              type="button"
              onClick={() => onSelect(seg.segment_id)}
              onMouseEnter={(e) =>
                setTooltip({
                  segmentId: seg.segment_id,
                  x: e.currentTarget.offsetLeft,
                  y: e.currentTarget.offsetTop,
                })
              }
              onMouseLeave={() => setTooltip(null)}
              style={{ flex: `0 0 ${100 / segments.length}%` }}
              className={cn(
                "h-full transition-opacity hover:opacity-75 focus-visible:outline-none",
                blockColor,
                isSelected && SELECTED_RING
              )}
              aria-label={`Segment ${seg.segment_number}: ${classification}${seg.quality_score !== undefined ? ` — score ${(seg.quality_score * 100).toFixed(1)}%` : ""}`}
              aria-current={isSelected ? "true" : undefined}
            />
          );
        })}
      </div>

      {/* Verdict-first mono tooltip */}
      {tooltip && (() => {
        const seg = segments.find((s) => s.segment_id === tooltip.segmentId);
        if (!seg) return null;
        const scoreLabel = seg.quality_score !== undefined
          ? ` — ${(seg.quality_score * 100).toFixed(1)}%`
          : "";
        return (
          <div
            className="pointer-events-none absolute z-10 rounded-md bg-popover border border-border px-2 py-1 text-xs text-popover-foreground shadow-lg"
            style={{ left: tooltip.x, top: tooltip.y + 36 }}
            aria-hidden="true"
          >
            <div className="capitalize font-medium">
              {seg.ai_classification}{scoreLabel}
            </div>
            <div className="num text-muted-foreground">#{seg.segment_number}</div>
          </div>
        );
      })()}

      {/* Segment number labels */}
      <div className="mt-1 flex text-xs text-muted-foreground overflow-x-auto" aria-hidden="true">
        {segments.map((seg) => (
          <span
            key={seg.segment_id}
            style={{ flex: `0 0 ${100 / segments.length}%` }}
            className="truncate text-center num"
          >
            {seg.segment_number}
          </span>
        ))}
      </div>
    </div>
  );
}
