# Phase goal-i_can_see_the_wealthy_future_forever-iter-9 — UI Test Results

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-9
**Date:** 2026-06-02
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

**Overall:** 15/15 tests passed (0 failed, 0 skipped)

All 10 P1 tests pass (UT-01, 02, 03, 05, 08, 09, 10, 11, 13, 14) — the required bar for a PASS verdict. The two new detected patterns (`pullback_to_rising_dma`, `flat_base_breakout`) are filterable on `/stocks`, badged with server reason + pivot + invalidation tooltips on the leaderboard and the stock detail, documented on `/methodology` (auto-rendered from the config catalog), and surfaced as pattern-vs-non-pattern forward-return breakdowns with sample size `n` on `/system-health`. VCP and the Sector/Setup filters regress cleanly.

---

## Method note (evidence integrity)

Per the iter-9 spec NOTES (iter-6 browser-concurrency + byte-identical-screenshot lessons), every assertion below is grounded on a **live DOM assertion** (`eval` of filtered row counts / badge text / tooltip attributes / cohort `n`) captured immediately before each screenshot — not on screenshots alone. Frontend values were cross-checked against the backend API (`/api/stocks`, `/api/stocks/{ticker}`, `/api/system-health`, `/api/methodology`).

- **All 15 UT evidence screenshots are byte-distinct** (verified by sha256) and **none collide** with the QA agent's pre-existing `TC-*` screenshots.
- **Tooling caveats (not product defects):**
  1. The Chrome-MCP explicit `screenshot` action returned a **stale cached frame** (byte-identical to a prior QA-agent capture). Evidence therefore uses the tool's per-action **auto-captured** frames, which are fresh and distinct.
  2. The Chrome-MCP **console capture is a stub** ("Console logging not yet implemented") on this build, so console messages could not be inspected directly. No error boundaries, "Backend unavailable" cards, or blank screens appeared on any route, and every rendered value matched the backend.
  3. The native `<select>` filters are React-controlled; rapidly re-selecting the **same** select twice corrupts its state. Mitigation: a fresh page navigation precedes each filter test (resetting two **different** selects sequentially works fine — see UT-14).

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-01 | Leaderboard loads with Pattern filter | smoke | P1 | h1 "Stocks"; Sector/Setup/Pattern filters; Pattern default "All patterns"; full column set; ≥1 row; no error card | h1 `Stocks`; 4 selects incl `aria-label="Filter by detected pattern"` default "All patterns"; columns `# Ticker Sector Leadership Entry Quality Risk Setup Reason`; 122 rows; counter "122 / 122"; no error | PASS | `UT-01-stocks-loaded.png` |
| UT-02 | Pattern dropdown offers 3 patterns ×2 modes | happy-path | P1 | "All patterns" + 3 optgroups each with "… only" / "Not …" | optgroups **VCP** (VCP only / Not VCP), **Pullback to rising DMA** (only / Not), **Flat-base breakout** (only / Not) + loose "All patterns" | PASS | DOM assert (006-eval) + `UT-01-stocks-loaded.png` |
| UT-03 | "Pullback only" narrows to flagged rows | happy-path | P1 | count drops ≤ total; every row has Pullback badge; no unflagged row | "122 / 122" → "9 / 122"; exactly ABNB,ANET,COST,ENTG,ETN,GEV,TPH,VKTX,VRT; all 9 carry Pullback badge | PASS | `UT-03-before-all-patterns-122.png`, `UT-03-after-pullback-only-9.png` |
| UT-04 | "Not Flat-base" removes flat-base rows | happy-path | P2 | flagged tickers (TPH/GS/ADI) absent; no Flat base badge; count = total − flagged | Flat-base only → TPH,GS,ADI; Not Flat-base → "119 / 122", none of TPH/GS/ADI present, zero Flat base badges | PASS | `UT-04-flatbase-only-3.png`, `UT-04-not-flatbase-119.png` |
| UT-05 | Pullback/Flat base badge + reason tooltip | happy-path | P1 | teal badge, help cursor, native tooltip with reason + "Pivot $N." + invalidation; plain prose | Pullback badge `rgb(79,209,197)`, `cursor:help`, `title`="Pulled back to a rising 50-day MA … Pivot $46.99. Pullback invalid … at $46.71"; all 9 badges teal; matches API | PASS | `UT-05-pullback-badges-teal.png` |
| UT-06 | Pattern glossary info tooltip | happy-path | P2 | info icon next to badge; reveals glossary definition; label "Definition of the Flat-base breakout pattern" | Click button `aria-label="Definition of the Flat-base breakout pattern"` → `aria-expanded=true`, `role="tooltip"` shows exact meaning "A shallow, sideways base built at the highs …" | PASS | `UT-06-flatbase-glossary-tooltip.png` |
| UT-07 | Pattern-aware empty state | validation | P2 | "No stocks match these filters"; description names active pattern + no-fabrication clause; no rows | Setup=Actionable + Pullback-only → 0 rows; "No Pullback to rising DMA-flagged name is currently "Actionable". No rows are fabricated to fill the view — clear a filter to see more." | PASS | `UT-07-empty-state-pullback-named.png` |
| UT-08 | Detail header pattern badge(s) | happy-path | P1 | heading = ticker; setup badge + teal pattern badge; tooltip matches leaderboard; sector + "as of" | `/stocks/TPH`, h1 "TPH"; header chips `Pullback-watch` + `Pullback` + `Flat base` + `as of 2026-05-28`; sector Consumer Discretionary; header Pullback `title` identical to leaderboard | PASS | `UT-08-detail-TPH-header-badges.png` |
| UT-09 | Detail pattern card (pivot + invalidation) | happy-path | P1 | "Flat-base breakout" card w/ teal badge, reason, "Pivot (breakout level)" $N, amber invalidation; VCP card still present | Flat-base card: teal `Flat base` badge, reason, "Pivot (breakout level)" **$46.99**, amber (`rgb(251,191,36)`) "… invalid below the base low at $46.74"; VCP card present showing "No VCP pattern detected." | PASS | `UT-09-detail-TPH-pattern-cards.png` |
| UT-10 | System Health two new panels + n/NA | happy-path | P1 | both new panels after VCP panel; 2 cohort rows each w/ mean + n; NA/⚠ below min-sample | Panels in order VCP→Pullback→Flat-base; Pullback-to-DMA −0.27% n=163 / non-Pullback +2.39% n=1055; Flat-base +0.91% n=48 / non-Flat-base +2.08% n=1170; VCP cohort n=27 ⚠ (low-sample); all values match API | PASS | `UT-10-system-health-pattern-panels.png` |
| UT-11 | Methodology two new pattern cards | happy-path | P1 | both cards w/ teal Pattern chip, meaning, Thresholds (live values), Example | "Pullback to a rising DMA" + "Flat-base breakout" cards; teal `Pattern` chip; meaning paragraph; Thresholds (50-day, ≥1.5%, 25 bars, ≤15%, ≤6% — concrete); "Example:" line | PASS | `UT-11-methodology-new-pattern-cards.png` |
| UT-12 | Methodology subtitle is generic | ux | P3 | subtitle generic, not VCP-specific; contains "What every setup status and detected price pattern mean" | Subtitle: "What every setup status and detected price pattern mean — with the exact config thresholds …"; no "the VCP pattern" phrasing | PASS | `UT-12-methodology-subtitle-generic.png` |
| UT-13 | VCP filter/badge/glossary/panel regression | regression | P1 | VCP only → only VCP rows + badge/tooltip; Not VCP → hidden; VCP methodology card + system-health panel intact | VCP only → "4 / 122" ORCL,STX,TSLA,TSM, teal badge + tooltip "… Pivot $905.39. VCP invalid …"; Not VCP → "118 / 122" (4 gone); VCP card + "Forward return: VCP vs non-VCP" panel render | PASS | `UT-13-vcp-only-4rows.png` |
| UT-14 | Sector + Setup filters still compose | regression | P1 | sector narrows; setup further narrows (AND); reset restores full; counter tracks | Technology → "58 / 122" (all Tech); +Avoid → "40 / 122" (all Tech AND Avoid); reset both → "122 / 122" | PASS | `UT-14-sector-setup-composed.png` |
| UT-15 | Glossary lists 6 setups + 3 patterns | regression | P2 | exactly 6 Setup chips + 3 Pattern chips; no dup/missing | 6 Setup chips + 3 Pattern chips (VCP, Pullback to a rising DMA, Flat-base breakout); pattern chips teal | PASS | DOM assert (044-eval) + `UT-11-…`, `UT-12-…` |

---

## Passed Tests

### UT-01 — Stock Leaderboard loads with the new Pattern filter
**Verdict:** PASS · **Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever-iter-9-evidence/UT-01-stocks-loaded.png`
- URL `http://localhost:3835/stocks`, `<h1>` = "Stocks".
- Filter bar has four `<select>`s: as-of date, "Filter by sector", "Filter by setup status", and **"Filter by detected pattern"** (default option text "All patterns").
- Table columns exactly: `# · Ticker · Sector · Leadership · Entry Quality · Risk · Setup · Reason`; 122 rows; counter "122 / 122".
- No "Backend unavailable" card, no blank screen, no error boundary.

### UT-02 — Pattern dropdown offers all three patterns with only/not options
**Verdict:** PASS · **Evidence:** DOM assertion (auto-capture 006-eval) + `UT-01-stocks-loaded.png`
- The pattern `<select>` contains a loose option "All patterns" (`__all__`) plus three `<optgroup>`s:
  - **VCP** → "VCP only" (`vcp__only`), "Not VCP" (`vcp__none`)
  - **Pullback to rising DMA** → "Pullback to rising DMA only" (`pullback_to_rising_dma__only`), "Not Pullback to rising DMA" (`pullback_to_rising_dma__none`)
  - **Flat-base breakout** → "Flat-base breakout only" (`flat_base_breakout__only`), "Not Flat-base breakout" (`flat_base_breakout__none`)

### UT-03 — Filtering by "Pullback to rising DMA only" narrows to flagged rows
**Verdict:** PASS · **Evidence:** `UT-03-before-all-patterns-122.png`, `UT-03-after-pullback-only-9.png`
- Counter "122 / 122" → "9 / 122". The 9 rows are exactly ABNB, ANET, COST, ENTG, ETN, GEV, TPH, VKTX, VRT — identical to the backend's `pullback_to_rising_dma.flagged` set. Every visible row carries a Pullback badge; no empty state.

### UT-04 — Filtering by "Not Flat-base breakout" removes flat-base rows
**Verdict:** PASS · **Evidence:** `UT-04-flatbase-only-3.png`, `UT-04-not-flatbase-119.png`
- "Flat-base breakout only" → TPH, GS, ADI (3, all with Flat base badge). "Not Flat-base breakout" → "119 / 122"; none of TPH/GS/ADI present; zero Flat base badges remain; pullback ticker VRT still present (only flat-base excluded).

### UT-05 — Pullback / Flat base badges render with reason tooltip
**Verdict:** PASS · **Evidence:** `UT-05-pullback-badges-teal.png`
- Pullback badge color `rgb(79,209,197)` (teal), `cursor:help`, native `title` = "Pulled back to a rising 50-day MA (up 17.8% over 40 bars); close 0.5% above the MA, 0% off the recent high on volume 104% of the trend average. **Pivot $46.99.** Pullback invalid on a decisive close below the rising 50-day MA at $46.71" — plain prose, matches `/api/stocks/TPH`. All 9 pullback badges verified teal. (Tooltip is a native `title`; verified by attribute + `cursor:help` since OS-rendered tooltips don't appear in DOM screenshots.)

### UT-06 — Pattern glossary info tooltip shows the definition
**Verdict:** PASS · **Evidence:** `UT-06-flatbase-glossary-tooltip.png`
- Clicking the info button `aria-label="Definition of the Flat-base breakout pattern"` sets `aria-expanded="true"` and reveals a `role="tooltip"` panel: "A shallow, sideways base built at the highs with price coiled just under the pivot (the base high) on building volume — breakout-ready. A detected PATTERN that rides ALONGSIDE the setup status — it never by itself makes a name Actionable." — identical to the `/methodology` meaning text.

### UT-07 — Pattern-aware empty state names the active filter
**Verdict:** PASS · **Evidence:** `UT-07-empty-state-pullback-named.png`
- Setup="Actionable" + Pattern="Pullback to rising DMA only" → 0 rows, no table. Empty-state card: title "No stocks match these filters"; description "No Pullback to rising DMA-flagged name is currently "Actionable". No rows are fabricated to fill the view — clear a filter to see more." — names the active pattern and ends with the honest no-fabrication clause.

### UT-08 — Stock detail header shows a badge per flagged pattern
**Verdict:** PASS · **Evidence:** `UT-08-detail-TPH-header-badges.png`
- Clicking the TPH ticker link navigated to `/stocks/TPH`, h1 "TPH". Header card chips in order: `Pullback-watch` (setup status) → `Pullback` → `Flat base` (teal pattern badges) → `as of 2026-05-28`; sector "Consumer Discretionary / Homebuilders" present. The header Pullback badge `title` is identical to the leaderboard tooltip (reason + Pivot $46.99 + invalidation at $46.71).

### UT-09 — Stock detail renders a dedicated pattern card with pivot and invalidation
**Verdict:** PASS · **Evidence:** `UT-09-detail-TPH-pattern-cards.png`
- "Flat-base breakout" card: teal `Flat base` badge, server reason text, "Pivot (breakout level)" **$46.99**, and an amber (`rgb(251,191,36)`) Invalidation note "Flat-base breakout invalid below the base low at $46.74". The "VCP — Volatility Contraction Pattern" card is still present, showing its honest "No VCP pattern detected." state (TPH is not VCP-flagged). The Pullback card is likewise present with its own Pivot $46.99 + invalidation.

### UT-10 — System Health renders both new forward-return panels with n / NA
**Verdict:** PASS · **Evidence:** `UT-10-system-health-pattern-panels.png`
- Panels render in order: "Forward return: VCP vs non-VCP" → "Forward return: Pullback-to-rising-DMA vs not" → "Forward return: Flat-base breakout vs not".
  - Pullback panel: **Pullback-to-DMA −0.27% n=163**, **non-Pullback +2.39% n=1055**.
  - Flat-base panel: **Flat-base +0.91% n=48**, **non-Flat-base +2.08% n=1170**.
  - All values match `/api/system-health` exactly. The low-sample ⚠ marker correctly appears on the VCP cohort (n=27 < min-sample 30) and is correctly absent from the well-sampled new cohorts — honest, never fabricated.

### UT-11 — Methodology auto-renders the two new pattern glossary cards
**Verdict:** PASS · **Evidence:** `UT-11-methodology-new-pattern-cards.png`
- "Pullback to a rising DMA" card: teal `Pattern` chip, meaning paragraph, Thresholds list (Moving-average basis=50-day, Rising over 40 bars, Min DMA slope≥1.5%, …), Example line. "Flat-base breakout" card: teal `Pattern` chip, meaning, Thresholds (Base window 25 bars, Max base depth≤15%, Within pivot≤6%), Example line. All threshold numbers are concrete live config values (none "undefined"/blank).
- **Minor wording note (not a defect):** the rendered card title is "Pullback **to a** rising DMA" (from the config catalog), whereas the test plan wrote "Pullback to rising DMA". The card renders correctly and is the correct pattern; the leaderboard glossary label uses "Pullback to rising DMA". No functional impact.

### UT-12 — Methodology subtitle is generic, not VCP-specific
**Verdict:** PASS · **Evidence:** `UT-12-methodology-subtitle-generic.png`
- Subtitle reads "What every setup status and detected price pattern mean — with the exact config thresholds that define each (read live from config, so they always match the scanner) and a worked example." Does not contain "the VCP pattern".

### UT-13 — Regression: VCP filter, badge, and glossary still work unchanged
**Verdict:** PASS · **Evidence:** `UT-13-vcp-only-4rows.png`
- "VCP only" → "4 / 122" (ORCL, STX, TSLA, TSM), each with a teal VCP badge; VCP badge `cursor:help` + tooltip "… Pivot $905.39. VCP invalid below the last-contraction low …".
- "Not VCP" → "118 / 122"; all 4 VCP tickers gone; no VCP badge.
- `/methodology` VCP card present with meaning/thresholds/example; `/system-health` "Forward return: VCP vs non-VCP" panel renders (VCP +3.18% n=27 ⚠, non-VCP +2.01% n=1191). VCP behaves exactly as in prior iterations.

### UT-14 — Regression: Sector + Setup filters still compose with the new Pattern filter
**Verdict:** PASS · **Evidence:** `UT-14-sector-setup-composed.png`
- Sector="Technology" → "58 / 122" (all 58 rows Technology). Adding Setup="Avoid" → "40 / 122" (every row both Technology AND Avoid). Resetting both selects → "122 / 122". The `<visible> / <total>` counter tracked correctly at each step (122 → 58 → 40 → 122). Sector + Setup + Pattern compose with AND semantics without interfering.

### UT-15 — Methodology glossary lists 6 setups + 3 patterns
**Verdict:** PASS · **Evidence:** DOM assertion (auto-capture 044-eval) + `UT-11-methodology-new-pattern-cards.png`, `UT-12-methodology-subtitle-generic.png`
- Exactly **6** cards carry a "Setup" chip (Actionable, Breakout-watch, Pullback-watch, Extended, Avoid, Risk-off-watchlist) and exactly **3** carry a "Pattern" chip (VCP, Pullback to a rising DMA, Flat-base breakout). No duplicate or missing pattern card. Pattern chips render teal.

---

## Failed Tests

None.

---

## Skipped Tests

None.

---

## Anti-goal spot-checks observed during browser QA (informational)

- **Pattern-not-status:** the new pattern badges ride in the Setup column **beside** the setup-status badge (e.g. TPH shows `Pullback-watch` + `Pullback` + `Flat base`); the patterns never replace the setup status. The pattern glossary tooltips explicitly state each "rides ALONGSIDE the setup status — it never by itself makes a name Actionable."
- **Single source of truth / no recompute:** every frontend value (badge flags, reasons, pivots, invalidation levels, forward-return means, sample sizes) matched the backend API responses verbatim; the client only re-displays and filters.
- **Honest NA / sample size:** System Health shows `n` on every cohort and a ⚠ low-sample marker on the VCP cohort (n=27 < 30); the new-pattern cohorts (n=48–1170) show real numbers — none fabricated.

---

## Environment

- **Frontend URL:** http://localhost:3835
- **Backend:** http://localhost:8835 (`/api/stocks`, `/api/stocks/{ticker}`, `/api/system-health`, `/api/methodology` reachable; as-of snapshot 2026-05-28; provider: seed, 122 ranked rows / 158 symbols)
- **Browser:** Chrome via `mcp__plugin_superpowers-chrome_chrome__use_browser` (CDP), viewports 1440×1100 and 1280×920
- **Test Date:** 2026-06-02
- **Evidence directory:** `reports/qa/goal-i_can_see_the_wealthy_future_forever-iter-9-evidence/` (15 byte-distinct UT screenshots; auto-captured `.md`/`.html`/`.png` per action retained in the Chrome session dir)
