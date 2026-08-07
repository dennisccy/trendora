# Goal Iteration 51 — Serve the Factor Lab from an ingest-time artifact, not a live compute

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** ops-hardening
- **Iteration:** 51
- **Mode:** next
- **Depth:** full
- **Full trigger:** 3 — the prior verdict (iter-50) was ESCALATE; full depth is mandatory this
  iteration with no exceptions, per the binding rule.
- **Frontend Present:** no
- **Target journeys:** J-05, J-06, J-07
- **Required-still-passing journeys:** J-01, J-03, J-04, J-08, J-09
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

Stop `GET /api/research/factor-lab?all=true` from ever computing live on the request path — warm its
default all-history view inside the same ingest finalize tail that already warms every other heavy
research aggregate, so opening the Factor Lab page is always a fast, stored-row read.

## BACKGROUND

Prior verdict was ESCALATE (mandatory full depth, no exceptions). The iter-50 evaluator's own
next-step item (1) named this exact fix as "the one change that matters," and the iter-50 audit-fix
pass's own live measurement (`reports/perf-budgets.md` Item S, Addendum 9/10) independently confirms
the mechanism: `compute_factor_lab_all`'s per-(factor,horizon) loops are tight CPU-bound Python that
starve the event loop via GIL contention, costing a live cold view 578–875s solo and 742s under a
concurrent ingest — three orders of magnitude over J-06's budget — and the auditor's own words name
the fix verbatim: *"serve `/research/factor-lab` from an ingest-time artifact instead of computing it
on the request path."* This is not a new invention; it is `docs/goal.md`'s own Improvement Direction
table, aggregation candidate #6 ("Research event-study/factor-lab/regime-lab hot keys ... warm default
keys at ingest"), which the existing `_refresh_ingest_aggregates` finalize tail already does for the
sibling `event_study_cache` default key (`research_hot_keys_warm`) — this iteration extends the SAME
precedent to `factor_lab_all_cached`.

**Lessons applied (Applies-to matches):** iter-50's second lesson — *"Bounding memory cannot close a
responsiveness requirement... the cause is GIL contention... not allocation"* — is the direct grounds
for this iteration's fix shape (a scheduling change, not a memory change). Iter-49's lesson — *"a bound
proven on an idle host with a throwaway DB copy is not a bound proven in the product"* — is why every
TC below requires an in-app, concurrent measurement, not an isolated drill. Iter-46/47's lesson on
null-test golden scripts applies if a fresh `journey-scripts/J-06.json`/`J-07.json` step is authored:
assert against a new run's own row/log line, never page-wide text.

Priority rubric: no journey regressed since iter-50 (rule 1 N/A). The last `coherence.md` was
COHERENCE-WARN, not FAIL (rule 2 N/A — advisory-only; its two advisories are closed by this iteration's
blueprint edits, see NOTES). J-05/J-06/J-07 are the clear unblocker set (rule 3) — all three share the
SAME root cause and the SAME `research.py`/`data_manager.py` finalize-tail subsystem, so this is ONE
risky change, not three (rule 5; logged to `assumptions.md`, iter-51). J-04, J-08, J-09 carry no code
work this iteration and stay in the regression set; J-04 additionally needs re-verification since it
was last checked at iter-45 (5 rounds untested) — the full 8-journey lane this depth mandates covers it.

**Honest limit, stated up front:** this fix removes the UNBOUNDED, unpredictable, request-triggered
compute (the wedge-class hazard) and is expected to close J-06's recorded over-budget readings (a cache
HIT becomes the common case). It does **not** by itself guarantee J-07 step 2's ≤2s during-ingest
ceiling — the auditor's own diagnosis (GIL contention between tight CPU-bound loops and the event loop)
is a property of running the compute in-process at all, and a small residual breach already existed in
the ingest window before this iteration's warm was added (96/1,179 polls in the iter-50 TC-1 drill).
That residual is disclosed as carried, not claimed fixed.

## IN SCOPE

### Backend
- [ ] Extend `_refresh_ingest_aggregates`'s finalize tail (`apps/backend/app/engine/data_manager.py`)
  with a new warm phase that calls `research.factor_lab_all_cached(session, cfg, as_of=None)` for the
  default all-history key, mirroring the existing `research_hot_keys_warm`/`index_series_warm` per-item
  isolation pattern (own try/except, `MemoryError` caught distinctly + `_release_process_memory()`,
  `prog.tick()` heartbeat before/during the call since this phase can run several minutes, phase-timing
  log line). On success, append a new legal `aggregates_refreshed` member, `"factor_lab_all"` — honestly
  omitted on a degrade, mirroring every other category's gate.
- [ ] Bound `_combination_cohort_members`'s (`apps/backend/app/engine/research.py:1530`)
  `strict_members` construction so it no longer allocates a `set(range(pool_n))` scratch set
  unconditionally — start the AND-intersection from the first single-condition membership set (or an
  empty set when there are no conditions) instead of a full-range set immediately reduced by
  intersection. This is the exact frame logged immediately before the 2026-08-05 17m30s wedge.
  Byte-identical `single`/`strict`/`composite` membership sets required against a pinned pre-fix
  reference fixture.
- [ ] Add a fresh, dated `reports/perf-budgets.md` addendum recording the new `factor_lab_all_warm`
  phase's own measured wall-clock contribution to the finalize tail, and reconcile the existing TC-1
  1,200s finalize-tail-total budget against the new real total (record it; do not silently exceed or
  silently loosen it).
- [ ] Capture the finalize-tail teardown timing lines (already instrumented iter-50:
  `_release_process_memory: START/DONE`, `J-05 finalize-tail teardown timing`) for this iteration's own
  concurrent heavy-warm drill, toward the still-open, unproven-either-way 2026-08-05 17m30s wedge
  question — a diagnostic capture, not a claimed fix.

### Frontend
None. No frontend file is touched — the existing `/research/factor-lab` route, component, and payload
shape are unchanged; only the warm TIMING moves earlier.

### New user-facing capability
Opening `/research/factor-lab`'s all-factors view immediately after any ingest job now serves the
already-computed stored result instead of triggering a live multi-minute compute.

### New information displayed
None new to the user. The two degrade-signal fields `by_horizon[].status` / `factors_status`
(`app.engine.research`, shipped iter-50, formally registered in the Data Contract this iteration per
the coherence-auditor's advisory) are pre-existing on the payload; the frontend is unchanged and does
not yet render them distinctly (a carried, disclosed UX gap, not this iteration's regression).

### New user actions
None.

### UI surface changes
None.

### Product surface delta
No visual change. The Factor Lab page becomes reliably fast after any ingest instead of occasionally
(now: always, when the dataset-version stamp changed) paying a multi-minute cold compute on the request
path.

### Blueprint conformance
No new page, route, or nav entry. Lives entirely under the existing "Membership timeline / research
hot-key caches" Data Contract row (`runs/goal-session-ops-hardening/state/blueprint.md`) and the
existing `/research/factor-lab` canonical home (Information Architecture — unchanged, Research nav
section). Blueprint already updated this iteration (additive edits): the row's Notes gain the iter-51
clause plus the registration of `by_horizon[].status`/`factors_status`, and the stale "(TARGETED, not
yet built)" wording on iter-50's own entry is corrected to "(BUILT)" per the coherence-auditor's third
advisory.

### Data-contract additions
- `aggregates_refreshed` (existing `list[str]` field on the Backfill run-summary contract / Job history
  rows) gains one new legal member, `"factor_lab_all": str` — computed by
  `app.engine.data_manager._refresh_ingest_aggregates` warming `app.engine.research.compute_factor_lab_all`
  (via `factor_lab_all_cached`), served by the SAME `GET /api/data` (persisted `runs` list) and
  `GET /api/data/jobs/{job_id}` (live poll) endpoints that already serve this field. No second producer,
  no second endpoint, no schema change. (TC-1 verifies this addition.)

## OUT OF SCOPE

- Moving `compute_factor_lab_all` to a separate process/subprocess/worker boundary (the auditor's
  alternative reading of "off the thread that answers requests") — a bigger, riskier structural change;
  logged as the road not taken in `assumptions.md`, iter-51.
- Closing J-07 step 2's ≤2s-during-ingest ceiling in full — the residual GIL-contention breach inside
  the finalize tail's own serialized warm phases is a pre-existing, disclosed gap, not newly introduced
  or newly worsened in kind by this iteration, and is not this iteration's deliverable.
- Raising or otherwise touching `server.memory_cap_mb` / `malloc_arena_max` / `host-guard.env` values —
  AG-10 frozen, never edit.
- Re-opening the columnar `_FactorCoreRecords`/`_FactorObsPool` bound, the single-flight waiter cooldown,
  or the `phase_context_by_date` conditional skip — all DONE per iteration-state.md's binding "Do not
  redo" list.
- The interlock spec contradiction (`iter-50/cc`) — an explicit owner decision, restated in NOTES, not
  re-planned as agent work this iteration.
- The Regime Lab's separate 8192MB-cap hit (`research.py`, iter-33/g) — 16 consecutive deferrals,
  untouched, a different row's territory.
- Evidence capture / demo walkthrough retakes — never an iteration goal (rule 7); ride the make-up lane
  as passenger tasks only.
- `_combination_observations`'s own ~250s cost (the LATE stall cluster, already named and deliberately
  carried since iter-50) — a separate, undiagnosed effort, not this iteration's one risky action.

## DEFINITION OF DONE

- [ ] TC-1 through TC-9 (below) all pass.
- [ ] Target journeys J-05, J-06, J-07 scored via browser-qa-agent / deterministic replay + LLM fallback.
- [ ] Required-still-passing journeys J-01, J-03, J-04, J-08, J-09 remain green (deterministic replay +
      LLM fallback where no golden exists).
- [ ] No anti-goal violation introduced: `git diff --stat` over `config.yaml`,
      `project-extensions/host-guard/host-guard.env`, `scripts/start-backend.sh`, `scripts/dev.sh`,
      `scripts/start-frontend.sh` stays EMPTY (AG-10); all ingest in any drill runs `provider='seed'`
      (AG-9); no committed secret (AG-7).
- [ ] Unit tests pass; no regressions (`apps/backend/tests/test_research_streaming.py`,
      `apps/backend/tests/test_data_manager.py`, plus new tests for the warm phase and the
      `_combination_cohort_members` bound).
- [ ] `reports/perf-budgets.md` carries a fresh, dated addendum with the new phase's measured cost and
      the reconciled finalize-tail total (never silently loosened or silently exceeded).
- [ ] The full 8-journey browser/replay lane runs LAST, after every fix-mode/audit-fix pass, with no
      product-code change afterward (TC-8 below; the TC-13/TC-7 sequencing rule, breached 5 consecutive
      rounds).
- [ ] Dev handoff written at `docs/handoffs/goal-ops-hardening-iter-51-dev.md`.

## TESTING REQUIREMENTS

- Browser: J-05 (steps 1–4, especially step 2's health-during-heavy-ingest poll and step 3's cold
  `/data` reload), J-06 (step 1's full 11-page sweep, specifically `/research` factor-lab), J-07 (steps
  1–3; step 4's induced-memory-pressure abort re-verified unchanged). Regression replay: J-01, J-03,
  J-04, J-08, J-09.
- Unit/integration: the new `factor_lab_all_warm` finalize-tail phase (cache-row creation, honest
  `aggregates_refreshed` gating on MemoryError, `_release_process_memory()` invoked on abort); the
  `_combination_cohort_members` bound (byte-identical `single`/`strict`/`composite` sets against a
  pinned pre-fix reference fixture, no `set(range(pool_n))` allocation for a representative pool size).
- Error cases: an ingest whose `factor_lab_all` warm raises `MemoryError` mid-compute must degrade
  honestly (existing per-entry/whole-response degrade path, unchanged), release memory, and omit
  `"factor_lab_all"` from `aggregates_refreshed` — never crash the job, never claim a refresh that
  didn't happen.

- TC-1: given a `/data` backfill request creates at least one new snapshot date (bumping the
  dataset-version stamp), when the job's finalize tail completes, then the persisted run record's
  `aggregates_refreshed` list contains `"factor_lab_all"` and an `EventStudyCache` row exists for the
  default all-history key (`subject=_ALL_FACTORS_SUBJECT`, `view=_ALL_FACTORS_VIEW`, `asof_key=None`,
  `dataset_version=<current>+token`, `horizon=default_horizon`).
- TC-2: given TC-1's ingest has just completed with no concurrent request during the warm, when
  `GET /api/research/factor-lab?all=true` (no `as_of`) is requested, then the response is HTTP 200 and
  the server logs show a cache HIT (no live `compute_factor_lab_all` invocation logged for this
  request).
- TC-3: given the `/research/factor-lab` all-factors page loads immediately after the ingest in TC-1/
  TC-2 in a live browser (prod-mode `scripts/start-backend.sh` / `scripts/start-frontend.sh`), when the
  time-to-interactive and on-load `GET /api/research/factor-lab?all=true` latency are measured, then
  both are recorded in `reports/perf-budgets.md` and are within the committed Factor Lab budget,
  closing the previously-recorded 780.2s/874.7s/742.07s over-budget readings.
- TC-4: given `_combination_cohort_members` is invoked on a fixture pool of representative size
  `pool_n`, when the strict-overlap AND-intersection is computed, then no `set(range(pool_n))` scratch
  allocation occurs (asserted by the targeted unit test) and the `single`/`strict`/`composite` outputs
  are byte-identical to a pinned pre-fix reference oracle.
- TC-5: given the ingest finalize tail (including the new `factor_lab_all_warm` phase) runs while
  `GET /api/health` is polled once per second for its full duration plus at least 300s past completion,
  when the run finishes, then every poll answers HTTP 200 (zero non-200s, zero connection failures) and
  the process's peak VmPeak stays under `server.memory_cap_mb` with the margin recorded in
  `reports/perf-budgets.md`.
- TC-6: given the same drill as TC-5, when a concurrent `GET /research/factor-lab?all=true` OR
  `GET /research/factor-combination` request is issued mid-warm (mirroring the iter-50 wedge scenario),
  then the request completes without triggering a live `compute_factor_lab_all`/`_combination_cohort_members`
  compute (cache HIT per TC-1/TC-2) and no `MemoryError` traceback appears in `logs/backend.log`
  attributable to `_combination_cohort_members`.
- TC-7: given the finalize-tail teardown timing lines added in iter-50 are already instrumented, when
  this iteration's TC-5/TC-6 drill runs, then those log lines (`_release_process_memory: START`/`DONE`,
  `J-05 finalize-tail teardown timing`) are present in `logs/backend.log` and their reported
  `total_teardown` duration is recorded in the dev handoff — diagnostic evidence toward the still-open
  2026-08-05 wedge question, no new fix claimed from this alone.
- TC-8: given all code changes for this iteration are complete and committed, when the full 8-journey
  browser/replay lane (J-01 through J-09) is dispatched, then it runs LAST — no product-code file under
  `apps/backend/` or `apps/frontend/` has an mtime later than the lane's own results-file mtime; any
  fix-mode/audit-fix pass that changes product code after the lane runs triggers a mandatory re-run
  before this iteration is scored.
- TC-9: given the new `factor_lab_all_warm` phase's own measured wall-clock cost from TC-5, when
  `reports/perf-budgets.md`'s existing TC-1 finalize-tail-total budget (1,200s) is reconciled against
  the new total, then a fresh dated addendum records the real total explicitly (never silently
  loosened, never silently exceeded without disclosure).

## NOTES

- **Documentation catch-up (blueprint only, not new code this iteration):** `by_horizon[].status:
  "unavailable"|absent` and `factors_status: "unavailable"|absent` on
  `GET /api/research/factor-lab?all=true` (`app.engine.research:1324`, `:1339`, `:3910`, shipped
  iter-50) were never formally registered — closed this iteration by editing
  `runs/goal-session-ops-hardening/state/blueprint.md`'s "Membership timeline / research hot-key
  caches" row to list both fields with their (unchanged) computing module and serving endpoint, per
  the iter-50 coherence-auditor's advisory. No TC needed (no code path exercises a registration).
- **Assumption logged (`assumptions.md`, iter-51, two entries):** (1) choosing "warm at ingest" over
  "move off-process" for the request-path fix, given the evaluator offered both as acceptable readings;
  (2) bundling the `factor_lab_all` warm and the `_combination_cohort_members` bound as ONE risky change
  under rule 5, mirroring the iter-50 decomposer's own precedent.
- **Owner item, restated, not re-planned:** the interlock spec contradiction (`iter-50/cc`) — TESTING
  REQUIREMENTS' "never silently drop the work" vs the finalize-tail warm's "defer when the boot/re-warm
  path already holds the slot" cannot both hold; the owner has not yet picked which wins. No agent
  action this iteration; simply do not touch `_try_acquire_drawdown_warm`/`_release_drawdown_warm`
  (`data_manager.py`) to "fix" this without an owner answer.
- **Carried, untouched (do not schedule as new diagnosis):** iter-29/b · iter-31/e · iter-32/f ·
  iter-33/g (16th deferral) · iter-35/k · iter-36/n · iter-37/o · iter-37/q · iter-39/u · iter-46/az ·
  iter-46/ba · iter-47/bd · iter-47/bf · iter-47/bi · iter-48/bj.
- **Golden-script caution:** `journey-scripts/J-05.json` and `J-06.json` exist but scored zero executed
  rows last round; `J-07.json` has no golden on file (LLM lane). Per iter-46/47's binding lesson, any
  fresh/rebuilt golden step for this iteration must assert against a NEW run's own row/log line (e.g.
  the persisted `aggregates_refreshed` value, or a fresh `data_provider_runs` id), never page-wide text
  that a stale history panel would already satisfy.
- **Budget tension, stated plainly:** adding the `factor_lab_all_warm` phase to the finalize tail is
  expected to push its total wall-clock meaningfully past the existing 1,200s (TC-1) figure. This is an
  accepted, disclosed trade — trading an unbounded, unpredictable, user-triggered multi-minute hang for
  a bounded, predictable, already-monitored addition to a window the product already treats as a
  background-compute period with its own relaxed 2s health ceiling. Record the real number; do not
  quietly raise or quietly blow through it.
