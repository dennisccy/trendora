import { ShieldAlert } from "lucide-react";

import { EmptyState } from "@/components/empty-state";
import { fmtPct, Return, returnClass } from "@/components/forward-return";
import { bucketVariant } from "@/components/score-badge";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { formatIsoDate } from "@/lib/dates";
import { cn } from "@/lib/utils";
import type { ControlGroupRow, EvidenceAggregate, ExcessVsBenchmark } from "@/lib/api";

/**
 * Forward-tested evidence panels — the SINGLE shared rendering of the as-of-scoped forward-return
 * aggregate (Data Contract: app.engine.forward_testing.compute_forward_aggregates). Extracted from the
 * retired System Health page (iter-17) so its one UI home is now the Backtest workspace. Every panel
 * RE-FORMATS values the backend already derived from the stored per-observation forward returns; none
 * recomputes a return/excess/bucket. NA (n=0) renders an em dash and figures below `min_sample` carry
 * the shared `--warn` low-sample flag (palette tokens only, per the DESIGN SYSTEM).
 */

function PanelTitle({ children, hint }: { children: React.ReactNode; hint?: string }) {
  return (
    <div className="border-b border-border px-4 py-3">
      <h3 className="text-sm font-semibold text-text">{children}</h3>
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

/**
 * The full forward-tested evidence section (J-09/J-10/J-16/J-28) — the as-of-scoped EXPANDING-WINDOW
 * aggregate over every snapshot dated <= the resolved global as-of date. Rendered on Backtest from the
 * single `/api/backtest` payload's `evidence_by_horizon[selectedHorizon]` (no refetch on horizon change).
 * Visually distinct from, and clearly labelled apart from, the per-date scorecard (which shows only what
 * THIS date's cohort did). `evidence.horizon` already equals the selected horizon. NA when the window has
 * no measurable forward return — never a fabricated figure.
 */
export function EvidenceAggregateSection({
  evidence,
  asofDate,
}: {
  evidence: EvidenceAggregate;
  asofDate: string;
}) {
  const min = evidence.min_sample;
  const horizon = evidence.horizon;
  const noEvidence = evidence.n_runs === 0 || evidence.overall.n === 0;

  return (
    <section className="space-y-4" data-testid="evidence-aggregate">
      <div>
        <h2 className="text-sm font-semibold text-text">
          Forward-tested evidence (expanding window ≤ {formatIsoDate(asofDate)})
        </h2>
        <p className="mt-0.5 max-w-3xl text-xs text-text-faint">
          The forward-test track record accumulated from{" "}
          <span className="text-text">every snapshot dated on or before {formatIsoDate(asofDate)}</span> — by bucket,
          setup and regime, excess vs benchmarks, VCP/pattern, and the control group. Moving the global
          as-of date earlier shrinks the sample (n); at the latest date this equals the full all-history
          aggregate. Distinct from the per-date scorecard above (which shows only what <em>this</em>{" "}
          date&rsquo;s cohort did). Read-only over the stored forward returns — never recomputed;
          survivorship-biased / universe-relative.
        </p>
      </div>

      {noEvidence ? (
        <EmptyState
          icon={ShieldAlert}
          title="No forward-tested evidence for this window yet"
          description="No snapshot dated on or before this as-of date has enough post-snapshot data to measure a realized return at this horizon. Move the global as-of date later (toward the present) to accumulate evidence — no numbers are fabricated to fill the gap."
        />
      ) : (
        <>
          <div
            className="flex flex-wrap items-center gap-x-6 gap-y-1 text-xs text-text-muted"
            data-testid="evidence-summary"
          >
            <span>
              <span className="text-text-faint">Snapshots contributing (≤ {formatIsoDate(asofDate)}): </span>
              <span className="num text-text">{evidence.n_runs}</span>
            </span>
            <span>
              <span className="text-text-faint">As-of range: </span>
              <span className="num text-text">
                {evidence.asof_dates.length > 0
                  ? `${formatIsoDate(evidence.asof_dates[evidence.asof_dates.length - 1])} → ${formatIsoDate(evidence.asof_dates[0])}`
                  : "—"}
              </span>
            </span>
            <span>
              <span className="text-text-faint">Mean stock fwd return ({horizon}d): </span>
              <span className={cn("num", returnClass(evidence.overall.mean_return))}>
                {fmtPct(evidence.overall.mean_return)}
              </span>{" "}
              <span className="num text-text-faint">(n={evidence.overall.n})</span>
            </span>
            <span className="text-text-faint">
              Figures with <span className="text-warn">n &lt; {min} ⚠</span> are low-sample.
            </span>
          </div>

          <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
            <BucketPanel rows={evidence.by_bucket} min={min} horizon={horizon} />
            <ExcessPanel excess={evidence.excess} min={min} />
            <BreakdownPanel
              title="Forward return by setup type"
              rows={evidence.by_setup.map((r) => ({ label: r.setup, ...r }))}
              min={min}
              emptyLabel="No setup had a measurable forward return at this horizon."
            />
            <BreakdownPanel
              title="Forward return by market regime"
              rows={evidence.by_regime.map((r) => ({ label: r.regime, ...r }))}
              min={min}
              emptyLabel="No regime had a measurable forward return at this horizon."
            />
            <BreakdownPanel
              title="Forward return: VCP vs non-VCP"
              rows={evidence.by_vcp.map((r) => ({ label: r.vcp, ...r }))}
              min={min}
              emptyLabel="No VCP / non-VCP cohort had a measurable forward return at this horizon."
            />
            <BreakdownPanel
              title="Forward return: Pullback-to-rising-DMA vs not"
              rows={evidence.by_pullback_to_rising_dma.map((r) => ({
                label: r.pullback_to_rising_dma,
                ...r,
              }))}
              min={min}
              emptyLabel="No pullback-to-rising-DMA cohort had a measurable forward return at this horizon."
            />
            <BreakdownPanel
              title="Forward return: Flat-base breakout vs not"
              rows={evidence.by_flat_base_breakout.map((r) => ({ label: r.flat_base_breakout, ...r }))}
              min={min}
              emptyLabel="No flat-base-breakout cohort had a measurable forward return at this horizon."
            />
          </div>

          <ControlGroupPanel rows={evidence.control_group} min={min} horizon={horizon} />
        </>
      )}
    </section>
  );
}
