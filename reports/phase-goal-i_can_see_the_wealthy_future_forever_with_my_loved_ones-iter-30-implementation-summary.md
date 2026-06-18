# Goal iter-30 — Implementation Summary

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-30
**Date:** 2026-06-18
**Written by:** developer

---

## Features Implemented

- **Market-phase history timeline (Dashboard)**: The Market-Phase panel now shows the FULL HISTORY of the
  market's phase (Expansion / Pullback / Correction / Bear / Recovery) and bear-probability as a dated
  step-function chart across snapshot dates — not just a single-date snapshot.
- **Dated downtrend episodes (Dashboard)**: A list of when each market downtrend causally began (its
  first-trigger date and the severity then) and whether it is still open as of the selected date or has
  closed. On the real data the 2022 bear shows up as one dated episode.
- **"Is this a recovery turn?" signal (Dashboard)**: For the selected date, the panel tells you whether the
  market just causally turned up out of a downtrend — with a plain-language reason (the bear-probability
  dropped below the recovery cutoff AND the index reclaimed its trailing average), never a bare yes/no flag.
- **Fenced retrospective "true bear dating" (Dashboard)**: A clearly-labelled "Retrospective (full-sample /
  analysis-only)" sub-view (toggle on/off) that shows the smoothed bear-probability and the after-the-fact
  peak-to-trough "true bear" dates. It is visibly walled off as hindsight analysis and never feeds any live
  reading. On the real data it dates the 2022 bear at 2022-01-03 → 2022-10-12, a −24.5% decline.
- **Recovery-Turn Edge study (Research)**: A new read-only lab section that answers "historically, what
  forward returns followed entering at a recovery turn?" — the per-horizon return distribution, win rate,
  expectancy, average max-drawdown, and a downside-only risk-adjusted figure, broken out by the market phase
  at the signal date. On the real data it found 6 recovery-turn dates (incl. the 2022→2023 turn) and an
  average +2.2% over the next 20 trading days.
- **Count-coherent drill-down (Research)**: Every "N=" sample-size chip on the new lab opens, in a new tab,
  the exact list of observations behind that number — and the count always matches.

---

## Changed Behavior

- **Dashboard Market-Phase panel**: Previously showed only the single-date phase, severity, and bear-
  probability. Now it ALSO shows the phase/probability history timeline, the dated downtrend episodes, the
  recovery-turn signal line, and the optional fenced retrospective sub-view. The single-date headline values
  are unchanged (verified byte-identical for the same date).
- **`GET /api/market-phase`**: Now returns extra history fields (timeline, episodes, recovery-turn) and
  accepts `?retrospective=true` to additionally return the fenced analysis-only data. The previously-served
  values for any date are unchanged.

---

## Backend-Only Items

- None. Every new backend capability is wired to the UI (the timeline/episodes/recovery-turn on the
  Dashboard panel; the edge study + drill-down on Research).

---

## Incomplete Items

- None deferred from this iteration's scope. (J-91 downtrend-conditioned study, J-92 FRED macro feed, and
  J-93–J-96 dynamic universe remain queued for later iterations, as planned — they were explicitly out of
  scope here.)

---

## Config and Environment Changes

- `config.yaml` → `market_phase` block — five new tunables (no code literals): `downtrend_pbear_threshold`
  (0.50 — the bear-probability that opens a downtrend episode), `recovery_signal_pbear_exit` (0.40 — the
  probability the recovery turn must cross below), `recovery_trailing_ma_days` (50 — the trailing-average
  window the index must reclaim), `bry_boschan_min_phase_days` (90) and `bry_boschan_min_amplitude_pct`
  (20.0 — the minimum length/depth for an after-the-fact "true bear" phase). All are validated at startup.
- No new database table, no migration, no new environment variable.

---

## Known Limitations

- **First-read caching on a busy host**: On a host that already had cached market-phase data from the
  previous iteration, the new timeline/episodes may be absent on the very first read until the cache
  refreshes (it refreshes automatically the next time the dataset changes; an operator can also clear the
  `MarketPhaseCache` cache table once to force it). No data is wrong — it is just the older cached shape.
- **Cold-compute time on the full daily-history host**: The first computation of a date's timeline takes
  ~30–55 seconds (and the retrospective adds ~30s), then it is cached and instant. A loading skeleton is
  shown; the retrospective is off by default so the heavy part only runs when requested.
- **Retrospective is hindsight by design**: The smoothed probability and the "true bear" dates use
  information from after each date. They are clearly labelled analysis-only and are walled off from every
  live/as-of reading — they never change a score, signal, episode, or study figure.
- **Macro (FRED) data is intentionally not used yet**: All figures come from price/breadth/VIX evidence
  only, so they are identical to the prior path.
