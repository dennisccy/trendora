# Iteration Summary — goal-market-compass-iter-26

**Verdict:** ESCALATE
**Iteration type:** goal-lean
**Date:** 2026-08-28
**Iteration:** 26

## In plain words

**What you can do now:** See each stock's honest, mostly-complete sector label. See why each next-session candidate was picked, and why the others weren't. Browse the two recovered trading days, with corrected price data, in the price history. Trust that the data-recovery work behind the app has been checked and holds up. And now, trust that each evening's saved briefing file is an exact, byte-for-byte copy of what the page shows you.

**What changed this time:** Behind-the-scenes work — nothing new appears on screen this round. The team tightened the safety tests behind the evening-briefing feature and confirmed, using the app's existing controls, that a saved briefing file exactly matches what the page shows, and that making a corrected copy of an old briefing leaves the original completely untouched.

**What's next:** Next: teach the app to honestly say when the data behind an old frozen briefing has gone missing, instead of quietly rebuilding it — reviewed extra carefully next round since it touches code every page uses.

## Headline

The iteration did what it promised, and I checked the important parts myself instead of trusting the write-ups.

## Direction

**Signal:** improving
**Why:** J-05 ("each close freezes one next-session manifest, exported byte-consistently") moved from `partial` to `passing` this iteration, with three of its four proof limbs re-derived live by the evaluator against the real database. J-06 ("a frozen manifest never changes") stays `partial` on a real product bug: `apps/backend/app/api/compass.py:59` recomputes a missing scan run before the honesty check can see it's gone. Verdict is ESCALATE, not because anything broke, but because the planned full-depth review was demoted to lean for the sixth time this session, leaving no independent auditor or QA lane for the one live write to the protected database this round.

**Trend (last 3 iters):**
- Newly passing this iter: J-05
- Newly passing in last 3 iters total: J-05
- Regressions in last 3 iters: none
- Anti-goal violations in last 3 iters: none
- Iters with no journey state change: 2 of last 3

**Latest evaluator reasoning:** The iteration did what it promised, and I checked the important parts myself instead of trusting the write-ups. J-06 "A frozen manifest never changes" made large progress but stays partial for one honest reason: the app can never tell a user that the underlying run behind a frozen briefing has gone missing, because opening the page quietly rebuilds that run first. I am escalating so the next round runs with the deeper checks, because fixing that touches the code path every page uses.

## What was done

- No product change this iteration.
- Fixed a genuine, newly-found test bug: the manifest-update safety scanner was false-flagging unrelated dict/hash `.update()` calls in 5 files; narrowed it and added a mutation-kill test proving it still catches real UPDATE statements against the manifest table (TC-1).
- Added an automated test proving the evening briefing's saved export file is byte-identical to the served payload and its embedded verification hash reproduces (TC-2).
- Added route-level test coverage proving `GET /api/compass` never crashes or 404s when the underlying scan run is missing, and that the frozen manifest's bytes survive unchanged across a run removal/restore (TC-8/TC-9).
- Investigated four orphaned leftover export files and confirmed, read-only, they are harmless pre-existing test artifacts with no matching database row, not a data-integrity concern (TC-10).
- Re-derived live, read-only, that the evening briefing's saved file matches the served page byte-for-byte (355,711 bytes) and that the older frozen version stayed byte-identical after a new version was minted.
- Triggered the app's existing confirm-gated "Regenerate manifest" control live for the first time this session, adding exactly one authorized database row; confirmed no other table moved.
- Verified 6/6 target and regression journeys (sector labels, candidate reasons, recovered trading days, incident recovery, briefing freeze, briefing immutability) pass browser QA.

## What's left

- Journey J-07 (The Today page answers the ten-second read) failing.
- Journey J-08 (Market page moves over intact and history stays honest) failing.
- Journey J-06 (A frozen manifest never changes) partial — `apps/backend/app/api/compass.py:59` recomputes a missing scan run before the honesty check can see it's gone, so the "unavailable" basis message can never reach a live page. Named as next iteration's target.
- Journey J-09 (The backend fits the host) partial — standing memory re-measured at ~3.06 GB against a 2.5 GB target (16.9% over); honest miss, open owner question on acceptability.
- Journeys J-02 (What changed since the previous session) and J-03 (Plain-English summary with cited facts) stay partial, not targeted this iteration.
- Known test-coverage gap: the manifest-update safety scanner only recognizes the literal name `update` and only scans `app/engine/` — an aliased import could slip past undetected (reviewer MINOR).
- J-05 and J-06 both still owe a recorded walkthrough video (passenger task).
- J-04's screenshot capture still stops above the candidate card — needs re-taking, 8th consecutive iteration owed.
- This iteration ran at lean depth despite the spec requesting full depth (sixth demotion this session) — no independent auditor or QA agent reviewed the one live write to the protected database this round.

## Next step

Close Journey J-06 "A frozen manifest never changes": when someone opens a page for an old date, the app must first notice whether the run behind the frozen briefing still exists and say so honestly, instead of quietly rebuilding it — a small, well-understood change. Run the next iteration at full depth: this one was planned as full and downgraded to lean for the sixth time this session, so no independent auditor or QA lane reviewed the one live write to the protected database; only the owner can add the "Depth enforcement: required" line that would force it (standing guidance keeps `CHAIN_REQUIRE_FULL_DEPTH` and `CHAIN_MAINTENANCE_ISOLATION` off). After J-06, the goal file's own order gives Journey J-07 (the Today page's ten-second read) and Journey J-08 (Market page move) as the last two pieces.

## Assumptions made

- iter-26 · goal-evaluator — Ambiguity: owner ruling item 5 says no further authorization is needed for "ordinary non-destructive product iterations," while item 6 requires owner approval for "immutable-manifest mutation... or another genuinely irreversible product-contract decision"; a permanent additive row isn't clearly one or the other. We chose: read the confirm-gated regenerate write as authorized — verified read-only that nothing was mutated/deleted, AG-12 names new version rows as the sanctioned correction mechanism, and J-06's own step 4 instructs triggering the regenerate action. Reversible: no for the row itself (permanent by design); yes for the policy going forward.
- iter-26 · goal-evaluator — Ambiguity: J-05 step 2 requires a live "at_ingest / version 1 / prospective_eligible true" state that can never be observed again on this database (the frontier's version 1 is a legacy pre-freeze row; later versions were regenerated during the incident and are correctly ineligible; no new trading day can arrive). We chose: promote J-05 to passing, scoring step 2 from route-level fixture evidence while scoring the other steps from live evidence re-derived read-only. Reversible: yes — a scoring-interpretation call with no mutation; if the owner rules a live observation is required regardless, J-05 returns to partial until new market data arrives.
- iter-26 · goal-decomposer — Ambiguity: J-05 step 1 / J-06 steps 1-3 literally instruct removing "the last two trading days," which today resolves to the exact two dates whose removal caused this session's core incident, with the recovery exception now exhausted. We chose: do not call remove_data()/backfill against the canonical database this iteration; prove the destructive-drill portions against the isolated fixture suite instead, and use only safe additive live actions (a read-only manifest render and the confirm-gated regenerate action) for real browser evidence. Reversible: yes for the scoping choice; the one non-reversible piece is narrow and intentional — the live regenerate call mints a permanent version-2 row by design.
- iter-25 · goal-evaluator — Ambiguity: a QA flag says an iteration must never show a clean headline while a target journey has no browser-test row, but J-09's own acceptance text waives the walkthrough requirement in favor of a measurement citation. We chose: treat the goal's own waiver as authoritative and score J-09 from the measurement evidence, not as unknown. Reversible: yes — if the owner rules every target journey needs a browser row regardless, J-09 drops to unknown and a future iteration adds one; the measurement evidence would not need redoing.
- iter-25 · goal-evaluator — Ambiguity: an earlier owner passage says the canonical database "remains OFF and protected," while a later owner ruling says normal product work resumes and needs no further authorization — this iteration booted the canonical database and served ~2,614 read requests, and the two passages could be read as conflicting. We chose: read the earlier passage as spent and scoped to a task that already completed, so the later ruling governs, and verified read-only that the boot touched nothing in the categories still reserved for owner approval. Reversible: yes — nothing was mutated by this reading; if the owner rules the database should stay off regardless, the remedy is to re-arm an isolated clone for future lanes.
- iter-25 · goal-decomposer — Ambiguity: J-09's steps completed at iter-4 with a recorded honest miss and a stop-for-owner-review instruction; it wasn't stated whether that closes J-09's work until the owner rules, or whether the database changing materially since then justifies a fresh re-measurement without waiting. We chose: treat it as fresh re-verification work — re-run J-09's measurement steps against the current database and record a new dated addendum, without waiting on the open acceptability question. Reversible: yes — pure measurement, no mutation; if the owner rules the earlier result was already sufficient, the fresh figure is simply corroborating evidence, not rework.
- iter-24 · goal-evaluator — Ambiguity: the owner appended a new ruling inside J-11's own goal-text block, changing its recorded hash; it wasn't stated whether any text edit inside a journey block demands fresh browser evidence regardless of the edit's content. We chose: re-verify against the current text as a documentary and state-integrity check rather than a fresh browser pass, since the edit was a purely additive ruling with no new or tightened acceptance criterion and the certified state was byte-intact. Reversible: yes — nothing was mutated by this reading; if the owner rules that any goal-text edit demands fresh browser evidence, J-11 drops to unknown and the next browser iteration re-runs the same check.

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-market-compass-iter-26.md |
| Dev handoff | — | docs/handoffs/goal-market-compass-iter-26-dev.md |
| Review | PASS_WITH_NOTES | reports/reviews/goal-market-compass-iter-26-review.md |
| Browser QA | PASS | reports/phase-goal-market-compass-iter-26-ui-test-results.md |
| Goal evaluation | ESCALATE | runs/goal-session-market-compass/iter-26/eval.md |
| Journey history | — | runs/goal-session-market-compass/state/journey-history.json |
