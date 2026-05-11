"use client";

import { useParams, useSearchParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Cell,
  ResponsiveContainer,
} from "recharts";
import client from "@/services/api-client";
import type { ReportResponse } from "@/types/api";

// ---------------------------------------------------------------------------
// Data fetching
// ---------------------------------------------------------------------------

async function fetchReport(reportId: string): Promise<ReportResponse> {
  const res = await client.get<ReportResponse>(`/reports/${reportId}`);
  return res.data;
}

// ---------------------------------------------------------------------------
// Helper components
// ---------------------------------------------------------------------------

function SectionAnchor({ id, label }: { id: string; label: string }) {
  return (
    <a
      href={`#${id}`}
      className="block px-3 py-1.5 rounded text-sm text-slate-600 hover:bg-slate-100 hover:text-slate-900 transition-colors"
    >
      {label}
    </a>
  );
}

function ScoreBadge({ score }: { score: number }) {
  const color =
    score >= 0.8
      ? "bg-green-100 text-green-800"
      : score >= 0.6
      ? "bg-yellow-100 text-yellow-800"
      : "bg-red-100 text-red-800";
  return (
    <span className={`inline-flex px-2 py-0.5 rounded text-xs font-semibold ${color}`}>
      {score.toFixed(3)}
    </span>
  );
}

function ClassBadge({ cls }: { cls: string }) {
  const color =
    cls === "accept"
      ? "bg-green-100 text-green-700"
      : cls === "reject"
      ? "bg-red-100 text-red-700"
      : "bg-yellow-100 text-yellow-700";
  return (
    <span className={`inline-flex px-2 py-0.5 rounded text-xs font-medium uppercase ${color}`}>
      {cls}
    </span>
  );
}

function formatTime(sec: number): string {
  const m = Math.floor(sec / 60);
  const s = Math.floor(sec % 60);
  return `${m}:${s.toString().padStart(2, "0")}`;
}

// ---------------------------------------------------------------------------
// Timeline heatmap
// ---------------------------------------------------------------------------

type TimelineSeg = {
  segment_number: number;
  start_time: number;
  end_time: number;
  classification: string;
  quality_score: number | null;
};

function TimelineHeatmap({ segments }: { segments: TimelineSeg[] }) {
  const colorMap: Record<string, string> = {
    accept: "#22c55e",
    reject: "#ef4444",
    pending: "#eab308",
    uncomputable: "#94a3b8",
  };

  const data = segments.map((s) => ({
    name: `S${s.segment_number}`,
    value: 1,
    cls: s.classification,
    score: s.quality_score ?? 0,
    start: formatTime(s.start_time),
    end: formatTime(s.end_time),
  }));

  return (
    <ResponsiveContainer width="100%" height={64}>
      <BarChart data={data} barCategoryGap={1} margin={{ top: 0, right: 0, bottom: 0, left: 0 }}>
        <XAxis dataKey="name" hide />
        <YAxis hide domain={[0, 1]} />
        <Tooltip
          content={({ active, payload }) => {
            if (!active || !payload?.[0]) return null;
            const d = payload[0].payload;
            return (
              <div className="bg-white border border-slate-200 rounded shadow px-2 py-1 text-xs">
                <div className="font-medium">{d.name}</div>
                <div>{d.start}–{d.end}</div>
                <div>Score: {d.score.toFixed(3)}</div>
                <div className="capitalize">{d.cls}</div>
              </div>
            );
          }}
        />
        <Bar dataKey="value" isAnimationActive={false}>
          {data.map((d, i) => (
            <Cell key={i} fill={colorMap[d.cls] ?? "#94a3b8"} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

// ---------------------------------------------------------------------------
// Main page
// ---------------------------------------------------------------------------

export default function ReportPage() {
  const params = useParams<{ id: string }>();
  const searchParams = useSearchParams();
  const reportId = searchParams.get("reportId");

  const { data: report, isLoading, isError } = useQuery({
    queryKey: ["report", reportId],
    queryFn: () => fetchReport(reportId!),
    enabled: !!reportId,
    refetchInterval: (query) =>
      query.state.data?.status === "generating" ? 3000 : false,
  });

  // Export handlers
  const handlePdfExport = () => {
    window.open(
      `${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api"}/reports/${reportId}?format=pdf`,
      "_blank"
    );
  };

  const handleHtmlExport = () => {
    if (!report?.content_html) return;
    const blob = new Blob([report.content_html as string], { type: "text/html" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `quality-report-${params.id}.html`;
    a.click();
    URL.revokeObjectURL(url);
  };

  if (!reportId) {
    return (
      <div className="text-center py-20 text-slate-500">
        No report ID provided. Navigate here from an assessment result.
      </div>
    );
  }

  if (isLoading || report?.status === "generating") {
    return (
      <div className="text-center py-20 text-slate-500">
        <div className="animate-spin w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full mx-auto mb-4" />
        Generating report…
      </div>
    );
  }

  if (isError || !report) {
    return (
      <div className="text-center py-20 text-red-500">Failed to load report.</div>
    );
  }

  const content = report.content_json as {
    summary?: Record<string, unknown>;
    timeline?: TimelineSeg[];
    flagged_segments?: Array<{
      segment_number: number;
      start_time: number;
      end_time: number;
      quality_score: number | null;
      failed_rules: Array<{ metric: string; value: number; threshold: number; operator: string }>;
    }>;
    recommendations?: string[];
    agent_interpretation?: string;
    confidence?: string;
  } | undefined;

  const summary = content?.summary ?? {};
  const timeline = content?.timeline ?? [];
  const flagged = content?.flagged_segments ?? [];
  const recommendations = content?.recommendations ?? [];

  return (
    <div className="flex gap-8">
      {/* Sticky sidebar nav */}
      <aside className="hidden lg:block w-44 shrink-0">
        <div className="sticky top-24 space-y-1">
          <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider px-3 mb-2">
            Sections
          </p>
          <SectionAnchor id="summary" label="Executive Summary" />
          <SectionAnchor id="timeline" label="Quality Timeline" />
          <SectionAnchor id="flagged" label="Flagged Segments" />
          <SectionAnchor id="recommendations" label="Recommendations" />
        </div>
      </aside>

      {/* Report body */}
      <div className="flex-1 max-w-4xl space-y-8">
        {/* Header */}
        <div className="bg-white rounded-lg border border-slate-200 p-6">
          <div className="flex items-start justify-between">
            <div>
              <h1 className="text-xl font-semibold text-slate-900">
                OUCRU Signal Quality Assessment Report
              </h1>
              <p className="text-sm text-slate-500 mt-1">
                Generated:{" "}
                {report.generated_at
                  ? new Date(report.generated_at).toLocaleString()
                  : "—"}
              </p>
            </div>
            <div className="flex gap-2">
              <button
                onClick={handlePdfExport}
                className="px-3 py-1.5 text-sm font-medium bg-slate-900 text-white rounded hover:bg-slate-700 transition-colors"
              >
                PDF
              </button>
              <button
                onClick={handleHtmlExport}
                className="px-3 py-1.5 text-sm font-medium border border-slate-300 text-slate-700 rounded hover:bg-slate-50 transition-colors"
              >
                HTML
              </button>
              <button
                onClick={() => window.print()}
                className="px-3 py-1.5 text-sm font-medium border border-slate-300 text-slate-700 rounded hover:bg-slate-50 transition-colors"
              >
                Print
              </button>
            </div>
          </div>

          <dl className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            {[
              ["Recording", String(summary.filename ?? params.id)],
              ["Signal Type", String(summary.signal_type ?? "—").toUpperCase()],
              [
                "Overall Score",
                typeof summary.acceptance_rate === "number"
                  ? summary.acceptance_rate.toFixed(3)
                  : "—",
              ],
              ["Assessed", summary.assessed_at ? new Date(String(summary.assessed_at)).toLocaleDateString() : "—"],
            ].map(([label, value]) => (
              <div key={label}>
                <dt className="text-slate-500">{label}</dt>
                <dd className="font-medium text-slate-900">{value}</dd>
              </div>
            ))}
          </dl>
        </div>

        {/* Section 1: Executive Summary */}
        <section id="summary" className="bg-white rounded-lg border border-slate-200 p-6">
          <h2 className="text-base font-semibold text-slate-900 mb-4">1. Executive Summary</h2>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            {[
              { label: "Total Segments", value: String(summary.total_segments ?? "—") },
              {
                label: "Accepted",
                value: `${summary.accepted ?? "—"} (${
                  typeof summary.acceptance_rate === "number"
                    ? (Number(summary.acceptance_rate) * 100).toFixed(1)
                    : "—"
                }%)`,
                color: "text-green-700",
              },
              {
                label: "Rejected",
                value: String(summary.rejected ?? "—"),
                color: "text-red-700",
              },
              {
                label: "Verdict",
                value: String(summary.overall_verdict ?? "—"),
              },
            ].map(({ label, value, color }) => (
              <div key={label} className="bg-slate-50 rounded p-3">
                <div className="text-xs text-slate-500">{label}</div>
                <div className={`text-lg font-semibold mt-0.5 ${color ?? "text-slate-900"}`}>
                  {value}
                </div>
              </div>
            ))}
          </div>

          {content?.agent_interpretation && (
            <p className="text-sm text-slate-700 leading-relaxed border-l-4 border-blue-200 pl-4">
              {content.agent_interpretation}
            </p>
          )}
        </section>

        {/* Section 2: Quality Timeline */}
        <section id="timeline" className="bg-white rounded-lg border border-slate-200 p-6">
          <h2 className="text-base font-semibold text-slate-900 mb-4">2. Quality Timeline</h2>

          {timeline.length > 0 ? (
            <>
              <TimelineHeatmap segments={timeline} />
              <div className="flex gap-4 mt-3 text-xs text-slate-500">
                <span className="flex items-center gap-1">
                  <span className="w-3 h-3 rounded-sm bg-green-500 inline-block" /> Accept
                </span>
                <span className="flex items-center gap-1">
                  <span className="w-3 h-3 rounded-sm bg-red-500 inline-block" /> Reject
                </span>
                <span className="flex items-center gap-1">
                  <span className="w-3 h-3 rounded-sm bg-yellow-400 inline-block" /> Pending
                </span>
              </div>
            </>
          ) : (
            <p className="text-sm text-slate-400">No timeline data available.</p>
          )}
        </section>

        {/* Section 3: Flagged Segments */}
        <section id="flagged" className="bg-white rounded-lg border border-slate-200 p-6">
          <h2 className="text-base font-semibold text-slate-900 mb-4">3. Flagged Segments</h2>

          {flagged.length === 0 ? (
            <p className="text-sm text-slate-400">No flagged segments.</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-slate-200 text-left text-xs text-slate-500 uppercase tracking-wider">
                    <th className="pb-2 pr-4">Seg</th>
                    <th className="pb-2 pr-4">Time</th>
                    <th className="pb-2 pr-4">Primary Reason</th>
                    <th className="pb-2 pr-4">Score</th>
                    <th className="pb-2">Class</th>
                  </tr>
                </thead>
                <tbody>
                  {flagged.map((seg) => {
                    const primaryRule = seg.failed_rules?.[0];
                    return (
                      <tr
                        key={seg.segment_number}
                        className="border-b border-slate-100 last:border-0"
                      >
                        <td className="py-2 pr-4 font-medium">{seg.segment_number}</td>
                        <td className="py-2 pr-4 text-slate-500">
                          {formatTime(seg.start_time)}–{formatTime(seg.end_time)}
                        </td>
                        <td className="py-2 pr-4 text-slate-700">
                          {primaryRule
                            ? `${primaryRule.metric} (${primaryRule.value.toFixed(2)} ${
                                primaryRule.operator === "min" ? "<" : ">"
                              } ${primaryRule.threshold})`
                            : "—"}
                        </td>
                        <td className="py-2 pr-4">
                          {seg.quality_score != null ? (
                            <ScoreBadge score={seg.quality_score} />
                          ) : (
                            "—"
                          )}
                        </td>
                        <td className="py-2">
                          <ClassBadge cls="reject" />
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </section>

        {/* Section 4: Recommendations */}
        <section id="recommendations" className="bg-white rounded-lg border border-slate-200 p-6">
          <h2 className="text-base font-semibold text-slate-900 mb-4">4. Recommendations</h2>

          {recommendations.length === 0 ? (
            <p className="text-sm text-slate-400">No recommendations generated.</p>
          ) : (
            <ul className="space-y-2">
              {recommendations.map((rec, i) => (
                <li key={i} className="flex gap-3 text-sm text-slate-700">
                  <span className="text-blue-500 shrink-0">•</span>
                  <span>{rec}</span>
                </li>
              ))}
            </ul>
          )}

          {content?.confidence && (
            <p className="mt-4 text-xs text-slate-400">
              Confidence:{" "}
              <span className="font-medium capitalize">{content.confidence}</span>
            </p>
          )}
        </section>
      </div>
    </div>
  );
}
