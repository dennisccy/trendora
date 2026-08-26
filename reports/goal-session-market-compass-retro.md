# Session retro — market-compass

> **Ideas only — nothing here is scheduled work.** These are suggestions for
> improving the build system itself, not your product. A human reviews them and
> decides (promotion into docs/improvement-roadmap.md §16, the staging list).
> Codes: P0/P1/P2 = how urgent · Effort S/M/L = how much work · Risk LOW/MED/HIGH
> = chance a change breaks something else.

**Session:** market-compass · **Terminal status:** STALLED · **Iterations:** 20

## Candidate items

### RETRO-1 · Pipeline stages exceed time budgets repeatedly
- **Proposed:** P1 · Effort M · Risk MED
- **Problem:** Post-dev-fanout and browser-qa stages repeatedly exceed the 3600-second quota across many iterations, causing work to be trimmed. This suggests either the budget is miscalibrated for real workloads or these stages are inefficient.
- **Evidence:** Agent economics, per-step wall breakdown — "OVER BUDGET at post-dev-fanout: 4769s > 3600s (mode=trim)" (line 143), "OVER BUDGET at browser-qa: 5705s > 3600s (mode=trim)" (line 121), and similar pattern across lines 158, 179, 198, 245, 285, 324, 340, 356, 372, 429.
- **Sketch:** Profile the post-dev-fanout and browser-qa stages to identify which agents consume the most time; either raise quotas to realistic values based on observed workloads, or optimize agent efficiency by parallelizing work or reducing redundant checks. Start with a replay analysis to establish baseline and target.
- **Verify idea:** Re-run a similar-complexity goal and confirm that the per-step wall breakdown contains no "OVER BUDGET" entries for the same stages.

### RETRO-2 · Pump wait time dominates session wall-clock time
- **Proposed:** P1 · Effort M · Risk MED
- **Problem:** The session spent over 500 minutes waiting for pump responses (8+ hours of wall time), making pump latency a significant drag on iteration cycle time. High wait time slows feedback and extends session duration.
- **Evidence:** Agent economics, per-step wall breakdown — "total AWAITING_PUMP paused gaps: 503.0m" (line 448) and halt sequence "halts: AWAITING_PUMP, AWAITING_PUMP, AWAITING_PUMP, ..." (line 449).
- **Sketch:** Measure pump response-time distribution and distinguish processing time from scheduling/network latency; add telemetry for pump queue depth and per-request latency. Consider buffering or pre-computing common pump responses, or splitting pump into separate processes for different verdict types.
- **Verify idea:** Re-run a similar-size goal and measure that AWAITING_PUMP paused gaps drop below 10% of total session wall time.

### RETRO-3 · Incomplete iteration attempts lack root-cause instrumentation
- **Proposed:** P2 · Effort M · Risk LOW
- **Problem:** Many iterations show multiple "(incomplete/interrupted attempt)" markers before reaching a final verdict, indicating retries or transient engine failures. Without structured logging of retry causes, it is hard to distinguish expected retries from framework instability or identify optimization opportunities.
- **Evidence:** Verdict sequence / per-step wall breakdown — Multiple iterations (0, 1, 3, 5, 8, 9, 10, 12, 18) show patterns such as "goal-market-compass-iter-0  depth=?  verdict=?  wall=?  (incomplete/interrupted attempt)" (line 65) before reaching their final verdict entries.
- **Sketch:** Add structured telemetry to distinguish between: (a) expected retries after an agent error verdict, (b) pump crash/recovery, (c) timeout-triggered restart, (d) manual pause/resume. Tag each incomplete attempt with its root cause in telemetry events.
- **Verify idea:** After instrumentation, re-run goal-mode sessions and verify that the retro digest includes a breakdown showing retry count and root-cause distribution (e.g., "2 pump-recovery, 3 agent-error-retry, 1 timeout").
