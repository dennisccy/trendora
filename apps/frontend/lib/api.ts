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
 *  same response — there is no second computation/source for the sector score. */
export async function fetchSectors(signal?: AbortSignal): Promise<SectorsResponse> {
  return getJSON<SectorsResponse>("/api/sectors", signal);
}

// --- dashboard (iter-2) --------------------------------------------------------------------
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
  candidate_counts: Record<string, number> | null; // null = pending (iter-3)
  top_themes: unknown[] | null; // null = pending (iter-3)
}

/** Canonical Market Regime source: GET /api/dashboard. */
export async function fetchDashboard(signal?: AbortSignal): Promise<DashboardResponse> {
  return getJSON<DashboardResponse>("/api/dashboard", signal);
}
