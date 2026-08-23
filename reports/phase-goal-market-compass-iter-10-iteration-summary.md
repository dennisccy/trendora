# Iteration Summary — goal-market-compass-iter-10

**Verdict:** STALLED
**Iteration type:** goal-full
**Date:** 2026-08-23
**Iteration:** 10

## In plain words

**What you can do now:** See honest sector labels on every new scan, read why each next-session candidate was picked and why others weren't, and trust that the two trading days lost in the August data incident are back in the price history.

**What changed this time:** Nothing changed on any screen — this work was entirely behind the scenes. The team built and tested new internal safety-check tools: one takes a complete "before" snapshot of the data the eventual cleanup will touch, and the other freezes a single fingerprint of today's calculation rules so a future rebuild can prove it used one consistent recipe throughout. The tools also corrected an old, incorrect claim buried in the database's own code about how two of its tables relate.

**What's next:** The product owner needs to make one small call about a technical safety detail in the database before the big cleanup of the two affected pages can start. Once that's decided, the team will finish rebuilding the daily summary and "what changed" pages so they reflect the now-restored prices.

## Headline

J-11 safety checks built and proven; two of six required proofs still fail on the real database

## Direction

**Signal:** holding
**Why:** This iteration made genuine, independently-verified progress (J-11 unknown → partial) with zero regressions and no new anti-goal violations, continuing three straight iterations (8, 9, 10) of real forward movement, with the forbidden browser/replay lane suppressed each time. But the iteration's own verdict is STALLED: the audit found two of J-11's six required safety proofs still false on the live database, and every unblock path is an owner-only decision, so the eight other unfinished journeys (J-02, J-03, J-05–J-09) stay legally frozen behind the Loop-mechanics gate until Stage C's precondition is resolved.

**Trend (last 4 iters):**
- Newly passing this iter: none
- Newly passing in last 4 iters total: J-10 (iter-9)
- Regressions in last 4 iters: none
- Anti-goal violations in last 4 iters: 2 critical, both found and fixed inside the same iteration (AG-9 iter-7, AG-17 iter-8); 0 new in iter-9 and iter-10
- Iters with no journey state change: 2 of last 4 (iter-7 and iter-8 advanced J-10 materially within `partial`, without a formal status flip)

**Latest evaluator reasoning:** This iteration built the safety checks that must pass before the big repair job may start, and they did their job: they showed the repair is not yet allowed to begin. The stock-price record was measured in full and the measurements are correct — I re-checked every number myself against the live database, reading only, and they all matched. But the goal file says the repair may not start until six safety points are proven, and two of them are still false on the real database. Nobody on the team can fix those two without a decision from the owner, and the goal file itself says to stop and ask in exactly this situation.

## What was done

- Product changes: apps/backend/app/models.py, apps/backend/app/engine/j11_maintenance.py, apps/backend/scripts/run_j11_pre_reset_inventory.py, apps/backend/tests/test_j11_maintenance.py
- Captured a read-only "before" snapshot of all 11 incident dates (row counts, manifest hashes, `daily_prices` totals) as the safety baseline for the future derived-data rebuild.
- Froze a single fingerprint of today's calculation code and config so a future rebuild can prove every date used the same version.
- Corrected the database's declared (but never-enforced) manifest-to-scan-run link to match reality — a documentation-level fix only, no live data touched.
- Added 9 new fixture-DB tests (all passing); reran 37 manifest-invariant tests and 50 J-10 recovery tests with no regressions.
- Independently proved the 7.8 GB live database received zero writes throughout the iteration (mtime/size unchanged before and after).
- No browser QA or replay lane ran — maintenance isolation held for the second iteration running (0 journeys re-verified via browser).

## What's left

- Journey J-07 ("The Today page answers the ten-second read") failing — never in scope this iteration, never yet passed.
- Journey J-08 ("Market page moves over intact and history stays honest") failing — never in scope this iteration, never yet passed.
- J-11 Stage C (the destructive derived-state clear) is blocked: two of six required safety proofs are still false on the live database — a switched-off-but-not-removed link between manifests and scan runs, and 12 existing rows that already violate it. Needs an owner decision before it can proceed.
- J-02 ("What changed since the previous session") and J-03 ("Plain-English summary with cited facts") still compute from the pre-repair, incomplete data basis until J-11 Stage G rebuilds them.
- A live bug the audit found: one recovered day's manifest wrongly reports "original basis intact" when it should say "rebuilt" — parked for the Stage C/D/G iteration, not yet fixed.
- J-05 and J-06 (manifest-freezing journeys) and J-09 (backend memory budget) remain partial, all gated behind the same J-11 Stage G lane freeze.
- Five older owner questions remain open and non-blocking (the J-09 memory-budget acceptance, J-06 wording, J-01 test-step rewording, an empty next-session-focus question, and whether MNST joins the recovery list).

## Next step

One decision is needed from the owner before any further repair work: the live database still declares an inert link between decision manifests and scan runs that the safety gate requires proven-clean, and twelve existing rows already violate it. Pick one of three paths — accept the current state in writing with a dated note, authorise a bounded rewrite of that 24-row table (a real write to the 7.8 GB database, needing its own single-writer isolation), or reword the gate so it checks the table the rebuild creates from current code rather than the one on disk. Once decided, the next iteration should run the full repair (Stages C–G) alone, at full depth, with no web server, no browser tests, and one writer only — carrying three fixes along: correct the manifest that falsely claims its original data is intact, open the database in a genuinely read-only mode for future inventories, and add a check that every rebuilt day used one single version of the code.

## Assumptions made

- iter-10 · goal-evaluator — Ambiguity: this iteration made real, verified progress (J-11 unknown → partial), which reads CONTINUE on the surface, but the blocker's only unblock paths are owner-only decisions, two of them irreversible-write class. We chose: STALLED — the goal file itself prescribes "STOP before J-11 and surface it as an owner decision," and no other journey may legally be worked on meanwhile. Reversible: yes.
- iter-10 · goal-evaluator — Ambiguity: J-11 spans Stages A–G; this iteration delivered Stages B and B2 in full but B1 only partly (two of six Stage C preconditions are false on the live database) — is that `partial` or `unknown`? We chose: `partial` — a named, contractually-required inventory artifact exists and was independently re-verified, so `unknown` would be dishonest; this is not a promotion to passing, so the isolation rail is not crossed. Reversible: yes.
- iter-10 · goal-decomposer — Ambiguity: `docs/goal.md` describes J-11's Stages A–G as one journey and says "the unit of work is the whole 11-date set," but that unit is explicitly scoped to the destructive phase (Stage C onward); it doesn't say whether the read-only Stages B/B1/B2 must ship with C-G. We chose: scoped this iteration to Stages B/B1/B2 only (zero writes to the database), deferring the destructive Stages C-G — mirroring how J-10 was safely chunked across iterations 7-9. Reversible: yes.
- iter-9 · goal-evaluator — Ambiguity: this iteration moved the recovery basis further (20→585 symbols) and created a genuinely mixed derived basis under J-01/J-04, but maintenance isolation forbids any lane that could measure the risk. We chose: kept J-01 and J-04 at `passing`, unchanged, and recorded the enlarged mixed-basis risk explicitly rather than inventing a downgrade; both will be re-measured at J-11 Stage G. Reversible: yes.
- iter-9 · goal-evaluator — Ambiguity: the maintenance-isolation rule says no journey may be promoted to `passing` on an iteration with no browser evidence, but J-10's walkthrough is explicitly waived by `docs/goal.md` in favor of a named substitute evidence set. We chose: promoted J-10 to `passing` — the rail exists to stop promotion on absent evidence, and J-10's required evidence is not absent; all four named artifacts exist and were independently re-derived from primary sources. Reversible: yes.
- iter-9 · goal-decomposer — Ambiguity: `docs/goal.md`'s J-10 Completion rule requires every recovery-population symbol to end up restored or explicitly classified, but doesn't state whether that terminal state must be reached inside a single iteration. We chose: set this iteration's target as full population coverage — every remaining symbol attempted this iteration — while allowing a named, externally-caused residual rather than requiring literal 100% success regardless of cause. Reversible: yes.
- iter-8 · goal-evaluator — Ambiguity: AG-17 (critical) was genuinely breached this iteration by a forbidden replay lane overwriting quarantined evidence, but the instance damage was repaired in-iteration while the root cause stayed live. We chose: scored it resolved and returned CONTINUE rather than REGRESSION, since the product/artifacts were verified byte-for-byte restored; the unfixed cause was made the first item of the next-step recommendation instead. Reversible: yes.
- iter-8 · goal-evaluator — Ambiguity: J-01/J-04's iter-4 evidence formally still holds under evidence durability since no frontend/scoring file changed, but the live "Latest" data basis moved to a 20-of-587-symbol recovery-era layer `docs/goal.md` itself calls non-authoritative. We chose: kept both at `passing`, unchanged, rather than downgrading on reasoning alone — no positive evidence of breakage exists, and J-11 Stage G is named as the exclusive place to re-measure both. Reversible: yes.

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-market-compass-iter-10.md |
| Dev handoff | — | docs/handoffs/goal-market-compass-iter-10-dev.md |
| Review | PASS | reports/reviews/goal-market-compass-iter-10-review.md |
| Browser QA | SKIPPED | reports/phase-goal-market-compass-iter-10-ui-test-results.md |
| Implementation summary | — | reports/phase-goal-market-compass-iter-10-implementation-summary.md |
| User-visible changes | — | reports/phase-goal-market-compass-iter-10-user-visible-changes.md |
| What to click | — | reports/phase-goal-market-compass-iter-10-what-to-click.md |
| QA | PASS | reports/qa/goal-market-compass-iter-10-qa.md |
| Audit | PASS_WITH_GAPS | docs/handoffs/goal-market-compass-iter-10-audit.md |
| Closure | CLOSURE-PASS | reports/phase-goal-market-compass-iter-10-closure-verdict.md |
| Goal evaluation | STALLED | runs/goal-session-market-compass/iter-10/eval.md |
| Journey history | — | runs/goal-session-market-compass/state/journey-history.json |
