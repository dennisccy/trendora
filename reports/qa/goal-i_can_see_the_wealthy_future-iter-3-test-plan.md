# goal-i_can_see_the_wealthy_future-iter-3 Functional Test Plan

**Phase:** goal-i_can_see_the_wealthy_future-iter-3
**Date:** 2026-05-29
**Frontend Present:** yes

## Phase Goal

Ship the per-entity canonical scores — three independent, A–E-bucketed, explainable per-stock scores (Leadership / Entry Quality / Risk) + setup status, a price-confirmed Theme Score, and a completed dashboard rollup — each computed exactly once in the engine and read identically everywhere (Stock Leaderboard `/stocks`, Stock Detail `/stocks/[ticker]`, Theme Leaderboard `/themes`, Dashboard `/`), flipping J-02/J-03/J-06/J-01 while keeping J-04 green.

> **Environment note:** the managed `next dev` frontend runs on **port 3835** (not 3000). Backend API base is the FastAPI app. Before recording any browser SKIP/PASS, confirm port 3835 is up and stable and reconcile the verdict against the on-disk PNGs in `reports/qa/<phase>-evidence/`.

## Test Cases

### TC-01 — GET /api/stocks serves ranked canonical rows
**Type:** api
**Preconditions:** Backend up; seed data loaded (latest_data_date not None).

**Steps:**
1. `curl -s -w "\n%{http_code}" http://localhost:8000/api/stocks`
2. Inspect the JSON envelope and the first few rows.

**Expected outcome:** `200`; envelope `{asof_date, benchmark, rows[]}`; each row carries three scores (leadership/entry_quality/risk), each with `{bucket, score}`, a `components[]` array (each `{name, raw, percentile, weight, contribution, available}`), `setup` status and a non-empty `reason`, plus `sector`.
**Pass criteria:** Status 200; ≥2 rows; every row has all three scores each with ≥3 `available:true` components keyed to config weight keys; setup status ∈ the six configured statuses; reason non-empty.

---

### TC-02 — GET /api/stocks/{ticker} returns the SAME row as the list (J-06 single source)
**Type:** api
**Preconditions:** Backend up with seed data.

**Steps:**
1. `curl -s http://localhost:8000/api/stocks` → extract the NVDA row.
2. `curl -s http://localhost:8000/api/stocks/NVDA`.
3. Compare leadership/entry_quality/risk scores AND A–E buckets field-by-field.

**Expected outcome:** Detail row is byte-identical (scores + buckets + components) to the NVDA row from the list endpoint — no per-ticker recompute.
**Pass criteria:** All three scores and all three buckets equal between list and detail. Any divergence = FAIL (single-source anti-goal violation).

---

### TC-03 — GET /api/stocks/{ticker} unknown ticker → 404
**Type:** api
**Preconditions:** Backend up.

**Steps:**
1. `curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/stocks/ZZZZ`

**Expected outcome:** HTTP 404.
**Pass criteria:** Status code is exactly 404 (no fabricated row).

---

### TC-04 — GET /api/themes serves ranked theme rows
**Type:** api
**Preconditions:** Backend up with seed data.

**Steps:**
1. `curl -s http://localhost:8000/api/themes`
2. Inspect rows and ordering.

**Expected outcome:** `200`; `{asof_date, rows[]}`; ≥3 theme rows ranked by Theme Score (non-increasing); each row has score+bucket+components, member tickers, numeric 1m & 3m basket return, breadth %, and a trend label.
**Pass criteria:** Status 200; ≥3 rows; scores non-increasing; top theme exposes members, numeric 1m/3m returns, breadth %, trend label.

---

### TC-05 — GET /api/dashboard wired with real counts + Top Themes (J-01 backend)
**Type:** api
**Preconditions:** Backend up with seed data.

**Steps:**
1. `curl -s http://localhost:8000/api/dashboard`
2. Inspect `candidate_counts`, `top_themes`, `breadth`, regime fields, as-of date.

**Expected outcome:** `candidate_counts` is real (numeric # Actionable / Breakout-watch / Pullback-watch, no longer null); `top_themes` is ≥3 sliced theme rows each with a score; breadth/new-high-low unchanged from regime engine; regime + as-of present.
**Pass criteria:** `candidate_counts != null` with numeric values; `top_themes` length ≥3 each scored; breadth % present and labelled universe-relative; values match `/api/stocks` & `/api/themes` (no second computation).

---

### TC-06 — All three new endpoints return 503 on no data (no fabrication)
**Type:** api
**Preconditions:** A backend state with `latest_data_date is None` (or document as covered by unit test if env cannot be reproduced).

**Steps:**
1. Hit `/api/stocks`, `/api/stocks/NVDA`, `/api/themes` with no price data.

**Expected outcome:** Each returns 503, never a fabricated row.
**Pass criteria:** Status 503 on all three; no synthesized scores returned. (If live no-data state is not reproducible, mark covered-by-unit-test and verify pytest covers it.)

---

### TC-07 — Backend unit + integration suite green
**Type:** artifact
**Preconditions:** Repo at iter-3 state.

**Steps:**
1. `cd apps/backend && .venv/bin/python -m pytest tests/ -v 2>&1 | tee reports/qa/<phase>-test.log`

**Expected outcome:** All tests pass, including new `test_scoring.py`, `test_themes.py`, `test_setups.py`, extended `test_api_engine.py` (J-06 list==detail guard), `test_no_magic_numbers.py` (CALC_FILES += scoring/themes/setups/labels; FORBIDDEN_INT_LITERALS += 85 and new cutoffs), and config-validation tests.
**Pass criteria:** pytest exit code 0; 0 failures; new test files present and passing.

---

### TC-08 — Risk-off ⇒ zero Actionable (CRITICAL gate, unit)
**Type:** artifact
**Preconditions:** `test_setups.py` exists.

**Steps:**
1. Confirm `test_setups.py` feeds a Risk-off regime to `classify_setup` and asserts no row returns "Actionable" regardless of scores.
2. Confirm `summarize_candidates` counts statuses correctly.

**Expected outcome:** Test exists and passes asserting zero Actionable under Risk-off.
**Pass criteria:** A passing test explicitly proves Risk-off ⇒ zero Actionable. Absence of this test = FAIL.

---

### TC-09 — No magic numbers / single-source unit guards
**Type:** artifact
**Preconditions:** Test suite present.

**Steps:**
1. Confirm `test_no_magic_numbers.py` CALC_FILES includes `scoring.py`, `themes.py`, `setups.py`, `labels.py`.
2. Confirm changing a `config.scores.*` weight changes a score (single-source/config-driven test).
3. Confirm config-validation tests reject bad `theme_scores`/`scores` weights and missing `decision_rules` cutoffs with `ConfigError`.

**Expected outcome:** All present and passing.
**Pass criteria:** All three guard tests exist and pass; `models.py` unchanged (git diff empty for that file).

---

### TC-10 — /stocks Stock Leaderboard renders + filters (J-02, browser)
**Type:** browser
**Preconditions:** `next dev` on port 3835 up and stable; backend serving data.

**Steps:**
1. Navigate to `http://localhost:3835/stocks`. Screenshot → `reports/qa/<phase>-evidence/TC-10-leaderboard.png`.
2. Verify multiple ranked rows, each with three bucketed scores (bucket + number), a setup status badge, and a non-empty reason.
3. Apply the **Sector** filter (pick one sector). Screenshot → `TC-10-sector-filter.png`.
4. Apply **Setup-status = Actionable** filter. Screenshot → `TC-10-actionable-filter.png`.

**Expected outcome:** Dense dark table of ranked stocks; sector filter reduces rows to one sector; Actionable filter shows only Actionable rows (or an explicit EmptyState if none). Filtering is client-side re-display (scores unchanged).
**Pass criteria:** ≥2 ranked rows each showing 3 scores + status + reason; sector filter narrows to one sector; setup filter narrows correctly or shows EmptyState; verified against PNGs.

---

### TC-11 — /stocks/NVDA detail renders three scores + components (J-06 visual)
**Type:** browser
**Preconditions:** Frontend up on 3835.

**Steps:**
1. Click NVDA row on `/stocks` (or navigate to `/stocks/NVDA`). Screenshot → `TC-11-detail.png`.
2. Read the three scores (ScoreBadge + raw), buckets, ComponentBreakdown, setup status, reason.
3. Capture a side-by-side of NVDA scores on `/stocks` vs `/stocks/NVDA` → `TC-11-side-by-side.png`.

**Expected outcome:** Detail page shows the three scores with buckets, expandable component breakdown, setup status, reason — identical to the leaderboard row.
**Pass criteria:** NVDA Leadership/Entry Quality/Risk scores AND A–E buckets match exactly between `/stocks` and `/stocks/NVDA` (confirmed from screenshots). Any mismatch = FAIL.

---

### TC-12 — /themes Theme Leaderboard renders (J-03, browser)
**Type:** browser
**Preconditions:** Frontend up on 3835.

**Steps:**
1. Navigate to `http://localhost:3835/themes`. Screenshot → `TC-12-themes.png`.
2. Verify ≥3 themes ranked by Theme Score (non-increasing).
3. Inspect the top theme's member tickers, 1m & 3m basket returns, breadth %, trend label.
4. Expand a theme row's ComponentBreakdown. Screenshot → `TC-12-theme-breakdown.png`.

**Expected outcome:** ≥3 themes ranked non-increasing; top theme shows members + numeric 1m/3m returns + breadth % + trend label; expandable component breakdown.
**Pass criteria:** ≥3 ranked themes (non-increasing scores); top theme exposes members, numeric 1m & 3m returns, breadth %, trend label; verified against PNGs.

---

### TC-13 — Dashboard rollup complete (J-01, browser)
**Type:** browser
**Preconditions:** Frontend up on 3835.

**Steps:**
1. Navigate to `http://localhost:3835/`. Screenshot → `TC-13-dashboard.png`.
2. Verify regime label + score, three candidate counts (each a number), ≥3 Top Sectors, ≥3 Top Themes (each with a score), a breadth %, and a last-scan/as-of timestamp.

**Expected outcome:** Dashboard fully populated — placeholders replaced by real candidate counts and Top Themes.
**Pass criteria:** All of: regime label+score, 3 numeric candidate counts, ≥3 Top Sectors, ≥3 scored Top Themes, breadth %, as-of timestamp render; verified against PNG.

---

### TC-14 — /sectors regression after labels.py extraction (J-04, browser)
**Type:** browser
**Preconditions:** Frontend up on 3835.

**Steps:**
1. Navigate to `http://localhost:3835/sectors`. Screenshot → `TC-14-sectors.png`.
2. Verify the Sector Leaderboard still renders ranked sectors with scores/buckets/components unchanged.

**Expected outcome:** Sector Leaderboard unaffected by the `labels.py` consolidation (`sectors.py` now imports `labels.label_for`).
**Pass criteria:** `/sectors` renders ranked sectors identically to iter-2; no regression in output or layout.

---

### TC-15 — Frontend production build green
**Type:** artifact
**Preconditions:** iter-3 frontend code in place.

**Steps:**
1. `cd apps/frontend && npm run build 2>&1 | tee reports/qa/<phase>-fe-build.log`

**Expected outcome:** Build completes with no errors (new `lib/api.ts` types + four updated pages compile).
**Pass criteria:** Build exit code 0; no TypeScript/build errors.

---

### TC-16 — Blueprint additive update, no reapproval (artifact)
**Type:** artifact
**Preconditions:** iter-3 complete.

**Steps:**
1. Inspect `runs/goal-session-i_can_see_the_wealthy_future/state/blueprint.md` for the additive Data-Contract reconciliations (counts→`setups:summarize_candidates`, breadth→`regime:score_regime`) + iter-3 serving notes.
2. Confirm NO `blueprint.reapproval-requested` file was written (no nav-skeleton change).

**Expected outcome:** Blueprint additive edits present; no reapproval request.
**Pass criteria:** Data-contract reconciliations present; reapproval-request file absent.

---

### TC-17 — Dev + frontend + audit handoffs present (artifact)
**Type:** artifact
**Preconditions:** iter-3 complete.

**Steps:**
1. Check `docs/handoffs/goal-i_can_see_the_wealthy_future-iter-3-dev.md` exists (and frontend handoff per iter-1/2 pattern).
2. Check the audit handoff exists (iter-2 process gap to be closed this full-depth iteration).

**Expected outcome:** Handoffs written.
**Pass criteria:** Dev handoff exists and is non-empty; frontend + audit handoffs present per the full-depth pipeline.

---

### TC-18 — Error/edge cases: insufficient history & all-NA theme don't crash
**Type:** api
**Preconditions:** Backend up with seed data (covered by unit tests where live repro is impractical).

**Steps:**
1. Confirm a stock with insufficient history yields NA components (`available:false`) — not a crash or a fabricated 0 (via `/api/stocks` row inspection or `test_scoring.py`).
2. Confirm a theme whose members all lack history is gracefully NA/excluded — not a crash (via `/api/themes` or `test_themes.py`).

**Expected outcome:** Graceful NA handling, no fabrication, no crash.
**Pass criteria:** NA components shown `available:false` and excluded from the weighted sum; no fabricated zeros; endpoints return valid responses.

---

## Summary

Total test cases: 18
- API tests: 6 (TC-01, TC-02, TC-03, TC-04, TC-05, TC-06, TC-18) — *note TC-18 is api/unit hybrid*
- Browser tests: 5 (TC-10, TC-11, TC-12, TC-13, TC-14)
- Artifact checks: 6 (TC-07, TC-08, TC-09, TC-15, TC-16, TC-17)

Counts by primary type: **API 7, Browser 5, Artifact 6** (TC-18 counted under API).

**Critical/blocking cases:** TC-02 & TC-11 (J-06 single source — list==detail), TC-08 (Risk-off ⇒ zero Actionable gate), TC-09 (no magic numbers / `models.py` unchanged), TC-07 & TC-15 (suites + build green). A failure in any of these = overall FAIL.
