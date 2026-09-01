# goal-market-compass-iter-33 Dev Handoff

**Phase:** goal-market-compass-iter-33
**Date:** 2026-09-01
**Agent:** developer
**Status:** complete

## Headline result

J-09's cold warm-up allocation is now bounded via a config-only budget. The standing-warm re-
measurement **MEETS the ≤ 2.5 GB target for the first time this session**: measured max
`VmPeak_kB` = **2,467,888 kB**, 153,552 kB (**5.86%) UNDER** the 2,621,440 kB target — an 18.78%
reduction from iter-32's own clean re-measurement (3,038,684 kB). The safety catch was NOT invoked:
the mechanism is proven byte-identical (both by a controlled unit test and by a live before/after
spot-check on the real committed-seed DB) and does not reproduce the iter-42-class whole-job
regression. Full evidence: `reports/perf-budgets.md` Addendum 44.

## What Was Built

- **`startup.warmup_bar_cache_bounded`** (`config.yaml`, new boot-validated boolean, default `true`)
  — governs which `app.engine.prices` bar-cache context `app.engine.warmup._run_warmup`'s cadence
  loop (the `run_scan` × N dates loop + trailing `backfill_forward_returns` call,
  `warmup.py:351`'s block) opens around itself.
  - `true` (the bound, and the default): `prices.prefilled_bar_cache(session)` — the SAME
    unconditional whole-table eager scan `_BarCache.prefill` already runs for every OTHER caller
    (`expected_symbols=None`, so nothing is excluded — deliberately NOT the iter-42
    `WHERE symbol IN (...)` filter reverted at iter-43). This builds the compact array-based
    `_SymbolColumns` representation (`array.array('d')` per numeric column, iter-41/B5) for every
    symbol the cadence loop touches, instead of letting the pre-iter-33 lazy `bar_cache(session)`
    context accumulate the costlier per-symbol `list[Bar]` NamedTuple representation.
  - `false`: reverts to the pre-iter-33 lazy `bar_cache(session)` shape (owner rollback lever). No
    other code path changes.
  - No new numeric literal was introduced into `warmup.py` (the key is a boolean selector, not a
    threshold), so `test_no_magic_numbers.py`'s `CALC_FILES` registration does not apply — confirmed
    by re-running that test's existing (unrelated, pre-existing red) subset unmodified.
- **Root cause, investigated live** (not assumed, per BACKGROUND's explicit prompt): a call-stack
  trace during this iteration's test development confirmed the pre-iter-33 bare
  `with bar_cache(session):` never called `.prefill()` — every symbol the cadence loop's `run_scan`
  touched was loaded through `bars_asof`'s lazy per-symbol branch (always `list[Bar]`). Because
  `run_scan` scores essentially the whole live universe on its FIRST cadence date already
  (breadth/regime/sector/theme all read the full pool), nearly every symbol's full series ended up
  resident in the costlier shape almost immediately — consistent with iter-32's own finding that the
  peak is a boot transient reached before/around readiness, not a slow per-date accumulation.
- **Two new targeted tests** (`apps/backend/tests/test_warmup.py`):
  - `test_warmup_bar_cache_bounded_config_selects_prefill_mechanism` — proves the config key
    genuinely selects the mechanism (`prefilled_bar_cache(session, expected_symbols=None)` exactly
    once when `true`; `bar_cache(session)` exactly once when `false`) — not merely documented intent.
  - `test_warmup_bar_cache_bounded_is_byte_identical_to_unbounded` — runs the same fast fixture
    warm-up twice (bounded / unbounded) on two fresh DBs and asserts every persisted
    `ScannerRun`/`ScannerResult`/`ForwardReturn` field is identical — the "no served value changes"
    safety-catch condition, proven at the unit level.
- **Repair item 1** — the deterministic replay lane was invoked WITH
  `--results reports/phase-goal-market-compass-iter-33-regression-replay-results.md`; the file
  exists, is non-empty, and lists an actually-executed PASS row for each of the 10
  Required-still-passing journeys (rc=0, 10/10 PASS, 0 skipped).
- **Repair item 2** — those real PASS rows were merged into
  `reports/phase-goal-market-compass-iter-33-ui-test-results.md` via
  `scripts/automation/lib/merge_ui_test_results.py`; the merged file's headline is PASS, 10/10, 0
  skipped — no journey the replay lane covered is left recorded SKIPPED.
- **Repair item 3** — a dated correction note was appended to `reports/perf-budgets.md` (append-only,
  Addendum 43's own text untouched) fixing its "no `as_of` outside this 3-value set was requested"
  sentence, which was scoped to the wrong backend instance (the same finding iter-32's own auditor
  already made in the dev handoff but never propagated to this file).
- **`reports/perf-budgets.md` Addendum 44** — the full re-measurement write-up: mechanism rationale
  (TC-1), method, honest host-quiet disclosure, the VmPeak/VmSize/VmRSS results table (at peak, at
  t+20s, end-of-window) against the target and every prior figure, the concurrent-load result (TC-4),
  the byte-identity result (TC-5), the manifest-immutability result (TC-6), and the replay-lane
  result (TC-7/TC-8).

## Files Changed

- `config.yaml` -- new `startup.warmup_bar_cache_bounded: true` key with a rationale comment.
- `apps/backend/app/config.py` -- `StartupCfg.warmup_bar_cache_bounded: bool = True`, documented in
  the class docstring alongside the other `startup.*` tunables.
- `apps/backend/app/engine/warmup.py` -- `_run_warmup`'s cadence context now selects between
  `prefilled_bar_cache(session)` and `bar_cache(session)` based on
  `cfg.startup.warmup_bar_cache_bounded`; import list extended to include `prefilled_bar_cache`.
  Docstring comment records the iter-33 rationale in place.
- `apps/backend/tests/test_warmup.py` -- two new targeted tests (see above), plus a short comment
  block explaining why both no-op `_warm_drawdown_expectations` (see Known Issues).
- `reports/perf-budgets.md` -- one new dated correction note (after Addendum 43, its own text
  untouched) plus one new dated addendum, Addendum 44 (append-only).
- `reports/phase-goal-market-compass-iter-33-regression-replay-results.md` -- new, written by the
  deterministic replay lane (`demo_runner.py --mode verify`).
- `reports/phase-goal-market-compass-iter-33-ui-test-results.md` -- new, merged from the replay
  results (no LLM/browser-qa lane input existed yet for this iteration — J-09 waives Walkthrough and
  is the only Target journey; the 10 Required-still-passing journeys are entirely covered by the
  deterministic replay lane, so a single-input merge is correct here).
- `reports/qa/goal-market-compass-iter-33-evidence/` -- new, the replay lane's per-journey
  screenshots (`J-01-verify.png` … `J-11-verify.png`, excluding J-09).
- `runs/goal-market-compass-iter-33/` -- new raw evidence: `j09-vmpeak-samples.csv` (177 rows,
  1-second interval, UTC timestamps, `VmPeak_kB`/`VmSize_kB`/`VmRSS_kB`/readiness every row),
  `vmpeak_sampler.py` / `pool_pressure_burst.py` (reused verbatim from iter-32, same measurement
  methodology), `byte_identity_capture.py` (new, this iteration's TC-5 tool),
  `concurrent64-burst-results.jsonl`, `byte-identity-before/` (8 files), `byte-identity-after/` (8
  files), `status.json`.

No product database migration -- no schema change.

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/test_warmup.py -k "warmup_bar_cache_bounded" -v`
Result: **both new tests pass** — `test_warmup_bar_cache_bounded_config_selects_prefill_mechanism`
passed on the first combined run (176.45s for that run, which also caught a field-name bug in the
second test's original draft — see below); after fixing the field names (`entry_quality_score` not
`entry_score`, `symbol`/`horizon`/`realized_return` not `ticker`/`horizon_days`/`forward_return_pct`
on `ForwardReturn`, `new_high_low_json`/`candidate_counts_json` not `new_highs`/`new_lows` on
`ScannerRun`), `test_warmup_bar_cache_bounded_is_byte_identical_to_unbounded` was re-run alone and
passed (144.59s). Each test spins up a fast-fixture warm-up (or two, for the byte-identity test), so
per-test wall time is dominated by that, not by the assertions themselves.

Command: `cd apps/backend && .venv/bin/python -m pytest tests/test_bar_cache.py -q`
Result: **21 passed, 1 failed** — the failure (`test_kdate_backfill_loads_each_symbol_at_most_once`)
is a PRE-EXISTING, unrelated race in `data_manager.py`'s PARALLEL K-date backfill, confirmed by
reproducing it on an unmodified baseline via `git stash` before touching anything. It is NOT one of
the named B1/B5/B6/iter-43 oracles this iteration must keep green — all five of those
(`test_lazy_load_is_published_atomically_to_a_concurrent_reader` [B1],
`test_prefill_old_vs_new_implementation_byte_identical` [B5],
`test_prefill_null_numeric_column_degrades_without_crashing` [B6],
`test_prefill_expected_symbols_no_longer_filters_the_eager_scan` [iter-43],
`test_prefill_empty_expected_symbols_still_loads_full_table` [iter-43]) PASS. See Known Issues.

Command: `cd apps/backend && .venv/bin/python -m pytest tests/test_no_magic_numbers.py -q`
Result: **1 passed, 1 failed** — the failure is the SAME pre-existing red failure the iter spec's own
OUT OF SCOPE list names verbatim ("`test_no_magic_numbers.py`'s pre-existing red failure on three
untouched files [`indicators.py`/`forward_testing.py`/`research.py`] remains out of scope [owner's
call]"). `warmup.py` (this iteration's only calc-adjacent file touched) is not in `CALC_FILES` and
was not added to it (no new numeric literal was introduced — see What Was Built).

Live evidence (not pytest -- real launched processes, `runs/goal-market-compass-iter-33/`):
- Standing-warm measurement: **PASS**, max `VmPeak_kB` 2,467,888 vs 2,621,440 target (−5.86%). Raw
  CSV, 177 rows, 1s interval, UTC window `2026-09-01T05:26:57.66Z` → `2026-09-01T05:29:57.30Z`.
- Concurrent-load check (`server.limit_concurrency`=64): **PASS**, 320 requests, 0 non-200, 0 client
  errors, 0 `QueuePool` lines in the corresponding `logs/backend.log` segment.
- Byte-identity spot check (7 as-of values × 2 endpoints = 16 captures, before vs after the code
  change, on the real committed-seed DB): **PASS**, `cmp -s` zero-diff on all 16 files.
- `next_session_manifests` census (before the "before" boot, after the "before" boot, after the
  "after" boot's full measurement window): **unchanged at 28 rows / 18 distinct `as_of` / max id 28**
  at every checkpoint — zero new mints, zero mutations.
- Deterministic replay lane: **PASS**, rc=0, 10/10 Required-still-passing journeys, 0 skipped.

## TC coverage (test-first contract)

- TC-1: `docs/handoffs/goal-ops-hardening-iter-43-dev.md` and `prices.py:245-259`'s iter-43 docstring
  paragraph were both read before any code change (see "What Was Built" / Addendum 44's Mechanism
  section) and both are cited in Addendum 44 with the measured +5.1% figure, plus the explicit
  argument for why this iteration's all-or-nothing (never partial/filtered) mechanism cannot
  reproduce that mixed-representation regression.
- TC-2/TC-3: the raw per-second CSV exists at `runs/goal-market-compass-iter-33/j09-vmpeak-samples.csv`;
  its max `VmPeak_kB` (2,467,888) is read directly from the file and compared to 2,621,440 kB in both
  this handoff and Addendum 44 — MET, stated plainly; `config.yaml`/`docs/goal.md`'s target value
  itself is unchanged.
- TC-4: the concurrent-load burst at `server.limit_concurrency` (64) completed with zero `QueuePool`
  TimeoutError lines, recorded in Addendum 44.
- TC-5: all 7 authorized as-of values × `GET /api/compass` (+ `GET /api/dashboard`) captured before
  and after the code change — byte-identical, cited above and in Addendum 44.
- TC-6: `next_session_manifests` row count / distinct `as_of` count / max id read before and after —
  all three unchanged.
- TC-7: the replay lane was invoked with `--results <path>`; the file exists, is non-empty, and lists
  an actually-executed PASS row for each of the ten Required-still-passing journeys.
- TC-8: the merged `ui-test-results.md` has no journey left SKIPPED that the replay lane covered.
- TC-9: a dated correction note stands after Addendum 43 (its own text untouched) stating the true
  combined-backend-instance as-of scope.
- TC-10: N/A — the bound was implemented without breaking correctness or reproducing a whole-job
  regression; the safety catch was never invoked. (Recorded here for completeness per the test-first
  contract's numbering, not because it fired.)

## Known Issues

**Pre-existing, unrelated test findings surfaced during this iteration's own investigation (not
introduced by this change, confirmed via `git stash` baseline reproduction before touching anything):**

1. **`test_warmup.py::test_warmup_loads_each_symbol_at_most_once_across_cadence_and_forward_returns`
   (an EXISTING iter-26 test) fails on an unmodified `main`, not just on this iteration's branch.**
   Root cause (found via a live call-stack trace, not guessed): `^VIX` is loaded 8 times (matching the
   8-date fast test fixture), not once, because `_warm_drawdown_expectations` (added ops-hardening
   iter-46, strictly AFTER `_run_warmup`'s cadence `with cache_ctx:` block this iteration targets has
   already exited) computes each of the 7 committed evidence-ledger claims on its OWN short-lived
   per-claim `Session` + bar-cache pair (`market_phase.phase_context_by_date` ->
   `_causal_timeline` -> `_severity_reading` -> `_latest_vix_on_or_before` -> `close_on`). This is
   unrelated machinery this iteration does not touch and was not asked to fix. The two new tests this
   iteration adds correctly no-op `_warm_drawdown_expectations` (mirroring the existing
   `_warm_membership_timeline` no-op) to avoid this pre-existing noise; the OLD iter-26 test was left
   unmodified (out of this iteration's scope — touching an unrelated test's assertions was judged
   riskier than leaving an honest, pre-existing, already-documented gap). **Recommended follow-up**
   (not done here): add the same `_warm_drawdown_expectations` no-op to that test, matching its own
   `_warm_membership_timeline` convention.
2. **`test_bar_cache.py::test_kdate_backfill_loads_each_symbol_at_most_once` failed once during this
   session** (`assert 2 == 1`) and reproduces identically on an unmodified baseline — a pre-existing,
   apparently host-load-sensitive race in `data_manager.py`'s PARALLEL K-date backfill (unrelated to
   `warmup.py`, which this iteration's change is confined to). Not investigated further (out of
   scope; `data_manager.py` was not touched).
3. **Host quiet could not be guaranteed during the live measurement**, same disclosure discipline as
   Addendum 43: a sibling goal-mode session (`/home/dennis-chan/Git/tensteps`) was actively
   dispatching (an `auditor` step) throughout the capture window. Host headroom was comfortable
   (`MemAvailable` ~21 GB, load average ~1.0-1.3 on a 16-thread host, swap 8 KiB used) and no sibling
   process was stopped (not this developer's call to make unilaterally). The figure is presented as
   honestly and thoroughly instrumented, not as guaranteed-clean — see Addendum 44's own disclosure
   section for the full detail.
4. VmSize/VmRSS (not VmPeak) fluctuate modestly after readiness during the ~30s-180s window of the
   capture — this is the SEPARATE, unrelated `_warm_drawdown_expectations` per-claim step (Known
   Issue 1 above) continuing in the background after the cadence loop + forward-returns this
   iteration bounds has already completed; it does not affect the reported VmPeak high-water mark,
   which never moves after t+30.83s.

**Nothing else new.** The nine previously-carried non-blocking items listed in this iteration's spec
OUT OF SCOPE section (candidate-card screenshot retake, recorded walkthroughs, the
`test_no_magic_numbers.py` red failure, etc.) remain untouched, as directed.

## Pre-handoff verification

- **Service startup:** `scripts/start-backend.sh` was started and stopped cleanly twice this session
  (once against the unmodified baseline for the "before" byte-identity capture, once against this
  iteration's change for the full measurement window), each time reaching `/api/health` 200 within 1s
  and shutting down cleanly on `SIGTERM` with no port conflict on the second start.
  `scripts/start-frontend.sh` was started once (skip-rebuild fast boot, no stale `.next`) for the
  replay lane and stopped cleanly. Final check: `ps aux` shows no stray `uvicorn`/`next-server`
  process from this session; `ss -ltn` confirms ports 8255/3255 free.
- **External integrations:** N/A -- no new adapter/scraper/external API; all live calls this
  iteration made are local HTTP GETs against the already-running backend/frontend and the committed
  canonical DB (AG-9 holds throughout, see Addendum 44).
- **Native dependency binaries:** N/A -- no new dependency was added.

## Escalation note carried forward (unchanged from iter-32, now resolved by this iteration)

iter-32 recorded two owner decisions in case a genuine bounding attempt still missed the target: (a)
accept the honest worst-moment figure, or (b) leave warm-up code untouched. **This iteration's
genuine bounding attempt MET the target** (2,467,888 kB vs the 2,621,440 kB target), so neither
owner decision needs to be invoked — J-09's own acceptance text ("Correctness: measured backend
VmPeak at standing warm ≤ 2.5 GB") is now satisfied by a config-only, whole-job-safe, byte-identical
mechanism. The evaluator should treat J-09 as closed on the numbers, subject to its own review of the
evidence above.
