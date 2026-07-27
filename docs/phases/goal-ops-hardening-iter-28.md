# Goal Iteration 28 — Close the browser-QA evidence gap for J-05/J-07/J-08 and fix the J-06 self-poisoning golden

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** ops-hardening
- **Iteration:** 28
- **Mode:** next
- **Depth:** lean
- **Frontend Present:** no
- **Target journeys:** J-05, J-06, J-07, J-08
- **Required-still-passing journeys:** J-01, J-03, J-04, J-09
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

Finish the independent browser verification that iter-27's account-usage-limit kill left undone for J-05,
J-07 and J-08 (their product fixes are already built and reviewed), and stop J-06 from reporting a false
failure caused by another goal session's file, not this product.

## BACKGROUND

Iter-27 fixed both anti-goal findings ESCALATE surfaced at iter-26 (the concurrent `/backtest` 500 and the
all-zero `/data` coverage panel) and the code review passed, but the browser-QA agent was killed mid-run by
an account usage limit before writing any row for its own three target journeys — J-05, J-07, J-08 landed
`unknown`, and the phase-closure-auditor returned CLOSURE-FAIL on exactly that missing evidence (coordinator
note 1). Per the priority rubric, an `unknown` journey blocking closure outranks new feature work, and the
smallest spec that resolves it is to re-run the SAME already-written browser-qa plan
(`reports/phase-goal-ops-hardening-iter-27-ui-test-plan.md`, UT-01..UT-09) against the UNCHANGED iter-27
build — no new product code for those three journeys. J-06 is bundled in because it is a one-line, zero-risk
casualty of a DIFFERENT, already-diagnosed bug (the golden script's step 1 depends on
`config.yaml:1152`'s `data_quality.drift.report_path`, which points at another, closed goal session's folder
— iter-27's lesson, carried unfixed for two iterations running). Per rule 5 (never bundle two risky
journeys), this iteration deliberately does NOT touch the separate, real AG-8 finding at
`research.py:215` (coordinator note 4) — the iter-27 evaluator named that "DECOMPOSER-PLANNED, not an
opportunistic patch," and mixing it into a re-verification pass would make any new browser-QA failure
undiagnosable (was it the drift-path move, or the memory fix?). It is this session's next dedicated
iteration. Coordinator notes 2 and 3 are carried into TESTING REQUIREMENTS below: keep any backend test
invocation to ONE combined run against the small, fixture-free selector set, and rely on DOM-extraction
cross-checked against the live API for any below-the-fold panel state.

## IN SCOPE

### Backend

- [ ] `config.yaml:1152` (`data_quality.drift.report_path`) and `apps/backend/app/config.py`'s
  `_DEFAULT_DRIFT_REPORT_PATH` constant (currently both `runs/goal-session-mcp-loop/state/drift-report.json`
  — another, closed/archived goal session's folder) move together, byte-identically, to THIS session's own
  `runs/goal-session-ops-hardening/state/drift-report.json`. `app.engine.drift`'s computation,
  `resolve_drift_report_path()`'s env-override-then-config-default resolution order, and both existing
  consumers (`readiness.severity.drift`'s preflight component served by `GET /api/health`; the additive
  `drift` field on `GET /api/data`) are byte-unchanged — this is a file-location change only, same computing
  module, same two serving endpoints.
- [ ] No other backend file changes. The iter-27 AG-8 (`_insert_run_forward_returns`) and AG-3
  (`coverage_from_storage`) fixes stay byte-frozen this iteration (already built + reviewed; only their
  browser verification is outstanding).

### Test infrastructure (QA artifact, not application code)

- [ ] `runs/goal-session-ops-hardening/journey-scripts/J-06.json` step 1: replace the incidental
  `{"text": "DEGRADED"}` expectation on `/` with an assertion on stable Dashboard content that renders
  regardless of the preflight verdict (e.g. the `Market Regime` card heading) — steps 2-11 are untouched.

### New user-facing capability

None — this iteration ships zero new product surface. It closes an evidence gap (independent browser
verification of already-built fixes) and corrects a self-inflicted test-script defect.

### New information displayed

None.

### New user actions

None.

### UI surface changes

None — no frontend file is touched this iteration.

### Product surface delta

None from the user's point of view; the only change a user could ever observe is that `/data`'s coverage
panel and `/backtest`'s concurrent-request handling — already shipped and reviewed at iter-27 — are now also
independently, browser-verified.

### Blueprint conformance

No new surfaces. J-05/J-07/J-08 keep their existing cross-cutting homes (`/data` coverage panel + run detail,
global readiness badge, `/backtest` + MCP `query_backtest`); J-06 keeps its existing cross-cutting
"measured, not a page" home. `runs/goal-session-ops-hardening/state/blueprint.md` already carries this
iteration's additive narrative paragraph (no Data Contract row's computing module or serving endpoint
changes; no Information Architecture change).

### Data-contract additions

None. The drift-report path relocation does not create a new displayed value — `app.engine.drift` stays the
sole computing module and `GET /api/health` / `GET /api/data` stay the sole two serving endpoints for the
existing `drift` field; only the artifact's file-system location moves.

## OUT OF SCOPE

- The AG-8 `research.py:215` finding (`ret_by_run_symbol` accumulates an unbounded in-RAM dict over the
  whole `forward_returns` scan despite the row read being `yield_per`-bounded) — real, minor, unresolved
  since iter-27, and DECOMPOSER-PLANNED as its own dedicated iteration next, not bundled here (rule 5).
- The four `_DEFAULT_*_PATH` constants that ALSO point at `runs/goal-session-mcp-loop/` — the certified-claims
  ledger, staging ledger, pre-registration registry, and referee-audit report paths (`config.py:2215-2286`).
  These intentionally stay rooted in the shared project-level path per goal.md's Constraints ("the referee
  and ledger live in the project... not in the shared framework"); only the drift-report path is the
  confirmed self-poisoning bug (a per-session diagnostic artifact, not a cross-session evidence store) — do
  not touch the other three.
- Audit finding B2 (`_backfill`'s cross-call rollback residual) — carried, unchanged, its own iteration.
- Retargeting `test_forward_testing_serving_split.py`'s four `is_latest` monkeypatches before removing the
  dangling imports at `backtest.py:75` / `mcp/tools.py:38` — carried, unchanged.
- OWNER, non-blocking: whether the 12-24 minute historical `/backtest` first-touch latency needs its own
  budget or a redesign; backlog card B-1107 (global dispatch cap).
- Any new feature, page, or Data-Contract value — this is a pure evidence-closure + test-hygiene iteration.

## DEFINITION OF DONE

- [ ] J-05 passes via browser-qa-agent (TC-1, TC-2, TC-3, TC-4)
- [ ] J-06 passes via browser-qa-agent (TC-9)
- [ ] J-07 passes via browser-qa-agent (TC-5, TC-8)
- [ ] J-08 passes via browser-qa-agent (TC-6, TC-7)
- [ ] Required-still-passing journeys J-01, J-03, J-04, J-09 remain green via deterministic golden replay
  (TC-10) — no journey may regress as a side effect of the drift-path move
- [ ] No anti-goal violation introduced; the iter-27 AG-8 and AG-3 fixes are confirmed still closed by this
  iteration's own fresh browser evidence, and no NEW anti-goal finding is discovered
- [ ] Unit tests pass in ONE combined pytest invocation; no regressions (TC-11)
- [ ] Dev handoff written at `docs/handoffs/goal-ops-hardening-iter-28-dev.md`

## TESTING REQUIREMENTS

- Browser: re-execute `reports/phase-goal-ops-hardening-iter-27-ui-test-plan.md` in full (UT-01 through
  UT-09) against the UNCHANGED iter-27 build — this is the exact plan the account-usage-limit kill
  interrupted; do not regenerate it from scratch. The ONE required deviation: UT-06's concurrent-race date
  must be a historical trading day never yet scanned in THIS run — 2011-03-10 and 2015-09-09 are both already
  consumed (iter-26/27 lesson: never re-trigger a background-compute window on a consumed date). Per
  coordinator note 3, this host returns a blank frame for any scrolled-viewport screenshot — verify
  below-the-fold panel state (the `/data` coverage panel, the full `/backtest` page) via the raw DOM capture
  cross-checked against the live `GET /api/data` / `GET /api/backtest` JSON, not a scrolled screenshot.
  Smoke replay: J-01, J-03, J-04, J-09 (golden scripts, unchanged this iteration).
- Unit/integration (bundle into ONE combined pytest invocation — per coordinator note 2, none of these need
  the expensive `loaded_engine` fixture):
  - `apps/backend/tests/test_drift.py` — `resolve_drift_report_path()`'s env-override and config-default
    cases still pass against the relocated default.
  - `apps/backend/tests/test_config.py -k drift` and `apps/backend/tests/test_readiness.py -k drift` — no
    test anywhere pins the literal string `goal-session-mcp-loop` for the drift path (confirmed absent by
    direct search ahead of this iteration); these selectors just re-confirm no regression.
  - `apps/backend/tests/test_api_data.py -k drift` — `GET /api/data`'s additive `drift` field still resolves
    from the relocated path.
- Error cases: an already-scanned historical `/backtest` view (UT-07) must keep rendering correctly after
  UT-06's race — proves the fix doesn't overcorrect into rejecting a legitimate concurrent duplicate.

Test-first contract:

- TC-1: given the iter-27-built AG-3 stale-coverage fix (`coverage_from_storage`'s fallback branch) is
  unchanged since iter-27, when browser-qa loads `/data` fresh (UT-01), then the page loads with no console
  error and the coverage panel renders (smoke baseline for J-05).
- TC-2: given UT-06 has just bumped `_membership_dataset_version` via a request-path historical `/backtest`
  view on a fresh never-scanned date, when browser-qa loads `/data` (UT-02), then the coverage panel shows
  real per-symbol figures under a label containing "stale" — never the all-zero sentinel ("— → —" /
  "UNIVERSE 0") — cross-checked against `GET /api/data`'s live JSON showing `coverage_status: "stale"`.
- TC-3: given the current `dataset_version` has a matching `CoverageSnapshot` row (UT-03's precondition, a
  rebuild if UT-02 was just run), when browser-qa loads `/data`, then the panel shows the "current" state
  with no stale label, matching `GET /api/data`'s `coverage_status: "current"`.
- TC-4: given a store where no coverage has ever been computed for any version (UT-04's fixture), when
  browser-qa loads `/data`, then the panel shows the unchanged "not yet computed" empty state, matching
  `GET /api/data`'s `coverage_status: "not_yet_computed"`.
- TC-5: given `/backtest` is loaded at the default (latest) view (UT-05), when browser-qa navigates there,
  then the page renders with no console error and the "Latest" badge visible (smoke baseline for J-07/J-08).
- TC-6: given two concurrent `GET /backtest` requests target the SAME never-scanned historical date (UT-06),
  when both fire at once, then both return HTTP 200 (no "Exception in ASGI application" line in
  `logs/backend.log` for that window) and the full-page (not viewport) capture — or, where screenshots are
  blank per coordinator note 3, the raw DOM capture cross-checked against the live `GET /api/backtest` JSON —
  shows normal page content, not an error page.
- TC-7: given an already-scanned historical date exists (any date present in `GET /api/runs`'s output,
  distinct from UT-06's date), when browser-qa loads `/backtest?as_of=<that date>` (UT-07), then the page
  renders the SAME evidence values `GET /api/backtest` returns for that as-of, consistent with what UT-06
  already established for the never-scanned date.
- TC-8: given the stale-coverage notice from TC-2 is visible, when browser-qa inspects its copy/styling
  (UT-08), then the notice reads as a calm, factual sentence (no red/alarm styling, no "error" wording) — a
  ux regression guard on J-07/J-08's "honest status, never hype" acceptance clause.
- TC-9: given `runs/goal-session-ops-hardening/journey-scripts/J-06.json` step 1's expectation is changed to
  stable Dashboard content and `config.yaml`'s `drift.report_path` no longer points at another session's
  folder, when the deterministic golden replay runs J-06 end-to-end (all 11 steps), then every step's expect
  clause holds and the merged `ui-test-results.md` shows `UT-J-06 PASS`.
- TC-10: given J-01/J-03/J-04/J-09's golden scripts are unchanged, when their deterministic replays run
  alongside this iteration's drift-path relocation, then all four report PASS in the merged
  `ui-test-results.md` with zero new lines in `logs/backend.log` beyond the pre-existing, already-tracked
  `research.py:215` MemoryError signature (no new anti-goal finding introduced).
- TC-11: given the four fixture-free selectors above (`test_drift.py`, `test_config.py -k drift`,
  `test_readiness.py -k drift`, `test_api_data.py -k drift`), when they run in ONE combined pytest
  invocation, then every selected test reports PASS and no test references the literal string
  `goal-session-mcp-loop` for the drift path.

## NOTES

- **Depth justification (self-check item 4):** the iter-27 evaluator's own next-step recommendation
  suggested full depth, but the deterministic trigger checklist does not fire for THIS iteration's actual
  remaining scope: (1) not structural/cross-cutting — one config-value relocation plus one test-script string
  fix, no refactor, no ≥3-module interaction; (2) no data-model or Data-Contract computing-module/serving-
  endpoint change; (3) the LAST evaluator verdict (iter-27) was CONTINUE, not ESCALATE — the mandatory-full
  trigger from iter-26's ESCALATE was already discharged by iter-27's own full-depth dispatch; (4) consecutive
  lean iterations dispatched = 0 (hardening cadence 4, not met). No full trigger holds, so lean is the
  correct depth, not a shortcut — the lean cycle (developer -> reviewer -> browser-qa) is exactly matched to
  this iteration's one trivial code change plus a full re-run of an already-written browser-qa plan.
- **Target selection (self-check item 5):** followed the priority rubric's "unblockers next" — J-05/J-07/J-08
  are the sole `unknown` journeys blocking CLOSURE-FAIL, and completing their verification (rather than any
  new feature) is the smallest, least-risky path to resolving it. J-06 is bundled only because its fix is
  trivial/zero-risk and shares no code path with the browser-QA re-verification.
- Coherence: iter-27's coherence.md verdict was COHERENCE-PASS — no consolidation pass required this
  iteration.
- Lesson applied (iter-26/iter-27, "Applies to: any iteration whose QA triggers a background-compute window
  or time-machines to a historical as-of date"): UT-06's date MUST be freshly chosen, never 2011-03-10 or
  2015-09-09, and the executing agent must diff `logs/backend.log` (ASGI errors, `backtest_timing total_ms`)
  plus `scanner_runs`/`coverage_snapshot` after the run, before scoring the browser narrative as evidence.
- Lesson applied (iter-25, "any golden script whose `expect` is a readiness/badge string"): TC-9's fix
  deliberately moves J-06 step 1 OFF any readiness/preflight-derived string entirely, onto plain Dashboard
  content, so this class of self-poisoning cannot recur for this journey.
- No assumptions.md entry this iteration — no genuine goal-ambiguity was resolved; scoping decisions above
  (deferring the AG-8 research.py fix, not touching the ledger-family default paths) follow directly from
  goal.md's own Constraints text and the evaluator's explicit "DECOMPOSER-PLANNED, not opportunistic" framing,
  not an interpretation call.
