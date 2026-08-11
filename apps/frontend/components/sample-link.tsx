"use client";

import Link from "next/link";
import { AlertTriangle } from "lucide-react";

import { useAsOfHref } from "@/components/asof-provider";
import { SampleSize } from "@/components/forward-return";
import { buildSamplesHref, type CohortParams, type SampleScope } from "@/lib/samples-link";
import { cn } from "@/lib/utils";

/**
 * J-51 — a published `N=` sample-size chip rendered as a LINK into the `/research/samples` drill-down for
 * the exact cohort it counts. It wraps the existing `SampleSize` chip (the single n-formatting source) so
 * the displayed `n=…` (+ the low-sample ⚠) is byte-identical to the non-linked chip — only now clickable.
 *
 * The href is built in two cleanly-separated steps, each with ONE author:
 *   1. `buildSamplesHref(cohort, scope)` serializes the COHORT selectors (kind/slice/params/horizon) +
 *      the analysis-mode `scope` (a cohort param — it changes WHICH observations pool).
 *   2. `useAsOfHref(...)` (the J-50 helper) merges the single global `?asof=D` while historical — the
 *      ONLY author of the date param, so there is no second date state.
 *
 * J-65 — the chip opens its drill-down in a NEW tab (`target="_blank"` + `rel="noopener noreferrer"`),
 * with the href construction BYTE-UNCHANGED from J-51 (same two-step `buildSamplesHref` + `useAsOfHref`
 * serialization, so cohort params + scope + `?asof` all carry — J-51/J-50 hold). Opening the drill-down
 * therefore never disturbs the originating Research tab's lab/scope/scroll state. New-tab in-app links are
 * now: stocks-leaderboard tickers (J-54), samples-row tickers (J-52), theme/sector member tickers
 * (J-57/J-58), and these `N=` chips (J-65); every OTHER in-app link (incl. the samples page's own "Back to
 * Research") stays same-window. Hover/focus underline the chip.
 *
 * `unavailable` (ops-hardening iter-60, J-05/J-07 closeout) is ADDITIVE and OPTIONAL, defaulting to
 * `false` — every existing call site that never passes it renders byte-unchanged. When `true` (a
 * `by_horizon` cell whose payload reports `status: "unavailable"` — a DEGRADED horizon, not a genuinely
 * empty cohort), the chip is a plain, non-tooltip-only "Unavailable" indicator, never the `n=0` link: the
 * cohort the link would drill into does not honestly exist for this response, so no `data-testid=
 * "sample-link"` element is rendered at all.
 */
export function SampleLink({
  n,
  min,
  cohort,
  scope,
  label,
  unavailable = false,
}: {
  n: number;
  min: number;
  cohort: CohortParams;
  /** The Research analysis mode ("asof" carries the point-in-time scope into the drill-down). */
  scope: SampleScope;
  /** Accessible label describing which cohort this chip drills into. */
  label: string;
  /** True for a degraded horizon (`status === "unavailable"`) — renders a non-link indicator instead. */
  unavailable?: boolean;
}) {
  const asofHref = useAsOfHref();

  if (unavailable) {
    return (
      <span
        className="inline-flex items-center gap-1 text-xs text-text-faint"
        data-testid="sample-link-unavailable"
        title="Temporarily unavailable — degraded under memory pressure"
      >
        <AlertTriangle className="h-3 w-3" aria-hidden />
        Unavailable
      </span>
    );
  }

  const href = asofHref(buildSamplesHref(cohort, scope));
  return (
    <Link
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      aria-label={label}
      title={label}
      data-testid="sample-link"
      className={cn(
        "inline-flex rounded-sm hover:underline",
        "focus-visible:underline focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-accent",
      )}
    >
      <SampleSize n={n} min={min} />
    </Link>
  );
}
