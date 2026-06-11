# Goal Iteration 3 — J-46: parallel bounded-worker fetch, per-chunk transactional writes, load-bars-once backfill, committed benchmark

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** i_can_see_the_wealthy_future_forever_with_my_loved_ones
- **Iteration:** 3
- **Mode:** normal
- **Depth:** full
- **Frontend Present:** no
- **Target journeys:** J-46
- **Required-still-passing journeys:** J-06, J-17, J-34, J-36, J-37, J-38, J-39, J-40, J-41
- **Anti-goal reminders:**
  - **No lookahead.** "Scoring for a snapshot dated D MUST use only price bars with date ≤ D; forward returns MUST use only bars with date > D. The walk-forward MUST be unit-tested to prove no future bar influences an as-of score." *(critical — the load-once bar cache must slice ≤ D exactly like `bars_asof` does today)*
  - **Snapshots are immutable.** "A persisted `scanner_run` and its result rows MUST never be updated or overwritten after creation; forward returns live in a separate append-only table keyed to the snapshot." *(critical)*
  - **On-demand snapshots stay immutable & lookahead-free.** "Creating a snapshot for a newly selected date is create-once: an existing snapshot MUST be read, never overwritten; an as-of-D snapshot MUST use only bars with date ≤ D." *(critical)*
  - **Single source of truth.** "Each of the six canonical scores (and the A–E bucket and setup status) MUST be computed exactly once by the scoring/regime engine and read identically by every page." *(critical — the vectorized refactor must produce byte-identical canonical outputs)*
  - **No fabricated data.** "On a data-provider failure the system MUST surface an explicit stale/unavailable state and MUST NOT synthesize prices or scores to force a green journey." — a rate-limited worker pauses resumable; it never invents a bar.
  - **No magic numbers.** "Every scoring weight, threshold, decision-rule cutoff … MUST come from the config file" — applied here to the worker-pool size: it lives in `config.yaml`, never a literal in `data_manager.py`.
  - **No secrets in source.** "any live-provider key is read only from the environment" — and the existing key scrubber MUST keep redacting errors raised on worker threads (httpx errors embed the full URL incl. `?apikey=`).

## GOAL

Multi-symbol fetch jobs run on a bounded, config-set parallel worker pool with per-chunk single-transaction bar writes, and a multi-date backfill loads each symbol's bars once for the whole job — measurably faster (committed advisory benchmark) while every canonical output and every J-34/J-37/J-38 import contract stays byte-identical.

## BACKGROUND

The iter-2 evaluator (CONTINUE) explicitly recommended J-46 next at **full** depth: this iteration rewires the concurrency-sensitive import pipeline under multiple critical contracts (resumable/checkpoint semantics, SQLite write safety, snapshot immutability, no-lookahead) where a subtle corruption would be invisible to browser QA — the full pipeline's reviewer + auditor steps earn their cost here. The pre-iteration code was strictly serial: `data_manager._run_chunked_fetch` fetched one symbol at a time and committed **per symbol** (line ~1129), and `_do_backfill` / `warmup._run_warmup` call `scanner.run_scan` per date, where every engine (`score_regime`, `score_sectors`, `score_themes`, `score_stocks`) re-queries `prices.bars_asof(session, symbol, d)` per symbol **per date** — for a K-date job each symbol's history is loaded K+ times. J-46 registers NO new displayed value; the blueprint's Import-job-control row already carries the J-46 TARGET clause (annotated with the concrete names below). J-47 (glossary) follows as the final lean iteration.

**RESUMED ITERATION:** iter-3 was interrupted mid-pipeline (the dev dispatch hit the 2h in-flight timeout while the pump ran the full suite) and is re-running from the top. The J-46 implementation is **ALREADY COMPLETE and full-suite GREEN (659 passed / 4 skipped / 0 failed)** in the working tree: `fetch_workers` in root `config.yaml` + `app/config.py`, parallel pool + per-chunk commits in `data_manager.py`, bar cache in `prices.py` consumed by `scanner.py`/`warmup.py`, new suites `test_data_manager_parallel.py` + `test_bar_cache.py`, benchmark script `apps/backend/scripts/benchmark_pipeline.py`, dev handoff written. Downstream steps must **verify the existing work against this spec, not re-implement it** — the developer step confirms/touches up at most; reviewer, QA, auditor, and evaluator proceed normally on the existing diff.

**Lessons applied (episodic memory, verbatim from session state):**
- Full backend pytest now takes **~46 min** (659 passed / 4 skipped / 0 failed baseline including the new J-46 suites). Budget accordingly, run it **ONCE to completion**, NEVER two concurrent invocations. A subagent cannot finish it (10-min Bash cap + background processes die on turn-end) — the dev runs targeted modules and hands the full suite to the pump.
- **Config fixture rule (updated):** a new required typed config field must be added to **ALL FIVE** inline test config dicts — `tests/test_config.py`, `tests/test_sectors.py`, `tests/test_themes.py`, `tests/test_config_engine.py`, `tests/test_indexes.py` (all five verified to contain `fetch_workers` in the completed work).
- **httpx error leaks URL query key:** `str(httpx.HTTPStatusError)` embeds the full URL; the `_make_scrubber` redaction must wrap errors raised on worker threads too — grep the job-status response for the key in tests.
- The iter-28 warm-up fix added a **single-flight guard + conftest pre-warm** to keep `TestClient` determinism — the new parallel/vectorized code must not spawn background threads that outlive the job or re-break API-test determinism (workers must be joined before the job thread finishes).
- ESLint is not installed; `tsc --noEmit` is the frontend gate — moot here (no frontend change planned).
- If this iteration touches `app/engine/snapshot_serving.py`, export a public alias for `snapshot_serving._http` (reviewer's standing note from iter-2).

## IN SCOPE

### Backend

- [ ] **New config key — worker pool size.** Add `fetch_workers` to `data_manager.import_chunking` in `config.yaml` (committed default **> 1**, e.g. 4) and to `ImportChunkingCfg` in `apps/backend/app/config.py` with boot validation (positive int; `fetch_workers >= 1`; 1 = effectively serial, still valid). No worker/parallelism literal anywhere in `data_manager.py`. **Add the key to all five inline test config dicts** (see lesson above).
- [ ] **Parallel bounded-worker fetch in `data_manager._run_chunked_fetch`.** Within each chunk, fetch the symbol batch on a bounded pool of `fetch_workers` threads (each worker runs the existing `_fetch_symbol_with_retry` backoff; `inter_request_sleep_seconds` stays honored as the polite per-worker delay). **All DB reads/writes stay on the orchestrating thread** — workers only do network I/O and return bars; SQLite writes remain serialized/transactional.
- [ ] **Per-chunk single-transaction bar writes.** Collect the chunk's new rows (per-`(symbol, date)` idempotency via the existing `_existing_dates` guard) and INSERT + `commit()` **once per chunk** — not per symbol. The durable checkpoint advance (`_advance_checkpoint` to `next_chunk_index = chunk_idx + 1`) happens only after that chunk's commit, so `next_chunk_index` never points past a chunk whose bars are not durably committed.
- [ ] **J-34 semantics intact under parallelism.** A worker exhausting `max_retries` on `RateLimitError` ⇒ drain/cancel the remaining workers, set job + checkpoint `resumable` with `next_chunk_index` at the **unfinished** chunk, and return gracefully (never raise, never fabricate). Whether the successfully fetched symbols of the interrupted chunk are committed before pausing or discarded is the developer's choice, BUT the invariants are fixed: the checkpoint is chunk-consistent, progress counters reflect committed reality and **never exceed totals**, and Resume re-attempts the unfinished chunk with **no duplicate fetch of committed bars** (idempotency via `_existing_dates`). A non-429 `ProviderUnavailableError` for one symbol ⇒ counted failed with a **scrubbed** error, the chunk continues — unchanged semantics.
- [ ] **Thread-safe live progress.** `JobProgress` counter/message updates from the orchestrating thread only (or behind the existing lock); the progress message stays accurate and monotone under parallel fetching (J-46 step 1: "live progress stays accurate").
- [ ] **Load-bars-once vectorized backfill (Capability 33).** Introduce a per-job bar cache at the single `prices.bars_asof` seam (explicit opt-in context, e.g. `prices.bar_cache(session)` / a cache object threaded through): the first request for a symbol loads its **full stored series once**, and every subsequent `bars_asof(symbol, D)` within the job slices ≤ D **in memory** (preserving today's ordering and contents exactly). Activate it in `data_manager._do_backfill` and `warmup._run_warmup` (and `scanner.bootstrap_runs` if trivially compatible) — multi-date job loops only. The default per-request read path is **unchanged**; the cache never outlives its job (no staleness across data-mutating jobs; fetch jobs that add bars never serve stale cached series).
- [ ] **Instrumented load-count test.** A test that runs a K-date (K ≥ 3) backfill over seed data with counting instrumentation at the bar-store load point and asserts **at most one bar-store load per symbol for the whole job** (vs ≥ K before).
- [ ] **Pure-refactor proof — identical canonical outputs.** The existing scanner / scoring / forward-testing / immutability / no-lookahead suites pass **unchanged** (same scores/buckets/returns). Additionally assert directly that a snapshot computed through the bar cache equals the snapshot computed through the uncached path for the same date (row-level equality on a sample date).
- [ ] **Committed advisory benchmark script** at `apps/backend/scripts/benchmark_pipeline.py`: runs offline against the committed seed (injected/offline provider for the fetch stage — no network, no keys) and reports per-stage timings — fetch (serial vs `fetch_workers` pool), scan/snapshot per date (cached vs uncached), forward returns. Output is a printed table + optional JSON; **advisory evidence only** — it is never imported by the test suite and no wall-clock assertion gates CI. Quote the real baseline figures (~30–40 s per walk-forward scan; full suite ~46 min) in its README/docstring for context.
- [ ] **Contract regression tests under parallelism** (injected stub providers returning bars or raising 429): resumable pause mid-chunk is chunk-consistent; Resume continues from the checkpoint with zero duplicate `(symbol, date)` rows; per-chunk single-commit verified (e.g. commit-count spy or asserting no partial-chunk rows after an injected mid-chunk failure, per the chosen pause semantics); progress counts never exceed totals; key never appears in job `errors[]` (worker-thread scrub); J-37 pull-the-gap and J-38 Retry-remaining ride the same rewired loop unchanged.

### Frontend

None. No UI change — the Data Manager surfaces (live progress, amber resumable state, Resume) are unchanged; only their backend gets faster. (`tsc --noEmit` not required unless an incidental frontend file is touched.)

### New user-facing capability

Nothing new to click — fetch and backfill jobs complete materially faster with the same honest live progress, and a committed benchmark script lets the operator measure the pipeline's per-stage speed on the seed at any time.

### New information displayed

None in the UI. The benchmark script's stage-timing table is operator-facing terminal output (advisory).

### New user actions

None.

### UI surface changes

None. No new pages, panels, or nav entries.

### Product surface delta

Invisible-by-design: same Data Manager experience, faster pipeline underneath. The only experiential change is shorter job durations and (unchanged) accurate progress under parallel fetching.

### Blueprint conformance

No new surfaces. J-46 is registered in the blueprint as cross-cutting ("backend pipeline speed (no UI surface; advisory benchmark script)") and as the TARGET clause on the **Import job control** Data-Contract row — this iteration builds exactly that clause. The blueprint row has been additively annotated with the concrete names (config key `data_manager.import_chunking.fetch_workers`, per-chunk transactional commit in `data_manager:_run_chunked_fetch`, load-once bar cache at the `prices:bars_asof` seam consumed by `_do_backfill`/`warmup`, benchmark script `apps/backend/scripts/benchmark_pipeline.py`). Flip the TARGET tag to built only after the evaluator verifies.

### Data-contract additions

**None.** J-46 introduces no new displayed value. Do NOT add a second compute/serve path for any registered value: bar writes keep going through the one import engine (`data_manager`), snapshots keep being created only by `scanner.run_scan` (create-once, immutable), and the bar cache is a *loading* optimization beneath the registered engines — it must never become a second source of bar truth (it reads the same `daily_prices` rows and dies with the job).

## OUT OF SCOPE

- **J-47** (≥100-term glossary + inline header tooltips) — the next, final lean iteration. Do not start it here.
- Any **live-provider fetch** against a real network source (data-walled; J-22/J-23/J-24 remain blocked-NA, non-halting). Tests use injected/offline providers only.
- Process pools, asyncio rewrites, or parallelizing the **scan/backfill compute** itself — J-46 requires a bounded *thread* pool for fetch I/O and a load-once cache for backfill; the scan stays single-writer and sequential per date.
- Changing existing `import_chunking` semantics or committed defaults (batch size, windows, retries, backoff) beyond adding `fetch_workers`.
- Any change to checkpoint schema/IDs that would orphan existing `import_checkpoints` rows.
- Capability 34 (precomputed snapshot seed accelerator) — separate concern, not this journey.
- Any UI redesign of `/data`; any new endpoint.
- Running the destructive `POST /api/data/remove` live against a real symbol during QA (NVDA carries unrestorable user-added bars — use the **preview** endpoint + suite, per project memory).
- Re-implementing or reworking the already-completed, full-suite-green J-46 changes (resumed iteration — verify, don't rebuild).

## DEFINITION OF DONE

- [ ] J-46 acceptance met end-to-end: config-set bounded worker pool (no magic number), per-chunk single-transaction bar writes with SQLite writes serialized, chunk-consistent checkpoints + durable Resume + per-`(symbol,date)` idempotency + honest progress regression-tested under parallelism, instrumented test proves ≤ 1 bar-store load per symbol for a K-date backfill, committed advisory benchmark script reports per-stage seed timings.
- [ ] Canonical outputs identical: existing scanner / forward-returns / immutability / no-lookahead / warmup suites pass **unchanged**; cached-vs-uncached snapshot equality test green.
- [ ] Required-still-passing journeys remain green: J-17 + the J-34 resumable surface via browser QA; J-36/J-37/J-38/J-39/J-40/J-41 via suite/API (the session's established verification basis); J-06 spot-checked in the browser (scores identical on `/stocks` and `/stocks/NVDA` after the engine-path refactor).
- [ ] No anti-goal violation introduced (no lookahead, no snapshot mutation, no fabricated bars, no magic numbers, no key leak in job errors).
- [ ] Full backend pytest run **once** to completion: 0 failures (659 passed / 4 skipped baseline already recorded for this working tree, ~46 min budget; re-run only if the diff changes after the recorded green run).
- [ ] Dev handoff written at `docs/handoffs/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-3-dev.md` (already exists from the pre-interruption dev pass — keep/refresh, don't duplicate).

## TESTING REQUIREMENTS

- **Browser** (J-46 surface legs + regression, on the running stack at :8835/:3835 — never self-restart the backend):
  - J-46 steps 1–2: on `/data`, start a multi-symbol fetch with **source=alpha_vantage + key `demo`** (project-memory technique: throttle body → `RateLimitError` → amber **rate-limited — resumable** in ~3 min); confirm live progress stays accurate (counts never exceed totals) while the pool fetches, the job pauses resumable, and **Resume** continues from the checkpoint with no duplicate fetch (job summary/coverage unchanged for already-committed bars).
  - J-17 re-check: a small seed-range **backfill-only** job (offline, deterministic) runs async with live progress to an `ok` summary.
  - J-06 spot check: NVDA's three scores + buckets identical on `/stocks` and `/stocks/NVDA`.
  - If every page renders as a dead un-hydrated shell ("Checking backend…", 404 on `_next/static/...`), record **SKIPPED** (stale `.next`), not FAIL — documented machine quirk.
- **Unit/integration** (offline, injected providers): worker-pool fan-out bounded by `fetch_workers`; per-chunk single commit; mid-chunk 429 ⇒ resumable + chunk-consistent checkpoint + idempotent resume (zero duplicate `(symbol,date)` rows); non-429 error ⇒ failed count + scrubbed message (assert the key string absent from the job-status payload); load-count instrumentation (≤ 1 load/symbol for K dates); cached-vs-uncached snapshot equality; `fetch_workers` boot validation; all five config-dict fixtures updated; existing suites green unchanged.
- **Error cases:** `fetch_workers: 0` / negative / missing ⇒ explicit `ConfigError` at boot (matching the other `import_chunking` validations); persistent 429 ⇒ resumable pause, never `failed`, never a fabricated bar; a worker exception must not deadlock the pool or strand the job in `running`.

## NOTES

- **Resumed iteration — do not redo green work.** The dev dispatch was interrupted by the 2h in-flight timeout AFTER completing the implementation; the working tree already contains the full J-46 change set, the new suites (`tests/test_data_manager_parallel.py`, `tests/test_bar_cache.py`), the benchmark script, the dev handoff, and a recorded full-suite green run (659 passed / 4 skipped / 0 failed). The developer step's job on this re-run is verification/confirmation against this spec; reviewer, QA, auditor, and evaluator run normally over the existing diff. A second full-suite run is needed only if the diff changes.
- Evaluator (iter-2) verbatim drive: "it rewires the concurrency-sensitive import pipeline under multiple critical contracts … where a subtle checkpoint/idempotency/SQLite-write regression would be invisible to browser QA — the full pipeline's skeptical audit step earns its cost here." Hence depth **full** despite zero UI change.
- Seam facts for the developer (verified in pre-iteration source): serial loop + per-symbol commit at `apps/backend/app/engine/data_manager.py` `_run_chunked_fetch` (~lines 1067–1137); per-date re-loading via `prices.bars_asof` call sites in `scoring.py` (lines ~110/236/261/324), `regime.py`, `sectors.py`, `themes.py`; multi-date loops in `data_manager._do_backfill` (~1140) and `warmup._run_warmup` (~102). `scoring.py` already keeps a per-call `sector_closes_cache` — the job-level cache generalizes that pattern one level up.
- The `seed_import` offline source (`seed_import_source_enabled`) and the existing stub-provider test patterns in `test_data_manager.py` are the intended harness for the parallel-contract tests — no network anywhere in the suite.
- Pytest discipline: one full-suite invocation, foreground handed to the pump — never two concurrent runs (shared session DB + warm-up determinism). Full suite is now ~46 min.
- Escalation flag: if making the bar cache safe inside `warmup._run_warmup` conflicts with the iter-28 single-flight guard in any way, prefer landing the cache for `_do_backfill` only and document the warm-up follow-up in the handoff — J-46's acceptance names the backfill job, not the warm-up.
