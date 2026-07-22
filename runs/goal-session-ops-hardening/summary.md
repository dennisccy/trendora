# Goal Session Summary — ops-hardening

**Final verdict:** BUDGET_EXHAUSTED
**Total iterations:** 9
**Wall time (seconds):** 8191
**Quota pauses:** 0
**Started:** 2026-07-19T13:57:02.848410Z
**Finished:** 2026-07-22T00:05:10.052109Z

## Branch

This session pushed iteration commits to `goal/ops-hardening`. Open a PR with:

    gh pr create --base main --head goal/ops-hardening \
      --title "feat: ops-hardening — BUDGET_EXHAUSTED" \
      --body-file runs/goal-session-ops-hardening/summary.md

## Final journey state

| Journey | Status | Last passing iter |
|---|---|---|
| J-01 | unknown | goal-ops-hardening-iter-7 |
| J-03 | unknown | goal-ops-hardening-iter-7 |
| J-04 | unknown | goal-ops-hardening-iter-7 |
| J-05 | regressed | goal-ops-hardening-iter-6 |
| J-06 | partial | - |

## Anti-goal violations

- [critical] AG-3: A journey passes ONLY if the displayed numbers are correct — they match the engine's computation for the same as-of date — not merely that the page renders. (iter goal-ops-hardening-iter-1)
- [critical] AG-3: A journey passes ONLY if the displayed numbers are correct — they match the engine's computation for the same as-of date — not merely that the page renders. (iter goal-ops-hardening-iter-2)
- [minor] AG-3 (dimension): displayed numbers must be correct — a fetch that lands new bars silently blanks the DEFAULT /data coverage panel to false all-zeros. (iter goal-ops-hardening-iter-2)
- [critical] AG-8 — Resilience to data-shape and data-scale change: widening the data basis (deeper history) must never crash an existing page or exhaust a service's memory; the UI degrades gracefully (contained error boundary, honest '—'/NA placeholder, never a blank/frozen frame); unbounded whole-table ORM loads forbidden on the deep basis. (iter goal-ops-hardening-iter-7)
- [minor] AG-10 — Host resource ceiling (hardware protection): heavy compute MUST be launched only via the project launch scripts (scripts/dev.sh / scripts/start-backend.sh), and those scripts MUST apply the host caps declared in project-extensions/host-guard/host-guard.env whenever that file is present (CPU-affinity mask, BLAS/OMP thread caps, memory_cap_mb, malloc_arena_max). (iter goal-ops-hardening-iter-8)

## Telemetry

See `runs/goal-session-ops-hardening/telemetry.jsonl` for the structured event log.

## Iteration timing

```
== Wall-time report: session ops-hardening
  goal-ops-hardening-iter-0  depth=?  verdict=?  wall=?  (incomplete/interrupted attempt)
      goal-decomposer              0.3m  calls=1  failures=1
      pump-wait                  0.3m
  goal-ops-hardening-iter-0  depth=lean  verdict=?  wall=?  (incomplete/interrupted attempt)
      browser-qa-agent            37.5m  calls=1
      goal-decomposer             10.4m  calls=1
      developer                    9.1m  calls=1
      reviewer                     4.2m  calls=1
      goal-evaluator               0.0m  calls=1  failures=1
      pump-wait                  0.4m
  goal-ops-hardening-iter-0  depth=lean  verdict=CONTINUE  wall=9.3m
      goal-evaluator               9.3m  calls=1
      (resume-skipped: goal-decomposer, developer, reviewer, browser-qa)
      pump-wait                  0.1m
      unattributed (glue)        0.0m
  goal-ops-hardening-iter-1  depth=full  verdict=CONTINUE  wall=241.5m
      goal-decomposer             16.4m  calls=1
      goal-evaluator              12.1m  calls=1
      coherence-auditor            6.3m  calls=1
      iteration-summarizer         6.3m  calls=1
      pump-wait                 18.9m
      unattributed (glue)      200.4m
  goal-ops-hardening-iter-2  depth=full  verdict=CONTINUE  wall=646.9m
      goal-decomposer             18.5m  calls=1
      iteration-summarizer        18.5m  calls=1
      goal-evaluator              15.5m  calls=1
      coherence-auditor            6.4m  calls=1
      readme-maintainer            3.4m  calls=1
      pump-wait                226.9m
      unattributed (glue)      584.5m
  goal-ops-hardening-iter-3  depth=full  verdict=CONTINUE  wall=259.8m
      goal-evaluator              15.6m  calls=1
      iteration-summarizer        14.1m  calls=1
      goal-decomposer             14.1m  calls=1
      readme-maintainer            7.7m  calls=1
      coherence-auditor            4.0m  calls=1
      pump-wait                  1.7m
      unattributed (glue)      204.3m
  goal-ops-hardening-iter-4  depth=full  verdict=CONTINUE  wall=276.2m
      iteration-summarizer        16.0m  calls=1
      goal-decomposer             16.0m  calls=1
      goal-evaluator              12.1m  calls=1
      readme-maintainer            6.9m  calls=1
      coherence-auditor            4.4m  calls=1
      pump-wait                  2.7m
      unattributed (glue)      220.8m
  goal-ops-hardening-iter-5  depth=full  verdict=?  wall=?  (incomplete/interrupted attempt)
      goal-decomposer             14.5m  calls=1
      iteration-summarizer        14.5m  calls=1
      readme-maintainer            3.4m  calls=1
      pump-wait                 26.3m
  goal-ops-hardening-iter-5  depth=full  verdict=CONTINUE  wall=32.6m
      goal-evaluator              10.6m  calls=1
      coherence-auditor            2.8m  calls=1
      (resume-skipped: goal-decomposer)
      pump-wait                  0.7m
      unattributed (glue)       19.3m
  goal-ops-hardening-iter-6  depth=full  verdict=CONTINUE  wall=252.8m
      goal-evaluator              12.0m  calls=1
      iteration-summarizer         9.9m  calls=1
      goal-decomposer              9.9m  calls=1
      coherence-auditor            3.9m  calls=1
      readme-maintainer            1.5m  calls=1
      pump-wait                  1.2m
      unattributed (glue)      215.6m
  goal-ops-hardening-iter-7  depth=full  verdict=REGRESSION  wall=304.9m
      iteration-summarizer        15.3m  calls=2
      goal-evaluator              10.9m  calls=1
      goal-decomposer             10.2m  calls=1
      readme-maintainer            4.0m  calls=2
      coherence-auditor            2.8m  calls=1
      pump-wait                  1.6m
      unattributed (glue)      261.7m
  goal-ops-hardening-iter-8  depth=full  verdict=?  wall=?  (incomplete/interrupted attempt)
      goal-decomposer             11.5m  calls=1
      pump-wait                  0.6m
  goal-ops-hardening-iter-8  depth=full  verdict=CONTINUE  wall=130.4m
      goal-evaluator              11.1m  calls=1
      coherence-auditor            3.2m  calls=1
      (resume-skipped: goal-decomposer)
      pump-wait                  1.7m
      unattributed (glue)      116.1m
  session: 9 completed iteration(s), mean wall 239.4m
      total goal-decomposer            121.8m
      total goal-evaluator             109.1m
      total iteration-summarizer        94.7m
      total browser-qa-agent            37.5m
      total coherence-auditor           33.7m
      total readme-maintainer           26.8m
      total developer                    9.1m
      total reviewer                     4.2m
      total AWAITING_PUMP paused gaps: 9.7m
      halts: AWAITING_PUMP, AWAITING_PUMP, REGRESSION_HALT, BUDGET_EXHAUSTED
```
