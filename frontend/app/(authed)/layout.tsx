'use client';

import { useState } from "react";
import { AppSidebar } from "@/components/shell/app-sidebar";
import { AppTopbar } from "@/components/shell/app-topbar";
import { Dialog, DialogContent } from "@/components/ui/dialog";
import { AppSidebar as MobileSidebar } from "@/components/shell/app-sidebar";

export default function AuthedLayout({ children }: { children: React.ReactNode }) {
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <div className="flex h-screen overflow-hidden">
      {/* Desktop sidebar */}
      <div className="hidden md:flex md:flex-col">
        <AppSidebar />
      </div>

      {/* Mobile drawer */}
      <Dialog open={mobileOpen} onOpenChange={setMobileOpen}>
        <DialogContent className="fixed left-0 top-0 h-full w-56 translate-x-0 translate-y-0 rounded-none p-0 data-[state=open]:slide-in-from-left data-[state=closed]:slide-out-to-left">
          <MobileSidebar />
        </DialogContent>
      </Dialog>

      {/* Main content */}
      <div className="flex flex-1 flex-col overflow-hidden">
        <AppTopbar onMenuClick={() => setMobileOpen(true)} />
        <main className="flex-1 overflow-y-auto bg-background p-6">
          {children}
        </main>
      </div>
    </div>
  );
}
