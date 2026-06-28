# Goal Mode Iter-56 — UI Test Results

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-56
**Date:** 2026-06-29
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

**Overall:** 5/5 tests passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-48 | Stocks leaderboard column sorting | happy-path | P1 | Columns sort asc/desc; filter+sort compose; # restores default rank | Leadership sort toggled asc→desc; Ticker sort alphabetical; filter (Technology) applied while sort active — 57 rows in sorted order; # header restored default rank (1:MU, 2:ARM, 3:MRVL) | PASS | `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-56-evidence/UT-J-48-result.png` |
| UT-J-50 | As-of date survives every in-app navigation | happy-path | P1 | All in-app hrefs embed `?asof=D` when historical date selected; clean at Latest | Picked 2025-01-02; all sidebar + leaderboard row hrefs confirmed carrying `?asof=2025-01-02`; navigated to /themes and URL showed `?asof=2025-01-02`; back at Latest, all nav links were param-free | PASS | `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-56-evidence/UT-J-50-result.png` |
| UT-J-109 | Factor Lab — all-horizon columns, no horizon selector | happy-path | P1 | No horizon selector; all 5 Fwd then 5 MDD columns on both tables; n chips link to samples | No select elements on page; headers: Fwd 1d→5d→10d→20d→60d then MDD 1d→5d→10d→20d→60d on all-factors table; expanded decile sort shows same grouped column order (D1–D10 with n chips); n chip navigated correctly to /research/samples with correct cohort params | PASS | `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-56-evidence/UT-J-109-result.png` |
| UT-J-113 | Research hub lab order | smoke | P1 | Labs ordered: Factor Lab → Regime Lab → Market Phase & Severity Lab → Regime×Phase×Factor → Regime×Setup×Pattern → Severity-velocity×Regime → Multi-factor → Event Study → Recovery-Turn Edge → Downtrend Opportunity | Exact order confirmed via link enumeration from `data-testid="research-hub"` / main container; all 10 labs present and deep-linkable | PASS | `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-56-evidence/UT-J-113-result.png` |
| UT-J-114 | Research labs column grouping (all Fwd then all MDD) | happy-path | P1 | All four all-horizon lab tables show all forward-return columns first then all max-drawdown columns, never interleaved | Factor Lab: Fwd 1d–60d then MDD 1d–60d (both all-factors table and decile sort); Regime Lab: same order on by-label and regime-score decile tables; Market Phase & Severity Lab: same order on by-phase-label and severity-score decile tables; Regime×Phase×Factor: same order on combination table | PASS | `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-56-evidence/UT-J-114-result.png` |

---

## Passed Tests

### UT-J-48 — Stocks leaderboard column sorting
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-56-evidence/UT-J-48-result.png`
- Visited `/stocks`; default order confirmed as rank (1:MU, 2:ARM, 3:MRVL).
- Clicked "Sort by Leadership" button — rows reordered ascending (COIN 4.62, HUBS 7.02, MSTR 7.48...). Sort indicator aria-label changed to "Sort by Leadership, ascending".
- Clicked again → descending (MU 94.58, ARM 93.61, MRVL 93.24).
- Clicked "Sort by Ticker" → alphabetical order (AAPL, ABNB, ADBE, ADI, AMAT).
- Applied Sector filter "Technology" with sort active → 57 Technology rows in sorted Leadership order, confirming filter+sort compose.
- Clicked "Sort by #" → default rank order restored exactly (1:MU, 2:ARM, 3:MRVL, 4:STX, 5:INTC).

### UT-J-50 — As-of date survives every in-app navigation
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-56-evidence/UT-J-50-result.png`
- Opened date picker on `/stocks`; navigated to January 2025, selected 2025-01-02.
- URL updated to `/stocks?asof=2025-01-02`.
- All 10 sidebar nav entries confirmed with `?asof=2025-01-02` in href (Dashboard, Stocks, Themes, Sectors, Scanner Runs, Backtest, Research, Watchlist, Methodology, Data Manager).
- Leaderboard row hrefs confirmed (e.g., `/stocks/HOOD?asof=2025-01-02`, `/stocks/PLTR?asof=2025-01-02`).
- Clicked Themes nav link → navigated to `http://localhost:3255/themes?asof=2025-01-02`.
- Navigated back to `/stocks` (Latest) → all nav links confirmed clean, no `?asof` parameter.

### UT-J-109 — Factor Lab — all-horizon columns, no horizon selector
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-56-evidence/UT-J-109-result.png`
- Visited `/research/factor-lab` — zero `<select>` elements; no horizon dropdown.
- All-factors table headers confirmed: Factor, Family, Rank-IC (20d), N, Risk-adjusted (20d), Fwd 1d, Fwd 5d, Fwd 10d, Fwd 20d, Fwd 60d, MDD 1d, MDD 5d, MDD 10d, MDD 20d, MDD 60d.
- Rows show colour-graded return and MDD values with real data (e.g., Proximity to 52w high: +0.11% / +0.59% / +1.38% / +2.74% / +7.41% fwd; -2.88% / -5.72% / -7.76% / -10.63% / -17.51% MDD).
- Expanded first factor row → decile sort shows same grouped column order: Decile, Factor range (20d), Fwd 1d–60d, MDD 1d–60d; per-decile n chips visible (e.g., n=11 per decile in As-of mode).
- Clicked "As of date" toggle — data refreshed; survivorship-bias evidence labels present.
- N chip links confirmed: `href="/research/samples?kind=factor&horizon=1&factor=high_proximity&slice=decile&decile=1&scope=asof"` — navigated to samples page which loaded correctly showing "Research Samples — observation drill-down" with member observations.

### UT-J-113 — Research hub lab order
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-56-evidence/UT-J-113-result.png`
- Visited `/research` hub.
- Enumerated all lab card links: 1) Factor Lab, 2) Regime Lab, 3) Market Phase & Severity Lab, 4) Regime × Phase × Factor, 5) Regime × Setup × Pattern, 6) Severity-velocity × Regime, 7) Multi-factor combination, 8) Setup & Pattern event study, 9) Recovery-Turn Edge, 10) Downtrend Opportunity.
- Order exactly matches J-113 specification. All 10 labs present with correct deep-linkable hrefs.

### UT-J-114 — Research labs column grouping
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-56-evidence/UT-J-114-result.png`
- **Factor Lab** (`/research/factor-lab`): all-factors table headers = [..., Fwd 1d, Fwd 5d, Fwd 10d, Fwd 20d, Fwd 60d, MDD 1d, MDD 5d, MDD 10d, MDD 20d, MDD 60d]; expanded decile sort = same grouped order.
- **Regime Lab** (`/research/regime-lab`): by-label headers = [Regime, Fwd 1d–60d, MDD 1d–60d]; regime-score decile headers = [Decile, Score range (20d), Fwd 1d–60d, MDD 1d–60d].
- **Market Phase & Severity Lab** (`/research/phase-severity-lab`): by-phase headers = [Market phase, Fwd 1d–60d, MDD 1d–60d]; severity decile headers = [Decile, Severity range (20d), Fwd 1d–60d, MDD 1d–60d].
- **Regime × Phase × Factor** (`/research/regime-phase-factor`): combination table headers = [Regime D, Severity D, Factor D, Fwd 1d–60d, MDD 1d–60d].
- All four labs: Fwd columns precede MDD columns, never interleaved.

---

## Failed Tests

(none)

---

## Skipped Tests

(none)

---

## Environment

- **Frontend URL:** http://localhost:3255
- **Browser:** Chrome via MCP
- **Test Date:** 2026-06-29
- **Evidence directory:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-56-evidence/`
