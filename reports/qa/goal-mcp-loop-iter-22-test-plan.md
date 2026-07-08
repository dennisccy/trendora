# Goal Iteration 22 Functional Test Plan

**Phase:** goal-mcp-loop-iter-22  
**Date:** 2026-07-08  
**Frontend Present:** yes

## Phase Goal

Surface the committed deep index context — the equity-index benchmarks `^SPX`/`^NDX`/`^DJI` (deep to 1996) and the `^VIX` / FRED-macro-proxy overlays — across the deep 30-year window on the Dashboard major-indexes chart, each labeled with its honest data vendor (Stooq / Yahoo / FRED-macro proxy), and disclose the same per-series vendor on `/data`.

## Test Cases

### TC-01 — Deep benchmark lines render on Dashboard chart across full history

**Type:** browser  
**Preconditions:**
- Backend services running in prod mode (`:8255`)
- Frontend running in prod mode (`:3255`)
- `.next` build cache cleared (`rm -rf apps/frontend/.next`)
- Database populated with deep index series bars (`^SPX`, `^NDX`, `^DJI`)

**Steps:**
1. Navigate to Dashboard (`http://localhost:3255`)
2. Locate the major-indexes chart
3. Change the range dropdown to "all" (if not already set)
4. Scroll chart into view and take a full-page screenshot
5. Verify that a benchmark line (e.g. `^SPX`) extends visibly before SPY's 2005 start (to ~1996)

**Expected outcome:**  
Deep benchmark line extends back to 1996, visibly beyond the ETF lines' 2005 start.

**Pass criteria:**  
- A line on the chart is labeled with a deep index symbol (`^SPX`) and its first visible date is before 2005 (e.g. 1996 or early 2000s).
- The screenshot md5 shows the line is truly rendered, not relabeled from a prior run.

---

### TC-02 — Chart legend shows vendor labels (Stooq / Yahoo / FRED-macro proxy)

**Type:** browser  
**Preconditions:**
- Same as TC-01
- Dashboard chart fully rendered with all configured index/benchmark series

**Steps:**
1. Navigate to Dashboard
2. Locate the major-indexes chart legend/tooltip area
3. Hover over or inspect the legend entries for series (SPY, ^SPX, ^VIX, etc.)
4. Take a screenshot of the legend showing vendor labels
5. Verify vendor labels are present for deep series and macro series

**Expected outcome:**  
Legend shows vendor labels: "Stooq" for `^SPX`/`^NDX`/`^DJI`, "Yahoo" for `^VIX`, "FRED-macro proxy" for macro series.

**Pass criteria:**  
- Vendor label text is visible in the legend for at least three series spanning all three vendor categories (Stooq, Yahoo, FRED-macro-proxy).
- No fabricated vendors; ETF lines (SPY/QQQ) show no vendor label or null.

---

### TC-03 — /data vendor-disclosure panel lists all series with vendor + first date

**Type:** browser  
**Preconditions:**
- Backend services running (`:8255`)
- Frontend running (`:3255`)
- GET /api/indexes endpoint returns series with `vendor` and `first` fields

**Steps:**
1. Navigate to `/data` page (`http://localhost:3255/data`)
2. Scroll down to locate the new vendor-disclosure panel (after MacroFeedPanel)
3. Take a screenshot of the vendor-disclosure panel
4. Verify each deep series lists: name, vendor, and first-bar date
5. Verify FRED-macro-proxy series is labeled honestly (not as market index)

**Expected outcome:**  
A dedicated panel lists index/benchmark/macro series with vendor badges and first-bar dates.

**Pass criteria:**  
- Panel is present on the `/data` page below the existing MacroFeedPanel.
- Each entry shows a series name, vendor (e.g., "Stooq", "Yahoo", "FRED-macro proxy"), and first date (e.g., `^SPX` → `1996-01-02`).
- FRED-macro-proxy series read as "FRED-macro proxy" (never as market index).
- Screenshot md5 confirms visual presence (not relabeled from a prior run).

---

### TC-04 — GET /api/indexes returns additive vendor + first fields; existing points byte-identical

**Type:** api  
**Preconditions:**
- Backend service running on `:8255`

**Steps:**
1. Run: `curl -s http://localhost:8255/api/indexes | jq '.series[] | select(.symbol | test("^SPY|^QQQ|^SPX")) | {symbol, vendor, first, points_count: (.points | length)}'`
2. Verify response includes `vendor` and `first` fields for all series
3. Confirm `^SPX` has `vendor: "Stooq"` and `first: "1996-01-02"` (or the actual first date from meta.json)
4. Compare the `points` array length for SPY/QQQ with a baseline (from git or prior log)
5. Run a test: golden-record the normalized-% `points[0].normalized_pct` for SPY, QQQ on a fixed date, and re-fetch to verify byte-identity

**Expected outcome:**  
- API response includes `vendor` (string or null) and `first` (ISO date string) for each series.
- Existing SPY/QQQ/IWM/RSP/DIA `points` arrays contain the same normalized-% values (byte-identical).
- New deep series (`^SPX`, `^NDX`, `^DJI`) are present with correct vendor and first-bar metadata.

**Pass criteria:**  
- HTTP 200; response is valid JSON.
- All configured series have a `vendor` field (null for ETFs, string for deep/macro).
- All series have a `first` field (ISO date).
- SPY normalized-% points match golden record exactly (to 10 decimal places).
- `^SPX` first date == `1996-01-02` (or meta.json value).

---

### TC-05 — Deep series are absent from scored universe / leaderboard

**Type:** api  
**Preconditions:**
- Backend service running
- Database populated with all configured symbols

**Steps:**
1. Run: `curl -s http://localhost:8255/api/stocks | jq '.leaderboard | length' > /tmp/stock_count.txt`
2. Record the leaderboard count
3. Run: `curl -s http://localhost:8255/api/data | jq '.universe_count'`
4. Record the universe count
5. Verify neither count has increased vs. the prior baseline (J-01/J-12 regression check)
6. Run: `curl -s http://localhost:8255/api/stocks | jq '.leaderboard[] | select(.symbol | test("^SPX|^NDX|^DJI"))'`
7. Confirm no deep index appears in the leaderboard (should return empty)

**Expected outcome:**  
Leaderboard and universe counts unchanged; deep indices absent from scored universe.

**Pass criteria:**  
- Leaderboard count matches J-01 baseline (no leaked index rows).
- Universe count matches J-12 baseline.
- No symbol matching `^SPX`, `^NDX`, `^DJI` appears in the leaderboard (empty result).

---

### TC-06 — compute_index_series emits correct vendor mapping + first dates

**Type:** api  
**Preconditions:**
- Backend test environment (`apps/backend/.venv`)
- Database with deep series loaded

**Steps:**
1. Run unit test: `cd apps/backend && .venv/bin/python -m pytest tests/test_indexes.py::test_compute_index_series_vendors -xvs`
2. Verify test assertions:
   - Deep series (`^SPX`, `^NDX`, `^DJI`) are included
   - Each series carries the correct `vendor` from `meta.json` (Stooq, Yahoo, FRED-macro-proxy)
   - `first` field matches `meta.json` real first bar (e.g. `^SPX` → `1996-01-02`)
   - Existing ETF lines (SPY/QQQ) have `vendor: null` (no fabricated vendor)

**Expected outcome:**  
All vendor and first-date assertions pass.

**Pass criteria:**  
- Test exit code 0.
- No assertion failures on vendor mapping or first-date byte-match.

---

### TC-07 — Existing SPY/QQQ/IWM/RSP/DIA points frozen-golden across refactor

**Type:** api  
**Preconditions:**
- Backend tests passing
- Golden record of existing lines' `points` arrays captured

**Steps:**
1. Run unit test: `cd apps/backend && .venv/bin/python -m pytest tests/test_indexes.py::test_existing_series_byte_identical -xvs`
2. Verify the test compares pre-refactor vs. post-refactor normalized-% values for each existing series
3. Confirm zero numeric drift (match to 10 decimal places)

**Expected outcome:**  
Existing lines are unchanged; only additive fields and new series entries are present.

**Pass criteria:**  
- Test exit code 0.
- All existing series pass byte-identity check.

---

### TC-08 — Symbol with no meta vendor record renders no vendor label

**Type:** api  
**Preconditions:**
- Backend with compute_index_series changes deployed
- Series without meta vendor (ETFs: SPY, QQQ, IWM, RSP, DIA)

**Steps:**
1. Run: `curl -s http://localhost:8255/api/indexes | jq '.series[] | select(.symbol | test("^SPY|^QQQ|^IWM")) | {symbol, vendor}'`
2. Verify `vendor: null` (key absent or null value) for each ETF

**Expected outcome:**  
ETF lines carry `vendor: null`, never a fabricated vendor string.

**Pass criteria:**  
- Vendor field is absent or null for all non-deep series.
- Frontend renders no vendor label for null vendor (tested in TC-02).

---

### TC-09 — load_seed_windows vendor extension does not break existing test

**Type:** api  
**Preconditions:**
- Backend tests
- `load_seed_windows` extended to return vendor

**Steps:**
1. Run test: `cd apps/backend && .venv/bin/python -m pytest tests/test_data_manager.py::test_load_seed_windows_and_is_seed_bar -xvs`
2. Verify test passes with the new `vendor` field in the return shape
3. Confirm existing return values (first, last, bars) are still present and byte-identical

**Expected outcome:**  
Test passes; new vendor field is present; existing fields unchanged.

**Pass criteria:**  
- Test exit code 0.
- No regression in existing callers of `load_seed_windows`.

---

### TC-10 — Dashboard chart: vendor labels absent for null-vendor series

**Type:** browser  
**Preconditions:**
- Dashboard chart rendered with all configured series
- Frontend consuming `vendor: null` from API

**Steps:**
1. Navigate to Dashboard
2. Locate the chart legend
3. Inspect entries for SPY, QQQ, IWM (ETF lines with `vendor: null`)
4. Take a screenshot of legend
5. Verify no vendor label badge appears for these lines

**Expected outcome:**  
ETF lines (SPY, QQQ, IWM) show no vendor label in the legend.

**Pass criteria:**  
- Legend entries for ETFs render the symbol only, no vendor badge.
- Vendor badges appear ONLY for deep/macro series with non-null vendor.

---

### TC-11 — FRED-macro-proxy series display honestly (not as market index)

**Type:** browser  
**Preconditions:**
- `/data` vendor-disclosure panel rendered
- FRED-macro-proxy series in config and loaded

**Steps:**
1. Navigate to `/data`
2. Scroll to vendor-disclosure panel
3. Locate FRED-macro-proxy entries (e.g., `^TNX`, `^DXY`, `^VXN`)
4. Take screenshot
5. Verify display reads exactly "FRED-macro proxy" or qualified name (e.g., "10Y-2Y spread proxy (^TNX)")

**Expected outcome:**  
FRED-macro series are labeled with vendor "FRED-macro proxy" and display name does not imply real market ticker.

**Pass criteria:**  
- Vendor label is "FRED-macro proxy".
- Display name is qualified (e.g., "proxy", "spread", not bare "^TNX").

---

### TC-12 — No index symbol leaks into /stocks or universe count

**Type:** browser  
**Preconditions:**
- J-01 baseline (baseline leaderboard and universe count)
- Fresh DB with deep series loaded

**Steps:**
1. Navigate to `/stocks` leaderboard (`http://localhost:3255/stocks`)
2. Scroll and inspect rows; take screenshot
3. Verify no row has symbol matching `^SPX`, `^NDX`, `^DJI`, `^VIX`
4. Check the universe count badge on the page (if visible)
5. Compare to J-01 baseline screenshot/count

**Expected outcome:**  
Leaderboard contains no deep index rows; universe count unchanged.

**Pass criteria:**  
- Visual inspection and count verify no index/macro symbols in leaderboard.
- Universe count matches J-01 baseline.

---

### TC-13 — Regression replay: J-01 /stocks leaderboard remains clean

**Type:** browser  
**Preconditions:**
- Backend and frontend running live
- Deep series configured and loaded

**Steps:**
1. Navigate to `/stocks` leaderboard
2. Take full-page screenshot
3. Compare visually and by count to J-01 golden screenshot
4. Verify no index row; no crash

**Expected outcome:**  
Leaderboard passes J-01 regression: clean rows, correct count, no index symbols.

**Pass criteria:**  
- Screenshot shows expected stock rows.
- No index/macro symbols visible.
- Page is responsive; no error boundary.

---

### TC-14 — Regression replay: J-04 Dashboard regime label + evidence affordance intact

**Type:** browser  
**Preconditions:**
- Dashboard rendered with deep benchmark lines added
- J-04 golden screenshot/behavior available

**Steps:**
1. Navigate to Dashboard
2. Locate the regime label and evidence affordance (badge/link)
3. Verify they are still present and functional after chart gains lines
4. Take screenshot
5. Compare to J-04 golden

**Expected outcome:**  
Regime label and evidence affordance work; chart gains lines do not break existing controls.

**Pass criteria:**  
- Regime label renders.
- Evidence affordance is clickable/present.
- Chart interaction (range selection, hover) functions.

---

### TC-15 — Regression replay: J-12 /data universe count == /stocks count, unchanged

**Type:** browser  
**Preconditions:**
- `/data` and `/stocks` both loaded
- J-12 baseline count known

**Steps:**
1. Navigate to `/data`
2. Locate the universe count (in a panel or badge)
3. Record the count
4. Navigate to `/stocks`
5. Record the leaderboard count
6. Compare to J-12 baseline

**Expected outcome:**  
Counts match; no increase from adding deep series.

**Pass criteria:**  
- `/data` universe count == `/stocks` leaderboard count.
- Both match J-12 baseline (or documented prior baseline).

---

### TC-16 — Type check: IndexSeries type has additive vendor + first fields

**Type:** artifact  
**Preconditions:**
- Frontend source code (`apps/frontend/lib/api.ts`)
- TypeScript compilation

**Steps:**
1. Open `apps/frontend/lib/api.ts`
2. Locate the `IndexSeries` type definition (around line 459)
3. Verify it includes `vendor?: string | null` and `first?: string`
4. Run TypeScript check: `cd apps/frontend && npx tsc --noEmit`
5. Verify no errors in index/indexes-related type usage

**Expected outcome:**  
Type definition is present; TypeScript compilation passes.

**Pass criteria:**  
- `IndexSeries` type has `vendor` (optional, string or null) and `first` (optional, string).
- `tsc --noEmit` exit code 0.

---

## Summary

**Total test cases:** 16  
**Browser tests:** 9 (TC-01, TC-02, TC-03, TC-10, TC-12, TC-13, TC-14, TC-15, TC-16 partial)  
**API tests:** 5 (TC-04, TC-05, TC-06, TC-07, TC-08)  
**Unit/integration tests:** 3 (TC-06, TC-07, TC-09)  
**Artifact checks:** 1 (TC-16)

All tests must pass for the iteration to pass QA. Deep series must be loaded into `daily_prices` before browser tests run.
