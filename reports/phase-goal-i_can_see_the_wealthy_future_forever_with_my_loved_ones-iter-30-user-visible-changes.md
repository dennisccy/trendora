# Phase goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-30 — User-Visible Changes

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-30
**Date:** 2026-06-18
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

- Users can now view the full history of the market's phase (Expansion / Pullback / Correction / Bear / Recovery) and bear-probability as a step-function chart on the Dashboard by scrolling down to the Market-Phase panel — rather than only seeing a single-date snapshot.
- Users can now see exactly when each historical downtrend causally began (its first-trigger date, severity-at-trigger, and peak bear-probability) and whether it is still open or closed at the selected date, by reading the dated episode list beneath the timeline on the Dashboard Market-Phase panel.
- Users can now check whether the currently selected date is a causal "recovery / turn" signal — and read the plain-language reason explaining why (bear-probability dropped below the recovery cutoff AND the index reclaimed its trailing average) — from the recovery-turn signal line on the Dashboard Market-Phase panel.
- Users can now enable a fenced "Retrospective (full-sample / analysis-only)" sub-view on the Market-Phase panel by clicking "Show" on the toggle, which reveals the smoothed bear-probability and the after-the-fact peak-to-trough "true bear" dates (e.g. 2022-01-03 to 2022-10-12, −24.5%). This view is clearly labelled as hindsight analysis and is off by default.
- Users can now study the historical forward-return edge of entering at recovery-turn dates on the Research page (`/research`) in the new "Recovery-Turn Edge" lab section — seeing per-horizon return distribution (mean, median, win rate, expectancy), average max-drawdown, and downside-only risk-adjusted figures broken out by the market phase at each signal date.
- Users can now switch the Recovery-Turn Edge lab between "Episodes" and "Pooled" views and between "All history" and "As-of" scoping using the existing page-level toggles, and sort the per-horizon and by-signal-phase tables by clicking column headers.
- Users can now click any "N=" chip on the Recovery-Turn Edge lab to open the exact list of observations behind that count in a new tab via the samples drill-down (`/research/samples`), with the count guaranteed to match the published number in all view and scope combinations.

---

## What Changed in the Visible UI

- The Dashboard Market-Phase panel (`/`) now shows a compact SVG step-function timeline — a phase-colored band (green for Expansion/Recovery, amber for Pullback, red for Correction/Bear) behind a filtered bear-probability polyline, with a dashed as-of marker at the resolved date and a swatch legend. Previously the panel showed only a single-date headline.
- The Dashboard Market-Phase panel now shows a dated causal downtrend-episode list beneath the timeline — one row per episode, with first-trigger date, last date, severity-at-trigger, peak P(bear), and an open/closed badge. On the real host, the 2022 bear appears as one dated episode.
- The Dashboard Market-Phase panel now shows a recovery-turn signal line — a colored callout ("Recovery / turn signalled" in green with an up-arrow icon, or "No recovery turn at this date" in muted with a shield icon) plus a plain-language reason beneath it.
- The Dashboard Market-Phase panel now includes a dashed-border "Retrospective (full-sample / analysis-only)" sub-panel with a Show/Hide toggle (hidden by default). When opened it shows the smoothed P(bear) tail and the peak-to-trough true-bear dating with an explicit disclosure that this view is future-aware analysis only and never feeds any score, signal, episode, or study.
- The Research page (`/research`) now contains a "Recovery-Turn Edge" lab section appended after the Regime x Setup x Pattern lab, showing a per-horizon edge table, a by-signal-phase conditioning table, a survivorship-bias label, and "N=" chips. This section uses the shared horizon selector and analysis-mode (Episodes/Pooled, As-of/All-history) controls already present on the page.
- The Research Samples drill-down page (`/research/samples`) now renders a cohort header describing the "recovery-turn" cohort (view and "All recovery-turn dates" or "Phase at signal: <label>") with qualifying columns for Signal date, Phase at signal, and P(bear) at signal when the link comes from the Recovery-Turn Edge lab.

---

## What Old Behavior Changed

- Dashboard Market-Phase panel: previously showed only the single current-date phase, severity, and bear-probability values. Now also shows the phase/probability history timeline, the dated downtrend-episode list, the recovery-turn signal line, and the optional fenced retrospective sub-view. The single-date headline values (phase, severity, P(bear)) are unchanged (byte-identical for the same date).
- `GET /api/market-phase`: previously returned only the single-date phase/severity/P(bear) payload. Now also returns `timeline`, `episodes`, and `recovery_turn` fields. The previously-served values for any given date are unchanged. The endpoint also now accepts `?retrospective=true` to additionally return the fenced analysis-only data. (Note: on a host with pre-iter-30 cached market-phase data the new fields may be absent on the very first request until the cache refreshes — clearing `MarketPhaseCache` once forces it.)

---

## Not Visible Yet

- None. Every new backend capability (timeline series, dated episodes, recovery-turn signal, fenced retrospective, recovery-turn-edge study, samples drill-down for the recovery-turn kind) is wired to a visible UI surface.
