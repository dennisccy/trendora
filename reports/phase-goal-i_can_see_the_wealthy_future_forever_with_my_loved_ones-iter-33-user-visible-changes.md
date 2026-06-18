# Phase goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-33 — User-Visible Changes

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-33
**Date:** 2026-06-18
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

- Users can now see exactly how many stocks qualify at the date they are viewing — the universe count on Data Manager changes as they step the global date switcher to earlier or later dates.
- Users can now view a per-date breakdown of why the universe is the size it is — on the Data Manager `/data` page, a new Universe Diagnostic panel shows how many names were admitted and how many were excluded for each reason (not enough history / price too low / liquidity too low) along with the exact cutoffs used.
- Users can now view the full history of how the universe grew over time on the Data Manager `/data` page — a new Membership Timeline panel shows a step-function chart of the resolved universe size across all snapshot dates, plus a per-date table of entries, exits, and excluded counts.
- Users can now see exactly which stocks entered and exited the universe on each snapshot date, along with three plain-English honesty labels explaining survivorship, warm-up, and universe-relative breadth caveats.
- Users can now trigger a "Extend history backward" action on Data Manager by clicking the confirm-gated button, which attempts a best-effort fetch of earlier price history so the universe can resolve further into the past.
- Users can now see an honest "no ranked stocks at this date — warm-up" message on the Stock Leaderboard when they step to an early date before the universe has enough history, instead of an error or fabricated rows.

---

## What Changed in the Visible UI

- The Data Manager (`/data`) "Universe" metric is now labeled "Universe (as of date)" and shows the point-in-time member count at the currently viewed date, not a fixed 122-name static count. The resolved date is shown beside the count.
- A new "Candidate universe" metric was added to the Data Manager coverage block, showing the static screened candidate count alongside the as-of-resolved member count.
- A new "Universe Diagnostic" panel was added to the Data Manager (`/data`) coverage surface, showing admitted count + excluded-by-reason counts (below history / below price / below liquidity) with exact threshold values. At an early date before the warm-up boundary, it shows an explicit honest empty-universe banner.
- A new "Membership Timeline" panel was added to the Data Manager (`/data`) page below the fold on the coverage home. It contains: an SVG step-function chart of universe size over time, a per-date table of size / entries / exits / excluded counts, and three verbatim honest labels (survivorship caveat, warm-up boundary note, universe-relative breadth note).
- A new "Extend history backward" section was added to Data Manager (`/data`) with a confirm-gated button and a modal that carries the survivorship caveat. After triggering, the live job card surfaces a blocked / limited-coverage (NA) outcome on this data-walled host.
- The Stock Leaderboard (`/stocks`) empty-state copy was changed: at an early/warm-up date it now reads a clear warm-up explanation pointing to the Data Manager diagnostic, not a generic "no results" message.

---

## What Old Behavior Changed

- Stock Leaderboard / Themes / Sectors / Scanner Runs: previously these views always showed the full static universe (122 names) at every date. Now they show only the names that qualify at the date being viewed — stepping to an early date reduces or empties the visible stock list, and the count grows toward full membership around early 2022.
- Data Manager "Universe" figure: previously always showed a fixed count (e.g. 122). Now it is date-dependent and slides as the global date switcher is stepped.
- Latest-date universe size: previously 122, now 120 — two names (RPD, DNN) honestly fail the minimum share-price gate at the latest date. This is expected point-in-time behavior, not a regression.
- Methodology page Universe Selection section: previously described a single-layer screen with a market-cap criterion. Now it documents two layers — the candidate-pool screen (which retains market cap) and the per-date membership rule (history + price + liquidity; market cap dropped for per-date use because it has no historical series).

---

## Not Visible Yet

- J-95 real backward-history fetch: the confirm-gated control, the job card, and the blocked/NA state are all visible. The actual retrieval of earlier real price history (e.g. from 2020) is blocked by the data provider on this host and is recorded honestly as blocked / limited-coverage (NA) — by design, non-halting, never faked.
- J-95 true point-in-time index-constituent feed: the survivorship caveat label noting this capability is absent is visible, but the actual per-date index constituent data is data-walled and not yet available. The candidate pool stays the documented current-constituent listing.
