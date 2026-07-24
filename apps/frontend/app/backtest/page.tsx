"use client";

import { useEffect, useState } from "react";
import { AlertTriangle, Clock, FlaskConical, History, Loader2, ShieldAlert } from "lucide-react";

import { useAsOf } from "@/components/asof-provider";
import { EmptyState } from "@/components/empty-state";
import { EvidenceAggregateSection } from "@/components/evidence-panels";
import { Return } from "@/components/forward-return";
import { PageHeading } from "@/components/page-heading";
import { useReadiness } from "@/components/readiness-provider";
import { ReturnAttributionSection } from "@/components/return-attribution";
import { ScoreBadge } from "@/components/score-badge";
import { shouldShowWarming, WarmingState } from "@/components/warming-state";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { TermInfo } from "@/components/ui/term-info";
import { formatIsoDate, formatIsoDateTime } from "@/lib/dates";
import { cn } from "@/lib/utils";
import {
  fetchBacktest,
  fetchDashboard,
  fetchSectors,
  fetchStocks,
  fetchThemes,
  type BacktestResponse,
  type ControlGroupRow,
  type DashboardResponse,
  type LeadershipReturns,
  type SectorsResponse,
  type StocksResponse,
  type ThemesResponse,
} from "@/lib/api";

// How many ranked rows / leaderboard slices the as-of scan summary shows (display-only; the canonical
// ranking + scores come from the backend, sliced here — never recomputed).
const TOP_N_PANEL = 5;
const COHORT_ROWS = 10;

type ScanSummary = {
  dashboard: DashboardResponse | null;
  sectors: SectorsResponse | null;
  themes: ThemesResponse | null;
  stocks: StocksResponse | null;
};

type State =
  | { kind: "loading" }
  | ({ kind: "ok"; backtest: BacktestResponse } & ScanSummary)
  | { kind: "error" };

function regimeVariant(label: string): "ok" | "warn" | "danger" | "default" {
  if (label === "Strong risk-on" || label === "Risk-on") return "ok";
  if (label === "Defensive" || label === "Risk-off") return "danger";
  return "warn"; // Narrow leadership · Choppy
}

export default function BacktestPage() {
  // The page reads the SINGLE global as-of date (the top-bar switcher) — it holds NO date state of its
  // own. The switcher's resolved date drives every fetch below; navigating between pages preserves it.
  const { asOf, isHistorical: globalIsHistorical } = useAsOf();
  // The SINGLE shared readiness value (J-40) — while the background historical warm-up is still loading
  // (`initializing`), this page shows the "warming up (n/m)" state instead of an empty/partial aggregate.
  // It reads the same value the badge reads; it adds NO date state (J-18 preserved).
  const { state: readiness } = useReadiness();
  const [state, setState] = useState<State>({ kind: "loading" });

  // The global as-of date drives every fetch. The scorecard (fetchBacktest) is the page's reason to
  // exist; the scan-summary endpoints are best-effort (each may fail independently without blanking
  // the page). The effect re-runs whenever the global switcher changes the resolved date.
  useEffect(() => {
    const controller = new AbortController();
    const asof = asOf ?? undefined; // historical date or latest
    setState({ kind: "loading" });
    fetchBacktest(asof, controller.signal)
      .then(async (backtest) => {
        const [dashboard, sectors, themes, stocks] = await Promise.all([
          fetchDashboard(asof, controller.signal).catch(() => null),
          fetchSectors(asof, controller.signal).catch(() => null),
          fetchThemes(asof, controller.signal).catch(() => null),
          fetchStocks(asof, controller.signal).catch(() => null),
        ]);
        setState({ kind: "ok", backtest, dashboard, sectors, themes, stocks });
      })
      .catch(() => {
        if (!controller.signal.aborted) setState({ kind: "error" });
      });
    return () => controller.abort();
    // `readiness` is a dep so the page AUTO-POPULATES the moment the background warm-up finishes (the
    // flip to `ready` re-runs the fetch). The global as-of switcher still owns the date (J-18).
  }, [asOf, readiness]);

  // Read-only "viewing as-of" DISPLAY indicator (not a control): prefer the backtest response's
  // resolved date/flag; before it loads, fall back to the global switcher's own state.
  const resolvedDate = state.kind === "ok" ? state.backtest.asof_date : asOf;
  const isHistorical = state.kind === "ok" ? !state.backtest.is_latest : globalIsHistorical;

  return (
    <div className="space-y-4">
      <PageHeading
        title="Backtest"
        subtitle="Time-machine to a past scan date and read its forward-test scorecard — how that date's ranked cohort actually performed over the next 1/5/10/20/60 trading days vs SPY/QQQ/sector and a random same-sector control."
      />

      <div className="flex flex-wrap items-center gap-2">
        {resolvedDate ? (
          isHistorical ? (
            <Badge variant="warn" className="num gap-1.5" data-testid="backtest-asof">
              <History className="h-3.5 w-3.5" aria-hidden />
              Viewing as-of {formatIsoDate(resolvedDate)} (historical)
            </Badge>
          ) : (
            <Badge variant="default" className="num gap-1.5" data-testid="backtest-asof">
              <Clock className="h-3.5 w-3.5" aria-hidden />
              Viewing as-of {formatIsoDate(resolvedDate)} (latest)
            </Badge>
          )
        ) : null}
      </div>

      <SurvivorshipBanner
        text={
          state.kind === "ok"
            ? state.backtest.survivorship_bias
            : "Walk-forward evidence carries survivorship bias (current-membership universe) — results may be overstated."
        }
      />

      {/* While the background historical warm-up is still loading, show the honest "warming up (n/m)"
          state — never an error, never an empty/partial aggregate presented as complete (J-40). It
          auto-populates when warm-up finishes (the readiness flip re-runs the fetch above). */}
      {shouldShowWarming(readiness) ? (
        <WarmingState what="The forward-tested evidence (by bucket / setup / regime, control groups, attribution)" />
      ) : (
        <>
          {state.kind === "loading" ? <BacktestSkeleton /> : null}

          {state.kind === "error" ? (
            <Card className="flex items-center gap-3 border-neg bg-surface p-5 text-sm text-neg">
              <AlertTriangle className="h-5 w-5 shrink-0" aria-hidden />
              <div>
                <p className="font-medium">Backend unavailable</p>
                <p className="text-text-muted">
                  The backtest scorecard could not load from the API. No figures are shown rather than
                  fabricated values. Confirm the backend is running and retry.
                </p>
              </div>
            </Card>
          ) : null}

          {state.kind === "ok" ? (
            <BacktestResults
              backtest={state.backtest}
              dashboard={state.dashboard}
              sectors={state.sectors}
              themes={state.themes}
              stocks={state.stocks}
            />
          ) : null}
        </>
      )}
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

// --- The full backtest results: as-of scan summary → forward-test scorecard → Return Attribution →
// the three leadership lists. `viewHorizon` is LIFTED here so the ONE horizon view-selector (rendered
// in the Return Attribution header) re-points BOTH the attribution AND the three leadership-return
// columns below. It is a VIEW selector only — no refetch, no fetch param, no date state (the global
// as-of switcher still owns the date → J-18 preserved).
function BacktestResults({
  backtest,
  dashboard,
  sectors,
  themes,
  stocks,
}: { backtest: BacktestResponse } & ScanSummary) {
  const rows = backtest.scorecard.by_horizon;
  // Default to the first horizon with an observed window (so attribution + return columns populate on
  // load); fall back to the last horizon when nothing has elapsed yet (an honest all-NA view).
  const [viewHorizon, setViewHorizon] = useState<number>(() => {
    const observed = rows.find((row) => row.attribution.distribution.n > 0);
    return (observed ?? rows[rows.length - 1])?.horizon ?? backtest.horizons[0];
  });
  const selected = rows.find((row) => row.horizon === viewHorizon) ?? rows[0];
  // The as-of-scoped evidence aggregate for the SAME selected horizon — picked from the single payload's
  // `evidence_by_horizon` (no refetch on horizon change; the global as-of switcher still owns the date).
  const evidence = backtest.evidence_by_horizon[selected?.horizon ?? viewHorizon];

  return (
    <div className="space-y-4">
      <AsOfScanSummary dashboard={dashboard} />
      <ScorecardSection data={backtest} />
      {selected ? (
        <ReturnAttributionSection
          attribution={selected.attribution}
          min={backtest.min_sample}
          horizon={selected.horizon}
          action={
            <HorizonViewSelector
              horizons={backtest.horizons}
              value={selected.horizon}
              onChange={setViewHorizon}
            />
          }
        />
      ) : null}
      <LeadershipListsSection
        sectors={sectors}
        themes={themes}
        stocks={stocks}
        leadership={selected?.leadership_returns}
        horizon={selected?.horizon ?? viewHorizon}
        min={backtest.min_sample}
      />
      {/* The expanding-window forward-tested evidence aggregate (J-09/J-10/J-16/J-28), relocated off the
          retired System Health. Placed at the VERY BOTTOM (after the leadership lists) so the J-21 order
          — scorecard → Return Attribution → leadership lists — is preserved; it is the single home now.
          ops-hardening iter-16 (J-08): the evidence panel never blocks on a cold recompute — the served
          `evidence_status` (computed server-side, never derived here) honestly discloses whether this is
          the current version (`ready`, unchanged from before), a labeled last-good prior version while a
          newer one warms (`refreshing`), or a never-warmed store (`not_yet_computed`). */}
      {backtest.evidence_status === "not_yet_computed" ? (
        <EmptyState
          icon={FlaskConical}
          title="Backtest evidence not yet computed"
          description="No forward-tested evidence exists yet for this date. Backfilling or fetching data that covers it will compute this evidence — no numbers are fabricated in the meantime."
        />
      ) : evidence ? (
        <>
          {backtest.evidence_status === "refreshing" ? (
            <RefreshingEvidenceBanner
              generatedAt={backtest.evidence_generated_at}
              evidenceAsof={backtest.evidence_asof}
            />
          ) : null}
          {/* iter-17 audit fix (J-08/AG-3): this section's OWN copy states a factual window claim —
              "expanding window ≤ <date>", "every snapshot dated on or before <date>", "Snapshots
              contributing (≤ <date>): n" — so it must be labeled with the as-of the served numbers
              were actually computed for, NOT the page's requested as-of. They are the SAME value in
              every state except the one this iteration introduced (`refreshing` after the fallback
              crossed an as-of boundary), where the served aggregate's window ends at the OLDER
              `evidence_asof`; labeling it with the page's newer `asof_date` would assert a window and
              an n that the payload does not contain, directly contradicting the banner above it. The
              `?? asof_date` keeps the pre-iter-17 value for any response without the field. */}
          <EvidenceAggregateSection
            evidence={evidence}
            asofDate={backtest.evidence_asof ?? backtest.asof_date}
          />
        </>
      ) : null}
    </div>
  );
}

// --- Refreshing-evidence disclosure (ops-hardening iter-16, J-08; evidenceAsof added iter-17, J-08 audit
// B1): a small, calm, factual banner shown ABOVE the still-fully-populated evidence section while the
// newer dataset version's evidence is not yet complete. The copy states ONLY what the resolver actually
// knows (the stamp changed; the new version is incomplete; WHICH as-of's evidence this is; and when it
// was generated) — it must never assert that a warm is currently in flight (a stamp bump from any new
// ScannerRun/ForwardReturn row leaves this state standing with no warm running) nor promise an automatic
// update (this page refetches only on mount / an as-of change / a readiness transition — there is no
// poll; see the effect deps in BacktestPage). `evidenceAsof` (iter-17) discloses WHICH as-of's evidence is
// being shown — equal to the page's own resolved date when the resolver served an older *version* of this
// SAME date, or a genuinely OLDER date when the fallback crossed an as-of boundary (the common shape
// right after a new latest trading day lands and its ingest warm has not finished, audit B1). Borrows the
// Card + Loader2 warn-toned LOOK already established by WarmingState/SurvivorshipBanner on this same page
// — but this is a DISTINCT, request-scoped disclosure (the served evidence's own status) and must NOT
// wire to useReadiness() (that hook is the boot-time warm-up concept, unrelated to this per-request state).
function RefreshingEvidenceBanner({
  generatedAt,
  evidenceAsof,
}: {
  generatedAt: string | null;
  evidenceAsof: string | null;
}) {
  return (
    <Card
      className="flex items-start gap-3 border-warn bg-surface p-4 text-sm"
      data-testid="evidence-refreshing"
    >
      <Loader2 className="mt-0.5 h-5 w-5 shrink-0 animate-spin text-warn" aria-hidden />
      <div className="space-y-1">
        <p className="font-medium text-warn">Refreshing — showing the last complete evidence</p>
        <p className="text-text-muted">
          The dataset has changed since this evidence was generated, and the newer version is not
          complete yet. The forward-tested evidence below is the last complete version — evidence as of{" "}
          <span className="num">{formatIsoDate(evidenceAsof)}</span>, generated{" "}
          <span className="num">{formatIsoDateTime(generatedAt)}</span> — no partial or fabricated
          figures are shown in the meantime. Reload this page after the next ingest finishes to pick up
          the new version.
        </p>
      </div>
    </Card>
  );
}

// --- As-of scan summary header (regime + candidate counts only; the leadership lists moved below) -
function AsOfScanSummary({ dashboard }: { dashboard: DashboardResponse | null }) {
  if (dashboard === null) {
    return (
      <Card className="flex items-center gap-3 border-border bg-surface p-5 text-sm text-text-muted">
        <AlertTriangle className="h-5 w-5 shrink-0 text-warn" aria-hidden />
        Scan summary unavailable for this date — the dashboard endpoint did not respond. The
        forward-test scorecard below is unaffected.
      </Card>
    );
  }
  const { regime } = dashboard;
  return (
    <div className="space-y-4">
      <h2 className="text-sm font-semibold text-text">As-of scan summary</h2>
      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader className="flex-row items-center justify-between space-y-0">
            <CardTitle>Market Regime</CardTitle>
            <Badge variant={regimeVariant(regime.label)}>{regime.label}</Badge>
          </CardHeader>
          <CardContent>
            <div className="flex items-baseline gap-2">
              <span className="num text-3xl font-semibold text-text">{regime.score.toFixed(2)}</span>
              <span className="text-sm text-text-muted">/ 100</span>
            </div>
          </CardContent>
        </Card>
        <CandidateCountsCard counts={dashboard.candidate_counts} />
      </div>
    </div>
  );
}

// --- Leadership cohorts (J-21) — Top Sectors / Top Themes / Ranked Cohort, relocated BELOW Return
// Attribution, each carrying the realized forward return at the SELECTED horizon. The returns are the
// read-only `leadership_returns` projection joined onto the rows already fetched from /api/sectors
// (by sector-ETF ticker), /api/themes (by slug), /api/stocks (by ticker). NA ("—") honestly when the
// horizon lacks post-bars. The horizon is the SAME view selector that drives the attribution above.
function LeadershipListsSection({
  sectors,
  themes,
  stocks,
  leadership,
  horizon,
  min,
}: {
  sectors: SectorsResponse | null;
  themes: ThemesResponse | null;
  stocks: StocksResponse | null;
  leadership: LeadershipReturns | undefined;
  horizon: number;
  min: number;
}) {
  const topSectors = sectors ? sectors.rows.slice(0, TOP_N_PANEL) : [];
  const topThemes = themes ? themes.rows.slice(0, TOP_N_PANEL) : [];
  const cohort = stocks ? stocks.rows.slice(0, COHORT_ROWS) : [];

  // join the read-only realized returns by the keys the lists already carry (sector ETF / slug / ticker)
  const sectorRet = new Map((leadership?.sectors ?? []).map((r) => [r.sector_etf, r] as const));
  const themeRet = new Map((leadership?.themes ?? []).map((r) => [r.slug, r] as const));
  const cohortRet = new Map((leadership?.cohort ?? []).map((r) => [r.ticker, r] as const));

  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-sm font-semibold text-text">Leadership cohorts</h2>
        <p className="mt-0.5 max-w-2xl text-xs text-text-faint">
          The top sectors, themes, and ranked stocks for this date — each with its{" "}
          <span className="text-text">realized forward return at the {horizon}-day horizon</span> (read
          from the stored forward returns; set by the Horizon selector above). “—” means the window has
          not elapsed in the seed (NA); nothing is fabricated.
        </p>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader className="flex-row items-center justify-between space-y-0">
            <CardTitle>Top Sectors</CardTitle>
            <span className="num text-xs uppercase tracking-wide text-text-faint">Fwd {horizon}d</span>
          </CardHeader>
          <CardContent>
            {sectors === null ? (
              <p className="text-sm text-neg">Sector data unavailable.</p>
            ) : topSectors.length === 0 ? (
              <p className="text-sm text-text-muted">No ranked sectors for this date.</p>
            ) : (
              <ul className="space-y-2">
                {topSectors.map((row) => {
                  const ret = sectorRet.get(row.ticker);
                  return (
                    <li key={row.ticker} className="flex items-center justify-between gap-2">
                      <span className="flex items-center gap-2">
                        <span className="num text-text-faint">{row.rank}</span>
                        <span className="num font-semibold text-text">{row.ticker}</span>
                        <span className="text-xs text-text-muted">{row.trend_label}</span>
                      </span>
                      <span className="flex items-center gap-3">
                        <ScoreBadge bucket={row.bucket} score={row.score} />
                        <Return value={ret?.mean_return ?? null} n={ret?.n ?? 0} min={min} />
                      </span>
                    </li>
                  );
                })}
              </ul>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex-row items-center justify-between space-y-0">
            <CardTitle>Top Themes</CardTitle>
            <span className="num text-xs uppercase tracking-wide text-text-faint">Fwd {horizon}d</span>
          </CardHeader>
          <CardContent>
            {themes === null ? (
              <p className="text-sm text-neg">Theme data unavailable.</p>
            ) : topThemes.length === 0 ? (
              <p className="text-sm text-text-muted">No ranked themes for this date.</p>
            ) : (
              <ul className="space-y-2">
                {topThemes.map((row) => {
                  const ret = themeRet.get(row.slug);
                  return (
                    <li key={row.slug} className="flex items-center justify-between gap-2">
                      <span className="flex items-center gap-2">
                        <span className="num text-text-faint">{row.rank}</span>
                        <span className="font-semibold text-text">{row.name}</span>
                        <span className="text-xs text-text-muted">{row.trend_label}</span>
                      </span>
                      <span className="flex items-center gap-3">
                        <ScoreBadge bucket={row.bucket} score={row.score} />
                        <Return value={ret?.mean_return ?? null} n={ret?.n ?? 0} min={min} />
                      </span>
                    </li>
                  );
                })}
              </ul>
            )}
          </CardContent>
        </Card>
      </div>

      <Card className="p-0">
        <div className="border-b border-border px-5 py-4">
          <h3 className="text-sm font-semibold text-text">Ranked cohort</h3>
          <p className="mt-0.5 text-xs text-text-faint">
            The top {COHORT_ROWS} ranked stocks for this date (the cohort the scorecard forward-tests),
            each with its realized {horizon}-day forward return.
          </p>
        </div>
        {stocks === null ? (
          <p className="px-5 py-4 text-sm text-neg">Stock data unavailable.</p>
        ) : cohort.length === 0 ? (
          <p className="px-5 py-4 text-sm text-text-muted">No ranked stocks for this date.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[40rem] border-collapse text-sm">
              <thead>
                <tr className="border-b border-border text-left text-xs uppercase tracking-wide text-text-faint">
                  <th className="px-5 py-2 font-medium">#</th>
                  <th className="px-3 py-2 font-medium">Ticker</th>
                  <th className="px-3 py-2 font-medium">Setup</th>
                  <th className="px-3 py-2 text-right font-medium">Leadership</th>
                  <th className="px-5 py-2 text-right font-medium">Fwd {horizon}d</th>
                </tr>
              </thead>
              <tbody>
                {cohort.map((row) => {
                  const ret = cohortRet.get(row.ticker);
                  return (
                    <tr key={row.ticker} className="border-b border-border last:border-b-0">
                      <td className="num px-5 py-2 text-text-faint">{row.rank}</td>
                      <td className="num px-3 py-2 font-semibold text-text">{row.ticker}</td>
                      <td className="px-3 py-2 text-xs text-text-muted">{row.setup.status}</td>
                      <td className="px-3 py-2 text-right">
                        <ScoreBadge bucket={row.leadership.bucket} score={row.leadership.score} />
                      </td>
                      <td className="px-5 py-2 text-right">
                        <Return value={ret?.mean_return ?? null} n={ret?.n ?? 0} min={min} />
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  );
}

function CandidateCountsCard({ counts }: { counts: Record<string, number> }) {
  const rows: { label: string; key: string; accent: boolean }[] = [
    { label: "Actionable", key: "Actionable", accent: true },
    { label: "Breakout-watch", key: "Breakout-watch", accent: false },
    { label: "Pullback-watch", key: "Pullback-watch", accent: false },
  ];
  return (
    <Card>
      <CardHeader>
        <CardTitle>Candidate Counts</CardTitle>
      </CardHeader>
      <CardContent>
        <ul className="space-y-1.5">
          {rows.map(({ label, key, accent }) => (
            <li key={key} className="flex items-center justify-between text-sm">
              <span className="text-text-muted">{label}</span>
              <span className={cn("num text-lg font-semibold", accent ? "text-pos" : "text-text")}>
                {counts[key] ?? 0}
              </span>
            </li>
          ))}
        </ul>
      </CardContent>
    </Card>
  );
}

// --- Forward-test scorecard (the NEW per-date value from /api/backtest) --------------------------
function controlCohort(row: { control_group: ControlGroupRow[] }, key: string): ControlGroupRow | undefined {
  return row.control_group.find((cohort) => cohort.key === key);
}

function ScorecardSection({ data }: { data: BacktestResponse }) {
  const min = data.min_sample;
  const rows = data.scorecard.by_horizon;
  const anyObserved = rows.some((row) => row.cohort.n > 0);

  return (
    <Card className="p-0">
      <div className="border-b border-border px-5 py-4">
        <h2 className="text-sm font-semibold text-text">Forward-test scorecard</h2>
        <p className="mt-0.5 text-xs text-text-faint">
          Realized return of the top-ranked cohort (rank ≤ top-N) per horizon, the excess vs
          SPY/QQQ/sector, and the control cohorts — each with sample size n. Windows that have not
          elapsed in the seed show “—” (NA) with n=0; figures with{" "}
          <span className="text-warn">n &lt; {min} ⚠</span> are low-sample. Nothing is fabricated.
        </p>
      </div>

      {!anyObserved ? (
        <EmptyState
          icon={FlaskConical}
          className="rounded-none border-0 border-b-0 py-12"
          title="No elapsed forward window for this date yet"
          description="This snapshot has no post-snapshot price bars in the seed, so no realized forward return is observable yet — every horizon is NA (n=0). Pick an older as-of date to see a full scorecard. No numbers are fabricated to fill the gap."
        />
      ) : null}

      <div className="overflow-x-auto">
        <table className="w-full min-w-[56rem] border-collapse text-sm">
          <thead>
            <tr className="border-b border-border text-left text-xs uppercase tracking-wide text-text-faint">
              <th className="px-5 py-2 font-medium">
                <span className="inline-flex items-center gap-1">Horizon<TermInfo term="horizon" /></span>
              </th>
              <th className="px-3 py-2 text-right font-medium">
                <span className="inline-flex items-center gap-1">Cohort<TermInfo term="forward return" /></span>
              </th>
              <th className="px-3 py-2 text-right font-medium">
                <span className="inline-flex items-center gap-1">vs SPY<TermInfo term="excess return" /></span>
              </th>
              <th className="px-3 py-2 text-right font-medium">
                <span className="inline-flex items-center gap-1">vs QQQ<TermInfo term="excess return" /></span>
              </th>
              <th className="px-3 py-2 text-right font-medium">
                <span className="inline-flex items-center gap-1">vs Sector<TermInfo term="excess return" /></span>
              </th>
              <th className="px-3 py-2 text-right font-medium">
                <span className="inline-flex items-center gap-1">Random peers<TermInfo term="random same-sector control" /></span>
              </th>
              <th className="px-3 py-2 text-right font-medium">SPY</th>
              <th className="px-3 py-2 text-right font-medium">QQQ</th>
              <th className="px-5 py-2 text-right font-medium">Sector ETF</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => {
              const random = controlCohort(row, "random_same_sector");
              const spy = controlCohort(row, "spy");
              const qqq = controlCohort(row, "qqq");
              const sectorEtf = controlCohort(row, "sector_etf");
              return (
                <tr key={row.horizon} className="border-b border-border last:border-b-0">
                  <td className="num px-5 py-2 font-semibold text-text">{row.horizon}d</td>
                  <td className="bg-surface-2 px-3 py-2 text-right">
                    <Return value={row.cohort.mean_return} n={row.cohort.n} min={min} />
                  </td>
                  <td className="px-3 py-2 text-right">
                    <Return value={row.excess.vs_spy.mean_excess} n={row.excess.vs_spy.n} min={min} />
                  </td>
                  <td className="px-3 py-2 text-right">
                    <Return value={row.excess.vs_qqq.mean_excess} n={row.excess.vs_qqq.n} min={min} />
                  </td>
                  <td className="px-3 py-2 text-right">
                    <Return value={row.excess.vs_sector.mean_excess} n={row.excess.vs_sector.n} min={min} />
                  </td>
                  <td className="px-3 py-2 text-right">
                    <Return value={random?.mean_return ?? null} n={random?.n ?? 0} min={min} />
                  </td>
                  <td className="px-3 py-2 text-right">
                    <Return value={spy?.mean_return ?? null} n={spy?.n ?? 0} min={min} />
                  </td>
                  <td className="px-3 py-2 text-right">
                    <Return value={qqq?.mean_return ?? null} n={qqq?.n ?? 0} min={min} />
                  </td>
                  <td className="px-5 py-2 text-right">
                    <Return value={sectorEtf?.mean_return ?? null} n={sectorEtf?.n ?? 0} min={min} />
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

// --- Return attribution (J-19) — a client-side horizon VIEW selector over data already in the payload
// The selector picks WHICH already-fetched by_horizon[*].attribution to display. It triggers NO
// refetch, takes NO fetch param, and keys NO date effect — the page still holds no independent date
// state and reads only the global useAsOf() switcher (preserves the J-18 single-date-control
// consolidation). The horizon is a VIEW preference, not a date control.
function HorizonViewSelector({
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
        aria-label="Attribution horizon (trading days)"
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

function BacktestSkeleton() {
  return (
    <div className="space-y-4">
      <div className="grid gap-4 lg:grid-cols-3">
        {Array.from({ length: 3 }).map((_, i) => (
          <Card key={i} className="h-32 animate-pulse bg-surface-2" />
        ))}
      </div>
      <Card className="h-64 animate-pulse bg-surface-2" />
    </div>
  );
}
