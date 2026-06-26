# goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-50 Dev Handoff

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-50
**Date:** 2026-06-26
**Agent:** developer
**Status:** complete

## What Was Built

J-107 — the Factor Lab `/research/factor-lab` is restructured from a single-factor dropdown into an
**all-factors comparison table**: one row per config-catalog factor (family + Spearman rank-IC value+N +
downside risk-adjusted at the selected horizon), client-side sortable NA-last, each row click-to-expand to
its full D1..D10 decile sort. Every value is **byte-identical** to the per-factor lab and served from a
**derived-once cached, bounded read path**.

- **Backend — additive `all=true` flag on the EXISTING `GET /api/research/factor-lab`** (NO new endpoint).
  When set, returns a `factors_table` block (one entry per catalog factor: `{key, label, family, direction,
  n_total, rank_ic:{value,n}, risk_adjusted, deciles:[…]}`) plus the resolved `horizon` / `horizons` /
  `default_horizon` / `deciles_count` / `min_sample` / `asof_date` / survivorship + descriptive caveats.
- **One shared observation pool, one computation path (byte-identity).** `_all_factor_observations` fires
  ONE heavy read carrying every factor's value per observation (NULLs kept), then per factor filters to its
  own non-null subset (preserving the shared pool's `(run_id, id)` order, which equals
  `_factor_observations`' order) and derives deciles/rank-IC from the SAME `_deciles` / `_rank_ic` builders.
  No second rank-IC / decile / risk-adjusted derivation, no new served value. The `risk_adjusted` column is
  the factor's OWN top-decile `risk_adjusted` (read off `deciles[-1]`, downside-only — never total vol).
- **Derived-once cache.** `factor_lab_all_cached` reuses the existing `EventStudyCache` under a fixed
  sentinel namespace (`subject="__all_factors__"`, `view="factors_table"`), keyed on `_dataset_version` +
  `asof_key` + `horizon` (HIT/MISS/prune pattern mirroring `factor_combination_cached`). **No new
  `table=True` model** — the `test_db.py` expected-tables guard is unchanged.
- **Bounded read (J-105 / iter-48 lesson).** The FR scan is column-projected + `yield_per`-streamed; the
  ScannerResult side is `yield_per`-streamed in `(run_id, id)` order (rides `ix_scanner_results_run_id`, no
  temp-B-tree disk spill). No unbounded `.all()` in the all-factors builder. Verified COLD on the live
  772 MB DB: ~26 s cold compute, then instant cache HIT.
- **`compute_factor_lab` (single-factor) untouched** — its per-factor output incl. `_regime_effectiveness`
  / `by_regime` still computes byte-identically. Only the FRONTEND retires the per-regime table from this
  view.
- **Frontend — `FactorLabPage`** now fetches `?all=true` and renders the sortable, expandable all-factors
  table; the factor dropdown (`FactorSelector`), the single-factor body (`FactorLab` / `RankICCard`), and
  the per-regime table (`RegimeEffectivenessTable`) are removed from this view. The HorizonSelector + the
  As-of mode toggle REMAIN (single global as-of — no second date state). Each decile `N=` chip keeps its
  existing `SampleLink` drill-down (`cohort={{kind:"factor", factor, horizon, slice:"decile", decile}}`).

## Files Changed

- `apps/backend/app/engine/research.py` -- added `_all_factor_observations` (shared bounded pool),
  `compute_factor_lab_all` (all-factors aggregate, byte-identical per factor), `factor_lab_all_cached`
  (`EventStudyCache` sentinel namespace), and the `_ALL_FACTORS_SUBJECT` / `_ALL_FACTORS_VIEW` constants.
- `apps/backend/app/api/research.py` -- added the additive `all: bool` query param to
  `GET /research/factor-lab`; when true serves `factor_lab_all_cached` (same horizon/as_of validation).
- `apps/backend/tests/test_factor_lab_all.py` -- NEW: byte-identity (per factor == `compute_factor_lab`,
  all-history + as-of + zero-N), cache HIT==MISS==fresh + stale-version prune (real populated row) +
  refresh-after-dataset-change, bounded-read (source guard + chunk-independence + one-shared-read), NA honesty.
- `apps/backend/tests/test_api_research.py` -- added all-factors API tests (one-row-per-factor shape;
  byte-identity vs the single-factor endpoint; as-of scoping echoes cutoff; bad-horizon 422).
- `apps/frontend/lib/api.ts` -- added `FactorTableRow` + `FactorLabAllResponse` types + `fetchFactorLabAll`.
- `apps/frontend/app/research/_labs.tsx` -- replaced the dropdown view with `FactorsTable` / `FactorRows` /
  `FactorSortHeader` / `RatioCell`; removed `FactorSelector` / `groupByFamily` / `FactorLab` / `RankICCard` /
  `RegimeCell` / `RegimeEffectivenessTable`; kept `DecileTable` (reused in the expand panel).

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -q`
Result (targeted research + guard suites, run together):
`tests/test_factor_lab_all.py tests/test_api_research.py tests/test_research.py tests/test_research_streaming.py tests/test_no_magic_numbers.py tests/test_db.py tests/test_iter20_research_cluster.py` → **231 passed** (0 failed).
- `test_factor_lab_all.py` alone → 12 passed.
- `test_db.py::test_create_all_produces_expected_tables` UNCHANGED (no new table) — green.
- `test_no_magic_numbers` green (catalog / horizons / decile count / batch all config-sourced).

Frontend: `cd apps/frontend && npx tsc --noEmit` → exit 0 (clean). (Project has no ESLint config; tsc is the
gate.) The running `next dev` hot-reloaded the change — the page serves HTTP 200 with the new subtitle and
no error overlay.

> NOTE: the FULL `pytest tests/` suite was NOT run end-to-end by the developer (the iteration's GREEN-suite
> gate is run nohup-async via the pump per the spec). The targeted research + guard subset is green; the
> heavy-lab browser probes must not run concurrently with the full suite.

## Live verification (real 772 MB DB, backend on :8255)

- Cold all-factors compute: **~26 s** over the live pool (n=122,964); cache HIT thereafter **~0.02 s**. No
  OOM, no `disk is full` — the bounded `(run_id, id)`-ordered streamed read held.
- **Byte-identity confirmed live** for a column factor (`leadership_score`), a component factor
  (`rs_spy_3m`), and a different-n factor (`high_proximity`, n=117,614): `deciles`, `rank_ic`,
  `risk_adjusted`, `n_total` all equal the single-factor `?factor=` endpoint.
- As-of: `?all=true&as_of=2021-01-04` echoes the cutoff and scopes n (honest 0 at the earliest snapshot).
- Errors: bad horizon → 422; future as-of → 400.

## Known Issues

- **As-of demo value at the very oldest date is 0** — at `2021-01-04` (the earliest snapshot) the scoped
  pool has no realized 20d forward returns yet (honest NA), so the browser J-32 leg should toggle As-of to a
  **mid-history** date to show a smaller-but-nonzero n change (a QA test-data choice, not a code issue).
- **The `risk_adjusted` column = the factor's TOP-decile (D10, highest factor value) downside
  risk-adjusted**, re-presented from `deciles[-1]` (an existing canonical value — no new derivation). For a
  `lower_better` factor the strongest cohort is the bottom decile; the column is still consistently the
  top-decile value (direction is conveyed by the rank-IC sign + the row's `(direction)` hint). This is a
  product/presentation choice, documented in code.
- **`fetchFactorLab` (single-factor) remains exported** in `lib/api.ts` (still used by nothing on this page;
  the all-factors view uses the new `fetchFactorLabAll`). Left in place — harmless, and the single-factor
  endpoint is still the canonical source the Research Samples drill-downs (`kind:factor`) read from.
- The `next dev` started for verification could not bind (a frontend was already running on :3255, which
  hot-reloaded the change and served 200); the developer-started **uvicorn on :8255 was killed** before
  finishing. No developer-started server processes remain.
