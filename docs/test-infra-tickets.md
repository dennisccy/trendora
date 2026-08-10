# Test-infrastructure tickets

Dedicated, append-only register for defects in the **test harness** — slow fixtures, unrunnable
files, flaky scaffolding — as opposed to product defects (which belong in a phase/iteration spec)
and product ideas (which belong in `docs/improvement-backlog.md`).

A ticket lands here when a test-infrastructure problem has recurred across iterations, blocks an
honest pass/fail signal, and is too large to fix inside a normal dev dispatch's time budget.

**Status legend:** `OPEN` · `IN-PROGRESS` · `DONE` · `WONTFIX`

---

## TI-1 — `apps/backend/tests/test_api_runs.py` cannot complete inside a dispatch (`loaded_engine` fixture cost)

**Status:** OPEN
**Filed:** 2026-08-10, ops-hardening iter-57 developer FIX PASS
**Filed because:** `reports/reviews/goal-ops-hardening-iter-57-review.md` (MINOR, third issue) asked
for a dedicated ticket rather than another in-dispatch retry.

**Symptom.** The file's session-scoped `loaded_engine` fixture (a fresh temp DB built against the
full 30-year committed seed, then warmed through a historical scanner/scoring cadence) has never
finished inside a dev dispatch. Documented non-completions:

| Iteration | Attempt | Outcome |
|---|---|---|
| iter-55 | `test_forward_testing.py` (same fixture class) | killed at 30+ min |
| iter-56 | `test_api_runs.py` ×2 | killed at ~30 min each |
| iter-57 | `test_api_runs.py`, run alone and first | 59 min, zero test assertions reached, terminated |
| iter-57 | `test_api_runs.py`, retried on a warm OS page cache | further 10 min, still zero output, terminated |

The warm-cache retry is the diagnostic that matters: the cost is **CPU-bound compute inside the
fixture**, not cold-disk I/O, so caching the filesystem cannot shortcut it.

**Impact.** Three iterations in a row have had to reason about `app/api/runs.py` from "this module
has zero diff" rather than from a green test run. That is a real, if low-probability, blind spot,
and it silently widens every time the seed grows.

**What is already known to work (measured, iter-57 fix pass).** Of the file's 9 tests, only 5 need
`loaded_engine`. The other 4 (`multi_run_engine`, a fast hand-built fixture, plus one `tmp_path`
test) run in **0.56 s**:

```
.venv/bin/python -m pytest tests/test_api_runs.py -q -k "n_stocks or no_price_data"
4 passed, 5 deselected in 0.56s
```

**Proposed fix (pick one, in preference order):**

1. **Split the file.** Move the 4 `loaded_engine`-independent tests into their own fast file so every
   dispatch gets a real signal on the grouped-aggregate `/api/runs` read, and leave the 5
   snapshot-history tests in a clearly-named slow file that only a full-suite run executes.
2. **Cache the fixture build** across pytest invocations (persist the built temp DB keyed by seed
   content hash + cadence config, rebuild only on a key change).
3. **Profile the cadence warm-up itself** and find what became O(expensive) at the current seed
   scale — the most valuable outcome, since the same fixture cost is what makes the whole suite
   ~10-11 h (see `docs/handoffs/` iters 55-57 and the memory note "30y test suite slow, not the
   product").

**Do NOT** "fix" this by deleting or weakening the 5 slow tests: they are the only coverage of the
stored-snapshot history contract.

---

## TI-2 — a `-k` selector silently deselected the only real-data test for the iter-57 `/api/health` rewrite

**Status:** OPEN
**Filed:** 2026-08-10, ops-hardening iter-57 developer AUDIT FIX PASS
**Filed because:** `docs/handoffs/goal-ops-hardening-iter-57-audit.md` finding **T3** — carried into
iter-58 by the audit's own recommended-next-step (4).

**Symptom.** `apps/backend/tests/test_health.py::test_health_symbol_count_matches_naive_count_distinct_on_loaded_engine`
has **never executed**. Both the developer and QA selected the health tests with
`-k distinct_symbol_count`, which does not match that test's name
(`..._naive_count_distinct_on_loaded_engine`), so pytest reported a clean `3 passed` while silently
deselecting the fourth. A green count from a `-k` run says nothing about a test the pattern missed.

**Why it matters.** It is the only **real-data byte-identity** check for the recursive-CTE
loose-index-scan that replaced `COUNT(DISTINCT symbol)` in `app/api/health.py`. What survives is 3
hand-built fixture tests plus a live query showing both query forms returning 591 — good evidence,
but not the seeded-fixture comparison this test was written to be.

**Why it is a test-infra ticket and not a one-line fix.** Running it requires `loaded_engine` — the
same fixture as **TI-1**, which has never completed inside a dispatch. Correcting the selector alone
would convert a silent skip into a silent multi-hour hang. It closes when TI-1 closes.

**Fix (with TI-1, preference order):**

1. Move this test alongside the split-out fast/slow files TI-1 proposes, and select health tests by
   **file or node id**, never by a substring pattern.
2. Whenever a `-k` pattern is used to justify a coverage claim, record the deselected count too
   (`N passed, M deselected`) — the iter-57 runs printed exactly that and nobody read the `M`.
