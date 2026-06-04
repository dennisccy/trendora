# Goal Iteration 17 — Implementation Summary

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-17
**Date:** 2026-06-04
**Written by:** developer

---

## Features Implemented

- **Time-machine forward-test evidence on Backtest (J-09)**: The Backtest workspace now shows the
  forward-tested track record — forward return by score bucket (A–E), excess vs SPY and QQQ, by setup
  type, by market regime, the VCP-vs-non-VCP breakdown, the two new pattern breakdowns, and the
  control-group comparison — **scoped to every snapshot dated on or before the chosen as-of date**. Move
  the single global as-of switcher to an earlier date and the evidence re-points and the sample size `n`
  shrinks; return to the latest date and it equals the full all-history track record.
- **Control-group comparison on Backtest (J-10)**: The top-ranked cohort vs a random same-sector cohort
  vs SPY / QQQ / sector ETF — each numeric and labelled — now lives on Backtest as part of the same
  as-of-scoped evidence, so a reader can see whether the ranking adds value beyond sector beta.
- **One date control everywhere (J-18 preserved)**: The new evidence section is driven entirely by the
  existing global as-of switcher and the existing Backtest horizon selector. No page-local date picker was
  added; the horizon selector is a view selector, not a date control.

---

## Changed Behavior

- **Forward-tested evidence moved off "System Health" onto "Backtest"**: Previously the forward-return
  aggregate (by bucket / setup / regime, excess vs benchmarks, VCP/pattern, control group) lived on a
  separate **System Health** page that was date-blind (it always showed the whole history). Now that
  exact evidence lives on **Backtest**, is **scoped to the selected as-of date** (an expanding window),
  and the **System Health page and its sidebar entry are removed**. At the latest date the numbers are
  identical to what System Health used to show.
- **Backtest API payload**: `GET /api/backtest` now also returns the as-of-scoped evidence aggregate
  (keyed by each forward horizon) alongside the existing per-date scorecard — all in one response, so the
  horizon selector needs no extra network call.

---

## Backend-Only Items

- None. Every backend change is surfaced on the Backtest page.

---

## Incomplete Items

- None. All in-scope Definition-of-Done items for iter-17 are implemented: the as-of cutoff on the
  aggregate, the `/api/backtest` evidence payload, the System Health retirement (page + nav + route +
  unused client), and the Backtest evidence-aggregate UI sections.
- Out of scope by design (not started, per the spec): J-26 composite factor cohort (iter-18), J-32
  Research as-of toggle (iter-19), and the Yahoo-429 data-walled J-22/J-23/J-24 (non-halting).

---

## Config and Environment Changes

- No new config keys, no schema change, no database regeneration. The as-of cutoff is a function
  parameter, not a config value. (One stale comment in `config.yaml` next to `default_horizon` that named
  the retired endpoint was corrected — no value changed.)

---

## Known Limitations

- **Survivorship bias / universe-relative**: As before, the walk-forward evidence is measured on the
  current-membership universe and is labelled survivorship-biased; breadth figures stay universe-relative.
  These honest caveats are carried on the new section.
- **Low-sample / partial windows show NA**: At an early as-of date (or a recent date with few elapsed
  bars) cells with fewer than the minimum sample size, or an empty cohort, render "—" (NA) with their
  sample size `n` — never a fabricated number.
- **Per-request computation (no new cache table)**: The evidence aggregate is computed as a read-only
  grouping over the already-stored forward returns on each request (filtered to ≤ the as-of date), the
  same model the retired System Health used — now for five horizons in one response. For the committed
  seed this is fast; no new caching/persistence table was added (per scope).
- **Operator note for browser testing**: A production `next build` was run for the type-check and then
  removed; the browser-QA step must start `next dev` on a clean `.next` (stop by port, `rm -rf
  apps/frontend/.next`, restart) before driving the UI, per the standing iter-15 lesson.
