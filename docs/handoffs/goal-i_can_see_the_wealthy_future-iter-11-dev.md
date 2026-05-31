# goal-i_can_see_the_wealthy_future-iter-11 Dev Handoff

**Phase:** goal-i_can_see_the_wealthy_future-iter-11
**Date:** 2026-05-31
**Agent:** developer
**Status:** complete

## What Was Built

J-16 — **VCP (Volatility Contraction Pattern)**: the product's first detected price pattern, a
config-driven flag that rides each stock's immutable snapshot row **alongside** (never replacing) its
setup status — filterable + explained + forward-tested.

- **New detector `app/engine/patterns.py :: detect_vcp(closes, highs, lows, volumes, cfg)`** — pure,
  deterministic, price+volume only, NA-graceful, config-driven. Detects progressively-shallower
  contractions (via a percent-reversal **ZigZag** swing detector, so it captures lower-high coiling
  below an established pivot — the canonical VCP shape) + volume dry-up into a pivot near the base high,
  reading only the passed as-of series (date ≤ D → no lookahead). Returns
  `{flagged, reason, pivot, invalidation:{level,note}, contractions, detail}`. Insufficient history or
  no qualifying base → `flagged=False` with an honest reason and **no fabricated pivot/level**.
- **`config.yaml` → new `patterns.vcp` block** with every threshold; **`config.py` → typed `VcpCfg` +
  `PatternsCfg`** (`patterns: PatternsCfg` on `Config`) validated like `WalkForwardCfg` (positive
  windows/counts, `0 < contraction_shrink_ratio ≤ 1`, positive percentages, `min ≤ max` contractions).
- **`scoring.py` → composes `row["vcp"]`** onto each `score_stocks` row in pass-3, reusing the as-of
  bars already read for the invalidation level (no extra DB round-trip). `classify_setup` / the setup
  block / the setup vocabulary are **untouched**.
- **`models.py` → one append-only column `ScannerResult.is_vcp`** (the denormalized mirror of
  `record_json`'s `vcp.flagged`); **`scanner.py` → populates it** in `run_scan` from the same single
  `detect_vcp` output.
- **`forward_testing.py` → `by_vcp` dimension** on `compute_forward_aggregates`: two cohorts
  (VCP / non-VCP) reading the stored `is_vcp` verbatim (never re-detected), each with mean return + `n`,
  padded to NA when empty. Served unchanged by `GET /api/system-health`. `compute_run_scorecard` (J-14)
  left unchanged.
- **Frontend**: `lib/api.ts` (`Vcp` type + `vcp` on `StockRow`; `ForwardVcpRow` + `by_vcp` on
  `SystemHealthResponse`); `/stocks` (VCP filter Select + teal VCP badge with reason/pivot/invalidation
  tooltip); `/stocks/[ticker]` (header VCP badge + dedicated VCP card with pivot + invalidation +
  contractions, or an explicit "No VCP pattern detected"); `/system-health` ("Forward return: VCP vs
  non-VCP" panel reusing `BreakdownPanel` + the shared `Return`/`SampleSize` formatters).

## Files Changed

- `config.yaml` — new `patterns.vcp` block (every VCP threshold; tuned vs the committed seed).
- `apps/backend/app/config.py` — `VcpCfg` + `PatternsCfg` typed/validated; `patterns` on `Config`.
- `apps/backend/app/engine/patterns.py` — **NEW** `detect_vcp` + ZigZag swing/contraction helpers.
- `apps/backend/app/engine/scoring.py` — compose `vcp` onto each row (reuse as-of bars); docstring.
- `apps/backend/app/models.py` — append-only `ScannerResult.is_vcp` mirror column.
- `apps/backend/app/engine/scanner.py` — set `is_vcp` mirror in `run_scan`.
- `apps/backend/app/engine/forward_testing.py` — `is_vcp` on stock_obs + `by_vcp` payload dimension.
- `apps/backend/app/engine/setups.py` — **UNCHANGED** (asserted; VCP never enters `ALL_STATUSES`).
- `apps/backend/tests/test_patterns.py` — **NEW** detector unit tests (positive/negative/NA/config-driven).
- `apps/backend/tests/test_no_magic_numbers.py` — `patterns.py` added to `CALC_FILES`; `8`,`35` added to forbidden ints.
- `apps/backend/tests/test_scoring.py` — vcp block shape + VCP-is-a-pattern-not-a-status (forced-flag) proof.
- `apps/backend/tests/test_scanner.py` — `is_vcp == record_json` mirror + risk-off flagged-rows-stay-watchlist.
- `apps/backend/tests/test_forward_testing.py` — `_add_result(is_vcp=...)` + `by_vcp` exact-means + empty-cohort NA.
- `apps/backend/tests/test_api_engine.py` — **keystone** (patch detect_vcp + score_* to raise → reads still serve stored).
- `apps/backend/tests/test_api_system_health.py` — `by_vcp` breakdown present with cohorts + n.
- `apps/backend/tests/test_config.py`, `test_config_engine.py` — `patterns` added to fixtures + VCP validation tests.
- `apps/backend/tests/test_sectors.py`, `test_themes.py` — `patterns` key added to synthetic config dicts.
- `apps/frontend/lib/api.ts` — `Vcp` type + `vcp` on `StockRow`; `ForwardVcpRow` + `by_vcp`.
- `apps/frontend/app/stocks/page.tsx` — VCP filter + badge + empty-state.
- `apps/frontend/app/stocks/[ticker]/page.tsx` — VCP badge + VCP card.
- `apps/frontend/app/system-health/page.tsx` — `by_vcp` breakdown panel.

## Tests Run

Backend command: `cd apps/backend && .venv/bin/python -m pytest tests/ -v`
- Result (full suite): **234 passed, 0 failed** in 1755s (~29 min — the walk-forward lifespan fixtures dominate).
- Verified individually during development: `test_patterns.py` 6 passed, `test_config*.py` 46 passed,
  `test_no_magic_numbers.py` 2 passed, `test_scoring.py` 12 passed.

Frontend command: `cd apps/frontend && npm run build`
- Result: **clean** — typecheck passed with the new `vcp` field on `StockRow`; all 11 routes compiled.

Live end-to-end verification (services booted on 8835/3835 against the rebuilt seed DB):
- `/api/stocks` (latest 2026-05-28): 4 VCP-flagged — STX (Extended), TSLA/TSM/ORCL (Avoid) — **none Actionable**.
- J-06 coherence: STX `vcp` byte-identical between `/api/stocks` and `/api/stocks/STX`.
- `/api/system-health`: `by_vcp` = VCP +3.18% (n=27 ⚠ low-sample) vs non-VCP +2.01% (n=1191) @ 20d.
- Browser evidence (4 distinct PNGs, md5-distinct) in
  `reports/evidence/goal-i_can_see_the_wealthy_future-iter-11/`:
  `01-leaderboard-vcp-filtered.png`, `02-detail-STX-vcp.png`, `03-system-health-by-vcp.png`,
  `04-detail-ORCL-vcp.png`.

## Known Issues

- The VCP forward-test cohort is small (n=27 @ 20d, below the 30 min-sample) — surfaced honestly with an
  ⚠ marker; the +3.18% vs +2.01% edge is indicative, not conclusive.
- The dedicated browser-qa runner has SKIPped for several iterations (runner-owner debt, non-gating);
  per the iter-7/iter-10 precedent the developer self-produced the live browser evidence above.
- First backend boot rebuilds the DB + runs the walk-forward backfill and takes ~8–9 minutes (expected).

## Suggested Next Phase

**J-12** — the `/methodology` config-backed glossary, including the VCP catalog entry (plain-language
meaning + the config thresholds + a worked example) and inline setup/pattern tooltips. It adds a nav
route (→ blueprint reapproval). The VCP reason/thresholds are already config-backed, so the glossary can
render the VCP entry with no detector code change. A clean J-12 takes the project to 16/16 Must-haves
and a legitimate GOAL_ACHIEVED check.
