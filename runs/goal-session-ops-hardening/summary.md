# Goal Session Summary — ops-hardening

**Final verdict:** AWAITING_PUMP
**Total iterations:** 39
**Wall time (seconds):** 2390
**Quota pauses:** 0
**Started:** 2026-07-19T13:57:02.848410Z
**Finished:** 2026-07-30T22:14:55.337946Z

## Branch

This session pushed iteration commits to `goal/ops-hardening`. Open a PR with:

    gh pr create --base main --head goal/ops-hardening \
      --title "feat: ops-hardening — AWAITING_PUMP" \
      --body-file runs/goal-session-ops-hardening/summary.md

## Final journey state

| Journey | Status | Last passing iter |
|---|---|---|
| J-01 | passing | goal-ops-hardening-iter-38 |
| J-03 | passing | goal-ops-hardening-iter-38 |
| J-04 | passing | goal-ops-hardening-iter-37 |
| J-05 | passing | goal-ops-hardening-iter-38 |
| J-06 | passing | goal-ops-hardening-iter-38 |
| J-07 | partial | goal-ops-hardening-iter-34 |
| J-08 | passing | goal-ops-hardening-iter-38 |
| J-09 | passing | goal-ops-hardening-iter-38 |

## Anti-goal violations

- [critical] AG-3: A journey passes ONLY if the displayed numbers are correct — they match the engine's computation for the same as-of date — not merely that the page renders. (iter goal-ops-hardening-iter-1)
- [critical] AG-3: A journey passes ONLY if the displayed numbers are correct — they match the engine's computation for the same as-of date — not merely that the page renders. (iter goal-ops-hardening-iter-2)
- [minor] AG-3 (dimension): displayed numbers must be correct — a fetch that landed zero rows must not present as a success. (iter goal-ops-hardening-iter-2)
- [critical] AG-8 — Resilience to data-shape and data-scale change: widening the data basis must never crash an existing page or exhaust a service's memory; unbounded whole-table ORM loads are forbidden on the deep basis. (iter goal-ops-hardening-iter-7)
- [minor] AG-10 — Host resource ceiling (hardware protection): heavy compute MUST be launched only via the project launch scripts, which must apply the declared host caps. (iter goal-ops-hardening-iter-8)
- [critical] AG-8 (distinct dimension) — Resilience to data-shape and data-scale change: unbounded whole-table ORM materialization on the forward-aggregate warm path. (iter goal-ops-hardening-iter-9)
- [minor] AG-10 — Host resource ceiling: heavy compute (backfills, full-universe rebuilds, measurement passes) MUST be launched only via the project launch scripts. (iter goal-ops-hardening-iter-10)
- [critical] AG-8 (iter-9 forward_aggregates dimension) — observed-severity escalation: the unbounded load wedged the service on the deep basis. (iter goal-ops-hardening-iter-13)
- [minor] AG-10 — Host resource ceiling: heavy compute MUST be launched only via the project launch scripts (operator process lapse: raw uvicorn on a throwaway port; disclosed and corrected via start-backend.sh, no launch script modified). (iter goal-ops-hardening-iter-17)
- [minor] AG-8 — Resilience to data-shape and data-scale change: widening the data basis (deeper history) must never crash an existing page; the UI degrades gracefully, never a blank application-error page. (iter goal-ops-hardening-iter-26)
- [minor] AG-3: A journey passes ONLY if the displayed numbers are correct — they match the engine's computation for the same as-of date — not merely that the page renders. (iter goal-ops-hardening-iter-26)
- [minor] AG-8 - Resilience to data-shape and data-scale change: widening the data basis (deeper history) must never crash an existing page or exhaust a service's memory - the UI degrades gracefully (contained error boundary, honest '-'/NA placeholder, never a blank application-error page), and unbounded whole-table ORM loads are forbidden on the deep basis. (iter goal-ops-hardening-iter-27)
- [minor] AG-8 - Resilience to data-shape and data-scale change: widening the data basis must never crash an existing page or exhaust a service's memory - the UI degrades gracefully (contained error boundary, honest '-'/NA placeholder, never a blank application-error page), and unbounded whole-table ORM loads are forbidden on the deep basis. (iter goal-ops-hardening-iter-29)
- [minor] AG-8 - Resilience to data-shape and data-scale change: widening the data basis must never exhaust a service's memory; unbounded whole-table ORM loads are forbidden on the deep basis. (Also goal.md Success Criteria: 'No unbounded whole-table loads: no code path streams the full daily_prices table into RAM'.) (iter goal-ops-hardening-iter-29)
- [minor] AG-8 - Resilience to data-shape and data-scale change: widening the data basis must never exhaust a service's memory; unbounded whole-table ORM materialization is forbidden on the warm or serving path. (iter goal-ops-hardening-iter-29)
- [minor] goal.md Success Criteria + Compute-at-ingest constraint: 'No unbounded whole-table loads: no code path streams the full daily_prices table into RAM' (AG-8's deep-basis clause). (iter goal-ops-hardening-iter-29)
- [minor] AG-8 - Resilience to data-shape and data-scale change: widening the data basis (new nulls, broader pools, deeper history) must never crash an existing page or exhaust a service's memory; unbounded whole-table ORM loads are forbidden on the deep basis. (iter goal-ops-hardening-iter-31)
- [minor] AG-8 - Resilience to data-shape and data-scale change: unbounded whole-table ORM loads are forbidden on the deep basis. (iter goal-ops-hardening-iter-32)
- [minor] AG-8 - Resilience to data-shape and data-scale change: widening the data basis (new nulls, broader pools, deeper history) must never crash an existing page or exhaust a service's memory - every existing consumer of a widened field is re-validated, the UI degrades gracefully (contained error boundary, honest '-'/NA placeholder, never a blank application-error page). (iter goal-ops-hardening-iter-33)
- [minor] AG-8 - Resilience to data-shape and data-scale change: the UI degrades gracefully (contained error boundary, honest '-'/NA placeholder, never a blank application-error page). (iter goal-ops-hardening-iter-33)
- [minor] AG-10 - Host resource ceiling (hardware protection): heavy compute - backfills, full-universe rebuilds, measurement passes, load drills, test-suite bursts - MUST be launched only via the project launch scripts, and those scripts MUST apply the host caps declared in project-extensions/host-guard/host-guard.env whenever that file is present. (iter goal-ops-hardening-iter-33)
- [minor] J-07 step 2 (docs/goal.md, Must-have journeys) + the committed `GET /api/health` <= 0.1 s budget in reports/perf-budgets.md: 'While step 1 runs, poll GET /api/health once per second; assert every poll answers HTTP 200 within its existing budget - no frozen or unresponsive window.' (iter goal-ops-hardening-iter-34)
- [minor] AG-8 - Resilience to data-shape and data-scale change: widening the data basis (new nulls, broader pools, deeper history) must never crash an existing page or exhaust a service's memory. Also J-07 step 3 (docs/goal.md, Must-have journeys): 'Record the process's peak memory (VmPeak) during step 1; assert it stays under the declared server.memory_cap_mb, with the margin recorded in reports/perf-budgets.md.' (iter goal-ops-hardening-iter-35)
- [minor] AG-8 - Resilience to data-shape and data-scale change: unbounded whole-table ORM loads are forbidden on the deep basis. Also docs/goal.md Success Criteria: 'No unbounded whole-table loads: no code path streams the full daily_prices table into RAM', and J-07's own Acceptance clause 'no unbounded whole-table ORM materialization remains on the warm or serving path'. (iter goal-ops-hardening-iter-36)
- [minor] AG-10 - Host resource ceiling (hardware protection): the ceilings are a physical constraint of the current host (repeated instant hardware resets under vectorized ingest bursts), not a performance budget to optimize away. Also AG-8's 'must never exhaust a service's memory' clause. (iter goal-ops-hardening-iter-36)
- [minor] AG-3: A journey passes ONLY if the displayed numbers are correct - they match the engine's computation for the same as-of date - not merely that the page renders. (iter goal-ops-hardening-iter-36)
- [minor] AG-8 — Resilience to data-shape and data-scale change: widening the data basis must never crash an existing page or exhaust a service's memory; unbounded whole-table ORM loads are forbidden on the deep basis. Also J-07 step 1 (docs/goal.md): 'trigger the forward-aggregate warm for every configured horizon (the ingest finalize path)' and step 4: re-verify the induced-pressure drill against the paths bounded by this iteration. (iter goal-ops-hardening-iter-37)
- [minor] AG-8 — Resilience to data-shape and data-scale change: widening the data basis must never crash an existing page or exhaust a service's memory. (J-07's own headline: heavy aggregates never take the service down.) (iter goal-ops-hardening-iter-37)
- [minor] AG-8 — Resilience to data-shape and data-scale change: ... the UI degrades gracefully (contained error boundary, honest '—'/NA placeholder, never a blank application-error page). Also J-07 step 4: the SAME process 'keeps serving GET /api/health and previously cached reads'. (iter goal-ops-hardening-iter-37)
- [minor] docs/goal.md Success Criteria ('measured, recorded in reports/perf-budgets.md') + .claude/core.md evidence honesty: a number presented as measured must be the number the instrument actually produced. (iter goal-ops-hardening-iter-38)
- [minor] docs/goal.md J-07 step 4 (verbatim): 'Induce memory pressure during a warm (test hook or a tightened cap in a throwaway process); assert the warm aborts honestly per the existing isolation convention while the SAME process keeps serving GET /api/health and previously cached reads - never a deadlock, wedge, or restart requirement.' (iter goal-ops-hardening-iter-38)
- [minor] docs/goal.md Must-have user journeys (the required-still-passing set must stay green) + the iteration spec's TC-11 ('zero FAIL rows and zero reconciliation overturns'). (iter goal-ops-hardening-iter-38)

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
      unattributed (glue)        0.0m  (wall − agents(active) − quota)
  goal-ops-hardening-iter-1  depth=full  verdict=CONTINUE  wall=241.5m
      goal-decomposer             16.4m  calls=1
      goal-evaluator              12.1m  calls=1
      coherence-auditor            6.3m  calls=1
      iteration-summarizer         6.3m  calls=1
      pump-wait                 18.9m
      unattributed (glue)      200.4m  (wall − agents(active) − quota)
  goal-ops-hardening-iter-2  depth=full  verdict=CONTINUE  wall=646.9m
      goal-decomposer             18.5m  calls=1
      iteration-summarizer        18.5m  calls=1
      goal-evaluator              15.5m  calls=1
      coherence-auditor            6.4m  calls=1
      readme-maintainer            3.4m  calls=1
      pump-wait                226.9m
      unattributed (glue)      584.5m  (wall − agents(active) − quota)
  goal-ops-hardening-iter-3  depth=full  verdict=CONTINUE  wall=259.8m
      goal-evaluator              15.6m  calls=1
      iteration-summarizer        14.1m  calls=1
      goal-decomposer             14.1m  calls=1
      readme-maintainer            7.7m  calls=1
      coherence-auditor            4.0m  calls=1
      pump-wait                  1.7m
      unattributed (glue)      204.3m  (wall − agents(active) − quota)
  goal-ops-hardening-iter-4  depth=full  verdict=CONTINUE  wall=276.2m
      iteration-summarizer        16.0m  calls=1
      goal-decomposer             16.0m  calls=1
      goal-evaluator              12.1m  calls=1
      readme-maintainer            6.9m  calls=1
      coherence-auditor            4.4m  calls=1
      pump-wait                  2.7m
      unattributed (glue)      220.8m  (wall − agents(active) − quota)
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
      unattributed (glue)       19.3m  (wall − agents(active) − quota)
  goal-ops-hardening-iter-6  depth=full  verdict=CONTINUE  wall=252.8m
      goal-evaluator              12.0m  calls=1
      iteration-summarizer         9.9m  calls=1
      goal-decomposer              9.9m  calls=1
      coherence-auditor            3.9m  calls=1
      readme-maintainer            1.5m  calls=1
      pump-wait                  1.2m
      unattributed (glue)      215.6m  (wall − agents(active) − quota)
  goal-ops-hardening-iter-7  depth=full  verdict=REGRESSION  wall=304.9m
      iteration-summarizer        15.3m  calls=2
      goal-evaluator              10.9m  calls=1
      goal-decomposer             10.2m  calls=1
      readme-maintainer            4.0m  calls=2
      coherence-auditor            2.8m  calls=1
      pump-wait                  1.6m
      unattributed (glue)      261.7m  (wall − agents(active) − quota)
  goal-ops-hardening-iter-8  depth=full  verdict=?  wall=?  (incomplete/interrupted attempt)
      goal-decomposer             11.5m  calls=1
      pump-wait                  0.6m
  goal-ops-hardening-iter-8  depth=full  verdict=CONTINUE  wall=130.4m
      goal-evaluator              11.1m  calls=1
      coherence-auditor            3.2m  calls=1
      (resume-skipped: goal-decomposer)
      pump-wait                  1.7m
      unattributed (glue)      116.1m  (wall − agents(active) − quota)
  goal-ops-hardening-iter-9  depth=full  verdict=CONTINUE  wall=648.7m
      goal-evaluator              11.6m  calls=1
      goal-decomposer              7.8m  calls=1
      coherence-auditor            4.3m  calls=1
      pump-wait                  8.4m
      unattributed (glue)      625.0m  (wall − agents(active) − quota)
  goal-ops-hardening-iter-10  depth=lean  verdict=CONTINUE  wall=110.6m
      browser-qa-agent            62.3m  calls=1
      developer                   20.1m  calls=1
      goal-evaluator              13.1m  calls=1
      goal-decomposer              9.8m  calls=1
      iteration-summarizer         9.8m  calls=1
      reviewer                     2.3m  calls=1
      readme-maintainer            2.0m  calls=1
      coherence-auditor            2.0m  calls=1
      (resume-skipped: coherence-auditor)
      pump-wait                  1.7m
      overlap saved             10.9m  (parallel steps)
  goal-ops-hardening-iter-11  depth=lean  verdict=ESCALATE  wall=81.3m
      developer                   25.5m  calls=1
      browser-qa-agent            17.5m  calls=1
      goal-evaluator              17.2m  calls=1
      goal-decomposer             10.4m  calls=1
      iteration-summarizer         4.7m  calls=1
      coherence-auditor            2.4m  calls=1
      reviewer                     1.9m  calls=1
      readme-maintainer            1.4m  calls=1
      (resume-skipped: coherence-auditor)
      pump-wait                  3.1m
      unattributed (glue)        0.3m  (wall − agents(active) − quota)
  goal-ops-hardening-iter-12  depth=full  verdict=CONTINUE  wall=179.2m
      goal-decomposer             11.5m  calls=1
      goal-evaluator              11.0m  calls=1
      iteration-summarizer         4.8m  calls=1
      coherence-auditor            2.6m  calls=1
      pump-wait                  1.9m
      unattributed (glue)      149.3m  (wall − agents(active) − quota)
  goal-ops-hardening-iter-13  depth=full  verdict=REGRESSION  wall=279.7m
      iteration-summarizer        19.4m  calls=2
      goal-decomposer             14.2m  calls=1
      goal-evaluator              12.2m  calls=1
      coherence-auditor            3.3m  calls=1
      readme-maintainer            2.0m  calls=1
      pump-wait                  1.6m
      unattributed (glue)      228.4m  (wall − agents(active) − quota)
  goal-ops-hardening-iter-14  depth=full  verdict=CONTINUE  wall=251.4m
      goal-evaluator              22.7m  calls=1
      goal-decomposer             21.6m  calls=1
      coherence-auditor            4.4m  calls=1
      [engine] full-pipeline     202.6m  (contains agent time above)
      [engine] showcase-join       0.0m  (contains agent time above)
      pump-wait                  4.8m
      unattributed (glue)      202.7m  (wall − agents(active) − quota)
  goal-ops-hardening-iter-15  depth=full  verdict=STALLED  wall=217.7m
      iteration-summarizer        29.9m  calls=2
      goal-decomposer             21.9m  calls=1
      goal-evaluator              15.9m  calls=1
      readme-maintainer            8.7m  calls=2
      coherence-auditor            6.1m  calls=1
      [engine] full-pipeline     156.9m  (contains agent time above)
      [engine] showcase-join       5.7m  (contains agent time above)
      pump-wait                  2.9m
      unattributed (glue)      135.2m  (wall − agents(active) − quota)
  goal-ops-hardening-iter-16  depth=full  verdict=CONTINUE  wall=212.6m
      goal-decomposer             21.8m  calls=1
      goal-evaluator              12.3m  calls=1
      coherence-auditor            7.3m  calls=1
      [engine] full-pipeline     171.2m  (contains agent time above)
      [engine] showcase-join       0.0m  (contains agent time above)
      pump-wait                  3.1m
      unattributed (glue)      171.2m  (wall − agents(active) − quota)
  goal-ops-hardening-iter-17  depth=full  verdict=CONTINUE  wall=517.3m
      iteration-summarizer        18.8m  calls=1
      goal-decomposer             18.8m  calls=1
      goal-evaluator              15.9m  calls=1  failures=1
      readme-maintainer            8.8m  calls=1
      coherence-auditor            4.5m  calls=1  failures=1
      [engine] full-pipeline     469.2m  (contains agent time above)
      [engine] showcase-join       8.9m  (contains agent time above)
      pump-wait                  1.5m
      unattributed (glue)      450.5m  (wall − agents(active) − quota)
  goal-ops-hardening-iter-18  depth=?  verdict=?  wall=?  (incomplete/interrupted attempt)
      goal-decomposer             13.2m  calls=1  failures=1
  goal-ops-hardening-iter-18  depth=lean  verdict=CONTINUE  wall=119.8m
      developer                   35.2m  calls=1
      goal-evaluator              30.9m  calls=1
      coherence-auditor           25.6m  calls=1
      browser-qa-agent            20.6m  calls=1
      goal-decomposer             15.4m  calls=1
      reviewer                    12.6m  calls=1
      [engine] lean-pipeline      73.5m  (contains agent time above)
      [engine] showcase-join       0.0m  (contains agent time above)
      (resume-skipped: coherence-auditor)
      pump-wait                 32.4m
      overlap saved             20.6m  (parallel steps)
  goal-ops-hardening-iter-19  depth=full  verdict=CONTINUE  wall=296.2m
      goal-decomposer             26.7m  calls=1
      goal-evaluator              14.8m  calls=1
      coherence-auditor            4.1m  calls=1
      [engine] full-pipeline     235.4m  (contains agent time above)
      [engine] showcase-join      15.1m  (contains agent time above)
      pump-wait                 23.0m
      unattributed (glue)      250.6m  (wall − agents(active) − quota)
  goal-ops-hardening-iter-20  depth=full  verdict=STALLED  wall=219.2m
      iteration-summarizer        35.1m  calls=2
      goal-decomposer             22.1m  calls=1
      goal-evaluator              16.6m  calls=1
      coherence-auditor            4.8m  calls=1
      readme-maintainer            4.5m  calls=2
      [engine] full-pipeline     158.0m  (contains agent time above)
      [engine] showcase-join      14.7m  (contains agent time above)
      pump-wait                  9.0m
      unattributed (glue)      136.1m  (wall − agents(active) − quota)
  goal-ops-hardening-iter-21  depth=lean  verdict=STALLED  wall=109.0m
      browser-qa-agent            36.0m  calls=1
      goal-decomposer             19.5m  calls=1
      goal-evaluator              18.8m  calls=1
      developer                    9.1m  calls=1
      iteration-summarizer         8.8m  calls=1
      reviewer                     4.1m  calls=1
      coherence-auditor            3.8m  calls=1
      [engine] lean-pipeline      49.6m  (contains agent time above)
      [engine] showcase-join       0.0m  (contains agent time above)
      (resume-skipped: coherence-auditor)
      pump-wait                  4.2m
      unattributed (glue)        8.9m  (wall − agents(active) − quota)
  goal-ops-hardening-iter-22  depth=lean  verdict=CONTINUE  wall=109.0m
      browser-qa-agent            28.8m  calls=1
      developer                   27.2m  calls=1
      goal-evaluator              17.3m  calls=1
      goal-decomposer             15.3m  calls=1
      reviewer                    10.9m  calls=1
      coherence-auditor            5.0m  calls=1
      [engine] lean-pipeline      67.3m  (contains agent time above)
      [engine] showcase-join       0.0m  (contains agent time above)
      (resume-skipped: coherence-auditor)
      pump-wait                 12.0m
      unattributed (glue)        4.5m  (wall − agents(active) − quota)
  goal-ops-hardening-iter-23  depth=lean  verdict=GOAL_ACHIEVED  wall=138.3m
      browser-qa-agent            24.3m  calls=1
      developer                   22.1m  calls=1
      iteration-summarizer        18.1m  calls=2
      goal-decomposer             18.1m  calls=1
      goal-evaluator              16.3m  calls=1
      reviewer                     8.4m  calls=1
      coherence-auditor            5.8m  calls=1
      readme-maintainer            3.5m  calls=1
      [engine] lean-pipeline      55.3m  (contains agent time above)
      [engine] showcase-join      13.3m  (contains agent time above)
      (resume-skipped: coherence-auditor)
      pump-wait                  6.4m
      unattributed (glue)       21.8m  (wall − agents(active) − quota)
  goal-ops-hardening-iter-24  depth=?  verdict=?  wall=?  (incomplete/interrupted attempt)
  goal-ops-hardening-iter-24  depth=full  verdict=CONTINUE  wall=202.9m
      goal-evaluator              14.3m  calls=1
      goal-decomposer              8.9m  calls=1
      coherence-auditor            2.8m  calls=1
      [engine] full-pipeline     176.8m  (contains agent time above)
      [engine] showcase-join       0.0m  (contains agent time above)
      pump-wait                  1.9m
      unattributed (glue)      176.8m  (wall − agents(active) − quota)
  goal-ops-hardening-iter-25  depth=lean  verdict=CONTINUE  wall=140.7m
      developer                   79.4m  calls=1
      browser-qa-agent            27.5m  calls=1
      goal-evaluator              13.4m  calls=1
      goal-decomposer              6.1m  calls=1
      iteration-summarizer         6.1m  calls=1
      reviewer                     4.8m  calls=1
      coherence-auditor            2.6m  calls=1
      readme-maintainer            1.8m  calls=1
      [engine] lean-pipeline     113.0m  (contains agent time above)
      [engine] showcase-join       1.9m  (contains agent time above)
      (resume-skipped: coherence-auditor)
      pump-wait                  2.1m
      overlap saved              1.1m  (parallel steps)
  goal-ops-hardening-iter-26  depth=lean  verdict=ESCALATE  wall=155.3m
      developer                   99.8m  calls=1
      goal-evaluator              19.0m  calls=1
      browser-qa-agent            11.3m  calls=1
      goal-decomposer              9.6m  calls=1
      iteration-summarizer         5.5m  calls=1
      reviewer                     3.5m  calls=1
      coherence-auditor            2.2m  calls=1
      readme-maintainer            1.5m  calls=1
      [engine] lean-pipeline     115.5m  (contains agent time above)
      [engine] showcase-join      11.2m  (contains agent time above)
      (resume-skipped: coherence-auditor)
      pump-wait                 11.4m
      unattributed (glue)        3.0m  (wall − agents(active) − quota)
  goal-ops-hardening-iter-27  depth=full  verdict=?  wall=?  (incomplete/interrupted attempt)
      goal-decomposer             12.5m  calls=1
      iteration-summarizer         4.7m  calls=1
      readme-maintainer            1.2m  calls=1
      [engine] full-pipeline    1204.1m  (contains agent time above)
      [engine] showcase-join      13.2m  (contains agent time above)
      pump-wait                 12.9m
  goal-ops-hardening-iter-27  depth=full  verdict=CONTINUE  wall=57.7m
      goal-evaluator              14.8m  calls=1
      coherence-auditor            2.6m  calls=1
      [engine] full-pipeline      40.3m  (contains agent time above)
      [engine] showcase-join       0.0m  (contains agent time above)
      (resume-skipped: goal-decomposer)
      pump-wait                  0.8m
      unattributed (glue)       40.4m  (wall − agents(active) − quota)
  goal-ops-hardening-iter-28  depth=lean  verdict=?  wall=?  (incomplete/interrupted attempt)
      developer                  111.4m  calls=1
      browser-qa-agent            62.9m  calls=1
      iteration-summarizer         8.9m  calls=1
      goal-decomposer              8.9m  calls=1
      coherence-auditor            3.1m  calls=1
      reviewer                     2.9m  calls=1
      readme-maintainer            1.6m  calls=1
      [engine] lean-pipeline     177.8m  (contains agent time above)
      [engine] showcase-join       1.7m  (contains agent time above)
      (resume-skipped: coherence-auditor)
      pump-wait                  3.0m
  goal-ops-hardening-iter-28  depth=lean  verdict=CONTINUE  wall=16.5m
      goal-evaluator              16.4m  calls=1
      [engine] lean-pipeline       0.0m  (contains agent time above)
      [engine] showcase-join       0.0m  (contains agent time above)
      (resume-skipped: goal-decomposer, developer, reviewer, coherence-auditor, browser-qa, coherence-auditor)
      unattributed (glue)        0.1m  (wall − agents(active) − quota)
  goal-ops-hardening-iter-29  depth=full  verdict=?  wall=?  (incomplete/interrupted attempt)
      goal-decomposer             20.6m  calls=1
      [engine] showcase-join      15.1m  (contains agent time above)
      pump-wait                 26.8m
  goal-ops-hardening-iter-29  depth=lean  verdict=CONTINUE  wall=46.8m
      browser-qa-agent            25.4m  calls=1
      goal-evaluator              18.5m  calls=1
      coherence-auditor            3.5m  calls=1
      demo-narrator                1.9m  calls=1
      [engine] evidence-pipeline    28.2m  (contains agent time above)
      [engine] showcase-join       0.0m  (contains agent time above)
      (resume-skipped: goal-decomposer, developer, reviewer, coherence-auditor)
      pump-wait                  3.1m
      overlap saved              2.5m  (parallel steps)
  goal-ops-hardening-iter-30  depth=full  verdict=CONTINUE  wall=152.0m
      developer                   48.9m  calls=1
      browser-qa-agent            32.3m  calls=1
      auditor                     15.8m  calls=1
      goal-evaluator              15.7m  calls=1
      iteration-summarizer         9.1m  calls=1
      goal-decomposer              9.1m  calls=1
      qa                           7.0m  calls=2
      ux-regression-reviewer       5.7m  calls=1
      ui-impact-analyst            5.4m  calls=1
      orchestrator                 5.0m  calls=1
      reviewer                     4.6m  calls=1
      coherence-auditor            3.1m  calls=1
      readme-maintainer            1.4m  calls=1
      demo-narrator                1.3m  calls=1
      ui-test-designer             1.2m  calls=1
      [engine] full-pipeline     122.6m  (contains agent time above)
      [engine] showcase-join       1.5m  (contains agent time above)
      pump-wait                  0.8m
      overlap saved             13.6m  (parallel steps)
  goal-ops-hardening-iter-31  depth=full  verdict=CONTINUE  wall=172.4m
      developer                   83.4m  calls=2
      auditor                     21.9m  calls=1
      goal-evaluator              13.8m  calls=1
      iteration-summarizer        10.8m  calls=1
      goal-decomposer             10.8m  calls=1
      reviewer                    10.2m  calls=2
      browser-qa-agent             9.8m  calls=1
      qa                           7.3m  calls=2
      ui-impact-analyst            5.8m  calls=1
      orchestrator                 4.8m  calls=1
      ux-regression-reviewer       3.0m  calls=1
      coherence-auditor            2.8m  calls=1
      demo-narrator                1.3m  calls=1
      ui-test-designer             1.3m  calls=1
      readme-maintainer            1.0m  calls=1
      [engine] full-pipeline     143.8m  (contains agent time above)
      [engine] showcase-join       1.1m  (contains agent time above)
      pump-wait                  0.9m
      overlap saved             15.7m  (parallel steps)
  goal-ops-hardening-iter-32  depth=full  verdict=CONTINUE  wall=166.2m
      developer                   72.4m  calls=1
      auditor                     20.9m  calls=1
      iteration-summarizer        15.5m  calls=1
      goal-decomposer             15.5m  calls=1
      goal-evaluator              14.5m  calls=1
      browser-qa-agent            11.9m  calls=1
      reviewer                     8.0m  calls=1
      qa                           6.7m  calls=2
      ui-impact-analyst            5.0m  calls=1
      orchestrator                 4.3m  calls=1
      coherence-auditor            4.0m  calls=1
      ux-regression-reviewer       2.9m  calls=1
      ui-test-designer             1.6m  calls=1
      readme-maintainer            1.4m  calls=1
      demo-narrator                1.4m  calls=1
      [engine] full-pipeline     130.8m  (contains agent time above)
      [engine] showcase-join       1.5m  (contains agent time above)
      pump-wait                  1.2m
      overlap saved             19.6m  (parallel steps)
  goal-ops-hardening-iter-33  depth=full  verdict=?  wall=?  (incomplete/interrupted attempt)
      developer                   88.4m  calls=2
      qa                          53.6m  calls=4
      browser-qa-agent            43.0m  calls=1
      ui-impact-analyst           41.1m  calls=1
      auditor                     18.2m  calls=1
      reviewer                    17.0m  calls=2
      goal-decomposer             10.3m  calls=1
      iteration-summarizer        10.3m  calls=1
      orchestrator                 5.8m  calls=1
      ui-test-designer             5.6m  calls=1
      ux-regression-reviewer       5.2m  calls=1
      coherence-auditor            2.9m  calls=1
      demo-narrator                1.6m  calls=1
      readme-maintainer            1.4m  calls=1
      [engine] full-pipeline     239.8m  (contains agent time above)
      [engine] showcase-join       1.4m  (contains agent time above)
      pump-wait                  1.6m
  goal-ops-hardening-iter-33  depth=lean  verdict=CONTINUE  wall=192.2m
      browser-qa-agent           142.1m  calls=1
      developer                   27.2m  calls=1
      goal-evaluator              14.9m  calls=1
      reviewer                     7.8m  calls=1
      coherence-auditor            4.5m  calls=1
      browser-qa-replay            1.1m  calls=1
      [engine] lean-pipeline     177.3m  (contains agent time above)
      [engine] showcase-join       0.0m  (contains agent time above)
      (resume-skipped: goal-decomposer, coherence-auditor)
      pump-wait                  4.8m
      OVER BUDGET at coherence-auditor: 10639s > 3600s (mode=trim)
      overlap saved              5.4m  (parallel steps)
  goal-ops-hardening-iter-34  depth=lean  verdict=CONTINUE  wall=113.2m
      developer                   72.5m  calls=1
      goal-evaluator              14.7m  calls=1
      goal-decomposer             12.2m  calls=1
      browser-qa-agent            10.1m  calls=1
      iteration-summarizer         4.4m  calls=1
      reviewer                     3.5m  calls=1
      coherence-auditor            2.4m  calls=1
      browser-qa-replay            1.2m  calls=1
      [engine] lean-pipeline      86.2m  (contains agent time above)
      [engine] showcase-join       0.1m  (contains agent time above)
      (resume-skipped: coherence-auditor)
      pump-wait                  7.1m
      OVER BUDGET at browser-qa: 5299s > 3600s (mode=trim)
      overlap saved              7.7m  (parallel steps)
  goal-ops-hardening-iter-35  depth=lean  verdict=ESCALATE  wall=55.1m
      browser-qa-agent            24.0m  calls=1
      goal-evaluator              14.7m  calls=1
      iteration-summarizer        14.0m  calls=1
      goal-decomposer             13.9m  calls=1
      demo-narrator                1.7m  calls=1
      [engine] evidence-pipeline    26.4m  (contains agent time above)
      [engine] showcase-join       0.1m  (contains agent time above)
      (resume-skipped: developer, reviewer, coherence-auditor)
      pump-wait                  0.1m
      overlap saved             13.2m  (parallel steps)
  goal-ops-hardening-iter-36  depth=full  verdict=ESCALATE  wall=404.3m
      browser-qa-agent           214.4m  calls=1
      developer                   87.3m  calls=1
      auditor                     47.4m  calls=1
      qa                          37.0m  calls=1
      goal-evaluator              17.4m  calls=1
      reviewer                    15.0m  calls=1
      goal-decomposer              8.2m  calls=1
      iteration-summarizer         8.2m  calls=1
      orchestrator                 4.7m  calls=1
      ui-impact-analyst            3.7m  calls=1
      coherence-auditor            3.7m  calls=1
      demo-narrator                1.4m  calls=1
      [engine] full-pipeline     374.9m  (contains agent time above)
      [engine] showcase-join       0.1m  (contains agent time above)
      (resume-skipped: ui-test-design, ux-regression)
      pump-wait                 37.2m
      OVER BUDGET at post-dev-fanout: 6921s > 3600s (mode=trim)
      overlap saved             44.2m  (parallel steps)
  goal-ops-hardening-iter-37  depth=full  verdict=ESCALATE  wall=195.9m
      developer                  106.3m  calls=1
      auditor                     21.2m  calls=1
      goal-evaluator              16.4m  calls=1
      iteration-summarizer        11.8m  calls=1
      goal-decomposer             11.8m  calls=1
      qa                          11.4m  calls=1
      reviewer                    10.1m  calls=1
      ui-test-designer            10.0m  calls=1
      orchestrator                 6.7m  calls=1
      browser-qa-agent             6.4m  calls=1
      coherence-auditor            3.0m  calls=1
      ui-impact-analyst            1.6m  calls=1
      demo-narrator                1.2m  calls=1
      [engine] full-pipeline     164.6m  (contains agent time above)
      [engine] showcase-join       0.1m  (contains agent time above)
      (resume-skipped: ux-regression)
      pump-wait                  4.2m
      OVER BUDGET at post-dev-fanout: 8101s > 3600s (mode=trim)
      overlap saved             21.9m  (parallel steps)
  goal-ops-hardening-iter-38  depth=full  verdict=ESCALATE  wall=223.7m
      developer                   89.2m  calls=1
      browser-qa-agent            61.3m  calls=1
      auditor                     16.8m  calls=1
      qa                          15.2m  calls=1
      ui-test-designer            13.8m  calls=1
      goal-evaluator              12.1m  calls=1
      iteration-summarizer        10.6m  calls=1
      goal-decomposer             10.6m  calls=1
      reviewer                     6.7m  calls=1
      orchestrator                 4.4m  calls=1
      coherence-auditor            2.8m  calls=1
      ui-impact-analyst            1.4m  calls=1
      demo-narrator                1.1m  calls=1
      [engine] full-pipeline     198.1m  (contains agent time above)
      [engine] showcase-join       0.1m  (contains agent time above)
      (resume-skipped: ux-regression)
      pump-wait                  2.2m
      OVER BUDGET at post-dev-fanout: 6659s > 3600s (mode=trim)
      overlap saved             22.4m  (parallel steps)
  goal-ops-hardening-iter-39  depth=full  verdict=?  wall=?  (incomplete/interrupted attempt)
      iteration-summarizer         8.2m  calls=1
      goal-decomposer              8.2m  calls=1
      orchestrator                 3.2m  calls=1
      [engine] showcase-join       0.1m  (contains agent time above)
      pump-wait                  0.1m
  goal-ops-hardening-iter-39  depth=full  verdict=?  wall=?  (incomplete/interrupted attempt)
      developer                   39.7m  calls=1
      reviewer                     0.0m  calls=1  failures=1
      [engine] full-pipeline      39.7m  (contains agent time above)
      [engine] showcase-join       0.0m  (contains agent time above)
      (resume-skipped: goal-decomposer)
      pump-wait                  0.2m
  session: 39 completed iteration(s), mean wall 203.6m
      total developer                 1154.3m
      total browser-qa-agent           909.5m
      total goal-evaluator             586.4m
      total goal-decomposer            567.2m
      total iteration-summarizer       372.4m
      total coherence-auditor          165.5m
      total auditor                    162.0m
      total reviewer                   138.4m
      total qa                         138.3m
      total readme-maintainer           69.3m
      total ui-impact-analyst           63.9m
      total orchestrator                38.8m
      total ui-test-designer            33.4m
      total ux-regression-reviewer      16.9m
      total demo-narrator               12.8m
      total browser-qa-replay            2.3m
      total AWAITING_PUMP paused gaps: 11.0m
      halts: AWAITING_PUMP, AWAITING_PUMP, REGRESSION_HALT, BUDGET_EXHAUSTED, REGRESSION_HALT, STALLED, DECOMPOSER_FAILED, STALLED, STALLED, AWAITING_PUMP, machine_reset, AWAITING_PUMP
```
