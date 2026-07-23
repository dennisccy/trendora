# Goal Iteration 13 — J-06 closeout attempt: ingest-time cache for `GET /api/indexes?full=true` (aggregation candidate #7)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** ops-hardening
- **Iteration:** 13
- **Mode:** next
- **Depth:** full
- **Frontend Present:** yes
- **Target journeys:** J-06
- **Required-still-passing journeys:** J-01, J-03, J-04, J-05
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

Bring `GET /api/indexes?full=true` — read by both `/` (Dashboard) and `/data` (Data Manager) on mount —
within its committed ≤1.5s budget by warming its unparameterized default hot key at ingest time
(aggregation candidate #7), so J-06, the session's last non-passing Must-have, can be scored on a
genuinely in-budget measurement instead of the confirmed 2138.7–2257.7ms over-budget reading.

## BACKGROUND

Priority rubric: no journey is `regressed` (rule 1 — none apply; J-01/J-03/J-04/J-05 are all `passing`);
the last coherence verdict (`iter-12/coherence.md`) was COHERENCE-PASS, so no consolidation mandate (rule
2); J-06 is the only non-passing Must-have and the iter-12 evaluator named this exact fix as the single
agent-owned item standing between J-06 and `passing` ("bring `/api/indexes?full=true` into budget via
aggregation candidate #7... the single item between J-06 and `passing`, alongside the walkthrough") — rule
3 (unblocker: closing this clears the last agent-tractable J-06 gap). Rule 4 (smallest spec wins ties) is
why this iteration touches ONLY the one over-budget endpoint's hot key, not every range preset or every
as-of value. Rule 5 (never bundle two risky changes) is why the critical AG-8
`forward_aggregates_cached` → `compute_forward_aggregates` MemoryError rewrite — a SEPARATE risky,
owner-scoped change carried unresolved since iter-8 — is explicitly excluded from this iteration, per the
operator's own boundary note this dispatch. Rule 6 (don't pick a human-blocked journey) is satisfied: this
specific gap is concrete, agent-owned perf work with an implementation path goal.md itself names (candidate
#7), unlike the AG-8/`HOST_GUARD_REQUIRE_MARKERS`/walkthrough items, which stay explicit OWNER decisions,
out of scope here exactly as they have been since iter-8.

**Depth is FULL — trigger 2 (Data model).** This iteration adds a new persisted, `create_all`-managed cache
table (mirroring the existing `ForwardAggregateCache`/`EventStudyCache`/`MarketPhaseCache` convention) and
a new ingest-warm step inside `_refresh_ingest_aggregates` — a genuine schema addition and a change to how
an already-registered blueprint Data-Contract field (`aggregates_refreshed`) is populated. Trigger 3 (prior
ESCALATE) does NOT apply — the last dispatched verdict was CONTINUE — but trigger 2 fires independently and
mandates full regardless.

Lessons applied directly: **iter-5** — TTI/endpoint latency must be measured with a REAL browser, not
`curl` (Chrome's connection-queuing profile under-reports on call-heavy pages); the post-fix control
readings must be real-Chrome, fresh-navigation, cache-disabled loads, exactly like iter-12's G2. **iter-6**
— measure on a verifiably idle host, and check for measurement contamination before filing or retracting a
number. **iter-8** — capacity/latency claims must be measured under LIKE-FOR-LIKE host conditions (the same
host-guard caps, no confounding launcher change) or the "fixed" claim is unattributable; also, the
per-item `MemoryError`-isolation + `_release_process_memory()` convention that function already uses for
every other warm loop applies identically to the new one this iteration adds. **iter-9** — `VmPeak` is a
monotone high-water mark; don't invent a measurement-artifact story for a number trending the wrong way
without checking it. **iter-11** (load-bearing) — never accept "ambient host contention" without
cross-reading `logs/backend.log` (job-start activity) and `logs/hwmon/hwmon.csv` (load1/MemAvailable) at
the EXACT timestamp of each reading; iter-11's own dismissed "ambient" story for this very endpoint was
later shown by iter-12's controlled re-measurement to be a genuine, reproducible over-budget condition, not
noise. **iter-12** (load-bearing) — closing an evidence gap is not the same as the journey passing: score
this iteration's own fix on whether the post-fix control readings actually land ≤1.5s, not on whether the
cache/warm-step code was written. If even one of the three control readings still exceeds budget, J-06
stays `partial` and that must be stated plainly, not rounded into a "may pass."

## IN SCOPE

### Backend
- [ ] Add a new STANDALONE, `create_all`-managed cache table (e.g. `IndexSeriesCache`) in
      `apps/backend/app/models.py`, mirroring the existing `ForwardAggregateCache`/`EventStudyCache`/
      `MarketPhaseCache` docstring convention exactly (own table — the `_ADDITIVE_COLUMNS` trap does not
      apply; a cache of the deterministic read-only `compute_index_series` derivation, never a second
      computation): stores the serialized payload for the SINGLE unparameterized default hot key
      (`range_key=cfg.index_chart.default_range`, `full=True`) actually requested on mount by
      `PhaseCrossViewCard` (`/`) and `IndexVendorPanel` (`/data`), keyed by that key plus a dataset-version
      stamp tied to the freshness of the configured `index_chart.symbols`' stored bars (a bounded, indexed
      read of those few symbols — never a whole-`daily_prices`-table scan).
- [ ] Add a `*_cached` wrapper function (e.g. `app.engine.indexes.index_series_cached`) that serves the
      stored row on a hit and self-heals — computes via the UNCHANGED `compute_index_series` and persists —
      on a miss or a stale dataset-version stamp, mirroring the self-healing convention every sibling cache
      in this codebase already follows. Route `GET /api/indexes` (`apps/backend/app/api/indexes.py`)
      through this wrapper ONLY when the request matches the hot key exactly; every other `range`/`as_of`/
      `full` combination (a user-selected non-default range preset, an explicit historical `as_of`) keeps
      calling `compute_index_series` directly, unchanged and lazy — the existing "cannot be precomputed
      (user-parameterized)" carve-out goal.md's own Improvement-direction section already applies to
      arbitrary as-of reads.
- [ ] Warm the hot key inside the EXISTING `_refresh_ingest_aggregates` finalize hook
      (`apps/backend/app/engine/data_manager.py`), following the SAME per-item `MemoryError`-isolation +
      `_release_process_memory()` convention (iter-8) already applied to every other warm loop in that
      function. Add `"index_series"` as a new legal member of the `aggregates_refreshed` enumerated list,
      appended ONLY when the warm step actually persisted a row this run — never fabricated.
- [ ] No change to `compute_index_series`'s signature, return shape, or byte-level output for ANY input; no
      change to its other call sites (the MCP `get_indexes` tool in `app/mcp/tools.py`/`server.py`).

### Frontend
- [ ] No product source changes anticipated — same endpoint, same request shape, same response shape, only
      a faster hot-key path. `Frontend Present: yes` is set solely to force the real-browser latency
      re-measurement (iter-5's own lesson: curl under-reports call-heavy pages) via browser-qa-agent.

### New user-facing capability
None new. The Dashboard's major-indexes/regime chart and the Data Manager's index-vendor panel render the
same data, same shape, same values — only faster on first load.

### New information displayed
None new to the product UI.

### New user actions
None.

### UI surface changes
None. `/` and `/data` are unchanged pages; only an existing on-load call's latency improves.

### Product surface delta
`GET /api/indexes?full=true` on its default hot key now reads a warmed cache row instead of hydrating each
configured index symbol's full multi-decade price history via ORM on every request; no visible change
except latency.

### Blueprint conformance
No new surfaces. This iteration's work lives under `/` (Dashboard, existing home) and `/data` (Data
Manager, existing home) per `blueprint.md`'s Information Architecture table; J-06's own canonical
measurement artifact remains `reports/perf-budgets.md`.

### Data-contract additions
No NEW displayed value or field — the `GET /api/indexes` response shape (`asof_date`/`range`/`ranges`/
`series`) is byte-identical before and after. Two blueprint bookkeeping additions, both registered in
`blueprint.md` this iteration: (1) a previously-unlisted existing row, "Index series (normalized-%
major-indexes chart, J-44)" — computing module `app.engine.indexes.compute_index_series` (unchanged),
served by `GET /api/indexes` (unchanged), now also naming the new `IndexSeriesCache` as its ingest-warmed
serving-path cache for the hot key; (2) the ALREADY-registered `aggregates_refreshed: list[str]` field
(Backfill run-summary contract row) gains one new legal enum member, `"index_series"` — same field, same
type, same nullability/omission rule (gated on "actually warmed," never fabricated) every existing member
already follows.

## OUT OF SCOPE

- The critical AG-8 `forward_aggregates_cached` → `compute_forward_aggregates` unbounded-load MemoryError
  (`apps/backend/app/engine/forward_testing.py:826`) — a SEPARATE, owner-scoped decision (bounded/streamed
  rewrite, goal.md amendment, or formal defer), unresolved since iter-8; not touched, not fixed inline, and
  deliberately not bundled with this iteration's own risky schema change (rule 5).
- Flipping `HOST_GUARD_REQUIRE_MARKERS` — owner decision.
- The J-05/J-06 `demo.sh ops-hardening --session-live` walkthrough — proven non-autonomous by the iter-12
  decomposer (`assumptions.md`, iter-12); owner decision (human run-once, wording amendment, or a framework
  enhancement).
- Caching any range preset other than the configured default, or any explicit historical `as_of` — those
  stay on the existing lazy, uncached path.
- The full pytest suite or any concurrent pytest run — targeted subset only, host-guard-confined
  (`taskset -c 0-3,8-11`, BLAS/OMP/numexpr threads=4).
- Any opt-in heavy-ingest workload or full-universe backfill (AG-10) — this host has hard-reset twice under
  that class of load; this iteration's own tests must stay bounded.
- Re-measuring the other 10 already-in-budget pages' TTI or the boot-to-health budget — unchanged and fresh
  since iter-11 (1.364s boot; all 10 other pages comfortably in budget) — spot-check only for a regression,
  do not re-run the full sweep methodology on them.
- Any change to `app/api/health.py`, `app/engine/readiness.py`, `main.py`'s boot sequence, `warmup.py`,
  `max_range_days`/`snapshot_cadence`, the `/evidence` drawdown warm, or `server.memory_cap_mb` — all
  BINDING "Do not redo" items from iteration-state.
- Framework harness bugs (`merge_ui_test_results.py`'s dropped `**FAIL**` cells, the `Frontend Present: no`
  browser-qa-skip misrouting) — out of a product-facing decomposer's remit; never patch
  `scripts/automation/*` from inside a product iteration.
- Hand-editing any past iteration's point-in-time artifacts.

## DEFINITION OF DONE

- [ ] `GET /api/indexes?full=true` on its default hot key lands ≤1.5s across three independent,
      cache-disabled, fresh-navigation real-browser loads of `/data` on a verifiably idle host
      (cross-checked against `logs/backend.log` + `logs/hwmon/hwmon.csv`, mirroring iter-12's G2 control
      methodology exactly) — AND a spot-check fresh-navigation load of `/` (Dashboard) confirms the SAME
      hot key also lands within budget there.
- [ ] `compute_index_series`'s output for the hot key is byte-identical (AG-3) between the cached serve and
      a fresh, direct, uncached call on the same DB state.
- [ ] A subsequent ingest job landing a new bar for a configured `index_chart` symbol invalidates the stale
      cache row; the next hot-key request reflects the new bar (never a stale pre-ingest snapshot).
- [ ] `aggregates_refreshed` reports `"index_series"` only on a run where the warm step actually persisted a
      row this run; omitted whenever it raised, was skipped, or the loop aborted early.
- [ ] Non-hot-key requests (an explicit `range` preset, an explicit historical `as_of`) are unaffected —
      byte-identical to their pre-iteration output, never routed through the new cache.
- [ ] A `MemoryError` raised while warming the index-series cache is isolated to that one warm step (stops
      immediately, `_release_process_memory()` runs) and never flips an otherwise-successful ingest job to
      `failed`.
- [ ] Required-still-passing journeys J-01, J-03, J-04, J-05 remain green (deterministic replay + LLM
      fallback, mechanically verified).
- [ ] No anti-goal violation introduced — the critical AG-8 entry is neither newly introduced nor worsened
      (its code path is untouched); AG-10 host-guard confinement honored for any pytest run this iteration.
- [ ] Targeted backend tests pass, including new coverage for the cache hit/miss/self-heal path, the
      dataset-version invalidation-on-new-bar behavior, and the finalize hook's `MemoryError` isolation for
      this new warm step — with no NEW failures beyond the pre-existing documented
      `tests/test_db.py::test_create_all_produces_expected_tables` failure.
- [ ] Dev handoff written at `docs/handoffs/goal-ops-hardening-iter-13-dev.md`.

## TESTING REQUIREMENTS

- Browser: J-06 (target — real-Chrome three-load control of `GET /api/indexes?full=true` on `/data` plus a
  spot-check on `/`, via browser-qa-agent, cross-checked against `logs/backend.log`/`logs/hwmon/hwmon.csv`),
  J-01/J-03/J-04/J-05 (required-still-passing, deterministic golden replay with LLM fallback).
- Unit/integration: `apps/backend/tests/test_indexes.py` (existing `compute_index_series` coverage stays
  green, unchanged — plus new tests for `index_series_cached`'s hit/miss/self-heal path and byte-identity
  against the uncached call), `apps/backend/tests/test_api_indexes.py` (routing: hot key served from cache,
  non-hot-key requests bypass it), `apps/backend/tests/test_data_manager.py` (new finalize-hook warm-step
  test plus a `MemoryError`-isolation test mirroring the existing
  `test_finalize_hook_forward_aggregates_memory_error_on_first_horizon_aborts_loop` pattern, and an
  `aggregates_refreshed` test confirming `"index_series"` is honestly gated).
- Error cases: a warm-step exception (non-`MemoryError`) is caught and logged without flipping the ingest
  job's final status, mirroring every other warm loop's existing non-fatal contract; a missing/never-warmed
  cache row serves an honest self-heal compute rather than a fabricated or stale value.

Test-first contract:

- TC-1: given the ingest-warmed `IndexSeriesCache` row for the hot key exists and no concurrent ingest job
  is running (confirmed via `logs/backend.log`), when a real Chrome browser performs three independent
  fresh navigations to `/data` (no reused tab, cache-disabled), then each navigation's
  `GET /api/indexes?full=true` Resource-Timing duration is ≤1500ms, with `logs/hwmon/hwmon.csv` load1 <2.0
  at each reading's exact timestamp.
- TC-2: given the same hot-key state, when a real Chrome browser performs one fresh navigation to `/`
  (Dashboard), then that page's own `GET /api/indexes?full=true` call also reads ≤1500ms.
- TC-3: given the hot key is requested twice in a row with no intervening ingest, when the second
  response's `series`/`asof_date`/`range`/`ranges` fields are compared to the first, then they are
  byte-identical (JSON-equal) to each other and to a direct, uncached call of `compute_index_series(session,
  as_of=None, range_key=cfg.index_chart.default_range, full=True)` on the same DB state.
- TC-4: given a backfill/fetch/rebuild job lands a new bar for a configured `index_chart` symbol (e.g.
  SPY), when that job's `_refresh_ingest_aggregates` finalize hook completes, then the next
  `GET /api/indexes?full=true` hot-key request's `series` includes a point for the new bar's date (not the
  pre-ingest snapshot).
- TC-5: given that same finalize-hook run, when the resulting `data_provider_runs` row's
  `aggregates_refreshed` field is read from the database, then it contains `"index_series"` if and only if
  the warm step actually persisted a row during that run.
- TC-6: given a request with an explicit `range=3M` OR an explicit historical `?as_of=` parameter, when
  `GET /api/indexes` is called with that combination, then the response is served via the unchanged,
  uncached `compute_index_series` call path (no `IndexSeriesCache` lookup) and is byte-identical to its
  pre-iteration output for the same inputs.
- TC-7: given the index-series warm step inside `_refresh_ingest_aggregates` raises `MemoryError`, when the
  finalize hook runs, then that step stops immediately, `_release_process_memory()` is invoked, the ingest
  job's own final status (`ok`/`partial`) is unaffected, and `"index_series"` is absent from that run's
  `aggregates_refreshed`.
- TC-8: given the required-still-passing journeys J-01, J-03, J-04, J-05, when each is re-verified this
  iteration (deterministic golden replay with LLM fallback), then all four are recorded `passing` with cited
  evidence and none transitions to `failing`.
- TC-9: given the 10 already-in-budget J-06 pages/endpoints from the iter-11 sweep (unchanged this
  iteration), when spot-checked for a regression, then each remains within its committed budget in
  `reports/perf-budgets.md`.
- TC-10: given the targeted backend test subset named above, when run under host-guard confinement
  (`taskset -c 0-3,8-11`, BLAS/OMP/numexpr threads=4), then it completes with zero failures beyond the
  pre-existing documented `tests/test_db.py::test_create_all_produces_expected_tables` failure.
- TC-11: given this iteration reaches completion, when
  `docs/handoffs/goal-ops-hardening-iter-13-dev.md` is inspected, then it exists, lists every changed file,
  and states explicitly whether the three control readings (TC-1) and the Dashboard spot-check (TC-2) held
  budget or not — never rounding an over-budget reading into a "may pass."
- TC-12: given the completed diff, when `apps/backend/app/engine/forward_testing.py` is inspected line by line against its pre-iteration state, then it is byte-unchanged (confirms the critical AG-8 `forward_aggregates_cached` → `compute_forward_aggregates` MemoryError entry was neither touched nor worsened by this iteration).

## NOTES

- **Score on the number, not on the fact that the code was written (iter-12's own lesson).** If even one of
  the three `/data` control readings or the `/` spot-check still exceeds 1.5s after this fix, state that
  plainly in the dev handoff and let the evaluator hold J-06 at `partial` — do not round a marginal miss
  into "close enough."
- **Technical note for the implementer (not a scope mandate):** for the specific hot key this iteration
  targets (`range_key="all"` i.e. `days=None`, `full=True`), `compute_index_series`'s own series computation
  does not depend on the resolved `as_of` at all — `bars_through_latest` ignores it, and `start` is `None`
  for the all-history preset, so the ONLY as-of-dependent part of that response is the echoed `asof_date`
  field. A cache design that re-derives/echoes the current resolved `as_of` at read time (rather than baking
  a stale one into the stored payload) avoids an unnecessary correctness trap here; left to the developer's
  own design, not mandated.
- **OWNER DECISIONS outstanding, not to be invented by any agent (unchanged since iter-8):** (1) scope,
  amend, or formally defer the critical AG-8 `forward_aggregates_cached` → `compute_forward_aggregates`
  unbounded-load MemoryError — hard-blocks GOAL_ACHIEVED regardless of this iteration's J-06 outcome; (2)
  `HOST_GUARD_REQUIRE_MARKERS`; (3) the J-05/J-06 `demo.sh ops-hardening --session-live` walkthrough — no
  autonomous mechanism produces it (iter-12 finding); needs a human run-once, a goal.md wording amendment,
  or a framework session-record enhancement.
- **If J-06 reaches `passing` this iteration**, all five Must-have journeys are passing session-wide, but
  the three owner decisions above still hard-block GOAL_ACHIEVED — the next decomposer pass should write
  the "all journeys passing, owner decisions outstanding" holding spec rather than manufacture new journey
  scope.
- **Operator note (as relayed):** backend is up on :8255, frontend on :3255, host-guard caps live. This
  iteration DOES change backend source (new table + new module code), so the running backend process needs
  a restart to pick it up before browser-qa can exercise it — the standard dev/browser-qa pipeline handles
  this restart itself (as it has for every other backend-changing iteration this session, e.g. iter-2
  through iter-9), so no operator action is anticipated. If the harness's own restart mechanism is blocked
  in this environment, the operator restarts per the documented sequence (kill/restart with recorded
  pid/timestamp) and hands the resulting state to browser-qa-agent — the same fallback iter-10/iter-11
  already established.
- Framework maintainer items, carried unchanged (never patch `scripts/automation/*` from a product
  iteration): `merge_ui_test_results.py` drops emphasised `**FAIL**` cells from the merged rollup — always
  score from the raw `.llm.md`. The `Frontend Present: no` → browser-qa-skip misrouting is routed around
  here via the explicit `Frontend Present: yes` field, not fixed at the source. The pre-existing
  `tests/test_db.py::test_create_all_produces_expected_tables` failure remains untouched.
