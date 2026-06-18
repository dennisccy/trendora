# goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-33 Audit Report

**Date:** 2026-06-18
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS

Iter-33 genuinely delivers the dynamic point-in-time universe cluster (J-93/J-94/J-96) plus the data-walled J-95 envelope and the one-line stale-guard consolidation. I verified the keystone behavior by reading the actual code and re-running the critical tests (resolver, no-magic-numbers, stale guard, the fast synthetic iter-33 suite, and the `loaded_engine` byte-identity/persisted-rows tests — all green, exit 0); every anti-goal invariant (no-lookahead, single source, no magic numbers, immutable seed, Risk-Off gate, exactly-one-date-selector) is enforced in backend logic, not just claimed. No CRITICAL or IMPORTANT issue was found; the residual items are documented GAPs/OBSERVATIONs, none compromising the phase goal.

---

## 2. Findings

### Backend Findings

**B1 — OBSERVATION (observation): `_coverage_diagnostic_absent` resolves a second time inside `compute_coverage`**
`apps/backend/app/engine/data_manager.py:608` calls `_coverage_diagnostic_absent(session, cfg)` WITHOUT passing the already-resolved `universe=` list, so it internally re-resolves the universe at the latest snapshot date (`data_manager.py:364-365`). The function's own docstring (`:357-365`) anticipates the caller passing `universe` "so it is resolved ONCE per coverage call." This is a minor perf duplication, NOT a correctness bug: the J-85 "absent from latest snapshot" diagnostic is semantically pinned to the *latest snapshot date* (not the viewed `as_of`), so resolving it independently is correct — the banner must always describe the latest snapshot regardless of which historical as-of the user is viewing. No fix applied (OBSERVATION only; the resolver's grouped-count short-circuit keeps the cost bounded, and the handoff already documents the ~2-min warm-up cost).

**B2 — OBSERVATION (observation): `methodology.resolved_size` kept as the static candidate-universe count**
`apps/backend/app/engine/methodology.py:150` sets `resolved_size = len(config.universe.symbols)` (the static candidate-universe size), not the members-resolved-at-D. The plan (line 36-41) phrased this as "report members-resolved-at-D," but the spec body (`spec` IN SCOPE) also frames `/methodology` as describing the *rule*, not a snapshot. The implementation's choice is defensible and explicitly documented: `per_date_rule` (`methodology.py:154-161`) states the per-date rule from config (no magic number), the market-cap criterion is honestly documented as the candidate-pool screen (dropped per-date, never silently asserted), and the as-of-DEPENDENT resolved count is correctly served on `GET /api/data` (`universe_count`), where the J-22 invariant (`universe_count == members-resolved-at-D`) actually lives. The canonical contract is satisfied on the canonical surface; methodology describes the rule. No drift, no recompute, single source preserved. No fix needed.

**B3 — GAP (gap): J-95 real backward-history fetch + point-in-time constituent feed remain data-walled (by design)**
The real earlier-start (e.g. 2020) EOD fetch and the true point-in-time index-constituent feed are honestly recorded blocked-NA, non-halting — exactly as the spec's OUT OF SCOPE and Data-dependency notes require (the J-22/J-44-DIA contract). The offline legs ARE built and verified: the confirm-gated control (`BackwardHistoryPanel` + modal), the survivorship label (`pool_survivorship()`, `basis: "current_constituent"`, `point_in_time_feed_available: false`), the seed-undeletable clear (`clear_snapshot_set` hard-asserts `bars_before == bars_after`), and the resolver resolving earlier dates once bars land. This is a documented, non-vetoing limitation — not a defect.

### Frontend Findings

**F1 — OBSERVATION (observation): J-18 (exactly-one-date-selector, CRITICAL) statically preserved**
Direct grep of the two changed pages (`apps/frontend/app/data/page.tsx`, `apps/frontend/app/stocks/page.tsx`): zero `type="date"` inputs (the only match is a historical-context code comment at `data/page.tsx:137`), zero `keydown`/`addEventListener`, and the only `useState` touching "Date" is `Date.now()` for a clock tick (`data/page.tsx:2132`) — not a date selector. All three new panels read the single global `useAsOf()` (`data/page.tsx:205`), which re-fetches `GET /api/data?as_of=` on as-of change. J-18 holds.

**F2 — OBSERVATION (observation): honest empty-universe state is genuinely distinct from filter-empty**
`apps/frontend/app/stocks/page.tsx:545-556` renders a dedicated warm-up empty state when `rows.length === 0` ("The point-in-time universe is honestly EMPTY at this as-of … No rows are fabricated …"), distinct from the filter-empty state (`:558+`, `visible.length === 0`). The three honest labels (survivorship / warm-up / universe-relative) are surfaced verbatim from the backend with test-ids (`timeline-label-survivorship/-warmup`, `data/page.tsx:1054-1071`) — the UI re-types none of the honesty copy.

### Test Findings

**T1 — OBSERVATION (observation): resolver no-lookahead is proved by genuine tail-invariance, not a shortcut**
`tests/test_universe_resolver.py::test_resolve_no_lookahead_tail_invariance` (`:150-173`) builds a full series (bars past D) AND a truncated series (only bars ≤ D) in two separate DBs and asserts `full == trunc` on BOTH `admitted` and the full `resolutions` list — the real anti-goal proof, not a `date <= D` re-statement. Verified passing (exit 0). The warm-up boundary, first-qualifying-date entry, gate-order (history→price→ADV), and per-reason exclusion counts are all asserted with exact values.

**T2 — OBSERVATION (observation): additive-key guard reconciliations are correct, not accident-masking**
The stale `test_get_data_overview_shape` was changed to a superset compare (verified passing). The `members` wrapper key `score_stocks` now returns is stripped before the byte-equality in `test_api_engine.py::test_api_stocks_equals_engine_output` (`:147`), with the canonical payload asserted byte-for-byte (`:160`) and the membership asserted separately (`:169-170`) — the proper iter-20/23/32 reconciliation. The migrated count-contract guards single-source the expected count via `resolve_members(...)` (e.g. `test_scanner.py:96-97`, `test_scoring.py:39`), so they assert "scanner persisted exactly the resolved membership," not a magic literal. `test_scoring.py::test_earliest_date_universe_is_honestly_empty_warmup` asserts `rows == []` and `members == []` at the earliest date (no fabrication).

**T3 — GAP (gap): full ~945-test suite GREEN line not independently re-confirmed by the auditor**
The spec names the flushed full-suite `0 failed, EXIT 0` as the GOAL_ACHIEVED gate; the `/tmp/iter33_full_suite.log` is gone (the documented background-helper harness-kill / `/tmp` log-loss pattern). I independently re-ran every fast-and-targeted module the migration touches (resolver, no-magic, stale guard, the 8 iter-33 tests incl. `loaded_engine` byte-identity, and the fast guard-migration modules) — all GREEN. The dev/QA evidence records the affected-modules group at 206 passed / 3 skipped. The full-suite GREEN line is the evaluator's gate to confirm before declaring GOAL_ACHIEVED; it is not a defect, and nothing in the audit evidence suggests a regression. Recommend the evaluator confirm the re-run's flushed `0 failed` line per the iter-11/29 operational note.

---

## 3. Domain Assessment

The core domain logic is correct and faithful to the no-lookahead, single-source, point-in-time contract:

- **Resolver (`universe_resolver.py`)** reads only `bars_asof` (`prices.py`: `date <= d`), gates in a fixed deterministic order (history → price → ADV) so the recorded exclusion reason is the first unmet criterion, drops market cap per-date (current-only scalar — correctly avoided as lookahead/fabrication), and carries zero threshold literals (confirmed in `test_no_magic_numbers.CALC_FILES:52`). The grouped-count short-circuit for un-fetched pool names is byte-equivalent to per-candidate resolution (same gate order, same admission). I confirmed `min_history_bars=200 ≥ adv_window_days=63`, so the ADV window is always full when the ADV gate is reached — no silent partial-window distortion.
- **Universe-source repoint** is clean: `score_stocks` iterates `resolve_members(session, asof)` in passes 1 and 3 (`scoring.py:297,321`), returns the additive `members`, and touches no scoring formula. `forward_symbols_for_run` = that run's stored `ScannerResult` tickers ∪ benchmarks, keeping the `close_on`/`bars_after` boundary byte-identical and benchmarks present on every run.
- **`universe_count` migration** is single-sourced: resolved once per coverage call (`compute_coverage` `:565`), with `candidate_pool_count` and `candidate_universe_count` carried beside it; the J-22 invariant is re-expressed as members-resolved-at-D on the canonical `/api/data` surface.
- **J-94/J-96 derivations** are read-only over stored bars + the persisted `ScannerResult` membership; the timeline is strictly causal (each date from its own ≤ D snapshot; BBB re-appearance correctly NOT a new entry — asserted) and deterministic (byte-identical across two calls — asserted).
- **Immutability** holds: `clear_snapshot_set` deletes only the snapshot layer (whole-row deletes, never an in-place UPDATE) and hard-raises if `bars_before != bars_after`; the committed price seed is un-deletable.
- **Honesty** is surfaced, not hidden: empty/warm-up universes render explicit honest states; the survivorship label states residual pool-survivorship plainly; the data-walled fetch is blocked-NA, never fabricated.

The byte-identity test (`test_scores_byte_identical_for_resolved_membership`, verified passing via `loaded_engine`, exit 0) confirms no canonical score/return/bucket changed — only which names are scanned.

---

## 4. Fixes Applied During This Audit

None. No CRITICAL or IMPORTANT issue was found. All findings are GAP (documented, non-blocking) or OBSERVATION (informational). Per the auditor rules, GAPs and OBSERVATIONs are documented, not fixed, and working implementations are not rewritten.

| # | Severity | File | Change |
|---|----------|------|--------|
| — | — | — | No fixes required |

---

## 5. Recommended Next Step

Proceed. Iter-33 achieves its goal: the scanned universe is honestly point-in-time, the membership timeline + per-date diagnostic explain it on the existing `/data` home, and every CRITICAL anti-goal invariant is enforced in backend logic and verified by tight tests. Before the goal-evaluator declares the GOAL_ACHIEVED candidacy, it should confirm the flushed full-suite `0 failed, EXIT 0` line from the (re-)run per the iter-11/29 operational note (T3) — the audit found no evidence of any regression, and J-22/J-23/J-24 plus the J-95 real-fetch/constituent-feed legs correctly stay honestly blocked-NA (non-vetoing).
