# goal-mcp-loop-iter-3 Functional Test Plan

**Phase:** goal-mcp-loop-iter-3  
**Date:** 2026-06-30  
**Frontend Present:** yes

## Phase Goal

Browser-prove the already-shipped evidence layer (J-01/J-02/J-03/J-05) by fixing the QA bring-up. Verify the Leadership "Proven" badge, proof drill-down, and evidence ledger render correctly with values byte-identical to the `/api/evidence` endpoint. Re-confirm Entry Quality and Risk remain "Not yet proven". No app-source changes expected — this is an operational bring-up fix for the verification lane.

## Pre-flight Gate (must pass before browser tests)

These checks gate the browser lane. All three must hold:

### PF-01 — Backend health check
- **Command:** `curl -s http://localhost:8255/api/health`
- **Expected:** HTTP 200
- **Pass criteria:** Response status is 200; backend is ready and stable

### PF-02 — Evidence endpoint confirms leadership_score certified
- **Command:** `curl -s http://localhost:8255/api/evidence | jq '.proven_signals.leadership_score.proven'`
- **Expected:** `true`
- **Pass criteria:** Response JSON shows `proven_signals.leadership_score.proven == true` (certification is live in the ledger)

### PF-03 — Frontend renders populated leaderboard (not empty, not "Checking backend…")
- **Command:** Open `http://localhost:3255/stocks` (no `?as_of=` param; use default view)
- **Expected:** Page renders ≥1 leaderboard row; each row has a ticker, scores, and evidence badges
- **Pass criteria:** Leaderboard has ≥1 populated row (iter-1 baseline: ~120 rows); no "Checking backend…" loading state; no empty table

**Gating rule:** If any pre-flight check fails (PF-01, PF-02, or PF-03), the browser lane FAILS the bring-up gate. A frontend-not-running skip or all-SKIP test result is a HARD FAIL of the verification, not a pass. Backend must be healthy (200), evidence must be certified, and the leaderboard must render with rows.

---

## Test Cases

### TC-01 — Stock detail page loads without errors

**Type:** browser  
**Preconditions:** Pre-flight gate passes; `/stocks` renders populated leaderboard

**Steps:**
1. Navigate to `http://localhost:3255/stocks`
2. Click the first stock ticker to open `/stocks/{ticker}`
3. Wait for page to load
4. Observe score cards rendered (Leadership, Entry Quality, Risk)

**Expected outcome:** Stock detail page renders at `/stocks/{ticker}` with all three score cards visible and accessible

**Pass criteria:** Page title/URL shows ticker; ≥3 score cards present; page has no console errors or 5xx responses

---

### TC-02 — Leadership score has "Why proven?" toggle

**Type:** browser  
**Preconditions:** Stock detail page (`/stocks/{ticker}`) is open and rendered

**Steps:**
1. Locate the Leadership score card
2. Look for a "Why proven?" button or drill-down toggle on the card
3. Observe the presence and styling of the toggle

**Expected outcome:** Leadership score card displays a "Why proven?" button or interactive element

**Pass criteria:** "Why proven?" button is visible and clickable on the Leadership card; button is not greyed out or disabled

---

### TC-03 — Stocks leaderboard shows Leadership "Proven" badge

**Type:** browser  
**Preconditions:** `/stocks` leaderboard is rendered with ≥1 row

**Steps:**
1. Navigate to `http://localhost:3255/stocks`
2. Observe the Leadership column in the leaderboard table
3. Check each row for an evidence badge

**Expected outcome:** Leadership column in each row shows a "Proven" badge with accent styling

**Pass criteria:** At least one row has a "Proven" badge in the Leadership column; badge is styled distinctly (accent green or primary color); no row lacks an evidence status

---

### TC-04 — Evidence ledger page loads with leadership_score row

**Type:** browser  
**Preconditions:** Frontend is running; navigation to `/evidence` is possible

**Steps:**
1. Navigate to `http://localhost:3255/evidence` (via nav or direct URL)
2. Wait for the ledger table to load
3. Look for a row with `signal = leadership_score`

**Expected outcome:** Evidence ledger page renders; at least one claim row exists for `leadership_score`

**Pass criteria:** `/evidence` page loads (no 404, no loading spinner hung); ledger table contains ≥1 row; at least one row is labeled or keyed with "leadership_score"

---

### TC-05 — Expand "Why proven?" panel shows OOS test result

**Type:** browser  
**Preconditions:** Stock detail page (`/stocks/{ticker}`) open; Leadership card has "Why proven?" toggle

**Steps:**
1. Click the "Why proven?" button on the Leadership score card
2. Wait for the proof panel to expand
3. Observe the panel content

**Expected outcome:** Panel expands and displays the out-of-sample test result

**Pass criteria:** Panel shows "PASS" verdict chip; displays holdout edge (+6.36%); displays p-value (~0.0005); displays cohort size (n=12297); all values match `/api/evidence` for the same as-of date

---

### TC-06 — Proof panel shows SPY benchmark control comparison

**Type:** browser  
**Preconditions:** "Why proven?" panel is expanded on Leadership card

**Steps:**
1. Examine the expanded proof panel content
2. Locate the SPY benchmark control comparison row

**Expected outcome:** Panel contains a row labeled "vs SPY (benchmark control)" showing the excess return

**Pass criteria:** SPY control row is visible and readable; displays +6.36% (the leadership_score OOS excess vs SPY control); matches `/api/evidence`

---

### TC-07 — Proof panel shows certified claim id and registration date

**Type:** browser  
**Preconditions:** "Why proven?" panel is expanded on Leadership card

**Steps:**
1. Examine the bottom of the expanded proof panel
2. Look for the claim id and registration date

**Expected outcome:** Panel displays the certified claim identifier and the registration date

**Pass criteria:** Claim id is visible (e.g., "leadership_score"); registration date is visible and reads "registered 2026-06-30"; link to evidence ledger is present

---

### TC-08 — "View backing evidence row →" link navigates to evidence anchor

**Type:** browser  
**Preconditions:** "Why proven?" panel is expanded; proof panel contains linkback text

**Steps:**
1. In the expanded proof panel, locate the link text "View backing evidence row →" or similar
2. Click the link
3. Observe the navigation

**Expected outcome:** Browser navigates to `/evidence` page and scrolls to the leadership_score claim row (anchor #signal-leadership_score)

**Pass criteria:** URL changes to `/evidence#signal-leadership_score`; the corresponding ledger row is visible/highlighted; no 404 or navigation error

---

### TC-09 — Evidence claim row shows all five required fields

**Type:** browser  
**Preconditions:** `/evidence` page is open; leadership_score row is visible

**Steps:**
1. Navigate to `/evidence` or scroll to the leadership_score row
2. Examine the row content in the ledger table
3. Verify all five fields are populated

**Expected outcome:** The leadership_score row displays all five required fields: hypothesis, OOS verdict, SPY control, registration date, forward-walk score-to-date

**Pass criteria:** All five columns/fields are present, non-empty, and readable in the row; values are byte-identical to `/api/evidence` response for the same as-of date

---

### TC-10 — "Backs: Stocks leaderboard →" link navigates to /stocks

**Type:** browser  
**Preconditions:** `/evidence` page is open; leadership_score row is visible; row has a linkback button

**Steps:**
1. In the leadership_score row, locate the "Backs: Stocks leaderboard →" link
2. Click the link
3. Observe the navigation

**Expected outcome:** Browser navigates back to `/stocks` with the leaderboard visible

**Pass criteria:** URL changes to `/stocks` (or `/stocks?as_of=<date>` if persisting date param); leaderboard is fully rendered; at least one row is visible; "Proven" badge is present in Leadership column

---

### TC-11 — Full round-trip: leaderboard → detail → proof panel → evidence → leaderboard

**Type:** browser  
**Preconditions:** Frontend is running; pre-flight gate passes

**Steps:**
1. Start at `/stocks` leaderboard
2. Click a stock ticker to open `/stocks/{ticker}`
3. Click "Why proven?" on Leadership card to expand proof panel
4. Click "View backing evidence row →" to navigate to `/evidence#signal-leadership_score`
5. In evidence row, click "Backs: Stocks leaderboard →" to return to `/stocks`
6. Verify the leaderboard is rendered

**Expected outcome:** All navigation steps complete successfully; final state is `/stocks` with populated leaderboard

**Pass criteria:** All steps execute without error; no broken links; all pages load and render; final URL is `/stocks` (or `/stocks?as_of=<date>`); leaderboard has ≥1 row with "Proven" badge visible

---

### TC-12 — Stocks leaderboard "Proven" badge links to evidence anchor

**Type:** browser  
**Preconditions:** `/stocks` leaderboard is rendered; Leadership "Proven" badge is visible

**Steps:**
1. In the leaderboard, locate a "Proven" badge in the Leadership column
2. Click the badge
3. Observe the navigation

**Expected outcome:** Browser navigates to `/evidence#signal-leadership_score`

**Pass criteria:** URL changes to `/evidence#signal-leadership_score`; leadership_score row is visible and highlighted; page loads without error

---

### TC-13 — Entry Quality score card has no "Why proven?" toggle

**Type:** browser  
**Preconditions:** Stock detail page (`/stocks/{ticker}`) is open; Entry Quality card is visible

**Steps:**
1. Locate the Entry Quality score card
2. Look for a "Why proven?" button or toggle on the card
3. Verify the absence of the toggle

**Expected outcome:** Entry Quality card does not display a "Why proven?" button (no drill-down toggle)

**Pass criteria:** No clickable "Why proven?" element is present on Entry Quality card; card renders score and badge only

---

### TC-14 — Risk score card has no "Why proven?" toggle

**Type:** browser  
**Preconditions:** Stock detail page (`/stocks/{ticker}`) is open; Risk card is visible

**Steps:**
1. Locate the Risk score card
2. Look for a "Why proven?" button or toggle on the card
3. Verify the absence of the toggle

**Expected outcome:** Risk card does not display a "Why proven?" button (no drill-down toggle)

**Pass criteria:** No clickable "Why proven?" element is present on Risk card; card renders score and badge only

---

### TC-15 — Entry Quality and Risk leaderboard badges read "Not yet proven"

**Type:** browser  
**Preconditions:** `/stocks` leaderboard is rendered; Entry Quality and Risk columns are visible

**Steps:**
1. Navigate to `/stocks`
2. Observe the Entry Quality and Risk columns in the leaderboard
3. Check the badges on multiple rows
4. Verify the badge text and styling

**Expected outcome:** Entry Quality and Risk badges display "Not yet proven" text with muted/gray styling

**Pass criteria:** Both Entry Quality and Risk badges in leaderboard rows read "Not yet proven"; styling is distinctly muted (not accent green); all rows are consistent

---

### TC-16 — "Why proven?" panel collapses on second click

**Type:** browser  
**Preconditions:** Stock detail page (`/stocks/{ticker}`) open; "Why proven?" panel is expanded

**Steps:**
1. Click "Why proven?" button to expand the proof panel (first click)
2. Verify the panel is expanded
3. Click the button again (second click)
4. Observe the panel state

**Expected outcome:** Panel collapses and is no longer visible after the second click

**Pass criteria:** Panel expands on first click; collapses on second click; toggle is repeatable; no console errors

---

### TC-17 — "Why proven?" feature is discoverable within 2 clicks from leaderboard

**Type:** browser  
**Preconditions:** `/stocks` leaderboard is rendered with populated rows

**Steps:**
1. Start at `/stocks` leaderboard
2. Click a stock ticker (1st click)
3. Locate and click the "Why proven?" button on Leadership card (2nd click)
4. Verify the proof panel is now visible

**Expected outcome:** "Why proven?" proof panel is reached in exactly 2 clicks from the leaderboard

**Pass criteria:** Proof panel is fully visible and interactive after 2 clicks; feature is easily discoverable; no additional clicks required beyond the expected path

---

### TC-18 — "Proven" badge is visually distinct from "Not yet proven" badges

**Type:** browser  
**Preconditions:** `/stocks` leaderboard is rendered with mixed evidence statuses (Leadership "Proven", Entry Quality / Risk "Not yet proven")

**Steps:**
1. Navigate to `/stocks`
2. Observe the leadership column and Entry Quality / Risk columns side-by-side
3. Compare the visual styling of the badges

**Expected outcome:** "Proven" badges (Leadership) are visually distinct from "Not yet proven" badges (Entry Quality, Risk)

**Pass criteria:** "Proven" badge uses accent styling (green or primary color); "Not yet proven" badges use muted styling (gray); contrast is immediately apparent; users can distinguish the two states at a glance

---

## API Correctness Checks

### API-01 — Displayed numbers match `/api/evidence` endpoint

**Type:** api  
**Preconditions:** Backend is running; `/api/evidence` returns valid data with `proven_signals.leadership_score.proven == true`

**Steps:**
1. Run `curl -s http://localhost:8255/api/evidence | jq '.proven_signals.leadership_score'` to get the canonical evidence data
2. For each browser test that displays evidence values (TC-05, TC-06, TC-07, TC-09), compare the displayed values to the API response
3. Verify byte-identical match for: holdout edge (+6.36%), p-value (~0.0005), cohort size (n=12297), SPY control comparison, registration date

**Expected outcome:** All displayed values in the browser UI match the `/api/evidence` response exactly for the same as-of date

**Pass criteria:** No discrepancy between displayed numbers and API response; all evidence values are byte-identical; no rounding or truncation in the browser display

---

## Invariant / Regression Checks

### REG-01 — Empty ledger returns 200, not 500

**Type:** api  
**Preconditions:** Backend is running

**Steps:**
1. Query `curl -s http://localhost:8255/api/evidence`
2. If the ledger is empty (no claims), verify the response status and shape

**Expected outcome:** Even if no claims exist, the endpoint returns HTTP 200 with `{"claims": [], "proven_signals": {}}`

**Pass criteria:** Status code is 200 (never 500); response is valid JSON; empty ledger structure is intact

---

### REG-02 — Backend-down state renders honest health badge

**Type:** browser  
**Preconditions:** Backend service is temporarily stopped or unreachable

**Steps:**
1. Verify backend is down (e.g., stop the service)
2. Navigate to `/stocks` in the browser
3. Observe the health state indicator or message

**Expected outcome:** Frontend renders an honest "Backend unavailable…" or similar message; never a faked "Ready" state

**Pass criteria:** Page indicates the backend is unreachable; no confident numbers are displayed; health badge (if present) shows a degraded/unavailable state; no fabricated data is shown

---

## Summary

**Total test cases:** 20  
**Pre-flight gate checks:** 3  
**Browser tests:** 15 (TC-01 through TC-18)  
**API tests:** 2 (API-01, REG-01)  
**Browser invariant tests:** 1 (REG-02)  

**Test coverage by journey:**
- **J-01** (Every score shows evidence status): TC-03, TC-13, TC-14, TC-15, REG-01, REG-02
- **J-02** (Drill into proof behind a score): TC-02, TC-05, TC-06, TC-07, TC-08, API-01
- **J-03** (Unproven signals marked honestly): TC-13, TC-14, TC-15, REG-02
- **J-05** (Audit evidence ledger): TC-04, TC-09, TC-10, TC-12

**End-to-end round-trip verification:** TC-11 (leaderboard → detail → proof panel → evidence → leaderboard)

**Critical gates:**
- Pre-flight (PF-01, PF-02, PF-03) must pass; if any fails, browser lane is FAIL
- All browser tests must execute and PASS (no SKIPs acceptable)
- All displayed evidence values must be byte-identical to `/api/evidence`
- No anti-goal language (return/price/buy-sell/alpha) on any proof surface
