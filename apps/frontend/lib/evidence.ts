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

/**
 * The signal key each per-stock score maps to on the evidence ledger — the canonical factor-catalog keys,
 * byte-identical to the UI signal key (e.g. the Leadership score IS `leadership_score`). The SINGLE
 * definition shared by the Stocks leaderboard and the Stock-detail score cards (de-duped in iter-2 — there
 * was one identical copy in each page). A score reads "Proven" ONLY when a PASS-backed ledger entry names
 * its key; everything absent from `proven_signals` is "Not yet proven".
 */
export const SCORE_SIGNALS = {
  leadership: "leadership_score",
  entry_quality: "entry_quality_score",
  risk: "risk_score",
} as const;

// --- proof drill-down (J-02) field extraction + display formatters ------------------------------------
// These are PURE and read-only: they re-display what the referee already certified (read VERBATIM from the
// served `proven_signals` map) and FABRICATE nothing. The Stock-detail "Why proven?" panel renders them;
// the unit tests pin them. Proven-ness still flows 100% from `resolveEvidenceStatus` (a PASS-backed entry).

/** Coerce a served numeric field to a finite number, else null (NA-honest — never a fabricated 0). */
function finiteOrNull(value: unknown): number | null {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

/**
 * The proof fields a "Proven" score drills into — read VERBATIM from the backing ledger entry (the
 * out-of-sample test, the SPY control comparison, and the certified-claim id/date). Every numeric field is
 * the referee's value exactly as written; the panel only re-formats it. `null` numerics render "—"
 * (never a fabricated figure).
 */
export interface ProofFields {
  /** The certified-claim's signal key (the stable id component, e.g. "leadership_score"). */
  signal: string;
  /** The out-of-sample verdict status, verbatim (e.g. "PASS"). */
  status: string;
  /** The out-of-sample holdout edge (a fraction), verbatim — null when the entry omits it. */
  holdoutEdge: number | null;
  /** The out-of-sample significance (p-value), verbatim — null when the entry omits it. */
  pValue: number | null;
  /** The control comparison vs SPY (the cohort's excess over the benchmark, a fraction), verbatim. */
  controlExcess: number | null;
  /** The sealed-holdout cohort size, verbatim — null when the entry omits it. */
  cohortN: number | null;
  /** The registration date (ISO), verbatim — null when the entry omits it. */
  registerDate: string | null;
  /** The stable certified-claim id label: `${signal} · registered ${registerDate}`. */
  claimId: string;
  /** The `/evidence` backing-row anchor this proof links to (claim → surface linkback). */
  href: string;
}

/**
 * Build the read-only proof fields for one signal from the served `proven_signals` map, or `null` when the
 * signal is NOT proven (absent / null map / non-`proven` row). FAIL-SAFE: an unproven signal yields `null`
 * so the "Why proven?" disclosure is absent entirely (no empty panel, no fabricated confidence). Reads
 * every field VERBATIM from the backing claim — recomputes nothing.
 */
export function proofFieldsFor(
  signal: string,
  provenSignals: Record<string, ProvenSignal> | null | undefined,
): ProofFields | null {
  const status = resolveEvidenceStatus(signal, provenSignals);
  if (!status.proven || !status.claim || !status.href) {
    return null;
  }
  const claim = status.claim;
  const verdict = claim.verdict ?? { status: "", reason: "" };
  const registerDate = claim.register_date ?? null;
  return {
    signal,
    status: verdict.status ?? "",
    holdoutEdge: finiteOrNull(verdict.holdout_edge),
    pValue: finiteOrNull(verdict.p_value),
    controlExcess: finiteOrNull(verdict.control_excess),
    cohortN: finiteOrNull(claim.cohort_n),
    registerDate,
    claimId: registerDate ? `${signal} · registered ${registerDate}` : signal,
    href: status.href,
  };
}

/**
 * Format a signed fraction as a percent with an explicit sign (e.g. +6.36% / -0.40%). Display-only; the
 * SAME representation the `/evidence` claim row uses for the holdout edge and the SPY control comparison.
 * A null/undefined/non-finite value renders an em dash (never a fabricated 0%).
 */
export function formatEvidencePct(value: number | null | undefined): string {
  if (value == null || !Number.isFinite(value)) {
    return "—";
  }
  const pct = value * 100;
  return `${pct >= 0 ? "+" : ""}${pct.toFixed(2)}%`;
}

/**
 * Format an out-of-sample p-value for display — 4 significant figures (matching the referee's own
 * `verdict.reason` formatting, e.g. 0.0004998), `< 0.0001` for vanishingly small values, an em dash for a
 * missing value. Display-only; never recomputed.
 */
export function formatPValue(value: number | null | undefined): string {
  if (value == null || !Number.isFinite(value)) {
    return "—";
  }
  if (value <= 0) {
    return "0";
  }
  if (value < 0.0001) {
    return "< 0.0001";
  }
  return Number(value.toPrecision(4)).toString();
}
