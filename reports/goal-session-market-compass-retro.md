# Session retro — market-compass

> **Ideas only — nothing here is scheduled work.** These are suggestions for
> improving the build system itself, not your product. A human reviews them and
> decides (promotion into docs/improvement-roadmap.md §16, the staging list).
> Codes: P0/P1/P2 = how urgent · Effort S/M/L = how much work · Risk LOW/MED/HIGH
> = chance a change breaks something else.

**Session:** market-compass · **Terminal status:** STALLED · **Iterations:** 14

## Candidate items

### RETRO-1 · Pipeline evaluation budget trim fires in 8 of 13 completed iterations
- **Proposed:** P1 · Effort M · Risk MED
- **Problem:** The evaluation pipeline routinely exceeds its 1-hour (3600s) stage budget, forcing trim mode on most iterations. This means downstream agents receive incomplete context for decisions, and the timeout design does not match real workload.
- **Evidence:** Friction counters (wall-time report) — "OVER BUDGET at qa-loop: 4178s > 3600s (mode=trim)" (iter-1), "OVER BUDGET at browser-qa: 5705s > 3600s (mode=trim)" (iter-2), "OVER BUDGET at post-dev-fanout: 4769s > 3600s (mode=trim)" (iter-3), "OVER BUDGET at browser-qa: 3864s > 3600s (mode=trim)" (iter-4), "OVER BUDGET at browser-qa: 12205s > 3600s (mode=trim)" (iter-6), "OVER BUDGET at post-dev-fanout: 4319s > 3600s (mode=trim)" (iter-7), "OVER BUDGET at post-dev-fanout: 4809s > 3600s (mode=trim)" (iter-9), "OVER BUDGET at goal-evaluator: 3757s > 3600s (mode=trim)" (iter-10), and 3 more in iter-11/12/13
- **Sketch:** Audit the 3600s limit: is it per-gate or total? Collect real stage times from past sessions to set empirical limits. Separate budgets for lean vs. full-depth (full may need +40%). Implement per-agent trim priorities so critical evaluators (goal-evaluator, browser-qa) are protected while optional steps (demo-narrator) skip first.
- **Verify idea:** Run next 3 goal sessions; track % exceeding budget. Target <25% vs. current 62%.

### RETRO-2 · Session accumulates 501.7m waiting for pump/services to be healthy
- **Proposed:** P1 · Effort M · Risk MED
- **Problem:** The session spent over 8 hours in idle AWAITING_PUMP status. This is dead time — no agent is running — that directly extends session wall time and delays feedback loops. Dominant contributors: iter-7 (373.9m wait) and iter-9 incomplete attempt (341.1m wait).
- **Evidence:** Agent economics (wall-time report) — "total AWAITING_PUMP paused gaps: 501.7m" with "pump-wait 373.9m" in iter-7 and "pump-wait 341.1m" in iter-9 incomplete attempt (line 223)
- **Sketch:** Instrument pump liveness: add telemetry counters for "pump_startup_attempts", "pump_liveness_check_failures", "service_healthcheck_latency_p50" per iteration. Measure if services are slow to become healthy or if the check threshold is overly conservative. Investigate whether services crash mid-session. Consider preflight service warm-up or caching health state between iterations.
- **Verify idea:** Measure AWAITING_PUMP gap on next 3 goal sessions; target 50% reduction (from 500m to <250m per 14-iteration session).

### RETRO-3 · Incomplete/interrupted iteration attempts not instrumented; stability gap
- **Proposed:** P2 · Effort S · Risk LOW
- **Problem:** The telemetry shows many iterations with "incomplete/interrupted attempt" entries — visual count suggests 10–13 restarts — but no friction counter tracks how often or why they occur. These hidden retries conceal crashes, dispatch failures, or executor instability that a framework fix could prevent.
- **Evidence:** Friction counters (wall-time report) — no "incomplete_attempt_count" exists; wall-time data shows "goal-market-compass-iter-0  depth=?  verdict=?  wall=?  (incomplete/interrupted attempt)" on lines 59, 62, 77, 117, 154, 194, 218, 224, 241, 247, 281 — untracked.
- **Sketch:** Add telemetry event `iteration_attempt_incomplete` logged by the engine whenever an iteration restarts mid-flight. Include reason code: crash, dispatch_timeout, executor_error, pump_unavailable. Aggregate into session.json as `incomplete_attempt_count` with per-reason breakdown.
- **Verify idea:** Re-run telemetry collector on this session; new counter correctly reports all incomplete attempts; reason breakdown matches engine logs.

### RETRO-4 · Reviewer agent single-call slowness drives 928m total agent time (28% of load)
- **Proposed:** P2 · Effort M · Risk MED
- **Problem:** The reviewer is the single largest consumer of pipeline time (928m total, 28% of all session active work), with two calls >150m (iter-6: 152.5m, iter-7 call 1: 373.9m). Reviewer slowness directly extends each iteration's turnaround and may indicate inefficient artifact handling or unbounded problem scope.
- **Evidence:** Agent economics (session totals) — "total reviewer 928.0m" (line 321); wall-time report shows "iter-6 reviewer 152.5m calls=1" (line 162) and "iter-7 reviewer 373.9m calls=2 failures=1" (line 176)
- **Sketch:** Profile one slow reviewer invocation (capture artifact size, refactor extent, depth of analysis). Set soft limit (30m) and hard limit (90m) per call. If soft exceeded, add escalation flag for triage. If hard exceeded, split review into chunks (per-file, per-module). Add telemetry for reviewer_time_per_artifact_bytes to detect pathological cases.
- **Verify idea:** Measure median reviewer call time on next 5 full-depth iterations; target <20m median (vs. current peak 373m indicating systemic slowness).
