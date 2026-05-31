# Phase goal-i_can_see_the_wealthy_future-iter-11 — UI Test Plan

**Phase:** goal-i_can_see_the_wealthy_future-iter-11
**Date:** 2026-05-31
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3835
**Backend API URL:** http://localhost:8835

---

## Test Cases

<!-- Test IDs use UT-XX prefix to distinguish from the functional test plan's TC-XX IDs. -->
<!-- API/data-contract checks (TC-01…TC-12) are NOT duplicated here — this plan covers user-visible rendering/behaviour only. -->

**Surfaces covered (from the UI surface map):**
- `/stocks` — VCP filter `Select`, teal "VCP" badge in Setup cell, VCP-aware empty-state, sector/setup regression
- `/stocks/[ticker]` — VcpBadge in header card, "VCP — Volatility Contraction Pattern" card, not-flagged state, leaderboard↔detail parity
- `/system-health` — "Forward return: VCP vs non-VCP" breakdown panel, existing-panels regression

**Exact strings taken from source** (`apps/frontend/app/stocks/page.tsx`, `.../[ticker]/page.tsx`, `.../system-health/page.tsx`):
- VCP filter `<label>` text: `VCP`; options: `All`, `VCP only`, `Non-VCP` (aria-label `Filter by VCP pattern`).
- Leaderboard table headers: `#`, `Ticker`, `Sector`, `Leadership`, `Entry Quality`, `Risk`, `Setup`, `Reason`.
- Count indicator format: `{visible} / {total}` (e.g. `4 / 50`).
- Teal badge label: `VCP` (variant `accent`); its `title` tooltip = `reason` + `Pivot $<n>.` + invalidation note, space-joined.
- VCP-only empty-state title: `No stocks match these filters`; description begins `No VCP-flagged name …` / `No non-VCP name …`.
- Detail card title: `VCP — Volatility Contraction Pattern`; sub-labels `Pivot (breakout level)`, invalidation note in warn colour, `Contractions` chips.
- Detail not-flagged: `VCP pattern` label + `No VCP pattern detected.`
- Detail back link: `Back to leaderboard` (→ `/stocks`).
- System-health panel title: `Forward return: VCP vs non-VCP`; rows labelled `VCP` / `non-VCP`; low-sample marker `n < 30 ⚠`; empty label `No VCP / non-VCP cohort had a measurable forward return at this horizon.`

---

### UT-01 — `/stocks` loads with the VCP filter and badge column present (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/stocks`

**Preconditions:**
- Backend running at http://localhost:8835 with a built snapshot DB (latest as-of has stock rows)
- Frontend running at http://localhost:3835

**Steps:**
1. Navigate to `http://localhost:3835/stocks`
2. Wait for the table to render (skeleton disappears)
3. Locate the filter row above the table

**Expected Result:**
- The page heading `Stocks` is visible
- Three filter dropdowns are visible in order: `Sector`, `Setup`, `VCP`
- The `VCP` dropdown shows the options `All`, `VCP only`, `Non-VCP`
- A count indicator in the form `<n> / <total>` is visible (e.g. `50 / 50`)
- The table headers read `#  Ticker  Sector  Leadership  Entry Quality  Risk  Setup  Reason`
- No "Backend unavailable" error card, no blank screen

---

### UT-02 — Filter "VCP only" narrows the leaderboard to flagged names (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/stocks`

**Preconditions:**
- `/stocks` loaded; the latest snapshot flags ≥1 VCP name (teal `VCP` badge visible on at least one row)

**Steps:**
1. Navigate to `http://localhost:3835/stocks`
2. Note the current count shown as `<n> / <total>` (this is the unfiltered count)
3. In the `VCP` dropdown, select `VCP only`
4. Observe the table rows and the count indicator
5. In the `VCP` dropdown, select `Non-VCP`
6. Observe the table rows and the count indicator
7. In the `VCP` dropdown, select `All`

**Expected Result:**
- After step 3 (`VCP only`): every remaining row shows a teal `VCP` badge in its Setup cell; the left number of `<n> / <total>` drops to the flagged-row count; `<total>` (right number) is unchanged
- After step 5 (`Non-VCP`): no remaining row shows a teal `VCP` badge; the count equals total minus the flagged count
- After step 7 (`All`): the full row set returns and the count returns to `<total> / <total>`
- Row ordering (the `#` rank column) is identical within each view to the unfiltered order — the filter never re-sorts

---

### UT-03 — VCP badge tooltip shows reason + pivot + invalidation (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/stocks`

**Preconditions:**
- `/stocks` loaded with ≥1 VCP-flagged row (apply `VCP only` to isolate them)

**Steps:**
1. Navigate to `http://localhost:3835/stocks`
2. Select `VCP only` in the `VCP` dropdown
3. Hover the mouse over the teal `VCP` badge in the first remaining row's Setup cell and wait ~1s for the native tooltip
4. Read the tooltip text

**Expected Result:**
- A teal `VCP` badge (with a help/`cursor-help` pointer) sits next to the setup-status badge in the Setup cell
- The tooltip contains a plain-language reason, a `Pivot $<number>.` fragment (e.g. `Pivot $905.39.`), and an invalidation note sentence (e.g. `VCP invalid below … $<number>`)
- The tooltip is NOT empty and does NOT show `undefined`, `null`, or `Pivot $.`

---

### UT-04 — "VCP only" with zero matches shows an honest empty-state (validation/error)

**Type:** validation
**Priority:** P2
**Surface:** `/stocks`

**Preconditions:**
- A filter combination that matches zero rows. If the latest snapshot has flagged names, combine `VCP only` with a `Setup` value that none of the flagged rows have (e.g. `Avoid`), OR test on an as-of date whose snapshot flags none.

**Steps:**
1. Navigate to `http://localhost:3835/stocks`
2. Select `VCP only` in the `VCP` dropdown
3. Select a `Setup` value held by none of the flagged rows (e.g. `Avoid`)
4. Observe the area where the table was

**Expected Result:**
- The table is replaced by an empty-state card titled `No stocks match these filters`
- The description begins with `No VCP-flagged name` and ends with the honest note `No rows are fabricated to fill the view — clear a filter to see more.`
- No table rows are shown (no fabricated rows)
- The count indicator shows `0 / <total>`

---

### UT-05 — Stock Detail shows the VCP badge + VCP card for a flagged ticker (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/stocks/[ticker]`

**Preconditions:**
- A known VCP-flagged ticker. Get one from `/stocks` → `VCP only` → note the first ticker (call it `<FLAGGED>`).

**Steps:**
1. Navigate to `http://localhost:3835/stocks` and select `VCP only`; click the first ticker link to open its detail page (URL becomes `/stocks/<FLAGGED>`)
2. Wait for the detail body to render
3. Inspect the top header card (the one with the setup-status badge)
4. Scroll to the card titled `VCP — Volatility Contraction Pattern`

**Expected Result:**
- In the header card a teal `VCP` badge appears immediately after the setup-status badge (e.g. after `Breakout-watch`)
- A card titled `VCP — Volatility Contraction Pattern` is visible, also carrying a small `VCP` accent badge
- The card shows: a reason sentence; a `Pivot (breakout level)` label with a `$<number>` value (e.g. `$905.39`); an invalidation note sentence rendered in the warn/amber colour; and a `Contractions` row with one or more numeric chips
- No `undefined` / `$undefined` / `NaN` anywhere in the card

---

### UT-06 — Stock Detail shows honest not-detected state for a non-flagged ticker (error/edge)

**Type:** error
**Priority:** P2
**Surface:** `/stocks/[ticker]`

**Preconditions:**
- A non-flagged ticker. From `/stocks` select `Non-VCP` and note the first ticker (call it `<UNFLAGGED>`).

**Steps:**
1. Navigate to `http://localhost:3835/stocks/<UNFLAGGED>`
2. Wait for the detail body to render
3. Inspect the header card and the VCP card area

**Expected Result:**
- No teal `VCP` badge appears in the header card (only the setup-status badge)
- The VCP card region shows the label `VCP pattern` and the line `No VCP pattern detected.`
- No `Pivot (breakout level)` value, no invalidation number, and no contraction chips are rendered (nothing fabricated)

---

### UT-07 — Detail VCP values are identical to the leaderboard tooltip (regression, J-06)

**Type:** regression
**Priority:** P1
**Surface:** `/stocks` ↔ `/stocks/[ticker]`

**Preconditions:**
- A VCP-flagged ticker `<FLAGGED>` identified in UT-05.

**Steps:**
1. On `http://localhost:3835/stocks` (with `VCP only`), hover `<FLAGGED>`'s teal `VCP` badge and record the `Pivot $<number>.` value and the invalidation note from the tooltip
2. Click `<FLAGGED>` to open `/stocks/<FLAGGED>`
3. On the detail page read the `Pivot (breakout level)` value and the invalidation note in the `VCP — Volatility Contraction Pattern` card

**Expected Result:**
- The pivot value on the detail card equals the `Pivot $<number>` value from the leaderboard tooltip, to the same cents (e.g. both `$905.39`)
- The invalidation note text on the detail card is the same sentence shown in the leaderboard tooltip
- (Confirms leaderboard and detail serve the byte-identical stored row — single source of truth)

---

### UT-08 — Sector + Setup filters still work and ranking unchanged (regression, J-02)

**Type:** regression
**Priority:** P1
**Surface:** `/stocks`

**Preconditions:**
- `/stocks` loaded with the VCP filter left at `All`.

**Steps:**
1. Navigate to `http://localhost:3835/stocks` (VCP dropdown = `All`)
2. Record the first 5 tickers in display order
3. Select a specific value in the `Sector` dropdown (e.g. `Technology`)
4. Observe the rows and count
5. Reset `Sector` to `All sectors`; select a specific `Setup` (e.g. `Breakout-watch`)
6. Observe the rows and count
7. Reset both filters to `All`

**Expected Result:**
- After step 3: only rows whose Sector equals the chosen sector remain; count `<n> / <total>` updates accordingly
- After step 5: only rows whose Setup badge equals the chosen status remain
- After step 7: the full list returns and the first 5 tickers match the order recorded in step 2 (ranking is unchanged — the new VCP filter did not disturb existing filters or sort order)

---

### UT-09 — System Health shows the "VCP vs non-VCP" breakdown panel (happy path, J-16)

**Type:** happy-path
**Priority:** P1
**Surface:** `/system-health`

**Preconditions:**
- Backend + frontend running; walk-forward backfill complete (the page shows forward-test panels, not the "No forward-tested evidence yet" empty-state).

**Steps:**
1. Navigate to `http://localhost:3835/system-health`
2. Wait for the dashboard to render
3. Locate the panel titled `Forward return: VCP vs non-VCP` (in the breakdown grid alongside `Forward return by setup type` and `Forward return by market regime`)
4. Read its two rows

**Expected Result:**
- A panel titled `Forward return: VCP vs non-VCP` is present
- It renders two rows labelled `VCP` and `non-VCP`
- Each row shows a mean forward return value and a sample size `n` (e.g. `+3.18%  n=27`)
- Any row with `n < 30` shows the low-sample `⚠` marker; a cohort with no measurable return shows the NA em-dash `—` (never a fabricated number)
- The page's `Survivorship bias` banner is present above the grid

---

### UT-10 — Existing System Health panels unchanged (regression, J-09/J-10)

**Type:** regression
**Priority:** P2
**Surface:** `/system-health`

**Preconditions:**
- `/system-health` loaded with evidence (as UT-09).

**Steps:**
1. Navigate to `http://localhost:3835/system-health`
2. Confirm the presence of each pre-existing panel
3. Click a different `Horizon` button (e.g. `60d`) and confirm the new VCP panel updates alongside the others

**Expected Result:**
- All pre-existing panels still render: `Forward return by score bucket`, `Excess vs benchmarks`, `Forward return by setup type`, `Forward return by market regime`, and `Control-group comparison — selection vs sector beta`
- Switching the horizon updates every panel's numbers including the new `Forward return: VCP vs non-VCP` panel (it participates in the same horizon switch)
- No panel shows a crash, blank body, or `undefined`

---

### UT-11 — VCP feature is discoverable without docs (ux)

**Type:** ux
**Priority:** P3
**Surface:** `/stocks`

**Steps:**
1. Navigate to `http://localhost:3835/stocks`
2. Without prior instruction, look for any indication of the VCP capability

**Expected Result:**
- A labelled `VCP` filter dropdown is plainly visible in the filter row (discoverable in 0 clicks)
- Teal `VCP` badges visibly mark flagged rows
- The badge has a help cursor, signalling it is hoverable for an explanation
- (Note: the `/methodology` glossary entry for VCP is intentionally deferred to the next iteration — its absence is NOT a failure here.)

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | `/stocks` loads with VCP filter + badge column | smoke | P1 | `/stocks` |
| UT-02 | "VCP only" / "Non-VCP" narrows rows; "All" restores | happy-path | P1 | `/stocks` |
| UT-03 | VCP badge tooltip = reason + pivot + invalidation | happy-path | P1 | `/stocks` |
| UT-04 | "VCP only" zero-match honest empty-state | validation | P2 | `/stocks` |
| UT-05 | Detail VCP badge + VCP card for flagged ticker | happy-path | P1 | `/stocks/[ticker]` |
| UT-06 | Detail "No VCP pattern detected." for non-flagged | error | P2 | `/stocks/[ticker]` |
| UT-07 | Detail pivot/invalidation == leaderboard tooltip | regression | P1 | `/stocks` ↔ detail |
| UT-08 | Sector + Setup filters intact; ranking unchanged | regression | P1 | `/stocks` |
| UT-09 | "VCP vs non-VCP" forward-return panel renders | happy-path | P1 | `/system-health` |
| UT-10 | Existing health panels unchanged across horizons | regression | P2 | `/system-health` |
| UT-11 | VCP filter/badge discoverable | ux | P3 | `/stocks` |

**P1 tests must all pass for the browser QA verdict to be PASS.**

## Coverage Notes

- API/data-contract correctness (no-recompute keystone, faithful mirror, `by_vcp` shape, no-magic-numbers, config validation) is covered by the functional test plan TC-01…TC-12 and is **not** duplicated here.
- **UT-02/UT-03/UT-05** depend on the latest snapshot actually flagging ≥1 VCP name. If it honestly flags none, the demonstrable path becomes UT-04's empty-state + UT-06's not-detected state; record the dataset condition rather than failing J-16 (an honest empty-state is acceptable per the spec).
- The `/methodology` VCP glossary entry (J-12) is out of scope this iteration — do not test it as a gap.
- At report time both services answered HTTP 200 (FE :3835, API :8835). The latest as-of snapshot served by the API is `2026-05-28`.

End of test plan.
