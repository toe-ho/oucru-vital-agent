"use client";

import { useQuery } from "@tanstack/react-query";
import { getDashboardSummary } from "@/services/dashboard";
import { useRouter } from "next/navigation";

export default function DashboardPage() {
  const router = useRouter();
  const { data, isLoading } = useQuery({
    queryKey: ["dashboard"],
    queryFn: () => getDashboardSummary({ days: 30 }),
    refetchInterval: 30_000,
  });

  if (isLoading) return <p className="text-gray-500">Loading dashboard...</p>;

  const summary = data;

  return (
    <div>
      <h1 className="text-2xl font-bold text-brand-900 mb-6">Quality Dashboard</h1>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        {[
          { label: "Total Recordings", value: summary?.total_recordings ?? 0 },
          { label: "Recent Assessments", value: summary?.recent_assessments.length ?? 0 },
          { label: "Active Alerts", value: summary?.alerts.filter((a) => !a.acknowledged).length ?? 0 },
          {
            label: "Avg Acceptance Rate",
            value: summary?.recent_assessments.length
              ? (
                  (summary.recent_assessments
                    .filter((a) => a.acceptance_rate !== null)
                    .reduce((s, a) => s + (a.acceptance_rate ?? 0), 0) /
                    summary.recent_assessments.filter((a) => a.acceptance_rate !== null).length) *
                  100
                ).toFixed(1) + "%"
              : "—",
          },
        ].map((kpi) => (
          <div key={kpi.label} className="bg-white border rounded-lg p-4 shadow-sm">
            <div className="text-2xl font-bold text-brand-900">{kpi.value}</div>
            <div className="text-xs text-gray-500 mt-1">{kpi.label}</div>
          </div>
        ))}
      </div>

      {/* Alerts */}
      {summary?.alerts.length ? (
        <div className="mb-8">
          <h2 className="text-lg font-semibold mb-3">Alerts</h2>
          <div className="space-y-2">
            {summary.alerts.map((alert) => (
              <div
                key={alert.alert_id}
                className="flex items-start gap-3 bg-red-50 border border-red-200 rounded-lg p-3"
              >
                <div className="w-2 h-2 rounded-full bg-red-500 mt-1.5 shrink-0" />
                <div>
                  <p className="text-sm text-red-800">{alert.message}</p>
                  <p className="text-xs text-gray-400 mt-0.5">{alert.created_at}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      ) : null}

      {/* Recent Assessments */}
      {summary?.recent_assessments.length ? (
        <div>
          <h2 className="text-lg font-semibold mb-3">Recent Assessments</h2>
          <table className="w-full text-sm border-collapse bg-white shadow-sm rounded-lg overflow-hidden">
            <thead className="bg-gray-100">
              <tr>
                <th className="text-left px-4 py-2">Recording</th>
                <th className="text-left px-4 py-2">Assessed</th>
                <th className="text-left px-4 py-2">Acceptance</th>
                <th className="text-left px-4 py-2">Verdict</th>
              </tr>
            </thead>
            <tbody>
              {summary.recent_assessments.map((a) => (
                <tr
                  key={a.assessment_job_id}
                  className="border-t hover:bg-gray-50 cursor-pointer"
                  onClick={() => router.push(`/recordings/${a.recording_id}/monitor`)}
                >
                  <td className="px-4 py-2 font-mono text-xs">{a.recording_id.slice(0, 8)}…</td>
                  <td className="px-4 py-2 text-gray-500">
                    {a.assessed_at ? new Date(a.assessed_at).toLocaleString() : "—"}
                  </td>
                  <td className="px-4 py-2">
                    {a.acceptance_rate != null ? (a.acceptance_rate * 100).toFixed(1) + "%" : "—"}
                  </td>
                  <td className="px-4 py-2">
                    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                      a.verdict === "acceptable" ? "bg-green-100 text-green-800" :
                      a.verdict === "marginal" ? "bg-yellow-100 text-yellow-800" :
                      "bg-red-100 text-red-800"
                    }`}>{a.verdict ?? "—"}</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <p className="text-gray-400">No recent assessments in the last 30 days.</p>
      )}
    </div>
  );
}
