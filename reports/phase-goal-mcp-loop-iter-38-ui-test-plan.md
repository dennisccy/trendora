# Phase goal-mcp-loop-iter-38 — UI Test Plan

**Phase:** goal-mcp-loop-iter-38
**Date:** 2026-07-15
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3255

---

## Scope

This plan covers the new **"Concentration X-ray"** section added to the existing `/watchlist`
page (J-23 / backlog B-204): a pairwise correlation matrix, cluster badges, an "effective
independent bets" (ENB) headline, and sector/theme/shared-setup concentration bars — all
additive, all read verbatim from `GET /api/watchlist`'s new `xray` field. No new page, no new
nav entry, no new user input control.

It does **not** duplicate the API-level checks already in
`reports/qa/goal-mcp-loop-iter-38-test-plan.md` (TC-01 through TC-18) — e.g. the ENB-formula
fixture, the offline correlation spot-check, the raw JSON shape of `GET /api/watchlist`, the
network-tab "single request / no client recompute" check, and the ledger-byte-identity /
Bonferroni-divisor checks are all covered there. This plan is exclusively about what an operator
**sees and can click** on the rendered page.

**Data note:** the watchlist in this environment is a real, persisted list (not a disposable test
fixture) and normally holds exactly two names, **ABBV** and **MSFT**. Several test cases below
quote the live figures observed when this plan was written (correlation **-0.11**, ENB **≈ 2.0**,
etc.) — treat these as the expected values for an immediate run; if the underlying price history
has moved since, the *shape* of each expectation (a specific number, a stated window, an honest
NA) still applies even if the digits differ slightly. **UT-15 is destructive** to this shared
list and must run last, with its own restore step — see its entry below.

---

## Test Cases

<!-- Test IDs use UT-XX prefix to distinguish from functional test plan TC-XX IDs. -->
<!-- Each test has exact steps and specific expected results — no "test the form" / "verify it works". -->

---

### UT-01 — Watchlist page loads with entries table and Concentration X-ray section (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/watchlist`

**Preconditions:**
- Frontend is running at http://localhost:3255; backend is running and reachable.
- The watchlist currently has at least 2 saved entries (the persisted real watchlist normally
  holds ABBV and MSFT). Do not remove entries before this test — see UT-15 for that scenario.

**Steps:**
1. Navigate to `http://localhost:3255/watchlist`.
2. Wait for the page to finish loading.
3. Scroll down past the existing entries table.

**Expected Result:**
- The page renders the heading "Watchlist" with a subtitle beginning "Your saved stocks — each
  shows its current Leadership / Entry / Risk...".
- The existing entries table renders with one row per saved ticker (ABBV, MSFT expected) and
  columns Ticker, Added, Reason, Leadership, Entry Quality, Risk, Setup, Since added,
  Invalidation, and an unlabeled Remove column.
- Below the entries table, a new `Card` titled "Concentration X-ray" is visible with the subtitle
  "Descriptive only — how correlated, clustered, and concentrated your watchlist really is. No
  recommendations."
- No "Backend unavailable" error card appears; no blank/crashed page; no uncaught JavaScript
  errors in the browser console.
- (Informational, non-blocking: on a slow connection you may briefly see a row of pulsing gray
  skeleton placeholders before the table and X-ray section render — expected, not a bug.)

---

### UT-02 — Correlation matrix renders the correct grid, values, colors and tooltips (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/watchlist`

**Preconditions:**
- Watchlist contains exactly ABBV and MSFT.

**Steps:**
1. Navigate to `http://localhost:3255/watchlist`.
2. In the "Concentration X-ray" section, locate the correlation matrix table (directly below the
   ENB headline).
3. Read the column headers (top row) and row headers (left column).
4. Hover the cell where row "ABBV" meets column "MSFT".
5. Hover the cell where row "MSFT" meets column "MSFT" (the diagonal/self cell).

**Expected Result:**
- Step 3: the matrix is a 2×2 grid of data cells; column headers read "ABBV" then "MSFT"; row
  headers read "ABBV" then "MSFT" in the same order.
- Step 4: the ABBV/MSFT cell displays the text "-0.11" in red/negative-tinted text (the app's
  standard negative-value color token, the same one used elsewhere on this page for a negative
  percentage). Its tooltip reads "ABBV vs MSFT: -0.114 correlation over the trailing 126 trading
  days" (the exact third-decimal figure may differ slightly if price history has moved since this
  plan was written, but the tooltip MUST show a specific signed number and the phrase "126 trading
  days" — never blank, "0", or "NaN").
- Step 5: the MSFT/MSFT self cell displays "1.00" in green/positive-tinted text; its tooltip reads
  "MSFT: <N> of 126 trailing days available" (a self cell never shows a blank or a "—").
- No cell in this fully-populated 2-name matrix shows a muted dashed "—" (NA) — both ABBV and MSFT
  have well over 126 trading days of history.

---

### UT-03 — Effective-independent-bets headline states the figure and its window (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/watchlist`

**Preconditions:**
- Watchlist contains ABBV and MSFT.

**Steps:**
1. Navigate to `http://localhost:3255/watchlist`.
2. In the "Concentration X-ray" section, read the line directly above the correlation matrix.

**Expected Result:**
- The text "≈ 2.0" appears in large/bold text, immediately followed by "effective independent
  bets (over the last 126 trading days)" in smaller muted text.
- The trailing window ("126 trading days") is always stated next to the figure — never shown
  without it.
- A small circular "i" info icon is visible immediately to the right of this text.

---

### UT-04 — Cluster badges group correlated names and separate uncorrelated ones (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/watchlist`

**Preconditions:**
- Watchlist contains ABBV and MSFT (correlation ≈ -0.11, well below the cluster threshold).

**Steps:**
1. Navigate to `http://localhost:3255/watchlist`.
2. In the "Concentration X-ray" section, locate the "Clusters" sub-heading (below the correlation
   matrix).
3. Read the caption directly under the heading.
4. Read the badge(s) below the caption.

**Expected Result:**
- Step 3: caption reads "Names grouped when their correlation is at or above 0.70."
- Step 4: two separate gray/default-colored badges are shown — one reading exactly "ABBV" and one
  reading exactly "MSFT" — **not** a single joined badge reading "ABBV · MSFT". (ABBV and MSFT are
  correlated at approximately -0.11, well below the 0.70 threshold, so they must not be grouped.)

---

### UT-05 — Sector concentration bars bucket the null-sector name as "Unassigned" (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/watchlist`

**Preconditions:**
- Watchlist contains ABBV (no GICS sector mapped in config) and MSFT (Technology sector).

**Steps:**
1. Navigate to `http://localhost:3255/watchlist`.
2. In the "Concentration X-ray" section, locate the "Sector concentration" sub-heading.
3. Read the bars listed underneath.

**Expected Result:**
- Exactly two bars are shown.
- One bar's label reads "Technology" with trailing text "1 · 50%".
- The other bar's label reads "Unassigned" with trailing text "1 · 50%" (ABBV — it must appear
  as "Unassigned", never blank, never silently omitted, never crash the page).
- The "Technology" bar appears above the "Unassigned" bar.

---

### UT-06 — Theme concentration bars show every theme the watchlist's names belong to (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/watchlist`

**Preconditions:**
- Watchlist contains ABBV (belongs to no configured theme) and MSFT (belongs to three).

**Steps:**
1. Navigate to `http://localhost:3255/watchlist`.
2. In the "Concentration X-ray" section, locate the "Theme concentration" sub-heading.
3. Read the bars listed underneath.

**Expected Result:**
- Exactly three bars are shown, each reading "1 · 50%": **"Ai Data Centre"**, **"Megacap
  Leaders"**, and **"Software Cloud"** (MSFT's three theme memberships in `config.yaml`). Each
  name is title-cased from its underlying slug (e.g. `ai_data_centre`), so "AI" renders as "Ai",
  not all-caps — this is expected, not a typo.
- ABBV contributes no bar of its own (it is not a member of any configured theme).

---

### UT-07 — Shared-setup bar reuses the existing status color vocabulary (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/watchlist`

**Preconditions:**
- Watchlist contains ABBV and MSFT, both currently classified "Avoid" in the entries table's
  Setup column.

**Steps:**
1. Navigate to `http://localhost:3255/watchlist`.
2. In the entries table, note the color of the "Avoid" badge in the Setup column.
3. Scroll to the "Concentration X-ray" section's "Shared setup" sub-heading.
4. Compare the badge color there to the one noted in step 2.

**Expected Result:**
- The "Concentration X-ray" section shows exactly one bar: a red/danger-colored "Avoid" badge
  with trailing text "2 · 100%".
- The red used for this badge is visually identical to the red used for "Avoid" in the entries
  table's Setup column — the same color token, not a new/different red.
- (If either name's setup status has since changed away from "Avoid", the bar(s) shown must match
  whatever the entries table's Setup column currently shows for each name — the two must always
  agree, since both read the same canonical row.)

---

### UT-08 — Adding a ticker via the existing form still works and the X-ray updates (regression)

**Type:** regression
**Priority:** P1 *(core write path for this page — classified P1 despite the skill's default
"regression = P3", because breaking Add/Remove breaks the page's only pre-existing interactive
capability; see Notes)*
**Surface:** `/watchlist`

**Preconditions:**
- Watchlist contains ABBV and MSFT; AAPL is not currently on the watchlist.

**Steps:**
1. Navigate to `http://localhost:3255/watchlist`.
2. Type "AAPL" into the field labeled "Ticker" (placeholder "e.g. ANET").
3. Type "UI test — temporary" into the field labeled "Reason" (placeholder "Why are you watching
   it?").
4. Click the "Add" button (accent-colored button with a "+" icon, to the right of the Reason
   field).
5. Wait for the entries table to refresh.

**Expected Result:**
- No error message appears below the Add form.
- A new row for "AAPL" appears in the entries table with reason "UI test — temporary".
- The saved-count text above the table (e.g. "3 saved") increments by one.
- The "Concentration X-ray" section re-renders: the correlation matrix grows to a 3×3 grid
  including AAPL as a row and column; the ENB headline value may change; the sector/theme/setup
  bars update to reflect three names instead of two.
- **Immediately continue to UT-09** to remove AAPL and restore the watchlist.

---

### UT-09 — Removing an entry via the existing control still works and the X-ray updates (regression)

**Type:** regression
**Priority:** P1 *(see UT-08 rationale)*
**Surface:** `/watchlist`

**Preconditions:**
- The watchlist currently contains ABBV, MSFT, and AAPL (run immediately after UT-08).

**Steps:**
1. On `http://localhost:3255/watchlist`, locate the AAPL row in the entries table.
2. Click the trash-can icon button at the right end of the AAPL row (accessible name "Remove AAPL
   from the watchlist").
3. Wait for the entries table to refresh.

**Expected Result:**
- No error message appears.
- The AAPL row disappears; the saved-count text decrements back to "2 saved".
- The "Concentration X-ray" section re-renders back to the original 2×2 ABBV/MSFT matrix, the ENB
  headline reads "≈ 2.0" again, and the sector/theme/setup bars return to their original two-name
  state (matching UT-02 through UT-07).
- The watchlist is now restored to its pre-test state (ABBV, MSFT only).

---

### UT-10 — Entries table columns and layout are unchanged (regression)

**Type:** regression
**Priority:** P3
**Surface:** `/watchlist`

**Preconditions:**
- Watchlist contains at least one entry.

**Steps:**
1. Navigate to `http://localhost:3255/watchlist`.
2. Read the entries table's column headers left to right.

**Expected Result:**
- Column headers read, in order: "Ticker", "Added", "Reason", "Leadership", "Entry Quality",
  "Risk", "Setup", "Since added", "Invalidation", plus an unlabeled Remove column on the far
  right.
- Each row's Ticker cell is a clickable accent-colored link to that stock's detail page.
- No new column was added to this table by this phase — the "Concentration X-ray" content lives
  entirely in the separate `Card` below the table, not inside it.

---

### UT-11 — ENB methodology info tooltip opens on click and closes on outside click (ux)

**Type:** ux
**Priority:** P3
**Surface:** `/watchlist`

**Preconditions:**
- Watchlist contains at least 2 entries (X-ray section visible).

**Steps:**
1. Navigate to `http://localhost:3255/watchlist`.
2. Click the small circular "i" icon immediately to the right of the "effective independent bets"
   headline (accessible name "What is effective independent bets?").
3. Read the panel that appears.
4. Click anywhere outside the panel (e.g. the page background).

**Expected Result:**
- Step 2/3: a text panel opens containing wording to the effect of: "How many genuinely
  independent positions your watchlist behaves like, derived from the eigenvalues of the pairwise
  correlation matrix over the trailing 126 trading days. Perfectly correlated names count as one
  bet; fully independent names each count as their own. A name with under 60 days of overlapping
  history is excluded and shown as NA."
- The panel explicitly states both the 126-trading-day window and the 60-day minimum-history
  floor as numbers, not vague language.
- Step 4: the panel closes and is no longer visible. (Alternative: pressing Escape also closes it.)

---

### UT-12 — Backend unavailable: X-ray section shares the page's single error state (error)

**Type:** error
**Priority:** P2
**Surface:** `/watchlist`

**Preconditions:**
- Frontend running at http://localhost:3255.
- Requires the ability to temporarily stop the backend process. Skip this test (and note the skip)
  if you cannot stop the backend — this exact scenario is inherent to `GET /api/watchlist`'s
  pre-existing error handling, unchanged by this phase, so a skip here is low-risk.

**Steps:**
1. Stop the backend process (e.g. Ctrl+C the running backend server, or kill the process).
2. Navigate to `http://localhost:3255/watchlist` (or refresh if already there).
3. Wait a few seconds for the fetch to fail.
4. Restart the backend process afterward.

**Expected Result:**
- A single red-bordered card appears headed "Backend unavailable", with body text starting "The
  watchlist could not load from the API. No entries are shown rather than fabricated values...".
- Neither the entries table, the "Concentration X-ray" section, nor any partial/broken X-ray
  content is shown — there is exactly ONE error state for the whole page, not a second, separate
  error state for the X-ray section (it rides the same `GET /api/watchlist` call).
- No stack trace, blank white screen, or raw JSON is shown to the user.
- After restarting the backend and refreshing, the page returns to normal (entries table + X-ray
  section both render again, unchanged from before the outage).

---

### UT-13 — A name with insufficient overlapping history renders honest NA, never a fabricated value (error)

**Type:** error
**Priority:** P2
**Surface:** `/watchlist`

**Preconditions:**
- Requires a watchlist member with under 60 trading days of overlapping price history.
  **Environment caveat:** the "Add" form only accepts tickers already present in the configured
  ~548-symbol universe (`config.yaml`'s `universe.symbols`), and essentially all of those names
  carry deep, multi-year seeded price history — a genuinely short-history ticker may not exist in
  this environment's live, addable universe. **If no such ticker can be found or added through the
  UI, this exact scenario is already covered by the backend automated test**
  (`apps/backend/tests/test_watchlist_xray.py::test_short_history_member_is_honest_na_never_fabricated`,
  a synthetic fixture that inserts a 10-bar-history ticker directly). In that case, mark this UT
  as satisfied-by-backend-test and record the skip reason in the QA report rather than forcing a
  live reproduction.

**Steps (attempt only if a short-history-eligible ticker is identified):**
1. Navigate to `http://localhost:3255/watchlist`.
2. Add the short-history ticker via the "Ticker" field and "Add" button (see UT-08 for exact
   control names).
3. In the correlation matrix, locate the row and column for the new ticker.
4. Hover a cell in that row/column other than its own self-diagonal cell.
5. Remove the ticker afterward (trash-can icon, see UT-09) to restore the watchlist.

**Expected Result:**
- Every off-diagonal cell in the short-history ticker's row and column displays a muted "—" with
  a dashed cell border, never a colored numeric value.
- The hover tooltip states the exact day counts on each side versus the requirement, e.g.
  "`<TICKER>` vs MSFT: not enough overlapping history for a correlation (`<TICKER>`: `<N>`d, MSFT:
  `<N>`d of the trailing 126d window; need >= 60d each)".
- The rest of the matrix (cells not involving the short-history ticker) is unaffected and still
  shows normal numeric values.

---

### UT-14 — Concentration X-ray is discoverable from the existing Watchlist nav item (ux)

**Type:** ux
**Priority:** P3
**Surface:** navigation / sidebar

**Preconditions:**
- None.

**Steps:**
1. Navigate to `http://localhost:3255` (the dashboard/home page).
2. Locate the left-hand sidebar navigation.
3. Click "Watchlist" (star icon) in the sidebar.
4. Once on the page, scroll down.

**Expected Result:**
- Step 3: the browser navigates to `http://localhost:3255/watchlist` — this is the SAME
  pre-existing nav item as before this phase; no new nav entry was added anywhere in the sidebar.
- Step 4: the "Concentration X-ray" section is visible below the entries table without any further
  navigation — reachable in exactly 1 click from the dashboard/home page (well within a "2 clicks
  from home" bar).

---

### UT-15 — Watchlist with fewer than 2 names shows an honest, distinct "not enough names" state (error) — DESTRUCTIVE, RUN LAST

**Type:** error
**Priority:** P2 *(destructive to the shared/real watchlist — run this test LAST, after every
other case in this plan, and restore immediately afterward; skip it if you are not comfortable
temporarily clearing the shared watchlist)*
**Surface:** `/watchlist`

**Preconditions:**
- **CAUTION:** this test requires temporarily removing entries from the real, persisted watchlist
  (normally ABBV and MSFT).
- Note the current watchlist entries before starting (expected: ABBV, MSFT) so they can be
  restored exactly.

**Steps:**
1. Navigate to `http://localhost:3255/watchlist`.
2. Using the trash-can icon in each row (see UT-09), remove entries until 0 or 1 remain. (If
   possible, test both the 0-entry and the 1-entry state in two passes.)
3. Refresh the page.
4. Observe the area below (or in place of) the entries table.
5. **Restore:** re-add every entry you removed in step 2 via the "Ticker"/"Reason" fields and
   "Add" button (re-add ABBV, then MSFT), returning the watchlist to its original state.

**Expected Result:**
- **0 entries:** the existing "Your watchlist is empty" `EmptyState` is shown, with description
  starting "Add a ticker above with your own reason...". The "Concentration X-ray" section (and
  its own empty state) is **not** shown at all when there are zero entries — the X-ray only
  appears once at least one entry exists.
- **Exactly 1 entry:** the entries table shows the one remaining row; below it, in place of the
  "Concentration X-ray" section, an `EmptyState` is shown titled **"Not enough names yet for an
  X-ray"** with description starting "Add at least one more stock to your watchlist to see how
  concentrated it is...". This wording is visibly different from the "Your watchlist is empty"
  wording, confirming the two states are distinct, not a shared/generic message.
- No crash, no blank page, no JavaScript error at any point.
- Step 5: after restoring, UT-02 through UT-07 pass again unchanged — confirms full recovery.

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | Page loads with entries table + X-ray section | smoke | P1 | `/watchlist` |
| UT-02 | Correlation matrix grid/values/colors/tooltips | happy-path | P1 | `/watchlist` |
| UT-03 | ENB headline shows figure + window | happy-path | P1 | `/watchlist` |
| UT-04 | Cluster badges group/separate correctly | happy-path | P1 | `/watchlist` |
| UT-05 | Sector bars bucket null sector as "Unassigned" | happy-path | P1 | `/watchlist` |
| UT-06 | Theme bars show every membership | happy-path | P1 | `/watchlist` |
| UT-07 | Shared-setup bar reuses existing status colors | happy-path | P1 | `/watchlist` |
| UT-08 | Add-ticker form still works, X-ray updates | regression | P1 | `/watchlist` |
| UT-09 | Remove-entry control still works, X-ray updates | regression | P1 | `/watchlist` |
| UT-10 | Entries table columns/layout unchanged | regression | P3 | `/watchlist` |
| UT-11 | ENB info tooltip opens/closes correctly | ux | P3 | `/watchlist` |
| UT-12 | Backend-unavailable shows single error state | error | P2 | `/watchlist` |
| UT-13 | Short-history member renders honest NA | error | P2 | `/watchlist` |
| UT-14 | X-ray discoverable via existing nav item | ux | P3 | navigation / sidebar |
| UT-15 | <2-name watchlist shows distinct empty state | error | P2 | `/watchlist` |

**P1 tests must all pass for browser QA verdict to be PASS.**

---

## Notes on Classification

- **No dedicated Validation-type case:** this phase added no new form, input, or user action (per
  the phase spec: "New user actions: none — read-only descriptive section"). The pre-existing
  "Add a ticker" form's own validation was not touched this phase, so it is exercised only
  incidentally via the regression cases (UT-08) rather than given a standalone Validation test.
- **Regression priority split:** the skill's default rubric files all regression tests as P3
  ("low risk"). UT-08/UT-09 (the page's only write controls — Add and Remove) are elevated to P1
  because they are high-risk: if either broke, the product's sole pre-existing interactive
  capability on this page would be lost. UT-10 (display-only column check) stays at the default P3.
- **UT-13 and UT-15 carry environment caveats** (addressed in their Preconditions) rather than
  being dropped, because both map directly to a named J-23 Definition-of-Done acceptance step —
  an honest "attempt, and here is the documented fallback if the live environment can't produce
  the precondition" is preferred over silently omitting the check.
