'use client';

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ReferenceArea,
  ReferenceLine,
  ResponsiveContainer,
} from "recharts";

// Neutral tints for segment background areas — no raw status hex
const CLASSIFICATION_FILL: Record<string, string> = {
  accept: "hsl(160 84% 39% / 0.12)",
  reject: "hsl(0 84% 60% / 0.12)",
  uncomputable: "hsl(38 92% 50% / 0.12)",
  pending: "hsl(220 14% 96% / 0.5)",
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
    <div className="h-[200px] w-full" role="img" aria-label="Waveform viewer — abstract signal boundaries">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 4, right: 8, bottom: 4, left: 8 }}>
          <XAxis dataKey="time" tick={{ fontSize: 10 }} minTickGap={40} />
          <YAxis tick={{ fontSize: 10 }} width={36} />
          <Tooltip
            contentStyle={{ fontSize: 11 }}
            formatter={(val: number) => [val.toFixed(3), "value"]}
            labelFormatter={(label) => `t=${label}`}
          />

          {/* Neutral segment background areas */}
          {segmentBoundaries.map((seg, i) => (
            <ReferenceArea
              key={`area-${i}`}
              x1={seg.start}
              x2={seg.end}
              fill={CLASSIFICATION_FILL[seg.classification] ?? "transparent"}
              fillOpacity={1}
              strokeOpacity={0}
            />
          ))}

          {/* Boundary lines */}
          {segmentBoundaries.map((seg, i) => (
            <ReferenceLine
              key={`line-${i}`}
              x={seg.start}
              stroke="hsl(215 16% 47% / 0.4)"
              strokeDasharray="3 3"
              strokeWidth={1}
            />
          ))}

          {/* Signal line — neutral slate, abstract */}
          <Line
            type="monotone"
            dataKey="value"
            dot={false}
            stroke="hsl(215 16% 47%)"
            strokeWidth={1.5}
            isAnimationActive={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
