# Iteration State — market-compass

**After iteration:** 28 · **Date:** 2026-08-31 · **Verdict:** ESCALATE

## Journeys

7 passing (J-01 J-04 J-05 J-06 J-08 J-10 J-11) · 4 partial (J-02 J-03 J-07 J-09) · 0 failing — 11 total

## Active blockers

- J-07 step 3 (dev): the three `state_band` direction words render "NA" on every servable date —
  `state_band_json` is non-null on 0 of 26 rows in `apps/backend/data/trendora.db`. Words exist and are
  proven by 11 fixture/route tests; all 26 rows were frozen before
  `apps/backend/app/engine/compass.py::build_state_band` existed and manifests are never backfilled.
  Closes with ONE authorized live `GET /api/compass?as_of=<date with no manifest row>` (mints one
  permanent additive row — the plan must name that date and permit no other).
- Depth demotion (human): spec `Depth: full` ran `lean` for the 7th time this session; only the owner
  may add `Depth enforcement: required`. Keep `CHAIN_REQUIRE_FULL_DEPTH`/`CHAIN_MAINTENANCE_ISOLATION` OFF.

## Last 2 verdicts

- iter 28: ESCALATE — J-08 closed on live evidence; J-07 held `partial` (its one new feature is
  invisible on all real data), and a 7th lean demotion shipped a permanent schema change to the
  protected manifests table with no auditor present.
- iter 27: CONTINUE — J-06 closed; the browser lane broke its own date constraint and minted row 26.

## Do not redo

- `/market` relocation and the sidebar Today/Market rename — DONE and live-verified
  (`apps/frontend/app/market/page.tsx`, `components/sidebar.tsx`); J-08 is closed.
- `/`'s six-section reorder, both state-band tiles, breakdown disclosures, AG-13 separation, chart
  removal + link-out, and the no-sectors/themes fetch — all live-verified this iteration
  (`apps/frontend/app/page.tsx`, `components/compass-state-band-card.tsx`). Only step 3's words remain.
- `build_state_band` itself (engine, config key `compass.delta.stress_velocity_flat_band`, additive
  `state_band_json` column, schema entry) — implemented, reviewed, 11 tests re-run green. Do not
  re-implement; only make it observable.
- TC-14 perf addendum — DONE (`reports/perf-budgets.md` Addendum 42) and the on-load network trace.
- The live remove+backfill drill for J-05 step 1 / J-06 steps 1-3 — binding "do not redo" (iter-26).
- Evidence-only work is never an iteration goal: J-04's retake + the J-05/J-06/J-07/J-08 walkthroughs
  ride as passenger tasks.
