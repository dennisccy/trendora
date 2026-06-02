# Goal Iteration 13 — Implementation Summary

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-13
**Date:** 2026-06-02
**Written by:** developer

---

## Features Implemented

- **Volatility is now a four-measure factor family on the Research → Factor Lab (`/research`).** Where the
  lab previously offered a single volatility factor (ATR %), the user can now pick each of **four**
  volatility measures from the Factor dropdown and read, for each, whether — and in which direction — it
  sorted realized forward returns in this universe:
  - **ATR % (volatility level)** — already present (unchanged).
  - **Historical volatility (HV)** — *new* — how spread-out the stock's recent daily returns have been.
  - **Volatility contraction (VCP-style)** — *new* — whether the stock's recent volatility is *drying up*
    (a continuous ratio; below 1 means contracting) versus the prior period.
  - **Downside volatility (semivol)** — *new* — only the *downside* dispersion of recent returns (upside
    moves are never counted), so it does not penalise healthy advances.
  Each measure shows the same evidence the lab already produces for any factor: a decile table (average
  forward return **and** a downside-risk-adjusted column, each with its sample size `n`), the rank-IC
  (a single correlation number with `n`), and the by-market-regime effectiveness split — with honest
  "NA + n" wherever a cell has too few observations, never a fabricated number.
- **The Factor dropdown is now grouped by family.** Options are organised under headings (Score,
  Momentum, Trend, **Volatility**) so the four volatility measures sit together under one "Volatility"
  heading — making "select the volatility family and view each measure" obvious.

---

## Changed Behavior

- **Daily scan snapshots now also record three new per-stock volatility numbers** (historical volatility,
  the contraction ratio, and downside volatility) alongside the existing scores and pattern flags. These
  are computed once per stock from price history up to the snapshot date and frozen into the immutable
  snapshot. They are **evidence inputs for the Factor Lab only** — they do **not** change any stock's
  Leadership / Entry Quality / Risk score, its A–E bucket, its setup status, the candidate counts, the
  market-regime label, or the Risk-Off→Actionable gate. All of those remain exactly as before (verified).
- **The stored database was regenerated** so every historical snapshot now carries the three new numbers
  and the forward-return evidence pool is intact. (The database is rebuilt deterministically from the
  committed offline seed — no new data was fetched.)

---

## Backend-Only Items

- The three new per-stock volatility values ride on the canonical `/api/stocks` and `/api/stocks/{ticker}`
  rows (like any other stored value) but are deliberately **not shown** on the `/stocks` leaderboard or
  the stock-detail score breakdown — they are stored for the Factor Lab's consumption only. This is by
  design for this iteration, not an oversight.

---

## Incomplete Items

- None deferred from this iteration's scope. (Out-of-scope by design: the J-29 event-study measures
  MAE/MFE/expectancy and a `return/MAE` risk-adjustment, which need a post-snapshot high/low excursion
  path not built here; and J-22/J-23/J-24, which remain blocked by an external data provider and were
  explicitly not retried.)

---

## Config and Environment Changes

- `config.yaml` → `indicators`: four new windows (trading days), all validated positive at startup —
  `hv_window: 21`, `semivol_window: 63`, `vol_contraction_recent: 21`, `vol_contraction_prior: 63`.
  These are illustrative defaults and can be tuned without code changes.
- `config.yaml` → `research.factor_lab.factors`: three new catalog entries (`hv`, `vcp_contraction`,
  `downside_vol`), each family `volatility`, direction `lower_better`.
- No environment variables added. No schema migration tool (tables are created from the models on
  startup); the database file was deleted and rebuilt so the three new columns are present from the start.

---

## Known Limitations

- **What the evidence actually says (honest, descriptive — not a forecast):** on the committed seed, none
  of the volatility measures is a strong forward-return predictor. The rank-IC values are small —
  historical volatility ≈ +0.03, the VCP-style contraction ratio ≈ −0.02 (essentially flat), downside
  volatility ≈ +0.12 (the strongest, and *positive* — higher recent downside has been associated with
  *higher* subsequent return in this universe, the opposite of the textbook "low-vol wins" assumption).
  These are reported as-is; the lab is descriptive evidence, never a prediction.
- **Contraction cross-check:** the VCP-style contraction factor's evidence is read from the *same* stored
  forward-return observations the System Health "VCP vs non-VCP" breakdown uses (no recomputation), so the
  two are consistent by construction. The continuous contraction ratio shows essentially no forward-return
  edge in this seed — a valid honest finding.
- **Short-history stocks** legitimately have "NA" for these measures at early snapshot dates; such
  observations are *excluded* from the lab (never counted as zero). This is why the contraction and
  downside-volatility factors show one fewer observation than historical volatility.
- The four volatility windows are illustrative; they were chosen to produce well-populated decile tables
  on the seed, not tuned to a target result.
