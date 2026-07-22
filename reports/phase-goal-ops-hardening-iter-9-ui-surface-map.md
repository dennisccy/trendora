# Phase goal-ops-hardening-iter-9 — UI Surface Map

**Phase:** goal-ops-hardening-iter-9
**Date:** 2026-07-22
**Written by:** ui-impact-analyst

---

## Affected UI Surfaces

No UI surface's code changed this iteration (zero files under `apps/frontend/` appear in the dev handoff's
"Files Changed" list). The rows below are **re-verification** surfaces only: pre-existing, already-shipped
pages/components that this iteration's `Frontend Present: yes` line requires browser-qa to re-check live,
because they are what J-01/J-03/J-04/J-05's acceptance steps (goal.md, plan.md TESTING REQUIREMENTS) run
against. "Why Changed" therefore names the journey/TC driving the re-check, not a code diff at that surface.

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/data` | `JobForm` / `JobProgressPanel` (`apps/frontend/app/data/page.tsx`) | Re-verification (no code change) | J-01 step 1–3 and J-05 step 1–2 depend on this surface's persisted job status/`aggregates_refreshed` display; iter-8 shipped the underlying `MemoryError`-hardening fix but never browser-checked it (J-05 = `regressed` entering this iteration) | Start a `backfill` job on `/data` for one unsnapshotted historical trading day (e.g. `2026-05-15`); watch `JobProgressPanel` until the job reaches persisted status exactly `"ok"` (not `"partial"`), and confirm the job-history row's `aggregates_refreshed` field lists a non-empty array of categories (TC-1, TC-6) |
| `/data` | `CoveragePanel` (`apps/frontend/app/data/page.tsx`) | Re-verification (no code change) | J-05 step 3 requires cold coverage load with no full `daily_prices` prefill; J-01 step 7 requires the persisted job history to survive reload | Restart the backend (`scripts/start-backend.sh`), then load `/data` cold and confirm `CoveragePanel` renders coverage within the budget recorded in `reports/perf-budgets.md`, with no multi-second stall or spinner hang (TC-4) |
| `/data` | `UnfinishedImportsPanel` (`apps/frontend/app/data/page.tsx`) | Re-verification (no code change) | J-04 step 6 requires a job mid-flight at a simulated backend crash to show an explicit interrupted/error state, never a still-"running" row with no living process | Kill the backend process mid-job (simulated crash), restart it, reload `/data`, and confirm the affected job's row in `UnfinishedImportsPanel` shows an explicit interrupted state with its last persisted progress — not a row still labeled "running" |
| `/scanner-runs` | `ScannerRunsPage` / `RunTableRow` (`apps/frontend/app/scanner-runs/page.tsx`) | Re-verification (no code change) | J-01 step 4 and J-05 step 2(a) require the leaderboard to list the newly-backfilled date with the stored snapshot rendered, no "computing…" placeholder | After the `2026-05-15` backfill (TC-1) completes, open `/scanner-runs`, locate the row for that date, and confirm it renders immediately with no "computing…" placeholder (TC-2) |
| `/scanner-runs/[runId]` | `RunDetailPage` / `RunBody` (`apps/frontend/app/scanner-runs/[runId]/page.tsx`) | Re-verification (no code change) | Same as above — J-01/J-05 require the opened run's leaderboard to match the stored snapshot for that as-of, not a recomputed value | Click into the `2026-05-15` run detail page and confirm the leaderboard table's rows match the stored `scanner_results` record for that date (TC-2) |
| `/` (home) | `MarketPhaseCard` / `PhaseGlanceCard` (`apps/frontend/app/page.tsx`) | Re-verification (no code change) | J-05 step 2(a) requires market phase for the newly-ingested as-of to be served from `market_phase_cache` storage with no live-recompute delay | After the `2026-05-15` backfill (TC-1) completes, load `/` and confirm the Market Phase & Severity card for that as-of renders without a visible compute-on-read delay (no stalled/blank card before data appears) (TC-3) |
| (top bar, all pages) | `HealthBadge` (`apps/frontend/components/health-badge.tsx`) | Re-verification (no code change) | J-04 steps 2–3 (required-still-passing) require the badge to surface boot-phase detail and progress `n/m` during the pre-ready window, never a bare "Backend unavailable" | Restart the backend via `scripts/start-backend.sh`, poll `GET /api/health` at ≤250ms intervals, and in the same window inspect `HealthBadge`'s DOM/screenshot to confirm it shows the same boot-phase detail (`n/m` progress) as the raw health payload during that window (TC-12: boot-to-health timing + pre-ready phase detail) |
| (global, all pages) | `PreflightBanner` / `LoudBanner` (`apps/frontend/components/preflight-banner.tsx`) | Re-verification (no code change) | J-04 step 4 (required-still-passing) requires an explicit crashed/unreachable presentation, visibly distinct from the initializing state, when the health poll fails | Kill the running backend process (simulated crash) and confirm `PreflightBanner` switches to its `LoudBanner` NO-GO/crashed state, visually distinct from the earlier initializing-badge state, within one health-poll interval (TC-12: crash presentation) |

<!-- Change Type here is consistently "Re-verification (no code change)" because this iteration shipped
     zero frontend file changes — see the Backend-Only Changes section below for what actually changed. -->

---

## Backend-Only Changes (No UI Impact)

- `scripts/start-backend.sh` — adds a HOST-GUARD-marked block: when `project-extensions/host-guard/host-guard.env`
  is present and `HOST_GUARD_ENABLED=1`, sources it, wraps the exec'd `uvicorn` process with
  `taskset -c "$HOST_GUARD_CPU_LIST"`, and exports `OMP_NUM_THREADS`/`OPENBLAS_NUM_THREADS`/
  `MKL_NUM_THREADS`/`NUMEXPR_NUM_THREADS` from `HOST_GUARD_BLAS_THREADS` — additive alongside the
  script's pre-existing `ulimit -v`/`MALLOC_ARENA_MAX` enforcement. A launch script, not a UI file — no
  browser-observable output. No UI surface affected.
- `scripts/dev.sh` — applies the identical HOST-GUARD block to the backend subshell only (frontend/`next dev`
  subshell explicitly untouched), plus mirrors `start-backend.sh`'s `ulimit -v`/`MALLOC_ARENA_MAX`
  derivation there. No UI surface affected.
- `apps/backend/app/engine/data_manager.py` — memoizes the libc `CDLL` handle resolved inside
  `_release_process_memory()` (new `_resolve_libc_malloc_trim()` helper, module-level cache); an internal
  memory-cleanup helper with unchanged `gc.collect()`/`malloc_trim` timing and effect per the dev handoff.
  Not called from, or reflected in, any API response shape. No UI surface affected.
- `apps/backend/tests/test_data_manager.py` — 2 new tests proving the libc-handle memoization and a
  cached-failure case. Test-only file. No UI surface affected.
- `apps/backend/tests/test_start_backend_script.py` — tightens the heavy-ingest regression test's
  assertions (status `"ok"` only, `aggregates_refreshed` completeness) and adds 7 new launcher-cap
  verification tests (TC-7/TC-8/TC-9). Test-only file, asserting existing behavior more strictly; does not
  itself alter the production finalize-hook logic `/data`'s job-history panel renders. No UI surface
  affected.

---

## Summary

- **Frontend surfaces changed:** 0
- **New pages/routes:** 0
- **Modified components:** 0
- **Navigation changes:** no
- **Backend-only changes:** 5 (`scripts/start-backend.sh`, `scripts/dev.sh`, `apps/backend/app/engine/data_manager.py`, `apps/backend/tests/test_data_manager.py`, `apps/backend/tests/test_start_backend_script.py`)
- **Re-verification-only surfaces (pre-existing, no code change):** 8 rows above, spanning `/data`, `/scanner-runs`, `/scanner-runs/[runId]`, `/`, the top-bar readiness badge, and the global preflight/crash banner — required by this iteration's `Frontend Present: yes` line to unblock J-01/J-03/J-04/J-05 browser-qa re-verification.
