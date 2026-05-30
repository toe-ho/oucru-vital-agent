import { Skeleton } from "@/components/ui/skeleton";

interface LoadingStateProps {
  rows?: number;
  message?: string;
}

export function LoadingState({ rows = 3, message }: LoadingStateProps) {
  return (
    <div className="space-y-3 p-4" role="status" aria-label={message ?? "Loading…"}>
      {message && (
        <p className="text-sm text-muted-foreground">{message}</p>
      )}
      {Array.from({ length: rows }).map((_, i) => (
        <Skeleton key={i} className="h-8 w-full" />
      ))}
      <span className="sr-only">Loading…</span>
    </div>
  );
}
