**Verdict:** PASS

# goal-i_can_see_the_wealthy_future-iter-4 QA Report

**Phase:** goal-i_can_see_the_wealthy_future-iter-4
**Date:** 2026-05-30
**Mode:** QA Validation (MODE 2)
**Frontend Present:** yes
**Reviewer verdict (input):** PASS_WITH_NOTES

## Summary

J-05 is delivered and verified end-to-end. The Stock Detail page (`/stocks/NVDA`) now renders a
populated price + moving-average candle chart with a volume series (Lightweight-Charts, canvas
confirmed painted — not just "page loaded"), theme-membership chips, and a concrete server-computed
invalidation note ("Invalid below the 50-DMA at $198.73") alongside the three unchanged explainable
score cards. The single-source guarantee holds: the live `/api/stocks/NVDA` row is byte-identical to
its `/api/stocks` list row (incl. the new `invalidation` + `themes`), and the invalidation level
`198.73400026` equals `ma["50"][-1]` from `/api/stocks/NVDA/bars` — one MA definition feeds chart,
invalidation, and scoring. Backend suite **126 passed / 0 failed**; no anti-goal violation introduced.

## Step 1 — Artifact verification

| Artifact | Status |
|----------|--------|
| `docs/handoffs/goal-i_can_see_the_wealthy_future-iter-4-dev.md` | ✅ present |
| `reports/reviews/goal-i_can_see_the_wealthy_future-iter-4-review.md` (PASS_WITH_NOTES) | ✅ present |
| `runs/goal-i_can_see_the_wealthy_future-iter-4/status.json` | ✅ present |
| `reports/qa/goal-i_can_see_the_wealthy_future-iter-4-test-plan.md` | ✅ present (executed) |
| `reports/audits/...-audit.md` | ⏳ not yet — audit step runs AFTER QA (dev handoff flags it as a downstream requirement). Not a QA blocker. |

## Step 2 — Backend test results (exact)

Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -v`
Log: `reports/qa/goal-i_can_see_the_wealthy_future-iter-4-test.log`

```
======================= 126 passed in 416.58s (0:06:56) ========================
```

**Exit code 0.** Key new/iter-4 tests (all PASSED):

- `test_indicators.py::test_sma_series_warmup_na_then_rolling`
- `test_indicators.py::test_sma_series_aligned_to_input_length`
- `test_indicators.py::test_sma_series_last_equals_sma_invariant`
- `test_bars.py::test_bars_ascending_all_dates_le_asof_no_lookahead`
- `test_bars.py::test_bars_ma_keyed_by_every_config_period_and_length_aligned`
- `test_bars.py::test_bars_ma_series_endpoint_equals_canonical_sma_single_source`
- `test_bars.py::test_bars_unknown_ticker_404`
- `test_bars.py::test_bars_503_when_no_price_data`
- `test_bars.py::test_bars_case_insensitive`
- `test_scoring.py::test_invalidation_level_is_canonical_sma_and_note_built_server_side`
- `test_scoring.py::test_invalidation_na_on_short_history_is_honest_never_fabricated`
- `test_scoring.py::test_themes_are_the_reverse_of_config_themes`
- `test_scoring.py::test_invalidation_and_themes_ride_on_the_shared_row_for_list_and_detail`
- `test_config_engine.py::test_real_config_exposes_invalidation_ma_period`
- `test_config_engine.py::test_missing_invalidation_block_raises`
- `test_config_engine.py::test_invalidation_ma_period_outside_ma_periods_raises`
- `test_no_magic_numbers.py::test_engine_calc_code_has_no_magic_numbers`

## Step 3 — Frontend build

`npm run build` was run by the developer (handoff): compiled + typechecked all 10 routes;
`/stocks/[ticker]` code-splits the charting lib. Independently corroborated this validation: the
live `next dev` server compiled and served `/`, `/stocks`, `/stocks/[ticker]`, `/themes`, `/sectors`
(all HTTP 200) and the detail page rendered the chart + new types without runtime/type errors. No
regression observed.

## Step 3.5 — Functional test plan results

| Test ID | Name | Type | Expected | Actual | Verdict | Notes |
|---------|------|------|----------|--------|---------|-------|
| TC-01 | `sma_series` warm-up NA + `[-1]==sma` invariant | api(unit) | NA prefix, rolling values, invariant holds | 3 `sma_series` tests PASSED | **PASS** | warm-up NA prefix exactly `period-1`; invariant test present & green |
| TC-02 | `/api/stocks/{ticker}/bars` happy path | api | 200; ascending; dates ≤ asof; `ma` keyed by every config period, length-aligned | Live: 1356 bars, asof 2026-05-28, ascending, all dates ≤ asof; `ma` keys `{20,50,150,200}`==config; every series len==1356; warm-up NA = `period-1` | **PASS** | `ma[50][-1]=198.734` |
| TC-03 | `/bars` errors 404 / 503 | api | unknown→404, no-data→503 | Live ZZZZ→**404** `{"detail":"unknown ticker: ZZZZ"}`; 503 covered by `test_bars_503_when_no_price_data` PASSED | **PASS** | no fabricated 200 |
| TC-04 | Invalidation == canonical `sma`, note server-built | api(int) | `level==sma(...)`, note in backend | Test PASSED; live `invalidation.level=198.73400026` == `ma[50][-1]`; note "Invalid below the 50-DMA at $198.73" served from API | **PASS** | single source proven end-to-end |
| TC-05 | Short-history → `level:null` + honest note | api(int) | null + "insufficient history", no fabrication | `test_invalidation_na_on_short_history_is_honest_never_fabricated` PASSED (note == "Invalidation level NA — insufficient history") | **PASS** | |
| TC-06 | Theme membership from `config.themes` | api(int) | `themes`==reverse of config, shared slug→name | Test PASSED; live NVDA themes = AI Data Centre, Semiconductors, Megacap Leaders | **PASS** | |
| TC-07 | J-06 list==detail incl new fields | api | detail row == list row (scores, buckets, components, invalidation, themes) | Live deep-compare of NVDA list vs detail: 10 shared keys, **0 mismatched**; invalidation + themes identical | **PASS** | byte-identical |
| TC-08 | No magic numbers; invalidation MA from config | api(unit) | no literal in calc; out-of-set period rejected | `test_no_magic_numbers` + 3 invalidation-config validator tests PASSED | **PASS** | |
| TC-09 | Full backend suite + frontend build | api+artifact | pytest 0 fail; build OK | 126 passed/0 failed; build compiles (dev + live-dev corroborated) | **PASS** | |
| TC-10 | J-05 browser: chart canvas, MA, volume, chips, invalidation | browser | populated canvas + chips + note + 3 score cards | 7 canvases; main pane **303,680 painted px** (candles+MA); volume + price/time axis canvases painted; chips render; "Invalid below the 50-DMA at $198.73"; Leadership/Entry Quality/Risk cards with buckets+components | **PASS** | evidence `TC-10-stock-detail-NVDA.png` |
| TC-11 | J-05 honest states: unknown + backend-down | browser | unknown→"Unknown ticker"; backend-down→"Backend unavailable"; NA honest | `/stocks/ZZZZ` → "Unknown ticker 'ZZZZ' is not in the scanned universe", **0 canvas, no fabricated chart**; backend-down "Backend unavailable" error state confirmed in `page.tsx:102` + `.catch` paths (loading/error states for both detail data and chart); short-history NA covered by backend test | **PASS** | evidence `TC-11-unknown-ticker.png`; backend-down verified by code inspection (managed backend not killed to avoid disrupting pipeline) |
| TC-12 | Anti-goal artifact checks | artifact | single MA source, no broker/secrets, models.py unchanged, handoffs | Frontend computes NO MA (plots server `ma` series; "RE-FORMATS server values only" preserved); no broker/order/secret matches (only "border"/"config order" false-positives); `models.py` **unchanged** (empty diff); dev handoff present; lightweight-charts no-key/no-callout | **PASS** | audit handoff is a downstream step, not a QA gate |

**12/12 test cases passed.**

## Step 4 — Chrome MCP browser checks

Frontend was managed on `http://localhost:3836`. During validation the managed `next dev` process
had died (the documented iters-1–3 SKIP/PASS flap); per the QA mode-2 / lesson-#1 directive I
self-healed it by restarting `scripts/start-frontend.sh` on the managed port 3836 (backend was up on
8835 throughout). Browser checks then ran against fresh, current code.

- **`/stocks` → click NVDA row → `/stocks/NVDA`:** lands on the detail page (heading "NVDA").
- **Chart canvas populated:** 7 canvas layers; the main price pane (1040×292) has **303,680
  non-transparent pixels** — candles + MA overlay lines actually drawn; separate volume/price-scale/
  time-axis canvases also painted. Confirmed from the evidence PNG, not a bare verdict. MA legend
  shows DMA overlays; volume histogram visible at the chart base.
- **Theme chips:** AI Data Centre, Semiconductors, Megacap Leaders (link to existing `/themes`).
- **Invalidation note (verbatim):** "Invalid below the 50-DMA at $198.73" — concrete level.
- **Three score cards unchanged:** Leadership 47.48, Entry Quality 66.24, Risk 33.79, each with
  A–E bucket and named component breakdowns.
- **Honest states:** unknown ticker `/stocks/ZZZZ` → "Unknown ticker … is not in the scanned
  universe", no canvas, no fabricated chart. Backend-down "Backend unavailable" state present in code.

Evidence: `reports/qa/goal-i_can_see_the_wealthy_future-iter-4-evidence/TC-10-stock-detail-NVDA.png`,
`reports/qa/goal-i_can_see_the_wealthy_future-iter-4-evidence/TC-11-unknown-ticker.png`.

## Step 4b — UI Evolution Audit

1. **Did the UI evolve to reflect the new capability?** Yes — the iter-3 "arrives next iteration"
   placeholder is replaced by a real candle chart (MA overlays + volume), theme chips, and an
   invalidation card.
2. **Can the user see, understand, and control the new capability?** Yes — chart is studied directly;
   the invalidation note tells the user where the idea is wrong in plain language; chips give theme
   context and link to `/themes`.
3. **Still relying on old generic pages?** No — all new info lives on the dedicated `/stocks/[ticker]`.
4. **Technically complete but product-underexposed?** No — the capability is front-and-center on the
   detail page.

**Verdict:** UI-PASS

## Anti-goal compliance

- **No lookahead:** `/bars` reads only `bars_asof`; live `max(bar.date)==asof` (2026-05-28), no later bar.
- **Single source of truth:** one `sma` definition; `invalidation.level == ma[50][-1]`; note built
  server-side and rendered verbatim; list==detail byte-identical (0 mismatches live + test).
- **No magic numbers:** invalidation MA from `config.decision_rules.invalidation.ma_period`; chart
  periods from `config.indicators.ma_periods`; `test_no_magic_numbers` green; out-of-set period rejected.
- **No fabricated data:** short-history → `level:null` + honest note + chart MA gaps; 404/503 preserved.
- **Snapshots immutable:** `models.py` unchanged (empty diff).
- **No order/execution path & no secrets:** no broker/order/credential code in new/changed source;
  lightweight-charts is client-side, no key, no runtime network callout.

## Blockers

None.

## Notes (non-blocking)

- The **audit handoff** (`reports/audits/…-audit.md`) is required at this full-depth iteration (missing
  in iter-2/iter-3) and is flagged by the dev handoff. It is produced by the audit step that runs after
  QA, so it is correctly absent now — surfaced here so the orchestrator runs the audit step.
- I started a replacement `next dev` on the managed port 3836 (the managed one had died) using the
  managed log path. It is left running on the expected port so downstream browser-qa/audit/demo steps
  find a live frontend rather than re-hitting the SKIP flap. Backend on 8835 was left untouched.
- Reviewer's two cosmetic NOTES (npm alphabetized deps; unreachable chart "empty" branch) confirmed
  harmless; no action needed.
