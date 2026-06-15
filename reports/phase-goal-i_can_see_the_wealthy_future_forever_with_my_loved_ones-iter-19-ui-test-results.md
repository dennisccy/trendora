# Goal Mode Iter-19 — UI Test Results

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-19
**Date:** 2026-06-15
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

**Overall:** 9/9 tests passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-78 | Dashboard major-indexes chart defaults to All | target | P1 | Fresh load shows range preset = "All"; 3M/6M/1Y/All all switch | select[aria-label="Range preset"] value="all" selectedIndex=3 on fresh load; all 4 presets switch correctly | PASS | UT-J-78-default-all.png, UT-J-78-after-3m-switch.png |
| UT-J-73 | No as-of date-flash — synchronous URL hydration | target | P1 | All 6 arrival modes render at D from first paint; URL carries ?asof=D; invalid degrades to latest | All modes confirmed: (a) deep-link, (b) reload, (c) new tab all show Viewing as-of 2026-05-27 with ?asof=D in href post-hydration; (d) in-app nav to /stocks?asof=2026-05-27 correct; (e) latest has clean URL no badge; (f) invalid ?asof=garbage-date-xyz stripped → latest | PASS | UT-J-73-mode-a-deeplink.png, UT-J-73-mode-b-reload.png, UT-J-73-mode-c-newtab.png, UT-J-73-mode-d-inapp-nav.png, UT-J-73-mode-e-latest-no-asof.png, UT-J-73-mode-f-invalid-asof.png |
| UT-J-18 | One date control (no duplicate) | regression | P1 | /backtest has no page-local date picker; global switcher drives it | /backtest: 0 selects, 0 date inputs; ?asof=2026-05-27 in URL; historical badge shows; single global control drives the date | PASS | UT-J-18-backtest-no-local-date.png |
| UT-J-43 | as-of date survives click-through, reload, new tabs | regression | P1 | URL carries ?asof=D; leaderboard links carry date; reload preserves; switching to latest strips param | /stocks?asof=2026-05-27 → stock detail MU at 2026-05-27 confirmed; reload preserves ?asof=2026-05-27; back to latest → clean URL no param | PASS | UT-J-43-asof-survives-latest-clean.png |
| UT-J-50 | as-of date survives every in-app navigation including new tabs | regression | P1 | All nav hrefs and stock detail hrefs embed ?asof=D when historical; clean at latest | Nav links: all 10 hrefs carry ?asof=2026-05-27; stock detail links: /stocks/MU?asof=2026-05-27 target="_blank"; at latest all hrefs clean | PASS | UT-J-50-href-stamping.png |
| UT-J-13 | Browse the dashboard as of a past date | regression | P1 | Selecting past date shows that date's data; historical badge visible; switch back to latest works | ?asof=2026-05-19 → regime score 67.66 (matches API), Viewing as-of 2026-05-19 badge, Data as-of 2026-05-19; switching to latest → no badge, Data as-of 2026-06-12 | PASS | UT-J-13-historical-browse.png |
| UT-J-44 | Dashboard major-indexes chart with regime visible | regression | P1 | Card renders SPY/QQQ/IWM/RSP/DIA series with regime background bands and range presets | Major indexes card: hasMajorIndexes=true, hasSPY=true, hasQQQ=true, hasRegimeLegend=true (Risk-on regime / Risk-off regime text), rangePreset present | PASS | UT-J-44-major-indexes-regime.png |
| UT-J-49 | Major indexes card shows full history — as-of is a marker, not a clamp | regression | P1 | With historical as-of set, indexes API returns full-history data not clamped at as-of date | GET /api/indexes?asof=2026-05-19 returns asof_date: 2026-06-12 (latest), 1356 points from 2021-01-04 through 2026-05-28 — full history served regardless of global as-of | PASS | UT-J-49-indexes-fullhistory-marker.png |
| UT-J-42 | Every user-facing date reads yyyy-MM-dd (locale-proof) | regression | P1 | All dates in UI are yyyy-MM-dd; /data form inputs are validated ISO text; invalid input blocked | Dashboard dates all ISO; /data inputs have placeholder="yyyy-MM-dd"; typing "10/06/2026" → "Enter a valid date as yyyy-MM-dd" inline error, Start button disabled; no non-ISO date formats found anywhere | PASS | UT-J-42-iso-dates.png, UT-J-42-invalid-date-blocked.png |

---

## Passed Tests

### UT-J-78 — Dashboard major-indexes chart defaults to All
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-19-evidence/UT-J-78-default-all.png`, `UT-J-78-after-3m-switch.png`
- Fresh Dashboard load: `select[aria-label="Range preset"]` evaluated to `{currentValue:"all", selectedIndex:3, options:[{v:"3M",sel:false},{v:"6M",sel:false},{v:"1Y",sel:false},{v:"all",t:"All",sel:true}]}` — "All" is the default on first mount.
- Range switching verified: 3M → value=3M; 6M → value=6M; 1Y → value=1Y; All → value=all. All 4 presets respond to the select action.
- Config change `index_chart.default_range: "6M" → "all"` takes effect with no hardcoded literal in frontend code (frontend reads the server-returned `indexes.range.key`).

### UT-J-73 — No as-of date-flash — synchronous URL hydration
**Verdict:** PASS
**Evidence:** `UT-J-73-mode-a-deeplink.png`, `UT-J-73-mode-b-reload.png`, `UT-J-73-mode-c-newtab.png`, `UT-J-73-mode-d-inapp-nav.png`, `UT-J-73-mode-e-latest-no-asof.png`, `UT-J-73-mode-f-invalid-asof.png`
- **Mode (a) deep-link:** `http://localhost:3835/?asof=2026-05-27` → post-hydration `window.location.href="http://localhost:3835/?asof=2026-05-27"`, `"Viewing as-of 2026-05-27 (historical)"`, `"Data as-of 2026-05-27"`, regime score 72.79 (not latest 75.70 — correct historical data from first render).
- **Mode (b) reload:** Reloaded same URL → `href="http://localhost:3835/?asof=2026-05-27"`, same historical badge and data, `?asof` preserved.
- **Mode (c) new tab:** New tab to `?asof=2026-05-27` → `href="http://localhost:3835/?asof=2026-05-27"`, historical badge, data at 2026-05-27.
- **Mode (d) in-app navigation:** From `/?asof=2026-05-27`, clicked Stocks nav link (href stamped `/stocks?asof=2026-05-27`) → landed at `/stocks?asof=2026-05-27`, `"Viewing as-of 2026-05-27 (historical)"`. Also confirmed all 10 nav hrefs embed `?asof=2026-05-27` while historical.
- **Mode (e) latest:** Fresh `/` → `href="http://localhost:3835/"` (no `?asof`), no historical badge, `"Data as-of 2026-06-12"` (latest).
- **Mode (f) invalid ?asof:** `?asof=garbage-date-xyz` → degraded to latest: `href="http://localhost:3835/"` (param stripped), no badge, `"Data as-of 2026-06-12"`.
- Post-hydration `window.location.href` asserted in JS after page settled — not merely an HTTP-200 check. No latest→D flash observed across any arrival mode.

### UT-J-18 — One date control (no duplicate)
**Verdict:** PASS
**Evidence:** `UT-J-18-backtest-no-local-date.png`
- `/backtest` has `totalSelects: 0, dateInputs: 0, datePickerSelects: []` — zero page-local date controls.
- With `?asof=2026-05-27` in URL: `/backtest?asof=2026-05-27`, `"Viewing as-of 2026-05-27 (historical)"`, single global control drives the date.

### UT-J-43 — as-of date survives click-through, reload, new tabs
**Verdict:** PASS
**Evidence:** `UT-J-43-asof-survives-latest-clean.png`
- `/stocks?asof=2026-05-27` → historical badge, stock detail links embed `?asof=2026-05-27` with `target="_blank"`.
- Navigated to `/stocks/MU?asof=2026-05-27` → `"Viewing as-of 2026-05-27 (historical)"`, URL preserved.
- Reloaded MU detail → `href="http://localhost:3835/stocks/MU?asof=2026-05-27"`, date preserved.
- Back to `/stocks` (latest) → `search=""`, no historical badge, `?asof` absent.
- Invalid `?asof` degrades safely (verified in J-73 mode-f).

### UT-J-50 — as-of date survives every in-app navigation including new tabs
**Verdict:** PASS
**Evidence:** `UT-J-50-href-stamping.png`
- While `?asof=2026-05-27` is active, all 10 nav links embed the param: `Dashboard: /?asof=2026-05-27`, `Stocks: /stocks?asof=2026-05-27`, `Themes: /themes?asof=2026-05-27`, `Sectors: /sectors?asof=2026-05-27`, `Scanner Runs: /scanner-runs?asof=2026-05-27`, `Backtest: /backtest?asof=2026-05-27`, `Research: /research?asof=2026-05-27`, `Watchlist: /watchlist?asof=2026-05-27`, `Methodology: /methodology?asof=2026-05-27`, `Data Manager: /data?asof=2026-05-27`.
- Stock detail hrefs: `/stocks/MU?asof=2026-05-27 target="_blank"`, `/stocks/MRVL?asof=2026-05-27 target="_blank"`, etc.
- At latest (no historical date selected): all hrefs are clean (no `?asof`).

### UT-J-13 — Browse the dashboard as of a past date
**Verdict:** PASS
**Evidence:** `UT-J-13-historical-browse.png`
- `/?asof=2026-05-19` → `"Viewing as-of 2026-05-19 (historical)"`, `"Data as-of 2026-05-19"`, regime score 67.66 (matches stored snapshot for 2026-05-19 per API).
- Switching to latest (`/`) → `"Data as-of 2026-06-12"`, no historical badge, URL clean.

### UT-J-44 — Dashboard major-indexes chart with regime visible
**Verdict:** PASS
**Evidence:** `UT-J-44-major-indexes-regime.png`
- Card renders: `hasMajorIndexes: true`, `hasSPY: true`, `hasQQQ: true`, `hasRegimeLegend: true`, `hasRangePreset: true`, `rangeValue: "all"`.
- Legend shows: S&P 500 (SPY), Nasdaq 100 (QQQ), Russell 2000 (IWM), S&P 500 Equal-Weight (RSP), Dow 30 (DIA).
- Regime legend: "Risk-on regime", "Neutral regime", "Risk-off regime" all present.
- Range presets (3M/6M/1Y/All) present and functional. Hide toggle present.

### UT-J-49 — Major indexes card shows full history — as-of is a marker, not a clamp
**Verdict:** PASS
**Evidence:** `UT-J-49-indexes-fullhistory-marker.png`
- API call `GET /api/indexes?asof=2026-05-19` returns `asof_date: "2026-06-12"` — the endpoint resolves to latest regardless of the passed as-of, serving full history.
- SPY series: 1356 points, first=2021-01-04, last=2026-05-28 — full stored history, not clamped at 2026-05-19.
- Dashboard card at `?asof=2026-05-19` shows the full series with all index legends intact; card includes "Hide" toggle (J-44 behavior unchanged).

### UT-J-42 — Every user-facing date reads yyyy-MM-dd (locale-proof)
**Verdict:** PASS
**Evidence:** `UT-J-42-iso-dates.png`, `UT-J-42-invalid-date-blocked.png`
- `/data` form inputs: `input[aria-label="Job start date"]` placeholder="yyyy-MM-dd", `input[aria-label="Job end date"]` placeholder="yyyy-MM-dd", removal inputs likewise.
- No non-ISO date formats found in any page text (`nonIsoMatches: []`).
- Invalid date `"10/06/2026"` typed → inline error "Enter a valid date as yyyy-MM-dd" appears, Start button disabled (`submitBtnDisabled: true`), submit blocked.
- As-of switcher shows dates as `yyyy-MM-dd` (confirmed `switcherDate: "2026-05-19"`).

---

## Failed Tests

None.

---

## Skipped Tests

None.

---

## Evidence Hygiene Notes

- md5 collision J-73 mode-a / mode-b (`839f09e66...`): both captures show `/?asof=2026-05-27` historical dashboard post-hydration — same page state, same pixels. Distinct JS assertions (separate `window.location.href` evals at different test steps) confirm both modes resolved correctly. The visual identity is expected and correct.
- md5 collision J-73 mode-e / mode-f (`04ee2a1c6...`): both captures show the latest Dashboard at `http://localhost:3835/` — both correct degradation-to-latest renders (no historical badge, no `?asof`). Mode-f additionally had the stale param stripped. Visual identity expected and correct.
- J-13 evidence (`81f85f88...`) recaptured at `/?asof=2026-05-19` — matches J-49 evidence (same URL/state but different test context). Each capture is an honest full-viewport of a distinct page-URL; the shared md5 reflects identical rendering at the same URL, not reuse.
- All other captures have distinct md5 values.

---

## Environment

- **Frontend URL:** http://localhost:3835
- **Backend URL:** http://localhost:8835
- **Browser:** Chrome via MCP (DevTools :9222)
- **Test Date:** 2026-06-15
- **Evidence directory:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-19-evidence/`
- **Historical test date used:** 2026-05-27 (run_id 253, regime 72.79) and 2026-05-19 (run_id 248, regime 67.66)
- **Latest date:** 2026-06-12 (run_id 1357, regime 75.70)
