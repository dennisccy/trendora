/**
 * Read-side evidence types + the inline-badge status resolver (goal-mcp-loop iter-1).
 *
 * This module is the SINGLE place the UI decides whether a signal reads "Proven" or "Not yet proven".
 * It is PURE and dependency-free (no React, no fetch) so it is unit-testable under the repo's
 * `node lib/*.test.ts` pattern — the React `EvidenceStatusBadge` and the `/evidence` page consume it.
 *
 * The evidence ledger is the ONLY source of proven-ness (goal.md Constraints + anti-goal): the UI NEVER
 * computes proven-ness itself. A signal is "Proven" ONLY when the served `proven_signals` map (built by the
 * backend from a `verdict.status == "PASS"` ledger entry) names it; any signal ABSENT from that map — or a
 * null/failed/empty map — is "Not yet proven" (the fail-safe default). Against today's empty ledger every
 * signal therefore reads "Not yet proven".
 */

/** The referee's verdict for one claim, re-displayed VERBATIM (never recomputed). Only the fields the
 *  Evidence page reads are typed explicitly; the additive audit fields ride along via the index signature. */
export interface Verdict {
  status: string; // "PASS" | "FAIL" | "INSUFFICIENT"
  reason: string;
  in_sample_edge?: number | null;
  holdout_edge?: number | null; // the out-of-sample edge
  control_excess?: number | null; // the control comparison (cohort − benchmark/SPY)
  p_value?: number | null;
  [key: string]: unknown;
}

/** One certified-claims ledger row, read VERBATIM from `GET /api/evidence`. `claim` is the hypothesis
 *  (the cohort selectors); `proven` is true ONLY for a PASS verdict; `signal` is the UI signal key the
 *  PASS backs (null for a real signal-less writer entry — fail-safe). `forward_walk` is the forward-walk
 *  score-to-date (null until a certified claim is monitored). */
export interface CertifiedClaim {
  signal: string | null;
  claim: Record<string, unknown>;
  register_date: string | null;
  horizon: number | null;
  cohort_n: number | null;
  control_n: number | null;
  verdict: Verdict;
  proven: boolean;
  forward_walk: unknown | null;
}

/** A proven claim row, as stored in the served `proven_signals` map (keyed by signal). Same shape as a
 *  `CertifiedClaim`; the alias documents intent at the badge call sites. */
export type ProvenSignal = CertifiedClaim;

/** The `GET /api/evidence` payload: the full claim list the ledger page renders + the proven-signal map
 *  the inline badge reads. */
export interface EvidenceLedgerResponse {
  claims: CertifiedClaim[];
  proven_signals: Record<string, ProvenSignal>;
}

/** The two honest, calm status labels — never hype (goal.md Design Direction). */
export const PROVEN_LABEL = "Proven";
export const NOT_PROVEN_LABEL = "Not yet proven";

/** The Evidence-page anchor a "Proven" badge links to (claim → surface linkback target). The claim rows
 *  on `/evidence` carry the matching `id`, so the badge jumps straight to the backing entry. */
export function evidenceAnchor(signal: string): string {
  return `/evidence#signal-${signal}`;
}

/** The resolved status for one signal's inline badge. */
export interface EvidenceStatus {
  proven: boolean;
  /** "Proven" | "Not yet proven" — the exact text the badge renders. */
  label: string;
  /** The ledger anchor to link to when proven; null when not yet proven (no link). */
  href: string | null;
  /** The backing claim row when proven; null otherwise. */
  claim: ProvenSignal | null;
}

/**
 * Resolve a signal's evidence status from the served `proven_signals` map. FAIL-SAFE: any signal absent
 * from the map (or a null/undefined map, or a row that is not `proven`) resolves to "Not yet proven" with
 * no link — the UI never fabricates proven-ness. A present, proven row resolves to "Proven" linking to its
 * backing ledger entry.
 */
export function resolveEvidenceStatus(
  signal: string,
  provenSignals: Record<string, ProvenSignal> | null | undefined,
): EvidenceStatus {
  const claim = provenSignals?.[signal] ?? null;
  if (claim && claim.proven) {
    return { proven: true, label: PROVEN_LABEL, href: evidenceAnchor(signal), claim };
  }
  return { proven: false, label: NOT_PROVEN_LABEL, href: null, claim: null };
}
