# Session retro — market-compass

> **Ideas only — nothing here is scheduled work.** These are suggestions for
> improving the build system itself, not your product. A human reviews them and
> decides (promotion into docs/improvement-roadmap.md §16, the staging list).
> Codes: P0/P1/P2 = how urgent · Effort S/M/L = how much work · Risk LOW/MED/HIGH
> = chance a change breaks something else.

**Session:** market-compass · **Terminal status:** REGRESSION_HALT · **Iterations:** 12

## Candidate items

### RETRO-1 · browser-qa stage budget overflow in lean iterations
- **Proposed:** P1 · Effort M · Risk LOW
- **Problem:** The browser-qa stage hits the 3600s quota limit in 4 lean-depth iterations (1, 2, 4, 6), suggesting the stage is consistently underbudgeted or tasks are serially queued instead of parallel.
- **Evidence:** Wall-time report — "OVER BUDGET at browser-qa: 5705s > 3600s" (iter 1, 2), "OVER BUDGET at browser-qa: 3864s > 3600s" (iter 4), "OVER BUDGET at browser-qa: 12205s > 3600s" (iter 6)
- **Sketch:** Profile browser-qa and browser-qa-replay execution; check whether replay is queued serially after qa instead of in parallel. Increase lean-mode browser-qa quota to 5500s or parallelize replay track.
- **Verify idea:** Run lean-depth iterations and confirm browser-qa wall times stay under quota; measure OVER BUDGET message count.

### RETRO-2 · post-dev-fanout stage budget overflow in full iterations
- **Proposed:** P1 · Effort M · Risk MED
- **Problem:** The post-dev-fanout stage exceeds its 3600s quota in all 4 full-depth iterations that reach it (3, 7, 9, 11), suggesting parallel fanout tasks are competing for resources or the quota is too tight.
- **Evidence:** Wall-time report — "OVER BUDGET at post-dev-fanout: 4769s > 3600s" (iter 3), "4319s > 3600s" (iter 7), "4809s > 3600s" (iter 9), "3752s > 3600s" (iter 11)
- **Sketch:** Measure CPU/memory utilization during post-dev-fanout; consider descheduling optional agents (auditor, qa, ui-impact-analyst) for certain iteration types, or raise full-depth fanout quota to 5000s.
- **Verify idea:** Confirm post-dev-fanout iterations complete within quota and CPU utilization stays even across parallel agents.

### RETRO-3 · Incomplete/interrupted iteration attempts lack clear halt reason
- **Proposed:** P1 · Effort S · Risk LOW
- **Problem:** Multiple iterations show failed attempts that restart before producing a final verdict (iter 1, 3, 8, 9, 10), consuming extra wall time and obscuring why the restart occurred.
- **Evidence:** Wall-time report — "(incomplete/interrupted attempt)" blocks appearing before final verdicts; example: iter 1 shows two failed attempts before CONTINUE, iter 9 shows two failed attempts before CONTINUE
- **Sketch:** Add deterministic logging to dispatch/resume to emit why an attempt halted (timeout, agent crash, pump disconnect, user pause, etc.). Export reason to telemetry structured field.
- **Verify idea:** New sessions should have zero incomplete attempts for clean runs; check telemetry for reason frequency and alert on unexpected patterns.

### RETRO-4 · Reviewer wall-time dominance and failure pattern
- **Proposed:** P2 · Effort M · Risk MED
- **Problem:** Reviewer accumulated 909.6m total wall time, exceeding developer's 714.1m by 27%. Two iterations (7, 8) show reviewer failures with extreme wall times (373.9m, 300.0m), suggesting tasks timeout or get stuck.
- **Evidence:** Agent economics table — "reviewer | 5 invocations"; Wall-time report — "reviewer 373.9m calls=1 failures=1" (iter 7), "reviewer 300.0m calls=1 failures=1" (iter 8); total reviewer 909.6m vs developer 714.1m
- **Sketch:** Profile reviewer task hot paths; consider breaking large reviews into parallel subtracks or add progress-check timeouts. Investigate why iter 7 and 8 reviewer calls failed.
- **Verify idea:** Confirm reviewer wall time per invocation < 90m and failure count drops to zero; reviewer time should be ≤ developer time.

### RETRO-5 · AWAITING_PUMP gaps total 501.7m, indicating pump starvation
- **Proposed:** P2 · Effort S · Risk LOW
- **Problem:** The pump spent 501.7m idle (over 8 hours, 13% of total wall time) in AWAITING_PUMP state. Halt context lists 3 AWAITING_PUMP halts, showing the pump restarted due to starvation multiple times.
- **Evidence:** Wall-time report tail — "total AWAITING_PUMP paused gaps: 501.7m"; Halt context — "halts: AWAITING_PUMP, AWAITING_PUMP, AWAITING_PUMP, STALLED, REGRESSION_HALT"
- **Sketch:** Instrument pump entry/exit points to log what state it waits for (decomposer ready? evaluator ready?). Add per-iteration AWAITING_PUMP budgets (target < 50m) and alert if exceeded.
- **Verify idea:** Run with pump instrumentation; confirm new sessions show < 50m AWAITING_PUMP per iteration; check telemetry for bottleneck (decomposer vs evaluator latency).
