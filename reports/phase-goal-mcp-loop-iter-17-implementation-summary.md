# Phase goal-mcp-loop-iter-17 — Implementation Summary

**Phase:** goal-mcp-loop-iter-17
**Date:** 2026-07-02
**Written by:** developer

---

## Features Implemented

- **The staged 30-year price seed is now complete ("swap-complete")**: the side-by-side
  replacement data set that iteration 16 started now also carries the market-index and macro
  context series it was missing — the S&P 500, Nasdaq-100, and Dow Jones indexes deep back to
  1996, a deep volatility index (VIX) back to 1996, and the three macro proxy series the app's
  Data page relies on. Every price series the app uses today now has a counterpart in the
  staged set, so the future one-time switch to the 30-year basis can happen in a single step.
- **Honest per-source labeling**: the staged data set's manifest now records, for every context
  series, exactly where it came from — Stooq (the index benchmarks, read from the operator's
  local Stooq world archive), Yahoo (the VIX), or "FRED-macro proxy" (the three macro series,
  copied unchanged from today's data so they keep matching the FRED macro numbers the app
  displays). This is the future single source for the vendor labels users will eventually see.
- **Deep VIX from Yahoo, verified live**: the VIX history was re-fetched from Yahoo in one pull
  covering 1996 through 2026. It matches today's data exactly on every overlapping day (zero
  difference), so it is the same series, simply extended 25 years deeper. A safe offline
  fallback (keep today's shorter copy unchanged) was built and tested but was not needed.
- **Stronger data validation**: five new automated checks now guard the staged data set —
  including the load-bearing "swap-completeness" check (the staged set must contain everything
  the live set has) that the next iteration's basis switch is required to see green.
- **Safety fix carried forward (audit B2)**: the ingest tool's anti-bot handshake solver now has
  a hard iteration cap with an honest failure message — it can no longer spin forever if the
  data provider ever serves an unsolvable challenge.
- **Durability guard for the merged manifest**: re-running the ingest tool later (for
  maintenance) can no longer accidentally erase the new source labels or shrink the staging
  plan recorded in the data set's manifest.

## Changed Behavior

- **None visible.** Every page, number, score, badge, and chart in the product is byte-identical
  to before this iteration. The staged data set is read by nothing at runtime; the app still
  runs entirely on today's committed seed. (This is an enablement iteration: it prepares data
  for the next iteration's one-time basis switch.)

## Backend-Only Items

- The completed staged data set (`apps/backend/data/seed-stooq-30y/`, 590 price files + its
  manifest) — deliberately not wired to anything; the switch is the next iteration's job.
- A new `--stage-context` mode on the seed-ingest tool that merges the context series into an
  existing staged manifest without disturbing the 583 equity records already staged.
- No UI wiring exists yet by design; the vendor labels become user-visible only after the swap.

## Incomplete Items

- **None from this iteration's scope.** All Definition-of-Done items landed, including the deep
  VIX (the plan allowed an honest shorter fallback; the deep pull succeeded so even the
  optional-best outcome was reached).
- Deliberately deferred (out of scope, sequenced later): the actual basis switch + evidence
  ledger reset (iteration 18); deepening the three macro proxy series via FRED; showing the
  deep charts and vendor labels in the UI (after the switch).

## Config and Environment Changes

- **None.** No config file, environment variable, or schema change. `STOOQ_API_KEY` remains an
  optional env-only setting for the (unused this iteration) network path; it is never written to
  any file, and the new failure paths run through the same redaction guard as before — with a
  test that proves a key in the environment cannot leak into the committed manifest.
- The operator's local archives under the repo-root `data/` folder (e.g. `data/d_world_txt/`)
  remain gitignored and uncommitted; only the validated staged OUTPUT is committed.

## Known Limitations

- The three macro proxy series in the staged set are honestly SHORT (2021 → 2026-05-28): they
  are exact copies of today's series, kept that way on purpose so they continue to match the
  FRED macro data the app displays. Re-fetching them from Yahoo would silently change their
  meaning (different index basis), which the project goal explicitly forbids.
- Stooq's US archive still has no data for SATS; it stays honestly absent (1 of 591 planned
  names) rather than fabricated.
- Yahoo's VIX series carries a bar on 2026-05-25 (a market holiday) — a vendor quirk already
  present in today's data, inherited unchanged, noted for transparency.
- The staged asset improves nothing user-visible yet; the payoff arrives with the iteration-18
  switch.
