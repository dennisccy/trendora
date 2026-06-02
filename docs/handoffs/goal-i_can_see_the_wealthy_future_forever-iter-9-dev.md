# goal-i_can_see_the_wealthy_future_forever-iter-9 Dev Handoff

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-9
**Date:** 2026-06-02
**Agent:** developer
**Status:** complete

## What Was Built

Two new config-driven detected price patterns beyond VCP (J-28), each held to the identical
"pattern-not-status" contract VCP follows — computed once with date ≤ D, price+volume only, riding
alongside the setup status, never a setup, never alone making a name Actionable, stored on the
immutable snapshot, read verbatim everywhere.

- **`detect_pullback_to_rising_dma`** — flags an uptrend that has pulled back *to* its rising MA: the
  `ma_period`-day MA must be rising ≥ `min_dma_slope_pct` over `trend_lookback_bars`; the close within
  `max_dist_above_dma_pct` above / `max_undercut_pct` below the MA; pullback from the recent high ≤
  `max_pullback_depth_pct`. Pivot = recent high; invalidation = the rising MA.
- **`detect_flat_base_breakout`** — flags a shallow base at the highs, breakout-ready: base range ≤
  `max_base_depth_pct` over `base_window`; base high is the `lookback_bars`-window high (at the highs);
  close within `pivot_proximity_pct` below the base high; recent volume ≥ `min_breakout_volume_ratio`
  of the base average. Pivot = base high; invalidation = base low.
- **Config:** `patterns.pullback_to_rising_dma` + `patterns.flat_base_breakout` (every threshold), and
  one `kind: pattern` `methodology.entries` catalog entry per pattern (numeric rows are `ref:` paths
  only — never re-typed). Thresholds tuned against the committed seed (see Tuning below).
- **Config model:** `PullbackToRisingDmaCfg` + `FlatBaseBreakoutCfg` Pydantic sub-models (mirror
  `VcpCfg`) with range validators; cross-field `pullback_to_rising_dma.ma_period ∈ indicators.ma_periods`
  on the top-level `Config` validator (where VCP's invalidation `ma_period` is also cross-checked).
- **Composition:** at the existing VCP call site in `scoring.py` each new detector is called on the
  SAME ≤ D bars and attached as `row["pullback_to_rising_dma"]` / `row["flat_base_breakout"]`.
  `row["vcp"]` is byte-identical (untouched); `setup` is never touched.
- **Persistence:** two indexed boolean mirror columns on `ScannerResult`
  (`is_pullback_to_rising_dma`, `is_flat_base_breakout`), written once in the single `ScannerResult(...)`
  construction from `row["<name>"]["flagged"]`. `record_json` carries the full pattern blocks losslessly.
- **Forward-test:** `compute_forward_aggregates` reads the new mirrors onto each observation and emits
  `by_pullback_to_rising_dma` + `by_flat_base_breakout` via the existing generic `_group_means`
  (both True/False cohorts always emitted; cohort < `min_sample` shows `n` + NA).
- **Frontend:** `api.ts` types per pattern + `StockRow`/`SystemHealthResponse` extensions; `/stocks`
  pattern filter (generalized from the VCP `<Select>`) + per-pattern badges/tooltips; `/stocks/[ticker]`
  per-pattern badge + card; `/system-health` two new breakdown panels; `/methodology` auto-renders the
  two new cards from the catalog (no per-pattern code; only the subtitle copy was de-VCP-specified).
- **DB regenerated** offline from the frozen seed so every immutable snapshot carries the new flags.

## Files Changed

**Backend**
- `config.yaml` — `patterns.pullback_to_rising_dma` + `patterns.flat_base_breakout` blocks; two
  `kind: pattern` `methodology.entries` catalog entries (ref-only numeric rows).
- `apps/backend/app/config.py` — `PullbackToRisingDmaCfg` + `FlatBaseBreakoutCfg` sub-models +
  `PatternsCfg` fields + the top-level `ma_period ∈ indicators.ma_periods` cross-validator.
- `apps/backend/app/engine/patterns.py` — `detect_pullback_to_rising_dma`,
  `detect_flat_base_breakout` (+ `_no_pullback` / `_no_flat_base` helpers); imports `indicators`.
- `apps/backend/app/engine/scoring.py` — calls both new detectors at the VCP site; attaches the two
  new row keys. (VCP call + `row["vcp"]` unchanged.)
- `apps/backend/app/models.py` — `is_pullback_to_rising_dma`, `is_flat_base_breakout` indexed bool
  columns on `ScannerResult`.
- `apps/backend/app/engine/scanner.py` — writes the two new mirrors in the single `ScannerResult(...)`.
- `apps/backend/app/engine/forward_testing.py` — `PULLBACK_LABELS` / `FLAT_BASE_LABELS`; reads the new
  mirrors onto observations; `by_pullback_to_rising_dma` + `by_flat_base_breakout` breakdowns.

**Backend tests (extended existing files — no parallel suites)**
- `tests/test_patterns.py` — positive / negative / short-history / config-driven / deterministic proofs
  for each new detector.
- `tests/test_scoring.py` — new-pattern blocks ride each row; force-flagging each new pattern changes no
  setup status (pattern-not-status).
- `tests/test_scanner.py` — `is_<name>` mirrors `record_json["<name>"]["flagged"]` for every result.
- `tests/test_forward_testing.py` — `by_<name>` groups by the stored mirror exactly (exact means);
  empty cohort NA-padded (both rows, n=0/mean None). `_add_result` helper extended with the new flags.
- `tests/test_api_system_health.py` — both `by_<name>` breakdowns present in the payload with `n`.
- `tests/test_api_engine.py` — keystone (patch-to-raise): with both detectors AND the score_* engines
  patched to raise, `/api/stocks` (list+detail) and the System Health `by_<name>` still serve.
- `tests/test_no_magic_numbers.py` — added the distinctive integer sentinels (40, 18, 25, 15) so the
  guard ENFORCES that the new detectors' thresholds come from config, not literals.
- `tests/test_config.py` — `MINIMAL_VALID` extended with the two now-required blocks; validation-failure
  cases (ma_period not an indicator period, insufficient history, non-positive percent/ratio,
  base_window > lookback) + `max_undercut_pct` may be 0.
- `tests/test_methodology.py` — new-pattern catalog numbers match config (live refs); dropping a pattern
  catalog entry fails `build_catalog` (pattern completeness).

**Frontend**
- `apps/frontend/lib/api.ts` — `PullbackToRisingDma` + `FlatBaseBreakout` interfaces; `StockRow`
  extended; `ForwardPullbackRow` + `ForwardFlatBaseRow`; `SystemHealthResponse.by_<name>`.
- `apps/frontend/app/stocks/page.tsx` — VCP `<Select>` generalized into a per-pattern filter (registry-
  driven); badges + tooltips rendered per flagged pattern from the registry.
- `apps/frontend/app/stocks/[ticker]/page.tsx` — per-pattern header badge + detail card (VCP unchanged).
- `apps/frontend/app/system-health/page.tsx` — two new `BreakdownPanel`s for `by_<name>`.
- `apps/frontend/app/methodology/page.tsx` — subtitle de-VCP-specified (cards already auto-render).

## Tuning (against the committed seed — offline, deterministic)

Latest snapshot (2026-05-28, Risk-on, 122 names): VCP 4, pullback-to-rising-DMA 9, flat-base 3 — a
sensible non-trivial set (some / not all / not none). Both Risk-Off bootstrap dates still label
"Risk-off" (J-07/J-08 intact); the sharp-selloff date (2025-04-04) honestly flags none of the three.
Across the full walk-forward at the 20-day horizon the new cohorts clear `min_sample` (pullback n≈163,
flat-base n≈48); the VCP cohort sits below it and is shown as honest NA. No threshold was loosened to
manufacture flags or forward-test sample.

## Tests Run

Command (backend): `cd apps/backend && .venv/bin/python -m pytest tests/`
Result: **351 passed, 0 failed, 4 skipped** (net). The single full-suite run reported 348 passed /
3 failed / 4 skipped in 18m35s; all 3 failures were **test-only** synthetic config fixtures
(`test_config_engine.py`, `test_sectors.py`, `test_themes.py`) that build a Config dict and were
missing the two now-required pattern blocks — the same "newly-required section" update already applied
to `test_config.py::MINIMAL_VALID`. Fixed in those three fixtures and re-verified: `pytest
tests/test_config_engine.py tests/test_sectors.py tests/test_themes.py` → **51 passed**. The fixes are
test-only (no production code), so the other 348 are unaffected.

New backend tests added this iteration (all passing): pattern detectors (positive/negative/short-
history/config-driven/deterministic, ×2 patterns), pattern-not-status, mirror==record_json,
by_<name> forward-test grouping + NA-pad, system-health by_<name> present, the patch-to-raise
read-path keystone, no-magic-number sentinels, and config-validation cases.

Command (frontend): `cd apps/frontend && npm run build`
Result: PASS — compiled + typechecked all 13 routes successfully.

## DB Regeneration + Live Verification

Regenerated `apps/backend/data/trendora.db` offline from the frozen seed (delete + lifespan rebuild;
no network). Verified on the regenerated DB and via the live API (`start-backend.sh` on port 8835,
booted cleanly, served, then stopped by port):
- Latest snapshot (2026-05-28, Risk-on): flagged vcp=4, pullback_to_rising_dma=9, flat_base_breakout=3
  of 122 — a non-trivial set (some/not all/not none).
- Mirror integrity: `is_<name>` == `record_json["<name>"]["flagged"]` for all 122 latest results.
- Risk-Off guard intact: both `scanner.bootstrap_dates` (2022-10-07, 2025-04-04) still label "Risk-off".
- Forward-test cohorts at the 20-day default horizon: by_pullback_to_rising_dma n=163/1055,
  by_flat_base_breakout n=48/1170 (both clear min_sample=30); by_vcp n=27 shows honest NA below it.
- `/api/stocks`, `/api/stocks/{ticker}`, `/api/system-health`, `/api/methodology` all serve the new
  fields/cards/breakdowns. No server left running (stopped by port 8835).

## Known Issues

- Honest small-sample cohorts: a pattern that flags few names can yield a `by_<name>` cohort below
  `walk_forward.min_sample` (30) at some horizons; those show NA + `n`, never a fabricated number.
- No `/research` code in this diff (out of scope; the `/research` nav entry was front-loaded into the
  blueprint by the decomposer only). No change to the six canonical scores, A–E buckets, setup-status
  enum, regime engine, as-of control, or watchlist.

## Suggested Next Phase

With J-28 closing the autonomous compute-only wave, the next iteration is positioned to begin the
`/research` labs (J-25–J-31) under the now-front-loaded `/research` nav home — pending the one-time
blueprint re-approval the decomposer requested. The J-22/23/24 universe-expansion journeys remain
externally data-walled (Yahoo 429) and should not be auto-redispatched.
