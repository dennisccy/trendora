/**
 * Pure numeric derivation for the readiness badge / preflight banner's LIVE staleness value
 * (ops-hardening iter-78, iter-77/d) -- the "as of Ns ago" annotation (`lib/staleness-annotation.ts`'s
 * `formatStaleAnnotation`) previously only updated on poll landing, so it could read "as of <1s ago" for
 * up to the full poll-idle interval (`health_poll_idle_interval_seconds`, 30s in config.yaml) before the
 * next poll refreshed it -- an annotation that looks frozen even though real time is passing.
 *
 * This function does NO formatting -- it only re-derives the numeric seconds-stale value that
 * `formatStaleAnnotation` is fed, from the last poll's own `stale_for_s` base plus how much client
 * wall-clock time has elapsed since that poll was received. `ReadinessProvider` calls it once a second
 * from a local tick interval; `formatStaleAnnotation` remains the single formatting authority downstream
 * -- never a second formatter.
 *
 * Ticking is intentionally a no-op (returns the base UNCHANGED) whenever the base itself is one of
 * `formatStaleAnnotation`'s own null-rendering cases -- `null` (no poll has landed yet, or the last poll
 * failed), `0` (a fresh/synchronous compute, a SENTINEL for "not stale" rather than a literal age to
 * count up from), or a non-finite/negative value (defensive, unexpected payload shape). Ticking those
 * upward would let a value that should never render start rendering once enough time passed -- a
 * fabricated annotation from an input that was never a real age. Only a genuinely positive, finite base
 * ticks.
 */
export function deriveLiveStaleForS(
  baseStaleForS: number | null,
  receivedAtMs: number | null,
  nowMs: number,
): number | null {
  if (baseStaleForS === null || !Number.isFinite(baseStaleForS) || baseStaleForS <= 0) {
    return baseStaleForS;
  }
  if (receivedAtMs === null || !Number.isFinite(receivedAtMs) || !Number.isFinite(nowMs)) {
    // No valid receipt anchor to tick from -- fall back to the last-known base, unticked, rather
    // than guess or fabricate an elapsed duration.
    return baseStaleForS;
  }
  const elapsedS = Math.max(0, (nowMs - receivedAtMs) / 1000);
  return baseStaleForS + elapsedS;
}
