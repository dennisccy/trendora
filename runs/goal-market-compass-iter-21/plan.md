# goal-market-compass-iter-21 Execution Plan

## What to Build
J-11 Stage F: classify all seven `dataset_version`-bearing derived-cache tables left stale by
Stage D (iter-19, live) and Stage E (iter-20, live), and delete exactly the rows proven stale —
so nothing in the database can silently serve pre-repair content once the app eventually
reboots. This is the ONE authorized write this iteration: bounded row deletion across at most 6
cache tables (~1,644 rows). No price, snapshot, or manifest row is touched.

1. **Fresh read-only preflight before any write** — reuse, never reimplement:
   `j11_stage_d_execute.recheck_maintenance_boundary_and_guard`; a new
   `confirm_stage_e_complete_and_unrestamped` (all 11 incident runs present/unrestamped, each
   `ForwardReturn` count matching `runs/goal-market-compass-iter-20/j11-stage-e-execute-population-report.json`
   exactly, including run 3158's legitimate 0); `j11_stage_e_execute.check_engine_identity_matches_stage_d`
   against the frozen `53d2ffd1…` identity; `j11_stage_e_execute.confirm_manifests_unchanged` against
   the certified iter-16 baseline. Combine into `stage_f_preflight_gate_verdict`. Any drift → zero
   writes, exact blocker reported, STOP.
2. **`derive_cache_table_inventory()`** — introspects `app.models` at run time for every
   `dataset_version`-bearing table (never a hardcoded list). Expected today: 7 tables
   (`event_study_cache`, `market_phase_cache`, `forward_aggregate_cache`, `index_series_cache`,
   `membership_timeline_cache`, `availability_cache`, `coverage_snapshot`); report explicitly if
   the live count differs.
3. **`classify_cache_table()` per table** — recompute the CURRENT live stamp from the table's actual
   writer/version function (`research._dataset_version` for the 3 broad-stamp caches,
   `research._membership_dataset_version` for the 3 narrow-stamp caches, its own narrow stamp for
   `index_series_cache`), read every distinct stored stamp, and compare every stored row's
   `created_at` against Stage D's frozen execution-start instant (re-derive fresh from the iter-19
   evidence AND cross-check live `MIN(created_at)` over `scanner_runs` ids 3148-3158 — never
   hardcode the citation).
4. **Apply dispositions:** `explicit_delete` for `event_study_cache`, `market_phase_cache`,
   `forward_aggregate_cache`, `coverage_snapshot`, `availability_cache` — required outright for
   `availability_cache` (the real finding this planning pass made: `data_manager.availability_from_storage`'s
   "no ingest job in flight" branch would otherwise serve the PRE-INCIDENT heatmap unflagged as
   stale, `stale: False`, the first time `/api/data/availability` loads after a post-Stage-G
   reboot — an AG-3/AG-8 risk, not hygiene). `prove_unaffected_leave_alone` for `index_series_cache`
   (its own narrow stamp still matches; `daily_prices` is byte-unchanged). `membership_timeline_cache`
   gets `preserve_for_incremental_reuse` ONLY if a live proof shows `membership_timeline_cached`'s
   MISS-repair `append_forward` condition (`min(new_dates) > prev_dates[-1]`) evaluates `False` for
   the incident dates against the live snapshot tail (expected — the incident dates aren't at the
   tail) — otherwise fall back to `explicit_delete` and record the tradeoff in the handoff.
5. **`execute_stage_f_cache_disposition`** — the one authorized write: delete exactly the
   already-classified stale rows in `explicit_delete` tables; zero writes elsewhere.
6. **`live_verify_cache_dispositions` + `build_stage_f_mutation_accounting`** (reusing
   `j11_maintenance.capture_full_table_sweep`/`diff_full_table_sweeps`) **+ `stage_f_execution_outcome`**
   — post-write proof that `changed_existing_tables` is a subset of exactly the `explicit_delete`
   set and every other table shows zero fingerprint change.
7. New CLI script `run_j11_stage_f_execute.py`, mirroring `run_j11_stage_e_execute.py`'s
   `--confirm`/`--evidence-dir` gating exactly.
8. Fixture-scoped tests only (`app.db.make_engine` isolated engine, never live `trendora.db`)
   covering TC-1–TC-19 (see Key Test Scenarios).
9. The live `--confirm`-gated execution against `apps/backend/data/trendora.db`, independent live
   re-verification of every claimed figure, and the dev handoff at
   `docs/handoffs/goal-market-compass-iter-21-dev.md` with the exact terminal-vocabulary block.

**Explicitly OUT OF SCOPE** (do not build): Stage G (verification/acceptance gate — the only stage
that may declare the incident repaired); eagerly regenerating/warming any of the 7 caches through
their canonical producer "while we're here" — deferred to the existing safe post-Stage-G warm
path; any change to a canonical producer/serving function; any write to `daily_prices`/
`scanner_runs`/`scanner_results`/`sector_scores`/`theme_scores`/`forward_returns`/
`next_session_manifests`/`data_provider_runs`/`watchlist`/`maintenance_boundaries`; deactivating
the `j11-incident-recovery` boundary; any network/provider call; any schema/DDL migration; any
J-01–J-09 product/UI work.

## Alignment check
Verified directly against `docs/goal.md` (not taken on the coordinator note's word alone): the
"OWNER RULING — J-11 Stage D through Stage G recovery execution AUTHORIZED" (owner, 2026-08-26)
item 8 authorizes Stage F unconditionally once Stage E succeeds — no new sign-off, no goal.md
amendment needed. `docs/handoffs/goal-market-compass-iter-19-dev.md` and `-iter-20-dev.md`
independently confirm Stage D and Stage E both executed live and cleanly (committed at `c7351663`
and `fe17a81a`, current HEAD); `state/iteration-state.md` agrees J-11 is still partial pending
Stage F/G. Maintenance isolation (backend/frontend/browser-QA/replay/Data Manager all OFF) is
binding through Stage G per ruling item 4 — this matches the phase spec's own
`Frontend Present: no` metadata and its "Browser: none — maintenance isolation forbids
application-service boot" testing requirement. No drift from `docs/goal.md` found; the spec is
narrowly scoped to J-11 step 6 + ruling item 8 and explicitly excludes Stage G and cache
regeneration.

## Agents Required
- backend-data: yes — one `developer` agent implements items 1-9 above; there is no separate
  frontend workstream. The developer must independently re-derive every cited live figure
  (stamps, counts, `created_at` values, the Stage D start instant) fresh against the live database
  rather than trust this plan, the phase spec, or the coordinator note — established practice
  after iter-19/iter-20 (see those handoffs' own "never trusted... alone" language).
- frontend-ux: no — zero UI, route, or component changes.

Frontend Present: no

## Constraints & Operating Mode (binding for every lane this iteration)
- **Maintenance isolation, whole iteration:** no backend boot, no frontend boot, no
  browser-qa-agent, no deterministic-replay lane, no Data Manager, no ordinary API request, no
  normal warmup, no second/unrelated producer. `CHAIN_MAINTENANCE_ISOLATION=true` and
  `CHAIN_REQUIRE_FULL_DEPTH=true` must be verified present in-process before any work begins; if
  the engine cannot provide full-depth/isolation, STOP and report rather than silently demoting to
  lean.
- **Boundary stays active:** `j11-incident-recovery` remains `active=1` at the end of this
  iteration regardless of outcome — never deactivate.
- **Resource discipline (AG-10):** the authorized write is small and bounded on its own; the real
  risk is eagerly regenerating any cache "while we're here" — explicitly forbidden
  (`_membership_timeline`'s documented >300s hang risk on this DB size). Measure and record live
  peak VmPeak against `memory_cap_mb: 8192` / `HOST_GUARD_MEMORY_HIGH: 12G` (confirmed current in
  `config.yaml:1377` / `host-guard.env:66`).
- **DB access:** read-only `sqlite3 "file:<path>?mode=ro" "..."` is fine for spot checks; never
  copy, move, or open-for-write `apps/backend/data/trendora.db` outside the authorized
  module/CLI path.
- **Tests:** targeted files only (`test_j11_stage_f_execute*.py`), never the full suite, never two
  pytest processes concurrently, never a fixture that touches the live DB.
- **Fail-closed on any drift:** a restamped/missing incident run, a `ForwardReturn` mismatch,
  boundary/guard drift, an identity mismatch, or — gravest — any cache row with `created_at` at or
  after Stage D's frozen start instant, halts the whole attempt before any write; report the exact
  blocker, never silently resolve.
- **No tautological checks:** iteration 20's audit flagged three Stage-E checks that could never
  fail by construction (`population_a_pre_was_zero`, `population_b_never_decreased` over a
  structurally-empty map, `population_c_latest_run_observable_ceiling_respected`). Every boolean
  this module computes must be traceable to a live- or fixture-derived value a deliberately broken
  fixture can flip — the reviewer checks this explicitly against those three named checks.

## Files to Create/Modify
- `apps/backend/app/engine/j11_stage_f_execute.py` — new; Stage F execution module (items 1-6).
- `apps/backend/scripts/run_j11_stage_f_execute.py` — new; `--confirm`/`--evidence-dir`-gated CLI.
- `apps/backend/tests/test_j11_stage_f_execute.py` — new; fixture-scoped unit/integration tests.
- `apps/backend/tests/test_j11_stage_f_execute_cli_script.py` — new; CLI control-flow tests.
- `docs/handoffs/goal-market-compass-iter-21-dev.md` — new; dev handoff with terminal vocabulary.
- `runs/goal-market-compass-iter-21/j11-stage-f-execute-*.json` — new; live-run evidence artifacts.
- Reused, read-only, must stay byte-unchanged: `apps/backend/app/engine/j11_stage_d_execute.py`,
  `apps/backend/app/engine/j11_stage_e_execute.py`, `apps/backend/app/engine/j11_maintenance.py`,
  `apps/backend/app/models.py`, `apps/backend/app/engine/research.py`,
  `apps/backend/app/engine/data_manager.py` (calls `availability_from_storage`/
  `coverage_from_storage`, does not modify them).
- Must show zero diff (verify via `git status --porcelain -uall`): `scoring.py` (J-01),
  `compass.py` (J-04), `data_manager.py`'s J-10 recovery code (J-10), and every file not named
  above.

## Key Test Scenarios
- **Preflight:** proceeds (empty `blocking_reasons`) only when boundary/guard, all 11 incident
  runs present/unrestamped with matching `ForwardReturn` counts, identity, and the 24-row manifest
  dump all agree live (TC-1); any single drift zero-writes and persists the exact blocker (TC-2).
- **Inventory:** introspection returns exactly the 7 known tables today; a synthetic 8th
  `dataset_version` model changes the returned set, proving it isn't a hardcoded list in disguise
  (TC-3).
- **Classification:** the 3 broad-stamp and 3 narrow-stamp caches each report zero stored rows
  matching the fresh live stamp and every `created_at` earlier than Stage D's start (TC-4, TC-5);
  `index_series_cache`'s fresh stamp still equals its one stored row's stamp, disposition
  `prove_unaffected_leave_alone`, zero deletions (TC-6).
- **The collision trap:** a fixture engineered to reproduce an identical `dataset_version` string
  via delete-and-recreate still gets caught and correctly disposed via the `created_at` check, not
  the stamp string alone (TC-7).
- **Execution:** deletion touches exactly the pre-classified stale rows in the `explicit_delete`
  tables and nothing else; live post-write `COUNT(*)` is 0 in each (TC-8).
- **membership_timeline_cache:** the live `append_forward` condition evaluates `False` for the
  incident-date pattern (safe gap-insert branch would run) → `preserve_for_incremental_reuse`; an
  ambiguous/append-eligible fixture instead falls back to `explicit_delete`, both outcomes
  recorded (TC-9).
- **The correctness payoff:** post-deletion, a fixture-level `availability_from_storage` call
  returns the honest "not yet computed" sentinel, never a stale `stale: False` payload (TC-10).
- **Mutation accounting:** `changed_existing_tables` is a subset of exactly the `explicit_delete`
  set, zero unexpected new/removed tables (TC-11); every table outside the seven-cache family
  shows zero fingerprint change (TC-12).
- **Memory:** live VmPeak recorded and compared against the configured ceiling (TC-13).
- **CLI gating:** missing `--confirm` → zero DB interaction, non-zero exit; missing
  `--evidence-dir` → refuses before config/engine construction (TC-14).
- **Terminal vocabulary:** dev handoff and evidence state exactly `J-11 STAGE D EXECUTED: YES`,
  `STAGE E COMPLETE: YES`, `STAGE F COMPLETE: YES/NO` (matching true outcome),
  `STAGE G VERIFIED: NO`, `INCIDENT STATUS: NOT REPAIRED — ATTEMPT INCOMPLETE`,
  `MAINTENANCE BOUNDARY: ACTIVE`, `LIVE PRE-BOOT GUARD: ARMED` (TC-15).
- **No tautologies:** reviewer traces every boolean check to a value a broken fixture can flip,
  explicitly against iter-20's three named tautological checks (TC-16).
- **Isolation:** any lane other than developer/reviewer/file-scoped-QA/auditor attempting to run
  (service boot, browser-qa-agent, replay) is refused and logged (TC-17).
- **Carry-forward:** `git status --porcelain -uall` grepped against `scoring.py`/`compass.py`/
  `data_manager.py`'s J-10 code returns zero matches (TC-18); zero network-capable call anywhere
  in the diff or evidence (TC-19, AG-9).
- **Browser:** none this iteration — `browser-qa-agent` does not run; QA is file-scoped/fixture-only.
