# Phase goal-ops-hardening-iter-6 — UI Surface Map

**Phase:** goal-ops-hardening-iter-6
**Date:** 2026-07-21
**Written by:** ui-impact-analyst

---

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/` (Dashboard) | `PhaseCrossViewCard` — the "Regime × phase cross-view" chart card (below the fold), specifically its on-mount `Promise.all` fetch of indexes-full + regime-history-full + market-phase-full | Changed behavior | The fetch now fires inside a `window.setTimeout(..., 250)` instead of immediately on mount, to let the page's own initial same-origin request/asset burst clear Chrome's connection queue first — fixes `GET /api/indexes?full=true` real-browser latency (1.68–2.19s pre-fix → 821–872ms post-fix, 3/3 reloads); values served are unchanged, only timing | In a real Chrome tab against a warm prod-mode session (`scripts/start-backend.sh` / `scripts/start-frontend.sh`, not `dev.sh`) with DevTools Network tab open, load `/` and reload it 3 times; confirm `GET /api/indexes?full=true`'s Network-tab "Time" reads ≤1500ms on all 3 reloads, and confirm the card's `animate-pulse` skeleton is visible immediately at page load with no blank gap before the "Regime × phase cross-view" chart itself renders |
| `/` (Dashboard) | `PhaseCrossViewCard` — abort/cleanup path (new race window introduced by the added `setTimeout`) | Changed behavior | The cleanup function must now clear both the pending timer AND the `AbortController` on unmount/deps-change, so a fast as-of date change that unmounts the effect before or during the deferred fetch never leaves a stale or blank card | On `/`, load the Dashboard, then within ~1 second use the as-of date picker to change the date twice in rapid succession; confirm the card shows its `animate-pulse` skeleton throughout the transition (never a blank or frozen panel), then settles to the "Regime × phase cross-view" chart populated with the newly-selected date's data |
| `/data` (Data Manager) | Availability heatmap's data loader (`loadAvailability()`, feeding `AvailabilityHeatmap`) inside `DataManagerPage`'s mount effect | Changed behavior | `loadAvailability()` now fires 2500ms after `loadOverview()` on the page's first mount only (every other reload path — job completion, retry/dismiss, removal — still calls both together, unchanged) — fixes `GET /api/data/availability` real-browser latency (2.8–3.0s pre-fix, previously unbudgeted → 1000–1052ms post-fix, 3/3 reloads) | In the same real-Chrome/prod-mode session, load `/data` and reload it 3 times; confirm `GET /api/data/availability`'s Network-tab timing reads ≤1500ms on all 3 reloads, and confirm the heatmap shows its `Loader2` spinner plus "Loading availability…" text throughout the ~2.5s deferred window before data appears, never a blank panel |
| `/data` (Data Manager) | Run History panel / persisted run entry (target of the rewritten `J-01.json` golden-script step 6 — the panel's own code is unchanged; only the automated assertion against it changed) | Test-infra target changed | `J-01.json` step 6 previously asserted a fixed, now-stale `"2026-05-15"` text buried past `/scanner-runs`'s unpaginated 750-row list; it now asserts `"no new snapshots"` against `/data`'s own persisted run-history entry for the exact backfill this script's own earlier steps submit | On `/data`, submit a weekend-only backfill via the job form (Start=`2026-05-02`, End=`2026-05-03`, Kind=Backfill, click "Start"), wait for it to finish, then reload `/data`; confirm the run-history panel/table shows "no new snapshots" text for that run's entry — this is what the automated J-01 replay now checks in step 6 |

<!-- Change Type "Changed behavior" throughout for the two live fixes — no new page, component, form, table,
     modal, or nav entry was added or removed; every touched component keeps its exact prior render contract,
     only WHEN its underlying fetch fires differs. -->

---

## Additional Finding: Pre-Existing Regression (Discovered This Iteration, Not Caused By or Fixed By This Diff)

While re-measuring all 11 J-06 pages (required by this iteration's own DoD), the developer found two pages
severely over their committed budget for reasons entirely unrelated to this iteration's code changes — zero
files under either page's directory, or any backend module, were touched this iteration. Listed here because
QA/closure/regression testers need to know these will still fail if tested, and should not misattribute the
failure to this iteration's fetch-timing fix:

| Route / Page | Component / Element | Change Type | Why (Not) Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/evidence` | Evidence Ledger main data panel | Known issue — NOT fixed this iteration | Pre-existing backend `EventStudyCache`/samples-resolution scaling regression as the live `forward_returns` table has grown ~5x since iter-5; unrelated to this diff | Navigate to `/evidence` with a cold cache and time how long the main panel takes to populate; expect it to take on the order of several minutes (555.97s measured via direct `curl` this iteration) rather than the ~9.3–9.6s recorded as of iter-5 — this is a known, already-flagged open issue, not a new regression to file against this iteration |
| `/research` (event-study lab, `view=episodes`) | Event-study lab results panel | Known issue — NOT fixed this iteration | Same root cause as `/evidence` — cache/scaling regression from live-DB growth, unrelated to this diff | Navigate to the `/research` event-study lab with a cold cache; expect roughly 92 seconds to first render (vs. ~0.003–0.005s recorded as of iter-5). Reload immediately after (warm/cached path) and expect ~1.46s — also regressed from the prior near-instant warm reads, though far better than the cold path |

---

## Backend-Only Changes (No UI Impact)

- `reports/perf-budgets.md` — engineering measurement log (new "J-06 closeout" dated section: 3-reload
  tables for both fixed endpoints, the new `GET /api/data/availability` budget row, the full 11-page
  single-pass breakdown, and the critical-finding writeup above) — explicitly a measurement artifact, not a
  UI surface; no UI element reads or renders this file.
- `runs/goal-session-ops-hardening/journey-scripts/J-01.json` — automated golden-script definition (JSON
  test fixture consumed by the deterministic replay harness, not shipped to end users) — its step-6 rewrite
  changes what an automated test asserts against the existing `/data` page, not the page's own code or
  behavior; captured above as a "test-infra target changed" row for QA traceability, not counted as a
  production UI surface change.
- `docs/handoffs/goal-ops-hardening-iter-6-dev.md`, `docs/handoffs/goal-ops-hardening-iter-6-frontend.md` —
  handoff documentation — no UI surface affected.
- No backend Python source file appears in this iteration's diff (confirmed via `git status` and the dev
  handoff) — every serving endpoint's code is byte-identical to before; only frontend request timing changed.

---

## Summary

- **Frontend surfaces changed:** 2 (`/` — `PhaseCrossViewCard`'s fetch timing; `/data` — the availability
  heatmap's fetch timing)
- **New pages/routes:** 0
- **Modified components:** 2 (`apps/frontend/components/phase-cross-view-card.tsx`,
  `apps/frontend/app/data/page.tsx`)
- **Navigation changes:** no
- **Backend-only changes:** 2 (`reports/perf-budgets.md` measurement log; golden-script JSON fixture)
- **Known pre-existing regressions surfaced (not part of this diff, not fixed):** 2 pages (`/evidence`,
  `/research` event-study lab) — see the dedicated section above
