/**
 * ops-hardening iter-33 (UT-11 fix) — the single pure decision a research lab route renders its
 * pre-data area from.
 *
 * WHY THIS EXISTS: `/research/regime-lab` previously rendered an UNLABELLED grey skeleton for as long as
 * its fetch stayed pending. On a cold cache the backing derivation (`GET /api/research/regime-lab`) is
 * computed once per dataset over the full stored forward-return history and measured 60-90 s on the deep
 * basis, so a first-time visitor sat on an animated placeholder with zero feedback — no explanation, no
 * elapsed time, no retry affordance — and could not tell "still working" apart from "broken". Browser QA
 * recorded that as a P1 smoke failure (UT-11).
 *
 * The rule this encodes: a SHORT wait stays a plain skeleton (no alarming copy for an ordinary sub-second
 * load), but once the wait crosses a small grace window the page must switch to an explicit, LABELLED
 * "still computing" state that shows how long it has been waiting; a failed fetch must resolve to an
 * explicitly RETRYABLE error panel. It never becomes an indefinite unlabelled skeleton.
 *
 * This is presentation only: it reads, recomputes, and fabricates NO figure — it decides which honest
 * state to show while the canonical value is still being fetched.
 */

/** How long a lab fetch may stay a plain skeleton before the page owes the user an explicit,
 *  time-stamped "still computing" explanation. A short grace window, so an ordinary fast load never
 *  flashes alarming copy, but a genuinely slow first compute is never silent. */
export const SLOW_COMPUTE_NOTICE_AFTER_SECONDS = 3;

/** The lab route's own fetch status (the three states every lab page already tracks). */
export type LabFetchStatus = "loading" | "ok" | "error";

/** Which honest state the lab's data area renders.
 *  - `skeleton`    — a brief ordinary load; the placeholder alone is honest.
 *  - `computing`   — the wait crossed the grace window; render the labelled notice WITH `elapsedSeconds`.
 *  - `error`       — the fetch failed; render the error card with a retry affordance.
 *  - `data`        — the payload arrived; render the tables. */
export type LabLoadPanel =
  | { kind: "skeleton" }
  | { kind: "computing"; elapsedSeconds: number }
  | { kind: "error"; retryable: true }
  | { kind: "data" };

/**
 * Resolve the panel to render from the lab's fetch status and how many seconds the current attempt has
 * been in flight. `elapsedSeconds` is ignored for a settled fetch (a slow-but-successful read renders its
 * data; a failure renders its retryable error) — it only decides how a still-pending read is presented.
 */
export function resolveLabLoadPanel(status: LabFetchStatus, elapsedSeconds: number): LabLoadPanel {
  if (status === "error") return { kind: "error", retryable: true };
  if (status === "ok") return { kind: "data" };
  if (elapsedSeconds >= SLOW_COMPUTE_NOTICE_AFTER_SECONDS) {
    return { kind: "computing", elapsedSeconds };
  }
  return { kind: "skeleton" };
}

/** A human-readable elapsed label for the computing notice: whole seconds under a minute ("42s"),
 *  minutes + zero-padded seconds at or above one ("1m 30s"). Negative/fractional inputs are floored to
 *  a sane whole second rather than rendering a nonsense label. */
export function formatElapsedSeconds(seconds: number): string {
  const total = Math.max(0, Math.floor(seconds));
  if (total < 60) return `${total}s`;
  const minutes = Math.floor(total / 60);
  const rest = total % 60;
  return `${minutes}m ${String(rest).padStart(2, "0")}s`;
}
