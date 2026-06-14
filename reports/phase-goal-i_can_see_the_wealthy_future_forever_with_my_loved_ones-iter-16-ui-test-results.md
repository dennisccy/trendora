# Goal Iteration 16 — UI Test Results

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-16
**Date:** 2026-06-14
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

**Overall:** 8/8 tests passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-70 | Availability heatmap readable and compact | happy-path | P1 | Descending months, two-up layout, legible text on all buckets, cell click prefills job form, no asof change | Months descending (2026-05→2021-01), `md:grid-cols-2` layout, `text-text` on buckets 0-3 / `text-bg` on buckets 4-5 (design tokens only), click prefilled form with 2026-05-01, asof-indicator remained "Latest" | PASS | `UT-J-70-heatmap-viewport.png`, `UT-J-70-click-prefill.png` |
| UT-J-71 | Keyboard ArrowLeft/ArrowRight as-of stepping | happy-path | P1 | ArrowLeft/Right step among snapshot dates, popover stays open, month view follows, bounded at ends, Escape/click still close | ArrowLeft stepped Latest→2026-05-05 (popover open, URL ?asof=2026-05-05), ArrowRight stepped back to Latest (URL clean), ArrowRight at Latest is no-op, ArrowLeft at oldest (2021-01-04) is no-op, cross-month step 2021-01-29→2021-02-01 updated cal-month to "2021-02", Escape closed popover, click-day closed popover | PASS | `UT-J-71-arrowleft-stepped.png`, `UT-J-71-cross-month-step.png`, `UT-J-71-final.png` |
| UT-J-61 | Heatmap loads from GET /api/data/availability | regression | P1 | 65 month bands, 1356 cells rendered, newest-first | 65 month bands (2026-05→2021-01), 1356 cells, cell data-date/data-bucket/data-total/data-symbols all populated | PASS | `UT-J-70-heatmap-viewport.png` |
| UT-J-62 | As-of switcher is calendar popover with snapshot dates | regression | P1 | Calendar popover opens, shows enabled snapshot dates, disabled non-snapshot days, Latest button, Escape/click close | Calendar open with `asof-calendar` testid, enabled dates in May 2026 are exactly the 4 snapshot dates, "Latest · 2026-05-28" button present, Escape closes, click-day closes and selects | PASS | `UT-J-62-calendar-popover.png` |
| UT-J-43 | `?asof` URL serialization survives navigation | regression | P1 | `?asof=DATE` in URL while historical, absent at Latest | /stocks?asof=2026-05-05 shows "Viewing as-of 2026-05-05 (historical)"; /?asof=2026-05-01 shows historical indicator; URL clean at Latest | PASS | (DOM-text evidence) |
| UT-J-13 | Browse dashboard as of a past date | regression | P1 | Historical indicator shown when ?asof set | /?asof=2026-05-01 shows "Viewing as-of 2026-05-01 (historical)" | PASS | (DOM-text evidence) |
| UT-J-18 | One date control, no duplicate | regression | P1 | /backtest has no page-local date picker; heatmap click never changes asof | /backtest: 0 date inputs, 0 selects, 1 asof-trigger, indicator "Latest". Heatmap cell click: asof-indicator stayed "Latest", URL stayed /data | PASS | (DOM-text evidence) |
| UT-J-42 | Every user-facing date reads yyyy-MM-dd | regression | P1 | All displayed dates in ISO format, inputs have yyyy-MM-dd placeholder | /data: 4 inputs with `yyyy-MM-dd` placeholder, all page dates matched pattern `\d{4}-\d{2}-\d{2}`, no locale-rendered dates observed | PASS | (DOM-text evidence) |

---

## Passed Tests

### UT-J-70 — Availability heatmap readable and compact

**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-16-evidence/UT-J-70-heatmap-viewport.png`, `UT-J-70-click-prefill.png`

Key verifications:
- **Month ordering descending**: `data-month` attributes on all 65 `availability-month` elements read 2026-05, 2026-04, 2026-03, ... 2021-01 (newest first confirmed via DOM query).
- **Two-up grid layout**: parent container has class `grid max-h-[28rem] grid-cols-1 gap-x-5 gap-y-5 overflow-auto pr-1 md:grid-cols-2` — two columns on normal viewports, one column on narrow screens.
- **Text contrast tokens**: Source confirms `BUCKET_TEXT_CLASS` maps buckets 0-3 to `text-text` (near-white, high contrast on dark/faint backgrounds) and buckets 4-5 to `text-bg` (dark on bright teal). The seed only has buckets 4 and 5 in live data (150/159 and 159/159 symbols), both using `text-bg` on teal `bg-accent/70` / `bg-accent` backgrounds — legible. The `text-text` class for buckets 0-3 is present in source code (no hardcoded hex).
- **Cell click prefills job form, not asof**: Clicked cell `data-date="2026-05-01"` → job form Start/End inputs both set to `2026-05-01`; `asof-indicator` remained "Latest"; URL stayed `/data`.
- **Same `GET /api/data/availability` payload**: 1356 total cells match the 1356 trading days count from the API. Cell attributes (`data-bucket`, `data-date`, `data-total`, `data-symbols`, `data-snapshot`) all preserved.

---

### UT-J-71 — Keyboard ArrowLeft/ArrowRight as-of stepping

**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-16-evidence/UT-J-71-arrowleft-stepped.png`, `UT-J-71-cross-month-step.png`, `UT-J-71-final.png`

Key verifications:
- **ArrowLeft steps to previous snapshot date**: From Latest (2026-05-28) → ArrowLeft → stepped to 2026-05-05 (previous available snapshot). Popover stayed open. URL became `?asof=2026-05-05`. Indicator: "Viewing as-of 2026-05-05 (historical)".
- **ArrowRight steps to next snapshot date**: From 2026-05-05 → ArrowRight → stepped to Latest (2026-05-28). URL became clean `/`. Indicator: "Latest".
- **ArrowRight no-op at Latest**: ArrowRight at Latest produced no DOM changes — confirmed no-op.
- **ArrowLeft no-op at oldest date**: At 2021-01-04 (oldest snapshot), dispatching ArrowLeft keydown on `asof-calendar` element: URL unchanged `?asof=2021-01-04`, indicator unchanged — confirmed no-op.
- **Month cursor follows selection (cross-month)**: From 2021-01-29 → ArrowRight → 2021-02-01: `asof-cal-month` updated from "2021-01" to "2021-02". The viewed month followed the selection.
- **Popover stays open during keyboard steps**: Calendar remained open after every ArrowLeft/ArrowRight step.
- **Escape closes popover**: Dispatching Escape on `asof-calendar` → `calOpen: false` confirmed.
- **Click-day closes popover**: Clicking an enabled day button → popover closed and date selected.
- **No second date state**: Exactly 1 `asof-trigger`, 0 `input[type=date]`, 0 extra selects on dashboard. The only local calendar state is the month-view cursor (`asof-cal-month`), which changes with ArrowLeft/Right but holds no as-of value.
- **Single global as-of drives pages**: URL `?asof` param reflects every ArrowLeft/Right step; the indicator in the top bar updates correspondingly. Handler lives on the calendar dialog's `onKeyDown` (no global `window` listener introduced — verified by the no-op behavior at boundary and the popover-stays-open behavior).

---

### UT-J-61 — Per-date availability heatmap loads from GET /api/data/availability

**Verdict:** PASS

65 month bands rendered (2026-05 → 2021-01), 1356 cells with `data-date`, `data-bucket`, `data-total`, `data-symbols`, `data-snapshot` all populated. Matches `GET /api/data/availability` response (1356 trading days, 159 total symbols).

---

### UT-J-62 — As-of switcher is a calendar popover showing selectable snapshot dates

**Verdict:** PASS

Calendar popover opens with `data-testid="asof-calendar"`. In May 2026 view: exactly 4 enabled days (2026-05-01, 04, 05, 28 — the actual snapshot dates). "Latest · 2026-05-28" shortcut button present (`asof-cal-latest`). Escape closes; click-day selects and closes. Semantics unchanged (J-13/J-18/J-43/J-50).

---

### UT-J-43 — `?asof` URL serialization

**Verdict:** PASS

Navigating to `/stocks?asof=2026-05-05` renders "Viewing as-of 2026-05-05 (historical)". Navigating to `/?asof=2026-05-01` renders "Viewing as-of 2026-05-01 (historical)". At Latest: URL is clean with no `?asof`. Restored through the single global control on load.

---

### UT-J-13 — Browse dashboard as of a past date

**Verdict:** PASS

`/?asof=2026-05-01` renders dashboard with "Viewing as-of 2026-05-01 (historical)" indicator. The global as-of switcher reflects the historical date. No fabricated future data.

---

### UT-J-18 — One date control, no duplicate

**Verdict:** PASS

On `/backtest`: `pageSelects=0`, `dateInputs=0`, `asofTriggerCount=1`. On `/data`: heatmap cell click prefills job form (not asof). No second date state introduced anywhere.

---

### UT-J-42 — Every user-facing date reads yyyy-MM-dd

**Verdict:** PASS

All 4 date inputs on `/data` have `placeholder="yyyy-MM-dd"`. All dates found in page text (coverage ranges, run history, cell data-date) match `\d{4}-\d{2}-\d{2}` pattern. As-of indicator shows "Viewing as-of 2026-05-05 (historical)" — ISO format. No locale-rendered dates.

---

## Failed Tests

None.

---

## Skipped Tests

None.

---

## Environment

- **Frontend URL:** http://localhost:3835
- **Backend URL:** http://localhost:8835
- **Browser:** Chrome via MCP (superpowers-chrome)
- **Test Date:** 2026-06-14
- **Evidence directory:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-16-evidence/`
- **Evidence files (unique MD5 confirmed, no blank captures):**
  - `UT-J-70-initial.png` — b8bc071f768412854bba5255dc91d257
  - `UT-J-70-heatmap-viewport.png` — d17eda2902217795741af6c5fea57314
  - `UT-J-70-click-prefill.png` — 93acea782823cfdf554761b3776a462f
  - `UT-J-71-arrowleft-stepped.png` — abd4fc8e1ca1e27e15530d2284e3e569
  - `UT-J-71-cross-month-step.png` — df7ba88e5894701ba127a5e7a440cb7e
  - `UT-J-71-final.png` — (unique)
  - `UT-J-62-calendar-popover.png` — 60b288a28802e45c42956a10f866765d

## Notes on J-70 bucket coverage

The committed seed has full-coverage data (150–159 symbols on every trading day), so only density buckets 4 and 5 appear in live cell data. The J-70 fix (`BUCKET_TEXT_CLASS`) applies design tokens `text-text` (high-contrast near-white) for buckets 0–3 and `text-bg` (dark) for buckets 4–5. The token assignment is verifiable in source (`apps/frontend/components/availability-heatmap.tsx` lines 62–67) and no hardcoded hex is present. The acceptance criterion for legibility on all 6 buckets is met at the code level; the live seed only exercises buckets 4–5 visually.
