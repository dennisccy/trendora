# Phase goal-ops-hardening-iter-29 — UI Test Plan

**Phase:** goal-ops-hardening-iter-29
**Date:** 2026-07-27
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3255
**Backend URL (referenced by a few steps below):** http://localhost:8000

---

## Scope note

This iteration's user-visible change is a single, passive disclosure: one optional field
(`expectations_status: "unavailable"`) that the existing `/evidence` claim card's drawdown-expectations
panel now renders as a calm inline note when a per-claim compute fails. There is no new page, no new form,
no new button, and no new nav item. Consequently:

- **No Validation-type test case is included.** The Validation category (per
  `.claude/skills/manual-ui-test-plan-generator.md`) applies to forms; this iteration adds/changes no form.
- Coverage instead concentrates on: does the page still load cleanly on the deep basis (smoke/happy-path),
  do the two pre-existing panel states still render byte-unchanged (regression), does the new failure-path
  note render correctly and calmly when triggered (error/ux), and does the secondary consumer
  (`/research/factor-lab`) still show real values after the shared engine rewrite (regression).
- UT-05 requires browser DevTools / network-interception capability to trigger, because today's live
  7-claim ledger has no claim naturally in the "unavailable" state (all 7 currently resolve successfully,
  per `reports/phase-goal-ops-hardening-iter-29-ui-surface-map.md`). It is written for a tester with
  automation/DevTools access, not a plain click-through operator — see
  `reports/phase-goal-ops-hardening-iter-29-what-to-click.md` for the operator-safe subset.

---

## Test Cases

<!-- Test IDs use UT-XX prefix to distinguish from functional test plan TC-XX IDs. -->
<!-- Each test MUST have exact steps and specific expected results. -->

---

### UT-01 — Evidence page loads without errors (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/evidence`

**Preconditions:**
- Frontend is running at http://localhost:3255
- Backend is running (`scripts/start-backend.sh`) and serving the evidence ledger's certified claims
- No login is required (this product has no auth)

**Steps:**
1. Navigate to `http://localhost:3255/evidence`
2. Wait for the page to finish loading (the animated loading-skeleton bars disappear)

**Expected Result:**
- The heading "Evidence" is visible near the top of the page
- No "Backend unavailable" card appears (that state — with the message "The certified-claims ledger could
  not load from the API...") only renders on a fetch failure)
- An element with `data-testid="evidence-claim-list"` is visible, containing one
  `data-testid="evidence-claim-row"` element per certified claim (7 today)
- No blank white page and no Next.js error overlay
- Browser console shows no uncaught errors

---

### UT-02 — Evidence page renders every claim card successfully within its committed budget (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/evidence`

**Preconditions:**
- Same as UT-01
- (Optional sub-check) tester has terminal access to `logs/backend.log`

**Steps:**
1. Navigate to `http://localhost:3255/evidence`
2. Time the interval from navigation until every claim card is fully visible and the loading skeleton is
   gone
3. Count the visible `data-testid="evidence-claim-row"` elements
4. Optional, for testers with terminal access: run
   `grep -i "memoryerror\|exception in asgi" logs/backend.log` scoped to the request window just made

**Expected Result:**
- Every claim in the ledger renders its own card (7 today — if the ledger has grown since this was
  written, "every claim renders, none missing" is the pass condition, not the literal count 7)
- A warm load completes within 3 seconds (committed budget, `reports/perf-budgets.md` Item I: "warm ≤3s
  page"). If this happens to be the very first `/evidence` load after a fresh backfill/dataset change (a
  "cold" miss), a longer one-time wait is expected and documented (up to ~75s in `reports/perf-budgets.md`)
  and is NOT a failure by itself — reload once more afterward and confirm the second load is fast
- No card is replaced by a blank section, a spinner that never resolves, or a crash
- Optional check: zero `MemoryError` / "Exception in ASGI application" lines in `logs/backend.log` for this
  request window

---

### UT-03 — Existing drawdown-expectations table renders unchanged (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/evidence`

**Preconditions:**
- Evidence page loaded per UT-01

**Steps:**
1. On `http://localhost:3255/evidence`, locate the claim card whose title text reads exactly
   `leadership_score`
2. Within that card, scroll to the section below the field grid (Hypothesis / Out-of-sample verdict /
   Control comparison (vs SPY) / Registration date / Forward-walk score-to-date) headed "Historical
   drawdown & dry-spell expectations (…-day hold)"
3. Confirm the section contains a table (`data-testid="evidence-expectations-table"`) with column headers
   "Phase", "Max-DD depth", "Underwater", "Time to recover", "Longest losing streak"
4. Confirm at least one row (`data-testid="evidence-expectations-phase-row"`) shows a real value (a
   percentage or a day-count like "7.4d", not a blank cell) in at least one of the Max-DD depth / Underwater
   / Time to recover columns
5. Scroll through the remaining claim cards (7 total on the page) and confirm each card's own panel area is
   either a complete table (like `leadership_score`'s) or fully blank (no heading, no text at all) — never a
   half-rendered table, a raw error string, or a broken layout

**Expected Result:**
- The `leadership_score` card's table renders exactly as described in steps 3–4, with real figures
- Every other claim card's panel area is in one clean, complete state (table or nothing) — no partial
  rendering, no stack trace or `[object Object]` text, no layout break

---

### UT-04 — Combination and event-study claim cards are unaffected by the accumulator/isolation fix (regression)

**Type:** regression
**Priority:** P2
**Surface:** `/evidence`

**Preconditions:**
- Evidence page loaded per UT-01

**Steps:**
1. On `http://localhost:3255/evidence`, locate the claim card whose bottom-right "Backs:" link
   (`data-testid="evidence-claim-linkback"`) reads exactly "Backs: Multi-factor combination lab →"
2. Confirm this card's field grid (Hypothesis / Out-of-sample verdict / Control comparison (vs SPY) /
   Registration date / Forward-walk score-to-date) is fully populated
3. Locate the claim card whose "Backs:" link reads exactly "Backs: Research event-study lab →"
4. Confirm this card's field grid is likewise fully populated

**Expected Result:**
- Both cards render completely — badge, title, field grid, and whatever drawdown-expectations panel state
  they carry (full table or nothing) — with no crash, no missing field, and no console error
- Neither card looks different from how it is documented to have rendered before this iteration (the
  isolate-and-continue guard only changes behavior on an actual compute failure; a successful compute or a
  pre-existing unresolvable cohort both stay byte-unchanged)

---

### UT-05 — A per-claim compute failure shows the honest "Unavailable" note without breaking other claims (error)

**Type:** error
**Priority:** P2
**Surface:** `/evidence`

**Preconditions:**
- Frontend running at http://localhost:3255; backend running and serving the 7-claim ledger normally
  (confirmed via UT-01)
- Tester has browser DevTools or a network-interception-capable browser-automation tool. This test cannot
  be performed as a plain click-through: today's live ledger has no claim naturally in the "unavailable"
  state (all 7 currently resolve successfully), so the failure must be simulated at the network layer.

**Steps:**
1. Before the page renders its data, set up interception of the `GET http://localhost:8000/api/evidence`
   network response (for example: Chrome DevTools Protocol `Fetch` domain intercepting that URL pattern, or
   a `window.fetch` wrapper injected before the page's own scripts run)
2. In the interception handler, parse the JSON response body, find the object in `claims[]` whose `signal`
   field equals `"leadership_score"`, delete its `expectations` key if present, and set
   `expectations_status: "unavailable"` on that ONE object — leave every other object in `claims[]`
   byte-unchanged
3. Load (or reload) `http://localhost:3255/evidence` so the page fetches and renders the modified response
4. Locate the `leadership_score` claim card and inspect its drawdown-expectations panel section
5. Inspect every other claim card's panel section

**Expected Result:**
- The `leadership_score` card's panel shows an element with `data-testid="evidence-expectations-unavailable"`
  containing the heading "Historical drawdown & dry-spell expectations" (note: no "(…-day hold)" suffix in
  this state, unlike the full-table heading) and the exact text "Unavailable — monitored and refreshed as
  new data arrives."
- No table and no numeric figures appear in that one card's panel section; no crash and no error overlay
  anywhere on the page
- Every other claim card's panel is unaffected — still shows its own normal table or blank state, exactly as
  observed in UT-03/UT-04
- The page as a whole still renders normally (no blank page, no Next.js error overlay) — proving one claim's
  compute failure does not take the others down with it
- Browser console shows no uncaught error

---

### UT-06 — The "Unavailable" note reads as a calm, routine disclosure, never an alarming error (ux)

**Type:** ux
**Priority:** P2
**Surface:** `/evidence`

**Preconditions:**
- UT-05 completed — the `leadership_score` card is currently showing the "Unavailable" note

**Steps:**
1. With the "Unavailable" note visible on the `leadership_score` card, visually compare its text color and
   weight to the "Forward-walk score-to-date" field's "Pending — monitored as new data matures" text earlier
   in the same card
2. Open the browser DevTools Elements panel and inspect the CSS classes on the
   `data-testid="evidence-expectations-unavailable"` element and its children

**Expected Result:**
- The "Unavailable" note is small, muted/faint gray text, visually matching the existing "Pending —
  monitored as new data matures" note's styling — NOT red, NOT bold, and NOT accompanied by a warning/error
  icon
- The element's classes indicate the faint/muted text style (e.g. `text-text-faint`), not any
  danger/warning/red styling, and there is no `AlertTriangle`-style icon inside this note (that icon is
  reserved for the page's actual "Backend unavailable" fetch-failure state, a different, unrelated element)
- The note occupies the same panel slot the full table would have used — no layout shift or broken spacing
  elsewhere on the card

---

### UT-07 — Research Factor Lab still renders real decile and rank-IC values (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/research/factor-lab`

**Preconditions:**
- Frontend running at http://localhost:3255; backend running

**Steps:**
1. Navigate to `http://localhost:3255/research/factor-lab`
2. Wait for the page to load (the all-factors table can take up to roughly a minute on a cold cache — this
   is pre-existing, uncached-by-design Factor Lab behavior, not a regression introduced this iteration)
3. Confirm the table with `data-testid="factors-table"` is visible, with a column headed "Rank-IC (…d)" and
   one row per catalog factor
4. Click anywhere on the row whose "Factor" column shows "vcp_contraction"
   (`data-testid="factor-row-vcp_contraction"`); if that exact factor is not visible, click any other row in
   the table instead
5. Observe the expanded panel that appears directly below the clicked row

**Expected Result:**
- Step 3: the table renders with real numeric values in the "Rank-IC (…d)" and "N" columns for most rows —
  not every cell reading "NA"
- Step 5: a decile grid expands below the clicked row (`data-testid="decile-grid-<factor>"`) showing rows
  D1 through D10, with real numeric forward-return and max-drawdown figures in at least several rows (not
  100% "NA")
- No browser console error ("Uncaught…", "TypeError…") at any point during this test
- No blank table and no crashed page

---

### UT-08 — Evidence and Factor Lab remain reachable within 2 clicks of the Dashboard (ux)

**Type:** ux
**Priority:** P3
**Surface:** navigation / sidebar

**Preconditions:**
- Frontend running at http://localhost:3255

**Steps:**
1. Navigate to `http://localhost:3255/` (the Dashboard)
2. In the left sidebar, confirm a link labeled "Evidence" is visible, then click it
3. Confirm the browser is now at `http://localhost:3255/evidence` with the "Evidence" heading visible
4. Navigate back to `http://localhost:3255/` and click "Research" in the sidebar
5. On the Research hub page, confirm a card titled "Factor Lab" is visible, then click it

**Expected Result:**
- Steps 2–3: clicking "Evidence" in the sidebar (one click from the Dashboard) lands on `/evidence`
- Steps 4–5: clicking "Research" then the "Factor Lab" card (two clicks from the Dashboard) lands on
  `/research/factor-lab`
- Both routes remain reachable in ≤2 clicks, matching the pre-existing Information Architecture — this
  iteration added no new nav item and did not relocate either page

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | Evidence page loads without errors | smoke | P1 | `/evidence` |
| UT-02 | Every claim card renders within budget | happy-path | P1 | `/evidence` |
| UT-03 | Existing drawdown table renders unchanged | regression | P1 | `/evidence` |
| UT-04 | Combination/event-study cards unaffected | regression | P2 | `/evidence` |
| UT-05 | Per-claim failure shows "Unavailable" note, others unaffected | error | P2 | `/evidence` |
| UT-06 | "Unavailable" note styled calmly, not as an error | ux | P2 | `/evidence` |
| UT-07 | Factor Lab still shows real decile/rank-IC values | regression | P1 | `/research/factor-lab` |
| UT-08 | Evidence + Factor Lab reachable in ≤2 clicks | ux | P3 | navigation / sidebar |

**P1 tests must all pass for browser QA verdict to be PASS.** (UT-01, UT-02, UT-03, UT-07)

No Validation-type test case exists this iteration — no form was added or changed (see "Scope note" above).
