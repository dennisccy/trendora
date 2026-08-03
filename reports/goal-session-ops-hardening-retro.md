# Session retro — ops-hardening

> **Ideas only — nothing here is scheduled work.** These are suggestions for
> improving the build system itself, not your product. A human reviews them and
> decides (promotion into docs/improvement-roadmap.md §16, the staging list).
> Codes: P0/P1/P2 = how urgent · Effort S/M/L = how much work · Risk LOW/MED/HIGH
> = chance a change breaks something else.

**Session:** ops-hardening · **Terminal status:** REGRESSION_HALT · **Iterations:** 43

## Candidate items

### RETRO-1 · Post-dev budget exhaustion and trim-mode churn
- **Proposed:** P1 · Effort M · Risk MED
- **Problem:** From iter 33 onwards, the post-dev-fanout step (running tests, QA, audits in parallel after developer finishes) consistently exceeds its 3600s budget. The budget-trim gate truncates agents mid-work, which may prevent full evaluation signals and contribute to escalation loops.
- **Evidence:** Agent economics — Wall-time report shows "OVER BUDGET at post-dev-fanout" warnings on iters 33, 34, 36, 37, 38, 39, 40, 41, 42. Example: "goal-ops-hardening-iter-36  depth=full  verdict=ESCALATE  wall=404.3m ... OVER BUDGET at post-dev-fanout: 6921s > 3600s (mode=trim)"
- **Sketch:** Investigate whether post-dev parallelism is over-subscribed: consider splitting into tighter groups (e.g., fast checks before heavy QA), increasing budget for full-depth mode, or adding a fast-path verdict gate that doesn't require browser-qa to complete. If budget overages are structural, document the trade-off and consider making trim-mode more observable to agents.
- **Verify idea:** Run a future session and measure whether relaxing or restructuring the post-dev budget reduces escalations and REGRESSION verdicts in the tail.

### RETRO-2 · Escalation-to-regression churn (seven ESCALATE in a row, then HALT)
- **Proposed:** P1 · Effort M · Risk MED
- **Problem:** Iters 35–41 produce seven consecutive ESCALATE verdicts, followed by a REGRESSION halt. This suggests the escalation gate (the framework mechanism meant to ask for owner help) was either triggered repeatedly for the same blocker, or the blocker evolved and escalation did not exit the loop.
- **Evidence:** Verdict sequence — "iter 35: ESCALATE, iter 36: ESCALATE, iter 37: ESCALATE, iter 38: ESCALATE, iter 39: ESCALATE, iter 40: ESCALATE, iter 41: ESCALATE, iter 42: REGRESSION"
- **Sketch:** Escalation verdicts should be rare; a run of seven suggests either (a) the evaluator's escalation criteria are too broad, (b) owner feedback was not acted on properly, or (c) the goal is mis-scoped. Add an escalation-saturation detector that alerts after 3+ escalations on the same journey/blocker, and log the reason each ESCALATE was chosen to enable post-session analysis.
- **Verify idea:** A future session with the same goal should not produce > 3 escalations in a row; if it does, investigate the goal definition and evaluator rubric.

### RETRO-3 · Developer agent wall-time dominance
- **Proposed:** P2 · Effort M · Risk LOW
- **Problem:** The developer agent consumed 1363.8m of total wall time, more than 40% of the total (3500m+ for all agents combined). The next highest is browser-qa-agent at 969.4m. This imbalance suggests work is not being decomposed or parallelized efficiently.
- **Evidence:** Agent economics — Per-session wall breakdown shows "total developer 1363.8m" vs "total browser-qa-agent 969.4m" vs "total goal-evaluator 648.6m". This is a 1.4× multiplier vs the second-largest consumer.
- **Sketch:** Review the developer agent's scope: is it doing work that should be parallelized (e.g., independent code fixes for separate failures)? Consider adding a "developer-multiplexer" pattern in the orchestrator that splits large development tasks into parallel subagents if the decomposer identifies independent fixes. Also audit whether developer is being called for verification work that could be pushed to reviewer or qa.
- **Verify idea:** Run a future iteration and compare the ratio of developer time to total wall time; aim for < 35% by delegating cross-cutting verification and secondary fixes to other agents.

### RETRO-4 · Large unattributed wall time in full-depth iterations
- **Proposed:** P2 · Effort S · Risk LOW
- **Problem:** Early full-depth iterations (1–17) show large unattributed wall time (100–600m per iteration). This "glue" time is likely test infrastructure, product startup, or other non-agent work, but it is not named. Without visibility, it is hard to optimize or diagnose slow iterations.
- **Evidence:** Agent economics — Wall-time report shows "unattributed (glue)" entries: iter-1 "unattributed (glue) 200.4m", iter-2 "584.5m", iter-3 "204.3m", iter-4 "220.8m". These dwarf many agent contributions.
- **Sketch:** Instrument the orchestrator to categorize unattributed time: separate test-run time, product-start time, fixture setup, and other overhead into named buckets. Emit a telemetry event at each checkpoint (pre-build, post-test, post-start) so the wall-time report can show "test framework: 150m" instead of "unattributed: 350m".
- **Verify idea:** A future session's wall-time report should show zero or <5% unattributed time, with all major phases named (e.g., "test-run: 120m", "startup: 45m").

### RETRO-5 · Incomplete attempt recovery adds iteration overhead
- **Proposed:** P2 · Effort M · Risk MED
- **Problem:** Multiple iterations (0, 5, 8, 18, 24, 27, 28, 29, 33, 39) show incomplete attempts followed by a resume and retry. Each retry costs full agent invocations. If the cause is transient (flaky dispatch, VM reset), the overhead is avoidable; if deterministic, the failures should be handled inline.
- **Evidence:** Friction counters — Wall-time report shows "(incomplete/interrupted attempt)" on iters 0 (twice), 5, 8, 18, 24, 27, 28, 29, 33, 39 (example: "goal-ops-hardening-iter-0  depth=?  verdict=?  wall=?  (incomplete/interrupted attempt)"). Halt context also lists: "halts: AWAITING_PUMP, AWAITING_PUMP, REGRESSION_HALT, BUDGET_EXHAUSTED, REGRESSION_HALT, STALLED, DECOMPOSER_FAILED, STALLED, STALLED, AWAITING_PUMP, machine_reset, AWAITING_PUMP, REGRESSION_HALT"
- **Sketch:** Log the root cause for every incomplete attempt (dispatch failure, budget exhausted, decomposer crashed, etc.). If AWAITING_PUMP or dispatch flakes are common, add retry logic with exponential backoff at the dispatch layer. If machine_reset is happening, harden the session checkpoint so a resume does not re-invoke agents that already completed.
- **Verify idea:** A future session should show zero or < 2 incomplete attempts; any remaining retries should have an explicit, non-transient root cause logged.

