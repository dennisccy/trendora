# goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-3 Execution Plan

J-46: parallel bounded-worker fetch, per-chunk transactional writes, load-bars-once backfill, committed advisory benchmark. Backend-only code change; zero new UI surface ("invisible-by-design" — same Data Manager experience, faster underneath). Realizes goal.md Capabilities 33 + 38 and the "Fetch + backfill are materially faster" success criterion. No scope drift detected against docs/goal.md.

**RESUMED ITERATION — verify, do not rebuild.** iter-3 was interrupted mid-pipeline AFTER the implementation finished. The working tree already contains the complete J-46 change set with a recorded full-suite GREEN run (**659 passed / 4 skipped / 0 failed, ~46 min**), and the dev handoff exists at `docs/handoffs/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-3-dev.md`. The developer step on this re-run is verification/confirmation against the spec (touch-ups at most — e.g. the benchmark docstring quotes the old ~34 min baseline where the spec now says ~46 min); reviewer, QA, auditor, and evaluator proceed normally over the existing diff. A second full-suite run is needed ONLY if the diff changes after the recorded green run.

## What to Build

(All items below are ALREADY IMPLEMENTED per the dev handoff — listed as the verification contract.)

- **`fetch_workers` config key** in `config.yaml` `data_manager.import_chunking` (committed default 4) + typed field on `ImportChunkingCfg` in `apps/backend/app/config.py`, boot-validated positive int `>= 1` (`ConfigError` on 0/negative/missing — matching the block's existing validations). No parallelism literal anywhere in `data_manager.py`. Key present in **all FIVE** inline test config dicts: `tests/test_config.py`, `tests/test_config_engine.py`, `tests/test_sectors.py`, `tests/test_themes.py`, `tests/test_indexes.py` (project memory said four; the real count is five — all five verified updated).
- **Parallel bounded-worker fetch** in `data_manager._run_chunked_fetch` (was serial per-symbol loop with per-symbol commit): each chunk's symbol batch fans onto a pool of `fetch_workers` threads, each worker running only the existing `_fetch_symbol_with_retry` (network I/O; `inter_request_sleep_seconds` honored as the per-worker polite delay). **All DB reads/writes and all `JobProgress` mutations stay on the orchestrating thread.** Workers fully joined/drained before the job thread returns (iter-28 lesson: no thread outlives the job or breaks `TestClient` determinism).
- **Per-chunk single-transaction bar writes**: chunk's new rows collected (idempotency via the existing `_existing_dates` guard), one INSERT + one `commit()` per chunk; `_advance_checkpoint(next_idx=chunk_idx+1)` only after that commit, so `next_chunk_index` never points past undurable bars.
- **J-34 semantics intact under parallelism**: a worker exhausting `max_retries` on `RateLimitError` ⇒ drain remaining workers, job + checkpoint `resumable` with `next_chunk_index` at the unfinished chunk, graceful return (never raise, never fabricate). Implemented pause semantics (developer's documented choice): **chunk-atomic discard** — the interrupted chunk commits entirely or not at all; Resume re-fetches the unfinished chunk with zero duplicate `(symbol, date)` rows (prior chunks skipped via `_existing_dates`). Non-429 `ProviderUnavailableError` ⇒ failed count + **scrubbed** error (worker-thread exceptions scrubbed on the orchestrating thread before `_record_error` — httpx errors embed `?apikey=`), chunk continues. Progress counters reflect committed reality and never exceed totals.
- **Load-bars-once bar cache (Capability 33)** at the single `prices.bars_asof` seam: opt-in `prices.bar_cache(session)` context manager (no engine signature churn for the call sites in `scoring.py`/`regime.py`/`sectors.py`/`themes.py`). First request per symbol loads the full stored series once; subsequent `bars_asof(symbol, D)` slices ≤ D in memory, preserving today's ordering/contents exactly. Activated around the multi-date snapshot loops in `data_manager._do_backfill`, `warmup._run_warmup`, AND `scanner._bootstrap` (landed cleanly — no conflict with the iter-28 single-flight guard, so the spec's backfill-only escalation was not needed). Default per-request read path unchanged; the cache dies with its `with` block and is never active across a data-mutating stage.
- **Instrumented load-count test**: K-date (K ≥ 3) backfill over seed data with counting instrumentation at the bar-store load point asserts ≤ 1 load per symbol for the whole job (vs ≥ K before).
- **Pure-refactor proof**: all existing scanner/scoring/forward-testing/immutability/no-lookahead/warmup suites pass unchanged, plus a direct row-level cached-vs-uncached snapshot equality test on a sample date.
- **Committed advisory benchmark** `apps/backend/scripts/benchmark_pipeline.py`: offline (injected stub provider, no network/keys), reports per-stage timings (fetch serial vs pool; scan/snapshot per date cached vs uncached; forward returns) as a printed table + optional JSON. Never imported by the test suite; no wall-clock CI assertion. Docstring quotes real baselines (~30–40 s per walk-forward scan; full suite **~46 min** — verify/refresh, the pre-interruption docstring said ~34 min).
- **Contract regression tests under parallelism** (injected stub providers; `seed_import` offline source; established `test_data_manager.py` patterns): bounded fan-out, per-chunk single commit, mid-chunk 429 ⇒ resumable + idempotent Resume, scrubbed errors, progress never exceeds totals, J-37 pull-the-gap and J-38 Retry-remaining ride the rewired loop unchanged.

## Agents Required

- developer: yes -- VERIFY the completed implementation against the spec (touch-ups at most, e.g. the benchmark docstring baseline figure); do NOT re-implement; re-run the full suite only if the diff changes
- backend-data: yes -- (same scope as developer; this iteration is entirely backend pipeline work)
- frontend-ux: no -- zero frontend file changes; `tsc --noEmit` only if an incidental frontend file is touched

## Frontend Present
yes

Rationale (documented decision, gating-only): the spec's metadata block says "Frontend Present: no", but its DEFINITION OF DONE explicitly requires browser QA — "J-17 + the J-34 resumable surface via browser QA" and "J-06 spot-checked in the browser" — and qa-phase.sh hard-skips browser checks when this line is "no". The parallel rewrite changes the runtime behavior of user-visible surfaces (live progress accuracy, the amber resumable pause, Resume) even though no frontend file changes, so browser regression must run. Marking yes here only forces those required checks; it does not imply UI work.

## Files to Create/Modify

(Already changed in the working tree — listed for reviewer/QA orientation.)

- `config.yaml` -- `fetch_workers: 4` added to `data_manager.import_chunking` (commented like siblings)
- `apps/backend/app/config.py` -- `fetch_workers: int` on `ImportChunkingCfg` + `>= 1` boot validation
- `apps/backend/app/engine/data_manager.py` -- parallel `_run_chunked_fetch` (`_SymbolFetchResult` / `_fetch_one_symbol` / `_fetch_chunk_symbols` + `ThreadPoolExecutor`), per-chunk single commit, checkpoint-after-commit, chunk-atomic resumable discard, orchestrating-thread scrub; bar-cache activation in `_do_backfill`
- `apps/backend/app/engine/prices.py` -- `_BarCache`, `_BAR_CACHES` registry, `bar_cache(session)` context manager; `bars_asof` consults the active cache (default path unchanged)
- `apps/backend/app/engine/warmup.py` -- bar-cache activation around the warm-up cadence `run_scan` loop
- `apps/backend/app/engine/scanner.py` -- bar-cache activation around the `_bootstrap` cadence loop
- `apps/backend/scripts/benchmark_pipeline.py` -- NEW advisory per-stage benchmark (offline; never imported by tests)
- `apps/backend/tests/test_data_manager_parallel.py` -- NEW: parallel-contract regression tests (7 passed)
- `apps/backend/tests/test_bar_cache.py` -- NEW: load-count instrumentation + cached-vs-uncached snapshot equality (8 passed)
- `apps/backend/tests/test_config.py` -- `fetch_workers` in `MINIMAL_VALID` + `VALID` + 4 validation tests (0/negative/missing ⇒ `ConfigError`)
- `apps/backend/tests/test_config_engine.py`, `test_sectors.py`, `test_themes.py`, `test_indexes.py` -- `fetch_workers: 4` added to each inline config dict

## UI Evolution (regression-only — no UI change this iteration)

- New user-facing capability: none in the UI. Fetch/backfill jobs complete materially faster with the same honest live progress; the benchmark script is operator-facing terminal output only.
- New information displayed: none.
- New user actions: none.
- UI surface changes: none — Data Manager (`/data`) live progress, amber resumable state, and Resume are unchanged surfaces whose backend got faster; they must be regression-verified in the browser.
- Navigation changes: none.

## Visual Requirements (regression-only)

- Component patterns: none new — existing `/data` job cards / progress / Resume controls untouched.
- Layout: unchanged.
- Key visual effects: none new.
- States to handle: the existing amber "rate-limited — resumable" state and live progress counts must remain accurate (counts never exceed totals) under parallel fetching — verified, not redesigned.

## Key Test Scenarios

- `fetch_workers: 0` / negative / missing ⇒ explicit `ConfigError` at boot; valid `1` ⇒ effectively serial, still valid.
- Stub-provider fan-out: max concurrent in-flight fetches ≤ `fetch_workers`; a worker exception never deadlocks the pool or strands the job in `running`; all workers joined before the job thread finishes.
- Per-chunk single commit (one-INSERT-per-chunk; chunk-atomic 429 discard ⇒ no partial-chunk rows, per the implemented pause semantics).
- Mid-chunk persistent 429 ⇒ `resumable` (never `failed`), chunk-consistent checkpoint, progress counters ≤ totals; Resume continues from checkpoint with **zero duplicate `(symbol, date)` rows**.
- Non-429 provider error ⇒ failed count + scrubbed message; grep the **job-status payload** to assert the key string is absent (worker-thread scrub).
- Instrumented K≥3-date backfill ⇒ ≤ 1 bar-store load per symbol for the whole job (vs ≥ K before).
- Cached-vs-uncached snapshot equality: row-level identical canonical outputs for a sample date; all existing scanner/forward-returns/immutability/no-lookahead/warmup suites pass **unchanged**.
- Benchmark script runs offline end-to-end and prints the stage-timing table (already executed once: serial vs pool 2.74× on Stage A).
- Full backend pytest: **already recorded GREEN — 659 passed / 4 skipped / 0 failed in ~46 min.** Re-run ONCE to completion only if the diff changes; never two concurrent invocations (shared session DB + warm-up determinism).
- Browser (running stack :8835/:3835 — **never self-restart the backend**): J-46 steps 1–2 on `/data` via source=alpha_vantage + key `demo` (throttle ⇒ amber **rate-limited — resumable** in ~3 min; live progress accurate; Resume continues with no duplicate fetch); J-17 small seed-range backfill-only job to an `ok` summary; J-06 NVDA scores/buckets identical on `/stocks` and `/stocks/NVDA`. Dead un-hydrated shell ("Checking backend…", 404 on `_next/static/...`) ⇒ record SKIPPED, not FAIL. Never run the destructive `POST /api/data/remove` against a real symbol — preview endpoint only (NVDA carries unrestorable user-added bars).

## Out of Scope (excluded; flag if attempted)

J-47 glossary (next, final lean iteration); any live-network provider fetch (tests use injected/offline providers only); process pools / asyncio / parallelizing the scan compute itself (scan stays single-writer, sequential per date); changing existing `import_chunking` semantics or committed defaults beyond adding `fetch_workers`; any checkpoint schema/ID change that would orphan existing `import_checkpoints` rows; Capability 34 (precomputed snapshot seed); any `/data` UI redesign or new endpoint; **re-implementing or reworking the already-completed, full-suite-green J-46 changes**.

## Assumptions (documented, not asked)

1. Default `fetch_workers: 4` (spec suggests "e.g. 4") — already committed as 4.
2. Bar-cache shape: context-manager at the `prices.bars_asof` seam (no engine signature churn) — already implemented as `prices.bar_cache(session)` with an `id(session)`-keyed registry; default per-request path byte-identical, cache cannot outlive the job.
3. Pause semantics for the interrupted chunk: **discard (chunk-atomic)** — the developer's documented choice within the spec's fixed invariants, stated in the dev handoff and matched by `test_mid_chunk_429_leaves_no_partial_chunk_rows`.
4. `snapshot_serving.py` untouched — the reviewer's standing iter-2 `_http` alias note does not apply.
5. The "Frontend Present: yes" line is a QA-gating decision only (see rationale above); no frontend work is planned and the UI/Visual sections above are regression-scoped.
6. The recorded full-suite green run (659/4/0, post-fix) stands as the suite evidence for this iteration unless any agent changes the diff, in which case exactly one fresh full-suite run is required before close.
