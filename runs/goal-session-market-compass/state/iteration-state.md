# Iteration State — market-compass

**After iteration:** 24 · **Date:** 2026-08-28 · **Verdict:** ESCALATE

## Journeys

4 passing (J-01 J-04 J-10 J-11) · 5 partial (J-02 J-03 J-05 J-06 J-09) · 2 failing (J-07 J-08) — 11 total

## Active blockers

- **NONE human-owned.** Owner ruling items 5+6 (`docs/goal.md:2194`, uncommitted): product work resumes
  now, no further authorization; do not STALL for reversible cleanup. Anti-goal ledger: 0 unresolved.
- **DEV — the replay lane silently skipped this iteration's regression re-test.** `replay_lane_spec_journeys`
  (`lib/replay-lane.sh:75-77`) takes the FIRST line matching `Required-still-passing`; iter-24's spec line 21
  mentions the phrase in prose (no `J-NN`) before the real bullet at line 23 → `REQUIRED_JOURNEYS` EMPTY,
  `_use_replay=no`, J-01/J-04/J-10 NOT re-tested, logged only as a benign "replay: no". Fix parse + prose.
- **DEV — depth demoted again** (5th time: iters 2, 6, 8, 23, 24). Spec said `Depth: full`, arbiter forced
  lean (`full-cap`). Next spec MUST carry `Depth enforcement: required` — it outranks the cost rung. Do NOT
  re-arm `CHAIN_REQUIRE_FULL_DEPTH`/`CHAIN_MAINTENANCE_ISOLATION` (standing owner guidance).
- Non-blocking: the 7.8 GB clone at `runs/goal-market-compass-iter-23/verify-clone/` may now be deleted (ruling item 4); J-04's capture still crops above the candidate card (`evidence_makeup`).

## Last 2 verdicts

- iter 24: ESCALATE — the authorized launcher fix landed and I verified it (18/18 test, refusal observed,
  canonical DB byte-untouched), but the regression safety net silently vanished and no auditor ran.
- iter 23: STALLED — J-11's clone-backed serving verification PASSED and J-11 closed, but the same run
  silently booted and wrote to the protected canonical database; every fix path needed the owner.

## Do not redo

- **J-11 is CLOSED, re-confirmed against the CURRENT goal text** (new `spec_hash 012568db…`): Stages D–G, the clone-backed serving check and the goal-edit drift are all settled. Do not reopen or re-verify.
- **Launcher fix DONE + verified**: `goal_iter_lock_backend_launch_context` + `ensure_services_running` drift
  guard (`lib/common.sh`), `tests/automation/test-backend-launch-context.sh` (18/18). RESIDUAL: it guarantees
  launch-context CONSISTENCY, not canonical-DB PROTECTION — an isolated run must still supply
  `CHAIN_START_BACKEND_CMD`/`TRENDORA_CONFIG` BEFORE the iteration starts.
- **The 10 iter-23 cache rows stay in place** — owner ruling item 2 forbids cleanup writes. Do not delete.
- **Clone tooling exists and works** — `app/engine/j11_disposable_clone.py`, `run_j11_disposable_clone.py`, `scripts/start-backend-j11-verify.sh`. Reuse it, do not rebuild.
- `scripts/`+`tests/` are tracked SYMLINKS into `incredible_auto_dev/` — one file, never "patch both". A
  `.db` sha256 does NOT prove a WAL-mode DB unchanged (bracket `.db`+`-wal`+`-shm`). `/market` 404 = J-08 gap.
- **Next target is J-09** (host resource-fit — config value + measurement), per the goal file's build order.
