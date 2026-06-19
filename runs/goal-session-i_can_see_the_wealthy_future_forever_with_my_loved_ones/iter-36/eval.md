# Iteration 36 Evaluation

**Verdict:** CONTINUE
**Depth Recommendation For Next Iteration:** lean

## Summary

iter-36 fixed the iter-35 J-94 REGRESSION **cause** at the data/API layer: `GET /api/data` is responsive again (~12-16s steady-state, down from the >300s hang) via a new `dataset_version`-keyed `MembershipTimelineCache` + warm-up precompute + a byte-identical cold-miss bound, with every served value byte-identical (review PASS, QA PASS, audit PASS_WITH_GAPS, coherence COHERENCE-PASS). But browser-QA was AUTO-SKIPPED on a "Frontend Present: no" basis (ui-test-results.md = SKIPPED; no evidence dir exists), so there is **no live rendered evidence** the `/data` page now hydrates. Per the strict standing rule, J-94 cannot flip `regressed → passing` and J-96 cannot flip `partial → passing` without positive live render proof — this is the established iter-30→31 / iter-33→34 lean live-re-verify path. NOT a new regression (no prior-passing journey newly broke; the backend diff is value-preserving) and NOT a stall (clear actionable next step), so CONTINUE.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-94 (min-history gate + honest warm-up diagnostic) | regressed | regressed (cause fixed at data layer; live render UNVERIFIED — browser-QA SKIPPED) | dev/QA timed `GET /api/data` ~12-16s HTTP 200; audit B1-B4 byte-identity; **no `-iter-36-evidence/` dir** |
| J-96 (membership timeline + honesty labels) | partial | partial (data deliverable promptly; rendered step function UNVERIFIED live) | `test_data_manager_membership_cache.py` 8/8 GREEN; no live non-skeleton frame captured |
| J-93 (`/stocks` dynamic universe slides 0→544) | passing | passing (carried; fast `/api/stocks` snapshot path unaffected by this `/api/data` fix; backend diff value-preserving) | reports/qa/...-iter-35-evidence/UT-J-93b-stocks-2022-02-01.png |
| J-06 (single-source score consistency) | passing | passing (carried; resolver branch byte-identical — audit B2/B3, 0 mismatches) | reports/qa/...-iter-35-evidence/UT-J-06b-stocks-detail-NVDA.png |
| J-07 (CRITICAL Risk-Off → 0 Actionable) | passing | passing (carried; not touched by any changed line — audit §3) | reports/qa/...-iter-35-evidence/UT-J-07-stocks-risk-off.png |
| J-18 (CRITICAL exactly one date selector) | passing | passing (carried; no frontend diff, no new date state) | reports/qa/...-iter-35-evidence/UT-J-18-backtest-no-date.png |
| J-87 / J-88 (Dashboard Market Phase / P(bear)) | passing | passing (carried; market-phase layer byte-unchanged) | reports/qa/...-iter-35-evidence/UT-J-87-dashboard-market-phase.png |
| J-36 / J-37 / J-39 / J-85 (co-located `/data` journeys) | passing | passing (carried; re-smoke deferred to the lean live pass — browser-QA SKIPPED) | reports/qa/...-iter-34-evidence/UT-J-36/37/39 + iter-34 UT-J-85-rebuild-panel.png |
| J-15 (fast snapshot reads) | already_passing | already_passing (carried; snapshot-served read architecture unchanged) | reports/qa/...-iter-35-evidence/UT-J-15-stocks-speed.png |
| J-22 / J-23 / J-24 (data-walled) | unknown | unknown (blocked-NA, non-vetoing per goal.md lines 105-108) | n/a |

All other Must-haves (J-01..J-92 not listed above) carried `passing`/`already_passing` — out of iter-36 scope; the backend diff is confined to the `/api/data` read path and is value-preserving.

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| No recompute in the read path | OK | The cache deserializes a stored payload; the deterministic derivation is computed once per `dataset_version` (warm-up / bounded cold miss), exactly as the "derived once… persisted/cached, read from storage" clause permits. `test_warm_read_does_not_recompute_timeline` patches `_membership_timeline` to raise and proves the warm read never recomputes. |
| Single source of truth | OK | Cache keyed by the single-sourced `research._dataset_version` (same stamp as `EventStudyCache`/`MarketPhaseCache`); `membership_timeline_cached` wraps the SAME canonical `_membership_timeline`; the resolver `trailing_count` branch is byte-identical to the grouped-count path (audit B2, 0 mismatches; coherence Data-Contract PASS). |
| Snapshots are immutable | OK | `scanner_runs`/`scanner_results`/`*_scores`/`forward_returns` untouched; the new `membership_timeline_cache` is a separate standalone mutable cache table (correctly registered, not subject to immutability / iter-12 `_ADDITIVE_COLUMNS` trap). J-85 `kind:"rebuild"` NOT re-triggered. |
| No lookahead | OK | `trailing_count` and `bars_asof` both bound at date ≤ D; causality asserted through the cache (`test_causality_entries_exits_through_cache`); holds on the scoring path too (audit B3). |
| No fabricated data | OK | Empty DB → empty-but-valid timeline (`test_empty_db_caches_empty_but_valid_timeline`); no synthesized prices/scores. |
| Honest limitations surfaced | OK | The three honesty labels (survivorship / warm-up / universe-relative) carried verbatim in the cached payload (`_membership_labels`), not re-typed. |
| Risk-Off must gate Actionable | OK | J-07 path not touched by any changed line. |
| Exactly one global date selector | OK | Zero frontend diff (`git diff --stat HEAD -- apps/frontend` empty); no new date state. |
| No magic numbers (config-sourced) | OK | `test_no_magic_numbers` GREEN; no new config literal — cache keyed only by `dataset_version`, no inline tunable. The lone ever-recorded violation (iter-20, minor) stays resolved since iter-21. |

No anti-goal violated this iteration. No new entry added to `anti_goal_violations`.

## Coherence

COHERENCE-PASS (`runs/goal-session-.../iter-36/coherence.md`) — `membership_timeline_cached` is a transparent performance wrapper around the registered canonical `_membership_timeline` → `compute_coverage` → `GET /api/data` path; no second computation, no non-canonical source, no new displayed value, no new route/page/nav. No structural veto.

## Full-suite status (not blocking this verdict)

The full backend pytest suite is in-flight on the pump (nohup-async, `/tmp/iter36_full_suite_pump.log`, ~51% at evaluation, NOT yet flushed — no `PYTEST_EXIT`/`EXIT_CODE` line). Exactly ONE `F` appears on the progress lines at ~22% (~ordinal 210), consistent with the documented `test_warmup.py` / `test_data_manager_jobs_pipeline.py` concurrent-QA-backend contention flake on a byte-unchanged path (iter-30/34 precedent), to be re-run isolated before attribution. Per the iter-11/29/30 lesson I do NOT block the verdict on the in-flight suite, and it is not load-bearing here because iter-36 is not a GOAL_ACHIEVED candidate (J-94/J-96 lack live render evidence regardless of the suite).

## Next-Step Recommendation

**iter-37 LEAN live re-verification (NO code rework — backend correct, byte-identity proven, suite gate deferred):**

1. Bring up backend `:8835` (WAIT for `GET /api/health` "ready" — warm-up precomputes the cache; a cold pre-warm `GET /api/data` still pays ~97s by design), frontend `:3835`, Chrome `:9222`; fall back to Playwright if Chrome MCP is down (iter-34 precedent). Use the fast `GET /api/stocks?as_of=` for J-93 re-derivation (slides 0/495/504/544).
2. Browser-QA the two targets on LIVE, md5-distinct, **non-skeleton** evidence (md5sum the dir FIRST; reject any un-hydrated skeleton frame — iter-18/33 precedent; scroll the below-the-fold panels into the viewport and VIEW the pixels): **J-94** = the per-date universe-resolution diagnostic renders (admitted + excluded-by-reason counts at the resolved as-of); **J-96** = the rising membership-timeline step function from ~2021-10-18 with populated Entries/Exits and the three honesty labels.
3. Re-smoke the co-located `/data` journeys **J-36/J-37/J-39/J-85**, re-confirm **J-93** (`/stocks` still slides — fast path), and the CRITICAL **J-18** (0 `input[type=date]`) and **J-07** (Risk-Off → 0 Actionable), plus **J-06** single-source (NVDA list == detail). Confirm the J-94 diagnostic count reconciles with the served `/stocks` membership (the J-06 single-source contract).
4. Gate iter-37's GOAL_ACHIEVED candidacy on the FLUSHED full-suite `0 failed, EXIT 0` line (pump nohup-async; never block the evaluator on the in-flight suite — iter-11/29/30; re-run any single `test_warmup.py` / `test_data_manager_jobs_pipeline.py` `F` isolated before attributing it).

After J-94 re-renders and J-96 flips to passing on live evidence, with COHERENCE-PASS, zero regression, and a GREEN full suite, iter-37 is a sound **GOAL_ACHIEVED** candidate — every buildable Must-have green; J-22/J-23/J-24 stay honestly blocked-NA (non-vetoing per goal.md lines 105-108). Closes open_item `iter35-api-data-timeline-uncached`.

## Halt Justification

N/A — verdict is CONTINUE (the loop continues). Not halting: no new regression (J-94 was already regressed in iter-35; iter-36 fixes its cause), no critical anti-goal, COHERENCE-PASS, and a clear tractable next step (lean live re-verification).
