# Goal Iteration 36 Functional Test Plan

**Phase:** goal-mcp-loop-iter-36 — Certifier calibration: referee placebo + lookahead-tripwire audit (J-22)  
**Date:** 2026-07-14  
**Frontend Present:** yes

## Phase Goal

Deliver `/research/referee-audit` — a read-only panel showing the certifier's measured empirical false-pass rate (with binomial confidence interval) vs. the configured α, plus a lookahead-contaminated-factor tripwire labeled "expected: rejected" — proving the certifier itself is calibrated and honest.

## Test Cases

### TC-01 — Backend: Seeded harness determinism

**Type:** api  
**Preconditions:** 
- Backend is running with config block `research.referee_audit` populated
- Seed value is fixed in config (e.g., `seed: 42`)
- The harness module `app/engine/referee_audit.py` exists and exports `build_referee_audit_report()`

**Steps:**
1. Call `build_referee_audit_report(seed=42, n_null_trials=20, contaminated_factor_horizon=5, price_data=<fixture>)`
2. Capture the returned report's empirical false-pass rate
3. Call the function again with identical parameters
4. Compare both reports' false-pass rates

**Expected outcome:** Both calls return byte-identical empirical false-pass rates (determinism proven).

**Pass criteria:** `report1.empirical_false_pass_rate == report2.empirical_false_pass_rate` and `report1.false_pass_count == report2.false_pass_count`

---

### TC-02 — Backend: Isolation — real ledgers untouched

**Type:** api  
**Preconditions:**
- Backend is running
- Real ledger files exist at paths configured in `research.referee_audit.report_path` and adjacent ledger paths
- Git working tree is clean (run `git status` to verify no uncommitted changes on state files)

**Steps:**
1. Record hash of `certified-claims.jsonl` via `git hash-object`
2. Record hash of `staging-ledger.jsonl` via `git hash-object`
3. Record hash of `pre-registrations.jsonl` via `git hash-object`
4. Run the seeded harness: `build_referee_audit_report(n_null_trials=200, seed=<configured>, ledger_path=<throwaway>)`
5. Recompute hashes of the three real files

**Expected outcome:** All three real state files remain byte-identical; only a throwaway ledger was created.

**Pass criteria:** 
- `git diff HEAD` shows EMPTY on `certified-claims.jsonl`, `staging-ledger.jsonl`, `pre-registrations.jsonl`
- `GET /api/evidence` still returns 0 PASS / 7 FAIL, byte-identical to pre-run state
- A distinct throwaway ledger file was written to the harness's isolated ledger path

---

### TC-03 — Backend: Lookahead-contaminated factor rejected

**Type:** api  
**Preconditions:**
- Backend is running
- Harness module exports `build_referee_audit_report()` with contaminated-factor generation logic

**Steps:**
1. Generate a contaminated factor where value = realized forward return at configured `contaminated_factor_horizon`
2. Call harness to run the referee (`certify_edge()` / `verify_edge()`) against this factor
3. Inspect the returned report's contaminated-factor verdict

**Expected outcome:** The contaminated factor is rejected by the referee (verdict = "expected: rejected").

**Pass criteria:** `report.contaminated_factor_verdict == "expected: rejected"` (or similar rejection signal)

---

### TC-04 — Backend: Binomial CI computation

**Type:** api  
**Preconditions:**
- Harness computes a binomial confidence interval vs. configured α
- Report includes CI bounds (lower, upper) and the observed false-pass rate

**Steps:**
1. Run harness with `n_null_trials=100, seed=99`, capture report
2. Manually compute a 95% binomial CI for observed false-pass count using scipy.stats or equivalent
3. Compare manual CI bounds to report's CI bounds

**Expected outcome:** CI bounds match the hand-computed interval (within floating-point tolerance).

**Pass criteria:** `abs(report.ci_lower - manual_ci_lower) < 1e-6 and abs(report.ci_upper - manual_ci_upper) < 1e-6`

---

### TC-05 — Backend: Endpoint serves fixture artifact verbatim

**Type:** api  
**Preconditions:**
- Endpoint `GET /api/research/referee-audit` exists and is wired in `main.py`
- A fixture artifact exists at the configured `report_path` with known fields

**Steps:**
1. Persist a fixture referee-audit report JSON at `report_path` with:
   - `n_null_trials: 25`
   - `empirical_false_pass_rate: 0.04`
   - `false_pass_count: 1`
   - `contaminated_factor_verdict: "expected: rejected"`
   - `run_date: "2026-07-14"`
   - `alpha: 0.05`
   - Run parameters (seed, horizon)
2. Call `GET /api/research/referee-audit`
3. Compare response JSON to persisted fixture

**Expected outcome:** Endpoint returns 200 with JSON matching fixture exactly (no recompute, no transformation).

**Pass criteria:** `response.status == 200 and response.json() == fixture_json` (byte-identical or deep-equal)

---

### TC-06 — Backend: Missing artifact returns honest empty state

**Type:** api  
**Preconditions:**
- The configured `report_path` does not exist or is empty
- Endpoint is running

**Steps:**
1. Delete the artifact file (if it exists)
2. Call `GET /api/research/referee-audit`
3. Inspect status code and response body

**Expected outcome:** Endpoint returns 200 with an empty/null snapshot (never a 500 error).

**Pass criteria:** `response.status == 200 and (response.json() is null or response.json() == {})`

---

### TC-07 — Backend: Unparseable artifact returns honest empty state

**Type:** api  
**Preconditions:**
- The artifact file exists but contains invalid JSON (e.g., truncated or malformed)

**Steps:**
1. Write corrupt JSON to the artifact file
2. Call `GET /api/research/referee-audit`

**Expected outcome:** Endpoint handles the parse error gracefully and returns 200 with empty/null (never 500).

**Pass criteria:** `response.status == 200 and (response.json() is null or response.json() == {})`

---

### TC-08 — Backend: CI variant with tiny synthetic fixture (determinism + speed)

**Type:** api  
**Preconditions:**
- CI variant config has `n_null_trials: 20` (or env override)
- A tiny synthetic price fixture (e.g., 100 rows) is available, NOT the full 30-year seed
- Module imports are verified to NOT include full seed imports

**Steps:**
1. Run harness with CI config: `build_referee_audit_report(n_null_trials=20, synthetic_fixture=tiny_fixture)`
2. Time the execution
3. Verify no full seed was loaded (check for absence of full-seed imports in module trace)

**Expected outcome:** Harness completes in <5 seconds; same seed reproducibly yields identical results.

**Pass criteria:** `execution_time < 5s and report_run_1.false_pass_count == report_run_2.false_pass_count`

---

### TC-09 — Frontend: Page renders at `/research/referee-audit`

**Type:** browser  
**Preconditions:**
- Frontend is running at configured URL (default http://localhost:3000)
- Backend is running
- A persisted referee-audit artifact exists (or honest-empty state is acceptable for this step)
- Force rebuild by confirming `.next/BUILD_ID` postdates the new page source

**Steps:**
1. Confirm `.next/BUILD_ID` timestamp is after the `page.tsx` creation time
2. Navigate to `http://localhost:3000/research/referee-audit`
3. Wait for page to fully load
4. Verify page is not a 404 or error boundary

**Expected outcome:** Page loads without errors; content area is visible (or honest-empty if artifact missing).

**Pass criteria:** HTTP 200 returned; page title or heading includes "Referee audit" or similar; no error boundary visible

---

### TC-10 — Frontend: All report fields displayed correctly

**Type:** browser  
**Preconditions:**
- Frontend is running
- Referee-audit artifact is persisted with known values:
  - `n_null_trials: 200`
  - `empirical_false_pass_rate: 0.05`
  - `false_pass_count: 10`
  - `contaminated_factor_verdict: "expected: rejected"`
  - `run_date: "2026-07-14"`
  - `alpha: 0.05`
  - CI bounds and run parameters (seed, horizon)

**Steps:**
1. Navigate to `/research/referee-audit`
2. Inspect DOM for each field:
   - Null-trial count: locate element with text "200" or "trials" or "n_null"
   - False-pass rate: locate "0.05" or "5%"
   - CI: locate CI notation like "[0.01, 0.12]" or similar
   - Configured α: locate "0.05" or "alpha"
   - Contaminated-factor verdict: locate "expected: rejected"
   - Run date: locate "2026-07-14"
   - Run parameters (seed, horizon): visible in a parameters section

**Expected outcome:** All fields are rendered and visible on the page.

**Pass criteria:** Each field is present in the DOM and readable by the user (not hidden, not truncated to empty)

---

### TC-11 — Frontend: Tripwire failure state (contaminated factor NOT rejected)

**Type:** browser  
**Preconditions:**
- Frontend is running
- A test artifact is created where contaminated factor is NOT rejected (verdict ≠ "expected: rejected")
- Artifact is persisted to the configured path

**Steps:**
1. Create and persist an artifact with `contaminated_factor_verdict: "not_rejected"` or blank
2. Navigate to `/research/referee-audit`
3. Inspect for a prominent red/warning styling or failure message

**Expected outcome:** A loud, unmissable red tripwire state appears (e.g., red border, danger-colored background, or explicit failure heading).

**Pass criteria:** CSS class includes "red"/"danger"/"warn" or similar; text includes "tripwire"/"failure"/"NOT caught" or equivalent; element is NOT hidden behind overflow or secondary styling

---

### TC-12 — Frontend: Navigation card links correctly

**Type:** browser  
**Preconditions:**
- Frontend is running
- User is on the `/research` hub page
- The 4th governance card has been added to the page source

**Steps:**
1. Navigate to `/research`
2. Locate the "Governance & process" grouping (should show Registry, Graveyard, Budget cards)
3. Verify the 4th card "Referee audit" is present
4. Inspect the card's link with `data-testid="research-governance-link-referee-audit"`
5. Click the card/link
6. Wait for navigation

**Expected outcome:** Navigation completes and `/research/referee-audit` page loads.

**Pass criteria:** URL changes to `http://localhost:3000/research/referee-audit` and page content loads (not 404)

---

### TC-13 — Frontend: Honest empty state (no artifact)

**Type:** browser  
**Preconditions:**
- Frontend is running
- Backend is running
- The artifact file is deleted or does not exist

**Steps:**
1. Ensure artifact is missing at `report_path`
2. Navigate to `/research/referee-audit`
3. Inspect for an empty-state message (e.g., "No audit report available" or similar)

**Expected outcome:** Page renders an honest, user-friendly empty state (not an error, not a blank white page).

**Pass criteria:** Page loads without errors; a message or placeholder indicates the artifact is unavailable (e.g., "Audit not yet run", "No data available")

---

### TC-14 — Frontend: Backend unavailable contained card

**Type:** browser  
**Preconditions:**
- Frontend is running
- Backend is stopped or unreachable

**Steps:**
1. Stop the backend service
2. Navigate to `/research/referee-audit`
3. Inspect for a contained error card (not a full-page error boundary)
4. Verify navigation to other pages still works (click nav link to `/research`)

**Expected outcome:** A contained "Backend unavailable" card appears; navigation remains intact.

**Pass criteria:** Error is shown in a card component (not a full-page error boundary); other nav links remain clickable and functional

---

### TC-15 — Frontend: Evidence badge remains unchanged (J-01 sanity check)

**Type:** browser  
**Preconditions:**
- Frontend is running
- Backend is running
- Navigate to `/stocks` or another score-display surface

**Steps:**
1. Navigate to `/stocks` leaderboard
2. Inspect evidence badges on score columns (should show "Proven" or "Not yet proven")
3. Note the current evidence status
4. Navigate away and back
5. Verify badges display consistently

**Expected outcome:** Evidence badges on `/stocks` are unchanged and display correctly (regression test for J-01).

**Pass criteria:** Badges are rendered; at least one badge is present on the leaderboard; no 500 errors; badge text is readable

---

### TC-16 — Integration: Null-factor generator preserves distribution

**Type:** api  
**Preconditions:**
- The null-factor generator in `referee_audit.py` is implemented
- A real factor's cross-section is available (loaded from committed seed)

**Steps:**
1. Load a real factor (e.g., `momentum_score`)
2. Generate null factors via permutation: `generate_null_factors(factor, n_trials=100, seed=42)`
3. Compute mean and stddev of real factor cross-section
4. Compute mean and stddev of generated null factors across all 100 trials
5. Compare distributions

**Expected outcome:** Null factors have approximately the same mean and stddev as the original (distribution preserved, signal killed).

**Pass criteria:** `abs(mean_null - mean_real) < 0.1 * mean_real` and similar for stddev

---

### TC-17 — Required-still-passing: J-01 (Evidence badges on scores)

**Type:** browser  
**Preconditions:**
- Frontend is running
- Backend is running
- J-01 was passing before this iteration

**Steps:**
1. Navigate to `/stocks`
2. Inspect leaderboard rows for evidence badges
3. Verify all displayed scores carry a badge
4. Click one badge to drill into evidence

**Expected outcome:** Evidence badges render correctly; drill-down works (or links to `/evidence` as before).

**Pass criteria:** All scores have badges; no new errors on the page; drill-down does not 404

---

### TC-18 — Required-still-passing: J-03 (Evidence ledger surface)

**Type:** browser  
**Preconditions:**
- Frontend is running
- Backend is running
- J-03 (`/evidence`) was passing before

**Steps:**
1. Navigate to `/evidence`
2. Inspect the ledger table (headers: Hypothesis, Verdict, Control, Claim ID, Date, etc.)
3. Verify at least one row is present (or honest empty if no claims yet)

**Expected outcome:** Ledger surface renders correctly; no regressions from the new referee-audit module.

**Pass criteria:** Page loads; table structure is intact; all columns present; no 500 errors

---

### TC-19 — Required-still-passing: J-05 (Regime-conditioned evidence)

**Type:** browser  
**Preconditions:**
- Frontend is running
- Backend is running
- J-05 (regime/phase conditioning) was passing before

**Steps:**
1. Navigate to a page showing regime-conditioned evidence (e.g., stock detail with regime badge)
2. Verify evidence badges reflect the current regime
3. Switch regime or change as-of date (if UI allows)
4. Verify evidence status updates accordingly

**Expected outcome:** Regime conditioning works as before; no regression.

**Pass criteria:** Evidence status matches the current regime; badges update on regime change; no errors

---

### TC-20 — Required-still-passing: J-11 (Honest uncertainty marking)

**Type:** browser  
**Preconditions:**
- Frontend is running
- Backend is running
- J-11 (thin/failed evidence markers) was passing before

**Steps:**
1. Navigate to a page showing a failed or unproven signal
2. Verify the badge reads "Not yet proven" or similar
3. Inspect for any "proven" language on unvalidated signals

**Expected outcome:** Failed signals are marked as unproven; no proven language on unvalidated claims.

**Pass criteria:** At least one "Not yet proven" badge present; no failed signals render as "proven"

---

### TC-21 — Required-still-passing: J-17 (Budget panel)

**Type:** browser  
**Preconditions:**
- Frontend is running
- Backend is running
- J-17 (budget panel at `/research/budget`) was passing before

**Steps:**
1. Navigate to `/research/budget`
2. Verify budget stats display (claims used, α budget remaining, divisor, etc.)

**Expected outcome:** Budget panel renders correctly; all stats match backend computation.

**Pass criteria:** Page loads; stats are displayed and match expected values; no errors

---

### TC-22 — Required-still-passing: J-18 (Registry surface)

**Type:** browser  
**Preconditions:**
- Frontend is running
- Backend is running
- J-18 (pre-registrations at `/research/registry`) was passing before

**Steps:**
1. Navigate to `/research/registry`
2. Verify registry table displays pre-registrations
3. Check that columns (ID, Hypothesis, Date, Status, etc.) are all present

**Expected outcome:** Registry surface unchanged; no regression.

**Pass criteria:** Page loads; table renders; all columns visible; at least one row present (or honest empty)

---

### TC-23 — Required-still-passing: J-19 (Graveyard surface)

**Type:** browser  
**Preconditions:**
- Frontend is running
- Backend is running
- J-19 (graveyard at `/research/graveyard`) was passing before

**Steps:**
1. Navigate to `/research/graveyard`
2. Verify graveyard table displays failed claims
3. Check table structure (Claim ID, Verdict, Date, etc.)

**Expected outcome:** Graveyard surface unchanged; no regression.

**Pass criteria:** Page loads; table renders; structure intact; no new errors

---

### TC-24 — Required-still-passing: J-20 (Preflight banner)

**Type:** browser  
**Preconditions:**
- Frontend is running
- Backend is running
- J-20 (preflight banner on new pages) was passing before

**Steps:**
1. Navigate to `/research/referee-audit`
2. Inspect for a preflight/integrity banner (e.g., "Data integrity check: ...")
3. Verify banner renders correctly on the new page

**Expected outcome:** Preflight banner appears on the new referee-audit page, consistent with other `/research/*` pages.

**Pass criteria:** Banner is visible; text is readable; no styling errors; banner is not duplicated

---

## Summary

**Total test cases:** 24  
**API tests:** 8 (TC-01 to TC-08)  
**Browser tests:** 16 (TC-09 to TC-24)  
**Artifact checks:** 0

### Test execution notes

- **Backend tests (TC-01 to TC-08):** Run backend test suite; these scenarios should be covered by `tests/test_referee_audit.py` and `tests/test_api_referee_audit.py`.
- **Browser tests (TC-09 to TC-24):** Execute using Chrome MCP; J-01, J-03, J-05, J-11, J-17, J-18, J-19, J-20 are regression checks to ensure existing journeys remain passing.
- **Isolation verification (TC-02):** Run after the full harness execution; this is the dominant failure mode and requires byte-identity proof.
- **Force rebuild check (TC-09):** Before trusting any "page missing" observation, verify `.next/BUILD_ID` postdates the new page source (iter-20/21/35 lesson).
