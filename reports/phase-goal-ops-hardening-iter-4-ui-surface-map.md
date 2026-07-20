# Phase goal-ops-hardening-iter-4 — UI Surface Map

**Phase:** goal-ops-hardening-iter-4
**Date:** 2026-07-20
**Written by:** ui-impact-analyst

---

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| Global header (every page, mounted once in `app/layout.tsx`) | `HealthBadge` (`data-testid="readiness-badge"`) — new `awaiting_snapshot` branch | New state | B3 fix: the benchmark symbol's (SPY) own latest bar advancing past the last persisted scan, with no run yet for that later date, now renders a 4th, calm state instead of the crash-identical "Backend unavailable". | Land a new price bar for SPY dated after the last persisted scan run (e.g. a "Fetch EOD prices" job scoped to SPY over a date range past the last run), without yet running a backfill/rebuild for that new date. Reload any page and confirm the header badge shows `data-state="awaiting_snapshot"`, visible text starting with "Snapshot pending" (never "Backend unavailable"), an accent-colored (not red) static/non-pulsing dot, and a trailing sentence naming SPY, the pending date, and "Run a backfill or rebuild on Data Manager". |
| Global header (every page) | `HealthBadge` — non-benchmark fetch must not move the badge | Changed behavior | The actual B3 bug fix: an ordinary fetch that lands a bar for a symbol OTHER than the benchmark must no longer affect the badge at all (previously it flipped it to "Backend unavailable"). | Note the header badge's current `data-state` (e.g. `ready`). Run a "Fetch EOD prices" job for a single ordinary stock that is NOT SPY, using a date range that lands a bar dated after the last persisted run. After the job reaches a terminal status, reload the page and confirm the badge's `data-state` is unchanged from what it was before the job — it must NOT become `unavailable` or `awaiting_snapshot`. |
| Global header (every page) | `HealthBadge` — true-unavailable path | Unchanged — regression check | The new state must never mask genuine unavailability: `latest_run is None` (no `ScannerRun` ever persisted) must still resolve unconditionally to `unavailable`. | Point the backend at a freshly-created database that has never had a scan run persisted (no `ScannerRun` rows) and load any page. Confirm the badge shows `data-state="unavailable"` with visible text "Backend unavailable" — not "Snapshot pending" and not "Ready". |
| Global header (every page) | `PreflightBanner` (`data-testid="preflight-banner"`, `data-verdict`) | Unchanged — regression check | `compute_preflight`'s servability component treats the new `awaiting_snapshot` state as non-breaching (same as `ready`/`initializing`) — the new badge state must not force the verdict to `DEGRADED`/`NO-GO`. | While the header badge is in the `awaiting_snapshot` state (from row 1's setup), reload any page and confirm the banner still shows `data-verdict="GO"` with its quiet "GO — today's board is current." text — not the loud amber/red `DEGRADED`/`NO-GO` banner. |
| `/data` (Data Manager) | `JobProgressPanel` live job card heartbeat (`data-testid="job-heartbeat"`) | Changed behavior | F1 fix: `_refresh_ingest_aggregates`/`_persist_per_date_coverage_snapshots` now call `prog.tick()` on every per-date step of BOTH finalize-phase loops (coverage + market-phase), so the heartbeat advances through the whole aggregate-refresh tail instead of freezing once the main scan ends. | Submit a "Backfill snapshots" (or "Fetch + backfill") job spanning enough dates to trigger the post-scan aggregate-refresh phase (a multi-date range with several new snapshot dates). Watch the live job card's heartbeat text continuously for the run's full duration: confirm "updated Ns ago" keeps resetting to a low value throughout, including after the main scan portion finishes, and the "· possibly stalled" suffix never appears while the job is still `running`. |
| `/data` (Data Manager) | `CoveragePanel` — never-ingested / fresh-boot all-zero state | Unchanged — regression check | Re-verifies iter-2/iter-3's cold-boot guarantee against a genuinely fresh database copy — this iteration's Definition of Done requires this check to actually execute (closes the previously-SKIPPED UT-04), not merely be re-argued from code. | Using a fresh, never-ingested copy of the database (no `coverage_snapshot` rows, no prior scan run), cold-boot the backend against it and load `/data` as the very first request. Confirm the "Dataset coverage" panel renders the honest all-zero "not yet computed" state within the page's normal load time — no infinite spinner, no error boundary, no long full-table-scan delay. |
| Global header + `/data` | `HealthBadge` / `JobProgressPanel` / `CoveragePanel` — required-still-passing J-01/J-03/J-04 | Unchanged — regression check | `readiness.py`'s servability rewrite and `data_manager.py`'s new `tick()` calls both touch shared, every-page-read code paths — J-01/J-03/J-04's already-shipped acceptance must render identically after this edit. | Submit a multi-day "Backfill snapshots" job spanning a range with existing gaps (the kind J-01/J-03 already exercise). Confirm the Job progress panel's "N calendar days · N already snapshotted · N non-trading" breakdown line renders exactly as before, the header badge reads "Ready" throughout (never flips or freezes), and `/data`'s Dataset coverage numbers update correctly once the job finishes. |

<!-- Change Type options used above: New state | Changed behavior | Unchanged — regression check -->

---

## Backend-Only Changes (No UI Impact)

- `apps/backend/app/engine/readiness.py`'s `_latest_benchmark_bar_date` query, the `has_servable_run`/
  `awaiting_snapshot` state-machine rewrite, and the new `detail` field on `compute_readiness`'s return —
  plus `apps/backend/app/api/health.py`'s new `readiness_detail` response key that carries it. This is
  the internal computation feeding the badge; its entire user-facing effect is captured by the
  `HealthBadge` rows above — no independent UI surface of its own.
- `apps/backend/app/engine/data_manager.py`'s `prog.tick()` additions inside `_refresh_ingest_aggregates`
  and `_persist_per_date_coverage_snapshots` — the internal heartbeat-timing fix feeding the job-progress
  card. Fully captured by the `JobProgressPanel` row above; no independent UI surface of its own.
- `apps/backend/tests/test_readiness.py` and `apps/backend/tests/test_data_manager.py` — new/updated
  unit tests pinning the B3 (benchmark-scoped servability, `awaiting_snapshot`, preflight non-breach,
  true-unavailable regression) and F1 (per-date heartbeat tick) fixes at the code level. Tests are not
  shipped to users; no UI surface.
- `docs/handoffs/goal-ops-hardening-iter-4-dev.md` and `docs/handoffs/goal-ops-hardening-iter-4-frontend.md`
  — developer documentation of the fixes and the exact state/field names chosen. No UI surface.

---

## Summary

- **Frontend surfaces changed:** 1 (`HealthBadge`, mounted once in the root layout, so the change is
  visible in the header on every page)
- **New pages/routes:** 0
- **Modified components:** 1 — `HealthBadge` (`apps/frontend/components/health-badge.tsx`); the other
  frontend file touched (`apps/frontend/lib/api.ts`) is a supporting type-definition file, not an
  independently rendered surface
- **Navigation changes:** no
- **Backend-only changes:** 4 (grouped above, covering `readiness.py`+`health.py`, `data_manager.py`, the
  2 backend test files, and the 2 handoff docs)
