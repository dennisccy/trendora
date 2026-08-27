# Goal Iteration 22 — J-11 Stage G: full verification / acceptance gate

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** market-compass
- **Iteration:** 22
- **Mode:** next
- **Depth:** full
- **Full trigger:** 1 — Stage G's verdict spans every J-11 acceptance category (raw inputs, snapshot
  scope, forward returns, manifests, audit/evidence/user state, seven caches, ~18 named traps,
  operational isolation) across `data_manager.py`, `scanner.py`, `compass.py`, `research.py`,
  `forward_testing.py`, `j11_maintenance.py`, `j11_stage_d_execute.py`, `j11_stage_e_execute.py`,
  `j11_stage_f_execute.py`, `j11_preboot_guard.py` and `models.py` — no single journey's test suite
  covers this interaction, and it is this iteration's own live edit (one guard call wired into
  `data_manager.coverage_from_storage`) whose correct interaction with three independent create-once
  code paths (an incident-quarantined date, an ordinary date, an already-cached read) is exactly the
  cross-module risk this trigger names. This also matches the evaluator's binding `full` recommendation;
  no escape condition was needed.
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
    addendum, the AVB diagnostic fetch #2) are **exhausted** and none applies here; Stage G authorizes
    **no** network fetch of any kind (full exception text on record in `docs/goal.md`, not reproduced).
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
    residual detail is on record in `docs/goal.md`; not reproduced here — Stage G verifies but does not
    touch `next_session_manifests`.)

## GOAL

Execute the owner-authorized J-11 Stage G — the terminal, full incident-cleanliness verification gate —
proving every acceptance requirement (raw inputs, snapshot scope, forward returns, manifests,
audit/evidence/user state, and derived caches) holds against the live database, closing the one
freshly-found write path that would silently undo Stage F's cache clearing the moment the app is next
allowed to boot, and emitting the honest `FULLY REPAIRED` or `NOT REPAIRED — ATTEMPT INCOMPLETE`
terminal-outcome status that only Stage G may write.

## BACKGROUND

Iterations 19, 20 and 21 executed Stages D, E and F live and cleanly, each independently re-verified by
the evaluator against the live 8.4 GB database: Stage D regenerated exactly the 11 canonical incident
dates (`ScannerRun` ids **3148–3158**, frozen attempt identity
`53d2ffd10cdbf89ef16681111bd900766e00e5809bc4ebc7d4b5f2bf1b7f6c55`, created
`2026-08-26T10:52:55.552946Z` → `10:53:02.010362Z`); Stage E filled 16,592 derivable forward-return
holes on those 11 rebuilt runs and proved population (b) — holes on otherwise-retained runs — is
**structurally zero**, not a missing repair (`data_manager._cascade_targets` deletes an affected run's
forward returns whole, so a retained-run hole cannot exist; live data agrees); Stage F classified all
seven `dataset_version`-bearing cache tables and explicitly deleted five (`event_study_cache`,
`market_phase_cache`, `forward_aggregate_cache`, `coverage_snapshot`, `availability_cache`), proved
`index_series_cache` unaffected, and preserved `membership_timeline_cache` on a live-proven
incremental-reuse argument. `docs/goal.md`'s "OWNER RULING — J-11 Stage D through Stage G recovery
execution AUTHORIZED" item 9 already authorizes Stage G as the acceptance gate **unconditionally
following a successful Stage F** — no further owner instruction is required to begin it, and this spec
does not amend `docs/goal.md`. Per that same ruling item 14, this is the terminal, "no third state"
iteration: it must end in exactly `FULLY REPAIRED` or `NOT REPAIRED — ATTEMPT INCOMPLETE`, nothing
partial.

**Three binding facts this iteration must honour, not re-litigate (owner-relayed, this session,
2026-08-26/27):**
1. **Membership rule.** Stage-D attempt membership is verified from the canonical 11
   `j11_maintenance.INCIDENT_DATES` **plus** the recorded run ids 3148–3158 **and** the Stage D/E/F
   execution evidence — **never** from `engine_identity` alone (`compute_engine_identity(cfg)` stamps
   every run identically regardless of which attempt created it, and `scanner.resolve_run` is
   unguarded, so identity alone cannot carry membership — iter-19 auditor finding B1).
2. **Population (b) = 0 is the correct answer, not a gap.** `docs/goal.md` J-11 step 5 asserts forward-
   return holes exist on retained runs; iteration 20 re-derived this is **false** for this codebase
   (`data_manager._cascade_targets`/`remove_price_data` delete an affected run's `ForwardReturn` rows
   whole, so a partial hole cannot survive on a retained run). Stage G's forward-return check must read
   `population_b_count == 0` as PASS.
3. **`docs/goal.md` ruling item 5 explicitly defers two named request-path gaps** — `scanner.resolve_run()`
   and "ordinary Data Manager persistence paths capable of calling `run_scan()` or `persist_run_payload()`"
   — to **post-J-11 maintenance-boundary hardening work after Stage G**, and explicitly forbids
   "expand[ing]... into a generalized `ScannerRun` writer redesign" or "introduc[ing] a new generic
   persistence architecture merely to satisfy this ruling." That deferral is honoured unchanged this
   iteration (see the scoping decision below and OUT OF SCOPE).

**The new finding this iteration must resolve.** Iteration 21's evaluator found, and no earlier lane
reported, that `data_manager.coverage_from_storage`'s self-heal branch (currently at
`data_manager.py:1547`; re-derive the live line number fresh, it has moved before) calls
`refresh_coverage_snapshot_for` → `_upsert_coverage_snapshot` — a **request-path INSERT** — whenever an
explicit `?as_of=` names a date backed by a real `ScannerRun`, with **no boundary-guard import anywhere
in `data_manager.py`**. Because Stage D gave all 11 incident dates real runs, a single future page visit
to an incident date would silently repopulate the `coverage_snapshot` row Stage F deliberately cleared —
Stage F's result is **not durable** against that one click. This is a genuinely new gap (found during
Stage F's own evaluation, after ruling item 5 was written), a **different function** than either of the
two gaps ruling item 5 names by name (it calls `_upsert_coverage_snapshot`, never `run_scan`/
`persist_run_payload`), and it directly threatens Stage G's own core claim — "caches consistent with the
rebuilt state" and "no stale derived state remains for the incident set" cannot be honestly asserted as
**durable** while this path stays open, and this session may not boot the app to *empirically* prove
durability without a human decision to authorize that boot (see OUT OF SCOPE).

**Scoping decision (logged to `assumptions.md`): foreclose this one write path now; leave the two
ruling-item-5-deferred gaps exactly as deferred.** This spec wires the EXISTING, already-tested
`j11_preboot_guard.evaluate_boundary_for_date_fail_closed` — the identical idiom already used at
`warmup.py:361` and `forward_testing.py:551` — into `coverage_from_storage`'s self-heal branch only. It
does **not** touch `scanner.py::resolve_run` or `compass.py::get_or_create_manifest`: the first is named
verbatim by ruling item 5's deferral; the second, while "the same species" of gap, is not named by
either ruling item 5's text or this iteration's coordinator note as something Stage G must resolve, and
fixing three call sites when only one was named risks exactly the scope-broadening ruling item 5
forbids. Both remain **recorded, not erased or described as resolved** (OUT OF SCOPE), for a future
maintenance-boundary hardening pass after this iteration.

**The B2 cache-content gap (iteration 21 auditor, "consider whether Stage G should assert against
this").** Stage F's `membership_timeline_cache` preserve decision proved the next MISS would take the
*cheap* repair branch (`append_forward=False`, so the incremental historical-gap-insert path runs, not
the >300s full resolver sweep) — a **performance/branch-selection** proof. It did **not** prove the
row's own **already-cached content** for incident dates is still correct. The preserved row's stored
`points` already contain entries for four incident dates that were *not* in Stage F's own recorded
`new_dates` list (2026-05-13, 07-10, 07-13, 07-24, 07-27, 08-03, 08-05 — seven dates; the other four
incident dates' points pre-exist in the row) — i.e., pre-repair-era values that an incremental refresh
never re-touches. Whether those values are still correct after Stage D's regeneration (same canonical
inputs → same membership, in principle, except for the two authorized AVB volume cells) is unproven.
`docs/goal.md`'s own Stage G acceptance item — "no stale derived state remains for the incident set" —
already requires this proof; it is not optional hardening. This spec requires Stage G to recompute each
such date's value read-only via `_membership_timeline` (`data_manager.py:563`, the pure, non-cache-
writing compute the cache wraps) and compare field-by-field against the stored row; a mismatch flips the
disposition to the deletion fallback Stage F's own design already anticipated.

**Lessons applied** (from `lessons.md`): iter-19's "a successful rebuild can move the danger, not remove
it" is this whole iteration's premise — Stage F succeeding is precisely what makes the coverage self-heal
path dangerous. Iter-19b's "diff against the PREVIOUS iteration's recorded end-state sweep, never just an
in-iteration pair" governs the cross-iteration mutation accounting below (diffed against iter-18's
pre-Stage-D baseline, reconciling the WHOLE D→G arc in one accounting, not just this iteration's own
before/after). Iter-15b's "state the exact recipe beside a fingerprint" governs every reused baseline
citation. Iter-20/21's "no verification check may pass by construction" (the three flagged tautological
Stage-E checks) governs every boolean `stage_g_verdict` computes — the reviewer explicitly re-applies that
scrutiny here. Iter-18's "enumerate writers via grep, never a hand-built call graph" governs the
write-path re-enumeration (TC-20). Iter-17's "a probe of a known-broken condition must state the
consequence in prose, not just the boolean" governs how population (b) = 0 and the two deferred gaps are
written up — each must say what it means, not just what it measures.

Depth is `full`, matching the evaluator's binding recommendation (0 consecutive lean iterations
dispatched, so no hardening-cadence trigger is even needed independently). This spec deliberately does
**not** set a `Maintenance isolation:` or `Depth enforcement:` metadata line — those are operator-only
controls, and a self-written safety declaration here would be exactly the governor-bypass anti-pattern 25
describes. Independently of this spec, `docs/goal.md`'s Stage D→G ruling item 13 requires the human
dispatching this run to supply `CHAIN_MAINTENANCE_ISOLATION=true` and `CHAIN_REQUIRE_FULL_DEPTH=true` as
required launch conditions — unchanged since iteration 19, and per this iteration's coordinator note,
already set for this run by the operator.

**On booting the app (coordinator note, explicit instruction).** This spec's design closes the
coverage-snapshot exposure **structurally** (fail-closed at the source, proven by fixture tests and a
fresh grep re-enumeration) rather than **empirically** (proving no live click will land). It does not
request, plan, or assume an application-service boot at any point. Whether to later boot the app under
supervision to gather live-traffic durability evidence — a stronger but categorically different kind of
proof — is explicitly a decision left to the human; this spec neither performs it nor asks for it.

**Resource discipline (AG-10; coordinator note resource constraints; the 2026-08-20 host-freeze
incident).** Every check below is either a read-only SQLite query, a fixture-scoped unit test against an
isolated in-memory/tmp engine, or (in the one PASS-only case) a single-row `UPDATE` on a two-column
boolean flag. No canonical producer is regenerated or warmed "while we're here." Three goal-mode engines
currently share this 26 GB host with the owner's consent; this iteration adds no parallel writer and
performs no bulk compute.

## IN SCOPE

### Backend

- [ ] New module `apps/backend/app/engine/j11_stage_g_verify.py`:
  - `stage_g_preflight_gate_verdict(session, ...)`: fresh, read-only preflight reusing existing
    functions directly (never reimplemented) — `j11_stage_d_execute.recheck_maintenance_boundary_and_guard`
    (boundary/guard, still ACTIVE, still scoped to exactly `j11_maintenance.INCIDENT_DATES`);
    `j11_stage_e_execute.confirm_stage_d_runs_present_unrestamped` and
    `check_engine_identity_matches_stage_d` (called with the frozen
    `53d2ffd10cdbf89ef16681111bd900766e00e5809bc4ebc7d4b5f2bf1b7f6c55` value) for a fresh identity-drift
    check; `confirm_manifests_unchanged` (reused as-is) against the same certified iter-16 baseline; a
    fresh comparison of the 11 runs' `ForwardReturn` counts against
    `runs/goal-market-compass-iter-20/j11-stage-e-execute-population-report.json`'s recorded per-run
    outcome (including run 3158's own recorded 0, a legitimate not-yet-mature outcome); a fresh
    comparison of the seven cache tables' live state against
    `runs/goal-market-compass-iter-21/j11-stage-f-execute-dispositions.json`'s recorded dispositions.
    Any drift → zero further checks, zero writes, STOP with the exact blocker named.
  - `verify_raw_inputs(session, cfg)`: `daily_prices` row count and content fingerprint compared against
    the certified post-AVB-correction baseline (cite the exact recipe from
    `runs/goal-market-compass-iter-16/j11-avb-correction-true-end.json` or the nearest certified
    successor — state the recipe beside the value, never a bare number, per iter-15b's lesson); confirm
    J-10's recovered 2026-08-11/12 rows remain intact; confirm zero network-capable call anywhere in this
    module (AG-9).
  - `verify_snapshot_scope(session)`: confirm the live `ScannerRun` id set for
    `j11_maintenance.INCIDENT_DATES` is EXACTLY `{3148, ..., 3158}` (11 dates, 11 ids, one-to-one) using
    the ids **and** Stage D's execution evidence (`runs/goal-market-compass-iter-19/j11-stage-d-execute-*
    .json`) — **never** `engine_identity` alone (the owner's binding membership rule); confirm, via a
    cross-iteration diff against iteration 18's pre-Stage-D full-table sweep
    (`runs/goal-market-compass-iter-18/j11-iter18-full-table-sweep-*.json`), that zero `ScannerRun`
    outside that 11-id set was deleted, created, or rewritten across the whole D→F arc.
  - `verify_forward_returns(session)`: reuse `j11_stage_e_execute.live_verify_three_populations` fresh;
    assert population (a) matches Stage E's recorded 16,592 fill; assert population (b) is exactly zero
    **and record this explicitly as the CORRECT, expected outcome** (binding fact 2 above — the check
    must not read a zero count as failure, and the reviewer explicitly confirms this framing); assert
    population (c) (genuinely immature horizons) remains honestly absent, with zero fabricated row.
  - `verify_manifests(session)`: direct `SELECT COUNT(*) FROM next_session_manifests` equals 24; every
    pre-existing row's `content_hash`/`manifest_hash`/`version`/`available_at_utc`/`prospective_eligible`
    byte-identical to the certified baseline; zero row exists for any of the 7 manifest-less incident
    dates (2026-05-12, 05-13, 07-10, 07-13, 07-24, 07-27, 08-03) — verified via a **direct SQL SELECT
    only**, never via `get_or_create_manifest(...)` or any HTTP call (the manifest-minting trap
    `docs/goal.md` names explicitly). For the 4 manifest-bearing incident dates (2026-08-05, 08-10,
    08-11, 08-12), confirm zero field changed and cite the existing `basis_disclosure` fixture tests
    (iter-11/12) as still green rather than re-deriving them.
  - `verify_audit_evidence_and_user_state(session)`: `data_provider_runs`, the certified and staging
    ledgers (7 entries, all `FAIL`, both), `watchlist`, pre-registrations, and graveyard/rejected-
    hypothesis history all row-count- and content-identical to the recorded pre-J-11 baseline.
  - `verify_cache_dispositions(session, cfg)`: `event_study_cache`, `market_phase_cache`,
    `forward_aggregate_cache`, `coverage_snapshot`, `availability_cache` each hold zero rows (live
    `COUNT(*)`); `index_series_cache`'s one row's narrow stamp re-derived fresh still equals its stored
    `dataset_version` (daily_prices proven byte-unchanged).
  - `verify_membership_timeline_preserved_row(session, cfg)` **(new — closes auditor gap B2)**: read the
    preserved row's stored `points`; for every incident date already present in it (i.e., NOT among
    Stage F's recorded `new_dates` — re-derive this set fresh from the live row and
    `runs/goal-market-compass-iter-21/j11-stage-f-execute-dispositions.json`, never assume it is the
    four dates named in BACKGROUND), recompute that date's `size`/`entries`/`exits`/`excluded` fields
    read-only via `_membership_timeline` (`data_manager.py:563`) against current storage and compare
    field-by-field against the stored point. If every compared date matches exactly: record the explicit
    field-by-field proof; disposition `preserve_for_incremental_reuse` CONFIRMED, zero write. If any date
    mismatches: the row is stale — delete it (the exact fallback Stage F's own design pre-approved),
    record which date(s) and field(s) disagreed, and flip the disposition to `explicit_delete`.
  - `verify_named_traps(session, engine)`: assemble, never re-implement, the ~18 named traps from
    `docs/goal.md`'s Acceptance section — the 10 "schema/identity/retry" traps and the 8 "J-10/J-11
    sequencing" traps — each resolved by citing its existing passing test (from the `test_j11_stage_b1_*`,
    `test_j11_stage_c_*`, `test_j11_stage_d*`, `test_j11_stage_e*`, `test_j11_stage_f*` suites) still
    green, plus a fresh live read-only spot-check wherever the trap concerns current live state (e.g.,
    "all 11 rebuilt runs share the frozen identity" — direct DB read, not a fixture citation alone).
  - `verify_operational_isolation()`: read the engine's own dispatch-refusal log for this iteration and
    confirm application-service boot, browser-qa-agent, and the replay lane were each refused/never
    dispatched for the whole iteration.
  - `close_coverage_snapshot_self_heal_write_path` — the ONE authorized code edit (see below), plus its
    own verification: a fresh `grep -rn "run_scan(\|get_or_create_manifest(\|refresh_coverage_snapshot_for("
    apps/backend/app/` (mirroring iter-18's "enumerate writers via grep, never a hand-built call graph"
    lesson) classifying every call site as: guarded (names the guard call), Stage D's own authorized
    write, or explicitly still-open-and-deferred (`scanner.py::resolve_run`,
    `compass.py::get_or_create_manifest`, and any Data-Manager `run_scan`/`persist_run_payload` path
    ruling item 5 names) — recorded in the dev handoff so no future lane re-derives it from scratch.
  - `build_stage_g_cross_iteration_mutation_accounting(session)`: reusing
    `j11_maintenance.capture_full_table_sweep`/`diff_full_table_sweeps` as-is, diff the live sweep against
    iteration 18's PRE-Stage-D baseline sweep (the earliest available pre-destructive-write full-table
    capture), reconciling every table's total delta across the WHOLE D→G arc to exactly: Stage D (11
    `ScannerRun`s + their `ScannerResult`/`SectorScoreRow`/`ThemeScoreRow` children), Stage E (16,592
    `ForwardReturn` rows), Stage F (five cache tables emptied), and this iteration's own possible writes
    (the `membership_timeline_cache` delete-if-stale fallback; the boundary's `active` flag on a full
    PASS). Zero unexplained change anywhere else.
  - `stage_g_verdict(...)`: aggregate every check above into one PASS/FAIL with a named list of any
    failing check — no boolean permitted to pass by construction (iter-20/21's flagged-tautology
    discipline; the reviewer explicitly re-checks this).
  - `finalize_stage_g(session, verdict, ...)`: the ONE conditional terminal action.
    - On a full PASS: emit the SUCCESS terminal-outcome block (below) and perform exactly one further
      write — deactivate (never delete) the `j11-incident-recovery` `MaintenanceBoundary` row via the
      existing `j11_preboot_guard.clear_boundary` function / `run_j11_maintenance_boundary_disarm.py`
      script (ruling item 11's already-authorized action; the row's `id=1` and audit history survive,
      only `active` flips `1 → 0`). This action does **not** start the backend, frontend, or any product
      work — it only permits a later iteration to do so.
    - On any FAIL: perform zero further writes (except the membership-timeline delete already covered
      above if that specific check is what failed), emit the INCOMPLETE terminal-outcome block, and
      leave the boundary `active=1`, exactly as ruling item 14 requires.
  - Memory measurement reused as-is: `j11_stage_e_execute.read_process_vm_peak_kb`/`build_memory_check`
    against `server.memory_cap_mb`.
- [ ] **One surgical edit to `apps/backend/app/engine/data_manager.py`'s `coverage_from_storage`**
  (currently the branch at `data_manager.py:1547`; re-derive the live line number fresh before editing —
  it has moved before). Import `app.engine.j11_preboot_guard`. Immediately before the existing
  `if as_of is not None and _scanner_run_exists(session, resolved_asof): return _tag_coverage_status(
  refresh_coverage_snapshot_for(...), "current")` self-heal call, evaluate
  `j11_preboot_guard.evaluate_boundary_for_date_fail_closed(session, resolved_asof)`; if `blocked` is
  `True`, do **not** call `refresh_coverage_snapshot_for` — fall through unchanged to the function's
  EXISTING subsequent fallback chain (the stale-row-under-an-older-stamp check, then the honest
  all-zero "not yet computed" sentinel). Change no other line of the function. This is the identical,
  already-tested guard idiom already used at `warmup.py:361` and `forward_testing.py:551` — not a new
  generic persistence architecture, not a redesign of `run_scan`/`persist_run_payload`, and it does not
  touch `scanner.py` or `compass.py` (see the scoping decision in BACKGROUND and OUT OF SCOPE).
- [ ] New CLI script `apps/backend/scripts/run_j11_stage_g_verify.py`, mirroring
  `run_j11_stage_f_execute.py`'s `--confirm`/`--evidence-dir` gating exactly (refuses any DB interaction
  without `--confirm`; refuses before config/engine construction without `--evidence-dir`).
- [ ] New tests `apps/backend/tests/test_j11_stage_g_verify.py` and
  `test_j11_stage_g_verify_cli_script.py` — fixture-scoped only (`app.db.make_engine` isolated engine),
  never against `apps/backend/data/trendora.db`.
- [ ] New/extended tests proving the `coverage_from_storage` guard edit — a boundary-blocked incident
  date's self-heal is refused with zero write; an ordinary (non-blocked) date's self-heal is byte-
  identical to pre-edit behavior; a read of an already-persisted `CoverageSnapshot` row (any date,
  including an incident date) is completely unaffected by the guard. Extend or sit alongside the
  existing `test_api_data.py` / `test_data_manager.py` files that already cover `coverage_from_storage`
  — run both fixture-scoped, never against the live database, and confirm zero regression.
- [ ] Dev handoff records, per acceptance category, the live/fixture evidence backing it — explicitly
  including the membership-timeline B2 closure's per-date comparison result, the write-path
  re-enumeration's classification table, and the exact terminal-outcome block emitted.

### New user-facing capability
None — backend-only maintenance/verification; no page, route, or UI element changes this iteration.

### New information displayed
None.

### New user actions
None.

### UI surface changes
None.

### Product surface delta
None this iteration. A full PASS unblocks normal Market Compass work (J-01–J-09) for a **future**
iteration's decomposer per the existing loop-mechanics gate — this iteration does not itself start any
product work, boot the app, or touch a UI file. Matches J-11's "Walkthrough: waived" status in
`docs/goal.md`.

### Blueprint conformance
No new surfaces. `runs/goal-session-market-compass/state/blueprint.md` is **not** edited this iteration —
nothing to register, matching iterations 13/19/20/21's identical conclusion for the identical reason.
Stage G verifies existing Data Contract rows' underlying storage; it introduces no new computing module
or serving endpoint.

### Data-contract additions
None.

## OUT OF SCOPE

- **`scanner.py::resolve_run()` and `compass.py::get_or_create_manifest()`'s own request-path guard
  gaps** — the first is named verbatim by `docs/goal.md` ruling item 5 and explicitly deferred to
  "post-J-11 maintenance-boundary hardening work after Stage G"; the second, while the same species of
  gap, is not named by ruling item 5's text or this iteration's coordinator note as something Stage G
  must resolve. Both are recorded as still-open in the dev handoff (TC-20), never described as
  resolved, and both remain **untouched** (git diff empty for both files — TC-21).
- **Booting the app, browser-qa-agent, the deterministic replay lane, a second backend or frontend
  process** — all OFF for the whole iteration (maintenance isolation, ruling item 4). This spec's guard
  fix is proven structurally (fixture tests + a static call-site re-enumeration), never by an empirical
  live-traffic test.
- **Regenerating or warming any of the seven caches through their canonical producer** — deferred to the
  existing, already-safe normal warm-up path that runs after Stage G's own conditional boundary release,
  EXCEPT the one narrowly-scoped `membership_timeline_cache` delete-if-stale corrective action, which is
  explicitly authorized above as Stage F's own pre-approved fallback, now exercised by Stage G's proof.
- Any write to `daily_prices`, `scanner_runs`, `scanner_results`, `sector_scores`, `theme_scores`,
  `forward_returns`, `next_session_manifests`, `data_provider_runs`, `watchlist` — Stage G's only
  authorized writes are: (a) the conditional single-row `maintenance_boundaries.active` flip on a full
  PASS; (b) the conditional single-row `membership_timeline_cache` delete if the B2 proof fails.
- Freezing a new attempt identity — Stage G cites Stage D's frozen identity for provenance/comparison
  only.
- Re-running or re-verifying Stage D, E, or F's own destructive/write steps — already DONE, verified
  live ("do not redo" per the iteration-state digest); this iteration's preflight only re-**verifies**
  their end state, read-only.
- Any provider/network fetch — AG-9 remains closed; no dated exception applies to Stage G.
- Any J-01–J-09 product/UI work, and specifically J-07/J-08 — blocked by the loop-mechanics gate until
  Stage G passes, and not started even by this spec's own success path (see Product surface delta).
- Application-service boot as a means of proving write-path closure "for real" — explicitly left to the
  human per the coordinator note; this spec neither performs it nor requests it.
- Any goal-mode framework change — including any proposal to fix `goal_gate.py`'s duplicate-journey
  defect, the `journey_history_hash`/stall-window mechanics, or the `scripts/automation/` forbidden-lane
  defect; the owner has explicitly deferred all three until after Stage G, and none is scoped to this
  iteration.
- Running the full pytest suite, or opening `apps/backend/data/trendora.db` for write from any test or
  tool (read-only `sqlite3 "file:...?mode=ro"` only, when a live spot-check is needed outside the
  engine's own SQLAlchemy session).
- Restamping, mutating, or otherwise touching the 11 Stage-D-rebuilt runs or any other `ScannerRun`.
- Any schema/DDL migration — none authorized or needed this iteration.
- The five older, non-blocking owner questions (J-09's 3.44 GB; J-06's wording; J-01's test-step
  wording; an empty "next-session focus"; MNST) — unchanged, not addressed here.

## DEFINITION OF DONE

- [ ] Fresh preflight (boundary/guard recheck; all 11 Stage-D runs present, unrestamped, frozen identity
  `53d2ffd1…` confirmed live; per-run `ForwardReturn` counts match Stage E's recorded outcome exactly;
  the seven cache tables' live state matches Stage F's recorded dispositions exactly; the 24-row
  manifest dump unchanged vs. the certified baseline) is re-derived live and read-only before any check
  below runs; any drift halts the attempt with the exact blocker named and zero further writes.
- [ ] Raw inputs verified unchanged against the certified post-AVB-correction baseline, with the exact
  fingerprint recipe stated beside the value (never a bare number).
- [ ] Snapshot scope verified using ids 3148–3158 plus Stage D's execution evidence — **never**
  `engine_identity` alone; zero `ScannerRun` outside that set touched across the whole D→F arc
  (cross-iteration diff against iteration 18's pre-Stage-D baseline).
- [ ] Forward-return populations (a)/(b)/(c) re-confirmed; population (b) = 0 is recorded and scored as
  the CORRECT outcome, not a gap; population (c) remains honestly absent with zero fabrication.
- [ ] Manifest row count (24) and every pre-existing row's stamps/hashes verified byte-identical via
  direct SQL only; zero new manifest exists for any of the 7 manifest-less incident dates — the
  manifest-minting trap is not tripped by this iteration's own verification.
- [ ] Audit/evidence/user-state tables (provider runs, both certified/staging ledgers, watchlist,
  pre-registrations, graveyard) verified row-count- and content-identical to the recorded baseline.
- [ ] The five explicit-delete cache tables hold zero rows; `index_series_cache`'s stamp re-derived
  equal to live; `membership_timeline_cache`'s preserved row is proven correct field-by-field for every
  already-cached incident date (auditor gap B2 closed) — or, if any date disagrees, the row is deleted
  and the mismatch is recorded, not hidden.
- [ ] The ~18 named traps (schema/identity/retry family; J-10/J-11 sequencing family) are each resolved
  by citing their existing passing test plus, where the trap concerns live state, a fresh spot-check —
  none re-implemented from scratch.
- [ ] `data_manager.coverage_from_storage`'s self-heal branch is guarded by
  `j11_preboot_guard.evaluate_boundary_for_date_fail_closed`: a boundary-blocked date's self-heal is
  refused with zero write; an ordinary date's self-heal is byte-identical to pre-edit behavior; a read
  of an already-persisted row is unaffected. Existing regression tests covering this function
  (`test_api_data.py`, `test_data_manager.py`) pass unchanged.
- [ ] A fresh whole-package grep re-enumerates every `run_scan(`/`get_or_create_manifest(`/
  `refresh_coverage_snapshot_for(` call site and classifies each as guarded, Stage D's own authorized
  write, or explicitly still-open-and-deferred — recorded in the dev handoff.
- [ ] `scanner.py` and `compass.py` show zero diff from HEAD — the two ruling-item-5-deferred gaps are
  recorded, not silently fixed and not silently left undocumented.
- [ ] Cross-iteration mutation accounting (this iteration's live sweep diffed against iteration 18's
  pre-Stage-D baseline) reconciles every changed table's delta to exactly Stage D + Stage E + Stage F +
  this iteration's own conditional writes — zero unexplained change anywhere else in the database.
- [ ] Operational isolation held for the entire iteration — no application-service boot, no
  browser-qa-agent dispatch, no replay lane; the engine's refusal log is the evidence.
- [ ] `stage_g_verdict` aggregates every category above with no boolean that can pass by construction —
  the reviewer explicitly checks this against iteration 20/21's own flagged-tautology pattern.
- [ ] The attempt ends in exactly one of the two states below; on a full PASS, the `j11-incident-recovery`
  maintenance boundary is deactivated (row preserved, `active: 1 → 0`) as the ONE further authorized
  write, and no product work, boot, or UI change is started by this spec; on any FAIL, the boundary stays
  `active=1` and zero further writes occur.
- [ ] Live peak process memory during the execution is measured and recorded against the configured
  `memory_cap_mb`/`HOST_GUARD_MEMORY_HIGH` ceiling (AG-10).
- [ ] Required-still-passing journeys J-01, J-04, J-10 are **not** re-verified via browser QA or replay
  this iteration (impossible under maintenance isolation); instead `scoring.py` (J-01), `compass.py`
  (J-04), and `j10_recovery.py` (J-10's dedicated recovery module) show zero diff, and
  `data_manager.py`'s diff — the one file this iteration DOES touch — is confirmed scoped to exactly the
  `coverage_from_storage` self-heal branch via a function-level diff, with zero change to
  `_cascade_targets`, `remove_price_data`, or any J-10-relied-upon function in that file.
- [ ] Fixture-scoped unit/integration tests (never against the live database, never the full suite) pass
  for every scenario in TESTING REQUIREMENTS.
- [ ] No anti-goal violation introduced; the ledger stays at its current total (7) with zero new
  unresolved entries.
- [ ] This iteration's new files and evidence folder are committed to git before scoring — confirm
  `git status --short` shows nothing under `apps/backend/app/engine/j11_stage_g_verify.py`,
  `apps/backend/scripts/run_j11_stage_g_verify.py`, `apps/backend/tests/test_j11_stage_g_verify*.py`,
  the `data_manager.py` diff, or `runs/goal-market-compass-iter-22/` left untracked (iterations 19, 20
  and 21 were each flagged for this at scoring time; this iteration closes the pattern rather than
  repeating it a fourth time).
- [ ] Dev handoff written at `docs/handoffs/goal-market-compass-iter-22-dev.md`; walkthrough is waived
  per `docs/goal.md` (J-11 has no UI surface) and browser-qa-agent does not run this iteration
  (maintenance isolation forbids application-service boot through this iteration's own completion) — the
  evaluator determines J-11's status from the live/fixture evidence this iteration produces.

## TESTING REQUIREMENTS

- **Browser:** none this iteration. `browser-qa-agent` does not run — maintenance isolation forbids
  application-service boot for the whole of J-11 through this iteration.
- **Unit/integration:** preflight gate composition; each acceptance-category verify function (raw
  inputs, snapshot scope + membership rule, forward-return populations, manifests + minting-trap
  avoidance, audit/evidence/user-state, cache dispositions, the membership-timeline B2 recompute-and-
  compare); the named-trap assembly; the `coverage_from_storage` guard edit (blocked / unblocked / read-
  unaffected); the write-path re-enumeration; cross-iteration mutation accounting; the aggregate verdict;
  the conditional finalize action (PASS → boundary deactivate; FAIL → no-op); the CLI script's
  `--confirm`/`--evidence-dir` gating — all fixture-scoped, reusing the isolated-engine pattern the
  sibling `test_j11_*` suites already use (`app.db.make_engine`, never the live `trendora.db`).
- **Error cases:** any preflight drift (restamped/missing run, forward-return-count mismatch, cache
  disposition mismatch, boundary inactive/scope-drifted, engine-identity mismatch); a fixture where a
  12th `ScannerRun` shares the frozen `engine_identity` but sits outside ids 3148–3158 (must be excluded
  from membership by the ids+evidence rule); a fixture where the membership-timeline recompute disagrees
  with the stored point for one date (must fall back to delete, not silently pass); a fixture request for
  a boundary-blocked date reaching `coverage_from_storage` (must refuse the self-heal write); a CLI
  invocation missing `--confirm`; a CLI invocation missing `--evidence-dir`; a mid-verification failure in
  any one category (must halt and report, never silently skip to the next).

Test-first contract — scenarios:

- TC-1: given the live database in Stage F's certified post-repair end state (11 incident-date
  `ScannerRun`s unrestamped, each stamped `53d2ffd10cdbf89ef16681111bd900766e00e5809bc4ebc7d4b5f2bf1b7f6c55`,
  five caches empty, `index_series_cache`/`membership_timeline_cache` preserved per iteration 21's
  recorded dispositions), when Stage G's fresh preflight runs before any check, then it re-derives every
  one of these directly and read-only and reports `proceed: true` with an empty `blocking_reasons` list.
- TC-2: given the fresh preflight instead detects any drift (a restamped/missing incident run, a
  `ForwardReturn` count mismatched against Stage E's recorded outcome, a cache table's live state
  mismatched against Stage F's recorded disposition, the boundary inactive or scope-drifted, or a
  recomputed `engine_identity` unequal to the frozen value), when the gate evaluates, then Stage G
  performs zero further checks and zero writes, exits non-zero, and persists the exact blocking reason to
  the evidence directory.
- TC-3: given `daily_prices`' certified post-AVB-correction row count and content fingerprint, when
  `verify_raw_inputs` runs, then it re-derives both fresh, states the exact fingerprint recipe beside the
  value, and reports an exact match with zero evidence of any network call anywhere in the module.
- TC-4: given the live `ScannerRun` table, when `verify_snapshot_scope` resolves membership using ids
  3148–3158 plus Stage D's execution evidence, then it reports exactly those 11 ids mapped 1:1 onto
  `j11_maintenance.INCIDENT_DATES`; given a fixture instead constructs a 12th run sharing the identical
  frozen `engine_identity` but a different id outside 3148–3158, then the membership check correctly
  EXCLUDES it (proving the ids+evidence rule, never identity alone, governs membership).
- TC-5: given iteration 18's pre-Stage-D full-table sweep and the live current sweep, when
  `diff_full_table_sweeps` compares `scanner_runs`, then every id outside {3148..3158} shows zero
  create/delete/rewrite across the whole D→F arc.
- TC-6: given Stage E's recorded population report, when `verify_forward_returns` re-derives all three
  populations live, then population (a) matches the recorded 16,592-row fill, population (b) is exactly
  0 and is recorded as the CORRECT expected outcome (not a gap — the reviewer confirms this framing
  explicitly), and population (c) remains honestly absent with zero fabricated row.
- TC-7: given `next_session_manifests` holds 24 rows today, when `verify_manifests` runs a direct SQL
  `SELECT`, then it reports exactly 24, zero row exists for any of the 7 manifest-less incident dates,
  and the verification made zero call to `get_or_create_manifest`/`GET /api/compass` (the minting trap is
  not tripped by the check itself).
- TC-8: given the 4 manifest-bearing incident dates' stored stamps (`source_run_id`, `available_at_utc`,
  `content_hash`, `manifest_hash`, `version`, `prospective_eligible`), when compared against the
  certified baseline, then every field is byte-identical, and the existing `basis_disclosure` fixture
  tests (iter-11/12) are confirmed still green rather than re-derived from scratch.
- TC-9: given the recorded baseline for `data_provider_runs`, both certified/staging ledgers (7 entries
  each, all `FAIL`), `watchlist`, pre-registrations, and graveyard history, when
  `verify_audit_evidence_and_user_state` runs, then every one matches row-count- and content-identical.
- TC-10: given Stage F's recorded dispositions, when `verify_cache_dispositions` runs, then
  `event_study_cache`/`market_phase_cache`/`forward_aggregate_cache`/`coverage_snapshot`/
  `availability_cache` each report a live `COUNT(*)` of zero, and `index_series_cache`'s one row's
  fresh-rederived narrow stamp equals its stored `dataset_version`.
- TC-11: given the `membership_timeline_cache` preserved row's stored `points` for every incident date
  already present in it (not among Stage F's recorded `new_dates`), when
  `verify_membership_timeline_preserved_row` recomputes each via `_membership_timeline` against current
  storage, then every recomputed `size`/`entries`/`exits`/`excluded` field matches the stored point
  exactly, the disposition `preserve_for_incremental_reuse` is CONFIRMED, and zero write occurs.
- TC-12: given a fixture engineered so that one incident date's recomputed membership-timeline value
  disagrees with the row's stored point for that date, when the same verification runs, then it deletes
  the stale row (never silently accepts it), records the exact date and field(s) that disagreed, and the
  disposition flips to `explicit_delete`.
- TC-13: given the 10 "schema/identity/retry" named traps from `docs/goal.md`'s Acceptance section
  (FK-enforced-mode survival; delete+rebuild never rewrites a historical manifest; `source_run_id` never
  rebound; `basis_disclosure` resolves correctly post-reconciliation; all 11 runs share the frozen
  identity; identity drift prevents piecemeal continuation; a simulated partial failure leaves the attempt
  incomplete, never partial progress; a retry redoes the full 11-date set; immutable manifests/audit
  survive a retry byte-unchanged; an unrelated cache is not invalidated solely for carrying a version
  field), when `verify_named_traps` assembles them, then each cites its existing passing test (still
  green) or a fresh live spot-check where the trap concerns current live state — none re-implemented.
- TC-14: given `docs/goal.md`'s named id-reuse scenario (mint a manifest from run id N created at T1;
  delete and rebuild that run; the replacement reuses numeric id N with `created_at=T2`), when the
  existing fixture test proving this is re-run, then it still passes: `source_run_id` remains N, bytes
  and hashes are unchanged, and `basis_disclosure` reports `rebuilt` because `source_run_created_at !=
  current_run.created_at` — id equality alone never proves original-source identity.
- TC-15: given the 8 "J-10/J-11 sequencing" named traps (completing J-10 doesn't imply the 2026-08-11/12
  runs were recomputed; J-10 reaches terminal state without J-11 having run; J-11 cannot start before
  J-10's terminal state; normal lanes stay blocked between J-10 and Stage G; the final replay belongs to
  Stage G not J-10; the recovery-era runs are recognized as temporary, never final; `source_run_id`
  equality alone never proves identity; exact id reuse still yields `rebuilt` when the timestamp differs),
  when `verify_named_traps` assembles them, then each cites its existing passing test, confirmed still
  green.
- TC-16: given the `j11-incident-recovery` boundary is ACTIVE covering an incident date D with a real
  `ScannerRun`, when a fixture-level call to `coverage_from_storage(session, cfg, as_of=D)` finds no
  persisted `CoverageSnapshot` row for D, then `refresh_coverage_snapshot_for` is NOT called (zero write
  to `coverage_snapshot`), and the function falls through to its existing stale/all-zero fallback chain
  unchanged.
- TC-17: given an ordinary (non-incident, non-boundary-covered) date D2 with a real `ScannerRun` and no
  persisted `CoverageSnapshot` row, when `coverage_from_storage(session, cfg, as_of=D2)` runs post-edit,
  then `refresh_coverage_snapshot_for` still fires exactly as before the edit — byte-identical behavior
  for every ordinary date, zero regression.
- TC-18: given a persisted `CoverageSnapshot` row already exists matching the live `dataset_version` for
  any date including an incident date, when `coverage_from_storage` runs, then the guard is never
  consulted and the stored row is served exactly as before — the guard only gates the CREATE branch,
  never a read.
- TC-19: given `test_api_data.py` and `test_data_manager.py` (the two existing files covering
  `coverage_from_storage`), when they run fixture-scoped post-edit, then both pass unchanged.
- TC-20: given a fresh `grep -rn "run_scan(\|get_or_create_manifest(\|refresh_coverage_snapshot_for("
  apps/backend/app/`, when every returned call site is classified, then each is exactly one of: guarded
  (names the guard call and its call site), Stage D's own authorized write
  (`j11_stage_d_execute.py:374`), or explicitly still-open-and-deferred (`scanner.py::resolve_run`,
  `compass.py::get_or_create_manifest`, and any Data-Manager `run_scan`/`persist_run_payload` path named
  by ruling item 5) — the full classification is recorded in the dev handoff.
- TC-21: given `scanner.py` and `compass.py` are explicitly OUT OF SCOPE this iteration, when
  `git diff HEAD -- apps/backend/app/engine/scanner.py apps/backend/app/engine/compass.py` is inspected
  after this iteration's changes are staged, then it returns empty for both files.
- TC-22: given iteration 18's pre-Stage-D full-table sweep and the live current sweep, when
  `build_stage_g_cross_iteration_mutation_accounting` diffs them, then every changed table's delta
  reconciles to exactly Stage D + Stage E + Stage F's already-recorded changes plus this iteration's own
  conditional writes (the membership-timeline delete-if-stale; the boundary's `active` flag on PASS) —
  zero unexplained change anywhere else.
- TC-23: given maintenance isolation is active for the whole iteration, when the engine's dispatch log is
  inspected, then application-service boot, browser-qa-agent, and the replay lane were each refused or
  never dispatched.
- TC-24: given `stage_g_verdict` is a full PASS across every category above, when `finalize_stage_g` runs,
  then it emits exactly `J-11 STAGE D EXECUTED: YES` / `J-11 STAGE E COMPLETE: YES` /
  `J-11 STAGE F COMPLETE: YES` / `J-11 STAGE G VERIFIED: YES` / `J-11 INCIDENT STATUS: FULLY REPAIRED`,
  performs exactly one further write (`maintenance_boundaries.active: 1 → 0` for
  `name='j11-incident-recovery'`, row `id=1` preserved), and a live post-write read confirms `active=0`
  with the row otherwise unchanged.
- TC-25: given `stage_g_verdict` instead reports any FAIL, when `finalize_stage_g` runs, then it performs
  zero further writes beyond any already-covered corrective delete, emits exactly
  `J-11 STAGE D EXECUTED: YES` / `J-11 STAGE E COMPLETE: YES` / `J-11 STAGE F COMPLETE: YES` /
  `J-11 STAGE G VERIFIED: NO` / `J-11 INCIDENT STATUS: NOT REPAIRED — ATTEMPT INCOMPLETE` /
  `J-11 MAINTENANCE BOUNDARY: ACTIVE`, and a live post-check read confirms the boundary's `active` value
  is still `1`.
- TC-26: given AG-10's `memory_cap_mb`/`HOST_GUARD_MEMORY_HIGH` envelope, when the live Stage G
  verification runs (a standalone process, never via `scripts/start-backend.sh`), then its measured peak
  memory (`/proc/<pid>/status` `VmPeak`, reusing `read_process_vm_peak_kb`/`build_memory_check`) is
  recorded in the evidence and compared against the configured ceiling.
- TC-27: given the CLI script is invoked without `--confirm`, when it runs, then it performs zero
  database interaction (not even a read) and exits non-zero; given it is invoked without an explicit
  `--evidence-dir`, when it runs, then it refuses before any config/engine construction and exits
  non-zero.
- TC-28: given J-01/J-04/J-10's passing status rests on the untouched content of `scoring.py`,
  `compass.py`, and `j10_recovery.py` respectively, when `git status --porcelain -uall` / `git diff` is
  inspected against that exact file set after this iteration's changes are staged, then it returns zero
  matches for all three; given `data_manager.py` — the one file this iteration touches — is inspected via
  a function-level diff, then the change is confirmed scoped to exactly the `coverage_from_storage`
  self-heal branch, with zero change to `_cascade_targets`, `remove_price_data`, or any other
  J-10/J-11-relied-upon function in that file.
- TC-29: given AG-9 forbids any live network call and every dated exception is exhausted, when the new
  module, CLI script, and the `data_manager.py` edit are inspected, then zero network-capable call
  appears anywhere in the diff, and the live execution's evidence artifacts record zero outbound
  requests.
- TC-30: given this iteration's new files and evidence folder must be committed before scoring, when
  `git status --short` is inspected at the end of the iteration, then nothing under
  `apps/backend/app/engine/j11_stage_g_verify.py`, `apps/backend/scripts/run_j11_stage_g_verify.py`,
  `apps/backend/tests/test_j11_stage_g_verify*.py`, the `data_manager.py` diff, or
  `runs/goal-market-compass-iter-22/` remains untracked.

## NOTES

- **Assumption-ledger entries filed this iteration** (`runs/goal-session-market-compass/state/
  assumptions.md`): (1) the write-path scoping decision — foreclosing only the freshly-found
  `data_manager.coverage_from_storage` self-heal path this iteration, while leaving
  `scanner.py::resolve_run` (named verbatim by ruling item 5) and `compass.py::get_or_create_manifest`
  (not named by either ruling item 5 or this iteration's coordinator note) explicitly deferred; (2) the
  `membership_timeline_cache` B2 closure methodology — a read-only per-date recompute-and-compare via
  `_membership_timeline` against the preserved row's stored points, with a delete fallback on any
  mismatch, closing iteration 21 auditor's open "consider" question as a required check rather than an
  optional one, on the strength of `docs/goal.md`'s own "no stale derived state remains for the incident
  set" acceptance item already requiring it.
- **Live figures cited above are this planning pass's own read-only spot-check (2026-08-27)**:
  `maintenance_boundaries` holds exactly one row, `id=1`, `name='j11-incident-recovery'`, `active=1`,
  created `2026-08-25 23:49:26.589515` — confirmed via `sqlite3 "file:...?mode=ro"`, never opened for
  write. `coverage_from_storage`'s self-heal check is at `data_manager.py:1547` today (`_upsert_coverage_
  snapshot` at `:1369`, `refresh_coverage_snapshot_for` at `:1409`, the function itself at `:1500`);
  `_membership_timeline` (the pure compute) is at `:563`, `membership_timeline_cached` (the cache
  wrapper) at `:854`. `scanner.py::resolve_run` ends at `:348`; `compass.py::get_or_create_manifest`
  begins at `:1041`. Per this session's own established discipline, the developer must re-derive every
  one of these live and fresh rather than trust this citation — they have moved before.
- **Operational recommendation:** keep `run-goal.sh`'s pump running with `CHAIN_MAINTENANCE_ISOLATION=true`
  and `CHAIN_REQUIRE_FULL_DEPTH=true` set through this iteration's completion — unchanged from
  iterations 19/20/21's own recommendation. If this iteration reaches a full PASS and deactivates the
  boundary, the human should decide when to next set `CHAIN_MAINTENANCE_ISOLATION=false` (or otherwise
  permit a boot) for a future iteration — this spec does not make that call.
- **Escalation flag:** if the fresh preflight finds any drift from Stage D/E/F's certified end state, or
  if any acceptance category below reports a failure, the developer must STOP, leave the boundary
  `active=1`, and report the exact blocker — never invent an intermediate "partially verified" status
  (ruling item 14 explicitly forbids a third state).
- Two standing framework notes carried forward unchanged, per owner instruction to leave them out of
  scope until after Stage G: the request-triggered write-path guard gaps this spec deliberately leaves
  open (`scanner.py::resolve_run`, `compass.py::get_or_create_manifest`), and `goal_gate.py`'s
  duplicate-journey-heading defect, plus the `scripts/automation/` forbidden-lane defect. None is
  addressed by this spec; a future maintenance-boundary hardening pass should treat all three
  write-path gaps (including the one this iteration closes) as one family when it finally redesigns the
  guard's coverage, per the "treat 'the guard covers boot paths only' as the recurring failure mode"
  observation.
- If the reviewer, QA, or auditor lane finds that live verification cannot proceed safely for any reason
  not anticipated above, the correct action is the same as every prior J-11 stage in this session: stop,
  preserve evidence, and report — never force a PASS past a failing check to obtain a "complete" status.
- **If this iteration reaches `J-11 INCIDENT STATUS: FULLY REPAIRED`:** the next decomposer iteration
  should treat J-11 as the evaluator's call to make (not pre-decided by this spec), pick up normal
  Market Compass work per the loop-mechanics gate and the suggested build order in `docs/goal.md`
  ("Loop mechanics" section), and may finally propose the deferred framework fixes (item 8 of the
  coordinator note) and the two now-eligible write-path hardening items above as candidate future scope.
