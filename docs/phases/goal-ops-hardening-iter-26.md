# Goal Iteration 26 — Close the two GOAL_ACHIEVED-confirm REJECT gaps on J-09

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** ops-hardening
- **Iteration:** 26
- **Mode:** next
- **Depth:** lean
- **Frontend Present:** yes
- **Target journeys:** J-09
- **Required-still-passing journeys:** J-01, J-03, J-04, J-05, J-06, J-07, J-08
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
    marked block from a launch script is a REGRESSION regardless of test outcomes. The ceilings
    are a physical constraint of the current host (two instant hardware resets under all-core
    vectorized ingest bursts: 2026-07-20 19:17, 2026-07-21 10:33), not a performance budget to
    optimize away. *(critical)*

## GOAL

Close, with fresh and citable evidence, the two specific gaps the iter-25 GOAL_ACHIEVED second-key CONFIRM
run rejected on — J-09's ambiguous `<= 0.1 s` health-budget re-measurement and its unexercised
"failed background compute shows the recorded reason" clause — so the next evaluator/confirm cycle can
close the session honestly.

## BACKGROUND

Iter-25's regular evaluator scored GOAL_ACHIEVED (8/8 passing), but the mandatory second-key CONFIRM run
(`runs/goal-session-ops-hardening/iter-25/eval-confirm.md`) **REJECTED** it on two named, agent-tractable
gaps, both explicitly called "actionable work, not a stall" / "cheap to close honestly" by that confirm
evaluator — not an owner-gated blocker (rule 6 of the priority rubric does not apply here):

1. **The `<= 0.1 s` steady-state health budget is scored met by interpretation, not by its own recorded
   evidence.** `reports/perf-budgets.md`'s only recorded re-measurement (iter-24) shows 3 of 4 statistics
   over budget (mean 0.103597 s, max 0.127788 s vs. official 0.100023 s), while a clean same-build QA read
   (0.094604 s) was never written into the artifact the Acceptance clause names. One quiet-host
   re-measurement, honestly recorded with an explicit verdict, settles it either way.
2. **J-09 step 4's failure branch ("shows a failed background compute with the recorded reason — never a
   silent failure") has no citable evidence.** Every captured panel state to date renders only `completed`;
   the two backend registry tests that guard the served shape (`test_health_background_compute_is_single_source`,
   `test_compute_readiness_composes_background_compute_empty_shape`) were rewritten in iter-25 but — per the
   coordinator's live host note at this dispatch — are **still** running after 50+ minutes with no pass/fail
   line, the same standing 1h+ `loaded_engine` session-fixture cost flagged since iter-25.

Both gaps are narrow and bounded: neither requires touching the byte-frozen dispatch/registry modules, a
schema change, or a live repeat of the memory-exhaustion pattern already tracked as owner-optional backlog
card B-1107. **Depth: no full trigger holds** — this is test-file-plus-one-small-refactor work confined to a
single journey (J-09), touches no persisted schema or Data-Contract computing module/endpoint, the last
verdict was not ESCALATE, and consecutive-lean count (1) is well under the hardening cadence (4). Lessons applied: iter-25's lesson (never leave heavy pytest fixture builds running while a lane
needs a healthy backend / measurement to stay clean) and iter-22's lesson (never leave two contradictory
readings side by side without a stated resolution) both apply directly to gap 1's remeasurement. Per the
priority rubric, this is the smallest, most direct unblocker available (rule 3/4) — no regressed journey
exists (rule 1 N/A) and the last coherence verdict was COHERENCE-PASS (rule 2 N/A), so no consolidation pass
is required beyond these two named items.

## IN SCOPE

### Backend
- [ ] Get `apps/backend/tests/test_health.py -k test_health_background_compute_is_single_source` and
  `apps/backend/tests/test_readiness.py -k test_compute_readiness_composes_background_compute_empty_shape`
  to a pass/fail line, in ONE combined pytest invocation (both target the same session-scoped `loaded_engine`
  fixture — invoking them together builds it once, not twice), on a host with no other pytest process
  competing for memory. Before launching, check for and resolve the two detached runs already in flight
  (wait for them or terminate cleanly) rather than adding a third concurrent build.
- [ ] Add one new test to `apps/backend/tests/test_health.py` that monkeypatches
  `app.engine.forward_testing.get_background_compute_status` to return a crafted `failed` outcome (non-null
  `reason`) and asserts `GET /api/health`'s `background_compute.recent_outcomes[0]` matches it verbatim
  (field-for-field). Run it in the SAME pytest invocation as the two tests above.
- [ ] Take one quiet-host `GET /api/health` re-measurement (the project's official single-sample convention
  plus a 10-sample, 0.5 s-spaced series) with no pytest process running concurrently, and record it in a NEW
  dated section of `reports/perf-budgets.md` (all prior sections, including the "OWNER BUDGET AMENDMENT" and
  its "Revision 1", untouched) with an explicit Holds?/breaches verdict and a plain statement of which
  measurement is now the binding one for J-09's Acceptance clause.

### Frontend
- [ ] Extract the completed/failed rendering decision currently inline in `LastOutcomeSummary`
  (`apps/frontend/app/data/page.tsx`) into one new exported pure function in a new file,
  `apps/frontend/lib/background-compute-last-outcome.ts`, and have `LastOutcomeSummary` call it — byte-identical
  rendered output for the existing `completed` case (refactor only, no behavior change).
- [ ] Add `apps/frontend/lib/background-compute-last-outcome.test.ts` (same `node`-executable convention as
  `background-compute-panel-branch.test.ts`) covering the `completed` and `failed` cases.

### New user-facing capability
None — this iteration closes evidence/verification gaps in a capability (J-09's failure disclosure and
health budget) already shipped in iter-24/25; it adds no new user-visible behavior.

### New information displayed
None.

### New user actions
None.

### UI surface changes
None — the frontend change is a pure extraction of existing render logic into a tested function; rendered
output is byte-identical for every case already captured.

### Product surface delta
None. This is a verification/evidence-closure iteration, not a feature iteration.

### Blueprint conformance
No new surfaces. J-09 keeps its existing registered homes — the global readiness badge (top bar, every page)
and `/data`'s `BackgroundComputePanel` (`blueprint.md` Data Contract row, iter-24/25 entries). No blueprint
edit is made this iteration.

### Data-contract additions
None. `background_compute.recent_outcomes[].reason` (string, present only when `outcome == "failed"`) is
already a registered field on the existing Data Contract row — computing module
`app.engine.forward_testing.get_background_compute_status()`, composed by `compute_readiness`, served only by
`GET /api/health` (unchanged, iter-24 entry in `blueprint.md`). This iteration adds test coverage proving that
existing round-trip; it introduces no second computing module and no second endpoint.

## OUT OF SCOPE

- Any live/browser-triggered *genuine* background-compute failure (e.g. repeating the 5-concurrent-BCW
  memory-pressure pattern) — unsafe on this host, already tracked as owner-optional backlog card B-1107, and
  not required to close either confirm gap (see NOTES / assumption ledger).
- Any change to `app.engine.forward_testing` (incl. `ensure_historical_forward_aggregates_dispatched`'s
  keying/single-flight semantics and `get_background_compute_status()`), `compute_readiness`,
  `compute_forward_aggregates`, `resolved_forward_aggregate_evidence`, or J-08's serving split/empty-state
  machine — all byte-frozen per binding "Do not redo".
- Any change to the panel's existing idle/active/unknown branch logic or copy (`background-compute-panel-branch.ts`,
  `BackgroundComputePanel`'s idle sentence) — already fixed (audit F1), leave byte-exact.
- Any edit to `reports/goal-session-ops-hardening-demo.json` (J-09 demo steps n=13-16 are written and
  verified — never re-author, re-order, or re-cap).
- Any edit to the "OWNER BUDGET AMENDMENT" section, its "Revision 1", or TC-13/TC-14 in `reports/perf-budgets.md`
  — settled owner policy; this iteration only ADDS a new, separate dated section.
- Retargeting `test_forward_testing_serving_split.py`'s `is_latest` monkeypatches or removing the dangling
  imports at `backtest.py:75` / `mcp/tools.py:38` — carried non-blocking item, unrelated to J-09.
- Backlog card B-1107 (global dispatch cap/semaphore) — owner-optional, untouched.
- Running the full pytest suite or any concurrent pytest invocation alongside the quiet-host health
  measurement.

## DEFINITION OF DONE

- [ ] J-09's two confirm-REJECT gaps are closed with fresh, citable evidence: the health-budget clause has an
  unambiguous recorded verdict (TC-1, TC-2) and the failure-branch clause has a passing round-trip test plus a
  passing rendering test (TC-3, TC-4, TC-5)
- [ ] Required-still-passing journeys (J-01, J-03, J-04, J-05, J-06, J-07, J-08) remain green via deterministic
  replay, zero FAIL rows (TC-7)
- [ ] No anti-goal violation introduced — byte-frozen modules untouched (TC-8), no new DB query, no new
  endpoint, no host-guard cap change
- [ ] Unit tests pass: TC-3/TC-4/TC-5 each report a literal pass/fail line with 0 failed; no regressions in
  any touched file
- [ ] `reports/perf-budgets.md` carries the new, unambiguous dated section (TC-1, TC-2)
- [ ] Dev handoff written at `docs/handoffs/goal-ops-hardening-iter-26-dev.md`

## TESTING REQUIREMENTS

- Browser: J-09 regression-only pass — confirm the existing idle/active/unknown panel states and the global
  readiness badge still render exactly as before (no new capture of a live failure state required; see
  NOTES). Smoke replay: J-01, J-03, J-04, J-05, J-06, J-07, J-08.
- Unit/integration:
  - `apps/backend/tests/test_health.py -k test_health_background_compute_is_single_source`
  - `apps/backend/tests/test_readiness.py -k test_compute_readiness_composes_background_compute_empty_shape`
  - new backend test proving the served `failed`-outcome round-trip (name at developer's discretion, same file)
  - new `apps/frontend/lib/background-compute-last-outcome.test.ts`
- Error cases: no new user input/endpoint is introduced this iteration; the "error case" this iteration
  guards is the crafted `failed` outcome itself — the served payload and the rendering function must never
  silently drop the `reason` string or render it with the `ok`/ completed styling.

Test-first contract:

- TC-1: given the backend was freshly started via `scripts/start-backend.sh`, warmup reached
  `readiness: "ready"`, and no pytest or other background job is running on the host, when `GET /api/health`
  is sampled once via the project's official single-sample convention and then 10 more times spaced 0.5 s
  apart, then all 11 raw latency readings are recorded in a NEW dated section of `reports/perf-budgets.md`
  (every prior section byte-unchanged) with an explicit "Holds?" `yes`/`no` value against the unamended
  `<= 0.1 s` steady-state budget for each statistic.
- TC-2: given that new section, when it is written, then it states in plain prose which single measurement
  (this iteration's quiet-host reading, or the prior iter-24 one) is now the CURRENT BINDING figure for J-09's
  Acceptance health-budget clause — never leaving two contradictory readings side by side unresolved.
- TC-3: given any pre-existing detached pytest process for these two tests is first waited-out or terminated,
  when `test_health_background_compute_is_single_source` and
  `test_compute_readiness_composes_background_compute_empty_shape` are executed in ONE combined pytest
  invocation, then the dev/reviewer handoff cites the literal pytest summary line showing both PASSED.
- TC-4: given a new backend test that monkeypatches `app.engine.forward_testing.get_background_compute_status`
  to return `{"active": [], "recent_outcomes": [{"asof_key": <str>, "dataset_version": <str>,
  "outcome": "failed", "started_at": <iso>, "finished_at": <iso>, "duration_ms": <int>,
  "reason": "forced test failure — <literal>"}]}`, when `GET /api/health` is requested via
  `TestClient(main.app)` in the same pytest invocation as TC-3 (sharing the session-scoped `loaded_engine`
  fixture), then the served JSON's `background_compute.recent_outcomes[0]` equals the crafted dict verbatim —
  no field dropped, no field re-derived — and the test reports PASSED.
- TC-5: given the new exported pure function extracted from `LastOutcomeSummary`, when it is called with a
  `completed` outcome (`reason: null`), then it returns `reasonText: null` and `badgeVariant: "ok"`; when
  called with a `failed` outcome carrying `reason: "forced test failure — <literal>"`, then it returns
  `reasonText` equal to that exact string and `badgeVariant: "danger"`.
- TC-6: given `LastOutcomeSummary` now calls the extracted function instead of its own inline ternaries, when
  the existing "idle-with-last-outcome" (`completed`) DOM state is re-captured, then the captured DOM/screenshot
  content is unchanged from the pre-iteration `completed` capture (no visual regression from the refactor).
- TC-7: given the 7 required-still-passing journeys' golden replay scripts, when replayed after this
  iteration's diff, then all 7 report PASS with zero FAIL rows in the merged UI-test-results file for this
  iteration.
- TC-8: given `git diff`/`git status --porcelain` scoped to `apps/backend/app/**` and the byte-frozen module
  list (`app.engine.forward_testing`, `compute_readiness`, `compute_forward_aggregates`,
  `resolved_forward_aggregate_evidence`, J-08's serving split), when checked against the pre-iteration
  snapshot, then none of those modules appear in the diff — only test files and the one new frontend
  lib/test-file pair are touched.

## NOTES

- **Host constraint (coordinator note at dispatch):** the two `test_health.py`/`test_readiness.py` runs from
  the iter-25 reviewer were still running 50+ minutes in with no pass/fail line at this dispatch's start,
  under the same standing 1h+ `loaded_engine` session-fixture cost documented since iter-25. Do not add a
  third concurrent `loaded_engine` build — either await those specific runs (reading their existing logs at
  the scratchpad paths the coordinator noted, if still present) or cleanly terminate them before launching the
  single combined invocation TC-3/TC-4 need.
- **Sequencing:** do not run the quiet-host health remeasurement (TC-1) concurrently with any pytest
  invocation — a `loaded_engine` fixture build is itself the kind of host-memory pressure the iter-25 lesson
  warns changes `/api/health` latency. Take the quiet reading either fully before or fully after the pytest
  runs, never overlapping.
- **Assumption logged:** this spec treats a deterministic, code-level round-trip test (backend
  served-payload + frontend pure-function) as sufficient citable evidence for J-09 step 4's "shows a failed
  background compute with the recorded reason" clause, rather than requiring a live browser capture of a
  *genuinely* triggered failure (which would require repeating the unsafe 5-concurrent-BCW memory-pressure
  pattern, backlog B-1107). See the assumption-ledger entry for this iteration; reversible if a human requires
  an actual witnessed live failure capture instead.
- **If the quiet-host remeasurement (TC-1) still breaches `<= 0.1 s`:** record that plainly too (TC-2 already
  requires an honest either-way statement) — do not round it into a pass. A genuine breach converts audit B5
  from an open question into a live owner decision for the next decomposer/evaluator to route, not something
  this iteration should paper over.
