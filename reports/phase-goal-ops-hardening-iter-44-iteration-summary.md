# Iteration Summary — goal-ops-hardening-iter-44

**Verdict:** ESCALATE
**Iteration type:** goal-lean
**Date:** 2026-08-03
**Iteration:** 44

## In plain words

**What you can do now:** Start a price backfill for any date range and get an honest explanation when nothing new needs fetching; run a wide, multi-month backfill without hitting a hidden size cap; see a clear status badge showing whether the app is starting up, ready, or down right after it boots; browse the site's pages without them loading more than they need; view backtest evidence pulled instantly from stored results rather than a slow live recalculation; and see a live indicator whenever a background calculation is actively running.

**What changed this time:** No screens changed — this was backend-only work. The team fixed the backend's job-tracking code so a failed data import now records the real reason instead of a generic message, and made the "Retry" button fail with a clear "try again later" message instead of a blank error. They also wired in connection and shutdown-timeout limits that existed in the settings but were never actually applied by the startup script. But the main problem this round targeted — the app freezing during a heavy background calculation — was not fixed: during testing the app stopped responding to everything for over 20 minutes and had to be force-restarted.

**What's next:** Next, the team plans to add an outside watchdog that force-restarts the app if it ever freezes like this again, and then fix the actual cause: a slow calculation that currently redoes 26 years of history every time you add just one new day of data.

## Headline

Backend now enforces its own connection and shutdown-timeout settings

## Direction

**Signal:** holding
**Why:** J-05 (aggregates precomputed at ingest) and J-07 (heavy warm never takes the service down) are both still failing — J-07 for the third round running — while the six other journeys (J-01, J-03, J-04, J-06, J-08, J-09) re-verified passing with fresh evidence. This round's headline result was diagnostic, not corrective: two live SIGUSR1 dumps finally named the exact stall, but the total outage got worse (20m51s vs iter-43's several minutes) and a new CRITICAL flaky-test finding surfaced in review. No journey formally regressed (0 critical anti-goal violations, no `regressed` status this iteration) and no journey newly passed, so the session is holding at 6/8 passing rather than moving in either direction.

**Trend (last 3 iters):**
- Newly passing this iter: none
- Newly passing in last 3 iters total: none
- Regressions in last 3 iters: J-05 (iter-42)
- Anti-goal violations in last 3 iters: 8 minor (iter-43: af, ag, ah, ai, aj; iter-44: ak, al, am), 0 critical (iter-42 detail not present in the inline log excerpt)
- Iters with no journey state change: 0 of last 3

**Latest evaluator reasoning:** The app still goes offline when a heavy background calculation gets stuck, and this time it was offline for 20 minutes and 51 seconds and had to be killed by force. Six of the eight journeys were re-checked and passed. The two journeys this round aimed at both failed: J-05 "Aggregates are precomputed at ingest" was tested for the first time on a day that had never been saved before, and the job ran for ten minutes without saving anything and then failed; J-07 "Heavy aggregates never take the service down" failed for the third round in a row.

## What was done

- Product changes: incredible_auto_dev/scripts/start-backend.sh, apps/backend/app/api/data.py, apps/backend/app/engine/data_manager.py
- Wired `ServerOpsCfg`'s previously-unenforced launcher flags (`--limit-concurrency` / `--timeout-keep-alive` / `--timeout-graceful-shutdown`) into `start-backend.sh`, config-driven and additive to the existing AG-10 host caps.
- Live-diagnosed J-07's stall for the first time in seven attempts: two SIGUSR1 all-thread dumps name the exact blocking call — an O(dates × pool) membership-timeline recompute (~2,860 days × 591 symbols) triggered on every ingest.
- Fixed two silent MemoryError-escape defects found during audit (an uncaught exception in the malloc-trim cleanup call, a deferred module import outside its guard) that let the memory-pressure abort handler crash instead of degrading gracefully.
- Made failed-job messages honest, including for textless `MemoryError`, and gave the Retry endpoint the same 503 parity as Start/Resume.
- Re-tested J-05 against a genuinely unsnapshotted day for the first time this session — the job ran 10 minutes and failed with zero snapshots created.
- Verified 6 of 8 target/regression journeys pass browser QA (J-01, J-03, J-04, J-06, J-08, J-09); the two target journeys, J-05 and J-07, both failed.

## What's left

- Journey J-05 ("Aggregates are precomputed at ingest, never on the fly") failing — its own defining case ran 10 minutes and failed with zero snapshots created.
- Journey J-07 ("Heavy aggregates never take the service down") failing — the service went fully unreachable for 20m51s and needed a forced SIGKILL, worse than the prior iteration's outage.
- The named root cause (an O(dates × pool) full-history recompute on every ingest) is diagnosed but not fixed — needs an incremental membership-timeline redesign, judged too large for one iteration.
- No in-process fix can close TC-2/TC-7: the event loop itself was wedged, so the new shutdown-timeout flag can't fire; an out-of-process watchdog is the next evidenced step.
- The health-check budget (TC-5) still misses on 6.7% of polls (down from 63.6%) — real improvement but not yet "every poll".
- Reviewer found a CRITICAL: the memory-pressure abort test is flaky — a third `MemoryError` escape surfaced on a rerun and is not yet fixed.
- Two new open (minor) anti-goal items: the recurring, worsened outage (iter-44/ak) and two still-unbounded per-row memory accumulators on the evidence path (iter-44/al).
- Long-carried backlog untouched: the badge wording after a permanently-failed warm-up (16 rounds unmade), plus iter-31/e, iter-32/f, iter-35/k, iter-36/n, iter-37/o, iter-37/q.

## Next step

Full depth (mandatory via ESCALATE). In order: (1) build a watchdog outside the app process — the launch script backgrounds the server, waits its own deadline, and force-kills it if it won't stop — so a freeze inside the app can no longer make the whole service silent for 20+ minutes; give this its own iteration. (2) Fix the real cause of the freeze now that it's named: ingesting one day currently recomputes the entire ~2,860-day × 591-symbol membership history from scratch; make it update incrementally instead, and prove the output is byte-identical. (3) Re-run all eight journey checks afterward, including the six that passed, since their evidence was captured 21 minutes before the app went silent. (4) Stabilize the flaky memory-pressure test (a third `MemoryError` escape) with 3-5 consecutive clean runs before calling it fixed, and refresh J-07's stale golden test numbers (`n=8878`, `3508`).

## Assumptions made

- iter-44 · goal-evaluator — Ambiguity: the schema literally defines `regressed` as "was passing in a prior iteration" (which would force REGRESSION for J-05), but decision tree C.1 is narrower ("moved passing→failing") and J-05's immediate prior status was `partial`, not `passing`; goal.md doesn't say which reading controls. We chose: score J-05 `failing`, not `regressed` — the halt for this exact regression already fired and was acknowledged at iter-42, and re-firing it every iteration until J-05 passes would be an unbounded halt loop; no owner-only lever remains. Reversible: yes
- iter-44 · goal-decomposer — Ambiguity: the iter-43 recommendation to "give shutdown a deadline and make a stuck calculation give up and say so" named no specific mechanism. We chose: wire the already-declared but never-enforced `ServerOpsCfg` launcher timeouts into `start-backend.sh`, plus fire the live SIGUSR1 diagnostic (armed since iter-40, never used) to find the actual blocked call first, leaving the fix shape conditional on what the diagnostic finds rather than guessing a watchdog design upfront. Reversible: yes
- iter-43 · goal-evaluator — Ambiguity: J-07 failing 2 consecutive iterations matches ESCALATE's trigger, but this would be the session's seventh ESCALATE (methodology says use it sparingly) and the iteration already ran full depth with real progress. We chose: ESCALATE anyway — the decision tree is applied top-down and the clause plainly matches, reinforced by an independent trigger (only the audit lane caught the load-bearing defects, again). Reversible: yes
- iter-43 · goal-evaluator — Ambiguity: J-05's merged results row read PASS with real dated evidence, but the tested day was already snapshotted, so the job created 0 new snapshots and never exercised the journey's own "ingest produces fresh aggregates" claim. We chose: score `partial`, not `passing` — a green row plus screenshot isn't sufficient when the journey's defining half was never tried. Reversible: yes
- iter-43 · goal-decomposer — Ambiguity: the owner's amendment commissioned four follow-up actions "for the iterations that follow" without saying whether they're one iteration's scope, and left the warm-seam rewrite as merely "may" rather than mandatory. We chose: bundle the revert, job-launch honesty fix, host-guard extension, and J-05/J-07 re-verification into one iteration, but make the warm-seam rewrite conditional on the live re-measurement still showing it over budget. Reversible: yes
- iter-42 · goal-evaluator — Ambiguity: the six required-still-passing journeys had genuine dated evidence, but it was captured minutes before the same run's service outage; the agent file's evidence bar doesn't say whether a later outage in the same run voids earlier-captured passes. We chose: keep all six `passing`, with the timing caveat recorded in each journey's note — downgrading them on a later, different event would be inferring failure without evidence. Reversible: yes
- iter-42 · goal-evaluator — Ambiguity: J-05's immediate prior recorded status was `unknown` (not tested), not `passing`, so decision tree C.1's literal wording for `regressed` didn't clearly match — but the schema defines `regressed` as "was passing in a prior iteration," and J-05 was verified passing at iter-39. We chose: score `regressed` and return REGRESSION — `unknown` was never an assertion the journey worked, and treating a not-tested gap as erasing a prior pass would let a regression launder itself by going unverified for one round. Reversible: yes

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-ops-hardening-iter-44.md |
| Dev handoff | — | docs/handoffs/goal-ops-hardening-iter-44-dev.md |
| Review | FAIL | reports/reviews/goal-ops-hardening-iter-44-review.md |
| Browser QA | FAIL | reports/phase-goal-ops-hardening-iter-44-ui-test-results.md |
| Implementation summary | — | reports/phase-goal-ops-hardening-iter-44-implementation-summary.md |
| User-visible changes | — | reports/phase-goal-ops-hardening-iter-44-user-visible-changes.md |
| What to click | — | reports/phase-goal-ops-hardening-iter-44-what-to-click.md |
| UI surface map | — | reports/phase-goal-ops-hardening-iter-44-ui-surface-map.md |
| UI test plan | — | reports/phase-goal-ops-hardening-iter-44-ui-test-plan.md |
| UX regression | UX-REGRESSION-SKIPPED | reports/phase-goal-ops-hardening-iter-44-ux-regression.md |
| QA | FAIL | reports/qa/goal-ops-hardening-iter-44-qa.md |
| Audit | FAIL | docs/handoffs/goal-ops-hardening-iter-44-audit.md |
| Goal evaluation | ESCALATE | runs/goal-session-ops-hardening/iter-44/eval.md |
| Journey history | — | runs/goal-session-ops-hardening/state/journey-history.json |
