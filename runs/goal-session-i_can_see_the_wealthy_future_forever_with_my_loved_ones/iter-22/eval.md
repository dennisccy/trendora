# Iteration 22 Evaluation

**Verdict:** CONTINUE
**Depth Recommendation For Next Iteration:** full

## Summary

Iter-22 delivered both target journeys cleanly at lean depth, frontend-only, with a verified zero-backend diff: J-79 (as-of ◀/▶ stepper buttons, opt-in field-guarded ←/→ arrow keys, calendar Year/Month quick-jump) and J-80 (Stocks header regime label+score + ranked Top-Themes strip + `#n` chip badges). Browser QA passed 15/15 (2 targets + 13 required-still-passing), coherence is COHERENCE-PASS, and the reviewer returned PASS with no fix tasks and no scope creep. This is NOT GOAL_ACHIEVED only because two buildable (non-data-dependent) Must-have journeys queued in goal.md — J-81 and J-82 — remain unbuilt (status `unknown`); both were explicitly deferred from this lean iteration to a full-depth backend iteration.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-79 (as-of stepping: buttons + opt-in arrows + year/month) | (new, not in history) | passing | reports/qa/.../iter-22-evidence/UT-J-79-step-buttons-pass.png, UT-J-79-field-guard-pass.png, UT-J-79-year-dropdown.png |
| J-80 (Stocks header regime + Top-Themes strip + #n badges) | (new, not in history) | passing | reports/qa/.../iter-22-evidence/UT-J-80-stocks-header.png, UT-J-80-latest-repoint.png |
| J-18 (one date control — critical anti-goal) | passing | passing | UT-J-18 (no page-local select on /backtest) |
| J-43 (deep-linkable ?asof) | passing | passing | UT-J-43 |
| J-50 (asof survives every nav) | passing | passing | UT-J-50 (10 nav links carry ?asof) |
| J-62 (calendar popover selectable dates) | passing | passing | reports/qa/.../iter-22-evidence/UT-J-79-calendar-open.png |
| J-71 (keyboard stepping with panel open) | passing | passing | UT-J-71 |
| J-13 (browse dashboard as-of past date) | passing | passing | reports/qa/.../iter-22-evidence/UT-J-79-historical-selected.png |
| J-06 (score consistency across pages) | passing | passing | UT-J-06 (NVDA 40.54/69.55/32.59 leaderboard==detail) |
| J-02 (leaderboard filters) | passing | passing | UT-J-02 |
| J-03 (theme leaderboard) | passing | passing | UT-J-03 |
| J-48 (column sorting) | passing | passing | UT-J-48 |
| J-55 (symbol search) | passing | passing | UT-J-55 |
| J-56 (theme column + filter) | passing | passing | UT-J-56 |
| J-75 (forward returns on leaderboard) | passing | passing | reports/qa/.../iter-22-evidence/UT-J-75-fwd-returns.png |
| J-81 (themes/sectors forward-return columns) | unknown | unknown (deferred, not built) | none — out of scope this iter |
| J-82 (Regime×Setup×Pattern NA-sort/filters/N=/Pooled) | unknown | unknown (deferred, not built) | none — out of scope this iter |
| J-22 / J-23 / J-24 | unknown (data-walled) | unknown (data-walled, non-vetoing) | none — no fetch attempted |

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| Single source of truth (six scores / bucket / setup computed once) — critical | OK | /stocks regime + theme rank are byte re-displays of /api/dashboard + /api/themes; coherence Step 1 confirms no recompute; UT-J-06 confirms NVDA 40.54/69.55/32.59 leaderboard==detail; UT-J-80 confirms /stocks regime 57.10 == Dashboard 57.10 same date. |
| No recompute in the read path | OK | Zero backend diff (git diff --stat HEAD -- apps/backend is empty); both header values read from already-served endpoints. |
| Exactly one date selector — critical | OK | ◀/▶ buttons, opt-in keys, and year/month dropdowns all drive the single `setAsOf` via the asof-provider (sole ?asof owner); year/month dropdowns move the viewed-month cursor only (UT-J-79 Step 3 — URL stayed ?asof=2026-06-10); field-guard verified (UT-J-79 Step 5); J-18/J-71 regressions green. Coherence Step 1 + 2 confirm no second/page-local date state. |
| No magic numbers | OK | No backend calc-code change; the prior iter-20 `_rsp_rank_key` float-literal violation was resolved in iter-21. New display constants (MONTH_NAMES, TOP_THEMES_STRIP_LIMIT=5) are presentation-only, flagged advisory by coherence, not scoring literals. |
| No fabricated data | OK | Honest empty states ("No regime for this date" / "No ranked themes for this date"); #n badge absent when no served rank; forward returns NA at latest (UT-J-75). |

## Next-Step Recommendation

Plan the two deferred buildable Must-haves at **full depth** (each needs the full pytest gate per the iter-21/iter-22 standing rule for any backend-touching journey):

1. **J-81** — forward-return columns (1/5/10/20/60-day) on the Themes and Sectors leaderboards, read from the stored `forward_returns` table via the SAME `_leadership_returns` builder Backtest uses (sector = ETF's own stored return; theme = equal-weight member basket). The coherence keystone: a theme/sector forward return must read identically on its leaderboard and on Backtest for the same date+horizon (J-81 canonical-value row). Full depth so the Backtest-coherence pytest assertions gate it.
2. **J-82** — Regime × Setup × Pattern table NA-last sorting + Regime/Setup/Pattern column filters + Pooled default + the `N=` drill-down 422 fix (samples-validation reconciliation over the stored event-study observation set). Full depth so the samples count-coherence + validation suite gates it.

Both are explicitly NOT data-dependent (goal.md:2146-2152) and verifiable offline against the committed seed. The dev handoff already recommends exactly this pairing. After J-81 and J-82 land green with a full suite GREEN, every buildable Must-have will be passing and J-22/J-23/J-24 remain honestly blocked-NA (non-vetoing) — at which point GOAL_ACHIEVED is appropriate.

## Halt Justification

Not halting. Progress was made (J-79 + J-80 newly passing, zero regressions, zero anti-goal violations), and two tractable buildable Must-haves (J-81, J-82) remain with a clear, specified next step.
