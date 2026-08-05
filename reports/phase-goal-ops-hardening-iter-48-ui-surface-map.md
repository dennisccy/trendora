# Phase goal-ops-hardening-iter-48 — UI Surface Map

**Phase:** goal-ops-hardening-iter-48
**Date:** 2026-08-04
**Written by:** ui-impact-analyst

---

## Diff Classification

Zero files under `apps/frontend/` changed this iteration. All three product files touched
(`apps/backend/app/engine/data_manager.py`, `apps/backend/app/engine/samples.py`,
`apps/backend/app/engine/research.py`) classify as **backend-api / backend-internal** by
`diff-to-ui-impact.md`'s rules — but two of them serve response fields the frontend already renders
unchanged, so their behavior change reaches the UI indirectly ("indirect — frontend consumes this API,
surface affected").

| File | Category | UI Impact | Explanation |
|------|----------|-----------|-------------|
| `apps/backend/app/engine/data_manager.py` | backend-api | indirect | `_membership_timeline` / `membership_timeline_cached` / `_refresh_ingest_aggregates` back the SAME `GET /api/data` job/run fields (`status`, `aggregates_refreshed`, `message`) the `/data` Job progress panel and `/scanner-runs` already render — the fields didn't change shape, but a historical-gap backfill now resolves them to a terminal value far faster for the targeted step. |
| `apps/backend/app/engine/samples.py` | backend-api | indirect (invisible) | `_factor_samples`'s `total`/`regime` branches back the SAME `/research/factor-lab` and `/evidence` drawdown-expectations reads — member rows are proven byte-identical, so the ONLY user-observable effect is a lower chance of a memory failure under load, not a display difference. |
| `apps/backend/app/engine/research.py` | backend-internal | none (indirect via samples.py) | New `_factor_regime_observations` helper is an internal resolver called only from `samples.py`'s `regime` branch above — no UI element calls it directly. |
| `apps/backend/tests/*.py` (4 files) | backend-internal | none | Test-only. |
| `reports/perf-budgets.md` | config/docs | none | Internal engineering record, not rendered in-product. |
| `runs/goal-session-ops-hardening/journey-scripts/J-05.json` | config/test-tooling | none | Golden-replay assertion fix + target-date rotation — QA tooling, not a product UI surface. |
| `runs/goal-session-ops-hardening/state/assumptions.md` | docs | none | Decision log, not rendered in-product. |

---

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/data` | Job progress panel — status badge (`JobProgressPanel`, `data-testid="job-status"`) | Changed behavior | A historical-gap backfill's coverage/membership-timeline finalize step no longer sweeps every historical date unbatched; that step now completes in ~10–25s instead of extrapolating to well over an hour, so the badge stops spinning on "running" for its own contribution. | Start a Backfill snapshots job for start date `2012-06-15` / end date `2012-06-15` on `/data`, then watch the element with `data-testid="job-status"` — confirm it eventually stops showing the spinner (`animate-spin` `Loader2` icon) and settles to `ok` (or `no new snapshots` if that date was already snapshotted by a prior run). |
| `/data` | "Refreshed: …" line (`BackfillBreakdown`, `data-testid="aggregates-refreshed"`) | Changed behavior | Populates promptly for a historical-gap backfill now that the membership-timeline refresh it names finishes fast. | After starting the same backfill, confirm the element with `data-testid="aggregates-refreshed"` renders text starting with `Refreshed:` and mentioning `membership timeline` (or `coverage`) within about 30 seconds. |
| `/data` | Readiness badge (`HealthBadge`, `data-testid="readiness-badge"`) | Regression check (unchanged code, verifies TC-4) | The backend must stay responsive (`GET /api/health` returns 200) throughout the whole finalize tail, even on a run where the OVERALL job takes a long time due to the separate, unfixed `drawdown_expectations_warm` step. | While the backfill from the row above is still `running`, repeatedly check the readiness badge in the page header — confirm it stays on `data-state="ready"` (green "Ready") the entire time and never flips to `data-state="unavailable"` ("Backend unavailable", red). |
| `/scanner-runs` | Run history table row (`RunTableRow`, "As of" column link) | Changed behavior | A historical-gap date's run now becomes a real, clickable row because the backfill job actually reaches a terminal status. | After the `/data` job above settles, navigate to `/scanner-runs` and confirm a row with "As of" text `2012-06-15` appears in the table, with a clickable date link. |
| `/scanner-runs/[runId]` | Run detail heading + leaderboard table | Changed behavior | Opens the stored snapshot for the historical date instead of never being reachable (the run row didn't exist while the job never terminated). | Click the `2012-06-15` link from the row above — confirm the page shows the text "Immutable snapshot — as of 2012-06-15" and the leaderboard table below it renders at least one stock row (not a loading skeleton or 404/"notfound" state). |
| `/evidence` | Drawdown-expectations panel (`data-testid="evidence-expectations-panel"` / `"evidence-expectations-table"`) | Changed behavior (invisible — memory only) | `_factor_samples`'s `total`/`regime` branches now build rows in one pass / filter inline instead of materializing the full population twice; member rows are proven byte-identical so nothing should visibly change. | Navigate to `/evidence`, open a claim card with a `data-testid="evidence-claim-regime"` badge (a regime-conditioned claim), and confirm its `evidence-expectations-table` renders populated `evidence-expectations-phase-row` rows with real percentage figures — not an empty/error state (`data-testid="evidence-expectations-unavailable"`). |
| `/research/factor-lab` | Drawdown-expectations panel (same components as `/evidence`, via `_labs.tsx`) | Changed behavior (invisible — memory only) | Same `_factor_samples` code path as the `/evidence` row above. | Navigate to `/research/factor-lab`, confirm the page loads without an error card and at least one factor's drawdown-expectations table renders populated rows. |
| `/data` | Job progress panel — zero-work badge (`data-testid="zero-work-note"`) | Regression check (unrelated code, but relevant to the fix's own correctness) | Confirms a re-run over an already-snapshotted historical date still reads honestly as "no new snapshots" rather than a fabricated success — this is the exact null-test shape the fix must not accidentally produce. | Re-run the SAME backfill (start/end date `2012-06-15`) a second time after step 1 completes — confirm the badge reads `no new snapshots` (not `ok`) and the note `data-testid="zero-work-note"` appears with text "Zero-work outcome — every requested trading day already had a snapshot…". |

<!-- Change Type key used above: Changed behavior (existing UI element now behaves differently because of
     an unchanged-shape backend response resolving faster / more safely); Regression check (unaffected by
     this diff, verified to confirm nothing else broke). No New page | New component | New form | New
     table | New modal | Added navigation rows apply — this iteration added none of those. -->

---

## Backend-Only Changes (No UI Impact)

- `data_manager.py`'s per-phase wall-clock instrumentation/logging (`logger.info("J-05 finalize-tail phase
  timing: ...")`) — server logs only, never surfaced in any page or component.
- `research.py`'s new `_factor_regime_observations` helper — an internal resolver function; its effect only
  reaches the UI indirectly through the `/evidence` / `/research/factor-lab` row above, and is invisible
  there (byte-identical output).
- `samples.py`'s `total` branch in-place row construction — a pure memory-layout change with proven
  byte-identical output; same reasoning as above.
- New/extended backend tests (`test_data_manager.py`, `test_research_streaming.py`,
  `test_samples_memory_pressure.py`, `test_start_backend_script.py`) — test-only, no UI surface.
- `reports/perf-budgets.md` new dated entries — internal engineering record, not shown in-product.
- `runs/goal-session-ops-hardening/journey-scripts/J-05.json`'s TC-9 assertion fix and target-date rotation
  — QA/golden-replay tooling, not a product UI surface.
- `runs/goal-session-ops-hardening/state/assumptions.md` — decision log, not rendered in-product.

---

## Summary

- **Frontend surfaces changed:** 0 frontend files modified this iteration.
- **Existing UI surfaces with changed BEHAVIOR (no code change on the frontend side):** 4 — `/data` Job
  progress panel (status badge + aggregates-refreshed line), `/scanner-runs` run history table,
  `/scanner-runs/[runId]` run detail page, `/evidence` + `/research/factor-lab` drawdown-expectations
  panels.
- **New pages/routes:** 0
- **Modified components:** 0 (behavior differs only because the backend now resolves the same
  already-rendered fields differently over time)
- **Navigation changes:** no
- **Backend-only changes:** 7 (instrumentation/logging, the new internal resolver, the `total` branch's
  in-place construction, 4 test files, the perf-budgets report, the journey-script assertion fix, the
  assumptions-log entry)
