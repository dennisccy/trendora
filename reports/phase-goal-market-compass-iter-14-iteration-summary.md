# Iteration Summary — goal-market-compass-iter-14

**Verdict:** STALLED
**Iteration type:** goal-full
**Date:** 2026-08-25
**Iteration:** 14

## In plain words

**What you can do now:** See each stock's real sector label instead of "Unassigned." Read why each next-session candidate was picked, and why others were not. The two trading days lost in the August data incident stay permanently restored in the price history. Backtesting, sector and theme views, and the methodology reference keep working the same as before.

**What changed this time:** No page or screen changed this round. Behind the scenes, the team built and ran (without executing the actual repair) the safety checks a future data-repair step will need, including a check into one stock's (AVB) unusual price-and-volume numbers. They also made the tool that already cleaned up old repair records safer — it now refuses to run unless told exactly where to save its records — closing a mistake this same round of work made, caught, and fixed before it shipped.

**What's next:** Next, the owner needs to decide how to settle one stock's (AVB) untested trading-volume question — by allowing a small one-time check, accepting the risk in writing, fixing the check first, or changing the rule — before the actual data repair can be authorized.

## Headline

Stage D readiness hardening delivered; evaluator overturns AVB-B to AVB-D, so Stage D stays NOT READY

## Direction

**Signal:** regressing
**Why:** A CRITICAL anti-goal breach (AG-17/C5) occurred this iteration — a new test overwrote three committed iteration-13 evidence files after falling back to a live default path; it was caught, fully reversed byte-for-byte, and the specific script was hardened, but the audit found the identical footgun pattern still lives in two more scripts that default into this iteration's own evidence folder, which currently has zero files tracked in git. On top of that, the evaluator independently re-derived the AVB diagnostic and overturned the developer's, reviewer's, QA's and auditor's shared AVB-B ("ready") classification to AVB-D ("evidence insufficient"), so the iteration's own headline "STAGE D READY: YES" does not stand. No journey itself regressed and nothing was lost, but a real process fault recurred (echoing iteration 8's precedent) and the central technical claim this iteration was built to prove did not survive independent scrutiny — that combination reads regressing rather than holding.

**Trend (last 3 iters):**
- Newly passing this iter: none
- Newly passing in last 3 iters total: none
- Regressions in last 3 iters: none (no journey's status flipped to `regressed` in iters 12–14)
- Anti-goal violations in last 3 iters: 1 critical (iter-14 AG-17/C5 — a new CLI test overwrote committed evidence, caught and fully reversed in-iteration)
- Iters with no journey state change: 3 of 3 (J-11 stayed `partial` in iters 12, 13 and 14 even though its underlying stage evidence advanced each time — Stage B1 complete → Stage C complete → Stage D built-but-not-ready)

**Latest evaluator reasoning:** "This iteration built the five things the owner asked for, wrote nothing to the real database, and I checked that myself: the database file has the same timestamp, the same size and an empty write log that it had when the last iteration finished. Four of the five pieces are sound. The fifth — the check on the share-trading numbers for one company, AVB — answers a price-and-volume question using price alone, and its own answer file says the matter is "proven" when only half of it was tested. The owner's own rule says that half-tested state must produce a "not ready" answer, so the iteration's headline "ready: yes" does not stand."

## What was done

- Product changes: apps/backend/app/engine/j11_stage_d.py, apps/backend/app/engine/j11_avb_diagnostic.py, apps/backend/scripts/run_j11_avb_bridge_diagnostic.py, apps/backend/scripts/run_j11_stage_d_preflight.py, apps/backend/scripts/run_j11_stage_c_bounded_clear.py, apps/backend/tests/test_j11_stage_d.py, apps/backend/tests/test_j11_stage_c_preflight.py, apps/backend/tests/test_j11_stage_c_cli_script.py, apps/backend/tests/test_j11_avb_diagnostic.py
- Froze a fresh Stage D attempt identity (recomputed live, not inherited from any earlier attempt) and persisted it to `runs/goal-market-compass-iter-14/j11-stage-d-attempt-identity.json`
- Built three fail-closed identity COMPARE checks (before-first-write, before-each-date, after-persist) that reuse the existing comparison primitive rather than reimplementing it; unit-tested only, not yet wired into a live Stage D loop
- Ran the Stage D preflight gate live, read-only, against the real database: all 11 checks pass (11 incident dates hold zero ScannerRuns, canonical inputs/manifests unchanged, fresh identity matches, date set agrees with goal.md)
- Added the missing negative/precondition tests for the Stage C/D safety skeleton (92 targeted tests total, up from 91)
- Built a read-only AVB bridge/volume diagnostic; the developer, reviewer, QA and auditor all classified it AVB-B ("ready"), but the evaluator overturned this to AVB-D ("evidence insufficient") because the classifier never actually reads trading volume
- Caught, in-iteration, a critical anti-goal breach: a new test overwrote three committed iteration-13 evidence files by falling back to a live default path; restored byte-for-byte from git, root cause fixed (the CLI now refuses to run without an explicit output folder), and the handoff's wrong first explanation was retracted by name
- Proved zero writes to the live 8.4 GB database across the whole iteration (identical mtime/size and an empty write-ahead log at true start and true end)

## What's left

- Journey J-07 "The Today page answers the ten-second read" failing — long-standing, out of scope until Stage G reopens the browser lane
- Journey J-08 "Market page moves over intact and history stays honest" failing — same, targeted first when Stage G reopens
- J-11 Stage D is called ready by every lane except the evaluator, who overturned the AVB classification to "evidence insufficient" — the owner must decide how to resolve the untested AVB trading-volume question before Stage D can even be authorized
- Stage D itself (and Stages E, F, G) remain unauthorized regardless of the AVB question — a separate, explicit owner instruction is required either way
- This iteration's evidence artifacts and new code are not yet committed to git — two of this iteration's own scripts write into that same untracked folder by default, the exact class of footgun that already caused this iteration's AG-17 breach
- The headline `j11-stage-d-readiness.json` verdict file has no committed producer script — it was hand-run, not reproducible from committed code
- Nine of the eleven Stage D preflight-gate checks have no committed negative test (the auditor verified all eleven fire on drift by hand, but the coverage gap remains)
- Five older, non-blocking owner questions remain open (J-09's 3.44 GB memory figure; J-06's "underlying run unavailable" wording; J-01's first-two-test-steps wording; whether an empty "next-session focus" is acceptable; whether MNST joins the recovery list)

## Next step

One decision is needed from the owner about one company's (AVB) trading-volume numbers on two days. The AVB diagnostic's own answer file calls the price/volume convention "proven," but its classifier never actually reads volume — only price — so the honest state is "not enough evidence," which the owner's own rule turns into "not ready." Pick one: (a) authorize a small, bounded, read-only comparison download (one symbol, a few already-stored days, volume only) — needs a dated goal.md amendment since the earlier download permission is used up; (b) accept the residual in writing, with a caveat on record — the worst case moves AVB's 63-day average dollar volume from about $215M to about $193M against a $50M floor, so admission, risk grade and "Avoid" status all stay the same, and only 2 of the 11 rebuild dates are affected; (c) order the honesty fix first (feed volume into the classifier, make the missing label reachable, give the readiness file a real producer, port the missing negative tests) — costs nothing but cannot change the answer; or (d) reword the gate so a volume question this small does not block the rebuild. Whichever is chosen, Stage D itself still needs a separate, fresh owner instruction, and two mechanical items ride along: get this iteration's evidence and code into version control (several of its own scripts write into that same untracked folder by default), and record 12 August as a caveat on rebuilt output since it is AVB's third-busiest day in 21 years of stored history.

## Assumptions made

- iter-14 · goal-evaluator — Ambiguity: With Stage C's owner-inspection gate already spent, tractable non-destructive hardening work exists (close the AVB classifier gap, give the readiness file a producer, port missing tests, commit artifacts), which reads like CONTINUE. We chose: STALLED anyway — that work cannot change the AVB-D answer, every path that actually clears the gate is owner-owned (a new AG-9 amendment, a dated acceptance, or a reworded gate), and Stage D itself still needs a separate fresh owner instruction. Reversible: yes.
- iter-14 · goal-evaluator — Ambiguity: A new test overwrote three committed Stage C evidence files (an AG-17-class act) but was caught and fully reversed within the same iteration; goal.md doesn't say whether a caught-and-reversed violation belongs in the ledger, and a critical+unresolved pair would force a REGRESSION halt. We chose: record it as critical, resolved: true, with the mechanism and restoration proof preserved verbatim — omitting it would be dishonest, and the restoration is independently confirmed (git status clean). Reversible: yes.
- iter-14 · goal-evaluator — Ambiguity: Whether "AVB-B" (internally consistent) can be established from the bridge transform's code and contract text, or must be established from actually measuring the stored series' volume; the developer, reviewer, QA and auditor all landed on AVB-B despite the auditor noting it looked like "AVB-D territory." We chose: AVB-D ("evidence insufficient") — the classifier never reads volume, its rescuing arguments don't survive checking, and the evaluator's own read-only statistics lean the other way. Reversible: yes — one bounded read-only comparison fetch, or a dated owner acceptance, settles it either way; nothing is mutated.
- iter-14 · goal-decomposer — Ambiguity: How to obtain a "raw provider close" for the AVB diagnostic's counterfactual B without a new network fetch (AG-9's exception is exhausted). We chose: derive it arithmetically as stored_close / bridge_factor, since the bridge was a single scalar multiply verified never applied to volume. Reversible: yes — a read-only arithmetic choice; if the developer's re-derivation disagrees, the spec requires reporting the correction.
- iter-14 · goal-decomposer — Ambiguity: Whether closing the iteration-13 auditor's "captures but never compares identity" finding means patching the already-executed Stage C code or building new Stage D code. We chose: build entirely new Stage D code and leave Stage C's completed, audited code untouched — the blind spot was always inert for Stage C (it deletes nothing that reads identity) and only matters for Stage D. Reversible: yes.
- iter-13 · goal-evaluator — Ambiguity: J-11's status vocabulary has no way to say "one of seven stages delivered cleanly"; `partial` reads weaker than a fully verified Stage C completion. We chose: kept the label `partial` but rewrote the gap text to state plainly that Stage C is complete while D–G are not — recording progress in the text a human reads, not by inflating the machine-parsed status. Reversible: yes.
- iter-13 · goal-evaluator — Ambiguity: With the owner's Stage-C inspection gate answered, tractable non-Stage-D hardening work existed, reading like CONTINUE. We chose: STALLED anyway — ruling C10 is a direct instruction to stop the engine for owner inspection first, and the hardening work loses nothing by waiting one owner message while CONTINUE cannot be un-run. Reversible: yes.
- iter-13 · auditor CORRECTION — Ambiguity/finding: two iter-13 assumption-ledger entries rested on factual premises the live database contradicts (the re-derived engine identity was assumed unchanged since iter-10; a forward-return population was assumed already absent). We chose: file an additive correction preserving the originals verbatim — the decisions were correct and correctly implemented, only the stated premises were wrong; now flagged as Stage D preconditions. Reversible: yes — corrects two facts and names one precondition; nothing in iteration-13's delivered code changes.
- iter-13 · goal-decomposer — Ambiguity: Whether a "Stage C attempt identity" (ruling C2) is a brand-new identifier or the same engine identity already frozen earlier, since goal.md doesn't define its contents. We chose: treat it as a new bookkeeping identifier that wraps and re-asserts the same engine identity — later found at audit to have actually drifted from the certified value, which developer/reviewer/QA all missed but the auditor caught. Reversible: yes — purely an evidence-artifact naming/structuring choice.

## Quick verify

From `reports/phase-goal-market-compass-iter-14-what-to-click.md`:

1. Open `runs/goal-market-compass-iter-14/j11-stage-d-readiness.json`
2. Open `docs/handoffs/goal-market-compass-iter-14-dev.md` and search for the text `STAGE D READY`
3. Open `runs/goal-market-compass-iter-14/j11-stage-d-attempt-identity.json`
4. Open `runs/goal-market-compass-iter-14/j11-stage-d-preflight-gate.json`
5. Open `runs/goal-market-compass-iter-14/j11-avb-bridge-diagnostic.json`

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-market-compass-iter-14.md |
| Dev handoff | — | docs/handoffs/goal-market-compass-iter-14-dev.md |
| Review | PASS_WITH_NOTES | reports/reviews/goal-market-compass-iter-14-review.md |
| Browser QA | SKIPPED | reports/phase-goal-market-compass-iter-14-ui-test-results.md |
| Implementation summary | — | reports/phase-goal-market-compass-iter-14-implementation-summary.md |
| User-visible changes | — | reports/phase-goal-market-compass-iter-14-user-visible-changes.md |
| What to click | — | reports/phase-goal-market-compass-iter-14-what-to-click.md |
| UI surface map | — | reports/phase-goal-market-compass-iter-14-ui-surface-map.md |
| UI test plan | — | reports/phase-goal-market-compass-iter-14-ui-test-plan.md |
| QA | PASS | reports/qa/goal-market-compass-iter-14-qa.md |
| Audit | PASS_WITH_GAPS | docs/handoffs/goal-market-compass-iter-14-audit.md |
| Closure | CLOSURE-PASS | reports/phase-goal-market-compass-iter-14-closure-verdict.md |
| Goal evaluation | STALLED | runs/goal-session-market-compass/iter-14/eval.md |
| Journey history | — | runs/goal-session-market-compass/state/journey-history.json |
