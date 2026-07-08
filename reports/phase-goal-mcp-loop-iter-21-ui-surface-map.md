# Phase goal-mcp-loop-iter-21 — UI Surface Map

**Phase:** goal-mcp-loop-iter-21
**Date:** 2026-07-08
**Written by:** ui-impact-analyst

**Scope note:** `docs/handoffs/goal-mcp-loop-iter-21-dev.md` lists zero changed product-source
files this iteration — only new doc/report artifacts. Per the execution plan's explicit UI
Evolution instruction ("a zero-diff phase must not collapse the UI chain into stub reports"), the
File Classification table below instead classifies the files from commit `aac9abc`
("`goal(mcp-loop): iter 20 — CONTINUE`") — one commit behind current HEAD `6b0f9618` — because
those are the files that carry the J-13 surfaces this iteration's canonical `browser-qa-agent` run
exists to verify live. `git diff HEAD` on every one of them is confirmed empty right now (checked
directly as part of this analysis), i.e., iter-21 changed none of them further. The two surface
tables below are split into (1) the J-13 target surfaces from that commit, and (2) five
functionally unrelated, never-changed regression surfaces that the phase spec requires be
live-replayed this iteration to close a gap iter-20's blanket-SKIPped browser run left open.

---

## File Classification

Per `.claude/skills/diff-to-ui-impact.md`, the files carrying the surfaces under verification this
iteration (source: commit `aac9abc`, confirmed byte-identical to current HEAD):

| File | Category | UI Impact | Explanation |
|------|----------|-----------|-------------|
| `apps/backend/app/engine/data_manager.py` | backend-internal | **indirect** | `_run_job`'s fresh-fetch branch targets `price_load_symbols` (548-pool ∪ context) instead of `all_seed_symbols` (context only). No API route or response shape changed, but the existing `JobProgressPanel`'s "X of Y symbols" counter and progress bar (`app/data/page.tsx`) render `job.symbols_total`, which is now a materially larger number for Fetch/Fetch+backfill jobs — see surface row "Job progress card → symbols counter" below. |
| `apps/backend/scripts/benchmark_pipeline.py` | backend-internal | none | Standalone offline benchmarking script; not run by pytest, not served to the product, not reachable from any UI. |
| `apps/backend/tests/test_data_manager.py` | backend-internal (test) | none | Test-only file; re-run this iteration (102/102 passed) to confirm no drift, not because it changed. |
| `apps/backend/tests/test_data_manager_jobs_pipeline.py` | backend-internal (test) | none | Test-only file; re-run this iteration, no drift. |
| `apps/backend/tests/test_data_manager_parallel.py` | backend-internal (test) | none | Test-only file; re-run this iteration, no drift. |
| `apps/frontend/app/data/page.tsx` | frontend-direct | **direct** | The Data Manager page: job-kind picker, source picker, job-progress panel. Expand option and its supporting code were removed in iter-20; confirmed byte-identical since. |
| `apps/frontend/components/availability-heatmap.tsx` | frontend-direct | **direct** | The per-date availability calendar/legend card on `/data`. Legend, colors, and copy re-encoded in iter-20; confirmed byte-identical since. |
| `apps/frontend/app/globals.css` | frontend-direct | **direct** | CSS custom properties backing the heatmap's density ramp (`--heat-0..5`) and the snapshot-ring token (`--snapshot`). |
| `apps/frontend/tailwind.config.ts` | frontend-direct | **direct** | Registers the `snapshot` Tailwind color utility consumed by `availability-heatmap.tsx`. |

---

## Affected UI Surfaces — J-13 (Target Journey)

All rows below describe the state shipped in iter-20 and confirmed unchanged for iter-21. "Why
Changed" describes the iter-20 rationale (the actual last change); "What to Test" is the live
re-verification action this iteration's `browser-qa-agent` run must execute against real running
services (not code inspection).

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/data` | Page load / required panels (`JobForm`, `AvailabilityHeatmap`) | Unchanged; re-verify reachability | Baseline smoke check — confirms the live stack (not just the code) actually serves the page (UT-01) | Navigate to `http://localhost:3255/data` and wait for loading spinners to clear; confirm the sidebar shows "Data Manager" as the active item, a panel titled "Start a fetch / backfill job" is visible, a card titled "Per-date availability" is visible further down, no "Backend unavailable" card appears anywhere, and no browser console error is logged. |
| `/data` | Job-kind picker (`<select>` in `JobForm`) | Removed element (iter-20) | "Expand universe" option deleted — redundant now that Fetch covers the full 548-pool by default | Open the "Job kind" dropdown on `/data` and read every option top to bottom; confirm there are exactly 3, in order "Backfill snapshots", "Fetch EOD prices", "Fetch + backfill", and no option's text contains the word "Expand". |
| `/data` | Import-source picker (`<select>` in `JobForm`) | Changed behavior (iter-20) | Per-option market-cap-eligibility disabling and suffix text removed along with Expand | Select "Fetch EOD prices" as the job kind, open the "Source" dropdown, and confirm every option is enabled (none greyed out) and its label ends in "· available" or "· needs key" only. |
| `/data` | Market-cap ineligibility alert (`data-testid="expand-ineligible-reason"`) | Removed element (iter-20) | The alert only ever fired for an Expand job paired with a market-cap-incapable source; Expand is gone | Cycle through every job-kind/source combination in the form; confirm the amber "cannot supply market cap" alert box never renders under any combination. |
| `/data` | Job-form panel title + explainer paragraph | Changed behavior/copy (iter-20) | Expand removed from the job-kind set; explainer rewritten to describe the widened Fetch scope honestly | Read the heading directly above the job form (must read exactly "Start a fetch / backfill job") and the grey paragraph beneath the fields (must state Fetch "covers the full committed symbol pool" and contain no occurrence of "Expand"). |
| `/data` | Job progress card → Universe-screen block (`ExpandScreenResult`, removed) | Removed element (iter-20) | The block only ever rendered for `job.kind === "expand"`, an option no longer reachable from the UI | Start a "Fetch EOD prices" job, then separately a "Backfill snapshots" job; confirm neither job's progress card ever shows a "Universe screen" line with "N passed" / "N omitted" badges. |
| `/data` | Job progress card → symbols counter + progress bar | Changed behavior — data volume (iter-20) | The Fetch job's target symbol set now comes from `price_load_symbols` (548-pool ∪ context) instead of the smaller context-only set | Start a "Fetch EOD prices" job and read the "Symbols fetched" row; confirm the total is approximately 588 and at minimum 548 (not the old ~162), that a progress bar advances, and the job reaches `{total}/{total}` without a client-side error. |
| `/data` | Job progress card → "Backfill snapshots" run | Regression (verify still works) | Confirms the dead-code removal around Expand did not collaterally break the two surviving job kinds | Select "Backfill snapshots" (the default), confirm the "Import source" dropdown does NOT appear, click "Start"; confirm the progress panel shows a "Snapshots backfilled" row (not "Symbols fetched") and the job runs with no client-side error. |
| `/data` | Job progress card → "Fetch + backfill" run | Regression (verify still works) | Same dead-code-removal regression risk as above, combined-mode variant | Select "Fetch + backfill", confirm an "· available" import source is selected, click "Start", scroll the whole progress card; confirm both a "Symbols fetched" row and (once fetch finishes) a "Snapshots backfilled" row appear, and no "Universe screen" section ever appears. |
| `/data` | Availability heatmap legend (`AvailabilityHeatmap`, `data-testid="availability-legend-density"` / `"availability-legend-snapshot"`) | Updated layout (iter-20) | Split one ambiguous "Coverage" row into two unmistakable, labeled groups | Scroll to the "Per-date availability" card; confirm the legend shows two separately labeled, stacked rows — "Price data — cell fill" (6 swatches) and "Scored snapshot — indicator" (1 ringed swatch) — never merged into a single label. |
| `/data` | Availability heatmap density cell colors | Changed behavior — visual (iter-20) | The old amber "full" bucket collided perceptually with the page's warning color and the adjacent green bucket | Inspect the rightmost ("full") swatch's computed `background-color` via DevTools; confirm it is `rgb(166, 200, 242)` / `#a6c8f2` (blue), not `rgb(240, 180, 41)` / `#f0b429` (amber); visually confirm all 6 swatches are one blue hue family, each visibly distinct from its neighbor. |
| `/data` | Availability heatmap snapshot ring | Changed behavior — visual (iter-20) | The old green ring collided with the (formerly) green density bucket | Hover or inspect a calendar cell with a ring; confirm its computed ring color is `rgb(167, 139, 250)` / `#a78bfa` (violet), not `rgb(52, 211, 153)` / `#34d399` (green), and that it stays visible against every one of the 6 blue fill shades. |
| `/data` | Availability heatmap per-cell tooltip / `aria-label` | Changed behavior — copy (iter-20) | Names which job (Fetch/Backfill) produced which signal, including calling out a "Backfill gap" | Hover a highly-filled cell WITHOUT a ring; confirm its tooltip reads "...have price data (Fetch) · no snapshot yet — Backfill gap". Hover a ringed cell; confirm its tooltip instead reads "...have price data (Fetch) · scored snapshot exists (Backfill)". Confirm the two tooltips are visibly different and both name "Fetch" and "Backfill". |
| `/data` | Availability heatmap header blurb + caption | Changed behavior — copy (iter-20) | Names the Fetch→fills / Backfill→scores workflow explicitly | Read the paragraph under the "Per-date availability" heading and the caption under the grid; confirm both explicitly state Fetch fills price data and Backfill produces scored snapshots. |
| `/data` | Availability card error/degrade state | Unchanged; re-verify honest degrade | Anti-goal #8 requires a contained, honest failure — never a blank/fabricated state | With DevTools Network open, block `GET /api/data/availability` (or stop the backend) and refresh `/data`; confirm the card shows "Availability could not load from the API. No cells are shown rather than fabricated values." while the rest of the page (job form, sidebar) stays usable, with no uncaught JS error dialog. |

---

## Affected UI Surfaces — Required-Still-Passing Regression Journeys (Live-Replayed This Iteration)

These five surfaces carry **no code change in iter-20 or iter-21** — they are included because
iter-20's canonical `browser-qa-agent` run blanket-SKIPped before reaching any live click-through
(both services were unreachable at precondition), so these journeys were never actually replayed
against the current build. The phase's Definition of Done requires each to pass live this
iteration to close that gap.

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/stocks` | "Sector" column header sort control | No change (regression replay) | Not touched by iter-20 or iter-21; J-01 is the highest-value smoke (the iter-18 crash driver) and was never live-replayed after iter-20's blanket SKIP | Navigate to `/stocks`, wait for the leaderboard to render, click the "Sector" column header, then click it again; confirm the table visibly re-orders both times (a sort-direction indicator appears/flips next to "Sector"), the page never goes blank, and the left sidebar stays visible and clickable throughout. |
| `/stocks` | Score status badge captions ("Not yet proven") | No change (regression replay) | Not touched by iter-20 or iter-21; J-03 (anti-goal #1: unproven scores must never look proven) was never live-replayed after the SKIP | On `/stocks`, read the small text beneath the Leadership, Entry Quality, and Risk score badges for the first 5 visible rows; confirm every one reads exactly "Not yet proven" and none instead reads "Proven" or "PASS". |
| `/evidence` | Evidence ledger list / empty-state card | No change (regression replay) | Not touched by iter-20 or iter-21; J-05 was never live-replayed after the SKIP | Click "Evidence" in the left sidebar and wait for `/evidence` to load; confirm the heading "Evidence" is visible and either a "No certified claims yet" empty-state card or a list of claim rows (each with a status badge and title) renders, with no "Backend unavailable" card and no blank page. |
| `/stocks/{ticker}` | "Recent" / "Full history" chart toggle | No change (regression replay) | Not touched by iter-20 or iter-21; J-10 was never live-replayed after the SKIP | Navigate to `/stocks/NVDA` (or another long-tenured ticker), scroll to the "Price & moving averages" card, click "Full history"; confirm the chart re-renders with a date range extending back many years, no blank chart area or error, the "history since" caption updates, and clicking back to "Recent" restores the shorter window without error. |
| `/methodology` + `/stocks` | Universe/symbol count display (cross-page consistency) | No change (regression replay) | Not touched by iter-20 or iter-21; J-12 was never live-replayed after the SKIP | Navigate to `/methodology` and note the universe/symbol count in the Universe Selection section; navigate to `/stocks` and note the leaderboard's `{visible} / {total}` indicator with no filters applied; confirm the two counts describe the same underlying point-in-time universe with no mismatch. |

---

## Backend-Only Changes (No UI Impact)

Carried forward from iter-20's commit; not re-touched this iteration (all four confirmed
byte-identical, all re-run green this iteration per the dev handoff's 102/102 pytest result):

- `apps/backend/tests/test_data_manager.py` — fixed 2 pre-existing tests that hardcoded the old
  context-only symbol universe as the fetch job's expectation, and added 2 tests (Fetch-scope
  coverage of the 548 pool + context; `compute_availability` byte-identical-output regression
  guard). Tests only; no UI surface.
- `apps/backend/tests/test_data_manager_jobs_pipeline.py` — fixed 3 pre-existing tests with the
  same hardcoded-universe issue. Tests only; no UI surface.
- `apps/backend/tests/test_data_manager_parallel.py` — fixed 7 pre-existing tests (explicit
  `seed_dir` pinning / monkeypatch retargeting). Tests only; no UI surface.
- `apps/backend/scripts/benchmark_pipeline.py` — standalone offline benchmarking script (not part
  of the served product, not run by pytest, not triggered from any UI); retargeted its own
  monkeypatch after the import rename. No UI surface.

---

## Summary

- **Frontend surfaces changed this iteration:** 0 (confirmed empty `git diff HEAD` on all 5
  product-source files; iter-21 is verification-only)
- **Frontend surfaces re-verified live this iteration:** 5 routes — `/data` (14 elements, J-13
  target), `/stocks` (2 elements, J-01 + J-03), `/evidence` (1 element, J-05),
  `/stocks/{ticker}` (1 element, J-10), `/methodology` + `/stocks` cross-page (1 check, J-12)
- **New pages/routes:** 0
- **Modified components this iteration:** 0 (4 frontend files were modified in iter-20 and remain
  confirmed byte-identical; 0 sub-components added or removed this iteration)
- **Navigation changes:** no
- **Backend-only changes:** 4 (3 test files + 1 offline benchmarking script, all from iter-20,
  re-run green this iteration); 1 additional backend file (`data_manager.py`) has an indirect UI
  effect captured in the J-13 surface table above, not here
