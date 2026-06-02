"use client";

import { useEffect, useState } from "react";
import { AlertTriangle, Microscope, ShieldAlert } from "lucide-react";

import { EmptyState } from "@/components/empty-state";
import { fmtPct, returnClass, SampleSize } from "@/components/forward-return";
import { PageHeading } from "@/components/page-heading";
import { Card } from "@/components/ui/card";
import { Select } from "@/components/ui/select";
import { cn } from "@/lib/utils";
import {
  fetchFactorLab,
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
    </div>
  );
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
        {factors.map((f) => (
          <option key={f.key} value={f.key}>
            {f.label}
          </option>
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
