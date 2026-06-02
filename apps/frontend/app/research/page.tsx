"use client";

import { useEffect, useState } from "react";
import { AlertTriangle, Microscope, Plus, ShieldAlert, X } from "lucide-react";

import { EmptyState } from "@/components/empty-state";
import { fmtPct, returnClass, SampleSize } from "@/components/forward-return";
import { PageHeading } from "@/components/page-heading";
import { Card } from "@/components/ui/card";
import { Select } from "@/components/ui/select";
import { cn } from "@/lib/utils";
import {
  fetchFactorCombination,
  fetchFactorLab,
  type CohortStats,
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
  const [state, setState] = useState<State>({ kind: "loading" });

  useEffect(() => {
    const controller = new AbortController();
    setState({ kind: "loading" });
    fetchFactorLab(factor, horizon, controller.signal)
      .then((data) => setState({ kind: "ok", data }))
      .catch(() => {
        if (!controller.signal.aborted) setState({ kind: "error" });
      });
    return () => controller.abort();
  }, [factor, horizon]);

  const data = state.kind === "ok" ? state.data : null;
  const selectedFactor = factor ?? data?.factor.key ?? "";
  const selectedHorizon = horizon ?? data?.horizon;

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <PageHeading
          title="Research — Factor Lab"
          subtitle="Does a factor actually sort future returns? Decile means + a downside risk-adjusted column + the rank-IC, derived once from the stored forward-tested evidence. Descriptive, not predictive."
        />
        <div className="flex flex-wrap items-end gap-3">
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
          page's shared `horizon` (no second date/horizon state). Always rendered (own loading/error). */}
      <CombinationLab horizon={horizon} />
    </div>
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
 *  cohort. Reuses the page's shared `horizon` (no second date/horizon state); adds ONLY `conditions`
 *  state. A cross-date aggregate — NO as-of/date control (J-18). Re-formats the payload only — recomputes
 *  no return/factor; low-sample/empty cohorts render NA + n (never a fabricated number). The factor +
 *  quantile option lists come from the payload (config-driven) — no hard-coded list here. */
function CombinationLab({ horizon }: { horizon: number | undefined }) {
  // null until the user first edits — then the explicit condition list. The server resolves the config
  // default_conditions when none are sent (config-driven; no hard-coded default in the UI).
  const [conditions, setConditions] = useState<ConditionInput[] | null>(null);
  const [data, setData] = useState<FactorCombinationResponse | null>(null);
  const [status, setStatus] = useState<"loading" | "ok" | "error">("loading");

  useEffect(() => {
    const controller = new AbortController();
    setStatus("loading");
    fetchFactorCombination(conditions ?? [], horizon, controller.signal)
      .then((d) => {
        if (controller.signal.aborted) return;
        setData(d);
        setStatus("ok");
      })
      .catch(() => {
        if (!controller.signal.aborted) setStatus("error");
      });
    return () => controller.abort();
  }, [conditions, horizon]);

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
        hint={`Combine 2–${data?.max_conditions ?? 3} factor conditions (each a catalog factor at its top/bottom quantile) and compare the combined-AND cohort against the all-names baseline and each single-factor cohort — does combining factors beat either alone? Each cohort shows mean / median forward return, hit-rate, and the downside risk-adjusted column with n; cohorts with n < ${data?.min_sample ?? "min"} show NA + n, never a fabricated number.`}
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
              measures arrive with the event-study lab (J-29).
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

/** The comparison table: Baseline (all names) vs each single-condition cohort vs the Combined (AND) cohort
 *  — columns Cohort / n / Mean fwd return / Median / Hit-rate / Risk-adjusted (downside). Re-formats the
 *  payload only; low-sample/empty/null cells render NA + n via CohortCell + SampleSize. */
function CombinationTable({ data, dim }: { data: FactorCombinationResponse; dim: boolean }) {
  const min = data.min_sample;
  const tableRows: { label: string; stats: CohortStats; emphasis?: "baseline" | "combined" }[] = [
    { label: data.baseline.label, stats: data.baseline.stats, emphasis: "baseline" },
    ...data.singles.map((s) => ({ label: conditionLabel(s.condition), stats: s.stats })),
    { label: data.combined.label, stats: data.combined.stats, emphasis: "combined" },
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
          {tableRows.map((row, i) => (
            <tr
              key={i}
              className={cn(
                "border-b border-border last:border-b-0",
                row.emphasis === "combined" && "bg-surface-2",
              )}
            >
              <td className="px-4 py-2">
                <span className={cn(row.emphasis ? "font-semibold text-text" : "text-text-muted")}>
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
          ))}
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
