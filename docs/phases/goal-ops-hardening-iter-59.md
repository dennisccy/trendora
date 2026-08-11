# Goal Iteration 59 — Close J-05's last step; profile-then-bound the Regime Lab's memory hazard for J-07

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** ops-hardening
- **Iteration:** 59
- **Mode:** next
- **Depth:** full
- **Full trigger:** 3 — prior evaluator verdict (iter-58) was ESCALATE, which mandates full depth this
  iteration, no exceptions. (The ESCALATE's own third clause also independently applies here: J-05 and
  J-07 both carry a `[NEW]`-flagged walkthrough clause and the demo/walkthrough lane runs only at full
  depth, so neither can close in a lean round regardless of the ESCALATE mandate.)
- **Frontend Present:** yes (conditional — see Data-contract additions)
- **Target journeys:** J-05, J-07
- **Required-still-passing journeys:** J-01, J-03, J-04, J-06, J-08, J-09 (full regression — widened
  because the prior evaluator verdict was ESCALATE, per this session's own "widen after ESCALATE" rule)
- **Anti-goal reminders:**
  - **AG-1:** A score, ranking, or "edge" MUST NOT be presented as proven/confident unless it is backed
    by a **passing certified-claim entry** in the evidence ledger (out-of-sample, control-beating).
    Unbacked values MUST render a "not yet proven" state. *(critical)*
  - **AG-2 — Decision-quality only:** never present return promises, price targets, "buy/sell" signals,
    or alpha claims; never place or simulate orders. *(critical)*
  - **AG-3:** A journey passes ONLY if the **displayed numbers are correct** — they match the engine's
    computation for the same as-of date — not merely that the page renders. *(critical)*
  - **AG-4 — No overfit edges:** any pattern surfaced as "proven" must have survived the referee (sealed
    out-of-sample holdout + controls + multiple-testing correction), never in-sample fit alone.
    *(critical)*
  - **AG-5 — Preserve determinism and no-lookahead:** scoring uses bars ≤ as-of; forward returns use
    bars > as-of; never introduce lookahead anywhere. *(critical)*
  - **AG-6:** No iteration ships if its evidence-derived claims (if any) lack a passing referee verdict
    from the post-decompose gate. *(critical)*
  - **AG-7:** No hard-coded credentials, API keys, or tokens in source files. *(critical)*
  - **AG-8 — Resilience to data-shape and data-scale change:** widening the data basis (new nulls,
    broader pools, deeper history) must never crash an existing page or exhaust a service's memory —
    every existing consumer of a widened field is re-validated, the UI degrades gracefully (contained
    error boundary, honest "—"/NA placeholder, never a blank application-error page), and unbounded
    whole-table ORM loads are forbidden on the deep basis. *(critical)*
  - **AG-9 — Offline-deterministic ingest:** ingest jobs (fetch/backfill/rebuild) run only against the
    committed seed / local provider fixtures — no live external network calls or paid data services may
    be introduced without an explicit goal.md amendment. *(critical)*
  - **AG-10 — Host resource ceiling (hardware protection):** heavy compute — backfills, full-universe
    rebuilds, measurement passes, load drills, test-suite bursts — MUST be launched only via the project
    launch scripts (`scripts/dev.sh` / `scripts/start-backend.sh`), and those scripts MUST apply the host
    caps declared in `project-extensions/host-guard/host-guard.env` whenever that file is present
    (CPU-affinity mask, BLAS/OMP thread caps, `memory_cap_mb`, `malloc_arena_max`). Never remove, weaken,
    or bypass these caps: stripping a HOST-GUARD marked block from a launch script is a REGRESSION
    regardless of test outcomes. The ceilings are a physical constraint of the current host, not a
    performance budget to optimize away. Owner amendment (2026-07-31): `server.memory_cap_mb` = 8192,
    `HOST_GUARD_MEMORY_HIGH` = 12G — this iteration must not touch these values, only consume less inside
    them. *(critical)*

## GOAL

Execute J-05's one remaining unexecuted acceptance step (a real backend restart followed by a cold
`/data` load that must still render coverage from storage, fast) and close the specific memory-safety gap
the last two ESCALATEs have named as "what keeps J-07 open" — a Regime Lab read that can raise an
uncaught `MemoryError` when a concurrent heavy warm is already near the declared 8192 MB ceiling — so
both journeys can move off `partial` for the first time this session.

## BACKGROUND

Depth is **full**, mandated: the prior verdict was ESCALATE (Full trigger 3), and the two open journeys
each carry a `[NEW]`-flagged walkthrough clause that only the full-depth demo lane can satisfy — the
iter-58 evaluator states this structurally ("neither journey can EVER close in a lean round"). Six of
eight journeys are `passing`; J-05 and J-07 are `partial` and have been the session's only open journeys
for many rounds. The iter-58 evaluator, verifying everything itself rather than trusting a lane report,
found: (1) J-05's remaining gap is narrow — every other acceptance clause is built and evaluator-confirmed
(binding "Do not redo"); only step 3 (restart + cold coverage check) was never executed, because the
browser-QA agent may not restart the app and the developer, who restarts it routinely, was never assigned
the step; (2) J-07's warm stalled at 1/5 horizons with VmPeak landing **exactly** on the declared 8192 MB
ceiling, from a concurrent `/api/research/regime-lab` request whose traceback names
`_regime_lab_members_by_horizon` — a function this session has never profiled or bounded, despite nine
rounds of owner questions about a larger architectural fix. Two lessons apply directly to this iteration's
own conduct: (iter-53) an ordering/discipline property that keeps breaking under exhortation must be
encoded as a binding DoD/TC line, not restated as a reminder — applied below to both the drill-reporting
requirement (iter-57/iter-58's repeated "segment boundaries hide failures" defect) and the browser/replay
lane's ordering (iter-52/53's TC-9 rule); (iter-58) hashing evidence for distinctness does not prove it
shows anything — screenshots must be opened, not just hashed, before being cited.

`_regime_lab_members_by_horizon`'s own docstring already documents its DB reads as bounded
(column-projected, `yield_per`-streamed — confirmed by direct code read, `apps/backend/app/engine/
research.py:4245-4317`); what iter-58's incident data implicates is the RESULT `compute_regime_lab`
retains across **all** configured horizons at once (`pools = {h: [...] for h in horizons}`,
`research.py:4399`) — the same shape this session already bound for `_all_factor_observations_by_horizon`
and `compute_forward_aggregates`'s per-horizon loop (iter-46/49/50/51, same Data Contract row). This
iteration applies that same proven isolate-and-continue pattern here rather than opening a new diagnosis
effort — see `assumptions.md` (iter-59) for the "measure and bound in one round" reading and its stated
cost if that reading is wrong.

## IN SCOPE

### Backend
- [ ] `app.engine.research`: profile `compute_regime_lab`'s peak memory footprint under a concurrent
  forward-aggregate-warm load (measure first — this session's own binding discipline), confirming or
  correcting the all-horizons-retained-`pools` diagnosis above, then bound it so a horizon that cannot
  complete under memory pressure degrades **only that horizon** (isolate-and-continue) instead of an
  uncaught `MemoryError` reaching `GET /api/research/regime-lab` as a 500. Byte-identical output required
  for every horizon that DOES complete, against a pinned pre-fix reference, for every configured horizon
  with and without `as_of`.
- [ ] Same module, CONDITIONAL on the profile confirming a partial-degrade signal is needed: add
  `by_horizon[].status: "unavailable"` and a whole-response `regime_lab_status: "unavailable"` to
  `compute_regime_lab`'s existing payload — mirrors the already-registered Factor Lab sibling fields
  (`by_horizon[].status`/`factors_status`, same row, iter-50/iter-51). Same computing module, same
  endpoint, no second producer, no new table.
- [ ] Developer executes J-05 step 3 directly (assigned per the iter-58 evaluator's explicit
  recommendation — the browser-QA agent may not restart the app): after a completed backfill, restart the
  backend via `scripts/start-backend.sh` (host-guard caps applied, unchanged), then confirm `/data` cold
  renders the persisted coverage payload within its committed budget with no `daily_prices`-scale
  prefill. This exercises already-built code (coverage payload persisted at ingest, cold-serving path
  built + evaluator-confirmed iter-8/iter-9 — binding "Do not redo"); no code change is anticipated. If
  the restart surfaces a genuine defect (not merely an un-executed step), it is diagnosed and filed as a
  note for iter-60 rather than force-fixed alongside this iteration's one risky product-code action (rule
  5 — the regime-lab bound above is that action).
- [ ] Re-verify `journey-scripts/J-05.json`'s reserved target date (2010-11-05) has 0 `scanner_runs` rows
  immediately before any lane uses it (live-verified 0 rows as of this spec's authoring, 2026-08-10);
  rotate in the same commit if a prior lane already consumed it. Use a **different**, already-ingested
  date for the developer's own step-3 restart-and-cold-check exercise so it never consumes the golden's
  reserved precondition date (iter-55 single-use-fixture lesson).
- [ ] Every latency/health-poll drill this iteration produces (the J-07 warm+concurrent-request
  measurement; any timing taken around the J-05 restart) publishes its raw log's line count (`wc -l`),
  its single slowest answer (value + timestamp), and a measurement window bounded by the job's own logged
  OPEN/CLOSED markers — reconciled against the raw log before any "zero failures"/"N polls" claim is
  written to `reports/perf-budgets.md`, the dev handoff, or `status.json` (iter-57/iter-58 lesson, now a
  binding DoD item rather than a reminder).
- [ ] If the coherence-auditor (full-depth lane) finds a defect requiring a further code change AFTER the
  8-journey browser/replay lane has already run, it is filed as a written note for iteration 60 rather
  than applied as a code-changing audit-fix inside this dispatch — preserves the lane's own evidence for
  the tree it actually measured (iter-52/53 TC-9 ordering rule, binding again this iteration).

### Frontend
- [ ] `/research/regime-lab` (`apps/frontend/app/research/regime-lab/page.tsx`): CONDITIONAL — only if
  the backend ships the `by_horizon[].status`/`regime_lab_status` degrade markers above, render an
  honest, contained "temporarily unavailable" placeholder for the affected horizon column(s) only — never
  a blank page, never a fabricated number. If the profile finds no partial-degrade signal is needed, this
  item does not apply and the developer records that in the dev handoff.

### New user-facing capability
None new. This closes gaps in behavior J-05 and J-07 already promise (storage-served coverage after a
restart; a service that survives its own memory ceiling), not new capability.

### New information displayed
CONDITIONAL: an honest per-horizon "temporarily unavailable" marker on `/research/regime-lab`, only if
shipped (see Data-contract additions) — mirrors an existing pattern already on the Factor Lab, not a new
kind of information for the product.

### New user actions
None.

### UI surface changes
`/research/regime-lab` (conditional degrade-state rendering only). No new page or route.

### Product surface delta
A cold-restarted backend must keep serving `/data`'s coverage panel from storage within budget (already
built; this iteration is its first live execution). A concurrent Regime Lab read must never raise an
uncaught `MemoryError` while a heavy warm is near the declared memory ceiling — it must degrade honestly,
horizon by horizon, if it cannot complete.

### Blueprint conformance
J-05: global readiness badge (top bar, every page) + `/data` (Data Manager) — unchanged home, per
`blueprint.md`'s "Feature / journey homes" table. J-07: global readiness badge + `/research/*` /
`/backtest` — unchanged home, same table. No new page, route, or nav entry.

### Data-contract additions
CONDITIONAL, registered in `blueprint.md`'s Data Contract row "Membership timeline / research hot-key
caches" (`[TARGET, iter-59 building]` tag added this iteration): `by_horizon[].status: "unavailable"|
absent` and `regime_lab_status: "unavailable"|absent` on the existing `compute_regime_lab` payload —
computed by the SAME `app.engine.research.compute_regime_lab`, served by the SAME
`GET /api/research/regime-lab` endpoint, no second producer, no new table. Ships ONLY if the developer's
own profiling pass (done first, inside this dispatch) finds the bound needs a partial-degrade signal; if
not, no field ships and the `[TARGET]` tag is removed with "no field added" recorded in the dev handoff.
No other new displayed value this iteration.

## OUT OF SCOPE

- Moving heavy compute into its own process (owner decision, asked 9 rounds running — human-blocked,
  rule 6).
- Whether the twenty-minute finalize budget applies while the app is also serving live traffic (owner
  decision — human-blocked, rule 6).
- The Regime Lab's own broader UI/feature backlog (iter-33/g, deferred 24 times) beyond the specific
  conditional degrade-marker rendering above.
- Re-measuring `/api/regime-history`'s 1.2-3.0s reading on a quiet host — backlog, not gating either
  target journey this round.
- `TI-1`/`TI-2` (`docs/test-infra-tickets.md`) — filed test-infrastructure tickets, outside this
  dispatch's budget.
- The "failed calculation records an empty `reason`" item and the full CARRIED list (iter-29/b, iter-31/e,
  iter-32/f, iter-35/k, iter-36/n, iter-37/o, iter-37/q, iter-39/u, iter-46/az, iter-46/ba, iter-47/bd,
  iter-47/bf, iter-47/bi, iter-48/bj, iter-57/f, iter-57/l) — untouched, carried per the evaluator's own
  list.
- Any live-fetch drill trigger (AG-9): all ingest exercised this iteration (dev drills, QA verification)
  uses Backfill against the committed seed only — never the "Fetch real EOD prices" live-provider button
  (binding process rule, assumptions.md iter-57).

## DEFINITION OF DONE

- [ ] J-05 passes via browser-qa-agent — all 4 acceptance steps executed, including step 3 (cold-restart
  coverage rendering from storage).
- [ ] J-07 passes via browser-qa-agent — all 4 acceptance steps executed: full-horizon warm with
  per-second health polling (0 non-200, no frozen window); VmPeak margin under 8192 MB recorded; an
  induced-pressure abort stays wedge-free with the SAME process still serving `/api/health` and previously
  cached reads.
- [ ] Required-still-passing journeys (J-01, J-03, J-04, J-06, J-08, J-09) remain green — deterministic
  replay + LLM fallback, full regression this iteration.
- [ ] No anti-goal violation introduced — AG-8/AG-9/AG-10 explicitly re-verified with evidence (not
  assumed); AG-7 scan clean.
- [ ] `compute_regime_lab`'s bounded implementation is byte-identical to the pinned pre-fix reference for
  every horizon that completes, proven by a fixture-backed equality test.
- [ ] Every drill this iteration produces publishes raw log line count, slowest answer (value +
  timestamp), and a job-marker-bounded measurement window before any "zero failures" claim is written.
- [ ] The full 8-journey browser/replay lane runs LAST, after all code (including any audit-fix) lands;
  any post-lane audit finding needing a further code change is filed as a note for iteration 60, not
  applied inside this dispatch.
- [ ] A `[NEW]`-flagged walkthrough for J-05 and J-07 is recorded via `demo.sh ops-hardening
  --session-live`, and every captured frame is opened (not merely hashed for distinctness) before being
  cited as evidence.
- [ ] Unit tests pass; no regressions.
- [ ] Dev handoff written at `docs/handoffs/goal-ops-hardening-iter-59-dev.md`.

## TESTING REQUIREMENTS

- Browser: J-05 (all 4 steps, especially step 3), J-07 (all 4 steps). Regression smoke: J-01, J-03, J-04,
  J-06, J-08, J-09 (full set — widened per the post-ESCALATE rule).
- Unit/integration: byte-identity fixture test for `compute_regime_lab`'s bounded implementation vs. a
  pinned pre-fix reference, across every configured horizon × {`as_of` scoped, unscoped}. A
  `MemoryError`-injection test for the bounded path, mirroring this session's existing
  `spawned_backend_fault_injected` / per-item isolate-and-continue test pattern.
- Error cases: an uncaught `MemoryError` inside `compute_regime_lab` must never reach FastAPI as a raw
  500 — it must degrade to an honest per-horizon marker (if shipped) or an already-established generic
  degrade response. A killed (`kill -9`, no clean shutdown) backend followed by a
  `scripts/start-backend.sh` restart must never re-trigger a whole-table `daily_prices` prefill on `/data`
  load.

Test-first contract:

- TC-1: given the backend process is killed (`kill -9`) after a completed backfill with a persisted
  `coverage_snapshot` row, when it is relaunched via `scripts/start-backend.sh` and `/data` is loaded cold
  (no ingest job running), then the Coverage panel renders the persisted coverage numbers (universe
  count, per-symbol coverage, gaps, capacity) within the committed boot+page budget in
  `reports/perf-budgets.md`, and `logs/backend.log` shows no `daily_prices`-scale (3.3M-row) prefill query
  during boot or the page load.
- TC-2: given the backend is restarted per TC-1, when `/scanner-runs` and the market-phase card on `/`
  are loaded for the most recently ingested as-of date, then both render the stored snapshot values with
  no compute-on-read, verified by watermarking `max(scanner_results.id)`/`max(forward_returns.id)` before
  and after the page load and confirming no new rows were created by the load itself.
- TC-3: given a forward-aggregate warm is in flight for a heavy-compute as-of covering all configured
  horizons, when a concurrent `GET /api/research/regime-lab` request is issued, then the response is
  either (a) HTTP 200 with all horizons byte-identical to the pinned pre-fix reference, or (b) HTTP 200
  with an honest `by_horizon[].status: "unavailable"` marker on only the horizon(s) that could not
  complete under memory pressure — never an uncaught `MemoryError`, never a 500, never a blank page.
- TC-4: given the same warm+concurrent-request scenario as TC-3, when process VmPeak is sampled
  throughout, then VmPeak stays under the declared `server.memory_cap_mb` (8192 MB), with the margin
  recorded in a new dated `reports/perf-budgets.md` addendum.
- TC-5: given the warm+concurrent-request scenario, when `GET /api/health` is polled once per second
  throughout (poll density must be ≤1s per the iter-54 lesson), then every poll answers HTTP 200 within
  the relaxed ≤2s bounded-background-compute ceiling, with zero unresponsive/frozen windows — the poll
  log's raw line count, slowest single answer (value + timestamp), and OPEN/CLOSED window boundaries
  (read from the job's own markers, never hand-picked) are published together in the same addendum before
  any "zero failures" claim is written.
- TC-6: given the bounded `compute_regime_lab` implementation, when it is run against the SAME inputs
  (horizons, `as_of`) that produce byte-identical output on a memory-unconstrained pass, then its output
  equals the pinned pre-fix reference for every horizon, both scoped and unscoped `as_of` — proven by a
  fixture-backed equality test.
- TC-7: given the six required-still-passing journeys' goldens (J-01, J-03, J-04, J-06, J-08, J-09), when
  the deterministic replay lane runs LAST, after all code changes and any audit-fix land, then all six
  replay PASS; if a live audit finding needs a code change, it is filed as a written note for iteration 60
  instead of being applied as a code-changing fix inside this dispatch.
- TC-8: given AG-9's backfill-only drill rule, when this iteration's developer and QA drills exercise
  ingest, then every `data_provider_runs` row created during this iteration reads `provider='seed'`,
  verified by a pre-lane watermark (`max(data_provider_runs.id)`) recorded before the lane and re-queried
  after it.
- TC-9: given AG-10's host-guard caps, when this iteration's diff is reviewed, then `git diff --stat` over
  `config.yaml`, `host-guard.env`, `start-backend.sh`, `dev.sh`, `start-frontend.sh` is empty (no cap
  weakened, removed, or bypassed).
- TC-10: given J-05 and J-07 both carry a `[NEW]`-flagged walkthrough clause, when the iteration runs at
  full depth, then `demo.sh ops-hardening --session-live` produces a recorded walkthrough covering (a) the
  TC-1/TC-2 cold-restart-and-serve-from-storage sequence for J-05, and (b) the TC-3/TC-4/TC-5
  crash-free-warm-and-healthy-health sequence for J-07 — every frame is opened and shows real, distinct,
  non-blank rendered state before being cited as evidence (iter-58 lesson).
- TC-11: given the API returns a per-horizon `status: "unavailable"` degrade marker (TC-3 case b), when
  `/research/regime-lab` renders that horizon's column, then the UI shows a contained, honest "temporarily
  unavailable" placeholder for that horizon only — never a blank crash page, never a fabricated number —
  mirroring the Factor Lab's existing degrade-field rendering convention.
- TC-12: given `journey-scripts/J-05.json`'s golden reserves a fixed historical date (2010-11-05) as a
  zero-`scanner_runs`-row precondition, when this iteration's lane needs to exercise J-05, then it first
  re-verifies that date still holds 0 `scanner_runs` rows (rotating it in the same commit if consumed)
  before relying on it, and the developer's own step-3 restart-and-cold-check exercise deliberately uses a
  DIFFERENT, already-ingested date so it never consumes the golden's reserved precondition date.

## NOTES

- **Lessons applied directly:** iter-53 ("encode a recurring ordering/discipline break as a binding
  DoD/TC line, not a reminder") → TC-5/TC-7 drill-reporting and lane-ordering items above; iter-54
  ("poll density decides whether an availability defect is visible at all") → TC-5's explicit ≤1s
  sampling requirement; iter-55 ("a verification fixture that consumes its own precondition is a
  guaranteed future false-regression") → TC-12; iter-57/iter-58 ("segment boundaries chosen by hand are
  where failures go to disappear" / "a drill write-up can reproduce the exact defect it was written to
  correct") → the binding raw-log-reconciliation requirement on every drill this iteration produces;
  iter-58 ("hashing an evidence directory for distinctness does not prove the pictures show anything") →
  TC-10's explicit "opened, not just hashed" requirement.
- **Assumption logged:** `assumptions.md` (iter-59) records the reading that "measure and then bound"
  means ship the bound this same round (not a diagnostic-only round), given iter-58's incident already
  supplies real profiling data and the fix pattern is already proven elsewhere in the same Data Contract
  row — with the stated fallback if the developer's own profiling pass contradicts that diagnosis.
- **Risk discipline (rule 5):** this iteration's one risky product-code action is the `compute_regime_lab`
  bound. J-05's step 3 is verification-only against already-built, evaluator-confirmed code; if it
  surfaces an unexpected defect, that defect is diagnosed and carried to iteration 60 rather than bundled
  into this same dispatch as a second risky change.
- **Escalation status:** this iteration directly answers the ESCALATE's structural point (neither journey
  can close without the full-depth demo lane) and its item (1)/(3). Items (2) (drill-reporting discipline)
  is encoded as a binding DoD/TC line above rather than left as prose. The owner items (off-process
  compute; the 20-minute finalize budget under live traffic) remain open and human-owned — not replanned
  here (rule 6).
