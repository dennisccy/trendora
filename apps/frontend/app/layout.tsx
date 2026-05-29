import type { Metadata } from "next";

import "./globals.css";
import { HealthBadge } from "@/components/health-badge";
import { Sidebar } from "@/components/sidebar";

export const metadata: Metadata = {
  title: "Trendora",
  description: "Local-first, research-only US-equity leadership scanner — decision support, no orders.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body>
        <div className="flex min-h-screen">
          <Sidebar />
          <div className="flex min-w-0 flex-1 flex-col">
            <header className="sticky top-0 z-10 flex h-14 items-center justify-between gap-4 border-b border-border bg-surface px-6">
              <span className="text-sm text-text-muted">Research-only · decision support · no orders</span>
              <HealthBadge />
            </header>
            <main className="flex-1 overflow-x-auto p-6">{children}</main>
          </div>
        </div>
      </body>
    </html>
  );
}
