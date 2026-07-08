# Phase goal-mcp-loop-iter-20 — User-Visible Changes

**Phase:** goal-mcp-loop-iter-20
**Date:** 2026-07-07
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

- Users can now tell, at a glance, whether a given trading day on the `/data` "Per-date availability" heatmap has complete stored price data versus an immutable scored snapshot — the two signals now sit in two separately labeled legend groups and use non-colliding colors (a blue cell fill vs. a violet ring), where previously a green density bucket and a green snapshot ring could look confusingly similar.
- Users can now hover any calendar cell on that heatmap and read a tooltip that explicitly names which job produced the signal they're looking at — e.g. "no snapshot yet — Backfill gap" for a day that has price bars but hasn't been scored, or "scored snapshot exists (Backfill)" for a day that has — instead of a bare "snapshot yes/no".
- Users who click "Fetch EOD prices" (or "Fetch + backfill") on `/data` now get the full ~548-name committed stock pool refreshed, in addition to the ~162 benchmark/context symbols it already refreshed (588 symbols total). No new button or option is needed — this happens automatically inside the existing Fetch action.

---

## What Changed in the Visible UI

- The job-kind dropdown on `/data` no longer offers "Expand universe" — it now lists exactly three options: "Backfill snapshots", "Fetch EOD prices", "Fetch + backfill".
- The import-source dropdown (shown when the job kind is Fetch or Fetch+backfill) no longer disables any option or appends "cannot supply market cap — not selectable for expand" text — every source now simply reads "\<name\> · available" or "\<name\> · needs key".
- The amber "cannot supply market cap — not selectable for an expand job" alert box that could previously appear below the source picker is gone; it can no longer render under any input combination.
- The panel title above the job form changed from "Start a fetch / backfill / expand job" to "Start a fetch / backfill job", and its hover hint no longer mentions "expand".
- The explanatory paragraph below the job form no longer describes screening the candidate pool for market cap or listing omitted candidates; it now states plainly that Fetch "covers the full committed symbol pool."
- A job's progress card no longer shows a "Universe screen" section (a "N passed" / "N omitted" badge pair plus an omitted-candidates list) under any circumstance — that block only ever appeared for an Expand job, which can no longer be started.
- The "Per-date availability" heatmap's legend changed from a single row labeled "Coverage" (6 color swatches plus a small green-ringed "snapshot" swatch) into two clearly separate, labeled groups: "Price data — cell fill" (6 blue swatches, dark to bright) and "Scored snapshot — indicator" (a violet-ringed swatch with the text "a scored snapshot exists for that day").
- The heatmap's 6-step density color scale changed from a multi-hue progression (slate → blue → cyan → teal-green → green → amber) to a single-hue blue ramp (dark → bright); the "full coverage" bucket is now a bright blue, not amber.
- The ring drawn around a calendar cell that has a scored snapshot changed from green to violet, and the "snapshot yes" text in the hovered-cell readout above the grid changed from green to that same violet.
- The heatmap's header blurb and the caption below the grid were reworded to spell out, in plain language, that Fetch fills price data and Backfill produces scored snapshots.

---

## What Old Behavior Changed

- Clicking "Fetch EOD prices" (or "Fetch + backfill"): previously refreshed only the ~162-name benchmark/context symbol set. It now refreshes that same set plus the full ~548-name committed stock pool (588 symbols total). The job's progress card will show a much larger "X of Y symbols" total and progress-bar denominator, and the job will take longer to reach completion.
- The only in-UI way to refresh company market-cap figures on demand (the "Expand universe" job) is gone. Market caps continue to display the values already on file; there is no longer any control on `/data` that refreshes them.
- The availability heatmap's legend, color ramp, and snapshot-ring color all look different from before, even though the underlying numbers behind them (`symbols_with_bars`, `total_symbols`, `snapshot_exists`) are byte-identical to what was served before this change — this is a re-coloring/re-labeling of the same data, not new data.

---

## Not Visible Yet

- The backend still accepts an "Expand universe" job (`kind: "expand"`) and its market-cap-refresh logic (`get_market_caps`) still exists and works if called directly, but `/data` no longer offers any button, dropdown option, or path to trigger either from the browser. The only remaining way to run that screening step is the offline `scripts/screen_universe.py` script, which is outside the web UI.
