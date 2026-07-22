# goal-ops-hardening-iter-9 Audit Report

**Date:** 2026-07-22
**Auditor:** Hard audit pass — skeptical, evidence-based (round 3, after the operator-authorized heavy run + the F1 fix)

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

The two findings that made rounds 1–2 FAIL are genuinely closed: the heavy-ingest measurement was
actually run under the launcher-applied caps (I re-derived every headline number from the retained CSVs
and the pytest log — all match to the digit), and the F1 interrupted-progress defect behind J-04 step 6 is
fixed with TDD tests. AG-10 is closed in code AND live: the backend serving `:8255` right now
(pid 1803579) carries `Cpus_allowed_list 0-3,8-11`, `OMP_NUM_THREADS=4`, `MALLOC_ARENA_MAX=2` and
`RLIMIT_AS 6442450944`, applied by `start-backend.sh`'s own new block (`logs/backend.log:25754-25756`).
Two things stop this being a PASS: **J-04 step 6 has no post-fix browser evidence, so J-04 must stay
`unknown` — not `passing`** (DoD item 2 unmet), and the audit found the F1 fix left a real hole (it only
began checkpointing after the first date persisted, so a kill during the multi-minute bar-cache prefill
still produced the exact "0 snapshots · 0 trading days in range" row) — fixed here, RED observed first.

---

## 2. Findings

### Backend Findings

**B1 — IMPORTANT (fixed): the F1 checkpoint never covered the pre-loop window, so the very kill the
journey performs could still yield an all-zero interrupted row**
`apps/backend/app/engine/data_manager.py:2955` was the only call site of `_checkpoint_run_record` — inside
`_persist_isolated`, i.e. it first writes only **after a date has been persisted**. The plan
(`calendar_days`/`dates_total`/`non_trading_days`/`already_snapshotted`) is computed at `:2837-2855`, but
between that point and the first date lies `prefilled_bar_cache` (`:2975`), the ~1.5 GB whole-universe bar
load that runs for minutes on the deep basis (the measured rebuild spent 979.3 s wall against 304.7 s in
the backfill stage — most of the job is *outside* the per-date loop). A `kill -9` in that window left the
run-history row at its creation-time defaults, i.e. literally the `0 snapshots · 0 trading days in range`
string UT-10 reported. The dev's own test only covers a kill *after* dates have been persisted, so it
could not see this.
**Fix applied:** one additional `_checkpoint_run_record(eng, prog)` call immediately after the target plan
is computed and the `if not targets: … return` guard, before the prefill (`data_manager.py:2880`). Same
throttled writer, same open row, no second derivation, no new state.
**Evidence:** new test `test_interrupted_before_first_date_still_keeps_the_computed_range`
(`apps/backend/tests/test_data_manager_jobs_pipeline.py`) — observed **RED first** with the call commented
out (`assert detail["dates_total"] == 3` → `assert 0 == 3`, 1 failed in 23.28s), **GREEN** with it
(`2 passed in 74.85s` alongside the dev's own F1 test).

**B2 — verified-correct (no action): the F1 checkpoint's concurrency and idempotency claims hold**
I traced both call paths of `_persist_isolated`: the serial one (`:2992`) and the parallel one (`:3017`,
inside the orchestrator's own `as_completed` drain loop — workers only *compute*). So the checkpoint only
ever runs on the orchestrating thread: no concurrent `UPDATE`, no SQLite lock contention. Its side effect
`prog.error_other = prog.date_failures_total` (`:3692`) is an **assignment**, identical to the end-of-stage
derivation at `:3031` — re-running it mid-loop cannot double-count. `sweep_orphaned_runs` (`:3746-3760`)
touches only `status`/`finished_at`, so a checkpointed `message` survives the sweep. Claims confirmed.

**B3 — GAP (not fixed, carried from round 1; reviewer concurs): no `command -v taskset` guard**
`incredible_auto_dev/scripts/start-backend.sh:89` and `dev.sh:78` build `HOST_GUARD_CMD_PREFIX=(taskset -c
…)` unconditionally when `HOST_GUARD_ENABLED=1`. On a host without `util-linux`'s `taskset`, `exec` fails
and the backend simply does not start. `taskset` is present on this host (TC-7/TC-8 pass live), so this is
a portability limitation, not a live defect. One-line fix when scoped: mirror `run-goal.sh`'s
`command -v taskset` check.

**B4 — OBSERVATION: `dev.sh`'s config read inherits `start-backend.sh`'s unguarded failure mode**
`dev.sh:49-56` — if the `.venv` python config read emits nothing, `ulimit -v $((MEMORY_CAP_MB * 1024))`
raises a bash arithmetic error under `set -e` and the backend subshell dies silently. Identical to the
pre-existing pattern in `start-backend.sh`; no behavior change introduced by this iteration.

### Evidence / Artifact Findings

**P1 — IMPORTANT (fixed): the perf-budgets narrative attributed part of the VmPeak margin narrowing to
sampling cadence, which this run's own data refutes**
`reports/perf-budgets.md` (iter-9 section) and the dev handoff both explained the 43.6% → 24.7% margin
narrowing as possibly caused by "a finer sampling cadence (4× more chances to catch a transient peak)" and
a larger DB, "and this run cannot separate them." The pump asked me to scrutinise exactly this. **The
cadence half is not merely unproven — it is impossible.** `VmPeak` in `/proc/<pid>/status` is a
kernel-maintained high-water mark: monotone non-decreasing for the process's life. Verified directly on
the retained trace (`runs/goal-ops-hardening-iter-9/heavy-ingest-vm-samples.csv`, 4,347 rows): the series
is monotone across every consecutive pair, and re-subsampling it at iter-8's **1 Hz** cadence — and at one
sample per **10 s** — reports the **identical** 4,738,948 KB peak. Sampling contributes 0 KB of the
1,190,124 KB increase. Leaving the benign-sounding explanation on file invites a future reader to discount
a real trend on a false basis.
**Fix applied:** an `AUDIT CORRECTION` block in `reports/perf-budgets.md` (with the monotonicity argument
and the subsample check) and a matching note in the dev handoff. No measured number was altered; no budget
loosened.

**P2 — verified-correct (no action): every headline number of the heavy run reproduces from the raw
evidence**
Independently recomputed from the retained files, not from the handoff: peak VmPeak **4,738,948 KB**, peak
VmSize 4,608,900, peak VmRSS/VmHWM 3,946,472/3,948,188; **439/439** health polls HTTP 200 with median
0.398 s / max 3.646 s and 46 polls > 1 s; hwmon max Tctl **81 °C**, DIMM 44/43 °C, NVMe 41 °C, PPT 44 W,
min mem_avail 16,866 MB; sampler cadence 0.25 s over a 1,087.7 s window; `heavy-ingest-pytest.log` = `1
passed in 1092.93s`. The hwmon slice (15:18:31–15:36:48) brackets the VM window (15:18:35–15:36:43) —
the thermal record really covers the run. The measured process was launched by the **new** launcher block:
`logs/backend.log:24243-24245` shows `launching at 2026-07-22T15:18:34Z` / `port=18755 memory_cap_mb=6144
malloc_arena_max=2` / `host-guard: cpu_list=0-3,8-11 blas_threads=4`. The attribution claim ("the caps came
from this iteration's own launcher block") is therefore substantiated, not asserted.

**P3 — GAP: no artifact anywhere carries an explicit `J-05` verdict line**
The DoD's first item is "J-05 passes all four acceptance steps via browser-qa-agent". The raw lane
(`...-ui-test-results.llm.md`) has explicit rows for UT-J-01/UT-J-03/UT-J-04 but **none for J-05** — its
evidence is spread across the UT-XX rows. Traced against `docs/goal.md:215-233`, the mapping is complete
and every cited row is a raw-lane PASS: step 1 → UT-04 (job `ok`, all 7 `aggregates_refreshed`, re-queried
post-restart) **and** the heavy run's job 2 (2026-04-21, `ok`, 1 snapshot, all 7 categories); step 2 →
UT-05 (leaderboard row), UT-06 (run detail matches the stored snapshot), UT-07 (market phase for the new
as-of, no delay), UT-04 (the persisted refresh list); step 3 → UT-08 (cold `/data` after the pump's
restart, `GET /api/data` responseEnd 436.9 ms / duration 126.4 ms vs a 1.5 s warm-API budget); step 4 →
UT-J-03 (live 4-min chunked backfill, health 200 throughout, RSS ~4.2 GB of the 6,144 MB cap) **and** the
heavy-ingest run's 439/439 polls. J-05 is scoreable as `passing` from those citations — but a future
reader should not have to assemble it; the browser lane should emit a `UT-J-05` row.

**P4 — GAP: `reports/qa/goal-ops-hardening-iter-9-qa.md` is stale and now contradicts the tree**
It still records TC-05/TC-06 as "DEFERRED — host safety" and TC-10/11/12/14 as "NOT EXECUTED", and carries
a `PASS` verdict generated at 09:30 UTC — before both the browser lane (11:57-12:30) and the heavy run
(15:18-15:36). A reader who trusts only the QA report would conclude the heavy measurement never happened
and that no browser evidence exists. Not fixed (regenerating a QA artifact is not audit scope); the
authoritative artifacts are the raw `.llm.md`, `reports/perf-budgets.md`, and the retained CSVs.

### Frontend Findings

**F1 — IMPORTANT (open, operator-gated): J-04 step 6 has NO post-fix browser evidence — J-04 must stay
`unknown`, not `passing`**
The only recorded J-04 outcome is the raw lane's `UT-J-04` **FAIL at step 6** (and `UT-10` FAIL), taken
*before* `_checkpoint_run_record` existed. The fix is real and unit-proven (3 tests incl. mine), and the
frontend needs no change (`apps/frontend/app/data/page.tsx:2612` already null-coalesces
`snapshots_created`/`dates_total`), but per the evidence floor a journey is `passing` only on journey-level
evidence. This is the single item standing between this iteration and a PASS.

**F2 — IMPORTANT (open, operator action required BEFORE that re-run): the live backend predates the fix
and `start-backend.sh` does not hot-reload**
The process serving `:8255` is pid **1803579**, started **17:59:28 BST** (`logs/backend.log:25754` =
`16:59:28Z`), and its command line is `uvicorn main:app --host 0.0.0.0 --port 8255` — **no `--reload`**.
The F1 fix landed at `17:05:00Z`/18:05 BST (`status.json.updated_at`) and my B1 fix later still. So the
running backend executes **pre-F1** code. A kill/restart cycle run against it would create the interrupted
row inside the *old* process and reproduce the original FAIL for a stale-build reason — the same class of
false negative that produced this iteration's first browser pass (stale `.next` bundle). **The backend
must be restarted first, then the backfill started, then killed, then restarted.** I did not restart
anything (service control is the operator's).

### Test Findings

**T1 — GAP: the new `aggregates_refreshed` completeness assertion cannot detect a mid-loop `MemoryError`
abort**
TC-6's stated purpose is "proving no loop silently early-aborted on `MemoryError`". The market-phase warm
appends its category on `if market_phase_warmed:` (`data_manager.py:3197-3198`), i.e. after **any one**
date warms successfully — so an abort at date 2 of 300 still yields all seven categories and the assertion
passes. The check is necessary, not sufficient. For *this* run I closed the gap independently: the spawned
backend's log region (from `logs/backend.log:24243`, the 15:18:34Z launch) contains **no** `warm aborted`
or `MemoryError` line at all, so no loop aborted during the measured run. A future iteration could assert
the warmed-date count rather than category presence.

**T2 — OBSERVATION: `dev.sh`'s host-guard-**absent** branch is untested (only the disabled branch is)**
Documented in the test's own docstring, and both branches share one no-op code path in the same block.
Acceptable, and honestly disclosed rather than glossed.

**T3 — OBSERVATION: pre-existing `tests/test_db.py::test_create_all_produces_expected_tables` failure**
Stale expected-table set since iter-2 (`coverage_snapshot`, `forward_aggregate_cache` missing). Correctly
discovered, disclosed (Known Issue #6) and NOT fixed under fix-mode rules. Unrelated to this diff.

**T4 — verified-correct: the T4 tightening deleted nothing**
`git diff` of `test_start_backend_script.py` removes exactly four assertion-bearing lines — the two
loosened `status in ("ok","partial")` checks and the hardcoded `2010-07-15` job — and no VmPeak/VmSize/
health/sampler assertion. The iter-8 splice lesson was genuinely applied.

---

## 3. Domain Assessment

The domain logic under audit is job-lifecycle bookkeeping and host-resource containment, and both are in
good shape.

*Run-record honesty.* The design keeps one representation of a job's detail (`_run_detail`) served by three
writers (create / checkpoint / finalize), with nullability gated on `calendar_days > 0` so a not-yet-planned
row serves `null` rather than a fabricated "0 calendar days". The checkpoint respects that contract exactly:
`message`-only, never `status`/`finished_at`, never an INSERT, throttled, non-fatal. My B1 addition is
consistent with it — after the plan is computed, `calendar_days > 0` holds, so the breakdown the row now
carries is real, not a default. `aggregates_refreshed` still serves `null` on an interrupted row, which is
the honest answer (the finalize hook never ran) and preserves AG-3.

*Host containment.* The AG-10 blocks are config-driven with no magic numbers, additive to the existing
`ulimit -v`/`MALLOC_ARENA_MAX` enforcement, no-op when the file is absent or disabled, and correctly scoped
to the backend subshell only. The evidence chain is now complete in both directions: unit-level
(`/proc/<pid>` assertions relative to the test process's own affinity — the right invariant on a sandbox
that is itself pinned), live (`pid 1803579`'s `/proc` state), and under load (the measured 18-minute heavy
run's own boot line).

*The one number to keep watching.* 4,627.9 MB against a 6,144 MB ceiling is a 24.7% margin that, per P1, is
genuinely worse than iter-8's 43.6% — not a sampling artifact. The workload passes today; it is closer to
the wall than the previous section implied, and the DB only grows.

---

## 4. Fixes Applied During This Audit

| # | Severity | File | Change |
|---|----------|------|--------|
| 1 | Important | `apps/backend/app/engine/data_manager.py` | Added one `_checkpoint_run_record(eng, prog)` call after the target plan is computed and before the bar-cache prefill, so a kill in the (minutes-long) pre-loop window still leaves the real range/plan on the interrupted row instead of zeros (B1) |
| 2 | Important | `apps/backend/tests/test_data_manager_jobs_pipeline.py` | New regression test `test_interrupted_before_first_date_still_keeps_the_computed_range` — simulates death inside the prefill (`prefilled_bar_cache` raises, `_finalize_run_record` patched away), sweeps, asserts `dates_total == 3` / real `calendar_days` / `snapshots_created == 0` / `aggregates_refreshed is None`. RED observed first (`assert 0 == 3`) |
| 3 | Important | `reports/perf-budgets.md` | `AUDIT CORRECTION` block: the sampling-cadence explanation for the VmPeak margin narrowing is refuted (VmPeak is a monotone high-water mark; the retained 4 Hz trace re-subsampled at 1 Hz and 0.1 Hz yields the identical peak) — the narrowing is real (P1). No measured number altered, no budget loosened |
| 4 | Important | `docs/handoffs/goal-ops-hardening-iter-9-dev.md` | Matching correction note on the same attribution claim, plus an addition note recording the B1 gap and its fix so the handoff's F1 description stays accurate |

**Verification of the fixes (commands and results, this audit):**

- `pytest tests/test_data_manager_jobs_pipeline.py -k "checkpoint or interrupted" -v` → **5 passed, 16
  deselected (202.33s)** (includes the dev's 2 F1 tests and my new one)
- RED proof: with the added call commented out,
  `pytest …::test_interrupted_before_first_date_still_keeps_the_computed_range -q` → **1 failed (23.28s)**,
  `assert detail["dates_total"] == 3` → `assert 0 == 3`
- After restoring the call: `pytest …::test_interrupted_before_first_date_still_keeps_the_computed_range
  …::test_interrupted_job_keeps_its_last_checkpointed_progress -q` → **2 passed (74.85s)**
- Whole-cluster regression after the fix: `pytest tests/test_data_manager_jobs_pipeline.py -q` → **21
  passed in 560.33s** (the dev's 20 + my new one; the extra pre-loop `UPDATE` regresses nothing in the
  J-59/J-60/J-66 lifecycle cluster). The full suite was NOT run (standing constraint)
- P1's claim re-derived with a script over `heavy-ingest-vm-samples.csv`: series monotone
  non-decreasing = True; max at 1 Hz subsample = max at 0.1 Hz subsample = 4,738,948 KB = the full-rate max
- The heavy workload was **not** re-run (operator constraint; its evidence is already on disk)

### DoD scorecard

| # | Definition-of-Done item | Verdict |
|---|---|---|
| 1 | J-05's four steps in a real browser + the heavy-ingest run, RAW `.llm.md` read | **MET** (evidence traced in P3; caveat: no explicit J-05 row) |
| 2 | Replay-results record J-01, J-03 **and J-04** passing | **NOT MET** — J-04 = `unknown` pending the post-fix kill/restart (F1) |
| 3 | Both launch scripts apply `host-guard.env` caps; frontend untouched; AG-10 resolved | **MET** (TC-7/8/9 + live `/proc` + the measured run's boot line) |
| 4 | Heavy test rejects `"partial"`, asserts completeness, keeps every prior assertion | **MET** (T4; caveat T1) |
| 5 | Sampler CSV retained under `runs/goal-ops-hardening-iter-9/` | **MET** (contents independently re-derived, P2) |
| 6 | No anti-goal violation; AG-10 closed; AG-8 re-assessed on host-guard-consistent evidence | **MET** — with the honest caveat now recorded (P1). `HOST_GUARD_REQUIRE_MARKERS` stays `0` (owner/framework work, explicitly out of scope) |
| 7 | Unit tests pass, exact commands/counts in the handoff | **MET** |
| 8 | Handoff carries forward the `/api/backtest` `MemoryError` and the unproduced `--session-live` walkthroughs | **MET** |

---

## 5. Recommended Next Step

**Do not close the session as GOAL_ACHIEVED yet, and do not let any downstream agent flip J-04 to
`passing` on the strength of the F1 fix alone.** The precise remaining sequence, in order:

1. **Operator restarts the backend** (`scripts/start-backend.sh`) so the running process contains
   `_checkpoint_run_record` **and** the audit's pre-loop checkpoint (F2 — the current pid 1803579 predates
   both and uvicorn is not in `--reload` mode). Confirm the new pid's `/proc` still shows
   `Cpus_allowed_list 0-3,8-11`.
2. **Operator re-runs the UT-10 / UT-J-04 step-6 cycle on the restarted build**: start a multi-date
   backfill on `/data`, let it advance past its first date (≥ 10 s of per-date progress, so at least one
   checkpoint lands), `kill -9`, restart, and read the run's row. Expected now: badge `interrupted` **and**
   non-zero `dates_total` / `snapshots_created` frozen at the crash point. If the kill lands during the
   bar-cache prefill instead, expect the real range with `0 snapshots` — also a pass for the journey's
   literal text ("last persisted progress"), and no longer "0 trading days in range".
3. Score J-04 from the RAW `.llm.md` verdict lines only (TC-14), then update
   `reports/phase-goal-ops-hardening-iter-9-regression-replay-results.md` — whose auditor addendum
   currently records J-04 as failing at step 6 — so DoD item 2 can be closed honestly.
4. Owner decisions still outstanding and unchanged: the deferred on-load `/api/backtest` `MemoryError`
   (J-06/AG-8), the unproduced `demo.sh --session-live` walkthroughs for J-05/J-06, and — now that the
   launcher caps have landed and are live-verified — whether to flip `HOST_GUARD_REQUIRE_MARKERS` to `1`
   so stripping a HOST-GUARD block pauses the engine (the file's own comment schedules exactly this).
5. Framework maintainer (unchanged, still unfixed): `merge_ui_test_results.py:57` drops emphasised
   `**FAIL**` verdict cells.
