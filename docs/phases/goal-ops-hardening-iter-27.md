# Goal Iteration 27 — Close the two ESCALATE-flagged anti-goal findings (concurrent /backtest 500 + stale default-view coverage)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** ops-hardening
- **Iteration:** 27
- **Mode:** next
- **Depth:** full
- **Frontend Present:** yes
- **Target journeys:** J-05, J-07, J-08
- **Required-still-passing journeys:** J-01, J-03, J-04, J-06, J-09
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

Close, with fresh citable evidence, the two unresolved anti-goal findings the iter-26 evaluator's ESCALATE
verdict cited — an unhandled `IntegrityError` that reaches the user as an HTTP 500 when two concurrent
`/backtest` requests race the same never-scanned historical date's forward-returns write, and the Data
Manager's `/data` coverage panel silently rendering an all-zero "not yet computed" dataset for a fully
populated database after that same kind of request-path visit advances the coverage cache's version stamp.

## BACKGROUND

Iter-26 re-verified all 8 journeys passing but returned **ESCALATE** (trigger 3, mandatory full depth — no
exceptions) because its own QA lane exposed two previously-unrecorded, unresolved anti-goal findings while
exercising J-07/J-08/J-09 for regression: (1) `logs/backend.log:81004` shows an unhandled
`sqlite3.IntegrityError: UNIQUE constraint failed: forward_returns.run_id, forward_returns.symbol,
forward_returns.horizon` escaping to uvicorn from `api/backtest.py:171 -> forward_testing.
backfill_run_forward_returns:1667 -> _insert_run_forward_returns:390` — the first such failure in the whole
81k-line logfile — when two never-scanned historical `/backtest` navigations raced each other; (2) that same
QA run's own screenshot (`UT-J-09-01-data-page-top-badge.png`, 18:33Z) shows `/data`'s coverage panel reading
PRICE HISTORY "— → —" / UNIVERSE 0 for a database that `J-07-verify.png` (18:25Z, eight minutes earlier) shows
holds 1996-01-02 → 2026-07-22 / universe 540. The evaluator scored both `minor` (service never went down,
no whole-table load occurred) but explicitly refused GOAL_ACHIEVED over them and named a full-depth,
three-item next round: (1) capture what the user actually sees when the race happens (full page, not
viewport), (2) stop the 500 by lifting the freeze on `forward_testing.backfill_run_forward_returns` on
purpose, (3) make `/data` honest instead of showing zeros for a populated DB.

**Root cause, verified by direct code read before writing this spec (not assumed):**
- **Finding 1 (AG-8).** `backfill_run_forward_returns` already has a tolerant-of-a-concurrent-duplicate design
  — `_commit_forward_returns_concurrency_safe` (iter-28/J-41 legacy) wraps the loop's *final* `session.commit()`
  in a `try`/`except IntegrityError: session.rollback()`. But `_insert_run_forward_returns`'s per-symbol loop
  (`forward_testing.py:384-431`) calls `session.add(ForwardReturn(...))` for one symbol/horizon (line 413) and
  then, for the *next* symbol, calls `close_on`/`bars_after` (lines 390/393) — both plain `session.exec(select(...))`
  reads, which trigger SQLAlchemy's default autoflush of the still-pending `add()` from the prior symbol. If a
  concurrent sibling request already committed that exact `(run_id, symbol, horizon)` key, THIS autoflush is
  where the `IntegrityError` actually fires — not at the final, already-guarded commit. This matches the
  traceback exactly: `_insert_run_forward_returns:390` is the `close_on(...)` call, not an INSERT statement.
  The existing guard covers the wrong point in the control flow.
- **Finding 2 (AG-3).** `coverage_from_storage` (`data_manager.py:1095-1131`) resolves the default
  (`as_of=None`) view's key via `_resolve_coverage_asof` (→ `max(ScannerRun.asof_date)`, unaffected by an old
  historical run) and `_membership_dataset_version` (`research.py:1550`) — a **global** stamp
  (`max(scanner_runs.id)`, `count(scanner_runs)`, bars manifest, `min_history_bars`). Any new `ScannerRun` row
  *anywhere*, including one created by a request-path historical `/backtest` create-once view for a date
  decades in the past, bumps this stamp. When the exact-match `CoverageSnapshot` lookup then misses, the
  function falls straight to `_coverage_not_yet_computed_payload`'s all-zero sentinel — even though a real,
  previously-computed row for the *same* `asof_key` still exists under the *older* stamp. The existing
  explicit-`as_of` self-heal (`coverage_from_storage:1129`, gated on `as_of is not None`) cannot help here
  because the affected view is the *default* one.

Both fixes are bounded, additive, and stay inside the already-established per-row idioms this module already
uses (a tolerant-duplicate commit; a labeled fallback state) — neither requires a schema change or a second
Data Contract producer. **Depth: full — trigger 3 (prior verdict was ESCALATE), mandatory, no exceptions.**
Per the priority rubric: rule 1 (regressed journeys) does not apply — no journey went passing→failing; rule 2
(consolidation before features) applies in spirit — the last `coherence.md` was COHERENCE-PASS so no forced
consolidation, but this iteration adds zero new journeys/features regardless, exactly matching the evaluator's
own "no new features" instruction; rule 6 (human-blocked) does not apply — both findings are agent-tractable,
as the evaluator itself concluded when rejecting STALLED. This iteration deliberately does **not** bundle
audit finding B2 (`ensure_historical_forward_aggregates_dispatched`'s `Thread.start()` failure leaving the
badge stuck on "running (1)") even though it also lives in `app.engine.forward_testing` and is nominally
"decomposer-planned, freeze-lift-pending" — it is a *different* function, unrelated to either ESCALATE
finding, non-blocking, and bundling it would be a second, unrelated risky concurrency change in the same
module the ESCALATE fix already touches (rubric: never bundle two risky changes). It stays carried, unchanged,
in OUT OF SCOPE below.

**Lessons applied:** the iter-26 lesson ("a regression-only browser pass can silently exercise a *heavier*
code path than the journey intends... always diff `logs/backend.log` ... and `scanner_runs`/`coverage_snapshot`
after a browser lane runs, before scoring its narrative as evidence") governs this iteration's own TC-1/TC-2
reproduction below — it is a single, deliberate, bounded, controlled repeat of the exact scenario (to prove
the FIX), not a routine regression check, and every other journey's regression pass in this iteration must
pick a date that already has a snapshot (iteration-state.md "Do not redo," carried forward). The iter-22 lesson
("never leave two contradictory readings side by side without a stated resolution") governs the perf-budgets
timestamp correction below. The binding freeze list (`app.engine.forward_testing`'s `compute_forward_aggregates`,
`resolved_forward_aggregate_evidence`, `ensure_historical_forward_aggregates_dispatched`'s keying/single-flight
semantics, and J-08's serving split) is lifted **only** for `_insert_run_forward_returns`/
`backfill_run_forward_returns`, on purpose, for this bounded fix — everything else in that freeze list stays
byte-frozen. See the assumption-ledger entry (iter-27) for the interpretation call on the coverage fix's
shape (stale-label fallback, never a request-path recompute).

## IN SCOPE

### Backend
- [ ] `apps/backend/app/engine/forward_testing.py` — extend `_insert_run_forward_returns`'s existing
  tolerant-of-a-concurrent-duplicate design (currently only `_commit_forward_returns_concurrency_safe`'s final
  commit) to also survive a mid-loop autoflush collision: when a `session.exec(...)` read inside the per-symbol
  loop (`close_on`/`bars_after`) triggers an autoflush that raises `IntegrityError` on a still-pending, now-
  colliding `ForwardReturn` insert from an earlier symbol in the SAME call, catch it, roll back to discard only
  the duplicate row(s) (a concurrent writer's committed row is byte-identical for frozen-seed data, per
  `_commit_forward_returns_concurrency_safe`'s own established reasoning), and continue the loop for the
  remaining symbols/horizons rather than letting the exception escape. Freeze lifted ON PURPOSE for this one
  function only; `compute_forward_aggregates`, `resolved_forward_aggregate_evidence`,
  `ensure_historical_forward_aggregates_dispatched`'s keying/single-flight semantics, and J-08's serving split
  remain byte-frozen and untouched.
- [ ] `apps/backend/app/engine/data_manager.py` — in `coverage_from_storage`, add one new fallback branch tried
  AFTER the existing exact-match `CoverageSnapshot` lookup and the existing explicit-`as_of` self-heal (both
  unchanged, still preferred when they apply): if a `CoverageSnapshot` row exists for the resolved `asof_key`
  under ANY older `dataset_version` (one bounded, indexed lookup by `asof_key` alone — never a scan of
  `daily_prices`), serve that row's payload with three new sibling fields — `coverage_status: "current"`,
  `coverage_status: "stale"` with `stale_dataset_version`/`stale_computed_at` naming the row it reflects, or
  `coverage_status: "not_yet_computed"` (the true no-row-for-any-version case, unchanged behavior) — instead of
  falling through to `_coverage_not_yet_computed_payload`'s all-zero sentinel whenever a real, previously-
  computed row exists. No new compute, no second derivation, same computing module
  (`app.engine.data_manager`), same endpoint (`GET /api/data`).
- [ ] `apps/backend/app/api/data.py` (wherever `GET /api/data` assembles its coverage block) — pass the new
  `coverage_status`/`stale_dataset_version`/`stale_computed_at` fields through on the existing response; no new
  endpoint, no new route.
- [ ] `reports/perf-budgets.md` — correct the Iteration 26 section's boot timestamp, mislabeled `19:14:25Z`
  when the underlying boot log entry is local time written as UTC: re-derive the true UTC timestamp from the
  boot log's own timezone-stamped line and fix the label (append/correct-only edit; no other content in that
  section changes).

### Frontend
- [ ] `apps/frontend/app/data/page.tsx` (Data Manager coverage panel) — when the served payload's
  `coverage_status === "stale"`, render the disclosed prior-snapshot figures (not zero) together with a calm,
  honest label — "Coverage as of a prior scan (version {stale_dataset_version}) — refreshes on the next data
  job" — distinct from the existing `not_yet_computed` empty-state copy, which stays byte-unchanged for the
  true fresh-install case.

### New user-facing capability
None — this is a hardening/consolidation iteration closing two anti-goal findings on already-shipped, already-
passing journeys (J-05, J-07, J-08). No new page, endpoint, or workflow.

### New information displayed
The Data Manager coverage panel now discloses a `coverage_status` label ("current" / "stale, as of version X"
/ "not yet computed") instead of silently rendering the same-looking empty state for two different underlying
conditions.

### New user actions
None.

### UI surface changes
`/data`'s existing coverage panel gains one new labeled state (`stale`); no new page/panel/route.

### Product surface delta
Two existing, already-passing journeys (J-07/J-08 via `/backtest`'s concurrent-request resilience; J-05 via
`/data`'s coverage honesty) become more robust and more honest under conditions this session's own QA already
proved occur live. No new surface.

### Blueprint conformance
No new Information Architecture. J-05's coverage payload keeps its registered home (`/data`, Data Manager nav
section); J-07/J-08 keep their registered homes (global readiness badge + `/backtest`, Backtest nav section).
`runs/goal-session-ops-hardening/state/blueprint.md` was updated this iteration (additive only): a new
"iter-27 update" narrative paragraph, and additive Notes-column appends to the existing "Regime score, market
phase, realized forward-returns" row and the existing "Coverage payload" row — no row's Computed-by/Served-by
columns changed, no second producer or endpoint introduced.

### Data-contract additions
- `coverage_status: "current" | "stale" | "not_yet_computed"` (string enum) — additive field on the EXISTING
  Coverage payload row. Computed by `app.engine.data_manager.coverage_from_storage` (unchanged module), served
  by `GET /api/data` (unchanged endpoint).
- `stale_dataset_version: string | null` — the older `dataset_version` the served figures actually reflect;
  non-null only when `coverage_status == "stale"`. Same module, same endpoint.
- `stale_computed_at: string | null` (ISO-8601 UTC) — the stale row's own `computed_at`; non-null only when
  `coverage_status == "stale"`. Same module, same endpoint.

No other Data Contract row changes. `compute_forward_aggregates`, `resolved_forward_aggregate_evidence`, and
`ensure_historical_forward_aggregates_dispatched` keep their existing single computing module and single
serving endpoint, unmodified.

## OUT OF SCOPE

- Audit finding B2 (`ensure_historical_forward_aggregates_dispatched`'s `Thread.start()` failure leaving the
  badge stuck on "running (1)" for the process lifetime) — a different function, unrelated to either ESCALATE
  finding, non-blocking, carried unchanged; needs its own deliberate freeze-lift in a future iteration.
- Backlog card B-1107 (global dispatch cap/semaphore) — owner-optional, untouched.
- The owner decision on whether the cold historical `/backtest` load (16–23s measured iter-26) needs its own
  written budget or should move off the request path — remains open, not engineering scope.
- Retargeting `test_forward_testing_serving_split.py`'s four `is_latest` monkeypatches or removing the
  dangling imports at `backtest.py:75` / `mcp/tools.py:38` — carried non-blocking item, unrelated to this
  iteration's two fixes.
- Any change to `compute_forward_aggregates`, `resolved_forward_aggregate_evidence`,
  `ensure_historical_forward_aggregates_dispatched`'s keying/single-flight semantics, or J-08's serving split —
  all byte-frozen per binding "Do not redo," except the one narrowly-scoped function named in IN SCOPE.
- Re-triggering a genuine live memory-pressure background-compute failure to re-prove J-09's failure branch —
  already proven by test (iter-26 "Do not redo"); never repeat.
- Editing the "OWNER BUDGET AMENDMENT" section, its "Revision 1", or TC-13/TC-14 in `reports/perf-budgets.md`
  — settled owner policy; this iteration only corrects one mislabeled timestamp in the Iteration 26 section and
  otherwise leaves that file's prior content untouched.
- Any change to `resolved_run`'s own concurrent-create-once behavior for a brand-new `ScannerRun` row — not
  implicated by either named finding; flagged as a possible related area but not investigated or touched this
  iteration.
- Editing `reports/goal-session-ops-hardening-demo.json` — settled, verified content; not touched.
- Running the full pytest suite or more than one concurrent pytest invocation.

## DEFINITION OF DONE

- [ ] J-05, J-07, J-08 pass via browser-qa-agent, re-verified with both fixes in place (TC-1, TC-2, TC-5, TC-6)
- [ ] Required-still-passing journeys J-01, J-03, J-04, J-06, J-09 remain green via deterministic golden replay
  / LLM fallback (TC-9)
- [ ] AG-8 finding closed: a deliberate, controlled reproduction of two concurrent `/backtest` requests for the
  same never-scanned historical date returns HTTP 200 from both, with zero unhandled ASGI exceptions in
  `logs/backend.log` for that window, and a full-page (not viewport) browser capture shows normal page content
  (TC-1, TC-2, TC-3, TC-4)
- [ ] AG-3 finding closed: `GET /api/data`'s default view serves `coverage_status: "stale"` with honest prior-
  snapshot figures (never the all-zero sentinel) whenever a real prior `CoverageSnapshot` row exists under an
  older `dataset_version`; the true never-computed case is unchanged (TC-5, TC-6, TC-7, TC-8)
- [ ] No anti-goal violation introduced; both iter-26 findings have a code fix, a passing regression test, and
  live evidence submitted for the evaluator's own resolution scoring
- [ ] Unit/integration tests pass via ONE combined pytest invocation (TC-11); no regressions in any touched file
- [ ] `reports/perf-budgets.md`'s mislabeled Iteration 26 timestamp is corrected (TC-10)
- [ ] `runs/goal-session-ops-hardening/state/blueprint.md`'s Data Contract additions match what was actually
  built (already additively edited this iteration by the decomposer; verify no drift) (TC-12)
- [ ] Dev handoff written at `docs/handoffs/goal-ops-hardening-iter-27-dev.md`

## TESTING REQUIREMENTS

- Browser: J-05 (Data Manager coverage panel, both `current` and the newly-reproduced `stale` state), J-07 and
  J-08 (the deliberate concurrent-race reproduction on `/backtest`, full-page capture). Smoke replay: J-01,
  J-03, J-04, J-06, J-09 — for J-09's regression check specifically, pick a date that ALREADY has a
  `scanner_runs` snapshot but incomplete aggregates, never a never-scanned date (iteration-state.md "Do not
  redo," directly governs this pass).
- Unit/integration (bundle into ONE combined pytest invocation — this project's shared 30-year `loaded_engine`
  fixture costs 1h+ per build; a single combined invocation covering every new/changed selector below builds
  it once, not per-file):
  - A new deterministic test proving `_insert_run_forward_returns` tolerates a mid-loop autoflush collision
    (stage a competing `ForwardReturn` row via a separate committed session/connection to simulate "a
    concurrent writer already inserted this key" before the loop's own `existing` set would have seen it, then
    call `backfill_run_forward_returns`/`_insert_run_forward_returns` and assert no exception propagates and
    exactly one row survives for that key) — file/name at developer's discretion, extending
    `apps/backend/tests/test_forward_testing_concurrency.py`.
  - A new test proving an unrelated `IntegrityError` (any constraint other than the targeted
    `(run_id, symbol, horizon)` uniqueness) still propagates unchanged — the new handling must not become a
    blanket catch-all.
  - New tests in `apps/backend/tests/test_api_data.py` (or `test_data_manager.py`, developer's choice — keep
    all three in ONE file): (a) stale-fallback serves the older row's figures + `coverage_status: "stale"` +
    `stale_dataset_version` when the exact-match key misses but an older row exists for the same `asof_key`;
    (b) `coverage_status: "not_yet_computed"` and the payload shape are unchanged when no row exists for this
    `asof_key` under any version (regression guard); (c) `coverage_status: "current"` after a normal ingest
    finalize refreshes the row for the new `dataset_version` (regression guard for the common path).
- Error cases: an `IntegrityError` NOT matching the targeted duplicate-key collision must still propagate (see
  above) — the fix is scoped narrowly, never a blanket try/except around the whole insert loop.

Test-first contract:

- TC-1: given two concurrent `GET /api/backtest` requests target the same never-scanned historical `as_of`
  date (a single deliberate, controlled reproduction — not a routine regression action), when both race
  `backfill_run_forward_returns`'s forward-returns insert for the same `(run_id, symbol, horizon)` keys, then
  both requests return HTTP 200 and `logs/backend.log` contains zero "Exception in ASGI application" lines for
  that request window.
- TC-2: given that same concurrent-race scenario is reproduced once under browser-qa with a full-page (not
  viewport) capture, when the responses return, then the captured `/backtest` page shows its normal evidence
  content (Scorecard / AsOfScanSummary rendered) — never a blank or frozen application-error frame.
- TC-3: given a concurrent caller's forward-returns insert for symbol A is still pending in the session when
  the loop's own next iteration issues symbol B's `close_on`/`bars_after` read, when that read's autoflush
  encounters the duplicate-key collision from symbol A's staged row, then the collision is caught, the session
  is rolled back to discard only the duplicate insert, and the loop continues processing the remaining
  symbols/horizons without an unhandled exception reaching the caller.
- TC-4: given an `IntegrityError` raised for a constraint OTHER than the `(run_id, symbol, horizon)` uniqueness
  this fix targets, when `_insert_run_forward_returns` runs, then the exception still propagates unchanged.
- TC-5: given a populated database whose `CoverageSnapshot` row is stored for an OLDER `dataset_version` than
  the current one (because a request-path-created `ScannerRun` advanced `_membership_dataset_version` outside
  ingest), when `GET /api/data` is requested with the default `as_of=None` view, then the response's coverage
  payload carries `coverage_status: "stale"`, non-zero `price_start`/`price_end`/`universe_count` taken from
  that older row, and a `stale_dataset_version` field naming the version those figures reflect.
- TC-6: given that same stale-state response, when the Data Manager `/data` page renders its coverage panel,
  then it displays the disclosed prior-snapshot figures together with the visible label "Coverage as of a
  prior scan (version {stale_dataset_version}) — refreshes on the next data job", replacing today's
  "— → —" / "UNIVERSE 0" rendering for this case.
- TC-7: given a genuinely fresh-install database that has never had a `CoverageSnapshot` row for ANY
  `dataset_version`, when `GET /api/data` is requested, then `coverage_status` reads `"not_yet_computed"` and
  the served payload's shape is unchanged from today's all-zero sentinel (regression guard).
- TC-8: given a normal ingest job (fetch/backfill/rebuild) completes and its existing finalize hook refreshes
  `CoverageSnapshot` for the new `dataset_version`, when `GET /api/data` is requested afterward, then
  `coverage_status` reads `"current"` and the `/data` panel shows no stale label (regression guard for the
  common path).
- TC-9: given J-01, J-03, J-04, J-06, J-09's existing golden scripts, when replayed against this iteration's
  build, then all five report PASS with zero FAIL rows.
- TC-10: given `reports/perf-budgets.md`'s Iteration 26 section labels a boot timestamp `19:14:25Z` while the
  underlying boot log entry records local time written as UTC, when the developer re-derives the true UTC
  timestamp from the boot log's own timezone-stamped line, then the corrected label in that section matches
  the log's actual UTC timestamp verbatim, with no other content in that section changed.
- TC-11: given the new tests for TC-3, TC-4, TC-5, TC-7, TC-8, when they are run, then a SINGLE combined pytest
  invocation (not multiple separate runs) reports a literal pass/fail summary line showing all of them PASSED,
  building any shared heavy fixture at most once.
- TC-12: given the developer's actual `GET /api/data` implementation of the coverage stale-fallback, when its served JSON field names are compared against `blueprint.md`'s Coverage payload row (`coverage_status`, `stale_dataset_version`, `stale_computed_at`), then the field names match verbatim — no renamed field, no field dropped, no field added beyond what is registered.

## NOTES

- **Coordinator constraint (this dispatch):** the shared 30-year `loaded_engine` pytest fixture costs 1h+ per
  build on this box and concurrent pytest invocations fork-lock the host; scope all new backend test selectors
  above into ONE combined pytest invocation (TC-11), mirroring iter-26's successful pattern (3 tests, one
  fixture build, 1:25:51).
- **Assumption logged (iter-27, assumption ledger):** chose the stale-label fallback for the coverage fix over
  triggering a request-path recompute — the latter would reintroduce exactly the whole-table-scan risk the
  Coverage payload's iter-2/iter-3 redesign eliminated. Reversible if a human requires the figures to always
  reflect the current dataset version rather than a labeled-stale prior one.
- **Root-cause note:** both fixes above are based on a direct read of the implicated code (cited by file/line
  in BACKGROUND), not assumed from the evaluator's narrative alone — per the session's own recurring lesson
  about re-deriving load-bearing facts. The developer should still independently confirm both diagnoses (e.g.
  via TC-3's staged-collision test and a direct query of `coverage_snapshot`/`scanner_runs` after TC-1's live
  reproduction) before considering either finding closed.
- **Non-blocking, carried, not this iteration's scope:** browser-QA narrative accuracy (a prior iteration's
  report said `/backtest` requests "returned immediately" when the log showed 16.7–23.2s — correct any such
  wording this iteration's own QA writes, by reading `logs/backend.log`'s `backtest_timing total_ms` rather
  than assuming); `J-01-verify.png` / `J-03-verify.png` being byte-identical is a known framework capture nit
  (6th recurrence), not a product defect.
