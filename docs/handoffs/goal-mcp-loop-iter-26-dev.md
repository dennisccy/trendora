# goal-mcp-loop-iter-26 Dev Handoff

**Phase:** goal-mcp-loop-iter-26
**Date:** 2026-07-10
**Agent:** developer
**Status:** audit fix-mode pass complete for the CHARGED regression (audit B3 — the forward-return
`close_on`/`bars_after` transient allocations are removed, byte-identically; VSZ measured at the
full-universe shape). **The root-cause full-universe crash (audit B1) is NOT fixed** — it is pre-existing
architectural memory work (regime `full[:cut]` + whole-universe prefill) explicitly out of this surgical
pass's scope. See "## Fix Notes (2026-07-10 audit fix-mode pass — VSZ memory regression)" at the very
bottom (most recent). The earlier "## Fix Notes (2026-07-10 fix-mode pass)" covered the prior review FAIL
(perf/RSS) and remains valid for that scope.

## What Was Built

- **`indicators.max_lookback_bars` config** (`config.yaml`, `apps/backend/app/config.py`): a new required, validated positive int on `IndicatorsCfg`, committed value `320` (= `high_window_52w` 252 + a ~68-bar safety margin). Two sanity-guard validators added: `IndicatorsCfg._validate` cross-checks it against every individually-configured window on that same model (`ma_periods`, `rs_windows`, `high_window_52w`, `vol_avg_period*2`, `atr_period+1`, `hv_window+1`, `semivol_window+1`, `vol_contraction_recent+vol_contraction_prior+1`); a new `Config._max_lookback_bars_covers_pattern_history` model_validator cross-checks it against the three pattern detectors' `min_history_bars` (VCP/pullback/flat-base), mirroring the existing `_pattern_ma_period_is_an_indicator_period` precedent for why the cross-check lives on `Config` rather than a sub-model. These are sanity guards only — the byte-identity harness (below) is the actual correctness authority, per the phase spec's explicit instruction.
- **Bounded scoring-input window** (`apps/backend/app/engine/scoring.py`): at both `bars_asof` call sites — `_raw_components` (`:113`) and pass-3 (`:339`) — the returned series is sliced to `bars[-icfg.max_lookback_bars:]` immediately after the call, before any indicator/pattern computation. A member with fewer than N bars keeps its whole (shorter) series unchanged.
- **Warm-up forward-return cache-scope fix** (`apps/backend/app/engine/warmup.py`, `apps/backend/app/engine/prices.py`) — two parts, both required (verified against the live code, not assumed from the spec's prose):
  1. `warmup.py:153-165` — `backfill_forward_returns(engine, cfg)` moved INSIDE the `with bar_cache(session):` block that already wraps the cadence loop, AND changed to `backfill_forward_returns(session, cfg)` (passing the session, not the engine) so it takes the `isinstance(Session)` branch and reuses the exact session/cache already active, instead of opening a brand-new uncached session.
  2. `prices.py` — `close_on` (`:343`) and `bars_after` (`:368`) are now cache-aware: each checks `_BAR_CACHES.get(id(session))` first and, if an active cache is found, derives the answer from the cache's already-loaded series (`close_on` via the cache's `bars_asof` + `[-1].close`; `bars_after` via a new `_BarCache.bars_after` method built with the same `bisect.bisect_right` idiom `bars_asof` uses, on the `> d` side). The default (no-context) path is byte-identical to before. This also speeds up the pre-existing `data_manager._do_backfill`'s forward-return step for free, since it already attaches a shared prefilled cache around its own `backfill_run_forward_returns` call but previously gained nothing from it (confirmed in code, not assumed).
- **Byte-identity harness** (new, `apps/backend/tests/test_scoring_window.py`): `score_stocks` windowed (committed 320) vs. an effectively-disabled (1,000,000) window, over 3 real cadence dates × the full resolved pool, plus a dedicated short-history-member date — 0 diffs, confirmed PASSING (see Tests Run).
- **New cache-awareness tests** (`apps/backend/tests/test_forward_testing.py`): `test_close_on_cache_aware_matches_uncached` and `test_bars_after_cache_aware_matches_uncached` prove `close_on`/`bars_after` are byte-identical inside vs. outside an active `bar_cache` context, for both a long-history and a short-history symbol.
- **New query-count proof** (`apps/backend/tests/test_warmup.py`): `test_warmup_loads_each_symbol_at_most_once_across_cadence_and_forward_returns` instruments `_BarCache.bars_asof`/`prefill` and proves the warm-up's cadence loop + trailing `backfill_forward_returns` together load each symbol's bar series AT MOST ONCE for the whole run — confirmed PASSING.
- Mechanical fixture updates (add the new required `max_lookback_bars` field, valued consistently with each fixture's own other window sizes) in `test_config.py`, `test_config_engine.py`, `test_indexes.py`, `test_sectors.py`, `test_themes.py` — no behavior change, required for Pydantic construction to keep succeeding.

## Files Changed

- `config.yaml` — added `indicators.max_lookback_bars: 320`
- `apps/backend/app/config.py` — `IndicatorsCfg.max_lookback_bars` field + validator; new `Config._max_lookback_bars_covers_pattern_history` validator
- `apps/backend/app/engine/scoring.py` — window slice at both `bars_asof` call sites
- `apps/backend/app/engine/prices.py` — `close_on`/`bars_after` made cache-aware; new `_BarCache.bars_after` method
- `apps/backend/app/engine/warmup.py` — `backfill_forward_returns` call moved inside `bar_cache`, passed `session` not `engine`
- `apps/backend/tests/test_scoring_window.py` — new byte-identity harness
- `apps/backend/tests/test_forward_testing.py` — new cache-awareness tests (`close_on`/`bars_after`)
- `apps/backend/tests/test_warmup.py` — new query-count proof test
- `apps/backend/tests/test_config.py`, `test_config_engine.py`, `test_indexes.py`, `test_sectors.py`, `test_themes.py` — mechanical fixture field addition only

## Tests Run

Command base: `cd apps/backend && .venv/bin/python -m pytest <files> -q` (real venv, real committed 30-year/583-symbol seed where noted).

| Suite | Result | Notes |
|---|---|---|
| `test_scoring_window.py` (the byte-identity harness — DoD's primary correctness gate) | **2 passed** in 587.18s | Windowed vs. unwindowed `score_stocks`, 3 dates × full pool + 1 short-history date — 0 diffs |
| `test_bar_cache.py` | **12 passed** in 92.70s | All 12 existing cases, UNEDITED |
| `test_forward_testing_streaming.py` + `test_forward_walk.py` | **12 passed** in 0.44s | UNEDITED |
| `test_config.py` + `test_config_engine.py` + `test_indexes.py` | **128 passed** in 3.41s | Includes the new `max_lookback_bars` fixture field |
| `test_forward_testing.py` | **50 passed, 1 deselected** in 793.31s | Deselected: `test_walk_forward_asof_dates_are_real_trading_days_with_full_horizon` (the ONE test in this file needing the shared session-scoped `loaded_engine` fixture, which pays for a full production-cadence historical warm-up — see Known Issues). Includes both new cache-awareness tests, both PASSING. |
| `test_warmup.py` | **9 passed, then 4 errors + 1 failure** — see Known Issues | The critical new query-count proof (`test_warmup_loads_each_symbol_at_most_once_across_cadence_and_forward_returns`) PASSED. The last 5 tests failed with `sqlite3.OperationalError: disk I/O error` from `tmp_path_factory` — an environment/tmpfs resource exhaustion on this host mid-run, not a code defect (see Known Issues for the exact trace and reasoning). |
| `test_scoring.py`, `test_sectors.py` (7/9 tests), `test_themes.py` (3/4 tests) | **NOT RUN** | Each depends on `conftest.py`'s session-scoped `loaded_engine` fixture (full production-config historical warm-up — the same order of cost as this project's documented ~2h full-suite figure), which did not fit this turn's time budget. Fixture dict correctness (the only iter-26-relevant change in these files) was verified by inspection, not execution — see Known Issues. |
| `test_data_manager.py` | **NOT RUN** | Time budget; historically ~2h combined with 3 other files at this data scale per the iter-25 dev handoff. Its `_do_backfill` forward-return "bonus" cache-awareness path was verified by code inspection (see "What Was Built") but not exercised by this file's own test suite in this turn. |
| Full 30-year pytest suite | **NOT RUN** (correctly, per phase spec's explicit instruction — targeted tests only, ~10-11h fixture cost, non-blocking deferred follow-up) | |

**Real before/after performance measurement (DoD requirement): NOT COMPLETED.** See Known Issues — the host's Bash/shell execution became completely unresponsive (confirmed host-wide via an independent subagent check, not session-specific) before this measurement could be run, immediately after the `test_warmup.py` disk I/O errors above. This is the most significant gap in this handoff against the phase's Definition of Done.

**Service startup / cold-path verification: NOT COMPLETED**, same blocker.

## Known Issues

1. **Real before/after performance measurement is missing (DoD-blocking).** The phase's Definition of Done requires a measured ≥30% improvement (per-date backfill AND a full/representative warm-up pass), same host / prod mode, plus peak-RSS confirmation under 6144 MB. I designed and wrote a benchmark script (`/tmp/claude-1000/.../scratchpad/bench_window.py` — NOT committed, scratch-only) that would time `compute_run_payload` before/after (config-toggled window) on a real late cadence date, plus a warm-up-shaped cadence-loop + `backfill_forward_returns` pass over a real ≥12-date deep-history subset on two independent fresh seed-DB copies (mirroring the exact pre-/post-iter-26 code shapes — the `engine` vs. `session` argument to `backfill_forward_returns`), sampling peak RSS via `resource.getrusage`. **It was never executed**: the host's Bash tool stopped responding (every command, including `echo hello` and `:`, returned exit code 1 with zero output) partway through this session's targeted-test run, and an independent subagent dispatched purely to sanity-check host shell health hit the identical failure — confirming this is a host-wide condition, not something specific to my shell session. The most likely proximate cause, based on the evidence immediately before the failure (see #2), is `/tmp` (a 14 GB tmpfs) exhaustion from this session's own repeated large seed-DB creation across many separate pytest invocations, compounded by this host also running another project's concurrent full pytest suite. **This must be re-run before the phase can be considered done**: either resume this session once the host recovers, or hand the `bench_window.py` script (logic described above) to the next developer/reviewer pass.
2. **`test_warmup.py`'s last 5 tests failed with an environment error, not a code defect.** After 9 clean passes (including the critical new `test_warmup_loads_each_symbol_at_most_once_across_cadence_and_forward_returns`), `test_concurrent_run_scan_threads_no_unique_crash` and 3 others erred at fixture setup with `sqlite3.OperationalError: disk I/O error` inside `tmp_path_factory`'s temp DB (path under `/tmp/pytest-of-dennis-chan/pytest-33`), and the final test (`test_readiness_unavailable_on_empty_db`) failed the same way. This is a generic SQLite commit failure on a brand-new fixture-created DB file — nothing about it touches iter-26's diff. I could not `rm -rf /tmp/pytest-of-*` before this test phase (the project's own documented lesson) because the permission system denied it as a "shared scratch sweep" risk, and by the time the disk I/O errors appeared the host's Bash tool had also become unresponsive, so I could not clear `/tmp` or re-run to confirm. **These 5 tests need to be re-run once the host environment is healthy** (clear `/tmp/pytest-of-*` first, per the project's own operational-hygiene note) before treating `test_warmup.py` as fully green.
3. **`test_scoring.py` (14/15 tests), `test_sectors.py` (7/9 tests), `test_themes.py` (3/4 tests) were not executed.** All of them route through `conftest.py`'s session-scoped `loaded_engine` fixture, which runs a FULL production-config historical cadence warm-up (`bootstrap_runs` + `backfill_forward_returns` over the real `scanner.bootstrap_dates` + walk-forward cadence, not the reduced `_fast_cfg()` other test files use) — empirically the same order of cost as this project's own documented ~2-hour, 123-test combined suite figure (iter-25 dev handoff). None of iter-26's diff touches these three files' logic; the only change in them is the mechanical addition of the new required `max_lookback_bars` config field to each file's fixture dict, valued consistently with that fixture's own other window sizes (e.g. `20` for a synthetic fixture whose `high_window_52w` is `20`). I verified by inspection that each added value satisfies the new validators (`>= high_window_52w`, `>= max(ma_periods)`, `>= max(rs_windows)+1`, `>= 2*vol_avg_period`, `>= largest pattern min_history_bars`, etc.) for that fixture's own other values, and confirmed the SAME pattern already passed cleanly in `test_config.py`/`test_config_engine.py`/`test_indexes.py` (128/128, including several `IndicatorsCfg`/`Config` constructions from equivalent dicts). This is a reasonable but NOT a substitute for actually running these three files — they should be run (ideally batched together in one pytest invocation so the expensive `loaded_engine` fixture is paid once, not three times) as a follow-up before this phase is signed off.
4. **`test_data_manager.py` (84 tests) was not run** — time budget; no `loaded_engine` dependency but has its own module-scoped full-seed fixtures (`backfilled_job`, others) and per iter-25's own dev handoff this file combined with 3 others took ~2 hours. The one iter-26-relevant path in it (`_do_backfill`'s forward-return step benefiting from the now-cache-aware `close_on`/`bars_after`) was verified by direct code inspection (`data_manager.py:2441-2450` already calls `attach_shared_cache` around `backfill_run_forward_returns` — confirmed in the plan's own "Bonus" note and re-verified against the live file), not by running this file's tests.
5. **Service startup verification (backend + frontend prod mode, HTTP 200, cold-`/data`-path OOM check per the iter-24 lesson) was not performed** — blocked by the same host Bash unresponsiveness. This is a normal pre-handoff checklist item that could not be completed.
6. **No frontend source change** (per the phase spec — confirmed nothing under `apps/frontend/` is modified in this diff), so there is no separate frontend handoff.
7. **`reports/perf-budgets.md` was NOT updated** — the DoD requires the real before/after timings to be committed there; since the measurement itself could not be run (#1), nothing was appended. The existing iter-19/24/25 sections are untouched.

## What Remains Before This Phase Can Close

In priority order: (a) recover host Bash access and clear `/tmp/pytest-of-*`; (b) run the before/after performance measurement (script logic described in Known Issue #1) and append results to `reports/perf-budgets.md`; (c) re-run `test_warmup.py`'s last 5 tests to confirm they were purely an environment artifact; (d) run `test_scoring.py`, `test_sectors.py`, `test_themes.py` (batched, to amortize the shared fixture) and `test_data_manager.py`; (e) verify service startup (prod mode, both services, cold `/data` path) before the browser-qa lane runs J-16.

The CODE changes themselves (config, scoring.py, prices.py, warmup.py) are complete and match the plan; the byte-identity harness and the new cache-awareness/query-count tests — the tests most directly proving THIS iteration's correctness — are all green. What is missing is breadth of regression coverage across pre-existing, iter-26-unrelated test files, and the mandatory performance evidence, both blocked by the same late-session host environment failure.

---

## Fix Notes (2026-07-10 fix-mode pass)

This pass addresses the review FAIL (`reports/reviews/goal-mcp-loop-iter-26-review.md`). The host was healthy
this pass (`/tmp` 14 GB free at start). No product source (config.yaml/scoring.py/prices.py/warmup.py) was
re-touched except the one cosmetic comment fix below — the code the reviewer already approved is unchanged.

**NOTE #5 (config.yaml:660 mangled `sectors:` header) — FIXED.** Restored the two clipped context lines
(the `# ---…` separator + the `# iter-2 CONSUMED — Sector/industry leadership. Component weights…` line)
above `sectors:`; the block header now reads coherently again. Only comment lines changed; no YAML value
moved.

**CRITICAL #1 (real before/after perf measurement) — DONE and recorded in `reports/perf-budgets.md`
(new "Item F" section).** Ran a real measurement on this host against the committed 30-year DB, under a
literal `ulimit -v 6291456` (6144 MB, the prod `server.memory_cap_mb` cap). Method: baseline =
`max_lookback_bars = 1_000_000` (`bars[-1_000_000:] == bars`, exactly the pre-iter-26 unwindowed path);
after = the committed `320`. Same subset both runs, network excluded, `min` of 3 reps, inside one shared
prefilled `bar_cache` (mirrors the warm-up's own load-once cache so the delta is the window's real
CPU/allocation effect; the one-time bar load is already budgeted as item A / iter-19).

- **Per-date backfill (latest deep-history cadence date 2026-04-01, full pool):** 1.681 s → 0.320 s =
  **81.0% faster** (≥ 30% ✓).
- **Warm-up pass (12-date deep-history representative subset, same subset both runs — the DoD's sanctioned
  ≥10-date alternative to a full 85-date double run):** 10.169 s → 2.250 s = **77.9% faster** (≥ 30% ✓).
- **Forward-return read step (the warmup.py/prices.py cache-scope change, isolated: one `close_on` + one
  `bars_after` per (run,symbol), 15 runs × pool = 6,110 pairs):** 2.806 s (raw queries) → 0.296 s
  (cache-aware) = **89.4% faster** (≥ 30% ✓).
- Every one of the 12 per-date rows improves 67.6%–81.0% (full table in `perf-budgets.md`). The benefit
  correctly scales with history depth (≈0 marginal window effect on <320-bar early dates; largest on the
  ~5,300-bar latest dates) — corroborating that the change is the trailing-window list-extraction saving,
  not a maths change.
- Bench script (scratch, not committed): logic is fully described in `perf-budgets.md`; it toggles
  `max_lookback_bars` on a fresh `load_config()` per config, times `score_stocks` over the resolved cadence
  subset, and times `close_on`/`bars_after` over the run subset. Re-runnable from `apps/backend` with the
  venv Python.

**CRITICAL #2 (peak RSS under 6144 MB) — DONE.** The SAME measurement above sampled peak process RSS via
`getrusage(RUSAGE_SELF).ru_maxrss` = **1,330.6 MB**, and — decisively — the entire run (scoring + the
full-pool bar prefill + the forward-return reads) COMPLETED under the literal 6144 MB `ulimit -v` cap with
NO `MemoryError`. iter-26 only shrinks per-member allocation and removes per-(run,symbol) forward-return
round-trips, so it cannot raise the ceiling above the full live server's ~1.8 GB cold-`/api/data` peak
already recorded (and under-cap) in the iter-25 section. Recorded in `perf-budgets.md`. (The live in-server
cold-`/data` OOM repro stays the browser-QA lane's job per the iter-24 lesson — unchanged by this pass.)

**MINOR #3 (5 `test_warmup.py` disk-I/O failures) — confirmed ENVIRONMENTAL, not a code defect.** With
`/tmp` cleared/healthy, `test_readiness_unavailable_on_empty_db` (one of the 5 that previously errored with
`sqlite3.OperationalError: disk I/O error`) now **passes cleanly in 0.18 s** — a passing empty-DB SQLite
test is direct proof the earlier failures were `/tmp` exhaustion, exactly as the review + coordinator note
stated. The other 4 (concurrency / warm-DB-fixture tests: `test_concurrent_run_scan_threads_no_unique_crash`,
`test_forward_returns_concurrent_insert_idempotent_no_duplicate`, `test_warmup_failure_is_caught_logged_and_nonfatal`,
`test_start_warmup_is_single_flight_no_duplicate_concurrent_worker`) each build a full 30-year warm DB in
their fixture and run for many minutes; none touches the iter-26 diff (scoring-window / forward-return
cache-scope). They are left to the full-suite lane (see below) rather than re-run under contention.

**MINOR #4 (run `test_scoring.py`/`test_sectors.py`/`test_themes.py`/`test_data_manager.py`) — see result
line below; strong indirect evidence regardless.** `test_scoring.py` and `test_data_manager.py` are UNEDITED
(git-confirmed — not in the diff). `test_sectors.py`/`test_themes.py` carry ONLY a one-line mechanical
fixture addition (`"max_lookback_bars": 20`, ≥ that fixture's own `high_window_52w=20`) — no expected value
changed (git diff confirms). Critically, the byte-identity harness (`test_scoring_window.py`, green) proves
`score_stocks` output is byte-identical windowed vs unwindowed, so an UNEDITED `test_scoring.py` cannot
regress from the window change by construction. A batched `test_scoring.py + test_sectors.py + test_themes.py`
run was launched on the idle box at the end of this pass; its shared `loaded_engine` fixture (a full
30-year warm-DB build — a pre-existing ~20-min-class cost at this data scale, CPU-active throughout, not a
deadlock and not an iter-26 regression) ran **~22 min at 100% CPU without reaching the test phase**.

<!-- BATCH_RESULT -->
> Batched-run result: **not captured within this pass** — the shared `loaded_engine` fixture had still not
> finished building after ~22 min; I stopped it deliberately (it would be reaped at turn end anyway, and
> leaving a runaway 30-year pytest running would compete with the pipeline's own full-suite lane). Deferred
> to that full-suite lane, which covers all four files. This is a MINOR verification-breadth gap, not a
> correctness gap: the iter-26-specific correctness is already proven green (byte-identity harness +
> `test_bar_cache.py` 12, `test_forward_testing.py` 50 incl. both new cache-awareness cases,
> `test_config*`/`test_indexes.py` 128, and the new query-count proof), and the four un-run files are
> unedited (`test_scoring.py`, `test_data_manager.py`) or carry only the one-line mechanical fixture-field
> addition (`test_sectors.py`, `test_themes.py`) with no expected value changed.

**Host-safety note (why the heavy files were not force-run twice):** during this pass a sustained external
`pytest tests/ -q` FULL-suite run was repeatedly active on this box. Piling a second concurrent 30-year
warm-DB pytest on top is the exact concurrent-pytest fork-lock that made the *previous* dev pass's host go
unresponsive (that pass's own Known Issue #1 names "another project's concurrent full pytest suite" as the
proximate cause). I deliberately did not recreate that condition; the external full-suite run is the
canonical lane that confirms these files green on an (eventually) idle box, per the DoD's "defer the
full-suite green to an idle box" instruction and the project's "reviewer verifies tests" lesson.

---

## Fix Notes (2026-07-10 audit fix-mode pass — VSZ memory regression)

Addresses the **audit FAIL** (`docs/handoffs/goal-mcp-loop-iter-26-audit.md`), specifically finding **B3**
(iter-26's cache-aware `close_on`/`bars_after` add large transient list-slice allocations to the
forward-return step of the crashing job) and the audit **§5 fix recipe items (1) and (2)**. Scope this
pass: **only `apps/backend/app/engine/prices.py`** — the two surgical, byte-identity-preserving allocation
reductions. No other file touched (config.yaml / scoring.py / warmup.py from earlier in the iteration are
unchanged). `/tmp` was healthy at start (14 GB free after clearing one stale 2.2 GB `pytest-of-*` dir).

### What changed (both output-identical)

1. **`_BarCache.close_on` (new method) + module-level `close_on` cache branch.** The old cache path did
   `cache.bars_asof(session, symbol, d)[-1].close` — materialising the whole `full[:cut]` (`<= d`) prefix
   (up to ~5,300 `Bar` tuples on a late date) only to read its last element and discard the rest. Replaced
   with a single `bisect.bisect_right(dates, d)` + `full[cut-1].close` (or `None` when `cut == 0`). No
   prefix allocation.
2. **`_BarCache.bars_after` (rewrite).** The old body called `self.bars_asof(session, symbol, d)` purely as
   a load-ensurer and **discarded** the `full[:cut]` prefix it built, then built the whole `full[cut:]`
   tail before truncating with `after[:limit]`. Replaced with (a) a load-ensuring branch mirroring
   `trailing_count`'s idiom (no prefix slice; a no-op on a prefilled cache) and (b) `full[cut:cut+limit]`
   when a `limit` is given (never materialises the full multi-year post-`d` tail just to truncate it). For
   every value the backfill passes (`limit = max(walk_forward.horizons) = 60`, or `None`) this is
   byte-identical to the old `full[cut:][:limit]` and to the raw `.limit(limit)` query.

`bars_asof` itself (the crash-frame code at `prices.py:191`) is **not** modified — its `full[:cut]` return
is its contract for the scoring/regime path and is out of this pass's scope (see boundary below).

### Byte-identity evidence (the NON-NEGOTIABLE — coordinator note 4)

- **Targeted unit tests — all green in 0.15 s** (the 5 tiny-fixture cases directly exercising BOTH paths,
  cache vs default, long+short history, limited+unlimited):
  `test_close_on_is_the_asof_close`, `test_bars_after_returns_only_future_bars_ascending`,
  `test_bars_after_limit_is_the_unbounded_prefix`, `test_close_on_cache_aware_matches_uncached`,
  `test_bars_after_cache_aware_matches_uncached`.
- **Real-DB byte-identity**: on the committed 30-year DB (3,293,160 bars / 590 symbols) under
  `ulimit -v 6291456`, a 3,000-pair `(date, symbol)` spot-check comparing **OLD-code vs NEW-code** for
  `close_on` AND `bars_after` (limited AND unlimited) = **0 mismatches**.
- **Scoring harness — CONFIRMED GREEN this pass**: `test_scoring_window.py` re-run on the committed
  30-year seed = **2 passed in 501.63 s** (`test_score_stocks_windowed_equals_unwindowed_across_dates` and
  `test_score_stocks_windowed_equals_unwindowed_for_short_history_member`). This is expected —
  `scoring.py`/`bars_asof` are untouched this pass and `score_stocks`/`scanner`/`regime` never call
  `close_on`/`bars_after` (grep-confirmed), so the harness result is invariant to this change — but it is
  now verified, not merely argued.

### Memory measurement — VSZ, the actual failing metric (audit B1/B2, coordinator note 2)

Measured on the committed 30-year DB under a **literal `ulimit -v 6291456` (6144 MB = `server.memory_cap_mb`)**,
sampling **VmPeak (peak VSZ — the metric the crash hit)** and **VmHWM (peak RSS)** from
`/proc/self/status`, at the **FULL-UNIVERSE shape** (full prefill of all 590 symbols, then the
forward-return reads over 590 symbols × 367 monthly-cadence dates = **216,530 calls** — the `_do_backfill`
forward-return shape, not a 12-date subset):

| phase | VmPeak (VSZ peak) | VmHWM (RSS peak) | tracemalloc transient peak |
|---|---|---|---|
| after full-universe prefill | 1,365 MB | 1,315 MB | — |
| after **NEW** forward-return sweep (216,530 calls) | 1,365 MB | 1,315 MB | ~0 MB |
| after **OLD** forward-return sweep (216,530 calls) | 1,365 MB | 1,315 MB | ~0 MB |

**Honest reading:** in **isolation**, the forward-return step — old OR new — does **not** itself grow VSZ
toward the 6144 MB ceiling; each per-call transient slice is freed within its iteration and the arena is
reused, so peak VSZ stays at the prefill baseline (~1,365 MB) in both cases. Therefore iter-26's added
forward-return allocation, **while a real and diff-confirmed regression (audit B3) that this pass removes
byte-identically**, is **not on its own the cause** of the VSZ ceiling hit. The fix makes each
forward-return call allocate O(1) instead of O(prefix ≈ 5,300) — strictly less transient pressure, which
can only help in the fully-fragmented real job — but the isolation numbers show it is not the dominant
driver. (Bench script: `scratchpad/fwd_mem_bench.py`, scratch-only, re-runnable with
`ulimit -v 6291456; PYTHONPATH=apps/backend .venv/bin/python fwd_mem_bench.py --mode {old,new,--verify}`.)

### What this pass does NOT fix (honest scope boundary — audit §5 item 4, coordinator note 3)

The crash the audit reproduced was `MemoryError` at **`_BarCache.bars_asof:191` (`full[:cut]`)** reached via
**`regime._index_ma_stack`**, inside the full 322-date `_do_backfill` which (a) prefills the ENTIRE 3.29M-bar
universe up front and (b) per date materialises `full[:cut]` slices in the **UNWINDOWED regime path** over
all members. That frame is **pre-existing, unmodified code** (git-confirmed: iter-26 never touched
`regime.py` / `data_manager.py` / `scanner.py`), and the scoring-window bound was applied only at the two
scoring sites, **not** the regime path. Bounding/streaming those regime `full[:cut]` allocations and/or the
full-universe prefill so the deep-basis rebuild stays under `ulimit -v` is **architectural memory work
beyond this surgical byte-identity-preserving pass**; per the audit's own §5 item 4 it should be owned as
its **own memory-hardening iteration**.

I did **not** run the full 322-date `_do_backfill` (regime + full scoring + forward returns) to completion
under the cap — it is a long run at the 30-year basis (per-date scoring 2–8 s × 322 dates plus the
full-universe prefill), and the outcome is predictable: since the dominant regime `full[:cut]` allocator is
unchanged, the full-universe rebuild is expected to **still approach the VSZ ceiling**. **I therefore do NOT
claim the crash is fixed.** This pass removes and quantifies the specific allocation the audit charged to
iter-26's diff (B3), byte-identically; the architectural crash frame remains open.

### Files changed this pass

- `apps/backend/app/engine/prices.py` — `_BarCache.close_on` (new), `_BarCache.bars_after` (rewrite: no
  discarded prefix, sliced tail), module-level `close_on` cache branch routed to `_BarCache.close_on`.
  **No other file.**

### Known Issues (this pass)

- **The full-universe `_do_backfill` VSZ exhaustion (audit B1) is NOT resolved** by this surgical pass — it
  is an architectural problem in the pre-existing regime path + full-universe prefill (see boundary above).
  **J-16 browser-qa is expected to still fail** on the full "Rebuild snapshots for current universe" job
  until a dedicated memory-hardening iteration bounds/streams those allocations. This is the honest state:
  the charged iter-26 regression is removed, the root-cause crash is not.
