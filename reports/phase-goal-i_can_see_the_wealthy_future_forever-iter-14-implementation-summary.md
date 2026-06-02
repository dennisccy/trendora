# Goal iter-14 — Implementation Summary

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-14
**Date:** 2026-06-02
**Written by:** developer

---

## Features Implemented

- **Setup & Pattern Lab (event study)** on the Research page (`/research`): pick any setup (Actionable,
  Breakout-watch, Pullback-watch, Extended, Avoid, Risk-off-watchlist) or detected pattern (VCP,
  Pullback-to-DMA, Flat-base) and read how it has actually performed across **every** past snapshot —
  pooled together — instead of one date at a time. It is a third lab section, below the existing Factor
  Lab and Combination Lab.
- **What the lab shows, per holding length (1 / 5 / 10 / 20 / 60 days):** the average forward return, the
  median, the % of times it was positive (hit-rate), the spread (dispersion), the **expectancy** (the
  average outcome per occurrence, broken into win-rate / average win / average loss), the typical worst dip
  and best rise during the trade (**MAE / MFE**), and two **risk-adjusted** scores that divide the return
  by downside risk only (never by healthy upside). The horizon with the best risk-adjusted return is
  highlighted as the **best exit-horizon**.
- **How it behaves by market regime and by sector:** two panels show the same setup/pattern split by the
  market regime it occurred in and by the stock's sector, so you can see where the edge actually came from.
- **New stored measurement — MAE / MFE (max adverse / favorable excursion):** for every past snapshot the
  system now records, alongside the realized return, how far price fell and rose during the trade window
  (from the post-snapshot daily highs and lows). This is what makes the drawdown/upside and the
  return-per-drawdown ratios possible.
- **Honesty everywhere:** any setup/pattern/regime/sector with too few past occurrences (below the
  configured minimum sample) shows "NA" plus the actual count `n` rather than a made-up number, and the
  survivorship-bias / "descriptive, not a forecast" caveats are shown on the section.

---

## Changed Behavior

- **Research page (`/research`)**: previously had two labs (Factor Lab, Combination Lab). Now has a third
  — the Setup & Pattern Lab — below them. The page's single Horizon selector now also drives the new
  section; there is still exactly one date control for the whole app (the global as-of switcher), and the
  new section is a cross-date aggregate that ignores it (same as the other labs).
- **Stored forward-test data**: each recorded forward return now also carries the trade's worst-dip and
  best-rise figures (MAE / MFE). Existing recorded returns are unchanged in value; the new figures were
  added by regenerating the local database from the committed seed.

---

## Backend-Only Items

- None. The one new backend capability (the `GET /api/research/event-study` data source and the stored
  MAE/MFE) is fully surfaced through the new Setup & Pattern Lab UI.

---

## Incomplete Items

- None from this phase's spec. The next journey, J-31 (a guided "find a winning driver and travel from the
  lab evidence to the live names" workflow), is intentionally out of scope this iteration and is the next
  target.

---

## Config and Environment Changes

- None. No new config keys or environment variables were added — the lab's subject list is derived from
  the setups and detected patterns already defined in `config.yaml`, and it reuses the existing
  walk-forward sample/horizon settings.
- **Local database regenerated**: the runtime database (`apps/backend/data/trendora.db`, not committed) was
  deleted and rebuilt from the committed seed so the new MAE/MFE figures are filled in. This happens
  automatically on a fresh boot; operators with an older local database should delete it once and restart
  the backend to pick up the new columns.

---

## Known Limitations

- **Rare setups show NA by design.** The lab defaults to the "Actionable" setup, which has only 2
  historical occurrences in the seed, so the default view honestly shows "NA + n=2" rather than numbers.
  To see populated figures, pick a more common subject — e.g. **Breakout-watch**, **Avoid**, or
  **Pullback to a rising DMA** all have plenty of occurrences. This is the product's intended
  evidence-driven honesty (it never fabricates a number on thin data), not a malfunction.
- **VCP shows NA in this seed.** The VCP pattern has 27 historical occurrences, just under the 30-sample
  minimum, so its distribution renders as NA + n; its by-regime panel still shows the honest empty-regime
  rows. Other patterns (Pullback-to-DMA: 163, Flat-base: 48) render full numbers.
- **Evidence is survivorship-biased and historical.** As labelled on the page, the figures are measured on
  the current-membership universe and are descriptive history, not a forecast.
