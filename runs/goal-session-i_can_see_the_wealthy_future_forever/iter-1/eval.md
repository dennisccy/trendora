# Iteration 1 Evaluation

**Verdict:** CONTINUE
**Depth Recommendation For Next Iteration:** full

## Summary

The lean, single-file Backtest consolidation landed exactly as scoped: `/backtest` now reads the one
global `useAsOf()` switcher and holds no date state of its own. **J-18** flips `failing → passing` and
**J-13** flips `partial → passing` (no extra code — it rides the same flow), the session's only live
anti-goal violation ("Exactly one date selector") is **resolved**, coherence is **PASS**, and no
journey regressed. Not GOAL_ACHIEVED — J-17 (Data Manager) and J-19 (return attribution) remain
`failing` and five iter-0 journeys remain `partial`.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-18 One date control (no duplicate) — **target** | failing | **passing** | reports/qa/goal-i_can_see_the_wealthy_future_forever-iter-1-evidence/UT-J-18-backtest-latest-no-picker.png, UT-J-18-backtest-historical-2025-05-28.png, UT-J-18-stocks-same-date-persists.png |
| J-13 Browse dashboard as-of past date — **target** | partial | **passing** | reports/qa/goal-i_can_see_the_wealthy_future_forever-iter-1-evidence/UT-J-13-dashboard-historical-2025-05-28.png |
| J-14 Backtest forward-test scorecard | already_passing | passing (re-verified) | reports/qa/goal-i_can_see_the_wealthy_future_forever-iter-1-evidence/UT-J-14-backtest-latest-NA.png, UT-J-18-backtest-historical-2025-05-28.png |
| J-01 Daily dashboard at a glance | already_passing | passing (re-verified) | reports/qa/goal-i_can_see_the_wealthy_future_forever-iter-1-evidence/UT-J-01-dashboard-latest.png |
| J-03 Theme Leaderboard | already_passing | passing (re-verified) | reports/qa/goal-i_can_see_the_wealthy_future_forever-iter-1-evidence/UT-J-03-themes-historical-expanded.png |
| J-04 Sector / industry Leaderboard | already_passing | passing (re-verified) | reports/qa/goal-i_can_see_the_wealthy_future_forever-iter-1-evidence/UT-J-04-sectors-historical.png |
| J-05 Stock Detail with explainable scores | already_passing | passing (re-verified) | reports/qa/goal-i_can_see_the_wealthy_future_forever-iter-1-evidence/UT-J-05-stock-detail-nvda.png |
| J-02, J-06, J-11, J-15, J-16 | partial | unchanged (out of scope) | carried from iter-0 |
| J-07, J-08, J-09, J-10, J-12 | already_passing | unchanged (not re-tested) | carried from iter-0 |
| J-17 Data Manager, J-19 Attribution | failing | unchanged (out of scope) | carried from iter-0 |

### Verification notes (skeptical, per the iter-0 lesson)

- **J-18 source gate (mandatory):** confirmed directly in `apps/frontend/app/backtest/page.tsx` — line 6
  imports `useAsOf`, line 54 consumes it, line 78 keys the data effect on `[asOf]`; the only `useState`
  (line 55) is the loading/ok/error machine; there is **no** `<Select>`, `BacktestDatePicker`,
  `fetchRuns`, or `selected`/`dates`/`latest`/`ready` state anywhere in the 418-line file. The
  "Viewing as-of" badge (lines 92–106) is display-only, re-derived from `state.backtest.asof_date` /
  `asOf`. Not passed on a screenshot alone.
- **Diff scope:** `git diff HEAD` touches one source file only — `apps/frontend/app/backtest/page.tsx`
  (17 +/81 −); the rest is session bookkeeping (telemetry/trace/session.json). Surgical, matches spec.
- **Screenshots inspected:** Backtest-latest shows the global switcher + badge but no page-local AS-OF
  dropdown; selecting 2025-05-28 re-points the scan summary (regime 74.32 → 68.91, sectors SOXX→XAR) AND
  the scorecard; `/stocks` then shows the same 2025-05-28 — one resolved date everywhere. J-14 latest
  honestly shows all-NA (n=0) with "No numbers are fabricated."

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| Exactly one date selector (extends Single source of truth) | **RESOLVED** | The iter-0 live violation (Backtest page-local `BacktestDatePicker` + own date state) is deleted; the page now consumes the single global provider. Confirmed in source + coherence audit. Marked `resolved: true` in journey-history. |
| Single source of truth (critical) | OK | No score/return/bucket/date computed on the page; all values read from existing endpoints for the resolved `asOf`. No new computation or endpoint. |
| No recompute in the read path | OK | The badge re-formats the canonically-echoed `asof_date`; no client recomputation. Coherence Part A: PASS. |
| No fabricated data / honest partial windows | OK | Scorecard NA (n=0) + low-sample `⚠` + empty-state preserved; latest date shows honest NA. |
| No-lookahead / immutable snapshots (critical) | OK | No backend, engine, or data-model change (backend pytest 248/0 unchanged). |
| No order/execution path, no secrets | OK | Frontend-only refactor that removes code; nothing introduced. |

**Coherence audit:** COHERENCE-PASS (no Data-Contract or Information-Architecture violation; the change
*removes* a divergent date source). No structural veto.

## Next-Step Recommendation

Proceed to **J-19 — return attribution** at **full** depth (the spec's planned iter-2). Surface the four
attribution layers — per-stock top contributors & detractors, by-sector, by-rank-band (1–10 / 11–50 /
51+), and distribution & hit-rate (median, % positive, dispersion) — on **/system-health** (aggregate)
and **/backtest** (per-date), now that Backtest reads the clean global date control. Honor the critical
anti-goal **"Attribution is read-only"**: every slice MUST be derived once from the stored
per-observation forward returns (never recomputed in the API or a view), with honest n / NA for
low-sample slices. Full depth is warranted: a new registered contract value spanning two pages, likely
backend derivation work, and a critical-family anti-goal — none of which apply to a single-file
frontend refactor.

Lower-cost follow-on (decomposer's discretion): the Chrome-MCP layer was **fully functional** this
iteration (31 clean states), so the five iter-0 `partial`s (J-02 filters, J-06 leaderboard==detail,
J-11 add+restart, J-15 warm-load, J-16 VCP filter) are likely convertible by re-verification alone (no
code change — exactly how J-13 converted here). They can be folded into J-19's regression set or swept
in a cheap lean pass.

## Halt Justification

Not halting. Progress was made (2 journeys newly passing, 1 anti-goal violation resolved, 0
regressions), and clear, tractable next work remains (J-19, J-17, plus five convertible partials), so
the loop continues.
