'use client';

import { useReport } from "@/lib/queries/report-queries";
import { ClassificationBadge } from "@/components/ui/classification-badge";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

interface ReportViewerProps {
  reportId: string;
}

export function ReportViewer({ reportId }: ReportViewerProps) {
  const { data: report, isLoading, error } = useReport(reportId);

  if (isLoading) {
    return <div className="py-8 text-center text-sm text-gray-500">Loading report…</div>;
  }
  if (error || !report) {
    return (
      <div className="py-8 text-center text-sm text-red-600">
        Failed to load report.
      </div>
    );
  }

  const summary = report.content_json?.summary ?? {};
  const segments = report.content_json?.segments ?? [];

  return (
    <div className="space-y-6">
      {/* Stale banner */}
      {report.is_stale && (
        <div className="rounded-md bg-amber-50 border border-amber-200 px-4 py-3 text-sm text-amber-800">
          This report may be outdated due to later segment overrides.
        </div>
      )}

      {/* KPI summary cards */}
      {Object.keys(summary).length > 0 && (
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
          {Object.entries(summary).map(([key, value]) => (
            <div key={key} className="rounded-lg border border-gray-200 bg-white p-3">
              <p className="truncate text-xs capitalize text-gray-500">
                {key.replace(/_/g, " ")}
              </p>
              <p className="mt-1 text-lg font-semibold text-gray-900">
                {typeof value === "number" && value < 2
                  ? `${(value * 100).toFixed(1)}%`
                  : String(value)}
              </p>
            </div>
          ))}
        </div>
      )}

      {/* Segments table */}
      {segments.length > 0 && (
        <div className="overflow-x-auto rounded-lg border border-gray-200">
          <table className="min-w-full divide-y divide-gray-100 text-sm">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-2 text-left text-xs font-medium text-gray-500">#</th>
                <th className="px-4 py-2 text-left text-xs font-medium text-gray-500">AI</th>
                <th className="px-4 py-2 text-left text-xs font-medium text-gray-500">Effective</th>
                <th className="px-4 py-2 text-right text-xs font-medium text-gray-500">Score</th>
                <th className="px-4 py-2 text-right text-xs font-medium text-gray-500">Overrides</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50 bg-white">
              {segments.map((seg) => (
                <tr key={seg.segment_id} className="hover:bg-gray-50">
                  <td className="px-4 py-2 text-gray-700">{seg.segment_number}</td>
                  <td className="px-4 py-2">
                    <ClassificationBadge classification={seg.ai_classification} />
                  </td>
                  <td className="px-4 py-2">
                    <ClassificationBadge
                      classification={seg.effective_classification}
                      effective
                    />
                  </td>
                  <td className="px-4 py-2 text-right text-gray-600">
                    {seg.quality_score !== undefined
                      ? `${(seg.quality_score * 100).toFixed(1)}%`
                      : "—"}
                  </td>
                  <td className="px-4 py-2 text-right text-gray-600">
                    {seg.override_count}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Export buttons */}
      <div className="flex gap-3">
        <a
          href={`${API_URL}/api/reports/${reportId}/export?format=html`}
          target="_blank"
          rel="noopener noreferrer"
          className="rounded-md border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
        >
          Download HTML
        </a>
        <a
          href={`${API_URL}/api/reports/${reportId}/export?format=pdf`}
          target="_blank"
          rel="noopener noreferrer"
          className="rounded-md border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
        >
          Download PDF
        </a>
      </div>
    </div>
  );
}
