# Goal MCP Loop Iteration 2 Functional Test Plan

**Phase:** goal-mcp-loop-iter-2
**Date:** 2026-06-30
**Frontend Present:** yes

## Phase Goal

Ship the first referee-certified claim so the Leadership score reads "Proven" with a browser-verifiable proof drill-down on stock detail pages, showing the out-of-sample test result, SPY control comparison, and certified-claim id/date — while Entry Quality and Risk remain honestly "Not yet proven."

---

## Test Cases

### TC-01 — Leadership badge reads "Proven" on stock leaderboard

**Type:** browser
**Preconditions:** 
- Frontend and backend running at localhost:3000 and localhost:8000
- Certified-claims ledger contains one PASS entry with `signal: "leadership_score"` and `verdict.status == "PASS"`
- GET /api/evidence returns a populated claim with `proven_signals["leadership_score"].proven == true`

**Steps:**
1. Navigate to `http://localhost:3000/stocks`
2. Observe the leaderboard table rows
3. Locate the "Leadership" score badge in the first data row

**Expected outcome:** The Leadership badge displays the text "Proven" in an accent color (not grayed out)
**Pass criteria:** Screenshot shows "Proven" badge visible on the leaderboard; badge text is readable and styled distinctly from "Not yet proven" badges

---

### TC-02 — Entry Quality and Risk badges stay "Not yet proven" on leaderboard

**Type:** browser
**Preconditions:** Same as TC-01

**Steps:**
1. Navigate to `http://localhost:3000/stocks`
2. Locate the same row as TC-01
3. Observe the "Entry Quality" and "Risk" score badges

**Expected outcome:** Both badges display "Not yet proven" in neutral/muted styling, with no proof panel or drill-down option
**Pass criteria:** Screenshot confirms Entry Quality and Risk badges read "Not yet proven"; no expand controls visible on these badges

---

### TC-03 — Stock detail Leadership badge reads "Proven" and is expandable

**Type:** browser
**Preconditions:** Same as TC-01

**Steps:**
1. From `/stocks`, click on a stock (any ticker) to open `/stocks/{ticker}` detail page
2. Locate the Leadership score card (typically shows the score number and badge)
3. Observe the "Proven" badge and any expand/disclosure controls

**Expected outcome:** The Leadership badge reads "Proven"; an expand control (e.g., "Why proven?" toggle or disclosure button) is visible and interactive
**Pass criteria:** Screenshot shows "Proven" badge + interactive expand control on the Leadership score card; control is clickable (cursor changes or hover effect visible)

---

### TC-04 — Proof panel expands to show out-of-sample test result

**Type:** browser
**Preconditions:** Stock detail page open at `/stocks/{ticker}` with Leadership score visible and expandable

**Steps:**
1. Click the expand control on the Leadership score card
2. Observe the revealed panel content
3. Locate the section labeled or describing the out-of-sample test

**Expected outcome:** A disclosure panel expands revealing at minimum:
- Verdict status: "PASS"
- Holdout edge: "6.36%" (or "0.06359" as decimal, matching the ledger entry)
- P-value: "0.0005" (rounded; matches the ledger `p_value = 0.0004998`)
**Pass criteria:** Expanded panel displays all three out-of-sample test fields byte-identical to `GET /api/evidence` response for the `leadership_score` claim

---

### TC-05 — Proof panel shows SPY control comparison

**Type:** browser
**Preconditions:** Proof panel is expanded on stock detail Leadership score card

**Steps:**
1. Within the expanded proof panel, locate the control comparison section
2. Read the label and the value shown

**Expected outcome:** A row or section explicitly labeled "vs SPY (benchmark control)" or similar displays the control excess value of "6.36%" or equivalent
**Pass criteria:** Panel shows control comparison labeled with "SPY" or "benchmark control"; value matches `verdict.control_excess` from the ledger (0.06359 or 6.36%)

---

### TC-06 — Proof panel shows certified-claim id and registration date

**Type:** browser
**Preconditions:** Proof panel is expanded on stock detail Leadership score card

**Steps:**
1. Within the expanded proof panel, locate the claim identification section
2. Read the claim identifier and registration date

**Expected outcome:** Panel displays:
- Claim id in the format: "leadership_score · registered 2026-06-30" (or similar)
- A clickable link to `/evidence#signal-leadership_score` (the anchor matching the ledger row id)
**Pass criteria:** Claim identifier is visible and matches format "leadership_score · registered YYYY-MM-DD"; link navigates to `/evidence` page anchored at the correct row

---

### TC-07 — Proof panel linkback to Evidence ledger

**Type:** browser
**Preconditions:** Proof panel is expanded on stock detail Leadership score card

**Steps:**
1. Click the link to the Evidence ledger from within the proof panel
2. Wait for navigation to complete

**Expected outcome:** Browser navigates to `/evidence` page and auto-scrolls to the `leadership_score` claim row (visible in browser address bar as `#signal-leadership_score`)
**Pass criteria:** URL shows `/evidence#signal-leadership_score`; the page displays the populated claim row in view

---

### TC-08 — /evidence page renders populated leadership_score claim row

**Type:** browser
**Preconditions:** Frontend running; certified-claims ledger has PASS entry for leadership_score

**Steps:**
1. Navigate directly to `http://localhost:3000/evidence`
2. Observe the claims table/list
3. Locate the row for leadership_score claim (should be the first/only populated row)
4. Verify all five fields are present

**Expected outcome:** A single populated claim row displays:
- **Hypothesis:** "Top decile leadership_score" or similar description
- **Out-of-sample verdict:** "PASS", "6.36% edge", "p ≈ 0.0005"
- **Control comparison:** "6.36% vs SPY"
- **Registration date:** "2026-06-30"
- **Forward-walk status:** "Pending" or equivalent (score-to-date not yet computed)
**Pass criteria:** All five claim fields render with correct values byte-identical to `GET /api/evidence`; no empty/placeholder fields; row has `id="signal-leadership_score"` anchor

---

### TC-09 — /evidence claim row "Backs:" linkback to stocks leaderboard

**Type:** browser
**Preconditions:** /evidence page open; leadership_score claim row visible

**Steps:**
1. Locate the "Backs: Stocks leaderboard →" link within the leadership_score claim row
2. Click the link
3. Wait for navigation to complete

**Expected outcome:** Browser navigates to `/stocks` leaderboard page
**Pass criteria:** URL changes to `/stocks`; leaderboard table loads with stock rows

---

### TC-10 — Round-trip navigation: stocks → proof panel → /evidence → stocks

**Type:** browser
**Preconditions:** Frontend running; certified-claims ledger populated

**Steps:**
1. Start at `/stocks` leaderboard
2. Click a stock to open detail page
3. Expand the Leadership proof panel
4. Click the Evidence ledger link in the panel
5. On `/evidence`, click the "Backs: Stocks leaderboard" link
6. Confirm return to `/stocks`

**Expected outcome:** Each navigation succeeds; no error pages; final URL is `/stocks`
**Pass criteria:** All four navigations complete without errors; no broken links; page content loads correctly at each destination

---

### TC-11 — Not-yet-proven scores have no proof panel on stock detail

**Type:** browser
**Preconditions:** Stock detail page open at `/stocks/{ticker}`

**Steps:**
1. Locate Entry Quality and Risk score cards on the stock detail page
2. Attempt to expand or interact with these badges
3. Verify no proof panel appears

**Expected outcome:** Entry Quality and Risk badges read "Not yet proven"; no expand control or proof panel is present; clicking the badge does nothing or shows no disclosure
**Pass criteria:** Screenshot shows "Not yet proven" badges without expand controls; no panel reveals when interacting with these badges

---

### TC-12 — Proof panel is absent/fail-safe when ledger is empty

**Type:** api
**Preconditions:** Empty or missing certified-claims ledger (e.g., after reset)

**Steps:**
1. Run: `curl -s http://localhost:8000/api/evidence | jq '.proven_signals'`
2. Verify the response

**Expected outcome:** Returns an empty object `{}` (no proven_signals keys)
**Pass criteria:** Response status is 200 (not 500); body is valid JSON with `"proven_signals": {}`

---

### TC-13 — GET /api/evidence returns correct schema with PASS entry

**Type:** api
**Preconditions:** Certified-claims ledger contains the PASS entry for leadership_score

**Steps:**
1. Run: 
```bash
curl -s http://localhost:8000/api/evidence | jq '.proven_signals["leadership_score"]'
```
2. Verify the response contains all required fields with correct values

**Expected outcome:** Response contains:
```json
{
  "proven": true,
  "verdict": {
    "status": "PASS",
    "holdout_edge": 0.06359,
    "p_value": 0.0004998,
    "control_excess": 0.06359
  },
  "register_date": "2026-06-30",
  "signal": "leadership_score"
}
```
**Pass criteria:** Status is 200; all fields present and values byte-identical to ledger entry; `proven == true` only for PASS entries

---

### TC-14 — Leadership badge regression test: badge links to /evidence anchor

**Type:** browser
**Preconditions:** Stock leaderboard at `/stocks`; Leadership badge visible with "Proven" status

**Steps:**
1. Click the "Proven" badge on the Leadership score column
2. Observe navigation

**Expected outcome:** Browser navigates to `/evidence#signal-leadership_score` and auto-scrolls to show the leadership_score claim row in view
**Pass criteria:** URL shows `#signal-leadership_score`; claim row is visible and highlighted

---

### TC-15 — Proof panel values remain in sync on navigation

**Type:** browser
**Preconditions:** Stock detail page with expanded proof panel

**Steps:**
1. Open stock detail with expanded proof panel showing all values
2. Navigate away (to `/stocks` or `/evidence`)
3. Navigate back to the same stock detail page
4. Expand the proof panel again
5. Compare values to the previous state

**Expected outcome:** All proof panel values (holdout edge, p-value, control excess, claim id, date) are identical to the first view
**Pass criteria:** Values are byte-identical across navigations; no data drift observed

---

### TC-16 — Artifact check: certified-claims.jsonl contains PASS entry

**Type:** artifact
**Preconditions:** Phase implementation complete

**Steps:**
1. Read file: `runs/goal-session-mcp-loop/state/certified-claims.jsonl`
2. Parse the JSON line for leadership_score claim
3. Verify structure

**Expected outcome:** File contains exactly one line (first claim), parseable as JSON, with:
- `claim.signal == "leadership_score"`
- `verdict.status == "PASS"`
- `verdict.holdout_edge == 0.06359`
- `verdict.p_value == 0.0004998`
- `verdict.control_excess == 0.06359`
- `register_date == "2026-06-30"`
**Pass criteria:** File exists and is readable; JSON entry is valid; all required fields present with correct values

---

### TC-17 — Unit test: proof panel renders correctly for proven signal

**Type:** artifact
**Preconditions:** Unit test file exists and test suite runs

**Steps:**
1. Review or run test file: `apps/frontend/lib/evidence.test.ts` (or equivalent)
2. Verify test case for proof panel rendering with a proven signal

**Expected outcome:** Test asserts that when a signal is provided and `proven == true`, the proof panel displays:
- status == "PASS"
- holdout_edge, p_value, control_excess values
- claim id and registration date
**Pass criteria:** Test exists; test passes; assertions cover all proof fields

---

### TC-18 — Unit test: proof panel is absent for not-yet-proven signals

**Type:** artifact
**Preconditions:** Unit test file exists and test suite runs

**Steps:**
1. Review or run test file: `apps/frontend/lib/evidence.test.ts`
2. Verify test case for absent proof panel when signal has `proven == false`

**Expected outcome:** Test asserts that when a signal is provided with `proven == false`, no proof panel renders (returns null or empty component)
**Pass criteria:** Test exists; test passes; demonstrates fail-safe behavior

---

### TC-19 — Unit test: build_evidence_payload returns proven_signals with leadership entry

**Type:** artifact
**Preconditions:** Backend test file exists; test suite runs

**Steps:**
1. Review or run test file: `apps/backend/tests/test_evidence.py`
2. Verify test case calling `build_evidence_payload()` with populated certified-claims ledger
3. Confirm assertion on the returned `proven_signals` dict

**Expected outcome:** Test asserts:
- `proven_signals["leadership_score"].proven == true`
- All verdict fields are present and correct
- Entry Quality and Risk are absent from `proven_signals` (not proven)
**Pass criteria:** Test exists; test passes; demonstrates single-signal proven state

---

### TC-20 — Unit test: empty/missing ledger yields empty proven_signals

**Type:** artifact
**Preconditions:** Backend test file exists; test suite runs

**Steps:**
1. Review or run test file: `apps/backend/tests/test_evidence.py`
2. Verify test case calling `build_evidence_payload()` with empty or missing ledger
3. Confirm assertion on return value

**Expected outcome:** Test asserts:
- Response status would be 200 (not error)
- `claims == []`
- `proven_signals == {}`
**Pass criteria:** Test exists; test passes; demonstrates fail-safe empty state

---

## Summary

**Total test cases:** 20
- **Browser tests:** 10 (TC-01, TC-02, TC-03, TC-04, TC-05, TC-06, TC-07, TC-08, TC-09, TC-10, TC-11, TC-14, TC-15)
- **API tests:** 2 (TC-12, TC-13)
- **Artifact/Unit tests:** 8 (TC-16, TC-17, TC-18, TC-19, TC-20)

**Coverage:**
- J-02 proof drill-down: TC-03, TC-04, TC-05, TC-06, TC-07, TC-10, TC-15 (browser verified)
- J-05 Evidence ledger rendering: TC-08, TC-09, TC-10, TC-14 (browser verified)
- J-01 regression (status badges): TC-01, TC-02, TC-11 (browser verified)
- J-03 regression (unproven stays unproven): TC-02, TC-11 (browser verified)
- Data contract / backend: TC-12, TC-13, TC-16, TC-19, TC-20 (API + artifact verified)
- End-to-end badge flip: TC-01, TC-03, TC-14 (real screenshot evidence)
- Fail-safe behavior: TC-12, TC-18 (proven absence on empty/unproven states)
