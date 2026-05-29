"use client";

import { useEffect, useState } from "react";
import { AlertTriangle, Clock } from "lucide-react";

import { ComponentBreakdown } from "@/components/component-breakdown";
import { PageHeading } from "@/components/page-heading";
import { ScoreBadge } from "@/components/score-badge";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import {
  fetchDashboard,
  fetchSectors,
  type DashboardResponse,
  type SectorsResponse,
} from "@/lib/api";

type State =
  | { kind: "loading" }
  | { kind: "ok"; dashboard: DashboardResponse; sectors: SectorsResponse | null }
  | { kind: "error" };

function regimeVariant(label: string): "ok" | "warn" | "danger" | "default" {
  if (label === "Strong risk-on" || label === "Risk-on") return "ok";
  if (label === "Defensive" || label === "Risk-off") return "danger";
  return "warn"; // Narrow leadership · Choppy
}

function fmtPct(value: number | null | undefined): string {
  return typeof value === "number" ? `${value.toFixed(2)}%` : "NA";
}

export default function DashboardPage() {
  const [state, setState] = useState<State>({ kind: "loading" });

  useEffect(() => {
    const controller = new AbortController();
    // Dashboard (regime) is critical; sectors feeds Top Sectors and may fail independently.
    fetchDashboard(controller.signal)
      .then(async (dashboard) => {
        let sectors: SectorsResponse | null = null;
        try {
          sectors = await fetchSectors(controller.signal);
        } catch {
          sectors = null;
        }
        setState({ kind: "ok", dashboard, sectors });
      })
      .catch(() => {
        if (!controller.signal.aborted) setState({ kind: "error" });
      });
    return () => controller.abort();
  }, []);

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-end justify-between gap-2">
        <PageHeading title="Dashboard" subtitle="The daily snapshot at a glance" />
        {state.kind === "ok" ? (
          <Badge variant="default" className="num gap-1.5">
            <Clock className="h-3.5 w-3.5" aria-hidden />
            Data as-of {state.dashboard.asof_date}
          </Badge>
        ) : null}
      </div>

      {state.kind === "loading" ? <DashboardSkeleton /> : null}

      {state.kind === "error" ? (
        <Card className="flex items-center gap-3 border-neg bg-surface p-5 text-sm text-neg">
          <AlertTriangle className="h-5 w-5 shrink-0" aria-hidden />
          <div>
            <p className="font-medium">Backend unavailable</p>
            <p className="text-text-muted">
              The dashboard could not load the market regime from the API. Nothing is fabricated —
              confirm the backend is running and reload.
            </p>
          </div>
        </Card>
      ) : null}

      {state.kind === "ok" ? <DashboardBody dashboard={state.dashboard} sectors={state.sectors} /> : null}
    </div>
  );
}

function DashboardBody({
  dashboard,
  sectors,
}: {
  dashboard: DashboardResponse;
  sectors: SectorsResponse | null;
}) {
  const { regime, breadth } = dashboard;
  const topSectors = sectors ? sectors.rows.slice(0, 5) : [];

  return (
    <div className="space-y-4">
      {/* Regime + breadth */}
      <div className="grid gap-4 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader className="flex-row items-center justify-between space-y-0">
            <CardTitle>Market Regime</CardTitle>
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

      {/* Top sectors + pending placeholders */}
      <div className="grid gap-4 lg:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle>Top Sectors</CardTitle>
          </CardHeader>
          <CardContent>
            {sectors === null ? (
              <p className="text-sm text-neg">Sector data unavailable — backend not reachable.</p>
            ) : topSectors.length === 0 ? (
              <p className="text-sm text-text-muted">No ranked sectors for this date.</p>
            ) : (
              <ul className="space-y-2">
                {topSectors.map((row) => (
                  <li key={row.ticker} className="flex items-center justify-between gap-2">
                    <span className="flex items-center gap-2">
                      <span className="num text-text-faint">{row.rank}</span>
                      <span className="num font-semibold text-text">{row.ticker}</span>
                      <span className="text-xs text-text-muted">{row.trend_label}</span>
                    </span>
                    <ScoreBadge bucket={row.bucket} score={row.score} />
                  </li>
                ))}
              </ul>
            )}
          </CardContent>
        </Card>

        <PendingCard
          title="Candidate Counts"
          rows={["Actionable", "Breakout-watch", "Pullback-watch"]}
        />
        <PendingCard title="Top Themes" rows={["Theme leadership"]} />
      </div>
    </div>
  );
}

function MetricCard({ title, value, caption }: { title: string; value: string; caption: string }) {
  return (
    <Card>
      <CardContent className="space-y-1 p-5">
        <p className="text-xs uppercase tracking-wide text-text-faint">{title}</p>
        <p className="num text-2xl font-semibold text-text">{value}</p>
        <Badge variant="warn" className="text-xs">{caption}</Badge>
      </CardContent>
    </Card>
  );
}

/** Honest placeholder for capabilities that land in a later iteration — never a fabricated 0. */
function PendingCard({ title, rows }: { title: string; rows: string[] }) {
  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between space-y-0">
        <CardTitle>{title}</CardTitle>
        <Badge variant="warn">pending</Badge>
      </CardHeader>
      <CardContent className="space-y-2">
        <ul className="space-y-1.5">
          {rows.map((label) => (
            <li key={label} className="flex items-center justify-between text-sm">
              <span className="text-text-muted">{label}</span>
              <span className="num text-text-faint">—</span>
            </li>
          ))}
        </ul>
        <p className="text-xs text-text-faint">Arriving in a later iteration (per-stock &amp; theme scoring).</p>
      </CardContent>
    </Card>
  );
}

function DashboardSkeleton() {
  return (
    <div className="space-y-4">
      <div className="grid gap-4 lg:grid-cols-3">
        <Card className="h-56 animate-pulse bg-surface-2 lg:col-span-2" />
        <Card className="h-56 animate-pulse bg-surface-2" />
      </div>
      <div className="grid gap-4 lg:grid-cols-3">
        {Array.from({ length: 3 }).map((_, i) => (
          <Card key={i} className="h-40 animate-pulse bg-surface-2" />
        ))}
      </div>
    </div>
  );
}
