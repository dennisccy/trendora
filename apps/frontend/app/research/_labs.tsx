"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import {
  AlertTriangle,
  ArrowDown,
  ArrowUp,
  ArrowUpDown,
  ChevronDown,
  ChevronRight,
  Microscope,
  Plus,
  ShieldAlert,
  X,
} from "lucide-react";

import { useAsOf, useAsOfHref } from "@/components/asof-provider";
import { EmptyState } from "@/components/empty-state";
import { fmtMdd, fmtPct, mddClass, returnClass } from "@/components/forward-return";
import { PageHeading } from "@/components/page-heading";
import { useReadiness } from "@/components/readiness-provider";
import { shouldShowWarming, WarmingState } from "@/components/warming-state";
import { Card } from "@/components/ui/card";
import { Select } from "@/components/ui/select";
import { TermInfo } from "@/components/ui/term-info";
import { SampleLink } from "@/components/sample-link";
import { groupedHorizonColumns, horizonColumnKey } from "@/lib/research-lab-columns";
import { type CohortParams, type SampleScope } from "@/lib/samples-link";
import { cn } from "@/lib/utils";
import {
  fetchDowntrendOpportunity,
  fetchEventStudy,
  fetchFactorCombination,
  fetchFactorLabAll,
  fetchPhaseSeverityLab,
  fetchRecoveryTurnEdge,
  fetchRegimeLab,
  fetchRegimePhaseFactor,
  fetchRegimeSetupPattern,
  type CohortStats,
  type DowntrendOpportunityResponse,
  type DowntrendOpportunityRow,
  type EventStudyHorizonRow,
  type EventStudyRegimeRow,
  type EventStudyResponse,
  type EventStudySectorRow,
  type FactorCombinationCondition,
  type FactorCombinationResponse,
  type FactorDecileRow,
  type FactorHorizonDeciles,
  type FactorLabAllResponse,
  type FactorTableRow,
  type PhaseSeverityLabDecileRow,
  type PhaseSeverityLabLabelRow,
  type PhaseSeverityLabResponse,
  type RecoveryTurnEdgeHorizonRow,
  type RecoveryTurnEdgePhaseRow,
  type RecoveryTurnEdgeResponse,
  type RegimeLabDecileHorizonCell,
  type RegimeLabDecileRow,
  type RegimeLabHorizonCell,
  type RegimeLabLabelRow,
  type RegimeLabResponse,
  type RegimePhaseFactorResponse,
  type RegimePhaseFactorRow,
  type RegimeSetupPatternResponse,
  type RegimeSetupPatternRow,
} from "@/lib/api";

type State =
  | { kind: "loading" }
  | { kind: "ok"; data: FactorLabAllResponse }
  | { kind: "error" };

/** Format a unitless ratio (the downside risk-adjusted column / the rank-IC) with sign + 2 decimals;
 *  null/NA renders an em dash. This is NOT a percent — `fmtPct` would be wrong for a ratio. */
function fmtRatio(value: number | null): string {
  if (value === null || value === undefined) return "—";
  return `${value >= 0 ? "+" : ""}${value.toFixed(2)}`;
}

/** iter-45 (J-104) — the config-driven horizon vocabulary a lab reports up to its route's shared horizon
 *  selector (so the selector stays config-driven without the route fetching the lab's payload itself). */
export interface LabMeta {
  horizons: number[];
  default_horizon: number;
}

/** iter-45 (J-104) — the SHARED research controls hook. Every `/research/*` lab route reads the SAME
 *  analysis mode (All-history ⇄ As-of), the SAME single global as-of, and the SAME readiness — so the
 *  point-in-time scope + the warming state are consistent across the relocated labs (no second date state,
 *  J-18 preserved). `horizon` is per-route local (each lab owns its horizon selector) but defaults to the
 *  backend's config default. Returns the resolved `asofCutoff` (the single global as-of in As-of mode, null
 *  in All-history mode — the only date the labs ever transmit). */
export function useResearchControls() {
  const [mode, setMode] = useState<"all" | "asof">("all");
  const { asOf } = useAsOf();
  const { state: readiness } = useReadiness();
  // ONE resolved cutoff (J-32): As-of mode reads the global `asOf`; All-history mode ignores it (null). At
  // the latest date `asOf` is already null → As-of@latest == all-history (J-09). Sending `?as_of=` is the
  // single global date transmitted on a snapshot-served read (like /api/stocks?as_of=), NOT a second date
  // state (J-18).
  const asofCutoff = mode === "asof" ? asOf : null;
  return { mode, setMode, asOf, readiness, asofCutoff, scope: mode as SampleScope };
}

/** The shared controls bar every lab route renders: the page heading + the analysis-mode toggle + an
 *  optional extra control (a horizon/subject/view selector the lab supplies) + the mode-context line.
 *  Single source for the lab shell so the relocated labs stay visually indistinguishable from before. */
export function ResearchControls({
  title,
  subtitle,
  mode,
  onModeChange,
  asofCutoff,
  controls,
}: {
  title: string;
  subtitle: string;
  mode: "all" | "asof";
  onModeChange: (mode: "all" | "asof") => void;
  asofCutoff: string | null;
  controls?: React.ReactNode;
}) {
  return (
    <div className="space-y-2">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <PageHeading title={title} subtitle={subtitle} />
        <div className="flex flex-wrap items-end gap-3">
          <AnalysisModeToggle mode={mode} onChange={onModeChange} />
          {controls}
        </div>
      </div>
      <ModeContext mode={mode} asofCutoff={asofCutoff} />
    </div>
  );
}

/** The shared survivorship/descriptive caveat banner every lab route renders (single source of the copy). */
export function ResearchCaveat({
  survivorship,
  descriptive,
}: {
  survivorship?: string;
  descriptive?: string;
}) {
  return (
    <CaveatBanner
      survivorship={
        survivorship ??
        "Walk-forward evidence carries survivorship bias (current-membership universe) — results may be overstated."
      }
      descriptive={
        descriptive ??
        "Descriptive evidence, not a predictive model — read these as historical association on a universe-relative seed."
      }
    />
  );
}

/** The shared "backend unavailable" card every lab route renders on a fetch error (single source). */
export function ResearchError({ what }: { what: string }) {
  return (
    <Card className="flex items-center gap-3 border-neg bg-surface p-5 text-sm text-neg">
      <AlertTriangle className="h-5 w-5 shrink-0" aria-hidden />
      <div>
        <p className="font-medium">Backend unavailable</p>
        <p className="text-text-muted">
          {what} could not load from the API. No figures are shown rather than fabricated values. Confirm
          the backend is running and retry.
        </p>
      </div>
    </Card>
  );
}

/** iter-52 (J-109) — the Factor Lab on its OWN route (`/research/factor-lab`). The page fires the
 *  ALL-FACTORS fetch (`?all=true`) and renders the sortable, expandable all-factors table showing EVERY
 *  config horizon at once as paired (forward-return, max-drawdown) columns — the top-decile edge and its
 *  downside per horizon — each row click-to-expand to its full D1…D10 decile grid (the same all-horizon
 *  paired columns). The horizon `<select>` is GONE (all horizons shown); the rank-IC / downside
 *  risk-adjusted figures are fixed at the config default horizon. The As-of mode toggle REMAINS (the single
 *  global as-of — no second date state). Every figure is byte-identical to the single-horizon view
 *  (re-presented per horizon, never recomputed). */
export function FactorLabPage() {
  const [state, setState] = useState<State>({ kind: "loading" });
  const { mode, setMode, readiness, asofCutoff, scope } = useResearchControls();

  useEffect(() => {
    const controller = new AbortController();
    setState({ kind: "loading" });
    fetchFactorLabAll(asofCutoff ?? undefined, controller.signal)
      .then((data) => setState({ kind: "ok", data }))
      .catch(() => {
        if (!controller.signal.aborted) setState({ kind: "error" });
      });
    return () => controller.abort();
  }, [asofCutoff, readiness]);

  const data = state.kind === "ok" ? state.data : null;

  return (
    <div className="space-y-4">
      <ResearchControls
        title="Research — Factor Lab"
        subtitle="Which factors actually sort future returns — and at what downside? Every catalog factor's top-decile forward-return edge AND its paired max-drawdown across all horizons at once, sortable, and expandable in place to its full decile grid. Rank-IC + downside risk-adjusted at the default horizon. Derived once from the stored forward-tested evidence; descriptive, not predictive."
        mode={mode}
        onModeChange={setMode}
        asofCutoff={asofCutoff}
      />
      <ResearchCaveat survivorship={data?.survivorship_bias} descriptive={data?.descriptive_caveat} />
      {shouldShowWarming(readiness) ? (
        <WarmingState what="The Factor Lab" />
      ) : (
        <>
          {state.kind === "loading" ? <LabSkeleton /> : null}
          {state.kind === "error" ? <ResearchError what="The Factor-Lab evidence" /> : null}
          {data ? <FactorsTable data={data} scope={scope} /> : null}
        </>
      )}
    </div>
  );
}

/** The analysis-mode toggle (J-32): a segmented "All history" ⟷ "As of date" button group (styled like
 *  `HorizonSelector`/`SideToggle`, clicked directly — not a `<select>`). It is a MODE, not a date control:
 *  "As of date" reads the SINGLE global top-bar as-of switcher (no second date state — J-18). Default is
 *  "All history" (the cross-date aggregate). */
function AnalysisModeToggle({
  mode,
  onChange,
}: {
  mode: "all" | "asof";
  onChange: (mode: "all" | "asof") => void;
}) {
  const options: { key: "all" | "asof"; label: string }[] = [
    { key: "all", label: "All history" },
    { key: "asof", label: "As of date" },
  ];
  return (
    <div className="flex flex-col gap-1">
      <span className="text-xs uppercase tracking-wide text-text-faint">Analysis mode</span>
      <div
        role="group"
        aria-label="Analysis mode (all-history or as-of-date)"
        data-testid="analysis-mode-toggle"
        className="inline-flex h-9 overflow-hidden rounded-md border border-border bg-surface-2"
      >
        {options.map((o) => {
          const active = o.key === mode;
          return (
            <button
              key={o.key}
              type="button"
              aria-pressed={active}
              data-testid={`analysis-mode-${o.key}`}
              onClick={() => onChange(o.key)}
              className={cn(
                "border-r border-border px-3 text-sm transition-colors last:border-r-0",
                "focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-accent",
                active
                  ? "bg-accent font-semibold text-bg"
                  : "text-text-muted hover:bg-surface hover:text-text",
              )}
            >
              {o.label}
            </button>
          );
        })}
      </div>
    </div>
  );
}

/** The mode context line (J-32): shows the current pooling scope inline — every snapshot (all history),
 *  or only snapshots dated ≤ the resolved as-of date (point-in-time). The resolved as-of date is read
 *  from the single global switcher (`asofCutoff`); in As-of mode at the latest date the cutoff is null,
 *  which equals all history (J-09). Re-formats the resolved cutoff only — no recompute. */
function ModeContext({ mode, asofCutoff }: { mode: "all" | "asof"; asofCutoff: string | null }) {
  return (
    <p className="text-xs text-text-faint" data-testid="analysis-mode-context">
      {mode === "all" ? (
        <>
          Pooling <span className="text-text-muted">every snapshot</span> — all history (the default
          cross-date aggregate).
        </>
      ) : asofCutoff ? (
        <>
          Point-in-time: pooling{" "}
          <span className="text-accent">only snapshots dated ≤ {asofCutoff}</span> (a walk-forward view —
          smaller n, honest NA at early dates), driven by the single global as-of switcher.
        </>
      ) : (
        <>
          As of the <span className="text-text-muted">latest date</span> — equals all history. Pick an
          earlier date in the top-bar as-of switcher to restrict the window.
        </>
      )}
    </p>
  );
}

/** Present a family key as a heading (capitalised first letter) — purely presentational. Re-used by the
 *  all-factors table's Family column (J-107); no hard-coded family list in the frontend. */
function familyLabel(family: string): string {
  return family.charAt(0).toUpperCase() + family.slice(1);
}

export function HorizonSelector({
  horizons,
  value,
  onChange,
}: {
  horizons: number[];
  value: number | undefined;
  onChange: (h: number) => void;
}) {
  return (
    <div className="flex flex-col gap-1">
      <span className="text-xs uppercase tracking-wide text-text-faint">Horizon</span>
      <div
        role="group"
        aria-label="Forward-return horizon (trading days)"
        data-testid="horizon-select"
        className="inline-flex h-9 overflow-hidden rounded-md border border-border bg-surface-2"
      >
        {horizons.length === 0 ? (
          <span className="px-3 py-1.5 text-sm text-text-faint">—</span>
        ) : null}
        {horizons.map((h) => {
          const active = h === value;
          return (
            <button
              key={h}
              type="button"
              aria-pressed={active}
              onClick={() => onChange(h)}
              className={cn(
                "num border-r border-border px-3 text-sm transition-colors last:border-r-0",
                "focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-accent",
                active
                  ? "bg-accent font-semibold text-bg"
                  : "text-text-muted hover:bg-surface hover:text-text",
              )}
            >
              {h}d
            </button>
          );
        })}
      </div>
    </div>
  );
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

// --- All-factors, all-horizons table (J-107 → J-109) ---------------------------------------------
/** The sortable columns of the all-factors table. `label`/`family` are string sorts; `rank_ic`/`n`/
 *  `risk_adjusted` are numeric (NA-last) at the default horizon; `fwd:${h}` / `mdd:${h}` are the per-horizon
 *  top-decile forward-return / max-drawdown numeric columns (NA-last). A pure VIEW transform — the sort
 *  re-orders the served rows only, it recomputes / refetches nothing (J-48). */
type FactorStaticSortKey = "label" | "family" | "rank_ic" | "n" | "risk_adjusted";
type FactorSortKey = FactorStaticSortKey | `fwd:${number}` | `mdd:${number}`;
type FactorSortDir = "asc" | "desc";

/** The default sort: strongest predictive edge first (rank-IC descending, NA-last). */
const FACTOR_DEFAULT_SORT: { key: FactorSortKey; dir: FactorSortDir } = { key: "rank_ic", dir: "desc" };

/** Parse a per-horizon sort key (`fwd:20` / `mdd:5`) into its metric + horizon, or null for a static key. */
function parseHorizonSortKey(key: FactorSortKey): { metric: "fwd" | "mdd"; horizon: number } | null {
  const m = /^(fwd|mdd):(\d+)$/.exec(key);
  return m ? { metric: m[1] as "fwd" | "mdd", horizon: Number(m[2]) } : null;
}

/** A factor's decile table at one horizon (or undefined if the horizon is absent — never expected). */
function horizonBlock(row: FactorTableRow, h: number): FactorHorizonDeciles | undefined {
  return row.by_horizon.find((b) => b.horizon === h);
}

/** A factor's top (highest-factor-value) decile at horizon `h` — the source of the top-decile paired cells. */
function topDecileAt(row: FactorTableRow, h: number): FactorDecileRow | undefined {
  const block = horizonBlock(row, h);
  return block && block.deciles.length > 0 ? block.deciles[block.deciles.length - 1] : undefined;
}

/** Whether a top-decile cell at horizon `h` renders NA (the SAME `low_sample || n===0 || value===null` rule
 *  the decile cells use) — for the forward-return (`fwd`) or max-drawdown (`mdd`) metric. */
function topCellIsNa(row: FactorTableRow, h: number, metric: "fwd" | "mdd"): boolean {
  const top = topDecileAt(row, h);
  if (!top || top.low_sample || top.n === 0) return true;
  return metric === "fwd" ? top.mean_return === null : top.mean_max_drawdown === null;
}

/** The NA predicate for a numeric sort column — mirrors the cell render so the sort NA-set == the visual
 *  NA-set: rank-IC is NA when its value is null; the risk-adjusted column is NA when the default-horizon top
 *  decile is low-sample / empty / its value is null; the per-horizon `fwd:`/`mdd:` columns mirror their
 *  top-decile cell; `n` is always a real number (0 is a value, not NA). */
function factorCellIsNa(row: FactorTableRow, key: FactorSortKey, defaultHorizon: number): boolean {
  if (key === "rank_ic") return row.rank_ic.value === null;
  if (key === "risk_adjusted") return topCellIsNa(row, defaultHorizon, "fwd") || row.risk_adjusted === null;
  const hk = parseHorizonSortKey(key);
  if (hk) return topCellIsNa(row, hk.horizon, hk.metric);
  return false;
}

/** The numeric sort value for a numeric column (NA rows are pushed last by the comparator regardless). */
function factorCellValue(row: FactorTableRow, key: FactorSortKey): number {
  if (key === "rank_ic") return row.rank_ic.value ?? 0;
  if (key === "risk_adjusted") return row.risk_adjusted ?? 0;
  if (key === "n") return row.rank_ic.n;
  const hk = parseHorizonSortKey(key);
  if (hk) {
    const top = topDecileAt(row, hk.horizon);
    if (!top) return 0;
    return (hk.metric === "fwd" ? top.mean_return : top.mean_max_drawdown) ?? 0;
  }
  return 0;
}

/** J-107 / J-48 — a sortable column header (mirrors the /sectors + /stocks SortHeader pattern). The
 *  button is resolved in tests by its `aria-label` (the visible label lives in a nested span). */
function FactorSortHeader({
  col,
  label,
  activeKey,
  dir,
  onSort,
  numeric,
}: {
  col: FactorSortKey;
  label: string;
  activeKey: FactorSortKey;
  dir: FactorSortDir;
  onSort: (key: FactorSortKey) => void;
  numeric?: boolean;
}) {
  const active = activeKey === col;
  const ariaSort: "ascending" | "descending" | "none" = active
    ? dir === "asc"
      ? "ascending"
      : "descending"
    : "none";
  return (
    <th className={cn("px-4 py-2 font-medium", numeric && "text-right")} aria-sort={ariaSort}>
      <button
        type="button"
        onClick={() => onSort(col)}
        aria-label={`Sort by ${label}${active ? (dir === "asc" ? ", ascending" : ", descending") : ""}`}
        className={cn(
          "group inline-flex items-center gap-1 rounded-sm uppercase tracking-wide transition-colors hover:text-text focus-visible:text-text focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-accent",
          numeric && "justify-end",
        )}
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
    </th>
  );
}

/** A colour-graded ratio cell (rank-IC / risk-adjusted): explicit muted "NA" when the value is NA — never
 *  a fabricated number — otherwise the sign-graded ratio. */
function RatioCell({ value, na, title }: { value: number | null; na: boolean; title?: string }) {
  if (na || value === null) {
    return (
      <span className="num font-semibold text-text-muted" title={title ?? "NA — low sample or no value, not a fabricated number"}>
        NA
      </span>
    );
  }
  return <span className={cn("num font-semibold", returnClass(value))}>{fmtRatio(value)}</span>;
}

/** The all-factors, all-horizons comparison table (J-107 → J-109): one row per config-catalog factor —
 *  family + rank-IC value+N + downside risk-adjusted (ALL at the fixed default horizon), then for EVERY
 *  config horizon a paired (top-decile forward-return, top-decile max-drawdown) column. Client-side sortable
 *  NA-last on every numeric column (incl. each per-horizon `fwd:`/`mdd:` column); each row click-to-expand to
 *  reveal that factor's full D1…D`deciles` decile grid across all horizons (`DecileTable`, hidden by
 *  default). Every value is the canonical `compute_factor_lab` output re-presented per horizon
 *  (byte-identical) — the page recomputes nothing; the sort + expand are pure view transforms. */
function FactorsTable({ data, scope }: { data: FactorLabAllResponse; scope: SampleScope }) {
  const [expanded, setExpanded] = useState<Set<string>>(new Set());
  const [sortKey, setSortKey] = useState<FactorSortKey>(FACTOR_DEFAULT_SORT.key);
  const [sortDir, setSortDir] = useState<FactorSortDir>(FACTOR_DEFAULT_SORT.dir);

  const rows = data.factors_table;
  const horizons = data.horizons;
  const defaultHorizon = data.default_horizon;

  // J-109 / J-48 — the sorted view: a STABLE sort (catalog-order tie-break) over the served rows, NA-last
  // for the numeric columns. Recomputes no value; re-orders only.
  const sorted = useMemo(() => {
    const sign = sortDir === "asc" ? 1 : -1;
    return rows
      .map((row, i) => ({ row, i }))
      .sort((a, b) => {
        let c = 0;
        if (sortKey === "label" || sortKey === "family") {
          c = a.row[sortKey].localeCompare(b.row[sortKey]) * sign;
        } else {
          const ana = factorCellIsNa(a.row, sortKey, defaultHorizon);
          const bna = factorCellIsNa(b.row, sortKey, defaultHorizon);
          if (ana && bna) c = 0;
          else if (ana) return 1; // NA last regardless of direction
          else if (bna) return -1;
          else c = (factorCellValue(a.row, sortKey) - factorCellValue(b.row, sortKey)) * sign;
        }
        return c !== 0 ? c : a.i - b.i; // stable tie-break by catalog order
      })
      .map((x) => x.row);
  }, [rows, sortKey, sortDir, defaultHorizon]);

  const onSort = (key: FactorSortKey) => {
    if (key === sortKey) {
      setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    } else {
      setSortKey(key);
      // string columns lead ascending (A→Z); numeric columns lead descending (strongest first).
      setSortDir(key === "label" || key === "family" ? "asc" : "desc");
    }
  };

  const toggle = (key: string) =>
    setExpanded((prev) => {
      const next = new Set(prev);
      next.has(key) ? next.delete(key) : next.add(key);
      return next;
    });

  if (rows.length === 0) {
    return (
      <EmptyState
        icon={Microscope}
        title="No forward-tested factors"
        description="No stored snapshot has a factor value with a realized forward return at any horizon. No rank-IC or decile is fabricated to fill the gap."
      />
    );
  }

  const colSpan = 5 + horizons.length * 2 + 1; // Factor+Family+Rank-IC+N+Risk-adj + 2·horizons + chevron

  return (
    <>
      <div className="flex flex-wrap items-center gap-x-6 gap-y-1 text-xs text-text-muted">
        <span>
          <span className="text-text-faint">Factors: </span>
          <span className="num text-text">{rows.length}</span>
        </span>
        <span>
          <span className="text-text-faint">Horizons: </span>
          <span className="num text-text">{horizons.map((h) => `${h}d`).join(" · ")}</span>
        </span>
        <span className="text-text-faint">
          Top-decile (D10) forward-return &amp; paired max-drawdown per horizon; rank-IC / risk-adjusted at{" "}
          <span className="num text-text">{defaultHorizon}d</span>. Click a column to sort (NA-last); click a
          factor to expand its decile grid. Cells with <span className="text-warn">n &lt; {data.min_sample} ⚠</span>{" "}
          render NA.
        </span>
      </div>

      <Card className="overflow-x-auto p-0">
        <table data-testid="factors-table" className="w-full border-collapse text-sm">
          <thead>
            <tr className="border-b border-border text-left text-xs uppercase tracking-wide text-text-faint">
              <FactorSortHeader col="label" label="Factor" activeKey={sortKey} dir={sortDir} onSort={onSort} />
              <FactorSortHeader col="family" label="Family" activeKey={sortKey} dir={sortDir} onSort={onSort} />
              <FactorSortHeader col="rank_ic" label={`Rank-IC (${defaultHorizon}d)`} activeKey={sortKey} dir={sortDir} onSort={onSort} numeric />
              <FactorSortHeader col="n" label="N" activeKey={sortKey} dir={sortDir} onSort={onSort} numeric />
              <FactorSortHeader
                col="risk_adjusted"
                label={`Risk-adjusted (${defaultHorizon}d)`}
                activeKey={sortKey}
                dir={sortDir}
                onSort={onSort}
                numeric
              />
              {/* J-114: all forward-return columns first, then all max-drawdown columns (no interleave). */}
              {groupedHorizonColumns(horizons).map((col) => (
                <FactorSortHeader
                  key={horizonColumnKey(col)}
                  col={`${col.metric}:${col.horizon}`}
                  label={`${col.metric === "fwd" ? "Fwd" : "MDD"} ${col.horizon}d`}
                  activeKey={sortKey}
                  dir={sortDir}
                  onSort={onSort}
                  numeric
                />
              ))}
              <th className="px-4 py-2" aria-label="expand" />
            </tr>
          </thead>
          <tbody>
            {sorted.map((row) => (
              <FactorRows
                key={row.key}
                row={row}
                open={expanded.has(row.key)}
                onToggle={() => toggle(row.key)}
                min={data.min_sample}
                horizons={horizons}
                defaultHorizon={defaultHorizon}
                colSpan={colSpan}
                scope={scope}
              />
            ))}
          </tbody>
        </table>
      </Card>
    </>
  );
}

/** One factor's summary row + (when expanded) its decile-sort panel. The summary `<tr>` is the keyboard-
 *  accessible expandable-row control (role=button + aria-expanded, Enter/Space toggles) the Sectors page
 *  uses; it carries NO nested interactive element (the decile `N=` SampleLinks live in the SEPARATE expanded
 *  panel, not in the clickable summary row — the iter-5 nested-interactive hazard). */
/** A muted "NA" span — never a fabricated number (the SAME copy the ratio/decile cells use). */
function NaCell({ title }: { title?: string }) {
  return (
    <span className="num font-semibold text-text-muted" title={title ?? "NA — low sample or no value, not a fabricated number"}>
      NA
    </span>
  );
}

/** A factor's TOP-decile (D10) paired cell at one horizon: the colour-graded forward-return (returnClass)
 *  or max-drawdown (mdd-color tokens), or an explicit NA when the top decile is low-sample / empty / its
 *  value is null. Read straight off the served top decile — recomputes nothing. */
function TopDecileCell({ row, horizon, metric, min }: {
  row: FactorTableRow;
  horizon: number;
  metric: "fwd" | "mdd";
  min: number;
}) {
  const top = topDecileAt(row, horizon);
  const value = metric === "fwd" ? top?.mean_return ?? null : top?.mean_max_drawdown ?? null;
  const na = !top || top.low_sample || top.n === 0 || value === null;
  if (na) {
    return (
      <NaCell
        title={
          top && top.low_sample
            ? `Top decile low sample (n < ${min}) — NA, not a fabricated number`
            : metric === "mdd"
              ? "No stored drawdown for the top-decile cohort at this horizon — NA"
              : "No top-decile observations at this horizon — NA"
        }
      />
    );
  }
  return metric === "fwd" ? (
    <span className={cn("num font-semibold", returnClass(value))}>{fmtPct(value)}</span>
  ) : (
    <span className={cn("num font-semibold", mddClass(value))}>{fmtMdd(value)}</span>
  );
}

function FactorRows({
  row,
  open,
  onToggle,
  min,
  horizons,
  defaultHorizon,
  colSpan,
  scope,
}: {
  row: FactorTableRow;
  open: boolean;
  onToggle: () => void;
  min: number;
  horizons: number[];
  defaultHorizon: number;
  colSpan: number;
  scope: SampleScope;
}) {
  const icNa = row.rank_ic.value === null;
  const raNa = topCellIsNa(row, defaultHorizon, "fwd") || row.risk_adjusted === null;
  return (
    <>
      <tr
        role="button"
        tabIndex={0}
        aria-expanded={open}
        data-testid={`factor-row-${row.key}`}
        onClick={onToggle}
        onKeyDown={(e) => {
          if (e.key === "Enter" || e.key === " ") {
            e.preventDefault();
            onToggle();
          }
        }}
        className={cn(
          "cursor-pointer border-b border-border transition-colors last:border-b-0",
          "hover:bg-surface-2 focus-visible:bg-surface-2 focus-visible:outline-none active:bg-border",
          open && "bg-surface-2",
        )}
      >
        <td className="px-4 py-2">
          <span className="font-semibold text-text">{row.label}</span>{" "}
          <span className="text-xs text-text-faint">({row.direction.replace("_", " ")})</span>
        </td>
        <td className="px-4 py-2 text-text-muted">{familyLabel(row.family)}</td>
        <td className="px-4 py-2 text-right">
          <RatioCell
            value={row.rank_ic.value}
            na={icNa}
            title={icNa ? "Not enough independent observations to rank-correlate — NA, not a fabricated 0" : undefined}
          />
        </td>
        <td className="num px-4 py-2 text-right text-text-muted">{row.rank_ic.n}</td>
        <td className="px-4 py-2 text-right">
          <RatioCell
            value={row.risk_adjusted}
            na={raNa}
            title={raNa ? `Low sample (n < ${min}) or no downside in the top decile — NA, not a fabricated number` : "Top-decile mean return per unit downside deviation"}
          />
        </td>
        {/* J-114: all forward-return cells first, then all max-drawdown cells (no interleave). */}
        {groupedHorizonColumns(horizons).map((col) => (
          <td key={`tc-${row.key}-${horizonColumnKey(col)}`} className="px-4 py-2 text-right">
            <TopDecileCell row={row} horizon={col.horizon} metric={col.metric} min={min} />
          </td>
        ))}
        <td className="px-4 py-2 text-text-faint">
          {open ? <ChevronDown className="h-4 w-4" aria-hidden /> : <ChevronRight className="h-4 w-4" aria-hidden />}
        </td>
      </tr>
      {open ? (
        // The expanded panel is a SEPARATE, non-clickable <tr> — the full all-horizon decile grid (with its
        // per-(horizon,decile) `N=` SampleLink drill-downs) lives here, NOT inside the clickable summary row.
        <tr className="border-b border-border bg-bg last:border-b-0">
          <td colSpan={colSpan} className="px-4 py-3">
            <DecileTable
              byHorizon={row.by_horizon}
              horizons={horizons}
              defaultHorizon={defaultHorizon}
              min={min}
              factor={row.key}
              scope={scope}
            />
          </td>
        </tr>
      ) : null}
    </>
  );
}

function PanelTitle({ children, hint }: { children: React.ReactNode; hint?: string }) {
  return (
    <div className="border-b border-border px-4 py-3">
      <h2 className="text-sm font-semibold text-text">{children}</h2>
      {hint ? <p className="mt-0.5 text-xs text-text-faint">{hint}</p> : null}
    </div>
  );
}

/** A decile's forward-return cell at one horizon: explicit "NA" when low-sample (n < min_sample) / empty /
 *  null — never a fabricated number; otherwise the colour-graded mean return (its own per-horizon factor
 *  range on hover). The trailing `n` chip is a J-51 LINK into the samples drill-down for THIS exact
 *  `(factor, horizon, decile)` cohort (count-coherent — its total == this n). One chip per (horizon, decile)
 *  — it lives on the return cell, never duplicated on the paired drawdown cell. */
function DecileReturnCell({
  cell,
  min,
  factor,
  horizon,
  decile,
  scope,
}: {
  cell: FactorDecileRow;
  min: number;
  factor: string;
  horizon: number;
  decile: number;
  scope: SampleScope;
}) {
  const na = cell.low_sample || cell.n === 0 || cell.mean_return === null;
  const rangeTitle =
    cell.factor_min === null || cell.factor_max === null
      ? undefined
      : `Factor range at ${horizon}d: ${cell.factor_min.toFixed(2)} … ${cell.factor_max.toFixed(2)}`;
  return (
    <span className="inline-flex items-center justify-end gap-2">
      {na ? (
        <span className="num font-semibold text-text-muted" title={cell.low_sample ? `Low sample — n below the ${min} minimum` : "No observations"}>
          NA
        </span>
      ) : (
        <span className={cn("num font-semibold", returnClass(cell.mean_return))} title={rangeTitle}>
          {fmtPct(cell.mean_return)}
        </span>
      )}
      <SampleLink
        n={cell.n}
        min={min}
        scope={scope}
        cohort={{ kind: "factor", factor, horizon, slice: "decile", decile }}
        label={`See the ${cell.n} observations in factor ${factor} decile D${decile} at the ${horizon}-day horizon`}
      />
    </span>
  );
}

/** A decile's paired max-drawdown cell at one horizon: explicit "NA" when low-sample / empty / null —
 *  never a fabricated number; otherwise the mdd-color-graded value (a deeper drawdown reads more severe). */
function DecileMddCell({ cell, min }: { cell: FactorDecileRow; min: number }) {
  const na = cell.low_sample || cell.n === 0 || cell.mean_max_drawdown === null;
  if (na) {
    return (
      <span className="num font-semibold text-text-muted" title={cell.low_sample ? `Low sample — n below the ${min} minimum` : "No stored drawdown — NA"}>
        NA
      </span>
    );
  }
  return <span className={cn("num font-semibold", mddClass(cell.mean_max_drawdown))}>{fmtMdd(cell.mean_max_drawdown)}</span>;
}

/** The all-horizon decile grid (J-109): rows D1…D10, columns = factor range (at the default horizon) then,
 *  per config horizon, a paired (forward-return, max-drawdown) cell. Each return cell carries the
 *  per-(factor,horizon,decile) `N=` drill-down chip. Every figure is re-presented from the served per-horizon
 *  decile tables — recomputes nothing. */
function DecileTable({
  byHorizon,
  horizons,
  defaultHorizon,
  min,
  factor,
  scope,
}: {
  byHorizon: FactorHorizonDeciles[];
  horizons: number[];
  defaultHorizon: number;
  min: number;
  factor: string;
  scope: SampleScope;
}) {
  const byH = new Map(byHorizon.map((b) => [b.horizon, b.deciles]));
  const defaultDeciles = byH.get(defaultHorizon) ?? byHorizon[0]?.deciles ?? [];
  const decileCount = defaultDeciles.length;
  return (
    <Card className="p-0">
      <PanelTitle
        hint={`Mean realized forward return AND its paired max-drawdown per factor decile (D1 = lowest factor value → D10 = highest) at every horizon. Monotonicity across D1→D10 = the factor sorts future returns. Factor range is shown at the ${defaultHorizon}-day horizon; each horizon's own range is on its return cell's hover. Low-sample / empty (factor, horizon, decile) cohorts render NA + n.`}
      >
        Decile grid — forward return &amp; paired max-drawdown, all horizons
      </PanelTitle>
      <div className="overflow-x-auto">
        <table data-testid={`decile-grid-${factor}`} className="w-full border-collapse text-sm">
          <thead>
            <tr className="border-b border-border text-left text-xs uppercase tracking-wide text-text-faint">
              <th className="px-4 py-2 font-medium">
                <span className="inline-flex items-center gap-1">Decile<TermInfo term="decile" /></span>
              </th>
              <th className="px-4 py-2 text-right font-medium">Factor range ({defaultHorizon}d)</th>
              {/* J-114: all forward-return columns first, then all max-drawdown columns (no interleave). */}
              {groupedHorizonColumns(horizons).map((col) => (
                <th key={horizonColumnKey(col)} className="px-4 py-2 text-right font-medium">
                  {col.metric === "fwd" ? (
                    <span className="inline-flex items-center justify-end gap-1">Fwd {col.horizon}d<TermInfo term="forward return" /></span>
                  ) : (
                    <>MDD {col.horizon}d</>
                  )}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {Array.from({ length: decileCount }, (_, i) => i + 1).map((d) => {
              const range = defaultDeciles[d - 1];
              return (
                <tr key={d} className="border-b border-border last:border-b-0">
                  <td className="px-4 py-2">
                    <span className="num font-semibold text-text">D{d}</span>
                  </td>
                  <td className="num px-4 py-2 text-right text-xs text-text-faint">
                    {!range || range.factor_min === null || range.factor_max === null
                      ? "—"
                      : `${range.factor_min.toFixed(2)} … ${range.factor_max.toFixed(2)}`}
                  </td>
                  {/* J-114: all forward-return cells first, then all max-drawdown cells (no interleave). */}
                  {groupedHorizonColumns(horizons).map((col) => {
                    const cell = byH.get(col.horizon)?.[d - 1];
                    return (
                      <td key={`dgc-${horizonColumnKey(col)}-${d}`} className="px-4 py-2 text-right">
                        {col.metric === "fwd" ? (
                          cell ? (
                            <DecileReturnCell cell={cell} min={min} factor={factor} horizon={col.horizon} decile={d} scope={scope} />
                          ) : (
                            <span className="text-text-faint">—</span>
                          )
                        ) : cell ? (
                          <DecileMddCell cell={cell} min={min} />
                        ) : (
                          <span className="text-text-faint">—</span>
                        )}
                      </td>
                    );
                  })}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </Card>
  );
}

export function LabSkeleton() {
  return (
    <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
      <Card className="space-y-2 p-4 lg:col-span-2">
        {Array.from({ length: 6 }).map((_, i) => (
          <div key={i} className="h-7 w-full animate-pulse rounded bg-surface-2" />
        ))}
      </Card>
      <Card className="space-y-2 p-4">
        {Array.from({ length: 3 }).map((_, i) => (
          <div key={i} className="h-7 w-full animate-pulse rounded bg-surface-2" />
        ))}
      </Card>
    </div>
  );
}

// --- Multi-factor combination cohort (J-26) ------------------------------------------------------
type ConditionInput = { factor: string; side: "top" | "bottom"; quantile: string };

/** Build the single-condition row label from the resolved condition (server values only) — e.g.
 *  "Relative strength vs SPY (3m) · top Quintile (20%)". Re-formats the payload; invents no copy. */
function conditionLabel(condition: FactorCombinationCondition): string {
  return `${condition.factor.label} · ${condition.side} ${condition.quantile.label}`;
}

/** The Multi-factor combination cohort section (J-26): compose 2–3 catalog-factor top/bottom quantile
 *  conditions and read the combined-AND cohort beside the unconditional baseline and each single-factor
 *  cohort. Reuses the page's shared `horizon` + the shared `asofCutoff` (no second date/horizon state);
 *  adds ONLY `conditions` state. J-32: when `asofCutoff` is set (As-of mode + a past global date) the
 *  cohorts pool only snapshots dated ≤ that date — the single global as-of, a mode not a second date
 *  control (J-18). Re-formats the payload only — recomputes no return/factor; low-sample/empty cohorts
 *  render NA + n (never a fabricated number). The factor + quantile option lists come from the payload
 *  (config-driven) — no hard-coded list here. */
export function CombinationLab({
  horizon,
  asofCutoff,
  scope,
  onMeta,
}: {
  horizon: number | undefined;
  asofCutoff: string | null;
  scope: SampleScope;
  onMeta?: (meta: LabMeta) => void;
}) {
  // null until the user first edits — then the explicit condition list. The server resolves the config
  // default_conditions when none are sent (config-driven; no hard-coded default in the UI).
  const [conditions, setConditions] = useState<ConditionInput[] | null>(null);
  const [data, setData] = useState<FactorCombinationResponse | null>(null);
  const [status, setStatus] = useState<"loading" | "ok" | "error">("loading");

  useEffect(() => {
    const controller = new AbortController();
    setStatus("loading");
    // depends on the RESOLVED `asofCutoff` (not raw asOf): All-history mode never refetches on a global
    // date change (cutoff stays null); toggling mode re-points the cohorts to the new window (J-32/J-15).
    fetchFactorCombination(conditions ?? [], horizon, asofCutoff ?? undefined, controller.signal)
      .then((d) => {
        if (controller.signal.aborted) return;
        setData(d);
        setStatus("ok");
        // report the config-driven horizon vocabulary up to the route's shared horizon selector (J-104).
        onMeta?.({ horizons: d.horizons, default_horizon: d.default_horizon });
      })
      .catch(() => {
        if (!controller.signal.aborted) setStatus("error");
      });
    return () => controller.abort();
  }, [conditions, horizon, asofCutoff]);

  // the editable rows: explicit user conditions, else the server's resolved defaults (kept stable across
  // re-fetches because `data` persists) — config-driven, never a hard-coded frontend list.
  const rows: ConditionInput[] =
    conditions ??
    (data
      ? data.conditions.map((c) => ({ factor: c.factor.key, side: c.side, quantile: c.quantile.key }))
      : []);

  const atMax = data ? rows.length >= data.max_conditions : true;
  const atMin = data ? rows.length <= data.min_conditions : true;

  const setRow = (idx: number, patch: Partial<ConditionInput>) =>
    setConditions(rows.map((r, i) => (i === idx ? { ...r, ...patch } : r)));
  const addRow = () => {
    if (!data || atMax) return;
    setConditions([
      ...rows,
      { factor: data.factors[0].key, side: "top", quantile: data.quantiles[0].key },
    ]);
  };
  const removeRow = (idx: number) => {
    if (atMin) return;
    setConditions(rows.filter((_, i) => i !== idx));
  };

  return (
    <Card className="p-0" data-testid="combination-section">
      <PanelTitle
        hint={`Combine 2–${data?.max_conditions ?? "all"} factor conditions (each a catalog factor at its top/bottom quantile) and read the Combined (composite rank-blend) cohort — the top ${data?.composite_quantile?.label ?? "config-quantile"} of the pool by a ${data?.weighting?.scheme ?? "config"}-weighted blend of the conditions' percentile ranks (a transparent ranking of stored values, NOT a fitted/ML model) — beside the all-names baseline and each single-factor cohort, so "does combining beat either alone?" is answerable. The Strict overlap (AND) row is the optional secondary exact intersection (NA + n when empty). Each cohort shows mean / median forward return, hit-rate, and the downside risk-adjusted column with n; cohorts with n < ${data?.min_sample ?? "min"} show NA + n, never a fabricated number.`}
      >
        Multi-factor combination cohort
      </PanelTitle>
      <div className="space-y-4 p-4">
        {data ? (
          <ConditionControls
            data={data}
            rows={rows}
            atMin={atMin}
            atMax={atMax}
            onSetRow={setRow}
            onAddRow={addRow}
            onRemoveRow={removeRow}
          />
        ) : null}

        {status === "error" ? (
          <div className="flex items-center gap-3 rounded-md border border-neg bg-surface p-4 text-sm text-neg">
            <AlertTriangle className="h-5 w-5 shrink-0" aria-hidden />
            <div>
              <p className="font-medium">Backend unavailable</p>
              <p className="text-text-muted">
                The combination cohorts could not load from the API. No figures are shown rather than
                fabricated values — confirm the backend is running and adjust a condition to retry.
              </p>
            </div>
          </div>
        ) : !data ? (
          <CombinationSkeleton />
        ) : data.pool_n === 0 ? (
          <EmptyState
            icon={Microscope}
            title="No forward-tested observations for these conditions / horizon"
            description="No stored snapshot has every selected factor's value and a realized forward return at this horizon. Pick a shorter horizon or different factors — no cohort is fabricated to fill the gap."
          />
        ) : (
          <>
            <CombinationTable data={data} dim={status === "loading"} scope={scope} />
            <p className="text-xs text-text-faint">
              The risk-adjusted column is{" "}
              <span className="text-text-muted">downside-deviation only</span> (mean ÷ downside deviation —
              never total volatility, so healthy upside is not penalised). return/MAE and MAE/MFE excursion
              measures are in the Setup &amp; Pattern Lab below (J-29).
            </p>
          </>
        )}
      </div>
    </Card>
  );
}

/** The 2–3 condition rows: each a Factor select, a Top/Bottom side toggle, and a Quantile select (option
 *  lists from the payload — config-driven), with a per-row Remove (disabled at min_conditions) and an
 *  "Add condition" control (disabled at max_conditions). Edits produce a full condition list re-fetched
 *  by the parent — the frontend chooses WHICH conditions, never recomputing a cohort. */
function ConditionControls({
  data,
  rows,
  atMin,
  atMax,
  onSetRow,
  onAddRow,
  onRemoveRow,
}: {
  data: FactorCombinationResponse;
  rows: ConditionInput[];
  atMin: boolean;
  atMax: boolean;
  onSetRow: (idx: number, patch: Partial<ConditionInput>) => void;
  onAddRow: () => void;
  onRemoveRow: (idx: number) => void;
}) {
  return (
    <div className="space-y-2">
      {rows.map((row, idx) => (
        <div
          key={idx}
          className="flex flex-wrap items-end gap-3 rounded-md border border-border bg-surface-2 p-3"
        >
          <label className="flex flex-col gap-1">
            <span className="text-xs uppercase tracking-wide text-text-faint">Factor</span>
            <Select
              aria-label={`Condition ${idx + 1} factor`}
              data-testid={`condition-factor-${idx}`}
              value={row.factor}
              onChange={(e) => onSetRow(idx, { factor: e.target.value })}
              className="w-56"
            >
              {data.factors.map((f) => (
                <option key={f.key} value={f.key}>
                  {f.label}
                </option>
              ))}
            </Select>
          </label>

          <div className="flex flex-col gap-1">
            <span className="text-xs uppercase tracking-wide text-text-faint">Side</span>
            <SideToggle
              value={row.side}
              onChange={(side) => onSetRow(idx, { side })}
              testId={`condition-side-${idx}`}
            />
          </div>

          <label className="flex flex-col gap-1">
            <span className="text-xs uppercase tracking-wide text-text-faint">Quantile</span>
            <Select
              aria-label={`Condition ${idx + 1} quantile`}
              data-testid={`condition-quantile-${idx}`}
              value={row.quantile}
              onChange={(e) => onSetRow(idx, { quantile: e.target.value })}
              className="w-44"
            >
              {data.quantiles.map((q) => (
                <option key={q.key} value={q.key}>
                  {q.label}
                </option>
              ))}
            </Select>
          </label>

          <button
            type="button"
            onClick={() => onRemoveRow(idx)}
            disabled={atMin}
            aria-label={`Remove condition ${idx + 1}`}
            data-testid={`condition-remove-${idx}`}
            className={cn(
              "inline-flex h-9 items-center gap-1 rounded-md border border-border px-3 text-sm transition-colors",
              "focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-accent",
              atMin
                ? "cursor-not-allowed text-text-faint opacity-50"
                : "text-text-muted hover:border-neg hover:text-neg",
            )}
          >
            <X className="h-4 w-4" aria-hidden /> Remove
          </button>
        </div>
      ))}

      <button
        type="button"
        onClick={onAddRow}
        disabled={atMax}
        data-testid="condition-add"
        className={cn(
          "inline-flex h-9 items-center gap-1 rounded-md border border-border px-3 text-sm transition-colors",
          "focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-accent",
          atMax
            ? "cursor-not-allowed text-text-faint opacity-50"
            : "text-accent hover:border-accent hover:bg-surface",
        )}
      >
        <Plus className="h-4 w-4" aria-hidden /> Add condition
      </button>
    </div>
  );
}

/** A Top / Bottom segmented toggle styled like the page's HorizonSelector control. `top`/`bottom` are the
 *  two fixed condition sides (a structural vocabulary, not a config tunable). */
function SideToggle({
  value,
  onChange,
  testId,
}: {
  value: "top" | "bottom";
  onChange: (side: "top" | "bottom") => void;
  testId: string;
}) {
  const sides: { key: "top" | "bottom"; label: string }[] = [
    { key: "top", label: "Top" },
    { key: "bottom", label: "Bottom" },
  ];
  return (
    <div
      role="group"
      aria-label="Condition side"
      data-testid={testId}
      className="inline-flex h-9 overflow-hidden rounded-md border border-border bg-surface-2"
    >
      {sides.map((s) => {
        const active = s.key === value;
        return (
          <button
            key={s.key}
            type="button"
            aria-pressed={active}
            onClick={() => onChange(s.key)}
            className={cn(
              "border-r border-border px-3 text-sm transition-colors last:border-r-0",
              "focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-accent",
              active
                ? "bg-accent font-semibold text-bg"
                : "text-text-muted hover:bg-surface hover:text-text",
            )}
          >
            {s.label}
          </button>
        );
      })}
    </div>
  );
}

/** A cohort's numeric cell: explicit "NA" (muted) when the cohort is low-sample (n < min_sample), empty
 *  (n === 0), or the value is null — never a fabricated number; otherwise the formatted value (returns +
 *  the risk-adjusted ratio are colour-graded; the hit-rate stays neutral so a low hit-rate is not painted
 *  "good"). The honest n is carried once per row by the SampleSize chip in the dedicated `n` column. */
function CohortCell({
  value,
  stats,
  kind,
  min,
}: {
  value: number | null;
  stats: CohortStats;
  kind: "pct" | "ratio" | "rate";
  min: number;
}) {
  const na = stats.low_sample || stats.n === 0 || value === null;
  if (na) {
    return (
      <span
        className="num font-semibold text-text-muted"
        title={
          stats.low_sample
            ? `Low sample — n below the ${min} minimum; NA, not a fabricated number`
            : "No observations"
        }
      >
        NA
      </span>
    );
  }
  const text = kind === "ratio" ? fmtRatio(value) : fmtPct(value);
  return (
    <span className={cn("num font-semibold", kind === "rate" ? "text-text" : returnClass(value))}>
      {text}
    </span>
  );
}

/** The comparison table: Baseline (all names) vs each single-condition cohort vs the HEADLINE Combined
 *  (composite rank-blend) cohort vs the SECONDARY Strict overlap (AND) cohort — columns Cohort / n / Mean
 *  fwd return / Median / Hit-rate / Risk-adjusted (downside). Row order Baseline → singles → Combined
 *  (composite, emphasized) → Strict overlap (AND) (secondary, muted). Re-formats the payload only; low-
 *  sample/empty/null cells render NA + n via CohortCell + SampleSize (the composite is populated while the
 *  strict overlap may show NA — never a fabricated number). */
function CombinationTable({
  data,
  dim,
  scope,
}: {
  data: FactorCombinationResponse;
  dim: boolean;
  scope: SampleScope;
}) {
  const min = data.min_sample;
  const horizon = data.horizon;
  // the resolved condition triples (config-driven) — the SAME the backend pooled; sent verbatim so the
  // drill-down reproduces this exact cohort (count-coherent). One author for the triple string shape.
  const conditions = data.conditions.map(
    (c) => `${c.factor.key}:${c.side}:${c.quantile.key}`,
  );
  // each table row carries the cohort selector its `n` chip drills into (J-51). `cohort` is the kind;
  // `singleIndex` identifies WHICH single-condition cohort (its index into `data.singles`).
  type Cohort = "baseline" | "single" | "composite" | "strict_overlap";
  const tableRows: {
    label: string;
    stats: CohortStats;
    emphasis?: "baseline" | "composite" | "strict_overlap";
    cohort: Cohort;
    singleIndex?: number;
  }[] = [
    { label: data.baseline.label, stats: data.baseline.stats, emphasis: "baseline", cohort: "baseline" },
    ...data.singles.map((s, idx) => ({
      label: conditionLabel(s.condition),
      stats: s.stats,
      cohort: "single" as Cohort,
      singleIndex: idx,
    })),
    { label: data.composite.label, stats: data.composite.stats, emphasis: "composite", cohort: "composite" },
    { label: data.strict_overlap.label, stats: data.strict_overlap.stats, emphasis: "strict_overlap", cohort: "strict_overlap" },
  ];
  return (
    <div className={cn("overflow-x-auto transition-opacity", dim && "opacity-60")} aria-busy={dim}>
      <table data-testid="combination-table" className="w-full border-collapse text-sm">
        <thead>
          <tr className="border-b border-border text-left text-xs uppercase tracking-wide text-text-faint">
            <th className="px-4 py-2 font-medium">
              <span className="inline-flex items-center gap-1">Cohort<TermInfo term="composite" /></span>
            </th>
            <th className="px-4 py-2 text-right font-medium">n</th>
            <th className="px-4 py-2 text-right font-medium">Mean fwd return</th>
            <th className="px-4 py-2 text-right font-medium">Median</th>
            <th className="px-4 py-2 text-right font-medium">
              <span className="inline-flex items-center gap-1">Hit-rate<TermInfo term="hit-rate" /></span>
            </th>
            <th className="px-4 py-2 text-right font-medium">Risk-adjusted (downside)</th>
          </tr>
        </thead>
        <tbody>
          {tableRows.map((row, i) => {
            // the HEADLINE composite row is emphasized (surface-2 + semibold); the strict-overlap row is the
            // optional SECONDARY column (muted); baseline stays a labelled header row.
            const primary = row.emphasis === "composite" || row.emphasis === "baseline";
            return (
            <tr
              key={i}
              className={cn(
                "border-b border-border last:border-b-0",
                row.emphasis === "composite" && "bg-surface-2",
              )}
              data-testid={row.emphasis ? `combination-row-${row.emphasis}` : undefined}
            >
              <td className="px-4 py-2">
                <span className={cn(primary ? "font-semibold text-text" : "text-text-muted")}>
                  {row.label}
                </span>
              </td>
              <td className="px-4 py-2 text-right">
                <SampleLink
                  n={row.stats.n}
                  min={min}
                  scope={scope}
                  cohort={{
                    kind: "combination",
                    conditions,
                    horizon,
                    cohort: row.cohort,
                    singleIndex: row.singleIndex,
                  }}
                  label={`See the ${row.stats.n} names in the ${row.label} cohort`}
                />
              </td>
              <td className="px-4 py-2 text-right">
                <CohortCell value={row.stats.mean_return} stats={row.stats} kind="pct" min={min} />
              </td>
              <td className="px-4 py-2 text-right">
                <CohortCell value={row.stats.median_return} stats={row.stats} kind="pct" min={min} />
              </td>
              <td className="px-4 py-2 text-right">
                <CohortCell value={row.stats.hit_rate} stats={row.stats} kind="rate" min={min} />
              </td>
              <td className="px-4 py-2 text-right">
                <CohortCell value={row.stats.risk_adjusted} stats={row.stats} kind="ratio" min={min} />
              </td>
            </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

function CombinationSkeleton() {
  return (
    <div className="space-y-2">
      {Array.from({ length: 5 }).map((_, i) => (
        <div key={i} className="h-7 w-full animate-pulse rounded bg-surface-2" />
      ))}
    </div>
  );
}

// --- Setup & Pattern event study (J-29) ----------------------------------------------------------
/** The Setup & Pattern Lab (J-29): pick a setup or pattern subject and read its pooled, cross-snapshot
 *  event study — per horizon the forward-return distribution + expectancy + MAE/MFE + the downside-only
 *  risk-adjusted ratios, the best exit-horizon, and behaviour by regime and by sector. Reuses the page's
 *  shared `horizon` + the shared `asofCutoff` (no second date/horizon state); adds ONLY a `subject`
 *  selector. J-32: when `asofCutoff` is set (As-of mode + a past global date) every figure pools only
 *  snapshots dated ≤ that date — the single global as-of, a mode not a second date control (J-18).
 *  Re-formats the payload only — recomputes no return/excursion; low-sample / empty cells render NA + n
 *  (never a fabricated number). The subject list comes from the payload (config-driven) — no hard-coded
 *  setup/pattern list here. */
/** The overlap-honesty view (J-63): Episodes (first-trigger, the DEFAULT) ⇄ Pooled (per-signal-day). A
 *  cohort/MODE selector — orthogonal to the date and the analysis-mode. */
type EventStudyView = "episodes" | "pooled";

/** The Episodes ⇄ Pooled segmented toggle (J-63): a button group with an active pill (styled exactly like
 *  `AnalysisModeToggle` — clicked directly, NOT a `<select>`), defaulting to Episodes. It is a cohort/MODE
 *  selector ONLY — it never touches `?asof`, the global as-of, or the analysis-mode `scope` (J-18 held). No
 *  nested interactive element / TermInfo inside the buttons (iter-5 nested-interactive hazard). */
function EventStudyViewToggle({
  view,
  onChange,
}: {
  view: EventStudyView;
  onChange: (view: EventStudyView) => void;
}) {
  const options: { key: EventStudyView; label: string }[] = [
    { key: "episodes", label: "Episodes" },
    { key: "pooled", label: "Pooled" },
  ];
  return (
    <div className="flex flex-col gap-1">
      <span className="text-xs uppercase tracking-wide text-text-faint">Overlap view</span>
      <div
        role="group"
        aria-label="Event-study overlap view (episodes or pooled)"
        data-testid="event-study-view-toggle"
        className="inline-flex h-9 overflow-hidden rounded-md border border-border bg-surface-2"
      >
        {options.map((o) => {
          const active = o.key === view;
          return (
            <button
              key={o.key}
              type="button"
              aria-pressed={active}
              data-testid={`event-study-view-${o.key}`}
              onClick={() => onChange(o.key)}
              className={cn(
                "border-r border-border px-3 text-sm transition-colors last:border-r-0",
                "focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-accent",
                active
                  ? "bg-accent font-semibold text-bg"
                  : "text-text-muted hover:bg-surface hover:text-text",
              )}
            >
              {o.label}
            </button>
          );
        })}
      </div>
    </div>
  );
}

export function EventStudyLab({
  horizon,
  asofCutoff,
  scope,
  onMeta,
}: {
  horizon: number | undefined;
  asofCutoff: string | null;
  scope: SampleScope;
  onMeta?: (meta: LabMeta) => void;
}) {
  // `undefined` lets the backend pick the canonical default (first catalog subject). The subject list is
  // built from the loaded payload — config-driven, never a hard-coded frontend list.
  const [subject, setSubject] = useState<string | undefined>(undefined);
  // J-63: the overlap-honesty view — Episodes (first-trigger, DEFAULT) ⇄ Pooled (per-signal-day). A local
  // MODE/cohort state, fully INDEPENDENT of `asofCutoff` and the page analysis-mode `scope` (not a date).
  const [view, setView] = useState<EventStudyView>("episodes");
  const [data, setData] = useState<EventStudyResponse | null>(null);
  const [status, setStatus] = useState<"loading" | "ok" | "error">("loading");

  useEffect(() => {
    const controller = new AbortController();
    setStatus("loading");
    // depends on the RESOLVED `asofCutoff` (not raw asOf): All-history mode never refetches on a global
    // date change (cutoff stays null); toggling mode re-points the study to the new window (J-32/J-15).
    // `view` re-points the study to the episodes/pooled observation set (J-63 — orthogonal to the date).
    fetchEventStudy(subject, horizon, asofCutoff ?? undefined, view, controller.signal)
      .then((d) => {
        if (controller.signal.aborted) return;
        setData(d);
        setStatus("ok");
        onMeta?.({ horizons: d.horizons, default_horizon: d.default_horizon });
      })
      .catch(() => {
        if (!controller.signal.aborted) setStatus("error");
      });
    return () => controller.abort();
  }, [subject, horizon, asofCutoff, view]);

  const selectedSubject = subject ?? data?.subject.key ?? "";
  const hasAny = data ? data.by_horizon.some((r) => r.n > 0) : false;

  return (
    <Card className="p-0" data-testid="event-study-section">
      <PanelTitle
        hint={`Pick a setup or pattern and read its pooled, cross-snapshot event study: per horizon the forward-return distribution + expectancy + MAE/MFE + the downside risk-adjusted ratios, the best exit-horizon, and behaviour by regime and by sector — all from stored, lookahead-free, survivorship-labelled evidence. Cohorts with n < ${data?.min_sample ?? "min"} show NA + n, never a fabricated number.`}
      >
        Setup &amp; Pattern Lab — event study
      </PanelTitle>
      <div className="space-y-4 p-4">
        <div className="flex flex-wrap items-end gap-3">
          <SubjectSelector
            subjects={data?.subjects ?? []}
            value={selectedSubject}
            onChange={(key) => setSubject(key)}
          />
          <EventStudyViewToggle view={view} onChange={setView} />
          <p className="max-w-md text-xs text-text-faint">
            Re-uses the page&apos;s shared horizon selector and the page-level analysis-mode toggle above —
            no date control of its own (the single global as-of drives any point-in-time scoping, J-18). The
            Episodes ⇄ Pooled view is a cohort mode, not a date: Episodes (default) counts each continuous
            run of a symbol once at its first trigger; Pooled counts every signal-day.
          </p>
        </div>

        {data ? (
          <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
            <SubjectLeaderboardLink subject={data.subject} />
            <span className="text-xs text-text-faint">
              completes the synthesis path — lab evidence → the names expressing this {data.subject.kind} at
              the current as-of date → Stock Detail. The list reflects the live snapshot; no count is asserted here.
            </span>
          </div>
        ) : null}

        {data ? (
          <CaveatBanner survivorship={data.survivorship_bias} descriptive={data.descriptive_caveat} />
        ) : null}

        {status === "error" ? (
          <div className="flex items-center gap-3 rounded-md border border-neg bg-surface p-4 text-sm text-neg">
            <AlertTriangle className="h-5 w-5 shrink-0" aria-hidden />
            <div>
              <p className="font-medium">Backend unavailable</p>
              <p className="text-text-muted">
                The event study could not load from the API. No figures are shown rather than fabricated
                values — confirm the backend is running and adjust the subject to retry.
              </p>
            </div>
          </div>
        ) : !data ? (
          <CombinationSkeleton />
        ) : !hasAny ? (
          <EmptyState
            icon={Microscope}
            title="No forward-tested occurrences for this subject"
            description="No stored snapshot has this setup/pattern with a realized forward return yet. Pick another subject or a shorter horizon — no distribution is fabricated to fill the gap."
          />
        ) : (
          <EventStudyBody data={data} dim={status === "loading"} scope={scope} />
        )}
      </div>
    </Card>
  );
}

/** The synthesis cross-link (J-31): from the resolved event-study subject to the Stock Leaderboard
 *  pre-filtered to the names expressing it TODAY. The leaderboard filter is derived from the subject's
 *  `kind` (payload/config-driven — NOT a hard-coded subject↔filter table): a pattern → the leaderboard's
 *  `<key>__only` pattern filter; a setup → the status filter (the key IS the status string). The value is
 *  URL-encoded (the seed's keys/statuses are already URL-safe). It points to the live as-of snapshot and
 *  asserts no count it cannot prove (no fetch). Rendered whenever a subject resolves — INCLUDING a
 *  low-sample / NA subject (the "names expressing it today" set is independent of the event-study sample). */
function SubjectLeaderboardLink({ subject }: { subject: EventStudyResponse["subject"] }) {
  const asofHref = useAsOfHref();
  // The filter param is the leaderboard's existing one; the J-50 helper MERGES `?asof=D` (while
  // historical) into the already-present query string WITHOUT clobbering the `pattern`/`setup` param.
  const href = asofHref(
    subject.kind === "pattern"
      ? `/stocks?pattern=${encodeURIComponent(subject.key)}__only`
      : `/stocks?setup=${encodeURIComponent(subject.key)}`,
  );
  return (
    <Link
      href={href}
      data-testid="subject-leaderboard-link"
      className="inline-flex items-center gap-1 rounded-sm text-sm font-medium text-accent hover:underline focus-visible:underline focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-accent"
    >
      View the names expressing this on the leaderboard
      <span aria-hidden>→</span>
    </Link>
  );
}

/** The subject selector (config-driven from the payload): a single `<select>` grouped by `kind` into
 *  Setups vs Patterns `<optgroup>`s — the same payload-derived pattern as the factor selector, no
 *  hard-coded subject list. */
function SubjectSelector({
  subjects,
  value,
  onChange,
}: {
  subjects: EventStudyResponse["subjects"];
  value: string;
  onChange: (key: string) => void;
}) {
  const setups = subjects.filter((s) => s.kind === "setup");
  const patterns = subjects.filter((s) => s.kind === "pattern");
  return (
    <label className="flex flex-col gap-1">
      <span className="text-xs uppercase tracking-wide text-text-faint">Subject</span>
      <Select
        data-testid="subject-select"
        aria-label="Event-study subject"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-64"
        disabled={subjects.length === 0}
      >
        {subjects.length === 0 ? <option value="">Loading…</option> : null}
        {setups.length ? (
          <optgroup label="Setups">
            {setups.map((s) => (
              <option key={s.key} value={s.key}>
                {s.label}
              </option>
            ))}
          </optgroup>
        ) : null}
        {patterns.length ? (
          <optgroup label="Patterns">
            {patterns.map((s) => (
              <option key={s.key} value={s.key}>
                {s.label}
              </option>
            ))}
          </optgroup>
        ) : null}
      </Select>
    </label>
  );
}

/** A value cell shared across the event-study tables: explicit "NA" (muted) when the row is low-sample
 *  (n < min_sample), empty (n === 0), or the value is null — never a fabricated number; otherwise the
 *  formatted value (returns/excursions/ratios colour-graded; rates stay neutral so a low rate is not
 *  painted "good"). The honest n is carried once per row by the SampleSize chip in the dedicated column. */
function EsValue({
  value,
  na,
  kind,
}: {
  value: number | null;
  na: boolean;
  kind: "pct" | "ratio" | "rate";
}) {
  if (na || value === null) {
    return (
      <span className="num font-semibold text-text-muted" title="NA — low sample or no observations">
        NA
      </span>
    );
  }
  return (
    <span className={cn("num font-semibold", kind === "rate" ? "text-text" : returnClass(value))}>
      {kind === "ratio" ? fmtRatio(value) : fmtPct(value)}
    </span>
  );
}

/** The event-study body once data has loaded: a meta line (subject + pooled n + best exit-horizon), the
 *  per-horizon distribution / exit-horizon table, and the by-regime + by-sector panels for the selected
 *  horizon. `dim` fades the body while a re-fetch is in flight (the prior values stay visible). */
function EventStudyBody({
  data,
  dim,
  scope,
}: {
  data: EventStudyResponse;
  dim: boolean;
  scope: SampleScope;
}) {
  const selectedHorizon = data.horizon;
  const subject = data.subject.key;
  const view = data.view; // the RESOLVED view the data reflects — drives the chip hrefs (J-63)
  return (
    <div className={cn("space-y-4 transition-opacity", dim && "opacity-60")} aria-busy={dim}>
      <div className="flex flex-wrap items-center gap-x-6 gap-y-1 text-xs text-text-muted">
        <span>
          <span className="text-text-faint">Subject: </span>
          <span className="text-text">{data.subject.label}</span>{" "}
          <span className="text-text-faint">({data.subject.kind})</span>
        </span>
        <span>
          <span className="text-text-faint">Best exit-horizon: </span>
          <span className="num text-text">
            {data.best_exit_horizon === null ? "NA" : `${data.best_exit_horizon}d`}
          </span>
        </span>
        <span className="text-text-faint">
          Rows with <span className="text-warn">n &lt; {data.min_sample} ⚠</span> render NA.
        </span>
      </div>

      {/* J-63 disclosure line (present in BOTH views) — n (current view), unique symbols, episodes — read
          verbatim from the payload so window overlap is never hidden. */}
      <EventStudyDisclosure data={data} horizon={selectedHorizon} />

      <EventStudyHorizonTable
        rows={data.by_horizon}
        min={data.min_sample}
        bestExit={data.best_exit_horizon}
        subject={subject}
        scope={scope}
        view={view}
      />

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <EventStudyRegimeTable
          rows={data.by_regime}
          min={data.min_sample}
          horizon={selectedHorizon}
          subject={subject}
          scope={scope}
          view={view}
        />
        <EventStudySectorTable
          rows={data.by_sector}
          min={data.min_sample}
          horizon={selectedHorizon}
          subject={subject}
          scope={scope}
          view={view}
        />
      </div>
    </div>
  );
}

/** The J-63 disclosure line beside the figures (BOTH views): the current view's n, the distinct unique
 *  symbols in that set, and the distinct first-trigger episode count — read VERBATIM from the payload
 *  (number formatting only). It makes window overlap impossible to hide: in Pooled mode n > episodes when
 *  a subject persists; in Episodes mode n == episodes. The "Episode"/"Pooled" terms carry a glossary
 *  tooltip (TermInfo renders its own button — kept OUTSIDE any other interactive element, iter-5). */
function EventStudyDisclosure({
  data,
  horizon,
}: {
  data: EventStudyResponse;
  horizon: number;
}) {
  const isEpisodes = data.view === "episodes";
  return (
    <div
      data-testid="event-study-disclosure"
      className="flex flex-wrap items-center gap-x-6 gap-y-1 rounded-md border border-border bg-surface-2 px-3 py-2 text-xs text-text-muted"
    >
      <span className="inline-flex items-center gap-1">
        <span className="text-text-faint">View:</span>
        <span className="font-semibold text-text">{isEpisodes ? "Episodes" : "Pooled"}</span>
        <TermInfo term={isEpisodes ? "Episode" : "Pooled (per-signal-day)"} />
      </span>
      <span>
        <span className="text-text-faint">n ({horizon}d, {isEpisodes ? "episodes" : "signal-days"}): </span>
        <span className="num font-semibold text-text" data-testid="disclosure-n">{data.n}</span>
      </span>
      <span>
        <span className="text-text-faint">Unique symbols: </span>
        <span className="num font-semibold text-text" data-testid="disclosure-unique-symbols">
          {data.unique_symbols}
        </span>
      </span>
      <span>
        <span className="text-text-faint">Episodes: </span>
        <span className="num font-semibold text-text" data-testid="disclosure-episodes">
          {data.episode_count}
        </span>
      </span>
    </div>
  );
}

/** The per-horizon distribution / exit-horizon curve table: one row per configured horizon carrying the
 *  distribution (mean / median / %positive / dispersion), expectancy, mean MAE / MFE, and BOTH downside-
 *  only risk-adjusted ratios (return ÷ downside-deviation and return ÷ mean-|MAE| — never total volatility,
 *  shown beside the raw mean). The best exit-horizon row is highlighted; low-sample rows render NA + n. */
function EventStudyHorizonTable({
  rows,
  min,
  bestExit,
  subject,
  scope,
  view,
}: {
  rows: EventStudyHorizonRow[];
  min: number;
  bestExit: number | null;
  subject: string;
  scope: SampleScope;
  view: EventStudyView;
}) {
  return (
    <Card className="p-0">
      <PanelTitle hint="One row per forward horizon (the exit-horizon curve): the forward-return distribution, per-occurrence expectancy, mean MAE / MFE excursions, and BOTH downside-only risk-adjusted ratios (return ÷ downside-deviation and return ÷ mean-|MAE| — never total volatility). The best exit-horizon (highest downside-risk-adjusted return among non-low-sample horizons) is highlighted; rows with n below the minimum render NA + n.">
        Per-horizon distribution &amp; exit-horizon curve
      </PanelTitle>
      <div className="overflow-x-auto">
        <table data-testid="event-study-horizon-table" className="w-full border-collapse text-sm">
          <thead>
            <tr className="border-b border-border text-left text-xs uppercase tracking-wide text-text-faint">
              <th className="px-3 py-2 font-medium">
                <span className="inline-flex items-center gap-1">Horizon<TermInfo term="horizon" /></span>
              </th>
              <th className="px-3 py-2 text-right font-medium">
                <span className="inline-flex items-center gap-1">n<TermInfo term="n (sample size)" /></span>
              </th>
              <th className="px-3 py-2 text-right font-medium">Mean</th>
              <th className="px-3 py-2 text-right font-medium">
                <span className="inline-flex items-center gap-1">Median<TermInfo term="median" /></span>
              </th>
              <th className="px-3 py-2 text-right font-medium">
                <span className="inline-flex items-center gap-1">% Positive<TermInfo term="% positive" /></span>
              </th>
              <th className="px-3 py-2 text-right font-medium">
                <span className="inline-flex items-center gap-1">Dispersion<TermInfo term="dispersion" /></span>
              </th>
              <th className="px-3 py-2 text-right font-medium">
                <span className="inline-flex items-center gap-1">Expectancy<TermInfo term="expectancy" /></span>
              </th>
              <th className="px-3 py-2 text-right font-medium">
                <span className="inline-flex items-center gap-1">Mean MAE<TermInfo term="MAE" /></span>
              </th>
              <th className="px-3 py-2 text-right font-medium">
                <span className="inline-flex items-center gap-1">Mean MFE<TermInfo term="MFE" /></span>
              </th>
              {/* J-86 — the aggregate mean max-drawdown beside the excursion stats (read-only over stored values) */}
              <th className="px-3 py-2 text-right font-medium">
                <span className="inline-flex items-center gap-1">Mean MDD<TermInfo term="max drawdown" /></span>
              </th>
              <th className="px-3 py-2 text-right font-medium">
                <span className="inline-flex items-center gap-1">Return / downside-dev<TermInfo term="return / downside-dev" /></span>
              </th>
              <th className="px-3 py-2 text-right font-medium">
                <span className="inline-flex items-center gap-1">Return / MAE<TermInfo term="return / MAE" /></span>
              </th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => {
              const na = row.low_sample || row.n === 0;
              const best = bestExit !== null && row.horizon === bestExit;
              return (
                <tr
                  key={row.horizon}
                  className={cn("border-b border-border last:border-b-0", best && "bg-surface-2")}
                >
                  <td className="px-3 py-2">
                    <span className="num font-semibold text-text">{row.horizon}d</span>
                    {best ? (
                      <span className="ml-2 rounded border border-accent px-1.5 py-0.5 text-xs font-medium text-accent">
                        best exit
                      </span>
                    ) : null}
                  </td>
                  <td className="px-3 py-2 text-right">
                    {/* this row's n is the pooled cohort AT THIS row's horizon — drill into it (J-51) */}
                    <SampleLink
                      n={row.n}
                      min={min}
                      scope={scope}
                      cohort={{ kind: "event-study", subject, horizon: row.horizon, slice: "pooled", view }}
                      label={`See the ${row.n} ${view === "episodes" ? "episodes" : "occurrences"} at the ${row.horizon}-day horizon`}
                    />
                  </td>
                  <td className="px-3 py-2 text-right">
                    <EsValue value={row.mean_return} na={na} kind="pct" />
                  </td>
                  <td className="px-3 py-2 text-right">
                    <EsValue value={row.median} na={na} kind="pct" />
                  </td>
                  <td className="px-3 py-2 text-right">
                    <EsValue value={row.pct_positive} na={na} kind="rate" />
                  </td>
                  <td className="px-3 py-2 text-right">
                    <EsValue value={row.dispersion} na={na} kind="pct" />
                  </td>
                  <td className="px-3 py-2 text-right">
                    <EsValue value={row.expectancy.expectancy} na={na} kind="pct" />
                  </td>
                  <td className="px-3 py-2 text-right">
                    <EsValue value={row.mean_mae} na={na} kind="pct" />
                  </td>
                  <td className="px-3 py-2 text-right">
                    <EsValue value={row.mean_mfe} na={na} kind="pct" />
                  </td>
                  {/* J-86 — the aggregate mean max-drawdown cell (NA + low-sample gated like the others). */}
                  <td className="px-3 py-2 text-right">
                    <EsValue value={row.mean_max_drawdown} na={na} kind="pct" />
                  </td>
                  <td className="px-3 py-2 text-right">
                    <EsValue value={row.return_per_downside_dev} na={na} kind="ratio" />
                  </td>
                  <td className="px-3 py-2 text-right">
                    <EsValue value={row.return_per_mae} na={na} kind="ratio" />
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </Card>
  );
}

/** By-market-regime panel for the selected horizon: one row per CONFIGURED regime label (server-driven
 *  from the payload — no hard-coded frontend regime list), each with its n, mean, hit-rate, and downside
 *  risk-adjusted. Low-sample / empty regimes render NA + n. */
function EventStudyRegimeTable({
  rows,
  min,
  horizon,
  subject,
  scope,
  view,
}: {
  rows: EventStudyRegimeRow[];
  min: number;
  horizon: number;
  subject: string;
  scope: SampleScope;
  view: EventStudyView;
}) {
  return (
    <Card className="p-0">
      <PanelTitle
        hint={`How the subject behaves by market regime at the ${horizon}-day horizon. Every configured regime emits a row (read verbatim from the stored snapshots); a regime with n below the minimum shows NA + n, never a fabricated number.`}
      >
        By market regime ({horizon}d)
      </PanelTitle>
      <div className="overflow-x-auto">
        <table data-testid="event-study-regime-table" className="w-full border-collapse text-sm">
          <thead>
            <tr className="border-b border-border text-left text-xs uppercase tracking-wide text-text-faint">
              <th className="px-3 py-2 font-medium">Regime</th>
              <th className="px-3 py-2 text-right font-medium">n</th>
              <th className="px-3 py-2 text-right font-medium">Mean</th>
              <th className="px-3 py-2 text-right font-medium">Hit-rate</th>
              <th className="px-3 py-2 text-right font-medium">Risk-adjusted (downside)</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => {
              const na = row.low_sample || row.n === 0;
              return (
                <tr key={row.regime} className="border-b border-border last:border-b-0">
                  <td className="px-3 py-2 text-text">{row.regime}</td>
                  <td className="px-3 py-2 text-right">
                    <SampleLink
                      n={row.n}
                      min={min}
                      scope={scope}
                      cohort={{ kind: "event-study", subject, horizon, slice: "regime", regime: row.regime, view }}
                      label={`See the ${row.n} ${view === "episodes" ? "episodes" : "occurrences"} in the ${row.regime} regime`}
                    />
                  </td>
                  <td className="px-3 py-2 text-right">
                    <EsValue value={row.mean_return} na={na} kind="pct" />
                  </td>
                  <td className="px-3 py-2 text-right">
                    <EsValue value={row.hit_rate} na={na} kind="rate" />
                  </td>
                  <td className="px-3 py-2 text-right">
                    <EsValue value={row.risk_adjusted} na={na} kind="ratio" />
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </Card>
  );
}

/** By-sector panel for the selected horizon: one row per STORED sector that has occurrences (non-padded —
 *  only sectors with members appear), each with its n, mean, and downside risk-adjusted. Low-sample
 *  sectors render NA + n; an empty slice shows an honest note. */
function EventStudySectorTable({
  rows,
  min,
  horizon,
  subject,
  scope,
  view,
}: {
  rows: EventStudySectorRow[];
  min: number;
  horizon: number;
  subject: string;
  scope: SampleScope;
  view: EventStudyView;
}) {
  return (
    <Card className="p-0">
      <PanelTitle
        hint={`How the subject behaves by sector at the ${horizon}-day horizon. Only sectors with occurrences appear; a sector with n below the minimum shows NA + n, never a fabricated number.`}
      >
        By sector ({horizon}d)
      </PanelTitle>
      {rows.length === 0 ? (
        <p className="px-4 py-4 text-sm text-text-muted">
          No sector has an occurrence of this subject at this horizon.
        </p>
      ) : (
        <div className="overflow-x-auto">
          <table data-testid="event-study-sector-table" className="w-full border-collapse text-sm">
            <thead>
              <tr className="border-b border-border text-left text-xs uppercase tracking-wide text-text-faint">
                <th className="px-3 py-2 font-medium">Sector</th>
                <th className="px-3 py-2 text-right font-medium">n</th>
                <th className="px-3 py-2 text-right font-medium">Mean</th>
                <th className="px-3 py-2 text-right font-medium">Risk-adjusted (downside)</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => {
                const na = row.low_sample || row.n === 0;
                return (
                  <tr key={row.sector} className="border-b border-border last:border-b-0">
                    <td className="px-3 py-2 text-text">{row.sector}</td>
                    <td className="px-3 py-2 text-right">
                      <SampleLink
                        n={row.n}
                        min={min}
                        scope={scope}
                        cohort={{ kind: "event-study", subject, horizon, slice: "sector", sector: row.sector, view }}
                        label={`See the ${row.n} ${view === "episodes" ? "episodes" : "occurrences"} in ${row.sector}`}
                      />
                    </td>
                    <td className="px-3 py-2 text-right">
                      <EsValue value={row.mean_return} na={na} kind="pct" />
                    </td>
                    <td className="px-3 py-2 text-right">
                      <EsValue value={row.risk_adjusted} na={na} kind="ratio" />
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </Card>
  );
}

// --- Regime × Setup × Pattern ranked combinations study (J-77) ------------------------------------
/** A combination row's numeric cell: explicit "NA" (muted) when low-sample / empty / null — never a
 *  fabricated number; otherwise the formatted value (returns + risk-adjusted ratios colour-graded; the
 *  hit-rate stays neutral so a low rate is not painted "good"). The honest n rides the N= chip column. */
function RspCell({
  value,
  stats,
  kind,
}: {
  value: number | null;
  stats: RegimeSetupPatternRow["stats"];
  kind: "pct" | "ratio" | "rate";
}) {
  const na = stats.low_sample || stats.n === 0 || value === null;
  if (na) {
    return (
      <span
        className="num font-semibold text-text-muted"
        title={stats.low_sample ? "Low sample — n below the minimum; NA, not a fabricated number" : "No observations"}
      >
        NA
      </span>
    );
  }
  return (
    <span className={cn("num font-semibold", kind === "rate" ? "text-text" : returnClass(value))}>
      {kind === "ratio" ? fmtRatio(value) : fmtPct(value)}
    </span>
  );
}

/** The client-side sortable column keys for the J-77 table (J-48 view-transform contract — re-orders the
 *  already-served rows only; never refetches or recomputes a stored value). */
type RspSortKey =
  | "regime"
  | "setup"
  | "pattern"
  | "n"
  | "mean"
  | "median"
  | "pct_positive"
  | "expectancy"
  | "return_per_downside_dev"
  | "return_per_mae";

/** The "All" sentinel for the J-82(b) Regime / Setup / Pattern filter dropdowns — a structural value
 *  (never a real regime/setup/pattern), so it can never collide with a config vocabulary entry. */
const RSP_FILTER_ALL = "__all__";

/** Pretty-print a pattern key (snake_case → spaced) and surface the `none` sentinel honestly. */
function patternLabel(pattern: string, none: string): string {
  if (pattern === none) return "— (none)";
  return pattern.replace(/_/g, " ");
}

/** J-82(b) — the three "All"-default Regime / Setup / Pattern filter dropdowns. The vocabulary is the
 *  config-driven payload (`regime_labels` / `setups` / `patterns` + the `pattern_none` sentinel) — no
 *  hardcoded list. Pure view-transform controls (the parent filters the served rows); recomputes nothing. */
function RspFilters({
  data,
  regime,
  setup,
  pattern,
  onRegime,
  onSetup,
  onPattern,
}: {
  data: RegimeSetupPatternResponse;
  regime: string;
  setup: string;
  pattern: string;
  onRegime: (v: string) => void;
  onSetup: (v: string) => void;
  onPattern: (v: string) => void;
}) {
  return (
    <>
      <label className="flex flex-col gap-1">
        <span className="text-xs uppercase tracking-wide text-text-faint">Regime</span>
        <Select
          data-testid="rsp-regime-filter"
          aria-label="Filter by regime"
          value={regime}
          onChange={(e) => onRegime(e.target.value)}
          className="w-44"
        >
          <option value={RSP_FILTER_ALL}>All regimes</option>
          {data.regime_labels.map((r) => (
            <option key={r} value={r}>
              {r}
            </option>
          ))}
        </Select>
      </label>
      <label className="flex flex-col gap-1">
        <span className="text-xs uppercase tracking-wide text-text-faint">Setup</span>
        <Select
          data-testid="rsp-setup-filter"
          aria-label="Filter by setup"
          value={setup}
          onChange={(e) => onSetup(e.target.value)}
          className="w-44"
        >
          <option value={RSP_FILTER_ALL}>All setups</option>
          {data.setups.map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </Select>
      </label>
      <label className="flex flex-col gap-1">
        <span className="text-xs uppercase tracking-wide text-text-faint">Pattern</span>
        <Select
          data-testid="rsp-pattern-filter"
          aria-label="Filter by pattern"
          value={pattern}
          onChange={(e) => onPattern(e.target.value)}
          className="w-44"
        >
          <option value={RSP_FILTER_ALL}>All patterns</option>
          {/* config pattern keys + the `none` sentinel (rendered honestly as "— (none)"). */}
          {data.patterns.map((p) => (
            <option key={p} value={p}>
              {patternLabel(p, data.pattern_none)}
            </option>
          ))}
          <option value={data.pattern_none}>{patternLabel(data.pattern_none, data.pattern_none)}</option>
        </Select>
      </label>
    </>
  );
}

/** The Regime × Setup × Pattern study section (J-77): a ranked, client-side-sortable table — each row a
 *  (regime, setup, pattern) combination with n, mean, median, hit-rate, expectancy, and BOTH downside
 *  risk-adjusted figures at the selected horizon; default ranked by the downside risk-adjusted return (the
 *  server order). Reuses the page's shared `horizon` + `asofCutoff` (no second date/horizon state) plus its
 *  OWN Episodes ⇄ Pooled view toggle (J-63). Its OWN independent read-only data source + loading state, so
 *  no single slow query blocks the page (J-15/J-72). Each row's N= chip opens the samples drill-down for
 *  that exact combination in a NEW tab (J-65, `?asof` stamped J-50). Low-sample/empty cells show NA + n;
 *  the survivorship-bias label persists. Re-formats the payload only — recomputes nothing. */
export function RegimeSetupPatternLab({
  horizon,
  asofCutoff,
  scope,
  onMeta,
}: {
  horizon: number | undefined;
  asofCutoff: string | null;
  scope: SampleScope;
  onMeta?: (meta: LabMeta) => void;
}) {
  // J-82(d): the RSP section defaults to POOLED (Episodes one click away) — scoped to THIS section's own
  // toggle initial state only; the rest of /research (the event study, J-29/J-63) keeps its Episodes
  // default, and the canonical `compute_regime_setup_pattern_study` default param is untouched.
  const [view, setView] = useState<EventStudyView>("pooled");
  const [data, setData] = useState<RegimeSetupPatternResponse | null>(null);
  const [status, setStatus] = useState<"loading" | "ok" | "error">("loading");
  // J-48 client-side sort state. Default: the stored server order (ranked by risk-adjusted return) — a
  // null sortKey means "as served", so the default order stays the engine's rank (a view transform only).
  const [sortKey, setSortKey] = useState<RspSortKey | null>(null);
  const [sortDir, setSortDir] = useState<"asc" | "desc">("desc");
  // J-82(b): three client-side filter dropdowns (Regime / Setup / Pattern), each defaulting to "All"
  // (the RSP_FILTER_ALL sentinel). Pure view transforms (J-56/J-48 contract) over the already-served rows
  // — they compose with the sort and recompute/refetch nothing. The vocabulary comes from the config-driven
  // payload fields (`regime_labels` / `setups` / `patterns` / `pattern_none`) — no hardcoded list.
  const [regimeFilter, setRegimeFilter] = useState<string>(RSP_FILTER_ALL);
  const [setupFilter, setSetupFilter] = useState<string>(RSP_FILTER_ALL);
  const [patternFilter, setPatternFilter] = useState<string>(RSP_FILTER_ALL);

  useEffect(() => {
    const controller = new AbortController();
    setStatus("loading");
    fetchRegimeSetupPattern(horizon, asofCutoff ?? undefined, view, controller.signal)
      .then((d) => {
        if (controller.signal.aborted) return;
        setData(d);
        setStatus("ok");
        onMeta?.({ horizons: d.horizons, default_horizon: d.default_horizon });
      })
      .catch(() => {
        if (!controller.signal.aborted) setStatus("error");
      });
    return () => controller.abort();
  }, [horizon, asofCutoff, view]);

  const hasAny = data ? data.rows.some((r) => r.stats.n > 0) : false;

  // J-82(b): apply the three "All"-default filter dropdowns FIRST — a pure view transform (J-56/J-48
  // contract) over the already-served rows. An "All" sentinel passes every row; a selected value narrows
  // to the matching regime / setup / pattern. Composes with the sort below; recomputes/refetches nothing.
  const filteredRows = data
    ? data.rows.filter(
        (r) =>
          (regimeFilter === RSP_FILTER_ALL || r.regime === regimeFilter) &&
          (setupFilter === RSP_FILTER_ALL || r.setup === setupFilter) &&
          (patternFilter === RSP_FILTER_ALL || r.pattern === patternFilter),
      )
    : [];

  // J-48 + J-82(a): a pure client-side stable re-order of the FILTERED served rows (never a refetch/
  // recompute). The label columns (regime/setup/pattern) and the always-present `n` sort directly; every
  // NUMERIC STAT column treats a cell as NA using the SAME predicate the cell DISPLAY (`RspCell`) uses —
  // `low_sample || n === 0 || value === null` — so every DISPLAYED-NA row sinks LAST in both directions
  // (a low-sample row whose raw mean is a real number still DISPLAYS NA, so it must SORT NA too — the
  // J-82(a) reconciliation). Present values sort numerically, labels lexically, with a stable tie-break
  // preserving the served rank.
  const sortedRows = (() => {
    if (!data) return [];
    if (sortKey === null) return filteredRows; // default = the served (risk-adjusted-ranked) order
    const sign = sortDir === "asc" ? 1 : -1;
    // The displayed value for the active column, or `null` when the cell DISPLAYS as NA (same predicate
    // as `RspCell`). Label columns and `n` are never display-NA. A numeric stat is NA when the row is
    // low-sample, empty, or the value itself is null.
    const displayedValue = (r: RegimeSetupPatternRow): string | number | null => {
      switch (sortKey) {
        case "regime": return r.regime;
        case "setup": return r.setup;
        case "pattern": return r.pattern;
        case "n": return r.stats.n;
        default: {
          const raw = r.stats[sortKey];
          // SAME NA predicate as the cell display (RspCell) — a low-sample / empty / null cell is NA.
          if (r.stats.low_sample || r.stats.n === 0 || raw === null) return null;
          return raw;
        }
      }
    };
    return filteredRows
      .map((row, index) => ({ row, index }))
      .sort((a, b) => {
        const av = displayedValue(a.row);
        const bv = displayedValue(b.row);
        // displayed-NA (null) always sorts last regardless of direction
        if (av === null && bv === null) return a.index - b.index;
        if (av === null) return 1;
        if (bv === null) return -1;
        let primary: number;
        if (typeof av === "string" && typeof bv === "string") primary = av.localeCompare(bv) * sign;
        else primary = ((av as number) - (bv as number)) * sign;
        return primary !== 0 ? primary : a.index - b.index; // stable tie-break
      })
      .map((e) => e.row);
  })();

  const onSort = (key: RspSortKey) => {
    if (sortKey === key) {
      setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    } else {
      setSortKey(key);
      // numeric columns default to descending (best-first); label columns ascending.
      setSortDir(key === "regime" || key === "setup" || key === "pattern" ? "asc" : "desc");
    }
  };

  return (
    <Card className="p-0" data-testid="regime-setup-pattern-section">
      <PanelTitle
        hint={`Which (market regime × setup × detected pattern) combinations have historically led to the strongest (downside risk-adjusted) ${data?.horizon ?? ""}-day forward returns? A ranked grouping of the SAME stored event-study observations (one observation per stored snapshot occurrence) — descriptive evidence, never a fitted model. Columns are client-side sortable; combinations with n < ${data?.min_sample ?? "min"} show NA + n, never a fabricated number. Each N= chip opens the exact observations in a new tab.`}
      >
        Regime × Setup × Pattern — ranked combinations
      </PanelTitle>
      <div className="space-y-4 p-4">
        <div className="flex flex-wrap items-end gap-3">
          <EventStudyViewToggle view={view} onChange={setView} />
          {/* J-82(b): the three "All"-default Regime / Setup / Pattern filter dropdowns — config-driven
              vocabulary from the payload; pure view transforms composing with the sort. */}
          {data ? (
            <RspFilters
              data={data}
              regime={regimeFilter}
              setup={setupFilter}
              pattern={patternFilter}
              onRegime={setRegimeFilter}
              onSetup={setSetupFilter}
              onPattern={setPatternFilter}
            />
          ) : null}
          <p className="max-w-md text-xs text-text-faint">
            Re-uses the page&apos;s shared horizon selector and analysis-mode toggle above — no date control
            of its own (the single global as-of drives any point-in-time scoping, J-18). Pooled (default for
            this section) counts every signal-day; Episodes counts each continuous run of a symbol once at
            its first trigger. An observation matching two patterns appears under both; one matching none
            appears under &ldquo;— (none)&rdquo;.
          </p>
        </div>

        {data ? (
          <CaveatBanner survivorship={data.survivorship_bias} descriptive={data.descriptive_caveat} />
        ) : null}

        {status === "error" ? (
          <div className="flex items-center gap-3 rounded-md border border-neg bg-surface p-4 text-sm text-neg">
            <AlertTriangle className="h-5 w-5 shrink-0" aria-hidden />
            <div>
              <p className="font-medium">Backend unavailable</p>
              <p className="text-text-muted">
                The combinations study could not load from the API. No figures are shown rather than
                fabricated values — confirm the backend is running and retry.
              </p>
            </div>
          </div>
        ) : !data ? (
          <CombinationSkeleton />
        ) : !hasAny ? (
          <EmptyState
            icon={Microscope}
            title="No forward-tested combinations for this horizon"
            description="No stored snapshot has an observation with a realized forward return at this horizon. Pick a shorter horizon — no combination is fabricated to fill the gap."
          />
        ) : sortedRows.length === 0 ? (
          // J-82(b): an honest empty-after-filter state — the served set has rows, but the active
          // Regime/Setup/Pattern filters match none. The published cohort total is unchanged; clearing
          // a filter restores rows. Never a fabricated row.
          <EmptyState
            icon={Microscope}
            title="No combinations match these filters"
            description="No (regime, setup, pattern) combination matches the current filter selection. Reset a filter to “All” to widen the view — nothing is fabricated to fill the gap."
          />
        ) : (
          <RegimeSetupPatternTable
            rows={sortedRows}
            data={data}
            view={view}
            scope={scope}
            sortKey={sortKey}
            sortDir={sortDir}
            onSort={onSort}
            dim={status === "loading"}
          />
        )}
      </div>
    </Card>
  );
}

/** A sortable column header button (J-48): clicking re-orders the already-served rows; the active column
 *  shows its direction arrow. Kept a plain button (no nested interactive element besides the optional
 *  glossary TermInfo, which sits OUTSIDE the button). */
function RspSortHeader({
  label,
  col,
  sortKey,
  sortDir,
  onSort,
  align = "right",
  term,
}: {
  label: string;
  col: RspSortKey;
  sortKey: RspSortKey | null;
  sortDir: "asc" | "desc";
  onSort: (key: RspSortKey) => void;
  align?: "left" | "right";
  term?: string;
}) {
  const active = sortKey === col;
  return (
    <th className={cn("px-3 py-2 font-medium", align === "right" ? "text-right" : "text-left")}>
      <span className={cn("inline-flex items-center gap-1", align === "right" && "justify-end")}>
        <button
          type="button"
          onClick={() => onSort(col)}
          aria-label={`Sort by ${label}`}
          data-testid={`rsp-sort-${col}`}
          className={cn(
            "inline-flex items-center gap-1 rounded-sm hover:text-text",
            "focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-accent",
            active ? "text-accent" : "text-text-faint",
          )}
        >
          {label}
          <span aria-hidden className="text-[10px]">{active ? (sortDir === "asc" ? "▲" : "▼") : "↕"}</span>
        </button>
        {term ? <TermInfo term={term} /> : null}
      </span>
    </th>
  );
}

function RegimeSetupPatternTable({
  rows,
  data,
  view,
  scope,
  sortKey,
  sortDir,
  onSort,
  dim,
}: {
  rows: RegimeSetupPatternRow[];
  data: RegimeSetupPatternResponse;
  view: EventStudyView;
  scope: SampleScope;
  sortKey: RspSortKey | null;
  sortDir: "asc" | "desc";
  onSort: (key: RspSortKey) => void;
  dim: boolean;
}) {
  const min = data.min_sample;
  const horizon = data.horizon;
  return (
    <div className={cn("overflow-x-auto transition-opacity", dim && "opacity-60")} aria-busy={dim}>
      <table data-testid="regime-setup-pattern-table" className="w-full border-collapse text-sm">
        <thead>
          <tr className="border-b border-border text-left text-xs uppercase tracking-wide text-text-faint">
            <RspSortHeader label="Regime" col="regime" sortKey={sortKey} sortDir={sortDir} onSort={onSort} align="left" />
            <RspSortHeader label="Setup" col="setup" sortKey={sortKey} sortDir={sortDir} onSort={onSort} align="left" term="setup status" />
            <RspSortHeader label="Pattern" col="pattern" sortKey={sortKey} sortDir={sortDir} onSort={onSort} align="left" />
            <RspSortHeader label="n" col="n" sortKey={sortKey} sortDir={sortDir} onSort={onSort} term="n (sample size)" />
            <RspSortHeader label="Mean" col="mean" sortKey={sortKey} sortDir={sortDir} onSort={onSort} />
            <RspSortHeader label="Median" col="median" sortKey={sortKey} sortDir={sortDir} onSort={onSort} term="median" />
            <RspSortHeader label="Hit-rate" col="pct_positive" sortKey={sortKey} sortDir={sortDir} onSort={onSort} term="hit-rate" />
            <RspSortHeader label="Expectancy" col="expectancy" sortKey={sortKey} sortDir={sortDir} onSort={onSort} term="expectancy" />
            {/* J-86 — the aggregate mean max-drawdown column (non-sortable; read-only over stored values). */}
            <th className="px-3 py-2 text-right font-medium">
              <span className="inline-flex items-center justify-end gap-1">Mean MDD<TermInfo term="max drawdown" /></span>
            </th>
            <RspSortHeader label="Return / downside-dev" col="return_per_downside_dev" sortKey={sortKey} sortDir={sortDir} onSort={onSort} term="return / downside-dev" />
            <RspSortHeader label="Return / MAE" col="return_per_mae" sortKey={sortKey} sortDir={sortDir} onSort={onSort} term="return / MAE" />
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr
              key={`${row.regime}|${row.setup}|${row.pattern}`}
              className="border-b border-border last:border-b-0"
            >
              <td className="px-3 py-2 text-text">{row.regime}</td>
              <td className="px-3 py-2 text-text">{row.setup}</td>
              <td className="px-3 py-2 text-text-muted">{patternLabel(row.pattern, data.pattern_none)}</td>
              <td className="px-3 py-2 text-right">
                <SampleLink
                  n={row.stats.n}
                  min={min}
                  scope={scope}
                  cohort={{
                    kind: "regime-setup-pattern",
                    horizon,
                    regime: row.regime,
                    setup: row.setup,
                    pattern: row.pattern,
                    view,
                  }}
                  label={`See the ${row.stats.n} observations for ${row.regime} · ${row.setup} · ${patternLabel(row.pattern, data.pattern_none)}`}
                />
              </td>
              <td className="px-3 py-2 text-right">
                <RspCell value={row.stats.mean} stats={row.stats} kind="pct" />
              </td>
              <td className="px-3 py-2 text-right">
                <RspCell value={row.stats.median} stats={row.stats} kind="pct" />
              </td>
              <td className="px-3 py-2 text-right">
                <RspCell value={row.stats.pct_positive} stats={row.stats} kind="rate" />
              </td>
              <td className="px-3 py-2 text-right">
                <RspCell value={row.stats.expectancy} stats={row.stats} kind="pct" />
              </td>
              {/* J-86 — the aggregate mean max-drawdown cell (NA + low-sample gated like the others). */}
              <td className="px-3 py-2 text-right">
                <RspCell value={row.stats.mean_max_drawdown} stats={row.stats} kind="pct" />
              </td>
              <td className="px-3 py-2 text-right">
                <RspCell value={row.stats.return_per_downside_dev} stats={row.stats} kind="ratio" />
              </td>
              <td className="px-3 py-2 text-right">
                <RspCell value={row.stats.return_per_mae} stats={row.stats} kind="ratio" />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// ==================================================================================================
// J-90 — Recovery-Turn Edge lab. The per-horizon forward-return edge of ENTERING at causal recovery-turn
// dates (from the read-only market_phase derivation, never recomputed), conditioned on the causal
// signal-date phase. Its OWN read-only data source + loading state, reusing the page's shared `horizon` +
// `asofCutoff` (no second date/horizon state) plus its own Episodes ⇄ Pooled view toggle. Forward-return
// evidence only — NO order/execution affordance.
// ==================================================================================================
export function RecoveryTurnEdgeLab({
  horizon,
  asofCutoff,
  scope,
  onMeta,
}: {
  horizon: number | undefined;
  asofCutoff: string | null;
  scope: SampleScope;
  onMeta?: (meta: LabMeta) => void;
}) {
  // J-63: the overlap-honesty view — Episodes (first-trigger, DEFAULT) ⇄ Pooled. A local MODE/cohort state,
  // fully INDEPENDENT of `asofCutoff` and the page analysis-mode `scope` (NOT a date — no second date state).
  const [view, setView] = useState<EventStudyView>("episodes");
  const [data, setData] = useState<RecoveryTurnEdgeResponse | null>(null);
  const [status, setStatus] = useState<"loading" | "ok" | "error">("loading");

  useEffect(() => {
    const controller = new AbortController();
    setStatus("loading");
    fetchRecoveryTurnEdge(horizon, asofCutoff ?? undefined, view, controller.signal)
      .then((d) => {
        if (controller.signal.aborted) return;
        setData(d);
        setStatus("ok");
        onMeta?.({ horizons: d.horizons, default_horizon: d.default_horizon });
      })
      .catch(() => {
        if (!controller.signal.aborted) setStatus("error");
      });
    return () => controller.abort();
  }, [horizon, asofCutoff, view]);

  const hasAny = data ? data.by_horizon.some((r) => r.n > 0) : false;

  return (
    <Card className="p-0" data-testid="recovery-turn-edge-section">
      <PanelTitle
        hint={`When the market causally turns up out of a downtrend (filtered P(bear) crosses below the recovery exit while the index reclaims its trailing MA), what forward-return edge has entering at those dates historically shown? A read-only aggregation of the stored forward returns of the recovery-turn signal dates, conditioned on the causal phase at the signal date — descriptive evidence, never a forecast and never an order. Columns are client-side sortable; cohorts with n < ${data?.min_sample ?? "min"} show NA + n. Each N= chip opens the exact observations in a new tab.`}
      >
        Recovery-Turn Edge — forward returns after a causal turn
      </PanelTitle>
      <div className="space-y-4 p-4">
        <div className="flex flex-wrap items-end gap-3">
          <EventStudyViewToggle view={view} onChange={setView} />
          <p className="max-w-md text-xs text-text-faint">
            Re-uses the page&apos;s shared horizon selector and analysis-mode toggle above — no date control
            of its own (the single global as-of drives any point-in-time scoping, J-18). Episodes (default)
            counts each continuous run of a symbol once at its first trigger; Pooled counts every signal-day.
            Forward-return evidence only — there is no order or execution affordance.
          </p>
        </div>

        {data ? (
          <RecoveryTurnDisclosure data={data} />
        ) : null}

        {data ? (
          <CaveatBanner survivorship={data.survivorship_bias} descriptive={data.descriptive_caveat} />
        ) : null}

        {status === "error" ? (
          <div className="flex items-center gap-3 rounded-md border border-neg bg-surface p-4 text-sm text-neg">
            <AlertTriangle className="h-5 w-5 shrink-0" aria-hidden />
            <div>
              <p className="font-medium">Backend unavailable</p>
              <p className="text-text-muted">
                The Recovery-Turn Edge study could not load from the API. No figures are shown rather than
                fabricated values — confirm the backend is running and retry.
              </p>
            </div>
          </div>
        ) : !data ? (
          <CombinationSkeleton />
        ) : data.signal_count === 0 || !hasAny ? (
          <EmptyState
            icon={Microscope}
            title="No causal recovery turns with forward-tested returns yet"
            description="No stored snapshot is a causal recovery-turn signal date with a realized forward return at this horizon / window. Pick a shorter horizon or widen the analysis mode — no edge is fabricated to fill the gap."
          />
        ) : (
          <RecoveryTurnEdgeBody data={data} dim={status === "loading"} scope={scope} view={data.view} />
        )}
      </div>
    </Card>
  );
}

/** The disclosure line for the Recovery-Turn Edge study: the resolved view, the cohort n at the selected
 *  horizon, the distinct unique symbols, and the count of distinct causal recovery-turn signal dates —
 *  read VERBATIM from the payload (number formatting only). */
function RecoveryTurnDisclosure({ data }: { data: RecoveryTurnEdgeResponse }) {
  const isEpisodes = data.view === "episodes";
  return (
    <div
      data-testid="recovery-turn-disclosure"
      className="flex flex-wrap items-center gap-x-6 gap-y-1 rounded-md border border-border bg-surface-2 px-3 py-2 text-xs text-text-muted"
    >
      <span className="inline-flex items-center gap-1">
        <span className="text-text-faint">View:</span>
        <span className="font-semibold text-text">{isEpisodes ? "Episodes" : "Pooled"}</span>
      </span>
      <span>
        <span className="text-text-faint">n ({data.horizon}d): </span>
        <span className="num font-semibold text-text" data-testid="recovery-disclosure-n">{data.n}</span>
      </span>
      <span>
        <span className="text-text-faint">Unique symbols: </span>
        <span className="num font-semibold text-text">{data.unique_symbols}</span>
      </span>
      <span>
        <span className="text-text-faint">Recovery-turn signal dates: </span>
        <span className="num font-semibold text-text" data-testid="recovery-signal-count">
          {data.signal_count}
        </span>
      </span>
      <span>
        <span className="text-text-faint">Best exit-horizon: </span>
        <span className="num font-semibold text-text">
          {data.best_exit_horizon === null ? "NA" : `${data.best_exit_horizon}d`}
        </span>
      </span>
    </div>
  );
}

function RecoveryTurnEdgeBody({
  data,
  dim,
  scope,
  view,
}: {
  data: RecoveryTurnEdgeResponse;
  dim: boolean;
  scope: SampleScope;
  view: EventStudyView;
}) {
  return (
    <div className={cn("space-y-4 transition-opacity", dim && "opacity-60")} aria-busy={dim}>
      <p className="text-xs text-text-faint">
        Rows with <span className="text-warn">n &lt; {data.min_sample} ⚠</span> render NA. Risk is
        downside-only everywhere (return ÷ downside-deviation and return ÷ mean-|MAE| — never total
        volatility); the aggregate max-drawdown column is read verbatim from the stored excursions.
      </p>
      <RecoveryTurnHorizonTable
        rows={data.by_horizon}
        min={data.min_sample}
        bestExit={data.best_exit_horizon}
        scope={scope}
        view={view}
      />
      <RecoveryTurnPhaseTable
        rows={data.by_phase}
        min={data.min_sample}
        horizon={data.horizon}
        scope={scope}
        view={view}
      />
    </div>
  );
}

/** The per-horizon distribution / exit-horizon curve for the recovery-turn cohort — identical column set to
 *  the event-study horizon table (reusing `EsValue`), with each row's `n` a SampleLink into the recovery-turn
 *  drill-down at that horizon (J-65 — new tab, count-coherent). The best exit-horizon row is highlighted. */
function RecoveryTurnHorizonTable({
  rows,
  min,
  bestExit,
  scope,
  view,
}: {
  rows: RecoveryTurnEdgeHorizonRow[];
  min: number;
  bestExit: number | null;
  scope: SampleScope;
  view: EventStudyView;
}) {
  return (
    <Card className="p-0">
      <PanelTitle hint="One row per forward horizon (the exit-horizon curve) for the recovery-turn cohort: the forward-return distribution, per-occurrence expectancy, mean MAE / MFE, the aggregate max-drawdown, and BOTH downside-only risk-adjusted ratios. The best exit-horizon (highest downside-risk-adjusted return among non-low-sample horizons) is highlighted; rows with n below the minimum render NA + n. Each N= chip opens the exact observations in a new tab.">
        Per-horizon edge &amp; exit-horizon curve
      </PanelTitle>
      <div className="overflow-x-auto">
        <table data-testid="recovery-turn-horizon-table" className="w-full border-collapse text-sm">
          <thead>
            <tr className="border-b border-border text-left text-xs uppercase tracking-wide text-text-faint">
              <th className="px-3 py-2 font-medium">
                <span className="inline-flex items-center gap-1">Horizon<TermInfo term="horizon" /></span>
              </th>
              <th className="px-3 py-2 text-right font-medium">
                <span className="inline-flex items-center gap-1">n<TermInfo term="n (sample size)" /></span>
              </th>
              <th className="px-3 py-2 text-right font-medium">Mean</th>
              <th className="px-3 py-2 text-right font-medium">
                <span className="inline-flex items-center gap-1">Median<TermInfo term="median" /></span>
              </th>
              <th className="px-3 py-2 text-right font-medium">
                <span className="inline-flex items-center gap-1">% Positive<TermInfo term="% positive" /></span>
              </th>
              <th className="px-3 py-2 text-right font-medium">
                <span className="inline-flex items-center gap-1">Expectancy<TermInfo term="expectancy" /></span>
              </th>
              <th className="px-3 py-2 text-right font-medium">
                <span className="inline-flex items-center gap-1">Mean MAE<TermInfo term="MAE" /></span>
              </th>
              <th className="px-3 py-2 text-right font-medium">
                <span className="inline-flex items-center gap-1">Mean MFE<TermInfo term="MFE" /></span>
              </th>
              <th className="px-3 py-2 text-right font-medium">
                <span className="inline-flex items-center gap-1">Mean MDD<TermInfo term="max drawdown" /></span>
              </th>
              <th className="px-3 py-2 text-right font-medium">
                <span className="inline-flex items-center gap-1">Return / downside-dev<TermInfo term="return / downside-dev" /></span>
              </th>
              <th className="px-3 py-2 text-right font-medium">
                <span className="inline-flex items-center gap-1">Return / MAE<TermInfo term="return / MAE" /></span>
              </th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => {
              const na = row.low_sample || row.n === 0;
              const best = bestExit !== null && row.horizon === bestExit;
              return (
                <tr
                  key={row.horizon}
                  className={cn("border-b border-border last:border-b-0", best && "bg-surface-2")}
                >
                  <td className="px-3 py-2">
                    <span className="num font-semibold text-text">{row.horizon}d</span>
                    {best ? (
                      <span className="ml-2 rounded border border-accent px-1.5 py-0.5 text-xs font-medium text-accent">
                        best exit
                      </span>
                    ) : null}
                  </td>
                  <td className="px-3 py-2 text-right">
                    <SampleLink
                      n={row.n}
                      min={min}
                      scope={scope}
                      cohort={{ kind: "recovery-turn", horizon: row.horizon, slice: "total", view }}
                      label={`See the ${row.n} recovery-turn observations at the ${row.horizon}-day horizon`}
                    />
                  </td>
                  <td className="px-3 py-2 text-right"><EsValue value={row.mean_return} na={na} kind="pct" /></td>
                  <td className="px-3 py-2 text-right"><EsValue value={row.median} na={na} kind="pct" /></td>
                  <td className="px-3 py-2 text-right"><EsValue value={row.pct_positive} na={na} kind="rate" /></td>
                  <td className="px-3 py-2 text-right"><EsValue value={row.expectancy.expectancy} na={na} kind="pct" /></td>
                  <td className="px-3 py-2 text-right"><EsValue value={row.mean_mae} na={na} kind="pct" /></td>
                  <td className="px-3 py-2 text-right"><EsValue value={row.mean_mfe} na={na} kind="pct" /></td>
                  <td className="px-3 py-2 text-right"><EsValue value={row.mean_max_drawdown} na={na} kind="pct" /></td>
                  <td className="px-3 py-2 text-right"><EsValue value={row.return_per_downside_dev} na={na} kind="ratio" /></td>
                  <td className="px-3 py-2 text-right"><EsValue value={row.return_per_mae} na={na} kind="ratio" /></td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </Card>
  );
}

type RecoveryPhaseSortKey = "phase" | "n" | "mean_return" | "hit_rate" | "risk_adjusted";

/** The by-signal-phase conditioning table (selected horizon): one row per CONFIGURED market-phase label
 *  (server-driven), each with its n (a SampleLink into the by-phase drill-down — count-coherent, new tab),
 *  mean, hit-rate, and downside risk-adjusted. Client-side sortable (J-48 view transform). Low-sample /
 *  null cells render NA + n. */
function RecoveryTurnPhaseTable({
  rows,
  min,
  horizon,
  scope,
  view,
}: {
  rows: RecoveryTurnEdgePhaseRow[];
  min: number;
  horizon: number;
  scope: SampleScope;
  view: EventStudyView;
}) {
  const [sortKey, setSortKey] = useState<RecoveryPhaseSortKey | null>(null);
  const [sortDir, setSortDir] = useState<"asc" | "desc">("desc");

  const onSort = (key: RecoveryPhaseSortKey) => {
    if (sortKey === key) {
      setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    } else {
      setSortKey(key);
      setSortDir(key === "phase" ? "asc" : "desc");
    }
  };

  const sorted = (() => {
    if (sortKey === null) return rows; // server order (config.market_phase.labels)
    const sign = sortDir === "asc" ? 1 : -1;
    const value = (r: RecoveryTurnEdgePhaseRow): string | number | null => {
      switch (sortKey) {
        case "phase": return r.phase;
        case "n": return r.n;
        default: {
          const raw = r[sortKey];
          if (r.low_sample || r.n === 0 || raw === null) return null; // SAME NA predicate as the cell
          return raw;
        }
      }
    };
    return rows
      .map((row, index) => ({ row, index }))
      .sort((a, b) => {
        const av = value(a.row);
        const bv = value(b.row);
        if (av === null && bv === null) return a.index - b.index;
        if (av === null) return 1; // NA always last
        if (bv === null) return -1;
        let primary: number;
        if (typeof av === "string" && typeof bv === "string") primary = av.localeCompare(bv) * sign;
        else primary = ((av as number) - (bv as number)) * sign;
        return primary !== 0 ? primary : a.index - b.index;
      })
      .map((e) => e.row);
  })();

  const header = (label: string, col: RecoveryPhaseSortKey, align: "left" | "right" = "right", term?: string) => {
    const active = sortKey === col;
    return (
      <th className={cn("px-3 py-2 font-medium", align === "right" ? "text-right" : "text-left")}>
        <span className={cn("inline-flex items-center gap-1", align === "right" && "justify-end")}>
          <button
            type="button"
            onClick={() => onSort(col)}
            aria-label={`Sort by ${label}`}
            data-testid={`recovery-phase-sort-${col}`}
            className={cn(
              "inline-flex items-center gap-1 rounded-sm hover:text-text",
              "focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-accent",
              active ? "text-accent" : "text-text-faint",
            )}
          >
            {label}
            <span aria-hidden className="text-[10px]">{active ? (sortDir === "asc" ? "▲" : "▼") : "↕"}</span>
          </button>
          {term ? <TermInfo term={term} /> : null}
        </span>
      </th>
    );
  };

  return (
    <Card className="p-0">
      <PanelTitle hint="Conditions the recovery-turn edge on the CAUSAL market phase at the signal date: one row per configured phase label, each with its n, mean, hit-rate, and downside risk-adjusted return at the selected horizon. Columns are client-side sortable; low-sample cells render NA + n. Each N= chip opens the exact observations in a new tab.">
        Edge by phase at the signal date ({horizon}d)
      </PanelTitle>
      <div className="overflow-x-auto">
        <table data-testid="recovery-turn-phase-table" className="w-full border-collapse text-sm">
          <thead>
            <tr className="border-b border-border text-left text-xs uppercase tracking-wide text-text-faint">
              {header("Phase at signal", "phase", "left")}
              {header("n", "n", "right", "n (sample size)")}
              {header("Mean", "mean_return", "right")}
              {header("Hit-rate", "hit_rate", "right", "hit-rate")}
              {header("Return / downside-dev", "risk_adjusted", "right", "return / downside-dev")}
            </tr>
          </thead>
          <tbody>
            {sorted.map((row) => {
              const na = row.low_sample || row.n === 0;
              return (
                <tr key={row.phase} className="border-b border-border last:border-b-0">
                  <td className="px-3 py-2 text-text">{row.phase}</td>
                  <td className="px-3 py-2 text-right">
                    <SampleLink
                      n={row.n}
                      min={min}
                      scope={scope}
                      cohort={{ kind: "recovery-turn", horizon, slice: "phase", phase: row.phase, view }}
                      label={`See the ${row.n} recovery-turn observations with a ${row.phase} phase at the signal date`}
                    />
                  </td>
                  <td className="px-3 py-2 text-right"><EsValue value={row.mean_return} na={na} kind="pct" /></td>
                  <td className="px-3 py-2 text-right"><EsValue value={row.hit_rate} na={na} kind="rate" /></td>
                  <td className="px-3 py-2 text-right"><EsValue value={row.risk_adjusted} na={na} kind="ratio" /></td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </Card>
  );
}

// ==================================================================================================
// iter-32 (J-91) — Downtrend Opportunity lab. Conditions the existing forward-return evidence on the
// CAUSAL as-of downtrend state (phase / severity band / P(bear) band, all <= D) and renders three angles
// side by side: (a) held-up-best, (b) fell-hardest (EVIDENCE ONLY — no order/execution affordance), and
// (c) the reused J-90 recovery-turn edge by phase. Conditioning controls (the dimension selector), the
// Episodes ⇄ Pooled toggle, client-side sortable ranked tables, N= chips → count-coherent samples in a new
// tab, NA + n on low-sample, the survivorship caveat, and the J-92 publication-lag limitation label.
// ==================================================================================================
const _DIMENSION_LABELS: Record<string, string> = {
  phase: "Phase",
  severity_band: "Severity band",
  pbear_band: "P(bear) band",
};

export function DowntrendOpportunityLab({
  horizon,
  asofCutoff,
  scope,
  onMeta,
}: {
  horizon: number | undefined;
  asofCutoff: string | null;
  scope: SampleScope;
  onMeta?: (meta: LabMeta) => void;
}) {
  // J-63: the overlap-honesty view (Episodes default ⇄ Pooled). A local MODE/cohort state, INDEPENDENT of
  // `asofCutoff` and the page analysis-mode `scope` (NOT a date — no second date state, J-18).
  const [view, setView] = useState<EventStudyView>("episodes");
  // the conditioning DIMENSION currently shown (phase | severity_band | pbear_band). A local cohort/view
  // selector — NOT a date control (J-18). Default: the first dimension the payload lists.
  const [dimension, setDimension] = useState<string | null>(null);
  const [data, setData] = useState<DowntrendOpportunityResponse | null>(null);
  const [status, setStatus] = useState<"loading" | "ok" | "error">("loading");

  useEffect(() => {
    const controller = new AbortController();
    setStatus("loading");
    fetchDowntrendOpportunity(horizon, asofCutoff ?? undefined, view, controller.signal)
      .then((d) => {
        if (controller.signal.aborted) return;
        setData(d);
        setStatus("ok");
        onMeta?.({ horizons: d.horizons, default_horizon: d.default_horizon });
      })
      .catch(() => {
        if (!controller.signal.aborted) setStatus("error");
      });
    return () => controller.abort();
  }, [horizon, asofCutoff, view]);

  const activeDimension = dimension ?? data?.dimensions[0] ?? "phase";
  const hasAny = data ? data.held_up_best.some((r) => r.stats.n > 0) : false;

  return (
    <Card className="p-0" data-testid="downtrend-opportunity-section">
      <PanelTitle
        hint={`Condition the SAME stored forward-return evidence on the CAUSAL as-of downtrend state at each observation's snapshot date — the market phase, the drawdown-severity band, or the filtered P(bear) band, all observed from <= that date (never a future bar, never the smoothed retrospective). Three angles: what held up best, what fell hardest (research EVIDENCE ONLY — there is no order or short-deployment path), and the recovery-turn edge. A read-only grouping of stored returns — descriptive, never a forecast. Columns are client-side sortable; cohorts with n < ${data?.min_sample ?? "min"} show NA + n. Each N= chip opens the exact observations in a new tab.`}
      >
        Downtrend Opportunity — forward returns conditioned on the causal downtrend state
      </PanelTitle>
      <div className="space-y-4 p-4">
        <div className="flex flex-wrap items-end gap-3">
          <EventStudyViewToggle view={view} onChange={setView} />
          {data ? (
            <DowntrendDimensionSelector
              dimensions={data.dimensions}
              value={activeDimension}
              onChange={setDimension}
            />
          ) : null}
          <p className="max-w-md text-xs text-text-faint">
            Re-uses the page&apos;s shared horizon selector and analysis-mode toggle above — no date control
            of its own (the single global as-of drives any point-in-time scoping, J-18). The conditioning
            dimension + Episodes/Pooled are cohort modes, not dates. Forward-return evidence only — there is
            no order or execution affordance, including on the weakness angle.
          </p>
        </div>

        {data ? (
          <CaveatBanner survivorship={data.survivorship_bias} descriptive={data.descriptive_caveat} />
        ) : null}

        {/* J-92: the macro inputs that COULD feed this study are config-default-OFF, so today's figures are
            the price/breadth/VIX-only path. Whenever a macro-conditioned figure IS shown, this
            publication-lag limitation label discloses that a macro value is only used once published
            (published_date <= D) — never the reference-date value (forbidden lookahead). */}
        <MacroPublicationLagLabel />

        {status === "error" ? (
          <div className="flex items-center gap-3 rounded-md border border-neg bg-surface p-4 text-sm text-neg">
            <AlertTriangle className="h-5 w-5 shrink-0" aria-hidden />
            <div>
              <p className="font-medium">Backend unavailable</p>
              <p className="text-text-muted">
                The Downtrend Opportunity study could not load from the API. No figures are shown rather than
                fabricated values — confirm the backend is running and retry.
              </p>
            </div>
          </div>
        ) : !data ? (
          <CombinationSkeleton />
        ) : data.n_total === 0 || !hasAny ? (
          <EmptyState
            icon={Microscope}
            title="No downtrend-conditioned observations with forward-tested returns yet"
            description="No stored observation has a causal downtrend tag with a realized forward return at this horizon / window. Pick a shorter horizon or widen the analysis mode — no evidence is fabricated to fill the gap."
          />
        ) : (
          <DowntrendOpportunityBody
            data={data}
            dimension={activeDimension}
            dim={status === "loading"}
            scope={scope}
            view={data.view}
          />
        )}
      </div>
    </Card>
  );
}

/** The conditioning-dimension selector (J-91): a segmented button group (phase / severity band / P(bear)
 *  band), built from the payload's `dimensions` list (config-driven). A cohort/view selector — NOT a date
 *  (J-18). Styled like the other research toggles. */
function DowntrendDimensionSelector({
  dimensions,
  value,
  onChange,
}: {
  dimensions: string[];
  value: string;
  onChange: (dimension: string) => void;
}) {
  return (
    <div className="flex flex-col gap-1">
      <span className="text-xs uppercase tracking-wide text-text-faint">Condition on</span>
      <div role="group" aria-label="Conditioning dimension" className="inline-flex rounded-md border border-border bg-surface-2 p-0.5">
        {dimensions.map((dim) => {
          const active = dim === value;
          return (
            <button
              key={dim}
              type="button"
              onClick={() => onChange(dim)}
              aria-label={`Condition on ${_DIMENSION_LABELS[dim] ?? dim}`}
              aria-pressed={active}
              data-testid={`downtrend-dimension-${dim}`}
              className={cn(
                "rounded px-3 py-1 text-sm transition-colors",
                "focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-accent",
                active ? "bg-accent/15 text-accent" : "text-text-muted hover:text-text",
              )}
            >
              {_DIMENSION_LABELS[dim] ?? dim}
            </button>
          );
        })}
      </div>
    </div>
  );
}

/** The J-92 publication-lag limitation label — an honest disclosure shown wherever a macro-conditioned
 *  figure could appear. The macro feed is config-default-OFF (so today's figures are byte-identical to the
 *  price/breadth/VIX-only path), and a macro value is only used once it was actually published
 *  (published_date <= D) — never the reference-date value (forbidden lookahead). */
function MacroPublicationLagLabel() {
  return (
    <div
      data-testid="macro-publication-lag-label"
      className="flex items-start gap-2 rounded-md border border-border bg-surface-2 px-3 py-2 text-xs text-text-muted"
    >
      <ShieldAlert className="mt-0.5 h-4 w-4 shrink-0 text-text-faint" aria-hidden />
      <span>
        <span className="font-medium text-text-faint">Macro inputs (FRED) are optional and off by default.</span>{" "}
        Today&apos;s figures use the price / breadth / VIX path only. When a macro-conditioned figure is shown,
        a macro value is used for a date only once it was actually published (publication-lag aligned —
        never the as-of-the-day reference value), and a walled or uncommitted series is shown as NA, never
        fabricated.
      </span>
    </div>
  );
}

function DowntrendOpportunityBody({
  data,
  dimension,
  dim,
  scope,
  view,
}: {
  data: DowntrendOpportunityResponse;
  dimension: string;
  dim: boolean;
  scope: SampleScope;
  view: EventStudyView;
}) {
  // angles (a) + (b) rank the SAME cohorts; filter each to the active conditioning dimension (a pure view
  // transform — recomputes nothing). The recovery-turn edge (angle c) by-phase rides the reused payload.
  const best = data.held_up_best.filter((r) => r.dimension === dimension);
  const worst = data.fell_hardest.filter((r) => r.dimension === dimension);
  return (
    <div className={cn("space-y-4 transition-opacity", dim && "opacity-60")} aria-busy={dim}>
      <p className="text-xs text-text-faint">
        Rows with <span className="text-warn">n &lt; {data.min_sample} ⚠</span> render NA. Risk is
        downside-only everywhere (return ÷ downside-deviation and return ÷ mean-|MAE| — never total
        volatility); the aggregate max-drawdown column is read verbatim from the stored excursions. Conditioned
        on the causal {_DIMENSION_LABELS[dimension]?.toLowerCase() ?? dimension} at each snapshot date (&le; that date).
      </p>
      <div className="grid grid-cols-1 gap-4 xl:grid-cols-3">
        <DowntrendAngleTable
          title="Held up best"
          hint="The downtrend-conditioned cohorts with the STRONGEST forward returns (best-first). Read-only association on the current-membership seed — not a forecast."
          rows={best}
          min={data.min_sample}
          horizon={data.horizon}
          scope={scope}
          view={view}
          testid="downtrend-held-up-best-table"
        />
        <DowntrendAngleTable
          title="Fell hardest"
          subtitle="Research evidence only"
          hint="The downtrend-conditioned cohorts with the WORST forward returns / deepest max-drawdown (worst-first). RESEARCH EVIDENCE ONLY — Trendora places no orders and offers no short-deployment path; this is what historically weakened, never an instruction to act."
          rows={worst}
          min={data.min_sample}
          horizon={data.horizon}
          scope={scope}
          view={view}
          testid="downtrend-fell-hardest-table"
        />
        <DowntrendRecoveryAngle data={data.recovery_turn_edge} scope={scope} />
      </div>
    </div>
  );
}

type DowntrendSortKey = "cohort" | "n" | "mean" | "pct_positive" | "return_per_downside_dev" | "mean_max_drawdown";

/** One ranked conditioned-cohort angle table (J-91), client-side sortable (J-48/J-82 view transform —
 *  re-orders only). Each row's `n` is a SampleLink into the (dimension, cohort) drill-down (count-coherent,
 *  new tab). Low-sample / null cells render NA + n (the SAME predicate the sort uses). */
function DowntrendAngleTable({
  title,
  subtitle,
  hint,
  rows,
  min,
  horizon,
  scope,
  view,
  testid,
}: {
  title: string;
  subtitle?: string;
  hint: string;
  rows: DowntrendOpportunityRow[];
  min: number;
  horizon: number;
  scope: SampleScope;
  view: EventStudyView;
  testid: string;
}) {
  const [sortKey, setSortKey] = useState<DowntrendSortKey | null>(null);
  const [sortDir, setSortDir] = useState<"asc" | "desc">("desc");

  const onSort = (key: DowntrendSortKey) => {
    if (sortKey === key) {
      setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    } else {
      setSortKey(key);
      setSortDir(key === "cohort" ? "asc" : "desc");
    }
  };

  const sorted = (() => {
    if (sortKey === null) return rows; // server rank order (the angle's best-first / worst-first)
    const sign = sortDir === "asc" ? 1 : -1;
    const value = (r: DowntrendOpportunityRow): string | number | null => {
      switch (sortKey) {
        case "cohort": return r.cohort_label;
        case "n": return r.stats.n;
        default: {
          const raw = r.stats[sortKey];
          if (r.stats.low_sample || r.stats.n === 0 || raw === null) return null; // SAME NA predicate as the cell
          return raw;
        }
      }
    };
    return rows
      .map((row, index) => ({ row, index }))
      .sort((a, b) => {
        const av = value(a.row);
        const bv = value(b.row);
        if (av === null && bv === null) return a.index - b.index;
        if (av === null) return 1; // NA always last
        if (bv === null) return -1;
        let primary: number;
        if (typeof av === "string" && typeof bv === "string") primary = av.localeCompare(bv) * sign;
        else primary = ((av as number) - (bv as number)) * sign;
        return primary !== 0 ? primary : a.index - b.index;
      })
      .map((e) => e.row);
  })();

  const header = (label: string, col: DowntrendSortKey, align: "left" | "right" = "right", term?: string) => {
    const active = sortKey === col;
    return (
      <th className={cn("px-2 py-2 font-medium", align === "right" ? "text-right" : "text-left")}>
        <span className={cn("inline-flex items-center gap-1", align === "right" && "justify-end")}>
          <button
            type="button"
            onClick={() => onSort(col)}
            aria-label={`Sort ${title} by ${label}`}
            data-testid={`${testid}-sort-${col}`}
            className={cn(
              "inline-flex items-center gap-1 rounded-sm hover:text-text",
              "focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-accent",
              active ? "text-accent" : "text-text-faint",
            )}
          >
            {label}
            <span aria-hidden className="text-[10px]">{active ? (sortDir === "asc" ? "▲" : "▼") : "↕"}</span>
          </button>
          {term ? <TermInfo term={term} /> : null}
        </span>
      </th>
    );
  };

  return (
    <Card className="p-0">
      <PanelTitle hint={hint}>
        <span className="inline-flex items-center gap-2">
          {title}
          {subtitle ? (
            <span
              data-testid={`${testid}-evidence-only`}
              className="rounded border border-warn px-1.5 py-0.5 text-[10px] font-medium uppercase tracking-wide text-warn"
            >
              {subtitle}
            </span>
          ) : null}
        </span>
      </PanelTitle>
      <div className="overflow-x-auto">
        <table data-testid={testid} className="w-full border-collapse text-sm">
          <thead>
            <tr className="border-b border-border text-left text-xs uppercase tracking-wide text-text-faint">
              {header("Cohort", "cohort", "left")}
              {header("n", "n", "right", "n (sample size)")}
              {header("Mean", "mean", "right")}
              {header("Hit-rate", "pct_positive", "right", "hit-rate")}
              {header("Ret/DD", "return_per_downside_dev", "right", "return / downside-dev")}
              {header("Mean MDD", "mean_max_drawdown", "right", "max drawdown")}
            </tr>
          </thead>
          <tbody>
            {sorted.map((row) => {
              const na = row.stats.low_sample || row.stats.n === 0;
              return (
                <tr key={`${row.dimension}-${row.cohort}`} className="border-b border-border last:border-b-0">
                  <td className="px-2 py-2 text-text">{row.cohort_label}</td>
                  <td className="px-2 py-2 text-right">
                    <SampleLink
                      n={row.stats.n}
                      min={min}
                      scope={scope}
                      cohort={{
                        kind: "downtrend-opportunity",
                        horizon,
                        dimension: row.dimension,
                        cohort: row.cohort,
                        view,
                      }}
                      label={`See the ${row.stats.n} observations conditioned on ${row.cohort_label}`}
                    />
                  </td>
                  <td className="px-2 py-2 text-right"><EsValue value={row.stats.mean} na={na} kind="pct" /></td>
                  <td className="px-2 py-2 text-right"><EsValue value={row.stats.pct_positive} na={na} kind="rate" /></td>
                  <td className="px-2 py-2 text-right"><EsValue value={row.stats.return_per_downside_dev} na={na} kind="ratio" /></td>
                  <td className="px-2 py-2 text-right"><EsValue value={row.stats.mean_max_drawdown} na={na} kind="pct" /></td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </Card>
  );
}

/** Angle (c): the reused J-90 recovery-turn edge surfaced in the same panel — the by-signal-phase
 *  conditioning slice (each row's n a SampleLink into the recovery-turn drill-down, count-coherent, new
 *  tab). Read VERBATIM from the reused payload — recomputes nothing. */
function DowntrendRecoveryAngle({
  data,
  scope,
}: {
  data: RecoveryTurnEdgeResponse;
  scope: SampleScope;
}) {
  return (
    <Card className="p-0">
      <PanelTitle hint="The reused Recovery-Turn Edge (J-90): the forward-return edge of entering at causal recovery-turn dates, conditioned on the causal phase at the signal date. Each N= chip opens the exact observations in a new tab. Forward-return evidence only — no order affordance.">
        Recovery-turn edge by phase ({data.horizon}d)
      </PanelTitle>
      <div className="overflow-x-auto">
        <table data-testid="downtrend-recovery-angle-table" className="w-full border-collapse text-sm">
          <thead>
            <tr className="border-b border-border text-left text-xs uppercase tracking-wide text-text-faint">
              <th className="px-2 py-2 font-medium">Phase at signal</th>
              <th className="px-2 py-2 text-right font-medium">
                <span className="inline-flex items-center justify-end gap-1">n<TermInfo term="n (sample size)" /></span>
              </th>
              <th className="px-2 py-2 text-right font-medium">Mean</th>
              <th className="px-2 py-2 text-right font-medium">
                <span className="inline-flex items-center justify-end gap-1">Hit-rate<TermInfo term="hit-rate" /></span>
              </th>
              <th className="px-2 py-2 text-right font-medium">
                <span className="inline-flex items-center justify-end gap-1">Ret/DD<TermInfo term="return / downside-dev" /></span>
              </th>
            </tr>
          </thead>
          <tbody>
            {data.by_phase.map((row) => {
              const na = row.low_sample || row.n === 0;
              return (
                <tr key={row.phase} className="border-b border-border last:border-b-0">
                  <td className="px-2 py-2 text-text">{row.phase}</td>
                  <td className="px-2 py-2 text-right">
                    <SampleLink
                      n={row.n}
                      min={data.min_sample}
                      scope={scope}
                      cohort={{ kind: "recovery-turn", horizon: data.horizon, slice: "phase", phase: row.phase, view: data.view }}
                      label={`See the ${row.n} recovery-turn observations with a ${row.phase} phase at the signal date`}
                    />
                  </td>
                  <td className="px-2 py-2 text-right"><EsValue value={row.mean_return} na={na} kind="pct" /></td>
                  <td className="px-2 py-2 text-right"><EsValue value={row.hit_rate} na={na} kind="rate" /></td>
                  <td className="px-2 py-2 text-right"><EsValue value={row.risk_adjusted} na={na} kind="ratio" /></td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </Card>
  );
}

/** iter-45 (J-104) — each lab route's shared shell: the controls bar (heading + mode toggle + a horizon
 *  selector populated from the lab's reported meta) + the caveat banner + the lab body (or the warming
 *  state). The lab fetches ONCE on its own route, so at most one heavy fetch fires per page. The horizon
 *  selector is config-driven (the lab reports its `horizons` via `onMeta`) — no hard-coded list. */
function LabRouteShell({
  title,
  subtitle,
  warmingWhat,
  render,
}: {
  title: string;
  subtitle: string;
  warmingWhat: string;
  render: (args: { horizon: number | undefined; asofCutoff: string | null; scope: SampleScope; onMeta: (m: LabMeta) => void }) => React.ReactNode;
}) {
  const { mode, setMode, readiness, asofCutoff, scope } = useResearchControls();
  const [horizon, setHorizon] = useState<number | undefined>(undefined);
  const [meta, setMeta] = useState<LabMeta | null>(null);
  return (
    <div className="space-y-4">
      <ResearchControls
        title={title}
        subtitle={subtitle}
        mode={mode}
        onModeChange={setMode}
        asofCutoff={asofCutoff}
        controls={
          <HorizonSelector
            horizons={meta?.horizons ?? []}
            value={horizon ?? meta?.default_horizon}
            onChange={(h) => setHorizon(h)}
          />
        }
      />
      <ResearchCaveat />
      {shouldShowWarming(readiness) ? (
        <WarmingState what={warmingWhat} />
      ) : (
        render({ horizon, asofCutoff, scope, onMeta: setMeta })
      )}
    </div>
  );
}

/** Route page: the Multi-factor combination lab (J-26) on its own `/research/factor-combination` route. */
export function CombinationLabPage() {
  return (
    <LabRouteShell
      title="Research — Multi-factor combination"
      subtitle="Does combining factor conditions beat either alone? The Combined (composite rank-blend) cohort vs the all-names baseline and each single-factor cohort — mean / median forward return, hit-rate, and the downside risk-adjusted column. Descriptive, not predictive."
      warmingWhat="The Combination Lab"
      render={({ horizon, asofCutoff, scope, onMeta }) => (
        <CombinationLab horizon={horizon} asofCutoff={asofCutoff} scope={scope} onMeta={onMeta} />
      )}
    />
  );
}

/** Route page: the Setup & Pattern event study (J-29 / J-63) on its own `/research/event-study` route. */
export function EventStudyLabPage() {
  return (
    <LabRouteShell
      title="Research — Setup & Pattern event study"
      subtitle="What forward-return distribution has each setup or detected pattern historically shown? Per-horizon mean / median / %-positive + expectancy + MAE/MFE excursions + downside risk-adjusted ratios, with the by-regime and by-sector slices. Descriptive evidence, never a forecast."
      warmingWhat="The Setup & Pattern event study"
      render={({ horizon, asofCutoff, scope, onMeta }) => (
        <EventStudyLab horizon={horizon} asofCutoff={asofCutoff} scope={scope} onMeta={onMeta} />
      )}
    />
  );
}

/** Route page: the Regime × Setup × Pattern study (J-77) on its own `/research/regime-setup-pattern` route. */
export function RegimeSetupPatternLabPage() {
  return (
    <LabRouteShell
      title="Research — Regime × Setup × Pattern"
      subtitle="Which (regime, setup, pattern) combinations have historically had the strongest forward-return edge? A ranked table over the stored forward returns, sortable and filterable, with each N= drilling into the exact reproducing cohort. Descriptive, not predictive."
      warmingWhat="The Regime × Setup × Pattern study"
      render={({ horizon, asofCutoff, scope, onMeta }) => (
        <RegimeSetupPatternLab horizon={horizon} asofCutoff={asofCutoff} scope={scope} onMeta={onMeta} />
      )}
    />
  );
}

/** Route page: the Recovery-Turn Edge lab (J-90) on its own `/research/recovery-turn-edge` route. */
export function RecoveryTurnEdgeLabPage() {
  return (
    <LabRouteShell
      title="Research — Recovery-Turn Edge"
      subtitle="When the market causally turns up out of a downtrend, what forward-return edge has entering at those dates historically shown? A read-only aggregation conditioned on the causal phase at the signal date. Descriptive evidence, never an order."
      warmingWhat="The Recovery-Turn Edge lab"
      render={({ horizon, asofCutoff, scope, onMeta }) => (
        <RecoveryTurnEdgeLab horizon={horizon} asofCutoff={asofCutoff} scope={scope} onMeta={onMeta} />
      )}
    />
  );
}

/** Route page: the Downtrend Opportunity lab (J-91) on its own `/research/downtrend-opportunity` route. */
export function DowntrendOpportunityLabPage() {
  return (
    <LabRouteShell
      title="Research — Downtrend Opportunity"
      subtitle="Conditioned on the causal downtrend state (phase / severity band / P(bear) band, all ≤ the date), which cohorts held up best and which fell hardest — plus the recovery-turn edge. Research evidence only, never an order or short-deployment path."
      warmingWhat="The Downtrend Opportunity lab"
      render={({ horizon, asofCutoff, scope, onMeta }) => (
        <DowntrendOpportunityLab horizon={horizon} asofCutoff={asofCutoff} scope={scope} onMeta={onMeta} />
      )}
    />
  );
}

// --- Regime Lab (iter-53, J-110) -----------------------------------------------------------------
/** The page's working overlap-honesty view. The Regime Lab studies the WHOLE cross-section (every
 *  stock × snapshot), so the first-trigger episode collapse would degenerate to each name's first
 *  appearance — `pooled` (every per-signal-day observation, tagged by THAT snapshot's regime) is the
 *  meaningful cross-sectional view. The view is a cohort/MODE (carried verbatim into the `N=` drill-down so
 *  the counts stay coherent), NOT a date — `?asof` remains the single global date (J-18). */
const REGIME_LAB_VIEW: "episodes" | "pooled" = "pooled";

/** A sortable column of a Regime-Lab table: a static key (the regime label string / the decile number) or a
 *  per-horizon `fwd:${h}` / `mdd:${h}` numeric column (NA-last). A pure VIEW transform — the sort re-orders
 *  the served rows only, it recomputes / refetches nothing (J-48). The empty key = the server's natural
 *  order (config-label order / D1…D10). */
type RegimeSortKey = "" | "regime" | "decile" | `fwd:${number}` | `mdd:${number}`;
type RegimeSortDir = "asc" | "desc";

/** Parse a per-horizon sort key (`fwd:20` / `mdd:5`) into its metric + horizon, or null for a static key. */
function parseRegimeHorizonKey(key: RegimeSortKey): { metric: "fwd" | "mdd"; horizon: number } | null {
  const m = /^(fwd|mdd):(\d+)$/.exec(key);
  return m ? { metric: m[1] as "fwd" | "mdd", horizon: Number(m[2]) } : null;
}

/** The cell at horizon `h` of a row's `by_horizon` list (undefined if absent — never expected). */
function regimeCellAt<T extends RegimeLabHorizonCell>(byHorizon: T[], h: number): T | undefined {
  return byHorizon.find((b) => b.horizon === h);
}

/** Whether a cell renders NA for a metric — the SAME `low_sample || n===0 || value===null` rule the cell
 *  uses, so the sort NA-set == the visual NA-set (NA-last in both directions, J-82 predicate). */
function regimeCellIsNa(cell: RegimeLabHorizonCell | undefined, metric: "fwd" | "mdd"): boolean {
  if (!cell || cell.low_sample || cell.n === 0) return true;
  return metric === "fwd" ? cell.mean_return === null : cell.mean_max_drawdown === null;
}

/** The numeric sort value for a metric (NA rows are pushed last by the comparator regardless of sign). */
function regimeCellValue(cell: RegimeLabHorizonCell | undefined, metric: "fwd" | "mdd"): number {
  if (!cell) return 0;
  return (metric === "fwd" ? cell.mean_return : cell.mean_max_drawdown) ?? 0;
}

/** A sortable column header for the Regime-Lab tables (mirrors `FactorSortHeader`). The button is resolved
 *  in tests by its `aria-label`; the visible label lives in a nested span. */
function RegimeSortHeader({
  col,
  label,
  activeKey,
  dir,
  onSort,
  numeric,
}: {
  col: RegimeSortKey;
  label: string;
  activeKey: RegimeSortKey;
  dir: RegimeSortDir;
  onSort: (key: RegimeSortKey) => void;
  numeric?: boolean;
}) {
  const active = activeKey === col;
  const ariaSort: "ascending" | "descending" | "none" = active
    ? dir === "asc"
      ? "ascending"
      : "descending"
    : "none";
  return (
    <th className={cn("px-4 py-2 font-medium", numeric && "text-right")} aria-sort={ariaSort}>
      <button
        type="button"
        onClick={() => onSort(col)}
        aria-label={`Sort by ${label}${active ? (dir === "asc" ? ", ascending" : ", descending") : ""}`}
        className={cn(
          "group inline-flex items-center gap-1 rounded-sm uppercase tracking-wide transition-colors hover:text-text focus-visible:text-text focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-accent",
          numeric && "justify-end",
        )}
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
    </th>
  );
}

/** A Regime-Lab forward-return cell at one horizon: colour-graded mean return (or explicit NA when the
 *  bucket is low-sample / empty / null — never a fabricated number) + the count-coherent `N=` drill-down
 *  chip (new tab). The chip lives on the return cell only (never duplicated on the paired drawdown cell). */
function RegimeReturnCell({
  cell,
  min,
  scope,
  cohort,
  chipLabel,
  rangeTitle,
}: {
  cell: RegimeLabHorizonCell;
  min: number;
  scope: SampleScope;
  cohort: CohortParams;
  chipLabel: string;
  rangeTitle?: string;
}) {
  const na = cell.low_sample || cell.n === 0 || cell.mean_return === null;
  return (
    <span className="inline-flex items-center justify-end gap-2">
      {na ? (
        <span
          className="num font-semibold text-text-muted"
          title={cell.low_sample ? `Low sample — n below the ${min} minimum` : "No observations"}
        >
          NA
        </span>
      ) : (
        <span className={cn("num font-semibold", returnClass(cell.mean_return))} title={rangeTitle}>
          {fmtPct(cell.mean_return)}
        </span>
      )}
      <SampleLink n={cell.n} min={min} scope={scope} cohort={cohort} label={chipLabel} />
    </span>
  );
}

/** A Regime-Lab paired max-drawdown cell at one horizon: mdd-color-graded value (a deeper drawdown reads
 *  more severe), or explicit NA when low-sample / empty / null — never a fabricated 0. */
function RegimeMddCell({ cell, min }: { cell: RegimeLabHorizonCell; min: number }) {
  const na = cell.low_sample || cell.n === 0 || cell.mean_max_drawdown === null;
  if (na) {
    return (
      <span
        className="num font-semibold text-text-muted"
        title={cell.low_sample ? `Low sample — n below the ${min} minimum` : "No stored drawdown — NA"}
      >
        NA
      </span>
    );
  }
  return (
    <span className={cn("num font-semibold", mddClass(cell.mean_max_drawdown))}>
      {fmtMdd(cell.mean_max_drawdown)}
    </span>
  );
}

/** Toggle a sort key: same key flips direction; a new key leads ascending for the static (label/decile)
 *  columns and descending (strongest first) for the numeric per-horizon columns. */
function useRegimeSort(initial: RegimeSortKey) {
  const [sortKey, setSortKey] = useState<RegimeSortKey>(initial);
  const [sortDir, setSortDir] = useState<RegimeSortDir>("asc");
  const onSort = (key: RegimeSortKey) => {
    if (key === sortKey) {
      setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    } else {
      setSortKey(key);
      setSortDir(key === "regime" || key === "decile" ? "asc" : "desc");
    }
  };
  return { sortKey, sortDir, onSort };
}

/** Stable, NA-last comparator over rows carrying a `by_horizon` list. `staticVal` resolves a static column
 *  (the regime label string / the decile number); the per-horizon `fwd:`/`mdd:` columns sort by the cell's
 *  metric, NA-last in BOTH directions. The empty key keeps the server's natural order. */
function sortRegimeRows<T extends { by_horizon: RegimeLabHorizonCell[] }>(
  rows: T[],
  sortKey: RegimeSortKey,
  sortDir: RegimeSortDir,
  staticVal: (row: T, key: RegimeSortKey) => { str?: string; num?: number },
): T[] {
  if (sortKey === "") return rows;
  const sign = sortDir === "asc" ? 1 : -1;
  const hk = parseRegimeHorizonKey(sortKey);
  return rows
    .map((row, i) => ({ row, i }))
    .sort((a, b) => {
      if (hk) {
        const ca = regimeCellAt(a.row.by_horizon, hk.horizon);
        const cb = regimeCellAt(b.row.by_horizon, hk.horizon);
        const ana = regimeCellIsNa(ca, hk.metric);
        const bna = regimeCellIsNa(cb, hk.metric);
        if (ana && bna) return a.i - b.i;
        if (ana) return 1; // NA last regardless of direction
        if (bna) return -1;
        const c = (regimeCellValue(ca, hk.metric) - regimeCellValue(cb, hk.metric)) * sign;
        return c !== 0 ? c : a.i - b.i;
      }
      const sa = staticVal(a.row, sortKey);
      const sb = staticVal(b.row, sortKey);
      let c = 0;
      if (sa.str !== undefined && sb.str !== undefined) c = sa.str.localeCompare(sb.str) * sign;
      else if (sa.num !== undefined && sb.num !== undefined) c = (sa.num - sb.num) * sign;
      return c !== 0 ? c : a.i - b.i;
    })
    .map((x) => x.row);
}

/** The by-LABEL summary table: one row per configured regime label (server-driven order), then per config
 *  horizon a paired (mean forward-return, mean max-drawdown) column + the count-coherent `N=` chip. Sortable
 *  NA-last on every numeric column. */
function RegimeLabByLabelTable({
  data,
  scope,
}: {
  data: RegimeLabResponse;
  scope: SampleScope;
}) {
  const { sortKey, sortDir, onSort } = useRegimeSort("");
  const horizons = data.horizons;
  const sorted = useMemo(
    () => sortRegimeRows(data.by_label, sortKey, sortDir, (row) => ({ str: row.regime })),
    [data.by_label, sortKey, sortDir],
  );
  if (data.by_label.length === 0) {
    return (
      <EmptyState
        icon={Microscope}
        title="No forward-tested observations"
        description="No stored snapshot has a realized forward return tagged with a regime. No figure is fabricated to fill the gap."
      />
    );
  }
  return (
    <Card className="overflow-x-auto p-0" data-testid="regime-lab-by-label">
      <PanelTitle
        hint={`Mean realized forward return AND its paired max-drawdown per market-regime label, at every horizon. Cells with n < ${data.min_sample} render NA + n. Click a column to sort (NA-last); click an N= chip to open that cohort's observations.`}
      >
        By regime label
      </PanelTitle>
      <table data-testid="regime-label-table" className="w-full border-collapse text-sm">
        <thead>
          <tr className="border-b border-border text-left text-xs uppercase tracking-wide text-text-faint">
            <RegimeSortHeader col="regime" label="Regime" activeKey={sortKey} dir={sortDir} onSort={onSort} />
            {/* J-114: all forward-return columns first, then all max-drawdown columns (no interleave). */}
            {groupedHorizonColumns(horizons).map((col) => (
              <RegimeSortHeader
                key={horizonColumnKey(col)}
                col={`${col.metric}:${col.horizon}`}
                label={`${col.metric === "fwd" ? "Fwd" : "MDD"} ${col.horizon}d`}
                activeKey={sortKey}
                dir={sortDir}
                onSort={onSort}
                numeric
              />
            ))}
          </tr>
        </thead>
        <tbody>
          {sorted.map((row) => (
            <tr key={row.regime} className="border-b border-border last:border-b-0" data-testid={`regime-label-row-${row.regime}`}>
              <td className="px-4 py-2 font-medium text-text">{row.regime}</td>
              {/* J-114: all forward-return cells first, then all max-drawdown cells (no interleave). */}
              {groupedHorizonColumns(horizons).map((col) => {
                const h = col.horizon;
                const cell = regimeCellAt(row.by_horizon, h);
                return (
                  <td key={`lc-${row.regime}-${horizonColumnKey(col)}`} className="px-4 py-2 text-right">
                    {col.metric === "fwd" ? (
                      cell ? (
                        <RegimeReturnCell
                          cell={cell}
                          min={data.min_sample}
                          scope={scope}
                          cohort={{ kind: "regime-lab", horizon: h, slice: "label", view: REGIME_LAB_VIEW, regime: row.regime }}
                          chipLabel={`Open the ${row.regime} regime cohort (n=${cell.n}) at the ${h}-day horizon in Research Samples (new tab)`}
                        />
                      ) : (
                        <span className="text-text-faint">—</span>
                      )
                    ) : cell ? (
                      <RegimeMddCell cell={cell} min={data.min_sample} />
                    ) : (
                      <span className="text-text-faint">—</span>
                    )}
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </Card>
  );
}

/** The by-regime-score-DECILE table: a header Rank-IC row (regime score ↔ forward return per horizon), the
 *  decile's regime-score range at the default horizon, then per config horizon a paired (mean forward-return,
 *  mean max-drawdown) column + the count-coherent `N=` chip. Sortable NA-last on every numeric column. */
function RegimeLabDecileTable({
  data,
  scope,
}: {
  data: RegimeLabResponse;
  scope: SampleScope;
}) {
  const { sortKey, sortDir, onSort } = useRegimeSort("");
  const horizons = data.horizons;
  const defaultHorizon = data.default_horizon;
  const rankIcByH = new Map(data.rank_ic_by_horizon.map((r) => [r.horizon, r.rank_ic]));
  const sorted = useMemo(
    () => sortRegimeRows(data.by_decile, sortKey, sortDir, (row) => ({ num: row.decile })),
    [data.by_decile, sortKey, sortDir],
  );
  return (
    <Card className="overflow-x-auto p-0" data-testid="regime-lab-by-decile">
      <PanelTitle
        hint={`Mean realized forward return AND its paired max-drawdown per regime-score decile (D1 = lowest 0–100 regime score → D10 = highest), at every horizon. The Rank-IC row is the Spearman correlation of the regime score vs the forward return per horizon (labelled at ${defaultHorizon}d for reference). Score range is shown at the ${defaultHorizon}-day horizon; each horizon's own range is on its return cell's hover. Cells with n < ${data.min_sample} render NA + n.`}
      >
        By regime-score decile
      </PanelTitle>
      <table data-testid="regime-decile-table" className="w-full border-collapse text-sm">
        <thead>
          <tr className="border-b border-border text-left text-xs uppercase tracking-wide text-text-faint">
            <RegimeSortHeader col="decile" label="Decile" activeKey={sortKey} dir={sortDir} onSort={onSort} />
            <th className="px-4 py-2 text-right font-medium">Score range ({defaultHorizon}d)</th>
            {/* J-114: all forward-return columns first, then all max-drawdown columns (no interleave). */}
            {groupedHorizonColumns(horizons).map((col) => (
              <RegimeSortHeader
                key={horizonColumnKey(col)}
                col={`${col.metric}:${col.horizon}`}
                label={`${col.metric === "fwd" ? "Fwd" : "MDD"} ${col.horizon}d`}
                activeKey={sortKey}
                dir={sortDir}
                onSort={onSort}
                numeric
              />
            ))}
          </tr>
        </thead>
        <tbody>
          {/* the Rank-IC header row (regime score ↔ forward return per horizon) — not a decile, so no chip. */}
          <tr className="border-b border-border bg-surface-2/40" data-testid="regime-decile-rank-ic-row">
            <td className="px-4 py-2 font-medium text-text-muted">
              <span className="inline-flex items-center gap-1">Rank-IC<TermInfo term="rank-IC" /></span>
            </td>
            <td className="px-4 py-2 text-right text-text-faint">—</td>
            {/* J-114: rank-IC lives on the forward-return columns (first), then the drawdown columns show —. */}
            {groupedHorizonColumns(horizons).map((col) => {
              const h = col.horizon;
              if (col.metric === "mdd") {
                return <td key={horizonColumnKey(col)} className="px-4 py-2 text-right text-text-faint">—</td>;
              }
              const ic = rankIcByH.get(h);
              const na = !ic || ic.value === null;
              return (
                <td key={horizonColumnKey(col)} className="px-4 py-2 text-right">
                  <RatioCell
                    value={ic?.value ?? null}
                    na={na}
                    title={na ? "Not enough independent observations to rank-correlate — NA, not a fabricated 0" : `Spearman rank-IC of the regime score vs the ${h}-day forward return`}
                  />
                </td>
              );
            })}
          </tr>
          {sorted.map((row) => {
            const range = regimeCellAt(row.by_horizon, defaultHorizon);
            return (
              <tr key={row.decile} className="border-b border-border last:border-b-0" data-testid={`regime-decile-row-${row.decile}`}>
                <td className="px-4 py-2">
                  <span className="num font-semibold text-text">D{row.decile}</span>
                </td>
                <td className="num px-4 py-2 text-right text-xs text-text-faint">
                  {!range || range.score_min === null || range.score_max === null
                    ? "—"
                    : `${range.score_min.toFixed(1)} … ${range.score_max.toFixed(1)}`}
                </td>
                {/* J-114: all forward-return cells first, then all max-drawdown cells (no interleave). */}
                {groupedHorizonColumns(horizons).map((col) => {
                  const h = col.horizon;
                  const cell = regimeCellAt(row.by_horizon, h);
                  const rangeTitle =
                    cell && cell.score_min !== null && cell.score_max !== null
                      ? `Regime-score range at ${h}d: ${cell.score_min.toFixed(1)} … ${cell.score_max.toFixed(1)}`
                      : undefined;
                  return (
                    <td key={`dc-${row.decile}-${horizonColumnKey(col)}`} className="px-4 py-2 text-right">
                      {col.metric === "fwd" ? (
                        cell ? (
                          <RegimeReturnCell
                            cell={cell}
                            min={data.min_sample}
                            scope={scope}
                            cohort={{ kind: "regime-lab", horizon: h, slice: "decile", view: REGIME_LAB_VIEW, decile: row.decile }}
                            chipLabel={`Open the regime-score decile D${row.decile} cohort (n=${cell.n}) at the ${h}-day horizon in Research Samples (new tab)`}
                            rangeTitle={rangeTitle}
                          />
                        ) : (
                          <span className="text-text-faint">—</span>
                        )
                      ) : cell ? (
                        <RegimeMddCell cell={cell} min={data.min_sample} />
                      ) : (
                        <span className="text-text-faint">—</span>
                      )}
                    </td>
                  );
                })}
              </tr>
            );
          })}
        </tbody>
      </table>
    </Card>
  );
}

type RegimeLabState =
  | { kind: "loading" }
  | { kind: "ok"; data: RegimeLabResponse }
  | { kind: "error" };

/** iter-53 (J-110) — the Regime Lab on its OWN route (`/research/regime-lab`). Cross-sectional realized
 *  forward returns + paired max-drawdowns grouped (a) by the six canonical regime labels and (b) into
 *  deciles of the 0–100 regime score, at EVERY config horizon at once (paired columns), with the per-horizon
 *  rank-IC of the regime score vs the forward return. The As-of mode toggle FILTERS the observation set (the
 *  single global as-of — no second date state, J-18). Every figure is read VERBATIM from the stored values
 *  and re-presented; the page recomputes nothing and the sort is a pure view transform. */
export function RegimeLabPage() {
  const [state, setState] = useState<RegimeLabState>({ kind: "loading" });
  const { mode, setMode, readiness, asofCutoff, scope } = useResearchControls();

  useEffect(() => {
    const controller = new AbortController();
    setState({ kind: "loading" });
    fetchRegimeLab(REGIME_LAB_VIEW, asofCutoff ?? undefined, controller.signal)
      .then((data) => setState({ kind: "ok", data }))
      .catch(() => {
        if (!controller.signal.aborted) setState({ kind: "error" });
      });
    return () => controller.abort();
  }, [asofCutoff, readiness]);

  const data = state.kind === "ok" ? state.data : null;

  return (
    <div className="space-y-4">
      <ResearchControls
        title="Research — Regime Lab"
        subtitle="How have stocks' realized forward returns and downside risk differed across the market regime? Mean forward return + paired max-drawdown grouped by the six regime labels and by deciles of the 0–100 regime score, at every horizon at once, with the rank-IC of the regime score vs the forward return. Derived once from the stored forward-tested evidence; descriptive survivorship-biased association, never a forecast."
        mode={mode}
        onModeChange={setMode}
        asofCutoff={asofCutoff}
      />
      <ResearchCaveat survivorship={data?.survivorship_bias} descriptive={data?.descriptive_caveat} />
      {shouldShowWarming(readiness) ? (
        <WarmingState what="The Regime Lab" />
      ) : (
        <>
          {state.kind === "loading" ? <LabSkeleton /> : null}
          {state.kind === "error" ? <ResearchError what="The Regime-Lab evidence" /> : null}
          {data ? (
            <>
              <RegimeLabByLabelTable data={data} scope={scope} />
              <RegimeLabDecileTable data={data} scope={scope} />
            </>
          ) : null}
        </>
      )}
    </div>
  );
}

// --- Market Phase & Severity Lab (iter-54, J-111) ------------------------------------------------
/** The page's working overlap-honesty view. Like the Regime Lab, the Phase & Severity Lab studies the WHOLE
 *  cross-section (every stock × snapshot), so the first-trigger episode collapse would degenerate to each
 *  name's first appearance — `pooled` (every per-signal-day observation, tagged by THAT snapshot's served
 *  phase/severity) is the meaningful cross-sectional view. The view is a cohort/MODE (carried verbatim into
 *  the `N=` drill-down so the counts stay coherent), NOT a date — `?asof` remains the single global date
 *  (J-18). Pinned to `pooled` on BOTH the lab fetch AND every `N=` chip. */
const PHASE_SEVERITY_LAB_VIEW: "episodes" | "pooled" = "pooled";

/** The by-PHASE-LABEL summary table: one row per configured market-phase label (server-driven order), then per
 *  config horizon a paired (mean forward-return, mean max-drawdown) column + the count-coherent `N=` chip.
 *  Sortable NA-last on every numeric column. Reuses the Regime-Lab cell/sort machinery (identical cell shape);
 *  the only difference is the grouping subject (the served market-phase label). */
function PhaseSeverityLabByLabelTable({
  data,
  scope,
}: {
  data: PhaseSeverityLabResponse;
  scope: SampleScope;
}) {
  const { sortKey, sortDir, onSort } = useRegimeSort("");
  const horizons = data.horizons;
  const sorted = useMemo(
    () =>
      sortRegimeRows<PhaseSeverityLabLabelRow>(
        data.by_label,
        sortKey,
        sortDir,
        (row) => ({ str: row.phase }),
      ),
    [data.by_label, sortKey, sortDir],
  );
  if (data.by_label.length === 0) {
    return (
      <EmptyState
        icon={Microscope}
        title="No forward-tested observations"
        description="No stored snapshot has a realized forward return tagged with a market phase. No figure is fabricated to fill the gap."
      />
    );
  }
  return (
    <Card className="overflow-x-auto p-0" data-testid="phase-severity-lab-by-label">
      <PanelTitle
        hint={`Mean realized forward return AND its paired max-drawdown per market-phase label, at every horizon. Cells with n < ${data.min_sample} render NA + n. Click a column to sort (NA-last); click an N= chip to open that cohort's observations.`}
      >
        By market phase
      </PanelTitle>
      <table data-testid="phase-severity-label-table" className="w-full border-collapse text-sm">
        <thead>
          <tr className="border-b border-border text-left text-xs uppercase tracking-wide text-text-faint">
            <RegimeSortHeader col="regime" label="Market phase" activeKey={sortKey} dir={sortDir} onSort={onSort} />
            {/* J-114: all forward-return columns first, then all max-drawdown columns (no interleave). */}
            {groupedHorizonColumns(horizons).map((col) => (
              <RegimeSortHeader
                key={horizonColumnKey(col)}
                col={`${col.metric}:${col.horizon}`}
                label={`${col.metric === "fwd" ? "Fwd" : "MDD"} ${col.horizon}d`}
                activeKey={sortKey}
                dir={sortDir}
                onSort={onSort}
                numeric
              />
            ))}
          </tr>
        </thead>
        <tbody>
          {sorted.map((row) => (
            <tr key={row.phase} className="border-b border-border last:border-b-0" data-testid={`phase-severity-label-row-${row.phase}`}>
              <td className="px-4 py-2 font-medium text-text">{row.phase}</td>
              {/* J-114: all forward-return cells first, then all max-drawdown cells (no interleave). */}
              {groupedHorizonColumns(horizons).map((col) => {
                const h = col.horizon;
                const cell = regimeCellAt(row.by_horizon, h);
                return (
                  <td key={`plc-${row.phase}-${horizonColumnKey(col)}`} className="px-4 py-2 text-right">
                    {col.metric === "fwd" ? (
                      cell ? (
                        <RegimeReturnCell
                          cell={cell}
                          min={data.min_sample}
                          scope={scope}
                          cohort={{ kind: "phase-severity-lab", horizon: h, slice: "label", view: PHASE_SEVERITY_LAB_VIEW, phase: row.phase }}
                          chipLabel={`Open the ${row.phase} market-phase cohort (n=${cell.n}) at the ${h}-day horizon in Research Samples (new tab)`}
                        />
                      ) : (
                        <span className="text-text-faint">—</span>
                      )
                    ) : cell ? (
                      <RegimeMddCell cell={cell} min={data.min_sample} />
                    ) : (
                      <span className="text-text-faint">—</span>
                    )}
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </Card>
  );
}

/** The by-severity-score-DECILE table: a header Rank-IC row (severity score ↔ forward return per horizon), the
 *  decile's severity-score range at the default horizon, then per config horizon a paired (mean forward-return,
 *  mean max-drawdown) column + the count-coherent `N=` chip. Sortable NA-last on every numeric column. */
function PhaseSeverityLabDecileTable({
  data,
  scope,
}: {
  data: PhaseSeverityLabResponse;
  scope: SampleScope;
}) {
  const { sortKey, sortDir, onSort } = useRegimeSort("");
  const horizons = data.horizons;
  const defaultHorizon = data.default_horizon;
  const rankIcByH = new Map(data.rank_ic_by_horizon.map((r) => [r.horizon, r.rank_ic]));
  const sorted = useMemo(
    () =>
      sortRegimeRows<PhaseSeverityLabDecileRow>(
        data.by_decile,
        sortKey,
        sortDir,
        (row) => ({ num: row.decile }),
      ),
    [data.by_decile, sortKey, sortDir],
  );
  return (
    <Card className="overflow-x-auto p-0" data-testid="phase-severity-lab-by-decile">
      <PanelTitle
        hint={`Mean realized forward return AND its paired max-drawdown per severity-score decile (D1 = lowest 0–100 severity → D10 = highest), at every horizon. The Rank-IC row is the Spearman correlation of the severity score vs the forward return per horizon (labelled at ${defaultHorizon}d for reference). Score range is shown at the ${defaultHorizon}-day horizon; each horizon's own range is on its return cell's hover. Cells with n < ${data.min_sample} render NA + n.`}
      >
        By severity-score decile
      </PanelTitle>
      <table data-testid="phase-severity-decile-table" className="w-full border-collapse text-sm">
        <thead>
          <tr className="border-b border-border text-left text-xs uppercase tracking-wide text-text-faint">
            <RegimeSortHeader col="decile" label="Decile" activeKey={sortKey} dir={sortDir} onSort={onSort} />
            <th className="px-4 py-2 text-right font-medium">Severity range ({defaultHorizon}d)</th>
            {/* J-114: all forward-return columns first, then all max-drawdown columns (no interleave). */}
            {groupedHorizonColumns(horizons).map((col) => (
              <RegimeSortHeader
                key={horizonColumnKey(col)}
                col={`${col.metric}:${col.horizon}`}
                label={`${col.metric === "fwd" ? "Fwd" : "MDD"} ${col.horizon}d`}
                activeKey={sortKey}
                dir={sortDir}
                onSort={onSort}
                numeric
              />
            ))}
          </tr>
        </thead>
        <tbody>
          {/* the Rank-IC header row (severity score ↔ forward return per horizon) — not a decile, so no chip. */}
          <tr className="border-b border-border bg-surface-2/40" data-testid="phase-severity-decile-rank-ic-row">
            <td className="px-4 py-2 font-medium text-text-muted">
              <span className="inline-flex items-center gap-1">Rank-IC<TermInfo term="rank-IC" /></span>
            </td>
            <td className="px-4 py-2 text-right text-text-faint">—</td>
            {/* J-114: rank-IC lives on the forward-return columns (first), then the drawdown columns show —. */}
            {groupedHorizonColumns(horizons).map((col) => {
              const h = col.horizon;
              if (col.metric === "mdd") {
                return <td key={horizonColumnKey(col)} className="px-4 py-2 text-right text-text-faint">—</td>;
              }
              const ic = rankIcByH.get(h);
              const na = !ic || ic.value === null;
              return (
                <td key={horizonColumnKey(col)} className="px-4 py-2 text-right">
                  <RatioCell
                    value={ic?.value ?? null}
                    na={na}
                    title={na ? "Not enough independent observations to rank-correlate — NA, not a fabricated 0" : `Spearman rank-IC of the severity score vs the ${h}-day forward return`}
                  />
                </td>
              );
            })}
          </tr>
          {sorted.map((row) => {
            const range = regimeCellAt(row.by_horizon, defaultHorizon);
            return (
              <tr key={row.decile} className="border-b border-border last:border-b-0" data-testid={`phase-severity-decile-row-${row.decile}`}>
                <td className="px-4 py-2">
                  <span className="num font-semibold text-text">D{row.decile}</span>
                </td>
                <td className="num px-4 py-2 text-right text-xs text-text-faint">
                  {!range || range.score_min === null || range.score_max === null
                    ? "—"
                    : `${range.score_min.toFixed(1)} … ${range.score_max.toFixed(1)}`}
                </td>
                {/* J-114: all forward-return cells first, then all max-drawdown cells (no interleave). */}
                {groupedHorizonColumns(horizons).map((col) => {
                  const h = col.horizon;
                  const cell = regimeCellAt(row.by_horizon, h);
                  const rangeTitle =
                    cell && cell.score_min !== null && cell.score_max !== null
                      ? `Severity-score range at ${h}d: ${cell.score_min.toFixed(1)} … ${cell.score_max.toFixed(1)}`
                      : undefined;
                  return (
                    <td key={`pdc-${row.decile}-${horizonColumnKey(col)}`} className="px-4 py-2 text-right">
                      {col.metric === "fwd" ? (
                        cell ? (
                          <RegimeReturnCell
                            cell={cell}
                            min={data.min_sample}
                            scope={scope}
                            cohort={{ kind: "phase-severity-lab", horizon: h, slice: "decile", view: PHASE_SEVERITY_LAB_VIEW, decile: row.decile }}
                            chipLabel={`Open the severity-score decile D${row.decile} cohort (n=${cell.n}) at the ${h}-day horizon in Research Samples (new tab)`}
                            rangeTitle={rangeTitle}
                          />
                        ) : (
                          <span className="text-text-faint">—</span>
                        )
                      ) : cell ? (
                        <RegimeMddCell cell={cell} min={data.min_sample} />
                      ) : (
                        <span className="text-text-faint">—</span>
                      )}
                    </td>
                  );
                })}
              </tr>
            );
          })}
        </tbody>
      </table>
    </Card>
  );
}

type PhaseSeverityLabState =
  | { kind: "loading" }
  | { kind: "ok"; data: PhaseSeverityLabResponse }
  | { kind: "error" };

/** iter-54 (J-111) — the Market Phase & Severity Lab on its OWN route (`/research/phase-severity-lab`). The
 *  structural twin of the Regime Lab: cross-sectional realized forward returns + paired max-drawdowns grouped
 *  (a) by the five canonical market-phase labels and (b) into deciles of the 0–100 severity score, at EVERY
 *  config horizon at once (paired columns), with the per-horizon rank-IC of the severity score vs the forward
 *  return. The grouping subject (phase label + severity LEVEL) is read VERBATIM from the served `market_phase`
 *  causal timeline, joined by snapshot date. The As-of mode toggle FILTERS the observation set (the single
 *  global as-of — no second date state, J-18). Every figure is read VERBATIM from the stored values and
 *  re-presented; the page recomputes nothing and the sort is a pure view transform. */
export function PhaseSeverityLabPage() {
  const [state, setState] = useState<PhaseSeverityLabState>({ kind: "loading" });
  const { mode, setMode, readiness, asofCutoff, scope } = useResearchControls();

  useEffect(() => {
    const controller = new AbortController();
    setState({ kind: "loading" });
    fetchPhaseSeverityLab(PHASE_SEVERITY_LAB_VIEW, asofCutoff ?? undefined, controller.signal)
      .then((data) => setState({ kind: "ok", data }))
      .catch(() => {
        if (!controller.signal.aborted) setState({ kind: "error" });
      });
    return () => controller.abort();
  }, [asofCutoff, readiness]);

  const data = state.kind === "ok" ? state.data : null;

  return (
    <div className="space-y-4">
      <ResearchControls
        title="Research — Market Phase & Severity Lab"
        subtitle="How have stocks' realized forward returns and downside risk differed across the market context? Mean forward return + paired max-drawdown grouped by the five market-phase labels and by deciles of the 0–100 severity score, at every horizon at once, with the rank-IC of the severity score vs the forward return. Derived once from the stored forward-tested evidence + the served market-phase timeline; descriptive survivorship-biased association, never a forecast."
        mode={mode}
        onModeChange={setMode}
        asofCutoff={asofCutoff}
      />
      <ResearchCaveat survivorship={data?.survivorship_bias} descriptive={data?.descriptive_caveat} />
      {shouldShowWarming(readiness) ? (
        <WarmingState what="The Market Phase & Severity Lab" />
      ) : (
        <>
          {state.kind === "loading" ? <LabSkeleton /> : null}
          {state.kind === "error" ? <ResearchError what="The Market Phase & Severity-Lab evidence" /> : null}
          {data ? (
            <>
              <PhaseSeverityLabByLabelTable data={data} scope={scope} />
              <PhaseSeverityLabDecileTable data={data} scope={scope} />
            </>
          ) : null}
        </>
      )}
    </div>
  );
}

// --- Regime × Phase × Factor 3-way decile study (iter-55, J-112) ---------------------------------
/** The page's working overlap-honesty view. Like the Regime / Phase-Severity Lab, this studies the WHOLE
 *  cross-section (every stock × snapshot), so the first-trigger episode collapse would degenerate to each
 *  name's first appearance — `pooled` (every per-signal-day observation) is the meaningful view. PINNED to
 *  `pooled` on BOTH the lab fetch AND every `N=` chip (no Episodes/Pooled toggle is exposed); it is a
 *  cohort/MODE carried verbatim into the drill-down so the counts stay coherent, NOT a date (`?asof` remains
 *  the single global date, J-18). */
const REGIME_PHASE_FACTOR_VIEW: "episodes" | "pooled" = "pooled";

/** The "All" sentinel for the three decile filter dropdowns — a structural value (never a real decile), so it
 *  can never collide with a 1..deciles entry. The config page size rides the served payload (no UI literal). */
const RPF_FILTER_ALL = "__all__";

/** The client-side sortable column keys for the J-112 ranked combination table (J-48 view-transform — re-orders
 *  the already-served rows only; never refetches or recomputes a stored value): the three static decile
 *  coordinates, or a per-horizon `fwd:${h}` / `mdd:${h}` numeric column (NA-last). The empty key keeps the
 *  server's default rank (by the default-horizon return). */
type RpfSortKey =
  | ""
  | "regime_decile"
  | "severity_decile"
  | "factor_decile"
  | `fwd:${number}`
  | `mdd:${number}`;

/** Toggle a sort key: same key flips direction; a new key leads ascending for the static decile columns and
 *  descending (strongest first) for the numeric per-horizon columns. */
function useRpfSort(initial: RpfSortKey) {
  const [sortKey, setSortKey] = useState<RpfSortKey>(initial);
  const [sortDir, setSortDir] = useState<RegimeSortDir>("desc");
  const onSort = (key: RpfSortKey) => {
    if (key === sortKey) {
      setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    } else {
      setSortKey(key);
      setSortDir(
        key === "regime_decile" || key === "severity_decile" || key === "factor_decile" ? "asc" : "desc",
      );
    }
  };
  return { sortKey, sortDir, onSort };
}

/** Stable, NA-last comparator over the combination rows. The three static decile columns sort numerically; the
 *  per-horizon `fwd:`/`mdd:` columns reuse the SHARED Regime-Lab cell helpers (`regimeCellAt` / `regimeCellIsNa`
 *  / `regimeCellValue`) so a DISPLAYED-NA cell sinks LAST in BOTH directions (the J-82 predicate — identical to
 *  the cell display). The empty key keeps the server's default rank (a pure view transform — recomputes
 *  nothing). */
function sortRpfRows(
  rows: RegimePhaseFactorRow[],
  sortKey: RpfSortKey,
  sortDir: RegimeSortDir,
): RegimePhaseFactorRow[] {
  if (sortKey === "") return rows;
  const sign = sortDir === "asc" ? 1 : -1;
  const hk = parseRegimeHorizonKey(sortKey as RegimeSortKey);
  return rows
    .map((row, i) => ({ row, i }))
    .sort((a, b) => {
      if (hk) {
        const ca = regimeCellAt(a.row.by_horizon, hk.horizon);
        const cb = regimeCellAt(b.row.by_horizon, hk.horizon);
        const ana = regimeCellIsNa(ca, hk.metric);
        const bna = regimeCellIsNa(cb, hk.metric);
        if (ana && bna) return a.i - b.i;
        if (ana) return 1; // NA last regardless of direction
        if (bna) return -1;
        const c = (regimeCellValue(ca, hk.metric) - regimeCellValue(cb, hk.metric)) * sign;
        return c !== 0 ? c : a.i - b.i;
      }
      const av = a.row[sortKey as "regime_decile" | "severity_decile" | "factor_decile"];
      const bv = b.row[sortKey as "regime_decile" | "severity_decile" | "factor_decile"];
      const c = (av - bv) * sign;
      return c !== 0 ? c : a.i - b.i;
    })
    .map((x) => x.row);
}

/** A sortable column header for the J-112 table (mirrors `RegimeSortHeader`). Resolved in tests by its
 *  `aria-label`; the visible label lives in a nested span. */
function RpfSortHeader({
  col,
  label,
  activeKey,
  dir,
  onSort,
  numeric,
}: {
  col: RpfSortKey;
  label: string;
  activeKey: RpfSortKey;
  dir: RegimeSortDir;
  onSort: (key: RpfSortKey) => void;
  numeric?: boolean;
}) {
  const active = activeKey === col;
  const ariaSort: "ascending" | "descending" | "none" = active
    ? dir === "asc"
      ? "ascending"
      : "descending"
    : "none";
  return (
    <th className={cn("px-3 py-2 font-medium", numeric && "text-right")} aria-sort={ariaSort}>
      <button
        type="button"
        onClick={() => onSort(col)}
        aria-label={`Sort by ${label}${active ? (dir === "asc" ? ", ascending" : ", descending") : ""}`}
        className={cn(
          "group inline-flex items-center gap-1 rounded-sm uppercase tracking-wide transition-colors hover:text-text focus-visible:text-text focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-accent",
          numeric && "justify-end",
        )}
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
    </th>
  );
}

/** A "DECILE / All" filter dropdown (one of the three coordinate filters). The vocabulary is 1..`decilesCount`
 *  from the served payload — no hard-coded list; default "All" passes every row. Pure view transform. */
function RpfDecileFilter({
  label,
  ariaLabel,
  testId,
  value,
  decilesCount,
  onChange,
}: {
  label: string;
  ariaLabel: string;
  testId: string;
  value: string;
  decilesCount: number;
  onChange: (v: string) => void;
}) {
  return (
    <label className="flex flex-col gap-1">
      <span className="text-xs uppercase tracking-wide text-text-faint">{label}</span>
      <Select
        data-testid={testId}
        aria-label={ariaLabel}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-40"
      >
        <option value={RPF_FILTER_ALL}>All</option>
        {Array.from({ length: decilesCount }, (_, i) => i + 1).map((d) => (
          <option key={d} value={String(d)}>
            D{d}
          </option>
        ))}
      </Select>
    </label>
  );
}

/** The ranked combination table (J-112): one row per `(regime-score decile, severity-score decile, factor
 *  decile)` triple, then per config horizon a paired (mean forward-return, mean max-drawdown) column + the
 *  count-coherent `N=` chip on the return cell. Horizontally scrollable (wide table). Reuses the shared
 *  Regime-Lab cell + NA-last sort machinery (identical cell shape). The rows are already filtered / sorted /
 *  paginated by the page (pure view transforms — recomputes nothing). */
function RegimePhaseFactorTable({
  data,
  rows,
  scope,
  sortKey,
  sortDir,
  onSort,
}: {
  data: RegimePhaseFactorResponse;
  rows: RegimePhaseFactorRow[];
  scope: SampleScope;
  sortKey: RpfSortKey;
  sortDir: RegimeSortDir;
  onSort: (key: RpfSortKey) => void;
}) {
  const horizons = data.horizons;
  const factorKey = data.factor.key;
  return (
    <div className="overflow-x-auto">
      <table data-testid="regime-phase-factor-table" className="w-full border-collapse text-sm">
        <thead>
          <tr className="border-b border-border text-left text-xs uppercase tracking-wide text-text-faint">
            <RpfSortHeader col="regime_decile" label="Regime D" activeKey={sortKey} dir={sortDir} onSort={onSort} />
            <RpfSortHeader col="severity_decile" label="Severity D" activeKey={sortKey} dir={sortDir} onSort={onSort} />
            <RpfSortHeader col="factor_decile" label="Factor D" activeKey={sortKey} dir={sortDir} onSort={onSort} />
            {/* J-114: all forward-return columns first, then all max-drawdown columns (no interleave). */}
            {groupedHorizonColumns(horizons).map((col) => (
              <RpfSortHeader
                key={horizonColumnKey(col)}
                col={`${col.metric}:${col.horizon}`}
                label={`${col.metric === "fwd" ? "Fwd" : "MDD"} ${col.horizon}d`}
                activeKey={sortKey}
                dir={sortDir}
                onSort={onSort}
                numeric
              />
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr
              key={`${row.regime_decile}-${row.severity_decile}-${row.factor_decile}`}
              className="border-b border-border last:border-b-0"
              data-testid={`rpf-row-${row.regime_decile}-${row.severity_decile}-${row.factor_decile}`}
            >
              <td className="px-3 py-2"><span className="num font-semibold text-text">D{row.regime_decile}</span></td>
              <td className="px-3 py-2"><span className="num font-semibold text-text">D{row.severity_decile}</span></td>
              <td className="px-3 py-2"><span className="num font-semibold text-text">D{row.factor_decile}</span></td>
              {/* J-114: all forward-return cells first, then all max-drawdown cells (no interleave). */}
              {groupedHorizonColumns(horizons).map((col) => {
                const h = col.horizon;
                const cell = regimeCellAt(row.by_horizon, h);
                return (
                  <td
                    key={`rpfc-${row.regime_decile}-${row.severity_decile}-${row.factor_decile}-${horizonColumnKey(col)}`}
                    className="px-3 py-2 text-right"
                  >
                    {col.metric === "fwd" ? (
                      cell ? (
                        <RegimeReturnCell
                          cell={cell}
                          min={data.min_sample}
                          scope={scope}
                          cohort={{
                            kind: "regime-phase-factor",
                            horizon: h,
                            factor: factorKey,
                            regimeDecile: row.regime_decile,
                            severityDecile: row.severity_decile,
                            factorDecile: row.factor_decile,
                            view: REGIME_PHASE_FACTOR_VIEW,
                          }}
                          chipLabel={`Open the regime D${row.regime_decile} × severity D${row.severity_decile} × factor D${row.factor_decile} cohort (n=${cell.n}) at the ${h}-day horizon in Research Samples (new tab)`}
                        />
                      ) : (
                        <span className="text-text-faint">—</span>
                      )
                    ) : cell ? (
                      <RegimeMddCell cell={cell} min={data.min_sample} />
                    ) : (
                      <span className="text-text-faint">—</span>
                    )}
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

type RegimePhaseFactorState =
  | { kind: "loading" }
  | { kind: "ok"; data: RegimePhaseFactorResponse }
  | { kind: "error" };

/** iter-55 (J-112) — the Regime × Phase × Factor 3-way decile study on its OWN route
 *  (`/research/regime-phase-factor`). For a SELECTED factor, a ranked, filterable, client-side-sortable,
 *  paginated table of `(regime-score decile × severity-score decile × factor decile)` combinations — each row
 *  carrying, per EVERY config horizon at once (paired columns), the combination's mean realized forward return
 *  + paired mean max-drawdown + n. The three grouping dimensions are read VERBATIM from their single canonical
 *  sources (stored regime score / served severity / stored factor value); the page re-formats + client-side
 *  sorts (NA-last) / filters / paginates only — it recomputes nothing. The factor selector drives the `factor`
 *  param; the three decile filters + the sort + the pagination are pure view transforms. The As-of mode toggle
 *  FILTERS the observation set (the single global as-of — no second date state, J-18). The view is PINNED to
 *  pooled (no Episodes/Pooled toggle — the whole-cross-section episode collapse degenerates). */
export function RegimePhaseFactorPage() {
  const { mode, setMode, readiness, asofCutoff, scope } = useResearchControls();
  const [factor, setFactor] = useState<string | undefined>(undefined);
  const [state, setState] = useState<RegimePhaseFactorState>({ kind: "loading" });
  // three "All"-default decile filter dropdowns (regime / severity / factor) — pure view transforms.
  const [regimeFilter, setRegimeFilter] = useState<string>(RPF_FILTER_ALL);
  const [severityFilter, setSeverityFilter] = useState<string>(RPF_FILTER_ALL);
  const [factorFilter, setFactorFilter] = useState<string>(RPF_FILTER_ALL);
  const { sortKey, sortDir, onSort } = useRpfSort("");
  const [pageIndex, setPageIndex] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    setState({ kind: "loading" });
    fetchRegimePhaseFactor(factor, REGIME_PHASE_FACTOR_VIEW, asofCutoff ?? undefined, controller.signal)
      .then((data) => setState({ kind: "ok", data }))
      .catch(() => {
        if (!controller.signal.aborted) setState({ kind: "error" });
      });
    return () => controller.abort();
  }, [factor, asofCutoff, readiness]);

  const data = state.kind === "ok" ? state.data : null;

  // a pure client-side filter (the three "All"-default decile dropdowns) → sort (NA-last) → page slice. None
  // refetch or recompute a stored value (J-48/J-56 view-transform contract).
  const filteredRows = useMemo(() => {
    if (!data) return [];
    return data.rows.filter(
      (r) =>
        (regimeFilter === RPF_FILTER_ALL || r.regime_decile === Number(regimeFilter)) &&
        (severityFilter === RPF_FILTER_ALL || r.severity_decile === Number(severityFilter)) &&
        (factorFilter === RPF_FILTER_ALL || r.factor_decile === Number(factorFilter)),
    );
  }, [data, regimeFilter, severityFilter, factorFilter]);

  const sortedRows = useMemo(
    () => sortRpfRows(filteredRows, sortKey, sortDir),
    [filteredRows, sortKey, sortDir],
  );

  const pageSize = data?.page_size ?? sortedRows.length;
  const pageCount = Math.max(1, Math.ceil(sortedRows.length / Math.max(1, pageSize)));
  // any change to the result set / ordering / filter / factor / scope returns to the first page.
  useEffect(() => {
    setPageIndex(0);
  }, [data, regimeFilter, severityFilter, factorFilter, sortKey, sortDir]);
  const safePage = Math.min(pageIndex, pageCount - 1);
  const pageStart = safePage * pageSize;
  const pageRows = sortedRows.slice(pageStart, pageStart + pageSize);

  const selectedFactor = factor ?? data?.factor.key;

  return (
    <div className="space-y-4" data-testid="regime-phase-factor-page">
      <ResearchControls
        title="Research — Regime × Phase × Factor"
        subtitle="For a chosen factor, how have realized forward returns and downside risk differed across the THREE-WAY interaction of market-regime-score decile × severity-score decile × factor decile? A ranked, filterable, paginated combination table over the stored forward-tested evidence — each N= drilling into the exact reproducing cohort. Derived once from stored values; descriptive survivorship-biased association, never a forecast."
        mode={mode}
        onModeChange={setMode}
        asofCutoff={asofCutoff}
      />
      <ResearchCaveat survivorship={data?.survivorship_bias} descriptive={data?.descriptive_caveat} />
      {shouldShowWarming(readiness) ? (
        <WarmingState what="The Regime × Phase × Factor lab" />
      ) : (
        <Card className="p-0" data-testid="regime-phase-factor-section">
          <PanelTitle
            hint={`Pick a factor, then read how forward returns + downside risk differ across the (regime-score decile × severity-score decile × factor decile) interaction, at every horizon at once. Combinations with n < ${data?.min_sample ?? "min"} show NA + n, never a fabricated number. Columns are client-side sortable (NA-last); the three decile filters narrow the rows; the table paginates ${data?.page_size ?? 30} rows per page. Each N= chip opens the exact observations in a new tab.`}
          >
            Regime × Phase × Factor — ranked combinations
          </PanelTitle>
          <div className="space-y-4 p-4">
            <div className="flex flex-wrap items-end gap-3">
              <label className="flex flex-col gap-1">
                <span className="text-xs uppercase tracking-wide text-text-faint">Factor</span>
                <Select
                  data-testid="rpf-factor-select"
                  aria-label="Select factor"
                  value={selectedFactor ?? ""}
                  onChange={(e) => setFactor(e.target.value)}
                  className="w-64"
                  disabled={!data}
                >
                  {data
                    ? data.factors.map((f) => (
                        <option key={f.key} value={f.key}>
                          {f.label}
                        </option>
                      ))
                    : null}
                </Select>
              </label>
              {data ? (
                <>
                  <RpfDecileFilter
                    label="Regime decile"
                    ariaLabel="Filter by regime decile"
                    testId="rpf-regime-filter"
                    value={regimeFilter}
                    decilesCount={data.deciles_count}
                    onChange={setRegimeFilter}
                  />
                  <RpfDecileFilter
                    label="Severity decile"
                    ariaLabel="Filter by severity decile"
                    testId="rpf-severity-filter"
                    value={severityFilter}
                    decilesCount={data.deciles_count}
                    onChange={setSeverityFilter}
                  />
                  <RpfDecileFilter
                    label="Factor decile"
                    ariaLabel="Filter by factor decile"
                    testId="rpf-factor-filter"
                    value={factorFilter}
                    decilesCount={data.deciles_count}
                    onChange={setFactorFilter}
                  />
                </>
              ) : null}
              <p className="max-w-md text-xs text-text-faint">
                D1 = lowest decile → D{data?.deciles_count ?? 10} = highest, computed per horizon. Counts are
                pooled (every per-signal-day observation); the single global as-of toggle above scopes any
                point-in-time view (J-18). Fwd = mean realized forward return; MDD = paired mean max-drawdown.
              </p>
            </div>

            {data ? (
              <CaveatBanner survivorship={data.survivorship_bias} descriptive={data.descriptive_caveat} />
            ) : null}

            {state.kind === "error" ? (
              <div className="flex items-center gap-3 rounded-md border border-neg bg-surface p-4 text-sm text-neg">
                <AlertTriangle className="h-5 w-5 shrink-0" aria-hidden />
                <div>
                  <p className="font-medium">Backend unavailable</p>
                  <p className="text-text-muted">
                    The Regime × Phase × Factor study could not load from the API. No figures are shown rather
                    than fabricated values — confirm the backend is running and retry.
                  </p>
                </div>
              </div>
            ) : !data ? (
              <CombinationSkeleton />
            ) : data.rows.length === 0 ? (
              <EmptyState
                icon={Microscope}
                title="No forward-tested combinations for this factor"
                description="No stored snapshot has an observation with all three dimensions (regime score, served severity, and the selected factor) and a realized forward return. No combination is fabricated to fill the gap."
              />
            ) : sortedRows.length === 0 ? (
              <EmptyState
                icon={Microscope}
                title="No combinations match these filters"
                description="No (regime, severity, factor) decile combination matches the current filter selection. Reset a filter to “All” to widen the view — nothing is fabricated to fill the gap."
              />
            ) : (
              <>
                <RegimePhaseFactorTable
                  data={data}
                  rows={pageRows}
                  scope={scope}
                  sortKey={sortKey}
                  sortDir={sortDir}
                  onSort={onSort}
                />
                <div className="flex flex-wrap items-center justify-between gap-3 text-sm" data-testid="rpf-pagination">
                  <span className="text-text-faint">
                    Showing {pageStart + 1}–{Math.min(pageStart + pageSize, sortedRows.length)} of{" "}
                    {sortedRows.length} combinations
                  </span>
                  <div className="flex items-center gap-2">
                    <button
                      type="button"
                      data-testid="rpf-prev-page"
                      onClick={() => setPageIndex((p) => Math.max(0, p - 1))}
                      disabled={safePage <= 0}
                      aria-label="Previous page"
                      className={cn(
                        "rounded-md border border-border px-3 py-1.5 transition-colors",
                        safePage <= 0
                          ? "cursor-not-allowed text-text-faint/50"
                          : "text-text hover:border-accent hover:text-accent focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-accent",
                      )}
                    >
                      Prev
                    </button>
                    <span className="num text-text-muted" data-testid="rpf-page-indicator">
                      Page {safePage + 1} of {pageCount}
                    </span>
                    <button
                      type="button"
                      data-testid="rpf-next-page"
                      onClick={() => setPageIndex((p) => Math.min(pageCount - 1, p + 1))}
                      disabled={safePage >= pageCount - 1}
                      aria-label="Next page"
                      className={cn(
                        "rounded-md border border-border px-3 py-1.5 transition-colors",
                        safePage >= pageCount - 1
                          ? "cursor-not-allowed text-text-faint/50"
                          : "text-text hover:border-accent hover:text-accent focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-accent",
                      )}
                    >
                      Next
                    </button>
                  </div>
                </div>
              </>
            )}
          </div>
        </Card>
      )}
    </div>
  );
}
