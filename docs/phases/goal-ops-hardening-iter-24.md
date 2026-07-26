# Goal Iteration 24 — Disclose in-flight background-compute activity (J-09, badge + /data panel)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** ops-hardening
- **Iteration:** 24
- **Mode:** next
- **Depth:** full
- **Frontend Present:** yes
- **Target journeys:** J-09
- **Required-still-passing journeys:** J-01, J-03, J-04, J-05, J-06, J-07, J-08
- **Anti-goal reminders:**
  - **AG-1:** A score, ranking, or "edge" MUST NOT be presented as proven/confident unless it is backed by a
    **passing certified-claim entry** in the evidence ledger (out-of-sample, control-beating). Unbacked
    values MUST render a "not yet proven" state. *(critical)*
  - **AG-2 — Decision-quality only:** never present return promises, price targets, "buy/sell" signals, or
    alpha claims; never place or simulate orders. *(critical)*
  - **AG-3:** A journey passes ONLY if the **displayed numbers are correct** — they match the engine's
    computation for the same as-of date — not merely that the page renders. *(critical)*
  - **AG-4 — No overfit edges:** any pattern surfaced as "proven" must have survived the referee (sealed
    out-of-sample holdout + controls + multiple-testing correction), never in-sample fit alone. *(critical)*
  - **AG-5 — Preserve determinism and no-lookahead:** scoring uses bars ≤ as-of; forward returns use bars >
    as-of; never introduce lookahead anywhere. *(critical)*
  - **AG-6:** No iteration ships if its evidence-derived claims (if any) lack a passing referee verdict from
    the post-decompose gate. *(critical)*
  - **AG-7:** No hard-coded credentials, API keys, or tokens in source files. *(critical)*
  - **AG-8 — Resilience to data-shape and data-scale change:** widening the data basis (new nulls, broader
    pools, deeper history) must never crash an existing page or exhaust a service's memory — every existing
    consumer of a widened field is re-validated, the UI degrades gracefully (contained error boundary, honest
    "—"/NA placeholder, never a blank application-error page), and unbounded whole-table ORM loads are
    forbidden on the deep basis. *(critical)*
  - **AG-9 — Offline-deterministic ingest:** ingest jobs (fetch/backfill/rebuild) run only against the
    committed seed / local provider fixtures — no live external network calls or paid data services may be
    introduced without an explicit goal.md amendment. *(critical)*
  - **AG-10 — Host resource ceiling (hardware protection):** heavy compute — backfills, full-universe
    rebuilds, measurement passes, load drills, test-suite bursts — MUST be launched only via the project
    launch scripts (`scripts/dev.sh` / `scripts/start-backend.sh`), and those scripts MUST apply the host
    caps declared in `project-extensions/host-guard/host-guard.env` whenever that file is present
    (CPU-affinity mask, BLAS/OMP thread caps, `memory_cap_mb`, `malloc_arena_max`). Never remove, weaken, or
    bypass these caps: stripping a HOST-GUARD marked block from a launch script is a REGRESSION regardless
    of test outcomes. The ceilings are a physical constraint of the current host (two instant hardware
    resets under all-core vectorized ingest bursts: 2026-07-20 19:17, 2026-07-21 10:33), not a performance
    budget to optimize away. *(critical)*

## GOAL

The backend discloses, honestly and live, whenever it is running a background historical
forward-aggregate compute (started iter-20's `/backtest` fix) — naming which as-of date(s), how far
along, and the outcome of the last one — via the SAME top-bar readiness badge and one new `/data` panel,
so operators no longer have to reconstruct dispatch timing by hand from the database.

## BACKGROUND

`docs/goal.md` was auto-extended (goal-proposer, continuous-improvement loop) with **J-09** between the
`<!-- AUTO:journeys -->` markers after iter-23's `GOAL_ACHIEVED`. All 7 pre-existing journeys
(J-01/J-03/J-04/J-05/J-06/J-07/J-08) are `passing` — J-09 is the only non-passing journey, so it is the
sole target this iteration (priority rubric: no regressed journey, coherence was PASS at iter-23 so no
consolidation mandate, no unblocker candidate exists among the other 7 since they are all already
passing). J-09 is not "manufactured work" — it targets a real, repeatedly-documented gap: the iter-20
background dispatch (`_HIST_DISPATCH_INFLIGHT` in `app.engine.forward_testing`) has been invisible to
users and to the evaluator itself since it was introduced; iter-21/22/23's own eval.md entries had to
reverse-engineer its timing from raw `forward_aggregate_cache` commit timestamps and backend log lines
because no disclosed field existed (lessons iter-17 "check whether the diagnosis is blocked by missing
telemetry before treating the residual as owner-owned" and iter-18/19 "instrument phases... a
per-phase timing breakdown that only covers the phase you suspected will not surface it" both apply
directly — this iteration is exactly that instrumentation, made user-facing rather than forensic-only).

**Depth = full**, citing two of the four numbered depth triggers, either alone sufficient: **trigger 4
(hardening cadence)** — iter-21/22/23 were all dispatched lean (3 consecutive; cadence = 4), so
dispatching iter-24 lean would make 4 straight lean iterations, and this dispatch is the one that must
be full to satisfy the cadence; and **trigger 1 (structural / cross-cutting)** — this iteration lands a
genuinely new user-visible UI surface (a badge detail + a new `/data` panel) spanning ≥3 modules whose
interaction is not covered by any existing journey's tests: a backend engine module
(`app.engine.forward_testing`), the readiness composer (`app.engine.readiness`), the health endpoint
(`app/api/health.py`), and two frontend consumers (`readiness-provider.tsx`, `health-badge.tsx`, plus a
new `/data` panel) — goal.md's own Loop-mechanics line ("full when an iteration first lands
user-visible UI changes") names exactly this shape.

This iteration is additive instrumentation only: it must not alter any byte of what J-06/J-07/J-08
already serve. Per the binding "Do not redo" list in iteration-state.md, `compute_forward_aggregates`,
`resolved_forward_aggregate_evidence`, `ensure_historical_forward_aggregates_dispatched`'s keying and
single-flight semantics, and J-08's serving split/empty-state machine stay byte-unchanged; the owner's
BCW budget amendment in `reports/perf-budgets.md` is settled policy and is not re-litigated or amended
here. TC-13 (concurrent-ingest overlay) and TC-14 (disruptive kill/restart) are DONE and are never
re-run this iteration.

## IN SCOPE

### Backend
- [ ] Extend the existing historical dispatch registry in `app.engine.forward_testing`
      (`_HIST_DISPATCH_LOCK` / `_HIST_DISPATCH_INFLIGHT` — the same single-flight guard, unchanged
      keying and unchanged dispatch/no-dispatch decision) so that, for each in-flight
      `(asof_key, dataset_version)`, it also records `started_at` (UTC timestamp at dispatch time) and
      live `horizons_done` / `horizons_total` counters (incremented as
      `_run_historical_forward_aggregates_dispatch` completes each configured horizon via the unchanged
      `forward_aggregates_ingest_cached` call).
- [ ] In the SAME dispatch worker's existing `finally` block, append exactly one newest-first outcome
      record — `{asof_key, dataset_version, outcome: "completed"|"failed", started_at, finished_at,
      duration_ms, reason}` — to a bounded in-process ring, capped at a new
      `startup.background_compute_history_size` config value (never a hardcoded literal); `reason` is
      non-null only when `outcome == "failed"` (the worker's existing caught-and-logged exception message).
- [ ] Add one new read-only accessor in the same module, e.g. `get_background_compute_status()`, returning
      `{"active": [...], "recent_outcomes": [...]}` from the registry above — no new lock semantics beyond
      what already guards `_HIST_DISPATCH_INFLIGHT`.
- [ ] Add `startup.background_compute_history_size: int` (validated `>= 1`, default `5`) to `config.yaml`
      and `StartupCfg` (`apps/backend/app/config.py`), following the existing `health_poll_interval_seconds`
      pattern.
- [ ] `app.engine.readiness.compute_readiness` composes the new accessor's output into its returned dict as
      a new `background_compute` sibling key (mirrors how it already composes `app.engine.warmup`'s
      separate-module state into the same dict) — no DB read added, in-memory registry read only.
- [ ] `GET /api/health` (`app/api/health.py`) serves `background_compute` as one new additive top-level
      field, degrading to `{"active": [], "recent_outcomes": []}` on any compute error (mirrors the
      existing `readiness`/`preflight` degrade-on-error convention — never blanks the probe).
- [ ] Zero change to `compute_forward_aggregates`, `resolved_forward_aggregate_evidence`, or
      `ensure_historical_forward_aggregates_dispatched`'s keying/dispatch-decision semantics.

### Frontend
- [ ] `ReadinessProvider` (`readiness-provider.tsx`) reads `background_compute` from the SAME existing
      `/api/health` poll and exposes it via `ReadinessContextValue` (no second fetch, no second poll,
      no client-side derivation of any field).
- [ ] `HealthBadge` (`health-badge.tsx`) renders one additional inline element,
      `data-testid="background-compute-indicator"`, alongside the existing readiness pill whenever
      `background_compute.active.length > 0` (any readiness state — `ready`, `initializing`, etc.), naming
      the count of in-flight windows; absent entirely when `active` is empty. Never replaces or hides the
      existing pill/state.
- [ ] New `BackgroundComputePanel` on `/data` (`app/data/page.tsx`), following the existing
      Card/PanelTitle/`data-testid` convention used by `RunHistoryPanel`/`JobProgressPanel`: lists each
      active window (as-of key, elapsed time, `horizons_done`/`horizons_total`) and the most recent
      completed/failed outcome (duration; the reason string when failed); an explicit idle copy
      ("No background compute running. Last outcome: none yet." or the most recent entry) when
      `active` is empty; a one-line note that this state is process-lifetime (cleared on backend restart).
      Reads `useReadiness()` — no second fetch.

### New user-facing capability
Any operator, on any page, can see live whether the backend is currently running a background
historical-evidence compute (and for the full detail, on `/data`, exactly which as-of date(s), how far
along by horizon count, and the outcome — success or failure with reason — of the most recent one)
without reading logs or querying the database.

### New information displayed
- Top bar (all pages): an inline "background compute running (N)" indicator next to the readiness pill,
  shown only while `background_compute.active` is non-empty.
- `/data`: a new panel listing in-flight windows (as-of, elapsed, horizons done/total) and recent
  completed/failed outcomes (duration, failure reason).

### New user actions
None — this is a read-only disclosure surface; no new buttons, forms, or controls.

### UI surface changes
- `HealthBadge` (existing component, every page): gains one conditional inline child element.
- `/data` page: gains one new panel (`BackgroundComputePanel`), placed alongside the existing
  `JobProgressPanel`/`RunHistoryPanel` panels.

### Product surface delta
The in-process background dispatch introduced by iter-20 (previously invisible — reconstructable only
via raw DB timestamps, as iters 21–23 each had to do) becomes a first-class, honestly-degrading served
field, visible from the global badge and detailed on `/data`.

### Blueprint conformance
Lives entirely under the already-registered "Backend readiness / boot phase + preflight verdict" home:
global readiness badge (top bar, every page) + `/data` (Data Manager). No new nav entry, no new route —
`runs/goal-session-ops-hardening/state/blueprint.md`'s Information Architecture "Feature / journey homes"
table and Data Contract row for that home were updated this iteration (additive edits; no nav-skeleton
change, so no `blueprint.reapproval-requested` file was written).

### Data-contract additions
**New value:** `background_compute` — one new sibling field on the existing `GET /api/health` payload.

```
background_compute: {
  active: [
    {
      asof_key: string,        # ISO date, e.g. "2026-05-30"
      dataset_version: string, # e.g. "r1865-f3954530"
      started_at: string,      # ISO 8601 UTC timestamp, dispatch start
      elapsed_ms: int >= 0,    # computed at read time = now - started_at
      horizons_done: int >= 0,
      horizons_total: int >= 1
    }, ...
  ],
  recent_outcomes: [           # newest-first; length <= startup.background_compute_history_size (config)
    {
      asof_key: string,
      dataset_version: string,
      outcome: "completed" | "failed",
      started_at: string,      # ISO 8601 UTC
      finished_at: string,     # ISO 8601 UTC
      duration_ms: int >= 0,
      reason: string | null    # non-null only when outcome == "failed"
    }, ...
  ]
}
```

- **Computing module (single producer):** the historical dispatch registry inside
  `app.engine.forward_testing` (extends the existing `_HIST_DISPATCH_LOCK`/`_HIST_DISPATCH_INFLIGHT`
  single-flight guard — the SAME writer, unchanged keying/dispatch-decision semantics), exposed through
  one new read-only accessor (`get_background_compute_status()`), composed into
  `app.engine.readiness.compute_readiness`'s existing return dict (mirrors the existing cross-module
  composition of `app.engine.warmup`'s state into this same dict — no new pattern).
- **Serving endpoint (single):** `GET /api/health` — the same endpoint already serving `readiness`,
  `readiness_detail`, `warmup`, `preflight`. No second endpoint, no second poll.
- **Threshold:** `startup.background_compute_history_size` (config.yaml / `StartupCfg`, default `5`,
  validated `>= 1`) bounds `recent_outcomes`'s retained length — never a hardcoded literal.

## OUT OF SCOPE

- Bounding or capping the number of concurrent background dispatches (backlog card B-1107) — owner-deferred,
  unrelated to disclosure.
- Any change to `compute_forward_aggregates`, `resolved_forward_aggregate_evidence`, or
  `ensure_historical_forward_aggregates_dispatched`'s keying/single-flight semantics, or to any served
  evidence value or the `ready`/`refreshing`/`not_yet_computed` state machine — byte-unchanged (binding
  "Do not redo").
- Any change to the `≤1.5s` / `≤0.1s` steady-state budgets or the BCW ceilings in `reports/perf-budgets.md`
  — settled owner policy (binding "Do not redo"); this iteration's own steady-state `GET /api/health`
  re-measurement must stay within the UNCHANGED `≤0.1s` budget (zero DB work added).
- Re-running TC-13 (concurrent-ingest overlay) or TC-14 (disruptive kill/restart) — already done and dated
  2026-07-25 (binding "Do not redo").
- Retargeting `test_forward_testing_serving_split.py`'s `is_latest` monkeypatches or removing the dangling
  imports at `backtest.py:75` / `mcp/tools.py:38` — unrelated carried item, not touched by this diff.
- Estimated finish times or fabricated completion percentages — J-09 step 6 explicitly forbids these; only
  real observed `horizons_done`/`horizons_total` counts and elapsed time are shown.
- Persisting background-compute history across a backend restart — J-09 step 6 requires this be honestly
  scoped as process-lifetime only (in-memory), never a persisted table.
- Any new nav entry or route — this lives entirely under the existing global badge + `/data` home.

## DEFINITION OF DONE

- [ ] Target journey J-09 passes via browser-qa-agent.
- [ ] Required-still-passing journeys J-01, J-03, J-04, J-05, J-06, J-07, J-08 remain green (deterministic
      replay + LLM fallback where no golden exists).
- [ ] No anti-goal violation introduced (AG-3 correctness of every disclosed number/timestamp against the
      dispatch's own record and `forward_aggregate_cache`; AG-1/AG-4/AG-6 — no proven/reassurance language
      introduced; AG-8/AG-10 untouched — zero new compute, zero new DB load).
- [ ] Unit tests pass; no regressions; `GET /api/health` steady-state latency re-measured and recorded in
      `reports/perf-budgets.md`, staying within the unchanged `≤0.1s` budget.
- [ ] Dev handoff written at `docs/handoffs/goal-ops-hardening-iter-24-dev.md`.

## TESTING REQUIREMENTS

- Browser: J-09 (primary — badge indicator + `/data` panel across a real background-compute window).
  Regression smoke via deterministic replay for J-01, J-03, J-04, J-05, J-06, J-07, J-08.
- Unit/integration: the dispatch registry's new `started_at`/`horizons_done`/`horizons_total` bookkeeping
  and bounded `recent_outcomes` ring; `get_background_compute_status()`'s shape on empty/active/failed
  states; `compute_readiness`'s composition of the new field; `GET /api/health`'s degrade-on-error path;
  `StartupCfg` validation of `background_compute_history_size >= 1`.
- Error cases: a dispatch worker exception (simulated by injecting a failure into one horizon's
  `forward_aggregates_ingest_cached` call in a test) must be caught, recorded as `outcome: "failed"` with a
  non-null `reason`, and must release the in-flight slot so the SAME identity can re-dispatch on the next
  request (mirrors the existing TC-7 non-fatal-failure contract) — never left silently stuck `active`.

Test-first contract: every DEFINITION OF DONE checkbox and every Data-contract addition above maps to at
least one concrete scenario below.

- TC-1: given a warm backend at rest with no background dispatch ever triggered since boot, when
  `GET /api/health` is polled, then the response is HTTP 200 with `background_compute.active == []` and
  `background_compute.recent_outcomes == []`, and `readiness == "ready"`.
- TC-2: given a `/backtest` (or MCP `query_backtest`) request for a historical as-of whose forward-aggregate
  evidence is not `"ready"` for the current `dataset_version`, when the request is made, then the HTTP
  response returns within J-08's existing unchanged budget (no request-path block) and the dispatch
  registry gains one `active` entry keyed on that `(asof_key, dataset_version)` with `horizons_total`
  equal to `len(cfg.walk_forward.horizons)` and `horizons_done == 0`.
- TC-3: given that dispatch is still in flight, when `GET /api/health` is polled during the window, then
  `background_compute.active` contains exactly one entry for that identity with `0 <= horizons_done <
  horizons_total`, `started_at` matching the dispatch's own recorded start (within 1s), and the top bar
  (any page) renders an element `data-testid="background-compute-indicator"` naming the in-flight count.
- TC-4: given the `/data` page is open during the same window, when it reads the shared readiness poll,
  then `BackgroundComputePanel` (element `data-testid="background-compute-panel"`) displays that window's
  as-of key, an elapsed-time value > 0, and the current `horizons_done`/`horizons_total` pair.
- TC-5: given the dispatch completes successfully, when `GET /api/health` is polled again, then
  `background_compute.active` no longer contains that identity, and
  `background_compute.recent_outcomes[0]` shows `outcome == "completed"` with a `finished_at` timestamp and
  `duration_ms >= 0`, and `finished_at` falls within 2s of the corresponding
  `forward_aggregate_cache` row's `created_at` for that `(asof_key, dataset_version)`.
- TC-6: given the dispatch worker's compute raises an exception for one horizon (test-injected fault),
  when the worker's existing `finally` block runs, then `background_compute.recent_outcomes[0]` shows
  `outcome == "failed"` with a non-null `reason` string, the identity's `active` slot is released, and a
  subsequent request for the SAME identity dispatches again (no permanent wedge).
- TC-7: given `GET /api/health` is polled at steady state (no background compute in flight, no concurrent
  ingest), when its latency is measured over the existing repeated-poll harness, then max observed latency
  is `<= 0.1s`, recorded in `reports/perf-budgets.md`'s Iteration 24 section.
- TC-8: given the backend process restarts, when `GET /api/health` is polled after boot, then
  `background_compute.active == []` and `background_compute.recent_outcomes == []` (in-memory state
  cleared), and the `/data` panel's copy states the history is since the last restart, not an empty
  fabricated history.
- TC-9: given more than `startup.background_compute_history_size` background dispatches have completed
  since boot, when `GET /api/health` is polled, then `len(background_compute.recent_outcomes) <=
  startup.background_compute_history_size`, with the newest entry first.
- TC-10: given a browser walkthrough triggers exactly one background-compute window the way a user does
  (loading `/backtest` for a historical as-of not yet complete for the current `dataset_version`), when the
  tester watches the top bar and `/data` panel across the window, then the badge's
  `background-compute-indicator` is present during the window and absent after it completes, and the
  `/data` panel's `recent_outcomes` gains a new entry with a real measured `duration_ms` matching J-09
  steps 1–6.

## NOTES

- This journey was added by the goal-proposer (continuous-improvement loop) between the
  `<!-- AUTO:journeys -->` markers in `docs/goal.md`; it is not a human-authored journey but is treated
  identically for planning purposes.
- Applies iter-17's lesson ("check whether the diagnosis is blocked by missing telemetry before treating a
  residual as owner-owned") and iter-18/19's lesson (instrument the actual subsystem, not just the phase
  you suspected) — this iteration is exactly that instrumentation, made permanently user-facing.
- Non-blocking carries from iter-23 (unaffected by this iteration, still owed): retarget
  `test_forward_testing_serving_split.py`'s four `is_latest` monkeypatches before removing the dangling
  imports at `backtest.py:75` / `mcp/tools.py:38`; run `test_api_backtest.py` TC-11 + `test_data_manager.py`
  heavy fixtures off the constrained box; owner-optional backlog card B-1107.
- If browser-qa cannot reliably trigger a real BCW deterministically (timing-dependent), the developer may
  add a narrow, clearly-labeled test-only hook to force-dispatch one historical as-of on demand for the
  walkthrough — it must call the SAME `ensure_historical_forward_aggregates_dispatched` function unchanged,
  never a second dispatch path.
