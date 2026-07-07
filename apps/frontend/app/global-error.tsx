"use client";

import "./globals.css";

/**
 * iter-19 — the ROOT error boundary (Next.js App Router special file). Only activates when an error
 * escapes the root layout itself (`app/layout.tsx`) or its own `error.tsx` boundary — cases the per-route
 * `app/error.tsx` cannot catch, because in that scenario the root layout that normally renders the
 * sidebar/providers is exactly what is broken. Next.js requires `global-error.tsx` to render its OWN
 * `<html>`/`<body>` (it REPLACES the root layout when active), and it deliberately imports NOTHING from
 * the app's component/provider tree (no Sidebar, no AsOfProvider, no shared UI components) — those all
 * depend on the very layout this boundary exists to substitute for, so pulling any of them in here would
 * risk this last-resort fallback throwing too. It re-declares the same dark-theme CSS tokens via the
 * shared stylesheet import so it still reads as Trendora, not a browser-default crash page (anti-goal #8:
 * never a blank application-error page).
 */
export default function GlobalError({
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <html lang="en" className="dark">
      <body>
        <div className="flex min-h-screen items-center justify-center bg-bg p-6 text-text">
          <div className="w-full max-w-md space-y-4 rounded-lg border border-neg bg-surface p-6 text-sm text-neg">
            <p className="font-medium">Trendora hit an unexpected error</p>
            <p className="text-text-muted">
              The application failed to render. No data is lost — reloading usually recovers; if it keeps
              happening, note what you were doing and report it.
            </p>
            <button
              type="button"
              onClick={() => reset()}
              className="inline-flex h-8 items-center rounded-md border border-border bg-surface-2 px-3 text-xs font-medium text-text transition-colors hover:border-border-strong hover:bg-surface focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-accent active:bg-border"
            >
              Try again
            </button>
          </div>
        </div>
      </body>
    </html>
  );
}
