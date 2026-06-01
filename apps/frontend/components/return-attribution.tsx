import { type ReactNode } from "react";

import { fmtPct, Return, returnClass, SampleSize } from "@/components/forward-return";
import { Card } from "@/components/ui/card";
import type { Distribution, PerStockAttribution, PerStockRow, ReturnAttribution } from "@/lib/api";

/**
 * Return-attribution section (J-19) — the SINGLE shared rendering of the four read-only attribution
 * slices, consumed by BOTH System Health (aggregate) and Backtest (per-date) so the contract value has
 * one UI home. It RE-FORMATS values the backend already derived from the stored per-observation
 * forward returns; it never recomputes a return. NA (n=0) renders an em dash, and figures below
 * `min_sample` carry the shared `--warn` low-sample flag (palette tokens only, per the DESIGN SYSTEM).
 */

/** Unsigned magnitude as a percentage (hit rate, dispersion) — no +/- sign, neutral colour. NA -> em
 *  dash. (Hit rate and stdev are not directional returns, so they are not green/red colour-graded.) */
function fmtUnsignedPct(value: number | null): string {
  if (value === null || value === undefined) return "—";
  return `${(value * 100).toFixed(2)}%`;
}

function PanelTitle({ children, hint }: { children: ReactNode; hint?: string }) {
  return (
    <div className="border-b border-border px-4 py-3">
      <h3 className="text-sm font-semibold text-text">{children}</h3>
      {hint ? <p className="mt-0.5 text-xs text-text-faint">{hint}</p> : null}
    </div>
  );
}

function PerStockColumn({ title, rows, min }: { title: string; rows: PerStockRow[]; min: number }) {
  return (
    <div>
      <div className="border-b border-border px-4 py-2 text-xs font-medium uppercase tracking-wide text-text-faint">
        {title}
      </div>
      {rows.length === 0 ? (
        <p className="px-4 py-3 text-sm text-text-muted">—</p>
      ) : (
        <ul>
          {rows.map((row) => (
            <li
              key={row.ticker}
              className="flex items-center justify-between gap-3 border-b border-border px-4 py-2 last:border-b-0"
            >
              <span className="flex flex-col">
                <span className="num font-semibold text-text">{row.ticker}</span>
                {row.sector ? <span className="text-xs text-text-faint">{row.sector}</span> : null}
              </span>
              <Return value={row.mean_return} n={row.n} min={min} />
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

function PerStockPanel({ data, min }: { data: PerStockAttribution; min: number }) {
  const empty = data.contributors.length === 0 && data.detractors.length === 0;
  return (
    <Card className="p-0">
      <PanelTitle hint="Each named ticker's mean realized forward return over the observed snapshots (with n)">
        Top contributors &amp; detractors
      </PanelTitle>
      {empty ? (
        <p className="px-4 py-4 text-sm text-text-muted">
          No ticker had a measurable forward return at this horizon.
        </p>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2">
          <div className="border-b border-border sm:border-b-0 sm:border-r">
            <PerStockColumn title="Contributors" rows={data.contributors} min={min} />
          </div>
          <PerStockColumn title="Detractors" rows={data.detractors} min={min} />
        </div>
      )}
    </Card>
  );
}

function StatRow({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="flex items-center justify-between border-b border-border px-4 py-2 last:border-b-0">
      <span className="text-text-muted">{label}</span>
      <span className="num">{children}</span>
    </div>
  );
}

function DistributionPanel({ d, min }: { d: Distribution; min: number }) {
  return (
    <Card className="p-0">
      <PanelTitle hint="The shape of the same observed returns — not just the mean">
        Distribution &amp; hit-rate
      </PanelTitle>
      <div className="text-sm">
        <StatRow label="Mean">
          <span className={returnClass(d.mean_return)}>{fmtPct(d.mean_return)}</span>
        </StatRow>
        <StatRow label="Median">
          <span className={returnClass(d.median)}>{fmtPct(d.median)}</span>
        </StatRow>
        <StatRow label="% positive (hit rate)">
          <span className="text-text">{fmtUnsignedPct(d.pct_positive)}</span>
        </StatRow>
        <StatRow label="Dispersion (σ)">
          <span className="text-text">{fmtUnsignedPct(d.dispersion)}</span>
        </StatRow>
        <StatRow label="Sample size">
          <SampleSize n={d.n} min={min} />
        </StatRow>
      </div>
    </Card>
  );
}

function GroupPanel({
  title,
  hint,
  rows,
  min,
  emptyLabel,
}: {
  title: string;
  hint?: string;
  rows: { label: string; mean_return: number | null; n: number }[];
  min: number;
  emptyLabel: string;
}) {
  return (
    <Card className="p-0">
      <PanelTitle hint={hint}>{title}</PanelTitle>
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

/** The four-panel attribution section. `horizon` only labels the copy; `action` is an optional control
 *  rendered in the header (Backtest passes its client-side horizon-view selector here — System Health
 *  rides its own page-level horizon selector and omits it). */
export function ReturnAttributionSection({
  attribution,
  min,
  horizon,
  action,
}: {
  attribution: ReturnAttribution;
  min: number;
  horizon: number;
  action?: ReactNode;
}) {
  return (
    <section className="space-y-4" data-testid="return-attribution">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h2 className="text-sm font-semibold text-text">Return attribution</h2>
          <p className="mt-0.5 max-w-2xl text-xs text-text-faint">
            Open the {horizon}-day forward return: which tickers drove or dragged it, which sectors and
            rank bands carried it, and its distribution shape. Read-only — derived from the stored
            per-observation returns, never recomputed.
          </p>
        </div>
        {action}
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <PerStockPanel data={attribution.per_stock} min={min} />
        <DistributionPanel d={attribution.distribution} min={min} />
        <GroupPanel
          title="Forward return by sector"
          hint="Mean realized forward return per stored sector"
          rows={attribution.by_sector.map((r) => ({ label: r.sector, mean_return: r.mean_return, n: r.n }))}
          min={min}
          emptyLabel="No sector had a measurable forward return at this horizon."
        />
        <GroupPanel
          title="Forward return by rank band"
          hint="Mean realized forward return per rank band"
          rows={attribution.by_rank_band.map((r) => ({
            label: r.rank_band,
            mean_return: r.mean_return,
            n: r.n,
          }))}
          min={min}
          emptyLabel="No rank band had a measurable forward return at this horizon."
        />
      </div>
    </section>
  );
}
