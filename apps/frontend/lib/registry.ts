/**
 * Pre-registration registry types (goal-mcp-loop iter-30, J-18 / backlog B-901).
 *
 * Mirrors `lib/evidence.ts`'s types-plus-small-helpers pattern for the SEPARATE `GET
 * /api/research/registry` payload — every hypothesis ever registered/tested, read VERBATIM (re-format
 * only; nothing recomputed).
 *
 * This module carries NO proven-language and NO evidence-status resolution: a registration's `status`
 * ("registered" / "tested" / "closed") is a descriptive PROCESS state, never a "Proven"/"Not yet proven"
 * signal — a "tested" row may have FAILED out-of-sample (every backfilled row today did). The ONLY source
 * of "Proven" stays the certified-claims ledger via `lib/evidence.ts` / `GET /api/evidence`; this file
 * never touches that path.
 */

/** One pre-registration row, read VERBATIM from `GET /api/research/registry`. `selectors` is the EXACT
 *  cohort selector-set (`kind` + the present cohort keys + `horizon` + `direction`) the gate matches an
 *  incoming Evidence Claim against — re-displayed as-is, never recomputed or reformatted into a numeric
 *  edge. */
export interface PreRegistrationRow {
  id: string;
  selectors: Record<string, unknown>;
  rationale: string;
  registered_by: string;
  registered_date: string;
  source: string;
  /** Descriptive process state (e.g. "registered" | "tested" | "closed") — NEVER proven-language. */
  status: string;
}

/** The `GET /api/research/registry` payload: every registration, in registration (append) order. */
export interface RegistryResponse {
  registrations: PreRegistrationRow[];
}
