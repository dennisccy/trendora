/**
 * Certification-budget accounting types (goal-mcp-loop iter-32, J-17 / backlog B-903).
 *
 * Mirrors `lib/graveyard.ts`'s types-only pattern for the SEPARATE `GET /api/research/budget` payload —
 * how much statistical-credibility budget has already been spent, re-read VERBATIM (or re-derived via
 * the SAME referee/ledger seams the certifier uses; re-format only — nothing recomputed here).
 *
 * This module carries NO proven-language: trial counts and alpha figures are descriptive accounting,
 * never a "Proven"/"Not yet proven" signal. The ONLY source of "Proven" stays the certified-claims
 * ledger via `lib/evidence.ts` / `GET /api/evidence`; this file never touches that path.
 */

/** One point on a ledger's per-trial spend-over-time series, read VERBATIM from that trial's OWN
 *  recorded verdict (never recomputed). `required_p` is the significance bar (Bonferroni or LORD++)
 *  that trial was actually judged at; `deflation_divisor` / `alpha_charged` ride along on the canonical
 *  series only (staging's `deflation_divisor` mirrors the trial ordinal under LORD++, not a meaningful
 *  divisor, so it is omitted there). */
export interface BudgetSpendPoint {
  trial: number;
  register_date: string | null;
  status: string | null;
  required_p: number | null;
  deflation_divisor?: number | null;
  alpha_charged?: number | null;
}

/** The canonical (strict-Bonferroni) accounting: trials to date (a DISPLAY value, distinct from the
 *  forward-looking `n_trials_next`), the forward next-trial bar, and the Thresholdout budget remaining. */
export interface CanonicalBudget {
  n_trials_to_date: number;
  n_trials_next: number;
  alpha_per_test: number;
  required_p: number;
  alpha_budget_total: number;
  alpha_spent: number;
  alpha_budget_remaining: number;
  spend_over_time: BudgetSpendPoint[];
}

/** The staging (LORD++) accounting: trials to date, and the forward next-trial significance level (the
 *  "alpha-wealth" figure) — the internal exploration economy, never served on the canonical /evidence bar. */
export interface StagingBudget {
  n_trials_to_date: number;
  n_trials_next: number;
  next_level: number;
  spend_over_time: BudgetSpendPoint[];
}

/** The `GET /api/research/budget` payload: the canonical + staging accounting, each self-contained. */
export interface BudgetResponse {
  canonical: CanonicalBudget;
  staging: StagingBudget;
}
