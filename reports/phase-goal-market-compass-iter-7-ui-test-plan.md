# Phase goal-market-compass-iter-7 — UI Test Plan

**Phase:** goal-market-compass-iter-7
**Date:** 2026-08-20
**Written by:** ui-impact-analyst (combined mode)
**Frontend URL:** not started this iteration — starting the frontend was explicitly out of scope per
the phase spec's host-safety guardrails ("Never start the frontend... this iteration — a second
goal-mode engine may be active on this host, which froze once already from two concurrent backends").
The dispatch metadata for this report named `http://localhost:3255`, but that line is not authoritative
for this iteration's scope (see the discrepancy note in
`reports/phase-goal-market-compass-iter-7-user-visible-changes.md`) and was not exercised.

---

## Scope note (read before concluding this document is incomplete)

`Frontend Present: no` for this iteration (`runs/goal-market-compass-iter-7/plan.md`,
`docs/phases/goal-market-compass-iter-7.md`). Per this project's "Backend-only phase handling" +
combined-mode precedent (see `reports/phase-goal-ops-hardening-iter-44-ui-test-plan.md` for the pattern
this follows), a backend-only iteration still owes one `UT-<journey-id>` regression case for every
journey named on EITHER the phase spec's `Required-still-passing journeys:` line OR its `Target
journeys:` line — IF that journey has a browser-observable UI surface.

This iteration's metadata names:
- **Required-still-passing journeys:** None — explicitly, deliberately empty. The phase spec's
  BACKGROUND section states this in full: J-01/J-02/J-03/J-04's browser-lane re-verification is
  "explicitly deferred to iteration 8... independent of this iteration's outcome," to avoid bundling a
  live cross-vendor data write with a live UI re-check in the same iteration (the "never bundle two
  risky journeys" rule, invoked directly in the spec).
- **Target journeys:** J-10 — but J-10 itself has **no UI surface**, ever, not merely "no UI surface
  changed this iteration." The phase spec states this explicitly: "None — J-10 has no UI surface
  (goal.md: 'Walkthrough: waived — data-layer repair with no UI surface change of its own')."

**Union of both lines with a browser-observable UI surface: zero journeys.** This is why this document
contains no `UT-` test cases — not an oversight, and not the same situation as a typical
`Frontend Present: no` iteration that still touches existing pages (contrast
`phase-goal-ops-hardening-iter-44-ui-test-plan.md`, where 8 pre-existing UI journeys needed regression
coverage despite zero frontend files changing that iteration). Here, the one named journey (J-10) was
never a browser journey to begin with, and the only journeys that would need regression coverage
(J-01–J-04) are explicitly excluded from this iteration's testing scope by the phase spec itself.

Writing a `UT-J-10` browser case here, or a `UT-J-0x` case for J-01–J-04, would mean inventing a click
path this iteration's own spec forbids testing and opening a browser against a dataset this iteration's
own recovery gate did not finish repairing — directly contrary to this report's explicit instruction not
to plan or recommend browser verification against the current dataset, and to the phase spec's own "No
browser-QA or deterministic-replay lane runs against J-01, J-02, J-03, or J-04 this iteration,
regardless of the recovery's outcome."

## Test Cases

None. See scope note above.

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| *(none)* | No journey in scope this iteration has a browser-observable UI surface | — | — | — |

**Nothing gates a P1 browser-QA verdict this iteration** — there are no P1 (or any) UT cases to run.
This is consistent with the phase spec's own testing requirements: "Browser: none. J-10 has no UI
surface (walkthrough waived). No browser-QA runs against J-01–J-04 this iteration — deferred to
iteration 8."
