# goal-i_can_see_the_wealthy_future_forever-iter-14 Dev Handoff

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-14
**Date:** 2026-06-02
**Agent:** developer
**Status:** complete

## What Was Built

J-29 — the **Setup & Pattern Lab (event study)** added to the existing approved `/research` home, plus
the stored MAE/MFE excursion path it depends on. All additive and forward-side only.

**A. Stored post-snapshot MAE/MFE excursion path (new immutable, lookahead-free value)**
- Added two append-only `Optional[float]` columns `mae` / `mfe` to `ForwardReturn` (`app/models.py`),
  default `None` (backward-compatible), documented in the docstring like the existing audit columns.
- Added the pure helper `forward_excursions(bars_after_list, entry_close, horizon)` in
  `app/engine/forward_testing.py`: `mae = min(low_i)/entry_close − 1`, `mfe = max(high_i)/entry_close − 1`
  over the FIRST `horizon` post-snapshot bars (date > D), reading each bar's `.low` / `.high`. It shares
  the EXACT no-lookahead NA gate as `forward_return` (None when entry missing/zero OR `< horizon`
  post-bars) and is unchanged when bars after the h-th are removed.
- Extended the single INSERT path `_insert_run_forward_returns` to populate `mae` / `mfe` on each
  `ForwardReturn` it INSERTs, reusing the `post_bars` / `entry_close` / `horizon` already in hand (no
  extra query). INSERT-only + idempotent — no `scanner_runs` / `scanner_results` / `*_scores` row is ever
  UPDATEd. This is the ONE place excursions are computed, shared by the boot backfill AND the per-date
  `backfill_run_forward_returns`.
- **DB regen performed**: deleted `apps/backend/data/trendora.db` and regenerated from the committed seed
  so existing forward-return rows carry `mae` / `mfe` (verified: all 6739 rows populated, 0 band
  violations). Snapshots regenerate byte-identical (6739 rows, same as before — scoring path untouched).

**B. Read-only event-study analytic**
- Added `app/engine/research.py :: compute_event_study(session, subject_key, horizon, config=None)` — a
  READ-ONLY aggregation derived ENTIRELY from stored `forward_returns` (`realized_return` + `mae` + `mfe`,
  read verbatim) JOINED to stored `scanner_results` (setup status + the pattern mirror flags) and
  `scanner_runs.regime_label` (verbatim). It issues only SELECTs + pure stats; it calls no scoring /
  regime / return / excursion / pattern math (patch-to-raise keystone test proves it).
- A **subject** is a setup OR a pattern. `subject_catalog(cfg)` derives the vocabulary from the existing
  config-backed sources — `setups.ALL_STATUSES` (6 setups) + `config.patterns` keys (3 patterns) — with
  labels reused from the config-backed methodology copy. No new required config key was introduced.
- Per subject × horizon it reports: the distribution (mean / median / %positive / dispersion, reusing
  `_distribution`), the expectancy decomposition (`win_rate` / `avg_win` / `avg_loss` / `expectancy`,
  which equals the mean), mean stored MAE / MFE, and BOTH downside-only risk-adjusted ratios
  (`return_per_downside_dev` reusing `_risk_adjusted`; `return_per_mae` = mean/mean(|MAE|)). Plus the
  best-exit-horizon (argmax of the primary metric among non-low-sample horizons), the by-regime slice
  (every config regime label emitted; Σ per-regime n == pooled n), and the by-sector slice (present-only,
  config order). Carries the survivorship + descriptive caveats verbatim. Raises `ValueError` on an
  unknown subject.

**C. Serving endpoint**
- Added `GET /api/research/event-study` (`app/api/research.py`), params `subject` (default = first catalog
  subject) and `horizon` (default = `walk_forward.default_horizon`). 422 on unknown subject / horizon,
  503 when no price data — mirrors the existing `factor-lab` / `factor-combination` handlers. NO
  `as_of`/date param (J-18).

**Frontend** — see `…-iter-14-frontend.md`.

## Files Changed
- `apps/backend/app/models.py` — `ForwardReturn` gains `mae` / `mfe` append-only `Optional[float]` columns (+ docstring).
- `apps/backend/app/engine/forward_testing.py` — new `forward_excursions(...)` helper; `_insert_run_forward_returns` now populates `mae` / `mfe`.
- `apps/backend/app/engine/research.py` — `compute_event_study` + `subject_catalog` + read-only helpers (`_event_study_members`, `_expectancy`, `_return_per_mae`, `_event_study_horizon_row`, `_best_exit_horizon`, `_event_study_by_regime`, `_event_study_by_sector`); imports `_distribution`/`_mean_or_none` + `ALL_STATUSES`.
- `apps/backend/app/api/research.py` — `GET /research/event-study` handler (+ module docstring update).
- `apps/frontend/lib/api.ts` — `fetchEventStudy(...)` + `EventStudyResponse` / row types.
- `apps/frontend/app/research/page.tsx` — `EventStudyLab` section (subject selector grouped by kind, per-horizon table, by-regime + by-sector panels, caveat) rendered below `CombinationLab`; updated the now-outdated CombinationLab footnote.
- `apps/backend/tests/test_forward_testing.py` — `forward_excursions` pure tests (no-lookahead, NA gate, band) + backfill mae/mfe-in-band test; `_Bar` carries high/low.
- `apps/backend/tests/test_research.py` — 13 event-study tests (read-only keystone incl. `forward_excursions`, consistency invariant, exact distribution/expectancy/MAE/MFE/risk-adjusted, downside-only NA, by-regime Σn, by-sector present-only, best-exit, unknown subject, config-driven catalog, payload shape); `_add_result`/`_add_fr` gain pattern-flag/excursion kwargs.
- `apps/backend/tests/test_api_research.py` — 7 event-study endpoint tests (default payload, no-date-control, subject/horizon re-point, 422×2, 503).
- `apps/backend/tests/test_no_magic_numbers.py` — comment annotations documenting iter-14 coverage (no new sentinel needed; additions reuse min_sample/horizons + ALL_STATUSES/config.patterns vocabulary).
- `apps/backend/data/trendora.db` — regenerated from seed (gitignored runtime artifact).

## Tests Run
Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -v`

Targeted runs (all green):
- `test_forward_testing.py`: 37 passed (4 new excursion tests + mae/mfe band test).
- `test_research.py`: 57 passed (13 new event-study tests).
- `test_api_research.py`: 25 passed (7 new event-study endpoint tests).
- `test_no_magic_numbers.py` + `test_config.py`: 25 passed.
- Frontend `npm run build`: typechecks + compiles (`/research` route built).

Full suite (run ONCE after the DB regen + fixture updates):
`cd apps/backend && .venv/bin/python -m pytest tests/ -q` → **453 passed, 4 skipped in 19m04s (exit 0)**.
The 4 skips are the offline-skipped `integration`-marked live-network tests (the Data Manager live fetch),
unchanged by this iteration — every iter-14 test runs and passes.

Live verification (fresh backend on :8835 against the regenerated DB, then stopped):
- `GET /api/research/event-study?subject=pullback_to_rising_dma` → n_total=163, best_exit=60, full
  distribution + expectancy (expectancy == mean) + MAE −8.7% / MFE +7.7% + both downside ratios; by-regime
  sums to 163 with honest NA empty regimes; 9 sectors present.
- Consistency invariant holds live: event-study mean == `compute_forward_aggregates` `by_setup` /
  `by_vcp[VCP]` for the same observations.
- **J-07 re-verified after regen**: both seeded Risk-off runs carry 0 Actionable.

## Cohort sizes (for QA subject selection)
At every horizon (n is ~horizon-independent in this seed). Subjects ≥ min_sample (30) render numbers;
below it the per-horizon rows are honest NA + n.
- Setups: **Avoid 827, Risk-off-watchlist 242, Breakout-watch 99, Extended 45** (numbers) · Actionable 2, Pullback-watch 3 (honest NA).
- Patterns: **pullback_to_rising_dma 163, flat_base_breakout 48** (numbers) · vcp 27 (honest NA).
- **For a numbers demonstration pick e.g. Breakout-watch (setup) + pullback_to_rising_dma (pattern).**
  For the honest-NA demonstration, vcp / Actionable show NA + n. The DEFAULT subject is Actionable
  (first catalog subject, per spec) → the default landing shows honest NA + n=2 (rare setup); pick a
  data-rich subject to see numbers. by-regime always shows ≥1 honest NA empty-regime row.

## Known Issues
- The default subject (Actionable, the first catalog subject per the spec contract) has only 2 historical
  occurrences in this seed, so the default event-study view renders honest NA + n=2 rather than numbers.
  This is correct/honest behavior (low-sample → NA, the established Factor-Lab pattern); a user/QA selects
  a data-rich subject (Breakout-watch, Avoid, pullback_to_rising_dma, …) to see populated figures.
- `best_exit_horizon` is NA for low-sample subjects (vcp, Actionable) because every horizon is below
  min_sample=30 — honest, not a bug (the iter-11 lesson: n is ~horizon-independent in this seed; design
  NA evidence around low-count subjects/empty regimes, which is what these are).
- `/api/health`'s `last_run_date` returns `null` — pre-existing behavior unrelated to iter-14 (unchanged
  from the prior backend); the scanner-run history is served correctly by `/api/runs`.

## Suggested Next Phase
J-31 (synthesis) is the only remaining buildable journey — the cross-page travel from lab evidence
(Factor Lab + this new event study) → leaderboard filter → Stock Detail across timeframes. It depends on
J-29 (now landed) and is the explicit iter-15 target. J-22/J-23/J-24 stay externally Yahoo-429 data-walled
(do not autonomously retry). After J-31, expect operator egress confirmation or a correct STALLED on the
data-walled remainder.
