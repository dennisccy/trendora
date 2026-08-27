# Goal Session Summary — market-compass

**Final verdict:** STALLED
**Total iterations:** 23
**Wall time (seconds):** 40398
**Quota pauses:** 0
**Started:** 2026-08-19T21:31:52.886915Z
**Finished:** 2026-08-27T14:20:23.113521Z

## Branch

This session pushed iteration commits to `goal/market-compass`. Open a PR with:

    gh pr create --base main --head goal/market-compass \
      --title "feat: market-compass — STALLED" \
      --body-file runs/goal-session-market-compass/summary.md

## Final journey state

| Journey | Status | Last passing iter |
|---|---|---|
| J-01 | passing | goal-market-compass-iter-4 |
| J-02 | partial | goal-market-compass-iter-4 |
| J-03 | partial | goal-market-compass-iter-4 |
| J-04 | passing | goal-market-compass-iter-4 |
| J-05 | partial | - |
| J-06 | partial | - |
| J-07 | failing | - |
| J-08 | failing | - |
| J-09 | partial | - |
| J-10 | passing | goal-market-compass-iter-13 |
| J-11 | partial | - |

## Anti-goal violations

- [minor] AG-2 - Decision-quality only: never present return promises, price targets, 'buy/sell' signals, or alpha claims; never place or simulate orders. Candidate framing is 'worth monitoring', never advice. (iter goal-market-compass-iter-2)
- [critical] AG-12 - Manifest immutability: a stored next_session_manifests row and its exported file are never mutated or deleted by any later ingest, rebuild, data removal, config change, or code change. (iter goal-market-compass-iter-3)
- [critical] AG-9 - Offline-deterministic ingest: ingest jobs run only against the committed seed / local provider fixtures - no live external network calls or paid data services without an explicit goal.md amendment. || Dated exception (owner, 2026-08-20): '...If the implementation cannot prove a request stays inside this scope, it MUST stop rather than broaden the fetch.' || J-10 step 2a (text in force during that iteration): '...If the conventions do not demonstrably agree within a stated tolerance - or if the comparison cannot be performed at all - insert nothing and STOP for owner review.' (iter goal-market-compass-iter-7)
- [critical] AG-17 - Repair never rewrites provenance (owner, 2026-08-20): ... The incident record itself is evidence: the iter-5 drill result, its handoff, the reviewer/QA evidence already produced, and the explicit statement that the committed seed could not restore these dates MUST NOT be deleted, rewritten, or silently superseded. (iter goal-market-compass-iter-8)
- [critical] AG-18 — The authorized manifest migration preserves everything (owner, 2026-08-23): the bounded next_session_manifests schema migration authorized in J-11 step 11 (ruling A1) removes the source_run_id foreign-key constraint and nothing else. ... No other table's schema may be altered under that authorization. A changed stored value is a REGRESSION, never a note. (iter goal-market-compass-iter-11)
- [critical] AG-17 — Repair never rewrites provenance (owner, 2026-08-20): "The incident record itself is evidence: the iter-5 drill result, its handoff, the reviewer/QA evidence already produced, and the explicit statement that the committed seed could not restore these dates MUST NOT be deleted, rewritten, or silently superseded." (read together with J-11 ruling C5, "do not rewrite ... incident evidence") (iter goal-market-compass-iter-14)
- [minor] AG-8 - Resilience to data-shape and data-scale change: ... unbounded whole-table ORM loads are forbidden (the delta engine reads column-projected selects, never full record_json sweeps). (critical) (iter goal-market-compass-iter-16)

## Telemetry

See `runs/goal-session-market-compass/telemetry.jsonl` for the structured event log.

## Iteration timing

```
== Wall-time report: session market-compass
  goal-market-compass-iter-0  depth=?  verdict=?  wall=?  (incomplete/interrupted attempt)
      goal-decomposer              0.0m  calls=1  failures=1
      pump-wait                  0.0m
  goal-market-compass-iter-0  depth=lean  verdict=?  wall=?  (incomplete/interrupted attempt)
      goal-decomposer             37.5m  calls=1
      [engine] showcase-join       0.0m  (contains agent time above)
      pump-wait                  0.1m
  goal-market-compass-iter-0  depth=lean  verdict=CONTINUE  wall=22.2m
      browser-qa-agent            10.2m  calls=1
      goal-evaluator               6.3m  calls=1
      developer                    3.7m  calls=1
      reviewer                     1.8m  calls=1
      browser-qa-replay            0.3m  calls=1
      [engine] lean-pipeline      15.9m  (contains agent time above)
      [engine] showcase-join       0.0m  (contains agent time above)
      (resume-skipped: goal-decomposer)
      pump-wait                  0.2m
      overlap saved              0.2m  (parallel steps)
  goal-market-compass-iter-1  depth=full  verdict=?  wall=?  (incomplete/interrupted attempt)
      developer                  240.1m  calls=2  failures=2
      demo-narrator               14.6m  calls=1
      goal-decomposer             13.6m  calls=1
      iteration-summarizer         5.7m  calls=1
      orchestrator                 4.5m  calls=1
      readme-maintainer            1.2m  calls=1
      [engine] full-pipeline     124.7m  (contains agent time above)
      [engine] showcase-join       8.1m  (contains agent time above)
      pump-wait                133.8m
  goal-market-compass-iter-1  depth=full  verdict=CONTINUE  wall=106.1m
      browser-qa-agent            40.9m  calls=1
      qa                          21.9m  calls=1
      auditor                     20.9m  calls=1
      ui-impact-analyst           14.5m  calls=1
      reviewer                    11.8m  calls=1
      goal-evaluator              10.7m  calls=1
      coherence-auditor            4.8m  calls=1
      demo-narrator                2.0m  calls=1
      [engine] full-pipeline      90.6m  (contains agent time above)
      [engine] showcase-join       0.0m  (contains agent time above)
      (resume-skipped: goal-decomposer, ui-test-design, ux-regression)
      pump-wait                 14.9m
      OVER BUDGET at qa-loop: 4178s > 3600s (mode=trim)
      overlap saved             21.4m  (parallel steps)
  goal-market-compass-iter-2  depth=lean  verdict=ESCALATE  wall=135.4m
      developer                   64.3m  calls=1
      browser-qa-agent            27.5m  calls=1
      goal-decomposer             17.7m  calls=1
      reviewer                    13.0m  calls=1
      goal-evaluator              12.7m  calls=1
      iteration-summarizer         6.9m  calls=1
      coherence-auditor            5.0m  calls=1
      browser-qa-replay            0.4m  calls=1
      [engine] lean-pipeline     104.9m  (contains agent time above)
      [engine] showcase-join       0.1m  (contains agent time above)
      (resume-skipped: coherence-auditor)
      pump-wait                  0.3m
      OVER BUDGET at browser-qa: 5705s > 3600s (mode=trim)
      overlap saved             12.1m  (parallel steps)
  goal-market-compass-iter-3  depth=full  verdict=?  wall=?  (incomplete/interrupted attempt)
      goal-decomposer             16.8m  calls=1
      orchestrator                 9.6m  calls=1
      iteration-summarizer         7.8m  calls=1
      [engine] showcase-join       0.1m  (contains agent time above)
      pump-wait                  0.2m
  goal-market-compass-iter-3  depth=full  verdict=CONTINUE  wall=167.0m
      developer                   66.1m  calls=1
      browser-qa-agent            39.4m  calls=1
      qa                          22.5m  calls=1
      auditor                     14.4m  calls=1
      goal-evaluator              13.8m  calls=1
      reviewer                    13.4m  calls=1
      ui-impact-analyst           10.2m  calls=1
      coherence-auditor            6.1m  calls=1
      demo-narrator                2.2m  calls=1
      [engine] full-pipeline     147.1m  (contains agent time above)
      [engine] showcase-join       0.0m  (contains agent time above)
      (resume-skipped: goal-decomposer, ui-test-design, ux-regression)
      pump-wait                 22.4m
      OVER BUDGET at post-dev-fanout: 4769s > 3600s (mode=trim)
      overlap saved             21.0m  (parallel steps)
  goal-market-compass-iter-4  depth=lean  verdict=CONTINUE  wall=90.8m
      developer                   38.8m  calls=1
      goal-decomposer             18.4m  calls=1
      browser-qa-agent            14.6m  calls=1
      goal-evaluator              11.7m  calls=1
      iteration-summarizer         8.1m  calls=1
      reviewer                     7.1m  calls=1
      coherence-auditor            2.3m  calls=1
      browser-qa-replay            1.3m  calls=1
      [engine] lean-pipeline      60.6m  (contains agent time above)
      [engine] showcase-join       0.1m  (contains agent time above)
      (resume-skipped: coherence-auditor)
      pump-wait                 10.6m
      OVER BUDGET at browser-qa: 3864s > 3600s (mode=trim)
      overlap saved             11.5m  (parallel steps)
  goal-market-compass-iter-5  depth=lean  verdict=?  wall=?  (incomplete/interrupted attempt)
      developer                   67.5m  calls=1
      goal-decomposer             30.9m  calls=1
      iteration-summarizer         7.6m  calls=1
      browser-qa-replay            1.7m  calls=1
      [engine] showcase-join       0.1m  (contains agent time above)
      pump-wait                  7.7m
  goal-market-compass-iter-6  depth=lean  verdict=ESCALATE  wall=229.5m
      reviewer                   152.5m  calls=1
      developer                   36.6m  calls=1
      goal-decomposer             14.2m  calls=1
      coherence-auditor           13.4m  calls=1
      goal-evaluator              12.7m  calls=1
      browser-qa-agent             4.4m  calls=1
      browser-qa-replay            1.5m  calls=1
      [engine] lean-pipeline     202.6m  (contains agent time above)
      [engine] showcase-join       0.0m  (contains agent time above)
      (resume-skipped: coherence-auditor)
      pump-wait                  2.9m
      OVER BUDGET at browser-qa: 12205s > 3600s (mode=trim)
      overlap saved              5.9m  (parallel steps)
  goal-market-compass-iter-7  depth=full  verdict=CONTINUE  wall=126.9m
      reviewer                   373.9m  calls=2  failures=1
      developer                   31.3m  calls=1
      goal-decomposer             18.6m  calls=1
      coherence-auditor           16.0m  calls=1
      goal-evaluator              14.0m  calls=1
      auditor                     13.6m  calls=1
      iteration-summarizer         9.8m  calls=1
      orchestrator                 8.2m  calls=1
      ui-impact-analyst            7.7m  calls=1
      qa                           3.9m  calls=1
      browser-qa-agent             2.2m  calls=1
      demo-narrator                1.2m  calls=1
      [engine] full-pipeline      78.1m  (contains agent time above)
      [engine] showcase-join       0.0m  (contains agent time above)
      (resume-skipped: ui-test-design, ux-regression)
      pump-wait                373.9m
      OVER BUDGET at post-dev-fanout: 4319s > 3600s (mode=trim)
      overlap saved            373.4m  (parallel steps)
  goal-market-compass-iter-8  depth=lean  verdict=?  wall=?  (incomplete/interrupted attempt)
      reviewer                   300.0m  calls=1  failures=1
      developer                   60.1m  calls=1
      goal-decomposer             18.1m  calls=1
      iteration-summarizer         7.1m  calls=1
      browser-qa-replay            1.2m  calls=1
      [engine] lean-pipeline     360.1m  (contains agent time above)
      [engine] showcase-join       0.0m  (contains agent time above)
      pump-wait                300.3m
  goal-market-compass-iter-8  depth=full  verdict=CONTINUE  wall=69.5m
      auditor                     20.9m  calls=1
      goal-evaluator              12.7m  calls=1
      qa                           9.7m  calls=1
      reviewer                     8.6m  calls=1
      ux-regression-reviewer       7.2m  calls=1
      ui-impact-analyst            6.7m  calls=1
      browser-qa-agent             6.2m  calls=1
      coherence-auditor            5.7m  calls=1
      demo-narrator                1.3m  calls=1
      [engine] full-pipeline      51.1m  (contains agent time above)
      [engine] showcase-join       0.0m  (contains agent time above)
      (resume-skipped: goal-decomposer, ui-test-design)
      pump-wait                  9.8m
      overlap saved              9.3m  (parallel steps)
  goal-market-compass-iter-9  depth=full  verdict=?  wall=?  (incomplete/interrupted attempt)
      orchestrator               340.9m  calls=1  failures=1
      goal-decomposer             19.1m  calls=1
      iteration-summarizer        11.6m  calls=1
      [engine] showcase-join       0.1m  (contains agent time above)
      pump-wait                341.1m
  goal-market-compass-iter-9  depth=full  verdict=?  wall=?  (incomplete/interrupted attempt)
      [engine] showcase-join       0.0m  (contains agent time above)
      (resume-skipped: goal-decomposer)
  goal-market-compass-iter-9  depth=full  verdict=CONTINUE  wall=133.8m
      developer                   61.3m  calls=1
      goal-evaluator              17.5m  calls=1
      auditor                     17.4m  calls=1
      orchestrator                 9.4m  calls=1
      coherence-auditor            9.3m  calls=1
      reviewer                     9.3m  calls=1
      qa                           9.3m  calls=1
      [engine] full-pipeline     107.0m  (contains agent time above)
      [engine] showcase-join       0.0m  (contains agent time above)
      (resume-skipped: goal-decomposer)
      pump-wait                  0.2m
      OVER BUDGET at post-dev-fanout: 4809s > 3600s (mode=trim)
      unattributed (glue)        0.1m  (wall − agents(active) − quota)
  goal-market-compass-iter-10  depth=full  verdict=?  wall=?  (incomplete/interrupted attempt)
      iteration-summarizer         9.1m  calls=1
      goal-decomposer              9.1m  calls=1
      orchestrator                 8.9m  calls=1
      [engine] showcase-join       0.0m  (contains agent time above)
      pump-wait                  0.0m
  goal-market-compass-iter-10  depth=full  verdict=?  wall=?  (incomplete/interrupted attempt)
      [engine] showcase-join       0.0m  (contains agent time above)
      [engine] full-pipeline       0.0m  (contains agent time above)
      (resume-skipped: goal-decomposer, coherence-auditor)
  goal-market-compass-iter-10  depth=full  verdict=STALLED  wall=88.8m
      developer                   17.9m  calls=1
      auditor                     17.5m  calls=1
      goal-evaluator              17.4m  calls=1
      reviewer                     9.2m  calls=1
      coherence-auditor            8.9m  calls=1
      qa                           8.9m  calls=1
      iteration-summarizer         8.8m  calls=1
      [engine] full-pipeline      53.6m  (contains agent time above)
      [engine] showcase-join       0.0m  (contains agent time above)
      (resume-skipped: goal-decomposer)
      pump-wait                  0.8m
      OVER BUDGET at goal-evaluator: 3757s > 3600s (mode=trim)
      unattributed (glue)        0.1m  (wall − agents(active) − quota)
  goal-market-compass-iter-11  depth=full  verdict=REGRESSION  wall=143.2m
      developer                   26.3m  calls=1
      auditor                     18.1m  calls=1
      goal-decomposer             18.0m  calls=1
      goal-evaluator              17.7m  calls=1
      ui-test-designer            17.6m  calls=1
      qa                           9.2m  calls=1
      orchestrator                 9.1m  calls=1
      reviewer                     9.1m  calls=1
      coherence-auditor            9.0m  calls=1
      iteration-summarizer         8.8m  calls=1
      [engine] full-pipeline      89.5m  (contains agent time above)
      [engine] showcase-join       0.0m  (contains agent time above)
      pump-wait                  0.6m
      OVER BUDGET at post-dev-fanout: 3752s > 3600s (mode=trim)
      unattributed (glue)        0.2m  (wall − agents(active) − quota)
  goal-market-compass-iter-12  depth=full  verdict=?  wall=?  (incomplete/interrupted attempt)
      developer                   27.0m  calls=1
      auditor                     17.6m  calls=1
      ui-test-designer            17.5m  calls=1
      goal-decomposer              9.6m  calls=1
      orchestrator                 9.2m  calls=1
      reviewer                     9.1m  calls=1
      qa                           9.1m  calls=1
      coherence-auditor            9.0m  calls=1
      [engine] full-pipeline      89.7m  (contains agent time above)
      [engine] showcase-join       0.0m  (contains agent time above)
      pump-wait                  0.5m
      OVER BUDGET at qa-loop: 4348s > 3600s (mode=trim)
  goal-market-compass-iter-12  depth=full  verdict=STALLED  wall=54.0m
      goal-evaluator              26.7m  calls=1
      coherence-auditor            9.3m  calls=1
      iteration-summarizer         9.1m  calls=1
      readme-maintainer            8.9m  calls=1
      [engine] showcase-join       0.0m  (contains agent time above)
      [engine] full-pipeline       0.0m  (contains agent time above)
      (resume-skipped: goal-decomposer)
      pump-wait                  0.3m
      unattributed (glue)        0.1m  (wall − agents(active) − quota)
  goal-market-compass-iter-13  depth=full  verdict=STALLED  wall=144.3m
      developer                   27.0m  calls=1
      auditor                     26.4m  calls=1
      goal-decomposer             17.9m  calls=1
      goal-evaluator              17.9m  calls=1
      orchestrator                 9.4m  calls=1
      qa                           9.3m  calls=1
      reviewer                     9.2m  calls=1
      coherence-auditor            9.1m  calls=1
      ui-test-designer             9.0m  calls=1
      iteration-summarizer         9.0m  calls=1
      [engine] full-pipeline      90.4m  (contains agent time above)
      [engine] showcase-join       0.0m  (contains agent time above)
      pump-wait                  0.8m
      OVER BUDGET at post-dev-fanout: 3817s > 3600s (mode=trim)
      unattributed (glue)        0.2m  (wall − agents(active) − quota)
  goal-market-compass-iter-14  depth=full  verdict=STALLED  wall=191.1m
      developer                   54.7m  calls=2
      auditor                     26.8m  calls=1
      goal-evaluator              26.4m  calls=1
      reviewer                    18.9m  calls=2
      goal-decomposer             18.0m  calls=1
      qa                           9.3m  calls=1
      orchestrator                 9.3m  calls=1
      coherence-auditor            9.2m  calls=1
      ui-test-designer             9.2m  calls=1
      iteration-summarizer         9.1m  calls=1
      [engine] full-pipeline     128.3m  (contains agent time above)
      [engine] showcase-join       0.0m  (contains agent time above)
      pump-wait                  0.8m
      OVER BUDGET at post-dev-fanout: 6063s > 3600s (mode=trim)
      unattributed (glue)        0.2m  (wall − agents(active) − quota)
  goal-market-compass-iter-15  depth=full  verdict=STALLED  wall=180.9m
      developer                   44.7m  calls=1
      goal-decomposer             26.6m  calls=1
      auditor                     18.6m  calls=1
      goal-evaluator              18.1m  calls=1
      reviewer                    17.8m  calls=1
      ui-test-designer            17.7m  calls=1
      qa                           9.4m  calls=1
      orchestrator                 9.4m  calls=1
      coherence-auditor            9.2m  calls=1
      iteration-summarizer         9.2m  calls=1
      [engine] full-pipeline     117.8m  (contains agent time above)
      [engine] showcase-join       0.0m  (contains agent time above)
      pump-wait                  0.8m
      OVER BUDGET at post-dev-fanout: 5916s > 3600s (mode=trim)
      unattributed (glue)        0.2m  (wall − agents(active) − quota)
  goal-market-compass-iter-16  depth=full  verdict=STALLED  wall=200.4m
      developer                   44.6m  calls=1
      goal-evaluator              27.2m  calls=1
      auditor                     27.1m  calls=1
      goal-decomposer             26.6m  calls=1
      coherence-auditor           19.2m  calls=1
      reviewer                    18.1m  calls=1
      qa                           9.4m  calls=1
      orchestrator                 9.4m  calls=1
      ui-test-designer             9.3m  calls=1
      iteration-summarizer         9.2m  calls=1
      [engine] full-pipeline     118.1m  (contains agent time above)
      [engine] showcase-join       0.0m  (contains agent time above)
      pump-wait                  0.9m
      OVER BUDGET at post-dev-fanout: 5930s > 3600s (mode=trim)
      unattributed (glue)        0.1m  (wall − agents(active) − quota)
  goal-market-compass-iter-17  depth=full  verdict=STALLED  wall=112.2m
      developer                   27.4m  calls=1
      goal-evaluator              15.9m  calls=1
      goal-decomposer             14.2m  calls=1
      auditor                     11.8m  calls=1
      ui-test-designer            10.1m  calls=1
      orchestrator                 9.2m  calls=1
      iteration-summarizer         8.8m  calls=1
      reviewer                     7.8m  calls=1
      qa                           3.6m  calls=1
      coherence-auditor            3.1m  calls=1
      [engine] full-pipeline      70.1m  (contains agent time above)
      [engine] showcase-join       0.0m  (contains agent time above)
      pump-wait                  0.9m
      OVER BUDGET at qa-loop: 4133s > 3600s (mode=trim)
      unattributed (glue)        0.1m  (wall − agents(active) − quota)
  goal-market-compass-iter-18  depth=lean  verdict=?  wall=?  (incomplete/interrupted attempt)
      goal-decomposer             17.3m  calls=1
      [engine] showcase-join       0.0m  (contains agent time above)
      pump-wait                  0.3m
  goal-market-compass-iter-18  depth=full  verdict=?  wall=?  (incomplete/interrupted attempt)
      developer                   73.0m  calls=1
      orchestrator                 8.7m  calls=1
      reviewer                     0.0m  calls=1  failures=1
      [engine] full-pipeline      81.7m  (contains agent time above)
      [engine] showcase-join       0.0m  (contains agent time above)
      (resume-skipped: goal-decomposer)
      pump-wait                  1.4m
  goal-market-compass-iter-18  depth=full  verdict=STALLED  wall=66.8m
      auditor                     15.2m  calls=1
      goal-evaluator              14.5m  calls=1
      ui-test-designer            11.6m  calls=1
      reviewer                    11.3m  calls=1
      iteration-summarizer         7.2m  calls=1
      qa                           3.1m  calls=1
      coherence-auditor            2.8m  calls=1
      readme-maintainer            0.9m  calls=1
      [engine] full-pipeline      41.4m  (contains agent time above)
      [engine] showcase-join       0.0m  (contains agent time above)
      (resume-skipped: goal-decomposer)
      pump-wait                  0.4m
      unattributed (glue)        0.1m  (wall − agents(active) − quota)
  goal-market-compass-iter-19  depth=full  verdict=CONTINUE  wall=324.7m
      reviewer                   172.2m  calls=1
      developer                   72.6m  calls=1
      goal-decomposer             19.4m  calls=1
      goal-evaluator              18.4m  calls=1
      auditor                     15.2m  calls=1
      ui-test-designer            10.1m  calls=1
      orchestrator                 8.0m  calls=1
      coherence-auditor            5.3m  calls=1
      qa                           3.4m  calls=1
      [engine] full-pipeline     281.5m  (contains agent time above)
      [engine] showcase-join       0.0m  (contains agent time above)
      pump-wait                165.8m
      OVER BUDGET at post-dev-fanout: 16335s > 3600s (mode=trim)
      unattributed (glue)        0.1m  (wall − agents(active) − quota)
  goal-market-compass-iter-20  depth=full  verdict=?  wall=?  (incomplete/interrupted attempt)
      goal-decomposer             17.8m  calls=1
      [engine] showcase-join       0.0m  (contains agent time above)
      pump-wait                  0.3m
  goal-market-compass-iter-20  depth=full  verdict=?  wall=?  (incomplete/interrupted attempt)
      reviewer                    39.4m  calls=1
      developer                   28.5m  calls=1
      auditor                     18.6m  calls=1
      ui-test-designer            11.6m  calls=1
      orchestrator                 9.4m  calls=1
      qa                           4.2m  calls=1
      [engine] full-pipeline     111.8m  (contains agent time above)
      [engine] showcase-join       0.0m  (contains agent time above)
      (resume-skipped: goal-decomposer)
      pump-wait                 40.1m
      OVER BUDGET at post-dev-fanout: 4641s > 3600s (mode=trim)
  goal-market-compass-iter-20  depth=full  verdict=?  wall=?  (incomplete/interrupted attempt)
      [engine] showcase-join       0.0m  (contains agent time above)
      [engine] full-pipeline       0.0m  (contains agent time above)
      (resume-skipped: goal-decomposer)
  goal-market-compass-iter-20  depth=full  verdict=CONTINUE  wall=24.1m
      goal-evaluator              20.5m  calls=1
      coherence-auditor            3.6m  calls=1
      [engine] showcase-join       0.0m  (contains agent time above)
      [engine] full-pipeline       0.0m  (contains agent time above)
      (resume-skipped: goal-decomposer)
      pump-wait                  0.3m
      unattributed (glue)        0.0m  (wall − agents(active) − quota)
  goal-market-compass-iter-21  depth=?  verdict=?  wall=?  (incomplete/interrupted attempt)
  goal-market-compass-iter-21  depth=full  verdict=CONTINUE  wall=307.7m
      reviewer                   142.6m  calls=1
      coherence-auditor           44.1m  calls=1
      developer                   37.0m  calls=1
      goal-decomposer             25.2m  calls=1
      auditor                     18.7m  calls=1
      goal-evaluator              17.5m  calls=1
      ui-test-designer            10.4m  calls=1
      orchestrator                 7.6m  calls=1
      qa                           4.3m  calls=1
      [engine] full-pipeline     220.8m  (contains agent time above)
      [engine] showcase-join       0.0m  (contains agent time above)
      pump-wait                  0.7m
      OVER BUDGET at post-dev-fanout: 12749s > 3600s (mode=trim)
      unattributed (glue)        0.2m  (wall − agents(active) − quota)
  goal-market-compass-iter-22  depth=full  verdict=STALLED  wall=365.4m
      reviewer                   198.6m  calls=2
      developer                   72.3m  calls=2
      auditor                     21.8m  calls=1
      goal-decomposer             21.5m  calls=1
      iteration-summarizer        17.2m  calls=2
      goal-evaluator              15.0m  calls=1
      ui-test-designer            12.9m  calls=1
      qa                           5.9m  calls=1
      coherence-auditor            4.7m  calls=1
      orchestrator                 4.7m  calls=1
      [engine] full-pipeline     316.4m  (contains agent time above)
      [engine] showcase-join       0.0m  (contains agent time above)
      pump-wait                  0.1m
      OVER BUDGET at post-dev-fanout: 17833s > 3600s (mode=trim)
      overlap saved              9.2m  (parallel steps)
  session: 22 completed iteration(s), mean wall 149.3m
      total reviewer                  1554.5m
      total developer                 1223.1m
      total orchestrator               484.9m
      total goal-decomposer            446.3m
      total goal-evaluator             365.2m
      total auditor                    340.5m
      total coherence-auditor          209.3m
      total iteration-summarizer       170.1m
      total qa                         156.5m
      total ui-test-designer           146.9m
      total browser-qa-agent           145.4m
      total ui-impact-analyst           39.1m
      total demo-narrator               21.3m
      total readme-maintainer           11.1m
      total ux-regression-reviewer       7.2m
      total browser-qa-replay            6.5m
      total AWAITING_PUMP paused gaps: 503.0m
      halts: AWAITING_PUMP, AWAITING_PUMP, AWAITING_PUMP, STALLED, REGRESSION_HALT, STALLED, STALLED, STALLED, STALLED, STALLED, STALLED, STALLED, STALLED, AWAITING_PUMP, STALLED, STALLED, STALLED, STALLED
```
