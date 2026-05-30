'use client';

interface ClassificationBadgeProps {
  classification: string;
  effective?: boolean;
}

const COLOR_MAP: Record<string, string> = {
  accept: "bg-green-100 text-green-800 border-green-300",
  reject: "bg-red-100 text-red-800 border-red-300",
  uncomputable: "bg-amber-100 text-amber-800 border-amber-300",
  pending: "bg-gray-100 text-gray-600 border-gray-300",
};

const LABEL_MAP: Record<string, string> = {
  accept: "Accept",
  reject: "Reject",
  uncomputable: "Uncomputable",
  pending: "Pending",
};

export function ClassificationBadge({ classification, effective }: ClassificationBadgeProps) {
  const colorClass = COLOR_MAP[classification] ?? "bg-gray-100 text-gray-600 border-gray-300";
  const label = LABEL_MAP[classification] ?? classification;

  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full border px-2.5 py-0.5 text-xs font-medium ${colorClass}`}
    >
      {effective && (
        <span className="h-1.5 w-1.5 rounded-full bg-current opacity-70" aria-hidden="true" />
      )}
      {label}
    </span>
  );
}
