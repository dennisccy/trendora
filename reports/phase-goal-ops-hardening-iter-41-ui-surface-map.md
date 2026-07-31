# Phase goal-ops-hardening-iter-41 — UI Surface Map

**Phase:** goal-ops-hardening-iter-41
**Date:** 2026-07-31
**Written by:** ui-impact-analyst

---

## Affected UI Surfaces

No file under `apps/frontend/` changed this iteration (`Frontend Present: no`, confirmed against the dev
handoff's "Files Changed" list). The rows below are **not new or modified surfaces** — they are the
EXISTING surfaces that this iteration's own verification-lane repair (item A in the plan) now makes it
possible to actually re-check. Before this iteration, a backend-only spec with `Frontend Present: no`
caused these surfaces to be skipped entirely by the automated pipeline even when required-still-passing
journeys named them; that gate is what the dev handoff's "Plan gap found" section fixed. "Change Type" is
therefore "Regression check only" throughout — every row exists to verify nothing broke, not to show
something new.

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/data` | "Start a fetch / backfill job" panel — `job-start-date` / `job-end-date` inputs, "Job kind" select, "Start" button | Regression check only — no code change | J-01 (backfill honors the requested range) and J-03 (no per-run range cap) must get fresh, non-carried-forward verification this iteration | Submit start `2026-05-02`, end `2026-05-29`, kind "Backfill snapshots"; click "Start"; verify the job's summary reports `dates_total = 19` (or an explicit zero-work explanation if already run) |
| `/data` | "Job progress" panel (`data-testid="job-status"`, `job-live-activity`, `job-heartbeat`) | Regression check only — no code change | J-01 requires live progress to be watchable to completion; J-03 requires progress to continue across chunks for a >370-day request | Watch the panel from job start to a terminal status; verify it never freezes on "running" with no heartbeat movement |
| `/data` | "Run history" table (`PanelTitle` "Run history") | Regression check only — no code change | J-01 step 7 requires persisted job history to survive a page reload — "never no job started this session" | Reload `/data` (F5) after a job completes; verify the same run row (kind, range, status, snapshot count) is still listed |
| `/scanner-runs` | Scanner Runs list | Regression check only — no code change | J-01 step 4 requires newly backfilled dates to appear here | After the May backfill completes, navigate to `/scanner-runs`; verify rows exist for `2026-05-04`, `2026-05-15`, `2026-05-29` |
| `/scanner-runs/[runId]` | Scanner Run detail (leaderboard table) | Regression check only — no code change | J-01 step 4 requires the opened run's leaderboard to render the stored snapshot, not an error/empty state | Click the `2026-05-29` row; verify the detail page shows a populated leaderboard table, not the "No stored stock rows" empty state |
| `/data` | "Start a fetch / backfill job" panel (wide-range request) | Regression check only — no code change | J-03 requires a >370-calendar-day span to be accepted, not rejected with a range-cap error | Submit start `2025-06-01`, end `2026-07-17` (411 days); verify no "date range too large" error appears and the job begins running in chunks |
| Global (any page) | Top-bar readiness badge (`data-testid="readiness-badge"`) | Regression check only — no code change | J-04 requires the badge to show honest initializing/ready/unavailable states across a backend restart and a simulated crash | Restart the backend; watch the badge move through `data-state="initializing"` (or `loading`) to `data-state="ready"` with text "Ready" — never a blank header |
| Global (any page) | Preflight banner (`preflight-banner.tsx`) | Regression check only — no code change | J-04 requires an explicit crashed/unreachable presentation, visibly distinct from initializing | Kill the backend process; verify the banner reads "Backend is unavailable — the preflight check could not run." |
| `/`, `/stocks`, `/stocks/AAPL`, `/sectors`, `/themes`, `/data`, `/evidence`, `/scanner-runs`, `/backtest`, `/watchlist`, `/research/event-study` | Page load / on-load API calls | Regression check only — no code change | J-06 requires every page's load time and API latencies to stay within `reports/perf-budgets.md`'s committed budgets this iteration | Load each URL once; verify none exceeds its budget row in `reports/perf-budgets.md` and no page shows an indefinite skeleton |
| `/backtest` | Evidence panel — `data-testid="evidence-refreshing"` banner ("Refreshing — showing the last complete evidence") and `title="Backtest evidence not yet computed"` empty state | Regression check only — no code change | J-08 requires `/backtest` to keep serving last-good stored evidence during a warm, never a cold recompute | While a backfill's finalize warm is in flight, load `/backtest`; verify it shows the previous version's values plus the "Refreshing…" banner, not a blank/frozen frame |
| `/data` | "Background compute" panel (`data-testid="background-compute-panel"`, states `background-compute-idle` / `background-compute-unknown`) | Regression check only — no code change | J-09 requires `/data` to disclose in-flight background-compute windows from the same readiness poll | Trigger a background-compute window (load `/backtest` for an under-computed as-of); verify the panel lists the window with elapsed time and horizons done/total instead of "No background compute running." |
| Global (any page) | Top-bar badge background-compute chip (`data-testid="background-compute-indicator"`, text "background compute running (N)") | Regression check only — no code change | J-09 requires the badge to disclose background compute alongside "Ready", never hide it | During the same background-compute window, verify the badge shows "Ready" plus the "background compute running (1)" chip |

<!-- Change Type is uniformly "Regression check only" because Frontend Present: no and no frontend file
     changed. Rows exist because this iteration's own fix (browser-qa-phase.sh / run-phase.sh / 
     ui-test-design-phase.sh gate carve-outs) is what makes these regression checks reachable at all this
     iteration — see dev handoff "Plan gap found." -->

---

## Backend-Only Changes (No UI Impact)

- `apps/backend/app/engine/prices.py` — `_SymbolColumns` columnar accumulator inside `_BarCache.prefill`
  (~52% resident-memory reduction on the live basis) — byte-identical output proven by a fixture test; no
  UI surface affected.
- `apps/backend/app/engine/data_manager.py` — `_RUN_RECORD_CHECKPOINT_DATE_FLOOR` count-based floor on
  `_checkpoint_run_record`, plus the new unserialized `JobProgress._dates_since_checkpoint` scratch field
  — same persisted `message` field/serializer, no new field, no UI surface affected.
- `apps/backend/main.py` — `TRENDORA_DIAG_FAULTHANDLER_SIGUSR1` opt-in diagnostic env var (arms
  `faulthandler.register(SIGUSR1, ...)`) — ops/CLI-only, default off, no UI surface affected.
- `apps/backend/tests/test_bar_cache.py`, `test_data_manager.py`,
  `test_faulthandler_sigusr1_diagnostic.py` — test-only files, no UI surface.
- `runs/goal-ops-hardening-iter-41/wedge-drill/*`,
  `runs/goal-ops-hardening-iter-41/bar-cache-prefill-bench/measure_prefill_peak.py` — one-off diagnostic
  drill config and benchmark script plus their evidence output, no UI surface.
- `reports/perf-budgets.md` — new "Iteration 41" measurement section (developer-facing report, not a
  served UI surface itself, though J-06's regression check above cross-references its budget numbers).
- `incredible_auto_dev/scripts/automation/{browser-qa-phase.sh, goal-iter-lean.sh, qa-phase.sh,
  demo-phase.sh, run-phase.sh, ui-test-design-phase.sh, lib/common.sh, lib/merge_ui_test_results.py,
  lib/replay-lane.sh, lib/goal_gate.py, lib/closure_gate.py, lib/verdicts.py}`,
  `incredible_auto_dev/agents/ui-test-designer/body.md`,
  `incredible_auto_dev/.claude/agents/ui-test-designer.md`,
  `incredible_auto_dev/tests/automation/{test-health-url-resolution.sh,
  test-backend-only-regression-gate.sh, test-blocked-verdict-grep-sites.sh}` — this project's own
  AI-development-pipeline tooling, not Trendora product code. There is no Trendora UI surface these files
  could ever affect; they change how future iterations of this framework get automatically verified.

---

## Summary

- **Frontend surfaces changed:** 0
- **New pages/routes:** 0
- **Modified components:** 0
- **Navigation changes:** no
- **Backend-only changes:** 7 groups (`prices.py`, `data_manager.py`, `main.py`, backend tests, drill/bench
  scratch scripts, `perf-budgets.md`, and the `incredible_auto_dev/` pipeline-tooling group)
- **Regression-only surfaces requiring fresh re-verification this iteration:** 12 rows above, spanning
  `/data`, `/scanner-runs`, `/scanner-runs/[runId]`, `/backtest`, the global readiness badge, and the
  preflight banner — covering required-still-passing journeys J-01, J-03, J-04, J-06, J-08, J-09
