"use client";

import { QueryClientProvider } from "@tanstack/react-query";
import { getQueryClient } from "@/lib/query-client";
import NavBar from "@/components/layout/NavBar";
import "./globals.css";

export default function RootLayout({ children }: { children: React.ReactNode }) {
  const queryClient = getQueryClient();

  return (
    <html lang="en">
      <body className="bg-gray-50 min-h-screen">
        <QueryClientProvider client={queryClient}>
          <NavBar />
          <main className="max-w-7xl mx-auto px-4 py-8">{children}</main>
        </QueryClientProvider>
      </body>
    </html>
  );
}
