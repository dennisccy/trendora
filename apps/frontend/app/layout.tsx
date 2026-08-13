import type { Metadata } from "next";
import { headers } from "next/headers";

import "./globals.css";
import { AsOfProvider } from "@/components/asof-provider";
import { AsOfSwitcher } from "@/components/asof-switcher";
import { HealthBadge } from "@/components/health-badge";
import { PreflightBanner } from "@/components/preflight-banner";
import { ReadinessProvider } from "@/components/readiness-provider";
import { Sidebar } from "@/components/sidebar";
import { ASOF_HEADER, isValidIsoDate } from "@/lib/dates";
import { GlossaryProvider } from "@/lib/glossary";

export const metadata: Metadata = {
  title: "Trendora",
  description: "Local-first, research-only US-equity leadership scanner — decision support, no orders.",
};

// This stays a SERVER component (no `"use client"`). It reads the `x-asof` request header the J-83
// middleware forwards (the shape-valid `?asof` deep-link value) and seeds `AsOfProvider` with it as
// `initialAsOf`, so the server-rendered HTML and the client's first paint resolve the ONE global as-of
// state identically — no React hydration mismatch, no latest→D chrome flip. `headers()` is async in
// Next 15, so the layout is async; the value is re-shape-validated here as a defensive read.
export default async function RootLayout({ children }: { children: React.ReactNode }) {
  const headerStore = await headers();
  const forwarded = headerStore.get(ASOF_HEADER);
  const initialAsOf = forwarded && isValidIsoDate(forwarded) ? forwarded : null;

  return (
    <html lang="en" className="dark">
      <body>
        <ReadinessProvider>
          <AsOfProvider initialAsOf={initialAsOf}>
            <GlossaryProvider>
            <div className="flex min-h-screen">
              <Sidebar />
              <div className="flex min-w-0 flex-1 flex-col">
                {/* ops-hardening iter-77 (iter-76/e fix): `min-h-14` (was a fixed `h-14`) + `flex-wrap`
                    on the badge row below — at 1280x800 the combined AsOfSwitcher + HealthBadge content
                    (readiness pill + staleness annotation + background-compute chip + provider/seed/
                    symbol badges) can exceed the row's available width; without a wrap allowance the
                    row simply overflowed the header's right edge instead of wrapping, pushing the
                    "Ready" pill off-screen. `min-h-14` keeps the header at its normal 56px height on
                    every page/width where content already fits on one line (unchanged), and only grows
                    to a second line when the row actually wraps — HealthBadge's own inner `flex-wrap`
                    (unchanged) can now take effect because the outer row no longer blocks it. */}
                <header className="sticky top-0 z-10 flex min-h-14 items-center justify-between gap-4 border-b border-border bg-surface px-6 py-2">
                  <span className="hidden text-sm text-text-muted lg:inline">
                    Research-only · decision support · no orders
                  </span>
                  <div className="flex flex-1 flex-wrap items-center justify-end gap-3">
                    <AsOfSwitcher />
                    <HealthBadge />
                  </div>
                </header>
                <PreflightBanner />
                <main className="flex-1 overflow-x-auto p-6">{children}</main>
              </div>
            </div>
            </GlossaryProvider>
          </AsOfProvider>
        </ReadinessProvider>
      </body>
    </html>
  );
}
