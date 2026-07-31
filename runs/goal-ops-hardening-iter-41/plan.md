# goal-ops-hardening-iter-41 Execution Plan

## What to Build

This iteration has two headline closures (per the spec's own framing) plus small ride-along
fixes. No new UI capability — this is a verification-lane repair + one backend memory bound.

**A. Verification-lane repair (why: iter-40 shipped with all 7 required-still-passing journeys
completely unverified while every gate reported clean — auditor-only catch, 4th time in a row)**
1. Fix the health-check URL surfaced to the browser-qa LLM dispatch in `browser-qa-phase.sh`,
   `goal-iter-lean.sh`, and sibling `*-phase.sh` scripts that derive
   `BACKEND_HEALTH_URL="${CHAIN_BACKEND_HEALTH_URL:-http://localhost:${PORT}/health}"` — mirror
   `demo_runner.py`'s existing `resolve_backend_health_url` (already resolves `/api/health`, not
   `/health`, since iter-39). Must distinguish "connection refused" (down) from "any HTTP status
   including 404" (up) — never report a live backend on the wrong path as "down."
2. Fix `incredible_auto_dev/agents/ui-test-designer/body.md` ("Backend-only phase handling",
   currently lines 70-85): `Frontend Present: no` must stub out NEW-surface UI test generation
   ONLY. It must still emit one `UT-J-XX` regression test case per required-still-passing journey
   named in the iteration spec's metadata. Re-render `.claude/agents/ui-test-designer.md` via
   `python3 scripts/automation/sync-cli-assets.py --cli claude` before this iteration's own
   test-plan step runs — do not hand-edit the rendered mirror.
3. Extend `merge_ui_test_results.py` (additive to the already-shipped iter-40 `BLOCKED` class —
   do not reopen that mechanism): a merged result set with zero executed test cases for a
   required-still-passing journey must not produce a clean `SKIPPED`/`PASS` headline.
4. Add `BLOCKED` to `verdicts.py::BrowserQAVerdict` (today only `PASS`/`FAIL`/`SKIPPED`) and to
   the four `grep -oE 'PASS|FAIL|SKIPPED'` sites in `goal-iter-lean.sh` (audit iter-40 finding T3
   — currently fail-safe by accident, not by contract).

**B. Close the session's last unbounded whole-table load (AG-8, goal.md Success Criteria)**
5. Bound `_BarCache.prefill` (`apps/backend/app/engine/prices.py:129-162`): the DB cursor is
   already `.yield_per(batch)`-streamed (since before iter-35), but every row still accumulates
   into one resident `by_symbol` dict (~1.1 GB at the live basis, open since iter-29, distinct
   from iter-35/36/37's narrower fix which bounded only `membership_timeline_cached`'s cache-miss
   sub-call and explicitly left `prefill` itself untouched). Bound the resident accumulator while
   keeping byte-identical `Bar` output for every existing consumer (coverage payload,
   membership-timeline resolver, any other `_BarCache` caller). Reconcile/retire
   `test_bar_cache.py::test_kdate_backfill_loads_each_symbol_at_most_once` (line 372), which this
   global bound supersedes.
6. Measure full-universe prefill peak RSS/VmPeak before vs. after on the live basis; record in
   `reports/perf-budgets.md` (new "Iteration 41" section, same format as the existing "Iteration
   40" section) showing the bounded implementation strictly lower than the unbounded baseline.

**C. Diagnostics (ride-along on the same drill infra — NOT a cap retune, binding iter-39/40
instruction)**
7. Arm `faulthandler.register(signal.SIGUSR1, all_threads=True)` in the throwaway-DB wedge-drill
   launch (via `scripts/start-backend.sh`, same tightened-cap family as iter-39/40, never
   widened) and re-run the drill once. Report honestly whichever outcome occurs: a positively
   identified frozen thread/function, or a clean non-recurrence — never claim the freeze is fixed
   either way.
8. Extend `runs/.../wedge-drill/monitor.py` (iter-40 build; audit finding B2) to keep polling at
   the same interval for a fixed window PAST a terminal `job_status` instead of stopping the
   instant the row reads `ok`/`interrupted` — iter-39's wedge appeared in exactly that
   post-terminal window, which iter-40's drill never covered.

**D. Small, already-specified**
9. Add a count-based floor to `_checkpoint_run_record`'s existing 1.0 s time-based throttle
   (`data_manager.py:4085-4109`, `_RUN_RECORD_CHECKPOINT_INTERVAL_S`): force a checkpoint write
   on every Kth date regardless of elapsed time. Same `message` field, same `_run_detail()`
   serializer, no new persisted field — dev Known Issue #2 from iter-40's own handoff.

## Agents Required

- developer: yes -- implements all of A1-A4, B5-B6, C7-C8, D9 above (Python backend + bash
  pipeline tooling + pytest). No frontend code changes (spec: "Frontend: None").
- No separate frontend-focused agent is needed; this iteration's UI-chain work is limited to the
  ui-test-designer neutral-source fix (A2), which the developer edits directly like any other
  source file, then re-renders.

## Frontend Present

Frontend Present: no

(No new UI surface, no frontend file changes — per the phase spec's own metadata and "Product
surface delta: None visible to the end user." The existing `/data`, `/backtest`, and top-bar
badge surfaces are exercised only as REGRESSION checks for J-01/J-03/J-04/J-06/J-08/J-09, using
whatever browser/replay verification the fixed pipeline (item A) produces — this plan does not
add or change any UI code.)

## Files to Create/Modify

- `incredible_auto_dev/scripts/automation/browser-qa-phase.sh` -- fix `BACKEND_HEALTH_URL`
  derivation to resolve `/api/health` (mirror `demo_runner.py:165-183`
  `resolve_backend_health_url`); treat any HTTP status as "up," only connection failure as "down."
- `incredible_auto_dev/scripts/automation/goal-iter-lean.sh` -- same health-URL fix; also update
  the four `grep -oE 'PASS|FAIL|SKIPPED'` sites (~lines 484, 531, 890, 1221) to also match
  `BLOCKED`.
- `incredible_auto_dev/scripts/automation/qa-phase.sh` -- same health-URL fix (sibling
  `*-phase.sh` pattern at line 89).
- `incredible_auto_dev/scripts/automation/demo-phase.sh` -- same health-URL fix (sibling pattern
  at line 191).
- `incredible_auto_dev/scripts/automation/run-phase.sh` -- same health-URL fix (pattern at line
  218).
- Consider factoring the shared resolution logic into one bash helper (e.g. in
  `incredible_auto_dev/scripts/automation/lib/common.sh`) sourced by all five scripts above,
  instead of duplicating the same project-specific override five times — avoids the exact drift
  this bug came from (`demo_runner.py` was fixed at iter-39; the shell scripts were not).
- `incredible_auto_dev/agents/ui-test-designer/body.md` -- neutral source: rewrite "Backend-only
  phase handling" (current lines 70-85) so `Frontend Present: no` stubs NEW-surface tests only,
  still emitting one `UT-J-XX` per required-still-passing journey.
- `.claude/agents/ui-test-designer.md` -- regenerate via
  `python3 scripts/automation/sync-cli-assets.py --cli claude` (never hand-edit).
- `incredible_auto_dev/scripts/automation/lib/merge_ui_test_results.py` -- add all-SKIP /
  zero-executed detection for required-still-passing journeys so it cannot merge into a clean
  `SKIPPED`/`PASS` headline; extend `compute_overall`/`parse_rows` and the self-test suite.
- `incredible_auto_dev/scripts/automation/lib/verdicts.py` -- add `BLOCKED` to
  `BrowserQAVerdict` (currently `PASS`/`FAIL`/`SKIPPED` only, line ~56-60).
- `apps/backend/app/engine/prices.py` -- bound `_BarCache.prefill`'s (lines 129-162) resident
  `by_symbol` accumulator; keep the existing `.yield_per(batch)` cursor.
- `apps/backend/tests/test_bar_cache.py` -- add a fixture-backed byte-identity test (old vs. new
  prefill output); reconcile/retire `test_kdate_backfill_loads_each_symbol_at_most_once` (line
  372).
- `apps/backend/app/engine/data_manager.py` -- add a count-based floor to
  `_checkpoint_run_record` / `_RUN_RECORD_CHECKPOINT_INTERVAL_S` (lines 4085-4120); `JobProgress`
  (~line 2060-2100) gains whatever internal counter the floor needs (unserialized scratch field,
  matching the existing `_last_checkpoint_monotonic` pattern).
- `apps/backend/tests/test_data_manager.py` -- add the count-based-floor unit test (TC-8).
- `reports/perf-budgets.md` -- new "Iteration 41" section: prefill RSS/VmPeak before/after
  measurement.
- `runs/goal-ops-hardening-iter-41/wedge-drill/` -- drill scratch config, `monitor.py` extended
  with post-terminal polling window, `faulthandler` SIGUSR1 arm, live evidence (`README.md`
  index), mirroring the shape of `runs/goal-ops-hardening-iter-40/wedge-drill/`.
- `docs/handoffs/goal-ops-hardening-iter-41-dev.md` -- dev handoff (required by DoD).

## UI Evolution

N/A — Frontend Present: no, no new UI surface (see Frontend Present section above).

## Visual Requirements

N/A — no UI code changes this iteration.

## Key Test Scenarios

- TC-1: `Frontend Present: no` + 6 named required-still-passing journeys →
  `reports/phase-goal-ops-hardening-iter-41-ui-test-plan.md` contains one `UT-J-XX` per required
  journey, zero NEW-surface cases.
- TC-2: backend mounted at `/api/health` (not `/health`) → the URL surfaced to browser-qa
  dispatch resolves to `.../api/health`; a wrong-path 404 is never reported as "backend down."
- TC-3: merged results with zero executed cases for a required journey → merged verdict is NOT a
  clean `SKIPPED`/`PASS`; surfaces as an unmet DoD item to the evaluator/`closure_gate.py`.
- TC-4: after re-rendering `ui-test-designer.md`, browser-qa executes J-01/J-03/J-04/J-06/J-08/J-09
  and each produces a fresh, dated evidence artifact under THIS iteration's own report/evidence
  path — not a reference to iter-39/40's artifacts.
- TC-5: wedge-drill with `faulthandler` SIGUSR1 armed, re-run once → either a freeze recurs and
  `SIGUSR1` writes an identifying all-thread stack dump, or it does not recur and the log honestly
  records that without claiming "fixed."
- TC-6: `_BarCache.prefill` old vs. new implementation, same fixture inputs → every returned `Bar`
  byte-identical for every symbol/date; full-universe peak RSS/VmPeak measured and recorded lower
  than the unbounded baseline in `reports/perf-budgets.md`.
- TC-7: `wedge-drill/monitor.py` polling a job that reaches terminal `job_status` → monitor
  continues polling at the same interval for a fixed additional window, recording every poll.
- TC-8: `_checkpoint_run_record`'s 1.0 s throttle with K dates completing inside one interval
  (mocked clock) → a count-based floor forces a checkpoint write on the Kth date regardless of
  elapsed time.
- TC-9: `BLOCKED` verdict emitted → `BrowserQAVerdict` accepts it as a legal enum member, and all
  four `goal-iter-lean.sh` grep sites also match it.
- Backend regression: full `apps/backend/tests/` suite still passes (per iter-40's own note this
  can be slow on the 30y basis — do not treat buffered progress as hung); at minimum
  `test_bar_cache.py`, `test_data_manager.py`, `test_data_manager_jobs_pipeline.py` targeted runs
  must pass.
- `merge_ui_test_results.py self-test` and `incredible_auto_dev/tests/automation/test-replay-lane.sh`
  both still pass after the tooling changes.
- AG-10 respected: all drill launches go only through `scripts/start-backend.sh`, host-guard caps
  intact, no `server.memory_cap_mb` retune (diagnostic-only per binding iter-39/40 instruction).
- AG-9 respected: no live network calls introduced; drills run offline against seeded/scratch DBs.

## Notes / Out of Scope (per spec, do not implement)

- iter-33/g Regime Lab cold `view=pooled` dispatch — deferred a 6th time.
- Any re-tuning of `server.memory_cap_mb` — cap trials are done; this iteration only instruments
  the same cap.
- J-07's `[NEW]` walkthrough recording — capture-only, not this iteration's goal.
- The two owner-decision items (iter-34/j `/api/health` ≤0.1s budget; iter-33/i
  `start-frontend.sh` host-guard membership) — carried forward unplanned, owner must settle before
  any GOAL_ACHIEVED attempt.
- Re-opening `_missing_data_diagnostic`'s streaming fix, the time-based checkpoint cadence
  redesign, the `BLOCKED` verdict class itself (already shipped iter-40), or J-07 steps 1-3 /
  step-4 isolation — all DONE/CLOSED per `iteration-state.md`'s binding "Do not redo" list.
- Any launch-script or `host-guard.env` change — AG-10's byte-frozen launch scripts stay
  untouched; drills still launch exclusively via `scripts/start-backend.sh`.
