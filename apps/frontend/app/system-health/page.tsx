"use client";

import { useEffect, useState } from "react";
import { AlertTriangle, ShieldAlert } from "lucide-react";

import { EmptyState } from "@/components/empty-state";
import { PageHeading } from "@/components/page-heading";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { bucketVariant } from "@/components/score-badge";
import { cn } from "@/lib/utils";
import {
  fetchSystemHealth,
  type ControlGroupRow,
  type ExcessVsBenchmark,
  type SystemHealthResponse,
} from "@/lib/api";

// The horizon the page requests first. Matches config.walk_forward.default_horizon; the loaded
// payload's `horizons` then drives the actual selector (the UI never owns the canonical set).
const DEFAULT_HORIZON = 20;

type State =
  | { kind: "loading" }
  | { kind: "ok"; data: SystemHealthResponse }
  | { kind: "error" };

/** Format a return fraction (0.0123 -> "+1.23%"); null/empty groups render an em dash. */
function fmtPct(value: number | null): string {
  if (value === null || value === undefined) return "—";
  const pct = value * 100;
  return `${pct >= 0 ? "+" : ""}${pct.toFixed(2)}%`;
}

/** Positive returns green, negative red, zero/NA muted — palette tokens only (DESIGN SYSTEM). */
function returnClass(value: number | null): string {
  if (value === null || value === undefined) return "text-text-muted";
  if (value > 0) return "text-pos";
  if (value < 0) return "text-neg";
  return "text-text";
}

/** Sample size beside every figure; flagged with the warn token when n < min_sample (low sample). */
function SampleSize({ n, min }: { n: number; min: number }) {
  const low = n < min;
  return (
    <span
      className={cn("num text-xs", low ? "text-warn" : "text-text-faint")}
      title={low ? `Low sample — n below the ${min} minimum; treat as indicative only` : undefined}
    >
      n={n}
      {low ? " ⚠" : ""}
    </span>
  );
}

function Return({ value, n, min }: { value: number | null; n: number; min: number }) {
  return (
    <span className="inline-flex items-center justify-end gap-2">
      <span className={cn("num font-semibold", returnClass(value))}>{fmtPct(value)}</span>
      <SampleSize n={n} min={min} />
    </span>
  );
}

export default function SystemHealthPage() {
  const [horizon, setHorizon] = useState<number>(DEFAULT_HORIZON);
  const [state, setState] = useState<State>({ kind: "loading" });

  useEffect(() => {
    const controller = new AbortController();
    setState({ kind: "loading" });
    fetchSystemHealth(horizon, controller.signal)
      .then((data) => setState({ kind: "ok", data }))
      .catch(() => {
        if (!controller.signal.aborted) setState({ kind: "error" });
      });
    return () => controller.abort();
  }, [horizon]);

  // Horizon options come from the loaded payload (config-driven); fall back to the requested one
  // until the first payload arrives so the selector always renders.
  const horizons = state.kind === "ok" ? state.data.horizons : [horizon];

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <PageHeading
          title="System Health"
          subtitle="Forward-tested evidence — did higher-ranked buckets, stronger setups and risk-on regimes actually beat SPY/QQQ/sector and random peers?"
        />
        <HorizonSelector horizons={horizons} value={horizon} onChange={setHorizon} />
      </div>

      <SurvivorshipBanner
        text={
          state.kind === "ok"
            ? state.data.survivorship_bias
            : "Walk-forward evidence carries survivorship bias (current-membership universe) — results may be overstated."
        }
      />

      {state.kind === "loading" ? <HealthSkeleton /> : null}

      {state.kind === "error" ? (
        <Card className="flex items-center gap-3 border-neg bg-surface p-5 text-sm text-neg">
          <AlertTriangle className="h-5 w-5 shrink-0" aria-hidden />
          <div>
            <p className="font-medium">Backend unavailable</p>
            <p className="text-text-muted">
              The forward-tested evidence could not load from the API. No figures are shown rather
              than fabricated values. Confirm the backend is running and retry.
            </p>
          </div>
        </Card>
      ) : null}

      {state.kind === "ok" ? <HealthDashboard data={state.data} /> : null}
    </div>
  );
}

function HorizonSelector({
  horizons,
  value,
  onChange,
}: {
  horizons: number[];
  value: number;
  onChange: (h: number) => void;
}) {
  return (
    <div className="flex items-center gap-2">
      <span className="text-xs uppercase tracking-wide text-text-faint">Horizon</span>
      <div
        role="group"
        aria-label="Forward-return horizon (trading days)"
        className="inline-flex overflow-hidden rounded-md border border-border bg-surface-2"
      >
        {horizons.map((h) => {
          const active = h === value;
          return (
            <button
              key={h}
              type="button"
              aria-pressed={active}
              onClick={() => onChange(h)}
              className={cn(
                "num border-r border-border px-3 py-1.5 text-sm transition-colors last:border-r-0",
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

function SurvivorshipBanner({ text }: { text: string }) {
  return (
    <Card className="flex items-start gap-3 border-warn bg-surface p-4 text-sm">
      <ShieldAlert className="mt-0.5 h-5 w-5 shrink-0 text-warn" aria-hidden />
      <div>
        <p className="font-medium text-warn">Survivorship bias</p>
        <p className="text-text-muted">{text}</p>
      </div>
    </Card>
  );
}

function HealthDashboard({ data }: { data: SystemHealthResponse }) {
  const min = data.min_sample;
  const noEvidence = data.n_runs === 0 || data.overall.n === 0;

  if (noEvidence) {
    return (
      <EmptyState
        icon={ShieldAlert}
        title="No forward-tested evidence yet"
        description="No walk-forward snapshot has enough post-snapshot data to measure a realized return at this horizon. Pick a shorter horizon, or wait for the backfill to complete — no numbers are fabricated to fill the gap."
      />
    );
  }

  return (
    <>
      <div className="flex flex-wrap items-center gap-x-6 gap-y-1 text-xs text-text-muted">
        <span>
          <span className="text-text-faint">Snapshots contributing: </span>
          <span className="num text-text">{data.n_runs}</span>
        </span>
        <span>
          <span className="text-text-faint">As-of range: </span>
          <span className="num text-text">
            {data.asof_dates.length > 0
              ? `${data.asof_dates[data.asof_dates.length - 1]} → ${data.asof_dates[0]}`
              : "—"}
          </span>
        </span>
        <span>
          <span className="text-text-faint">Mean stock fwd return: </span>
          <span className={cn("num", returnClass(data.overall.mean_return))}>
            {fmtPct(data.overall.mean_return)}
          </span>{" "}
          <span className="num text-text-faint">(n={data.overall.n})</span>
        </span>
        <span className="text-text-faint">
          Figures with{" "}
          <span className="text-warn">n &lt; {min} ⚠</span> are low-sample.
        </span>
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <BucketPanel rows={data.by_bucket} min={min} horizon={data.horizon} />
        <ExcessPanel excess={data.excess} min={min} />
        <BreakdownPanel
          title="Forward return by setup type"
          rows={data.by_setup.map((r) => ({ label: r.setup, ...r }))}
          min={min}
          emptyLabel="No setup had a measurable forward return at this horizon."
        />
        <BreakdownPanel
          title="Forward return by market regime"
          rows={data.by_regime.map((r) => ({ label: r.regime, ...r }))}
          min={min}
          emptyLabel="No regime had a measurable forward return at this horizon."
        />
      </div>

      <ControlGroupPanel rows={data.control_group} min={min} horizon={data.horizon} />
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

function BucketPanel({
  rows,
  min,
  horizon,
}: {
  rows: { bucket: string; mean_return: number | null; n: number }[];
  min: number;
  horizon: number;
}) {
  return (
    <Card className="p-0">
      <PanelTitle hint={`Mean realized ${horizon}-day forward return per leadership bucket`}>
        Forward return by score bucket
      </PanelTitle>
      <table className="w-full border-collapse text-sm">
        <thead>
          <tr className="border-b border-border text-left text-xs uppercase tracking-wide text-text-faint">
            <th className="px-4 py-2 font-medium">Bucket</th>
            <th className="px-4 py-2 text-right font-medium">Mean fwd return</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.bucket} className="border-b border-border last:border-b-0">
              <td className="px-4 py-2">
                <Badge variant={bucketVariant(row.bucket)} className="num font-semibold">
                  {row.bucket}
                </Badge>
              </td>
              <td className="px-4 py-2 text-right">
                <Return value={row.mean_return} n={row.n} min={min} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </Card>
  );
}

function ExcessRow({ label, excess, min }: { label: string; excess: ExcessVsBenchmark; min: number }) {
  return (
    <tr className="border-b border-border last:border-b-0">
      <td className="px-4 py-2">
        <span className="text-text">{label}</span>{" "}
        <span className="num text-xs text-text-faint">({excess.benchmark})</span>
      </td>
      <td className="num px-4 py-2 text-right text-text-muted">{fmtPct(excess.stock_mean)}</td>
      <td className="num px-4 py-2 text-right text-text-muted">{fmtPct(excess.benchmark_mean)}</td>
      <td className="px-4 py-2 text-right">
        <Return value={excess.mean_excess} n={excess.n} min={min} />
      </td>
    </tr>
  );
}

function ExcessPanel({
  excess,
  min,
}: {
  excess: { vs_spy: ExcessVsBenchmark; vs_qqq: ExcessVsBenchmark };
  min: number;
}) {
  return (
    <Card className="p-0">
      <PanelTitle hint="Mean stock forward return minus the benchmark's, over matched snapshots">
        Excess vs benchmarks
      </PanelTitle>
      <table className="w-full border-collapse text-sm">
        <thead>
          <tr className="border-b border-border text-left text-xs uppercase tracking-wide text-text-faint">
            <th className="px-4 py-2 font-medium">Excess</th>
            <th className="px-4 py-2 text-right font-medium">Stocks</th>
            <th className="px-4 py-2 text-right font-medium">Benchmark</th>
            <th className="px-4 py-2 text-right font-medium">Excess</th>
          </tr>
        </thead>
        <tbody>
          <ExcessRow label="Excess vs SPY" excess={excess.vs_spy} min={min} />
          <ExcessRow label="Excess vs QQQ" excess={excess.vs_qqq} min={min} />
        </tbody>
      </table>
    </Card>
  );
}

function BreakdownPanel({
  title,
  rows,
  min,
  emptyLabel,
}: {
  title: string;
  rows: { label: string; mean_return: number | null; n: number }[];
  min: number;
  emptyLabel: string;
}) {
  return (
    <Card className="p-0">
      <PanelTitle>{title}</PanelTitle>
      {rows.length === 0 ? (
        <p className="px-4 py-4 text-sm text-text-muted">{emptyLabel}</p>
      ) : (
        <table className="w-full border-collapse text-sm">
          <tbody>
            {rows.map((row) => (
              <tr key={row.label} className="border-b border-border last:border-b-0">
                <td className="px-4 py-2 text-text">{row.label}</td>
                <td className="px-4 py-2 text-right">
                  <Return value={row.mean_return} n={row.n} min={min} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </Card>
  );
}

function ControlGroupPanel({
  rows,
  min,
  horizon,
}: {
  rows: ControlGroupRow[];
  min: number;
  horizon: number;
}) {
  return (
    <Card className="p-0">
      <PanelTitle
        hint={`At ${horizon} days: does the top-ranked cohort beat random same-sector peers and the benchmarks — i.e. is the ranking adding value beyond sector beta?`}
      >
        Control-group comparison — selection vs sector beta
      </PanelTitle>
      <table className="w-full border-collapse text-sm">
        <thead>
          <tr className="border-b border-border text-left text-xs uppercase tracking-wide text-text-faint">
            <th className="px-4 py-2 font-medium">Cohort</th>
            <th className="px-4 py-2 text-right font-medium">Mean fwd return</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => {
            const highlight = row.key === "top_ranked";
            return (
              <tr
                key={row.key}
                className={cn("border-b border-border last:border-b-0", highlight && "bg-surface-2")}
              >
                <td className="px-4 py-2">
                  <span className={cn(highlight ? "font-semibold text-text" : "text-text")}>
                    {row.label}
                  </span>
                </td>
                <td className="px-4 py-2 text-right">
                  <Return value={row.mean_return} n={row.n} min={min} />
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </Card>
  );
}

function HealthSkeleton() {
  return (
    <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
      {Array.from({ length: 4 }).map((_, i) => (
        <Card key={i} className="space-y-2 p-4">
          {Array.from({ length: 5 }).map((__, j) => (
            <div key={j} className="h-7 w-full animate-pulse rounded bg-surface-2" />
          ))}
        </Card>
      ))}
    </div>
  );
}
