# goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-42 Dev Handoff

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-42
**Date:** 2026-06-20
**Agent:** developer
**Status:** complete

## What Was Built

J-100 — bounded-resource backend hardening for the `compute_coverage` / membership-timeline read path.
A **pure performance/stability** change: every served `coverage` / `membership_timeline` /
`universe_diagnostic` value stays **byte-identical**. Backend-only; no frontend diff; no payload key added;
no new table; no canonical value, regime, membership, or `_dataset_version` touched.

- **(a) Single-flight + result cache around `compute_coverage`.** Concurrent `/api/data` callers for the
  SAME resolved as-of + membership stamp now share ONE heavy computation: the first caller computes, the
  rest WAIT on a per-key event and return the SAME cached payload. **K=12 concurrent probes → exactly 1
  heavy compute** (verified). Reuses the warm-up controller's lock idiom (no new abstraction). This is the
  documented pool-exhaustion / VM-freeze fix: N parallel probes no longer cost N connection-holding ~8s
  resolves.
- **(b) Membership-specific dataset stamp (`research._membership_dataset_version`).** The membership cache
  key now depends ONLY on membership's real inputs — `max(scanner_runs.id)` + `count(scanner_runs)` + the
  bars manifest (`max(daily_prices.date)` + `count(daily_prices)`) + `indicators.min_history_bars` — and
  NOT on the `forward_returns` row count. So a warm-up forward-return insert NO LONGER invalidates the
  membership cache (the recompute storm is eliminated), while a real snapshot add/remove or a bar backfill
  still correctly refreshes it. `research._dataset_version` (the J-72/J-87 event-study/market-phase stamp)
  is **UNCHANGED** — only the membership cache adopts the narrower stamp.
- **(c) Reused one process-level bar cache for the read path.** The whole coverage derivation now runs
  inside ONE shared `prefilled_bar_cache`, so `_resolved_universe`'s `resolve_with_reasons` and the
  membership cold-compute read from a single once-loaded copy of every symbol's series (memory bounded to
  one copy regardless of concurrency). The iter-37 J-46 load-once-per-job invariant is preserved
  (zero-bar candidates recorded as empty series up front; `test_bar_cache.py` load-COUNT test stays green).
- **(d) Ops guards in `scripts/start-backend.sh`.** Added uvicorn `--limit-concurrency` /
  `--timeout-keep-alive` / `--timeout-graceful-shutdown` and a `ulimit -v` process memory cap — **every
  value read from `config.server`** (no magic literal in the script; env overrides `CHAIN_SERVER_*` win).
  The light endpoints (`/health`) stay responsive under a heavy `/api/data` burst; a pathological memory
  spike is OOM-killed as ONE process, never a VM-wide swap freeze.
- **(e) Test hygiene codified** (see "Test Hygiene Note" below): `/api/data` is single-loaded, never
  concurrently probed in normal QA; the new concurrency load test is the ONE sanctioned concurrent probe.

## Files Changed

- `apps/backend/app/engine/research.py` -- ADD `_membership_dataset_version(session, config)` (the narrow
  membership-cache stamp); `_dataset_version` left UNCHANGED. Imported `DailyPrice`.
- `apps/backend/app/engine/data_manager.py` -- `membership_timeline_cached` adopts the narrow stamp;
  `compute_coverage` is now a single-flight + result-cache wrapper (`_compute_coverage_uncached` runs the
  derivation inside one shared `prefilled_bar_cache`; `_compute_coverage_body` is the split-out body);
  added `_coverage_cache_key` / `_config_fingerprint` / `_db_identity` / `reset_coverage_cache`. Imported
  `copy`, `hashlib`, `_membership_dataset_version`.
- `apps/backend/app/engine/warmup.py` -- comments updated: the membership cache is warmed under the narrow
  stamp (independent of the forward-return backfill, so the warmed row stays valid). No behavior change.
- `apps/backend/app/config.py` -- ADD `ServerOpsCfg` (uvicorn concurrency/timeout caps + `memory_cap_mb`),
  wired into `Config.server` with a default factory (a config/test fixture predating it still loads).
- `config.yaml` -- ADD the `server:` block (limit_concurrency 64, timeout_keep_alive_seconds 65,
  graceful_timeout_seconds 120, memory_cap_mb 6144).
- `scripts/start-backend.sh` -- read the four bounds from `config.server` via the venv python; apply
  `ulimit -v` + the three uvicorn flags (env-overridable, no magic literal).
- `apps/backend/tests/test_data_manager_concurrency_load.py` -- NEW: the concurrency load test (3 tests).
- `apps/backend/tests/test_data_manager_membership_cache.py` -- the FR-insert test now asserts the cache is
  NOT invalidated (the J-100 decoupling); ADD a bar-backfill-DOES-invalidate test; row-version asserts use
  the narrow stamp.
- `apps/backend/tests/test_warmup.py` -- the warmed-cache row-version assert uses the narrow stamp.

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -q` (split into targeted modules locally;
full suite handed to the pump nohup-async per the standing GREEN-suite gate).

Local results (each via nohup detached to survive the harness wrapper-kill on this multi-run host):
- `test_data_manager_membership_cache.py` + `test_data_manager_concurrency_load.py` — **12 passed, EXIT 0**
- `test_config.py` + `test_bar_cache.py` + `test_db.py::test_create_all_produces_expected_tables` +
  `test_api_data.py` (overview/availability shape) — **69 passed, EXIT 0**
- `test_data_manager.py -k "coverage or availability or diagnostic or universe or resolved or per_symbol or
  membership"` — **21 passed, EXIT 0**
- `test_warmup.py` — running via nohup at handoff time (seed-boot heavy; the warmed-cache assertion was
  updated to the narrow stamp). **The full pytest suite (`0 failed, EXIT 0`) is the pump's nohup-async
  gate** — the evaluator must read the FLUSHED terminal line, not the in-flight stream.

Single-flight COUNT proof (instrumented run): **K=12 concurrent `compute_coverage` calls → 1 heavy
`_compute_coverage_uncached` call**, max latency 0.142s, byte-identical payloads.

## Test Hygiene Note (scope (e))

- **`/api/data` is SINGLE-LOADED, never concurrently probed in normal QA** (the MEMORY pool-exhaustion
  lesson). One `/api/data` holds a DB connection ~10s; the pool is size 5 + overflow 10. The single-flight
  (a) is what makes the load test's K concurrent probes safe — **the concurrency load test is the ONE
  sanctioned concurrent probe.** Wait ~30s for `/data` hydration; load it ONCE.
- For the long nohup full suite on this 1369/1371-date host, export `CHAIN_PUMP_HEARTBEAT_TIMEOUT` /
  `CHAIN_DISPATCH_INFLIGHT_TIMEOUT` generously and run a `.pump-alive` toucher tied to the engine pid; run
  the suite via `nohup bash -c '...' &` so it outlives any wrapper-kill (iter-29/35→37 lessons).
- Re-run any single `test_warmup.py` / `test_data_manager_jobs_pipeline.py` `F` in ISOLATION before calling
  it a regression — those are the documented scanner_runs-race / slow-boot / warm-up-contention flakes.

## Known Issues

- **Full backend pytest suite is ~3.5h on this host** (1369/1371 seed dates, heavy walk-forward boot). It
  cannot finish under a subagent Bash cap, so it is handed to the pump nohup-async (the standing
  GOAL_ACHIEVED gate). Local verification used targeted fast (no-boot) modules + the new load test; the
  `test_warmup.py` seed-boot legs were launched via nohup.
- **Live backend start was NOT performed in this dev turn** to avoid triggering the heavy seed-boot
  warm-up daemon on the shared host (MEMORY: slow-boot + concurrency lessons). The start-script change was
  verified by a non-serving dry-run: the config read returns `limit=64 keepalive=65 graceful=120
  memMB=6144`, `ulimit -v` applies cleanly to `6291456 KiB`, the env overrides (`CHAIN_SERVER_*`) win, and
  uvicorn supports all three flags (`--help` confirmed). The QA step should do the live `/data` re-verify.
- **Browser-QA auto-skip risk (iter-36/39):** `Frontend Present: no`, but the required-still-passing
  journeys (J-94/J-96/J-93 + the Dashboard cluster) are RENDERED pages and the whole point is to prove no
  served value changed. The QA/browser-qa step MUST explicitly run the live `/data` + Dashboard re-verify;
  do NOT mark any required journey "still passing" on API-layer byte-identity alone. If the framework
  auto-skips on the `no` flag, a lean live re-verify follows next iter (the iter-36→37 pattern). Plan the
  Playwright fallback up front (Chrome MCP CDP has emptied the evidence dir on iters 38/39/40).
- **`ulimit -v` is a soft-lowering only** — it cannot exceed a stricter inherited hard cap; if the host
  already enforces a lower cap the script keeps it (`|| true`) rather than failing the start. On this host
  the 6144MB cap applied cleanly.
