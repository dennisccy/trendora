# goal-ops-hardening-iter-9 Execution Plan

Session closeout iteration (last of `max_iterations: 9`). Pure verification-and-compliance work: no new
product feature, no Data Contract change. Target journey J-05 (regressed, iter-8 shipped the fix but never
browser-verified it); required-still-passing re-verification for J-01/J-03/J-04 (never ran in iter-8 —
`unknown`, not `regressed`); plus closing the goal.md-scheduled AG-10 launcher gap
(`scripts/start-backend.sh` / `scripts/dev.sh` backend subshell must apply `host-guard.env`'s
`taskset`/BLAS-thread caps, not just `ulimit -v`/`MALLOC_ARENA_MAX`).

This directly matches goal.md's "Improvement direction" binding note ("closing that gap is in-scope
launcher work for the next iteration") and the Loop-mechanics priority rubric (regressed journeys outrank
new work; absence-of-evidence journeys get re-verified, not re-diagnosed). No drift from `docs/goal.md`
found.

## What to Build

- **AG-10 launcher fix:** add a HOST-GUARD-marked block to `scripts/start-backend.sh` that, when
  `project-extensions/host-guard/host-guard.env` is present and `HOST_GUARD_ENABLED=1`, sources it and
  wraps the exec'd `uvicorn` with `taskset -c "$HOST_GUARD_CPU_LIST"` plus exports
  `OMP_NUM_THREADS`/`OPENBLAS_NUM_THREADS`/`MKL_NUM_THREADS`/`NUMEXPR_NUM_THREADS` =
  `HOST_GUARD_BLAS_THREADS` — additive alongside the script's existing `ulimit -v`/`MALLOC_ARENA_MAX`
  enforcement. Absent or `HOST_GUARD_ENABLED=0`: behavior unchanged (host-guard stays project-neutral).
- Apply the identical HOST-GUARD block to `scripts/dev.sh`'s **backend subshell only** (never the
  `next dev` frontend subshell), and have that subshell also mirror `start-backend.sh`'s existing
  `ulimit -v` + `MALLOC_ARENA_MAX` derivation (same `app.config.get_config()` values — no second
  computation). All values come from `host-guard.env`; no magic numbers hardcoded in either script.
- **Tighten the heavy-ingest regression test**
  (`test_start_backend_survives_back_to_back_heavy_ingest_under_memory_cap`,
  `apps/backend/tests/test_start_backend_script.py`): require `status == "ok"` (reject `"partial"`) for
  BOTH the rebuild and the backfill job, and assert each job's persisted `aggregates_refreshed` list
  contains every category expected for that job kind. Every pre-existing VmPeak/VmSize/health-poll
  assertion stays intact — re-read both boundaries of the edit before and after (iter-8's lesson: a prior
  edit was spliced into the middle of a test and silently deleted its real assertions).
- **If capacity allows (B2):** memoize the resolved libc `CDLL` handle inside `_release_process_memory()`
  (`app.engine.data_manager`) so `ctypes.util.find_library`/`ctypes.CDLL` resolves once (module-level,
  first-call-cached) instead of on every call — removing a redundant fork/exec on the exact
  memory-pressure abort path this session hardened. No change to `gc.collect()`/`malloc_trim` timing or
  effect.
- **New launcher-cap verification tests** (TC-7/TC-8/TC-9): `/proc/<pid>/status Cpus_allowed_list` and env
  vars match `host-guard.env` for both scripts' backend process; the SAME `dev.sh` run's frontend
  subshell shows none of these caps; both scripts start cleanly with no caps applied when
  `host-guard.env` is absent or `HOST_GUARD_ENABLED=0`.
- **Regression replay:** run J-01's golden replay, J-03's golden replay, and J-04's 6-step LLM acceptance
  against the current build; emit `reports/phase-goal-ops-hardening-iter-9-regression-replay-results.md`
  (iter-7 precedent format) — this is what moves all three out of `unknown`.
- **Live heavy-ingest re-measurement** under the NEW launcher caps (same conditions the browser-qa J-05
  step 4 check also exercises): retain a VmPeak/VmSize sampler CSV under `runs/goal-ops-hardening-iter-9/`,
  and add a dated additive section to `reports/perf-budgets.md` recording the applied
  `taskset`/thread-cap values alongside the VmPeak numbers (iter-8 lesson: a clean measurement under
  different host-guard settings than the failing run does not prove attribution — record the conditions).
- **Browser verification of J-05's four acceptance steps** in a real browser against a host-guard-capped
  live build (this is the actual point of `Frontend Present: yes` below — no UI code changes ship).

## Agents Required

- developer: yes -- backend/launcher-script changes (AG-10 fix), test hardening (heavy-ingest test +
  new launcher-cap tests), optional libc-handle memoization (B2), regression-replay evidence gathering
  (J-01/J-03/J-04), live VmPeak re-measurement, dev handoff.
- backend-data: yes -- same scope as above (launch scripts + `data_manager.py` + test files are all
  backend/ops surfaces; no separate backend-data role exists in this project's agent roster, `developer`
  covers it).
- frontend-ux: no -- zero frontend code changes this iteration (confirmed by the spec's own "Frontend:
  None" section); the `Frontend Present: yes` line below exists solely so browser-qa actually runs against
  J-01/J-03/J-04/J-05's already-shipped UI surfaces, per the corrective lesson iter-9 exists to apply
  (iter-8 wrote `Frontend Present: no` and the entire browser-qa lane was silently skipped even though its
  own TESTING REQUIREMENTS named browser journeys as mandatory).

## Frontend Present: yes

(No frontend code changes. `Frontend Present: yes` is set because this iteration's Definition of Done and
TESTING REQUIREMENTS name four browser journeys — J-01, J-03, J-04, J-05 — as mandatory acceptance
evidence against already-shipped UI surfaces (`/data`, `/scanner-runs`, the top-bar readiness badge, the
preflight banner). QA MUST run the Chrome MCP browser-qa lane; do not skip it on the basis of "no
frontend files in the diff.")

## Files to Create/Modify

- `scripts/start-backend.sh` -- add HOST-GUARD-marked block: source `host-guard.env` when present and
  `HOST_GUARD_ENABLED=1`, wrap the exec'd uvicorn with `taskset -c "$HOST_GUARD_CPU_LIST"`, export the
  BLAS/OMP/numexpr thread-cap env vars from `HOST_GUARD_BLAS_THREADS`; keep the existing `ulimit -v`/
  `MALLOC_ARENA_MAX`/logfile behavior unchanged when the file is absent or disabled.
- `scripts/dev.sh` -- apply the identical HOST-GUARD block to the backend subshell only; mirror the
  existing `ulimit -v` + `MALLOC_ARENA_MAX` derivation there too (reuse `app.config.get_config()`, do not
  recompute); the frontend (`next dev`) subshell is untouched.
- `apps/backend/tests/test_start_backend_script.py` -- tighten
  `test_start_backend_survives_back_to_back_heavy_ingest_under_memory_cap` (status `"ok"` only +
  `aggregates_refreshed` completeness for both jobs, all pre-existing assertions intact); add new
  launcher-cap verification tests (TC-7/TC-8/TC-9).
- `apps/backend/app/engine/data_manager.py` -- (B2, if capacity allows) memoize the resolved libc `CDLL`
  handle used by `_release_process_memory()`; no other logic change.
- `apps/backend/tests/test_data_manager.py` -- (if B2 lands) add a monkeypatched call-count test (TC-13)
  proving the libc-resolution path executes at most once across repeated
  `_release_process_memory()` calls.
- `reports/phase-goal-ops-hardening-iter-9-regression-replay-results.md` -- new: J-01 golden replay, J-03
  golden replay, J-04 6-step LLM acceptance outcomes.
- `reports/perf-budgets.md` -- additive dated section: fresh heavy-ingest VmPeak/VmSize measurement under
  the new launcher caps, with the applied `taskset`/thread-cap values recorded alongside.
- `runs/goal-ops-hardening-iter-9/*.csv` -- retained VmPeak/VmSize sampler CSV from the live heavy-ingest
  run (audit precedent, iter-8 recommendation item 1).
- `docs/handoffs/goal-ops-hardening-iter-9-dev.md` -- dev handoff; "Known Issues" carries forward the
  still-deferred on-load `/api/backtest` `MemoryError` (J-06/AG-8) and the unproduced J-05/J-06
  `demo.sh --session-live` walkthroughs (do not silently drop either).

**Do not touch** (settled, per `iteration-state.md`'s "Do not redo" + this spec's OUT OF SCOPE):
`app/api/health.py`, `app/engine/readiness.py`, `main.py`'s boot sequence, `warmup.py`,
`max_range_days`/`snapshot_cadence`/range-cap logic, the four-loop `MemoryError` early-abort handling
itself (done, iter-8), `project-extensions/host-guard/host-guard.env` (owner/framework file — do not flip
`HOST_GUARD_REQUIRE_MARKERS`), `server.memory_cap_mb` (raising it was considered and rejected in iter-8),
and `scripts/automation/*` (the harness's `Frontend Present: no` → skip-browser-qa bug is a framework
issue, explicitly routed around by this spec's own `Frontend Present: yes`, not fixed here).

## UI Evolution

- New user-facing capability: none.
- New information displayed: none.
- New user actions: none.
- UI surface changes: none.
- Navigation changes: none.

## Visual Requirements

- No new visual/component work. Browser-qa exercises EXISTING, already-shipped surfaces only: the `/data`
  backfill job form + persisted job-history panel, `/scanner-runs` leaderboard, the top-bar readiness
  badge, and the preflight/crash-unreachable banner. No new component patterns, layout, or visual effects
  to design this iteration.
- States to verify (not build): the initializing-with-phase-detail state, the crashed/unreachable state,
  the interrupted-job state, and the zero-work-vs-success distinction on `/data` — all pre-existing, being
  re-confirmed live, not created.

## Key Test Scenarios

- TC-1/TC-2: a `backfill` job for one unsnapshotted historical trading day reaches `status: "ok"` with a
  non-empty `aggregates_refreshed` array; `/scanner-runs` renders the stored leaderboard with no
  "computing…" placeholder.
- TC-3: market phase for that as-of is served from `market_phase_cache` with no live-recompute delay.
- TC-4: after a restart, `/data` cold-loads coverage within its committed budget with no full
  `daily_prices` prefill.
- TC-5/TC-6: `TRENDORA_RUN_HEAVY_INGEST_TEST=1` heavy-ingest test — full-universe rebuild immediately
  followed by a second heavy backfill in the same process — both reach `status: "ok"` (never `"partial"`),
  VmPeak/VmSize stay under `server.memory_cap_mb`'s KB ceiling, every `GET /api/health` poll returns 200,
  and each job's `aggregates_refreshed` list is fully complete for its kind.
- TC-7/TC-8: with `host-guard.env` present and enabled, both `start-backend.sh` and `dev.sh`'s backend
  subshell launch a process whose `Cpus_allowed_list` matches `HOST_GUARD_CPU_LIST` and whose environment
  carries the BLAS/OMP/numexpr thread caps; `dev.sh`'s effective `ulimit -v`/`MALLOC_ARENA_MAX` match
  config; the SAME script's frontend subshell shows none of these caps.
- TC-9: with `host-guard.env` absent or `HOST_GUARD_ENABLED=0`, both launch scripts start successfully
  with no caps applied and no error.
- TC-10/TC-11/TC-12: J-01 golden replay, J-03 golden replay, and J-04's 6-step LLM acceptance all pass and
  are recorded in `reports/phase-goal-ops-hardening-iter-9-regression-replay-results.md`.
- TC-13 (if B2 lands): a call-count test proves the libc-resolution path runs at most once across
  multiple `_release_process_memory()` invocations, with `gc.collect()`/`malloc_trim` still firing on every
  call.
- TC-14: QA/audit must read the RAW `reports/phase-goal-ops-hardening-iter-9-ui-test-results.llm.md`
  directly — never just the merged summary or `status.json` — before scoring any journey (iter-3/iter-4
  lesson).

## Notes / Out-of-scope carry-forwards (do not build these this iteration)

- The on-load `/api/backtest` → `forward_aggregates_cached` → `ScannerResult` `MemoryError` (J-06/AG-8) —
  record as unresolved carry-forward in the dev handoff, needs its own scoped iteration.
- The `[NEW]`-flagged `demo.sh ops-hardening --session-live` walkthroughs for J-05/J-06 — session-closeout
  showcase artifact, not a per-journey gate; obtain explicit human deferral before any GOAL_ACHIEVED gate.
- Flipping `HOST_GUARD_REQUIRE_MARKERS` in `host-guard.env` — owner/framework work, not this iteration's.
- Fixing the goal-mode harness's `Frontend Present: no` → skip-browser-qa misrouting in
  `scripts/automation/*` itself — framework/pipeline maintenance, out of this session's product scope;
  this plan's `Frontend Present: yes` line routes around it per the spec's own logged assumption.
- Do not run the full pytest suite concurrently with the live VmPeak/health measurement (standing
  constraint, iter-6 lesson on measurement contamination).
