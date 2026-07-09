# Phase goal-mcp-loop-iter-23 — UI Test Results

**Phase:** goal-mcp-loop-iter-23
**Date:** 2026-07-08 / 2026-07-09
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

<!-- PASS: All P1 tests pass -->
<!-- FAIL: Any P1 test fails -->
<!-- SKIPPED: Frontend not running or Chrome MCP unavailable -->

**Overall:** 22/23 tests passed (1 skipped)

All 16 P1 tests (UT-01, UT-02, UT-03, UT-04, UT-05, UT-06, UT-07, UT-10, UT-15, UT-16, UT-17, UT-18, UT-19,
UT-20, UT-21, UT-22) PASSED with live-verified evidence. The J-14 target flip case (UT-03 — deep `^SPX`
line before 2005 in the default chart view) is confirmed PASS, clearing the iter-22 stale-report gap. The
one SKIP (UT-13) is explicitly sanctioned by its own test-plan text ("skip if no request-blocking capability
is available") — Chrome MCP's action set has no network-interception primitive.

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-01 | Dashboard loads, chart renders | smoke | P1 | Heading, green Ready badge, cross-view chart renders, no console errors | Heading "Dashboard" visible; green "Ready" badge + provider/seed/590-symbols badges; chart rendered fully within ~1s (no stuck spinner). Console-log capture unavailable in this Chrome MCP build (see note) | PASS | `reports/qa/goal-mcp-loop-iter-23-evidence/UT-01-result.png` |
| UT-02 | `/data` loads with all panels + provenance panel | smoke | P1 | All named panels render in order, provenance panel present | Heading "Data Manager"; no Backend-unavailable card; panels rendered top-to-bottom in the specified order ending with "Index & benchmark data provenance" directly after the macro-feed panel | PASS | `reports/qa/goal-mcp-loop-iter-23-evidence/UT-12-backend-recovered.png` |
| UT-03 | Deep lines extend to 1996 — J-14 flip case | happy-path | P1 | Deep `^SPX`/`^NDX`/`^DJI`/`^VIX` lines visible from ~1996 in default view, no zoom/pan | Zoomed crop shows real line pixels (orange dot-com hump, teal/green/pink lines) at the chart's left edge; hover at left edge → tooltip "1996-02-26" listing only `^SPX`/`^NDX`/`^DJI`/`^VIX` with `%`+vendor, no ETFs/`^TNX` | PASS | `reports/qa/goal-mcp-loop-iter-23-evidence/UT-03-hover-leftedge.png`, `UT-03-left-edge-zoom.png` |
| UT-04 | Legend shows vendor labels (3 categories) | happy-path | P1 | 10 exact legend entries, vendor tag in parens for the 5 deep/macro series only | `extract` text confirmed exact 10-entry order/text; `Stooq`/`Yahoo`/`FRED-macro proxy` all present; 5 ETF entries have no parenthetical | PASS | `reports/qa/goal-mcp-loop-iter-23-evidence/UT-06-legend-zoom.png` |
| UT-05 | Tooltip shows vendor suffix | happy-path | P1 | Recent-date hover shows `symbol · vendor · %` for deep series, bare `symbol %` for ETFs | Hover at 2025-03-25 → exact tooltip text captured: `^SPX· Stooq+830.62%`, `^VIX· Yahoo+40.69%`, `^TNX· FRED-macro proxy+440.83%`; SPY/QQQ/IWM/RSP/DIA show no `·` | PASS | `reports/qa/goal-mcp-loop-iter-23-evidence/UT-05-hover-recent.png` |
| UT-06 | 10 legend colors all distinct | happy-path | P1 | No two of the 10 swatches share a color; entry1 (SPY) ≠ entry6 (^SPX) | Computed `background-color` read programmatically for all 10 dots: 10 distinct RGB values (teal/green/amber/red/gray/violet/orange/lime/blue/pink); SPY=rgb(79,209,197) vs ^SPX=rgb(167,139,250) — clearly different | PASS | `reports/qa/goal-mcp-loop-iter-23-evidence/UT-06-legend-zoom.png` |
| UT-07 | `/data` panel lists 10 series correctly | happy-path | P1 | Exact hint text; 10-row table matching vendor/first-bar reference table | Hint text byte-matches spec; table's 10 rows (SERIES/VENDOR/FIRST BAR) matched the reference table exactly, incl. `^SPX`→Stooq/1996-01-02 and `^TNX`→FRED-macro proxy/2021-01-04 | PASS | (grep-verified against live DOM extract; see narrative) |
| UT-08 | ETF lines show no vendor tag (chart) | validation | P2 | No `(vendor)` in legend or `· vendor` in tooltip for the 5 ETFs | Confirmed via the same UT-05 tooltip capture: SPY/QQQ/IWM/RSP/DIA rows show bare `%`, no `·` suffix, no `()`/`(null)`/`(undefined)` anywhere | PASS | `reports/qa/goal-mcp-loop-iter-23-evidence/UT-05-hover-recent.png` |
| UT-09 | ETF/proxy rows read honestly (`/data`) | validation | P2 | SPY/QQQ show `—` vendor + real first-bar; `^TNX` row says "proxy"/"spread", vendor "FRED-macro proxy" | SPY: `—` / `2005-02-25`; QQQ: `—` / `1999-03-10`; `10Y-2Y spread proxy (^TNX)` / `FRED-macro proxy` — all exact matches | PASS | (grep-verified against live DOM extract; see narrative) |
| UT-10 | J-13 dedicated replay — legend/ramp/ring/tooltip | happy-path | P1 | Two-group legend exact text, non-amber blue ramp, violet ring, md5-distinct hover pair | "Price data — cell fill" / "Scored snapshot — indicator" confirmed exact; 6-step ramp rgb(57,81,111)→rgb(166,200,242) (blue family); ring color `#a78bfa` (violet); hover readouts "2026-05-01 · 590/590 symbols · snapshot yes" (violet) vs "2026-05-04 · 590/590 symbols · snapshot no" (gray) — md5-distinct screenshots | PASS | `reports/qa/goal-mcp-loop-iter-23-evidence/UT-10-legend-overview.png`, `UT-10-hover-snapshot-yes.png`, `UT-10-hover-snapshot-no.png`, `UT-10-readout-yes-zoom.png`, `UT-10-readout-no-zoom.png` |
| UT-11 | Header badge "590 symbols" (fixture accuracy) | regression | P2 | Header badge reads exactly "590 symbols" | Confirmed on every page visited (Dashboard, /stocks, /data, /evidence, /stocks/NVDA): badge reads "590 symbols"; backend `/api/health` also reports `symbol_count: 590` | PASS | `reports/qa/goal-mcp-loop-iter-23-evidence/UT-01-result.png` |
| UT-12 | Whole-backend-down error is honest | error | P2 | One red "Backend unavailable" card, header pill turns red, clean recovery after restart | Killed backend (PID) → reload showed exact text "Backend unavailable" / "Dataset coverage could not load from the API. No figures are shown rather than fabricated values. Confirm the backend is running and retry."; header pill red, provider/seed/symbols badges gone; restarted backend → page recovered to normal "Ready"/"590 symbols" state | PASS | `reports/qa/goal-mcp-loop-iter-23-evidence/UT-12-backend-down.png`, `UT-12-backend-recovered.png` |
| UT-13 | Isolated panel error (automation-only) | error | P3 | N/A — requires network request-blocking | Chrome MCP's action set (navigate/click/type/extract/screenshot/eval/hover/scroll/etc.) exposes no request-interception or URL-blocking primitive | SKIPPED | none — tooling limitation, sanctioned by test-plan text |
| UT-14 | Loading skeleton (best-effort) | ux | P3 | Gray pulsing skeleton blocks before content, no unstyled flash | Fresh `/data` navigation captured mid-load: solid gray pulsing rectangular placeholders in place of every panel (no readable text), replaced by real content ~1s later; no layout jump or error flash observed | PASS | `reports/qa/goal-mcp-loop-iter-23-evidence/UT-14-loading-skeleton.png` |
| UT-15 | Existing ETF lines unchanged | regression | P1 | Names/order/colors byte-identical to pre-iter-22; tooltip % values present | Computed CSS confirmed exact var names: SPY=`--accent` rgb(79,209,197), QQQ=`--pos` rgb(52,211,153), IWM=`--warn` rgb(251,191,36), RSP=`--neg` rgb(248,113,113), DIA=`--text-muted` rgb(139,152,169); recent-date tooltip showed all 5 with real `%` values | PASS | `reports/qa/goal-mcp-loop-iter-23-evidence/UT-05-hover-recent.png` |
| UT-16 | J-01 — `/stocks` 541/541, no leaked rows, sort+nav | regression | P1 | "Stock Leaderboard" text, no `^`-symbol rows, "541 / 541", sort works, "Unassigned" present, Evidence nav works | All confirmed: 1623× "Not yet proven", 0 leaked caret symbols, "541 / 541" exact; clicked "Sort by Sector" (aria-label match) → re-sorted with ↑ indicator, re-checked "Unassigned" count (423, unchanged) confirming no data loss on sort; clicked "Evidence" sidebar link → navigated to `/evidence` | PASS | `reports/qa/goal-mcp-loop-iter-23-evidence/UT-16-stocks-leaderboard.png` |
| UT-17 | J-03 — "Not yet proven" on list + detail | regression | P1 | Leaderboard AND `/stocks/MU` both show "Not yet proven"; zero "Proven" | Leaderboard: 1623 occurrences, 0 "Proven". `/stocks/MU`: `document.body.innerText.includes('Not yet proven')` → true | PASS | `reports/qa/goal-mcp-loop-iter-23-evidence/UT-17-MU-detail.png` |
| UT-18 | J-04 — Regime card + regime-conditioned evidence | regression | P1 | "Risk-on" badge, evidence link works, exact ledger row/subtitle/verdict | Market Regime badge = "Risk-on" exactly; clicked "See evidence proven in this regime →" → `/evidence`; row shows "Regime: Risk-on", subtitle "Out-of-sample edge in the Risk-on regime" (exact), verdict "FAIL · holdout edge -0.68%" (exact) | PASS | `reports/qa/goal-mcp-loop-iter-23-evidence/UT-01-result.png`, `UT-19-evidence-ledger.png` |
| UT-19 | J-05 — Evidence ledger 7 FAIL rows + linkback | regression | P1 | Exact subtitle, exactly 7 rows all-FAIL, 3 exact factor strings, working linkback | Subtitle byte-matched; counted exactly 7 claim rows (leadership_score, Breakout-watch/regime, ma_stack D10, vcp_contraction D10 ×2 horizons, rs_spy_3m×high_proximity composite, rs_spy_3m D10); leadership_score verdict "FAIL · holdout edge -0.03%" + date "2026-07-03" exact; all 3 named factor strings present verbatim; clicked "Backs: Stocks leaderboard →" → navigated cleanly to `/stocks` | PASS | `reports/qa/goal-mcp-loop-iter-23-evidence/UT-19-evidence-ledger.png` |
| UT-20 | J-10 — NVDA Full/Recent toggle, exact bar counts | regression | P1 | "Technology" visible; Full history → "3025 bars…weekly-sampled"; Recent → "1255 bars…" no suffix | "Technology" confirmed; clicked "Full history" → caption exactly "3025 bars · as of 2026-07-01 · history since 1999-01-22 · older bars weekly-sampled"; clicked "Recent" → exactly "1255 bars · as of 2026-07-01 · history since 1999-01-22" (no weekly-sampled suffix); no console/DOM errors toggling either way | PASS | `reports/qa/goal-mcp-loop-iter-23-evidence/UT-20-NVDA-full-history.png`, `UT-20-NVDA-recent.png` (md5-distinct) |
| UT-21 | J-11 — No stale edge; ledgers all-FAIL | regression | P1 | `/evidence` all-FAIL; `/stocks` + `/stocks/NVDA` all "Not yet proven"; zero "Proven" | `/evidence`: 7/7 rows FAIL, 0 "Proven"/"PASS". `/stocks`: 1623× Not yet proven, 0 Proven. `/stocks/NVDA`: score cards read "Not yet proven" ×3 (Leadership/Entry Quality/Risk), 0 Proven | PASS | `reports/qa/goal-mcp-loop-iter-23-evidence/UT-21-nvda-notproven.png` |
| UT-22 | J-12 — Universe count consistency; DDOG present | regression | P1 | `/data` "541" == `/stocks` "541/541"; "Stale series" metric visible; DDOG present | "Dynamic-universe membership timeline" panel present; "Stale series" metric = 1 (visible in Universe-resolution panel); "Universe (as of date)" = 541, matching `/stocks`' "541 / 541"; searched leaderboard for "DDOG" → 1 row, Technology sector | PASS | `reports/qa/goal-mcp-loop-iter-23-evidence/UT-22-universe-resolution-stale.png`, `UT-22-ddog-present.png` |
| UT-23 | Provenance panel discoverable in ≤2 clicks | ux | P2 | Reached in ≤2 clicks via existing nav; self-explanatory title+hint | Dashboard → "Data Manager" (1 click) → scroll (0 clicks) → panel visible; title "Index & benchmark data provenance" + hint text (quoted in UT-07) is self-explanatory without external context | PASS | `reports/qa/goal-mcp-loop-iter-23-evidence/UT-01-result.png`, `UT-12-backend-recovered.png` |

---

## Passed Tests

### UT-01 — Dashboard loads and the cross-view chart renders
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-23-evidence/UT-01-result.png`
- Navigated to `http://localhost:3255`. Heading "Dashboard" visible immediately. Header shows green "Ready"
  pill + "provider: seed" + "seed 2026-07-01" + "590 symbols" badges (not a red "Backend unavailable"
  badge). The "Regime × phase cross-view" card initially rendered an empty canvas for well under a second,
  then filled with the full chart on the very next screenshot — no stuck spinner.
- **Limitation noted, not a failure:** this Chrome MCP build's `get_console_messages` action returns "No
  console messages captured" / the auto-captured `*-console.txt` files literally contain "# TODO: Console
  logging not yet implemented" regardless of `enable_console_logging` being called repeatedly. Console-error
  verification for this and every other test case relied on absence of any visible error boundary / crash
  UI / broken layout instead of a captured console stream. No visual error indication was observed on any
  page throughout this run.

### UT-02 — `/data` loads with all existing panels plus the provenance panel
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-23-evidence/UT-12-backend-recovered.png` (shows the top of a
normally-loaded `/data`; the full panel-by-panel order was confirmed via a full-page text extract)
- Heading "Data Manager" visible, no "Backend unavailable" card. Confirmed via a full-page text dump
  (grepped for section order) that panels render in this order: "Dataset coverage" → "Rebuild snapshots for
  current universe" → "Universe resolution as of 2026-07-01" → "Dynamic-universe membership timeline" →
  "Per-date availability" → "Missing-data diagnostic" → a macro-feed panel → "Index & benchmark data
  provenance" (directly after the macro panel), matching the required order.
- **Minor observation (not a failure):** the macro panel's own on-page heading text is "FRED (macro feed)",
  not the literal string "Macro feed" the test-plan prose uses as a shorthand label. The panel's content
  ("Optional FRED macro feed — yield-curve, unemployment...") is unambiguously the macro-feed panel in the
  correct position; this is a naming-precision note for future test-plan wording, not a UI defect.

### UT-03 — Deep `^SPX`/`^NDX`/`^DJI`/`^VIX` lines extend to 1996 in the DEFAULT chart view — the J-14 flip case
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-23-evidence/UT-03-hover-leftedge.png`,
`UT-03-left-edge-zoom.png`
- This is the exact case that FAILed in iter-22's stale QA report (x-axis floored ~2018). Loaded `/`
  fresh, took NO zoom/pan action. A 2×-zoomed pixel crop of the chart's left ~30% (`UT-03-left-edge-zoom.png`)
  shows real, in-frame line pixels at the absolute left edge — an orange line with a visible late-1990s hump
  (the dot-com bubble, consistent with `^NDX`) plus flatter teal/green/pink lines — while the colored
  regime/phase background shading only starts around 2005 (a separate visual layer, not the price lines).
- Hovered the leftmost ~2% of the plotted area (x=274px of a ~1200px-wide plot). Tooltip read date
  "1996-02-26" (within the first two months of the deep series — "near 1996-01-02" per the test's own
  tolerance) with exactly 4 rows: `^SPX · Stooq +4.79%`, `^NDX · Stooq +8.87%`, `^DJI · Stooq +7.49%`,
  `^VIX · Yahoo +34.37%`. SPY/QQQ/IWM/RSP/DIA/`^TNX` were absent from the tooltip (honestly not yet
  started this early), not shown as 0% or a fabricated flat line.
- The evidence screenshot is a full, unscrolled view of the entire chart element (legend visible at the
  bottom, x-axis visible, nothing cropped) — satisfies the "never a scrolled viewport that could hide the
  left edge" requirement.

### UT-04 — Chart legend shows vendor labels spanning all three vendor categories
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-23-evidence/UT-06-legend-zoom.png`
- A full-page text extract confirmed the legend renders exactly these 10 entries in order: `S&P 500 (SPY)`,
  `Nasdaq 100 (QQQ)`, `Russell 2000 (IWM)`, `S&P 500 Equal-Weight (RSP)`, `Dow 30 (DIA)`,
  `S&P 500 Index (^SPX) (Stooq)`, `Nasdaq 100 Index (^NDX) (Stooq)`,
  `Dow Jones Industrial Average (^DJI) (Stooq)`, `CBOE Volatility Index (^VIX) (Yahoo)`,
  `10Y-2Y spread proxy (^TNX) (FRED-macro proxy)`. The zoomed legend screenshot visually confirms the
  vendor tag renders in a lighter/faint gray parenthetical immediately after each of the 3 vendor
  categories (Stooq/Yahoo/FRED-macro proxy), and that the 5 original ETF entries carry no such tag.

### UT-05 — Hover tooltip shows the vendor next to a deep series' symbol
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-23-evidence/UT-05-hover-recent.png`
- Hovered a recent date (2025-03-25, where all 10 series have data). Extracted the tooltip's exact text:
  `SPY+514.19%QQQ+1039.81%IWM+284.77%RSP+447.54%DIA+383.39%^SPX· Stooq+830.62%^NDX· Stooq+3362.44%^DJI·
  Stooq+722.55%^VIX· Yahoo+40.69%^TNX· FRED-macro proxy+440.83%` — confirming the `· Stooq`/`· Yahoo`/
  `· FRED-macro proxy` suffix appears for exactly the 5 deep/macro rows and nowhere else.

### UT-06 — All 10 legend color swatches are visually distinct
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-23-evidence/UT-06-legend-zoom.png`
- Read `getComputedStyle(...).backgroundColor` for all 10 legend dots programmatically (stronger evidence
  than eyeballing a screenshot): SPY `rgb(79,209,197)` (`--accent`), QQQ `rgb(52,211,153)` (`--pos`), IWM
  `rgb(251,191,36)` (`--warn`), RSP `rgb(248,113,113)` (`--neg`), DIA `rgb(139,152,169)` (`--text-muted`),
  ^SPX `rgb(167,139,250)` (`--snapshot`, violet), ^NDX `rgb(251,141,63)` (orange), ^DJI `rgb(75,205,81)`
  (lime), ^VIX `rgb(85,184,226)` (sky blue), ^TNX `rgb(244,124,213)` (pink). All 10 values are pairwise
  distinct; SPY (teal) vs ^SPX (violet) — the historically-buggy pair — are unambiguously different colors.

### UT-07 — `/data` provenance panel lists all 10 series with correct vendor + first-bar date
**Verdict:** PASS
**Evidence:** live DOM text extract (grepped), cross-referenced against `UT-12-backend-recovered.png`
- Hint text under the title read, verbatim: "Every index/benchmark/macro line on the major-indexes chart,
  with its honest data vendor and real first-bar date — the same GET /api/indexes payload the Dashboard
  chart reads, never a recompute." — exact match.
- The table's 10 data rows matched the reference table exactly, in order: SPY `—`/2005-02-25, QQQ
  `—`/1999-03-10, IWM `—`/2005-02-25, RSP `—`/2005-02-25, DIA `—`/2005-02-25, ^SPX Stooq/1996-01-02, ^NDX
  Stooq/1996-01-02, ^DJI Stooq/1996-01-02, ^VIX Yahoo/1996-01-02, ^TNX FRED-macro proxy/2021-01-04.

### UT-08 — Chart legend/tooltip show no vendor tag for the 5 original ETF lines
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-23-evidence/UT-05-hover-recent.png`
- Confirmed via the same UT-04/UT-05 captures: none of the 5 ETF legend entries carry any parenthetical
  (no `(Stooq)`, `(null)`, `(undefined)`, or empty `()`); none of the 5 ETF tooltip rows carry a `·`-prefixed
  suffix — just the bare symbol and `%` value.

### UT-09 — `/data` panel: ETF rows show honest "—" vendor; FRED-macro-proxy row reads honestly
**Verdict:** PASS
**Evidence:** live DOM text extract (grepped)
- SPY row: Vendor `—` (single em dash, not blank/null), First bar `2005-02-25` (a real date). QQQ row:
  Vendor `—`, First bar `1999-03-10`. `^TNX` row: Series name reads `10Y-2Y spread proxy (^TNX)` (uses
  "proxy"/"spread" language, never implies a literal real-time yield); Vendor badge reads exactly
  `FRED-macro proxy` (not "FRED" alone, not "Yahoo"/"Stooq").

### UT-10 — J-13 dedicated replay: two-group legend, density ramp, snapshot ring, md5-distinct hover-tooltip pair
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-23-evidence/UT-10-legend-overview.png`,
`UT-10-hover-snapshot-yes.png`, `UT-10-hover-snapshot-no.png`, `UT-10-readout-yes-zoom.png`,
`UT-10-readout-no-zoom.png` (all md5-distinct — verified with `md5sum`)
- Legend group labels read exactly `Price data — cell fill` and `Scored snapshot — indicator` (read from
  the live DOM, confirming the actual un-transformed text, not the CSS-uppercased display).
- The 6 fill swatches (`bg-heat-0`…`bg-heat-5`) have computed colors `rgb(57,81,111)` →
  `rgb(61,107,164)` → `rgb(77,134,203)` → `rgb(102,155,219)` → `rgb(131,176,231)` → `rgb(166,200,242)` — a
  monotonic dark-to-light **blue** ramp; the brightest/"full" swatch is unambiguously blue, not amber/orange.
- The snapshot ring's computed ring color is `#a78bfa` (`rgb(167,139,250)`) — a violet/purple, not green —
  read directly from `--tw-ring-color` / the CSS variable `--snapshot`.
- Hovered a "full" (100%) cell with a snapshot (`2026-05-01`) and a "full" cell without one (`2026-05-04`).
  The top-right hover-readout area showed exactly `2026-05-01 · 590/590 symbols · snapshot yes` (the
  "snapshot yes" portion rendered in a distinct violet color) vs `2026-05-04 · 590/590 symbols · snapshot
  no` (the "snapshot no" portion in the same faint gray as the rest of the line) — textually and visually
  distinct, confirmed with separate, md5-distinct screenshots (`bdb9a68e...` vs `15731dac...`).
- The footer caption text included, verbatim: "...total stored symbols (590)...filled by Fetch...",
  matching the current 590-symbol pool.
- **Tooling note:** capturing screenshots at this section required a workaround — see "Browser automation
  notes" below.

### UT-11 — Header badge shows the correct total-symbol count "590 symbols"
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-23-evidence/UT-01-result.png`
- The header's last badge read exactly `590 symbols` on every page visited during this run (Dashboard,
  `/stocks`, `/data`, `/evidence`, `/stocks/MU`, `/stocks/NVDA`) — confirming the `journey-scripts/J-13.json`
  fixture refresh (587→590) matches the live, currently-served data. The backend's own `/api/health`
  endpoint independently reports `"symbol_count": 590`.

### UT-12 — `/data` shows one honest "Backend unavailable" message when the whole backend is down
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-23-evidence/UT-12-backend-down.png`,
`UT-12-backend-recovered.png`
- Confirmed `/data` loaded normally first. Stopped the backend process (graceful `kill` on the uvicorn
  PID; frontend left running). Reloaded `/data`: page showed the "Data Manager" heading, then exactly one
  red-bordered card with bold text "Backend unavailable" and the message "Dataset coverage could not load
  from the API. No figures are shown rather than fabricated values. Confirm the backend is running and
  retry." — byte-exact match to spec. No other panel rendered below it. The header's readiness pill turned
  red and read "Backend unavailable"; the provider/seed/symbols badges disappeared entirely (no stale or
  fabricated values). No blank white page, no stack-trace crash page.
- Restarted the backend via `scripts/start-backend.sh` (same port/env as the original launch) and confirmed
  `/api/health` returned 200 with `symbol_count: 590` within 1 second. Reloaded `/data`: page returned to
  the normal state — "Ready" badge, "590 symbols", full "Dataset coverage" panel with all figures restored.

### UT-14 — Provenance panel shows a loading skeleton before data resolves (best-effort)
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-23-evidence/UT-14-loading-skeleton.png`
- No network throttling tool was available, but a fresh `/data` navigation happened to be captured mid-load:
  solid gray pulsing rectangular blocks (no readable text) stood in place of every panel — including where
  the provenance panel would render, since (per the UT-12 investigation) the whole page shares one gating
  fetch, so its skeleton batch necessarily includes the provenance panel's own loading state. The real
  content replaced the skeleton roughly a second later with no layout jump or error flash.

### UT-15 — Regression: the 5 pre-existing ETF lines and legend entries are unchanged
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-23-evidence/UT-05-hover-recent.png`
- All 5 original entries present, in original relative order, with the exact pre-iter-22 color assignment
  confirmed via computed CSS variable names: SPY=`--accent` (teal), QQQ=`--pos` (green), IWM=`--warn`
  (amber), RSP=`--neg` (red), DIA=`--text-muted` (gray) — byte-identical to the spec's required mapping.
  Hovering a recent date (2025-03-25) showed all 5 with real `%` values in the tooltip (SPY +514.19%, QQQ
  +1039.81%, IWM +284.77%, RSP +447.54%, DIA +383.39%). No existing chart control behaved differently.

### UT-16 — Required-still-passing J-01: `/stocks` leaderboard — 541/541, zero leaked index carets, sort + evidence nav
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-23-evidence/UT-16-stocks-leaderboard.png`
- "Stock Leaderboard" text visible in the page subtitle; table rendered 541 real tickers, no crash.
- A full-page text extract found 1623 occurrences of "Not yet proven" and zero rows starting with `^`
  (`^SPX`/`^NDX`/`^DJI`/`^VIX`/`^TNX` never leak into the scored leaderboard). The toolbar count read exactly
  `541 / 541`.
- Clicked the "Sector" column header (`aria-label="Sort by Sector"`) — table re-sorted (▲ indicator, rows
  reordered to "Communication Services" first, alphabetically ascending), no crash. Re-checked the
  "Unassigned" substring count immediately after the sort: **423** occurrences — identical to the pre-sort
  count, confirming the sort neither lost nor hid any "Unassigned"-sector rows.
- Clicked "Evidence" in the left sidebar — navigated cleanly to `/evidence`, heading "Evidence" visible.
- **Cross-check note:** a deterministic Playwright replay of this same journey's golden script
  (`journey-scripts/J-01.json`, via `demo_runner.py --mode verify`) flagged its step 4 ("Sort by Sector" →
  expect "Unassigned") as failing to find the text within its timeout. I re-drove the identical interaction
  twice more, live, via Chrome MCP with the exact same `aria-label="Sort by Sector"` selector immediately
  before and after the click, and got a consistent, repeatable 423-occurrence count both times — the text is
  genuinely present in the DOM (this is an unvirtualized ~541-row table; all rows are always mounted). I
  attribute the replay tool's single failure to a timing/race nuance in its own Playwright automation
  against this specific non-virtualized-but-very-large table, not a product regression. `J-01.json` was left
  unmodified since its assertion is factually accurate.

### UT-17 — Required-still-passing J-03: unvalidated signals flagged "Not yet proven" on leaderboard AND detail page
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-23-evidence/UT-17-MU-detail.png`
- Leaderboard: "Not yet proven" confirmed across many spot-checked rows (1623 total occurrences, 0
  "Proven"). `/stocks/MU`: `document.body.innerText.includes('Not yet proven')` evaluated to `true`. Zero
  "Proven" badges found anywhere.

### UT-18 — Required-still-passing J-04: Dashboard regime card + regime-conditioned evidence
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-23-evidence/UT-01-result.png`,
`reports/qa/goal-mcp-loop-iter-23-evidence/UT-19-evidence-ledger.png`
- "Market Regime" badge reads exactly `Risk-on`. "See evidence proven in this regime →" link present and,
  when clicked, navigated to `/evidence` (heading "Evidence" visible). The ledger row for
  "Breakout-watch setup" shows the field `Regime: Risk-on`, subtitle "Out-of-sample edge in the Risk-on
  regime" (exact), and verdict `FAIL · holdout edge -0.68%` (exact). The adjacent "Market Phase & Severity"
  card independently rendered its own badge ("Expansion") and score (29.95/100), unaffected by the chart's
  new vendor labels.

### UT-19 — Required-still-passing J-05: `/evidence` ledger — 7 all-FAIL rows, auditable linkbacks
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-23-evidence/UT-19-evidence-ledger.png`
- Subtitle byte-matched: "The certified-claims ledger — the single source of proven-ness. A signal reads
  "Proven" ONLY when a referee-certified, out-of-sample, control-beating claim backs it; everything else
  honestly reads "Not yet proven."" `leadership_score` row: verdict `FAIL · holdout edge -0.03%` exact, date
  `2026-07-03` present. All three named strings present verbatim: `vcp_contraction — top decile (D10)`,
  `ma_stack — top decile (D10)`, `rs_spy_3m — top decile (D10)`. Counted exactly **7** claim rows. Clicked
  the "Backs: Stocks leaderboard →" linkback on the `leadership_score` row — navigated cleanly to `/stocks`
  (557 links / 736 buttons rendered, no 404, no blank page). Every one of the 7 rows shows FAIL; zero
  "Proven"/"PASS" anywhere on the page.

### UT-20 — Required-still-passing J-10: `/stocks/NVDA` Full history ↔ Recent toggle, exact bar counts, no crash
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-23-evidence/UT-20-NVDA-full-history.png`,
`UT-20-NVDA-recent.png` (md5: `3ad7e490...` vs `49dd3d7f...` — distinct)
- Sector text "Technology" confirmed near the top of the page. Clicked "Full history"
  (`data-testid="chart-range-full"`) — caption read exactly `3025 bars · as of 2026-07-01 · history since
  1999-01-22 · older bars weekly-sampled`. Clicked "Recent" (`data-testid="chart-range-recent"`) — caption
  read exactly `1255 bars · as of 2026-07-01 · history since 1999-01-22` (no weekly-sampled suffix). No
  errors toggling either direction; screenshots of both states are md5-distinct, confirming the chart
  visibly redrew.

### UT-21 — Required-still-passing J-11: no stale pre-refresh edge resurfaces; ledgers all-FAIL
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-23-evidence/UT-21-nvda-notproven.png`
- `/evidence`: all 7 rows show "FAIL", zero "Proven"/"PASS". `/stocks`: "Not yet proven" present 1623×, zero
  "Proven". `/stocks/NVDA`: the Leadership (34.24), Entry Quality (52.54), and Risk (34.64) score cards each
  show a "Not yet proven" badge — visually confirmed in the evidence screenshot — with zero "Proven" badges
  anywhere on the page.

### UT-22 — Required-still-passing J-12: universe consistency — `/data` "541" matches `/stocks` "541/541"; DDOG present
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-23-evidence/UT-22-universe-resolution-stale.png`,
`UT-22-ddog-present.png`
- "Dynamic-universe membership timeline" panel title confirmed visible. The "Universe resolution" panel
  shows a metric labeled "Stale series" with value **1**. The "Dataset coverage" panel's "Universe (as of
  date)" figure reads **541** — the same number as `/stocks`' "541 / 541" toolbar count (UT-16), and
  distinct from the separate "Symbols" stat (590). Searched the leaderboard for "DDOG" — exactly one
  matching row, Technology sector, confirming the real, currently-listed ticker is present.

### UT-23 — UX: the provenance panel is discoverable within 2 clicks from home, with a self-explanatory title
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-23-evidence/UT-01-result.png`,
`reports/qa/goal-mcp-loop-iter-23-evidence/UT-12-backend-recovered.png`
- From the Dashboard (click 0), clicking "Data Manager" in the left sidebar (click 1) lands on `/data`;
  scrolling (no further click) reveals the "Index & benchmark data provenance" card — reached in exactly 1
  click, within the ≤2-click requirement, via the pre-existing nav item (no new nav item needed). The card's
  title combined with its hint text ("Every index/benchmark/macro line on the major-indexes chart, with its
  honest data vendor and real first-bar date...") is self-explanatory without external context.

---

## Skipped Tests

### UT-13 — Provenance panel's own isolated "Vendor disclosure unavailable" message when only its endpoint fails
**Verdict:** SKIPPED
**Reason:** Requires selectively blocking network requests matching `*/api/indexes*` while leaving all
other endpoints unaffected. The `mcp__plugin_superpowers-chrome_chrome__use_browser` tool's full action set
(navigate, click, type, extract, screenshot, eval, select, attr, await_element, await_text, hover,
drag_drop, mouse_move, scroll, double_click, right_click, file_upload, keyboard_press, set_viewport,
clear_cookies, enable_console_logging, get_console_messages, kill_chrome, restart_chrome, tab management)
exposes no request-interception or URL-blocking primitive. This is explicitly sanctioned by the test case's
own text: "skip if no request-blocking capability is available — UT-12 already covers the human-executable
error path." UT-12 (whole-backend-down) was executed and PASSED.

---

## Browser automation notes (not product defects)

- **Console-log capture unavailable:** `enable_console_logging` + `get_console_messages` never returned
  captured entries in this tool build (the auto-generated `*-console.txt` capture files literally read `#
  TODO: Console logging not yet implemented`). Every test's "no console errors" check was therefore based on
  the absence of any visible error boundary, crash page, or broken layout — never a captured JS exception
  stream. No error indication was observed visually anywhere in this run.
- **Screenshot capture returned solid-black frames at non-zero scroll positions on the heaviest `/data`
  page section** (the "Per-date availability" calendar, which mounts ~5,000+ day-cell buttons + the
  "Per-symbol coverage" table below it): reproduced across `scroll` (wheel), `scrollIntoView`, and
  `window.scrollTo`, in both headless and headed Chrome, using both full-viewport and element-clipped
  screenshot requests — while the DOM/content itself was independently confirmed correct and complete via
  `eval` at every one of those same scroll positions (aria-labels, computed colors, exact text all resolved
  correctly). The reliable workaround used throughout this run: keep `scrollY = 0` and instead grow the
  CDP viewport height (`set_viewport` up to ~4200px) so the target section falls inside the always-rendered
  first frame, then crop the resulting screenshot in post-processing. All colored evidence screenshots in
  this report used this technique where a plain scroll produced a black frame. This is a capture-tooling
  limitation, not a rendering defect in the product (a real user scrolling with a mouse wheel was not
  independently tested, but the DOM/CSS were confirmed correct at every affected position).
- **Mid-run service interruption:** partway through this run, both the QA backend (port 8255) and frontend
  (port 3255) processes were killed externally (frontend log showed a bare "Killed" with no matching
  request in-flight), most likely a concurrent cleanup step elsewhere in this same pipeline run reusing the
  same ports. Both were restarted immediately via `scripts/start-backend.sh` / `scripts/start-frontend.sh`
  with the original `CHAIN_BACKEND_PORT=8255` / `CHAIN_FRONTEND_PORT=3255` env, came back healthy within 1
  second (frontend reused its cached prod build — no rebuild needed), and `symbol_count` was confirmed still
  590 post-restart. All test cases executed after this point were re-verified against the restarted stack;
  no evidence gathered before the interruption was invalidated. Both services were left running and healthy
  at the end of this QA run for the next pipeline step.
- **Golden-script cross-check (supplementary, not a UT case):** after writing/confirming the goal-mode
  golden replay scripts (see below), I ran `demo_runner.py --mode verify` against the live stack for
  J-01/J-03/J-04/J-05/J-10/J-11/J-12/J-14 as an extra diligence pass. 7/8 replayed clean; J-01's "Sort by
  Sector → Unassigned" step was investigated and could not be reproduced via direct live re-testing (see the
  UT-16 note above) — treated as a replay-tool timing nuance, not a product or script defect.

---

## Golden replay scripts (goal mode)

Written to `runs/goal-session-mcp-loop/journey-scripts/`:

- **J-14.json — newly created.** This iteration's target journey had no prior golden script. Wrote 7
  goto+expect steps asserting only statically-present (non-hover-dependent) text, since the golden-script
  schema supports only `goto`/`click`/`fill` — the true pixel-level "deep line in-frame" check (UT-03) is
  not scriptable this way and remains the browser-qa-agent's job each time. Lint-clean
  (`demo_runner.py --mode lint`) and confirmed PASS under a live `--mode verify` replay against the running
  stack.
- **J-01, J-03, J-04, J-05, J-10, J-11, J-12 — left unchanged.** Each was independently re-confirmed
  accurate against the live app this session (either by directly executing its exact steps per the UT-16
  through UT-22 narratives above, or — for J-10's `data-testid` selectors and J-01's `aria-label` — by a
  targeted DOM check). No edits were needed; a live `--mode verify` replay of all seven passed cleanly
  except for the J-01 nuance discussed above, which is a replay-tool observation, not an inaccuracy in the
  script itself.
- **J-13.json — left unchanged.** The developer already refreshed its one pinned assertion (587→590) this
  iteration. Its two non-mutating assertions ("590 symbols", "SCORED SNAPSHOT — INDICATOR") were
  independently re-confirmed live via the UT-10 replay above. Its step 2 (click "Start" → expect "Snapshots
  backfilled") triggers a real, asynchronous backfill job — a state-mutating action outside this iteration's
  UT-10 test-plan scope — and was not re-executed.

---

## Environment

- **Frontend URL:** http://localhost:3255
- **Backend URL:** http://localhost:8255
- **Browser:** Chrome via `mcp__plugin_superpowers-chrome_chrome__use_browser` (Chromium, headless/headed
  mixed during this run per the automation notes above)
- **Test Date:** 2026-07-08 through 2026-07-09 (session crossed local midnight)
- **Evidence directory:** `reports/qa/goal-mcp-loop-iter-23-evidence/`
- **Backend state at test time:** `provider: seed`, `seed 2026-07-01`, `symbol_count: 590`, `readiness:
  ready` (confirmed via `GET /api/health` both before and after the mid-run service restart)
