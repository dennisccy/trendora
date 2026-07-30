# goal-ops-hardening-iter-38 Execution Plan

## What to Build

This is a verification/measurement iteration closing J-07 ("Heavy aggregates never take the service
down") — the session's last non-`passing` journey (`partial` for 3 consecutive iterations). iter-37
shipped the real code fix (one shared `_BarCache` across `_do_backfill` + the ingest-finalize tail
instead of two whole-table loads) but both its live drills exercised paths where the new behavior is
inert (step 1/3 via `GET /api/backtest`'s daemon-thread dispatch — no `JobProgress`; step 4's drill had
`dates_total: 0` — `cache_ctx` was `nullcontext()`). This iteration measures the ONE state iter-37's own
change creates (the shared cache held resident across the WHOLE finalize tail) for the first time, plus
closes small hygiene/test gaps the iter-37 auditor left as GAP/OBSERVATION. **No changes to
`compute_forward_aggregates` / `resolved_forward_aggregate_evidence` /
`ensure_historical_forward_aggregates_dispatched`** — byte-frozen per the spec's binding "Do not redo."

- **Widen the throwaway-DB drill fixture** (reuse the `runs/goal-ops-hardening-iter-34/mem-drill/
  seed_throwaway_db.py` lineage into a new `runs/goal-ops-hardening-iter-38/mem-drill/` copy) so a
  submitted backfill targets a REAL K≥3-trading-day range not already snapshotted (`dates_total >= 3` in
  final job status) instead of the prior deliberate 0-target no-op. This is what makes `_do_backfill`
  genuinely stash `prog._shared_bar_cache` and makes `data_manager.py`'s finalize-tail `cache_ctx`
  (~line 3337-3338) resolve to a real `attach_shared_cache(...)`, never `nullcontext()`.
- **Add an explicit liveness assertion/log line** proving `cache_ctx` was the live `attach_shared_cache`
  branch for the drill run (per the binding iter-37 lesson: assert the condition was live, don't assume
  it from the lexical wrap alone) — e.g. log/assert `cache_ctx is not contextlib.nullcontext()` or an
  equivalent identity check, captured in the drill's own evidence output.
- **Sample VmPeak continuously across the WHOLE finalize tail** during that live-cache drill (not just
  inside the per-item aggregate-warm sub-loops, which is all iter-34/37's monitor scripts covered) — a
  throwaway process, launched ONLY via `scripts/start-backend.sh` (AG-10), tightened
  `server.memory_cap_mb` mirroring iter-34/37's calibrated boundary (they used `970` — reuse or
  recalibrate as needed).
- **Produce a comparable forced-fallback measurement** of the SAME finalize-tail work with the shared
  cache attach forced off (`cache_ctx` = `nullcontext()`, mirroring pre-iter-37 behavior — e.g. a test
  hook/monkeypatch that stashes `prog._shared_bar_cache = None` before the finalize hook runs, or an env
  toggle) so "does holding the cache across the tail raise the peak?" is answered by a genuine two-arm
  comparison, not one number read in isolation.
- **Re-run J-07 step 1 on the real, full-deep-basis live seed DB**: trigger the forward-aggregate warm
  for every configured horizon through a genuine backfill/rebuild job's ingest-finalize hook (NOT
  `GET /api/backtest`, which has no `JobProgress`/shared-cache path at all). Select/confirm a target
  as-of date NOT yet cached under the current `dataset_version` (query `ForwardAggregateCache` first) so
  the warm performs real work — bounded to one warm cycle (iter-37's own precedent: well under 5 minutes
  wall-clock), launched only via `scripts/start-backend.sh`.
- **Run a 1Hz `GET /api/health` poll concurrently** for the full duration of that live-basis warm (J-07
  step 2). The standing ≤0.1s steady-state budget stays the separately-tracked owner item (iter-34/j) —
  disclose an honest WARN if missed, same convention as iter-37; do not score it as a J-07 failure.
- **Record both measurements as new dated sections in `reports/perf-budgets.md`** (the SAME artifact,
  append — no second file): (a) the two-arm live-cache-vs-forced-fallback VmPeak comparison across the
  whole finalize tail, (b) the real-trigger step-1 VmPeak margin against `server.memory_cap_mb`.
- **Add a dedicated unit test** for `_do_backfill`'s whole-stage `except Exception:` branch
  (`data_manager.py` ~line 3162, the iter-37-added release-and-reraise path) confirming it sets
  `prog._shared_bar_cache = None`, calls `_release_process_memory()`, and re-raises the original
  exception (reviewer MINOR, iter-37 — currently untested).
- **Strengthen `test_run_data_job_backfill_wires_finalize_hook_end_to_end`**
  (`apps/backend/tests/test_data_manager.py:2167`) to compare the live-cache run's `aggregates_refreshed`
  category list against a forced-fallback run of the same job shape (audit T2, iter-37 — the per-category
  warm loops swallow non-`MemoryError` exceptions, so a break shows up only as a silently shorter list;
  today's assertion is `>=` a subset, not a full comparison).
- **Investigate and fix the stale `membership_timeline_cached` docstring** near `data_manager.py:650-654`
  (audit B7, iter-37). NOTE for the developer: a direct read of the current file at those lines already
  states the code pays "ONE prefill + in-memory bisects, NOT one grouped-count round-trip per date" —
  i.e. it may already be accurate. Before editing, re-locate the actually-stale text (it may have shifted
  a few lines, or the stale reference may be a different nearby docstring/comment describing
  `membership_timeline_cached`'s cost shape) and confirm the finding is still live before changing
  anything; if genuinely already correct, note that in the dev handoff instead of a no-op edit.
- **Fix `reports/perf-budgets.md:4466`**: "591 symbols" → "548 symbols" (audit B8, iter-37 — confirmed
  stale; matches the live pool count).
- **Measure and record `read_pool()`'s now-per-(batch × date) re-read wall-clock cost** (~20,680 calls
  against 1,880 dates, versus 1,880 before the iter-37 shared-cache change) as a new row/section in
  `reports/perf-budgets.md` (audit B6, iter-37 — a real added constant-time cost on a cold path, never
  measured in wall-clock terms). `read_pool()` lives in `apps/backend/app/engine/universe_screen.py`; the
  per-(batch × date) call pattern is in the per-date coverage/membership warm loops in `data_manager.py`
  (search callers around line 3241 and the per-date coverage snapshot loop) — trace which loop's calling
  pattern changed shape due to iter-37's edit before measuring.

## Agents Required
- backend-data: yes -- all work above (drill fixture, two-arm memory measurement, live-basis warm
  re-trigger, new/strengthened unit tests, docstring/perf-budgets hygiene fixes, wall-clock measurement)
- frontend-ux: no -- zero frontend files touched; `Frontend Present: no` per the phase spec's own
  metadata

## Frontend Present
no

## Files to Create/Modify
- `apps/backend/app/engine/data_manager.py` -- docstring fix near `membership_timeline_cached`
  (~line 650-654) if genuinely stale; possibly a small liveness-assertion helper/log line near the
  finalize-tail `cache_ctx` resolution (~line 3337-3338) if not already loggable from outside; no change
  to `compute_forward_aggregates`/`resolved_forward_aggregate_evidence`/
  `ensure_historical_forward_aggregates_dispatched` (byte-frozen)
- `apps/backend/tests/test_data_manager.py` -- new test for `_do_backfill`'s `except Exception:` branch
  (TC-6); strengthen `test_run_data_job_backfill_wires_finalize_hook_end_to_end` (~line 2167) to compare
  against a forced-fallback run (TC-7)
- `apps/backend/tests/test_backfill_coverage_shared_cache.py` -- extend if a forced-fallback/liveness
  helper belongs here alongside the existing pinned-oracle/mutation tests, at developer's discretion
- `runs/goal-ops-hardening-iter-38/mem-drill/` -- NEW: widened `seed_throwaway_db.py` (K≥3 real trading
  days), drill/monitor scripts (continuous VmPeak sampler across the whole finalize tail), forced-fallback
  harness, scratch config, log excerpts, JSON captures (throwaway DB itself never committed, per iter-37
  precedent)
- `runs/goal-ops-hardening-iter-38/j07-warm/` -- NEW: evidence for the live-basis real-trigger step-1
  warm (monitor script/CSV, health-latency CSV, baseline/trigger/post-warm JSON captures)
- `reports/perf-budgets.md` -- new dated "Iteration 38" section(s): two-arm cache-liveness comparison,
  real-trigger step-1 VmPeak margin, `read_pool()` wall-clock cost row, plus the "591→548 symbols"
  correction at line 4466
- `docs/handoffs/goal-ops-hardening-iter-38-dev.md` -- dev handoff (required by DoD)

## UI Evolution
N/A -- `Frontend Present: no`. No new user-facing capability, no new information displayed, no new user
actions, no UI surface changes, no navigation changes. This iteration is backend measurement/verification
plus test and documentation hygiene on an already-shipped capability.

## Visual Requirements
N/A -- backend-only iteration.

## Key Test Scenarios
- TC-1: throwaway DB via `scripts/start-backend.sh`, tightened `server.memory_cap_mb`, backfill targeting
  a real K≥3-trading-day range (none pre-snapshotted) → final job status `dates_total >= 3`, and the
  drill's own log/assertion confirms `cache_ctx` resolved to `attach_shared_cache` (not `nullcontext()`).
- TC-2: TC-1's job with the shared `_BarCache` genuinely attached across the WHOLE finalize tail, VmPeak
  sampled continuously from `/proc/<pid>/status` throughout (not only per-item sub-loops) → recorded in
  `reports/perf-budgets.md` alongside a forced-fallback run (`cache_ctx` forced to `nullcontext()`) of the
  same job shape, showing whether live-cache peak is higher or lower.
- TC-3: real full-deep-basis live seed DB, fresh backend via `scripts/start-backend.sh`, genuine
  backfill/rebuild's ingest-finalize hook triggers the forward-aggregate warm for every horizon (target
  as-of confirmed NOT cached under current `dataset_version`) → completes without crashing, triggered
  date's `GET /api/backtest` reaches `evidence_status: "ready"` for all horizons, VmPeak recorded under
  `server.memory_cap_mb` in `reports/perf-budgets.md`.
- TC-4: during TC-3's warm, `GET /api/health` polled 1Hz for the full duration → every poll HTTP 200, no
  gap > ~2.15s; any steady-state ≤0.1s miss recorded as honest WARN against iter-34/j, not scored as J-07
  failure.
- TC-5: any browser/QA test plan touching J-07 places the induced-pressure drill (step 4, inherently
  disruptive) strictly AFTER every other J-07 assertion — a denied restart afterward cannot strand an
  earlier assertion. **QA/browser-qa agents must honor this ordering explicitly in their test plans.**
- TC-6: `_do_backfill`'s `except Exception:` branch (`data_manager.py` ~line 3162) — new test asserts a
  whole-stage exception inside `with prefilled_bar_cache(...)` sets `prog._shared_bar_cache` back to
  `None`, calls `_release_process_memory()`, and re-raises the original exception (not swallowed).
- TC-7: `test_run_data_job_backfill_wires_finalize_hook_end_to_end` strengthened to assert the live-cache
  run's `aggregates_refreshed` category list is complete versus a forced-fallback run's correctly
  degraded/shorter list where applicable.
- TC-8/TC-9: docstring (`data_manager.py:650-654`) and `perf-budgets.md:4466` hygiene fixes, verified by
  direct read after the change.
- TC-10: `read_pool()`'s per-(batch × date) re-read wall-clock cost measured on a representative
  multi-date backfill, recorded as a new row/section in `reports/perf-budgets.md`.
- TC-11: deterministic golden replay for J-01, J-03, J-04, J-05, J-06, J-08, J-09 (required-still-passing)
  runs zero FAIL rows, zero reconciliation overturns — no journey moves `passing` → `failing`. Since
  TC-3's live-basis warm mutates the real committed-seed DB (new/refreshed `dataset_version`, similar to
  how J-08's own acceptance text already exercises "a small single-day backfill... bumps the dataset
  version"), sequence the replay/browser checks for the other required-still-passing journeys with this in
  mind — either capture their evidence before TC-3's warm or confirm their checks are robust to the
  dataset-version advance (this project's existing convention, not a new risk).

## Coordination / Sequencing Notes for downstream agents
- AG-10: ALL heavy compute (both the throwaway-DB drill and the live-basis warm) must launch only via
  `scripts/start-backend.sh` — never `dev.sh`, never bypassing host-guard caps.
- TC-5's "induced-pressure drill last" rule applies to the QA/browser-qa test plan ordering, not just dev
  work — flag this explicitly when designing the J-07 test plan.
- Corroborate every drill claim against a bounded line range in the LIVE `logs/backend.log`, not a saved
  excerpt (binding iter-34 lesson — a prior iteration's excerpt omitted the single most important
  corroborating line class for its own claim).
- Out of scope (do not touch): iter-33/g (Regime Lab `view=pooled` dispatch), iter-34/j (`GET /api/health`
  ≤0.1s budget owner decision), iter-33/i (`start-frontend.sh`/`HOST_GUARD_MARKER_FILES`), the vendored
  `closure_gate.py` regex false-positive, `warmup.py:194`, iter-29/b, iter-31/e, iter-32/f, iter-36/n.
