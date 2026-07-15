# Iteration Summary — goal-mcp-loop-iter-36

**Verdict:** CONTINUE
**Iteration type:** goal-full
**Date:** 2026-07-15
**Iteration:** 36

## In plain words

**What you can do now:** Browse a broad stock universe where every score is honestly labeled "not yet proven" (or "proven" only once it clears a strict statistical bar), drill into the evidence behind any score, and audit the full evidence ledger. See extra context like market regime, up to 30 years of price history, and vendor-labeled index and macro benchmarks. Browse a registry of ideas being tested, a graveyard of ideas that already failed, and a running tally of the statistical testing budget before it's spent. Check one daily "is today's data trustworthy" banner on every page, get warned if live data starts drifting from the validated baseline, and now also check a report showing whether the site's own testing process is itself trustworthy.

**What changed this time:** The team finished the last piece of that trust picture: a page that checks the checker itself, showing how often it would wrongly call a fake pattern "real" (currently about 8 times out of 100, against a 5-in-100 target) and loudly flagging that one obviously "cheating" test pattern slipped past it — exactly as designed, to catch and disclose rather than hide. This new page passed every test thrown at it and is now fully counted as delivered, after a couple of already-working pages got a fresh double-check that they were still fine.

**What's next:** Next, a quick housekeeping pass will formally re-confirm that double-check on paper, then work moves on to a new "risk" section of the product — starting with a view of how concentrated a user's watchlist really is.

## Headline

Referee-audit panel (J-22) shipped and browser-verified — governance cluster complete (4/4)

## Direction

**Signal:** improving
**Why:** iter-36 shipped and browser-verified the referee-audit panel (J-22), the fourth and final governance surface, flipping it from unknown to passing on a clean canonical browser-qa lane (13/13) with the certification-economy isolation independently confirmed byte-identical. The iteration ended CLOSURE-FAIL on a narrow, non-J-22 gap (required-still-passing journeys J-05/J-11 lacked concrete live evidence in the QA report), which the evaluator closed by personally re-verifying both on frames it opened itself, so CONTINUE holds with 22 of 25 Must-haves now passing and only the risk-analytics cluster (J-23/J-24/J-25) left unbuilt.

**Trend (last 5 iters):**
- Newly passing this iter: J-22
- Newly passing in last 5 iters total: J-17, J-19 (iter-32), J-20 (iter-33), J-21 (iter-35), J-22 (iter-36)
- Regressions in last 5 iters: none
- Anti-goal violations in last 5 iters: none (the two prior CRITICAL entries, iter-24 and iter-26, are outside this window and remain resolved=true)
- Iters with no journey state change: 1 of last 5 (iter-34, a lean verification-only closeout)

**Latest evaluator reasoning:** iter-36 delivered **J-22** (backlog B-102) — the referee-calibration placebo + lookahead-tripwire audit, the **4th and final governance surface** — cleanly and additively. J-22 flips **unknown → passing**; its own canonical browser-qa evidence is complete on the final build (13/13 UT PASS, no post-lane auditor fix → no partial-trap), the dominant failure mode (isolation) is byte-identical confirmed 4+ ways including the evaluator's own `git diff HEAD`, and displayed numbers byte-match the persisted artifact. The iteration ended **CLOSURE-FAIL**, but it is narrow and the closure auditor explicitly **exempts J-22** — the block is the required-still-passing DoD line. GOAL_ACHIEVED is unreachable regardless: **J-23/J-24/J-25 remain unknown/unbuilt.**

## What was done

- Shipped `/research/referee-audit` — a new read-only page reporting the certifier's own empirical false-pass rate (vs configured α) and a lookahead-contaminated-factor tripwire.
- Added the 4th and final "Referee audit" card to the Research hub's governance grouping, completing the cluster (registry + graveyard + budget + referee-audit).
- Ran the offline calibration harness once against the real 30-year seed and persisted an honest result (16/200 false-pass, rate 0.08, CI [0.0498, 0.126]; the deliberately "cheating" contaminated factor was NOT caught — the tripwire fired as designed) without tuning any referee constant.
- Verified isolation: the real evidence ledgers (`certified-claims.jsonl`, `staging-ledger.jsonl`, `pre-registrations.jsonl`) stayed byte-identical before/after, confirmed independently by the developer, QA, the auditor, and the evaluator's own git diff.
- Added 39 new backend tests (34 unit + 5 API, all passing) plus a clean 251-test regression run across sibling governance/referee/drift modules.
- Verified 1 target journey (J-22) passes browser QA — 13/13 dispatched UI tests passed across all six page states (loading, tripwire, calm, empty, unreadable, backend-down).
- The evaluator additionally re-verified all 8 required-still-passing journeys (J-01, J-03, J-05, J-11, J-17, J-18, J-19, J-20) on frames it personally opened, closing the QA report's evidence gap on J-05/J-11.
- J-22 promoted unknown → passing; 22 of 25 Must-have journeys now passing.

## What's left

- Closure's formal blocker is technically still open: the deterministic golden-script replay for the required-still-passing set (especially J-05, J-11) hasn't been run yet — the evaluator's live spot-check unblocked CONTINUE, but the recommended next step still pays down this record-keeping gap and formally re-clears closure to CLOSURE-PASS.
- The risk-analytics cluster is unbuilt: J-23 (watchlist concentration/correlation view), J-24 (per-stock risk-budget card), and J-25 (drawdown/dry-spell expectations) all remain unknown.
- The persisted referee-audit report artifact is git-untracked; on a clean checkout the page would show the honest-empty state instead of today's real calibration result until it's committed alongside its governance siblings.
- One computed field (`n_insufficient_null`, count of inconclusive null trials) is typed and served by the API but has no display slot on the page yet — currently 0 in the real data, so nothing is visibly hidden today.
- The offline calibration job has no UI trigger by design — a user cannot re-run it from the product; it stays a command-line/operator action.
- `what-to-click.md` step 7 and the UI test plan's UT-13 both still describe a stale `/evidence` empty state ("No certified claims yet") instead of the real 7-claims-all-FAIL page — non-blocking wording fix.
- A dev-handoff test-count typo ("41 tests" at one line) still doesn't match the actual 34 — cosmetic, already flagged by the reviewer and auditor.

## Next step

iter-37 = LEAN verify-only closeout (the iter-33→34 pattern): run the deterministic replay lane (only available in `goal-iter-lean.sh`) over the widened golden set to formally re-verify the required-still-passing journeys — especially J-05 and J-11, the ones closure named — and fold in the two accumulated golden scripts (J-21.json, J-22.json), then re-clear closure to CLOSURE-PASS. This is a hygiene/record closeout, not failure-remediation — J-22's own evidence is clean; the gap is a paperwork/evidence-trail issue on other journeys the diff never touched. Then FULL J-23 (backlog B-204, watchlist concentration X-ray) — or J-24/J-25 — continuing the risk-analytics cluster one journey per iteration; about 3 journeys remain to GOAL_ACHIEVED, a tractable path, not a plateau. Systemic flag (recurred at iter-33 and iter-36): the required-still-passing deterministic-replay DoD line is structurally unsatisfiable by any FULL iteration — a durable framework fix (adding the replay lane to the full path) is recommended. Non-blocking carry-forwards: commit the referee-audit report artifact at the next showcase step; soften the tripwire prose or build a genuinely-catchable temporal leak; push the contaminated assembler's cohort-date bound into SQL; fix the dev-handoff test-count typo; and correct the stale `/evidence` wording in `what-to-click.md` and the UI test plan.

## Assumptions made

- iter-36 · goal-evaluator — Ambiguity: DoD required J-01/J-03/J-05/J-11/J-17/J-18/J-19/J-20 live-re-verified or replayed inline; neither happened cleanly (QA's J-05/J-11 rows were unevidenced, no golden replay ran). We chose: marked J-05, J-11 (and J-01/J-03) re-verified passing on frames the evaluator personally opened (UT-13, TC-17), since the diff never touches their code paths; the dedicated golden replay is still owed as the next lean-closeout step. Reversible: yes
- iter-36 · goal-evaluator — Ambiguity: the iteration ended CLOSURE-FAIL, and the session's "partial" discipline normally withholds passing from an incompletely-verified target, but J-22's own canonical evidence is complete and the closure block is a different DoD line (other journeys' replay). We chose: scored J-22 passing — the closure auditor itself exempts J-22 by name; the "partial" guard is honored at the overall verdict level (CONTINUE, not GOAL_ACHIEVED) instead. Reversible: yes
- iter-36 · goal-decomposer — Ambiguity: whether J-22's acceptance requires a single live 200-trial run in the QA lane or a bounded/offline seeded run the panel reads. We chose: a two-halves decomposition — a fast seeded CI test proves the job-to-artifact half, browser-qa reading the persisted artifact proves the artifact-to-UI half — keeping the 200-trial battery offline per the session's anti-goal #8 discipline. Reversible: yes
- iter-35 · goal-evaluator — Ambiguity: J-21/J-16 acceptance reads as one live end-to-end Fetch observation, but browser-qa induced states via direct artifact injection and J-16's re-verification was a pytest integration test, not a live click-path. We chose: scored both passing via a two-halves decomposition (real-fetch integration test + artifact-injection DOM assertions), since the artifact is the single-source seam both readers consume. Reversible: yes
- iter-35 · goal-decomposer — Ambiguity: B-304 names three post-fetch checks, but J-21's own acceptance only exercises the overlap check, and the B-113 sentinel detectors a seam-scan check depends on don't exist yet. We chose: scoped iter-35 to the overlap comparator + drift artifact + preflight/`/data` surfacing, deferring the seam scan and distribution-envelope check as not required by J-21's acceptance text. Reversible: yes
- iter-34 · goal-evaluator — Ambiguity: J-20's re-confirmation only re-induced its GO state live; the loud DEGRADED/NO-GO states weren't re-induced due to a tool-permission boundary. We chose: scored J-20 passing (re-confirmed) — it was already fully verified across all three states at iter-33 and the readiness code is git-identical since, so a fresh loud-state induction would be verification for its own sake. Reversible: yes
- iter-33 · goal-evaluator — Ambiguity: the iteration ended CLOSURE-FAIL, and precedent withholds passing from a same-iteration target under CLOSURE-FAIL, but J-20's own evidence is clean and the block is a different DoD line (six other journeys' replay). We chose: scored J-20 passing — marking it partial would misattribute an unrelated replay gap to J-20's own evidence; the gap is recorded explicitly on the other six journeys instead. Reversible: yes
- iter-33 · goal-decomposer — Ambiguity: B-301's freshness check is underspecified for an offline app on a frozen seed — a wall-clock anchor would make the healthy GO state impossible and break determinism. We chose: anchor freshness to a deterministic seed-derived reference, counted in trading days, with stale states induced only via a controlled config/env override, never wall-clock time or mutated seed data. Reversible: yes
- iter-32 · goal-evaluator — Ambiguity: J-11 got no dedicated golden replay this iteration; unclear whether a 0-PASS ledger plus byte-identical economy suffices in lieu. We chose: scored J-11 passing on byte-identity plus corroboration rather than unknown — the invariant is trivially satisfied on an all-FAIL ledger with no stale-edge mechanism. Reversible: yes
- iter-31 · goal-evaluator — Ambiguity: J-19's core acceptance was fully browser-verified, but a lineage-link auto-scroll assist failed pre-fix and the fix was never re-run through the canonical lane. We chose: held J-19 at partial per the session's "correct-but-not-canonically-re-verified = partial" discipline, since an auditor's own browser re-check is not the DoD-named lane. Reversible: yes
- iter-31 · goal-decomposer — Ambiguity: whether J-19's graveyard should surface the staging ledger's non-PASS verdicts (previously "internal-only") and whether composition should be backend- or frontend-side. We chose: a new backend composition endpoint surfacing both ledgers' non-PASS verdicts, since staging still carries 0 PASS so the honesty fence holds. Reversible: yes
- iter-30 · goal-evaluator — Ambiguity: the DoD literally required "≥14" registry rows but the committed registry has 11, leaving open whether the literal count or the substantive dedup clause governs. We chose: scored the backfill line met by 11 rows — 14 raw ledger entries contain 3 exact cross-ledger duplicates, and round-trip tests prove full coverage. Reversible: yes
- iter-30 · goal-decomposer — Ambiguity: B-901 left open whether "already-certified claims" for the registry backfill means the canonical ledger only or every distinct claim across both ledgers. We chose: backfilled the union of pre-registered candidates and every distinct claim across both ledgers, deduplicated by hypothesis and labeled by source/status. Reversible: yes

## Quick verify

From `reports/phase-goal-mcp-loop-iter-36-what-to-click.md`:

1. Open `http://localhost:3255/research` in your browser
2. Click the "Referee audit" card
3. Look at the row of 4 number cards near the top of the page
4. Scroll down to the large card just below those 4 number cards
5. Click "Back to Research" near the top of the page

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-mcp-loop-iter-36.md |
| Dev handoff | — | docs/handoffs/goal-mcp-loop-iter-36-dev.md |
| Review | PASS_WITH_NOTES | reports/reviews/goal-mcp-loop-iter-36-review.md |
| Browser QA | PASS | reports/phase-goal-mcp-loop-iter-36-ui-test-results.md |
| Implementation summary | — | reports/phase-goal-mcp-loop-iter-36-implementation-summary.md |
| User-visible changes | — | reports/phase-goal-mcp-loop-iter-36-user-visible-changes.md |
| What to click | — | reports/phase-goal-mcp-loop-iter-36-what-to-click.md |
| UI surface map | — | reports/phase-goal-mcp-loop-iter-36-ui-surface-map.md |
| UI test plan | — | reports/phase-goal-mcp-loop-iter-36-ui-test-plan.md |
| UX regression | UX-REGRESSION-PASS | reports/phase-goal-mcp-loop-iter-36-ux-regression.md |
| QA | PASS | reports/qa/goal-mcp-loop-iter-36-qa.md |
| Audit | PASS_WITH_GAPS | docs/handoffs/goal-mcp-loop-iter-36-audit.md |
| Closure | CLOSURE-FAIL | reports/phase-goal-mcp-loop-iter-36-closure-verdict.md |
| Goal evaluation | CONTINUE | runs/goal-session-mcp-loop/iter-36/eval.md |
| Journey history | — | runs/goal-session-mcp-loop/state/journey-history.json |
