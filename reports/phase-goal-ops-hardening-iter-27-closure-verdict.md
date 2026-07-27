# goal-ops-hardening-iter-27 — Closure Verdict

**Phase:** goal-ops-hardening-iter-27
**Date:** 2026-07-27
**Written by:** phase-closure-auditor

---

**Verdict:** CLOSURE-FAIL

---

## Standard Pipeline Gate Checks

| Artifact | Status | Verdict |
|----------|--------|---------|
| Review report (`reports/reviews/goal-ops-hardening-iter-27-review.md`) | exists | PASS |
| QA report (`reports/qa/goal-ops-hardening-iter-27-qa.md`) | exists | PASS |
| Audit report (`docs/handoffs/goal-ops-hardening-iter-27-audit.md`) | exists | PASS_WITH_GAPS (acceptable per gate) |

All three formal pipeline gates are individually present and each carries an acceptable verdict string.
This iteration is NOT blocked at Step 1. The block below is a Step 2/3 finding: the audit's own
PASS_WITH_GAPS is explicitly conditional ("Proceed, but do not let the evidence gap close silently") and
the gap it names is exactly the one this gate exists to catch.

---

## UI Visibility Artifact Checks

| Artifact | Exists | Non-Empty | Non-Vague | Status |
|----------|--------|-----------|-----------|--------|
| implementation-summary.md | yes | yes | yes | OK |
| user-visible-changes.md | yes | yes | yes | OK |
| ui-surface-map.md | yes | yes | yes | OK |
| ui-test-plan.md | yes | yes | yes | OK |
| ui-test-results.md | yes | yes | non-vague prose, but **critically incomplete** | **GAP — see below** |
| what-to-click.md | yes | yes | yes (6 numbered steps) | OK |

All 6 files exist with real, specific content — no placeholder/TODO artifacts. The failure here is not
"missing/vague artifact," it is that `ui-test-results.md` reports only a fraction of what
`ui-test-plan.md` itself scoped, and the fraction it does report never touches the iteration's actual
deliverable.

### `ui-test-results.md` in detail (independently re-derived, not taken on the file's own summary line)

- `ui-test-plan.md` (written by ui-test-designer) specifies **9** test cases, UT-01 through UT-09,
  purpose-built for this iteration: UT-02 is the core "stale" disclosure happy path, UT-06 is the
  concurrent-`/backtest`-race error test (the AG-8 fix), UT-03/04/07/08/09 are the regression guards.
- `reports/phase-goal-ops-hardening-iter-27-ui-test-results.md` contains **zero rows for UT-01 through
  UT-09**. Its table instead reports the deterministic *golden-replay* lane (relabeled `UT-J-01` etc.),
  which is a different, pre-existing regression mechanism covering J-01/J-03/J-04/J-06/J-09 —
  not the iteration-specific test plan at all.
- I checked `reports/qa/goal-ops-hardening-iter-27-evidence/` directly (`ls -la`): it holds 7 PNGs total —
  `J-01/J-03/J-04/J-06/J-09-verify.png` (golden-replay captures) plus exactly two files that do match the
  ui-test-plan's own IDs: `UT-01-data-page-top.png` and `UT-05-backtest-latest-fullpage.png`. Both of
  those are smoke tests ("does the page load"). **UT-02 (stale-state disclosure) and UT-06 (the
  concurrent-race reproduction) — the two test cases that actually exercise this iteration's two fixes —
  have no screenshot, no DOM-text-cross-check record, and no row in ui-test-results.md at all.**
- The provenance note accompanying this dispatch confirms why: the browser-QA agent was killed mid-run by
  an account usage limit before it got past the first two smoke tests, and no `.llm.md` variant exists for
  this iteration to fill the gap.
- The file's own summary line — "Overall: 4/5 journeys passed (0 skipped)" — is accurate only for the
  5 golden-replay rows it happens to show; it silently omits that the phase spec's actual
  **target journeys, J-05/J-07/J-08, have no row at all**, and reads, out of context, as if the iteration's
  QA coverage were complete. It is not a false statement about the 5 rows present, but it is a misleading
  one about the iteration's overall verification state if read at face value.

This matches the skill's blocking criterion "Frontend Present: yes but no UI test execution at all" in
substance where it matters most: for the exact two capabilities (`/data` stale disclosure, `/backtest`
concurrency fix) and the exact three journeys (J-05, J-07, J-08) this iteration exists to deliver, **UI
test execution is entirely absent** — not SKIPPED-with-a-documented-reason, but cut short by an
account-limit kill with no downstream re-run yet.

---

## Cross-Reference Checks

- [x] `user-visible-changes.md` lists ≥1 specific capability — yes (the `/data` stale-coverage disclosure,
  described concretely with before/after wording).
- [x] `ui-surface-map.md` has specific route/component entries — yes (`/data` `CoveragePanel`, `/backtest`
  evidence page, with exact test instructions per row).
- [x] `ui-test-plan.md` has specific steps with exact actions and expected results — yes, unusually
  thorough (exact selectors, exact expected strings, an explicit screenshot-capture-defect workaround
  protocol).
- [ ] `ui-test-results.md` shows execution evidence (or SKIPPED with documented reason) — **NO.** UT-02 and
  UT-06 (this iteration's two purpose-built core tests) are neither executed nor marked
  SKIPPED-with-reason inside the artifact itself — they are simply absent from it. J-05/J-07/J-08 (the
  phase's Target journeys per the phase spec's own metadata) have no row anywhere in the merged results.
  The reason (quota kill) is documented only in the coordinator's out-of-band note to this closure pass,
  not in the artifact a future reader would consult.
- [x] `what-to-click.md` has ≥3 numbered steps with exact expected outcomes — yes, 6 steps, each with a
  concrete expected result.
- [ ] `implementation-summary.md` claims are consistent with `ui-test-results.md` evidence —
  **INCONSISTENT.** `implementation-summary.md`'s "Incomplete Items" section states: *"None from this
  iteration's scope. Everything listed in the phase spec was built and verified."* The phase spec's own
  Definition of Done, bullet 1, reads: *"J-05, J-07, J-08 pass via browser-qa-agent, re-verified with both
  fixes in place (TC-1, TC-2, TC-5, TC-6)."* That specific, named DoD item has no browser-qa-agent evidence
  anywhere in this iteration's artifacts — only developer self-verification (dev handoff's "Live
  Verification" section) stands in its place, which both the auditor (T2) and the ux-regression-reviewer
  independently flag as insufficient to equate to a completed browser-qa-agent pass. "Verified" in the
  implementation-summary is true only in the narrower sense of developer self-verification, not in the
  sense the phase spec's DoD requires.

---

## Blocking Issues

1. **DoD bullet 1 ("J-05, J-07, J-08 pass via browser-qa-agent") is unmet — zero browser-QA evidence for
   the iteration's own target journeys.**
   The merged `ui-test-results.md` has no row, screenshot, or DOM-check for J-05, J-07, or J-08, and no
   row for UT-02 (stale-disclosure) or UT-06 (concurrent-race), the two test cases the ui-test-designer
   built specifically to exercise them. This is not a benign SKIP with a documented, accepted reason inside
   the artifact — it is an unrun check caused by a mid-run account-quota kill, and the file that should
   record that reason does not. The only standing evidence is the developer's own self-verification
   (real, concrete, and independently spot-checked by the auditor as substantively convincing — but
   self-verification is explicitly what the pipeline's browser-qa-agent stage exists to avoid resting on
   alone for a DoD sign-off).
   **Remediation:** Re-dispatch the browser-qa-agent for this iteration scoped to UT-02, UT-06, UT-03,
   UT-04, UT-07, UT-08 (the ui-test-plan.md cases with no evidence yet), with the full-page-capture +
   DOM-text-cross-check protocol the plan itself specifies (UT-06 in particular needs a genuinely
   never-scanned date — not `2011-03-10`, already consumed). Merge the result into
   `reports/phase-goal-ops-hardening-iter-27-ui-test-results.md` before re-running this closure gate.

2. **`implementation-summary.md`'s "Everything listed in the phase spec was built and verified" overstates
   the current verification state** given Blocking Issue 1. It is accurate for "built"; it is not yet
   accurate for "verified" in the DoD's own sense.
   **Remediation:** No code change needed. Once Blocking Issue 1 is remediated and browser-QA evidence for
   J-05/J-07/J-08 exists, this claim becomes true and no edit is required; if a decision is instead made to
   accept developer self-verification in lieu of browser-qa-agent evidence, that decision needs to be an
   explicit, documented owner call (as the audit itself recommends), not a silent pipeline pass-through.

---

## Non-Blocking Notes (tracked, not gating this verdict)

- **J-06 golden-replay FAIL is well-investigated and most likely not a regression from this iteration's
  diff**, per both the auditor (T3) and the ux-regression-reviewer: it traces to a shared,
  session-unscoped `runs/goal-session-mcp-loop/state/drift-report.json` that appears to be mutated by
  other concurrent goal-mode sessions on this host, and the golden script's step-1 assertion
  ("DEGRADED") is itself an incidental capture-time artifact unrelated to J-06's actual subject. Neither
  investigator could get a *live* re-confirmation (services were down at review time). Per the
  coordinator's framing, this is reported here as an unresolved-but-well-evidenced item, not scored as a
  pass or a fail in this gate's own accounting. Recommend the auditor's proposed fix: drop the incidental
  "DEGRADED" expectation from J-06 step 1 and scope `readiness.drift.report_path` per goal-mode session.
- **Audit finding B1 (fabricated `rows_inserted` count) was found and fixed during the audit itself**, with
  a new regression test (`test_iter27_audit_returned_count_is_truthful_when_collision_follows_earlier_flushed_symbols`),
  bringing the combined suite to 201 passed. This is a positive signal on code quality, not a blocker.
- **Audit finding B2 (GAP, carried)**: `_backfill`'s cross-call rollback residual survives B1's fix and is
  explicitly deferred to a future scoped iteration by the auditor's own recommendation — correctly out of
  this iteration's scope, not a blocker here.
- **Audit finding B5 (GAP, carried)**: two unhandled `MemoryError` exceptions on `GET /api/evidence` and
  12–24 minute historical `/backtest` latencies were observed live inside this iteration's own QA window,
  unrelated to this diff and explicitly out of scope, but flagged by the auditor for owner awareness
  alongside the already-open cold-`/backtest` budget decision. Carrying forward, not blocking.
- **Test finding T1 (QA report accuracy)**: the QA report's TC-01 claim of reproducing the race is vacuous
  (it reused an already-scanned date) and its "ASGI exception count unchanged" claim is factually wrong
  (13→15 in-window). The underlying fix itself is still well-corroborated by other means (audit T4); this
  is a report-quality issue, not a product defect, and does not itself change this gate's verdict — it is
  noted here so a future reader does not treat the QA report's narrative as additional independent
  corroboration beyond what actually stands.
- The frontend deliverable itself (the `CoveragePanel` stale notice) is well-built and well-evidenced:
  real code read by both the auditor and ux-regression-reviewer, a live developer screenshot showing the
  exact specified text and a calm, non-alarming tone using the file's existing design tokens, and correct,
  additive, one-endpoint data-contract wiring. The gap this verdict blocks on is the *independent
  verification* step, not the underlying implementation.

---

## Recommendation

Re-run browser-QA (or its LLM re-confirmation lane) specifically for UT-02, UT-03, UT-04, UT-06, UT-07,
UT-08 and merge real rows for J-05/J-07/J-08 into `ui-test-results.md`, then re-submit this iteration to
the phase-closure gate. The underlying code fixes (AG-8 mid-loop collision handling, AG-3 stale-coverage
disclosure) are well-supported by unit tests, an independent audit pass, and the developer's own live
reproduction — the block here is specifically the absence of the browser-qa-agent's independent
confirmation that the phase spec's Definition of Done explicitly requires for J-05/J-07/J-08, not a doubt
about the fixes' correctness.
