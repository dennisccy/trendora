# Session retro — market-compass

> **Ideas only — nothing here is scheduled work.** These are suggestions for
> improving the build system itself, not your product. A human reviews them and
> decides (promotion into docs/improvement-roadmap.md §16, the staging list).
> Codes: P0/P1/P2 = how urgent · Effort S/M/L = how much work · Risk LOW/MED/HIGH
> = chance a change breaks something else.

**Session:** market-compass · **Terminal status:** STALLED · **Iterations:** 18

## Candidate items

### RETRO-1 · Persistent per-stage wall-time budget overruns on most iterations
- **Proposed:** P1 · Effort M · Risk MED
- **Problem:** Nearly every iteration hits "OVER BUDGET at <stage>" warnings, with shortfalls ranging from 3 to 30 percent over the 1-hour quota. Repeated overruns force the pipeline to truncate agent outputs or requeue work, reducing iteration quality and extending wall time for future sessions.
- **Evidence:** Agent economics (Per-step wall breakdown) — "OVER BUDGET at qa-loop: 4178s > 3600s (mode=trim)" (line 104), "OVER BUDGET at browser-qa: 5705s > 3600s (mode=trim)" (line 119), "OVER BUDGET at browser-qa: 12205s > 3600s (mode=trim)" (line 177), appearing in 14 of 17 completed iterations across stages qa-loop, browser-qa, post-dev-fanout, and goal-evaluator.
- **Sketch:** Audit current per-stage time allocations in goal-mode pipeline configuration. Compare measured wall times per agent to their budgeted quota. Increase quotas for stages that consistently exceed them (browser-qa, post-dev-fanout), or decompose long-running stages into parallel substeps. Rebalance agent allocation based on measured workload.
- **Verify idea:** Next session: count "OVER BUDGET" warnings in per-step wall breakdown; target fewer than 2 overruns in 10 iterations.

### RETRO-2 · Reviewer wall-time dominance with repeated failures
- **Proposed:** P1 · Effort M · Risk MED
- **Problem:** The reviewer agent consumed 990.5 minutes across the session — more than the developer and second only to the session total — and failed twice (iters 7–8). High reviewer load combined with failures suggests either scope creep in what it reviews or systematic instability in its core logic.
- **Evidence:** Agent economics — "total reviewer 990.5m" (line 389); Wall breakdown: "reviewer 373.9m calls=2 failures=1" (line 180), "reviewer 300.0m calls=1 failures=1" (line 199); Friction counters "Attempt-1 review FAILs: 1" (line 412).
- **Sketch:** Profile reviewer evidence sets and deliverables per iteration to spot patterns: Are full-pipeline iterations triggering duplicate or overlapping reviews? Does the evidence corpus grow unbounded? Add telemetry to log which artifacts the reviewer examines per run. Consider splitting review into shallow pre-dev and deep post-dev phases, or gating review depth based on whether the prior iteration's review passed.
- **Verify idea:** Next session: measure reviewer total wall time as a ratio to developer (target <1.2×); achieve zero review failures on attempt 1.

### RETRO-3 · High AWAITING_PUMP paused gaps indicate pump latency bottleneck
- **Proposed:** P1 · Effort S · Risk LOW
- **Problem:** The pipeline spent 501.7 minutes (8.4 hours) blocked waiting for the pump (engine service dispatcher) across 17 iterations. This is time agents are idle; pump latency directly extends per-iteration wall time and reduces throughput for future sessions.
- **Evidence:** Agent economics (Per-step wall breakdown) — "total AWAITING_PUMP paused gaps: 501.7m" (line 405).
- **Sketch:** Profile pump dispatch latency in telemetry: measure queue depth, message round-trip time per call, and pump restart patterns between iterations. If restarts cascade delays or if median latency is >2 seconds per dispatch, identify root cause (CPU contention, I/O, subprocess overhead) and optimize dispatch batching or pump responsiveness.
- **Verify idea:** Next session: add pump dispatch latency counters to telemetry; report median and 95th-percentile latency per iteration; target median <2 seconds per pump call.

### RETRO-4 · Prolonged STALLED sequence (iters 10–17) suggests weak halt escalation
- **Proposed:** P1 · Effort M · Risk MED
- **Problem:** After iter 10 STALLED, seven more iterations (11–17) returned STALLED or REGRESSION verdicts. The goal loop did not break out of an unproductive state; instead, it continued rerunning the same evaluators and agents. Repeated STALLEDs should trigger user escalation or goal infeasibility; instead, the session burned iteration budget.
- **Evidence:** Verdict sequence — "iter 10: STALLED, iter 11: REGRESSION, iter 12: STALLED, iter 13: STALLED, iter 14: STALLED, iter 15: STALLED, iter 16: STALLED, iter 17: STALLED" (lines 28–36).
- **Sketch:** Define halt policy: if 3 or more consecutive STALLED verdicts occur, or STALLED follows REGRESSION within 1 iteration, escalate to ENGINE_MANUAL_REVIEW or GOAL_INFEASIBLE. Add a stuck-loop counter to session.json; emit telemetry alert when counter reaches 2, allowing user intervention before further iteration budget is consumed.
- **Verify idea:** Next session: if a goal reaches 2 consecutive STALLEDs, the framework halts with ENGINE_MANUAL_REVIEW; verify no completed session produces 3+ STALLEDs in a row without user intervention.

### RETRO-5 · Incomplete/interrupted attempts lack root-cause instrumentation
- **Proposed:** P2 · Effort M · Risk LOW
- **Problem:** The wall-time breakdown records 8+ attempts marked "(incomplete/interrupted attempt)" with no verdict or wall time logged, scattered across iters 0–12. The reasons for incompleteness (timeout, signal, dispatch error, pump unavailable, user pause) are not recorded, blocking diagnosis of systematic failure modes.
- **Evidence:** Agent economics (Per-step wall breakdown) — "goal-market-compass-iter-0  depth=?  verdict=?  wall=?  (incomplete/interrupted attempt)" (line 63), "goal-market-compass-iter-1  depth=full  verdict=?  wall=?  (incomplete/interrupted attempt)" (line 81), "goal-market-compass-iter-5  depth=lean  verdict=?  wall=?  (incomplete/interrupted attempt)" (line 158), "goal-market-compass-iter-8  depth=full  verdict=?  wall=?  (incomplete/interrupted attempt)" (line 198), similar patterns in iters 9, 10, 12.
- **Sketch:** Enhance engine event logger to capture why each attempt halts incompletely: agent timeout, process signal, dispatch error, pump unavailable, user pause, or other. Log this to telemetry as incomplete_reason field. Update wall-time reporter to include reason phrase in the breakdown (e.g., "incomplete/interrupted attempt: agent timeout").
- **Verify idea:** Next session: every "(incomplete/interrupted attempt)" line in the per-step wall breakdown includes a reason phrase; zero unexplained incomplete attempts in the report.
