# goal-ops-hardening-iter-31 Dev Handoff

**Phase:** goal-ops-hardening-iter-31
**Date:** 2026-07-29
**Agent:** developer
**Status:** complete

## What Was Built

Hardening-only iteration, no new journey/page/endpoint/score/claim, no UI change. Closes the session's
oldest still-open critical AG-8 finding — `/research/factor-lab?all=true`'s `MemoryError` at
`research.py:583` — deferred at both iter-29 and iter-30 — plus the audit's separately-found B5
concurrency gap in the same read path.

- **Fix 1 — bounded the Factor-Lab-all RETURN VALUE (`apps/backend/app/engine/research.py`):**
  `_all_factor_observations_by_horizon`'s join accumulator was already run-chunk-bounded at iter-29, but its
  RETURN SHAPE was documented as "NOT bounded here (deliberate)" — `{horizon: [5-key dict, ...]}`, one full
  Python list per configured horizon, each dict inlining its OWN copy of `run_id`/`ticker` on top of the
  (already-shared) `values` reference. Restructured to a genuine, byte-preserving memory-representation
  redesign (not a smaller constant):
  - `core_records: list[tuple[run_id, ticker, values]]` — ONE entry per `ScannerResult` with a realized
    return at >= 1 horizon (~781K on the live basis), built lazily on the FIRST horizon a result has an FR
    at (the same trigger the old shared `values` dict used). `ticker` is interned against a local
    dict scoped to the call (dedupes the ~590-symbol universe instead of allocating a fresh string per
    horizon-observation); `values` is now a TUPLE ordered to match the `factors` list (position-indexed,
    never dict-keyed).
  - `pools[h]: list[tuple[core_idx, realized_return, max_drawdown]]` — only the genuinely per-horizon data;
    identity + factor values are shared via `core_idx` into `core_records`.
  - The existing "ONE shared read serves every factor at every horizon" property is unchanged (still ONE
    call from `compute_factor_lab_all`, still one run-chunked sweep of `ScannerResult`/`ForwardReturn` —
    `test_all_factors_fires_one_shared_pool_read_not_n` passes unmodified) and every `(factor, horizon,
    decile)` output value is byte-identical to the pre-iteration reference (proven both on a hand-built
    fixture and against the live-shaped shipped config).
  - New `ResearchCfg.factor_pool_max_observations` config field (own unit, boot-validated `>= 1`, default
    2,000,000) is an AG-8 DISCLOSURE net layered on top of the representation fix: if a future data-scale
    widening ever pushes a horizon's pool past this ceiling, the function logs a WARNING and keeps going —
    it never raises and never truncates (truncation would break the byte-identity contract). Documented in
    `config.yaml` with the live measured basis (see "Live verification" below).
- **Fix 2 — single-flight guard on `factor_lab_all_cached`'s MISS path (`research.py`):** the audit's B5
  finding — a concurrent duplicate `compute_factor_lab_all` invocation for the SAME cache identity completed
  while another was already in flight and about to write the same row, wasting exactly the memory headroom
  Fix 1 exists to create — is closed by mirroring `data_manager.compute_coverage`'s established per-key-lock
  + in-flight-event idiom (`_FACTOR_LAB_ALL_LOCK` / `_FACTOR_LAB_ALL_INFLIGHT`, no new abstraction) with
  `forward_aggregates_ingest_cached`'s bounded-wait failure-path convention
  (`_FACTOR_LAB_ALL_WAIT_TIMEOUT_S`, sized at **900 s** = the measured 300 s worst-case cold-MISS compute ×
  a safety factor of 3 — see "Fix Notes" below; the first cut copied `_FORWARD_AGG_WAIT_TIMEOUT_S`'s 45 s
  and was correctly rejected in review as shorter than this call's own compute): the FIRST
  caller for a `(asof_key, dataset_version+token, horizon)` key computes; every other concurrent caller
  waits (bounded), then re-reads the now-persisted row with its own session. A waiter whose bounded wait
  elapses (owner raised, or a genuine wedge) falls through and computes independently — never a hang, never
  a raise of its own.
- **Left byte-frozen, as specified:** `_factor_observations`, `_runs_with_fr`, `_fr_slice_map` (the
  single-factor path serving `/evidence`'s drawdown expectations, evaluator-confirmed fixed at iter-29) —
  zero diff, confirmed by `grep`. `compute_forward_aggregates`, `resolved_forward_aggregate_evidence`,
  `ensure_historical_forward_aggregates_dispatched` (`forward_testing.py`) — zero diff. `stock_obs`
  (`forward_testing.py:988`), `warmup.py:194`'s boot MemoryError, `prices.py:141`'s coverage-refresh
  prefill, `_combination_observations` / `_event_study_members` — all explicitly out of scope this
  iteration (session rule 5, one risky change per iteration), unchanged.

## Files Changed

- `apps/backend/app/engine/research.py` -- `_all_factor_observations_by_horizon` restructured to return
  `(core_records, pools)` (compact encoding, AG-8 disclosure warning); `compute_factor_lab_all`'s
  per-(factor, horizon) filter updated to consume the new shape (byte-identical values, same order);
  `factor_lab_all_cached` gains the single-flight lock/event/bounded-wait guard around its MISS path;
  `logger = logging.getLogger("trendora.research")` added (module had none before); `import logging`,
  `import threading` added.
- `apps/backend/app/config.py` -- new `ResearchCfg.factor_pool_max_observations: int = 2_000_000` field +
  boot validation (`>= 1`).
- `config.yaml` -- `research.factor_pool_max_observations: 2000000` with a comment documenting the live
  measured basis (771,629-804,372 observations/horizon, 2026-07-29) it must sanely cover.
- `apps/backend/tests/test_factor_lab_all.py` -- updated the two tests that inspected
  `_all_factor_observations_by_horizon`'s raw return shape directly
  (`test_shared_pools_chunked_equal_the_pinned_unchunked_reference` via new
  `_materialize_compact_pools`/`_reference_as_positional` test-only adapters that expand the compact shape
  back to the pinned pre-fix reference shape for comparison; `test_shared_pool_accumulator_is_chunk_bounded_
  at_the_shipped_config` via a 2-tuple unpack) — the pinned oracle (`_all_pools_reference_unchunked`) itself
  is UNTOUCHED. Added 4 new tests: `test_shipped_factor_pool_max_observations_actually_covers_the_live_
  basis` (TC-6, shipped-config-vs-live-basis, mirrors `test_shipped_factor_join_run_chunk_actually_binds_
  on_the_live_basis`'s convention), `test_factor_pool_cap_exceeded_logs_a_warning_and_never_truncates`
  (mechanism test, tiny overridden cap + `caplog`), `test_factor_lab_all_cached_single_flight_dedups_
  concurrent_miss_to_one_compute` (TC-3, `ThreadPoolExecutor`, call-count instrumentation),
  `test_factor_lab_all_cached_waiter_does_not_deadlock_when_owner_raises` (TC-4, owner-raises failure path).
- `apps/backend/tests/test_research_streaming.py` -- ONE genuine unrelated collision found and fixed (not
  in the plan's explicit list, flagged per the retry-mode note that touching this file is allowed "only if
  a genuine unrelated collision forces it"): `test_all_factor_observations_by_horizon_matches_per_factor_
  per_horizon` also directly consumed the OLD dict-shaped return value and failed with `TypeError: 'int'
  object is not subscriptable` on the RED check. Updated to unpack `(core_records, pools)` and index
  `values` positionally — same intent, same assertions, no test logic changed.
  `test_all_factor_observations_by_horizon_chunk_independent` needed NO change (`_eq` compares the new
  2-tuple structurally, unaffected by the shape change).

## Tests Run

Command (host-guard taskset/BLAS-capped per `project-extensions/host-guard/host-guard.env`; run in the
foreground, never concurrently with another pytest process):

```
cd apps/backend && taskset -c 0-3,8-11 env OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 MKL_NUM_THREADS=4 \
  NUMEXPR_NUM_THREADS=4 .venv/bin/python -m pytest tests/test_factor_lab_all.py -v
```
**Result: 22 passed in 4.04s** (18 pre-existing + 4 new: TC-6 shipped-config-covers-live-basis, the
cap-exceeded-warning mechanism test, TC-3 single-flight dedup, TC-4 waiter-does-not-deadlock).

RED check (confirmed before implementing): the 4 new tests failed as expected (`AttributeError` /
`TypeError` — the config field and single-flight guard did not exist yet); all 18 pre-existing tests in the
file still passed.

Wider regression sweep (every cheap-fixture research-adjacent + config + evidence file):
```
cd apps/backend && taskset -c 0-3,8-11 env OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 MKL_NUM_THREADS=4 \
  NUMEXPR_NUM_THREADS=4 .venv/bin/python -m pytest tests/test_research_streaming.py tests/test_research.py \
  tests/test_regime_phase_factor.py tests/test_iter20_research_cluster.py \
  tests/test_phase_severity_lab.py tests/test_regime_lab.py tests/test_samples.py \
  tests/test_severity_velocity.py tests/test_config.py tests/test_factor_lab_all.py \
  tests/test_evidence.py -q
```
**Result: 392 passed in 51.07s.** Zero failures (this run includes the one `test_research_streaming.py` fix
above; before that fix, the same sweep reported 2 failed / 350 passed, isolating the collision cleanly).

`test_shipped_factor_join_run_chunk_actually_binds_on_the_live_basis` and the rest of
`test_research_streaming.py`'s `_factor_observations`/`_runs_with_fr`/`_fr_slice_map` proofs are among the
350+392 passed above — confirmed passing UNMODIFIED (zero diff to their bodies).

Not run: the full suite (project convention — the 30-year `loaded_engine`-based tests make it ~10-11h;
deliberately excluded `test_api_research.py` / `test_api_evidence.py`, `loaded_engine`-based, per the
iter-28/iter-29 convention of steering new/regression runs at cheap fixtures only). The reviewer/QA verify
the broader suite.

## Live verification (measured peak memory vs `server.memory_cap_mb` — DoD requirement)

Started the backend via `scripts/start-backend.sh` (prod mode, host-guard caps applied, `logs/backend.log`
boot banner at line 132519, `2026-07-29T04:02:57Z`) against the LIVE deep-basis DB
(`apps/backend/data/trendora.db`, ~4.97 GB). Measured basis at query time (direct SQL, `sqlite3` module):
`forward_returns` per horizon = h1 804,372 / h5 802,156 / h10 799,381 / h20 793,837 / h60 771,629 (3,971,375
total); `scanner_results` 781,965 total, 781,417 with a realized return at >= 1 horizon. These are the exact
figures documented in `config.yaml`'s `factor_pool_max_observations` comment.

Methodology: an `EventStudyCache` row for `subject='__all_factors__'` already existed from before this
session (a stale cache HIT would have skipped the compute entirely) — deleted it directly (a best-effort
cache table, safe to clear) to force a genuine cold MISS, waited for the boot warm-up to fully stabilize
(`VmHWM` unchanged across 3 consecutive 5s polls, `GET /api/health` reporting `readiness: "ready"`,
`background_compute.active: []`), recorded the stabilized baseline, then fired
`GET /research/factor-lab?all=true` and re-read `/proc/<pid>/status` immediately after completion. Repeated
across TWO independent backend restarts (cache cleared each time) for reproducibility.

| | Run 1 (PID 4148491) | Run 2 (PID 4193353, isolated baseline) |
|---|---|---|
| Pre-request `VmHWM` | 2,088,416 kB (from earlier unrelated warm-up growth) | 2,181,564 kB (stabilized baseline) |
| Post-request `VmPeak` | 2,435,820 kB | 2,518,784 kB |
| Post-request `VmHWM` | 2,088,416 kB (unchanged) | 2,181,564 kB (unchanged) |
| Response | HTTP 200, 117,289 bytes | HTTP 200, 117,289 bytes — **byte-identical to Run 1** |
| Wall time | ~2-4 min (host-guard halves available cores) | ~4-5 min |

**Actual measured peak: `VmHWM` = 2,181,564 kB ≈ 2,130 MB ≈ 2.08 GB; `VmPeak` = 2,518,784 kB ≈ 2,460 MB ≈
2.40 GB.** Compared plainly to `server.memory_cap_mb` = 6,144 MB: **margin ≈ 3,684 MB (~60% headroom below
the cap on the virtual-memory dimension `ulimit -v` actually enforces)** — not a thin margin, stated as
measured, not rounded. In BOTH restarts the compute's peak never exceeded the process's already-stabilized
post-warmup baseline (`VmHWM` identical before and after the request) — i.e., the all-factors compute's own
incremental memory need fits inside memory the process had already touched during normal boot warm-up,
comfortably below the cap on both occasions.

Additional live evidence:
- `logs/backend.log` from this boot's banner (line 132519) onward: **zero `MemoryError` lines** (`grep -c
  MemoryError` after the banner = 0), across both a cold-MISS request AND the same-process idle/health
  polling around it.
- The two independent cold-MISS computes (separate process restarts, separate cache-clears) produced
  **byte-identical response bodies** (`diff` = no output) — the fix is deterministic, not merely
  "didn't crash this once."
- `GET /api/health` throughout: `status: "ok"`, `readiness: "ready"`, `background_compute.active: []` — the
  factor-lab compute (a synchronous request-path call, unchanged by this iteration) did not register as a
  background-compute window, and health stayed responsive to interleaved polls during the multi-minute
  compute.
- Backend stop/restart: killed cleanly via port-based `lsof -ti :8255` (twice, for the two measurement
  runs) and once more at the end of this session; confirmed no port conflicts on relaunch and no dangling
  `uvicorn`/`next dev` process for this project afterward.

Single-flight guard: proven by the two new unit tests (TC-3/TC-4) above, not re-tested live (a live
concurrent-duplicate reproduction would require racing two simultaneous `?all=true` requests against the
SAME multi-minute compute window — the unit tests' call-count instrumentation is the authoritative proof
per the plan's own test-first contract; QA/browser verification is scoped to the single-request TC-1/TC-2
path).

## Known Issues

- **[RESOLVED in the fix round below — kept for the record] `test_no_magic_numbers.py` gains ONE new
  pre-existing-pattern line.** The review-round fix derives the timeout from two INTEGER constants, so
  `research.py` no longer contributes a float literal at all and has dropped off the offender list. The
  original note follows. The new
  `_FACTOR_LAB_ALL_WAIT_TIMEOUT_S = 45.0` module constant (mirroring `forward_testing._FORWARD_AGG_WAIT_
  TIMEOUT_S = 45.0` exactly, per the plan's explicit instruction to reuse that convention) is flagged by
  `test_engine_calc_code_has_no_magic_numbers` as a float literal in an engine calc file — the SAME false
  positive `forward_testing.py`'s own identical constant already triggers (a carried, non-blocking,
  documented issue per the phase spec's NOTES: "`test_no_magic_numbers.py` red on unrelated files
  (`indicators.py`, `forward_testing.py`) ... own future iterations"). This is a test-infrastructure
  limitation (it cannot distinguish a single well-named module constant from a scattered inline literal),
  not a new magic number introduced by this iteration in the sense the rule targets; not touched (out of
  developer scope this iteration, per the carried-issue list).
- **TC-1/TC-2 (real-browser cold-MISS + zero-MemoryError spot-check) were exercised via `curl`, not a real
  browser.** The API-level evidence above (HTTP 200, correct real factor/decile payload shape, byte-identity
  across repeats, zero `MemoryError` in the log) is strong circumstantial proof the fix works at full scale,
  but the formal browser capture (screenshot, zero console errors, DOM assertion) is reviewer/QA's job per
  the plan's own scoping — this developer agent verified the underlying mechanism, not the UI presentation
  (which is unchanged by this backend-only fix).
- **TC-8 (J-01/J-03/J-04/J-05/J-08/J-09 required-still-passing replay) was not run by this developer
  agent** — explicitly scoped to QA/the deterministic replay lane, and running it here would risk
  re-triggering a background-compute window on a consumed as-of date (session rule: "never re-trigger
  live memory pressure beyond what this iteration's own TC-1/TC-2 spot-check requires").
- No product-code regression found; no new anti-goal finding surfaced during this iteration's own work.

## Fix Notes (review round 1 — FAIL, `reports/reviews/goal-ops-hardening-iter-31-review.md`)

ONE issue was raised (CRITICAL, `research.py:3059`) and it is fixed. Nothing else was touched.

**The finding (accepted in full, no push-back):** the single-flight bounded wait shipped at
`_FACTOR_LAB_ALL_WAIT_TIMEOUT_S = 45.0`, copied from `forward_testing._FORWARD_AGG_WAIT_TIMEOUT_S` without
checking it against THIS call's own duration — while the "Live verification" section of this very handoff
measures a cold-MISS `compute_factor_lab_all` at ~2-4 min / ~4-5 min under the mandatory host-guard CPU caps
(AG-10, permanent on this host). With 45s << ~300s every waiter would have woken mid-compute, found no
persisted row, and started its own duplicate compute — the guard would have been inert exactly where audit
B5 needed it. The reviewer was right that TC-3/TC-4 could not catch this: their owner computes finish in
milliseconds and never approach the ceiling.

**Fix 1 — size the wait against the measured duration (`apps/backend/app/engine/research.py`).** The
constant is now DERIVED, not copied, and the derivation is stated in the code:
`_FACTOR_LAB_ALL_MEASURED_COLD_MISS_S = 300` (worst observed live cold-MISS, the 2026-07-29 measurement
above) × `_FACTOR_LAB_ALL_WAIT_SAFETY_FACTOR = 3` → **900 s (15 min)**. Rationale recorded in the comment:
the owner ALWAYS sets the in-flight event in its `finally` (success or raise), so a healthy request never
touches this ceiling — only a genuinely wedged owner does. Sizing it generously therefore costs a normal
request nothing, while sizing it below the real compute duration silently disables the de-dup. The wait
stays BOUNDED (the fall-through-to-independent-compute failure path is unchanged, never a hang), and both
new values are integer seconds (`Event.wait` accepts an int).

**Fix 2 — make the rare fallback observable (same function).** The fall-through path (owner raised, or a
genuine wedge outlasted the 900 s ceiling) now emits `logger.warning("factor_lab_all single-flight wait
elapsed or owner failed for key=%s …")`. B5 was originally found by *observing* a duplicate compute; this
is the only path that can still start one, so it must never start one silently again. Two lines, same
function, no new abstraction.

**Fix 3 — tests that actually exercise the boundary (`apps/backend/tests/test_factor_lab_all.py`).**
Two new tests, mirroring conventions already in this file:
- `test_shipped_factor_lab_all_wait_timeout_covers_the_measured_live_cold_miss_compute` — the
  shipped-value-vs-live-measurement lock (same convention as
  `test_shipped_factor_pool_max_observations_actually_covers_the_live_basis` and
  `test_shipped_factor_join_run_chunk_actually_binds_on_the_live_basis`): asserts the shipped constant is
  `> 45 s`, `>= 2 × the measured 300 s`, and `<= 3600 s` (still a bounded wait, not an effectively-infinite
  one). Reverting toward the rejected value fails this immediately.
- `test_factor_lab_all_single_flight_holds_across_a_compute_past_the_pre_fix_timeout` — **slow by design,
  ~48 s of real wall time, no patched clock and no scaled proxy** (the finding was precisely that the
  constant had never been tested against a realistic duration). The owner's compute is stretched to 48 s —
  PAST the rejected 45 s ceiling — with the SHIPPED constant left untouched; the waiter must still be
  waiting when the owner persists, so `compute_factor_lab_all` must run EXACTLY ONCE.

**RED check on the fix (the review finding reproduced, then closed):** with the constant temporarily set
back to `45.0`, both new tests FAIL, and the slow one fails with exactly the reviewer's predicted symptom —
`compute_factor_lab_all ran 2 times for one slow (48.0s) same-key MISS`, together with the new warning line
`… wait elapsed or owner failed for key=('all', 'r2-f80-allh-mdd-v1', 20) after 45.0s — computing
independently (duplicate compute possible)`. The constant was then restored and both pass. The duplicate
compute is therefore not a theoretical argument in this handoff — it was reproduced on this host and is
now covered by a test that fails if the value regresses.

**Tests re-run after the fix** (host-guard `taskset -c 0-3,8-11` + BLAS caps, foreground, no concurrent
pytest, isolated `TMPDIR`):
```
.venv/bin/python -m pytest tests/test_factor_lab_all.py tests/test_no_magic_numbers.py -v
  -> 25 passed, 1 failed in 51.61s
     (test_factor_lab_all.py: 24/24 PASSED — 22 prior + the 2 new;
      test_no_magic_numbers.py::test_engine_calc_code_has_no_magic_numbers is the pre-existing carried
      failure, see below)
.venv/bin/python -m pytest tests/test_research_streaming.py tests/test_config.py tests/test_research.py -q
  -> 205 passed in 23.02s   (regression guard; `_factor_observations`/`_runs_with_fr`/`_fr_slice_map` and
     `test_shipped_factor_join_run_chunk_actually_binds_on_the_live_basis` still green, unmodified)
```

**A prior Known Issue is now resolved by this fix.** The round-1 handoff recorded that
`_FACTOR_LAB_ALL_WAIT_TIMEOUT_S = 45.0` added a NEW `research.py` line to
`test_no_magic_numbers.py::test_engine_calc_code_has_no_magic_numbers`. Deriving the timeout from two
INTEGER constants removes that float literal; the test's offender list is now back to the pre-existing,
carried-in-the-spec entries only — `indicators.py: 0.5 / 0.95` and `forward_testing.py: 45.0 / 0.5 / 0.9`.
`research.py` no longer appears (verified in the run above; `research.py` contained exactly one float
literal — the one this fix removed). That test remains red on those other files, unchanged and out of scope
per the phase spec's NOTES.

**Not re-measured live.** The 900 s value changes only how long a NON-owner caller waits before giving up;
it cannot change the memory figures, the served payload, or the single-request path measured in "Live
verification" above (a single request is always the owner and never waits). No new live cold-MISS run was
triggered — the session rule forbids re-triggering live memory pressure beyond what TC-1/TC-2 requires, and
nothing in this fix could have moved those numbers.

**Nothing else changed.** No new problem was discovered while fixing; the return-value memory redesign, the
config knob, the byte-identity oracles, and the frozen `_factor_observations`/`_runs_with_fr`/`_fr_slice_map`
path were all reviewer-confirmed correct and were not touched.
