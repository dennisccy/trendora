# Iteration State — market-compass

**After iteration:** 1 · **Date:** 2026-08-20 · **Verdict:** CONTINUE

## Journeys

1 partial (J-01 — substance verified, capture missing) · 7 failing (J-02..J-08) — 8 total

## Active blockers

- **dev (passenger task, NOT an iteration goal):** J-01 capture gap — no screenshot of `/stocks` at
  as-of 2026-08-12 showing 0 "Unassigned" / GRMN = Consumer Discretionary, and no `[NEW]` walkthrough
  (demo recorder JSON parse error). Run 3081 already exists — no data prep needed.
- **human (owner):** `docs/goal.md` J-01 step 1's Remove+backfill precondition is destructive and
  unrecoverable here (audit T2 — it destroyed 2026-08-13/14 bars this run); step 2's "select the
  Unassigned filter option" is unexecutable at 0% (option honestly disappears, F1). Needs rewording.
- **infra:** restart backend/frontend before browser-qa — this run's QA hit a stale uvicorn process.

## Last 2 verdicts

- iter 1: CONTINUE — J-01's fallback + disclosure work and were verified live (0/539 Unassigned;
  disclosure card screenshotted), but the browser lane FAILed on a destructive precondition and a
  stale backend, so J-01 stays `partial` on evidence, not on behavior.
- iter 0: CONTINUE — baseline only, no code changed; 0 passing / 1 partial / 7 failing measured.

## Do not redo

- **J-01 backend fallback — DONE, live-verified.** `scoring.py:453-458` (`cfg.stock_sectors.get(t) or
  pool_sectors.get(t)`, computed once at `:303`) + `universe_screen.pool_sector_map`. 0/539
  Unassigned on run 3081 (as-of 2026-08-12), was 78.4%. No second reader.
- **J-01 methodology disclosure — DONE, visible.** `_sector_basis()` (`engine/methodology.py:79`)
  emits a SIBLING top-level `sector_basis`; `SectorBasisCard` (`app/methodology/page.tsx:303`); prose
  in `config.methodology.universe_selection.sector_basis`. Never re-nest it inside
  `universe_selection` — the J-22 gate pops that section and would hide it again. Evidence:
  `reports/qa/goal-market-compass-iter-1-evidence/AUDIT-01-methodology-sector-basis-visible.png`
- **J-01 honesty half — settled** (iter-0, re-confirmed iter-1): single stored source, unknown →
  null/"Unassigned", leaderboard + detail + API agree.
- **TC-4 byte-identity + TC-8 immutability — proven** (fixtures + production rows 3049 vs 3081).
- **`universe.pool_sector_aliases` stays empty** (TC-6 no-op); do not re-run J-01's Remove+backfill
  precondition as written — use run 3081.
