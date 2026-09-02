# Iteration State — market-compass

**After iteration:** 40 · **Date:** 2026-09-02 · **Verdict:** GOAL_ACHIEVED

## Journeys

15 passing (J-01..J-15) · 0 failing · 0 unknown — 15 total. All Must-have journeys met.

## Active blockers

- none. Evidence debt only (never blocking, never a round of its own): walkthrough films owed for
  J-05, J-06, J-12, J-14 (retake from the "Not priority" list) and J-15 (`[NEW]` flag), plus one
  photo of "— not recorded" at an older as-of (e.g. 2001-04-17) — proven in code, not on screen.
- Owner decisions, not dev work: (1) the depth ladder cut a `full` spec to `lean` on budget grounds
  (`engine.log:8447`) — 2nd cut in 3 rounds, on the round that shipped a new journey; (2) 3rd round
  running, the boilerplate reconciliation footer turned a replay FAIL into a merged PASS, this time
  alongside an UNDECLARED post-failure golden edit (`J-02.json` "(36)"→"(79)" at 10:08:08).

## Last 2 verdicts

- iter 40: GOAL_ACHIEVED — J-15 built and verified; I re-derived 57 crossings = 10 shown + 43
  suppressed + 4 residual (TRV/SJM/ALL/TTWO) from stored runs 3157/3158 read-only, read the new lines
  out of the screenshot, confirmed old as-of dates still render, and closed the last anti-goal entry
  (iter-39's minor AG-8). All gates exit 0; coherence PASS; scan CLEAN.
- iter 39: CONTINUE — the iter-38 AG-8 crash repaired, six regressed journeys restored, four tampered goldens reverted byte-exact; only J-15 remained unbuilt.

## Do not redo

- **J-15 is DONE** — `session_delta.py::_stock_changes` classifies the full `crossing_pairs` list
  BEFORE the `max_stock_items` bound; `stock_accounting` served by `compute_delta`; disclosure lines
  in `compass-whatchanged-card.tsx:79-85, 102-112` via `lib/stock-accounting-summary.ts`.
- **The AG-8 `gating` fix is DONE** — `api.ts` `gating?: boolean` + `gatingSuffix()` 3-state render
  (`undefined` → "— not recorded"), single call site `compass-focus-section.tsx:166`.
- **The J-04/J-14 goldens are repaired** (declared in advance; as-of unchanged) and re-pass replay.
  Never re-point a golden at a same-day-minted date, and never edit one after a FAIL.
- **The iter-38 AG-8 crash repair stands** (iter-39) — old manifests render; re-verified this round
  at `/?asof=2026-03-30`, `2026-07-23`, `1996-02-01`.
- **Manifest immutability holds** — 37 rows / 23 as-of dates, +1 additive v11, 0 mutated/deleted; v7
  export md5 `d905dcfeb788…` for a 6th round. Never rewrite a row, never retune `max_stock_items`
  (10, DISPLAY cap only) or `stock_score_min_change` (8.0) — AG-15.
