# goal-ops-hardening-iter-69 Dev Handoff

**Phase:** goal-ops-hardening-iter-69
**Date:** 2026-08-12
**Agent:** developer
**Status:** complete

**`handler_compute_s` is now decomposed into `db_reads_s`/`readiness_s`/`preflight_s`, unit-tested for both
flag states (15/15 passing).** Live-job drill: **77 of 952 polls over the 2.0s ceiling (8.09%)**, including
3 non-answers at the poller's own 5.0s client timeout — a markedly higher breach rate than iter-67/68's
single-breach rounds, reported exactly as measured (see "Host-load context" in Addendum 35: this session's
own outer orchestration loop, `goal-iter-lean.sh`, was confirmed concurrently polling the same backend
during this drill — a measurement-condition difference from prior rounds, not smoothed away). Idle-control
drill: **0 of 330 polls over the ceiling.** Joining the two new sub-spans plus the pre-receive gap (already
recoverable from existing artifacts, no new instrument) against every one of the 74 answered breaches:
**median breach is now ~94.0% NAMED (residual 5.99%)** — up from iter-68's own ~80.4% combined figure, this
session's best-ever J-07 time-budget attribution. `readiness_s` dominates 43 of the 74 breaches,
`preflight_s` the other 31. Full numbers, both write-up corrections (iter-68/a, iter-68/c), and a new
finding about the watchdog's own pre-`db_reads_s` write cost under load are in `reports/perf-budgets.md`
Addendum 35.

## What Was Built

- **Three new sub-spans on the SAME `handler_compute` record** (`apps/backend/app/engine/health_watchdog.
  py`, `record_handler_compute`) — `db_reads_s`, `readiness_s`, `preflight_s` added as keyword-only params,
  written into the SAME record type, through the SAME `TRENDORA_HEALTH_WATCHDOG=1` flag and the SAME
  `app.engine.ledger.append_entry` writer. Omitted from the entry entirely when not supplied, so the
  pre-iter-69 direct-call shape (`record_handler_compute(t0, t1, ts)`, no keyword args) is unaffected.
- **`apps/backend/app/api/health.py`** — each of the three existing computation blocks (the DB reads,
  `compute_readiness`, `compute_preflight` including its own nested `record_verdict_transition` write) is
  now timed with the SAME monotonic clock `handler_compute_s` already uses, with each timing window placed
  OUTSIDE its own try/except so a full sample is captured whether the wrapped call succeeds or raises
  internally (already caught, degrades honestly — unchanged). No change to what is computed or returned —
  `GET /api/health`'s response body/shape stays byte-identical regardless of the flag (re-proven live: two
  full `scripts/dev.sh` cycles with the flag unset left `logs/health-watchdog.jsonl`'s line count
  unchanged, 49,479, across both).
- **6 new unit tests** in `apps/backend/tests/test_health_watchdog.py` (15 total, all passing, 115-116s,
  run twice for stability): flag-unset writes no `handler_compute` entry at all; flag-set writes a record
  whose three sub-fields are each `>= 0` and sum to `handler_compute_s` within a 5ms tolerance (widened
  slightly from the spec's own "e.g. 1ms" example — see "Known Issues"); the error case (`compute_
  readiness` raising internally) still yields a full, non-suppressed sub-span sample; the direct-call shape
  with no keyword args still works, omitting the three fields.
- **The live-job drill (TC-1/TC-2)** — a real single-date backfill (`2018-01-08`, live-verified
  unsnapshotted before dispatch: no `scanner_runs` row, a real SPY close of $243.843, distinct from every
  prior round's date) run with the watchdog armed via `scripts/start-backend.sh`, `scripts/qa/poll_health.
  py` polling at 1 Hz for 952 polls covering the job's full 17m18.9s wall time (`job_id=
  29c72f278f2445e88e7d976837824dbd`, `"source": null` in the final record — AG-9 clean), joined against
  `logs/health-watchdog.jsonl` by UTC timestamp.
- **The idle-control drill (TC-3)** — same already-warm backend (no restart), 330 polls (~5.5 minutes), no
  job running, launched immediately after the live-job drill's poller stopped.
- **A corrected join method** — discovered mid-analysis that this session's own outer orchestration loop
  (`goal-iter-lean.sh`) was concurrently polling the same backend during the drill, occasionally landing
  closer in raw time to a given poll than that poll's own true match. Fixed by constraining the join to
  the EARLIEST `handler_compute` entry with `t_received_wall >= send timestamp` (a request cannot be
  received before it is sent on the same host clock) rather than plain nearest-neighbor — eliminated the
  one physically-impossible negative pre-receive-gap match this produced; zero negative gaps across all
  1,282 joined rows after the fix.
- **`reports/perf-budgets.md` Addendum 35** (append-only; every earlier addendum untouched) — the
  instrument, both drills' method and side-by-side component distributions, the full TC-2 breach-by-breach
  attribution (dominance tally + representative rows + the 3 non-answer cases handled separately since
  server-side time can exceed the client's own capped `elapsed_s`), TC-5's pre-receive-gap distributions
  (closes iter-68/b), a new finding about the watchdog's own pre-`db_reads_s` write cost ballooning under
  load (idle: negligible, ~0.3ms; live: up to 497ms), and the two dated corrections:
  - **TC-6** (closes iter-68/a): iter-68's own browser-QA write-up said `/backtest` "rendered the full
    forward-test scorecard ... (all 5 score buckets, excess-vs-SPY/QQQ) ..." — re-examining
    `UT-J-07-result.png` shows the per-horizon "Forward-test scorecard" panel actually rendered its own
    honest "No elapsed forward window yet for this date" empty state (every horizon row `— n/a` / `— n=0`);
    the populated content described belongs to a SEPARATE "Forward-tested evidence (expanding window)"
    section. Same iter-66/e pattern, second occurrence this session.
  - **TC-7** (closes iter-68/c): `health_watchdog.py`'s two synchronous JSONL writes per request each cost
    real wall-clock time OUTSIDE the window they measure — `record_queue_wait`'s write sits between
    `t_handler_start` and `db_reads_s`'s own start (this iteration's own new finding: negligible idle, up
    to 497ms under live load); `record_handler_compute`'s write happens AFTER `handler_compute_s` is
    already frozen, adding directly to the client's own `elapsed_s` with no span ever capturing it.

## Files Changed

- `apps/backend/app/engine/health_watchdog.py` — `record_handler_compute` gains `db_reads_s`/`readiness_s`/
  `preflight_s` keyword-only params; module docstring extended (three sample types -> four items).
- `apps/backend/app/api/health.py` — each of the three existing computation blocks now timed with the SAME
  monotonic clock; the watchdog write near the end of `health()` passes the three new values; docstring
  extended.
- `apps/backend/tests/test_health_watchdog.py` — 6 new tests (see above); module docstring extended.
- `reports/perf-budgets.md` — new `## Addendum 35` (append-only; every earlier addendum untouched).
- `runs/goal-ops-hardening-iter-69/evidence-drill/` — every raw artifact behind the numbers above:
  `tc1-job-create.json`/`tc1-job-final.json`/`tc1-job-dispatch-time.txt`, `tc1-health-poll.csv`/`.meta.
  json`, `tc3-idle-poll.csv`/`.meta.json`, `health-watchdog-slice.jsonl` (this run's own watchdog-log
  slice), `poll_health_tc1.log`/`poll_health_tc3.log`, `reconcile_drill.py` (the join script, corrected
  matching rule), `tc1-full-join-fixed.json`/`tc3-full-join-fixed.json` (every poll, matched), `tc1-
  breaches-fixed.json` (all 77 breaches with their full component breakdown).
- `runs/goal-ops-hardening-iter-69/start-backend.out`, `dev-run1.log`, `dev-run2.log` — service-startup
  verification logs.
- `docs/handoffs/goal-ops-hardening-iter-69-dev.md` — this file.
- `runs/goal-ops-hardening-iter-69/status.json` — `current_step: dev_complete`.

**No change to `compute_factor_lab_all_warm`, `coverage_membership_timeline_refresh`, `scripts/automation/
browser-qa-phase.sh`, or any file under `apps/frontend/*`** — confirmed via `git status --porcelain` before
writing this handoff (only `apps/backend/app/api/health.py`, `apps/backend/app/engine/health_watchdog.py`,
`apps/backend/tests/test_health_watchdog.py`, and `reports/perf-budgets.md` are modified under version
control), matching this iteration's "diagnostic-only, no new user-facing capability" scope and "Frontend
Present: no". The direction to the browser-qa-agent to arm `TRENDORA_HEALTH_WATCHDOG=1` for its own J-07
lane (closing iter-68/d) is a spec-level instruction already present in the iteration spec's TESTING
REQUIREMENTS — no code or script change was needed or made for that item.

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/test_health_watchdog.py -v`
Result: **15 passed** in ~116s (9 iter-67/68 tests + 6 new iter-69 tests, all green). Run twice for
stability (timing-tolerance assertions); both runs fully green with no flakiness observed.

Note on scope: the full whole-repo test suite and `test_health.py` (the `loaded_engine`-fixture module,
~1h on this host, already run clean 17/17 in iter-68 and not re-touched this round) were NOT re-run this
iteration, per this session's own established convention (`.claude/core.md`'s "Pump: don't run the full
suite" discipline) and because this iteration's own diff touches none of `test_health.py`'s exercised
surface beyond what `test_health_watchdog.py` already re-verifies end-to-end via `TestClient`. Confidence
in the rest of the diff rests on: (a) the targeted file run above, fully green, twice; (b) `main.py` was
NOT touched this iteration (no new middleware, no new lifespan hook — only `health.py`/`health_watchdog.py`
changed); (c) the flag-unset byte-identity re-verified live twice via `scripts/dev.sh` below.

Service startup (pre-handoff checklist): ran `scripts/dev.sh` twice back-to-back on the default project
ports (8255/3255), flag UNSET (the default path) — both backend (`GET /api/health` -> 200) and frontend
(`GET /` -> 200) started cleanly each time, healthy within one 2s poll. `logs/health-watchdog.jsonl`'s line
count was IDENTICAL (49,479) before both launches and after several `/api/health` hits on each — confirms
the new sub-span code genuinely never activates on the default path. Both shutdowns (`kill -TERM` on the
`dev.sh` PID) were clean in `logs/backend.log`/the run's own stdout log ("Application shutdown complete",
no tracebacks/`CancelledError` noise); both times the frontend's `next-server` grandchild briefly held its
port after the parent `next dev` process exited (repeating the iter-66/67/68-documented `dev.sh` trap gap)
— killed directly (`kill -9` on the PID resolved from `ss -tlnp`) and confirmed both ports clear before
finishing. Separately, the WATCHDOG-armed backend (launched via `scripts/start-backend.sh` with
`TRENDORA_HEALTH_WATCHDOG=1` for the two live drills) also shut down cleanly on `kill -TERM` with no
tracebacks in `logs/backend.log`.

External integration: the live-job drill's `POST /api/data/jobs` backfill ran against the real committed
seed (`"source": null` in the persisted job record — AG-9 clean, no live network call), producing a real
snapshot + 2,145 forward returns and all 9 `aggregates_refreshed` categories including `factor_lab_all` and
`drawdown_expectations` — this IS the live-external-integration check for this iteration.

## Known Issues

- **Median breach is ~94.0% named, not 100%** — a genuine 5.99% median / 9.71% mean residual remains even
  after joining `pre_receive_gap_s` + `queue_wait_s` + `db_reads_s` + `readiness_s` + `preflight_s`. The
  most likely remaining sources, both newly named this round (see Addendum 35's "A new finding" and TC-7):
  `record_queue_wait`'s own JSONL-write cost sitting between `t_handler_start` and `db_reads_s`'s own start
  (negligible idle, up to 497ms under this round's live load), and `record_handler_compute`'s own JSONL
  write happening AFTER `handler_compute_s` is already frozen (adds to the client's `elapsed_s` with no
  span ever capturing it). Neither is separately instrumented this round (one risky change only, per spec
  rule 5) — named for a future round to weigh, not attempted here.
- **This round's breach rate (77/952, 8.09%) is far higher than iter-67/68's single-breach rounds** — this
  session's own outer orchestration loop (`goal-iter-lean.sh`) was confirmed concurrently polling the same
  backend during this drill (`logs/backend.log` shows interleaved `GET /api/data`/`/api/data/availability`/
  `/api/runs` calls from a second client throughout the window) — a material difference in measurement
  conditions from prior rounds' drills, named explicitly rather than folded into a round-over-round trend
  claim. Whether the elevated rate is attributable to that added concurrent load vs. genuine phase-level
  contention is not this round's own ask (OUT OF SCOPE: no bound attempted); a future round doing further
  breach-rate attribution work should control for or at least record whether the orchestration loop was
  concurrently active.
- **3 of the 77 breaches were non-answers** (the poller's own 5.0s client timeout, `http_status: 0`) — for
  these the server-side named-component sum can legitimately exceed the client's own capped `elapsed_s`
  (the server kept computing after the client gave up); reported separately in Addendum 35's TC-2 table
  rather than blended into the 74 answered breaches' residual statistics.
- **The 5ms unit-test sum-tolerance** (vs. the spec's own "e.g. 1ms" example) reflects the SAME
  `record_queue_wait`-write-cost gap named above — even under the unit test's own isolated, uncontended
  conditions this gap was never observed to exceed a fraction of a millisecond in either of two full test
  runs, so 5ms carries real margin without masking a genuine regression; chosen explicitly rather than
  silently widened to something looser.
- **The J-05 walkthrough capture remains unrecorded** (11th round now) — rides along only if a
  showcase/demo lane happens to run this iteration; not this iteration's own goal, per OUT OF SCOPE.
- **The three long-parked OWNER items** (2-second-ceiling policy, `browser-qa-phase.sh` ordering fix, the
  replay-lane cost sanction) remain untouched, per this iteration's own OUT OF SCOPE.
