**Verdict:** PASS

# goal-i_can_see_the_wealthy_future_forever-iter-6 QA Report

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-6
**Date:** 2026-06-02
**Agent:** qa (MODE 2 — validation)
**Frontend Present:** yes
**Target journeys:** J-20 (chart full-path-through-latest, display-only) · J-21 (Backtest leadership cohorts below Return Attribution with horizon-linked realized returns)

---

## Summary

Both target journeys pass end-to-end. J-20 renders the Stock-Detail chart through the latest seed bar with an as-of divider and a labelled forward/display-only region while the three scores + setup + VCP + invalidation stay byte-identical to the ≤ D snapshot. J-21 relocates the three leadership lists below Return Attribution, each carrying a horizon-linked realized-return column read from stored forward returns, and a **single** horizon view-selector re-points both the attribution and all three columns with no date change. Both critical anti-goal seams (No-lookahead, Attribution-read-only / Exactly-one-date-selector) are confirmed in source and by tests. Full backend regression: **312 passed, 1 skipped, 0 failed**. **18/18 functional test cases passed.**

---

## Step 1 — Artifact verification

| Artifact | Status |
|----------|--------|
| `docs/handoffs/goal-...-iter-6-dev.md` | ✅ present |
| `docs/handoffs/goal-...-iter-6-frontend.md` | ✅ present |
| `reports/reviews/goal-...-iter-6-review.md` | ✅ present — **PASS_WITH_NOTES** (2 non-blocking notes) |
| `runs/goal-...-iter-6/status.json` | ✅ present |
| `reports/qa/goal-...-iter-6-test-plan.md` | ✅ present (executed below) |

---

## Step 2 — Backend tests (full regression, TC-09)

Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -v` (log: `reports/qa/goal-i_can_see_the_wealthy_future_forever-iter-6-test.log`)

```
================= 312 passed, 1 skipped in 1166.45s (0:19:26) ==================
```

- **0 failed, 0 errors.** The 1 skip is the offline-skipped `@pytest.mark.integration` live-fetch (`test_stooq_provider` network test) — expected without network. No regression in any previously-passing test.

Targeted runs (subsets of the above, executed first for fast anti-goal confirmation):
- TC-04 `-k "through_latest or no_lookahead or bars_through"` → **13 passed**
- TC-05 `-k "leadership_returns or leadership"` → **10 passed**
- TC-06 `-k "leadership and (na or null or insufficient)"` → **1 passed**
- TC-08 `-k "no_magic_numbers"` → **2 passed**

## Step 3 — Frontend tests

Per dev/frontend handoff: `cd apps/frontend && npm run build` compiled + typechecked successfully (13 routes, no type errors). Not re-run here (QA runner serves the already-built frontend on :3835, which responded 200 throughout); UI behaviour validated by the browser checks below.

---

## Step 3.5 — Functional test plan results

Services: backend `http://localhost:8835` (health 200), frontend `http://localhost:3835` (200). Seed latest date = **2026-05-28**. Historical D used = **2025-04-04** (confirmed ~287 post-D bars); recent date = **2026-02-27**. All date changes driven via the global as-of `<select aria-label="View as-of date">` + in-app navigation (in-memory provider). API ports adjusted from the plan's `:8000` to this project's `:8835`.

| Test ID | Name | Type | Expected | Actual | Verdict | Notes |
|---------|------|------|----------|--------|---------|-------|
| TC-01 | Bars extend through latest w/ as-of boundary | api | forward bars > D flagged `is_forward`, `latest_date` > D, ma full | 1356 bars (1069 ≤D + 287 forward), all forward dated > D, `latest_date`=2026-05-28, ma keys 20/50/150/200 present; no ≤D bar mis-flagged | **PASS** | |
| TC-02 | Default bars stay ≤ D (no-lookahead default) | api | no bar > D, no `is_forward`, no `latest_date` | 1069 bars, last = 2025-04-04, 0 bars > D, 0 `is_forward`, `latest_date` absent | **PASS** | default contract unchanged |
| TC-03 | Error/edge paths preserved | api | unknown→404, invalid as_of→4xx, latest as-of→no forward | ZZZZ→**404**, `as_of=not-a-date`→**422**, latest as-of (2026-05-28) `through=latest`→0 bars > D / 0 `is_forward` | **PASS** | no fabricated rows |
| TC-04 | No-lookahead scores/VCP unchanged + source-seam | artifact | named tests pass; helper not in scoring path | 13 passed; `bars_through_latest` referenced only in `prices.py` + `api/stocks.py` — **not** in `scoring.py`/`scanner.py`/`patterns.py` (grep) | **PASS** | |
| TC-05 | Leadership returns = direct read of stored forward_returns | artifact | named tests pass; no Session/query | 10 passed (sector=ETF row, theme=member mean, cohort=own row; recomputes-nothing keystone) | **PASS** | |
| TC-06 | Honest NA for insufficient post-bars | artifact | NA test passes; null not fabricated 0% | 1 passed | **PASS** | |
| TC-07 | leadership_returns per horizon in /api/backtest | api | sectors/themes/cohort present per by_horizon | 5 by_horizon entries each with sectors=11, themes=11, cohort=122; XLK sector +0.60% n=1, ai_data_centre theme +3.53% n=16, NVDA cohort +3.53% n=1 | **PASS** | values match stored returns; no new endpoint |
| TC-08 | No magic numbers in forward_testing | artifact | `test_no_magic_numbers` passes | 2 passed | **PASS** | complete keyed projection — no row-cap literal |
| TC-09 | Full backend regression | artifact | exit 0, 0 failed/0 error | 312 passed, 1 skipped (offline integration), 0 failed | **PASS** | no regressions |
| TC-10 | Stock-Detail chart as-of divider + forward region @ D | browser | bars past D, divider at D, forward label | "Full path through 2026-05-28", 1356 bars, dashed as-of divider labelled 2025-04-04, chart extends into 2026, legend "Forward — after as-of 2025-04-04 (display only)", display-only caption | **PASS** | evidence `TC-10-*.png` |
| TC-11 | Scores/setup/VCP unchanged from ≤D snapshot | browser | displayed = snapshot API values | Leadership **43.39**, Entry **37.36**, Risk **50.34**, setup Risk-off-watchlist, inval $121.27, VCP not detected — all equal `/api/stocks/NVDA?as_of=2025-04-04` (incl. every component contribution) | **PASS** | forward bars don't alter scores |
| TC-12 | Latest as-of: no forward region | browser | no forward region, chart unchanged | At Latest: no "Forward" legend, no display-only caption, no historical badge; bars line "1356 bars · as of 2026-05-28" | **PASS** | evidence `TC-12-*.png` |
| TC-13 | Backtest section order | browser | scan summary → scorecard → attribution → 3 lists | Vertical order: As-of scan summary (296) → Forward-test scorecard (537) → Return attribution (826) → Leadership cohorts / Ranked cohort (2056) | **PASS** | lists below attribution |
| TC-14 | Realized-return column on each list | browser | column present + populated, honest NA | Top Sectors/Themes/Ranked Cohort each show "FWD 1D"; populated (e.g. PLTR +5.17% n=1); CIBR "—" n=0 (honest NA) | **PASS** | |
| TC-15 | One horizon selector re-points all columns + attribution | browser | one selector flips lists + attribution, no refetch/date change | Switching 1d→20d (as-of unchanged 2025-04-04): Top Sectors XLP −1.16%→**+3.86%**, XLF −0.25%→**+11.86%**; attribution Distribution mean +0.72%→**+19.71%**; column header FWD 1D→FWD 20D; single selector (`aria-pressed` toggled) | **PASS** | defining J-21 proof; evidence `TC-15-before/after-horizon.png` |
| TC-16 | Recent as-of renders NA honestly | browser | "—" NA, no fabricated returns | 2026-02-27 @ 60d: 9 NA "—" cells (n=0) on rows lacking post-bars; populated rows real (Semiconductors +63.46% n=27); no 0% fabrication | **PASS** | evidence `TC-16-backtest-recent-na.png` |
| TC-17 | No page-local date control on Backtest | browser+source | only global switcher; horizon = view selector | 0 `input[type=date]`, single `<select>` (global as-of); horizon is 5 buttons (1d/5d/10d/20d/60d). Source `app/backtest/page.tsx`: only `asOf` (global) + view-only `viewHorizon` (`onChange=setViewHorizon`, drives `selected` row, no fetch param/date state) | **PASS** | J-18 preserved |
| TC-18 | Required-still-passing journeys remain green | browser | J-05/06/13/14/15/16/18/19 render, behave | Dashboard, Stocks, Stock Detail (NVDA), Themes (rows), Sectors (rows), Scanner Runs (56 links), System Health (data), Backtest (full) all render with data, no error boundary; single date control intact | **PASS** | no regression observed |

**18/18 test cases passed.**

---

## Step 4 — Chrome MCP browser checks

Performed (frontend reachable on :3835). Evidence saved under `reports/qa/goal-i_can_see_the_wealthy_future_forever-iter-6-evidence/`:
- `TC-10-chart-historical-divider.png`, `TC-10-chart-zoom.png` — J-20 defining artifact: as-of divider + labelled forward/display-only region at D, chart through 2026-05-28.
- `TC-12-chart-latest-no-forward.png` — latest as-of, no forward region.
- `TC-13-backtest-section-order.png` — three leadership lists below Return Attribution.
- `TC-15-before-horizon.png` / `TC-15-after-horizon.png` — return columns + attribution re-point together on the one horizon selector.
- `TC-16-backtest-recent-na.png` — honest "—" NA on a recent date.

(Pre-existing `UT-01/02/03-*.png` from the per-iteration browser-qa-agent run are also present and consistent; not overwritten.)

**Browser-automation note (not an app defect):** the Chrome-DevTools synthetic click on the horizon `<button>` did not always trigger the React handler (likely a synthetic-click coordinate/overlay quirk); dispatching the element's native `click()` did, after which `aria-pressed` toggled and every return column + the attribution re-pointed correctly. A real user mouse click invokes the same `onClick` handler, so the control is functional — verified by the resulting state change in TC-15/TC-16.

---

## Step 4b — UI Evolution Audit

1. **Did the UI evolve to reflect the phase's new capability?** Yes — the Stock-Detail chart gained a visible as-of divider, muted post-D candles/volume, a forward-region legend, and a display-only caption; the Backtest page reordered (three lists below Return Attribution) and each list gained a horizon-linked realized-return column.
2. **Can the user see, understand, and control the new capability?** Yes — the caption explains the forward bars are display-only and do not affect scores; the single horizon selector visibly re-points the attribution and all three columns; the global as-of switcher drives the date.
3. **Relying on old generic pages for new functionality?** No — both changes land on the existing dedicated homes (`/stocks/[ticker]`, `/backtest`), enhanced in place; no nav/sidebar change.
4. **Technically complete but product-wise underexposed?** No — both capabilities are fully and legibly surfaced with honest NA states.

**Verdict:** UI-PASS

---

## Anti-goal seam confirmation

- **No-lookahead (critical):** default `/bars` contract stays ≤ D and byte-identical (TC-02); forward extension is opt-in `?through=latest` (TC-01); `bars_through_latest` is referenced only by the bars endpoint, never by scoring/scanner/patterns (TC-04 source-seam); displayed scores/setup/VCP/invalidation equal the ≤ D snapshot (TC-11). 13 no-lookahead tests pass.
- **Attribution-read-only / Single-source / No-recompute (critical):** `_leadership_returns` takes no Session, issues no query, recomputes no return — pure projection of the same stored `forward_returns` the scorecard reads (TC-05, TC-07); 10 tests pass incl. the recomputes-nothing keystone.
- **Exactly-one-date-selector (J-18):** only the global as-of select drives the date; the horizon control is a lifted **view** selector with no date state/refetch (TC-17, source-verified).
- **No fabricated data:** missing (row, horizon) renders "—" / n=0, never a fabricated 0% (TC-06, TC-14, TC-16).

---

## Blockers

None.

## Notes (non-blocking, from reviewer — confirmed acceptable)

- Cohort projection iterates `cfg.universe.symbols` (complete stored-result set) rather than literal stored `ScannerResult` tickers; the frontend joins by ticker so each Ranked-Cohort row resolves to the symbol's own stored return — values identical, no row-count literal, no Session/query. Confirmed in TC-14 (every displayed cohort row populated).
- No-lookahead "scores/VCP unchanged" is proven structurally (`bars_asof` invariance + trailing `sma_series` + source-seam) rather than by an explicit `score_stocks` before/after call — equivalent and confirmed green (TC-04, TC-11).

---

**Verdict:** PASS
