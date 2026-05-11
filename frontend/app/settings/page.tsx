"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import client from "@/services/api-client";
import type { ThresholdsResponse } from "@/types/api";

export default function SettingsPage() {
  const qc = useQueryClient();
  const { data, isLoading } = useQuery<ThresholdsResponse>({
    queryKey: ["thresholds"],
    queryFn: async () => (await client.get("/settings/thresholds")).data,
  });

  const [editing, setEditing] = useState<Record<string, { min: string; max: string }>>({});
  const [saved, setSaved] = useState(false);

  const mutation = useMutation({
    mutationFn: async (thresholds: Record<string, { min?: number | null; max?: number | null }>) => {
      await client.put("/settings/thresholds", { thresholds });
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["thresholds"] });
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    },
  });

  function handleSave() {
    const thresholds: Record<string, { min?: number | null; max?: number | null }> = {};
    for (const [k, v] of Object.entries(editing)) {
      thresholds[k] = {
        min: v.min === "" ? null : Number(v.min),
        max: v.max === "" ? null : Number(v.max),
      };
    }
    mutation.mutate(thresholds);
  }

  if (isLoading) return <p className="text-gray-500">Loading settings…</p>;

  const thresholds = { ...(data?.thresholds ?? {}), ...Object.fromEntries(
    Object.entries(editing).map(([k, v]) => [k, { min: v.min === "" ? null : Number(v.min), max: v.max === "" ? null : Number(v.max) }])
  )};

  return (
    <div className="max-w-2xl">
      <h1 className="text-2xl font-bold text-brand-900 mb-6">Settings — SQI Thresholds</h1>

      <div className="bg-white border rounded-lg shadow-sm overflow-hidden mb-6">
        <table className="w-full text-sm">
          <thead className="bg-gray-100">
            <tr>
              <th className="text-left px-4 py-3 text-gray-700">Metric</th>
              <th className="text-left px-4 py-3 text-gray-700">Min</th>
              <th className="text-left px-4 py-3 text-gray-700">Max</th>
            </tr>
          </thead>
          <tbody>
            {Object.entries(data?.thresholds ?? {}).map(([metric, rule]) => (
              <tr key={metric} className="border-t">
                <td className="px-4 py-3 font-mono text-xs">{metric}</td>
                {(["min", "max"] as const).map((bound) => (
                  <td key={bound} className="px-4 py-3">
                    <input
                      type="number"
                      step="any"
                      defaultValue={rule[bound] ?? ""}
                      onChange={(e) =>
                        setEditing((prev) => ({
                          ...prev,
                          [metric]: { ...prev[metric], [bound]: e.target.value },
                        }))
                      }
                      className="border border-gray-300 rounded px-2 py-1 w-24 text-sm"
                    />
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="flex gap-3">
        <button
          onClick={handleSave}
          disabled={mutation.isPending}
          className="px-6 py-2 bg-brand-900 text-white rounded-lg font-medium disabled:opacity-40 hover:bg-brand-700"
        >
          {mutation.isPending ? "Saving…" : "Save Thresholds"}
        </button>
        {saved && <span className="text-green-600 text-sm self-center">Saved!</span>}
      </div>
    </div>
  );
}
