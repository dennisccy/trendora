"use client";

import { useEffect } from "react";
import { AlertTriangle, RotateCcw } from "lucide-react";

import { Card } from "@/components/ui/card";

/**
 * iter-19 — route-level error boundary (Next.js App Router special file). Catches any uncaught
 * exception thrown while rendering a page (or its children) in `app/` and degrades to a CONTAINED error
 * card instead of a blank "Application error" screen. `error.tsx` renders IN PLACE of the page inside the
 * root layout's `{children}` slot, so the sidebar nav + header (app/layout.tsx) keep rendering around it
 * — the rest of the app stays usable (anti-goal #8: resilience to data-shape/data-scale change; "the UI
 * degrades gracefully — contained error boundary... never a blank application-error page").
 *
 * This is the exact containment the iter-18 regression lacked: an unguarded null `.sector.localeCompare`
 * on `/stocks` threw an uncaught TypeError with no boundary in place, collapsing the WHOLE page (nav
 * included) to Next's default blank error screen. That specific crash is separately fixed at its source
 * (`lib/sector-label.ts`'s null-safe comparator) — this boundary is the general-purpose safety net for
 * any OTHER future uncaught client error, on any page.
 *
 * Must be a Client Component (Next.js requirement for `error.tsx`).
 */
export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    // Log for local/operator visibility. No user-identifying data; the error object is whatever the
    // thrown exception carried (a message string) — never fabricated, never silently swallowed.
    // eslint-disable-next-line no-console
    console.error("Unhandled client error:", error);
  }, [error]);

  return (
    <div className="space-y-4">
      <Card className="flex items-start gap-3 border-neg bg-surface p-5 text-sm text-neg" role="alert">
        <AlertTriangle className="h-5 w-5 shrink-0" aria-hidden />
        <div className="space-y-3">
          <div>
            <p className="font-medium">Something went wrong on this page</p>
            <p className="text-text-muted">
              An unexpected error stopped this page from rendering. No data is lost — use the sidebar to
              open another page, or try this one again.
            </p>
          </div>
          <button
            type="button"
            onClick={() => reset()}
            className="inline-flex h-8 items-center gap-1.5 rounded-md border border-border bg-surface-2 px-3 text-xs font-medium text-text transition-colors hover:border-border-strong hover:bg-surface focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-accent active:bg-border"
          >
            <RotateCcw className="h-3.5 w-3.5" aria-hidden />
            Try again
          </button>
        </div>
      </Card>
    </div>
  );
}
