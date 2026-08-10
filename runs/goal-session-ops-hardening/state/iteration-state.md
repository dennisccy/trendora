# Iteration State — ops-hardening

**After iteration:** 58 · **Date:** 2026-08-10 · **Verdict:** ESCALATE

## Journeys

6 passing (J-01 J-03 J-04 J-06 J-08 J-09) · 2 partial (J-05 J-07) · 0 failing — 8 total

## Active blockers

- **NEXT ROUND MUST RUN FULL DEPTH (binding — ESCALATE).** Iters 55/56/58 declared `Depth: full`, ran
  `lean`; no audit ran, two false measurement records reached the evaluator unreported. J-05 and J-07 both
  require a `[NEW]` walkthrough and the demo lane runs only at full depth — **neither can close in a lean
  round**. Owner: engine depth selection.
- **J-05 needs ONE thing: a backend restart + cold `/data` check (step 3).** The browser-QA agent may not
  restart the app (its SIGTERM was blocked by the permission classifier); the DEVELOPER lane restarts it
  routinely. Assign to dev, not QA. Owner: dev.
- **J-07: VmPeak hit exactly the 8192 MB `memory_cap_mb`**, warm stalled 1/5 horizons. Never-profiled
  lever: `_regime_lab_members_by_horizon`'s un-chunked `forward_returns` read
  (`apps/backend/app/engine/research.py`) — measure first. Owner: dev. Off-process compute — human, 9 rounds.
- **Drill write-ups contradict their own logs** (3rd round): `j07-health-poll.log` holds 2.097s/2.064s vs a
  claimed 1.18s max; `j05-health-poll.log:114` is a real 3.474s answer written up as a "poll-script restart
  gap". Every drill must publish raw line count + slowest answer + window, as Addendum 24 does. Owner: lanes.

## Last 2 verdicts

- iter 58: ESCALATE — clean, verified product fix (job-aware `stale`, empty-state gate, TC-6 correction),
  but zero journey movement and a lean round hid two false records the audit would have caught.
- iter 57: CONTINUE — J-06 newly passing (first movement in 4 rounds); TC-7 drilled for real, mis-reported.

## Do not redo

- **Availability `stale` gating (B2) DONE** — `availability_from_storage` = stamp mismatch AND
  `_ingest_job_in_flight` (reads `data_provider_runs.status == "running"`, deliberately not `_JOBS`).
- **Empty-state gate (B5) DONE** — `apps/frontend/lib/availability-empty-state.ts`, `cells.length === 0 &&
  !stale`, 4 unit tests; banner copy aligned with the Coverage panel. **`models.py` docstring (B6) DONE.**
- **TC-6 correction DONE** in all three places (perf-budgets Addendum 24, iter-57 dev handoff, iter-57
  `status.json` `corrections`), append-only. **TC-7 re-drill DONE and honest** (967 raw lines, 834 in-window,
  0 non-200, one 2.865s breach disclosed) — re-verified line-by-line; build on it, don't re-run.
- **J-05 golden rotated to 2010-11-05** (0 `scanner_runs` rows); re-verify before use — consumed twice in one
  round. **AG-10 caps verified untouched** (both git checks empty; 8192/2) — never edit them.
