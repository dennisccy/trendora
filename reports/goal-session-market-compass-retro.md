# Session retro — market-compass

> **Ideas only — nothing here is scheduled work.** These are suggestions for
> improving the build system itself, not your product. A human reviews them and
> decides (promotion into docs/improvement-roadmap.md §16, the staging list).
> Codes: P0/P1/P2 = how urgent · Effort S/M/L = how much work · Risk LOW/MED/HIGH
> = chance a change breaks something else.

**Session:** market-compass · **Terminal status:** STALLED · **Iterations:** 13

## Candidate items

### RETRO-1 · Reviewer agent dominates session time and repeatedly times out
- **Proposed:** P0 · Effort M · Risk MED
- **Problem:** The reviewer spent 918.8 minutes (39% of all agent time) with multiple catastrophic hangs. Iter-7 and iter-8 each took 300+ minutes on review and both reported failures, forcing iteration restarts and preventing goal progress.
- **Evidence:** Agent economics (wall-time report) — "total reviewer 918.8m" with iter-7 showing "reviewer 373.9m calls=2 failures=1" and iter-8 showing "reviewer 300.0m calls=1 failures=1".
- **Sketch:** Profile reviewer to isolate what triggers 300m+ hangs (likely large code diffs or complex refactoring). Implement staged review: fast auto-checks for small changes, deep review only on large deltas. Add explicit timeout with fallback (flag for triage instead of blocking). Monitor and alert on reviewer calls >60m.
- **Verify idea:** Future sessions show reviewer using <50m per lean iteration and <5% of total session wall time.

### RETRO-2 · Iteration budget (3600s) exceeded in 10 stages; trim mode unenforced
- **Proposed:** P1 · Effort S · Risk LOW
- **Problem:** Ten iteration stages logged "OVER BUDGET" messages (qa-loop, browser-qa, post-dev-fanout regularly exceeded 3600s quota), but all agents still ran to completion. The budget appears miscalibrated or not enforced, creating unpredictable iteration length.
- **Evidence:** Wall-time report — lines 99, 114, 136, 151, 172, 191, 238, 262, 278, 292 all show "OVER BUDGET at <stage>: <seconds> > 3600s (mode=trim)".
- **Sketch:** Audit whether 3600s is based on historical data or guesswork and adjust threshold. Add per-agent limits within each stage so trim mode can skip expensive agents selectively. Track "budget utilization %" per session for future tuning and document the budget policy.
- **Verify idea:** Tuned budget results in <30% of iterations exceeding quota, or budget policy is documented for maintainers.

### RETRO-3 · Orchestrator transient hang (340.9m) in iter-9; no diagnostic instrumentation
- **Proposed:** P1 · Effort M · Risk MED
- **Problem:** Iter-9's orchestrator took 340.9 minutes and failed on first attempt, then succeeded in 9.4 minutes on retry (36× speedup). This indicates an undiagnosed external dependency stall (pump, service unavailability, resource contention), but no instrumentation logged the cause.
- **Evidence:** Wall-time report — iter-9 incomplete attempt (line 218): "orchestrator 340.9m calls=1 failures=1" with "pump-wait 341.1m"; iter-9 retry (line 230): "orchestrator 9.4m calls=1" with "pump-wait 0.2m".
- **Sketch:** Add substep logging to orchestrator so future hangs can be traced (which decompose step, which dispatch call). Implement explicit timeout (60m) with escalation instead of silent hang. Consider preflight dependency checks (app availability, pump state) before dispatch. Correlate orchestrator hangs with pump/engine logs to find root cause.
- **Verify idea:** Future sessions show zero orchestrator failures and all orchestrator calls complete in <20m.

