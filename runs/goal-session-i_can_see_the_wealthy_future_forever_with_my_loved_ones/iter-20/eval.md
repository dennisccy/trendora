# Iteration 20 Evaluation

**Verdict:** CONTINUE
**Depth Recommendation For Next Iteration:** lean

## Summary

The three target journeys (J-72 event-study perf/cache, J-75 per-stock forward returns, J-77 Regime × Setup × Pattern study) are functionally built and verified: byte-identity, single-batched-read, count-coherence (same-instant, both views), NA honesty, and 4xx error paths all pass; coherence-auditor returned COHERENCE-PASS; review PASS; QA UI-PASS. BUT the authoritative full backend pytest suite (the standing GOAL_ACHIEVED gate from iter-19) is **RED — 2 failed, 831 passed** — both failures introduced by the iter-20 diff: a missing expected-tables entry for the new `event_study_cache` table, and two `0.0` float literals in `research.py` tripping the **No magic numbers** anti-goal guard. The DoD explicitly requires the full suite GREEN, so this is a CONTINUE with a tightly-scoped fix iteration — NOT a GOAL_ACHIEVED candidate yet, and NOT a regression (no prior-passing journey broke; both hits are minor and trivially fixable).

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-72 (event-study perf/cache) | failing | partial | iter-20 test cluster (TC-01..04: byte-identity both views all-windows, single-batched-read, cache-refresh) + TC-19-research-sections.png; functionally correct, but the suite gate (full pytest GREEN) is not met |
| J-75 (per-stock forward returns 1/5/10/20/60d) | failing | passing (functional) | TC-06-stock-detail-forward-returns.png, TC-09-stocks-forward-returns.png, TC-09-sort-1d.png; leaderboard==detail==stored, NA-at-latest, config-driven horizons, view-transform sortable. No suite failure attributable to J-75. |
| J-77 (Regime × Setup × Pattern study) | failing | partial | TC-77-research-page.png + API verified (n=116 study == samples total == len(rows) SAME-INSTANT); count-coherent both views; but its `research.py` enrichment introduced the two `0.0` sort-sentinels that trip the no-magic-numbers guard |
| J-29 (event study) — req-still-passing | passing | passing | TC-20 factor-lab byte-identical; test_research/test_samples 107 passed |
| J-63 (episodes/pooled) — req-still-passing | passing | passing | TC-21: pooled byte-identical to prior; default episodes disclosure |
| J-25/J-26/J-32 (factor lab + as-of mode) — req-still-passing | passing | passing | TC-20 factor-lab identical across calls; as-of scopes pool |
| J-51/J-64/J-65 (samples count-coherence) — req-still-passing | passing | passing | TC-24: test_samples_factor_every_decile_coherence + total_coherence PASSED |
| J-05/J-06 (detail/leaderboard score coherence) — req-still-passing | passing | passing | TC-22: MU 94.5==94.5; test_api_stock_detail_equals_list_row_single_source_j06 PASSED |
| J-21 (Backtest reads stored forward_returns) — req-still-passing | already_passing | passing | TC-23: test_stocks_forward_returns_match_backtest_stored PASSED |
| J-48 (view-transform sorting) — req-still-passing | passing | passing | TC-09 sort re-orders client-side, no refetch |
| J-18 (one date control) — req-still-passing | passing | passing | new study reuses shared horizon/as-of; no page-local date state (review + coherence confirm) |
| J-50 (?asof href stamping) — req-still-passing | passing | passing | N= chips href-stamped via shared SampleLink/useAsOfHref (code-verified; TC-18 SKIPPED on new-tab click only) |

J-72 and J-77 are held at `failing` in journey-history (not flipped to passing) because the binding DoD gate (full suite GREEN) is RED and one of the two suite failures is attributable to J-77's `research.py` changes. J-75 has no suite failure attributable to it but I keep it `failing` for the iteration because the iteration as a whole does not meet its DoD; it flips to passing once the suite is green.

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| No lookahead (critical) | OK | forward returns read verbatim from stored `forward_returns` (bars > D intrinsic); no walk-forward change |
| Single source of truth (critical) | OK | J-75 reads stored rows; leaderboard==detail; coherence PASS |
| No recompute in read path | OK | J-72 serves from `event_study_cache`; J-75 reads stored; J-77 pure grouping (coherence PASS) |
| Research lab read-only / not predictive | OK | descriptive grouping only; survivorship label persists |
| Sample drill-downs count-coherent | OK | study n == samples total SAME-INSTANT both views (TC-12) |
| Episode mode recomputes nothing (J-63) | OK | byte-identical pooled; enrichment additive (TC-10/TC-21) |
| Honest forward-test for partial windows | OK | NA at latest, low_sample flagged (TC-07/TC-13) |
| **No magic numbers** | **VIOLATED (minor)** | `apps/backend/app/engine/research.py:1435-1436` — two `0.0` float literals in `_rsp_rank_key` (sort-tie sentinels) trip `test_no_magic_numbers.py::test_engine_calc_code_has_no_magic_numbers` (blanket-forbids any float literal in CALC_FILES). Not a tunable scoring constant; trivially fixable. NOT marked `(critical)` in goal.md. |
| Exactly one date selector (critical) | OK | new study reuses the single global control; no second date state |
| Snapshots immutable (critical) | OK | cache is a separate create_all table; no scanner_run/result mutated |
| No order/execution path (critical) | OK | none |
| No secrets in source (critical) | OK | none |

Plus a second (non-anti-goal) suite failure: `test_db.py::test_create_all_produces_expected_tables` — the new standalone `event_study_cache` table (correctly architected per coherence) was not added to the expected-tables set. The new-table analog of the iter-12 `_ADDITIVE_COLUMNS` lesson. Test-fixture omission, not a product defect.

## Next-Step Recommendation

Dispatch a **lean** consolidation iteration (iter-21) that fixes EXACTLY these two suite failures and re-runs the full suite to green — no new feature work:

1. **`test_db.py` expected-tables set** — add `event_study_cache` (or `'event_study_cache'`) to the `SNAPSHOT_TABLES` / appropriate expected-tables group in `apps/backend/tests/test_db.py` so `set(SQLModel.metadata.tables.keys()) == ...` includes the new J-72 cache table. (The table itself is correct — coherence-auditor confirmed standalone create_all-managed, no `_ADDITIVE_COLUMNS` needed.)
2. **`research.py:1435-1436` two `0.0` literals** — remove the magic-number-guard hit in `_rsp_rank_key`. These are sort-tie sentinels (only consulted after the `is_not_none` boolean already partitions None-last under `reverse=True`), so the cleanest fix is to source a named module-level constant (e.g. a config-justified `_RANK_NA_SENTINEL` or restructure so no float literal is needed — `key=lambda` with `(is_not_none, value)` where value defaults are pulled from a sourced constant). Confirm `test_no_magic_numbers.py::test_engine_calc_code_has_no_magic_numbers` passes.
3. **Re-run the FULL backend suite (~790 tests) via the pump (nohup background)** and gate iter-21's GOAL_ACHIEVED candidacy on the flushed terminal summary line being **0 failed**. The goal-evaluator must NOT block on the in-flight suite (iter-11 lesson) — gate on the flushed line.

After iter-21 lands the suite green with J-72/J-75/J-77 still byte-identity/count-coherence green and COHERENCE-PASS, iter-21 is the GOAL_ACHIEVED candidate — these are the last buildable Must-haves. J-22/J-23/J-24 stay honestly blocked-NA (non-vetoing per goal.md:2111-2126). No browser re-QA of J-72/J-75/J-77 is needed if iter-21 touches only `test_db.py` + the `_rsp_rank_key` sentinels (no served-payload change) — but the no-magic-numbers fix DOES touch `research.py` calc code, so re-assert J-77 byte-identity (the existing iter-20 cluster test) and re-smoke the J-77 endpoint once after the fix.

## Halt Justification

Not halting. CONTINUE. The product is functionally complete on all three target journeys and all required-still-passing journeys, with COHERENCE-PASS, but the explicit DoD / standing iter-19 gate ("full backend pytest suite GREEN") is RED on two minor, iter-20-introduced failures (a missing expected-table entry and a no-magic-numbers blanket-guard hit on two sort sentinels). Neither is a critical anti-goal violation (no secrets, no paid SaaS, no lookahead, no immutability/single-source/order-path breach) and neither regresses a prior-passing journey, so this is not a REGRESSION halt — it is a one-step fix that the next lean iteration closes, after which iter-21 becomes the GOAL_ACHIEVED candidate.
