# Phase goal-mcp-loop-iter-32 — UI Test Plan

**Phase:** goal-mcp-loop-iter-32 (goal mode, journey J-17 / backlog B-903, + J-19 close-out)
**Date:** 2026-07-14
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3255 (this run's offset port — `scripts/dev.sh` moves to 8255/3255
when the defaults 8000/3000 are occupied; substitute your actual running port if different)
**Backend URL:** http://localhost:8255 (health check: `GET /api/health`)

---

## Baseline Data Assumptions

Every exact number in this plan (7 canonical trials, `required_p = 0.00625`, Thresholdout remaining
`0.9`, staging level `≈0.0003926`, 11 registry rows, 7 all-FAIL evidence claims) is the live value
confirmed by the dev handoff's end-to-end smoke test on 2026-07-14, against the real, untouched
ledgers (`certified-claims.jsonl`, `staging-ledger.jsonl`, `pre-registrations.jsonl` are byte-identical
before/after this iteration — no `## Evidence Claim` was submitted). These should still hold at test
time. If a later, unrelated iteration has legitimately added a trial before you run this plan, treat
each figure's **internal consistency** (e.g. `required_p` headline = `0.05 ÷` the trial number named in
its own subtext) as the pass condition instead of the literal digit — do not fail a test solely because
the ledger has grown.

---

## Test Cases

<!-- Test IDs use UT-XX prefix to distinguish from functional test plan TC-XX IDs. -->
<!-- Each test has exact steps and specific expected results — no vague "test the form" / "verify it works". -->

---

### UT-01 — `/research/budget` loads directly without errors (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/research/budget`

**Preconditions:**
- Frontend is running at http://localhost:3255
- Backend is running and reachable (http://localhost:8255/api/health returns `"readiness":"ready"`)
- No login is required (read-only page, no auth anywhere in this product)

**Steps:**
1. Navigate to `http://localhost:3255/research/budget`
2. Observe the page immediately after navigation
3. Wait up to 3 seconds for the page to finish loading

**Expected Result:**
- Immediately after navigating, four placeholder cards with a pulsing/shimmering animation appear (the loading skeleton) — never a blank white page
- Within a few seconds the placeholders are replaced by four real stat cards laid out in a row/grid
- The page heading reads "Certification-budget accounting", with a "Back to Research" link above it
- No browser error page, no "Application error" text, no unhandled-exception overlay appears
- Opening the browser console (F12 → Console tab) shows no red error messages

---

### UT-02 — `/research` hub still loads with the 3-card governance grid (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/research`

**Preconditions:**
- Frontend is running at http://localhost:3255

**Steps:**
1. Navigate to `http://localhost:3255/research`
2. Scroll down past the main "Research" lab grid to the "Governance & process" section

**Expected Result:**
- Page heading "Research" is visible at the top
- A section labeled "Governance & process" is visible below the main lab grid
- Exactly 3 cards appear in that section, in this left-to-right / top-to-bottom order: "Pre-registration registry", "Negative-results graveyard", "Certification-budget accounting"
- The third card shows a wallet-shaped icon on the left of its title and an arrow icon on the right
- No blank page, no error message, no missing card

---

### UT-03 — No "Proven"/"Not yet proven" badge language appears on the budget panel (smoke — critical anti-goal)

**Type:** smoke
**Priority:** P1
**Surface:** `/research/budget`

**Preconditions:**
- Frontend and backend running; `/research/budget` fully loaded (per UT-01)

**Steps:**
1. Navigate to `http://localhost:3255/research/budget`
2. Wait for the four-card grid to finish loading
3. Read the page heading, the one-line description directly beneath it, and all four card titles / headline values / subtext lines

**Expected Result:**
- The exact capitalized badge-style text **"Proven"** does NOT appear anywhere on the page
- The exact capitalized badge-style text **"Not yet proven"** does NOT appear anywhere on the page
- **Important nuance:** the page's own description line legitimately contains the lowercase phrase "…nothing here is a proven/not-proven signal" as a disclaimer. This is expected and is **not** a failure — it is denying, not claiming, proven-ness. Only a capitalized "Proven" or "Not yet proven" **status label/badge** (the kind seen on `/evidence` or `/stocks`) would be a failure here.
- All four card values (trial counts, `required_p`, budget remaining, staging level) read as plain numbers/formulas with no proven/unproven claim attached to any of them

---

### UT-04 — Budget panel is discoverable from the Research hub in ≤2 clicks (happy-path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/research` → `/research/budget`

**Preconditions:**
- Frontend running at http://localhost:3255
- Starting from any page (e.g. the dashboard)

**Steps:**
1. Navigate to `http://localhost:3255`
2. Click "Research" in the left sidebar (Microscope icon, seventh item down)
3. On the `/research` page, scroll to "Governance & process" and click the "Certification-budget accounting" card (the third card, Wallet icon)

**Expected Result:**
- After step 2: URL is `http://localhost:3255/research`, heading "Research" is visible
- After step 3: URL is `http://localhost:3255/research/budget`, heading "Certification-budget accounting" is visible
- Total clicks from the dashboard: exactly 2 ("Research" in the sidebar, then the budget card) — no intermediate page, no extra click needed

---

### UT-05 — All four budget figures display the correct values and explanatory subtext (happy-path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/research/budget`

**Preconditions:**
- Frontend and backend running
- Baseline ledger state: 7 canonical trials, 7 staging trials (see "Baseline Data Assumptions" above)

**Steps:**
1. Navigate to `http://localhost:3255/research/budget`
2. Wait for the four-card grid to load
3. Read the headline value and subtext line on each of the four cards

**Expected Result:**
- Card "Total trials to date": headline reads **"7"**; subtext reads **"Next canonical trial will be #8"**
- Card "Current canonical required p": headline reads **"0.00625"**; subtext reads **"= 0.05 ÷ 8 (Bonferroni)"**
- Card "Thresholdout budget remaining": headline reads **"0.9"**; subtext reads **"of 1 total · spent 0.1"**
- Card "Staging LORD++ next-trial level": headline reads **"0.0003926"**; subtext reads **"trial #8 of the internal staging economy"**
- (See "Baseline Data Assumptions" for the fallback consistency check if the ledger has legitimately grown since this plan was written)

---

### UT-06 — Spend-over-time sparklines render on all four cards (happy-path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/research/budget`

**Preconditions:**
- Frontend and backend running; budget panel loaded (baseline: 7 trials on each ledger)

**Steps:**
1. Navigate to `http://localhost:3255/research/budget`
2. Wait for the four-card grid to load
3. Look at the bottom of each of the four cards, below the subtext, for a small trend-line graphic

**Expected Result:**
- All four cards show a small line-and-dot graphic (a sparkline) below the subtext — none show the placeholder text "No trials yet" in its place
- The "Total trials to date" card's sparkline is a generally rising line (trial numbers only ever increase)
- The "Current canonical required p" card's sparkline generally trends downward (the significance bar tightens as trials accumulate)
- No sparkline renders as a single flat dot, a visibly broken shape, or is missing entirely

---

### UT-07 — Card subtext explains each figure in plain language (ux)

**Type:** ux
**Priority:** P2
**Surface:** `/research/budget`

**Preconditions:**
- Budget panel loaded

**Steps:**
1. Navigate to `http://localhost:3255/research/budget`
2. Read each card's title and subtext line without any outside explanation

**Expected Result:**
- Each card's title is a plain-English label (e.g. "Total trials to date"), never a raw code/variable name (e.g. not "n_trials_to_date")
- Each subtext line explains the number in words or a simple formula (e.g. "= 0.05 ÷ 8 (Bonferroni)"), never raw JSON or an unexplained code
- Someone unfamiliar with the codebase can tell, from the card alone, roughly what the number means (a trial count, a probability bar, a remaining budget, a staging-only figure)
- The page's subtitle line makes clear this is accounting information, never a prediction, recommendation, or order

---

### UT-08 — Thresholdout sparkline visually reflects discrete spend events, not a smooth trend (ux — informational)

**Type:** ux
**Priority:** P3
**Surface:** `/research/budget`

**Preconditions:**
- Budget panel loaded; baseline ledger has exactly 2 trials (of 7) that actually charged Thresholdout alpha

**Steps:**
1. Navigate to `http://localhost:3255/research/budget`
2. Look closely at the sparkline on the "Thresholdout budget remaining" card only (the third card)

**Expected Result:**
- The line is mostly flat/level with two visible upward steps or spikes (the two trials that actually spent alpha), rather than a smooth, continuously rising or falling curve
- This is a best-effort visual check at a small (120×32px) size — if you genuinely cannot distinguish the shape, treat the result as inconclusive rather than a failure; this check is P3/informational only, not a blocking pass/fail gate

---

### UT-09 — Backend-unavailable state shows a contained error card with navigation intact (error)

**Type:** error
**Priority:** P2
**Surface:** `/research/budget`

**Preconditions:**
- Frontend running at http://localhost:3255
- Backend service stopped or otherwise made unreachable (ask whoever manages this test environment to stop it if you cannot do so yourself)

**Steps:**
1. With the backend stopped, navigate to `http://localhost:3255/research/budget`
2. Wait a few seconds for the fetch attempt to fail
3. Observe the page

**Expected Result:**
- A single card with a red/warning-colored left border and an alert-triangle icon appears in place of the four-card grid
- The card reads **"Backend unavailable"**, with a line underneath explaining the panel could not load and to confirm the backend is running
- The "Back to Research" link at the top of the page is still visible and clickable
- No blank white page, no browser crash screen, no unhandled-exception overlay

---

### UT-10 — Budget panel recovers once the backend is back (error)

**Type:** error
**Priority:** P2
**Surface:** `/research/budget`

**Preconditions:**
- Continuing directly from UT-09 (page currently showing "Backend unavailable")

**Steps:**
1. Restart/restore the backend service
2. Refresh the `/research/budget` page (F5 or Cmd+R)

**Expected Result:**
- The loading skeleton (4 placeholder cards) appears briefly
- The real four-card grid returns with the same values seen before the outage (see UT-05)
- The red "Backend unavailable" card is gone

---

### UT-11 — J-19: graveyard → registry lineage link scrolls the target row into view (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/research/graveyard` → `/research/registry`

**Preconditions:**
- Frontend and backend running
- `/research/graveyard` has at least one row whose "Lineage" column (rightmost) shows a clickable accent-colored link ending in "→", not the gray text "No registration lineage"

**Steps:**
1. Navigate to `http://localhost:3255/research/graveyard`
2. Wait for the table to load
3. In the "Lineage" column, find any row showing a clickable link (an id followed by "→")
4. Click that lineage link

**Expected Result:**
- The browser navigates to `http://localhost:3255/research/registry#registration-<id>` (the URL now ends with a `#registration-` fragment)
- The page visibly scrolls down on its own — the matching registry row is already in view once the page settles, positioned just below the sticky header, **without** you needing to scroll manually to find it
- If devtools is open, typing `window.scrollY` into the Console tab returns a number greater than 0, confirming the page did not stay at the very top
- **What "broken" looks like:** landing on `/research/registry` at the very top of the page (as if no anchor were present) and having to scroll manually to find the row — this is exactly the regression this iteration re-verifies is fixed

---

### UT-12 — J-18: `/research/registry` unaffected — 11 rows, 5 columns, `ma_stack` shows "closed" (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/research/registry`

**Preconditions:**
- Frontend and backend running
- Baseline registry state: 11 registrations

**Steps:**
1. Navigate to `http://localhost:3255/research/registry`
2. Wait for the table to load
3. Count the column headers in the table
4. Count the data rows in the table
5. Find the row whose Selectors chips mention "ma_stack" and read its Status badge (rightmost column)

**Expected Result:**
- Column headers read exactly, left to right: **"Selectors", "Rationale", "Registered", "Source", "Status"** (5 columns)
- 11 data rows are present
- The `ma_stack` row's Status badge reads **"closed"**
- No error card, no blank table

---

### UT-13 — J-05/J-06/J-08/J-09: `/evidence` unaffected — FAIL claims still render correctly (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/evidence`

**Preconditions:**
- Frontend and backend running
- Baseline ledger: 7 certified claims, all currently FAIL (none PASS)

**Steps:**
1. Navigate to `http://localhost:3255/evidence`
2. Wait for the claim list to load
3. Count the claim cards on the page
4. Find the card whose title contains "vcp_contraction — top decile" and read its verdict badge (top-left of the card)
5. Find the card whose title contains "×" and the word "composite" (the multi-factor combination row) and read its verdict badge

**Expected Result:**
- 7 claim cards are rendered (matching the 7 canonical trials shown on the budget panel)
- Every visible verdict badge reads **"FAIL"** — none read "PASS"
- The vcp_contraction card's badge reads "FAIL"
- The combination ("× … composite") card's badge reads "FAIL"
- No card anywhere on the page shows the accent-colored "Proven" badge
- No blank page, no error card

---

### UT-14 — J-01: `/stocks` leaderboard unaffected — loads without crash, evidence badges visible (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/stocks`

**Preconditions:**
- Frontend and backend running

**Steps:**
1. Navigate to `http://localhost:3255/stocks`
2. Wait for the leaderboard table to finish loading
3. Inspect the first 5 stock rows for small badges next to the Leadership, Entry quality, and Risk scores
4. Open the browser console (F12) and check for red error messages

**Expected Result:**
- The leaderboard renders with stock rows and score columns — no blank page, no crash screen
- Each of the first 5 rows shows 3 small badges (one per score) reading **"Not yet proven"** (muted/gray, shield icon) — none read "Proven" (the ledger currently has 0 PASS entries)
- No red errors in the browser console

---

## Validation — Not Applicable This Iteration

`/research/budget` is a strictly read-only accounting panel: no forms, no inputs, no mutations, no user
actions beyond navigation (confirmed in the phase spec's "New user actions: none beyond navigation" and
the dev handoff). There is no field to submit invalid data into, so no validation-type test case applies
this iteration — this is a deliberate omission, not an oversight.

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | Budget page loads without errors | smoke | P1 | `/research/budget` |
| UT-02 | Research hub shows 3-card governance grid | smoke | P1 | `/research` |
| UT-03 | No "Proven"/"Not yet proven" badge language | smoke | P1 | `/research/budget` |
| UT-04 | Discoverable in ≤2 clicks from Research hub | happy-path | P1 | `/research` → `/research/budget` |
| UT-05 | Four figures show correct values + subtext | happy-path | P1 | `/research/budget` |
| UT-06 | Sparklines render on all four cards | happy-path | P1 | `/research/budget` |
| UT-07 | Card subtext is plain-language, not code | ux | P2 | `/research/budget` |
| UT-08 | Thresholdout sparkline shows discrete spend events | ux | P3 | `/research/budget` |
| UT-09 | Backend-unavailable shows contained error card | error | P2 | `/research/budget` |
| UT-10 | Panel recovers once backend is back | error | P2 | `/research/budget` |
| UT-11 | J-19 lineage link scrolls target row into view | regression | P1 | `/research/graveyard` → `/research/registry` |
| UT-12 | J-18 registry unaffected (11 rows / 5 cols / ma_stack) | regression | P1 | `/research/registry` |
| UT-13 | J-05/06/08/09 evidence FAIL claims unaffected | regression | P1 | `/evidence` |
| UT-14 | J-01 stocks leaderboard unaffected | regression | P1 | `/stocks` |

**P1 tests must all pass for browser QA verdict to be PASS.** (10 of 14 tests are P1 this iteration,
reflecting that both J-17's new capability and four named "required-still-passing" journeys — J-18,
J-05/06/08/09, J-01 — plus the J-19 close-out are all DoD-blocking, not merely informational.)
