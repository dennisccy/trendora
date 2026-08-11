# Phase goal-ops-hardening-iter-59 — UI Test Plan

**Phase:** goal-ops-hardening-iter-59
**Date:** 2026-08-11
**Written by:** ui-impact-analyst (combined mode)
**Frontend URL:** http://localhost:3255

---

## Test Cases

<!-- Test IDs use UT-XX prefix to distinguish from functional test plan TC-XX IDs. -->

---

### UT-01 — `/research/regime-lab` loads without errors under normal conditions (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/research/regime-lab`

**Preconditions:**
- Frontend is running at http://localhost:3255
- Backend is running WITHOUT `TRENDORA_FAULT_INJECT_MEMORY_ERROR` set in its environment (the normal case)
- No login required

**Steps:**
1. Navigate to `http://localhost:3255/research/regime-lab`
2. Wait for the page to finish loading (the "Research — Regime Lab" heading and both tables appear)

**Expected Result:**
- The heading "Research — Regime Lab" is visible
- Two cards are visible: one titled "By regime label" (`data-testid="regime-lab-by-label"`) and one titled
  "By regime-score decile" (`data-testid="regime-lab-by-decile"`)
- No red "Backend unavailable" error card appears
- No browser console errors
- Every "Fwd 1d"/"Fwd 5d"/"Fwd 10d"/"Fwd 20d"/"Fwd 60d" and "MDD 1d"/.../"MDD 60d" column header is
  present in both tables, in that left-to-right order (all Fwd columns first, then all MDD columns)

---

### UT-02 — A memory-pressure degrade renders honestly instead of crashing the page (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/research/regime-lab`

**Preconditions:**
- Requires shell access to restart the backend with an environment variable set — skip this test if you
  only have browser access
- Stop the currently-running backend

**Steps:**
1. Restart the backend via `scripts/start-backend.sh` with `TRENDORA_FAULT_INJECT_MEMORY_ERROR=regime_lab`
   set in its environment (an existing test-only switch, new this iteration for the `"regime_lab"` site —
   it deterministically simulates a `MemoryError` on every horizon `compute_regime_lab` processes; it has
   no effect unless explicitly set)
2. Navigate to `http://localhost:3255/research/regime-lab`
3. Wait for the page to finish loading
4. Hover any "NA" cell in a "Fwd Xd" or "MDD Xd" column of the "By regime label" table
   (`data-testid="regime-lab-by-label"`)
5. Hover any "NA" cell in a "Fwd Xd" or "MDD Xd" column of the "By regime-score decile" table
   (`data-testid="regime-lab-by-decile"`)
6. Restart the backend again WITHOUT `TRENDORA_FAULT_INJECT_MEMORY_ERROR` set
7. Reload `http://localhost:3255/research/regime-lab`

**Expected Result (steps 3-5):**
- The page loads normally — NOT the red "Backend unavailable" error card, NOT a blank page, NOT a browser
  crash/error boundary
- Every "Fwd Xd"/"MDD Xd" cell in BOTH tables shows "NA" (every horizon is injected, so every cell degrades)
- The hover tooltip on every one of those "NA" cells reads exactly: **"Temporarily unavailable — degraded
  under memory pressure"**

**Expected Result (step 7, confirms the fix is condition-triggered, not a permanent state):**
- The SAME page now renders real numeric values (not "NA") in the "Fwd Xd"/"MDD Xd" columns — proving the
  degrade in steps 3-5 was caused by the injected condition, not a permanent regression, and that the
  "never cache a degraded payload" guard did not leave the earlier degraded response stuck in place

---

### UT-03 — The Rank-IC row keeps its old, generic NA tooltip during a degrade (validation / known-gap confirmation)

**Type:** validation
**Priority:** P2
**Surface:** `/research/regime-lab`

**Preconditions:**
- Same as UT-02: backend restarted with `TRENDORA_FAULT_INJECT_MEMORY_ERROR=regime_lab` set

**Steps:**
1. With the fault-injected backend from UT-02 step 1 still running, navigate to
   `http://localhost:3255/research/regime-lab`
2. In the "By regime-score decile" table, locate the "Rank-IC" row (`data-testid="regime-decile-rank-ic-row"`)
3. Hover any "NA" cell in that row under a "Fwd Xd" column

**Expected Result:**
- The cell shows "NA" (not a fabricated number, not blank)
- Its tooltip reads the PRE-EXISTING generic text: **"Not enough independent observations to
  rank-correlate — NA, not a fabricated 0"** — it must NOT read "Temporarily unavailable — degraded under
  memory pressure"
- This is a disclosed scope boundary, not a bug: confirming the OLD wording here (rather than asserting a
  crash) is the correct passing result for this test

---

### UT-04 — A fully-down backend still shows the pre-existing generic error card (error)

**Type:** error
**Priority:** P2
**Surface:** `/research/regime-lab`

**Preconditions:**
- Requires shell access to stop the backend entirely — skip this test if you only have browser access

**Steps:**
1. Stop the backend process entirely (do not restart it)
2. Navigate to `http://localhost:3255/research/regime-lab` (or reload if already on the page)

**Expected Result:**
- A red-bordered card appears with the heading "Backend unavailable"
- Body text reads: "The Regime-Lab evidence could not load from the API. No figures are shown rather than
  fabricated values. Confirm the backend is running and retry."
- A "Retry" button (`data-testid="research-error-retry"`) is visible
- No tables, no partial data, no "Temporarily unavailable" wording appear — this confirms the new
  isolate-and-continue behavior is scoped to a computed-but-degraded response and does not change how a
  fully unreachable backend is reported
- Restart the backend afterward (`scripts/start-backend.sh`, no special environment variable) so later
  tests are unaffected

---

### UT-05 — Normal (non-degraded) figures are unchanged from before this phase (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/research/regime-lab`

**Preconditions:**
- Backend running WITHOUT `TRENDORA_FAULT_INJECT_MEMORY_ERROR` set
- At least one as-of date is available (use the global as-of selector's default / most recent option)

**Steps:**
1. Navigate to `http://localhost:3255/research/regime-lab`
2. Note the value and `n=` shown in the "Fwd 20d" column for the first row of the "By regime label" table
3. Open DevTools → Network tab, find the `GET /api/research/regime-lab` request, and inspect its JSON
   response body
4. Confirm the response body has NO `regime_lab_status` key, and no `by_horizon[]` entry anywhere in the
   payload has a `status` key

**Expected Result:**
- The value/`n=` observed in step 2 matches the number shown in the table (no discrepancy between raw API
  data and rendered UI)
- Step 4's absence of `regime_lab_status`/`status` confirms this is a genuinely clean (non-degraded)
  response — the byte-identity guarantee (an automated backend test, not re-verified manually here) means
  this value is provably the same one the page showed before this phase's change
- Clicking a column header (e.g. "Fwd 20d") still re-sorts the table rows (NA-last), and clicking an "N="
  chip on a populated cell still opens the matching cohort in a new tab at `/research/samples` — both
  pre-existing behaviors are unaffected by this phase

---

### UT-06 — Regime Lab remains reachable from the Research index exactly as before (ux)

**Type:** ux
**Priority:** P3
**Surface:** `/research`

**Steps:**
1. Navigate to `http://localhost:3255/research`
2. Locate the card/link with `data-testid="research-lab-link-regime-lab"`

**Expected Result:**
- A card titled "Regime Lab" is visible with description text starting "How have stocks' forward returns
  and downside risk differed across market regimes?"
- Clicking it navigates to `http://localhost:3255/research/regime-lab`
- No new badge, icon, or "degraded"/"unavailable" indicator was added to this card — this phase changed
  only cell-level rendering inside the page itself, not the entry point or its description (confirms no
  navigation regression was introduced)

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | Page loads under normal conditions | smoke | P1 | `/research/regime-lab` |
| UT-02 | Memory-pressure degrade renders honestly | happy-path | P1 | `/research/regime-lab` |
| UT-03 | Rank-IC row keeps old NA tooltip (known gap) | validation | P2 | `/research/regime-lab` |
| UT-04 | Fully-down backend shows generic error card | error | P2 | `/research/regime-lab` |
| UT-05 | Normal figures unchanged from before this phase | regression | P1 | `/research/regime-lab` |
| UT-06 | Regime Lab still reachable from Research index | ux | P3 | `/research` |

**P1 tests (UT-01, UT-02, UT-05) must all pass for browser QA verdict to be PASS.**
