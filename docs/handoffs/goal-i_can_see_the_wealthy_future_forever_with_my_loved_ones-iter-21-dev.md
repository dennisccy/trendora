# goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-21 Dev Handoff

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-21
**Date:** 2026-06-15
**Agent:** developer
**Status:** complete

## What Was Built

A lean, internal consolidation iteration — two surgical fixes that turn the standing iter-19 DoD gate (the full backend pytest suite) GREEN by resolving the exactly-two iter-20-introduced failures. **No served payload changed; no UI surface changed; no endpoint shape changed.** This unblocks confirmation of J-72, J-75, and J-77 (built functionally-correct in iter-20).

1. **`tests/test_db.py` expected-tables set** now includes the iter-20 standalone J-72 cache table `event_study_cache`. Added a new named group `RESEARCH_CACHE_TABLES = {"event_study_cache"}` (with a one-line comment documenting it as legitimately-mutable derived/cache state — explicitly NOT a snapshot, the new-table analog of the documented `_ADDITIVE_COLUMNS` pattern) and included it in the `==` comparison in `test_create_all_produces_expected_tables`. The `EventStudyCache` model itself (`apps/backend/app/models.py`) was NOT touched.

2. **The two `0.0` magic-number-guard hits in `_rsp_rank_key` (`apps/backend/app/engine/research.py`)** are removed. These were sort-tie sentinels consulted only between two rows that BOTH have a `None` metric (the `(is_not_none, value)` boolean already partitions present-before-None under `reverse=True`). The fix uses spec option (b): the `None` fallback now reuses the `is_not_none` boolean flag itself — a structural, non-float comparable that equals itself for a both-None pair and is NEVER cross-compared against a float (a differing first tuple element short-circuits the comparison). This carries **no float literal** in calc code, and the DEFAULT ranking + published J-77 study figures stay **byte-identical** (proven by a new test — see below).

## Files Changed

- `apps/backend/app/engine/research.py` — `_rsp_rank_key`: replaced the two `0.0` float-literal NA sentinels with the structural `is_not_none` boolean fallback (no-functional-change sort-key refactor; no float literal remains anywhere in the file). Docstring updated to explain why the fallback is structural, not a tunable.
- `apps/backend/tests/test_db.py` — added `RESEARCH_CACHE_TABLES = {"event_study_cache"}` and included it in the `test_create_all_produces_expected_tables` expected-tables union.
- `apps/backend/tests/test_iter20_research_cluster.py` — added `test_j77_rsp_rank_key_refactor_orders_identically_to_legacy`: a byte-identity oracle that pins the literal-free `_rsp_rank_key` to the legacy `0.0`-sentinel key across all four cases (both present, ra-only, mean-only, both-None), confirming NA-last ordering is unchanged and a both-None pair compares EQUAL.

## Tests Run

Command (targeted, run directly by the developer — these two failures surface ONLY in the full suite, so both guard tests were run directly):
- `cd apps/backend && .venv/bin/python -m pytest tests/test_db.py tests/test_no_magic_numbers.py -q`
  Result: **10 passed** (235.68s) — includes `test_create_all_produces_expected_tables` (now green with `event_study_cache`) and `test_engine_calc_code_has_no_magic_numbers` (now green, 0 float literals in `research.py`).
- `cd apps/backend && .venv/bin/python -m pytest tests/test_iter20_research_cluster.py -q`
  Result: **16 passed** (7.02s) — J-72 single-batched-read + byte-identity, J-75 verbatim/NA/config-driven, J-77 group-by/ranking/min-sample/count-coherence all still green, PLUS the new rank-key byte-identity oracle.

Independent tokenizer check (the exact check the guard uses): `research.py` now has **0 float/complex literals**.

### Full backend suite — NOHUP-ASYNC IN PROGRESS

Per the iter-20/iter-11 lessons and project MEMORY (full suite ~34 min, 831+ tests; a subagent cannot finish it within the 10-min Bash cap + bg jobs die on turn-end), the **FULL backend suite was launched nohup-async** and is still running at handoff time:

- Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -q`
- Log: `/tmp/trendora-iter21-fullsuite.log` (terminal summary line + `EXIT_CODE=...` appended on completion)
- Status at handoff: **in progress** (no terminal summary flushed yet).

**The binding DoD gate is the FLUSHED `0 failed` summary line in that log.** The goal-evaluator must read that flushed line — it must NOT block in-flight on the suite (iter-11 lesson). Pre-fix baseline was **2 failed / 831 passed** (`/tmp/trendora-iter20-fullsuite.log`); both failures are addressed by the two fixes above, and both guard tests now pass when run directly, so the expected post-fix terminal line is **0 failed / 833 passed** (831 prior passing + the 2 now-fixed + 1 new oracle test = 834 total selected; the exact passed count depends on collection, but the binding signal is `0 failed`).

## Known Issues

- The full-suite `0 failed` line was not yet flushed at handoff (suite is long-running nohup-async). If the pump/evaluator finds the suite still running, answer the dispatch promptly with "two guard tests green + iter-20 cluster green + suite re-run nohup-async in progress" and gate GOAL_ACHIEVED candidacy on the flushed `0 failed` line (do NOT wait in-flight).
- No external integrations, native deps, or services were added/started this iteration — no live-integration or service-startup verification applicable (this is a test-fixture + sort-key-sentinel internal consolidation; no server processes were started, so no cleanup needed).
- J-22/J-23/J-24 remain honestly blocked-NA (data-dependent, non-vetoing per goal.md) — unchanged by this iteration.
