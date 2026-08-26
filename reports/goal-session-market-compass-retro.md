# Session retro — market-compass

> **Ideas only — nothing here is scheduled work.** These are suggestions for
> improving the build system itself, not your product. A human reviews them and
> decides (promotion into docs/improvement-roadmap.md §16, the staging list).
> Codes: P0/P1/P2 = how urgent · Effort S/M/L = how much work · Risk LOW/MED/HIGH
> = chance a change breaks something else.

**Session:** market-compass · **Terminal status:** STALLED · **Iterations:** 18

## Candidate items

### RETRO-1 · Long STALLED sequence signals goal-loop stuck point
The goal evaluator and decomposer could not escape STALLED for 9 consecutive iterations (10–18), burning iteration quota and wall time with no recovery until session halt.
- **Proposed:** P1 · Effort M · Risk MED
- **Problem:** When an iteration verdict is STALLED, the next decomposition often re-engages the same path. After 3–4 consecutive STALLED verdicts, the loop has no escalation mechanism; it should flag for manual review or switch strategy.
- **Evidence:** Verdict sequence — "iter 10: STALLED" through "iter 18: STALLED" (lines 28–37); nine consecutive STALLED verdicts with no recovery.
- **Sketch:** Add a STALLED-persistence counter to goal-evaluator state. If consecutive STALLED verdicts reach 3, emit a "manual escalation required" signal with a structured summary (what changed last, what is blocking). Route to orchestrator or a human-confirmable pause.
- **Verify idea:** Next session with similar conditions will escalate after 3 STALLED with diagnostics, allowing manual inspection or re-parameterization.

### RETRO-2 · Budget trim mode opacity defeats convergence diagnosis
Many iterations exceed the 3600s wall-time budget at different pipeline steps (qa-loop, browser-qa, post-dev-fanout), trimming skipped agents silently. Agents do not know what was trimmed or why, making it impossible to diagnose whether STALLED is due to incomplete review or genuine blockage.
- **Proposed:** P1 · Effort M · Risk LOW
- **Problem:** Pipeline steps trim silently; the goal-evaluator and developers see end results but no visibility into which agents were skipped or how the budget shortfall affected evaluation completeness.
- **Evidence:** Agent economics (Per-step wall breakdown) — "OVER BUDGET at qa-loop: 4178s > 3600s (mode=trim)" (line 105); "OVER BUDGET at browser-qa: 5705s > 3600s (mode=trim)" (line 120); "OVER BUDGET at browser-qa: 12205s > 3600s (mode=trim)" (line 178); similar at iters 1, 2, 3, 4, 6, 7, 9, 10, 13–17.
- **Sketch:** When trim mode skips steps, emit a structured "budget report" attached to the iteration's state: which agents were skipped, which tests deferred, which reviews truncated. Log alongside the iteration verdict so the goal-evaluator can reason about evaluation completeness.
- **Verify idea:** Next session's iteration logs include budget impact summary; goal-evaluator can cite it when deciding whether to re-run a step or accept a verdict.

### RETRO-3 · Developer and Reviewer wall time imbalance lacks role clarity
Developer (1012.7m total) and Reviewer (1001.8m total) are nearly equal and consume 74% of session agent time. Telemetry does not distinguish what each agent reviews (code quality vs. goal alignment vs. test coverage), making it unclear if there is role overlap or genuine efficiency problem.
- **Proposed:** P2 · Effort S · Risk LOW
- **Problem:** When two agents take equal time, it is hard to optimize which tasks each should own or whether one is redundant. The absence of purpose tags in telemetry means future sessions will repeat the same blind spot.
- **Evidence:** Agent economics (session summary) — "total developer 1012.7m" and "total reviewer 1001.8m" as the two largest consumers (lines 416–417).
- **Sketch:** Tag each developer and reviewer invocation with a purpose (e.g., "code-quality", "goal-alignment", "test-coverage"). Emit a per-session role-separation report showing which purposes each agent handles and how time is split.
- **Verify idea:** Next session's telemetry will reveal whether the split is intentional and tuned, or overlapping; the report becomes input to next session's decomposition.

### RETRO-4 · Incomplete/interrupted attempts recur without root-cause instrumentation
Eight iterations (0, 1, 3, 5, 8, 9, 12, 18) show multiple "incomplete/interrupted attempt" entries before final verdict. Wall logs record that interruptions happened but do not explain why (pump unavailable, agent timeout, dispatch error, user pause).
- **Proposed:** P2 · Effort M · Risk LOW
- **Problem:** Without root-cause codes for interrupts, future sessions cannot distinguish transient glitches from systemic hangs, so corrective actions remain speculative.
- **Evidence:** Wall breakdown — "goal-market-compass-iter-0  depth=?  verdict=?  wall=?  (incomplete/interrupted attempt)" (line 64); "goal-market-compass-iter-1 depth=full verdict=? wall=? (incomplete/interrupted attempt)" with "failures=2" (line 82); recurs at iters 3, 5, 8, 9, 12, 18.
- **Sketch:** When an iteration attempt is interrupted before final verdict, capture and log the reason: PUMP_UNAVAIL, AGENT_TIMEOUT, DISPATCH_ERR, USER_PAUSE, or other enum. Store in telemetry and a "interrupts" ledger entry.
- **Verify idea:** Next session with similar interrupts will emit explicit reason codes; a retro report can then group interrupts by root cause and propose fixes.

### RETRO-5 · Guard side-effects lack systematic dependency audit
The iter-18 lesson describes a critical pattern: a quarantine guard suppressed a value (`ensure_latest_snapshot` returning None) that cascaded to disable a subsystem (warm-up via `main.py:113`). The framework has no systematic way to audit guard dependencies before or after arm-time.
- **Proposed:** P1 · Effort S · Risk MED
- **Problem:** Guards and kill-switches can have unintended knock-on effects in places far from insertion point. Future iterations touching guards or boot sequencing will repeat this blind spot without a dependency audit step.
- **Evidence:** Lessons tail — "Arming the quarantine silently disabled a whole subsystem: `ensure_latest_snapshot` returns `None` for a blocked latest date, and `main.py:113` starts the background warm-up only `if latest is not None`... Ask of every new blocking guard: what ELSE keys off the value this guard now suppresses?" (lines 460–463).
- **Sketch:** When an iteration proposal adds a guard/quarantine/kill-switch, require a "guard-dependencies" audit step: grep the codebase for all call sites of the guarded value, classify each as "returns None-tolerant", "expects value", or "requires warning", and document findings in the iteration's lesson entry.
- **Verify idea:** Next iteration adding a guard will produce a dependency audit; the audit will catch at least one unexpected call site or confirm none exist.
