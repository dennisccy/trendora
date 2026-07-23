# Phase goal-ops-hardening-iter-12 — UI Surface Map

**Phase:** goal-ops-hardening-iter-12
**Date:** 2026-07-22
**Written by:** ui-impact-analyst

---

## Affected UI Surfaces

No UI surface's code changed this iteration — `git status`/`git diff --stat -- apps/backend apps/frontend`
both return empty, and the dev handoff's "Files Changed" list names only `reports/perf-budgets.md`, the dev
handoff itself, the implementation summary, and `runs/goal-ops-hardening-iter-12/status.json`, none of which
are frontend or backend source. The rows below are **re-verification / controlled-measurement** surfaces
only: pre-existing, already-shipped pages/components that this iteration's `Frontend Present: yes` line
requires browser-qa to exercise live, because they are exactly what G2's re-measurement and the
J-01/J-03/J-04/J-05 required-still-passing replay run against (plan.md TESTING REQUIREMENTS, goal.md
acceptance steps). "Why Changed" therefore names the journey/TC driving the check, not a code diff at that
surface.

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/data` | Coverage/`/api/indexes` panel (`apps/frontend/app/data/page.tsx`) | Controlled measurement (no code change) | G2 requires three independent, cache-disabled, fresh-navigation loads of `/data` timing `GET /api/indexes?full=true`, each cross-checked against `logs/backend.log` (no in-flight ingest job) and `logs/hwmon/hwmon.csv` (idle load1/MemAvailable) at that exact timestamp, to give the existing over-budget reading (2066.3ms/2671.8ms) its first genuine like-for-like control | Open a fresh, cache-disabled Chrome tab, navigate to `/data`, and record the elapsed time from navigation start to the `GET /api/indexes?full=true` response completing in the network panel; repeat in two more fresh tabs (never reload the same tab); immediately before/during each load, `grep` `logs/backend.log` for the same timestamp window to confirm no backfill/fetch/rebuild job is in-flight, and read `logs/hwmon/hwmon.csv`'s row nearest that timestamp to confirm load1/MemAvailable sit in the established idle range (TC-2) |
| `/data` | `JobForm` / `JobProgressPanel` (`apps/frontend/app/data/page.tsx`) | Required-still-passing re-verification (no code change) | J-01 requires the persisted job-history panel to still report `dates_total`/`snapshots_created`/exclusion reasons correctly and to survive reload; J-03 requires a >370-day backfill to still be accepted with no range-cap rejection | Submit a backfill on `/data` spanning more than 370 calendar days (e.g. 2025-06-01 → 2026-07-17); confirm the request is accepted (no "date range too large" error), `JobProgressPanel` shows live chunk-by-chunk progress, and reload the page afterward to confirm the job's history row is still listed with the same outcome (TC-5, J-01/J-03 replay) |
| `/data` | `UnfinishedImportsPanel` (`apps/frontend/app/data/page.tsx`) | Required-still-passing re-verification (no code change) | J-04 step 6 requires a job mid-flight at a simulated backend crash to still show an explicit interrupted/error state, never a still-"running" row with no living process | If a backend restart/crash is exercised as part of the J-04 replay, reload `/data` afterward and confirm the row for the job that was mid-flight at kill time shows an explicit interrupted/error state with its last persisted progress, not a row still labeled "running" (TC-6, J-04 replay) |
| `/scanner-runs` and `/scanner-runs/[runId]` | `ScannerRunsPage` / `RunDetailPage` (`apps/frontend/app/scanner-runs/`) | Required-still-passing re-verification (no code change) | J-01 step 4 and J-05 step 2(a) require a backfilled date's leaderboard to render the stored snapshot immediately, with no "computing…" placeholder and no recomputed value | Open `/scanner-runs`, locate a previously-backfilled date's row, confirm it renders immediately with no "computing…" placeholder, then open that run's detail page and confirm the leaderboard rows match the stored `scanner_results` record for that as-of (TC-5/TC-6, J-01/J-05 replay) |
| `/` (home) | `MarketPhaseCard` (`apps/frontend/app/page.tsx`) | Required-still-passing re-verification (no code change) | J-05 step 2(a) requires market phase for the latest ingested as-of to be served from `market_phase_cache` storage with no live-recompute delay | Load `/` and confirm the Market Phase & Severity card for the latest as-of renders without a visible compute-on-read stall (no blank/spinner-frozen card before the phase value appears) (TC-6, J-05 replay) |
| (top bar, all pages) | `HealthBadge` (`apps/frontend/components/health-badge.tsx`) | Required-still-passing re-verification (no code change) | J-04 steps 2–3 require the badge to surface boot-phase detail and progress `n/m` during the pre-ready window, never a bare "Backend unavailable", if a backend restart is exercised as part of this replay | If the J-04 replay restarts the backend, poll `GET /api/health` at ≤250ms intervals from process start and, in that same window, inspect `HealthBadge`'s DOM/screenshot to confirm it shows the same boot-phase detail (`n/m` progress) as the raw health payload (TC-6, J-04 replay) |
| (global, all pages) | `PreflightBanner` (`apps/frontend/components/preflight-banner.tsx`) | Required-still-passing re-verification (no code change) | J-04 step 4 requires an explicit crashed/unreachable presentation, visibly distinct from the initializing state, when the health poll fails, if a simulated crash is exercised as part of this replay | If the J-04 replay simulates a backend crash, confirm `PreflightBanner` switches to its crashed/unreachable NO-GO state, visibly distinct from the earlier initializing-badge state, within one health-poll interval (TC-6, J-04 replay) |

<!-- Change Type here is consistently "no code change" because this iteration shipped zero apps/backend or
     apps/frontend file changes — see the Backend-Only Changes section below for what actually changed
     (a report/documentation artifact only). -->

---

## Backend-Only Changes (No UI Impact)

- `reports/perf-budgets.md` — gained three new sections (lines ~1728–1891): a G1 transcription of the
  already-captured 11-page TTI + endpoint-latency sweep, a G2 preparatory idle-window log/hwmon cross-read
  (not itself the three-load measurement), and a TC-4 audit-correction blockquote naming
  `apps/backend/app/engine/forward_testing.py:826` as an unbounded-load MISS/compute-path site not
  previously examined. This is a documentation/measurement artifact, not application source or a served
  runtime value (goal.md's Data Contract explicitly registers it as such) — no UI surface affected.
- `docs/handoffs/goal-ops-hardening-iter-12-dev.md` (new) — this iteration's dev handoff, including a
  read-only `data_provider_runs` rows 120/121/122 finding. Documentation only — no UI surface affected.
- `reports/phase-goal-ops-hardening-iter-12-implementation-summary.md` (new) — developer-authored plain-
  language summary of the above. Documentation only — no UI surface affected.
- `runs/goal-ops-hardening-iter-12/status.json` (new) — pipeline bookkeeping (`current_step: dev_complete`).
  Internal orchestration state, never rendered to a user — no UI surface affected.
- `apps/backend/app/engine/forward_testing.py:826` (`compute_forward_aggregates`'s
  `session.exec(select(ScannerResult).where(ScannerResult.run_id.in_(runs_with_fr))).all()`) — named in the
  TC-4 correction addendum as the unbounded MISS/compute-path site, but **not modified**: `git diff` on this
  file is empty. No UI surface affected (and none created, since nothing changed here).

---

## Summary

- **Frontend surfaces changed:** 0
- **New pages/routes:** 0
- **Modified components:** 0
- **Navigation changes:** no
- **Backend-only changes:** 5 (`reports/perf-budgets.md`, the dev handoff, the implementation summary,
  `status.json`, and the named-but-unmodified `forward_testing.py:826` location)
- **Re-verification/measurement-only surfaces (pre-existing, no code change):** 7 rows above, spanning
  `/data` (coverage/`/api/indexes` panel, job form/progress panel, unfinished-imports panel),
  `/scanner-runs` + `/scanner-runs/[runId]`, `/` (home), the top-bar readiness badge, and the global
  preflight/crash banner — required by this iteration's `Frontend Present: yes` line to unblock G2's
  controlled re-measurement and the J-01/J-03/J-04/J-05 required-still-passing browser-qa replay.
