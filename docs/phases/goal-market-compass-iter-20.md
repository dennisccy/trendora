# Goal Iteration 20 — J-11 Stage E: forward-return hole repair over the retained + rebuilt snapshot set

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** market-compass
- **Iteration:** 20
- **Mode:** next
- **Depth:** full
- **Full trigger:** 1 — Stage E's correctness is a cross-cutting invariant spanning `forward_testing.py`
  (two candidate entry points with materially different side-effect scope — see BACKGROUND), the
  `j11_maintenance.py` identity/mutation-accounting tooling Stage D already proved, `prices.py`'s
  bar-cache sharing mechanism, and a live, additive-but-still-irreversible write potentially touching
  every row of the ~6.8M-row `forward_returns` table across the full `scanner_runs` population
  (~3,100+ rows) — no single journey's existing test suite covers this interaction. This planning pass
  itself found a live risk (calling the wrong existing entry point can mint a `ScannerRun` OUTSIDE the
  11-date incident boundary as an undocumented side effect) that no prior lane in this session had
  reason to look for. (This also matches the evaluator's binding `full` recommendation for this
  iteration; no escape condition was needed since the recommendation already says `full`.)
- **Frontend Present:** no
- **Target journeys:** J-11
- **Required-still-passing journeys:** J-01, J-04, J-10
- **Anti-goal reminders (verbatim from `docs/goal.md`):**
  - **AG-1:** A score, ranking, or "edge" MUST NOT be presented as proven/confident unless it is backed
    by a **passing certified-claim entry** in the evidence ledger (out-of-sample, control-beating).
    Unbacked values MUST render a "not yet proven" state. *(critical)*
  - **AG-2 — Decision-quality only:** never present return promises, price targets, "buy/sell" signals,
    or alpha claims; never place or simulate orders. Candidate framing is "worth monitoring", never
    advice. *(critical)*
  - **AG-3:** A journey passes ONLY if the **displayed numbers are correct** — they match the engine's
    computation for the same as-of date — not merely that the page renders. *(critical)*
  - **AG-4 — No overfit edges:** any pattern surfaced as "proven" must have survived the referee (sealed
    out-of-sample holdout + controls + multiple-testing correction), never in-sample fit alone.
    *(critical)*
  - **AG-5 — Preserve determinism and no-lookahead:** scoring uses bars ≤ as-of; forward returns use
    bars > as-of; the manifest for close D derives only from state stored at or before D; never
    introduce lookahead anywhere. *(critical)*
  - **AG-6:** No iteration ships if its evidence-derived claims (if any) lack a passing referee verdict
    from the post-decompose gate. *(critical)*
  - **AG-7:** No hard-coded credentials, API keys, or tokens in source files. *(critical)*
  - **AG-8 — Resilience to data-shape and data-scale change:** widening the data basis must never crash
    an existing page or exhaust memory — consumers of widened fields are re-validated, the UI degrades
    gracefully, and unbounded whole-table ORM loads are forbidden. *(critical)*
  - **AG-9 — Offline-deterministic ingest:** ingest jobs run only against the committed seed / local
    provider fixtures — no live external network calls or paid data services without an explicit
    goal.md amendment. *(critical)* — all three dated exceptions (J-10 recovery fetch, its vendor
    addendum, and the AVB diagnostic fetch #2) are **exhausted**; none applies to Stage E, and Stage E
    authorizes **no** network fetch of any kind.
  - **AG-10 — Host resource ceiling:** heavy compute MUST be launched only via the project launch
    scripts, which MUST apply the host caps; never remove, weaken, or bypass these caps. *(critical)*
  - **AG-11 — No new composite candidate number:** no "fit", "conviction", "match", "probability of
    success", or any new blended score may be attached to candidates, the market, or the manifest.
    *(critical)*
  - **AG-12 — Manifest immutability:** a stored `next_session_manifests` row and its exported file are
    never mutated or deleted by any later ingest, rebuild, data removal, config change, or code change;
    corrections happen only as new version rows; a historical view never substitutes a newer manifest.
    *(critical)*
  - **AG-13 — System-vs-market separation:** readiness/preflight vocabulary must never label market
    state, and regime/phase vocabulary must never label system state. *(critical)*
  - **AG-14 — No Tapeology coupling:** no imports from, network calls to, or writes into the tapeology
    repository or its services. *(critical)*
  - **AG-15 — No outcome-tuned selection:** the selection rule and its thresholds must not be chosen or
    revised from realized forward returns within this goal. *(critical)*
  - **AG-16 — Cohorts are not controls:** the comparison cohort and the near-threshold shadow cohort are
    frozen non-selected pools, not matched or causal control groups. *(critical)*
  - **AG-17 — Repair never rewrites provenance:** restoring deleted historical data MUST NOT
    retroactively change research provenance. Any manifest or artifact produced while the database was
    known to be damaged — everything dated from the iter-5 drill until **J-11 Stage G passes** — remains
    marked unusable as prospective/out-of-sample evidence. The incident record itself is evidence and
    MUST NOT be deleted, rewritten, or silently superseded. *(critical)*
  - **AG-18 — The authorized manifest migration preserves everything:** the bounded
    `next_session_manifests` schema migration authorized in J-11 step 11 (ruling A1) removes the
    `source_run_id` foreign-key constraint and **nothing else**. No manifest may be regenerated,
    rebound, rehashed, upgraded, deleted, or newly minted by it or around it. *(critical)*

## GOAL

Execute the owner-authorized J-11 Stage E global create-once forward-return hole repair — filling every
derivable `forward_returns` gap on the eleven Stage-D-regenerated incident-date runs AND on any retained
run whose forward-return rows the original incident cascade deleted — through the existing canonical
machinery only, with zero raw-input, snapshot, or manifest mutation. This is a backend-only,
no-user-visible-surface maintenance iteration: on success it reports `J-11 STAGE E COMPLETE: YES`, while
the overall incident honestly remains `J-11 INCIDENT STATUS: NOT REPAIRED — ATTEMPT INCOMPLETE` until
Stages F and G follow in later iterations.

## BACKGROUND

Iteration 19 executed J-11 Stage D live and cleanly: all eleven `app.engine.j11_maintenance.
INCIDENT_DATES` now carry exactly one freshly regenerated `ScannerRun` each (ids 3148–3158), every one
stamped with the same frozen attempt identity (`53d2ffd1…`, recorded in
`runs/goal-market-compass-iter-19/j11-stage-d-execute-frozen-identity.json`), and the evaluator
independently re-derived every figure read-only against the live database. `docs/goal.md`'s own
"OWNER RULING — J-11 Stage D through Stage G recovery execution AUTHORIZED" item 7 already authorizes
Stage E **unconditionally following a successful Stage D regeneration** — no further owner instruction is
required to begin it, and this spec does not amend `docs/goal.md`.

This spec scopes iteration 20 to **Stage E alone**, continuing the one-stage-per-iteration discipline
iteration 19 itself established and logged for Stage D (see the assumption-ledger entry filed below):
Stage F (dependency-aware cache invalidation across seven named caches) and Stage G (the full
verification/acceptance gate — the only stage that may declare the incident repaired) remain for later
iterations. This is exactly the honest checkpoint item 14's terminal-outcome contract anticipates:
`J-11 STAGE D EXECUTED: YES` (carried), `J-11 STAGE E COMPLETE:` this iteration's own outcome, Stages
F/G not yet attempted, `J-11 INCIDENT STATUS: NOT REPAIRED — ATTEMPT INCOMPLETE`, boundary still
`ACTIVE`.

**A live write-scope risk found while planning this iteration (logged to `assumptions.md`).**
`docs/goal.md` step 5 names two existing functions side by side for the forward-return repair —
`forward_testing.backfill_forward_returns` and `backfill_run_forward_returns` — without saying which one
to call. Reading `forward_testing._backfill()` (the function `backfill_forward_returns()` delegates to,
`forward_testing.py:531-590`) directly: **before** it inserts a single forward return, it first "ensures
a persisted snapshot for every walk-forward cadence date" by calling `scanner.run_scan` for any
`walk_forward_asof_dates()`-computed date that lacks an existing `ScannerRun` — guarded only by the J-11
boundary check, which only blocks dates that happen to be incident dates. `walk_forward_asof_dates()`
computes a `quarterly`, 30-`history_years` cadence grid (`config.yaml` `walk_forward:`) that is
independent of the scanner's own `monthly` deep-cadence snapshot schedule, so nothing already on record
proves every one of its target dates already carries a run. Calling `backfill_forward_returns()`'s
whole-database entry point therefore risks minting a **new `ScannerRun` outside the eleven-date incident
boundary** as an undocumented side effect — exactly what the Stage D→G ruling item 7 forbids ("Stage E
may **not**... broaden into unrelated historical cleanup"). `backfill_run_forward_returns()` performs the
identical create-once forward-return INSERT with no such side effect (its own docstring: "it never
UPDATEs a `scanner_runs` / `scanner_results` / `*_scores` row"). This spec therefore requires the per-run
path exclusively — see IN SCOPE and TC-3/TC-19.

Depth is `full`, matching the evaluator's binding recommendation for this iteration (0 consecutive lean
iterations dispatched, so no hardening-cadence trigger is even needed independently). This spec
deliberately does **not** set a `Maintenance isolation:` or `Depth enforcement:` metadata line — those
are operator-only controls, and a self-written safety declaration here would be exactly the
governor-bypass anti-pattern 25 describes. Independently of this spec, `docs/goal.md`'s Stage D→G ruling
item 13 requires the human dispatching this run to supply `CHAIN_MAINTENANCE_ISOLATION=true` and
`CHAIN_REQUIRE_FULL_DEPTH=true` as required launch conditions for the whole D→G execution, unchanged
since iteration 19.

**Lessons applied** (from `lessons.md`): iter-15/iter-18's shared lesson — a guard or invariant scoped by
"which code path" must be checked against a real, grepped call graph, never a hand-built one; that is
precisely how this spec's cadence-ensure risk above was found, by reading `_backfill()`'s body rather
than trusting its docstring summary or the goal text's side-by-side function naming. Iter-9's
population-wide-claim lesson governs the three-population classification below (a per-population count
and a per-key proof, never one aggregate "all filled" boolean). Iter-12/13's "mtime+WAL as the PRIMARY
instrument, corroborated — never replaced — by a narrower fingerprint" precedent governs the mutation-
accounting requirement. Iter-19/19b's cross-iteration-diff technique (compare a fresh live sweep against
the PREVIOUS iteration's own recorded end state, not only this iteration's internal before/after pair)
should be applied again where iteration 19 left a reusable end-state artifact; if no standalone raw
"after" sweep is available from iteration 19 (its evidence directory persists diffs, not a separately
named raw sweep file — verified by inspection), state that gap honestly rather than skip the
corroboration silently — the in-iteration before/after pair plus the whole-file mtime/size/WAL bracket
remain the primary instrument regardless, so this is not blocking.

**Resource discipline (AG-10, and the 2026-08-20 host-freeze incident carried in `docs/goal.md`
Constraints).** This host previously froze from memory overcommit + swap-thrash during a goal-mode run.
`prices._BarCache.prefill` (the mechanism behind `prices.prefilled_bar_cache`) has its own documented OOM
history (an unbounded `.all()` materialization fixed by streaming, then a further list-overhead fix via
`array.array`) and J-09's own Constraints text records it as a candidate for a configured memory budget
that has **not yet landed** in this session (J-09 is still `partial`). Whichever bar-loading approach
Stage E uses — a shared `prefilled_bar_cache` or the default lazy per-symbol path — this spec requires a
live peak-memory measurement against the existing `memory_cap_mb`/`HOST_GUARD_MEMORY_HIGH` ceiling,
mirroring J-09's own measurement discipline, and forbids introducing a parallel writer.

## IN SCOPE

### Backend
- [ ] New Stage E execution module — e.g. `apps/backend/app/engine/j11_stage_e_execute.py`. It must:
  - re-run a fresh, read-only preflight before any write: confirm the `j11-incident-recovery`
    maintenance boundary is still `active=1` covering exactly `INCIDENT_DATES` and the live guard still
    blocks all 11 dates (read-only re-verification only — never re-arms, never disarms); confirm each of
    Stage D's 11 rebuilt `ScannerRun`s is still present, unrestamped (same id, same `asof_date`, same
    `created_at`), and each currently has zero `ForwardReturn` rows; recompute
    `engine_identity.compute_engine_identity(config)` fresh and assert it **equals** the identity Stage D
    froze (read from `runs/goal-market-compass-iter-19/j11-stage-d-execute-frozen-identity.json`) — a
    mismatch means the attempt's engine/config identity has drifted since Stage D, which per the ruling's
    item 2 makes the whole D→G attempt **incomplete**, and Stage E must STOP rather than continue
    piecemeal under a different identity; confirm `next_session_manifests` is still 24 rows, byte-
    identical to the Stage-D-verified state, on the 4 incident-date rows;
  - do **not** freeze a new Stage-E-specific attempt identity and do **not** re-run
    `freeze_stage_d_attempt_identity` — `ForwardReturn` carries no `engine_identity` column (verified:
    `models.py`'s `ForwardReturn` class), Stage E writes no `ScannerRun`, and the ruling's item 2 already
    permits Stage E to simply **cite** Stage D's frozen identity for provenance;
  - iterate every row currently in `scanner_runs` (the full retained-plus-Stage-D-rebuilt population, in
    ascending `asof_date` order for reproducibility) and call
    `forward_testing.backfill_run_forward_returns(session, run, config)` once per row — the create-once,
    INSERT-only path. **Never call `forward_testing.backfill_forward_returns()`** (the whole-database
    entry point) anywhere in this module or its CLI script, for the reason in BACKGROUND;
  - run the per-run loop inside one shared bar-loading context on one `Session` — either
    `prices.prefilled_bar_cache(session, expected_symbols=<the resolved pool>)` (one whole-table load,
    shared by every subsequent `backfill_run_forward_returns` call via `close_on`/`bars_after`'s existing
    session-keyed cache lookup) or the default lazy per-symbol path with no prefill — and measure and
    record live peak process memory either way (see NOTES / TESTING);
  - after the loop, distinguish and report the three populations `docs/goal.md` step 5 names by name:
    (a) forward returns newly inserted for the 11 Stage-D-rebuilt runs; (b) forward returns newly filled
    on retained (non-incident) runs whose `measured_date` lands on one of the 11 incident dates (the
    defensive-sweep hole population first sized in Stage B's pre-reset inventory); (c) genuinely
    not-yet-mature (run, symbol, horizon) combinations, which must remain absent — never fabricate a row
    to reach parity;
  - perform post-execution mutation accounting via `j11_maintenance.capture_full_table_sweep` /
    `diff_full_table_sweeps` (before/after), plus the whole-file mtime/size/WAL bracket captured at the
    true process start and true process end as the primary instrument, expecting `changed_existing_tables`
    to be a subset of `{forward_returns}` only.
- [ ] A `--confirm`-gated CLI script — e.g. `apps/backend/scripts/run_j11_stage_e_execute.py` — mirroring
  `run_j11_stage_d_execute.py`'s idiom exactly: zero database interaction of any kind without `--confirm`;
  `--evidence-dir` required with no implicit default; evidence persisted at every checkpoint before the
  write; a completion/outcome marker written only after full post-execution verification passes.
- [ ] The confirmed live execution itself: run the script once against `apps/backend/data/trendora.db`
  under maintenance isolation, producing the full evidence set and the exact status lines listed in
  DEFINITION OF DONE.
- [ ] Fixture-scoped unit/integration tests for the new module and CLI script (never against the live
  database) covering every scenario in TESTING REQUIREMENTS.

### New user-facing capability
None — backend-only maintenance; no page, route, or UI element changes this iteration.

### New information displayed
None.

### New user actions
None.

### UI surface changes
None.

### Product surface delta
None this iteration. (Forward-return data becomes servable through the already-built `/backtest`/
research surfaces once Stage G eventually passes; J-11 needs no surface of its own, matching its
"Walkthrough: waived" status in `docs/goal.md`.)

### Blueprint conformance
No new surfaces. Stage E fills existing `forward_returns` rows through the SAME already-existing,
already-registered canonical functions (`forward_testing.backfill_run_forward_returns`, itself built on
the single `_insert_run_forward_returns` formula) — no second computation, no new endpoint, no new page.
`forward_returns`/`/backtest` data is not a tracked row in this session's `blueprint.md` Data Contract (it
predates this session, from `ops-hardening`) and this iteration adds no new one.
`runs/goal-session-market-compass/state/blueprint.md` is **not** edited this iteration (nothing to
register — mirroring iteration 19's identical conclusion for the identical reason).

### Data-contract additions
None.

## OUT OF SCOPE

- Stage F (dependency-aware cache invalidation across the seven named caches) and Stage G (full
  verification / the acceptance gate) — deferred to later iterations (scoping decision logged to
  `assumptions.md`).
- Calling `forward_testing.backfill_forward_returns()`'s whole-database entry point anywhere — see
  BACKGROUND; the per-run `backfill_run_forward_returns` loop is the only sanctioned write path this
  iteration.
- Any write to `scanner_runs`, `scanner_results`, `sector_scores`, or `theme_scores` — Stage D already
  regenerated the 11 incident-date rows; Stage E must not restamp, rewrite, or otherwise touch any of the
  four tables (`forward_returns` is the only table this iteration may write).
- Freezing a new Stage-E-specific attempt identity, or re-running `freeze_stage_d_attempt_identity` —
  Stage E cites Stage D's already-frozen identity for provenance only (see IN SCOPE).
- Deactivating or clearing the `j11-incident-recovery` maintenance boundary — forbidden until Stage G
  passes; it must remain `active=1` at the end of this iteration, whatever the outcome.
- Re-creating or re-arming `maintenance_boundaries`/the boundary row, or re-running Stage D — already
  LIVE, EXECUTED, VERIFIED ("do not redo" per the iteration-state digest); this iteration only
  re-**verifies** Stage D's state, read-only.
- Any provider/network fetch — AG-9 remains closed; no dated exception applies to Stage E.
- Any `daily_prices` write — raw inputs remain immutable through Stage G.
- The ordinary request-path guard gap (`scanner.resolve_run`, `scanner.py:348`) and the Data Manager
  write-path guard — explicitly recorded-but-deferred by the Stage D→G ruling (item 5) to post-Stage-G
  hardening work. Do not touch `app/api/*` or `data_manager.py`'s write paths this iteration.
- Any J-01–J-09 product/UI work, and specifically J-07/J-08 — blocked by the Loop-mechanics gate until
  Stage G passes.
- Application-service boot, browser-qa-agent, the deterministic replay lane, a second backend or frontend
  process — all OFF for the whole iteration (maintenance isolation).
- Any schema/DDL migration — none authorized or needed this iteration (`forward_returns`'s existing schema
  is unchanged; this is a pure row-insert operation).
- Modifying `forward_testing.py`, `scanner.py`, `prices.py`, `j11_maintenance.py`, `j11_stage_d.py`, or
  `j11_stage_d_execute.py` — Stage E composes their existing functions as-is; it introduces no second
  implementation of any scoring, return, or identity computation.
- Restamping, mutating, or otherwise touching the 34 iteration-10-era `ScannerRun`s (identity
  `6261ca17…`) or any pre-stamping-era NULL-`engine_identity` row.

## DEFINITION OF DONE

- [ ] Fresh preflight (maintenance boundary state, live guard, all-11-rebuilt-runs-present-and-unrestamped,
  all-11-at-zero-`ForwardReturn`, a live-recomputed `engine_identity` equal to Stage D's frozen value,
  manifest row count/values unchanged) is re-derived live and read-only immediately before any write; the
  attempt proceeds only if every check agrees with the certified Stage D end state — otherwise it STOPs
  with the exact blocker named and zero writes performed.
- [ ] The forward-return repair loop calls ONLY `forward_testing.backfill_run_forward_returns`, once per
  existing `ScannerRun`; `forward_testing.backfill_forward_returns()` is never called or imported by the
  new module or CLI script (proven by test, not by code review alone).
- [ ] The attempt ends in exactly one of the two states `docs/goal.md`'s Stage D→G ruling (item 14)
  defines — never an invented third state — and the dev handoff states the outcome using its exact
  vocabulary: `J-11 STAGE D EXECUTED: YES`, `J-11 STAGE E COMPLETE: YES/NO`, `J-11 STAGE F COMPLETE: NO`,
  `J-11 STAGE G VERIFIED: NO`, `J-11 INCIDENT STATUS: NOT REPAIRED — ATTEMPT INCOMPLETE`,
  `J-11 MAINTENANCE BOUNDARY: ACTIVE`, `J-11 LIVE PRE-BOOT GUARD: ARMED`.
- [ ] If `STAGE E COMPLETE: YES`: the three populations from `docs/goal.md` step 5 are each reported by
  name with their own counts — (a) rows newly inserted for the 11 Stage-D-rebuilt runs, (b) rows newly
  filled on retained runs whose `measured_date` lands on an incident date, (c) the not-yet-mature
  combinations have zero `ForwardReturn` rows — proven by live read-only query, not asserted from a diff.
- [ ] If `STAGE E COMPLETE: NO`: the attempt stopped at the first failing check or mid-loop error with
  full evidence preserved, and the handoff states explicitly that any retry re-runs Stage E's own
  create-once loop (idempotent — never resumes from "the next unfinished run" as though state were lost,
  and never treated as requiring a full C→G restart, since Stage E performs no destructive delete).
- [ ] Zero `ScannerRun`/`ScannerResult`/`SectorScoreRow`/`ThemeScoreRow` rows created, deleted, or changed
  — proven by live read-only query (row counts and per-row identity fields) before and after.
- [ ] Zero `NextSessionManifest` rows created or changed: 24 rows before and after; the 4 incident-date
  rows byte/value-identical (`version`, `content_hash`, `manifest_hash`, `prospective_eligible`,
  `available_at_utc`, `source_run_id` unchanged) — proven live and read-only.
- [ ] No surviving pre-Stage-E `ForwardReturn` row is overwritten: a sampled set of rows outside the two
  hole populations is byte-identical before and after.
- [ ] Post-execution `COUNT(*) FROM forward_returns` minus the pre-execution count equals the execution
  module's own self-reported total inserted-row count exactly.
- [ ] Zero writes to `daily_prices`, `data_provider_runs`, `watchlist`, `maintenance_boundaries`, and every
  table outside `forward_returns` — proven by before/after full-table sweep plus the whole-file
  mtime/size/WAL bracket as the primary instrument.
- [ ] Live peak process memory during the execution is measured and recorded against the configured
  `memory_cap_mb`/`HOST_GUARD_MEMORY_HIGH` ceiling (AG-10), whichever bar-loading approach is chosen.
- [ ] Maintenance isolation held for the entire iteration — no application-service boot, no
  browser-qa-agent dispatch, no replay lane; the engine's refusal log is the evidence.
- [ ] Required-still-passing journeys J-01, J-04, J-10 are **not** re-verified via browser QA or replay
  this iteration (both are impossible under maintenance isolation); instead their canonical files
  (`app/api/*`, `scoring.py`, `sectors.py`, `compass.py`, `data_manager.py`'s J-10 recovery code) are
  proven untouched via `git status --porcelain -uall` grepped against that file set — the same method
  iteration 19's coherence audit used.
- [ ] Fixture-scoped unit/integration tests (never against the live database) pass for every scenario in
  TESTING REQUIREMENTS.
- [ ] No anti-goal violation introduced; the ledger stays at its current total with zero new unresolved
  entries.
- [ ] Dev handoff written at `docs/handoffs/goal-market-compass-iter-20-dev.md`.

## TESTING REQUIREMENTS

- **Browser:** none this iteration. `browser-qa-agent` does not run — maintenance isolation forbids
  application-service boot for the whole of J-11 through Stage G (`docs/goal.md` Loop mechanics, and the
  Stage D→G ruling's own item 4).
- **Unit/integration:** the new execution module's preflight-gate composition (including the fresh
  identity-equality check against Stage D's frozen value), the per-run loop's exclusive use of
  `backfill_run_forward_returns` (never `backfill_forward_returns`), the three-population classification
  and reporting, the shared bar-cache-context wiring, the mutation-accounting sweep, and the CLI script's
  `--confirm`/`--evidence-dir` gating — all fixture-scoped, reusing the isolated-engine pattern the
  sibling `test_j11_*` suites already use (`app.db.make_engine`, never the live `trendora.db`).
- **Error cases:** an `engine_identity` recomputed fresh that no longer equals Stage D's frozen value; a
  Stage-D-rebuilt run unexpectedly missing, restamped, or already carrying a `ForwardReturn` row; the
  maintenance boundary inactive or scope-drifted; a mid-loop failure on one run; a CLI invocation missing
  `--confirm`; a CLI invocation missing `--evidence-dir`; an accidental call to
  `forward_testing.backfill_forward_returns()`.

Test-first contract — scenarios:

- TC-1: given the live database in Stage D's certified post-regeneration end state (11 `INCIDENT_DATES`
  each carrying exactly one `ScannerRun`, ids and `engine_identity` recorded in
  `runs/goal-market-compass-iter-19/j11-stage-d-execute-regeneration.json` /
  `-frozen-identity.json`, each with zero `ForwardReturn` rows) and the `j11-incident-recovery`
  maintenance boundary `active=1` covering exactly `app.engine.j11_maintenance.INCIDENT_DATES`, when
  Stage E's fresh preflight step runs before any write, then it re-derives every one of these directly
  and read-only from the live database — never from a cached artifact — and additionally recomputes
  `engine_identity.compute_engine_identity(config)` fresh and asserts it equals the identity Stage D
  froze, reporting `passed: true` only if every value agrees.
- TC-2: given the fresh preflight detects any drift — a missing or restamped Stage-D-rebuilt run, a
  `ForwardReturn` row already present for one of the 11 incident-date runs, the boundary inactive or
  scope-drifted, or a recomputed `engine_identity` that no longer equals Stage D's frozen value — when
  the gate evaluates, then Stage E performs zero writes to any table, exits non-zero, and persists the
  exact blocking reason to the evidence directory.
- TC-3: given preflight passes, when the execution module runs its forward-return repair loop, then it
  iterates every row currently in `scanner_runs` (the full retained-plus-Stage-D-rebuilt population) in
  ascending `asof_date` order and calls `forward_testing.backfill_run_forward_returns(session, run,
  config)` once per row; a static/import-level test asserts `forward_testing.backfill_forward_returns`
  is never imported or called anywhere in the new module or its CLI script.
- TC-4: given the per-run loop completes, when `scanner_runs`/`scanner_results`/`sector_scores`/
  `theme_scores` are re-queried, then every row's identity, `asof_date`, and (for `scanner_runs`)
  `engine_identity` and `created_at` are byte-unchanged from the pre-Stage-E capture, and each table's
  row count is unchanged.
- TC-5: given the 11 Stage-D-rebuilt runs start with zero `ForwardReturn` rows, when Stage E completes,
  then each of the 11 carries exactly one `ForwardReturn` row per (`symbol`, horizon) pair where the
  horizon is elapsed (at least `horizon` trading days exist in `daily_prices` strictly after that run's
  `asof_date`) across the run's own resolved symbol set, and zero rows for any not-yet-elapsed horizon —
  the same `observable_horizons` rule `backfill_run_forward_returns` already applies to every other run.
- TC-6: given the pre-Stage-E population of `ForwardReturn` rows whose `measured_date` lands on one of
  the 11 incident dates but whose `run_id` belongs to a RETAINED (non-incident) run — first sized in
  Stage B's pre-reset inventory and untouched by Stage C/D — when Stage E completes, then a fresh grouped
  scan of that population shows a row present for every (retained run, symbol, horizon) combination
  whose horizon is now elapsed given the J-10/AVB-corrected raw bars, and the per-run count for that
  population never decreases from its pre-Stage-E value.
- TC-7: given a `ForwardReturn` row that existed before Stage E ran, sampled from outside the two hole
  populations in TC-5/TC-6, when Stage E completes, then that row's `run_id`/`symbol`/`horizon`/
  `realized_return`/`mae`/`mfe`/`max_drawdown`/`underwater_days`/`time_to_recover_days`/`measured_date`/
  `entry_close` values are byte-identical to their pre-Stage-E values.
- TC-8: given a (run, symbol, horizon) combination with fewer than `horizon` trading days available in
  `daily_prices` strictly after that run's `asof_date` even after J-10/Stage D's repairs, when Stage E
  completes, then no `ForwardReturn` row exists for that exact key.
- TC-9: given a before-capture and an after-capture of `j11_maintenance.capture_full_table_sweep`,
  bracketed by the whole-file mtime/size/WAL fingerprint at the true process start and end, when
  `diff_full_table_sweeps` compares them after the live run, then `changed_existing_tables` is a subset
  of `{forward_returns}` only, and `unexpected_new_tables`/`unexpected_removed_tables` are both empty.
- TC-10: given `next_session_manifests` holds 24 rows with the 4 incident-date rows at specific
  `version`/`content_hash`/`manifest_hash`/`prospective_eligible`/`available_at_utc`/`source_run_id`
  values before Stage E runs, when Stage E completes, then it still holds exactly 24 rows and every one
  of those six fields on the 4 incident-date rows is byte-identical to its pre-Stage-E value.
- TC-11: given AG-10's `memory_cap_mb`/`HOST_GUARD_MEMORY_HIGH` envelope, when the live Stage E execution
  runs (whichever bar-loading path — `prices.prefilled_bar_cache` or the default lazy per-symbol path —
  the developer selects), then the process's measured peak memory (read from `/proc/<pid>/status`
  `VmPeak`, the same method J-09 uses) is recorded in the evidence and is within the configured ceiling,
  and the dev handoff states which path was chosen and why.
- TC-12: given the per-run loop's own self-reported total inserted-row count (summed across every
  `backfill_run_forward_returns` call), when compared against `COUNT(*) FROM forward_returns` measured
  immediately before and immediately after the live run, then `after_count - before_count` equals that
  self-reported total exactly.
- TC-13: given the CLI script is invoked without `--confirm`, when it runs, then it performs zero
  database interaction (not even a read) and exits non-zero.
- TC-14: given the CLI script is invoked without an explicit `--evidence-dir`, when it runs, then it
  refuses before any config/engine construction and exits non-zero.
- TC-15: given a synthetic fixture database (never `trendora.db`) seeded with a Stage-D-shaped state —
  the 11 incident dates each carrying a `ScannerRun` with zero `ForwardReturn` rows, at least one
  retained run with a `ForwardReturn` hole whose `measured_date` lands on an incident date, at least one
  genuinely immature (run, symbol, horizon) combination, and an active `MaintenanceBoundary` row — when
  the fixture test suite runs the execution module end-to-end via `app.db.make_engine`'s isolated engine,
  then it reproduces TC-3 through TC-8's assertions without opening the real database file.
- TC-16: given the live execution has run to its conclusion (full success or a clean stop), when the dev
  handoff and evidence artifacts report status, then they state exactly `J-11 STAGE D EXECUTED: YES`,
  `J-11 STAGE E COMPLETE: YES` or `NO` matching the true outcome, `J-11 STAGE F COMPLETE: NO`,
  `J-11 STAGE G VERIFIED: NO`, `J-11 INCIDENT STATUS: NOT REPAIRED — ATTEMPT INCOMPLETE`,
  `J-11 MAINTENANCE BOUNDARY: ACTIVE`, and `J-11 LIVE PRE-BOOT GUARD: ARMED`.
- TC-17: given maintenance isolation is active for the whole iteration, when any lane other than
  developer/reviewer/file-scoped-QA/auditor attempts to run (application-service boot, browser-qa-agent,
  the deterministic replay lane), then the engine refuses the dispatch and logs the refusal.
- TC-18: given `daily_prices`, `scanner_runs`, `scanner_results`, `sector_scores`, `theme_scores`,
  `data_provider_runs`, `watchlist`, and `maintenance_boundaries` are all outside Stage E's authorized
  write scope, when the post-execution mutation accounting is inspected, then all eight show zero
  fingerprint change from the pre-execution capture.
- TC-19: given J-01/J-04/J-10's passing status each rest on the untouched content of `app/api/*`,
  `scoring.py`, `sectors.py`, `compass.py`, and `data_manager.py`'s J-10 recovery code, when
  `git status --porcelain -uall` is grepped against that exact file set after this iteration's changes
  are staged, then it returns zero matches.
- TC-20: given AG-9 forbids any live network call and every dated exception is exhausted, when the new
  execution module and CLI script are inspected, then zero network-capable call appears anywhere in the
  diff, and the live execution's evidence artifacts record zero outbound requests.

## NOTES

- **Assumption-ledger entries filed this iteration** (`runs/goal-session-market-compass/state/
  assumptions.md`): (1) scoping this iteration to Stage E alone rather than the full authorized D→G
  sequence, continuing iteration 19's precedent; (2) requiring the per-run `backfill_run_forward_returns`
  loop and forbidding `backfill_forward_returns()`'s whole-database entry point, resolving `docs/goal.md`
  step 5's side-by-side naming of both functions in favor of the one with no out-of-scope write side
  effect.
- **Live figures cited above are this planning pass's own read-only spot-check (2026-08-26)** — current
  `scanner_runs` count 3128, `forward_returns` count 6797728, zero `forward_returns` rows for run ids
  3148–3158, exactly one `maintenance_boundaries` row (`j11-incident-recovery`, `active=1`) — cited for
  continuity only. Per this session's own established discipline, the developer must re-derive every one
  of these live and fresh rather than trust this citation.
- **Operational recommendation:** keep `run-goal.sh`'s pump running continuously with
  `CHAIN_MAINTENANCE_ISOLATION=true` and `CHAIN_REQUIRE_FULL_DEPTH=true` set across this iteration AND the
  subsequent Stage F/G iterations until `J-11 STAGE G VERIFIED: YES` — unchanged from iteration 19's own
  recommendation.
- **Escalation flag:** if the fresh preflight step finds ANY drift from Stage D's certified end state —
  most importantly a recomputed `engine_identity` that no longer equals Stage D's frozen value — the
  developer must STOP before any write and report the exact blocker; per the ruling's item 2, an identity
  drift makes the whole D→G attempt **incomplete**, and Stage E must not paper over it by proceeding
  under the new value.
- **For a future Stage G iteration's decomposer (not actionable this iteration):** the owner's Stage G
  membership rule requires verifying Stage-D attempt membership using the canonical 11 incident dates
  PLUS the recorded Stage-D run ids (3148–3158, per `runs/goal-market-compass-iter-19/
  j11-stage-d-execute-regeneration.json`) and execution evidence — never inferred from `engine_identity`
  alone, since `compute_engine_identity` is mathematically forced to equal several historical readiness
  values and cannot alone distinguish this attempt's runs from a future runless-date write (auditor
  finding B1, iteration 19).
- If the reviewer, QA, or auditor lane finds that live execution cannot proceed safely for any reason not
  anticipated above, the correct action is the same as every prior J-11 stage in this session: stop,
  preserve evidence, and report — never force a write past a failing check to obtain a "complete" status.
