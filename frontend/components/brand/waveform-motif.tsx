import * as React from "react";
import { cn } from "@/lib/utils";

/** Decorative abstract waveform SVG — NOT a real patient trace, purely ornamental. */
export function WaveformMotif({ className }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 400 80"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      className={cn("text-primary/20 w-full", className)}
    >
      <polyline points="0,40 30,40 40,20 50,55 60,30 70,45 80,35 90,40 120,40 130,15 140,60 150,25 160,50 170,35 180,40 220,40 230,22 240,52 250,32 260,48 270,38 280,40 310,40 320,18 330,58 340,28 350,46 360,36 370,40 400,40" />
    </svg>
  );
}
