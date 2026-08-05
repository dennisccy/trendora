# Goal Iteration 49 — Bound the two finalize-tail phases still blocking J-05's own TC-1 termination bound

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** ops-hardening
- **Iteration:** 49
- **Mode:** next
- **Depth:** full
- **Full trigger:** 3 — prior iteration's (iter-48) verdict was ESCALATE; full depth is mandatory per
  the binding evaluator recommendation, no exceptions.
- **Frontend Present:** no
- **Target journeys:** J-05, J-07
- **Required-still-passing journeys:** J-01, J-03, J-04, J-06, J-08, J-09 (full regression widen —
  this is the FOURTH consecutive ESCALATE round; per audit F3, J-04 has produced zero executed lane
  rows for 2 consecutive rounds and must actually run this time, not `DEFERRED-BUDGET` again)
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
    are a physical constraint of the current host, not a performance budget to optimize away.
    (Owner-amended envelope: `server.memory_cap_mb=8192`, `HOST_GUARD_MEMORY_HIGH=12G` — never
    re-tune these values this iteration.) *(critical)*

## GOAL

Make a historical-gap-insert backfill's ENTIRE finalize tail — not just the phase iter-48 already fixed
— reach a terminal `data_provider_runs.status` within J-05's own TC-1 20-minute (1,200 s) bound,
reliably, across repeated runs, by bounding the two remaining finalize-tail phases (`forward_aggregates_warm`,
`drawdown_expectations_warm`) the iter-48 audit named and explicitly scoped to this iteration.

## BACKGROUND

Iter-48 ended ESCALATE for the fourth consecutive round. Its own fix — closing the O(dates × pool)
`resolve_with_reasons` resolver storm in `coverage_membership_timeline_refresh` — is genuinely proven,
live, three times (9.18 s / 24.10 s / 21.01 s across three different target dates, down from an
extrapolated well-over-an-hour). But the iter-48 audit (finding B1, CRITICAL, "cannot be fixed in this
audit") and the iter-48 dev handoff's own Known Issues both name the SAME residual, in the SAME words:
the job's TOTAL wall time still misses TC-1's 1,200 s bound because two OTHER, pre-existing finalize-tail
phases every ingest already pays are themselves unbounded in wall-clock time. Measured directly from
`logs/backend.log` across three independent live runs (`reports/perf-budgets.md` Item R, Addenda 1-2):
`forward_aggregates_warm` took 102.48 s, then 153.07 s, then **1,334.13 s (22 min 14 s) — alone over
TC-1's entire budget** — and `drawdown_expectations_warm` took 667.30 s, then was still running past
950 s+ in a second run, then never even logged completion in the third (job id 308, still
`status: "running"`, `finished_at: NULL` in the live committed DB as of the iter-48 audit). The audit's
own words: *"bounding two unrelated finalize-tail phases is explicitly out of this iteration's scope and
is a full iteration of work"* — the dev handoff is more direct: *"that is iter-49 work, not an
audit-fix."* This iteration is that work. Binding lesson applied (iter-48, first entry): a phase whose
cost swings 13x across three samples cannot be characterised from two of them — every fix this iteration
ships must be proven across **at least 3** independent live runs, not 1-2, mirroring the same discipline
iter-44 established for memory-pressure flakiness and this session has now twice needed for wall-clock
variance too. Also carried: audit finding F3 — the browser-qa lane produced **zero executed rows** for
J-04, J-05, and J-07 across the last two rounds combined (DEFERRED-BUDGET / missing / FAIL-before-terminal
respectively); this iteration's DEFINITION OF DONE makes producing a real row for all three non-negotiable,
not merely "TC-7 sequencing holds" (which iter-46/47/48 each satisfied while still failing on row
completeness).

## IN SCOPE

### Backend
- [ ] Extend the existing whole-phase `"J-05 finalize-tail phase timing"` log convention
  (`data_manager.py:3965-4004` for `forward_aggregates_warm`, `:4091-4130` for
  `drawdown_expectations_warm`) with per-horizon and per-claim sub-phase timing respectively, so a slow
  run's cost is attributable to a SPECIFIC horizon (of `cfg.walk_forward.horizons = [1, 5, 10, 20, 60]`)
  or a SPECIFIC ledger claim (of the 7 currently on record) — not just "the loop as a whole," which is
  all last iteration's coarser instrumentation could name.
- [ ] Diagnose the actual driver of the demonstrated variance before committing to a fix: rule out
  concurrent host load/contention during measurement (the iter-6 "measurement-contamination" precedent —
  check `logs/hwmon/hwmon.csv` and whether another heavy process/test suite ran during each sampled
  window) versus genuine per-call cost growth against the live DB's accumulated `forward_returns`
  (344,334+ rows and growing every iteration this session backfills more history) /
  `scanner_results` volume, and versus lock/single-flight contention in
  `forward_aggregates_ingest_cached`'s existing de-dup guard (iter-15).
- [ ] Bound whichever mechanism the diagnosis identifies as the actual cost driver, for BOTH
  `forward_aggregates_warm` and `drawdown_expectations_warm`, so a historical-gap-insert backfill's ENTIRE
  finalize tail (every phase combined) reaches a terminal `data_provider_runs.status` within TC-1's
  existing 1,200 s bound on an otherwise-idle host, across at least 3 independent live runs (see
  TESTING REQUIREMENTS). `compute_forward_aggregates` / `forward_aggregates_ingest_cached` and
  `compute_drawdown_expectations` / `compute_drawdown_expectations_cached` remain the SAME sole canonical
  producers (Data Contract row below) — byte-identical output required for every horizon and every claim
  against a pinned pre-fix reference oracle; no second producer, no schema change.
- [ ] Re-run the existing opt-in live test, `test_start_backend_historical_gap_insert_reaches_terminal_status_within_bound`
  (`apps/backend/tests/test_start_backend_script.py`, `TRENDORA_RUN_HEAVY_INGEST_TEST=1`, currently
  `xfail(strict=False)` per iter-48's audit-fix): if this iteration's fix makes it genuinely pass, remove
  the `xfail` marker; if it still cannot be made to pass reliably, leave it `xfail` with an accurate,
  updated reason naming whatever cost driver remains open — never loosen its assertion to make it pass.
- [ ] Add/extend unit + live-drill test coverage per TESTING REQUIREMENTS below. The iter-45
  append-forward suite and the iter-48 gap-insert reuse branch (`data_manager.py:891-917`,
  `_membership_timeline_incremental`/`append_forward` gating) stay byte-for-byte untouched — **Do not
  redo**, already correct and mutation-proven (audit T1).

### Frontend (if applicable)
None. This iteration is backend-only (`Frontend Present: no`). Extending the J-05 golden replay script
(`journey-scripts/J-05.json`) to directly prove TC-1's full 1,200 s termination was investigated and
found infeasible within the existing replay-lane infrastructure — `demo_runner.py`'s per-step timeout is
hard-capped at 20,000 ms regardless of a script's own `timeout_ms`
(`scripts/automation/lib/demo_runner.py:1267`/`1349`) — so TC-1's proof continues to run through the
live/integration test + manual drill pattern iter-48 already established, not the browser replay lane.

### New user-facing capability
A historical-day backfill (any date earlier than the latest cached snapshot) reaches a genuine terminal
outcome — not merely an early snapshot write — within the same ~20-minute window already advertised to
the operator, reliably across repeated runs, instead of appearing to finish and then silently continuing
to run for 20+ more minutes.

### New information displayed
None new — existing job-card/run-history fields (`status`, `message`, `aggregates_refreshed`) already
convey the outcome; this iteration makes them reach a terminal value reliably within budget, not add a
field.

### New user actions
None new.

### UI surface changes
None — no new page/panel/route.

### Product surface delta
`/data`'s job history panel for a historical-gap-insert backfill (and every OTHER ingest — both warm
loops are unconditional, not gated on `new_snapshot_dates`) now reaches a terminal status within the
committed 20-minute bound reliably, not only on a lucky run.

### Blueprint conformance
`/data` (Data Manager), `/backtest` and `/evidence` (Research/Evidence — `forward_aggregates` and
`drawdown_expectations` both feed those pages) — all pre-existing homes per `blueprint.md`'s Information
Architecture; no new page/nav/route.

### Data-contract additions
None. Deepens the ALREADY-registered "Membership timeline / research hot-key caches" Data Contract row —
SAME computing modules (`app.engine.forward_testing`: `compute_forward_aggregates` /
`forward_aggregates_ingest_cached`, `compute_drawdown_expectations` /
`compute_drawdown_expectations_cached`), SAME tables (`ForwardAggregateCache`, `event_study_cache`), SAME
serving endpoints (`GET /api/backtest`, `GET /api/evidence`, the ingest finalize warm) — no second
producer, no second endpoint, no schema change.

## OUT OF SCOPE

- The Regime Lab's separate, still-undiagnosed 8192MB-cap hit (`research.py`'s
  `_regime_lab_members_by_horizon`/downstream, iter-33/g) — a distinct memory investigation, unrelated to
  this iteration's wall-clock bound; bundling it would violate rule 5 (one risky change per iteration).
- `_membership_bars_are_forward_only`'s compensating-removal weakness (audit B3, iter-48) — a pre-existing
  correctness edge case that needs a real manifest/checksum design decision, not exercised by any live
  code path today; carried.
- The golden's page-wide-text scoping gap (audit F2, iter-48) — needs a dedicated frontend testid on the
  job-card snapshot count, i.e. a frontend change this iteration deliberately excludes (`Frontend Present: no`).
- The shared ingest-vs-request warm-in-progress flag — carried, unowned this round.
- J-09's background-worker visibility gap — carried; J-09 is currently `passing`, not touched to avoid
  destabilizing it for a minor, already-ledgered gap.
- Health-poll ≤2 s ceiling breach re-measurement — folded into required-still-passing J-04/J-06/J-07
  verification; no fix attempted this round.
- Any change to `server.memory_cap_mb` / `malloc_arena_max` / host-guard cap VALUES (AG-10) — never
  re-tune.
- iter-29/b + the badge wording after a permanently failed warm-up, iter-31/e, iter-32/f, iter-35/k,
  iter-36/n, iter-37/o, iter-37/q, iter-39/u, iter-46/az, iter-46/ba, iter-47/bd, iter-47/bf, iter-47/bi —
  all carried untouched.
- J-07's `[NEW]` walkthrough capture and J-05's acceptance frames — capture-only, never a round's goal;
  ride the showcase pipeline, not developer scope.

## DEFINITION OF DONE

- [ ] J-05 passes via browser-qa/live evidence: a historical-gap-insert backfill reaches a terminal
  `data_provider_runs.status` within TC-1's 1,200 s bound, proven across ≥3 independent live runs; the
  resulting snapshot renders from storage on `/scanner-runs`/`/data`.
- [ ] J-07 advances/passes via browser-qa/live evidence: `GET /api/health` answers HTTP 200 every poll
  throughout the ENTIRE finalize tail across the same drills, and process VmPeak stays under the declared
  `server.memory_cap_mb=8192` cap with its margin recorded.
- [ ] Required-still-passing journeys J-01, J-03, J-04, J-06, J-08, J-09 each produce a real executed
  lane row this round (deterministic replay where a golden exists, its script CONTENT checked not just
  its PASS row; LLM browser-qa fallback otherwise) — none may end `DEFERRED-BUDGET` or missing.
- [ ] TC-7 holds on BOTH axes this time — sequencing (the full 8-journey pass is the LAST
  product-code-adjacent event) AND row completeness (every target/required journey has an executed row) —
  the fourth consecutive iteration this exact requirement is written down; the first three each satisfied
  sequencing while still failing row completeness (audit F3).
- [ ] No anti-goal violation introduced; AG-10 caps (`memory_cap_mb=8192`, `malloc_arena_max=2`) unchanged
  and enforced by launch scripts.
- [ ] Unit tests pass: the existing gap-insert/append-forward suite stays green with assertions
  unmodified; new tests from TESTING REQUIREMENTS added and green.
- [ ] Dev handoff written at `docs/handoffs/goal-ops-hardening-iter-49-dev.md`.

## TESTING REQUIREMENTS

- Browser: J-05 (all 4 steps, historical-gap case — reuse the existing `journey-scripts/J-05.json` target
  `2012-01-05` unless this iteration's own live drills already consume it, in which case rotate to a
  freshly-confirmed-unsnapshotted date and log the rotation per the iter-46 lesson), J-07 (all 4 steps);
  required-still-passing replay/LLM fallback for J-01, J-03, J-04, J-06, J-08, J-09. Do not start a second
  data job while one is still finishing.
- Unit/integration: per-horizon/per-claim sub-phase timing tests; the un-xfailed (or honestly-still-xfailed)
  termination test; a pinned-reference byte-identity test for both `forward_aggregates` (every configured
  horizon) and `drawdown_expectations` (every ledger claim) against the fix.
- Error cases: a genuine exception (memory or non-memory) raised inside either newly-bounded loop is
  caught by the existing per-item isolation convention (log + continue for a generic exception; stop the
  loop + release memory for `MemoryError`) — `aggregates_refreshed` stays honest, reflecting only what
  actually completed before any abort; the finalize hook itself never raises, unchanged.

Test-first contract:

- TC-1: given a DB whose latest cached `membership_timeline_cache` date is on/after 2020-01-01 (the SAME
  live committed DB, shared `_BarCache` attached), when a backfill ingests exactly one historical date
  earlier than that cached date, then the job's `data_provider_runs.status` reaches a terminal value
  (`ok`/`partial`/`failed` with an honest, non-blank reason) within 1,200 s of the snapshot itself being
  written, on ≥3 independent live runs on an otherwise-idle host — not 1-2 (binding iter-44/iter-48
  lesson).
- TC-2: given each of the ≥3 TC-1 runs, then the per-run phase-timing log names, for BOTH
  `forward_aggregates_warm` and `drawdown_expectations_warm`, which SPECIFIC horizon/claim consumed the
  largest share of that phase's own wall time — not just which phase.
- TC-3: given a TC-1 run completes, then `forward_aggregates_ingest_cached`'s output for every configured
  horizon (1, 5, 10, 20, 60) and `compute_drawdown_expectations_cached`'s output for every ledger claim
  are byte-identical to a pinned pre-fix reference computation for the same inputs.
- TC-4: given a TC-1 job is running, when `GET /api/health` is polled once per second throughout the
  ENTIRE finalize tail (every phase, not only the newly-bounded ones), then every poll answers HTTP 200
  within its existing budget — no frozen or unresponsive window.
- TC-5: given the same TC-1 drill (J-07 step 1), then process VmPeak stays under the declared
  `server.memory_cap_mb=8192` cap, with the margin recorded in `reports/perf-budgets.md`.
- TC-6: given the existing opt-in `test_start_backend_historical_gap_insert_reaches_terminal_status_within_bound`
  test, when it is re-run against this iteration's fix, then it either passes with its `xfail` marker
  removed, or — if the driver genuinely cannot be bounded reliably this iteration — stays honestly
  `xfail` with an accurate, updated reason naming the still-open cost driver (never a loosened assertion).
- TC-7: given all product code for this iteration has landed, when the full 8-journey browser-qa/replay
  pass runs, then (a) it is the LAST product-code-adjacent event before scoring (results-file mtime
  checked against the newest product-code mtime; any later fix/audit-fix pass forces a re-run before
  closure) AND (b) every one of J-01, J-03, J-04, J-05, J-06, J-07, J-08, J-09 has at least one executed
  row in the merged results — not merely "sequencing held while three journeys had zero rows," the exact
  gap audit F3 found in iter-48.
- TC-8: given each Required-still-passing journey's golden replay script, when its result is scored, then
  the script's own JSON content (not merely its PASS/FAIL verdict) is read and confirmed to assert against
  that run's own new row/testid rather than page-wide text a persisted history panel could already
  satisfy.
- TC-9: given J-04's own steps (boot-to-health timing, kill/restart, interrupted-job detection), when this
  iteration's browser-qa lane runs, then it executes a real row for J-04 — not `DEFERRED-BUDGET` or a
  missing/skipped outcome (binding audit F3 finding: J-04 has had zero executed rows for 2 consecutive
  rounds).
- TC-10: given this iteration's diff, when it is compared against the pre-iteration snapshot, then `git
  diff` over `config.yaml`, `host-guard.env`, `scripts/start-backend.sh`, and `scripts/dev.sh` is EMPTY,
  and every launch banner still reports `memory_cap_mb=8192`/`malloc_arena_max=2` unchanged (AG-10 —
  never re-tune).
- TC-11: given a genuine non-memory exception is injected inside either newly-bounded loop's own new
  code, when it is raised, then the run row still reaches its own terminal status (never silently
  `running`) with `aggregates_refreshed` honestly omitting only the affected category; given a
  `MemoryError` is injected at the same site, then the existing per-item isolation convention (stop the
  loop, `_release_process_memory()`, honest partial reporting) catches it identically.

## NOTES

- Lessons applied (see `runs/goal-session-ops-hardening/state/lessons.md`): iter-44 (a memory-pressure/
  variance claim proven by one green run is not proven — run ≥3, TC-1/TC-6); iter-48 first entry (a
  finalize-tail phase whose cost swings 13x across three samples cannot be characterised from two of
  them — TC-2's per-horizon/per-claim attribution exists specifically to avoid repeating this); iter-48
  second entry (a journey's PASS must rest on a row the work itself caused, not a script's content or
  verdict alone — TC-1/TC-3/TC-8); iter-46/47 (a QA-fix/audit-fix pass landing after browser-qa silently
  voids the whole lane — TC-7(a)); iter-6 (a concurrent pytest/heavy-process run can contaminate a live
  timing measurement — factored into this iteration's own diagnosis step).
- `reports/perf-budgets.md` Item R (Addenda 1-2) and `docs/handoffs/goal-ops-hardening-iter-48-dev.md`
  Known Issues + `docs/handoffs/goal-ops-hardening-iter-48-audit.md` findings B1/B2 are the primary
  evidence base for this iteration's scope — read them before starting the diagnosis; they already
  contain three independent live phase-timing tables (834 s / >1200 s / >1200 s totals) this iteration
  should not re-derive from scratch.
- No new `assumptions.md` entry this iteration — the scope call (bound both phases together as ONE risky
  action; defer the Regime Lab, B3, and F2) directly continues the precedent iter-48's own decomposer
  already established and logged (`assumptions.md`, "iter-48 — goal-decomposer"); nothing new was left
  ambiguous by `docs/goal.md` here.
- `blueprint.md` updated this iteration: an iter-49 changelog paragraph plus a note appended to the
  "Membership timeline / research hot-key caches" Data Contract row — no Information Architecture change,
  no new Data Contract value.
- OWNER: nothing in this iteration requires an owner decision.
