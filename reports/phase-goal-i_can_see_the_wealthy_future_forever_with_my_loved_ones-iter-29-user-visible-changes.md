# Phase goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-29 — User-Visible Changes

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-29
**Date:** 2026-06-17
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

- Users can now read the current market cycle phase (Expansion, Pullback, Correction, Bear, or Recovery) at a glance on the Dashboard home page (`/`), without navigating away or opening any additional page.
- Users can now see a 0–100 severity score that explains how deep or stressed the current market environment is, with each of the five named drivers (drawdown depth, time underwater, market regime, breadth below 200-day moving average, and VIX stress) shown individually with its value and point contribution — so the score is always explained, never a bare number.
- Users can now see a 0–1 bear-market probability (P(bear)) on the Dashboard, alongside the recent series of stress readings that produced it, making the figure transparent rather than opaque.
- Users can now use the global as-of date control to time-travel: stepping the date back to the 2022 sell-off deepens the panel to Bear / high severity / high P(bear); moving to a 2024 or later date shows Expansion / low severity / low P(bear). The panel repoints automatically with no additional controls.

---

## What Changed in the Visible UI

- The Dashboard home page (`/`) now contains a new "Market Phase & Severity" card placed directly below the existing "Major indexes & regime" card. The card was not present before this iteration.
- The card header row shows two new badges: the phase label (colored green for Expansion/Recovery, amber for Pullback, red for Correction/Bear) and the P(bear) badge (colored by probability level), with the resolved as-of date displayed beside the card title.
- The card body shows the severity headline number (e.g., "28.75 / 100 severity") alongside drawdown percentage and off-trough percentage, followed by a three-column breakdown table listing every named severity driver with its [0,1] value and point contribution.
- Below the breakdown table, the card shows the filter observation vector: a row of dated chips, each showing a stress reading, that fed the deterministic bear-probability filter up to the selected date. The total observation count is disclosed even when only a capped tail is shown.
- When a date has insufficient price history, the card body shows the message "Not enough history to derive a market phase for this date" with a minimum-bar count, rather than any fabricated value.
- When the backend is unreachable, the card body shows a styled warning alert ("Market phase unavailable — confirm the backend is running and reload"), not a blank or fabricated panel.
- While the backend computes the result for the first time on a given date, the card body shows an animated loading placeholder (skeleton) so the panel never appears broken.

---

## What Old Behavior Changed

- None. This iteration is purely additive. No existing Dashboard card, page, score, stock bucket, setup, pattern, regime label, or Risk-Off rule was altered. All previously working surfaces behave exactly as before.

---

## Not Visible Yet

- The market-phase history timeline (J-89) — a chart showing how the phase and severity evolved over time — exists as a future planned capability but has no UI entry point yet.
- The recovery-turn edge signal (J-90), the downtrend-conditioned opportunity study (J-91), and the FRED economic data feed (J-92) are all deferred to later iterations and have no UI at this time.
- The `GET /api/market-phase` endpoint is fully wired to the new panel. There is no orphaned backend capability from this iteration.
