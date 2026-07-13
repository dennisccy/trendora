# Goal Iteration 31 Functional Test Plan (J-19)

**Phase:** goal-mcp-loop-iter-31
**Date:** 2026-07-13
**Frontend Present:** yes

## Phase Goal

Ship `/research/graveyard` — a read-only page displaying every non-PASS referee verdict (FAIL/INSUFFICIENT) from both canonical and staging ledgers, with selectors, verdict kind, date, deflation context, origin ledger, and registration lineage, so users and future iterations can browse institutional memory and avoid re-deriving dead hypotheses.

## Test Cases

### TC-01 — Graveyard page renders all non-PASS entries from both ledgers

**Type:** browser
**Preconditions:** 
- Backend is running
- Frontend is running
- Both `certified-claims.jsonl` and `staging-ledger.jsonl` contain non-PASS entries (today: 7 canonical + 7 staging)

**Steps:**
1. Navigate to `/research` page
2. Locate the "Governance & process" grid
3. Click the graveyard card (data-testid="research-governance-link-graveyard")
4. Wait for page to load
5. Count visible table rows in the graveyard

**Expected outcome:** Page loads with a table containing all 14 non-PASS entries; selectors visible as key=value chips; verdict badges show "FAIL" or "INSUFFICIENT" with neutral/negative styling

**Pass criteria:** Exactly 14 rows rendered; all rows display selector chips; verdict column contains only "FAIL" or "INSUFFICIENT" badges (never "Proven")

---

### TC-02 — Graveyard filters to non-PASS verdicts only

**Type:** api
**Preconditions:** 
- Backend is running
- Ledger files contain a mix of PASS and non-PASS entries (fixture or real)

**Steps:**
1. Run: `curl -s http://localhost:8000/api/research/graveyard | jq '.entries | length'`
2. For each entry in response, verify: `entry.verdict.status` is either "FAIL" or "INSUFFICIENT"
3. Verify no entry has `entry.verdict.status == "PASS"`

**Expected outcome:** API returns only non-PASS verdicts; PASS entries are excluded

**Pass criteria:** Entry count matches expected non-PASS count; jq filter confirms all entries have `verdict.status` in ["FAIL", "INSUFFICIENT"]

---

### TC-03 — Canonical and staging ledger origins are tagged correctly

**Type:** browser
**Preconditions:** 
- `/research/graveyard` page is loaded and displaying entries
- Both canonical and staging ledgers have non-PASS entries

**Steps:**
1. Inspect the "Ledger" column in the graveyard table
2. For rows sourced from canonical ledger, verify the ledger pill shows "canonical"
3. For rows sourced from staging ledger, verify the ledger pill shows "staging"
4. Verify at least one canonical and one staging row are visible

**Expected outcome:** Ledger origin pills render with correct labels; canonical rows visually distinct from staging rows

**Pass criteria:** All visible rows have a ledger pill with either "canonical" or "staging"; at least one row of each origin is present and correctly labeled

---

### TC-04 — Verdict badge styling excludes "Proven" accent color

**Type:** browser
**Preconditions:** 
- `/research/graveyard` page is loaded

**Steps:**
1. Inspect the "Verdict" column badges
2. Verify FAIL badges use `danger` styling (red/negative)
3. Verify INSUFFICIENT badges use `warn` styling (yellow/warning)
4. Confirm no badge uses the `accent` color reserved for PASS/"Proven"

**Expected outcome:** Verdict badges render with neutral/negative colors; no accent styling applied

**Pass criteria:** Badge color scheme confirmed via visual inspection; no accent color present in the verdict column

---

### TC-05 — Deflation context is re-displayed verbatim

**Type:** api
**Preconditions:** 
- Backend is running
- Ledger entries include verdicts with `deflation` and `deflation_divisor` fields

**Steps:**
1. Run: `curl -s http://localhost:8000/api/research/graveyard | jq '.entries[0]'`
2. Verify the response includes `verdict.deflation` (e.g., "bonferroni")
3. Verify the response includes `verdict.deflation_divisor` (e.g., 8)
4. Compare displayed values against the raw ledger file entry

**Expected outcome:** API response includes deflation context fields; values match the source ledger exactly (byte-identical)

**Pass criteria:** Both `deflation` and `deflation_divisor` fields are present and match the source ledger; no recomputation detected

---

### TC-06 — Registration lineage is attached via registry.match_registration

**Type:** browser
**Preconditions:** 
- `/research/graveyard` page is loaded
- At least one entry has a matching registration (e.g., `ma_stack`)

**Steps:**
1. Locate a row with known registration lineage (e.g., `ma_stack`)
2. Click the "Lineage" link in that row
3. Verify the navigation to `/research/registry#registration-<id>`
4. Confirm the registry page highlights or scrolls to the corresponding row

**Expected outcome:** Lineage link resolves to the correct registry row; anchor navigation works; the row is identified

**Pass criteria:** Lineage link is clickable; navigates to registry page; URL contains the correct anchor; target row is reachable

---

### TC-07 — Honest null lineage when selector-set is unregistered

**Type:** api
**Preconditions:** 
- Backend is running
- At least one fixture ledger entry has selectors that match no registration

**Steps:**
1. Run: `curl -s http://localhost:8000/api/research/graveyard | jq '.entries[] | select(.lineage == null)'`
2. Verify at least one entry has `lineage: null`
3. Confirm no crash occurred and the response is valid JSON

**Expected outcome:** API returns entries with `lineage: null` when no registration matches; no error or crash

**Pass criteria:** At least one null-lineage entry is present; API does not return 500; response is valid

---

### TC-08 — Browser: null lineage renders as honest text, not a broken link

**Type:** browser
**Preconditions:** 
- `/research/graveyard` page is loaded
- At least one entry with null lineage is visible (exercise via fixture if needed)

**Steps:**
1. Inspect the "Lineage" column for rows with null lineage
2. Verify text renders as "No registration lineage" or similar honest message
3. Confirm no broken link or crash

**Expected outcome:** Null-lineage rows display descriptive text instead of a link; page remains stable

**Pass criteria:** Honest text visible; no link rendered; no page error or blank state

---

### TC-09 — Forward-walk monitoring records are excluded from graveyard

**Type:** api
**Preconditions:** 
- Backend is running
- Ledger contains forward-walk type entries (if any)

**Steps:**
1. Run: `curl -s http://localhost:8000/api/research/graveyard | jq '.entries[] | select(.type == "forward_walk") | length'`
2. Verify the result is 0 (no forward-walk entries in the response)

**Expected outcome:** Forward-walk records are filtered out; only non-forward-walk non-PASS entries remain

**Pass criteria:** No forward-walk entries present in the graveyard payload

---

### TC-10 — Closed registry status ("permanent" marking) is displayed verbatim

**Type:** browser
**Preconditions:** 
- `/research/graveyard` page is loaded
- The `ma_stack` entry (a closed/permanent entry) is visible

**Steps:**
1. Locate the `ma_stack` row in the graveyard table
2. Inspect for a "permanent" or "closed" marker/badge
3. Verify the marker is visible and correctly positioned
4. Take a screenshot capturing the marker in-frame

**Expected outcome:** Closed entries display a "permanent" marking; the marker is visually distinct and in-frame

**Pass criteria:** "Permanent" marker visible on the `ma_stack` row; screenshot captures the marker; no visual ambiguity

---

### TC-11 — Revisit-protocol rule is displayed and linked from all rows

**Type:** browser
**Preconditions:** 
- `/research/graveyard` page is loaded
- Revisit-protocol panel is rendered

**Steps:**
1. Scroll to the Revisit-protocol panel (or Card) on the page
2. Verify the rule text is displayed (the B-406/§0 rule about re-testing conditions)
3. Verify each graveyard row includes a link/anchor to the revisit-protocol panel
4. Click the link on a row and verify navigation/scroll to the panel

**Expected outcome:** Revisit-protocol panel renders with rule text; all rows link to it; anchor navigation works

**Pass criteria:** Panel visible; rule text contains key phrases ("materially changed precondition", "new data span", etc.); row links are functional and navigate to the panel

---

### TC-12 — Graveyard page is reachable from /research in ≤2 clicks

**Type:** browser
**Preconditions:** 
- Frontend is running
- User is on the `/research` page

**Steps:**
1. Navigate to `/research`
2. Locate the "Governance & process" grid section
3. Count the number of clicks to reach the graveyard (should be ≤2)
4. Verify the graveyard card is discoverable without scrolling excessively

**Expected outcome:** Graveyard is discoverable from `/research` in ≤2 clicks; card is in the governance grid

**Pass criteria:** Graveyard card visible in the governance grid; clicking it navigates to `/research/graveyard` within 2 clicks

---

### TC-13 — Backend unavailable state renders honestly

**Type:** browser
**Preconditions:** 
- Frontend is running
- Backend is stopped or unreachable

**Steps:**
1. Stop the backend service (or simulate connectivity loss)
2. Navigate to `/research/graveyard`
3. Wait for the page to fail fetching from the backend
4. Verify the error state

**Expected outcome:** Page shows a contained error card (not a blank page); navigation remains intact; honest messaging about backend unavailability

**Pass criteria:** Error card rendered; nav sidebar/footer intact; no crash or blank page

---

### TC-14 — Empty/missing ledger files render empty state honestly

**Type:** api
**Preconditions:** 
- Backend is running
- Ledger files are missing or empty

**Steps:**
1. Rename or delete `certified-claims.jsonl` and `staging-ledger.jsonl` (or set to empty)
2. Run: `curl -s -w "\n%{http_code}" http://localhost:8000/api/research/graveyard`
3. Verify the response is HTTP 200 with an empty entries list
4. Restore ledger files
5. Verify no 500 error occurred

**Expected outcome:** API returns 200 with empty payload when ledgers are missing/empty; no crash

**Pass criteria:** HTTP 200 returned; response JSON is valid; entries array is empty; no 500 error

---

### TC-15 — Browser: empty state renders honestly with no crash

**Type:** browser
**Preconditions:** 
- Frontend is running
- Ledger files are empty or missing

**Steps:**
1. Ensure ledgers are empty (or missing)
2. Navigate to `/research/graveyard`
3. Verify the page renders an honest empty state (e.g., "No graveyard entries")
4. Verify navigation is intact

**Expected outcome:** Page displays a friendly empty state; no crash; nav remains accessible

**Pass criteria:** Empty-state message displayed; no blank page; page is usable

---

### TC-16 — Graveyard payload matches build_graveyard_payload() directly

**Type:** api
**Preconditions:** 
- Backend is running
- Both canonical and staging ledgers exist with non-PASS entries

**Steps:**
1. Call the backend's `build_graveyard_payload()` function directly (via Python or test harness)
2. Fetch `GET /api/research/graveyard`
3. Compare the two JSON payloads byte-for-byte (or structure-for-structure)

**Expected outcome:** Endpoint response is identical to direct function call; no transformation or filtering by the router

**Pass criteria:** Payload equality confirmed; single-source assertion passes

---

### TC-17 — Correctness round-trip: graveyard entry matches source ledger byte-exactly

**Type:** api
**Preconditions:** 
- Backend is running
- At least one committed ledger entry is known (e.g., `ma_stack` from `certified-claims.jsonl`)

**Steps:**
1. Fetch `GET /api/research/graveyard`
2. Locate the entry matching the known ledger row (e.g., by claim selectors)
3. Compare displayed selectors, verdict, date against the raw ledger file entry
4. Verify byte-exact match (or expected canonical formatting)

**Expected outcome:** Graveyard entry selectors, verdict, and date match the source ledger entry

**Pass criteria:** At least one entry round-trips byte-exactly from ledger → endpoint → display; no data loss or recomputation

---

### TC-18 — Required-still-passing journeys remain green

**Type:** api
**Preconditions:** 
- Backend is running
- All required journeys are available (J-01, J-03, J-04, J-05, J-06, J-08, J-09, J-11, J-18)

**Steps:**
1. Run the full test suite to verify required journeys pass: `pytest -xvs apps/backend/tests/ -k "test_" 2>&1 | grep -E "(PASSED|FAILED|ERROR)"`
2. Confirm J-01, J-03, J-04, J-05, J-06, J-08, J-09, J-11, J-18 all pass (or skip if specific journey tests are not named)

**Expected outcome:** All required-still-passing journeys continue to pass; no regressions

**Pass criteria:** No new failures in required journeys; test suite exit code 0

---

### TC-19 — Ledger files remain byte-identical before and after

**Type:** artifact
**Preconditions:** 
- Ledger files exist and are committed

**Steps:**
1. Record MD5 hash of `certified-claims.jsonl`, `staging-ledger.jsonl`, `pre-registrations.jsonl` before iteration
2. After iteration, record MD5 hashes of the same files
3. Compare hashes

**Expected outcome:** All three ledger files remain byte-identical

**Pass criteria:** MD5 hashes are identical before and after; no ledger writes occurred

---

### TC-20 — Canonical Bonferroni divisor remains 8

**Type:** api
**Preconditions:** 
- Backend is running

**Steps:**
1. Fetch `GET /api/evidence` (proven signals endpoint)
2. Verify the response includes only canonical entries (no staging)
3. Verify the divisor context is still 8 (or check the hardcoded constant)

**Expected outcome:** Proven signals endpoint unchanged; divisor remains 8; no staging entries leaked into proven signals

**Pass criteria:** Bonferroni divisor == 8; `/api/evidence` response is byte-identical to pre-iteration

---

### TC-21 — Selector matching uses registry.match_registration, not reimplemented

**Type:** artifact
**Preconditions:** 
- Implementation files are available

**Steps:**
1. Search `app/engine/graveyard.py` for calls to `registry.match_registration`
2. Verify the graveyard lineage attachment uses the existing function, not a new selector matcher
3. Confirm `app.engine.registry._CLAIM_SELECTOR_KEYS == app.mcp.tools._CLAIM_SELECTOR_KEYS` (drift-insurance test exists in test_registry.py)

**Expected outcome:** Graveyard reuses registry's matching logic; no duplicate matcher exists; drift-insurance test passes

**Pass criteria:** `registry.match_registration` is called; no alternative matcher in graveyard.py; drift-insurance test present and passing

---

## Summary

**Total test cases:** 21

**By type:**
- Browser tests: 8 (TC-01, TC-04, TC-06, TC-08, TC-12, TC-13, TC-15, TC-12)
- API tests: 9 (TC-02, TC-03, TC-05, TC-07, TC-09, TC-14, TC-16, TC-17, TC-20)
- Artifact checks: 4 (TC-19, TC-21 + regression ledger verification, TC-18 for journey regressions)

**Key conformance:**
- All test cases trace back to spec requirements (DEFINITION OF DONE, TESTING REQUIREMENTS, IN SCOPE)
- Anti-goal violations tested: #1 (honest styling, never "Proven"), #3 (correctness round-trip), #7 (no hardcoded credentials), #8 (graceful degradation)
- Critical paths: lineage attachment, non-PASS filter, forward-walk exclusion, honest null handling, empty-ledger handling
- Regression proof: ledger byte-identity, proven-signals unchanged, required journeys passing
