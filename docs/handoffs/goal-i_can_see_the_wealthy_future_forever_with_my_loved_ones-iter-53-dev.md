# goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-53 Dev Handoff

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-53
**Date:** 2026-06-27
**Agent:** developer
**Status:** complete

## What Was Built

J-110 — a new **Research → Regime Lab** at `/research/regime-lab`. Descriptive, survivorship-biased
cross-sectional evidence of how stocks' realized forward returns + paired max-drawdowns relate to the
market regime, grouped (a) by the six canonical regime **labels** and (b) into **deciles of the 0–100
regime score**, at every configured horizon at once (paired columns), with the rank-IC of the regime score
vs the forward return per horizon and count-coherent `N=` drill-downs. The structural twin of iter-52's
Factor Lab — it READS already-stored canonical values and **recomputes nothing**.

- **Backend — engine `compute_regime_lab`.** New `compute_regime_lab(session, *, view, as_of, config)` in
  `app/engine/research.py`. Pools the SAME cross-sectional per-observation forward returns the Factor Lab /
  event study build (stock × snapshot), each observation tagged with its run's STORED `regime_score` +
  `regime_label` (J-80, read VERBATIM from the immutable `ScannerRun`) joined to the append-only
  `forward_returns` (`realized_return` + the J-86 `max_drawdown`, read verbatim). Groups two ways at EVERY
  `config.walk_forward.horizons` horizon: by the six `config.regime.labels`, and by D1…D`deciles` of the
  regime score (the EXISTING generic `_deciles` / `_decile_member_slice` machinery). Per bucket: mean
  realized forward return, paired mean max-drawdown (the `_mean_or_none` NA convention), n, low_sample; the
  decile view additionally carries the score range and a per-horizon `rank_ic` of the regime score vs the
  forward return. Supports the J-63 Episodes/Pooled view (the SAME `_collapse_to_episodes` overlap-honesty
  collapse the event study uses) and the J-32 as-of FILTER.
- **Backend — bounded observation builder.** `_regime_lab_members_by_horizon` builds the shared per-horizon
  pools in ONE streamed, column-projected read (FR scan column-projected to run_id/symbol/realized_return/
  max_drawdown `yield_per`-streamed; ScannerResult column-projected to run_id/id/ticker and streamed ordered
  `(run_id, id)` — rides `ix_scanner_results_run_id`, no temp-B-tree spill; per-run regime read via the new
  projected `_regime_meta_by_run`). NO unbounded `.all()` over `ForwardReturn`/`ScannerResult`. The
  single-horizon `_regime_lab_observation_set` (the samples builder) is byte-identical to the all-horizons
  build per horizon — the count-coherence keystone.
- **Backend — cache (no new table).** New `regime_lab_cached` reusing the EXISTING `event_study_cache`
  table under the `_REGIME_LAB_SUBJECT` sentinel + the actual `view`, with a folded `_REGIME_LAB_SCHEMA_TOKEN`
  (`"regimelab-v1"`) in the dataset-version slot — any old-schema row is a guaranteed MISS + prune
  (iter-38/39/44). NO new `table=True` model — `test_db.py`'s expected-tables guard stays UNCHANGED.
- **Backend — API.** New read-only `GET /api/research/regime-lab` (`view` Episodes/Pooled + `as_of`
  FILTER-only; no `horizon` selector — all-horizons shape), 503-no-data + 422-bad-view like its siblings.
- **Backend — samples cohort.** New `regime-lab` cohort `kind` (`KIND_REGIME_LAB`) in
  `app/engine/samples.py` (`_regime_lab_samples`, reproducing the exact `(regime label | regime-score
  decile, horizon, view)` cohort from the SAME shared observation builder), wired into `compute_samples` and
  the `/research/samples` validation vocabulary. Every displayable bucket resolves; an unknown label /
  out-of-range decile / unknown view is an honest 4xx.
- **Frontend.** New `/research/regime-lab` page (`RegimeLabPage` in `app/research/_labs.tsx` + the thin
  route file) rendering the by-label table (6 rows) and the regime-score decile table (D1…D10 + a Rank-IC
  header row): paired (forward-return, max-drawdown) columns per horizon, n, score range (decile), colour-
  graded (return tokens + `lib/mdd-color`). Columns client-side sortable NA-last both directions (J-48; sort
  headers resolved by `aria-label`). The As-of mode toggle FILTERS the observation set (single global as-of,
  J-18 — no second date control). Each return cell carries a count-coherent `N=` chip opening
  `/research/samples` in a new tab (J-65) carrying `?asof` (J-50). Survivorship-bias / descriptive-evidence
  labels + honest empty/NA states. New **Regime Lab** tile on the `/research` hub. `fetchRegimeLab` + types
  in `lib/api.ts`; `RegimeLabCohortParams` in `lib/samples-link.ts`. The page uses the POOLED working view
  (every stock × snapshot tagged by THAT snapshot's regime — the meaningful cross-sectional view; the
  whole-universe Episodes collapse degenerates to first-appearances), passing `view=pooled` to both the lab
  fetch and the `N=` chips so the counts stay coherent.

## Files Changed

- `apps/backend/app/engine/research.py` -- add `_regime_meta_by_run`, `_regime_lab_members_by_horizon`,
  `_regime_score_ordered`, `_regime_lab_observation_set`, `compute_regime_lab`, `regime_lab_cached` +
  `_REGIME_LAB_SUBJECT` / `_REGIME_LAB_SCHEMA_TOKEN` (reuse `_deciles`/`_rank_ic`/`_mean_or_none`/
  `_collapse_to_episodes`/`_run_position_index`/`_dataset_version`/`_cache_asof_key`).
- `apps/backend/app/api/research.py` -- new `GET /research/regime-lab` route; import `regime_lab_cached` +
  `KIND_REGIME_LAB`; add `KIND_REGIME_LAB` to the samples view-validation set; widen the `slice` param doc.
- `apps/backend/app/engine/samples.py` -- `KIND_REGIME_LAB` + `ALL_KINDS`; `_REGIME_LAB_SLICES`;
  `_regime_lab_samples`; wire into `compute_samples`; import `_regime_lab_observation_set` +
  `_regime_score_ordered`.
- `apps/backend/tests/test_regime_lab.py` (new) -- byte-identity vs a reference over the single-horizon
  builder (both views + both scopes), read-verbatim manual aggregation, NA-honesty, episodes<pooled +
  as-of-shrinks, cache HIT==MISS==fresh, schema-token MISS-then-prune against a real old-schema row, cache
  refresh, bounded-read source guard, chunk-independence, single-vs-batched byte-identity, samples
  count-coherence for every bucket, invalid-selector 4xx.
- `apps/backend/tests/test_api_research.py` -- new endpoint shape + view validity + as-of scoping +
  pooled≠episodes + HTTP samples count-coherence + invalid-selector 4xx.
- `apps/backend/tests/test_samples.py` -- `regime-lab` label + decile cohort count-coherence over the
  `multi_regime_engine` fixture.
- `apps/frontend/app/research/_labs.tsx` -- `RegimeLabPage` + `RegimeLabByLabelTable` /
  `RegimeLabDecileTable` + `RegimeSortHeader` / `RegimeReturnCell` / `RegimeMddCell` + sort helpers; new
  imports (`fetchRegimeLab`, regime-lab types, `CohortParams`).
- `apps/frontend/app/research/regime-lab/page.tsx` (new) -- the lazy sub-route page.
- `apps/frontend/app/research/page.tsx` -- new **Regime Lab** tile in `LABS` (Gauge icon).
- `apps/frontend/lib/api.ts` -- `fetchRegimeLab` + `RegimeLab*` response/row types.
- `apps/frontend/lib/samples-link.ts` -- `RegimeLabCohortParams` + its `buildSamplesHref` serialization.

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -v` (run per-file during dev)

Result (changed/affected files, all green):
- `test_regime_lab.py` — 28 passed
- `test_samples.py` — 16 passed (incl. the new `regime-lab` coherence test)
- `test_api_research.py -k regime_lab` — 7 passed (over the real seed)
- `test_no_magic_numbers.py` + `test_db.py` — 11 passed (guards UNCHANGED + green)
- Frontend: `node_modules/.bin/tsc --noEmit` — EXIT 0 (typecheck clean)

Full suite (launched **nohup-async**, flushed) ->
`reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-53-fullsuite.log`:
**1 failed, 1123 passed, 4 skipped in 2076s**. The single failure is
`tests/test_api_data.py::test_post_job_returns_job_id_and_reaches_final_summary` — the data-manager **async
backfill-job** pipeline (`_await_job` polls for a background worker thread to reach a final summary), an area
my purely-additive regime-lab changes do NOT touch. It is a load/timing flake under the 34-minute heavy
concurrent run: **re-run in isolation it PASSES** (`1 passed in 0.31s`). Every regime-lab + research + samples
+ no-magic-numbers + db-guard test is green. (Per the spec this iter is NOT a GOAL_ACHIEVED candidate, so the
flushed `0 failed` is owed by a future candidacy, not this iter; the one flake should be re-confirmed green on
a quiescent run then.)

## Live integration (real backend + DB — 1,357 runs / 125,019 scanner_results / 701,218 forward_returns, max run 2026-06-25)

Run AFTER the full suite finished (to honor the iter-47 OOM-under-RAM-pressure lesson). Backend started via
`scripts/start-backend.sh` (port 8255), frontend via `scripts/start-frontend.sh` (port 3255); both started
cleanly and were stopped afterward (ports 8255/3255 free).

- **Cold uncached `GET /api/research/regime-lab?view=pooled`** over the LIVE DB: `http=200`, **6.7s, 13KB —
  NO MemoryError** (the bounded streamed/column-projected read; faster than the Factor Lab's 47s because the
  regime is per-RUN so the ScannerResult side is column-projected, not a full-ORM stream). Real data: 6
  by-label rows (e.g. Risk-off @20d return +2.64% / MDD −15.6% / n 19,246; Risk-on +1.47% / −12.5% /
  n 46,532), 10 by-decile rows with score ranges (D1 score [3.75, 20.92] return +4.0%; D10 [83.0, 90.13]
  +2.36%), and a per-horizon rank-IC (e.g. 20d −0.017 over n 122,964).
- **Cache HIT** (2nd identical fetch): `http=200` in **0.012s** (served from the EventStudyCache row).
- **As-of FILTER** (`&as_of=2024-06-03`): `http=200`, echoes `asof_date=2024-06-03`, and the @20d observation
  total SHRINKS 122,964 → 67,837 (strictly smaller, still positive) — a pure point-in-time filter, no second
  date control.
- **Samples count-coherence over HTTP** (pooled, @20d): `slice=label&regime=Risk-on` total 46,532 == the
  published chip n 46,532; `slice=decile&decile=10` total 12,297 == the published D10 chip n 12,297. No 4xx.
- **Frontend:** `/research/regime-lab` serves `http=200` (heading + caveat in the SSR shell; the two tables
  render client-side after the fetch — verified live by the browser-qa-agent step); the `/research` hub lists
  the new **Regime Lab** tile (`research-lab-link-regime-lab`).

## Known Issues

- **Episodes view is a degenerate cross-section by design.** The Regime Lab pools the WHOLE universe (every
  stock × snapshot), so the J-63 first-trigger Episodes collapse reduces each name to its first appearance —
  meaningful for a subject-scoped event study, not for a whole-cross-section regime study. The API still
  serves both views (count-coherent in both, unit-proven), but the FRONTEND uses the POOLED working view
  (every observation tagged by that snapshot's regime), which is the meaningful cross-sectional study. No
  Episodes/Pooled toggle is exposed on the page (the spec's only page controls are the As-of toggle, column
  sort, and `N=` chips).
- The frontend node unit-test runner errors `ERR_UNKNOWN_FILE_EXTENSION` on this box's Node (TS type-
  stripping off by default) — an environment quirk; TS correctness is gated by `tsc --noEmit` (EXIT 0). No
  new frontend component unit test was added (no pre-existing harness; the paired columns / sort / `N=`
  chips are covered by backend byte-identity + count-coherence tests, live HTTP checks, and in-iteration
  browser-QA).
- `next lint` is not configured in this project (prompts interactively) — not a gate; not run.
- The by-label and by-decile tables are intentionally WIDE (5 forward-return + 5 max-drawdown columns). Each
  Card uses `overflow-x-auto` (horizontal scroll) rather than dropping columns (the iter-52 precedent).
