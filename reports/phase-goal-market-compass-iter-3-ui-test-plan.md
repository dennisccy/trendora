# goal-market-compass-iter-3 — UI Test Plan

**Phase:** goal-market-compass-iter-3
**Date:** 2026-08-20
**Written by:** ui-impact-analyst (combined mode)
**Frontend URL:** http://localhost:3255

---

## Test Cases

<!-- Test IDs use UT-XX prefix to distinguish from the phase spec's own functional TC-XX IDs. -->
<!-- Each test has exact steps and specific expected results. -->

---

### UT-01 — Dashboard loads with the Manifest card present (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend is running at http://localhost:3255
- Backend is reachable at its configured API base
- No login is required (this product has no auth)

**Steps:**
1. Navigate to `http://localhost:3255/`
2. Wait for the page to finish loading (the loading skeleton disappears)
3. Open the browser devtools console

**Expected Result:**
- The page renders "Dashboard" as the page heading, with subtitle "The daily snapshot at a glance"
- Scrolling down, a card titled "Manifest" is visible as the last of four compass cards ("Summary",
  "What changed", "Next-session focus", "Manifest"), positioned above the "Market Regime" /
  "Market Phase & Severity" cards
- No red error text or blank page appears in place of the Manifest card (it shows either its populated
  content, its "pre-freeze era" message, or its "unavailable" message — never nothing)
- No uncaught exception/error is printed to the browser console

---

### UT-02 — Manifest card shows full freeze/integrity badges + hash chips on a historical date (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend running at http://localhost:3255, backend reachable
- At least one stored historical trading date exists in the as-of switcher's calendar (true for this
  project's committed 30-year seed)

**Steps:**
1. Navigate to `http://localhost:3255/`
2. Click the "◀" button (`data-testid="asof-step-prev"`, aria-label "Previous available date") next to
   the date badge in the top bar, once
3. Confirm the date badge (`data-testid="asof-indicator"`) now reads "Viewing as-of \<date\> (historical)"
   instead of "Latest"
4. Scroll to the "Manifest" card

**Expected Result:**
- The card shows a `data-testid="compass-manifest-badges"` row containing: a mode badge reading either
  "retrospective" or "at ingest"; a badge reading "version 1" (or higher, if this date was already
  regenerated in an earlier test pass); a badge reading "frozen" or "not frozen"; a badge reading
  "prospective-eligible" or "not prospective-eligible"
- A line reading "Frozen \<date/time\>" appears beside the badges
- Four hash chips are visible with labels "Engine identity:", "Candidate rule:", "Cohort rule:",
  "Manifest config:" — each showing a short alphanumeric value ending in "…"
- Hovering over (or long-pressing) a hash chip's value shows the full untruncated hash via the browser's
  native tooltip (the element's `title` attribute)
- A line shows "Dataset stamp: \<value\>", a "Universe pool:" hash chip, "Members: \<a number\>", and
  "Profile: core"
- A "Basis: available" (or "rebuilt"/"unavailable") badge is visible
- If this manifest is genuinely "pre-freeze era" (mode is null) instead, the card shows ONLY the
  sentence "This manifest predates the freeze/integrity block — no stamps were recorded for it." — in
  that case, repeat steps 2-4 (click "◀" again to try an older date) until a date with the full
  badge/chip set above is found, since most historical dates in the 30-year seed have never been
  fetched before and will create-once mint a fresh `retrospective` manifest on first view

---

### UT-03 — Audit table expands to reveal comparison cohort + near-threshold shadow tables (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Complete UT-02 first so the Manifest card is showing a populated (non-pre-freeze-era) manifest

**Steps:**
1. On the Manifest card, locate the collapsed row whose visible text starts "Audit table — comparison
   cohort (" (it also shows a count and "+ near-threshold shadow (" with a second count)
2. Click that row

**Expected Result:**
- The row expands (its chevron icon rotates) to reveal:
  - A sub-heading "Comparison cohort (non-selected pool)" followed by a caveat sentence stating the
    cohort is "a frozen non-selected comparison pool, not a matched or causal control group" (verbatim
    text may vary slightly but must include this non-causal framing)
  - A table with columns "Ticker", "Leadership", "Entry", "Risk", "Setup", "Sector", "Disposition" —
    every row's "Disposition" cell reads either "below selection floor" or "excluded by cap"
  - Below it, a sub-heading in amber/warning text reading "Near-threshold shadow — research-only
    substrate, not part of selection or display ranking"
  - A second table with the SAME columns EXCEPT "Disposition" (that column is absent from this table)
  - Below both tables, three caveat sentences (evidence / survivorship / sector-basis disclosures)
- If the comparison-cohort count shown in the summary row is 0, the table shows the text "No rows."
  instead of an empty table — this is a valid, honest empty state, not a bug

---

### UT-04 — Confirm-gated regenerate mints a new manifest version in place (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Complete UT-02 first — the as-of switcher must be on a historical date (NOT "Latest"), and the
  Manifest card must be showing a populated manifest (not pre-freeze-era, not unavailable)
- Note the current "version N" badge value shown on the card before starting

**Steps:**
1. On the Manifest card, click the "Regenerate manifest" button (amber outline, refresh icon,
   `data-testid="compass-manifest-regenerate-button"`)
2. In the modal that opens (heading "Confirm manifest regenerate"), read the body text — it must state
   this "mints a NEW manifest version for \<date\>" and that "The existing version is never touched,
   changed, or deleted"
3. Click the "Regenerate manifest" button in the modal's footer (`data-testid="compass-manifest-regenerate-confirm-button"`)
4. Wait for the button's spinner ("Regenerating…") to finish

**Expected Result:**
- The modal closes automatically on success (no page navigation/reload occurs — the URL stays the same)
- The Manifest card's "version N" badge now shows a number exactly one higher than the value noted in
  Preconditions
- The "prospective-eligible" badge now reads "not prospective-eligible" (a regenerated version can never
  be eligible, even if this exact same click were somehow repeated)
- The "Frozen \<date/time\>" line shows a new, later timestamp than before
- A "Versions" section (`data-testid="compass-manifest-versions"`) is now visible, listing at least two
  rows

---

### UT-05 — Cancelling the regenerate confirm modal creates no new version (validation)

**Type:** validation
**Priority:** P2
**Surface:** `/`

**Preconditions:**
- As-of switcher on a historical date; Manifest card showing a populated manifest
- Note the current "version N" badge value before starting

**Steps:**
1. Click the "Regenerate manifest" button on the Manifest card
2. In the "Confirm manifest regenerate" modal, click the "Cancel" button in the footer (NOT the
   "Regenerate manifest" confirm button)
3. Observe the Manifest card

**Expected Result:**
- The modal closes
- The "version N" badge on the Manifest card is UNCHANGED from the value noted in Preconditions
- No new row appears in a "Versions" list (if one was already visible from a prior test, its entry count
  is unchanged)
- Repeat steps 1-3 but close the modal via the "✕" icon button (aria-label "Cancel") in the modal's
  top-right corner instead of the footer "Cancel" button — same expected result (version unchanged)

---

### UT-06 — Regenerate control is replaced by an explanatory line while viewing "Latest" (validation)

**Type:** validation
**Priority:** P2
**Surface:** `/`

**Preconditions:**
- Frontend running, backend reachable

**Steps:**
1. Navigate to `http://localhost:3255/` fresh (no `?asof=` query parameter in the URL)
2. Confirm the date badge (`data-testid="asof-indicator"`) reads "Latest" (not "Viewing as-of…")
3. Scroll to the Manifest card

**Expected Result:**
- No "Regenerate manifest" button is present anywhere on the card
- Instead, a line of text is visible reading "Regenerate is available only for a stored historical
  date — step the as-of switcher off "Latest" first." (`data-testid="compass-manifest-regenerate-unavailable"`)
- Clicking anywhere in that text line does nothing (it is plain text, not a button)

---

### UT-07 — Manifest card shows an honest "unavailable" state when the backend is unreachable (error)

**Type:** error
**Priority:** P2
**Surface:** `/`

**Preconditions:**
- Ability to stop the backend process, or to block/redirect the `GET /api/compass` request via browser
  devtools request-blocking (Network tab → Block request URL containing `/api/compass`)

**Steps:**
1. Block or stop the backend so `GET /api/compass` fails
2. Navigate to (or reload) `http://localhost:3255/`

**Expected Result:**
- The Manifest card renders a red-bordered box (`data-testid="compass-manifest-strip-unavailable"`)
  containing the text "Manifest strip is unavailable — backend not reachable, or this session has not
  been frozen yet."
- The rest of the page does not crash to a blank white screen — the page's own top-level error state (if
  the Dashboard's primary fetch also fails) or the other compass cards' matching "unavailable" messages
  render instead, consistent with this card's degradation
- Unblock/restart the backend afterward and reload to confirm the card recovers to its normal content

---

### UT-08 — Regenerate API rejects a missing confirm flag and an as-of with no manifest (error)

**Type:** error
**Priority:** P2
**Surface:** `POST /api/compass/regenerate` (API — not reachable as a distinct path through normal UI
clicks, since the "Regenerate manifest" button always sends `confirm=true` and is only shown once a
manifest already exists for the selected date; verified via direct API call per the phase spec's own
Error Cases list)

**Preconditions:**
- Backend reachable at its configured base (e.g. `http://localhost:8255` per the dev handoff's live
  verification port, or the configured `NEXT_PUBLIC_API_URL`)
- A known stored trading date with no existing manifest is NOT required for the second check below —
  any date already covered by tests above will 409/succeed instead, so use an as-of far outside the
  seed's trading calendar (e.g. a weekend date) for the "no manifest" check, or a symbol/date combo
  confirmed absent from `next_session_manifests`

**Steps:**
1. Open the browser devtools console on any page (or a terminal with `curl`)
2. Run: `fetch("http://localhost:8255/api/compass/regenerate?as_of=2026-08-05", {method:"POST"}).then(r => r.status)`
   (omit `confirm=true`) — or the `curl` equivalent: `curl -s -o /dev/null -w "%{http_code}" -X POST "http://localhost:8255/api/compass/regenerate?as_of=2026-08-05"`
3. Run the same call WITH `&confirm=true` appended, against an as-of date confirmed to have no stored
   manifest row (e.g. a Saturday/Sunday date, which the backend's as-of resolver will reject before
   reaching the manifest lookup)

**Expected Result:**
- Step 2 (no `confirm=true`): HTTP 400, with a JSON body containing `"detail"` text mentioning
  "confirm=true" — no new manifest version is created (re-check the Versions list for that date is
  unchanged)
- Step 3 (no existing manifest / invalid as-of): a 4xx status (404 for a valid trading date with no
  manifest yet, or the existing honest as-of-resolution error for a non-trading date) — never a 200 with
  a fabricated payload

---

### UT-09 — Summary card's cited facts render rounded, not raw floats (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend running, backend reachable, `/` loaded successfully

**Steps:**
1. Navigate to `http://localhost:3255/`
2. Scroll to the "Summary" card (the first compass card, above "What changed")
3. Click the "Show cited facts" disclosure row inside it

**Expected Result:**
- The disclosure expands to a list of sentence IDs, each with its cited fact name/value pairs
- Every numeric fact value (for example a fact named `regime_score_delta`) displays with exactly 2
  digits after the decimal point (e.g. "6.27", "-0.20") — no value shows more than 2 decimal digits or a
  long trailing-digit float artifact (e.g. "-0.20000000000000284" must NOT appear anywhere)
- Non-numeric fact values (strings, booleans, null) are unaffected and render as before

---

### UT-10 — Candidate card ATR caution states the fact only, no advice-sounding tail (regression)

**Type:** regression
**Priority:** P2
**Surface:** `/`

**Preconditions:**
- Frontend running, backend reachable
- At least one candidate card in "Next-session focus" carries a caution starting "ATR_RISK_BUDGET:" (if
  the current live "Latest" date has zero candidates, step to a historical date via the as-of switcher
  until a candidate with this caution appears — a Risk-off-regime date will show it on every candidate)

**Steps:**
1. Navigate to `http://localhost:3255/` (stepping the as-of switcher if needed, per Preconditions)
2. Scroll to "Next-session focus"
3. On a candidate card, locate the "Cautions" section (amber-highlighted, appears directly below "Why")

**Expected Result:**
- A caution line starting "ATR_RISK_BUDGET: ATR is \<N\>% of price (p\<N\> of universe)." is visible
- The sentence does NOT contain the phrase "sized risk accordingly" anywhere
- If the regime is Risk-off for the viewed date, a second caution "REGIME_RISK_OFF: the market regime is
  Risk-off as of this date — every candidate here is context, not a signal to act." is also present
  (unchanged wording, not part of this iteration's fix, included here only as a same-section regression
  check)

---

### UT-11 — Pre-existing compass cards still render correctly beside the new Manifest card (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend running, backend reachable

**Steps:**
1. Navigate to `http://localhost:3255/`
2. Scroll from top to bottom of the page, noting each card in order

**Expected Result:**
- Cards appear in this exact order: "Summary" → "What changed" → "Next-session focus" → "Manifest" →
  the unmodified dashboard body (Market Regime / Market Phase & Severity glance cards → the two-pane
  cross-view chart → the collapsed "More detail" section)
- "Summary" still shows its narrative sentences; "What changed" still shows either a change list or its
  "no prior run"/"quiet session" message; "Next-session focus" still shows either candidate cards or the
  empty-focus message plus the "Not priority (N)" disclosure
- No card that existed before this iteration was removed, reordered relative to each other, or broken by
  the new Manifest card's presence

---

### UT-12 — `/data` "Refreshed:" line shows the hyphenated "next-session manifest" phase name (regression)

**Type:** regression
**Priority:** P3
**Surface:** `/data`

**Preconditions:**
- Ability to run a snapshot job on `/data` whose finalize tail includes the compass freeze phase (any
  successful "Backfill snapshots" or "Fetch + backfill" job for a date range including the frontier
  date qualifies) — this is the SAME existing J-01 data-operations flow, unchanged in mechanics by this
  iteration; only the finalize phase's disclosed NAME changed

**Steps:**
1. Navigate to `http://localhost:3255/data`
2. Start (or locate the most recent completed) a "Backfill snapshots" job whose range includes dates
   this iteration's code has processed
3. In the Job progress panel (while running or after completion) or in a Run history row, locate the
   line starting "Refreshed:" (`data-testid="aggregates-refreshed"`)

**Expected Result:**
- The "Refreshed:" line's comma-separated list includes the text "next-session manifest" (with a
  hyphen between "next" and "session")
- The text "next session manifest" (a plain space, no hyphen) does NOT appear
- This test is lower priority (P3) because it exercises the pre-existing J-01 remove/backfill mechanism
  which is out of this iteration's primary scope — treat a skip as acceptable if no backfill can safely
  be run during this QA pass, but do not skip if one is already scheduled/available

---

### UT-13 — Manifest card is discoverable without extra navigation (ux)

**Type:** ux
**Priority:** P2
**Surface:** `/` (page scroll, no separate nav)

**Steps:**
1. Navigate to `http://localhost:3255/` as a first-time visitor would (no prior knowledge of the
   feature)
2. Scroll down the page only — do not open any menu, sidebar link, or settings page

**Expected Result:**
- The "Manifest" card is reached purely by scrolling `/` — no click through a menu, tab, or secondary
  page is required
- The card's title "Manifest" and its badges are self-explanatory enough that a user can tell, without
  reading code, that this card is about proof/freezing/versions (badge words: "frozen", "version",
  "prospective-eligible" are visible without expanding anything)
- No broken link, disabled nav item, or "coming soon" placeholder appears anywhere related to this
  feature (per the plan, there is intentionally no separate nav route for it)

---

### UT-14 — Legacy pre-freeze-era manifest rows show the honest empty state, never fabricated badges (ux)

**Type:** ux
**Priority:** P3
**Surface:** `/`

**Preconditions:**
- Applicability depends on live data state: this state is only reachable while viewing an as-of date
  whose manifest row was created before this iteration's schema existed (`mode` stored as NULL) and
  which has NOT since been regenerated. The live frontier date was in exactly this state during the
  developer's own live-verification pass (recorded in the dev handoff) — check it first before trying
  other dates.

**Steps:**
1. Navigate to `http://localhost:3255/` with the as-of switcher on "Latest" (no `?asof` in the URL)
2. Scroll to the Manifest card

**Expected Result (if a pre-freeze-era row is currently being viewed):**
- The card shows ONLY the sentence "This manifest predates the freeze/integrity block — no stamps were
  recorded for it." (`data-testid="compass-manifest-pre-freeze-era"`)
- NO mode/version/frozen/prospective-eligible badges, hash chips, dataset/universe stamps, basis line,
  audit table, or Regenerate button appear — the card must not fabricate any of these for a row that
  never had them computed
- **If instead the "Latest" date already shows full badges/chips** (meaning a new ingest-finalize has
  run since the developer's last test), this state is simply not currently reproducible on "Latest" —
  note this in the QA report as "not applicable — Latest is already post-freeze" rather than marking the
  test failed; this is expected drift over time, not a defect

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | Dashboard loads with Manifest card present | smoke | P1 | `/` |
| UT-02 | Manifest card shows full badges + hash chips (historical date) | happy-path | P1 | `/` |
| UT-03 | Audit table expands (comparison cohort + shadow) | happy-path | P1 | `/` |
| UT-04 | Regenerate mints a new version in place | happy-path | P1 | `/` |
| UT-05 | Cancel regenerate modal creates no new version | validation | P2 | `/` |
| UT-06 | Regenerate hidden while on "Latest" | validation | P2 | `/` |
| UT-07 | Manifest card "unavailable" state on backend down | error | P2 | `/` |
| UT-08 | Regenerate API rejects missing confirm / missing manifest | error | P2 | API |
| UT-09 | Summary card cited facts render rounded | regression | P1 | `/` |
| UT-10 | ATR caution text has no advice-sounding tail | regression | P2 | `/` |
| UT-11 | Pre-existing compass cards still render correctly | regression | P1 | `/` |
| UT-12 | `/data` "Refreshed:" line shows hyphenated phase name | regression | P3 | `/data` |
| UT-13 | Manifest card discoverable by scroll alone | ux | P2 | `/` |
| UT-14 | Pre-freeze-era rows show honest empty state | ux | P3 | `/` |

**P1 tests must all pass for browser QA verdict to be PASS.**
