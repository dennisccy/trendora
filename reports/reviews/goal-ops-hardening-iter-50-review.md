**Verdict:** PASS_WITH_NOTES

```yaml
phase: goal-ops-hardening-iter-50
date: 2026-08-06
reviewer: reviewer
summary: |
  Bounds compute_factor_lab_all's obs-build/sort (columnar _FactorCoreRecords/_FactorObsPool at the real
  MemoryError site, plus a __slots__ _FactorLabAllObs at the originally-named site), adds a MemoryError +
  broad-exception isolate-and-continue around it, adds a shared warm-in-progress interlock between the boot
  re-warm and the whole ingest finalize-tail heavy-warm window, and skips phase_context_by_date when no
  ledger claim needs recompute. Went through two audit-fix rounds (B2/B3/B4 fixes, T3 golden rewrite) that
  are well-disclosed and verified in-repo: guard/enter-exit control flow is correctly balanced (confirmed by
  direct code read), byte-identity oracle and AG-8 data-shape tests pass, and targeted re-runs of the new/
  changed tests (test_factor_lab_all.py 33/33, targeted test_data_manager.py guard+skip tests 7/7 +
  release_process_memory test, targeted test_research_streaming.py cooldown/isolation/byte-identity tests
  10/10) all pass live in this checkout. Frozen AG-10 files (config.yaml, host-guard.env, start-backend.sh,
  dev.sh) confirmed byte-identical via git diff.
spec_alignment:
  definition_of_done: partial
  scope_creep: none
issues:
  - severity: NOTE
    file: apps/backend/app/engine/research.py
    line: 1307
    category: spec
    summary: J-07 step 2's health-poll <=2s ceiling still breaches under real TC-1 concurrency (96/1179 polls >2s, GIL contention from two CPU-bound computes) — the memory fix does not close this, honestly disclosed as failing by the dev handoff.
    fix: no action needed from this pass; QA/evaluator should score J-07 step 2 as failing per the dev's own note, and a future iteration should move this compute off the event loop or to an ingest-time artifact.
  - severity: NOTE
    file: apps/backend/app/engine/warmup.py
    line: 202
    category: spec
    summary: the widened ingest heavy-warm interlock is deliberately asymmetric (ingest finalize tail never yields to the boot re-warm), so TC-5 ("guard holds in both trigger orders") is only literally true for the narrow drawdown-specific slot, not the full window — disclosed as B5 in the handoff.
    fix: no action needed; already disclosed and a reasoned priority-producer decision, carried per the handoff.
  - severity: NOTE
    file: apps/backend/app/engine/research.py
    line: 3760
    category: code-quality
    summary: _FACTOR_LAB_ALL_DEGRADED cooldown entries for a key that is never queried again (e.g. after a dataset-version bump) are only pruned on next touch of that exact key, so stale entries could accumulate in the dict over many dataset versions.
    fix: optional follow-up — sweep/expire the whole registry opportunistically (e.g. on each _degraded_cooldown_set call) rather than per-key-on-touch only.
standards:
  state_transitions_server_side: n/a
  test_quality: pass
  no_dead_code: pass
  no_hardcoded_localhost: n/a
  architecture_principles: pass
```
