# Iteration State — ops-hardening

**After iteration:** 67 · **Date:** 2026-08-12 · **Verdict:** CONTINUE

## Journeys

7 passing (J-01 J-03 J-04 J-05 J-06 J-08 J-09) · 1 partial (J-07) — 8 total. Replay 8/8, zero overturns.

## Active blockers

- **Human (owner), 19th round:** does the ≤2 s health-check ceiling apply to an 18-minute job, or only to
  the ~30 s job it was written for? J-07's last gap is exactly this. `docs/goal.md`, "Additional binding
  notes" (2026-07-31 amendment).
- **Human (owner):** sign-off on the `scripts/automation/browser-qa-phase.sh` ordering bug, and a cost
  sanction — 7th over-budget round (10,543 s vs 3,600 s, two real ~18-minute ingest jobs inside it).
- **Dev:** ~2.55 s of the round's one 2.875 s health-check answer is unexplained — it sits inside the
  handler body (readiness/preflight + DB reads), which no instrument times yet
  (`apps/backend/app/api/health.py`, `app/engine/health_watchdog.py`).

## Last 2 verdicts

- iter 67: CONTINUE — the new in-app watchdog worked and named a real component (queue-wait 160x, loop-lag
  23x above idle), but it explains only ~11 % of the single breach; 1 of 1,036 polls over 2.0 s, 0 of 330
  idle, so J-07 stays partial.
- iter 66: CONTINUE — worst drill of the session (70 of 1,024 over 2.0 s), 68 inside `factor_lab_all_warm`;
  the duplicate job-history row was root-caused and fixed.

## Do not redo

- **Re-running a suspect compute chain in a STANDALONE script** — three null results now (iter-65
  `factor_lab_all_warm`, iter-66 `coverage_membership_timeline_refresh`, iter-52/53's sampler). Watch the
  live process instead: `apps/backend/app/engine/health_watchdog.py` already exists to extend.
- **Building a second health-poll counter or a second JSONL writer** — `scripts/qa/poll_health.py` and
  `app.engine.ledger.append_entry` are canonical; the watchdog already reuses both.
- **Re-proving `GET /api/health` is unchanged by the watchdog flag** — fixture-backed equality test at
  `apps/backend/tests/test_health_watchdog.py:422-443`, plus the direct-call shape test.
- **Re-deriving iter-66's breach attribution or its timezone correction** — settled and dated in
  `reports/perf-budgets.md` Addendum 33 (TC-5) and the iter-66 results files (iter-66/a, /c, /d closed).
- **Touching `config.yaml` caps, `project-extensions/host-guard/`, or the launch scripts' HOST-GUARD
  blocks** — owner-set envelope (AG-10), verified clean again this round.
