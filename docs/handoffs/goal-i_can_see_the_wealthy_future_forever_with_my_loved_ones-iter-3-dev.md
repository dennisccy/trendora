# goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-3 Dev Handoff

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-3
**Date:** 2026-06-11
**Agent:** developer
**Status:** complete

## What Was Built

J-46 — parallel bounded-worker fetch, per-chunk transactional writes, load-bars-once backfill, and a committed advisory benchmark. **Backend-only; zero new UI surface, zero new endpoint, zero new displayed value** (invisible-by-design: the same Data Manager experience, faster underneath).

- **`fetch_workers` config key** — new required typed field on `data_manager.import_chunking` (committed default **4**). Boot-validated `>= 1` (`1` = effectively serial, still valid; `0`/negative/missing ⇒ explicit `ConfigError`). No parallelism literal anywhere in `data_manager.py` — the pool size is read from config.
- **Parallel bounded-worker fetch** — `_run_chunked_fetch` now fans each chunk's symbol batch onto a bounded pool of `fetch_workers` threads. Workers do **network I/O only** (the existing `_fetch_symbol_with_retry` backoff + the polite `inter_request_sleep_seconds` per-worker delay); **all DB reads/writes and all `JobProgress` mutations stay on the orchestrating thread**. Every worker is joined/drained before the job thread returns (no thread outlives the job — the iter-28 `TestClient` determinism lesson).
- **Per-chunk single-transaction bar writes** — a chunk's new `(symbol, date)` rows are collected (idempotency via the existing `_existing_dates` guard) and written in **one INSERT + one `commit()` per chunk** (previously one commit per symbol). `_advance_checkpoint(next_idx=chunk_idx+1)` happens only **after** that commit, so `next_chunk_index` never points past undurable bars.
- **J-34 semantics intact under parallelism** — a worker exhausting `max_retries` on `RateLimitError` ⇒ the chunk's fetched bars are **discarded (chunk-atomic, nothing committed)**, the job + checkpoint go `resumable` with `next_chunk_index` at the **unfinished** chunk, and the loop returns gracefully (never raises, never fabricates). A non-429 `ProviderUnavailableError` for one symbol ⇒ counted failed with a **scrubbed** error (worker returns the raw error; the orchestrating thread scrubs before `_record_error`), the chunk continues. Resume re-attempts the unfinished chunk; prior committed chunks are skipped by `_existing_dates` (zero duplicate fetch).
- **Load-bars-once bar cache (Capability 33)** — an opt-in `prices.bar_cache(session)` context manager registers a per-session cache keyed by `id(session)`. While active, the first `bars_asof(symbol, D)` loads the symbol's **full stored series once** and every subsequent call slices `date <= D` **in memory** (byte-identical to today's date-bounded query — the `(symbol, date)` unique constraint means no ties). Activated around the read-only multi-date snapshot loops in **`data_manager._do_backfill`**, **`warmup._run_warmup`**, and **`scanner._bootstrap`** (`bootstrap_runs`). The default per-request read path (no active context) is **completely unchanged**; the cache dies with its `with` block (never outlives the job, never serves a stale series across a data-mutating stage).
- **Committed advisory benchmark** — `apps/backend/scripts/benchmark_pipeline.py`: offline (injected stub provider, no network/keys), prints per-stage timings (fetch serial vs pool; scan/snapshot per date uncached vs cached; forward returns) as a table + optional `--json`. Never imported by the test suite; no wall-clock CI assertion. Quotes the real baselines (~30–40 s per walk-forward scan; full suite ~34 min) in its docstring.

## Files Changed

- `config.yaml` — added `fetch_workers: 4` to `data_manager.import_chunking` (commented like its siblings).
- `apps/backend/app/config.py` — `fetch_workers: int` field on `ImportChunkingCfg` + `>= 1` boot validation; docstring updated.
- `apps/backend/app/engine/prices.py` — new `_BarCache`, the `_BAR_CACHES` registry, the `bar_cache(session)` context manager, and `bars_asof` consulting the active cache (default path unchanged).
- `apps/backend/app/engine/data_manager.py` — parallel `_run_chunked_fetch` (new `_SymbolFetchResult` / `_fetch_one_symbol` / `_fetch_chunk_symbols` helpers + `ThreadPoolExecutor` import), per-chunk single commit, checkpoint-after-commit, resumable chunk-atomic discard, worker-thread scrub on the orchestrating thread; bar-cache activation in `_do_backfill`.
- `apps/backend/app/engine/warmup.py` — bar-cache activation around the warm-up cadence `run_scan` loop.
- `apps/backend/app/engine/scanner.py` — bar-cache activation around the `_bootstrap` cadence `run_scan` loop.
- `apps/backend/scripts/benchmark_pipeline.py` — **NEW** advisory per-stage benchmark (offline; never imported by tests).
- `apps/backend/tests/test_bar_cache.py` — **NEW**: load-count instrumentation (≤ 1 bar-store load per symbol for a K-date job), cached-vs-uncached row-level snapshot equality, `<= D` slice correctness, default-path / lifetime / no-staleness.
- `apps/backend/tests/test_data_manager_parallel.py` — **NEW**: bounded fan-out, `fetch_workers: 1` serial-equivalence, one-INSERT-per-chunk, mid-chunk 429 no-partial-rows, parallel pause→idempotent resume (zero duplicate rows), scrubbed worker-thread errors, worker-exception no-strand.
- `apps/backend/tests/test_config.py` — `fetch_workers` in `MINIMAL_VALID` + four new validation tests (loads, `1` valid, `0`/negative raise, missing raises).
- `apps/backend/tests/test_config_engine.py`, `test_sectors.py`, `test_themes.py`, `test_indexes.py` — `fetch_workers: 4` added to each inline config dict (5 inline config literals total — see Known Issues; the project-memory note said "four", the real count today is five).

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -v` (run targeted modules in the foreground; full suite handed to the pump per session protocol)

Targeted + new results (all green, real numbers):
- `test_data_manager.py` — **68 passed** (all existing J-34 resumable / idempotency / expand / retry / dismiss contracts green unchanged under the parallel rewrite).
- `test_bar_cache.py` (NEW) — **8 passed** (incl. K=3 load-count ≤ 1/symbol; cached==uncached row-level equality).
- `test_data_manager_parallel.py` (NEW) — **7 passed** (bounded fan-out max_in_flight ≤ 4 & ≥ 2; one-INSERT-per-chunk; chunk-atomic 429 discard; parallel resume zero-dup; scrubbed errors; worker-exception no-strand).
- `test_config.py` — **37 passed** (incl. the 4 new `fetch_workers` validation tests).
- `test_no_magic_numbers.py`, `test_prices_asof.py`, `test_bars.py`, `test_regime.py`, `test_sectors.py`, `test_themes.py`, `test_asof_resolver.py` — **45 passed** (the no-magic-numbers scan over `prices.py` is green — the cache added no tunable literal; the `bars_asof` no-lookahead boundary tests pass unchanged).
- `test_scanner.py`, `test_forward_testing.py`, `test_warmup.py`, `test_scoring.py` — **78 passed** (the immutability + no-lookahead + walk-forward + cache-wrapped cadence suites all green unchanged; confirms the warm-up cache landed cleanly with no single-flight conflict).

**Targeted total: 243 passed, 0 failed** across all new and directly-affected modules (68 + 8 + 7 + 37 + 45 + 78).

**Full-suite run: RUN BY PUMP — GREEN.** `cd apps/backend && .venv/bin/python -m pytest tests/ -q` to completion: **659 passed, 4 skipped, 0 failed in 2760.91s (0:46:00)** (+20 vs iter-2's 639 — the new J-46 parallel/bar-cache/config tests; zero failures, zero regressions). The pre-fix pump run was 1 failed / 658 passed; the single failure was the cross-test-pollution assertion fixed below, and re-running the full suite post-fix is fully green.

**Targeted reproduction after the fix below is GREEN:** `cd apps/backend && .venv/bin/python -m pytest tests/test_data_manager.py tests/test_data_manager_parallel.py -q` → **75 passed, 0 failed** (this is the exact in-suite ordering that exposed the bug); the previously-failing test passes in isolation (`test_worker_exception_does_not_strand_job` → 1 passed).

The benchmark script was executed once offline end-to-end (`scripts/benchmark_pipeline.py --dates 1 --fetch-symbols 12`): Stage A showed the parallel pool win (serial 0.281 s vs pool 2.74× faster); Stage B/C ran clean.

## Known Issues

- **Bar-cache wall-clock crossover (advisory only).** The load-once cache loads each symbol's **full** series on first touch, whereas the uncached per-date query reads only the `<= D` prefix. So at a **small K** (e.g. K=1) the cache can be *slower* in wall-clock; its win grows with K as the full load amortizes. The deterministic J-46 evidence is the **load-COUNT** proof (≤ 1 bar-store load per symbol for the whole job — `test_bar_cache.py`), not the wall-clock ratio. The benchmark's Stage-B default K is set past the seed crossover and its docstring states this honestly.
- **Five inline config dicts, not four.** Project memory says a new required `import_chunking` field must be added to "all four" inline test config dicts; the real count in the suite today is **five** (`test_config.py`, `test_config_engine.py`, `test_sectors.py`, `test_themes.py`, `test_indexes.py`). All five were updated and verified to construct a valid `Config` with `fetch_workers=4`.
- **Pause semantics choice (documented per plan Assumption 3): discard.** On a mid-chunk persistent 429, the interrupted chunk's already-fetched bars are **discarded** (the chunk is committed entirely or not at all — chunk-atomic). Resume re-fetches the whole unfinished chunk; prior chunks are idempotent via `_existing_dates`. The `test_mid_chunk_429_leaves_no_partial_chunk_rows` test asserts exactly this (zero bars committed, `next_chunk_index` stays at the chunk, status `resumable`).
- **Warm-up cache landed (no escalation needed).** The plan flagged an escalation to fall back to `_do_backfill`-only if the warm-up cache conflicted with the iter-28 single-flight guard. No conflict exists — the single-flight guard serializes the warm-up *thread* in `start_warmup`; the cache only changes how that one thread's session loads bars. The cache was landed in `_run_warmup`, `_do_backfill`, and `_bootstrap`. (Final confirmation pending the `test_warmup.py` run handed to the pump alongside the full suite.)
- **No live-provider testing.** Per spec/scope, this iteration is data-walled — all tests use injected/offline stub providers (no network, no keys). The browser-QA legs (J-46 amber-resumable via `alpha_vantage`+`demo`, J-17 backfill, J-06 coherence) run on the live stack at QA time, not in this dev turn.
- **`snapshot_serving.py` untouched** — the reviewer's standing iter-2 `_http` alias note did not apply (no change to that module).

## Fix note (full-suite failure: cross-test thread pollution)

**Symptom (pump full-suite run, 1 failed / 658 passed / 4 skipped):** `tests/test_data_manager_parallel.py::test_worker_exception_does_not_strand_job` failed only on the FINAL assertion `assert not any(t.name.startswith("data-job-") and t.is_alive() for t in threading.enumerate())` → `assert not True`. The job under test settled correctly (`status == "failed"`, `finished_at` set — both prior asserts passed). Passes in isolation, fails in the full suite.

**Root cause (confirmed by reproduction, NOT a production bug):** that last assertion uses `threading.enumerate()`, which is **process-global** — it returns every live thread, including daemons spawned by EARLIER tests. `test_data_manager.py` has async tests (`test_expand_writes_to_overlay_not_committed_seed` via `start_data_job`, `test_retry_run_...` via `retry_run`) that run a job on a daemon thread named `data-job-{job_id}` and then poll only the job *status* (`while get_job(jid)["status"] == "running": sleep`). They break out of the poll loop the instant the status flips to a terminal value and **never `join()` the thread object** — so a `data-job-*` daemon can still be winding down (the gap between the last status write inside `run_data_job` and `Thread.run` actually returning) when a later test runs. The parallel test's global scan then catches that *foreign* leftover daemon. This test calls `run_data_job(...)` **synchronously** on the main thread, so it spawns no `data-job-*` thread of its own — its own worker pool uses `ThreadPoolExecutor`, whose `with` block already joins all workers on exit, including on the worker-exception path (`future.result()` re-raises, the `with` still joins). **No production thread is stranded.**

Reproduced deterministically: `pytest tests/test_data_manager.py tests/test_data_manager_parallel.py -q` → `1 failed` (`assert not True`) before the fix; the same command → `75 passed` after.

**Fix (option 1 — scope the assertion to this call's own threads; intent preserved, zero production change):** before calling `run_data_job`, snapshot the ids of any pre-existing `data-job-*` threads, then assert that no `data-job-*` thread that is **new since the call** remains alive. This still proves THIS job's worker/job threads were joined before `run_data_job` returned on the exception path, while being robust to foreign daemons left winding down by earlier async tests. No production code was changed — `app/engine/data_manager.py`'s `with ThreadPoolExecutor(...)` already guarantees the pool join on every path.

**File changed by this fix:** `apps/backend/tests/test_data_manager_parallel.py` — `test_worker_exception_does_not_strand_job` only (snapshot-before / new-threads-only assertion).

## Suggested Next Phase

J-47 (the final lean iteration): the ≥ 100-term config-backed glossary on `/methodology` + inline info-tooltips on the dense pages' column headers / stat labels, reading the same catalog mechanism as the existing setup/pattern catalog. It is the last remaining journey and is UI-bearing (frontend present), so it returns to a normal lean build with browser QA on `/methodology` and the tooltip surfaces.
