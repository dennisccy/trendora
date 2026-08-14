/**
 * The single, pure authority for how the `/data` job card renders the ingest FINALIZE TAIL — the
 * post-scan phase where a job has finished every date but is still warming the caches `/data` reads.
 * No React, no DOM types, so it is unit-testable under `node` (the existing frontend convention — see
 * `lib/availability-empty-state.ts`, `lib/availability-month-bands.ts`).
 *
 * The defect this exists to fix (measured live 2026-08-14, run 530 — an 8-date backfill): for 15m22s
 * after the scan loop ended, `GET /api/data/jobs/<id>` served `dates_done/dates_total = 8/8`,
 * `message: "snapshots 8/8 dates"`, `current_activity: "scanning 2026-08-12 (8/8)"` — a scan that had
 * ended minutes earlier — and a `last_progress_at` 141s stale. So the card rendered a FULL progress bar,
 * a completed-sounding message, a false "still scanning" line AND an amber "· possibly stalled", all at
 * once, on a perfectly healthy job. It read as permanently stuck.
 *
 * The backend now publishes `finalize_phase` + `finalize_phase_started_at` (`JobProgress`), so the card
 * can say what is actually happening. Two rules encoded here:
 *
 *   1. While a finalize phase is named, that phase — with its own elapsed time — replaces the frozen
 *      scan line, and the generic stall warning is suppressed. The elapsed figure carries the same
 *      "this is taking a while" signal truthfully; a stall warning that fires on every healthy backfill
 *      is noise, and this one fired because the longest phase (`factor_lab_all_warm`, 511s) is a single
 *      call with no per-item heartbeat.
 *   2. The stale-heartbeat heuristic is UNCHANGED for the scan loop, where it is still the honest
 *      signal — no finalize phase is named there.
 */

/** The finalize fields as served by `GET /api/data/jobs/<id>` (both absent/empty when no phase runs). */
export interface FinalizeFields {
  status: string;
  finalize_phase?: string | null;
  finalize_phase_started_at?: string | null;
}

export interface FinalizeView {
  /** The phase label to render, e.g. "factor lab". */
  phase: string;
  /** Time spent in THIS phase, pre-formatted (e.g. "6m38s"), or "" when it cannot be computed. */
  elapsed: string;
}

/** Format a whole-second duration as `1h02m`, `6m38s` or `12s` — compact enough for the card's one line. */
export function formatElapsed(seconds: number): string {
  if (!Number.isFinite(seconds) || seconds < 0) return "";
  const total = Math.floor(seconds);
  const h = Math.floor(total / 3600);
  const m = Math.floor((total % 3600) / 60);
  const s = total % 60;
  if (h > 0) return `${h}h${String(m).padStart(2, "0")}m`;
  if (m > 0) return `${m}m${String(s).padStart(2, "0")}s`;
  return `${s}s`;
}

/**
 * The finalize line to render, or null when no finalize phase is in flight (the honest idle case — the
 * card then falls back to its normal activity + heartbeat rendering, unchanged).
 *
 * `nowMs` is passed in rather than read from the clock so this stays pure and testable.
 */
export function finalizeView(job: FinalizeFields, nowMs: number): FinalizeView | null {
  const phase = job.finalize_phase?.trim();
  if (!phase) return null;
  const started = job.finalize_phase_started_at ? Date.parse(job.finalize_phase_started_at) : NaN;
  const elapsed = Number.isFinite(started) ? formatElapsed((nowMs - started) / 1000) : "";
  return { phase, elapsed };
}

/**
 * Whether the generic "· possibly stalled" warning may render. Suppressed while a finalize phase is
 * named: the job is provably doing known work, and the phase's own elapsed time is the honest signal.
 * Every other case is unchanged, so the scan loop keeps its stall detection.
 */
export function shouldShowStallWarning(job: FinalizeFields, heartbeatIsStale: boolean): boolean {
  if (!heartbeatIsStale) return false;
  return !job.finalize_phase?.trim();
}

/**
 * The label beside the backfill progress bar. A bar sitting at 8/8 must not be the card's only signal
 * while the tail runs — so the counts get an explicit "· finalizing" suffix in that state, and are
 * returned unchanged otherwise.
 */
export function backfillCountsLabel(job: FinalizeFields, done: number, total: number): string {
  const base = `${done}/${total} dates`;
  return job.status === "running" && job.finalize_phase?.trim() ? `${base} · finalizing` : base;
}
