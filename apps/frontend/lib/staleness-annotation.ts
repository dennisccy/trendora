/**
 * Pure formatter for the readiness badge / preflight banner's "as of {N}s ago" staleness annotation
 * (ops-hardening iter-77, J-04/J-07 disclosure) -- the FIRST UI consumer of `GET /api/health`'s
 * `stale_for_s` field (served since iter-71, never rendered until now). Re-formats the server value
 * ONLY -- no computation. Renders nothing (null) for a fresh/synchronous compute (`stale_for_s === 0`,
 * per the spec's "no annotation for a synchronous/fresh compute" acceptance) and, defensively, for any
 * non-finite/negative value, so a caller can never accidentally render a fabricated "as of 0s ago" or
 * "as of NaNs ago" from an unexpected payload shape. `staleForS === null` (before the first poll
 * resolves, or on a failed poll -- `useReadiness()`'s own honest-failure convention) also renders
 * nothing -- callers must never show a stale or fabricated number when the backend is unreachable.
 */
export function formatStaleAnnotation(staleForS: number | null): string | null {
  if (staleForS === null || !Number.isFinite(staleForS) || staleForS <= 0) return null;
  const seconds = Math.round(staleForS);
  // Sub-second staleness is the STEADY STATE here, not an edge case: the readiness cache refreshes
  // every `readiness.refresh_interval_seconds` (0.5s), so a live sample of the served field reads e.g.
  // 0.053 / 0.128 / 0.505 -- roughly 11 of 15 values round to zero (measured, ops-hardening iter-77
  // audit finding F1). Rounding those to "as of 0s ago" printed a self-contradictory annotation ("it is
  // stale... by no time at all") on almost every render. Say what is actually true instead -- the
  // payload IS stale, by less than a second -- so the disclosure never reads as nonsense and never
  // disappears while real staleness exists.
  return seconds < 1 ? "as of <1s ago" : `as of ${seconds}s ago`;
}
