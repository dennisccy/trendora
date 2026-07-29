# goal-ops-hardening-iter-30 Dev Handoff

**Phase:** goal-ops-hardening-iter-30
**Date:** 2026-07-29
**Agent:** developer
**Status:** complete

## What Was Built

- **Bounded `compute_forward_aggregates`'s join-accumulator (J-07's newest AG-8 finding).** The two
  containers every streamed `forward_returns` row landed in (`ret_by_run_symbol`/`mdd_by_run_symbol`) used
  to hold every distinct `(run_id, symbol)` pair across the WHOLE horizon-partition at once — 770K-803K
  measured live per horizon, iter-29's audit — the exact join-accumulator shape iter-29 fixed one function
  over in `research.py`, now confirmed live in THIS function via the ops-hardening iter-29 evaluator's
  browser-QA `MemoryError` finding at `forward_testing.py:965`. The fix:
  - `_forward_agg_runs_with_fr(session, horizon, as_of)` — a lightweight `SELECT DISTINCT run_id` discovery
    query (bounded by run count, never by pair count) replacing the old "materialize every pair, then take
    the set of keys" pattern.
  - `_forward_agg_slice_map(session, horizon, slice_run_ids, batch)` — the bounded per-chunk join map,
    mirroring `research._fr_slice_map` exactly (merged into ONE dict of `(return, mdd)` tuples rather than
    two parallel dicts).
  - `compute_forward_aggregates` now walks `runs_with_fr` in ascending slices of `walk_forward.
    forward_agg_run_chunk` run ids. Each slice builds its own `_forward_agg_slice_map`, uses it to build
    ONLY that slice's contribution to `stock_obs`, extracts the tiny benchmark-symbol subset (`bm_returns`
    — SPY/QQQ/sector-ETF returns only, the ONLY symbols `_control_groups`/the excess calc ever look up in
    it), then discards the slice map before the next chunk. The two named dicts never again hold the full
    horizon-partition at once.
  - `_group_means`, `_group_mdd`, `_control_groups`, `_attribution_slices`, and the VCP/pullback/breakout
    groupings are all UNCHANGED (same signatures, same bodies) — this fix is confined entirely to how
    `compute_forward_aggregates` assembles the containers those functions consume.
- **New dedicated config knob** `walk_forward.forward_agg_run_chunk` (default `100`, boot-validated `>= 1`)
  on `WalkForwardCfg` — its own RUN-count key, never reusing `research.read_batch_size` (a ROWS knob) or
  `research.factor_join_run_chunk` (a different function's own run-chunk knob) — iter-29's binding
  unit/ownership lesson, enforced by a dedicated shipped-config unit test (see Tests Run).
- **Byte-identity + shipped-chunk + error-case tests** covering the chunking mechanism (see Tests Run).
- **J-06 mechanical closure**: a fresh 11-page curl-based sweep + the boot-to-health measurement, appended
  to `reports/perf-budgets.md` with explicit PASS/WARN scoring (no code change).

## Files Changed

- `apps/backend/app/engine/forward_testing.py` — added `_forward_agg_runs_with_fr` and
  `_forward_agg_slice_map`; rewrote `compute_forward_aggregates`'s accumulation section to walk
  `runs_with_fr` in bounded run-id slices; updated the `_control_groups` call site to pass the bounded
  `bm_returns` map instead of the old full `ret_by_run_symbol`; extended the function's docstring.
- `apps/backend/app/config.py` — `WalkForwardCfg.forward_agg_run_chunk: int = 100` + boot validator
  (`>= 1`); docstring extended.
- `config.yaml` — `walk_forward.forward_agg_run_chunk: 100` with the live measurement recorded in a
  comment (1,813-1,872 distinct runs/horizon, ~417 symbols/run, measured 2026-07-29).
- `apps/backend/tests/test_forward_testing_aggregates_streaming.py` — appended the iter-30 section: a
  chunk-bounded-accumulator test (TC-1), a byte-identity test across 4 run-chunk widths × 5 horizons × 2
  `as_of` values against the file's EXISTING pinned pre-rewrite reference (TC-2, reused rather than
  re-pinned — see Known Issues for why a new sibling file was not created), a no-lookahead-preserved test,
  two error-case tests (a run never splits across a chunk boundary; an all-excluded chunk does not crash
  the merge), a static shipped-width ceiling test, a synthetic shipped-config-actually-chunks test, and a
  read-only test against the LIVE committed seed DB's actual distinct-run count (TC-3, skips if the DB is
  absent).
- `reports/perf-budgets.md` — a fresh `scripts/measure-perf.sh --boot --skip-backfill` sweep (auto-appended
  two sections) plus a hand-authored "Iteration 30" section with explicit PASS/WARN scoring of all 11 J-06
  pages + their on-load endpoints + the boot-to-health reading.
- `docs/handoffs/goal-ops-hardening-iter-30-dev.md` — this handoff.

## Tests Run

Commands (host-guard taskset/BLAS-capped per `project-extensions/host-guard/host-guard.env`, launched via
`setsid nohup` + polled to completion in bounded foreground loops — never run concurrently with another
pytest process):

```
cd apps/backend && taskset -c 0-3,8-11 env OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 MKL_NUM_THREADS=4 \
  NUMEXPR_NUM_THREADS=4 .venv/bin/python -m pytest \
  tests/test_forward_testing_aggregates_streaming.py tests/test_forward_testing_streaming.py -v
```
**Result: 51 passed in 7.59s.** Includes the new TC-1 (chunk-bounded accumulator), TC-2 (byte-identity vs
the pinned pre-chunk reference at run-chunk widths 1/2/4/100, all 5 configured horizons, with/without
`as_of`), TC-3 (both the synthetic shipped-config-chunks test AND the read-only test against the LIVE
committed seed DB's actual run count — confirmed >1 chunk on the real 1,872-run/horizon basis), the two
error-case tests, and the static shipped-width ceiling test. The pre-existing iter-14
`test_compute_forward_aggregates_byte_identical_to_pre_rewrite_reference` (30 cases: 3 batch sizes × 5
horizons × 2 `as_of` values) also passed unchanged, confirming the run-chunking rewrite is byte-identical
to iter-14's row-streamed implementation at the default chunk width too.

```
cd apps/backend && taskset -c 0-3,8-11 env OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 MKL_NUM_THREADS=4 \
  NUMEXPR_NUM_THREADS=4 .venv/bin/python -m pytest \
  tests/test_forward_testing.py -k "not walk_forward_asof_dates and not backfill and not stored_scores_identical" \
  tests/test_config.py -v
```
**Result: 142 passed, 12 deselected in 7.54s.** Deselected tests are the ones depending on the heavy
session-scoped `loaded_engine` fixture (full 30-year seed bootstrap+backfill) or the module-scoped
`backfilled_engine` fixture — neither touches `compute_forward_aggregates`'s accumulator shape, and this
project's own prior iterations (e.g. iter-29's dev handoff) established the same exclusion for the same
reason. Every cheap-fixture test in `test_forward_testing.py` that DOES exercise `compute_forward_
aggregates` (by-bucket/setup/regime, excess, control-group, VCP/pullback/flat-base cohorts, all 8
attribution tests, all 6 `as_of` scoping tests, the 3 `forward_aggregates_ingest_cached` tests) passed.
`test_config.py`'s full suite (including the new `forward_agg_run_chunk` boot-validator coverage via the
real config) passed.

```
cd apps/backend && taskset -c 0-3,8-11 env OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 MKL_NUM_THREADS=4 \
  NUMEXPR_NUM_THREADS=4 .venv/bin/python -m pytest \
  tests/test_forward_testing_concurrency.py tests/test_forward_testing_serving_split.py -q
```
**Result: 41 passed in 27.29s.** Zero failures — the concurrency single-flight guard and J-08's serving
split (both explicitly named in the plan as "stay green unmodified") are unaffected.

**RED check performed before implementing:** the new byte-identity/chunk-bounded tests were written against
the (at-that-point) unmodified `compute_forward_aggregates`; `_forward_agg_slice_map`/`_forward_agg_runs_
with_fr` did not exist yet, so the chunk-bounded test failed with `AttributeError` as expected, confirming
the test exercises the new code path rather than passing vacuously.

## Known Issues

- **The plan suggested a new sibling test file named `test_forward_testing_streaming.py`; that name is
  already taken** by an unrelated iter-47 test file (`_streamed_existing_keys`'s idempotency-key streaming
  proof). Rather than overwrite it or invent a confusing third near-duplicate reference implementation, I
  appended the iter-30 tests to the ALREADY-EXISTING `test_forward_testing_aggregates_streaming.py`, which
  turned out to be the better home regardless: it already carries a rich multi-run/multi-sector fixture
  (`multi_run_engine`) and a pinned pre-rewrite reference implementation
  (`_reference_compute_forward_aggregates`) for this EXACT function from iter-14's own row-streaming fix.
  Since that reference never chunks by run either, it doubles as the byte-identity oracle for the
  run-chunking dimension too — reused, not re-pinned a second time. No new reference implementation was
  written for the byte-identity proof itself.
- **`stock_obs` (the third named container, a list of ~10-key dicts, one per observation) is NOT literally
  bounded to chunk-width — it is still assembled to full size by the end of the loop.** This is a
  deliberate scope decision, not an oversight: `_attribution_slices`'s signature is a FROZEN, test-pinned
  `(stock_obs, cfg)` read-only contract (`test_attribution_is_pure_over_passed_observations_no_new_query`
  asserts `inspect.signature(_attribution_slices).parameters == {"stock_obs", "cfg"}`), and several OTHER
  tests in `test_forward_testing.py` call `_attribution_slices` directly with hand-built observation lists
  (`test_attribution_empty_observations_are_all_na`, `test_attribution_single_observation_dispersion_is_
  null`, etc.). Changing that signature to accept pre-built per-group accumulators instead of a raw
  observation list — the only way to make `stock_obs` genuinely bounded — would have meant rewriting that
  frozen contract and every test asserting against it, a materially larger and riskier footprint than "one
  iteration, one risky change" (per goal.md's own rule 5). The plan's own "Known hard constraint" note
  anticipated exactly this tension and offered latitude ("A byte-identity-safe design either (a)... or
  (b)..."); I chose the LOWER-RISK scope that still delivers a real, measured reduction: the two dominant
  ~770K-803K-entry join-accumulator dicts are now genuinely bounded (chunk-scoped, discarded before the
  next chunk — proven directly by the TC-1 monkeypatch test), removing them from ever co-existing with
  `stock_obs` at full size. Whether this alone fully eliminates the live `MemoryError` under the real
  forward-aggregate warm (all 5 horizons, full deep basis, one long-lived process) is unverified by me —
  that live measurement is explicitly assigned to browser-qa-agent (TC-1/TC-4 in the plan), and I did not
  trigger a full-basis forward-aggregate warm during this dev pass (host-guard/time constraints; the plan's
  own NOTES also say not to artificially induce or re-trigger this). If QA's live measurement shows the
  bound does not fully eliminate the failure, the honest next step is a follow-up iteration that revisits
  `_attribution_slices`'s frozen contract deliberately — not a silent claim of success here.
- **Live verification performed instead:** I did restart the backend twice via `scripts/start-backend.sh`
  (once via `scripts/measure-perf.sh --boot`, once standalone for the pre-handoff port-conflict check) and
  confirmed `logs/backend.log` carries ZERO new `MemoryError` lines after either boot (the existing
  `MemoryError` lines in that log are all timestamped before my session's first boot at
  `2026-07-29T01:30:19Z` — the pre-existing iter-29 finding, not something reproduced by my changes). This
  is NOT a substitute for TC-1's full-basis forward-aggregate warm (my boots only ran the existing boot
  warm-up path, which does not itself call `compute_forward_aggregates`) — it only confirms the backend
  boots and serves cleanly with the new code in place.
- **`test_forward_agg_run_chunk_boundary_never_splits_a_run`'s docstring notes (and this handoff repeats)**
  a structural property worth flagging for the reviewer: because chunking is by RUN ID (never by symbol or
  row), one run's observations can never literally split across two chunks — the plan's literal error-case
  wording ("a chunk boundary that splits one run's observations across two chunks") describes a scenario
  this design makes structurally impossible, so the test instead proves the stronger guarantee (no run's
  contribution is ever double-counted or dropped at maximum fragmentation, `run_chunk=1`).

## Pre-handoff verification

- **Service startup**: `scripts/start-backend.sh` + `scripts/start-frontend.sh` started cleanly (backend
  :8255, frontend :3255, both HTTP 200 within ~4s). Stopped (verified both ports return connection-refused,
  killing the full process tree including the detached `next-server` child), then started again — both
  came up cleanly a second time with no port conflicts. Both stopped again before finishing this handoff —
  `ps aux` confirmed no `uvicorn`/`next dev`/`next-server` process remained on ports 8255/3255.
- **External integrations**: N/A this iteration (no new adapter/scraper/external API call; AG-9 offline-
  deterministic ingest unaffected).
- **Native dependency binaries**: N/A this iteration (no new dependency).

## Follow-ups for QA / next iteration

- TC-1/TC-4: trigger the real ingest-time forward-aggregate warm (all 5 configured horizons, full deep
  basis, one long-lived process) and confirm `logs/backend.log` carries zero `MemoryError` frames naming
  `compute_forward_aggregates`/`stock_obs`/`ret_by_run_symbol`, citing the exact boot-banner line number
  counted from (TC-9's process-quality requirement). If a `MemoryError` still occurs, it will most likely
  point at `stock_obs`'s full-size assembly (see Known Issues above) rather than the now-bounded join
  accumulator — worth checking the traceback's frame before assuming the whole fix failed.
- TC-5: `/research/factor-lab` regression spot-check in a real browser (unaffected by this iteration's
  diff — `research.py` was not touched — but the plan calls it out as sharing the accumulator-bounding
  pattern, so a fresh confirmation is still warranted).
- TC-7/TC-8: `J-06.json` deterministic replay + the required-still-passing set (J-01, J-03, J-04, J-05,
  J-08, J-09).
