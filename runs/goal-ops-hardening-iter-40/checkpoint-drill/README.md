# iter-40 — live checkpoint-honesty kill -9 drill (TC-4)

Re-proves iter-39/w's checkpoint-cadence fix (`_RUN_RECORD_CHECKPOINT_INTERVAL_S` tightened 10.0 -> 1.0,
`apps/backend/app/engine/data_manager.py:~4055`) with a fresh live `kill -9` + restart cycle. Launched
only via `scripts/start-backend.sh` (AG-10), throwaway DB seeded offline from the committed seed (AG-9),
committed `memory_cap_mb` (6144 — this drill is about checkpoint timing, not memory pressure, so the cap
was left untouched).

## Method

1. `seed_throwaway_db.py` loads the committed seed into `drill.db` and reports a K=25-trading-day window
   (`2026-03-30` → `2026-05-04`) at least 8 trading days before the seed's own latest date.
2. Backend launched on a dedicated port; the drill waits for `GET /api/health`'s `"readiness":"ready"`
   (warmup fully settled) before triggering anything, so the measurement isn't confounded by a concurrent
   boot warmup thread (see `../wedge-drill/run1-notes.md` for why that confound matters).
3. `trigger_and_poll_and_kill.py` — a single script that POSTs the backfill job AND immediately starts
   polling `GET /api/data/jobs/{id}` every 0.1 s, so there is no round-trip gap between an orchestrating
   shell's trigger call and a separately-launched poller (the drill's own first attempt, discarded,
   lost the whole mid-flight window that way — the 20-date job finished between two separate tool calls
   before a separately-started poller ever got its first sample). The instant the polled `dates_done`
   first reaches the chosen kill threshold (12 of 25), the SAME script sends `kill -9` to the backend PID
   and records that instant as **M** (`trigger-poll-kill.csv`, `trigger-poll-kill.out`).
4. Backend restarted (same config, same `drill.db`) via `scripts/start-backend.sh` again. Boot's
   `sweep_orphaned_runs` (J-60) flips the still-`running` row to `interrupted` on the next boot, exactly
   as designed.
5. The persisted row for that `job_id` read DIRECTLY from `drill.db`'s `data_provider_runs` table
   (`post-restart-persisted-row.txt`) — the SAME row `GET /api/data`'s Run History panel reads through
   `recent_runs`/`summarize_provider_run`, just read at the source for verification precision.

## Result

- **M (true in-memory progress at kill time, independently polled): 12 of 25 dates.**
  `KILLED_AT_M=12 t=26.590s pid=1343648` (`trigger-poll-kill.out`) — the poll immediately before the kill
  read `dates_done=12`; the kill fired within the SAME 0.1 s poll tick, before another `GET /api/data/jobs`
  round-trip could pass.
- **Persisted `dates_done` after restart: 11** (`post-restart-persisted-row.txt`, job `367704f472084be2
  afbf991bf49126ae`, row id 3, `status: interrupted`).
- **Gap: 1 date** — the persisted figure is one date behind the true kill-time progress, not an
  order-of-magnitude gap. iter-39's own live drill (`../../goal-ops-hardening-iter-39/live-restart/
  kill-test-mid-flight-state.json` vs `pre-kill-runs-state.json`) measured 18/18 in memory against a
  persisted row still in single digits — the exact honesty gap this fix (10.0 s → 1.0 s interval) exists
  to close. This run's 1-date gap is well within "one checkpoint interval" of true progress for a job whose
  per-date burst rate (~120-140 ms/date once the shared bar-cache prefill finished — see the CSV's rapid
  `dates_done` ticks from t=24.037s onward) is far faster than the OLD 10 s throttle could ever track
  honestly, and the NEW 1.0 s throttle tracks closely.
- The persisted detail also shows the run-summary contract holding through an interrupted state:
  `snapshots_created: 10`, `already_snapshotted: 1`, `error_other: 0` — `10 + 1 + 0 = 11 = dates_done`,
  consistent (a `kill -9` mid-run never leaves the persisted counts internally contradictory).

## Files

- `config.scratch.yaml` — scratch config: throwaway DB url only (committed `memory_cap_mb: 6144`
  unchanged — this drill is not a memory-pressure test).
- `seed_throwaway_db.py` — throwaway-DB seeding (K=25 non-current trading days).
- `trigger_and_poll_and_kill.py` — the combined trigger+poll+kill script (the corrected methodology).
- `poll_and_kill.py`, `poll-and-kill.out` — the FIRST attempt's poll-only script; discarded (job `bd9a9a
  39d0334fa8a1e666ab6deee25b` had already reached `dates_done=20/20` by the time a SEPARATELY-launched
  poller took its first sample — a round-trip-delay artifact of orchestrating trigger and poll as two
  separate tool calls, not a product behavior). Kept for the honesty trail, not used as evidence.
- `trigger-poll-kill.csv`, `trigger-poll-kill.out` — the authoritative run's poll log + summary.
- `post-restart-persisted-row.txt` — the persisted `data_provider_runs` row read directly from `drill.db`
  after restart.
