# Session retro — market-compass

> **Ideas only — nothing here is scheduled work.** These are suggestions for
> improving the build system itself, not your product. A human reviews them and
> decides (promotion into docs/improvement-roadmap.md §16, the staging list).
> Codes: P0/P1/P2 = how urgent · Effort S/M/L = how much work · Risk LOW/MED/HIGH
> = chance a change breaks something else.

**Session:** market-compass · **Terminal status:** STALLED · **Iterations:** 19 (18 completed)

## Candidate items

### RETRO-1 · Persistent per-stage wall-time budget overruns reduce iteration quality
- **Proposed:** P1 · Effort M · Risk MED
- **Problem:** Fourteen of eighteen completed iterations hit "OVER BUDGET" warnings, with quota shortfalls ranging 15–70 percent. The mode is "trim" — agent outputs are being truncated at quota boundaries, leaving incomplete verdicts and forcing iteration rework.
- **Evidence:** Agent economics (Per-step wall breakdown) — "OVER BUDGET at qa-loop: 4178s > 3600s (mode=trim)" (line 105); "OVER BUDGET at browser-qa: 5705s > 3600s (mode=trim)" (line 120); "OVER BUDGET at browser-qa: 12205s > 3600s (mode=trim)" (line 178); similar entries at iters 1, 2, 3, 4, 6, 7, 9, 10, 13, 14, 15, 16, 17.
- **Sketch:** Audit current per-stage quotas in goal-mode pipeline config. Measure actual median and 95th-percentile wall time per agent across agents. Increase quotas for stages (browser-qa, post-dev-fanout, qa-loop) that consistently exceed 3600s, or decompose long-running stages into parallel substeps. Rebalance agent allocation based on measured workload.
- **Verify idea:** Next session: count "OVER BUDGET" warnings; target fewer than 3 overruns in 10 completed iterations.

### RETRO-2 · Reviewer wall-time dominance with repeated failures
- **Proposed:** P1 · Effort M · Risk MED
- **Problem:** The reviewer agent consumed 1001.8m total wall time across the session — more than any other single agent and nearly equal to the developer — and exhibited failures at iters 7–8 with extreme per-call durations (300–373m). High reviewer load combined with repeated failures suggests either scope creep in evidence auditing or systematic instability in the agent's core logic.
- **Evidence:** Agent economics — "total reviewer 1001.8m" (line 417); Wall breakdown: "reviewer 373.9m calls=2 failures=1" at iter-7 (line 181); "reviewer 300.0m calls=1 failures=1" at iter-8 (line 200); Friction counters — "Attempt-1 review FAILs: 1" (line 439).
- **Sketch:** Profile reviewer evidence sets and deliverables per iteration to identify scope creep: Are full-pipeline iterations triggering duplicate or overlapping review passes? Does the evidence corpus grow unbounded? Add telemetry to log which artifacts and decision trees the reviewer traverses per run. Consider splitting review into shallow pre-dev and deep post-dev phases, or gating review depth based on prior iteration's review outcome.
- **Verify idea:** Next session: measure reviewer total wall time as a ratio to developer (target <1.1×); achieve zero review failures on attempt 1.

### RETRO-3 · High AWAITING_PUMP paused gaps indicate pump latency or availability bottleneck
- **Proposed:** P1 · Effort S · Risk LOW
- **Problem:** The pipeline spent 503.0m (8.4 hours) blocked in AWAITING_PUMP state waiting for the pump (the engine dispatcher service) to respond. Multiple AWAITING_PUMP halts across the session indicate pump availability issues or dispatch-queue latency that directly extends per-iteration wall time and reduces throughput.
- **Evidence:** Agent economics (Per-step wall breakdown) — "total AWAITING_PUMP paused gaps: 503.0m" (line 432); "halts: AWAITING_PUMP, AWAITING_PUMP, AWAITING_PUMP, STALLED, REGRESSION_HALT, STALLED, STALLED, STALLED, STALLED, STALLED, STALLED, STALLED, STALLED, AWAITING_PUMP, STALLED" (line 433).
- **Sketch:** Profile pump dispatch latency in telemetry: measure per-call round-trip time, queue depth on each agent dispatch, and pump restart patterns between iterations. If restarts cascade delays or if median latency >2 seconds per call, identify root cause (CPU contention, I/O, subprocess overhead) and optimize dispatch batching or pump responsiveness. Implement pump liveness heartbeat to detect and fast-fail on pump hangs instead of indefinite wait.
- **Verify idea:** Next session: add pump dispatch latency counters to telemetry; report median and 95th-percentile latency per iteration; target median <2 seconds per pump call and zero AWAITING_PUMP halts >5 minutes.

### RETRO-4 · Prolonged STALLED verdict sequence indicates weak halt escalation
- **Proposed:** P1 · Effort M · Risk MED
- **Problem:** After iter-10 returned STALLED, eight of the next nine iterations (11–18) also returned STALLED or REGRESSION. The goal loop did not break out of the unproductive state; instead, it continued rerunning the same evaluators and agents. Repeated STALLEDs signal the goal is infeasible or the iteration strategy is broken, yet the session burned 9 more iterations before halting externally.
- **Evidence:** Verdict sequence — "iter 10: STALLED / iter 11: REGRESSION / iter 12: STALLED / iter 13: STALLED / iter 14: STALLED / iter 15: STALLED / iter 16: STALLED / iter 17: STALLED / iter 18: STALLED" (lines 28–37).
- **Sketch:** Define halt escalation policy: if 2 or more consecutive STALLED verdicts occur, emit a stuck-loop warning and increment a counter in session.json. If the counter reaches 3, halt with ENGINE_MANUAL_REVIEW instead of STALLED. Alternatively, if STALLED follows REGRESSION within 1 iteration, treat as a signal of goal infeasibility and escalate immediately.
- **Verify idea:** Next session: no completed session produces more than 2 consecutive STALLED verdicts without user intervention; if it reaches 3, the framework halts with ENGINE_MANUAL_REVIEW in the verdict line.

### RETRO-5 · Incomplete iteration attempts lack root-cause instrumentation
- **Proposed:** P2 · Effort M · Risk LOW
- **Problem:** Eight or more attempts across iterations 0–18 are marked "(incomplete/interrupted attempt)" with no verdict logged and no recorded reason for the incompleteness. The causes (timeout, signal, dispatch error, pump unavailable, user pause) are not captured in telemetry, blocking diagnosis of systematic failure modes in the engine.
- **Evidence:** Agent economics (Per-step wall breakdown) — "goal-market-compass-iter-0  depth=?  verdict=?  wall=?  (incomplete/interrupted attempt)" (line 64); similar patterns at iters 1 (line 82), 3 (line 122), 5 (line 159), 8 (line 199), 9 (lines 223, 229), 10 (line 252), 12 (line 286), 18 (lines 389, 393).
- **Sketch:** Enhance engine event logger to capture why each attempt halts incompletely: agent timeout, process signal, dispatch error, pump unavailable, user pause, or other. Log this as an incomplete_reason field in telemetry. Update wall-time reporter to include the reason phrase in per-step breakdown (e.g., "incomplete/interrupted attempt: pump_timeout").
- **Verify idea:** Next session: every "(incomplete/interrupted attempt)" entry in per-step wall breakdown includes a reason phrase; zero unexplained incomplete attempts in the final report.
