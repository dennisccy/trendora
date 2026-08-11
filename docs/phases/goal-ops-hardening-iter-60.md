# Goal Iteration 60 — Close the target-journey verification gap and finish J-05/J-07's small named defects

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** ops-hardening
- **Iteration:** 60
- **Mode:** next
- **Depth:** full
- **Full trigger:** 1 — Structural/cross-cutting: the evaluator's recommendation for this iteration is
  itself `full` (binding by default — both open journeys carry a `[NEW]` walkthrough clause and the
  demo/walkthrough recorder runs only at full depth). Independently, the fix spans the shared
  `scripts/automation/lib/replay-lane.sh` dispatch module (read by every future iteration's regression
  gate, not just this one), backend (`app/engine/research.py`), frontend
  (`app/research/_labs.tsx`, `components/sample-link.tsx`), and a test golden
  (`journey-scripts/J-01.json`) — ≥3 modules whose interaction (does a target journey's golden actually
  get replayed; does a degraded value render honestly) is not covered by any single journey's own test.
- **Frontend Present:** yes
- **Target journeys:** J-05, J-07
- **Required-still-passing journeys:** J-01, J-03, J-04, J-06, J-08, J-09 (full regression set — this
  iteration edits the shared replay dispatch logic all six are verified through, so the whole passing
  set is included rather than a smaller rotating smoke set)
- **Anti-goal reminders:**
  - **AG-1:** A score, ranking, or "edge" MUST NOT be presented as proven/confident unless it is backed by a
    **passing certified-claim entry** in the evidence ledger (out-of-sample, control-beating). Unbacked
    values MUST render a "not yet proven" state. *(critical)*
  - **AG-2 — Decision-quality only:** never present return promises, price targets, "buy/sell" signals, or alpha
    claims; never place or simulate orders. *(critical)*
  - **AG-3:** A journey passes ONLY if the **displayed numbers are correct** — they match the engine's computation
    for the same as-of date — not merely that the page renders. *(critical)*
  - **AG-4 — No overfit edges:** any pattern surfaced as "proven" must have survived the referee (sealed
    out-of-sample holdout + controls + multiple-testing correction), never in-sample fit alone. *(critical)*
  - **AG-5 — Preserve determinism and no-lookahead:** scoring uses bars ≤ as-of; forward returns use bars > as-of;
    never introduce lookahead anywhere. *(critical)*
  - **AG-6:** No iteration ships if its evidence-derived claims (if any) lack a passing referee verdict from the
    post-decompose gate. *(critical)*
  - **AG-7:** No hard-coded credentials, API keys, or tokens in source files. *(critical)*
  - **AG-8 — Resilience to data-shape and data-scale change:** widening the data basis (new nulls, broader pools, deeper history) must never crash an existing page or exhaust a service's memory — every
    existing consumer of a widened field is re-validated, the UI degrades gracefully (contained error
    boundary, honest "—"/NA placeholder, never a blank application-error page), and unbounded
    whole-table ORM loads are forbidden on the deep basis. *(critical)*
  - **AG-9 — Offline-deterministic ingest:** ingest jobs (fetch/backfill/rebuild) run only
    against the committed seed / local provider fixtures — no live external network calls or
    paid data services may be introduced without an explicit goal.md amendment. *(critical)*
  - **AG-10 — Host resource ceiling (hardware protection):** heavy compute — backfills,
    full-universe rebuilds, measurement passes, load drills, test-suite bursts — MUST be launched
    only via the project launch scripts (`scripts/dev.sh` / `scripts/start-backend.sh`), and those
    scripts MUST apply the host caps declared in `project-extensions/host-guard/host-guard.env`
    whenever that file is present. Never remove, weaken, or bypass these caps. *(critical)*

## GOAL

Fix the framework gap that let J-05 and J-07's already-passing goldens go unreplayed for an entire
round, then finish the three small, already-diagnosed defects standing between those two journeys and
closing: the Regime-Lab prologue's unhandled-exception path, the degraded `n=0` cohort display, and the
`J-01` golden's spurious replay failure.

## BACKGROUND

iter-59 (CONTINUE, full depth) executed J-05's steps 1-4 and J-07's steps 1/3/4 LIVE for the first time
in the session and all of them passed — but neither journey received a lane row: `replay-lane.sh`'s
partition function only ever loops `REQUIRED_JOURNEYS`, never `TARGET_JOURNEYS`, even though the
`--target` flag wired into `merge_results.py` at iter-42 correctly *flags* the gap (hence `BLOCKED`)
without *closing* it (iter-59 lesson entry 1; `iteration-state.md`'s "LANE COVERAGE" blocker, TOP
PRIORITY). That is this iteration's first and largest item. iter-59's evaluator also re-confirmed via
`git diff`/`git log` that `journey-scripts/J-01.json` was never rewritten despite a merged-results claim
that it was (iter-59/e) — its step 09 will fail replay again on a journey the LLM lane already
re-confirmed genuinely works. The remaining two items are the evaluator's own named small defects: the
Regime-Lab prologue (`labels`/`horizons`/`run_position` build in `compute_regime_lab`,
`research.py:~4438-4441`) sits OUTSIDE the per-horizon `try` the loop body already uses, so a failure
there still reaches `GET /api/research/regime-lab` as a 500; and the degraded-cell display
(`_labs.tsx`'s `RegimeReturnCell` + `components/sample-link.tsx`'s `SampleLink`) shows `n=0` with a live
drill-down link for a horizon whose real cohort holds 17,440 observations, distinguishable from a
genuine low-sample cell only by a `title` tooltip (iter-59/a, scored `minor` not critical, but named as
this round's top display-honesty item). Depth is `full` because the evaluator's own recommendation for
this round is `full` (binding by default) — a shallow round cannot record the walkthrough both open
journeys' acceptance text requires (`[NEW]`-flagged, demo lane only runs at full depth) — and
independently because the change set is genuinely cross-cutting (framework + backend + frontend + test
golden). **Lessons applied:** the iter-59 lane-coverage lesson (target journeys can end up verified by
nobody — this iteration is that fix); the iter-58 blank-picture lesson (open every evidence frame this
round produces, don't just hash for distinctness); the iter-57 segment-boundary lesson (bound any new
drill/measurement window by the process's own markers, reconcile against the raw log's line count before
writing a "zero failures" claim). **Deliberately not re-litigated:** J-07 step 2's health-latency clause
depends on an outstanding owner decision (2-second ceiling applied to short jobs only, vs. relaxed for
long jobs) that has been asked for ten rounds and remains unanswered — per the priority rubric's rule 6,
this iteration does not attempt that fix; J-07 may still read `partial` afterward for that reason alone,
and that is expected, not a shortfall of this iteration's own scope.

## IN SCOPE

### Backend
- [ ] `app/engine/research.py`: wrap `compute_regime_lab`'s pre-loop prologue (the `labels` build,
  `horizons` build, and `_run_position_index` call) in the SAME per-horizon try/except-and-degrade
  pattern the horizon loop body already uses, so a DB-read failure before the loop starts returns an
  honest degraded response instead of propagating an unhandled exception to
  `GET /api/research/regime-lab` as a 500.

### Frontend
- [ ] `app/research/_labs.tsx` (`RegimeReturnCell`) + `components/sample-link.tsx` (`SampleLink`): when a
  `by_horizon` cell's `status === "unavailable"` (a degraded horizon), stop rendering the `n={n}`
  sample-size chip as an active drill-down link into a cohort the payload itself reports as unavailable;
  render a distinct, non-tooltip-only "unavailable" indicator on the cell instead. Non-degraded cells
  (including genuine `low_sample` ones) keep their existing chip and link byte-unchanged.

### Test infrastructure (framework — shared across all future iterations)
- [ ] `scripts/automation/lib/replay-lane.sh` (`replay_lane_partition_and_verify` or its caller): extend
  the golden-file partition loop so any journey in `TARGET_JOURNEYS` with an on-file golden is also
  routed into the deterministic replay set (`R_REPLAY`), not only journeys in `REQUIRED_JOURNEYS`. A
  target journey with a valid golden must be ACTUALLY REPLAYED, not merely flagged missing by the
  existing `merge_results.py --target` check.
- [ ] `journey-scripts/J-01.json`: diagnose and fix the actual cause of its replay failure (step 09's
  `zero-work-note` assertion or an earlier step) so the deterministic replay lane passes it without
  requiring the LLM lane to overturn a false FAIL. Do not just re-annotate the script as "rewritten" —
  verify the fix against a live replay run before commit.

### New user-facing capability
None new — this iteration corrects two existing surfaces (Regime Lab degrade rendering, prologue error
handling) and one test-infrastructure gap (target-journey replay coverage) so J-05/J-07's already-built
behavior is honestly displayed and mechanically verifiable, rather than adding a feature.

### New information displayed
A degraded Regime-Lab cohort's true state becomes visible on the cell itself (not only in a hover
tooltip): an "unavailable" indicator replaces the misleading `n=0` count, and the cell's drill-down link
is suppressed for that state only.

### New user actions
None. (One existing action — the `N=` drill-down click — is withheld specifically for the already-broken
degraded state; no new action is added.)

### UI surface changes
`/research/regime-lab`'s by-label and by-decile tables (`RegimeReturnCell`) — same page, same tables,
corrected cell rendering only. No new page, panel, or route.

### Product surface delta
No nav or page-count change. Data Manager (`/data`), Research (`/research/regime-lab`), and the global
readiness badge each get a walked-through, mechanically-replayed verification record for the first time
this session — the product surfaces themselves are unchanged; what changes is that the surfaces are now
provably tested.

### Blueprint conformance
No new pages or nav entries. All work lives under existing Information Architecture homes already
registered in `blueprint.md`: Data Manager (`/data`, J-05's row), Research (`/research/regime-lab`,
J-05/J-06's row), global readiness badge (J-04/J-07/J-09's row). No `blueprint.reapproval-requested`
needed.

### Data-contract additions
None. `by_horizon[].status`, `.n`, `.low_sample`, `.mean_return` are already registered in `blueprint.md`
(the "Regime score, market phase, realized forward-returns" row) and already typed in
`apps/frontend/lib/api.ts:1495-1502` (`RegimeLabHorizonCell`). This iteration only corrects how the
frontend CONSUMES those already-registered fields — no second computing module, no second endpoint, no
new field. (`blueprint.md` has been updated in place with an `iter-60` note on that row recording this as
a consumption/robustness fix only — see the row's tail.)

## OUT OF SCOPE

- J-07 step 2's health-latency ceiling question (does the relaxed ≤2s promise apply to a ~30s window
  only, or to a 23-minute one) — an outstanding owner decision, ten rounds unanswered; no code change to
  `/api/health`'s budget or its window interpretation this iteration.
- Moving heavy Regime-Lab / forward-aggregate compute into its own process — the other outstanding owner
  question; per iter-59's own evaluator, it has "lost most of its urgency" now that VmPeak sits at 71%
  of the cap.
- The CARRIED backlog list untouched for multiple rounds (iter-29/b, iter-31/e, iter-32/f, iter-35/k,
  iter-36/n, iter-37/o, iter-37/q, iter-39/u, iter-46/az, iter-46/ba, iter-47/bd, iter-47/bf, iter-47/bi,
  iter-48/bj, iter-57/f, iter-57/l) and iter-33/g (the Regime Lab cold `view=pooled` background dispatch,
  deferred 25 times) — none is named by iter-59's next-step items 1-4 as this round's priority.
- QA/audit/closure write-up discipline (a blank frame cited as evidence, a "no blockers" summary over a
  file listing one, the closure gate's false alarm about user-visible changes, a vanished prior audit
  report) — these are report-writing behaviors already covered by standing lessons (iter-57, iter-58);
  no product code change is planned for them.
- A new drill file or dedicated measurement campaign for the "quiet machine" memory/latency comparison —
  a single opportunistic cold-load timing is recorded (TC-9) but no new sustained drill is built this
  round.
- Rewriting `merge_results.py`'s `--target` check itself — it already does its one job (flag a target
  journey with zero executed test cases); this iteration closes the execution gap upstream of it in
  `replay-lane.sh`, not the check.

## DEFINITION OF DONE

- [ ] J-05 and J-07 (this iteration's Target journeys) each get an ACTUALLY EXECUTED lane row from the
  deterministic replay lane (TC-1, TC-2) — never "no test case executed by any lane"
- [ ] `journey-scripts/J-01.json` replays PASS deterministically, without an LLM-lane override (TC-3)
- [ ] `compute_regime_lab`'s prologue no longer propagates an unhandled exception as an HTTP 500 (TC-4)
- [ ] Degraded Regime-Lab cells show an honest "unavailable" indicator, not a misleading `n=0` with an
  active drill-down link (TC-5); non-degraded low-sample cells are unchanged (TC-6)
- [ ] Required-still-passing journeys J-01, J-03, J-04, J-06, J-08, J-09 remain green (TC-7)
- [ ] A recorded walkthrough exists for J-05's ingest→fresh-aggregates→cold-`/data`-within-budget
  sequence and J-07's crash-free-warm+healthy-`/api/health` sequence, with every evidence frame opened
  and confirmed non-blank (not just hashed for distinctness) (TC-8)
- [ ] No anti-goal violation introduced: AG-3 (displayed numbers correct — the degrade fix must not
  fabricate a value, only relabel/withhold the link), AG-8 (honest degradation, no unbounded load)
- [ ] Unit tests pass; no regressions
- [ ] Dev handoff written at `docs/handoffs/goal-ops-hardening-iter-60-dev.md`

## TESTING REQUIREMENTS

- Browser: J-05 (all 4 steps + walkthrough), J-07 (steps 1/3/4 + walkthrough; step 2 re-stated with its
  existing honest numbers, not re-scored); regression replay of J-01, J-03, J-04, J-06, J-08, J-09.
- Unit/integration: `test_regime_lab.py` gains a prologue-failure-degrades-honestly test (mirrors the
  existing `test_compute_regime_lab_one_horizon_non_memory_failure_degrades_only_that_horizon` pattern);
  a frontend test (or a component-level check alongside the existing `research-labs.test.ts` /
  `lab-load-panel.test.ts` suite) asserting a degraded cell suppresses its `SampleLink` while a
  low-sample-but-not-degraded cell keeps it; a `replay-lane.sh` test/dry-run confirming
  `TARGET_JOURNEYS` entries with on-file goldens land in `R_REPLAY`.
- Error cases: a simulated DB-read failure in the Regime-Lab prologue must degrade honestly, never crash
  the endpoint; a golden file missing for a `TARGET_JOURNEYS` entry must still fall to the LLM lane
  (existing fallback path), never silently skip verification.

Test-first contract:

- TC-1: given `REQUIRED_JOURNEYS` is set to the smoke set and `TARGET_JOURNEYS="J-05 J-07"` before
  `replay_lane_partition_and_verify` runs, when the function partitions journeys with on-file goldens,
  then J-05 and J-07 (both have valid `journey-scripts/*.json` goldens) are added to `R_REPLAY` and
  actually executed by `demo_runner.py --mode verify`, producing rows in the raw replay results file
  (`$REGRESSION_RESULTS`) — not merely flagged missing by `--target`.
- TC-2: given the same run, when `replay_lane_merge_results` merges LLM + replay outputs, then
  `phase-goal-ops-hardening-iter-60-ui-test-results.md` shows an executed PASS/FAIL row for both J-05 and
  J-07.
- TC-3: given a fresh replay of `journey-scripts/J-01.json` against the committed-seed DB, when all 16
  steps execute, then every step (including step 9's `zero-work-note` assertion) passes deterministically
  without requiring an LLM-lane override to reach PASS.
- TC-4: given a unit test that makes `compute_regime_lab`'s prologue read (`labels`/`horizons`/
  `_run_position_index`) raise, when `compute_regime_lab` is invoked, then it returns a degraded result
  (or a handled, logged degradation) instead of propagating the raw exception, and
  `GET /api/research/regime-lab` never returns HTTP 500 for this condition.
- TC-5: given a `by_horizon` cell with `status: "unavailable"` and `n: 0` (a degraded horizon), when the
  Regime Lab page renders that cell, then it shows a visible "unavailable" indicator distinct from a real
  n=0 count, and no `data-testid="sample-link"` element is rendered for that cell.
- TC-6: given a `by_horizon` cell with `low_sample: true`, `status` absent, and a genuine `n` below `min`
  (e.g. n=3), when the page renders that cell, then the existing `n={n} ⚠` `SampleLink` chip still
  renders exactly as before, with its drill-down link intact.
- TC-7: given the six Required-still-passing journeys (J-01, J-03, J-04, J-06, J-08, J-09), when the
  deterministic replay lane runs after this iteration's `replay-lane.sh` change, then all six still
  verify PASS via replay or the LLM fallback, with zero regressions attributable to the partition-loop
  change.
- TC-8: given the full-depth pipeline's demo/walkthrough recorder runs, when it executes J-05's
  ingest→fresh-aggregates→cold-`/data`-within-budget sequence and J-07's crash-free-warm+healthy-
  `/api/health` sequence, then it saves screenshots/recording frames for each step that are opened and
  confirmed non-blank (not just hashed for distinctness) before being cited as evidence.
- TC-9 (opportunistic measurement, no code change required): given an idle backend with no concurrent
  heavy job, when a cold `/research/regime-lab` page load is timed once, then the recorded
  seconds-to-render figure is appended to `reports/perf-budgets.md` as the first "quiet machine"
  comparison point against iter-59's 340-second under-load figure.

## NOTES

- Priority-rubric application: rule 1 (regressed journeys first) — none regressed this session, N/A.
  Rule 2 (consolidation before features) — last `coherence.md` was COHERENCE-PASS (0 blocking), so no
  forced consolidation. Rule 3 (unblockers next) — the lane-coverage fix unblocks verification of every
  future target journey, not just this iteration's; picked first. Rule 5 (never bundle two risky
  journeys) — J-05 and J-07 share the SAME named blockers (lane coverage, walkthrough) so this is one
  coordinated fix, not two independent risky changes; none of this iteration's four changes is itself a
  data-model migration or provider integration. Rule 6 (don't plan human-blocked work) — J-07's step-2
  latency clause is genuinely owner-blocked and is explicitly excluded; the rest of J-07's and all of
  J-05's remaining work is agent-actionable and is in scope.
- Assumption ledger: no new entry filed this iteration — target selection and scope followed directly
  from iter-59's own named next-step items (1)-(4) plus the J-01 sub-item of (5), with no fresh
  interpretation call beyond what iter-58/iter-59's own decomposer/evaluator entries already logged.
- If profiling `replay_lane_partition_and_verify`'s existing tests during implementation surfaces a
  reason target-journey goldens were deliberately excluded from replay (rather than just an oversight),
  the developer should record that finding in the dev handoff rather than force the union — but no such
  reason is evident in the current code or its comments (the `--target` flag's own iter-42 comment frames
  it purely as a "flag the gap" check, not a deliberate no-replay decision).
