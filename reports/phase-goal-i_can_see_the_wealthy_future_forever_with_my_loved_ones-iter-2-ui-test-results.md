# Goal Mode Iteration 2 — UI Test Results

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-2
**Date:** 2026-06-11
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

**Overall:** 9/9 tests passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| J-43 | Deep-linkable ?asof survives reload/new-tab/click-through | happy-path | P1 | `?asof=D` in URL after hydration; survives reload, fresh tab, click-through; invalid degrades to latest; switching to latest removes param | All legs pass: URL carries `?asof=2026-06-05` after interactive select; click-through to `/stocks/NVDA?asof=2026-06-05` keeps param; reload keeps param (post-hydration href confirmed); fresh tab opens with `?asof=2026-06-05` and "Viewing as-of 2026-06-05 (historical)" indicator; invalid `?asof=2026-13-40` → `/stocks` (param stripped, latest view); switching to latest → `/stocks` (param absent) | PASS | J-43-fresh-tab-result.png, J-43-stocks-asof-set.png |
| J-44 | Dashboard major-indexes & regime card | happy-path | P1 | Card present by default (ON); SPY/QQQ/IWM/RSP lines with legend; DIA honestly absent; regime bands; range presets; toggle persists; historical as-of bounds series | Card visible on `/` at latest; 4 config-listed series (SPY, QQQ, IWM, RSP), DIA absent; regime legend shows Risk-on/Neutral/Risk-off; range select has 3M/6M/1Y/all options (server-side: 3M start=2026-03-10, 1Y start=2025-06-09 — re-normalization confirmed); toggle off → card hides, survives reload as hidden; toggle back on → card returns; historical `?asof=2026-03-10` → indexes API last bar 2026-03-10, regime-history last point 2026-03-10 (no data past D) | PASS | J-44-dashboard-card-visible.png, J-44-range-presets.png, J-44-toggle-hidden.png, J-44-historical-asof-bound.png |
| J-45 | Regime bands behind stock-detail price chart | happy-path | P1 | Same stored regime bands as dashboard; 3-family colors; Regime toggle default ON, persists; no bands past as-of D; J-20 forward region unchanged | `/stocks/NVDA` shows "Regime on" button and Risk-on/Neutral/Risk-off legend (identical 3-family mapping as dashboard card); clicking toggle → "Regime off"; reload → still "Regime off" (persists client-side); `?asof=2026-03-10` → "Forward — after as-of 2026-03-10 (display only)" label present (J-20 unchanged); API confirms regime-history last point = 2026-03-10 for that as-of; same date 2026-03-10 yields `Defensive 42.99` in both regime-history endpoint calls → color coherence confirmed | PASS | J-45-detail-regime-on.png, J-45-regime-off-persisted.png, J-45-historical-asof-forward-region.png |
| J-01 | Daily dashboard at a glance | smoke | P1 | Regime label + score; candidate counts; top sectors ≥3; top themes ≥3; breadth; timestamp; Major indexes card present | "Narrow leadership" regime with score, Actionable/Breakout-watch counts, ≥5 top sectors (SOXX/WGMI/SMH/HACK/CIBR), ≥3 top themes (Cybersecurity/Semiconductors/Ai Data Centre), breadth % and 50-DMA visible, timestamp 2026-06-10, "Major indexes & regime" card present | PASS | J-01-dashboard.png |
| J-06 | Score consistency across pages (coherence) | regression | P1 | NVDA scores identical on leaderboard and detail page | Leaderboard: Leadership E 43.14, Entry Quality E 54.05, Risk E 35.80. Detail page: Leadership E 43.14, Entry Quality E 54.05, Risk E 35.80. Exact match. | PASS | J-06-score-coherence.png |
| J-13 | Browse dashboard as of a past date (global as-of switcher) | happy-path | P1 | Selecting a past date re-points all pages; historical indicator visible; returning to latest restores current view | Selected 2026-05-01 via native setter; "Viewing as-of 2026-05-01 (historical)" present on `/` and `/stocks?asof=2026-05-01`; "as of 2026-05-01" label on stocks leaderboard | PASS | J-13-historical-asof.png |
| J-18 | One date control (no duplicate) | regression | P1 | /backtest has no page-local date picker; single global switcher drives it; URL carries `?asof` when historical | `/backtest` has exactly 1 `<select>` (global as-of — options start 2026-06-09...); no second date select; `/backtest?asof=2026-05-01` loads with "Viewing as-of 2026-05-01 (historical)" indicator; post-hydration `window.location.href` retains `?asof=2026-05-01` | PASS | J-18-one-date-control.png |
| J-20 | Price & MA chart shows full path through latest with as-of marker | regression | P1 | Historical as-of D: chart renders through 2026-06-10; forward region labelled; scores unchanged from as-of snapshot | `/stocks/NVDA?asof=2026-03-10`: "1365 bars · as of 2026-03-10"; "Full path through 2026-06-10"; "Forward — after as-of 2026-03-10 (display only)" present; scores read from 2026-03-10 snapshot (Leadership E 55.21); regime bands stop at D (no bands past 2026-03-10 confirmed via API) | PASS | J-20-full-path-asof-marker.png |
| J-42 | Every user-facing date reads yyyy-MM-dd (locale-proof) | regression | P1 | All dates in yyyy-MM-dd; no locale-format (M/D/YYYY etc.); date inputs use yyyy-MM-dd placeholder | `/data` date inputs placeholder = "yyyy-MM-dd"; no locale-format dates found (regex match = null); ISO dates present on scanner-runs list (2026-06-10, 2026-06-09…); as-of switcher options in yyyy-MM-dd format | PASS | J-42-iso-dates.png |

---

## Passed Tests

### J-43 — Deep-linkable ?asof survives reload/new-tab/click-through
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-2-evidence/J-43-fresh-tab-result.png`

Key verification steps:
- On `/stocks`, native-setter changed as-of select to `2026-06-05` → URL became `http://localhost:3835/stocks?asof=2026-06-05`
- Clicked NVDA row → navigated to `/stocks/NVDA?asof=2026-06-05` (click-through preserved)
- Navigated directly to `http://localhost:3835/stocks/NVDA?asof=2026-06-05` (reload simulation) → post-hydration `window.location.href` = `http://localhost:3835/stocks/NVDA?asof=2026-06-05` (param survived hydration)
- Fresh tab opened with same URL → `window.location.href` = `http://localhost:3835/stocks/NVDA?asof=2026-06-05`; "Viewing as-of 2026-06-05 (historical)" indicator visible; scores are from the 2026-06-05 snapshot
- Invalid `?asof=2026-13-40` → post-hydration URL = `http://localhost:3835/stocks` (degraded to latest, no crash)
- Switching to latest via native setter → URL = `http://localhost:3835/stocks` (param absent)

---

### J-44 — Dashboard major-indexes & regime card
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-2-evidence/J-44-dashboard-card-visible.png`

Key verification steps:
- "Major indexes & regime" card visible on `/` by default (default ON)
- 4 index series in legend: "S&P 500 (SPY)", "Nasdaq 100 (QQQ)", "Russell 2000 (IWM)", "S&P 500 Equal-Weight (RSP)" — DIA absent (honest omission, no fabricated line)
- Regime legend shows 3 risk-family colors: "Risk-on regime / Neutral regime / Risk-off regime"
- Range select options: 3M, 6M, 1Y, all — config-driven; re-normalization verified: 3M start=2026-03-10 vs 1Y start=2025-06-09 (different range starts, different first-point rebasing confirmed via `GET /api/indexes`)
- Toggle clicked → card hidden ("Show Major indexes & regime" button appears); reload → still hidden; toggle back → card returns
- Historical `/?asof=2026-03-10`: indexes API `last bar = 2026-03-10`; regime-history `last point = 2026-03-10, label=Defensive, score=42.99` — no data past D

---

### J-45 — Regime bands behind stock-detail price chart
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-2-evidence/J-45-detail-regime-on.png`

Key verification steps:
- `/stocks/NVDA` (latest): "Regime on" button present (default ON); legend shows "Risk-on regime / Neutral regime / Risk-off regime" — identical 3-family mapping as dashboard card
- Clicked Regime toggle → button changed to "Regime off" (bands hidden); reload → button still "Regime off" (persists client-side)
- `/stocks/NVDA?asof=2026-03-10`: "Viewing as-of 2026-03-10 (historical)" indicator; "Forward — after as-of 2026-03-10 (display only)" label present (J-20 forward region treatment unchanged); "Regime on" button visible
- Color coherence: `GET /api/regime-history?as_of=2026-03-10` and `GET /api/regime-history?as_of=2026-06-10` both read from the same stored `scanner_runs` rows — date 2026-03-10 returns `Defensive 42.99` in both, confirming identical label/color for the same date across surfaces
- Hover tooltip automation not applicable (lightweight-charts canvas); accepted on code inspection per J-42 precedent noted in iter spec

---

### J-01 — Daily dashboard at a glance
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-2-evidence/J-01-dashboard.png`

- Regime label "Narrow leadership" with score 61.00/100 (one of six defined labels)
- Candidate counts: Actionable 1, Breakout-watch 15, Pullback-watch 0
- Top Sectors ≥3: SOXX/WGMI/SMH/HACK/CIBR each with scores
- Top Themes ≥3: Cybersecurity/Semiconductors/Ai Data Centre with scores
- Breadth % above 50-DMA and 200-DMA visible; timestamp 2026-06-10 present
- "Major indexes & regime" card present with new J-44 content

---

### J-06 — Score consistency across pages (coherence)
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-2-evidence/J-06-score-coherence.png`

- `/stocks` leaderboard NVDA row: Leadership E 43.14, Entry Quality E 54.05, Risk E 35.80
- `/stocks/NVDA` detail page: Leadership E 43.14, Entry Quality E 54.05, Risk E 35.80
- Exact match on bucket letter and numeric value — single source of truth confirmed

---

### J-13 — Browse dashboard as of a past date (global as-of switcher)
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-2-evidence/J-13-historical-asof.png`

- Selected 2026-05-01 via native setter on `/`; "Viewing as-of 2026-05-01 (historical)" appeared
- Navigated to `/stocks?asof=2026-05-01`; "Viewing as-of 2026-05-01 (historical)" and "as of 2026-05-01" both present — stored snapshot re-pointed
- Switching back to latest removes indicator (tested in J-43 flow)

---

### J-18 — One date control (no duplicate)
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-2-evidence/J-18-one-date-control.png`

- `/backtest` has exactly 1 `<select>` element (the global as-of switcher, options starting 2026-06-09)
- No second page-local date picker present
- `/backtest?asof=2026-05-01` loads showing "Viewing as-of 2026-05-01 (historical)"; post-hydration `window.location.href` = `http://localhost:3835/backtest?asof=2026-05-01` (URL serialization as per J-43 amendment)

---

### J-20 — Price & MA chart shows full path through latest with as-of marker
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-2-evidence/J-20-full-path-asof-marker.png`

- `/stocks/NVDA?asof=2026-03-10`: "1365 bars · as of 2026-03-10" confirms full bar set rendered
- "Full path through 2026-06-10" text present — chart extends to latest seed date
- "Forward — after as-of 2026-03-10 (display only)" label present — post-D region marked
- Scores read from 2026-03-10 snapshot (Leadership E 55.21 — different from latest E 43.14)
- J-20 behavior unchanged: regime bands stop at 2026-03-10, forward region remains display-only

---

### J-42 — Every user-facing date reads yyyy-MM-dd (locale-proof)
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-2-evidence/J-42-iso-dates.png`

- `/data` form inputs: placeholder = "yyyy-MM-dd" (4 date inputs confirmed)
- No locale-format dates found on any page (regex `\d{1,2}/\d{1,2}/\d{4}` returned null)
- Scanner runs page: all run dates in yyyy-MM-dd (2026-06-10, 2026-06-09, …)
- Global as-of switcher options in yyyy-MM-dd format

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
- **Browser:** Chrome via MCP
- **Test Date:** 2026-06-11
- **Evidence directory:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-2-evidence/`

### Additional observations

- **Hover tooltip:** The lightweight-charts canvas tooltip (regime label + score on hover) was not automated (canvas hover automation not applicable per iter spec Notes). Accepted on code inspection: the chart reads the same `GET /api/regime-history` endpoint that returns the stored `label` + `score` fields. The date format path via `lib/dates.ts` confirmed by ISO dates appearing on all other surfaces.
- **Range preset UI:** Range presets rendered as `<select><option>` elements (not buttons). Native setter technique used. Options confirmed: 3M, 6M, 1Y, all. Re-normalization to range start confirmed via API (3M start 2026-03-10 ≠ 1Y start 2025-06-09).
- **DIA:** Absent from legend as expected — no stored bars, honest omission, card renders fully without it.
- **Anti-goal compliance:** No regime recomputation observed; both `/api/regime-history` and `/api/indexes` serve stored values; no client-side return math; no second date state; bands stop exactly at resolved as-of.
