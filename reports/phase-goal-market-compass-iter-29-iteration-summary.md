# Iteration Summary — goal-market-compass-iter-29

**Verdict:** ESCALATE
**Iteration type:** goal-full
**Date:** 2026-09-01
**Iteration:** 29

## In plain words

**What you can do now:** See each stock's honest, mostly-complete sector label; see why each next-session candidate was picked and why others weren't; trust that each evening's saved briefing exactly matches what's on screen and never changes once saved; see the app honestly report when an old briefing's underlying data has gone missing instead of quietly rebuilding it; browse the two recovered trading days with corrected numbers, backed by checked-live repair work; read the reordered "Today" page (market state, summary, what changed, next-session focus) on one screen; and reach the full former dashboard, unchanged, on the "Market" page. On one specific date, August 3rd 2026, you can also read plain words saying whether the market was improving or getting worse that day.

**What changed this time:** On the Today page, looking up August 3rd, 2026 specifically now shows three real market-direction words ("improving", "improving", "little changed") next to the Regime, Market phase, and Breadth figures, instead of the placeholder "NA" — and the sentence in the Summary card just below agrees with them. Every other date, including today's own latest briefing (August 12th, 2026), still shows "NA" for those three words.

**What's next:** Next, the team plans to give today's own latest briefing those same real direction words too — right now they only show up on that one practice date, not on the page most people actually open.

## Headline

Make J-07's direction words observable on real data

## Direction

**Signal:** holding
**Why:** J-07 ("The Today page answers the ten-second read") made real, verified progress this iteration — the three direction badges now show correct words on one live date (2026-08-03), matching the Summary card's sentence — but it stayed at `partial` because the default landing page at the latest date (2026-08-12) still reads "NA". No journey passed, failed, or regressed: the seven already-passing journeys (J-01, J-04, J-05, J-06, J-08, J-10, J-11) all re-verified clean via 8/8 deterministic replay, and the anti-goal ledger held at 9 total, 0 unresolved.

**Trend (last 3 iters):**
- Newly passing this iter: none
- Newly passing in last 3 iters total: J-06 (iter-27), J-08 (iter-28)
- Regressions in last 3 iters: none
- Anti-goal violations in last 3 iters: 1 minor (iter-27 — an unauthorized as-of call minted a benign extra manifest row; resolved, no enumerated anti-goal breached); none new in iter-28 or iter-29
- Iters with no journey state change: 1 of last 3 (iter-29)

**Latest evaluator reasoning:** The one job this round was asked to do was done, and done well. One allowed request created a saved daily briefing for 3 August 2026, and on that date the Today page now says in plain words whether things are improving or getting worse — "improving", "improving", "little changed" — and the sentence just below it agrees. But the journey is still not finished: on the page a user actually lands on, all three words still read "NA" while the sentence one line below reports a real change, so J-07 stays open for one more small piece of work.

## What was done

- Product changes: No product change this iteration.
- Started the canonical backend/frontend and issued exactly one authorized `GET /api/compass?as_of=2026-08-03`, minting `next_session_manifests` row id=27 (version 1, retrospective, prospective_eligible=0) carrying real state-band words instead of blanks.
- Re-derived AG-12 byte-identity across all 26 pre-existing manifest rows after every lane finished (dev, replay, browser-qa) — confirmed unchanged.
- Re-ran targeted backend suites: `test_manifest_invariants.py` (51 passed), `test_compass.py` + `test_api_compass.py` (54 passed, includes the 11 state-band tests), `test_no_magic_numbers.py` (1 passed, 1 pre-existing unrelated failure).
- Auditor closed the cross-lane `as_of` ledger (TC-6), flagging 3 out-of-set replay-lane dates that turned out harmless, and wrote an honest per-step coverage table for J-07 replacing an overstated "all 7 steps verified live" claim.
- Verified 15/15 browser QA journeys pass (0 skipped); J-07's step 3 confirmed live on 2026-08-03, but the default landing view (2026-08-12) still shows "NA".

## What's left

- Journey J-07 ("The Today page answers the ten-second read") partial — the default landing view at the latest date (2026-08-12) still shows "NA" on all three direction badges while the Summary sentence directly below reports a real change.
- Journey J-02 ("What changed since the previous session") partial — carried unchanged since iteration 6, not re-examined.
- Journey J-03 ("Plain-English summary with cited facts") partial — carried unchanged since iteration 6, not re-examined.
- Journey J-09 ("The backend fits the host") partial — standing memory-budget miss (+16.9% over target), not targeted this iteration.
- No durable browser regression guard exists yet for the three direction badges — the new replay-test step checks the wrong sentence (the narrative, not the badges) and never actually executed this iteration.
- A pre-existing red test (`test_no_magic_numbers.py`) covering three older engine files (`indicators.py`, `forward_testing.py`, `research.py`) needs fixing or a formal waiver.
- Recorded walkthroughs are still owed for J-05, J-06, J-07, and J-08; the J-04 screenshot retake is still owed (11th round running).

## Next step

FINISH J-07 "The Today page answers the ten-second read" — make the three direction words appear on the page a person actually lands on. The proven approach is to mint a new version of the frontier date's (2026-08-12) saved briefing through the same confirm-gated regenerate path already used successfully at iteration 26, leaving the older versions untouched and keeping the new one marked as not usable as forward-looking evidence. The next plan must name that one date and permit no other, and must re-check the briefing table after every lane finishes, exactly as this round did. Run it at full depth — only an ESCALATE verdict has reliably held full depth for database-mutating specs this session. One owner question could close J-07 immediately: if showing the words correctly on one real date is enough, and "NA" on the frontier landing view is acceptable because the data set has no newer trading day, then J-07 is finished today.

## Assumptions made

- iter-29 · goal-evaluator — Ambiguity: J-07's real words now render on `2026-08-03`, but the default `/` (no `asof`) still shows "NA" on all three badges, and the journey text doesn't name which as-of date step 3 must be demonstrated on. We chose: hold J-07 at `partial`, not `passing` — `docs/goal.md`'s Success Criteria require direction to be readable "from `/` alone," `state_band_json` is non-null on only 1 of 27 rows, and the gap is producible (not permanently unprovable) via one more confirm-gated regenerate mint. Reversible: yes — one owner line accepting the current evidence would promote J-07 to passing immediately.
- iter-29 · goal-decomposer — Ambiguity: which date to use for the one authorized live mint that would make J-07's `state_band` words observable; goal.md doesn't name one. We chose: `2026-08-03` — it has a real stored scanner run and a prior run for comparison, carries zero existing manifest rows, sits outside the incident window and the AG-9 dated-exception list, and resolves normally (well before the data frontier). Reversible: yes for the date choice; the minted row itself is permanent (create-once).
- iter-28 · goal-evaluator — Ambiguity: whether J-08 step 4's "version-1 stamps" wording is literal or shorthand for "that date's own frozen manifest," since the frontier date's real version 1 predates the freeze feature and can never be re-minted. We chose: read it as shorthand and promote J-08 to `passing` on the substantive acceptance (provenance stamps, correct lineage) it did meet. Reversible: yes — if the owner rules version 1 literal, J-08 returns to `partial` permanently unless a new trading day is authorized.
- iter-28 · goal-evaluator — Ambiguity: whether J-07 step 3 is satisfied when a served field and its display both honestly read "NA," given two earlier journeys (J-05, J-06) were closed on similar fixture-only evidence. We chose: hold J-07 at `partial` — unlike those two, this gap is producible with one authorized live GET rather than permanently unprovable, so holding it open is a task, not an unsatisfiable-criterion loop. Reversible: yes — one owner line would promote it immediately.
- iter-28 · goal-decomposer — Ambiguity: whether adding a nullable `state_band_json` column to the protected `next_session_manifests` table counts as prohibited AG-18 schema drift or ordinary authorized additive work. We chose: authorized/ordinary — every AG-18 protection held (no row regenerated, rebound, rehashed, deleted, or backfilled) and the column uses the same additive mechanism prior columns on this table already used. Reversible: no for the column itself (permanent in practice); reversible for the policy going forward.
- iter-28 · goal-decomposer — Ambiguity: whether the new `state_band` direction words belong frozen inside the immutable manifest content (computed once at write) or should be computed fresh at read time from live endpoints. We chose: freeze inside `build_manifest_payload`, matching every other derived field's contract and keeping historical reads reproducible. Reversible: yes — an implementation-placement call; nothing depends on it being frozen.
- iter-28 · goal-decomposer — Ambiguity: whether "leadership rotation" (one of J-07's six body sections) needed its own distinct computation or could reuse `session_delta`'s already-served `changes` array. We chose: present it as a client-filtered view of the same already-served data (narrowed to sector/theme/stock kinds), avoiding a second producer for the same value. Reversible: yes — a scoping call with no data-model impact.

## Quick verify

From `reports/phase-goal-market-compass-iter-29-what-to-click.md`:

1. Open `http://localhost:3255` in your browser
2. In the top bar, click the "Latest" pill button (clock icon, next to the arrows)
3. Click the day cell numbered "3" in the calendar popover (should already be showing August 2026)
4. Look at the "Market state" card and read the three pill badges next to Regime, Market phase, and Breadth
5. Scroll down slightly to the "Summary" card and read its first sentence

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-market-compass-iter-29.md |
| Dev handoff | — | docs/handoffs/goal-market-compass-iter-29-dev.md |
| Review | PASS_WITH_NOTES | reports/reviews/goal-market-compass-iter-29-review.md |
| Browser QA | PASS | reports/phase-goal-market-compass-iter-29-ui-test-results.md |
| Implementation summary | — | reports/phase-goal-market-compass-iter-29-implementation-summary.md |
| User-visible changes | — | reports/phase-goal-market-compass-iter-29-user-visible-changes.md |
| What to click | — | reports/phase-goal-market-compass-iter-29-what-to-click.md |
| UI surface map | — | reports/phase-goal-market-compass-iter-29-ui-surface-map.md |
| UI test plan | — | reports/phase-goal-market-compass-iter-29-ui-test-plan.md |
| UX regression | UX-REGRESSION-SKIPPED | reports/phase-goal-market-compass-iter-29-ux-regression.md |
| QA | PASS | reports/qa/goal-market-compass-iter-29-qa.md |
| Audit | PASS_WITH_GAPS | docs/handoffs/goal-market-compass-iter-29-audit.md |
| Closure | CLOSURE-PASS | reports/phase-goal-market-compass-iter-29-closure-verdict.md |
| Goal evaluation | ESCALATE | runs/goal-session-market-compass/iter-29/eval.md |
| Journey history | — | runs/goal-session-market-compass/state/journey-history.json |
