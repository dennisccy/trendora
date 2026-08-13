"use client";

import { useReadiness } from "@/components/readiness-provider";
import { formatStaleAnnotation } from "@/lib/staleness-annotation";
import { cn } from "@/lib/utils";

/**
 * The single daily preflight verdict, rendered as an unmissable layout-level banner on every decision
 * surface (iter-33, J-20 / backlog B-301) — a risk-officer kill-switch UX: at a glance, is today's board
 * safe to trust? Mounted ONCE in `app/layout.tsx`; reads ONLY `useReadiness()` (the SAME single
 * `/api/health` poll the `HealthBadge` reads) — no second fetch, no per-page recompute (single source;
 * B-301's named trap is a page computing its own "mini-readiness").
 *
 * `GO` is a quiet, thin strip (does not compete for attention — protects the required-still-passing
 * surfaces' existing assertions); `DEGRADED`/`NO-GO` are loud, full-width banners naming the concrete
 * reasons verbatim from the payload — `NO-GO` always contains the exact phrase "do not rely on today's
 * board" (goal.md J-20 acceptance). Read-only status: no buttons/forms, no proven-language, no
 * buy/sell-order language (anti-goals #1/#2 — this gates trust, not orders).
 */
export function PreflightBanner() {
  const { preflight, loading, staleForS } = useReadiness();
  // ops-hardening iter-77 (J-04/J-07): the SAME "as of Ns ago" annotation the readiness badge renders,
  // reading the SAME single `useReadiness()` poll (no second fetch) -- honest by construction: null
  // (no annotation) for a fresh synchronous compute, a failed poll, or before the first poll resolves.
  const staleAnnotation = formatStaleAnnotation(staleForS);

  if (loading) {
    // Mirrors HealthBadge's `loading` state: a neutral placeholder, never a fabricated GO.
    return (
      <div
        data-testid="preflight-banner"
        data-verdict="loading"
        role="status"
        className="border-b border-border bg-surface px-6 py-1.5 text-xs text-text-muted"
      >
        Checking board status…
      </div>
    );
  }

  if (preflight === null) {
    // The health poll itself failed (backend unreachable) — an honest NO-GO, never a blank crash.
    // No staleness annotation here either: `staleForS` is already null on a failed poll (the SAME
    // honest-failure convention every sibling readiness field follows), so `staleAnnotation` above is
    // already null too — nothing to pass.
    return (
      <LoudBanner
        verdict="NO-GO"
        reasons={["Backend is unavailable — the preflight check could not run."]}
        staleAnnotation={null}
      />
    );
  }

  if (preflight.verdict === "GO") {
    return (
      <div
        data-testid="preflight-banner"
        data-verdict="GO"
        role="status"
        className="flex items-center gap-2 border-b border-pos/40 bg-pos/5 px-6 py-1.5 text-xs text-pos"
      >
        <span className="h-1.5 w-1.5 rounded-full bg-pos" aria-hidden />
        GO — today&apos;s board is current.
        {staleAnnotation ? (
          <span className="text-pos/70" data-testid="preflight-staleness">
            ({staleAnnotation})
          </span>
        ) : null}
      </div>
    );
  }

  return <LoudBanner verdict={preflight.verdict} reasons={preflight.reasons} staleAnnotation={staleAnnotation} />;
}

function LoudBanner({
  verdict,
  reasons,
  staleAnnotation,
}: {
  verdict: "DEGRADED" | "NO-GO";
  reasons: string[];
  staleAnnotation: string | null;
}) {
  const isNoGo = verdict === "NO-GO";
  return (
    <div
      data-testid="preflight-banner"
      data-verdict={verdict}
      role="alert"
      className={cn(
        "border-b px-6 py-3 text-sm",
        isNoGo ? "border-neg bg-neg/10 text-neg" : "border-warn bg-warn/10 text-warn",
      )}
    >
      <p className="font-semibold">
        {isNoGo
          ? "NO-GO — do not rely on today's board."
          : "DEGRADED — treat today's board with caution."}
        {staleAnnotation ? (
          <span className="ml-1.5 font-normal opacity-70" data-testid="preflight-staleness">
            ({staleAnnotation})
          </span>
        ) : null}
      </p>
      {reasons.length > 0 ? (
        <ul className="mt-1 list-disc space-y-0.5 pl-5">
          {reasons.map((reason) => (
            <li key={reason}>{reason}</li>
          ))}
        </ul>
      ) : null}
    </div>
  );
}
