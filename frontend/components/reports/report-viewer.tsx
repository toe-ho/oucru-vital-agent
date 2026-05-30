'use client';

import { useReport } from "@/lib/queries/report-queries";
import { ClassificationBadge } from "@/components/ui/classification-badge";
import { Stat } from "@/components/ui/stat";
import { Button } from "@/components/ui/button";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

interface ReportViewerProps {
  reportId: string;
}

export function ReportViewer({ reportId }: ReportViewerProps) {
  const { data: report, isLoading, error } = useReport(reportId);

  if (isLoading) {
    return <div className="py-8 text-center text-sm text-muted-foreground">Loading report…</div>;
  }
  if (error || !report) {
    return <div className="py-8 text-center text-sm text-reject">Failed to load report.</div>;
  }

  const summary = report.content_json?.summary ?? {};
  const segments = report.content_json?.segments ?? [];

  return (
    <div className="space-y-6">
      {/* Stale banner — exact required copy */}
      {report.is_stale && (
        <div className="rounded-md border border-stale/30 bg-stale/10 px-4 py-3 text-sm text-stale" role="alert">
          Report is stale: overrides postdate generation. Regenerate to refresh.
        </div>
      )}

      {/* Verdict-first summary cards */}
      {Object.keys(summary).length > 0 && (
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
          {Object.entries(summary).map(([key, value]) => (
            <div key={key} className="rounded-lg border border-border bg-card p-3">
              <p className="truncate text-xs capitalize text-muted-foreground">
                {key.replace(/_/g, " ")}
              </p>
              <p className="mt-1 text-lg font-semibold text-foreground">
                <Stat>
                  {typeof value === "number" && value < 2
                    ? `${(value * 100).toFixed(1)}%`
                    : String(value)}
                </Stat>
              </p>
            </div>
          ))}
        </div>
      )}

      {/* Segments table */}
      {segments.length > 0 && (
        <div className="overflow-x-auto rounded-lg border border-border">
          <table className="min-w-full divide-y divide-border text-sm">
            <thead className="bg-muted/30">
              <tr>
                <th className="px-4 py-2 text-left text-xs font-medium text-muted-foreground">#</th>
                <th className="px-4 py-2 text-left text-xs font-medium text-muted-foreground">AI</th>
                <th className="px-4 py-2 text-left text-xs font-medium text-muted-foreground">Effective</th>
                <th className="px-4 py-2 text-right text-xs font-medium text-muted-foreground">Score</th>
                <th className="px-4 py-2 text-right text-xs font-medium text-muted-foreground">Overrides</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border bg-card">
              {segments.map((seg) => (
                <tr key={seg.segment_id} className="hover:bg-muted/30 transition-colors">
                  <td className="px-4 py-2 text-muted-foreground"><Stat>{seg.segment_number}</Stat></td>
                  <td className="px-4 py-2">
                    <ClassificationBadge classification={seg.ai_classification} />
                  </td>
                  <td className="px-4 py-2">
                    <ClassificationBadge classification={seg.effective_classification} effective />
                  </td>
                  <td className="px-4 py-2 text-right">
                    <Stat className="text-foreground">
                      {seg.quality_score !== undefined
                        ? `${(seg.quality_score * 100).toFixed(1)}%`
                        : "—"}
                    </Stat>
                  </td>
                  <td className="px-4 py-2 text-right">
                    <Stat className="text-muted-foreground">{seg.override_count}</Stat>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Export buttons */}
      <div className="flex gap-3">
        <Button variant="outline" size="sm" asChild>
          <a href={`${API_URL}/api/reports/${reportId}/export?format=html`} target="_blank" rel="noopener noreferrer">
            Download HTML
          </a>
        </Button>
        <Button variant="outline" size="sm" asChild>
          <a href={`${API_URL}/api/reports/${reportId}/export?format=pdf`} target="_blank" rel="noopener noreferrer">
            Download PDF
          </a>
        </Button>
      </div>
    </div>
  );
}
