# Phase goal-mcp-loop-iter-23 — UI Test Plan

**Phase:** goal-mcp-loop-iter-23
**Date:** 2026-07-08
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3255
**Backend URL:** http://localhost:8255

---

## Scope

**This is a zero-application-diff, verification-only iteration.** `git diff HEAD` touches exactly one
file in the whole repo — `runs/goal-session-mcp-loop/journey-scripts/J-13.json` (a QA fixture, not
application code) — confirmed independently by the developer, the reviewer, and the ui-impact-analyst.
Every test case below re-exercises a surface that was already fully built in iter-22; nothing new is
being introduced. Per `runs/goal-mcp-loop-iter-23/plan.md`, this plan mirrors the structure of
`reports/phase-goal-mcp-loop-iter-22-ui-test-plan.md` (its 19 cases, UT-01..UT-19) — since the only code
delta since then is the one-line `minBarSpacing: 0.02` chart fix — **plus new cases dedicated to the J-13
availability-heatmap replay** (the gap iter-22 left open; last dedicated pixel-level replay was iter-21),
**plus a case for the one permitted fixture refresh** (587→590 symbols).

Per the iter-21 lesson embedded in this iteration's own phase spec — **"grade a required-still-passing
replay against the journey's own golden script (`journey-scripts/J-XX.json`), not test-plan wording"** —
every regression case below (J-01/J-03/J-04/J-05/J-10/J-11/J-12) quotes the literal `expect.text` strings
from that journey's actual golden-script file, read directly from
`runs/goal-session-mcp-loop/journey-scripts/` on 2026-07-08 for this plan, not paraphrased or guessed.

The two live-reachable surfaces J-14 touches (unchanged since iter-22, being re-verified here):
1. **Dashboard (`/`) → "Regime × phase cross-view" card** — 10 lines total (5 ETFs + `^SPX`/`^NDX`/`^DJI`/
   `^VIX`/`^TNX`), each index/macro line carrying a vendor label in the legend + hover tooltip.
2. **`/data` → "Index & benchmark data provenance" panel** — a table disclosing each series' vendor and
   true first-bar date, directly below the existing "Macro feed" panel.

Plus the J-13 surface being dedicated-replayed this iteration:
3. **`/data` → "Per-date availability" heatmap** — two-group legend, monotonic density ramp, violet
   snapshot ring (component source: `apps/frontend/components/availability-heatmap.tsx`).

## Global Preconditions (apply to every test case unless overridden)

- Prod-mode services running per the iter-20/21/22 harness-discipline lesson: `rm -rf apps/frontend/.next`
  was run before starting the frontend; backend reachable at `http://localhost:8255`, frontend at
  `http://localhost:3255`. Confirm both return HTTP 200 before starting.
- The local database already has the deep symbols loaded (iter-22's additive backfill): `^SPX`/`^NDX`/
  `^DJI`/`^VIX` each have bars from `1996-01-02`; total distinct symbols with stored bars = **590** (this
  is the exact figure the one permitted fixture edit this iteration made was refreshed to match — see
  UT-11). Do not re-run any load/backfill script — it is already done.
- No login is required anywhere in this app (no auth system; confirmed no session/auth code in
  `app/layout.tsx` or `middleware.ts`).
- Browser has no prior `localStorage` override that hides the cross-view card (see UT-01 precondition).

## Key numbers — do not confuse these three

| Figure | Value | Where it renders | What it counts |
|--------|-------|-------------------|-----------------|
| Chart/vendor-panel index lines | **10** | Dashboard chart legend; `/data` provenance table rows | The configured benchmark/macro overlay lines only (5 ETFs + `^SPX`/`^NDX`/`^DJI`/`^VIX`/`^TNX`) |
| Total stored symbols | **590** | Header badge "590 symbols" (every page, top-right); also `/data`'s "Symbols" stat and the availability heatmap's footer caption "total stored symbols (590)" | Every ticker with any stored price bar — equities + ETFs + indices + macro proxies |
| Scored universe | **541** | `/stocks` toolbar "541 / 541"; `/data`'s "Universe (as of date)" stat | The point-in-time SCORED equity universe only (excludes ETFs/indices/macro) |

## Reference: exact expected values for the 10 chart/vendor-panel lines

Unchanged since iter-22 (re-confirmed by direct source read on 2026-07-08 against
`apps/frontend/components/phase-cross-view-chart.tsx` and `apps/frontend/components/index-vendor-panel.tsx`
— code is byte-identical to iter-22, per the zero-diff confirmation above). Row order is both the chart's
legend order and the `/data` panel's table order.

| # | Symbol | Display name (chart legend / `/data` "Series") | Vendor badge | First bar |
|---|--------|--------------------------------------------------|--------------|-----------|
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

Legend format (from source): `{name}{vendor ? " (" + vendor + ")" : ""}` → e.g. `S&P 500 Index (^SPX) (Stooq)`.
Tooltip format: `{symbol}{vendor ? " · " + vendor : ""}` → e.g. `^SPX · Stooq`.

---

## Test Cases

### UT-01 — Dashboard loads and the cross-view chart renders (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Global preconditions above.
- Fresh browser profile, or `localStorage` key `trendora.dashboard.phaseCrossView` not set to hidden (if a
  prior session clicked "Hide", the card starts collapsed — see step 3).

**Steps:**
1. Navigate to `http://localhost:3255`.
2. Wait for the page to finish loading.
3. If a dashed button reading "Show regime × phase cross-view" is visible instead of a chart, click it.

**Expected Result:**
- The heading "Dashboard" is visible at the top.
- The top-right header shows a green "Ready" badge (not a red "Backend unavailable" badge).
- A card titled "Regime × phase cross-view" is visible, containing a rendered chart (not a blank area, not
  a spinner stuck for more than a couple of seconds).
- No browser console errors.

---

### UT-02 — `/data` loads with all existing panels plus the provenance panel (smoke)

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
- In this top-to-bottom order, all of the following panels render with real data (not blank, not a
  permanent skeleton): "Dataset coverage", "Rebuild snapshots for current universe", "Universe resolution
  as of … (latest)", "Dynamic-universe membership timeline", "Per-date availability", a missing-data
  diagnostic panel, "Macro feed", and — directly after "Macro feed" — a card titled **"Index & benchmark
  data provenance"** containing a table.

---

### UT-03 — Deep `^SPX`/`^NDX`/`^DJI`/`^VIX` lines extend to 1996 in the DEFAULT chart view — the J-14 flip case (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/` — "Regime × phase cross-view" card

**Preconditions:**
- UT-01 passed (chart rendered).
- **This is the exact case that FAILed in iter-22's stale QA report** (x-axis floored at ~2018) before the
  `minBarSpacing: 0.02` fix; it must now flip to PASS with zero manual zoom/pan.

**Steps:**
1. Navigate to `http://localhost:3255` and confirm the "Regime × phase cross-view" chart is visible. Do
   NOT zoom, drag, or pan — this case tests the chart's default/initial rendered state only.
2. Look at the overall shape of the chart: most of the 10 colored lines should visibly start partway
   across the chart (around the left third, roughly where 2005 falls in a 1996–2026 span) — the 5
   pre-existing ETF lines starting late. A smaller number of lines should extend all the way to the
   chart's left edge.
3. Move the mouse to hover the very left edge of the chart's plotted area (leftmost ~2–5% of its width).
4. Read the tooltip box in the upper-right of the chart.
5. Capture a full-page or element-clip screenshot of the chart (never a scrolled/cropped viewport that
   could hide the left edge).

**Expected Result:**
- Step 2: a visible "starting gap" — several lines have no path across the left ~30% of the chart, while a
  few lines run the full width. This confirms the chart's leftmost visible date is on or before
  `1997-12-31` (not ~2018, the pre-fix symptom) **without any manual zoom or pan**.
- Step 4: the tooltip's date reads a day at or near `1996-01-02`. Its series list includes `^SPX`, `^NDX`,
  `^DJI`, and `^VIX` (each with a `%` value and a `· Stooq`/`· Yahoo` suffix) — and does **not** include
  `SPY`, `QQQ`, `IWM`, `RSP`, `DIA`, or `^TNX` (honestly absent this early, never shown as 0% or a
  fabricated flat line).
- Step 5: the captured image must show the `^SPX` line pixels actually in-frame at the left edge — a PASS
  label or a DOM-text legend line alone is not sufficient evidence (lesson from iter-3/11/13/14: screenshots
  from different states must be md5-distinct, and the deep line must be visibly present in the captured
  pixels, not just referenced in text).

---

### UT-04 — Chart legend shows vendor labels spanning all three vendor categories (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/` — "Regime × phase cross-view" card legend

**Preconditions:**
- UT-01 passed.

**Steps:**
1. Navigate to `http://localhost:3255`.
2. Scroll to the legend row directly below the chart (a horizontal wrapped list of colored-dot + label
   entries, above the "Phase pane:" row).
3. Count the entries and read each one's text.

**Expected Result:**
- The legend lists exactly **10** entries, in this order: `S&P 500 (SPY)`, `Nasdaq 100 (QQQ)`,
  `Russell 2000 (IWM)`, `S&P 500 Equal-Weight (RSP)`, `Dow 30 (DIA)`, `S&P 500 Index (^SPX) (Stooq)`,
  `Nasdaq 100 Index (^NDX) (Stooq)`, `Dow Jones Industrial Average (^DJI) (Stooq)`,
  `CBOE Volatility Index (^VIX) (Yahoo)`, `10Y-2Y spread proxy (^TNX) (FRED-macro proxy)`.
- The vendor tag reads exactly `Stooq`, `Yahoo`, or `FRED-macro proxy` in a lighter/faint gray tone in
  parentheses immediately after the name — confirmed present for at least one entry from each category.
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
2. Move the mouse over the chart's plotted area near the right-hand (recent) side, where all 10 lines have
   data.
3. Read the tooltip box's list of series values.

**Expected Result:**
- The tooltip shows the hovered date, then one row per visible series, formatted as the raw symbol (e.g.
  `^SPX`) followed by its `%` value.
- For `^SPX`, `^NDX`, `^DJI` rows: a lighter-gray `· Stooq` suffix appears right after the symbol (e.g.
  `^SPX · Stooq`). For `^VIX`: `· Yahoo`. For `^TNX`: `· FRED-macro proxy`.
- For `SPY`, `QQQ`, `IWM`, `RSP`, `DIA` rows: no `·` suffix at all — just the bare symbol and its `%` value.

---

### UT-06 — All 10 legend color swatches are visually distinct; no repeated color (happy path — prior-bug regression)

**Type:** happy-path
**Priority:** P1
**Surface:** `/` — "Regime × phase cross-view" card legend

**Preconditions:**
- UT-04 passed (10 legend entries confirmed present).

**Steps:**
1. Navigate to `http://localhost:3255` and locate the 10-entry legend.
2. Zoom in on (or screenshot) the small colored dots to the left of each of the 10 labels.
3. Compare the dot next to entry 1 (`S&P 500 (SPY)`) against the dot next to entry 6
   (`S&P 500 Index (^SPX) (Stooq)`) specifically — the exact pair a since-fixed palette bug rendered
   identically (the old 5-color palette wrapped every 5th line back to the 1st color).
4. Visually scan all 10 dots against each other.

**Expected Result:**
- Entry 1's dot and entry 6's dot are clearly different colors — they must NOT look like the same swatch.
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
3. Read the hint text under the title.
4. Read the table (3 columns: "Series", "Vendor", "First bar").
5. Locate the row whose Series column reads `S&P 500 Index (^SPX)`.
6. Locate the row whose Series column reads `10Y-2Y spread proxy (^TNX)`.

**Expected Result:**
- Step 3: hint text reads (in full): "Every index/benchmark/macro line on the major-indexes chart, with
  its honest data vendor and real first-bar date — the same GET /api/indexes payload the Dashboard chart
  reads, never a recompute."
- Step 4: the table has exactly 10 data rows, in the order in the Reference table above.
- Step 5: Vendor column shows badge `Stooq`; First bar column shows `1996-01-02`.
- Step 6: Vendor column shows badge `FRED-macro proxy`; First bar column shows `2021-01-04`.

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
  `(undefined)`, no empty `()`).
- None of the 5 tooltip rows has a `·`-prefixed suffix (no `· null`, no stray dot, nothing after the `%`
  value).

---

### UT-09 — `/data` panel: ETF rows show honest "—" vendor with a real First-bar date; the FRED-macro-proxy row reads honestly (validation)

**Type:** validation
**Priority:** P2
**Surface:** `/data` — "Index & benchmark data provenance" panel

**Preconditions:**
- UT-07 passed.

**Steps:**
1. Navigate to `http://localhost:3255/data` and scroll to the provenance table.
2. Locate the row for `S&P 500 (SPY)`. Read both its Vendor and First bar cells.
3. Locate the row for `Nasdaq 100 (QQQ)`. Read both its Vendor and First bar cells.
4. Locate the row for `10Y-2Y spread proxy (^TNX)`. Read its Series name and Vendor cell.

**Expected Result:**
- Step 2: Vendor cell shows exactly `—` (a single em dash — not blank, not "null", not "undefined"). First
  bar cell shows `2005-02-25` (a real date, not a dash — first is read from the manifest for every series
  regardless of whether it has a vendor key).
- Step 3: Vendor cell shows `—`; First bar cell shows `1999-03-10`.
- Step 4: Series name reads `10Y-2Y spread proxy (^TNX)` — says "proxy" and "spread," never implying it is
  the literal real-time 10-year Treasury yield. Vendor badge reads `FRED-macro proxy`, not "FRED" alone and
  not "Yahoo"/"Stooq".

---

### UT-10 — J-13 dedicated replay: two-group legend, density ramp, snapshot ring, md5-distinct hover-tooltip pair (happy path)

**Type:** happy-path
**Priority:** P1 *(DoD-required dedicated J-13 replay — last dedicated pixel-level check was iter-21)*
**Surface:** `/data` — "Per-date availability" heatmap

**Preconditions:**
- UT-02 passed (`/data` loads).
- The heatmap has at least one fully-covered cell with no snapshot ring and at least one fully-covered
  cell with a snapshot ring (true of the current dataset — recent trading days have both price bars and a
  scored snapshot; the very latest 0–3 trading days may have bars but no snapshot yet, a normal Backfill
  lag).

**Steps:**
1. Navigate to `http://localhost:3255/data` and scroll to the "Per-date availability" card.
2. Read the legend directly under the card's hint text. It has two rows.
3. Read the first legend row's group label (leftmost bold uppercase text) and its 6 swatches.
4. Read the second legend row's group label and its single sample swatch.
5. In the calendar grid below, find a filled-in day cell whose color is the brightest/fullest shade (100%
   coverage) but has **no** ring around it — hover over it and read the readout text that appears (either
   in the top-right "hover readout" area, or the cell's native tooltip).
6. Find a second filled-in day cell that is also the brightest/fullest shade but **does** have a
   colored ring around its border — hover over it and read its readout text.
7. Compare the two readout texts from steps 5 and 6.

**Expected Result:**
- Step 3: the first group's label reads exactly "Price data — cell fill", with 6 swatches running from a
  very dark/empty shade to a bright shade, all the same hue family (blue) — the brightest ("full") swatch
  is **not amber/orange**.
- Step 4: the second group's label reads exactly "Scored snapshot — indicator", shown as a small square
  with a distinct **violet/purple ring** around it (not green).
- Step 5: the readout text reads in the form `<date> · <N>/<total> symbols · snapshot no` (the "snapshot
  no" portion in a faint gray tone) — confirming a "Backfill gap" day (fully fetched, not yet scored).
- Step 6: the readout text reads `<date> · <N>/<total> symbols · snapshot yes` (the "snapshot yes" portion
  in a violet tone).
- Step 7: the two readout strings are **visually and textually distinct** (different date, and one ends
  "snapshot no" while the other ends "snapshot yes") — capture both as separate, md5-distinct screenshots;
  identical screenshots for both hover states is a FAIL (a PASS label alone is not proof, per the
  iter-3/11/13/14 evidence lesson applied here to J-13).
- The card's footer caption (below the calendar grid) reads, in part: "...total stored symbols (590),
  filled by Fetch..." — confirming the pool denominator matches the current 590-symbol count (see UT-11).

---

### UT-11 — Header badge shows the correct total-symbol count "590 symbols" (regression / fixture-accuracy check)

**Type:** regression
**Priority:** P2
**Surface:** global header (visible on every page)

**Preconditions:**
- Global preconditions above. This case directly verifies the ONE application-adjacent change this
  iteration made: `runs/goal-session-mcp-loop/journey-scripts/J-13.json`'s expected-text assertion was
  refreshed from `"587 symbols"` to `"590 symbols"` to track iter-22's additive load of `^SPX`/`^NDX`/`^DJI`.
  This case confirms the LIVE app actually renders the number the fixture now expects.

**Steps:**
1. Navigate to `http://localhost:3255/data` (or any page — this badge is in the shared header, not
   specific to `/data`).
2. Look at the top-right of the page header, next to the green "Ready" pill.
3. Read the small badges in that row: a "provider: …" badge, a "seed …" badge, and a "… symbols" badge.

**Expected Result:**
- The last badge in that row reads exactly `590 symbols` (not `587 symbols`, and not any other number).
- This confirms the golden-script fixture refresh (587→590) matches the live, currently-served data — if
  this badge shows a number other than 590, that is a real backend data-state problem (the refreshed
  fixture would then be WRONG, not the app), not a caching artifact.

---

### UT-12 — `/data` shows one honest "Backend unavailable" message when the whole backend is down (error)

**Type:** error
**Priority:** P2
**Surface:** `/data` and global header

**Preconditions:**
- `/data` loads normally first (UT-02 passed), so you can compare before/after.
- You have a way to stop the backend process (e.g., `lsof -ti:8255 | xargs kill`) and restart it afterward
  (`scripts/start-backend.sh` or equivalent).

**Steps:**
1. Confirm `http://localhost:3255/data` currently loads normally with all panels visible.
2. Stop the backend service (leave the frontend running).
3. Reload the page (F5) at `http://localhost:3255/data`.
4. Look at the top-right header badge area.
5. Restart the backend, then reload the page once more.

**Expected Result:**
- Step 3: the page shows the "Data Manager" heading, then **one** red-bordered card with the bold text
  "Backend unavailable" and the message "Dataset coverage could not load from the API. No figures are
  shown rather than fabricated values. Confirm the backend is running and retry." No other panel renders
  below it (this is expected — the whole page shares one gating fetch, not a defect).
- Step 4: the header's readiness pill turns red and reads "Backend unavailable" (the `provider:`/`seed`/
  `symbols` badges disappear rather than showing stale or fabricated values).
- No blank white page, no unstyled crash/stack-trace page, no partially-fabricated table.
- Step 5: after restarting the backend, the page returns to the normal UT-02 state and the header shows
  "Ready" + "590 symbols" again.

---

### UT-13 — Provenance panel's own isolated "Vendor disclosure unavailable" message when only its endpoint fails (error, automation-only)

**Type:** error
**Priority:** P3 — requires network-request blocking (e.g. Chrome DevTools Protocol); not achievable by a
human clicking alone. Intended for the browser-qa-agent's automated run; skip if no request-blocking
capability is available — UT-12 already covers the human-executable error path.

**Surface:** `/data` — "Index & benchmark data provenance" panel

**Preconditions:**
- Backend and frontend both running normally (UT-02 passing).
- Tooling that can block only requests matching `*/api/indexes*` while leaving other endpoints unaffected.

**Steps:**
1. With `/data` not yet loaded, enable network blocking for the URL pattern `*/api/indexes*`.
2. Navigate to `http://localhost:3255/data`.
3. Confirm "Dataset coverage", "Macro feed", and other pre-existing panels still render with real data.
4. Scroll to where the "Index & benchmark data provenance" panel appears.
5. Remove the network block and reload the page.

**Expected Result:**
- Step 3: rest of the page is fully normal — this is the key difference from UT-12.
- Step 4: only the provenance panel shows a warning-toned box with an alert-triangle icon, the bold text
  "Vendor disclosure unavailable", and the message "Could not load the index series from the API. Nothing
  is fabricated — confirm the backend is running and reload."
- Step 5: after removing the block and reloading, the panel recovers to the normal UT-07 table.

---

### UT-14 — Provenance panel shows a loading skeleton before data resolves (ux / smoke, best-effort)

**Type:** ux
**Priority:** P3 — typically visible for well under a second on a local network; treat a missed
observation as inconclusive, not a failure, unless network throttling is available.

**Surface:** `/data` — "Index & benchmark data provenance" panel

**Preconditions:**
- Ability to throttle the network (e.g. DevTools "Slow 3G") is helpful but optional.

**Steps:**
1. If available, enable network throttling in the browser.
2. Navigate to `http://localhost:3255/data`.
3. Watch the area where the provenance panel will appear, immediately after the page starts loading.

**Expected Result:**
- Briefly, a solid gray pulsing rectangular block (no readable text) appears in place of the table, then
  is replaced by the real table once data arrives.
- No layout jump/flash of unstyled content, no error flash before the real content.

---

### UT-15 — Regression: the 5 pre-existing ETF lines and legend entries are unchanged (regression)

**Type:** regression
**Priority:** P1 *(anti-goal #8 in this iteration's DoD explicitly requires the existing SPY/QQQ/IWM/RSP/
DIA lines to be byte-identical to pre-iter-22 — a visible change here is a hard failure, not informational)*
**Surface:** `/` — "Regime × phase cross-view" card

**Preconditions:**
- UT-04 passed (all 10 legend entries visible).

**Steps:**
1. Navigate to `http://localhost:3255`.
2. Confirm all 5 original entries — `S&P 500 (SPY)`, `Nasdaq 100 (QQQ)`, `Russell 2000 (IWM)`,
   `S&P 500 Equal-Weight (RSP)`, `Dow 30 (DIA)` — are still present, in that relative order, each with no
   vendor tag.
3. Hover over the chart on a recent date (within the last month) and confirm each of the 5 ETF symbols
   shows a `%` value in the tooltip.

**Expected Result:**
- All 5 original lines/legend entries are present, unchanged in name, order, and color assignment
  (SPY=teal/`--accent`, QQQ=green/`--pos`, IWM=amber/`--warn`, RSP=red/`--neg`, DIA=gray/`--text-muted`).
- No existing chart control (zoom, drag-to-pan, hover) behaves differently than before.

---

### UT-16 — Required-still-passing J-01: `/stocks` leaderboard — 541/541, zero leaked index carets, sort + evidence nav (regression)

**Type:** regression
**Priority:** P1 *(required-still-passing per DoD; graded against the actual golden script
`journey-scripts/J-01.json`, read verbatim on 2026-07-08)*
**Surface:** `/stocks`

**Preconditions:**
- None beyond global preconditions.

**Steps:**
1. Navigate to `http://localhost:3255/stocks`.
2. Wait for the leaderboard table to load. Confirm the text "Stock Leaderboard" is visible (part of the
   page subtitle).
3. Scan every row's ticker/symbol cell; confirm every score cell shows an evidence badge reading
   "Not yet proven".
4. In the filter toolbar directly above the table (right end, after the Sector/Setup/Pattern/Theme
   dropdowns), read the count text.
5. Click the "Sector" column header (a sortable column; clicking it re-sorts the table by sector).
6. After the re-sort, scan the Sector column for any row showing "Unassigned".
7. Click "Evidence" in the left sidebar navigation.

**Expected Result:**
- Step 2: "Stock Leaderboard" text is visible; table renders with real tickers, no crash, no blank page.
- Step 3: no row's symbol is `^SPX`, `^NDX`, `^DJI`, `^VIX`, or `^TNX` (deep index/macro symbols never leak
  into the scored leaderboard); every visible score shows "Not yet proven".
- Step 4: the count reads exactly `541 / 541`.
- Step 6: at least one row's Sector cell reads exactly "Unassigned" (for a ticker with no sector on file) —
  the table re-sorted without crashing.
- Step 7: the browser navigates to `http://localhost:3255/evidence`, where the heading "Evidence" is
  visible.

---

### UT-17 — Required-still-passing J-03: unvalidated signals flagged "Not yet proven" on leaderboard AND detail page (regression)

**Type:** regression
**Priority:** P1 *(required-still-passing per DoD; graded against `journey-scripts/J-03.json`)*
**Surface:** `/stocks`, `/stocks/MU`

**Preconditions:**
- None beyond global preconditions.

**Steps:**
1. Navigate to `http://localhost:3255/stocks`.
2. Confirm "Not yet proven" appears on the leaderboard (spot-check 3–5 rows).
3. Navigate to `http://localhost:3255/stocks/MU`.
4. Confirm "Not yet proven" appears somewhere on this ticker's detail page.

**Expected Result:**
- Both the leaderboard and the MU detail page show "Not yet proven" for their score badges; zero "Proven"
  badges appear anywhere.

---

### UT-18 — Required-still-passing J-04: Dashboard regime card + regime-conditioned evidence (regression)

**Type:** regression
**Priority:** P1 *(required-still-passing per DoD; graded against `journey-scripts/J-04.json`)*
**Surface:** `/`, `/evidence`

**Preconditions:**
- None beyond global preconditions.

**Steps:**
1. Navigate to `http://localhost:3255`. Confirm "Dashboard" heading is visible.
2. Locate the "Market Regime" card and read its badge value.
3. Confirm the link text "See evidence proven in this regime →" is present in that card.
4. Click that link.
5. On the resulting page, read the ledger row that shows a "Regime:" field.
6. Read that same row's subtitle/context text and its verdict field.

**Expected Result:**
- Step 2: the "Market Regime" badge reads exactly `Risk-on` (reflects the current committed dataset's
  latest as-of snapshot as of this iteration).
- Step 4: the browser navigates to `http://localhost:3255/evidence`, heading "Evidence" visible.
- Step 5: a row shows the field `Regime: Risk-on`.
- Step 6: that same row's subtitle reads exactly "Out-of-sample edge in the Risk-on regime", and its
  verdict field reads exactly `FAIL · holdout edge -0.68%`.
- Also confirm the adjacent "Market Phase & Severity" card (next to "Market Regime") still renders its own
  badge/score, unaffected by the chart below gaining vendor labels.

---

### UT-19 — Required-still-passing J-05: `/evidence` ledger — 7 all-FAIL rows, auditable linkbacks (regression)

**Type:** regression
**Priority:** P1 *(required-still-passing per DoD; graded against `journey-scripts/J-05.json`)*
**Surface:** `/evidence`

**Preconditions:**
- None beyond global preconditions.

**Steps:**
1. Navigate to `http://localhost:3255/evidence`. Confirm heading "Evidence" is visible.
2. Read the subtitle under the heading.
3. Scan the ledger for a row/field containing the text "leadership_score".
4. On that same row, read its verdict field and confirm a date field.
5. Scan for rows/fields containing "vcp_contraction — top decile (D10)", "ma_stack — top decile (D10)",
   and "rs_spy_3m — top decile (D10)".
6. Count the total number of claim rows on the page.
7. Click any row's linkback (text pattern "Backs: `<label>` →", e.g. "Backs: Stocks leaderboard →").

**Expected Result:**
- Step 2: subtitle reads: `The certified-claims ledger — the single source of proven-ness. A signal reads
  "Proven" ONLY when a referee-certified, out-of-sample, control-beating claim backs it; everything else
  honestly reads "Not yet proven."`
- Step 4: the verdict field for the `leadership_score` row reads exactly `FAIL · holdout edge -0.03%`; a
  date field on the page reads `2026-07-03`.
- Step 5: all three exact strings are present verbatim somewhere on the page.
- Step 6: exactly **7** claim rows render.
- Step 7: every row shows a FAIL verdict (no "Proven"/"PASS" anywhere); the clicked linkback navigates to
  the correct research surface without a 404 or blank page.

---

### UT-20 — Required-still-passing J-10: `/stocks/NVDA` Full history ↔ Recent toggle, exact bar counts, no crash (regression)

**Type:** regression
**Priority:** P1 *(required-still-passing per DoD; graded against `journey-scripts/J-10.json`, which uses
NVDA specifically — not an arbitrary ticker)*
**Surface:** `/stocks/NVDA`

**Preconditions:**
- None beyond global preconditions.

**Steps:**
1. Navigate to `http://localhost:3255/stocks/NVDA`.
2. Near the top of the page (in the setup/status area), confirm the sector text reads "Technology".
3. Locate the "Price & moving averages" card. In its header, find the "Recent" / "Full history" toggle
   buttons and, to their right (past the "Regime on/off" toggle), a small caption showing a bar count.
4. Click the "Full history" button.
5. Read the caption text.
6. Click the "Recent" button.
7. Read the caption text again.

**Expected Result:**
- Step 2: "Technology" is visible.
- Step 5 (after clicking "Full history"): the caption reads `3025 bars · as of 2026-07-01 · history since
  1999-01-22 · older bars weekly-sampled` (the leading number and "older bars weekly-sampled" suffix are
  the parts to verify; the "as of" date may differ slightly if the dataset has advanced since this plan was
  written — the bar count and downsample suffix are the load-bearing checks).
- Step 7 (after clicking "Recent"): the caption reads `1255 bars · as of … · history since 1999-01-22`
  (no "weekly-sampled" suffix — the recent window is full-resolution).
- No console error or crash when toggling either direction; the chart visibly redraws with a different
  date range each time.

---

### UT-21 — Required-still-passing J-11: no stale pre-refresh edge resurfaces; ledgers all-FAIL (regression)

**Type:** regression
**Priority:** P1 *(required-still-passing per DoD; also a direct anti-goal check — a score must never be
presented as proven without a passing certified-claim entry; graded against `journey-scripts/J-11.json`)*
**Surface:** `/evidence`, `/stocks`, `/stocks/NVDA`

**Preconditions:**
- None beyond global preconditions.

**Steps:**
1. Navigate to `http://localhost:3255/evidence`. Scan every row's verdict for the text "FAIL".
2. Navigate to `http://localhost:3255/stocks`. Scan for "Not yet proven".
3. Navigate to `http://localhost:3255/stocks/NVDA`. Scan for "Not yet proven".

**Expected Result:**
- Every row on `/evidence` shows "FAIL" (both the 30-year certified and staging ledgers are all-FAIL this
  iteration — no `## Evidence Claim` was introduced).
- `/stocks` and `/stocks/NVDA` both show "Not yet proven" wherever a score would otherwise be claimed
  proven. If any row unexpectedly reads "Proven," that is a serious regression to escalate immediately,
  not a minor note.

---

### UT-22 — Required-still-passing J-12: universe consistency — `/data` "541" matches `/stocks` "541/541"; DDOG present (regression)

**Type:** regression
**Priority:** P1 *(required-still-passing per DoD; graded against `journey-scripts/J-12.json`)*
**Surface:** `/data`, `/stocks`

**Preconditions:**
- None beyond global preconditions.

**Steps:**
1. Navigate to `http://localhost:3255/data`.
2. Confirm the text "Dynamic-universe membership timeline" (a panel title) is visible.
3. In the "Universe resolution" panel, confirm a metric labeled "Stale series" is visible.
4. In the "Dataset coverage" panel, read the "Universe (as of date)" figure.
5. Navigate to `http://localhost:3255/stocks`.
6. Confirm the ticker "DDOG" appears somewhere in the leaderboard.

**Expected Result:**
- Step 4: the "Universe (as of date)" value reads `541` — the same number as `/stocks`' "541 / 541" count
  (UT-16) — confirming the two independently-rendered surfaces agree on the scored-universe size. (Do not
  confuse this with the separate "Symbols" stat on the same page, which reads `590` — see the "Key numbers"
  table above.)
- Step 6: "DDOG" (Datadog) is present in the current leaderboard — a real, currently-listed ticker.

---

### UT-23 — UX: the provenance panel is discoverable within 2 clicks from home, with a self-explanatory title (ux)

**Type:** ux
**Priority:** P2
**Surface:** `/` → `/data`

**Preconditions:**
- None beyond global preconditions.

**Steps:**
1. Navigate to `http://localhost:3255` (home/Dashboard) — this is click 0.
2. Click "Data Manager" in the left sidebar — click 1.
3. Scroll down the `/data` page — no further click needed, just scrolling.
4. Read the new card's title and its one-line hint text, without any outside explanation.

**Expected Result:**
- The provenance panel is reached in exactly 1 click from the Dashboard (within the blueprint's ≤2-click
  requirement) via the existing "Data Manager" nav item — no new nav item exists or is needed.
- The card's title, "Index & benchmark data provenance," combined with its hint text (quoted in UT-07), is
  self-explanatory: a first-time reader can tell without external help that this table shows where each
  chart line's data comes from and how far back it truly goes.

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | Dashboard loads, chart renders | smoke | P1 | `/` |
| UT-02 | `/data` loads with all panels + provenance panel | smoke | P1 | `/data` |
| UT-03 | Deep lines extend to 1996 — J-14 flip case | happy-path | P1 | `/` |
| UT-04 | Legend shows vendor labels (3 categories) | happy-path | P1 | `/` |
| UT-05 | Tooltip shows vendor suffix | happy-path | P1 | `/` |
| UT-06 | 10 legend colors all distinct | happy-path | P1 | `/` |
| UT-07 | `/data` panel lists 10 series correctly | happy-path | P1 | `/data` |
| UT-08 | ETF lines show no vendor tag (chart) | validation | P2 | `/` |
| UT-09 | ETF/proxy rows read honestly (`/data`) | validation | P2 | `/data` |
| UT-10 | J-13 dedicated replay — legend/ramp/ring/tooltip | happy-path | P1 | `/data` |
| UT-11 | Header badge "590 symbols" (fixture accuracy) | regression | P2 | global header |
| UT-12 | Whole-backend-down error is honest | error | P2 | `/data` |
| UT-13 | Isolated panel error (automation-only) | error | P3 | `/data` |
| UT-14 | Loading skeleton (best-effort) | ux | P3 | `/data` |
| UT-15 | Existing ETF lines unchanged | regression | P1 | `/` |
| UT-16 | J-01 — `/stocks` 541/541, no leaked rows, sort+nav | regression | P1 | `/stocks` |
| UT-17 | J-03 — "Not yet proven" on list + detail | regression | P1 | `/stocks`, `/stocks/MU` |
| UT-18 | J-04 — Regime card + regime-conditioned evidence | regression | P1 | `/`, `/evidence` |
| UT-19 | J-05 — Evidence ledger 7 FAIL rows + linkback | regression | P1 | `/evidence` |
| UT-20 | J-10 — NVDA Full/Recent toggle, exact bar counts | regression | P1 | `/stocks/NVDA` |
| UT-21 | J-11 — No stale edge; ledgers all-FAIL | regression | P1 | `/evidence`, `/stocks`, `/stocks/NVDA` |
| UT-22 | J-12 — Universe count consistency; DDOG present | regression | P1 | `/data`, `/stocks` |
| UT-23 | Provenance panel discoverable in ≤2 clicks | ux | P2 | `/` → `/data` |

**P1 tests must all pass for browser QA verdict to be PASS.** UT-13 and UT-14 are best-effort/automation
-only and must not block a PASS verdict on their own if the tooling to execute them is unavailable.
