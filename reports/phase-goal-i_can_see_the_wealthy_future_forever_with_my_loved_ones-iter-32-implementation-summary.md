# Goal iter-32 — Implementation Summary

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-32
**Date:** 2026-06-18
**Written by:** developer

---

## Features Implemented

- **Downtrend Opportunity study (J-91)**: On the Research page you can now ask "during the kinds of market
  conditions that came before/inside a downtrend, what historically held up best, what fell hardest, and
  what the recovery-turn edge looked like?" — all over the SAME stored forward-tested evidence the other
  Research labs use. Each observation is tagged with the market state at its own snapshot date (the market
  phase, the drawdown-severity band, or the bear-probability band), and the study shows three side-by-side
  ranked tables: **Held up best**, **Fell hardest** (clearly marked research evidence only — there is no
  order or short-selling action anywhere), and the reused **Recovery-turn edge by phase**.
- **Condition + read controls**: pick which market state to condition on (phase / severity band / P(bear)
  band), switch the forward-return horizon, switch Episodes vs Pooled counting, and switch All-history vs
  As-of-date — all reusing the page's single existing date control (no new date picker). Every table column
  is click-sortable, and every `N=` count opens the exact underlying observations in a new tab.
- **Optional FRED macro feed (J-92)**: a real, optional economic-data feed (Treasury yield-curve spread,
  unemployment trend, credit spreads, plus market proxies) that CAN be wired into the market-phase /
  regime / downtrend layers. It ships **off by default**, so today's numbers are exactly what they were
  before. The Data Manager now shows a macro-feed catalog (which series exist, how much committed data is
  available, whether a live key is detected, and which wiring legs are on/off).

---

## Changed Behavior

- **None of the existing numbers changed.** This iteration is purely additive: the Downtrend Opportunity
  study is a new read-only view over already-stored evidence, and the macro feed is off by default. The
  existing Factor Lab, Combination Lab, Setup & Pattern event study, the Regime × Setup × Pattern study,
  the Recovery-Turn Edge study, the Dashboard market-phase panel, and the Risk-Off → Actionable gate all
  produce byte-identical figures (this is unit-tested).

---

## Backend-Only Items

- `GET /api/data` now carries a `macro` block (the FRED feed catalog + availability). It is surfaced in the
  Data Manager UI (the new Macro feed panel), so it is not backend-only.
- The FRED live-fetch capability exists (the macro provider can pull real FRED data when a key is set), but
  there is **no UI button to trigger a live macro fetch** this iteration — the Data Manager macro panel is
  read-only catalog/availability. The committed offline macro seed + the provider give the testable path.

---

## Incomplete Items

- **None of the in-scope spec items are incomplete.** Both target journeys (J-91, J-92's offline-testable
  legs) are implemented. J-92's live FRED/proxy pull is, by design, data-dependent and non-halting (it is
  honestly shown as NA until a key is set and a fetch is run) — this is the intended honest behavior, not
  an unfinished item.

---

## Config and Environment Changes

- `config.yaml` → `research.downtrend_opportunity` — the conditioning-band catalog for the Downtrend
  Opportunity study (severity bands over 0–100, P(bear) bands over 0–1). Validated contiguous + full-cover.
- `config.yaml` → `macro` — the FRED macro feed config: the environment-variable NAME the key is read from
  (`FRED_API_KEY` — the NAME only, never a key value), the four configured series (with their FRED ids,
  publication lags, and OHLCV proxies), and the three per-leg enable flags (`severity`,
  `regime_switching`, `study`) — **all false by default**.
- `FRED_API_KEY` (environment variable) — read ONLY from the environment, request-only, never written to
  disk, the database, the run log, or any committed file. Optional — unset means the live macro pull is
  honestly unavailable (NA); the committed offline macro seed still loads.
- New database table `macro_series` — a standalone, additive table for macro observations (created
  automatically; no migration needed; the immutable scanner snapshots are untouched). The `^TNX` / `^DXY`
  / `^VXN` macro proxies ride the existing daily-prices table as plain price bars.
- New committed seed files: `apps/backend/data/seed/macro/*.csv` and the three proxy price CSVs — a small
  offline macro seed so the macro-conditioned features are testable without any live fetch.

---

## Known Limitations

- The committed macro seed values are a deterministic, plausible OFFLINE seed (derived from the seed
  calendar + the committed VIX), NOT a live FRED pull. They make the wiring testable offline; the real
  FRED values replace them on a live fetch. Because every macro leg is off by default, this changes no
  served figure.
- The macro inputs only influence figures when a leg is deliberately enabled in config AND per-series
  scaling (`weight` + `stress_gate`) is configured — both off/unset by default. The enabled path is
  unit-tested but not exercised by the default boot.
- The Data Manager macro panel is read-only (catalog + availability). There is no in-app button to start a
  live macro fetch this iteration; the live pull is exercised by setting `FRED_API_KEY` and running a macro
  fetch through the provider (out of the default offline path).
