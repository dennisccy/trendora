# goal-i_can_see_the_wealthy_future_forever-iter-2 Functional Test Plan

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-2
**Date:** 2026-06-01
**Frontend Present:** yes

## Phase Goal

On **System Health** (aggregate) and **Backtest** (single resolved date), a user can open any
forward-test mean into four read-only attribution layers — per-stock top contributors & detractors,
by-sector, by-rank-band (config bands 1–10 / 11–50 / 51+), and a distribution & hit-rate panel — each
with sample size `n`, derived from the stored per-observation forward returns (no recompute), so a weak
mean becomes diagnosable.

## Test Cases

### TC-01 — Aggregate attribution rides existing horizon on `/api/system-health`

**Type:** api
**Preconditions:** Backend running on :8000; a snapshot with elapsed forward windows exists for the resolved as-of date.

**Steps:**
1. `curl -s "http://localhost:8000/api/system-health" | python3 -m json.tool`
2. Inspect the top-level `attribution` object.

**Expected outcome:** Response carries an `attribution` key keyed to the selected horizon with sub-keys `per_stock` (`contributors`, `detractors`), `by_sector`, `by_rank_band`, `distribution`.
**Pass criteria:** `attribution.per_stock.contributors` and `.detractors` are arrays of `{ticker, mean_return, n, sector}`; `by_sector` and `by_rank_band` are arrays of rows each with `n`; `distribution` has `{mean_return, median, pct_positive, dispersion, n}`. HTTP 200.

### TC-02 — Distribution mean equals aggregate overall mean (read-only consistency)

**Type:** api
**Preconditions:** As TC-01, a horizon with samples.

**Steps:**
1. Fetch `/api/system-health`.
2. Compare `attribution.distribution.mean_return` to the existing `overall.mean_return` for the same horizon.
3. Sum the `n` of every `by_sector` row and separately every `by_rank_band` row (excluding rows from `rank is None` observations).

**Expected outcome:** Distribution mean equals the canonical aggregate mean; group `n`s reconcile to `overall.n`.
**Pass criteria:** `distribution.mean_return == overall.mean_return` (within float tolerance); `sum(by_sector[*].n) == overall.n` and `sum(by_rank_band[*].n) == overall.n` on a fixture where every observation has a sector and a non-null rank. No second/divergent value.

### TC-03 — Per-date attribution attached to each `by_horizon` entry on `/api/backtest`

**Type:** api
**Preconditions:** Backend running; a historical as-of date with ≥60 post-snapshot bars.

**Steps:**
1. `curl -s "http://localhost:8000/api/backtest" | python3 -m json.tool` (resolved to the global as-of date).
2. Inspect each `by_horizon[*]` entry.

**Expected outcome:** Every `by_horizon` entry carries its own `attribution` object with the same four slices.
**Pass criteria:** Each `by_horizon[h].attribution` contains `per_stock`/`by_sector`/`by_rank_band`/`distribution`; figures present for horizons with elapsed windows. HTTP 200.

### TC-04 — Honest NA: horizon with no elapsed forward window

**Type:** api
**Preconditions:** A recent as-of date where one or more horizons have no elapsed window (empty `stock_obs`).

**Steps:**
1. Set as-of to a recent date; fetch `/api/backtest`.
2. Inspect the `attribution` of a horizon with no elapsed window.

**Expected outcome:** Slices report NA, not fabricated zeros.
**Pass criteria:** Empty `stock_obs` → `distribution` all-None with `n: 0`; `per_stock` lists empty; group rows either absent or padded `{mean_return: null, n: 0}`. No `0%`/`0.0` substituted for missing data.

### TC-05 — Config-driven rank bands (no magic numbers)

**Type:** artifact
**Preconditions:** Repo checkout.

**Steps:**
1. Open `config.yaml`; confirm `walk_forward.attribution.rank_bands` (ordered `{label, min, max}`, `max: null` for open top band) and `top_contributors_k`.
2. Open `apps/backend/app/config.py`; confirm `AttributionCfg` nested under `WalkForwardCfg` with validation.
3. Grep `apps/backend/app/engine/forward_testing.py` for hard-coded band edges (e.g. `10`, `50`) or list-length literals in `_attribution_slices`.

**Expected outcome:** Bands and list length sourced from config; no literal band edge or list size in calc code.
**Pass criteria:** Both config keys present and typed-accessed; `_attribution_slices` references config for band edges and `top_contributors_k`; no magic band/length literal in calculation code.

### TC-06 — Config bands drive emitted output

**Type:** api
**Preconditions:** Backend test harness; ability to vary config in a unit test.

**Steps:**
1. In a unit test, render attribution with the default bands; record emitted `by_rank_band` labels.
2. Change `rank_bands` (and `top_contributors_k`) in config; re-run.

**Expected outcome:** Emitted band labels follow config; contributor/detractor list length follows `top_contributors_k`.
**Pass criteria:** Changing config changes the emitted bands; `len(contributors) == len(detractors) == top_contributors_k` (or fewer when observations are scarce).

### TC-07 — Edge cases: empty / single-observation / empty band

**Type:** api
**Preconditions:** Backend unit-test harness with crafted `stock_obs`.

**Steps:**
1. Empty `stock_obs` → all four slices.
2. Single-observation `stock_obs` → `distribution`.
3. Observations with no member in one config band → `by_rank_band`.

**Expected outcome:** Honest degenerate handling.
**Pass criteria:** Empty → all-None, `n: 0`; single obs → `dispersion: null` (no spurious 0 stdev); empty band → padded row `{mean_return: null, n: 0}`; observations with `rank is None` excluded from bands (not forced into a band).

### TC-08 — No-lookahead / no new data access inheritance

**Type:** artifact
**Preconditions:** Repo checkout.

**Steps:**
1. Inspect `_attribution_slices` and its callers in `forward_testing.py`.
2. Confirm it consumes only the already-built `stock_obs` (stored `forward_returns` ⋈ `scanner_results`).

**Expected outcome:** No new bar / `forward_returns` query introduced by attribution.
**Pass criteria:** `_attribution_slices` takes `stock_obs` as input and issues no DB/price-bar query; same observation set as the existing aggregate — existing no-lookahead guarantee unaffected.

### TC-09 — J-19 primary on `/system-health`

**Type:** browser
**Preconditions:** Frontend on :3000, backend on :8000; a horizon with samples.

**Steps:**
1. Navigate to `http://localhost:3000/system-health`.
2. Scroll to the new "Return attribution" section; select a horizon with samples.
3. Read all four panels.

**Expected outcome:** Four panels render real figures with `n`.
**Pass criteria:** Per-stock panel names individual tickers with realized mean return + `n` + sector; by-sector and by-rank-band show mean fwd return with `n`; distribution shows mean / median / % positive / dispersion each with `n`. Screenshot saved under `reports/qa/<phase>-evidence/`.

### TC-10 — J-19 primary on `/backtest` (historical date) + horizon view selector

**Type:** browser
**Preconditions:** Frontend + backend running; a historical as-of date with ≥60 post-snapshot bars set via the global as-of switcher.

**Steps:**
1. Navigate in-app to `/backtest` (not a hard reload).
2. Locate the "Return attribution" section and its horizon view selector.
3. Switch horizons; observe the panels update.

**Expected outcome:** Four panels render for the selected horizon; switching horizons re-renders from data already in the payload (no refetch).
**Pass criteria:** All four panels show numbers with `n` for the selected horizon; toggling the horizon selector changes the displayed slice with no network refetch and no change to the as-of date. Screenshot saved.

### TC-11 — J-19 honesty on `/backtest` (recent date)

**Type:** browser
**Preconditions:** As TC-10 but a recent as-of date where some horizons lack an elapsed window.

**Steps:**
1. Set a recent as-of date via the global switcher (in-app nav).
2. Open the attribution section; select a low/empty horizon.

**Expected outcome:** NA states, not fabricated numbers.
**Pass criteria:** `n=0` slices show "—" (NA); `n < min_sample` figures carry the existing `⚠` low-sample treatment; no-elapsed-window shows the existing empty-state copy. No fabricated figure anywhere.

### TC-12 — Regression: J-09 / J-10 System Health unchanged

**Type:** browser
**Preconditions:** Frontend + backend running.

**Steps:**
1. Navigate to `/system-health`.
2. Verify the existing aggregate panels and the control-group panel still render correct values.

**Expected outcome:** Pre-existing System Health surfaces are unchanged by the additive attribution section.
**Pass criteria:** Existing aggregate forward-return panels and control-group comparison render with correct values and `n`; no layout breakage or removed panel.

### TC-13 — Regression: J-14 / J-18 / J-13 Backtest single date control intact

**Type:** browser
**Preconditions:** Frontend + backend running.

**Steps:**
1. Navigate to `/backtest` via in-app nav (not a hard reload).
2. Change the as-of date using the single global switcher; confirm the scorecard updates.
3. Inspect the page for any independent/page-local date control.

**Expected outcome:** Exactly one date selector (the global `useAsOf()`); the new horizon selector is a view-only control.
**Pass criteria:** Scorecard updates with the global as-of change; the page holds no independent date state; the horizon selector does not alter the date and triggers no date effect. (Confirm in `apps/frontend/app/backtest/page.tsx` that the new `useState` is horizon-only.)

### TC-14 — Regression: J-01 baseline journey

**Type:** browser
**Preconditions:** Frontend + backend running.

**Steps:**
1. Exercise the J-01 baseline flow (per journey definition).

**Expected outcome:** J-01 still passes.
**Pass criteria:** J-01 flow completes with no regression; screenshot saved.

### TC-15 — Backend regression suite stays green

**Type:** artifact
**Preconditions:** Backend test command available.

**Steps:**
1. Run the backend pytest suite (per `.claude/project-template.md`).

**Expected outcome:** No regressions; new attribution tests included.
**Pass criteria:** Full suite passes (was 248/0 at iter-1; expect ≥248 plus the new attribution/consistency/config/edge tests, 0 failures).

### TC-16 — Dev handoff artifact exists

**Type:** artifact
**Preconditions:** Dev complete.

**Steps:**
1. Check `docs/handoffs/goal-i_can_see_the_wealthy_future_forever-iter-2-dev.md`.

**Expected outcome:** Handoff present and documents the additive change, including the call-out that the Backtest horizon selector is a view selector (not date state).
**Pass criteria:** File exists and notes the no-recompute seam and the view-only horizon selector.

### TC-17 — Opportunistic re-verify (no code): J-02, J-06, J-11, J-15, J-16

**Type:** browser
**Preconditions:** Frontend + backend running with healthy browser tooling.

**Steps:**
1. Exercise each of J-02, J-06, J-11, J-15, J-16 per its journey definition.
2. Capture fresh evidence (screenshots) for each.

**Expected outcome:** Fresh evidence captured for the evaluator to decide conversion of iter-0 partials.
**Pass criteria:** Each journey exercised and a screenshot saved under the evidence directory; pass/fail recorded (these do not block this iteration's verdict — evaluator decides conversion).

## Summary

Total test cases: 17
- API tests: 6 (TC-01, TC-02, TC-03, TC-04, TC-06, TC-07)
- Browser tests: 7 (TC-09, TC-10, TC-11, TC-12, TC-13, TC-14, TC-17)
- Artifact checks: 4 (TC-05, TC-08, TC-15, TC-16)

Coverage map: J-19 (TC-09, TC-10, TC-11); read-only/consistency anti-goal (TC-02, TC-08); no-magic-numbers (TC-05, TC-06); honesty/NA (TC-04, TC-07, TC-11); regressions J-09/J-10/J-13/J-14/J-18/J-01 (TC-12, TC-13, TC-14); backend suite (TC-15); opportunistic re-verify (TC-17).
