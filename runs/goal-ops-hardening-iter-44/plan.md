# goal-ops-hardening-iter-44 Execution Plan

## Environment note
Before running any test/build/live-drill command, export:
`TMPDIR="/home/dennis-chan/.cache/iad/iad.goal-ops-harde-845d9bcd.18723" TMP="/home/dennis-chan/.cache/iad/iad.goal-ops-harde-845d9bcd.18723" TEMP="/home/dennis-chan/.cache/iad/iad.goal-ops-harde-845d9bcd.18723"`

**Do NOT run the full pytest suite** (≈10h on the 30-year basis, forks-locks the box). Run only the
targeted test files/`-k` selections named below. All heavy compute (the live warm reproduction, the
subprocess shutdown test) MUST launch only via `scripts/start-backend.sh` (AG-10) — never a bare
`uvicorn`/`python -m` invocation.

## What to Build
- Wire `ServerOpsCfg`'s three already-declared, never-enforced values
  (`limit_concurrency` / `timeout_keep_alive_seconds` / `graceful_timeout_seconds`) into
  `incredible_auto_dev/scripts/start-backend.sh`'s uvicorn `exec` line as `--limit-concurrency` /
  `--timeout-keep-alive` / `--timeout-graceful-shutdown`, read from `get_config().server` exactly like
  the existing `memory_cap_mb`/`malloc_arena_max` block immediately above the `exec` line. No magic
  numbers. `scripts/dev.sh` is untouched (out of scope).
- Live-reproduce J-07 step 1's stall: launch via `start-backend.sh` with
  `TRENDORA_DIAG_FAULTHANDLER_SIGUSR1=1`, trigger the full-deep-basis historical forward-aggregate warm
  with ONE single trigger (no manual mid-run `/api/backtest` probing — the iter-43 dev's own disclosed
  confound), poll `GET /api/health`'s `background_compute.active[].horizons_done` via the existing
  accessor. When `horizons_done` has not advanced for a bounded window past `started_at`, send
  `kill -USR1 <pid>` and capture the resulting `faulthandler.dump_traceback` all-thread output verbatim
  in the dev handoff (`main.py:63-67` already arms this on the env var — confirmed present, never fired
  at a genuine freeze until now). Name the exact blocked call/lock, not a re-citation of iter-43's two
  unconfirmed candidates (T2 `_SymbolColumns` slicing cost vs. the self-inflicted concurrent-dispatch
  confound).
- Apply the smallest correct fix at the identified blocking site so a fresh reproduction of the same
  warm advances/terminates — OR, if the true fix needs materially larger unevidenced work, document the
  exact finding (named blocked call, stack excerpt) for evaluator/owner disposition instead of
  re-claiming it fixed. Any new except/guard clause must be keyed to the diagnosed incident's WHOLE
  exception set (binding iter-43 lesson), confirmed against what the live dump/log actually produced —
  not just its headline exception.
- Re-measure J-07's rescoped ≤2s bounded-compute-window `/api/health` budget and the concurrent cached
  `GET /api/backtest` read with the SAME single trigger used for the diagnostic (one clean run covers
  both the diagnostic and the re-measurement — do not re-trigger a second warm only to re-measure).
  Record a fresh dated section in `reports/perf-budgets.md`.
- `apps/backend/app/api/data.py`'s `retry_job` (~line 309, the `data_manager.retry_run(...)` call) —
  wrap in the SAME `except (RuntimeError, MemoryError)` → `HTTPException(503, ...)` handling
  `start_job` (`:202`) and `resume_job` already carry, closing audit B4 so all three job-launch
  endpoints share one honest-error contract.
- `apps/backend/app/engine/data_manager.py`'s `_run_job` `finally` block (~line 4543,
  `prog.message = _final_summary(prog)`) — stop unconditionally overwriting a `failed` job's message;
  when `prog.status == "failed"`, preserve the message `_record_error` already captured in the outer
  `except Exception` handler (~line 4514) instead of overwriting it with `_final_summary`'s generic
  text. A normally-completed job (`ok`/`partial`/`resumable`) keeps getting `_final_summary`'s
  descriptive summary, byte-identical to today (reviewer MINOR, carried from iter-43's B5 finding that
  the `_run_detail` serializer fix at line ~4037 is currently a no-op on this exact path because the two
  expressions collide there).
- `apps/frontend/tsconfig.json` — currently clean against `git diff HEAD` (the iter-43 F1 stray
  `include`-array reordering is NOT present in the current working tree — likely already reverted when
  iter-43's changes were committed). No action needed unless this iteration's own test run (which
  exercises a real `next build` per `test_start_frontend_script.py`) reintroduces the reordering, in
  which case revert it before handoff and say so explicitly.
- Full regression replay (browser lane, not this plan's dev work): J-01, J-03, J-04, J-06, J-08, J-09 —
  each needs its own distinct, checksummed screenshot (closing iter-43/T3's byte-identical duplicate
  finding).
- J-05 retest against a historical trading day CONFIRMED absent from `/scanner-runs` before the run
  (not the already-snapshotted date iter-43 quietly reused) — through to a terminal or honestly-reported
  in-flight state.

## Agents Required
- backend-data: yes -- all code changes above are backend (launcher script, `data.py`, `data_manager.py`),
  plus the live diagnostic/fix and both re-measurement/retest passes.
- frontend-ux: no -- `tsconfig.json` is a one-line verify-or-revert check with no UI code change; no new
  page, component, or user-facing control ships this iteration (goal.md's own "New user-facing
  capability: None" / "New user actions: None" for iter-44).

Frontend Present: no

## Files to Create/Modify
- `incredible_auto_dev/scripts/start-backend.sh` -- add `--limit-concurrency` / `--timeout-keep-alive` /
  `--timeout-graceful-shutdown` to the uvicorn `exec` line, values read from `get_config().server`
  via the same inline venv-python read pattern used for `MEMORY_CAP_MB`/`MALLOC_ARENA_MAX_VALUE` just
  above it.
- `apps/backend/app/api/data.py` -- `retry_job` (~line 309): wrap `data_manager.retry_run(...)` in
  `try/except (RuntimeError, MemoryError)` → `HTTPException(503, ...)`, matching `start_job`/`resume_job`.
- `apps/backend/app/engine/data_manager.py` -- `_run_job`'s `finally` block (~line 4543): make the
  `prog.message = _final_summary(prog)` assignment conditional on `prog.status != "failed"` (or
  equivalent — preserve the `_record_error`-captured message on the failed path only); the file's blocking
  site identified by the live SIGUSR1 diagnostic (exact location unknown until the diagnostic runs —
  document wherever it lands).
- `apps/backend/tests/test_start_backend_script.py` (or the equivalent existing file covering
  `start-backend.sh`) -- new subprocess test asserting the launched uvicorn process's `/proc/<pid>/cmdline`
  carries the three new flags matching `get_config().server` (TC-1); a SIGTERM-under-stuck-task test
  proving self-termination within `graceful_timeout_seconds` without `kill -9` (TC-2) — confirm which
  existing file houses the current start-backend tests before creating a new one.
- `apps/backend/tests/test_api_data.py` -- mocked `POST /data/jobs/{run_id}/retry` test asserting 503 on
  `(RuntimeError, MemoryError)` (TC-9).
- `apps/backend/tests/test_data_manager.py` -- `_run_job` failure-path test asserting the persisted
  `message` contains the real captured exception text for a `failed` job, and an unchanged
  `_final_summary` string for a normally-completed job (TC-10); must not regress the audit's B5-verified
  no-op paths (`_create_run_record`/`_checkpoint_run_record` serializing a still-`running` job).
- `apps/frontend/tsconfig.json` -- verify clean (currently is); revert if this iteration's own test run
  reintroduces the F1 reordering.
- `reports/perf-budgets.md` -- new dated "Iteration 44" section: the SIGUSR1 dump excerpt, the named
  blocking call, TC-4's fix-or-disclosure outcome, TC-5/TC-6 latency+concurrent-read re-measurement, TC-7
  availability confirmation, TC-8 induced-pressure regression confirmation.
- `docs/handoffs/goal-ops-hardening-iter-44-dev.md` -- dev handoff (required by DoD).

## UI Evolution
N/A — Frontend Present: no. No new user-facing capability, information, action, surface, or navigation
change ships this iteration per goal.md's own "New user-facing capability: None" / "UI surface changes:
None" text for iter-44. CONDITIONAL: if (and only if) the live diagnostic's fix requires disclosing a
non-advancing background compute, the ONLY authorized shape is one new field,
`background_compute.active[].stalled: bool`, additive to the already-served `GET /api/health` payload —
no new component, no new page. If this ships, the badge/`/data` `BackgroundComputePanel` render it as an
additive detail on their EXISTING shape; do not build a new panel.

## Visual Requirements
N/A — Frontend Present: no; no browser-rendered UI changes ship this iteration outside the conditional
field above, which (if it ships) is a plain existing-component detail addition, not a new visual surface.

## Key Test Scenarios
- TC-1: `start-backend.sh`'s launched uvicorn process's own command line (verified via `/proc/<pid>/cmdline`
  or equivalent, not the script's source text) carries `--limit-concurrency`, `--timeout-keep-alive`, and
  `--timeout-graceful-shutdown` matching `get_config().server` (default 64 / 65 / 120).
- TC-2: a backend launched via `start-backend.sh` with a stuck in-flight background task self-terminates
  on SIGTERM within `graceful_timeout_seconds`, without a manual `kill -9`.
- TC-3/TC-4: the live SIGUSR1 all-thread dump names the exact blocked call/lock; the targeted fix (or an
  honest documented finding) is applied and a fresh single-trigger reproduction either advances/terminates
  with byte-identical output for any touched producer, or is disclosed as unresolved naming the blocking
  call.
- TC-5/TC-6/TC-7: one single-trigger full-horizon warm, `/api/health` polled at 1Hz throughout — every
  poll ≤2s and HTTP 200 (rescoped BCW budget), a concurrent cached `GET /api/backtest` read returns 200
  once, and the port never goes connection-refused (the iter-43 total-outage failure mode does not
  recur).
- TC-8 (regression): the existing sanctioned induced-pressure test hook (J-07 step 4) still aborts
  honestly via the per-item `MemoryError` isolation handler while `/api/health` and cached reads keep
  responding 200 — no deadlock/wedge/restart.
- TC-9: `POST /data/jobs/{run_id}/retry` returns 503 (not 500) on `(RuntimeError, MemoryError)` from
  `data_manager.retry_run`.
- TC-10: a job failing via `_run_job`'s outer exception handler persists the real captured exception text
  as its `message`; a normally-completed job's `_final_summary` text is unchanged.
- TC-11: `apps/frontend/tsconfig.json` matches its pre-iter-43 content (currently true) or the dev handoff
  states why a reordering is load-bearing.
- TC-12: J-05 retested on a day CONFIRMED absent from `/scanner-runs` beforehand; a backfill covering
  exactly that day reaches `ok` with `/scanner-runs` listing the date and a rendered leaderboard and
  `aggregates_refreshed` naming the refreshed aggregates, OR an honest in-flight state is captured if it
  does not terminate within the observation window.
- TC-13: the full required-still-passing set (J-01, J-03, J-04, J-06, J-08, J-09) all PASS with unique,
  dated, checksum-distinct evidence screenshots — no two journeys sharing one file.

## Notes for the developer
- This is the SEVENTH consecutive ESCALATE on this session; review/QA/the deterministic gate have all
  previously missed load-bearing defects the auditor caught — be skeptical of your own "PASS" claims and
  prefer an honest unresolved-finding over a speculative fix (binding iter-38/39/42 lessons).
- The one genuinely risky lever this iteration is the live stall diagnosis and whatever fix it points to;
  the launcher wiring, Retry 503 parity, and `_run_job` message fix are small and mechanical — do not let
  scope creep into `warmup.start_warmup`'s same-class gap (`forward_testing.py:1691`, deliberately
  deferred), `scripts/dev.sh`, or a sixth `_BarCache.prefill` bound attempt (all explicitly OUT OF SCOPE
  unless the live diagnostic directly implicates them).
- `main.py:63-67` already arms `faulthandler.register(signal.SIGUSR1, ...)` when
  `TRENDORA_DIAG_FAULTHANDLER_SIGUSR1=1` is set — confirmed present this session; no new plumbing needed
  to fire it, only to actually trigger and read it during a genuine reproduced stall.
  `get_background_compute_status()` (`forward_testing.py:1700`) is the existing, only accessor for
  `horizons_done`/`started_at` — reuse it for the bounded-window detection, do not add a second polling
  mechanism.
