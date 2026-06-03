# Goal Iteration 15 — Implementation Summary

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-15
**Date:** 2026-06-03
**Written by:** developer

---

## Features Implemented

- **Travel from lab evidence to the names, in one click (J-31):** On the Research page's Setup &
  Pattern Lab, a new link — **"View the names expressing this on the leaderboard →"** — takes the
  setup or pattern you are studying and opens the Stock Leaderboard already filtered to the names that
  express it right now. No more copying a ticker by hand to get from "this pattern has good evidence"
  to "which stocks have this pattern today."
- **Shareable, bookmarkable Stock Leaderboard filters:** The Sector / Setup / Pattern filters on the
  Stocks page now live in the page's web address. You can open a link like
  `/stocks?pattern=pullback_to_rising_dma__only` or `/stocks?setup=Breakout-watch` and the filter is
  already applied; changing a filter updates the address so you can share or bookmark the exact view.

---

## Changed Behavior

- **Stock Leaderboard filters:** Previously the Sector / Setup / Pattern filters were in-page only —
  the view could not be linked to or shared, and the labs could not point at it. Now the filters are
  carried in the page address (so a link can pre-apply them) and update the address when changed. The
  rows shown, the scores, and the load speed are unchanged — only the address now reflects the filters,
  and the page can be opened pre-filtered.
- **Setup & Pattern Lab:** Previously a read-only dead-end (you read the evidence, then had to navigate
  to the leaderboard by hand). Now it offers a direct cross-link to the matching names on the
  leaderboard.

---

## Backend-Only Items

- None. This iteration changed only the web interface. No new server endpoint, value, or calculation
  was added or needed — the leaderboard rows and the lab analytics were already being served.

---

## Incomplete Items

- **"Across timeframes" (the intraday 1D/1h/15m/5m chart selector):** Out of scope and not built. The
  underlying intraday data feed is blocked by an external rate limit, so this iteration's travel uses
  the standard daily chart (which works). This is a known, pre-existing limitation, not a gap
  introduced here.

---

## Config and Environment Changes

- None. No new environment variables, config entries, settings, or dependencies. No database change.

---

## Known Limitations

- **Filters reflect to the address one-way.** Opening a shared/bookmarked filtered link works (the
  filter is pre-applied), and changing a filter updates the address. The page does not additionally
  react to the browser's Back/Forward buttons to re-read the address into the filters — this was
  deliberately left out to keep the behavior simple and avoid a refresh loop. It is not required for
  the feature and does not affect sharing.
- **The cross-link follows the subject the lab has finished loading.** If you switch the lab's subject
  and click the link in the same instant, it may briefly point at the previous subject until the new
  evidence finishes loading (under a second). Let the lab finish loading before clicking.
- **Empty results are shown honestly.** If a shared filter link matches no names for the current date,
  the page shows its normal "no matches" message rather than inventing rows. Pick a populated subject
  (e.g. the pullback-to-rising-DMA pattern, or the Breakout-watch setup) to land on real names.
- **The date you are viewing is still controlled in exactly one place** — the top-bar as-of switcher.
  The new filter links never carry a date; switching the date keeps your filter and re-points the page
  by date, as before.
