# Iteration Summary — goal-market-compass-iter-12

**Verdict:** STALLED
**Iteration type:** goal-full
**Date:** 2026-08-24
**Iteration:** 12

## In plain words

**What you can do now:** See an honest, nearly-complete sector label for every stock (no more "Unassigned" guesswork), read why each next-session candidate was picked and why the others were not, and trust that the two trading days lost in the August data incident (11 and 12 August) are permanently back in the price history.

**What changed this time:** Nothing changed on any page a user sees. Behind the scenes, the internal tool that changes the database's structure was fixed so it can never again quietly drop settings or reorder a column the way it did last round. The "can this saved briefing be trusted?" check was made stricter — it now honestly says "can't verify" instead of ever wrongly claiming a briefing checks out when it has no proof. An inaccurate internal note about the database was also corrected. All of this is safety and cleanup work getting the ground ready for the bigger repair still to come.

**What's next:** The team needs one word from the owner: go, or not yet. Every safety condition for the big repair — rebuilding the daily-summary pages using the two restored trading days — now checks out. Once the owner says go, that rebuild is the next piece of work.

## Headline

J-11 Stage B1 cleanup: migration tool fixed for future safety, basis-disclosure fail-open closed

## Direction

**Signal:** stalling
**Why:** No journey was newly promoted this iteration and none regressed — J-10 and J-11 were both re-derived read-only and stay at their prior status, and the owner's acceptance of iter-11's DDL residual closed the session's only unresolved anti-goal item without erasing iter-11's REGRESSION verdict. Two journeys (J-07, J-08) remain failing and cannot be worked on because `docs/goal.md`'s Loop-mechanics gate shuts every lane except J-11 until Stage G passes, and the evaluator halted for the third consecutive full-depth iteration on the same structural blocker: Stage C (the destructive rebuild) is technically ready but requires an explicit owner "go" that has not yet been given.

**Trend (last 3 iters):**
- Newly passing this iter: none
- Newly passing in last 3 iters total: none
- Regressions in last 3 iters: iter-11 (AG-18 — authorized schema migration exceeded its scope; stored values unaffected)
- Anti-goal violations in last 3 iters: 1 critical (AG-18, raised iter-11; resolved iter-12 by explicit owner acceptance, not by repair)
- Iters with no journey state change: 2 of last 3 (iter-11, iter-12 — iter-10 advanced J-11 unknown→partial)

**Latest evaluator reasoning:** This iteration did the four small clean-up jobs the owner asked for, and it did them without touching the real database even once. I am halting anyway. Nothing is broken and nothing is missing — the next step is the destructive rebuild of eleven days of derived data, and the owner's own written rule says that step may only start on the owner's explicit say-so.

## What was done

- Product changes: apps/backend/app/engine/j11_schema_migration.py, apps/backend/app/engine/compass.py, apps/backend/app/models.py, apps/backend/scripts/run_j11_stage_b1_manifest_schema_migration.py, apps/backend/scripts/run_j11_stage_b1_cleanup_fingerprint.py, apps/backend/scripts/run_j11_stage_b1_cleanup_fingerprint_diff.py, apps/backend/scripts/run_j11_stage_b1_live_reverification.py
- Fixed the J-11 schema-migration utility so any future rebuild derives the replacement table from captured live DDL text (never ORM metadata) and fails closed if the target FK clause can't be found exactly — proven only on fixture databases, never run against the live database.
- Closed `basis_disclosure`'s A4-bis fail-open on null/empty/unparseable recorded timestamps — these now return "unverifiable" instead of silently claiming "available".
- Corrected `models.py`'s false claim that the live table matches its model declaration exactly; the comment now names the four owner-accepted residual differences from iteration 11.
- Statically re-confirmed the `preFreezeEra` UI branch is honest (asserts no basis status at all) — filed as a Stage G item, no frontend code touched.
- Proved zero live-database writes via read-only before/after fingerprinting across every table; ran 107 targeted tests, 0 failures.
- Independently re-derived all 13 items of ruling A12's Stage C readiness checklist against the live database; the evaluator's own answer: J-11 STAGE C READY: YES.

## What's left

- Journey J-07 ("The Today page answers the ten-second read") failing — never verified passing, unchanged since iteration 0.
- Journey J-08 ("Market page moves over intact and history stays honest") failing — never verified passing since iteration 1; the `/market` route doesn't exist yet.
- J-11 Stages C–G (the destructive clear-and-rebuild of 11 days of derived results) not started — blocked solely on an explicit owner go/no-go instruction, not on any remaining engineering work.
- Journeys J-02, J-03, J-05, J-06, J-09 remain only "partial" — all await J-11 Stage G's rebuild and the reopened browser lane before they can be re-tested.
- Non-blocking precondition for any future live migration run: the tool's row-copy and equality-proof steps still read the ORM model's column list rather than the real table's, so an undeclared future column could be silently dropped and unverified (cannot fire on today's table; flagged by the auditor for before, not after, any next live run).
- A pre-existing, unrelated test failure (`test_no_magic_numbers.py`, on literals in `indicators.py`/`forward_testing.py`/`research.py`) remains outstanding — not introduced this iteration, out of scope.
- Five older owner questions remain open and non-blocking: whether 3.44 GB is acceptable for J-09; J-06's "underlying run unavailable" wording; the rewording of J-01's first two test steps; whether an empty "next-session focus" is acceptable; and whether MNST joins the recovery list.

## Next step

One word is needed from the owner: go, or not yet. Every safety condition for Stage C is met and was independently re-verified against the live database this iteration. Pick one: (a) instruct the engine to start Stage C and resume — the readiness answer is YES; (b) ask first that the migration tool's column-list blind spot (audit finding B1) be closed before any future live run — it cannot cause harm today, but the owner may prefer it fixed before rather than after; or (c) change the plan in `docs/goal.md`. Once authorized, the next iteration is J-11 Stages C through G at full depth, alone — one writer, no web server, no browser tests — carrying forward the AVB volume-scale caveat, the ban on re-running the recovery script, the ban on running the table-rebuild tool against the live database, and re-freezing the attempt identity at the start of the attempt.

## Assumptions made

- iter-12 · goal-evaluator — Ambiguity: The dispatching framing pairs STALLED with "a concrete unresolved prerequisite remains," but every one of ruling A12's 13 readiness items holds this iteration — which reads like CONTINUE on the surface, yet the decision tree's human-owned-blocker clause sits above CONTINUE. We chose: STALLED — ruling A12 itself ends with an explicit human gate ("Stage C... waits for an explicit owner instruction to resume"); CONTINUE would let the engine decompose an iteration that could only be the irreversible destructive clear, without that sanction, and no other lane is legally available meanwhile. Reversible: yes — one dated owner line or instruction plus resume continues the session with nothing repaired, nothing lost, no status changed.
- iter-12 · goal-evaluator — Ambiguity: The ledger's `resolved` flag has only one precedent (iter-8), set after damage was undone byte-for-byte; here the iter-11 DDL residual is accepted by the owner but never repaired, and `docs/goal.md` doesn't say whether an accepted-but-unrepaired breach counts as resolved. We chose: `resolved: true`, with severity, iteration and the full original evidence preserved verbatim plus the owner's acceptance appended — leaving it `false` would force a second REGRESSION halt for a decision already made, and nothing is softened: iteration 11's REGRESSION verdict itself stays untouched. Reversible: yes — one boolean, full evidence retained, can be flipped back at no cost.
- iter-12 · goal-decomposer — Ambiguity: Owner ruling A11(a) leaves open whether the `preFreezeEra` UI branch is honest or fail-open, and `docs/goal.md` doesn't state the answer or the overlap between its trigger and the population the A4-bis fix targets. We chose: ran read-only queries confirming a complete 8/8 overlap and read the component source confirming the branch never renders a basis-status claim — recorded as honest, filed as a Stage G item, no frontend code touched; the developer/reviewer are instructed to independently re-derive this rather than trust the entry. Reversible: yes — if a later re-derivation disagrees, the spec requires stopping and surfacing the exact contradiction rather than proceeding silently.
- iter-11 · goal-evaluator — Ambiguity: J-10's goal text changed (spec-hash drift flagged); maintenance isolation forbids any browser lane or promotion this iteration, but `docs/goal.md` waives J-10's walkthrough entirely and names written/database evidence as its substitute. We chose: kept J-10 `passing` and re-stamped the new hash on read-only live-database evidence produced this iteration — not a promotion, since status is unchanged, and the waived walkthrough means no screenshot could ever apply. Reversible: yes — J-11 Stage G is the first legal verification lane and can re-score J-10 there at no cost.
- iter-11 · goal-evaluator — Ambiguity: The iter-11 schema migration exceeded its owner authorization (dropped 3 DEFAULTs, moved a column) but preserved every stored value exactly; the decision tree's REGRESSION trigger is a changed stored value (none changed here), while STALLED's "stop and surface as owner decision" shape also fits. We chose: REGRESSION, under the fail-closed rule for an uncertain critical classification — the violated state is still materialized on the live database and unreversed without a second authorization, and the very next step is the same class of destructive action that permanently lost data in iteration 5. Reversible: yes — if the owner reads the deviation as within authorization, a dated line plus acknowledge-regression resumes with nothing repaired or lost, and the ledger can later be marked resolved.
- iter-11 · goal-decomposer — Ambiguity: Owner ruling A4 requires `basis_disclosure`'s UI half (the honest "unverifiable" placeholder) as part of the Stage C precondition, but ruling A5 keeps maintenance isolation active (no app boot, no browser) for the whole iteration, and `docs/goal.md` doesn't say whether the UI half must land this iteration or can wait for Stage G. We chose: landed the minimal type/label change (a status union plus a pure label function), verified only by type-checking and a no-boot node-script test — satisfies A4 without violating A5; no page render or browser evidence claimed. Reversible: yes — a one-line edit to a type union/label map if it ever needs to change; nothing stored depends on it.
- iter-10 · goal-evaluator — Ambiguity: Real progress was made (J-11 unknown→partial) and three engineering follow-ups exist, which reads CONTINUE on the decision tree's surface — but the headline follow-up routes to Stage C/D/G, and `docs/goal.md`'s Loop-mechanics gate shuts every other lane until J-11 Stage G passes. We chose: STALLED — the blocker that matters is Stage C's precondition gate, and all three of its unblock paths are owner decisions (two irreversible-write class); `docs/goal.md` itself prescribes "STOP before J-11 and surface it as an owner decision," and scheduling a passenger-sized engineering fix instead would be motion without moving the blocker. Reversible: yes — the owner can answer with one dated line and resume; nothing here forecloses CONTINUE if the owner prefers the follow-ups land first.
- iter-10 · goal-evaluator — Ambiguity: J-11 spans Stages A–G; this iteration delivered B and B2 in full and B1 only partly (two of six Stage C precondition items false on the live database), and the methodology's status vocabulary offers only `unknown`/`partial` for this case, with the spec itself hedging it should stay "at least partial/unknown." We chose: `partial`, stamped with the current goal-text hash — the pre-reset inventory is one of the substitute-evidence items `docs/goal.md` itself names for this journey, it exists, and every load-bearing figure was re-derived from the live database read-only; `unknown` would have understated a measured, contractually-required artifact. Reversible: yes — nothing mechanical turns on it, and the Stage C/D/G iteration re-measures J-11 end to end.

## Quick verify

From `reports/phase-goal-market-compass-iter-12-what-to-click.md`:

1. Open `http://localhost:3255/` in your browser
2. Scroll down to the "Manifest" card and read its top badge row
3. Scroll to the "Next-session focus" card
4. Navigate to `http://localhost:3255/?asof=2020-03-20`
5. Navigate to `http://localhost:3255/?asof=2026-08-10`

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-market-compass-iter-12.md |
| Dev handoff | — | docs/handoffs/goal-market-compass-iter-12-dev.md |
| Review | PASS | reports/reviews/goal-market-compass-iter-12-review.md |
| Browser QA | SKIPPED | reports/phase-goal-market-compass-iter-12-ui-test-results.md |
| Implementation summary | — | reports/phase-goal-market-compass-iter-12-implementation-summary.md |
| User-visible changes | — | reports/phase-goal-market-compass-iter-12-user-visible-changes.md |
| What to click | — | reports/phase-goal-market-compass-iter-12-what-to-click.md |
| UI surface map | — | reports/phase-goal-market-compass-iter-12-ui-surface-map.md |
| UI test plan | — | reports/phase-goal-market-compass-iter-12-ui-test-plan.md |
| QA | PASS | reports/qa/goal-market-compass-iter-12-qa.md |
| Audit | PASS_WITH_GAPS | docs/handoffs/goal-market-compass-iter-12-audit.md |
| Closure | CLOSURE-PASS | reports/phase-goal-market-compass-iter-12-closure-verdict.md |
| Goal evaluation | STALLED | runs/goal-session-market-compass/iter-12/eval.md |
| Journey history | — | runs/goal-session-market-compass/state/journey-history.json |
