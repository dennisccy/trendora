# Goal Iteration 11 Functional Test Plan

**Phase:** goal-mcp-loop-iter-11
**Date:** 2026-07-01
**Frontend Present:** yes

## Phase Goal

Promote the referee-certified `vcp_contraction` D10 @ h60 signal-less edge (holdout +8.91%, p=0.00049975) to canonical status and surface it as a per-horizon "Proven" badge on the factor lab + a new certified-claim row on `/evidence`, while uncertified horizons (h1/h5/h10) render "Not yet proven" and the existing h20 claim remains unchanged.

## Test Cases

### TC-01 — New h60 Evidence Claim Created

**Type:** api
**Preconditions:** Backend service running; `certified-claims.jsonl` contains 4 prior entries

**Steps:**
1. `curl -s http://localhost:8000/api/evidence | jq '.claims | length'`
2. Verify response is `5`
3. `curl -s http://localhost:8000/api/evidence | jq '.claims[4]'`
4. Confirm the 5th entry has `factor="vcp_contraction"`, `decile=10`, `horizon=60`, `direction="positive"`, `status="PASS"`, `"ledger":"canonical"`

**Expected outcome:** The evidence API serves exactly 5 claims, with the new h60 claim at index 4

**Pass criteria:** `claims | length == 5`; entry 5 has exact JSON: `{"kind":"factor","factor":"vcp_contraction","slice_kind":"decile","decile":10,"horizon":60,"direction":"positive","status":"PASS","holdout_edge":0.08909719710495288,"control_excess":0.08909719710495288,"p_value":0.0004997501249375312,"deflation":"bonferroni","deflation_divisor":5,"required_p":0.010,"cohort_n":12026,"control_n":1055,"ledger":"canonical"}`

---

### TC-02 — proven_signals Unchanged

**Type:** api
**Preconditions:** Backend service running; new h60 claim exists

**Steps:**
1. `curl -s http://localhost:8000/api/evidence | jq '.proven_signals'`
2. Verify the output

**Expected outcome:** `proven_signals` contains only `{leadership_score}` (no entry for vcp_contraction h60)

**Pass criteria:** `proven_signals == {"leadership_score": {"...": "..."}}` (exact structure preserved)

---

### TC-03 — Evidence Badge h60 Renders "Proven"

**Type:** browser
**Preconditions:** Frontend running; backend returns the new h60 claim; `/research/factor-lab` accessible

**Steps:**
1. Navigate to `http://localhost:3000/research/factor-lab`
2. Wait for page to load (factor table visible)
3. Scroll to the `vcp_contraction` factor row
4. Scroll horizontally to locate the h60 (60-day) forward-return column
5. Locate the evidence badge in the h60 column: `[data-factor="vcp_contraction"][data-horizon="60"]`
6. Read the badge text and href

**Expected outcome:** Badge reads "Proven ✓" and its href is `/evidence#factor-vcp_contraction-d10-h60`

**Pass criteria:** `[data-factor="vcp_contraction"][data-horizon="60"][data-proven="true"]` exists; href matches `/evidence#factor-vcp_contraction-d10-h60`

---

### TC-04 — Evidence Badge h10 Renders "Not yet proven"

**Type:** browser
**Preconditions:** Frontend running; `/research/factor-lab` accessible; h10 claim does not exist

**Steps:**
1. Navigate to `http://localhost:3000/research/factor-lab`
2. Scroll to `vcp_contraction` row
3. Locate the h10 (10-day) forward-return column evidence badge: `[data-factor="vcp_contraction"][data-horizon="10"]`
4. Read badge text and href attribute

**Expected outcome:** Badge reads "Not yet proven"; no href (or href is empty/null)

**Pass criteria:** `[data-factor="vcp_contraction"][data-horizon="10"][data-proven="false"]` exists; href is missing or empty

---

### TC-05 — Evidence Badge h20 Regression (Still "Proven")

**Type:** browser
**Preconditions:** Frontend running; existing h20 claim present; `/research/factor-lab` accessible

**Steps:**
1. Navigate to `http://localhost:3000/research/factor-lab`
2. Scroll to `vcp_contraction` row
3. Locate the h20 (20-day) column evidence badge: `[data-factor="vcp_contraction"][data-horizon="20"]`
4. Read badge text and href

**Expected outcome:** Badge reads "Proven ✓" and href is `/evidence#factor-vcp_contraction-d10-h20`

**Pass criteria:** `[data-factor="vcp_contraction"][data-horizon="20"][data-proven="true"]` exists; href is `/evidence#factor-vcp_contraction-d10-h20`

---

### TC-06 — Evidence Page New h60 Row Renders Correctly

**Type:** browser
**Preconditions:** Frontend running; backend returns 5 claims; `/evidence` accessible

**Steps:**
1. Navigate to `http://localhost:3000/evidence`
2. Wait for claims list to load
3. Locate the row with `factor="vcp_contraction"` and `horizon=60`
4. Verify all fields are present and correct: hypothesis display (including `horizon=60` chip), status "PASS", holdout edge "+8.91%", control vs SPY "+8.91%", registration date, forward-walk "Pending", "Backs: Research factor lab →"

**Expected outcome:** h60 row renders with all fields, status PASS, correct edge/control percentages, and linkback

**Pass criteria:** Row contains `factor-vcp_contraction-d10-h60` anchor; displays "+8.91%" for holdout edge; "PASS" status; "Pending" forward-walk; linkback text "Backs: Research factor lab →"

---

### TC-07 — Evidence Page h60 Row Deep-links Back to Factor Lab

**Type:** browser
**Preconditions:** Frontend running; `/evidence` accessible; h60 row present

**Steps:**
1. Navigate to `http://localhost:3000/evidence`
2. Locate the vcp_contraction h60 row
3. Click the "Backs: Research factor lab →" link
4. Verify page navigates and anchor is set

**Expected outcome:** User is taken to `/research/factor-lab#factor-vcp_contraction-d10-h60` or similar, landing near the h60 badge

**Pass criteria:** Navigation succeeds; URL contains `/research/factor-lab`; no 404 errors

---

### TC-08 — Evidence Page h20 Row Unchanged (Regression)

**Type:** browser
**Preconditions:** Frontend running; `/evidence` accessible; existing h20 claim present

**Steps:**
1. Navigate to `http://localhost:3000/evidence`
2. Locate the vcp_contraction h20 row
3. Verify all fields match iter-8 expectation: status "PASS", holdout edge, control vs SPY, registration date, "Backs: Research factor lab →"
4. Confirm wording does NOT include "60-day" or any h60-specific language

**Expected outcome:** h20 row is byte-identical to iter-8 (exact field values and wording preserved)

**Pass criteria:** h20 row displays with iter-8's exact subtitle wording (no "60-day hold" suffix on h20); href is `/evidence#factor-vcp_contraction-d10-h20`

---

### TC-09 — All Prior Evidence Rows Unchanged (Regression)

**Type:** browser
**Preconditions:** Frontend running; `/evidence` accessible

**Steps:**
1. Navigate to `http://localhost:3000/evidence`
2. Verify all 5 rows are present: leadership_score PASS, Breakout-watch PASS, ma_stack FAIL, vcp_contraction h20 PASS, vcp_contraction h60 PASS
3. Spot-check 2-3 fields on the leadership_score and ma_stack rows (status, edge percentages, control)

**Expected outcome:** All 4 prior rows render unchanged; new h60 row is additive

**Pass criteria:** Exactly 5 rows present; each prior row renders with same values as iter-8/iter-10

---

### TC-10 — Leadership Badge on /stocks Regression (No h60 Signal)

**Type:** browser
**Preconditions:** Frontend running; `/stocks` leaderboard accessible; no new h60 signal badge should appear

**Steps:**
1. Navigate to `http://localhost:3000/stocks`
2. Inspect any stock row's score column
3. Locate all evidence badges (Leadership, Entry Quality, Risk)
4. Confirm Leadership reads "Proven ✓"
5. Confirm no new inline badge references "vcp_contraction" or "h60"

**Expected outcome:** Leadership badge reads "Proven ✓"; Entry Quality and Risk read "Not yet proven"; no vcp_contraction h60 inline badge exists

**Pass criteria:** Score badges unchanged from iter-8; `proven_signals` still equals `{leadership_score}`; zero new signals on `/stocks`

---

### TC-11 — Unit Test: resolveCohortEvidence h60 Resolves Proven

**Type:** artifact
**Preconditions:** Frontend test suite runs; h60 claim in `certified-claims.jsonl`

**Steps:**
1. Run: `cd apps/frontend && npm test -- lib/evidence.test.ts`
2. Locate test case covering `resolveCohortEvidence({factor:"vcp_contraction", slice_kind:"decile", decile:10, horizon:60, direction:"positive"}, claims)`
3. Verify it asserts `status="proven"` and `href` contains `factor-vcp_contraction-d10-h60`

**Expected outcome:** Test passes; matcher resolves h60 to proven with correct href

**Pass criteria:** Test output shows green/pass for h60 proven case; no regressions on h20 or h10 cases

---

### TC-12 — Unit Test: resolveCohortEvidence h10 Resolves Not Proven

**Type:** artifact
**Preconditions:** Frontend test suite runs; no h10 claim exists in `certified-claims.jsonl`

**Steps:**
1. Run: `cd apps/frontend && npm test -- lib/evidence.test.ts`
2. Locate test case covering `resolveCohortEvidence({factor:"vcp_contraction", decile:10, horizon:10, ...}, claims)`
3. Verify it asserts `status="not_proven"` and `href` is empty/falsy

**Expected outcome:** Test passes; h10 correctly resolves to not proven with no href

**Pass criteria:** Test output shows green/pass for h10 not-proven case

---

### TC-13 — Unit Test: formatEvidencePct Edge Percentage

**Type:** artifact
**Preconditions:** Frontend test suite runs

**Steps:**
1. Run: `cd apps/frontend && npm test -- lib/evidence.test.ts`
2. Locate test case covering `formatEvidencePct(0.08909719710495288)`
3. Verify assertion is `"+8.91%"`

**Expected outcome:** Formatter rounds correctly to +8.91%

**Pass criteria:** Test assertion passes exactly; no rounding error

---

### TC-14 — Unit Test: claimSurface Subtitle Disambiguation

**Type:** artifact
**Preconditions:** Frontend test suite runs

**Steps:**
1. Run: `cd apps/frontend && npm test -- lib/evidence.test.ts`
2. Locate test case for `claimSurface` subtitle for the h60 factor-cohort claim
3. Verify subtitle includes "60-day hold" (or similar horizon-specific language)
4. Locate test case for h20 subtitle
5. Verify h20 subtitle does NOT include "60-day"; it remains byte-identical to iter-8

**Expected outcome:** h60 subtitle disambiguates by horizon; h20 remains unchanged

**Pass criteria:** h60 subtitle includes horizon marker; h20 subtitle is byte-identical to iter-8 test expectation

---

### TC-15 — Component Test: FactorEvidenceBadge data-horizon Attribute

**Type:** artifact
**Preconditions:** Frontend component tests run; `FactorEvidenceBadge` renders per-horizon

**Steps:**
1. Run: `cd apps/frontend && npm test -- _labs.test.tsx` (or component test location)
2. Locate test rendering vcp_contraction row with all horizons [1, 5, 10, 20, 60]
3. Verify each badge renders with `data-horizon="{horizon}"` attribute
4. Verify h60 badge has `data-proven="true"`; h1/h5/h10 have `data-proven="false"`; h20 has `data-proven="true"`

**Expected outcome:** Each badge carries correct `data-horizon` and `data-proven` attributes

**Pass criteria:** h60 renders `[data-horizon="60"][data-proven="true"]`; h10 renders `[data-horizon="10"][data-proven="false"]`; h20 renders `[data-horizon="20"][data-proven="true"]`

---

### TC-16 — Component Test: ma_stack (FAIL claim) Renders "Not yet proven"

**Type:** artifact
**Preconditions:** Frontend component tests run; ma_stack FAIL claim exists in ledger

**Steps:**
1. Run: `cd apps/frontend && npm test -- _labs.test.tsx`
2. Locate test for ma_stack row
3. Verify all horizons render "Not yet proven" (because the claim has `status="FAIL"`)
4. Verify no badge reads "Proven" for ma_stack at any horizon

**Expected outcome:** Failed claims never light "Proven" badge, even if a horizon is queried

**Pass criteria:** All ma_stack badges render `data-proven="false"`; no horizon exception for failed entries

---

### TC-17 — Backend API Integrity: No Engine Edit

**Type:** api
**Preconditions:** Backend source code; routes, referee, ledger, online_fdr, triad_scan, evidence.py should be unchanged from iter-10

**Steps:**
1. `git diff HEAD~1 apps/backend/app/engine/referee.py` (or relevant step range)
2. `git diff HEAD~1 apps/backend/app/evidence.py`
3. `git diff HEAD~1 apps/backend/app/engine/ledger.py`
4. Verify no substantive changes (comment-only edits are acceptable)

**Expected outcome:** No engine / referee / ledger / triad_scan edit; the 5th claim entry is written by the post-decompose gate only

**Pass criteria:** `git diff` shows zero engine edits (or only TEST-only edits in test_evidence.py)

---

### TC-18 — Browser: factor-lab Badge Scrolled into Viewport (Iter-3 Lesson)

**Type:** browser
**Preconditions:** Frontend running; factor table is wide and h60 column may be off-screen initially

**Steps:**
1. Navigate to `http://localhost:3000/research/factor-lab`
2. Locate vcp_contraction row
3. If h60 column is not visible: scroll right/horizontally until the h60 forward-return column is in viewport
4. Take a screenshot showing the h60 badge and confirm it reads "Proven ✓"
5. Screenshot filename: `reports/qa/goal-mcp-loop-iter-11-evidence/TC-18-factor-lab-h60-badge.png`

**Expected outcome:** h60 badge is visibly present in the screenshot; "Proven ✓" is legible; no "below the fold" ambiguity

**Pass criteria:** Screenshot artifact exists; badge is on screen and readable; data-proven="true" confirmed via DOM inspection after scroll

---

### TC-19 — Browser: leadership_score h20 Badge Remains Proven (Iter-8 Regression)

**Type:** browser
**Preconditions:** Frontend running; `/research/factor-lab` accessible; leadership_score factor row present

**Steps:**
1. Navigate to `http://localhost:3000/research/factor-lab`
2. Locate leadership_score factor row
3. Check the h20 (20-day) column badge
4. Confirm it reads "Proven ✓" and href is `/evidence#signal-leadership_score` (or appropriate anchor for score-column factors)

**Expected outcome:** leadership_score h20 badge is "Proven ✓" and unaffected by the new h60 claim

**Pass criteria:** Badge reads "Proven ✓"; href is correct for signal-backed claim; iter-8 behavior fully preserved

---

## Summary

**Total test cases:** 19
- **API tests:** 7 (TC-01, TC-02, TC-17 conceptual + live curl; plus browser-side evidence fetch verification)
- **Browser tests:** 9 (TC-03, TC-04, TC-05, TC-06, TC-07, TC-08, TC-09, TC-10, TC-18, TC-19)
- **Unit/Component tests:** 3 (TC-11, TC-12, TC-13, TC-14, TC-15, TC-16 — artifact; frontend test suite)
- **Error-case coverage:** TC-04 (h10 uncertified), TC-10 (signal-less claim does not light /stocks badge), TC-16 (FAIL claim never "Proven")

**Pass requirements:**
- All 19 test cases must pass for the iteration to complete.
- h60 claim must be PASS in certified-claims.jsonl (gate precondition).
- h20 claim unchanged (J-06 regression protection).
- All 4 prior claims render unchanged (J-05 regression protection).
- proven_signals byte-identical {leadership_score} (anti-goal #1 upheld).
- No /stocks inline badge for h60 (signal-less claim; J-01/J-02/J-03 unaffected).
