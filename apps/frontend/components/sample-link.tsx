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
 * It is a plain same-window `<Link>` (every link on this page stays same-window; only the SAMPLES ROW
 * ticker opens a new tab, J-52). Hover/focus underline the chip.
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
