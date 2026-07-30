# goal-ops-hardening-iter-37 Audit Report

**Date:** 2026-07-30
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

The code defect is genuinely closed: `_do_backfill` and the whole ingest finalize tail now share ONE
prefilled `_BarCache` per job, TC-6 passes at exactly 1 load per symbol, and the byte-identity oracle is
pinned to the real `git show HEAD` body and is proven load-bearing by its paired mutation test (I re-ran
all three and re-verified the pinned body against `git show HEAD` myself). One IMPORTANT defect the
review and QA lanes both missed — the deferred release can leave the ~1.13 GB whole-table cache
referenced **forever** on a `JobProgress` that `_JOBS` never evicts — was found, fixed, and locked down
with a mutation-proven regression test during this audit.

The gap that remains is verification, not code: **both** live drills this iteration ran through paths
where the new code is inert (step 1/3's warm was dispatched by `GET /api/backtest`, never through
`_refresh_ingest_aggregates`; step 4's drill job had `dates_total: 0`, so `_do_backfill` returned before
its prefill and `cache_ctx` was a `nullcontext()`). So the one behavioural change this iteration makes —
holding the whole-table cache resident across the *entire* finalize tail, where it used to be freed
before the forward-aggregate and drawdown warms ran — has never been measured. J-07's availability
guarantee itself is honestly demonstrated (I recomputed the health-poll evidence from the raw CSV and it
matches to the digit); the iteration's own memory-peak claim is not.

---

## 2. Findings

### Backend Findings

**B1 — IMPORTANT (fixed): a successful `_do_backfill` can pin the ~1.13 GB shared `_BarCache` on a
retained `JobProgress` for the life of the process**

`_do_backfill` deliberately stops releasing on the success path (`data_manager.py:3172`) and hands the
only surviving reference to `prog._shared_bar_cache`. The single release point is
`_refresh_ingest_aggregates`'s own `finally` (`data_manager.py:3541`). But `_run_job` reaches that hook
only through a narrow window (`data_manager.py:4286`), and three writes sit between a *successful*
backfill and it: `_mark_checkpoint_failed_backfill` (`:4248`), `_finalize_checkpoint` (`:4253`) and the
stage-record write in the enclosing `finally` — plus `Session(eng)` itself at `:4285`. If any of those
raises (a `MemoryError` under real pressure, a locked SQLite DB), the exception unwinds to `_run_job`'s
outer handler, the hook never runs, and **nothing else ever clears the reference**: `_JOBS`
(`data_manager.py:2190`) has `create_job`/`resume_data_job` inserts and no eviction anywhere, so the
finished job — and its 1.13 GB cache — stay resident until process exit. `_do_backfill`'s new
`except Exception:` branch does not cover this (the failure happens *after* it returns), and
`except Exception` also lets a `BaseException` (`KeyboardInterrupt`/`SystemExit`) skip its release
entirely, which the pre-iter-37 blanket `finally: _release_process_memory()` did cover.

This is the exact failure class J-07/AG-8 exists to forbid ("heavy aggregates never take the service
down"), and it was structurally impossible before the release moved out of `_do_backfill`'s `finally` —
so it is a regression introduced by this iteration, not a pre-existing gap. (I was unsure between
IMPORTANT and CRITICAL: the consequence is severe and permanent, but it needs a second failure to
trigger. Recording IMPORTANT.)

**Fix applied** (`data_manager.py:4327-4341`) — a last-resort release at the top of `_run_job`'s own
`finally`, which runs on *every* exit path including `BaseException`:

```python
if prog._shared_bar_cache is not None:
    prog._shared_bar_cache = None
    _release_process_memory()
```

Guarded on the reference, so it is a plain no-op on every job that reaches the hook normally (no new
`gc.collect()`/`malloc_trim` on the happy path, no timing change). Nulls the reference before releasing,
per the plan's own ordering requirement.

**Verification (mandatory evidence):**
- New test `tests/test_backfill_coverage_shared_cache.py:251`
  `test_shared_cache_released_even_when_finalize_hook_never_runs` — runs a REAL 1-target backfill through
  `run_data_job` with `_refresh_ingest_aggregates` monkeypatched to raise `MemoryError`, then asserts the
  retained job's `_shared_bar_cache is None` and that the job still ends `ok` (the hook's pre-existing
  non-fatal contract).
  `.venv/bin/python -m pytest tests/test_backfill_coverage_shared_cache.py -k "released_even_when" -q`
  → **1 passed, 2 deselected in 56.00s**.
- Mutation-proven load-bearing: with the fix text temporarily removed, the same command → **1 failed**
  (`MemoryError: simulated pressure...` logged non-fatally, `job._shared_bar_cache` still holding the
  cache). Fix restored and re-verified present.
- No regression from my change: `tests/test_backfill_coverage_shared_cache.py` → **3 passed (125.03s)**;
  `tests/test_bar_cache.py::test_kdate_backfill_loads_each_symbol_at_most_once` → **1 passed (47.28s)**;
  `tests/test_data_manager.py -k "coverage or aggregates_refreshed or persist_per_date or finalize_hook
  or release_process_memory"` → **54 passed, 83 deselected (140.45s)**. No test asserts a per-job count of
  `_release_process_memory()` calls, so the added call site breaks no existing assertion.
- Diff re-read: `git diff` on `data_manager.py` shows my hunk is the comment + 3 statements above and
  nothing else.

**B2 — IMPORTANT (gap): this iteration's own memory profile is unmeasured — both live drills ran paths
where the new code is inert**

The single behavioural change of iter-37 is that the ~1.13 GB whole-table cache is now held resident
across the WHOLE finalize tail (`data_manager.py:3338` wraps coverage, per-date coverage, market-phase,
forward-aggregates, research hot-keys, index-series and drawdown warms). Pre-fix, `_do_backfill`'s
`finally: _release_process_memory()` freed that block *before* the forward-aggregate and drawdown warms
ran — the two heaviest, and the two that actually raised `MemoryError` in the drill. Neither live
measurement this iteration exercised that state:

- **Steps 1-3** (`perf-budgets.md:4632-4636`): the warm was dispatched by
  `GET /api/backtest?as_of=2026-07-17` → `ensure_historical_forward_aggregates_dispatched` in a daemon
  thread. That path never calls `_refresh_ingest_aggregates` and has no `JobProgress`, so
  `prog._shared_bar_cache` was never in play. The spec's step 1 explicitly names "the ingest finalize
  path". VmPeak flat at 2,693,672 kB is a true margin figure (57.19 % under the 6144 MB cap) but it is
  also a monotone high-water mark set at boot — it says nothing about the changed path.
- **Step 4** (`runs/goal-ops-hardening-iter-37/mem-drill/final-job-status.json`): `"dates_total": 0`,
  `stages.backfill.elapsed_seconds: 0.0052`. A 0-target backfill returns at `data_manager.py:2980`
  **before** the prefill, so `prog._shared_bar_cache` stayed `None` and `cache_ctx` resolved to
  `nullcontext()` (`data_manager.py:3338`). The claim at `perf-budgets.md:4717` that the `MemoryError`
  fired "INSIDE this iteration's own new `with cache_ctx:` wrap (confirming the restructuring did not
  disturb the catch's placement/behavior)" is true only lexically — the wrap was a no-op, so the drill
  re-verified the iter-8 catch on the pre-iter-37 fallback path, not "against the paths bounded by this
  iteration" as the spec's step 4 requires. The dev handoff's own note that
  `test_ingest_finalize_memory_pressure.py` "exercises the `nullcontext()` fallback path" means the unit
  coverage has the same blind spot.

Consequence: the spec's Product-surface-delta claim and the dev handoff's "lower peak memory" are
unproven, and for the finalize tail specifically the direction is plausibly reversed (post-fix
instantaneous peak during the forward-aggregate/drawdown warms = pre-fix peak **plus** ~1.13 GB). The
whole-job peak may still be dominated by `_do_backfill`'s own per-date parallel compute, in which case
nothing changes — but that is inference, which this DoD explicitly forbids ("this-iteration evidence,
not inference"). The measured 3,597,784 kB margin makes an actual cap breach unlikely, not impossible.

**Not fixed — deliberately.** Closing it needs a real multi-date backfill against the 4.97 GB live basis
in a `scripts/start-backend.sh` process with VmPeak sampling: hours of heavy all-core compute on a host
with two documented instant hardware resets under exactly that load (AG-10), and it would mutate the
committed-seed DB (new `ScannerRun` rows, `dataset_version` bump) — invalidating the browser-QA and demo
evidence this iteration already captured. That is a next-iteration task with its own spec, not an audit
action. Recorded here so it is not inherited silently.

**B3 — OBSERVATION (confirmed reviewer NOTE): direct `_do_backfill` callers still get no release on
success**

The reviewer's NOTE at `data_manager.py:3172` is accurate. My B1 fix covers every path routed through
`_run_job` (both production call sites, `:4220`/`:4235`); a direct caller that never runs the finalize
hook — several unit tests, e.g. `tests/test_data_manager.py:2154` — still leaves the reference set on its
own throwaway `JobProgress`, which is garbage-collected with the test. No production path, no fix needed.

### Frontend Findings

None — `Frontend Present: no`, and I confirmed the diff touches no file under `apps/frontend/`. The
browser lane's UT-J-07a/b evidence
(`reports/qa/goal-ops-hardening-iter-37-evidence/UT-J-07a-backtest-readiness.png`,
`UT-J-07b-data-runsummary.png`) shows both J-07 page homes rendering real values with the run-summary
contract fields (`dates_total` / exclusion breakdown / `aggregates_refreshed`) intact — the TC-9
no-regression check, at page level.

### Test Findings

**T1 — OBSERVATION: the TC-7 byte-identity test would pass on a silent no-op (the paired mutation test is
what saves it)**

`test_shared_cache_coverage_byte_identical_to_pinned_reference`
(`tests/test_backfill_coverage_shared_cache.py:162`) runs the REFERENCE first, then the SHIPPED function
over the same dates, and reads back the same `(asof_key, dataset_version)` rows. Every per-date failure
inside the shipped function is swallowed (`data_manager.py:3263`, log + continue), so if the shipped call
had written nothing at all, the reference's rows would still be present and the equality would hold. The
paired TC-8 mutation test does close the hole — poisoning one admitted symbol inside the shared cache
changes the shipped output while leaving the pinned reference blind — so the pair is genuinely
load-bearing. Worth knowing that the byte-identity assertion alone is not.

**T2 — GAP: nothing asserts the newly-wrapped warm categories still succeed under the attached cache**

Wrapping the whole finalize tail means market-phase, forward-aggregates, research-hot-keys, index-series
and drawdown warms now read through a shared cache they previously did not see. Every one of those warms
swallows non-`MemoryError` exceptions, so a break there surfaces only as a silently shorter
`aggregates_refreshed` list (a J-05/J-06 regression: the warm silently stops happening and the first page
view pays a cold compute). Coverage of that: TC-6 asserts load counts, not category success; the one
end-to-end test that runs *with* a shared cache present
(`tests/test_data_manager.py:2167 test_run_data_job_backfill_wires_finalize_hook_end_to_end`, selected and
green this iteration) asserts only `>= {latest_snapshot, coverage, membership_timeline}`; and the live
drill's full 5-category list came from the `nullcontext()` path. Mitigating (why GAP, not IMPORTANT):
those warms already opened their OWN `bar_cache(session)` pre-fix — that is precisely how the dev's
pre-fix trace attributed 3 SPY loads to `market_phase_cached` and 5 to `compute_drawdown_expectations` —
so they were already reading lightweight `Bar` records from a `_BarCache`; only the cache's provenance
changed, and `attach_shared_cache` is correctly re-entrant (`prices.py:420-430`: the inner attach sees
`had=True` and never pops the outer registration). A one-line strengthening of the existing end-to-end
assertion to compare the category list against a forced-fallback run would close this cheaply.

**T3 — OBSERVATION: DoD item 1's provenance is single-party**

"J-07 passes via browser-qa: steps 1-4 all execute" is satisfied by a union, not by the browser lane: the
UI test plan correctly declares itself N/A (backend-only), the browser lane verified only that J-07's two
page homes render, and steps 1-4 were executed and recorded solely by the developer — the QA report
restates those artifacts rather than re-measuring them. I did corroborate them independently rather than
accept the prose: recomputing `runs/goal-ops-hardening-iter-37/j07-warm/health-latency.csv` from raw gives
130 rows, **130/130 HTTP 200**, span **148.9 s**, max inter-poll gap **1.9996 s**, latency
min 0.106 / median 0.113 / max 0.980 s — matching the handoff and `perf-budgets.md` to the digit; and both
AG-10 host-guard boot banners are present in the live log at `logs/backend.log:140405`
(`port=8255 memory_cap_mb=6144 malloc_arena_max=2`, `cpu_list=0-3,8-11 blas_threads=4`) and `:140635`
(`port=8256 memory_cap_mb=970`, same host-guard block). The recorded numbers are trustworthy; steps 1/3/4
simply have no second measurer.

TC-5 is satisfied vacuously and effectively: the test plan contains no backend-down/error-state case at
all, so no ordering could strand anything, and nothing was stranded (9/9 journeys passed, versus iter-36
losing the whole J-07 verification this way).

---

## 3. Domain Assessment

The core mechanism is right and it reuses proven infrastructure instead of inventing a second caching
approach: `prefilled_bar_cache` is re-entrant on session id, `attach_shared_cache` registers only when the
session is not already registered and pops only what it registered (`prices.py:420-430`), so the outer
finalize-tail attach and the inner `_persist_per_date_coverage_snapshots` attach nest safely. The
`JobProgress` field is real internal scratch — `to_dict()` (`data_manager.py:2138`) enumerates its keys
explicitly, so a `_BarCache` can never leak into a served payload or a persisted row. The fallback for a
direct call (`prog._shared_bar_cache is None` → own prefill) genuinely preserves pre-iter-37 behaviour,
which is what lets the pinned oracle be a real oracle.

Value-correctness reasoning holds up: the backfill stage adds no bars, so a cache prefilled at
`_do_backfill`'s start cannot be stale when the finalize tail reads it, and for a `both` job the fetch
stage's bars are committed before that prefill. The oracle test proves this for the coverage payloads
byte-for-byte, and the mutation test proves the oracle is not a rubber stamp. `_final_status` can never
return `failed` for a backfill/rebuild kind (`data_manager.py:3760-3770`), so the normal route to the
release point is not conditional on luck — the leak I fixed needed a *secondary* write failure.

Where the iteration's reasoning is weaker is the memory story it tells about itself. Eliminating one of
two whole-table loads is unambiguously good for time and allocator churn; it does not follow that peak
memory drops, because the same change extends the surviving load's *residency* across the heaviest warms.
The iteration asserts the favourable direction and then measures a path where the change cannot appear.
That is the one place the evidence discipline this session has otherwise enforced well (pinned oracles,
mutation tests, live-log corroboration) slipped.

---

## 4. Fixes Applied During This Audit

| # | Severity | File | Change |
|---|----------|------|--------|
| 1 | Important | `apps/backend/app/engine/data_manager.py` (`:4327-4341`) | Last-resort release of `prog._shared_bar_cache` at the top of `_run_job`'s `finally` — nulls the reference then `_release_process_memory()`, guarded so it is a no-op whenever the finalize hook already released. Closes the permanent ~1.13 GB retention when a write between a successful `_do_backfill` and `_refresh_ingest_aggregates` fails, and restores pre-iter-37 parity for `BaseException` paths. |
| 2 | Important | `apps/backend/tests/test_backfill_coverage_shared_cache.py` (`:251-289`) | New regression test `test_shared_cache_released_even_when_finalize_hook_never_runs`: real 1-target backfill through `run_data_job` with the finalize hook raising `MemoryError`; asserts the retained job's `_shared_bar_cache is None` and the job stays `ok`. Verified to FAIL without fix #1 and PASS with it. |

No other file was touched. The dev handoff's claims remain valid as written; fix #1 adds a safety net it
did not describe, so no handoff claim needed correcting.

---

## 5. Recommended Next Step

Proceed. J-07's own acceptance is now demonstrated with this-iteration live evidence I was able to
re-derive from the raw artifacts, the last unbounded double-load is closed and provably so, and the one
real defect in the new cache lifetime is fixed and regression-tested.

Carry exactly one thing forward into the next iteration's spec, ahead of or alongside iter-33/g (Regime
Lab dispatch): **measure the changed path.** One real multi-date backfill (K ≥ 3 targets, live basis, one
`scripts/start-backend.sh` process, VmPeak/VmHWM sampled through the whole finalize tail) settles B2
either way, and the same run yields the `aggregates_refreshed` category list that closes T2 — cheaply, if
it is scoped as the iteration's *own* measurement rather than a ride-along. Until it exists, treat "lower
peak memory" as an unproven claim and do not let a future spec cite this iteration's VmPeak table as
evidence for the finalize-tail path.

Unchanged owner decisions (out of scope, not re-opened): iter-34/j (`GET /api/health` ≤0.1 s budget on
this shared host) and iter-33/i (`start-frontend.sh` in `HOST_GUARD_MARKER_FILES`). Also still open and
correctly deferred: the two uncaught read-path `MemoryError`s the dev disclosed at the 970 MB drill cap,
`warmup.py:194`, iter-36/n, Audit B6, and the vendored `closure_gate.py` regex false-positive.
