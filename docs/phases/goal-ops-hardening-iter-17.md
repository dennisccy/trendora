# Goal Iteration 17 — Last-good evidence crosses as-of boundaries + `/backtest` latency root-cause

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** ops-hardening
- **Iteration:** 17
- **Mode:** next
- **Depth:** full
- **Frontend Present:** yes
- **Target journeys:** J-06, J-07, J-08
- **Required-still-passing journeys:** J-01, J-03, J-04, J-05
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

`/backtest`'s evidence section keeps showing real, honestly-labeled numbers — never an empty
"not yet computed" state — through the single most common ingest shape (the latest trading day
advancing while its forward-aggregate warm is still in flight), and the stored-row-read latency spikes
seen during ingest windows are root-caused and, where boundedly fixable, reduced, with fresh live
evidence captured for the two serving states nobody has seen rendered yet.

## BACKGROUND

Iteration 16 shipped the precompute-before-serve split for J-08 and the evaluator scored it `partial` on
exactly three open items, all agent-owned (`runs/goal-session-ops-hardening/iter-16/eval.md`): **(1) audit
B1** — `resolved_forward_aggregate_evidence` (`apps/backend/app/engine/forward_testing.py:1163-1242`)
resolves completeness filtered to ONE `asof_key` only (line 1209), so the *common single-latest-date*
backfill shape — where a brand-new latest `ScannerRun` lands with zero forward-aggregate rows yet — serves
the fresh-install-shaped `not_yet_computed` instead of the labeled last-good evidence J-08 step 2 promises.
The evaluator ruled (not deferred) that the fallback must cross `asof_key` boundaries. **(2)** two of the
three serving states have never been rendered in a browser: `not_yet_computed` (zero evidence — UT-03 was
correctly SKIPPED as non-destructive on the populated working DB) and the *corrected* refreshing banner
copy (the only screenshot on file shows the pre-fix, factually-false wording). **(3)** 11/68 live polls of
`/backtest` breach the committed ≤1.5s budget (max 12.655s) during the ingest window, a documented DoD
miss per iter-12's human-ratified precedent (a real number beats a "may pass" recommendation).

This iteration closes all three, which is also why it names three journey IDs rather than one: J-08's own
step 2/5 clauses cover items 1-2 directly; J-06's step 2 latency assertion and J-07's amended step-1 "served
from storage per J-08" (confirmed by iter-16 as met for the gap-backfill shape but **not** for the
as-of-advancing shape — audit B1) are both closed by the *same* B1 fix and the *same* latency work. Per the
priority rubric, this is deliberately ONE integrated change (the forward-aggregate serving path) carried
across three journey labels, not two independent risky changes — matching how iterations 14/15/16 have
each bundled 2-3 of these same IDs throughout this arc (rubric rule 5 permits several journeys per
iteration as long as it is not two *unrelated* risky changes).

**Depth: full.** Trigger 1 (structural/cross-cutting) fires: the fix touches ≥3 modules whose interactions
span more than one journey's own tests — `apps/backend/app/engine/forward_testing.py` (the completeness
search itself), `apps/backend/app/api/backtest.py` + `apps/backend/app/mcp/tools.py` (both response
shapes gain the new field), and `apps/frontend/app/backtest/page.tsx` (the label surfaces it) — and the
latency investigation may additionally touch `apps/backend/app/engine/data_manager.py`'s ingest finalize
write pattern. Trigger 2 (data model) reinforces this: the fix changes how an already-registered
Data-Contract value's computing module resolves its result (a new field, `evidence_asof`, ships on the
same row) — the prior verdict was `CONTINUE`, not `ESCALATE`, so full is not otherwise mandatory, and this
iteration is dispatched full on the merits, matching the iter-16 evaluator's own explicit recommendation
("FULL depth — the fix changes the same serving contract and adds a user-visible as-of label").

**Lessons applied:** iter-16's own lesson — "enumerate the ways the *identity* can move, not just the ways
the *value* can go stale, and make sure the live test exercises the identity-advancing shape, not only the
convenient one" — is exactly what TC-1/TC-4/TC-8 below require (the prior two iterations' live passes both
used historical *gap* dates, which never advance the latest `asof_key`; this iteration's tests must
exercise a genuinely advancing key). iter-11's lesson — cross-read `logs/backend.log` and
`logs/hwmon/hwmon.csv` before accepting an "environmental" explanation for an anomaly — applies to the
latency investigation: `database.pragmas` already runs WAL+NORMAL with a 30s `busy_timeout_ms`
(`config.yaml:106-108`), so a 12.655s read is consistent with a reader waiting out a writer/checkpoint
lock rather than an unrelated ambient cause; rule that in or out with the actual logs, not a plausible
story. iter-15's lesson — a small-fixture concurrency ratio does not extrapolate to a deep-basis cost —
means any latency mitigation must be validated by the SAME deep-basis, operator-supervised protocol
iter-16's TC-16 used, not a fixture reproduction alone.

**Operational constraints this dispatch (per the pump/operator note):** agents cannot start or stop
services this session (permission classifier). Both backend and frontend are already running
(`:8255`/`:3255`) — normal app actions against them (submitting a small backfill, polling endpoints,
browser navigation) are NOT service starts/stops and are agent/QA-performable. Two exceptions require the
operator: (a) rendering `not_yet_computed` needs a *disposable* database copy (never the working
`trendora.db`), which means booting a throwaway backend process on an alternate port — a genuine service
start; (b) the deep-basis latency re-measurement mirroring TC-16's 68-poll protocol is an AG-10-class heavy
pass (cooled host, sampler, armed watchdog, `taskset -c 0-3,8-11`, BLAS/OMP=4) per this session's standing
practice for every iter-14/15/16 heavy pass. Both are written below as OPERATOR steps; write any
restart/kill/boot/live-measurement instruction as operator-performed, never agent-performed, per the pump
note.

## IN SCOPE

### Backend

- [ ] Widen `resolved_forward_aggregate_evidence`'s (`apps/backend/app/engine/forward_testing.py`)
  completeness/fallback search so that when the REQUESTED `asof_key` has no complete `dataset_version`, it
  looks at OLDER `asof_key`s (never a later one — AG-5) and serves the most recent one that DOES have a
  complete version, labeled `refreshing`. Reserve `not_yet_computed` for the case where NO `asof_key` has
  ever had a complete version (the true fresh-install shape, J-08 step 5).
- [ ] Add the new `evidence_asof` field to the SAME response shape returned by `GET /api/backtest`
  (`apps/backend/app/api/backtest.py`) and the MCP `query_backtest` tool (`apps/backend/app/mcp/tools.py`)
  — both already destructure `resolved_forward_aggregate_evidence`'s return dict; extend that dict, not a
  second source.
- [ ] Add the as-of-advancing scenario (and the multi-older-key tie-break case) to
  `apps/backend/tests/test_forward_testing_serving_split.py`, which currently has zero coverage of this
  shape.
- [ ] Root-cause the 11/68 `/backtest` stored-row-read latency breaches (max 12.655s) inside the ingest
  window — `config.yaml`'s `database.pragmas` already enables WAL+NORMAL with a 30s `busy_timeout_ms`
  (lines 106-108), so investigate writer-lock/checkpoint contention from the ingest finalize hook's write
  pattern (`apps/backend/app/engine/data_manager.py`'s per-date/per-horizon commit loops) rather than
  assuming an unrelated cause; apply a bounded mitigation if the root cause is fixable within this
  iteration's scope, or record precisely why the residual is an unavoidable, disclosed contention cost.
  Audit B5 (the historical branch reads and deserializes every stored payload twice) is a cheap adjacent
  win worth taking regardless.
- [ ] Non-blocking hygiene: `evidence_generated_at`'s ISO-8601 UTC timezone designator (audit B3, the field
  is young); the duplicated empty-state sentence (audit F3); soften the `not_yet_computed` `EmptyState`
  copy so it no longer presumes a user hasn't started an ingest (audit F2 residual) — this should already
  be moot once B1 correctly routes the mid-ingest shape to `refreshing`, but confirm and tidy the wording
  regardless.

### Frontend

- [ ] `RefreshingEvidenceBanner` (`apps/frontend/app/backtest/page.tsx`) surfaces the new `evidence_asof`
  field so the banner discloses WHICH as-of's evidence is being shown, not only its generation timestamp —
  the literal J-08 step 2 wording ("labeled with that version's served as-of").
- [ ] Apply the F2/F3 copy adjustments to the same page's `not_yet_computed` `EmptyState` call site.

### New user-facing capability

When the single most common ingest shape occurs (the latest trading day advances while its
forward-aggregate warm is still running), `/backtest` now shows the honest last-good evidence — labeled
with its own as-of date — instead of an empty "not yet computed" state that wrongly told an
already-ingesting user to run an ingest.

### New information displayed

The served evidence's own as-of date (`evidence_asof`), shown in the refreshing banner alongside the
existing generation timestamp.

### New user actions

None — no new controls; this is a correctness and disclosure fix to an existing read-only evidence
display.

### UI surface changes

The existing `/backtest` refreshing banner and not-yet-computed empty state gain sharper, more honest
text. No new page, panel, or route.

### Product surface delta

`/backtest`'s evidence section stays populated and honestly labeled across the single most common ingest
shape (latest-date advance), where before it silently emptied and misdirected the user.

### Blueprint conformance

Backtest section, canonical home `/backtest` + MCP `query_backtest` tool — the SAME existing home J-06,
J-07, and J-08 already have in `runs/goal-session-ops-hardening/state/blueprint.md`'s Information
Architecture table. No new page, nav entry, or route this iteration (confirmed — blueprint.md's iter-17
paragraph, appended by this decomposer, states this explicitly).

### Data-contract additions

`evidence_asof: string|null` (ISO 8601 date, e.g. `"2026-07-22"`) — the as-of whose stored complete
forward-aggregate version is actually being served: equal to the page's own resolved `asof_date` when
`evidence_status="ready"`, an OLDER date when `evidence_status="refreshing"` crosses `asof_key` boundaries,
`null` when `evidence_status="not_yet_computed"`. Computed by the SAME module,
`app.engine.forward_testing.resolved_forward_aggregate_evidence` (unchanged function name/module), served
by the SAME two endpoints, `GET /api/backtest` and MCP `query_backtest` (unchanged) — registered as an
additive Notes-column append to the EXISTING "Regime score, market phase, realized forward-returns" row in
`blueprint.md`'s Data Contract (done by this decomposer; tagged `[TARGET, iter-17 building]` until
evaluator-confirmed, per the file's own established convention). No other new displayed value this
iteration — the latency investigation produces a measurement recorded in `reports/perf-budgets.md`, not a
new served value.

## OUT OF SCOPE

- `compute_forward_aggregates`'s body — byte-unchanged since iter-14, AG-8 resolved; not reopened
  (binding, iteration-state.md "Do not redo").
- The compute-vs-serve split itself and the completeness-gated cutover pruning logic
  (`forward_testing.py` ~lines 1122-1160) — this iteration extends the READ-side fallback search only;
  never revert cutover pruning to per-horizon deletion, and never add a compute branch to the read path
  (binding, "Do not redo").
- `refreshing`'s no-self-heal behavior (audit B2) — an explicit, documented trade-off, not built this
  iteration: values stay correct and honestly labeled, a page reload is the only cost, and no journey step
  asks for auto-refresh.
- The `loaded_engine`-dependent test (T1, `test_api_backtest.py::test_backtest_evidence_by_horizon_shape_and_keys`)
  — the ~80-minute fixture; cite it, do not run it (binding, "Do not redo").
- A fresh J-04 kill/restart replay — operator-owned and deferred since iter-14/15/16; this iteration
  performs only a non-disruptive steady-state sanity check (TC-11), never a kill/restart.
- `main.py`, `app/api/health.py`, `app/engine/readiness.py`, `app/engine/warmup.py`, `scripts/*`,
  `scripts/automation/*` — untouched (binding, "Do not redo").
- The full pytest suite — targeted, host-guard-confined runs only (`taskset -c 0-3,8-11`, BLAS/OMP=4).
- The `demo.sh ops-hardening --session-live` walkthrough — a human-interactive-only terminal mode (iter-12
  finding, settled); not an autonomous deliverable, not part of this iteration's DoD.
- J-06's other 10 idle-host page budgets, the ≤5s boot budget, and the non-`/backtest` on-load audit —
  settled iter-9/11/13; not re-measured (binding, "Do not redo").

## DEFINITION OF DONE

- [ ] `resolved_forward_aggregate_evidence` crosses `asof_key` boundaries correctly (TC-1, TC-4); the true
  fresh-install shape (TC-3), the historical carve-out (TC-6), and no-lookahead (TC-5) all still hold
- [ ] `evidence_asof` is served identically by `GET /api/backtest` and MCP `query_backtest` (TC-2) and is
  registered in `blueprint.md`'s Data Contract (done this iteration)
- [ ] `RefreshingEvidenceBanner` visibly displays `evidence_asof` (TC-7)
- [ ] Live browser evidence captured for the as-of-advancing `refreshing` case (TC-8) and the
  `not_yet_computed` case on a disposable DB copy (TC-9) — or, if operator time does not permit TC-9 this
  session, the attempt and the reason are documented for the evaluator to judge sufficiency
- [ ] The `/backtest` latency root-cause investigation is complete, any bounded mitigation is applied, and a
  fresh, directly-comparable measurement is recorded in `reports/perf-budgets.md` (TC-10)
- [ ] J-04 gets a non-disruptive carry-forward sanity check (TC-11) — no kill/restart performed
- [ ] Target journeys J-06, J-07, J-08 are evaluated by the goal-evaluator against the evidence this
  iteration produces (this spec does not itself declare any journey passing)
- [ ] Required-still-passing journeys J-01, J-03, J-04, J-05 remain green (deterministic replay + LLM
  fallback, mechanically verified)
- [ ] No anti-goal violation introduced; AG-5 no-lookahead is specifically re-verified for the new
  cross-`asof_key` search (TC-5); AG-3 byte-identity holds for evidence served from any `asof_key` (TC-1,
  TC-2)
- [ ] All pre-existing tests in `test_forward_testing_serving_split.py`, `test_forward_testing_concurrency.py`,
  `test_forward_testing.py`, and `test_data_manager.py` keep passing alongside the new TC-1/3/4/5/6 tests;
  no regressions (the pre-existing, unrelated `test_db.py::test_create_all_produces_expected_tables`
  failure is carried, not a new regression)
- [ ] Dev handoff written at `docs/handoffs/goal-ops-hardening-iter-17-dev.md`

## TESTING REQUIREMENTS

- Browser: J-06 (`/backtest` latency, TC-10), J-07 (health/availability during the ingest window, carried
  from TC-16's protocol, TC-10), J-08 (the `refreshing` cross-boundary case TC-8, the `not_yet_computed`
  case TC-9, the banner label TC-7)
- Unit/integration: `apps/backend/tests/test_forward_testing_serving_split.py` (TC-1, TC-3, TC-4, TC-5,
  TC-6 below), plus any regression test the latency mitigation itself needs
- Error cases: a request whose resolved `asof_key` has no complete version anywhere in the table (TC-3)
  must still answer HTTP 200 with the honest empty state, never a 500 or a fabricated payload

- TC-1: given a `ForwardAggregateCache` fixture with a COMPLETE version at an older `asof_key`
  (e.g. `2025-01-10`) and a newer `asof_key` (e.g. `2025-01-13`) with ZERO forward-aggregate rows of any
  version, when `resolved_forward_aggregate_evidence` is called with `as_of=2025-01-13`, then it returns
  `evidence_status="refreshing"`, `evidence_asof="2025-01-10"`, and `evidence_by_horizon` equal to the
  older version's stored rows for every configured horizon — never `not_yet_computed`.
- TC-2: given the same fixture as TC-1, when `GET /api/backtest`'s route function builds its latest-view
  response, then the returned JSON includes `evidence_asof: "2025-01-10"` alongside the existing
  `evidence_status`/`evidence_generated_at`/`evidence_by_horizon` fields, and the MCP `query_backtest` tool
  returns the identical `evidence_asof` value for the same inputs.
- TC-3: given a store where NO `asof_key` has ever had a complete `dataset_version` (the existing
  `test_evidence_not_yet_computed_before_any_warm` fixture, unchanged), when
  `resolved_forward_aggregate_evidence` is called, then it still returns `evidence_status="not_yet_computed"`,
  `evidence_asof=None`, `evidence_by_horizon={}` — identical to today's behavior (regression guard).
- TC-4: given TWO older `asof_key`s each with a complete version (e.g. `2025-01-08` and `2025-01-10`) and
  the requested `asof_key` (`2025-01-13`) incomplete, when resolved, then the served `evidence_asof` is the
  MORE RECENT of the two (`2025-01-10`), never the older one and never a response mixing rows from both.
- TC-5: given the fallback crosses to an older `asof_key`, when the completeness query executes, then no
  row whose `asof_key` date is AFTER the requested `as_of` is ever read or served — verified via the same
  `before_cursor_execute` SQL-inspection technique the existing TC-18 test already uses.
- TC-6: given the historical (`is_latest=False`) fixture (mirrors the existing
  `test_historical_asof_keeps_pre_iter16_create_once_and_cache_behavior`), when requested twice, then it
  still computes-once on the first call and caches on the second — unchanged by this iteration's fallback
  search.
- TC-7: given a `/backtest` response with `evidence_status="refreshing"` and `evidence_asof` earlier than
  the page's own resolved `asof_date`, when the page renders, then `RefreshingEvidenceBanner` visibly
  displays the `evidence_asof` date text, not only the generation timestamp.
- TC-8 (agent/QA-performed, no service start/stop): given the currently-running backend/frontend, when a
  small single-day backfill is submitted through the existing `/data` job form for a date that ADVANCES the
  latest stored run (not a historical gap date), and `/backtest` is loaded while that date's
  forward-aggregate warm is still incomplete, then the page renders within its committed ≤1.5s
  served-from-storage budget showing `refreshing` labeled with the PRIOR `asof_key`'s date (screenshot
  captured) — never `not_yet_computed`, never a frozen frame.
- TC-9 (OPERATOR-performed — requires booting a throwaway process): given a throwaway backend instance
  launched via `scripts/start-backend.sh` under a `TRENDORA_CONFIG` override pointed at a disposable copy
  of `trendora.db` (schema created, zero ingest ever run) on an unused port, when `/backtest` is loaded
  against that instance, then the page renders the `not_yet_computed` `EmptyState` within budget (screenshot
  captured), and the working `trendora.db`'s own row counts are unchanged before/after (never opened by the
  throwaway instance).
- TC-10 (OPERATOR-performed, AG-10-class, ONE pass): given the same deep-basis ingest-window
  concurrent-poll protocol iter-16's TC-16 used (cooled host, sampler live, watchdog armed,
  `taskset -c 0-3,8-11`, BLAS/OMP=4), when `/backtest` is re-measured after this iteration's latency
  investigation/mitigation, then the breach count and max latency are recorded in a new dated section of
  `reports/perf-budgets.md`, directly comparable to iter-16's baseline (11/68 breaches, max 12.655s).
- TC-11 (non-disruptive, no kill/restart): given the backend is already running, when `GET /api/health` is
  polled once, then it returns HTTP 200 with `readiness: "ready"`, and `logs/backend.log` shows no new
  crash/restart banner since the last recorded one.

## NOTES

- **Operator-performed steps this iteration:** TC-9 (throwaway disposable-DB instance) and TC-10 (deep-basis
  latency re-measurement) both require actions agents cannot take this session (a new process boot; an
  AG-10-class heavy pass). Everything else — the B1 code fix, its unit tests, the small-backfill evidence
  capture (TC-8), and the J-04 sanity check (TC-11) — is agent/QA-performable against the already-running
  services.
- **`TRENDORA_CONFIG`** (`apps/backend/app/config.py:2729-2739`) is the existing mechanism for pointing a
  process at an alternate `config.yaml` whose `database.url` targets a disposable SQLite file — no new
  script needed for TC-9.
- If TC-9's full browser pairing (frontend + throwaway backend on matched alternate ports) proves
  impractical within this session, a backend-only capture (the raw JSON response showing
  `evidence_status="not_yet_computed"`, HTTP 200) plus confirmation that the frontend's existing
  `EmptyState` call site is unconditionally reached for that status is an acceptable documented fallback —
  state which was achieved.
- The B1 fix is a reading of goal text already ruled by the iter-16 evaluator (not a fresh ambiguity this
  iteration introduces), so no new `assumptions.md` entry was logged for it.
- Carried, unrelated: `test_db.py::test_create_all_produces_expected_tables` (pre-existing, no schema
  change this iteration).
- If the latency investigation concludes the residual is a hard, unavoidable contention cost (mirroring
  iter-15's STALLED cold-MISS finding), that is a legitimate outcome to report — do not force a fix that
  isn't there; record the finding plainly in `reports/perf-budgets.md` and let the evaluator route any
  budget-amendment decision to the owner, exactly as iter-15 did.
