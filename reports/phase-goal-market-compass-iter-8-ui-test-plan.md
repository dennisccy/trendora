# Phase goal-market-compass-iter-8 — UI Test Plan

**Phase:** goal-market-compass-iter-8
**Date:** 2026-08-21
**Written by:** ui-impact-analyst (combined mode)
**Frontend URL:** not started this iteration — starting the frontend was explicitly out of scope per
the phase spec's host-safety guardrails ("never start the frontend... this iteration — a second
goal-mode engine may be active on this host, which froze once already from two concurrent backends,
memory overcommit + swap-thrash, no OOM kill, 2026-08-20"). The dispatch metadata for this report
named `http://localhost:3255`, but that line is not authoritative for this iteration's scope (see the
discrepancy note in `reports/phase-goal-market-compass-iter-8-user-visible-changes.md`) and was not
exercised.

---

## Scope note (read before concluding this document is incomplete)

`Frontend Present: no` for this iteration (`docs/phases/goal-market-compass-iter-8.md`; no
`runs/goal-market-compass-iter-8/plan.md` exists on disk). Per this project's "Backend-only phase
handling" + combined-mode precedent (see `reports/phase-goal-ops-hardening-iter-44-ui-test-plan.md`
for the pattern this follows, and `reports/phase-goal-market-compass-iter-7-ui-test-plan.md` for the
same J-10 feature hitting this identical situation one iteration earlier), a backend-only iteration
still owes one `UT-<journey-id>` regression case for every journey named on EITHER the phase spec's
`Required-still-passing journeys:` line OR its `Target journeys:` line — IF that journey has a
browser-observable UI surface.

This iteration's metadata names:
- **Required-still-passing journeys:** None — explicitly, deliberately empty. The phase spec's own
  BACKGROUND section states: "J-01–J-04 re-verification stays OUT of this iteration, unconditionally,
  even if recovery succeeds... deferred to iteration 9, UNCONDITIONALLY, regardless of whether this
  iteration's recovery succeeds" — a deliberate choice to avoid bundling a live cross-vendor data
  write with a live UI re-check in the same iteration, repeating iteration 7's own reasoning for the
  same underlying constraint.
- **Target journeys:** J-10 — but J-10 itself has **no UI surface**, ever, not merely "no UI surface
  changed this iteration." The phase spec's `### Frontend` section states this explicitly: "None —
  J-10 has no UI surface (goal.md: 'Walkthrough: waived — data-layer repair with no UI surface change
  of its own')."

**Union of both lines with a browser-observable UI surface: zero journeys.** This is why this document
contains no `UT-` test cases — not an oversight. This iteration's live run did partially succeed (20
of 587 proven-missing symbols restored, causing `GET /api/compass?as_of=2026-08-12` to now return 200
instead of 400 — see the user-visible-changes report), but the phase spec is explicit that this
outcome does not pull J-01–J-04 into this iteration's testing scope: "The dispatching coordinator's
context permits planning browser-QA for J-01–J-04 'unless the recovery actually completes and
verifies first' — but a goal-mode spec is fixed before dispatch... there is no way to make a named
journey's lane conditional on an earlier step's runtime outcome within one spec." Separately,
`docs/goal.md`'s newly-recorded J-10/J-11 responsibility boundary places the final repaired-state
J-01/J-02/J-03 replay claim in a not-yet-run **J-11 Stage G**, not in J-10 at all — so even a full
(not just partial) restoration this iteration would not have moved those journeys into scope here.

Writing a `UT-J-10` browser case here, or a `UT-J-0x` case for J-01–J-04, would mean inventing a click
path this iteration's own spec forbids testing and opening a browser against a dataset that is still
only 20/587 (3.4%) repaired for the two affected dates — directly contrary to this report's explicit
instruction not to plan or recommend browser verification against the current dataset, and to the
phase spec's own "No browser-QA or deterministic-replay lane runs against J-01, J-02, J-03, or J-04
this iteration, regardless of the recovery's outcome" (TC-19).

## Test Cases

None. See scope note above.

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| *(none)* | No journey in scope this iteration has a browser-observable UI surface | — | — | — |

**Nothing gates a P1 browser-QA verdict this iteration** — there are no P1 (or any) UT cases to run.
This is consistent with the phase spec's own testing requirements: "Browser: none. J-10 has no UI
surface (walkthrough waived). No browser-QA runs against J-01–J-04 this iteration — deferred to
iteration 9 unconditionally."
