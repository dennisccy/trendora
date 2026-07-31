# iter-41 — faulthandler-armed wedge-recurrence re-check (C7/C8)

Re-runs the SAME throwaway-DB wedge drill iter-39/iter-40 used (2650 MB tightened cap, never widened —
binding iter-39/40 instruction), this time with two additions:

1. **C7** — `TRENDORA_DIAG_FAULTHANDLER_SIGUSR1=1` set before launch, so `apps/backend/main.py` arms
   `faulthandler.register(signal.SIGUSR1, all_threads=True)`. If the process wedges, `kill -USR1 <pid>`
   would dump an all-thread stack trace WITHOUT killing it — the tool iter-40's run 1 needed but did not
   have (`gdb` attach denied by `yama.ptrace_scope`; no `py-spy` installed).
2. **C8** — `wedge-drill/monitor.py` extended to keep polling (health + job-status + VmPeak/VmHWM) for a
   fixed window PAST the job's first terminal `job_status` reading (30 s here), instead of stopping the
   instant it appears — closing audit finding B2 ("the previous wedge appeared shortly after the terminal
   DB write, and iter-40's own monitor stopped covering exactly that window").

Launched only via `scripts/start-backend.sh` (AG-10), throwaway DB seeded offline from the committed
seed (AG-9, `seed_throwaway_db.py`, identical to iter-40's). Job triggered only AFTER `GET /api/health`
reported `"readiness":"ready"` (warmup fully settled, 89/89 history + membership-timeline + coverage
snapshot all warmed) — the same single-job shape iter-39's trial 3 / iter-40's run 2 used, avoiding
run 1's confound (job racing the still-mid-flight boot warmup thread).

## Setup

- **Config:** `config.scratch.yaml` — `memory_cap_mb: 2650` (same cap family as iter-39 trial 3 / iter-40,
  never widened), `database.url` pointed at this directory's own throwaway `drill.db`.
- **PID:** 1897577 · **port:** 18270 · **launched:** 2026-07-31T03:42:27Z (`logs/backend.log`).
- **Trigger:** `{"kind":"backfill","start":"2026-06-16","end":"2026-06-18","source":"yahoo"}` — identical
  request shape to iter-40's own drill (`trigger-response.json`), job id
  `45f34324470b46de8bc92cdfdfe9e0c8`, started `2026-07-31T03:46:18Z`.

## Result: the wedge did NOT recur

- **Job finished `status: ok`** at `2026-07-31T03:50:32Z` (254 s total). `aggregates_refreshed`: **all
  eight** — `latest_snapshot, coverage, membership_timeline, market_phase, forward_aggregates,
  research_hot_keys, index_series, drawdown_expectations`. Notably `coverage` completed this run — the
  ONE item iter-40's run 2 could not get (its `_compute_coverage_body` COUNT-DISTINCT allocation
  `MemoryError`'d because the process was already sitting at the 2650 MB ceiling by the time that line
  ran). No such MemoryError appears anywhere in this run's log window (`logs/backend.log` lines
  150061-150362, i.e. from this launch's own banner through the run's end — grepped directly, zero
  matches for `memoryerror|traceback|exception|error`, case-insensitive).
- **`GET /api/health` answered 200 on all 58 polls, 0 non-200, max inter-poll latency 1.73 s** (the
  monitor's own health CALL latency, not a gap between polls — see `run1-monitor.csv`) — no unresponsive
  window at any point, pre- or post-terminal.
- **Post-terminal coverage (C8, closes audit B2): 28 additional polls recorded for 30 s PAST the job's
  first terminal reading** — every one healthy (`health=200`), `job_status` staying `ok` throughout. This
  is the window iter-39's trial-3 wedge actually appeared in and iter-40's own monitor never covered; here
  it is fully evidenced, clean.
- **VmPeak peaked at 2,446,836 kB (~2.39 GB)** — **266,764 kB (~260 MB, ~9.8%) BELOW the 2,713,600 kB
  (2650 MB) cap**, never exceeded it. **VmHWM (peak RSS) peaked at 1,908,124 kB (~1.86 GB)**. Contrast
  with iter-40's run 2, whose VmPeak hit the cap EXACTLY (2,713,600 kB, zero margin) on a job that could
  NOT complete `coverage`. This run has MORE headroom AND completed MORE work (all 8 aggregates, not 7) —
  consistent with (not proof of) B5's ~52% `_BarCache.prefill` memory-footprint reduction (see
  `reports/perf-budgets.md`'s Iteration 41 section) giving the finalize sequence more room under the same
  tightened cap.
- **The wall-clock (254 s) is longer than iter-40's run 2 (35.9 s)** — NOT a performance regression: the
  two runs did different amounts of work. Iter-40's `coverage` computation MemoryError'd out early and
  was skipped (absent from its `aggregates_refreshed`); this run's `coverage` computation ran to
  completion. Comparing wall-clock across runs that completed a different amount of work would be
  misleading, so this report does not claim a speed finding either way.

## Interpretation (signal, not certainty — same binding honesty requirement as iter-39/40)

`faulthandler.register(SIGUSR1, all_threads=True)` was successfully armed (`logs/backend.log`:
`"diagnostic: faulthandler armed on SIGUSR1 (TRENDORA_DIAG_FAULTHANDLER_SIGUSR1=1)"`) and remained armed
for the whole drill, but **the freeze did not recur, so `SIGUSR1` was never sent and the diagnostic was
never exercised for its intended purpose.** This is an honest, valid outcome — TC-5 explicitly allows
"the freeze does not recur and the drill log records that outcome honestly without claiming the freeze is
fixed," and that is exactly the outcome here. iter-39/u's original run-1 freeze remains
**unreproduced and undiagnosed** — this drill does not identify a frozen thread/function, and does not
claim to. What it DOES show: at the identical 2650 MB ceiling, the SAME finalize sequence that
previously either wedged (iter-39 trial 3) or MemoryError'd on `coverage` (iter-40 run 2) this time
completed every aggregate cleanly with real (if modest) memory headroom to spare, and the
newly-extended post-terminal polling window (C8) — the exact window iter-39's wedge appeared in — shows
no health/responsiveness gap at all.

The diagnostic capability itself (SIGUSR1-armed live stack dump) is now in place for the NEXT time a
freeze is caught live, whenever that occurs; it earned no evidence this run because there was nothing to
diagnose.

## Files

- `config.scratch.yaml` — scratch config: throwaway DB url + `memory_cap_mb: 2650` (copied from iter-40,
  never widened).
- `seed_throwaway_db.py` — throwaway-DB seeding (committed seed), copied from iter-40's own script.
- `monitor.py` — iter-40's monitor.py extended (C8): post-terminal polling window, `phase` CSV column.
- `trigger-response.json` — the job-trigger request/response.
- `run1-monitor.out`, `run1-monitor.csv` — this run's full poll log (58 rows: pre- and post-terminal).
- `launch-wrapper.out` — the `start-backend.sh` launcher's own stdout/stderr (host-guard banner, etc.).
