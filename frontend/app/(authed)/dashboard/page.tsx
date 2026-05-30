'use client';

import { useState } from "react";
import Link from "next/link";
import { useRecordings } from "@/lib/queries/recording-queries";
import { EmptyState } from "@/components/feedback/empty-state";
import { LoadingState } from "@/components/feedback/loading-state";
import { Stat } from "@/components/ui/stat";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import type { Recording } from "@/lib/types";

const STATUS_BADGE: Record<string, string> = {
  pending: "bg-muted text-muted-foreground",
  processing: "bg-brand-ink text-primary",
  completed: "bg-accept/10 text-accept",
  failed: "bg-reject/10 text-reject",
};

function KpiCard({ label, value }: { label: string; value: string | number }) {
  return (
    <Card>
      <CardContent className="pt-4">
        <p className="text-xs text-muted-foreground">{label}</p>
        <p className="mt-1 text-2xl font-bold text-foreground">
          <Stat>{value}</Stat>
        </p>
      </CardContent>
    </Card>
  );
}

function acceptanceRate(recordings: Recording[]): string {
  const completed = recordings.filter((r) => r.status === "completed");
  if (!completed.length) return "—";
  return `${Math.round((completed.length / recordings.length) * 100)}%`;
}

function todayCount(recordings: Recording[]): number {
  const today = new Date().toISOString().slice(0, 10);
  return recordings.filter((r) => r.created_at.startsWith(today)).length;
}

export default function DashboardPage() {
  const [page, setPage] = useState(1);
  const { data, isLoading, error } = useRecordings(page);

  const recordings = data?.items ?? [];
  const total = data?.total ?? 0;
  const pageSize = data?.page_size ?? 20;
  const totalPages = Math.ceil(total / pageSize);

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-foreground">Quality Dashboard</h1>
        <Button asChild>
          <Link href="/upload">+ Upload New</Link>
        </Button>
      </div>

      {/* KPI cards */}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-3">
        <KpiCard label="Total Recordings" value={total} />
        <KpiCard label="Today's Uploads" value={todayCount(recordings)} />
        <KpiCard label="Avg Acceptance Rate" value={acceptanceRate(recordings)} />
      </div>

      {/* Recordings table */}
      <div className="overflow-hidden rounded-lg border border-border bg-card">
        <div className="px-4 py-3 border-b border-border">
          <h2 className="text-sm font-semibold text-foreground">Recent Recordings</h2>
        </div>

        {isLoading && <LoadingState message="Loading recordings…" />}
        {error && (
          <p className="py-10 text-center text-sm text-reject">Failed to load recordings.</p>
        )}
        {!isLoading && !error && recordings.length === 0 && (
          <EmptyState
            description="No recordings yet. Upload a CSV or Parquet file to begin."
            actionLabel="Upload your first recording"
            actionHref="/upload"
          />
        )}

        {recordings.length > 0 && (
          <table className="min-w-full divide-y divide-border text-sm">
            <thead className="bg-muted/30">
              <tr>
                <th className="px-4 py-2 text-left text-xs font-medium text-muted-foreground">File</th>
                <th className="px-4 py-2 text-left text-xs font-medium text-muted-foreground">Type</th>
                <th className="px-4 py-2 text-left text-xs font-medium text-muted-foreground">Subject</th>
                <th className="px-4 py-2 text-left text-xs font-medium text-muted-foreground">Status</th>
                <th className="px-4 py-2 text-left text-xs font-medium text-muted-foreground">Created</th>
                <th className="px-4 py-2 text-right text-xs font-medium text-muted-foreground">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {recordings.map((rec) => (
                <tr key={rec.id} className="hover:bg-muted/30 transition-colors">
                  <td className="px-4 py-2 font-mono text-xs text-foreground truncate max-w-[160px]">
                    {rec.filename}
                  </td>
                  <td className="px-4 py-2 uppercase text-muted-foreground text-xs">{rec.signal_type}</td>
                  <td className="px-4 py-2 text-muted-foreground text-sm">{rec.subject_id ?? "—"}</td>
                  <td className="px-4 py-2">
                    <span className={`inline-block rounded-full px-2 py-0.5 text-xs font-medium ${STATUS_BADGE[rec.status] ?? "bg-muted text-muted-foreground"}`}>
                      {rec.status}
                    </span>
                  </td>
                  <td className="px-4 py-2 text-muted-foreground text-sm">
                    {new Date(rec.created_at).toLocaleDateString()}
                  </td>
                  <td className="px-4 py-2 text-right">
                    <Link href={`/recordings/${rec.id}/monitor`} className="text-primary hover:underline text-xs font-medium">
                      View
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}

        {totalPages > 1 && (
          <div className="flex items-center justify-end gap-2 border-t border-border px-4 py-3">
            <button onClick={() => setPage((p) => Math.max(1, p - 1))} disabled={page === 1} className="rounded px-2 py-1 text-xs text-muted-foreground hover:bg-muted disabled:opacity-40">Prev</button>
            <span className="text-xs text-muted-foreground"><Stat>{page}</Stat> / <Stat>{totalPages}</Stat></span>
            <button onClick={() => setPage((p) => Math.min(totalPages, p + 1))} disabled={page === totalPages} className="rounded px-2 py-1 text-xs text-muted-foreground hover:bg-muted disabled:opacity-40">Next</button>
          </div>
        )}
      </div>
    </div>
  );
}
