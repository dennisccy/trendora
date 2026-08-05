# Goal Iteration 48 — J-05's finalize-tail never terminates; two more unbounded Evidence/Factor-Lab reads bounded

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** ops-hardening
- **Iteration:** 48
- **Mode:** next
- **Depth:** full
- **Full trigger:** 3 — prior iteration's (iter-47) verdict was ESCALATE; full depth is mandatory per
  the binding evaluator recommendation, no exceptions.
- **Frontend Present:** no
- **Target journeys:** J-05, J-07
- **Required-still-passing journeys:** J-01, J-03, J-04, J-06, J-08, J-09 (full regression widen —
  post-ESCALATE; nothing has been verified against the shipped build for two consecutive rounds)
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
    (Owner-amended envelope: `server.memory_cap_mb=8192`, `HOST_GUARD_MEMORY_HIGH=12G` — never
    re-tune these values this iteration.)

## GOAL

Make a historical-day backfill (a date earlier than every already-cached snapshot) actually finish —
its run reaches a real terminal outcome instead of sitting on `running` forever — and bound two more
unbounded whole-cohort reads on the Evidence/Factor-Lab serving path, while re-verifying all eight
Must-have journeys against the current shipped build with the browser-qa/replay lane run LAST.

## BACKGROUND

Iter-47 ended ESCALATE for the second consecutive round: the round's real engineering win (Evidence
page 163s → 0.012s) has no journey-level proof because the browser-qa lane never re-ran after two
in-round fix passes (iter-46's and iter-47's own lesson, now twice-recurring). J-05 ("Aggregates are
precomputed at ingest") has failed FOUR consecutive rounds and is explicitly named by the iter-47
evaluator as "the only remaining product fault on a must-have journey": a backfill of a historical date
earlier than the latest cached membership-timeline date writes its snapshot in ~12s, then the finalize
tail's `_membership_timeline` full recompute (the iter-45-deliberate fallback for this order-dependent
case — the append-forward fast path is NOT generalized to it, per `assumptions.md` iter-45) never lets
the run row leave `status: "running"`. This is item (3) in the iter-47 evaluator's own numbered
next-step order. Item (5)'s first bullet — `samples.py:161`/`:168`, the `_factor_samples` `total`/
`regime` branches that still materialize `_factor_observations`'s full unfiltered population — is a
trivial, mechanical continuation of the already-proven two-pass bound (`decile` branch, iter-47, 5/5
pressure runs) on the SAME already-registered "Membership timeline / research hot-key caches" Data
Contract row, so it rides alongside J-05's fix at no added risk. Item (4) (the Regime Lab's separate,
still-undiagnosed 8192MB-cap hit — deferred 13 times) and the rest of item (5) (shared warm-in-progress
flag, health-poll re-measurement, J-09's background-worker visibility) are deliberately DEFERRED this
round — rule 5 bars bundling two risky/undiagnosed changes, and J-05's fix is already the one
correctness-adjacent, order-dependent change this iteration can safely carry (see `assumptions.md`
iter-48 for the full reasoning). Applying the binding lessons on record: iter-44 (a memory-pressure test
proven by one green run is not proven — run 3-5x), iter-45 (verify the live DB actually contains an
instance of the failure shape before committing — 2011-01-05, J-05's own golden target, is confirmed
absent from `scanner_runs` by the iter-47 evaluator's own DB read), and iter-46/iter-47 (a browser lane
that ran before a later fix pass is void — this iteration's spec makes the full 8-journey pass the LAST
product-code-adjacent event, non-negotiably, for the third round running).

## IN SCOPE

### Backend
- [ ] Diagnose why a historical-gap-insert backfill (a new snapshot date earlier than the latest cached
  `membership_timeline_cache` date) leaves its `data_provider_runs` row at `status: "running"`
  indefinitely even though the snapshot itself writes in ~12s. Add or reuse phase-level timing/heartbeat
  instrumentation across `_refresh_ingest_aggregates`'s finalize-tail steps (coverage/membership-timeline
  refresh, per-date coverage warm, market-phase warm, forward-aggregates warm, drawdown-expectations
  warm, research-hot-key warm) if needed to identify which step(s) actually dominate wall-clock time or
  block outright for this case, before committing to a fix.
- [ ] Fix the identified blocking step(s) so the job reaches a terminal `status` (`ok`/`partial`/`failed`)
  within a bounded, measured time on an idle host (see TC-1), preserving byte-identical
  `entries`/`exits`/`excluded` output from `_membership_timeline` for the new date AND every
  already-cached date (no change to computed values — see TC-2). Do NOT extend the iter-45 append-forward
  incremental fast path to this case (a deliberate design decision preserving order-dependent
  entries/exits correctness, `assumptions.md` iter-45) unless the investigation itself proves a new, safe,
  tested alternative — if it does, log that as a NEW `assumptions.md` entry naming the correctness proof.
- [ ] Bound `_factor_samples`'s `total` and `regime` slice branches (`apps/backend/app/engine/samples.py:161`,
  `:168`), which currently call `_factor_observations` and use/return its full unfiltered population, using
  the SAME two-pass bounded pattern already shipped for the `decile` branch
  (`research._factor_decile_observations`, iter-47) — byte-identical member rows required for the same
  inputs (see TC-5).
- [ ] Add/extend unit + live-drill test coverage for both fixes per TESTING REQUIREMENTS below; the
  existing `test_historical_gap_fill_falls_back_to_full_recompute_not_stale_reuse` correctness test in
  `apps/backend/tests/test_data_manager.py` stays green, unmodified in its assertions.

### Frontend (if applicable)
None anticipated — no new field, no new page, no UI copy change. If the diagnosis in the first bullet
above reveals the finalize tail genuinely needs longer than any reasonable ceiling and the honest fix is
to surface an explicit "still finishing" state on the job card (mirroring the existing heartbeat/
checkpoint convention), that is an allowed, minimal, additive exception — log it as a new `assumptions.md`
entry rather than silently expanding scope.

### New user-facing capability
A historical-day backfill (a date earlier than every already-cached snapshot) reaches a real, honest
outcome — success or a named failure reason — instead of appearing to run forever.

### New information displayed
None new — existing job-card/run-history fields (`status`, `message`, `aggregates_refreshed`) already
convey the outcome; this iteration makes them reach a terminal value for this case, not add a field.

### New user actions
None new.

### UI surface changes
None — no new page/panel/route.

### Product surface delta
`/data`'s job history panel for a historical-gap-insert backfill now shows a terminal outcome instead of
staying on "running" past any reasonable wait; the Factor Lab (`/research/factor-lab`) and Evidence
(`/evidence`) drawdown-expectations panels' `total`/`regime` cohort reads no longer risk a whole-population
memory spike on the serving path.

### Blueprint conformance
`/data` (Data Manager) and `/evidence` / `/research/factor-lab` (Research) — both pre-existing homes per
`blueprint.md`'s Information Architecture; no new page/nav/route. This iteration deepens the ALREADY-
registered "Membership timeline / research hot-key caches" Data Contract row (see `blueprint.md`'s
iter-48 changelog paragraph and the row's own iter-48 note, both already appended this iteration).

### Data-contract additions
None. Same computing modules (`app.engine.data_manager`: `_membership_timeline` /
`_excluded_counts_by_date` / `membership_timeline_cached`; `app.engine.research` / `app.engine.samples`:
`_factor_observations` / `_factor_samples`), same tables (`membership_timeline_cache`,
`event_study_cache`), same serving endpoints (`GET /api/data`, `GET /api/evidence`, plus
`/research/factor-lab`'s samples drill-down for the same functions) — no second producer, no second
endpoint, no schema change.

## OUT OF SCOPE

- The Regime Lab's separate, still-undiagnosed 8192MB-cap hit (`research.py`'s
  `_regime_lab_members_by_horizon`/downstream, iter-33/g, 14th deferral) — a distinct memory
  investigation; bundling it with J-05's correctness-adjacent fix would violate rule 5
  (`assumptions.md` iter-48).
- The shared ingest-vs-request warm-in-progress flag (audit B2) — carried.
- J-09's background-worker visibility gap (iter-47/bi) — J-09 is currently `passing`; not touched this
  round to avoid destabilizing it for a minor, already-ledgered gap.
- Health-poll ≤2s ceiling breach (8/20 over budget while a job was finishing) — re-measure only, as part
  of required-still-passing J-04/J-07 verification; no fix attempted this round.
- Database connection-pool exhaustion handling — carried, unowned this round.
- iter-29/b + the badge wording after a permanently failed warm-up (20th round carried), iter-31/e,
  iter-32/f, iter-35/k, iter-36/n, iter-37/o, iter-37/q, iter-39/u, iter-46/az, iter-46/ba — all carried
  untouched.
- Extending the append-forward incremental fast path to the historical-gap-insert case, UNLESS the
  investigation itself proves a safe, tested alternative (see IN SCOPE note).
- Any change to `server.memory_cap_mb` / `malloc_arena_max` / host-guard cap VALUES (AG-10) — never
  re-tune.
- J-07's `[NEW]` walkthrough capture and J-05's acceptance frames — capture-only, never a round's goal
  (18th/4th round respectively still unrecorded; ride the showcase pipeline, not developer scope).

## DEFINITION OF DONE

- [ ] J-05 passes (or is scored honestly against fresh evidence) via browser-qa: a backfill of a
  historical date earlier than every cached snapshot date reaches a terminal `data_provider_runs.status`
  within the measured bound (TC-1), and `/scanner-runs`/`/data` render the resulting snapshot from
  storage (TC-3).
- [ ] J-07 advances (or is scored honestly): the `samples.py:161`/`:168` bound closes one more named
  unbounded-materialization item against its AG-8 acceptance clause; no new `MemoryError` introduced
  anywhere in this iteration's diff.
- [ ] Required-still-passing journeys J-01, J-03, J-04, J-06, J-08, J-09 replay/verify clean — deterministic
  replay where a golden exists (its script CONTENT checked, not just its PASS row — TC-8), LLM
  browser-qa fallback otherwise.
- [ ] The full 8-journey browser-qa/replay pass is the LAST product-code-adjacent event before this
  iteration is scored (TC-7); if any fix-mode/audit-fix pass changes product code after that pass runs,
  the pass MUST be re-run before closure — this is the THIRD round this exact requirement has been
  written down (iter-46, iter-47, iter-48); do not let it recur a third time.
- [ ] No anti-goal violation introduced; AG-10 caps (`memory_cap_mb=8192`, `malloc_arena_max=2`) unchanged
  and enforced by launch scripts.
- [ ] Unit tests pass: `test_historical_gap_fill_falls_back_to_full_recompute_not_stale_reuse` and the
  full append-forward suite in `test_data_manager.py` stay green, assertions unmodified; new tests from
  TESTING REQUIREMENTS added and green.
- [ ] The `samples.py` `total`/`regime` memory-pressure test runs 5 consecutive times and passes 5/5
  before being called closed (TC-6, binding iter-44 lesson).
- [ ] Dev handoff written at `docs/handoffs/goal-ops-hardening-iter-48-dev.md`.

## TESTING REQUIREMENTS

- Browser: J-05 (all 4 steps, historical-gap case per journey text), J-07 (all 4 steps); required-still-
  passing replay/LLM fallback for J-01, J-03, J-04, J-06, J-08, J-09. Do not start a second data job while
  one is still finishing (iter-47 evaluator's own operational note) — the live drills below run
  sequentially.
- Unit/integration:
  - `data_manager.py`'s historical-gap-insert finalize path: a NEW live/integration test proving the job
    reaches a terminal status within the measured bound (mirrors the existing heavy-ingest pattern in
    `test_start_backend_script.py`), plus a byte-identity test extending
    `test_historical_gap_fill_falls_back_to_full_recompute_not_stale_reuse`'s existing correctness proof
    with the new liveness/termination proof (TC-1, TC-2).
  - `samples.py`'s `total`/`regime` bound: a pinned-reference byte-identity test (mirrors
    `test_research_streaming.py`'s decile-branch reference test) plus a memory-pressure drill extending
    `test_samples_memory_pressure.py`'s existing pattern to the two new branches, run 5 consecutive times
    (TC-5, TC-6).
- Error cases: a historical-gap-insert job that raises a genuine non-memory exception during the finalize
  tail must still leave the run row `failed` with a real, non-blank reason (never silently `running`); a
  `MemoryError` on the same path must be caught per the existing per-item isolation convention and leave
  `aggregates_refreshed` honestly reflecting only what actually completed before the abort.

Test-first contract:

- TC-1: given a DB whose `membership_timeline_cache` row's latest cached date is on or after 2020-01-01,
  when a backfill job ingests exactly one historical date earlier than that cached date (2011-01-05,
  matching J-05's own golden script — confirmed absent from `scanner_runs` by the iter-47 evaluator's own
  DB read), then the job's `data_provider_runs` row reaches a terminal `status` of `ok` (or `partial`/
  `failed` with an honest, non-blank reason) within 20 minutes of the snapshot itself being written —
  never remaining `running` on an otherwise idle, live backend process.
- TC-2: given the TC-1 job completes, then `_membership_timeline`'s output for 2011-01-05 AND every
  previously-cached date is byte-identical to a pinned pre-fix reference computation (no `entries`/
  `exits`/`excluded` value changes for any date).
- TC-3: given the TC-1 job completes, when the user visits `/scanner-runs` and opens the 2011-01-05 run,
  then the leaderboard renders the stored snapshot for that as-of (not a "not yet computed" placeholder).
- TC-4: given the TC-1 job is running, when `GET /api/health` is polled once per second throughout the
  whole finalize tail, then every poll answers HTTP 200 within its existing budget (no frozen or
  unresponsive window).
- TC-5: given `/research/factor-lab` or `/evidence` requests a `total`-slice or `regime`-slice cohort for
  a factor with a large all-history population, when `_factor_samples` resolves that cohort, then the
  returned member rows are byte-identical to the pre-fix `_factor_observations`-based population for the
  same inputs, and process VmPeak during the request stays under the declared 8192 MB `server.memory_cap_mb`
  cap with the margin recorded in `reports/perf-budgets.md`.
- TC-6: given the TC-5 bound, when the extended memory-pressure drill for the `total`/`regime` branches
  runs 5 consecutive times, then it passes 5/5 with no flake (binding iter-44 lesson — a single green run
  is not proof).
- TC-7: given all product code for this iteration has landed, when the full 8-journey browser-qa/replay
  pass runs, then it is the LAST product-code-adjacent event before scoring — the results-file mtime is
  checked against the newest product-code mtime (binding iter-47 lesson) and confirmed no code changed
  after the pass ran; if a fix/audit-fix pass changes code afterward, the pass is re-run before the
  iteration closes.
- TC-8: given each Required-still-passing journey's golden replay script, when its result is scored, then
  the script's own JSON content (not merely its PASS/FAIL verdict) is read and confirmed to assert against
  that run's own new row/testid rather than page-wide text a persisted history panel could already satisfy
  (binding iter-46/iter-47 lesson).
- TC-9: given the J-05 golden script/replay assertion, when it runs against a job that produced ZERO real
  work (a no-op job over an already-snapshotted date), then it FAILS — i.e. the script asserts positive
  evidence of new work (a non-zero snapshot/date count on the job card), never text a pre-existing history
  row could already satisfy (the auditor's already-written fix, iter-47 next-step item 2).

## NOTES

- Lessons applied (see `runs/goal-session-ops-hardening/state/lessons.md`): iter-44 (a memory-pressure
  guard proven by one green run is not proven — run 3-5x, TC-6); iter-45 (verify the live data basis
  actually contains an instance of the failure shape before committing an iteration to a fix — 2011-01-05
  confirmed unsnapshotted, TC-1); iter-46 (a golden script asserting page-wide text on a page with
  persistent history is a null test — TC-8/TC-9); iter-47 (a QA-fix/audit-fix pass landing after
  browser-qa silently voids the whole lane, and a rebuilt golden that is never executed buys nothing —
  TC-7); iter-40/iter-42 (a memory claim must measure a whole job, not a function — TC-5's VmPeak
  measurement is end-to-end, not an isolated function call).
- `assumptions.md` iter-48 records the decompose-time call to bundle J-05's fix with the trivial
  `samples.py:161`/`:168` bound while deferring the Regime Lab fix and the rest of item (5) — read it for
  the full reasoning if this iteration's scope is questioned.
- `blueprint.md` was updated this iteration (an iter-48 changelog paragraph plus a note appended to the
  "Membership timeline / research hot-key caches" Data Contract row) — no Information Architecture change,
  no new Data Contract value.
- OWNER: nothing in this iteration requires an owner decision.
