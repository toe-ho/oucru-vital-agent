'use client';

import { useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useRecordingReports, useGenerateReport } from "@/lib/queries/report-queries";
import { useRecordingJobs } from "@/lib/queries/assessment-queries";
import { ReportViewer } from "@/components/reports/report-viewer";
import type { ReportSummary } from "@/lib/types";

export default function RecordingReportPage() {
  const params = useParams<{ recordingId: string }>();
  const recordingId = params.recordingId;

  const { data: reports, isLoading, refetch } = useRecordingReports(recordingId);
  const { data: jobs } = useRecordingJobs(recordingId);
  const latestJobId =
    jobs
      ?.filter((j) => j.status === "completed")
      .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())[0]
      ?.job_id;
  const generateReport = useGenerateReport();

  const [selectedReportId, setSelectedReportId] = useState<string | null>(null);

  const reportList: ReportSummary[] = reports ?? [];
  const activeReport =
    selectedReportId ?? reportList[0]?.report_id ?? null;

  const handleGenerate = async () => {
    if (!latestJobId) return;
    const newReport = await generateReport.mutateAsync({
      recording_id: recordingId,
      job_id: latestJobId,
    });
    await refetch();
    setSelectedReportId(newReport.report_id);
  };

  return (
    <main className="min-h-screen bg-gray-50 p-6">
      <div className="mx-auto max-w-5xl space-y-6">
        {/* Header */}
        <div className="flex items-center gap-3">
          <Link
            href={`/recordings/${recordingId}/monitor`}
            className="text-sm text-blue-600 hover:underline"
          >
            ← Monitor
          </Link>
          <h1 className="text-xl font-bold text-gray-900">Reports</h1>
          <button
            onClick={handleGenerate}
            disabled={generateReport.isPending || !latestJobId}
            className="ml-auto rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-700 disabled:opacity-50"
          >
            {generateReport.isPending ? "Generating…" : "Generate Report"}
          </button>
        </div>

        {/* Report selector */}
        {reportList.length > 1 && (
          <div className="flex gap-2 overflow-x-auto">
            {reportList.map((r) => (
              <button
                key={r.report_id}
                type="button"
                onClick={() => setSelectedReportId(r.report_id)}
                className={`shrink-0 rounded-lg border px-3 py-1.5 text-xs font-medium transition-colors ${
                  activeReport === r.report_id
                    ? "border-blue-500 bg-blue-50 text-blue-700"
                    : "border-gray-200 bg-white text-gray-600 hover:bg-gray-50"
                }`}
              >
                {new Date(r.created_at).toLocaleString()}
                {r.is_stale && (
                  <span className="ml-1 text-amber-500" title="Stale">●</span>
                )}
              </button>
            ))}
          </div>
        )}

        {isLoading && (
          <p className="py-10 text-center text-sm text-gray-500">Loading reports…</p>
        )}

        {!isLoading && reportList.length === 0 && (
          <div className="rounded-lg border border-gray-200 bg-white py-12 text-center">
            <p className="text-sm text-gray-500">No reports yet.</p>
            <p className="mt-1 text-xs text-gray-400">
              Generate a report from the button above.
            </p>
          </div>
        )}

        {activeReport && (
          <div className="rounded-xl border border-gray-200 bg-white p-6">
            <ReportViewer reportId={activeReport} />
          </div>
        )}
      </div>
    </main>
  );
}
