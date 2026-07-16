# goal-mcp-loop-iter-41 Audit Report

**Date:** 2026-07-16
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS

J-25's phase-conditional drawdown & dry-spell expectations panel is fully and correctly delivered: the panel renders per-phase (median/p90/n) distributions of max-DD depth, underwater duration, time-to-recover, and walk-forward-cadence loss-streak on every `/evidence` claim card, from stored `ForwardReturn` columns read verbatim, joined to the causal phase-at-entry. I did **not** accept the correctness claim on trust — I independently re-derived every served phase cell for all 7 ledger claims (raw-SQL column read + numpy percentiles + a hand-rolled cadence streak, cohort via the mandated single resolver) and got **zero mismatches** (all deltas 0.00e+00), and those values match both the recorded perf-budgets spot-check and the QA-rendered screenshot pixels exactly. No critical or important issues; the residual items are GAP/observation-level polish that fixing would be scope creep.

---

## 2. Findings

### Backend Findings

**B1 — OBSERVATION (observation): EventStudyCache invalidation is data-version-only, not config-sensitive**
`compute_drawdown_expectations_cached` (`forward_testing.py:1321`) keys the cache on `_dataset_version` (`research.py:1532` — max `scanner_runs.id` + `forward_returns` row count) plus horizon. `min_sample`/`streak_min_n` are NOT in the key, so a config floor change without a data rebuild would serve a stale-floored payload. This is the **sanctioned, codebase-wide EventStudyCache contract the spec explicitly mandated reusing** ("the SAME cache every other research-derived aggregate uses"), not a new J-25 defect; in practice floor changes accompany a rebuild (which bumps the row count → new version). The `underwater_horizons` scope gate is correctly applied pre-cache in the wrapper, so it is not affected. Acceptable as-is.

**B2 — OBSERVATION (observation): `build_evidence_payload` docstring lists 4 test files that never call it**
`engine/evidence.py:130` claims "~13 existing call sites (incl. `test_graveyard.py`, `test_api_graveyard.py`, `test_api_budget.py`, `test_budget_accounting.py`)" but only `test_evidence.py` calls it. Inherited from an inaccurate plan reference. Documentation-accuracy only — the backward-compat behavior it describes is correct and verified. (Already flagged as the reviewer's NOTE.)

### Frontend Findings

**F1 — OBSERVATION (observation): phase Badge uses `variant="default"` rather than the `lib/phase.ts` `phasePosture` color mapping**
`app/evidence/page.tsx:282` renders the phase label with the flat neutral Badge instead of the single-source phase-color mapping used by `market-phase-card.tsx`/`app/page.tsx`. The dev made this a deliberate no-hype choice (five repeated per-row labels under the loud `accent` variant would read as noisy — and the plan's own Visual Requirements say "no hype color"). Defensible; a minor cross-app consistency-polish item. (Already flagged as the reviewer's MINOR.)

### Test Findings

**T1 — GAP (gap): time-to-recover distribution is silently conditional on recovery-within-horizon**
`compute_drawdown_expectations` (`forward_testing.py:1271`) appends `time_to_recover_days` to the phase distribution only when it is non-None, i.e. only for observations that DID recover to the entry level within the horizon. Names that never recovered (arguably the worst dry spells) are excluded from the median/p90; the only signal is a `time_to_recover_days` cell `n` lower than the phase `n`. This is **within spec** — B-205/the spec define time-to-recover as "NA if it never recovers in-window", and excluding NAs from a distribution is standard — and it is honest (the lower n is shown). But the visible `method_note` covers only the loss-streak cadence, not this censoring, so a reader could misread a short median time-to-recover as reassuring. A future single-sentence method-note addition would close it. Not fixed (GAP-level; per-spec; fixing is scope creep).

---

## 3. Domain Assessment

The core domain logic is correct, single-sourced, and no-lookahead by construction:

- **Correctness (anti-goal #3) — independently verified far beyond the DoD.** The DoD asked for ONE re-derived cell. I re-derived **every served phase cell for all 7 claims** — max-DD median/p90/n and loss-streak value/n — using a raw `sqlite3` read of the stored columns (not the module's ORM `select`) and `numpy.percentile` (not the module's `_median_p90`), with a hand-rolled cadence streak. Result: 0 mismatches across 5 factor + 1 event-study + 1 combination claims. My claim-0 Expansion values (median -7.70%, p90 -3.72%, n=1264) match both `reports/perf-budgets.md` Item I and the QA screenshot's rendered `-7.70% (p90 -3.72%) n=1264` — a triple match (independent re-derivation = served value = rendered pixels). The phase split is meaningful (e.g. claim 3 vcp_contraction: Correction median max-DD -14.4% vs Expansion -6.5%), which is precisely J-25's product point.
- **Single source / no fork.** `max_drawdown` is called once in `_insert_run_forward_returns:392` and stored verbatim; `underwater_days`/`time_to_recover_days` are separate additive helpers. `time_to_recover_days` re-derives the running-peak series ONLY to locate the trough index (which `max_drawdown` does not expose) — it does not alter or fork the DD-depth value; a unit test pins them in agreement. `compute_drawdown_expectations` is the only module computing the panel; the UI reads it verbatim (`page.tsx:236`).
- **No-lookahead (anti-goal #5).** The helpers slice `window = bars_after_list[:horizon]`, so no later bar can change a stored value; phase-at-entry uses the strictly-causal `phase_context_by_date` keyed on each observation's own snapshot date. A no-lookahead unit test is among the 29 that pass.
- **Honest failure handling.** I directly exercised the unhappy paths: session-less `build_evidence_payload` attaches no `expectations` key (byte-identical to pre-iter-41); a missing ledger returns `{"claims": [], "proven_signals": {}}`; an unknown factor, a malformed combination `condition`, a zero-observation cohort, and an out-of-scope horizon each return `None` (honest omission, never a raise); the cached path is byte-identical to the uncached one. The NA gate is real: `underwater_days` is populated on 170,229/170,229 rows (identical to `max_drawdown`), `time_to_recover_days` on 103,589 (the rest honest NA).
- **No regression / additive-only.** The tracked diff is +1504/−19; all 19 deletions are import expansions, function-signature changes for session threading, and docstring edits — no existing aggregation/scoring logic removed. `scoring.py`/`prices.py` are untouched; `compute_forward_aggregates`/`compute_run_scorecard` signatures and bodies are unchanged. The certified-claims ledger is untouched (7 entries, 0 PASS / 7 FAIL, divisor stays 8, no `## Evidence Claim` introduced). Existing `test_evidence.py` (incl. the frozen golden) is unedited and green.
- **Anti-goals #1/#2.** The panel carries no "Proven"/"Not yet proven" badge (only a neutral phase-name Badge) and no buy/sell/trim/reduce/rebalance/target verb in rendered copy; wording is historical ("historically felt like … descriptive history only, never a forecast or a promise"), with the served walk-forward method note and the B-111 survivorship caveat ("upper bound, not a guarantee") shown verbatim.
- **Anti-goal #8 (memory).** `reports/perf-budgets.md` Item I records the full-universe rebuild under the literal 6144 MB `ulimit -v` cap with both VmPeak (VSZ ~2.70 GB, 56% margin) and VmHWM (RSS ~1.79 GB) sampled on two consecutive runs (Run 2 ≤ Run 1) — the exact iter-26 methodology. I did not re-run the multi-hour 30-year rebuild in-audit (it would fork-lock the host and the memory notes warn against concurrent heavy runs), but its verifiable outputs — the row counts and the correctness spot-check values — independently check out against the committed DB, so the recorded measurement is a sound basis for this DoD line. The discovered ~3x `/api/evidence` latency regression (uncached ~9.5 s) was fixed via the shared EventStudyCache (warm 6–17 ms), inside the J-15 budget.

**Verification note:** the operational note said the live services were up on :8255/:3255 for byte-match; they were NOT (the only running services belong to a different project, `tapeology`, on :8301/:8301). I verified against the committed DB and the module code directly instead — a stronger, more independent check than reading a served byte.

---

## 4. Fixes Applied During This Audit

None. Every finding is GAP- or OBSERVATION-level; per the auditor rules, fixing them would be scope creep. No critical or important issue was found that required a source change.

| # | Severity | File | Change |
|---|----------|------|--------|
| — | — | — | No fixes applied — implementation verified correct as-shipped |

---

## 5. Recommended Next Step

**Proceed.** J-25 — the last unbuilt Must-have — is delivered, correct, and independently verified; GOAL_ACHIEVED is now reachable after the **iter-42 lean closeout**, whose job (per this spec's NOTES and the recurring iter-33/36/38/40 pattern) is the deterministic golden-replay of the full required-still-passing set folding in the never-replayed J-23.json, J-24.json, and the new J-25.json — the structurally-unsatisfiable-in-a-FULL-iter replay line this iteration legitimately deferred and live-verified via browser-qa instead. Optional, non-blocking polish for a future touch of `/evidence`: add one method-note sentence disclosing that time-to-recover is measured only over names that recovered within the horizon (T1), and align the phase Badge with `lib/phase.ts` `phasePosture` (F1). Neither blocks the goal.
