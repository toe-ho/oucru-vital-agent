'use client';

import { useState } from "react";
import Link from "next/link";
import { useRecordings } from "@/lib/queries/recording-queries";
import type { Recording } from "@/lib/types";

const STATUS_BADGE: Record<string, string> = {
  pending: "bg-gray-100 text-gray-600",
  processing: "bg-blue-100 text-blue-700",
  completed: "bg-green-100 text-green-700",
  failed: "bg-red-100 text-red-700",
};

function KpiCard({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="rounded-lg border border-gray-200 bg-white p-4">
      <p className="text-xs text-gray-500">{label}</p>
      <p className="mt-1 text-2xl font-bold text-gray-900">{value}</p>
    </div>
  );
}

function acceptanceRate(recordings: Recording[]): string {
  const completed = recordings.filter((r) => r.status === "completed");
  if (!completed.length) return "—";
  // approximation: ratio of completed to total
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
    <main className="min-h-screen bg-gray-50 p-6">
      <div className="mx-auto max-w-6xl space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold text-gray-900">Quality Dashboard</h1>
          <div className="flex gap-2">
            <Link
              href="/chat"
              className="rounded-lg border border-gray-200 bg-white px-4 py-2 text-sm font-semibold text-gray-700 hover:bg-gray-50"
            >
              Chat
            </Link>
            <Link
              href="/upload"
              className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-700"
            >
              + Upload New
            </Link>
          </div>
        </div>

        {/* KPI cards */}
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-3">
          <KpiCard label="Total Recordings" value={total} />
          <KpiCard label="Today's Uploads" value={todayCount(recordings)} />
          <KpiCard label="Avg Acceptance Rate" value={acceptanceRate(recordings)} />
        </div>

        {/* Recent recordings table */}
        <div className="overflow-hidden rounded-lg border border-gray-200 bg-white">
          <div className="px-4 py-3 border-b border-gray-100">
            <h2 className="text-sm font-semibold text-gray-800">Recent Recordings</h2>
          </div>

          {isLoading && (
            <p className="py-10 text-center text-sm text-gray-500">Loading…</p>
          )}
          {error && (
            <p className="py-10 text-center text-sm text-red-600">Failed to load recordings.</p>
          )}
          {!isLoading && !error && recordings.length === 0 && (
            <p className="py-10 text-center text-sm text-gray-500">No recordings yet.</p>
          )}

          {recordings.length > 0 && (
            <table className="min-w-full divide-y divide-gray-100 text-sm">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500">File</th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500">Type</th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500">Subject</th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500">Status</th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500">Created</th>
                  <th className="px-4 py-2 text-right text-xs font-medium text-gray-500">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {recordings.map((rec) => (
                  <tr key={rec.id} className="hover:bg-gray-50">
                    <td className="px-4 py-2 font-mono text-xs text-gray-700 truncate max-w-[160px]">
                      {rec.filename}
                    </td>
                    <td className="px-4 py-2 uppercase text-gray-600">{rec.signal_type}</td>
                    <td className="px-4 py-2 text-gray-600">{rec.subject_id ?? "—"}</td>
                    <td className="px-4 py-2">
                      <span
                        className={`inline-block rounded-full px-2 py-0.5 text-xs font-medium ${
                          STATUS_BADGE[rec.status] ?? "bg-gray-100 text-gray-600"
                        }`}
                      >
                        {rec.status}
                      </span>
                    </td>
                    <td className="px-4 py-2 text-gray-500">
                      {new Date(rec.created_at).toLocaleDateString()}
                    </td>
                    <td className="px-4 py-2 text-right">
                      <Link
                        href={`/recordings/${rec.id}/monitor`}
                        className="text-blue-600 hover:underline text-xs"
                      >
                        View
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-end gap-2 border-t border-gray-100 px-4 py-3">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
                className="rounded px-2 py-1 text-xs text-gray-600 hover:bg-gray-100 disabled:opacity-40"
              >
                Prev
              </button>
              <span className="text-xs text-gray-500">{page} / {totalPages}</span>
              <button
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                disabled={page === totalPages}
                className="rounded px-2 py-1 text-xs text-gray-600 hover:bg-gray-100 disabled:opacity-40"
              >
                Next
              </button>
            </div>
          )}
        </div>
      </div>
    </main>
  );
}
