# Phase goal-mcp-loop-iter-21 — User-Visible Changes

**Phase:** goal-mcp-loop-iter-21
**Date:** 2026-07-08
**Written by:** ui-impact-analyst

**Status:** Verification-only iteration — zero product-source diff. `git diff HEAD` on every J-13
implementation file (`apps/backend/app/engine/data_manager.py`, `apps/frontend/app/data/page.tsx`,
`apps/frontend/components/availability-heatmap.tsx`, `apps/frontend/app/globals.css`,
`apps/frontend/tailwind.config.ts`) is confirmed empty against current HEAD
`6b0f9618683e7dc77ac7e33ef128b522de6b41a4` (one commit past `aac9abc`, the commit that actually
carries the changes described below; the intervening commit touches only iter-20 showcase
artifacts). Per the execution plan's UI Evolution note, **this is not a "nothing changed" stub** —
it restates the already-committed iter-20 J-13 capabilities because they are exactly the surfaces
this iteration's canonical `browser-qa-agent` run exists to prove live. Every bullet below
describes a capability that already existed as of iter-20; iter-21 changes none of it and adds no
new capability — it only produces the first real (not code-inspected) browser evidence that it
works.

---

## What Users Can Now Do

*(Shipped in iter-20; unchanged this iteration. Restated here because iter-21's entire purpose is
to prove these live against a running stack, not to add anything new.)*

- On the `/data` "Per-date availability" calendar, users can tell at a glance whether a trading day
  has complete stored price data versus a scored (immutable) snapshot — the legend is split into
  two separately labeled groups ("Price data — cell fill" and "Scored snapshot — indicator") using
  two visually distinct colors (blue cell fill, violet ring), so the two signals can no longer be
  confused the way a green density bucket and a green snapshot ring previously could be.
- Users can hover any calendar cell on that same heatmap and read a tooltip that names which job
  produced what they're looking at — e.g., a cell with price bars but no snapshot reads "no
  snapshot yet — Backfill gap," while a scored cell reads "scored snapshot exists (Backfill)" —
  instead of an unlabeled "snapshot yes/no."
- Users who click "Fetch EOD prices" or "Fetch + backfill" on `/data` get the full ~548-name
  committed stock pool refreshed alongside the ~162 benchmark/context symbols already covered (588
  symbols total). This happens automatically inside the existing "Start" action — no new button or
  option was added.

---

## What Changed in the Visible UI

*(This is the iter-20 change set — the last time any of these surfaces actually changed. No
further UI change ships in iter-21; every fact below is being re-confirmed live, not re-applied.)*

- The "Job kind" dropdown on `/data` lists exactly three options — "Backfill snapshots," "Fetch EOD
  prices," "Fetch + backfill" — with no "Expand universe" option anywhere.
- The "Import source" dropdown (shown for Fetch / Fetch+backfill) no longer disables any option,
  appends "cannot supply market cap" suffix text, or can trigger the amber "cannot supply market
  cap — not selectable for an expand job" alert under any combination — every option now simply
  reads "· available" or "· needs key."
- The job-form panel heading reads "Start a fetch / backfill job" (previously "... / expand job"),
  and its explainer paragraph now states Fetch "covers the full committed symbol pool" instead of
  describing a market-cap screening step.
- A job's progress card no longer shows a "Universe screen" section ("N passed" / "N omitted"
  badges plus an omitted-candidates list) under any circumstance — that block only ever rendered
  for the now-removed Expand job kind.
- The "Per-date availability" legend changed from one row labeled "Coverage" into two labeled rows:
  "Price data — cell fill" (6 blue swatches, dark to bright) and "Scored snapshot — indicator" (one
  violet-ringed swatch).
- The 6-step density color ramp changed from a multi-hue progression (slate → blue → cyan →
  teal-green → green → amber) to a single-hue blue ramp; the "full coverage" bucket is now bright
  blue (`#a6c8f2`), not amber (`#f0b429`).
- The ring around a snapshotted calendar cell, and the "snapshot yes" text in the hovered-day
  readout above the grid, changed from green (`#34d399`) to violet (`#a78bfa`).
- The heatmap's header blurb and grid caption were reworded to explicitly say Fetch fills price
  data and Backfill produces scored snapshots.

---

## What Old Behavior Changed

*(Also from iter-20 — carried forward, not re-changed this iteration.)*

- Clicking "Fetch EOD prices" or "Fetch + backfill": previously refreshed only the ~162-name
  benchmark/context symbol set. It now also refreshes the full ~548-name committed pool (588 total)
  — the job's progress card shows a much larger "X of Y symbols" denominator and the job runs
  longer to completion.
- The only in-UI path to refresh company market-cap figures on demand (the "Expand universe" job)
  is gone. Market caps keep displaying whatever value is already on file; no control on `/data`
  refreshes them anymore.
- The availability heatmap's legend, color ramp, and ring color all look different from before,
  even though the underlying numbers behind them (`symbols_with_bars`, `total_symbols`,
  `snapshot_exists`) are byte-identical to what was served previously — this was a
  re-coloring/re-labeling of the same data, not a new data source or new computation.

---

## Not Visible Yet

- The backend still accepts an `"expand"`-kind job and its market-cap-refresh logic
  (`get_market_caps`) still works if invoked directly, but `/data` offers no button, dropdown
  option, or path to trigger either from the browser. The only remaining way to run that screening
  step is the offline `scripts/screen_universe.py` script, outside the web UI. (Unchanged from
  iter-20; iter-21 does not touch or plan to expose this.)

---

## What This Iteration Actually Adds (Not a UI Change — a Verification Change)

Iter-20 shipped every capability above, but its canonical `browser-qa-agent` run blanket-SKIPped —
both services were unreachable at precondition (`curl` returned `000` on `:3255`/`:8255`), so the
evidence directory came back empty and `phase-closure` returned CLOSURE-FAIL, even though the code
itself was independently confirmed correct by every other gate (review PASS, audit
PASS_WITH_GAPS, coherence PASS, a live but non-canonical ux-regression DOM/computed-style spot
check). Iter-21's job is entirely operational, not visual: bring both prod-mode services up
cleanly (clearing the stale `.next` bundle first so a pre-iter-20 build can't be silently
re-served), confirm both are actually reachable, and have the real canonical `browser-qa-agent`
lane click through the surfaces above plus five pre-existing, functionally unrelated journeys that
iter-20's SKIP never got to live-replay:

- `/stocks` — the "Sector" column header still re-sorts the leaderboard without crashing (J-01).
- `/stocks` — the Leadership/Entry Quality/Risk score badges still read "Not yet proven" (J-03).
- `/evidence` — the ledger page still renders its empty-state or claim list (J-05).
- `/stocks/{ticker}` — the "Full history" deep-history chart toggle still renders (J-10).
- `/methodology` and `/stocks` — the universe/symbol count shown on each still agrees (J-12).

None of these five carries any code change this iteration or last — they are included because a
real user could reach every one of them in the same browsing session as `/data`, and the phase's
Definition of Done requires seeing them pass live (not merely assumed unaffected) before the
overall goal-mode loop can consider J-13 — and the wider product — verified.
