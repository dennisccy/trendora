# Session retro — ops-hardening

> **Ideas only — nothing here is scheduled work.** These are suggestions for
> improving the build system itself, not your product. A human reviews them and
> decides (promotion into docs/improvement-roadmap.md §16, the staging list).
> Codes: P0/P1/P2 = how urgent · Effort S/M/L = how much work · Risk LOW/MED/HIGH
> = chance a change breaks something else.

**Session:** ops-hardening · **Terminal status:** GOAL_ACHIEVED · **Iterations:** 80

## Candidate items

### RETRO-1 · Post-dev-fanout budget overruns are frequent and ineffective at trimming

- **Proposed:** P1 · Effort M · Risk MED
- **Problem:** The pipeline's post-dev-fanout step has a 3600-second (1 hour) budget ceiling, but consistently overshoots by large margins — up to 28,696 seconds (7.9 hours) at iter 50. The system attempts to trim agents when the budget is tight ("mode=trim"), but the overruns still appear in the logs across most of the session. This means either the budget is unrealistic, or the trimming logic is too weak to actually reduce wall time.
- **Evidence:** Agent economics (wall-time report) — Lines like "OVER BUDGET at post-dev-fanout: 6921s > 3600s (mode=trim)" (iter 36), "OVER BUDGET at post-dev-fanout: 28696s > 3600s (mode=trim)" (iter 50), and dozens more (iters 33–79). The session averaged 215.3 minutes per iteration wall time, with post-dev-fanout consistently in the 6000–14000 second range.
- **Sketch:** (1) Analyze wall-time distributions across past goal sessions to determine the true 95th percentile for post-dev-fanout. If it consistently exceeds 3600s, adjust the budget or document why it is intentionally tight. (2) Strengthen the trimming policy: pre-filter low-priority agents (ui-test-designer, ux-regression-reviewer) earlier, or add a secondary trim round if the first fails to meet budget. (3) Add telemetry to log which agents were trimmed and the time saved, so the trimming effectiveness is measurable.
- **Verify idea:** Run a new session and confirm post-dev-fanout wall times stay under budget (or overruns drop to <5% of iterations); measure trim agent counts and savings.

---

### RETRO-2 · Carry-forward iteration state (journeys' "still owed" metadata) becomes stale and wrong

- **Proposed:** P1 · Effort M · Risk LOW
- **Problem:** When the goal-evaluator or goal-decomposer carry a "Nth round owed" note from one iteration to the next, the carried state can become incorrect and outdated — reported as fixed by one correction in iter 78, but then found still undercorrected when a fresh artifact inspection was done. In this session, the demo walkthrough JSON showed four journeys with incorrect `new: false` status that were carried through 20+ rounds of logs claiming only one was still owed.
- **Evidence:** Lessons tail — "Opening `reports/goal-session-ops-hardening-demo.json` shows FOUR journeys' walkthrough steps are `new: false` (J-01 steps 3-4, J-03 5-6, J-04 2, J-05 7), not just J-05's as twenty rounds of logs claimed — iter-78 corrected this carry once (for J-07) and it was still under-stated."
- **Sketch:** (1) In goal-evaluator.md and goal-decomposer.md, add a startup step that opens and re-inspects the final iteration artifacts (e.g., `reports/goal-session-<sid>-demo.json`) and recalculates the "Nth round owed" list from the artifact directly, instead of copying it from the previous iteration's lessons. (2) Compute a checksum or hash of the final "Nth round owed" state and include it in the telemetry so mismatches can be detected by a deterministic audit. (3) Document the rule: carry-forward state must be re-verified against the artifact every iteration, especially walkthrough and demo metadata.
- **Verify idea:** Add a deterministic audit step that compares the lessons "Nth round owed" text against the demo artifact and fails loudly if the new: flag counts don't match; run a session and confirm the audit passes without discrepancies.

---

### RETRO-3 · Timing outlier signals conflate compute time and queue-wait time, leading to misdiagnosis

- **Proposed:** P1 · Effort M · Risk LOW
- **Problem:** When the goal-evaluator flags a timing outlier (e.g., a slow `/api/backtest` response), it reports the end-to-end latency without distinguishing compute time from queue-wait time. An outlier reported as a budget breach turned out to be queueing delay behind concurrent work, not a slow compute operation. This leads to incorrect scoring of performance issues and misdirects the developer to the wrong fix.
- **Evidence:** Lessons tail (iter 79) — "The 9.3 s `/api/backtest` outlier was reported as a budget breach; the database settled the cause in one query — that as-of's five horizons committed inside ~1.5 s (`forward_aggregate_cache` 23:56:41.68 → 23:56:43.14 UTC), so the wait was queueing behind another in-flight warm, not slow compute … the two point at completely different fixes (bounding concurrency vs bounding the computation)."
- **Sketch:** (1) Add timing instrumentation to capture cache/queue entry and exit timestamps within critical paths (e.g., `forward_aggregate_cache` calls in `app/engine/forward_testing.py`). (2) Modify goal-evaluator to consume these timestamps and split end-to-end latency into (a) compute time and (b) queue-wait time. (3) Score performance against compute time alone; log both metrics separately so the developer can identify root cause. (4) Add a skill that logs "latency = {compute_time}s compute + {wait_time}s queue" when an outlier is detected.
- **Verify idea:** Add a new telemetry event type for split compute/queue time; run a session and confirm timing-outlier lessons log both metrics and that root-cause identification (compute vs concurrency) is accurate.
