# Phase goal-i_can_see_the_wealthy_future_forever-iter-6 — UI Test Results

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-6
**Date:** 2026-06-02
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

**Overall:** 18/18 tests passed (0 failed, 0 skipped)

All P1 tests pass. The two iteration journeys are confirmed end-to-end through real multi-step browser flows (not single page-loads): J-20 (Stock-Detail chart full-path-through-latest, display-only with an as-of divider) and J-21 (Backtest leadership cohorts below Return Attribution with one horizon selector re-pointing realized-return columns). Both critical anti-goal seams were verified live: **No-lookahead** (the ≤D scores/setup/VCP/invalidation are byte-equal to the as-of snapshot regardless of the displayed forward region) and **Attribution-read-only / single date control / honest NA** (returns are read-only projections, the horizon switch triggers no refetch, and missing data renders "—", never a fabricated 0%).

---

## Execution note (shared-browser concurrency — resolved)

The `qa` agent (QA-validation mode, pid 175018) was running its own Chrome MCP checks **concurrently** on the same shared single-tab Chrome (port 9222). This initially corrupted captures (a "Latest" navigation came back showing the qa agent's historical state; an eval landed on the qa agent's `/backtest`). Rather than race it (which would have corrupted both runs), I **waited for the qa agent to vacate the browser** (it moved on to the backend pytest suite, then exited), then ran all 18 tests cleanly on a single dedicated tab, verifying live state (`data-testid="asof-indicator"`, URL, values) immediately before every capture. No report-file collision: the qa agent writes `reports/qa/<phase>-qa.md`; this file is separate. The evidence dir also contains the qa agent's own `TC-*.png` screenshots — those are its artifacts; this report references only the `UT-*` files I captured.

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-01 | Stock-detail loads with chart | smoke | P1 | Page renders, NVDA heading, candles+volume, no forward region at Latest | NVDA renders at Latest; chart canvas 1520×292 with visible up/down candles + volume; scores 47.48/66.24/33.79; invalidation $198.73; no forward legend/caption | PASS | UT-01-latest-nvda.png |
| UT-02 | Muted forward region at historical as-of | happy-path | P1 | ≤D candles coloured, >D candles greyed; chart extends to latest; panels render | At 2025-04-04: header "1356 bars · as of 2025-04-04", x-axis runs through 2026; candles after the boundary render greyed/muted, ≤D candles green/red; score/setup/VCP panels render | PASS | UT-02-historical-forward-region.png, UT-02-UT-03-chart-divider-zoom.png |
| UT-03 | As-of divider marker at boundary | happy-path | P1 | Arrow marker "as-of 2025-04-04" at the last ≤D candle, at the colour↔grey transition | Amber arrow marker labelled "as-of 2025-04-04" sits exactly at the boundary; coloured candles to its left, greyed candles to its right | PASS | UT-03-divider-marker-crop.png |
| UT-04 | Forward swatch in legend | happy-path | P2 | Legend entry "Forward — after as-of {date} (display only)" with muted swatch | Legend shows "Forward — after as-of 2025-04-04 (display only)" with a muted swatch; date matches the selected as-of | PASS | UT-02-UT-03-chart-divider-zoom.png |
| UT-05 | Display-only caption above chart | happy-path | P2 | One-line caption stating forward bars are display-only and don't affect scores/setup/VCP | Caption: "Full path through 2026-05-28. Bars after the as-of date 2025-04-04 are display-only — they don't affect the scores, setup, or VCP flag below (those read the as-of snapshot, bars ≤ 2025-04-04)." | PASS | UT-02-UT-03-chart-divider-zoom.png |
| UT-06 | Scores/VCP unchanged by forward region | regression | P1 | Displayed scores/setup/VCP/invalidation == snapshot API for as_of=2025-04-04 (forward region doesn't shift them) | Displayed @2025-04-04: Leadership 43.39/E, Entry 37.36, Risk 50.34, setup "Risk-off-watchlist", VCP not flagged, invalidation $121.27 — **exactly equal** to `GET /api/stocks/NVDA?as_of=2025-04-04`; legitimately differ from Latest (47.48/66.24/33.79, "Avoid", $198.73) by date | PASS | UT-02-historical-forward-region.png |
| UT-07 | Latest as-of: no forward region | regression | P1 | No greyed candles, no marker, no "after as-of" legend, no caption | Switched switcher back to Latest: indicator "Latest", invalidation $198.73, "1356 bars · as of 2026-05-28", forward legend ABSENT, caption ABSENT, candles coloured end-to-end | PASS | UT-07-latest-no-forward.png |
| UT-08 | Backtest section order correct | happy-path | P1 | As-of scan summary → Forward-test scorecard → Return Attribution → Top Sectors → Top Themes → Ranked Cohort | DOM heading order: As-of scan summary → Forward-test scorecard → Return attribution (+ its 4 sub-slices) → Leadership cohorts (Top Sectors, Top Themes, Ranked cohort). The three lists are BELOW attribution | PASS | UT-08-UT-09-backtest-top-order.png, UT-08-backtest-fullpage-h1.png |
| UT-09 | As-of scan summary = regime + counts only | happy-path | P2 | Summary shows regime + candidate counts only; no leadership lists | Summary: "Market Regime Risk-off 6.30 / 100" + "Candidate Counts: Actionable 0 / Breakout-watch 0 / Pullback-watch 0"; contains no Top Sectors/Themes/Cohort | PASS | UT-08-UT-09-backtest-top-order.png |
| UT-10 | Top Sectors return column | happy-path | P1 | Each sector row shows a realized return (or "—"/NA); equals the sector ETF's forward return | At 2025-04-04 / Fwd 1d: XLP −1.16%, XLU −1.53%, XLF −0.25%, XLE −0.65%, CIBR "—" (n=0) — **exact match** to `/api/backtest` leadership_returns.sectors | PASS | UT-10-11-12-leadership-returns-h1.png |
| UT-11 | Top Themes member-mean + n column | happy-path | P1 | Each theme row shows equal-weight member-mean return with sample count n; NA when 0 | At Fwd 1d: Defense +0.01% (n=10), Megacap Leaders +0.21% (n=20), Homebuilders −4.89% (n=9), Software Cloud +0.12% (n=15), Cybersecurity +0.28% (n=11) — **exact match** to leadership_returns.themes (equal-weight member mean + n) | PASS | UT-10-11-12-leadership-returns-h1.png |
| UT-12 | Ranked Cohort per-ticker return | happy-path | P1 | Every cohort row resolves a per-ticker return or "—"/NA; no fabricated 0% | At Fwd 1d: KTOS +1.51%, NOC −0.81%, PLTR +5.17%, NFLX +1.40%, RTX −0.11%, V −0.26%, INTC −1.41%, OKTA −0.75%, MSTR −8.67%, ZS +3.08% — **exact match** to leadership_returns.cohort; missing data shows "—", never 0% | PASS | UT-10-11-12-leadership-returns-h1.png |
| UT-13 | Cohort table horizontal scroll @640px | ux | P3 | Table horizontally scrollable revealing the new column; layout not broken | At 640px: container `overflow-x:auto`, scrollWidth 640 > clientWidth 351 (overflows), scrollLeft 0→289, header `[#, Ticker, Setup, Leadership, Fwd 60d]`; scrolled shot reveals the FWD 60D column; single-column layout intact | PASS | UT-13-narrow-cohort-crop.png, UT-13-narrow-fullpage.png |
| UT-14 | One selector re-points all columns + attribution | happy-path | P1 | One horizon selector updates BOTH attribution AND all 3 return columns; no reload/refetch; as-of unchanged | Clicking 60d re-pointed simultaneously: XLP −1.16%→+5.51%, KTOS +1.51%→+55.57%, attribution Technology +1.52%→+48.02% (Financials +0.11%→+69.27%). Network spy during switch: only 3× `/api/health` (background poller), **no `/api/backtest` refetch**; as-of stayed "Viewing as-of 2025-04-04 (historical)", URL unchanged | PASS | UT-10-11-12-leadership-returns-h1.png (before), UT-14-leadership-returns-h60.png (after), UT-14-backtest-fullpage-h60.png |
| UT-15 | Honest NA at recent as-of | validation | P2 | Rows lacking post-as-of data show "—"/NA; no fabricated numeric | At 2026-02-27 / Fwd 60d: cohort #1 **TPH = "— n=0"** (NA) while TER +21.64%, CIEN +72.75% etc. have real returns; sector **ITA = "—"** (NA). Caption states "'—' means the window has not elapsed in the seed (NA); nothing is fabricated." | PASS | UT-15-recent-asof-NA-cohort.png, UT-15-recent-asof-NA-fullpage.png |
| UT-16 | Low-sample ⚠ marker | validation | P3 | Rows with n below the minimum show the existing low-sample ⚠ (no new ad-hoc style) | min_sample=30; every per-name row (n=1 sectors/cohort; themes n=9–27) carries the `n=… ⚠` warn-token marker — the same treatment used by the Forward-test scorecard | PASS | UT-10-11-12-leadership-returns-h1.png |
| UT-17 | No page-local date control | regression | P1 | Exactly one date control (global as-of switcher); horizon selector lists horizons not dates | Page has exactly ONE `<select>` ("View as-of date"); 0 date inputs / calendars; only that select has YYYY-MM-DD options; horizon buttons are 1d/5d/10d/20d/60d (horizons); changing horizon doesn't change the as-of (UT-14) | PASS | UT-08-backtest-fullpage-h1.png |
| UT-18 | Core journeys still work | regression | P1 | Stock-detail panels + backtest scorecard/attribution render; one global control drives both pages | At Latest: `/backtest` renders scorecard + Return attribution + Leadership cohorts, no error banner; in-app nav `/backtest → /stocks → /stocks/NVDA` preserved as-of=Latest and rendered NVDA panels (Leadership 47.48, $198.73, VCP none, setup "Avoid", chart) | PASS | UT-18-backtest-latest-renders.png |

---

## Passed Tests (detail)

### J-20 — Stock-Detail chart through latest (display-only)

#### UT-01 — Stock-detail loads with chart (smoke, P1)
**Verdict:** PASS — `reports/qa/<phase>-evidence/UT-01-latest-nvda.png`
- `/stocks/NVDA` at default Latest: "NVDA" heading, chart canvas present (1520×292) with visible green/red candles + volume bars across 2021→2026, no greyed region. Scores 47.48 / 66.24 / 33.79, invalidation $198.73, "No VCP pattern detected". No forward legend, no display-only caption.

#### UT-02 — Muted forward region at historical as-of (happy-path, P1)
**Verdict:** PASS — `UT-02-historical-forward-region.png`, `UT-02-UT-03-chart-divider-zoom.png`
- Set the global switcher to 2025-04-04 (in-app, no F5). Header reads "1356 bars · as of 2025-04-04"; the chart x-axis extends through 2026 (does not stop at the as-of). Candles dated > 2025-04-04 render greyed/muted (volume too); candles ≤ 2025-04-04 render normal green/red. The score/setup/VCP panels below still render.

#### UT-03 — As-of divider marker at boundary (happy-path, P1)
**Verdict:** PASS — `UT-03-divider-marker-crop.png`
- A zoomed crop of the boundary shows an amber arrow marker labelled **"as-of 2025-04-04"** sitting at the last ≤D candle, precisely at the transition between the coloured region (left) and the greyed forward region (right).

#### UT-04 — Forward swatch in legend (happy-path, P2)
**Verdict:** PASS — `UT-02-UT-03-chart-divider-zoom.png`
- Legend row contains **"Forward — after as-of 2025-04-04 (display only)"** with a muted swatch; the date matches the selected as-of.

#### UT-05 — Display-only caption above chart (happy-path, P2)
**Verdict:** PASS — `UT-02-UT-03-chart-divider-zoom.png`
- One-line caption directly above the chart: "Full path through 2026-05-28. Bars after the as-of date 2025-04-04 are display-only — they don't affect the scores, setup, or VCP flag below (those read the as-of snapshot, bars ≤ 2025-04-04)." Present only because a forward region exists at this historical as-of (absent at Latest — see UT-07).

#### UT-06 — Scores/VCP unchanged by forward region (regression / no-lookahead, P1)
**Verdict:** PASS — `UT-02-historical-forward-region.png`
- Displayed at 2025-04-04: Leadership **43.39** (E), Entry Quality **37.36**, Risk **50.34**, setup "Risk-off-watchlist", VCP not flagged, invalidation **$121.27**. These are **byte-equal** to `GET /api/stocks/NVDA?as_of=2025-04-04` (the immutable snapshot row). They legitimately differ from the Latest view (47.48 / 66.24 / 33.79, "Avoid", $198.73) because the snapshot is date-scoped — but the presence of the greyed forward candles did **not** shift any score / setup / VCP / invalidation. No-lookahead carve-out holds at the UI layer.

#### UT-07 — Latest as-of: no forward region (regression / edge, P1)
**Verdict:** PASS — `UT-07-latest-no-forward.png`
- Returning the switcher to Latest: indicator "Latest", invalidation $198.73, header "1356 bars · as of 2026-05-28". No greyed forward candles, no as-of divider beyond the chart end, the "Forward — after as-of …" legend entry is ABSENT, the display-only caption is ABSENT. Chart matches the pre-iter-6 Latest view.

### J-21 — Backtest leadership cohorts + horizon-linked realized returns

#### UT-08 — Backtest section order correct (happy-path, P1)
**Verdict:** PASS — `UT-08-UT-09-backtest-top-order.png`, `UT-08-backtest-fullpage-h1.png`
- Reached `/backtest` via **in-app nav** from `/stocks/NVDA` (as-of 2025-04-04 preserved). Top-to-bottom: **As-of scan summary → Forward-test scorecard → Return attribution** (with its 4 sub-slices) **→ Leadership cohorts (Top Sectors, Top Themes, Ranked cohort)**. The three leadership lists are BELOW Return Attribution.

#### UT-09 — As-of scan summary = regime + counts only (happy-path, P2)
**Verdict:** PASS — `UT-08-UT-09-backtest-top-order.png`
- Top summary shows "Market Regime: Risk-off 6.30 / 100" and "Candidate Counts: Actionable 0 / Breakout-watch 0 / Pullback-watch 0" only — no leadership lists.

#### UT-10 — Top Sectors return column (happy-path, P1)
**Verdict:** PASS — `UT-10-11-12-leadership-returns-h1.png`
- Each sector row carries a "Fwd 1d" realized return. Rendered = API leadership_returns.sectors exactly: XLP −1.16%, XLU −1.53%, XLF −0.25%, XLE −0.65%, CIBR "—" (n=0, honest NA — CIBR is not a GICS sector ETF, so it has no stored sector-ETF return; rendered as NA, never fabricated).

#### UT-11 — Top Themes member-mean + n column (happy-path, P1)
**Verdict:** PASS — `UT-10-11-12-leadership-returns-h1.png`
- Each theme row shows the equal-weight member-mean return + sample count: Defense +0.01% (n=10), Megacap Leaders +0.21% (n=20), Homebuilders −4.89% (n=9), Software Cloud +0.12% (n=15), Cybersecurity +0.28% (n=11). Exact match to leadership_returns.themes.

#### UT-12 — Ranked Cohort per-ticker return (happy-path, P1)
**Verdict:** PASS — `UT-10-11-12-leadership-returns-h1.png`
- Every cohort row resolves a per-ticker return: KTOS +1.51%, NOC −0.81%, PLTR +5.17%, NFLX +1.40%, RTX −0.11%, V −0.26%, INTC −1.41%, OKTA −0.75%, MSTR −8.67%, ZS +3.08% — exact match to leadership_returns.cohort. Missing data renders "—" (see UT-15), never a fabricated 0%.

#### UT-13 — Cohort table horizontal scroll @640px (ux, P3)
**Verdict:** PASS — `UT-13-narrow-cohort-crop.png`, `UT-13-narrow-fullpage.png`
- At a 640px viewport the Ranked-cohort table's container has `overflow-x:auto`, scrollWidth 640 > clientWidth 351 (it overflows), and scrolls right by 289px. The header is `[#, Ticker, Setup, Leadership, Fwd 60d]`; the scrolled screenshot reveals the FWD 60D column. The page's single-column narrow layout is not broken.

#### UT-14 — One selector re-points all columns + attribution (happy-path, P1 — defining proof)
**Verdict:** PASS — before: `UT-10-11-12-leadership-returns-h1.png`; after: `UT-14-leadership-returns-h60.png`, `UT-14-backtest-fullpage-h60.png`
- Clicking the single horizon view-selector from 1d → 60d simultaneously re-pointed: Top Sectors XLP −1.16% → +5.51%; Ranked Cohort KTOS +1.51% → +55.57%; Return Attribution by-sector Technology +1.52% → +48.02% (Financials +0.11% → +69.27%). A `window.fetch` spy recorded only 3× `/api/health` (the unrelated background badge poller) during the switch — **no `/api/backtest` / `/api/sectors` / `/api/stocks` / `/api/themes` refetch**. The global as-of switcher still read "Viewing as-of 2025-04-04 (historical)" and the URL did not change. One selector, attribution + all three lists, pure client-side view change.

#### UT-15 — Honest NA at recent as-of (validation, P2)
**Verdict:** PASS — `UT-15-recent-asof-NA-cohort.png`, `UT-15-recent-asof-NA-fullpage.png`
- At the recent as-of 2026-02-27 with horizon 60d (the 60-day window has not fully elapsed for every name), Ranked-cohort #1 **TPH = "— n=0"** (honest NA) while TER +21.64%, CIEN +72.75%, etc. show real returns; sector **ITA = "—"** (NA). The section caption states the "—" means the window has not elapsed (NA), nothing fabricated. No misleading 0% appears for missing data.

#### UT-16 — Low-sample ⚠ marker (validation, P3)
**Verdict:** PASS — `UT-10-11-12-leadership-returns-h1.png`
- min_sample = 30. The per-name leadership rows are inherently small-sample (sectors/cohort n=1; themes n=9–27), and each correctly carries the existing low-sample `n=… ⚠` warn-token marker — the SAME treatment used by the Forward-test scorecard (no new ad-hoc style). This honestly flags the per-row realized returns as single-observation / indicative rather than statistically robust.

#### UT-17 — No page-local date control (regression, P1)
**Verdict:** PASS — `UT-08-backtest-fullpage-h1.png`
- The Backtest page exposes exactly ONE `<select>` ("View as-of date" — the shared global switcher); zero `<input type=date>` / calendar widgets; only that one select has YYYY-MM-DD options. The horizon control is a set of buttons (1d / 5d / 10d / 20d / 60d) — horizons, not dates — and changing it leaves the as-of unchanged (UT-14). No second/page-local date picker exists.

#### UT-18 — Core journeys still work (regression, P1)
**Verdict:** PASS — `UT-18-backtest-latest-renders.png`
- At the default Latest as-of, `/backtest` renders the Forward-test scorecard + Return attribution + Leadership cohorts with no error banner. In-app navigation `/backtest → /stocks → /stocks/NVDA` preserved the global as-of (Latest) and rendered all stock-detail panels (Leadership 47.48, invalidation $198.73, "No VCP pattern detected", setup "Avoid", chart). The single global as-of control drives both pages without a broken page or missing data.

---

## Failed Tests

None.

---

## Skipped Tests

None.

---

## Cross-check sources (live backend, :8835)

- `GET /api/stocks/NVDA/bars?as_of=2025-04-04&through=latest` → 1356 bars (1069 ≤D + 287 forward, per-bar `is_forward`), `latest_date=2026-05-28`.
- `GET /api/stocks/NVDA?as_of=2025-04-04` (snapshot row) → Leadership 43.39/E, Entry 37.36, Risk 50.34, setup "Risk-off-watchlist", VCP not flagged, invalidation $121.27. (Latest: 47.48/66.24/33.79, "Avoid", $198.73.)
- `GET /api/backtest?as_of=2025-04-04` → `scorecard.by_horizon[*].leadership_returns` {sectors, themes, cohort}; horizons [1,5,10,20,60]; min_sample 30. Rendered columns matched these values at Fwd 1d and Fwd 60d.
- `GET /api/backtest?as_of=2026-02-27` → at horizon 60, cohort TPH `mean_return=null` (the lone NA), confirming the UI "—" is an honest NA from the stored data.

## Environment

- **Frontend URL:** http://localhost:3835 (Next.js dev; `NEXT_PUBLIC_API_URL` resolved to http://localhost:8835)
- **Backend:** http://localhost:8835 (health at `/api/health`: status ok, provider seed, seed_latest_date 2026-05-28, 158 symbols)
- **Browser:** Chrome via MCP (`mcp__plugin_superpowers-chrome_chrome__use_browser`), persistent profile shared with a concurrent `qa` agent (resolved by waiting for it to vacate — see Execution note)
- **Test Date:** 2026-06-02
- **Evidence directory:** `reports/qa/goal-i_can_see_the_wealthy_future_forever-iter-6-evidence/` (UT-* files are this run's; TC-* files belong to the concurrent qa agent)
- **Note on captures:** all date changes were driven via the global as-of switcher with in-app navigation (never F5 — the as-of provider is in-memory and resets to Latest on hard reload). Viewport (non-fullpage) screenshots at large scroll offsets intermittently returned blank frames in this environment; affected shots were re-captured via full-page screenshot + crop, and every visual claim is additionally backed by a DOM `eval` assertion.
