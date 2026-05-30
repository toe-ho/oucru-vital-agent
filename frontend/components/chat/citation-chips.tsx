'use client';

import Link from "next/link";
import { FileText, Activity } from "lucide-react";
import { cn } from "@/lib/utils";

interface CitationChipsProps {
  sources: string[];
  className?: string;
}

function classifySource(id: string): { type: "recording" | "job"; href: string; label: string } {
  // Heuristic: job IDs tend to be UUID-like; recording IDs may match other patterns.
  // Both are rendered as chips — segment-level enrichment is a future follow-up.
  const isJobLike = id.includes("job") || id.startsWith("job_");
  return {
    type: isJobLike ? "job" : "recording",
    href: isJobLike ? `#source-${id}` : `/recordings/${id}/monitor`,
    label: id.length > 12 ? `${id.slice(0, 8)}…` : id,
  };
}

export function CitationChips({ sources, className }: CitationChipsProps) {
  if (!sources.length) return null;

  return (
    <div className={cn("flex flex-wrap gap-1 mt-1.5", className)} aria-label="Source citations">
      {sources.map((id) => {
        const { type, href, label } = classifySource(id);
        const Icon = type === "job" ? Activity : FileText;
        return (
          <Link
            key={id}
            href={href}
            className="inline-flex items-center gap-1 rounded-full border border-primary/30 bg-brand-ink px-2 py-0.5 text-[10px] font-medium text-primary hover:bg-brand-tint transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            aria-label={`Source: ${id} (${type})`}
          >
            <Icon className="h-2.5 w-2.5" aria-hidden="true" />
            {label}
          </Link>
        );
      })}
    </div>
  );
}
