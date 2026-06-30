# goal-mcp-loop-iter-5 Functional Test Plan

**Phase:** goal-mcp-loop-iter-5
**Date:** 2026-06-30
**Frontend Present:** yes

## Phase Goal

Close the verification-integrity gap by fixing the QA harness port-binding, re-confirm all five Must-have journeys end-to-end through the canonical browser-qa-agent lane with fresh screenshots, and produce the post-QA audit handoff.

## Test Cases

### TC-01 — Frontend port-free preamble frees stale process

**Type:** artifact
**Preconditions:** `scripts/start-frontend.sh` script exists; `$FRONTEND_PORT` (default 3000) has a stale process holding it from a prior `next start` invocation.

**Steps:**
1. Start a background `next server` on port 3000 and let it run
2. Verify port 3000 is occupied: `lsof -ti :3000` returns a PID
3. Execute `bash scripts/start-frontend.sh`
4. Verify the script completes without hanging
5. Verify port 3000 is now bound to the NEW `next start` process launched by the script
6. Verify `lsof -ti :3000` returns a different PID than the stale process
7. Verify the readiness probe returns 2xx serving the current bundle (not stale): `curl -s http://localhost:3000 | grep -q '<html'` and HTTP status is 200

**Expected outcome:** The script pre-bind preamble successfully kills the stale process, waits for port release, and binds the new `next start` successfully. The new bundle is served, not the stale one.

**Pass criteria:** Script exits 0; new PID ≠ old PID; port 3000 is reachable; HTTP 200 returned; `<html` tag present in response body (confirming current bundle, not stale).

---

### TC-02 — Frontend port-free preamble handles already-free port (happy path)

**Type:** artifact
**Preconditions:** Port 3000 is free; `scripts/start-frontend.sh` exists.

**Steps:**
1. Verify port 3000 is free: `lsof -ti :3000` exits non-zero
2. Execute `bash scripts/start-frontend.sh`
3. Measure elapsed time from start to readiness probe returning 2xx
4. Verify `next start` binds and serves within ~10 seconds (preamble should exit immediately on free port)

**Expected outcome:** Port-free preamble exits immediately (no wait loop delays) when port is already free. `next start` proceeds normally.

**Pass criteria:** Script exits 0 within ~10s; no lingering sleep delays; HTTP 200 from `http://localhost:3000` within 10s; startup time ≤ 10s (not inflated by unnecessary waits).

---

### TC-03 — Pre-flight reachability gate confirms backend connection

**Type:** api
**Preconditions:** Backend is running; frontend is running; both services are healthy.

**Steps:**
1. Run `curl -s http://localhost:8000/api/evidence`
2. Parse JSON response
3. Check `proven_signals` keys: must include `["leadership_score"]`
4. Check first claim entry: `proven=true`, `signal="leadership_score"`
5. Check second claim entry: `kind="event-study"`, `signal=null`, `regime="Risk-on"`, `subject="Breakout-watch"`
6. Run `curl -s http://localhost:3000/stocks` and verify response is HTML with leaderboard content (non-empty rows)

**Expected outcome:** Backend `/api/evidence` returns 2 certified claims; leaderboard renders non-empty with ≥1 stock row.

**Pass criteria:** `GET /api/evidence` returns 200; `proven_signals` contains `leadership_score`; first claim has `proven=true`; second claim has `kind="event-study"` and `regime="Risk-on"`; leaderboard HTML contains ≥1 ticker symbol (non-empty).

---

### TC-04 — J-01 `/stocks` leaderboard shows evidence badges

**Type:** browser
**Preconditions:** Frontend is running; backend is running; reachability confirmed (TC-03 passing).

**Steps:**
1. Navigate to `http://localhost:3000/stocks`
2. Wait for leaderboard to render (≥1 row visible)
3. Locate the first stock row's score area
4. Identify the evidence badge(s) in the score area
5. Read the badge text (should be "Proven" or "Not yet proven")
6. Verify "Leadership" badge reads "Proven"
7. Verify "Entry Quality" and "Risk" badges read "Not yet proven"
8. Scroll down and verify ≥1 additional row has a badge visible
9. Take screenshot and save to `reports/qa/goal-mcp-loop-iter-5-evidence/UT-04-stocks-badges.png`

**Expected outcome:** Each leaderboard row's score area displays evidence badge(s); Leadership badge reads "Proven"; Entry Quality and Risk read "Not yet proven"; at least one badge is present on each row.

**Pass criteria:** Screenshot shows ≥1 badge on first row; Leadership badge text == "Proven"; Entry Quality and Risk badges text == "Not yet proven"; ≥2 rows visible, each with a badge; no score lacks a status badge.

---

### TC-05 — J-02 `/stocks/{ticker}` detail shows and expands proof panel

**Type:** browser
**Preconditions:** Frontend is running; leaderboard renders (TC-04 passing).

**Steps:**
1. Navigate to `http://localhost:3000/stocks`
2. Click the first stock row to open detail at `/stocks/{ticker}`
3. Wait for detail page to render
4. Locate a score with a "Proven" badge (should be Leadership)
5. Click the badge or its expand control
6. Wait for the proof panel to expand (may be below the fold initially)
7. Scroll the proof panel into the viewport
8. Verify the panel displays: out-of-sample test result, control comparison, certified-claim id, registration date
9. Take screenshot and save to `reports/qa/goal-mcp-loop-iter-5-evidence/UT-05-detail-proof-panel.png` (with panel visible in frame)

**Expected outcome:** Proof panel expands and contains: out-of-sample test, control comparison (vs SPY/QQQ/sector/random), claim id, registration date.

**Pass criteria:** Screenshot shows expanded panel; panel text contains keywords: "out-of-sample", "control" or "vs SPY", "claim", and a date matching certified-claims.jsonl registration; panel is fully visible in viewport (not cut off).

---

### TC-06 — J-03 Unproven signals render "Not yet proven" (Entry Quality + Risk)

**Type:** browser
**Preconditions:** Frontend is running; `/stocks` leaderboard renders.

**Steps:**
1. Navigate to `http://localhost:3000/stocks`
2. Locate the first stock row's score area
3. Verify Entry Quality badge text == "Not yet proven"
4. Verify Risk badge text == "Not yet proven"
5. Verify no inline per-stock score badge is lit for the signal-less Breakout-watch regime claim
6. Navigate to `/stocks/{ticker}` detail
7. Verify Entry Quality and Risk badges still read "Not yet proven"
8. Take screenshot and save to `reports/qa/goal-mcp-loop-iter-5-evidence/UT-06-not-yet-proven.png`

**Expected outcome:** Entry Quality and Risk scores display "Not yet proven" (not a confident number); no Breakout-watch regime badge appears inline on individual stocks.

**Pass criteria:** Screenshot shows "Not yet proven" text for Entry Quality and Risk on both leaderboard and detail; no Breakout-watch regime badge visible inline on stock rows; Leadership badge is "Proven", but Entry Quality + Risk are not.

---

### TC-07 — J-04 Dashboard regime card links to `/evidence` with regime scoping

**Type:** browser
**Preconditions:** Frontend is running; backend serves `/api/dashboard`.

**Steps:**
1. Navigate to `http://localhost:3000/`
2. Wait for Dashboard to render
3. Locate the regime card (should display current regime, e.g., "Risk-on 76.05/100")
4. Verify the card displays the regime name and score
5. Locate the affordance text "See evidence proven in this regime →" (or similar)
6. Click the affordance to navigate to `/evidence`
7. Wait for `/evidence` to render
8. Locate the second row in the claims list (Breakout-watch regime claim)
9. Scroll the second row into the viewport
10. Verify the row displays: Breakout-watch setup, "Regime: Risk-on" label, holdout +6.12%, p-value, control comparison, registration date
11. Take screenshot and save to `reports/qa/goal-mcp-loop-iter-5-evidence/UT-07-regime-evidence.png` (with 2nd row visible)

**Expected outcome:** Dashboard regime card displays current regime and affordance; clicking affordance navigates to `/evidence` with regime-scoped claims; second row is labeled with the regime it applies to.

**Pass criteria:** Screenshot shows regime card with score; affordance link is clickable and leads to `/evidence`; second row visible in screenshot with "Regime: Risk-on" label; values match API (holdout +6.12%, registered 2026-06-30); no regime rows truncated or cut off.

---

### TC-08 — J-04 Evidence row values byte-match API `GET /api/evidence`

**Type:** api
**Preconditions:** Backend is running; frontend loaded; claim values visible in browser (TC-07 passing).

**Steps:**
1. Run `curl -s http://localhost:8000/api/evidence | jq '.[1]'` to get the second claim (Breakout-watch)
2. Extract fields: `holdout_return`, `p_value`, `control_return`, `registration_date`
3. Note the exact values (e.g., holdout_return=6.12, p_value=0.0004998, control_return=6.12, registration_date="2026-06-30")
4. Return to the screenshot from TC-07
5. Verify the `/evidence` page displays the SAME values (byte-match) for the second row: holdout +6.12%, p=0.0004998, control +6.12% vs SPY, registered 2026-06-30

**Expected outcome:** Displayed values on `/evidence` row 2 are byte-identical to API response.

**Pass criteria:** Holdout return on page == API value (6.12% or 6.12); p-value on page == API value (0.0004998); control return on page == API value (6.12% vs SPY); registration date on page == API date (2026-06-30).

---

### TC-09 — J-05 Evidence ledger renders both claims and linkback round-trip works

**Type:** browser
**Preconditions:** Frontend is running; `/evidence` page is accessible.

**Steps:**
1. Navigate to `http://localhost:3000/evidence`
2. Wait for claims list to render
3. Verify the list shows ≥2 rows: leadership_score (Proven) and Breakout-watch (Regime: Risk-on)
4. Locate the leadership_score row
5. Verify it has a linkback affordance (e.g., "Backs: Stocks leaderboard →")
6. Click the linkback to navigate to `/stocks`
7. Verify `/stocks` leaderboard loads and shows Leadership badges with "Proven" status
8. Click a badge or navigate back to `/evidence`
9. Verify the browser returns to `/evidence` and the claims list is still intact (no blank state)
10. Take screenshot and save to `reports/qa/goal-mcp-loop-iter-5-evidence/UT-09-evidence-linkback.png`

**Expected outcome:** `/evidence` displays both claims; leadership row has linkback affordance; round-trip navigation (/evidence → /stocks → /evidence) preserves state; both claims remain visible after round-trip.

**Pass criteria:** Screenshot shows ≥2 claim rows; leadership row text contains "Proven"; linkback affordance is clickable; round-trip navigation succeeds (no 404 or broken state); both claims visible on return.

---

### TC-10 — Unit tests remain green (no code-path regression)

**Type:** artifact
**Preconditions:** Backend and frontend test suites exist; no app code changes in this iteration (harness-only).

**Steps:**
1. Run backend tests: `cd apps/backend && .venv/bin/python -m pytest tests/test_evidence.py -v`
2. Run backend API tests: `cd apps/backend && .venv/bin/python -m pytest tests/test_api_evidence.py -v`
3. Run frontend tests: `cd apps/frontend && npm test -- --passWithNoTests`
4. Capture all output; note pass/fail counts
5. Verify each test suite exits with code 0 (all pass)

**Expected outcome:** All backend and frontend tests pass (exit code 0); no new failures introduced.

**Pass criteria:** Backend test output: X tests pass, 0 fail, exit code 0; frontend test output: Y tests pass (or passWithNoTests), 0 fail, exit code 0.

---

### TC-11 — Canonical browser-qa-agent lane produces UT-* screenshots for all five journeys

**Type:** artifact
**Preconditions:** Phase execution reaches the auditor stage; `reports/phase-goal-mcp-loop-iter-5-ui-test-results.md` is generated by the browser-qa-agent.

**Steps:**
1. After QA and browser verification, check for `reports/phase-goal-mcp-loop-iter-5-ui-test-results.md`
2. Verify the file contains `browser_checks_run=true` (not false/skipped)
3. Verify the file lists journey results: J-01, J-02, J-03, J-04, J-05
4. Verify each journey has a PASS or partial verdict (J-04 must flip from partial → PASS)
5. Verify UT-* screenshot files exist in the evidence directory for each journey:
   - `UT-01-stocks-badges.png` (or similar)
   - `UT-02-detail-proof.png`
   - `UT-03-not-yet-proven.png`
   - `UT-04-regime-evidence.png`
   - `UT-05-evidence-list.png`
6. Verify J-01, J-02, J-03, J-05 are PASS (re-confirmed with fresh canonical pixels)
7. Verify J-04 is PASS (flipped from partial)

**Expected outcome:** Canonical lane runs successfully (not SKIPPED); all five journeys render fresh screenshots; J-04 transitions from partial → PASS.

**Pass criteria:** File exists; `browser_checks_run=true`; ≥5 UT-* images exist; all five journeys listed; J-01/J-02/J-03/J-05 verdict == PASS; J-04 verdict == PASS (not partial); no all-SKIP entry.

---

## Summary

**Total test cases:** 11
**API tests:** 3 (TC-03, TC-08, TC-10)
**Browser tests:** 6 (TC-04, TC-05, TC-06, TC-07, TC-09, TC-11)
**Artifact checks:** 2 (TC-01, TC-02)
**Infrastructure/Harness tests:** 2 (TC-01, TC-02)

### Critical Success Criteria (Anti-Goal Guards)
- **Port-free preamble works:** TC-01 and TC-02 must pass (stale process freed; free port handled efficiently)
- **Reachability gate passes:** TC-03 must pass (backend reachable, 2 claims in API, non-empty leaderboard)
- **All five journeys re-verified:** TC-04 through TC-09 must pass (all journeys render and display correct data)
- **No regressions:** TC-10 must pass (unit tests green, no code-path changes)
- **Canonical lane completes:** TC-11 must pass (browser-qa-agent produces UT-* screenshots, not SKIPPED; J-04 flips to PASS)
- **Evidence integrity:** Displayed values must byte-match API (TC-08); all "proven" claims must be backed by certified-claims.jsonl; unproven signals must read "Not yet proven" (TC-06)
- **No anti-goal violations:** Zero `apps/` diff; determinism preserved; no lookahead; regime claim does not light inline score badges (TC-06)
