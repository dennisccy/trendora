# Iteration Summary — goal-ops-hardening-iter-70

**Verdict:** CONTINUE
**Iteration type:** goal-full
**Date:** 2026-08-12
**Iteration:** 70

## In plain words

**What you can do now:** Just like before: browse stock rankings, sector and theme views, backtests, and all five research tools, with an honest status message while the backend starts up; run backfills for any date range with no hidden cap; see backtest results and other aggregates load instantly from storage; get the Data Manager page kept current on its own; and count on the Regime Lab page holding up under heavy load. None of these were re-checked with a live browser this round (the test backend shut itself down partway through the checks), so they're marked "needs a quick re-check" rather than confirmed fresh — but nothing suggests any of them actually broke.

**What changed this time:** The app's small "backend status" indicator (the badge and banner shown at the top of every page, plus the status panel on the Data Manager page) now gets its answer from a fast, pre-prepared cache instead of recalculating it from scratch on every single check. During a real 17-minute heavy data job, every one of 1,030 status checks came back quickly (the slowest took about 1.2 seconds) — a big improvement over last round, when dozens of checks were slow and three got no answer at all. Nothing looks different on screen; it just answers faster and more reliably when the app is busy.

**What's next:** Re-check all eight promises with the backend actually running (it wasn't tested this round because of a test-setup hiccup, not a product problem), then close a small gap where the status cache could theoretically go stale without anyone noticing if its background updater ever stalls.

## Headline

Health check now answers from a pre-computed cache instead of recomputing on every request

## Direction

**Signal:** holding
**Why:** No journey moved to `failing` or `regressed` this iteration — the evaluator explicitly rejected REGRESSION (C.1) because nothing was tested, and `BLOCKED`/`SKIPPED` evidence is not the same as a failed check. All eight journeys shifted from mostly-`passing` to `partial (pending_infra)` purely because the QA backend shut down cleanly between test lanes, leaving zero fresh browser/replay evidence this round — a verification gap, not a product regression. Meanwhile J-07 (the one target journey) had its best round yet: 0 of 1,030 health polls over the 2.0s ceiling and 0 non-answers, down from 77 breaches and 3 non-answers last round.

**Trend (last 2 iters):**
- Newly passing this iter: none
- Newly passing in last 2 iters total: none
- Regressions in last 2 iters: none (both iter-69 and iter-70 explicitly rejected a REGRESSION verdict)
- Anti-goal violations in last 2 iters: iter-70 opened 6 new (all minor) and closed 4 from iter-69; iter-69's own new-violation count is outside the trimmed log excerpt available this round. Cumulative ledger: 230 total, 115 unresolved, 0 unresolved critical.
- Iters with no journey state change: 0 of last 2 (both iters recorded journey-status deltas)

**Latest evaluator reasoning:** "The fix worked. The app used to redo two slow checks every time something asked 'are you healthy?'. Now it prepares those answers in the background and hands over a ready answer. During a real 17-minute data job, all 1,030 health checks were answered, none took longer than 2 seconds, and the slowest was 1.23 seconds... But this round produced no picture evidence for any journey. The test backend shut itself down between two test stages, so the browser check and the replay check never ran. Nothing failed — they were never run. All eight journeys now wait for a re-check next round."

## What was done

- Product changes: apps/backend/app/engine/readiness.py, apps/backend/app/api/health.py, apps/backend/main.py, apps/backend/app/engine/data_manager.py, apps/backend/app/config.py, config.yaml, apps/backend/tests/test_readiness.py, apps/backend/tests/test_health.py, apps/backend/tests/test_health_watchdog.py, apps/backend/tests/test_data_manager.py, reports/perf-budgets.md
- Added a bounded-interval background-refresh cache for `compute_readiness`/`compute_preflight` inside `app.engine.readiness`, ticking every `readiness.refresh_interval_seconds` (new config knob, default 0.5s) via a daemon thread started/stopped from the same `lifespan` sequence as the existing warmup thread.
- `GET /api/health` now reads the cached dict instead of recomputing readiness/preflight on the request thread; the three existing DB reads stay on the request path unchanged (out of scope, not implicated by iter-69's attribution).
- Added a cold-start synchronous fallback, an immediate-refresh trigger fired at the end of ingest finalize, degrade-on-error (serve last-known-good on tick failure), and an atomic dict-swap proven by a dedicated concurrency test.
- During audit, fixed a re-introduced unguarded `logger.exception` in the tick path (could have discarded a completed ingest's `aggregates_refreshed` or silently killed the refresh thread under memory pressure) and corrected two coverage mis-statements in the new perf-budgets addendum.
- Live-warm drill (17m20s, real backfill, full 9-phase warm including `factor_lab_all_warm`): 0 of 1,030 polls over the 2.0s ceiling, 0 non-answers — first zero-breach round in this session's history, versus iter-69's 8.09% breach rate.
- 14 new/updated backend tests added across `test_readiness.py`, `test_health.py`, `test_health_watchdog.py`, `test_data_manager.py`; 279/280 pass (1 pre-existing, unrelated test-order artifact).
- Browser QA and deterministic replay lanes were SKIPPED/BLOCKED (0/8, 0/7) — the QA backend shut down cleanly between lanes; the evaluator independently confirmed the live process (restarted separately) answers healthily.

## What's left

- All 8 journeys (J-01, J-03, J-04, J-05, J-06, J-07, J-08, J-09) are `partial` — a fresh browser/replay verification is owed against a live backend before any can return to `passing`; the engine schedules this automatically next round.
- J-07 ("Heavy aggregates never take the service down") specifically: the browser half of its required "union of both drills" never ran this round, 32.1 seconds at the start of the job window went unpolled (including `coverage_membership_timeline_refresh`, the phase that held the single breach in each of the two prior rounds), and steps 3 (VmPeak margin) and 4 (memory-pressure abort) still carry forward on evidence durability rather than being re-measured.
- Unbounded cache staleness: if the new background refresh thread ever dies or wedges, `GET /api/health` would keep serving a frozen-but-plausible value with no age check or `stale_for_s` field — a small, already-scoped fix (stamp the payload, fall back to a synchronous compute past N intervals).
- A QA report write-up defect: it marked two coverage claims "✓ Developer verified via replay" when no such replay ran — flagged by the audit, not yet corrected in the artifact itself.
- The J-05 walkthrough recording remains unmade for a 12th consecutive round; J-07's own new walkthrough steps are also unrecorded.
- Several owner-only decisions remain parked: the 2-second health-check ceiling policy (long jobs vs. short jobs only), sign-off on a one-line ordering-bug fix in `scripts/automation/browser-qa-phase.sh`, and a cost-sanction decision (this round ran ~5x over its time budget).

## Next step

Run a normal (lean) round with two jobs: (1) re-check all eight journeys with the backend actually running — they were never tested this round, and the engine schedules this automatically since every journey is marked as owing browser evidence; confirm the backend answers before the checking stage begins. (2) Stop the health answer from going stale silently — add a "prepared at" timestamp to the cached answer and recompute on the spot if it's older than a few refresh cycles, protecting the goal's own promise that the app tells the truth about its state. Smaller items riding along: fix the QA report's false "verified via replay" claim, make the `health.py` fallback explicit instead of relying on an incidental error, add a test composing the finalize-hook trigger with a served response, and record the long-overdue J-05 and J-07 walkthroughs.

## Assumptions made

- iter-70 · goal-evaluator — Ambiguity: the pending-infra carve-out is keyed to a `browser-infra.json` token, but this round's failure was a backend service death (not a browser failure), so no token was written and the literal fallback rule points to `unknown` while the carve-out points to `partial`. We chose: apply the carve-out anyway — all eight journeys scored `partial` with `pending_infra: true`, since the failure class is identical in every way that matters and the engine schedules the make-up ride from that flag, not from the token. Reversible: yes.
- iter-70 · goal-decomposer — Ambiguity: "serve from a stored/bounded value" didn't name a mechanism (persisted DB table vs. in-process cache). We chose: an in-process, bounded-interval background-refresh cache inside `app.engine.readiness`, reusing the existing `app.engine.warmup` daemon-thread idiom, since readiness/preflight are liveness state (not data that must survive a restart) and a synchronous cold-start fallback already covers that case. Reversible: yes.
- iter-69 · goal-evaluator (2 of 2) — Ambiguity: the standing "profile before bounding" ban on `factor_lab_all_warm` was conditional on the sub-timing naming a component, and this round's sub-timing did. We chose: declare the ban's release condition met and mark it RELEASED as a legitimate alternative target (not the primary recommendation). Reversible: yes.
- iter-69 · goal-evaluator (1 of 2) — Ambiguity: whether a 5-second client-side non-answer (server still computing) counts as an "unresponsive window" for J-07 step 2. We chose: keep the journey at `partial` and record the deterioration explicitly rather than downgrading further, since the server itself never returned a non-200 or crashed. Reversible: yes.
- iter-69 · goal-decomposer — Ambiguity: how to arm the health-check diagnostic flag for the browser-QA lane's backend without editing owner-gated `scripts/automation/*` files. We chose: direct the browser-qa-agent via the iteration's own testing requirements to export the flag itself and disclose honestly if it inherits an already-running, unarmed backend. Reversible: yes.
- iter-68 · goal-evaluator — Ambiguity: J-07 step 2 doesn't say which health polls count toward the acceptance measurement when two lanes poll under different workloads. We chose: score against the union of all polls taken in the iteration rather than just the smaller, better-looking dev-drill subset. Reversible: yes.
- iter-67 · goal-evaluator — Ambiguity: whether an un-re-measured J-07 acceptance step (VmPeak margin, memory-pressure abort) should count against the journey's status. We chose: carry those steps forward on evidence durability since the warm-path code they test is byte-identical to when they last passed. Reversible: yes.
- iter-67 · goal-decomposer — Ambiguity: the prior recommendation named a diagnostic method only at the concept level ("an in-app watchdog"), consistent with several designs. We chose: the smallest option that directly answers the question — an ASGI-layer timestamp pair plus a periodic event-loop-lag probe, gated behind an off-by-default env var. Reversible: yes.

## Quick verify

From `reports/phase-goal-ops-hardening-iter-70-what-to-click.md`:

1. Open `http://localhost:3255/` in your browser
2. Navigate to `http://localhost:3255/data`
3. In the job form, type "2026-05-02" into "Start date" and "2026-05-03" into "End date", then click "Start"
4. Navigate to `http://localhost:3255/scanner-runs`
5. Click any row's date

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-ops-hardening-iter-70.md |
| Dev handoff | — | docs/handoffs/goal-ops-hardening-iter-70-dev.md |
| Review | PASS_WITH_NOTES | reports/reviews/goal-ops-hardening-iter-70-review.md |
| Browser QA | SKIPPED | reports/phase-goal-ops-hardening-iter-70-ui-test-results.md |
| Implementation summary | — | reports/phase-goal-ops-hardening-iter-70-implementation-summary.md |
| User-visible changes | N/A — Backend-only phase | reports/phase-goal-ops-hardening-iter-70-user-visible-changes.md |
| What to click | — | reports/phase-goal-ops-hardening-iter-70-what-to-click.md |
| UI surface map | N/A — Backend-only phase | reports/phase-goal-ops-hardening-iter-70-ui-surface-map.md |
| UI test plan | — | reports/phase-goal-ops-hardening-iter-70-ui-test-plan.md |
| UX regression | UX-REGRESSION-SKIPPED | reports/phase-goal-ops-hardening-iter-70-ux-regression.md |
| QA | PASS_WITH_NOTES | reports/qa/goal-ops-hardening-iter-70-qa.md |
| Audit | PASS_WITH_GAPS | docs/handoffs/goal-ops-hardening-iter-70-audit.md |
| Closure | CLOSURE-PASS | reports/phase-goal-ops-hardening-iter-70-closure-verdict.md |
| Goal evaluation | CONTINUE | runs/goal-session-ops-hardening/iter-70/eval.md |
| Journey history | — | runs/goal-session-ops-hardening/state/journey-history.json |
