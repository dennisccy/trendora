# iter-39 FIX PASS — deterministic J-07 step-4 fault-injection drill

Closes audit findings **B3** (TC-1 unmet) and **B5** (TC-3's "during-abort" read not literal), and
supersedes the three cap-calibration trials in `../mem-drill/` as this iteration's TC-1/2/3/4 evidence.

## Why this replaces the cap drill

The three live trials at 3420 / 2700 / 2650 MB never reached the two per-item aggregate-warm handlers
J-07's acceptance names. The mechanical reason is in the audit (B3) and `reports/perf-budgets.md`:
`_missing_data_diagnostic` materializes the whole `daily_prices` table **earlier in the same finalize
sequence**, so any cap tight enough to threaten the target loops exhausts the budget upstream first.
Continuing to tune the cap is the wrong-direction pattern in `.claude/judgment-rubrics.md` §4 — and the
tightest trial produced a process wedge instead of a proof.

J-07 step 4 sanctions the alternative in its own text: *"Induce memory pressure during a warm (**test
hook** or a tightened cap in a throwaway process)"*. This drill uses the test hook
(`TRENDORA_FAULT_INJECT_MEMORY_ERROR`, `data_manager._fault_inject_memory_error`) at the exact named
call site. It therefore runs at the **committed `memory_cap_mb: 6144`** — unchanged — and induces no
real memory pressure at all, which also makes it host-safe to repeat (AG-10).

## How it was run (AG-9 / AG-10)

Throwaway DB only (`../mem-drill/drill.db`, offline committed seed — no network), launched **only** via
`scripts/start-backend.sh` with the HOST-GUARD block untouched:

```
TRENDORA_CONFIG=<this dir>/config.faultdrill.yaml \
TRENDORA_FAULT_INJECT_MEMORY_ERROR=forward_aggregates \
CHAIN_BACKEND_PORT=18255 bash scripts/start-backend.sh
```

Two runs, same process (PID 982870), same injection. Run 2 is authoritative; run 1 is kept because it
is the honest reason run 2 exists.

| | run 1 (`run1-1hz/`) | **run 2 (this dir — authoritative)** |
|---|---|---|
| job id | `441758a38a444c55844a93b1f3cbbce5` | `c67a6b0a31c040d0a666605081aef4aa` |
| backfill range | 2026-06-25 → 2026-06-26 | 2026-06-29 → 2026-06-30 |
| `/api/backtest` poll cadence | 1 Hz (sampled) | back-to-back (continuous) |
| TC-3 request in flight at the abort instant | **no** — missed by 74 ms | **yes** |

## Results (run 2)

- **TC-1 — which stage aborted, read directly from the log, job-scoped** (`abort-log-excerpt.txt`):
  - `00:10:52,524 INFO … J-07 finalize-tail cache_ctx liveness: job=c67a6b0a… resolved=attach_shared_cache(live shared cache)`
  - `00:11:16,666 ERROR … ingest forward-aggregate warm aborted at horizon 1 — memory pressure, stopping remaining horizons in this loop: injected at fault-injection site 'forward_aggregates'`
  - This is the **per-horizon forward-aggregate handler**, not `_do_backfill`'s prefill and not
    `refresh_coverage_snapshot`'s generic handler — each of which logs a different, distinctive line.
- **Honest partial-success accounting** (`final-job-status.json`): `status: ok`, `dates_total 2`,
  `dates_done 2`, `snapshots_created 2`, `error_other 0`, and
  `aggregates_refreshed = [latest_snapshot, coverage, membership_timeline, market_phase,
  research_hot_keys, drawdown_expectations]` — `forward_aggregates` is **honestly absent** (it aborted)
  while `research_hot_keys` and `drawdown_expectations`, which run **after** it, completed normally.
  That is the per-item isolation contract proven end to end in a live server, not in a unit test.
- **TC-2 — health coverage** (`health-monitor.csv` / `.out`): 68 polls at 1 Hz from job start to
  terminal status, **0 non-200**, max inter-poll gap 2.298 s, safety backstop did not fire. No
  `MAX_SECONDS` window.
- **TC-3 — a previously-cached read during AND after the abort** (`backtest-poll.jsonl`,
  `tc3-containment.json`): 1,246 `GET /api/backtest?as_of=2026-06-24` requests, **0 non-200**. One
  request's interval literally contains the abort instant — start `23:11:16.566Z`, abort
  `23:11:16.666Z`, end `23:11:17.118Z` — returning **HTTP 200** with the full 105,190-byte cached
  payload. 500 further requests started after the abort; all 200.
- **TC-4 — no wedge, no restart**: uvicorn PID `982870` before and after the drill
  (`drill-pid-before.txt`), and a follow-up `GET /api/health` answered **200**.

## Files

- `config.faultdrill.yaml` — scratch config: drill DB url + the **committed** `memory_cap_mb: 6144`.
- `backtest_poller.py` — the TC-3 poller (records each request's start/end epoch so containment is
  checkable, not asserted in prose).
- `health-monitor.*` — the 1 Hz health/VmPeak monitor (`../mem-drill/monitor.py`, unchanged).
- `abort-log-excerpt.txt`, `final-job-status.json`, `tc3-containment.json`, `trigger-response.json`,
  `pre-/post-drill-backtest-2026-06-24.json`, `drill-pid-before.txt`, `run1-1hz/`.
