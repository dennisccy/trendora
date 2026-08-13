# Goal Iteration 76 — Root-cause the asset-less QA frontend + give J-07/J-09 goldens real assertions

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** ops-hardening
- **Iteration:** 76
- **Mode:** next
- **Depth:** lean
- **Frontend Present:** yes
- **Target journeys:** J-07, J-09
- **Required-still-passing journeys:** J-01, J-03, J-04, J-05, J-06, J-08
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
    whenever that file is present (CPU-affinity mask, BLAS/OMP thread caps, `memory_cap_mb`,
    `malloc_arena_max`). Never remove, weaken, or bypass these caps: stripping a HOST-GUARD
    marked block from a launch script is a REGRESSION regardless of test outcomes. *(critical)*

## GOAL

Root-cause and fix the intermittent asset-less/unstyled QA frontend defect that has voided replay
evidence across four prior rounds, and replace J-07's and J-09's trivially-weak deterministic-replay
goldens with assertions that can actually detect a regression, so the replay lane is trustworthy again.

## BACKGROUND

All 8 Must-have journeys are `passing` (iter-75), but iter-75's own dev/reviewer lane never ran
(EVIDENCE micro-path, diff "(no changes)"), so the carried harness/hygiene backlog is untouched. The
iter-75 evaluator's binding next-step order puts, first, root-causing `scripts/start-frontend.sh`'s
intermittent asset-less-page defect (iter-72/c, carried 4 rounds — voided goldens in iters 72, 73 and
74) using the frontend start-command log to rule the "`next build` writes into a live `.next` while
`next start` serves it" theory in or out; second, giving J-07's and J-09's replay goldens real
assertions (iter-75/c) — J-07's golden is a 2-step page-render smoke check and J-09's strongest
assertion is a panel's mere presence, so it passes against an idle background-compute panel exactly as
readily as an active one. Two small carried one-liners (delete the stray zero-byte `=` at repo root,
iter-74/c, 4th round; close TC-10's `/data` honest-fallback evidence, iter-72/b) and clearing the stale
`state/goldens-regen-pending` (still names J-05..J-09 though all passed — regenerating a script was
never the fix, per the iter-73 lesson) ride along. No full trigger holds: the verdict is CONTINUE, not
ESCALATE; coherence is PASS; consecutive-lean count is 3 of the cadence-6 threshold; this is
harness/hygiene work with no new Data-Contract value and no user-visible product change (rendering
`stale_for_s`, this cycle's first true UI change, is explicitly deferred to its own future FULL round
per the evaluator's own item (6)) — so Depth stays **lean**, matching the binding recommendation.
Applying the iter-75 (1 of 2) lesson: a quiet round is NOT evidence the frontend defect is fixed —
this iteration requires a NAMED cause with cited evidence and a regression test, not just an absence of
recurrence. Applying the iter-75 (2 of 2) and iter-73 lessons: strengthen the goldens with real
discriminating assertions, and if replay shows a mass-simultaneous FAIL again, sort frames by capture
time and open more than one before trusting any auto-generated "selector drift" explanation.

Priority-rubric note (self-check #5): no journey regressed (rule 1 n/a); no coherence-FAIL to
consolidate (rule 2 n/a); this iteration IS the unblocker (rule 3) — the asset-less-frontend defect is
what makes every replay-lane result untrustworthy, and J-07/J-09's weak goldens are named explicitly by
the evaluator as unable to detect a regression today. J-07/J-09 are the smallest concrete, testable
target for the golden work (rule 4); no second risky journey is bundled (rule 5) — the frontend-harness
fix is infrastructure shared by all journeys' evidence quality, not a second product-risk journey. The
owner-blocked items (2s health-ceiling decision, B-1107 concurrency cap, `browser-qa-phase.sh`
ordering-bug permission, the cost/time-budget question, the housekeeping-ledger GOAL_ACHIEVED
criteria question) are explicitly excluded per rule 6 — none of them are re-plannable agent work this
round.

## IN SCOPE

### Backend / harness
- [ ] Root-cause the intermittent asset-less/unstyled QA frontend defect (iter-72/c): read
      `scripts/start-frontend.sh`'s build-if-stale sequence and reconstruct the frontend
      start-command log across the recent voided rounds; confirm or rule out that a concurrent
      invocation of the script (from a second pipeline lane) can run `next build` into the SAME
      live `.next` `DIST_DIR` while an already-running `next start` is serving from it. Land a fix
      (e.g. serializing the build-if-stale sequence with a lock) with a regression test that
      reproduces the pre-fix defect and proves it closed.
- [ ] Strengthen `runs/goal-session-ops-hardening/journey-scripts/J-07.json`'s replay assertions
      (structural smoke steps only — the full step 1-4 acceptance stays LLM-lane-verified, per its
      existing `_notes`, since it cannot be reproduced by a click script): tighten step 1 to require
      the readiness badge's `data-state="ready"` attribute, and tighten step 2 to also require a
      populated scorecard row is present (see Frontend below), not just the section header text.
- [ ] Strengthen `runs/goal-session-ops-hardening/journey-scripts/J-09.json`'s `/data` panel step:
      require ONE of the panel's two real sub-states (`background-compute-idle` or
      `background-compute-active-row`) instead of only the outer panel container's presence, so a
      silent fall-through to the "state unknown / backend unreachable" branch fails the replay.
- [ ] Delete the stray zero-byte `=` file at the repo root (iter-74/c, carried 4 rounds).
- [ ] Clear `runs/goal-session-ops-hardening/state/goldens-regen-pending` of its stale `J-05..J-09`
      listing (all five are `passing`; regeneration was never the correct remedy — iter-73 lesson).

### Frontend
- [ ] Add a `data-testid="scorecard-row-<horizon>d"` attribute to each row in
      `apps/frontend/app/backtest/page.tsx`'s `ScorecardSection` table body (QA hook only — no
      change to any displayed value, computing module, or endpoint) so J-07's strengthened golden
      can assert a populated row exists.

### New user-facing capability
None — this iteration is QA-harness and replay-golden hardening only.

### New information displayed
None.

### New user actions
None.

### UI surface changes
None visible to a user — one additive `data-testid` attribute on already-rendered scorecard rows.

### Product surface delta
No product surface change. The frontend-harness fix affects only the QA/demo pipeline's own
build-and-serve reliability; the golden changes affect only the deterministic replay lane's ability
to detect a regression.

### Blueprint conformance
No new surfaces. J-07 and J-09 keep their existing registered homes (global readiness badge +
`/backtest` for J-07; global readiness badge + `/data`'s `BackgroundComputePanel` for J-09) per
`blueprint.md`'s Information Architecture. No blueprint edit made this iteration (nothing additive to
register — see Data-contract additions below).

### Data-contract additions
None. The new `data-testid` on the Forward-test scorecard rows is a QA-hook attribute on the
ALREADY-registered "Regime score, market phase, realized forward-returns" / forward-aggregate row in
`blueprint.md`'s Data Contract — same computing module (`app.engine.forward_testing`), same endpoint
(`GET /api/backtest`), no second producer, no new field, no new endpoint.

## OUT OF SCOPE

- Re-measuring J-07 step 3's VmPeak/margin, re-tuning `pool_size`/`max_overflow`/`cache_size`, or a
  full-`rebuild` drill on this host — binding "Do not redo" (J-07 step 3 DONE).
- Regenerating any of the J-05..J-09 goldens — binding "Do not redo"; this iteration hand-STRENGTHENS
  J-07's and J-09's assertions, which is different work.
- Re-verifying J-08's or J-09's full live acceptance beyond confirming the strengthened goldens still
  pass — both were freshly verified at iter-75; not an iteration goal again (binding "Do not redo").
- Rendering `stale_for_s` on the badge/preflight banner (iter-72/f) — this cycle's first user-visible
  UI change; deferred to its own dedicated FULL-depth round per the evaluator's own item (6), not
  bundled into this lean harness-repair round.
- The `[NEW]`-flagged walkthrough steps for J-05/J-07/J-08/J-09 and J-06's `reports/perf-budgets.md`
  page timings — explicitly "rides along, never the goal" per the evaluator; excluded to keep this
  round's scope tight.
- Removing the `TRENDORA_FAULT_INJECT_MEMORY_ERROR=data_overview_endpoint` hook at
  `apps/backend/app/api/data.py:119` — it already has backend test coverage
  (`test_get_data_overview_fault_injection_probe_makes_the_endpoint_raise`) and the frontend already
  renders the honest-fallback copy it exists to exercise; this iteration closes the carry by capturing
  the missing LIVE evidence instead (see TESTING REQUIREMENTS TC-7), not by removing working code —
  see `assumptions.md` iter-76.
- Any change to `app.engine.readiness`'s cache/staleness mechanism or `compute_forward_aggregates` —
  both are binding "Do not redo" (DONE at iter-72/iter-14 respectively; byte-identity frozen).
- iter-33/g, the Regime Lab — stays deferred without owner direction (binding "Do not redo").
- Any of the six owner-only questions carried in iteration-state (2s health-ceiling scope, B-1107
  concurrency cap, `browser-qa-phase.sh` ordering-bug permission, the cost/time-budget decision, and
  the housekeeping-ledger GOAL_ACHIEVED-criteria question) — human-owned, not re-planned this round.

## DEFINITION OF DONE

- [ ] Target journeys J-07, J-09 pass via browser-qa-agent (replay lane, on the strengthened goldens,
      plus LLM-lane confirmation of anything replay cannot reach) — TC-3, TC-4, TC-5
- [ ] Required-still-passing journeys J-01, J-03, J-04, J-05, J-06, J-08 remain green (deterministic
      replay, golden on file for all six)
- [ ] No anti-goal violation introduced
- [ ] Root cause of the intermittent asset-less QA frontend page is named with cited evidence and
      fixed with its own regression test — TC-1, TC-2
- [ ] Stray zero-byte `=` file removed from the repo root — TC-6
- [ ] TC-10's `/data` honest-fallback live evidence captured, closing the iter-72/b carry — TC-7
- [ ] `state/goldens-regen-pending` cleared of its stale J-05..J-09 listing — TC-8
- [ ] Unit tests pass; no regressions
- [ ] Dev handoff written at `docs/handoffs/goal-ops-hardening-iter-76-dev.md`

## TESTING REQUIREMENTS

- Browser: J-07, J-09 (target journeys, on the strengthened goldens); J-01, J-03, J-04, J-05, J-06,
  J-08 (required-still-passing, deterministic replay)
- Unit/integration: the new frontend-start concurrency regression test (backend/harness test suite,
  mirroring the `test_start_backend_script.py` subprocess-spawn pattern); `journey-scripts/J-07.json`
  and `journey-scripts/J-09.json` still `validate_script`-clean after editing
- Error cases: a concurrent `start-frontend.sh` invocation against a stale build must not corrupt the
  live server's served assets (TC-2); an armed `data_overview_endpoint` fault-injection must still
  produce the existing honest-fallback frontend state, never a blank crash page (TC-7)

Test-first contract: every DEFINITION OF DONE checkbox and every Data-contract addition above maps to
at least one concrete scenario line, numbered sequentially, of exactly this shape:

- TC-1: given the QA/demo pipeline can invoke `scripts/start-frontend.sh` from more than one lane
  within the same iteration window, when the developer reproduces the intermittent asset-less-page
  defect (iter-72/c) via a targeted reproduction, then the root cause is named with cited evidence
  (specific log lines and/or a failing-before-fix reproduction) and a fix lands with its own
  regression test that fails on the pre-fix code and passes after.
- TC-2: given the TC-1 fix is in place, when two invocations of `scripts/start-frontend.sh` run
  concurrently against a `.next` build that is stale relative to source, then the regression test
  observes exactly one build sequence completing before either process execs `next start`, and any
  request made once the port answers returns a page whose `_next/static` asset references all
  resolve HTTP 200 (no missing-chunk / unstyled render).
- TC-3: given `journey-scripts/J-07.json` step 1 (`goto /`), when the golden replays, then the
  expectation resolves against the CSS selector `[data-testid="readiness-badge"][data-state="ready"]`
  and the step fails if the badge is present with any other `data-state` value.
- TC-4: given `journey-scripts/J-07.json` step 2 (`goto /backtest`), when the golden replays, then it
  additionally asserts at least one `[data-testid^="scorecard-row-"]` element is present, so an
  empty/error-boundary scorecard render fails the replay even though the page header text alone would
  still match.
- TC-5: given `journey-scripts/J-09.json`'s `/data` step, when the golden replays, then the
  expectation resolves against the CSS selector
  `[data-testid="background-compute-idle"], [data-testid="background-compute-active-row"]` and the
  step fails if the panel instead rendered its `background-compute-unknown` (backend-unreachable)
  branch.
- TC-6: given the repo root, when `ls -la` is run after this iteration lands, then no zero-byte file
  named `=` exists.
- TC-7: given the backend is started with `TRENDORA_FAULT_INJECT_MEMORY_ERROR=data_overview_endpoint`
  armed, when `/data` is loaded in the browser, then a screenshot under
  `reports/qa/goal-ops-hardening-iter-76-evidence/` shows the existing frontend honest-fallback text
  ("Dataset coverage could not load from the API. No figures are shown rather than fabricated")
  rendered in place of the coverage panel, and no blank/crashed page.
- TC-8: given `state/goldens-regen-pending` lists `J-05, J-06, J-07, J-08, J-09` before this
  iteration, when this iteration completes, then the file contains no entries for any journey that is
  `passing` with fresh or durable evidence (emptied or removed).

## NOTES

- Binding lessons applied: iter-75 (1 of 2) — a quiet replay round is NOT evidence the asset-less-page
  defect is fixed; TC-1/TC-2 require a NAMED cause plus a regression test, not merely "it didn't
  recur." iter-75 (2 of 2) and iter-73 — a golden's "PASS" is a claim about the golden, not the
  product, and a mass-simultaneous replay FAIL should be sorted by capture time with more than one
  frame opened before trusting an auto-generated "selector/environment drift" explanation; this
  applies if TC-1/TC-2's regression test or the strengthened goldens produce a new mass-FAIL signal
  during this round's own verification pass. iter-72 (2 of 2) — if any lane's own report blames a
  FAIL on "transient/concurrent load," cite a timestamp bracket and open the frame before accepting it.
- Logged to `assumptions.md` (iter-76 — goal-decomposer): the choice to close the TC-10/iter-72/b carry
  by capturing live evidence rather than removing the fault-injection hook, since the hook already has
  backend test coverage and the frontend already implements the honest-fallback copy it exercises.
- Owner questions carried forward untouched (see iteration-state.md "Active blockers" and the last
  eval's owner paragraph): the 2-second health-ceiling scope decision, permission for B-1107's
  concurrency cap, permission to fix the one-line ordering bug in `scripts/automation/browser-qa-phase.sh`,
  the cost/time-budget decision (this session has run over its per-round time budget for many
  consecutive rounds), and the housekeeping-ledger GOAL_ACHIEVED-criteria question (a/b choice). None
  of these are re-planned this round; they remain visible to the evaluator for another owner escalation
  if still unanswered.
