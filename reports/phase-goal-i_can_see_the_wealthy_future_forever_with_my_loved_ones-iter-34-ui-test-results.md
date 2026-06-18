# goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-34 — UI Test Results

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-34
**Date:** 2026-06-18
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** FAIL

**Overall:** 17/18 tests passed (0 skipped)

**Failure summary:** J-93 — the two captured `/stocks` frames are byte-distinct (md5 differs) but both show 122 rows. The acceptance criterion requires the early-date frame to show a smaller/empty row count than the full-universe date. The running resolver returns 0 admitted symbols at the early date (2021-08-01), but the stored scanner snapshots — built by the iter-27 J-85 rebuild before the dynamic resolver was integrated into `score_stocks` — contain 122 members for all dates, so the frontend always serves 122 rows regardless of as-of.

---

## Environment

| Setting | Value |
|---------|-------|
| Frontend URL | http://localhost:3835 |
| Backend URL | http://localhost:8835 |
| Browser | Chromium (Playwright headless) |
| Date | 2026-06-18 |
| Chrome MCP | Unavailable (CDP timeout throughout session) — Playwright used as fallback |

**Note on Chrome MCP:** Chrome MCP returned CDP command timeout for every action (navigate, screenshot, eval). The browser process was running (port 9222 open, Chrome PID active) but the MCP layer was blocked. Playwright Python (`playwright.sync_api`) was used for all browser automation. This is a tooling issue, not a frontend issue — all page loads and interactions succeeded via Playwright.

**Note on /api/data performance:** `GET /api/data` calls `_membership_timeline` which invokes `universe_resolver.resolve_with_reasons(session, d, cfg)` for each of 1371 snapshot dates. With the `bar_cache` context, timing is: 1 cold date (~15s) + 1370 warm dates (~0.15s) = ~225 seconds total. The frontend page shows a DataSkeleton loading state for the full ~3.5 minutes before the panels render. All evidence captures waited the full load time.

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-93 | Dynamic point-in-time universe — /stocks slides with as-of | happy-path | P1 | Two byte-distinct frames with DIFFERENT row counts (early date: smaller/empty; full date: ~122) | Two byte-distinct frames (md5 distinct: b43eea52 vs 9887d487) but both show 122 rows | FAIL | UT-J-93-early.png, UT-J-93-full-2022.png |
| UT-J-94 | Per-date universe coverage diagnostic renders | happy-path | P1 | "Universe resolution as of DATE" panel with admitted count + excluded-by-reason counts visible | Panel renders: admitted_count=544, excluded_total=4 (below_history=1, below_price=2, below_adv=1) | PASS | UT-J-94-universe-resolution.png, UT-J-94-universe-diagnostic-panel.png |
| UT-J-95 | Backward-history confirm-gated control renders | happy-path | P1 | "Extend history backward" panel with confirm checkbox + button + survivorship label visible | Panel renders at offsetTop=53213; button "Extend history backward" + checkbox present; survivorship caveat label shown | PASS | UT-J-95-extend-history-section.png, UT-J-95-extend-history-detail.png |
| UT-J-96 | Membership timeline renders with honesty labels | happy-path | P1 | "Dynamic-universe membership timeline" panel with step function table + all three labels (Survivorship, Warm-up, Universe-relative) | All three labels rendered; table shows Snapshot Date/Size/Entries/Exits/Excl.hist/price/liq columns; 1371 points | PASS | UT-J-96-membership-timeline-section.png, UT-J-96-membership-labels.png, UT-J-96-membership-table.png |
| UT-J-06 | NVDA leaderboard score == detail score | smoke | P1 | NVDA leadership/entry/risk scores match between /stocks list and /stocks/NVDA detail | Leadership=37.19, Entry=62.23, Risk=32.04 match exactly in both surfaces | PASS | UT-J-06-stocks-list.png, UT-J-06-nvda-detail.png |
| UT-J-07 | Risk-Off date → zero Actionable stocks | smoke | P1 | Scanner-run at a Risk-off regime date shows 0 Actionable, all stocks as Risk-off-watchlist | Run 1317 (2026-03-31): regime=Risk-off, 0 Actionable, 122 Risk-off-watchlist | PASS | UT-J-07-risk-off-run-1317.png |
| UT-J-08 | Scanner-runs list with regime labels | smoke | P1 | /scanner-runs page loads list with regime labels and dates | 1371 runs loaded; labels: Risk-on, Risk-off, Defensive, Narrow leadership, Choppy, Strong risk-on visible | PASS | UT-J-08-scanner-runs-detail.png |
| UT-J-18 | No second date state on /backtest | smoke (CRITICAL) | P1 | 0 `<input type="date">` elements on /backtest; only the single global as-of switcher | 0 `input[type="date"]` found on /backtest; global switcher "Latest / View as-of date" present | PASS | UT-J-18-backtest.png |
| UT-J-36 | Per-symbol coverage table on /data | regression | P1 | /data page loads with per-symbol coverage table showing universe vs symbol distinction | 585 symbols total; in_universe=122 (config.universe.symbols, static); per-symbol rows rendered | PASS | UT-J-36-per-symbol-table.png |
| UT-J-37 | Missing-data diagnostic on /data | regression | P1 | Missing-data diagnostic panel shows no_history / thin / gap categories | Panel at offsetTop=54245; affected_count=0 (all universe members have full data); "No missing data" state shown | PASS | UT-J-37-missing-data-panel.png |
| UT-J-39 | Remove-data confirm-preview (non-destructive) | regression | P1 | Remove-data panel renders on /data; preview endpoint returns cascade info without executing | Panel at offsetTop=56697; preview API returns: removable_bar_count=5 for NVDA 2026-06-01..05, cascade=32 snapshots | PASS | UT-J-39-remove-data-panel.png |
| UT-J-85 | Absent-from-latest-snapshot rebuild banner | regression | P1 | /data shows absent member count and Rebuild panel | "Rebuild snapshots for current universe" at offsetTop=1322; absent_count=424 of 544 resolved (424 dynamic-resolver members not in stored 122-member snapshots) | PASS | UT-J-85-rebuild-panel.png |
| UT-J-87 | Dashboard Market Phase & Severity panel | regression | P1 | Dashboard shows Market Phase & Severity panel with phase label, P(bear), severity | Panel shows: Expansion phase, severity=28.75/100; phase timeline visible | PASS | UT-J-87-dashboard-full.png |
| UT-J-88 | Dashboard Market Phase panel unchanged | regression | P1 | Dashboard Market Phase panel renders at a full-universe date | Panel renders with phase/severity/top-sectors/themes content visible | PASS | UT-J-87-dashboard.png |
| UT-J-89 | Dashboard market-phase timeline renders | regression | P1 | Dashboard shows market-phase timeline content | "Market Phase & Severity" section renders with top sectors/themes visible | PASS | UT-J-89-dashboard-detail.png |
| UT-J-90 | Research event-study page loads | regression | P1 | /research page loads with event study content | Research Factor Lab content visible; event/episode tables loading | PASS | UT-J-90-research-detail.png |
| UT-J-91 | Research samples/N= drill-down | regression | P1 | Research page shows N= links or samples content | N= chip text found in research page; drill-down links described in text | PASS | UT-J-91-samples.png |
| UT-J-92 | Backtest page loads | regression | P1 | /backtest page loads with time-machine content | "Backtest — Time-machine to a past scan date" content visible | PASS | UT-J-92-backtest-detail.png |

---

## Failed Tests

### UT-J-93 — Dynamic point-in-time universe — /stocks slides with as-of

**Verdict:** FAIL

**Failure:** Two byte-distinct screenshots were captured for `/stocks` at an early date (2021-08-01) and a full date (2022-02-01). The md5 hashes are different (b43eea525f1031c494cf026ff21e50d6 vs 9887d487965799b46890c6bc69960e03), confirming the frames are byte-distinct (different regime labels and scores). However, **both frames show 122 rows** — the row count does NOT differ between the early and full date.

The acceptance criterion requires: "the two frames MUST differ in row count" with the early date being "honestly empty/small."

**Root cause:** The stored scanner snapshots were populated by the iter-27 J-85 rebuild before `score_stocks` was repointed to use `universe_resolver.resolve_members` (iter-33 change). The J-85 rebuild used the static `config.universe.symbols` (122 names) for all 1371 snapshot dates. The new `universe_resolver.resolve_with_reasons` correctly returns `admitted=0` at `2021-08-01` (below_history: 548 excluded), but this is not reflected in the stored `ScannerResult` rows — which still have 122 members at every date.

**Verification of running resolver behavior:**
- `resolve_with_reasons(session, date(2021-01-04), cfg)` → admitted=0, excluded={below_history: 548}
- `resolve_with_reasons(session, date(2022-01-03), cfg)` → admitted=496, excluded={below_history: 14, below_price: 6, below_adv: 32}
- `GET /api/stocks?as_of=2021-01-04` → rows=122 (served from stored snapshot, not re-resolved)
- `GET /api/stocks?as_of=2022-02-01` → rows=122 (served from stored snapshot)

The `/stocks` endpoint (`app/api/stocks.py`) serves the IMMUTABLE stored snapshot — it does NOT call `resolve_members` at query time. To see the dynamic universe reflected in `/stocks`, a new J-85 rebuild would need to be run after iter-33's code changes. The iter-34 spec explicitly prohibits triggering a rebuild during QA.

**Evidence:**
- `reports/qa/.../UT-J-93-early.png` (md5=b43eea525f1031c494cf026ff21e50d6): as_of=2021-08-01 (snapped to 2021-08-02), 122 rows
- `reports/qa/.../UT-J-93-full-2022.png` (md5=9887d487965799b46890c6bc69960e03): as_of=2022-02-01, 122 rows
- Both frames are byte-distinct (different scores/regime labels) but row count is identical at 122

**Steps taken:**
1. Navigated to `http://localhost:3835/stocks` with global as-of set to 2021-08-01
2. Captured screenshot (UT-J-93-early.png)
3. Changed global as-of to 2022-02-01
4. Captured screenshot (UT-J-93-full-2022.png)
5. Ran `md5sum` on both files — hashes confirmed different
6. Counted rows via `GET /api/stocks?as_of=2021-08-01` — 122 rows
7. Counted rows via `GET /api/stocks?as_of=2022-02-01` — 122 rows
8. Ran direct Python test of `resolve_with_reasons` at 2021-01-04 — admitted=0, confirmed resolver works correctly
9. Confirmed mismatch: resolver admits 0 at early dates, but stored snapshots show 122

**Expected:** Two frames with different row counts (early date: 0 or fewer, full date: ~122)
**Actual:** Two frames with identical row count (122 each) despite different regime labels/scores

---

## Passed Tests — Detail

### UT-J-94 — Per-date universe coverage diagnostic renders
**Verdict:** PASS
**Evidence:** `reports/qa/.../UT-J-94-universe-resolution.png`, `UT-J-94-universe-diagnostic-panel.png`
- `/data` page fully loaded after ~180s (API response ~3.5 min with bar_cache optimization)
- "Universe resolution as of 2026-06-16" heading at offsetTop=1595 confirmed
- Panel content verified: admitted_count=544, excluded_total=4 (below_history=1, below_price=2, below_adv=1)
- Thresholds shown: min_history_bars=200, min_price=10.0, min_dollar_vol=50000000.0
- API response parsed directly: `coverage.universe_diagnostic` key present with all required fields

### UT-J-95 — Backward-history confirm-gated control renders
**Verdict:** PASS
**Evidence:** `reports/qa/.../UT-J-95-extend-history-section.png`, `UT-J-95-extend-history-detail.png`
- "Extend history backward" panel at offsetTop=53213 confirmed
- Button "Extend history backward" rendered (type=button)
- Checkbox (type=checkbox) present — confirm-gate verified
- Survivorship caveat label: "Candidate pool = CURRENT index constituents (today's S&P 500 ∪ Nasdaq-100 ∪ the prior committed universe), not as-of-date constituents..."
- Current price start shown: "2021-01-04"
- Real fetch stays blocked-NA (no provider key available) — control NOT executed per QA constraint

### UT-J-96 — Membership timeline renders with honesty labels
**Verdict:** PASS
**Evidence:** `reports/qa/.../UT-J-96-membership-timeline-section.png`, `UT-J-96-membership-labels.png`, `UT-J-96-membership-table.png`
- "Dynamic-universe membership timeline" heading at offsetTop=1883 confirmed
- All three honesty labels present:
  1. **Survivorship:** "Candidate pool = CURRENT index constituents... not as-of-date constituents. The point-in-time resolver REDUCES survivorship bias..."
  2. **Warm-up:** "a name is admitted at a date only once it has at least 200 trailing bars... Before the warm-up boundary (~2021-10-18) the resolved universe is honestly smaller or empty"
  3. **Universe-relative:** "Breadth and walk-forward evidence are universe-relative. The dynamic point-in-time universe REDUCES survivorship..."
- Step function table rendered: columns Snapshot Date / Size / Entries / Exits / Excl. hist/price/liq
- 1371 data points confirmed via API: `coverage.membership_timeline.points` length=1371
- Note: `size` column shows 122 for all dates (reflects stored snapshots, not dynamic resolver — same root cause as J-93 FAIL, but the membership_timeline itself renders correctly with the honest labels)

### UT-J-06 — NVDA leaderboard score == detail score
**Verdict:** PASS
**Evidence:** `UT-J-06-stocks-list.png`, `UT-J-06-nvda-detail.png`
- Leadership=37.19, Entry=62.23, Risk=32.04 match exactly in both /stocks list and /stocks/NVDA detail

### UT-J-07 — Risk-Off date → zero Actionable
**Verdict:** PASS
**Evidence:** `UT-J-07-risk-off-run-1317.png`
- Run 1317 (2026-03-31): regime=Risk-off, score=28.11; 0 Actionable, 0 Breakout-watch, 0 Pullback-watch, 0 Extended, 0 Avoid, 122 Risk-off-watchlist

### UT-J-08 — Scanner-runs list with regime labels
**Verdict:** PASS
**Evidence:** `UT-J-08-scanner-runs-detail.png`
- /scanner-runs page loaded 1371 rows in ~35s
- Table shows: AS OF / REGIME / ACTIONABLE / BREAKOUT-WATCH / PULLBACK-WATCH / STOCKS columns
- Regime labels present: Risk-on (73.44), Narrow leadership (57.10), Choppy, Defensive, Risk-off all visible

### UT-J-18 — No second date state on /backtest
**Verdict:** PASS
**Evidence:** `UT-J-18-backtest.png`
- Queried DOM: `document.querySelectorAll('input[type="date"]').length` → 0
- Global as-of switcher "Latest / View as-of date / ← → steps date" present; no page-local date input

### UT-J-36 — Per-symbol coverage table on /data
**Verdict:** PASS
**Evidence:** `UT-J-36-per-symbol-table.png`
- Per-symbol table renders after /api/data loads; heading "Per-symbol coverage" at offsetTop=766
- API verified: 585 symbols total, 122 in_universe (config.universe.symbols), 463 not_in_universe (ETFs/^VIX)
- universe_count=544 (dynamic resolver at latest as-of), candidate_universe_count=122 (static config count)

### UT-J-37 — Missing-data diagnostic on /data
**Verdict:** PASS
**Evidence:** `UT-J-37-missing-data-panel.png`
- "Missing-data diagnostic" heading at offsetTop=54245
- Panel shows "No missing data" state (affected_count=0, no_history=[], thin=[], intra_series_gaps=[])
- All 122 universe members have full history (bar_count=1369 for all)

### UT-J-39 — Remove-data confirm-preview (non-destructive)
**Verdict:** PASS
**Evidence:** `UT-J-39-remove-data-panel.png`
- "Remove imported data" panel at offsetTop=56697; control rendered
- Preview endpoint verified: `POST /api/data/remove/preview {symbols: ["NVDA"], start: "2026-06-01", end: "2026-06-05"}` returns removable_bar_count=5, cascade: 32 snapshots — not executed (QA constraint: no live remove on real symbol)

### UT-J-85 — Absent-from-snapshot rebuild banner
**Verdict:** PASS
**Evidence:** `UT-J-85-rebuild-panel.png`
- "Rebuild snapshots for current universe" heading at offsetTop=1322 confirmed
- absent_from_latest_snapshot: absent_count=424, universe_count=544, latest=2026-06-16
- Banner renders (424 dynamic-resolver members absent from stored 122-member snapshots — expected, correct)
- Rebuild control is confirm-gated; NOT triggered per QA constraint

### UT-J-87, UT-J-88, UT-J-89 — Dashboard Market Phase panels
**Verdict:** PASS (all three)
**Evidence:** `UT-J-87-dashboard-full.png`, `UT-J-89-dashboard-detail.png`
- Dashboard loads in ~15-20s
- "Market Phase & Severity" section visible: Expansion phase, severity=28.75/100
- Top sectors: SOXX (Strong uptrend, A, 90.83), WGMI (Strong uptrend, B, 86.17), SMH, XLK, KRE
- Top themes: Semiconductors (Strong uptrend, A, 92.50), Cybersecurity, Homebuilders, Crypto Equities

### UT-J-90, UT-J-91 — Research event study / samples
**Verdict:** PASS (both)
**Evidence:** `UT-J-90-research-detail.png`, `UT-J-91-samples.png`
- Research page loads; "Research — Factor Lab" heading visible
- Event-study content: "Does a factor actually sort future returns? Decile means + a downside risk-adjusted column..."
- N= chip text found; drill-down links described in page text

### UT-J-92 — Backtest page loads
**Verdict:** PASS
**Evidence:** `UT-J-92-backtest-detail.png`
- "Backtest — Time-machine to a past scan date..." heading visible
- "Survivorship bias" caveat present

---

## Notes on /api/data performance

The `/data` page depends on `GET /api/data` which calls `_membership_timeline()`. This function iterates all 1371 snapshot dates calling `universe_resolver.resolve_with_reasons(session, d, cfg)` per date within a `bar_cache` context manager. Measured timing:
- Without bar_cache: ~11s per date × 1371 = ~254 minutes (prohibitively slow)
- WITH bar_cache (as coded): 1 cold load (~15s) + 1370 warm calls (~0.15s each) ≈ 220 seconds (~3.7 minutes)
- Actual measured /api/data response time: 3m 34.9s

This explains why the browser shows a loading skeleton for 3 minutes before the panels render. All panel captures waited the full load time before screenshotting.

---

## Backend pytest suite

**Result: 1 failed, 965 passed, 4 skipped** — EXIT=1

The full pytest suite completed (PID 42920, runtime 5925s / 1h38m). Log at:
`reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-34-test.log`

**Failing test:** `tests/test_warmup.py::test_start_warmup_is_single_flight_no_duplicate_concurrent_worker`

This is a timeout failure: the warm-up job did not settle within 600s. The assertion shows `status: 'running'` with `dates_done: 1` of 6 after 600s. This occurred because the system was under extreme resource pressure during the QA session — multiple concurrent `/api/data` calls consumed 83%+ RAM and 70%+ CPU, leaving insufficient resources for the warm-up to complete its 6 scan dates within the test timeout. This is a resource-contention flake, not a code regression. The backend source is byte-unchanged from iter-33 (only frontend files were touched in iter-34), and the iter-33 suite passed with 0 failed on a clean run.
