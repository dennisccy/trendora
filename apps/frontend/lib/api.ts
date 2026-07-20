/**
 * Typed backend API client. RE-FORMATS server values only — NO business computation here
 * (no scores/buckets/returns are ever computed client-side; the backend is the single source
 * of truth). Each fetcher throws on a network error or non-200 so callers render an explicit
 * "Backend unavailable" state — we never fabricate data.
 */

import { resolveApiBase } from "@/lib/api-base";
import type { BudgetResponse, BudgetSpendPoint, CanonicalBudget, StagingBudget } from "@/lib/budget";
import type {
  CertifiedClaim,
  DistributionCell,
  DrawdownExpectations,
  EvidenceLedgerResponse,
  LossStreakCell,
  PhaseExpectations,
  ProvenSignal,
} from "@/lib/evidence";
import type { GraveyardEntry, GraveyardResponse, RevisitProtocol } from "@/lib/graveyard";
import type { PreRegistrationRow, RegistryResponse } from "@/lib/registry";
import type {
  RefereeAuditContaminatedVerdict,
  RefereeAuditReport,
  RefereeAuditResponse,
} from "@/lib/referee-audit";

// Re-export the read-side evidence types (goal-mcp-loop iter-1) so callers import them from the API client
// alongside `fetchEvidence`. These are DISTINCT from `EvidenceAggregate` below (the Backtest forward-tested
// aggregate) — do not confuse the two.
export type { CertifiedClaim, EvidenceLedgerResponse, ProvenSignal };

// Re-export the additive drawdown & dry-spell expectations types (goal-mcp-loop iter-41, J-25) — the
// nullable `median`/`p90`/`value` numeric fields route every consumer through the guarded
// `formatDays`/`formatStreak`/`fmtMdd` formatters (never an unguarded `.toFixed` on a possibly-null value).
export type { DistributionCell, DrawdownExpectations, LossStreakCell, PhaseExpectations };

// Re-export the pre-registration registry types (goal-mcp-loop iter-30, J-18) alongside `fetchRegistry`.
export type { PreRegistrationRow, RegistryResponse };

// Re-export the negative-results graveyard types (goal-mcp-loop iter-31, J-19) alongside `fetchGraveyard`.
export type { GraveyardEntry, GraveyardResponse, RevisitProtocol };

// Re-export the certification-budget accounting types (goal-mcp-loop iter-32, J-17) alongside `fetchBudget`.
export type { BudgetResponse, BudgetSpendPoint, CanonicalBudget, StagingBudget };

// Re-export the referee-calibration report types (goal-mcp-loop iter-36, J-22) alongside `fetchRefereeAudit`.
export type { RefereeAuditContaminatedVerdict, RefereeAuditReport, RefereeAuditResponse };

/** The build-time configured backend base (`NEXT_PUBLIC_API_URL`, default localhost). The configured
 *  backend PORT (`NEXT_PUBLIC_API_PORT`) is read alongside so the runtime resolver can host-swap to the
 *  page's own host when the page is opened at a non-localhost (LAN-IP) origin (J-108). Both are inlined
 *  by Next at build time. */
const CONFIGURED_API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const CONFIGURED_API_PORT = process.env.NEXT_PUBLIC_API_PORT ?? null;

/** Back-compat export: the build-time configured base. Prefer `apiBase()` for runtime host-aware use. */
export const API_BASE = CONFIGURED_API_BASE;

/** Resolve the backend base at REQUEST time — host-aware (J-108). On the client it reads the page's
 *  `window.location.hostname` so a page opened at a LAN-IP origin hits the backend on that SAME host
 *  (not "localhost", which would be the viewer's own machine); during SSR (`window` undefined) it falls
 *  back to the configured base. An explicit non-localhost `NEXT_PUBLIC_API_URL` is always used verbatim.
 *  This re-resolves only WHERE the backend is — it never fabricates readiness or any served value. */
function apiBase(): string {
  const hostname = typeof window !== "undefined" ? window.location.hostname : undefined;
  return resolveApiBase(CONFIGURED_API_BASE, hostname, CONFIGURED_API_PORT);
}

async function getJSON<T>(path: string, signal?: AbortSignal): Promise<T> {
  const res = await fetch(`${apiBase()}${path}`, { signal, cache: "no-store" });
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
  const res = await fetch(`${apiBase()}${path}`, {
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

// --- health + readiness (iter-1 / iter-28 J-40) --------------------------------------------
/** The honest backend readiness state computed ONCE by the backend (app.engine.readiness) and served
 *  on the single canonical /api/health endpoint. The frontend NEVER computes readiness itself — it
 *  renders this value. `ready` = serving + history warmed; `initializing` = latest servable but the
 *  background historical warm-up is still loading; `unavailable` = no servable snapshot / DB down. */
export type ReadinessState = "ready" | "initializing" | "unavailable";

/** Background warm-up progress (cadence snapshots produced / expected — "history n/m"). `done`/`total`
 *  drive the badge progress + the Backtest/Research "warming up (n/m)" states. */
export interface WarmupProgress {
  done: number;
  total: number;
  status: string;
  message: string;
}

// --- daily preflight verdict (iter-33, J-20 / backlog B-301) ------------------------------
/** The single canonical GO/DEGRADED/NO-GO verdict computed ONCE by the backend
 *  (app.engine.readiness.compute_preflight) and served on the SAME /api/health payload. The frontend
 *  NEVER computes this itself — it renders this value verbatim (single source). */
export type PreflightVerdict = "GO" | "DEGRADED" | "NO-GO";

/** One composed input's contribution to the verdict (servability / freshness / integrity). */
export interface PreflightComponent {
  ok: boolean;
  severity: string;
  detail: string;
}

export interface PreflightStatus {
  verdict: PreflightVerdict;
  /** Plain-language reason strings for every breached component, in composition order. */
  reasons: string[];
  components: Record<string, PreflightComponent>;
  /** The deterministic, seed-resolved freshness anchor (ISO date), or null with no price data. Served
   *  under both names (`as_of`/`reference` are the SAME value) since the spec names it either way. */
  as_of: string | null;
  reference: string | null;
}

export interface HealthStatus {
  status: string;
  db_ok: boolean;
  provider: string;
  last_run_date: string | null;
  seed_latest_date: string | null;
  symbol_count: number;
  // iter-28 (J-40): the single canonical readiness value (state + warm-up progress).
  readiness: ReadinessState;
  warmup: WarmupProgress;
  // the config-derived poll cadences the badge derives its interval from (no client-side poll literal).
  poll_interval_seconds: number;
  poll_idle_interval_seconds: number;
  // iter-33 (J-20): the single daily preflight verdict (additive).
  preflight: PreflightStatus;
}

/** Fetch backend health + readiness. Throws on network error or non-200 so callers can render an
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
  // J-58: config reference metadata served verbatim from the stored snapshot. `description` is a
  // plain-language one-liner (null for sector ETFs and for a stored run predating the column);
  // `members` is the config-derived universe-member list (sector members from stock_sectors,
  // industry members from stock_industries) — an empty array renders the explicit empty state.
  description: string | null;
  members: string[];
  score: number;
  bucket: string; // A | B | C | D | E
  rs_vs_spy: number | null;
  dist_from_52w_high_pct: number | null;
  trend_label: string;
  components: ScoreComponent[];
  rank: number;
  // iter-23 (J-81): the five realized forward returns (1/5/10/20/60-day from config horizons) — the
  // sector/industry ETF's OWN stored return per horizon, read VERBATIM via the SAME _leadership_returns
  // builder Backtest's Top Sectors uses (never recomputed). `return` is null (NA) where no stored row
  // exists (industry ETFs without a stored bar, or at/near latest) — never fabricated. Config order.
  forward_returns: ForwardReturnEntry[];
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

/** One risk-budget component (iter-40, J-24 / B-201): a stored value + its CROSS-SECTIONAL universe
 *  percentile in [0,1] (higher percentile = MORE risk by this measure — the card's "pXX of universe"
 *  framing), both read verbatim from the server — never recomputed client-side. `value`/`percentile`
 *  null together = NA (insufficient history); `percentile` is never present without `value`. */
export interface RiskBudgetComponent {
  value: number | null;
  percentile: number | null;
}

/** The overnight-gap risk profile (iter-40, J-24 / B-201): the distribution of overnight moves over the
 *  gap window (median / p95 / worst), plus the overnight share of the same window's return variance —
 *  the risk an invalidation level cannot protect against (a gap jumps past it, it does not breach it). */
export interface GapProfile {
  median: RiskBudgetComponent;
  p95: RiskBudgetComponent;
  worst: RiskBudgetComponent;
  overnight_variance_share: RiskBudgetComponent;
}

/** The per-stock "how much can this hurt" risk-budget bundle (iter-40, J-24 / B-201) — computed ONCE by
 *  `scoring:score_stocks` and served verbatim on the SAME two stock endpoints the rest of `StockRow`
 *  comes from (no new endpoint, no UI recompute). Descriptive statistics only — no proven-language, no
 *  position advice (anti-goals #1/#2). Historical scanner rows predating iter-40 carry no `risk_budget`
 *  key at all (honest absence, never a fabricated NA) — optional on `StockRow` for that reason. */
export interface RiskBudget {
  atr_pct: RiskBudgetComponent;
  downside_vol: RiskBudgetComponent;
  gap_profile: GapProfile;
  worst_20d_window: RiskBudgetComponent;
  distance_to_invalidation_pct: RiskBudgetComponent;
}

export interface StockRow {
  ticker: string;
  name: string;
  // GICS sector name (one of the 11 sector ETF names), or null for a pool name with no mapped sector
  // (iter-19: the broadened 548-name pool left ~78% of names unmapped in `config.stock_sectors` — the
  // backend honestly serves null rather than fabricating a sector). Consumers must use
  // `lib/sector-label.ts`'s `sectorLabel`/`compareSectors` — never `.localeCompare` a raw `sector` value.
  sector: string | null;
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
  // iter-20 (J-75): the five realized forward returns (1/5/10/20/60-day from config horizons) read
  // VERBATIM from the stored forward_returns table for the resolved as-of run — the SAME stored data
  // Backtest reads (never recomputed). `return` is null (NA) where no stored row exists for that horizon
  // (so at/near the latest date all five are NA — never fabricated). Order maps to config horizons.
  forward_returns: StockForwardReturn[];
  // iter-40 (J-24 / B-201): the risk-budget card/leaderboard-column bundle. Optional — a scanner row
  // persisted before iter-40 carries no `risk_budget` key at all (honest absence; only the served
  // bootstrap + latest snapshots regenerate with it, historical runs stay as they were).
  risk_budget?: RiskBudget;
}

/** One forward-return entry: the realized return at `horizon` trading days, or null (NA) when no stored
 *  row exists, paired with the realized max-drawdown (iter-27, J-86 — the true peak-to-trough decline,
 *  <= 0 or null/NA, read VERBATIM from the same stored row). Read verbatim from the stored forward_returns
 *  table — never recomputed. The SHARED shape used by the per-stock (J-75) and the per-theme / per-sector
 *  (J-81) leaderboard forward-return lists. `max_drawdown` is NA exactly when `return` is NA. */
export interface ForwardReturnEntry {
  horizon: number;
  return: number | null;
  max_drawdown: number | null;
}

/** Alias preserved for the J-75 per-stock callsites (the same `{horizon, return}` shape as J-81). */
export type StockForwardReturn = ForwardReturnEntry;

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

// --- read-side evidence ledger (goal-mcp-loop iter-1) --------------------------------------
/** GET /api/evidence — the read-only certified-claims ledger surface. Returns the ledger rows the
 *  Evidence page renders (`claims`) and the `proven_signals` map the inline status badge reads. The
 *  evidence ledger is the SINGLE source of proven-ness — the UI never computes it; it re-displays the
 *  referee's verdicts verbatim. Against today's empty ledger this is `{claims: [], proven_signals: {}}`,
 *  so every signal honestly reads "Not yet proven". Throws on network error or non-200 so callers fall
 *  back to the fail-safe "Not yet proven" — never a fabricated "Proven". */
export async function fetchEvidence(signal?: AbortSignal): Promise<EvidenceLedgerResponse> {
  return getJSON<EvidenceLedgerResponse>("/api/evidence", signal);
}

// --- pre-registration registry (goal-mcp-loop iter-30, J-18 / backlog B-901) ----------------
/** GET /api/research/registry — the read-only pre-registration registry: every hypothesis ever
 *  registered/tested, read VERBATIM from the SAME file + loader the post-decompose gate cross-checks an
 *  incoming Evidence Claim against. Re-formats nothing; introduces no proven-language. Throws on network
 *  error or non-200 so the page renders an explicit "Backend unavailable" state. */
export async function fetchRegistry(signal?: AbortSignal): Promise<RegistryResponse> {
  return getJSON<RegistryResponse>("/api/research/registry", signal);
}

// --- negative-results graveyard (goal-mcp-loop iter-31, J-19 / backlog B-902) ---------------
/** GET /api/research/graveyard — the read-only negative-results graveyard: every NON-PASS referee
 *  verdict across BOTH the canonical and staging certified-claims ledgers, read VERBATIM and tagged with
 *  its origin ledger + registration lineage. Re-formats nothing; introduces no proven-language (a
 *  verdict-kind badge, never "Proven"/"Not yet proven"). Throws on network error or non-200 so the page
 *  renders an explicit "Backend unavailable" state. */
export async function fetchGraveyard(signal?: AbortSignal): Promise<GraveyardResponse> {
  return getJSON<GraveyardResponse>("/api/research/graveyard", signal);
}

// --- certification-budget accounting (goal-mcp-loop iter-32, J-17 / backlog B-903) ----------
/** GET /api/research/budget — the read-only certification-budget accounting panel: total canonical
 *  trials to date, the current canonical `required_p` bar, the Thresholdout budget remaining, and the
 *  staging LORD++ next-trial level — each with a per-trial spend-over-time series, re-read (or
 *  re-derived via the SAME referee/ledger seams the certifier uses — never a parallel computation).
 *  Introduces no proven-language. Throws on network error or non-200 so the page renders an explicit
 *  "Backend unavailable" state. */
export async function fetchBudget(signal?: AbortSignal): Promise<BudgetResponse> {
  return getJSON<BudgetResponse>("/api/research/budget", signal);
}

// --- referee-calibration report (goal-mcp-loop iter-36, J-22 / backlog B-102) ---------------
/** GET /api/research/referee-audit — the read-only referee-calibration report: the empirical false-pass
 *  rate + binomial CI over seeded null factors, the configured α, and the lookahead-contaminated-factor
 *  verdict (labeled "expected: rejected") — re-read VERBATIM from the persisted offline-audit artifact
 *  (`report: null` when the harness has never run). Introduces no proven-language. Throws on network
 *  error or non-200 so the page renders an explicit "Backend unavailable" state. */
export async function fetchRefereeAudit(signal?: AbortSignal): Promise<RefereeAuditResponse> {
  return getJSON<RefereeAuditResponse>("/api/research/referee-audit", signal);
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

/** The iter-18 chart range selection (J-10 performance on the ~30-year basis): `"default"` = the
 *  bounded trailing window (config `chart_bars.default_years` before the as-of — the chart never ships
 *  every deep bar by default); `"full"` = the explicit whole-real-history opt-in (weekly-sampled beyond
 *  the config span; every sampled bar is a REAL stored daily bar — never synthesized). */
export type BarsRange = "default" | "full";

/** GET /api/stocks/{ticker}/bars payload. `ma` is keyed by each config MA period ("20","50",…) →
 *  a rolling moving-average series aligned 1:1 with `bars` (a number, or null for the warm-up gap;
 *  each value is the canonical DAILY series value at that bar — the server never recomputes an MA over
 *  a sampled subset). The chart PLOTS this server series — it never computes a moving average from the
 *  close array. `latest_date` is present only in the J-20 `through=latest` mode (the last bar shown =
 *  the right boundary); `asof_date` is always the resolved as-of D (the forward-region boundary).
 *  iter-18: `range` echoes the served range, `first_available_date` is the symbol's REAL first stored
 *  bar (honest per-name depth — a post-IPO name stays short), `window_start` the first SHOWN bar, and
 *  `downsampled` whether deep-region weekly sampling applied. */
export interface BarsResponse {
  asof_date: string;
  ticker: string;
  range: BarsRange;
  first_available_date: string; // the symbol's real first stored bar (honest depth disclosure)
  window_start: string; // the first bar actually shown for the selected range
  downsampled: boolean; // true when the deep region is weekly-sampled (range=full on a deep series)
  bars: PriceBar[];
  ma: Record<string, (number | null)[]>;
  latest_date?: string; // J-20: latest seed bar shown (only in through=latest mode)
}

/** Canonical price/MA/volume series source: GET /api/stocks/{ticker}/bars. Throws on non-200 so the
 *  chart renders an explicit unavailable state (404 unknown ticker / 503 no data / 4xx bad as_of) —
 *  never fabricated. `asof` returns the bars with date <= D (the as-of chart; iter-8). Pass
 *  `through="latest"` (J-20) to render the DISPLAY-ONLY full path through the latest seed date with the
 *  as-of boundary marked (`is_forward` per bar + `latest_date`); the default (no `through`) stays <= D.
 *  iter-18: pass `range="full"` for the explicit whole-real-history opt-in (default: the bounded
 *  trailing window — same endpoint, presentation bounding only). */
export async function fetchStockBars(
  ticker: string,
  asof?: string,
  signal?: AbortSignal,
  through?: string,
  range?: BarsRange,
): Promise<BarsResponse> {
  let path = withAsOf(`/api/stocks/${encodeURIComponent(ticker)}/bars`, asof);
  if (through) {
    path += `${path.includes("?") ? "&" : "?"}through=${encodeURIComponent(through)}`;
  }
  if (range) {
    path += `${path.includes("?") ? "&" : "?"}range=${encodeURIComponent(range)}`;
  }
  return getJSON<BarsResponse>(path, signal);
}

// --- major-indexes chart + regime history (iter-2 goal mode, J-44 + J-45) ------------------
/** One stored per-date regime point read VERBATIM from the immutable scanner_runs (label + score).
 *  Both regime-band surfaces (dashboard card + stock-detail chart) consume the SAME points so the same
 *  date shows the same stored label/color everywhere — the frontend never recomputes a regime. */
export interface RegimePoint {
  date: string; // ISO yyyy-MM-dd
  label: string; // one of the six configured regime labels (stored)
  score: number; // 0–100 (stored)
}

/** GET /api/regime-history payload. `points` are ascending by date and bounded to dates <= asof_date
 *  (no band past the resolved as-of). */
export interface RegimeHistoryResponse {
  asof_date: string;
  points: RegimePoint[];
}

/** The stored per-date market-regime series for the regime bands (J-44/J-45). `asof` bounds it to a
 *  historical date; the latest view passes nothing. Read-only — no regime is recomputed client-side.
 *
 *  `full` (J-49 — dashboard card only): when true, ask the endpoint for the WHOLE stored regime series
 *  through the latest run (display-only context past the as-of marker) instead of clamping at the as-of.
 *  The stock-detail consumer omits it, keeping the clamped (J-45) default. `asof_date` is still echoed
 *  so the card draws the vertical marker at D; the stored labels/scores are byte-identical either way. */
export async function fetchRegimeHistory(
  asof?: string,
  signal?: AbortSignal,
  full = false,
): Promise<RegimeHistoryResponse> {
  let path = withAsOf("/api/regime-history", asof);
  if (full) path += `${path.includes("?") ? "&" : "?"}full=true`;
  return getJSON<RegimeHistoryResponse>(path, signal);
}

/** One point on a normalized-% index line (rebased to the range start, computed server-side). */
export interface IndexSeriesPoint {
  date: string; // ISO yyyy-MM-dd
  pct: number; // normalized % vs the range-start close (first point ~0)
}

/** One config-listed index ETF line: its `symbol`, legend `name`, and the rebased % `points`.
 *
 *  iter-22 (J-14) additive fields, sourced from the committed-seed manifest (never a UI recompute):
 *  `vendor` is the honest data vendor ("Stooq" | "Yahoo" | "FRED-macro proxy"), `null` when the
 *  manifest has no vendor record for this symbol (e.g. the SPY/QQQ/IWM/RSP/DIA ETF lines) — never a
 *  fabricated vendor. `first` is the symbol's REAL first bar date (yyyy-MM-dd) from the manifest,
 *  independent of the selected range — NOT `points[0].date`, which is range-clamped. `first` is
 *  `null` (rendered "—") for the SAME null-vendor symbols the manifest has no record for, matching the
 *  backend contract (`compute_index_series` emits `first: null` when there is no manifest row). */
export interface IndexSeries {
  symbol: string;
  name: string;
  vendor: string | null;
  first: string | null;
  points: IndexSeriesPoint[];
}

/** One range-preset switcher option (from config). */
export interface IndexRangeOption {
  key: string;
  label: string;
}

/** GET /api/indexes payload. `series` excludes any configured symbol with no stored bars in the range
 *  (e.g. DIA — honestly omitted, never fabricated). `range` is the resolved preset; `ranges` are the
 *  config-driven switcher options. `asof_date` bounds every series (no bar dated after it). */
export interface IndexesResponse {
  asof_date: string;
  range: { key: string; label: string; days: number | null; start: string | null };
  ranges: IndexRangeOption[];
  series: IndexSeries[];
}

/** The normalized-% major-indexes display series for the dashboard chart (J-44). `range` is a preset
 *  key (from `ranges`); `asof` bounds it to a historical date. The frontend only re-formats these
 *  server-computed numbers — it never does return math. An unknown `range` yields a 422 (thrown).
 *
 *  `full` (J-49 — dashboard card only): when true, ask the endpoint for the WHOLE stored path through
 *  the latest date (display-only context past the as-of marker) instead of clamping at the as-of. The
 *  server still echoes the resolved `asof_date` (the card draws the marker at D); the overlapping
 *  `<= D` portion is value-identical to the clamped default. */
export async function fetchIndexes(
  range?: string,
  asof?: string,
  signal?: AbortSignal,
  full = false,
): Promise<IndexesResponse> {
  let path = withAsOf("/api/indexes", asof);
  if (range) {
    path += `${path.includes("?") ? "&" : "?"}range=${encodeURIComponent(range)}`;
  }
  if (full) path += `${path.includes("?") ? "&" : "?"}full=true`;
  return getJSON<IndexesResponse>(path, signal);
}

// --- market phase & severity (iter-29, J-87 + J-88) ----------------------------------------
/** One named severity component (drawdown depth / time-underwater / regime-risk / breadth-below-200DMA /
 *  VIX gate). `value` is the [0,1] component reading, `weight` its config weight, `contribution` its
 *  points contributed to the 0-100 severity. `available: false` -> the component is NA (excluded from the
 *  blend, never fabricated). The values are computed once in the backend engine and only re-formatted here. */
export interface MarketPhaseComponent {
  name: string;
  value: number | null;
  weight: number;
  contribution: number | null;
  available: boolean;
}

/** One disclosed filter observation (J-88): the [0,1] stress reading on a stored snapshot date <= D plus
 *  the filtered P(bear) at that step. The payload discloses the most-recent tail (the filter still
 *  consumed every observation <= D). */
export interface MarketPhaseObservation {
  date: string; // ISO yyyy-MM-dd
  reading: number; // [0,1] stress reading the Hamilton filter ingested at this date
  p_bear: number; // the forward-filtered P(bear) after ingesting this observation (causal)
}

/** The optional ^VIX raw-level disclosure beside the scaled vix_gate component. */
export interface MarketPhaseVixLevel {
  name: string;
  value: number | null;
  threshold: number;
  available: boolean;
}

/** GET /api/market-phase payload (J-87 + J-88). The discrete `phase` (Expansion/Pullback/Correction/
 *  Bear/Recovery), the 0-100 `severity` with its named `components` breakdown, the cycle legs
 *  (`drawdown_pct`/`off_trough_pct`), and the forward FILTERED `p_bear` (0-1) with its disclosed
 *  `observations` vector. `available: false` -> insufficient history (NA/partial — phase/severity/p_bear
 *  null), an honest empty treatment, never a fabricated figure. `asof_date` is the resolved single global
 *  as-of (the panel re-points with it — no second date state). */
/** iter-30 (J-89): one CAUSAL timeline point — the per-snapshot-date FILTERED phase + P(bear) + severity.
 *  The SAME single derived series the panel value reads (the timeline and the panel are ONE derivation). */
export interface MarketPhaseTimelinePoint {
  date: string; // ISO yyyy-MM-dd
  phase: string;
  p_bear: number; // the FILTERED (causal) P(bear) at this date (never the smoothed value)
  severity: number;
  // iter-44 (J-102): the CAUSAL config-windowed OLS slope of the served 0-100 severity (severity-points per
  // snapshot; positive = worsening, negative = easing). NULL at the warm-up head where the window is
  // unavailable (NA — never a fabricated slope). Read verbatim — the frontend computes no velocity.
  severity_velocity: number | null;
}

/** iter-30 (J-89): one dated CAUSAL downtrend episode — observed on its dates only (no future bar). */
export interface MarketPhaseEpisode {
  first_trigger_date: string;
  severity_at_trigger: number;
  last_date: string;
  peak_p_bear: number;
  peak_severity: number;
  open: boolean; // still in the downtrend as of the resolved as-of (else closed on last_date)
}

/** iter-30 (J-90): the CAUSAL recovery/turn signal for the resolved as-of — explainable, never a bare flag. */
export interface MarketPhaseRecoveryTurn {
  is_recovery_turn: boolean;
  available: boolean;
  reason: string; // the config-defined triggering reason in words
  p_bear?: number | null;
  prev_p_bear?: number | null;
  exit_threshold?: number;
  ma_reclaimed?: boolean | null;
  ma_window_days?: number;
}

/** iter-30 (J-89): one fenced retrospective smoothed-P(bear) point (full-sample / analysis-only). */
export interface MarketPhaseSmoothedPoint {
  date: string;
  p_bear_smoothed: number; // lookahead by construction — analysis-only, never an as-of value
}

/** iter-30 (J-89): one peak-to-trough true-bear phase (retrospective / Bry-Boschan-NBER-style). */
export interface MarketPhaseTrueBearEpisode {
  peak_date: string;
  trough_date: string;
  peak_close: number;
  trough_close: number;
  drawdown_pct: number;
  duration_days: number;
}

/** iter-30 (J-89): the FENCED retrospective sub-view payload (only served with `?retrospective=true`). The
 *  SMOOTHED series + true-bear dating are future-aware (analysis-only) — they NEVER feed any as-of value. */
export interface MarketPhaseRetrospective {
  asof_date: string;
  available: boolean;
  analysis_only: boolean; // always true — the structural fence disclosure
  smoothed: MarketPhaseSmoothedPoint[];
  total_smoothed_dates?: number;
  true_bear_episodes: MarketPhaseTrueBearEpisode[];
  min_history_bars: number;
  min_phase_days: number;
  min_amplitude_pct: number;
}

export interface MarketPhaseResponse {
  asof_date: string;
  available: boolean;
  phase: string | null;
  severity: number | null;
  p_bear: number | null;
  drawdown_pct: number | null;
  off_trough_pct: number | null;
  components: MarketPhaseComponent[];
  vix_level?: MarketPhaseVixLevel;
  observations: MarketPhaseObservation[]; // the disclosed most-recent tail (the filter consumed all <= D)
  total_observations?: number; // the FULL causal observation count (>= observations.length)
  min_history_bars: number;
  labels: string[];
  // iter-30 (J-89 / J-90) additive CAUSAL fields (read from the SAME single derived series)
  timeline?: MarketPhaseTimelinePoint[]; // the per-date step-function series (bounded disclosure tail)
  total_timeline_dates?: number; // the FULL causal timeline-date count (>= timeline.length)
  episodes?: MarketPhaseEpisode[]; // the dated causal downtrend episodes
  recovery_turn?: MarketPhaseRecoveryTurn; // the causal recovery/turn signal for the resolved as-of
  // iter-38 (J-97): the FULL-history causal timeline series — present ONLY when fetched with full=true (the
  // SAME series the bounded `timeline` tail is sliced from; read VERBATIM from the same cached derivation,
  // no recompute). Each point is the causal {date, phase, p_bear, severity} — never the smoothed value. The
  // Dashboard two-pane cross-view chart reads THIS for its phase bands + severity + filtered P(bear) lines.
  timeline_full?: MarketPhaseTimelinePoint[];
  // the FENCED retrospective — present ONLY when fetched with retrospective=true (a sibling cached read)
  retrospective?: MarketPhaseRetrospective;
}

/** The Market Phase & Severity layer for the dashboard panel (J-87 + J-88 + J-89 + J-90). `asof` re-points
 *  it to a historical date (the single global as-of); the latest view passes nothing. `retrospective=true`
 *  ADDITIVELY requests the fenced full-sample / analysis-only sub-view (the SMOOTHED series + true-bear
 *  dating — lookahead by construction, never an as-of value). `full=true` (J-97) ADDITIVELY requests the
 *  full-history causal `timeline_full` series for the Dashboard two-pane cross-view chart (read verbatim
 *  from the SAME cached derivation, no recompute, no new endpoint — the `/api/indexes?full=true` precedent);
 *  the default card payload stays byte-identical. The frontend only re-formats these server-computed values
 *  — it never recomputes a phase / severity / probability / signal. */
export async function fetchMarketPhase(
  asof?: string,
  signal?: AbortSignal,
  retrospective?: boolean,
  full?: boolean,
): Promise<MarketPhaseResponse> {
  let base = "/api/market-phase";
  const params: string[] = [];
  if (retrospective) params.push("retrospective=true");
  if (full) params.push("full=true");
  if (params.length > 0) base += `?${params.join("&")}`;
  return getJSON<MarketPhaseResponse>(withAsOf(base, asof), signal);
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
  // iter-23 (J-81): the five realized forward returns (1/5/10/20/60-day from config horizons) — the
  // EQUAL-WEIGHT mean of the theme's member stocks' stored returns over only members that HAVE a stored
  // return, read VERBATIM via the SAME _leadership_returns builder Backtest's Top Themes uses (never
  // recomputed). `return` is null (NA) where no member has a stored return (or at/near latest). Config order.
  forward_returns: ForwardReturnEntry[];
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

// --- forward-tested evidence aggregate (iter-6; relocated onto Backtest in iter-17) ---------
/** One row of a grouped forward-return breakdown: the mean realized return (a fraction, e.g. 0.0123
 *  = +1.23%) and the sample size `n`. `mean_return` is null for a padded empty group (n === 0).
 *  Re-formatted only — the page never recomputes a return. */
export interface ForwardGroupRow {
  mean_return: number | null;
  // iter-27 (J-86): the aggregate mean max-drawdown beside the return stat (read-only over the stored
  // values; <= 0 or null/NA). Present on the grouped Backtest aggregate rows (by_bucket/setup/regime/vcp/
  // overall). Optional because some rows that share this base shape (e.g. control-group cohorts) do not
  // carry it.
  mean_max_drawdown?: number | null;
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

/** The as-of-scoped forward-tested evidence aggregate (Data Contract: app.engine.forward_testing) — the
 *  SINGLE canonical forward-return aggregation over an EXPANDING WINDOW of snapshots dated <= the
 *  resolved global as-of date. Served per horizon inside the `/api/backtest` payload (iter-17 relocated
 *  it off the retired System Health page, so the evidence has exactly one home). Every figure carries its
 *  sample size `n`; the page re-formats only and recomputes no return/excess/bucket. */
export interface EvidenceAggregate {
  horizon: number; // the forward window this aggregate is computed for (trading days)
  horizons: number[]; // valid horizons (from config — not hard-coded in the UI)
  default_horizon: number;
  min_sample: number; // figures with n below this are flagged low-sample
  survivorship_bias: string; // honest caveat, rendered verbatim
  n_runs: number; // walk-forward snapshots (dated <= D) contributing evidence at this horizon
  asof_dates: string[]; // the contributing as-of dates (descending) — all <= the resolved as-of date
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
  max_drawdown?: number | null; // iter-27 (J-86): the ETF's OWN stored drawdown at the horizon (<= 0 / NA)
}
/** One Top-Themes row's realized forward return = the equal-weight mean of its members' stored returns
 *  at the horizon. `slug` is the join key onto a `/api/themes` row (`row.slug`). */
export interface LeadershipThemeReturn extends ForwardGroupRow {
  slug: string; // theme slug (join key = /api/themes row.slug)
  max_drawdown?: number | null; // iter-27 (J-86): equal-weight member-basket stored drawdown (<= 0 / NA)
}
/** One Ranked-Cohort row's realized forward return = the stock's OWN stored return at the horizon.
 *  `ticker` is the join key onto a `/api/stocks` row (`row.ticker`). */
export interface LeadershipCohortReturn extends ForwardGroupRow {
  ticker: string; // universe ticker (join key = /api/stocks row.ticker)
  max_drawdown?: number | null; // iter-27 (J-86): the cohort symbol's OWN stored drawdown (<= 0 / NA)
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
  // iter-17 (J-09/J-10): the as-of-scoped forward-tested evidence aggregate, keyed by horizon (every
  // config horizon), all in this one payload so the client-side horizon selector needs no refetch. Each
  // entry is scoped to the EXPANDING WINDOW of snapshots dated <= `asof_date` (relocated off System Health).
  evidence_by_horizon: Record<number, EvidenceAggregate>;
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

// --- watchlist concentration X-ray (iter-38, J-23 / backlog B-204) --------------------------
/** One sector's share of the watchlist. `sector` is nullable (a stock with no mapped GICS sector) —
 *  render its label via the EXISTING `sectorLabel()` helper (`lib/sector-label.ts`, the ONE place
 *  that maps null -> "Unassigned"), never a second null-handling rule. Single-valued: `pct` sums to
 *  1.0 across every returned entry. */
export interface WatchlistXraySectorConcentration {
  sector: string | null;
  count: number;
  pct: number;
}

/** One theme's share of the watchlist. Multi-valued (a stock may carry several themes, or none) —
 *  `pct` is share-of-watchlist, NOT a partition (entries need not sum to 1.0). Only themes with >= 1
 *  watchlist member are listed. */
export interface WatchlistXrayThemeConcentration {
  slug: string;
  name: string;
  count: number;
  pct: number;
}

/** One setup status's share of the watchlist — always all six canonical statuses (0 where absent),
 *  mirroring the dashboard's own `summarize_candidates` "a number always renders" contract. */
export interface WatchlistXraySetupConcentration {
  status: string;
  count: number;
  pct: number;
}

/** GET /api/watchlist's additive `xray` field (B-204): the watchlist concentration X-ray, computed
 *  ONCE engine-side by `app.engine.watchlist_xray.build_xray_payload` and re-read VERBATIM here — NO
 *  browser-side correlation/ENB recompute (B-204's named dominant failure mode). `status ===
 *  "insufficient"` (fewer than 2 watchlist names) means every list/matrix field below is empty; the
 *  page renders a distinct "not enough names yet" state rather than an empty matrix. A `null`
 *  `correlation_matrix[a][b]` cell is an HONEST NA (undefined pairwise correlation — insufficient own
 *  history, missing bars, or zero-variance series), never a fabricated 0. `effective_number_of_bets`
 *  is `null` only when NO member has enough usable history to compute it at all. */
export interface WatchlistXray {
  status: "ok" | "insufficient";
  window_days: number; // the trailing correlation window (config watchlist.xray.corr_window_days)
  min_overlap_days: number; // the honesty floor below which a member's row/column is NA throughout
  cluster_threshold: number; // the Pearson correlation at/above which two members join a cluster
  tickers: string[]; // every watchlist ticker, sorted — the matrix's row/column vocabulary
  history_days: Record<string, number>; // observed own-history length per ticker, capped at window_days
  correlation_matrix: Record<string, Record<string, number | null>>;
  clusters: string[][]; // deterministic connected components; a lone name is its own singleton cluster
  effective_number_of_bets: number | null;
  enb_member_count: number; // how many members contributed to the ENB computation
  sector_concentration: WatchlistXraySectorConcentration[];
  theme_concentration: WatchlistXrayThemeConcentration[];
  setup_concentration: WatchlistXraySetupConcentration[];
}

export interface WatchlistResponse {
  asof_date: string;
  entries: WatchlistEntry[];
  xray: WatchlistXray;
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

/** The Universe Selection section (J-22 / J-93) — the config-recorded screen that defines membership. The
 *  `membership_rule` prose + the three screen `thresholds` (resolved LIVE from `universe.filters` on the
 *  backend, so they always match the offline screen) + the `resolved_size` read from the ONE canonical
 *  universe (the same value GET /api/data reports as `candidate_universe_count`). J-93 additionally serves
 *  the per-as-of-date membership rule: `per_date_rule` is the prose for the per-date resolver (the same
 *  candidate pool screened from bars ≤ D only on price + ADV + `per_date_min_history_bars` trailing bars,
 *  market-cap dropped per-date), `candidate_pool_size` is the full candidate-pool denominator, and
 *  `per_date_min_history_bars` is the warm-up bar count. All three are produced by the single canonical
 *  module `methodology._universe_selection` and served by the single `GET /api/methodology`; the frontend
 *  re-formats them only — it never recomputes membership. */
export interface UniverseSelection {
  membership_rule: string;
  thresholds: MethodologyThresholdRow[];
  resolved_size: number;
  candidate_pool_size: number;
  per_date_rule: string;
  per_date_min_history_bars: number;
}

/** One glossary term (iter-4 goal-mode, J-47). `term` is the LITERAL UI string (the tooltip/lookup
 *  key, e.g. "rank-IC"); `definition` is the plain-language explanation; `where` optionally notes where
 *  it appears; `thresholds` optionally cite config thresholds (resolved live on the backend, never
 *  re-typed). Setup/pattern rows additionally carry `entry_key`/`kind` linking to the full catalog entry. */
export interface GlossaryTerm {
  term: string;
  category: string;
  definition: string;
  where?: string;
  thresholds?: MethodologyThresholdRow[];
  entry_key?: string;
  kind?: "setup" | "pattern";
}

/** One glossary category (iter-4 goal-mode, J-47) — an ordered group of terms. `key` is the stable id,
 *  `label` the display heading; `terms` are the category's terms in catalog order. */
export interface GlossaryCategory {
  key: string;
  label: string;
  terms: GlossaryTerm[];
}

/** The J-47 terminology glossary served on the SAME GET /api/methodology payload — categorized terms in
 *  catalog order. The /methodology Glossary page and every inline info-tooltip read THESE entries. */
export interface MethodologyGlossary {
  categories: GlossaryCategory[];
}

/** The config-backed Setup & Pattern catalog served by GET /api/methodology. The ONE source for the
 *  /methodology page, the /stocks badge tooltips, the /stocks setup-filter vocabulary, AND (J-47) the
 *  full terminology glossary + every inline term tooltip. `universe_selection` (J-22) carries the
 *  Universe Selection section when configured; `glossary` (J-47) carries the categorized term list. */
export interface MethodologyCatalog {
  intro?: string;
  universe_selection?: UniverseSelection;
  entries: MethodologyEntry[];
  glossary?: MethodologyGlossary;
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
  mean_max_drawdown: number | null; // iter-52 (J-109): paired mean max-drawdown (fraction, <= 0); null = NA
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
  asof_date?: string | null; // J-32: the resolved point-in-time cutoff (ISO) when scoped; null = all-history
}

/** Canonical Factor-Lab source: GET /api/research/factor-lab?factor=&horizon=. Throws on non-200 so the
 *  page renders an explicit "Backend unavailable" state (503 no data / 422 unknown factor or horizon /
 *  400 future as-of) — never fabricated evidence. All params optional (defaults: first catalog factor /
 *  config default horizon). `asof` (J-32) is the single global as-of cutoff — appended via `withAsOf`
 *  ONLY when a historical cutoff is active (As-of mode + a past date); omitted = all-history. */
export async function fetchFactorLab(
  factor?: string,
  horizon?: number,
  asof?: string,
  signal?: AbortSignal,
): Promise<FactorLabResponse> {
  const params = new URLSearchParams();
  if (factor) params.set("factor", factor);
  if (horizon !== undefined) params.set("horizon", String(horizon));
  const query = params.toString();
  const path = `/api/research/factor-lab${query ? `?${query}` : ""}`;
  return getJSON<FactorLabResponse>(withAsOf(path, asof), signal);
}

/** One factor's decile table at a SINGLE horizon (J-109): the served forward window + the per-decile rows
 *  (each pairing mean_return + mean_max_drawdown) + the horizon's observation count. One of these per
 *  config horizon rides inside `FactorTableRow.by_horizon`. Re-presented byte-identically from the
 *  single-horizon `compute_factor_lab(factor, horizon)` output — the page recomputes nothing. */
export interface FactorHorizonDeciles {
  horizon: number; // the forward window (trading days)
  n_total: number; // observations contributing at this horizon
  deciles: FactorDecileRow[]; // D1…D10 (config-driven count) — paired return + max-drawdown
}

/** One all-factors table row (J-107 → J-109): a config-catalog factor's family + Spearman rank-IC (value +
 *  n) + the downside `risk_adjusted` figure (the factor's OWN top-decile risk_adjusted) — ALL at the FIXED
 *  default horizon — PLUS a `by_horizon` block carrying that factor's full decile table at EVERY config
 *  horizon (each decile pairing mean forward-return + mean max-drawdown), revealed when the row is expanded.
 *  Every figure is a re-presentation of the canonical `compute_factor_lab` output — byte-identical per
 *  (factor, horizon, decile); the page recomputes nothing. */
export interface FactorTableRow {
  key: string;
  label: string;
  family: string;
  direction: string; // higher_better | lower_better (descriptive)
  n_total: number; // observations at the default horizon (== rank_ic.n)
  rank_ic: RankIC; // Spearman rank-IC at the default horizon; value null = NA
  risk_adjusted: number | null; // top-decile downside risk-adjusted at the default horizon; null = NA
  by_horizon: FactorHorizonDeciles[]; // one decile table per config horizon — hidden until the row expands
}

/** GET /api/research/factor-lab?all=true payload (J-107 → J-109) — the ALL-FACTORS, ALL-HORIZONS view: one
 *  entry per config catalog factor, each carrying the rank-IC + downside risk-adjusted at the fixed default
 *  horizon PLUS a per-horizon decile table (paired forward-return + max-drawdown) for every config horizon.
 *  Every figure is byte-identical to the single-factor `FactorLabResponse` at the same horizon. The page
 *  re-formats + client-side sorts (NA-last) only — it recomputes no return/factor. The As-of toggle is the
 *  single global as-of (no second date state, J-18); there is no horizon selector (all horizons shown). */
export interface FactorLabAllResponse {
  factors: FactorLabFactor[]; // the config-driven catalog (reference / family vocabulary)
  horizons: number[]; // every config horizon shown as paired columns (config-driven — not hard-coded)
  default_horizon: number; // the fixed horizon the rank-IC / risk-adjusted are labelled with
  deciles_count: number;
  min_sample: number; // factors/deciles with n below this are NA/low-sample
  survivorship_bias: string; // honest caveat, rendered verbatim
  descriptive_caveat: string; // "descriptive, not predictive / universe-relative", rendered verbatim
  factors_table: FactorTableRow[]; // one row per catalog factor (in catalog order)
  asof_date?: string | null; // J-32: the resolved point-in-time cutoff (ISO) when scoped; null = all-history
}

/** Canonical all-factors, all-horizons Factor-Lab source: GET /api/research/factor-lab?all=true. Throws on
 *  non-200 so the page renders an explicit "Backend unavailable" state (503 no data / 400 future as-of) —
 *  never fabricated evidence. The view is horizon-independent (it shows every horizon at once), so no
 *  `horizon` param is sent. `asof` (J-32) is the single global as-of cutoff, appended via `withAsOf` ONLY
 *  when a historical cutoff is active (As-of mode + a past date); omitted = all-history. */
export async function fetchFactorLabAll(
  asof?: string,
  signal?: AbortSignal,
): Promise<FactorLabAllResponse> {
  return getJSON<FactorLabAllResponse>(withAsOf("/api/research/factor-lab?all=true", asof), signal);
}

// --- research / Regime Lab (iter-53, J-110) ------------------------------------------------
/** One regime-LABEL or regime-score-DECILE bucket's paired figures at ONE horizon: the mean realized
 *  forward return + paired mean max-drawdown + sample size `n`. `low_sample` (n < min_sample) flags the
 *  cell the UI renders as NA + n. Re-formatted only — the page recomputes no return/drawdown. */
export interface RegimeLabHorizonCell {
  horizon: number; // the forward window (trading days)
  n: number;
  low_sample: boolean; // n < min_sample — render NA + n, never a fabricated number
  mean_return: number | null; // raw mean forward return (fraction); null when n === 0
  mean_max_drawdown: number | null; // paired mean max-drawdown (fraction, <= 0); null = NA (none stored)
}

/** A regime-score DECILE bucket's per-horizon cell additionally carries the decile's regime-score range. */
export interface RegimeLabDecileHorizonCell extends RegimeLabHorizonCell {
  score_min: number | null; // the decile's lowest regime score (0–100); null when empty
  score_max: number | null; // the decile's highest regime score (0–100); null when empty
}

/** One by-LABEL row: a configured regime label + its paired figures at every config horizon. */
export interface RegimeLabLabelRow {
  regime: string; // a config.regime.labels value (verbatim — server-driven, not hard-coded in the UI)
  by_horizon: RegimeLabHorizonCell[];
}

/** One by-DECILE row: a 1..deciles bucket of the 0–100 regime score + its paired figures + score range. */
export interface RegimeLabDecileRow {
  decile: number; // 1..deciles_count
  by_horizon: RegimeLabDecileHorizonCell[];
}

/** The decile table's header rank-IC of the regime score vs the realized forward return, per horizon. */
export interface RegimeLabRankIcRow {
  horizon: number;
  rank_ic: RankIC; // value null = NA (n < 2 or zero rank variance) — never a fabricated 0
}

/** GET /api/research/regime-lab payload (J-110) — cross-sectional realized forward returns + paired
 *  max-drawdowns grouped (a) by the six canonical regime labels and (b) into deciles of the 0–100 regime
 *  score, at EVERY config horizon at once (paired columns), with the per-horizon rank-IC of the regime
 *  score vs the forward return. Every figure is derived once from stored values (read VERBATIM); the page
 *  re-formats + client-side sorts (NA-last) only — it recomputes no return/regime/drawdown. The As-of toggle
 *  is the single global as-of (no second date state, J-18); there is no horizon selector (all horizons). */
export interface RegimeLabResponse {
  view: "episodes" | "pooled"; // the resolved overlap-honesty view
  horizons: number[]; // every config horizon shown as paired columns (config-driven — not hard-coded)
  default_horizon: number; // the horizon the rank-IC column header is labelled with
  deciles_count: number;
  min_sample: number; // buckets with n below this are NA/low-sample
  regime_labels: string[]; // the by-label row vocabulary (config-driven — not hard-coded in the UI)
  survivorship_bias: string; // honest caveat, rendered verbatim
  descriptive_caveat: string; // "descriptive, not predictive / universe-relative", rendered verbatim
  by_label: RegimeLabLabelRow[]; // one row per configured regime label (in config order)
  by_decile: RegimeLabDecileRow[]; // D1..D`deciles` of the regime score
  rank_ic_by_horizon: RegimeLabRankIcRow[]; // regime score vs forward return, per horizon
  asof_date?: string | null; // J-32: the resolved point-in-time cutoff (ISO) when scoped; null = all-history
}

/** Canonical Regime-Lab source: GET /api/research/regime-lab. Throws on non-200 so the page renders an
 *  explicit "Backend unavailable" state (503 no data / 422 bad view / 400 future as-of) — never fabricated
 *  evidence. The view is horizon-independent (it shows every horizon at once), so no `horizon` param is sent.
 *  `asof` (J-32) is the single global as-of cutoff, appended via `withAsOf` ONLY when a historical cutoff is
 *  active (As-of mode + a past date); omitted = all-history. */
export async function fetchRegimeLab(
  view?: "episodes" | "pooled",
  asof?: string,
  signal?: AbortSignal,
): Promise<RegimeLabResponse> {
  const params = new URLSearchParams();
  if (view) params.set("view", view);
  const query = params.toString();
  const path = `/api/research/regime-lab${query ? `?${query}` : ""}`;
  return getJSON<RegimeLabResponse>(withAsOf(path, asof), signal);
}

// --- research / Market Phase & Severity Lab (iter-54, J-111) --------------------------------
/** One by-PHASE-LABEL row: a configured market-phase label + its paired figures at every config horizon. The
 *  per-horizon cell shape (mean_return + paired mean_max_drawdown + n + low_sample) is identical to the Regime
 *  Lab's, so the cell type is reused; the decile cell additionally carries the severity-score range. */
export interface PhaseSeverityLabLabelRow {
  phase: string; // a config.market_phase.labels value (verbatim — server-driven, not hard-coded in the UI)
  by_horizon: RegimeLabHorizonCell[];
}

/** One by-DECILE row: a 1..deciles bucket of the 0–100 severity score + its paired figures + score range. */
export interface PhaseSeverityLabDecileRow {
  decile: number; // 1..deciles_count
  by_horizon: RegimeLabDecileHorizonCell[]; // score_min/score_max are the severity-score bounds here
}

/** GET /api/research/phase-severity-lab payload (J-111) — the structural twin of the Regime Lab:
 *  cross-sectional realized forward returns + paired max-drawdowns grouped (a) by the five canonical
 *  market-phase labels and (b) into deciles of the 0–100 severity score, at EVERY config horizon at once
 *  (paired columns), with the per-horizon rank-IC of the severity score vs the forward return. The grouping
 *  subject (phase label + severity LEVEL) is read VERBATIM from the served `market_phase` causal timeline,
 *  joined by snapshot date. Every figure is derived once from stored values (read VERBATIM); the page
 *  re-formats + client-side sorts (NA-last) only. The As-of toggle is the single global as-of (no second date
 *  state, J-18); there is no horizon selector (all horizons). */
export interface PhaseSeverityLabResponse {
  view: "episodes" | "pooled"; // the resolved overlap-honesty view
  horizons: number[]; // every config horizon shown as paired columns (config-driven — not hard-coded)
  default_horizon: number; // the horizon the rank-IC column header is labelled with
  deciles_count: number;
  min_sample: number; // buckets with n below this are NA/low-sample
  phase_labels: string[]; // the by-label row vocabulary (config-driven — not hard-coded in the UI)
  survivorship_bias: string; // honest caveat, rendered verbatim
  descriptive_caveat: string; // "descriptive, not predictive / universe-relative", rendered verbatim
  by_label: PhaseSeverityLabLabelRow[]; // one row per configured market-phase label (in config order)
  by_decile: PhaseSeverityLabDecileRow[]; // D1..D`deciles` of the severity score
  rank_ic_by_horizon: RegimeLabRankIcRow[]; // severity score vs forward return, per horizon
  asof_date?: string | null; // J-32: the resolved point-in-time cutoff (ISO) when scoped; null = all-history
}

/** Canonical Phase & Severity-Lab source: GET /api/research/phase-severity-lab. Throws on non-200 so the page
 *  renders an explicit "Backend unavailable" state (503 no data / 422 bad view / 400 future as-of) — never
 *  fabricated evidence. The view is horizon-independent (every horizon at once), so no `horizon` param is sent.
 *  `asof` (J-32) is the single global as-of cutoff, appended via `withAsOf` ONLY when a historical cutoff is
 *  active (As-of mode + a past date); omitted = all-history. */
export async function fetchPhaseSeverityLab(
  view?: "episodes" | "pooled",
  asof?: string,
  signal?: AbortSignal,
): Promise<PhaseSeverityLabResponse> {
  const params = new URLSearchParams();
  if (view) params.set("view", view);
  const query = params.toString();
  const path = `/api/research/phase-severity-lab${query ? `?${query}` : ""}`;
  return getJSON<PhaseSeverityLabResponse>(withAsOf(path, asof), signal);
}

// --- research / Regime × Phase × Factor 3-way decile study (iter-55, J-112) ------------------
/** One `(regime-score decile, severity-score decile, factor decile)` combination row of the J-112 study: the
 *  three decile coordinates + a per-config-horizon paired (mean forward-return, mean max-drawdown) cell list.
 *  The per-horizon cell shape (mean_return + paired mean_max_drawdown + n + low_sample) is identical to the
 *  Regime / Phase-Severity Lab cell, so that cell type is reused; the page re-formats + client-side sorts /
 *  filters / paginates only — it recomputes nothing. */
export interface RegimePhaseFactorRow {
  regime_decile: number; // 1..deciles_count
  severity_decile: number; // 1..deciles_count
  factor_decile: number; // 1..deciles_count
  by_horizon: RegimeLabHorizonCell[];
}

/** GET /api/research/regime-phase-factor payload (J-112) — for a SELECTED factor, a ranked combination table
 *  of `(regime-score decile × severity-score decile × factor decile)` triples, each row carrying per EVERY
 *  config horizon at once (paired columns — no horizon selector) the combination's mean realized forward
 *  return + paired mean max-drawdown + n. The three grouping dimensions are read VERBATIM from their single
 *  canonical sources (stored regime score / served severity / stored factor value) — derived once, never
 *  recomputed. The page re-formats + client-side sorts (NA-last) / filters / paginates only. The As-of toggle
 *  is the single global as-of (no second date state, J-18); there is no horizon selector (all horizons). */
export interface RegimePhaseFactorResponse {
  view: "episodes" | "pooled"; // the resolved overlap-honesty view (the page pins pooled)
  factor: FactorLabFactor; // the selected factor (resolved from the config catalog)
  factors: FactorLabFactor[]; // the config-driven factor catalog (the factor selector vocabulary)
  horizons: number[]; // every config horizon shown as paired columns (config-driven — not hard-coded)
  default_horizon: number; // the horizon the default ranking is on
  deciles_count: number;
  min_sample: number; // combinations with n below this are NA/low-sample
  page_size: number; // config-driven rows-per-page for the client-side pagination (no UI literal)
  survivorship_bias: string; // honest caveat, rendered verbatim
  descriptive_caveat: string; // "descriptive, not predictive / universe-relative", rendered verbatim
  rows: RegimePhaseFactorRow[]; // one row per emitted combination, server-ranked by default-horizon return
  asof_date?: string | null; // J-32: the resolved point-in-time cutoff (ISO) when scoped; null = all-history
}

/** Canonical Regime × Phase × Factor source: GET /api/research/regime-phase-factor. Throws on non-200 so the
 *  page renders an explicit "Backend unavailable" state (503 no data / 422 bad factor|view / 400 future as-of)
 *  — never fabricated evidence. The view is horizon-independent (every horizon at once), so no `horizon` param
 *  is sent. `factor` selects the studied factor (config catalog key); `asof` (J-32) is the single global as-of
 *  cutoff, appended via `withAsOf` ONLY when a historical cutoff is active; omitted = all-history. */
export async function fetchRegimePhaseFactor(
  factor?: string,
  view?: "episodes" | "pooled",
  asof?: string,
  signal?: AbortSignal,
): Promise<RegimePhaseFactorResponse> {
  const params = new URLSearchParams();
  if (factor) params.set("factor", factor);
  if (view) params.set("view", view);
  const query = params.toString();
  const path = `/api/research/regime-phase-factor${query ? `?${query}` : ""}`;
  return getJSON<RegimePhaseFactorResponse>(withAsOf(path, asof), signal);
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

/** A combination cohort (baseline / composite rank-blend / strict-overlap): a server-built `label` +
 *  its `stats`. The label is rendered verbatim — the UI never invents the cohort name. */
export interface FactorCombinationCohort {
  label: string;
  stats: CohortStats;
}

/** The echoed composite-blend weighting scheme (iter-18) — config-driven, so the UI labels the blend
 *  honestly (e.g. "equal-weight"). `scheme` is the config-declared scheme (currently "equal"); the UI
 *  re-formats it only and never computes a weight. */
export interface CompositeWeighting {
  scheme: string; // config-declared blend scheme (e.g. "equal"), rendered verbatim
  default_weight: number; // per-condition base weight the backend normalized (descriptive)
}

/** One single-factor cohort: the resolved `condition` (for the row label) + its `stats`. */
export interface FactorCombinationSingle {
  condition: FactorCombinationCondition;
  stats: CohortStats;
}

/** GET /api/research/factor-combination payload (J-26, iter-18 re-scoped) — the SINGLE canonical
 *  multi-factor combination analysis: the HEADLINE `composite` rank-blend cohort + the SECONDARY
 *  `strict_overlap` (exact AND-intersection) cohort vs the unconditional `baseline` vs each single-factor
 *  cohort, each with mean / median forward return, hit-rate, downside-risk-adjusted, and n. The composite
 *  is the top config-quantile of the pool by a config-weighted blend of the conditions' oriented percentile
 *  ranks of the STORED factor values — a deterministic ranking/grouping (like the J-25 decile sort), NOT a
 *  fitted/ML model. Every figure is derived once from the SAME stored pool the Factor Lab reads; the page
 *  re-formats only and recomputes no return/factor/cohort. A cross-date aggregate (like the Factor Lab) —
 *  there is NO as-of/date control (J-18). `factors`/`quantiles` are the config-driven dropdown
 *  vocabularies; `composite_quantile`/`weighting` are echoed so the blend's labelling stays config-driven
 *  (no hard-coded list/number in the UI). */
export interface FactorCombinationResponse {
  conditions: FactorCombinationCondition[]; // the resolved requested combination
  horizon: number; // the served forward window (trading days)
  horizons: number[]; // valid horizons (from config — not hard-coded in the UI)
  default_horizon: number;
  min_sample: number; // cohorts with n below this are flagged low-sample (render NA + n)
  min_conditions: number; // condition-count bounds (from config) — drive add/remove enablement
  max_conditions: number; // raised to the catalog factor count — combine UP TO all factors
  factors: FactorLabFactor[]; // the config-driven factor catalog (the Factor dropdown vocabulary)
  quantiles: QuantileOption[]; // the config-driven quantile vocabulary (the Quantile dropdown)
  composite_quantile: QuantileOption; // the resolved composite cohort fraction (echoed from config)
  weighting: CompositeWeighting; // the echoed composite blend weighting (config-driven label)
  survivorship_bias: string; // honest caveat, rendered verbatim
  descriptive_caveat: string; // "descriptive, not predictive", rendered verbatim
  pool_n: number; // the multi-factor observation pool size (all referenced factors non-null)
  baseline: FactorCombinationCohort; // the unconditional all-names cohort
  singles: FactorCombinationSingle[]; // one cohort per condition
  composite: FactorCombinationCohort; // HEADLINE: the composite percentile-rank-blend cohort (non-empty)
  strict_overlap: FactorCombinationCohort; // SECONDARY: the exact AND-intersection (NA + n when empty)
  asof_date?: string | null; // J-32: the resolved point-in-time cutoff (ISO) when scoped; null = all-history
}

/** Canonical multi-factor combination source: GET /api/research/factor-combination. Builds repeated
 *  `condition=<factor>:<side>:<quantile>` query params + an optional `horizon`. Throws on non-200 so the
 *  page renders an explicit "Backend unavailable" state (503 no data / 422 bad factor/side/quantile/count/
 *  horizon) — never fabricated cohorts. With no conditions the backend serves its config default_conditions. */
export async function fetchFactorCombination(
  conditions: { factor: string; side: string; quantile: string }[],
  horizon?: number,
  asof?: string,
  signal?: AbortSignal,
): Promise<FactorCombinationResponse> {
  const params = new URLSearchParams();
  for (const c of conditions) {
    params.append("condition", `${c.factor}:${c.side}:${c.quantile}`);
  }
  if (horizon !== undefined) params.set("horizon", String(horizon));
  const query = params.toString();
  // `asof` (J-32) is appended via `withAsOf` only when a historical cutoff is active (As-of mode + a past date)
  const path = `/api/research/factor-combination${query ? `?${query}` : ""}`;
  return getJSON<FactorCombinationResponse>(withAsOf(path, asof), signal);
}

// --- research / setup & pattern event study (iter-14, J-29) --------------------------------
/** One event-study subject (the dropdown vocabulary, config-driven on the backend — NOT a hard-coded
 *  frontend list): a setup status (`kind:"setup"`) or a detected pattern (`kind:"pattern"`). The
 *  frontend renders `label` and selects by `key`; the selector groups by `kind`. */
export interface EventStudySubject {
  key: string;
  label: string;
  kind: "setup" | "pattern";
}

/** The per-occurrence expectancy decomposition over the subject cohort: `win_rate` (fraction `> 0`),
 *  `avg_win` (mean of winning returns; null = no win), `avg_loss` (mean of losing returns, negative;
 *  null = no loss), and `expectancy` (= win_rate*avg_win + (1−win_rate)*avg_loss, which equals the
 *  mean). All null for an empty cohort (NA, never a fabricated 0). Re-formatted only. */
export interface EventStudyExpectancy {
  win_rate: number | null;
  avg_win: number | null;
  avg_loss: number | null;
  expectancy: number | null;
}

/** One per-horizon row of the event study: the forward-return distribution (mean / median / %positive
 *  / dispersion), the expectancy decomposition, the mean stored MAE / MFE excursions, and BOTH
 *  downside-only risk-adjusted ratios (return/downside-dev and return/mean-|MAE| — never total vol),
 *  with `n` and `low_sample` (n < min_sample → render NA + n). Re-formatted from stored values only. */
export interface EventStudyHorizonRow {
  horizon: number;
  n: number;
  low_sample: boolean;
  mean_return: number | null;
  median: number | null;
  pct_positive: number | null;
  dispersion: number | null;
  expectancy: EventStudyExpectancy;
  mean_mae: number | null; // mean max-adverse excursion (fraction, <= ~0); null = NA
  mean_mfe: number | null; // mean max-favorable excursion (fraction, >= ~0); null = NA
  mean_max_drawdown: number | null; // iter-27 (J-86): mean max-drawdown (fraction, <= 0); null = NA
  return_per_downside_dev: number | null; // mean / downside-deviation; null = NA (no downside / n<2)
  return_per_mae: number | null; // mean / mean-|MAE|; null = NA (no adverse excursion / n<2)
}

/** One by-regime slice row (selected horizon): per configured regime label, the per-regime n,
 *  mean_return, hit_rate (fraction `> 0`), and downside risk_adjusted. `low_sample`/null cells render
 *  NA + n; the regime list is SERVER-driven (config.regime.labels) — not a hard-coded frontend list. */
export interface EventStudyRegimeRow {
  regime: string;
  n: number;
  low_sample: boolean;
  mean_return: number | null;
  hit_rate: number | null;
  risk_adjusted: number | null;
}

/** One by-sector slice row (selected horizon): per stored sector with members, the per-sector n,
 *  mean_return, and downside risk_adjusted. Non-padded (only sectors with members appear); low-sample
 *  cells render NA + n. */
export interface EventStudySectorRow {
  sector: string;
  n: number;
  low_sample: boolean;
  mean_return: number | null;
  risk_adjusted: number | null;
}

/** GET /api/research/event-study payload (J-29) — the SINGLE canonical Setup & Pattern event study for
 *  one subject × horizon. Every figure is derived once from the stored forward returns + the stored
 *  MAE/MFE excursions; the page re-formats only and recomputes no return/excursion. A cross-date
 *  aggregate (like the Factor Lab) — there is NO as-of/date control (J-18). `subjects` is the
 *  config-driven dropdown vocabulary (no hard-coded list in the UI). */
export interface EventStudyResponse {
  subject: EventStudySubject; // the resolved subject
  horizon: number; // the selected forward window (drives the by-regime/by-sector slices)
  subjects: EventStudySubject[]; // the config-driven subject catalog (setups + patterns)
  horizons: number[]; // valid horizons for the selector (from config — not hard-coded in the UI)
  default_horizon: number;
  min_sample: number; // figures with n below this are flagged low-sample (render NA + n)
  survivorship_bias: string; // honest caveat, rendered verbatim
  descriptive_caveat: string; // "descriptive, not predictive", rendered verbatim
  n_total: number; // pooled observations at the selected horizon (== `n` in the current view)
  // J-63 overlap-honesty: the resolved view + the three disclosure values (present in BOTH views)
  view: "episodes" | "pooled"; // the resolved overlap-honesty view (episodes default | pooled)
  n: number; // observations in the CURRENT view at the selected horizon (== n_total)
  unique_symbols: number; // distinct tickers in the current view's observation set
  episode_count: number; // distinct first-trigger episodes — IDENTICAL in both views
  by_horizon: EventStudyHorizonRow[]; // one row per configured horizon (the exit-horizon curve)
  best_exit_horizon: number | null; // argmax horizon of the primary metric among non-low-sample; null = NA
  by_regime: EventStudyRegimeRow[]; // per configured regime label at the selected horizon
  by_sector: EventStudySectorRow[]; // per stored sector with members at the selected horizon
  asof_date?: string | null; // J-32: the resolved point-in-time cutoff (ISO) when scoped; null = all-history
}

/** Canonical event-study source: GET /api/research/event-study?subject=&horizon=. Throws on non-200 so
 *  the page renders an explicit "Backend unavailable" state (503 no data / 422 unknown subject or
 *  horizon) — never fabricated evidence. Both params are optional (defaults: first catalog subject /
 *  config default horizon). */
export async function fetchEventStudy(
  subject?: string,
  horizon?: number,
  asof?: string,
  view?: "episodes" | "pooled",
  signal?: AbortSignal,
): Promise<EventStudyResponse> {
  const params = new URLSearchParams();
  if (subject) params.set("subject", subject);
  if (horizon !== undefined) params.set("horizon", String(horizon));
  // J-63: the overlap-honesty view (episodes default | pooled) — a cohort/mode selector, not a date.
  if (view !== undefined) params.set("view", view);
  const query = params.toString();
  // `asof` (J-32) is appended via `withAsOf` only when a historical cutoff is active (As-of mode + a past date)
  const path = `/api/research/event-study${query ? `?${query}` : ""}`;
  return getJSON<EventStudyResponse>(withAsOf(path, asof), signal);
}

// --- research / Regime × Setup × Pattern study (iter-20, J-77) --------------------------------
/** One (regime, setup, pattern) combination row's stats (J-77). Every figure derives from the SAME
 *  enriched event-study observation set; risk is downside-only (return ÷ downside-deviation AND
 *  return ÷ mean-|MAE| — never total volatility). `low_sample`/null cells render NA + n. */
export interface RegimeSetupPatternStats {
  n: number;
  low_sample: boolean;
  mean: number | null;
  median: number | null;
  pct_positive: number | null; // hit-rate (fraction > 0)
  expectancy: number | null;
  mean_max_drawdown: number | null; // iter-27 (J-86): mean max-drawdown (fraction, <= 0); null = NA
  return_per_downside_dev: number | null; // mean / downside-deviation; null = NA
  return_per_mae: number | null; // mean / mean-|MAE|; null = NA
}

/** One ranked combination row: a (regime, setup, pattern) key + its stats. `pattern` is a config pattern
 *  key OR the `pattern_none` sentinel (an observation with no flagged pattern). */
export interface RegimeSetupPatternRow {
  regime: string;
  setup: string;
  pattern: string;
  stats: RegimeSetupPatternStats;
}

/** GET /api/research/regime-setup-pattern payload (J-77) — the ranked Regime × Setup × Pattern study. A
 *  grouping of the SAME stored event-study observation set; the page re-formats only and recomputes
 *  nothing. Vocabularies (`regime_labels` / `setups` / `patterns`) are config-driven. */
export interface RegimeSetupPatternResponse {
  horizon: number;
  view: "episodes" | "pooled";
  horizons: number[];
  default_horizon: number;
  min_sample: number;
  regime_labels: string[];
  setups: string[];
  patterns: string[];
  pattern_none: string; // the "no pattern flagged" sentinel value
  survivorship_bias: string;
  descriptive_caveat: string;
  n_total: number;
  rows: RegimeSetupPatternRow[];
  asof_date?: string | null; // J-32: resolved cutoff (ISO) when scoped; null = all-history
}

/** Canonical Regime × Setup × Pattern source: GET /api/research/regime-setup-pattern. Throws on non-200
 *  so the page renders an explicit "Backend unavailable" state (503 no data / 422 bad horizon/view) —
 *  never fabricated evidence. Both params are optional (defaults: config default horizon / episodes). */
export async function fetchRegimeSetupPattern(
  horizon?: number,
  asof?: string,
  view?: "episodes" | "pooled",
  signal?: AbortSignal,
): Promise<RegimeSetupPatternResponse> {
  const params = new URLSearchParams();
  if (horizon !== undefined) params.set("horizon", String(horizon));
  if (view !== undefined) params.set("view", view);
  const query = params.toString();
  const path = `/api/research/regime-setup-pattern${query ? `?${query}` : ""}`;
  return getJSON<RegimeSetupPatternResponse>(withAsOf(path, asof), signal);
}

// --- research / Recovery-Turn Edge study (iter-30, J-90) --------------------------------------
/** One per-horizon row of the Recovery-Turn Edge study (J-90) — identical shape to the event-study row:
 *  the forward-return distribution + expectancy + mean MAE/MFE + aggregate max-drawdown + BOTH
 *  downside-only risk-adjusted ratios, with `n` + `low_sample`. Re-formatted from stored values only. */
export interface RecoveryTurnEdgeHorizonRow {
  horizon: number;
  n: number;
  low_sample: boolean;
  mean_return: number | null;
  median: number | null;
  pct_positive: number | null;
  dispersion: number | null;
  expectancy: EventStudyExpectancy;
  mean_mae: number | null;
  mean_mfe: number | null;
  mean_max_drawdown: number | null; // aggregate max-drawdown (fraction, <= 0); null = NA
  return_per_downside_dev: number | null;
  return_per_mae: number | null;
}

/** One by-signal-phase row (selected horizon): per configured market-phase label, the per-phase n,
 *  mean_return, hit_rate, and downside risk_adjusted — conditioning the recovery-turn edge on the causal
 *  phase at the signal date. The phase list is SERVER-driven (config.market_phase.labels). */
export interface RecoveryTurnEdgePhaseRow {
  phase: string;
  n: number;
  low_sample: boolean;
  mean_return: number | null;
  hit_rate: number | null;
  risk_adjusted: number | null;
}

/** GET /api/research/recovery-turn-edge payload (J-90) — the per-horizon forward-return edge of entering
 *  at CAUSAL recovery-turn signal dates, conditioned on the causal phase/severity/P(bear). Every figure is
 *  read VERBATIM from the stored forward returns; the page re-formats only (recomputes nothing). `as_of`
 *  (J-32) scopes the pool; `view` (J-63) is the overlap-honesty mode. No order/execution affordance. */
export interface RecoveryTurnEdgeResponse {
  horizon: number;
  asof_date: string | null;
  view: "episodes" | "pooled";
  horizons: number[];
  default_horizon: number;
  min_sample: number;
  phase_labels: string[];
  survivorship_bias: string;
  descriptive_caveat: string;
  n_total: number;
  n: number;
  unique_symbols: number;
  signal_dates: string[]; // the causal recovery-turn signal dates (entry dates studied)
  signal_count: number;
  by_horizon: RecoveryTurnEdgeHorizonRow[];
  best_exit_horizon: number | null;
  by_phase: RecoveryTurnEdgePhaseRow[];
}

/** Canonical Recovery-Turn Edge source: GET /api/research/recovery-turn-edge. Throws on non-200 so the
 *  page renders an explicit "Backend unavailable" state (503 no data / 422 bad horizon/view) — never
 *  fabricated evidence. All params optional (defaults: config default horizon / episodes / all-history). */
export async function fetchRecoveryTurnEdge(
  horizon?: number,
  asof?: string,
  view?: "episodes" | "pooled",
  signal?: AbortSignal,
): Promise<RecoveryTurnEdgeResponse> {
  const params = new URLSearchParams();
  if (horizon !== undefined) params.set("horizon", String(horizon));
  if (view !== undefined) params.set("view", view);
  const query = params.toString();
  const path = `/api/research/recovery-turn-edge${query ? `?${query}` : ""}`;
  return getJSON<RecoveryTurnEdgeResponse>(withAsOf(path, asof), signal);
}

// --- research / Downtrend Opportunity study (iter-32, J-91) ------------------------------------
/** One conditioned-cohort row of the Downtrend Opportunity study (J-91): a (dimension, cohort) group
 *  with its per-horizon-selected forward-return stats. The `dimension` is phase | severity_band |
 *  pbear_band; `cohort` is the cohort key in that dimension's config catalog; `cohort_label` is the
 *  display string. Re-formatted from stored values only. */
export interface DowntrendOpportunityRow {
  dimension: "phase" | "severity_band" | "pbear_band";
  cohort: string;
  cohort_label: string;
  stats: RegimeSetupPatternStats; // SAME stats shape as the J-77 study (downside-only risk-adjusted)
}

/** GET /api/research/downtrend-opportunity payload (J-91) — condition the existing forward-return evidence
 *  on the CAUSAL as-of downtrend state (phase / severity band / P(bear) band, all <= D) and read three
 *  angles: (a) held_up_best, (b) fell_hardest (EVIDENCE ONLY — no order/execution affordance), and (c) the
 *  reused J-90 recovery-turn edge. Every figure is read VERBATIM from the stored forward returns; the page
 *  re-formats only (recomputes nothing). `as_of` (J-32) scopes the pool + the causal context; `view` (J-63)
 *  is the overlap-honesty mode. The conditioning vocabulary (`conditioning_catalog`) is config-driven. */
export interface DowntrendOpportunityResponse {
  horizon: number;
  asof_date: string | null;
  view: "episodes" | "pooled";
  horizons: number[];
  default_horizon: number;
  min_sample: number;
  dimensions: ("phase" | "severity_band" | "pbear_band")[];
  conditioning_catalog: Record<string, { key: string; label: string }[]>;
  phase_labels: string[];
  survivorship_bias: string;
  descriptive_caveat: string;
  weakness_evidence_only: boolean; // J-91: the weakness angle is research evidence only — no order path
  n_total: number;
  held_up_best: DowntrendOpportunityRow[]; // angle (a) — best-first
  fell_hardest: DowntrendOpportunityRow[]; // angle (b) — worst-first, EVIDENCE ONLY
  recovery_turn_edge: RecoveryTurnEdgeResponse; // angle (c) — the reused J-90 payload
}

/** Canonical Downtrend Opportunity source: GET /api/research/downtrend-opportunity. Throws on non-200 so
 *  the page renders an explicit "Backend unavailable" state (503 no data / 422 bad horizon/view) — never
 *  fabricated evidence. All params optional (defaults: config default horizon / episodes / all-history). */
export async function fetchDowntrendOpportunity(
  horizon?: number,
  asof?: string,
  view?: "episodes" | "pooled",
  signal?: AbortSignal,
): Promise<DowntrendOpportunityResponse> {
  const params = new URLSearchParams();
  if (horizon !== undefined) params.set("horizon", String(horizon));
  if (view !== undefined) params.set("view", view);
  const query = params.toString();
  const path = `/api/research/downtrend-opportunity${query ? `?${query}` : ""}`;
  return getJSON<DowntrendOpportunityResponse>(withAsOf(path, asof), signal);
}

// --- research / severity-velocity × regime study (iter-45, J-103) ---------------------------
/** One matrix cell's stats: mean forward (SPY) return + win-rate + N + low-sample flag. mean/win-rate are
 *  null (NA) for an empty cell — read verbatim, the page gates low-sample/empty to NA. */
export interface SeverityVelocityCellStats {
  n: number;
  low_sample: boolean;
  mean_return: number | null;
  win_rate: number | null;
}

/** One matrix cell: a (family, velocity-sign) cohort + its stats. */
export interface SeverityVelocityCell {
  velocity_sign: string;
  velocity_sign_label: string;
  stats: SeverityVelocityCellStats;
}

/** One matrix row: a regime family + one cell per velocity sign. */
export interface SeverityVelocityRow {
  family: string;
  family_label: string;
  cells: SeverityVelocityCell[];
}

/** GET /api/research/severity-velocity payload (J-103) — the regime-family × velocity-sign matrix of the
 *  stored benchmark (SPY) forward return (mean / win-rate / N per cell), a read-only GROUPING of stored
 *  forward returns by the served severity-velocity (J-102) + stored regime label. NO new canonical value. */
export interface SeverityVelocityResponse {
  horizon: number;
  asof_date: string | null;
  horizons: number[];
  default_horizon: number;
  min_sample: number;
  benchmark: string; // the SPY benchmark whose forward return is the "market" return
  regime_families: { key: string; label: string }[]; // config-driven family vocabulary (matrix rows)
  velocity_signs: { key: string; label: string }[]; // config-driven sign vocabulary (matrix columns)
  survivorship_bias: string;
  descriptive_caveat: string;
  verdict_caveat: string; // the honest verdict caveats VERBATIM (hypothesis NOT supported on this seed)
  n_total: number; // the assignable observation count (== Σ cell N)
  matrix: SeverityVelocityRow[];
}

/** Canonical Severity-velocity × Regime source: GET /api/research/severity-velocity. Throws on non-200 so
 *  the page renders an explicit "Backend unavailable" state (503 no data / 422 bad horizon) — never
 *  fabricated evidence. All params optional (defaults: config default horizon / all-history). */
export async function fetchSeverityVelocity(
  horizon?: number,
  asof?: string,
  signal?: AbortSignal,
): Promise<SeverityVelocityResponse> {
  const params = new URLSearchParams();
  if (horizon !== undefined) params.set("horizon", String(horizon));
  const query = params.toString();
  const path = `/api/research/severity-velocity${query ? `?${query}` : ""}`;
  return getJSON<SeverityVelocityResponse>(withAsOf(path, asof), signal);
}

// --- research / samples drill-down (iter-7, J-51 / J-52) -----------------------------------
/** One displayed qualifying value on a sample row: the catalog `key` + `label` + the STORED `value`
 *  (a numeric factor value, or for an event study the matched setup/pattern label as a string). Read
 *  verbatim — the page re-formats only. */
export interface SampleRowValue {
  key: string;
  label: string;
  value: number | string;
}

/** One sample observation row (J-51): the ticker, its snapshot (as-of) date, the qualifying stored
 *  value(s), and the realized forward return at the cohort's horizon. The ticker links (J-52) to
 *  `/stocks/[ticker]?asof=<snapshot_date>` in a new tab. Re-formatted from stored values only. */
export interface SampleRow {
  ticker: string;
  snapshot_date: string | null; // the run's as-of date (ISO) — the J-52 deep-link date
  regime?: string | null;
  sector?: string | null;
  values: SampleRowValue[];
  forward_return: number | null;
}

/** The echoed resolved cohort definition (re-formatted into the page header so the drill-down states
 *  exactly which published N it reproduces). Shape varies by `kind`; the page reads the fields it needs. */
export interface SampleCohort {
  kind:
    | "factor"
    | "combination"
    | "event-study"
    | "regime-setup-pattern"
    | "recovery-turn"
    | "downtrend-opportunity"
    | "severity-velocity"
    | "regime-lab"
    | "phase-severity-lab"
    | "regime-phase-factor";
  horizon: number;
  slice?: string; // factor: total|decile|regime · event-study: pooled|regime|sector · recovery-turn: total|phase
  cohort?: string; // combination: baseline|single|composite|strict_overlap · downtrend: the band/phase cohort key
  factor?: FactorLabFactor; // factor kind · J-112 regime-phase-factor kind (the selected factor)
  decile?: number | null;
  regime_decile?: number; // J-112: the regime-score decile of the triple cohort
  severity_decile?: number; // J-112: the severity-score decile of the triple cohort
  factor_decile?: number; // J-112: the factor decile of the triple cohort
  regime?: string | null;
  sector?: string | null;
  setup?: string | null; // J-77: regime-setup-pattern kind
  pattern?: string | null; // J-77: regime-setup-pattern kind (a config pattern key or "none")
  phase?: string | null; // J-90: recovery-turn by-phase cohort (a market-phase label)
  dimension?: string | null; // J-91: downtrend-opportunity conditioning dimension (phase|severity_band|pbear_band)
  family?: string | null; // J-103: severity-velocity regime family (risk_on|neutral|risk_off)
  velocity_sign?: string | null; // J-103: severity-velocity sign (rising|flat|falling)
  subject?: EventStudySubject; // event-study kind
  view?: "episodes" | "pooled"; // J-63: the event-study overlap-honesty view this cohort reproduces
  conditions?: FactorCombinationCondition[]; // combination kind
  single_index?: number | null;
  deciles_count?: number;
}

/** GET /api/research/samples payload (J-51 / J-52) — the read-only drill-down behind one published `N=`
 *  figure. `total` EQUALS the published N by construction (count-coherence); `rows` are the exact member
 *  observations (the same stored per-observation inputs the aggregate consumed). A VALID n=0 cohort
 *  returns `rows: []` + `total: 0` (honest empty state, never a fabricated row). The page re-formats only
 *  — it recomputes no value/membership. `asof_date` (J-32) echoes the resolved point-in-time cutoff (ISO)
 *  when scoped; null = all-history. */
export interface SamplesResponse {
  kind: "factor" | "combination" | "event-study" | "regime-setup-pattern" | "recovery-turn";
  horizon: number;
  asof_date: string | null;
  cohort: SampleCohort;
  survivorship_bias: string;
  descriptive_caveat: string;
  total: number;
  rows: SampleRow[];
}

/** Canonical samples source: GET /api/research/samples. The query string fully reproduces the cohort
 *  (deep-linkable + reload-safe). Throws on non-200 so the page renders an explicit "Backend unavailable"
 *  state (503 no data / 422 invalid selector) — never fabricated rows. `asof` (J-32) is appended via
 *  `withAsOf` only when a historical cutoff is active (As-of mode + a past date). `params` is a flat
 *  list of [key, value] pairs so a repeated `condition` (combination kind) is preserved. */
export async function fetchSamples(
  params: [string, string][],
  asof?: string,
  signal?: AbortSignal,
): Promise<SamplesResponse> {
  const search = new URLSearchParams();
  for (const [k, v] of params) search.append(k, v);
  const query = search.toString();
  const path = `/api/research/samples${query ? `?${query}` : ""}`;
  return getJSON<SamplesResponse>(withAsOf(path, asof), signal);
}

// --- data manager (iter-3, J-17) -----------------------------------------------------------
/** Current dataset coverage — descriptive metadata only (the frontend re-formats it; it computes no
 *  coverage figure). `gaps_preview` is a bounded list of the backfill-able trading days that have bars
 *  but no snapshot; `gap_count` is the true total. */
/** One row of the J-36 per-symbol / per-universe-member coverage table — READ-ONLY descriptive metadata
 *  (the frontend re-formats it only; it recomputes no coverage figure). One row per stored symbol AND per
 *  universe member: `in_universe` is membership from the single canonical config.universe.symbols;
 *  `has_data` whether the symbol has bars; `first`/`last` the bar-date range (null/NA when no bars —
 *  never fabricated); `bar_count` the stored bar count; `thin` true iff 0 < bars < indicators.min_history_bars
 *  (the config thin threshold); `missing` true iff a universe member has no data (shown missing, not faked). */
export interface PerSymbolCoverage {
  symbol: string;
  in_universe: boolean;
  has_data: boolean;
  first: string | null; // NA when no bars
  last: string | null;
  bar_count: number;
  thin: boolean;
  missing: boolean;
}

/** J-37 — one no-history diagnostic row: a universe member with ZERO stored bars. `bars_have` is 0,
 *  `bars_needed` the config thin threshold; `pull_start`/`pull_end` span the benchmark calendar (the
 *  pull target). The frontend re-formats this only — it computes no shortfall. */
export interface DiagnosticNoHistory {
  symbol: string;
  category: "no_history";
  bars_have: number;
  bars_needed: number;
  pull_start: string | null;
  pull_end: string | null;
  pullable: boolean;
}

/** J-37 — one thin diagnostic row: 0 < bar_count < indicators.min_history_bars (insufficient history).
 *  A thin row alone is not pullable (its actionable gap, if any, surfaces as an intra_series_gap row). */
export interface DiagnosticThin {
  symbol: string;
  category: "thin";
  bars_have: number;
  bars_needed: number;
  pullable: boolean;
}

/** J-37 — one intra-series-gap diagnostic row: trading days (benchmark calendar) MISSING inside the
 *  member's own first→last range. `missing_day_count` + [first_gap, last_gap] are the exact shortfall;
 *  `missing_preview` is a bounded sample; `pull_start`/`pull_end` are the gap span the pull fills. */
export interface DiagnosticGap {
  symbol: string;
  category: "intra_series_gap";
  missing_day_count: number;
  first_gap: string;
  last_gap: string;
  missing_preview: string[];
  pull_start: string;
  pull_end: string;
  pullable: boolean;
}

/** J-37 — the Missing-data diagnostic: three honest categories of universe members insufficient for
 *  analysis, each with its EXACT shortfall, derived once from stored bars + config threshold + the
 *  benchmark calendar. A fine member appears in none. `threshold` is indicators.min_history_bars (the
 *  cutoff, surfaced so the UI states it). Read-only descriptive metadata — recomputes no canonical value. */
export interface MissingDataDiagnostic {
  threshold: number;
  no_history: DiagnosticNoHistory[];
  thin: DiagnosticThin[];
  intra_series_gaps: DiagnosticGap[];
  affected_count: number;
}

export interface DataCoverage {
  price_start: string | null;
  price_end: string | null;
  symbol_count: number;
  // iter-33 (J-93): the AS-OF-RESOLVED universe size — the members the point-in-time resolver admits at
  // the single global as-of (the dynamic membership the scored snapshot scores for that date). Distinct
  // from symbol_count (DISTINCT priced symbols incl. ETFs+^VIX) and from the static counts below.
  universe_count: number;
  // J-93: the resolved as-of (ISO) the dynamic universe_count was computed at (null on an empty DB).
  universe_asof: string | null;
  // J-93: the full candidate-pool denominator (the read_pool listing the resolver screens).
  candidate_pool_count: number;
  // J-93: the STATIC candidate-universe count (len(config.universe.symbols)) the per-symbol table's
  // `in_universe` rows count (the data-table membership view — NOT date-scoped).
  candidate_universe_count: number;
  snapshot_count: number;
  snapshot_dates: string[]; // newest first
  trading_day_count: number;
  gap_count: number;
  gap_first: string | null;
  gap_last: string | null;
  gaps_preview: string[]; // ascending; bounded by config.data_manager.gap_preview
  // J-36: the per-symbol / per-universe-member coverage table (universe members first, then priced
  // symbols; the UI re-sorts/filters only). distinct has-data rows == symbol_count;
  // in-universe == candidate_universe_count.
  per_symbol: PerSymbolCoverage[];
  // J-37: the Missing-data diagnostic (three honest categories with exact shortfalls). Read-only.
  diagnostic: MissingDataDiagnostic;
  // J-94: the per-date coverage diagnostic — for the resolved as-of, the admitted count + the
  // excluded-by-reason counts (below_history / below_price / below_adv) against the candidate pool.
  universe_diagnostic: UniverseDiagnostic;
  // J-96: the dynamic-universe membership timeline — per-snapshot-date resolved size (step function) +
  // entries/exits + per-date excluded counts, with the three honest labels. Read-only descriptive.
  membership_timeline: MembershipTimeline;
  // J-85: the universe-vs-latest-snapshot coverage diagnostic — the count of resolved-universe members
  // ABSENT from the latest scanner snapshot's scored set (the operator-facing "rebuild to include the new
  // members" signal). Read-only descriptive derivation; absent_count 0 → the UI shows NO banner.
  absent_from_latest_snapshot: AbsentFromLatestSnapshot;
}

/** J-94 — the per-date coverage diagnostic. For the resolved as-of: the admitted count + the excluded-
 *  by-reason counts (below_history / stale_series / below_price / below_adv — iter-18 added the recency
 *  gate) against the candidate-pool denominator, plus the exact config thresholds the resolver gated on
 *  (the UI states them, never re-types them). */
export interface UniverseDiagnostic {
  asof: string | null;
  candidate_pool_count: number;
  admitted_count: number;
  excluded_total: number;
  excluded: { below_history: number; stale_series: number; below_price: number; below_adv: number };
  thresholds: {
    min_history_bars: number;
    min_price: number;
    min_dollar_vol: number;
    adv_window_days: number;
    max_staleness_days: number;
  };
}

/** J-96 — one point of the membership timeline: the resolved size (step function) + the deterministic
 *  entries/exits + the per-date excluded-by-reason counts, observed causally from that date's snapshot.
 *  iter-18: `stale_series` (the recency gate — a name whose data ended exits cleanly) joins the counts. */
export interface MembershipTimelinePoint {
  date: string;
  size: number;
  entries: string[];
  exits: string[];
  excluded: { below_history: number; stale_series: number; below_price: number; below_adv: number };
}

/** J-95(b) — the candidate pool's honest survivorship descriptor (current-constituent caveat). */
export interface PoolSurvivorship {
  label: string;
  basis: string; // "current_constituent"
  pool_count: number;
  point_in_time_feed_available: boolean; // always false — the data-walled enhancement, never faked
}

/** J-96 — the three honest labels carried VERBATIM beside the timeline (the UI re-types none of this). */
export interface MembershipLabels {
  survivorship: PoolSurvivorship;
  warmup: { min_history_bars: number; boundary_date: string | null; label: string };
  universe_relative: string;
}

/** J-96 — the dynamic-universe membership timeline served on the Data Manager coverage surface. */
export interface MembershipTimeline {
  candidate_pool_count: number;
  points: MembershipTimelinePoint[];
  labels: MembershipLabels;
}

/** J-85 — the universe-vs-latest-snapshot coverage diagnostic. `absent_count` is the count of resolved
 *  universe members NOT scored in the latest snapshot; `absent_preview` a bounded sample; the UI shows the
 *  "N members absent — rebuild to include them" banner ONLY when `absent_count > 0`. `universe_count` is
 *  now the members RESOLVED at the latest snapshot date (J-93); `candidate_pool_count` the full pool. */
export interface AbsentFromLatestSnapshot {
  absent_count: number;
  absent_preview: string[];
  latest_snapshot_date: string | null;
  universe_count: number;
  candidate_pool_count: number;
}

/** One row of the fetch/backfill run history (from the append-only DataProviderRun log). A Data Manager
 *  job carries `kind`/`start`/`end`/`snapshots_created`/…; a plain seed-load row leaves them null. */
export interface DataRun {
  id: number;
  provider: string;
  kind: string | null; // fetch | backfill | both | expand | null (seed load)
  start: string | null;
  end: string | null;
  // J-60: the job lifecycle — running (in-flight, from job start) → ONE terminal transition. interrupted
  // = a boot sweep marked an orphaned running row whose process died; resumable = a rate-limited pause.
  status: string; // running | ok | partial | failed | interrupted | resumable
  symbols_ok: number;
  symbols_failed: number;
  snapshots_created: number | null;
  dates_done: number | null;
  dates_total: number | null;
  // ops-hardening iter-1 (J-01) — the backfill/both/rebuild run-summary exclusion breakdown; null for a
  // fetch/expand run (matching the existing dates_total nullability pattern). Invariants (enforced
  // server-side, never re-derived here): non_trading_days + dates_total == calendar_days;
  // snapshots_created + already_snapshotted + error_other == dates_total.
  calendar_days: number | null;
  non_trading_days: number | null;
  already_snapshotted: number | null;
  error_other: number | null;
  // ops-hardening iter-2 (J-05) — which downstream aggregates (coverage, latest snapshot, membership
  // timeline, market phase, research hot-keys) this run's ingest finalize hook refreshed. null for a
  // fetch/expand run and for a not-yet-computed/interrupted row (matches the calendar_days-style
  // nullability convention above — never a fabricated list).
  aggregates_refreshed: string[] | null;
  bars_fetched: number | null;
  passers: number | null; // J-35 expand screen outcome (null for non-expand runs)
  omitted_total: number | null; // J-35 expand screen outcome (null otherwise)
  started_at: string | null;
  finished_at: string | null;
  message: string | null;
}

/** One import-source provider in the config-driven catalog (J-33), with env-detected availability. The
 *  frontend re-formats this only — it NEVER hardcodes a provider list (the catalog + each source's key
 *  requirement come from GET /api/data). `env_var` is the environment-variable NAME the key is read from
 *  (the NAME only — a key value is NEVER served by the API); `available` is true when no key is needed or
 *  the env var is set; `reason` is a server-built sentence rendered verbatim. */
export interface ProviderSource {
  id: string;
  label: string;
  needs_key: boolean;
  env_var: string | null;
  supports_market_cap: boolean;
  available: boolean;
  reason: string;
}

/** One paused, resumable chunked import (J-34), surfaced by GET /api/data so it survives a backend
 *  restart (the in-memory job is gone but the durable checkpoint persists). Descriptive job-control
 *  metadata ONLY — it carries the chosen `source` id (not secret) and chunk/symbol progress, NEVER a
 *  key value (the checkpoint has no key column). The frontend re-formats it and offers a Resume action. */
export interface ResumableImport {
  import_id: string;
  source: string; // the chosen import provider id (not secret); never the key
  kind: string;
  start: string;
  end: string;
  chunk_index: number; // completed chunks == the resume point
  chunk_total: number;
  symbols_total: number;
  symbols_ok: number;
  symbols_failed: number;
  symbols_remaining: number;
  bars_fetched: number;
  status: string; // always "resumable" in this list
  updated_at: string | null;
}

/** J-38 — one row of the UNIFIED Unfinished-imports list: every import that did NOT finish cleanly.
 *  `record_type` distinguishes a resumable durable CHECKPOINT (`id` = import_id; actions Resume/Remove)
 *  from a partial/failed operational RUN (`id` = numeric run id; actions Retry/Dismiss). `state` is a
 *  server-built plain-language explanation rendered verbatim; `actions` lists the offered actions.
 *  Descriptive job-control metadata ONLY — NEVER a key value (the source id is not secret). */
export interface UnfinishedImport {
  record_type: "checkpoint" | "run";
  id: string | number; // import_id (checkpoint) or run id (run)
  import_id: string | null;
  source: string;
  kind: string | null;
  start: string | null;
  end: string | null;
  chunk_index: number | null;
  chunk_total: number | null;
  symbols_total: number;
  symbols_ok: number;
  symbols_failed: number;
  symbols_remaining: number;
  bars_fetched: number | null;
  status: string; // resumable | failed_backfill (J-59) | partial | failed
  // J-59: which pipeline stages completed (e.g. ["fetch"] for a failed-at-backfill row that is
  // resumable from the backfill stage). Present on checkpoint rows.
  completed_stages?: string[];
  updated_at: string | null;
  state: string; // plain-language explanation (rendered verbatim)
  actions: string[]; // e.g. ["resume","remove"] or ["retry","dismiss"]
}

/** J-66: the fine-grained job-progress knobs from config (No magic numbers) — the live job card reads
 *  the poll interval + heartbeat-stale threshold from here, never a hardcoded literal. */
export interface JobProgressConfig {
  poll_interval_seconds: number;
  heartbeat_stale_seconds: number;
  per_symbol_ticks: boolean;
}

/** J-92: one configured FRED macro series' availability in the Data Manager catalog. `committed_rows` is
 *  the number of committed-seed observations; `available` is true when there ARE committed rows (offline)
 *  — a walled/uncommitted series (0 rows + no live key) is honestly NA, never a fabricated value. Carries
 *  the FRED series id + the publication lag + the optional OHLCV proxy ticker; never a key value. */
export interface MacroSeriesAvailability {
  id: string;
  label: string;
  fred_series_id: string;
  publication_lag_days: number;
  proxy_symbol: string | null;
  committed_rows: number;
  available: boolean;
  reason: string;
}

/** J-92: the OPTIONAL FRED macro feed catalog + availability surfaced in the Data Manager. The FRED key is
 *  env-only (`env_var` is the NAME; `live_available` is whether it is set) — NEVER a key value. `enable`
 *  carries the per-leg config-default-OFF flags (so default figures are unchanged). Descriptive metadata. */
export interface MacroAvailability {
  provider: string; // "fred"
  label: string;
  env_var: string; // the env-var NAME only — never a key value
  live_available: boolean; // whether the FRED key env-var is set (the NAME is detected, not the value)
  enable: { severity: boolean; regime_switching: boolean; study: boolean };
  series: MacroSeriesAvailability[];
  publication_lag_note: string;
}

/** Item K (iter-24 fast-platform pass) — the DB storage-footprint snapshot: on-disk file size + row
 *  counts for the three largest tables. Pure DB introspection over stored rows (recomputes no canonical
 *  value); an honest all-zero snapshot on a cold/empty DB (never an error). Presentation of stored
 *  values only — the frontend re-formats this, it never derives a size/count itself. */
export interface DataCapacity {
  db_file_bytes: number;
  daily_prices_rows: number;
  scanner_results_rows: number;
  forward_returns_rows: number;
}

/** iter-35 (J-21/B-304) — one symbol whose overlap window disagreed between a live fetch and the
 *  committed seed: the exact mismatching dates + the honest classification (an "adjustment_seam" — the
 *  vendor silently re-adjusted already-committed history). Never a fabricated diagnosis. */
export interface DriftAffectedSymbol {
  symbol: string;
  mismatching_dates: string[];
  classification: string;
}

/** iter-35 (J-21/B-304) — the live-vs-seed drift report: the SAME artifact the readiness `drift`
 *  preflight component reads (`app.engine.drift.read_drift_report`), served here VERBATIM — no
 *  recompute, no second parse path (the Data Contract single-source requirement). `status` is
 *  `"clean"` (the last fetch matched the seed over the overlap window), `"drift"` (a mismatch —
 *  `affected` names every symbol + its mismatching dates), or `"unreadable"` (the artifact exists but
 *  could not be parsed — an honest degraded state, never silently treated as clean). Descriptive
 *  integrity reporting only — no proven/not-proven language. */
export interface DriftReport {
  status: "clean" | "drift" | "unreadable";
  reference: string | null;
  overlap_days: number | null;
  affected: DriftAffectedSymbol[];
}

export interface DataOverviewResponse {
  coverage: DataCoverage;
  runs: DataRun[];
  sources: ProviderSource[]; // J-33 import-source catalog (config-driven, env-detected availability)
  macro: MacroAvailability; // J-92 optional FRED macro feed catalog (env-detected; committed-seed coverage)
  resumable_imports: ResumableImport[]; // J-34 paused imports (survive a backend restart); never a key
  unfinished_imports: UnfinishedImport[]; // J-38 unified unfinished imports (resumable + partial + failed)
  job_progress: JobProgressConfig; // J-66 poll/heartbeat/granularity knobs (config-driven)
  capacity: DataCapacity; // item K (iter-24) — the DB storage-footprint snapshot
  // iter-35 (J-21/B-304): `null` when no fetch has ever run (honest inert — the card renders a quiet
  // "no fetch yet" state, distinct from a confirmed "clean").
  drift: DriftReport | null;
}

export type DataJobKind = "fetch" | "backfill" | "both" | "expand" | "rebuild";

/** One omitted candidate from a J-35 expand screen — the symbol + the plain-language reason it did NOT
 *  become a universe member (e.g. "market_cap … < …", "price … < …", "no_market_cap", "fetch_failed").
 *  Read-only descriptive job-control metadata; never a fabricated member/cap. */
export interface ExpandOmission {
  symbol: string;
  reason: string;
}

/** J-53: one EXECUTED stage's operational timings (descriptive metadata, NOT a canonical score). Only
 *  stages that actually ran are present in `DataJob.stages` — a stage that never ran is ABSENT (NA),
 *  never a fabricated zero. `items_processed` is symbols (fetch) or dates (backfill); `concurrency` is
 *  the config pool size used; `per_date_seconds_sum` (backfill only) is the sequential per-date baseline
 *  the parallel `elapsed_seconds` is measured against (the >=~2x speedup is read from the two figures). */
export interface JobStageTiming {
  elapsed_seconds: number;
  items_processed: number;
  concurrency: number;
  per_date_seconds_sum?: number; // backfill only — the sum of per-date compute times (the serial baseline)
  // J-66: the SERVER-computed backfill speedup figure (per_date_seconds_sum / elapsed_seconds) — the
  // frontend only re-formats it (no client-side division). null = honest NA (a missing/zero figure).
  speedup_factor?: number | null;
}

/** J-67: one per-date backfill failure on a `partial` job — the date that failed (others completed) and
 *  its honest error. Never a fabricated snapshot for the failed date. */
export interface JobDateFailure {
  date: string;
  error: string;
}

/** Live progress for one fetch/backfill job (polled from the in-memory job registry). `status` is
 *  running | ok | partial | failed | "resumable" (J-34: a rate-limited graceful pause). Counters are
 *  the live progress; `chunk_index`/`chunk_total` are the J-34 chunked-fetch progress (both 0 / absent
 *  for a non-chunked job); `message` is a server-built summary (rendered verbatim); `errors` carries
 *  explicit per-symbol failure messages (never fabricated; the key is redacted at source + scrubbed). */
export interface DataJob {
  job_id: string;
  kind: string;
  start: string;
  end: string;
  source?: string | null; // J-33: the chosen import provider id (not secret); never the key
  status: string; // running | ok | partial | failed | resumable
  symbols_total: number;
  symbols_ok: number;
  symbols_failed: number;
  bars_fetched: number;
  dates_total: number;
  dates_done: number;
  snapshots_created: number;
  forward_returns_inserted: number;
  // ops-hardening iter-1 (J-01/J-03): the live exclusion breakdown — 0 for a fetch/expand-only job (no
  // backfill stage ran). Mirrors the persisted `DataRun` fields (see api layer / data_manager.py).
  calendar_days?: number;
  non_trading_days?: number;
  already_snapshotted?: number;
  error_other?: number;
  // ops-hardening iter-2 (J-05): the live job's finalize-hook output so far — empty/absent while running
  // or before the hook has run (honest; never fabricated), populated once the finalize hook completes.
  aggregates_refreshed?: string[] | null;
  chunk_index?: number; // J-34: completed chunks (== checkpoint resume point)
  chunk_total?: number; // J-34: total planned chunks (chunk x/N); 0/absent for a non-chunked job
  passers?: number; // J-35 expand: candidates that passed the screen (became universe members)
  omitted_total?: number; // J-35 expand: EXACT omitted count (the list below is bounded)
  omitted?: ExpandOmission[]; // J-35 expand: bounded [{symbol, reason}] — never fabricated
  stages?: Record<string, JobStageTiming>; // J-53: per-stage timings (only EXECUTED stages present)
  // J-66: fine-grained, honest live-progress fields. `current_activity` names what is being worked on
  // RIGHT NOW (the symbol/chunk during fetch, the date being scanned during backfill); `last_progress_at`
  // is the heartbeat (the UI renders "updated Ns ago"). Honest metadata — never fabricated.
  current_activity?: string;
  last_progress_at?: string | null;
  // J-59: which pipeline stages completed (so the UI can render "failed at backfill — resumable from the
  // backfill stage" and the resume routes correctly).
  completed_stages?: string[];
  // J-67: per-date backfill failures (honest error + which dates) on a `partial` job.
  date_failures?: JobDateFailure[];
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
  source?: string; // J-33: the resolved import source id (echoed; never the key)
  status: string;
}

/** Canonical Data Manager coverage + run-history source: GET /api/data. Throws on non-200 so the page
 *  renders an explicit "Backend unavailable" state — never fabricated coverage.
 *
 *  iter-33 (J-93/J-94): `asof` is the SINGLE GLOBAL as-of (read from `useAsOf`, NOT a second date
 *  state) — the coverage block's dynamic `universe_count` + per-date `universe_diagnostic` are resolved
 *  at this date. Omitting it serves the latest stored date's resolution. The backend falls back
 *  gracefully on a bad as-of (descriptive coverage never 4xx's). */
export async function fetchDataCoverage(asof?: string, signal?: AbortSignal): Promise<DataOverviewResponse> {
  return getJSON<DataOverviewResponse>(withAsOf("/api/data", asof), signal);
}

/** J-61: one cell of the per-trading-date availability heatmap — READ-ONLY descriptive metadata derived
 *  over the SAME stored bars + runs the coverage figures use (never a recomputed score/return). For one
 *  benchmark trading day: the point-in-time DISTINCT count of symbols with a bar on that date (NOT
 *  cumulative; a zero-bar day is honestly present with a low/zero count, never omitted as covered), the
 *  density denominator (== coverage `symbol_count`), and whether an immutable snapshot exists for it. */
export interface AvailabilityCell {
  date: string; // yyyy-MM-dd (a benchmark trading day)
  symbols_with_bars: number; // distinct symbols WITH a bar ON this date (point-in-time)
  total_symbols: number; // the distinct stored-symbol universe == coverage symbol_count (the denominator)
  snapshot_exists: boolean; // an immutable ScannerRun snapshot exists for this as-of date
}

/** J-61: the per-trading-date availability payload (GET /api/data/availability). `cells` is one entry per
 *  benchmark trading day, ascending. An empty / bars-less DB → `cells: []`, `total_symbols: 0` (no
 *  fabricated cells). Descriptive metadata only — no canonical value is recomputed. */
export interface AvailabilityResponse {
  total_symbols: number;
  trading_day_count: number;
  cells: AvailabilityCell[];
}

/** J-61: GET /api/data/availability — the per-trading-date availability heatmap source. Throws on a
 *  non-200 so the `/data` page can show no figures rather than fabricated cells (mirrors the coverage
 *  "Backend unavailable" treatment). The date inputs the heatmap PREFILLS are job parameters — selecting
 *  a heatmap day never writes the global as-of viewing control. */
export async function fetchDataAvailability(signal?: AbortSignal): Promise<AvailabilityResponse> {
  return getJSON<AvailabilityResponse>("/api/data/availability", signal);
}

/** POST /api/data/jobs — start an async fetch/backfill job over a date range (the date inputs are JOB
 *  PARAMETERS, NOT a viewing as-of control). The optional J-33 `opts` carry the chosen import `source`
 *  and a SESSION-ONLY `api_key` (sent only when non-blank — never stored client-side beyond the request).
 *  Returns immediately with a `job_id`; throws with the backend's honest `detail` on a non-2xx (400
 *  invalid range / unknown source / needs-key-without-key, 422 malformed date, 503 no data). */
export async function startDataJob(
  kind: DataJobKind,
  start: string,
  end: string,
  opts?: { source?: string; api_key?: string; symbols?: string[] },
): Promise<StartJobResponse> {
  const body: Record<string, unknown> = { kind, start, end };
  if (opts?.source) body.source = opts.source;
  if (opts?.api_key) body.api_key = opts.api_key; // session-only; omitted when blank
  if (opts?.symbols && opts.symbols.length) body.symbols = opts.symbols; // J-37 gap-exact pull scope
  return sendJSON<StartJobResponse>("POST", "/api/data/jobs", body);
}

/** J-37 pull-missing — start a gap-exact fetch over EXACTLY the diagnosed `(symbols, [start,end])`
 *  shortfall, dispatched through the SAME job-start path (no second fetch engine). The chunked fetch is
 *  per-(symbol, date) idempotent, so it fills only the missing bars. The optional `opts` carry the chosen
 *  import `source` + a SESSION-ONLY `api_key` (sent only when non-blank — never stored beyond the request). */
export async function pullMissingData(
  symbols: string[],
  start: string,
  end: string,
  opts?: { source?: string; api_key?: string },
): Promise<StartJobResponse> {
  return startDataJob("fetch", start, end, { ...opts, symbols });
}

/** J-38 Retry — re-dispatch ONLY the outstanding/failed work of a partial/failed run through the SAME
 *  chunked engine (per-(symbol, date) idempotent — no duplicate bar). The optional `opts.api_key` is the
 *  SESSION-ONLY key re-supplied for a needs-key source (sent only when non-blank). Returns the NEW job's
 *  id; throws with the backend's honest `detail` (404 unknown run, 409 not retryable, 400 needs-key). */
export async function retryDataJob(
  runId: number,
  opts?: { api_key?: string },
): Promise<{ run_id: number; job_id: string; source: string; status: string }> {
  const body: Record<string, string> = {};
  if (opts?.api_key) body.api_key = opts.api_key; // session-only; omitted when blank
  return sendJSON<{ run_id: number; job_id: string; source: string; status: string }>(
    "POST",
    `/api/data/jobs/${encodeURIComponent(String(runId))}/retry`,
    body,
  );
}

/** J-38 Remove/Dismiss — drop ONLY the actionable job-control record so it leaves the Unfinished-imports
 *  list: a resumable `checkpoint` is DELETED; a partial/failed `run` is SOFT-DISMISSED (it stays in the
 *  append-only Run-history audit). No immutable snapshot/forward-return/audit row is deleted or mutated.
 *  Throws with the backend's honest `detail` on a non-2xx (404 unknown id). */
export async function dismissUnfinishedImport(
  recordType: "checkpoint" | "run",
  recordId: string | number,
): Promise<{ record_type: string; id: string | number; dismissed: boolean }> {
  const qs = `?record_type=${encodeURIComponent(recordType)}`;
  return sendJSON<{ record_type: string; id: string | number; dismissed: boolean }>(
    "POST",
    `/api/data/jobs/${encodeURIComponent(String(recordId))}/dismiss${qs}`,
    {},
  );
}

/** GET /api/data/jobs/{job_id} — poll a job's live status/progress, ending in its final summary.
 *  Throws on non-200 (404 unknown job) so the UI surfaces the failure rather than fabricating one. */
export async function fetchDataJob(jobId: string, signal?: AbortSignal): Promise<DataJob> {
  return getJSON<DataJob>(`/api/data/jobs/${encodeURIComponent(jobId)}`, signal);
}

/** POST /api/data/jobs/{import_id}/resume — resume a paused (resumable) chunked import from its next
 *  un-fetched chunk (J-34). The optional `opts.api_key` is the SESSION-ONLY key re-supplied for a
 *  needs-key source (sent only when non-blank — the checkpoint stores no key, so a restart-then-resume
 *  of a key source must re-supply it; never stored client-side beyond the request). Returns immediately
 *  with the resumed job's id; throws with the backend's honest `detail` on a non-2xx (404 unknown import,
 *  409 not resumable, 400 needs-key-without-key). */
export async function resumeDataJob(
  importId: string,
  opts?: { api_key?: string },
): Promise<{ import_id: string; source: string; status: string }> {
  const body: Record<string, string> = {};
  if (opts?.api_key) body.api_key = opts.api_key; // session-only; omitted when blank
  return sendJSON<{ import_id: string; source: string; status: string }>(
    "POST",
    `/api/data/jobs/${encodeURIComponent(importId)}/resume`,
    body,
  );
}

// --- J-39 seed-safe Remove-data: confirm-preview + destructive removal ----------------------------

/** The removal scope (action parameters — which bars to remove, NOT the global as-of viewing control):
 *  by symbol and/or by date range. At least one must be set; the committed seed is never deletable. */
export interface RemoveScope {
  symbols?: string[];
  start?: string;
  end?: string;
}

/** One not-removable (committed-seed) breakdown line in a removal preview: the protected symbol, how many
 *  of its in-scope bars are committed seed, and the reason ("committed seed"). The committed seed is
 *  un-deletable, so these bars are always excluded from the removal. */
export interface RemoveSeedLine {
  symbol: string;
  bar_count: number;
  reason: string;
}

/** The cascade of derived rows a removal would (preview) / did (execute) remove: the snapshots
 *  (ScannerRun + children) and forward returns that depended SOLELY on the removed bars. A whole-row
 *  delete — never an in-place overwrite of a retained snapshot. */
export interface RemoveCascade {
  snapshot_count: number;
  snapshot_dates: string[];
  forward_return_count: number;
}

/** The J-39 confirm-preview / removal result (read-only descriptive metadata; the frontend re-formats it).
 *  `removable_*` is exactly what would be / was removed (user-added bars only); `not_removable_by_symbol`
 *  is the protected committed-seed breakdown; `cascade` is the dependent snapshot/forward-return rows;
 *  `refused` + `reason` mark a wholly-committed-seed scope (the destructive endpoint 400s on it, the
 *  preview returns refused=true so the UI disables the confirm). `removed_bar_count` is present on the
 *  executed-removal response (the done-count). */
export interface RemovePreview {
  removable_bar_count: number;
  removable_symbol_count: number;
  removable_symbols: string[];
  removable_first: string | null;
  removable_last: string | null;
  not_removable_bar_count: number;
  not_removable_by_symbol: RemoveSeedLine[];
  cascade: RemoveCascade;
  refused: boolean;
  reason: string;
  removed_bar_count?: number; // present on the executed removal response only
}

/** POST /api/data/remove/preview — READ-ONLY confirm-preview: returns exactly what WOULD be removed
 *  (removable user-added bars + range, the not-removable committed-seed breakdown, and the cascade of
 *  dependent snapshot/forward-return rows) while DELETING NOTHING. A wholly-committed-seed scope returns
 *  refused=true (a 200 the UI renders to disable the destructive confirm). Throws with the backend's
 *  honest `detail` on a non-2xx (400 empty/inverted/unknown scope). */
export async function previewDataRemoval(scope: RemoveScope): Promise<RemovePreview> {
  return sendJSON<RemovePreview>("POST", "/api/data/remove/preview", scope);
}

/** POST /api/data/remove — DESTRUCTIVE seed-safe removal: deletes only the user-added bars in scope and
 *  cascade-removes the snapshot/forward-return rows that derived solely from them (the committed seed is
 *  un-deletable). Throws with the backend's honest `detail` on a non-2xx (400 wholly-seed / empty /
 *  inverted / unknown scope). After it resolves, re-read GET /api/data — it reflects the smaller dataset. */
export async function executeDataRemoval(scope: RemoveScope): Promise<RemovePreview> {
  return sendJSON<RemovePreview>("POST", "/api/data/remove", scope);
}
