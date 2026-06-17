# goal iteration 29 — Implementation Summary

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-29
**Date:** 2026-06-17
**Written by:** developer

---

## Features Implemented

- **Market Phase & Severity panel (Dashboard):** A new card on the home Dashboard tells you, for whatever
  date you are viewing, **where in the market cycle the tape is**. It shows a plain phase label —
  Expansion, Pullback, Correction, Bear, or Recovery — alongside a **0–100 severity score** (higher =
  deeper market stress) broken down into its named drivers, so the number is always explained rather than
  shown bare.

- **Severity, explained:** The severity number is built from five named drivers, each shown with its value
  and how many points it contributed: how deep the market has fallen from its recent peak (drawdown), how
  long it has spent below that peak (time underwater), the stored market-regime reading, how much of the
  universe sits below its 200-day average (breadth), and the volatility-index (VIX) stress level. If a
  driver can't be measured for a date, it is shown honestly as "NA" rather than guessed.

- **Bear-market probability (P(bear)):** Beside the phase the panel shows a **0–1 probability that the
  market is in a bear state**, produced by a deterministic statistical filter that reads only information
  available up to the selected date. It also discloses the recent run of stress readings that drove the
  probability, so the figure is transparent.

- **Time-travel aware:** The panel re-points automatically when you change the global as-of date. Step the
  date back into the 2022 sell-off and it deepens to **Bear, high severity, bear-probability near 1**; the
  latest date reads **Expansion, low severity, low bear-probability**.

---

## Changed Behavior

- **None.** This is a purely additive read-only layer. No existing score, bucket, setup, pattern, market-
  regime value, or the Risk-Off→Actionable rule changed. The new panel is the only visible difference;
  every other page behaves exactly as before.

---

## Backend-Only Items

- `GET /api/market-phase?as_of=…` — the data source for the new panel. It is fully wired to the UI (the
  panel reads it), so there is no orphaned backend capability.

---

## Incomplete Items

- **None for this iteration's scope (J-87 + J-88).** This iteration deliberately builds only the
  foundational phase/severity/bear-probability layer. The follow-on capabilities that consume it — a
  market-phase history timeline, a recovery-turn signal, a downtrend-conditioned opportunity study, and a
  real economic-data (FRED) feed — are explicitly out of scope and remain for later iterations.

---

## Config and Environment Changes

- **New config sections in `config.yaml`** (no code change needed to tune them):
  - `market_phase` — the phase names, the severity cutoffs that map a score to a phase, the five severity
    driver weights (which must add up to ~1.0), the drawdown / volatility / time thresholds, and a minimum-
    history gate below which a date is reported "not enough history" instead of a guessed phase.
  - `regime_switching` — the parameters of the deterministic bear-probability filter (a small fixed
    transition table and per-state settings). These are committed, fixed values — the filter is never
    re-fitted while serving.
- **New database table `market_phase_cache`** — a performance cache that stores each date's computed
  phase/severity/probability so a repeat view is instant. It refreshes automatically whenever the
  underlying data changes; it is not a snapshot and holds no scores.
- No new environment variables; no migration command to run (the table is created automatically on
  startup).

---

## Known Limitations

- **First view of a date can be slow on the full daily-history host (~10–12 seconds), then instant.** This
  host stores about 1,369 daily snapshots, so the very first calculation for a given date works through a
  long history. The result is cached, so every later view of that date is sub-second, and the panel shows a
  loading placeholder in the meantime. On a smaller dataset the calculation is immediate.
- **The bear-probability filter uses price, breadth, and the volatility index only.** It does not yet
  incorporate broader economic data (interest rates, etc.) — that economic feed is a separately scoped
  future capability. The probability is honest about what it reads.
- **A very early date with too little price history shows "not enough history"** rather than a fabricated
  phase or probability — by design.
