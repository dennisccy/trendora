# Goal-MCP-Loop Iteration 4 Functional Test Plan

**Phase:** goal-mcp-loop-iter-4
**Date:** 2026-06-30
**Frontend Present:** yes

## Phase Goal

Surface the first regime-conditioned certified evidence claim (Breakout-watch setup in the Risk-on regime) on the Evidence page, clearly labeled with the regime it holds in, and add a Dashboard→Evidence affordance so users can discover regime-scoped decision-support evidence from the current market regime context.

## Test Cases

### TC-01 — Dashboard regime panel displays current regime

**Type:** browser
**Preconditions:** Frontend is running; backend API returns current regime (Risk-on); leaderboard populates.

**Steps:**
1. Navigate to `http://localhost:3000`
2. Locate the regime panel (RegimeGlanceCard on the Dashboard)
3. Verify the regime label displays "Risk-on"
4. Verify the regime score displays "76.05"

**Expected outcome:** Regime panel renders with current regime and score.
**Pass criteria:** Regime label == "Risk-on" AND score == "76.05"

---

### TC-02 — Dashboard regime affordance link navigates to Evidence page

**Type:** browser
**Preconditions:** Frontend is running; Dashboard regime panel is rendered.

**Steps:**
1. Navigate to `http://localhost:3000`
2. Locate the affordance link "See evidence proven in this regime →" in the regime panel
3. Click the link
4. Wait for navigation to complete

**Expected outcome:** User is navigated to `/evidence` page.
**Pass criteria:** Current URL == `http://localhost:3000/evidence`

---

### TC-03 — Evidence page renders regime-conditioned claim with regime label

**Type:** browser
**Preconditions:** Frontend is running; `/api/evidence` returns 2-entry certified-claims ledger (leadership_score PASS + Breakout-watch Risk-on PASS).

**Steps:**
1. Navigate to `http://localhost:3000/evidence`
2. Scroll the page to bring the Breakout-watch claim row into the viewport
3. Locate the regime-conditioned claim row (subject: "Breakout-watch")
4. Verify the "Regime: Risk-on" label/badge is present in the row header
5. Capture a screenshot with the row fully visible

**Expected outcome:** The regime-conditioned claim row displays a prominent "Regime: Risk-on" label in its header.
**Pass criteria:** "Regime: Risk-on" label is visible AND readable AND the row is in the viewport at capture time

---

### TC-04 — Evidence page displays correct holdout edge for regime claim

**Type:** browser
**Preconditions:** Frontend is running; certified-claims ledger has the Breakout-watch Risk-on PASS entry with holdout edge +0.06125.

**Steps:**
1. Navigate to `http://localhost:3000/evidence`
2. Scroll the Breakout-watch claim row into view
3. Locate the displayed holdout edge value
4. Verify it reads "+6.12%" or "+0.06125" (equivalent formatting)
5. Verify the control comparison shows "vs SPY"
6. Verify the registration date displays "2026-06-30"

**Expected outcome:** Displayed values match the certified-claims entry verbatim.
**Pass criteria:** holdout_edge == "+6.12%" (or equivalent) AND control == "SPY" AND register_date == "2026-06-30"

---

### TC-05 — Evidence page regime claim has honest title and non-leaderboard linkback

**Type:** browser
**Preconditions:** Frontend is running; regime claim has `signal: null`; claim title/linkback are rendered.

**Steps:**
1. Navigate to `http://localhost:3000/evidence`
2. Scroll the Breakout-watch claim row into view
3. Locate the claim's title text (should reference "Breakout-watch setup")
4. Locate the linkback text (should NOT say "Backs: Stocks leaderboard →")
5. Verify the linkback points to Dashboard regime context or Research lab (not `/stocks`)

**Expected outcome:** Non-score regime claim has an honest title and a non-"Stocks leaderboard" linkback.
**Pass criteria:** title contains "Breakout-watch" AND linkback does NOT contain "Stocks leaderboard" AND linkback href does NOT link to `/stocks`

---

### TC-06 — Leadership score claim row unchanged (regression check)

**Type:** browser
**Preconditions:** Frontend is running; `/api/evidence` returns the leadership_score PASS entry.

**Steps:**
1. Navigate to `http://localhost:3000/evidence`
2. Locate the leadership (first) claim row
3. Verify the "Regime:" label is NOT present (score claims have no regime)
4. Verify the title still references the leadership score
5. Verify the linkback still says "Backs: Stocks leaderboard →"
6. Verify the row renders unchanged from iteration 3

**Expected outcome:** Leadership row is byte-identical to previous iteration.
**Pass criteria:** NO regime label present AND title AND linkback text are unchanged AND row structure is unchanged

---

### TC-07 — Stock leaderboard shows all three scores with correct proven status (regression)

**Type:** browser
**Preconditions:** Frontend is running; leaderboard populates with ~120 stocks.

**Steps:**
1. Navigate to `http://localhost:3000/stocks`
2. Locate any stock row
3. Verify Leadership score shows status badge "Proven"
4. Verify Entry Quality score shows status badge "Not yet proven"
5. Verify Risk score shows status badge "Not yet proven"

**Expected outcome:** All three scores display; proven status matches iteration 3.
**Pass criteria:** Leadership badge == "Proven" AND Entry Quality badge == "Not yet proven" AND Risk badge == "Not yet proven"

---

### TC-08 — Stock detail page Leadership proof drill-down intact (regression)

**Type:** browser
**Preconditions:** Frontend is running; leaderboard populates; at least one stock has Leadership score.

**Steps:**
1. Navigate to `http://localhost:3000/stocks`
2. Click on any stock row to open the detail page
3. Locate the Leadership score drill-down section
4. Verify it shows the out-of-sample test methodology
5. Verify it displays the SPY control comparison
6. Verify it shows the claim ID and registration date

**Expected outcome:** Leadership proof drill-down renders with all original details.
**Pass criteria:** OOS test description present AND SPY control shown AND claim ID present AND registration date present

---

### TC-09 — Build evidence payload returns correct proven signals and claims (unit)

**Type:** api
**Preconditions:** Backend test environment; certified-claims.jsonl has 2-entry ledger (leadership_score PASS + Breakout-watch Risk-on PASS).

**Steps:**
1. Run: `cd apps/backend && python -m pytest tests/test_evidence.py::test_build_evidence_payload_two_entries -v`
2. Inspect the test output for assertion results
3. Verify `proven_signals` dict contains ONLY `leadership_score` key
4. Verify `claims[]` array contains 2 entries
5. Verify the 2nd entry has `regime == "Risk-on"`, `proven == true`, `signal == null`

**Expected outcome:** Backend assertion passes; no new signal added to proven_signals; regime claim renders as intended.
**Pass criteria:** Test passes with exit code 0 AND `proven_signals` == `{"leadership_score": {...}}` (no other keys) AND regime_claim.regime == "Risk-on"

---

### TC-10 — Regime label rendering (unit test)

**Type:** api
**Preconditions:** Frontend test environment; `lib/evidence.ts` has a regime-label extractor.

**Steps:**
1. Run: `cd apps/frontend && node lib/evidence.test.ts`
2. Verify test case "regime label present" passes (returns "Risk-on" when `claim.claim.regime` == "Risk-on")
3. Verify test case "regime label absent" passes (returns `null` when `claim.claim.regime` is missing/blank)
4. Verify test case "score claim has no regime label" passes (returns `null` for leadership claim)

**Expected outcome:** All regime-label unit tests pass.
**Pass criteria:** All 3 test cases pass with no errors; regime label is correctly extracted and hidden when absent

---

### TC-11 — Non-score claim title and linkback (unit test)

**Type:** api
**Preconditions:** Frontend test environment; `lib/evidence.ts` has a title/linkback resolver.

**Steps:**
1. Run: `cd apps/frontend && node lib/evidence.test.ts`
2. Verify test case "event-study claim honest title" passes (title contains subject name, e.g. "Breakout-watch")
3. Verify test case "event-study claim non-leaderboard linkback" passes (linkback does NOT reference `/stocks`)
4. Verify test case "score claim title and linkback unchanged" passes (title and linkback are byte-identical to iteration 3)

**Expected outcome:** All title/linkback unit tests pass.
**Pass criteria:** All 3 test cases pass; non-score claim has honest title + non-leaderboard linkback; score claim is unchanged

---

### TC-12 — Empty or missing ledger error handling (unit test)

**Type:** api
**Preconditions:** Backend test environment; test mocks missing or empty certified-claims.jsonl.

**Steps:**
1. Run: `cd apps/backend && python -m pytest tests/test_evidence.py::test_build_evidence_payload_empty_ledger -v`
2. Verify the test passes
3. Verify response status code is 200 (not 500)
4. Verify response is `{"claims": [], "proven_signals": {}}`

**Expected outcome:** Missing ledger does not cause a crash; empty response is returned gracefully.
**Pass criteria:** Test passes AND HTTP 200 AND `claims == []` AND `proven_signals == {}`

---

### TC-13 — Claim with blank regime selector (unit test)

**Type:** artifact
**Preconditions:** Frontend code; `ClaimRow` component receives a claim with `regime: ""` or `regime: null`.

**Steps:**
1. Review `apps/frontend/app/evidence/page.tsx` ClaimRow rendering
2. Verify that when `claim.claim.regime` is blank or null, the "Regime: " label is NOT rendered
3. Verify no empty chip (e.g., "Regime: " with no value) appears
4. Verify the row structure remains intact

**Expected outcome:** Blank regime selector is handled gracefully; no visual artifact or crash.
**Pass criteria:** Regime label is completely hidden (no empty "Regime:" chip) AND row renders normally

---

### TC-14 — No anti-goal violation: regime claim is evidence, not a signal

**Type:** artifact
**Preconditions:** Frontend code; backend code; certified-claims ledger.

**Steps:**
1. Review the regime claim's display on `/evidence` page
2. Verify no return-promise language (e.g., no "expected return X%")
3. Verify no buy/sell signal language
4. Verify the claim is framed as "out-of-sample evidence" and "regime-conditioned"
5. Verify nothing reads "Proven" except the leadership score (which already does in iter 3)

**Expected outcome:** Regime claim is presented as historical evidence, never as a buy signal or return promise.
**Pass criteria:** No anti-goal language on the regime row AND all "Proven" badges are on leadership only (no new "Proven" badges for Entry Quality or Risk)

---

### TC-15 — No engine or referee changes (artifact)

**Type:** artifact
**Preconditions:** Git diff between iteration 3 and iteration 4 code.

**Steps:**
1. Run: `git diff main...HEAD -- apps/backend/app/engine/ apps/backend/app/mcp/referee.py`
2. Verify no changes to engine files (scores, regime/forward-return logic)
3. Verify no changes to referee
4. Verify no changes to `/api/evidence` endpoint

**Expected outcome:** Zero engine/referee diff; no new computation added.
**Pass criteria:** Engine and referee files are unchanged AND `/api/evidence` endpoint signature and response shape are unchanged

---

## Summary

**Total test cases:** 15
- **Browser tests:** 8 (TC-01, TC-02, TC-03, TC-04, TC-05, TC-06, TC-07, TC-08)
- **API/Unit tests:** 6 (TC-09, TC-10, TC-11, TC-12, TC-14, TC-15)
- **Artifact checks:** 1 (TC-13)

**Critical pass criteria (DoD blockers):**
- TC-03: Regime label visible on claim row
- TC-04: Displayed values byte-identical to `/api/evidence`
- TC-06: Leadership row unchanged (J-05 regression)
- TC-07: All three scores show correct proven status (J-01/J-03 regression)
- TC-08: Leadership drill-down intact (J-02 regression)
- TC-09: Backend proven_signals dict contains ONLY leadership_score (no signal added)

**Optional/polish (not blockers):**
- Dashboard affordance wording ("See evidence proven in this regime →")
- Non-leaderboard linkback destination (Dashboard vs Research lab — either acceptable)
