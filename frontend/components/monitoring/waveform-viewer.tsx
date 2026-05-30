'use client';

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ReferenceLine,
  ReferenceArea,
  ResponsiveContainer,
} from "recharts";

const CLASSIFICATION_FILL: Record<string, string> = {
  accept: "#dcfce7",
  reject: "#fee2e2",
  uncomputable: "#fef3c7",
  pending: "#f3f4f6",
};

interface SegmentBoundary {
  start: number;
  end: number;
  classification: string;
}

interface WaveformViewerProps {
  data: { time: number; value: number }[];
  segmentBoundaries?: SegmentBoundary[];
}

export function WaveformViewer({ data, segmentBoundaries = [] }: WaveformViewerProps) {
  return (
    <div className="h-[200px] w-full">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 4, right: 8, bottom: 4, left: 8 }}>
          <XAxis dataKey="time" tick={{ fontSize: 10 }} minTickGap={40} />
          <YAxis tick={{ fontSize: 10 }} width={36} />
          <Tooltip
            contentStyle={{ fontSize: 11 }}
            formatter={(val: number) => [val.toFixed(3), "value"]}
            labelFormatter={(label) => `t=${label}`}
          />

          {/* Colored segment background areas */}
          {segmentBoundaries.map((seg, i) => (
            <ReferenceArea
              key={`area-${i}`}
              x1={seg.start}
              x2={seg.end}
              fill={CLASSIFICATION_FILL[seg.classification] ?? "#f3f4f6"}
              fillOpacity={0.5}
              strokeOpacity={0}
            />
          ))}

          {/* Boundary lines */}
          {segmentBoundaries.map((seg, i) => (
            <ReferenceLine
              key={`line-${i}`}
              x={seg.start}
              stroke="#94a3b8"
              strokeDasharray="3 3"
              strokeWidth={1}
            />
          ))}

          <Line
            type="monotone"
            dataKey="value"
            dot={false}
            stroke="#2563eb"
            strokeWidth={1.5}
            isAnimationActive={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
