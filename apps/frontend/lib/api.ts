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
/** One ascending OHLCV bar (date <= as-of; no lookahead — the backend reads only `bars_asof`). */
export interface PriceBar {
  date: string; // ISO date (YYYY-MM-DD)
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

/** GET /api/stocks/{ticker}/bars payload. `ma` is keyed by each config MA period ("20","50",…) →
 *  a rolling moving-average series aligned 1:1 with `bars` (a number, or null for the warm-up gap).
 *  The chart PLOTS this server series — it never computes a moving average from the close array. */
export interface BarsResponse {
  asof_date: string;
  ticker: string;
  bars: PriceBar[];
  ma: Record<string, (number | null)[]>;
}

/** Canonical price/MA/volume series source: GET /api/stocks/{ticker}/bars. Throws on non-200 so the
 *  chart renders an explicit unavailable state (404 unknown ticker / 503 no data / 4xx bad as_of) —
 *  never fabricated. `asof` returns the bars with date <= D (the as-of chart; iter-8). */
export async function fetchStockBars(ticker: string, asof?: string, signal?: AbortSignal): Promise<BarsResponse> {
  return getJSON<BarsResponse>(withAsOf(`/api/stocks/${encodeURIComponent(ticker)}/bars`, asof), signal);
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
  excess: { vs_spy: ExcessVsBenchmark; vs_qqq: ExcessVsBenchmark }; // J-09
  control_group: ControlGroupRow[]; // J-10
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

/** One per-horizon row of the per-date scorecard: the top-ranked cohort's mean realized return + n,
 *  the excess vs SPY/QQQ/sector, and the five control-group cohorts — each figure with its sample
 *  size `n` and honest NA (null) for a window that has not fully elapsed in the seed. */
export interface BacktestScorecardHorizonRow {
  horizon: number; // 1 | 5 | 10 | 20 | 60 (from config.walk_forward.horizons)
  cohort: ForwardGroupRow; // top-ranked cohort (rank ≤ control_group.top_n)
  excess: { vs_spy: ScorecardExcess; vs_qqq: ScorecardExcess; vs_sector: ScorecardExcess };
  control_group: ControlGroupRow[]; // top_ranked / random_same_sector / spy / qqq / sector_etf
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

/** The config-backed Setup & Pattern catalog served by GET /api/methodology. The ONE source for the
 *  /methodology page, the /stocks badge tooltips, AND the /stocks setup-filter vocabulary. */
export interface MethodologyCatalog {
  intro?: string;
  entries: MethodologyEntry[];
}

/** Canonical Setup & Pattern glossary source: GET /api/methodology. Throws on non-200 so callers
 *  render an explicit "Backend unavailable" state — never fabricated copy. */
export async function fetchMethodology(signal?: AbortSignal): Promise<MethodologyCatalog> {
  return getJSON<MethodologyCatalog>("/api/methodology", signal);
}
