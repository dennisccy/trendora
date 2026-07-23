# Iteration Summary — goal-ops-hardening-iter-15

**Verdict:** STALLED
**Iteration type:** goal-full
**Date:** 2026-07-23
**Iteration:** 15

## In plain words

**What you can do now:** Browse stock rankings, sector and theme views, backtests, research tools, and evidence-backed scores. Back-fill any historical date range with no size cap and get an honest explanation when there's no new work to do. Trust the status badge to tell the truth while the app is starting up, updating its data, or recovering from a crash, and see an honest record of real progress even if an update gets interrupted mid-way. Two pages (the Data page's index/benchmark list, and the home page's chart) load quickly rather than sluggishly.

**What changed this time:** Behind-the-scenes work — nothing new to click. The team found and fixed the exact reason the Backtest page could sometimes take several minutes to respond: several requests asking for the same not-yet-calculated numbers at the same time were each redoing the same expensive work instead of sharing one answer. Now only the first request does the work, and everyone else waits briefly and shares it. But testing this fix against the real full-size data showed that a genuinely brand-new calculation (one nobody has already started) can still take about three minutes on its own — a cost this fix can't remove, so the Backtest page can still be slow to load in that one situation. It never shows an error or freezes though; it always keeps showing honest results.

**What's next:** Next, the product owner needs to pick one way to handle that lingering slow case — show a progress indicator instead of a silent wait, redesign so results are always ready before anyone asks for them, or formally accept the wait as a known limit — before this chapter of the work can be called finished.

## Headline

Faster, reliable /backtest responses when a data-refresh job is running at the same time

## Direction

**Signal:** holding
**Why:** J-06 and J-07 stayed `partial` again this iteration; the one agent-tractable item (root-causing and fixing the concurrent-load `/backtest` slowdown) is done and correct — a single-flight de-dup verified 9.91x→1.04x on a fixture — but the live full-scale measurement shows the residual 178.74s cold-compute cost is a hard limit that fix cannot reduce, and every remaining path (an affordance, a redesign, or accepting the budget) is now an owner decision, not agent-tractable progress or a fresh regression.

**Trend (last 5 iters):**
- Newly passing this iter: none
- Newly passing in last 5 iters total: none (J-01/J-03/J-04/J-05 have stayed passing throughout; J-06/J-07 remain partial)
- Regressions in last 5 iters: iter-13 (REGRESSION verdict — the AG-8 anti-goal escalated to a ~12-minute availability outage; no journey itself moved passing→failing)
- Anti-goal violations in last 5 iters: 1 critical (AG-8), firing/unresolved across iter-11, iter-12, and iter-13 (escalating to iter-13's ~12-minute outage — the REGRESSION trigger), resolved at iter-14 and stays resolved through iter-15
- Iters with no journey state change: 4 of last 5 (iter-14 introduced a new journey, J-07)

**Latest evaluator reasoning:** "The agent-tractable item iter-14 named — root-cause and fix `/backtest`'s 211.8s concurrent cache-miss (UT-04) — is genuinely DONE: a correctly-scoped, byte-identity-preserving single-flight de-dup in `forward_aggregates_cached` (5 concurrent same-key MISSes 9.91x → 1.04x on a 60k-row fixture). But the one operator-supervised deep-basis pass proves the fix does NOT close the ≤1.5s `/backtest` budget: the live cold MISS is still 178.74s (WARN, ~119x over) plus an unflagged 5.37s second breach. No journey regressed, no anti-goal is violated, coherence is PASS — but every remaining path to closing J-06/J-07 is now a human-owned product-direction decision, exactly the escalation the spec reserved for the owner."

## What was done

- Root-caused UT-04's 211.8s `/backtest` concurrent cache-miss finding by measurement, not assumption: confirmed redundant same-key recomputation as the dominant mechanism (5 concurrent MISSes triggered 5 full compute calls, 9.91x slower); a separate database-contention candidate was isolated and measured at only 1.59x, ruled out as dominant, and left untouched.
- Implemented an in-process single-flight de-duplication in `forward_aggregates_cached`'s cache-miss path (mirroring an existing per-key-lock idiom elsewhere in the codebase); the underlying calculation itself stays byte-identical, and all three places that call it are unchanged.
- Added three new tests (same-key de-dup, concurrent-write-during-read ratio, and failure-path/no-deadlock) and validated the deadlock test by deliberately breaking the fix and confirming it correctly failed. 70/70 targeted backend tests passed, host-guard-confined.
- Ran the one authorized full-scale reproduction of the exact prior slow-down trigger; transcribed and independently re-checked every number from raw measurement files into the canonical performance record, surfacing a second, previously-unflagged 5.37s slow response and a thermal-reporting discrepancy (84°C measured vs. 64°C reported) along the way.
- Re-verified all 4 required-still-passing journeys (J-01, J-03, J-04, J-05) via browser QA this iteration (7/7 overall, 0 skipped); the 2 target journeys (J-06, J-07) remain partial, verified instead through the operator-supervised measurement pass described above.

## What's left

- Journey J-06 (Pages load only what they need) partial — the pile-up defect is fixed, but a genuinely new (never-before-cached) `/backtest` response still takes 178.74s against the committed ≤1.5s budget (~119x over), plus an unflagged 5.37s second breach.
- Journey J-07 (Heavy aggregates never take the service down) partial — the availability/memory guarantee holds (498/500 health checks OK, 36.3% memory margin, zero memory errors), but the same 178.74s slow compute keeps its responsiveness clause open, and 2 of 500 health checks saw isolated 4-second cutoffs during that compute.
- Owner decision required: choose one direction for the lingering slow `/backtest` case — add a progress/elapsed-time indicator, authorize a precompute-before-serve redesign, or formally accept/amend the budget as a disclosed constraint.
- The unflagged 5.37-second slow response (separate from the 178.74s case) is undiagnosed and needs another supervised measurement pass to investigate.
- The 84°C-vs-64°C thermal reporting discrepancy needs reconciliation given this host's crash history, even though no safety threshold was breached.
- Four sibling data-caching functions share the same unguarded concurrent-request pattern this iteration fixed for the Backtest page — disclosed, unmeasured, no live symptom reported yet.
- A first-ever 30-second timeout was observed on the Evidence page under heavy concurrent load — not yet root-caused or independently re-verified.
- Carried, unrelated: a pre-existing test failure (`tests/test_db.py::test_create_all_produces_expected_tables`), untouched by this iteration.

## Next step

Halt for an owner decision on the `/backtest` cold-compute residual. Once the owner picks a direction, resume at full depth (this is shared-infrastructure/cross-cutting, so whichever direction is chosen — a frontend affordance or an architectural precompute redesign — warrants the full audit/closure/UX-regression pipeline). No new feature work; the next iteration should carry forward the binding "do not redo" list (the single-flight fix, the resolved memory/availability guarantee, byte-identity of the underlying calculation, and the host-guard resource caps).

## Assumptions made

- iter-15 · goal-evaluator — Ambiguity: with the stacking pathology fixed, whether J-06/J-07's serve-responsiveness clause is satisfied by "stacking-fixed + honest-skeleton + warm-path-fast" (flipping both to passing → GOAL_ACHIEVED) or stays partial pending an owner decision — J-06's "assert every measurement is within budget" and the honest-status clause pull opposite directions. We chose: did NOT flip J-06/J-07 to passing on the evaluator's own authority; kept both partial and returned STALLED to route the acceptance decision to the owner, since a 119x budget breach is a real recorded violation and iter-12's human-ratified precedent kept J-06 partial rather than launder a breach into a green check. Reversible: yes
- iter-15 · goal-decomposer — Ambiguity: whether UT-04's 211.8s concurrent-cache-miss finding is a J-06 budget violation, a J-07 "honestly responsive while serving" violation, both, or neither, since neither journey's step text explicitly requires `/backtest`'s own response time to stay in budget during the concurrent warm+serve scenario. We chose: followed iter-14's evaluator, who already read UT-04 as blocking BOTH J-06 and J-07, and built this iteration's entire scope on that same reading rather than re-litigating it. Reversible: yes
- iter-14 · goal-evaluator — Ambiguity: UT-04 shows the same concurrent-load trigger that drove iter-13's REGRESSION still produces a 211.8s `/backtest` anomaly — is AG-8 resolved or still open? We chose: marked AG-8 RESOLVED — UT-04 is a latency/lock-contention regression (J-06 budget territory), not a crash/memory-exhaustion continuation (page rendered fully, health green, VmPeak flat), so kept it as a distinct non-critical follow-up and held J-06/J-07 partial on it instead. Reversible: yes
- iter-14 · goal-evaluator — Ambiguity: TC-6's literal live-induced-memory-pressure test on the SAME full-deep-basis process was not executed (the operator judged ballooning a 6GB-capped process on this two-hard-reset host an unjustified AG-10 hazard) — is TC-3's synthetic subprocess induction plus TC-5's organic MemoryError-absence enough for J-07 step 4? We chose: ruled the two-leg evidence reasonable and did not treat TC-6-partial as a hard blocker, but did not upgrade it to a literal pass either — J-07 stays partial, independently held there by UT-04 and the unproduced walkthrough too. Reversible: yes
- iter-14 · goal-decomposer — Ambiguity: the pump note said "operator-supervised" for J-07's full-basis warm + VmPeak measurement but didn't specify whether the agent runs the confined measurement itself or a human must literally type the launch command. We chose: standard path is the developer/reviewer running the confined pass directly (mirroring iter-3/8/9's own protocol), with an explicit operator-fallback only if the environment blocks the process start. Reversible: yes
- iter-14 · goal-decomposer — Ambiguity: J-07 step 4 permits either a test hook or a monkeypatched cap, but the repo's existing monkeypatch-only tests already missed iter-11's live 500s and iter-13's live wedge — does goal.md require a stricter real induction plus a concurrent-caller test? We chose: required BOTH a real (non-monkeypatched) tightened-`ulimit -v` subprocess test AND a concurrent-caller (N≥4) test mirroring iter-13's actual trigger shape — a stricter reading than the letter of step 4's permissive "or." Reversible: yes
- iter-13 · goal-evaluator — Ambiguity: whether escalating AG-8 from a "silent internal abort, zero client 500s" (iter-12) to a "full ~12-minute availability outage requiring an operator hard-restart" (iter-13) counts as newly-discovered damage (fire REGRESSION) or a re-presentation of the same carried, already-deferred bug (CONTINUE, as iters 11/12 did). We chose: fired REGRESSION — the specific "blast radius smaller, mitigation holds" justification iters 11/12 used to withhold the halt is directly falsified this iteration, and availability is the exact guarantee this ops-hardening goal exists to protect. Reversible: yes
- iter-12 · goal-evaluator — Ambiguity: decision-tree C.1 reads "an unresolved critical anti-goal → REGRESSION"; AG-8 is unresolved and fired live again (3-for-3) this iteration — read literally, C.1 halts. We chose: did NOT fire REGRESSION — the product diff is literally empty and the blast radius was smaller than iter-11 (caught internally, zero client-facing 500s vs. iter-11's two), so nothing was introduced or worsened; recorded it critical+unresolved so it still hard-blocks GOAL_ACHIEVED without repeating a halt the human had already declined four times. Reversible: yes
- iter-12 · goal-evaluator — Ambiguity: J-06's "assert every measurement is within budget" success criterion and its "honest status & anti-goals" clause (which tolerates something "slower than its budget" as long as it degrades honestly) pull in opposite directions, and `/api/indexes?full=true` was 43-51% over its ≤1.5s budget on an idle host while `/data` still rendered fully. We chose: read the budget requirement as the primary gate and the honest-status clause as a defensive AG-8-tie-in fallback, scoring J-06 `partial` rather than `passing`, rejecting the audit's "may be scored passing" recommendation. Reversible: yes
- iter-12 · goal-decomposer — Ambiguity: every decomposer since iter-4 scoped the `demo.sh ops-hardening --session-live` walkthrough out of developer scope on the reasoning that it "self-resolves automatically," but grepping every `demo-phase.sh` invocation in `run-goal.sh` found no call anywhere (including the GOAL_ACHIEVED path) that passes `--session`/`--session-live`. We chose: kept the item out of developer scope (same outcome as prior iterations) but stopped repeating the now-falsified "will self-resolve automatically" framing, recording it as a parallel open owner-decision item alongside AG-8. Reversible: yes

## Quick verify

From `reports/phase-goal-ops-hardening-iter-15-what-to-click.md`:

1. Open `http://localhost:3255/backtest` in your browser
2. Open a second browser tab and navigate to the exact same `http://localhost:3255/backtest` URL
3. Go to `http://localhost:3255/data`
4. Scroll to the "Run history" table at the very bottom of the page
5. Click into any one run's row (or its linked detail page)

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-ops-hardening-iter-15.md |
| Dev handoff | — | docs/handoffs/goal-ops-hardening-iter-15-dev.md |
| Review | PASS_WITH_NOTES | reports/reviews/goal-ops-hardening-iter-15-review.md |
| Browser QA | PASS | reports/phase-goal-ops-hardening-iter-15-ui-test-results.md |
| Implementation summary | — | reports/phase-goal-ops-hardening-iter-15-implementation-summary.md |
| User-visible changes | — | reports/phase-goal-ops-hardening-iter-15-user-visible-changes.md |
| What to click | — | reports/phase-goal-ops-hardening-iter-15-what-to-click.md |
| UI surface map | — | reports/phase-goal-ops-hardening-iter-15-ui-surface-map.md |
| UI test plan | — | reports/phase-goal-ops-hardening-iter-15-ui-test-plan.md |
| UX regression | UX-REGRESSION-WARN | reports/phase-goal-ops-hardening-iter-15-ux-regression.md |
| QA | PASS_WITH_NOTES | reports/qa/goal-ops-hardening-iter-15-qa.md |
| Audit | PASS_WITH_GAPS | docs/handoffs/goal-ops-hardening-iter-15-audit.md |
| Closure | CLOSURE-PASS | reports/phase-goal-ops-hardening-iter-15-closure-verdict.md |
| Goal evaluation | STALLED | runs/goal-session-ops-hardening/iter-15/eval.md |
| Journey history | — | runs/goal-session-ops-hardening/state/journey-history.json |
