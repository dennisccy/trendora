"use client";

import { use, useEffect, useState } from "react";
import Link from "next/link";
import { AlertTriangle, ArrowLeft, History, Lock } from "lucide-react";

import { ComponentBreakdown } from "@/components/component-breakdown";
import { EmptyState } from "@/components/empty-state";
import { PageHeading } from "@/components/page-heading";
import { ScoreBadge } from "@/components/score-badge";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { formatIsoDate, formatIsoDateTime } from "@/lib/dates";
import { cn } from "@/lib/utils";
import { fetchRun, type RunDetail, type StockRow } from "@/lib/api";

type State =
  | { kind: "loading" }
  | { kind: "ok"; data: RunDetail }
  | { kind: "notfound" }
  | { kind: "error" };

function regimeVariant(label: string): "ok" | "warn" | "danger" | "default" {
  if (label === "Strong risk-on" || label === "Risk-on") return "ok";
  if (label === "Defensive" || label === "Risk-off") return "danger";
  return "warn"; // Narrow leadership · Choppy
}

// Setup-status badge colouring — mirrors the live Stock Leaderboard so a status reads identically
// on a stored run and on /stocks.
function setupVariant(status: string): "ok" | "warn" | "danger" | "accent" | "default" {
  switch (status) {
    case "Actionable":
      return "ok";
    case "Breakout-watch":
    case "Pullback-watch":
      return "accent";
    case "Extended":
    case "Risk-off-watchlist":
      return "warn";
    case "Avoid":
      return "danger";
    default:
      return "default";
  }
}

function fmtPct(value: number | null | undefined): string {
  return typeof value === "number" ? `${value.toFixed(2)}%` : "NA";
}

export default function RunDetailPage({ params }: { params: Promise<{ runId: string }> }) {
  const { runId } = use(params);
  const [state, setState] = useState<State>({ kind: "loading" });

  useEffect(() => {
    const controller = new AbortController();
    fetchRun(runId, controller.signal)
      .then((data) => setState({ kind: "ok", data }))
      .catch((err: unknown) => {
        if (controller.signal.aborted) return;
        const is404 = err instanceof Error && err.message.includes("HTTP 404");
        setState({ kind: is404 ? "notfound" : "error" });
      });
    return () => controller.abort();
  }, [runId]);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between gap-2">
        <PageHeading
          title="Scanner Run"
          subtitle="The exact, immutable as-of view the scanner produced on this date"
        />
        <Link
          href="/scanner-runs"
          className="inline-flex items-center gap-1.5 rounded-md border border-border px-3 py-1.5 text-xs text-text-muted transition-colors hover:bg-surface-2 hover:text-text focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-accent"
        >
          <ArrowLeft className="h-3.5 w-3.5" aria-hidden />
          All runs
        </Link>
      </div>

      {state.kind === "loading" ? <DetailSkeleton /> : null}

      {state.kind === "error" ? (
        <Card className="flex items-center gap-3 border-neg bg-surface p-5 text-sm text-neg">
          <AlertTriangle className="h-5 w-5 shrink-0" aria-hidden />
          <div>
            <p className="font-medium">Backend unavailable</p>
            <p className="text-text-muted">
              This run could not load from the API. Nothing is fabricated — confirm the backend is
              running and retry.
            </p>
          </div>
        </Card>
      ) : null}

      {state.kind === "notfound" ? (
        <EmptyState
          icon={History}
          title="Run not found"
          description={`No scanner run exists with id ${runId}. It may never have been persisted — no run is fabricated to fill the gap.`}
        />
      ) : null}

      {state.kind === "ok" ? <RunBody data={state.data} /> : null}
    </div>
  );
}

function RunBody({ data }: { data: RunDetail }) {
  const { regime, breadth, rows } = data;
  return (
    <div className="space-y-4">
      {/* Immutable / as-of header strip — unmistakably a historical, frozen snapshot */}
      <Card className="flex flex-wrap items-center justify-between gap-3 border-border-strong bg-surface-2 p-4">
        <div className="flex items-center gap-2.5">
          <Lock className="h-4 w-4 text-warn" aria-hidden />
          <div>
            <p className="text-sm font-semibold text-text">
              Immutable snapshot — as of <span className="num">{formatIsoDate(data.asof_date)}</span>
            </p>
            <p className="text-xs text-text-muted">
              Stored exactly as scanned; never recomputed for today. Scanned {formatIsoDateTime(data.created_at)} ·
              provider {data.provider} · benchmark {data.benchmark}
            </p>
          </div>
        </div>
        <Badge variant={regimeVariant(regime.label)}>{regime.label}</Badge>
      </Card>

      {/* Regime panel + breadth + candidate counts */}
      <div className="grid gap-4 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader className="flex-row items-center justify-between space-y-0">
            <CardTitle>Market Regime · as of {formatIsoDate(data.asof_date)}</CardTitle>
            <Badge variant={regimeVariant(regime.label)}>{regime.label}</Badge>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-baseline gap-2">
              <span className="num text-4xl font-semibold text-text">{regime.score.toFixed(2)}</span>
              <span className="text-sm text-text-muted">/ 100</span>
            </div>
            <ComponentBreakdown components={regime.components} className="max-w-xl" />
          </CardContent>
        </Card>

        <div className="grid gap-4">
          <MetricCard
            title="Breadth · above 50-DMA"
            value={fmtPct(breadth.above_50dma_pct)}
            caption={breadth.label}
          />
          <MetricCard
            title="Breadth · above 200-DMA"
            value={fmtPct(breadth.above_200dma_pct)}
            caption={breadth.label}
          />
          <MetricCard
            title="Net new highs"
            value={`${breadth.new_high_low.net_pct.toFixed(2)}%`}
            caption={`${breadth.new_high_low.new_highs} hi / ${breadth.new_high_low.new_lows} lo · ${breadth.label}`}
          />
        </div>
      </div>

      <CandidateCountsRow counts={data.candidate_counts} />

      {/* Ranked stored stock table — the canonical StockRow shape, reusing ScoreBadge */}
      {rows.length === 0 ? (
        <EmptyState
          icon={History}
          title="No stored stock rows"
          description="This run persisted no per-stock results."
        />
      ) : (
        <Card className="overflow-x-auto p-0">
          <table className="w-full border-collapse text-sm">
            <thead>
              <tr className="border-b border-border text-left text-xs uppercase tracking-wide text-text-faint">
                <th className="px-3 py-2 font-medium">#</th>
                <th className="px-3 py-2 font-medium">Ticker</th>
                <th className="px-3 py-2 font-medium">Sector</th>
                <th className="px-3 py-2 font-medium">Leadership</th>
                <th className="px-3 py-2 font-medium">Entry Quality</th>
                <th className="px-3 py-2 font-medium">Risk</th>
                <th className="px-3 py-2 font-medium">Setup</th>
                <th className="px-3 py-2 font-medium">Reason</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => (
                <StoredStockRow key={row.ticker} row={row} />
              ))}
            </tbody>
          </table>
        </Card>
      )}
    </div>
  );
}

function StoredStockRow({ row }: { row: StockRow }) {
  return (
    <tr className="border-b border-border transition-colors hover:bg-surface-2">
      <td className="num px-3 py-2 text-text-faint">{row.rank}</td>
      <td className="num px-3 py-2 font-semibold text-text">{row.ticker}</td>
      <td className="px-3 py-2 text-xs text-text-muted">{row.sector}</td>
      <td className="px-3 py-2">
        <ScoreBadge bucket={row.leadership.bucket} score={row.leadership.score} />
      </td>
      <td className="px-3 py-2">
        <ScoreBadge bucket={row.entry_quality.bucket} score={row.entry_quality.score} />
      </td>
      <td className="px-3 py-2">
        <ScoreBadge bucket={row.risk.bucket} score={row.risk.score} invert />
      </td>
      <td className="px-3 py-2">
        <Badge variant={setupVariant(row.setup.status)}>{row.setup.status}</Badge>
      </td>
      <td className="max-w-xs px-3 py-2 text-xs text-text-muted">
        <span className="line-clamp-2" title={row.setup.reason}>
          {row.setup.reason}
        </span>
      </td>
    </tr>
  );
}

/** The stored candidate counts (counts of the canonical setup statuses for this run). */
function CandidateCountsRow({ counts }: { counts: Record<string, number> }) {
  const items: { label: string; key: string; accent: boolean }[] = [
    { label: "Actionable", key: "Actionable", accent: true },
    { label: "Breakout-watch", key: "Breakout-watch", accent: false },
    { label: "Pullback-watch", key: "Pullback-watch", accent: false },
    { label: "Risk-off-watchlist", key: "Risk-off-watchlist", accent: false },
  ];
  return (
    <Card>
      <CardHeader>
        <CardTitle>Candidate Counts</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          {items.map(({ label, key, accent }) => (
            <div key={key} className="flex flex-col gap-0.5">
              <span className="text-xs text-text-muted">{label}</span>
              <span className={cn("num text-2xl font-semibold", accent ? "text-pos" : "text-text")}>
                {counts[key] ?? 0}
              </span>
            </div>
          ))}
        </div>
        <p className="mt-2 text-xs text-text-faint">
          Stored counts of the canonical per-stock setup statuses (zero Actionable in a Risk-off
          regime).
        </p>
      </CardContent>
    </Card>
  );
}

function MetricCard({ title, value, caption }: { title: string; value: string; caption: string }) {
  return (
    <Card>
      <CardContent className="space-y-1 p-5">
        <p className="text-xs uppercase tracking-wide text-text-faint">{title}</p>
        <p className="num text-2xl font-semibold text-text">{value}</p>
        <Badge variant="warn" className="text-xs">
          {caption}
        </Badge>
      </CardContent>
    </Card>
  );
}

function DetailSkeleton() {
  return (
    <div className="space-y-4">
      <Card className="h-20 animate-pulse bg-surface-2" />
      <div className="grid gap-4 lg:grid-cols-3">
        <Card className="h-56 animate-pulse bg-surface-2 lg:col-span-2" />
        <Card className="h-56 animate-pulse bg-surface-2" />
      </div>
      <Card className="h-64 animate-pulse bg-surface-2" />
    </div>
  );
}
