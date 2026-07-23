# Goal Iteration 16 — Backtest evidence serves from storage only: precompute-before-serve (J-08)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** ops-hardening
- **Iteration:** 16
- **Mode:** next
- **Depth:** full
- **Frontend Present:** yes
- **Target journeys:** J-06, J-07, J-08
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

`/backtest` and the MCP `query_backtest` tool never trigger a forward-aggregate compute on a request —
every request for the current default (latest) view is served from the last COMPLETE stored version,
honestly labeled `ready`, `refreshing`, or `not_yet_computed`, closing the cold-MISS residual that has
kept J-06/J-07 `partial` since iter-11 and building the new J-08 Must-have journey the owner added to
close it.

## BACKGROUND

iter-15 STALLED: the single-flight de-dup fix was correct, but the operator-supervised deep-basis pass
proved the residual `/backtest` cold-MISS is **178.74s (~119x over the ≤1.5s budget)** — one inherent
cold full-basis `compute_forward_aggregates` pass a wrapper-scoped fix cannot reduce. All three unblock
paths were owner-owned. The owner has now decided: **`docs/goal.md` gained a new Must-have journey,
J-08** ("Backtest evidence serves from storage only — never a cold recompute on request"), option 2 of
iter-15's three (precompute-before-serve / incremental-aggregate redesign). J-08's 5 steps and 4-part
Acceptance are read verbatim from goal.md (§ "J-08"). J-07 step 1 gained one parenthetical
("served from storage per J-08") — no other goal.md change. Current journey states confirmed against the
inlined digest: J-01/J-03/J-04/J-05 `passing`; J-06/J-07 `partial`, **both held solely on this cold-MISS
residual** — J-08 is what closes them (pump note; iter-15 eval; iteration-state.md). AG-8 stays
RESOLVED (iter-14) and is not reopened. Coherence was PASS at iter-15 (no consolidation mandate).

**The architectural problem, confirmed by direct evidence, not merely inferred from the journey text:**
`forward_aggregates_cached` (`forward_testing.py:1016`) is a single read-through-cache wrapper called by
THREE sites — `GET /api/backtest`, the MCP `query_backtest` tool, and the ingest finalize warm
(`_refresh_ingest_aggregates` in `data_manager.py:3215-3242`) — and on a cache MISS it computes
synchronously (iter-15 only added single-flight de-dup around that MISS; it did not remove the compute).
Its own pruning ("prune stale rows for THIS `(horizon, asof_key)` identity", `forward_testing.py:1098`)
deletes any OTHER-`dataset_version` row for that identity **the moment ONE horizon's new-version row is
written** — per-horizon, not per-version-cutover. A direct read-only inspection of the live DB's
`forward_aggregate_cache` table (2026-07-23, `apps/backend/data/trendora.db`, no service start required)
proves this is not hypothetical: the non-latest `asof_key='2026-07-17'` is **already split across two
different `dataset_version` stamps** across its 5 horizon rows — `r1272-f2674831` for horizon 1 vs.
`r1193-f2522006` for horizons 5/10/20/60. A naive "latest row per horizon, ignore version" read of that
identity would already serve a mixed-version payload today — exactly what J-08's Acceptance forbids
("all horizons in one response come from ONE complete version — the last-good fallback never mixes
versions"). This is why the fix cannot be "just stop pruning" or "just serve whatever's cached" — it
needs a completeness/cutover contract, not only removing the request-path compute. Current table depths
(read-only, same method): `scanner_results` 775,627, `forward_returns` 3,938,660, `scanner_runs` 1,859 —
essentially unchanged since iter-15 (no new ingest this pause), so the deep-basis cost characterized
there still applies unchanged.

**Depth is full — two independent triggers, both hold:**
1. **Structural/cross-cutting:** the change spans `forward_testing.py` (the split + completeness/cutover
   logic), `backtest.py` (the API router), `mcp/tools.py` (`query_backtest`), `data_manager.py`'s existing
   ingest-finalize warm call site, and the frontend `/backtest` page + `lib/api.ts` — five files across
   backend/MCP/frontend whose interaction (request-path vs. ingest-path racing the SAME cache identity) is
   not covered by any single journey's own tests.
2. **Data model:** this changes the blueprint Data-Contract row's *serving* contract for an
   already-registered value (`compute_forward_aggregates`/`forward_aggregates_cached`) — the
   compute-vs-serve split, the pruning/cutover semantics, and two new response fields.

**Target selection (rubric):** rule 3 (unblocker) — J-08 is the new journey whose construction is the
literal, sole item both J-06 and J-07 need to leave `partial` (pump note: "there are no other outstanding
owner decisions"). Rule 5 (never bundle two risky journeys) is respected: J-06/J-07/J-08 share this ONE
risky architectural change (the precompute-before-serve redesign), not three separate risky changes —
mirroring iter-15's own precedent of listing J-06+J-07 together for the SAME shared blocker. Rule 6
(don't pick a human-blocked journey) does not apply — this is the one item the owner explicitly
authorized and handed to the agent.

**Lessons applied:** iter-15 ("a small-fixture concurrency ratio does not extrapolate to a deep-basis
cost... trust the LIVE number") — unit/integration proof that the completeness/cutover logic is correct
on a small fixture does NOT by itself prove the `refreshing`/`not_yet_computed` paths stay within the
≤1.5s budget at deep-basis scale; TC-16 below requires a live operator-supervised confirmation, not just
green unit tests. iter-14 ("a memory fix and a lock-contention fix are different problems — measure
under the concurrent trigger, not just correctness") — applies equally here: proving the read-only path
never calls `compute_forward_aggregates` (correctness) is not the same claim as proving it answers within
budget (latency); both are required and both are tested separately below (TC-1/2/6/7 vs. TC-3/16).
iter-11 ("cross-read `logs/backend.log`/`hwmon.csv` before accepting an environmental explanation") —
applies to TC-16's live measurement. iter-9 ("a plausible artifact story must be verified, not accepted")
— applies if the completeness-lookup query's own cost is dismissed as "small today" without checking it
stays bounded as the table grows (see IN SCOPE bullet on this).

**Scope note (interpretation call — logged to `assumptions.md`, iter-16):** J-08 step 4's literal text
("perform zero aggregate computation on any request") is scoped in this spec to requests where the
resolved run is the current latest (`is_latest == true`) — matching the ingest warm's own target and
every one of J-08's 5 steps' scenario (none names a historical as-of). A historical `?as_of=` request
keeps its existing, unchanged lazy create-once-and-cache behavior (the same carve-out every sibling
ingest-time cache already documents; goal.md's Non-Goals bars "not a rewrite" of the pre-existing
time-machine capability). See TC-13 and OUT OF SCOPE.

**Operational constraints this iteration (pump note, binding):** agents cannot start/stop services this
dispatch (permission classifier) and the subagent-resume channel is broken — every restart/boot/live-
measurement step below is written as OPERATOR-performed (the operator runs it on request and reports
console output, pids, and timestamps verbatim). No full pytest suite — targeted, host-guard-confined only
(`taskset -c 0-3,8-11`, BLAS/OMP threads 4). Any full-basis live measurement is AG-10-class: exactly ONE
operator-supervised pass on a cooled host with sampler + armed watchdog, sequenced AFTER the code lands
with green targeted tests. Byte-identity (AG-3) still binds. Services are currently DOWN; the operator
boots them on request.

## IN SCOPE

### Backend
- [ ] `apps/backend/app/engine/forward_testing.py`: split `forward_aggregates_cached`'s two roles.
  (a) An **ingest-only compute-and-persist path**, invoked ONLY from the existing per-horizon warm loop
  in `_refresh_ingest_aggregates` (`data_manager.py:3215-3242`, unchanged trigger/looping) — the SOLE
  remaining caller of `compute_forward_aggregates`. Retains iter-15's single-flight lock/in-flight-event
  guard UNCHANGED (still needed for two concurrent ingest jobs racing the same key; "Do not redo" —
  binding). (b) A **new read-only serving path**, the ONLY code `GET /api/backtest` and the MCP
  `query_backtest` tool call from now on — structurally incapable of calling `compute_forward_aggregates`
  under any circumstance, including a lock-wait timeout (no compute-fallback branch at all on this path;
  the existing wait-then-compute-independently fallback stays, unchanged, on the ingest-only path only,
  for the producer-vs-producer race case).
- [ ] The read-only path resolves, for the requested `asof_key`, the latest `dataset_version` for which
  ALL configured horizons (`cfg.walk_forward.horizons`) have a stored row ("complete"). Serves it with
  `evidence_status = "ready"` when that complete version is the current global stamp; `"refreshing"` when
  the current stamp's set is not yet complete but a PRIOR complete version still has all its rows (served,
  labeled with that version's own cache timestamp); `"not_yet_computed"` when no complete version has
  ever existed for this `asof_key` (`evidence_by_horizon = {}`, HTTP 200, honest empty state — never a
  synchronous compute, never a 500/503).
- [ ] Change `ForwardAggregateCache` pruning from per-horizon-write deletion to a **cutover**: a superseded
  version's rows for an `asof_key` are retained until the NEW version's full configured-horizon set is
  confirmed complete, so a reader can never observe a partial/mixed-version row set for that identity.
- [ ] The completeness-lookup query is filtered by the requested `asof_key` (never an unfiltered scan of
  the whole `forward_aggregate_cache` table) — bounded to the handful of rows belonging to that one
  identity, regardless of how many other historical `asof_key`s the table has accumulated over the
  session (AG-8 spirit: no new unbounded-scan path, even a small one today).
- [ ] `apps/backend/app/api/backtest.py`: switch `GET /api/backtest`'s `evidence_by_horizon` population
  to the new read-only serving path; add `evidence_status` and `evidence_generated_at` to the response
  (see Data-contract additions).
- [ ] `apps/backend/app/mcp/tools.py` (`query_backtest`): same switch, same two new fields — mirrors the
  endpoint exactly, per its own existing docstring convention.
- [ ] Call-count instrumentation (mirrors `test_forward_testing_concurrency.py`'s existing monkeypatch
  counter idiom) proving `compute_forward_aggregates` is invoked EXACTLY as many times as the ingest
  warm's own horizon loop calls it, and ZERO times from `GET /api/backtest` / `query_backtest`, across all
  three serving states (ready / refreshing / not_yet_computed).
- [ ] Extend `test_forward_testing_concurrency.py` (or a small sibling file, matching this module's
  existing per-concern-file convention) with the completeness/cutover/never-computed logic tests.
- [ ] ONE operator-supervised, host-guard-confined pass reproducing J-08 steps 1-3 literally: a small
  single-day `/data` backfill (bumps `dataset_version`, schedules the finalize warm) while polling
  `/backtest`, recording the `refreshing`-state response time, then the post-warm `ready`-state response
  time, both against the existing committed ≤1.5s `/backtest` budget in `reports/perf-budgets.md` (same
  file, no second artifact) — sequenced AFTER targeted tests are green, per the pump note's AG-10 protocol.

### Frontend
- [ ] `apps/frontend/lib/api.ts`: add `evidence_status: "ready" | "refreshing" | "not_yet_computed"` and
  `evidence_generated_at: string | null` to `BacktestResponse`.
- [ ] `apps/frontend/app/backtest/page.tsx` (`BacktestResults`): when `evidence_status === "refreshing"`,
  render a calm, factual banner (reuse the existing spinner/banner visual idiom already established for
  status surfaces — e.g. `WarmingState`'s Card + `Loader2` treatment — as a visual reference only; this is
  a DISTINCT concept from `useReadiness()`'s boot-time warm-up and must not reuse that component's
  `useReadiness()` wiring) labeled with `evidence_generated_at`, shown ALONGSIDE the still-fully-populated
  `EvidenceAggregateSection` (the last-good values) — never a skeleton in its place. When
  `evidence_status === "not_yet_computed"`, replace the current silent `{evidence ? (...) : null}` omission
  with an explicit `EmptyState` (reuse the existing `EmptyState` component) reading "Backtest evidence not
  yet computed — run an ingest" (or equivalent honest copy). When `evidence_status === "ready"`, render
  exactly as today — no banner, no empty state (regression guard, TC-12).

### New user-facing capability
None new to what a user can DO. A user now SEES an honest, labeled disclosure of whether the Backtest
evidence panel is showing a slightly-stale-but-labeled prior version during a dataset refresh, or an
explicit "not yet computed" message on a never-warmed store — instead of either an invisible multi-minute
wait blocking the page, or (on a never-warmed store) a silently-blank section with no explanation.

### New information displayed
The forward-aggregate evidence's serving status (`ready` / `refreshing` / `not_yet_computed`) and the
served version's generation timestamp, on the existing `/backtest` page's evidence section.

### New user actions
None — a read-only status disclosure; no new buttons, forms, or controls.

### UI surface changes
The EXISTING `/backtest` page's evidence section gains a status banner (refreshing) or an explicit empty
state (not-yet-computed); no new page, panel, or route.

### Product surface delta
`/backtest` (and the MCP `query_backtest` tool) never again blocks a request on a cold aggregate compute;
every request answers within the committed budget, honestly labeled with which version it is serving.

### Blueprint conformance
No new page/nav/route. J-08 gets a new Feature/journey-homes row in `blueprint.md` (already added this
iteration, additive) pointing to the SAME existing canonical home as J-07: `/backtest` (nav section
"Backtest") + the MCP `query_backtest` tool. No nav-skeleton change — `blueprint.reapproval-requested` is
NOT written.

### Data-contract additions
Two new fields on the EXISTING `GET /api/backtest` + MCP `query_backtest` payload (additive Notes-column
append to the EXISTING "Regime score, market phase, realized forward-returns" row in `blueprint.md`,
already applied this iteration — NOT a new row, NOT a second computing module, NOT a second endpoint):
- `evidence_status: "ready" | "refreshing" | "not_yet_computed"` — computed by the new read-only serving
  path in `app.engine.forward_testing`; served by `GET /api/backtest` and MCP `query_backtest`.
- `evidence_generated_at: string (ISO 8601 UTC datetime) | null` — the served version's
  `ForwardAggregateCache.created_at`; `null` only when `evidence_status == "not_yet_computed"`. Same
  computing module + endpoints as above.
- The pre-existing `evidence_by_horizon` field (unchanged shape) may now be `{}` (never partially
  populated) when `evidence_status == "not_yet_computed"`; unchanged, fully populated in the other two
  states. `compute_forward_aggregates` itself is NOT reopened (same signature/columns/streamed pattern,
  byte-identical since iter-14 — binding "Do not redo").
- For an `is_latest == false` (historical) request: both new fields are still present
  (`evidence_status` normally `"ready"` once its existing lazy create-once compute finishes;
  `evidence_generated_at` = that cache row's `created_at`) — this path's underlying compute behavior is
  UNCHANGED (see Scope note in BACKGROUND / OUT OF SCOPE / TC-13).

## OUT OF SCOPE

- The four sibling ingest-time caches — `event_study_cached`, `market_phase_cached`,
  `compute_drawdown_expectations_cached`, `index_series_cached_with_status` — keep their existing
  lazy-warm-and-self-heal shape; not touched (iter-15 coherence-auditor advisory: reuse this session's
  single-flight idiom if any of these is ever patched, but not this iteration).
- `compute_forward_aggregates` itself — signature, columns read, and streamed-read pattern stay
  byte-identical (AG-8 resolved iter-14, binding "Do not redo"; re-confirmed, not reopened).
- A historical (`is_latest == false`) `?as_of=` request's existing lazy compute-once-and-cache behavior
  for `evidence_by_horizon` — UNCHANGED this iteration (logged interpretation call, `assumptions.md`
  iter-16; see BACKGROUND Scope note and TC-13). Do not extend the "never compute on request" guarantee
  to this path.
- Any new DB table or a second cache identity — reuses the EXISTING `ForwardAggregateCache` columns/keys;
  if the developer needs a schema-level completeness marker, it stays inside the SAME table/module, never
  a second cache table for this value.
- J-06's already-settled clauses (the 10 idle-host page budgets, the ≤5s boot budget, the on-load
  code-level audit for pages other than `/backtest`) — settled iter-9/11, NOT re-measured or re-litigated
  this iteration; only the `/backtest` residual is addressed.
- J-07's already-confirmed clauses (steps 2-4: the full-basis warm + health-poll liveness + VmPeak margin
  + the memory-pressure-induction sufficiency call) — built + evaluator-confirmed iter-14/15, carried
  forward, NOT re-run from scratch; this iteration's evidence additionally confirms step 1's amended text
  ("served from storage per J-08") as a byproduct of the SAME operator pass (TC-16).
- AG-8 (`forward_testing.py`'s prior unbounded-load defect) — already RESOLVED iter-14; not reopened.
  `HOST_GUARD_REQUIRE_MARKERS` — resolved iter-14. The `demo.sh --session-live` walkthrough — already has
  operator evidence (iter-14); not a blocking item (a fresh J-08-specific operator run may be requested as
  a non-blocking follow-up once this lands — see NOTES).
- The undiagnosed 5.37s latency spike and the 84°C-vs-64°C thermal reporting gap (iter-15 carryover,
  non-blocking, unrelated to this architecture change) — not investigated this iteration.
- Touching `scripts/automation/*`, `main.py`, `app/api/health.py`, `app/engine/readiness.py`, or
  `app/engine/warmup.py` — binding "Do not redo" (iteration-state.md).
- A full pytest suite run — targeted, host-guard-confined tests only (standing session constraint).
- Repeating the operator-supervised pass beyond the ONE authorized run this iteration (AG-10-class; not a
  drill to repeat casually).
- Any new nav entry, top-level page, or IA change beyond the additive `blueprint.md` row already applied.

## DEFINITION OF DONE

- [ ] J-08's 5 steps pass: the `ready`/`refreshing`/`not_yet_computed` states each render their
  specified banner/section/empty-state per TC-10/TC-11/TC-12 (browser-qa-agent for the visible states;
  API/unit test layer for the call-count-zero assertion, step 4).
- [ ] J-06 re-verified passing: the `/backtest` budget is met in all three serving states (TC-3, TC-6,
  TC-16); J-06's other clauses stay carried from iter-9/11 (not re-litigated).
- [ ] J-07 re-verified passing: step 1's amended text ("served from storage per J-08") is confirmed by
  TC-16's operator pass; steps 2-4 carry forward from iter-14/15's confirmed evidence.
- [ ] Required-still-passing journeys J-01/J-03/J-04/J-05 remain green via deterministic replay + LLM
  fallback (TC-15).
- [ ] `compute_forward_aggregates` is invoked ONLY by the ingest finalize warm — zero invocations from
  `GET /api/backtest` / `query_backtest` across all three serving states, proven by call-count
  instrumentation (TC-1, TC-2, TC-6, TC-7).
- [ ] No response ever mixes horizon payloads from two different `dataset_version`s — per-version
  completeness enforced before any row is eligible to serve (TC-4).
- [ ] `compute_forward_aggregates`'s signature/columns/streamed pattern remain byte-identical; served
  payloads are byte-identical to a direct fresh compute for the same stored inputs (AG-3; TC-9).
- [ ] No anti-goal violation introduced (AG-3 byte-identity; AG-5 — the fallback never serves a partially
  newer/mixed state; AG-8 — no unbounded scan reintroduced, including in the new completeness lookup).
- [ ] The historical (`is_latest == false`) as-of path is unaffected — still computes-once-and-caches on
  first view, unchanged (TC-13).
- [ ] Unit/integration tests pass, host-guard-confined; no regressions beyond the carried, pre-existing
  `test_db.py::test_create_all_produces_expected_tables` (unrelated, no schema change).
- [ ] `reports/perf-budgets.md` gains one new dated section covering all three serving states against the
  existing committed ≤1.5s `/backtest` budget — same file, no second artifact.
- [ ] Dev handoff written at `docs/handoffs/goal-ops-hardening-iter-16-dev.md`.

## TESTING REQUIREMENTS

- Browser: J-01, J-03, J-04, J-05 (regression replay/LLM fallback); J-06/J-07/J-08 verified via a
  combination of the operator-supervised pass's recorded numbers (TC-3/TC-16) and browser-rendered
  screenshots of the `ready`/`refreshing`/`not_yet_computed` states on `/backtest` (TC-10/TC-11/TC-12).
- Unit/integration: extend `test_forward_testing_concurrency.py` (or a small sibling file) with the
  completeness/cutover logic, the call-count-zero proof for the request-serving path, the byte-identity
  proof, and a regression test proving the iter-15 single-flight guard still holds on the ingest-only path
  after the split; all host-guard-confined (`taskset -c 0-3,8-11`, BLAS/OMP/numexpr threads=4); never the
  full suite concurrently.
- Error cases: a never-warmed store must return HTTP 200 with the explicit empty state, never a 500/503;
  the read-only serving path must have NO compute-fallback branch under any failure/timeout condition
  (unlike the ingest-only path's existing wait-then-compute-independently fallback, which is scoped to
  producer-vs-producer races only and is never reachable from a request).

Test-first contract:

- TC-1: given a warm backend with a fully-warmed forward-aggregate store at `dataset_version` V1 (all 5
  configured horizons cached for the current latest `asof_key`), when `GET /api/backtest` (no `as_of`
  param) is requested 10 times, then every response has `evidence_status == "ready"`,
  `evidence_generated_at` equal to V1's cache `created_at`, and a call-count instrumentation wrapper
  around `compute_forward_aggregates` records exactly 0 invocations across all 10 requests.
- TC-2: given the same warm store, when the MCP `query_backtest` tool is invoked with `asof=None` 10
  times, then every response has `evidence_status == "ready"` and the SAME call-count wrapper records
  exactly 0 invocations across all 10 calls.
- TC-3: given a warm store complete at V1 and a `/data` single-day backfill that bumps the stamp to V2 and
  starts the ingest finalize warm, when `GET /api/backtest` is requested while V2's per-horizon warm has
  completed 2-of-5 horizons (a test-injected partial-warm state), then the response serves V1's complete
  `evidence_by_horizon` values byte-identical to V1's stored payload, `evidence_status == "refreshing"`,
  `evidence_generated_at` equals V1's `created_at`, and the response arrives within the committed ≤1.5s
  `/backtest` budget.
- TC-4: given the same partial-warm state as TC-3, when all 5 horizons of the served `evidence_by_horizon`
  are inspected, then every horizon's payload is verified to originate from V1 (none from V2) — no
  response ever mixes V1 and V2 horizon payloads.
- TC-5: given V2's ingest finalize warm has completed all 5 horizons and the run record's
  `aggregates_refreshed` list contains `"forward_aggregates"`, when `/backtest` is reloaded, then the
  response serves V2's stored values byte-identical to a direct fresh `compute_forward_aggregates` call at
  V2, `evidence_status == "ready"`, and V1's now-superseded cache rows are pruned (0 rows remain for the
  old `dataset_version` at this `asof_key`).
- TC-6: given a store where no forward-aggregate warm has ever completed for any `dataset_version` at the
  requested `asof_key` (a fresh-install/test-fixture DB), when `GET /api/backtest` is requested, then the
  response has `evidence_status == "not_yet_computed"`, `evidence_by_horizon == {}`,
  `evidence_generated_at == null`, HTTP status 200, arrives within the committed ≤1.5s budget, and the
  call-count wrapper records 0 invocations of `compute_forward_aggregates`.
- TC-7: given the `not_yet_computed` state of TC-6, when the same request is issued against the MCP
  `query_backtest` tool, then it returns the identical `evidence_status`/`evidence_by_horizon`/
  `evidence_generated_at` shape (mirrors the endpoint) with 0 `compute_forward_aggregates` invocations.
- TC-8: given the ingest finalize warm computing V2 via the existing per-horizon loop in
  `_refresh_ingest_aggregates`, when the warm completes all 5 horizons, then `compute_forward_aggregates`
  was invoked exactly 5 times (once per horizon) by that warm and 0 times by any concurrent
  request-path caller sampled during the same window.
- TC-9: given a real `GET /api/backtest` request served at `evidence_status == "ready"`, when its
  `evidence_by_horizon` payload is diffed against a direct, test-only call to `compute_forward_aggregates`
  for the same horizon/as_of/`dataset_version`, then the two are `==` byte-identical for every configured
  horizon.
- TC-10: given `/backtest` rendered in the browser with `evidence_status == "refreshing"`, when the page
  is inspected, then a visible banner or badge reading a refreshing-in-progress label plus the served
  generation timestamp is present alongside the still-fully-populated forward-tested evidence section —
  never a spinner-only skeleton in place of the evidence section.
- TC-11: given `/backtest` rendered in the browser with `evidence_status == "not_yet_computed"`, when the
  page is inspected, then an explicit empty-state message containing "not yet computed" and a
  call-to-action to run an ingest is visible in place of the forward-tested evidence section — the rest of
  the page (scorecard, leadership lists, as-of scan summary) renders unaffected, and no horizon numbers
  are shown.
- TC-12: given `/backtest` rendered in the browser with `evidence_status == "ready"`, when the page is
  inspected, then no refreshing banner and no empty-state message are present, and the forward-tested
  evidence section renders its normal populated numbers (regression guard against TC-10/TC-11's markup
  leaking into the steady state).
- TC-13: given a historical `?as_of=` request for a date whose `evidence_by_horizon` was never warmed by
  any ingest finalize run, when `GET /api/backtest?as_of=<date>` is requested, then it performs its
  existing pre-iter-16 create-once-and-cache behavior (one fresh `compute_forward_aggregates` call, then
  served from that cache row on a subsequent identical request) — confirming the request-path-zero-compute
  guarantee is scoped to `is_latest == true` and does not regress historical time-machine viewing.
- TC-14: given the targeted test suite for the touched functions in `forward_testing.py` / `backtest.py` /
  `tools.py` / `data_manager.py`, when run host-guard-confined (`taskset -c 0-3,8-11`, BLAS/OMP threads 4,
  no `loaded_engine`-marked full-basis fixtures), then all tests pass with 0 new failures beyond the
  carried pre-existing `test_db.py::test_create_all_produces_expected_tables`.
- TC-15: given the four currently-passing required-still-passing journeys (J-01, J-03, J-04, J-05), when
  their golden-script deterministic replay (or LLM fallback on a golden miss) is run, then all four remain
  `passing` with none moving from passing to failing.
- TC-16: given an operator-supervised pass (sequenced after code lands with all targeted tests green, per
  the pump note's AG-10 protocol) reproducing J-08 steps 1-3 — a small single-day `/data` backfill against
  the live deep basis while `/backtest` is polled throughout — when the `refreshing`-state response and
  then the post-warm `ready`-state response are measured, then both are recorded in `reports/perf-budgets.md`
  (same file, no second artifact) explicitly marked PASS or WARN against the committed ≤1.5s
  `/backtest` budget.
- TC-17: given N ≥ 4 concurrent ingest-triggered warm calls for the SAME never-yet-cached `(horizon,
  asof_key, dataset_version)` key on the ingest-only compute-and-persist path (simulating two overlapping
  ingest jobs), when they execute concurrently, then `compute_forward_aggregates` is invoked exactly once
  for that key (the iter-15 single-flight guard still holds after the split) and all callers complete
  within the existing bounded 45s wait.
- TC-18: given the completeness-lookup query the read-only serving path issues, when it is inspected
  (query plan or row-count assertion) for a DB containing forward-aggregate cache rows for many distinct
  historical `asof_key`s, then the query is filtered by the requested `asof_key` and touches only that
  identity's rows — never an unfiltered scan of the whole `forward_aggregate_cache` table.

## NOTES

- **Operational protocol for TC-16 (AG-10-class, ONE supervised pass):** launch via
  `scripts/start-backend.sh` only, host-guard caps active, 1Hz hwmon sampler + thermal watchdog armed —
  mirrors the iter-3/8/9/14/15 protocol. Standard path: developer/reviewer runs it directly under
  confinement. Fallback (pump note constraint — agents cannot start/stop services this session): the
  operator starts/monitors and reports console output, pids, and timestamps verbatim for attributed
  recording — never fabricate or omit a number. Services are currently DOWN; the operator boots them on
  request. Sequence TC-16 strictly AFTER TC-1 through TC-14/17/18 are green under targeted tests — do not
  spend the one authorized heavy pass on code that is not yet proven correct at the unit/integration level.
- **DB evidence motivating the completeness/cutover design (read-only inspection, 2026-07-23,
  `apps/backend/data/trendora.db`, no service start required):** `forward_aggregate_cache` currently holds
  10 rows; the current latest `asof_key='2026-07-22'` has all 5 horizons at the SAME `dataset_version`
  (`r1859-f3938660` — complete, consistent with a freshly-warmed identity). The non-latest
  `asof_key='2026-07-17'` (a prior "was-once-latest" identity) has 5 rows split across TWO
  `dataset_version`s (`r1272-f2674831` for horizon 1; `r1193-f2522006` for horizons 5/10/20/60) — proof
  that a naive "newest row per horizon" read would already serve a mixed-version payload for that
  identity today. This is exactly why a per-`(asof_key, dataset_version)` completeness check (not a
  per-row/per-horizon check) is required, not merely a stylistic preference.
- **Lesson applied (iter-15):** unit-test correctness on a synthetic fixture does not prove the ≤1.5s
  budget holds on the deep basis — TC-16's live operator pass is not optional decoration; it is the proof
  this session's own precedent (iter-11 through iter-15) requires before crediting a latency claim.
  **Lesson applied (iter-14):** correctness (call-count-zero, byte-identity) and latency (budget
  compliance) are different claims — both TC sets are required; neither substitutes for the other.
  **Lesson applied (iter-11):** cross-read `logs/backend.log` and `logs/hwmon/hwmon.csv` for the TC-16
  measurement window before attributing any remaining slowness to "ambient load."
- **Follow-up to weigh, not this iteration's scope:** once J-08 lands and is evaluator-confirmed, a fresh
  `demo.sh ops-hardening --session-live` operator run would newly exercise J-08's own `[NEW]`-flagged
  walkthrough steps (version-bump → instantly-served last-good with refreshing marker → fresh serve after
  the warm) — worth requesting from the operator as a non-blocking follow-up; not a DoD item here (no
  autonomous artifact-producing mechanism exists for this command, per the iter-12 decomposer finding,
  unchanged).
- **Carried, unrelated, non-blocking:** `test_db.py::test_create_all_produces_expected_tables`
  (pre-existing failure, no schema change this iteration); the undiagnosed 5.37s latency spike and the
  84°C-vs-64°C thermal reporting gap from iter-15 (unrelated to this architecture change).
- **Escalation flag:** if the completeness/cutover redesign turns out to require a genuinely new schema
  concept beyond what `ForwardAggregateCache`'s existing columns support (e.g., a race the cutover cannot
  resolve without an explicit "in-progress" marker row), implement the smallest such addition INSIDE the
  same table/module (never a second cache table) and document it plainly in the dev handoff rather than
  improvising an ad hoc second identity — flag to the evaluator if this materially changes the row's
  schema shape.
