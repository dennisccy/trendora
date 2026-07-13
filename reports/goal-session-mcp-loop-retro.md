# Session retro — mcp-loop

> **PROPOSALS ONLY** — a human promotes candidates into docs/improvement-roadmap.md §16
> per EVO-1; nothing here is scheduled work.

**Session:** mcp-loop · **Terminal status:** STALLED · **Iterations:** 29

## Candidate items

### RETRO-1 · Goal-decomposer mid-iteration failures and resume-skip patterns
- **Proposed:** P1 · Effort M · Risk MED
- **Problem:** Across iters 7–28, goal-decomposer fails mid-iteration (sometimes repeatedly), triggering incomplete attempts and resume-skip logic that silently drops prior work. This pattern correlates with the eventual STALLED halt and makes iteration recovery unpredictable.
- **Evidence:** Agent economics — "goal-mcp-loop-iter-7: (incomplete/interrupted attempt); goal-mcp-loop-iter-8: (incomplete/interrupted attempt); … goal-mcp-loop-iter-18: seven incomplete/interrupted attempts with one 120.4m call marked failures=1; goal-mcp-loop-iter-28: (incomplete/interrupted attempt)" and halt sequence: "DECOMPOSER_FAILED, DECOMPOSER_FAILED, DECOMPOSER_FAILED" (3 times listed).
- **Sketch:** Strengthen goal-decomposer's error recovery and logging: add explicit pre/post-state checkpoints so resume can be deterministic; log the exact failure reason (network, timeout, token limit, memory) for each failure, not just the count. Instrument whether resume-skip truly recovers the prior step or silently drops it.
- **Verify idea:** Run a session without resume-skip logic; confirm iters complete end-to-end without silent drops, and collect explicit failure categories in telemetry.

### RETRO-2 · Unattributed "glue" time dominates wall-time; instrumentation gap
- **Proposed:** P1 · Effort M · Risk LOW
- **Problem:** Starting mid-session, "unattributed (glue)" consumes 70–91% of iteration wall time (e.g., iter-23: 404.6m / 441.7m = 91%, iter-22: 291.6m / 344.4m = 85%). This obscures where time is actually spent and blocks root-cause analysis of performance regressions or pump blockages.
- **Evidence:** Agent economics — Per-step wall breakdown: "goal-mcp-loop-iter-22 wall=344.4m unattributed (glue) 291.6m; goal-mcp-loop-iter-23 wall=441.7m unattributed (glue) 404.6m; goal-mcp-loop-iter-24 wall=497.3m unattributed (glue) 440.2m" — consistently >80% unattributed across full-depth iters.
- **Sketch:** Instrument all pump coordination / iteration dispatch / state synchronization points with explicit telemetry events (add claude_sync, pump_wait_start/end, state_fetch, verdict_gate timing). Route "glue" time into named buckets (dispatch overhead, state I/O, pump coordination) instead of a catch-all.
- **Verify idea:** Re-run session and confirm "unattributed (glue)" shrinks to <30% of wall time, with named buckets accounting for the rest.

### RETRO-3 · AWAITING_PUMP halts indicate pump/coordinator bottleneck
- **Proposed:** P1 · Effort M · Risk MED
- **Problem:** Halt sequence lists "AWAITING_PUMP" 9 times with 1308.7m total paused time, suggesting the pump coordinator is frequently blocking iterations. Combined with large glue times, this indicates the pump/goal-loop synchronization is not scaling with session length.
- **Evidence:** Agent economics — "total AWAITING_PUMP paused gaps: 1308.7m" and halt sequence: "AWAITING_PUMP" appears 9 times in the halts list across iters 1–27.
- **Sketch:** Profile pump/coordinator latency during a full session: measure how long each iteration waits for pump acknowledgment, dispatch, or subagent completion. If pump subagents (dev, reviewer, qa) regularly exceed their expected windows, add queuing or parallel dispatch logic.
- **Verify idea:** Run a session with pump latency instrumentation; confirm AWAITING_PUMP paused gaps shrink to <100m total or are eliminated via parallel dispatch.

### RETRO-4 · Repeated REGRESSION verdicts (iters 18, 24, 26) ending STALLED
- **Proposed:** P2 · Effort M · Risk MED
- **Problem:** The verdict sequence shows three REGRESSION verdicts (iters 18, 24, 26) in the second half, each followed by recovery attempts that eventually lead to STALLED (iter 28). This pattern suggests iteration recovery logic or regression detection may be weak, allowing regressions to recur instead of being fixed before retry.
- **Evidence:** Verdict sequence — "iter 18: REGRESSION, iter 24: REGRESSION, iter 26: REGRESSION, … iter 28: STALLED" with no successful recovery between iter-26 REGRESSION and iter-28 STALLED.
- **Sketch:** Add explicit regression-state tracking: after a REGRESSION verdict, do not allow next CONTINUE → goal attempt until a deterministic root-cause review confirms the regressed artifact is reverted or fixed. Emit a named halt (REGRESSION_HALT) instead of trying the next iter blindly; require human unlock or automated fix detection.
- **Verify idea:** Run a session that hits a REGRESSION; confirm it halts with REGRESSION_HALT (not CONTINUE), collects explicit failure evidence, and requires human review before retry.

### RETRO-5 · Goal-evaluator late-iter scoring paradox (iter-28 honest-absence as PASS)
- **Proposed:** P2 · Effort S · Risk LOW
- **Problem:** Lessons tail (iter-28) documents that goal-evaluator scored journeys as PASS based on "honest status" (correct absence badge) without requiring the journey's success criterion (presence of a certified artifact). This is a judgment rubric / acceptance-gate issue: an honest "no artifact" is not the same as a proven artifact.
- **Evidence:** Lessons tail — "The browser-qa lane graded the five all-FAIL evidence journeys (J-02/J-06/J-07/J-08/J-09) as 'PASS' by scoring only the honest-status half (… honest 'no edge here' state … never `passing`) … When a journey's success criterion is the PRESENCE of a proven artifact, an honest-absence screenshot is `partial`, never `passing`."
- **Sketch:** Refine goal-evaluator's rubric (`.claude/judgment-rubrics.md`) to explicitly distinguish "honest but absent" from "proven present" for artifact-presence journeys. Add a pre-evaluation checklist: if a journey requires a proven/certified X, the PASS verdict must cite the X's attestation, not just the badge correctness.
- **Verify idea:** Run iter-28-style evaluation on J-02/J-06/J-07/J-08/J-09; confirm PASS verdicts cite the proof artifact (e.g., edge ledger link) or emit PARTIAL with a clear "artifact not found" reason.
