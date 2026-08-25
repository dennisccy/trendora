# Goal Iteration 17 — J-11 maintenance-boundary lifecycle: arm/disarm code + AG-8 fix, fixture-proven (live arm stays owner-blocked)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** market-compass
- **Iteration:** 17
- **Mode:** next
- **Depth:** full
- **Full trigger:** 1 — the guard sits on `warmup.ensure_latest_snapshot`, the shared boot path every future page's data depends on, and this work spans ≥3 modules (`j11_preboot_guard.py`, new committed arm/disarm entrypoints, `j11_maintenance.py`'s canonical `INCIDENT_DATES` source) whose interaction is exactly the class of failure one journey's tests do not cover — this same code area has produced 7 straight iterations where only the independent auditor caught what developer, reviewer and QA all missed. The evaluator's own recommendation for this iteration is also explicitly `full` and binding.
- **Target journeys:** J-11
- **Required-still-passing journeys:** J-01, J-04, J-10
- **Frontend Present:** no
- **Anti-goal reminders:**
  - AG-1: A score, ranking, or "edge" MUST NOT be presented as proven/confident unless it is backed by a **passing certified-claim entry** in the evidence ledger (out-of-sample, control-beating). Unbacked values MUST render a "not yet proven" state. *(critical)*
  - AG-5 — Preserve determinism and no-lookahead: scoring uses bars ≤ as-of; forward returns use bars > as-of; the manifest for close D derives only from state stored at or before D; never introduce lookahead anywhere. *(critical)*
  - AG-7: No hard-coded credentials, API keys, or tokens in source files. *(critical)*
  - AG-8 — Resilience to data-shape and data-scale change: widening the data basis must never crash an existing page or exhaust memory — consumers of widened fields are re-validated, the UI degrades gracefully (contained error boundary, honest "—"/NA placeholder), and unbounded whole-table ORM loads are forbidden (the delta engine reads column-projected selects, never full record_json sweeps). *(critical)*
  - AG-9 — Offline-deterministic ingest: ingest jobs run only against the committed seed / local provider fixtures — no live external network calls or paid data services without an explicit goal.md amendment. *(critical)* Both dated exceptions (the J-10 recovery fetch, the AVB diagnostic fetch #2) are exhausted; this iteration makes **zero** network calls.
  - AG-12 — Manifest immutability: a stored `next_session_manifests` row and its exported file are never mutated or deleted by any later ingest, rebuild, data removal, config change, or code change; corrections happen only as new version rows; a historical view never substitutes a newer manifest. *(critical)*
  - AG-17 — Repair never rewrites provenance (owner, 2026-08-20): restoring deleted historical data MUST NOT retroactively change research provenance… `prospective_eligible` is never upgraded merely because historical data was later repaired… *(critical)*
  - AG-18 — The authorized manifest migration preserves everything (owner, 2026-08-23): the bounded `next_session_manifests` schema migration authorized in J-11 step 11 (ruling A1) removes the `source_run_id` foreign-key constraint and **nothing else**… No other table's schema may be altered under that authorization. *(critical)*

## GOAL

Make the J-11 pre-boot incident guard's arm/disarm lifecycle production-capable and fully proven on disposable state — including the AG-8 fix and the owner's 9 named tests — so that creating the live `maintenance_boundaries` table is the *only* remaining step before iteration 16's boot-path safety hole closes, while leaving that one live step, and Stage D itself, exactly where the owner's 2026-08-25 ruling leaves them: not authorized.

## BACKGROUND

Iteration 16 built the pre-boot guard and proved it correct on fixtures, but the evaluator found it inert against the live database (no `MaintenanceBoundary` row ever registered — `maintenance_boundaries` doesn't even exist there) and returned STALLED, recommending the owner arm it. The owner responded (2026-08-25, commit `9f71d4d0`) with the "J-11 maintenance-boundary lifecycle AUTHORIZED" ruling: it authorizes the lifecycle's *code* in full — production arm/disarm entrypoints, the AG-8 bounded-query fix, fail-closed hardening, 9 named tests (A)-(I) — but pre-emptively blocks the one live-database step, because the table doesn't exist and creating it is explicitly "NOT authorized." The ruling's own text instructs that sub-step to "return STALLED with the blocker named," while requirements 1, 2, 3, 5, 6 and the arm path's *code* (requirement 4) "are NOT blocked and must still be delivered in full." This iteration targets exactly that authorized slice: everything proven on fixture/disposable state or via strictly read-only live inspection; nothing writes to `trendora.db`. It also folds in one small, safe rider iteration 16 itself flagged (see NOTES / assumption ledger): the recorded AVB readiness label is the honest-but-conservative `AVB-B` rather than the correct `AVB-A`, because the counterfactual trace's volume basis went stale the moment the AVB volume correction landed (iter-16's own second lesson below). Applicable lessons: iter-16's "a guard's live state must be checked, never assumed" (drives the live read-only verification below) and its "a corrected value invalidates any counterfactual that read the old value" (drives the AVB-A re-derivation); iter-12's mtime+WAL-size instrument as the primary "zero writes" proof (drives the before/after DB fingerprint). Per this agent's own operating rules, the need for continued maintenance isolation is stated here in prose rather than as a metadata line: **this iteration must not boot the backend, the frontend, browser QA, or the deterministic replay lane at any point** — every check below is either a disposable/in-memory fixture test or a strictly read-only inspection of the live `trendora.db` (`mode=ro` + `PRAGMA query_only=ON`), matching the discipline iterations 11-16 already established.

## IN SCOPE

### Backend
- [ ] Bound the whole-table ORM load in `evaluate_boundary_for_date` (`apps/backend/app/engine/j11_preboot_guard.py:143`) — the AG-8 fix required by the owner's ruling item 3 — while preserving its exact fail-closed semantics, including the case where a row's `active` column is stored as SQL `NULL` (not `False`): that row must still surface as ambiguous/blocking under the new bounded query, never be silently excluded by a naive equality filter (`active = 1` alone drops `NULL` rows in SQLite comparison semantics — this is the specific regression trap to avoid).
- [ ] Add a committed, production-capable **arm** entrypoint under `apps/backend/scripts/` (following the existing `run_j11_*.py` convention) that calls `register_j11_incident_boundary`, is idempotent, sources its date-set only from `j11_maintenance.INCIDENT_DATES` (never a re-typed literal), and makes its mutation obvious (prints the boundary row before/after). Do **not** invoke it against `apps/backend/data/trendora.db` this iteration — fixture/temp-DB invocation only.
- [ ] Add a companion, production-capable **disarm** entrypoint calling `clear_boundary`, scoped strictly by boundary name so it never touches an unrelated boundary. Do **not** invoke it against any live-armed state this iteration (nothing is live-armed yet).
- [ ] Deliver the owner's 9 named tests, items (A)-(I), extending `apps/backend/tests/test_j11_preboot_guard.py` (currently 17 tests, all disposable/in-memory) — keep every existing test green.
- [ ] Strictly read-only live verification (no write path of any kind): confirm `maintenance_boundaries` is still absent from the live `sqlite_master`, and call the real, unmodified `evaluate_boundary_for_date` against a read-only session opened on the live DB for `2026-08-12`, persisting the result as evidence of the exact current exposure (satisfies the ruling's "verify through the same production guard entry point using a non-writing diagnostic/test harness" instruction).
- [ ] Capture `trendora.db` file mtime + size + `-wal` size at the true start and true end of this iteration (an iter-17 equivalent of iteration 16's `j11-iter16-readiness-db-file-true-start.json` / `-true-end.json`) and confirm all three are byte-identical — the primary "zero live writes" instrument (iter-12 lesson), corroborated by, never replaced by, any narrower before/after fingerprint pair.
- [ ] Rider — re-run the AVB Stage D readiness classification supplying `volume_override` to both decision-impact trace calls (`trace_universe_resolver_impact`, `trace_scoring_and_selection_impact`) so the counterfactual representation's close **and** volume move on the same hypothetical basis, instead of pairing a counterfactual close with the already-corrected DB volume (the exact hybrid iter-16's second lesson identified — its fingerprint is an A/B ratio landing exactly on `bridge_factor`). Persist the corrected classification as a **new** iter-17 evidence artifact under `runs/goal-market-compass-iter-17/`; do not edit iteration 16's `j11-stage-d-readiness.json` (immutable evidence). This does **not** re-run `run_j11_avb_correction.py` (spent, "do not redo") — only the read-only classification/diagnostic is re-derived.
- [ ] Render the owner-facing status lines in the dev handoff exactly as specified in DEFINITION OF DONE below, naming the live-arm blocker rather than silently attempting or silently omitting it.

### Frontend
None — backend-only; no frontend file is touched this iteration.

### New user-facing capability
None. J-11 remains an internal maintenance repair with no UI surface of its own (walkthrough waived per `docs/goal.md` J-11 Acceptance).

### New information displayed
None.

### New user actions
None.

### UI surface changes
None.

### Product surface delta
None — invisible to any user-facing surface. This iteration hardens the safety substrate that must be effective before J-11's later, still-unauthorized stages may ever run against the live database.

### Blueprint conformance
No new surfaces — matches iterations 13-16's own precedent (none added a blueprint.md entry) and iteration 16's coherence audit finding that no Data Contract row names `daily_prices`, a Stage-D baseline, or maintenance/incident-boundary state as a *displayed* value; all of it is internal safety/evidence state. No edit to `runs/goal-session-market-compass/state/blueprint.md` is made this iteration.

### Data-contract additions
None. `MaintenanceBoundary` state, the arm/disarm entrypoints, and the corrected AVB readiness artifact are backend-internal safety/evidence state, never routed through an endpoint or UI component.

## OUT OF SCOPE

- Creating the `maintenance_boundaries` table on the live `apps/backend/data/trendora.db`, or invoking the arm path against it — explicitly **not authorized** by the owner's 2026-08-25 ruling ("do not create it and do not migrate to it"). This sub-step is expected to return `STALLED` with this exact blocker named, per the ruling's own text — that is the anticipated, correct outcome, not a failure of this spec.
- Invoking the disarm path against any live-armed state (nothing is live-armed to disarm).
- J-11 Stage D execution (regeneration of the 11 incident dates) or any later J-11 stage — remains **not authorized**.
- Any schema migration, `ALTER`, or table rewrite of any kind — "No schema migration" is explicit in the ruling.
- Any write to `daily_prices`, `scanner_runs`, `scanner_results`, `sector_scores`, `theme_scores`, `forward_returns`, `next_session_manifests`, `data_provider_runs`, or any other research/business table.
- Booting any application service, browser QA, or the deterministic replay lane.
- Changes to the existing `warmup.py` guard call-site wiring itself (already correct and coherence-audited in iteration 16), beyond whatever the bounded-query signature change requires at its call boundary.
- The five older open owner questions (J-09's 3.44 GB figure, J-06's "underlying run unavailable" wording, J-01's first two test-step rewording, whether an empty "next-session focus" is acceptable, whether MNST joins the recovery list) — unchanged, non-blocking, not this iteration's job.
- The `scripts/automation/` forbidden-test-lane defect and `goal_gate.py`'s duplicate-journey-heading defect — framework-level defects outside `docs/goal.md`'s Key Capabilities; flagged for the record in NOTES, not fixed here (scope-creep guard).
- Any redesign of J-10/J-11 semantics, candidate thresholds, manifest contract, or research architecture.

## DEFINITION OF DONE

- [ ] AG-8 fix lands: the live boot-path query in `evaluate_boundary_for_date` is bounded and provably preserves fail-closed behavior on `NULL`/unreadable `active` state and on a table containing many irrelevant rows — closes iteration 16's minor, unresolved AG-8 ledger entry (TC-4, TC-5).
- [ ] All 11 `j11_maintenance.INCIDENT_DATES` individually proven blocked once a boundary is armed on disposable state; a non-incident date proven unaffected (TC-2, TC-3).
- [ ] A committed, production-capable arm entrypoint exists, is idempotent, and (proven on fixture state) writes only to `maintenance_boundaries` (TC-6, TC-7, TC-8).
- [ ] A committed, production-capable disarm entrypoint exists and, given multiple registered boundaries, mutates only the boundary named at invocation, leaving every other boundary's row unchanged (TC-9, TC-10).
- [ ] All 9 owner-named tests (A)-(I) pass on disposable/fixture state; all pre-existing `test_j11_preboot_guard.py` tests remain green (TC-1 through TC-10 collectively).
- [ ] Live read-only verification confirms `maintenance_boundaries` is still absent from the live DB and the real `evaluate_boundary_for_date` function still returns `blocked: False` for `2026-08-12` against a strictly read-only live session (TC-11).
- [ ] Zero live writes to `trendora.db` proven via mtime + size + `-wal` size, identical at true start and true end (TC-12).
- [ ] AVB Stage D readiness re-derived with `volume_override` applied to the counterfactual trace; honest `AVB-A` label recorded in a new iter-17 artifact; iteration 16's artifact stays byte-unedited (TC-13).
- [ ] The four owner-facing status lines render exactly as specified, with the live-arm blocker named rather than silently skipped or silently attempted (TC-14).
- [ ] Target journey J-11 advances within `partial`: the maintenance-boundary lifecycle deliverables above are fixture- and live-read-only-verified — no browser-qa lane runs under maintenance isolation, matching iterations 11-16. Stage D remains NOT authorized and is not attempted.
- [ ] Required-still-passing journeys (J-01, J-04, J-10) remain carried at their last-verified status — maintenance isolation forbids re-verification via browser/replay this iteration; confirm (and cite in the dev handoff) that this iteration's diff touches none of `apps/backend/app/api/*`, `scoring.py`, `sectors.py`, or `compass.py`, so none of their served values could have moved.
- [ ] No anti-goal violation introduced; AG-8's minor iteration-16 ledger entry is closed by this iteration's fix.
- [ ] Unit tests pass; no regressions.
- [ ] Dev handoff written at `docs/handoffs/goal-market-compass-iter-17-dev.md`.

## TESTING REQUIREMENTS

- Browser: None — maintenance isolation (owner ruling, `docs/goal.md` J-11 step 11, 2026-08-25) forbids application-service boot and the browser-QA/replay lanes this iteration; every claim above is proven via fixture/unit tests plus strictly read-only live-DB inspection.
- Unit/integration: extend `apps/backend/tests/test_j11_preboot_guard.py` with the owner's 9 named cases (A)-(I) plus the `NULL`-active bounded-query regression case, all on in-memory/fixture SQLite engines, never the live file; extend or add a script-level test for the new arm/disarm entrypoints (idempotency, scoping, no-forbidden-writes).
- Error cases: malformed/missing `quarantined_dates_json`, an `active` column stored as `NULL`, and an unexpectedly duplicated/ambiguous active-boundary state must all fail **closed** (blocked), never fail open.

Test-first contract — numbered scenarios (every DEFINITION OF DONE checkbox maps to at least one of these; Data-contract additions are "none" so none apply here):

- TC-1: given a fixture SQLite database with zero `MaintenanceBoundary` rows, when `evaluate_boundary_for_date` is called for any date, then it returns `{"blocked": False, "boundary_name": None}`.
- TC-2: given a fixture database with the J-11 boundary registered `active=True` and `quarantined_dates_json` equal to the sorted ISO form of all eleven `j11_maintenance.INCIDENT_DATES` values, when `evaluate_boundary_for_date` is called once for each of the eleven dates individually, then every one of the eleven calls returns `blocked: True` naming that boundary.
- TC-3: given the same armed boundary as TC-2, when `evaluate_boundary_for_date` is called for `2026-07-23` (a surviving, non-incident date), then it returns `blocked: False`.
- TC-4: given a fixture database with one `MaintenanceBoundary` row whose `active` column is stored as SQL `NULL`, when the new bounded-query implementation of `evaluate_boundary_for_date` evaluates any date, then the result is `blocked: True, ambiguous: True` naming that row — the row is not excluded by the query's new filter/bound.
- TC-5: given a fixture database containing 50 additional `active=False` or otherwise irrelevant boundary rows plus one `active=True` row whose date-set contains the queried date, when `evaluate_boundary_for_date` runs, then it returns `blocked: True` for that date and the test asserts the executed query is bounded (row-fetch count or emitted SQL clause asserted directly, not only the resulting boolean).
- TC-6: given no `MaintenanceBoundary` row exists in a fixture database, when the committed arm entrypoint is invoked once, then exactly one row is created with `active=True` and `quarantined_dates_json` equal to the sorted ISO form of `j11_maintenance.INCIDENT_DATES`.
- TC-7: given the armed state from TC-6, when the same arm entrypoint is invoked a second time against the same fixture database, then the row count for that boundary name is still exactly 1 and its stored fields are unchanged.
- TC-8: given a fixture database pre-loaded with non-empty `daily_prices`, `scanner_runs`, and `watchlist` tables, when the arm entrypoint runs, then a before/after row-count-and-content comparison of every table other than `maintenance_boundaries` shows zero changed rows.
- TC-9: given a fixture database with two active boundaries — the J-11 boundary and one differently-named boundary covering different dates — when the committed disarm entrypoint is invoked by the J-11 boundary's name only, then that row's `active` flips to `False` and the other boundary's row is unchanged in every field.
- TC-10: given the disarmed state from TC-9, when `evaluate_boundary_for_date` is called for an incident date, then it returns `blocked: False`, and when it is called for a date inside the other, still-active boundary's own set, it returns `blocked: True` naming that other boundary.
- TC-11: given the live `apps/backend/data/trendora.db` opened strictly read-only (`mode=ro` plus `PRAGMA query_only=ON`), when the unmodified production `evaluate_boundary_for_date` function is called against that session for `2026-08-12`, then it returns `blocked: False`, and a companion query `SELECT count(*) FROM sqlite_master WHERE type='table' AND name='maintenance_boundaries'` returns `0` — both persisted as evidence.
- TC-12: given `trendora.db`'s file mtime, file size, and `-wal` file size recorded at the true start of this iteration, when the same three values are recorded again at the true end, then all three are byte-identical.
- TC-13: given the committed iteration-15 AVB provider-fetch evidence and the iteration-16-corrected `daily_prices` volume cells, when the Stage D readiness classification is re-run with `volume_override` supplied to both decision-impact trace calls, then the persisted new artifact records classification `AVB-A` (not `AVB-B`), the A/B dollar-volume ratio on both `2026-08-11` and `2026-08-12` lands within the same relative tolerance the calibration-window check already uses (not at the exact `bridge_factor` value), `READY: YES` is unchanged, and iteration 16's own `j11-stage-d-readiness.json` file hash is unchanged.
- TC-14: given all of the above, when the dev handoff states the owner-facing status, then it reads exactly `J-11 STAGE D READY: YES`, `J-11 STAGE D AUTHORIZED: NO`, `J-11 MAINTENANCE BOUNDARY: NOT ACTIVE`, `J-11 LIVE PRE-BOOT GUARD: NOT ARMED`, and names the live-arm sub-step of the owner's requirements 4 and 7 as blocked by the table's absence rather than omitting or silently attempting it.

## NOTES

- Pre-iteration DB baseline (independently captured by the decomposer, read-only, 2026-08-25): `trendora.db` mtime `1787670395`, size `8365871104` bytes, `-wal` size `0` bytes, live table count `24`, `maintenance_boundaries` count `0`. The dev handoff's true-start capture is expected to reproduce these exact figures; the true-end capture must match them exactly too.
- Escalation flag: none. This is the fifth consecutive J-11-only iteration under maintenance isolation (iters 13-17). If iteration 18 again ends STALLED purely on the owner's own reserved live-arm/Stage-D decision with no new tractable non-owner work identified, the next decomposition pass should consider the one-line "all remaining work is human-blocked" spec per the priority rubric rather than inventing further riders.
- Standing framework notes carried forward, unchanged, not this iteration's job: the defect that once let a forbidden test lane run is still unfixed in `scripts/automation/`; `goal_gate.py`'s duplicate-journey-heading defect is still unfixed and must be closed before any `GOAL_ACHIEVED` certification.
