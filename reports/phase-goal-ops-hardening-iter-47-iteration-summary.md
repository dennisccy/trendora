# Iteration Summary — goal-ops-hardening-iter-47

**Verdict:** ESCALATE
**Iteration type:** goal-full
**Date:** 2026-08-04
**Iteration:** 47

## In plain words

**What you can do now:** View backtest evidence pulled straight from storage, never a live recalculation while you wait. Get an honest badge whenever the app is crunching numbers in the background. Other things you could do before — backfilling price history, browsing sector and research pages, seeing an honest zero-work explanation — likely still work, but haven't been freshly re-checked this round, so they aren't listed as confirmed here.

**What changed this time:** The Evidence page now shows a small amber "Refreshing" badge on any claim card that's serving last-known-good numbers while a fresher version finishes computing in the background — and the page itself now answers in about a hundredth of a second right after a data update, instead of sometimes freezing for over two and a half minutes.

**What's next:** Next the team will re-check all eight of the app's core capabilities against today's build — nothing has been freshly confirmed end-to-end for two rounds running — and then tackle the one ingest job that still never finishes.

## Headline

The Evidence page no longer stalls after a data update.

## Direction

**Signal:** holding
**Why:** ESCALATE fires because the browser-QA lane was never re-run after three subsequent product-code changes, leaving both target journeys (J-06, J-07) with zero executed test cases and the closure gate at CLOSURE-FAIL — even though the underlying Evidence-page fix is proven correct at live scale (byte-identical output, 0.012s vs iter-46's 163s+). J-05 remains failing for a fourth consecutive round (its ingest finalize tail never reaches a terminal state), and no journey's status moved in either direction this iteration, so direction reads as holding rather than improving or regressing — real engineering progress, unverified end-to-end for the second round running.

**Trend (last 2 iters):**
- Newly passing this iter: none
- Newly passing in last 2 iters total: none
- Regressions in last 2 iters: none
- Anti-goal violations in last 2 iters: iter-46: 7 new (5 open minor, 2 resolved same iter); iter-47: 7 new (6 open minor, 1 resolved in-audit) — all minor, 0 unresolved critical in either iter
- Iters with no journey state change: 1 of last 2

**Latest evaluator reasoning:** The code work this round did what it set out to do. I opened the Evidence page's own endpoint on the running app and it answered in 0.012 seconds with all seven claim panels filled in. Last round the same call took about 163 seconds when the app was idle and never finished at all when it was busy. The check nobody ran is the problem.

## What was done

- Product changes: apps/backend/app/engine/evidence.py, apps/backend/app/engine/forward_testing.py, apps/backend/app/engine/research.py, apps/backend/app/engine/samples.py, apps/backend/app/engine/warmup.py, apps/frontend/app/evidence/page.tsx, apps/frontend/lib/evidence.ts
- Fixed `GET /api/evidence` to survive an unrelated data update: serves the last-good generation behind an honest "Refreshing" label instead of falling onto a 163s+ cold-recompute tail (byte-identical output, live-scale SHA-256 verified)
- Bounded `samples.py`'s decile-cohort observation resolver (a third unbounded whole-history read the iter-46 audit flagged) — peak memory down 5x (1,173MB to 573MB), longest GIL-hold down 9.4x, 5/5 clean under a tightened memory-pressure test
- Narrowed `_drawdown_ticker_slice_map`'s row read from ~8M rows to per-ticker cohort dates (90-96% row reduction on the two measured claims), byte-identical
- Guarded the last two unprotected log calls in `warmup.py`'s per-claim exception handlers
- Rebuilt 6 of 8 journey replay scripts the prior audit proved were null tests (asserting persisted page text instead of the live job); retired J-04 and J-07's goldens to the LLM lane, which never ran
- Auditor found and fixed an IMPORTANT defect mid-iteration: the new re-warm ran a duplicate full-ledger warm alongside the boot warm, doubling peak concurrent heavy compute — fix is mutation-verified
- Browser QA lane never re-ran after 3 subsequent code changes — 0 of this iteration's 2 target journeys (J-06, J-07) verified; closure gate returned CLOSURE-FAIL

## What's left

- Journey J-05 (Aggregates are precomputed at ingest, never on the fly) failing — 4th consecutive round; a real ingest's finalize tail runs for many minutes after the ~12s snapshot write and the job row never reaches a terminal state
- Closure blocker: browser QA lane must re-run and produce dedicated rows for J-06 and J-07 (this iteration's targets) before the iteration can be scored complete
- Journeys J-01, J-03, J-04 (partial) — carried, not re-verified this iteration; still resting on iter-46 evidence
- Journey J-06 (partial) — the Evidence-page fix is confirmed, but its own step 11 route (`/research/regime-lab`) can still drive the process to the 8192MB memory ceiling, deferred 12 times
- Journey J-07 (partial) — `samples.py`'s "total"/"regime" branches still read the whole population unbounded; `GET /api/health` exceeded its 2s budget on 8 of 20 polls during an ingest finalize tail
- Known limitation: full catch-up after a data change now measured at ~26 minutes, not the originally-recorded 7-8 minutes
- Known limitation: `tests/test_api_evidence.py` (a slow integration fixture) not re-run this iteration
- Anti-goal note: a `provider='yahoo'` live-network ingest ran this iteration via a pre-existing sanctioned import path — filed as minor (iter-47/bh), flagged for the owner since the session's premise is offline-deterministic

## Next step

Full depth. Give the next round this order.

1. Run the eight journey checks FIRST, before writing any new code. The app has not been checked since three code changes ago, so nobody knows what today's app really does. The services are already up and healthy for it. Two journeys — "Pages load only what they need" (J-06) and "Heavy aggregates never take the service down" (J-07) — have no check at all and no picture. Do not start a new data job while another one is still finishing, and expect "Aggregates are precomputed at ingest" (J-05) to come out red; that is the honest answer.
2. Before that run, add one line to the J-05 check so it cannot pass by accident: make it require "1 snapshots" on the job card. The auditor wrote the exact fix. Today the check passes even when the job does no work at all.
3. Then make adding one old day of history finish. The day's snapshot is written in about twelve seconds; what never ends is the clean-up work that follows, so the job row sits on "running" forever. This is the fourth round in a row this journey has failed and it is the only remaining product fault on a must-have journey.
4. Stop one page from being able to eat the whole machine. Opening the Regime Lab page took the app to its 8 GB limit twice this round and left the background warm-up stuck at three of seven panels for twenty minutes. This has been put off twelve times; it is now measured, on a page a normal user can open.
5. Smaller, already written down: two more places on the same Evidence page still read a whole cohort at once (`samples.py:161` and `:168`); the app can still run two identical warm-ups at the same time when a data job is finishing (audit B2 — one shared "warm in progress" flag fixes it); the health check answered slower than its 2-second promise on 8 of 20 tries while a job was finishing; the new background worker does not show up on the page that is supposed to list background work.
6. Carried, untouched: iter-29/b and the badge wording after a failed warm-up (nineteen rounds unmade); iter-31/e; iter-32/f; iter-35/k; iter-36/n; iter-37/o; iter-37/q; iter-39/u; iter-46/az (the ~29 s first answer after start, still unmeasured on a quiet machine); iter-46/ba.
7. Capture only, never a round's goal: J-07's `[NEW]` walkthrough (seventeenth round unrecorded) and J-05's acceptance frames.
8. For the owner: nothing needs a decision, but three facts belong in front of him. The Evidence page went from about three minutes to about one hundredth of a second, which is this round's real win. The app was never checked end to end after that win landed, for the second round running. And a data job in this round pulled real prices from Yahoo over the internet rather than from the committed offline copy — that is how the product has been built since July and nothing was saved into version control, but it is worth him knowing, because this project's promise is to run offline.

## Assumptions made

- iter-47 · goal-evaluator — Ambiguity: no lane verified any journey against this iteration's shipped build (the only browser artifact reads BLOCKED with zero rows for both target journeys, and the six replay rows came from scripts that assert almost nothing). Unclear whether a journey whose prior "passing" was earned one iteration ago keeps that status when its module changed but its own code path didn't, and its only fresh "evidence" is a null test. We chose: keep J-08 and J-09 passing (their own producers are untouched by this diff, confirmed at the source, plus a live spot-check) while scoring J-01/J-03/J-04/J-06/J-07 partial and J-05 failing. Reversible: yes
- iter-47 · goal-evaluator — Ambiguity: AG-9 (critical) forbids live network calls in ingest jobs without a goal.md amendment; a `provider='yahoo'` job ran this iteration via a pre-existing, product-sanctioned import path and moved the working DB's latest bar forward. Unclear whether an already-sanctioned live path counts as "introduced" without an amendment. We chose: score it minor and open (not critical), so ESCALATE rather than REGRESSION — nothing was introduced by this iteration, the path predates this cycle, and the data is real, never fabricated. Reversible: yes
- iter-47 · goal-decomposer — Ambiguity: goal.md doesn't rank J-05 (the sole failing journey) above J-06/J-07 (both partial, sharing one diagnosed defect cluster); the priority rubric doesn't by itself resolve which single risky change to take this round. We chose: target J-06/J-07's Evidence-page fix (an explicit two-journey unblocker) this iteration, deferring J-05's riskier old-day-insert fix to a later round. Reversible: yes
- iter-46 · goal-evaluator — Ambiguity: the browser lane scored J-07 FAIL on a criterion (`/api/evidence`'s 300s budget) that actually belongs to this iteration's own DoD item TC-4, not to any of J-07's own four acceptance steps. We chose: score J-07 against its own four steps separately, giving it partial (its first movement since iter-34) while filing the `/api/evidence` cost as its own open ledger item. Reversible: yes
- iter-46 · goal-evaluator — Ambiguity: decision tree C.1 fires REGRESSION when a journey moves passing to failing, but the only browser lane that scored J-01/J-03/J-06 FAIL (and J-04 PASS on a missed budget) ran before two build-changing fixes landed inside the same iteration. We chose: partial for all four (not failing), since each row records only some assertion steps failing and the specific repairs were verified in the machine record — so ESCALATE rather than REGRESSION. Reversible: yes
- iter-46 · goal-decomposer — Ambiguity: goal.md doesn't say whether a journey may be listed as a Target journey when the iteration's code change doesn't directly address that journey's own root cause (J-05's fix doesn't touch the two accumulator bounds this round targets). We chose: list J-05 as a Target journey alongside J-07 anyway, since this round supplies J-05 its first dedicated live drill in the underlying failure class. Reversible: yes
- iter-45 · goal-evaluator — Ambiguity: AG-8 (critical) forbids exhausting a service's memory; this iteration the backend was fully unreachable for ~42 minutes, and goal.md doesn't say whether a memory-exhaustion defect an iteration inherited (rather than introduced) counts as critical. We chose: minor, therefore ESCALATE rather than REGRESSION — this iteration's diff never ran the code implicated, the two driving accumulators are pre-existing, and the UI degraded honestly rather than blank. Reversible: yes

## Quick verify

From `reports/phase-goal-ops-hardening-iter-47-what-to-click.md`:

1. Open `http://localhost:3255/evidence` in your browser
2. On any visible claim card, look under the heading "Historical drawdown & dry-spell expectations (…-day hold)"
3. Open `http://localhost:3255/data` and find the "Price history" row in the "Dataset coverage" panel near the top
4. In the "Start date" field, type the calendar day right after the date you just noted (e.g. if you saw "→ 2026-07-31", type `2026-08-01`). Type the same date into the "End date" field, then click the "Start" button
5. Return to `http://localhost:3255/evidence` (open a new tab or navigate back) within the next few minutes and reload the page

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-ops-hardening-iter-47.md |
| Dev handoff | — | docs/handoffs/goal-ops-hardening-iter-47-dev.md |
| Review | PASS_WITH_NOTES | reports/reviews/goal-ops-hardening-iter-47-review.md |
| Browser QA | BLOCKED | reports/phase-goal-ops-hardening-iter-47-ui-test-results.md |
| Implementation summary | — | reports/phase-goal-ops-hardening-iter-47-implementation-summary.md |
| User-visible changes | — | reports/phase-goal-ops-hardening-iter-47-user-visible-changes.md |
| What to click | — | reports/phase-goal-ops-hardening-iter-47-what-to-click.md |
| UI surface map | — | reports/phase-goal-ops-hardening-iter-47-ui-surface-map.md |
| UI test plan | — | reports/phase-goal-ops-hardening-iter-47-ui-test-plan.md |
| UX regression | UX-REGRESSION-SKIPPED | reports/phase-goal-ops-hardening-iter-47-ux-regression.md |
| QA | PASS | reports/qa/goal-ops-hardening-iter-47-qa.md |
| Audit | PASS_WITH_GAPS | docs/handoffs/goal-ops-hardening-iter-47-audit.md |
| Closure | CLOSURE-FAIL | reports/phase-goal-ops-hardening-iter-47-closure-verdict.md |
| Goal evaluation | ESCALATE | runs/goal-session-ops-hardening/iter-47/eval.md |
| Journey history | — | runs/goal-session-ops-hardening/state/journey-history.json |
