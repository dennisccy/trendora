# Phase goal-market-compass-iter-13 — UI Test Plan

**Phase:** goal-market-compass-iter-13 (J-11 Stage C — owner-authorized bounded destructive clear)
**Date:** 2026-08-24
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3255

**Not executed this iteration.** Maintenance isolation (ruling A5/A13, reaffirmed by C10) forbids
booting any application service, browser QA, or the deterministic-replay lane for the whole of
iter-13 — nothing below has been run, clicked, or observed. This report documents *why* it
contains zero executable UI test cases this iteration, so a later run does not mistake the
absence of cases for an oversight.

---

## Scope note (read before doing anything with this report)

Phase spec metadata: `Frontend Present: no`. `reports/phase-goal-market-compass-iter-13-ui-surface-map.md`
and the matching user-visible-changes report are both "Not mapped/observed — maintenance
isolation" — there is no UI-surface-map row to derive a NEW-surface (`UT-01`-style) case from, and
this iteration's own TC-16 mechanically forbids any file under `apps/frontend/` from appearing in
the diff (confirmed absent — the dev handoff's "Files Changed" / "Confirmed OUT of the diff"
section lists every file under `apps/frontend/` as untouched).

Per the "Backend-only phase handling" rule, this document checks BOTH journey metadata lines on
the phase spec (`docs/phases/goal-market-compass-iter-13.md`), not just one:

> **Required-still-passing journeys:** none mechanically re-verifiable this iteration —
> maintenance isolation (ruling A5/A13, still active) keeps the browser-QA lane and the
> deterministic-replay lane shut, so no journey can be replayed. For evaluator awareness only,
> unchanged and carried per `iteration-state.md`'s "Do not redo" list: J-01, J-04, J-10 stay
> `passing`; J-02, J-03, J-05, J-06, J-09 stay `partial`; J-07, J-08 stay `failing`. **None of
> their surfaces or Data-Contract values are touched by this iteration.**

> **Target journeys:** J-11 — Stage C only (step 11's rulings C1-C12; steps 1-10 and 12-14
> already govern the wider journey and are unchanged by this iteration)

### Required-still-passing resolves to zero journeys

Unlike iter-11's identically-worded opening ("none ... For evaluator awareness ...") — which went
on to actively name J-05/J-06/J-08 as journeys whose Data-Contract value that iteration's work
*touched*, and so earned three `UT-J-XX` regression cases in
`reports/phase-goal-market-compass-iter-11-ui-test-plan.md` — this iteration's line makes the
**opposite** claim explicitly: the carried J-01/J-02/J-03/J-04/J-05/J-06/J-07/J-08/J-09/J-10
statuses are listed "for evaluator awareness only" and the line states outright that "none of
their surfaces or Data-Contract values are touched by this iteration." That claim is consistent
with the actual live evidence this iteration produced: the mutation-accounting artifact
(`runs/goal-market-compass-iter-13/j11-stage-c-mutation-accounting.json`) proves the non-incident
`scanner_runs`/`scanner_results`/`sector_scores`/`theme_scores`/`forward_returns` population's
ID-set fingerprint is byte-identical before and after (the exact proof mechanism ruling C9
requires), and `next_session_manifests`/`data_provider_runs`/`watchlist` all show unchanged row
counts and full-value fingerprints. No journey outside the 11 incident dates had anything touched.
**No `UT-J-XX` case is written from this line.**

### Target journeys names J-11, which has no UI surface to test

`docs/goal.md`'s own J-11 entry states its Walkthrough acceptance item verbatim: **"Walkthrough:
waived — maintenance repair of the derived layer with no UI surface of its own; the demo
requirement is replaced by the pre/post inventory, the mutation reconciliation, the
cache-invalidation proof, and the manifest-immutability evidence."** This iteration's scope is
narrower still than the whole of J-11 — it is **Stage C only** (rulings C1-C12), the bounded
destructive clear, executed with maintenance isolation active and zero application-service boot
(ruling C10: "full depth means developer, reviewer, static/file-scoped QA, auditor, coherence and
evaluator, **not** application-service execution").

This exactly matches a precedent already established twice in this project for an
identically-shaped journey:
- `reports/phase-goal-market-compass-iter-11-ui-test-plan.md` excluded **J-11 itself** on this
  same ground ("Excluded: J-11 (Target journey) — no browser case written").
- That report in turn cites `reports/phase-goal-market-compass-iter-7-ui-test-plan.md`, which
  excluded **J-10** on the same ground (J-10's own goal.md entry: "Walkthrough: waived —
  data-layer repair with no UI surface change of its own").

Inventing a click path this iteration for a journey whose own contract declares it has none would
mean testing something that cannot exist. J-11 Stage C's own acceptance mechanism — the fresh
preflight, the intended-delete-set, the mutation-accounting ID-set diff, the completion marker —
is DB/file-level evidence, not renderable UI state. It is covered by this iteration's fixture
tests (TC-1 through TC-6, TC-13 in the functional test contract) and by the live evidence
artifacts the dev handoff cites, not by anything a browser can observe. **No `UT-J-11` row appears
below.**

For the record — grounding, not a UI claim — the evidence this iteration actually produced:
- `runs/goal-market-compass-iter-13/j11-stage-c-complete.json`: `"j11_stage_c_complete": true`,
  `"verdict": {"passed": true, "reason": "all_checks_passed"}`
- `docs/handoffs/goal-market-compass-iter-13-dev.md` closes with the literal lines
  `## J-11 STAGE C COMPLETE: YES` and `## J-11 STAGE D AUTHORIZED: NO`
- `runs/goal-market-compass-iter-13/j11-stage-c-mutation-accounting.json`: `scanner_runs` 3,121 →
  4 deleted → 3,117 post; `all_checks_pass: true`; the four deleted run ids (3114, 3148, 3149,
  3150) match the pre-declared intended-delete-set exactly; `daily_prices` 3,310,374 rows
  unchanged; `next_session_manifests` 24 rows, full 24×28 value diff `equal: true`

None of this is UI-observable, and none of it belongs in a UI test plan as a click-based case — it
is cited here only to show the zero-case result above reflects "something real happened, entirely
outside any UI surface," not "nothing was checked."

**Note for later re-verification (not this iteration's UI surface, but recorded so a future
operator does not misread it as a bug):** the 11 incident dates — including the 4 whose
`scanner_runs` rows this iteration deleted — now serve zero `scanner_runs` and zero derived
children. Once application-service boot is re-authorized, any UI surface asked for one of those
as-of dates (e.g. `/?asof=2026-08-11`) will hit a missing-run path until J-11 Stage D regenerates
them. That is the intended, owner-authorized mid-repair state left by this iteration — **not** a
regression, and not something a future `UT-J-XX` case should flag as a failure until Stage D has
run.

---

## Test Cases

None. Zero `UT-XX` / `UT-J-XX` cases this iteration — see the two resolutions above.

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| — | (no test cases this iteration) | — | — | — |

**Zero NEW-surface test cases** — `Frontend Present: no`, empty UI surface map, TC-16 mechanically
forbids any `apps/frontend/` file in the diff (confirmed absent in the dev handoff).

**Zero `UT-J-XX` regression cases** — `Required-still-passing journeys:` names no journey as
touched this iteration; the sole `Target journeys:` entry (J-11 Stage C) has no UI surface by
goal.md's own explicit declaration, consistent with the iter-7 (J-10) and iter-11 (J-11) precedent
already established in this project.

**P1 tests must all pass for browser QA verdict to be PASS** — not applicable this iteration; no
browser-QA lane runs (maintenance isolation, ruling A5/A13/C10).
