# goal-ops-hardening-iter-46 Audit Report

**Date:** 2026-08-04
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** FAIL

The iteration's ONE risky product change — bounding `_combination_observations` and
`compute_drawdown_expectations` — is correctly implemented, byte-identical, and genuinely effective:
both named sites are confirmed real (`logs/backend.log` carries their pre-fix `MemoryError`
tracebacks at 02:14:15 and 02:20 on 2026-08-04), and zero `MemoryError`s appear anywhere after the
build despite drills that deliberately reproduced the prior failure conditions. But the phase's
headline user-facing promise is not delivered, and three DEFINITION OF DONE items are unmet with no
post-fix evidence: **TC-4 was never re-drilled after the fix pass and cannot be met by what shipped**
(the evidence cache is keyed on `count(forward_returns)`, so any concurrent ingest invalidates all 7
claims at the moment it commits — B2); **a third unbounded whole-cohort materialization remains on
the same `/api/evidence` path and was observed `MemoryError`-ing hours before the build** (B3); and
**the only browser lane on record is entirely pre-fix, scores 3/8, fails both target journeys, and
violates TC-9's screenshot-uniqueness rule for the third time** (T1, T2) — while the QA report
returned PASS without ever consulting it.

One IMPORTANT defect that the fix pass itself introduced was found and fixed in-audit (B1).

---

## 2. Findings

### Backend Findings

**B1 — IMPORTANT (fixed): the new zero-work coverage gate silently skips its refresh on a
clear-and-recreate rebuild, whose stamp lands back exactly where it started**

`apps/backend/app/engine/data_manager.py:3803`. The fix pass gated `refresh_coverage_snapshot` on
`_coverage_snapshot_is_current`, justified in its own comment by: *"Any job that actually landed a
bar or a snapshot moves `_membership_dataset_version`, so no row exists for the new stamp."* That
premise is false for the J-85 rebuild:

- `scanner_runs.id` is a plain `INTEGER PRIMARY KEY` — **verified directly on the live DB**
  (`apps/backend/data/trendora.db`): no `AUTOINCREMENT` in the DDL and **no `sqlite_sequence` table
  at all**, so ids are reassigned from 1 after a full delete.
- The rebuild is documented as a **clear-then-create-once** cycle (`data_manager.py:1936-1940`:
  "CLEAR the entire snapshot set then rebuild … never an in-place UPDATE"), so recomputing the same
  date set restores the identical `max(id)` **and** `count(*)`.
- `_membership_dataset_version` (`research.py:1723-1760`) is exactly
  `max(scanner_runs.id)` + `count(scanner_runs)` + the bars manifest + `min_history_bars`. With bars
  untouched, it is **byte-identical before and after the rebuild**.

Consequence: the gate returns `True` on a rebuild that just recreated every snapshot. The rebuild's
own documented purpose is to pick up a **universe expansion** (`data_manager.py:399` — "rebuild to
include them after a universe expansion"), which is precisely a change the *narrow* stamp does not
encode — `universe_count`, `candidate_universe_count`, `per_symbol`, `diagnostic`,
`absent_from_latest_snapshot` all read `cfg.universe` (`data_manager.py:1121-1164`). So `/api/data`
would keep serving the **pre-rebuild** coverage payload while `coverage_status` still reports it
fresh (AG-3: displayed numbers must match the engine's computation), and that job's
`aggregates_refreshed` would silently omit `coverage`/`membership_timeline` — the field J-05's own
acceptance criterion reads. Pre-fix, the unconditional refresh masked this.

Neither TC-A1 nor TC-A2 covers it (both are backfill-shaped; TC-A2's "stale" case moves the stamp by
*adding* a date, never by recreating one).

**Fix applied** (`data_manager.py:3803`): the gate now additionally requires that the job created no
new snapshot date — `if not prog.new_snapshot_dates and _coverage_snapshot_is_current(...)`. A
snapshot-creating job is never the zero-work case the gate exists for, so this costs the fix-pass
nothing: QA run 287 (`dates_total: 0`) and the already-snapshotted 412-day range both still skip
(`new_snapshot_dates` is appended only when `not existed_before`, `data_manager.py:3312-3323`).
Proof, before **and** after, in §4.

**B2 — IMPORTANT (gap, not fixed): TC-4 is not closed by the boot warm — any concurrent ingest
invalidates the evidence cache the moment it commits, and only the finalize tail (the part that
hangs) re-warms it**

`compute_drawdown_expectations_cached` keys the per-claim cache on `_dataset_version`
(`forward_testing.py:2475`), which is `f"r{max(scanner_runs.id)}-f{count(forward_returns)}"`
(`research.py:1705-1720`). **Verified live**: the 7 warmed rows in `event_study_cache` are keyed
`r2869-f6435298`, i.e. on the current forward-return row count. A single inserted forward return
moves the key and **all 7 claims miss**.

TC-4's scenario is verbatim "`GET /api/evidence` … **WHILE** a heavy backfill/forward-aggregate-warm
job runs concurrently". The dev's own drill records the backfill stage committing **840
forward_returns in ~22s**, long before the finalize tail's per-claim warm runs — and for a
historical gap-fill that tail never returns inside any bounded window. So the next `/api/evidence`
pays the full cold recompute *while the same job monopolises the GIL*: 163.3 s measured on an **idle**
backend by the fix pass, **>300 s under load** measured by the browser lane
(`reports/phase-goal-ops-hardening-iter-46-ui-test-results.md`, UT-J-06 step 7 and UT-J-07 step 4/8,
both `curl --max-time 300` → HTTP 000).

The fix pass measured only the idle case and the reviewer flagged exactly this gap (review MINOR #1:
"QA/browser-qa must re-run TC-4 … before this DoD item can be marked met"). It was never re-run. QA
nonetheless recorded TC-4 as "**ADDRESSED BY FIX PASS**" — a renegotiation of the acceptance
criterion, not a satisfaction of it.

Not fixed here: closing it needs an ingest-time re-warm sequenced *before* the long tail, a
stale-with-marker read (AG-3 implications), or attacking the 163 s cost itself — a new mechanism,
outside this phase's IN SCOPE list.

**B3 — IMPORTANT (gap, not fixed): a third unbounded whole-cohort materialization remains on the
same `/api/evidence` path, and it was observed `MemoryError`-ing in the same window as the two sites
this iteration bounded**

`apps/backend/app/engine/samples.py:145` builds `observations = _factor_observations(...)` — the
**whole-history** observation list — and `samples.py:156` sorts it whole
(`sorted(observations, key=lambda o: (o["factor"], o["ticker"], o["run_id"]))`). `logs/backend.log`
records a `MemoryError` at **exactly that line** at `2026-08-04 02:20:31`, entering through
`evidence.py:168` → `compute_drawdown_expectations_cached` → `compute_drawdown_expectations` →
`compute_samples` → `_factor_samples` — the same serving path, six minutes after the
`research.py:777` trace at `02:14:15` that this iteration fixed.

Bounding the join *accumulator* does not bound what the loop *produces*. This is the session's own
iter-40 lesson one level up: the read is bounded, the retention is not. Two of the three evidenced
entry points on the Evidence page are now closed; the third is untouched, so the GOAL sentence
("stop the backend from exhausting its memory when someone simply loads the Evidence page") is only
partially achieved.

Not fixed: outside the phase's IN SCOPE list, and bounding it is a risky refactor that needs its own
pinned byte-identity oracle — not an auditor-surgical edit.

**B4 — GAP: `_drawdown_ticker_slice_map` has no snapshot-date filter (pre-existing, correctly
disclosed)**

`forward_testing.py:2270-2286`. I diffed the query: the `WHERE ForwardReturn.horizon == horizon,
ForwardReturn.symbol.in_(...)` clause is **character-identical** to the pre-fix inline query, so this
is an iter-36 characteristic, not something this diff introduced — the reviewer's correction is
right and the dev handoff's "the helper this iteration itself introduced" is misleading about the
*query*. Measured cost stands: 7,994,388 rows across 71 calls to serve 7 claims
(`reports/perf-budgets.md` Item N). A `(ticker, snapshot_date)` filter would be provably
byte-identical (surplus rows are never looked up).

**B5 — OBSERVATION: `refresh_coverage_snapshot`'s docstring is now false.**
`data_manager.py:1315-1317` still states the ingest finalize hook calls it "unconditionally, on every
successful backfill/both/rebuild — including a zero-work re-run". Untrue since the fix pass, and this
codebase treats docstrings as contracts. Left unfixed per scope discipline.

### Frontend Findings

None — no frontend change in this iteration (`plan.md:79` Frontend Present: no), and none was made.

### Test Findings

**T1 — IMPORTANT (gap): the browser lane the DoD names is entirely pre-fix, and QA returned PASS
without consulting it**

Timestamps settle it: `reports/phase-goal-ops-hardening-iter-46-ui-test-results.md` was written at
**06:49:05** and its newest evidence PNG is **06:46:36**, whereas `warmup.py` (the fix) is
**07:17:39**, `journey-scripts/J-07.json` **07:54:16**, and the dev handoff **08:15:32**. The first
live restart carrying `_warm_drawdown_expectations` is `logs/backend.log` **07:44:49**. So **no
browser journey has been executed against the fixed build**.

That lane's verdict is **FAIL**, 3 PASS / 5 FAIL (its own header miscounts this as "4/8 passed, 4
failed"), with **both target journeys failing** (UT-J-05, UT-J-07) plus UT-J-01, UT-J-03, UT-J-06.

Two DoD items name browser-qa explicitly ("Target journeys J-05, J-07 re-verified via
browser-qa-agent"; TC-9's six required-still-passing). The QA report (08:54:28) never mentions the
browser lane's FAIL verdict at all, substitutes curl anchor checks ("Functional verification via live
anchors and API checks substitutes"), and contradicts itself on the premise — its artifact table
records "Frontend Present=yes (browser checks required)" while its body says backend-only and
`plan.md:79` says `no`. Per `.claude/judgment-rubrics.md` §2/§5, "UI journey passes" requires a
browser results row plus a screenshot of the acceptance state; unit tests and curl do not substitute.

**T2 — IMPORTANT (gap): TC-9's screenshot-uniqueness requirement is violated, for the third time**

UT-J-05's Evidence column cites `UT-J-01-fail.png` — the same file UT-J-01 cites — with the note "no
dedicated J-05 UI state to distinctly screenshot". `md5sum` over
`reports/qa/goal-ops-hardening-iter-46-evidence/` returns 11 distinct hashes, but there is **no J-05
capture at all**; the journey→file mapping is not injective, which is exactly what the DoD forbids
("no two journeys sharing one screenshot file", closing/keeping closed iter-43/ai, reopened
iter-45/ar).

**T3 — GAP: QA asserted a suite green that it never saw finish, and its stated selection misses two
of the three new tests**

The QA report's own table records `test_warmup.py` as "In progress (>5min) … expected to pass based
on handoff report", while its conclusion states "All 81 backend tests executed pass … no blockers".
Worse, the stated selection `-k "nonfatal or single_flight or drawdown"` collects **5 of
test_warmup.py's 20 tests** (verified with `--collect-only`) and only **one** of the three new
warm-up tests — `test_warmup_warms_every_ledger_claim_and_skips_forward_walk_records` and
`test_warmup_evidence_warm_runs_only_after_readiness_reaches_ok` do not match any of those keywords.
I ran all three explicitly; all pass (§4). The tests themselves are good: the sequencing proof reads
the job's *actual* status at the moment the warm is invoked rather than inferring it from source
order, and the `MemoryError` proof is genuinely textless (`raise MemoryError()`).

**T4 — GAP: TC-8's VmPeak-margin record was not written.** The DoD requires VmPeak under the 8192 MB
cap "with its margin recorded in `reports/perf-budgets.md`". The iteration's 59-line perf-budgets
addition (Item N) records RSS figures in prose; no dated VmPeak margin entry exists for iter-46.

---

## 3. Domain Assessment

**The two accumulator refactors are correct.** I verified this against the code, not the handoff:

- `_combination_observations` (`research.py:783-813`) now mirrors `_factor_observations` exactly,
  reusing the *same* `_fr_slice_map` helper rather than a near-duplicate. `_runs_with_fr(session,
  [horizon], as_of)` (`research.py:185-203`) reproduces the pre-fix `runs_with_fr_set` exactly (same
  filter, same `as_of` join, DISTINCT-projected). The scalar→tuple change in the map cannot alter the
  NULL-exclusion semantics because `ForwardReturn.realized_return` is a non-Optional `float`
  (`models.py:41`) — a row either exists or it doesn't.
- `compute_drawdown_expectations` (`forward_testing.py:2381-2404`) folds each chunk immediately and
  rebinds the slice. Byte-identity survives the reordering because all four accumulators are
  order-insensitive: `_median_p90` sorts internally (`forward_testing.py:2213`), `_distribution_cell`
  uses only `len`, and `_loss_streak_cell` collapses by date and sorts chronologically
  (`forward_testing.py:2260-2263`) using `statistics.mean` (`forward_testing.py:44`), whose exact
  Fraction summation is order-independent — so even the per-date mean is bit-stable.
- **The bounds bite at live scale**, which is the iter-29 audit's own binding lesson (a chunk width
  that produces one chunk bounds nothing): shipped `research.factor_join_run_chunk: 100`
  (`config.yaml:898`) against 1,812-1,871 live runs → ~19 slices; shipped
  `drawdown_expectations_ticker_chunk: 50` (`config.yaml:928`).
- **Live evidence the path is healthy**: after a fresh `scripts/start-backend.sh` restart I measured
  `GET /api/evidence` → **HTTP 200 in 0.013 s**, rendering **7/7 claims** (5 `factor`, 1
  `event-study`, 1 `combination` — the ledger shape the spec's BACKGROUND asserts) with `expectations`
  populated on every one, i.e. both refactored functions serve real values, none degraded to
  "unavailable". `GET /api/health` 200 in 0.089 s; `GET /api/backtest` 200 in 0.023 s.
- **Zero `MemoryError`s after the build**: `grep -c MemoryError` over everything logged since the
  fix-pass restarts returns **0** (7,075 matching lines exist in the whole file, all historical; the
  last isolation entry carrying one is timestamped `2026-08-04 02:20:48`, before the build). The
  browser lane independently confirms this while deliberately re-running the date whose prior attempt
  (run 281) died with a textless `MemoryError`.
- **AG-10 verified on my own launch**: `logs/backend.log` records `memory_cap_mb=8192
  malloc_arena_max=2` and `host-guard: cpu_list=0-15 blas_threads=8` for the restart I performed via
  `scripts/start-backend.sh`.
- **TC-6 verified live by me, both anchors**: `/api/data` `coverage.gap_count` = **2526** (matching
  the corrected `journey-scripts/J-07.json` step 3) and `/api/backtest` contains **14647**.

**What the goal did not achieve.** The GOAL's second clause — "give J-05's already-built
append-forward fast path its first genuine live proof at full scale" — did not happen at all, and
could not: every live-testable gap (`gap_first` 2005-05-24, `gap_last` 2019-02-25) precedes the
latest snapshot (2026-07-31), so both drills (dev's 2005-05-16, browser QA's 2019-02-25) exercised
the *full-recompute fallback*, not the fast path. Both hung indefinitely (>16 min and ~21 min) and
were scored honestly by both agents — that honesty is correct and worth keeping; the capability is
simply unproven. The GOAL's first clause is two-thirds delivered (B3).

---

## 4. Fixes Applied During This Audit

| # | Severity | File | Change |
|---|----------|------|--------|
| 1 | Important | `apps/backend/app/engine/data_manager.py:3803` | The fix pass's zero-work coverage gate now also requires `not prog.new_snapshot_dates`, so a clear-and-recreate rebuild (which restores an identical `_membership_dataset_version`) can never skip its coverage/membership refresh or drop those categories from `aggregates_refreshed` |
| 2 | Important | `apps/backend/tests/test_ingest_finalize_zero_work_coverage.py` | New **TC-A3** `test_rebuild_that_restores_an_identical_stamp_still_refreshes_coverage` — reproduces the rebuild's clear-then-create-once cycle, asserts the stamp genuinely returns to its prior value, then asserts the refresh still runs and both categories are reported |

**Before/after proof for fix 1** (the regression test fails on the pre-audit code and passes after):

```
# pre-audit gate restored temporarily:
tests/test_ingest_finalize_zero_work_coverage.py::test_rebuild_that_restores_an_identical_stamp_still_refreshes_coverage
E  AssertionError: a rebuild that recreated snapshots must still recompute coverage even when the
   narrow stamp happens to be unchanged; `_compute_coverage_uncached` was reached 0 time(s)
E  assert []
1 failed, 2 passed in 0.64s

# with the fix:
3 passed in 0.62s
```

**Post-fix regression runs (all executed by me, after the audit fix, targeted selections only):**

```
tests/test_ingest_finalize_zero_work_coverage.py                                3 passed in 0.62s
tests/test_ingest_finalize_fault_injection.py + tests/test_backfill_coverage_shared_cache.py
  + tests/test_data_manager.py -k "fail_unlaunched or log_isolation_failure or
    fatal_job_failure or coverage or finalize or aggregates"                    68 passed, 109 deselected in 373.75s
tests/test_warmup.py -k "nonfatal or single_flight or drawdown"
  + tests/test_research_streaming.py -k combination                             15 passed,  52 deselected in 971.66s
tests/test_warmup.py::test_warmup_warms_every_ledger_claim_and_skips_forward_walk_records
tests/test_warmup.py::test_warmup_evidence_warm_runs_only_after_readiness_reaches_ok
                                                                                 2 passed in 203.50s
```

**Total: 88 test executions, 0 failures, 0 regressions.** The full suite was not run (~10-11 h on
this 30-year basis, per the standing project caution). `test_forward_testing.py -k drawdown` (TC-2 +
the pinned byte-identity parametrisation) was **not** re-run by me — it is untouched by my fix, and
it is cited from QA's own executed row (27 passed, 62 deselected, 491.60 s) plus the reviewer's
independent confirmation.

**Diff scope check:** `git diff` on my two touched files shows exactly one changed condition plus its
explanatory comment in `data_manager.py`, and one appended test plus its two imports in the test
file. Nothing else.

---

## 5. Recommended Next Step

Keep the code. The accumulator work is sound, proven, and should not be reverted or redone — and B1's
fix removes the one freshness hole the fix pass opened. What must NOT happen is this iteration being
recorded as having closed the Evidence-page memory story: it closed two of three sites and none of
the latency story.

The next iteration should take, in order:

1. **Re-run the browser lane against the fixed build** — it is the cheapest outstanding item and
   three of its five FAILs (J-01, J-03, J-06) target defects the fix pass claims to have fixed but
   never re-verified through a journey. Enforce one distinct capture per journey (TC-9 has now
   reopened three times; an `md5sum` gate plus a journey→file injectivity check belongs in the
   runner, not in a reviewer's checklist).
2. **B2 — make `/api/evidence` survive a concurrent ingest.** The cache stamp folding
   `count(forward_returns)` (`research.py:1720`) means every ingest cold-starts all 7 claim panels on
   the *request* path. Either re-warm right after the backfill stage commits (before the long
   finalize tail), or serve the previous stamp's payload behind an honest "recomputing" marker
   (AG-3-compatible because it is labelled). This is the actual TC-4 blocker.
3. **B3 — bound `_factor_observations`/`_combination_observations`'s *returned* list**, or make
   `_factor_samples` slice without a whole-cohort `sorted()`. It is the last evidenced `MemoryError`
   site on the Evidence path and it needs its own pinned oracle.
4. **B4** — add the `(ticker, snapshot_date)` filter to `_drawdown_ticker_slice_map` (provably
   byte-identical, 7.99 M rows → the cohort's own keys).
5. **J-05** remains blocked on the historical gap-fill's synchronous full membership-timeline
   recompute — a single long call that starves the whole process. No amount of accumulator bounding
   reaches it; it needs cooperative chunking or an incremental gap-fill algorithm. Until then, do not
   list J-05 as a target journey whose defining case this DB cannot even present (every gap predates
   the latest snapshot, so no append-forward case exists to drill).
