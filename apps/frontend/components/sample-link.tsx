"use client";

import Link from "next/link";

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
 */
export function SampleLink({
  n,
  min,
  cohort,
  scope,
  label,
}: {
  n: number;
  min: number;
  cohort: CohortParams;
  /** The Research analysis mode ("asof" carries the point-in-time scope into the drill-down). */
  scope: SampleScope;
  /** Accessible label describing which cohort this chip drills into. */
  label: string;
}) {
  const asofHref = useAsOfHref();
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
