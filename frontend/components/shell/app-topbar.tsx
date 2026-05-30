'use client';

import { Menu, LogOut, User } from "lucide-react";
import { useAuth } from "@/lib/auth-context";
import { Button } from "@/components/ui/button";
import { ThemeToggle } from "./theme-toggle";
import { Breadcrumbs } from "./breadcrumbs";

interface AppTopbarProps {
  onMenuClick?: () => void;
}

export function AppTopbar({ onMenuClick }: AppTopbarProps) {
  const { user, logout } = useAuth();

  return (
    <header className="flex h-14 items-center gap-3 border-b border-border bg-card px-4">
      {/* Mobile menu toggle */}
      <Button
        variant="ghost"
        size="icon"
        className="md:hidden"
        onClick={onMenuClick}
        aria-label="Open navigation menu"
      >
        <Menu className="h-5 w-5" />
      </Button>

      {/* Breadcrumbs */}
      <div className="flex-1 overflow-hidden">
        <Breadcrumbs />
      </div>

      {/* Right controls */}
      <div className="flex items-center gap-1">
        <ThemeToggle />

        {user && (
          <div className="flex items-center gap-1">
            <span className="hidden text-xs text-muted-foreground sm:block">
              <User className="inline h-3 w-3 mr-1" aria-hidden="true" />
              {user.name}
            </span>
            <Button
              variant="ghost"
              size="icon"
              onClick={logout}
              aria-label="Sign out"
            >
              <LogOut className="h-4 w-4" />
            </Button>
          </div>
        )}
      </div>
    </header>
  );
}
