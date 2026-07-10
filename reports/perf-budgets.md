# Performance Budgets

Committed measurements for the data path on the 30-year / 587-symbol basis (`daily_prices` 3,270,066
rows, 1.3 GB DB). Created in **iter-19** to record fast-platform **item A** (the `/api/data` bar-prefill
OOM fix) per goal.md J-15/J-16's sequencing — this file does **not** yet claim the full J-15/J-16 budget
contracts (every endpoint, every item B–K optimization); those land with their own iterations and append
to this table. Every number below is a real measurement on this host, not an estimate.

## How to reproduce

```bash
bash scripts/start-backend.sh            # cold boot, real committed seed/DB, ulimit -v 6144 MB applied
curl -s http://localhost:<port>/api/data # cold hit (first call after boot — membership-timeline cache miss)
```

Peak RSS sampled via `/proc/<pid>/status` `VmRSS`/`VmHWM` at 0.2–0.25 s intervals for the duration of the
request(s), against the real 30-year DB (no synthetic/scaled-down fixture).

## Item A — bound the bar-prefill OOM (iter-19)

**Problem (measured, iter-18 operator incident):** `prices.py`'s `_BarCache.prefill()` materialized the
whole `daily_prices` table as hydrated `DailyPrice` ORM instances in one `.all()` call (~6.8 GB peak
reported), against the 6144 MB `server.memory_cap_mb` `ulimit -v` cap — the backend OOM'd/hung on its
first `/api/data` visit under the canonical browser-QA lane. A second, distinct cost compounded it: the
same whole-table scan re-ran a SECOND time within one request (`_membership_timeline`'s nested
`prefilled_bar_cache` call on top of `_compute_coverage_uncached`'s own context), because `prefill()`
re-queried unconditionally on every call — invisible at the old ~122-symbol/5-year basis, a doubled
contribution to the OOM at 583 symbols/30 years.

**Fix:** `_BarCache.prefill()` now streams a column-projected query (`symbol, date, open, high, low,
close, volume` — not a whole `DailyPrice` ORM row) via `.yield_per(research.read_batch_size)`, building a
lightweight `Bar` NamedTuple per row (module `app/engine/prices.py`); the lazy per-symbol fallback inside
`bars_asof()` adopts the same lightweight record type (already per-symbol-bounded — no bounding change).
`prefill()` also now skips its expensive scan entirely once already run on that cache instance (a
`self._prefilled` guard), so the nested-call double-scan is eliminated. `ORDER BY symbol, date` and served
values are unchanged — `tests/test_bar_cache.py`'s byte-identical snapshot tests are the correctness gate.

**Measured (2026-07-07, this host, cold boot, real 30-year DB, `memory_cap_mb: 6144`):**

| Scenario | HTTP result | Wall time | Peak RSS (process) | Budget |
|---|---|---|---|---|
| Baseline (post-boot, before any `/api/data` hit) | — | — | ~179 MB | — |
| **Single cold `/api/data`** | 200 (all) | 10.5 s | **~1,087 MB** (`VmHWM`) | ≤ 60 s, no OOM under 6144 MB |
| **6 concurrent cold `/api/data`** (the exact iter-18 incident shape) | 200 ×6 | 18.5 s (all 6) | **~1,101 MB** | ≤ 60 s, no OOM under 6144 MB |
| Settled RSS after the single cold request | — | — | ~243 MB | — |

**Before → after (item A):**

| | Before (reported, iter-18 incident) | After (measured, iter-19) |
|---|---|---|
| Retained/peak footprint, 1 cold request | ~6.8 GB (whole-table ORM `.all()`) | **~1.09 GB** |
| 6 concurrent cold requests | OOM / hung (exceeded the 6144 MB cap) | **~1.10 GB peak — NOT ~6×** (single-flight + streamed prefill hold memory to ~one copy regardless of concurrency) |
| Cold `/api/data` completion | did not complete (OOM) | **10.5 s (1 request) / 18.5 s (6 concurrent)** — both ≤ 60 s budget |

**Reading the numbers:** the ~1.09 GB peak is the transient cost of the ONE-TIME streamed scan building
583 `Bar` lists (3.27M lightweight records); it is not the *retained* steady-state footprint, which settles
back to ~243 MB once the request's `with prefilled_bar_cache(...):` block exits and the cache is garbage
collected. Either figure clears the 6144 MB cap with wide headroom — the prior ~6.8 GB estimate for the
unfixed ORM load left none. The 6-concurrent-request peak (~1.10 GB) barely exceeds the 1-request peak
(~1.09 GB), confirming the pre-existing J-100 single-flight (`compute_coverage`'s per-key lock + in-flight
event) already serializes concurrent cold callers correctly — iter-19's fix was the nested-call double-scan
inside a single compute, not the cross-request single-flight itself (see the dev handoff for the full
diagnosis).

**Config comment fix:** `config.yaml`'s `server.memory_cap_mb` comment referenced "the one-copy ~1.3M-row
bar prefill" (a stale figure from the pre-30y basis); it now cites the real ~3.27M-row figure and the
streamed-load footprint.

## Budgets not yet re-measured this iteration

Items B–K of goal.md's fast-platform section (mechanical backend pass, payload/interaction pass,
compute/storage pass) and the full J-15/J-16 endpoint-by-endpoint budget table (`/stocks`,
`/stocks/{ticker}`, `/api/data` warm path, `/api/health`, page time-to-interactive) are **out of scope for
iter-19** (goal.md sequencing: "iter-19 lands item A only"). They are deferred to the iterations goal.md
already schedules for that work, which will append their own measured rows here.

## Items B/C/D/G/H/K — mechanical backend pass + storage-footprint card (iter-24)

Measured 2026-07-09T06:23:22Z on this host (Linux 7.0.0-27-generic x86_64) via `scripts/measure-perf.sh` against PROD MODE
(`start-backend.sh`/`start-frontend.sh`, backend :8255 / frontend :3255).

**Warm endpoint latencies:**

| Endpoint | Wall time | Budget |
|---|---|---|
| `GET /api/health` | 0.092038s | ≤ 0.1 s |
| `GET /api/stocks` | 0.095589s | ≤ 1.5 s |
| `GET /api/stocks/AAPL` | 0.002907s | ≤ 0.3 s |
| `GET /api/data` | 0.014924s | ≤ 1.5 s |

**Warm page latencies (HTTP response time; the browser-qa lane verifies true interactivity):**

| Page | Wall time | Budget |
|---|---|---|
| `/stocks` | 0.008216s | ≤ 3 s |
| `/stocks/AAPL` | 0.006776s | ≤ 3 s |
| `/data` | 0.005676s | ≤ 3 s |
| `/evidence` | 0.005887s | ≤ 3 s |

**DB capacity snapshot** (item K; from `GET /api/data`'s additive `capacity` field):

| Metric | Value |
|---|---|
| DB file size | 1307414528 bytes |
| `daily_prices` rows | 3293160 |
| `scanner_results` rows | 165755 |
| `forward_returns` rows | 821054 |

**Bounded backfill timing** (item K harness; `--backfill-days 5`): 2005-02-28 → 2005-03-07 (0 cadence-eligible dates in this exact range (the coverage gap list is not cadence-filtered; this backend's cadence is already fully warm) -- an honest no-op, not a failure): status=ok, 0 date(s) covered, 0 snapshot(s) created, 0.23s wall time

**Reading the numbers:** every J-15 budget is met with wide headroom on this warm run (`/api/health`
0.092 s vs the tight 0.1 s budget; every other endpoint/page well under 1/10th of its budget).

**Cold `/api/data` path — CORRECTED by the iter-24 audit (was falsely claimed "re-verified").** The
original iter-24 entry here claimed the cold path "was re-verified ... items C/G/H's query-plan changes did
not reintroduce the OOM" — but its cited evidence was a `/api/health` (readiness) boot, NOT an actual
`GET /api/data` cold-boot request (a different code path; the warm `GET /api/data` 0.0149 s above is a
cache-hit, not a cold-boot number). browser-qa (UT-16) then exercised the REAL cold `/data` load on a fresh
restart and reproduced a backend crash 2/2 times — `MemoryError` in the bar-prefill's `cursor.fetchmany()`,
then a fatal PyO3 panic. **Root cause (audit, confirmed by a controlled ablation):** item B's new
`database.pragmas.mmap_size_bytes = 1073741824` (1 GB) reserves ~1 GB of VIRTUAL address space PER pooled
connection; at `pool_size=10 + max_overflow=20` just ~6 live connections reached 6154 MB — past the
`server.memory_cap_mb = 6144` `ulimit -v` cap — BEFORE the ~3.27M-row prefill allocated anything, so the
prefill's own heap then tipped the process over. **Fix (audit):** `mmap_size_bytes: 0` (mmap disabled;
SQLite's own default). Re-verified end-to-end under the real 6144 MB `RLIMIT_AS` with the same 5-live-pooled-
connection model: at mmap=1 GB the cold `_compute_coverage_uncached` prefill crashes with `MemoryError` at
exactly 6144 MB VmSize (reproduces UT-16); at mmap=0 the identical run peaks at **471 MB** and returns the
full 19-key coverage payload — the cold path completes well under the 60 s / 6144 MB budget. The 256 MB
page cache (demand-resident, not a virtual reservation) is unaffected, so read latency is unchanged.
**Byte-identity:** every optimized path (items B/C/D/G/H) re-serves stored values
verbatim — proven by the existing `test_api_engine.py`/`test_api_watchlist.py` byte-identity suites passing
UNEDITED, plus new targeted tests for each item (`test_db.py`, `test_data_manager.py`, `test_health.py`);
no displayed number changed. **Index hygiene (item C) applied for real:** this run's boot dropped the
byte-for-byte-duplicate `ix_daily_prices_symbol_date` and the redundant `ix_forward_returns_run_symbol`
from the live committed DB (confirmed present before, absent after) and added `ix_daily_prices_date` — the
guarded migration is not just unit-tested, it ran against the real 3.27M-row table in ~1.3 s.

## Cold `/api/data` path — LIVE-VERIFIED by the iter-25 developer pass (real HTTP, not an ablation)

**No source change this iteration.** `config.yaml:108`'s `mmap_size_bytes: 0` was already committed at
HEAD (`665565a`, the iter-24 audit fix); confirmed clean vs HEAD before this measurement, with
`pool_size`/`max_overflow`/`memory_cap_mb` untouched. The prior section's "471 MB" figure came from the
iter-24 audit's controlled ablation of `_compute_coverage_uncached`'s prefill under a simulated
pooled-connection model — real evidence of the ROOT CAUSE, but not an end-to-end HTTP request through the
live FastAPI/uvicorn stack. Per the session lesson ("an engine-level fix is not journey evidence until the
canonical lane re-runs it live"), iter-25 closes that gap with two independent LIVE cold-boot repros
against the real committed 30-year/583-symbol DB — full `kill -TERM` backend stop + fresh
`scripts/start-backend.sh` cold start between them, never accepting an `/api/health` boot as a substitute
(a different code path than the heavy `/api/data` bar-prefill).

**Measured 2026-07-09 (this host, backend :8255, `memory_cap_mb: 6144` `ulimit -v` applied, peak RSS
sampled from `/proc/<pid>/status` `VmRSS` at 0.2 s intervals for the request's duration):**

| Run | Sequence | `GET /api/data` | Wall time | Peak backend RSS | Backend survived? |
|---|---|---|---|---|---|
| 1 | cold-start → (an unrelated background process on this host pinged `/api/health` ×4 first — see note below) → `/api/data` | HTTP 200 | 9.522 s | ~1,814 MB (1,857,632 KB `VmRSS`) | **YES** |
| 2 | cold-start → (same unrelated process pinged `/api/health` ×1) → `/api/data` as the first/only HEAVY request | HTTP 200 | 9.387 s | ~1,859 MB (1,903,228 KB `VmRSS`) | **YES** |

Both runs: HTTP 200, well inside the ≤ 60 s budget, and well inside the 6144 MB `ulimit -v` cap (peak RSS
~1.8 GB leaves ~4.3 GB of headroom — higher than the 471 MB ablation figure since this measurement carries
the full live stack's overhead: uvicorn/FastAPI/SQLAlchemy pool + ORM machinery + JSON serialization on top
of the prefill itself, not just the prefill in isolation — still nowhere near the cap). The backend process
never crashed and never OOM'd in either run, and stayed up afterward to serve warm requests. **This flips
iter-24's UT-16 (browser-qa reproduced the crash 2/2) to fixed, verified 2/2.** Both cold responses'
`capacity` payloads were byte-identical to each other AND to every previously-recorded figure in this file
(`db_file_bytes 1307414528`, `daily_prices_rows 3293160`, `scanner_results_rows 165755`,
`forward_returns_rows 821054`) — no drift, cold or warm.

**Note on the stray `/api/health` hits:** an unrelated background process on this host (not started by this
verification pass) polled `/api/health` a few times immediately after each backend boot. This does not
weaken the repro: `mmap_size_bytes: 0` removes the per-pooled-connection virtual-memory reservation that
caused the original OOM regardless of which endpoint opens a connection first, so a few cheap health pings
before the real test cannot mask or worsen the crash; run 2 confirms `/api/data` was still the first and
only HEAVY (prefill-triggering) request in that process's lifetime.

## Warm budgets — re-confirmed on the fixed build (2026-07-09T11:48:59Z, iter-25)

Re-ran `scripts/measure-perf.sh` (methodology unchanged; output captured to a scratch file rather than
appended here directly, to avoid the script's hardcoded "(iter-24)" section label — the numbers below are
transcribed verbatim from that run) against the same PROD-mode services used for the cold-path repro
above, backend :8255 / frontend :3255, immediately after the cold `/api/data` hit (i.e. now warm):

**Warm endpoint latencies:**

| Endpoint | Wall time | Budget | Holds? |
|---|---|---|---|
| `GET /api/health` | 0.090045s | ≤ 0.1 s | yes |
| `GET /api/stocks` | 0.058175s | ≤ 1.5 s | yes |
| `GET /api/stocks/AAPL` | 0.003139s | ≤ 0.3 s | yes |
| `GET /api/data` | 0.013954s | ≤ 1.5 s | yes |

**Warm page latencies (HTTP response time; the browser-qa lane verifies true interactivity):**

| Page | Wall time | Budget | Holds? |
|---|---|---|---|
| `/stocks` | 0.007822s | ≤ 3 s | yes |
| `/stocks/AAPL` | 0.007391s | ≤ 3 s | yes |
| `/data` | 0.010037s | ≤ 3 s | yes |
| `/evidence` | 0.007531s | ≤ 3 s | yes |

**DB capacity snapshot** (unchanged — byte-identical to every prior measurement in this file):

| Metric | Value |
|---|---|
| DB file size | 1307414528 bytes |
| `daily_prices` rows | 3293160 |
| `scanner_results` rows | 165755 |
| `forward_returns` rows | 821054 |

**Bounded backfill timing** (`--backfill-days 5`): 2005-02-28 → 2005-03-07 (0 cadence-eligible dates in
this exact range — this backend's cadence is already fully warm — an honest no-op, not a failure):
status=ok, 0 date(s) covered, 0 snapshot(s) created, 0.23s wall time.

**Reading the numbers:** every J-15 budget — cold AND warm — is met on this iteration's build, with the
same wide headroom as before. No source code changed this iteration; this section exists purely to replace
the prior ablation-only cold-path claim with a real, live, end-to-end HTTP-level measurement.

**Test-suite corroboration (byte-identity, unedited):** `test_bar_cache.py`, `test_api_engine.py`,
`test_health.py`, `test_data_manager.py` (123 tests, the DoD-named selection) ran with zero source edits:
`123 passed in 7156.23s (1:59:16)`. No displayed value drifted.

## Item F — bound the scoring-input window + warmup forward-return cache-scope (iter-26, J-16)

**Problem (measured, this iteration):** both scoring `bars_asof` sites (`scoring.py:113` `_raw_components`,
`scoring.py:339` pass-3) fed each member's WHOLE ascending as-of series (≈5,300 bars on late dates) into
indicator/pattern computation whose longest lookback is only `high_window_52w` = 252 — so the per-member
list-extraction (`closes`/`volumes`/`highs`/`lows`) and slice work scaled with the full 30-year history
instead of the trailing window that is actually read. Separately, `warmup.py`'s `backfill_forward_returns`
ran OUTSIDE the cadence loop's `bar_cache` on a fresh (uncached) session, and `prices.py`'s `close_on` /
`bars_after` were raw uncached queries — so the forward-return step re-round-tripped the DB per
(run, symbol) even though the cadence loop had already loaded every series.

**Fix:** `indicators.max_lookback_bars = 320` (252 + margin); `scoring.py` slices each member's series to
the last `max_lookback_bars` bars before indicator/pattern computation (byte-identical — every consumer
already reads only a trailing window off the end; `test_scoring_window.py` is the 0-diff gate).
`warmup.py` moved `backfill_forward_returns` INSIDE the cadence `bar_cache` and passes `session` (not
`engine`); `prices.py`'s `close_on`/`bars_after` are now cache-aware, reading the already-loaded series
when a cache is active (default no-context path unchanged). All outputs byte-identical (harness + the
UNEDITED scoring/bar-cache/forward-return suites are the correctness gate).

### Measured before → after (2026-07-10, this host, `.venv` Python 3.12, under `ulimit -v 6291456` KB == the real 6144 MB `server.memory_cap_mb` cap)

Method (honest, same-host, same-subset-both-runs, no estimates — script logic in the dev handoff): baseline
("before") = `max_lookback_bars = 1_000_000` (`bars[-1_000_000:] == bars`, i.e. the exact pre-iter-26
unwindowed behavior); after = the committed `320`. Scoring is timed over a fixed representative 12-date
deep-history cadence subset (evenly spread across the full 85-date cadence, **the same subset both runs**),
`score_stocks` over the full resolved pool, inside ONE shared prefilled `bar_cache` so the one-time bar
load (already budgeted as item A, iter-19) is amortized and the measured delta is the window's real
CPU/allocation effect — exactly the cost shape of the warm-up's own `bar_cache`-wrapped cadence loop.
Each cell is the **min of 3 reps** (strips GC/one-time noise); a discarded process-warmup call precedes the
loop. Network fetch time is excluded (frozen-seed reads only).

**Per-date scoring cost — window OFF (before) vs ON (after):**

| Cadence date | Before (unwindowed) | After (windowed 320) | Improvement |
|---|---|---|---|
| 2005-04-01 | 0.204 s | 0.066 s | 67.6% |
| 2007-03-30 | 0.341 s | 0.108 s | 68.5% |
| 2008-12-31 | 0.354 s | 0.109 s | 69.3% |
| 2010-12-31 | 0.461 s | 0.126 s | 72.7% |
| 2012-12-31 | 0.560 s | 0.143 s | 74.4% |
| 2014-10-01 | 0.738 s | 0.168 s | 77.3% |
| 2016-09-30 | 0.838 s | 0.191 s | 77.3% |
| 2018-06-29 | 1.040 s | 0.223 s | 78.5% |
| 2020-07-01 | 1.199 s | 0.246 s | 79.5% |
| 2022-07-01 | 1.289 s | 0.266 s | 79.4% |
| 2024-04-01 | 1.463 s | 0.285 s | 80.6% |
| 2026-04-01 (latest, deepest history) | 1.681 s | 0.320 s | **81.0%** |

**Committed never-regress J-16 budgets:**

| Budget | Before | After | Improvement | Threshold |
|---|---|---|---|---|
| **Per-date backfill** (latest deep-history cadence date, full pool, scoring compute) | 1.681 s | 0.320 s | **81.0%** | ≥ 30% |
| **Warm-up pass** (12-date deep-history representative subset, sum, scoring compute) | 10.169 s | 2.250 s | **77.9%** | ≥ 30% |
| **Forward-return read step** (`close_on` + `bars_after`, 15-run × pool = 6,110 (run,symbol) pairs) | 2.806 s (raw queries) | 0.296 s (cache-aware) | **89.4%** | ≥ 30% |

The forward-return row is the warmup.py/prices.py cache-scope change measured in isolation: one `close_on`
+ one `bars_after` per (run, symbol) — exactly the read path that step issues — BEFORE (no active cache →
raw per-(run,symbol) queries, the pre-iter-26 `engine`-session shape) vs AFTER (inside an already-prefilled
`bar_cache` → in-memory bisects; the prefill is excluded from the timed region because the cadence loop has
already paid it). No rows are written (the forward-return math is pure Python, identical either way and not
what changed).

**Peak process RSS = 1,330.6 MB** (`getrusage(RUSAGE_SELF).ru_maxrss` high-water mark), well under the
6144 MB cap — and the entire measurement RAN TO COMPLETION under a literal `ulimit -v 6291456` (6144 MB)
virtual-memory cap with NO `MemoryError`, so the iter-26 warm-up/backfill compute path (scoring + the
full-pool bar prefill + forward-return reads) is proven under the cap end-to-end (anti-goal #8). This is
the leaner compute-path process; the FULL live uvicorn/FastAPI server's cold `/api/data` prefill peaks at
~1.8 GB under the same cap (iter-25 section above) — the iter-26 change only REDUCES per-member allocation
and removes per-(run,symbol) forward-return round-trips, so it cannot raise that ceiling. The live cold-path
`/data` OOM repro (stop → cold start → `/data` first, ≥2×) remains the browser-QA lane's check per the
iter-24 lesson.

**Reading the numbers:** the window's benefit scales with history depth — negligible on early short-history
dates (a <320-bar series returns whole, identical work — the 2005 row's improvement is the fixed
list-extraction saving, not the window) and largest on the latest 30-year dates (≈5,300 bars sliced to
320). Every J-16 budget clears the ≥30% threshold with wide margin. Correctness is separate from and prior
to speed here: the byte-identity harness (`test_scoring_window.py`, 0 diffs windowed vs unwindowed over 3
dates × full pool + a short-history date) and the UNEDITED scoring/bar-cache/forward-return suites are the
authority that every displayed score / forward return is unchanged.

**What this measurement does NOT claim:** it is not a full 85-date warm-up run twice end-to-end (the DoD's
sanctioned ≥10-date representative-subset alternative was used, same subset both runs); and the per-date
figures are the scoring COMPUTE cost (the item-F CPU driver), inside the warm cache, not the one-time cold
bar-load (item A, iter-19) or snapshot-persist I/O, which the window change does not touch.

