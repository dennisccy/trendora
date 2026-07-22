# Phase goal-ops-hardening-iter-9 — UX Regression Review

**Date:** 2026-07-22

**Verdict:** UX-REGRESSION-WARN

---

## New Capability Discoverability

None to assess. `plan.md`'s "UI Evolution" section and `reports/phase-goal-ops-hardening-iter-9-user-visible-changes.md`
both state, and the dev handoff's "Files Changed" list confirms (zero files under `apps/frontend/`), that
this iteration shipped no new user-facing capability, no new information displayed, no new user action, and
no navigation change. `Frontend Present: yes` was set for one documented reason only — to force the
goal-mode harness's browser-qa lane to actually run (correcting an iter-8 harness bug where `Frontend
Present: no` silently skipped browser-qa) — not because new UI shipped. There is nothing to flag as hidden
or undiscoverable this iteration.

## Regression Risk

| Shared component touched | Prior feature it serves | This iteration's change | Risk |
|---|---|---|---|
| `scripts/start-backend.sh`, `scripts/dev.sh` (backend subshell) | **Every journey's boot path** — the process every page/API request depends on, including J-04's boot-to-health timing SLA (steps 1–2, ≤5s to first `GET /api/health` 200) | Adds `taskset -c "$HOST_GUARD_CPU_LIST"` (pins backend to 8 cores) + BLAS/OMP/numexpr thread caps (`HOST_GUARD_BLAS_THREADS`), additive to the pre-existing `ulimit -v`/`MALLOC_ARENA_MAX` | **Medium.** This is exactly the class of change the spec's own "Depth is full" rationale calls out ("touches the launch scripts every journey boots through... correctness only provable by re-running the FULL live verification battery"). But the raw QA report (`ui-test-results.llm.md`, UT-J-04 steps 1–2) explicitly states the boot-time budget was **not re-measured** under the new caps — it cites the iter-5 measurement (1.387–1.459s) taken *before* this iteration's CPU/thread restriction existed, reasoning "remains valid by construction since zero boot-path *files* changed." That reasoning covers the code path but not the resource envelope: fewer cores/threads available to warmup could plausibly slow first-health timing, and this was asserted, not measured, under the new caps this iteration itself introduces. |
| `apps/backend/app/engine/data_manager.py` (`_release_process_memory`) | J-05's heavy-ingest `MemoryError`-hardening fix (iter-8) — the per-item warm-loop abort path this whole session hardens | Memoizes the libc `CDLL` handle (module-level cache) instead of re-resolving it on every call; `gc.collect()`/`malloc_trim` timing/effect unchanged per two new unit tests | **Low.** Verified byte-identical behavior via targeted unit tests (call-count + cached-failure cases). Not exercised under a real heavy-ingest run this session (see below) — the unit-test evidence is sound but narrower than the live proof the DoD originally called for. |
| `apps/backend/tests/test_start_backend_script.py` | The heavy-ingest regression guard itself (J-05) | Tightens `status == "ok"` (rejects `"partial"`) + `aggregates_refreshed` completeness; adds TC-7/TC-8/TC-9 launcher-cap tests | **Low** — test-only, strictly tightens an existing gate; dev handoff confirms every pre-existing assertion (VmPeak/VmSize/health-poll) was re-read intact at both edit boundaries. No user-facing risk. |
| `/data`'s `JobProgressPanel` / `UnfinishedImportsPanel` (no code touched this iteration) | J-04's interrupted-job step (goal.md step 6) and the original J-59/J-60 job-history design (prior product-goal session) | **No code change** — but this iteration's `Frontend Present: yes` line forced the *first-ever* live browser verification of this journey, and it found a real, pre-existing defect (see Flags below) | **Not a regression from this iteration's diff** — the raw QA report traces the failure to `_finalize_run_record()`/`sweep_orphaned_runs()`, neither touched this iteration, and confirms zero frontend files changed. Included here because it is a "required-still-passing" journey whose actual current state (FAIL on 1 of 6 steps) is being masked by downstream artifacts — see Flags. |

**Live heavy-ingest re-measurement was deferred this session** (dev handoff Known Issue #1, host-thermal
safety) — no VmPeak/VmSize CSV exists under `runs/goal-ops-hardening-iter-9/` and no dated section was
added to `reports/perf-budgets.md` (confirmed: neither artifact exists). This means the one measurement
that would most directly validate "the new caps keep health responsive through a real back-to-back heavy
job" has not been taken under the conditions this iteration actually created. Independently, the non-heavy
test suite and manual launcher smoke tests (real `host-guard.env`, short of full heavy load) do back the
caps' mechanical correctness — this is a coverage gap, not evidence the caps are broken.

## UI vs Backend Parity

- No new backend capability this iteration (confirmed by `implementation-summary.md`'s "Features
  Implemented" section — launch-script hardening, test tightening, and an internal memoization, all
  operationally invisible) that isn't already reflected honestly in `user-visible-changes.md`. No parity
  gap on the "new feature not surfaced" axis.
- A different parity problem exists between **QA reporting artifacts**, not between backend and UI:
  - `reports/phase-goal-ops-hardening-iter-9-ui-test-results.llm.md` (the RAW browser-qa file) states
    **`Browser QA Verdict: FAIL`**, "17/19 rows passed, 2 failed" (UT-10 and UT-J-04 step 6).
  - `reports/phase-goal-ops-hardening-iter-9-ui-test-results.md` (the **merged** summary) states
    **`Browser QA Verdict: PASS`**, "16/19 journeys passed" — despite reproducing the identical UT-10/UT-J-04
    FAIL rows verbatim in its own results table.
  - `runs/goal-ops-hardening-iter-9/status.json` carries `"qa_verdict": "PASS"`.
  - The phase spec's own TC-14 and DEFINITION OF DONE anticipate exactly this trap ("the RAW
    `ui-test-results.llm.md` is read directly — never the merged summary or `status.json` alone"). Anyone
    who follows the merged file or `status.json` instead of the raw file — as this project's own recurring
    iter-3/iter-4 lesson warns against — would conclude J-04 fully passed when it did not.

## Flags

### Hidden Capabilities
- None. No new capability shipped this iteration.

### Undiscoverable Capabilities
- None. No new capability shipped this iteration.

### Potential Regressions
- **Boot-time SLA unverified under this iteration's own CPU/thread caps.** `scripts/start-backend.sh` /
  `scripts/dev.sh` — the shared boot path for every journey — now applies `taskset` CPU-affinity (8 cores)
  and BLAS/OMP/numexpr thread caps. J-04 steps 1–2 (boot-to-health ≤5s) were scored PASS on a citation of
  iter-5's measurement (1.387–1.459s), taken **before** these caps existed, with the raw QA report itself
  stating "I did not re-run this measurement myself." A CPU/thread-count reduction to the exact process
  whose cold-boot warmup is timed is a plausible (if likely small) source of regression that remains
  unmeasured, not just unlikely.
- **J-04 (required-still-passing) does not, in fact, fully pass, and two downstream artifacts say it does.**
  The raw QA file scores UT-J-04 **FAIL** (step 6: an interrupted backfill's persisted progress resets to
  `0 snapshots · 0 trading days` instead of freezing at the crash point — contradicting the literal text of
  both `goal.md`'s J-04 step 6 and this iteration's own UT-10 expected result). The merged summary
  (`ui-test-results.md`) and `status.json` both report an overall PASS verdict. The raw report's own
  root-cause trace is credible that this bug pre-dates this iteration (zero touches to
  `_finalize_run_record()`/`sweep_orphaned_runs()` in the diff) — so it is not a regression *caused* by
  iter-9's changes. But it is a real, currently-failing state of a "required-still-passing" journey, and the
  merge/status pipeline is under-reporting it as passing — the same class of harness-trust bug this
  session's own iter-8 lesson ("check `browser_checks_run` and the evidence directory before believing any
  completion claim") was written to prevent, now recurring one level down (merged-summary vs. raw-file
  trust, rather than skip-vs-run trust).
- **Live heavy-ingest proof under the new launcher caps is still outstanding.** No VmPeak/VmSize CSV exists
  under `runs/goal-ops-hardening-iter-9/`, and `reports/perf-budgets.md` has no iter-9 dated section —
  confirmed by direct inspection. The dev handoff attributes this to a responsible host-thermal-safety
  deferral (not a shortcut), and non-heavy automated coverage independently backs the caps' mechanical
  wiring — but the single most direct end-to-end proof point for "AG-10 fix + J-05 heavy-ingest hold
  together" has not been taken under the actual current conditions.

### Visual Consistency
- Not applicable — zero frontend files changed this iteration (confirmed via the dev handoff's "Files
  Changed" list and `ui-surface-map.md`'s "Frontend surfaces changed: 0"). No new component patterns, no
  arbitrary values introduced; all 8 re-verification rows in the UI surface map are pre-existing surfaces
  exercised as-is.

## Recommendation

1. **Do not treat this iteration's overall QA outcome as a clean PASS on the strength of the merged summary
   or `status.json` alone** — score J-04 (and thus the session's `unknown`→`passing` transition claim for
   it) from the raw `ui-test-results.llm.md`, which shows step 6 FAIL. This is a scoring input for the
   evaluator/auditor, not something for this review to adjudicate, but it should not be silently absorbed
   as "16/19 PASS" by any downstream consumer of the merged file.
2. **Recommend a follow-up item (backlog, not this iteration's scope):** fix the merge script that produces
   `phase-*-ui-test-results.md` so it cannot report an overall PASS when its own results table contains FAIL
   rows for a required-still-passing regression journey — this is the second instance (after the iter-8
   `Frontend Present: no` skip bug) of a harness/reporting layer silently under-representing true state.
3. **Recommend re-measuring J-04 steps 1–2's boot-time budget** under the AG-10 caps once feasible (same
   host-idle precondition as the deferred heavy-ingest run) rather than continuing to cite a pre-caps
   measurement as "valid by construction" — the caps changed the resource envelope the timing was measured
   against, even though no boot-path *file* changed.
4. No action required on discoverability or visual consistency — this iteration introduced neither new
   surfaces nor code-level UI changes.
