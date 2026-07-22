# goal-ops-hardening-iter-9 Dev Handoff

**Phase:** goal-ops-hardening-iter-9
**Date:** 2026-07-22
**Agent:** developer
**Status:** complete — AG-10 launcher fix, T4 test hardening, TC-7/TC-8/TC-9 launcher-cap tests, and B2
libc-handle memoization are all implemented and passing. The live heavy-ingest re-measurement under the
new caps (VmPeak/VmSize CSV + `perf-budgets.md` dated section) was deliberately **deferred this session**
for a host-safety reason — see Known Issues #1, this is the one DoD item not closed.

## What Was Built

This is a pure verification-and-compliance closeout iteration per the plan — no new product feature, no
Data Contract change. Scope: the AG-10 launcher-cap gap, test hardening on the existing heavy-ingest
regression guard, and an optional libc-handle memoization (B2). The J-01/J-03/J-04 regression-replay
evidence gathering and J-05's browser verification named in the plan's "What to Build" section are
QA/browser-qa-agent responsibilities per this project's own pipeline (`.claude/workflow.md` stage 6,
`browser-qa-phase.sh`) and the phase's own generated test plan (`reports/qa/goal-ops-hardening-iter-9-test-plan.md`
TC-10/TC-11/TC-12 explicitly assign them to "browser-qa-agent") — not reproduced here; this developer
session's own dispatch instructions scope its deliverables to the dev handoff, implementation summary,
and status update.

- **AG-10 launcher-cap closure** — `scripts/start-backend.sh` (`incredible_auto_dev/scripts/start-backend.sh`,
  `scripts/` is a symlink into it) now sources `project-extensions/host-guard/host-guard.env` when present
  and `HOST_GUARD_ENABLED=1`, wraps the exec'd `uvicorn` with `taskset -c "$HOST_GUARD_CPU_LIST"`, and
  exports `OMP_NUM_THREADS`/`OPENBLAS_NUM_THREADS`/`MKL_NUM_THREADS`/`NUMEXPR_NUM_THREADS` =
  `HOST_GUARD_BLAS_THREADS` — additive alongside the script's pre-existing `ulimit -v`/`MALLOC_ARENA_MAX`
  enforcement (unchanged). Absent file or `HOST_GUARD_ENABLED=0`: zero behavior change (verified — see
  Tests Run). A `HOST_GUARD_ENV_FILE` env-var override (unset in every real launch, defaulting to the
  committed path) lets tests exercise the absent/disabled branches without ever touching the real,
  safety-critical file.
- **`scripts/dev.sh`'s backend subshell only** gets the identical HOST-GUARD block, plus it now mirrors
  `start-backend.sh`'s config-derived `ulimit -v` + `MALLOC_ARENA_MAX` derivation (same
  `app.config.get_config()` values, computed once inside that subshell — no second computation
  elsewhere). The frontend (`next dev`) subshell is untouched — confirmed by a live test that finds its
  actual listening process (via `lsof`/`ss`, since `next dev` and `uvicorn --reload` both fork a further
  worker process) and asserts it carries none of the backend-only caps. Verified live: `dev.sh`'s backend
  process showed `Cpus_allowed_list=0-3,8-11`, all 4 thread-cap vars, `MALLOC_ARENA_MAX=2`, and RLIMIT_AS
  6442450944 bytes; the frontend process showed `Max address space: unlimited`, no `MALLOC_ARENA_MAX`, and
  the SAME CPU affinity as the launching test process (proving `dev.sh` issued no `taskset` for it).
- **T4 — tightened `test_start_backend_survives_back_to_back_heavy_ingest_under_memory_cap`**
  (`apps/backend/tests/test_start_backend_script.py`): both the rebuild and the second backfill job must
  now reach status `"ok"` exactly (a `"partial"` result is rejected — it would mean a per-item warm loop
  silently early-aborted on `MemoryError` during that live run), and each job's persisted
  `aggregates_refreshed` list must contain all 7 categories the finalize hook can refresh
  (`latest_snapshot`, `coverage`, `membership_timeline`, `market_phase`, `forward_aggregates`,
  `research_hot_keys`, `drawdown_expectations` — matching iter-8's own live measurement, which observed
  all 7 for both job kinds). Every pre-existing VmPeak/VmSize/health-poll assertion is untouched — the
  edit only tightened the two `status` assertions and appended the two new `aggregates_refreshed`
  assertions between the existing `try/finally` block and the VmPeak checks; both boundaries were
  re-read before and after per the iter-8 lesson on the same test file (a prior edit there silently
  deleted a different test's real assertions).
- **New launcher-cap verification tests (TC-7/TC-8/TC-9)**, all in `test_start_backend_script.py`:
  - TC-7 (`test_start_backend_applies_host_guard_caps_when_enabled`): reuses the existing `spawned_backend`
    fixture (real `start-backend.sh`, real committed `host-guard.env`) and asserts the launched process's
    `Cpus_allowed_list` matches `HOST_GUARD_CPU_LIST` and all 4 thread vars match `HOST_GUARD_BLAS_THREADS`.
  - TC-8 (`test_dev_script_applies_host_guard_caps_to_backend_only`): spawns a real `scripts/dev.sh` (its
    own process group, so teardown can reliably kill the whole tree — a plain PID kill left stray
    processes in manual testing, see Known Issues #2), asserts the backend's caps (CPU affinity, thread
    vars, `MALLOC_ARENA_MAX`, RLIMIT_AS) and that the frontend has none of them.
  - TC-9 (three tests: absent/disabled for `start-backend.sh`, disabled for `dev.sh`): both scripts start
    cleanly with zero caps applied when `host-guard.env` is absent or `HOST_GUARD_ENABLED=0` — verified
    against the real committed file (via `HOST_GUARD_ENV_FILE` override, never mutating it) for the
    "disabled" case, and a nonexistent path for the "absent" case. `dev.sh`'s absent sub-case is not
    separately tested (only disabled) — both branches share the identical no-op code path in the SAME
    HOST-GUARD block, and a full `dev.sh` launch (real frontend + backend) is materially more expensive
    than `start-backend.sh` alone, so the shared path is proven once rather than paying that cost twice
    for a byte-identical outcome (documented in the test's own docstring).
  - All "no caps applied" assertions compare against **this test process's own live affinity/environment**
    (never a hardcoded assumption about the host's full CPU set or an empty ambient BLAS-var environment)
    — this sandbox's own outer wrapper already pins the session to `0-3,8-11` and pre-sets the BLAS thread
    vars, so a naive "must equal the wide/default set" or "must be absent" assertion would have been
    false-positive-prone; the relative comparison is the only correct invariant. `_read_proc_limits_max_address_space_raw`
    was added because the existing byte-parsing helper raises on the frontend's literal "unlimited" value.
- **B2 — memoized libc handle in `_release_process_memory()`** (`apps/backend/app/engine/data_manager.py`):
  extracted a new `_resolve_libc_malloc_trim()` helper with a module-level cache dict; `ctypes.util.find_library`
  / `ctypes.CDLL` now resolve at most once per process (a permanent resolution failure is cached too, never
  retried). `gc.collect()` and `malloc_trim(0)` still run on every call with unchanged timing/effect — proven
  by two new tests in `test_data_manager.py` (memoization across 5 calls; a first-call failure cached across
  3 calls, `gc.collect()` still firing every time in both cases).

## Files Changed

- `scripts/start-backend.sh` (`incredible_auto_dev/scripts/start-backend.sh`) — HOST-GUARD block: source
  `host-guard.env` when present+enabled, `taskset -c` wrap + BLAS/OMP/numexpr thread-cap exports.
- `scripts/dev.sh` (`incredible_auto_dev/scripts/dev.sh`) — identical HOST-GUARD block in the backend
  subshell only, plus mirrored `ulimit -v` / `MALLOC_ARENA_MAX` derivation there; frontend subshell
  untouched.
- `apps/backend/app/engine/data_manager.py` — B2: `_resolve_libc_malloc_trim()` memoization helper;
  `_release_process_memory()` now calls it instead of re-resolving `ctypes.util.find_library`/`ctypes.CDLL`
  inline every call.
- `apps/backend/tests/test_data_manager.py` — 2 new tests: memoization across repeated calls, and a
  cached-failure case.
- `apps/backend/tests/test_start_backend_script.py` — tightened the heavy-ingest test's status +
  `aggregates_refreshed` assertions (T4); added 7 new tests + supporting helpers for TC-7/TC-8/TC-9.

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/test_data_manager.py -q`
Result: **133 passed, 0 failed** (273.06s) — includes the 2 new B2 tests; zero regressions in the
pre-existing 131.

Command: `cd apps/backend && .venv/bin/python -m pytest tests/test_start_backend_script.py -v -k "not heavy_ingest"`
Result: **8 passed, 1 deselected** (56.00s) — the 3 pre-existing TC-15/16/17 tests plus all 5 new
TC-7/TC-8/TC-9 tests, run together in one process (no state leakage between them); deselected the one
opt-in heavy-ingest test (see Known Issues #1).

`test_start_backend_survives_back_to_back_heavy_ingest_under_memory_cap`
(`TRENDORA_RUN_HEAVY_INGEST_TEST=1`) was **not executed this session** — see Known Issues #1. Its T4
tightening (status `"ok"` only, `aggregates_refreshed` completeness) is implemented and syntax/logic
reviewed, but has no fresh live pass/fail evidence from this session.

## Pre-handoff verification

- **Service startup**: `scripts/dev.sh` was started, confirmed both backend and frontend healthy
  (`GET /api/health` 200, frontend answering), stopped, and started AGAIN on the identical ports — no
  port conflict, clean re-bind both times (manual round-trip, plus the automated TC-8/TC-9 tests each
  independently launch and tear down `dev.sh` cleanly). One thing worth flagging: killing `dev.sh`'s
  launching PID alone (or a naively-computed process-group id from an external `setsid` wrapper) does
  **not** reliably reap the `next dev` → `next-server` child in every invocation shape — see Known Issues
  #2. The automated tests avoid this by spawning `bash scripts/dev.sh` directly with `preexec_fn=os.setsid`
  (Python-level, not the external `setsid` utility) and killing that process group, which was verified
  to leave zero stray processes afterward.
- **Native/external dependencies**: N/A — no new dependency added this iteration.
- **Live launcher verification**: both scripts were manually smoke-tested against the REAL, committed
  `host-guard.env` (not just via pytest) before writing any test — confirmed `Cpus_allowed_list=0-3,8-11`,
  all 4 thread-cap vars = 4, `MALLOC_ARENA_MAX=2`, RLIMIT_AS = 6442450944 bytes on the launched backend
  process for both scripts, and that `dev.sh`'s frontend process carried none of the backend-only caps.

## Known Issues

**1. Live heavy-ingest re-measurement under the new launcher caps — DEFERRED this session, host-safety
reason (not a shortcut).** The DoD calls for running
`TRENDORA_RUN_HEAVY_INGEST_TEST=1 pytest tests/test_start_backend_script.py::test_start_backend_survives_back_to_back_heavy_ingest_under_memory_cap -v`
on an idle host, retaining a VmPeak/VmSize sampler CSV under `runs/goal-ops-hardening-iter-9/`, and adding
a dated section to `reports/perf-budgets.md`. At the time of this session's work, `logs/hwmon/hwmon.csv`
showed `Tctl` steady at 74–86°C (vs. the documented 43–50°C idle baseline) and `ps` showed an **unrelated
process from a different project on this same physical host** (`/home/dennis-chan/Git/tapeology/apps/backend/...uvicorn`,
PID 818822, 97–98% of one core, running 30+ minutes throughout this session, not started or controllable
by this developer session) keeping the machine warm. This host hard-reset twice (2026-07-20/21) under
exactly this class of workload (full-universe rebuild + heavy backfill), and iter-8's own live measurement
of the SAME test reached a peak Tctl of 89°C from a true idle baseline — running the identical heavy job
on top of an ALREADY-elevated baseline risks approaching the 95°C abort threshold from a much smaller
margin, for a workload this project's own `goal.md` AG-10 explicitly calls "a physical constraint of the
current host... not a performance budget to optimize away." A background thermal watchdog was observed
running and armed, but it is a reactive 10-second-sustained-95°C safeguard, not a substitute for not adding
load to an already-warm, uncapped, unrelated concurrent burn — the original incidents were themselves
**instant** resets with no preceding software warning. Given this, the responsible choice was to defer the
run rather than gamble a third hard reset for one measurement. **Everything else this test proves —
correctness of the tightened assertions, the launcher caps actually applying to a real process — is
independently verified** via the non-heavy test suite above and the manual launcher smoke tests. Recommended
next step: re-run the exact command above once `logs/hwmon/hwmon.csv` shows a return to the ~43–50°C idle
baseline (i.e., once the unrelated process has finished), then append the dated section to
`reports/perf-budgets.md` and retain the sampler CSV under `runs/goal-ops-hardening-iter-9/` per the DoD.
This is the ONE DoD checklist item not closed by this handoff.

**2. `dev.sh`'s child processes are not always reachable via a naively-computed process-group kill.**
While manually verifying "stop, then start again" (see Pre-handoff verification), killing the PID/pgid
captured from an external `setsid ... bash scripts/dev.sh &` invocation left the `uvicorn --reload` worker
and `next-server` child processes still holding their ports — they had to be killed directly by PID
(found via `lsof`/`ss`). The automated TC-8/TC-9 tests sidestep this by using Python's
`subprocess.Popen(..., preexec_fn=os.setsid)` directly (which reliably keeps the whole tree in one process
group, verified clean afterward), so this is not a regression in `dev.sh` itself, but an operator running
`dev.sh` manually via a plain background job and a bare `kill` should be aware that `next dev`'s child may
need a direct-PID or `fuser -k <port>/tcp` cleanup, not just a signal to the shell's own PID. This is
pre-existing `dev.sh`/uvicorn-reload/next-dev process-tree behavior, unrelated to and unchanged by this
iteration's diff — flagged for awareness, not fixed here (out of this iteration's scope, and `scripts/dev.sh`'s
port-cleanup preamble at the top of the script already handles this on the NEXT launch regardless).

**3. Carried forward — deferred `/api/backtest` on-load `MemoryError` (J-06/AG-8).** Still unresolved,
per the plan's explicit carry-forward instruction. Not touched by this diff (out of scope — settled in
"Do not touch").

**4. Carried forward — unproduced `demo.sh ops-hardening --session-live` walkthroughs for J-05/J-06.**
Still not produced; per the plan and goal.md NOTES this needs an explicit human deferral or new iteration
budget before any `GOAL_ACHIEVED` gate, not manufactured here.

**5. J-01/J-03/J-04 regression-replay evidence and J-05 browser verification are not in this handoff.**
As explained in "What Was Built" above, these are QA/browser-qa-agent pipeline responsibilities (confirmed
by this phase's own generated `reports/qa/goal-ops-hardening-iter-9-test-plan.md`, whose TC-10/TC-11/TC-12
explicitly assign them to "browser-qa-agent," and by `.claude/workflow.md`'s stage ordering, where Browser
QA (stage 6) runs after Dev+Review (stage 3) as a separate pipeline stage) and this developer session had
neither a live-browser tool nor Playwright available in the backend venv to run them. Not fabricated here.

---

## Fix Notes (audit FAIL round — 2026-07-22)

Audit report: `docs/handoffs/goal-ops-hardening-iter-9-audit.md` (verdict FAIL). Only the one finding the
audit left OPEN for the developer was addressed — **T3**. Nothing else in the diff was touched.

### T3 (fixed) — the tightened heavy-ingest assertion was unsatisfiable: its backfill target date was already snapshotted, so the second job could only ever be a zero-work no-op

**Confirmed the audit's claim before changing anything** (read-only query against the real dev DB, the same
DB the throwaway fixture copies):

```
sqlite3 file:apps/backend/data/trendora.db?mode=ro
  select count(*) from scanner_runs where asof_date='2010-07-15';   -> 1     (already snapshotted)
  select count(distinct date) from daily_prices where symbol='SPY'; -> 5380  (trading calendar)
  select count(distinct asof_date) from scanner_runs;               -> 1113
```

So `_backfill_snapshots` would have dropped the only requested date from `targets`, returned early
(`data_manager.py:2863-2866`), left `prog.new_snapshot_dates` empty, and therefore skipped exactly the two
snapshot-gated aggregate categories (`latest_snapshot`, `market_phase`) — producing a test failure that
looks like a `MemoryError` early-abort but is really "the scenario went stale". Exactly as the audit traced.

**Changes (all in `apps/backend/tests/test_start_backend_script.py` — no product code touched):**

1. `_pick_unsnapshotted_trading_day(port, cfg)` (new helper) — selects the second job's date **at run time**
   from the spawned instance's own `GET /api/data/availability`, i.e. the same benchmark trading calendar
   (`_trading_days`) + `ScannerRun.asof_date` set the ingest orchestrator's own target selection reads (no
   second derivation, no date literal). Candidates must be unsnapshotted, must have bars, and must retain at
   least `max(cfg.walk_forward.horizons)` trading days of following calendar so the finalize hook's
   forward-return/forward-aggregate work is real rather than truncated; the latest such day wins (maximum
   history for the scan). If no candidate exists the test **skips with an explicit reason** rather than
   measuring a no-op.
2. The date is chosen **after** the rebuild job reaches terminal status, so it reflects the DB state the
   backfill will actually face.
3. New scenario-integrity assertion: `job2["snapshots_created"] >= 1` — a zero-work second job now fails
   loudly and specifically ("this run proves nothing about warm-loop survival") instead of resurfacing later
   as a confusing missing-category error.
4. `_expected_aggregate_categories(job)` (new helper) + `_SNAPSHOT_DEPENDENT_CATEGORIES` — the
   completeness bar is now all 7 categories when a job persisted >= 1 new snapshot and the 5
   snapshot-independent ones otherwise. `job2` is asserted to have done real work, so it is always held to
   the full 7. This encodes the actual invariant in `_refresh_ingest_aggregates` (`latest_snapshot` gated on
   `if prog.new_snapshot_dates:`, `market_phase` iterating it) instead of a scenario assumption. The
   rebuild job's own date selection is cadence-driven and not controlled by this test, so the conditional
   also protects it from the same staleness trap.

Every pre-existing assertion in the test is intact — re-read both boundaries of the function after editing
(iter-8 splice lesson): `status == "ok"` for both jobs, `aggregates_refreshed` completeness for both,
`VmPeak`/`VmSize` under `server.memory_cap_mb`, `mem.samples` non-empty, every health poll HTTP 200,
`health.results` non-empty.

**Verification of the new selection logic without running the heavy workload** (the heavy run stays
deferred — see below): the real DB's availability payload was reconstructed read-only and served to the
new helper over a loopback stub, so the function itself ran end-to-end:

- 5380 trading days, 4267 of them unsnapshotted → picked `2025-05-30` (`snapshot_exists: false`,
  `symbols_with_bars: 589`, 283 trading days of following calendar — comfortably past the 60-day max horizon).
- Old hardcoded `2010-07-15`: `snapshot_exists: true` (i.e. it would indeed have been zero-work).
- All-snapshotted input → `Skipped: no unsnapshotted trading day with bars and >= 60 trading days of
  following calendar remains…` (the honest skip path, not a silent pass).
- `_expected_aggregate_categories({'snapshots_created': 0})` → the 5 snapshot-independent categories;
  `{'snapshots_created': 3}` → all 7.

### Audit findings deliberately NOT actioned here (and why)

- **T1** (`merge_ui_test_results.py` drops emphasised `**FAIL**` verdict cells) — `scripts/automation/*` is
  explicitly OUT OF SCOPE for this phase; the audit already corrected the merged artifact's headline.
  **Still needs reporting to the framework maintainer** (one-line fix: strip `*`/`_` before verdict
  matching, plus a regression case for a bolded `**FAIL**` cell).
- **T2** — artifact honesty; already fixed by the audit itself (AUDITOR ADDENDUM in the regression-replay
  results). J-04 stands as **failing at step 6**.
- **T4** — the live heavy-ingest measurement is **still deferred** (Known Issues #1 above, unchanged). The
  pump operator's standing instruction for this run repeats it: do not launch heavy full-universe backfills
  or the opt-in `TRENDORA_RUN_HEAVY_INGEST_TEST` run on this host on my own initiative (goal.md AG-10, two
  hard resets last week). The T3 fix is precisely what the audit asked to land *before* that deferred run,
  so the run does not report a false J-05 failure when it finally happens.
- **F1** (an interrupted job's progress is never checkpointed, so it can only render as zero) — a
  newly-discovered, pre-existing defect in `_finalize_run_record()` / `sweep_orphaned_runs()`; out of this
  iteration's scope, recorded as backlog work for the data-jobs cluster.
- **B1/B2** (no `command -v taskset` guard; `dev.sh` inherits `start-backend.sh`'s unguarded config-read
  failure mode) — audit-classified observations, explicitly out of the iteration's declared scope.

### Tests run (fix round)

Command (from `apps/backend/`, `TMPDIR` isolated per the run's environment note):

- `.venv/bin/python -m pytest tests/test_start_backend_script.py -k "host_guard" -v` → **5 passed, 4
  deselected (51.42s)**
- `.venv/bin/python -m pytest tests/test_start_backend_script.py -k heavy_ingest -v` → **1 skipped** (opt-in
  guard intact — the heavy workload did not run)
- `.venv/bin/python -m pytest tests/test_start_backend_script.py --collect-only -q` → **9 tests collected**
  (module imports cleanly after the edit)
- `.venv/bin/python -m pytest tests/test_data_manager.py -k release_process_memory -q` → **2 passed**

The full suite was NOT run (standing constraint: ~10-11h on the 30y basis, and no concurrent suite during
live measurement). No server process was left running by this session; `pgrep` for trendora
`uvicorn`/`next dev` after the runs returned nothing.

### Operator note

The pump's dispatch note said the backend was live on `:8255` and the frontend on `:3255`. **Neither was
listening during this fix round** (`ss -tlnp` empty for both ports; the only live services on the box belong
to an unrelated project on `:8301`/`:3301`). Nothing in this round required them — the launcher-cap tests
spawn their own short-lived backends on dedicated ports — but any follow-up browser/QA lane will need the
services restarted by the operator (this session does not start or kill them).

---

## Fix Notes — audit FAIL round 2 (2026-07-22, operator-authorized heavy run)

Audit report: `docs/handoffs/goal-ops-hardening-iter-9-audit.md` (verdict FAIL). Round 1 closed T3. This
round closes the two items the audit routed to an operator decision, per the pump operator's dispatch
note for this round:

| Audit finding | Decision this round | Outcome |
|---|---|---|
| **T4** — live heavy-ingest measurement + sampler CSV + `perf-budgets.md` row never produced (DoD items 1, 4-by-execution, 5, AG-8) | **RUN IT** — the repo owner authorized the run through the pump operator, with the documented preconditions verified before launch | **DONE — the test PASSED.** Evidence below |
| **F1** — an interrupted job's progress is never checkpointed, so J-04 step 6 renders "0 snapshots · 0 trading days in range" | **FIX IT** — small, well-tested, low-risk; it is the last unmet journey of the session contract | **DONE — `_checkpoint_run_record` landed with 2 new tests** |
| **T1** — `merge_ui_test_results.py` drops `**FAIL**` cells | **OUT OF SCOPE** (framework file) — unchanged from round 1 | Still flagged for the framework maintainer |
| B1, B2, T5 | Below the fix bar / out of the declared scope, per the audit's own classification | Not touched |

### T4 (CLOSED by execution) — the live heavy-ingest measurement was performed and PASSED

**Authorization + safety preconditions, verified by me immediately before launch** (this is the reason the
two previous rounds deferred; it is now a documented, satisfied condition rather than an assumption):
host at **Tctl 41 °C / load1 0.51** (the documented 43-50 °C idle band; it was 74-86 °C when round 1
deferred and 68 °C at audit time), the 1 Hz host-guard hwmon sampler live, and an auto-kill thermal
watchdog armed on the README abort criteria. The watchdog never fired; peak Tctl during the whole run was
**81 °C**, i.e. 14 °C below the 95 °C abort threshold and 8 °C below iter-8's own peak for the same
workload.

**Command run (exactly the DoD's, plus the new CSV-retention env var):**

```
TRENDORA_RUN_HEAVY_INGEST_TEST=1 \
TRENDORA_HEAVY_INGEST_SAMPLER_CSV=runs/goal-ops-hardening-iter-9/heavy-ingest-vm-samples.csv \
apps/backend/.venv/bin/python -m pytest \
  tests/test_start_backend_script.py::test_start_backend_survives_back_to_back_heavy_ingest_under_memory_cap -v -s
```

**Result: `1 passed in 1092.93s (0:18:12)`** — with the round-1 T3 fix and the T4-tightened assertions
active, so the pass means: both jobs reached `status == "ok"` (a `"partial"` is now rejected), each job's
`aggregates_refreshed` was complete for its outcome, the second job genuinely created a snapshot, peak
VmPeak/VmSize stayed under the `ulimit -v` ceiling, and every health poll returned 200.

Measured 2026-07-22T15:18:35Z-15:36:43Z, both jobs in ONE spawned process launched by the real
`scripts/start-backend.sh` (so the host-guard caps came from **this iteration's own launcher block**, not
inherited from the launching session — the whole reason a re-measurement was required):

| | Value |
|---|---|
| Job 1 — full-universe `rebuild` | `ok`, 378 snapshots, 709,093 forward returns, 0 date failures, **all 7** aggregate categories, 979.3 s |
| Job 2 — `backfill` of `2026-04-21` (picked at run time by the T3 helper) | `ok`, 1 snapshot, 2,773 forward returns, **all 7** categories, 103.2 s |
| Peak VmPeak (4,347 samples @ 0.25 s) | 4,738,948 KB (4,627.9 MB) vs the 6,291,456 KB cap → **24.7% margin** |
| Peak VmRSS / VmHWM | 3,946,472 / 3,948,188 KB |
| `GET /api/health` | **439 polls, 0 non-200, 0 timeouts**; median 0.398 s, max 3.646 s |
| Host (hwmon 1 Hz, 1,049 rows over the window) | max Tctl 81 °C · DIMM 44/43 °C · NVMe 41 °C · PPT 44 W |
| Applied caps (from `host-guard.env`, evidenced in `logs/backend.log`) | `cpu_list=0-3,8-11`, `blas_threads=4`, `ulimit -v` 6,291,456 KB, `MALLOC_ARENA_MAX=2` |

**Retained artifacts (DoD item 5):** `runs/goal-ops-hardening-iter-9/heavy-ingest-vm-samples.csv` (4,347
rows), `…-health.csv` (439 rows), `…/heavy-ingest-hwmon.csv` (the sampler sliced to the run window),
`…/heavy-ingest-pytest.log`. **Dated budget section added:** `reports/perf-budgets.md` → "iter-9 update —
heavy-ingest re-measurement under the LAUNCHER-APPLIED host-guard caps".

**The one number that deserves attention, stated plainly:** the VmPeak margin is **24.7%**, down from
iter-8's 43.6%. This run cannot attribute that narrowing (it sampled 4× more often AND ran against a 24%
larger DB copy), so `perf-budgets.md` records it as an unattributed narrowing to watch as the DB grows —
not as a comfortable pass.

> **AUDIT CORRECTION (iter-9 audit round 3, finding P1):** the "sampled 4× more often" half of that
> attribution is **wrong** and has been corrected in `reports/perf-budgets.md`. `VmPeak` is a kernel
> high-water mark and is monotone non-decreasing over the process's life — verified on this run's own
> retained 4,347-row trace, which is monotone across every consecutive pair and yields the identical
> 4,738,948 KB peak when re-subsampled at iter-8's 1 Hz cadence (and at 0.1 Hz). Cadence contributes
> zero KB. The +1,190,124 KB is a real increase in peak address-space demand, not a measurement artifact. Nothing in this run failed, but "4.6 GB against a 6.0 GB ceiling" is a
materially thinner margin than the previous section implies.

**To retain the CSV, one test-file change was needed** (`test_start_backend_script.py`): `_MemSampler`
now stamps each sample with its epoch, and a new `_write_run_evidence()` writes the samples + health
timings to the path in `TRENDORA_HEAVY_INGEST_SAMPLER_CSV` **from the test's `finally` block**, so a
FAILING heavy run would also leave its evidence behind (that is exactly when the samples matter). Unset
env var → no files written, behavior unchanged. No assertion was altered.

### F1 (FIXED) — an interrupted job now keeps its last persisted progress

**The defect, re-confirmed in this iteration's own artifacts before fixing:** the numeric detail fields
were written into the persisted `DataProviderRun.message` exactly once, by `_finalize_run_record()`, which
a `kill -9` never reaches; `sweep_orphaned_runs()` flips only `status`/`finished_at`. I found the live
proof sitting in the throwaway DB copy this round's heavy run used — run record **id 113**, the row
browser-qa's kill/restart created: `status: interrupted`, `snapshots_created: 0`, `dates_total: 0`, for a
job whose requested range was `2025-06-01 → 2026-07-17`. That is the exact "0 snapshots · 0 trading days
in range" the browser lane reported for J-04 step 6 / UT-10.

**Fix (`apps/backend/app/engine/data_manager.py`, ~45 lines):** a new `_checkpoint_run_record(engine, prog)`
writes the CURRENT `_run_detail(prog)` onto the job's OPEN run-history row, called from
`_persist_isolated()` after every date (success or failure), throttled to one write per
`_RUN_RECORD_CHECKPOINT_INTERVAL_S` (10 s). Deliberate properties:

- **Writes only `message`** — never `status`/`finished_at`, so the row stays OPEN and the boot sweep still
  claims it; and never INSERTs, so a job with no open row is a silent no-op.
- **No second derivation** — it serializes the same `_run_detail(prog)` the create and finalize paths
  already use, and syncs `error_other` from the same uncapped `date_failures_total` `_do_backfill` uses at
  the end, so a checkpointed row is internally consistent.
- **Never fatal** — a write failure is logged and swallowed; the job's outcome must not depend on its
  progress bookkeeping.
- **Bounded cost** — one small UPDATE per 10 s regardless of date throughput.
- **No frontend change needed**: `/data` already renders `run.snapshots_created ?? "—"` /
  `run.dates_total ?? "—"` (`apps/frontend/app/data/page.tsx:2612`) straight from this persisted detail.

**Tests (TDD — written first, observed failing, then implemented):** two new tests in
`tests/test_data_manager_jobs_pipeline.py` (the J-60 lifecycle cluster's home):
`test_interrupted_job_keeps_its_last_checkpointed_progress` runs a REAL 3-date backfill with
`_finalize_run_record` monkeypatched away (the only honest in-process simulation of `kill -9`), sweeps,
and asserts the `interrupted` row's detail carries `dates_total == 3`, `dates_done == 3`,
`snapshots_created == 3`, the real `calendar_days`, and `aggregates_refreshed is None` (the finalize hook
never ran — still never fabricated); `test_run_record_checkpoint_is_throttled_open_ended_and_never_fatal`
pins the throttle (an advance inside the window is NOT written), the row staying `running`/`finished_at
is None`, the no-open-row no-op (no second record), and that a broken engine does not raise.

> **AUDIT ADDITION (iter-9 audit round 3, finding F2):** the checkpoint was called ONLY from
> `_persist_isolated`, i.e. only once a date had been persisted — so a kill during the shared bar-cache
> prefill (minutes long on the deep basis, and it precedes the first date) still left the exact
> "0 snapshots · 0 trading days in range" row. The audit added ONE more call, immediately after the target
> plan is computed and before the prefill (`data_manager.py`, after the `if not targets: … return`
> guard), so the honest range/plan is durable from the start. Covered by a new test
> (`test_interrupted_before_first_date_still_keeps_the_computed_range`), observed RED (`dates_total 0 != 3`)
> before the call was added.

**What this does NOT close by itself:** J-04 step 6 is a browser journey. This fix makes the persisted
progress real; only the browser-qa lane re-running the kill/restart cycle can score the journey. It should
be re-run.

### Tests run (this round)

All from `apps/backend/` with the run's isolated `TMPDIR`, one workload at a time, never the full suite:

| Command | Result |
|---|---|
| `TRENDORA_RUN_HEAVY_INGEST_TEST=1 … ::test_start_backend_survives_back_to_back_heavy_ingest_under_memory_cap -v -s` | **1 passed** (1092.93 s) |
| `pytest tests/test_data_manager_jobs_pipeline.py -k checkpoint -q` (before implementing) | **2 failed** (RED — `_checkpoint_run_record` absent) |
| `pytest tests/test_data_manager_jobs_pipeline.py -q` | **20 passed** (548.66 s) — incl. the 2 new |
| `pytest tests/test_data_manager.py -q` | **133 passed** (250.61 s) |
| `pytest tests/test_data_manager_backfill_parallel.py -q` | **10 passed** (276.02 s) |
| `pytest tests/test_start_backend_script.py -q -k "not heavy_ingest"` | **8 passed, 1 deselected** (55.50 s) |
| `pytest tests/test_api_data.py` | **48 passed** (run alongside `test_db.py`, which surfaced the pre-existing failure below) |

### Known Issues (this round)

**6. NEW, pre-existing, NOT fixed (out of fix-mode scope): `tests/test_db.py::test_create_all_produces_expected_tables` fails on the current tree.**
It asserts an exact table-name set and is missing `coverage_snapshot` and `forward_aggregate_cache`,
tables added by **iter-2** (`git log -S coverage_snapshot -- apps/backend/app/models.py` → commit
`1e5a311e`, 2026-07-20). Neither `app/models.py` nor `tests/test_db.py` is touched by any uncommitted work
in this tree, so this stale assertion has been failing since iter-2 and is entirely unrelated to this
iteration's diff. Discovered while running regression sets; recorded here for triage rather than silently
fixed (fix-mode rule: no unlisted changes). One-line fix when someone scopes it: add the two table names
to the expected set.

**7. `tests/test_api_data.py` + `tests/test_db.py` are very slow** (>45 min for ~56 tests on the 30y
basis) — consistent with the standing "the suite is test-slow, not product-slow" note. I stopped that run
after identifying the failing test and re-ran the single case instead.

**Known Issues #1 from the main handoff is now CLOSED** (the heavy-ingest run happened — see T4 above).
#2, #3 (deferred `/api/backtest` `MemoryError`), #4 (unproduced `demo.sh --session-live` walkthroughs) and
#5 stand unchanged.

### Operator notes

- The long-lived services survived this round: `:8255` `GET /api/health` → **200**, `:3255` → **200** at
  the end of the session. I neither started nor stopped them.
- No stray processes: the heavy run's own spawned backend (`:18755`) exited with the test; the 5 GB
  throwaway DB copy it created under `TMPDIR` was deleted afterwards.
- The heavy run's measurement predates the F1 checkpoint landing in the tree — disclosed explicitly in the
  `perf-budgets.md` section rather than glossed over.
