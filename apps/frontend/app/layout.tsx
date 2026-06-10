import type { Metadata } from "next";

import "./globals.css";
import { AsOfProvider } from "@/components/asof-provider";
import { AsOfSwitcher } from "@/components/asof-switcher";
import { HealthBadge } from "@/components/health-badge";
import { ReadinessProvider } from "@/components/readiness-provider";
import { Sidebar } from "@/components/sidebar";

export const metadata: Metadata = {
  title: "Trendora",
  description: "Local-first, research-only US-equity leadership scanner — decision support, no orders.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body>
        <ReadinessProvider>
          <AsOfProvider>
            <div className="flex min-h-screen">
              <Sidebar />
              <div className="flex min-w-0 flex-1 flex-col">
                <header className="sticky top-0 z-10 flex h-14 items-center justify-between gap-4 border-b border-border bg-surface px-6">
                  <span className="hidden text-sm text-text-muted lg:inline">
                    Research-only · decision support · no orders
                  </span>
                  <div className="flex flex-1 items-center justify-end gap-3">
                    <AsOfSwitcher />
                    <HealthBadge />
                  </div>
                </header>
                <main className="flex-1 overflow-x-auto p-6">{children}</main>
              </div>
            </div>
          </AsOfProvider>
        </ReadinessProvider>
      </body>
    </html>
  );
}
