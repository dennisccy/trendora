"use client";

import { useEffect, useState } from "react";
import { AlertTriangle, Clock } from "lucide-react";

import { useAsOf } from "@/components/asof-provider";
import { ComponentBreakdown } from "@/components/component-breakdown";
import { MajorIndexesCard } from "@/components/major-indexes-card";
import { PageHeading } from "@/components/page-heading";
import { ScoreBadge } from "@/components/score-badge";
import { TermInfo } from "@/components/ui/term-info";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { formatIsoDate } from "@/lib/dates";
import { regimeVariant } from "@/lib/regime-variant";
import { cn } from "@/lib/utils";
import {
  fetchDashboard,
  fetchSectors,
  fetchThemes,
  type DashboardResponse,
  type SectorsResponse,
  type ThemesResponse,
} from "@/lib/api";

type State =
  | { kind: "loading" }
  | {
      kind: "ok";
      dashboard: DashboardResponse;
      sectors: SectorsResponse | null;
      themes: ThemesResponse | null;
    }
  | { kind: "error" };

function fmtPct(value: number | null | undefined): string {
  return typeof value === "number" ? `${value.toFixed(2)}%` : "NA";
}

export default function DashboardPage() {
  const { asOf } = useAsOf();
  const [state, setState] = useState<State>({ kind: "loading" });

  useEffect(() => {
    const controller = new AbortController();
    const asof = asOf ?? undefined; // historical date or latest
    // Dashboard (regime + candidate counts) is critical; Top Sectors and Top Themes read their
    // own canonical endpoints (/api/sectors, /api/themes) and may fail independently. All three
    // fetch the SAME as-of date so the snapshot view is coherent across the page.
    setState({ kind: "loading" });
    fetchDashboard(asof, controller.signal)
      .then(async (dashboard) => {
        let sectors: SectorsResponse | null = null;
        let themes: ThemesResponse | null = null;
        try {
          sectors = await fetchSectors(asof, controller.signal);
        } catch {
          sectors = null;
        }
        try {
          themes = await fetchThemes(asof, controller.signal);
        } catch {
          themes = null;
        }
        setState({ kind: "ok", dashboard, sectors, themes });
      })
      .catch(() => {
        if (!controller.signal.aborted) setState({ kind: "error" });
      });
    return () => controller.abort();
  }, [asOf]);

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-end justify-between gap-2">
        <PageHeading title="Dashboard" subtitle="The daily snapshot at a glance" />
        {state.kind === "ok" ? (
          <Badge variant="default" className="num gap-1.5">
            <Clock className="h-3.5 w-3.5" aria-hidden />
            Data as-of {formatIsoDate(state.dashboard.asof_date)}
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

      {state.kind === "ok" ? (
        <DashboardBody dashboard={state.dashboard} sectors={state.sectors} themes={state.themes} />
      ) : null}
    </div>
  );
}

function DashboardBody({
  dashboard,
  sectors,
  themes,
}: {
  dashboard: DashboardResponse;
  sectors: SectorsResponse | null;
  themes: ThemesResponse | null;
}) {
  const { regime, breadth } = dashboard;
  const topSectors = sectors ? sectors.rows.slice(0, 5) : [];
  const topThemes = themes ? themes.rows.slice(0, 5) : [];

  return (
    <div className="space-y-4">
      {/* Regime + breadth */}
      <div className="grid gap-4 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader className="flex-row items-center justify-between space-y-0">
            <CardTitle className="flex items-center gap-1.5">
              Market Regime
              <TermInfo term="market regime" />
            </CardTitle>
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
            term="breadth > 50-DMA"
            value={fmtPct(breadth.above_50dma_pct)}
            caption={breadth.label}
          />
          <MetricCard
            title="Breadth · above 200-DMA"
            term="breadth > 200-DMA"
            value={fmtPct(breadth.above_200dma_pct)}
            caption={breadth.label}
          />
          <MetricCard
            title="Net new highs"
            term="net new-high/low"
            value={`${breadth.new_high_low.net_pct.toFixed(2)}%`}
            caption={`${breadth.new_high_low.new_highs} hi / ${breadth.new_high_low.new_lows} lo · ${breadth.label}`}
          />
        </div>
      </div>

      {/* J-44: Major indexes & regime — normalized % index lines over stored-regime bands (default ON). */}
      <MajorIndexesCard />

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

        <CandidateCountsCard counts={dashboard.candidate_counts} />

        <Card>
          <CardHeader>
            <CardTitle>Top Themes</CardTitle>
          </CardHeader>
          <CardContent>
            {themes === null ? (
              <p className="text-sm text-neg">Theme data unavailable — backend not reachable.</p>
            ) : topThemes.length === 0 ? (
              <p className="text-sm text-text-muted">No ranked themes for this date.</p>
            ) : (
              <ul className="space-y-2">
                {topThemes.map((row) => (
                  <li key={row.slug} className="flex items-center justify-between gap-2">
                    <span className="flex items-center gap-2">
                      <span className="num text-text-faint">{row.rank}</span>
                      <span className="font-semibold text-text">{row.name}</span>
                      <span className="text-xs text-text-muted">{row.trend_label}</span>
                    </span>
                    <ScoreBadge bucket={row.bucket} score={row.score} />
                  </li>
                ))}
              </ul>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

/** The three candidate counts (# Actionable / Breakout-watch / Pullback-watch) — counted once on
 *  the backend from the canonical setup statuses, only re-formatted here (never recomputed). */
function CandidateCountsCard({ counts }: { counts: Record<string, number> }) {
  const rows: { label: string; key: string; accent: boolean }[] = [
    { label: "Actionable", key: "Actionable", accent: true },
    { label: "Breakout-watch", key: "Breakout-watch", accent: false },
    { label: "Pullback-watch", key: "Pullback-watch", accent: false },
  ];
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-1.5">
          Candidate Counts
          <TermInfo term="setup status" />
        </CardTitle>
      </CardHeader>
      <CardContent>
        <ul className="space-y-1.5">
          {rows.map(({ label, key, accent }) => (
            <li key={key} className="flex items-center justify-between text-sm">
              <span className="flex items-center gap-1.5 text-text-muted">
                {label}
                <TermInfo term={label} />
              </span>
              <span className={cn("num text-lg font-semibold", accent ? "text-pos" : "text-text")}>
                {counts[key] ?? 0}
              </span>
            </li>
          ))}
        </ul>
        <p className="mt-2 text-xs text-text-faint">
          Counts of the canonical per-stock setup statuses (zero Actionable in a Risk-off regime).
        </p>
      </CardContent>
    </Card>
  );
}

function MetricCard({
  title,
  value,
  caption,
  term,
}: {
  title: string;
  value: string;
  caption: string;
  term?: string;
}) {
  return (
    <Card>
      <CardContent className="space-y-1 p-5">
        <p className="flex items-center gap-1.5 text-xs uppercase tracking-wide text-text-faint">
          {title}
          {term ? <TermInfo term={term} /> : null}
        </p>
        <p className="num text-2xl font-semibold text-text">{value}</p>
        <Badge variant="warn" className="text-xs">{caption}</Badge>
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
