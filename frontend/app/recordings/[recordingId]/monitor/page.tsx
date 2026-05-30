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
import { useEffectiveClassification } from "@/lib/queries/override-queries";
import type { EffectiveSegmentResult } from "@/lib/types";

function AgentLogSection({ jobId }: { jobId: string }) {
  const [open, setOpen] = useState(false);
  const { data: logs } = useJobLogs(jobId);

  return (
    <div className="rounded-lg border border-gray-200 bg-white">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="flex w-full items-center justify-between px-4 py-3 text-sm font-semibold text-gray-800"
      >
        <span>Agent Logs</span>
        <span className="text-gray-400">{open ? "▲" : "▼"}</span>
      </button>
      {open && (
        <div className="border-t border-gray-100 px-4 py-3">
          {!logs?.length ? (
            <p className="text-xs text-gray-500">No log entries.</p>
          ) : (
            <ul className="space-y-1 max-h-48 overflow-y-auto font-mono text-xs">
              {logs.map((entry) => (
                <li
                  key={entry.log_id}
                  className={`${
                    entry.level === "error"
                      ? "text-red-600"
                      : entry.level === "warning"
                      ? "text-amber-600"
                      : "text-gray-700"
                  }`}
                >
                  <span className="text-gray-400 mr-2">
                    {new Date(entry.timestamp).toLocaleTimeString()}
                  </span>
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
  // Use the most recent completed job
  const latestJobId =
    jobs
      ?.filter((j) => j.status === "completed")
      .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())[0]
      ?.job_id ?? "";
  const {
    data: results,
    isLoading: resultsLoading,
    refetch,
  } = useJobResults(latestJobId);

  const [selectedSegmentId, setSelectedSegmentId] = useState<string | null>(null);

  const segments = results?.segments ?? [];
  const selectedSegment =
    segments.find((s) => s.segment_id === selectedSegmentId) ?? segments[0] ?? null;

  const jobId = results?.job_id ?? "";

  if (recLoading || jobsLoading || resultsLoading) {
    return (
      <main className="flex min-h-screen items-center justify-center">
        <p className="text-sm text-gray-500">Loading…</p>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-gray-50 p-6">
      <div className="mx-auto max-w-6xl space-y-4">
        {/* Header */}
        <div className="flex items-center gap-3">
          <Link href="/dashboard" className="text-sm text-blue-600 hover:underline">
            ← Dashboard
          </Link>
          <h1 className="text-xl font-bold text-gray-900 truncate">
            {recording?.filename ?? recordingId}
          </h1>
          <Link
            href={`/recordings/${recordingId}/report`}
            className="ml-auto text-sm text-blue-600 hover:underline"
          >
            View Report →
          </Link>
        </div>

        {/* Waveform */}
        <div className="rounded-lg border border-gray-200 bg-white p-4">
          <h2 className="mb-2 text-sm font-semibold text-gray-700">Waveform</h2>
          <WaveformViewer
            data={[]}
            segmentBoundaries={segments.map((s) => ({
              start: s.start_sample,
              end: s.end_sample,
              classification: s.effective_classification,
            }))}
          />
          <p className="mt-1 text-xs text-gray-400">
            Waveform data not streamed — segment boundaries shown only.
          </p>
        </div>

        {/* Segment timeline */}
        <div className="rounded-lg border border-gray-200 bg-white p-4">
          <h2 className="mb-2 text-sm font-semibold text-gray-700">
            Segments ({segments.length})
          </h2>
          {segments.length > 0 ? (
            <SegmentTimeline
              segments={segments}
              selectedSegmentId={selectedSegmentId ?? undefined}
              onSelect={setSelectedSegmentId}
            />
          ) : (
            <p className="text-sm text-gray-500">No segments available.</p>
          )}
        </div>

        {/* Selected segment detail */}
        {selectedSegment && (
          <SelectedSegmentPanel
            segment={selectedSegment}
            onOverrideCreated={() => refetch()}
          />
        )}

        {/* Agent logs */}
        {jobId && <AgentLogSection jobId={jobId} />}
      </div>
    </main>
  );
}
