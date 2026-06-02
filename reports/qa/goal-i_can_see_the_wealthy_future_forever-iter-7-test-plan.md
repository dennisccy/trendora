# goal-i_can_see_the_wealthy_future_forever-iter-7 Functional Test Plan

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-7
**Date:** 2026-06-02
**Frontend Present:** yes

## Phase Goal

Replace the 122-name hand-curated stock universe (J-22) with a transparent, reproducible, config-recorded screen resolving to ~400–500 real US names — each backed by committed real OHLCV + GICS sector + a stored screen-pass market cap — and surface the selection methodology read-only on `/methodology` (rule + 3 config thresholds + resolved size) and the grown count on `/data`, with all critical anti-goals (no-lookahead, immutable snapshots, single-source/no-recompute, Risk-Off gating, no fabricated data, no secrets) preserved and J-01…J-21 still green.

## Test Cases

### TC-01 — Universe resolves to ~400–500 real screened names
**Type:** artifact
**Preconditions:** Seed-build/screen step has run; `config.yaml` committed.
**Steps:**
1. Count entries in `config.yaml` `universe.symbols`.
2. Confirm every symbol has a committed CSV under `apps/backend/data/seed/prices/<SYM>.csv` with non-empty real OHLCV.
3. Confirm every symbol has a `stock_sectors` mapping to a valid `etfs.sector` GICS name.
**Expected outcome:** ~400–500 symbols (≫ the prior 122), each with committed prices + a sector.
**Pass criteria:** `len(universe.symbols)` in 380–520 band; zero symbols missing a CSV; zero symbols missing a valid `stock_sectors` entry.

### TC-02 — Screen application: all members pass all three thresholds
**Type:** api (unit/integration test)
**Preconditions:** Committed screen record (`universe.json`/`meta.json`) with per-member reference cap/ADV/price.
**Steps:**
1. Run the screen-application unit test over the resolved universe.
2. For each member assert `close ≥ universe.filters.min_price`, `ADV (close×vol) ≥ min_dollar_vol`, `market_cap ≥ min_market_cap`.
**Expected outcome:** Every resolved member passes all three config thresholds against its committed reference values.
**Pass criteria:** Test passes with zero members failing any threshold; thresholds read from `config.universe.filters` (not literals).

### TC-03 — Screen failure path: below-threshold candidate is EXCLUDED
**Type:** api (unit test)
**Preconditions:** Fixture candidate below one threshold (price OR dollar-vol OR market cap).
**Steps:**
1. Feed the fixture candidate through the screen.
2. Assert it is NOT in the resulting membership.
**Expected outcome:** Below-threshold candidate excluded from the universe (exclusion asserted, not just inclusion).
**Pass criteria:** Excluded candidate absent from resolved membership; exclusion is logged.

### TC-04 — Fetch failure path: omitted + logged, never fabricated
**Type:** api (unit test)
**Preconditions:** Fixture candidate whose fetch fails / returns empty/partial series.
**Steps:**
1. Run the build step against the failing fixture.
2. Inspect membership and the build log.
**Expected outcome:** Symbol omitted from membership and recorded in the omitted/failed log; no interpolated/synthesized bars.
**Pass criteria:** Symbol absent from `universe.symbols`; appears in omitted log; no fabricated CSV rows exist.

### TC-05 — No magic numbers + config validation green over expanded universe
**Type:** api (unit test)
**Preconditions:** Expanded `config.yaml`.
**Steps:**
1. Run `test_no_magic_numbers` and the config-validation suite.
**Expected outcome:** Screen reads thresholds only from `config.universe.filters`; every universe symbol has a valid sector; every theme member is in the universe.
**Pass criteria:** Both suites pass; no int literal introduced in `methodology.py`/calc code.

### TC-06 — No-lookahead re-asserted over the new universe
**Type:** api (unit test)
**Preconditions:** Regenerated snapshots + forward returns over expanded seed.
**Steps:**
1. Run the walk-forward no-lookahead test.
**Expected outcome:** As-of-D snapshot uses only bars ≤ D; forward returns only bars > D.
**Pass criteria:** Test passes over the expanded seed.

### TC-07 — Snapshots immutable / create-once
**Type:** api (unit/integration)
**Preconditions:** Regenerated bootstrap snapshots.
**Steps:**
1. Confirm regenerated snapshots are create-once; existing run result rows not mutated.
2. Confirm `forward_returns` is a separate append-only table (> D).
**Expected outcome:** No in-place mutation of existing snapshot rows; forward returns append-only.
**Pass criteria:** Immutability/append-only invariants assert true in the test suite.

### TC-08 — Single source of truth: scores/bucket identical list↔detail
**Type:** api
**Preconditions:** Backend running; a sampled NEW universe name (ticker T).
**Steps:**
1. `curl -s http://localhost:8000/api/stocks` → find T's six scores + A–E bucket.
2. `curl -s http://localhost:8000/api/stocks/<T>` → read same fields.
**Expected outcome:** Three/six scores + bucket identical in list and detail; served `market_cap` comes from storage.
**Pass criteria:** HTTP 200 both; per-field equality for T; `market_cap` matches committed record (not recomputed).

### TC-09 — Risk-Off gating (code-level, J-07)
**Type:** api (unit/integration)
**Preconditions:** Chosen Risk-off bootstrap date confirmed/swapped in `scanner.bootstrap_dates`.
**Steps:**
1. Run the chosen Risk-off bootstrap run under the new universe.
2. Count Actionable stocks.
**Expected outcome:** Zero Actionable in a Risk-off regime.
**Pass criteria:** Actionable count == 0 for the Risk-off bootstrap run.

### TC-10 — Bootstrap dates still label Risk-off (J-07/J-08)
**Type:** api (unit/integration)
**Preconditions:** Expanded universe; `scanner.bootstrap_dates` (with any documented swap).
**Steps:**
1. Compute regime label for each configured bootstrap date.
2. Confirm ≥2 differing dated runs exist (J-08).
**Expected outcome:** Each bootstrap date used by J-07/J-08 labels Risk-off; ≥2 differing dated runs available.
**Pass criteria:** Configured Risk-off bootstrap date(s) label "Risk-off"; any swap documented in dev handoff; ≥2 dated runs differ.

### TC-11 — Coverage/universe consistency: one source, no drift
**Type:** api
**Preconditions:** Backend running.
**Steps:**
1. `curl -s http://localhost:8000/api/data` → read universe-member count.
2. `curl -s http://localhost:8000/api/methodology` → read resolved universe size.
3. Compare both to `len(config.universe.symbols)`.
**Expected outcome:** `/api/data` universe count == `/api/methodology` size == `len(resolved universe)`.
**Pass criteria:** All three equal; HTTP 200 both endpoints.

### TC-12 — `/api/methodology` Universe Selection payload (config-backed)
**Type:** api
**Preconditions:** Backend running.
**Steps:**
1. `curl -s http://localhost:8000/api/methodology`.
2. Locate the Universe Selection section.
**Expected outcome:** Section contains the membership-rule prose, the three screen thresholds resolved live from `universe.filters` (min market cap / min dollar vol / min price), and the resolved member count.
**Pass criteria:** HTTP 200; thresholds equal config `universe.filters` values; member count == resolved universe size; no re-typed literal numbers.

### TC-13 — J-22 browser read flow on /methodology + /data
**Type:** browser
**Preconditions:** Frontend on :3000, backend on :8000.
**Steps:**
1. Navigate to `/methodology`; locate the Universe Selection section.
2. Read the membership rule + the three thresholds; assert they match config.
3. Read the resolved universe size; confirm ~400–500.
4. Navigate to `/data`; confirm the universe/symbol count shows the same grown value.
**Expected outcome:** Universe Selection rule + 3 config thresholds + size visible; `/data` shows the same grown count.
**Pass criteria:** Both pages render; size ~400–500 and identical across pages; thresholds match config; evidence screenshots saved under `reports/qa/<phase>-evidence/` (de-duped by sha256).

### TC-14 — J-22 /stocks renders many more ranked rows
**Type:** browser
**Preconditions:** Frontend + backend running.
**Steps:**
1. Navigate to `/stocks`.
2. Count ranked rows (account for pagination/total count display).
**Expected outcome:** Far more ranked rows than the prior 122 (≫ before).
**Pass criteria:** Total ranked-stock count ≫ 122 (consistent with ~400–500 universe).

### TC-15 — Regression J-07: Risk-off run shows zero Actionable (browser)
**Type:** browser
**Preconditions:** Frontend + backend running.
**Steps:**
1. Open the Risk-off bootstrap run in the UI.
2. Assert regime label = Risk-off; count Actionable rows.
**Expected outcome:** Zero Actionable stocks displayed.
**Pass criteria:** Actionable count == 0; live DOM asserted before capture.

### TC-16 — Regression J-02: sector + Actionable filters narrow rows
**Type:** browser
**Preconditions:** `/stocks` loaded.
**Steps:**
1. Record total row count.
2. Apply a sector filter, then the Actionable filter.
3. Record row count after each.
**Expected outcome:** Each filter reduces (narrows) the visible rows.
**Pass criteria:** Filtered count < unfiltered count for each filter; URL/state reflects filter.

### TC-17 — Regression J-01: dashboard regime + counts + breadth render
**Type:** browser
**Preconditions:** Dashboard loaded.
**Steps:**
1. Open dashboard; read regime label, bucket counts, breadth metrics.
2. Confirm breadth/new-high-low labelled "universe-relative".
**Expected outcome:** Valid regime label + counts + breadth render; honest-limitation label intact.
**Pass criteria:** All elements present; "universe-relative" label present on breadth/new-high-low.

### TC-18 — Regression J-06: a named stock's three scores identical leaderboard↔detail
**Type:** browser
**Preconditions:** Frontend + backend running.
**Steps:**
1. Pick a named stock on the leaderboard; record its three scores.
2. Open its detail page; read the same scores; confirm ≥3 components.
**Expected outcome:** Scores identical across leaderboard and detail.
**Pass criteria:** Per-score equality; detail shows ≥3 score components.

### TC-19 — Regression J-16: VCP filter → badge → detail → glossary → System Health by-VCP
**Type:** browser
**Preconditions:** Frontend + backend running.
**Steps:**
1. Apply VCP filter on `/stocks`; confirm rows show a VCP badge.
2. Open a VCP stock detail; confirm VCP status.
3. Confirm VCP defined in glossary/methodology.
4. On System Health, view the by-VCP breakdown.
**Expected outcome:** VCP flows consistent end-to-end.
**Pass criteria:** Badge present, detail consistent, glossary entry present, by-VCP renders with `n`.

### TC-20 — Regression J-09: by-bucket + control groups render with n
**Type:** browser
**Preconditions:** System Health / backtest page loaded.
**Steps:**
1. Open by-bucket view; confirm rows + `n` per bucket.
2. Open control-group view; confirm `n`.
3. Confirm walk-forward evidence labelled survivorship-biased.
**Expected outcome:** By-bucket + control groups render with sample sizes; honest label intact.
**Pass criteria:** Each group shows a numeric `n`; "survivorship-biased" label present.

### TC-21 — Regression J-11: add a screened name + persistence
**Type:** browser
**Preconditions:** Watchlist feature available; backend persists watchlist.
**Steps:**
1. Add a NEW screened universe name to the watchlist (validates against new universe).
2. Restart backend (or reload) and re-open watchlist.
**Expected outcome:** Add validates against the expanded universe; entry survives restart.
**Pass criteria:** New name accepted + visible; still present after restart.

### TC-22 — Regression J-17: coverage symbol count grew
**Type:** browser
**Preconditions:** `/data` loaded.
**Steps:**
1. Read the coverage symbol/universe count.
2. Confirm live-fetch/backfill controls still function (unchanged behavior).
**Expected outcome:** Coverage reflects the grown universe; controls unchanged.
**Pass criteria:** Count grew (≫ prior); fetch/backfill controls present and operable.

### TC-23 — Full backend/integration suite green; no secrets committed
**Type:** artifact / api
**Preconditions:** Expanded seed + config committed.
**Steps:**
1. Run the backend test suite once (do not run concurrent pytest — see project memory).
2. Grep committed seed/scripts/config for any API key/secret.
**Expected outcome:** Suite passes over the new universe; no committed secret; any live-provider key is environment-only.
**Pass criteria:** Test suite exits 0 with no regressions; zero secrets found in source/seed.

## Summary

Total test cases: 23
API tests (incl. unit/integration): 11 (TC-02, TC-03, TC-04, TC-05, TC-06, TC-07, TC-08, TC-09, TC-10, TC-11, TC-12)
Browser tests: 10 (TC-13, TC-14, TC-15, TC-16, TC-17, TC-18, TC-19, TC-20, TC-21, TC-22)
Artifact checks: 2 (TC-01, TC-23) — TC-23 spans artifact + api

Coverage notes: TC-13/TC-14 cover the J-22 acceptance flow; TC-15–TC-22 cover the required-still-passing regression sweep (J-07, J-02, J-01, J-06, J-16, J-09, J-11, J-17). Critical anti-goals are pinned by TC-03/TC-04 (no fabricated data), TC-05 (no magic numbers), TC-06/TC-07 (no-lookahead + immutable snapshots), TC-08/TC-11/TC-12 (single source / no recompute), TC-09/TC-10 (Risk-Off gating), TC-23 (no secrets).
