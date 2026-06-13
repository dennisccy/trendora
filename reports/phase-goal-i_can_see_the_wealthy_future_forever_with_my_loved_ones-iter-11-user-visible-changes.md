# Phase goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-11 — User-Visible Changes

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-11
**Date:** 2026-06-13
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

- On the `/sectors` page, users can expand any ranked ETF row and read a plain-language description of what that industry group represents (e.g. "Semiconductors" rather than the bare ticker "SMH").
- Users can expand a sector ETF row (e.g. XLK) to see which universe stocks belong to that sector — each listed as a clickable ticker chip.
- Users can expand an industry ETF row (e.g. SMH) to see which universe stocks are mapped to that industry group via the config-defined membership, labelled "Members (config-defined)".
- When more than 6 members exist, users can click the "+N" button in the expanded row to reveal all remaining members, and click "Show fewer" to collapse back to the preview.
- Users can click any member ticker chip in the expanded panel to open that stock's detail page in a new browser tab. When viewing a historical as-of date, the link carries the `?asof` parameter so the stock detail opens at the same date.
- Users expanding "Regional Banks (SPDR)" (KRE) will see an explicit "No universe members are mapped to this ETF (config-defined)." message — no fabricated names.

---

## What Changed in the Visible UI

- The `/sectors` leaderboard: industry ETF rows previously showed bare tickers (e.g. "KRE") in their expanded panel header. They now show a config display name (e.g. "Regional Banks (SPDR)").
- Each expanded ETF row panel on `/sectors` now contains two new sections below the existing score-component breakdown: (1) a description line (for industry ETFs that have one), and (2) an expandable universe-member list with ticker chips.
- The member chip styling on `/sectors` matches the established `/themes` chip pattern (bordered chips with hover accent, focus-visible ring, dashed-border "+N" button) — the two leaderboards are now visually consistent.
- An explicit empty-state line ("No universe members are mapped to this ETF (config-defined).") appears inside the expanded panel of any ETF with zero mapped universe stocks.
- The industry membership section header reads "Members (config-defined)" to communicate the source of the mapping.

---

## What Old Behavior Changed

- `/sectors` expanded panel — industry ETF name display: previously the expanded panel header for an industry ETF showed only the raw ticker string (e.g. "KRE"). Now it shows the config-defined display name (e.g. "Regional Banks (SPDR)"). The ranked table row itself is unchanged.
- `/sectors` expanded panel — content scope: previously the expanded panel showed only the score-component breakdown. Now it additionally shows the description (if present) and the member list (or explicit empty state). The score components themselves are byte-identical — no ranked value changed.

---

## Not Visible Yet

- None. Every backend addition in this iteration (config name/description, member list resolution, persistence, API echo) is reflected in the `/sectors` expanded panel UI.
