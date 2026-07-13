# Goal Iteration 30 Functional Test Plan

**Phase:** goal-mcp-loop-iter-30
**Date:** 2026-07-13
**Frontend Present:** yes

## Phase Goal

Ship the pre-registration registry (J-18): a `/research/registry` page listing every registered hypothesis, and the post-decompose gate enforcing that only pre-registered claims reach the referee, making ad-hoc data mining structurally impossible.

## Test Cases

### TC-01 — Registry page renders with all backfilled rows

**Type:** browser
**Preconditions:** Backend running, registry file populated with 11 backfilled rows, frontend running in prod mode

**Steps:**
1. Navigate to `http://localhost:3000/research`
2. Locate and click the "Governance & process" card/link pointing to `/research/registry`
3. Wait for the registry page to load
4. Inspect the table for all visible columns

**Expected outcome:** The registry page loads; a table displays rows with selectors, rationale, registration date, source, and status columns; all 11 backfilled hypotheses are visible.

**Pass criteria:** Table renders, 11 rows present, each row contains all expected columns (selectors, rationale, registration_date, source, status), no validation/error messages.

---

### TC-02 — Registry page labels backfilled rows visibly

**Type:** browser
**Preconditions:** Registry page loaded (TC-01 pass)

**Steps:**
1. On `/research/registry`, scan the status column for all rows
2. Identify any row with `status: "tested"` or `status: "closed"` (backfilled rows)
3. Verify the visual presentation (e.g., a badge or label marking it as historical)

**Expected outcome:** Backfilled rows are visibly distinguished from any new registrations (historical backfills clearly labeled).

**Pass criteria:** At least one row renders a visual indicator (e.g., "backfill" pill, muted styling, or explicit label) differentiating it from fresh registrations.

---

### TC-03 — Registry is discoverable from Research hub in ≤2 clicks

**Type:** browser
**Preconditions:** Frontend running, user on `/research` hub page

**Steps:**
1. Navigate to `http://localhost:3000/research`
2. Scan the page for a navigation link to the registry
3. Count the number of clicks required to reach `/research/registry`

**Expected outcome:** A single link/card on the Research hub clearly points to `/research/registry`.

**Pass criteria:** The registry is reachable in exactly 1 click from `/research`; no more than 2 clicks total.

---

### TC-04 — Registry page handles missing/empty registry file gracefully

**Type:** api
**Preconditions:** Registry loader configured to a non-existent file path

**Steps:**
1. Temporarily rename or delete `runs/goal-session-mcp-loop/state/pre-registrations.jsonl`
2. Call `curl -s http://localhost:8000/api/research/registry | jq '.'`
3. Frontend browser test: navigate to `/research/registry`

**Expected outcome:** API returns HTTP 200 with an empty list `[]`; frontend shows an honest empty state (e.g., "No registrations yet"), no crash or 500 error.

**Pass criteria:** HTTP 200, response body is valid JSON array, frontend does not throw an unhandled error boundary.

---

### TC-05 — Registered exact-match claim proceeds to referee

**Type:** api
**Preconditions:** Registry populated, `evidence.registry.enforce: true`, gate script accessible

**Steps:**
1. Construct a claim JSON object whose selectors exactly match a known registry row (e.g., vcp_contraction decile 10, horizon 20, direction positive)
2. Call the gate via `python3 project-extensions/gates/verify_claim.py` (or equivalent test harness) with `enforce=true`
3. Inspect the output for a "proceed" or "PASS_GATE" verdict
4. Assert that `verify_edge` was invoked (via spy/monkeypatch in test)

**Expected outcome:** The claim passes the registry cross-check; `verify_edge` is called; no BLOCKED result returned.

**Pass criteria:** Gate exits with code 0 (or verdict is "proceed"); `verify_edge` called exactly once for that claim; ledger file unchanged before/after.

---

### TC-06 — Unregistered claim refused BEFORE referee computation

**Type:** api
**Preconditions:** Registry populated with known rows, `evidence.registry.enforce: true`, test harness for gate script

**Steps:**
1. Construct a claim JSON object whose selectors do NOT match any registry row (e.g., a fabricated factor name or decile)
2. Call the gate script with the unregistered claim and `enforce=true`
3. Inspect the output for a BLOCKED result and check that `verify_edge` was NOT called
4. Verify the ledger file is byte-identical before/after (no write occurred)

**Expected outcome:** The claim is rejected before the referee runs; `verify_edge` is not invoked; ledger unchanged; error message names the registry requirement.

**Pass criteria:** Gate output includes a result with `"status":"BLOCKED"` and a message mentioning "registry"; `verify_edge` not called; ledger byte-identical; exit code 3 (or equivalent error code).

---

### TC-07 — Near-miss claim (one selector differs) is refused

**Type:** api
**Preconditions:** Registry contains a known row (e.g., vcp_contraction d10 h20), `enforce: true`

**Steps:**
1. Construct a claim matching that row but with ONE selector changed (e.g., decile 10 → 9, or horizon 20 → 21)
2. Call the gate with the near-miss claim
3. Assert the result is BLOCKED and `verify_edge` not called

**Expected outcome:** The claim is refused because the selector-set does not exactly match; this proves matching is exact, not fuzzy/superset-based.

**Pass criteria:** Gate returns BLOCKED result; `verify_edge` not called; error message present; exit code 3.

---

### TC-08 — Enforcement OFF preserves pre-iter-30 behavior

**Type:** api
**Preconditions:** Registry file present, `evidence.registry.enforce: false` in config

**Steps:**
1. Construct an unregistered claim
2. Call the gate with `enforce=false`
3. Verify the claim proceeds to `verify_edge` (is not blocked)

**Expected outcome:** With enforcement disabled, the gate acts as it did before iter-30; unregistered claims do not trigger a BLOCKED result.

**Pass criteria:** Claim proceeds past the registry check (reaches `verify_edge`); no BLOCKED result; gate behaves identically to pre-iter-30 when enforce is false.

---

### TC-09 — Endpoint and loader single-source assertion

**Type:** api
**Preconditions:** Registry file with 11 backfilled rows, backend running

**Steps:**
1. Call `curl -s http://localhost:8000/api/research/registry | jq '.' > /tmp/endpoint-output.json`
2. In a test script, import `app.engine.registry` and call `load_registrations()` directly, dump to JSON
3. Byte-compare the two outputs

**Expected outcome:** The endpoint response and the loader output are identical (same rows, same order, same field values).

**Pass criteria:** `diff endpoint-output.json loader-output.json` produces no differences; both contain all 11 rows with matching field values.

---

### TC-10 — Registry loader handles missing file without crash

**Type:** api
**Preconditions:** Test harness can invoke loader module directly

**Steps:**
1. Configure the loader to a non-existent file path (e.g., `/tmp/nonexistent.jsonl`)
2. Call `load_registrations()` directly
3. Inspect the return value

**Expected outcome:** The loader returns an empty list `[]`, not an exception or None.

**Pass criteria:** Return value is an empty list; no exception raised; no crash or error log entry.

---

### TC-11 — Registry page shows honest loading and error states

**Type:** browser
**Preconditions:** Frontend running

**Steps:**
1. Open the browser DevTools Network tab
2. Throttle the network to "Slow 3G" or manually pause the fetch
3. Navigate to `/research/registry`
4. Observe the loading state briefly, then resume network
5. (Alternate step) Kill the backend temporarily, navigate to `/research/registry`, observe error state

**Expected outcome:** Page shows a loading skeleton/spinner while fetching; if backend is unreachable, shows an error card with a helpful message (not a blank page or unhandled error boundary).

**Pass criteria:** Loading state is rendered briefly; error state is user-friendly (e.g., "Unable to load registry — try refreshing"); no unhandled error thrown to browser console.

---

### TC-12 — No proven-language appears on registry page

**Type:** browser
**Preconditions:** Registry page loaded and populated

**Steps:**
1. On `/research/registry`, use browser DevTools to search page text for keywords: "proven", "evidence", "passed", "certified", "beat"
2. Inspect the status column specifically; ensure statuses are descriptive (e.g., "registered", "tested", "closed")

**Expected outcome:** No proven/confidence language anywhere on the page; status values are process-state descriptors, never outcomes.

**Pass criteria:** No match of proven-language keywords; status badges display only "registered", "tested", or "closed" (or equivalent neutral terms); no numeric edges or "passed/failed" verdicts shown.

---

### TC-13 — Backfill verification: loader ↔ endpoint round-trip

**Type:** api
**Preconditions:** Registry backfill complete with 11 rows

**Steps:**
1. For each of the 11 backfilled rows, fetch via endpoint: `GET /api/research/registry`
2. For each row in the registry, construct the claim selectors (kind + factor/event/regime + decile/horizon/direction + horizon + direction)
3. Call `match_registration(claim)` for each constructed claim
4. Assert each returns exactly one matching row with byte-identical content

**Expected outcome:** Every backfilled row round-trips through the loader's exact-match logic without loss.

**Pass criteria:** All 11 rows match; no row returns None; each match's content byte-matches the endpoint response for that row.

---

### TC-14 — Registry status vocabulary is consistent (no proven language)

**Type:** artifact
**Preconditions:** `runs/goal-session-mcp-loop/state/pre-registrations.jsonl` populated

**Steps:**
1. Read the registry file: `cat runs/goal-session-mcp-loop/state/pre-registrations.jsonl | jq '.status'`
2. Collect all unique status values
3. Verify each is in the approved vocabulary

**Expected outcome:** All status values are one of: "registered", "tested", "closed" (or other process-neutral terms specified in the spec).

**Pass criteria:** No row contains status values like "passed", "proven", "failed", "certified", or any proven-language keyword.

---

### TC-15 — Both ledgers byte-identical before/after iteration

**Type:** artifact
**Preconditions:** Iteration complete

**Steps:**
1. Before iteration start: `sha256sum runs/goal-session-mcp-loop/state/certified-claims.jsonl runs/goal-session-mcp-loop/state/staging-ledger.jsonl > /tmp/ledger-sums-before.txt`
2. After iteration complete: `sha256sum runs/goal-session-mcp-loop/state/certified-claims.jsonl runs/goal-session-mcp-loop/state/staging-ledger.jsonl > /tmp/ledger-sums-after.txt`
3. Compare: `diff /tmp/ledger-sums-before.txt /tmp/ledger-sums-after.txt`

**Expected outcome:** No differences; both ledgers unchanged.

**Pass criteria:** `diff` output is empty; file checksums match exactly before and after.

---

## Summary

**Total test cases:** 15
- **Browser tests:** 4 (TC-01, TC-02, TC-03, TC-11, TC-12)
- **API tests:** 10 (TC-04, TC-05, TC-06, TC-07, TC-08, TC-09, TC-10, TC-13)
- **Artifact checks:** 2 (TC-14, TC-15)

**Key Coverage:**
- Registry page rendering and discoverability ✓
- Graceful empty/error handling ✓
- Gate enforcement (registered/unregistered/near-miss/enforce-off) ✓
- Single-source assertion (loader ↔ endpoint) ✓
- No proven-language pollution ✓
- Ledger byte-identity (regression guard) ✓
