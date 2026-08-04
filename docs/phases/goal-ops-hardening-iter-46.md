# Goal Iteration 46 — Bound the two unbounded evidence-page memory accumulators; live-drill J-05's fast path

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** ops-hardening
- **Iteration:** 46
- **Mode:** next
- **Depth:** full
- **Full trigger:** 3 — the prior iteration's verdict was ESCALATE; per the binding rule ("If the prior
  evaluator log emitted `ESCALATE`, you MUST set depth to `full` for this iteration"), this is
  mandatory, and it is independently the evaluator's own bound-by-default recommendation for this
  iteration. Reinforced by trigger 1: the two functions touched (`app.engine.research`,
  `app.engine.forward_testing`) sit on the SAME cross-cutting serving path the blueprint's "Membership
  timeline / research hot-key caches" row already registers as feeding `/data`, `/sectors`, `/themes`,
  `/research/*`, and `/evidence` — several required-still-passing journeys transitively depend on its
  correctness.
- **Frontend Present:** no
- **Target journeys:** J-05, J-07
- **Required-still-passing journeys:** J-01, J-03, J-04, J-06, J-08, J-09 (full regression of the
  entire currently-passing set — the iter-45 evaluator explicitly asked that "all eight journey checks"
  be re-run afterward, each with its own unique screenshot, since TC-11's shared-file defect has now
  reopened twice)
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
    optimize away. *(Owner amendment 2026-07-31, two corrections of record — nothing above is
    relaxed: `memory_cap_mb` / `malloc_arena_max` live in `config.yaml`, not in `host-guard.env`;
    and the 2026-07-20/21 resets were subsequently attributed to an uncorrected hardware
    data-fabric fault (`host-guard.env`, 2026-07-30), so the ceiling VALUES are an owner-set
    envelope — re-set by the dated entry in "Additional binding notes" below — while this
    paragraph's prohibition on agents removing, weakening, or bypassing caps is unchanged.)*
    *(critical)*

## GOAL

Stop the backend from exhausting its memory when someone simply loads the Evidence page — the two
per-observation accumulators the iter-45 audit named (`research.py:777`, `forward_testing.py:2343`)
must retain at most one bounded slice at a time instead of the claim's whole cohort — and give J-05's
already-built append-forward fast path its first genuine live proof at full scale.

## BACKGROUND

The iter-45 evaluator measured a ~42-minute total outage (`logs/backend.log`, zero access-log lines
between 01:52Z and 02:34Z) with **16 of the 24** `MemoryError`s inside that window entering through
`evidence.py:168` — `GET /api/evidence`'s serving path, reachable from ORDINARY PAGE BROWSING, not only
an ingest job. The evaluator named the exact two sites and gave the next round ONE job: "stop the app
running out of memory while somebody is just looking at a page… put a firm limit on those two places,
then prove it by loading the Evidence page while a data job runs." I verified both sites directly rather
than taking the naming on faith:

- `_combination_observations` (`app.engine.research:748-807`) builds `ret_by_run_symbol` — one dict
  entry per `(run_id, symbol)` — over the ENTIRE horizon's `forward_returns` population in a single
  pass, unbounded by `as_of=None` on the evidence path. Live-measured on the current DB:
  **1,285,609 rows at horizon=20**, **1,263,406 at horizon=60** — the SAME order of magnitude
  `_factor_observations`'s pre-iter-29 accumulator held (803,042 measured then) before it was bounded.
  `_factor_observations` itself is ALREADY fixed (iter-29): it discovers `_runs_with_fr` once, then
  walks it in slices of `research.factor_join_run_chunk`, building + discarding each slice's
  `_fr_slice_map` join map in turn. `_combination_observations` — its sibling, used by combination-kind
  evidence-ledger claims and the Combination Lab — never received the same treatment.
- `compute_drawdown_expectations` (`app.engine.forward_testing:2270-2392`) already streams+chunks its
  `stored_by_key` READ by the existing `research.drawdown_expectations_ticker_chunk` knob (iter-36) —
  but every chunk's rows land in the SAME dict, retained whole, before the phase-aggregation loop
  (lines 2354-2370) ever consumes them. The QUERY is bounded; the RETENTION is not — the exact "bounded
  read, unbounded retention" shape this session's own iter-40 lesson (`.yield_per()` bounds the cursor,
  not the accumulator) already named once.

Applying the binding iter-45 lesson ("check the live data basis can satisfy a fix's precondition before
committing an iteration to it"): I confirmed BOTH sites are genuinely live-reachable before planning
this fix, not assumed. The live evidence ledger (`runs/goal-session-mcp-loop/state/certified-claims.jsonl`)
carries 7 non-forward-walk claims; exactly **one** has `kind == "combination"` (exercising
`_combination_observations`), and every claim's horizon (20 or 60) is inside `walk_forward.
underwater_horizons: [1, 5, 10, 20, 60]` (exercising `compute_drawdown_expectations` for all 7). A single
`GET /api/evidence` load genuinely reaches both hot spots.

I also verified, rather than assumed, that half of eval item (2) ("add a log line to the outer failure
handler") is ALREADY closed in the current committed tree: `_run_job`'s outer `except Exception` handler
(`data_manager.py:4809-4865`) and the per-date isolated worker's `MemoryError` branch (`:3451-3467`) both
already call `_log_isolation_failure`, landed in-audit during iter-45 (documented "ops-hardening iter-45
FIX (audit B6)"). What remains open, per `iteration-state.md`'s "Do not redo" list, is the last two
unprotected `logger.exception` calls at `data_manager.py:5058` and `:5091` (`_fail_unlaunched_job`'s and
`_fail_unlaunched_resume`'s own bookkeeping-failure handlers) — small, mechanical, bundled here per this
session's established convention for carried small items riding alongside the one risky change (rule 5).

Per rule 5 (never bundle two risky changes): bounding the two evidence-path accumulators — named
together by the SAME evaluator recommendation as one job, fixed by the SAME already-audited pattern — is
this iteration's ONE risky product-code action. The log-call guard, the `journey-scripts/J-07.json`
anchor check, and J-05's live drill are small/verification work, not a second risky change. The
out-of-process watchdog (perf-budgets.md's OTHER named "highest-value" candidate) is deliberately
deferred again — a distinct new mechanism, not a completion of this row's existing bound (see OUT OF
SCOPE). Per rule 1, no journey is `regressed` this iteration (both targets are `failing`, unchanged in
status, per the iter-44 evaluator's own ruling on the `regressed`-vs-`failing` distinction). Per rule 2,
iter-45's coherence verdict was COHERENCE-PASS (zero blocking) — no consolidation pass is forced.

See `assumptions.md` iter-46 for the reasoning on listing J-05 as a Target journey even though this
iteration's own code diff does not address run 281's specific failure mode.

## IN SCOPE

### Backend

- [ ] `app.engine.research._combination_observations`: refactor `ret_by_run_symbol` from a single
      whole-history pass into the SAME bounded-slice pattern `_factor_observations`/`_fr_slice_map`
      already use — discover `_runs_with_fr` once, walk it in slices of the EXISTING
      `research.factor_join_run_chunk` knob, build + discard each slice's join map before the next. No
      new config knob. Returned `observations` list must stay byte-identical.
- [ ] `app.engine.forward_testing.compute_drawdown_expectations`: restructure so each ticker chunk's
      (`research.drawdown_expectations_ticker_chunk`, unchanged) `stored_by_key` slice is folded into
      `by_phase_mdd`/`by_phase_uw`/`by_phase_ttr`/`by_phase_returns` immediately and discarded before the
      next chunk, instead of retaining every chunk's rows in one dict until the phase-aggregation loop
      runs. No new config knob. Returned `by_phase` payload must stay byte-identical.
- [ ] Fixture-backed byte-identity tests for both refactors against a pinned pre-fix reference oracle,
      including a real reproduction of the live ledger's one `combination`-kind claim.
- [ ] Size-bound assertions (mirroring `_factor_observations`'s TC-1-style live-size check) proving peak
      live accumulator size for both refactored functions is bounded by one chunk's width, not the full
      cohort/horizon population.
- [ ] Guard the last two unprotected `logger.exception` calls — `data_manager.py:5058`
      (`_fail_unlaunched_job`) and `:5091` (`_fail_unlaunched_resume`) — with the SAME
      `_log_isolation_failure` degrade-to-marker convention already applied at the other 19 sites
      (iter-44/am, iter-45 audit B6).
- [ ] Verify `runs/goal-session-ops-hardening/journey-scripts/J-07.json`'s dataset-size anchor
      (`"n=14647"` in the current file; the iter-45 eval flagged an unverified `n=8991`) against the live
      dataset's actual, verified count; correct if stale.

### Frontend

None — this iteration is a backend memory-bound fix with no UI-visible change in shape.

### New user-facing capability

Loading the Evidence page (with or without a concurrent data job running) no longer risks exhausting the
backend's memory or taking the whole app down; a single-day backfill of a genuinely unsnapshotted
historical date (J-05's defining case) gets its first full-scale live proof of the already-built
append-forward fast path.

### New information displayed

None.

### New user actions

None.

### UI surface changes

None — no new component; the Evidence page, global readiness badge, and `/data` panels keep their
existing shape and byte-identical values.

### Product surface delta

None visible in shape for a healthy run. The observable delta is that the Evidence page and concurrent
heavy jobs coexist without exhausting memory or freezing the app — a reliability fix, not a new feature.

### Blueprint conformance

J-05 and J-07 keep their existing cross-cutting homes per
`runs/goal-session-ops-hardening/state/blueprint.md`'s Information Architecture table (J-05: Data
Manager / Scanner Runs / Dashboard / Research / Evidence; J-07: global readiness badge + `/backtest`) —
no new page/nav/route this iteration. Blueprint updated with an iter-46 narrative paragraph and a
`[TARGETED, not yet built]` addendum on the "Membership timeline / research hot-key caches" Data-Contract
row, completing that row's own iter-29/iter-36 AG-8 bound work.

### Data-contract additions

None. This is an implementation-only completion of the ALREADY-registered "Membership timeline /
research hot-key caches" row — same computing modules (`app.engine.research`, `app.engine.forward_testing`),
same tables, same serving endpoints (`GET /api/evidence`, `/research/*`'s Combination Lab), byte-identical
output required. No second producer, no new field, no schema change.

## OUT OF SCOPE

- The out-of-process watchdog / shutdown-deadline mechanism (perf-budgets.md's OTHER named
  "highest-value" candidate, deferred at iter-45) — deliberately deferred again; a distinct new
  mechanism, not this iteration's one risky action (rule 5).
- Extending the incremental membership-timeline fast path (iter-45) to historical gap-fill inserts — out
  of scope since iter-45, unaffected by this iteration.
- A sixth `_BarCache.prefill`/`_SymbolColumns`/`bars_asof` bound attempt (`iteration-state.md`'s
  "Do not redo" — "No sixth `_BarCache.prefill` attempt").
- Rewriting `_combination_observations`'s NULL-exclusion semantics or `compute_drawdown_expectations`'s
  phase-classification logic beyond the accumulator bound — output must stay byte-identical.
- The same thread-launch-guard class gap in `warmup.start_warmup` (`forward_testing.py:1691`) — same
  class as iter-43's fix, no evidenced incident there, carried.
- iter-33/g — Regime Lab's cold `view=pooled` background dispatch (deferred a TWELFTH time).
- iter-29/b and the badge wording after a permanently failed warm-up; iter-31/e; iter-32/f; iter-36/n;
  iter-37/o; iter-37/q; iter-39/u; iter-43/ag — carried, untouched, none blocking J-05/J-07.
- J-07's `[NEW]` walkthrough recording and J-05's real acceptance frames — capture-only, never an
  iteration's own goal (rule 7); ride along with whichever iteration lands the passing evidence.
- Any further `docs/goal.md` edit or `memory_cap_mb`/host-guard cap change — no owner items outstanding.

## DEFINITION OF DONE

- [ ] `_combination_observations`'s live peak accumulator size is bounded by one
      `research.factor_join_run_chunk` slice, not the full horizon population (TC-1).
- [ ] `compute_drawdown_expectations`'s live peak `stored_by_key` size is bounded by one
      `research.drawdown_expectations_ticker_chunk` slice, not the claim's whole cohort (TC-2).
- [ ] Both refactored functions produce byte-identical output to a pinned pre-fix reference oracle for
      the same inputs, including the live ledger's one `combination`-kind claim (TC-3).
- [ ] `GET /api/evidence` (rendering all 7 live claims) stays within its committed budget and
      `GET /api/health` stays responsive throughout, while a heavy data job runs concurrently — no
      MemoryError-triggered outage, closing iter-45/ap (TC-4).
- [ ] `data_manager.py:5058` and `:5091` are guarded with `_log_isolation_failure` and hold under a
      parametrized textless-`MemoryError` test (TC-5).
- [ ] `journey-scripts/J-07.json`'s dataset-size anchor matches the live, verified dataset count (TC-6).
- [ ] J-05's defining case (a day confirmed absent from `/scanner-runs` beforehand) gets its first
      full-scale live drill of the append-forward fast path, scored honestly whichever way it lands
      (TC-7).
- [ ] J-07 steps 1-4 hold on re-verification — no regression (TC-8).
- [ ] Target journeys J-05, J-07 re-verified via browser-qa-agent, scored on their actual live result.
- [ ] Required-still-passing journeys J-01, J-03, J-04, J-06, J-08, J-09 all report PASS with unique,
      dated evidence — no two journeys sharing one screenshot file (TC-9).
- [ ] No anti-goal violation introduced; AG-8's unbounded-load ban and AG-10's caps stay enforced
      end-to-end.
- [ ] Unit tests pass; no regressions.
- [ ] Dev handoff written at `docs/handoffs/goal-ops-hardening-iter-46-dev.md`.

## TESTING REQUIREMENTS

- Browser: J-05 (`journey-scripts/J-05.json`, re-triggered against a date freshly confirmed absent from
  `/scanner-runs`, not a stale default date), J-07 (`journey-scripts/J-07.json`, all 4 steps); full
  regression replay of J-01, J-03, J-04, J-06, J-08, J-09; a dedicated Evidence-page-under-concurrent-load
  scenario (TC-4). Evidence capture must produce a distinct, checksum-verified screenshot per journey —
  no two journeys sharing one capture (closes/keeps closed iter-43/ai, reopened iter-45/ar).
- Unit/integration: live/instrumented size-bound assertions for both refactored accumulators; a
  fixture-backed byte-identity test comparing refactored vs. pre-fix reference-oracle output, including a
  reproduction of the live ledger's one `combination`-kind claim; a parametrized textless-`MemoryError`
  test for `data_manager.py:5058`/`:5091`.
- Error cases: a per-claim compute failure (`MemoryError` or otherwise) at either bounded site must still
  degrade via the EXISTING isolate-and-continue contract (`expectations_status: "unavailable"` for that
  one claim, `GET /api/evidence` still returns HTTP 200 with every other claim rendered) — never crash or
  blank the whole response.

Test-first contract: every DEFINITION OF DONE checkbox and every Data-contract addition above maps
to at least one concrete scenario line below.

- TC-1: given `_combination_observations`'s current single-pass `ret_by_run_symbol` dict (built over the
  WHOLE horizon's `forward_returns` population in one shot, unbounded at `as_of=None`), when refactored
  to walk `_runs_with_fr`-discovered run ids in slices of `research.factor_join_run_chunk` (mirroring
  `_factor_observations`), then a unit test asserts peak live accumulator size is bounded by (chunk width
  × symbols-per-run), never by the full ~1.28M-row horizon-20 population measured live on the current DB.
- TC-2: given `compute_drawdown_expectations`'s current `stored_by_key` dict (already
  ticker-chunked for its QUERY via `research.drawdown_expectations_ticker_chunk` but RETAINED whole
  across every chunk before the phase-aggregation loop runs), when refactored so each chunk's rows are
  folded into the by-phase accumulators immediately and that chunk's `stored_by_key` slice is discarded
  before the next, then a unit test asserts peak live accumulator size is bounded by (chunk width tickers
  × their forward-returns rows), never by the claim's whole cohort.
- TC-3: given a pinned pre-fix reference oracle run over a fixed database state (including the live
  ledger's one `kind == "combination"` claim), when compared to this iteration's refactored
  `_combination_observations` output and `compute_drawdown_expectations` output for the SAME inputs, then
  both are byte-identical (fixture-backed equality test).
- TC-4: given the backend running with both accumulators bounded, when `GET /api/evidence` is loaded
  (rendering all 7 live ledger claims, so both hot spots are genuinely exercised) WHILE a heavy
  backfill/forward-aggregate-warm job runs concurrently, then the page returns HTTP 200 within its
  committed budget and `GET /api/health` stays responsive (HTTP 200) at every poll throughout — no
  MemoryError-triggered outage.
- TC-5: given `data_manager.py:5058` (`_fail_unlaunched_job`) and `:5091` (`_fail_unlaunched_resume`)'s
  current bare `logger.exception` calls, when wrapped with the SAME `_log_isolation_failure`
  degrade-to-marker convention already applied at the other 19 sites, then a parametrized test raising a
  textless `MemoryError` from inside each site's own logging call passes without the second exception
  escaping the handler.
- TC-6: given `journey-scripts/J-07.json`'s dataset-size anchor (current file reads `n=14647`; the
  iter-45 eval flagged an unverified `n=8991`), when checked against the live dataset, then the anchor
  matches the live, verified count — corrected in the diff if it does not.
- TC-7: given a historical trading day CONFIRMED absent from `/scanner-runs` immediately before the run
  (checked via the UI/API, not assumed), when a backfill covering exactly that one day is submitted via
  `/data` and run to completion, then EITHER (a) within 300 seconds the run reaches status `ok`,
  `/scanner-runs` lists the new date with its rendered leaderboard, and the persisted run record's
  `aggregates_refreshed` includes `"membership_timeline"`, OR (b) if it still fails, `logs/backend.log`
  now names the failure explicitly (per TC-5's logging convention already in place) instead of leaving no
  trace — either outcome is recorded honestly in the dev handoff and eval, never silently rounded to a
  pass.
- TC-8 (regression): given J-07 steps 1-4 (full-basis warm, 1Hz health poll, VmPeak margin, induced-pressure
  abort), when re-run against this iteration's build, then all four hold — `horizons_done` advances past
  0 within 120 seconds, every health poll returns HTTP 200 within its ≤2s bounded-compute-window budget,
  VmPeak stays under the 8192MB cap with its margin recorded in `reports/perf-budgets.md`, and the induced
  memory-pressure abort degrades honestly (per-item isolation) without deadlock, wedge, or restart.
- TC-9: given the full required-still-passing set (J-01, J-03, J-04, J-06, J-08, J-09), when the full
  regression replay runs against this iteration's build, then all six report PASS with dated evidence,
  and an `md5sum` check over the evidence directory confirms every one of the eight journeys checked this
  iteration (six required-still-passing plus J-05/J-07) has its own unique screenshot file — no two
  sharing one capture.

## NOTES

- Applies the binding iter-38/39/42 lessons: this fix mirrors an ALREADY-audited pattern
  (`_factor_observations`/`_fr_slice_map`, iter-29) rather than inventing a new one; TC-4/TC-8 measure
  the whole page load / whole warm job, never an isolated sub-call.
- Applies the binding iter-40 (second) lesson verbatim: `.yield_per()`/per-chunk streaming bounds the
  QUERY, not the accumulator — `compute_drawdown_expectations`'s pre-fix shape is exactly this gap
  (bounded read, unbounded retention), and TC-2 is written to catch a regression back into it.
- Applies the binding iter-45 (second) lesson: before committing to this fix I confirmed the live
  evidence ledger actually contains an instance of the shape being fixed (one `combination`-kind claim
  among 7, all horizons inside `underwater_horizons`) rather than assuming reachability — see BACKGROUND.
- Applies the binding iter-44 lesson (a memory-pressure guard proven by one green run is not proven):
  TC-1/TC-2's size-bound assertions and TC-3's byte-identity test must be run to green before any claim
  of "bounded," and TC-4's live drill is the real proof, not a narrowed function-level measurement alone.
- See `runs/goal-session-ops-hardening/state/assumptions.md` iter-46 for the reasoning on listing J-05 as
  a Target journey even though this iteration's own diff does not address run 281's specific failure
  mode — TC-7 is scored honestly either way.
- `reports/perf-budgets.md`'s "For the evaluator" section (iter-44 dated entries) and the iter-45 eval.md
  are the primary evidentiary sources for this iteration's diagnosis — read them before re-deriving the
  call chain from scratch.
