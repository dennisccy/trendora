# Phase goal-mcp-loop-iter-31 — UI Test Plan

**Phase:** goal-mcp-loop-iter-31
**Date:** 2026-07-13
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3255 (backend: http://localhost:8255)

---

## Context for the tester

This iteration ships J-19 / backlog B-902 — the negative-results graveyard. One brand-new read-only page
(`/research/graveyard`), one small addition to the existing `/research` hub, and one small presentation-only
addition to the existing `/research/registry` page (a per-row anchor so a graveyard Lineage link can land
precisely on its backing row).

**What this plan covers:** the browser-visible half — the new page and its four states (loaded / loading /
error / empty), the hub card, the cross-page Lineage link, and the two places a shared code/file change
could have broken something that already worked (`/research/registry`'s normal browsing, and `/evidence`'s
shared canonical-ledger read path via `apps/backend/main.py`'s new router registration).

**What this plan deliberately does NOT cover** (per the phase spec's own testing-requirements split, and to
avoid duplicating `reports/qa/goal-mcp-loop-iter-31-test-plan.md`):
- The **honest-null lineage** path (a ledger entry whose selectors match no registration renders "No
  registration lineage" instead of a link). Every one of the 14 real entries today IS matched — the iter-30
  backfill is complete — so this path has no live-data trigger and is fixture-proven only in
  `apps/backend/tests/test_graveyard.py`. Do not go hunting for an unmatched row; there isn't one.
- API-level single-source equality (`GET /api/research/graveyard` payload equals `build_graveyard_payload()`
  called directly — TC-16), the drift-insurance `_CLAIM_SELECTOR_KEYS` equality assertion (TC-21, code-level
  only), the required-still-passing journey pytest replay (TC-18), and the pre/post ledger byte-identity
  hashing (TC-19) — these need a test harness or source access, not a browser.
- A PASS entry being excluded from the graveyard (TC not applicable live — all 14 real entries are FAIL
  today; the status-driven filter is proven by fixture, not live data).

**Operational preconditions for every test below:**
- Both services running in **prod mode** with a fresh build — run `rm -rf apps/frontend/.next` and restart
  both `scripts/start-backend.sh` and `scripts/start-frontend.sh` before this pass if either service has
  been up since before this iteration's code landed (iter-13/20/22 lesson, restated in this iteration's own
  spec: never accept a stale cached build as "ready to ship").
- No login/authentication exists in this product — nothing to sign in as.
- Both real ledgers must be present at their normal paths for every test EXCEPT UT-10 (which intentionally
  removes them): `runs/goal-session-mcp-loop/state/certified-claims.jsonl` (7 rows, all `FAIL`) and
  `runs/goal-session-mcp-loop/state/staging-ledger.jsonl` (7 rows, all `FAIL`).
- `runs/goal-session-mcp-loop/state/pre-registrations.jsonl` (11 backfilled rows) must be present so all 14
  graveyard rows resolve real lineage, including `ma_stack`'s `closed` status.

---

## Test Cases

<!-- Test IDs use UT-XX prefix to distinguish from functional test plan TC-XX IDs. -->
<!-- Each test MUST have exact steps and specific expected results. -->

---

### UT-01 — `/research/graveyard` loads directly with all structural elements present (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/research/graveyard`

**Preconditions:**
- Backend and frontend running per the Operational preconditions above.
- Both ledger files present with their 7+7 rows.

**Steps:**
1. Navigate directly to `http://localhost:3255/research/graveyard` (do not go through the hub first).
2. Wait up to 10 seconds for the page to finish loading.

**Expected Result:**
- A "Back to Research" link with a left-arrow icon appears above the title.
- The heading "Negative-results graveyard" is visible.
- Below it, subtitle text beginning "Every hypothesis the statistical referee has rejected — out-of-sample
  FAIL or INSUFFICIENT, across both the canonical and internal staging ledgers" is visible.
- A table renders with exactly 6 column headers, in this exact left-to-right order: "Selectors", "Verdict",
  "Date", "Deflation", "Ledger", "Lineage".
- Below the table, a "Revisit protocol" panel is visible.
- No blank white page, no browser "can't reach this page" error, no unhandled application-error page.
- No JavaScript console error.

---

### UT-02 — CENTERPIECE: Graveyard is discoverable from the Research hub and displays all 14 rejected hypotheses correctly, including a byte-exact ma_stack row (happy-path, J-19 core capability)

**Type:** happy-path
**Priority:** P1
**Surface:** `/research` → `/research/graveyard`

**Preconditions:**
- Backend and frontend running; both ledgers present (7 canonical + 7 staging); registry present.

**Steps:**
1. Navigate to `http://localhost:3255/research`.
2. Scroll down past the lab-card grid to the "Governance & process" heading.
3. Confirm two cards render side by side beneath it: "Pre-registration registry" (first, book icon) and
   "Negative-results graveyard" (second, archive icon).
4. Click the "Negative-results graveyard" card.
5. Confirm the browser navigates to `http://localhost:3255/research/graveyard`.
6. Wait for the table to finish loading.
7. Count the number of data rows in the table (excluding the header row).
8. Count how many rows show a "canonical" Ledger pill and how many show a "staging" Ledger pill.
9. Locate the row whose Selectors chips read exactly `decile=10`, `direction=positive`, `factor=ma_stack`,
   `horizon=20`, `kind=factor`, `slice_kind=decile`.
10. Read that row's Verdict badge text and Date cell.

**Expected Result:**
- Exactly one click from `/research` reaches `/research/graveyard` (2 clicks total starting from the
  Dashboard, per UT-14).
- The table shows **exactly 14 rows**.
- Exactly **7 rows** show a "canonical" Ledger pill and exactly **7 rows** show a "staging" Ledger pill.
- Every row's Verdict badge reads either "FAIL" or "INSUFFICIENT" — today all 14 read "FAIL".
- The `ma_stack` row (step 9) shows Verdict "FAIL" and Date "2026-07-03" — this matches its raw line in
  `certified-claims.jsonl` byte-for-byte (`claim` selectors, `verdict.status: "FAIL"`,
  `register_date: "2026-07-03"`; the underlying `reason` text begins "holdout edge +0.002062 is not
  significant after multiple-testing deflation").
- No cell in any row is blank or reads "undefined".

---

### UT-03 — Selectors render as readable key=value chips, never raw JSON; dates render as yyyy-MM-dd (validation)

**Type:** validation
**Priority:** P2
**Surface:** `/research/graveyard`

**Preconditions:**
- Graveyard page loaded with all 14 rows visible (UT-01/UT-02 pass).

**Steps:**
1. On `/research/graveyard`, locate a row tagged "staging" whose Selectors chips include a
   `cohort=composite` chip and a `condition=` chip (a "combination"-kind row, e.g. the one with
   `horizon=20`).
2. Inspect that row's Selectors cell closely.
3. Read that same row's Date cell.
4. Locate any other row and read its Date cell too.

**Expected Result:**
- The row from step 1 shows **5 separate small pill-shaped chips**, reading exactly `cohort=composite`,
  `condition=rs_spy_3m:top:quintile+high_proximity:top:tertile`, `direction=positive`, `horizon=20`,
  `kind=combination` — the two condition legs joined by a single `+` sign, never a bracketed array
  (`[...]`) or a comma-separated list. No `{`, `}`, or raw JSON text is visible anywhere in the cell.
- Both Date cells (steps 3–4) read `2026-07-03` in plain `yyyy-mm-dd` form — never a raw ISO timestamp
  (no trailing `T00:00:00`), never "Invalid Date".
- **Note for the tester:** three of the *canonical*-ledger rows (the ones whose Selectors include
  `factor=vcp_contraction`+`horizon=60`, `factor=rs_spy_3m`+`horizon=60`, or the `cohort=composite`/
  `horizon=20` combination row tagged canonical) legitimately show an EXTRA chip reading `ledger=canonical`.
  This is a pre-existing quirk baked into those three ledger rows' own raw `claim` JSON (it predates this
  iteration and is re-displayed verbatim, per the "recomputes nothing" contract) — do not flag it as a bug,
  and do not confuse it with the row's separate, dedicated Ledger column badge two columns over.

---

### UT-04 — Verdict badges use only FAIL(red)/INSUFFICIENT(amber) styling — never the "Proven" accent color or language (validation, critical anti-goal #1)

**Type:** validation
**Priority:** P1
**Surface:** `/research/graveyard`

**Preconditions:**
- Graveyard page loaded with all 14 rows visible.

**Steps:**
1. Inspect the Verdict badge in every one of the 14 rows.
2. Note the badge color/style for each.
3. Read the page's title and subtitle text.
4. Use the browser's in-page search (Ctrl+F / Cmd+F) to search for the word "Proven" anywhere on the page.

**Expected Result:**
- Every Verdict badge is either a red-outlined "FAIL" badge or an amber-outlined "INSUFFICIENT" badge
  (today: all 14 read "FAIL", red).
- No badge anywhere on the page uses the green/accent styling that `/evidence` reserves exclusively for a
  "Proven" PASS verdict.
- The word "Proven" does not appear anywhere on `/research/graveyard` — the page's own subtitle explicitly
  ends "...nothing here is a proven/not-proven signal."
- No badge reads "PASS".

---

### UT-05 — Deflation column re-displays the referee's context verbatim for both ledgers (validation)

**Type:** validation
**Priority:** P2
**Surface:** `/research/graveyard`

**Preconditions:**
- Graveyard page loaded with all 14 rows visible.

**Steps:**
1. Locate the "canonical" row whose Selectors include `factor=leadership_score` and `horizon=20`.
2. Read that row's Deflation cell.
3. Locate the "staging" row whose Selectors include `factor=vcp_contraction` and `horizon=10`.
4. Read that row's Deflation cell.

**Expected Result:**
- Step 2 (canonical): Deflation cell reads exactly `bonferroni ÷1`.
- Step 4 (staging): Deflation cell reads exactly `lord++ ÷1`.
- Both values are plain policy-name-plus-divisor text — no recalculated percentage, p-value, or alpha
  number appears in this column (that detail, where shown at all, is the small reason text under the
  Verdict badge, not the Deflation column).

---

### UT-06 — The closed `ma_stack` hypothesis shows its "permanent" marking in-frame; no other row shows it (happy-path, explicit DoD item)

**Type:** happy-path
**Priority:** P1
**Surface:** `/research/graveyard`

**Preconditions:**
- Graveyard page loaded with all 14 rows visible; registry file present (`ma_stack`'s registration row has
  `status: "closed"`).

**Steps:**
1. Locate the row whose Selectors chips read `factor=ma_stack`.
2. Inspect the Verdict cell of that row for a second badge beside the "FAIL" badge.
3. Take a screenshot (or otherwise capture) the row with both badges visible in the same frame.
4. Inspect the Verdict cell of the other 13 rows for the same second badge.

**Expected Result:**
- The `ma_stack` row shows a small muted badge reading exactly "permanent" immediately beside its red
  "FAIL" badge.
- The screenshot/capture shows both badges clearly, in-frame, in the same cell — not cropped or scrolled
  out of view.
- None of the other 13 rows shows a "permanent" badge — it appears on exactly one row.

---

### UT-07 — A row's Lineage link navigates to, and scrolls precisely to, its exact `/research/registry` row (happy-path, explicit DoD item)

**Type:** happy-path
**Priority:** P1
**Surface:** `/research/graveyard` → `/research/registry`

**Preconditions:**
- Graveyard page loaded; `/research/registry` has its 11 backfilled rows including
  `factor-ma_stack-d10-h20`; browser is at the default/live as-of date (no historical date selected).

**Steps:**
1. Locate the `ma_stack` row on `/research/graveyard`.
2. Read the Lineage cell's link text.
3. Click the Lineage link.
4. Observe the resulting URL in the browser's address bar.
5. Observe which row on the page is scrolled into view, positioned below the sticky page header.

**Expected Result:**
- Step 2: the link reads exactly `factor-ma_stack-d10-h20 →`.
- Step 4: the URL is `http://localhost:3255/research/registry#registration-factor-ma_stack-d10-h20` (no
  `?asof=` query string, since the browser is at the live date).
- Step 5: the page auto-scrolls so the `ma_stack` row (Rationale text beginning "Moving-average-stack
  (price stacked above its short/long moving averages)") is positioned just below the page header — not
  the top of the page, not left for the operator to hunt for.
- No broken link, no 404, no landing on the page top with the target row unreachable without manual
  scrolling/searching.

---

### UT-08 — Revisit-protocol panel displays the rule text; every row's link anchors to it (happy-path)

**Type:** happy-path
**Priority:** P2
**Surface:** `/research/graveyard`

**Preconditions:**
- Graveyard page loaded with all 14 rows visible.

**Steps:**
1. Scroll to the bottom of `/research/graveyard`, below the table.
2. Read the panel's heading and body text.
3. Scroll back to the table and locate any row's "Revisit protocol →" link (directly under its Verdict
   badge).
4. Click that link.
5. Observe where the page scrolls to.

**Expected Result:**
- Step 2: a card headed "Revisit protocol" is visible, with body text reading exactly: "A referee
  FAIL/INSUFFICIENT is final for that hypothesis; a re-test requires a materially changed precondition (a
  new data span covering ≥2 additional OOS years, a data-basis change, or a genuinely different
  hypothesis) and must be registered as a NEW candidate citing the closed verdict."
- Step 3: every one of the 14 rows shows a small "Revisit protocol →" text link under its Verdict badge.
- Step 5: the page scrolls down so the "Revisit protocol" panel (the same one read in step 2) is in view.

---

### UT-09 — Backend unavailable degrades to one contained error card, not a blank crash (error, critical anti-goal #8)

**Type:** error
**Priority:** P1
**Surface:** `/research/graveyard`

**Preconditions:**
- Graveyard page previously loaded successfully at least once.
- Operator has the ability to stop the backend process.

**Steps:**
1. With the backend running, load `http://localhost:3255/research/graveyard` and confirm the table renders
   (per UT-01/UT-02).
2. Stop the backend process.
3. Reload the page (F5).
4. Observe the result.
5. Restart the backend afterward and confirm the page recovers on a subsequent reload.

**Expected Result:**
- Step 4: a single card appears reading "Backend unavailable" with body text "The graveyard could not load
  from the API. Confirm the backend is running and reload."
- The card has a red-tinted border and a warning-triangle icon.
- The "Negative-results graveyard" heading and "Back to Research" link still render above the error card —
  the error is contained to the data area, not a full-page takeover.
- No blank white page, no browser network-error page, no unhandled JavaScript error overlay.
- The left sidebar navigation remains visible and every link in it stays clickable.
- Step 5: once the backend is back up, reloading shows the populated 14-row table again with no leftover
  error card.

---

### UT-10 — Missing/empty ledger files show an honest empty state, not a crash (error, critical anti-goal #8)

**Type:** error
**Priority:** P1
**Surface:** `/research/graveyard`

**Preconditions:**
- Backend running and reachable.
- Operator has filesystem access to `runs/goal-session-mcp-loop/state/` (relative to the repo root).
- **CAUTION:** this test temporarily empties BOTH the canonical and staging ledgers. Since `/evidence`
  reads the same canonical file, `/evidence` will also show its own empty state for the duration of this
  test — this is an expected side effect, not a new bug. Restore both files immediately after step 3.

**Steps:**
1. Rename both files:
   `mv runs/goal-session-mcp-loop/state/certified-claims.jsonl
   runs/goal-session-mcp-loop/state/certified-claims.jsonl.bak`
   `mv runs/goal-session-mcp-loop/state/staging-ledger.jsonl
   runs/goal-session-mcp-loop/state/staging-ledger.jsonl.bak`
   (No backend restart is required — the loader re-reads both files fresh on every request.)
2. Navigate to `http://localhost:3255/research/graveyard` (or reload if already open).
3. Observe the result.
4. Rename both files back immediately:
   `mv runs/goal-session-mcp-loop/state/certified-claims.jsonl.bak
   runs/goal-session-mcp-loop/state/certified-claims.jsonl`
   `mv runs/goal-session-mcp-loop/state/staging-ledger.jsonl.bak
   runs/goal-session-mcp-loop/state/staging-ledger.jsonl`
5. Reload the page again to confirm the real 14-row table returns.

**Expected Result:**
- Step 3: a card appears with an archive icon and heading "No rejected hypotheses yet", with body text
  beginning "Nothing has been referee-rejected yet on either ledger. Once a hypothesis fails, or is ruled
  insufficient, out-of-sample, it appears here with its selectors, verdict, and registration lineage."
- This is a calm, honest empty-state card — NOT a "Backend unavailable" error card, NOT a blank page, NOT
  a crash/500 page.
- The page's own heading/subtitle still render above the empty-state card.
- Step 5: the real 14-row table reappears exactly as before, confirming the rename/restore round-trips
  cleanly with no leftover empty-state card and no stale cache.

---

### UT-11 — Loading skeleton renders honestly before data arrives, then is fully replaced (smoke)

**Type:** smoke
**Priority:** P2
**Surface:** `/research/graveyard`

**Preconditions:**
- Backend and frontend running normally.
- Browser DevTools available for network throttling.

**Steps:**
1. Open DevTools → Network tab → set throttling to "Slow 3G" (or similar).
2. Navigate to `http://localhost:3255/research/graveyard`.
3. Immediately observe the page before the data finishes loading.
4. Wait for the fetch to complete, then observe again.
5. Turn network throttling back off.

**Expected Result:**
- Step 3: a card containing **8 pulsing gray placeholder bars** is visible in place of the table — no
  flash of an empty table, no "No rejected hypotheses yet" card shown prematurely.
- Step 4: once the fetch completes, the skeleton is fully replaced by the real 14-row table — no skeleton
  bars remain visible alongside or after the loaded data.

---

### UT-12 — Research hub's existing lab grid and registry card are unchanged; the new graveyard card is correctly the second governance card (regression)

**Type:** regression
**Priority:** P2
**Surface:** `/research`

**Preconditions:**
- Frontend running.

**Steps:**
1. Navigate to `http://localhost:3255/research`.
2. Count the cards in the main grid **above** the "Governance & process" heading.
3. Below "Governance & process", count the cards and read each card's title, left to right.
4. Read the first ("Pre-registration registry") card's description text.

**Expected Result:**
- Exactly **10 cards** remain in the main lab grid, unchanged (same titles/order as before this
  iteration: "Factor Lab", "Regime Lab", "Market Phase & Severity Lab", "Regime × Phase × Factor",
  "Regime × Setup × Pattern", "Severity-velocity × Regime", "Multi-factor combination", "Setup & Pattern
  event study", "Recovery-Turn Edge", "Downtrend Opportunity").
- Exactly **2 cards** appear under "Governance & process", in this exact order: "Pre-registration
  registry" (book icon), then "Negative-results graveyard" (archive icon).
- The "Pre-registration registry" card's description text is unchanged: still ends with the exact words
  "The gate refuses to certify anything that isn't here."
- The new "Negative-results graveyard" card's description reads "Every hypothesis the referee has
  rejected, across the canonical and staging ledgers — its verdict, deflation context, and registration
  lineage. Nobody retries a dead idea blindly."

---

### UT-13 — `/research/registry` and `/evidence` remain visually and functionally unchanged under normal browsing (regression, shared-file risk)

**Type:** regression
**Priority:** P1
**Surface:** `/research/registry`, `/evidence`

**Preconditions:**
- Backend and frontend running.

**Steps:**
1. Navigate to `http://localhost:3255/research/registry` with a plain URL (no `#` fragment).
2. Confirm the table shows its usual 11 rows, all 5 columns (Selectors, Rationale, Registered, Source,
   Status) populated exactly as before this iteration.
3. Navigate to `http://localhost:3255/research/registry#registration-factor-ma_stack-d10-h20` directly
   (type the fragment yourself — do not arrive via a graveyard link).
4. Observe whether the page scrolls to and positions the `ma_stack` row beneath the header.
5. Navigate to `http://localhost:3255/evidence`.
6. Count the claim cards and read each one's verdict badge.

**Expected Result:**
- Step 2: normal top-to-bottom browsing of `/research/registry` looks and behaves exactly as it did
  before this iteration — no visible difference from browsing without a fragment.
- Step 4: the same scroll-to-row behavior confirmed in UT-07, now triggered by typing the URL fragment
  directly rather than clicking a graveyard link — proves the anchor works standalone, not only as a
  click target from the graveyard.
- Step 6: exactly **7 claim cards** render on `/evidence`, every one showing a red "FAIL" verdict badge —
  identical to before this iteration. This confirms `apps/backend/main.py`'s new `graveyard.router`
  registration did not break backend startup or either pre-existing page, and that `/evidence` stayed
  byte-identical.

---

### UT-14 — Graveyard is discoverable within 2 clicks from the Dashboard, with a clear label (ux)

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
5. Read the "Negative-results graveyard" card's title and one-line description.
6. Click the card.

**Expected Result:**
- Step 3 navigates to `http://localhost:3255/research` — **click 1**.
- The "Governance & process" heading and its two cards are visible directly below the main lab grid on
  ordinary scroll — not hidden in a submenu, tab, or collapsed section.
- The card's title "Negative-results graveyard" and its description are in plain, readable language (no
  internal jargon like "non-PASS" or "lineage-attached") — a first-time user can tell what the page
  contains before clicking.
- Step 6 navigates to `http://localhost:3255/research/graveyard` — **click 2**. Total: 2 clicks from the
  Dashboard, meeting the "reachable in ≤2 clicks" requirement.
- The left sidebar itself gained no new entry and no reordering — "Research" is the same single entry it
  was before this iteration (Dashboard, Stocks, Themes, Sectors, Scanner Runs, Backtest, **Research**,
  Evidence, Watchlist, Methodology, Data Manager).

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | `/research/graveyard` loads directly, structure present | smoke | P1 | `/research/graveyard` |
| UT-02 | CENTERPIECE: discover from hub + all 14 rows correct incl. byte-exact ma_stack | happy-path | P1 | `/research` → `/research/graveyard` |
| UT-03 | Selectors render as chips, never raw JSON; dates yyyy-MM-dd | validation | P2 | `/research/graveyard` |
| UT-04 | Verdict badges FAIL/INSUFFICIENT only, never accent/"Proven" | validation | P1 | `/research/graveyard` |
| UT-05 | Deflation context verbatim for both ledgers | validation | P2 | `/research/graveyard` |
| UT-06 | ma_stack "permanent" marking in-frame, unique to that row | happy-path | P1 | `/research/graveyard` |
| UT-07 | Lineage link resolves + scrolls to exact registry row | happy-path | P1 | `/research/graveyard` → `/research/registry` |
| UT-08 | Revisit-protocol panel + every row's anchor link | happy-path | P2 | `/research/graveyard` |
| UT-09 | Backend unavailable → one contained error card | error | P1 | `/research/graveyard` |
| UT-10 | Missing/empty ledgers → honest empty state, no crash | error | P1 | `/research/graveyard` |
| UT-11 | Loading skeleton (8 bars) shown, then fully replaced | smoke | P2 | `/research/graveyard` |
| UT-12 | Hub lab grid + registry card unchanged; graveyard card 2nd | regression | P2 | `/research` |
| UT-13 | `/research/registry` + `/evidence` unaffected under normal browsing | regression | P1 | `/research/registry`, `/evidence` |
| UT-14 | Discoverable in ≤2 clicks from Dashboard, clear label | ux | P2 | nav / `/research` |

**P1 tests must all pass for browser QA verdict to be PASS:** UT-01, UT-02, UT-04, UT-06, UT-07, UT-09,
UT-10, UT-13. UT-02 is the actual J-19 DoD proof (discoverability + all 14 rows correctly populated + a
byte-exact ma_stack round-trip) and is the centerpiece of this plan. UT-04 is elevated to P1 because it is
the CRITICAL anti-goal #1 check (no FAIL/INSUFFICIENT ever rendered as proven). UT-06 and UT-07 are
elevated to P1 because the phase's own Definition of Done names them explicitly (the permanent marking
in-frame; the lineage link resolving to its registry row). UT-09/UT-10 are elevated to P1 because they
directly exercise the CRITICAL anti-goal #8 resilience requirement ("the UI degrades gracefully... never a
blank application-error page"). UT-13 is elevated to P1 because it is the named shared-file/shared-router
regression risk (`apps/backend/main.py`'s new router registration, plus the presentation-only
`/research/registry` row-anchor edit) — a failure there would mean either the whole backend failed to
start or an existing, already-shipped page broke.

**Not covered here** (see `reports/qa/goal-mcp-loop-iter-31-test-plan.md` instead): the honest-null
lineage path (TC-07/TC-08 — no live-data trigger exists today, fixture-only), the API-level single-source
byte-equality check (TC-16), the correctness round-trip at the API layer (TC-17, browser-equivalent
covered live in UT-02 instead), the drift-insurance `_CLAIM_SELECTOR_KEYS` equality test (TC-21,
code-level only), the required-still-passing journey pytest replay (TC-18), the canonical Bonferroni
divisor / `/api/evidence` byte-identity check (TC-20), and the pre/post ledger checksum diff (TC-19).
