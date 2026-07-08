# Phase goal-mcp-loop-iter-22 — UI Test Plan

**Phase:** goal-mcp-loop-iter-22
**Date:** 2026-07-08
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3255
**Backend URL:** http://localhost:8255

---

## Scope

J-14: deep, vendor-labeled index/macro context. The only two **live** user-reachable surfaces this
iteration touches (per the ui-surface-map, independently re-confirmed below) are:

1. **Dashboard (`/`) → "Regime × phase cross-view" card** — gains 5 new lines (`^SPX`/`^NDX`/`^DJI`/
   `^VIX`/`^TNX`), a per-series vendor label on the legend + hover tooltip, and an extended 10-slot
   line-color palette.
2. **`/data` → new "Index & benchmark data provenance" panel** — a table disclosing every series' vendor
   and honest first-bar date, placed directly under the existing "Macro feed" panel.

`components/index-regime-chart.tsx` / `components/major-indexes-card.tsx` received an identical code fix
but are **dead code** (zero imports from any route — verified independently via
`grep -rn "major-indexes-card\|MajorIndexesCard" apps/frontend/app/` → no hits). No test case below
targets that component; do not spend time hunting for a second "Major indexes & regime" card on any page.

## Global Preconditions (apply to every test case unless overridden)

- Prod-mode services running, per the iter-20/21 harness-discipline lesson: `rm -rf apps/frontend/.next`
  was run before starting the frontend; backend reachable at `http://localhost:8255`, frontend at
  `http://localhost:3255`.
- The local database already has the deep symbols loaded — independently verified live (2026-07-08):
  `^SPX`/`^NDX`/`^DJI` each have 7,674 `daily_prices` rows spanning `1996-01-02` → `2026-07-01`; `^VIX` has
  7,675 rows from `1996-01-02`; `^TNX` has 1,363 rows from `2005-02-28`. **Do not re-run
  `scripts/load_missing_index_symbols.py`** — it is a one-time, already-executed backfill (idempotent if
  re-run, but not needed).
- Browser has no prior `localStorage` override that hides the cross-view card (see UT-01 precondition).
- No login is required anywhere in this app (no auth system).

## Reference: exact expected values (verified against live `data/seed/meta.json` + `daily_prices`, not just the dev handoff's prose)

All 10 `index_chart.symbols` entries currently have bars, so **all 10 render** (none are honestly omitted
today). Row order below is both the chart's legend order and the `/data` panel's table order (both read
`cfg.index_chart.symbols` in this exact sequence):

| # | Symbol | Display name (chart legend / `/data` "Series") | Vendor badge | First bar (byte-exact) |
|---|--------|--------------------------------------------------|--------------|-------------------------|
| 1 | SPY | `S&P 500 (SPY)` | `—` | `2005-02-25` |
| 2 | QQQ | `Nasdaq 100 (QQQ)` | `—` | `1999-03-10` |
| 3 | IWM | `Russell 2000 (IWM)` | `—` | `2005-02-25` |
| 4 | RSP | `S&P 500 Equal-Weight (RSP)` | `—` | `2005-02-25` |
| 5 | DIA | `Dow 30 (DIA)` | `—` | `2005-02-25` |
| 6 | ^SPX | `S&P 500 Index (^SPX)` | `Stooq` | `1996-01-02` |
| 7 | ^NDX | `Nasdaq 100 Index (^NDX)` | `Stooq` | `1996-01-02` |
| 8 | ^DJI | `Dow Jones Industrial Average (^DJI)` | `Stooq` | `1996-01-02` |
| 9 | ^VIX | `CBOE Volatility Index (^VIX)` | `Yahoo` | `1996-01-02` |
| 10 | ^TNX | `10Y-2Y spread proxy (^TNX)` | `FRED-macro proxy` | `2021-01-04` |

Notes:
- The Vendor badge is `—` (em dash) for any symbol with no `vendor` key in `meta.json` (SPY/QQQ/IWM/RSP/
  DIA) — **never** blank and never a fabricated vendor name.
- `first` is read from the manifest for **every** series (not gated on having a `vendor`) — this is why
  the ETF rows still show a real date, not a dash (see Correction #1 below).
- `^TNX`'s live `daily_prices` table actually has bars back to `2005-02-28` (a pre-existing, out-of-scope
  data quirk noted in the dev handoff), but its **disclosed** `first` is `2021-01-04` — byte-matching
  `meta.json`, per the DoD's explicit "read from the manifest, not the DB" instruction. Do not test `^TNX`
  for chart/disclosure date consistency; use `^SPX` (clean, no such discrepancy) wherever a byte-match
  check is needed.
- These are local build-artifact values (`apps/backend/data/trendora.db`, gitignored) as of 2026-07-08.
  `first` dates are stable (sourced from the committed manifest); do not key any assertion off row counts
  or `last` dates, which drift forward as new data loads.

## Corrections to prior iteration artifacts (verified independently before writing this plan)

1. **`/data` panel "First bar" for the 5 ETF rows is NOT "—".** The ui-surface-map's "honest-omission
   rows" entry states the SPY row shows "First bar '—'". Reading `compute_index_series`
   (`apps/backend/app/engine/indexes.py:156-162`) shows `first_date = meta_row.get("first")` runs for
   **every** configured symbol, independent of whether that symbol has a `vendor` key — and SPY's
   `meta.json` row is `{"symbol": "SPY", "bars": 5369, "first": "2005-02-25", "last": "2026-07-01"}` (no
   `vendor` key, but a real `first`). So SPY's row correctly shows Vendor **"—"** and First bar
   **"2005-02-25"** — a real date, not a dash. UT-09 below tests the corrected behavior; do not flag
   "2005-02-25" appearing in that cell as a bug.
2. **A full backend outage does not leave "the rest of `/data` continuing to render normally."** The
   ui-surface-map's error-state row assumes stopping the backend produces an isolated "Vendor disclosure
   unavailable" panel while the rest of the page renders. Reading `app/data/page.tsx` shows the entire page
   body (every panel, including the new one) is gated behind one shared `fetchDataCoverage` call's
   `state.kind === "ok"` branch — a full backend outage instead renders **one page-level "Backend
   unavailable" card and nothing else** (no panels at all). The panel's own isolated error state is real,
   correct code, but is reachable only by failing `/api/indexes` specifically while `/api/data` still
   succeeds (e.g., via DevTools network-request blocking). See UT-10 (whole-backend-down, human-executable)
   vs. UT-11 (isolated-panel error, automation-only) for the two separate, accurate tests.

---

## Test Cases

### UT-01 — Dashboard loads and the cross-view chart renders (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Global preconditions above.
- Fresh browser profile or cleared `localStorage` key `trendora.dashboard.phaseCrossView` (if a prior
  session clicked "Hide", the card starts collapsed — see step 3 fallback).

**Steps:**
1. Navigate to `http://localhost:3255`.
2. Wait for the page to finish loading.
3. If you see a dashed button reading "Show regime × phase cross-view" instead of a chart, click it.

**Expected Result:**
- The heading "Dashboard" and subtitle "The daily snapshot at a glance" are visible at the top.
- No red "Backend unavailable" card appears.
- A card titled "Regime × phase cross-view" is visible, directly below the "Market Regime" and "Market
  Phase & Severity" cards, containing a rendered chart (not a blank area, not a spinner stuck forever).
- No browser console errors.

---

### UT-02 — `/data` loads with the existing panels plus the new provenance panel (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/data`

**Preconditions:**
- Global preconditions above.

**Steps:**
1. Navigate to `http://localhost:3255/data`.
2. Wait for the page to finish loading.
3. Scroll down through the whole page once, top to bottom.

**Expected Result:**
- The heading "Data Manager" is visible at the top.
- No red "Backend unavailable" card appears.
- The pre-existing "Dataset coverage", "Rebuild snapshots for current universe", "Universe resolution",
  "Dynamic-universe membership timeline", "Per-date availability", and "Macro feed" panels all render with
  real data (not blank).
- A new card titled **"Index & benchmark data provenance"** is visible directly below the "Macro feed"
  panel, containing a table (not a blank card, not a permanent skeleton).

---

### UT-03 — Deep benchmark lines (`^SPX`/`^NDX`/`^DJI`/`^VIX`) extend back to 1996, before the ETF lines' 2005 floor (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/` — "Regime × phase cross-view" card

**Preconditions:**
- UT-01 passed (chart rendered).

**Steps:**
1. Navigate to `http://localhost:3255` and confirm the "Regime × phase cross-view" chart is visible (per
   UT-01). No range control exists on this chart — it always plots full history by default.
2. Look at the overall shape of the chart first: most of the 10 colored lines should visibly start
   partway across the chart (around the left third of the width, roughly where the year 2005 falls in a
   1996–2026 span) — this is the 5 pre-existing ETF lines starting late. A smaller number of lines should
   extend all the way to the chart's left edge.
3. Move the mouse pointer to hover over the very left edge of the chart's plotted area (the leftmost ~2–5%
   of its width, where the x-axis would read a date in early-to-mid 1996).
4. Read the tooltip box that appears in the upper-right of the chart.

**Expected Result:**
- Step 2: a visible "starting gap" — several lines have no path at all across the left ~30% of the chart,
  while a few lines run the full width.
- Step 4: the tooltip's date reads a day at or near `1996-01-02`. Its list of series includes `^SPX`,
  `^NDX`, `^DJI`, and `^VIX` (each with a `%` value) — and does **not** include `SPY`, `QQQ`, `IWM`, `RSP`,
  `DIA`, or `^TNX` (they have no data this early — honestly absent from the tooltip, not shown as 0% or a
  fabricated flat line).

---

### UT-04 — Chart legend shows vendor labels spanning all three vendor categories (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/` — "Regime × phase cross-view" card legend

**Preconditions:**
- UT-01 passed.

**Steps:**
1. Navigate to `http://localhost:3255`.
2. Scroll to the legend row directly below the "Regime × phase cross-view" chart (a horizontal wrapped
   list of colored-dot + label entries, above the "Phase pane:" row).
3. Count the entries and read each one's text.

**Expected Result:**
- The legend lists exactly **10** index/benchmark entries (in this order): `S&P 500 (SPY)`,
  `Nasdaq 100 (QQQ)`, `Russell 2000 (IWM)`, `S&P 500 Equal-Weight (RSP)`, `Dow 30 (DIA)`,
  `S&P 500 Index (^SPX) (Stooq)`, `Nasdaq 100 Index (^NDX) (Stooq)`,
  `Dow Jones Industrial Average (^DJI) (Stooq)`, `CBOE Volatility Index (^VIX) (Yahoo)`,
  `10Y-2Y spread proxy (^TNX) (FRED-macro proxy)`.
- The vendor tag reads exactly `Stooq`, `Yahoo`, or `FRED-macro proxy` (capitalization and hyphenation as
  written) in a lighter/faint gray tone in parentheses immediately after the name — confirmed present for
  at least one entry from each of the three categories.
- The 5 original entries (SPY/QQQ/IWM/RSP/DIA) show **no** trailing parenthetical vendor tag at all.

---

### UT-05 — Hover tooltip shows the vendor next to a deep series' symbol (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/` — "Regime × phase cross-view" chart tooltip

**Preconditions:**
- UT-01 passed.

**Steps:**
1. Navigate to `http://localhost:3255`.
2. Move the mouse pointer anywhere over the chart's plotted area, near the right-hand (recent) side, where
   all 10 lines have data.
3. Read the tooltip box's list of series values.

**Expected Result:**
- The tooltip shows the hovered date, then one row per visible series, each formatted as the raw symbol
  (e.g. `^SPX`, not the full name) followed by its `%` value.
- For `^SPX`, `^NDX`, `^DJI` rows, a lighter-gray `· Stooq` suffix appears right after the symbol (e.g.
  `^SPX · Stooq`). For `^VIX`, `· Yahoo`. For `^TNX`, `· FRED-macro proxy`.
- For `SPY`, `QQQ`, `IWM`, `RSP`, `DIA` rows, there is **no** `·` suffix at all — just the bare symbol and
  its `%` value.
- (Note: the tooltip shows the raw ticker symbol, not the friendly legend name — this is pre-existing
  behavior, unchanged by this iteration; only the vendor suffix is new.)

---

### UT-06 — All 10 legend color swatches are visually distinct; no repeated color (happy path / visual defect fix)

**Type:** happy-path
**Priority:** P1
**Surface:** `/` — "Regime × phase cross-view" card legend

**Preconditions:**
- UT-04 passed (10 legend entries confirmed present).

**Steps:**
1. Navigate to `http://localhost:3255` and locate the 10-entry legend (per UT-04).
2. Take a full-width screenshot or zoom in on the row of small colored dots to the left of each of the 10
   labels.
3. Compare the color dot next to entry 1 (`S&P 500 (SPY)`) against the color dot next to entry 6
   (`S&P 500 Index (^SPX) (Stooq)`) specifically — this is the exact pair that a since-fixed bug would
   have rendered identically (the old 5-color palette wrapped every 5th line back to the 1st color).
4. Visually scan all 10 dots against each other.

**Expected Result:**
- Entry 1's dot (teal/`--accent`) and entry 6's dot (purple/`--snapshot`) are clearly different colors —
  they must NOT look like the same swatch.
- No two of the 10 dots are the same color as each other.

---

### UT-07 — `/data` provenance panel lists all 10 series with correct vendor + first-bar date (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/data` — "Index & benchmark data provenance" panel

**Preconditions:**
- UT-02 passed (panel visible).

**Steps:**
1. Navigate to `http://localhost:3255/data`.
2. Scroll to the "Index & benchmark data provenance" card (directly below "Macro feed").
3. Read its hint text under the title.
4. Read the table, which has 3 columns: "Series", "Vendor", "First bar".
5. Locate the row whose Series column reads `S&P 500 Index (^SPX)`.
6. Locate the row whose Series column reads `10Y-2Y spread proxy (^TNX)`.

**Expected Result:**
- Step 3: the hint text reads (in full): "Every index/benchmark/macro line on the major-indexes chart,
  with its honest data vendor and real first-bar date — the same GET /api/indexes payload the Dashboard
  chart reads, never a recompute."
- Step 4: the table has exactly 10 data rows, in the order listed in the Reference table above.
- Step 5: that row's Vendor column shows a badge reading `Stooq`; its First bar column shows `1996-01-02`.
- Step 6: that row's Vendor column shows a badge reading `FRED-macro proxy`; its First bar column shows
  `2021-01-04`.

---

### UT-08 — Chart legend/tooltip show no vendor tag for the 5 original ETF lines (validation — honest omission)

**Type:** validation
**Priority:** P2
**Surface:** `/` — "Regime × phase cross-view" chart legend + tooltip

**Preconditions:**
- UT-04 and UT-05 passed.

**Steps:**
1. Navigate to `http://localhost:3255`.
2. In the legend, read the entries for `S&P 500 (SPY)`, `Nasdaq 100 (QQQ)`, `Russell 2000 (IWM)`,
   `S&P 500 Equal-Weight (RSP)`, `Dow 30 (DIA)`.
3. Hover the chart and read the tooltip rows for symbols `SPY`, `QQQ`, `IWM`, `RSP`, `DIA`.

**Expected Result:**
- None of the 5 legend entries has any parenthetical text after its name (no `(Stooq)`, no `(null)`, no
  `(undefined)`, no empty `()`  — nothing at all).
- None of the 5 tooltip rows has a `·`-prefixed suffix (no `· null`, no stray dot, nothing at all after the
  `%` value).

---

### UT-09 — `/data` panel: ETF rows show an honest "—" vendor (but a real First-bar date); the FRED-macro-proxy row reads honestly as a proxy (validation)

**Type:** validation
**Priority:** P2
**Surface:** `/data` — "Index & benchmark data provenance" panel

**Preconditions:**
- UT-07 passed.

**Steps:**
1. Navigate to `http://localhost:3255/data` and scroll to the "Index & benchmark data provenance" table.
2. Locate the row for `S&P 500 (SPY)`. Read both its Vendor and First bar cells.
3. Locate the row for `Nasdaq 100 (QQQ)`. Read both its Vendor and First bar cells.
4. Locate the row for `10Y-2Y spread proxy (^TNX)`. Read its Series name and Vendor cell.

**Expected Result:**
- Step 2: Vendor cell shows a badge reading exactly `—` (a single em dash, not blank, not "null", not
  "undefined"). First bar cell shows `2005-02-25` (a real date — **not** a dash; see the Correction note
  above this table).
- Step 3: Vendor cell shows `—`; First bar cell shows `1999-03-10`.
- Step 4: the Series name itself reads `10Y-2Y spread proxy (^TNX)` — it says "proxy" and "spread," never
  a bare `^TNX` or any text implying it is the literal, real-time 10-year Treasury yield. The Vendor badge
  reads `FRED-macro proxy`, not "FRED" alone and not "Yahoo"/"Stooq".

---

### UT-10 — `/data` shows one honest "Backend unavailable" message when the whole backend is down (error)

**Type:** error
**Priority:** P2
**Surface:** `/data`

**Preconditions:**
- `/data` loads normally first (UT-02 passed), so you can compare before/after.
- You have a way to stop the backend process (e.g., the terminal running it, or
  `fuser -k 8255/tcp` / `lsof -ti:8255 | xargs kill` from a terminal) and restart it afterward
  (`./scripts/dev.sh` or equivalent).

**Steps:**
1. Confirm `http://localhost:3255/data` currently loads normally with all panels visible.
2. Stop the backend service (leave the frontend running).
3. Reload the page (F5) at `http://localhost:3255/data`.
4. Restart the backend, then reload the page once more.

**Expected Result:**
- Step 3: the page shows the "Data Manager" heading, then **one** red-bordered card with the bold text
  "Backend unavailable" and the message "Dataset coverage could not load from the API. No figures are
  shown rather than fabricated values. Confirm the backend is running and retry." **No other panel
  renders below it** — not "Dataset coverage", not "Macro feed", not the new "Index & benchmark data
  provenance" panel. This is expected, correct behavior (the whole page shares one gating fetch), not a
  defect specific to the new panel — see Correction #2 above.
- No blank white page, no unstyled crash/stack-trace page, no partially-fabricated table.
- Step 4: after restarting the backend, the page returns to the normal UT-02 state (all panels, including
  the new one, render with real data again).

---

### UT-11 — Provenance panel's own isolated "Vendor disclosure unavailable" message when only its endpoint fails (error, automation-only)

**Type:** error
**Priority:** P3 — requires Chrome DevTools Protocol network-request blocking; not achievable by a human
clicking alone. Intended for the browser-qa-agent's automated run, not a manual operator. Skip this case
if no request-blocking capability is available; UT-10 already covers the human-executable error path.

**Surface:** `/data` — "Index & benchmark data provenance" panel

**Preconditions:**
- Backend and frontend both running normally (UT-02 passing).
- Tooling that can block only requests matching `*/api/indexes*` while leaving `/api/data` and other
  endpoints unaffected (e.g. Chrome DevTools Protocol `Network.setBlockedURLs` or Fetch-domain
  interception).

**Steps:**
1. With `/data` not yet loaded, enable network blocking for the URL pattern `*/api/indexes*`.
2. Navigate to `http://localhost:3255/data`.
3. Confirm the "Dataset coverage", "Macro feed", and other pre-existing panels still render with real
   data (they use `/api/data`, unaffected by the block).
4. Scroll to where the "Index & benchmark data provenance" panel appears.
5. Remove the network block and reload the page.

**Expected Result:**
- Step 3: rest of the page is fully normal — this is the key difference from UT-10.
- Step 4: only the provenance panel shows a warning-toned box with an alert-triangle icon, the bold text
  "Vendor disclosure unavailable", and the message "Could not load the index series from the API. Nothing
  is fabricated — confirm the backend is running and reload."
- Step 5: after removing the block and reloading, the panel recovers to the normal UT-07 table.

---

### UT-12 — Provenance panel shows a loading skeleton before data resolves (ux / smoke, best-effort)

**Type:** ux
**Priority:** P3 — this state is typically visible for well under a second on a local network; treat a
missed observation as inconclusive, not a failure, unless network throttling is available.

**Surface:** `/data` — "Index & benchmark data provenance" panel

**Preconditions:**
- Ability to throttle the network (e.g. DevTools "Slow 3G") is helpful but optional.

**Steps:**
1. If available, enable network throttling (e.g. "Slow 3G") in the browser.
2. Navigate to `http://localhost:3255/data`.
3. Watch the area where the "Index & benchmark data provenance" panel will appear, immediately after the
   page starts loading.

**Expected Result:**
- Briefly, a solid gray pulsing rectangular block (no readable text) appears in place of the table, then
  is replaced by the real table once data arrives.
- No layout jump/flash of unstyled content, no error flash before the real content.

---

### UT-13 — Regression: the 5 pre-existing ETF lines and legend entries are unchanged (regression)

**Type:** regression
**Priority:** P1 *(elevated from the skill's default P3 — anti-goal #3 in this iteration's DoD explicitly
requires the existing SPY/QQQ/IWM/RSP/DIA lines to be byte-identical; a visible change here is a hard DoD
failure, not merely informational)*
**Surface:** `/` — "Regime × phase cross-view" card

**Preconditions:**
- UT-04 passed (all 10 legend entries visible).
- Ideally, a screenshot of this same chart/legend from a prior iteration (iter-21 or earlier) is available
  for side-by-side comparison; if not available, judge via the criteria below.

**Steps:**
1. Navigate to `http://localhost:3255`.
2. Confirm all 5 original entries — `S&P 500 (SPY)`, `Nasdaq 100 (QQQ)`, `Russell 2000 (IWM)`,
   `S&P 500 Equal-Weight (RSP)`, `Dow 30 (DIA)` — are still present in the legend, in that relative order,
   each with no vendor tag.
3. Hover over the chart on a recent date (e.g., within the last month) and confirm each of the 5 ETF
   symbols shows a `%` value in the tooltip.
4. Zoom/scroll the chart to a recent 3-month window and confirm the 5 ETF lines still move and look the
   same relative shape as before (no visual distortion, no missing segments).

**Expected Result:**
- All 5 original lines/legend entries are present, unchanged in name, order, and (per UT-06) original
  color assignment (SPY=teal/`--accent`, QQQ=green/`--pos`, IWM=amber/`--warn`, RSP=red/`--neg`,
  DIA=gray/`--text-muted`).
- No existing chart control (zoom, drag-to-pan, hover) behaves differently than before.

---

### UT-14 — Regression: `/stocks` leaderboard shows no leaked index/macro symbol rows (J-01)

**Type:** regression
**Priority:** P1 *(required-still-passing per DoD)*
**Surface:** `/stocks`

**Preconditions:**
- None beyond global preconditions.

**Steps:**
1. Click "Stocks" in the left sidebar (or navigate directly to `http://localhost:3255/stocks`).
2. Wait for the leaderboard table to load.
3. Scan every row's ticker/symbol cell (leftmost columns).

**Expected Result:**
- The "Stocks" heading and subtitle "Stock Leaderboard — ranked by Leadership, with independent Entry
  Quality and Risk (danger) scores, a setup status and a reason" are visible.
- The table renders normally with real tickers (e.g. common equity symbols), no crash, no blank page.
- **No row's symbol is** `^SPX`, `^NDX`, `^DJI`, `^VIX`, or `^TNX` — the deep index/macro symbols never
  leak into the scored universe/leaderboard (they were deliberately kept out of `etfs.index`).

---

### UT-15 — Regression: Dashboard "Market Regime" card + evidence link intact after the chart gains lines (J-04)

**Type:** regression
**Priority:** P1 *(required-still-passing per DoD)*
**Surface:** `/`

**Preconditions:**
- None beyond global preconditions.

**Steps:**
1. Navigate to `http://localhost:3255`.
2. Locate the "Market Regime" card (top-left of the two-column summary row, above the cross-view chart).
3. Note the badge value shown next to the "Market Regime" title (a regime label, e.g. "Risk-On" or
   similar — the exact current value is not being tested here, only that it renders).
4. Click the link reading exactly "See evidence proven in this regime →" inside that card.
5. Also confirm the adjacent "Market Phase & Severity" card (top-right) still renders its own badge/score.

**Expected Result:**
- Step 3: a non-empty badge and a numeric score out of 100 are visible; no crash.
- Step 4: the browser navigates to `http://localhost:3255/evidence`, which loads the "Evidence" heading
  without error.
- Step 5: "Market Phase & Severity" shows its own badge + score, unaffected by the chart below it gaining
  5 new lines.

---

### UT-16 — Regression: `/data` "Universe" count is unchanged and matches `/stocks`' count (J-12)

**Type:** regression
**Priority:** P1 *(required-still-passing per DoD)*
**Surface:** `/data`, `/stocks`

**Preconditions:**
- None beyond global preconditions.

**Steps:**
1. Navigate to `http://localhost:3255/data`.
2. In the "Dataset coverage" panel, read the "Universe (as of date)" figure's value (a plain number).
3. Navigate to `http://localhost:3255/stocks`.
4. Count (or use any on-page total, if shown) the number of rows in the leaderboard table.

**Expected Result:**
- The "Universe (as of date)" number from step 2 is a plain integer, not visibly inflated by 3–5 compared
  to what you'd expect (the deep index/macro symbols must not have widened the scored universe count).
- The leaderboard row count in step 4 is consistent with (not larger because of this iteration's change
  than) the universe figure from step 2 — this iteration adds 0 to both counts.

---

### UT-17 — Regression: `/stocks/{ticker}` deep-history chart + Recent/Full history toggle still works (J-10)

**Type:** regression
**Priority:** P2 *(required-still-passing per DoD, but lower urgency than the Dashboard/`/data` surfaces
this iteration actually touched)*
**Surface:** `/stocks/{ticker}`

**Preconditions:**
- At least one ticker row exists on `/stocks` to click into.

**Steps:**
1. Navigate to `http://localhost:3255/stocks`.
2. Click any ticker's row/symbol link to open its detail page (`/stocks/<TICKER>`).
3. Locate the price chart and the two-button toggle labeled "Recent" / "Full history" near it.
4. Click "Full history".
5. Click "Recent" again.

**Expected Result:**
- The stock detail page loads with a candlestick/price chart and no crash.
- Clicking "Full history" visibly widens the plotted date range (older bars appear); clicking "Recent"
  narrows it back — both remain smooth, no error state introduced by this iteration's unrelated backend
  change (widening `daily_prices` with 3 new symbols must not affect a per-ticker query).

---

### UT-18 — Regression: `/evidence` ledger still reads "Not yet proven" only; no new "Proven" claim leaked (J-03/J-05)

**Type:** regression
**Priority:** P1 *(required-still-passing per DoD; also a direct anti-goal check — a score must never be
presented as proven without a passing certified-claim entry)*
**Surface:** `/evidence`

**Preconditions:**
- None beyond global preconditions.

**Steps:**
1. Navigate to `http://localhost:3255/evidence`.
2. Read the subtitle under the "Evidence" heading.
3. Scan the list/table of claims for their status badges.

**Expected Result:**
- Subtitle reads: "The certified-claims ledger — the single source of proven-ness. A signal reads
  "Proven" ONLY when a referee-certified, out-of-sample, control-beating claim backs it; everything else
  honestly reads "Not yet proven."" (unchanged by this iteration).
- Every claim status still honestly reads "Not yet proven" (both 30-year ledgers are all-FAIL per this
  iteration's own spec — this iteration adds no `## Evidence Claim` and does not touch the referee). If any
  row unexpectedly reads "Proven," that is a serious regression to escalate immediately, not a minor note.

---

### UT-19 — UX: the new provenance panel is discoverable within 2 clicks from home, with a clear title (ux)

**Type:** ux
**Priority:** P2
**Surface:** `/` → `/data`

**Preconditions:**
- None beyond global preconditions.

**Steps:**
1. Navigate to `http://localhost:3255` (home/Dashboard) — this is click 0.
2. Click "Data Manager" in the left sidebar — click 1.
3. Scroll down the resulting `/data` page — no further click needed to reach the new panel, just scrolling.
4. Read the new card's title and the one-line hint text beneath it, without any outside explanation.

**Expected Result:**
- The new panel is reached in exactly 1 click from the Dashboard (well within the blueprint's ≤2-click
  requirement), via the existing "Data Manager" nav item — no new nav item was added or needed.
- The card's title, "Index & benchmark data provenance," combined with its hint text (quoted in UT-07),
  is self-explanatory: a first-time reader can tell without external help that this table shows where each
  chart line's data comes from and how far back it truly goes — it does not require a manual/wiki lookup
  to understand what the table means.

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | Dashboard loads, chart renders | smoke | P1 | `/` |
| UT-02 | `/data` loads with new panel present | smoke | P1 | `/data` |
| UT-03 | Deep lines extend to 1996 | happy-path | P1 | `/` |
| UT-04 | Legend shows vendor labels (3 categories) | happy-path | P1 | `/` |
| UT-05 | Tooltip shows vendor suffix | happy-path | P1 | `/` |
| UT-06 | 10 legend colors all distinct | happy-path | P1 | `/` |
| UT-07 | `/data` panel lists 10 series correctly | happy-path | P1 | `/data` |
| UT-08 | ETF lines show no vendor tag (chart) | validation | P2 | `/` |
| UT-09 | ETF/proxy rows read honestly (`/data`) | validation | P2 | `/data` |
| UT-10 | Whole-backend-down error is honest | error | P2 | `/data` |
| UT-11 | Isolated panel error (automation-only) | error | P3 | `/data` |
| UT-12 | Loading skeleton (best-effort) | ux | P3 | `/data` |
| UT-13 | Existing ETF lines unchanged | regression | P1 | `/` |
| UT-14 | `/stocks` — no leaked index rows (J-01) | regression | P1 | `/stocks` |
| UT-15 | Market Regime + evidence link intact (J-04) | regression | P1 | `/` |
| UT-16 | Universe count unchanged (J-12) | regression | P1 | `/data`, `/stocks` |
| UT-17 | Ticker detail chart + toggle (J-10) | regression | P2 | `/stocks/{ticker}` |
| UT-18 | Evidence ledger unaffected (J-03/J-05) | regression | P1 | `/evidence` |
| UT-19 | New panel discoverable in ≤2 clicks | ux | P2 | `/` → `/data` |

**P1 tests must all pass for browser QA verdict to be PASS.** UT-11 and UT-12 are best-effort/automation
-only and should not block a PASS verdict on their own if the tooling to execute them is unavailable.
