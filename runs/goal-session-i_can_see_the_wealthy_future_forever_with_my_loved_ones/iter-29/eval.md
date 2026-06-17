# Iteration 29 Evaluation

**Verdict:** CONTINUE
**Depth Recommendation For Next Iteration:** full

## Summary

The foundational market-phase cluster J-87 (Dashboard Market Phase & Severity panel) and J-88 (deterministic filtered P(bear)) both shipped and verify passing with primary, evaluator-viewed evidence. The implementation is a clean, strictly-causal, read-only additive layer (new `market_phase` engine + cached `GET /api/market-phase` + Dashboard panel) that recomputes no canonical value and alters no gate; coherence is COHERENCE-PASS, review/QA PASS, and I independently re-ran the load-bearing anti-goal tests GREEN. This is NOT a GOAL_ACHIEVED candidate: goal.md was extended through J-96, and J-89..J-96 remain unbuilt (`failing`, no positive evidence) per the iter-22 lesson.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-87 (Market Phase & Severity panel) | failing (unbuilt) | passing | reports/qa/.../iter-29-evidence/UT-05-bear-red-badge-2022-10-07.png (also UT-01, UT-16, UT-07) |
| J-88 (filtered P(bear) + observation vector) | failing (unbuilt) | passing | reports/qa/.../iter-29-evidence/UT-06-observation-chips.png (also UT-05, UT-07) |
| J-01 (Daily dashboard) | passing | passing | iter-29-evidence/UT-01-market-phase-card.png |
| J-06 (Score/regime coherence) | passing | passing | iter-29-evidence/UT-12-13-regime-coherence-2024-12-31.png |
| J-07 (Risk-Off gates Actionable) | already_passing | already_passing | iter-29 QA TC-17 (/stocks?asof=2022-03-15 zero Actionable) |
| J-13 (Browse past date) | passing | passing | iter-29-evidence/UT-10-asof-update-no-reload.png |
| J-18 (One date control — CRITICAL) | passing | passing | iter-29-ui-test-results.md UT-09 + source grep |
| J-43 (?asof serialization) | passing | passing | iter-29-evidence/UT-10-asof-update-no-reload.png |
| J-44 (major-indexes & regime card) | passing | passing | iter-29-evidence/UT-12-13-regime-coherence-2024-12-31.png |
| J-49 (indexes full-history marker) | passing | passing | iter-29-evidence/UT-12-13-regime-coherence-2024-12-31.png |
| J-50 (?asof survives nav) | passing | passing | iter-29-ui-test-results.md (Browser Checks) |
| J-72 (event-study cache shared `_dataset_version`) | passing | passing | source: market_phase.py reuses research._dataset_version |
| J-89..J-96 (queued buildable extension) | (new) | failing (unbuilt) | none — no positive evidence |
| J-22 / J-23 / J-24 | unknown | unknown | blocked-NA, data-walled, non-vetoing (goal.md lines 105-108) |

All other Must-haves J-02..J-86 carry passing/already_passing (not in iter-29 scope; the diff is provably additive — no canonical engine touched).

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| No lookahead (≤ D) | OK | Engine uses `bars_asof` (date ≤ D) for trailing-peak/time-underwater; filter consumes only observations ≤ D. Evaluator ran `test_no_lookahead_tail_invariance` + `test_filter_causality_past_value_unchanged_by_later_observation` GREEN. |
| Single source of truth | OK | `market_phase.py:146` reads `ScannerRun.regime_score` VERBATIM; no `score_regime`/`compute_regime` call (grep-confirmed + coherence Part A). New endpoint; no existing `*_equals_engine_output` guard tripped. |
| No recompute in read path | OK | Computed-once-per-resolved-as-of, cached behind shared `research._dataset_version` stamp; cache byte-identity + refresh-on-change tested. |
| No magic numbers | OK | `market_phase.py` added to `CALC_FILES`; evaluator ran `test_no_magic_numbers` GREEN. All weights/edges/thresholds/VIX-gate/transition-matrix/emissions in config.yaml. |
| No fabricated data | OK | UT-07 (2021-01-05) shows explicit NA honest empty state (no severity/phase/probability); `test_na_when_insufficient_benchmark_history` GREEN. |
| Risk-Off must gate Actionable | OK | QA TC-17: 2022-03-15 zero Actionable; gate-invariance test in the API/seed suite. The panel changes no gate. |
| Scores must be explainable | OK | 5-row named component breakdown rendered (UT-02); `test_components_breakdown_disclosed_and_explainable` GREEN. Never a bare number. |
| Exactly one date selector (CRITICAL) | OK | Panel has only `data`/`status` useStates, reads `useAsOf()`; NO new date state, NO window/document/keydown listener (grep + UT-09). |
| Snapshots are immutable | OK | New standalone `MarketPhaseCache` table (registered in test_db.py); NO new column on scanner_runs/scanner_results/forward_returns; NO rebuild triggered. |
| No order/execution path | OK | Read-only descriptive panel; no brokerage/order code. |
| Honest limitations surfaced | OK | Observation count disclosed ("SHOWING LATEST 60 OF 1170"); macro/FRED leg honestly omitted (J-92 deferred); config weights-sum validator rejects malformed config at load. |
| (Severity weights sum ~1.0 validator) | OK | config.yaml weights sum 1.0 (TC-13); `test_severity_weights_must_sum_to_one` + complete/edges/transition/emission validation GREEN. |

The lone ever-recorded violation (iter-20 minor magic-number in `_rsp_rank_key`) remains RESOLVED since iter-21. No new anti-goal violation introduced.

## Next-Step Recommendation

Run the **J-89 + J-90** cluster at **FULL** depth — both consume the J-87/J-88 market-phase layer built this iteration. J-89 = market-phase history timeline + the fenced retrospective/SMOOTHED view (the smoothed/full-sample probability that was deliberately kept off the live causal path this iteration — it must be behind a clear future-aware marker per the J-49 precedent, never feeding an as-of value). J-90 = recovery-turn signal + downtrend-exit edge study. Both are offline-provable against the committed 2021-2026 seed (the 2022 bear + `^VIX`); neither is data-walled. After that: J-91 (downtrend-conditioned opportunity study), J-92 (FRED macro feed + MacroSeries table) at full depth, then the J-93/J-94/J-96 dynamic point-in-time universe cluster with J-95's data-dependent/non-halting envelope.

Required-still-passing for J-89/J-90: J-87/J-88 (the consumed layer must stay byte-identical and causal), J-06/J-07 (no canonical regime/gate change), J-18/J-43/J-50 (single date selector + ?asof), J-72 (shared cache machinery).

Suite-gate (iter-11 lesson): the full backend pytest suite (~908 items, ~34min+ on this daily-history host) is the standing GOAL_ACHIEVED gate but is NOT load-bearing for a non-candidate iteration. Hand it to the pump nohup-async and gate the next evaluator on the FLUSHED `0 failed` line — never block the evaluator dispatch on the in-flight suite. NOTE: iter-29's `/tmp/mp_full_suite.log` shows `exit=137` (operational SIGKILL of the nohup wrapper, not a test failure — the known background-helper harness-kill); the load-bearing targeted tests were independently re-run GREEN by this evaluator, which is sufficient for a non-candidate iteration. When J-89..J-96 are all built, ensure the full suite actually reaches a flushed `0 failed, EXIT 0` (launch via `nohup` per the helper-needs-nohup lesson) before the GOAL_ACHIEVED candidacy.

Evidence-hygiene for the next QA: iter-29 was clean (TC-01 was a 6.4KB near-blank capture but the UT-* full-viewport frames are all real and byte-distinct). md5sum the dir first; the market-phase panel sits below the fold on the Dashboard (~1060px) — scroll it into view and VIEW the pixels.

## Halt Justification (if halting)

N/A — not halting. CONTINUE: J-87/J-88 newly passing (progress), zero regressions, COHERENCE-PASS, and tractable buildable Must-haves (J-89..J-96) remain.
