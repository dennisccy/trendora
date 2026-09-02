# Session retro — market-compass

> **Ideas only — nothing here is scheduled work.** These are suggestions for
> improving the build system itself, not your product. A human reviews them and
> decides (promotion into docs/improvement-roadmap.md §16, the staging list).
> Codes: P0/P1/P2 = how urgent · Effort S/M/L = how much work · Risk LOW/MED/HIGH
> = chance a change breaks something else.

**Session:** market-compass · **Terminal status:** GOAL_ACHIEVED · **Iterations:** 41

## Candidate items

### RETRO-1 · Post-dev-fanout quota design misalignment
- **Proposed:** P1 · Effort M · Risk MED
- **Problem:** The pipeline stage post-dev-fanout (which runs auditor, qa, ui-test-designer, and other agents in parallel) consistently exceeds its 3600s budget by 40–400%, truncating work in trim mode. This affects roughly 1 in 4 iterations and loses iteration quality.
- **Evidence:** Agent economics wall-time report — "OVER BUDGET at post-dev-fanout: 4769s > 3600s (mode=trim)" (iter 3), "OVER BUDGET at post-dev-fanout: 6063s > 3600s (mode=trim)" (iter 14), "OVER BUDGET at post-dev-fanout: 16335s > 3600s (mode=trim)" (iter 19), "OVER BUDGET at post-dev-fanout: 17833s > 3600s (mode=trim)" (iter 22)
- **Sketch:** Audit which agents run in post-dev-fanout and their actual wall-time ranges. Either increase the budget to 6000–6500s (matching measured needs) or separate independent agents (auditor vs. qa) into non-blocking parallel paths so neither starves the other's time.
- **Verify idea:** Run a 10-iteration trial with the fix; measure total post-dev-fanout wall time and trim-mode activation count. Target: zero trim-mode cutoffs or at least one agent always completes fully.

### RETRO-2 · Reviewer agent dominates wall time and times out on first attempt
- **Proposed:** P1 · Effort M · Risk LOW
- **Problem:** Reviewer is the single highest wall-time consumer (1803.1m total, nearly tied with developer at 1791.8m) and times out frequently, with 4 first-attempt FAILs that force retries. Reviewer alone accounts for 22% of the session's wall time.
- **Evidence:** Friction counters — "Attempt-1 review FAILs: 4"; Agent economics — "total reviewer 1803.1m"; wall-time report — "reviewer 300.0m calls=1 failures=1" (iter 8), "reviewer 373.9m calls=2 failures=1" (iter 7), "reviewer 152.5m calls=1" (iter 6)
- **Sketch:** Profile reviewer's invocations to identify which code diffs or feedback patterns cause timeouts. Check for: unbounded loops in verdict synthesis, LLM prompts that grow with iteration history, or redundant re-analysis of prior code. Split quick-pass structural review from detailed feedback synthesis.
- **Verify idea:** Run 10 iterations after fix; measure reviewer wall time per call. Target: <100m per lean iteration, zero first-attempt FAILs.

### RETRO-3 · AWAITING_PUMP coordination wastes 923.6 wall minutes
- **Proposed:** P1 · Effort L · Risk HIGH
- **Problem:** The engine spent 923.6 minutes (14+ occurrences) waiting for the pump to respond, indicating lossy pump liveness detection or dispatch reliability. These long idle gaps frustrate iteration pacing and inflate total session time by ~15%.
- **Evidence:** Agent economics wall-time report — "total AWAITING_PUMP paused gaps: 923.6m"; Halt context halts list — "halts: AWAITING_PUMP, AWAITING_PUMP, AWAITING_PUMP, AWAITING_PUMP, AWAITING_PUMP, AWAITING_PUMP, ... [14 listed]"
- **Sketch:** Instrument the pump dispatch protocol: add pump heartbeat file with timestamp + PID, engine polls every 30s, escalates to user if heartbeat stales >60s. On pump restart, clear the stale heartbeat so engine unblocks immediately. Log all AWAITING_PUMP transitions with duration and restart outcome.
- **Verify idea:** Run a trial session; log all AWAITING_PUMP->RUNNING transitions. Target: zero AWAITING_PUMP halts lasting >60s, or automatic recovery (e.g., engine auto-restarts pump) on detection.

### RETRO-4 · Goal-evaluator budget exhaustion correlates with STALLED streak
- **Proposed:** P1 · Effort M · Risk MED
- **Problem:** Goal-evaluator hits budget ceiling multiple times (iters 10, 33) and the 9-iteration STALLED streak (iters 10–18) aligns with evaluator timeouts. This suggests evaluator's verdict logic scales poorly with goal/journey count.
- **Evidence:** Agent economics wall-time report — "OVER BUDGET at goal-evaluator: 3757s > 3600s (mode=trim)" (iter 10); Verdict sequence — "iter 10: STALLED iter 11: REGRESSION iter 12: STALLED iter 13: STALLED iter 14: STALLED iter 15: STALLED iter 16: STALLED iter 17: STALLED iter 18: STALLED"
- **Sketch:** Profile goal-evaluator's journey validation and evidence-collection logic. Check for: re-execution of journeys inside verdict (should use cached test results), evidence-synthesis loops that walk every prior iteration, or LLM prompts that grow linearly with history. Optimize or split into separate phases.
- **Verify idea:** Measure goal-evaluator call time before/after fix across 20 iterations. Target: <2000s per call, zero OVER BUDGET marks at goal-evaluator.

### RETRO-5 · Incomplete/interrupted attempts indicate pump or engine instability
- **Proposed:** P0 · Effort L · Risk HIGH
- **Problem:** At least 12 iterations have "incomplete/interrupted attempt" phases that never produce a verdict (iters 0, 1, 3, 5, 8, 9, 10, 12, 18, 20, 21, 25, 27, 28), suggesting the pump or engine crashes, hangs, or times out mid-iteration. These restarts add uncertainty and waste wall time.
- **Evidence:** Agent economics wall-time report — "goal-market-compass-iter-0 depth=? verdict=? wall=? (incomplete/interrupted attempt)" (line 86), "goal-market-compass-iter-1 depth=full verdict=? wall=? (incomplete/interrupted attempt)" (line 104), repeated pattern at iters 3, 5, 8–10, 12, 18, 20–21, 25, 27–28
- **Sketch:** Capture engine and pump stderr/logs during incomplete attempts. Add restart-reason field to session.json (pump timeout, disk full, engine panic, user signal, etc.). Implement pre-flight checks: pump heartbeat validation before engine resumes, engine state sanity check on iteration restart.
- **Verify idea:** Run a 30-iteration trial; count and categorize incomplete attempts. Target: zero incomplete attempts due to system failure (only user-initiated pauses acceptable).
