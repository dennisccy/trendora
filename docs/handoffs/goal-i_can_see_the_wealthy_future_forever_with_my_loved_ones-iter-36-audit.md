# goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-36 Audit Report

**Date:** 2026-06-19
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

The iter-36 read-path performance fix is implemented correctly and surgically: `GET /api/data` is made responsive (>300s hang → ~12-16s steady-state, 97s bounded cold miss) by caching the J-96 membership timeline behind a standalone `dataset_version`-keyed table, exactly mirroring the J-72/J-87 cache precedent, with **no change to any served value**. I independently confirmed the central byte-identity claim — the new context-active `trailing_count` resolver branch produces byte-identical `admitted` / `excluded_counts` / `resolutions` (incl. per-symbol bar counts) versus the original grouped-count path across multiple as-of dates (0 mismatches) — and the targeted unit suite (9 tests) is green on my own run. The two GAPS are both downstream pipeline gates the auditor cannot close and that are NOT code defects: (a) the spec's DoD live browser re-verification of J-94/J-96 has not yet executed (the pipeline is at `ux_regression_complete`; browser QA and the goal-evaluator run after this audit), and (b) the full backend pytest suite is still in-flight on the pump (nohup-async), which by spec design gates the evaluator, not the audit.

---

## 2. Findings

### Backend Findings

**B1 — OBSERVATION (verified): The membership-timeline cache faithfully follows the J-72/J-87 precedent.**
`MembershipTimelineCache` (`apps/backend/app/models.py:516-558`) is a standalone `create_all`-managed table keyed uniquely on `dataset_version`, mirroring `EventStudyCache` / `MarketPhaseCache`. `membership_timeline_cached(...)` (`apps/backend/app/engine/data_manager.py:541-594`) reads on the current `_dataset_version` stamp, returns the stored payload on hit, computes-once + prunes-stale + upserts on miss. The stamp is the single-sourced `research._dataset_version(session)` (`apps/backend/app/engine/research.py:1229-1244`) — `max(scanner_runs.id)` + `forward_returns` row count — so the cache invalidates in lockstep with the other two caches on any dataset change. No import cycle (`research.py` does not import `data_manager`; confirmed by grep). This is a permitted cache of a deterministic read-only derivation, not a recompute — anti-goal held.

**B2 — OBSERVATION (verified): The resolver `trailing_count` branch is byte-identical to the grouped-count path.**
`resolve_with_reasons` (`apps/backend/app/engine/universe_resolver.py:140-150`) now sources per-symbol trailing-bar counts from `active_bar_cache(session).trailing_count(...)` (`apps/backend/app/engine/prices.py:106-119`) when a `bar_cache`/`prefilled_bar_cache` context is active, and from the original `func.count(DailyPrice.id)` grouped query otherwise. The default (no-context) path is byte-for-byte unchanged (verified against `git diff` — the `else` branch is the original query verbatim). `trailing_count` is `bisect_right(dates_<=_asof)` over the once-loaded full series; because `(symbol, date)` is unique (`test_db.py::test_daily_prices_has_unique_symbol_date_constraint`), the bisect count equals the row count exactly. **I independently verified this**: a throwaway run over a synthetic DB (8 real pool symbols, varied history lengths straddling `min_history_bars`, 5 as-of dates) produced `admitted` / `admitted_count` / `excluded_counts` AND the full `resolutions` list byte-identical between the context-active and no-context paths — 0 mismatches.

**B3 — OBSERVATION (verified): The change is value-preserving on the SCORING path, not only the timeline path.**
`run_scan` (`scanner.py:255`) runs inside `with bar_cache(session)`, and `score_stocks` → `resolve_members` → `resolve_with_reasons` (`scoring.py:249`) executes within that context — so during warm-up's cadence loop and any `run_scan`, the resolver now takes the new `trailing_count` branch. Because B2 proves byte-identity (including the per-symbol `bars` count that feeds the price/ADV gates), the resolved/persisted membership is unchanged — the *Single source of truth* and *No-lookahead* critical anti-goals are preserved on the scoring path too. (`trailing_count` reads only bars with date ≤ D, so causality is intact.)

**B4 — OBSERVATION (verified): The in-fix `compute_coverage` dedup is byte-identical across all branches.**
`compute_coverage` (`data_manager.py:642-645, 691`) passes the already-resolved latest-date `admitted` list to `_coverage_diagnostic_absent(universe=...)` only when `resolved["asof"] == max(ScannerRun.asof_date)`, eliminating one redundant ~8s resolve. I traced `_resolve_coverage_asof` (`data_manager.py:305-315`): the `None` fallback resolves to `max(ScannerRun.asof_date)` (the same latest run date), so the reused admitted set equals what `_coverage_diagnostic_absent(universe=None)` would resolve. When the page as_of differs from the latest run, `absent_universe=None` and J-85 resolves independently (its contract unchanged). The wholly-empty-DB and bars-but-no-runs edge cases both fall through to `absent_universe=None` (no incorrect reuse). Dev's live verification corroborates (`absent_count 0, universe_count 544` identical both ways).

**B5 — OBSERVATION: Cold-miss compute is bounded but still O(dates).**
The cold (cache-miss) path still iterates ~1369 dates inside `prefilled_bar_cache`, measured at 97s on the live DB (down from ~240s, under the 300s budget). It is only reachable in the narrow window between boot and warm-up-precompute completion. Disclosed honestly in the dev handoff and implementation summary. Acceptable; not a defect.

### Frontend Findings

**F1 — GAP: Live browser re-verification of J-94/J-96 has not executed at audit time.**
The spec DoD and TESTING REQUIREMENTS explicitly require J-94/J-96 to pass via browser-qa-agent on LIVE, md5-distinct, non-skeleton evidence, plus a re-smoke of J-36/J-37/J-39/J-85 and the CRITICAL J-18/J-07/J-93. `status.json` shows `browser_checks_run: false` and `current_step: ux_regression_complete`; no `*-iter-36-evidence/` directory or browser-qa report exists yet. The UI-visibility artifacts (`ui-surface-map`, `ui-test-results`, `user-visible-changes`, `what-to-click`) are all marked N/A / SKIPPED on the "Frontend Present: no" basis — but plan.md explicitly warned NOT to skip browser QA, since the user-visible regression being fixed is the hydration of an existing page. This is a downstream pipeline gate (browser QA + goal-evaluator run after the auditor in goal mode); it is the goal-evaluator's responsibility to confirm, and it cannot be closed by the auditor. The *served-value* correctness that determines whether the page CAN hydrate is fully verified (B1-B4 + dev's live HTTP `GET /api/data` 200, 1369 points, 3 honesty labels, ~12-16s). Recorded as a GAP for the evaluator to close, not a code defect.

### Test Findings

**T1 — OBSERVATION (verified green): Targeted unit tests are tight and pass.**
`apps/backend/tests/test_data_manager_membership_cache.py` (8 tests) asserts exact values: cross-session byte-identity vs a fresh `_membership_timeline` (`test_cached_timeline_byte_identical_to_fresh_compute`), warm==cold, no-recompute-on-hit (patches `_membership_timeline` to raise — proves the read path never recomputes), single-row-under-version, invalidation on BOTH stamp components (snapshot add AND forward-return add), exact entries/exits/size causality, and empty-DB empty-but-valid. I ran `test_data_manager_membership_cache.py` + `test_db.py::test_create_all_produces_expected_tables` myself: **9 passed in 8.41s**. QA's larger targeted run reported 19/19 (incl. `test_no_magic_numbers`).

**T2 — GAP: Two slow `loaded_engine`/`warmed_engine` tests deferred to the pump's full suite.**
The 2 new `test_warmup.py` tests (`test_warmup_precomputes_membership_timeline_cache`, `test_membership_timeline_cache_warm_failure_is_nonfatal`) and the pre-existing iter-33 `loaded_engine` byte-identity tests (`test_scores_byte_identical_for_resolved_membership`, `test_resolved_membership_persisted_rows_match_members`) were not run by the dev/QA under the Bash cap (multi-minute slow boot). I reviewed the two warmup tests (`test_warmup.py:210-266`): the assertions are tight (exactly one cache row under the FINAL stamp, byte-identical to a fresh compute; non-fatal failure → job still `ok`, failure logged, no garbage row written, server recovers on un-patch). Their byte-identity property is independently and more strongly proven on real paths by B2/B3. Per spec/operator note, the full suite is run nohup-async by the pump and the evaluator gates GOAL_ACHIEVED on the flushed `0 failed, EXIT 0` line — I correctly did NOT run the ~34min suite myself (it exceeds the Bash cap). The pump log (`/tmp/iter36_full_suite_pump.log`) was still in-flight at audit time. This is the standard iter-11/29/30 arrangement, not a defect.

**T3 — OBSERVATION: No test directly asserts trailing_count == grouped-count on the resolver path.**
The new tests prove timeline byte-identity, but both the "fresh" and "cached" comparands run inside `prefilled_bar_cache`, so they do not by themselves prove the context-active branch equals the no-context branch. I closed this gap manually (B2, 0 mismatches). A small dedicated unit test pinning `resolve_with_reasons(no-context) == resolve_with_reasons(prefilled context)` on a synthetic DB would harden this for the future; non-blocking.

---

## 3. Domain Assessment

The core domain logic is correct and the implementation respects every critical anti-goal:

- **No recompute in the read path** — the warm read deserializes a stored payload; recompute happens once per `dataset_version` (in warm-up or a bounded cold miss), exactly as the "derived once… persisted/cached, read from storage" clause permits. The no-recompute property is directly tested (`test_warm_read_does_not_recompute_timeline`).
- **Single source of truth** — the J-96 timeline reads the persisted `ScannerResult` membership (the canonical scored sets); the resolver mechanism change (B2/B3) is value-preserving, so no view diverges. The cache stamp is single-sourced via `research._dataset_version` (never duplicated).
- **Snapshots immutable** — `scanner_runs` / `scanner_results` / `*_scores` / `forward_returns` are untouched; the cache is a separate standalone mutable table (correctly NOT subject to the immutability anti-goal or the iter-12 `_ADDITIVE_COLUMNS` trap).
- **No lookahead** — `trailing_count` and `bars_asof` both bound at date ≤ D; causality is asserted through the cache (`test_causality_entries_exits_through_cache`) and holds on the scoring path.
- **No fabrication / honesty labels** — empty DB → empty-but-valid timeline (tested); the three honesty labels (survivorship / warmup / universe_relative) are carried verbatim in the cached payload (`_membership_labels`, `data_manager.py:441-468`), not re-typed.
- **Risk-Off gate (J-07) and single date selector (J-18)** — not touched by any changed line.

The fix is minimal (294 insertions / 18 deletions across 7 files + 1 new test file), reuses an established abstraction rather than inventing one, and introduces no scope creep, no new endpoint, no new displayed value, and no new config literal. The gitignored DB backup (`trendora.db.pre-iter35-rebuild.bak`) is untracked and must not be committed (security baseline; the release-manager should respect `.gitignore`).

---

## 4. Fixes Applied During This Audit

None. No CRITICAL or IMPORTANT issues were found; the implementation is correct as written. The two GAPS (F1 live browser verification, T2 full-suite flush) are downstream pipeline gates the auditor cannot and should not close, not code defects.

| # | Severity | File | Change |
|---|----------|------|--------|
| — | — | — | No fixes required |

---

## 5. Recommended Next Step

Proceed to the remaining goal-mode gates. Specifically:

1. **Browser QA (browser-qa-agent)** must run against the live `/data` page to satisfy the DoD: J-94 per-date coverage diagnostic + J-96 rising step function (Entries/Exits + 3 honesty labels) on md5-distinct, non-skeleton evidence, plus a re-smoke of J-36/J-37/J-39/J-85 and a re-confirm of the CRITICAL J-18 (0 `input[type=date]`) and J-07 (Risk-Off → 0 Actionable), and J-93 (`/stocks` slides 0→544). The UI-visibility artifacts marking this SKIPPED on the "Frontend Present: no" basis are too narrow — the regression being fixed is page hydration, so the browser re-verification is required by the spec and must not be skipped.
2. **Full backend pytest suite** (in-flight on the pump, nohup-async): the goal-evaluator must gate the GOAL_ACHIEVED candidacy on the FLUSHED `0 failed, EXIT 0` terminal line, never on the in-flight suite (and re-run any single `test_warmup.py` / `scanner_runs`-touching `F` in isolation before attributing it to this iteration). An `exit=137` on the nohup wrapper is the known harness-kill, not a test failure.

The code is correct and the served values are byte-identical; once the live J-94/J-96 evidence is captured and the full suite flushes green, this iteration is a sound GOAL_ACHIEVED candidate (J-22/J-23/J-24 stay honestly blocked-NA, non-vetoing). Closes open_item `iter35-api-data-timeline-uncached`.
