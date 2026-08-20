# Iteration Summary — goal-market-compass-iter-2
**Verdict:** ESCALATE
**Iteration type:** goal-lean
**Date:** 2026-08-20
**Iteration:** 2

## In plain words

**What you can do now:** On the home page, read a plain-English summary of today's market. See what changed since the previous session. See which stocks are worth watching next, each with a plain reason and an honest note if it almost qualified but didn't. Every stock also shows a real sector label now, not "Unassigned".

**What changed this time:** The home page now has three new sections above the old dashboard. One is a plain-English "Today" summary. One lists what changed since last time. One shows next-session stock picks with reasons and honest "why not" notes for names that didn't make the list. The Methodology page also explains how those picks are chosen.

**What's next:** Next, each night's closing briefing will be locked into a permanent record that can never be quietly changed afterward.

## Headline

Home page now shows a plain-English market summary, what changed, and next-session candidates

## Direction

**Signal:** improving
**Why:** This iteration promoted J-01, J-02, J-03 and J-04 to passing on evidence the evaluator cross-checked itself (screenshot figures matching the pre-existing dashboard tiles), so real product progress happened and nothing regressed. The evaluator still returned ESCALATE rather than CONTINUE because the engine dispatched lean depth against a spec and prior recommendation that both called for full, skipping the auditor, visual-regression, and walkthrough lanes on the session's biggest change yet — which is why all four newly-passing journeys carry an `evidence_makeup` flag. Next iteration must run full depth for J-05/J-06, the riskiest remaining pair.

**Trend (last 3 iters):**
- Newly passing this iter: J-01, J-02, J-03, J-04
- Newly passing in last 3 iters total: J-01, J-02, J-03, J-04
- Regressions in last 3 iters: none
- Anti-goal violations in last 3 iters: 1 MINOR (iter-2, AG-2 — ATR caution reads as advice); no critical violations
- Iters with no journey state change: 1 of last 3 (iter-1)

**Latest evaluator reasoning:** The home page now answers three of the eight questions the goal asks for: a plain-English summary of the market, a list of what changed since the previous session, and a "next-session focus" section that explains why each name was chosen and why twenty others were not. I checked the four pictures myself rather than trusting the write-ups, and the numbers in the new text match the older tiles sitting further down the same page, so the new words are quoting the site's own figures. Nothing that worked before stopped working. I am still returning ESCALATE, because the engine ran this iteration in the light "lean" mode although its own plan asked for the full mode, so the independent auditor, the visual-regression check and the walkthrough recorder never ran — and the developer raised a genuine product question (today no stock passes all three selection rules, so the headline section is honestly empty) that those missing lanes were supposed to settle.

## What was done

- Product changes: apps/backend/app/engine/session_delta.py, apps/backend/app/engine/compass.py, apps/backend/app/api/compass.py (new `GET /api/compass` route), apps/backend/app/models.py, apps/backend/app/config.py, apps/backend/app/engine/data_manager.py, apps/backend/app/engine/methodology.py, apps/backend/app/engine/universe_screen.py, apps/backend/main.py, config.yaml, apps/frontend/app/page.tsx, apps/frontend/app/methodology/page.tsx, apps/frontend/components/compass-summary-card.tsx, apps/frontend/components/compass-whatchanged-card.tsx, apps/frontend/components/compass-focus-section.tsx, apps/frontend/components/ui/disclosure.tsx, apps/frontend/lib/api.ts
- Built new engine producer `app.engine.session_delta.compute_delta` for session-over-session deltas (market/breadth/sector/theme/stock), threshold-gated, with an explicit no-prior-run state; reads column-projected selects only (AG-8).
- Built the narrative sentence builder and `evaluate_selection` candidate-selection trace inside `app.engine.compass`, plus `build_manifest_payload`/`content_hash` assembly over both.
- Added the `next_session_manifests` table and a create-once-on-GET `GET /api/compass` endpoint — computes once, serves from storage on every later hit.
- Wired a new "compass content" phase into the ingest finalize tail, isolated by its own try/except so a producer failure can't block the rest of the tail.
- Added three new home-page cards (Summary, What-changed, Next-session focus) above the unchanged dashboard body, plus a new Methodology disclosure card for the selection rule.
- Fixed the demo/walkthrough recorder's JSON-parse bug (a stray regex literal) and closed two carried housekeeping items (a test-fixture pollution bug, a hoisted per-scan sector set).
- Verified 4 target journeys (J-01, J-02, J-03, J-04) pass browser QA, each cross-checked live against the pre-existing dashboard tiles.

## What's left

- Journey J-05 (Each close freezes one next-session manifest, exported byte-consistently) failing — freeze/versioning/provenance apparatus not yet built, though this iteration's table/endpoint substrate is ready for it.
- Journey J-06 (A frozen manifest never changes) failing — gated on J-05's freeze apparatus.
- Journey J-07 (The Today page answers the ten-second read) failing — page heading, state band, readiness/preflight chrome, leadership-rotation section, and manifest strip still missing.
- Journey J-08 (Market page moves over intact and history stays honest) failing — `/market` still 404, sidebar unchanged.
- Missing `[NEW]` walkthrough recordings for J-01 through J-04 — all four carry an evidence-makeup flag because no demo lane ran at lean depth.
- The auditor and visual-regression lanes did not run this iteration (lean depth dispatched against a full-depth spec) — a process gap the evaluator wants closed by running full depth next time.
- Minor: the ATR caution phrase ("— sized risk accordingly") reads like advice, and the banned-word guard doesn't yet scan candidate reason/caution lines.
- Zero stocks currently clear all three selection qualifiers on the latest date, so the Next-session focus section is honestly empty — an owner decision is pending on whether to accept this or revisit the thresholds.
- Two owner decisions are still open: reword J-01's now-destructive/unexecutable test steps 1 and 2 in `docs/goal.md`.

## Next step

Run the next iteration in full mode and build J-05 "Each close freezes one next-session manifest" together with J-06 "A frozen manifest never changes." These two turn the daily briefing into a sealed, dated, tamper-evident file that can never be altered afterwards — the riskiest part of the whole plan, and the substrate it extends (storage table, endpoint, compute-once path) already landed this iteration.

Carry three small jobs along with it: (1) record the missing walkthroughs for J-01 to J-04 and capture one screenshot of the Risk-off warning state on 2026-03-30; (2) reword the ATR caution so it stops sounding like advice, and extend the banned-word check to the candidate reason/caution lines; (3) fix the cited-fact display so it prints "-0.20" instead of the untidy raw float.

Two things need the owner: approve rewording J-01's first two test steps (step 1's destructive Remove+backfill is unusable offline; step 2's "Unassigned" filter option no longer exists), and decide whether the current empty next-session-focus list on the latest date is acceptable as an honest result or whether the three selection thresholds should be revisited (not because past prices would have looked better — that would break AG-15).

## Assumptions made

- iter-2 · goal-evaluator — Ambiguity: J-01 step 1 (destructive Remove+backfill) wasn't executed and step 2 ("select the Unassigned filter option") is now unexecutable since coverage is 100%; goal.md doesn't say whether a journey can pass when a precondition step is skipped and an assertion step is unexecutable as worded. We chose: Scored J-01 `passing` — the Acceptance block, not the Steps list, is the bar, and every acceptance clause is met with evidence; step 2's intent was met more strongly than its literal wording (the browser lane confirmed the Unassigned option doesn't exist at all). The owner-facing request to reword both steps stays open. Reversible: yes
- iter-2 · goal-evaluator — Ambiguity: J-04 steps 2-6 require opening a candidate card "on the latest as-of," but zero members clear the three-qualifier rule on the latest stored date, so no card exists. goal.md doesn't say which date to use when the frontier date is legitimately empty. We chose: Verified steps 1 and 8 live at the latest as-of (0 candidates, explicit `candidates_empty_reason`) and steps 2-6 at the stored historical as-of 2026-07-23 (1 real candidate, GWW), using genuine stored data rather than a synthetic fixture. Reversible: yes
- iter-2 · goal-evaluator — Ambiguity: J-01 through J-04 each require a `[NEW]`-flagged walkthrough, but the lean-depth run had no demo lane, so none exists for any of the four; goal.md doesn't say whether a missing walkthrough blocks a journey whose behavior is otherwise fully demonstrated by a screenshot. We chose: Scored all four `passing` with `evidence_makeup: true`, the gap recorded as a capture-defect per methodology A.7 — the no-screenshot rail is separately satisfied by each journey's own cited screenshot. The missing recordings ride the next iteration as a passenger task. Reversible: yes
- iter-2 · goal-decomposer — Ambiguity: the blueprint already names `/` as home for J-02/J-03/J-04's new cards, but `/` is still the unmodified legacy Dashboard, and the full Today-page ordering/chrome is J-07's job while relocating the old body to `/market` is J-08's. We chose: Add the three new cards to the existing `/` page above the current unmodified dashboard body, reading only the new `GET /api/compass` endpoint; leave final section ordering, chrome, and the old body's removal to J-07 and J-08. Reversible: yes
- iter-2 · goal-decomposer — Ambiguity: the Data Contract's baseline manifest row combines this iteration's content fields with J-05/J-06's freeze/integrity fields, and goal.md doesn't say which fields this iteration must persist versus which stay unbuilt until the freeze iteration. We chose: Build only the content-computation logic (session delta, narrative, `evaluate_selection`'s candidates/why-not) plus `content_hash`, persisted in a new minimal `next_session_manifests` table; freeze/versioning/provenance/hash/cohort-storage/export stay out of scope for J-05/J-06 to add additively. Reversible: yes
- iter-1 · goal-evaluator — Ambiguity: the browser-QA run permanently destroyed two days of user-added bars/snapshots/forward-returns, recoverable only via a live network fetch that AG-9 forbids; no anti-goal names data destruction directly, and the REGRESSION rule only fires on a passing-to-failing flip or a critical anti-goal violation. We chose: Did not treat the loss as a REGRESSION or an anti-goal violation — the destroyed bars were outside the committed seed and no journey depended on those dates; recorded it as a prominent owner-facing flag plus a binding goal.md-amendment request for J-01 step 1. Reversible: yes
- iter-1 · goal-evaluator — Ambiguity: the browser-QA lane FAILed on J-01 (its precondition died against a stale backend) while the auditor verified the journey's substance live; goal.md doesn't say how to score a journey whose behavior is confirmed live but whose browser-lane capture never reached the acceptance state. We chose: Scored J-01 `partial` with `evidence_makeup: true`, the gap recorded as a capture-defect — not `passing` (no screenshot exists) and not `failing` (the behavior is demonstrably met). The make-up capture rides the next iteration as a passenger task. Reversible: yes
- iter-1 · goal-decomposer — Ambiguity: the agent instructions describe two related but not identical depth=full trigger sets, and neither says how "brand-new full-stack journey" maps onto one of the four numbered metadata triggers. We chose: Cited numbered Trigger 1 (Structural/cross-cutting), grounded in the objective fact that J-01's wiring touches four modules whose combined interaction has no single existing test; Triggers 3 and 4 were checked and don't hold. Reversible: yes
- iter-0 · goal-evaluator — Ambiguity: goal.md says depth=full applies "when an iteration first lands user-visible UI changes," but doesn't say whether J-01 (mostly backend sector wiring plus one changed page) counts as user-visible. We chose: Treated it as user-visible and recommended full depth for iteration 1, since the owner would see different sector labels and new disclosure text on screen, and J-01's byte-identical-scores claim benefits from the audit lane on the session's first product change. Reversible: yes
- iter-0 · goal-evaluator — Ambiguity: J-01's acceptance bundles four things, and goal.md doesn't say how to score a journey where the honesty rails hold but the coverage target is missed by a wide margin. We chose: Scored J-01 `partial` rather than `failing` — some acceptance steps passed with evidence while coverage (78.4% Unassigned vs. the <=5% target) and the methodology disclosure were entirely absent; `partial` is a factual record, not credit toward the deliverable. Reversible: yes

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-market-compass-iter-2.md |
| Dev handoff | — | docs/handoffs/goal-market-compass-iter-2-dev.md |
| Review | PASS_WITH_NOTES | reports/reviews/goal-market-compass-iter-2-review.md |
| Browser QA | PASS | reports/phase-goal-market-compass-iter-2-ui-test-results.md |
| Goal evaluation | ESCALATE | runs/goal-session-market-compass/iter-2/eval.md |
| Journey history | — | runs/goal-session-market-compass/state/journey-history.json |
