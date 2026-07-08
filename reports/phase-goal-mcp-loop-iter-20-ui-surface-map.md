# Phase goal-mcp-loop-iter-20 — UI Surface Map

**Phase:** goal-mcp-loop-iter-20
**Date:** 2026-07-07
**Written by:** ui-impact-analyst

---

## File Classification

Per `.claude/skills/diff-to-ui-impact.md`, each changed file from the dev handoff:

| File | Category | UI Impact | Explanation |
|------|----------|-----------|-------------|
| `apps/backend/app/engine/data_manager.py` | backend-internal | **indirect** | `_run_job`'s fresh-fetch branch now targets `price_load_symbols` (548-pool ∪ context) instead of `all_seed_symbols` (context only). No API route or response schema changed — but the existing `JobProgressPanel`'s "X of Y symbols" counter and progress bar (unmodified frontend code, `app/data/page.tsx:2446,2451`) render `job.symbols_total`, which will now be a materially larger number for Fetch/Fetch+backfill jobs. See surface-map row 7. |
| `apps/backend/scripts/benchmark_pipeline.py` | backend-internal | none | Standalone offline benchmarking script; not run by pytest, not served to the product, not reachable from any UI. Retargeted its own monkeypatch to avoid an `AttributeError` after `all_seed_symbols` was dropped from `data_manager.py`'s imports. |
| `apps/backend/tests/test_data_manager.py` | backend-internal (test) | none | Test-only file. |
| `apps/backend/tests/test_data_manager_jobs_pipeline.py` | backend-internal (test) | none | Test-only file. |
| `apps/backend/tests/test_data_manager_parallel.py` | backend-internal (test) | none | Test-only file. |
| `apps/frontend/app/data/page.tsx` | frontend-direct | **direct** | The Data Manager page: job-kind picker, source picker, job-progress panel. Expand option and its supporting code removed. |
| `apps/frontend/components/availability-heatmap.tsx` | frontend-direct | **direct** | The per-date availability calendar/legend card on `/data`. Legend, colors, and copy re-encoded. |
| `apps/frontend/app/globals.css` | frontend-direct | **direct** | CSS custom properties backing the heatmap's density ramp (`--heat-0..5`) and the new snapshot-ring token (`--snapshot`) — the project's stated only location for these hex values. |
| `apps/frontend/tailwind.config.ts` | frontend-direct | **direct** | Registers the new `snapshot` Tailwind color utility consumed by `availability-heatmap.tsx`. |

---

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/data` | Job-kind picker (`<select>` in `JobForm`) | Removed element | "Expand universe" option deleted — redundant now that Fetch covers the full 548-pool by default | Open the "Job kind" dropdown on `/data` and count its options; confirm there are exactly 3 ("Backfill snapshots", "Fetch EOD prices", "Fetch + backfill") and no "Expand universe" entry. |
| `/data` | Import-source picker (`<select>` in `JobForm`) | Changed behavior | Per-option market-cap-eligibility disabling and suffix text removed along with Expand | Select "Fetch EOD prices" as the job kind, open the "Source" dropdown, and confirm every option is enabled (none greyed out) and its label ends in "· available" or "· needs key" only — no "cannot supply market cap" text. |
| `/data` | Market-cap ineligibility alert (`data-testid="expand-ineligible-reason"`) | Removed element | The alert only ever fired for an Expand job paired with a market-cap-incapable source; Expand is gone | Try every job-kind/source combination in the form and confirm the amber "cannot supply market cap" alert box never appears anywhere on the page. |
| `/data` | Job-kind explainer paragraph (below the form fields, `JobForm`) | Changed behavior (copy) | Described the deleted Expand behavior; replaced with an honest description of Fetch's widened scope | Read the small grey paragraph under the job-kind/source fields and confirm it states Fetch covers "the full committed symbol pool" and contains no occurrence of the word "Expand". |
| `/data` | Job-form panel title (`PanelTitle`) | Changed behavior (copy) | Expand removed from the job-kind set | Look at the heading directly above the job form and confirm it reads "Start a fetch / backfill job" (not "... / expand job"). |
| `/data` | Job progress card → Universe-screen block (`ExpandScreenResult`, removed) | Removed element | The block only rendered for `job.kind === "expand"`, an option no longer reachable from the UI | Start a Fetch job, then separately a Backfill job, from `/data`; confirm neither job's progress card ever shows a "Universe screen" line with "N passed" / "N omitted" badges. |
| `/data` | Job progress card → symbols counter + progress bar (existing element; underlying data widened) | Changed behavior (data volume) | The Fetch job's target symbol set now comes from `price_load_symbols` (548-pool ∪ context) instead of the smaller context-only set | Start a "Fetch EOD prices" job on `/data` and read the progress card's "X of Y symbols" counter; confirm Y is in the high-500s (the full committed pool plus context), not the old ~162, and that the job still runs to completion without error. |
| `/data` | Availability heatmap legend (`AvailabilityHeatmap`) | Updated layout | Split one ambiguous "Coverage" row into two unmistakable, labeled groups | Scroll to the "Per-date availability" card; confirm the legend area shows two separately labeled rows — "Price data — cell fill" and "Scored snapshot — indicator" — each with its own heading text (verify via `data-testid="availability-legend-density"` and `data-testid="availability-legend-snapshot"`). |
| `/data` | Availability heatmap density cell colors | Changed behavior (visual) | The old amber "full" bucket collided perceptually with the page's warning color and the adjacent green bucket | Find a fully-covered ("full") day cell on the heatmap, inspect its computed `background-color` via browser dev tools, and confirm it is the new blue (`#a6c8f2`), not the old amber (`#f0b429`); confirm none of the 6 buckets renders as amber, cyan, teal, or green. |
| `/data` | Availability heatmap snapshot ring | Changed behavior (visual) | The old green ring collided with the (formerly) green density bucket | Hover a calendar cell with `data-snapshot="yes"`, inspect its ring's computed color, and confirm it is violet (`#a78bfa`), not green (`#34d399`). |
| `/data` | Availability heatmap hovered-day readout text ("snapshot yes") | Changed behavior (visual) | Text color token switched to match the new ring color | Hover a calendar cell that has a snapshot and look at the "X/Y symbols · snapshot yes" line above the grid; confirm the words "snapshot yes" render in violet, not green. |
| `/data` | Availability heatmap per-cell tooltip / `aria-label` | Changed behavior (copy) | Names which job (Fetch/Backfill) produced which signal, including calling out a "Backfill gap" | Hover a cell that has bars but no snapshot and read its tooltip text; confirm it reads something like "no snapshot yet — Backfill gap"; then hover a snapshotted cell and confirm its tooltip instead reads "scored snapshot exists (Backfill)". |
| `/data` | Availability heatmap header blurb + caption | Changed behavior (copy) | Names the Fetch→fills / Backfill→scores workflow explicitly | Read the paragraph under the "Per-date availability" heading and the caption under the calendar grid; confirm both explicitly state that Fetch fills price data and Backfill produces scored snapshots. |

---

## Backend-Only Changes (No UI Impact)

- `apps/backend/tests/test_data_manager.py` — fixed 2 pre-existing tests that hardcoded the old context-only symbol universe as the fetch job's expectation, and added 2 new tests (Fetch-scope coverage of the 548 pool + context; `compute_availability` byte-identical-output regression guard). Tests only; no UI surface.
- `apps/backend/tests/test_data_manager_jobs_pipeline.py` — fixed 3 pre-existing tests with the same hardcoded-universe issue. Tests only; no UI surface.
- `apps/backend/tests/test_data_manager_parallel.py` — fixed 7 pre-existing tests (explicit `seed_dir` pinning or monkeypatch-target retargeting from `all_seed_symbols` to `price_load_symbols`), found by the developer's own sweep beyond the plan's file list. Tests only; no UI surface.
- `apps/backend/scripts/benchmark_pipeline.py` — standalone offline benchmarking script (not part of the served product, not run by pytest, not triggered from any UI); retargeted its own monkeypatch to avoid an `AttributeError` after the import rename. No UI surface.

---

## Summary

- **Frontend surfaces changed:** 1 route (`/data`) — 13 distinct UI elements affected within it (see table above)
- **New pages/routes:** 0 (no new page, no route change — J-13's canonical home `/data` was already registered)
- **Modified components:** 4 frontend files changed (`app/data/page.tsx`, `components/availability-heatmap.tsx`, `app/globals.css`, `tailwind.config.ts`); 1 sub-component removed entirely (`ExpandScreenResult`)
- **Navigation changes:** no
- **Backend-only changes:** 4 (3 test files + 1 offline benchmarking script); 1 additional backend file (`data_manager.py`) has an indirect UI effect and is captured in the surface map above, not here
