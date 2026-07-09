# goal-mcp-loop-iter-23 Functional Test Plan

**Phase:** goal-mcp-loop-iter-23
**Date:** 2026-07-08
**Frontend Present:** yes

## Phase Goal

Verify the already-built J-14 deep, vendor-labeled index/macro context (deep `^SPX`/`^NDX`/`^DJI`/`^VIX`/`^TNX` overlays + per-series vendor labels) through the canonical browser-qa-agent lane; confirm required-still-passing journeys (J-01, J-03, J-04, J-05, J-10, J-11, J-12, J-13) remain green; re-run ux-regression-reviewer and phase-closure gates to clear the iter-22 CLOSURE-FAIL. **Zero new feature code in scope.**

## Test Cases

### TC-01 — J-14 Deep-window default view (deep `^SPX` visible before SPY 2005 start)

**Type:** browser
**Preconditions:** Backend running (:8255), frontend running (:3255), `rm -rf apps/frontend/.next` applied, Dashboard accessible, deep index data present in seed

**Steps:**
1. Navigate to Dashboard `/`
2. Locate the "Regime × phase cross-view" chart card
3. Verify chart renders without zoom/pan (default view)
4. Inspect for a deep equity-index line (e.g., `^SPX` labeled in legend) that extends well before 2005
5. Hover/inspect the x-axis to confirm the leftmost visible date is circa 1996–2000, NOT circa 2018

**Expected outcome:** A deep index line is rendered in-frame, starting near 1996-01-02, well before SPY's 2005 first bar. The default chart view shows the deep historical window without requiring manual zoom/pan.

**Pass criteria:** The chart's leftmost visible date is ≤1997-12-31 (confirming deep history renders in default view); a legend entry or tooltip confirms the presence of a deep index (e.g., `^SPX`); md5-distinct screenshot shows the deep line visibly in-frame, not clipped or off-screen.

---

### TC-02 — J-14 Vendor labels on Dashboard legend & tooltip

**Type:** browser
**Preconditions:** Dashboard chart rendered; legend/tooltip available on hover

**Steps:**
1. Locate the chart legend (10-slot line palette for `^SPX`, `^NDX`, `^DJI`, `^VIX`, and 5 pre-existing ETFs)
2. Hover over or inspect each index-series legend entry
3. Verify vendor attribution is shown (Stooq, Yahoo, or FRED-macro proxy label)
4. Confirm the tooltip contains vendor information for at least the three main index overlays

**Expected outcome:** Legend/tooltip displays vendor attribution (Stooq/Yahoo/FRED-macro proxy) for each index series.

**Pass criteria:** Vendor label is present and accurate for at least `^SPX` (Stooq), `^VIX` (Yahoo), and one macro proxy; no fabricated vendor claimed; ETF rows carry no vendor label.

---

### TC-03 — J-14 `/data` vendor-disclosure panel byte-matches `meta.json`

**Type:** browser
**Preconditions:** `/data` page loads; index vendor disclosure panel visible; `data/seed/meta.json` available for verification

**Steps:**
1. Navigate to `/data`
2. Locate the index/vendor-disclosure panel
3. Inspect listed series: `^SPX`, `^NDX`, `^DJI`, `^VIX`, `^TNX`, `^DXY`, `^VXN`
4. For each, verify the displayed first-bar date and vendor label
5. Confirm `^SPX` shows 1996-01-02 / Stooq; `^VIX` shows Yahoo; `^TNX`/`^DXY`/`^VXN` show "FRED-macro proxy"
6. Verify ETF series (e.g., SPY, QQQ) carry no vendor label

**Expected outcome:** Panel displays per-series vendor labels and first-bar dates that byte-match the `meta.json` configuration.

**Pass criteria:** Vendor labels and first-bar dates are byte-identical to `meta.json`; `^TNX`/`^DXY`/`^VXN` are labeled as "FRED-macro proxy" (never as market indices); ETF rows have no vendor label.

---

### TC-04 — J-13 Dedicated availability-heatmap replay (548-pool coverage, two-group legend)

**Type:** browser
**Preconditions:** `/data` page loads; availability heatmap renders; backend serving `GET /api/data/availability`

**Steps:**
1. Navigate to `/data`
2. Locate the per-date availability heatmap
3. Inspect the legend; verify it clearly separates two groups: "Price data — cell fill" and "Scored snapshot — indicator"
4. Verify cell fill uses a monotonic single-hue density ramp (no amber in top bucket)
5. Verify snapshot indicator uses a distinct non-green treatment (e.g., violet ring)
6. Hover over two dates: one with bars but no snapshot (backfill gap), one with both
7. Verify tooltips distinguish the two states plainly
8. Inspect the legend caption for Fetch→fills / Backfill→scores workflow explanation

**Expected outcome:** Heatmap legend unambiguously separates data-fill and snapshot-indicator; density ramp is monotonic; snapshot ring is visually distinct; tooltips clarify the workflow.

**Pass criteria:** Legend renders two labeled groups; density fill uses no amber in the top bucket; snapshot indicator is not green; md5-distinct screenshot shows at least two hover-tooltip states (one with bars-only, one with snapshot); legend caption mentions Fetch and Backfill workflows; pool coverage reflects 590 total symbols (verified via backend live-query or test-plan setup).

---

### TC-05 — J-01 Live replay: `/stocks` leaderboard (541 stocks, zero leaked index carets)

**Type:** browser
**Preconditions:** Backend running; `/stocks` leaderboard loads; evidence badges present on score columns

**Steps:**
1. Navigate to `/stocks`
2. Verify leaderboard loads 541 equity rows (no index carets like `^SPX`)
3. Scan for any row starting with a caret (`^`); verify none are present
4. Inspect score columns (Leadership, Entry Quality, Risk); verify each row's score area displays an evidence badge
5. Verify badges read either "Proven" or "Not yet proven"

**Expected outcome:** Leaderboard shows exactly 541 equity rows; zero index-caret rows leaked; every score has a visible evidence badge.

**Pass criteria:** Row count is 541; zero rows with caret prefix; 100% of visible scores have an evidence badge; md5-distinct screenshot.

---

### TC-06 — J-03 Live replay: All scores read "Not yet proven"

**Type:** browser
**Preconditions:** J-01 leaderboard loaded; evidence badges visible; certified-claims ledger is all-FAIL

**Steps:**
1. Inspect the leaderboard badges from J-01
2. Scan for any badge reading "Proven"
3. Verify all badges read "Not yet proven"
4. Spot-check 3–5 random rows for consistency

**Expected outcome:** All evidence badges on the leaderboard display "Not yet proven"; no confident-number styling applied.

**Pass criteria:** 100% of inspected score badges read "Not yet proven"; zero "Proven" badges visible; md5-distinct screenshot.

---

### TC-07 — J-04 Live replay: Dashboard regime card + evidence link

**Type:** browser
**Preconditions:** Dashboard `/` loads; regime card renders; evidence link intact

**Steps:**
1. Navigate to Dashboard `/`
2. Locate the regime card (regime/phase + current label)
3. Verify the card displays the current market regime/phase
4. Verify an "Evidence" link or navigation path is present and clickable
5. Click the link; verify it navigates to `/evidence`

**Expected outcome:** Dashboard regime card shows current regime; evidence link is present and functional.

**Pass criteria:** Regime label matches backend computation; evidence link navigates to `/evidence` (HTTP 200); md5-distinct screenshot.

---

### TC-08 — J-05 Live replay: `/evidence` ledger renders all-FAIL rows

**Type:** browser
**Preconditions:** `/evidence` page loads; ledger displays rows; certified-claims.jsonl all-FAIL

**Steps:**
1. Navigate to `/evidence`
2. Verify the ledger displays rows with columns: hypothesis, out-of-sample verdict, control comparison, registration date, forward-walk score-to-date, and linkback
3. Inspect all visible rows; verify every row shows a FAIL verdict or "Not yet proven" status
4. Verify each row's linkback (e.g., "Backs: Research factor lab →") is clickable and navigates correctly
5. Count total rows; verify count matches certified-claims.jsonl entry count (expected: 7 all-FAIL rows from iter-22)

**Expected outcome:** Ledger displays all 7 canonical certified-claims rows; all show FAIL verdicts; linkbacks are functional.

**Pass criteria:** Row count is 7; every row displays a FAIL verdict; every linkback is clickable and navigates to the correct research surface (factor lab, combination lab, etc.); md5-distinct screenshot.

---

### TC-09 — J-10 Live replay: Full ↔ Recent history toggle (no crash)

**Type:** browser
**Preconditions:** `/stocks/{ticker}` page loads for a long-tenured name (e.g., AAPL); history toggle available

**Steps:**
1. Navigate to `/stocks/AAPL` (or another long-tenured name)
2. Locate the history toggle (e.g., "Full" / "Recent" buttons or dropdown)
3. Verify the chart initially shows a limited recent window (≤5 years)
4. Click "Full" to expand to deep history
5. Verify the chart re-renders to show ~30-year history
6. Verify no console errors or page crash occurs
7. Click "Recent" to toggle back; verify the chart re-renders to the recent window
8. Verify the first visible date in Full mode is ≤1997-12-31

**Expected outcome:** Toggle switch between recent and full history without crash; full history window displays deep 30-year span; no application errors logged.

**Pass criteria:** Full-history toggle is functional and renders without crash; full-history view shows first date ≤1997-12-31; recent-history toggle re-renders to ≤5-year window; md5-distinct screenshot of both states.

---

### TC-10 — J-11 Live replay: No stale edge resurfaces; ledgers all-FAIL

**Type:** browser
**Preconditions:** `/evidence` and research factor-lab pages load; certified-claims and staging-ledger both all-FAIL

**Steps:**
1. Navigate to `/evidence`
2. Inspect all ledger rows; verify none display a "Proven" edge from iter-21 (old values like +21.34%, +6.36%, p=0.0004998)
3. Navigate to a research factor lab (e.g., `/research/factor-lab` for `vcp_contraction`)
4. Inspect cohort badges; verify all read "Not yet proven" (no old certified edges carry forward)
5. Verify the frozen-golden test expectations (`test_evidence.py`, `test_staging_ledger_routing.py`) match the current ledger

**Expected outcome:** Zero pre-refresh edge values displayed; all badges read "Not yet proven"; ledgers byte-match regenerated state.

**Pass criteria:** No visible "Proven" badge displays an old pre-refresh value; all factor-lab cohort badges read "Not yet proven"; ledger row count matches current regenerated state; md5-distinct screenshot.

---

### TC-11 — J-12 Live replay: `/data` count == `/stocks` count

**Type:** browser
**Preconditions:** `/data` and `/stocks` pages load; both count their universes

**Steps:**
1. Navigate to `/stocks`
2. Count or inspect the total number of rows displayed (expected: 541 equities, zero indices)
3. Navigate to `/data`
4. Locate the universe/pool count display (e.g., "548 total symbols in pool" or similar)
5. Verify the count matches the `/stocks` universe count (541 equities) or the full pool (548)
6. Verify a name that IPO'd mid-history (e.g., ARM, COIN, HOOD) is present in `/stocks` only after its real listing date and absent before

**Expected outcome:** Universe counts across `/stocks` and `/data` are consistent; point-in-time entry/exit is respected.

**Pass criteria:** Equity count on `/stocks` matches the universe resolver's latest snapshot (541); pool count on `/data` reflects the full committed pool (548 or 590 per refresh); a post-IPO name is absent from early leaderboard snapshots and present from its real first bar; md5-distinct screenshot.

---

### TC-12 — Backend: `test_api_indexes.py` passes (audit T2)

**Type:** api
**Preconditions:** Backend running; pytest environment configured; `test_api_indexes.py` test file present

**Steps:**
1. Run: `python -m pytest apps/backend/tests/test_api_indexes.py -v`
2. Capture exit code and output
3. Verify all test cases pass (green checkmarks)
4. Verify no timeouts or OOM errors (the fixture loads the full 30y/590-symbol basis)

**Expected outcome:** All tests in `test_api_indexes.py` pass; exit code 0.

**Pass criteria:** Exit code is 0; 100% of test cases pass; no timeout or OOM; the `vendor` and `first` fields on `GET /api/indexes` are correctly populated and match `meta.json`.

---

### TC-13 — Backend: Evidence frozen-golden tests pass

**Type:** api
**Preconditions:** Backend running; `test_evidence.py` and `test_staging_ledger_routing.py` test files present; ledgers regenerated

**Steps:**
1. Run: `python -m pytest apps/backend/tests/test_evidence.py apps/backend/tests/test_staging_ledger_routing.py -v`
2. Capture exit code and output
3. Verify all test cases pass
4. Verify ledger snapshots match the current canonical and staging ledger states

**Expected outcome:** Frozen-golden tests pass with updated expectations reflecting the current all-FAIL ledger state.

**Pass criteria:** Exit code is 0; 100% of test cases pass; ledger row counts and content byte-match regenerated state; no pre-refresh edge values present.

---

### TC-14 — Backend: `test_bar_cache.py` green (regression)

**Type:** api
**Preconditions:** Backend running; `test_bar_cache.py` test file present

**Steps:**
1. Run: `python -m pytest apps/backend/tests/test_bar_cache.py -v`
2. Capture exit code and output
3. Verify all test cases pass (no changes to test expectations needed beyond optional offset-date comment)

**Expected outcome:** Bar cache tests pass; byte-identical snapshot assertions confirm the deep-history data is correctly cached.

**Pass criteria:** Exit code is 0; 100% of test cases pass; no assertion changes needed (or only optional comment updates); deep history cache loads consistently.

---

### TC-15 — Frontend: TypeScript compilation clean

**Type:** artifact
**Preconditions:** Frontend source tree present; TypeScript compiler available

**Steps:**
1. Run: `cd apps/frontend && npx tsc --noEmit`
2. Capture exit code and output
3. Verify no type errors or warnings

**Expected outcome:** TypeScript compilation passes with no errors (exit code 0).

**Pass criteria:** Exit code is 0; zero type errors reported; the no-source-change assumption is validated.

---

### TC-16 — Error handling: Backend-down state on `/data` (honest degradation)

**Type:** browser
**Preconditions:** Backend is down or unreachable; frontend running; `/data` page loads

**Steps:**
1. Stop the backend service (e.g., via `pkill -f "uvicorn.*:8255"`)
2. Reload the frontend at `/data`
3. Inspect the page for error state
4. Verify the error message is honest (e.g., "Backend unavailable") and not a blank white screen or application-error page
5. Verify the heatmap gracefully degrades with honest "—" or NA placeholders
6. Restart the backend and reload; verify recovery

**Expected outcome:** Backend-down state degrades gracefully with an honest error message; no blank error page; heatmap uses honest placeholders.

**Pass criteria:** Error message is human-readable and clearly states "Backend unavailable" or similar; no blank white screen or unhandled exception page; placeholders use "—" or "NA"; after backend restart, page recovers normally; md5-distinct screenshot of error state.

---

### TC-17 — Error handling: ETF with no `meta.json` vendor record renders no fabricated label

**Type:** browser
**Preconditions:** Dashboard chart renders; `/data` vendor panel visible; an ETF series with missing vendor record is present (or artificially simulated)

**Steps:**
1. Inspect the Dashboard chart legend for an ETF (e.g., SPY, QQQ)
2. Verify no vendor label is shown (honest omission, not fabricated)
3. Navigate to `/data` vendor panel
4. Inspect the same ETF row; verify it carries no vendor label
5. Verify an ETF with a mock/missing `meta.json` vendor field does not invent a label

**Expected outcome:** ETF rows display no vendor label (honest omission, not fabricated Stooq/Yahoo/FRED claim).

**Pass criteria:** Zero ETF rows show a fabricated vendor label; vendor-less rows are clearly unlabeled; md5-distinct screenshot.

---

### TC-18 — J-13 Golden replay: `journey-scripts/J-13.json` fixture count (587→590 permitted refresh)

**Type:** artifact
**Preconditions:** `runs/goal-session-mcp-loop/journey-scripts/J-13.json` file exists and is readable

**Steps:**
1. Read the `J-13.json` file
2. Inspect the step 1 expectation (the "expect" field in the first step)
3. Verify it contains `"text": "590 symbols"` (or the current denominator after iter-22's additive load of `^SPX`/`^NDX`/`^DJI`)
4. Confirm the fixture was refreshed from the iter-21 pin of 587 to the iter-22/23 expected value of 590

**Expected outcome:** `J-13.json` step 1 expects exactly 590 symbols (the current verified pool count after iter-22's deep-index additions).

**Pass criteria:** `J-13.json` step 1 `"expect"` field reads `"590 symbols"` (or current denominator); the fixture was intentionally updated per the phase spec's "Permitted test-fixture refresh" section; no other expectations in the file were altered.

---

## Summary

Total test cases: 18
- API tests: 4 (TC-12, TC-13, TC-14, TC-18)
- Browser tests: 13 (TC-01, TC-02, TC-03, TC-04, TC-05, TC-06, TC-07, TC-08, TC-09, TC-10, TC-11, TC-16, TC-17)
- Artifact checks: 1 (TC-15)

**Coverage:**
- **J-14 (target):** TC-01, TC-02, TC-03 (deep-window default view, vendor labels, `/data` disclosure panel)
- **J-13 (dedicated replay):** TC-04, TC-18 (availability heatmap, golden fixture)
- **Required-still-passing (J-01, J-03, J-04, J-05, J-10, J-11, J-12):** TC-05 through TC-11 (live replays)
- **Backend verification:** TC-12, TC-13, TC-14 (API indexes, evidence ledgers, bar cache)
- **Frontend & error handling:** TC-15, TC-16, TC-17 (TypeScript, backend-down degradation, vendor label honesty)
