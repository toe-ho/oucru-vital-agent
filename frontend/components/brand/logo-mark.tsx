import * as React from "react";
import { cn } from "@/lib/utils";

interface LogoMarkProps extends React.SVGAttributes<SVGSVGElement> {
  size?: number;
}

/** Abstract monoline peak-to-baseline glyph — never recolored to a status hue. */
export function LogoMark({ size = 24, className, ...props }: LogoMarkProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      className={cn("text-primary", className)}
      {...props}
    >
      {/* Abstract signal-peak motif: baseline → rise → peak → descent → checkmark tail */}
      <polyline points="2,14 6,14 8,6 10,18 12,10 14,16 16,12 18,14 22,14" />
    </svg>
  );
}
