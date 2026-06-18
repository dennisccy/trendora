# Phase goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-33 — UI Surface Map

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-33
**Date:** 2026-06-18
**Written by:** ui-impact-analyst

---

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|---------------------|-------------|-------------|--------------|
| `/data` | Coverage block — "Universe" metric | Changed behavior | J-93: universe count is now point-in-time (members resolved at the current as-of date), not a fixed static number | Step the global date switcher to a date before 2022-01; verify the "Universe (as of date)" figure drops below 120 (or to 0 before ~2021-10) and the resolved date label updates |
| `/data` | Coverage block — "Candidate universe" metric | New component | J-93: static screened candidate count added alongside the dynamic resolved count so users can see the total pool vs the currently admitted subset | Navigate to `/data` and verify a "Candidate universe" count appears beside the "Universe (as of date)" value, with a higher or equal number |
| `/data` | `UniverseDiagnosticPanel` | New component | J-94: per-date admitted + excluded-by-reason counts explain why the universe is the size it is at the viewed date | With a post-warm-up date, verify the panel shows an admitted count > 0 and three excluded-by-reason rows (below history / below price / below liquidity) with numeric counts and exact threshold values. Then step to a date before ~2021-10 and verify the panel renders an explicit "empty universe" banner, not an error or spinner |
| `/data` | `MembershipTimelinePanel` — SVG step-function chart | New component | J-96: shows how universe size grew across all snapshot dates as a visual step-function line | Scroll down past the diagnostic panel; verify an SVG chart appears with a rising step-function line using the design-token accent color (not a blank or table-only frame); confirm the chart starts near 0 and rises toward the full count around 2022-01 |
| `/data` | `MembershipTimelinePanel` — per-date entries/exits table | New component | J-96: lists which stocks entered and exited on each snapshot date | In the timeline table, find a date where the size increases from the previous row and verify at least one ticker is listed under "entries" for that date; find a date where size decreases and verify at least one ticker is listed under "exits" |
| `/data` | `MembershipTimelinePanel` — three honest labels | New component | J-96: verbatim survivorship / warm-up / universe-relative honesty labels must appear beside the timeline | Verify three distinct label texts appear in the panel — one mentioning "survivorship", one mentioning "warm-up" or the boundary date, and one mentioning "universe-relative" breadth |
| `/data` | `BackwardHistoryPanel` + confirm modal | New component | J-95(a): confirm-gated "Extend history backward" control with honest blocked/NA state on data-walled host | Click the "Extend history backward" button; verify a confirmation modal appears carrying a survivorship caveat text. Confirm the action; verify a job card appears and eventually shows a blocked / limited-coverage (NA) outcome without throwing an error or crashing the page |
| `/stocks` | Empty-state copy | Changed behavior | J-93/J-94: empty leaderboard at a warm-up date now shows an explanatory warm-up message instead of a generic empty state | Step the global date to a date before ~2021-10; navigate to `/stocks`; verify the empty-state message explicitly references the warm-up window and points to the Data Manager diagnostic — not a generic "no results" or an error page |
| `/stocks` | Stock list rows | Changed behavior | J-93: the leaderboard now shows only the stocks that qualify at the viewed date, so the row count changes with the date | At the latest date verify the list shows 120 rows (not 122); step back to a mid-2022 date and verify the count is lower than at the latest date |
| `/themes` | Theme member counts / rows | Changed behavior | J-93: theme membership reflects the per-date resolved universe — early dates show fewer or zero members per theme | Step to a date around 2021-10 and navigate to `/themes`; verify that theme member counts are smaller than at the latest date, consistent with the smaller universe at that date |
| `/sectors` | Sector member counts / rows | Changed behavior | J-93: sector membership reflects the per-date resolved universe | Step to a date around 2021-10 and navigate to `/sectors`; verify sector member counts are smaller than at the latest date |
| `/scanner-runs` | Scanner run membership rows | Changed behavior | J-93: scanner run results reflect the membership that was resolved at each run's own as-of date | Navigate to `/scanner-runs` and open a run from before 2022-01; verify the stock count in that run is lower than for a run after full membership was reached |

---

## Backend-Only Changes (No UI Impact)

- `apps/backend/app/engine/universe_resolver.py` (NEW) — the per-as-of-date resolver logic (price + ADV + min-history gate from bars ≤ D; market-cap dropped). All of its output is surfaced through the Data Manager diagnostic panel and the membership timeline, and through the stock/theme/sector/scanner-runs pages — no hidden capability.
- `apps/backend/app/engine/scoring.py` — `score_stocks` now iterates the resolver's resolved set instead of the static symbol list. The scoring formulas are byte-identical; the change is internal (membership set source). Visible effect is that scores for stocks outside the resolved set disappear at early dates.
- `apps/backend/app/engine/forward_testing.py` — `forward_symbols_for_run` repointed to per-run stored members ∪ benchmarks. No user-visible forward-returns change for the same resolved membership; internal computation path only.
- `apps/backend/app/engine/universe_screen.py` — `POOL_SURVIVORSHIP_LABEL` + `pool_survivorship()` added. The label is surfaced in the frontend timeline panel labels; the computation is internal.
- `apps/backend/app/engine/methodology.py` — `_universe_selection` two-layer documentation + `per_date_rule`. Visible on the Methodology page Universe Selection section text.
- `apps/backend/tests/test_universe_resolver.py` (NEW) — test file, no UI impact.
- `apps/backend/tests/test_iter33_dynamic_universe.py` (NEW) — test file, no UI impact.
- `apps/backend/tests/test_no_magic_numbers.py` — test file, no UI impact.
- `apps/backend/tests/test_api_data.py` — test file (stale `macro` guard fixed), no UI impact.
- `apps/backend/tests/test_data_manager.py` — test file, no UI impact.
- `apps/backend/tests/test_universe_screen.py` — test file, no UI impact.
- `apps/backend/tests/test_iter27_rebuild_mdd.py` — test file, no UI impact.

---

## Summary

- **Frontend surfaces changed:** 10 (Data Manager coverage metric ×2, UniverseDiagnosticPanel, MembershipTimelinePanel chart, MembershipTimelinePanel entries/exits table, MembershipTimelinePanel honesty labels, BackwardHistoryPanel + modal, /stocks empty-state, /stocks row count, /themes + /sectors + /scanner-runs member counts)
- **New pages/routes:** 0 (all new surfaces land on existing pages)
- **Modified components:** 3 files changed — `apps/frontend/lib/api.ts`, `apps/frontend/app/data/page.tsx`, `apps/frontend/app/stocks/page.tsx`
- **Navigation changes:** no
- **Backend-only changes:** 13 files (engine modules, test files — all outputs surfaced through existing or new UI panels)
