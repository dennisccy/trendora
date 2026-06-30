# Phase goal-mcp-loop-iter-4 — UI Test Plan

**Phase:** goal-mcp-loop-iter-4
**Date:** 2026-06-30
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3255

---

## Test Cases

---

### UT-01 — Evidence page loads without errors

**Type:** smoke
**Priority:** P1
**Surface:** `/evidence`

**Preconditions:**
- Frontend is running at http://localhost:3255
- Backend API is reachable (`/api/evidence` returns 200)

**Steps:**
1. Navigate to `http://localhost:3255/evidence`
2. Wait for the page to fully load (the page heading must be visible)

**Expected Result:**
- Page renders without a blank screen or error message
- A page heading for the Evidence section is visible
- Two distinct claim rows are rendered on the page
- No browser console errors or uncaught exceptions

---

### UT-02 — Dashboard loads without errors

**Type:** smoke
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend is running at http://localhost:3255
- Backend API is reachable (Dashboard calls at minimum the regime and leaderboard APIs)

**Steps:**
1. Navigate to `http://localhost:3255/`
2. Wait for the page to fully load

**Expected Result:**
- Dashboard page renders without blank screen or error message
- The Market Regime card is visible on the page
- A regime score and label are visible inside the Market Regime card

---

### UT-03 — Breakout-watch row displays "Regime: Risk-on" badge

**Type:** happy-path
**Priority:** P1
**Surface:** `/evidence`

**Preconditions:**
- Frontend is running at http://localhost:3255
- `/api/evidence` returns a 2-entry certified-claims ledger that includes a Breakout-watch entry with `regime: "Risk-on"` and `proven: true`

**Steps:**
1. Navigate to `http://localhost:3255/evidence`
2. Scroll down until both claim rows are visible
3. Locate the second claim row (the Breakout-watch row — it appears below the leadership/score row)
4. Look in the row header area next to the verdict badge

**Expected Result:**
- A badge labeled exactly "Regime: Risk-on" is visible in the second row's header, beside the green "PASS" verdict badge
- The first (leadership/score) row does NOT show any badge containing the text "Regime:"
- The "Regime: Risk-on" badge is readable (not truncated or hidden behind another element)

---

### UT-04 — Breakout-watch row shows correct title and subtitle

**Type:** happy-path
**Priority:** P1
**Surface:** `/evidence`

**Preconditions:**
- Frontend is running at http://localhost:3255
- `/api/evidence` returns the Breakout-watch Risk-on entry with subject "Breakout-watch setup"

**Steps:**
1. Navigate to `http://localhost:3255/evidence`
2. Scroll down until the second claim row is visible
3. Read the title text displayed at the top of the second claim row
4. Read the subtitle text displayed below the title on the same row

**Expected Result:**
- The row title reads "Breakout-watch setup" (not "Unmapped signal" or any other placeholder)
- A subtitle line reading "Out-of-sample edge in the Risk-on regime" is visible directly beneath the title
- No developer placeholder text (e.g., "Unmapped signal", "TODO", or blank) appears anywhere on the row

---

### UT-05 — Breakout-watch linkback reads "Research event-study lab" and navigates to /research/event-study

**Type:** happy-path
**Priority:** P1
**Surface:** `/evidence`

**Preconditions:**
- Frontend is running at http://localhost:3255
- The second claim row (Breakout-watch setup) is visible on `/evidence`

**Steps:**
1. Navigate to `http://localhost:3255/evidence`
2. Scroll down until the second claim row (Breakout-watch setup) is visible
3. Locate the linkback line in the second claim row — it begins with the text "Backs:"
4. Read the full linkback text on the second claim row
5. Click the "Backs: Research event-study lab →" link
6. Wait for navigation to complete and read the URL in the browser address bar

**Expected Result:**
- The linkback text reads "Backs: Research event-study lab →" (not "Backs: Stocks leaderboard →")
- After clicking, the browser address bar shows `http://localhost:3255/research/event-study`
- The page for the Research event-study lab loads without errors

---

### UT-06 — Dashboard Market Regime card contains the Evidence affordance link

**Type:** happy-path
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend is running at http://localhost:3255
- The Dashboard Market Regime card renders with regime score and label

**Steps:**
1. Navigate to `http://localhost:3255/`
2. Locate the Market Regime card on the Dashboard
3. Scroll or expand within the Market Regime card to see the component-breakdown disclosure area
4. Look for a link below the component-breakdown disclosure area

**Expected Result:**
- A link with the exact text "See evidence proven in this regime →" is visible below the component-breakdown disclosure in the Market Regime card
- The link is displayed as a clickable hyperlink (not greyed out or as plain text)
- No error message, placeholder, or empty space appears where the link should be

---

### UT-07 — Dashboard affordance link navigates to the Evidence page

**Type:** happy-path
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend is running at http://localhost:3255
- The "See evidence proven in this regime →" link is visible in the Dashboard Market Regime card

**Steps:**
1. Navigate to `http://localhost:3255/`
2. Locate the Market Regime card on the Dashboard
3. Locate the "See evidence proven in this regime →" link below the component-breakdown disclosure
4. Click "See evidence proven in this regime →"
5. Wait for navigation to complete

**Expected Result:**
- The browser navigates to `http://localhost:3255/evidence`
- The browser address bar shows `http://localhost:3255/evidence`
- The Evidence page loads with both claim rows visible (the leadership row and the Breakout-watch row)

---

### UT-08 — Breakout-watch row displays holdout edge, control comparison, and registration date

**Type:** happy-path
**Priority:** P1
**Surface:** `/evidence`

**Preconditions:**
- Frontend is running at http://localhost:3255
- `/api/evidence` returns the Breakout-watch entry with `holdout_edge: 0.06125`, `control: "SPY"`, and `register_date: "2026-06-30"`

**Steps:**
1. Navigate to `http://localhost:3255/evidence`
2. Scroll down until the second claim row (Breakout-watch setup) is visible
3. Read the holdout edge value displayed in the row
4. Read the control comparison label in the row
5. Read the registration date displayed in the row

**Expected Result:**
- The holdout edge value reads "+6.12%" (or an equivalent formatted representation of 0.06125 such as "+6.12 pp")
- The control comparison reads "vs SPY"
- The registration date reads "2026-06-30"

---

### UT-09 — Leadership score row has no regime badge and linkback is unchanged

**Type:** regression
**Priority:** P1
**Surface:** `/evidence`

**Preconditions:**
- Frontend is running at http://localhost:3255
- `/api/evidence` returns both entries; the leadership_score row is the first row on the page

**Steps:**
1. Navigate to `http://localhost:3255/evidence`
2. Locate the first claim row on the page (the leadership/score row — it appears above the Breakout-watch row)
3. Scan the first row header for any badge or text containing "Regime:"
4. Read the linkback text on the first claim row
5. Read the out-of-sample edge value on the first claim row
6. Read the verdict badge on the first claim row

**Expected Result:**
- The first (leadership) row has NO badge or text containing "Regime:" — the badge is completely absent from this row
- The linkback reads "Backs: Stocks leaderboard →" (unchanged from iteration 3)
- The out-of-sample edge value reads "+6.36%"
- The verdict badge reads "PASS"

---

### UT-10 — Dashboard regime score and label unchanged after affordance addition

**Type:** regression
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend is running at http://localhost:3255
- The Dashboard Market Regime card renders

**Steps:**
1. Navigate to `http://localhost:3255/`
2. Locate the Market Regime card on the Dashboard
3. Read the regime label text displayed in the card
4. Read the regime score number displayed in the card

**Expected Result:**
- The regime label reads "Risk-on" (unchanged)
- The regime score reads "76.05" (unchanged)
- Neither value is missing, blank, or altered by the presence of the new "See evidence proven in this regime →" link below the component breakdown

---

### UT-11 — Regime-conditioned evidence is discoverable from Dashboard in one click

**Type:** ux
**Priority:** P2
**Surface:** `/` and `/evidence`

**Preconditions:**
- Frontend is running at http://localhost:3255
- User starts on the Dashboard with no prior knowledge of the Evidence page URL

**Steps:**
1. Navigate to `http://localhost:3255/`
2. Without typing any URL or using the navigation menu, look at the Market Regime card for a way to learn more about regime-related evidence
3. Locate the "See evidence proven in this regime →" link in the Market Regime card
4. Click "See evidence proven in this regime →" — this is the single click required
5. On the Evidence page at `http://localhost:3255/evidence`, look at the second claim row
6. Observe whether the "Regime: Risk-on" badge makes the connection between the Dashboard regime and this evidence row self-explanatory

**Expected Result:**
- The full journey from Dashboard → regime-conditioned evidence is achievable in exactly 1 click (no menu navigation, no URL typing)
- The label "See evidence proven in this regime →" is self-explanatory in the Dashboard context — a non-technical reader would understand it references the Risk-on regime shown in the same card
- The "Regime: Risk-on" badge on the Evidence page immediately connects the claim row to the current market regime shown on the Dashboard
- No developer knowledge is required to complete this discovery flow

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | Evidence page loads without errors | smoke | P1 | `/evidence` |
| UT-02 | Dashboard loads without errors | smoke | P1 | `/` |
| UT-03 | Breakout-watch row displays "Regime: Risk-on" badge | happy-path | P1 | `/evidence` |
| UT-04 | Breakout-watch row shows correct title and subtitle | happy-path | P1 | `/evidence` |
| UT-05 | Breakout-watch linkback reads "Research event-study lab" and navigates to /research/event-study | happy-path | P1 | `/evidence` |
| UT-06 | Dashboard Market Regime card contains the Evidence affordance link | happy-path | P1 | `/` |
| UT-07 | Dashboard affordance link navigates to the Evidence page | happy-path | P1 | `/` |
| UT-08 | Breakout-watch row displays holdout edge, control comparison, and registration date | happy-path | P1 | `/evidence` |
| UT-09 | Leadership score row has no regime badge and linkback is unchanged | regression | P1 | `/evidence` |
| UT-10 | Dashboard regime score and label unchanged after affordance addition | regression | P1 | `/` |
| UT-11 | Regime-conditioned evidence is discoverable from Dashboard in one click | ux | P2 | `/` + `/evidence` |

**P1 tests must all pass for browser QA verdict to be PASS.**
