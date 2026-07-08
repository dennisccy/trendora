# Phase goal-mcp-loop-iter-22 — UI Test Results

**Phase:** goal-mcp-loop-iter-22
**Date:** 2026-07-08
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** FAIL

<!-- FAIL reason: UT-03 (P1, happy-path) fails — the Dashboard "Regime × phase cross-view" chart's
     DEFAULT (and max-zoomed-out) view never shows the deep 1996-2018 benchmark history at any common
     viewport width; per the browser-qa-agent verdict rule, any failing P1/happy-path test forces FAIL
     even though all other P1 tests (including the legend/tooltip vendor labeling and the /data
     provenance panel, which are J-14's other two DoD screenshot requirements) pass cleanly. -->

**Overall:** 16/17 tests passed (2 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-01 | Dashboard loads, chart renders | smoke | P1 | Dashboard heading, no backend-unavailable card, cross-view chart renders with data, no console errors | All present exactly as expected; chart rendered with 10 lines, no console errors observed | PASS | `reports/qa/goal-mcp-loop-iter-22-evidence/UT-01-initial.png` |
| UT-02 | `/data` loads with new panel present | smoke | P1 | Data Manager heading, existing panels + new "Index & benchmark data provenance" panel with a table | All present; new panel renders a populated table directly below "Macro feed" | PASS | `reports/qa/goal-mcp-loop-iter-22-evidence/UT-02-data-page-full.png` |
| UT-03 | Deep lines extend to 1996 | happy-path | P1 | Default view shows a visible "gap" (ETF lines start late); hovering left edge ≈ 1996-01-02 | Default view (1440×900) spans only ~2018-2026; left-edge hover shows ~2018-02-09/2018-03-xx (reproduced 3×); no gap visible (all 10 series already have data at the visible left edge); wheel zoom-out caps at the same ~8yr boundary; confirmed at 1920×1080 default is still only ~2015-2026 | **FAIL** | `reports/qa/goal-mcp-loop-iter-22-evidence/UT-03-fail-fullpage.png`, `UT-03-fail-crop.png` |
| UT-04 | Legend shows vendor labels (3 categories) | happy-path | P1 | Exactly 10 entries, vendor tag in faint gray for Stooq/Yahoo/FRED-macro proxy, no tag on the 5 ETFs | Exact match — all 10 names, order, and vendor tags correct; 5 ETF entries have no tag | PASS | `reports/qa/goal-mcp-loop-iter-22-evidence/UT-04-legend-crop.png` |
| UT-05 | Tooltip shows vendor suffix | happy-path | P1 | `^SPX · Stooq`, `^VIX · Yahoo`, `^TNX · FRED-macro proxy`; no suffix for the 5 ETFs | Confirmed via DOM extraction at two different hovered dates; exact match | PASS | `reports/qa/goal-mcp-loop-iter-22-evidence/UT-05-tooltip-crop.png` |
| UT-06 | 10 legend colors all distinct | happy-path | P1 | No two of 10 swatches share a color; SPY(teal) ≠ ^SPX(purple) specifically | Confirmed via computed-style RGB extraction — all 10 distinct; SPY `rgb(79,209,197)` vs ^SPX `rgb(167,139,250)` | PASS | `reports/qa/goal-mcp-loop-iter-22-evidence/UT-06-legend-zoom.png` |
| UT-07 | `/data` panel lists 10 series correctly | happy-path | P1 | Exact hint text; 10 rows in reference order; ^SPX row Stooq/1996-01-02; ^TNX row FRED-macro proxy/2021-01-04 | Byte-exact match on all 10 rows (verified via DOM table extraction) and hint text | PASS | `reports/qa/goal-mcp-loop-iter-22-evidence/UT-07-provenance-panel-crop.png` |
| UT-08 | ETF lines show no vendor tag (chart) | validation | P2 | No `(vendor)` in legend, no `· vendor` in tooltip for SPY/QQQ/IWM/RSP/DIA | Confirmed absent in both legend and tooltip DOM text | PASS | `reports/qa/goal-mcp-loop-iter-22-evidence/UT-04-legend-crop.png`, `UT-05-tooltip-crop.png` |
| UT-09 | ETF/proxy rows read honestly (`/data`) | validation | P2 | SPY/QQQ rows: Vendor `—`, real First-bar date (not a dash); ^TNX: "proxy"/"spread" wording, vendor `FRED-macro proxy` | Exact match: SPY `—`/2005-02-25, QQQ `—`/1999-03-10, ^TNX "10Y-2Y spread proxy (^TNX)" / `FRED-macro proxy` | PASS | `reports/qa/goal-mcp-loop-iter-22-evidence/UT-07-provenance-panel-crop.png` |
| UT-10 | Whole-backend-down error is honest | error | P2 | One red "Backend unavailable" card, exact message, no other panel renders, clean recovery after restart | Exact match; recovered fully after backend restart | PASS | `reports/qa/goal-mcp-loop-iter-22-evidence/UT-10-backend-down.png` |
| UT-11 | Isolated panel error (automation-only) | error | P3 | Provenance panel shows isolated "Vendor disclosure unavailable" when only `/api/indexes` is blocked | Not executed — Chrome MCP tool exposes no network-request-blocking/interception action (no `Network.setBlockedURLs`/Fetch-domain equivalent) | SKIPPED | none |
| UT-12 | Loading skeleton (best-effort) | ux | P3 | Brief pulsing skeleton block before table appears | Not observed — no network-throttling action available in the Chrome MCP tool; local load completed before a manual check could catch it (test spec treats this as inconclusive, not a failure) | SKIPPED | none |
| UT-13 | Existing ETF lines unchanged | regression | P1 | 5 original entries present, same order/colors; chart controls still work | Confirmed: names/order/colors byte-identical to expected (teal/green/amber/red/gray); extensive zoom/pan/hover interaction during UT-03 investigation worked smoothly throughout | PASS | `reports/qa/goal-mcp-loop-iter-22-evidence/UT-04-legend-crop.png` |
| UT-14 | `/stocks` — no leaked index rows (J-01) | regression | P1 | Real tickers only; no `^SPX`/`^NDX`/`^DJI`/`^VIX`/`^TNX` rows | Confirmed via full-table DOM scan of all 541 rows — zero leaked symbols | PASS | `reports/qa/goal-mcp-loop-iter-22-evidence/UT-14-stocks-leaderboard.png` |
| UT-15 | Market Regime + evidence link intact (J-04) | regression | P1 | Regime badge/score render; link navigates to `/evidence`; Phase & Severity card unaffected | Confirmed: "Risk-on 72.25/100" + "Expansion" badges render; link navigated to `/evidence` cleanly | PASS | `reports/qa/goal-mcp-loop-iter-22-evidence/UT-01-initial.png`, `UT-15-18-evidence-page.png` |
| UT-16 | Universe count unchanged (J-12) | regression | P1 | `/data` universe count == `/stocks` leaderboard count, unchanged by this iteration | Both read 541 (cross-verified: `/data` "Universe (as of date) 541"; `/stocks` "541 / 541") | PASS | `reports/qa/goal-mcp-loop-iter-22-evidence/UT-14-stocks-leaderboard.png` |
| UT-17 | Ticker detail chart + toggle (J-10) | regression | P2 | "Full history"/"Recent" toggle changes plotted range smoothly, no error | Confirmed: Full history=3185 bars ↔ Recent=1255 bars, toggled both directions without error | PASS | `reports/qa/goal-mcp-loop-iter-22-evidence/UT-17-ticker-detail-before.png`, `UT-17-recent-crop.png`, `UT-17-fullhistory-restored.png` |
| UT-18 | Evidence ledger unaffected (J-03/J-05) | regression | P1 | Exact subtitle; every claim honestly "Not yet proven"/FAIL, no leaked "Proven" | Subtitle byte-exact; all 7 ledger claims show FAIL; zero standalone "Proven" occurrences outside the explanatory subtitle | PASS | `reports/qa/goal-mcp-loop-iter-22-evidence/UT-15-18-evidence-page.png` |
| UT-19 | New panel discoverable in ≤2 clicks | ux | P2 | Reached in ≤2 clicks via existing nav; title+hint self-explanatory | Reached in exactly 1 click (Dashboard → "Data Manager"); title + hint text are self-explanatory (verified text in UT-07) | PASS | `reports/qa/goal-mcp-loop-iter-22-evidence/UT-02-data-page-full.png` |

---

## Passed Tests

### UT-01 — Dashboard loads and the cross-view chart renders
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-22-evidence/UT-01-initial.png`
- "Dashboard" heading + "The daily snapshot at a glance" subtitle visible; no red "Backend unavailable" card.
- "Regime × phase cross-view" card renders directly below "Market Regime" / "Market Phase & Severity", with a populated two-pane chart (not blank, not a stuck spinner).
- Console check: `enable_console_logging` + `get_console_messages` after full load returned no messages (no errors/warnings logged by the app during load or interaction).

### UT-02 — `/data` loads with the existing panels plus the new provenance panel
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-22-evidence/UT-02-data-page-full.png`
- "Data Manager" heading visible; no backend-unavailable card.
- All pre-existing panels render with real data: Dataset coverage, Rebuild snapshots, Universe resolution, Dynamic-universe membership timeline, Per-date availability, Missing-data diagnostic, Macro feed.
- New "Index & benchmark data provenance" card renders directly below "Macro feed," containing a populated table (not blank, not a stuck skeleton).

### UT-04 — Chart legend shows vendor labels spanning all three vendor categories
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-22-evidence/UT-04-legend-crop.png`
- Legend lists exactly 10 index/benchmark entries in the exact expected order and text: `S&P 500 (SPY)`, `Nasdaq 100 (QQQ)`, `Russell 2000 (IWM)`, `S&P 500 Equal-Weight (RSP)`, `Dow 30 (DIA)`, `S&P 500 Index (^SPX) (Stooq)`, `Nasdaq 100 Index (^NDX) (Stooq)`, `Dow Jones Industrial Average (^DJI) (Stooq)`, `CBOE Volatility Index (^VIX) (Yahoo)`, `10Y-2Y spread proxy (^TNX) (FRED-macro proxy)`.
- Vendor tags render in a visibly lighter/faint gray tone (`text-text-faint` class, confirmed in code and visually) in parentheses after the name — present for exactly the 5 deep/macro series, spanning all three vendor categories (Stooq/Yahoo/FRED-macro proxy).
- The 5 original ETF entries carry no trailing parenthetical at all.

### UT-05 — Hover tooltip shows the vendor next to a deep series' symbol
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-22-evidence/UT-05-tooltip-crop.png`
- Hovering a recent date (all 10 series present) produced (via DOM extraction): `SPY+672.48% QQQ+1474.40% IWM+423.45% RSP+534.91% DIA+459.61% ^SPX· Stooq+1069.46% ^NDX· Stooq+4681.22% ^DJI· Stooq+852.16% ^VIX· Yahoo+42.58% ^TNX· FRED-macro proxy+443.47%`.
- Exact match to expectations: `· <vendor>` suffix present only for the 5 deep/macro symbols; bare symbol+value for the 5 ETFs.
- Minor cosmetic note (not a failure): in the screenshot crop, the longest vendor label ("^TNX · FRED-macro proxy") visually crowds/slightly overlaps its percentage value at this tooltip width — content is correct (confirmed via DOM) and legible, just tightly spaced.

### UT-06 — All 10 legend color swatches are visually distinct
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-22-evidence/UT-06-legend-zoom.png`
- Computed-style extraction of each swatch's `background-color`: SPY `rgb(79,209,197)`, QQQ `rgb(52,211,153)`, IWM `rgb(251,191,36)`, RSP `rgb(248,113,113)`, DIA `rgb(139,152,169)`, ^SPX `rgb(167,139,250)`, ^NDX `rgb(251,141,63)`, ^DJI `rgb(75,205,81)`, ^VIX `rgb(85,184,226)`, ^TNX `rgb(244,124,213)` — all 10 distinct.
- Specifically confirmed SPY (teal) vs ^SPX (purple) are clearly different — the exact pair the old 5-color wraparound bug would have collided.

### UT-07 — `/data` provenance panel lists all 10 series with correct vendor + first-bar date
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-22-evidence/UT-07-provenance-panel-crop.png`
- Hint text byte-exact: "Every index/benchmark/macro line on the major-indexes chart, with its honest data vendor and real first-bar date — the same GET /api/indexes payload the Dashboard chart reads, never a recompute."
- Table has exactly 10 rows in the exact reference order; extracted via DOM (`Series | Vendor | First bar`):
  `S&P 500 (SPY) | — | 2005-02-25`, `Nasdaq 100 (QQQ) | — | 1999-03-10`, `Russell 2000 (IWM) | — | 2005-02-25`, `S&P 500 Equal-Weight (RSP) | — | 2005-02-25`, `Dow 30 (DIA) | — | 2005-02-25`, `S&P 500 Index (^SPX) | Stooq | 1996-01-02`, `Nasdaq 100 Index (^NDX) | Stooq | 1996-01-02`, `Dow Jones Industrial Average (^DJI) | Stooq | 1996-01-02`, `CBOE Volatility Index (^VIX) | Yahoo | 1996-01-02`, `10Y-2Y spread proxy (^TNX) | FRED-macro proxy | 2021-01-04`.
- Cross-checked against `GET /api/indexes?full=true` directly (curl) — byte-identical `vendor`/`first` values.

### UT-08 — Chart legend/tooltip show no vendor tag for the 5 original ETF lines
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-22-evidence/UT-04-legend-crop.png`, `UT-05-tooltip-crop.png`
- Legend: none of the 5 ETF entries has any parenthetical text after its name.
- Tooltip: none of the 5 ETF rows has a `·`-prefixed suffix (confirmed via raw DOM text — no stray dot, no "null", no "undefined").

### UT-09 — `/data` panel: ETF rows show an honest "—" vendor; the FRED-macro-proxy row reads honestly
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-22-evidence/UT-07-provenance-panel-crop.png`
- SPY row: Vendor `—` (em dash), First bar `2005-02-25` (a real date, not a dash — matches the plan's Correction #1).
- QQQ row: Vendor `—`, First bar `1999-03-10`.
- ^TNX row: Series name reads "10Y-2Y spread proxy (^TNX)" (says "proxy"/"spread," never implies a literal real-time yield); Vendor badge reads exactly "FRED-macro proxy" (not "FRED" alone, not "Yahoo"/"Stooq").

### UT-10 — `/data` shows one honest "Backend unavailable" message when the whole backend is down
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-22-evidence/UT-10-backend-down.png`
- Stopped the backend process (`kill -TERM` on the uvicorn PID), reloaded `/data`: page showed the "Data Manager" heading, then exactly ONE red-bordered card reading "Backend unavailable" / "Dataset coverage could not load from the API. No figures are shown rather than fabricated values. Confirm the backend is running and retry." — byte-exact match to the expected text. No other panel rendered below it. No blank page, no stack trace.
- Restarted the backend (`scripts/start-backend.sh`, confirmed healthy via `/api/health`) and reloaded: page returned to the normal UT-02 state with all panels (including the new provenance panel) rendering real data again.

### UT-13 — Regression: the 5 pre-existing ETF lines and legend entries are unchanged
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-22-evidence/UT-04-legend-crop.png`
- All 5 original entries present, same relative order, same original colors (SPY=teal, QQQ=green, IWM=amber, RSP=red, DIA=gray) — matches pre-iteration expectations exactly.
- Chart interactivity (hover/zoom/pan) was exercised extensively during the UT-03 investigation (dozens of wheel-zoom and drag-pan operations) without any error, crash, or visual corruption — the existing chart mechanics are intact.

### UT-14 — Regression: `/stocks` leaderboard shows no leaked index/macro symbol rows (J-01)
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-22-evidence/UT-14-stocks-leaderboard.png`
- "Stocks" heading + exact subtitle visible; table renders 541 real-ticker rows (INTC, GL, TENB, MRVL, ... ), no crash.
- Full-table DOM scan for `^SPX`/`^NDX`/`^DJI`/`^VIX`/`^TNX` in any row returned zero matches.

### UT-15 — Regression: Dashboard "Market Regime" card + evidence link intact (J-04)
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-22-evidence/UT-01-initial.png`, `UT-15-18-evidence-page.png`
- "Market Regime" card shows badge "Risk-on" + score "72.25/100"; "Market Phase & Severity" shows "Expansion" + "29.95/100 severity" + "P(bear) 0.00" — both render normally alongside the chart's 5 new lines.
- Clicking "See evidence proven in this regime →" (`a[href="/evidence"]`) navigated to `http://localhost:3255/evidence`, which loaded the "Evidence" heading without error.

### UT-16 — Regression: `/data` "Universe" count is unchanged and matches `/stocks`' count (J-12)
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-22-evidence/UT-14-stocks-leaderboard.png`
- `/data` "Universe (as of date)" = 541. `/stocks` leaderboard shows "541 / 541" and a 541-row table. Both counts match and are unaffected by this iteration's 5 new configured symbols (deep indices correctly excluded from the scored universe).

### UT-17 — Regression: `/stocks/{ticker}` deep-history chart + Recent/Full history toggle (J-10)
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-22-evidence/UT-17-ticker-detail-before.png`, `UT-17-recent-crop.png`, `UT-17-fullhistory-restored.png`
- Opened `/stocks/INTC`; candlestick/price chart with moving averages renders, no crash.
- Toggle confirmed bidirectional and functional: "Full history" → 3185 bars (`history since 1996-01-02 · older bars weekly-sampled`); "Recent" → 1255 bars (visibly narrower, ~mid-2021 to 2026); back to "Full history" → 3185 bars restored. No error at any step — confirms this iteration's backend/DB changes (3 new symbols in `daily_prices`) did not affect per-ticker queries.

### UT-18 — Regression: `/evidence` ledger still reads "Not yet proven"/FAIL only (J-03/J-05)
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-22-evidence/UT-15-18-evidence-page.png`
- Subtitle byte-exact: "The certified-claims ledger — the single source of proven-ness. A signal reads "Proven" ONLY when a referee-certified, out-of-sample, control-beating claim backs it; everything else honestly reads "Not yet proven.""
- All 7 ledger entries (leadership_score, Breakout-watch setup, ma_stack — top decile, + 4 more) show a red "FAIL" verdict badge. Regex scan of the whole page for a standalone "Proven" (excluding "Not yet proven") found exactly one hit, located inside the explanatory subtitle sentence itself — not an actual claim status. No leaked "Proven" claim.

### UT-19 — UX: the new provenance panel is discoverable within 2 clicks from home
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-22-evidence/UT-02-data-page-full.png`
- Dashboard (click 0) → "Data Manager" in the left sidebar (click 1) → scroll (no further click) reaches the new panel — 1 click, within the ≤2-click blueprint requirement, no new nav item needed.
- Title "Index & benchmark data provenance" + hint text (quoted under UT-07) are self-explanatory without external context.

---

## Failed Tests

### UT-03 — Deep benchmark lines (`^SPX`/`^NDX`/`^DJI`/`^VIX`) extend back to 1996, before the ETF lines' 2005 floor
**Verdict:** FAIL
**Failure:** The Dashboard "Regime × phase cross-view" chart's default (freshly-loaded, uninteracted) view — and its maximum-zoomed-out state reachable via mouse wheel — never shows the deep 1996–2018 portion of the `^SPX`/`^NDX`/`^DJI`/`^VIX` lines at any common viewport width. The specific verification method in the test plan (hover the left ~2–5% of the chart in the default view, expect a date at/near 1996-01-02) does not hold.
**Evidence:** `reports/qa/goal-mcp-loop-iter-22-evidence/UT-03-fail-fullpage.png`, `UT-03-fail-crop.png` (both at 1440×900, the same viewport used for every other test case in this run)

**Steps taken:**
1. Navigated to `http://localhost:3255` (fresh page load, no prior interaction) at 1440×900 — the same viewport used throughout this test run.
2. Moved the pointer to the leftmost ~2px of the chart's plotted canvas (x=272 of a canvas spanning x=269–1311).
3. Read the resulting crosshair tooltip via DOM extraction and via the visible x-axis label.
4. Repeated on 3 separate fresh page loads for reproducibility, and additionally probed with mouse-wheel zoom-out (400 synthetic `wheel` events, `deltaY:+120`, dispatched directly on the chart canvas) and with a large manual drag-pan (10× full-width drags) to determine the reachable range.
5. Repeated the default-state check at 1920×1080 (common desktop) and 3840×1200 (uncommon ultra-wide) viewports to check whether this is viewport-width-dependent.
6. Cross-checked the underlying data directly via `curl http://localhost:8255/api/indexes?full=true`.

**Expected:** Per the test plan: a visible "starting gap" (several lines absent across the left ~30% of the chart) in the default view, and hovering the left edge shows a date at/near 1996-01-02 with `^SPX`/`^NDX`/`^DJI`/`^VIX` present but `SPY`/`QQQ`/`IWM`/`RSP`/`DIA`/`^TNX` honestly absent.

**Actual:**
- At 1440×900 (default, untouched): the chart's x-axis spans only **~2018-02-09 to 2026-07-01** (~8 years). Hovering the left edge produced tooltip dates of `2018-02-09`, `2018-03-26`, and `2018-03-28` across three separate fresh loads — never within decades of 1996-01-02.
- **No "gap" is visible anywhere in the default view**: at the leftmost visible point, all 10 series (including the 4 ETFs whose real start is 2005) already show non-zero percentage values (e.g., at 2018-02-09: `SPY +148.43%, QQQ +243.02%, IWM +156.39%, RSP +181.10%, DIA +161.66%, ^SPX +322.01%, ^NDX +994.43%, ^DJI +367.23%, ^VIX +138.39%`) — because even the latest-starting ETF (2005) already has 13 years of history by the view's 2018 left edge.
- **Zooming out does not reach further back**: dispatching 400 synthetic mouse-wheel events (`deltaY:+120`, confirmed to zoom via a preceding zoom-in test that visibly narrowed the range to ~2 months) returned the view to the exact same ~2018-2026 boundary — this appears to be the library's effective maximum zoom-out, not merely the default.
- **Panning (drag) does reach the deep history**, confirmed by manually dragging the chart ~10 full-pane-widths toward the past — `^SPX`/`^NDX`/`^DJI`/`^VIX` data is genuinely present back to 1996 and renders correctly once panned there — but this requires many non-obvious repeated drag gestures with no visible scrollbar, minimap, position indicator, or "view full history" control; the card's only button is "Hide." A user would have no way to discover that this is necessary or how far to drag.
- **Not a narrow-viewport artifact**: re-tested at 1920×1080 (very common desktop resolution) — default view is still only **~2015-2026** (~11 years), still short of even SPY's 2005 start. Only at an uncommon 3840×1200 viewport does the default view extend back far enough (~1999) to precede SPY's 2005 start (still short of the 1996 target).
- **Underlying data is correct** (this is a presentation gap, not a data gap): `GET /api/indexes?full=true` confirms `^SPX`/`^NDX`/`^DJI`/`^VIX` each have `"first": "1996-01-02"` and their `points[0].date` is genuinely `1996-01-02`/`1996-01-02`/`1996-01-02` respectively (7,674-7,675 points each), byte-matching `meta.json`. The `/data` provenance panel (UT-07/UT-09) discloses this correctly. Only the Dashboard chart's own default/reachable view fails to surface it.
- **Likely root cause** (from reading `apps/frontend/components/phase-cross-view-chart.tsx:315`, which calls `chart.timeScale().fitContent()` once after all data loads, combined with the empirical zoom-out ceiling matching the same boundary as the default): the `lightweight-charts` library enforces a minimum bar-spacing floor; with ~7,674 daily bars needed for the full 1996-2026 window and only a ~1,042px-wide plotted pane at 1440px viewport (or ~1,620px at 1920px), `fitContent()` cannot legally fit all bars at the minimum spacing and instead settles on (and cannps zoom-out at) the most-recent subset of bars that does fit — which is why wider viewports (more pixels) push the reachable boundary further back but never to 1996 within any reasonably-sized browser window without further code changes (e.g., an explicit `minBarSpacing` override, an explicit initial `setVisibleRange`, or reducing total bar count via older-bar sampling — the `/stocks/{ticker}` detail chart already does the latter, per UT-17's "older bars weekly-sampled" caption).

This does not affect UT-04/UT-05/UT-06/UT-07/UT-08/UT-09/UT-13 (legend, tooltip vendor formatting, and the `/data` panel are independent of the chart's current zoom/pan state and all verified correct).

---

## Skipped Tests

### UT-11 — Provenance panel's own isolated "Vendor disclosure unavailable" message
**Verdict:** SKIPPED
**Reason:** Requires blocking only `*/api/indexes*` requests while leaving other endpoints unaffected (e.g., CDP `Network.setBlockedURLs` or Fetch-domain interception). The `mcp__plugin_superpowers-chrome_chrome__use_browser` tool's action set (navigate/click/type/extract/screenshot/eval/select/attr/await_*/tab management/viewport/cookies/console/profile/lifecycle) exposes no network-request-blocking or pre-navigation script-injection primitive, so per-URL request interception is not achievable from this tool. The test spec explicitly permits skipping this case when blocking capability is unavailable, and notes UT-10 (executed, PASS) already covers the human-executable error path.

### UT-12 — Provenance panel loading skeleton
**Verdict:** SKIPPED
**Reason:** Best-effort/P3 per its own spec. No network-throttling action is exposed by the Chrome MCP tool, and the local backend/frontend respond fast enough that the transient skeleton state could not be observed with a manual navigate-then-check approach (the panel's table was already fully populated by the time control returned). Per the test spec, a missed observation under these conditions is inconclusive, not a failure.

---

## Environment

- **Frontend URL:** http://localhost:3255
- **Backend URL:** http://localhost:8255
- **Browser:** Chrome via MCP (`mcp__plugin_superpowers-chrome_chrome__use_browser`), primary viewport 1440×900 (also probed 1920×1080 and 3840×1200 for UT-03)
- **Test Date:** 2026-07-08
- **Evidence directory:** `reports/qa/goal-mcp-loop-iter-22-evidence/`
- **Note:** the backend was deliberately stopped and restarted as part of executing UT-10 (`kill -TERM` on the uvicorn process, then `scripts/start-backend.sh`); it was confirmed healthy (`GET /api/health` → 200) before proceeding to subsequent tests.
