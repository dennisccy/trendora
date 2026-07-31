# iter-40 — post-fix wedge-recurrence drill (TC-2 / TC-3)

Re-checks iter-39 trial 3's wedge (`_missing_data_diagnostic` uncaught `MemoryError` inside
`cursor._raw_all_rows()`, `data_manager.py:271`) against THIS iteration's fix (streamed via
`.yield_per(cfg.research.read_batch_size)`), at the SAME cap family iter-39 used (2650 MB), never
widened (binding iter-38 lesson). Launched only via `scripts/start-backend.sh` (AG-10), throwaway DB
seeded offline from the committed seed (AG-9), never the live product DB.

## Two runs

**Run 1 (confounded — kept as a secondary artifact, not authoritative).** The backfill job was
triggered immediately once `/api/health` first answered 200, while the boot warmup thread
(`warmup.py::_run_warmup`) was still mid-flight — TWO independent heavy consumers (warmup's own
coverage-snapshot warm, which also calls the fixed function, plus the triggered job's own ~1.1 GB
bar-cache prefill) competed for the same 2650 MB ceiling at once. The process wedged (all 14 threads in
`futex_do_wait`, 0 CPU-tick delta over a 3 s sample, `VmPeak` pinned at 2,713,600 kB — identical to
iter-39's own trial-3 reading) roughly 75+ s after an uncaught `"Exception ignored in thread started by:
<object repr() failed>\nMemoryError:"` line with NO preceding traceback (unlike iter-39's trial 3, whose
evidence captured a traceback naming the exact site). `gdb -p <pid> -batch -ex "thread apply all bt"` was
attempted to positively identify the blocked thread; this host's `yama.ptrace_scope` policy denies
non-root attach (`Could not attach to process ... Inappropriate ioctl for device`), and no `py-spy` was
installed (not added mid-drill to avoid an unplanned new dependency). The dying thread in run 1 was
**not** positively identified — full details and the reasoning for why this run does not answer TC-2/TC-3
on its own: `run1-notes.md`. Process killed (`kill -9`, confirmed exit 137) after ~3.5 min of confirmed
non-recovery. Superseded by run 2 below, which corrects the trigger-timing bug (my own test-setup error,
not a re-tuning of the cap — same 2650 MB both runs).

**Run 2 (clean — authoritative).** This time the job was triggered only after `GET /api/health` reported
`"readiness":"ready"` (warmup fully settled, 89/89, `"status":"ok"`) — the same single-job shape iter-39's
trial 3 exercised. `trigger-response.json` here is run 1's (both runs used the identical
`{"kind":"backfill","start":"2026-06-16","end":"2026-06-18","source":"yahoo"}` request); run 2's own job
id is `b447496315604ef0ab39e76aa93b3109`, PID `1313338`, `CHAIN_BACKEND_PORT=18261`,
`PYTHONFAULTHANDLER=1` (diagnostic-only launch env, added for a stack dump if the wedge recurred again —
it did not, so it was never needed).

### Result: the wedge did NOT recur

- **Job finished `status: ok`** in 35.9 s total, `aggregates_refreshed: ["latest_snapshot", "market_phase",
  "forward_aggregates", "research_hot_keys", "index_series", "drawdown_expectations"]` — `coverage` is
  honestly absent (see below), `membership_timeline` had already been warmed by boot and was not re-run.
- **`GET /api/health` answered 200 on all 28 polls, 0 non-200, max inter-poll gap 1.826 s** — well under
  budget, no unresponsive window at any point (`run2-monitor.csv`, `run2-monitor.out`).
- **`VmPeak` peaked at exactly 2,713,600 kB (2650 MB, the declared cap) and never exceeded it** — the
  process stayed alive and fully responsive throughout, confirmed by a follow-up `GET /api/health` after
  the job reached `ok`.
- **A `MemoryError` DID fire once** (live log, `run2-live-log-lines-149620-149729.txt`, lines 149620-149729
  of the cumulative `logs/backend.log`) — but at a DIFFERENT, much earlier site than iter-39's trial 3:
  `_compute_coverage_body`'s `symbol_count = session.scalar(select(func.count(func.distinct(DailyPrice.
  symbol))))` (`data_manager.py:898`), a small COUNT-DISTINCT aggregate that itself allocates almost
  nothing — the process was already sitting at the 2650 MB ceiling from other work by the time this line
  ran, so essentially ANY further allocation would have failed here first. **`_missing_data_diagnostic` /
  `data_manager.py:271` / `_raw_all_rows` do NOT appear anywhere in this traceback** — the fixed call was
  never reached this time, let alone blamed (TC-2's literal assertion, satisfied).
  - This MemoryError was CAUGHT by the EXISTING single non-per-item handler in `_refresh_ingest_
    aggregates` (`"ingest coverage/membership-timeline refresh failed (non-fatal)"` — the SAME handler
    iter-39's own trial 2 (2700 MB) demonstrated catching a `_missing_data_diagnostic` MemoryError). The
    job continued and finished cleanly afterward — `forward_aggregates` and `drawdown_expectations` both
    completed normally on the SAME run, exactly the per-item-isolation behavior the acceptance clause
    requires. `coverage` is the one item honestly absent from `aggregates_refreshed` (its own compute
    failed and was isolated, not silently marked done).

### Interpretation (signal, not certainty — per this iteration's own binding instruction)

This is consistent with — but does not by itself PROVE with certainty — the hypothesis that iter-39
trial 3's wedge was caused by the fixed allocation (`_missing_data_diagnostic`'s whole-result
materialization). What it DOES show directly: at the identical 2650 MB ceiling and the identical
single-job shape, the SAME finalize sequence that previously wedged now (a) never reaches the old
uncaught-materialization site at all, (b) still hits SOME memory pressure at this tight a cap (expected —
2650 MB is only ~84.6 MB above the measured prefill/compute-done baseline), and (c) that pressure is
now fully absorbed by the existing non-fatal isolation handler with zero downtime. No new uncaught
MemoryError, no wedge, no restart. Run 1's inconclusive (confounded) result is retained rather than
discarded, per this iteration's own honesty requirement — it is NOT read as evidence the wedge recurred
under the SAME conditions iter-39 measured, because it was not the same conditions.

## Files

- `config.scratch.yaml` — scratch config: throwaway DB url + `memory_cap_mb: 2650` (same cap family as
  iter-39 trial 3, never widened).
- `seed_throwaway_db.py` — throwaway-DB seeding (committed seed, `scanner_results` bulk-relabeled
  `"Avoid"`, iter-34 lesson), adapted from `../../goal-ops-hardening-iter-39/mem-drill/seed_throwaway_db.py`.
- `monitor.py` — the unchanged iter-39 1 Hz health/VmPeak/job-status poller (`../../goal-ops-hardening-
  iter-39/mem-drill/monitor.py`, copied verbatim).
- `run1-notes.md`, `run1-log-tail-at-wedge.txt` — the confounded first run (kept for honesty, not
  authoritative).
- `run2-monitor.csv`, `run2-monitor.out`, `run2-live-log-lines-149620-149729.txt` — the clean, authoritative
  run's evidence.
- `trigger-response.json` — the job-trigger request/response shape (identical both runs).
