'use client';

import { CheckCircle, XCircle } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Stat } from "@/components/ui/stat";
import type { SegmentResult } from "@/lib/types";

interface SqiScoresPanelProps {
  segment: SegmentResult;
}

export function SqiScoresPanel({ segment }: SqiScoresPanelProps) {
  const metrics = segment.sqi_summary ?? [];

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm">
          SQI Scores
          {segment.quality_score !== undefined && (
            <span className="ml-2 font-normal text-muted-foreground">
              Overall: <Stat className="font-semibold text-foreground">
                {(segment.quality_score * 100).toFixed(1)}%
              </Stat>
            </span>
          )}
        </CardTitle>
      </CardHeader>
      <CardContent>
        {metrics.length === 0 ? (
          <p className="text-xs text-muted-foreground">No SQI metrics available.</p>
        ) : (
          <div aria-live="polite" role="status" aria-label="SQI metric scores">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-border text-muted-foreground">
                  <th className="pb-1 text-left font-medium">Metric</th>
                  <th className="pb-1 text-right font-medium">Value</th>
                  <th className="pb-1 text-right font-medium">Range</th>
                  <th className="pb-1 text-center font-medium">Pass</th>
                </tr>
              </thead>
              <tbody>
                {metrics.map((m) => {
                  const rangeStr =
                    m.threshold_min !== undefined && m.threshold_max !== undefined
                      ? `${m.threshold_min}–${m.threshold_max}`
                      : m.threshold_min !== undefined
                      ? `≥${m.threshold_min}`
                      : m.threshold_max !== undefined
                      ? `≤${m.threshold_max}`
                      : "—";

                  return (
                    <tr key={m.metric_name} className="border-b border-border/50">
                      <td className="py-1 font-mono text-foreground">{m.metric_name}</td>
                      <td className="py-1 text-right">
                        <Stat className="text-foreground">
                          {typeof m.value === "number" ? m.value.toFixed(3) : m.value}
                        </Stat>
                      </td>
                      <td className="py-1 text-right">
                        <Stat className="text-muted-foreground">{rangeStr}</Stat>
                      </td>
                      <td className="py-1 text-center">
                        {m.passed ? (
                          <span aria-label="Passed">
                            <CheckCircle className="inline h-3.5 w-3.5 text-accept" aria-hidden="true" />
                            <span className="sr-only">Passed</span>
                          </span>
                        ) : (
                          <span aria-label="Failed">
                            <XCircle className="inline h-3.5 w-3.5 text-reject" aria-hidden="true" />
                            <span className="sr-only">Failed</span>
                          </span>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
