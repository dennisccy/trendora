"use client";

import { Suspense, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { AlertTriangle, ArrowLeft, Microscope, ShieldAlert } from "lucide-react";

import { useAsOf, useAsOfHref } from "@/components/asof-provider";
import { EmptyState } from "@/components/empty-state";
import { fmtPct, returnClass } from "@/components/forward-return";
import { PageHeading } from "@/components/page-heading";
import { Card } from "@/components/ui/card";
import { TermInfo } from "@/components/ui/term-info";
import { fetchSamples, type SampleCohort, type SamplesResponse } from "@/lib/api";
import { formatIsoDate } from "@/lib/dates";
import { samplesFetchParams } from "@/lib/samples-link";
import { cn } from "@/lib/utils";

/**
 * Research Samples drill-down (iter-7 goal-mode, J-51 / J-52). The read-only page behind every published
 * `N=` figure on `/research`: it reproduces the exact cohort from its URL params and lists the member
 * observations (ticker, snapshot date, qualifying stored value(s), realized forward return). The displayed
 * `total` EQUALS the published N it was reached from (the backend guarantees count-coherence). Deep-linkable
 * + reload-safe (the params fully reproduce the cohort). Re-formats stored values only — recomputes nothing.
 *
 * Reached from the `N=` chips (not a top-nav tab). Same-window links everywhere EXCEPT each row's ticker,
 * which opens the dated Stock Detail (`/stocks/[ticker]?asof=<that row's snapshot date>`) in a NEW tab (J-52).
 */
export default function ResearchSamplesPage() {
  // useSearchParams() requires a Suspense boundary in the App Router.
  return (
    <Suspense fallback={<SamplesSkeleton />}>
      <SamplesView />
    </Suspense>
  );
}

type State =
  | { kind: "loading" }
  | { kind: "ok"; data: SamplesResponse }
  | { kind: "error"; status: "invalid" | "unavailable" };

function SamplesView() {
  const searchParams = useSearchParams();
  const { asOf } = useAsOf();
  const [state, setState] = useState<State>({ kind: "loading" });

  // the drill-down's as-of SCOPE is a cohort param (`scope=asof` → pool only snapshots ≤ the global date).
  // The global as-of DATE itself comes from the one global control (`asOf`), not a second date state.
  const scope = searchParams.get("scope");
  const asofCutoff = scope === "asof" ? asOf ?? undefined : undefined;

  // the backend selectors (drop the frontend-only `scope`/`asof`); stable key so the effect re-fetches on
  // any deep-link change (reload-safe). Repeated `condition` params are preserved.
  const fetchParams = useMemo(
    () => samplesFetchParams(new URLSearchParams(searchParams.toString())),
    [searchParams],
  );

  useEffect(() => {
    const controller = new AbortController();
    setState({ kind: "loading" });
    fetchSamples(fetchParams, asofCutoff, controller.signal)
      .then((data) => setState({ kind: "ok", data }))
      .catch((err: Error) => {
        if (controller.signal.aborted) return;
        // a 422 (invalid/unknown cohort selector) is a distinct, honest "this drill-down doesn't exist"
        // state vs a transient backend outage — surfaced separately, never a fabricated table.
        const invalid = /HTTP 4\d\d/.test(err.message);
        setState({ kind: "error", status: invalid ? "invalid" : "unavailable" });
      });
    return () => controller.abort();
  }, [fetchParams, asofCutoff]);

  const data = state.kind === "ok" ? state.data : null;

  return (
    <div className="space-y-4">
      <div className="space-y-2">
        <BackToResearch />
        <PageHeading
          title="Research Samples — observation drill-down"
          subtitle="Every member observation behind a published research sample count — ticker, snapshot date, the qualifying stored value(s), and the realized forward return. The total below equals the N you clicked; nothing is recomputed."
        />
        {data ? <CohortSummary cohort={data.cohort} asofDate={data.asof_date} total={data.total} /> : null}
      </div>

      {data ? (
        <CaveatBanner survivorship={data.survivorship_bias} descriptive={data.descriptive_caveat} />
      ) : null}

      {state.kind === "loading" ? <SamplesSkeleton /> : null}

      {state.kind === "error" ? (
        <Card className="flex items-center gap-3 border-neg bg-surface p-5 text-sm text-neg">
          <AlertTriangle className="h-5 w-5 shrink-0" aria-hidden />
          <div>
            <p className="font-medium">
              {state.status === "invalid"
                ? "Unknown sample cohort"
                : "Backend unavailable"}
            </p>
            <p className="text-text-muted">
              {state.status === "invalid"
                ? "This drill-down link does not describe a valid research cohort. Return to Research and click an N= figure to open its samples."
                : "The samples could not load from the API. No rows are shown rather than fabricated values — confirm the backend is running and retry."}
            </p>
          </div>
        </Card>
      ) : null}

      {data ? <SamplesTable data={data} /> : null}
    </div>
  );
}

/** A same-window link back to the Research labs (carries the global `?asof` via the J-50 helper). */
function BackToResearch() {
  const asofHref = useAsOfHref();
  return (
    <Link
      href={asofHref("/research")}
      className="inline-flex items-center gap-1 text-xs font-medium text-text-muted hover:text-accent focus-visible:text-accent focus-visible:outline-none"
    >
      <ArrowLeft className="h-3.5 w-3.5" aria-hidden /> Back to Research
    </Link>
  );
}

/** The resolved cohort description (re-formats the echoed cohort params): which lab, which slice, the
 *  horizon, the as-of scope, and the cohort total (== the published N). No value is recomputed. */
function CohortSummary({
  cohort,
  asofDate,
  total,
}: {
  cohort: SampleCohort;
  asofDate: string | null;
  total: number;
}) {
  const parts = describeCohort(cohort);
  return (
    <div className="flex flex-wrap items-center gap-x-6 gap-y-1 text-xs text-text-muted" data-testid="cohort-summary">
      <span>
        <span className="text-text-faint">Cohort: </span>
        <span className="text-text">{parts.title}</span>
      </span>
      {parts.detail ? (
        <span>
          <span className="text-text-faint">Slice: </span>
          <span className="text-text">{parts.detail}</span>
        </span>
      ) : null}
      <span>
        <span className="text-text-faint">Horizon: </span>
        <span className="num text-text">{cohort.horizon}d</span>
      </span>
      <span>
        <span className="text-text-faint">Scope: </span>
        <span className="text-text">
          {asofDate ? `As of ≤ ${formatIsoDate(asofDate)} (point-in-time)` : "All history"}
        </span>
      </span>
      <span>
        <span className="text-text-faint">Total observations: </span>
        <span className="num font-semibold text-text" data-testid="samples-total">{total}</span>
      </span>
    </div>
  );
}

/** Re-format the echoed cohort into a plain-language title + slice detail (presentation only). */
function describeCohort(cohort: SampleCohort): { title: string; detail: string | null } {
  if (cohort.kind === "factor") {
    const factor = cohort.factor?.label ?? "factor";
    if (cohort.slice === "decile") {
      return { title: `Factor Lab — ${factor}`, detail: `Decile D${cohort.decile} of ${cohort.deciles_count ?? ""}` };
    }
    if (cohort.slice === "regime") {
      return { title: `Factor Lab — ${factor}`, detail: `Regime: ${cohort.regime}` };
    }
    return { title: `Factor Lab — ${factor}`, detail: "All observations (rank-IC pool)" };
  }
  if (cohort.kind === "combination") {
    const conds = (cohort.conditions ?? [])
      .map((c) => `${c.factor.label} · ${c.side} ${c.quantile.label}`)
      .join(" + ");
    const labelByCohort: Record<string, string> = {
      baseline: "Baseline (all names)",
      single: cohort.single_index !== null && cohort.single_index !== undefined
        ? (cohort.conditions?.[cohort.single_index]
            ? `Single: ${cohort.conditions[cohort.single_index].factor.label} · ${cohort.conditions[cohort.single_index].side} ${cohort.conditions[cohort.single_index].quantile.label}`
            : "Single condition")
        : "Single condition",
      composite: "Combined (composite rank-blend)",
      strict_overlap: "Strict overlap (AND)",
    };
    return {
      title: `Combination Lab — ${labelByCohort[cohort.cohort ?? "baseline"] ?? cohort.cohort}`,
      detail: conds || null,
    };
  }
  // event-study
  const subject = cohort.subject?.label ?? "subject";
  if (cohort.slice === "regime") return { title: `Setup & Pattern Lab — ${subject}`, detail: `Regime: ${cohort.regime}` };
  if (cohort.slice === "sector") return { title: `Setup & Pattern Lab — ${subject}`, detail: `Sector: ${cohort.sector}` };
  return { title: `Setup & Pattern Lab — ${subject}`, detail: "All occurrences (pooled)" };
}

function CaveatBanner({ survivorship, descriptive }: { survivorship: string; descriptive: string }) {
  return (
    <Card className="flex items-start gap-3 border-warn bg-surface p-4 text-sm">
      <ShieldAlert className="mt-0.5 h-5 w-5 shrink-0 text-warn" aria-hidden />
      <div className="space-y-1">
        <p className="font-medium text-warn">Survivorship bias · universe-relative · descriptive</p>
        <p className="text-text-muted">{survivorship}</p>
        <p className="text-text-muted">{descriptive}</p>
      </div>
    </Card>
  );
}

/** The samples table: one row per observation. n=0 renders an explicit honest empty state (never a
 *  fabricated row). Column headers carry TermInfo tooltips reading the shared J-47 glossary. Each row's
 *  ticker opens the dated Stock Detail in a NEW tab (J-52). */
function SamplesTable({ data }: { data: SamplesResponse }) {
  if (data.total === 0) {
    return (
      <EmptyState
        icon={Microscope}
        title="This cohort has zero observations"
        description="No stored observation matches this exact cohort under the selected scope — an honest empty set, not a fabricated row. The published N for this slice is also 0."
      />
    );
  }
  // the value column header label: for an event study it's the matched setup/pattern; otherwise the
  // qualifying factor value(s). The first row's values drive the column count (every row shares the shape).
  const valueColumns = data.rows[0]?.values ?? [];
  const isEventStudy = data.kind === "event-study";

  return (
    <Card className="p-0">
      <div className="overflow-x-auto">
        <table data-testid="samples-table" className="w-full border-collapse text-sm">
          <thead>
            <tr className="border-b border-border text-left text-xs uppercase tracking-wide text-text-faint">
              <th className="px-4 py-2 font-medium">Ticker</th>
              <th className="px-4 py-2 font-medium">
                <span className="inline-flex items-center gap-1">Snapshot date<TermInfo term="as-of date" /></span>
              </th>
              {valueColumns.map((v) => (
                <th key={v.key} className="px-4 py-2 text-right font-medium">
                  <span className="inline-flex items-center justify-end gap-1">
                    {isEventStudy ? "Matched" : v.label}
                    <TermInfo term={isEventStudy ? "setup status" : "factor"} />
                  </span>
                </th>
              ))}
              <th className="px-4 py-2 text-right font-medium">
                <span className="inline-flex items-center justify-end gap-1">
                  Forward return ({data.horizon}d)<TermInfo term="forward return" />
                </span>
              </th>
            </tr>
          </thead>
          <tbody>
            {data.rows.map((row, i) => (
              <tr key={`${row.ticker}-${row.snapshot_date}-${i}`} className="border-b border-border last:border-b-0">
                <td className="px-4 py-2">
                  <TickerLink ticker={row.ticker} snapshotDate={row.snapshot_date} />
                </td>
                <td className="num px-4 py-2 text-text-muted">{formatIsoDate(row.snapshot_date)}</td>
                {row.values.map((v) => (
                  <td key={v.key} className="num px-4 py-2 text-right text-text">
                    {typeof v.value === "number" ? v.value.toFixed(2) : v.value}
                  </td>
                ))}
                <td className="px-4 py-2 text-right">
                  <span className={cn("num font-semibold", returnClass(row.forward_return))}>
                    {fmtPct(row.forward_return)}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Card>
  );
}

/** J-52 — the row ticker opens `/stocks/[ticker]?asof=<that row's snapshot date>` in a NEW tab. The asof
 *  param is the ROW's snapshot date (NOT the page's global as-of) — so the new tab restores exactly the
 *  date that observation came from, through the one global control (J-43). `rel` carries new-tab safety. */
function TickerLink({ ticker, snapshotDate }: { ticker: string; snapshotDate: string | null }) {
  // build the href directly from the ROW's date (not the page's global as-of). The global as-of is NOT
  // merged here — this link intentionally carries the observation's OWN date.
  const href = snapshotDate
    ? `/stocks/${ticker}?asof=${encodeURIComponent(snapshotDate)}`
    : `/stocks/${ticker}`;
  return (
    <Link
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      data-testid="samples-ticker-link"
      className="num font-semibold text-accent hover:underline focus-visible:underline focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-accent"
    >
      {ticker}
    </Link>
  );
}

function SamplesSkeleton() {
  return (
    <Card className="space-y-2 p-4">
      {Array.from({ length: 8 }).map((_, i) => (
        <div key={i} className="h-7 w-full animate-pulse rounded bg-surface-2" />
      ))}
    </Card>
  );
}
