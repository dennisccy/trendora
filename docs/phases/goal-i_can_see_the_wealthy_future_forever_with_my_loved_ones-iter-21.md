# Goal Iteration 21 — Make the full backend suite green (J-72/J-75/J-77 consolidation)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** i_can_see_the_wealthy_future_forever_with_my_loved_ones
- **Iteration:** 21
- **Mode:** next
- **Depth:** lean
- **Frontend Present:** no
- **Target journeys:** J-72, J-75, J-77
- **Required-still-passing journeys:** J-05, J-06, J-18, J-21, J-25, J-26, J-29, J-32, J-48, J-50, J-51, J-63, J-64, J-65
- **Anti-goal reminders:**
  - **No magic numbers.** Every scoring weight, threshold, decision-rule cutoff, bucket edge, universe entry, and theme definition MUST come from the config file — no such literal in calculation code.
  - **Snapshots are immutable.** A persisted `scanner_run` and its result rows MUST never be updated or overwritten after creation; forward returns live in a separate append-only table keyed to the snapshot. *(critical)*
  - **Single source of truth.** Each of the six canonical scores (and the A–E bucket and setup status) MUST be computed exactly once by the scoring/regime engine and read identically by every page; the API and frontend MUST NOT recompute them. The same symbol's score MUST NOT differ between two views. *(critical)*
  - **No recompute in the read path.** Read endpoints MUST serve canonical values from the persisted immutable snapshot for the resolved as-of date; they MUST NOT recompute scores/returns/buckets per request. *(critical)*
  - **No lookahead.** Scoring for a snapshot dated D MUST use only price bars with date ≤ D; forward returns MUST use only bars with date > D. *(critical)*

## GOAL

Turn the authoritative full backend pytest suite GREEN (0 failed) by fixing exactly the two iter-20-introduced failures — without changing any served payload — so J-72, J-75, and J-77 can be confirmed and the session becomes a GOAL_ACHIEVED candidate.

## BACKGROUND

iter-20 built J-72 (event-study perf/cache), J-75 (per-stock forward returns), and J-77 (Regime × Setup × Pattern study) functionally correct: coherence-auditor returned COHERENCE-PASS, review PASS, QA UI-PASS, byte-identity + count-coherence + NA-honesty + 4xx paths all verified, and no prior-passing journey regressed. The ONLY gap is the standing iter-19 DoD gate — the full backend pytest suite — which is RED at **2 failed / 831 passed** (`/tmp/trendora-iter20-fullsuite.log`), both failures introduced by the iter-20 diff:

1. `tests/test_db.py::test_create_all_produces_expected_tables` — the new standalone `EventStudyCache` SQLModel table (`__tablename__ = "event_study_cache"`, the J-72 cache; `apps/backend/app/models.py:367-403`) was correctly architected as a standalone create_all-managed table (coherence-confirmed, no `_ADDITIVE_COLUMNS` needed) but was not added to the expected-tables set the test compares against.
2. `tests/test_no_magic_numbers.py::test_engine_calc_code_has_no_magic_numbers` — two `0.0` float literals at `apps/backend/app/engine/research.py:1435-1436` in `_rsp_rank_key` (J-77 sort-tie sentinels) trip the **No magic numbers** anti-goal blanket guard (which forbids ANY float literal in the engine CALC_FILES).

The iter-20 evaluator recommended this exact lean consolidation. This is NOT a regression (no prior-passing journey broke) and NOT a coherence-fail (iter-20 coherence was PASS) — it is a one-step suite-green fix. J-72/J-75/J-77 stay `failing` in journey-history until the suite flushes `0 failed`. J-22/J-23/J-24 stay honestly blocked-NA (non-vetoing per goal.md "Data-dependent journeys (non-halting)").

**Lessons applied (from `lessons.md` / MEMORY):**
- *iter-20 lesson — these two failures surface ONLY in the FULL suite.* `test_db.py` and `test_no_magic_numbers.py` are full-suite-only guard tests; a targeted module run of `test_iter20_research_cluster.py` will pass while the suite stays red. The fix MUST be confirmed by re-running BOTH guard tests AND the full suite.
- *Backend test suite runtime (~34 min, 639+ tests) — a SUBAGENT cannot finish the full suite (10-min Bash cap + bg job dies on turn-end).* The developer runs the two targeted guard tests directly; the FULL suite is handed to the pump and run nohup-async.
- *Goal pump never block evaluator on suite (iter-11).* The goal-evaluator must NOT wait in-flight for the full suite; it gates GOAL_ACHIEVED candidacy on the FLUSHED terminal `0 failed` summary line, answering the dispatch promptly with "two guard tests green + suite re-run in progress" if the suite is still running.
- *Config fixtures need new required keys.* This fix touches NO config schema — no new required config key is introduced (the `_rsp_rank_key` fix sources a sentinel from an EXISTING config value or restructures the sort; no new `config.yaml` section).

## IN SCOPE

### Backend
- [ ] **Fix `tests/test_db.py` expected-tables set.** Add the new J-72 cache table `event_study_cache` to the expected-tables grouping in `apps/backend/tests/test_db.py` (a new named set, e.g. `RESEARCH_CACHE_TABLES = {"event_study_cache"}`, OR add it to the appropriate existing group), and include it in the `==` comparison in `test_create_all_produces_expected_tables`, with a one-line comment explaining it is the iter-20 standalone J-72 cache table (legitimately mutable cache, explicitly NOT a snapshot — the new-table analog of the documented `_ADDITIVE_COLUMNS` pattern). The `EventStudyCache` table itself is correct and MUST NOT change.
- [ ] **Remove the two `0.0` magic-number-guard hits in `apps/backend/app/engine/research.py:1435-1436` (`_rsp_rank_key`).** These are sort-tie sentinels consulted only AFTER the `is_not_none` boolean already partitions None-last under `reverse=True`, so they never affect the ranking of present values. Fix so NO float literal remains in calc code: either (a) source the NA sort sentinel from a named module-level constant that carries a config-justification comment (the value is structural to the sort, not a tunable scoring weight), or (b) restructure the key so the `(is_not_none, value)` pairing carries no fallback float literal (e.g. rely on the boolean partition + tuple ordering so a `None` need never be replaced by a literal). The DEFAULT ranking and the published study figures MUST stay byte-identical — this is a no-functional-change refactor of the sort key only.
- [ ] Confirm `tests/test_no_magic_numbers.py::test_engine_calc_code_has_no_magic_numbers` and `tests/test_db.py::test_create_all_produces_expected_tables` both pass; confirm the iter-20 research cluster (`tests/test_iter20_research_cluster.py`) still passes (byte-identity + single-batched-read locked).

### Frontend (if applicable)
- None. No served payload changes; no UI surface changes.

### New user-facing capability
None — this is an internal consolidation that makes the full test suite green. The user-facing behavior delivered by J-72/J-75/J-77 in iter-20 is unchanged.

### New information displayed
None.

### New user actions
None.

### UI surface changes
None.

### Product surface delta
No change to the product experience. The J-72 cache, J-75 forward-return columns, and J-77 study built in iter-20 continue to serve byte-identical values; this iteration only removes the two test-suite failures that block confirming them.

### Blueprint conformance
No new surfaces. All J-72/J-75/J-77 pages were registered in iter-20 under existing IA homes (`/stocks`, `/stocks/[ticker]`, `/research`, `/research/samples`) and coherence-confirmed PASS. No nav-skeleton change. The blueprint's IA `[TARGET iter-20]` labels for J-72/J-75/J-77 should be retroactively marked `[built iter-20]` (an additive labelling edit) once the evaluator confirms; no re-approval needed.

### Data-contract additions
None. No new displayed value. The `event_study_cache` table (J-72) and the `regime-setup-pattern` value (J-77) and the per-stock forward-return serving surface (J-75) were all registered in the Data Contract in iter-20. This iteration introduces no second computation or endpoint for any value, and reads no value from a non-canonical source.

## OUT OF SCOPE

- Any change to served payloads, endpoint shapes, or UI components (the iter-20 functional surfaces are correct — do not touch them).
- Any change to `EventStudyCache` (`apps/backend/app/models.py`), `compute_event_study`/`event_study_cached`, `_forward_returns_by_symbol`, `compute_regime_setup_pattern_study`, or `samples.py` cohort logic beyond the `_rsp_rank_key` sort-key sentinel fix.
- Any new feature work or new journey scope.
- Any new `config.yaml` section or new required config key.
- Browser re-QA of J-72/J-75/J-77 served behavior (no served-payload change). A single post-fix re-assertion of J-77 byte-identity via the existing iter-20 cluster test is sufficient because the `_rsp_rank_key` change touches calc code but not output.

## DEFINITION OF DONE

- [ ] `tests/test_db.py::test_create_all_produces_expected_tables` passes (expected-tables set includes `event_study_cache`).
- [ ] `tests/test_no_magic_numbers.py::test_engine_calc_code_has_no_magic_numbers` passes (no float literal in `research.py`).
- [ ] `tests/test_iter20_research_cluster.py` still passes — J-77 default ranking + published figures byte-identical after the `_rsp_rank_key` refactor.
- [ ] The FULL backend pytest suite is re-run (handed to the pump, nohup-async) and its FLUSHED terminal summary line reads **0 failed** — this is the binding gate. Target journeys J-72, J-75, J-77 flip to passing only after this line is confirmed.
- [ ] Required-still-passing journeys remain green (no served-payload change ⇒ no regression; confirm via the suite, not browser).
- [ ] No anti-goal violation introduced; the iter-20 `anti_goal_violations` entry (No magic numbers, `research.py:1435-1436`) is resolved.
- [ ] Unit tests pass; no regressions.
- [ ] Dev handoff written at `docs/handoffs/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-21-dev.md`, explicitly stating whether the full-suite re-run reached `0 failed` (and, if the suite is still in flight at handoff, that the two guard tests + the iter-20 cluster passed and the suite re-run is nohup-async in progress).

## TESTING REQUIREMENTS

- Browser: none required (no served-payload / UI change). Do NOT spend a Chrome MCP session re-smoking unchanged surfaces.
- Unit/integration:
  - `apps/backend/tests/test_db.py::test_create_all_produces_expected_tables` — green with `event_study_cache` in the expected set.
  - `apps/backend/tests/test_no_magic_numbers.py::test_engine_calc_code_has_no_magic_numbers` — green (no float literal in `research.py`).
  - `apps/backend/tests/test_iter20_research_cluster.py` — green (J-77 default ranking + figures byte-identical; J-72 single-batched-read + byte-identity locked).
  - FULL backend suite (`cd apps/backend && .venv/bin/python -m pytest tests/`) — flushed `0 failed`, run via the pump nohup-async (a subagent cannot finish it within the Bash cap).
- Error cases: no new input paths introduced; the existing J-77 4xx validation (unknown view → 422, bad horizon) is unchanged and re-covered by the existing cluster tests.

## NOTES

- This iteration was directly recommended by the iter-20 evaluator (`runs/goal-session-i_can_see_the_wealthy_future_forever_with_my_loved_ones/iter-20/eval.md`, Next-Step Recommendation). It is a lean consolidation: developer → reviewer → (no browser-qa needed). Depth is `lean` — prior verdict was CONTINUE (not ESCALATE), the change is two surgical fixes (one test-fixture set, one sort-key sentinel), and no served behavior changes.
- The two failures surface ONLY in the FULL suite — the developer MUST run both guard tests directly AND hand the full suite to the pump. Do not declare done on a targeted-module pass alone.
- After this lands the suite green with J-72/J-75/J-77 byte-identity/count-coherence still green and coherence PASS, iter-21 is the GOAL_ACHIEVED candidate — these are the last buildable Must-haves. J-22/J-23/J-24 remain honestly blocked-NA (non-vetoing).
- The evaluator must gate GOAL_ACHIEVED candidacy on the FLUSHED `0 failed` line, NOT on an in-flight suite (iter-11 lesson) — answer the dispatch promptly with the guard-tests-green status if the suite is still running.
