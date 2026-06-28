# goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-56 Frontend Handoff

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-56
**Date:** 2026-06-28
**Agent:** developer
**Status:** complete

## What Was Built (UI)

Two pure presentation / information-architecture changes — same labs, same figures (byte-identical), clearer order. No new surface, no new action, no new data.

- **J-113 — `/research` hub card order.** The hub grid (`data-testid="research-hub"`) now reads regime/phase/factor-first: Factor Lab → Regime Lab → Market Phase & Severity Lab → Regime × Phase × Factor → Regime × Setup × Pattern → Severity-velocity × Regime → Multi-factor combination → Setup & Pattern event study → Recovery-Turn Edge → Downtrend Opportunity. All ten cards keep their route, icon, title, description, hover/focus states, and `?asof`-stamped href.
- **J-114 — de-interleaved per-horizon columns.** On the four all-horizon lab tables (Factor Lab all-factors table + its expandable decile grid, Regime Lab by-label + by-decile, Phase & Severity by-label + by-decile, Regime × Phase × Factor), the per-horizon columns now show all `Fwd Xd` columns first (1/5/10/20/60d), then all `MDD Xd` columns — matching the `/stocks` · `/themes` · `/sectors` leaderboard grouping. Headers, body cells, and sort affordances all follow the grouped order; sort still works on a forward-return column and a max-drawdown column (resolve sort buttons by `aria-label`, e.g. "Sort by Fwd 5d" / "Sort by MDD 5d", per the iter-27/28b lesson).

## Surfaces touched

- `/research` (hub card order)
- `/research/factor-lab`, `/research/regime-lab`, `/research/phase-severity-lab`, `/research/regime-phase-factor` (column order)

## Design-system conformance

No new visual tokens, effects, colours, or components. Colour-grading (`returnClass` / `mddClass`), NA-honesty (explicit muted "NA" on low-sample / empty / null), loading/empty/error states, and responsive overflow-x wrappers are unchanged. Only column position and card order changed.

## Verify

- J-113 live: rendered `/research` HTML lists `research-lab-link-*` in the exact order above.
- J-114: on each of the four lab pages, the header row shows all `Fwd Xd` columns before all `MDD Xd` columns (no `Fwd → MDD → Fwd` alternation); expand a Factor Lab row → its decile grid uses the same grouped order; a sort on a `Fwd` column and on a `MDD` column still reorders the rows; an NA forward-return cell still shows its paired NA drawdown (no fabricated fill).
- Servers left up for browser QA: backend `http://localhost:8255`, frontend `http://localhost:3255`.
