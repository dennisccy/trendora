# Iteration State — market-compass

**After iteration:** 39 · **Date:** 2026-09-02 · **Verdict:** CONTINUE

## Journeys

14 passing (J-01..J-14) · 0 failing · 0 regressed · 1 unknown/never-built (J-15) — 15 total.
Gates: results 0 · journeys 1 `blocking:["J-15"]` · regressions 0 · coherence 0 · drift `changed:[]`.

## Active blockers

- **J-15 "What changed accounts for every stock-level crossing"** — never built, sole GOAL_ACHIEVED
  blocker. Owner: dev. Spec `docs/goal.md:2543`; target `apps/backend/app/engine/session_delta.py`.
- **Minor AG-8, unresolved (ledger 11 / 1 open):** `WhyNotFailedCondition.gating` still required at `apps/frontend/lib/api.ts:1051` but absent on all 21 pre-iter-38 as-of dates, so `compass-focus-section.tsx:151` labels 26 stored `leadership_min_score` misses "— advisory" on 2001-04-17 / 2005-04-01 / 2020-01-02. No crash. Fix: `gating?: boolean` + honest "not recorded".
- **Two goldens need a DECLARED-IN-ADVANCE repair.** `J-04.json` step 2 clicks the stale literal `Not priority (20)`; `J-14.json` step 3 re-navigates then asserts text inside a `<details>` that `components/ui/disclosure.tsx` never opens. Never edit a golden after it fails without declaring it; never re-point one at a same-day-minted date.
- **Capture debt (passenger only, never a round of its own):** walkthrough frames owed for J-05, J-06, J-12; J-14's step-08 frame is a top-of-page viewport and no step carries `[NEW]`; `UT-10-result.png` came out a 1-colour blank.
- Human-owned, non-blocking: one pre-existing failing test on three untouched files; the 7.8 GB
  iter-23 throwaway copy; `apps/frontend/.next-verify/` still tracked (61 of 65 diff paths).

## Last 2 verdicts

- iter 39: CONTINUE — AG-8 crash repaired at root; all six regressed journeys restored on
  pre-existing dates, J-14 promoted from partial; only J-15 (never built) remains.
- iter 38: REGRESSION — unguarded `why_not_totals` read crashed the Today page on 21 of 23 stored
  as-of dates, regressing six journeys; critical AG-8 violation.

## Do not redo

- **AG-8 crash fix is DONE** (`api.ts` optionality + `lib/why-not-summary.ts` guard; 21/21 dates
  HTTP 200, evaluator opened five repaired pages). Do not re-fix or re-litigate.
- **The four tampered goldens are byte-exact to `ab3cca63`** (re-verified: zero diff); J-05/J-06's
  freeze-stamp assertion and J-07's 7 steps are back. Do not re-restore.
- **J-14's backend logic is correct and untouched**; numbers re-derived against stored row id 35. Do not rebuild it. Its crop gap is CLOSED (`UT-09-result.png`, full 20-entry panel).
- **Do not schedule an evidence-only round** — all remaining capture debt rides as passengers.
- **AG-12/AG-17 immutability re-proven** (36 rows / 23 dates, `prospective_eligible` 0, export v7
  md5 `d905dcfeb788…` for a fifth round). Do not re-audit from scratch.
