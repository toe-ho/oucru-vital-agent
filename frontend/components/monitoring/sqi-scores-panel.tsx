'use client';

import type { SegmentResult } from "@/lib/types";

interface SqiScoresPanelProps {
  segment: SegmentResult;
}

export function SqiScoresPanel({ segment }: SqiScoresPanelProps) {
  const metrics = segment.sqi_summary ?? [];

  return (
    <div className="rounded-lg border border-gray-200 bg-white p-4">
      <h3 className="mb-3 text-sm font-semibold text-gray-800">SQI Scores</h3>

      {metrics.length === 0 ? (
        <p className="text-xs text-gray-500">No SQI metrics available.</p>
      ) : (
        <table className="w-full text-xs">
          <thead>
            <tr className="border-b border-gray-100 text-gray-500">
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
                <tr key={m.metric_name} className="border-b border-gray-50">
                  <td className="py-1 font-mono text-gray-700">{m.metric_name}</td>
                  <td className="py-1 text-right text-gray-700">
                    {typeof m.value === "number" ? m.value.toFixed(3) : m.value}
                  </td>
                  <td className="py-1 text-right text-gray-500">{rangeStr}</td>
                  <td className="py-1 text-center">
                    {m.passed ? (
                      <span className="text-green-600" title="Passed">✓</span>
                    ) : (
                      <span className="text-red-600" title="Failed">✗</span>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      )}

      {segment.quality_score !== undefined && (
        <div className="mt-3 flex items-center justify-between border-t border-gray-100 pt-2">
          <span className="text-xs text-gray-500">Overall Quality Score</span>
          <span className="text-sm font-semibold text-gray-800">
            {(segment.quality_score * 100).toFixed(1)}%
          </span>
        </div>
      )}
    </div>
  );
}
