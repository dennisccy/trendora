**Verdict:** PASS

# QA Validation Report — goal-i_can_see_the_wealthy_future-iter-2

**Phase:** goal-i_can_see_the_wealthy_future-iter-2
**Date:** 2026-05-29
**Agent:** qa (MODE 2 — validation)
**Frontend Present:** yes
**Services:** backend `http://localhost:8835` (managed), frontend `http://localhost:3835`

---

## Step 1 — Artifact verification

| Artifact | Status |
|----------|--------|
| `docs/handoffs/goal-i_can_see_the_wealthy_future-iter-2-dev.md` | ✅ present |
| `docs/handoffs/goal-i_can_see_the_wealthy_future-iter-2-frontend.md` | ✅ present |
| `reports/reviews/goal-i_can_see_the_wealthy_future-iter-2-review.md` | ✅ present — **PASS_WITH_NOTES** (1 NOTE: cross-module private import `_label_for`; non-blocking) |
| `runs/goal-i_can_see_the_wealthy_future-iter-2/status.json` | ✅ present (`review_passed`) |
| `reports/qa/goal-i_can_see_the_wealthy_future-iter-2-test-plan.md` | ✅ present (17 TCs) |

All required artifacts present. Review verdict is PASS_WITH_NOTES (acceptable).

---

## Step 2 — Backend tests (exact output)

Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -v`
Log: `reports/qa/goal-i_can_see_the_wealthy_future-iter-2-test.log`

```
============================= 72 passed in 17.20s ==============================
EXIT=0
```

**72 passed, 0 failed.** The prior 25 backend tests remain green; new engine/api/config tests added. Includes:
`test_indicators` (sma/rs_vs/atr_pct/dist_from_high/ma_stack/vol_trend + NA-on-short-history), `test_prices_asof` (includes date=d, excludes date>d, ascending), `test_buckets`, `test_regime` (range/labels/edge-boundary/determinism), `test_sectors` (ranked desc / required fields / SPY excluded / determinism / min_history NA), `test_config_engine` (14 ConfigError paths), `test_api_engine` (served == engine), `test_no_magic_numbers`.

---

## Step 3 — Frontend build

Command: `cd apps/frontend && npm run build`

```
✓ Generating static pages (10/10)
BUILD_EXIT=0
```
Build succeeds and typechecks. `/` (3.45 kB) and `/sectors` (3.76 kB) compile; 10 routes total.

---

## Step 3.5 — Functional test plan results

| Test ID | Name | Type | Expected | Actual | Verdict | Notes |
|---------|------|------|----------|--------|---------|-------|
| TC-01 | `/api/sectors` ranked leaderboard | api | 200; rows with all fields; score non-increasing | 200; `{asof_date,benchmark,rows}`; 31 rows, scores 93.67→7.17 non-increasing; each row has ticker/kind/name/score/bucket/rs_vs_spy/dist_from_52w_high_pct/trend_label/components/rank; components non-empty `{name,raw,percentile,weight,contribution,available}` | **PASS** | — |
| TC-02 | SPY excluded as ranked leader | api | no SPY row | `SPY present: False`; kinds = {industry, sector} only | **PASS** | SPY is the RS benchmark, surfaced as caption "RS benchmark: SPY (excluded)" |
| TC-03 | `/api/dashboard` regime + breadth + honest pending | api | 200; regime/breadth/null pending | 200; regime.score 74.32∈[0,100], label "Risk-on"∈six, components non-empty; breadth.label "universe-relative", above_50dma 65.57, above_200dma 59.02; asof 2026-05-28; `candidate_counts=null`, `top_themes=null` | **PASS** | nulls, not zeros |
| TC-04 | Single source of truth (served==engine) | api/unit | API == engine output; no drift | `test_api_engine.py` PASS in suite; Dashboard Top Sectors (SOXX 93.67/WGMI 90.67/SMH 90.00) match `/api/sectors` top-3 exactly (verified in browser) | **PASS** | regime only via `/api/dashboard`, sectors only via `/api/sectors`; dashboard has no `top_sectors` field — UI reads canonical `/api/sectors` |
| TC-05 | `bars_asof` no-lookahead boundary | unit | includes d, excludes >d, ascending | `test_prices_asof` 4 tests PASS | **PASS** | — |
| TC-06 | Indicator exact values | unit | exact hand-computed | `test_indicators` 15 tests PASS | **PASS** | — |
| TC-07 | `to_bucket` edges | unit | correct letter at each edge | `test_buckets` PASS in suite | **PASS** | only A–E derivation site |
| TC-08 | Regime range/labels/boundary | unit | score∈[0,100], label∈six, edge mapping | `test_regime` 3 tests PASS incl. `test_label_edges_boundary_mapping` | **PASS** | — |
| TC-09 | Sector ranked/complete/SPY-excl/determ | unit | all asserts | `test_sectors` 4 tests PASS | **PASS** | — |
| TC-10 | No magic numbers | artifact | no literal in calc code; config has sections | `test_no_magic_numbers` PASS; config has `indicators`, `sectors`, `sectors.weights`, `regime.label_edges`; independent grep of engine/*.py finds only `1.0`/`[0,1]` in a docstring | **PASS** | — |
| TC-11 | Config validation → ConfigError | unit | explicit ConfigError per malformed section | `test_config_engine` 14 tests PASS (missing indicators, missing rs window, nonpositive period, missing sectors, weights-missing/not-summing, trend edges not covering 0, missing/uncovered/unknown/non-descending label_edges, regime weights) | **PASS** | never a silent default |
| TC-12 | Short-history → NA | unit | NA, no crash, no fabrication | `test_min_history_bars_floor_reports_na_for_short_history` + indicator NA tests PASS | **PASS** | — |
| TC-13 | Regression: existing tests | unit | prior 25 green | 72 passed total, 0 failed | **PASS** | — |
| TC-14 | Frontend build compiles+typechecks | artifact | exit 0, no type errors | BUILD_EXIT=0, 10 routes | **PASS** | — |
| TC-15 | J-04 browser: `/sectors` leaderboard | browser | ranked rows; top row RS/dist/trend; SPY not a leader; expand → components | 31 rows non-increasing (93.67→7.17); top row SOXX `A 93.67`, RS `+45.49%`, dist `-0.11%`, `Strong uptrend`; no SPY row; expand SOXX → component table (RS 1m/3m/6m, MA stack, Dist 52w high, Volume trend; contributions sum ≈93.67) | **PASS** | evidence: TC-15-sectors.png, TC-15-sectors-expanded.png |
| TC-16 | J-01 partial browser: `/` dashboard | browser | regime label+score+components; universe-relative breadth; data-as-of; ≥3 Top Sectors w/ scores; pending placeholders | "Risk-on" + `74.32 /100` + 5-row component breakdown; breadth 65.57%/59.02% labelled universe-relative + net new highs 9.02%; "Data as-of 2026-05-28"; Top Sectors SOXX/WGMI/SMH/XLK/ROBO with scores; Candidate Counts & Top Themes "pending" + "—" + "Arriving in a later iteration" | **PASS** | J-01 stays partial/failing by design; evidence: TC-16-dashboard.png |
| TC-17 | Backend-unavailable state | browser | explicit "unavailable"; no fabricated data | `/sectors` → "Backend unavailable", no ticker/score leak; `/` → "Backend unavailable — Nothing is fabricated", no regime/score leak | **PASS** | evidence: TC-17-sectors-unavailable.png, TC-17-dashboard-unavailable.png |

**17/17 test cases passed.**

---

## Step 4 — Chrome MCP browser checks

Performed against `http://localhost:3835` with the managed backend up on `http://localhost:8835`.

- **J-04 (`/sectors`)**: dense ranked leaderboard with 31 ETF rows ordered by Sector Score (strictly non-increasing 93.67 → 7.17). Columns: `# · TICKER · KIND · SECTOR SCORE (A–E bucket foregrounded + raw, colour-graded) · RS VS SPY · DIST. 52W HIGH · TREND`. SPY excluded from ranked rows (shown as "RS benchmark: SPY (excluded)"). Clicking a row expands its named component breakdown (explainability — no bare numbers).
- **J-01 partial (`/`)**: Market Regime panel (Risk-on, 74.32/100, component breakdown summing to score), universe-relative breadth (50-DMA 65.57%, 200-DMA 59.02%, net new highs 9.02% "11 hi / 0 lo"), "Data as-of 2026-05-28", Top Sectors list (5 rows sourced from `/api/sectors`, identical to the leaderboard top-5), and explicit "pending — Arriving in a later iteration" placeholders for Candidate Counts and Top Themes.
- **Backend-unavailable**: both pages render explicit "Backend unavailable" with no fabricated rows/scores.

Evidence (on disk, `reports/qa/goal-i_can_see_the_wealthy_future-iter-2-evidence/`):
- `TC-15-sectors.png`, `TC-15-sectors-expanded.png`
- `TC-16-dashboard.png`
- `TC-17-sectors-unavailable.png`, `TC-17-dashboard-unavailable.png`

**Note on service stability (iter-1 lesson recurred):** the runner-managed frontend on port 3835 was found **down** (HTTP 000, no process) partway through browser checks — the `next dev` flap noted in the iter-1 lessons. To complete the browser QA I started a clean frontend instance via `scripts/start-frontend.sh` (correctly pointed at backend 8835), ran all browser checks while it was stable, and **killed it afterward** (verified 0 remaining `next dev -p 3835` processes). The managed backend was never touched. The pages render correctly and reproducibly once the frontend is up; this is a service-supervision flap, not an application defect. The runner is expected to restart the managed frontend.

---

## Step 4b — UI Evolution Audit

1. **Did the UI evolve to reflect the new capability?** Yes. `/sectors` went from an empty state to a populated 31-row ranked leaderboard; `/` from empty to a full regime/breadth/data-as-of/top-sectors dashboard.
2. **Can the user see, understand, and control it?** Yes. Buckets foregrounded with raw scores, colour-graded; each row/regime expands to a named component breakdown (explainable). Honest "universe-relative" and "pending" labels are visible.
3. **Still relying on old generic pages?** No — both target pages are purpose-built for the new values.
4. **Technically complete but under-exposed?** No — every backend value (regime score+label+components, breadth, data-as-of, sector score/RS/dist/trend/components) is surfaced; deferred values (candidate counts, themes) are honestly marked pending, not hidden.

**Verdict:** UI-PASS

---

## Blockers

None.

## Notes (non-blocking)

- Review NOTE carried forward: `sectors.py` imports private `_label_for` from `regime.py`. Code-quality nit only; does not affect single-source-of-truth (label-from-edges is still one helper). Candidate for a small refactor in a later iteration.
- Managed `next dev` frontend flapped during QA (iter-1 lesson); QA completed against a fresh stable instance and cleaned it up. Worth keeping an eye on supervision robustness.

---

## Verdict rationale

72/72 backend tests pass (no regressions), frontend builds clean, 17/17 functional test cases pass, all five DoD pillars verified end-to-end: J-04 flips green in the browser (ranked leaderboard, SPY excluded, RS/dist/trend on the top row, expandable components); J-01 partially advances exactly as specified (regime + breadth + data-as-of + Top Sectors real; counts/themes honestly pending); single source of truth holds (served == engine; dashboard Top Sectors == `/api/sectors`; frontend recomputes nothing); no-lookahead `bars_asof` boundary unit-tested; no magic numbers; explainable components; honest universe-relative / pending labels; and backend-unavailable surfaces an explicit non-fabricated state.

**Verdict:** PASS
