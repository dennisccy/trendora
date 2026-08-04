**Verdict:** FAIL

```yaml
phase: goal-ops-hardening-iter-45
date: 2026-08-04
reviewer: reviewer
summary: |
  Re-review after the audit FAIL and fix-mode pass. The append-forward fast path itself is correctly
  scoped and byte-identical to the pre-fix oracle (TC-1/2/3 + gap-fill fallback re-verified
  independently; 16/16 targeted tests green). The audit's B3/B4/B5/T1/T2 fixes and this fix-mode
  pass's B6 (fatal-job logging, with two self-caught regressions — a key leak and a re-opened
  MemoryError escape — genuinely corrected and negative-controlled) and F1 (PNG-provenance evidence
  stamping) are all well-built, tightly tested, and in-scope; no scope creep. However the phase's own
  Definition of Done is not met: browser-qa-agent returned FAIL 0/2 for the target journeys, with the
  backend going fully unreachable for ~34-42 minutes (a worse outcome than the stall this iteration
  set out to fix) — TC-4/5/6 failed, TC-7 never executed, TC-11 stays unmet. The dev handoff is honest
  about this; the root cause (unbounded evidence-path accumulators) is explicitly deferred out of this
  iteration's scope, but "Target journeys J-05, J-07 pass via browser-qa-agent" is unambiguously unmet.
spec_alignment:
  definition_of_done: partial
  scope_creep: none
issues:
  - severity: CRITICAL
    file: docs/phases/goal-ops-hardening-iter-45.md
    line: 218
    category: spec
    summary: "DoD item \"Target journeys J-05, J-07 pass via browser-qa-agent\" is unmet — browser-qa returned FAIL 0/2 (reports/phase-goal-ops-hardening-iter-45-ui-test-results.llm.md), with a ~34-42 min full backend outage; TC-4/TC-5/TC-6 failed, TC-7 never executed"
    fix: "cannot be closed inside this diff (root cause — unbounded research.py:777/forward_testing.py:2343 accumulators driving AnyIO thread-creation failure — is explicitly out of scope per rule 5); escalate to a dedicated follow-up iteration before re-attempting J-05/J-07 acceptance"
  - severity: MINOR
    file: apps/backend/app/engine/data_manager.py
    line: 3678
    category: backend
    summary: "_log_isolation_failure's fallback branch is not actually traceback-free/minimal-allocation for the exc_info=False B6 caller: the retry re-passes the SAME args (including the potentially large scrubbed traceback string tb) with only text appended, so a failure caused by formatting tb's size would likely recur on the fallback too (silently swallowed by the outer except, so \"never raise\" still holds, but the diagnostic guarantee can be lost)"
    fix: "for the exc_info=False caller, have the fallback drop the tb arg (e.g. log only job_id/kind/reason) so the retry is genuinely smaller than the primary attempt"
  - severity: MINOR
    file: reports/qa/goal-ops-hardening-iter-45-evidence/
    line: 1
    category: tests
    summary: "TC-11 (no two journeys share one screenshot) remains unmet — F1's PNG-provenance fix is correct and tested, but the already-captured J-03/J-04 duplicate predates the mechanism and is honestly left unfixed"
    fix: "re-run the browser-qa evidence capture once B1 is resolved so the new provenance stamping actually produces the required unique files"
standards:
  state_transitions_server_side: n/a
  test_quality: pass
  no_dead_code: pass
  no_hardcoded_localhost: n/a
  architecture_principles: pass
fix_tasks:
  - file: apps/backend/app/engine/research.py
    line: 777
    action: "bound the ret_by_run_symbol accumulator in _combination_observations (and forward_testing.py:2343's stored_by_key) — independently confirmed by browser-qa as the proximate cause of the live wedge; required before J-05/J-07 can be re-attempted"
  - file: runs/goal-session-ops-hardening/journey-scripts/J-07.json
    line: 4
    action: "TC-4's live DB has zero append-forward-testable gaps left (everything after 2019-02-26 is already snapshotted) — per the dev handoff's own recommendation, re-scope TC-4's acceptance mechanism (synthetic/small fixture drill) since no code change within AG-9 can make it pass as currently worded"
```

## Detailed Findings

**docs/phases/goal-ops-hardening-iter-45.md (DoD, CRITICAL).** The phase spec requires J-05 and J-07 to
pass via browser-qa-agent. They did not: `reports/phase-goal-ops-hardening-iter-45-ui-test-results.llm.md`
records a 0/2 FAIL with the backend fully unreachable (curl `000`) for 60+ consecutive `/api/health` polls
spanning ~34 minutes, and the audit independently traces the mechanism to AnyIO worker-thread creation
failing under memory exhaustion driven by two accumulators this iteration explicitly defers
(`research.py:777`, `forward_testing.py:2343`). The append-forward fast path this diff adds was never
exercised live either (every backfill target in the current DB is a historical gap-fill, which the fast
path deliberately does not accelerate) — so the mechanism this iteration exists to prove has zero live
evidence at the ~2,860-date scale, only unit-fixture evidence at 3-4 dates. This is a real, currently-open
gap, not something this review can wave through even though the code shipped is otherwise sound.

**apps/backend/app/engine/data_manager.py:3678 (`_log_isolation_failure`, MINOR).** For the one caller that
passes `exc_info=False` with a large pre-rendered traceback argument (`_run_job`'s B6 fatal-job handler),
the fallback retry reuses the identical `*args` (including `tb`) — so it is not actually the
"minimal-allocation, traceback-free record" the docstring promises for that caller; a size-driven failure
on the primary attempt would likely recur on the fallback too. The outer `except Exception: pass` still
prevents any escape, so this does not break the "never raise" contract, only the diagnostic guarantee in an
extreme edge case.
