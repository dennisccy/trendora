# Phase goal-ops-hardening-iter-7 — Closure Verdict

**Phase:** goal-ops-hardening-iter-7
**Date:** 2026-07-21
**Written by:** phase-closure-auditor

---

**Verdict:** CLOSURE-FAIL

---

## Standard Pipeline Gate Checks

| Artifact | Status | Verdict |
|----------|--------|---------|
| Review report (`reports/reviews/goal-ops-hardening-iter-7-review.md`) | exists | PASS (as written) |
| QA report (`reports/qa/goal-ops-hardening-iter-7-qa.md`) | exists | PASS (as written) — **unreliable, see Blocking Issue 1** |
| Audit report (`docs/handoffs/goal-ops-hardening-iter-7-audit.md`) | exists | PASS (as written) — **unreliable, see Blocking Issue 1** |

The three verdict lines are literally present and read PASS. This is not, however, sufficient for closure:
cross-referencing these reports against the pipeline's own raw browser-QA evidence and the UX-regression
report shows both the QA and Audit PASS verdicts are contradicted by directly-observed, reproducible test
evidence that they either mis-stated or never engaged with. See Blocking Issue 1 below — this is what
drives the CLOSURE-FAIL, not a missing-artifact problem.

---

## UI Visibility Artifact Checks

| Artifact | Exists | Non-Empty | Non-Vague | Status |
|----------|--------|-----------|-----------|--------|
| implementation-summary.md | yes | yes | yes | OK |
| user-visible-changes.md | yes | yes | yes | OK |
| ui-surface-map.md | yes | yes | yes | OK |
| ui-test-plan.md | yes | yes | yes | OK |
| ui-test-results.md | yes | yes | yes (content) / **inconsistent (verdict)** | OK on quality bar, but see Blocking Issue 1 |
| what-to-click.md | yes | yes | yes (7 numbered steps) | OK |

All six artifacts independently meet the existence/quality bar (real, specific content; ≥5 lines; no
placeholder text). `Frontend Present: yes` is satisfied structurally — this is not an artifact-vagueness or
backend-only-masking failure. The problem is a verdict-vs-evidence integrity failure inside
`ui-test-results.md` itself (see below).

---

## Cross-Reference Checks

- [x] user-visible-changes lists ≥1 specific capability — yes (`/evidence` fast-first-view; `/data`
      "drawdown expectations" phrase in three render locations)
- [x] ui-surface-map has specific route/component entries — yes (`/evidence`, `/data`'s `BackfillBreakdown`
      in three distinct render paths, with exact test steps per row)
- [x] ui-test-plan has specific steps with exact actions and expected results — yes (UT-01..UT-09, each with
      numbered steps, exact `data-testid`s, exact expected strings)
- [x] ui-test-results shows execution evidence — yes, 13 screenshots in
      `reports/qa/goal-ops-hardening-iter-7-evidence/`, real measured values (timings, DOM reads)
- [x] what-to-click has ≥3 numbered steps with exact expected outcomes — yes, 7 steps
- [ ] **implementation-summary claims are consistent with ui-test-results evidence — FAILS.**
      `implementation-summary.md` states "No other known limitations. All automated tests pass... the fix
      was independently confirmed live against the running application" with no mention of any regression.
      The RAW browser-qa-agent output
      (`reports/phase-goal-ops-hardening-iter-7-ui-test-results.llm.md`) states **`Browser QA Verdict: FAIL`**,
      driven entirely by a confirmed regression in journey J-05. This is a direct claims-vs-evidence
      contradiction, and it propagates into the QA and Audit reports too (Blocking Issue 1).

---

## Blocking Issues

1. **A confirmed regression in Required-still-passing journey J-05 is documented by the pipeline's own
   browser-qa-agent and ux-regression-reviewer, but is masked (not surfaced) by the merged test-results
   file, the QA report, and the Audit report — all three of which claim clean PASS.**

   Evidence chain, in chronological order (file mtimes confirm QA and Audit both ran *after* this evidence
   existed, so this is not a timing/staleness issue — it was available to be caught and was not):

   - `reports/phase-goal-ops-hardening-iter-7-ui-test-results.llm.md` (06:58, browser-qa-agent, RAW):
     **`Browser QA Verdict: FAIL`**, with an explicit inline comment: *"The FAIL is driven entirely by the
     goal-mode regression journey J-05, which surfaced a critical, directly-observed backend hang (GET
     /api/health unresponsive for 7+ minutes) during a routine heavy ingest job — a hard violation of J-05's
     explicit acceptance."* Full account of the hang (UT-J-05 section, lines 105-124): `GET /api/health`
     timed out for 7+ continuous minutes during a heavy ingest; backend process was alive but idle (all 22
     threads in `futex_do_wait`); `logs/backend.log` shows a `MemoryError` in a worker thread at the exact
     moment health stopped responding; manual backend restart was required to recover. The browser-qa-agent
     itself attributes partial causation to this iteration's own diff: the new `drawdown_expectations` warm
     step "adds one more memory-hungry synchronous computation to the ingest finalize hot path, making the
     ingest path more likely to be the trigger."
   - `reports/phase-goal-ops-hardening-iter-7-ui-test-results.md` (06:59, merged): top-line states
     **`Browser QA Verdict: PASS`** and **"11/13 journeys passed (0 skipped)"**, while its own results table
     three lines below marks `UT-J-05` as **FAIL**. This is an internal self-contradiction in the same file —
     exactly the failure mode the phase spec's own carried-forward lesson (quoted verbatim in
     `docs/phases/goal-ops-hardening-iter-7.md` BACKGROUND) warns every downstream reader to catch: *"(iter-6)
     always cross-check the merged QA verdict against the RAW `ui-test-results.llm.md` browser-qa verdict."*
   - `reports/qa/goal-ops-hardening-iter-7-qa.md` (07:15, after both files above existed): **`Verdict: PASS`**,
     296 lines, zero mention of J-05, the health hang, or the `MemoryError` anywhere.
   - `reports/phase-goal-ops-hardening-iter-7-ux-regression.md` (07:20, ux-regression-reviewer): correctly
     caught all of the above. **Verdict: UX-REGRESSION-FAIL.** Explicitly recommends: *"Do not let this
     iteration's PASS verdict stand as-is. Route this back through the loop (developer/auditor) to
     investigate and fix the ingest-path memory/hang regression before J-06 (or the session) is declared
     closed."*
   - `docs/handoffs/goal-ops-hardening-iter-7-audit.md` (07:27, AFTER the ux-regression report existed):
     **`Verdict: PASS`**, "No CRITICAL or IMPORTANT issue found." Zero mention of J-05, the health hang, the
     `MemoryError`, or the ux-regression-reviewer's UX-REGRESSION-FAIL finding, anywhere in the report's 5
     sections. The audit's own finding T3 discusses QA verdict timing (TC-7 not finished when QA wrote its
     verdict) but does not touch the J-05 regression at all — a materially more severe gap that was already
     on record by the time the audit ran.

   This is not a cosmetic discrepancy. The phase spec's own DEFINITION OF DONE item 2 requires: *"Required-
   still-passing journeys J-01, J-03, J-04, J-05 remain green."* `journey-history.json` confirms J-05's
   pre-iteration status was `"passing"` (`last_passing_iter: goal-ops-hardening-iter-6`). Per the raw
   browser-qa evidence, J-05 did **not** remain green this iteration — it hard-failed on its own explicit
   acceptance clause ("assert `/api/health` stays responsive throughout a heavy ingest"), with a concrete,
   reproducible, screenshot-documented 7+-minute outage requiring manual intervention to recover. This also
   sits squarely inside AG-8's territory (service memory exhaustion under a widened/heavier data path) — one
   of the phase spec's own `critical`-tagged anti-goals. For a session whose explicit charter is
   "ops-hardening," a backend availability outage during ingest is close to the most severe possible finding,
   not a minor gap to wave through.

   **Remediation:**
   - Do not finalize this phase. Re-open the pipeline at the developer step (or a targeted fix-and-reverify
     pass) to investigate and address the memory/hang interaction between the new `drawdown_expectations`
     warm step and the pre-existing `memory_cap_mb=6144` ceiling under back-to-back heavy ingest jobs — per
     the ux-regression report's own recommendation. Candidate directions (for the developer/auditor to
     evaluate, not prescribed here): bound the new warm step's memory footprint, avoid holding per-claim
     computation results/sessions open longer than necessary, or add backpressure/serialization so two heavy
     ingests cannot both hold peak memory simultaneously — but the root-cause diagnosis is the implementing
     agent's job, not this gate's.
   - Independently of the product fix, fix the **verdict-reporting pipeline itself**: the `merge_ui_test_results.py`
     step must not print a top-line PASS when its own table contains a FAIL row for a named journey, and the
     `qa` and `auditor` agents must explicitly read and reconcile against
     `reports/phase-goal-ops-hardening-iter-7-ui-test-results.llm.md`'s raw verdict (and, once produced, the
     `ux-regression-reviewer`'s verdict) before emitting their own PASS. This is the second time this exact
     class of masking has been named as a carried-forward lesson in this session (iter-6 lesson, restated in
     this very phase spec) — the lesson is not yet actually being applied by the QA/audit steps in practice.
   - After a genuine fix, QA and Audit must be re-run so their verdicts are written with the corrected
     evidence in hand, and this closure gate must be re-run against the updated reports.

---

## Non-Blocking Notes

- Audit finding T2 (test hermeticity: `test_finalize_hook_persists_coverage_snapshot_and_warms_aggregates`
  transitively depends on the real project ledger's contents) is a legitimate, correctly-scoped-out
  observation — not a closure blocker on its own.
- Audit finding T3 (QA wrote its PASS verdict while the 4-file pytest run was ~73% complete, and marked
  TC-08/TC-02/TC-06 as PENDING) is a real process gap but a minor one next to Blocking Issue 1 above; it is
  superseded in severity by the J-05 finding and does not need separate remediation once the QA re-run
  happens for the primary fix.
- The core `drawdown_expectations` warm mechanism itself — the actual feature this iteration shipped — is
  well-evidenced as correct in isolation: byte-identical output (TC-3), honest gating on empty/unresolvable
  ledgers (TC-5/TC-4), per-claim failure isolation, 7 new unit tests plus 12 pre-existing finalize-hook tests
  all green, and a credible live end-to-end proof (genuinely-new dataset version, sub-50ms first view). The
  blocking problem is specifically the *interaction* of this new synchronous work with an already-marginal
  memory ceiling under heavy/back-to-back load, not the correctness of the warm logic itself.
