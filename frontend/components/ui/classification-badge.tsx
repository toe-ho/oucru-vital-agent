'use client';

import { CheckCircle, XCircle, HelpCircle, Clock } from "lucide-react";
import { cn } from "@/lib/utils";

type Verdict = "accept" | "reject" | "uncomputable" | "pending";

const VERDICT_CONFIG: Record<Verdict, {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  classes: string;
  ariaLabel: string;
}> = {
  accept: {
    icon: CheckCircle,
    label: "Accept",
    classes: "border-accept/30 bg-accept/10 text-accept",
    ariaLabel: "Verdict: Accept",
  },
  reject: {
    icon: XCircle,
    label: "Reject",
    classes: "border-reject/30 bg-reject/10 text-reject",
    ariaLabel: "Verdict: Reject",
  },
  uncomputable: {
    icon: HelpCircle,
    label: "Uncomputable",
    classes: "border-uncomputable/30 bg-uncomputable/10 text-uncomputable",
    ariaLabel: "Verdict: Uncomputable",
  },
  pending: {
    icon: Clock,
    label: "Pending",
    classes: "border-border bg-muted text-muted-foreground",
    ariaLabel: "Verdict: Pending",
  },
};

interface ClassificationBadgeProps {
  classification: string;
  effective?: boolean;
  showScore?: number;
  className?: string;
}

export function ClassificationBadge({
  classification,
  effective,
  showScore,
  className,
}: ClassificationBadgeProps) {
  const config = VERDICT_CONFIG[classification as Verdict] ?? VERDICT_CONFIG.pending;
  const { icon: Icon, label, classes, ariaLabel } = config;

  const fullAriaLabel = showScore !== undefined
    ? `${ariaLabel} — score ${(showScore * 100).toFixed(1)}%`
    : ariaLabel;

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full border px-2.5 py-0.5 text-xs font-medium",
        classes,
        className
      )}
      aria-label={fullAriaLabel}
      role="status"
    >
      <Icon className="h-3 w-3 shrink-0" aria-hidden="true" />
      {label}
      {effective && <span className="sr-only">(effective)</span>}
      {showScore !== undefined && (
        <span className="num ml-1 opacity-80">{(showScore * 100).toFixed(0)}%</span>
      )}
    </span>
  );
}
