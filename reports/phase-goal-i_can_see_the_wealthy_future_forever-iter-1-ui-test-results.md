# goal-i_can_see_the_wealthy_future_forever-iter-1 — UI Test Results

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-1
**Date:** 2026-06-01
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

<!-- PASS: all target + required-still-passing journeys passed; no P1 failure -->

**Overall:** 7/7 tests passed (0 failed, 0 skipped)

Goal-mode lean iteration. Target journeys: **J-18, J-13**. Required-still-passing journeys re-run for
no-regression: **J-14, J-01, J-03, J-04, J-05**. Each journey is one test case (`UT-<journey-id>`),
executed against `goal.md`'s "Must-have user journeys" steps + Acceptance line.

The Chrome-MCP tool layer was **fully functional** this iteration — every `select` / `click` /
`navigate` / `eval` interaction succeeded and the browser console was clean (no errors/exceptions
across 31 captured states). So J-13's interaction-driven flow is recorded as a full **PASS**, not
PARTIAL.

---

## J-18 source-level verification gate (mandatory per iter spec NOTES / iter-0 lesson)

The spec requires J-18 be confirmed against **frontend source**, not on a "no dropdown" screenshot
alone (iter-0 QA wrongly reported "no separate date dropdown" while the source still had
`BacktestDatePicker`). Confirmed against `apps/frontend/app/backtest/page.tsx`:

- **(a) No page-local picker / no `<Select>` for dates** — `grep -nE "BacktestDatePicker|<Select"
  app/backtest/page.tsx` → **NO MATCHES**. Live DOM on `/backtest` has exactly **one** `<select>`,
  and its `aria-label` is `"View as-of date"` (the global top-bar switcher); the deleted
  `aria-label="Backtest as-of date"` element is **absent** (`document.querySelector` → null).
- **(b) Imports `useAsOf` and keys the data effect on `asOf`** — `page.tsx:6`
  `import { useAsOf } from "@/components/asof-provider"`; `page.tsx:54`
  `const { asOf, isHistorical: globalIsHistorical } = useAsOf();`; the data `useEffect` ends `}, [asOf]`.
- **(c) Holds no independent date state** — `grep -nE "\bselected\b|setDates|setLatest|setReady|fetchRuns"
  app/backtest/page.tsx` → **NO MATCHES**. The only `useState` is the loading/ok/error `state`
  machine; no `selected`/`dates`/`latest`/`ready` date state, no `fetchRuns` import.

**Gate result: PASS** (source + live DOM agree). Coherence invariant #5 (exactly one date selector;
no second independent date state) is satisfied in source.

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-18 | One date control (no duplicate) — **target** | target journey | P1 | `/backtest` has no date selector of its own; the single global top-bar switcher drives its scan + scorecard; as-of date matches the switcher and matches `/stocks` for the same date | `/backtest` had exactly 1 `<select>` ("View as-of date", global); no page-local picker. Switcher→2025-05-28 re-pointed Backtest badge+scorecard; `/stocks` showed the same 2025-05-28; back on `/backtest` date persisted; Latest restored | **PASS** | `UT-J-18-backtest-latest-no-picker.png`, `UT-J-18-backtest-historical-2025-05-28.png`, `UT-J-18-stocks-same-date-persists.png` |
| UT-J-13 | Browse dashboard as of a past date (global switcher) — **target** | target journey | P1 | Selecting a past date re-points `/`, `/stocks`, `/themes`, `/sectors` (and `/backtest`) to that date's stored snapshot; historical indicator visible; latest restores | Switcher→2025-05-28: `/` regime changed 74.32→**68.91**, top sectors SOXX/WGMI→**XAR/ITA/URA**; `/themes`, `/sectors`, `/stocks`, `/backtest` all showed "Viewing as-of 2025-05-28 (historical)"; Latest restored SOXX/WGMI/SMH | **PASS** | `UT-J-13-dashboard-historical-2025-05-28.png` |
| UT-J-14 | Backtest a past date + forward-test scorecard | regression | P1 | Numeric per-horizon returns + excess vs SPY/QQQ/sector + control-group cols + sample n; recent/latest date shows honest NA, not fabricated | 2025-05-28: 1d −0.97% / 5d +4.01% / 10d +5.65% / 20d +14.05% / 60d +18.09% (cohort n=20), excess vs SPY/QQQ/Sector, random-peers/SPY/QQQ/sector-ETF cols, all with n. Latest 2026-05-28: every horizon "—n=0 ⚠" + "No elapsed forward window… nothing fabricated" empty-state | **PASS** | `UT-J-14-backtest-latest-NA.png`, `UT-J-18-backtest-historical-2025-05-28.png` |
| UT-J-01 | Daily dashboard at a glance | regression | P1 | Regime label (one of six)+score; 3 candidate counts; ≥3 top sectors & ≥3 top themes w/ scores; breadth %; last-scan timestamp | Regime "Risk-on 74.32/100"; Actionable 0 / Breakout-watch 8 / Pullback-watch 1; 5 sectors (SOXX 93.67…), 5 themes (Semiconductors 100.00…); breadth 65.57% / 59.02% / NNH 9.02% (universe-relative); "Data as-of 2026-05-28" | **PASS** | `UT-J-01-dashboard-latest.png` |
| UT-J-03 | Theme Leaderboard | regression | P2 | ≥3 themes ranked non-increasing by Theme Score; top theme shows member tickers, 1m & 3m returns, breadth %, trend label | Ranked Nuclear Uranium 100.00 → Power Grid 74.50 → Crypto Eq 72.50 → AI DC 70.00 → Megacap 51.50; top theme members CEG/VST/NRG/CCJ/LEU/UEC, 1M +36.30%, 3M +23.15%, breadth 100%, "Strong uptrend" | **PASS** | `UT-J-03-themes-historical-expanded.png` |
| UT-J-04 | Sector / industry Leaderboard | regression | P2 | ETFs ranked by Sector Score; each row RS-vs-SPY, dist-52w-high, trend; SPY as 0% ref or excluded (not ranked as leader) | 31 rows ranked XAR 85.83 → … → ITB 7.33; top row XAR RS +18.90%, dist −0.03%, "Strong uptrend"; **SPY excluded** from the ranked list | **PASS** | `UT-J-04-sectors-historical.png` |
| UT-J-05 | Stock Detail with explainable scores | regression | P2 | Price+MA chart & volume; each of 3 scores shows A–E bucket + 0–100 + ≥3 named components; theme chips, setup, reason, invalidation | `/stocks/NVDA`: 7 canvases (price+MA, volume); Leadership E 47.48 (7 comps), Entry Quality D 66.24 (comps), Risk E 33.79 (comps); THEMES Ai Data Centre/Semiconductors/Megacap; setup "Avoid"; reason "…too weak… Top driver: MA stack"; "Invalid below the 50-DMA at $198.73" | **PASS** | `UT-J-05-stock-detail-nvda.png` |

---

## Passed Tests

### UT-J-18 — One date control (no duplicate) [TARGET]
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever-iter-1-evidence/UT-J-18-backtest-latest-no-picker.png`, `…/UT-J-18-backtest-historical-2025-05-28.png`, `…/UT-J-18-stocks-same-date-persists.png`

Steps executed exactly per `goal.md` J-18:
1. **Visit `/backtest`, confirm no page-local date dropdown** — live DOM had exactly **1** `<select>`,
   `aria-label="View as-of date"` (the global top-bar switcher, 11 options, "Latest · 2026-05-28").
   `document.querySelector('[aria-label="Backtest as-of date"]')` → **null** (deleted picker absent).
   Page badge (display-only) read "Viewing as-of 2026-05-28 (latest)".
2. **Change the global top-bar switcher → 2025-05-28** — both the page badge AND the top-bar indicator
   updated to "Viewing as-of 2025-05-28 (historical)" (one resolved date, in sync).
3. **Backtest scan + scorecard re-point** — the forward-test scorecard re-rendered 2025-05-28's data
   (cohort n=20; 1d −0.97% … 60d +18.09%), matching `GET /api/backtest?as_of=2025-05-28` exactly.
4. **Open `/stocks` for the same date & compare** — client-side nav to `/stocks` kept 2025-05-28
   (top-bar indicator + switcher value both `2025-05-28`); navigating back to `/backtest` still showed
   2025-05-28 with only the single global `<select>`. **One resolved date everywhere.**
5. **Return to Latest** — Backtest restored "Viewing as-of 2026-05-28 (latest)", 1 select only.

Governed by the **source-level gate above (PASS)** in addition to the browser flow — not a screenshot
alone, per the iter-0 lesson.

### UT-J-13 — Browse the dashboard as of a past date (global as-of switcher) [TARGET]
**Verdict:** PASS
**Evidence:** `…/UT-J-13-dashboard-historical-2025-05-28.png` (+ the per-page states captured for `/stocks`, `/themes`, `/sectors`, `/backtest`)

1–4. On `/`, selected 2025-05-28 in the global switcher: the dashboard re-pointed to that date's stored
snapshot — regime **68.91/100** (vs latest **74.32**), top sectors **XAR/ITA/URA/CIBR** (vs latest
SOXX/WGMI/SMH), "Data as-of 2025-05-28", and the clear "Viewing as-of 2025-05-28 (historical)"
indicator. Client-side navigation then showed the **same** date re-pointed on `/themes` (Nuclear
Uranium-led), `/sectors` (XAR-led, 31 rows), `/stocks` (HOOD/ZS/NRG-led), and `/backtest`.
5. Returning the switcher to Latest restored the current view (`/sectors` reverted to SOXX/WGMI/SMH,
"Data as-of 2026-05-28", indicator "Latest").

This is J-13's acceptance extended to Backtest (the J-18 flow). No code change beyond the J-18 edit was
needed; in iter-0 J-13 was only "partial" due to a degraded browser tool — this run drove the
interaction cleanly, so it is a full PASS.

### UT-J-14 — Backtest a past date and read its forward-test scorecard
**Verdict:** PASS
**Evidence:** `…/UT-J-18-backtest-historical-2025-05-28.png` (full numeric scorecard), `…/UT-J-14-backtest-latest-NA.png` (honest NA)

For **2025-05-28** (≥60 elapsed bars) the scorecard rendered numeric per-horizon cohort returns
(1d −0.97%, 5d +4.01%, 10d +5.65%, 20d +14.05%, 60d +18.09%) with excess-vs-SPY/QQQ/Sector columns,
random-same-sector + SPY + QQQ + sector-ETF control columns, each carrying sample size **n** (cohort
n=20; random peers n=31). Low-sample figures (n < min_sample 30) are flagged `⚠`. For the
**latest 2026-05-28** every horizon honestly shows "—n=0 ⚠" with the empty-state "No elapsed forward
window for this date yet … No numbers are fabricated to fill the gap." Driven entirely by the global
switcher's resolved date. NA/n honesty intact — no fabrication.

### UT-J-01 — Daily dashboard at a glance
**Verdict:** PASS
**Evidence:** `…/UT-J-01-dashboard-latest.png`
Regime "Risk-on" (a valid label) 74.32/100; candidate counts Actionable 0 / Breakout-watch 8 /
Pullback-watch 1 (all numeric); Top Sectors (SOXX 93.67, WGMI 90.67, SMH 90.00, XLK 79.83, ROBO 74.00)
and Top Themes (Semiconductors 100.00, AI Data Centre 85.00, Cybersecurity 77.50, Crypto 66.50, Power
Grid 64.00) each ≥3 with scores; breadth 65.57% (>50-DMA) / 59.02% (>200-DMA) / net-new-highs 9.02%
(labelled universe-relative); last-scan "Data as-of 2026-05-28".

### UT-J-03 — Theme Leaderboard
**Verdict:** PASS
**Evidence:** `…/UT-J-03-themes-historical-expanded.png`
Themes ranked non-increasing by Theme Score (Nuclear Uranium 100.00 → Power Grid 74.50 → Crypto
Equities 72.50 → AI Data Centre 70.00 → Megacap Leaders 51.50). Expanding the top theme shows member
tickers (CEG, VST, NRG, CCJ, LEU, UEC, +1), 1M +36.30%, 3M +23.15%, breadth 100% (universe-relative),
trend "Strong uptrend", plus a component breakdown. (Captured at as-of 2025-05-28 during the J-13 flow;
structurally untouched this iteration.)

### UT-J-04 — Sector / industry Leaderboard
**Verdict:** PASS
**Evidence:** `…/UT-J-04-sectors-historical.png`
31 sector/industry ETFs ranked by Sector Score (XAR 85.83 → … → ITB 7.33). Each row shows numeric
RS-vs-SPY (XAR +18.90%), distance-from-52w-high (−0.03%), and a trend label ("Strong uptrend").
**SPY is excluded** from the ranked rows (not ranked as a leader against itself) — satisfying the
acceptance. (Captured at as-of 2025-05-28 during the J-13 flow.)

### UT-J-05 — Stock Detail with explainable scores
**Verdict:** PASS
**Evidence:** `…/UT-J-05-stock-detail-nvda.png`
`/stocks/NVDA` (opened from the leaderboard) renders a price+moving-average chart and volume series
(7 canvas charts, "20/50/150/200-DMA", "Volume", 1356 bars). All three scores show A–E bucket + 0–100
value + named components: Leadership **E 47.48** (7 components incl. RS vs SPY·1m/·3m, MA stack,
Proximity to 52w high), Entry Quality **D 66.24** (Proximity to 20-DMA, Volatility contraction, …),
Risk **E 33.79** (Extension above 50-DMA, ATR%, Liquidity, Market regime, Sector strength). Theme chips
(Ai Data Centre, Semiconductors, Megacap Leaders), setup status "Avoid", reason "Leadership is too weak
for a setup — avoid. Top driver: moving-average stack.", and a concrete invalidation "Invalid below the
50-DMA at $198.73". Bonus: NVDA Leadership E 47.48 / Entry D 66.24 / Risk E 33.79 are **identical** to
the leaderboard values (single source of truth).

---

## Failed Tests

None.

---

## Skipped Tests

None. (Frontend `http://localhost:3835` → HTTP 200; backend `http://localhost:8835/api/runs` → HTTP 200;
Chrome MCP available and fully functional.)

---

## Environment

- **Frontend URL:** http://localhost:3835
- **Backend URL:** http://localhost:8835 (provider: seed; latest run 2026-05-28; 158 symbols; 11 run dates)
- **Browser:** Chrome via `mcp__plugin_superpowers-chrome_chrome__use_browser` (1440×900 viewport)
- **Test Date:** 2026-06-01
- **Evidence directory:** `reports/qa/goal-i_can_see_the_wealthy_future_forever-iter-1-evidence/`
- **Console:** clean — no errors/exceptions/failed-fetches across the 31 captured browser states.
- **Note on persistence (not a defect):** the global as-of date lives in an in-memory app-shell
  provider (no localStorage/URL persistence by design), so it survives **client-side** navigation
  (the journeys' path) but resets to Latest on a hard page reload. J-13/J-18 were driven via in-app
  nav accordingly.
