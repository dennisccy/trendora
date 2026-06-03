# Phase goal-i_can_see_the_wealthy_future_forever-iter-15 — UI Surface Map

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-15
**Date:** 2026-06-03
**Written by:** ui-impact-analyst

---

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/research` | `SubjectLeaderboardLink` (accent link, `data-testid="subject-leaderboard-link"`) in `EventStudyLab` card | New navigation | J-31: bridge lab evidence to the names expressing it | In the Setup & Pattern Lab, select pattern `pullback_to_rising_dma`, let it finish loading, click "View the names expressing this on the leaderboard →"; confirm it navigates to `/stocks?pattern=pullback_to_rising_dma__only` with the Pattern dropdown pre-set and a narrowed `visible/total` count. |
| `/research` | `SubjectLeaderboardLink` for a **setup** subject | New navigation | J-31: cross-link works for setup subjects too | Select setup `Breakout-watch`, click the link; confirm URL is `/stocks?setup=Breakout-watch` and the Setup dropdown is pre-applied. |
| `/research` | `SubjectLeaderboardLink` for a **low-sample / NA** subject + synthesis caption | New behavior | Link renders even when event-study sample is NA (expressing-names set is independent) | Select a subject whose event study shows NA / low sample; confirm the cross-link still renders and the caption asserts no name count. |
| `/stocks` | `StocksInner` filter state init from URL (`useSearchParams`, lazy) | Changed behavior | J-31: deep-linkable pre-filtered leaderboard | Open `/stocks?pattern=pullback_to_rising_dma__only` directly in a fresh nav; confirm the Pattern dropdown is pre-selected and only matching rows show. |
| `/stocks` | Sector / Setup / Pattern `Select` dropdowns → URL reflect (`router.replace`, `{scroll:false}`) | Changed behavior | J-31: shareable/bookmarkable filtered view | Change the Sector dropdown to a value (e.g. `Energy`); confirm the address bar updates to `/stocks?sector=Energy` without a scroll jump, and rows narrow accordingly. |
| `/stocks` | Unrecognized / absent param fallback (`parsePatternParam` validator) | Changed behavior | Robustness: bad param must not crash or fabricate a filter | Open `/stocks?pattern=garbage_value`; confirm no crash and the Pattern filter falls back to "all" (full list shown). |
| `/stocks` | Zero-match filter | Changed behavior | Honest empty-state preserved under deep-link | Open a deep-link whose filter matches no rows for the current date; confirm the existing honest empty-state shows (no fabricated rows). |
| `/stocks` | `<Suspense fallback={<StocksSkeleton/>}>` wrapper around `StocksInner` | Updated layout | Next 15 build requires a Suspense boundary around `useSearchParams()` | Load `/stocks`; confirm the page renders (transient skeleton then content) and the production build prerenders `/stocks` as static. |
| `/stocks` ↔ top-bar | Global as-of switcher vs. deep-linked filter (J-18 anti-goal) | Changed behavior | Exactly one date control must remain; filters must not become a second date state | With a filter deep-linked, toggle the top-bar as-of; confirm via DOM + network that the filter stays intact, the page re-points by date, and **no `as_of` appears in a leaderboard fetch** — exactly one date control. |
| `/stocks/[ticker]` | (downstream landing — unchanged code) | Changed behavior (reached via new path) | J-31 travel ends at Stock Detail; consistency must hold | After landing pre-filtered on `/stocks`, click a visible row; confirm `/stocks/[ticker]` shows the subject's badge + the three A–E scores + invalidation, byte-consistent with the leaderboard row. |

---

## Backend-Only Changes (No UI Impact)

- None. This iteration touched only `apps/frontend/app/stocks/page.tsx` and `apps/frontend/app/research/page.tsx` (+89/−4). No backend file, endpoint, query param, computation, config, or dependency was changed.

---

## Summary

- **Frontend surfaces changed:** 3 routes (`/research`, `/stocks`, `/stocks/[ticker]` as a downstream landing)
- **New pages/routes:** 0 (no new route; existing routes gain deep-link/cross-link behavior)
- **Modified components:** 2 files — `research/page.tsx` (new `SubjectLeaderboardLink` + caption), `stocks/page.tsx` (URL-backed filters, `parsePatternParam`, `<Suspense>`/`StocksInner` split)
- **Navigation changes:** yes (new lab → leaderboard cross-link; deep-linkable/shareable leaderboard filters)
- **Backend-only changes:** 0
