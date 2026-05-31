# goal-i_can_see_the_wealthy_future-iter-10 Functional Test Plan

**Phase:** goal-i_can_see_the_wealthy_future-iter-10
**Date:** 2026-05-31
**Frontend Present:** yes

## Phase Goal

Deliver J-14: a `/backtest` Time-Machine workspace where a user picks a historical as-of date,
sees that date's immutable as-of scan summary (regime / sectors / themes / ranked cohort) and a
per-date forward-test scorecard (realized 1/5/10/20/60d cohort returns, excess vs SPY/QQQ/sector,
control-group cohorts, each with sample size `n` and honest NA), computed only from seed bars
**after** the snapshot date — with no lookahead, no recompute in the read path, and no fabricated data.

## Test Cases

### TC-01 — Backtest endpoint serves scorecard for an omitted date (latest run)

**Type:** api
**Preconditions:** Backend running on :8835 with seed data; at least one stored `scanner_run`.

**Steps:**
1. `curl -s -w "\n%{http_code}" http://localhost:8835/api/backtest`

**Expected outcome:** 200 with JSON containing `asof_date`, `is_latest: true`, `min_sample` (int),
`horizons: [1,5,10,20,60]`, `survivorship_bias` (non-empty label), and
`scorecard.by_horizon` (array of 5 rows; each with `cohort.{mean_return,n}`,
`excess.{vs_spy,vs_qqq,vs_sector}`, `control_group` of 5 cohorts each with `mean_return`+`n`).
**Pass criteria:** HTTP 200; `is_latest == true`; `horizons == [1,5,10,20,60]`; `by_horizon` length 5;
every figure carries an `n`; no top-level recompute error.

---

### TC-02 — Full-window historical date renders numeric scorecard

**Type:** api
**Preconditions:** A historical run date D exists with ≥60 post-snapshot seed bars (obtain a D from
`GET /api/runs`, choosing an early/older run).

**Steps:**
1. `curl -s http://localhost:8835/api/backtest?as_of=<D>`

**Expected outcome:** 200; `asof_date == D`; `is_latest == false`; the 1/5/10/20/60d rows each return
a numeric `cohort.mean_return` (not null) with `n >= 1`, numeric `excess.vs_spy/vs_qqq/vs_sector`,
and a `random_same_sector` control cohort present in `control_group`.
**Pass criteria:** All five horizons have non-null `cohort.mean_return` and `n > 0`; `random_same_sector`,
`top_ranked`, `spy`, `qqq`, `sector_etf` all present in `control_group`.

---

### TC-03 — Partial/recent date shows honest NA, never fabricated numbers

**Type:** api
**Preconditions:** The latest run date (0 post-snapshot bars) or a recent date with fewer than 60 post-bars.

**Steps:**
1. `curl -s http://localhost:8835/api/backtest?as_of=<latest-D>`

**Expected outcome:** Horizons lacking ≥`h` post-bars return `cohort.mean_return: null` and `n: 0`;
shorter observable horizons (if any) render numerically; the latest-date run is all-NA.
**Pass criteria:** Unobservable horizons have `mean_return == null` AND `n == 0` (no `0.0` substituted
for missing data); no horizon fabricates a return where `n == 0`.

---

### TC-04 — Invalid / edge `as_of` returns explicit status, never a fabricated scorecard

**Type:** api
**Preconditions:** Backend running.

**Steps:**
1. Future date: `curl -s -o /dev/null -w "%{http_code}" "http://localhost:8835/api/backtest?as_of=2099-01-01"`
2. Unparseable: `curl -s -o /dev/null -w "%{http_code}" "http://localhost:8835/api/backtest?as_of=not-a-date"`
3. Before history: `curl -s -o /dev/null -w "%{http_code}" "http://localhost:8835/api/backtest?as_of=1990-01-01"`

**Expected outcome:** Future → 400; unparseable → 422; before_history → 400 (per the iter-8
`_STATUS_BY_KIND` map); a no-price-data resolution → 503. No 200 with a synthesized scorecard.
**Pass criteria:** Each edge returns the mapped 4xx/503 status; none returns 200 with fabricated data.

---

### TC-05 — KEYSTONE: read path recomputes nothing (patch-to-raise seam)

**Type:** artifact (pytest)
**Preconditions:** A new `apps/backend/tests/test_backtest_scorecard.py` / `test_api_backtest.py` exists.

**Steps:**
1. Locate the test that, after a date is populated, monkeypatches `forward_testing.forward_return`
   AND `app.engine.scanner.{score_stocks,score_regime,score_sectors,score_themes}` to raise, then
   asserts `GET /api/backtest?as_of=D` (or `compute_run_scorecard`) still serves from stored rows.
2. Run: `cd apps/backend && python -m pytest tests/test_backtest_scorecard.py tests/test_api_backtest.py -q`

**Expected outcome:** The keystone test passes — serving an already-populated date does not call the
patched (raising) compute functions.
**Pass criteria:** A patch-to-raise (NOT value-equality) keystone test exists and passes; serving the
populated date does not raise.

---

### TC-06 — No-lookahead boundary + create-once immutability (unit)

**Type:** artifact (pytest)
**Preconditions:** New backtest tests exist.

**Steps:**
1. Run the no-lookahead test: scorecard for run D measures returns only from bars date > D (entry
   close ON D); no bar with date ≤ D contributes.
2. Run the create-once test: a 2nd `/api/backtest` view / `backfill_run_forward_returns` call INSERTs
   zero new `forward_returns` rows and performs NO UPDATE on `scanner_runs`/`scanner_results`.

**Expected outcome:** Both tests pass.
**Pass criteria:** No-lookahead test asserts only date>D bars contribute; idempotency test asserts
0 new rows on 2nd call and 0 mutations of snapshot tables.

---

### TC-07 — Single source: scorecard reads stored buckets and agrees with aggregates

**Type:** artifact (pytest)
**Preconditions:** New backtest tests exist; `compute_forward_aggregates` available.

**Steps:**
1. Run the test asserting cohort observations group by **stored** `leadership_bucket`/`setup_status`/
   `rank`/`sector` (verbatim, not re-derived).
2. Run the cross-check: `compute_run_scorecard` scoped to one run agrees with
   `compute_forward_aggregates` filtered to that run.

**Expected outcome:** Both pass — single shared forward-return math, no re-bucketing.
**Pass criteria:** Tests confirm stored-value grouping and agreement between the two compute paths.

---

### TC-08 — Refactor preserves iter-6 forward-testing suite byte-green + no magic numbers

**Type:** artifact (pytest)
**Preconditions:** `_insert_run_forward_returns` factored out of `_backfill`.

**Steps:**
1. `cd apps/backend && python -m pytest tests/test_forward_testing.py tests/test_no_magic_numbers.py -q`
   (or the suite-wide `test_no_magic_numbers`).
2. Run the full suite: `python -m pytest -q`.

**Expected outcome:** iter-6 forward-testing tests pass unchanged; `test_no_magic_numbers` green
(no horizon/`min_sample`/`top_n`/seed literal in `app/api/backtest.py` or the new forward-testing
functions — all from `config.walk_forward`); full suite green.
**Pass criteria:** Full backend pytest exit 0; forward-testing + no-magic-numbers tests pass.

---

### TC-09 — Implementation actually present (anti-no-op gate)

**Type:** artifact
**Preconditions:** None.

**Steps:**
1. Verify files exist: `apps/backend/app/api/backtest.py`, `apps/frontend/app/backtest/page.tsx`,
   `apps/backend/tests/test_backtest*.py`.
2. `grep -n "def compute_run_scorecard\|def backfill_run_forward_returns\|def _insert_run_forward_returns" apps/backend/app/engine/forward_testing.py`
3. `grep -n "/backtest" apps/frontend/components/sidebar.tsx`; `grep -n "fetchBacktest" apps/frontend/lib/api.ts`
4. Verify `app.include_router(backtest.router, prefix="/api")` in `apps/backend/main.py`.
5. Verify dev handoff `docs/handoffs/goal-i_can_see_the_wealthy_future-iter-10-dev.md` exists; `git diff` shows real `apps/` changes.

**Expected outcome:** All files/functions/edits present; dev handoff exists; non-empty `apps/` diff.
**Pass criteria:** Every listed path/symbol/edit present; handoff file exists. (Any missing → FAIL.)

---

### TC-10 — Frontend build clean

**Type:** artifact
**Preconditions:** Frontend deps installed.

**Steps:**
1. `cd apps/frontend && npm run build`

**Expected outcome:** Compile + typecheck succeed (new types `BacktestResponse`/`BacktestScorecard`/
`BacktestScorecardHorizonRow` resolve; `mean_return`/`mean_excess` are `number | null`).
**Pass criteria:** `npm run build` exits 0 with no type errors.

---

### TC-11 — Sidebar Backtest entry routes to /backtest

**Type:** browser
**Preconditions:** Frontend on :3835, backend on :8835 (CORS allows :3835).

**Steps:**
1. Navigate to `http://localhost:3835/`.
2. Locate the **Backtest** nav entry (after Scanner Runs / before System Health) and click it.

**Expected outcome:** URL becomes `/backtest`; the Backtest workspace renders with a date picker.
**Pass criteria:** Backtest sidebar link visible, one click reaches `/backtest`. Capture `TC-11-sidebar-nav.png`.

---

### TC-12 — Full-window date renders scan summary + numeric scorecard (J-14 happy path)

**Type:** browser
**Preconditions:** `/backtest` loads; an older run date with ≥60 post-bars selectable.

**Steps:**
1. On `/backtest`, pick an older historical date from the page's date picker.
2. Read the as-of scan summary; read the forward-test scorecard.

**Expected outcome:** Scan summary shows regime label (one of the six) + numeric score, ≥3 top sectors,
≥3 top themes, candidate counts, the ranked cohort. Scorecard shows numeric 1/5/10/20/60d cohort
returns with excess-vs-SPY/QQQ/sector + random-same-sector-control columns, each with `n`. Survivorship
banner and "Viewing as-of D" indicator visible.
**Pass criteria:** All scan-summary fields populated AND ≥1 numeric scorecard cell with an `n` value;
survivorship banner present. Capture **focused** `TC-12-scorecard-full.png` (scorecard panel; md5-distinct).

---

### TC-13 — Recent/latest date renders honest NA in the UI

**Type:** browser
**Preconditions:** `/backtest` loads; latest date selectable.

**Steps:**
1. On `/backtest`, pick the latest/recent date.
2. Inspect the longer-horizon scorecard rows.

**Expected outcome:** Longer horizons render `—` / NA with `n=0`; no fabricated numbers. `n < min_sample`
figures flagged with the `⚠` warn token.
**Pass criteria:** At least one longer horizon shows `—`/`n=0`; no numeric return where `n=0`.
Capture **focused** `TC-13-scorecard-partial.png` (md5-distinct from TC-12 capture).

---

### TC-14 — J-13 global switcher did not regress

**Type:** browser
**Preconditions:** Frontend + backend running.

**Steps:**
1. Navigate to `/` (or `/stocks`).
2. Use the global top-bar as-of switcher to select a historical date.

**Expected outcome:** The page time-travels to the chosen date (values update); the global switcher
still drives Dashboard/Stocks/Themes/Sectors/Stock Detail as before.
**Pass criteria:** Switcher changes the page's as-of values without error. Capture `TC-14-j13-switcher.png`.

---

### TC-15 — Scan summary values match canonical pages (single source)

**Type:** browser
**Preconditions:** `/backtest` and the canonical pages reachable for the same date D.

**Steps:**
1. On `/backtest`, pick date D; note the regime label/score and a top sector/theme value.
2. Open `/` (dashboard) and `/sectors` switched to D; compare.

**Expected outcome:** The `/backtest` scan-summary values are byte-identical to the canonical pages
for D (the page reuses `fetchDashboard/fetchSectors/fetchThemes/fetchStocks` — no second source).
**Pass criteria:** Regime label/score and the compared sector/theme value match exactly across views.

---

## Summary

Total test cases: 15
- **API tests: 4** — TC-01, TC-02, TC-03, TC-04
- **Artifact checks: 6** — TC-05, TC-06, TC-07, TC-08 (pytest); TC-09 (file/symbol presence); TC-10 (frontend build)
- **Browser tests: 5** — TC-11, TC-12, TC-13, TC-14, TC-15

**Note (per spec NOTES / Out-of-scope):** the dedicated browser-qa has SKIPPED on an HTTP-000/CORS flap
for 8+ iterations. If browser checks (TC-11–TC-15) SKIP again, J-14 should be reconciled from on-disk
QA evidence PNGs + the unit/API proofs (TC-01–TC-08) + direct source reads — a SKIP is not a FAIL.
