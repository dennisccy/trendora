# Iteration Summary — goal-ops-hardening-iter-61

**Verdict:** CONTINUE
**Iteration type:** goal-full
**Date:** 2026-08-11
**Iteration:** 61

## In plain words

**What you can do now:** Start a backfill over any date range and get a clear explanation when there's nothing new to fetch. Pull in long stretches of history with no hidden cap. See the app's status live while it's starting up instead of a blank page. Trust that the Data Manager page's counts reflect the latest finished job — new this round. Pages load quickly because they only fetch what they need. View backtest results instantly, already computed and stored. See when the app is crunching numbers in the background.

**What changed this time:** The Data Manager page (`/data`) now refreshes its own "Snapshot Dates" and "Backfill Gaps" numbers automatically, about every 30 seconds. Before, those numbers only updated when the same browser tab had started the job itself — a backfill finished elsewhere (another tab, a script, a teammate) left the page showing stale counts until someone manually reloaded. Now it catches up on its own within about half a minute.

**What's next:** Next, the team will fix a testing-tool bug that has been hiding two rounds of results, get a fresh live check for the aggregates-at-ingest fix, and ask the product owner to decide how fast the app must answer a health check during a long background job — that answer is the one thing standing between the last journey and being finished.

## Headline

The Data Manager page now keeps its numbers current on its own.

## Direction

**Signal:** improving
**Why:** J-05 "Aggregates are precomputed at ingest, never on the fly" moved from partial to passing this iteration, after the evaluator proved last iteration's reported blocker was a UTC-vs-local-time misreading rather than a real defect. The round also shipped a genuine fix (the `/data` ambient 30-second refresh) and reconciled J-07's health-check measurement from a raw log. Only J-07 remains partial, now blocked on a single owner decision rather than any open engineering work.

**Trend (last 2 iters):**
- Newly passing this iter: J-05
- Newly passing in last 2 iters total: J-05 (iter-61 only; iter-60 held J-05 at partial)
- Regressions in last 2 iters: none
- Anti-goal violations in last 2 iters: iter-60 — 7 new, all minor; iter-61 — 7 new, all minor (1 raised and closed within the same round); 0 unresolved critical in either round
- Iters with no journey state change: 1 of last 2 (iter-60)

**Latest evaluator reasoning:** This round was sent to fix a broken number on the Data Manager page. That number was never broken — the database stores its times in UTC, while the app's log and the picture files use local time, one hour later, and last round compared a picture taken at 07:47 to a database row written at 07:58 and called the picture stale. With that blocker withdrawn, J-05 "Aggregates are precomputed at ingest" moves to passing: 7 of 8 journeys now pass, and J-07 is one owner sentence from closing.

## What was done

- Product changes: apps/backend/tests/test_data_manager.py, apps/frontend/components/readiness-provider.tsx, apps/frontend/app/data/page.tsx
- Root-caused the `/data` coverage-staleness defect: the backend was already serving the correct persisted row; the actual gap was the frontend never refetching coverage except after a job the SAME tab had started.
- Fixed it: `/data` now runs an ambient refresh on the existing readiness-poll's 30-second idle cadence, independent of which tab or script started the underlying job.
- Re-measured J-07's health-check responsiveness from a raw poll log during a real 17-minute backfill: 1078/1078 answered, exactly one 2.849s outlier, fully reconciled against the job's own OPEN/CLOSED markers.
- Captured and opened the first inspected screenshot of the Regime Lab's "Unavailable" degrade indicator, with a control arm proving the underlying cohort holds real observations.
- Withdrew iteration 60's own reported blocker (stale `/data` counts) after proving it was a UTC-vs-local-time misreading on two independent jobs — promoting J-05 to passing.
- Verified 6 required-still-passing journeys (J-01, J-03, J-04, J-06, J-08, J-09) pass browser QA via deterministic replay (6/6); target journeys J-05 and J-07 got no fresh browser-QA row this round because of a lane-ordering bug in `browser-qa-phase.sh`.

## What's left

- Journey J-07 "Heavy aggregates never take the service down" stays partial — blocked solely on one owner decision about the 2-second health-check ceiling during long background jobs.
- Closure gate is CLOSURE-FAIL: the merged browser-QA result is BLOCKED because target journeys J-05 and J-07 got zero executed test rows this round, due to `browser-qa-phase.sh` assigning `TARGET_JOURNEYS` after it's needed.
- That lane-ordering bug needs owner sign-off to fix (it touches a build-system script) before J-05 can get a fresh, machine-made pass instead of a carried-over one.
- The walkthrough recording for J-05 and J-07 (`demo.sh ops-hardening --session-live`) still has not been made — deferred for the 27th round.
- The new `/data` auto-refresh has no automated regression test protecting it (audit finding F2).
- `GET /api/health`'s `last_run_date` field is hardcoded to null — a separate, pre-existing, out-of-scope bug flagged for the backlog.
- A long list of smaller carried backlog items (Regime Lab badge wording after a failed warm-up, and roughly a dozen more) remains untouched, per the session's one-risky-change-per-iteration rule.

## Next step

Run the next round at full depth. First, fix the `browser-qa-phase.sh` ordering bug that has silently hidden two rounds' worth of target-journey test results — this needs the owner's go-ahead since it is a build-system script. Then replay J-05's own check script for real against the reserved date so it has a fresh machine-made pass, ask the owner the J-07 health-check-ceiling question a twelfth time (it is the only thing left that cannot be measured further), and record the walkthrough for J-05 and J-07. Smaller carried items (a stray evidence-count note, the empty "last run date" field, a missing test for the new refresh) follow behind those.

## Assumptions made

- iter-61 · goal-evaluator (2 of 2) — Ambiguity: ESCALATE's practical effect binds the next round's depth, and structural facts still favor full depth, but none of ESCALATE's three clauses fires literally this round (already full depth, no failing journey, review not fail-open). We chose: CONTINUE with a full-depth recommendation rather than ESCALATE, since manufacturing a clause match to get a side effect is what the methodology forbids, and a full-to-full ESCALATE would only buy the mandate. Reversible: yes
- iter-61 · goal-evaluator (1 of 2) — Ambiguity: methodology normally requires a status-change to carry a results row and screenshot in the same iteration, but no lane produced a J-05 row this round (a lane bug, not a product failure), while the evidence-durability and no-blocking-on-lane-gap rules both support promotion. We chose: promote J-05 from partial to passing on durable evidence, since the one blocker on record was proven void and the product diff never touched ingest/serving code. Reversible: yes
- iter-60 · goal-evaluator (2 of 2) — Ambiguity: whether to keep J-05 partial because its written acceptance text still names a missing walkthrough recording, versus the framework's rule against blocking a journey on a missing capture. We chose: treat the missing walkthrough as non-blocking, holding J-05 partial instead on the (separately evidenced, later withdrawn) stale-coverage-count defect. Reversible: yes
- iter-60 · goal-evaluator (1 of 2) — Ambiguity: whether a stale-by-one descriptive count on the Data Manager page — real numbers that had gone stale, not invented ones — counts as a breach of the critical "displayed numbers must be correct" anti-goal. We chose: score it minor, not a critical halt, since nothing was fabricated (this call was withdrawn the next round after being proven a timezone misreading). Reversible: yes
- iter-59 · goal-evaluator (2 of 2) — Ambiguity: whether to choose ESCALATE to bind the next round to full depth (needed for the walkthrough/demo lane) even though none of ESCALATE's literal clauses fired. We chose: CONTINUE with a full-depth recommendation instead, since manufacturing a clause match is what the methodology forbids. Reversible: yes
- iter-59 · goal-evaluator (1 of 2) — Ambiguity: whether a new "degraded" display showing zero for cohorts that genuinely hold observations (distinguishable only via a hover tooltip) counts as a critical "wrong number on screen" anti-goal breach. We chose: score it minor, not critical, since the value is truthfully degraded rather than fabricated and only appears under deliberate fault injection. Reversible: yes
- iter-59 · goal-decomposer — Ambiguity: whether the prior evaluator's "measure and then bound" instruction meant one combined round or two separate rounds (measure now, fix later). We chose: ship the fix this same iteration, since the mechanism was already profiled by a real prior incident and the fix pattern was already proven elsewhere in this codebase. Reversible: yes

## Quick verify

From `reports/phase-goal-ops-hardening-iter-61-what-to-click.md`:

1. Open `http://localhost:3255/data` in your browser
2. Look at the "Dataset coverage" panel near the top of the page
3. Look at the "Start a fetch / backfill job" panel below the coverage panel
4. Refresh the page (press F5 or Cmd+R)
5. Navigate to `http://localhost:3255/research/regime-lab?asof=2010-11-05`

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-ops-hardening-iter-61.md |
| Dev handoff | — | docs/handoffs/goal-ops-hardening-iter-61-dev.md |
| Review | PASS_WITH_NOTES | reports/reviews/goal-ops-hardening-iter-61-review.md |
| Browser QA | BLOCKED | reports/phase-goal-ops-hardening-iter-61-ui-test-results.md |
| Implementation summary | — | reports/phase-goal-ops-hardening-iter-61-implementation-summary.md |
| User-visible changes | — | reports/phase-goal-ops-hardening-iter-61-user-visible-changes.md |
| What to click | — | reports/phase-goal-ops-hardening-iter-61-what-to-click.md |
| UI surface map | — | reports/phase-goal-ops-hardening-iter-61-ui-surface-map.md |
| UI test plan | — | reports/phase-goal-ops-hardening-iter-61-ui-test-plan.md |
| UX regression | UX-REGRESSION-SKIPPED | reports/phase-goal-ops-hardening-iter-61-ux-regression.md |
| QA | PASS | reports/qa/goal-ops-hardening-iter-61-qa.md |
| Audit | PASS_WITH_GAPS | docs/handoffs/goal-ops-hardening-iter-61-audit.md |
| Closure | CLOSURE-FAIL | reports/phase-goal-ops-hardening-iter-61-closure-verdict.md |
| Goal evaluation | CONTINUE | runs/goal-session-ops-hardening/iter-61/eval.md |
| Journey history | — | runs/goal-session-ops-hardening/state/journey-history.json |
