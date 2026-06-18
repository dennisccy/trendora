"use client";

import { Suspense, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import {
  AlertTriangle,
  ArrowDown,
  ArrowLeft,
  ArrowUp,
  ArrowUpDown,
  Microscope,
  Search,
  ShieldAlert,
} from "lucide-react";

import { useAsOf, useAsOfHref } from "@/components/asof-provider";
import { EmptyState } from "@/components/empty-state";
import { fmtPct, returnClass } from "@/components/forward-return";
import { PageHeading } from "@/components/page-heading";
import { Card } from "@/components/ui/card";
import { TermInfo } from "@/components/ui/term-info";
import { fetchSamples, type SampleCohort, type SampleRow, type SamplesResponse } from "@/lib/api";
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
 * Reached from the `N=` chips (which open this page in a NEW tab — J-65). Same-window links everywhere
 * (incl. this page's own "Back to Research") EXCEPT each row's ticker, which opens the dated Stock Detail
 * (`/stocks/[ticker]?asof=<that row's snapshot date>`) in a NEW tab (J-52).
 *
 * J-64 — the table is client-side SORTABLE (every column) and ticker-FILTERABLE under the J-48 view-transform
 * contract: both are pure view transforms over the already-served `data.rows` (re-order / narrow the rendered
 * list only; recompute / re-rank / refetch nothing). The filter shows an honest "showing x of N observations"
 * while the published cohort total stays the served `total` — a filtered view never alters the cohort.
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

/** J-64 — the samples table's sortable columns. `served` is the sentinel default: the rows render in the
 *  exact backend-served order (no client re-order), and clicking the active column a third time clears the
 *  sort back to `served`. A `value:<key>` column key sorts by one qualifying-value column. */
type SortCol =
  | { kind: "served" }
  | { kind: "ticker" }
  | { kind: "date" }
  | { kind: "value"; key: string }
  | { kind: "forward_return" };
type SortDir = "asc" | "desc";

const SERVED_SORT: { col: SortCol; dir: SortDir } = { col: { kind: "served" }, dir: "asc" };

/** Two `SortCol`s are equal iff same kind (and same value key). Used to decide toggle-vs-switch and to
 *  light exactly ONE active header. */
function sameCol(a: SortCol, b: SortCol): boolean {
  if (a.kind !== b.kind) return false;
  if (a.kind === "value" && b.kind === "value") return a.key === b.key;
  return true;
}

/** A stable ascending comparator for a `SortCol` over the already-served rows. Pure view transform: it
 *  reads each row's stored value exactly as served and never recomputes anything. A null/absent value
 *  sorts LAST in ascending order (so missing data is consistently grouped, not silently treated as 0). */
function comparatorFor(col: SortCol): (a: SampleRow, b: SampleRow) => number {
  switch (col.kind) {
    case "ticker":
      return (a, b) => a.ticker.localeCompare(b.ticker);
    case "date":
      // ISO dates sort correctly as strings; a null snapshot date sorts last.
      return (a, b) => cmpNullableString(a.snapshot_date, b.snapshot_date);
    case "forward_return":
      return (a, b) => cmpNullableNumber(a.forward_return, b.forward_return);
    case "value": {
      const key = col.key;
      return (a, b) => {
        const av = a.values.find((v) => v.key === key)?.value;
        const bv = b.values.find((v) => v.key === key)?.value;
        // a value column is homogeneous across rows (numeric OR string); compare accordingly.
        if (typeof av === "number" || typeof bv === "number") {
          return cmpNullableNumber(
            typeof av === "number" ? av : null,
            typeof bv === "number" ? bv : null,
          );
        }
        return cmpNullableString(
          typeof av === "string" ? av : null,
          typeof bv === "string" ? bv : null,
        );
      };
    }
    case "served":
    default:
      return () => 0;
  }
}

/** Ascending compare where `null` sorts AFTER any present value (kept stable for ties by the caller). */
function cmpNullableNumber(a: number | null, b: number | null): number {
  if (a === null && b === null) return 0;
  if (a === null) return 1;
  if (b === null) return -1;
  return a - b;
}
function cmpNullableString(a: string | null, b: string | null): number {
  if (a === null && b === null) return 0;
  if (a === null) return 1;
  if (b === null) return -1;
  return a.localeCompare(b);
}

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
  // J-77 — the Regime × Setup × Pattern combination cohort.
  if (cohort.kind === "regime-setup-pattern") {
    const viewLabel = cohort.view === "pooled" ? "Pooled (per-signal-day)" : "Episodes (first-trigger)";
    const patternLabel = cohort.pattern === "none" ? "— (no pattern)" : (cohort.pattern ?? "").replace(/_/g, " ");
    return {
      title: "Regime × Setup × Pattern",
      detail: `${viewLabel} · ${cohort.regime} · ${cohort.setup} · ${patternLabel}`,
    };
  }
  // J-90 — the Recovery-Turn Edge cohort (the forward returns of causal recovery-turn dates).
  if (cohort.kind === "recovery-turn") {
    const viewLabel = cohort.view === "pooled" ? "Pooled (per-signal-day)" : "Episodes (first-trigger)";
    const sliceDetail = cohort.slice === "phase" ? `Phase at signal: ${cohort.phase}` : "All recovery-turn dates";
    return {
      title: "Recovery-Turn Edge",
      detail: `${viewLabel} · ${sliceDetail}`,
    };
  }
  // event-study
  const subject = cohort.subject?.label ?? "subject";
  // J-63: the overlap-honesty view this drill-down reproduces (Episodes = first-trigger; Pooled = per
  // signal-day). Shown so the operator can see which mode the listed rows belong to.
  const viewLabel = cohort.view === "pooled" ? "Pooled (per-signal-day)" : "Episodes (first-trigger)";
  if (cohort.slice === "regime") {
    return { title: `Setup & Pattern Lab — ${subject}`, detail: `${viewLabel} · Regime: ${cohort.regime}` };
  }
  if (cohort.slice === "sector") {
    return { title: `Setup & Pattern Lab — ${subject}`, detail: `${viewLabel} · Sector: ${cohort.sector}` };
  }
  return { title: `Setup & Pattern Lab — ${subject}`, detail: `${viewLabel} · All occurrences` };
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

/** The samples table: one row per observation. A VALID n=0 cohort renders an explicit honest empty state
 *  (never a fabricated row). Column headers carry TermInfo tooltips reading the shared J-47 glossary and —
 *  J-64 — are click-sortable; a ticker type-to-filter narrows the visible rows. Each row's ticker opens the
 *  dated Stock Detail in a NEW tab (J-52).
 *
 *  J-64 contract: BOTH the sort and the filter are pure client-side VIEW transforms over the already-served
 *  `data.rows` — they re-order / narrow the rendered list only and recompute, re-rank, and refetch nothing
 *  (every cell value reads exactly as served). The published cohort total (`samples-total`) stays the
 *  served `data.total` regardless of the filter; the filter only affects the honest "showing x of N
 *  observations" VIEW count. The transform layers filter THEN sort (both memoized) so they compose and a
 *  large cohort (the rank-IC pool serves ~20k rows) stays responsive. */
function SamplesTable({ data }: { data: SamplesResponse }) {
  // J-64 view state — the sort lives here (not in the URL): per OUT OF SCOPE, view state is NOT serialized,
  // so J-51 deep-link/reload behavior stays byte-unchanged. Default is the served order (no client sort).
  const [sortCol, setSortCol] = useState<SortCol>(SERVED_SORT.col);
  const [sortDir, setSortDir] = useState<SortDir>(SERVED_SORT.dir);
  // J-64 ticker type-to-filter — case-insensitive substring match on the ticker; no submit affordance.
  const [query, setQuery] = useState("");

  // the value column header label: for an event study it's the matched setup/pattern; otherwise the
  // qualifying factor value(s). The first row's values drive the column count (every row shares the shape).
  const valueColumns = data.rows[0]?.values ?? [];
  const isEventStudy = data.kind === "event-study";

  // J-64 — FILTER then SORT, each memoized (the iter-9 `/stocks` structure). Filter narrows the served
  // rows by ticker substring; sort re-orders the already-filtered rows with a stable tie-break that
  // preserves the SERVED order on ties (so equal keys stay in scanner/observation order and `served`
  // returns the list untouched).
  const trimmed = query.trim().toLowerCase();
  const filtered = useMemo(
    () => (trimmed ? data.rows.filter((r) => r.ticker.toLowerCase().includes(trimmed)) : data.rows),
    [data.rows, trimmed],
  );
  const visible = useMemo(() => {
    if (sortCol.kind === "served") return filtered;
    const cmp = comparatorFor(sortCol);
    const sign = sortDir === "asc" ? 1 : -1;
    return filtered
      .map((row, index) => ({ row, index }))
      .sort((a, b) => {
        const primary = cmp(a.row, b.row) * sign;
        // Stable tie-break: preserve the incoming (served / filtered) order on ties.
        return primary !== 0 ? primary : a.index - b.index;
      })
      .map((entry) => entry.row);
  }, [filtered, sortCol, sortDir]);

  // J-64 header click: a NEW column adopts ascending; clicking the ACTIVE column toggles asc⇄desc, and a
  // THIRD click clears the sort back to the served order (J-64 step 5 — "clear the sort → served order").
  const onSort = (col: SortCol) => {
    if (sameCol(col, sortCol)) {
      if (sortDir === "asc") {
        setSortDir("desc");
      } else {
        // third click on the active column: restore the served order.
        setSortCol(SERVED_SORT.col);
        setSortDir(SERVED_SORT.dir);
      }
      return;
    }
    setSortCol(col);
    setSortDir("asc");
  };

  // A VALID n=0 cohort (the cohort itself is empty) — the existing honest empty state, unchanged.
  if (data.total === 0) {
    return (
      <EmptyState
        icon={Microscope}
        title="This cohort has zero observations"
        description="No stored observation matches this exact cohort under the selected scope — an honest empty set, not a fabricated row. The published N for this slice is also 0."
      />
    );
  }

  const filterActive = trimmed.length > 0;

  return (
    <div className="space-y-3">
      {/* J-64 — the ticker type-to-filter + the honest view-count line. The cohort total is shown in the
          CohortSummary above (data-testid="samples-total") and is NOT touched by this filter; this line
          only describes the VIEW ("showing x of N observations"). */}
      <div className="flex flex-wrap items-center gap-3">
        <div className="relative">
          <Search
            className="pointer-events-none absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-text-faint"
            aria-hidden
          />
          <input
            type="search"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Filter by ticker…"
            aria-label="Filter observations by ticker"
            data-testid="samples-ticker-filter"
            className="h-9 w-52 rounded-md border border-border bg-surface-2 pl-8 pr-3 text-sm text-text placeholder:text-text-faint transition-colors hover:border-border-strong focus-visible:border-accent focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-accent"
          />
        </div>
        {filterActive ? (
          <span className="text-xs text-text-muted" data-testid="samples-view-count">
            Showing <span className="num font-semibold text-text">{visible.length}</span> of{" "}
            <span className="num font-semibold text-text">{data.total}</span> observations
          </span>
        ) : null}
      </div>

      {/* J-64 — an all-filtered-out result is a VIEW empty state (the cohort is NOT empty — that is the
          n=0 branch above). Honest, distinct copy; never a fabricated row. Clearing the filter restores
          every row. */}
      {filterActive && visible.length === 0 ? (
        <EmptyState
          icon={Search}
          title="No observations match this filter"
          description={`No ticker in this cohort matches "${query.trim()}". This is a view filter over the ${data.total} served observations — the cohort itself is unchanged. Clear the filter to see every row.`}
        />
      ) : (
        <Card className="p-0">
          <div className="overflow-x-auto">
            <table data-testid="samples-table" className="w-full border-collapse text-sm">
              <thead>
                <tr className="border-b border-border text-left text-xs uppercase tracking-wide text-text-faint">
                  <SortHeader
                    col={{ kind: "ticker" }}
                    label="Ticker"
                    activeCol={sortCol}
                    dir={sortDir}
                    onSort={onSort}
                  />
                  <SortHeader
                    col={{ kind: "date" }}
                    label="Snapshot date"
                    term="as-of date"
                    activeCol={sortCol}
                    dir={sortDir}
                    onSort={onSort}
                  />
                  {valueColumns.map((v) => (
                    <SortHeader
                      key={v.key}
                      col={{ kind: "value", key: v.key }}
                      label={isEventStudy ? "Matched" : v.label}
                      term={isEventStudy ? "setup status" : "factor"}
                      align="right"
                      activeCol={sortCol}
                      dir={sortDir}
                      onSort={onSort}
                    />
                  ))}
                  <SortHeader
                    col={{ kind: "forward_return" }}
                    label={`Forward return (${data.horizon}d)`}
                    term="forward return"
                    align="right"
                    activeCol={sortCol}
                    dir={sortDir}
                    onSort={onSort}
                  />
                </tr>
              </thead>
              <tbody>
                {visible.map((row, i) => (
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
      )}
    </div>
  );
}

/** J-64 — a sortable column header (the proven `/stocks` `SortHeader` structure). Renders a sort `<button>`
 *  and, when `term` is given, a `TermInfo` definition trigger as a SIBLING beside it — NEVER nested inside
 *  the sort button (valid DOM; the iter-5 nested-interactive-element lesson). The sort indicator
 *  (`data-testid="sort-indicator"`) renders ONLY on the active column, so exactly ONE is visible at a time;
 *  inactive columns show a faint neutral glyph on hover as the affordance. */
function SortHeader({
  col,
  label,
  term,
  align = "left",
  activeCol,
  dir,
  onSort,
}: {
  col: SortCol;
  label: string;
  /** Optional glossary term — renders a definition info affordance BESIDE the sort button (a sibling). */
  term?: string;
  align?: "left" | "right";
  activeCol: SortCol;
  dir: SortDir;
  onSort: (col: SortCol) => void;
}) {
  const active = sameCol(col, activeCol);
  const ariaSort: "ascending" | "descending" | "none" = active
    ? dir === "asc"
      ? "ascending"
      : "descending"
    : "none";
  return (
    <th
      className={cn("px-4 py-2 font-medium", align === "right" && "text-right")}
      aria-sort={ariaSort}
    >
      {/* The sort control and the term-definition affordance are SIBLINGS — the info trigger lives OUTSIDE
          the sort <button> so no interactive element is nested in another (valid DOM; iter-5 fix). */}
      <span className={cn("inline-flex items-center gap-1", align === "right" && "justify-end")}>
        <button
          type="button"
          onClick={() => onSort(col)}
          aria-label={`Sort by ${label}${active ? (dir === "asc" ? ", ascending" : ", descending") : ""}`}
          className="group inline-flex items-center gap-1 rounded-sm uppercase tracking-wide transition-colors hover:text-text focus-visible:text-text focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-accent"
        >
          <span className={cn(active && "text-text")}>{label}</span>
          {active ? (
            dir === "asc" ? (
              <ArrowUp className="h-3 w-3 text-accent" aria-hidden data-testid="sort-indicator" />
            ) : (
              <ArrowDown className="h-3 w-3 text-accent" aria-hidden data-testid="sort-indicator" />
            )
          ) : (
            <ArrowUpDown
              className="h-3 w-3 text-text-faint/40 opacity-0 transition-opacity group-hover:opacity-100"
              aria-hidden
            />
          )}
        </button>
        {term ? <TermInfo term={term} /> : null}
      </span>
    </th>
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
