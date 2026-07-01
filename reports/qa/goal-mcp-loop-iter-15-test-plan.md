# goal-mcp-loop-iter-15 Functional Test Plan

**Phase:** goal-mcp-loop-iter-15  
**Date:** 2026-07-01  
**Frontend Present:** yes

## Phase Goal

Surface the 7th referee-certified canonical edge — the pre-registered relative-strength (`rs_spy_3m`) top-decile 60-day-horizon factor claim as a "Proven" badge on the Research factor lab and a new row on the Evidence ledger, while leaving all `/stocks` inline score badges unchanged (signal-less claim).

## Test Cases

### TC-01 — Certified claim appended to canonical ledger

**Type:** artifact  
**Preconditions:**  
- Post-decompose gate has completed certification (already done per plan)
- `runs/goal-session-mcp-loop/state/certified-claims.jsonl` exists

**Steps:**
1. Read `certified-claims.jsonl` directly to the file system (do NOT trust rendered UI labels)
2. Locate row 7 (the 7th entry)
3. Verify the row contains: `factor: "rs_spy_3m"`, `slice_kind: "decile"`, `decile: 10`, `horizon: 60`, `direction: "positive"`, `ledger: "canonical"`
4. Verify certification fields: `status: "PASS"`, `deflation: "bonferroni"`, `deflation_divisor: 7`, `required_p: 0.0071428...`
5. Verify evidence fields: `p_value: 0.0004997501249375312`, `holdout_edge: 0.21344270202534893`, `control_excess: 0.21344270202534893`
6. Verify registration: `register_date: "2026-07-01"`, `block_length: 87`

**Expected outcome:** Row 7 exists in canonical ledger with all required fields present and byte-matching the expected values.  
**Pass criteria:** `jq '.[] | select(.factor=="rs_spy_3m" and .horizon==60 and .ledger=="canonical")' certified-claims.jsonl` returns exactly one row with `status="PASS"`, `deflation_divisor=7`, `p_value≈0.0004998`, `holdout_edge≈0.2134`.

---

### TC-02 — /evidence ledger displays 7th row with correct values

**Type:** browser  
**Preconditions:**  
- Backend is running and serving `/api/evidence`
- Frontend is running on `http://localhost:3000`
- Certified-claims.jsonl contains row 7 (TC-01 passed)

**Steps:**
1. Navigate to `http://localhost:3000/evidence` in Chrome
2. Verify the page loads without errors (no "Backend unavailable" pill)
3. Scroll to locate the `rs_spy_3m` D10 h60 claim row (newest row, bottom of list if reverse-chronological)
4. Verify the row displays all standard fields: hypothesis, out-of-sample verdict (PASS), SPY control value (+0.2134 or "+21.34%"), registration date (2026-07-01), forward-walk score-to-date, and a "Backs: Research factor lab →" link
5. Verify the deep-link in the row points to `/evidence#factor-rs_spy_3m-d10-h60`
6. Click the deep-link and verify the browser anchor jumps to that row's DOM element

**Expected outcome:** The new `rs_spy_3m` h60 claim row renders on `/evidence` with all fields present and byte-matching the canonical ledger row 7.  
**Pass criteria:** Row displays `rs_spy_3m D10 h60`, verdict "Proven" / "PASS", edge "+21.34%" or "+0.2134", SPY control "+21.34%", p-value "0.0005" or "0.00050", register date "2026-07-01", divisor "7", and the anchor link is functional.

---

### TC-03 — /research/factor-lab rs_spy_3m h60 badge shows "Proven"

**Type:** browser  
**Preconditions:**  
- Backend is running and serving `/api/evidence`
- Frontend is running on `http://localhost:3000`
- Certified-claims.jsonl contains row 7 (TC-01 passed)

**Steps:**
1. Navigate to `http://localhost:3000/research/factor-lab` in Chrome
2. Locate the `rs_spy_3m` (3-month Relative Strength) factor row in the factor table
3. Scroll the factor row into view if needed
4. Within the evidence column for `rs_spy_3m`, locate the per-horizon evidence chips (h1, h5, h10, h20, h60)
5. Verify that the **h60 chip displays "Proven"** and has a distinct visual state (e.g., checkmark, green pill, or "proven-✓" styling)
6. Verify the h60 chip is clickable and deep-links to `/evidence#factor-rs_spy_3m-d10-h60`
7. Click the h60 "Proven" chip and verify the browser navigates to the `/evidence` page with the anchor `#factor-rs_spy_3m-d10-h60`

**Expected outcome:** The `rs_spy_3m` factor's h60 cohort displays a "Proven" badge on the factor lab, and clicking it deep-links to the evidence row.  
**Pass criteria:** h60 chip displays "Proven" (not "Not yet proven"), has `data-factor="rs_spy_3m"`, `data-horizon="60"`, `data-proven="true"` (or similar), and clicking navigates to `/evidence#factor-rs_spy_3m-d10-h60`.

---

### TC-04 — /research/factor-lab rs_spy_3m uncertified horizons read "Not yet proven"

**Type:** browser  
**Preconditions:**  
- Backend is running and serving `/api/evidence`
- Frontend is running on `http://localhost:3000`
- Certified-claims.jsonl row 7 only certifies h60, no other `rs_spy_3m` horizons are certified

**Steps:**
1. Navigate to `http://localhost:3000/research/factor-lab` in Chrome
2. Locate the `rs_spy_3m` factor row
3. Within the evidence column, locate the per-horizon evidence chips
4. Verify h1 chip displays "Not yet proven" (no "Proven" state)
5. Verify h5 chip displays "Not yet proven"
6. Verify h10 chip displays "Not yet proven"
7. Verify h20 chip displays "Not yet proven"
8. Verify none of h1/h5/h10/h20 have a "proven-✓" visual indicator or link

**Expected outcome:** Only h60 shows "Proven"; all other `rs_spy_3m` horizons display "Not yet proven" with no proof indicator.  
**Pass criteria:** h1/h5/h10/h20 chips all display "Not yet proven" text/styling, have no `data-proven="true"` attribute, and do not deep-link to evidence rows (or deep-link to a non-existent anchor).

---

### TC-05 — proven_signals remains {leadership_score}

**Type:** artifact  
**Preconditions:**  
- Backend is running
- certified-claims.jsonl row 7 is present

**Steps:**
1. Query the backend via API or read the config/engine state for the `proven_signals` set
2. Verify `proven_signals == {"leadership_score"}` (exact set membership, no new signals added)
3. Verify `rs_spy_3m` ∉ `proven_signals` (the 60-day edge is certified but signal-less by design)

**Expected outcome:** `proven_signals` contains only `leadership_score`; `rs_spy_3m` is not a proven signal.  
**Pass criteria:** `proven_signals` JSON field or config value matches `["leadership_score"]` exactly (order may vary), and `rs_spy_3m` is not present.

---

### TC-06 — /stocks inline score badges unchanged (J-01/J-02/J-03 no regression)

**Type:** browser  
**Preconditions:**  
- Frontend is running on `http://localhost:3000`
- `/stocks` page serves via the existing score-badge logic
- Certified-claims.jsonl row 7 is present

**Steps:**
1. Navigate to `http://localhost:3000/stocks` (or equivalent stocks index)
2. Select a stock and view its inline score badge (e.g., leadership score, growth score, if displayed)
3. Verify the badge displays only columns backed by `proven_signals` (leadership_score, etc.)
4. Verify `rs_spy_3m` does NOT appear as a new inline badge, score column, or data field
5. Take a screenshot of the score badge area for evidence

**Expected outcome:** No new `/stocks` inline badges light from the `rs_spy_3m` h60 certification; the score badge set is unchanged.  
**Pass criteria:** Stock detail view shows the same score columns as before (no new `rs_spy_3m` inline badge); badge layout and values match prior iteration (J-01/J-02/J-03 baseline).

---

### TC-07 — Frontend unit test: resolveCohortEvidence resolves rs_spy_3m h60 to "Proven"

**Type:** api  
**Preconditions:**  
- `apps/frontend/lib/evidence.test.ts` exists
- A `rsSpy3mH60Row()` fixture is present (mirroring `vcpContractionH60Row()`) in the ledger test data
- The `resolveCohortEvidence` matcher is implemented

**Steps:**
1. Run the frontend unit tests: `cd apps/frontend && npm test -- evidence.test.ts`
2. Locate the test case for `rs_spy_3m` h60 (should mirror the existing `vcp_contraction` h60 case)
3. Verify the test asserts: `resolveCohortEvidence(cohort) === "Proven"` when a matching canonical PASS claim is present
4. Verify the test asserts: `href === "/evidence#factor-rs_spy_3m-d10-h60"`
5. Verify separate assertions for h1, h5, h10, h20 return "Not yet proven"
6. Verify the test case (o) has been reconciled to use a still-uncertified `rs_spy_3m` horizon (not h60)

**Expected outcome:** The `resolveCohortEvidence` function correctly resolves `rs_spy_3m` h60 to "Proven" with the correct deep-link, and h1/h5/h10/h20 to "Not yet proven".  
**Pass criteria:** Test suite passes with all `rs_spy_3m` assertions green; case (o) no longer uses h60; no existing assertions regress (all prior cases still pass).

---

### TC-08 — Backend engine/referee/ledger byte-identical

**Type:** artifact  
**Preconditions:**  
- Implementation is complete
- No edits to `apps/backend/app/engine/{referee,ledger,forward_walk}.py`, `apps/backend/app/engine/evidence.py`, `apps/backend/app/mcp/tools.py`

**Steps:**
1. Compute MD5 hash of `apps/backend/app/engine/referee.py`
2. Compute MD5 hash of `apps/backend/app/engine/ledger.py`
3. Compute MD5 hash of `apps/backend/app/engine/forward_walk.py`
4. Compute MD5 hash of `apps/backend/app/engine/evidence.py`
5. Compute MD5 hash of `apps/backend/app/mcp/tools.py`
6. Compare hashes to prior iteration (should match — no change)
7. Run backend unit/integration tests: `cd apps/backend && python -m pytest tests/test_evidence.py tests/test_staging_ledger_routing.py -v`
8. Verify all tests pass (especially referee/ledger determinism tests)

**Expected outcome:** All backend engine and evidence files are byte-identical to prior iteration; all backend tests pass unedited.  
**Pass criteria:** MD5 hashes match prior version; test suite returns green (0 failures, all determinism tests pass); referee re-runs the canonical cohort seeded (20240601) and reproduces p-value at floor 0.00049975.

---

### TC-09 — /evidence row displays backend values correctly (no render drift)

**Type:** browser  
**Preconditions:**  
- `/evidence` page is rendering the new row 7
- TC-01 has read the canonical ledger file directly
- Backend is running and responding

**Steps:**
1. Read `certified-claims.jsonl` row 7 to capture exact values: p_value, holdout_edge, control_excess, register_date, deflation_divisor
2. Navigate to `/evidence` in Chrome
3. Locate the `rs_spy_3m` h60 row
4. Extract the displayed p-value, edge (%), SPY control (%), and registration date from the DOM
5. Verify displayed edge matches ledger (0.2134 → "+21.34%")
6. Verify displayed p-value matches ledger (0.0004998, not rounded to 0.0005)
7. Verify displayed SPY control matches ledger (0.2134 → "+21.34%")
8. Verify displayed register date matches ledger (2026-07-01)
9. Verify divisor badge shows "7"

**Expected outcome:** Every numeric value rendered on the `/evidence` row byte-matches the canonical ledger row 7.  
**Pass criteria:** Displayed p-value = "0.0005" or "0.00050" (acceptable rounding), edge = "+21.34%", control = "+21.34%", date = "2026-07-01", divisor = "7"; all fields present and none missing/blank.

---

### TC-10 — J-01/J-02/J-03 (must-have journeys) still pass

**Type:** browser  
**Preconditions:**  
- Backend is running
- Frontend is running
- Prior iteration J-01/J-02/J-03 baseline test results available

**Steps:**
1. Navigate to `/stocks` and verify a stock with `leadership_score` displays the existing score badge
2. Verify the badge column layout is unchanged from prior iteration
3. Navigate to `/research/factor-lab` and verify the `vcp_contraction` factor still shows "Proven" badges at h20 and h60 (J-06/J-07)
4. Verify no regression in factor lab page rendering, sorting, or filtering
5. Navigate to `/evidence` and verify the first 6 rows (prior claims) are unchanged; row 7 is new

**Expected outcome:** All J-01/J-02/J-03 surfaces remain unchanged; no regressions in existing functionality.  
**Pass criteria:** Stock score badge displays leadership_score columns unchanged; factor lab `vcp_contraction` h20/h60 still show "Proven"; `/evidence` first 6 rows unchanged; no 404s or console errors.

---

## Summary

**Total test cases:** 10  
**API tests:** 0  
**Browser tests:** 6 (TC-02, TC-03, TC-04, TC-06, TC-09, TC-10)  
**Artifact checks:** 4 (TC-01, TC-05, TC-07, TC-08)

**Key verification focus:**
- Ledger row 7 byte-match from file system (TC-01)
- Visual rendering accuracy on `/evidence` and `/research/factor-lab` (TC-02, TC-03, TC-04, TC-09)
- Signal-less claim integrity (TC-05, TC-06)
- Frontend unit test coverage (TC-07)
- Backend determinism and no regression (TC-08)
- Existing journey regression guard (TC-10)
