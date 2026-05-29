# goal-i_can_see_the_wealthy_future-iter-4 Functional Test Plan

**Phase:** goal-i_can_see_the_wealthy_future-iter-4
**Date:** 2026-05-29
**Frontend Present:** yes

## Phase Goal

Complete the Stock Detail page (`/stocks/[ticker]`) so opening a leader (e.g. NVDA) shows a price+MA candle chart with a volume series, theme-membership chips, and a concrete server-computed invalidation level alongside the three explainable scores — turning **J-05** green without regressing J-01–J-04 / J-06, and without violating any anti-goal (no lookahead, single source of truth, no magic numbers, no fabricated data).

## Test Cases

### TC-01 — `sma_series` rolling values + warm-up NA + `[-1] == sma` invariant

**Type:** api (unit test)
**Preconditions:** Backend venv installed; `apps/backend/app/engine/indicators.py` has `sma` and the new `sma_series`.

**Steps:**
1. `cd apps/backend && .venv/bin/python -m pytest tests/test_indicators.py -v`
2. Inspect cases covering `sma_series(values, period)`: first `period-1` indices are `None`/NA; subsequent indices equal the rolling simple MA; the invariant `sma_series(values, p)[-1] == sma(values, p)` holds for multiple periods.

**Expected outcome:** All `sma_series` tests pass; output length equals input length; warm-up prefix is NA.
**Pass criteria:** `test_indicators.py` exits 0; explicit assertions for the NA prefix and the `[-1] == sma(values, p)` invariant are present and pass.

---

### TC-02 — `GET /api/stocks/{ticker}/bars` happy path (ascending, no-lookahead, MA aligned)

**Type:** api
**Preconditions:** Backend seeded and running on its port; NVDA in `config.universe.symbols`; `latest_data_date` set.

**Steps:**
1. `curl -s http://localhost:8000/api/stocks/NVDA/bars` (use the project's actual backend port).
2. Inspect JSON: `asof_date`, `ticker`, `bars[]` (each `date, open, high, low, close, volume`), `ma` map.
3. Verify every `bars[i].date <= asof_date` (ascending order, no bar after as-of).
4. Verify `ma` has a key for every period in `config.indicators.ma_periods` ("20","50","150","200") and each `ma[p]` array length equals `bars.length`.

**Expected outcome:** 200 with ascending OHLCV bars all dated ≤ as-of and an `ma` map keyed by every config MA period, each series length-aligned 1:1 with `bars` (numbers, with `null` for warm-up gaps).
**Pass criteria:** HTTP 200; `bars` ascending and all dates ≤ `asof_date`; `ma` keys == `config.indicators.ma_periods`; `len(ma[p]) == len(bars)` for every `p`. (Backend test `test_bars`/`test_api_engine.py` covers this — must pass.)

---

### TC-03 — `/bars` error paths: 404 unknown ticker, 503 no price data

**Type:** api
**Preconditions:** Backend running.

**Steps:**
1. `curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/stocks/ZZZZ/bars` (ticker not in universe).
2. Confirm a known-symbol-but-no-data scenario (or backend with `latest_data_date` None) returns 503 — covered by the backend test case.

**Expected outcome:** Unknown ticker → 404; no price data → 503. Never a fabricated/empty-but-200 row.
**Pass criteria:** Status 404 for unknown ticker; status 503 for no-data; no 200 with synthesized/empty bars. Backend test asserting both passes.

---

### TC-04 — Invalidation level computed once, equals canonical `sma`

**Type:** api (unit/integration test)
**Preconditions:** Backend seeded; `config.decision_rules.invalidation.ma_period` set (default 50).

**Steps:**
1. `cd apps/backend && .venv/bin/python -m pytest tests/test_scoring.py -v`
2. Inspect: each per-stock row carries `invalidation = {basis, ma_period, level, price, note}`.
3. Verify `invalidation.level == sma(closes_asof(ticker), config invalidation ma_period)` — the same 50-DMA value that ends the `/bars` MA series.
4. Verify the human `note` string is built server-side (e.g. "Invalid below the 50-DMA at $<level>").

**Expected outcome:** Invalidation rides on the shared `score_stocks` row; `level` is the canonical `sma` over the config period; note assembled in backend.
**Pass criteria:** Test asserting `invalidation.level == sma(...)` passes; `ma_period` and `basis` derive from config (no `50` literal in calc code); note string present and server-built.

---

### TC-05 — Short-history ticker → invalidation `level: null` + honest note (no fabrication)

**Type:** api (unit/integration test)
**Preconditions:** A ticker (or fixture) with fewer than `ma_period` bars.

**Steps:**
1. Run `tests/test_scoring.py` short-history case.
2. Verify `invalidation.level is None` and `note` is an honest message (e.g. "Invalidation level NA — insufficient history") — no synthesized number.

**Expected outcome:** When the MA is not computable, `level` is null and the note honestly states NA; the `/bars` `ma` series shows a gap at that index, not an interpolated value.
**Pass criteria:** `level is None`; honest NA note; no fabricated numeric level anywhere.

---

### TC-06 — Theme membership computed from canonical `config.themes`

**Type:** api (unit/integration test)
**Preconditions:** Backend seeded; `config.themes` defines member lists.

**Steps:**
1. Run `tests/test_scoring.py` theme case.
2. Verify each row's `themes = [{slug, name}, ...]` lists every theme whose member list contains the ticker (`[]` if none).
3. Verify `name` uses the SAME `theme_name(slug)` derivation that `score_themes` uses (shared, not duplicated).

**Expected outcome:** `row.themes` is the reverse mapping of `config.themes`, with slug→name from the single shared source.
**Pass criteria:** `themes` matches the reverse of `config.themes` for sampled tickers; slug→name identical to `score_themes`; empty list for a ticker in no theme.

---

### TC-07 — J-06 guard: `/api/stocks/{ticker}` row byte-identical to `/api/stocks` list row (incl. new fields)

**Type:** api
**Preconditions:** Backend running and seeded.

**Steps:**
1. `curl -s http://localhost:8000/api/stocks` → extract the NVDA row.
2. `curl -s http://localhost:8000/api/stocks/NVDA` → extract its row.
3. Deep-compare both rows including the new `invalidation` and `themes` fields and the three scores/buckets/components.

**Expected outcome:** The detail row equals the matching list row exactly — scores, buckets, components, `invalidation`, and `themes` all identical (single source preserved; no second shape).
**Pass criteria:** Rows are byte-identical for shared fields incl. `invalidation` + `themes`; the extended list==detail backend guard passes; leaderboard still returns all rows.

---

### TC-08 — No magic numbers: invalidation MA basis sourced from config

**Type:** api (unit test)
**Preconditions:** `tests/test_no_magic_numbers.py` covers calc files incl. the new series helper / endpoint.

**Steps:**
1. `cd apps/backend && .venv/bin/python -m pytest tests/test_no_magic_numbers.py tests/test_config.py -v`
2. Verify `decision_rules.invalidation.ma_period` comes from config and is validated to be one of `indicators.ma_periods`; a value outside `ma_periods` is rejected.

**Expected outcome:** No invalidation/MA literal in calculation code; config validator rejects an out-of-set `ma_period`.
**Pass criteria:** Both test modules pass; no forbidden literal introduced in `indicators.py` / `scoring.py` / `stocks.py`.

---

### TC-09 — Full backend suite + frontend build (no regressions)

**Type:** api + artifact
**Preconditions:** Repo at iter-4 head.

**Steps:**
1. `cd apps/backend && .venv/bin/python -m pytest tests/ -v`
2. `cd apps/frontend && npm run build`

**Expected outcome:** All backend tests pass (≥109 prior + new); frontend compiles and typechecks (incl. the new `price-chart.tsx`, `fetchStockBars`, extended `StockRow`).
**Pass criteria:** pytest exits 0 with no failures/regressions; `npm run build` succeeds with no type errors.

---

### TC-10 — J-05 browser: chart canvas, MA overlays, volume, chips, invalidation render

**Type:** browser
**Preconditions:** Backend + frontend running (browser-qa must self-heal/start the frontend if down — see NOTES re SKIP/PASS flap; J-05 is canvas-rendered).

**Steps:**
1. Navigate to `/stocks`; click a leader row (e.g. NVDA) → lands on `/stocks/NVDA`.
2. Verify the price candle chart `<canvas>` actually renders candles (not just that the page loaded).
3. Verify MA overlay lines are visible and a volume series/sub-pane is visible.
4. Verify theme-membership chips render; clicking a chip reaches the existing `/themes` (if linked).
5. Verify the invalidation note renders verbatim with a concrete level (e.g. "Invalid below the 50-DMA at $X").
6. Verify the three score cards still show A–E bucket + 0–100 value + ≥3 named components.
7. Save a screenshot to the iteration evidence dir (`reports/qa/<phase>-evidence/TC-10-stock-detail.png`).

**Expected outcome:** Stock Detail shows a populated candle chart with MA overlays + volume, theme chips, a concrete invalidation note, and the unchanged three explainable scores.
**Pass criteria:** Chart canvas is visibly populated (candles + MA lines + volume — confirmed from the evidence PNG, not a bare verdict); chips + invalidation note + three score cards all present; screenshot saved.

---

### TC-11 — J-05 honest states: unknown ticker + backend-down

**Type:** browser
**Preconditions:** Frontend running.

**Steps:**
1. Navigate to `/stocks/ZZZZ` (unknown ticker) → verify the "Unknown ticker" state renders (no fabricated chart).
2. With the backend stopped, load `/stocks/NVDA` → verify the "Backend unavailable" state renders; the chart shows an honest error/empty state, not synthesized data.
3. Confirm a short-history ticker (if present) renders the chart with MA gaps and the honest NA invalidation note (no fabricated number).
4. Save evidence screenshots under `reports/qa/<phase>-evidence/`.

**Expected outcome:** Error/empty/NA states behave honestly and match existing dark-workstation styling; no fabricated prices or invalidation values.
**Pass criteria:** Unknown ticker → "Unknown ticker"; backend down → "Backend unavailable"; NA invalidation → honest note + chart gaps; no synthesized data shown.

---

### TC-12 — Anti-goal artifact checks (single source, no broker path, no secrets, snapshots immutable, audit handoff)

**Type:** artifact
**Preconditions:** iter-4 diff complete.

**Steps:**
1. Grep new/changed frontend (`page.tsx`, `price-chart.tsx`, `lib/api.ts`) to confirm the MA is plotted from the server `ma` series and **no** MA is computed from the close array client-side; `lib/api.ts` keeps "RE-FORMATS server values only".
2. Grep new/changed source to confirm no brokerage/order/execution path and no hard-coded credentials/keys/tokens; confirm `lightweight-charts` adds no key/credential and no runtime network callout (supply-chain gate cleared).
3. Confirm `apps/backend/app/models.py` is UNCHANGED (no persistence this iteration).
4. Confirm dev handoff exists at `docs/handoffs/goal-i_can_see_the_wealthy_future-iter-4-dev.md`.
5. Confirm the **audit handoff** was emitted (full-depth requirement; missing in iter-2/iter-3).

**Expected outcome:** Single MA source; frontend computes no MA; no order path; no secrets; charting lib is no-key/no-callout; `models.py` unchanged; both dev and audit handoffs present.
**Pass criteria:** No client-side MA computation; no broker/order code; no hard-coded secrets; `models.py` diff empty; dev handoff and audit handoff files both exist.

---

## Summary

Total test cases: 12
API tests (incl. backend unit/integration): 7 (TC-01, TC-02, TC-03, TC-04, TC-05, TC-06, TC-07, TC-08, TC-09 backend portion)
Browser tests: 2 (TC-10, TC-11)
Artifact checks: 2 (TC-09 frontend-build portion, TC-12)

> Coverage note: TC-01–TC-09 cover the DEFINITION OF DONE backend criteria and anti-goal computational guarantees (no lookahead, single source, no magic numbers, no fabrication). TC-10–TC-11 cover the J-05 browser acceptance and honest-state requirements. TC-12 covers the remaining anti-goal + process (audit handoff) artifact checks.
