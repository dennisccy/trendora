# Phase goal-mcp-loop-iter-41 — UI Test Plan

**Phase:** goal-mcp-loop-iter-41
**Date:** 2026-07-15
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3255

---

## Context

This phase (J-25 / B-205) adds one new, read-only **"Historical drawdown & dry-spell expectations"**
panel appended inside every existing certified-claim card on `/evidence` — no new page, no new route,
no new controls. All test cases below therefore target `/evidence`, plus the required-still-passing
journeys the phase spec explicitly gates on (J-01, J-02, J-04, J-05, J-10, J-11, J-13, J-20).

**Claim ordering note:** today's live ledger (verified 2026-07-15, the same day this plan was written)
renders the 7 certified claims in a fixed order. Steps below identify "the first card" / "the second
card" by both position AND by their Hypothesis chip text / badges, so a tester can still locate the
right card if the ledger order ever shifts — always prefer the chip/badge text over raw position if
they disagree.

**Priority note (deviation from the default P1/P2/P3 skill mapping):** the phase's own Definition of
Done explicitly gates on 7 required-still-passing journeys (J-01, J-02, J-04, J-05, J-10, J-11, J-13,
J-20) remaining green, verified live this iteration (no golden-replay lane exists for a FULL iteration —
see `docs/phases/goal-mcp-loop-iter-41.md` NOTES). These are therefore treated as **P1**, not the
skill's generic "regression = P3 (low risk)" default — a break in any of them is a hard gate, not an
informational nice-to-have.

---

## Test Cases

<!-- Test IDs use UT-XX prefix to distinguish from the functional test plan's TC-XX IDs. -->

---

### UT-01 — `/evidence` loads with all 7 certified-claim cards, each carrying the new panel (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/evidence`

**Preconditions:**
- Frontend is running at http://localhost:3255 and the backend is reachable
- The evidence ledger is populated (today: 7 certified claims, 0 PASS / 7 FAIL)
- The database has completed its full-universe rebuild for this iteration (so the two new columns are
  populated rather than NULL — see `reports/perf-budgets.md` for the rebuild record)

**Steps:**
1. Navigate to `http://localhost:3255/evidence`
2. Wait for the page to finish loading (the 3-bar pulsing gray skeleton disappears)
3. Confirm the page heading reads exactly "Evidence"
4. Count the visible claim cards (elements with `data-testid="evidence-claim-row"`)
5. On each of the 7 cards, scroll within the card past its 5-field grid and confirm a heading whose text
   starts with "Historical drawdown & dry-spell expectations (" is present, followed by a table
   (`data-testid="evidence-expectations-table"`)

**Expected Result:**
- Page renders without a blank screen and without the red "Backend unavailable" error card
- The heading "Evidence" is visible at the top
- Exactly 7 claim cards render (NOT the "No certified claims yet" empty state, `data-testid="evidence-empty"`)
- Every one of the 7 cards shows the new panel (`data-testid="evidence-expectations-panel"`) below its
  existing field grid, each containing a 5-row table
- No visible JavaScript error overlay; the page's data returns quickly (well under 1 second, no extended
  spinner) — consistent with a warm cache

---

### UT-02 — User reads real, well-populated historical figures on the first claim card (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/evidence`

**Preconditions:**
- `/evidence` loads successfully
- The FIRST claim card's "Hypothesis" field shows badges reading "factor=leadership_score",
  "decile=10", "horizon=20" (today's ledger order — if a different claim is first, locate this one by
  its chips instead of position)

**Steps:**
1. Navigate to `http://localhost:3255/evidence`
2. Wait for the page to load
3. Locate the FIRST claim card in the list (`data-testid="evidence-claim-row"`) and confirm its
   "Hypothesis" field shows badges "factor=leadership_score", "decile=10", "horizon=20"
4. Scroll down within that card past the "Forward-walk score-to-date" field until a heading reading
   "Historical drawdown & dry-spell expectations (20-day hold)" is visible
5. In the table below that heading, locate the row whose "Phase" badge reads "Expansion" — it is the
   FIRST of 5 rows, in this fixed order: Expansion, Pullback, Correction, Bear, Recovery
6. Read the "Max-DD depth" cell for the Expansion row
7. Read the "Underwater" cell and the "Time to recover" cell for the same Expansion row
8. Scroll slightly further down and read the two sentences directly below the table
   (`data-testid="evidence-expectations-method-note"` and `data-testid="evidence-expectations-survivorship"`)

**Expected Result:**
- The panel heading reads exactly "Historical drawdown & dry-spell expectations (20-day hold)" — the
  "20" matches the "horizon=20" chip read in step 3
- The Expansion row's "Max-DD depth" cell reads exactly "-7.70% (p90 -3.72%) n=1264"
- The Expansion row's "Underwater" cell reads exactly "20.0d (p90 20.0d) n=1264"
- The Expansion row's "Time to recover" cell reads exactly "0.0d (p90 6.0d) n=769" — a smaller `n` than
  the other two columns is CORRECT: it means only 769 of the 1264 observations recovered within the
  20-day window; the remainder are honestly excluded, never zeroed
- The first sentence below the table starts with "Longest losing streak is counted at the walk-forward
  cadence"
- The second sentence starts with "Walk-forward evidence now spans up to ~30 years of history" and ends
  with "Read the edge as an upper bound, not a guarantee."
- Nowhere in the panel does the text contain "expect to", "forecast", "predict", "target", "buy",
  "sell", "trim", "reduce", or "you will"

---

### UT-03 — Below-floor "Longest losing streak" reads insufficient while sibling cells stay real (validation)

**Type:** validation
**Priority:** P2
**Surface:** `/evidence`

**Preconditions:**
- Same FIRST claim card as UT-02 (Hypothesis chips "factor=leadership_score", "decile=10", "horizon=20")

**Steps:**
1. Navigate to `http://localhost:3255/evidence` and wait for load
2. Locate the FIRST claim card
3. In its expectations table, locate the row whose "Phase" badge reads "Correction" — the 3rd of 5 rows
4. Read the "Longest losing streak" cell (rightmost column) for that row
5. Read the "Max-DD depth", "Underwater", and "Time to recover" cells on the SAME Correction row

**Expected Result:**
- The "Longest losing streak" cell for the Correction row reads exactly "insufficient (n=5)" — rendered
  in muted/gray text, not a fabricated streak number (5 walk-forward cadence dates, below the
  `streak_min_n` floor)
- The other three cells on the SAME Correction row each show a normal value, NOT "insufficient" —
  pattern `<number>% (p90 <number>%) n=<count>` for Max-DD depth, `<number>d (p90 <number>d) n=<count>`
  for Underwater and Time to recover — confirming the honesty floor is applied per-measure, not per-row
- No cell in this row is blank, or reads "undefined", "NaN", or "null"

---

### UT-04 — Zero-observation cohort×phase renders insufficient(n=0) across all four measures (error)

**Type:** error
**Priority:** P2
**Surface:** `/evidence`

**Preconditions:**
- `/evidence` loaded
- The SECOND claim card carries a "FAIL" badge and a "Regime: Risk-on" badge at the top, with Hypothesis
  chips "kind=event-study", "subject=Breakout-watch" (today's ledger order — locate by badge/chip text
  if position differs)

**Steps:**
1. Navigate to `http://localhost:3255/evidence` and wait for load
2. Locate the SECOND claim card — confirm it shows badges "FAIL" and "Regime: Risk-on"
   (`data-testid="evidence-claim-regime"`) at the top, and Hypothesis chips "kind=event-study",
   "subject=Breakout-watch"
3. Scroll to its expectations table
4. Read all four measure cells (Max-DD depth, Underwater, Time to recover, Longest losing streak) on
   the row whose "Phase" badge reads "Correction"
5. Read all four measure cells on the row whose "Phase" badge reads "Bear"

**Expected Result:**
- All 4 cells on the Correction row read exactly "insufficient (n=0)"
- All 4 cells on the Bear row read exactly "insufficient (n=0)"
- The page does NOT show a crash, blank card, error boundary message, or any cell reading "undefined",
  "NaN", "null", or a blank space where a value should be
- The rest of the same card (verdict badge, Hypothesis chips, the OTHER 3 phase rows) still renders
  normally around this zero-observation state — the degradation is isolated to the two affected rows

---

### UT-05 — Panel gracefully renders nothing when `expectations` is absent (contract check, best-effort)

**Type:** error
**Priority:** P3
**Surface:** `/evidence` + its `GET .../api/evidence` network response

**Preconditions:**
- Browser DevTools available
- **Known limitation:** no claim in today's live ledger currently reproduces the absent-panel VISUAL
  state by simple clicking — all 7 claims resolve a non-null `expectations` today. This test confirms
  the API contract is intact and every card has a panel today, as the closest live proxy; it does not
  exercise the "no panel" rendering path directly.

**Steps:**
1. Navigate to `http://localhost:3255/evidence`
2. Open DevTools (F12, or right-click → Inspect) and switch to the "Network" tab
3. Reload the page
4. Find the request whose URL path ends in `/api/evidence` and open its "Response" (or "Preview") tab
5. Confirm every one of the 7 objects in the `claims` array has a non-null `expectations` key
6. Scroll through all 7 rendered claim cards and confirm every single one shows the "Historical drawdown
   & dry-spell expectations" panel (none is missing the panel or shows a broken/empty box in its place)

**Expected Result:**
- Every one of the 7 claim objects in the API response carries a populated `expectations` object — none
  is `null` or missing the key
- Every one of the 7 rendered cards shows the panel — no card has a blank gap or broken layout where the
  panel would otherwise be
- For future regression coverage: if a claim ever DOES resolve `expectations: null` (e.g. a session-less
  payload or an unresolvable cohort), the correct behavior is that its card renders normally with NO
  panel section at all — no error box, no stuck "Loading…" text, no blank placeholder box. Re-test this
  path directly if such a claim ever appears in the ledger.

---

### UT-06 — Existing verdict/field grid on `/evidence` is unchanged; new panel is strictly appended below (regression, J-05 / J-11)

**Type:** regression
**Priority:** P1
**Surface:** `/evidence`

**Preconditions:**
- `/evidence` loads with 7 claim cards

**Steps:**
1. Navigate to `http://localhost:3255/evidence`
2. On EACH of the 7 claim cards, read the top verdict badge
3. On the first claim card, confirm the field grid shows exactly these 5 labels, in this order:
   "Hypothesis", "Out-of-sample verdict", "Control comparison (vs SPY)", "Registration date",
   "Forward-walk score-to-date"
4. Confirm none of these 5 fields' values look broken (e.g. no field reads "undefined")
5. Confirm the new "Historical drawdown & dry-spell expectations" panel appears strictly BELOW all 5
   fields on every card — never inserted between them
6. Search the page (Ctrl+F / Cmd+F) for the strings "+21.34%", "+6.36%", and "p=0.0004998" (stale
   pre-30-year-refresh values that must not survive on the current ledger)

**Expected Result:**
- All 7 verdict badges read "FAIL" (0/7 PASS today) — unchanged from before this phase
- The 5 field labels appear in the exact order listed, on every one of the 7 cards
- The new panel appears exactly once per card, always after (below) the 5-field grid — never interleaved
  into it
- Zero matches for "+21.34%", "+6.36%", or "p=0.0004998" anywhere on the page (no stale edge survives —
  J-11)

---

### UT-07 — Regime-conditioned claim still shows a correct, clearly-labeled regime badge (regression, J-04)

**Type:** regression
**Priority:** P1
**Surface:** `/evidence`, `/` (dashboard, cross-check only)

**Preconditions:**
- The SECOND claim card carries Hypothesis chips "kind=event-study", "subject=Breakout-watch" (today's
  ledger order)

**Steps:**
1. Navigate to `http://localhost:3255/evidence`
2. Locate the SECOND claim card
3. Confirm a badge next to the "FAIL" verdict badge reads "Regime: Risk-on"
   (`data-testid="evidence-claim-regime"`)
4. Separately, navigate to `http://localhost:3255` (dashboard) and note the current phase shown in the
   "Market Phase & Severity" card

**Expected Result:**
- The claim card's regime badge reads exactly "Regime: Risk-on" — a distinct accent-colored badge
  positioned next to the FAIL verdict badge
- The label is present and legible (not blank, not "Regime: undefined")
- This is an informational cross-check, not a strict equality requirement — "Risk-on" reflects the
  claim's own cohort selector and may legitimately differ from today's live dashboard phase. The pass
  bar is: a regime label IS present and clearly readable on this row, per J-04's "evidence is
  regime-scoped and clearly labeled" acceptance criterion

---

### UT-08 — GO preflight strip still renders correctly on `/evidence`, unaffected by the new panel (regression, J-20)

**Type:** regression
**Priority:** P1
**Surface:** `/evidence` (the strip is global — mounted once in the root layout, so it renders on every route)

**Preconditions:** none beyond the frontend running

**Steps:**
1. Navigate to `http://localhost:3255/evidence`
2. Look at the thin strip directly below the very top header bar, above the "Evidence" page heading
   (`data-testid="preflight-banner"`)
3. Read its text and note its background color

**Expected Result:**
- A thin strip is visible reading one of: "GO — today's board is current." (green), "DEGRADED — treat
  today's board with caution." (amber/warning), or "NO-GO — do not rely on today's board." (red/danger)
- The strip text is not cut off, overlapped, or hidden by the new panel content below it
- If it reads "NO-GO — do not rely on today's board.", treat this as a DATA-freshness condition unrelated
  to this phase's code — only fail this test if the strip is missing entirely or visually broken
  (overlapping text, wrong page position), not merely for showing a non-GO state

---

### UT-09 — Stock-detail deep-history chart range controls still work (regression, J-10)

**Type:** regression
**Priority:** P1
**Surface:** `/stocks/AAPL`

**Preconditions:**
- AAPL exists in the seeded universe

**Steps:**
1. Navigate to `http://localhost:3255/stocks/AAPL`
2. Confirm the page heading reads exactly "AAPL"
3. Scroll down to the card titled "Price & moving averages"
4. Confirm two buttons are visible in that card's header controls: "Recent" and "Full history"
   (`data-testid="chart-range-recent"` / `data-testid="chart-range-full"`)
5. Note the chart's caption text (`data-testid="chart-window-caption"`) BEFORE clicking
6. Click the "Full history" button
7. Read the caption text again, after the chart re-renders

**Expected Result:**
- Page heading reads exactly "AAPL"
- The "Price & moving averages" card is present with both "Recent" and "Full history" buttons
  (`data-testid="chart-range-control"`)
- After clicking "Full history", the caption matches the pattern "<number> bars · as of <date> ·
  history since <date>", and the "history since" date is much earlier than the one shown before the
  click — confirming the deep multi-year history loaded, not just a recent window

---

### UT-10 — Data Manager page still loads correctly (regression, J-13)

**Type:** regression
**Priority:** P1
**Surface:** `/data`

**Preconditions:** none

**Steps:**
1. Navigate to `http://localhost:3255/data`
2. Wait for the page to load

**Expected Result:**
- Page heading reads exactly "Data Manager"
- Subtitle text begins with "Grow the dataset on demand"
- A "Dataset coverage" panel is visible
- No blank page and no error message

---

### UT-11 — "Proven" / "Not yet proven" badges still render correctly (regression, J-01)

**Type:** regression
**Priority:** P1
**Surface:** `/stocks`, `/stocks/AAPL`

**Preconditions:** none

**Steps:**
1. Navigate to `http://localhost:3255/stocks`
2. Find any row in the leaderboard table and look directly beneath its Leadership, Entry Quality, and
   Risk score values
3. Navigate to `http://localhost:3255/stocks/AAPL`
4. Look directly beneath each of the 3 score cards (Leadership, Entry Quality, Risk)
5. Hover over one "Not yet proven" badge (`data-testid="evidence-badge"`)

**Expected Result:**
- On `/stocks`, all 3 score cells in the sampled row show a small badge reading "Not yet proven" (since
  today's ledger is 0/7 PASS, no signal should currently show "Proven")
- On `/stocks/AAPL`, all 3 score cards likewise show a "Not yet proven" badge beneath their score
- Hovering shows a tooltip starting with "Not yet proven — no certified out-of-sample evidence"

---

### UT-12 — Score-drill "Why proven?" toggle correctly stays absent for not-yet-proven scores (regression, J-02)

**Type:** regression
**Priority:** P1
**Surface:** `/stocks/AAPL`

**Preconditions:**
- `/stocks/AAPL` loads; the ledger is 0/7 PASS (no score is currently proven)

**Steps:**
1. Navigate to `http://localhost:3255/stocks/AAPL`
2. On each of the 3 score cards (Leadership, Entry Quality, Risk), look immediately below the "Not yet
   proven" badge
3. Confirm there is no "Why proven?" button or any other drill-down control on any of the 3 cards

**Expected Result:**
- No "Why proven?" button (`data-testid="score-proof-toggle"`) appears on any of the 3 score cards —
  since none is currently proven, this honest absence is CORRECT behavior, not a bug
- No broken/empty box, stuck loading spinner, or dangling control appears where a drill-down would go
- Each card otherwise renders its score value and "Not yet proven" badge normally

---

### UT-13 — Method note and survivorship caveat are visible without extra interaction and read identically across cards (ux)

**Type:** ux
**Priority:** P3
**Surface:** `/evidence`

**Preconditions:**
- `/evidence` loaded with 7 claim cards

**Steps:**
1. Navigate to `http://localhost:3255/evidence`
2. On the FIRST claim card, scroll to the bottom of its expectations panel and read the two sentences
   below the table — do not click, hover, or expand anything first
3. Scroll down to a THIRD claim card (any card other than the first two) and read its two sentences in
   the same position
4. Compare the two sentences word-for-word between the first card and this third card

**Expected Result:**
- Both sentences are visible by scrolling alone — no accordion, "show more" link, or tooltip-only reveal
  is needed to read them
- The wording is identical between the two cards (same method note, same survivorship caveat) —
  confirming the copy is server-provided and consistent, never authored per-claim in the browser
- Both sentences read as historical/descriptive, with no promise or forecast language

---

### UT-14 — Phase badges inside the new table are flat gray, unlike the color-coded phase badge elsewhere (ux, known minor gap)

**Type:** ux
**Priority:** P3
**Surface:** `/evidence` vs `/` (dashboard)

**Preconditions:** none

**Steps:**
1. Navigate to `http://localhost:3255/evidence`
2. On any claim card's expectations table, look at the "Phase" column badges — e.g. the "Bear" row's
   badge
3. Note their color/styling across all 5 phase rows
4. Navigate to `http://localhost:3255` (dashboard)
5. Find the "Market Phase & Severity" card and note the color of its phase badge

**Expected Result:**
- The new table's phase badges (Expansion / Pullback / Correction / Bear / Recovery) are ALL the same
  flat neutral gray, regardless of which phase they name
- The dashboard's "Market Phase & Severity" badge is color-coded — green for Expansion/Recovery, amber
  for Pullback, red for Bear/Correction
- This mismatch is EXPECTED and already tracked as a MINOR, cosmetic-only gap in
  `reports/reviews/goal-mcp-loop-iter-41-review.md`. This test exists only to confirm the known gap is
  still accurately described (i.e. no worse than documented — the underlying figures are correct
  regardless of badge color). Do not file this as a new bug.

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | Page loads, panel present on all 7 cards | smoke | P1 | `/evidence` |
| UT-02 | Read real Expansion-row figures (card 1) | happy-path | P1 | `/evidence` |
| UT-03 | Below-floor streak insufficient, siblings real | validation | P2 | `/evidence` |
| UT-04 | Zero-observation cohort insufficient(n=0) | error | P2 | `/evidence` |
| UT-05 | Absent-panel contract check (best-effort) | error | P3 | `/evidence` (network) |
| UT-06 | Existing field grid / verdict badges unchanged | regression | P1 | `/evidence` |
| UT-07 | Regime badge still correct | regression | P1 | `/evidence` |
| UT-08 | GO preflight strip unaffected | regression | P1 | `/evidence` |
| UT-09 | Stock deep-history chart controls | regression | P1 | `/stocks/AAPL` |
| UT-10 | Data Manager page loads | regression | P1 | `/data` |
| UT-11 | Proven / Not yet proven badges | regression | P1 | `/stocks`, `/stocks/AAPL` |
| UT-12 | Score-drill honest absence | regression | P1 | `/stocks/AAPL` |
| UT-13 | Caveat visible + consistent wording | ux | P3 | `/evidence` |
| UT-14 | Phase-badge color gap (known minor) | ux | P3 | `/evidence` vs `/` |

**P1 tests must all pass for browser QA verdict to be PASS.** (Note: P1 here includes every
required-still-passing journey per this iteration's DoD, not just smoke/happy-path — see "Priority
note" in Context above.)
