# goal-ops-hardening-iter-8 Execution Plan

## Context (for the developer, not restated in spec form)

This is a REGRESSION-recovery iteration (full depth). iter-7 shipped a genuinely-correct
`drawdown_expectations` ingest-time warm (closing J-06's `/evidence` cold-miss) but browser-qa
live-observed J-05 break: during a real back-to-back heavy ingest (full rebuild immediately
followed by a heavy backfill, same long-lived process), `GET /api/health` hung 7+ minutes, a
worker thread hit `MemoryError` at the enforced `memory_cap_mb=6144` `ulimit -v` ceiling, all
threads sat in `futex_do_wait`, and a manual restart was required
(`runs/goal-session-ops-hardening/iter-7/eval.md`).

Root cause (confirmed by code read, `apps/backend/app/engine/data_manager.py`): the ingest
finalize hook `_refresh_ingest_aggregates` (starts line 3046) and the per-date coverage helper it
calls, `_persist_per_date_coverage_snapshots` (line 3005), each isolate per-item failures with a
**generic** `except Exception: log + continue`. A `MemoryError` is a subtype of `Exception`, so
under real pressure it gets caught, logged, and the loop immediately tries the NEXT item's
allocation — hammering further large allocations instead of backing off. Four loops are affected,
all sequential on the same finalize tail:
1. Per-date coverage warm — `_persist_per_date_coverage_snapshots`, lines 3038-3043
   (`refresh_coverage_snapshot_for` per date in `todo`).
2. Per-date market-phase warm — inside `_refresh_ingest_aggregates`, lines 3098-3104
   (`market_phase.market_phase_cached` per date in `prog.new_snapshot_dates`).
3. Per-horizon forward-aggregates warm — lines 3122-3132
   (`forward_testing.forward_aggregates_cached` per horizon in `cfg.walk_forward.horizons`).
4. Per-claim drawdown-expectations warm (iter-7's new block) — lines 3158-3180
   (`forward_testing.compute_drawdown_expectations_cached` per ledger claim).

The fix is a bounded, surgical error-handling change to these four loops ONLY — no change to
`app/api/health.py`, `app/engine/readiness.py`, `main.py`'s boot sequence, or `warmup.py` (their
existing exception handling already degrades honestly once the process has allocation headroom;
this iteration restores that headroom at the source). No change to `max_range_days`,
`snapshot_cadence`, or the backfill range cap. Do not touch the CORRECTNESS of any warm (all stay
byte-identical to a fresh compute) — only what happens when one item raises `MemoryError`.

## What to Build

- **Live baseline measurement (before any code change):** spawn a real backend process
  (`scripts/start-backend.sh`, prod mode, enforced `ulimit -v`) on an otherwise-idle host, run a
  full-universe rebuild immediately followed by a second heavy backfill in the SAME process
  (mirrors iter-7's failure scenario), and sample `/proc/<pid>/status` VmPeak/VmSize throughout.
  Confirms and quantifies the drawdown-expectations warm block's marginal contribution to peak
  VSZ before changing anything (root-cause confirmation the prior lesson requires).
- **Distinct `MemoryError` handling in all four loops above:** on the FIRST `MemoryError` caught
  inside one of these four loops, stop attempting further items in THAT loop only (do not
  continue to the next item under pressure), log an honest "aborted remaining `<category>` warm —
  memory pressure" message, and force `gc.collect()` before returning/continuing to the next
  independent block. Every other loop's own try/except boundary is untouched — one loop backing
  off must not abort the whole function or the other three loops. Non-`MemoryError` exceptions
  keep the EXISTING generic isolate-and-continue behavior unchanged (do not regress
  `test_finalize_hook_drawdown_expectations_isolates_claim_that_raises` or the analogous
  coverage/market-phase/forward-aggregates isolation behavior).
- **Honesty-gate re-verification (no gate logic change):** confirm the existing "only report a
  category in `aggregates_refreshed` if it actually warmed ≥1 item" gate still holds correctly
  under the new early-abort path — a loop that warms ≥1 item then aborts on item 2+ still reports
  the category honestly; a loop that aborts on item 1 (zero items warmed) omits it, exactly like
  today's "nothing happened" path.
- **Post-fix live re-measurement:** re-run the SAME real back-to-back heavy ingest on the hardened
  build; confirm peak VmPeak stays under 6144 MB with a documented safety margin and `GET
  /api/health` stays responsive (every poll within budget, zero hangs) throughout. Record both the
  pre-fix and post-fix numbers as a new dated section in `reports/perf-budgets.md` (extends Item
  L) — additive only, no existing budget number loosened.
- **Unit tests for the new behavior** (see Key Test Scenarios below) — MemoryError injected on the
  first item of a loop vs. after ≥1 item succeeded, a real-process back-to-back heavy-ingest
  health-poll test mirroring the `spawned_backend` fixture pattern in
  `test_start_backend_script.py`, and a same-process recovery check (no leaked lock/transaction
  after an injected `MemoryError`).
- **Dev handoff** at `docs/handoffs/goal-ops-hardening-iter-8-dev.md`, with a "Known Issues"
  section that explicitly carries forward the deferred `/api/backtest` on-load `MemoryError` (out
  of scope this iteration, per goal.md OUT OF SCOPE) as next-iteration work.

## Agents Required

- backend-data: yes -- all work is backend: `apps/backend/app/engine/data_manager.py`'s four warm
  loops, plus live measurement scripts/tests and `reports/perf-budgets.md`.
- frontend-ux: no -- goal.md iter-8 spec states "None. No UI surface, state, or contract changes."
  No frontend file may be touched this iteration.

## Frontend Present

no

## Out of Scope (do not build)

- The separate `/api/backtest` → `forward_aggregates_cached` → large `ScannerResult` `MemoryError`
  on an ON-LOAD (not ingest-finalize) path — explicitly deferred to a follow-up iteration; record
  it in the dev handoff's Known Issues, do not fix it here.
- Raising `server.memory_cap_mb` as a workaround — rejected in goal.md; the fix bounds peak RAM,
  it does not raise the ceiling.
- Any change to `readiness.py`, `main.py`'s boot sequence, or `warmup.py`.
- Any change to `max_range_days`, `snapshot_cadence`, or the backfill range-cap logic.
- Removing/weakening the `drawdown_expectations` (or any other) warm's correctness — it must stay
  byte-identical to a fresh compute.
- Isolating ingest jobs into a separate OS process — bigger than this bounded fix; only a fallback
  direction if the live measurement shows the loop-level bound is insufficient (escalate instead
  of scope-creeping into this iteration).
- Loosening any committed budget number in `reports/perf-budgets.md`.

## Files to Create/Modify

- `apps/backend/app/engine/data_manager.py` -- add `MemoryError`-specific early-abort handling
  (distinct `except MemoryError` before the existing generic `except Exception`) to the four warm
  loops: `_persist_per_date_coverage_snapshots` (per-date coverage, ~line 3038-3043),
  `_refresh_ingest_aggregates`'s per-date market-phase loop (~line 3098-3104), per-horizon
  forward-aggregates loop (~line 3122-3132), and per-claim drawdown-expectations loop (~line
  3158-3180); force `gc.collect()` on abort; keep the existing "actually warmed" honesty gate
  correct under early abort; import `gc` if not already imported.
- `apps/backend/tests/test_data_manager.py` -- add unit tests: `MemoryError` on first item of each
  affected loop (zero items warmed, category honestly omitted, job still reaches terminal status),
  `MemoryError` after ≥1 item succeeded (category honestly reports partial warm, no further items
  attempted), a same-process DB-read recovery check after an injected `MemoryError` (no leaked
  lock/transaction), and byte-identity of a warmed value vs. a fresh uncached compute (correctness
  untouched). Verify `test_finalize_hook_drawdown_expectations_isolates_claim_that_raises` (and
  equivalent coverage/market-phase/forward-aggregates isolation tests) still pass unchanged for
  non-memory exceptions.
- `apps/backend/tests/test_start_backend_script.py` -- add (or extend) a real-process
  back-to-back heavy-ingest test using the existing `spawned_backend` fixture pattern: full
  rebuild immediately followed by a heavy backfill in the same spawned process, `/proc/<pid>/status`
  VmPeak sampled throughout, `GET /api/health` polled every ~2s for the full duration, asserting
  zero timeouts/hangs and VmPeak staying under `memory_cap_mb` with margin.
- `reports/perf-budgets.md` -- new dated section extending Item L: pre-fix VmPeak baseline
  (confirming the drawdown-expectations block's marginal contribution), post-fix VmPeak measured
  across the same real back-to-back heavy ingest, and the `GET /api/health` responsiveness poll
  log for the SAME run. Additive only.
- `docs/handoffs/goal-ops-hardening-iter-8-dev.md` -- new dev handoff; Known Issues section must
  carry forward the deferred `/api/backtest` on-load `MemoryError`.
- `runs/goal-session-ops-hardening/state/blueprint.md` -- verify only (per DoD: "already updated
  this iteration by the decomposer; developer/reviewer confirm no drift"). Do not add a new field,
  endpoint, or computing module — this iteration changes only internal error-handling/memory
  behavior of the already-registered `_refresh_ingest_aggregates` hook and the already-registered
  `aggregates_refreshed` field's honesty gating.

## Key Test Scenarios

- TC-1: real spawned backend, enforced `ulimit -v`, full-universe rebuild immediately followed by
  a second heavy backfill in the SAME process → `/proc/<pid>/status` VmPeak sampled throughout
  stays below `memory_cap_mb` (6144 MB) with a documented margin, no `MemoryError` raised.
- TC-2: same back-to-back heavy-ingest run, `GET /api/health` polled every 2s for the full
  duration of both ingests → every poll HTTP 200 within its existing committed budget, zero
  timeouts/hangs.
- TC-3: unit test monkeypatches one per-item warm call to raise `MemoryError` on the FIRST item →
  that loop stops immediately, the category is NOT in `refreshed` (zero items warmed), job still
  reaches a terminal status (not stuck `running`).
- TC-4: same injected-`MemoryError` scenario, in the SAME process a subsequent DB read afterward
  (e.g. `refresh_coverage_snapshot` or `GET /api/data`) succeeds — no leaked lock/open transaction
  blocking recovery without a process restart.
- TC-5: unit test raises `MemoryError` only on the SECOND of N items (first succeeds) → category
  IS in `refreshed` (≥1 item honestly warmed), no items after the second attempted.
- TC-6: `test_finalize_hook_drawdown_expectations_isolates_claim_that_raises` (existing,
  non-`MemoryError` exception) re-run unchanged → still passes; generic isolate-and-continue
  behavior for ordinary exceptions is not altered.
- TC-7: a warmed value (e.g. one ledger claim's `drawdown_expectations`) on the hardened build vs.
  a fresh uncached compute for the same claim → byte-identical (correctness untouched).
- TC-8: `pytest apps/backend/tests/test_data_manager.py apps/backend/tests/test_start_backend_script.py -v`
  → 0 failures, 0 errors (targeted files only — do NOT run the full suite concurrently with the
  live VmPeak measurement; export `TMPDIR`/`TMP`/`TEMP` to the session-isolated scratch dir first).
- TC-9: J-01's and J-03's existing golden replay scripts, replayed against this build → both PASS
  end-to-end, no step failures attributable to this iteration's diff.
- TC-10: J-04 (non-blocking boot with visible status) re-verified live (LLM fallback) → still
  passes unchanged, since this iteration's diff does not touch boot/readiness code.
- J-05 full re-verification via browser-qa-agent: all 4 acceptance steps, especially step 4
  (`GET /api/health` responsive throughout a real heavy-ingest job) — must pass with no
  hang/timeout, on the SAME real back-to-back heavy-ingest conditions that broke it in iter-7.
