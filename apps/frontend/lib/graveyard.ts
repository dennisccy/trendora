/**
 * Negative-results graveyard types (goal-mcp-loop iter-31, J-19 / backlog B-902).
 *
 * Mirrors `lib/registry.ts`'s types-only pattern for the SEPARATE `GET /api/research/graveyard`
 * payload — every NON-PASS referee verdict across BOTH the canonical and staging certified-claims
 * ledgers, read VERBATIM (re-format only; nothing recomputed, nothing re-matched).
 *
 * This module carries NO proven-language and NO evidence-status resolution: `verdict.status` here is
 * ALWAYS "FAIL" or "INSUFFICIENT" (the backend filters PASS out before this ever reaches the client) —
 * a verdict-kind badge, never a "Proven"/"Not yet proven" signal. The ONLY source of "Proven" stays the
 * certified-claims ledger via `lib/evidence.ts` / `GET /api/evidence`; this file never touches that path.
 */

import type { Verdict } from "@/lib/evidence";
import type { PreRegistrationRow } from "@/lib/registry";

/** The two ledgers a graveyard entry may originate from — `"canonical"` (the user-facing, always-strict-
 *  Bonferroni ledger) or `"staging"` (the internal exploration ledger, never served elsewhere). Surfacing
 *  staging's NON-PASS rows here is the one deliberate, documented narrowing of the prior "staging is
 *  internal-only" invariant; staging carries 0 PASS rows, so this never surfaces a proven-looking edge. */
export type GraveyardLedger = "canonical" | "staging";

/** One rejected (non-PASS) hypothesis, read VERBATIM from `GET /api/research/graveyard`. `claim` is the
 *  EXACT cohort selector-set the referee tested (re-displayed as-is, same shape as a certified-claims row
 *  or a registry row's `selectors`). `lineage` is the matched pre-registration row (`null` for an honest,
 *  unregistered selector-set — no crash, no fabricated link). */
export interface GraveyardEntry {
  ledger: GraveyardLedger;
  claim: Record<string, unknown>;
  register_date: string | null;
  horizon: number | null;
  cohort_n: number | null;
  control_n: number | null;
  verdict: Verdict;
  lineage: PreRegistrationRow | null;
}

/** The re-test policy (backlog B-406 / §0), served as a single constant so the page's panel and every
 *  row's anchor agree on the SAME wording — descriptive governance text, never proven-language. */
export interface RevisitProtocol {
  rule: string;
}

/** The `GET /api/research/graveyard` payload: every non-PASS entry across both ledgers, plus the served
 *  revisit-protocol constant. */
export interface GraveyardResponse {
  entries: GraveyardEntry[];
  revisit_protocol: RevisitProtocol;
}
