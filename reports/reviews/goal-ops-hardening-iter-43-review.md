**Verdict:** PASS_WITH_NOTES

```yaml
phase: goal-ops-hardening-iter-43
date: 2026-07-31
reviewer: reviewer
summary: |
  Reverts iter-42's _BarCache.prefill symbol filter (byte-identity oracle proves the revert; the B1
  KeyError publish-race fix is untouched), adds an honest thread-launch-failure path for
  start_data_job/start_resume_job (503, not a false 200-running), and extends the HOST-GUARD block to
  start-frontend.sh (marker list updated). All in-scope code is correct, matches spec precisely, no
  scope creep. Independently re-ran test_bar_cache.py (22/22) and the two new thread-launch tests
  (2/2) — both green. Live J-07 steps 1-3 re-verification did not reach a terminal state this session;
  memory (67.6% margin) and availability (272/272 200s) pass cleanly, but a new latency WARN against
  the rescoped 2s budget is honestly disclosed, unresolved, and correctly left out of this iteration's
  code scope (its trigger condition for a code fix was not met).
spec_alignment:
  definition_of_done: partial
  scope_creep: none
issues:
  - severity: MINOR
    file: apps/backend/app/engine/data_manager.py
    line: 4654
    category: backend
    summary: _fail_unlaunched_job never sets prog.message, and the unchanged _final_summary/_run_detail
      never surface prog.errors, so the persisted DataProviderRun.message stays a generic "0 snapshots"
      summary rather than text naming the thread-launch failure per TC-3/TC-4's literal wording; only
      the transient 503 response body and the live pre-eviction errors[] array carry the real reason.
    fix: set prog.message in _fail_unlaunched_job (or fold the first prog.errors entry into
      _run_detail's summary when status==failed), and extend the two new tests to assert on the
      persisted row.message content, not just row.status.
  - severity: MINOR
    file: reports/perf-budgets.md
    line: 5742
    category: spec
    summary: TC-6/TC-7/TC-8 live re-verification did not reach a terminal state this session (honestly
      disclosed, not hidden). Memory and availability axes pass cleanly, but 63.6% of 272 health polls
      breached the rescoped 2s BCW budget (up to 6.6s, worsening over the window), with two unconfirmed
      candidate causes (T2 exposure widened by the revert; a self-inflicted concurrent-dispatch
      confound).
    fix: next iteration isolates the latency regression cleanly (single-trigger repeat, no concurrent
      manual probe) or addresses T2 directly, per the dev handoff's own recommendation — not a code
      defect in this diff, and its conditional TC-10 trigger (over-cap or wedging) was correctly not met.
standards:
  state_transitions_server_side: pass
  test_quality: pass
  no_dead_code: pass
  no_hardcoded_localhost: n/a
  architecture_principles: pass
```
