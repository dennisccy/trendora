# goal-i_can_see_the_wealthy_future_forever-iter-6 Functional Test Plan

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-6
**Date:** 2026-06-01
**Frontend Present:** yes

## Phase Goal

At a historical as-of date D, the Stock-Detail chart renders the full price/MA/volume path **through the latest seed date** with D marked and the post-D region labelled forward/display-only (J-20); and the Backtest page moves Top Sectors / Top Themes / Ranked Cohort **below Return Attribution**, each carrying a **realized forward-return at the selected horizon** read from stored forward returns (J-21) — all without contaminating the as-of scores or adding a second date control.

## Test Cases

### TC-01 — Bars endpoint extends through latest with as-of boundary (J-20)
**Type:** api
**Preconditions:** Backend running on :8000; seed data present; a historical as-of date D exists with bars dated > D; NVDA listed.

**Steps:**
1. `curl -s "http://localhost:8000/api/stocks/NVDA/bars?as_of=<historical-D>&through=latest"`
2. Inspect `asof_date`, `latest_date`, and the `bars[]` / `is_forward` fields.

**Expected outcome:** Response 200 with `asof_date` = resolved D, `latest_date` ≥ D, bars extending past D, and bars with `date > D` flagged `is_forward: true`; `ma` map covers the full series.
**Pass criteria:** At least one bar has `date > asof_date` AND `is_forward: true`; all bars with `date ≤ asof_date` have `is_forward` false/absent; `latest_date` present and > `asof_date`.

---

### TC-02 — Default bars contract stays ≤ D (no-lookahead default) (J-20)
**Type:** api
**Preconditions:** Same as TC-01.

**Steps:**
1. `curl -s "http://localhost:8000/api/stocks/NVDA/bars?as_of=<historical-D>"` (no `through` param).

**Expected outcome:** Response is byte-identical to today's contract — every bar has `date ≤ asof_date`; no `is_forward: true` bars.
**Pass criteria:** No bar has `date > asof_date`; behaviour unchanged from pre-iter-6 default (status 200, bars ≤ D only).

---

### TC-03 — Bars endpoint error/edge paths preserved (J-20)
**Type:** api
**Preconditions:** Backend running.

**Steps:**
1. `curl -s -o /dev/null -w "%{http_code}" "http://localhost:8000/api/stocks/ZZZZ/bars?through=latest"` (unknown ticker).
2. `curl -s -o /dev/null -w "%{http_code}" "http://localhost:8000/api/stocks/NVDA/bars?as_of=not-a-date&through=latest"` (invalid as_of).
3. `curl -s "http://localhost:8000/api/stocks/NVDA/bars?as_of=<latest-date>&through=latest"` (latest as-of edge).

**Expected outcome:** Unknown ticker → 404; invalid `as_of` → 4xx; latest as-of → 200 with **no** `is_forward: true` bars (no forward region). No fabricated rows in any case.
**Pass criteria:** Step 1 = 404; step 2 = 4xx (not 200, not 500); step 3 returns no bar with `date > asof_date`.

---

### TC-04 — No-lookahead: scores/VCP byte-identical with vs without forward bars (J-20, CRITICAL anti-goal)
**Type:** artifact
**Preconditions:** Backend test venv; `pytest` suite present.

**Steps:**
1. `cd apps/backend && .venv/bin/python -m pytest tests/ -v -k "through_latest or no_lookahead or bars_through"`
2. Confirm a test asserts the as-of-D snapshot row + `score_stocks`/`detect_vcp` output is unchanged whether or not post-D bars exist, and that `bars_through_latest` is NOT routed into `score_stocks`/`detect_vcp`/`run_scan`.

**Expected outcome:** Tests pass proving the forward extension never feeds the scoring path.
**Pass criteria:** Named no-lookahead test(s) PASS; grep confirms `bars_through_latest` is imported only by the bars endpoint / display path, not by `scanner.run_scan` / `scoring` / `patterns`.

---

### TC-05 — Leadership returns equal direct read of stored forward_returns (J-21, CRITICAL anti-goal)
**Type:** artifact
**Preconditions:** Backend test venv.

**Steps:**
1. `cd apps/backend && .venv/bin/python -m pytest tests/ -v -k "leadership_returns or leadership"`
2. Confirm tests assert: sector return = its ETF's stored `forward_returns` row; theme return = equal-weight mean of member rows; cohort return = the symbol's own row — at the given horizon, recomputing no return.

**Expected outcome:** Derived sector/theme/cohort returns equal a direct read of stored `forward_returns`; consistency with the existing scorecard (same stored observations).
**Pass criteria:** Named leadership-return equality test(s) PASS; `_leadership_returns` takes no Session and issues no query (source check).

---

### TC-06 — Honest NA for insufficient post-bars (J-21, No-fabricated-data)
**Type:** artifact
**Preconditions:** Backend test venv.

**Steps:**
1. `cd apps/backend && .venv/bin/python -m pytest tests/ -v -k "leadership and (na or null or insufficient)"`
2. Confirm a (row, horizon) lacking enough stored returns yields `null`/NA with honest `n`, never a fabricated 0%.

**Expected outcome:** Missing data surfaces as `null` (NA), not a synthesized number; theme with no member returns → `null`, n=0.
**Pass criteria:** Named NA test(s) PASS; no fabricated/extrapolated return value substituted for missing data.

---

### TC-07 — leadership_returns present per horizon in /api/backtest payload (J-21)
**Type:** api
**Preconditions:** Backend running; historical D with post-bars.

**Steps:**
1. `curl -s "http://localhost:8000/api/backtest?as_of=<historical-D>"`
2. Inspect `scorecard.by_horizon[*]` entries.

**Expected outcome:** Each `by_horizon` entry carries a `leadership_returns` object with `sectors`, `themes`, `cohort` lists keyed appropriately (sector_etf, slug, ticker), each with `mean_return`/`n`.
**Pass criteria:** `leadership_returns.sectors`, `.themes`, `.cohort` all present in every `by_horizon` entry; values match stored forward returns (cross-check vs TC-05). No new endpoint introduced.

---

### TC-08 — No magic numbers in forward_testing (J-21)
**Type:** artifact
**Preconditions:** Backend test venv.

**Steps:**
1. `cd apps/backend && .venv/bin/python -m pytest tests/ -v -k "no_magic_numbers"`

**Expected outcome:** `test_no_magic_numbers` passes — `_leadership_returns` introduces no integer literal row-cap; any bound comes from config.
**Pass criteria:** `test_no_magic_numbers` PASS.

---

### TC-09 — Full backend regression suite (no regressions)
**Type:** artifact
**Preconditions:** Backend test venv. (Note: full suite ~14 min; do not run two pytest invocations concurrently.)

**Steps:**
1. `cd apps/backend && .venv/bin/python -m pytest tests/ -v 2>&1 | tee reports/qa/goal-i_can_see_the_wealthy_future_forever-iter-6-test.log`

**Expected outcome:** All tests pass.
**Pass criteria:** Exit code 0; 0 failed, 0 errors. No previously-passing test regresses.

---

### TC-10 — Stock-Detail chart shows as-of divider + labelled forward region at historical D (J-20)
**Type:** browser
**Preconditions:** Frontend on :3000, backend on :8000. Use global as-of switcher + in-app nav (provider is in-memory; resets to Latest on hard reload).

**Steps:**
1. Open the app; set a **historical** as-of date D via the global switcher.
2. Navigate in-app to `/stocks/NVDA` (do not hard-reload).
3. Observe the price chart.
4. Save screenshot to `reports/qa/goal-i_can_see_the_wealthy_future_forever-iter-6-evidence/TC-10-chart-historical-divider.png`.

**Expected outcome:** Chart renders through the latest seed date with a visible **as-of divider/shaded region at D** and the post-D region labelled "forward / after-as-of (display only)". Divider uses design-system palette tokens (no ad-hoc hex).
**Pass criteria:** Legible screenshot shows (a) bars past D, (b) a divider/shaded boundary at D, (c) a forward-region label. This is the defining J-20 artifact — not a bare page-load shot.

---

### TC-11 — Scores/setup/VCP unchanged from ≤ D snapshot (J-20)
**Type:** browser
**Preconditions:** Continue from TC-10 (same historical D, /stocks/NVDA).

**Steps:**
1. On the historical-D Stock-Detail page, record the three score cards, setup status, VCP badge, and invalidation note.
2. Compare against the values served by `/api/stocks/NVDA` (snapshot row, bars ≤ D).

**Expected outcome:** The three scores, setup status, VCP flag, and invalidation note match the ≤ D snapshot exactly — the chart's forward extension does not alter them.
**Pass criteria:** Displayed scores/setup/VCP/invalidation equal the `fetchStock` (snapshot) values; no value shifts due to the forward chart bars.

---

### TC-12 — Latest as-of: chart shows no forward region (J-20 edge)
**Type:** browser
**Preconditions:** Continue in-app from TC-10/11.

**Steps:**
1. Set the global as-of switcher to **Latest** (in-app, no hard reload).
2. Stay/navigate to `/stocks/NVDA`.
3. Save screenshot to `.../TC-12-chart-latest-no-forward.png`.

**Expected outcome:** At the latest as-of there are no post-D bars → the chart is visually unchanged (no forward region, no divider beyond the end).
**Pass criteria:** No labelled forward region present; chart visually equivalent to pre-iter-6 latest view.

---

### TC-13 — Backtest section order: scorecard → Return Attribution → three lists (J-21)
**Type:** browser
**Preconditions:** Frontend + backend up; historical D with post-bars set via global switcher + in-app nav.

**Steps:**
1. Set historical D via global switcher; navigate in-app to `/backtest`.
2. Observe vertical section order.
3. Save screenshot to `.../TC-13-backtest-section-order.png`.

**Expected outcome:** Order is: as-of scan summary (regime + candidate counts) → forward-test scorecard → Return Attribution → **Top Sectors, Top Themes, Ranked Cohort** (the three leadership lists now BELOW Return Attribution).
**Pass criteria:** The three leadership lists render below the Return Attribution section; scan summary (regime/counts) remains at top.

---

### TC-14 — Realized-return column on each leadership list (J-21)
**Type:** browser
**Preconditions:** Continue from TC-13 (historical D with post-bars).

**Steps:**
1. On `/backtest`, inspect Top Sectors, Top Themes, and Ranked Cohort.
2. Confirm each list has a realized forward-return column populated at the selected horizon.

**Expected outcome:** Each of the three lists shows a realized-return column (sector = ETF return, theme = member mean, cohort = own return) at the current horizon, with honest "—" (NA) where data is missing.
**Pass criteria:** A return column is present and populated on all three lists; NA renders as "—" not a fabricated 0%.

---

### TC-15 — One horizon selector re-points all return columns + attribution (J-21, defining proof)
**Type:** browser
**Preconditions:** Continue from TC-14.

**Steps:**
1. Capture before-state of a leadership return column at horizon H1. Save `.../TC-15-before-horizon.png`.
2. Switch the **horizon view selector** to H2 (no page reload, no date change).
3. Capture after-state of the same column + the attribution panel. Save `.../TC-15-after-horizon.png`.

**Expected outcome:** Switching the single horizon selector re-points BOTH the three lists' return columns AND the Return Attribution — without any refetch, date param, or date-state change.
**Pass criteria:** Before/after screenshots show the return columns (and attribution) change together when the one selector flips; no second/independent selector involved.

---

### TC-16 — Recent as-of renders NA honestly (J-21 edge)
**Type:** browser
**Preconditions:** Frontend + backend up.

**Steps:**
1. Set the as-of to a **recent** date (short/no post-bars) via global switcher + in-app nav to `/backtest`.
2. Inspect the leadership return columns.
3. Save screenshot to `.../TC-16-backtest-recent-na.png`.

**Expected outcome:** Return columns show "—" (NA) for horizons lacking post-bars — no fabricated returns.
**Pass criteria:** NA ("—") rendered on the columns for a recent date; no synthesized numeric returns.

---

### TC-17 — No page-local date control on Backtest (J-18, Exactly-one-date-selector)
**Type:** browser
**Preconditions:** On `/backtest`.

**Steps:**
1. Inspect the Backtest page for any date picker/dropdown that is not the global as-of switcher.
2. Cross-check source: `app/backtest/page.tsx` holds no date state; the horizon control is a VIEW selector only.

**Expected outcome:** Only the global as-of switcher drives the date; the horizon selector changes the view, not the date. No `BacktestDatePicker`-style control exists.
**Pass criteria:** No page-local date picker present in UI or source; horizon selector triggers no refetch/date param.

---

### TC-18 — Required-still-passing journeys remain green (regression)
**Type:** browser
**Preconditions:** Frontend + backend up.

**Steps:**
1. Smoke the still-required journeys: J-05 (stock detail core), J-06, J-13, J-14 (backtest core), J-15, J-16, J-18 (single date control), J-19.
2. Confirm each renders and behaves as before via in-app nav.

**Expected outcome:** All eight required journeys continue to function; no regression from the iter-6 changes.
**Pass criteria:** J-05, J-06, J-13, J-14, J-15, J-16, J-18, J-19 each verified green (no broken page, no missing data, single date control intact).

---

## Summary

Total test cases: 18
API tests: 4 (TC-01, TC-02, TC-03, TC-07)
Browser tests: 9 (TC-10, TC-11, TC-12, TC-13, TC-14, TC-15, TC-16, TC-17, TC-18)
Artifact checks: 5 (TC-04, TC-05, TC-06, TC-08, TC-09)

**Critical anti-goal coverage:** No-lookahead (TC-02, TC-03, TC-04), Attribution-read-only / Single-source / No-recompute (TC-05, TC-07), No-fabricated-data (TC-06, TC-16), Exactly-one-date-selector / J-18 (TC-17). Defining journey artifacts: TC-10 (J-20 chart divider+forward region), TC-15 (J-21 one-selector re-points all columns).
