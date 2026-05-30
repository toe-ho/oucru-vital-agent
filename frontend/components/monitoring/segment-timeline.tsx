'use client';

import { useState } from "react";
import type { SegmentResult } from "@/lib/types";

const BLOCK_COLOR: Record<string, string> = {
  accept: "bg-green-500",
  reject: "bg-red-500",
  uncomputable: "bg-amber-400",
  pending: "bg-gray-400",
};

const BORDER_COLOR: Record<string, string> = {
  accept: "border-green-700",
  reject: "border-red-700",
  uncomputable: "border-amber-600",
  pending: "border-gray-600",
};

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
    return <p className="text-sm text-gray-500">No segments available.</p>;
  }

  return (
    <div className="relative">
      <div className="flex h-8 w-full overflow-x-auto rounded-md border border-gray-200">
        {segments.map((seg) => {
          const classification = seg.ai_classification;
          const isSelected = seg.segment_id === selectedSegmentId;
          const blockColor = BLOCK_COLOR[classification] ?? "bg-gray-300";
          const borderColor = BORDER_COLOR[classification] ?? "border-gray-500";

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
              className={`h-full transition-opacity hover:opacity-80 ${blockColor} ${
                isSelected ? `border-2 ${borderColor}` : "border-0"
              }`}
              aria-label={`Segment ${seg.segment_number}: ${classification}`}
            />
          );
        })}
      </div>

      {/* Tooltip */}
      {tooltip && (() => {
        const seg = segments.find((s) => s.segment_id === tooltip.segmentId);
        if (!seg) return null;
        return (
          <div
            className="pointer-events-none absolute z-10 rounded-md bg-gray-900 px-2 py-1 text-xs text-white shadow-lg"
            style={{ left: tooltip.x, top: tooltip.y + 36 }}
          >
            <div>Segment #{seg.segment_number}</div>
            <div className="capitalize">{seg.ai_classification}</div>
            {seg.quality_score !== undefined && (
              <div>Score: {(seg.quality_score * 100).toFixed(1)}%</div>
            )}
          </div>
        );
      })()}

      {/* Segment number labels for selected */}
      <div className="mt-1 flex text-xs text-gray-400 overflow-x-auto">
        {segments.map((seg) => (
          <span
            key={seg.segment_id}
            style={{ flex: `0 0 ${100 / segments.length}%` }}
            className="truncate text-center"
          >
            {seg.segment_number}
          </span>
        ))}
      </div>
    </div>
  );
}
