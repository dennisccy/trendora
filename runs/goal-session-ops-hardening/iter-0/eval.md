# Iteration 0 Evaluation

**Verdict:** CONTINUE
**Depth Recommendation For Next Iteration:** full

## Summary

Baseline verify-only iteration: all five Must-have journeys (J-01, J-03, J-04, J-05, J-06)
were exercised live against the unchanged codebase and none passes yet — the intended,
honest outcome of a starting-line measurement (browser-QA verdict FAIL is a measurement, not
an incident). Zero product changes were made (`git diff apps/ config.yaml` empty; scan-report
CLEAN), so no anti-goal was introduced. The session has a clear, tractable build path — this
is a CONTINUE, not a stall.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 Backfill honors range / explains zero-work | (new) | failing | reports/qa/goal-ops-hardening-iter-0-evidence/J-01-may-backfill-zero-dates.png ; J-01-J-05-data-page-fullpage.png |
| J-03 No per-run range cap | (new) | failing | reports/qa/goal-ops-hardening-iter-0-evidence/J-03-submit-attempt.png |
| J-04 Non-blocking boot with visible status | (new) | partial | reports/qa/goal-ops-hardening-iter-0-evidence/J-04-badge-unavailable-crash.png ; J-04-badge-initializing.png ; J-04-midflight-job-interrupted.png |
| J-05 Aggregates precomputed at ingest | (new) | failing | reports/qa/goal-ops-hardening-iter-0-evidence/J-05-single-day-backfill-zero.png |
| J-06 Pages load only what they need | (new) | failing | reports/qa/goal-ops-hardening-iter-0-evidence/J-06-backtest-still-loading.png |

**Evidence notes (per changed journey — all five newly seen this baseline):**
- **J-01 failing** — live May 2026-05-02→05-29 backfill returned `dates_total=0` / 0 snapshots
  (`_cadence_allowed_dates` still filters explicit requests; every May date precedes
  `snapshot_cadence.daily_start: 2026-06-01`); `/scanner-runs` gained no new dates; weekend-only
  and re-run showed identical generic "0 snapshots over 0 dates" with no per-reason breakdown;
  the live "Job progress" panel reset to the literally-forbidden "No job has been started this
  session." on reload; the persisted Run-history table shows every zero-work AND productive run
  with the same `ok` badge (no visual distinction). Root cause source-confirmed, not UI-only.
- **J-03 failing** — live submission of a 412-calendar-day span returned the forbidden inline
  error "date range too large: 412 days exceeds the configured maximum 370"; `max_range_days: 370`
  and its `validate_job_request` enforcement + three pinning tests unchanged.
- **J-04 partial** — 5 of 6 numbered steps reproduced live: first `/api/health` 200 at 0.909s/1.05s
  (≤5s), phase-aware "Initializing… history 89/89" badge during a real ~13s pre-ready window
  (DOM-asserted), distinct red "Backend unavailable"/"NO-GO" crash presentation (screenshot
  confirms), and a mid-flight job returning `status=interrupted` after restart. The ONE confirmed
  miss (step 5): `scripts/start-backend.sh` writes no persistent logfile and enforces no
  `ulimit`/`MALLOC_ARENA_MAX` (confirmed by source read + `/proc/<pid>/environ`). Genuinely
  partial — the distinct-states/timing/interrupted-job half already works (mcp-loop iter-28/33
  legacy); only the logfile + memory-cap-enforcement layer is unbuilt.
- **J-05 failing** — the suggested single-day backfill (2026-05-15) hits the SAME cadence-gate bug
  as J-01 (`dates_total=0`, cannot ingest); no `_do_backfill` finalize hook refreshes any named
  aggregate (source-confirmed); a cold restart + `GET /api/data` measured 10.055s with RSS climbing
  646MB→1.75GB (the whole-table bar-prefill signature). Only the peripheral step-4 check
  (`/api/health` stayed responsive, 32/32 polls, during heavy ingest) passed.
- **J-06 failing** — 8/11 pages fast and healthy, but those are pre-existing mcp-loop behavior; the
  3 pages J-06 targets (`/data`, `/evidence`, `/backtest`) measured 13.3s/17.7s/14.5s after a
  backfill (5-12x over ≤1.5s/≤3s budgets, same coverage-cache-fragility root cause as J-05), and
  the two new required budget rows (boot time, current-basis cold `/api/data`) plus the code-audit
  statement are absent from `reports/perf-budgets.md`. None of J-06's own new deliverables exist.

## Anti-goal Check

Verify-only iteration: `git diff <snapshot>..HEAD -- apps/ config.yaml` is empty, `iter-diff.md`
= "(no changes)", scan-report = CLEAN. Nothing was added, so no anti-goal was introduced.

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| AG-1 proven-language needs ledger backing | OK | No code changed; no new proven-language introduced |
| AG-2 decision-quality only (no return promises/orders) | OK | No changes |
| AG-3 displayed numbers correct | OK | Verify-only; failing states observed are honest (dates_total=0 is the real bug, not fabricated) |
| AG-4 no overfit edges | OK | No changes |
| AG-5 determinism / no-lookahead | OK | No changes |
| AG-6 no ship w/ unbacked evidence-claims | OK | Iteration carries no Evidence Claims (pure ops baseline); referee gate auto-passes |
| AG-7 no hard-coded credentials | OK | scan-report CLEAN, empty diff |
| AG-8 no unbounded whole-table loads | OK (not introduced) | The pre-existing `compute_coverage` full-pool prefill (goal.md "Ground truth" offender #1; QA measured 10s/1.75GB) is NOT a this-iteration violation — it is the documented target J-05/J-06 will retire, already tracked via those failing journeys |
| AG-9 offline-deterministic ingest | OK | QA's backfill/fetch jobs were all offline seed/fixture-backed, no live network; no new deps |

## Next-Step Recommendation

Start real feature work with the **data-jobs cluster (J-01 + J-03)** per goal.md's suggested
build order — it unblocks the owner's immediate backfill need. The **load-bearing change is
J-01's "requested range always wins"**: `_do_backfill` must stop applying `_cadence_allowed_dates`
to explicit backfill requests (the cadence gate is a warm-up-density control only). This single
fix is the root cause of BOTH J-01's `dates_total=0` and J-05's un-ingestable single-day date, so
it must land before J-05 can be exercised. Pair it with the `data_provider_runs` schema extension
(per-date exclusion reasons + the pinned run-summary contract: non-trading + `dates_total` =
calendar days; `snapshots_created` + already-snapshotted + error-other = `dates_total`), the
zero-work explanatory UI state (visually distinct from success), a job-progress surface that
survives reload (never "No job has been started this session"), and J-03's `max_range_days`
removal (config + validation + the four pinning tests). Defer the J-05/J-06 ingest-finalize +
lazy-loading cluster and the J-04 logfile/memory-cap layer to subsequent iterations.

**Depth = full:** this iteration first lands user-visible UI (J-01's honest zero-work / persisted
job-history surface) AND a data-model change (`data_provider_runs` exclusion fields), triggering
goal.md's "full when an iteration first lands user-visible UI changes" rule; the schema + cadence
blast radius warrants the audit/ux-regression/closure lanes.

## Halt Justification (if halting)

Not halting — verdict is CONTINUE. All five journeys fail as a starting-line measurement, none
regressed (first evaluation, no prior passing state), no anti-goal was introduced, and every gap
is "surface not yet implemented" — buildable offline against the committed seed (AG-9). Clear
productive next work exists (data-jobs cluster), so this is neither STALLED nor GOAL_ACHIEVED.
