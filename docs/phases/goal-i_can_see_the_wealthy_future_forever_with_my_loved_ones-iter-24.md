# Goal Iteration 24 — Turn the full backend suite GREEN: reconcile two stale `served == engine_output` byte-equality guards for J-81's additive `forward_returns`

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** i_can_see_the_wealthy_future_forever_with_my_loved_ones
- **Iteration:** 24
- **Mode:** next
- **Depth:** full
- **Frontend Present:** no
- **Target journeys:** J-81, J-82
- **Required-still-passing journeys:** J-03, J-04, J-06, J-09, J-21, J-75
- **Anti-goal reminders:**
  - Single source of truth — every score read identically everywhere (J-06). *(critical)*
  - No recompute in the read path — reads serve persisted-snapshot values; create-once on first view is the only blessed compute. *(critical)*
  - Snapshots immutable — `scanner_runs`/`scanner_results`/`*_scores` never mutated; `forward_returns` separate append-only. *(critical)*
  - No lookahead — as-of-D uses bars ≤ D; forward returns bars > D. *(critical)*
  - No fabricated data — provider failure → explicit error; partial horizons/low samples → NA + n; never synthesized. *(critical)*
  - No magic numbers — horizons/thresholds/edges from `config.yaml`/design tokens (e.g. horizons from `config.walk_forward.horizons`).

## GOAL

Make the full backend pytest suite pass with `EXIT_CODE=0` by reconciling the two stale over-strict byte-equality guards that J-81's legitimate, coherence-approved additive `forward_returns` field broke — with zero change to any served payload, endpoint, or UI.

## BACKGROUND

J-81 (themes/sectors forward-return columns) and J-82 (RSP table NA-last sort + filters + emitted-combination drill-down + Pooled default) landed correct and coherent in iter-23 (browser QA 23/23, COHERENCE-PASS, J-06 byte-identity proven by `test_iter23_leaderboard_returns.py`). The only thing blocking the standing GOAL_ACHIEVED gate — a GREEN full backend suite — is `2 failed, 844 passed, 4 skipped, EXIT_CODE=1`. Both failures are stale `served == engine_output` byte-equality guards in `apps/backend/tests/test_api_engine.py` — `test_api_themes_equals_engine_output` (line 172) and `test_api_sectors_equals_engine_output` (line 27) — that compare the served `/api/themes` & `/api/sectors` payloads byte-for-byte to raw `score_themes`/`score_sectors` engine output; J-81 additively attached a `forward_returns` key (read VERBATIM from the separate `forward_returns` table, byte-identical to Backtest) that the engine score functions never compute. This is the identical iter-20→iter-21 consolidation pattern (a correct additive feature trips a pre-existing blanket guard), and the FIX IS ALREADY PRESENT IN THE SAME FILE: the iter-20 dev updated `test_api_stocks_equals_engine_output` (lines 121-143) to (a) strip `forward_returns` from each served row before the byte-equality assert and (b) separately assert the additive field exists with `[fr["horizon"] for fr in row["forward_returns"]] == list(cfg.walk_forward.horizons)`. This iteration mirrors that exact pattern onto the two themes/sectors guards. Depth is **full** (prior depth was full; the iter-23 evaluator explicitly recommends a full-depth consolidation iteration with the full pytest suite as the binding gate). This is a TEST-ONLY change — no source, served-payload, endpoint, or UI change is expected.

## IN SCOPE

### Backend
- [ ] In `apps/backend/tests/test_api_engine.py`, update `test_api_themes_equals_engine_output` (line 172) so the no-drift byte-equality is asserted on the CANONICAL scored payload modulo J-81's additive `forward_returns` key: strip/pop `forward_returns` from each served theme row before `served == expected`, then SEPARATELY assert each served row carries `forward_returns` with `[fr["horizon"] for fr in row["forward_returns"]] == list(cfg.walk_forward.horizons)`. Mirror the established `test_api_stocks_equals_engine_output` pattern (lines 121-143) verbatim in shape. Keep the existing `len(served["rows"]) == len(cfg.themes)` assertion.
- [ ] In the same file, update `test_api_sectors_equals_engine_output` (line 27) identically: strip `forward_returns` from each served sector row before `served == expected`, then separately assert the additive field exists with the configured horizons per row. Keep the existing `served["benchmark"] == "SPY"` and `len(served["rows"]) == 31` assertions.
- [ ] Re-run the FULL backend pytest suite to confirm `EXIT_CODE=0` (handed to the pump, nohup-async — see NOTES). Confirm exactly the two prior failures are now green and that no other test regressed (target ~846 passed, 4 skipped, 0 failed).

### Frontend (if applicable)
- None. No frontend file changes. This iteration is a backend test-only reconciliation.

### New user-facing capability
None. No user-visible change — the served `/api/themes` and `/api/sectors` payloads (including J-81's `forward_returns`) are byte-unchanged; only the test guards are corrected.

### New information displayed
None.

### New user actions
None.

### UI surface changes
None.

### Product surface delta
None. The product experience is unchanged from iter-23; this iteration removes the only blocker (a red suite) to GOAL_ACHIEVED.

### Blueprint conformance
No new surfaces. The blueprint already registers J-81 under `/themes` + `/sectors` and J-82 under `/research` + `/research/samples` as built and coherent (COHERENCE-PASS iter-23). No blueprint edit is required — this iteration introduces no new displayed value, no new page, and no nav-skeleton change.

### Data-contract additions
None. No new displayed value is introduced. The `forward_returns` value on `/api/themes` and `/api/sectors` is already registered in the Data Contract (the **Per-stock forward returns** row, J-81 [TARGET iter-23], now built) and is served VERBATIM via the SAME `forward_testing:_leadership_returns` builder Backtest uses — never a second computation or endpoint.

## OUT OF SCOPE

- ANY change to source code under `apps/backend/app/` or `apps/frontend/` (no served-payload, endpoint, schema, config, or UI change — the served shape and the J-81 `forward_returns` value are correct and proven byte-identical to Backtest; only the tests are stale).
- Loosening or disabling the no-drift / single-source guarantee: the byte-equality on the CANONICAL scored payload (all scores/ranks/components/breadth/trend/members) MUST remain asserted — only the additive `forward_returns` key is excluded from the equality and then separately asserted to exist with the configured horizons.
- Any new feature, journey, or refactor. J-22/J-23/J-24 remain honestly blocked-NA (data-walled, non-vetoing) and are NOT in scope.
- Browser re-QA of full journeys beyond a light smoke that `/themes` + `/sectors` still serve 200 with the forward-return columns (a test-only change needs no full browser re-run).

## DEFINITION OF DONE

- [ ] `test_api_themes_equals_engine_output` and `test_api_sectors_equals_engine_output` pass, asserting byte-equality on the canonical scored payload (modulo `forward_returns`) AND separately asserting `forward_returns` exists per row with horizons == `config.walk_forward.horizons`.
- [ ] The FULL backend pytest suite passes with `EXIT_CODE=0` (0 failed; the prior 2 failures green; no new failures/regressions; ~846 passed, 4 skipped).
- [ ] Target journeys J-81, J-82 remain passing (unchanged behaviour — served payloads byte-identical; the two tests now correctly accept the legitimate additive surface).
- [ ] Required-still-passing journeys J-03, J-04, J-06, J-09, J-21, J-75 remain green (no served-value change; J-06 single-source byte-identity intact).
- [ ] No anti-goal violation introduced (single source of truth, no-recompute, immutability, no-lookahead, no-fabrication all preserved — verified by the still-asserted canonical byte-equality).
- [ ] No source/UI change (diff is confined to `apps/backend/tests/test_api_engine.py`).
- [ ] Dev handoff written at `docs/handoffs/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-24-dev.md`, explicitly stating the full-suite result and `EXIT_CODE`.

## TESTING REQUIREMENTS

- Browser: light smoke only — confirm `/themes` and `/sectors` still serve and render their five forward-return columns (J-81). No full per-journey browser re-run is required for a test-only change (see NOTES re J-06 already proven by `test_iter23_leaderboard_returns.py`).
- Unit/integration: `apps/backend/tests/test_api_engine.py::test_api_themes_equals_engine_output` and `::test_api_sectors_equals_engine_output` must pass with the corrected guards; the FULL backend suite must reach `EXIT_CODE=0`. The canonical-payload byte-equality (scores/ranks/components/breadth/trend/members) MUST still be asserted — the test must still fail if a genuine score/rank drift were introduced (the reconciliation strips ONLY the additive `forward_returns` key, nothing else).
- Error cases: the corrected tests must still detect real drift — verify by construction that stripping ONLY `forward_returns` (not other keys) leaves every canonical scored field under the `served == expected` assert.

## NOTES

- **This is exactly the iter-20→iter-21 consolidation pattern.** The blessed fix already lives in the same file: `test_api_stocks_equals_engine_output` (lines 121-143) strips `forward_returns` per row, byte-compares the rest, then asserts `[fr["horizon"] for fr in row["forward_returns"]] == list(cfg.walk_forward.horizons)`. Mirror it onto the two themes/sectors guards. Do NOT invent a new approach.
- **Iter-23 evaluator recommendation (verbatim intent):** run a small full-depth consolidation iteration that turns the full backend suite GREEN, then GOAL_ACHIEVED is appropriate; the dev may choose either (a) strip/pop `forward_returns` before the equality + separately assert the field/horizons, OR (b) build `expected` from the served-payload helper path the endpoint actually uses. Option (a) is the mirror of the in-file precedent and is preferred for minimal, surgical change.
- **Lessons that apply (surfaced for dev/reviewer/evaluator):**
  - `backend-test-suite-runtime` — the full pytest suite is ~34 min (639+ tests, heavy walk-forward boot); do NOT run two concurrently; a SUBAGENT can't finish it (10-min Bash cap + bg job dies on turn-end) → the dev runs the two targeted `test_api_engine.py` tests directly to confirm the fix, and HANDS the full suite to the pump.
  - `goal-pump-never-block-evaluator-on-suite` — NEVER make the pump wait for the background full-suite before answering a CLAIMED dispatch; run the suite nohup-async and answer promptly with "targeted fix tests green + full suite re-run in progress" if it isn't done.
  - `goal-pump-background-helpers-need-nohup` — launch the full-suite run via `nohup bash -c '...' &` so it outlives the ~3h wrapper-kill.
  - `dev-server-cleanup-by-port` — never broad `pkill -f` on this multi-project machine; kill by port (no service restart should be needed for a test-only change).
- **GOAL_ACHIEVED gate context:** after this suite is GREEN with zero regressions, every buildable Must-have (J-01..J-21, J-25..J-82) is passing and J-22/J-23/J-24 stay honestly blocked-NA (non-vetoing per goal.md "Data-dependent journeys"). GOAL_ACHIEVED is then the evaluator's call — the goal-decomposer does not declare it.
- **Single-source intent must remain intact:** the reconciliation must NOT weaken the no-drift guarantee. The byte-equality on the canonical scored payload stays; only the additive `forward_returns` key (proven byte-identical to Backtest's `_leadership_returns` in iter-23) is excluded and then separately asserted to exist with the configured horizons.
