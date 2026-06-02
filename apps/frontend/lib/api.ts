/**
 * Typed backend API client. RE-FORMATS server values only — NO business computation here
 * (no scores/buckets/returns are ever computed client-side; the backend is the single source
 * of truth). Each fetcher throws on a network error or non-200 so callers render an explicit
 * "Backend unavailable" state — we never fabricate data.
 */

export const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function getJSON<T>(path: string, signal?: AbortSignal): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, { signal, cache: "no-store" });
  if (!res.ok) {
    throw new Error(`request failed: GET ${path} -> HTTP ${res.status}`);
  }
  return (await res.json()) as T;
}

/** Append `?as_of=YYYY-MM-DD` (the iter-8 as-of switch) when a historical date is selected; the
 *  latest view passes nothing. The frontend only chooses WHICH date's stored values to fetch — it
 *  never recomputes a score/bucket/return (the backend serves them from the immutable snapshot). */
function withAsOf(path: string, asof?: string): string {
  if (!asof) return path;
  const sep = path.includes("?") ? "&" : "?";
  return `${path}${sep}as_of=${encodeURIComponent(asof)}`;
}

/** Mutating request (POST/DELETE — the iter-7 watchlist write calls). On a non-2xx it throws an
 *  Error carrying the backend's honest `detail` message so the UI renders an explicit failure
 *  (e.g. "ANET is already on the watchlist") — never a fabricated success. */
async function sendJSON<T>(method: "POST" | "DELETE", path: string, body?: unknown): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    method,
    headers: body === undefined ? undefined : { "Content-Type": "application/json" },
    body: body === undefined ? undefined : JSON.stringify(body),
    cache: "no-store",
  });
  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try {
      const data = (await res.json()) as { detail?: unknown };
      if (typeof data?.detail === "string") detail = data.detail;
      else if (data?.detail) detail = JSON.stringify(data.detail);
    } catch {
      /* non-JSON error body — keep the HTTP status message */
    }
    throw new Error(detail);
  }
  return (await res.json()) as T;
}

// --- health (iter-1) -----------------------------------------------------------------------
export interface HealthStatus {
  status: string;
  db_ok: boolean;
  provider: string;
  last_run_date: string | null;
  seed_latest_date: string | null;
  symbol_count: number;
}

/** Fetch backend health. Throws on network error or non-200 so callers can render an
 *  explicit "unavailable" state — we never fabricate an "ok". */
export async function fetchHealth(signal?: AbortSignal): Promise<HealthStatus> {
  return getJSON<HealthStatus>("/api/health", signal);
}

// --- shared score shapes (iter-2) ----------------------------------------------------------
/** One named, explainable score component (the source of the "why"). Sector rows carry
 *  raw+percentile; the regime panel carries value; the VIX gate carries threshold/factor. */
export interface ScoreComponent {
  name: string;
  weight: number;
  contribution: number | null;
  available: boolean;
  raw?: number | null;
  percentile?: number | null;
  value?: number | null;
  threshold?: number;
  factor?: number;
  elevated?: boolean;
}

// --- sectors (iter-2) ----------------------------------------------------------------------
export interface SectorRow {
  ticker: string;
  kind: "sector" | "industry";
  name: string;
  score: number;
  bucket: string; // A | B | C | D | E
  rs_vs_spy: number | null;
  dist_from_52w_high_pct: number | null;
  trend_label: string;
  components: ScoreComponent[];
  rank: number;
}

export interface SectorsResponse {
  asof_date: string;
  benchmark: string; // SPY — the RS benchmark, excluded from the ranked rows
  rows: SectorRow[];
}

/** Canonical Sector Score source: GET /api/sectors. The Dashboard's Top Sectors slice this
 *  same response — there is no second computation/source for the sector score. `asof` time-travels
 *  to that date's stored snapshot (iter-8). */
export async function fetchSectors(asof?: string, signal?: AbortSignal): Promise<SectorsResponse> {
  return getJSON<SectorsResponse>(withAsOf("/api/sectors", asof), signal);
}

// --- dashboard (iter-2 + iter-3 candidate counts) ------------------------------------------
export interface NewHighLow {
  new_highs: number;
  new_lows: number;
  evaluated: number;
  net_pct: number;
  universe_relative: boolean;
}

export interface DashboardResponse {
  regime: {
    score: number;
    label: string;
    components: ScoreComponent[];
    asof_date: string;
  };
  breadth: {
    above_50dma_pct: number | null;
    above_200dma_pct: number | null;
    new_high_low: NewHighLow;
    label: string; // "universe-relative"
  };
  asof_date: string;
  // iter-3: real counts of the canonical per-stock setup statuses (keyed by status name).
  candidate_counts: Record<string, number>;
}

/** Canonical Market Regime + candidate-counts source: GET /api/dashboard. `asof` time-travels to
 *  that date's stored snapshot (iter-8). */
export async function fetchDashboard(asof?: string, signal?: AbortSignal): Promise<DashboardResponse> {
  return getJSON<DashboardResponse>(withAsOf("/api/dashboard", asof), signal);
}

// --- stocks (iter-3) -----------------------------------------------------------------------
/** One of the three independent scores: 0-100 + its A-E bucket + named component breakdown.
 *  Re-formatted only — never computed client-side (the backend is the single source of truth). */
export interface ScoreBlock {
  score: number;
  bucket: string; // A | B | C | D | E
  components: ScoreComponent[];
}

export interface StockSetup {
  status: string; // Actionable | Pullback-watch | Breakout-watch | Extended | Avoid | Risk-off-watchlist
  reason: string;
}

/** One theme the stock belongs to (the reverse of config.themes). `name` is the backend's shared
 *  derivation — the SAME label shown on the Themes leaderboard (no client-side renaming). */
export interface ThemeChip {
  slug: string;
  name: string;
}

/** The server-computed invalidation level (iter-4): the price below which the long thesis is wrong.
 *  `level` is the canonical N-DMA (or null on short history) and `note` is built server-side — the UI
 *  renders `note` VERBATIM and never assembles the "$X" string (single source of truth). */
export interface Invalidation {
  basis: string; // e.g. "50-DMA"
  ma_period: number;
  level: number | null; // canonical sma over the config invalidation MA period; null = NA
  price: number | null; // latest close (as-of); null when no history
  note: string; // human sentence, rendered verbatim
}

/** The VCP (Volatility Contraction Pattern) flag (iter-11) — a DETECTED PATTERN that rides the row
 *  ALONGSIDE the setup status, never replacing it. Computed once on the backend (price+volume only,
 *  date <= as-of) and read identically on the leaderboard and detail page (single source → J-06). The
 *  UI re-formats this only — it NEVER computes a flag client-side. When not flagged, `pivot` and
 *  `invalidation.level` are null (no fabricated pattern); `reason`/`note` are server-built, rendered
 *  verbatim. SEPARATE from the setup status — VCP alone never makes a name Actionable. */
export interface Vcp {
  flagged: boolean;
  reason: string; // plain-language, server-built (rendered verbatim)
  pivot: number | null; // the breakout level = the base high; null when not flagged
  invalidation: { level: number | null; note: string }; // last-contraction low + verbatim sentence
  contractions?: number[]; // detected contraction depths (percent), tightening
  detail?: Record<string, number | null>; // n_contractions, volume_ratio, dist_from_pivot_pct
}

/** The pullback-to-rising-DMA pattern flag (iter-9) — a DETECTED PATTERN riding the row ALONGSIDE the
 *  setup status (never replacing it; never alone making a name Actionable). Same read-only contract as
 *  `Vcp`: computed once on the backend (price+volume only, date <= as-of), read identically everywhere
 *  (single source → J-06), re-formatted by the UI only (never recomputed). When not flagged, `pivot`
 *  and `invalidation.level` are null (no fabricated pattern); `reason`/`note` are server-built. */
export interface PullbackToRisingDma {
  flagged: boolean;
  reason: string;
  pivot: number | null; // the recent high (resumption level); null when not flagged
  invalidation: { level: number | null; note: string }; // the rising MA + verbatim sentence
  detail?: Record<string, number | null>; // dma, slope_pct, dist_from_dma_pct, pullback_depth_pct, volume_ratio
}

/** The flat-base-breakout pattern flag (iter-9) — same read-only, pattern-not-status contract as
 *  `Vcp`/`PullbackToRisingDma`. `pivot` is the base high (breakout level); `invalidation.level` is the
 *  base low. Null when not flagged (never fabricated); reason/note are server-built, rendered verbatim. */
export interface FlatBaseBreakout {
  flagged: boolean;
  reason: string;
  pivot: number | null; // the base high (breakout level); null when not flagged
  invalidation: { level: number | null; note: string }; // the base low + verbatim sentence
  detail?: Record<string, number | null>; // base_depth_pct, dist_below_pivot_pct, volume_ratio
}

export interface StockRow {
  ticker: string;
  name: string;
  sector: string; // GICS sector name (one of the 11 sector ETF names)
  leadership: ScoreBlock;
  entry_quality: ScoreBlock;
  risk: ScoreBlock; // higher score = MORE dangerous (colour-graded by danger direction)
  setup: StockSetup;
  themes: ThemeChip[]; // every theme whose member list contains this ticker (config order)
  invalidation: Invalidation;
  vcp: Vcp; // the VCP pattern flag (iter-11) — separate from `setup`, read-only re-display
  // iter-9: two more detected patterns ride the row the SAME way (separate from `setup`, read-only)
  pullback_to_rising_dma: PullbackToRisingDma;
  flat_base_breakout: FlatBaseBreakout;
  rank: number;
}

export interface StocksResponse {
  asof_date: string;
  benchmark: string; // SPY
  rows: StockRow[];
}

export interface StockDetailResponse {
  asof_date: string;
  benchmark: string;
  row: StockRow;
}

/** Canonical per-stock scores source: GET /api/stocks (list). Filters/sorting on this list are
 *  pure client-side re-display — no score/bucket is recomputed. `asof` time-travels to that date's
 *  stored snapshot (iter-8). */
export async function fetchStocks(asof?: string, signal?: AbortSignal): Promise<StocksResponse> {
  return getJSON<StocksResponse>(withAsOf("/api/stocks", asof), signal);
}

/** GET /api/stocks/{ticker} — the SAME row the leaderboard serves (single source → J-06). `asof`
 *  time-travels to that date's stored snapshot (iter-8). */
export async function fetchStock(ticker: string, asof?: string, signal?: AbortSignal): Promise<StockDetailResponse> {
  return getJSON<StockDetailResponse>(withAsOf(`/api/stocks/${encodeURIComponent(ticker)}`, asof), signal);
}

// --- stock price/MA/volume series for the detail chart (iter-4) -----------------------------
/** One ascending OHLCV bar. By default date <= as-of (no lookahead — the backend reads only
 *  `bars_asof`). With the J-20 `through=latest` opt-in the series extends through the latest seed bar
 *  and each bar carries `is_forward` (true iff its date is AFTER the as-of D) so the chart can label
 *  the post-D region; those forward bars are DISPLAY-ONLY and never feed a score/bucket/VCP. */
export interface PriceBar {
  date: string; // ISO date (YYYY-MM-DD)
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  is_forward?: boolean; // J-20: true for bars dated AFTER the as-of D (display-only forward region)
}

/** GET /api/stocks/{ticker}/bars payload. `ma` is keyed by each config MA period ("20","50",…) →
 *  a rolling moving-average series aligned 1:1 with `bars` (a number, or null for the warm-up gap).
 *  The chart PLOTS this server series — it never computes a moving average from the close array.
 *  `latest_date` is present only in the J-20 `through=latest` mode (the last bar shown = the right
 *  boundary); `asof_date` is always the resolved as-of D (the forward-region boundary). */
export interface BarsResponse {
  asof_date: string;
  ticker: string;
  bars: PriceBar[];
  ma: Record<string, (number | null)[]>;
  latest_date?: string; // J-20: latest seed bar shown (only in through=latest mode)
}

/** Canonical price/MA/volume series source: GET /api/stocks/{ticker}/bars. Throws on non-200 so the
 *  chart renders an explicit unavailable state (404 unknown ticker / 503 no data / 4xx bad as_of) —
 *  never fabricated. `asof` returns the bars with date <= D (the as-of chart; iter-8). Pass
 *  `through="latest"` (J-20) to render the DISPLAY-ONLY full path through the latest seed date with the
 *  as-of boundary marked (`is_forward` per bar + `latest_date`); the default (no `through`) stays <= D. */
export async function fetchStockBars(
  ticker: string,
  asof?: string,
  signal?: AbortSignal,
  through?: string,
): Promise<BarsResponse> {
  let path = withAsOf(`/api/stocks/${encodeURIComponent(ticker)}/bars`, asof);
  if (through) {
    path += `${path.includes("?") ? "&" : "?"}through=${encodeURIComponent(through)}`;
  }
  return getJSON<BarsResponse>(path, signal);
}

// --- themes (iter-3) -----------------------------------------------------------------------
export interface ThemeRow {
  slug: string;
  name: string;
  score: number;
  bucket: string;
  members: string[];
  return_1m: number | null; // % equal-weight basket return
  return_3m: number | null;
  breadth_pct: number | null; // % members above their 50-DMA
  breadth_label: string; // "universe-relative"
  trend_label: string;
  components: ScoreComponent[];
  rank: number;
}

export interface ThemesResponse {
  asof_date: string;
  rows: ThemeRow[];
}

/** Canonical Theme Score source: GET /api/themes. The Dashboard's Top Themes slice this same
 *  response (top N) — there is no second computation/source for the theme score. `asof` time-travels
 *  to that date's stored snapshot (iter-8). */
export async function fetchThemes(asof?: string, signal?: AbortSignal): Promise<ThemesResponse> {
  return getJSON<ThemesResponse>(withAsOf("/api/themes", asof), signal);
}

// --- scanner runs (iter-5) -----------------------------------------------------------------
/** One row in the immutable scan-run history (GET /api/runs). `regime` carries the stored as-of
 *  label+score; `candidate_counts` are the stored counts of the canonical setup statuses. */
export interface RunSummary {
  run_id: number;
  asof_date: string;
  created_at: string;
  regime: { label: string; score: number };
  candidate_counts: Record<string, number>;
  n_stocks: number;
}

export interface RunsResponse {
  runs: RunSummary[];
}

/** The immutable scan-run history, descending by as-of date (GET /api/runs). Throws on non-200 so
 *  the page renders an explicit "Backend unavailable" state — never fabricated runs. */
export async function fetchRuns(signal?: AbortSignal): Promise<RunsResponse> {
  return getJSON<RunsResponse>("/api/runs", signal);
}

/** One run's full STORED snapshot (GET /api/runs/{run_id}) — the exact as-of view for that date.
 *  `regime`/`breadth`/`candidate_counts` mirror the dashboard shapes; `rows` are the SAME canonical
 *  `StockRow` shape the leaderboard serves (rehydrated from the stored record), so the detail page
 *  reuses the leaderboard row rendering + `ScoreBadge`. Nothing is recomputed client-side. */
export interface RunDetail {
  run_id: number;
  asof_date: string;
  created_at: string;
  provider: string;
  benchmark: string;
  regime: {
    label: string;
    score: number;
    components: ScoreComponent[];
    asof_date: string;
  };
  breadth: {
    above_50dma_pct: number | null;
    above_200dma_pct: number | null;
    new_high_low: NewHighLow;
    label: string; // "universe-relative"
  };
  candidate_counts: Record<string, number>;
  rows: StockRow[]; // stored canonical rows for the run's as-of date
}

/** GET /api/runs/{run_id}. Throws on non-200 so the detail page renders an explicit unavailable
 *  state (404 unknown run / 503 no data) — never a fabricated run. */
export async function fetchRun(runId: string | number, signal?: AbortSignal): Promise<RunDetail> {
  return getJSON<RunDetail>(`/api/runs/${encodeURIComponent(String(runId))}`, signal);
}

// --- system health / forward-tested evidence (iter-6) --------------------------------------
/** One row of a grouped forward-return breakdown: the mean realized return (a fraction, e.g. 0.0123
 *  = +1.23%) and the sample size `n`. `mean_return` is null for a padded empty group (n === 0).
 *  Re-formatted only — the page never recomputes a return. */
export interface ForwardGroupRow {
  mean_return: number | null;
  n: number;
}

export interface ForwardBucketRow extends ForwardGroupRow {
  bucket: string; // A | B | C | D | E (the stored canonical leadership bucket, verbatim)
}
export interface ForwardSetupRow extends ForwardGroupRow {
  setup: string; // canonical setup status
}
export interface ForwardRegimeRow extends ForwardGroupRow {
  regime: string; // stored regime label of the run
}
export interface ForwardVcpRow extends ForwardGroupRow {
  vcp: string; // "VCP" | "non-VCP" cohort label (iter-11)
}
export interface ForwardPullbackRow extends ForwardGroupRow {
  pullback_to_rising_dma: string; // "Pullback-to-DMA" | "non-Pullback" cohort label (iter-9)
}
export interface ForwardFlatBaseRow extends ForwardGroupRow {
  flat_base_breakout: string; // "Flat-base" | "non-Flat-base" cohort label (iter-9)
}

/** Excess vs a benchmark = mean stock forward return − mean benchmark forward return over matched
 *  runs (a stored subtraction; never recomputed client-side). */
export interface ExcessVsBenchmark {
  benchmark: string; // SPY | QQQ
  mean_excess: number | null;
  stock_mean: number | null;
  benchmark_mean: number | null;
  n: number; // stock observations
  benchmark_n: number; // benchmark observations (runs)
}

/** One control-group cohort (J-10): top-ranked vs random same-sector vs SPY/QQQ/sector-ETF. */
export interface ControlGroupRow extends ForwardGroupRow {
  key: string; // top_ranked | random_same_sector | spy | qqq | sector_etf
  label: string; // server-built human label (rendered verbatim)
}

// --- return attribution (J-19) -------------------------------------------------------------
/** One per-stock attribution row: a named ticker's mean realized forward return over the same stored
 *  observations, its sample size n, and its stored sector. Re-formatted only — never recomputed. */
export interface PerStockRow {
  ticker: string;
  mean_return: number | null;
  n: number;
  sector: string | null;
}

/** Per-stock contributors (highest mean) and detractors (lowest mean), each up to top_contributors_k. */
export interface PerStockAttribution {
  contributors: PerStockRow[];
  detractors: PerStockRow[];
}

/** By-sector attribution row (reuses the grouped mean+n shape with the stored sector name). */
export interface BySectorRow extends ForwardGroupRow {
  sector: string; // stored sector name (config sector vocabulary)
}

/** By-rank-band attribution row: the config band label (1–10 / 11–50 / 51+) with its mean+n. */
export interface ByRankBandRow extends ForwardGroupRow {
  rank_band: string; // config band label, rendered verbatim
}

/** Distribution & hit-rate of the SAME observed forward returns: mean, median, % positive (hit rate,
 *  a 0..1 fraction), dispersion (sample stdev; null when n < 2), with n. Re-formatted from stored
 *  returns — never recomputed client-side. */
export interface Distribution {
  mean_return: number | null;
  median: number | null;
  pct_positive: number | null;
  dispersion: number | null;
  n: number;
}

/** The four READ-ONLY return-attribution slices (J-19): which tickers drove/dragged the cohort, which
 *  sectors and rank bands carried the return, and the return's distribution shape. Derived from the
 *  stored per-observation forward returns by the SAME engine that builds the aggregate/scorecard — the
 *  page re-formats only and recomputes no return. */
export interface ReturnAttribution {
  per_stock: PerStockAttribution;
  by_sector: BySectorRow[];
  by_rank_band: ByRankBandRow[];
  distribution: Distribution;
}

/** GET /api/system-health payload — the SINGLE canonical forward-return aggregation. Every figure
 *  carries its sample size `n`; the page re-formats only and recomputes no return/excess/bucket. */
export interface SystemHealthResponse {
  horizon: number; // the served forward window (trading days)
  horizons: number[]; // valid horizons for the selector (from config — not hard-coded in the UI)
  default_horizon: number;
  min_sample: number; // figures with n below this are flagged low-sample
  survivorship_bias: string; // honest caveat, rendered verbatim
  n_runs: number; // walk-forward snapshots contributing evidence at this horizon
  asof_dates: string[]; // the contributing as-of dates (descending)
  overall: ForwardGroupRow;
  by_bucket: ForwardBucketRow[]; // rows A..E (J-09)
  by_setup: ForwardSetupRow[]; // by setup type (J-09)
  by_regime: ForwardRegimeRow[]; // by market regime — both Risk-on and Risk-off (J-09)
  by_vcp: ForwardVcpRow[]; // VCP vs non-VCP cohorts (iter-11, J-16) — each with n; NA below min_sample
  // iter-9, J-28: pattern-vs-non-pattern cohorts for the two new detected patterns — each with n; NA below min_sample
  by_pullback_to_rising_dma: ForwardPullbackRow[];
  by_flat_base_breakout: ForwardFlatBaseRow[];
  excess: { vs_spy: ExcessVsBenchmark; vs_qqq: ExcessVsBenchmark }; // J-09
  control_group: ControlGroupRow[]; // J-10
  attribution: ReturnAttribution; // J-19 — per-stock / by-sector / by-rank-band / distribution
}

/** Canonical forward-tested evidence source: GET /api/system-health?horizon=. Throws on non-200 so
 *  the page renders an explicit "Backend unavailable" state (503 no data / 422 invalid horizon) —
 *  never fabricated evidence. */
export async function fetchSystemHealth(horizon: number, signal?: AbortSignal): Promise<SystemHealthResponse> {
  return getJSON<SystemHealthResponse>(`/api/system-health?horizon=${encodeURIComponent(horizon)}`, signal);
}

// --- backtest / per-date forward-test scorecard (iter-10, J-14) ----------------------------
/** Cohort excess vs one benchmark cohort = cohort mean − benchmark mean (a stored subtraction; the
 *  page never recomputes it). `mean_excess` / `cohort_mean` / `benchmark_mean` are null for an NA
 *  cohort or benchmark; `n` is the cohort sample size, `benchmark_n` the benchmark cohort's. */
export interface ScorecardExcess {
  benchmark: string; // SPY | QQQ | sector-ETF cohort label (rendered verbatim)
  mean_excess: number | null;
  cohort_mean: number | null;
  benchmark_mean: number | null;
  n: number; // cohort observations
  benchmark_n: number; // benchmark observations
}

// --- backtest leadership realized returns (J-21) -------------------------------------------
/** One Top-Sectors row's realized forward return = its sector-ETF's OWN stored return at the horizon.
 *  `sector_etf` is the join key onto a `/api/sectors` row (`row.ticker`). Re-formatted only — never
 *  recomputed (a read-only projection of the stored `forward_returns`). */
export interface LeadershipSectorReturn extends ForwardGroupRow {
  sector_etf: string; // sector ETF ticker (join key = /api/sectors row.ticker)
  sector: string; // sector name
}
/** One Top-Themes row's realized forward return = the equal-weight mean of its members' stored returns
 *  at the horizon. `slug` is the join key onto a `/api/themes` row (`row.slug`). */
export interface LeadershipThemeReturn extends ForwardGroupRow {
  slug: string; // theme slug (join key = /api/themes row.slug)
}
/** One Ranked-Cohort row's realized forward return = the stock's OWN stored return at the horizon.
 *  `ticker` is the join key onto a `/api/stocks` row (`row.ticker`). */
export interface LeadershipCohortReturn extends ForwardGroupRow {
  ticker: string; // universe ticker (join key = /api/stocks row.ticker)
}

/** The J-21 read-only leadership-return projection riding each scorecard horizon row: the realized
 *  forward return of every Top Sector / Top Theme / Ranked-Cohort name at that horizon, derived from
 *  the SAME stored `forward_returns` the scorecard/attribution read. The page joins these onto the rows
 *  it already fetches (sectors by `sector_etf`, themes by `slug`, cohort by `ticker`) and re-formats
 *  only — it recomputes no return. Honest NA (mean_return null, n 0) when a horizon lacks post-bars. */
export interface LeadershipReturns {
  sectors: LeadershipSectorReturn[];
  themes: LeadershipThemeReturn[];
  cohort: LeadershipCohortReturn[];
}

/** One per-horizon row of the per-date scorecard: the top-ranked cohort's mean realized return + n,
 *  the excess vs SPY/QQQ/sector, and the five control-group cohorts — each figure with its sample
 *  size `n` and honest NA (null) for a window that has not fully elapsed in the seed. */
export interface BacktestScorecardHorizonRow {
  horizon: number; // 1 | 5 | 10 | 20 | 60 (from config.walk_forward.horizons)
  cohort: ForwardGroupRow; // top-ranked cohort (rank ≤ control_group.top_n)
  excess: { vs_spy: ScorecardExcess; vs_qqq: ScorecardExcess; vs_sector: ScorecardExcess };
  control_group: ControlGroupRow[]; // top_ranked / random_same_sector / spy / qqq / sector_etf
  attribution: ReturnAttribution; // J-19 — over THIS horizon's observed set (not just the cohort)
  leadership_returns: LeadershipReturns; // J-21 — Top Sector/Theme/Cohort realized returns at this horizon
}

export interface BacktestScorecard {
  by_horizon: BacktestScorecardHorizonRow[];
}

/** GET /api/backtest payload — the SINGLE canonical per-date forward-test scorecard (J-14). Every
 *  figure carries its sample size `n`; the page re-formats only and recomputes no return/excess. The
 *  scan summary's regime/sector/theme/stock values come from their OWN canonical endpoints, not here. */
export interface BacktestResponse {
  asof_date: string; // the resolved as-of date (ISO)
  is_latest: boolean; // true when the resolved date is the latest stored run
  min_sample: number; // figures with n below this are flagged low-sample
  horizons: number[]; // 1/5/10/20/60 (from config — not hard-coded in the UI)
  survivorship_bias: string; // honest caveat, rendered verbatim
  scorecard: BacktestScorecard;
}

/** Canonical per-date forward-test scorecard source: GET /api/backtest?as_of=. Throws on non-200 so
 *  the page renders an explicit "Backend unavailable" state (503 no data / 4xx invalid date) — never
 *  fabricated evidence. `asof` time-travels to that date's stored immutable snapshot. */
export async function fetchBacktest(asof?: string, signal?: AbortSignal): Promise<BacktestResponse> {
  return getJSON<BacktestResponse>(withAsOf("/api/backtest", asof), signal);
}

// --- watchlist (iter-7) --------------------------------------------------------------------
/** One persisted watchlist entry, enriched at serve time. The stored fields are `id`/`ticker`/
 *  `date_added`/`asof_date_added`/`reason`; the CURRENT `leadership`/`entry_quality`/`risk` (each a
 *  ScoreBlock), `setup`, and `invalidation` are READ LIVE from the canonical `score_stocks` row (the
 *  SAME values `/api/stocks` serves — single source → J-06) and re-displayed only. `price_since_added`
 *  is a fraction (0.0123 = +1.23%) derived from the canonical price series — null = NA (no entry_close
 *  / no current close); 0.0 against the frozen seed is the honest, correct value. */
export interface WatchlistEntry {
  id: number;
  ticker: string;
  date_added: string; // ISO datetime ("date added")
  asof_date_added: string; // ISO date (latest data date captured at add time)
  reason: string;
  sector: string;
  leadership: ScoreBlock;
  entry_quality: ScoreBlock;
  risk: ScoreBlock; // higher = MORE dangerous (ScoreBadge uses invert)
  setup: StockSetup;
  invalidation: Invalidation;
  price_since_added: number | null; // fraction; null = NA, never fabricated
}

export interface WatchlistResponse {
  asof_date: string;
  entries: WatchlistEntry[];
}

/** GET /api/watchlist — every saved entry (newest first), enriched live. Throws on non-200 so the
 *  page renders an explicit "Backend unavailable" state (503 no data) — never fabricated entries. */
export async function fetchWatchlist(signal?: AbortSignal): Promise<WatchlistResponse> {
  return getJSON<WatchlistResponse>("/api/watchlist", signal);
}

/** POST /api/watchlist — save a stock with a free-text reason (the first MUTATING client call).
 *  Returns the enriched entry on success; throws with the backend's honest `detail` on a non-2xx
 *  (404 unknown ticker / 409 duplicate / 503 no data) so the UI shows an explicit error. */
export async function addWatchlistEntry(ticker: string, reason: string): Promise<WatchlistEntry> {
  return sendJSON<WatchlistEntry>("POST", "/api/watchlist", { ticker, reason });
}

/** DELETE /api/watchlist/{id} — remove an entry. Throws with the backend's `detail` on a non-2xx
 *  (404 missing entry) so the UI surfaces the failure rather than silently succeeding. */
export async function removeWatchlistEntry(id: number): Promise<{ id: number; deleted: boolean }> {
  return sendJSON<{ id: number; deleted: boolean }>("DELETE", `/api/watchlist/${id}`);
}

// --- methodology / glossary catalog (iter-12, J-12) ----------------------------------------
/** One threshold row of a methodology entry. EITHER a config-referenced numeric row (`value` with an
 *  optional `cmp`/`unit`) whose number is resolved LIVE on the backend from the same config the engine
 *  reads (so it always matches — never recomputed/​re-typed client-side), OR a prose `text` rule. */
export interface MethodologyThresholdRow {
  label: string;
  cmp?: string;
  value?: number;
  unit?: string;
  text?: string;
}

/** One glossary entry — a setup status (`kind:"setup"`) or a detected pattern (`kind:"pattern"`).
 *  `key` is the canonical identifier (a setup status name, or a pattern key like "vcp"); `meaning`
 *  and `example` are plain-language copy; `thresholds` are the config-defined rules. */
export interface MethodologyEntry {
  key: string;
  kind: "setup" | "pattern";
  name: string;
  meaning: string;
  thresholds: MethodologyThresholdRow[];
  example: string;
}

/** The Universe Selection section (J-22) — the config-recorded screen that defines membership. The
 *  `membership_rule` prose + the three screen `thresholds` (resolved LIVE from `universe.filters` on the
 *  backend, so they always match the offline screen) + the `resolved_size` read from the ONE canonical
 *  universe (the same value GET /api/data reports as `universe_count`). The frontend re-formats it only. */
export interface UniverseSelection {
  membership_rule: string;
  thresholds: MethodologyThresholdRow[];
  resolved_size: number;
}

/** The config-backed Setup & Pattern catalog served by GET /api/methodology. The ONE source for the
 *  /methodology page, the /stocks badge tooltips, AND the /stocks setup-filter vocabulary.
 *  `universe_selection` (J-22) carries the Universe Selection section when configured. */
export interface MethodologyCatalog {
  intro?: string;
  universe_selection?: UniverseSelection;
  entries: MethodologyEntry[];
}

/** Canonical Setup & Pattern glossary source: GET /api/methodology. Throws on non-200 so callers
 *  render an explicit "Backend unavailable" state — never fabricated copy. */
export async function fetchMethodology(signal?: AbortSignal): Promise<MethodologyCatalog> {
  return getJSON<MethodologyCatalog>("/api/methodology", signal);
}

// --- research / factor lab (iter-10, J-25) -------------------------------------------------
/** One catalogued factor (the dropdown vocabulary, config-driven on the backend — NOT a hard-coded
 *  frontend list). `direction`/`family` are descriptive metadata; `source` documents where the stored
 *  value is read from. The frontend renders `label` and selects by `key`. */
export interface FactorLabFactor {
  key: string;
  label: string;
  family: string;
  direction: string; // higher_better | lower_better (descriptive)
  source: string;
}

/** One decile row (D1…D10): the mean realized forward return (raw), the DOWNSIDE risk-adjusted column
 *  (mean / downside-deviation; null = NA — never total volatility), and the sample size `n`, plus the
 *  factor value bounds of the decile. `low_sample` (n < min_sample) flags the cells the UI renders as
 *  NA + n. Re-formatted only — the page recomputes no return/factor. */
export interface FactorDecileRow {
  decile: number; // 1..deciles
  factor_min: number | null;
  factor_max: number | null;
  mean_return: number | null; // raw mean forward return (fraction); null when n === 0
  risk_adjusted: number | null; // downside-deviation-adjusted; null = NA (no downside / n < 2)
  n: number;
  low_sample: boolean; // n < min_sample — render NA + n, never a fabricated number
}

/** The factor's rank information coefficient (Spearman): value + sign + n; value null = NA (n < 2 or
 *  zero rank variance) — never a fabricated 0. */
export interface RankIC {
  value: number | null;
  n: number;
}

/** One row of the J-27 regime-effectiveness split: does this factor still sort forward returns WITHIN
 *  this market regime? The per-regime sample size `n`, the Spearman `rank_ic`, the raw top/bottom decile
 *  means, and the long-short top-minus-bottom-decile `spread` both raw and downside-`risk_adjusted`.
 *  `low_sample` (n < min_sample) or a null leg renders NA + n; the regime list is SERVER-driven (from
 *  config.regime.labels) — NOT a hard-coded frontend list. Re-formatted only — never recomputed. */
export interface RegimeEffectivenessRow {
  regime: string; // stored regime label (config.regime.labels vocabulary, verbatim)
  n: number;
  low_sample: boolean; // n < min_sample — render NA + n, never a fabricated number
  rank_ic: RankIC;
  top_decile_mean: number | null; // raw mean of the highest factor decile within the regime
  bottom_decile_mean: number | null; // raw mean of the lowest factor decile within the regime
  spread: number | null; // top − bottom decile mean (raw long-short); null = NA (low-sample / empty leg)
  risk_adjusted_spread: number | null; // downside-risk-adjusted long-short; null = NA (no downside / low-sample)
}

/** GET /api/research/factor-lab payload (J-25) — the SINGLE canonical Factor-Lab analysis for one
 *  factor × horizon. Every figure is derived once from the stored forward returns + stored factor
 *  values; the page re-formats only and recomputes no return/factor. A cross-date aggregate (like
 *  System Health) — there is NO as-of/date control (J-18). */
export interface FactorLabResponse {
  factor: FactorLabFactor; // the resolved factor
  horizon: number; // the served forward window (trading days)
  factors: FactorLabFactor[]; // the config-driven catalog (the factor dropdown vocabulary)
  horizons: number[]; // valid horizons for the selector (from config — not hard-coded in the UI)
  default_horizon: number;
  deciles_count: number;
  min_sample: number; // deciles with n below this are NA/low-sample
  survivorship_bias: string; // honest caveat, rendered verbatim
  descriptive_caveat: string; // "descriptive, not predictive / universe-relative", rendered verbatim
  n_total: number; // observations contributing at this horizon
  deciles: FactorDecileRow[]; // D1…D10 (config-driven count)
  rank_ic: RankIC;
  by_regime: RegimeEffectivenessRow[]; // J-27: per configured regime — rank-IC + raw/downside long-short spread + n
}

/** Canonical Factor-Lab source: GET /api/research/factor-lab?factor=&horizon=. Throws on non-200 so the
 *  page renders an explicit "Backend unavailable" state (503 no data / 422 unknown factor or horizon) —
 *  never fabricated evidence. Both params are optional (defaults: first catalog factor / config default
 *  horizon). */
export async function fetchFactorLab(
  factor?: string,
  horizon?: number,
  signal?: AbortSignal,
): Promise<FactorLabResponse> {
  const params = new URLSearchParams();
  if (factor) params.set("factor", factor);
  if (horizon !== undefined) params.set("horizon", String(horizon));
  const query = params.toString();
  return getJSON<FactorLabResponse>(`/api/research/factor-lab${query ? `?${query}` : ""}`, signal);
}

// --- research / multi-factor combination cohorts (iter-12, J-26) ---------------------------
/** One quantile option (the top/bottom tail vocabulary, config-driven on the backend — NOT a hard-coded
 *  frontend list). `fraction` is the tail size a top/bottom condition selects (0.20 = a quintile). The
 *  frontend renders `label` and selects by `key`. */
export interface QuantileOption {
  key: string;
  label: string;
  fraction: number;
}

/** One resolved combination condition: a catalog factor at its `top`/`bottom` quantile tail. The factor
 *  + quantile descriptors come from the payload (config-driven) — the frontend renders their labels and
 *  builds the row label, never inventing a factor/quantile. */
export interface FactorCombinationCondition {
  factor: FactorLabFactor;
  side: "top" | "bottom";
  quantile: QuantileOption;
}

/** One cohort's descriptive stats, derived once on the backend from the stored returns (the page
 *  re-formats only). `mean_return`/`median_return` are return fractions; `hit_rate` is the fraction `> 0`
 *  (0..1); `risk_adjusted` is the DOWNSIDE-only ratio (mean / downside-deviation — never total vol; null
 *  = NA). Every figure is `null` for an empty cohort (NA, never a fabricated 0); `low_sample`
 *  (n < min_sample) flags the cohort the UI renders as NA + n. */
export interface CohortStats {
  n: number;
  mean_return: number | null;
  median_return: number | null;
  hit_rate: number | null;
  risk_adjusted: number | null;
  low_sample: boolean;
}

/** The unconditional baseline / combined-AND cohort: a server-built `label` + its `stats`. */
export interface FactorCombinationCohort {
  label: string;
  stats: CohortStats;
}

/** One single-factor cohort: the resolved `condition` (for the row label) + its `stats`. */
export interface FactorCombinationSingle {
  condition: FactorCombinationCondition;
  stats: CohortStats;
}

/** GET /api/research/factor-combination payload (J-26) — the SINGLE canonical multi-factor combination
 *  analysis: the combined-AND cohort vs the unconditional `baseline` vs each single-factor cohort, each
 *  with mean / median forward return, hit-rate, downside-risk-adjusted, and n. Every figure is derived
 *  once from the SAME stored pool the Factor Lab reads; the page re-formats only and recomputes no
 *  return/factor. A cross-date aggregate (like the Factor Lab) — there is NO as-of/date control (J-18).
 *  `factors`/`quantiles` are the config-driven dropdown vocabularies (no hard-coded list in the UI). */
export interface FactorCombinationResponse {
  conditions: FactorCombinationCondition[]; // the resolved requested combination
  horizon: number; // the served forward window (trading days)
  horizons: number[]; // valid horizons (from config — not hard-coded in the UI)
  default_horizon: number;
  min_sample: number; // cohorts with n below this are flagged low-sample (render NA + n)
  min_conditions: number; // condition-count bounds (from config) — drive add/remove enablement
  max_conditions: number;
  factors: FactorLabFactor[]; // the config-driven factor catalog (the Factor dropdown vocabulary)
  quantiles: QuantileOption[]; // the config-driven quantile vocabulary (the Quantile dropdown)
  survivorship_bias: string; // honest caveat, rendered verbatim
  descriptive_caveat: string; // "descriptive, not predictive", rendered verbatim
  pool_n: number; // the multi-factor observation pool size (all referenced factors non-null)
  baseline: FactorCombinationCohort; // the unconditional all-names cohort
  singles: FactorCombinationSingle[]; // one cohort per condition
  combined: FactorCombinationCohort; // the exact AND-intersection cohort
}

/** Canonical multi-factor combination source: GET /api/research/factor-combination. Builds repeated
 *  `condition=<factor>:<side>:<quantile>` query params + an optional `horizon`. Throws on non-200 so the
 *  page renders an explicit "Backend unavailable" state (503 no data / 422 bad factor/side/quantile/count/
 *  horizon) — never fabricated cohorts. With no conditions the backend serves its config default_conditions. */
export async function fetchFactorCombination(
  conditions: { factor: string; side: string; quantile: string }[],
  horizon?: number,
  signal?: AbortSignal,
): Promise<FactorCombinationResponse> {
  const params = new URLSearchParams();
  for (const c of conditions) {
    params.append("condition", `${c.factor}:${c.side}:${c.quantile}`);
  }
  if (horizon !== undefined) params.set("horizon", String(horizon));
  const query = params.toString();
  return getJSON<FactorCombinationResponse>(
    `/api/research/factor-combination${query ? `?${query}` : ""}`,
    signal,
  );
}

// --- data manager (iter-3, J-17) -----------------------------------------------------------
/** Current dataset coverage — descriptive metadata only (the frontend re-formats it; it computes no
 *  coverage figure). `gaps_preview` is a bounded list of the backfill-able trading days that have bars
 *  but no snapshot; `gap_count` is the true total. */
export interface DataCoverage {
  price_start: string | null;
  price_end: string | null;
  symbol_count: number;
  // the RESOLVED UNIVERSE size — the one canonical universe (the committed screen result), the SAME
  // value /api/methodology reports as universe_selection.resolved_size (J-22; single source, no drift).
  // Distinct from symbol_count (DISTINCT priced symbols, which includes the benchmark ETFs + ^VIX).
  universe_count: number;
  snapshot_count: number;
  snapshot_dates: string[]; // newest first
  trading_day_count: number;
  gap_count: number;
  gap_first: string | null;
  gap_last: string | null;
  gaps_preview: string[]; // ascending; bounded by config.data_manager.gap_preview
}

/** One row of the fetch/backfill run history (from the append-only DataProviderRun log). A Data Manager
 *  job carries `kind`/`start`/`end`/`snapshots_created`/…; a plain seed-load row leaves them null. */
export interface DataRun {
  id: number;
  provider: string;
  kind: string | null; // fetch | backfill | both | null (seed load)
  start: string | null;
  end: string | null;
  status: string; // ok | partial | failed
  symbols_ok: number;
  symbols_failed: number;
  snapshots_created: number | null;
  dates_done: number | null;
  dates_total: number | null;
  bars_fetched: number | null;
  started_at: string | null;
  finished_at: string | null;
  message: string | null;
}

export interface DataOverviewResponse {
  coverage: DataCoverage;
  runs: DataRun[];
}

export type DataJobKind = "fetch" | "backfill" | "both";

/** Live progress for one fetch/backfill job (polled from the in-memory job registry). `status` is
 *  running | ok | partial | failed; counters are the live progress; `message` is a server-built summary
 *  (rendered verbatim); `errors` carries explicit per-symbol failure messages (never fabricated). */
export interface DataJob {
  job_id: string;
  kind: string;
  start: string;
  end: string;
  status: string;
  symbols_total: number;
  symbols_ok: number;
  symbols_failed: number;
  bars_fetched: number;
  dates_total: number;
  dates_done: number;
  snapshots_created: number;
  forward_returns_inserted: number;
  message: string;
  errors: string[];
  started_at: string;
  finished_at: string | null;
}

export interface StartJobResponse {
  job_id: string;
  kind: string;
  start: string;
  end: string;
  status: string;
}

/** Canonical Data Manager coverage + run-history source: GET /api/data. Throws on non-200 so the page
 *  renders an explicit "Backend unavailable" state — never fabricated coverage. */
export async function fetchDataCoverage(signal?: AbortSignal): Promise<DataOverviewResponse> {
  return getJSON<DataOverviewResponse>("/api/data", signal);
}

/** POST /api/data/jobs — start an async fetch/backfill job over a date range (the date inputs are JOB
 *  PARAMETERS, NOT a viewing as-of control). Returns immediately with a `job_id`; throws with the
 *  backend's honest `detail` on a non-2xx (400 invalid range / 422 malformed date / 503 no data). */
export async function startDataJob(
  kind: DataJobKind,
  start: string,
  end: string,
): Promise<StartJobResponse> {
  return sendJSON<StartJobResponse>("POST", "/api/data/jobs", { kind, start, end });
}

/** GET /api/data/jobs/{job_id} — poll a job's live status/progress, ending in its final summary.
 *  Throws on non-200 (404 unknown job) so the UI surfaces the failure rather than fabricating one. */
export async function fetchDataJob(jobId: string, signal?: AbortSignal): Promise<DataJob> {
  return getJSON<DataJob>(`/api/data/jobs/${encodeURIComponent(jobId)}`, signal);
}
