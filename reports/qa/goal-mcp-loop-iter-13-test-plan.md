# goal-mcp-loop-iter-13 Functional Test Plan

**Phase:** goal-mcp-loop-iter-13  
**Date:** 2026-07-01  
**Frontend Present:** yes

## Phase Goal

Surface J-08 (the terminal Must-have journey): promote the pre-registered 2-factor combination (`rs_spy_3m:top:quintile` × `high_proximity:top:tertile`) certified by the referee to the canonical evidence ledger. Render a "Proven" badge on the Multi-factor combination lab composite cohort and add a new claim row to `/evidence`, both reading the same `GET /api/evidence` payload. Verify the existing J-01..J-07 journeys remain non-regressed.

---

## Test Cases

### TC-01 — Backend: GET /api/evidence includes the 6th canonical combination entry

**Type:** api  
**Preconditions:** Backend is running; `certified-claims.jsonl` has 6 entries with row 6 being the combination PASS (iter-12 gate output already on disk).

**Steps:**
1. Run: `curl -s http://localhost:8000/api/evidence | jq '.claims[] | select(.kind == "combination")'`
2. Verify the response contains exactly one entry with `kind: "combination"`, `cohort: "composite"`, `condition: ["rs_spy_3m:top:quintile", "high_proximity:top:tertile"]`, `horizon: 20`, `direction: "positive"`.
3. Verify the entry has `verdict: {status: "PASS", holdout_edge: 0.04693, control_excess: 0.04693, p_value: 0.0009995002498750624}`.
4. Verify the entry has `signal: null` (signal-less claim).
5. Verify the entry has `proven: true`.

**Expected outcome:** The combination claim is served verbatim from the ledger with the correct verdict and no signal key.  
**Pass criteria:** Response contains exactly one combination entry with `signal: null`, `proven: true`, `p_value ≈ 0.0009995`, `holdout_edge ≈ 0.04693`, and no changes to the prior 5 canonical rows.

---

### TC-02 — Backend: proven_signals excludes the combination claim

**Type:** api  
**Preconditions:** Backend is running; `GET /api/evidence` endpoint is responding.

**Steps:**
1. Run: `curl -s http://localhost:8000/api/evidence | jq '.proven_signals'`
2. Verify the result is an object with a single key: `leadership_score`.
3. Verify no `combination` key exists in `proven_signals`.

**Expected outcome:** The combination claim does not light any inline `/stocks` badge; only `leadership_score` remains in `proven_signals`.  
**Pass criteria:** `proven_signals === {leadership_score: <value>}` (exact byte-match, no new keys).

---

### TC-03 — Frontend: CombinationCohort type extraction and validation

**Type:** artifact  
**Preconditions:** Frontend TypeScript compiles without errors.

**Steps:**
1. Check file: `/home/dennis-chan/Git/trendora/apps/frontend/lib/evidence.ts`
2. Verify it exports a `CombinationCohort` type with fields: `kind: "combination"`, `cohort: "composite"`, `condition: string[]`, `horizon: number`, `direction: string`.
3. Verify it exports a `combinationCohortFromClaim(claim)` function that extracts a claim into a `CombinationCohort` or returns `null` for non-combination claims.
4. Verify `combinationCohortFromClaim` rejects claims with `kind !== "combination"`, `cohort !== "composite"`, or invalid field types.

**Expected outcome:** The type and extractor are present and correctly validate combination claims.  
**Pass criteria:** File contains `CombinationCohort` type definition, `combinationCohortFromClaim` function present, TypeScript compilation succeeds.

---

### TC-04 — Frontend: resolveCombinationEvidence returns "Proven" for the certified cohort

**Type:** artifact  
**Preconditions:** Frontend TypeScript compiles; the certified claim is available from `GET /api/evidence`.

**Steps:**
1. Check file: `/home/dennis-chan/Git/trendora/apps/frontend/lib/evidence.ts`
2. Verify it exports `resolveCombinationEvidence(cohort, claims)` function.
3. Create a test cohort: `{kind: "combination", cohort: "composite", condition: ["rs_spy_3m:top:quintile", "high_proximity:top:tertile"], horizon: 20, direction: "positive"}`.
4. Call `resolveCombinationEvidence(testCohort, <served claims array>)`.
5. Verify the result is `{proven: true, label: "Proven", href: "/evidence#combination-high_proximity-rs_spy_3m-h20", claim: <the combination entry>}`.
6. Verify the anchor ID is deterministic and distinct from any `factor-…` anchor (starts with `combination-`).

**Expected outcome:** The matcher correctly identifies the certified cohort and returns the proper proven status with a deep-link anchor.  
**Pass criteria:** `proven === true`, `label === "Proven"`, `href` contains a valid `/evidence#combination-…` anchor, `claim.p_value ≈ 0.0009995`.

---

### TC-05 — Frontend: resolveCombinationEvidence returns "Not yet proven" for non-matching combinations

**Type:** artifact  
**Preconditions:** Frontend TypeScript compiles; the certified claim is available.

**Steps:**
1. Create a test cohort with different legs: `{kind: "combination", cohort: "composite", condition: ["rs_spy_3m:top:quintile", "atr_pct:bottom:tertile"], horizon: 20, direction: "positive"}`.
2. Call `resolveCombinationEvidence(testCohort, <served claims array>)`.
3. Verify the result is `{proven: false, label: "Not yet proven", href: null, claim: null}`.
4. Repeat with a different horizon (e.g., h60) and verify "Not yet proven" again.
5. Repeat with reversed condition legs (order-independence test): `{..., condition: ["high_proximity:top:tertile", "rs_spy_3m:top:quintile"], ...}` and verify "Proven" (order does not matter for leg matching).

**Expected outcome:** Non-certified combinations resolve to "Not yet proven"; certified combinations resolve to "Proven" regardless of leg order.  
**Pass criteria:** Non-matching horizon/legs → `proven: false`; same cohort with legs in different order → `proven: true`.

---

### TC-06 — Frontend: claimAnchorId returns combination anchor for combination claims

**Type:** artifact  
**Preconditions:** Frontend TypeScript compiles; `lib/evidence.ts` is updated.

**Steps:**
1. Check file: `/home/dennis-chan/Git/trendora/apps/frontend/lib/evidence.ts`
2. Verify `claimAnchorId` function handles combination claims and returns a deterministic anchor.
3. Call `claimAnchorId(<combination claim from certified-claims.jsonl>)`.
4. Verify the returned anchor matches the format `combination-high_proximity-rs_spy_3m-h20` (sorted legs, prefix `combination-`, h-notation for horizon).
5. Call it twice and verify the result is identical (determinism).
6. Verify no collision with factor anchors (they use `factor-…` prefix).

**Expected outcome:** Combination claims get a unique, deterministic, order-independent anchor.  
**Pass criteria:** Anchor format `combination-<leg1>-<leg2>-h<horizon>` (legs sorted alphabetically), identical on repeated calls, distinct from `factor-…` anchors.

---

### TC-07 — Frontend: claimSurface combination branch provides honest title and linkback

**Type:** artifact  
**Preconditions:** Frontend TypeScript compiles; `lib/evidence.ts` is updated.

**Steps:**
1. Check file: `/home/dennis-chan/Git/trendora/apps/frontend/lib/evidence.ts`
2. Verify `claimSurface` function has a `combination` branch.
3. Call `claimSurface(<combination claim>)`.
4. Verify the result includes:
   - `title`: an honest composite title naming both factors (e.g., "RS Leaders × Near 52-week High" or similar, NOT "Unmapped signal").
   - `subtitle`: a historical-evidence subtitle (NOT a return promise, price target, or buy-sell signal).
   - `href: "/research/factor-combination"` (links to the combination lab).
   - `label: "Multi-factor combination lab"` (replacing the fallback).
5. Verify the combination branch does NOT generate a `signal` key.

**Expected outcome:** The combination claim surfaces with honest language and correct linkage to the combination lab.  
**Pass criteria:** `title` is present and descriptive (no "Unmapped signal"); `href` is "/research/factor-combination"; no `signal` key present.

---

### TC-08 — Frontend unit tests: lib/evidence.test.ts covers combination paths

**Type:** artifact  
**Preconditions:** Frontend test suite exists and compiles.

**Steps:**
1. Check file: `/home/dennis-chan/Git/trendora/apps/frontend/lib/evidence.test.ts`
2. Verify new test cases cover:
   - `resolveCombinationEvidence` with the certified cohort → "Proven" + correct anchor.
   - `resolveCombinationEvidence` with order-reversed legs → "Proven" (order-independence).
   - `resolveCombinationEvidence` with non-matching cohort → "Not yet proven".
   - `resolveCombinationEvidence` with matched-but-non-PASS entry → "Not yet proven".
   - `resolveCombinationEvidence` with empty/null/undefined claims list → "Not yet proven".
   - `combinationCohortFromClaim` extracts the certified claim correctly.
   - `combinationCohortFromClaim` rejects factor/event-study/malformed claims.
   - `claimAnchorId` returns the combination anchor (deterministic, distinct from `factor-…`).
   - `claimSurface` combination branch → honest title + `/research/factor-combination` linkback + correct anchor.
3. Run frontend tests: `cd apps/frontend && npm test -- --testPathPattern=evidence --coverage`
4. Verify all new tests pass and existing factor/event-study/score tests are NOT regressed.

**Expected outcome:** New combination test coverage added; all tests pass; no regressions in existing evidence logic.  
**Pass criteria:** Test suite passes; coverage includes all combination matchers; existing evidence tests unchanged and passing.

---

### TC-09 — Frontend: Multi-factor combination lab composite badge fetches evidence

**Type:** browser  
**Preconditions:** Frontend is running at http://localhost:3000; backend is running at http://localhost:8000; `GET /api/evidence` returns the 6-entry payload.

**Steps:**
1. Navigate to `http://localhost:3000/research/factor-combination`.
2. Verify the page loads without errors.
3. Use Chrome MCP to inspect the network: confirm a fetch to `GET /api/evidence` occurs (or was cached from a prior page load).
4. Verify the response in browser DevTools contains the combination claim with `proven: true`.
5. Confirm the `CombinationTable` renders with the `data-testid="combination-row-composite"` element present.

**Expected outcome:** The combination lab successfully fetches the evidence payload.  
**Pass criteria:** Network tab shows `GET /api/evidence` 200 OK; response body includes the combination entry with `proven: true`; composite row element is present.

---

### TC-10 — Frontend: Multi-factor combination lab shows "Proven" for the certified selection

**Type:** browser  
**Preconditions:** Frontend is running; backend is running; `GET /api/evidence` includes the certified combination entry.

**Steps:**
1. Navigate to `http://localhost:3000/research/factor-combination`.
2. The default combination is `rs_spy_3m × atr_pct` (a FAILED anchor pair at h60). Verify the composite cohort badge reads **"Not yet proven"** (honest default).
3. Change Leg 1 to `rs_spy_3m` (top quintile, h-unchanged).
4. Change Leg 2 to `high_proximity` (top tertile).
5. Verify the horizon is set to **20**.
6. **Scroll the composite row into the viewport** (critical: iter-3/iter-11 lesson).
7. Capture a screenshot: `reports/qa/goal-mcp-loop-iter-13-evidence/TC-10-proven-badge.png`.
8. Verify the badge now reads **"Proven"** and has a deep link: `href="/evidence#combination-high_proximity-rs_spy_3m-h20"`.
9. Click the badge to navigate to `/evidence`.
10. Verify you land on the `/evidence#combination-high_proximity-rs_spy_3m-h20` anchor (smooth scroll to the combination row).

**Expected outcome:** When the user composes the certified combination, the badge flips to "Proven" and deep-links to the `/evidence` row.  
**Pass criteria:** Badge text is "Proven"; `href` matches the deep-link anchor; click navigates to `/evidence` and scrolls to the combination row; screenshot is MD5-distinct from the "Not yet proven" state.

---

### TC-11 — Frontend: Multi-factor combination lab shows "Not yet proven" for other combinations

**Type:** browser  
**Preconditions:** Frontend is running; backend is running; the user just verified TC-10 (Proven state).

**Steps:**
1. Navigate to `http://localhost:3000/research/factor-combination`.
2. Compose a different 2-factor combination (e.g., `rs_spy_3m × vcp_contraction` at h20, or the default `rs_spy_3m × atr_pct` at h60).
3. **Scroll the composite row into the viewport**.
4. Capture a screenshot: `reports/qa/goal-mcp-loop-iter-13-evidence/TC-11-not-yet-proven-badge.png`.
5. Verify the badge reads **"Not yet proven"** with NO deep link (href is null).

**Expected outcome:** All combinations except the certified one show "Not yet proven" with no link.  
**Pass criteria:** Badge text is "Not yet proven"; `href` is null or undefined; screenshot is MD5-distinct from TC-10's "Proven" screenshot.

---

### TC-12 — Frontend: /evidence page displays the combination claim row

**Type:** browser  
**Preconditions:** Frontend is running; backend is running; `GET /api/evidence` includes the certified combination entry.

**Steps:**
1. Navigate to `http://localhost:3000/evidence`.
2. Verify the page renders 6 claim rows (5 prior + 1 new combination).
3. Identify the combination row (the row with `kind=combination` and `cohort=composite` chips).
4. **Scroll the combination row into the viewport** (critical).
5. Capture a screenshot: `reports/qa/goal-mcp-loop-iter-13-evidence/TC-12-evidence-row.png`.
6. Verify the row displays:
   - **Hypothesis chips:** `kind: combination`, `cohort: composite`, `condition: [rs_spy_3m:top:quintile, high_proximity:top:tertile]`, `horizon: 20`, `direction: positive`.
   - **Verdict:** "PASS" or "✓" badge.
   - **Holdout edge:** "+4.69%" (matches `certified-claims.jsonl` row 6).
   - **Control vs SPY:** "+4.69%" (matches control_excess).
   - **Registration date:** "2026-07-01" (or the gate-written date from row 6).
   - **Forward-walk score:** "Pending" or similar (from row 6's forward-walk field).
   - **Linkback:** "Backs: Multi-factor combination lab →" (with an `href="/research/factor-combination"`).
7. Click the linkback to navigate to `/research/factor-combination`.
8. Verify you land on the combination lab page.
9. Verify the composite cohort is selected with the certified legs (`rs_spy_3m × high_proximity` at h20) and the badge reads "Proven".

**Expected outcome:** The combination row renders with verbatim ledger data and a correct back-link to the combination lab.  
**Pass criteria:** All 6 rows present; combination row displays correct hypothesis + verdict + edge + control + registration date + "Backs: Multi-factor combination lab →" linkback; linkback is clickable and navigates to the combination lab with the badge set to "Proven"; screenshot is MD5-distinct from other evidence rows.

---

### TC-13 — Regression: /stocks inline badges unchanged

**Type:** browser  
**Preconditions:** Frontend is running; backend is running.

**Steps:**
1. Navigate to `http://localhost:3000/stocks`.
2. Identify the first stock's inline leadership score badge (e.g., "Leadership Score: Proven").
3. Verify **NO new combination badge** appears on the page (no `/stocks` inline badge for the signal-less combination claim).
4. Scroll and verify Entry Quality and Risk badges still show "Not yet proven".
5. Capture a screenshot: `reports/qa/goal-mcp-loop-iter-13-evidence/TC-13-stocks-no-combo.png`.
6. Navigate to a stock page (e.g., `http://localhost:3000/stocks/SPY`).
7. Verify the same badge set (Leadership Proven, Entry Quality and Risk Not yet proven).
8. Verify NO new combination badge inline.

**Expected outcome:** The combination claim does not light any inline `/stocks` or `/stocks/{ticker}` badge (signal-less design preserved).  
**Pass criteria:** Leadership "Proven"; Entry Quality and Risk "Not yet proven"; NO new combination badge; `proven_signals` still `{leadership_score}`.

---

### TC-14 — Regression: /evidence prior 5 rows unchanged

**Type:** browser  
**Preconditions:** Frontend is running; backend is running.

**Steps:**
1. Navigate to `http://localhost:3000/evidence`.
2. Scroll to view the first 5 rows (the prior canonical entries: leadership_score, vcp_contraction@h20, vcp_contraction@h60, entry_quality, risk_score).
3. Verify each row still displays:
   - Correct hypothesis chips (kind, cohort, horizon, direction, condition where applicable).
   - Correct verdict + edge + control.
   - Correct registration date.
   - Correct linkback (e.g., "Backs: Leadership Lab →", "Backs: Factor Lab →").
4. Capture a screenshot of each row and MD5-compare to a prior run baseline (if available) to confirm no visual change.
5. Navigate to `/research/factor-lab`.
6. Verify the vcp_contraction badges at h20 and h60 still show "Proven" (unchanged).
7. Verify NO new combination badge on this page.

**Expected outcome:** All existing 5 canonical rows and their badges remain unchanged.  
**Pass criteria:** 5 rows render identically to prior iterations; no new badges on `/research/factor-lab`; vcp_contraction h20/h60 still "Proven".

---

### TC-15 — Regression: Breakout-watch regime row unchanged on /evidence

**Type:** browser  
**Preconditions:** Frontend is running; backend is running.

**Steps:**
1. Navigate to `http://localhost:3000/evidence`.
2. Scroll to find the Breakout-watch regime row (the event-study entry).
3. Verify it still displays: hypothesis chips (kind, cohort, horizon, direction), verdict, duration, control.
4. Verify NO change to the row's structure or styling.

**Expected outcome:** The event-study row remains unchanged.  
**Pass criteria:** Row present and visually identical to prior iterations.

---

### TC-16 — Backend: existing referee/evidence tests pass

**Type:** api  
**Preconditions:** Backend is running; test suite is available.

**Steps:**
1. Run: `cd apps/backend && .venv/bin/python -m pytest tests/test_evidence.py -v`
2. Verify all existing tests pass (no new failures).
3. If a test-only assertion was added (e.g., verifying the 6th combination entry in `GET /api/evidence`), verify it passes.
4. Verify no changes to the referee, `verify_edge`, `online_fdr`, `evidence.py`, or `api/evidence.py` source code (git diff should show only optional test additions).

**Expected outcome:** All backend evidence tests pass; no regressions.  
**Pass criteria:** Test exit code 0; all tests pass; no modifications to referee or verification logic.

---

### TC-17 — Data correctness: combination edge matches certified-claims.jsonl

**Type:** artifact  
**Preconditions:** `certified-claims.jsonl` row 6 exists with the combination PASS; `GET /api/evidence` payload is served.

**Steps:**
1. Read `runs/goal-session-mcp-loop/state/certified-claims.jsonl` line 6 (the combination entry).
2. Extract: `holdout_edge`, `control_excess`, `p_value`, `register_date`, `verdict.status`.
3. Fetch `GET /api/evidence` and locate the combination claim in the `claims[]` array.
4. Verify the `GET /api/evidence` entry matches the ledger row byte-for-byte (same edge, control, p, date, status).
5. Navigate to `http://localhost:3000/evidence` and find the combination row.
6. Verify the displayed edge, control, and registration date visually match the ledger (no UI recompute, no rounding discrepancy).

**Expected outcome:** All displayed values are verbatim from the certified ledger; no recomputation.  
**Pass criteria:** `holdout_edge ≈ 0.04693`, `control_excess ≈ 0.04693`, `p_value ≈ 0.0009995`, `register_date = 2026-07-01` (or gate-written date), `status = PASS`; all match in ledger and UI.

---

## Summary

**Total test cases:** 17

- **API tests:** 2 (TC-01, TC-02)
- **Artifact (TypeScript/unit) tests:** 8 (TC-03, TC-04, TC-05, TC-06, TC-07, TC-08, TC-16, TC-17)
- **Browser tests:** 7 (TC-09, TC-10, TC-11, TC-12, TC-13, TC-14, TC-15)

All test cases map directly to the phase spec requirements:
- **Definition of Done:** TC-01, TC-02, TC-08, TC-16, TC-17 verify the ledger entry and payload correctness.
- **J-08 acceptance (browser-qa):** TC-09, TC-10, TC-11, TC-12 verify the new "Proven" badge and `/evidence` row.
- **Regression (J-01..J-07):** TC-13, TC-14, TC-15 verify no changes to prior surfaces.
- **Anti-goals:** TC-02, TC-13 confirm no signal leakage to `/stocks`; TC-07 confirms honest language (no return/price promises); TC-04, TC-05 confirm no-lookahead logic in matchers.

All browser tests REQUIRE scrolling elements into the viewport and MD5-distinct screenshots (iter-3/iter-11 recurring lesson).
