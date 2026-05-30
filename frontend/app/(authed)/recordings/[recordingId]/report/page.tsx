'use client';

import { useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useRecordingReports, useGenerateReport } from "@/lib/queries/report-queries";
import { useRecordingJobs } from "@/lib/queries/assessment-queries";
import { ReportViewer } from "@/components/reports/report-viewer";
import { Button } from "@/components/ui/button";
import { LoadingState } from "@/components/feedback/loading-state";
import { EmptyState } from "@/components/feedback/empty-state";
import { Stat } from "@/components/ui/stat";
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
  const activeReport = selectedReportId ?? reportList[0]?.report_id ?? null;

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
    <div className="mx-auto max-w-5xl space-y-6">
      <div className="flex items-center gap-3">
        <Link href={`/recordings/${recordingId}/monitor`} className="text-sm text-primary hover:underline">
          ← Monitor
        </Link>
        <h1 className="text-xl font-bold text-foreground">Reports</h1>
        <Button
          className="ml-auto"
          onClick={handleGenerate}
          disabled={generateReport.isPending || !latestJobId}
        >
          {generateReport.isPending ? "Generating…" : "Generate Report"}
        </Button>
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
                  ? "border-primary bg-brand-ink text-primary"
                  : "border-border bg-card text-muted-foreground hover:bg-muted"
              }`}
            >
              <Stat>{new Date(r.created_at).toLocaleString()}</Stat>
              {r.is_stale && (
                <span className="ml-1 text-stale" title="Stale">●</span>
              )}
            </button>
          ))}
        </div>
      )}

      {isLoading && <LoadingState rows={4} message="Loading reports…" />}

      {!isLoading && reportList.length === 0 && (
        <EmptyState
          title="No reports yet."
          description="Generate a report from the button above."
        />
      )}

      {activeReport && (
        <div className="rounded-xl border border-border bg-card p-6">
          <ReportViewer reportId={activeReport} />
        </div>
      )}
    </div>
  );
}
