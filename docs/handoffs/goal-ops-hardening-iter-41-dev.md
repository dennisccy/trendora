# goal-ops-hardening-iter-41 Dev Handoff

**Phase:** goal-ops-hardening-iter-41
**Date:** 2026-07-31
**Agent:** developer
**Status:** complete

## What Was Built

This iteration had two headline closures (verification-lane repair + the last unbounded whole-table
load) plus small ride-along fixes, per the plan's own framing. No new UI capability — Frontend Present:
no.

### A. Verification-lane repair (A1-A4)

- **A1 — health-check URL fix.** `browser-qa-phase.sh`, `goal-iter-lean.sh`, `qa-phase.sh`,
  `demo-phase.sh`, `run-phase.sh` all used to derive `BACKEND_HEALTH_URL` from the framework's generic
  `.../health` default, which 404s on Trendora (every route is namespaced under `/api`). Factored a
  shared `resolve_backend_health_url()` helper into `lib/common.sh` (mirroring `demo_runner.py`'s
  already-fixed iter-39 override) and switched all five call sites to it.
- **A1 companion fix (found during implementation, not in the original file list — see "Plan gap
  found" below).** `run-phase.sh`'s Steps 5/6, plus `ui-test-design-phase.sh` and `browser-qa-phase.sh`'s
  own standalone early exits, ALL unconditionally skipped UI test design + browser QA (writing bare N/A
  stubs) whenever `Frontend Present: no` — regardless of whether the iteration spec named
  required-still-passing journeys needing regression re-verification. This is the ACTUAL mechanism that
  let iter-40 ship all seven required-still-passing journeys with zero evidence: the agent-level fix
  below (A2) was unreachable behind these shell-level gates. Added
  `phase_spec_has_required_regression()` to `lib/common.sh` and used it as a carve-out in all three
  gates: a backend-only goal-mode iteration that names required-still-passing journeys now still runs
  Steps 5/6.
- **A2 — `ui-test-designer` neutral source.** Rewrote "Backend-only phase handling"
  (`incredible_auto_dev/agents/ui-test-designer/body.md`): `Frontend Present: no` now suppresses
  NEW-surface test-case generation ONLY; it still emits one `UT-J-XX` regression test case per
  required-still-passing journey named in the phase spec's metadata, sourced from `docs/goal.md`'s
  Must-have user journeys section. Re-rendered `.claude/agents/ui-test-designer.md` via
  `sync-cli-assets.py --cli claude`. Also lightly extended `ui-test-design-phase.sh`'s own dispatch
  prompt with a note pointing the agent at this behavior when backend-only.
- **A3 — `merge_ui_test_results.py` missing-required-journey detection.** Added
  `missing_required_journeys()` and wired it into `merge()`: a required-still-passing journey with ZERO
  executed test cases (no row at all from any lane) now forces the merged headline away from a clean
  `PASS`/`SKIPPED` to `BLOCKED` (reusing the existing BLOCKED semantics), and a new "Missing Required
  Journeys" section documents the gap. Added a `--required J-01,J-03,...` CLI flag and wired
  `lib/replay-lane.sh::replay_lane_merge_results` to pass the iteration's `REQUIRED_JOURNEYS`. Also
  extended `goal_gate.py::cmd_results` (headline-only BLOCKED detection — the existing cell-scan alone
  cannot see a missing-row case) and `closure_gate.py`'s ui-test-results check (a new `elif file_top_
  verdict(...) == "BLOCKED"` branch) so both the achievement gate and phase-closure gate treat this
  correctly — TC-3 explicitly named both.
- **A4 — `BLOCKED` verdict enum + grep sites.** Added `BLOCKED` to
  `verdicts.py::BrowserQAVerdict` (previously PASS/FAIL/SKIPPED only — this fixes `artifact_schemas.py`'s
  shape validation, which previously treated a BLOCKED headline as malformed). Widened all four
  `goal-iter-lean.sh` `grep -oE 'PASS|FAIL|SKIPPED'` sites to also match `BLOCKED`.

### B. `_BarCache.prefill`'s resident accumulator (B5/B6)

- Added `_SymbolColumns` (a `collections.abc.Sequence`-conformant columnar store: `array.array('d')` per
  numeric field, synthesizing real `Bar` NamedTuples via `__getitem__`) beside `_BarCache` in
  `prices.py`. `prefill()`'s eager whole-table scan now builds one `_SymbolColumns` per symbol instead of
  a `list[Bar]`; nothing else in the class changed (`bars_asof`/`bars_asof_window`/`bars_after`/
  `close_on` read it through the exact same slicing/indexing code they already used).
- **Measured, live basis:** OLD (`list[Bar]`) VmPeak 1,371,032 kB vs NEW (`_SymbolColumns`) VmPeak
  664,580 kB — a 51.5% reduction (52.1% on VmHWM/peak RSS). See `reports/perf-budgets.md`'s Iteration 41
  section for the full table and the benchmark script
  (`runs/goal-ops-hardening-iter-41/bar-cache-prefill-bench/measure_prefill_peak.py`).
- Added `test_bar_cache.py::test_prefill_old_vs_new_implementation_byte_identical` (TC-6): the same
  fixture run through a test-only reimplementation of the pre-iter-41 body and the shipped
  `_BarCache.prefill` produce byte-identical `Bar` values.

### C. Diagnostics (ride-along, C7/C8)

- **C7.** `main.py` now arms `faulthandler.register(signal.SIGUSR1, all_threads=True)` when
  `TRENDORA_DIAG_FAULTHANDLER_SIGUSR1=1` is set (opt-in, default-off, never touching the byte-frozen
  launch scripts — the env var is inherited by `scripts/start-backend.sh`'s child process like any other).
  Re-ran the throwaway-DB wedge drill once with it armed: **the freeze did NOT recur** — job finished
  `status: ok` with all 8 aggregates refreshed (including `coverage`, which iter-40's own run could not
  get), zero MemoryError/exception in this run's log window, `VmPeak` 2,446,836 kB (~9.8% below the
  2650 MB cap, more margin than iter-40's run 2 which hit the cap exactly). `SIGUSR1` was never sent
  (nothing to diagnose) — an honest non-recurrence, not a claimed fix. Full detail:
  `runs/goal-ops-hardening-iter-41/wedge-drill/README.md`.
- **C8.** Extended `wedge-drill/monitor.py` to keep polling at the same 1 Hz interval for a fixed 30 s
  window PAST the job's first terminal `job_status` reading (closes audit finding B2 — iter-39's wedge
  appeared in exactly the window iter-40's own monitor stopped covering). This run: 28 additional
  post-terminal polls, all `health=200`, `job_status` staying `ok` throughout.

### D. Small, already-specified (D9)

- Added a count-based floor (`_RUN_RECORD_CHECKPOINT_DATE_FLOOR = 5`) to `_checkpoint_run_record`'s
  existing 1.0 s time-based throttle (`data_manager.py`): a new `JobProgress._dates_since_checkpoint`
  counter (unserialized scratch, mirroring the existing `_last_checkpoint_monotonic` field) forces a
  write on every 5th call regardless of elapsed time. Same `message` field, same `_run_detail()`
  serializer, no new persisted field.

## Plan gap found (disclosed, not silently expanded)

The plan's file list named only `incredible_auto_dev/agents/ui-test-designer/body.md` for A2. During
implementation I traced the actual dispatch path and found THREE shell-level gates
(`run-phase.sh` Steps 5/6, `ui-test-design-phase.sh`, `browser-qa-phase.sh`) that unconditionally
short-circuit to N/A stubs whenever `Frontend Present: no`, regardless of required-still-passing
journeys — meaning the agent-level A2 fix would never actually run for a backend-only iteration like
this one, and TC-1/TC-4 (which require a REAL `UT-J-XX`-populated test plan and fresh browser-qa
evidence) would be unreachable. I fixed all three gates (see A1 companion fix above) because the DoD
cannot be met otherwise. This is a bigger diff than the plan's file list stated; flagging it explicitly
for review rather than letting it pass silently.

## Files Changed

- `incredible_auto_dev/scripts/automation/lib/common.sh` -- `resolve_backend_health_url()` +
  `phase_spec_has_required_regression()` helpers.
- `incredible_auto_dev/scripts/automation/browser-qa-phase.sh` -- health-URL fix; backend-only gate
  carve-out for required-still-passing journeys.
- `incredible_auto_dev/scripts/automation/goal-iter-lean.sh` -- health-URL fix; four `grep -oE` sites
  widened to match `BLOCKED`.
- `incredible_auto_dev/scripts/automation/qa-phase.sh` -- health-URL fix.
- `incredible_auto_dev/scripts/automation/demo-phase.sh` -- health-URL fix.
- `incredible_auto_dev/scripts/automation/run-phase.sh` -- health-URL fix; Step 5/6 gate carve-out.
- `incredible_auto_dev/scripts/automation/ui-test-design-phase.sh` -- backend-only gate carve-out +
  dispatch-prompt note.
- `incredible_auto_dev/agents/ui-test-designer/body.md` -- neutral source: Backend-only phase handling
  rewrite.
- `incredible_auto_dev/.claude/agents/ui-test-designer.md` -- re-rendered mirror (via
  `sync-cli-assets.py`, not hand-edited).
- `incredible_auto_dev/scripts/automation/lib/merge_ui_test_results.py` -- `missing_required_journeys()`,
  `merge()` extended with `required_journeys`, `--required` CLI flag, new self-tests.
- `incredible_auto_dev/scripts/automation/lib/replay-lane.sh` -- `replay_lane_merge_results` passes
  `REQUIRED_JOURNEYS` through to the merger.
- `incredible_auto_dev/scripts/automation/lib/goal_gate.py` -- `cmd_results` headline-BLOCKED detection
  (`_UI_HEADLINE_RE`); self-test case added.
- `incredible_auto_dev/scripts/automation/lib/closure_gate.py` -- ui-test-results check extended with a
  headline-BLOCKED branch; self-test case added.
- `incredible_auto_dev/scripts/automation/lib/verdicts.py` -- `BLOCKED` added to `BrowserQAVerdict`.
- `apps/backend/app/engine/prices.py` -- `_SymbolColumns` columnar accumulator; `_BarCache.prefill`
  rewired to use it.
- `apps/backend/app/engine/data_manager.py` -- `_RUN_RECORD_CHECKPOINT_DATE_FLOOR`,
  `JobProgress._dates_since_checkpoint`, `_checkpoint_run_record` count-based floor.
- `apps/backend/main.py` -- `TRENDORA_DIAG_FAULTHANDLER_SIGUSR1` opt-in SIGUSR1 faulthandler arm.
- `apps/backend/tests/test_bar_cache.py` -- TC-6 old-vs-new byte-identity test.
- `apps/backend/tests/test_data_manager.py` -- TC-8 count-based-floor tests (+ companion time-vs-count
  test).
- `apps/backend/tests/test_faulthandler_sigusr1_diagnostic.py` -- new: subprocess-isolated proof the
  SIGUSR1 diagnostic is armed only when the env var is set.
- `incredible_auto_dev/tests/automation/test-health-url-resolution.sh` -- new (A1, TC-2).
- `incredible_auto_dev/tests/automation/test-backend-only-regression-gate.sh` -- new (A1 companion,
  TC-1/TC-4).
- `incredible_auto_dev/tests/automation/test-blocked-verdict-grep-sites.sh` -- new (A4, TC-9).
- `runs/goal-ops-hardening-iter-41/wedge-drill/` -- `config.scratch.yaml`, `seed_throwaway_db.py`
  (copied from iter-40), `monitor.py` (extended, C8), `README.md`, live run evidence (`run1-monitor.csv`,
  `run1-monitor.out`, `trigger-response.json`).
- `runs/goal-ops-hardening-iter-41/bar-cache-prefill-bench/measure_prefill_peak.py` -- new (B6
  measurement script).
- `reports/perf-budgets.md` -- new "Iteration 41" section.

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/test_bar_cache.py -v`
Result: **17 passed** (all pre-existing tests unmodified in behavior + 1 new TC-6 test), including the
two live-DB seed-fixture tests (`test_kdate_backfill_loads_each_symbol_at_most_once`,
`test_cached_snapshot_equals_uncached_row_level`, `test_bootstrap_snapshots_equal_with_cache` — ~96 s).

Command: `cd apps/backend && .venv/bin/python -m pytest tests/test_backfill_coverage_shared_cache.py -v`
Result: **3 passed** (~136 s) -- includes the cache-poisoning/mutation test
(`test_shared_cache_mutation_caught_as_failure`), which directly exercises `_by_symbol` reassignment to a
plain list mid-flight; confirms `_SymbolColumns` duck-types correctly.

Command: `cd apps/backend && .venv/bin/python -m pytest tests/test_membership_timeline_batch_bound.py -v`
Result: **4 passed** (~564 s, live-DB reference-vs-shipped comparison) -- includes
`test_peak_memory_reduced_vs_pinned_reference_on_live_seed`, which independently confirms a real
tracemalloc peak reduction through the SAME `prefill()` call this iteration changed.

Command: `cd apps/backend && .venv/bin/python -m pytest tests/test_warmup.py::test_warmup_loads_each_symbol_at_most_once_across_cadence_and_forward_returns -v`
Result: **1 passed** (~86 s) -- the analogous load-once-per-job counting proof, unaffected by the storage
change.

Command: `cd apps/backend && .venv/bin/python -m pytest tests/test_data_manager.py -v -k "checkpoint_count or checkpoint_time_based"`
Result: **2 passed** (TC-8 new tests).

Command: `cd apps/backend && .venv/bin/python -m pytest tests/test_data_manager.py::test_checkpoint_cadence_density_and_throttle_control -v`
Result: **1 passed** -- pre-existing iter-40 cadence test unaffected by the D9 count-floor addition.

Command: `cd apps/backend && .venv/bin/python -m pytest tests/test_faulthandler_sigusr1_diagnostic.py -q`
Result: **2 passed** (C7 armed-dump/survival + unarmed-default-disposition). *This file was NOT run before
the first handoff and shipped failing — see Fix Notes below; it now passes, re-confirmed 3/3 consecutive
runs plus once more alongside the other changed files.*

Command: `cd apps/backend && .venv/bin/python -m pytest tests/test_data_manager.py -q` (full file)
Result: **144 passed in 373.00s (0:06:12)** -- confirms the D9 count-based-floor addition and every
other change in this file's own scope regress-clean across the whole file, not just the targeted subset.

Command: `python3 incredible_auto_dev/scripts/automation/lib/merge_ui_test_results.py self-test`
Result: **20 passed, 0 failed** (14 pre-existing + 6 new: missing-required-journey detection, CLI
`--required` flag).

Command: `python3 incredible_auto_dev/scripts/automation/lib/goal_gate.py self-test`
Result: **passed** (includes the new headline-only-BLOCKED case).

Command: `python3 incredible_auto_dev/scripts/automation/lib/closure_gate.py self-test`
Result: **10 passed, 0 failed** (9 pre-existing + 1 new).

Command: `python3 incredible_auto_dev/scripts/automation/lib/artifact_schemas.py self-test`
Result: **passed** (BLOCKED now a recognized `BrowserQAVerdict` member).

Command: `python3 incredible_auto_dev/scripts/automation/lib/lint_contracts.py self-test`
Result: **passed**, "current tree lint -> clean OK" (repo-wide contract lint over all changed agent/
verdict files).

Command: `bash incredible_auto_dev/tests/automation/test-replay-lane.sh`
Result: **65 passed, 0 failed** (confirms the `--required` wiring and health-URL fix didn't regress the
replay-lane integration suite).

Command: `bash incredible_auto_dev/tests/automation/test-closure-gate.sh`
Result: **18 passed, 0 failed**.

Command: `bash incredible_auto_dev/tests/automation/test-zero-change-guard.sh`
Result: **13 passed, 0 failed**.

Command: `bash incredible_auto_dev/tests/automation/test-goal-context-slice.sh`
Result: **26 passed, 0 failed**.

Command: `bash incredible_auto_dev/tests/automation/test-iter-budget.sh`
Result: **33 passed, 0 failed**.

Command: `bash incredible_auto_dev/tests/automation/test-doc-drift.sh`
Result: **65 passed, 1 failed** -- the 1 failure (`anti-patterns tree: entry files missing an index row:
27 28`) is PRE-EXISTING, unrelated to this iteration's changes (confirmed via `git status` -- zero
modifications under `incredible_auto_dev/.claude/anti-patterns/` from this session).

Command: `bash incredible_auto_dev/tests/automation/test-health-url-resolution.sh` (new)
Result: **12 passed, 0 failed**.

Command: `bash incredible_auto_dev/tests/automation/test-backend-only-regression-gate.sh` (new)
Result: **6 passed, 0 failed**.

Command: `bash incredible_auto_dev/tests/automation/test-blocked-verdict-grep-sites.sh` (new)
Result: **4 passed, 0 failed**.

**Not run this session:** the full `apps/backend/tests/` suite (per prior iterations' own note, this is
~10-11 h on the 30-year basis and is the reviewer/QA's job to run, not the developer's per pump/dev
guidance) and `test_warmup.py`'s other tests beyond the one directly relevant to this change (time
budget; the one run is the mechanically-identical analog of the already-verified
`test_kdate_backfill_loads_each_symbol_at_most_once`).

## Live drill / diagnostic verification (pre-handoff checklist)

- **Service startup:** `scripts/start-backend.sh` launched cleanly against the throwaway drill DB with
  `TRENDORA_DIAG_FAULTHANDLER_SIGUSR1=1` and the 2650 MB tightened cap; log shows the diagnostic-armed
  line, host-guard banner, and a full clean boot (89/89 warmup, membership-timeline + coverage snapshot
  both warmed). Backend was stopped cleanly after the drill (`kill -TERM`, confirmed process gone, port
  18270 confirmed free, no stray `uvicorn`/`monitor.py` processes left running).
- **External integration:** N/A -- no new external adapters this iteration (AG-9: offline-only).
- **Native dependency binaries:** N/A -- no new dependencies added (`faulthandler`, `array`,
  `collections.abc` are all stdlib).

## Known Issues

- **`test_warmup.py`'s OTHER tests** (beyond the one directly analogous to the `_BarCache.prefill`
  load-once proof) were not re-run this session, for time-budget reasons -- their own `_by_symbol` usage
  (where present) is membership/key-only (`in`, `set()`, `len()`), which is structurally unaffected by
  the `_SymbolColumns` value-type change (verified by direct code inspection, not just assumed).
- **The C7 diagnostic earned no positive evidence** (the freeze did not recur, so `SIGUSR1` was never
  actually sent/exercised) -- this is an honest, expected TC-5 outcome, not a gap, but flagging so it is
  not mistaken for "the freeze is fixed." iter-39/u's original run-1 freeze remains formally unreproduced
  and undiagnosed.
- **The two owner-decision items carried forward unplanned** (iter-34/j's `/api/health` ≤0.1 s budget,
  iter-33/i's `start-frontend.sh` host-guard membership) remain open, exactly as the phase spec's own OUT
  OF SCOPE section states -- not touched this iteration.
- **iter-33/g Regime Lab's cold `view=pooled` dispatch** deferred again, per spec.
- **The A1 companion fix (shell-gate carve-outs) is a bigger diff than the plan's own file list named**
  -- see "Plan gap found" above. Reviewer should specifically check `run-phase.sh`'s Step 5/6 gating,
  `ui-test-design-phase.sh`, and `browser-qa-phase.sh`'s own early-exit conditions for correctness, since
  this is the load-bearing fix that makes A2/A3/A4 actually reachable for this and future backend-only
  goal-mode iterations.

## Fix Notes (attempt 2 — review FAIL remediation)

Review report: `reports/reviews/goal-ops-hardening-iter-41-review.md` (verdict FAIL, 1 CRITICAL issue).

### CRITICAL — `test_faulthandler_sigusr1_diagnostic.py:77` shipped deterministically failing

**Reproduced before fixing** (`pytest tests/test_faulthandler_sigusr1_diagnostic.py -v`), and the
reviewer's diagnosis was exactly right. Captured stderr from the signalled subprocess:

```
'Current thread 0x00007d92285a4780 (most recent call first):\n  File "<string>", line 1 in <module>\n'
```

The drill subprocess is single-threaded, so `faulthandler`'s `all_threads=True` dump emits only the
**"Current thread 0x..."** header — lowercase `thread`. The assertion required a capitalized `"Thread"`,
which `faulthandler` uses only for the *non-signalled* threads of a multi-threaded process. So the
assertion could never pass in this test's own single-threaded setup.

**Fix** (`apps/backend/tests/test_faulthandler_sigusr1_diagnostic.py`, the only file touched in this
attempt): replaced the bare substring check with an anchored, case-insensitive thread-id-line regex that
accepts BOTH header forms, plus a real stack-frame check:

```python
_THREAD_ID_LINE_RE = re.compile(r"^(?:Current )?thread 0x[0-9a-f]+ ", re.IGNORECASE | re.MULTILINE)
...
assert _THREAD_ID_LINE_RE.search(stderr) and 'File "' in stderr, ...
```

The check was deliberately kept strict rather than merely loosened — `^` + `MULTILINE` anchors it to a
real dump header, so it still fails on an empty dump and on incidental mid-line prose containing the word
"thread". Verified against four inputs directly: the observed single-thread output → match; a synthetic
multi-thread dump (`Thread 0x...` + `Current thread 0x...`) → match; no dump at all → no match; mid-line
prose mentioning `thread 0x...` → no match. Assertion semantics are therefore unchanged for the property
the test exists to prove; only the format signature was corrected.

`main.py`'s C7 arming logic was NOT touched — the reviewer confirmed it was never in question (the
companion unarmed-default-disposition test passed all along), and the observed dump proves the arm works.

**Verification after fix** (all re-run under this attempt, per the review's `fix_tasks` instruction):

| Command | Result |
|---|---|
| `pytest tests/test_faulthandler_sigusr1_diagnostic.py -q` (×3 consecutive) | **2 passed** each run (3/3) |
| `pytest tests/test_bar_cache.py -q` | **17 passed** (94.05 s) |
| `pytest tests/test_data_manager.py -q -k "checkpoint"` | **4 passed**, 140 deselected |
| `pytest tests/test_faulthandler_sigusr1_diagnostic.py -q` (final, alongside the above) | **2 passed** |

### Process note (the honest part)

The root cause was not the regex — it was that this test file was written and handed off without ever
being executed, while the handoff's "Tests Run" section listed twenty other commands, which made the
omission invisible. That is precisely the failure mode this iteration exists to close, reproduced by the
dev agent inside the very same diff. No compensating mechanism was added for it here (that would be
unrequested scope); recording it plainly so the auditor can weigh whether a handoff-vs-diff test-coverage
cross-check belongs in a future iteration.

**No other files were changed in this attempt.** No new problems were found while fixing.
