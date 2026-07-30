# Phase goal-ops-hardening-iter-36 — UI Test Plan

**Phase:** goal-ops-hardening-iter-36
**Date:** 2026-07-30
**Written by:** ui-impact-analyst (combined mode)
**Frontend URL:** http://localhost:3255

---

## Test Cases

<!-- Test IDs use UT-XX prefix to distinguish from functional test plan TC-XX IDs. -->

---

### UT-01 — Factor Lab loads without errors (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/research/factor-lab`

**Preconditions:**
- Frontend running at http://localhost:3255
- Backend running and healthy (`GET /api/health` returns 200)

**Steps:**
1. Navigate to `http://localhost:3255/research/factor-lab`
2. Wait for the page to fully load (data table appears)

**Expected Result:**
- The heading "Research — Factor Lab" is visible
- Eventually a data table (factors with forward-return edge and drawdown columns) renders — no blank screen, no "Backend unavailable" card
- No console errors

---

### UT-02 — Factor Lab shows the labelled "still computing" card on a slow load (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/research/factor-lab`

**Preconditions:**
- Frontend running at http://localhost:3255, backend running
- Chrome DevTools open (Network tab)

**Steps:**
1. Open Chrome DevTools → Network tab → set Throttling to "Slow 3G" (or add a >3 second delay to the `GET /api/research/factor-lab*` request via "Network conditions")
2. Navigate to `http://localhost:3255/research/factor-lab`
3. Watch the page for the first 3+ seconds while the request is still pending

**Expected Result:**
- Within the first ~3 seconds, a plain skeleton placeholder may appear briefly with no alarming copy
- After 3 seconds of the fetch still being pending, a card with `data-testid="slow-compute-notice"` appears, showing heading text starting with "Still computing —" followed by an elapsed-time value (e.g. "4s elapsed") and a spinning icon
- Explanatory text below reads approximately "The Factor Lab is derived once per dataset from the whole stored forward-return history..."
- Once the response arrives, the computing card disappears and the data table renders
- Reset Network throttling to "No throttling" afterward

---

### UT-03 — Factor Lab error card shows a working Retry control (error)

**Type:** error
**Priority:** P1
**Surface:** `/research/factor-lab`

**Preconditions:**
- Frontend running at http://localhost:3255
- Backend process stopped (or `GET /api/research/factor-lab*` blocked via Chrome DevTools "Block request URL")

**Steps:**
1. Stop the backend service (e.g., terminate the uvicorn process serving port 8255), or in Chrome DevTools Network tab right-click any prior `research/factor-lab` request and choose "Block request URL"
2. Navigate to (or reload) `http://localhost:3255/research/factor-lab`
3. Wait for the fetch to fail
4. Restart the backend service (or un-block the request in DevTools)
5. Click the "Retry" button (`data-testid="research-error-retry"`) inside the error card

**Expected Result:**
- After step 3: a card reads "Backend unavailable" with body text "The Factor-Lab evidence could not load from the API. No figures are shown rather than fabricated values. Confirm the backend is running and retry." and a "Retry" button (`data-testid="research-error-retry"`) is visible
- After step 5: the error card disappears and the page re-enters the loading state (skeleton or computing card) — never a second frozen error card
- Once the backend responds successfully, the data table renders

---

### UT-04 — Phase Severity Lab loads without errors (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/research/phase-severity-lab`

**Preconditions:**
- Frontend running at http://localhost:3255, backend healthy

**Steps:**
1. Navigate to `http://localhost:3255/research/phase-severity-lab`
2. Wait for the page to fully load

**Expected Result:**
- The heading "Research — Market Phase & Severity Lab" is visible
- The by-label and by-decile tables render — no blank screen, no "Backend unavailable" card
- No console errors

---

### UT-05 — Phase Severity Lab shows the labelled "still computing" card on a slow load (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/research/phase-severity-lab`

**Preconditions:**
- Frontend running at http://localhost:3255, backend running
- Chrome DevTools Network throttling available

**Steps:**
1. Set Network throttling to "Slow 3G" (or delay the `GET /api/research/phase-severity-lab*` response past 3 seconds)
2. Navigate to `http://localhost:3255/research/phase-severity-lab`
3. Watch the page during the pending fetch

**Expected Result:**
- A card with `data-testid="slow-compute-notice"` appears after 3+ seconds, heading text starting "Still computing —" with an elapsed-time value and a spinner
- Explanatory text mentions "The Market Phase & Severity Lab is derived once per dataset..."
- Data tables render once the response arrives; reset throttling afterward

---

### UT-06 — Phase Severity Lab error card shows a working Retry control (error)

**Type:** error
**Priority:** P1
**Surface:** `/research/phase-severity-lab`

**Preconditions:**
- Backend process stopped or request blocked

**Steps:**
1. Stop the backend (or block `GET /api/research/phase-severity-lab*` via DevTools)
2. Navigate to `http://localhost:3255/research/phase-severity-lab`
3. Wait for the fetch to fail
4. Restart the backend (or un-block the request)
5. Click the "Retry" button (`data-testid="research-error-retry"`)

**Expected Result:**
- A "Backend unavailable" card appears with text "The Market Phase & Severity-Lab evidence could not load from the API..." and a visible "Retry" button
- Clicking Retry re-enters the loading state (never a second frozen error card); once the backend responds, the tables render

---

### UT-07 — Regime × Phase × Factor shows the labelled "still computing" card above its own skeleton (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/research/regime-phase-factor`

**Preconditions:**
- Frontend running at http://localhost:3255, backend running
- Chrome DevTools Network throttling available

**Steps:**
1. Set Network throttling to "Slow 3G" (or delay `GET /api/research/regime-phase-factor*` past 3 seconds)
2. Navigate to `http://localhost:3255/research/regime-phase-factor`
3. Watch the page during the pending fetch

**Expected Result:**
- The heading "Research — Regime × Phase × Factor" is visible immediately (controls render before data)
- After 3+ seconds, a card with `data-testid="slow-compute-notice"` appears above the page's own `CombinationSkeleton` placeholder, heading text starting "Still computing —" with an elapsed-time value
- The rows/table render once the response arrives; reset throttling afterward

---

### UT-08 — Regime × Phase × Factor's own error card shows a working Retry control (error)

**Type:** error
**Priority:** P1
**Surface:** `/research/regime-phase-factor`

**Preconditions:**
- Backend process stopped or request blocked

**Steps:**
1. Stop the backend (or block `GET /api/research/regime-phase-factor*` via DevTools)
2. Navigate to `http://localhost:3255/research/regime-phase-factor`
3. Wait for the fetch to fail
4. Restart the backend (or un-block the request)
5. Click the "Retry" button — this page uses its OWN test id: `data-testid="rpf-error-retry"` (NOT `research-error-retry`)

**Expected Result:**
- The page's own inline card reads "Backend unavailable" with text "The Regime × Phase × Factor study could not load from the API. No figures are shown rather than fabricated values — confirm the backend is running and retry." and a "Retry" button (`data-testid="rpf-error-retry"`)
- Clicking Retry re-enters the loading state; once the backend responds, rows render (or the empty state if the filtered result set is genuinely empty)

---

### UT-09 — Severity-velocity × Regime loads without errors (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/research/severity-velocity`

**Preconditions:**
- Frontend running at http://localhost:3255, backend healthy

**Steps:**
1. Navigate to `http://localhost:3255/research/severity-velocity`
2. Wait for the page to fully load

**Expected Result:**
- The heading "Research — Severity-velocity × Regime" is visible
- The study body renders — no blank screen, no "Backend unavailable" card
- No console errors

---

### UT-10 — Severity-velocity × Regime shows the labelled "still computing" card on a slow load (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/research/severity-velocity`

**Preconditions:**
- Frontend running at http://localhost:3255, backend running
- Chrome DevTools Network throttling available

**Steps:**
1. Set Network throttling to "Slow 3G" (or delay `GET /api/research/severity-velocity*` past 3 seconds)
2. Navigate to `http://localhost:3255/research/severity-velocity`
3. Watch the page during the pending fetch

**Expected Result:**
- A card with `data-testid="slow-compute-notice"` appears after 3+ seconds, heading text starting "Still computing —" with an elapsed-time value and a spinner
- The study body renders once the response arrives; reset throttling afterward

---

### UT-11 — Severity-velocity × Regime error card shows a working Retry control (error)

**Type:** error
**Priority:** P1
**Surface:** `/research/severity-velocity`

**Preconditions:**
- Backend process stopped or request blocked

**Steps:**
1. Stop the backend (or block `GET /api/research/severity-velocity*` via DevTools)
2. Navigate to `http://localhost:3255/research/severity-velocity`
3. Wait for the fetch to fail
4. Restart the backend (or un-block the request)
5. Click the "Retry" button (`data-testid="research-error-retry"`)

**Expected Result:**
- A "Backend unavailable" card appears with text "The Severity-velocity × Regime study could not load from the API..." and a visible "Retry" button
- Clicking Retry re-enters the loading state (never a second frozen error card); once the backend responds, the study body renders

---

### UT-12 — Regime Lab still shows its existing computing/error/retry behavior (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/research/regime-lab`

**Preconditions:**
- Frontend running at http://localhost:3255, backend running
- This page received NO code change in this phase — it is the reference implementation the other 4 pages were wired to match

**Steps:**
1. Navigate to `http://localhost:3255/research/regime-lab`
2. Confirm the page loads and (on a cold cache) shows its existing "Still computing — Ns elapsed" card, then data

**Expected Result:**
- Behavior is unchanged from before this phase: labelled computing card on a slow load, retryable error card on failure — this page must not regress

---

### UT-13 — Data page coverage panel shows byte-identical values (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/data`

**Preconditions:**
- Frontend and backend running; a pre-phase capture of `/data`'s reported values is available (or use the dev handoff's recorded live values: `universe_count: 540`, `membership_timeline` with 1,880 points, `coverage_status: current`)

**Steps:**
1. Navigate to `http://localhost:3255/data`
2. Note the displayed universe count, coverage status, and membership-timeline chart/point count

**Expected Result:**
- Values match the pre-phase capture exactly (or the dev handoff's recorded live values) — the backend batching change must not alter any displayed number
- Page loads without an error boundary or blank screen

---

### UT-14 — Evidence page per-claim expectations panel still renders real figures (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/evidence`

**Preconditions:**
- Frontend and backend running under normal (non-throttled) conditions

**Steps:**
1. Navigate to `http://localhost:3255/evidence`
2. Click into any certified claim's row to expand its "drawdown & dry-spell expectations" panel

**Expected Result:**
- The panel shows real computed figures (max drawdown, underwater days, time-to-recover), NOT the "not available right now" / `expectations_status: unavailable` placeholder, under normal load
- Figures match a pre-phase capture if one is available (byte-identical payload requirement)

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | Factor Lab loads | smoke | P1 | `/research/factor-lab` |
| UT-02 | Factor Lab computing notice | happy-path | P1 | `/research/factor-lab` |
| UT-03 | Factor Lab Retry works | error | P1 | `/research/factor-lab` |
| UT-04 | Phase Severity Lab loads | smoke | P1 | `/research/phase-severity-lab` |
| UT-05 | Phase Severity Lab computing notice | happy-path | P1 | `/research/phase-severity-lab` |
| UT-06 | Phase Severity Lab Retry works | error | P1 | `/research/phase-severity-lab` |
| UT-07 | Regime×Phase×Factor computing notice | happy-path | P1 | `/research/regime-phase-factor` |
| UT-08 | Regime×Phase×Factor Retry works (`rpf-error-retry`) | error | P1 | `/research/regime-phase-factor` |
| UT-09 | Severity-velocity loads | smoke | P1 | `/research/severity-velocity` |
| UT-10 | Severity-velocity computing notice | happy-path | P1 | `/research/severity-velocity` |
| UT-11 | Severity-velocity Retry works | error | P1 | `/research/severity-velocity` |
| UT-12 | Regime Lab unchanged | regression | P1 | `/research/regime-lab` |
| UT-13 | Data page values unchanged | regression | P1 | `/data` |
| UT-14 | Evidence panel renders real figures | regression | P1 | `/evidence` |

**P1 tests must all pass for browser QA verdict to be PASS.**
