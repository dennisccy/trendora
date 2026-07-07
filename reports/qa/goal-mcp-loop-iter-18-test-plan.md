# Goal Iteration 18 Functional Test Plan

**Phase:** goal-mcp-loop-iter-18
**Date:** 2026-07-06
**Frontend Present:** yes

## Phase Goal

Execute the atomic 30-year / 548-pool price basis swap with an honestly-regenerated evidence ledger (all FAIL verdicts, register date 2026-07-03) and a recency/staleness gate hardening the point-in-time universe. Three journeys: J-10 (deep price history), J-11 (regenerated evidence ledger), J-12 (broadened pool with staleness gate). Four required regressions: J-01, J-03, J-04, J-05 (contract sense on regenerated data, fresh pixels only).

## Test Cases

### TC-01 — Deep history rendering on AAPL/MSFT (J-10)

**Type:** browser
**Preconditions:** Backend running; `/stocks/AAPL` page loads

**Steps:**
1. Navigate to `/stocks/AAPL`
2. Observe chart header for range toggle ("Recent" / "Full history" segmented control)
3. In Recent mode, verify caption displays "N bars · as of DATE · history since 1996-01-02"
4. Verify chart renders a bounded ~5-year trailing window (not full history)
5. Click "Full history" toggle
6. Verify chart renders the deep span with visual downsampling indicator
7. Confirm "Weekly-sampled beyond [threshold]" disclosure appears in caption
8. Confirm first available date in caption reads **1996-01-02** (AAPL's real first bar)

**Expected outcome:** Chart toggle renders and switches between bounded recent and deep history; real data depth surfaces correctly with honest disclosure.

**Pass criteria:** Recent mode shows ~5y bars; Full mode renders deeper span with weekly-sample indicator; caption displays 1996-01-02 as first available date for AAPL.

---

### TC-02 — Post-IPO name honest short history (J-10)

**Type:** browser
**Preconditions:** Backend running; data includes ARM/COIN/HOOD

**Steps:**
1. Navigate to `/stocks/ARM` (IPO 2023-09-14)
2. Observe chart in Recent mode
3. Note caption displays first available date as **2023-09-14** or shortly thereafter
4. Click "Full history" toggle
5. Verify chart does NOT fabricate data before real IPO date
6. Confirm the span is short (≤1 year) and honest
7. Verify no pre-IPO bars render

**Expected outcome:** Post-IPO name shows only real history since its listing; deep history is still short but honest.

**Pass criteria:** First available date matches ARM's real IPO 2023-09-14; chart does not render pre-IPO invented bars.

---

### TC-03 — Backtest window deepening (J-10)

**Type:** browser
**Preconditions:** Backend running; `/backtest` page accessible

**Steps:**
1. Navigate to `/backtest`
2. Expand the as-of date range picker
3. Verify minimum date available is **2005-02-25** (SPY's real first committed bar)
4. Confirm this is a disclosed floor (caption or legend explains the floor)
5. Verify the as-of window is visibly deeper than the old 5-year default
6. Perform a backtest run on any strategy at the deep floor date
7. Confirm results render (no crash, no stale chart)

**Expected outcome:** Backtest window deepens to 2005-02-25 floor with honest disclosure; deep backtests complete without errors.

**Pass criteria:** Min as-of date is 2005-02-25; backtest at that date succeeds; page stays responsive.

---

### TC-04 — Evidence ledger all-FAIL regeneration (J-11)

**Type:** browser
**Preconditions:** Backend running; `/evidence` page loads

**Steps:**
1. Navigate to `/evidence`
2. Count visible rows in the evidence table
3. Verify exactly **7 rows** are displayed
4. For at least one row, spot-check the displayed values:
   - Click/expand the row to see full details
   - Record the p-value, edge, control comparison, register date
5. Verify every row's register_date displays as **2026-07-03**
6. Verify every row's verdict shows **FAIL** or "Not yet proven" badge
7. Scroll through all 7 rows and confirm zero "Proven" badges anywhere

**Expected outcome:** Evidence ledger displays exactly 7 regenerated rows, all with 2026-07-03 register date, all with honest FAIL verdicts.

**Pass criteria:** 7 rows displayed, all register_date == 2026-07-03, all verdicts == FAIL, no "Proven" badges render.

---

### TC-05 — No retired edge values rendered anywhere (J-11 anti-goal)

**Type:** browser
**Preconditions:** Backend running; full app surface explored

**Steps:**
1. Verify no appearance of old retired edge values on any page:
   - Old values: +21.34% / +8.91% / +6.36% / +6.12% / +4.69% / +3.33%
   - Old p-value: p=0.0004998
   - Old register dates: 2026-06-30 or 2026-07-01
2. Search these strings in the rendered page HTML/text
3. Verify they do NOT appear on `/stocks`, `/evidence`, `/research/factor-lab`, or any detail page

**Expected outcome:** No retired edge values surface in the UI; the old ledger is completely replaced.

**Pass criteria:** Zero occurrences of the 6 retired edge values or their dates (06-30/07-01) anywhere in the rendered app.

---

### TC-06 — "Not yet proven" badges product-wide (J-01 regression)

**Type:** browser
**Preconditions:** Backend running; `/stocks` leaderboard loads

**Steps:**
1. Navigate to `/stocks`
2. For each visible row's three scores (Leadership, Entry Quality, Risk), locate the evidence badge
3. Verify every badge reads "Not yet proven" or carries an honest FAIL status indicator
4. Confirm no badge reads "Proven" anywhere on the page
5. Verify all three scores on a single row have visible status indicators

**Expected outcome:** Every score shows an evidence status; all are "Not yet proven" this iteration; no vague scores.

**Pass criteria:** 100% of score badges visible and displaying "Not yet proven"; no missing status indicators.

---

### TC-07 — Honest FAIL marking on evidence ledger (J-03 regression)

**Type:** browser
**Preconditions:** Backend running; `/evidence` and stock detail pages accessible

**Steps:**
1. Navigate to `/evidence`
2. Locate a row with a regime-labeled claim (e.g., "Breakout-watch × Risk-on")
3. Verify the regime label is still present and reads "Regime: Risk-on"
4. Confirm the verdict for that claim is FAIL
5. Verify the regime label and FAIL status are both present end-to-end

**Expected outcome:** Regime-conditioned evidence displays honestly with regime label and FAIL verdict.

**Pass criteria:** Regime label visible, verdict shows FAIL, link chain from detail page to evidence ledger works.

---

### TC-08 — Membership timeline and staleness gate (J-12)

**Type:** browser
**Preconditions:** Backend running; `/methodology` page loads

**Steps:**
1. Navigate to `/methodology`
2. Scroll to the membership timeline table
3. Locate a mid-history-IPO name (e.g., ARM 2023-09-14)
4. Verify that name is absent from the timeline before its IPO date
5. Confirm it appears in the timeline after the IPO date
6. Scroll to the exclusion reasons / filters section
7. Verify the `stale_series` exclusion reason is listed
8. Confirm the `max_staleness_days: 10` threshold is disclosed

**Expected outcome:** Membership timeline shows honest entry/exit; staleness gate and threshold are surfaced.

**Pass criteria:** Mid-IPO name absent before IPO, present after; stale_series reason visible; max_staleness_days=10 disclosed.

---

### TC-09 — Stock detail drill into evidence (J-02 regression)

**Type:** browser
**Preconditions:** Backend running; `/stocks/{ticker}` loads

**Steps:**
1. Navigate to `/stocks` and click any stock to open `/stocks/{ticker}` detail
2. Locate a score with a "Not yet proven" badge
3. Click/expand the badge
4. Verify a panel opens showing: hypothesis, verdict, control comparison, registration date, forward-walk score, link to ledger
5. Click the ledger link and verify it navigates to `/evidence` for that claim

**Expected outcome:** Evidence drill opens properly; all required fields render; navigation to ledger works.

**Pass criteria:** Drill panel displays all fields; verdict shows FAIL honestly; ledger link is active.

---

### TC-10 — Broadened pool name renders honestly (J-12)

**Type:** browser
**Preconditions:** Backend running; a name outside the legacy ~122 set is in the pool

**Steps:**
1. Navigate to `/stocks`
2. Search or scroll to locate a name NOT in the legacy ~122 default set
3. Click to open its detail page
4. Verify the page renders with no errors
5. Confirm the stock has real metadata, chart with honest price data, and scores with "Not yet proven" badges
6. Verify no fabricated data appears

**Expected outcome:** Broadened pool member renders correctly; no crashes or fabricated data.

**Pass criteria:** Detail page loads, renders real metadata, chart is honest, no errors.

---

### TC-11 — Required-pass J-01 (every score has visible status)

**Type:** browser
**Preconditions:** Backend running; `/stocks` leaderboard loads

**Steps:**
1. Navigate to `/stocks`
2. For each visible row, verify each of the 3 scores carries a visible evidence-status badge
3. Confirm no score on the page is missing a status indicator
4. Verify badges are inline and unmissable

**Expected outcome:** 100% of scores carry visible status badges.

**Pass criteria:** Every visible score has a badge; 0% missing statuses; badges are inline.

---

### TC-12 — Required-pass J-03 (honest FAIL marking product-wide)

**Type:** browser
**Preconditions:** Backend running; `/stocks`, `/evidence` accessible

**Steps:**
1. Navigate to `/evidence`
2. Verify at least one row displays with a FAIL verdict
3. Navigate to `/stocks` and find a stock detail showing that claim
4. Verify the claim shows an honest FAIL badge
5. Navigate to `/research/factor-lab` and verify factor badges read "Not yet proven"

**Expected outcome:** FAIL verdicts render honestly and consistently across all surfaces.

**Pass criteria:** FAIL marks visible on `/evidence` and linked stock/factor; zero contradictions.

---

### TC-13 — Required-pass J-04 (Breakout-watch regime label with FAIL)

**Type:** browser
**Preconditions:** Backend running; `/evidence` loads

**Steps:**
1. Navigate to `/evidence`
2. Locate the Breakout-watch × Risk-on row
3. Verify the row displays: hypothesis, regime label "Regime: Risk-on", verdict FAIL, register_date 2026-07-03

**Expected outcome:** Breakout-watch row renders with honest regime label and FAIL verdict.

**Pass criteria:** Hypothesis visible, regime == "Risk-on", verdict == FAIL, register_date == 2026-07-03.

---

### TC-14 — Required-pass J-05 (evidence ledger audit end-to-end)

**Type:** browser
**Preconditions:** Backend running; `/evidence` loads

**Steps:**
1. Navigate to `/evidence`
2. Verify 7 rows are displayed
3. For each row, confirm presence of: hypothesis, verdict, control comparison, register date, forward-walk score, linkback
4. Click at least 2 linkbacks and verify navigation to correct research surface
5. Re-locate the badge and verify it links back to the `/evidence` row

**Expected outcome:** All 7 rows are auditable end-to-end; linkbacks work bidirectionally.

**Pass criteria:** 7 rows rendered, all fields present, ≥2 round-trip linkbacks work.

---

### TC-15 — Required-pass J-02 (drill affordance renders)

**Type:** browser
**Preconditions:** Backend running; `/stocks/{ticker}` loads

**Steps:**
1. Navigate to `/stocks` and click a stock to open detail
2. Locate a score badge
3. Verify the badge is clickable
4. Click the badge to expand
5. Confirm the drill panel opens and displays claim details in "Not yet proven" state

**Expected outcome:** Drill affordance is discoverable; drill opens successfully.

**Pass criteria:** Badge is clickable, drill panel opens, state is "Not yet proven".

---

### TC-16 — Broadened pool membership count (J-12)

**Type:** artifact
**Preconditions:** Membership count displayed on `/methodology`

**Steps:**
1. Open `/methodology`
2. Record the total membership count from the membership timeline
3. Confirm the count reflects the broadened ~548-symbol pool (not ~122 old default)

**Expected outcome:** Membership count is ≥500.

**Pass criteria:** Displayed count >= 500; no hardcoded 122-name default.

---

### TC-17 — NVDA real IPO continuity (J-10)

**Type:** browser
**Preconditions:** Backend running; `/stocks/NVDA` loads

**Steps:**
1. Navigate to `/stocks/NVDA`
2. Click "Full history" on the chart
3. Verify the chart's first bar date is **1999-01-22** (NVDA's real IPO)
4. Inspect the close prices around the known NVDA split
5. Verify continuity in close prices across the split (no jump)

**Expected outcome:** NVDA's deep history is honest; IPO date is real; split adjustment is continuous.

**Pass criteria:** First bar == 1999-01-22, split-adjusted close is continuous.

---

### TC-18 — Stale name exclusion (J-12)

**Type:** browser
**Preconditions:** Backend running; a name with data ending mid-history is in the pool

**Steps:**
1. Navigate to `/methodology` membership timeline
2. Locate a symbol whose data ends mid-history
3. Verify the symbol's membership ends at its last data date
4. Confirm membership does not extend past data end
5. Verify no misaligned relative-strength scores

**Expected outcome:** Stale names are cleanly excluded; no misaligned scores.

**Pass criteria:** Symbol exits membership at data end, no misaligned RS score.

---

## Summary

Total test cases: 18

- **Browser tests:** 15
- **Artifact checks:** 3

**Coverage by journey:**
- J-10 (deep history): TC-01, TC-02, TC-03, TC-17
- J-11 (regenerated ledger): TC-04, TC-05
- J-12 (broadened pool + staleness): TC-08, TC-16, TC-18
- J-01 (every score has status): TC-11
- J-03 (honest marking): TC-12
- J-04 (regime label + FAIL): TC-13
- J-05 (ledger audit): TC-14
- J-02 (drill affordance): TC-15
- J-10 (broadened pool honesty): TC-10

All test cases derive directly from the phase spec's TESTING REQUIREMENTS and DEFINITION OF DONE sections.
