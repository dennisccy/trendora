# Iteration Summary — goal-market-compass-iter-23

**Verdict:** STALLED
**Iteration type:** goal-lean
**Date:** 2026-08-27
**Iteration:** 23

## In plain words

**What you can do now:** See each stock's sector label, honestly filled in for nearly every stock. See why each pick for tomorrow's watchlist was chosen — or passed over — with a plain reason. Look up the two trading days lost in August's data problem and see their corrected volume numbers. And, new this round: trust that the whole data-repair effort — not just those two days — has been proven to show up correctly on screen, not just sit correctly in the database.

**What changed this time:** The Today page was switched back on for a supervised test — the first time in many weeks — using a safe practice copy of the database, and it correctly showed the recovered trading days and the latest numbers. That finishes the long data-repair project. At the same time, a mistake in the automated test tooling briefly started a second, unauthorized copy of the app against the real, protected data and added a handful of small, harmless recalculated entries to it. Nothing important was lost or changed, but the team is pausing to get this properly fixed before doing more.

**What's next:** The owner needs to decide what to do with those accidental entries in the protected data and approve a fix so this mix-up can't happen again — only then can work resume, starting with the "backend fits the host" and manifest-freezing pieces.

## Headline

J-11 serving verification passed on a clone; the protected database was also booted by mistake

## Direction

**Signal:** regressing
**Why:** J-11 closed this iteration after real serving verification passed cleanly on a disposable database clone, and three other journeys (J-01, J-04, J-10) re-verified passing with no regressions. But a harness defect also let the regression-replay lane boot the real protected canonical database instead of the clone, writing 10 rows into five cache tables there — a critical, unresolved breach of the owner's written protection rule, still open at scoring time. No enumerated anti-goal (AG-1..18) was actually broken and no journey moved backward, but the severity of this unresolved breach is why this summary marks the iteration's direction as regressing rather than holding, pending the owner's decision on remediation.

**Trend (last 2 iters):**
- Newly passing this iter: J-11
- Newly passing in last 2 iters total: J-11
- Regressions in last 2 iters: none
- Anti-goal violations in last 2 iters: 1 critical (iter-23 — owner-ruling breach: canonical database booted and written to; not one of the enumerated AG-1..18, but recorded as an unresolved critical ledger entry)
- Iters with no journey state change: 1 of last 2 (iter-22; J-11 stayed `partial` that round)

**Latest evaluator reasoning:** "The one job the owner asked for is done, and it worked. The repaired data was copied to a throw-away copy of the database, the real app was started against that copy, and the pages served the repaired days correctly — I opened the pictures myself and checked the numbers against the database, read-only. J-11 'Repair the damaged saved results' can close. But while that was happening, something else went wrong that nobody in the pipeline noticed."

## What was done

- Product changes: apps/backend/app/engine/j11_disposable_clone.py, apps/backend/scripts/run_j11_disposable_clone.py, scripts/start-backend-j11-verify.sh, apps/backend/tests/test_j11_disposable_clone.py, apps/backend/tests/test_j11_disposable_clone_cli_script.py
- Built disposable-clone tooling (SQLite online-backup clone creation, provenance/checksum capture, a verification-only config builder) plus a launch guard that refuses to boot unless pointed away from the canonical database.
- Ran a live `--confirm` clone of the real 8.4 GB canonical database; proved the canonical file byte-unchanged (sha256-identical) both immediately after cloning and at the end of the whole verification window.
- Booted real backend + frontend against the disposable clone and ran the goal.md ruling item 4 minimum live-HTTP verification — every check passed with zero unacceptable canonical-data-contract side effects (only 5 cache tables warmed from their existing producers).
- 27/27 new tests pass; review verdict PASS_WITH_NOTES (one MINOR: two handoff claims lack a persisted evidence JSON).
- Verified 4/4 target and required-still-passing journeys pass browser QA: J-11 (target), J-01, J-04, J-10.
- Evaluator independently discovered and recorded a critical incident: the same iteration's regression-replay lane booted the real protected database (via a harness gap in `scripts/automation/goal-iter-lean.sh`) and wrote 10 rows into 5 derived cache tables there — logged as an unresolved critical ledger entry.

## What's left

- Journey J-07 "The Today page answers the ten-second read" — failing, not tested this iteration (out of scope).
- Journey J-08 "Market page moves over intact and history stays honest" — failing; the `/market` route still doesn't exist (re-confirmed 404).
- Journeys J-02, J-03, J-05, J-06, J-09 remain `partial` — not re-tested this iteration (explicitly out of scope per owner ruling).
- Unresolved critical incident: the real protected database was booted and written to; 10 scratch-cache rows now sit there awaiting an owner decision (keep or remove).
- The harness defect that caused the incident (`scripts/automation/goal-iter-lean.sh` missing a database override) is still unfixed and needs owner authorization.
- The 7.8 GB disposable clone and its verification config are still on disk (`runs/goal-market-compass-iter-23/verify-clone/`) and need cleanup.
- The J-02/J-03 repaired-state replay named in J-11's own acceptance text was never run.
- J-04's screenshot still crops above the "Next-session focus" card and needs re-capturing.
- `goal_gate.py`'s duplicate-journey-heading defect remains unfixed and must close before any GOAL_ACHIEVED certification.

## Next step

Ask the owner three questions before anything else runs. First, what to do with the ten scratch rows now sitting in the protected canonical database — leave them (they're correct and harmless) or remove them (which means writing to that database again). Second, whether the automation may be fixed so the app can never boot against the real database again — the defect is one missing config line in the regression-replay launcher, and the owner's own ruling defers this kind of tool work until authorized. Third, whether the owner agrees J-11 is finished, since its database-level and clone-serving evidence is now complete. If the answers are "leave them" and "yes, fix it," the next iteration should fix the launcher, then resume normal product work in the owner's stated order — J-09, then J-05/J-06, then J-07/J-08 — run at full depth this time, since this iteration was specified full depth and was silently downgraded to lean, which is part of why the incident went unreported.

## Assumptions made

- iter-23b · goal-evaluator — Ambiguity: the owner's ruling requires verification to run only against the disposable clone with the canonical database left unmutated, but this iteration satisfied J-11's clone-based closure condition while a separate part of the same run also breached the canonical-database protection; the goal text doesn't say whether a breach elsewhere voids an otherwise-conforming journey closure. We chose: close J-11 as passing (its own evidence traces cleanly to the guarded clone) and halt the session on the breach instead, recording it as a critical unresolved ledger entry for the owner to rule on. Reversible: yes.
- iter-23 · goal-evaluator — Ambiguity: the goal file doesn't say whether "Today / Market Compass serving path" in the owner's ruling means the not-yet-built `/market` route or the Market Compass feature content, which currently lives on `/`. We chose: read it as the feature, and score the `/market` check as inapplicable rather than failed, since the Compass content demonstrably renders and serves correctly on `/` and building `/market` is explicitly deferred J-08 work. Reversible: yes.
- iter-23 · goal-decomposer — Ambiguity: the owner's ruling names no specific technical mechanism for pointing the app at the disposable database clone, and says full depth is "not required" for this task without saying whether it's still permitted. We chose: use the existing, already-tested `TRENDORA_CONFIG` environment-variable override (not an edit to the committed config file) to load the clone, and keep the iteration at full depth since the dispatch's own engine recommendation and the cross-cutting trigger rubric both independently justified it. Reversible: yes.
- iter-22 · goal-evaluator — Ambiguity: the goal file both assigns Stage G a "final serving/replay verification" duty and forbids booting the app until Stage G passes, so Stage G literally cannot perform the check one line assigns it; the latest owner ruling's acceptance list is entirely database-level. We chose: score the recovery attempt as having honestly reached its owner-defined success state, but keep the J-11 journey at "partial" rather than "passing" since no serving evidence existed yet — one owner line would settle it either way. Reversible: yes.
- iter-22 · goal-decomposer — Ambiguity: the owner's ruling requires content-correctness proof of "no stale derived state" for a preserved timeline cache, but a prior audit only softly suggested checking it, and the earlier stage's own proof covered only performance/branch-selection, not content correctness, for the same table. We chose: treat the per-date content-correctness recompute-and-compare as required this iteration, not optional, with a mismatch falling back to deleting the row. Reversible: yes.
- iter-22 · goal-decomposer — Ambiguity: the owner's ruling explicitly defers fixing two named unguarded write paths, but this iteration's own review found a third, different unguarded write path not literally on that named list, and it wasn't clear whether fixing the third should also extend to the other two. We chose: fix only the newly-found third path and leave the other two explicitly open and deferred, to avoid the scope-creep the owner's ruling separately forbids. Reversible: yes.

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-market-compass-iter-23.md |
| Dev handoff | — | docs/handoffs/goal-market-compass-iter-23-dev.md |
| Review | PASS_WITH_NOTES | reports/reviews/goal-market-compass-iter-23-review.md |
| Browser QA | PASS | reports/phase-goal-market-compass-iter-23-ui-test-results.md |
| Goal evaluation | STALLED | runs/goal-session-market-compass/iter-23/eval.md |
| Journey history | — | runs/goal-session-market-compass/state/journey-history.json |
