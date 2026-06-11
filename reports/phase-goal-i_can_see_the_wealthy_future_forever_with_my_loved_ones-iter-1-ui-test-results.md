# Goal Mode Iter-1 — UI Test Results

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-1
**Date:** 2026-06-11
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** FAIL

**Overall:** 6/7 tests passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-42 | ISO dates everywhere (locale-proof) | happy-path | P1 | All displayed dates yyyy-MM-dd; /data inputs are validated text; invalid input blocked | Date inputs are type=text placeholder=yyyy-MM-dd; invalid 2026-13-40 shows border-neg error + disabled submit; all page dates in yyyy-MM-dd | PASS | UT-J-42-invalid-2026-13-40.png |
| UT-J-43 | Deep-linkable as-of (URL serialization) | happy-path | P1 | ?asof=D in URL when historical; reload/tab/click-through preserves; latest is param-free; invalid degrades to latest | Interactive selection correctly writes ?asof=D; click-through preserves date in switcher but URL drops ?asof after hydration; reload strips ?asof (not preserved); invalid ?asof degrades correctly | FAIL | UT-J-43-url-missing-asof.png |
| UT-J-06 | Score consistency across pages | regression | P1 | MRVL scores identical on leaderboard and detail at same historical date | MRVL at 2026-06-09: Leadership A 94.42, Entry Quality E 20.54, Risk E 58.42 — identical on leaderboard and detail | PASS | UT-J-43-detail-clickthrough.png |
| UT-J-13 | Browse dashboard as of a past date | regression | P1 | Switcher re-points all pages; historical indicator visible; returns to latest correctly | Switcher fires correctly via React fiber; /, /stocks, /themes, /sectors all re-point; historical indicator and Data as-of label correct; URL carries ?asof=D when selected interactively | PASS | UT-J-13-dashboard-historical.png |
| UT-J-17 | Grow the dataset (form submit with typed dates) | regression | P1 | Valid ISO text inputs allow form submission; job runs asynchronously | Valid dates 2021-02-10/2021-02-17 — Start button enabled; backfill job ran and completed showing "backfill job · 2021-02-10 → 2021-02-17" | PASS | UT-J-17-job-complete.png |
| UT-J-18 | One date control (no page-local date state) | regression | P1 | Backtest has no page-local date picker; single global switcher drives it | /backtest has no page-local date select (5 buttons, 1 input = global select only); global switcher drives Backtest; URL shows /backtest?asof=2026-06-09 when historical | PASS | UT-J-18-backtest-no-local-date.png |
| UT-J-20 | Price and MA chart full path with as-of marker | regression | P1 | Chart extends to latest seed date; D marked with divider; post-D region labelled display-only | NVDA chart: "Full path through 2026-06-10. Bars after the as-of date 2026-06-09 are display-only"; chart legend shows "Forward — after as-of 2026-06-09 (display only)" | PASS | UT-J-20-nvda-chart-full.png |

---

## Passed Tests

### UT-J-42 — ISO dates everywhere (locale-proof)
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-1-evidence/UT-J-42-invalid-2026-13-40.png`
- `/data` date inputs confirmed as `type="text"` with `placeholder="yyyy-MM-dd"` (data-testid="job-start-date" and "job-end-date") — not native `type="date"` locale-dependent widgets
- Input `2026-13-40`: class changes to `border-neg focus-visible:ring-neg` (red border), "Enter a valid date as yyyy-MM-dd" error text appears in parent container, Start button `disabled=true`
- Input `10/06/2026` (appended): same `border-neg` styling and button disabled — format rejected
- Coverage figures show `2021-01-04 → 2026-06-10` (yyyy-MM-dd)
- Job progress shows `backfill job · 2021-02-10 → 2021-02-17` (yyyy-MM-dd)
- Scanner Runs "AS OF" column: all dates `2026-06-10`, `2026-06-09`, `2026-06-08`, etc. (yyyy-MM-dd)
- As-of switcher options: `2026-06-09`, `2026-06-08`, etc. (yyyy-MM-dd); "Latest · 2026-06-10" label
- Historical indicator shows "Viewing as-of 2026-06-09 (historical)" (yyyy-MM-dd)

---

### UT-J-06 — Score consistency across pages (coherence)
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-1-evidence/UT-J-43-detail-clickthrough.png`
- At historical date 2026-06-09: Leaderboard row MRVL — Leadership A 94.42, Entry Quality E 20.54, Risk E 58.42 (verified via DOM text extraction)
- Detail page `/stocks/MRVL?asof=2026-06-09` shows Leadership A 94.42, Entry Quality E 20.54, Risk E 58.42 — identical
- No recomputation; single source of truth confirmed

---

### UT-J-13 — Browse dashboard as of a past date (global as-of switcher)
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-1-evidence/UT-J-13-dashboard-historical.png`
- Opened `/` at latest: Market Regime "Narrow leadership" 61.00 / 100
- Selected historical date 2026-06-09 via React fiber onChange trigger: URL → `/?asof=2026-06-09`; "Viewing as-of 2026-06-09 (historical)" indicator visible; "Data as-of 2026-06-09" shown; Market Regime changed to "Risk-on" 68.95 (different from latest — confirms different snapshot)
- Navigated to `/stocks`: switcher retained 2026-06-09, historical indicator still visible, stocks reflect 2026-06-09 snapshot
- Switched back to latest: switcher empty (latest), historical indicator gone, URL `/stocks` (no param)

---

### UT-J-17 — Grow the dataset (form submit leg only — no live provider fetch)
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-1-evidence/UT-J-17-job-complete.png`
- `/data` form has valid dates "2021-02-10" and "2021-02-17" (yyyy-MM-dd text inputs)
- Job kind "backfill" selected; Start button `disabled=false` (valid dates)
- Clicked Start; job appeared with live progress showing "running"
- Job completed; Job progress section shows "backfill job · 2021-02-10 → 2021-02-17" with status "ok"
- Dates in job card are yyyy-MM-dd (J-42 compliance confirmed here too)

---

### UT-J-18 — One date control (no page-local date state)
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-1-evidence/UT-J-18-backtest-no-local-date.png`
- `/backtest` page: DOM shows 5 buttons + 1 input (the global select) — no page-local date dropdown present
- "Viewing as-of 2026-06-10 (latest)" indicator shown; Backtest as-of scan summary matches global date
- Changed global switcher to 2026-06-09: URL → `/backtest?asof=2026-06-09`; Backtest re-pointed (Market Regime, candidate counts changed)
- J-18 amendment noted: URL carrying `?asof=D` is the serialization of the single global state, not a page-local state — confirmed

---

### UT-J-20 — Price and MA chart shows full path with as-of marker
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-1-evidence/UT-J-20-nvda-chart-full.png`
- Set global as-of to 2026-06-09; opened `/stocks/NVDA?asof=2026-06-09`
- Page text: "Full path through 2026-06-10. Bars after the as-of date 2026-06-09 are display-only — they don't affect the scores, setup, or VCP flag below (those read the as-of snapshot, bars ≤ 2026-06-09)"
- Chart legend includes "Forward — after as-of 2026-06-09 (display only)"
- Chart section header: "Price & moving averages — 1365 bars · as of 2026-06-09"
- Scores (Leadership A 47.93, Entry Quality E 59.09, Risk E 33.77) computed from bars ≤ 2026-06-09

---

## Failed Tests

### UT-J-43 — Deep-linkable as-of (URL serialization)
**Verdict:** FAIL
**Failure:** When loading a URL carrying `?asof=yyyy-MM-dd` (direct navigation, reload, or fresh tab), the date is correctly restored into the global control (switcher shows D, historical indicator visible, data correct) but the `?asof=D` param is immediately stripped from the URL after client-side hydration. The URL ends up as `/stocks` (or `/`) without `?asof=D` even though the view is historical. Deep links are therefore non-functional: copying the URL and opening a new tab or reloading shows the correct date in the switcher momentarily but the URL does not carry `?asof=D`, defeating shareability.

**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-1-evidence/UT-J-43-url-missing-asof.png`

**Steps taken:**
1. Navigated to `http://localhost:3835/stocks?asof=2026-06-09` — navigate action confirmed `Current URL: http://localhost:3835/stocks?asof=2026-06-09`
2. After hydration: `window.location.href` = `http://localhost:3835/stocks`; `?asof` param gone; but switcher value = `2026-06-09` and historical indicator visible
3. Confirmed same behaviour for `/?asof=2026-06-09` and `/stocks/MRVL?asof=2026-06-09` — all lose `?asof` after hydration
4. Confirmed interactive selection (via React fiber onChange) DOES write `?asof=D` correctly: `http://localhost:3835/stocks?asof=2026-06-09` persists while historical, disappears at latest
5. Confirmed invalid `?asof=not-a-date` → URL `/stocks` (no crash, no fabricated date) — degradation works
6. Confirmed invalid `?asof=2026-01-01` (no run) → URL `/stocks`, switcher empty (latest) — degradation works
7. Confirmed switching back to latest from historical removes `?asof` → URL `/stocks` — this part works

**Expected:** Loading `http://localhost:3835/stocks?asof=2026-06-09` should restore date into global control AND the URL should continue to carry `?asof=2026-06-09` (the `writeAsofParam → router.replace` effect should re-serialize after restore); reload and fresh tab must preserve the param

**Actual:** Date restored into global control correctly (switcher = 2026-06-09, indicator = "(historical)", data correct for that date) but URL is stripped to `/stocks` — the re-serialization effect in `AsofParamSync` runs after restore but the `router.replace` does not re-write `?asof` back, causing the URL to be permanently param-free despite the historical state

**Partially passing steps:**
- Step 1: Interactive selection writes `?asof=D` to URL — PASS
- Step 2 (click-through): URL carries `?asof=D` immediately after click (JS navigation) — PASS for the instant the navigate fires, but after hydration the destination page loses the param — partial FAIL
- Step 3 (reload) — FAIL: `?asof` not in URL after reload
- Step 4 (fresh tab) — FAIL: `?asof` stripped after hydration
- Step 5 (switch to latest removes param) — PASS
- Invalid `?asof` degradation — PASS

---

## Skipped Tests

(none)

---

## Environment

- **Frontend URL:** http://localhost:3835
- **Browser:** Chrome via MCP (plugin_superpowers-chrome)
- **Test Date:** 2026-06-11
- **Evidence directory:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-1-evidence/`

---

## Notes

### J-42 additional detail
The four `/data` date inputs are confirmed `type="text"` with `placeholder="yyyy-MM-dd"` and `data-testid` attributes (`job-start-date`, `job-end-date`, `remove-start-date`, `remove-end-date`). No native `type="date"` widgets exist. Validation fires on `input`/`change` events and applies `border-neg` class to the input plus renders an inline error message "Enter a valid date as yyyy-MM-dd" in the parent container. The Start button becomes `disabled=true` while any date input is in error state. Chart tooltip/crosshair date format was not directly verified via automation (chart tooltip requires hover on canvas element which is not directly automatable), but the chart section header and page text all use yyyy-MM-dd. Given the shared formatter confirmed in code (`apps/frontend/lib/dates.ts`) and all other date surfaces confirmed ISO, this is treated as passing.

### J-43 root cause observation (for developer, not QA speculation)
The `AsofParamSync` component in `asof-provider.tsx` has two effects: (1) restore `?asof` from URL into state, and (2) serialize state back to URL. On load with `?asof=D`, effect (1) calls `setAsOf(D)`, then effect (2) should call `writeAsofParam(router, pathname, searchParams, D)`. The observed behaviour suggests effect (2) is running with `asOf=null` (latest) before effect (1) completes the state update, or the `router.replace` is being overridden. The URL is correctly written during interactive selection because effect (1) is not competing. This is a React effect ordering / hydration timing issue in the serializer.
