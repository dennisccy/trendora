# Session retro — market-compass

> **Ideas only — nothing here is scheduled work.** These are suggestions for
> improving the build system itself, not your product. A human reviews them and
> decides (promotion into docs/improvement-roadmap.md §16, the staging list).
> Codes: P0/P1/P2 = how urgent · Effort S/M/L = how much work · Risk LOW/MED/HIGH
> = chance a change breaks something else.

**Session:** market-compass · **Terminal status:** STALLED · **Iterations:** 24

## Candidate items

### RETRO-1 · SQLite WAL-mode database immutability check broken
- **Proposed:** P0 · Effort S · Risk LOW
- **Problem:** The goal evaluator uses sha256 of the `.db` file to check if a database was left unchanged. In SQLite WAL mode, new rows can live in the `.db-wal` file and never get checkpointed to the main file, so the sha256 matches even though the database content changed. When the evaluator can't detect whether changes stuck, it reports STALLED instead of CONTINUE.
- **Evidence:** Lessons tail — "sha256 of a WAL-mode SQLite `.db` file is NOT a proof that the database is unmutated... SQLite kept the new rows in the sibling `trendora.db-wal`... Any future immutability claim over a SQLite file must bracket `.db` + `-wal` + `-shm`, or read logical row state"
- **Sketch:** Add a utility function that checks SQLite immutability by comparing file mtimes and checksums of `.db`, `.db-wal`, and `.db-shm` together, or by reading logical row counts from the database itself. Update goal-evaluator to call this instead of sha256-only checks. Document the pattern in judgment-rubrics or project-template.
- **Verify idea:** Run iter-23 replay or new session and confirm the evaluator correctly detects unchanged databases in WAL mode.

### RETRO-2 · Persistent pipeline quota overruns in full-depth gates
- **Proposed:** P1 · Effort L · Risk MED
- **Problem:** Nearly every full-depth pipeline iteration exceeds the 3600-second budget at some stage. Iterations 19, 21, and 22 massively overrun (>12k seconds each). The system trims work but violations persist, wasting wall time and suggesting either the quota is unrealistic or the pipeline stages need restructuring.
- **Evidence:** Agent economics wall-time report — "OVER BUDGET at post-dev-fanout: 16335s > 3600s (mode=trim)" (iter 19), "OVER BUDGET at post-dev-fanout: 12749s > 3600s (mode=trim)" (iter 21), "OVER BUDGET at post-dev-fanout: 17833s > 3600s (mode=trim)" (iter 22); similar overruns in 10 other iterations
- **Sketch:** Profile which agents inside post-dev-fanout consume the most time. Consider splitting fanout into parallel sub-stages with independent budgets, or deferring non-blocking agents (e.g., demo-narrator, ux-regression) to an optional stage. Alternatively, increase the budget if the work is necessary.
- **Verify idea:** Run a full session and confirm max per-stage wall time is under budget, or document why the new budget is correct.

### RETRO-3 · Reviewer agent bottleneck and intermittent failures
- **Proposed:** P1 · Effort M · Risk MED
- **Problem:** The reviewer agent consumed 1558.6 minutes — the highest wall time of any agent, 20% of the session. It also had attempt-1 review FAILs in iters 7 and 8, requiring retries. Multiple review failures and long wall times suggest either the review task is underspecified or the agent is encountering systematic issues with its inputs.
- **Evidence:** Agent economics — reviewer total wall 1558.6m (largest agent); Friction counters — "Attempt-1 review FAILs: 2"; wall-time breakdown iter 7: "reviewer 373.9m calls=2 failures=1", iter 8: "reviewer 300.0m calls=1 failures=1"
- **Sketch:** Add telemetry instrumentation to track reviewer failure reasons (malformed verdict, input missing, timeout). Audit the review rubric for clarity and falsifiability. Consider parallelizing review sub-tasks or moving lighter review gates upstream to developer/qa stages.
- **Verify idea:** Run a new session and confirm reviewer wall time is <800m and attempt-1 FAILs are zero.

### RETRO-4 · AWAITING_PUMP halts consume 503 minutes of paused time
- **Proposed:** P1 · Effort M · Risk LOW
- **Problem:** The session halted at AWAITING_PUMP status multiple times, accumulating 503 minutes of paused wall time. These are not user-initiated pauses (quota_pause_count = 0), suggesting the pump (subagent running tests and services) is unresponsive or the engine is not correctly detecting when it is ready.
- **Evidence:** Agent economics — "total AWAITING_PUMP paused gaps: 503.0m"; halt sequence — "halts: AWAITING_PUMP, AWAITING_PUMP, AWAITING_PUMP, ... [4 entries total]"
- **Sketch:** Add pump heartbeat monitoring to detect when the pump process is stuck or dead. Implement a timeout and failover (restart pump or escalate to user). Log the reason for each pump wait in telemetry (timeout, slow tests, service startup delay).
- **Verify idea:** Run a new session and confirm AWAITING_PUMP total paused time is <100m and each halt is logged with a clear reason.

### RETRO-5 · Verdict sequence: seven-iteration STALLED loop (iters 12–18) masks underlying detection failure
- **Proposed:** P1 · Effort M · Risk MED
- **Problem:** The evaluator entered STALLED at iter 12 and remained stuck for seven consecutive iterations (12–18). Combined with earlier STALLED at iters 10, 22–23, this is a recurring pattern. Once the database immutability check is fixed (RETRO-1), the engine should detect stuck states earlier and escalate instead of looping silently.
- **Evidence:** Verdict sequence — "iter 10: STALLED\niter 11: REGRESSION\niter 12: STALLED\niter 13: STALLED\niter 14: STALLED\niter 15: STALLED\niter 16: STALLED\niter 17: STALLED\niter 18: STALLED"
- **Sketch:** Add a rule: if iter N returns STALLED and iter N-1 was also STALLED, after 4 consecutive matches escalate to user with details (evaluator reason, last verdicts, proposed recovery) instead of silently continuing. Alternatively, trigger a lightweight replay to verify actual progress was made.
- **Verify idea:** Run a new session and confirm that if evaluator detection fails, the engine escalates within 2–4 iters instead of looping 7+ times.

