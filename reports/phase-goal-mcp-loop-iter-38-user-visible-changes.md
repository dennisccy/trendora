# goal-mcp-loop-iter-38 — User-Visible Changes

**Phase:** goal-mcp-loop-iter-38
**Date:** 2026-07-15
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

- Users can now see, on the existing `/watchlist` page, a new **"Concentration X-ray"** section below the saved-stocks table that answers "how concentrated is my watchlist really?" — a pairwise return-correlation matrix, correlation-threshold clusters, and a headline **"effective independent bets"** figure with its trailing window stated.
- Users can read, for the real persistent watchlist right now (ABBV, MSFT): a correlation of **−0.11** between the two names, a headline reading **"≈ 2.0 effective independent bets (over the last 126 trading days)"**, and two separate single-name clusters (the pair isn't correlated enough to group together).
- Users can see sector, theme, and shared-setup-status concentration bars beneath the matrix — right now: a 50% Technology / 50% Unassigned sector split, three theme bars (AI / data-centre, Software & cloud, Megacap leaders — each 50%, all from MSFT's theme membership), and a single "Avoid" setup bar at 100% (both watchlist names currently classify as "Avoid").
- Users can click or hover the info icon next to the "effective independent bets" headline to read a plain-language explanation of the methodology and the minimum-history floor below which a name is excluded.
- Users can hover any cell in the correlation matrix to see the exact correlation value, or — for a muted, dashed-border "—" (NA) cell — the exact reason it's NA (how many days of price history each side actually has versus how many are required).
- Users with an empty or single-name watchlist see an honest **"Not enough names yet for an X-ray"** message in place of a broken or empty chart, distinct in wording from the existing "Your watchlist is empty" message shown for a fully empty list.

No new *interactive* control was added — this is a read-only, descriptive section layered onto an already-existing page. The existing "Add a ticker" form and each row's "Remove" button are unchanged.

---

## What Changed in the Visible UI

- The `/watchlist` page now renders a new "Concentration X-ray" `Card` section immediately below the existing entries table (shown whenever the watchlist has at least one saved entry — the same gate the table itself already uses), stacked in the page's existing vertical layout rhythm. No new page and no new navigation entry — `/watchlist` is the same pre-existing top-level nav item.
- Within that new section: a ticker-by-ticker correlation heatmap grid, a row of cluster badges, the ENB headline with its info icon, and three horizontal bar-chart breakdowns (sector / theme / shared setup status). The shared-setup bars are colored using the exact same status→color mapping (e.g. red for "Avoid") the entries table's own Setup column already uses, so the color vocabulary is consistent across the page.
- The page's existing loading skeleton and "Backend unavailable" error card are unchanged in appearance, but now implicitly also cover the X-ray section's data, since all of it rides the same single `GET /api/watchlist` call the page already made — a user does not see a separate loading or error state for the new section.

---

## What Old Behavior Changed

None — this phase is purely additive:
- The existing entries table (Ticker / Added / Reason / Leadership / Entry Quality / Risk / Setup / Since added / Invalidation / Remove columns) is visually and behaviorally unchanged.
- The "Add a ticker" form and each row's "Remove" button work exactly as before.
- `GET /api/watchlist`'s existing `asof_date` and `entries[]` fields are byte-identical to before this phase; only a new, additive `xray` field was added alongside them.

---

## Not Visible Yet

- `enb_member_count` — how many watchlist names actually contributed to the "effective independent bets" figure — is computed and served in the API response but has no display slot on the page today. For the current 2-name watchlist this always matches the visible ticker count, so nothing is hidden in practice right now, but on a larger watchlist where some names are excluded for short history, this diagnostic count (distinct from the plain list of tickers) would not be visible anywhere.
- A similar correlation view for certified evidence claims on `/evidence` (the future backlog item this phase's underlying math is explicitly built to be reused by) was not built this phase — only the shared calculation helper exists; `/evidence` itself is untouched.
- A per-stock "how much can this hurt" risk-budget card and phase-conditional drawdown/dry-spell expectation panels — both referenced as adjacent future work in this phase's planning — were not built in any form this phase, not even as unwired backend code.
