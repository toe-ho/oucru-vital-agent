"use client";

import { useState } from "react";
import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { getRecording, getWaveform } from "@/services/recordings";
import { getJobResults } from "@/services/assessments";
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from "recharts";
import type { SegmentSummary } from "@/types/api";

export default function MonitorPage() {
  const { id } = useParams<{ id: string }>();
  const [segIdx, setSegIdx] = useState(0);

  const { data: recording } = useQuery({
    queryKey: ["recording", id],
    queryFn: () => getRecording(id),
  });

  const { data: results } = useQuery({
    queryKey: ["results", id],
    queryFn: async () => {
      // Use latest job — simplified: get recording then results
      const rec = await getRecording(id);
      // For now return null if no job ID readily available
      return null;
    },
    enabled: false, // Replaced by the results query below
  });

  const currentSeg: SegmentSummary | undefined = undefined; // Placeholder

  const { data: waveform, isLoading: loadingWaveform } = useQuery({
    queryKey: ["waveform", id, segIdx],
    queryFn: () =>
      getWaveform(id, {
        start: currentSeg ? currentSeg.start_time : 0,
        end: currentSeg ? currentSeg.end_time : 60,
        downsample: 5000,
      }),
    enabled: !!recording,
  });

  const chartData = waveform?.channels[0]?.data.map((v, i) => ({ i, v })) ?? [];

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-xl font-bold text-brand-900">
          Monitoring — {recording?.filename ?? id}
        </h1>
        <span className={`px-3 py-1 rounded-full text-sm font-medium ${
          recording?.status === "completed" ? "bg-green-100 text-green-800" :
          "bg-yellow-100 text-yellow-800"
        }`}>{recording?.status}</span>
      </div>

      <div className="bg-white border rounded-lg p-4 shadow-sm mb-4">
        {loadingWaveform ? (
          <div className="h-48 flex items-center justify-center text-gray-400">Loading waveform...</div>
        ) : chartData.length > 0 ? (
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis dataKey="i" hide />
              <YAxis />
              <Tooltip formatter={(v: number) => v.toFixed(4)} />
              <Line
                type="monotone"
                dataKey="v"
                stroke="#1e3a5f"
                strokeWidth={1}
                dot={false}
              />
            </LineChart>
          </ResponsiveContainer>
        ) : (
          <div className="h-48 flex items-center justify-center text-gray-400">
            No waveform data available
          </div>
        )}
      </div>

      <div className="bg-white border rounded-lg p-4 shadow-sm">
        <h2 className="font-semibold text-gray-800 mb-2">Recording Details</h2>
        <dl className="grid grid-cols-2 gap-x-4 gap-y-2 text-sm">
          {[
            ["Signal Type", recording?.signal_type?.toUpperCase()],
            ["Sampling Rate", recording?.sampling_rate ? `${recording.sampling_rate} Hz` : "—"],
            ["Duration", recording?.duration_seconds ? `${recording.duration_seconds}s` : "—"],
            ["Subject", recording?.subject_id ?? "—"],
          ].map(([k, v]) => (
            <>
              <dt key={`k-${k}`} className="text-gray-500">{k}</dt>
              <dd key={`v-${k}`} className="font-medium">{v}</dd>
            </>
          ))}
        </dl>
      </div>
    </div>
  );
}
