# Goal Iteration 20 — UI Test Results (Browser QA)

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-20
**Date:** 2026-06-04
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

<!-- PASS: All P1 tests pass -->

**Overall:** 29/29 buildable must-have journeys passed (J-01–J-21, J-25–J-32). 3 data-walled journeys (J-22, J-23, J-24) SKIPPED as NA / non-halting per `docs/goal.md`. 0 regressions, 0 console errors.

This is iteration 20 — a finalization / no-code-change iteration with **no Target journeys**. Per the dispatch, every **Required-still-passing** journey (all 29 buildable journeys) was re-executed through real browser workflows to confirm no regression. All hold green.

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | Daily dashboard at a glance | regression | P1 | Regime label+score, 3 candidate counts, ≥3 top sectors+themes, breadth, last-scan | Risk-on **74.32/100** (explainable components), Actionable 0 / Breakout-watch 8 / Pullback-watch 1, 5 sectors + 5 themes w/ scores, breadth 65.57%, "Data as-of 2026-05-28" | PASS | UT-J-01-dashboard.png |
| UT-J-02 | Stock Leaderboard with working filters | regression | P1 | Ranked rows w/ 3 bucketed scores+setup+reason; sector filter narrows; Actionable filter or empty-state | 122 ranked rows; Sector=Technology → 58 rows all Technology; Setup=Actionable → explicit empty-state "0/122 — No stock is currently 'Actionable'" | PASS | UT-J-02-leaderboard.png, UT-J-02-actionable-empty-state.png |
| UT-J-03 | Theme Leaderboard | regression | P1 | ≥3 themes ranked desc; top theme members + 1m/3m + breadth + trend | 11 themes non-increasing (Semiconductors A100 → Homebuilders E20.5); Semiconductors: members NVDA/AMD/AVGO/MRVL/MU/WDC+21, 1m +28.38%, 3m +61.22%, breadth 100%, "Strong uptrend" | PASS | UT-J-03-themes.png |
| UT-J-04 | Sector / industry Leaderboard | regression | P1 | Ranked by Sector Score; RS-vs-SPY, dist-52w, trend; SPY as ref or excluded | 31 rows ranked; top SOXX A93.67, RS +45.49%, dist −0.11%, "Strong uptrend"; SPY excluded from ranking (only the "RS vs SPY" column references it) | PASS | UT-J-04-sectors.png |
| UT-J-05 | Stock Detail with explainable scores | regression | P1 | Price+MA chart+volume; 3 scores w/ bucket+value+≥3 components; themes/setup/reason/invalidation | NVDA chart (1356 bars) + volume; Leadership E 47.48 / Entry D 66.24 / Risk E 33.79 each w/ named components (RS vs SPY 1m/3m, MA stack, 52w proximity…); themes, Avoid, reason, "Invalid below 50-DMA at $198.73" | PASS | UT-J-05-J-06-nvda-detail-coherence.png |
| UT-J-06 | Score consistency across pages | regression | P1 | NVDA's 3 scores identical leaderboard↔detail | Leaderboard E47.48/D66.24/E33.79 == detail E47.48/D66.24/E33.79 (buckets + values identical) | PASS | UT-J-05-J-06-nvda-detail-coherence.png |
| UT-J-07 | Risk-Off regime suppresses Actionable | regression | P1 | Risk-off run shows zero Actionable | Run 2025-04-04 regime **Risk-off**; candidate counts Actionable 0; all 122 stock rows status "Risk-off-watchlist", zero Actionable | PASS | UT-J-07-riskoff-run.png |
| UT-J-08 | Immutable scanner-run history | regression | P1 | ≥2 dated runs; older differs from latest | 11 dated runs; older (2025-04-04) top KTOS/NOC/PLTR (Industrials) vs latest (2026-05-28) MU/ARM/MRVL (semis) — clearly distinct snapshots | PASS | UT-J-08-scanner-runs.png |
| UT-J-09 | Backtest forward-tested evidence (as-of-scoped) | regression | P1 | By-bucket/setup/regime + excess vs SPY/QQQ w/ n; re-points on as-of move; n non-decreasing toward latest | At ≤2026-05-28: A+14.37%(n23) B+15.28%(n87) … E+11.07%(n772); excess SPY +10.57% vs +6.21%. Moved to ≤2025-08-28 → n dropped (E 772→618) and "Narrow leadership" regime row vanished (its snapshot is dated >2025-08-28) — no future leak | PASS | UT-J-09-J-10-backtest-latest.png, UT-J-09-backtest-fullpage-2025-08-28.png |
| UT-J-10 | Control-group honesty | regression | P1 | Top cohort vs random same-sector vs SPY/QQQ/sector, numeric+labelled | At 60d: Top-ranked +10.48%(n199), Random same-sector +8.18%(n280), SPY +6.21%, QQQ +7.37%, Sector ETF +5.14% | PASS | UT-J-09-J-10-backtest-latest.png |
| UT-J-11 | Watchlist with persistence | regression | P1 | Add ANET → shows date/reason/scores/setup/price-since/invalidation; persists across restart | Added ANET (date 2026-06-04, reason, L E46.61/E E57.69/R E39.62, Avoid, +0.00%, invalid $148.38); survived hard reload; **row present in SQLite `trendora.db`** (id 1) → survives backend restart | PASS | UT-J-11-watchlist-added.png |
| UT-J-12 | Glossary + inline explanations | regression | P1 | 6 setups + VCP each w/ meaning+thresholds+example; inline tooltip matches; config-backed | /methodology lists all 6 setups + VCP + Pullback-to-rising-DMA + Flat-base, each w/ meaning + config thresholds + worked example ("read live from config"); leaderboard badge `title` tooltip matches ("Strong leader but the entry is extended — wait for a pullback…") | PASS | UT-J-12-methodology.png |
| UT-J-13 | Browse as of a past date (global switcher) | regression | P1 | Past date re-points every page; historical indicator; return to latest restores | Switcher→2025-08-28 re-pointed /stocks (MU→KTOS, "as-of 2025-08-28", historical badge) and propagated to /themes via in-app nav; return to latest restored NVDA $198.73 / Entry D66.24 | PASS | UT-J-13-stocks-historical-asof.png |
| UT-J-14 | Backtest a past date + forward-test scorecard | regression | P1 | Numeric fwd returns by horizon w/ excess+control+n; recent date shows NA not fabricated | At 2025-08-28: 1d −1.15% / 5d +1.61% / 10d +5.08% / 20d +12.38% / 60d +3.02% (n20) w/ vs SPY/QQQ/Sector + random peers (n25). At latest (no post-bars) every horizon NA (n=0) "nothing fabricated" | PASS | UT-J-14-J-19-J-21-backtest-historical-60d.png |
| UT-J-15 | Fast page loads from persisted snapshots | regression | P1 | Warm load < ~1.5 s; snapshot-served; coherent | /stocks domInteractive **57 ms**, fully loaded **429 ms**; `/api/stocks` snapshot-served at steady **~35 ms**; coherence preserved (per J-06) | PASS | (timing — see notes) |
| UT-J-16 | VCP — detected, explained, filterable, forward-tested | regression | P1 | VCP filter → flagged rows w/ badge+reason+invalidation; detail badge+pivot; glossary; backtest VCP-vs-non | VCP filter → 4 names (STX/TSLA/TSM/ORCL) each w/ badge + reason ("3 contractions… Pivot $905.39, invalid below $816.98"); TSM detail VCP pivot $430.55 / invalid $414.71 (Avoid+VCP, not Actionable); glossary entry; backtest VCP +5.20%(n27) vs non-VCP +10.69%(n1190) | PASS | UT-J-16-vcp-filter.png, UT-J-16-tsm-vcp-detail.png |
| UT-J-17 | Grow the dataset by date / range | regression | P1 | Async job w/ progress+summary; new as-of dates selectable; backtest n grows; provider failure explicit | /data coverage (2021-01-04→2026-05-28, universe 122, 158 symbols, 11 snapshot dates, 1345 gaps); ran offline backfill 2024-01-03 → progress "1/1 dates" → summary "1 snapshot, 670 forward returns" (run history logged ok); 2024-01-03 now selectable (11→12); backtest bucket E n 772→852 (+~121). Fetch failure handling surfaced in copy ("fabricates nothing") | PASS | UT-J-17-data-coverage.png, UT-J-17-backfill-job-done.png |
| UT-J-18 | One date control (no duplicate) | regression | P1 | Backtest has no page-local date picker; global switcher drives it; same resolved date everywhere | Backtest has exactly **one** `<select>` (the global switcher); page URLs are date-free (`/stocks`, `/backtest`); switcher to 2025-08-28 resolved identically on Backtest, /stocks, /themes | PASS | UT-J-14-J-19-J-21-backtest-historical-60d.png |
| UT-J-19 | Diagnose weak returns via attribution | regression | P1 | Per-stock contributors/detractors (named), by-sector, by-rank-band, distribution/hit-rate, all w/ n | At 2025-08-28: contributors S +7.10%, DNN +5.45% … detractors MRVL −18.59%, DELL −8.88%; by-sector (Technology −1.79% n58 …); rank bands 1–10/11–50/51+; distribution & hit-rate panel — all w/ n | PASS | UT-J-14-J-19-J-21-backtest-historical-60d.png |
| UT-J-20 | Full chart path through latest (as-of marker) | regression | P1 | Chart extends to latest; D marked, post-D labelled forward; scores from ≤D | At as-of 2025-08-28 NVDA chart renders all 1356 bars (through 2026-05-28); post-D region labelled "**Forward — after as-of 2025-08-28 (display only)**"; scores recomputed ≤D (Entry E58.93, Risk E41.45, invalid $169.92 — differ from latest) | PASS | UT-J-20-nvda-chart-asof-marker.png |
| UT-J-21 | Backtest cohorts below attribution, horizon-linked | regression | P1 | Order: summary→scorecard→attribution→Top Sectors/Themes/Cohort; horizon selector re-points returns | Section order correct (Leadership cohorts below Return attribution); Top Themes + Ranked Cohort carry realized returns; horizon 1d→60d re-pointed Homebuilders +0.04%→−9.83% and labels; niche industry ETFs honestly NA | PASS | UT-J-14-J-19-J-21-backtest-historical-60d.png |
| UT-J-25 | Factor Lab — decile sort + rank-IC (raw+risk-adj) | regression | P1 | Decile means w/ risk-adj col + numeric rank-IC, each w/ n; low-sample NA; survivorship label | Decile table (D1…D10 w/ factor range + mean + downside risk-adj + n); downside_vol rank-IC **+0.08 n=1338** w/ plain-language read; survivorship-bias label shown | PASS | UT-J-25-J-27-factor-lab.png |
| UT-J-26 | Factor Lab — multi-factor composite cohort | regression | P1 | Combine 2..all factors; Combined composite non-empty, clears min-sample; beside baseline+singles | 3 conditions (RS3m top + ATR% bottom + Leadership top) → **Combined (composite rank-blend) n=268 +2.47%, median +1.67%, hit-rate 59.70%, risk-adj +0.47** (non-empty, clears min-sample); beside Baseline n=1338 + each single; Strict-overlap (AND) n=41; "Add condition" scales | PASS | UT-J-26-composite-cohort.png |
| UT-J-27 | Factor Lab — regime-conditioned effectiveness | regression | P1 | Factor decile/IC split by regime w/ per-regime n; low-sample NA | "Factor effectiveness by market regime": Strong risk-on IC −0.09 (n121), Risk-on +0.02 (n732), Narrow leadership +0.01 (n122), Choppy −0.12 (n122), Defensive NA (n0), Risk-off −0.06 (n242) | PASS | UT-J-25-J-27-factor-lab.png |
| UT-J-28 | More detected patterns beyond VCP | regression | P1 | ≥2 new patterns filterable w/ badge+reason+invalidation; documented; pattern-vs-non breakdown | Flat-base filter → 3 names (TPH/GS/ADI) w/ badge + reason + invalidation ("Flat 25-bar base… Pivot $46.99, invalid below $46.74"); Pullback-to-rising-DMA same mechanism; both on /methodology; backtest Pullback-to-DMA +2.45%(n163) & Flat-base +6.34%(n48) breakdowns | PASS | UT-J-28-flatbase-filter.png |
| UT-J-29 | Setup & Pattern Lab — event study | regression | P1 | Pooled per-horizon distribution + expectancy + MAE/MFE + risk-adj + best exit + regime/sector slices w/ n | Breakout-watch (n=110): per-horizon mean/median/%positive (60d +10.68%, 56.36% pos), expectancy, MAE/MFE (60d MAE −15.51%/MFE +25.35%), 2 downside risk-adj ratios, 60d highlighted "best exit", by-regime + by-sector slices; low-sample (Actionable n2) NA | PASS | UT-J-29-event-study.png |
| UT-J-30 | Volatility as a return driver (family) | regression | P1 | level/contraction/downside measures w/ decile (raw+risk-adj) + rank-IC, regime-conditioned; risk uses downside | Factor selector exposes atr_pct (level), hv, vcp_contraction, downside_vol; downside_vol decile D1 +1.07%→D10 +5.60% (n133/134) + rank-IC +0.08 n=1338; regime-conditioned table updates; "risk = downside-deviation only" | PASS | UT-J-25-J-27-factor-lab.png |
| UT-J-31 | Find a high-return driver end-to-end | regression | P1 | Travel lab evidence → leaderboard filter → detail without recompute/fabrication | Factor Lab + Setup/Pattern Lab give n+regime-context evidence; "View the names expressing this on the leaderboard→" bridges to `/stocks?setup=Breakout-watch`; leaderboard filter → Stock Detail flow verified (J-02/J-05); weak/low-sample shown as NA | PASS | UT-J-29-event-study.png, UT-J-02-leaderboard.png |
| UT-J-32 | Research point-in-time toggle (as-of vs all-history) | regression | P1 | All-history⟷As-of toggle; as-of pools only snapshots ≤ global date (smaller n); reuses single control; back restores | Toggle "As of date" + as-of 2024-05-28 → rank-IC n 1338→362, baseline n 1338→362, decile D1 n 133→36; reuses the single global switcher (no 2nd date state); "All history" restored n→1338 | PASS | UT-J-32-asof-mode.png |
| UT-J-22 | Transparent rule-based ~500-name universe | data-walled | P1 | Universe ~400–500 names w/ committed history | Universe remains 122 (158 incl. ETFs); expanded-universe data unreachable (Yahoo 429). NA / non-halting per goal.md | SKIP | none |
| UT-J-23 | Multi-timeframe intraday bars | data-walled | P1 | 1D/1h/15m/5m timeframe-aware seed | No committed intraday seed (data wall). NA / non-halting per goal.md | SKIP | none |
| UT-J-24 | Timeframe selector on stock chart | data-walled | P1 | 1D/1h/15m/5m chart selector | Depends on J-23 intraday data (unbuilt). NA / non-halting per goal.md | SKIP | none |

---

## Passed Tests (highlights)

All 29 buildable journeys passed; full per-journey evidence is in the results table and the evidence directory. Selected verification highlights that double as anti-goal checks:

### Single source of truth / coherence (J-06, J-15)
NVDA's three scores (E 47.48 / D 66.24 / E 33.79) and A–E buckets read **identically** on the leaderboard and the detail page. `/api/stocks` serves the persisted snapshot in ~35 ms; the page reaches interactive in 57 ms. No view recomputes a score.

### No-lookahead / immutability (J-07, J-08, J-09, J-20)
- The 2025-04-04 **Risk-off** run forces all 122 rows to "Risk-off-watchlist" (zero Actionable) — regime gating holds.
- The as-of-scoped Backtest aggregate at ≤2025-08-28 **drops the "Narrow leadership" regime row entirely** (its only snapshot is dated 2026-02-27 > 2025-08-28) — direct proof no future snapshot leaks into as-of-D evidence.
- The NVDA chart at historical as-of 2025-08-28 renders the **full 1356-bar path through the latest date** but labels the post-D region "**Forward — after as-of 2025-08-28 (display only)**"; the scores/invalidation are recomputed strictly from bars ≤ D (differ from the latest values) — the chart extension is display-only and feeds no signal.

### Exactly one date selector (J-18, J-32, J-24-intent)
The Backtest page has exactly one `<select>` (the global as-of switcher); page URLs are date-free; the Research **All history ⟷ As of date** control is a **mode toggle** that reuses the single global as-of (no second date state). The Data Manager's import date inputs are explicitly labelled job parameters, not the viewing date.

### Honest evidence / no fabrication (J-09, J-14, J-19, J-25–J-32)
Every aggregate carries sample size n; low-sample cells show NA + ⚠; horizons without elapsed windows show "—" (NA) rather than fabricated numbers; every lab view carries the survivorship-bias / universe-relative label and is read-only over stored values (the composite cohort is a transparent rank-blend, not a fitted model).

---

## Skipped Tests

### UT-J-22 / UT-J-23 / UT-J-24 — data-walled, non-halting
**Verdict:** SKIPPED (NA)
**Reason:** These three journeys require a real data fetch the committed seed does not contain — an expanded ~400–500-name daily universe + market cap (J-22) and an intraday bar seed (J-23/J-24). The live provider (Yahoo EOD) is rate-limited (persistent 429) for this environment. Per `docs/goal.md` (lines 99–103, 824–844) these journeys are **explicitly non-halting**: they are recorded as honestly blocked / limited-coverage (NA) and MUST NOT halt the loop, drive STALLED, or veto GOAL_ACHIEVED. They auto-unblock with no code change once a reachable provider is confirmed (incl. via the J-35 Data Manager Expand-universe path). No fabrication was introduced to force them green.

---

## Notes

- **No code was changed this iteration** (finalization pass). Every buildable journey was re-executed end-to-end via real browser workflows (filters, as-of switching, watchlist add+persist, backfill job, factor/pattern lab interactions) — not mere page loads — and all hold green with **zero regressions**.
- **State touched during verification:**
  - **J-11 watchlist:** ANET was added (verified persisted to SQLite `trendora.db`), then **removed** to restore the original empty state (0 rows confirmed). Remove also exercised successfully.
  - **J-17 backfill:** one offline, deterministic, create-once-immutable snapshot for **2024-01-03** was created via the legitimate Data Manager backfill path (the workflow under test). This added 1 snapshot + 670 forward returns to the **untracked runtime DB** (`apps/backend/data/trendora.db`); **no git-tracked file was modified**, no seed CSV was touched, and the data is deterministic. It is benign and causes no regression; it is left in place as the natural product of J-17 (snapshots are append-only/immutable, so there is no app-level delete path). This is why the latest-date Backtest bucket samples are now slightly larger than iter-19 (e.g. bucket E n 772→852).
- **Performance (J-15):** `/api/stocks?as_of=…` warm ≈ 35 ms; `/api/backtest` (heaviest aggregate read) ≈ 0.40–0.49 s; page domInteractive 57 ms / load 429 ms — all well within the ~1.5 s warm budget.
- **Console:** 0 JavaScript errors across all 90 captured browser console logs.

---

## Environment

- **Frontend URL:** http://localhost:3835
- **Backend URL:** http://localhost:8835 (`/api/health` → 200, db_ok true, provider seed, seed latest 2026-05-28)
- **Browser:** Chrome via Chrome MCP (`mcp__plugin_superpowers-chrome_chrome__use_browser`)
- **Test Date:** 2026-06-04
- **Evidence directory:** `reports/qa/goal-i_can_see_the_wealthy_future_forever-iter-20-evidence/` (25 screenshots)
