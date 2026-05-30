# goal-i_can_see_the_wealthy_future-iter-6 Functional Test Plan

**Phase:** goal-i_can_see_the_wealthy_future-iter-6
**Date:** 2026-05-30
**Frontend Present:** yes

## Phase Goal

Deliver a strict no-lookahead walk-forward forward-testing engine that replays scans as-of past dates, measures realized 1/5/10/20/60-day forward returns from post-snapshot data into an append-only `forward_returns` table, and surfaces the evidence (returns by bucket/setup/regime, excess vs SPY/QQQ, control-group comparison — each with sample size `n` and a survivorship-bias label) on a populated `/system-health` dashboard (J-09, J-10), without mutating the immutable snapshot or regressing J-01–J-08.

## Test Cases

### TC-01 — `bars_after` no-lookahead boundary

**Type:** api (unit/pytest)
**Preconditions:** Seeded test DB; `bars_after` implemented in `app/engine/prices.py`.

**Steps:**
1. For a symbol with bars spanning a date `d`, call `bars_after(session, symbol, d)`.
2. Inspect returned bars' dates and order.

**Expected outcome:** Returns only bars with `date > d`, none with `date ≤ d`, in ascending date order — strict inverse of `bars_asof`.
**Pass criteria:** Test asserts every returned bar date `> d`, list is ascending, and no bar with `date == d` or earlier is present.

---

### TC-02 — `forward_return` purity: horizon-bound, NA, entry-close-on-D

**Type:** api (unit/pytest)
**Preconditions:** `forward_return(bars_after_list, entry_close, horizon)` implemented; horizons read from `config.walk_forward.horizons`.

**Steps:**
1. Compute `forward_return` for horizon `h` on a fixture with ≥ `h` post-bars.
2. Remove all bars dated `> d+h` and recompute.
3. Compute with fewer than `h` post-bars available.
4. Verify `entry_close` is the close on `asof_date` (≤ D).

**Expected outcome:** Result = `close[h-th post-bar]/entry_close − 1`; unchanged when later bars (`> d+h`) are removed; returns `None` (NA) when `< h` post-bars exist; entry close is the on-D close.
**Pass criteria:** Equality of result before/after removing later bars; `None` returned on insufficient bars (no fabricated/truncated number); entry close matches the close on D.

---

### TC-03 — Forward returns never feed back into snapshot scores

**Type:** api (unit/pytest)
**Preconditions:** A persisted `scanner_run` with stored scores; backfill available.

**Steps:**
1. Capture a pre-existing run's stored scores/buckets/setups.
2. Run `backfill_forward_returns` (which creates `forward_returns`).
3. Re-read the run's stored scores.

**Expected outcome:** Stored scores are byte-identical with vs without post-snapshot bars / `forward_returns` — forward returns never influence an as-of score.
**Pass criteria:** Faithful-equality check of the run's score/bucket/setup rows before vs after backfill passes (no field changed).

---

### TC-04 — Immutability: backfill is INSERT-only

**Type:** api (integration/pytest)
**Preconditions:** DB with existing `scanner_runs` / `scanner_results` / `*_scores` rows.

**Steps:**
1. Record row counts and field snapshots of `scanner_runs`, `scanner_results`, `*_scores`.
2. Run `backfill_forward_returns`.
3. Compare counts and snapshots; inspect `forward_returns` for new rows.

**Expected outcome:** No UPDATE/overwrite of any snapshot row; new rows appear only in `forward_returns`.
**Pass criteria:** Snapshot-table row counts and field values unchanged; `forward_returns` row count increased; faithful-equality on a pre-existing run holds.

---

### TC-05 — Backfill idempotency

**Type:** api (integration/pytest)
**Preconditions:** Backfill already run once.

**Steps:**
1. Record `forward_returns` row count.
2. Call `backfill_forward_returns` a second time.
3. Re-count.

**Expected outcome:** Second call inserts zero new `forward_returns` rows (and creates no duplicate `scanner_run`).
**Pass criteria:** `forward_returns` row count identical before and after the second call; `(run_id, symbol, horizon)` uniqueness preserved.

---

### TC-06 — `compute_forward_aggregates` correctness on hand-built fixture

**Type:** api (unit/pytest)
**Preconditions:** Small hand-built fixture of `scanner_results` + `forward_returns` with known values.

**Steps:**
1. Call `compute_forward_aggregates(session, horizon, config)`.
2. Compare by-bucket (A–E), by-setup, by-regime means + `n`, excess vs SPY/QQQ, and control-group cohort means against hand-computed values.
3. Verify by-bucket grouping uses stored `scanner_results.leadership_bucket` verbatim.

**Expected outcome:** All aggregate means and `n` match hand-computed values exactly; buckets/setups/sectors/regime are READ verbatim — never re-bucketed or recomputed.
**Pass criteria:** Exact numeric equality for every cell; grouping key proven to be the stored bucket (no second formula).

---

### TC-07 — Control-group determinism

**Type:** api (unit/pytest)
**Preconditions:** `control_group.seed` set in config; random-same-sector cohort drawn with config-seeded RNG.

**Steps:**
1. Call `compute_forward_aggregates` twice (and across a simulated restart).
2. Compare the random-same-sector cohort membership.

**Expected outcome:** Same config seed → identical cohort each time.
**Pass criteria:** Cohort membership byte-identical across both calls / restart (reproducible; no bare `random`).

---

### TC-08 — No fabrication: n=0 run and both regimes present

**Type:** api (integration/pytest)
**Preconditions:** Seeded as-of dates including the latest seed-date run (no post-bars) and the Risk-off date 2025-04-04.

**Steps:**
1. Run backfill + `compute_forward_aggregates`.
2. Inspect the latest-seed-date run's contribution.
3. Inspect the by-regime breakdown entries.

**Expected outcome:** Zero-post-bar run contributes `n=0` (excluded) with no fabricated return; by-regime breakdown contains BOTH a Risk-on and a Risk-off entry.
**Pass criteria:** No fabricated 0% from the empty run; both Risk-on and Risk-off keys present in the by-regime result.

---

### TC-09 — No magic numbers guard extended

**Type:** api (unit/pytest)
**Preconditions:** No-literal guard test extended to `forward_testing.py` and `prices.bars_after`.

**Steps:**
1. Run the no-magic-numbers guard test.

**Expected outcome:** horizons, min_sample, history_years, asof_cadence, and control-group `{seed, top_n, peers_per_sector}` all sourced from config; benchmark symbols from `config.etfs`.
**Pass criteria:** Guard passes — no scoring/threshold literal in `forward_testing.py` or `bars_after` calculation code.

---

### TC-10 — `GET /api/system-health` default + non-default horizon

**Type:** api
**Preconditions:** Backend running on :8000 with backfilled data.

**Steps:**
1. `curl -s -w "\n%{http_code}" http://localhost:8000/api/system-health`
2. `curl -s -w "\n%{http_code}" "http://localhost:8000/api/system-health?horizon=5"`

**Expected outcome:** 200 with payload containing by-bucket/setup/regime breakdowns + excess vs SPY/QQQ + control groups, each cell carrying `n`, plus a `survivorship_bias` label and a `min_sample` field; default request behaves as horizon=20.
**Pass criteria:** Both return HTTP 200; JSON contains by_bucket, by_setup, by_regime, excess_vs_spy, excess_vs_qqq, control_group, `n` per cell, survivorship label, and min_sample; payloads differ between horizons.

---

### TC-11 — `GET /api/system-health` invalid horizon → 422

**Type:** api
**Preconditions:** Backend running.

**Steps:**
1. `curl -s -o /dev/null -w "%{http_code}" "http://localhost:8000/api/system-health?horizon=999"`

**Expected outcome:** Out-of-range horizon (∉ config.walk_forward.horizons) rejected.
**Pass criteria:** HTTP 422.

---

### TC-12 — `GET /api/system-health` 503 when no price data

**Type:** api
**Preconditions:** A DB state with no price data (or documented inference from code path).

**Steps:**
1. Call `/api/system-health` against an empty-price-data backend.

**Expected outcome:** Explicit unavailable state, not fabricated data.
**Pass criteria:** HTTP 503 returned; no synthesized prices/scores.

---

### TC-13 — J-01–J-08 regression guard (endpoints byte-identical)

**Type:** api
**Preconditions:** Backend running.

**Steps:**
1. `curl` each of `/api/dashboard`, `/api/stocks`, `/api/sectors`, `/api/themes`, `/api/stocks/{ticker}/bars`, `/api/runs`, `/api/runs/{run_id}`.
2. Verify J-07: in a Risk-Off run, zero stocks marked "Actionable".

**Expected outcome:** All live + run endpoints return HTTP 200 with behaviourally identical shapes; Risk-Off run has zero Actionable.
**Pass criteria:** Each endpoint 200 and unchanged shape; Risk-Off Actionable count = 0; `/api/runs` returns ≥2 dated runs (walk-forward cadence adds runs — intended, not a regression).

---

### TC-14 — J-09: System Health by-bucket/setup/regime + excess render (browser)

**Type:** browser
**Preconditions:** Frontend on :3000, backend on :8000 with backfilled data.

**Steps:**
1. Navigate to `http://localhost:3000/system-health`.
2. Verify a by-bucket (A–E) forward-return table renders numeric means.
3. Verify numeric excess-vs-SPY and excess-vs-QQQ figures.
4. Verify by-setup-type and by-regime breakdowns render numbers.
5. Verify a sample size `n` is shown beside figures and a survivorship-bias caveat is visible.
6. Screenshot to `reports/qa/goal-i_can_see_the_wealthy_future-iter-6-evidence/TC-14-system-health-j09.png`.

**Expected outcome:** All J-09 panels render numeric values with `n` and the survivorship caveat.
**Pass criteria:** By-bucket table (rows A–E) shows numbers; excess-vs-SPY and excess-vs-QQQ numeric; by-setup and by-regime numeric; `n` and survivorship-bias label visible. (Structural/relational assertions — NOT exact return values.)

---

### TC-15 — J-09: Horizon selector changes figures (browser)

**Type:** browser
**Preconditions:** `/system-health` loaded with data.

**Steps:**
1. Note displayed figures at default horizon (20).
2. Click the horizon selector to a different horizon (e.g. 5).
3. Observe the tables/panels re-fetch and update.
4. Screenshot to `.../TC-15-horizon-change.png`.

**Expected outcome:** Page re-fetches `/api/system-health?horizon=…` and the displayed figures change.
**Pass criteria:** Figures differ between two horizons; selector default is 20; no client-side recomputation (values come from payload).

---

### TC-16 — J-10: Control-group comparison panel (browser)

**Type:** browser
**Preconditions:** `/system-health` loaded with data.

**Steps:**
1. Locate the control-group comparison panel.
2. Verify it shows top-ranked cohort, random-same-sector cohort, SPY, QQQ, and sector-ETF returns at the selected horizon.
3. Verify each is numeric, labelled, and carries `n`.
4. Screenshot to `.../TC-16-control-group-j10.png`.

**Expected outcome:** Control-group panel shows all five cohorts, each numeric, labelled, with `n`.
**Pass criteria:** Top-ranked, random-same-sector, SPY, QQQ, and sector-ETF all present, numeric, labelled, with sample size `n` shown.

---

### TC-17 — Low-sample / unavailable states explicit (browser)

**Type:** browser
**Preconditions:** `/system-health`; `min_sample` from config (30).

**Steps:**
1. Inspect cells with `n < min_sample`.
2. (If reachable) inspect the "Backend unavailable" state by simulating fetch failure.

**Expected outcome:** Low-sample figures visibly flagged (warn token) with `n` shown; unavailable/empty states explicit — never hidden or fabricated.
**Pass criteria:** Low-sample cells display `n` and a warn flag; failure renders an explicit unavailable state (no fabricated numbers).

---

### TC-18 — Dev handoff artifact present and complete

**Type:** artifact
**Preconditions:** Phase implementation complete.

**Steps:**
1. Open `docs/handoffs/goal-i_can_see_the_wealthy_future-iter-6-dev.md`.

**Expected outcome:** Handoff documents chosen walk-forward cadence, as-of date count, first-boot backfill time, and confirms both Risk-on and Risk-off as-of dates are present in the by-regime sample.
**Pass criteria:** File exists and contains all four documented items.

---

### TC-19 — Frontend build green

**Type:** artifact
**Preconditions:** Frontend changes complete.

**Steps:**
1. Run `npm run build` in `apps/frontend`.

**Expected outcome:** Build/typecheck succeeds for all routes including `/system-health`.
**Pass criteria:** `npm run build` exits 0 with no type errors.

---

## Summary

Total test cases: 19
- API tests (incl. unit/integration pytest): 13 — TC-01 to TC-13
- Browser tests: 4 — TC-14, TC-15, TC-16, TC-17
- Artifact checks: 2 — TC-18, TC-19

Coverage maps to DoD J-09 (TC-14, TC-15), J-10 (TC-16); no-lookahead keystone (TC-01–TC-03); immutability/idempotency (TC-04, TC-05); single-source aggregates (TC-06); control-group determinism (TC-07); no-fabrication & both regimes (TC-08, TC-12, TC-17); no-magic-numbers (TC-09); API contract (TC-10–TC-12); J-01–J-08 regression guard (TC-13); handoff + build artifacts (TC-18, TC-19).
