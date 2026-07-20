# Phase goal-ops-hardening-iter-2 — UI Surface Map

**Phase:** goal-ops-hardening-iter-2
**Date:** 2026-07-19
**Written by:** ui-impact-analyst

---

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/data` | `BackfillBreakdown` — new `data-testid="aggregates-refreshed"` line, shared by `LastRunSummary`, `JobProgressPanel`'s live card, and `RunHistoryPanel` table rows (`apps/frontend/app/data/page.tsx`) | New element | The ingest finalize hook now reports which downstream aggregates (coverage, latest snapshot, membership timeline, market phase, research hot keys) it actually refreshed at the end of a backfill/both/rebuild job (J-05; TC-5, TC-20). | Start a backfill for one currently-unsnapshotted single day (e.g. start=end=2026-05-15) and wait for it to reach a terminal `ok` status. Confirm the Job progress panel shows a line "Refreshed: coverage, market phase, membership timeline, research hot keys" (exact wording matches whichever categories the hook actually ran, comma-joined, underscores shown as spaces) directly beneath the existing "N calendar days · N already snapshotted · N non-trading" line. Then reload `/data` and confirm the identical "Refreshed: ..." line now also appears on that run's row in the Run history table at the bottom of the page. |
| `/data` | `JobProgressPanel`'s no-session-job branch → `LastRunSummary` card | Unchanged — regression check | `BackfillBreakdown`'s outer suppression guard changed from "all four breakdown fields null" to `!hasBreakdown && !hasAggregates` to accommodate the new prop — the pre-existing no-job / persisted-history fallback must still behave identically. | With no job started in the current browser session but persisted run history present, load `/data` fresh. Confirm the panel still renders the status badge, the run's message text, and the pre-existing "N calendar days · ..." breakdown line exactly as before. If that persisted run's `aggregates_refreshed` is null (predates this iteration, or is a fetch/expand run), confirm the "Refreshed:" line is completely absent — not rendered as an empty or dashed label. |
| `/data` | "Dataset coverage" panel — `DefinedMetric` stat tiles (Price history, Universe `data-testid="universe-count"`, Candidate universe `data-testid="candidate-universe-count"`, Symbols, Trading days, Snapshot dates, Backfill gaps) | Changed behavior (data source + timing) | `GET /api/data`'s coverage block now reads the persisted `coverage_snapshot` table (`data_manager.coverage_from_storage`) instead of live-calling `compute_coverage` on the request path — removes the whole-table-scan OOM/hang source (TC-6, TC-7). | Restart the backend via `scripts/start-backend.sh` against a database that already has at least one completed ingest, then load `/data` as the very first request after that restart. Confirm the "Dataset coverage" panel's stat tiles (Symbols, Snapshot dates, Price history range, etc.) populate immediately — well under a second, not the several-second wait the page used to show — and display the exact same numbers the panel showed before the restart. |
| `/data` | "Dataset coverage" panel + the app-wide as-of switcher (global header control, `useAsOf`) | Regression check — AG-3-critical (bug introduced and fixed within this same iteration) | The coverage-from-storage read path's first pass only ever had a stored row for the single current/latest as-of; selecting any OTHER already-ingested historical date incorrectly served the all-zero "not yet computed" sentinel instead of that date's real numbers. Code review caught this before this handoff and it was fixed via a per-date persist at ingest time plus a self-healing read for legacy dates. | Use the as-of switcher to select an older date that has real, pre-existing data (not the current latest date). Confirm the "Dataset coverage" panel shows that date's genuine non-zero Symbols / Snapshot-dates / Universe counts — not an all-zero "nothing here yet" panel. Then switch back to the latest date and confirm its numbers are unchanged and still instant. |
| `/data` | "Dataset coverage" panel — zero-`coverage_snapshot`-row state | New element (honest empty state) | A genuinely never-ingested database must serve HTTP 200 with an honest empty/zero coverage state, never a 500 or an indefinitely hung request, and the background warm-up thread must fill it in shortly after boot (TC-9, TC-10). | On a database with zero rows in the new `coverage_snapshot` table (a pre-ingest or freshly-seeded state), load `/data`. Confirm the page loads normally — no error boundary, no infinite spinner — with the coverage stat tiles reading `0`/empty rather than crashing or hanging. Wait for the backend's background warm-up to finish (a few seconds; the header's readiness badge settles from "Initializing…" to "Ready"), then reload `/data` and confirm the same stat tiles now show real, non-zero numbers with no job having been run in between. |

<!-- Change Type options used above: New element | Changed behavior | Unchanged — regression check -->

---

## Backend-Only Changes (No UI Impact)

- `apps/backend/app/engine/data_manager.py`'s market-phase/membership-timeline/research-hot-key warming calls inside the new ingest finalize hook (`_refresh_ingest_aggregates`) — these reuse the SAME pre-existing `market_phase_cached`/`membership_timeline_cached`/`event_study_cached` functions that `/`, `/scanner-runs`, and `/research/*` already called before this iteration; none of those pages' routes or components changed this iteration. The only effect is that the cache row those pages already read may already be warm by the time anyone visits — byte-identical output either way, confirmed by the dev handoff's own call-count/byte-identity tests. Not an independent, testable UI surface.
- `apps/backend/app/models.py` — new `CoverageSnapshot` table — pure storage; its only consumer is `coverage_from_storage`, already captured in the coverage-panel rows above. No independent UI surface.
- `apps/backend/app/engine/warmup.py` — new `_warm_coverage_snapshot` boot-safety-net step — its user-facing effect is already captured in the zero-row-state row above (the "reload a few seconds later" transition). No separate UI surface of its own.
- `apps/backend/app/api/data.py` — the one-line swap from `compute_coverage` to `coverage_from_storage` inside `data_overview` — the route's request/response shape is unchanged; its behavioral effect is already captured in the coverage-panel rows above.
- `scripts/start-backend.sh` (the real git-tracked file is `incredible_auto_dev/scripts/start-backend.sh`; `scripts/` is a pre-existing symlink to it) — new `ulimit -v`, `MALLOC_ARENA_MAX` export, and persistent `logs/backend.log` redirect — a process-launch/ops concern only; nothing in the web UI reads or displays any of this. No UI surface.
- `reports/perf-budgets.md` — new dated sections (Items J and K) documenting the before/after timing and memory measurements — an internal engineering report, not part of the running product. No UI surface.
- Backend test suite changes — `apps/backend/tests/test_data_manager.py`, `test_api_data.py`, `test_warmup.py`, and the new `test_start_backend_script.py` — pin the contracts above at the test level. No UI surface (tests are not shipped to users).

---

## Summary

- **Frontend surfaces changed:** 1 page (`/data`); 3 further pages (`/`, `/scanner-runs`, `/research/*`) are named as explicit no-code-change / no-visible-delta regression targets, not as changed surfaces.
- **New pages/routes:** 0
- **Modified components:** `BackfillBreakdown` (extended with one new optional prop, not forked) across its existing 3 call sites (`LastRunSummary`, `JobProgressPanel`, `RunHistoryPanel`), all within `apps/frontend/app/data/page.tsx`; `DataRun`/`DataJob` TypeScript interfaces extended in `apps/frontend/lib/api.ts` to carry the new field through.
- **Navigation changes:** no
- **Backend-only changes:** 6 (grouped above)
