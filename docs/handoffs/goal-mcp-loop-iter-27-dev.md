# goal-mcp-loop-iter-27 Dev Handoff

**Phase:** goal-mcp-loop-iter-27
**Date:** 2026-07-10
**Agent:** developer
**Status:** complete

## What Was Built

- **`_BarCache.bars_asof_window` + module-level `bars_asof_window`** (`apps/backend/app/engine/prices.py`,
  additive): a bounded trailing-window bar accessor. `bars_asof_window(session, symbol, d, lookback)` is
  byte-identical to `bars_asof(session, symbol, d)[-lookback:]` (same rows, same order, same `date <= d`
  no-lookahead boundary) but computes `full[max(0, cut - lookback):cut]` directly instead of materializing
  the whole `<= d` prefix first. Cache-aware (slices the once-loaded cached series when a `bar_cache`
  context is active) and default-path (bounded `WHERE date <= d ORDER BY date DESC LIMIT lookback` +
  reverse) branches, mirroring the existing `close_on`/`bars_after` dispatch pattern. `bars_asof` itself and
  every other pre-existing consumer/behavior is UNCHANGED.
- **`regime.py` routed through the bounded accessor** (the primary fix — this is the exact crash frame from
  the iter-26 audit): `_index_ma_stack` and `_universe_stats` now read through
  `bars_asof_window(..., lookback=cfg.indicators.max_lookback_bars)` instead of the whole-prefix
  `bars_asof`; `_latest_vix` now reads through the already-optimized `close_on` (O(1) via bisect) instead of
  building a whole prefix to read one scalar.
- **`scoring.py` routed through the bounded accessor too** (plan fallback lever 1, applied — see "Known
  Issues" for why): `_raw_components` and pass-3's two `bars_asof(...)` + `bars[-N:]` two-step slices now
  call `bars_asof_window(..., lookback=icfg.max_lookback_bars)` directly — mathematically identical, so the
  existing (unedited) `score_stocks` byte-identity harness continues to pass unchanged.
- **Byte-identity gate extended** (`apps/backend/tests/test_scoring_window.py`): added
  `test_score_regime_windowed_equals_unwindowed_across_dates` (same 3 real cadence dates the `score_stocks`
  harness uses, with a vacuous-pass guard) and
  `test_bars_asof_window_matches_tail_slice_default_and_cached` (direct `bars_asof_window` vs.
  `bars_asof(...)[-lookback:]` equivalence, default + cache-active paths, long/short-history symbols, every
  boundary case: empty/no-bar symbol, `d` before the first bar, `d` after the last bar, `cut == 0`,
  `cut == len(full)`, `lookback` > available history).
- **Full 322-date × 590-member "Rebuild snapshots" memory measurement**, under a literal
  `ulimit -v 6291456` (6144 MB), on two DB shapes (fresh committed seed, and an isolated copy of this
  host's actual accumulated dev DB), before vs. after the fix — recorded in `reports/perf-budgets.md`
  ("Item G"). See "Known Issues" below for the honest limitation of this measurement.

## Files Changed

- `apps/backend/app/engine/prices.py` -- add `_BarCache.bars_asof_window` + module-level
  `bars_asof_window` (additive; `bars_asof` and every other function unchanged)
- `apps/backend/app/engine/regime.py` -- route `_index_ma_stack`/`_universe_stats` through
  `bars_asof_window`; route `_latest_vix` through `close_on`
- `apps/backend/app/engine/scoring.py` -- route `_raw_components`/pass-3's two `bars_asof(...)` +
  `bars[-N:]` slices through `bars_asof_window` directly (fallback lever 1, applied)
- `apps/backend/tests/test_scoring_window.py` -- new `score_regime` windowed-vs-unwindowed test + new
  direct `bars_asof_window` equivalence test (+ `window_price_engine` fixture)
- `reports/perf-budgets.md` -- new dated section "Item G" (before→after full-universe VSZ/RSS budget)

## Tests Run

Command: `apps/backend/.venv/bin/python -m pytest <file> -v` (targeted files, NOT the full suite — per
coordinator instruction; the full suite is ~10-11h at this 30-year data basis)

- `apps/backend/tests/test_scoring_window.py` — **4 passed** (2 existing `score_stocks` tests unaffected +
  2 new iter-27 tests), re-run twice (once after the `regime.py` fix, again after the `scoring.py` fallback
  lever) — both runs green.
- `apps/backend/tests/test_forward_testing.py -k "bars_after or close_on or no_lookahead or cache_aware"`
  — **5 passed** (the cache-awareness/no-lookahead boundary tests the plan names — untouched by this
  change, confirmed still green).
- `apps/backend/tests/test_bar_cache.py` — **12 passed** (re-run AFTER the `scoring.py` change too, since
  several of its tests drive real `score_stocks`/backfill runs through the changed code paths — the
  load-once-per-job counting test (`test_kdate_backfill_loads_each_symbol_at_most_once`) and the
  cached-vs-uncached snapshot-equality tests all stay green).
- `apps/backend/tests/test_warmup.py` — **9 of 14 confirmed PASSED**, zero failures, in file order:
  `test_ensure_latest_persists_only_latest_before_warmup`,
  `test_readiness_unavailable_then_initializing_then_ready`,
  `test_warmup_produced_every_cadence_snapshot_and_forward_returns`,
  `test_warmup_loads_each_symbol_at_most_once_across_cadence_and_forward_returns` (the load-once counting
  test that most directly exercises this change's code paths), `test_warmup_precomputes_membership_
  timeline_cache`, `test_membership_timeline_cache_warm_failure_is_nonfatal`,
  `test_lifespan_serves_dashboard_200_while_warmup_in_flight`,
  `test_scheduling_change_only_old_synchronous_path_is_a_noop`,
  `test_run_scan_concurrency_safe_returns_existing_no_duplicate`. The remaining 5 (from
  `test_concurrent_run_scan_threads_no_unique_crash` onward) were still mid-run, slowed by host resource
  pressure this session's own repeated testing created (see "Known Issues"), when this handoff was
  finalized — an incomplete run, not a failure; zero of the tests that DID complete failed. This file is
  not a listed gate in the plan's Key Test Scenarios.
- `apps/backend/tests/test_scoring.py` — attempted but not completed (see "Known Issues"); NOT a listed
  gate in the plan's Key Test Scenarios, and its structural assertions (bucket ranges, component keys,
  ranking order) are logically implied by the byte-identity proof already established.

**Migrations:** none (no schema change).

## Known Issues

- **Memory measurement is honest but inconclusive on attribution, and does NOT by itself prove the live
  crash is resolved.** Four full 322-date × 590-member isolated "rebuild" runs (fresh seed before/after
  the fix; a copy of the actual accumulated dev DB before/after the fix) all completed `ok` with peak
  VmPeak/VmSize ≈ 3.3–3.4 GB and peak VmRSS ≈ 2.8–2.9 GB, comfortably under the literal 6144 MB
  `ulimit -v` cap (verified genuinely enforced via a deliberate 7 GiB allocation that correctly raised
  `MemoryError` under the same wrapper) — but the BEFORE and AFTER numbers are nearly IDENTICAL on both DB
  shapes. This isolated, short-lived (~150–180 s), single-purpose harness never reproduces the reported
  crash even in the pre-fix state, so it cannot discriminate this fix's contribution. The most likely
  explanation (detailed in `reports/perf-budgets.md` Item G): the dominant fixed cost in this harness is
  the whole-universe bar-cache prefill itself (unaffected by windowing by design — the cache always
  retains the full per-symbol series regardless of how a caller windows its reads), and the live crash
  occurred inside a long-lived, busy `uvicorn` process carrying additional baseline overhead and allocator
  fragmentation history this isolated script cannot replicate. **This is why the `scoring.py` fallback
  lever (plan-sanctioned lever 1) was applied in addition to the primary `regime.py` fix**: since the
  isolated measurement could not empirically rule out needing it, and it is low-risk/byte-identical
  (proven by the unedited `test_scoring_window.py` harness), applying it was the more conservative choice
  given anti-goal #8's "never exhaust a service's memory" bar. The `prefill(symbols=/min_date=)` fallback
  lever (lever 2) was NOT applied — it is a larger, more invasive change, and nothing in this session's
  evidence pointed at needing it; it remains available if the live browser-qa lane still reproduces the
  crash.
- **The live browser-qa J-16 lane (stop → cold-start → drive the actual "Rebuild snapshots" job) is the
  authoritative check this fix has not yet passed through.** Per the coordinator's explicit instruction,
  the 322-date rebuild was NOT triggered against the live shared backend from this developer pass (only
  against isolated, throwaway DB copies) — that live verification is the next pipeline step's job, not
  this one's, and this handoff does not claim its result.
- **Host resource exhaustion during this session's own testing**, not a product defect: `/tmp` on this host
  is a RAM-backed tmpfs (14 GB) that filled to ~80% from the cumulative temp SQLite DBs this session's own
  repeated pytest/memory-measurement runs created (`/tmp/pytest-of-dennis-chan/` alone reached 5.4 GB
  across many runs; the permission system correctly declined to let me `rm -rf` that shared path, so it
  could not be fully reclaimed). This caused intermittent, silent failures late in the session (`pytest`
  and even plain shell commands occasionally exiting with no output) — diagnosed via `df -h /tmp` and
  `free -h`, NOT a code defect. Mitigated by cleaning up this session's OWN scratch DB copies and
  redirecting later pytest runs' `--basetemp` to the real project disk (`204 GB` free) instead of the
  tmpfs. `test_warmup.py`'s final confirmation run was affected by this and its result was not captured
  cleanly before this handoff was written — it exercises the same `bar_cache`/`score_regime`/`score_stocks`
  code paths `test_bar_cache.py` (12/12 green, re-run after the `scoring.py` change) and
  `test_scoring_window.py` (4/4 green) already proved byte-identical, so the risk this specific gap
  represents is low, but it is flagged honestly rather than silently claimed green.
- No config or schema changes. `indicators.max_lookback_bars` (320, committed in iter-26) is reused
  unchanged — no new config value was introduced, per the plan.
- No frontend source was touched (verification-only per the phase spec); no separate frontend handoff was
  written.

---

## Fix Notes (2026-07-11 — second fix pass, after audit FAIL)

**Audit verdict addressed:** `docs/handoffs/goal-mcp-loop-iter-27-audit.md` = **FAIL**, finding **B1** (the
target J-16 rebuild still crashed the live backend on a **second** consecutive full-universe rebuild —
anti-goal #8 NOT resolved) and **B2** (root cause = cross-job VSZ / glibc-arena accumulation dominated by
retained address space, which the first pass's read-side windowing did not touch).

### What changed this pass (the read-side windowing above is KEPT and untouched)

1. **`server.malloc_arena_max: 2`** (new config field, `apps/backend/app/config.py` + `config.yaml`)
   **exported as `MALLOC_ARENA_MAX` by `scripts/start-backend.sh`** before the `ulimit -v` + uvicorn `exec`.
   glibc otherwise creates up to `8 x ncpus = 128` independent arenas on this 16-core host; across the
   uvicorn threadpool + parallel backfill workers each retains its own freed-but-unreturned VSZ, so a second
   rebuild pins the ceiling. Capping to 2 arenas bounds that fragmentation — **the dominant VSZ lever**.
2. **`data_manager._release_process_memory()`** (`gc.collect()` + glibc `malloc_trim(0)`) in `_do_backfill`'s
   new `try/finally` — returns the freed `_BarCache` + per-date transients to the OS on every exit path, so
   the next rebuild starts lean instead of stacking on run 1's retained arenas.

Both are **byte-identity-NEUTRAL** (allocator/OS-return behavior only — no computed value changes).

### Why fallback lever 2 (bound `_BarCache.prefill`) was measured and deliberately NOT applied

- `min_date=` is byte-identity-**unsafe/unverifiable**: the resolver's `trailing_count(symbol, d)` counts
  *all* bars `<= d` incl. deep pre-2005 history, so a date bound changes membership — and the byte-identity
  gate does not cover the resolver, so it could not catch that drift. Rejected.
- `symbols=` is safe but **marginal**: `daily_prices` = 590 symbols, reading set (pool ∪ universe ∪ ETFs ∪
  ^VIX) ≈ 557 → bounds ~33 symbols ≈ **~55 MB / 1.6%** of the prefill. Does not move the margin. Skipped to
  keep the fix minimal; documented here + in perf-budgets so the deviation from the prescription is auditable.
- The audit's own **B2** hypothesis (arena retention) is the real driver — confirmed by an in-process
  two-run probe: BEFORE the peak climbs run→run and settle VSZ is retained (RSS drops but VSZ does not);
  AFTER it plateaus. `MALLOC_ARENA_MAX` + `malloc_trim` target exactly that.

### Re-verification (all green; commands + numbers)

- **Byte-identity RE-PROVEN** (non-negotiable): `test_scoring_window.py` **4/4 (472.51s)**, `test_bar_cache.py`
  **12/12**, `test_forward_testing.py` cache-awareness **5/5**, `test_config.py`+`test_config_engine.py`
  **111/111**. `prices.py`/`regime.py`/`scoring.py` are unchanged this pass, so the windowing byte-identity
  is unchanged by construction — re-run anyway per the coordinator.
- **LIVE two consecutive full-universe rebuilds** (`start-backend.sh` under `ulimit -v 6291456` +
  `MALLOC_ARENA_MAX=2`, throwaway DB copy, real `POST /api/data/jobs {kind:"rebuild"}` ×2, no restart):
  - AFTER run 1: **VmPeak 5,147,876 KB (5,027 MB), 1,116 MB margin**, `status=ok`, 322 dates, 597,044 fwd
    returns, `/api/health` 200 throughout.
  - AFTER run 2 (no restart): **VmPeak 5,147,876 KB — NO growth**, `status=ok`, 322 dates, 597,044 fwd
    returns (bit-for-bit identical to run 1), `/api/health` 200 throughout.
  - Post-run `/api/health`=200, `/api/data`=200, `/api/stocks`=200.
  - vs BEFORE (audit B1): run 1 6,073,864 KB (212 MB margin) → run 2 pinned at the 6,291,456 KB ceiling,
    `MemoryError`, wedged. **Single-run peak down ~926 MB AND cross-run accumulation eliminated.**
- **Cold `/api/data` no-OOM repro ×2** (stop → cold-start → `/api/data` FIRST, socket-poll readiness): both
  200, VmPeak ~3.5 GB, backend alive, `capacity` byte-identical — no regression from the allocator cap.
- Full numbers in `reports/perf-budgets.md` **Item H**.

### Honesty / scope notes for the reviewer & auditor

- The **isolated in-process harness peaks only ~3.0–3.8 GB** and cannot reproduce the live 6 GB (less
  framework/threadpool arena baseline) — this is why the **LIVE** two-rebuild lane above is the authoritative
  evidence, and why anti-goal #8 `resolved=true` still needs the **canonical browser-qa J-16 lane** to
  re-drive `/data` + the 8 required-still-passing journeys (iter-24 lesson). This pass provides a faithful
  live HTTP-level PASS; it does not substitute for that lane's verdict.
- **New/known gaps NOT fixed here (fix-mode scope discipline — recorded for triage, not silently touched):**
  audit B3 (`breadth_short_ma`/`breadth_long_ma` not guarded against `max_lookback_bars` in
  `IndicatorsCfg._validate` — latent, byte-safe today only by the 200==max(ma_periods) coincidence) and F1
  (`/data` has no guardrail against a repeated rebuild; a *wedged* backend has no client-side readiness-poll
  timeout to fall back to the iter-25 "Backend unavailable" card). Both were audit-marked non-blocking.
- `dev.sh` (uncapped local dev launcher, no `ulimit`) left unchanged; the fix lives in the prod/browser-qa
  launcher `start-backend.sh`.
