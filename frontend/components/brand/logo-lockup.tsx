import * as React from "react";
import { cn } from "@/lib/utils";
import { LogoMark } from "./logo-mark";

interface LogoLockupProps {
  collapsed?: boolean;
  className?: string;
}

export function LogoLockup({ collapsed = false, className }: LogoLockupProps) {
  return (
    <div className={cn("flex items-center gap-2", className)}>
      <LogoMark size={28} />
      {!collapsed && (
        <div className="flex flex-col leading-none">
          <span className="text-sm font-semibold tracking-tight text-foreground">
            Vital Agent
          </span>
          <span className="text-[10px] font-medium tracking-[0.15em] text-muted-foreground uppercase">
            OUCRU
          </span>
        </div>
      )}
    </div>
  );
}
