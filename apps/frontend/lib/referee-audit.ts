/**
 * Referee-calibration report types (goal-mcp-loop iter-36, J-22 / backlog B-102).
 *
 * Mirrors `lib/budget.ts`'s types-only pattern for the SEPARATE `GET /api/research/referee-audit`
 * payload — the certifier's own measured empirical false-pass rate (with a binomial CI) against the
 * configured α over seeded null factors, plus the lookahead-contaminated-factor tripwire result —
 * computed once by an ISOLATED offline audit job against a throwaway ledger and re-read VERBATIM here.
 *
 * This module carries NO proven-language: every figure is descriptive calibration accounting (a trial
 * count, a false-pass rate, a verdict kind) — never a "Proven"/"Not yet proven" signal. The ONLY source
 * of "Proven" stays the certified-claims ledger via `lib/evidence.ts` / `GET /api/evidence`; this file
 * never touches that path, and the audit's throwaway trials never appear there.
 */

import type { Verdict } from "@/lib/evidence";

/** The lookahead-contaminated factor's referee verdict — the SAME `Verdict` shape a certified-claims row
 *  carries (status/reason/edge/p-value/etc.), re-displayed verbatim. Its `status` is expected to be
 *  "FAIL" or "INSUFFICIENT" (caught) but MAY legitimately be "PASS" (the tripwire case) — the page must
 *  render whichever the artifact actually recorded, never assume it away. */
export type RefereeAuditContaminatedVerdict = Verdict;

/** One persisted referee-calibration run, read VERBATIM from `GET /api/research/referee-audit`.
 *  `status === "unreadable"` is the honest degraded-parse state (a corrupt artifact) — every OTHER field
 *  is `null` in that case; `status === "ok"` is a real, successfully-built run and every field below is
 *  populated. `contaminated_caught` is the DERIVED boolean (`contaminated_verdict.status !== "PASS"`)
 *  the page uses to choose its calm vs. its loud tripwire-failure treatment;
 *  `contaminated_expected_outcome` is always the STATIC label `"rejected"` (a caption, not a claim about
 *  what happened). */
export interface RefereeAuditReport {
  status: "ok" | "unreadable";
  run_date: string | null;
  n_null_trials: number | null;
  seed: number | null;
  alpha: number | null;
  source_factor: string | null;
  false_pass_count: number | null;
  false_pass_rate: number | null;
  false_pass_ci_low: number | null;
  false_pass_ci_high: number | null;
  n_insufficient_null: number | null;
  contaminated_factor_horizon: number | null;
  contaminated_verdict: RefereeAuditContaminatedVerdict | null;
  contaminated_expected_outcome: "rejected" | null;
  contaminated_caught: boolean | null;
}

/** The `GET /api/research/referee-audit` payload: `report` is `null` when the offline harness has never
 *  run (the honest empty state — distinct from `status === "unreadable"`, which means a run DID happen
 *  but its artifact could not be parsed). */
export interface RefereeAuditResponse {
  report: RefereeAuditReport | null;
}
