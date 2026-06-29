# Goal-MCP-Loop-Iter-1 Functional Test Plan

**Phase:** goal-mcp-loop-iter-1
**Date:** 2026-06-29
**Frontend Present:** yes

## Phase Goal

Implement the read-side evidence infrastructure so every score on `/stocks` and stock-detail carries a visible "Proven / Not yet proven" status badge, and a new nav-reachable `/evidence` ledger page displays the certified-claims ledger — against the empty ledger today, all signals honestly read "Not yet proven" and nothing is presented as confident without referee certification.

## Test Cases

### TC-01 — Absent ledger returns empty payload

**Type:** api
**Preconditions:** No ledger file exists at the configured path; backend service is running

**Steps:**
1. Run backend service with an absent or empty ledger path
2. Execute: `curl -s http://localhost:8000/api/evidence | jq .`

**Expected outcome:** HTTP 200 response with JSON `{"claims": [], "proven_signals": {}}`
**Pass criteria:** Status code is 200; response body contains exactly empty arrays/objects; no 500 error on missing file

---

### TC-02 — PASS entry in ledger maps to proven_signals

**Type:** api
**Preconditions:** Ledger file exists with a single entry: `{claim: {signal: "leadership_v1"}, verdict: {status: "PASS"}, register_date: "2026-01-01", ...}`

**Steps:**
1. Start backend service pointing to the seeded ledger fixture
2. Execute: `curl -s http://localhost:8000/api/evidence | jq '.proven_signals'`

**Expected outcome:** Response includes `{"leadership_v1": {...claim, verdict summary...}}`
**Pass criteria:** The PASS entry's signal appears in proven_signals; claim data is included; verdict.status is "PASS"

---

### TC-03 — FAIL/INSUFFICIENT entries do NOT appear as proven

**Type:** api
**Preconditions:** Ledger file exists with entries where `verdict.status` is "FAIL" or "INSUFFICIENT"

**Steps:**
1. Start backend service pointing to the seeded ledger with FAIL/INSUFFICIENT entries
2. Execute: `curl -s http://localhost:8000/api/evidence | jq '.proven_signals'`

**Expected outcome:** FAIL/INSUFFICIENT signals are absent from proven_signals
**Pass criteria:** proven_signals map does not contain entries with verdict.status != "PASS"

---

### TC-04 — Ledger path resolution: env override vs config default

**Type:** api
**Preconditions:** Environment and config are settable; two different ledger files exist

**Steps:**
1. Unset `TRENDORA_LEDGER_PATH`; start backend (should use config default)
2. Verify `GET /api/evidence` reads from default path
3. Set `TRENDORA_LEDGER_PATH=/custom/ledger.jsonl` with different content
4. Restart backend; verify `GET /api/evidence` reads from custom path

**Expected outcome:** Without env var, default config path is used; with env var, it takes precedence
**Pass criteria:** Payload changes when env var points to a different file; config.yaml `evidence.ledger_path` is respected as fallback

---

### TC-05 — Evidence badge renders on /stocks leaderboard

**Type:** browser
**Preconditions:** Frontend and backend are running; leaderboard has at least 3 rows

**Steps:**
1. Navigate to `http://localhost:3000/stocks`
2. Observe the leaderboard rows (score area showing Leadership, Entry Quality, Risk)
3. For each of the first 3 rows, locate and inspect the score badges

**Expected outcome:** Each row's score area displays a visible badge (chip/pill shape) reading "Not yet proven" (gray/muted styling)
**Pass criteria:** At least 3 rows are visible; each row has at least one evidence badge; no row lacks a badge for its scores; styling is muted (not hype/bright)

---

### TC-06 — Evidence badge on stock detail page

**Type:** browser
**Preconditions:** Frontend and backend are running; a stock detail page is reachable

**Steps:**
1. Navigate to `http://localhost:3000/stocks`
2. Click the first stock row to open `/stocks/{ticker}`
3. Locate the score cards (Leadership, Entry Quality, Risk)
4. Inspect each score card for an evidence badge

**Expected outcome:** Each score card displays an evidence badge reading "Not yet proven"
**Pass criteria:** All three score cards present a visible badge; no score card lacks a status; styling is consistent with leaderboard badges

---

### TC-07 — Evidence nav entry is reachable and leads to /evidence

**Type:** browser
**Preconditions:** Frontend is running; sidebar nav is visible on `/stocks` or any page

**Steps:**
1. Navigate to `http://localhost:3000/stocks`
2. Locate the sidebar navigation menu
3. Find the "Evidence" entry (should appear after "Research")
4. Click it

**Expected outcome:** Browser navigates to `/evidence` page; page header displays "Evidence" or similar
**Pass criteria:** Click action succeeds; URL changes to `/evidence`; page content is non-404

---

### TC-08 — Evidence page renders honest empty state

**Type:** browser
**Preconditions:** Frontend is running; ledger is empty or absent (empty proven_signals)

**Steps:**
1. Navigate to `http://localhost:3000/evidence`
2. Inspect the page content

**Expected outcome:** Page displays text like "No certified claims yet" or "every signal currently reads Not yet proven"; no error or loading spinner
**Pass criteria:** Empty state message is visible; page does not show a claims list; page is not an error state

---

### TC-09 — Evidence ledger page has correct layout structure

**Type:** browser
**Preconditions:** Frontend is running; page renders without ledger content (empty)

**Steps:**
1. Navigate to `http://localhost:3000/evidence`
2. Inspect the page DOM for presence of layout containers
3. Confirm the markup includes placeholders or labels for: hypothesis, out-of-sample verdict, control comparison, registration date, forward-walk score-to-date

**Expected outcome:** Page structure includes all expected columns/labels even if no claims are present
**Pass criteria:** Page markup contains text like "Hypothesis", "Verdict", "Control", "Date", "Score-to-date" or equivalent; layout is a grid/list ready to display claims

---

### TC-10 — Evidence badge click links to /evidence (when proven)

**Type:** browser
**Preconditions:** Ledger file contains one PASS entry; frontend and backend are running

**Steps:**
1. Seed the ledger with a PASS entry naming a signal
2. Navigate to `/stocks`
3. Locate a badge that displays "Proven" (for the seeded signal)
4. Click the "Proven" badge

**Expected outcome:** Browser navigates to `/evidence` page; the claim row is visible or highlighted
**Pass criteria:** Click succeeds; page changes to `/evidence`; the backing claim is findable

---

### TC-11 — Evidence fetch failure does not break leaderboard

**Type:** browser
**Preconditions:** Frontend and backend are running; evidence endpoint returns a 500 or timeout

**Steps:**
1. Start backend; seed a condition that causes `/api/evidence` to error (e.g., ledger file permission denied)
2. Navigate to `/stocks`
3. Wait for network requests to settle
4. Inspect the leaderboard

**Expected outcome:** Leaderboard rows and scores are still visible; badges render "Not yet proven" (fallback); no page crash or loading indefinitely
**Pass criteria:** Leaderboard is interactive; badges are present; fetch failure does not cascade to a broken page

---

### TC-12 — Backend unit test: resolve_ledger_path() honors env and config

**Type:** artifact
**Preconditions:** Unit test file exists at `apps/backend/tests/test_evidence.py`

**Steps:**
1. Run: `cd /home/dennis-chan/Git/trendora && python -m pytest apps/backend/tests/test_evidence.py::test_resolve_ledger_path -v`

**Expected outcome:** Test passes; output shows env override is checked first, config default is fallback
**Pass criteria:** Test exit code is 0; log contains assertion that env var takes precedence and config is used when env is absent

---

### TC-13 — Backend unit test: build_evidence_payload handles PASS/FAIL entries

**Type:** artifact
**Preconditions:** Unit test file exists at `apps/backend/tests/test_evidence.py`

**Steps:**
1. Run: `cd /home/dennis-chan/Git/trendora && python -m pytest apps/backend/tests/test_evidence.py::test_build_evidence_payload -v`

**Expected outcome:** Test passes; output shows PASS entries are mapped to proven_signals, FAIL/INSUFFICIENT are not
**Pass criteria:** Test exit code is 0; assertions cover all verdict states; no entries with non-PASS status appear in proven_signals

---

### TC-14 — Frontend component test: EvidenceStatusBadge absent signal

**Type:** artifact
**Preconditions:** Frontend test file exists (e.g., `apps/frontend/components/__tests__/evidence-status-badge.test.tsx` or equivalent)

**Steps:**
1. Run the frontend test suite: `cd /home/dennis-chan/Git/trendora && npm run test -- evidence-status-badge` (or project's test command)

**Expected outcome:** Test passes; output shows badge renders "Not yet proven" when signal is absent from proven map
**Pass criteria:** Test exit code is 0; assertion checks that muted styling is applied; no link is rendered

---

### TC-15 — Frontend component test: EvidenceStatusBadge present signal

**Type:** artifact
**Preconditions:** Frontend test file exists

**Steps:**
1. Run: `cd /home/dennis-chan/Git/trendora && npm run test -- evidence-status-badge` (test for presence case)

**Expected outcome:** Test passes; output shows badge renders "Proven" with a link to `/evidence` when signal is in proven map
**Pass criteria:** Test exit code is 0; assertion checks the "Proven" text and `/evidence` link are rendered; correct icon/styling is applied

---

### TC-16 — Regression: /api/stocks payload is unchanged

**Type:** api
**Preconditions:** Backend is running; a baseline `/api/stocks` response was captured before evidence feature

**Steps:**
1. Execute: `curl -s http://localhost:8000/api/stocks | jq '.stocks[0]' > /tmp/current.json`
2. Compare `current.json` against a baseline snapshot for the three scores (values, not structure)

**Expected outcome:** The Leadership, Entry Quality, and Risk score values in each stock record are byte-identical to the baseline
**Pass criteria:** Stock scores have not been recomputed; they match the baseline; no numerical drift is introduced in the read path

---

### TC-17 — Config file contains typed evidence.ledger_path

**Type:** artifact
**Preconditions:** Config files exist at `apps/backend/app/config.py` and `config.yaml`

**Steps:**
1. Read `apps/backend/app/config.py`; search for class `EvidenceCfg` or a field `evidence: EvidenceCfg`
2. Read `config.yaml`; search for an `evidence:` block with `ledger_path` key

**Expected outcome:** Both files contain the typed config field; the default value in config.yaml matches the spec (runs/goal-session-mcp-loop/state/certified-claims.jsonl)
**Pass criteria:** `config.py` has `EvidenceCfg.ledger_path: str`; `config.yaml` has `evidence.ledger_path` with the correct default

---

### TC-18 — Evidence router is registered in main.py

**Type:** artifact
**Preconditions:** `apps/backend/main.py` exists; `apps/backend/app/api/evidence.py` exists

**Steps:**
1. Read `apps/backend/main.py`
2. Search for `include_router(evidence.router, prefix="/api")`

**Expected outcome:** The evidence router is imported and registered under the `/api` prefix
**Pass criteria:** `import` statement exists for the evidence module; `include_router` call is present with correct prefix

---

### TC-19 — Browser QA: J-01 journey verification

**Type:** browser
**Preconditions:** Frontend and backend are running; full depth phase execution (browser-qa-agent will run)

**Steps:**
1. Visit `/stocks`
2. Observe leaderboard rows
3. Assert every leaderboard row's score area shows an evidence badge ("Proven" or "Not yet proven")
4. Assert at least one badge is present and no displayed score lacks a status

**Expected outcome:** Every score on the leaderboard carries a visible badge; no score is shown without a status
**Pass criteria:** J-01 acceptance criterion met; browser-qa-agent records PASS in test results

---

### TC-20 — Browser QA: J-03 journey verification

**Type:** browser
**Preconditions:** Frontend and backend are running; ledger is empty

**Steps:**
1. Visit `/stocks`; observe badge text on all visible scores
2. Click a stock row; visit `/stocks/{ticker}`; observe badge text on all score cards
3. Assert all badges read "Not yet proven" (never "Proven")

**Expected outcome:** Every badge on both surfaces reads "Not yet proven"; no confident "Proven" number is shown
**Pass criteria:** J-03 acceptance criterion met; browser-qa-agent records PASS

---

### TC-21 — Browser QA: J-05 journey verification

**Type:** browser
**Preconditions:** Frontend and backend are running; /evidence page is reachable

**Steps:**
1. From `/stocks`, click "Evidence" in the nav (≤2 clicks)
2. Assert `/evidence` page renders
3. Assert the honest empty state is displayed ("No certified claims yet...")
4. Inspect markup for claim-row layout (hypothesis, out-of-sample verdict, control comparison, registration date, forward-walk score-to-date)
5. Verify claim→surface linkback is built (check DOM or test harness)

**Expected outcome:** Page is reachable, empty state is honest, layout structure is present, linkback is wired
**Pass criteria:** J-05 acceptance criterion met; browser-qa-agent records PASS; evidence directory has screenshots

---

## Summary

**Total test cases:** 21
**API tests:** 4 (TC-01, TC-02, TC-03, TC-04, TC-16)
**Browser tests:** 12 (TC-05, TC-06, TC-07, TC-08, TC-09, TC-10, TC-11, TC-19, TC-20, TC-21)
**Artifact/Unit tests:** 5 (TC-12, TC-13, TC-14, TC-15, TC-17, TC-18)

**Key coverage:**
- Empty ledger behavior (fail-safe default)
- PASS/FAIL/INSUFFICIENT verdict distinction
- Env and config-driven path resolution
- Frontend badge rendering and linking
- Evidence page structure and empty state
- Regression: scores unchanged
- Full browser journeys (J-01, J-03, J-05)
- Network resilience (fetch failure does not break leaderboard)
