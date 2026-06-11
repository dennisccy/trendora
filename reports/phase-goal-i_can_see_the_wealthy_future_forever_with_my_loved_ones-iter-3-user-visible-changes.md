# Phase goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-3 — User-Visible Changes

**Phase:** J-46 — Parallel bounded-worker fetch, per-chunk transactional writes, load-bars-once backfill cache, committed advisory benchmark
**Frontend Present:** no (spec metadata); plan.md overrides to yes only to force browser regression checks — no frontend file was changed
**Classification:** Backend-only speed improvement with behavioral regression surface on existing UI

---

## What users can now do

Nothing new. No new pages, no new actions, no new data displayed.

## What is faster (perceptible behavioral change)

### Data Manager — import and backfill jobs complete materially faster

**Surface:** `/data` — Data Manager job cards and live progress

Previously, every import job fetched symbols one-at-a-time in strict serial order, and committed each symbol's bars individually. Every backfill or warm-up job re-queried a symbol's full price history from the database once per date in the job window (a K-date job caused K+ database reads per symbol).

After this iteration:

- **Import jobs run faster.** Symbol fetch now fans out across up to `fetch_workers` (default: 4) parallel network workers per chunk. The user sees the same live progress counter and job card; those same counts now advance faster.
- **Backfill and warm-up jobs run faster.** The bar cache loads each symbol's full price history once for the entire job, slicing in memory for each subsequent date. Multi-date jobs (e.g. a historical backfill over a date range) complete in materially less wall-clock time.
- **Live progress remains accurate.** Progress counters are updated only on the orchestrating thread and are never inflated beyond totals, even under parallel fetching. A user watching the progress counter during a multi-symbol import sees monotonically increasing counts that reflect only durably committed bars.

These changes are invisible by design — the user sees the same Data Manager page, the same job card layout, the same progress display, and the same amber "rate-limited — resumable" state and Resume button. The experience is identical; the time to completion is shorter.

## What behavior changed (existing features that work differently)

### Resumable / Resume semantics — chunk-atomic, unchanged contract

The amber resumable pause and Resume flow on `/data` work identically from the user's perspective:

- A rate-limited pause still shows the amber "rate-limited — resumable" state.
- The Resume button still continues from the last committed checkpoint.
- Already-committed bars are never re-fetched (idempotent resume).

The one internal implementation choice: when a parallel worker hits a persistent rate limit mid-chunk, the interrupted chunk's partially-fetched bars are discarded (chunk-atomic — the chunk commits entirely or not at all). Resume re-fetches the whole interrupted chunk. The user does not see this distinction — the job summary and coverage counts accurately reflect only committed bars at all times.

### Non-rate-limit provider errors — scrubbed error messages unchanged

A non-rate-limit provider error for a single symbol still increments the failed-symbol count and records a scrubbed error message. The behavior is unchanged; the fix ensures that errors raised on parallel worker threads are scrubbed on the orchestrating thread before reaching the job card, so provider API keys never appear in the displayed error text.

## What is NOT visible yet (backend capabilities with no UI)

### Advisory benchmark script

`apps/backend/scripts/benchmark_pipeline.py` is a new offline CLI script that prints per-stage pipeline timings (fetch serial vs parallel pool; scan/snapshot cached vs uncached; forward returns) as a table. It runs against injected stub data with no network access and no API keys. It is never imported by the backend API or the test suite, and it produces no output in the web application. An operator runs it from a terminal to measure pipeline speed on the committed seed data. It is not accessible from any browser page.

### `fetch_workers` config key

The new `data_manager.import_chunking.fetch_workers` key in `config.yaml` controls the parallel pool size (default: 4). It is boot-validated (must be a positive integer; `fetch_workers: 0` or negative causes an explicit `ConfigError` at startup). This key is not displayed anywhere in the web application — there is no settings page, no config panel, and no tooltip showing its value. An operator changes it only by editing `config.yaml` and restarting the backend.

---

## Summary

This is a pure backend performance iteration. Every file changed is backend Python (engine modules, test suites, a benchmark script) or root config. No frontend file was touched. The user-visible surface of the Data Manager (`/data`) is unchanged in layout, labels, and interaction model. The only perceptible user-facing change is that import and backfill jobs complete in less wall-clock time with the same accurate live progress display.
