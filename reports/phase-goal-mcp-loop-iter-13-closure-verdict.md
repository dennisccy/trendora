# Phase goal-mcp-loop-iter-13 — Closure Verdict

**Phase:** goal-mcp-loop-iter-13
**Date:** 2026-07-01
**Written by:** phase-closure-auditor

---

**Verdict:** CLOSURE-FAIL

<!-- CLOSURE-FAIL: Browser QA recorded a P1 test failure (UT-05). The auditor applied a scroll fix
     that was not subsequently re-verified via browser QA. The ui-test-results.md verdict is FAIL. -->

---

## Standard Pipeline Gate Checks

| Artifact | Status | Verdict |
|----------|--------|---------|
| Review report (`reports/reviews/goal-mcp-loop-iter-13-review.md`) | exists — PASS | PASS |
| QA report (`reports/qa/goal-mcp-loop-iter-13-qa.md`) | exists — PASS_WITH_NOTES | PASS_WITH_NOTES (gate expects PASS) |
| Audit report (`docs/handoffs/goal-mcp-loop-iter-13-audit.md`) | exists — PASS_WITH_GAPS | PASS |

**Note on QA report:** The gate specification requires "PASS" for the QA report; the issued verdict is
PASS_WITH_NOTES. This is a secondary concern — the QA agent's notes are partly based on a
misdiagnosis (it believed the badge was not flipping; the audit report corrects this, showing the badge
DID flip in the browser-qa run). The more significant issue is addressed under Blocking Issues below.

---

## UI Visibility Artifact Checks

| Artifact | Exists | Non-Empty | Non-Vague | Status |
|----------|--------|-----------|-----------|--------|
| phase-goal-mcp-loop-iter-13-implementation-summary.md | yes | yes (73 lines) | yes — 3 specific features described with routes and values | OK |
| phase-goal-mcp-loop-iter-13-user-visible-changes.md | yes | yes (34 lines) | yes — 4 specific user-facing capabilities listed | OK |
| phase-goal-mcp-loop-iter-13-ui-surface-map.md | yes | yes (37 lines) | yes — 5 specific route/component rows with test instructions | OK |
| phase-goal-mcp-loop-iter-13-ui-test-plan.md | yes | yes (414 lines) | yes — 14 test cases with exact steps and expected results | OK |
| phase-goal-mcp-loop-iter-13-ui-test-results.md | yes | yes (230 lines) | yes — 14 tests executed, per-test evidence cited | OK (execution evidence present; but Browser QA Verdict: FAIL) |
| phase-goal-mcp-loop-iter-13-what-to-click.md | yes | yes (58 lines) | yes — 8 numbered steps with exact expected outcomes | OK |

All 6 UI visibility artifacts exist and contain real, non-placeholder content. The quality gate is
met for artifact presence; the blocking issue is the FAIL verdict within ui-test-results.md.

---

## Cross-Reference Checks

- [x] user-visible-changes lists 4 specific capabilities the user can try (combination badge, 6th evidence row, click-through, honest not-yet-proven state)
- [x] ui-surface-map names specific routes (`/research/factor-combination`, `/evidence`) and specific components (`CombinationEvidenceBadge`, `CombinationLab`, `CombinationTable`, `ClaimRow`)
- [x] ui-test-plan has 14 test cases with exact numbered steps, specific selector names (`data-testid="combination-evidence-badge"`), and precise expected values (+4.69%, 2026-07-01, "Proven" / "Not yet proven")
- [x] ui-test-results shows evidence of actual execution — 14 tests run (0 SKIPPED), with per-test DOM evidence and screenshot paths cited
- [x] what-to-click has 8 numbered steps with specific expected outcomes, troubleshooting section, and exact URL + anchor values
- [x] implementation-summary claims are substantially consistent with ui-test-results evidence: the core claimed capabilities (badge flips, 6th evidence row, reactive updates) are all browser-verified PASS

**Inconsistency flagged:** The ui-test-plan designates UT-05 as P1 happy-path and states "P1 tests (UT-01 through UT-07, UT-10, UT-11, UT-12) must all pass for browser QA verdict to be PASS." UT-05 failed in the browser-qa run. The implementation-summary and what-to-click guide (step 4) both describe the deep-link scroll-into-view as an expected user experience; the browser QA confirms it did not work at the time of testing. The auditor applied a fix, but the fix has not been re-tested in a browser.

---

## Blocking Issues

1. **Browser QA verdict FAIL — P1 test UT-05 failed, auditor fix unverified:**
   The browser-qa-agent's ui-test-results.md records `Browser QA Verdict: FAIL`. UT-05 ("Proven badge
   deep-link navigates to evidence anchor", P1 happy-path) failed: after clicking the "Proven" badge on
   `/research/factor-combination`, the browser navigated to the correct URL
   (`/evidence#combination-high_proximity-rs_spy_3m-h20`) but `window.scrollY` remained 0 and the
   combination claim row (at top=1585px) remained below the viewport (height=1252px). UT-14 (P2 UX)
   failed for the same reason on direct navigation.

   The auditor identified the root cause (no JS hash-scroll in the async-loading `/evidence` page) and
   applied a fix: an additive hash-scroll `useEffect` keyed on the load→ok transition in
   `apps/frontend/app/evidence/page.tsx`. The auditor verified the fix via `tsc --noEmit` and confirmed
   `lib/evidence.test.ts` still passes 37/37. However, the auditor explicitly stated: "The remaining gap
   is that my scroll fix awaits a browser-qa re-run to confirm UT-05/UT-14 flip to PASS."

   No browser QA re-run was conducted. The sole ui-test-results.md on file records "Browser QA Verdict:
   FAIL." The plan required the "canonical browser-qa-agent lane MUST actually run" and the phase spec
   includes the deep-link scroll-into-view ("click through to its /evidence row") in the J-08 definition
   of done. The J-08 deep-link flow is not browser-confirmed with the fix applied.

   **Remediation:** Re-run the browser-qa-agent against the running stack (frontend port 3255, backend
   port 8255) with the auditor's `evidence/page.tsx` scroll fix in place. At minimum, execute UT-05 and
   UT-14 and confirm both flip to PASS. If they pass, write an updated or supplemental
   `reports/phase-goal-mcp-loop-iter-13-ui-test-results.md` (or an addendum file) with a PASS verdict.
   Command: `./scripts/automation/browser-qa-phase.sh goal-mcp-loop-iter-13`

---

## Non-Blocking Notes

- **QA report PASS_WITH_NOTES vs expected PASS:** The gate specification nominally requires "PASS" for
  the QA report. The issued verdict is PASS_WITH_NOTES. The QA agent's central browser-issue note (that
  the badge was not flipping) was later shown by the audit to be incorrect — the badge DID flip (UT-03
  PASS). The QA report is partly misinformed; the browser-qa-agent's test results (which the QA report
  should wrap) are the ground truth. This is a documentation/process concern, not a functional one; the
  re-run of browser QA (above) will supersede it.

- **UX regression report absent:** `reports/phase-goal-mcp-loop-iter-13-ux-regression.md` does not
  exist. This is not blocking — the pipeline may not require a separate UX regression report in
  goal-mode iterations, and the QA/audit artifacts cover UX regression checks.

- **UT-05 P1 classification vs scroll-only failure scope:** The failing scroll behavior is a UX
  enhancement rather than a core capability failure — the URL does navigate to the correct anchor page and
  the row IS present (just below the fold). The 12 PASS tests confirm all core J-08 flows (badge flips,
  6th evidence row with correct data, reactive updates, linkbacks, regression). The P1 label and the plan's
  explicit scroll-into-view requirement make this blocking, but the remediation (a browser-qa re-run) is
  a single straightforward step.
