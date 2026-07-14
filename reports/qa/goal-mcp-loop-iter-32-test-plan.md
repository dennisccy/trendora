# goal-mcp-loop-iter-32 Functional Test Plan

**Phase:** goal-mcp-loop-iter-32  
**Date:** 2026-07-14  
**Frontend Present:** yes

## Phase Goal

Expose the statistical-credibility budget visible before it is spent: a read-only certification-budget panel at `/research/budget` that surfaces total trials, current `required_p`, Thresholdout budget remaining, and staging LORD++ alpha-wealth with spend-over-time views; also re-verify J-19 (graveyard→registry deep-link scroll) via canonical browser-qa.

## Test Cases

### TC-01 — Budget payload single-source equality vs verify_edge

**Type:** api  
**Preconditions:**
- Backend running with live ledger files at canonical + staging paths
- Ledger contains 7+ certified claims (baseline state)

**Steps:**
1. Call `GET /api/research/budget` and capture the JSON payload
2. Independently call `ledger.count_trials(canonical_path)` via Python test harness
3. Independently compute `required_p = 0.05 / (count_trials(canonical_path) + 1)` using imported `referee.DEFAULT_ALPHA_PER_TEST`
4. Independently compute Thresholdout remaining = `0.05 - ledger.alpha_spent(canonical_path)` using imported `referee.DEFAULT_ALPHA_BUDGET`
5. Independently call `online_fdr.test_level(count_trials(staging_path) + 1, rejection_offsets(staging_path), config params)` for staging wealth

**Expected outcome:** Payload fields match independently derived values exactly (byte-equal).

**Pass criteria:** 
- Payload `n_trials` equals `count_trials(canonical_path)` (not `+1`)
- Payload `required_p` equals `0.05 / (count_trials(canonical_path) + 1)` (the next-trial bar)
- Payload `budget_remaining` equals `0.05 - alpha_spent(canonical_path)`
- Payload `staging_wealth` equals the `online_fdr.test_level(...)` call result

---

### TC-02 — Fixture claim spend: trials, required_p, alpha_charged, staging wealth recompute

**Type:** api  
**Preconditions:**
- Create a throwaway temp ledger at isolated path (never the real `certified-claims.jsonl` or `staging-ledger.jsonl`)
- Backend reconfigured to read from throwaway paths for this test only

**Steps:**
1. Get baseline payload from throwaway ledger (initially empty or zero state)
2. Append one **stable** fixture claim to the throwaway canonical ledger (hand-compute expected `alpha_charged = 0`)
3. Call `GET /api/research/budget` and capture new payload
4. Assert `n_trials` incremented by 1
5. Assert `required_p = 0.05 / (new_count + 1)`
6. Verify `alpha_charged` for stable claim is 0 (no Thresholdout debit)
7. Append one **overfit** fixture claim and re-call; assert `alpha_charged > 0`
8. Assert staging LORD++ level recomputes per the online-FDR formula

**Expected outcome:** All figures move exactly as per hand-computation; real ledgers (`certified-claims.jsonl`, `staging-ledger.jsonl`, `pre-registrations.jsonl`) byte-identical before/after test run.

**Pass criteria:**
- `n_trials: m → m+1 → m+2` as fixtures appended
- `required_p: 0.05/(m+1) → 0.05/(m+2) → 0.05/(m+3)` (exact fractions, no rounding)
- Stable fixture: `alpha_charged = 0`; overfit fixture: `alpha_charged > 0` (exact per-claim cost)
- Staging wealth recomputes per LORD++ recursion (recorded in fixture claim's `verdict.deflation` field)
- `git diff certified-claims.jsonl staging-ledger.jsonl pre-registrations.jsonl` is empty after test

---

### TC-03 — Missing/empty ledger resilience: 200 with honest snapshot

**Type:** api  
**Preconditions:**
- Backend ledger paths point to non-existent directory or empty files

**Steps:**
1. Call `GET /api/research/budget` with missing canonical ledger file
2. Call `GET /api/research/budget` with missing staging ledger file
3. Call `GET /api/research/budget` with empty (0 claims) ledger files

**Expected outcome:** HTTP 200 (never 500 or 404); payload returns honest zero/empty state.

**Pass criteria:**
- HTTP status 200
- `n_trials: 0`
- `required_p: 0.05 / 1` (the baseline bar with no trials yet)
- `budget_remaining: 0.05` (full budget, nothing spent)
- `staging_wealth` equals initial LORD++ level (no claims recorded)
- `spend_over_time` array is empty `[]`

---

### TC-04 — Spend-over-time series length and field integrity

**Type:** api  
**Preconditions:**
- Backend running with live ledger containing recorded claims (fixture or real)

**Steps:**
1. Call `GET /api/research/budget`
2. Count entries in `spend_over_time` array (canonical and staging separately)
3. Spot-check 3 historical entries: for each, verify recorded `required_p`, `deflation_divisor` (canonical), `alpha_charged` (canonical), and `deflation` (staging) fields match the persisted `verdict` object in the ledger file

**Expected outcome:** Series length matches claim count; historical points re-read from ledger verbatim.

**Pass criteria:**
- Length of `spend_over_time.canonical` equals `count_trials(canonical_path)`
- Length of `spend_over_time.staging` equals `count_trials(staging_path)`
- Each entry's `required_p`, `alpha_charged` (canonical) and `deflation` (staging) match the recorded `verdict` fields in the ledger
- No recomputation; only forward next-trial bar uses live functions

---

### TC-05 — Endpoint serves payload verbatim (no transformation)

**Type:** api  
**Preconditions:**
- Backend running with `GET /api/research/budget` wired and responding
- `build_budget_payload()` function exists and is called by the endpoint

**Steps:**
1. Call `GET /api/research/budget`
2. Compare returned JSON to direct call to `app.engine.budget_accounting.build_budget_payload()` in same session

**Expected outcome:** Byte-identical JSON (same key order, same precision, same values).

**Pass criteria:**
- Response body equals `json.dumps(build_budget_payload(), sort_keys=True)` (or equivalent deterministic serialization)
- Status 200, no extra fields added/removed by endpoint wrapper

---

### TC-06 — J-17 browser: /research/budget renders four figures with spend-over-time views

**Type:** browser  
**Preconditions:**
- Frontend and backend running in prod mode
- `/research/budget` page deployed and accessible
- Live ledger state populated (baseline: 7 trials)

**Steps:**
1. Navigate to `http://localhost:3000/research`
2. Locate the Governance & process grid and click the "Budget" card (`data-testid="research-governance-link-budget"`)
3. Assert page loads and displays four stat cards: **Total Trials**, **Current Required P**, **Budget Remaining**, **Staging LORD++ Wealth**
4. For each card, verify title + value rendered; inspect one card's spend-over-time mini-chart (sparkline or lightweight-charts line)
5. Verify no "Proven" / "Not yet proven" badges or proven-language appear

**Expected outcome:** All four figures visible, each with a per-trial spend-over-time view; no loading/error state.

**Pass criteria:**
- Total Trials card shows "7" (current baseline)
- Current Required P shows "0.00625" (0.05/8, formatted appropriately)
- Budget Remaining shows correct alpha remaining (e.g., "0.05" minus alpha_spent)
- Staging Wealth shows next-trial LORD++ level
- Each has a compact mini-chart or inline sparkline showing historical trend
- No error card, no "Proven" text, clean render

---

### TC-07 — J-17 browser: backend-unavailable state is contained error card

**Type:** browser  
**Preconditions:**
- Frontend deployed and running
- Backend service intentionally stopped or network made unreachable

**Steps:**
1. Navigate to `http://localhost:3000/research/budget`
2. Page loads but `GET /api/research/budget` fails (timeout or 5xx)
3. Inspect the page for error handling

**Expected outcome:** Contained error card displayed; navigation sidebar and top nav remain intact; page does not blank or show unhandled exception.

**Pass criteria:**
- Error card visible with message like "Backend unavailable" or similar
- Sidebar links remain clickable
- No blank app-error page or JavaScript error in console
- User can navigate away and retry

---

### TC-08 — J-17 browser: discovery path ≤2 clicks from Research hub

**Type:** browser  
**Preconditions:**
- Frontend running at http://localhost:3000
- User on dashboard or any initial page

**Steps:**
1. Click sidebar "Research" nav item → lands on `/research`
2. On `/research` page, locate "Governance & process" section and the Budget card
3. Click Budget card → navigates to `/research/budget`
4. Count total clicks

**Expected outcome:** Budget page reachable in exactly 2 clicks from Research hub.

**Pass criteria:**
- Sidebar → Research (1 click) → Governance grid visible
- Budget card present in grid with `data-testid="research-governance-link-budget"` (2 clicks) → `/research/budget`
- No intermediate pages; direct link path exists

---

### TC-09 — J-17 browser: displayed figures byte-match GET /api/research/budget payload

**Type:** browser  
**Preconditions:**
- Frontend running and displaying `/research/budget`
- Backend serving live payload

**Steps:**
1. In browser DevTools Network tab, record `GET /api/research/budget` response body
2. On the page, read displayed values: Total Trials, Required P, Budget Remaining, Staging Wealth
3. Compare each displayed value to the corresponding payload field

**Expected outcome:** Rendered numbers match payload values exactly (no UI-recompute, no format drift).

**Pass criteria:**
- `n_trials` on page = payload `n_trials`
- `required_p` on page = payload `required_p` (formatted consistently)
- `budget_remaining` on page = payload `budget_remaining` (formatted consistently)
- `staging_wealth` on page = payload `staging_wealth` (formatted consistently)
- No rounding error or recomputation drift

---

### TC-10 — J-19 browser: graveyard→registry deep-link scrolls target row into view

**Type:** browser  
**Preconditions:**
- Frontend running at http://localhost:3000
- `/research/graveyard` page loaded with one or more rows
- J-19 fix (`useEffect` scroll on lineage deep-link) already in tree at `apps/frontend/app/research/registry/page.tsx:43-58`

**Steps:**
1. Navigate to `/research/graveyard`
2. Locate a row with a lineage link (e.g., "View in registry" or similar)
3. Click the lineage link → navigates to `/research/registry#registration-<id>`
4. Assert `window.scrollY > 0` immediately after navigation completes (not 0, i.e., page did scroll)
5. Assert the target registry row with `registration-<id>` is visible in viewport (not above fold)

**Expected outcome:** Deep-link click triggers scroll to the target registry row; row is in view.

**Pass criteria:**
- Navigation completes without error
- URL changes to `/research/registry#registration-<id>`
- `window.scrollY > 0` (page scrolled down)
- Target row element with matching id is `getBoundingClientRect().top > 0 && .top < viewport height`

---

### TC-11 — J-18 regression re-verify: /research/registry 11 rows, 5 columns, ma_stack closed

**Type:** browser  
**Preconditions:**
- Frontend running
- Registry ledger populated (baseline: 11 registrations)

**Steps:**
1. Navigate to `/research/registry`
2. Count rendered rows in the table (excluding headers)
3. Count column headers
4. Locate the `ma_stack` registration row
5. Assert its status is "closed" or similar

**Expected outcome:** Registry displays all 11 rows with 5 columns as expected; ma_stack marked closed.

**Pass criteria:**
- Row count = 11
- Column count = 5 (e.g., hypothesis, selectors, status, date, source or similar)
- ma_stack row present with closed/permanent status
- Numbers byte-match the ledger file (no UI recompute)

---

### TC-12 — J-05 regression re-verify: /evidence 7 FAIL cards, numbers byte-match ledger

**Type:** browser  
**Preconditions:**
- Frontend running
- Canonical ledger has 7 FAIL verdicts (current baseline state)

**Steps:**
1. Navigate to `/evidence`
2. Count rendered claim rows showing FAIL verdict
3. For one FAIL claim, extract displayed values: out-of-sample edge, p-value, control comparison
4. Cross-check against the same claim's record in `certified-claims.jsonl`

**Expected outcome:** All 7 FAIL claims render; displayed numbers match ledger exactly.

**Pass criteria:**
- Claim count = 7
- All visible verdicts show FAIL state
- One spot-checked claim's out-of-sample edge / p-value / control byte-match the ledger row
- No rounding error; no UI recompute

---

### TC-13 — J-01 regression re-verify: /stocks leaderboard evidence badges render, no crash

**Type:** browser  
**Preconditions:**
- Frontend running
- `/stocks` leaderboard loads without errors
- Baseline: leaderboard has 100+ stocks (or as many as loaded)

**Steps:**
1. Navigate to `/stocks`
2. Assert page loads and leaderboard renders (no blank page or error)
3. Inspect first 5 rows for evidence badges (e.g., "Not yet proven" text or badge element)
4. Verify no console errors logged

**Expected outcome:** Leaderboard renders, evidence badges present, page stable.

**Pass criteria:**
- Page loads in <3s (interactive)
- Leaderboard rows render with scores and badges
- At least 5 rows have visible evidence status (badge or text)
- No unhandled JavaScript errors; no "Proven" labels on FAIL ledger state

---

### TC-14 — J-06/J-08/J-09 regression re-verify: /evidence claim rows FAIL, numbers byte-match

**Type:** browser  
**Preconditions:**
- Frontend running with `/evidence` loaded
- Ledger contains multi-horizon (J-09), combination (J-08), and vcp_contraction (J-06) rows, all FAIL

**Steps:**
1. Navigate to `/evidence`
2. Locate vcp_contraction top-decile claim row; record displayed verdict, edge, p-value, control
3. Locate rs_spy_3m 60-day horizon claim row; record displayed verdict, edge, p-value, control
4. Locate combination claim row; record displayed verdict, edge, p-value, control
5. Cross-check each against `certified-claims.jsonl` for the same claim (exact selector match)

**Expected outcome:** All three rows render with FAIL verdict and byte-matching numbers; no "Proven" badge on any.

**Pass criteria:**
- vcp_contraction row present, FAIL verdict shown, numbers match ledger
- rs_spy_3m h60 row present, FAIL verdict shown, numbers match ledger
- combination row present, FAIL verdict shown, numbers match ledger
- No "Proven" text on any row (current all-FAIL ledger state)
- Correct control comparison (SPY) displayed

---

## Summary

**Total test cases:** 14  
**API tests:** 5 (TC-01, TC-02, TC-03, TC-04, TC-05)  
**Browser tests:** 9 (TC-06, TC-07, TC-08, TC-09, TC-10, TC-11, TC-12, TC-13, TC-14)  
**Artifact checks:** 0

**Test categories by requirement:**
- **Single-source / UI-recompute guard:** TC-01, TC-02, TC-04, TC-05, TC-09
- **Resilience / error handling:** TC-03, TC-07
- **Discovery / navigation:** TC-08
- **J-17 functionality:** TC-06, TC-07, TC-08, TC-09
- **J-19 deep-link scroll:** TC-10
- **Regression suite:** TC-11, TC-12, TC-13, TC-14

**Key anti-goal coverage:**
- No proven-language on budget panel (TC-06)
- Numbers correct / byte-match (TC-02, TC-04, TC-09, TC-12, TC-14)
- Real ledgers untouched by tests (TC-02)
- No lookahead / determinism (implicit in all payload checks)
