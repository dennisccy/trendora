# goal-mcp-loop-iter-8 Functional Test Plan

**Phase:** goal-mcp-loop-iter-8
**Date:** 2026-06-30
**Frontend Present:** yes

## Phase Goal

Surface the vcp_contraction top-decile certified edge (out-of-sample +3.33%, p=0.01149) on the Research factor lab and Evidence ledger, reading the canonical `GET /api/evidence` payload, so J-06 passes and all six Must-have journeys are green.

## Test Cases

### TC-01 — Factor-lab vcp_contraction top-decile badge renders "Proven" and links to ledger

**Type:** browser
**Preconditions:** 
- Frontend running at localhost:3000
- Backend running with `/api/evidence` returning the 4-entry certified-claims ledger
- vcp_contraction factor data populated in the research labs

**Steps:**
1. Navigate to `http://localhost:3000/research/factor-lab`
2. Scroll to find the **vcp_contraction** factor's top-decile (D10) summary row
3. Verify the evidence status badge is visible on that row
4. Read the badge text

**Expected outcome:** The vcp_contraction top-decile row displays an evidence status badge reading **"Proven"** (green accent badge, ShieldCheck icon).

**Pass criteria:** The badge text is exactly **"Proven"** and is positioned in a dedicated cell on the vcp_contraction top-decile summary row.

---

### TC-02 — Factor-lab "Proven" badge deep-links to /evidence vcp_contraction row

**Type:** browser
**Preconditions:** 
- TC-01 passes (vcp_contraction "Proven" badge visible)
- Browser at `/research/factor-lab`

**Steps:**
1. Click the vcp_contraction "Proven" badge
2. Wait for navigation
3. Verify the URL and page content

**Expected outcome:** Browser navigates to `/evidence#factor-vcp_contraction-d10-h20` (or equivalent stable cohort anchor). The vcp_contraction claim row is visible and scrolled into focus.

**Pass criteria:** URL contains the cohort anchor `#factor-vcp_contraction-d10-h20` or similar stable identifier derived from (kind, factor, slice_kind, decile, horizon). The anchor does NOT conflict with signal-based anchors (e.g. `signal-leadership_score`).

---

### TC-03 — /evidence vcp_contraction claim row renders with correct fields

**Type:** browser
**Preconditions:** 
- Frontend running at localhost:3000
- Backend running with `/api/evidence` returning the 4-entry certified-claims ledger (vcp_contraction entry #4)
- User navigated to `/evidence` (via TC-02 or direct navigation)

**Steps:**
1. Navigate to or remain on `http://localhost:3000/evidence`
2. Scroll down to locate the **vcp_contraction** claim row (likely below leadership and Breakout-watch rows)
3. For each field, verify it is present and rendered

**Expected outcome:** The vcp_contraction row renders ALL of the following fields identically to existing claim rows:
- **Hypothesis:** cohort selectors clearly displayed (e.g. "vcp_contraction — top decile (D10)")
- **Out-of-sample verdict:** edge **+3.33%** (matches certified-claims.jsonl)
- **Control comparison:** **"vs SPY"** (explicitly labeled)
- **P-value / significance:** **p ≈ 0.01149** or similar notation (matches ledger)
- **Registration date:** **2026-06-30** (matches ledger register_date)
- **Forward-walk score-to-date:** present (same format as leadership/Breakout-watch rows)
- **Linkback:** **"Backs: Research factor lab →"** link visible

**Pass criteria:** All seven fields render. The edge (+3.33%) and p-value (0.01149), and register_date (2026-06-30) **byte-match** the vcp_contraction entry in `GET /api/evidence`. The linkback text is exactly **"Backs: Research factor lab →"** (not "Backs: Stocks leaderboard →", which is for score-signal rows).

---

### TC-04 — /evidence vcp_contraction linkback navigates to /research/factor-lab

**Type:** browser
**Preconditions:** 
- TC-03 passes (vcp_contraction row visible on `/evidence`)
- Browser at `/evidence`, vcp_contraction row in viewport

**Steps:**
1. Click the **"Backs: Research factor lab →"** link in the vcp_contraction row
2. Wait for navigation

**Expected outcome:** Browser navigates to `/research/factor-lab`.

**Pass criteria:** URL is `http://localhost:3000/research/factor-lab`. The page displays the factor-lab summary table with vcp_contraction row visible.

---

### TC-05 — Factor-lab other factors show "Not yet proven" badges

**Type:** browser
**Preconditions:** 
- Frontend running at localhost:3000
- `/research/factor-lab` accessible
- Backend `/api/evidence` has no PASS certified-claim for factors other than vcp_contraction

**Steps:**
1. Navigate to `/research/factor-lab`
2. Scan the top-decile summary rows for factors other than vcp_contraction (e.g. Entry Quality, Risk, momentum, ma_stack, hv, etc.)

**Expected outcome:** Every factor top-decile row EXCEPT vcp_contraction shows an evidence badge reading **"Not yet proven"** (muted default badge, Shield icon, no link).

**Pass criteria:** At least TWO unbacked factors (e.g. Entry Quality + Risk, or ma_stack + hv) render a "Not yet proven" badge on their D10 rows. No badge is a link; all are non-interactive chips.

---

### TC-06 — /stocks leaderboard still shows score status badges (regression J-01)

**Type:** browser
**Preconditions:** 
- Frontend running at localhost:3000
- Backend fully populated
- `/stocks` page accessible

**Steps:**
1. Navigate to `http://localhost:3000/stocks`
2. Observe the leaderboard rows
3. For each score column (Leadership, Entry Quality, Risk), verify a badge is present

**Expected outcome:** Every score column shows an evidence status badge. Leadership reads **"Proven"**; Entry Quality and Risk read **"Not yet proven"**.

**Pass criteria:** All three score badges are visible on at least the first 3 leaderboard rows. NO vcp_contraction badge or factor-family badge appears inline on the stock rows (J-01 unaffected by iter-8; vcp_contraction backs factor-lab only, not per-stock scores).

---

### TC-07 — /stocks/{ticker} detail proof drill-down still renders (regression J-02)

**Type:** browser
**Preconditions:** 
- TC-06 passes (leadership badge visible on leaderboard)
- Frontend at `/stocks`

**Steps:**
1. Click any stock ticker to open `/stocks/{ticker}`
2. Locate the Leadership score section
3. Click or expand the "Proven" badge to reveal the drill-down panel

**Expected outcome:** The panel shows the proof details:
- Out-of-sample test result (e.g. "beat SPY out-of-sample holdout")
- Control comparison (e.g. "vs SPY")
- Certified-claim ID
- Registration date

**Pass criteria:** The drill-down panel renders with at least the control label ("vs SPY") and the claim ID + date clearly visible. The panel content is identical to pre-iter-8 behavior (no regression).

---

### TC-08 — Dashboard/Evidence Breakout-watch row labels "Regime: Risk-on" (regression J-04)

**Type:** browser
**Preconditions:** 
- Frontend running at localhost:3000
- Backend has Breakout-watch regime-conditioned evidence claim
- `/evidence` page accessible

**Steps:**
1. Navigate to `http://localhost:3000/evidence`
2. Locate the **Breakout-watch** claim row (should appear before or near vcp_contraction row)
3. Read the hypothesis/title text

**Expected outcome:** The Breakout-watch row's hypothesis field displays **"Regime: Risk-on"** (or similar regime label). A linkback reads **"Backs: Research [regime/event-study] lab →"** (NOT "Research factor lab →").

**Pass criteria:** The regime label text is exactly **"Regime: Risk-on"** and the linkback is to a research lab other than factor-lab. The row content is byte-identical to pre-iter-8 (no regression).

---

### TC-09 — /evidence leadership row and "Backs: Stocks leaderboard →" unchanged (regression J-05)

**Type:** browser
**Preconditions:** 
- `/evidence` page accessible
- Backend has leadership_score certified claim

**Steps:**
1. Navigate to `http://localhost:3000/evidence`
2. Locate the **Leadership** claim row (first row)
3. Verify all fields and the linkback text

**Expected outcome:** The leadership row renders with:
- Hypothesis: "Leadership Score"
- Out-of-sample verdict (e.g. "beat SPY out-of-sample holdout")
- Control: "vs SPY"
- Registration date, p-value, and forward-walk score
- **Linkback: "Backs: Stocks leaderboard →"**

**Pass criteria:** The linkback is exactly **"Backs: Stocks leaderboard →"** (not "Backs: Research factor lab →"). All other fields match pre-iter-8 rendering (byte-identical).

---

### TC-10 — /evidence leadership row deep-links to /stocks (regression J-05 round-trip)

**Type:** browser
**Preconditions:** 
- TC-09 passes (leadership linkback visible)
- Browser at `/evidence`

**Steps:**
1. Click the **"Backs: Stocks leaderboard →"** linkback on the leadership row
2. Wait for navigation

**Expected outcome:** Browser navigates to `/stocks` (or `/stocks#signal-leadership_score` if an anchor is used).

**Pass criteria:** URL is `/stocks` or contains the leadership signal anchor. The stocks leaderboard is displayed.

---

### TC-11 — GET /api/evidence returns vcp_contraction claim with PASS verdict (API correctness)

**Type:** api
**Preconditions:** 
- Backend running at localhost:8000
- certified-claims.jsonl contains the 4-entry ledger (leadership PASS, Breakout-watch PASS, ma_stack FAIL, vcp_contraction PASS)

**Steps:**
1. Execute:
   ```bash
   curl -s http://localhost:8000/api/evidence | jq '.claims[] | select(.claim.factor == "vcp_contraction")'
   ```
2. Verify the vcp_contraction entry in the response

**Expected outcome:** The response contains exactly ONE claim entry with:
- `kind: "factor"`
- `factor: "vcp_contraction"`
- `slice_kind: "decile"`
- `decile: 10`
- `horizon: 20`
- `direction: "positive"`
- `proven: true`
- `verdict.status: "PASS"`
- `verdict.edge: 0.0333` (or +3.33% formatted)
- `verdict.p_value: 0.011494` (or ≈ 0.01149)
- `verdict.control_excess: 0.0333`
- `verdict.register_date: "2026-06-30"` (ISO format)
- **`signal: null`** (NOT present or explicitly null — no per-stock score)

**Pass criteria:** All fields above are present with exact values. HTTP status code is 200. The `signal` key is absent or null (NOT a string like "vcp_contraction"). No score-column signal is created.

---

### TC-12 — GET /api/evidence proven_signals excludes vcp_contraction (signal-less claim)

**Type:** api
**Preconditions:** 
- Backend running at localhost:8000
- certified-claims.jsonl has 4 entries

**Steps:**
1. Execute:
   ```bash
   curl -s http://localhost:8000/api/evidence | jq '.proven_signals | keys'
   ```
2. Verify the key list

**Expected outcome:** The `proven_signals` keys are **exactly `["leadership_score"]`** (or sorted equivalent). vcp_contraction is NOT a key in proven_signals.

**Pass criteria:** proven_signals keys == `["leadership_score"]` (only one key, the score column). No `"vcp_contraction"`, `"entry_quality_score"`, `"risk_score"`, or other factor names are present as keys.

---

### TC-13 — GET /api/evidence ma_stack FAIL entry is still present and unprovable

**Type:** api
**Preconditions:** 
- Backend running at localhost:8000

**Steps:**
1. Execute:
   ```bash
   curl -s http://localhost:8000/api/evidence | jq '.claims[] | select(.claim.factor == "ma_stack")'
   ```
2. Verify the ma_stack entry in the response

**Expected outcome:** The response contains exactly ONE claim entry for ma_stack with:
- `proven: false`
- `verdict.status: "FAIL"`
- All cohort selectors (ma_stack, decile 10, horizon 20, direction positive) verbatim

**Pass criteria:** ma_stack row is present; `proven: false`; `verdict.status: "FAIL"` (no subsequent PASS overrides it). The FAIL entry is auditable and demonstrates honest failed-claim history.

---

### TC-14 — Unit test: resolveCohortEvidence selector matching (frontend)

**Type:** artifact
**Preconditions:** 
- Frontend test suite runnable
- `apps/frontend/lib/evidence.test.ts` contains cases for `resolveCohortEvidence`

**Steps:**
1. Run `npm test -- apps/frontend/lib/evidence.test.ts` (or equivalent test command for the frontend)
2. Locate the `resolveCohortEvidence` test suite

**Expected outcome:** 
- **Case 1 (full selector match):** a cohort querying `{kind:"factor", factor:"vcp_contraction", slice_kind:"decile", decile:10, horizon:20, direction:"positive"}` against a claims[] list containing the vcp_contraction PASS entry returns `{proven:true, label:"Proven", href:"#factor-vcp_contraction-d10-h20", claim:{...}}`.
- **Case 2 (partial selector mismatch):** querying the same cohort against a claims[] missing vcp_contraction returns `{proven:false, label:"Not yet proven", href:null}`.
- **Case 3 (matched-but-FAIL):** querying ma_stack against claims[] containing the ma_stack FAIL entry returns `{proven:false, label:"Not yet proven", href:null}`.
- **Case 4 (empty/null claims):** querying any cohort against `claims:[]` or `claims:undefined` returns `{proven:false, label:"Not yet proven", href:null}`.

**Pass criteria:** All four cases pass. resolveCohortEvidence never returns `proven:true` unless the matched entry's `proven` field is strictly `true` and `verdict.status === "PASS"`.

---

### TC-15 — Unit test: claimSurface factor branch renders honest title and linkback

**Type:** artifact
**Preconditions:** 
- Frontend test suite runnable
- `apps/frontend/lib/evidence.test.ts` contains cases for `claimSurface`

**Steps:**
1. Run the frontend test suite
2. Locate the `claimSurface` test suite, specifically the `kind:"factor"` branch

**Expected outcome:**
- **Case 1 (factor claim):** calling `claimSurface({kind:"factor", factor:"vcp_contraction", slice_kind:"decile", decile:10, horizon:20, direction:"positive"})` returns an object with:
  - `title: "vcp_contraction — top decile (D10)"` (or similar derived from selectors, NOT "Unmapped signal")
  - `subtitle: "Out-of-sample edge — factor top decile"` (never a return promise)
  - `backingPath: "/research/factor-lab"` (linkback is to factor-lab, NOT stocks)
- **Case 2 (score row unchanged):** calling `claimSurface({kind:"score", signal:"leadership_score"})` returns an object with:
  - `title: "Leadership Score"`
  - `backingPath: "/stocks"` (unchanged from pre-iter-8)
- **Case 3 (event-study row unchanged):** calling `claimSurface({kind:"event-study", ...})` returns its pre-iter-8 output byte-identical.

**Pass criteria:** Factor branch title is honest and derived from selectors. Score and event-study branches are byte-identical to pre-iter-8 (zero regression).

---

### TC-16 — Unit test: cohortClaimId/cohortEvidenceAnchor stability and collision-free

**Type:** artifact
**Preconditions:** 
- Frontend test suite runnable
- `apps/frontend/lib/evidence.test.ts` contains cases for `cohortClaimId` / `cohortEvidenceAnchor`

**Steps:**
1. Run the frontend test suite
2. Locate the cohort anchor stability test cases

**Expected outcome:**
- **Case 1 (deterministic):** calling `cohortEvidenceAnchor({factor:"vcp_contraction", slice_kind:"decile", decile:10, horizon:20, direction:"positive"})` returns the same string on every call.
- **Case 2 (collision-free):** the returned anchor differs from `"signal-leadership_score"` and other signal-based anchors; likely format is `"factor-vcp_contraction-d10-h20"` (or similar rule-based derivation).
- **Case 3 (different cohorts diverge):** two distinct cohorts (e.g. vcp_contraction D10 vs D9, or different horizon) produce different anchors.

**Pass criteria:** The anchor function produces identical output on repeated calls (deterministic). No collision between signal-based anchors (signal-*) and cohort anchors (factor-*). ClaimRow uses this anchor for factor claims via `id={cohortClaimId(claim.claim)}`.

---

### TC-17 — Unit test: backend build_evidence_payload post-certification ledger

**Type:** artifact
**Preconditions:** 
- Backend test suite runnable
- `apps/backend/tests/test_evidence.py` contains a post-certification assertion

**Steps:**
1. Run `pytest apps/backend/tests/test_evidence.py::test_build_evidence_payload_post_certification` (or similar test name)
2. Verify the test runs and passes

**Expected outcome:** The test:
- Constructs a 4-entry certified-claims ledger: leadership_score PASS, Breakout-watch Risk-on PASS, ma_stack D10 FAIL, vcp_contraction D10 PASS
- Calls `build_evidence_payload(ledger)` to get the served response
- Asserts:
  - `payload["proven_signals"] == {"leadership_score": <leadership_claim>}` (vcp_contraction is NOT a key; only score columns enter proven_signals)
  - `payload["claims"][3]["proven"] == true` (vcp_contraction row is proven)
  - `payload["claims"][3]["signal"] == None` or is absent (signal-less claim, backing factor-lab only)
  - `payload["claims"][3]["claim"]["factor"] == "vcp_contraction"` and all cohort selectors verbatim
  - `payload["claims"][3]["verdict"]["edge"] == 0.0333`, `payload["claims"][3]["verdict"]["p_value"] == 0.011494`, `payload["claims"][3]["verdict"]["register_date"] == "2026-06-30"`
  - `payload["claims"][2]["proven"] == false` (ma_stack FAIL row is still present and unprovable)
  - `_resolve_signal(vcp_contraction_claim) -> None` (the _SCORE_COLUMN_FACTORS exclusion logic works)

**Pass criteria:** All assertions pass. No regression in the served claim shape or the proven_signals computation.

---

### TC-18 — Frontend port is freed before binding; backend connection confirmed

**Type:** artifact
**Preconditions:** 
- Frontend and backend services are starting fresh
- Port 3000 (frontend) and 8000 (backend) are available

**Steps:**
1. Run `start-frontend.sh` and wait for readiness
2. Run `curl -s http://localhost:3000/`
3. Run `curl -s http://localhost:8000/api/evidence | jq '.claims | length'`

**Expected outcome:** 
- Frontend responds with 200 status and HTML content
- Backend responds with 200 status and `claims` array length == 4 (all four ledger entries)

**Pass criteria:** Both services bind successfully to their ports with zero conflict. Backend `/api/evidence` returns all 4 certified-claims entries (leadership PASS, Breakout-watch PASS, ma_stack FAIL, vcp_contraction PASS) with vcp_contraction data present.

---

### TC-19 — /evidence vcp_contraction row scrolls into viewport before screenshot

**Type:** browser
**Preconditions:** 
- Frontend at `/evidence`
- vcp_contraction row exists but is below the fold

**Steps:**
1. Navigate to `/evidence`
2. Scroll down to locate the vcp_contraction row
3. Scroll the row into the viewport center

**Expected outcome:** The vcp_contraction claim row and its fields (edge, control, date, linkback) are fully visible and not cropped by the viewport.

**Pass criteria:** The row is scrolled into frame before any screenshot is taken (iter-3 lesson: below-the-fold disclosures must be scrolled into viewport for visual evidence).

---

### TC-20 — /research/factor-lab vcp_contraction "Proven" badge scrolls into viewport before screenshot

**Type:** browser
**Preconditions:** 
- Frontend at `/research/factor-lab`
- vcp_contraction top-decile row exists and may be below the fold

**Steps:**
1. Navigate to `/research/factor-lab`
2. Scroll down to locate the vcp_contraction factor summary row
3. Scroll the row and its evidence badge into the viewport center

**Expected outcome:** The vcp_contraction top-decile row and its "Proven" badge are fully visible and not cropped.

**Pass criteria:** The badge is scrolled into frame before any screenshot is taken (iter-3 lesson: below-the-fold disclosures must be scrolled into viewport for visual evidence).

---

## Summary

**Total test cases:** 20

**Browser tests (UI verification):** 11 (TC-01, TC-02, TC-03, TC-04, TC-05, TC-06, TC-07, TC-08, TC-09, TC-10, TC-19, TC-20)

**API tests (backend verification):** 3 (TC-11, TC-12, TC-13)

**Unit/integration tests (pure functions + artifacts):** 5 (TC-14, TC-15, TC-16, TC-17, TC-18)

**Key assertions:**
- vcp_contraction "Proven" badge on factor-lab deep-links to `/evidence` cohort anchor
- `/evidence` vcp_contraction row renders 7 fields + "Backs: Research factor lab →" linkback
- Edge (+3.33%), p-value (0.01149), register_date (2026-06-30) byte-match `GET /api/evidence` and certified-claims.jsonl
- ma_stack FAIL row present and honestly reads "Not yet proven"
- proven_signals keys == ["leadership_score"] only (vcp_contraction has NO signal)
- J-01/J-02/J-04/J-05 regressions: leadership "Proven" on `/stocks`, proof drill-down intact, Breakout-watch "Regime: Risk-on" unchanged, `/evidence` leadership round-trip preserved
- Below-the-fold rows (vcp_contraction on `/evidence` and factor-lab) scrolled into viewport before capture
