/**
 * Typed backend API client. RE-FORMATS server values only — NO business computation here
 * (no scores/buckets/returns are ever computed client-side; the backend is the single source
 * of truth). iter-1 exposes only the health probe.
 */

export interface HealthStatus {
  status: string;
  db_ok: boolean;
  provider: string;
  last_run_date: string | null;
  seed_latest_date: string | null;
  symbol_count: number;
}

export const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

/** Fetch backend health. Throws on network error or non-200 so callers can render an
 *  explicit "unavailable" state — we never fabricate an "ok". */
export async function fetchHealth(signal?: AbortSignal): Promise<HealthStatus> {
  const res = await fetch(`${API_BASE}/api/health`, { signal, cache: "no-store" });
  if (!res.ok) {
    throw new Error(`health check failed: HTTP ${res.status}`);
  }
  return (await res.json()) as HealthStatus;
}
