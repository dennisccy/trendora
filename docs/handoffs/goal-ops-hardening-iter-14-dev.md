# goal-ops-hardening-iter-14 Dev Handoff

**Phase:** goal-ops-hardening-iter-14
**Date:** 2026-07-23
**Agent:** developer
**Status:** complete (code + targeted tests). TC-5/TC-7 (the full-deep-basis measurement pass) CLOSED PASS
via an operator-supervised pass, transcribed into the canonical artifact 2026-07-23 — see "Operator
action needed" below (now resolved) and the "Operator-Supervised Measurement Transcription" section at
the end of this handoff. TC-6 has partial evidence only; evaluator decides sufficiency — see Known Issue
#2.

## What Was Built

- **Bounded/streamed rewrite of `compute_forward_aggregates`** (`apps/backend/app/engine/forward_testing.py`)
  — the two whole-partition ORM reads this REGRESSION-recovery iteration targets:
  - The `ForwardReturn` scan (previously `select(ForwardReturn).where(horizon==h)` [+ optional `as_of`
    join], materialized via `.all()`) is now column-projected to the 4 fields actually read
    (`run_id`, `symbol`, `realized_return`, `max_drawdown`) and consumed via
    `.yield_per(cfg.research.read_batch_size)`, building `ret_by_run_symbol`, `mdd_by_run_symbol`, and the
    `runs_with_fr` set incrementally in a single pass.
  - The `ScannerResult` scan (previously `select(ScannerResult).where(run_id.in_(runs_with_fr))`,
    materialized via `.all()` — the table with the largest per-row footprint, `record_json` blobs) is now
    column-projected to the 8 fields actually read (`run_id`, `ticker`, `leadership_bucket`,
    `setup_status`, `sector`, `rank`, `is_vcp`, `is_pullback_to_rising_dma`, `is_flat_base_breakout`) and
    consumed the same way, ordered by `ScannerResult.id` (mirroring `research._subject_matching_result_
    rows`'s established precedent for this exact table) so the streamed order reproduces the row order the
    prior un-ordered `.all()` naturally returned. `stock_obs` is built directly in the loop with the SAME
    `if realized is None: continue` NA gate.
  - The `ScannerRun` read (`run_rows`, ~line 829 pre-rewrite) is UNTOUCHED, per the plan — bounded/small
    (one row per cadence date), not one of the two named offenders.
  - Same function signature, same return dict shape, same batch-size config knob
    (`cfg.research.read_batch_size` — the SAME single source `_streamed_existing_keys`/`research.py`
    already use; no second batch-size config value introduced). The three call sites
    (`forward_aggregates_cached` same file, `GET /api/backtest`, the MCP `query_backtest` tool) are
    confirmed unchanged (`git diff` shows neither `app/api/backtest.py` nor `app/mcp/tools.py` in the
    diff).
- **Byte-identity test suite** (`apps/backend/tests/test_forward_testing_aggregates_streaming.py`, new) —
  a pinned copy of the pre-rewrite implementation (`_reference_compute_forward_aggregates`, calling the
  SAME unchanged downstream helpers `benchmark_symbols`/`_group_means`/`_control_groups`/
  `_attribution_slices`/`_mean_or_none`) compared against the rewritten function on a hand-built 4-run
  (+ 1 zero-forward-return run) fixture spanning 3 real config sectors, all 3 rank bands, mixed VCP/
  pullback/flat-base flags, and both Risk-on/Risk-off regimes. Parametrized across all 5 configured
  horizons `[1, 5, 10, 20, 60]` x `{as_of=None, a historical as_of that excludes the newest snapshot}` x 3
  streaming batch sizes (`1, 3, 1_000_000`) = 30 full-dict equality assertions, plus 2 sanity checks (32
  tests total, all passing). Verified this test's own discriminating power two ways: (a) a deliberate
  column-swap mutation in the rewrite made 31/32 of these tests fail immediately (then reverted); (b)
  re-running this same file against the TRUE pre-rewrite original (`git show HEAD:...`) correctly FAILS
  the "new succeeds under the same cap" assertion in the companion TC-3 file (see below) — confirming the
  test suite actually depends on the fix being present, not just on syntactic validity.
- **TC-3: a REAL (non-monkeypatched) tightened-`ulimit -v` induction test**
  (`apps/backend/tests/test_forward_testing_concurrency.py`, new) — empirically calibrated (measured on
  this host, not guessed): a 60,000-row `ScannerResult`+`ForwardReturn` fixture (`record_json` padded to
  4,000 bytes, mirroring the real table's dominant per-row cost) shows the pre-rewrite unbounded pattern
  needing ~587 MB VmPeak vs. the rewritten pattern needing ~255 MB (baseline ~100 MB). A `ulimit -v` of
  420,000 KB (~410 MB) sits between the two. Two tests: (1) a preserved copy of the pre-rewrite pattern,
  run in a real subprocess under this cap, raises `MemoryError` honestly (no hang, sub-2s) and a fresh
  same-process session re-reading an existing `ForwardAggregateCache` row succeeds immediately after; (2)
  the REWRITTEN `compute_forward_aggregates`, run under the IDENTICAL cap against the SAME fixture,
  succeeds — the direct proof the fix closes the gap. Both verified failing/passing appropriately when I
  temporarily reverted the source to the true pre-rewrite version (`git show HEAD:...`) and back.
- **TC-4: a concurrent-caller regression test** (same new file) — a `ThreadPoolExecutor` with 4 threads
  calling `forward_aggregates_cached` (mirroring 4 concurrent backfills' finalize hooks racing on the SAME
  cache key — exercising the existing `ForwardAggregateCache` unique-constraint race that function's own
  `except Exception: session.rollback()` is designed to absorb) plus 1 thread calling
  `compute_forward_aggregates` directly (the "diagnostic read" in iter-13's own trigger shape), all against
  a shared file-based engine. All 5 complete well within the 45s bounded timeout (measured ~7-10s), zero
  errors, and all 5 returned payloads are byte-identical (the cache race changes only who persists, never
  what is computed).
- **`reports/perf-budgets.md`** gained two new dated sections:
  1. A verbatim transcription of iter-13's already-evaluator-confirmed J-06 readings (218.7 ms / 218.7 ms
     / 219.2 ms on `/data`, 70.5 ms on `/`, each labeled PASS against the ≤1,500 ms budget with margin),
     sourced from `reports/phase-goal-ops-hardening-iter-13-ui-test-results.llm.md` and the iter-13 audit/
     closure-verdict chain — transcription only, no new measurement.
  2. An honest "PENDING, operator-supervised" placeholder for TC-5/TC-6/TC-7 (the full-deep-basis
     measurement pass), stating plainly this was NOT performed this turn and recording the exact protocol
     for whoever runs it next — no number fabricated or estimated.

## Files Changed

- `apps/backend/app/engine/forward_testing.py` -- rewrote the `ForwardReturn` and `ScannerResult` reads
  inside `compute_forward_aggregates` to column-projected `yield_per`-streamed access; no signature/return-
  shape change; `run_rows` (`ScannerRun`) read untouched; +84/-36 lines (`git diff --stat`).
- `apps/backend/tests/test_forward_testing_aggregates_streaming.py` (new) -- TC-1/TC-2 byte-identity suite,
  32 tests.
- `apps/backend/tests/test_forward_testing_concurrency.py` (new) -- TC-3 (real memory-cap induction, 2
  tests) + TC-4 (concurrent-caller, 1 test), 3 tests.
- `reports/perf-budgets.md` -- two new dated sections (TC-8 transcription; TC-5/6/7 pending placeholder).
- `docs/handoffs/goal-ops-hardening-iter-14-dev.md` -- this handoff (new).

No file under `apps/frontend/` appears in the diff (`Frontend Present: no`, confirmed by `git status`).
`main.py`, `app/api/health.py`, `app/engine/readiness.py`, `app/engine/warmup.py` are confirmed
byte-unchanged (absent from `git status`). `app/api/backtest.py` and `app/mcp/tools.py` are confirmed
byte-unchanged (absent from `git status`) — both call sites are unaffected by this rewrite.

## Tests Run

All commands run from `apps/backend/`, host-guard-confined per the pump note
(`taskset -c 0-3,8-11`, `OMP_NUM_THREADS=OPENBLAS_NUM_THREADS=MKL_NUM_THREADS=NUMEXPR_NUM_THREADS=4`),
with `TMPDIR`/`TMP`/`TEMP` exported per the dispatch's environment note.

Command:
```
taskset -c 0-3,8-11 .venv/bin/python -m pytest \
  tests/test_forward_testing.py tests/test_forward_testing_streaming.py \
  tests/test_forward_testing_aggregates_streaming.py tests/test_forward_testing_concurrency.py \
  tests/test_backtest_scorecard.py tests/test_research.py \
  -k "not test_walk_forward_asof_dates_are_real_trading_days_with_full_horizon and not test_backfill_inserts_forward_returns_without_mutating_snapshot and not test_backfill_is_idempotent and not test_backfill_populates_mae_mfe_within_band and not test_backfill_populates_max_drawdown_same_na_gate and not test_backfill_latest_run_has_zero_post_bars and not test_stored_scores_identical_with_and_without_forward_returns" \
  -q
```
Result: **229 passed, 7 deselected in 35.15s**

Command: `taskset -c 0-3,8-11 .venv/bin/python -m pytest tests/test_data_manager.py -k "forward_aggregate" -q`
Result: **4 passed, 132 deselected in 0.87s**

Zero new failures. The 7 deselected tests (all in `test_forward_testing.py`) use `loaded_engine` or the
local `backfilled_engine` fixture, both of which do a full real-seed `load_seed()` — deliberately not run
this turn (see Known Issues #1). None of the 7 calls `compute_forward_aggregates` directly (confirmed by
grep); all test the backfill/scoring path, which this diff does not touch.

**Discriminating-power verification (not a normal test run, done twice by design):**
1. Deliberately swapped the `sector`/`setup_status` projected-column assignment in the rewrite — 31/32
   byte-identity tests failed immediately (then reverted, confirmed clean via `git diff --stat`).
2. Temporarily restored the TRUE pre-rewrite file (`git show HEAD:apps/backend/app/engine/forward_testing.py`)
   and re-ran the new concurrency test file: `test_tc3_rewritten_pattern_succeeds_under_the_same_cap_that_broke_the_old_one`
   correctly FAILED with `UNEXPECTED_MEMORYERROR` (the pre-rewrite code needs more memory than the fix
   does, as expected), while the "old pattern fails honestly" and TC-4 tests still passed (unaffected by
   which version is in place, by design). Restored the fix afterward (`git diff --stat` confirmed back to
   the intended 84/-36-line change).

## Operator action needed: TC-5 / TC-6 / TC-7 (full-deep-basis measurement pass)

**RESOLVED 2026-07-23 — see the "Operator-Supervised Measurement Transcription" section at the end of
this handoff, and `reports/perf-budgets.md`'s "TC-5 / TC-6 / TC-7 ... RESULTS (operator-supervised pass,
2026-07-23)" section for the full numbers. TC-5/TC-7 close PASS; TC-6 has partial evidence only (see Known
Issue #2). The paragraph below is left unedited as the historical record of what was requested and why.**

Per this iteration's PUMP NOTE, services are DOWN as of this dispatch and this pipeline's agents cannot
start/stop them this session; the full-deep-basis warm is additionally AG-10-class (one owner-authorized,
cooled-host, sampler+watchdog-armed pass). **I did not attempt to start any service.** The exact protocol
for the next pass (mirroring iter-3/8/9's own precedent) is recorded in `reports/perf-budgets.md`'s new
"TC-5 / TC-6 / TC-7 ... PENDING" section: start `scripts/start-backend.sh` under host-guard confinement
against the real deep-basis DB, poll `GET /api/health` at 1 Hz (closes TC-7 against the ≤5s boot budget),
let the finalize warm trigger all 5 horizons then call `GET /api/backtest` per horizon in the same process,
sample `/proc/<pid>/status` VmPeak at 1 Hz against the 6,291,456 KB cap (closes TC-5), and induce a
memory-pressure condition during one horizon's warm to confirm the same process keeps serving `/api/health`
+ cached reads afterward (closes TC-6). Report console output, PIDs, and timestamps verbatim for the next
developer turn to transcribe into `reports/perf-budgets.md` with attribution.

## Known Issues

**1. Seven pre-existing `test_forward_testing.py` tests were not re-run this turn** (all depend on
`loaded_engine` or the file-local `backfilled_engine` fixture, both of which do a real `load_seed()` — a
multi-minute-plus cost this session's own convention warns against running casually for a change that
doesn't touch the backfill/scoring path). Confirmed by grep that none of the 7 calls
`compute_forward_aggregates` directly. Similarly, `test_api_engine.py`, `test_api_backtest.py` (both
depend on the session-scoped `loaded_engine` fixture, ~80 min per this session's own documented convention)
and `test_iter27_rebuild_mdd.py` (its own module-scoped `load_seed(engine, cfg, None)` — the real, full
seed, not a reduced one) were also not run, for the same reason. This diff's correctness for their call
patterns is covered instead by: (a) the byte-identity proof (`compute_forward_aggregates`'s output is
unchanged for any input), and (b) confirming both of `compute_forward_aggregates`'s non-test call sites
(`app/api/backtest.py`, `app/mcp/tools.py`) are textually byte-unchanged.

**2. TC-5/TC-6/TC-7 (the full-deep-basis measurement pass) — UPDATED 2026-07-23.** An operator-supervised
pass was run after this handoff was first written (backend pid 3669411, host-guard-confined, real
deep-basis DB); this developer turn transcribed the results verbatim with attribution into
`reports/perf-budgets.md` (new "...RESULTS (operator-supervised pass, 2026-07-23)" section) and
independently recomputed the headline figures against the two retained raw CSVs
(`runs/goal-ops-hardening-iter-14/tc5-vm-samples.csv`, `tc5-health.csv`).

**TC-7: PASS** (1.80 s vs the ≤5 s boot budget, ~2.8x margin).

**TC-5: PASS** (250/250 `GET /api/health` polls HTTP 200 throughout the 278 s full-deep-basis
forward-aggregates warm, no frozen window, median 0.157 s / max 1.444 s; peak `VmPeak` 2,404,408 KB vs the
6,291,456 KB / 6144 MB cap, 61.8% margin — the first successful full-deep-basis forward-aggregate warm
since the basis grew this large; iters 11-13 aborted 3-for-3 with `MemoryError` at this exact step).

**TC-6: NOT fully resolved.** The operator did not induce artificial memory pressure on the LIVE
full-basis process (judged not a justified action on this crash-history host — PC hard-reset 2026-07-20/21
under ingest bursts is the reason the host-guard hardening exists at all). TC-6's evidence rests on the
prior turn's TC-3 (a REAL tightened-`ulimit -v` induction, but on a synthetic 60,000-row fixture in a
throwaway subprocess, not this live process) plus this pass's absence of any organic
`MemoryError`/memory-pressure log line during the 278 s warm. Neither is a live induced-pressure repro on
the exact TC-5 process TC-6's GWT specifies — the evaluator decides whether this is sufficient or whether a
follow-up live-induction pass is still needed.

**3. Pre-handoff "service startup works" check was not performed — status unchanged by the later
transcription turn, for a different reason than originally stated.** At original write time, services
were DOWN and this constraint meant "cannot start them." As of the 2026-07-23 transcription turn, the
backend IS running (pid 3669411, started by the operator's TC-5/6/7 pass) and that turn was explicitly
instructed NOT to start or stop it (it must stay up for the browser-qa lane that follows). So the standard
"stop, restart, verify no port conflicts" pre-handoff check still was not performed in either turn — first
because nothing was up to test, now because something is up that must not be touched. No service action
was needed for either turn's actual scope (originally: new tests using throwaway file-based SQLite
fixtures via `make_engine`, never the live app process; the transcription turn: a canonical-artifact
transcription plus a handoff/status edit, no code or test change).

**4. No external integrations or native dependencies were added** — this iteration is a pure internal
read-path rewrite; the "external integrations work live" and "native dependency binaries" pre-handoff
checks do not apply.

**5. This iteration does not itself prove or claim J-06 or J-07 "passes."** Per the plan's carried iter-12
lesson, this handoff records only what the developer-stage tests (TC-1 through TC-4) actually show: byte-
identity holds, the real memory-pressure induction succeeds where the pre-rewrite pattern honestly failed,
and the concurrent-caller test shows no hang. TC-5/TC-6/TC-7 (memory/health under the full deep basis) and
TC-9/TC-10 (browser regression replay) remain outstanding, per their own owners (operator and browser-qa-
agent respectively) — the evaluator should score J-07/J-06 only once those close.

**6. Carried, unrelated: `tests/test_db.py::test_create_all_produces_expected_tables`** is a pre-existing
failure (stale since iter-2, missing table names in its expected set), unaffected by this iteration (no
schema change) and not re-run this turn, per the plan's own explicit carve-out.

**7. `assumptions.md`'s already-logged interpretation call** (TC-3/TC-4 going beyond J-07 step 4's literal
"test hook OR monkeypatch, single sequential process" wording) was not re-litigated or re-logged here — the
plan states it is already recorded in `runs/goal-session-ops-hardening/state/assumptions.md`; this handoff
just confirms the resulting tests were actually built to that stricter standard (real subprocess induction,
real thread concurrency), not the cheaper reading.

## Operator-Supervised Measurement Transcription (2026-07-23)

**Continuation context:** this is a fresh continuation of the developer lane for this same iteration (the
subagent-resume channel was broken this session); the original build turn above (code, tests, handoff,
`reports/perf-budgets.md`'s PENDING placeholder) is untouched except where explicitly cross-referenced.
This turn touched only: `reports/perf-budgets.md` (resolved the PENDING section with the operator's
results), this handoff (Status line, the "Operator action needed" section, Known Issues #2/#3, this
section), and `runs/goal-ops-hardening-iter-14/status.json`. No source file, test file, or config file was
touched. No service was started or stopped — backend pid 3669411 was already up from the operator's pass
and was left running throughout, per explicit instruction (it must stay up for the browser lane).

**What happened:** the operator ran the TC-5/TC-6/TC-7 protocol this handoff's "Operator action needed"
section specified (mirroring the iter-3/8/9 VmPeak-measurement precedent) and reported console output,
timestamps, and two raw sampler CSVs verbatim. This turn transcribed those results with attribution into
`reports/perf-budgets.md`'s new "TC-5 / TC-6 / TC-7 — full-deep-basis measurement pass (J-07): RESULTS
(operator-supervised pass, 2026-07-23)" section — the canonical, single-source location for these numbers
— and independently recomputed the headline figures directly from the two retained CSVs
(`runs/goal-ops-hardening-iter-14/tc5-vm-samples.csv`, 250 rows; `tc5-health.csv`, 250 rows) rather than
accepting the operator's arithmetic on faith. Every recomputed figure matched the operator's reported
figure exactly (peak `VmPeak` 2,404,408 KB → 61.8% margin under the 6,291,456 KB cap; health-poll median
0.157 s / max 1.444 s over 250/250 HTTP 200; the 278 s warm-job duration from its own launch/terminal
timestamps; the boot-banner log line's UTC timestamp matching the operator's BST launch time exactly, a
1-hour offset).

**Result in one line:** TC-7 and TC-5 close **PASS** with wide margin (1.80 s vs ≤5 s; 2,404,408 KB vs
6,291,456 KB, 61.8% margin; 250/250 health polls 200, no frozen window across the 278 s full-deep-basis
forward-aggregates warm — the first one this basis size has ever completed, vs. 3-for-3 `MemoryError`
aborts in iters 11-13). TC-6 remains **partial** — no live pressure was induced on the measured process
this pass; the evaluator decides whether TC-3's synthetic-subprocess induction (prior turn) plus this
pass's organic-absence observation are sufficient, per Known Issue #2 above. Full numbers, recomputation
detail, and the honest TC-6 caveat are in `reports/perf-budgets.md`, not duplicated here (this session's
own "budgets live in one canonical file" convention).
