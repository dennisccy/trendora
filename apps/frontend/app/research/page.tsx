"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { AlertTriangle, Microscope, Plus, ShieldAlert, X } from "lucide-react";

import { useAsOf } from "@/components/asof-provider";
import { EmptyState } from "@/components/empty-state";
import { fmtPct, returnClass, SampleSize } from "@/components/forward-return";
import { PageHeading } from "@/components/page-heading";
import { Card } from "@/components/ui/card";
import { Select } from "@/components/ui/select";
import { cn } from "@/lib/utils";
import {
  fetchEventStudy,
  fetchFactorCombination,
  fetchFactorLab,
  type CohortStats,
  type EventStudyHorizonRow,
  type EventStudyRegimeRow,
  type EventStudyResponse,
  type EventStudySectorRow,
  type FactorCombinationCondition,
  type FactorCombinationResponse,
  type FactorDecileRow,
  type FactorLabResponse,
  type RegimeEffectivenessRow,
} from "@/lib/api";

type State =
  | { kind: "loading" }
  | { kind: "ok"; data: FactorLabResponse }
  | { kind: "error" };

/** Format a unitless ratio (the downside risk-adjusted column / the rank-IC) with sign + 2 decimals;
 *  null/NA renders an em dash. This is NOT a percent — `fmtPct` would be wrong for a ratio. */
function fmtRatio(value: number | null): string {
  if (value === null || value === undefined) return "—";
  return `${value >= 0 ? "+" : ""}${value.toFixed(2)}`;
}

export default function ResearchPage() {
  // `undefined` lets the backend pick the canonical default (first catalog factor / config default
  // horizon). The selectors are built from the loaded payload — config-driven, never a hard-coded list.
  const [factor, setFactor] = useState<string | undefined>(undefined);
  const [horizon, setHorizon] = useState<number | undefined>(undefined);
  // J-32: the analysis MODE — "all" (default, pool every snapshot) vs "asof" (point-in-time / walk-forward).
  // It is a MODE, NOT a date control: As-of mode reads the SINGLE global as-of below (no second date state).
  const [mode, setMode] = useState<"all" | "asof">("all");
  const [state, setState] = useState<State>({ kind: "loading" });
  // The single global as-of date (the only date control on the whole app). At the latest date it is null.
  const { asOf } = useAsOf();
  // ONE resolved cutoff shared by all three labs (J-32). As-of mode reads the global `asOf`; All-history
  // mode ignores it (null). At the latest date `asOf` is already null → As-of@latest == all-history
  // (matches J-09). The fetch effects depend on THIS resolved cutoff, NOT raw `asOf`: so toggling
  // asof→all refetches (full sample returns), while in All-history mode moving the global date does NOT
  // refetch the labs (cutoff stays null) — preserving the J-15 read-path discipline + the genuine
  // cross-date nature of all-history. Sending `?as_of=` here is the single global date transmitted on a
  // snapshot-served read (like /api/stocks?as_of=), NOT a second date state (J-18).
  const asofCutoff = mode === "asof" ? asOf : null;

  useEffect(() => {
    const controller = new AbortController();
    setState({ kind: "loading" });
    fetchFactorLab(factor, horizon, asofCutoff ?? undefined, controller.signal)
      .then((data) => setState({ kind: "ok", data }))
      .catch(() => {
        if (!controller.signal.aborted) setState({ kind: "error" });
      });
    return () => controller.abort();
  }, [factor, horizon, asofCutoff]);

  const data = state.kind === "ok" ? state.data : null;
  const selectedFactor = factor ?? data?.factor.key ?? "";
  const selectedHorizon = horizon ?? data?.horizon;

  return (
    <div className="space-y-4">
      <div className="space-y-2">
        <div className="flex flex-wrap items-end justify-between gap-3">
          <PageHeading
            title="Research — Factor Lab"
            subtitle="Does a factor actually sort future returns? Decile means + a downside risk-adjusted column + the rank-IC, derived once from the stored forward-tested evidence. Descriptive, not predictive."
          />
          <div className="flex flex-wrap items-end gap-3">
            <AnalysisModeToggle mode={mode} onChange={setMode} />
            <FactorSelector
              factors={data?.factors ?? []}
              value={selectedFactor}
              onChange={(key) => setFactor(key)}
            />
            <HorizonSelector
              horizons={data?.horizons ?? []}
              value={selectedHorizon}
              onChange={(h) => setHorizon(h)}
            />
          </div>
        </div>
        <ModeContext mode={mode} asofCutoff={asofCutoff} />
      </div>

      <CaveatBanner
        survivorship={
          data?.survivorship_bias ??
          "Walk-forward evidence carries survivorship bias (current-membership universe) — results may be overstated."
        }
        descriptive={
          data?.descriptive_caveat ??
          "Descriptive evidence, not a predictive model — read these as historical association on a universe-relative seed."
        }
      />

      {state.kind === "loading" ? <LabSkeleton /> : null}

      {state.kind === "error" ? (
        <Card className="flex items-center gap-3 border-neg bg-surface p-5 text-sm text-neg">
          <AlertTriangle className="h-5 w-5 shrink-0" aria-hidden />
          <div>
            <p className="font-medium">Backend unavailable</p>
            <p className="text-text-muted">
              The Factor-Lab evidence could not load from the API. No figures are shown rather than
              fabricated values. Confirm the backend is running and retry.
            </p>
          </div>
        </Card>
      ) : null}

      {data ? <FactorLab data={data} /> : null}

      {/* J-26: the multi-factor combination cohort section — its own read-only data source, reusing the
          page's shared `horizon` + the shared `asofCutoff` (no second date/horizon state). Always rendered. */}
      <CombinationLab horizon={horizon} asofCutoff={asofCutoff} />

      {/* J-29: the Setup & Pattern event study — its own read-only data source, reusing the page's shared
          `horizon` + the shared `asofCutoff` (no second date/horizon state) plus a subject selector. */}
      <EventStudyLab horizon={horizon} asofCutoff={asofCutoff} />
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

/** Group the config-driven factors by `family`, preserving first-appearance order — derived entirely
 *  from the payload (no hard-coded family or factor list in the frontend). J-30's volatility family
 *  (ATR%, HV, VCP-style contraction, downside/semivol) collects under one "Volatility" heading. */
function groupByFamily(
  factors: FactorLabResponse["factors"],
): { family: string; items: FactorLabResponse["factors"] }[] {
  const groups: { family: string; items: FactorLabResponse["factors"] }[] = [];
  for (const f of factors) {
    const existing = groups.find((g) => g.family === f.family);
    if (existing) existing.items.push(f);
    else groups.push({ family: f.family, items: [f] });
  }
  return groups;
}

/** Present a family key as a heading (capitalised first letter) — purely presentational. */
function familyLabel(family: string): string {
  return family.charAt(0).toUpperCase() + family.slice(1);
}

function FactorSelector({
  factors,
  value,
  onChange,
}: {
  factors: FactorLabResponse["factors"];
  value: string;
  onChange: (key: string) => void;
}) {
  return (
    <label className="flex flex-col gap-1">
      <span className="text-xs uppercase tracking-wide text-text-faint">Factor</span>
      <Select
        data-testid="factor-select"
        aria-label="Factor"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-56"
        disabled={factors.length === 0}
      >
        {factors.length === 0 ? <option value="">Loading…</option> : null}
        {/* Grouped by family (config-driven <optgroup>); option values are unchanged so selection
            semantics stay identical — purely presentational, no recompute, no hard-coded list. */}
        {groupByFamily(factors).map((group) => (
          <optgroup key={group.family} label={familyLabel(group.family)}>
            {group.items.map((f) => (
              <option key={f.key} value={f.key}>
                {f.label}
              </option>
            ))}
          </optgroup>
        ))}
      </Select>
    </label>
  );
}

function HorizonSelector({
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

function FactorLab({ data }: { data: FactorLabResponse }) {
  if (data.n_total === 0) {
    return (
      <EmptyState
        icon={Microscope}
        title="No forward-tested observations for this factor / horizon"
        description="No stored snapshot has both this factor's value and a realized forward return at this horizon. Pick a shorter horizon or a different factor — no decile or rank-IC is fabricated to fill the gap."
      />
    );
  }
  return (
    <>
      <div className="flex flex-wrap items-center gap-x-6 gap-y-1 text-xs text-text-muted">
        <span>
          <span className="text-text-faint">Factor: </span>
          <span className="text-text">{data.factor.label}</span>{" "}
          <span className="text-text-faint">({data.factor.family} · {data.factor.direction.replace("_", " ")})</span>
        </span>
        <span>
          <span className="text-text-faint">Observations: </span>
          <span className="num text-text">{data.n_total}</span>
        </span>
        <span>
          <span className="text-text-faint">Horizon: </span>
          <span className="num text-text">{data.horizon}d</span>
        </span>
        <span className="text-text-faint">
          Deciles with <span className="text-warn">n &lt; {data.min_sample} ⚠</span> render NA.
        </span>
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <DecileTable rows={data.deciles} min={data.min_sample} horizon={data.horizon} />
        </div>
        <RankICCard ic={data.rank_ic} min={data.min_sample} label={data.factor.label} />
      </div>

      <RegimeEffectivenessTable rows={data.by_regime} min={data.min_sample} horizon={data.horizon} />
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

/** A decile's mean/risk-adjusted cell: explicit "NA" + n when the decile is low-sample (n < min_sample)
 *  or empty — never a fabricated number; otherwise the colour-graded value + n. */
function DecileValue({
  value,
  lowSample,
  isRatio,
  n,
  min,
}: {
  value: number | null;
  lowSample: boolean;
  isRatio: boolean;
  n: number;
  min: number;
}) {
  const na = lowSample || n === 0 || value === null;
  return (
    <span className="inline-flex items-center justify-end gap-2">
      {na ? (
        <span className="num font-semibold text-text-muted" title={lowSample ? `Low sample — n below the ${min} minimum` : "No observations"}>
          NA
        </span>
      ) : (
        <span className={cn("num font-semibold", returnClass(value))}>
          {isRatio ? fmtRatio(value) : fmtPct(value)}
        </span>
      )}
      <SampleSize n={n} min={min} />
    </span>
  );
}

function DecileTable({ rows, min, horizon }: { rows: FactorDecileRow[]; min: number; horizon: number }) {
  return (
    <Card className="p-0">
      <PanelTitle
        hint={`Mean realized ${horizon}-day forward return per factor decile (D1 = lowest factor value → D10 = highest), with a downside risk-adjusted column. Monotonicity across D1→D10 = the factor sorts future returns.`}
      >
        Decile sort — raw &amp; downside risk-adjusted
      </PanelTitle>
      <div className="overflow-x-auto">
        <table className="w-full border-collapse text-sm">
          <thead>
            <tr className="border-b border-border text-left text-xs uppercase tracking-wide text-text-faint">
              <th className="px-4 py-2 font-medium">Decile</th>
              <th className="px-4 py-2 text-right font-medium">Factor range</th>
              <th className="px-4 py-2 text-right font-medium">Mean fwd return</th>
              <th className="px-4 py-2 text-right font-medium">Risk-adjusted (downside)</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.decile} className="border-b border-border last:border-b-0">
                <td className="px-4 py-2">
                  <span className="num font-semibold text-text">D{row.decile}</span>
                </td>
                <td className="num px-4 py-2 text-right text-xs text-text-faint">
                  {row.factor_min === null || row.factor_max === null
                    ? "—"
                    : `${row.factor_min.toFixed(2)} … ${row.factor_max.toFixed(2)}`}
                </td>
                <td className="px-4 py-2 text-right">
                  <DecileValue value={row.mean_return} lowSample={row.low_sample} isRatio={false} n={row.n} min={min} />
                </td>
                <td className="px-4 py-2 text-right">
                  <DecileValue value={row.risk_adjusted} lowSample={row.low_sample} isRatio n={row.n} min={min} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Card>
  );
}

function RankICCard({
  ic,
  min,
  label,
}: {
  ic: FactorLabResponse["rank_ic"];
  min: number;
  label: string;
}) {
  const na = ic.value === null;
  const sign = ic.value !== null && ic.value > 0 ? "positive" : ic.value !== null && ic.value < 0 ? "negative" : "flat";
  return (
    <Card className="p-0">
      <PanelTitle hint="Spearman rank correlation between the factor and the realized forward return across all observations.">
        Rank-IC
      </PanelTitle>
      <div className="space-y-3 p-5">
        <div className="flex items-baseline gap-3">
          <span
            data-testid="rank-ic-value"
            className={cn(
              "num text-3xl font-semibold",
              na ? "text-text-muted" : sign === "positive" ? "text-pos" : sign === "negative" ? "text-neg" : "text-text",
            )}
          >
            {na ? "NA" : fmtRatio(ic.value)}
          </span>
          <SampleSize n={ic.n} min={min} />
        </div>
        <p className="text-xs text-text-muted">
          {na
            ? `Not enough independent observations to rank-correlate ${label} with forward return — NA, not a fabricated 0.`
            : sign === "positive"
              ? `A higher ${label} is associated with a higher forward return in this universe (positive rank correlation).`
              : sign === "negative"
                ? `A higher ${label} is associated with a lower forward return in this universe (negative rank correlation).`
                : `${label} shows no monotone rank relationship with forward return in this universe.`}
        </p>
      </div>
    </Card>
  );
}

/** A regime row's numeric cell: explicit "NA" (muted) when the regime is low-sample (n < min_sample) or
 *  the value is null — never a fabricated number; otherwise the colour-graded value. The honest `n` is
 *  carried once per row by the SampleSize chip in the dedicated `n` column (not repeated per cell). */
function RegimeCell({
  value,
  lowSample,
  isRatio,
}: {
  value: number | null;
  lowSample: boolean;
  isRatio: boolean;
}) {
  if (lowSample || value === null) {
    return (
      <span
        className="num font-semibold text-text-muted"
        title={lowSample ? "Low sample — n below the minimum; NA, not a fabricated number" : "No value for this regime"}
      >
        NA
      </span>
    );
  }
  return (
    <span className={cn("num font-semibold", returnClass(value))}>
      {isRatio ? fmtRatio(value) : fmtPct(value)}
    </span>
  );
}

/** Factor effectiveness by market regime (J-27): one row per CONFIGURED regime label (server-driven from
 *  the payload — never a hard-coded frontend regime list), each with its per-regime n, rank-IC, top/bottom
 *  decile means, and the raw + downside-risk-adjusted top-minus-bottom-decile spread. Low-sample or null
 *  cells render NA + the honest n — so a factor strong in the pooled table can be seen to be regime-
 *  dependent. Re-formats the payload only — recomputes no return/factor/regime. */
function RegimeEffectivenessTable({
  rows,
  min,
  horizon,
}: {
  rows: RegimeEffectivenessRow[];
  min: number;
  horizon: number;
}) {
  return (
    <Card className="p-0">
      <PanelTitle
        hint={`Does this factor still sort ${horizon}-day forward returns WITHIN each market regime? Per configured regime: the rank-IC and the long-short (top-minus-bottom-decile) spread — raw and downside-risk-adjusted. A factor strong in the pooled table can be regime-dependent here; regimes with n < ${min} show NA + n, never a fabricated number.`}
      >
        Factor effectiveness by market regime
      </PanelTitle>
      <div className="overflow-x-auto">
        <table data-testid="regime-effectiveness-table" className="w-full border-collapse text-sm">
          <thead>
            <tr className="border-b border-border text-left text-xs uppercase tracking-wide text-text-faint">
              <th className="px-4 py-2 font-medium">Regime</th>
              <th className="px-4 py-2 text-right font-medium">n</th>
              <th className="px-4 py-2 text-right font-medium">Rank-IC</th>
              <th className="px-4 py-2 text-right font-medium">Top-decile mean</th>
              <th className="px-4 py-2 text-right font-medium">Bottom-decile mean</th>
              <th className="px-4 py-2 text-right font-medium">Spread (top − bottom)</th>
              <th className="px-4 py-2 text-right font-medium">Risk-adjusted spread</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.regime} className="border-b border-border last:border-b-0">
                <td className="px-4 py-2 text-text">{row.regime}</td>
                <td className="px-4 py-2 text-right">
                  <SampleSize n={row.n} min={min} />
                </td>
                <td className="px-4 py-2 text-right">
                  <RegimeCell value={row.rank_ic.value} lowSample={row.low_sample} isRatio />
                </td>
                <td className="px-4 py-2 text-right">
                  <RegimeCell value={row.top_decile_mean} lowSample={row.low_sample} isRatio={false} />
                </td>
                <td className="px-4 py-2 text-right">
                  <RegimeCell value={row.bottom_decile_mean} lowSample={row.low_sample} isRatio={false} />
                </td>
                <td className="px-4 py-2 text-right">
                  <RegimeCell value={row.spread} lowSample={row.low_sample} isRatio={false} />
                </td>
                <td className="px-4 py-2 text-right">
                  <RegimeCell value={row.risk_adjusted_spread} lowSample={row.low_sample} isRatio />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Card>
  );
}

function LabSkeleton() {
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
function CombinationLab({
  horizon,
  asofCutoff,
}: {
  horizon: number | undefined;
  asofCutoff: string | null;
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
            <CombinationTable data={data} dim={status === "loading"} />
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
function CombinationTable({ data, dim }: { data: FactorCombinationResponse; dim: boolean }) {
  const min = data.min_sample;
  const tableRows: { label: string; stats: CohortStats; emphasis?: "baseline" | "composite" | "strict_overlap" }[] = [
    { label: data.baseline.label, stats: data.baseline.stats, emphasis: "baseline" },
    ...data.singles.map((s) => ({ label: conditionLabel(s.condition), stats: s.stats })),
    { label: data.composite.label, stats: data.composite.stats, emphasis: "composite" },
    { label: data.strict_overlap.label, stats: data.strict_overlap.stats, emphasis: "strict_overlap" },
  ];
  return (
    <div className={cn("overflow-x-auto transition-opacity", dim && "opacity-60")} aria-busy={dim}>
      <table data-testid="combination-table" className="w-full border-collapse text-sm">
        <thead>
          <tr className="border-b border-border text-left text-xs uppercase tracking-wide text-text-faint">
            <th className="px-4 py-2 font-medium">Cohort</th>
            <th className="px-4 py-2 text-right font-medium">n</th>
            <th className="px-4 py-2 text-right font-medium">Mean fwd return</th>
            <th className="px-4 py-2 text-right font-medium">Median</th>
            <th className="px-4 py-2 text-right font-medium">Hit-rate</th>
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
                <SampleSize n={row.stats.n} min={min} />
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
function EventStudyLab({
  horizon,
  asofCutoff,
}: {
  horizon: number | undefined;
  asofCutoff: string | null;
}) {
  // `undefined` lets the backend pick the canonical default (first catalog subject). The subject list is
  // built from the loaded payload — config-driven, never a hard-coded frontend list.
  const [subject, setSubject] = useState<string | undefined>(undefined);
  const [data, setData] = useState<EventStudyResponse | null>(null);
  const [status, setStatus] = useState<"loading" | "ok" | "error">("loading");

  useEffect(() => {
    const controller = new AbortController();
    setStatus("loading");
    // depends on the RESOLVED `asofCutoff` (not raw asOf): All-history mode never refetches on a global
    // date change (cutoff stays null); toggling mode re-points the study to the new window (J-32/J-15).
    fetchEventStudy(subject, horizon, asofCutoff ?? undefined, controller.signal)
      .then((d) => {
        if (controller.signal.aborted) return;
        setData(d);
        setStatus("ok");
      })
      .catch(() => {
        if (!controller.signal.aborted) setStatus("error");
      });
    return () => controller.abort();
  }, [subject, horizon, asofCutoff]);

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
          <p className="max-w-md text-xs text-text-faint">
            Re-uses the page&apos;s shared horizon selector and the page-level analysis-mode toggle above —
            no date control of its own (the single global as-of drives any point-in-time scoping, J-18).
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
          <EventStudyBody data={data} dim={status === "loading"} />
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
  const href =
    subject.kind === "pattern"
      ? `/stocks?pattern=${encodeURIComponent(subject.key)}__only`
      : `/stocks?setup=${encodeURIComponent(subject.key)}`;
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
function EventStudyBody({ data, dim }: { data: EventStudyResponse; dim: boolean }) {
  const selectedHorizon = data.horizon;
  return (
    <div className={cn("space-y-4 transition-opacity", dim && "opacity-60")} aria-busy={dim}>
      <div className="flex flex-wrap items-center gap-x-6 gap-y-1 text-xs text-text-muted">
        <span>
          <span className="text-text-faint">Subject: </span>
          <span className="text-text">{data.subject.label}</span>{" "}
          <span className="text-text-faint">({data.subject.kind})</span>
        </span>
        <span>
          <span className="text-text-faint">Pooled occurrences ({selectedHorizon}d): </span>
          <span className="num text-text">{data.n_total}</span>
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

      <EventStudyHorizonTable rows={data.by_horizon} min={data.min_sample} bestExit={data.best_exit_horizon} />

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <EventStudyRegimeTable rows={data.by_regime} min={data.min_sample} horizon={selectedHorizon} />
        <EventStudySectorTable rows={data.by_sector} min={data.min_sample} horizon={selectedHorizon} />
      </div>
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
}: {
  rows: EventStudyHorizonRow[];
  min: number;
  bestExit: number | null;
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
              <th className="px-3 py-2 font-medium">Horizon</th>
              <th className="px-3 py-2 text-right font-medium">n</th>
              <th className="px-3 py-2 text-right font-medium">Mean</th>
              <th className="px-3 py-2 text-right font-medium">Median</th>
              <th className="px-3 py-2 text-right font-medium">% Positive</th>
              <th className="px-3 py-2 text-right font-medium">Dispersion</th>
              <th className="px-3 py-2 text-right font-medium">Expectancy</th>
              <th className="px-3 py-2 text-right font-medium">Mean MAE</th>
              <th className="px-3 py-2 text-right font-medium">Mean MFE</th>
              <th className="px-3 py-2 text-right font-medium">Return / downside-dev</th>
              <th className="px-3 py-2 text-right font-medium">Return / MAE</th>
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
                    <SampleSize n={row.n} min={min} />
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
}: {
  rows: EventStudyRegimeRow[];
  min: number;
  horizon: number;
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
                    <SampleSize n={row.n} min={min} />
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
}: {
  rows: EventStudySectorRow[];
  min: number;
  horizon: number;
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
                      <SampleSize n={row.n} min={min} />
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
