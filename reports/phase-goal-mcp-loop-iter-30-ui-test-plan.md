# Phase goal-mcp-loop-iter-30 — UI Test Plan

**Phase:** goal-mcp-loop-iter-30
**Date:** 2026-07-13
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3255 (backend: http://localhost:8255)

---

## Context for the tester

This iteration ships J-18 / backlog B-901 — the pre-registration registry. One brand-new read-only page
(`/research/registry`), one small addition to the existing `/research` hub, and one backend-only
certification-gate check that has **no browser surface at all**.

**What this plan covers:** the browser-visible half — the new page, its states, and the two places a
shared-file change could have broken something that already worked (`/research`'s existing lab grid and
`/evidence`, both downstream of `apps/backend/main.py`'s new router registration).

**What this plan deliberately does NOT cover** (per the phase spec's own testing-requirements split): the
gate's registered/unregistered/near-miss/enforcement-off behavior in `project-extensions/gates/verify_claim.py`
is a CLI/backend mechanism with **no UI, ever, by design** — it is fixture-proven in
`apps/backend/tests/test_gate_registry_enforcement.py`, not browser-testable. Do not attempt to click
through a "claim gets refused" flow in the browser; there is nothing there to click. Likewise this plan does
not duplicate the API/artifact-level checks already in `reports/qa/goal-mcp-loop-iter-30-test-plan.md`
(TC-04 through TC-10, TC-13 through TC-15: loader/endpoint fixtures, gate fixtures, ledger byte-identity
checksums) — those need a test harness, not a browser. This plan's UT-01/02/03/07 are the human-precision
version of that functional plan's TC-01/02/03/11; UT-08/09/10 cover the regression + discoverability ground
its TC-03 gestured at more loosely.

**Operational preconditions for every test below:**
- Both services running in **prod mode** with a fresh build — run `rm -rf apps/frontend/.next` and restart
  both `scripts/start-backend.sh` and `scripts/start-frontend.sh` before this pass if either service has
  been up since before this iteration's code landed (iter-13/20/22 lesson: a stale `.next` build would
  serve a 404 for the brand-new `/research/registry` route instead of the real page).
- No login/authentication exists in this product — nothing to sign in as.
- The backfilled registry file `runs/goal-session-mcp-loop/state/pre-registrations.jsonl` (11 rows) must be
  present at its normal path for UT-01 through UT-05 and UT-07 through UT-10 (only UT-06 intentionally
  removes it).
- `evidence.registry.enforce: true` in `config.yaml` has no bearing on anything in this plan — enforcement
  only affects the CLI gate, never a page a browser loads.

---

## Test Cases

<!-- Test IDs use UT-XX prefix to distinguish from functional test plan TC-XX IDs. -->
<!-- Each test MUST have exact steps and specific expected results. -->

---

### UT-01 — `/research/registry` loads directly with all structural elements present (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/research/registry`

**Preconditions:**
- Backend and frontend running per the Operational preconditions above.
- Registry file present with its 11 backfilled rows.

**Steps:**
1. Navigate directly to `http://localhost:3255/research/registry` (do not go through the hub first).
2. Wait up to 10 seconds for the page to finish loading.

**Expected Result:**
- A "Back to Research" link with a left-arrow icon appears above the title.
- The heading "Pre-registration registry" is visible.
- Below it, subtitle text beginning "Every hypothesis the system has ever registered or tested — its
  selectors, economic rationale, and audit-trail date." is visible.
- A table renders with exactly 5 column headers, in this exact left-to-right order: "Selectors",
  "Rationale", "Registered", "Source", "Status".
- No blank white page, no browser "can't reach this page" error, no unhandled application-error page.
- No JavaScript console error.

---

### UT-02 — CENTERPIECE: Registry is discoverable from the Research hub and displays all 11 registered hypotheses (happy-path, J-18 step 1)

**Type:** happy-path
**Priority:** P1
**Surface:** `/research` → `/research/registry`

**Preconditions:**
- Backend and frontend running; registry file present with 11 rows.

**Steps:**
1. Navigate to `http://localhost:3255/research`.
2. Confirm the heading "Research" renders with its existing grid of lab cards above the fold.
3. Scroll down past the last lab card.
4. Confirm a heading "Governance & process" appears, and directly below it exactly one card titled
   "Pre-registration registry" (with a book icon).
5. Read the card's description text and confirm it ends with the exact words "The gate refuses to certify
   anything that isn't here."
6. Click the "Pre-registration registry" card.
7. Confirm the browser navigates to `http://localhost:3255/research/registry` with no `?asof=` query
   string appended (a plain, clean URL at the live/default date).
8. Wait for the table to finish loading.
9. Count the number of data rows in the table (excluding the header row).
10. For each of the 11 rows, confirm the Selectors, Rationale, Registered, Source, and Status cells are ALL
    non-empty — none reads "—" or is blank.

**Expected Result:**
- Exactly one click from `/research` reaches `/research/registry` (2 clicks total starting from the
  Dashboard, per UT-10).
- The table shows **exactly 11 rows**.
- Every one of the 11 rows has real, non-empty content in all 5 columns.
- The Registered column shows a `yyyy-mm-dd`-formatted date for every row (all 11 currently read
  `2026-07-03`) — never a raw ISO timestamp, never "Invalid Date".

---

### UT-03 — Selectors render as readable key=value chips, never raw JSON (validation)

**Type:** validation
**Priority:** P2
**Surface:** `/research/registry`

**Preconditions:**
- Registry page loaded with all 11 rows visible (UT-01/UT-02 pass).

**Steps:**
1. On `/research/registry`, locate the row whose Rationale text begins "Does the post-contraction
   expansion edge persist/strengthen over a quarter?".
2. Inspect that row's Selectors cell.
3. Locate the row whose Rationale text begins "Momentum leadership that is NOT volatile/extended".
4. Inspect that row's Selectors cell.

**Expected Result:**
- Row from step 1 (the vcp_contraction h60 factor claim): the Selectors cell shows **6 separate small
  pill-shaped chips**, reading exactly `decile=10`, `direction=positive`, `factor=vcp_contraction`,
  `horizon=60`, `kind=factor`, `slice_kind=decile` — no `{`, `}`, or raw JSON text visible anywhere in the
  cell.
- Row from step 3 (the combination claim): the Selectors cell shows 5 chips including one reading exactly
  `condition=rs_spy_3m:top:quintile+atr_pct:bottom:tertile` — the two condition legs joined by a single
  `+` sign, never displayed as a bracketed array (`[...]`) or with a comma between them. The other chips
  read `cohort=composite`, `direction=positive`, `horizon=20`, `kind=combination`.
- Neither cell shows a raw `{...}` object dump anywhere.

---

### UT-04 — Status column uses neutral, vocabulary-only badges; every row is labeled "backfill" (validation, anti-goal-1 spirit check)

**Type:** validation
**Priority:** P2
**Surface:** `/research/registry`

**Preconditions:**
- Registry page loaded with all 11 rows visible.

**Steps:**
1. Locate the row whose Rationale text begins "Moving-average-stack (price stacked above its short/long
   moving averages)".
2. Read that row's Status badge text.
3. Read every one of the other 10 rows' Status badge text.
4. For all 11 rows, look immediately beside the Status badge for a second, smaller badge.
5. Note the color/style of the Status and second badges (gray/muted vs. green/red).
6. Read the page's title and subtitle text, and skim every row's Source column text.

**Expected Result:**
- The `ma_stack` row's (step 1) Status badge reads exactly `closed`.
- All other 10 rows' Status badges read exactly `tested`.
- No badge anywhere on this page reads "Proven", "Not yet proven", "PASS", "FAIL", or any confidence
  wording — the only two values in the Status column across all 11 rows are `tested` and `closed`.
- Every one of the 11 rows shows a second, smaller badge reading `backfill` immediately beside its Status
  badge (all 11 rows were constructed by backfilling the ledgers).
- Both badges render in a plain neutral gray/muted style (light gray background, muted-gray text) — this
  must look visually distinct from `/evidence`'s colored PASS (accent) / FAIL (red) verdict badges, never
  green or red here.
- **Note for the tester:** several Source-column cells legitimately contain the word "certified" as part of
  a filename citation (e.g. "certified-claims.jsonl (original canonical claim; predates
  proposer-guidance.md §4.x)"). That is an honest provenance citation, not a proven-language claim about the
  hypothesis — do not flag it. Only a colored/confidence-worded **badge** or headline claiming proven-ness
  would be a real anti-goal violation, and none should appear.

---

### UT-05 — Backend unavailable degrades to one contained error card, not a blank crash (error)

**Type:** error
**Priority:** P1
**Surface:** `/research/registry`

**Preconditions:**
- Registry page previously loaded successfully at least once.
- Operator has the ability to stop the backend process.

**Steps:**
1. With the backend running, load `http://localhost:3255/research/registry` and confirm the table renders
   (per UT-01).
2. Stop the backend process.
3. Reload the page (F5).
4. Observe the result.
5. Restart the backend afterward and confirm the page recovers on a subsequent reload.

**Expected Result:**
- Step 4: a single card appears reading "Backend unavailable" with body text "The pre-registration
  registry could not load from the API. Confirm the backend is running and reload."
- The card has a red-tinted border and a warning-triangle icon.
- The "Pre-registration registry" heading and "Back to Research" link still render above the error card —
  the error is contained to the data area, not a full-page takeover.
- No blank white page, no browser network-error page, no unhandled JavaScript error overlay.
- The left sidebar navigation remains visible and every link in it stays clickable.
- Step 5: once the backend is back up, reloading shows the populated 11-row table again with no leftover
  error card.

---

### UT-06 — Missing registry file shows an honest empty state, not a crash (error, data-shape resilience)

**Type:** error
**Priority:** P1
**Surface:** `/research/registry`

**Preconditions:**
- Backend running and reachable.
- Operator has filesystem access to
  `runs/goal-session-mcp-loop/state/pre-registrations.jsonl` (relative to the repo root).

**Steps:**
1. Rename the file: `mv runs/goal-session-mcp-loop/state/pre-registrations.jsonl
   runs/goal-session-mcp-loop/state/pre-registrations.jsonl.bak`. (No backend restart is required — the
   loader re-reads the file fresh on every request, so the very next page load already reflects the
   missing file.)
2. Navigate to `http://localhost:3255/research/registry` (or reload if already open).
3. Observe the result.
4. Rename the file back immediately: `mv runs/goal-session-mcp-loop/state/pre-registrations.jsonl.bak
   runs/goal-session-mcp-loop/state/pre-registrations.jsonl`.
5. Reload the page again to confirm normal data returns.

**Expected Result:**
- Step 3: a card appears with a book icon and heading "No registrations yet", with body text beginning
  "Nothing is registered yet. Once a hypothesis is registered, it appears here with its selectors,
  rationale, registration date, and source".
- This is a calm, honest empty-state card — NOT a "Backend unavailable" error card, NOT a blank page, NOT
  a crash/500 page.
- The page's own heading/subtitle still render above the empty-state card.
- Step 5: the real 11-row table reappears exactly as before, confirming the file rename/restore round-trips
  cleanly with no leftover empty-state card and no stale cache.

---

### UT-07 — Loading skeleton renders honestly before data arrives, then is fully replaced (smoke)

**Type:** smoke
**Priority:** P2
**Surface:** `/research/registry`

**Preconditions:**
- Backend and frontend running normally.
- Browser DevTools available for network throttling.

**Steps:**
1. Open DevTools → Network tab → set throttling to "Slow 3G" (or similar).
2. Navigate to `http://localhost:3255/research/registry`.
3. Immediately observe the page before the data finishes loading.
4. Wait for the fetch to complete, then observe again.
5. Turn network throttling back off.

**Expected Result:**
- Step 3: a card containing **8 pulsing gray placeholder bars** is visible in place of the table — no
  flash of an empty table, no "No registrations yet" card shown prematurely.
- Step 4: once the fetch completes, the skeleton is fully replaced by the real 11-row table — no skeleton
  bars remain visible alongside or after the loaded data.

---

### UT-08 — Existing Research hub lab grid is completely unchanged (regression)

**Type:** regression
**Priority:** P2
**Surface:** `/research`

**Preconditions:**
- Frontend running.

**Steps:**
1. Navigate to `http://localhost:3255/research`.
2. Count the cards in the main grid **above** the new "Governance & process" heading.
3. Read each card's title, top to bottom / left to right.

**Expected Result:**
- Exactly **10 cards**, in this exact reading order: "Factor Lab", "Regime Lab", "Market Phase & Severity
  Lab", "Regime × Phase × Factor", "Regime × Setup × Pattern", "Severity-velocity × Regime", "Multi-factor
  combination", "Setup & Pattern event study", "Recovery-Turn Edge", "Downtrend Opportunity".
- No 11th card mixed into this grid, no card removed, reordered, or renamed — the "Pre-registration
  registry" card appears ONLY in the separate "Governance & process" section below this grid, never inside
  it.

---

### UT-09 — Evidence page renders unaffected — confirms the new router wiring did not break app startup (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/evidence`

**Preconditions:**
- Backend running and reachable.

**Steps:**
1. Navigate to `http://localhost:3255/evidence`.
2. Wait for the page to load.
3. Count the number of claim cards rendered.
4. Read the verdict badge on each of the 7 claim cards.

**Expected Result:**
- URL is `http://localhost:3255/evidence`; heading "Evidence" renders with subtitle text beginning "The
  certified-claims ledger — the single source of proven-ness."
- Exactly **7 claim cards** render — NOT the "No certified claims yet" empty state, NOT a "Backend
  unavailable" error card.
- Every one of the 7 claim cards shows a red **"FAIL"** verdict badge (all 7 certified claims remain FAIL
  per the frozen, byte-identical ledger) — none shows "PASS" or "INSUFFICIENT".
- No console error. A clean load here confirms `apps/backend/main.py`'s new
  `registry.router` registration (added beside the pre-existing `evidence.router` line) did not break
  backend startup or this pre-existing page — the one shared-file regression risk this iteration touches.

---

### UT-10 — Registry is discoverable within 2 clicks from the Dashboard, with a clear label (ux)

**Type:** ux
**Priority:** P2
**Surface:** navigation / `/research`

**Preconditions:**
- Frontend running; start from the Dashboard.

**Steps:**
1. Navigate to `http://localhost:3255/` (Dashboard).
2. Look at the left sidebar navigation and locate "Research" (microscope icon, 7th item).
3. Click "Research".
4. On `/research`, scroll to the "Governance & process" heading without using browser find/search.
5. Read the "Pre-registration registry" card's title and one-line description.
6. Click the card.

**Expected Result:**
- Step 3 navigates to `http://localhost:3255/research` — **click 1**.
- The "Governance & process" heading and its single card are visible directly below the main lab grid on
  ordinary scroll — not hidden in a submenu, tab, or collapsed section.
- The card's title "Pre-registration registry" and its description are in plain, readable language (no
  internal jargon like "selector-set" or "cross-check") — a first-time user can tell what the page contains
  before clicking.
- Step 6 navigates to `http://localhost:3255/research/registry` — **click 2**. Total: 2 clicks from the
  Dashboard, meeting the "reachable in ≤2 clicks" requirement.
- The left sidebar itself gained no new entry and no reordering — "Research" is the same single entry it
  was before this iteration (Dashboard, Stocks, Themes, Sectors, Scanner Runs, Backtest, **Research**,
  Evidence, Watchlist, Methodology, Data Manager).

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | `/research/registry` loads directly, structure present | smoke | P1 | `/research/registry` |
| UT-02 | CENTERPIECE: discover from hub + all 11 rows populated (J-18 step 1) | happy-path | P1 | `/research` → `/research/registry` |
| UT-03 | Selectors render as chips, never raw JSON | validation | P2 | `/research/registry` |
| UT-04 | Status badges neutral + vocabulary-only + "backfill" label | validation | P2 | `/research/registry` |
| UT-05 | Backend unavailable → one contained error card | error | P1 | `/research/registry` |
| UT-06 | Missing file → honest empty state, no crash | error | P1 | `/research/registry` |
| UT-07 | Loading skeleton (8 bars) shown, then fully replaced | smoke | P2 | `/research/registry` |
| UT-08 | Existing 10-lab grid completely unchanged | regression | P2 | `/research` |
| UT-09 | `/evidence` unaffected — 7 FAIL claims, confirms router wiring safe | regression | P1 | `/evidence` |
| UT-10 | Discoverable in ≤2 clicks from Dashboard, clear label | ux | P2 | nav / `/research` |

**P1 tests must all pass for browser QA verdict to be PASS:** UT-01, UT-02, UT-05, UT-06, UT-09. UT-02 is
the actual J-18 DoD proof (discoverability + all 11 rows correctly populated) and is the centerpiece of this
plan. UT-05/UT-06 are elevated to P1 because they directly exercise the phase spec's CRITICAL anti-goal on
data-shape/service-failure resilience ("the UI degrades gracefully... never a blank application-error
page"). UT-09 is elevated to P1 because it is the single named shared-file regression risk
(`apps/backend/main.py`'s new router registration) — a failure there would mean the whole backend failed to
start, not just this iteration's own feature.

**Not covered here** (see `reports/qa/goal-mcp-loop-iter-30-test-plan.md` instead): the gate's
registered/unregistered/near-miss/enforcement-off cross-check (TC-05 through TC-08 — CLI/fixture-only, no
UI exists or will ever exist for it), the loader/endpoint single-source byte-comparison (TC-09), the
missing-file loader-level unit test (TC-10), the backfill round-trip proof (TC-13), the registry-file
status-vocabulary artifact check (TC-14), and the pre/post ledger checksum diff (TC-15).
