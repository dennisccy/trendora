# Iteration State — ops-hardening

**After iteration:** 68 · **Date:** 2026-08-12 · **Verdict:** CONTINUE

## Journeys

7 passing (J-01 J-03 J-04 J-05 J-06 J-08 J-09) · 1 partial (J-07) — 8 total. Replay 8/8, zero overturns.

## Active blockers

- **Human (owner), 20th round:** does the ≤2 s health-check ceiling apply to a 17-minute job, or only to
  the ~30 s job it was written for? J-07's last gap is exactly this (`docs/goal.md`, 2026-07-31 amendment).
- **Human (owner):** sign-off on the `scripts/automation/browser-qa-phase.sh` ordering bug, and a cost
  sanction — 8th over-budget round (9,933 s pipeline / 10,538 s elapsed vs 3,600 s).
- **Dev:** the slow time is located but not named — 79 % of the one breach and a 79x p90 elevation sit
  inside `GET /api/health`'s own body, which does 3 DB reads + `compute_readiness` + `compute_preflight`
  per request (`apps/backend/app/api/health.py:117-163`). No sub-timing exists yet.

## Last 2 verdicts

- iter 68: CONTINUE — the third watchdog sample named 79.4 % of the one breach (the handler BODY, 0.484 s
  mean during the heaviest phase vs 0.019 s idle); 1,609/1,609 HTTP 200 but 10 over 2.0 s (worst 4.19 s),
  so J-07 stays partial. `test_health.py` finally ran: 17 passed.
- iter 67: CONTINUE — the watchdog named a real component (queue-wait 160x above idle) but explained only
  ~11 % of the single breach; 1 of 1,036 polls over 2.0 s.

## Do not redo

- **Re-running a suspect compute chain in a STANDALONE script** — three null results (iter-52/53, 65, 66).
  Extend the live instrument instead: `apps/backend/app/engine/health_watchdog.py`.
- **A second health-poll counter, JSONL writer, or env flag** — `scripts/qa/poll_health.py`,
  `ledger.append_entry`, `TRENDORA_HEALTH_WATCHDOG` are canonical; both lanes shared the script this round.
- **Re-proving `GET /api/health` is byte-identical with the flag on/off** — `test_health_watchdog.py`
  (11 tests) + `test_health.py` (17 passed, `runs/goal-ops-hardening-iter-68/test_health.log`).
- **Re-deriving iter-67's loop-lag misattribution / phase-distribution correction** — settled and dated in
  `reports/perf-budgets.md` Addendum 34, TC-5/TC-6 (iter-67/a, /b closed).
- **Bounding `factor_lab_all_warm` / `coverage_membership_timeline_refresh` by code change** — diagnostic
  only until the handler-body sub-timing names a component; profile before bounding.
- **Touching `config.yaml` caps, `project-extensions/host-guard/`, or the HOST-GUARD blocks in the launch
  scripts** — owner-set envelope (AG-10), verified clean again this round.
