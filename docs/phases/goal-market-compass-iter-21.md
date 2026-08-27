# Goal Iteration 21 — J-11 Stage F: dependency-aware derived-cache invalidation

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** market-compass
- **Iteration:** 21
- **Mode:** next
- **Depth:** full
- **Full trigger:** 1 — Stage F's correctness spans seven cache tables across `research.py`,
  `data_manager.py`, `forward_testing.py`, and the Stage D/E preflight-reuse chain
  (`j11_stage_d_execute.py`, `j11_stage_e_execute.py`, `j11_maintenance.py`), on a live, irreversible
  database write, and no single journey's test suite covers this interaction. This planning pass itself
  found a real, previously-unreported correctness risk — `data_manager.availability_from_storage`'s
  "no ingest job in flight" branch (`:1741-1747`, `:1760-1763`) serves a stamp-mismatched
  `AvailabilityCache` row **unflagged as stale** (`stale: False`) — that would make the first
  `GET /api/data/availability` after Stage G reboot display pre-incident coverage figures as current.
  This also matches the evaluator's binding `full` recommendation; no escape condition was needed.
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
    from the post-decompose gate. (This cycle introduces no Evidence Claims — the gate passes
    automatically.) *(critical)*
  - **AG-7:** No hard-coded credentials, API keys, or tokens in source files. *(critical)*
  - **AG-8 — Resilience to data-shape and data-scale change:** widening the data basis must never crash
    an existing page or exhaust memory — consumers of widened fields are re-validated, the UI degrades
    gracefully (contained error boundary, honest "—"/NA placeholder), and unbounded whole-table ORM
    loads are forbidden (the delta engine reads column-projected selects, never full record_json
    sweeps). *(critical)*
  - **AG-9 — Offline-deterministic ingest:** ingest jobs run only against the committed seed / local
    provider fixtures — no live external network calls or paid data services without an explicit
    goal.md amendment. *(critical)* All three dated exceptions (J-10 recovery fetch, its vendor
    addendum, the AVB diagnostic fetch #2) are **exhausted** and none applies here; Stage F authorizes
    **no** network fetch of any kind (full exception text on record in `docs/goal.md`, not reproduced —
    it does not bear on a cache-row-only iteration).
  - **AG-10 — Host resource ceiling (hardware protection), carried from ops-hardening:** heavy compute
    MUST be launched only via the project launch scripts, which MUST apply the host caps declared in
    `project-extensions/host-guard/host-guard.env` whenever present (CPU-affinity mask, BLAS/OMP thread
    caps) plus the `config.yaml` `server.memory_cap_mb` / `malloc_arena_max` values. Never remove,
    weaken, or bypass these caps; stripping a HOST-GUARD marked block from a launch script is a
    REGRESSION regardless of test outcomes. The ceiling VALUES are an owner-set envelope (current:
    `memory_cap_mb` 8192, `HOST_GUARD_MEMORY_HIGH` 12G); only the owner may change them. *(critical)*
  - **AG-11 — No new composite candidate number:** no "fit", "conviction", "match", "probability of
    success", or any new blended score may be attached to candidates, the market, or the manifest;
    candidate presentation is limited to the existing three scores/buckets, config word maps, and
    structured reason/caution codes. *(critical)*
  - **AG-12 — Manifest immutability:** a stored `next_session_manifests` row and its exported file are
    never mutated or deleted by any later ingest, rebuild, data removal, config change, or code change;
    corrections happen only as new version rows; a historical view never substitutes a newer manifest.
    *(critical)*
  - **AG-13 — System-vs-market separation:** readiness/preflight vocabulary (Ready, Initializing,
    Backend unavailable, GO, DEGRADED, NO-GO) must never label market state, and regime/phase
    vocabulary must never label system state; the manifest's market and narrative blocks must contain
    no readiness tokens. *(critical)*
  - **AG-14 — No Tapeology coupling:** no imports from, network calls to, or writes into the tapeology
    repository or its services; the handoff is exclusively the local exported artifact and Trendora's
    own served API. *(critical)*
  - **AG-15 — No outcome-tuned selection:** the selection rule and its thresholds must not be chosen or
    revised from realized forward returns within this goal; no Evidence Claim is introduced for it; any
    future selection-edge claim goes through the pre-registration registry and referee. *(critical)*
  - **AG-16 — Cohorts are not controls:** the comparison cohort and the near-threshold shadow cohort are
    frozen non-selected pools, not matched or causal control groups; no surface, artifact, or narrative
    may present candidate-vs-cohort differences as causal, as expectancy, or as a certified edge; any
    incremental-value or threshold study over these cohorts requires its own pre-registered experiment
    in a future goal, consuming only manifests with `prospective_eligible: true`. *(critical)*
  - **AG-17 — Repair never rewrites provenance (owner, 2026-08-20):** restoring deleted historical data
    MUST NOT retroactively change research provenance. A manifest that was retrospective or ineligible
    stays that way; `prospective_eligible` is never upgraded merely because historical data was later
    repaired; `available_at_utc`, manifest versions, `content_hash`/`manifest_hash`, and prior
    eligibility classifications remain immutable. Any manifest or artifact produced while the database
    was known to be damaged — everything dated from the iter-5 drill until **J-11 Stage G** passes —
    **remains marked unusable as prospective/out-of-sample evidence**; nothing is retroactively marked
    prospective merely because raw bars were repaired in J-10 or derived snapshots were regenerated in
    J-11. Repairing the database never rewrites historical causality. *(critical)*
  - **AG-18 — The authorized manifest migration preserves everything (owner, 2026-08-23):** the bounded
    `next_session_manifests` schema migration authorized in J-11 step 11 removes the `source_run_id`
    foreign-key constraint and **nothing else**; no manifest may be regenerated, rebound, rehashed,
    upgraded, deleted, or newly minted by it or around it. *(critical)* (The iter-11 bounded-exception
    residual detail is on record in `docs/goal.md`; not reproduced here — Stage F never touches
    `next_session_manifests`.)

## GOAL

Execute the owner-authorized J-11 Stage F: classify every derived-cache table the incident-repair
sequence could have made stale, and explicitly clear the ones a live, evidence-grounded reading proves
are actually at risk — so nothing in this database can silently serve pre-repair content once the app
eventually reboots — while touching no raw price, snapshot, or manifest row.

## BACKGROUND

Iteration 19 executed J-11 Stage D live and cleanly (11 `INCIDENT_DATES`, `ScannerRun` ids 3148–3158, one
frozen attempt identity `53d2ffd10cdbf89ef16681111bd900766e00e5809bc4ebc7d4b5f2bf1b7f6c55`). Iteration 20
executed Stage E live and cleanly (16,592 `ForwardReturn` rows filled on the 11 rebuilt runs;
`forward_returns` 6,797,728 → 6,814,320; `scanner_runs` unchanged at 3,128; population (b) — holes on
retained runs — is structurally zero, not a missing repair, per iteration 20's own re-derivation of
`data_manager._cascade_targets`/`remove_price_data`, carried forward as binding for Stage G). Both were
independently re-verified by the evaluator against the live database. `docs/goal.md`'s "OWNER RULING —
J-11 Stage D through Stage G recovery execution AUTHORIZED" item 8 already authorizes Stage F
**unconditionally following a successful Stage E** — no further owner instruction is required to begin
it, and this spec does not amend `docs/goal.md`.

This spec scopes iteration 21 to **Stage F alone**, continuing the one-stage-per-iteration discipline
iterations 19 and 20 established and logged (assumption-ledger entries filed below): Stage G (the full
verification/acceptance gate — the only stage that may declare the incident repaired) remains for a
later iteration.

**What step 6 requires.** `docs/goal.md` J-11 step 6 requires classifying every cache that depends
directly or transitively on `scanner_runs`/`scanner_results`/`sector_scores`/`theme_scores`/
`forward_returns`, "deriving the set from the current models rather than copying" its own seven-item
list, and assigning each ONE of three dispositions: (1) its key is guaranteed to change and cleanly
invalidates; (2) explicitly delete the affected rows; or (3) explicitly regenerate through the canonical
producer — "prove it unaffected and leave it alone" is the fourth legitimate outcome for a cache proven
data-independent of anything J-11 touched. Ruling item 8 additionally forbids "unrelated rebuild, broad
application initialization or ordinary backend boot ... merely to perform Stage F."

**This planning pass independently re-derived the classification rather than trusting the goal text's
own list or the model classes' own docstrings — several were found stale or a materially incomplete
guide, and the findings below are the substantive reason this iteration needs full depth (trigger 1).**

1. **The seven-table inventory is confirmed exhaustive today (2026-08-27), by grep, not by citation.**
   `grep -n "dataset_version: str" apps/backend/app/models.py` returns exactly seven hits across exactly
   25 table classes: `EventStudyCache` (`:456`, key field `:468`), `MarketPhaseCache` (`:502`, `:509`),
   `ForwardAggregateCache` (`:556`, `:564`), `IndexSeriesCache` (`:618`, `:626`),
   `MembershipTimelineCache` (`:706`, `:712`), `AvailabilityCache` (`:759`, `:765`), `CoverageSnapshot`
   (`:945`, `:952`). No new cache table has been added since the goal text's 2026-08-21 writing. Stage F
   must re-run this same grep fresh, not trust this count.
2. **Two keying families, confirmed at each table's actual writer call site — not from class docstrings:**
   - **Broad `research._dataset_version(session)`** (`research.py:2517-2532`,
     `f"r{max(scanner_runs.id)}-f{count(forward_returns)}"`): `event_study_cache`
     (`event_study_cached`, `research.py:2591+`), `market_phase_cache` (`market_phase_cached`,
     `research.py:~3126`), `forward_aggregate_cache` (`forward_aggregates_ingest_cached`,
     `forward_testing.py:1511`, confirmed `version = _dataset_version(session)` at `:1570`).
   - **Narrow `research._membership_dataset_version(session, config)`** (`research.py:2535-2583`,
     folds in `max(scanner_runs.id)`, `count(scanner_runs)`, `max(daily_prices.date)`,
     `count(daily_prices)`, `config.indicators.min_history_bars` — deliberately excludes
     `forward_returns` so a warm-up forward-return insert never re-triggers the O(dates × pool)
     membership resolver, iter-42/J-100): `membership_timeline_cache` (`membership_timeline_cached`,
     `data_manager.py:854`, `version = _membership_dataset_version(session, cfg)` at `:884`),
     `availability_cache` (`availability_cached_with_status`, `data_manager.py:1640`, same call at
     `:1660`), `coverage_snapshot` (`coverage_from_storage`, `data_manager.py:1500`, same call at
     `:1536`).
   - **`index_series_cache`** keys on its OWN narrow stamp scoped only to the configured
     `index_chart.symbols` ETFs' bars (`d{max_date}-c{count}` shape) — independent of both stamps above.
   - **A stale docstring, found and worth flagging so nobody re-derives it the hard way:**
     `MembershipTimelineCache`'s own CLASS-level prose docstring (`models.py:672-704`) still asserts the
     table is keyed on the broad `research._dataset_version` ("single-sourced with J-72 / J-87 ... the
     forward-return row count") — true when the class was first written, **false today**. The FIELD-level
     comment two lines above it (`:712`), the actual writer at `data_manager.py:884`, and
     `AvailabilityCache`'s own (later, accurate) docstring all agree the real key has been the narrow
     `_membership_dataset_version` since iter-42/J-100. Trust the field comment and the call site, never
     the class prose, for this one table.
3. **Live evidence (this planning pass's own read-only spot-check, 2026-08-27 — re-derive fresh, do not
   copy): every currently-stored cache row is already unreachable under the live post-Stage-E stamps —
   no collision exists today.** Current live stamp inputs: `max(scanner_runs.id)=3158`,
   `count(scanner_runs)=3128`, `count(forward_returns)=6814320`, `max(daily_prices.date)=2026-08-12`,
   `count(daily_prices)=3310374`, `min_history_bars=200` (`config.yaml:656`) ⇒ broad stamp
   `r3158-f6814320`, narrow stamp `r3158-rc3128-b2026-08-12-bc3310374-h200`. Stored rows: `event_study_
   cache` 18 rows (highest stored stamp `r3150-f6800539`), `market_phase_cache` 1,290 rows (highest
   `r3150-f6800539`), `forward_aggregate_cache` 333 rows (highest `r3150-f6800539`),
   `membership_timeline_cache`/`availability_cache`/`coverage_snapshot` — 1 row each, all three sharing
   `r3150-rc3121-b2026-08-12-bc3310374-h200` — every one strictly below the live values on both the
   `r`/`rc` terms (Stage D's net +7 `scanner_runs` rows across the 11 incident dates and Stage E's
   forward-return fill both moved past every stored stamp). `index_series_cache` holds 1 row at
   `d2026-08-12-c60699`, unaffected because `daily_prices` is byte-unchanged (already proven by Stage D's
   and Stage E's own mutation accounting).
4. **A real correctness risk this planning pass found, not merely a theoretical stamp-collision worry
   (the substantive reason this iteration is not a no-op).** `data_manager.availability_from_storage`
   (`:1711-1763`, `GET /api/data/availability`'s actual serving path) has FOUR cases on a stamp mismatch;
   the one that matters here is `:1741-1747`/`:1760-1763`: **"a row exists, its stamp does not match the
   current one, but no ingest job is in flight" → serve the SAME stale stored row with `stale: False`.**
   This is correct behavior for its designed case (an ordinary stamp bump with nothing running to chase
   it — ops-hardening iter-58's own B2 fix). It is **not** correct for J-11: once the app reboots after
   Stage G with no ingest job running, the very first availability request would silently serve the
   **pre-incident** heatmap — missing/wrong cells for the 11 incident dates — labeled current. Leaving
   `availability_cache`'s stale row in place is therefore a live AG-3/AG-8 risk, not a hygiene question.
   `coverage_from_storage` (`data_manager.py:1500-1554+`) has an analogous stale-serving fallback but
   labels it honestly (`coverage_status: "stale"`) and additionally self-heals an explicit `?as_of=` for
   an already-real `ScannerRun` — materially safer, but still a table Stage F must classify, not skip.
5. **A tradeoff this planning pass could not fully resolve and deliberately leaves to Stage F's own
   verification, rather than guessing.** `membership_timeline_cached`'s own MISS-repair logic
   (`data_manager.py:894-963`) opportunistically reuses the **most recent row of ANY stamp** (not the
   version-matched one) to run a cheaper incremental refresh instead of `_membership_timeline`'s full
   O(dates × pool) resolver sweep — the same sweep its own docstring says "made the endpoint hang >300s"
   on a DB this size. Deleting the stale row removes that fallback's only input, forcing the next real
   request onto the expensive, previously-hang-inducing cold path on a host that has already frozen once
   from memory pressure (`docs/goal.md` Constraints, "Host resource-fit"). See IN SCOPE for the required
   disposition and its proof obligation.

**Lessons applied** (from `lessons.md`): iter-20's audit finding (relayed by the coordinator) that three
of Stage E's own verification checks were tautological or vacuous by construction
(`population_a_pre_was_zero`, `population_b_never_decreased` over a structurally-empty pre-map,
`population_c_latest_run_observable_ceiling_respected`) governs every boolean this iteration's module
computes — see DEFINITION OF DONE and TC-16. Iter-15b's "never trust a single fingerprint alone" governs
the classification design directly: every cache's disposition is proven by BOTH a live-recomputed
dataset-version-stamp comparison AND an independent `created_at`-vs-Stage-D-start comparison (see IN
SCOPE), never the stamp string alone. Iter-14b/18's "open the cited call site, never the docstring or a
hand-built enumeration" is exactly how finding 2 above (the stale `MembershipTimelineCache` docstring)
and finding 4 (the `availability_from_storage` risk) were made. Iter-19's "a successful rebuild can move
the danger, not remove it" governs this whole iteration's premise: Stage D/E succeeding is precisely what
makes six of the seven caches stale.

Depth is `full`, matching the evaluator's binding recommendation for this iteration (0 consecutive lean
iterations dispatched, so no hardening-cadence trigger is even needed independently). This spec
deliberately does **not** set a `Maintenance isolation:` or `Depth enforcement:` metadata line — those
are operator-only controls, and a self-written safety declaration here would be exactly the
governor-bypass anti-pattern 25 describes. Independently of this spec, `docs/goal.md`'s Stage D→G ruling
item 13 requires the human dispatching this run to supply `CHAIN_MAINTENANCE_ISOLATION=true` and
`CHAIN_REQUIRE_FULL_DEPTH=true` as required launch conditions for the whole D→G execution — this is a
live-database-write iteration under that same ruling, unchanged since iteration 19.

**Resource discipline (AG-10, and the 2026-08-20 host-freeze incident carried in `docs/goal.md`
Constraints).** Stage F's own authorized write (row deletion, at most ~1,644 rows total across six small
tables) is cheap and bounded on its own. The real memory/host risk this spec guards against is the
OPPOSITE temptation — eagerly regenerating any of the seven caches through their canonical producer
"while we're here" (disposition 3). That is explicitly OUT OF SCOPE: `_membership_timeline`'s documented
>300s hang risk on this exact DB size is reason enough to defer all regeneration to the existing,
already-built, already-safe path (the normal ingest-finalize/boot-warmup warm, which runs only after
Stage G, when the app is genuinely allowed to boot).

## IN SCOPE

### Backend

- [ ] New module `apps/backend/app/engine/j11_stage_f_execute.py`:
  - Fresh, read-only preflight, reusing existing functions directly (never reimplemented):
    `j11_stage_d_execute.recheck_maintenance_boundary_and_guard` (boundary/guard); a new
    `confirm_stage_e_complete_and_unrestamped` check (per incident date: the Stage-D-rebuilt run is
    present, unrestamped — same id, same `asof_date`, same frozen `engine_identity` — AND its
    `ForwardReturn` row count matches Stage E's own recorded per-run-id outcome in
    `runs/goal-market-compass-iter-20/j11-stage-e-execute-population-report.json` exactly, including run
    3158's own recorded value of 0 — a legitimate not-yet-mature outcome, never treated as a gap);
    `j11_stage_e_execute.check_engine_identity_matches_stage_d` (reused as-is, called with the same
    frozen `53d2ffd1…` value) for a fresh identity-drift check; `j11_stage_e_execute.
    confirm_manifests_unchanged` (reused as-is) against the same certified iter-16 baseline. Combined by
    a `stage_f_preflight_gate_verdict` mirroring `stage_e_preflight_gate_verdict`'s shape.
  - `derive_cache_table_inventory()`: introspects `app.models` at run time for every SQLModel table
    carrying a `dataset_version` field — never a hardcoded list — and reports it explicitly (the run must
    not silently proceed if the count differs from the seven confirmed at planning time).
  - `classify_cache_table(session, ...)`, called once per inventoried table: recomputes the table's
    CURRENT live stamp via its actual writer/version function (not a docstring), reads every DISTINCT
    stored `dataset_version` value, and reads every stored row's `created_at`. Compares against Stage
    D's frozen execution-start instant (`2026-08-26T10:52:55.552946Z` per the iteration-state digest —
    re-derive fresh from `runs/goal-market-compass-iter-19/j11-stage-d-execute-*.json` AND cross-check
    against a live `MIN(created_at)` over `scanner_runs` where `id` in 3148–3158; never hardcode the
    citation). Produces a disposition record naming: `stamp_matches_live` (bool per stored distinct
    stamp), `all_rows_created_before_stage_d_start` (bool — a hard hygiene precondition for these six
    tables; see below), and the chosen disposition with a stated reason.
  - Disposition defaults this module must apply, each with its own proof obligation (not merely
    asserted): **`event_study_cache`, `market_phase_cache`, `forward_aggregate_cache`,
    `coverage_snapshot`, `availability_cache`** → `explicit_delete` of every row whose stamp does not
    match the fresh live one (today, that is every row in each table) — required outright for
    `availability_cache` (BACKGROUND finding 4: its own serving function would otherwise serve stale
    figures unflagged as current the first time `/data` loads post-reboot); required by default for the
    other four unless the developer's own reading of their actual serving functions finds an equally
    concrete reason to prefer otherwise (documented in the handoff, mirroring the rigor of finding 4).
    **`index_series_cache`** → `prove_unaffected_leave_alone`: re-derive its own narrow stamp fresh and
    confirm it still equals the one stored row's stamp (corroborated by `daily_prices` proven
    byte-unchanged by Stage D's/Stage E's own mutation accounting) — zero write. **`membership_timeline_
    cache`** → the decomposer's recommended default is `preserve_for_incremental_reuse` (do NOT delete),
    specifically to leave `membership_timeline_cached`'s own MISS-repair fast path
    (`data_manager.py:894-963`) able to run its cheaper "historical gap-insert" branch instead of forcing
    the next real request onto the documented >300s full cold-compute path — but ONLY if this module
    first proves, live and read-only, that the existing fast-path logic would take that safe branch (not
    the narrower "append-forward" branch) for the actual stale row's cached date list against the
    current live snapshot-date set (`append_forward` requires `min(new_dates) > prev_dates[-1]`; the
    newly-run incident dates span 2026-05-12 through 2026-08-03, which are not later than the existing
    history's tail, so this should evaluate `False` — prove it against the live payload, do not assume
    it). If that proof cannot be established with confidence, fall back to `explicit_delete` for this
    table too and record the tradeoff explicitly in the handoff — never leave the question unresolved.
  - `execute_stage_f_cache_disposition(session, dispositions)`: the ONE authorized write — deletes
    exactly the rows already classified stale in tables landing on `explicit_delete`; zero write to any
    other table.
  - `live_verify_cache_dispositions`: post-write, read-only — deleted tables hold zero rows (or only
    rows matching the live stamp, which should not occur since the app stayed off throughout); preserved
    tables (`index_series_cache`, and `membership_timeline_cache` if preserved) are row-count-unchanged.
  - `build_stage_f_mutation_accounting`, mirroring `j11_stage_e_execute.build_stage_e_mutation_
    accounting`'s composition idiom (reuses `j11_maintenance.capture_full_table_sweep`/`diff_full_table_
    sweeps`): `changed_existing_tables` must be a subset of exactly the tables classified
    `explicit_delete`; `daily_prices`, `scanner_runs`, `scanner_results`, `sector_scores`, `theme_scores`,
    `forward_returns`, `data_provider_runs`, `watchlist`, `maintenance_boundaries`,
    `next_session_manifests`, `index_series_cache`, and any cache classified preserved all show zero
    fingerprint change.
  - `stage_f_execution_outcome`, mirroring `stage_e_execution_outcome`'s "no third state" shape exactly.
  - Memory measurement reused as-is: `j11_stage_e_execute.read_process_vm_peak_kb` /
    `build_memory_check` against `server.memory_cap_mb`.
- [ ] New CLI script `apps/backend/scripts/run_j11_stage_f_execute.py`, mirroring `run_j11_stage_e_
  execute.py`'s `--confirm`/`--evidence-dir` gating exactly (refuses any DB interaction without
  `--confirm`; refuses before config/engine construction without `--evidence-dir`).
- [ ] New tests `apps/backend/tests/test_j11_stage_f_execute.py` and
  `apps/backend/tests/test_j11_stage_f_execute_cli_script.py` — fixture-scoped only (`app.db.make_engine`
  isolated engine), never against `apps/backend/data/trendora.db`.
- [ ] Dev handoff records, per cache table, the disposition chosen and the live/fixture evidence backing
  it — explicitly including the `availability_cache` correctness finding and the `membership_timeline_
  cache` incremental-reuse proof (or its fallback to deletion if the proof did not hold).

### New user-facing capability
None — backend-only maintenance; no page, route, or UI element changes this iteration.

### New information displayed
None.

### New user actions
None.

### UI surface changes
None.

### Product surface delta
None this iteration. (The seven caches Stage F classifies back `/backtest`, `/research`, and `/data`
surfaces that predate this session and are blocked from normal use until Stage G passes regardless;
Stage F needs no surface of its own, matching J-11's "Walkthrough: waived" status in `docs/goal.md`.)

### Blueprint conformance
No new surfaces. `runs/goal-session-market-compass/state/blueprint.md` is **not** edited this iteration
— nothing to register. The seven cache tables' underlying computations (`compute_event_study`,
`compute_market_phase`, `compute_forward_aggregates`, `_membership_timeline`, `compute_availability`,
`_compute_coverage_uncached`, `compute_index_series`) are unchanged, pre-existing (from `ops-hardening`),
not tracked Data Contract rows in this session's blueprint, and this iteration adds no new one — Stage F
manages cache ROWS only, never a computing module or a serving endpoint (mirroring iteration 19's and
20's identical conclusion for the identical reason).

### Data-contract additions
None.

## OUT OF SCOPE

- Stage G (the full verification/acceptance gate) — deferred to a later iteration (scoping decision
  logged to `assumptions.md`).
- Eagerly regenerating/warming ANY of the seven caches through their canonical producer this iteration
  (disposition 3) — see BACKGROUND's resource-discipline note; regeneration is deferred to the existing,
  already-safe normal warm-up path that runs after Stage G.
- Modifying any canonical producer or serving function
  (`compute_event_study`/`event_study_cached`, `compute_market_phase`/`market_phase_cached`,
  `compute_forward_aggregates`/`forward_aggregates_ingest_cached`, `_membership_timeline`/
  `membership_timeline_cached`, `compute_availability`/`availability_cached_with_status`/
  `availability_from_storage`, `_compute_coverage_uncached`/`coverage_from_storage`,
  `compute_index_series`) — Stage F composes and reads them as-is; it introduces no second
  implementation and changes no serving logic, only cache-table rows.
- Any write to `daily_prices`, `scanner_runs`, `scanner_results`, `sector_scores`, `theme_scores`,
  `forward_returns`, `next_session_manifests`, `data_provider_runs`, `watchlist`,
  `maintenance_boundaries` — Stage F's only authorized write target is the subset of the seven
  `dataset_version`-bearing cache tables landing on `explicit_delete`.
- Freezing a new attempt identity — Stage F cites Stage D's frozen identity for provenance/comparison
  only.
- Deactivating or clearing the `j11-incident-recovery` maintenance boundary — forbidden until Stage G
  passes; it must remain `active=1` at the end of this iteration, whatever the outcome.
- Re-running or re-verifying Stage D or Stage E's own destructive/write steps — already DONE, verified
  live ("do not redo" per the iteration-state digest); this iteration's preflight only re-**verifies**
  their end state, read-only.
- Any provider/network fetch — AG-9 remains closed; no dated exception applies to Stage F.
- The ordinary request-path guard gap (`scanner.resolve_run`) and the Data Manager write-path guard gap
  — recorded-but-deferred by the Stage D→G ruling (item 5) to post-Stage-G hardening work.
- Any J-01–J-09 product/UI work, and specifically J-07/J-08 — blocked by the Loop-mechanics gate until
  Stage G passes.
- Application-service boot, browser-qa-agent, the deterministic replay lane, a second backend or frontend
  process — all OFF for the whole iteration (maintenance isolation).
- Any schema/DDL migration — none authorized or needed; this is a pure row-delete operation on tables
  whose schema is unchanged.
- Any goal-mode framework change — including any proposal to fix `goal_gate.py`'s duplicate-journey
  defect or the journey-history-hash/stall-window mechanics; the owner has explicitly deferred both until
  after Stage G, and neither is scoped to this iteration.
- Running the full pytest suite, or opening `apps/backend/data/trendora.db` for write from any test.
- Restamping, mutating, or otherwise touching the 11 Stage-D-rebuilt runs or any other `ScannerRun`.

## DEFINITION OF DONE

- [ ] Fresh preflight (boundary/guard recheck reused directly; all 11 Stage-D/E incident runs present,
  unrestamped, and carrying a `ForwardReturn` count matching Stage E's own recorded per-run-id outcome
  exactly; a live-recomputed `engine_identity` equal to the frozen `53d2ffd1…` value; the 24-row manifest
  dump unchanged vs. the certified iter-16 baseline) is re-derived live and read-only immediately before
  any write; the attempt proceeds only if every check agrees — otherwise it STOPs with the exact blocker
  named and zero writes performed.
- [ ] The exhaustive set of `dataset_version`-bearing tables is re-derived from `app.models` at run time
  (never hardcoded) and the run reports explicitly whether it matches the seven confirmed at planning
  time or found a different count.
- [ ] Every one of the seven tables receives one documented, evidence-backed disposition: the actual
  writer/version function used (verified by reading the call site, never a class docstring alone), the
  live-recomputed stamp, every distinct stored `dataset_version` value, and every stored row's
  `created_at` compared against Stage D's frozen execution-start instant.
- [ ] For the six tables whose stamp depends on `scanner_runs` and/or `forward_returns`: every currently
  stored row's `created_at` is proven earlier than Stage D's frozen execution-start instant — an
  unexplained row at or after that instant halts the iteration and is reported as a maintenance-isolation
  breach, never silently deleted or silently accepted.
- [ ] `event_study_cache`, `market_phase_cache`, `forward_aggregate_cache`, `coverage_snapshot`, and
  `availability_cache` end the iteration with zero rows carrying a pre-Stage-F stamp (today, that means
  zero rows total in each, proven by a live post-write `COUNT(*)`).
- [ ] `index_series_cache` ends the iteration with its one row untouched, and the dev handoff records the
  fresh re-derivation proving its stamp still equals the stored value.
- [ ] `membership_timeline_cache`'s disposition (preserve-for-incremental-reuse or explicit-delete) is
  chosen only after the live proof described in IN SCOPE is attempted and its result recorded either way
  — never defaulted without that proof attempt on record.
- [ ] The one authorized write touches only tables classified `explicit_delete`, deleting exactly the
  rows already proven stale — zero rows deleted from any table classified otherwise, and zero write to
  any table outside the seven-table cache family.
- [ ] No canonical producer or serving function's code is modified (see OUT OF SCOPE) — Stage F manages
  rows only.
- [ ] Post-execution mutation accounting proves `changed_existing_tables` is a subset of exactly the
  tables classified `explicit_delete`; every other table in the database (the ten named in OUT OF SCOPE
  plus every cache table not classified `explicit_delete`) shows zero fingerprint change.
- [ ] A fixture-scoped test reproduces `docs/goal.md`'s own named risk — a delete-and-recreate of
  `scanner_runs`/`forward_returns` engineered to reproduce a byte-identical `dataset_version` stamp — and
  proves the module's classification logic detects it (via the `created_at` check, since a pure
  stamp-string match cannot by itself distinguish a coincidental collision from a genuine fresh compute)
  and still prevents a stale payload from being served under that stamp.
- [ ] No verification check in the new module can pass by construction: every boolean in
  `stage_f_preflight_gate_verdict` / the classification functions / `build_stage_f_mutation_accounting` /
  `stage_f_execution_outcome` is traceable to a live- or fixture-derived value that could plausibly
  disagree — the reviewer explicitly checks this against iteration 20's three named tautological checks
  (`population_a_pre_was_zero`, `population_b_never_decreased` over a structurally-empty map,
  `population_c_latest_run_observable_ceiling_respected`) and records the comparison in the review.
- [ ] The attempt ends in exactly one of item 14's two states; the dev handoff states the outcome using
  its exact vocabulary: `J-11 STAGE D EXECUTED: YES`, `J-11 STAGE E COMPLETE: YES`,
  `J-11 STAGE F COMPLETE: YES/NO`, `J-11 STAGE G VERIFIED: NO`,
  `J-11 INCIDENT STATUS: NOT REPAIRED — ATTEMPT INCOMPLETE`, `J-11 MAINTENANCE BOUNDARY: ACTIVE`,
  `J-11 LIVE PRE-BOOT GUARD: ARMED`.
- [ ] Live peak process memory during the execution is measured and recorded against the configured
  `memory_cap_mb`/`HOST_GUARD_MEMORY_HIGH` ceiling (AG-10).
- [ ] Maintenance isolation held for the entire iteration — no application-service boot, no
  browser-qa-agent dispatch, no replay lane; the engine's refusal log is the evidence.
- [ ] Required-still-passing journeys J-01, J-04, J-10 are **not** re-verified via browser QA or replay
  this iteration (impossible under maintenance isolation); instead their canonical files (`scoring.py`
  for J-01, `compass.py` for J-04, `data_manager.py`'s J-10 recovery code for J-10) are proven untouched
  via `git status --porcelain -uall` grepped against that exact file set — the same method iterations 19
  and 20 used. Stage F's own new/modified files are exactly the ones named in IN SCOPE — no existing
  engine module's source changes.
- [ ] Fixture-scoped unit/integration tests (never against the live database, never the full suite) pass
  for every scenario in TESTING REQUIREMENTS.
- [ ] No anti-goal violation introduced; the ledger stays at its current total (7) with zero new
  unresolved entries.
- [ ] This iteration's new files and evidence folder are committed to git before scoring — confirm
  `git status --short` shows nothing under `apps/backend/app/engine/j11_stage_f_execute.py`,
  `apps/backend/scripts/run_j11_stage_f_execute.py`, `apps/backend/tests/test_j11_stage_f_execute*.py`,
  or `runs/goal-market-compass-iter-21/` left untracked (iterations 19 and 20 were both flagged for this
  at scoring time; this iteration closes that pattern rather than repeating it a third time).
- [ ] Dev handoff written at `docs/handoffs/goal-market-compass-iter-21-dev.md`.

## TESTING REQUIREMENTS

- **Browser:** none this iteration. `browser-qa-agent` does not run — maintenance isolation forbids
  application-service boot for the whole of J-11 through Stage G.
- **Unit/integration:** cache-table inventory derivation; per-table classification (live-stamp
  recomputation via the actual writer call site, distinct stored stamps, the `created_at`-vs-Stage-D-start
  comparison); the deletion action scoped exactly to classified rows; the `membership_timeline_cache`
  incremental-reuse proof; mutation accounting; the outcome verdict; the CLI script's
  `--confirm`/`--evidence-dir` gating — all fixture-scoped, reusing the isolated-engine pattern the
  sibling `test_j11_*` suites already use (`app.db.make_engine`, never the live `trendora.db`).
- **Error cases:** a stamp collision a pure string comparison cannot resolve (must fall back to the
  `created_at` check); a row with `created_at` at or after Stage D's frozen start instant (an unexplained
  write — must halt the whole attempt, never be silently deleted or accepted); the boundary/guard/identity/
  manifest preflight drifted; a Stage-D/E run unexpectedly missing, restamped, or with a `ForwardReturn`
  count that does not match Stage E's recorded outcome; the live model inventory reports an eighth
  `dataset_version`-bearing table not in the planning-time list of seven; a CLI invocation missing
  `--confirm`; a CLI invocation missing `--evidence-dir`; a mid-loop failure deleting one table's rows.

Test-first contract — scenarios:

- TC-1: given the live database in Stage E's certified post-repair end state (11 incident-date
  `ScannerRun`s unrestamped, each stamped `53d2ffd10cdbf89ef16681111bd900766e00e5809bc4ebc7d4b5f2bf1b7f6c55`,
  each carrying the exact `ForwardReturn` count recorded in
  `runs/goal-market-compass-iter-20/j11-stage-e-execute-population-report.json`) and the
  `j11-incident-recovery` maintenance boundary `active=1` covering exactly the 11 `INCIDENT_DATES`, when
  Stage F's fresh preflight runs before any write, then it re-derives every one of these directly and
  read-only from the live database and reports `proceed: true` with an empty `blocking_reasons` list.
- TC-2: given the fresh preflight instead detects any drift — a restamped or missing incident run, a
  `ForwardReturn` count mismatched against Stage E's recorded outcome, the boundary inactive or
  scope-drifted, or a recomputed `engine_identity` unequal to the frozen value — when the gate evaluates,
  then Stage F performs zero writes to any table, exits non-zero, and persists the exact blocking reason
  to the evidence directory.
- TC-3: given `app.models` is introspected for every table carrying a `dataset_version` field, when
  `derive_cache_table_inventory` runs, then it returns exactly the seven tables
  (`event_study_cache`, `market_phase_cache`, `forward_aggregate_cache`, `index_series_cache`,
  `membership_timeline_cache`, `availability_cache`, `coverage_snapshot`) against today's live schema, and
  a fixture test proves that adding an eighth synthetic `dataset_version`-bearing model to the introspected
  metadata changes the returned set (proving the function is not a hardcoded list wearing an
  introspection costume).
- TC-4: given `event_study_cache`/`market_phase_cache`/`forward_aggregate_cache` each hold at least one
  row whose stored `dataset_version` was computed from a `max(scanner_runs.id)`/`count(forward_returns)`
  pair strictly below the live post-Stage-E values, when `classify_cache_table` runs against each, then
  it reports zero stored rows matching the fresh live `research._dataset_version(session)` value and
  every stored row's `created_at` earlier than Stage D's frozen execution-start instant, and records
  disposition `explicit_delete` for each.
- TC-5: given `membership_timeline_cache`/`availability_cache`/`coverage_snapshot` each hold a row whose
  stored `dataset_version` was computed from a `scanner_runs` count/max-id pair strictly below the live
  post-Stage-D values, when `classify_cache_table` runs against each using
  `research._membership_dataset_version(session, config)`, then it reports zero stored rows matching the
  fresh live narrow stamp and every stored row's `created_at` earlier than Stage D's frozen
  execution-start instant.
- TC-6: given `daily_prices` is proven byte-unchanged by Stage D's and Stage E's own already-recorded
  mutation accounting, when `classify_cache_table` re-derives `index_series_cache`'s own narrow
  index-symbol stamp fresh and compares it to the one stored row's `dataset_version`, then the two values
  are equal and the recorded disposition is `prove_unaffected_leave_alone` with zero rows scheduled for
  deletion.
- TC-7: given a synthetic fixture database where a cache row is written under dataset-version string S,
  and the fixture then performs a delete-and-recreate of `ScannerRun`/`ForwardReturn` rows engineered to
  reproduce that IDENTICAL string S, when `classify_cache_table` runs against this fixture, then the pure
  stamp-string comparison alone reports a match, but the `created_at` comparison against the fixture's
  own recorded "repair start" instant proves the row predates the repair, and the combined disposition is
  `explicit_delete` — proving the `created_at` check is what makes a real collision detectable, not the
  stamp comparison alone.
- TC-8: given `execute_stage_f_cache_disposition` receives the classification output from TC-4/TC-5 (five
  tables `explicit_delete`, two preserved), when it runs, then it issues a `DELETE` against exactly the
  rows already proven stale in the five `explicit_delete` tables, zero `DELETE` against any other table,
  and a live post-write `COUNT(*)` on each of the five reports zero remaining pre-Stage-F rows.
- TC-9: given the live `membership_timeline_cache` row's cached date list and the current live
  `scanner_runs.asof_date` set, when the module evaluates whether `membership_timeline_cached`'s own
  `append_forward` condition (`min(new_dates) > prev_dates[-1]`) would hold for the newly-run incident
  dates (2026-05-12 through 2026-08-03) against the existing history's tail, then it reports `False`
  (proving the safe "historical gap-insert" branch would run, not the narrower append-forward branch),
  and the recorded disposition is `preserve_for_incremental_reuse`; given this evaluation instead cannot
  be established with confidence (a fixture forces an ambiguous or append-forward-eligible date pattern),
  then the recorded disposition falls back to `explicit_delete` and the handoff states which case
  occurred.
- TC-10: given `data_manager.availability_from_storage`'s documented "no ingest job in flight, stamp
  mismatch" branch would otherwise serve a stale `AvailabilityCache` row labeled `stale: False`, when
  Stage F completes with `availability_cache` classified `explicit_delete` and its row removed, then a
  fixture-level call to `availability_from_storage` against the post-deletion state returns the honest
  "not yet computed" empty sentinel (`_availability_not_yet_computed_payload`), never a stale payload
  labeled current.
- TC-11: given a before-capture and an after-capture of `j11_maintenance.capture_full_table_sweep`,
  bracketed by the whole-file mtime/size/WAL fingerprint at the true process start and end, when
  `diff_full_table_sweeps` compares them after the live run, then `changed_existing_tables` is a subset of
  exactly the tables classified `explicit_delete`, and `unexpected_new_tables`/`unexpected_removed_tables`
  are both empty.
- TC-12: given `daily_prices`, `scanner_runs`, `scanner_results`, `sector_scores`, `theme_scores`,
  `forward_returns`, `data_provider_runs`, `watchlist`, `maintenance_boundaries`, `next_session_manifests`,
  `index_series_cache`, and any cache table classified other than `explicit_delete` are all outside
  Stage F's authorized write scope, when the post-execution mutation accounting is inspected, then every
  one of them shows zero fingerprint change from the pre-execution capture.
- TC-13: given AG-10's `memory_cap_mb`/`HOST_GUARD_MEMORY_HIGH` envelope, when the live Stage F execution
  runs (a standalone maintenance process, never via `scripts/start-backend.sh`), then its measured peak
  memory (`/proc/<pid>/status` `VmPeak`, reusing `read_process_vm_peak_kb`/`build_memory_check`) is
  recorded in the evidence and compared against the configured ceiling.
- TC-14: given the CLI script is invoked without `--confirm`, when it runs, then it performs zero database
  interaction (not even a read) and exits non-zero; given it is invoked without an explicit
  `--evidence-dir`, when it runs, then it refuses before any config/engine construction and exits non-zero.
- TC-15: given the live execution has run to its conclusion (full success or a clean stop), when the dev
  handoff and evidence artifacts report status, then they state exactly `J-11 STAGE D EXECUTED: YES`,
  `J-11 STAGE E COMPLETE: YES`, `J-11 STAGE F COMPLETE: YES` or `NO` matching the true outcome,
  `J-11 STAGE G VERIFIED: NO`, `J-11 INCIDENT STATUS: NOT REPAIRED — ATTEMPT INCOMPLETE`,
  `J-11 MAINTENANCE BOUNDARY: ACTIVE`, `J-11 LIVE PRE-BOOT GUARD: ARMED`.
- TC-16: given every boolean check the new module computes (preflight gate, per-table classification,
  mutation accounting, execution outcome), when the reviewer inspects each one's construction, then none
  compares a hardcoded literal against itself and none evaluates `all()`/`any()` over a collection the
  same call already proved structurally empty — each is traced to a live- or fixture-derived value that a
  deliberately broken fixture can flip from pass to fail (the reviewer records this trace explicitly,
  naming iteration 20's three flagged checks as the pattern being avoided).
- TC-17: given maintenance isolation is active for the whole iteration, when any lane other than
  developer/reviewer/file-scoped-QA/auditor attempts to run (application-service boot, browser-qa-agent,
  the deterministic replay lane), then the engine refuses the dispatch and logs the refusal.
- TC-18: given J-01/J-04/J-10's passing status each rest on the untouched content of `scoring.py`,
  `compass.py`, and `data_manager.py`'s J-10 recovery code respectively, when
  `git status --porcelain -uall` is grepped against that exact file set after this iteration's changes
  are staged, then it returns zero matches.
- TC-19: given AG-9 forbids any live network call and every dated exception is exhausted, when the new
  execution module and CLI script are inspected, then zero network-capable call appears anywhere in the
  diff, and the live execution's evidence artifacts record zero outbound requests.

## NOTES

- **Assumption-ledger entries filed this iteration** (`runs/goal-session-market-compass/state/
  assumptions.md`): (1) scoping this iteration to Stage F alone rather than Stage F+G, continuing
  iterations 19/20's precedent; (2) the per-cache disposition design — `created_at`-vs-Stage-D-start as
  the decisive classification signal (not the `dataset_version` stamp string alone), five caches defaulted
  to `explicit_delete`, `index_series_cache` proven unaffected and preserved, and
  `membership_timeline_cache` given a conditional preserve-for-incremental-reuse recommendation
  contingent on a live proof — since `docs/goal.md` step 6 offers three dispositions without assigning one
  per named cache.
- **Live figures cited above are this planning pass's own read-only spot-check (2026-08-27)** —
  `scanner_runs` max id 3158 / count 3128, `forward_returns` count 6,814,320, `daily_prices` max date
  2026-08-12 / count 3,310,374, `min_history_bars` 200, and every cache table's current row count and
  stored stamp(s) as listed in BACKGROUND. Per this session's own established discipline, the developer
  must re-derive every one of these live and fresh rather than trust this citation.
- **Operational recommendation:** keep `run-goal.sh`'s pump running continuously with
  `CHAIN_MAINTENANCE_ISOLATION=true` and `CHAIN_REQUIRE_FULL_DEPTH=true` set across this iteration AND the
  subsequent Stage G iteration until `J-11 STAGE G VERIFIED: YES` — unchanged from iterations 19/20's own
  recommendation.
- **Escalation flag:** if the fresh preflight finds any drift from Stage D/E's certified end state, or if
  any of the six scanner-run/forward-return-dependent cache tables holds a row with `created_at` at or
  after Stage D's frozen execution-start instant, the developer must STOP before any write and report the
  exact blocker — the latter case specifically means an unauthorized write happened during maintenance
  isolation, which is graver than a routine classification disagreement and must not be silently resolved
  by deleting the evidence of it.
- **For a future Stage G iteration's decomposer (not actionable this iteration):** (1) the owner's Stage G
  membership rule requires verifying Stage-D attempt membership using the canonical 11 incident dates PLUS
  the recorded Stage-D run ids (3148–3158) and execution evidence — never inferred from `engine_identity`
  alone, since `compute_engine_identity` is mathematically forced to equal several historical readiness
  values and cannot alone distinguish this attempt's runs from a future runless-date write (auditor
  finding B1, iteration 19). (2) `docs/goal.md` step 5's premise that forward-return holes exist on
  retained runs is factually wrong for this codebase (iteration 20's own re-derivation, carried in the
  iteration-state digest as binding) — Stage G must accept population (b) = 0 as correct, never as a
  missing repair, and must not weaken its gate to accommodate a premise that was never true.
- Two standing framework notes carried forward unchanged, per owner instruction to leave them out of scope
  until after Stage G: the request-triggered write-path guard gaps recorded by ruling item 5, and
  `goal_gate.py`'s duplicate-journey-heading defect. Neither is addressed by this spec.
- If the reviewer, QA, or auditor lane finds that live execution cannot proceed safely for any reason not
  anticipated above, the correct action is the same as every prior J-11 stage in this session: stop,
  preserve evidence, and report — never force a write past a failing check to obtain a "complete" status.
