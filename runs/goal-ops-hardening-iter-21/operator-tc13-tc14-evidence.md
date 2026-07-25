# Operator evidence — TC-13 + TC-14 (owner direction 1, 2026-07-25)

**Produced by:** the goal-mode operator (pump), after the owner chose **direction 1** at the iter-20 STALL —
*"authorize the AG-10-gated ingest so the operator can run TC-13 + TC-14."* Both are now DONE and PASSING.
Full numbers + tables: `reports/perf-budgets.md` § "Post-STALL owner-authorized measurements — TC-13 + TC-14".
Raw poll data: `runs/goal-ops-hardening-iter-21/tc13-backtest-poll.csv`.

Host-guard ritual honored throughout: backend launched via `scripts/start-backend.sh` (`/proc`-verified
affinity `0-3,8-11` + 6144 MB cap); canonical 1 Hz `hwmon` sampler live; thermal watchdog re-armed (peak
89 °C < 95 abort, never tripped); host cooled to 46 °C at start. **AG-9 confirmed:** every ingest ran with
`provider: "seed"` (committed local fixture) — no live network fetch (the `source:"yahoo"` in the POST echo is
a default label only). The full-universe `rebuild` kind was classifier-blocked (correctly, as the heaviest
op); bounded `backfill` kinds were permitted and sufficient.

## TC-13 — `/backtest` ≤1.5 s budget under a concurrent INGEST overlay — **PASS**

6 concurrent `/backtest` pollers, with a real backfill overlay (run id 163, 2026-06-01…2026-07-22, which
finalized and refreshed `forward_aggregates` = a genuine warm during the poll):

- **0 / 4096 breaches** (> 1.5 s), **max 429 ms**, mean 185 ms, p99 387 ms, all HTTP 200 / `ready`.
- vs the iter-16 baseline **11 / 68 breaches @ max 12,655 ms** — a ~30× max-latency improvement under the
  *exact* concurrent-ingest condition that produced the historical worst case.

This is the proof the iters 11–20 latency arc was missing: with the create-once INSERT off the read path
(iter-19) + the historical compute off the request thread (iter-20), `/backtest` no longer contends on the
ingest's SQLite writer lock. **J-08's ingest-overlay budget clause is met.**

## TC-14 — disruptive J-04 kill/restart + checkpoint survival — **PASS**

- **Part A (crash recovery):** `kill -9` the live backend (no clean shutdown) → restart via
  `scripts/start-backend.sh` → health `ok/initializing` → `ok/ready` in ~25 s (honest non-blocking boot, no
  reload, no wedge).
- **Part B (checkpoint survival):** wide backfill (run id 164, 2015-01-01…2026-07-22) checkpointed to
  `dates_done 1366/2904` (`running`, `finished_at: null`); `kill -9` mid-run. After restart, run 164 reads
  **`status: interrupted`, `dates_done: 1366/2904`, `finished_at` stamped by recovery** — the checkpoint
  **survived the hard crash** (non-zero, not reset to defaults), honestly marked *interrupted* (not a fake
  "done", not stuck "running"), with `/api/health` 200 `ready`.

J-04's disruptive kill/restart + checkpoint-survival contract is **freshly proven** (last live-verified
iter-15; owed since then).

## What remains for GOAL_ACHIEVED

Both owner-gated blockers from the iter-20 STALL are cleared. The only open item the iter-20 evaluator named
is the **J-07 transient-contention residual** during the *historical background-compute* window (a bounded,
no-wedge ~1.6 s health / 3–6 s `/backtest` degradation while a cold historical as-of computes off-thread) —
an **owner budget-amendment call**, separate from and not contradicted by TC-13 (which measured the
latest-view budget under an ingest warm, and held). The next evaluator should weigh these two now-passing
proofs against J-06/J-07/J-08.

## Resume note (subagent cap)

The interactive pump conversation that ran iters 16–20 reached the 200-subagent session cap while producing
this evidence, so it cannot itself dispatch the pipeline agents for a fresh iteration. To formally close the
goal, resume with `/goal-resume ops-hardening` in a fresh Claude Code conversation — the new pump will find
this evidence + the perf-budgets section and can drive the evaluator to a GOAL_ACHIEVED verdict (or an
explicit J-07 budget decision) without re-running TC-13/TC-14.
