# Phase goal-ops-hardening-iter-9 — User-Visible Changes

**Phase:** goal-ops-hardening-iter-9
**Date:** 2026-07-22
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

None. This iteration is an explicit verification-and-compliance closeout (plan.md, dev handoff, and
implementation summary all agree): no new product feature, no new endpoint, no new Data Contract value.
The dev handoff's complete "Files Changed" list is:

- `scripts/start-backend.sh`
- `scripts/dev.sh`
- `apps/backend/app/engine/data_manager.py`
- `apps/backend/tests/test_data_manager.py`
- `apps/backend/tests/test_start_backend_script.py`

Zero of these are under `apps/frontend/`. There is no new action a user can take that they could not take
before this iteration.

---

## What Changed in the Visible UI

Nothing. Plan.md's own "UI Evolution" section states it plainly: "New user-facing capability: none. New
information displayed: none. New user actions: none. UI surface changes: none. Navigation changes: none."
`Frontend Present: yes` was set for this iteration for one reason only — to force the goal-mode harness's
browser-qa lane to actually run against four already-shipped surfaces (`/data`, `/scanner-runs`, the
top-bar readiness badge, the preflight/crash banner) for regression re-verification, correcting a harness
bug from iter-8 (`Frontend Present: no` silently skipped browser-qa even though browser journeys were
named as mandatory). None of those surfaces' code changed this iteration — see the UI Surface Map for the
specific re-verification rows.

---

## What Old Behavior Changed

None from a user's vantage point. The production code paths a user's browser actually exercises —
`GET /api/health` / boot readiness (`app.engine.readiness`), the ingest finalize hooks that populate
`scanner_results` / `market_phase_cache` / the coverage payload, and the job-status computation rendered on
`/data`'s job-history panel — were explicitly untouched this iteration (plan.md's "Do not touch" list names
`app/api/health.py`, `app/engine/readiness.py`, `main.py`'s boot sequence, `warmup.py`, and the four-loop
`MemoryError` early-abort handling itself as settled/out-of-scope).

The two production changes that did ship are both operationally invisible to a user:

- **Launch-script process confinement** (`scripts/start-backend.sh`, and now `scripts/dev.sh`'s backend
  subshell): whenever `project-extensions/host-guard/host-guard.env` is present and
  `HOST_GUARD_ENABLED=1`, the backend process is pinned to a declared-safe CPU-core set (`taskset`) and a
  BLAS/OMP/numexpr thread cap, on top of the pre-existing `ulimit -v`/`MALLOC_ARENA_MAX` enforcement. This
  is a process-level hardware safeguard (AG-10, following two host hard-resets this week) — it changes
  nothing a browser can observe; `dev.sh`'s frontend (`next dev`) subshell is explicitly untouched and
  keeps unrestricted resources.
- **`_release_process_memory()` internal memoization** (`apps/backend/app/engine/data_manager.py`): the
  libc handle used for `malloc_trim` is now resolved once per process instead of on every call. Per the dev
  handoff, `gc.collect()`/`malloc_trim` timing and effect are unchanged — this is a byte-identical-behavior
  micro-optimization (fewer redundant fork/execs), not a behavior change a user could perceive.
- The heavy-ingest regression test
  (`test_start_backend_survives_back_to_back_heavy_ingest_under_memory_cap`) was tightened to reject a
  `"partial"` job outcome and require full `aggregates_refreshed` completeness for both jobs it drives —
  but this is a **test assertion** change only. It does not touch the finalize-hook production logic that
  computes and persists a job's status, so no different rendering is expected on `/data`'s job-history
  panel as a direct result of this edit; the test only asserts more strictly against the same production
  behavior.

---

## Not Visible Yet

- **The live heavy-ingest re-measurement under the new launcher caps was deferred this session**
  (dev handoff, Known Issue #1) for a host-thermal-safety reason (an unrelated process already running hot
  on the same physical host). This means the concrete end-to-end claim — "the new CPU/thread caps keep
  `GET /api/health` responsive through a real back-to-back heavy backfill + rebuild on this host" — has
  **not yet been proven with a fresh live run this session**; only the non-heavy automated test suite and
  manual launcher smoke tests (against the real `host-guard.env`, short of the full heavy workload) back
  the caps today. The `reports/perf-budgets.md` dated section and the retained VmPeak/VmSize sampler CSV
  called for in the plan are both still outstanding. Browser-qa's J-05 step 4 check is expected to exercise
  this same path independently — its outcome should be read from the raw
  `reports/phase-goal-ops-hardening-iter-9-ui-test-results.llm.md`, not assumed from this handoff.
- **The on-load `/api/backtest` → `forward_aggregates_cached` → `ScannerResult` `MemoryError` (J-06/AG-8)**
  remains unresolved — carried forward again, unchanged by this iteration's diff.
- **The `demo.sh ops-hardening --session-live` walkthroughs for J-05/J-06** are still not produced —
  needs an explicit human deferral or a new iteration budget before any `GOAL_ACHIEVED` gate.
- **`HOST_GUARD_ENV_FILE`** — a new test-only environment variable that lets automated tests point at a
  practice copy of `host-guard.env` instead of the real file. It has no UI, is not set in any real launch,
  and is safe to ignore for day-to-day use.
