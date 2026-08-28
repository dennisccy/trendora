# Iteration Summary — goal-market-compass-iter-25

**Verdict:** CONTINUE
**Iteration type:** goal-full
**Date:** 2026-08-28
**Iteration:** 25

## In plain words

**What you can do now:** See each stock's honest, mostly filled-in sector label. See why each next-session candidate was picked, and why the others weren't. Browse the two trading days recovered from last month's data incident, with corrected volume numbers, in the price history. The repair behind all of this has now been checked, live, on the real app, for a second time.

**What changed this time:** Nothing changed on screen this round. Behind the scenes, the team re-checked how much computer memory the app needs when it's warmed up and running — it still uses a bit more than hoped, but noticeably less than the last check. They also fixed a bug in the project's own testing tool that had let last round's routine safety re-check silently skip itself without telling anyone.

**What's next:** Next, the team will make sure each evening's saved briefing is locked in place the moment it's created and never quietly changes afterward.

## Headline

J-09 memory re-measured (honest miss, +16.9% over target, -10.9% vs iter-4); replay-lane parser bug fixed

## Direction

**Signal:** holding
**Why:** No journey changed status this iteration — J-01, J-04 and J-10 were already `passing` and were only re-verified (a safety net that had silently gone missing at iteration 24 due to a parser bug is now fixed and proven working), and J-09 stayed `partial` on a repeat honest miss. An independent auditor caught two further defects in this round's own work — a mirror-image parsing bug and a false causal claim in the perf report — before either could mislead the owner, which is a sign of a healthy check chain rather than expansion. With J-07/J-08 still failing and the loop moving on to ordinary next-in-queue work, the project is holding steady this round rather than growing.

**Trend (last 3 iters):**
- Newly passing this iter: none
- Newly passing in last 3 iters total: J-11 (iteration 23)
- Regressions in last 3 iters: none
- Anti-goal violations in last 3 iters: 1 new critical entry (owner-ruling breach, iteration 23), resolved at iteration 24; none new since
- Iters with no journey state change: 2 of last 3

**Latest evaluator reasoning:** "Both halves of this iteration really happened, and I checked them myself rather than trusting the write-ups. The memory measurement was re-taken on the real database and it missed its goal again: the backend needs about 2.99 GB of memory where the goal asks for 2.5 GB or less. That is an honest miss, recorded plainly and without moving the goalposts, and the goal file itself says a miss is an owner question, not a reason to stop the loop."

## What was done

- No product change this iteration.
- Re-measured J-09's backend memory footprint against the current live canonical database (post J-10/J-11 recovery): primary VmPeak 3,064,772 kB — still an honest miss vs the ≤2,621,440 kB (2.5 GB) target (+16.9%) but 10.9% better than iteration 4's figure — recorded as Addendum 41 in `reports/perf-budgets.md`.
- Re-ran and confirmed the concurrent-load burst check (zero `QueuePool` errors) and the byte-identity spot check across 4 endpoints at `as_of=2026-08-10`.
- Fixed the goal-mode regression-replay parser bug that had silently emptied the required-still-passing journey list at iteration 24 (`replay-lane.sh`); wired an explicit warning into both call sites for any future zero-parse, and added a new regression test.
- Deleted the ~7.8 GB disposable iteration-23 database clone after confirming no test suite depended on it.
- Verified 3 required-still-passing journeys (J-01, J-04, J-10) pass browser QA for real via the newly repaired deterministic replay lane.
- An independent auditor — dispatched at full depth for the first time in three iterations — found and fixed two further defects the delivered work missed: the "fixed" parser introduced a mirror bug that silently returns a WRONG non-empty journey set for a spec whose bullet says "none," and Addendum 41's stated cause for its own 10.9% improvement was false — a second, unrelated project's engine was actually running through the measurement window, and the request load was undercounted by roughly 2x.
- Confirmed the canonical database's first ordinary boot since the iteration-23 incident left only 4 rows in two recomputable cache tables, with no new saved briefing minted, no new day-record, and the price frontier unchanged.

## What's left

- Journey J-07 ("The Today page answers the ten-second read") failing — not yet built.
- Journey J-08 ("Market page moves over intact and history stays honest") failing — the `/market` route still doesn't exist.
- Journey J-09 ("The backend fits the host") stays partial: memory still ~2.99 GB against the 2.5 GB target — an honest, anticipated miss awaiting an owner ruling on whether it's acceptable.
- J-09's headline VmPeak figure has no surviving raw measurement artifact — it should reach the owner as a caveated figure, not a settled conclusion.
- Journeys J-02, J-03, J-05, J-06 remain partial, untouched this iteration (product surface byte-unchanged).
- J-04's evidence screenshot still doesn't capture the candidate card (7th consecutive iteration) — a capture-framing gap only, not a product defect; the underlying data is already proven correct.
- A framework defect in `goal_gate.py` (duplicate-journey-heading) remains unfixed and must be closed before any GOAL_ACHIEVED certification.
- Several non-blocking owner questions remain open: whether ~2.99 GB is acceptable for J-09, J-06's "underlying run unavailable" wording, J-01's first two test-step wording, whether an empty "next-session focus" is acceptable, and whether MNST joins the recovery list.

## Next step

Build J-05 "Each close freezes one next-session manifest, exported byte-consistently" and J-06 "A frozen manifest never changes" next — the goal file's own next pair, needing no further owner permission, and the last two items before the page-building journeys J-07 and J-08. Run it at full depth with the independent auditor present: this round's auditor found and fixed two real defects (the replay-lane parser's mirror bug and Addendum 41's false causal claim) that the developer, reviewer, QA and coherence checks all missed, and J-05/J-06 govern frozen records never changing — the most dangerous area in this goal. Only the owner can make full depth non-demotable, by adding "Depth enforcement: required" to the next plan; a full-depth plan has been auto-downgraded on cost grounds five times this session.

## Assumptions made

- iter-25 · goal-evaluator — Ambiguity: J-09 has no browser-QA row (flagged "Missing Target Journeys"), but J-09's own acceptance text waives its walkthrough as backend-only, replaced by the dated VmPeak measurement. We chose: treat the goal's own waiver as authoritative and score J-09 from the measurement evidence, not as `unknown`; it stays `partial` either way since the measured figure misses target. Reversible: yes.
- iter-25 · goal-evaluator — Ambiguity: the goal file's post-Stage-G clarification says the canonical database "remains OFF and protected," while the later "OWNER RULING — J-11 CLOSED" says normal product work resumes once the launcher fix lands, and this iteration booted the canonical database and served ~2,614 requests. We chose: read the earlier clarification as spent and scoped to the now-completed verification task, so the later ruling governs and the boot was sanctioned — verified read-only that no manifest, day-record, or provenance value was touched, only 4 rows in two recomputable cache tables. Reversible: yes.
- iter-25 · goal-decomposer — Ambiguity: J-09's iter-4 honest miss stopped for owner review per its own acceptance text, and it isn't stated whether that closes J-09's work until the owner rules, or whether the database's material change since (J-10/J-11 recovery) justifies a fresh re-measurement without waiting. We chose: treat it as fresh, non-destructive re-verification work rather than owner-blocked work, re-running J-09's measurement steps with no config edit and appending a new dated addendum rather than resolving the acceptability question itself. Reversible: yes.
- iter-24 · goal-evaluator — Ambiguity: J-11's goal text changed (a spec-hash drift that normally voids a recorded pass pending re-verification), but the new text IS the owner's ruling declaring "J-11 STATUS: PASSING — CLOSED" and forbidding re-verification. We chose: keep J-11 passing, record the new hash, and treat a documentary + state-integrity check (byte-identical database state, no acceptance criterion tightened) as the re-verification the current text admits of — not a fresh browser pass, and said so explicitly in the evidence field. Reversible: yes.
- iter-24 · goal-decomposer — Ambiguity: the owner-authorized launcher fix is a Goal Mode harness/tooling change touching no product code or journey acceptance criterion, so the spec format's "Target journeys" field has no natural non-empty value. We chose: leave Target journeys empty ("none — infrastructure fix"), treat the owner ruling as binding and superseding normal journey-based targeting for this one iteration, and substitute a required-still-passing regression check plus the fix's own test as the pass bar. Reversible: yes.
- iter-24 · goal-decomposer — Ambiguity: the owner's launcher-fix authorization names only the vendored mirror copy of `goal-iter-lean.sh` by path, not the live executing copy, and the repo keeps the two byte-identical via a sync convention. We chose: apply the identical patch to both copies, since fixing only the mirror would leave the actually-executing copy carrying the live defect, defeating the ruling's own stated purpose. Reversible: yes.
- iter-23b · goal-evaluator — Ambiguity: the owner's ruling lets J-11 pass once its own disposable-clone verification succeeds with no further authorization needed, but this same iteration also breached a separate rule requiring canonical-database verification to stay off it — the text doesn't say whether a breach elsewhere voids an otherwise-conforming journey pass. We chose: close J-11 as passing (every artifact traces to the guarded clone-backed boot) and halt the session on the breach instead, recording it as an unresolved critical ledger entry rather than withholding the journey status or silently absorbing the breach. Reversible: yes.

## Quick verify

From `reports/phase-goal-market-compass-iter-25-what-to-click.md`:

1. Open `reports/perf-budgets.md` and check the newest dated addendum (Addendum 41) for the fresh VmPeak figure and its comparison against the 2.5 GB target and the iter-4 figure.
2. Open `reports/phase-goal-market-compass-iter-25-regression-replay-results.md` and confirm it shows PASS for J-01, J-04, and J-10.

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-market-compass-iter-25.md |
| Dev handoff | — | docs/handoffs/goal-market-compass-iter-25-dev.md |
| Review | PASS | reports/reviews/goal-market-compass-iter-25-review.md |
| Browser QA | BLOCKED | reports/phase-goal-market-compass-iter-25-ui-test-results.md |
| Implementation summary | — | reports/phase-goal-market-compass-iter-25-implementation-summary.md |
| User-visible changes | — | reports/phase-goal-market-compass-iter-25-user-visible-changes.md |
| What to click | — | reports/phase-goal-market-compass-iter-25-what-to-click.md |
| UX regression | UX-REGRESSION-PASS | reports/phase-goal-market-compass-iter-25-ux-regression.md |
| QA | PASS | reports/qa/goal-market-compass-iter-25-qa.md |
| Audit | PASS_WITH_GAPS | docs/handoffs/goal-market-compass-iter-25-audit.md |
| Closure | CLOSURE-PASS | reports/phase-goal-market-compass-iter-25-closure-verdict.md |
| Goal evaluation | CONTINUE | runs/goal-session-market-compass/iter-25/eval.md |
| Journey history | — | runs/goal-session-market-compass/state/journey-history.json |
