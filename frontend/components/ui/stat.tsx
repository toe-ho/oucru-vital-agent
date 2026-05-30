import * as React from "react";
import { cn } from "@/lib/utils";

/** Wraps any numeric/measurement value in mono tabular-nums. */
export function Stat({ className, children, ...props }: React.HTMLAttributes<HTMLSpanElement>) {
  return (
    <span className={cn("num", className)} {...props}>
      {children}
    </span>
  );
}
