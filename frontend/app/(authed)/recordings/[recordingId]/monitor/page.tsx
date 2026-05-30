'use client';

import { useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useRecording } from "@/lib/queries/recording-queries";
import { useJobResults, useJobLogs, useRecordingJobs } from "@/lib/queries/assessment-queries";
import { WaveformViewer } from "@/components/monitoring/waveform-viewer";
import { SegmentTimeline } from "@/components/monitoring/segment-timeline";
import { SqiScoresPanel } from "@/components/monitoring/sqi-scores-panel";
import { SegmentOverridePanel } from "@/components/monitoring/segment-override-panel";
import { ClassificationBadge } from "@/components/ui/classification-badge";
import { useEffectiveClassification } from "@/lib/queries/override-queries";
import { LoadingState } from "@/components/feedback/loading-state";
import { ErrorState } from "@/components/feedback/error-state";
import { Stat } from "@/components/ui/stat";
import type { EffectiveSegmentResult } from "@/lib/types";

function AgentLogSection({ jobId }: { jobId: string }) {
  const [open, setOpen] = useState(false);
  const { data: logs } = useJobLogs(jobId);

  return (
    <div className="rounded-lg border border-border bg-card">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="flex w-full items-center justify-between px-4 py-3 text-sm font-semibold text-foreground"
        aria-expanded={open}
      >
        <span>Agent Logs</span>
        <span className="text-muted-foreground text-xs">{open ? "▲" : "▼"}</span>
      </button>
      {open && (
        <div className="border-t border-border px-4 py-3" aria-live="polite">
          {!logs?.length ? (
            <p className="text-xs text-muted-foreground">No log entries.</p>
          ) : (
            <ul className="space-y-1 max-h-48 overflow-y-auto font-mono text-xs">
              {logs.map((entry) => (
                <li
                  key={entry.log_id}
                  className={
                    entry.level === "error"
                      ? "text-reject"
                      : entry.level === "warning"
                      ? "text-uncomputable"
                      : "text-foreground"
                  }
                >
                  <Stat className="text-muted-foreground mr-2">
                    {new Date(entry.timestamp).toLocaleTimeString()}
                  </Stat>
                  [{entry.level.toUpperCase()}] {entry.message}
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}

function SelectedSegmentPanel({
  segment,
  onOverrideCreated,
}: {
  segment: EffectiveSegmentResult;
  onOverrideCreated: () => void;
}) {
  const { data: effectiveData } = useEffectiveClassification(segment.segment_id);
  const effectiveClass =
    effectiveData?.effective_classification ?? segment.effective_classification;

  return (
    <div className="grid gap-4 lg:grid-cols-2">
      <SqiScoresPanel segment={segment} />
      <SegmentOverridePanel
        segmentId={segment.segment_id}
        aiClassification={segment.ai_classification}
        effectiveClassification={effectiveClass}
        onOverrideCreated={onOverrideCreated}
      />
    </div>
  );
}

export default function MonitorPage() {
  const params = useParams<{ recordingId: string }>();
  const recordingId = params.recordingId;

  const { data: recording, isLoading: recLoading } = useRecording(recordingId);
  const { data: jobs, isLoading: jobsLoading } = useRecordingJobs(recordingId);
  const latestJobId =
    jobs
      ?.filter((j) => j.status === "completed")
      .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())[0]
      ?.job_id ?? "";
  const { data: results, isLoading: resultsLoading, isError, refetch } = useJobResults(latestJobId);

  const [selectedSegmentId, setSelectedSegmentId] = useState<string | null>(null);
  const segments = results?.segments ?? [];
  const selectedSegment =
    segments.find((s) => s.segment_id === selectedSegmentId) ?? segments[0] ?? null;
  const jobId = results?.job_id ?? "";

  if (recLoading || jobsLoading || resultsLoading) {
    return <LoadingState rows={5} message="Loading assessment data…" />;
  }

  if (isError) {
    return <ErrorState title="Failed to load assessment." onRetry={() => refetch()} />;
  }

  // Verdict summary for the recording overall
  const summary = results?.summary;

  return (
    <div className="mx-auto max-w-6xl space-y-4">
      {/* Navigation breadcrumb override */}
      <div className="flex items-center gap-3">
        <Link href="/recordings" className="text-sm text-primary hover:underline">
          ← Recordings
        </Link>
        <h1 className="text-xl font-bold text-foreground truncate">
          {recording?.filename ?? recordingId}
        </h1>
        <Link
          href={`/recordings/${recordingId}/report`}
          className="ml-auto text-sm text-primary hover:underline font-medium"
        >
          View Report →
        </Link>
      </div>

      {/* 1. Verdict summary */}
      {summary && (
        <div className="rounded-lg border border-border bg-card p-4">
          <h2 className="mb-3 text-sm font-semibold text-foreground">Verdict Summary</h2>
          <div className="flex flex-wrap gap-4 text-xs text-muted-foreground">
            <span>Total: <Stat className="font-semibold text-foreground">{summary.total_segments}</Stat></span>
            <span className="text-accept">Accepted: <Stat className="font-semibold">{summary.accepted}</Stat></span>
            <span className="text-reject">Rejected: <Stat className="font-semibold">{summary.rejected}</Stat></span>
            <span className="text-uncomputable">Uncomputable: <Stat className="font-semibold">{summary.uncomputable}</Stat></span>
            <span>Acceptance Rate: <Stat className="font-semibold text-foreground">{(summary.acceptance_rate * 100).toFixed(1)}%</Stat></span>
          </div>
        </div>
      )}

      {/* 2. Waveform */}
      <div className="rounded-lg border border-border bg-card p-4">
        <h2 className="mb-2 text-sm font-semibold text-foreground">Waveform</h2>
        <WaveformViewer
          data={[]}
          segmentBoundaries={segments.map((s) => ({
            start: s.start_sample,
            end: s.end_sample,
            classification: s.effective_classification,
          }))}
        />
        <p className="mt-1 text-xs text-muted-foreground">
          Segment boundaries shown — waveform data not streamed.
        </p>
      </div>

      {/* 3. Segment timeline */}
      <div className="rounded-lg border border-border bg-card p-4">
        <h2 className="mb-2 text-sm font-semibold text-foreground">
          Segments (<Stat>{segments.length}</Stat>)
        </h2>
        {segments.length > 0 ? (
          <SegmentTimeline
            segments={segments}
            selectedSegmentId={selectedSegmentId ?? undefined}
            onSelect={setSelectedSegmentId}
          />
        ) : (
          <p className="text-sm text-muted-foreground">No segments available.</p>
        )}
      </div>

      {/* 4. Selected segment evidence */}
      {selectedSegment && (
        <div>
          <h2 className="mb-2 text-sm font-semibold text-foreground flex items-center gap-2">
            Segment <Stat>#{selectedSegment.segment_number}</Stat>
            <ClassificationBadge classification={selectedSegment.effective_classification} effective />
          </h2>
          <SelectedSegmentPanel segment={selectedSegment} onOverrideCreated={() => refetch()} />
        </div>
      )}

      {/* 5. Agent logs (collapsible) */}
      {jobId && <AgentLogSection jobId={jobId} />}
    </div>
  );
}
