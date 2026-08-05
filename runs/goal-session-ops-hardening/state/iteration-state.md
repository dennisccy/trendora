# Iteration State — ops-hardening

**After iteration:** 49 · **Date:** 2026-08-05 · **Verdict:** ESCALATE

## Journeys

4 passing (J-01 J-03 J-08 J-09) · 3 partial (J-04, J-05 — up from failing, J-06) · 1 failing (J-07 — the service actually went DOWN this round) — 8 total. J-01/J-03 rest on `data_provider_runs` 309/310/311, created by the replay itself at 04:40-04:41Z.

## Active blockers

- **The backend DIED for 12m45s during this round's own lane** (`logs/backend.log:191719-191721`, restart 09:48:49Z). Owner: dev. Two halves, must land as ONE change: `research.py:1051` (`compute_factor_lab_all`, unbounded `sorted(obs,…)`, uncaught `MemoryError`, untouched 5 rounds = audit B1) + `warmup.py:198` (`_warm_drawdown_expectations`, no `phases` memoization, no interlock with the ingest loop = audit B2, proven live by its own traceback). J-07's only remaining blocker and the next round's primary scope.
- **Three journeys have ZERO executed lane rows** (J-04, J-08, J-09 — all SKIP, app was down). Run the 8-journey lane LAST and change no code after it: 4th consecutive breach (lane 10:46 vs product-code mtime 12:34:46).
- **`reports/qa/…-iter-49-qa.md` reads PASS while the same phase's browser lane reads FAIL** and never cites it — regenerate, do not edit. **No owner blockers.** Ledger: 85 total, 35 unresolved, **0 unresolved critical**. scan CLEAN, coherence COHERENCE-PASS.

## Last 2 verdicts

- iter 49: ESCALATE — the 1,200s termination bound is genuinely met 3/3 on idle-host drills, but the service went down under ordinary concurrent use and J-07 dropped to `failing`.
- iter 48: ESCALATE — J-01/J-03 promoted on real replay-caused job rows; J-05 failed a 5th round on two unbounded finalize-tail phases (this round's scope, now closed).

## Do not redo

- **Both finalize-tail phases are BOUNDED and proven** — TC-1 met 3/3 (1,012-1,048s vs 1,200s), VmPeak 45-49% margin, live in-app `forward_aggregates_warm elapsed=168.15s` (was 1,334s). `reports/perf-budgets.md` Addenda 4-6.
- **Per-horizon/per-claim sub-phase timing EXISTS and is regression-guarded** — `data_manager.py:3978-4013`/`:4105-4199`, `test_data_manager.py:2070` (mutation-proven).
- **J-04's boot + crash/restart halves have REAL executed rows** — `tests/test_start_backend_script.py::test_j04_*`, re-run after the final build.
- **J-05's golden is already rotated to `2012-01-04`** (0 snapshot rows, 480 symbols with bars, verified in the DB). Never re-target 2012-01-05 — this round's lane consumed it.
- **AG-10 values frozen, verified untouched** (`config.yaml` 8192/2) — bound the page, never raise the cap. Gap-insert reuse branch (`data_manager.py:891-917`) correct; leave byte-for-byte alone.
- **Evidence capture is never an iteration goal** — J-07's walkthrough (19 rounds), J-05's frames and this round's 5 blank/copied screenshots ride the showcase / `Depth: evidence` lane.
