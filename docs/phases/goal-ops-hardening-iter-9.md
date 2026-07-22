# Goal Iteration 9 — Session closeout: verify J-05's recovery live, close the AG-10 launcher gap, and clear the J-01/J-03/J-04 evidence gap

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** ops-hardening
- **Iteration:** 9
- **Mode:** next
- **Depth:** full
- **Frontend Present:** yes
- **Target journeys:** J-05
- **Required-still-passing journeys:** J-01, J-03, J-04
- **Anti-goal reminders:**
  - **AG-1:** A score, ranking, or "edge" MUST NOT be presented as proven/confident unless it is backed by a
    **passing certified-claim entry** in the evidence ledger (out-of-sample, control-beating). Unbacked
    values MUST render a "not yet proven" state. *(critical)*
  - **AG-2 — Decision-quality only:** never present return promises, price targets, "buy/sell" signals, or alpha
    claims; never place or simulate orders. *(critical)*
  - **AG-3:** A journey passes ONLY if the **displayed numbers are correct** — they match the engine's computation
    for the same as-of date — not merely that the page renders. *(critical)*
  - **AG-4 — No overfit edges:** any pattern surfaced as "proven" must have survived the referee (sealed
    out-of-sample holdout + controls + multiple-testing correction), never in-sample fit alone. *(critical)*
  - **AG-5 — Preserve determinism and no-lookahead:** scoring uses bars ≤ as-of; forward returns use bars > as-of;
    never introduce lookahead anywhere. *(critical)*
  - **AG-6:** No iteration ships if its evidence-derived claims (if any) lack a passing referee verdict from the
    post-decompose gate. *(critical)*
  - **AG-7:** No hard-coded credentials, API keys, or tokens in source files. *(critical)*
  - **AG-8 — Resilience to data-shape and data-scale change:** widening the data basis (new nulls, broader pools, deeper history) must never crash an existing page or exhaust a service's memory — every
    existing consumer of a widened field is re-validated, the UI degrades gracefully (contained error
    boundary, honest "—"/NA placeholder, never a blank application-error page), and unbounded
    whole-table ORM loads are forbidden on the deep basis. *(critical)*
  - **AG-9 — Offline-deterministic ingest:** ingest jobs (fetch/backfill/rebuild) run only
    against the committed seed / local provider fixtures — no live external network calls or
    paid data services may be introduced without an explicit goal.md amendment. *(critical)*
  - **AG-10 — Host resource ceiling (hardware protection):** heavy compute — backfills,
    full-universe rebuilds, measurement passes, load drills, test-suite bursts — MUST be launched
    only via the project launch scripts (`scripts/dev.sh` / `scripts/start-backend.sh`), and those
    scripts MUST apply the host caps declared in `project-extensions/host-guard/host-guard.env`
    whenever that file is present (CPU-affinity mask, BLAS/OMP thread caps, `memory_cap_mb`,
    `malloc_arena_max`). Never remove, weaken, or bypass these caps: stripping a HOST-GUARD
    marked block from a launch script is a REGRESSION regardless of test outcomes. The ceilings
    are a physical constraint of the current host (two instant hardware resets under all-core
    vectorized ingest bursts: 2026-07-20 19:17, 2026-07-21 10:33), not a performance budget to
    optimize away. *(critical)*

## GOAL

Close out this session's last budgeted iteration by (a) live-verifying, in a real browser under
host-guard-capped launch conditions, that J-05's four-step acceptance genuinely holds after iter-8's
`MemoryError`-hardening fix — the thing iter-8 shipped but never checked — (b) clearing the J-01/J-03/J-04
evidence gap iter-8 also left behind, and (c) closing the still-open, goal.md-scheduled AG-10 launcher
gap so every heavy-compute path this session protects is actually running under the declared host caps.

## BACKGROUND

`iteration-state.md` after iter-8: 0 passing, 1 `regressed` (J-05, carried from iter-7, never
re-verified by iter-8), 3 `unknown` (J-01/J-03/J-04 — their replay/LLM lanes simply never ran in iter-8),
1 `partial` (J-06, out of scope). `session.json`'s `max_iterations: 9` makes this the **last budgeted
iteration** — the evaluator's iter-8 recommendation is explicit: "a pure VERIFICATION-AND-COMPLIANCE
closeout, no new features." Per the priority rubric, rule 1 (regressed journeys outrank all new work)
keeps J-05 the sole **target**; J-01/J-03/J-04 are **required-still-passing** re-verification, not new
targets, since nothing in iter-8's diff is suspected of breaking them — they simply have no fresh
evidence (iter-5's own precedent: absence of evidence is scored `unknown`, not `regressed`, and this
iteration's job is to close that gap, not repeat the diagnosis). No second risky journey is bundled
(rule 5): the AG-10 launcher fix and the T4 test-hardening/B2 hygiene carry-ins are small, mechanical,
config-driven changes to the SAME launch scripts and SAME regression-guard test J-05's own verification
already depends on — not a second product journey.

**Root failure this iteration exists to fix.** iter-8's dev handoff, review, and QA all reported success,
but the phase spec literally wrote `Frontend Present: no`, which caused the ENTIRE browser-qa lane to be
skipped (`ui-test-results.md` = "SKIPPED", `status.json browser_checks_run: false`, no evidence
directory at all) even though iter-8's own TESTING REQUIREMENTS named J-05's four browser steps as
mandatory. Lesson applied verbatim (`lessons.md` iter-8, entry 1): *"'No frontend CODE changed' is not
'no journey needs browser verification'... check `browser_checks_run` and the existence of the evidence
directory before believing any completion claim."* This spec sets **`Frontend Present: yes`** explicitly
— this iteration's TESTING REQUIREMENTS name four browser journeys, so that is the honest value
regardless of whether any frontend *code* changes (see the NOTES section and the assumption logged to
`assumptions.md` for why this iteration does not instead patch the goal-mode harness scripts themselves).

**Depth is full**, citing trigger 1 (structural/cross-cutting): the AG-10 fix touches the launch scripts
every journey boots through (`scripts/start-backend.sh`, `scripts/dev.sh`'s backend subshell,
`project-extensions/host-guard/host-guard.env`) — a change whose correctness is only provable by
re-running the FULL live verification battery (J-05's heavy-ingest test, J-01/J-03/J-04 replay) under the
new caps, not by any single journey's own unit tests. This is also the session's REGRESSION-recovery
closeout; per iter-7's own precedent (`assumptions.md`, iter-7 — goal-decomposer), only the full
pipeline's audit + closure steps can certify a regression recovery's evidence chain, which a lean cycle
(developer → reviewer → browser-qa only) does not produce. Not cited: trigger 3 (prior verdict was
CONTINUE, not ESCALATE) or trigger 4 (consecutive-lean counter is 0 — cadence not met).

**Lessons applied, beyond the Frontend-Present one above:**
- (iter-8, entry 3) *"A ~220-line block was pasted into the MIDDLE of an existing test... silently
  deleting that test's real assertions."* This iteration edits
  `test_start_backend_survives_back_to_back_heavy_ingest_under_memory_cap` in place (T4) — re-read the
  function's full boundaries before and after the edit; the existing VmPeak/VmSize/health-poll assertions
  must remain intact, only the `status` check and an `aggregates_refreshed`-completeness check tighten.
- (iter-8, entry 2) A clean measurement under DIFFERENT host-guard settings than the failing run does not
  prove attribution. This iteration's live measurements (J-05 step 4, the heavy-ingest test) must run
  under the SAME host-guard caps the AG-10 fix now makes the launch scripts apply automatically — record
  the applied `taskset`/thread-cap values alongside the VmPeak numbers so a future reader is not left to
  guess whether conditions matched.
- (iter-6) Measure on an otherwise-idle host; do not run the full pytest suite concurrently with a live
  VmPeak/health measurement (also the pump's own standing constraint).
- (iter-3/iter-4) Read the RAW `...-ui-test-results.llm.md`, never just the merged summary or
  `status.json`, before scoring any journey.

**Coherence:** `runs/goal-session-ops-hardening/iter-8/coherence.md` = COHERENCE-PASS, no consolidation
mandate — this iteration is free to proceed with normal target selection.

## IN SCOPE

### Backend
- [ ] Close the AG-10 launcher gap: add a HOST-GUARD-marked block to `scripts/start-backend.sh` that,
      when `project-extensions/host-guard/host-guard.env` is present and `HOST_GUARD_ENABLED=1`, sources
      it and wraps the exec'd `uvicorn` process with `taskset -c "$HOST_GUARD_CPU_LIST"` plus exported
      `OMP_NUM_THREADS` / `OPENBLAS_NUM_THREADS` / `MKL_NUM_THREADS` / `NUMEXPR_NUM_THREADS` set to
      `HOST_GUARD_BLAS_THREADS` — alongside (not replacing) the script's existing config-derived
      `ulimit -v` / `MALLOC_ARENA_MAX` enforcement. Absent or `HOST_GUARD_ENABLED=0`: behavior unchanged
      (host-guard stays project-neutral per its own header contract).
- [ ] Apply the identical HOST-GUARD block to `scripts/dev.sh`'s **backend subshell only** (never the
      frontend/`next dev` subshell — it needs the address space), and have that subshell also mirror
      `start-backend.sh`'s existing `ulimit -v` + `MALLOC_ARENA_MAX` derivation (same
      `app.config.get_config()` values, no second computation of them). `dev.sh` currently applies no
      caps at all (confirmed iter-8) — this closes that gap goal.md itself schedules as "in-scope
      launcher work for the next iteration."
- [ ] All values come from `host-guard.env` — no magic numbers hardcoded into either script.
- [ ] Tighten `test_start_backend_survives_back_to_back_heavy_ingest_under_memory_cap`
      (`apps/backend/tests/test_start_backend_script.py`) to require `status == "ok"` (reject
      `"partial"`) for BOTH the rebuild and the backfill job, and to assert each job's persisted record
      shows an `aggregates_refreshed` list containing every category expected for that job kind — proving
      no per-item warm loop silently early-aborted on a `MemoryError` during this run. Every existing
      VmPeak/VmSize/health-poll assertion in this test stays intact (see lesson above — do not splice,
      re-read both boundaries of the edit).
- [ ] If capacity allows after the above: memoize the resolved libc `CDLL` handle inside
      `_release_process_memory()` (`app.engine.data_manager`) — resolve `ctypes.util.find_library` /
      `ctypes.CDLL` once (module-level, first-call-cached) instead of on every invocation, so repeated
      calls during one heavy ingest's per-item `MemoryError`-abort path stop re-triggering a
      library-resolution fork/exec on the exact memory-pressure path this session is hardening. No change
      to `gc.collect()` / `malloc_trim` timing or effect — byte-identical behavior, fewer redundant
      subprocess spawns only.
- [ ] Run J-01's golden replay, J-03's golden replay, and J-04's 6-step LLM acceptance against the
      current build and emit `reports/phase-goal-ops-hardening-iter-9-regression-replay-results.md`
      (iter-7 precedent) — this is what moves all three out of `unknown`.
- [ ] No change to `app/api/health.py`, `app/engine/readiness.py`, `main.py`'s boot sequence, or any
      already-registered Data Contract value's computing module/endpoint (see "Do not redo" below).

### Frontend
None. No UI code changes — `Frontend Present: yes` reflects that this iteration's DEFINITION OF DONE
requires real-browser verification of J-01, J-03, J-04, and J-05 (all already-shipped UI surfaces), not
that new frontend code ships.

### New user-facing capability
None (verification + a launcher/host-safety compliance fix; no new feature).

### New information displayed
None.

### New user actions
None.

### UI surface changes
None.

### Product surface delta
None to the product surfaces themselves. The operational guarantee strengthens: every heavy-compute path
(backfill/rebuild/measurement) now runs under the SAME declared CPU/thread/memory ceilings whether
launched via `scripts/start-backend.sh` or `scripts/dev.sh`'s backend subshell, and J-05's "aggregates
precomputed at ingest, health stays responsive" promise is confirmed live rather than asserted from a
prior, differently-configured run.

### Blueprint conformance
No new surfaces. All touched rows — "Job history & per-date exclusion reasons" (the
`_refresh_ingest_aggregates` finalize hook, T4/B2 changes), "Backend readiness / boot phase + preflight
verdict" (`GET /api/health`, re-verified only, not modified) — already have their homes in
`blueprint.md`. The AG-10 launcher scripts are not a Data Contract value or a UI page; they are a
cross-cutting operational concern already documented in `blueprint.md`'s framing notes.

### Data-contract additions
None. No new field, no new computing module, no new serving endpoint. This iteration only (a) hardens an
existing test's assertions, (b) changes internal fork/exec behavior of an already-internal helper
(`_release_process_memory`) with no observable value change, and (c) makes two launch scripts apply
config that already exists (`host-guard.env`) — no new displayed value anywhere.

## OUT OF SCOPE

- The on-load `/api/backtest` → `forward_aggregates_cached` → `ScannerResult` `MemoryError` (a distinct
  J-06/AG-8 concern, deferred since iter-8's eval item 6) — needs its own scoped iteration; this session
  is out of budget (`max_iterations: 9`) to take it up, so it is recorded here as unresolved carry-forward
  work for a human decision (new iteration budget, or explicit deferral) rather than silently dropped.
- The `[NEW]`-flagged `demo.sh ops-hardening --session-live` walkthroughs for J-05 and J-06 — still a
  session-closeout showcase artifact per the standing assumption (`assumptions.md`, iter-4/iter-5), not a
  per-journey passing gate. Produce them or obtain explicit human deferral before any GOAL_ACHIEVED gate;
  this iteration does not manufacture them as new scope.
- Flipping `HOST_GUARD_REQUIRE_MARKERS` from `0` to `1` in `project-extensions/host-guard/host-guard.env`
  — that file is explicitly owner/framework work per goal.md's own binding note ("The sampler,
  `run-goal.sh` preflight, and `host-guard.env` itself are owner/framework work, not product scope"); this
  iteration only makes the two launch scripts apply the caps the file ALREADY declares.
- Fixing the goal-mode/phase-mode harness's `Frontend Present: no`→skip-browser-qa misrouting itself
  (`scripts/automation/*`) — a framework/pipeline bug, not this session's product scope; this spec routes
  around it by declaring the honest `Frontend Present: yes` (see NOTES + `assumptions.md`).
- Re-implementing or re-touching the four-loop `MemoryError` early-abort fix, the audit's B1/T1/T2/T3
  repairs, iter-7's `/evidence` `drawdown_expectations` warm, `readiness.py` / `main.py` / `warmup.py`, or
  `max_range_days` / `snapshot_cadence` / range-cap logic — all settled ("Do not redo",
  `iteration-state.md`).
- Raising `server.memory_cap_mb` as a workaround (considered and rejected, iter-8 `assumptions.md`).
- A second computing module, a second endpoint, or a second cache table for any already-registered Data
  Contract value.
- Loosening any committed budget number in `reports/perf-budgets.md` — only additive, honestly-measured
  rows (a fresh dated section for this iteration's heavy-ingest re-measurement under the new launcher
  caps).

## DEFINITION OF DONE

- [ ] J-05 passes all four acceptance steps via browser-qa-agent in a REAL browser, driven by a live
      build with the AG-10 launcher fix active — including step 4's heavy-ingest health-responsiveness
      check, run at least once via
      `TRENDORA_RUN_HEAVY_INGEST_TEST=1 apps/backend/.venv/bin/pytest apps/backend/tests/test_start_backend_script.py::test_start_backend_survives_back_to_back_heavy_ingest_under_memory_cap -v`
      on an idle host — and the RAW `reports/phase-goal-ops-hardening-iter-9-ui-test-results.llm.md` is
      read directly (not just the merged table or `status.json`) before scoring.
- [ ] `reports/phase-goal-ops-hardening-iter-9-regression-replay-results.md` records J-01 (golden replay),
      J-03 (golden replay), and J-04 (6-step LLM acceptance) all passing — moving all three out of
      `unknown`.
- [ ] `scripts/start-backend.sh` and `scripts/dev.sh`'s backend subshell apply `host-guard.env`'s
      `taskset` CPU-affinity mask and BLAS/OMP/numexpr thread caps whenever that file is present and
      enabled; `dev.sh`'s backend subshell additionally mirrors the existing `ulimit -v` +
      `MALLOC_ARENA_MAX` enforcement; `dev.sh`'s frontend subshell is unmodified. AG-10 recorded resolved
      (not merely mitigated) in this iteration's eval.
- [ ] The heavy-ingest regression test rejects `"partial"` and asserts full `aggregates_refreshed`
      completeness for both jobs, with every pre-existing assertion in the test still present and passing.
- [ ] A VmPeak/VmSize sampler CSV from the live heavy-ingest run is retained under
      `runs/goal-ops-hardening-iter-9/` (audit precedent, iter-8 recommendation item 1).
- [ ] No anti-goal violation introduced; AG-10 closed, AG-8 assessed for closure with fresh
      host-guard-consistent live evidence (not evidence gathered under different host conditions than the
      originally-failing run — iter-8 lesson).
- [ ] Unit tests pass; no regressions — exact command and pass/fail counts recorded in the dev handoff
      (targeted files only; do not run the full suite concurrently with the live VmPeak measurement).
- [ ] Dev handoff written at `docs/handoffs/goal-ops-hardening-iter-9-dev.md`, with its "Known Issues"
      section carrying forward the still-deferred on-load `/api/backtest` `MemoryError` (J-06/AG-8) and
      the unproduced J-05/J-06 `demo.sh --session-live` walkthroughs — not silently dropped.

## TESTING REQUIREMENTS

- Browser: J-05 (all 4 steps, real browser, host-guard-capped build). Required-still-passing: J-01
  (deterministic golden replay), J-03 (deterministic golden replay), J-04 (LLM 6-step acceptance).
- Unit/integration: the tightened heavy-ingest test (`test_start_backend_survives_back_to_back_heavy_ingest_under_memory_cap`),
  a `taskset`/env-cap verification for both launch scripts, and (if B2 lands) a call-count assertion on
  the libc-handle memoization.
- Error cases: a launch with `host-guard.env` absent or `HOST_GUARD_ENABLED=0` must leave both scripts'
  behavior unchanged (no caps applied, no crash); a heavy-ingest run that DOES hit a `MemoryError` in one
  warm loop must still report `status == "ok"` with a partial (not full) `aggregates_refreshed` list for
  that job's affected category only, never silently dropped or fabricated.

Test-first contract:

- TC-1: given a build with this iteration's launcher fix and host-guard active, when browser-qa runs
  J-05 step 1 (start a `backfill` job for one unsnapshotted historical trading day, e.g. 2026-05-15, on
  `/data`), then the job reaches terminal status `"ok"` and `GET /api/data`'s persisted run record for
  that job lists a non-empty `aggregates_refreshed` array.
- TC-2: given the job from TC-1 completed, when the browser visits `/scanner-runs` and opens that date's
  run, then the leaderboard table renders rows matching the stored `scanner_results` snapshot for that
  as-of, with no "computing…" placeholder.
- TC-3: given the job from TC-1 completed, when market phase for that as-of is requested, then the
  response is served from the persisted `market_phase_cache` row with no live-recompute delay.
- TC-4: given the backend is restarted after TC-1's ingest, when the browser loads `/data` cold, then the
  coverage panel renders within its committed budget in `reports/perf-budgets.md` and the backend process
  performs no full `daily_prices` table prefill for that request.
- TC-5: given `TRENDORA_RUN_HEAVY_INGEST_TEST=1` is set and the AG-10 launcher fix is active, when
  `test_start_backend_survives_back_to_back_heavy_ingest_under_memory_cap` runs a full-universe rebuild
  immediately followed by a second heavy backfill in the same spawned process, then both jobs reach
  status `"ok"` (not `"partial"`), peak `VmPeak`/`VmSize` stay under `server.memory_cap_mb`'s KB ceiling,
  and every `GET /api/health` poll during the run returns HTTP 200 with zero timeouts.
- TC-6: given the same test run as TC-5, when each job's persisted record is inspected, then each
  `aggregates_refreshed` list contains every category expected for that job kind, proving no loop
  silently early-aborted on `MemoryError`.
- TC-7: given `project-extensions/host-guard/host-guard.env` present with `HOST_GUARD_ENABLED=1`, when
  `scripts/start-backend.sh` launches the backend, then the launched process's
  `/proc/<pid>/status Cpus_allowed_list` matches `HOST_GUARD_CPU_LIST` and its environment shows
  `OMP_NUM_THREADS` (and sibling BLAS vars) set to `HOST_GUARD_BLAS_THREADS`.
- TC-8: given the same `host-guard.env`, when `scripts/dev.sh`'s backend subshell launches uvicorn, then
  its `Cpus_allowed_list` matches `HOST_GUARD_CPU_LIST`, its effective `ulimit -v` equals
  `server.memory_cap_mb * 1024` KiB, and `MALLOC_ARENA_MAX` is exported — while the SAME script's
  frontend (`next dev`) subshell process shows none of these caps applied.
- TC-9: given `host-guard.env` is absent (or `HOST_GUARD_ENABLED=0`), when either launch script runs,
  then it starts successfully with no caps applied and no error — host-guard stays fully optional.
- TC-10: given J-01's stored golden replay script, when it is run against the current build, then every
  step passes (or, if one step misses on a stale-data proxy per the iter-5 precedent, it is explicitly
  adjudicated in the regression-replay-results artifact rather than auto-scored a regression) and the
  outcome is recorded in `reports/phase-goal-ops-hardening-iter-9-regression-replay-results.md`.
- TC-11: given J-03's stored golden replay script, when it is run against the current build, then it
  passes and the outcome is recorded in the same artifact.
- TC-12: given J-04's 6-step acceptance (boot-to-health timing, pre-ready phase detail, crash
  presentation, interrupted-job detection), when it is LLM-verified live against the current build, then
  all 6 steps pass and the outcome is recorded in the same artifact.
- TC-13: given (if B2 lands) a unit test that monkeypatches `ctypes.util.find_library`/`ctypes.CDLL` with
  a call counter, when `_release_process_memory()` is invoked multiple times within one process lifetime,
  then the library-resolution path executes at most once; every call still performs `gc.collect()` +
  `malloc_trim` with unchanged effect.
- TC-14: given the completed iter-9 browser-qa run, when the RAW
  `reports/phase-goal-ops-hardening-iter-9-ui-test-results.llm.md` is read directly, then its per-journey
  verdict lines are the ones scored — never the merged summary or `status.json` alone (iter-3/iter-4
  merge-script drift lesson).

## NOTES

- **Assumption logged** (`assumptions.md`, iter-9 — goal-decomposer): this iteration deliberately does
  NOT implement the evaluator's iter-8 next-step item 4 ("fix the harness misrouting so `Frontend
  Present: no` cannot suppress browser-qa") as framework code. Instead it sets this spec's own
  `Frontend Present: yes` line, which is the honest value for an iteration whose TESTING REQUIREMENTS name
  four browser journeys — sidestepping the bug without touching `scripts/automation/*` (framework/pipeline
  maintenance, out of this session's product scope per CLAUDE.md's asset-source routing). The underlying
  harness bug remains unfixed and could recur if a future spec sets `Frontend Present: no` while still
  naming browser journeys in TESTING REQUIREMENTS — flagged for the framework maintainer, not fixed here.
- If, after TC-1 through TC-9 pass and J-05/AG-10 are scored resolved, J-01/J-03/J-04 all pass and J-06
  stays the only non-`passing` journey (still `partial`, its own gaps already scoped out per iter-5/6/7),
  the evaluator should weigh whether the session is at (or near) `GOAL_ACHIEVED` given `max_iterations: 9`
  — noting the two still-outstanding closure items (the deferred `/api/backtest` on-load `MemoryError`
  and the J-05/J-06 `--session-live` walkthroughs) both need an explicit human call (new budget, scope
  amendment, or accepted deferral) rather than the evaluator inventing either resolution.
- Do not run the full pytest suite concurrently with the live VmPeak/health measurement (pump standing
  constraint + iter-6 lesson on measurement contamination).
