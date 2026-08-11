# Goal Iteration 63 — Close J-07's last agent-actionable latency gap; repair two self-inflicted verification-substrate defects

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** ops-hardening
- **Iteration:** 63
- **Mode:** next
- **Depth:** full
- **Full trigger:** 3 — prior iteration's (iter-62) evaluator verdict was `ESCALATE`, which mandates full
  depth this iteration with no exceptions (agent instructions: "If the prior evaluator log emitted
  ESCALATE, you MUST set depth to full for this iteration"). ESCALATE's own third clause also fired on
  real content this round: a lean iteration (iter-62) surfaced cross-cutting complexity in the
  verification substrate itself (a replay-lane restart race and a self-consuming golden), which is
  exactly what this iteration consolidates before any further feature work.
- **Frontend Present:** no — this iteration's only frontend-adjacent touch is a one-line doc-comment
  correction inside a non-shipping test file (see Test infrastructure); nothing users see changes.
- **Target journeys:** J-07
- **Required-still-passing journeys:** J-01, J-03, J-04, J-05, J-06, J-08, J-09 (full regression —
  widened because the prior evaluator verdict was ESCALATE, per this session's own "widen after
  ESCALATE" convention, iter-59)
- **Anti-goal reminders:**
  - **AG-3:** A journey passes ONLY if the **displayed numbers are correct** — they match the engine's
    computation for the same as-of date — not merely that the page renders. *(critical)*
  - **AG-5 — Preserve determinism and no-lookahead:** scoring uses bars ≤ as-of; forward returns use
    bars > as-of; never introduce lookahead anywhere. *(critical)*
  - **AG-8 — Resilience to data-shape and data-scale change:** widening the data basis (new nulls,
    broader pools, deeper history) must never crash an existing page or exhaust a service's memory —
    every existing consumer of a widened field is re-validated, the UI degrades gracefully (contained
    error boundary, honest "—"/NA placeholder, never a blank application-error page), and unbounded
    whole-table ORM loads are forbidden on the deep basis. *(critical)*
  - **AG-9 — Offline-deterministic ingest:** ingest jobs (fetch/backfill/rebuild) run only against the
    committed seed / local provider fixtures — no live external network calls or paid data services may
    be introduced without an explicit goal.md amendment. *(critical)*
  - **AG-10 — Host resource ceiling (hardware protection):** heavy compute — backfills,
    full-universe rebuilds, measurement passes, load drills, test-suite bursts — MUST be launched
    only via the project launch scripts (`scripts/dev.sh` / `scripts/start-backend.sh`), and those
    scripts MUST apply the host caps declared in `project-extensions/host-guard/host-guard.env`
    whenever that file is present (CPU-affinity mask, BLAS/OMP thread caps, `memory_cap_mb`,
    `malloc_arena_max`). Never remove, weaken, or bypass these caps: stripping a HOST-GUARD
    marked block from a launch script is a REGRESSION regardless of test outcomes. The ceilings
    are a physical constraint of the current host (two instant hardware resets under all-core
    vectorized ingest bursts: 2026-07-20 19:17, 2026-07-21 10:33), not a performance budget to
    optimize away. *(Owner amendment 2026-07-31, two corrections of record — nothing above is
    relaxed: `memory_cap_mb` / `malloc_arena_max` live in `config.yaml`, not in `host-guard.env`;
    and the 2026-07-20/21 resets were subsequently attributed to an uncorrected hardware
    data-fabric fault (`host-guard.env`, 2026-07-30), so the ceiling VALUES are an owner-set
    envelope — re-set by the dated entry in "Additional binding notes" below — while this
    paragraph's prohibition on agents removing, weakening, or bypassing caps is unchanged.)*
    *(critical)* (Note for this iteration: the SAME "Additional binding notes" amendment also
    rescopes — never waives — `GET /api/health`'s ceiling during a bounded background-compute
    window to a relaxed ≤2 s per poll; that is the exact ceiling this iteration's fix targets,
    see BACKGROUND.)

## GOAL

Eliminate the single measured `GET /api/health` latency breach (2.849 s against the owner's ≤2.0 s
background-compute-window ceiling) that sits inside the ingest finalize tail's
`coverage_membership_timeline_refresh` phase — the last concretely-measurable gap in J-07's acceptance
that an agent can close without the owner — and repair the two verification-substrate defects iter-62's
ESCALATE identified before they produce a false regression halt next round.

## BACKGROUND

iter-62 (ESCALATE) found, by re-deriving every fact from source rather than trusting any lane's prose,
three problems that no lane reported: (1) J-05's own golden (`journey-scripts/J-05.json`) backfills
2010-11-17 and asserts "0 already snapshotted" — but iter-62's own replay created that exact day
(`scanner_runs.id=2958`), so the SAME golden will report a false FAIL on a currently-`passing` journey
next time it runs, and its closing steps 13-15 still assert `2010-11-16`, two rotations stale (lesson
iter-62 #1, applies verbatim: "any iteration that runs, edits or trusts
`runs/goal-session-*/journey-scripts/*.json` goldens that create data"). (2) The deterministic replay
lane started ~1 minute after the pipeline's own pre-QA backend restart and reported two false FAILs
(J-01 step 09, J-04 step 02) on journeys that were honestly still warming up (lesson iter-62 #2, applies
verbatim: "any change to the browser-QA lane's restart/replay ordering"). Both are dev-actionable (the
iteration-state digest labels them `(dev)`, distinct from the ONE item explicitly labeled
`OWNER-gated` — the `browser-qa-phase.sh` TARGET_JOURNEYS line-ordering fix, which stays untouched this
round per that gate). (3) iter-62's own reasoning (8) named a concrete, agent-actionable target for
J-07's last gap: the finalize tail's phase-timing log shows `coverage_membership_timeline_refresh`
55.20 s / `forward_aggregates_warm` 297.17 s / `factor_lab_all_warm` 608.68 s / `research_hot_keys_warm`
23.79 s, and iter-61's ONE >2 s health poll (2.849 s) fell inside the FIRST of those. This session has
already closed the identical class of defect on `coverage_membership_timeline_refresh` twice
(iter-53: bounded `universe_resolver.resolve_with_reasons`'s per-symbol fetch, zeroing connection-level
non-answers; iter-54: bounded the sibling `per_date_coverage_warm` phase) and on
`compute_factor_lab_all` (iter-52) — this iteration applies the SAME profile-then-bound discipline
(iter-48/50/53's own standing rule: "never force-fit a prior mechanism without profiling first") to
close the ONE remaining latency outlier, not availability (already zero since iter-53).

Per the priority rubric: no journey regressed (rule 1); the last `coherence.md` (iter-62) was
COHERENCE-PASS, so no consolidation-only pass is mandated (rule 2), but the ESCALATE verdict itself
functions as an unblocker case (rule 3) — the J-05 golden fix protects the ENTIRE required-still-passing
regression set from a false halt next round, and the replay-lane fix protects every future round's
signal quality. J-07 is the only target journey and the only risky (backend engine) change this round
(rule 5); the golden-rotation and replay-lane fixes are test-infrastructure hygiene, not a second risky
journey. Per rule 6, this iteration deliberately does NOT wait on the owner's still-open one-sentence
policy question (does the ≤2 s ceiling apply to a 15–23-minute job, or only the "order ~30 s" window the
amendment's own text describes) — a dev-actionable path exists (this iteration's fix) that makes the
answer moot by driving the measured breach count to zero regardless of which reading is eventually
chosen, exactly as iter-62's evaluator identified.

## IN SCOPE

### Backend
- [ ] Profile (never assume) the live GIL-holding/latency source inside the finalize tail's
  `coverage_membership_timeline_refresh` phase during a real backfill/rebuild job, using the same
  stack-sampling method iter-53 used (`reports/perf-budgets.md`'s iter-53 addendum) — candidates to rule
  in or out: `universe_resolver.resolve_with_reasons`'s per-symbol loop (already bounded to
  `bars_asof_window` at iter-53 — confirm whether a residual cost remains) and
  `refresh_coverage_snapshot` / `_compute_coverage_uncached`'s own compute.
- [ ] Apply whichever bounded/cooperative-yield construct the profile supports (mirroring this
  session's own proven precedents: `_cooperative_sorted`'s chunked `time.sleep(0)` hand-off and
  `_cyclic_gc_paused`'s GC-pause suspension in `apps/backend/app/engine/research.py:143-205`, or a
  further-bounded fetch in the style of `universe_resolver.py`'s iter-53 fix) so that a concurrent
  `GET /api/health` request is never blocked past the owner's ≤2.0 s background-compute-window ceiling
  during this phase — byte-identical `admitted`/`excluded_counts`/`resolutions` and coverage-payload
  output required for the same inputs (no change to WHAT is computed, only how CPU time / GIL hold is
  yielded).
- [ ] Add a unit test proving byte-identical output against a pinned pre-fix reference oracle for the
  bounded construct (mirrors `test_universe_resolver.py`'s iter-53 tests).

### Test infrastructure (goldens & replay lane — not application code)
- [ ] Live-verify (direct read-only sqlite query against `apps/backend/data/trendora.db`, per this
  file's own standing practice) a fresh unsnapshotted trading day, then rotate
  `runs/goal-session-ops-hardening/journey-scripts/J-05.json`'s steps 2/3 fill targets off
  `2010-11-17` (consumed by iter-62's replay, `scanner_runs.id=2958`) to that new date, and update
  steps 13-15's asserted date to match the SAME new date (not `2010-11-16`, two rotations stale).
  Append a dated rotation-history entry to the file's own `_notes`, per its established convention.
- [ ] Fix the deterministic replay lane's restart race: gate the lane's first step on the backend's own
  readiness signal (e.g. `data-state="ready"`, mirroring what the app's own UI already waits on) rather
  than a fixed short sleep, so a lane invoked moments after the pipeline's pre-QA restart no longer
  reports a false FAIL on a required-still-passing journey. Locate and fix at whichever call site the
  restart-to-lane-start ordering actually lives (`scripts/automation/lib/replay-lane.sh` and/or
  `scripts/automation/goal-iter-lean.sh` / `browser-qa-phase.sh`'s restart step — NOT the
  `browser-qa-phase.sh` TARGET_JOURNEYS line-286-before-272 ordering bug, which stays untouched
  (OWNER-gated, out of scope this iteration)).
- [ ] Fix `apps/frontend/lib/data-overview-refresh.test.ts`'s header comment, which documents
  `node lib/data-overview-refresh.test.ts` as the run command though only `npx tsx
  lib/data-overview-refresh.test.ts` actually passes (iter-62 next-step item 6; matches the "Do not
  redo" note already on record that the test itself is correct and green under `npx tsx`).

### New user-facing capability
None — this iteration is a latency/reliability fix to an already-shipped, already-registered background
process, plus test-harness maintenance. No new page, control, or displayed value.

### New information displayed
None.

### New user actions
None.

### UI surface changes
None — the global readiness badge and `/backtest` (J-07's existing homes) are unchanged in shape; only
the finalize tail's internal timing changes.

### Product surface delta
`GET /api/health` stays responsive (≤2.0 s per poll) throughout the ENTIRE finalize tail, including the
`coverage_membership_timeline_refresh` phase, closing the one measured exception to that promise.

### Blueprint conformance
No new surfaces. This iteration extends the ALREADY-registered "Job history & per-date exclusion
reasons" Data Contract row (`runs/goal-session-ops-hardening/state/blueprint.md`, same computing modules
`app.engine.data_manager` / `app.engine.universe_resolver`, same two endpoints `GET /api/data` +
`GET /api/data/jobs/{job_id}`) — an iter-63 note has been appended to that row's Notes cell documenting
this plan, following the session's own established per-iteration-changelog convention. The golden and
replay-lane fixes are pipeline/test-infrastructure artifacts, not Information-Architecture surfaces.

### Data-contract additions
None. No new field, no new computing module, no new endpoint, no second producer for any
already-registered value. The bounded/cooperative-yield construct changes only HOW CPU time is yielded
during an existing phase — verified byte-identical output is the acceptance bar (see TC-2, TC-5).

## OUT OF SCOPE

- The owner's outstanding one-sentence policy decision (does the ≤2 s ceiling apply to a 15–23-minute
  background-compute window, or only the "order ~30 s" window the amendment's text describes) — not
  decided by this iteration; the fix is designed to make the measured answer the same either way (zero
  breaches).
- `scripts/automation/browser-qa-phase.sh`'s TARGET_JOURNEYS line-286-before-272 ordering fix — remains
  explicitly OWNER-gated (build-system file); not touched this iteration.
- The cost decision on the replay lane now running a real ~15-minute ingest job every round — owner-gated,
  not decided here.
- Recording the `[NEW]`-flagged J-05/J-07 walkthrough — scored `evidence_makeup` (non-blocking) per
  standing convention; rides along automatically at this iteration's full depth (demo/walkthrough
  recorder), never this iteration's own goal.
- `/data`'s indefinite-stale-on-permanent-outage behavior (iter-62/e, scored minor) and the
  background-compute chip's unreconcilable log gap (iter-62/f, scored minor) — both carried, not fixed
  this round.
- All long-carried backlog items (iter-29/b warm-up badge wording; iter-31/e; iter-32/f; iter-35/k;
  iter-36/n; iter-37/o; iter-37/q; iter-39/u; iter-46/az/ba; iter-47/bd/bf/bi; iter-48/bj; iter-57/f/l;
  iter-59/g/h/k; iter-33/g the Regime Lab) — untouched, no new deferral needed beyond the evaluator's own
  running ledger.
- No change to `server.memory_cap_mb`, `malloc_arena_max`, or any `host-guard.env` value (AG-10).

## DEFINITION OF DONE

- [ ] A fresh live health-poll drill (1 Hz `GET /api/health` for the full duration of a real finalize
  tail that reaches `coverage_membership_timeline_refresh`) records ZERO polls over 2.0 s, reconciled
  against the raw log's own line count (TC-1).
- [ ] The bounded/cooperative-yield construct's output is proven byte-identical to the pre-fix reference
  for the same inputs (TC-2, TC-5).
- [ ] `journey-scripts/J-05.json` is rotated off its consumed date and its closing steps assert the
  correct date (TC-3).
- [ ] The deterministic replay lane no longer reports a false FAIL when invoked shortly after a backend
  restart (TC-4).
- [ ] `data-overview-refresh.test.ts`'s header comment documents the command that actually passes (TC-6).
- [ ] Required-still-passing journeys (J-01, J-03, J-04, J-05, J-06, J-08, J-09) pass via deterministic
  replay + LLM fallback.
- [ ] No anti-goal violation introduced (AG-3, AG-8, AG-9, AG-10 particular attention — no unbounded
  whole-table load added; host caps untouched; every ingest row `provider='seed'`).
- [ ] Unit tests pass; no regressions.
- [ ] Dev handoff written at `docs/handoffs/goal-ops-hardening-iter-63-dev.md`.

## TESTING REQUIREMENTS

- Browser: J-07 (target — TC-1 drill evidence); J-01, J-03, J-04, J-05, J-06, J-08, J-09 (required-still-
  passing, full regression per the widen-after-ESCALATE convention).
- Unit/integration: `test_universe_resolver.py` / `test_data_manager_membership_cache.py` (or wherever
  the profile locates the fix) gain a byte-identity test against a pinned pre-fix reference oracle;
  existing tests in those files stay green.
- Error cases: a fault-injected `MemoryError` at the `coverage_membership_timeline` probe site
  (`TRENDORA_FAULT_INJECT_MEMORY_ERROR=coverage_membership_timeline`) still isolates cleanly (existing
  behavior, re-run as a regression check — not a new mechanism).

Test-first contract:

- TC-1: given a live in-app backfill/rebuild job whose finalize tail reaches
  `coverage_membership_timeline_refresh`, when `GET /api/health` is polled at 1 Hz for the full duration
  of that phase (bounded by the phase's own OPEN/CLOSED log markers, never a hand-picked segment — iter-
  57/58 lesson), then every poll answers HTTP 200 within ≤2.0 s and the raw poll log's line count
  reconciles exactly against the reported total.
- TC-2: given the SAME `coverage_membership_timeline_refresh` phase's resolved `coverage` /
  `membership_timeline` payload before and after the fix, when compared for identical inputs, then the
  served `GET /api/data` coverage payload and the phase's `admitted` / `excluded_counts` / `resolutions`
  values are byte-identical to the pinned pre-fix reference.
- TC-3: given `runs/goal-session-ops-hardening/journey-scripts/J-05.json`'s current rotation target
  (`2010-11-17`, already consumed — `scanner_runs.id=2958`), when a live read-only sqlite query
  confirms a fresh unsnapshotted trading day BEFORE this edit, then the file's steps 2/3 fill values and
  steps 13-15's asserted date are updated to that SAME new date, and a rotation-history entry is
  appended to `_notes`.
- TC-4: given the deterministic replay lane is invoked within 60 s of the pipeline's own pre-QA backend
  restart (reproducing iter-62's exact false-FAIL condition on J-01 step 09 / J-04 step 02), when the
  lane's first step runs, then it blocks on the backend's own readiness signal before executing any
  replay step, and the SAME two journeys report PASS rather than a warm-up-induced false FAIL.
- TC-5: given the bounded/cooperative-yield construct added to close TC-1, when the new unit test runs
  against a pinned pre-fix reference oracle, then every returned `resolutions` / `admitted` /
  `excluded_counts` value is identical (not merely equal-looking) to the reference, and all pre-existing
  tests in the touched module remain green.
- TC-6: given `apps/frontend/lib/data-overview-refresh.test.ts`'s header comment currently documents
  `node lib/data-overview-refresh.test.ts`, when the comment is corrected, then it documents
  `npx tsx lib/data-overview-refresh.test.ts` — the command that actually exits 0 — and running that
  exact command still reports 3/3 checks passed.

## NOTES

- Lessons applied (both iter-62, both apply verbatim to this iteration's Test-infrastructure scope): (1)
  "any iteration that runs, edits or trusts `runs/goal-session-*/journey-scripts/*.json` goldens that
  create data" — J-05's golden is state-mutating and must rotate off its own consumed date; (2) "any
  change to the browser-QA lane's restart/replay ordering — proof is cheap and should be the first check
  on any replay FAIL: compare the frame's mtime with the `=== start-backend.sh: launching at ... ===`
  banner in `logs/backend.log`."
- The `_cooperative_sorted` / `_cyclic_gc_paused` constructs already proven on the sibling
  `factor_lab_all_warm` phase (iter-52, `research.py:143-205`) are the strongest prior for what a
  profile here is likely to support — but per iter-48/50/53's own standing discipline, do not force-fit
  either construct without a live stack-sampling profile confirming the actual bottleneck; iter-52's own
  history shows a first guess (plain yield points) measured WORSE before profiling found the real cause.
- If profiling finds the phase already has zero residual latency risk (i.e. iter-61's 2.849 s reading
  does not reproduce under a fresh measurement), record that finding honestly in the dev handoff rather
  than shipping a speculative fix with no measured effect — J-07 would then rest entirely on the
  owner's outstanding one-sentence policy question, and the next iteration should say so plainly.
- Both test-infrastructure fixes are framework/pipeline work, not product code — per this session's own
  precedent (iter-9/iter-18/iter-23), they are not Data Contract additions and needed no
  blueprint.reapproval-requested (no nav-skeleton change).
