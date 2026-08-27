# goal-market-compass-iter-22 Execution Plan

## Context check (against docs/goal.md)

Verified directly against `docs/goal.md`'s "OWNER RULING — J-11 Stage D through Stage G recovery
execution AUTHORIZED" (lines 1750-1903, commit `5fe72f5c`, dated 2026-08-26, binding) and the J-11
Acceptance section (lines 1978-2080): this spec is Stage G, the terminal acceptance gate. Item 9 of
that ruling authorizes Stage G unconditionally following a successful Stage F — no further owner
sign-off is required, and the spec correctly does not amend `docs/goal.md`. Cross-checked against
`docs/handoffs/goal-market-compass-iter-21-dev.md` (Stage F: 5 caches emptied, 2 preserved, boundary
still `active=1`) and `-iter-21-audit.md` (verdict `PASS_WITH_GAPS`, gap B2 = the
`membership_timeline_cache` preserved-row proof only covers today's state) — both match this spec's
BACKGROUND and its new `verify_membership_timeline_preserved_row` check verbatim. No drift between the
phase spec and the goal contract was found; no scope creep. `Frontend Present: no` is correct — J-11 is
recorded in `docs/goal.md` as "Walkthrough: waived" (no UI surface of its own).

## What to Build

- New module `apps/backend/app/engine/j11_stage_g_verify.py`: a fresh, read-only preflight (recheck
  boundary/guard, Stage D run presence+identity, Stage E's recorded forward-return outcome, Stage F's
  recorded cache dispositions — any drift halts with zero further checks/writes) followed by one
  verify function per acceptance category — raw inputs, snapshot scope (membership via ids 3148-3158 +
  execution evidence, never `engine_identity` alone), forward-return populations (a)/(b)/(c) with
  population (b) = 0 scored as the CORRECT outcome, manifests (direct SQL only — never
  `get_or_create_manifest`/`GET /api/compass`, the manifest-minting trap), audit/evidence/user-state,
  cache dispositions (5 empty tables + `index_series_cache` stamp), the new
  `verify_membership_timeline_preserved_row` closing auditor gap B2 (per-date recompute via
  `_membership_timeline` vs. the stored row, field-by-field; mismatch -> delete the row, not a silent
  pass), and assembly of the ~18 already-tested named traps. Aggregates into one `stage_g_verdict` with
  no boolean that can pass by construction, then `finalize_stage_g`: on full PASS, emit
  `FULLY REPAIRED` and perform exactly one further write (deactivate, never delete, the
  `j11-incident-recovery` boundary row); on any FAIL, emit `NOT REPAIRED — ATTEMPT INCOMPLETE` and
  leave the boundary `active=1` with zero further writes (beyond the membership-timeline delete already
  covered if that specific check is what failed).
- One surgical, guard-only edit to `apps/backend/app/engine/data_manager.py`'s `coverage_from_storage`
  self-heal branch (near line 1547 — re-derive the live line fresh before editing): import
  `j11_preboot_guard` and consult `evaluate_boundary_for_date_fail_closed` immediately before the
  existing `refresh_coverage_snapshot_for(...)` call; if blocked, fall through unchanged to the
  function's existing stale/all-zero fallback chain. This is the same idiom already live at
  `warmup.py:361` and `forward_testing.py:551` — it closes the one freshly-found gap (iteration 21's
  evaluator) where a future page visit to an incident date would silently repopulate
  `coverage_snapshot` after Stage F cleared it. No other line of the function changes.
- New CLI script `apps/backend/scripts/run_j11_stage_g_verify.py`, mirroring
  `run_j11_stage_f_execute.py`'s `--confirm`/`--evidence-dir` gating exactly.
- Fixture-scoped tests for the new module and CLI script, plus 3 new scenarios extending
  `test_api_data.py`/`test_data_manager.py` for the guard edit (blocked date refused with zero write;
  ordinary date byte-identical to pre-edit behavior; an already-persisted row's read is unaffected) —
  all against isolated engines, never `apps/backend/data/trendora.db`.
- Live, `--confirm`-gated read-only execution against the real database producing the terminal outcome
  block, the write-path re-enumeration (fresh grep of `run_scan(`/`get_or_create_manifest(`/
  `refresh_coverage_snapshot_for(`, classifying every call site as guarded / Stage D's own authorized
  write / still-open-and-deferred), and the cross-iteration mutation accounting (live sweep diffed
  against iteration 18's pre-Stage-D baseline, reconciling every changed table's delta to exactly
  Stage D + E + F + this iteration's own conditional writes).
- Dev handoff at `docs/handoffs/goal-market-compass-iter-22-dev.md` recording every acceptance
  category's evidence, the B2 per-date comparison result, the write-path classification table, the
  memory measurement vs. `memory_cap_mb`/`HOST_GUARD_MEMORY_HIGH`, and the exact terminal-outcome block
  emitted.

## Hard constraints the developer must not violate (all binding, all cited above)

1. **Never touch `scanner.py::resolve_run` or `compass.py::get_or_create_manifest`.** Both are the
   ruling-item-5-deferred request-path gaps; `git diff` for both files must stay empty (TC-21). Only
   `data_manager.py`'s `coverage_from_storage` branch may change in production code.
2. **No application boot of any kind** — no backend, no frontend, no browser-qa-agent, no replay lane.
   The guard fix is proven structurally (fixture tests + a static grep re-enumeration), never
   empirically. Booting is explicitly reserved for a future human decision.
3. **Membership is ids {3148..3158} + Stage D's execution evidence — never `engine_identity` alone**
   (`compute_engine_identity` stamps every run identically regardless of which attempt created it).
4. **Population (b) = 0 is PASS, not a gap.** `data_manager._cascade_targets`/`remove_price_data`
   delete an affected run's `ForwardReturn` rows whole, so a retained-run hole cannot exist — do not
   flag a zero count as a missing repair.
5. **Manifest checks are direct SQL only** — calling `get_or_create_manifest` or `GET /api/compass`
   during verification would itself mint a manifest for one of the 7 manifest-less incident dates.
6. **Only two conditional writes are authorized**: (a) `maintenance_boundaries.active: 1 -> 0` for
   `id=1` on a full PASS only; (b) a `membership_timeline_cache` row delete only if the B2 recompute
   disagrees with the stored point. Every other table (`daily_prices`, `scanner_runs`,
   `scanner_results`, `sector_scores`, `theme_scores`, `forward_returns`, `next_session_manifests`,
   `data_provider_runs`, `watchlist`) must show zero write.
7. **No full pytest suite; no two pytest processes concurrently; never open
   `apps/backend/data/trendora.db` for write from a test** — read-only `sqlite3 "file:...?mode=ro"` for
   any live spot-check outside the engine's own session.
8. **Exactly one of two terminal states, never a third**: `FULLY REPAIRED` (full PASS, boundary
   deactivated) or `NOT REPAIRED — ATTEMPT INCOMPLETE` (boundary stays `active=1`, zero further
   writes). Any preflight drift or category failure halts immediately with the exact blocker named.
9. **Commit everything before scoring.** Iterations 19, 20 and 21 were each flagged at scoring time for
   leaving new files/evidence untracked (iter-21 audit finding Q1) — `git status --short` must show
   nothing under the new module, CLI script, test files, the `data_manager.py` diff, or
   `runs/goal-market-compass-iter-22/`.
10. **AG-10 resource ceiling** — record live peak process memory (`VmPeak`) against
    `server.memory_cap_mb`/`HOST_GUARD_MEMORY_HIGH`; no bulk compute, no parallel writer, only the
    project's own reused measurement helpers.

## Agents Required

- developer: yes -- implement `j11_stage_g_verify.py`, the single guarded edit to
  `data_manager.py`, the new CLI script, and the fixture-scoped tests (new + the 3 extended
  `coverage_from_storage` scenarios), then run the `--confirm`-gated live verification against the real
  database and write the dev handoff, per the constraints above and the full TESTING REQUIREMENTS /
  test-scenario list (TC-1 through TC-30) in `docs/phases/goal-market-compass-iter-22.md`.

## Frontend Present

no

## Files to Create/Modify

- `apps/backend/app/engine/j11_stage_g_verify.py` -- new; preflight + 8 acceptance-category verify
  functions + named-trap assembly + `stage_g_verdict` + `finalize_stage_g` + mutation accounting.
- `apps/backend/app/engine/data_manager.py` -- one surgical guard edit to `coverage_from_storage`'s
  self-heal branch only; zero other line changes (function-level diff must prove this).
- `apps/backend/scripts/run_j11_stage_g_verify.py` -- new; `--confirm`/`--evidence-dir`-gated CLI.
- `apps/backend/tests/test_j11_stage_g_verify.py` -- new; fixture-scoped unit/integration tests.
- `apps/backend/tests/test_j11_stage_g_verify_cli_script.py` -- new; mock-based CLI control-flow tests.
- `apps/backend/tests/test_api_data.py` / `apps/backend/tests/test_data_manager.py` -- extend with the
  3 guard scenarios for `coverage_from_storage`; confirm existing coverage still passes unchanged.
- `runs/goal-market-compass-iter-22/*.json` -- new; live evidence artifacts (preflight, per-category
  results, write-path classification, mutation accounting, terminal outcome).
- `docs/handoffs/goal-market-compass-iter-22-dev.md` -- new; dev handoff.

**Explicitly zero-diff (verify, do not modify):** `apps/backend/app/engine/scanner.py`,
`apps/backend/app/engine/compass.py`, `apps/backend/app/engine/scoring.py`,
`apps/backend/app/engine/j10_recovery.py` (J-01/J-04/J-10's untouched-content proof, TC-28).

## Key Test Scenarios

- Fresh preflight re-derives boundary/guard state, Stage D run presence+identity, Stage E's recorded
  forward-return outcome, and Stage F's recorded cache dispositions live; any single drift halts the
  whole attempt with zero further checks/writes (TC-1, TC-2).
- Snapshot-scope membership resolves via ids 3148-3158 + Stage D's execution evidence; a fixture 12th
  run sharing the identical frozen `engine_identity` but a different id is correctly EXCLUDED (TC-4).
- Forward-return population (a) matches Stage E's recorded 16,592 fill; population (b) = 0 is recorded
  as the CORRECT expected outcome, not a failure; population (c) stays honestly absent (TC-6).
- Manifest verification is a direct SQL `SELECT` only (24 rows, byte-identical stamps) and makes zero
  call to `get_or_create_manifest`/`GET /api/compass` (TC-7).
- `verify_membership_timeline_preserved_row` recomputes each already-cached incident date via
  `_membership_timeline` and matches the stored point exactly (TC-11); a fixture where one date's
  recompute disagrees causes a delete of the stale row, never a silent pass (TC-12).
- `coverage_from_storage`: a boundary-blocked incident date's self-heal is refused with zero write
  (TC-16); an ordinary date's self-heal is byte-identical to pre-edit behavior (TC-17); a read of an
  already-persisted row is unaffected by the guard either way (TC-18).
- A fresh whole-package grep classifies every `run_scan(`/`get_or_create_manifest(`/
  `refresh_coverage_snapshot_for(` call site as guarded / Stage D's own write / still-open-and-deferred
  (TC-20); `scanner.py` and `compass.py` show zero diff from HEAD (TC-21).
- Cross-iteration mutation accounting (live sweep vs. iteration 18's pre-Stage-D baseline) reconciles
  every changed table's delta to exactly Stage D + E + F + this iteration's own conditional writes,
  with zero unexplained change elsewhere (TC-22).
- On a full `stage_g_verdict` PASS, `finalize_stage_g` emits the exact `FULLY REPAIRED` block and
  performs exactly one further write (`maintenance_boundaries.active: 1 -> 0`, row `id=1` preserved,
  live post-write read confirms it) (TC-24); on any FAIL, it emits `NOT REPAIRED — ATTEMPT INCOMPLETE`
  with zero further writes and the boundary still reads `active=1` (TC-25).
- CLI script refuses any DB interaction without `--confirm` and refuses before config/engine
  construction without `--evidence-dir` (TC-27).
- Live peak process memory is recorded against `memory_cap_mb`/`HOST_GUARD_MEMORY_HIGH` (TC-26); zero
  network-capable call appears anywhere in the diff (TC-29).
- End of iteration: `git status --short` shows nothing untracked under the new module, CLI script, test
  files, the `data_manager.py` diff, or `runs/goal-market-compass-iter-22/` (TC-30).
