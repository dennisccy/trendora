# Session retro — market-compass

> **Ideas only — nothing here is scheduled work.** These are suggestions for
> improving the build system itself, not your product. A human reviews them and
> decides (promotion into docs/improvement-roadmap.md §16, the staging list).
> Codes: P0/P1/P2 = how urgent · Effort S/M/L = how much work · Risk LOW/MED/HIGH
> = chance a change breaks something else.

**Session:** market-compass · **Terminal status:** STALLED · **Iterations:** 15

## Candidate items

### RETRO-1 · Verdict loop cannot escape escalation→stalled→regression churn
- **Proposed:** P0 · Effort M · Risk MED
- **Problem:** The goal reached STALLED at iter 10, spiked REGRESSION at iter 11, then got stuck looping STALLED for the last 4 iterations. The framework lacks a circuit-breaker to halt escalation/stalled churn and request human decision.
- **Evidence:** Verdict sequence — "iter 2: ESCALATE\niter 6: ESCALATE\niter 10: STALLED\niter 11: REGRESSION\niter 12: STALLED\niter 13: STALLED\niter 14: STALLED" (lines 19-33)
- **Sketch:** Add rule: if verdict is STALLED and next verdict is REGRESSION (or STALLED persists >3 consecutive iters), emit REQUIRES_OWNER_DECISION instead of looping. Audit goal-evaluator and coherence-auditor to find why iter-11 spiked REGRESSION after iter-10 STALLED.
- **Verify idea:** Inspect iter-11/12 evaluator logs for root cause; run next 3 sessions and measure whether new circuit-breaker prevents looping.

### RETRO-2 · Budget overruns systematic and untracked across evaluation lanes
- **Proposed:** P1 · Effort S · Risk LOW
- **Problem:** Eleven of fourteen completed iterations exceeded their per-lane 1-hour budget limit (browser-qa, qa-loop, post-dev-fanout, goal-evaluator lanes). Iter 6 browser-qa hit 3.4 hours; iter 14 post-dev-fanout hit 1.7 hours. The system silently invokes "mode=trim" but has no counter tracking how often this occurs or what work was cut.
- **Evidence:** Friction counters — missing "trim_mode_invocations" counter (lines 358-362). Wall-time report — "OVER BUDGET at browser-qa: 12205s > 3600s (mode=trim)" (line 174, iter 6), "OVER BUDGET at post-dev-fanout: 6063s > 3600s (mode=trim)" (line 335, iter 14)
- **Sketch:** Add two telemetry counters: trim_mode_invocations and trimmed_step_count (per session). Log which lane(s) were trimmed and how many steps skipped. Cross-check if trimmed lane verdicts diverge from untrimmed baseline.
- **Verify idea:** Next session: if trim_mode_invocations > 0, compare trimmed lane verdicts to prior runs without trim. If verdicts diverge, either increase budget or refactor lane into finer sub-gates.

### RETRO-3 · Reviewer wall-time dominance and failure-retry pattern
- **Proposed:** P1 · Effort M · Risk MED
- **Problem:** Reviewer accumulated 946.8m total wall time (7.8 hours more than developer). Iter 6: 152.5m (ESCALATE). Iter 7: 373.9m across 2 calls with 1 failure, yet iteration continued. Single reviewer calls consuming 6+ hours suggest looping analysis or missing exit criteria.
- **Evidence:** Agent economics — "total reviewer 946.8m" (line 338), "total developer 822.9m" (line 339). Wall-time report — "iter 6: reviewer 152.5m calls=1" (line 163), "iter 7: reviewer 373.9m calls=2 failures=1" (line 177)
- **Sketch:** Instrument reviewer to emit per-step timings (code review, test review, integration). Flag any single call exceeding 30 minutes. Audit iter-7 failure: was it a resource timeout or logic error? Consider splitting review into sequential gates (syntax first, then logic) so late failures don't re-review everything.
- **Verify idea:** In next 3 sessions, monitor reviewer per-call durations via telemetry. If calls >30m are rare (<5% of calls), no change needed. If frequent, escalate to skill or model review.

### RETRO-4 · Incomplete/interrupted attempts leak through, no recovery tracking
- **Proposed:** P1 · Effort S · Risk LOW
- **Problem:** Six completed iterations showed 1–2 incomplete/interrupted attempts before final verdict (iters 1, 3, 8, 9, 10, 12). Iter 5 has no final verdict and no clear reason why. These halts are not counted in friction metrics, making it impossible to diagnose if they are timeout, resource, or pump liveness issues.
- **Evidence:** Wall-time report — "iter 1: (incomplete/interrupted attempt)" (line 78), "iter 5: (incomplete/interrupted attempt)" (line 155), "iter 8: (incomplete/interrupted attempt)" (line 195), "iter 9: (incomplete/interrupted attempt)" (line 219), "iter 10: (incomplete/interrupted attempt)" (line 242)
- **Sketch:** Add telemetry counter: incomplete_attempt_reasons (timeout, agent_failure, pump_unavailable, resource_exhausted). When an attempt is interrupted, log the reason. Cross-check with AWAITING_PUMP halt list (line 355) — if pump liveness is culprit, fix pump detection; if agent failures, improve error propagation.
- **Verify idea:** Run next session with reason tracking. Goal: incomplete_attempts <3 per 15-iteration session, and >90% of reasons are attributable to a known cause.

### RETRO-5 · AWAITING_PUMP halts accumulate 501 minutes, liveness detection weak
- **Proposed:** P2 · Effort M · Risk MED
- **Problem:** Session halted with AWAITING_PUMP 501.7m of idle wall time (line 354) across multiple pause/resume cycles (line 355). The pump is not responsive or the liveness check is not detecting death. This directly causes incomplete attempts and extends session duration.
- **Evidence:** Wall-time report — "total AWAITING_PUMP paused gaps: 501.7m" (line 354), "halts: AWAITING_PUMP, AWAITING_PUMP, AWAITING_PUMP, STALLED, REGRESSION_HALT, STALLED, STALLED, STALLED" (line 355)
- **Sketch:** Audit pump liveness logic: is the heartbeat/timeout window appropriate for goal-mode wall times (this session had iters >3h)? Check if pump PID is stale. Add a timeout (e.g., if AWAITING_PUMP >120s, force restart or escalate). Review memory notes on pump-PID-ancestry and heartbeat-keepalive lessons (potential related prior fixes).
- **Verify idea:** Next session: monitor AWAITING_PUMP gap duration; if max gap >60s or cumulative >120m, the pump needs hardening. Check telemetry for pump restart count.
