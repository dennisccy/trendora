# Phase goal-mcp-loop-iter-36 — Closure Verdict

**Phase:** goal-mcp-loop-iter-36 — Certifier calibration: referee placebo + lookahead-tripwire audit (J-22)
**Date:** 2026-07-15
**Written by:** phase-closure-auditor

---

**Verdict:** CLOSURE-FAIL

---

## Standard Pipeline Gate Checks

| Artifact | Status | Verdict |
|----------|--------|---------|
| Review report (`reports/reviews/goal-mcp-loop-iter-36-review.md`) | exists | PASS_WITH_NOTES |
| QA report (`reports/qa/goal-mcp-loop-iter-36-qa.md`) | exists | PASS |
| Audit report (`docs/handoffs/goal-mcp-loop-iter-36-audit.md`) | exists | PASS_WITH_GAPS |

All three standard gates pass at face value. Step 1 alone would not block this phase. The block below comes from Step 3 (cross-reference validation), where a claim in the QA report does not survive comparison against the more rigorous artifacts in this same pipeline.

---

## UI Visibility Artifact Checks

| Artifact | Exists | Non-Empty | Non-Vague | Status |
|----------|--------|-----------|-----------|--------|
| `reports/phase-goal-mcp-loop-iter-36-implementation-summary.md` | yes | yes (77 lines) | yes | OK |
| `reports/phase-goal-mcp-loop-iter-36-user-visible-changes.md` | yes | yes (47 lines) | yes | OK |
| `reports/phase-goal-mcp-loop-iter-36-ui-surface-map.md` | yes | yes (52 lines) | yes | OK |
| `reports/phase-goal-mcp-loop-iter-36-ui-test-plan.md` | yes | yes (372 lines) | yes | OK |
| `reports/phase-goal-mcp-loop-iter-36-ui-test-results.md` | yes | yes (182 lines) | yes | OK |
| `reports/phase-goal-mcp-loop-iter-36-what-to-click.md` | yes | yes (55 lines) | yes | OK |

All six artifacts exist with substantive, specific, non-templated content — exact numeric values, `data-testid`s, byte-verbatim expected strings, and real screenshot evidence (`reports/qa/goal-mcp-loop-iter-36-evidence/UT-*.png`, independently confirmed present on disk). This is not a Frontend-Present-yes-but-backend-only phase: `implementation-summary.md` and `user-visible-changes.md` both name a concrete new page and concrete new capability, and `ui-surface-map.md` confirms `/research/referee-audit` and the 4th `/research` nav card as real, additive frontend surfaces. The optional `reports/phase-goal-mcp-loop-iter-36-ux-regression.md` also exists (UX-REGRESSION-PASS) and is substantive.

---

## Cross-Reference Checks

- [x] user-visible-changes lists ≥1 specific capability — yes, several, with exact live values (false-pass rate 0.08, CI [0.04984, 0.126], α 0.05, run date 2026-07-01)
- [x] ui-surface-map has specific route/component entries — yes, a table naming `/research/referee-audit`, `/research`, and specific `data-testid`s per state
- [x] ui-test-plan has specific steps with exact actions and expected results — yes, 13 cases (UT-01–UT-13), each with byte-verbatim expected text
- [x] ui-test-results shows execution evidence — yes, 13/13 executed and passed, screenshots present on disk, `curl`/source-grep cross-checks cited alongside DOM `extract` calls
- [x] what-to-click has ≥3 numbered steps with exact expected outcomes — yes, 7 steps — **but see Non-Blocking Note 1**: step 7's expected text is stale/inaccurate
- [ ] **implementation-summary / QA claims are consistent with the evidence in this pipeline — FAILS for one specific, named claim (see Blocking Issue below)**

---

## Blocking Issues

1. **QA report's "required-still-passing… All live-verified ✓" claim is not evidenced for J-05 and J-11, and this exact gap was raised twice inside the pipeline and never resolved before reaching this gate.**

   The phase's own Definition of Done (`docs/phases/goal-mcp-loop-iter-36.md:85`) requires: *"Required-still-passing journeys J-01, J-03, J-05, J-11, J-17, J-18, J-19, J-20 remain green — **LIVE-re-verified via the browser-qa lane** (a FULL iter has no deterministic-replay lane; live re-verification reaches CLOSURE-PASS — the iter-35 pattern), **or the closure one-liner replay run inline**."

   `reports/qa/goal-mcp-loop-iter-36-qa.md:14` and `:261` assert this is fully satisfied ("All live-verified ✓"). On inspection this is true for 6 of 8 but not for J-05 or J-11:

   - **TC-19** (`goal-mcp-loop-iter-36-qa.md:119`, J-05/regime-conditioned evidence) evidence text is: *"No regression detected from new module/config block"* — a conclusion, not an observation; names no page, no rendered value, no screenshot.
   - **TC-20** (`goal-mcp-loop-iter-36-qa.md:120`, J-11/honest uncertainty marking) evidence text is: *"Unproven signals correctly marked in evidence"* — again no specific value, no screenshot.
   - These are the **only two rows out of 24** in the QA report's functional test table that lack any falsifiable, specific observation (every other row — TC-01–18, TC-21–24 — names a concrete value, string, or file). I independently confirmed via `ls reports/qa/goal-mcp-loop-iter-36-evidence/` that screenshots exist for TC-09, TC-12, TC-17, and TC-21 only — **no TC-18, TC-19, TC-20, TC-22, TC-23, or TC-24 screenshot exists**.
   - The dedicated, purpose-built lane the DoD names — the ui-test-designer → browser-qa-agent pipeline that produced `ui-test-plan.md`/`ui-test-results.md` (UT-01–UT-13) — **explicitly and transparently excludes the required-still-passing set** from its scope. `reports/phase-goal-mcp-loop-iter-36-ui-test-results.md:168-169` states this in writing: *"Required-still-passing set out of my dispatched scope… I did not fabricate coverage for journeys outside my assigned test plan… Whether that DoD line is satisfied… is a decision for the auditor/goal-evaluator step, not something I ran myself."*
   - `reports/phase-goal-mcp-loop-iter-36-ux-regression.md:42-43` **independently raised the identical concern**, by name, addressed to the auditor: *"the actual dispatched browser-qa test plan (UT-01–UT-13)… does not contain a live navigation to `/stocks`, which is the page J-01… and J-11… both depend on… Recommend the auditor either dispatch one supplemental live `/stocks` check or explicitly invoke the DoD's own documented fallback… before closing the iteration"* (repeated at line 87).
   - I read `docs/handoffs/goal-mcp-loop-iter-36-audit.md` in full: it contains **zero mentions** of J-01, J-05, J-11, `/stocks`, or the required-still-passing verification question anywhere in its 5 findings (B1, B2, F1, T1, T2). The explicit recommendation from two upstream agents reached the auditor and was not acted on or acknowledged.
   - I confirmed the fallback path was not exercised either: both backend and frontend are currently stopped (health checks return `000`), and while golden-replay scripts for J-05 and J-11 exist (`runs/goal-session-mcp-loop/journey-scripts/J-05.json`, `J-11.json`), nothing in any artifact indicates `scripts/automation/lib/demo_runner.py --mode verify` was run against them this iteration (contrast with J-22's own script, which `ui-test-results.md:168` explicitly documents as linted and live-replayed before that report was written).

   **This is narrow, not a verdict on the J-22 feature itself.** J-22's own deliverable is thoroughly and rigorously verified (13/13 UT tests, byte-verbatim text checks, `curl` cross-checks, source-level badge-color verification), and the dominant failure mode (isolation of the real ledgers/budget) is independently confirmed three separate ways (dev, QA, audit, and my own `git status --porcelain` on the three real files, which returned empty). The regression risk to J-05/J-11 is also plausibly low — the iteration's diff (`app/engine/referee_audit.py`, `app/api/referee_audit.py`, `config.py`, `main.py`, `config.yaml`, `research/page.tsx`, `lib/api.ts`, `lib/referee-audit.ts`) never touches the scoring/regime/evidence-badge code paths J-05/J-11 depend on. But this project's own phase spec explicitly treats "skip the canonical live lane, reason from the diff instead" as a previously-costly failure mode (the spec's own NOTES cite the "canonical-lane discipline (iter-13/20/22/31 lesson)"), so a diff-based argument is not, by this project's own standard, a substitute for the DoD's named live-or-replay check. The claim of completion in the QA report's summary table is what fails on inspection, not the underlying feature.

   **Remediation:**
   1. Start the backend and frontend (`scripts/start-backend.sh`, `scripts/start-frontend.sh`; wait for `/api/data` to return 200).
   2. Either (a) live-navigate to the surfaces J-05 and J-11 depend on and capture the same class of concrete evidence TC-17/TC-21 captured (specific rendered values/text, a screenshot), or (b) run the existing golden-replay scripts for exactly these two journeys — e.g. `scripts/automation/lib/demo_runner.py --mode verify --journeys J-05,J-11` against the running frontend — mirroring how J-22's own script was verified this iteration per `ui-test-results.md:168`.
   3. Update `reports/qa/goal-mcp-loop-iter-36-qa.md`'s TC-19/TC-20 rows (or append a supplemental QA note) with the concrete evidence obtained, replacing the current unfalsifiable text.
   4. Re-run this closure check.

---

## Non-Blocking Notes

1. **`what-to-click.md` step 7 has stale/inaccurate expected text.** `reports/phase-goal-mcp-loop-iter-36-what-to-click.md:39` tells an operator to expect `/evidence` to show *"a card headed 'No certified claims yet'"*. The actual, correctly-documented live state (per `ui-test-results.md`'s UT-13 note, lines 137-150) is **7 individual claim rows, all badged FAIL, zero PASS** — this is the real, DoD-sanctioned baseline (`docs/phases/goal-mcp-loop-iter-36.md:82`: "0 PASS, 7 FAIL"), not an empty-state card. `ui-test-plan.md`'s UT-13 carries the same stale wording, and the browser-qa-agent already caught and explained the mismatch transparently rather than silently passing it — but `what-to-click.md`, which a non-technical operator would follow literally, was not corrected to match. Following this guide today would produce a false "something's broken" impression at step 7. Recommend fixing the wording in both `ui-test-plan.md` (UT-13) and `what-to-click.md` (step 7) to describe the actual 7-FAIL-row state. Not blocking: the substantive isolation claim the step exists to verify is true and independently triple-corroborated (page content, `git diff` empty, `/research/budget` counters unchanged).

2. **Persisted report artifact is git-untracked (audit finding B1, independently re-confirmed).** `runs/goal-session-mcp-loop/state/referee-audit-report.json` shows `??` under `git status`, while the analogous iter-35 sibling (`drift-report.json`) is committed. On a clean checkout the page would show the honest-empty state rather than the real calibration data the browser-qa evidence is based on. The audit report already flagged this and assigned it to the release/showcase commit step (not a code defect — the empty state is itself a tested, DoD-sanctioned state). I concur with that disposition; flagging again here only for visibility so it isn't lost before the commit/showcase step.

3. **Audit findings B2 and F1 are adequately disposed of by the audit report and require no further action here**: B2 (contaminated assembler materializes a full horizon-slice in Python rather than SQL-bounding by cohort date) is offline-CLI-only, never reachable from any serving path (grep-confirmed by the auditor); F1 (tripwire prose reads as a stronger indictment than the underlying tautological-construction limitation warrants) is a spec-sanctioned outcome ("expected: rejected" is the DoD's own label for this exact branch). Both are correctly non-blocking per the audit's own reasoning, which I have no evidence to contradict.

4. **Minor QA-report accuracy note (relates to audit finding T2).** The QA report (`goal-mcp-loop-iter-36-qa.md:248`) states the dev handoff's test-count error was *"corrected in the handoff (commit a089d7a)."* I independently read the current dev handoff (`docs/handoffs/goal-mcp-loop-iter-36-dev.md`): the "Tests Run" section (line 114) is correct ("39 passed... 34 from test_referee_audit.py + 5 from test_api_referee_audit.py"), but the "Files Changed" section (line 73) still reads *"41 tests"* — i.e., the fix was partial, and the audit report's T2 finding ("Dev handoff line 74 says '41 tests'... remains") is accurate as of this reading. Cosmetic only, correctly scored MINOR/OBSERVATION by the reviewer and auditor — not blocking — but noted here because it is a second, independently-confirmed instance of a specific QA-report claim not matching the artifact it describes, which is part of why Blocking Issue #1 above was investigated rather than taken at face value.
