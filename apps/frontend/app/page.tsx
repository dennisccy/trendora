"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { AlertTriangle, Clock, ChevronDown } from "lucide-react";

import { useAsOf } from "@/components/asof-provider";
import { ComponentBreakdown } from "@/components/component-breakdown";
import { MarketPhaseCard } from "@/components/market-phase-card";
import { PhaseCrossViewCard } from "@/components/phase-cross-view-card";
import { PageHeading } from "@/components/page-heading";
import { ScoreBadge } from "@/components/score-badge";
import { TermInfo } from "@/components/ui/term-info";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { formatIsoDate } from "@/lib/dates";
import { usePersistedToggle } from "@/lib/use-persisted-toggle";
import { phaseColor } from "@/lib/phase";
import { regimeVariant } from "@/lib/regime-variant";
import { cn } from "@/lib/utils";
import {
  fetchDashboard,
  fetchMarketPhase,
  fetchSectors,
  fetchThemes,
  type DashboardResponse,
  type MarketPhaseComponent,
  type MarketPhaseResponse,
  type SectorsResponse,
  type ThemesResponse,
} from "@/lib/api";

type State =
  | { kind: "loading" }
  | {
      kind: "ok";
      dashboard: DashboardResponse;
      phase: MarketPhaseResponse | null;
      sectors: SectorsResponse | null;
      themes: ThemesResponse | null;
    }
  | { kind: "error" };

function fmtPct(value: number | null | undefined): string {
  return typeof value === "number" ? `${value.toFixed(2)}%` : "NA";
}

/** Phase label → Badge palette variant (same posture grouping as the Market-Phase card; presentation
 *  only). Reuses the shared `lib/phase` posture so the colour matches the cross-view bands. */
function phaseBadgeVariant(phase: string | null): "ok" | "warn" | "danger" {
  if (phase === "Bear" || phase === "Correction") return "danger";
  if (phase === "Pullback") return "warn";
  return "ok";
}

export default function DashboardPage() {
  const { asOf } = useAsOf();
  const [state, setState] = useState<State>({ kind: "loading" });

  useEffect(() => {
    const controller = new AbortController();
    const asof = asOf ?? undefined; // historical date or latest
    // Dashboard (regime + candidate counts) is critical; the market-phase summary + Top Sectors + Top
    // Themes read their own canonical endpoints and may fail independently. All fetch the SAME as-of date
    // so the snapshot view is coherent across the page.
    setState({ kind: "loading" });
    fetchDashboard(asof, controller.signal)
      .then(async (dashboard) => {
        let phase: MarketPhaseResponse | null = null;
        let sectors: SectorsResponse | null = null;
        let themes: ThemesResponse | null = null;
        try {
          phase = await fetchMarketPhase(asof, controller.signal);
        } catch {
          phase = null;
        }
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
        setState({ kind: "ok", dashboard, phase, sectors, themes });
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
        <DashboardBody
          dashboard={state.dashboard}
          phase={state.phase}
          sectors={state.sectors}
          themes={state.themes}
        />
      ) : null}
    </div>
  );
}

function DashboardBody({
  dashboard,
  phase,
  sectors,
  themes,
}: {
  dashboard: DashboardResponse;
  phase: MarketPhaseResponse | null;
  sectors: SectorsResponse | null;
  themes: ThemesResponse | null;
}) {
  const { regime } = dashboard;

  return (
    <div className="space-y-4">
      {/* J-98: the compact AT-A-GLANCE summary — Market Regime + Market Phase & Severity. Each re-displays
          the SAME served canonical values and keeps its named component breakdown reachable (no bare
          number). This is the first paint, above the cross-view chart. */}
      <div className="grid gap-4 md:grid-cols-2">
        <RegimeGlanceCard regime={regime} />
        <PhaseGlanceCard phase={phase} />
      </div>

      {/* J-97 / J-101a: the single two-pane synced regime × phase cross-view chart — the ONE market chart on
          the Dashboard. The former standalone "Major indexes & regime" card (J-44/J-49) was a DUPLICATE of
          this chart's pane 0 (same `/api/indexes?full=true` + `/api/regime-history?full=true` series) and is
          removed (J-101a) — nothing is lost, pane 0 already IS that chart. */}
      <PhaseCrossViewCard />

      {/* J-98: every supporting figure relocated into a collapsed, expandable "More detail" section —
          same data, same endpoints, only repositioned (nothing removed). */}
      <MoreDetailSection dashboard={dashboard} sectors={sectors} themes={themes} />
    </div>
  );
}

/** J-98 compact Market Regime figure: the stored label + 0–100 score, with the named component breakdown
 *  reachable via an inline disclosure (explainable — never a bare number). Re-displays `/api/dashboard`. */
function RegimeGlanceCard({ regime }: { regime: DashboardResponse["regime"] }) {
  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between space-y-0">
        <CardTitle className="flex items-center gap-1.5">
          Market Regime
          <TermInfo term="market regime" />
        </CardTitle>
        <Badge variant={regimeVariant(regime.label)}>{regime.label}</Badge>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="flex items-baseline gap-2">
          <span className="num text-4xl font-semibold text-text">{regime.score.toFixed(2)}</span>
          <span className="text-sm text-text-muted">/ 100</span>
        </div>
        <Disclosure summary="Why this regime — component breakdown">
          <ComponentBreakdown components={regime.components} className="max-w-xl pt-1" />
        </Disclosure>
        {/* J-04: a discoverable affordance from the current regime to the certified evidence that holds
            in it — the Dashboard regime → Evidence ledger flow. The regime number/label above is unchanged. */}
        <Link
          href="/evidence"
          className="inline-flex items-center gap-1 text-xs text-accent hover:underline focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-accent"
        >
          See evidence proven in this regime →
        </Link>
      </CardContent>
    </Card>
  );
}

/** J-98 compact Market Phase & Severity figure: the stored phase label + 0–100 severity + filtered P(bear),
 *  with the named severity-component breakdown reachable via an inline disclosure. Re-displays
 *  `/api/market-phase` (the SAME served value the detail card shows — single source). */
function PhaseGlanceCard({ phase }: { phase: MarketPhaseResponse | null }) {
  if (phase === null) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-1.5">Market Phase &amp; Severity</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-neg">Market-phase data unavailable — backend not reachable.</p>
        </CardContent>
      </Card>
    );
  }
  const available = phase.available;
  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between space-y-0">
        <CardTitle className="flex items-center gap-1.5">Market Phase &amp; Severity</CardTitle>
        {available && phase.phase ? (
          <span className="flex items-center gap-2">
            <Badge variant={phaseBadgeVariant(phase.phase)}>{phase.phase}</Badge>
            <span
              className="num rounded border border-border bg-surface-2 px-2 py-0.5 text-xs text-text-muted"
              title={`filtered P(bear) ${phase.p_bear?.toFixed(2) ?? "NA"}`}
            >
              P(bear) {phase.p_bear != null ? phase.p_bear.toFixed(2) : "NA"}
            </span>
          </span>
        ) : null}
      </CardHeader>
      <CardContent className="space-y-3">
        {available ? (
          <>
            <div className="flex items-baseline gap-2">
              <span
                className="num text-4xl font-semibold"
                style={{ color: phase.phase ? phaseColor(phase.phase) : undefined }}
              >
                {phase.severity != null ? phase.severity.toFixed(2) : "NA"}
              </span>
              <span className="text-sm text-text-muted">/ 100 severity</span>
            </div>
            <Disclosure summary="Why this severity — component breakdown">
              <SeverityBreakdown components={phase.components} />
            </Disclosure>
          </>
        ) : (
          <p className="text-sm text-text-muted">
            Not enough history to derive a market phase for this date — reported NA, never fabricated.
          </p>
        )}
      </CardContent>
    </Card>
  );
}

/** Human labels for the five named severity component keys (presentation only). Mirrors the Market-Phase
 *  card so the compact breakdown reads identically to the detail card (single source). */
const SEVERITY_COMPONENT_LABELS: Record<string, string> = {
  drawdown_depth: "Drawdown depth",
  time_underwater: "Time underwater",
  regime_risk: "Market regime (stored)",
  breadth_below_200dma: "Breadth below 200-DMA",
  vix_gate: "VIX stress gate",
};

/** The compact named severity breakdown for the at-a-glance phase figure (every component with its [0,1]
 *  value + contribution; NA honestly marked) — the SAME values the detail card shows (single source). */
function SeverityBreakdown({ components }: { components: MarketPhaseComponent[] }) {
  return (
    <div className="space-y-1.5 pt-1">
      <div className="grid grid-cols-[1fr_auto_auto] gap-x-4 text-xs uppercase tracking-wide text-text-faint">
        <span>Severity driver</span>
        <span className="text-right">Value</span>
        <span className="text-right">Contribution</span>
      </div>
      {components.map((component) => (
        <div key={component.name} className="grid grid-cols-[1fr_auto_auto] items-center gap-x-4 text-xs">
          <span className="text-text-muted">
            {SEVERITY_COMPONENT_LABELS[component.name] ?? component.name}
          </span>
          <span className={cn("num text-right", component.available ? "text-text-faint" : "text-warn")}>
            {component.available && component.value != null ? component.value.toFixed(2) : "NA"}
          </span>
          <span className="num text-right text-text">
            {component.contribution == null ? "—" : component.contribution.toFixed(2)}
          </span>
        </div>
      ))}
    </div>
  );
}

/** A lightweight inline disclosure (native `<details>`) — keeps a figure's named breakdown REACHABLE
 *  (one click) without crowding the at-a-glance summary. Pure presentation, no business logic. */
function Disclosure({ summary, children }: { summary: string; children: React.ReactNode }) {
  return (
    <details className="group rounded border border-border bg-surface-2/40">
      <summary
        className={cn(
          "flex cursor-pointer list-none items-center justify-between gap-2 px-2.5 py-1.5 text-xs text-text-muted",
          "transition-colors hover:text-text focus:outline-none focus-visible:ring-1 focus-visible:ring-accent",
        )}
      >
        {summary}
        <ChevronDown className="h-3.5 w-3.5 transition-transform group-open:rotate-180" aria-hidden />
      </summary>
      <div className="border-t border-border px-2.5 pb-2.5">{children}</div>
    </details>
  );
}

/** J-98: the collapsed "More detail" section — breadth metrics, candidate counts, Top Sectors, Top Themes,
 *  and the full Market Phase & Severity detail card. SAME data, SAME endpoints, only repositioned (nothing
 *  removed). Defaults to COLLAPSED at first paint (the spec: first paint shows only the summary + chart). */
function MoreDetailSection({
  dashboard,
  sectors,
  themes,
}: {
  dashboard: DashboardResponse;
  sectors: SectorsResponse | null;
  themes: ThemesResponse | null;
}) {
  const [open, setOpen] = usePersistedToggle("trendora.dashboard.moreDetail", false);
  const { breadth } = dashboard;
  const topSectors = sectors ? sectors.rows.slice(0, 5) : [];
  const topThemes = themes ? themes.rows.slice(0, 5) : [];

  return (
    <Card>
      <button
        type="button"
        onClick={() => setOpen(!open)}
        aria-expanded={open}
        className={cn(
          "flex w-full items-center justify-between gap-2 px-5 py-3 text-left",
          "transition-colors hover:bg-surface-2 focus:outline-none focus-visible:ring-1 focus-visible:ring-accent",
        )}
      >
        <span className="flex items-center gap-2">
          <CardTitle>More detail</CardTitle>
          <span className="text-xs text-text-muted">
            Breadth · candidate counts · Top Sectors · Top Themes · Market Phase detail
          </span>
        </span>
        <ChevronDown
          className={cn("h-4 w-4 text-text-muted transition-transform", open ? "rotate-180" : "")}
          aria-hidden
        />
      </button>
      {open ? (
        <CardContent className="space-y-4 border-t border-border pt-4">
          {/* breadth metrics (relocated, unchanged) */}
          <div className="grid gap-4 sm:grid-cols-3">
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

          {/* Top Sectors + candidate counts + Top Themes (relocated, unchanged) */}
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

          {/* J-87/J-88: the full Market Phase & Severity detail card (relocated, unchanged). */}
          <MarketPhaseCard />
        </CardContent>
      ) : null}
    </Card>
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
      <div className="grid gap-4 md:grid-cols-2">
        <Card className="h-48 animate-pulse bg-surface-2" />
        <Card className="h-48 animate-pulse bg-surface-2" />
      </div>
      <Card className="h-80 animate-pulse bg-surface-2" />
      <Card className="h-[28rem] animate-pulse bg-surface-2" />
    </div>
  );
}
