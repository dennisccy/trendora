# Session retro — market-compass

> **Ideas only — nothing here is scheduled work.** These are suggestions for
> improving the build system itself, not your product. A human reviews them and
> decides (promotion into docs/improvement-roadmap.md §16, the staging list).
> Codes: P0/P1/P2 = how urgent · Effort S/M/L = how much work · Risk LOW/MED/HIGH
> = chance a change breaks something else.

**Session:** market-compass · **Terminal status:** STALLED · **Iterations:** 17

## Candidate items

### RETRO-1 · Quota trims silently block feedback to goal-decomposer
- **Proposed:** P1 · Effort M · Risk MED
- **Problem:** The pipeline runs out of time and cancels work automatically on nearly every iteration, but nothing tells the goal-maker that this happened. So the next iteration, it asks for the same amount of work and the pipeline cancels it again, wasting effort.
- **Evidence:** Agent economics (per-step wall breakdown) — "OVER BUDGET at post-dev-fanout: 6063s > 3600s (mode=trim)" [9 iterations]; "OVER BUDGET at browser-qa: 5705s > 3600s (mode=trim)" [3 iterations]; "OVER BUDGET at qa-loop: 4178s > 3600s (mode=trim)" [2 iterations]; 14 budget overages across 16 completed iterations.
- **Sketch:** (1) Add "trim-event-count-by-stage" counter to friction counters showing how many times each pipeline stage exceeded its quota; (2) When a trim fires, log stage name + overage % to session.json; (3) Before each iteration, have goal-decomposer read trim history from session.json and reduce the next iteration's work scope at over-budget stages (e.g., if stage was 30% over budget last time, cut scope by 20% this time).
- **Verify idea:** In the next session, friction counters should show either (a) trim-event-count near zero, or (b) goal-decomposer log should show it read trim history and adjusted scope downward.

### RETRO-2 · Iteration restarts lack explanation in telemetry
- **Proposed:** P2 · Effort S · Risk LOW
- **Problem:** When the engine has to restart an iteration partway through, it records the interruption but does not log why it happened. Without knowing the restart reason, the retro-analyst cannot tell if it is a framework problem (pump crash, timeout) or a symptom of deeper product issues.
- **Evidence:** Agent economics (per-step wall breakdown) — "goal-market-compass-iter-0  depth=?  verdict=?  wall=?  (incomplete/interrupted attempt)"; "goal-market-compass-iter-8  depth=lean  verdict=?  wall=?  (incomplete/interrupted attempt)"; "goal-market-compass-iter-9  depth=full  verdict=?  wall=?  (incomplete/interrupted attempt)" [10 incomplete attempts across iters 0, 1, 3, 5, 8, 9(×2), 10(×2), 12, with no stated reason].
- **Sketch:** Capture why each iteration restart fires (user pause, pump timeout, agent error, malformed verdict, quota exceeded, etc.) and write it to telemetry as a new event "iter_restart" with a "reason" field. The retro-collect script can then categorize these and produce a restart-reason-distribution counter.
- **Verify idea:** Next session's retro-input should list restart reasons in friction counters (e.g., "iter-restart-count: 5, top-reason: user-pause (3)"); the breakdown reveals if one cause dominates.
