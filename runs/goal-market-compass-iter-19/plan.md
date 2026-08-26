# goal-market-compass-iter-19 Execution Plan

## Alignment check

Verified directly against `docs/goal.md` (not trusted from the phase spec's paraphrase alone): read
`git show 5fe72f5c` in full. The commit adds exactly one block, "OWNER RULING — J-11 Stage D through
Stage G recovery execution AUTHORIZED" (owner, 2026-08-26, 155 insertions, `docs/goal.md` the only file
touched). Its 14 numbered rulings map onto this spec's IN SCOPE/OUT OF SCOPE/DEFINITION OF DONE exactly:
ruling 1 (Stage D authorized, exact 11-date `INCIDENT_DATES` set) → What to Build §1; ruling 2 (fresh
identity immediately before first write, never iter-10/14/16/17/18 identities) → §1b; ruling 3 (raw
inputs immutable, no fetch) → Guardrails; ruling 4 (isolation mandatory through Stage G) → Guardrails;
ruling 5 (ordinary-writer gaps recorded, deferred, isolation keeps them unreachable, do not expand scope
to fix them) → OUT OF SCOPE, restated in Guardrails; ruling 6 (exact write scope, existing scanner path
only) → §1c; rulings 7-9 (Stage E/F/G) → correctly OUT OF SCOPE this iteration, a disclosed scoping
decision (assumptions.md entry 1), consistent with every prior J-11 stage in this session getting its
own iteration; ruling 10 (whole-attempt failure semantics, no resume-from-next-date) → §1c/Guardrails;
ruling 11 (boundary stays active regardless of D/E/F outcome) → Guardrails; ruling 12 (normal Market
Compass work stays blocked) → correctly excluded; ruling 13 (launch conditions) → see environment check
below; ruling 14 (exact two-terminal-state vocabulary) → Definition of Done / dev-handoff requirement.
**No drift found** between the ruling, the phase spec, and this plan.

**Environment check (an independently-observed operator fact, not a self-declaration):** this
orchestrator's own process environment carries `CHAIN_MAINTENANCE_ISOLATION=true` and
`CHAIN_REQUIRE_FULL_DEPTH=true` (confirmed via `env`, 2026-08-26). Per anti-pattern 25
(`.claude/anti-patterns/25-self-justifying-governor-bypass.md`), a governor must never accept the
governed agent's own prose as its input — these two flags are exactly that kind of operator knob, and
this plan does not, and must not, assert isolation is "active" as if writing it here made it so. **The
developer must independently re-check both variables in its own dispatch environment before treating
either precondition as satisfied.** If either is absent or false when the developer's process actually
runs, STOP immediately, write no code, perform no database interaction, and report the unmet launch
condition exactly as ruling 13 requires — this plan's observation is not a substitute for that check.

**Ground-truth checks performed against the live repo (not trusted from the spec alone):**
- `apps/backend/app/engine/j11_stage_d.py` exists (readiness-only, confirmed unchanged intent from its
  own docstring: "It performs NO Stage D execution") and already defines every function the spec names:
  `freeze_stage_d_attempt_identity` (line 97), the three identity-compare checks —
  `check_identity_before_first_write` = Check (A) (line 208), `check_identity_before_date` = Check (B)
  (line 222), `check_identity_after_persist` = Check (C) (line 249) — `capture_stage_d_preflight` (284),
  `load_stage_d_certified_baseline` (341), `build_avb_correction_superseded_baseline` (385),
  `compare_stage_d_preflight_to_certified` (435), `stage_d_preflight_verdict` (494).
- `apps/backend/app/engine/j11_maintenance.py` defines `INCIDENT_DATES` (line 63, the exact 11 dates:
  2026-05-12/13, 07-10/13/24/27, 08-03/05/10/11/12), `freeze_attempt_identity` (199),
  `capture_full_table_sweep` (231), `diff_full_table_sweeps` (285),
  `check_attempt_identity_consistency` (308) — all as the spec describes, none missing.
  `scanner.run_scan(session, asof, config)` and `scanner.persist_run_payload` (both in `scanner.py`)
  and `j11_avb_diagnostic.classify_avb`/`classify_local_convention_with_volume_evidence` (the AVB
  re-derivation pipeline) all confirmed present.
- The exact reusable composition precedent for a fresh live preflight + AVB re-derivation already exists
  end-to-end in `apps/backend/scripts/run_j11_iter17_stage_d_readiness.py` (imports `j11_avb_diagnostic
  as diag`, `j11_stage_d as jsd`; calls `diag.classify_local_convention_with_volume_evidence` →
  `diag.classify_avb` → `jsd.produce_stage_d_readiness_artifact`) — the new execution module's preflight
  gate should read this script first and reuse the same call sequence, never a second implementation.
- `apps/backend/scripts/run_j11_stage_c_bounded_clear.py` confirmed as the exact CLI idiom to mirror:
  zero DB interaction without `--confirm`; `--evidence-dir` required with no implicit default (its own
  docstring explains why — an omitted flag once silently overwrote committed iter-13 evidence);
  checkpoints persisted before the destructive step; completion marker written only after verification.
- Live `apps/backend/data/trendora.db`: current size `8365871104` bytes matches iteration 18's recorded
  post-arm true-end size exactly — no drift since iteration 18 closed. (mtime/table-count/boundary-state
  are the developer's own true-start capture to make, not re-derived here — the spec requires this
  re-derivation be LIVE, immediately before the write, not cited from this plan.)
- `git status --porcelain -uall`: only goal-mode session bookkeeping (session.json, assumptions.md,
  lessons.md, telemetry, trace) plus this iteration's new spec/status files are pending — no unexpected
  production-code drift, no stray uncommitted engine change from a prior session.
- Test naming precedent: `test_j11_stage_d.py` / `test_j11_stage_d_cli_scripts.py` already exist for the
  readiness-only module (untouched this iteration); the new execution module and script get their own
  parallel files (exact names below), never edits inside the existing readiness test files.

No scope creep found; IN SCOPE stays within ruling 1/2/3/6/10 exactly, and Stage E/F/G are correctly
deferred rather than bundled in.

## What to Build

1. **New Stage D execution orchestration module**, `apps/backend/app/engine/j11_stage_d_execute.py`
   (new file; `j11_stage_d.py` stays completely unchanged — it is deliberately readiness-only):
   1. **Fresh live preflight, before any write.** Compose the EXISTING functions only:
      `capture_stage_d_preflight` → `compare_stage_d_preflight_to_certified` (against the AVB-corrected
      superseded baseline — build it via `load_stage_d_certified_baseline` +
      `build_avb_correction_superseded_baseline`, mirroring iter-17's readiness script) →
      `stage_d_preflight_verdict`; plus a fresh read-only AVB re-derivation via `j11_avb_diagnostic`
      (same call sequence as `run_j11_iter17_stage_d_readiness.py`, never a second implementation); plus
      a fresh, read-only re-check that the maintenance boundary is `active=1` with persisted dates
      exactly equal to `j11_maintenance.INCIDENT_DATES` and that
      `j11_preboot_guard.evaluate_boundary_for_date_fail_closed` reports `blocked=True` for all 11 dates
      (read-only re-verification only — never re-arms, never disarms, never calls the disarm script).
      Gate: proceed only if the preflight comparison passes AND classification is exactly `AVB-A` AND
      the boundary/guard re-checks agree; otherwise STOP, zero writes of any kind, persist the exact
      blocking reason to the evidence directory, exit non-zero (TC-1, TC-2).
   2. **Freeze one fresh attempt identity.** Call `j11_stage_d.freeze_stage_d_attempt_identity` directly
      — never `capture_readiness_time_identity_observation`/the `readiness_time_only` wrapper — once
      preflight passes, immediately before the first write. Persist the returned `engine_identity` to a
      new evidence artifact and prove by independent recomputation (never a copied/pasted value) that it
      differs from the iteration-10, iteration-14, and iteration-16/17/18 readiness-time identities
      already on disk (TC-3). Recommended: call Check (A) `check_identity_before_first_write` once here,
      immediately after freezing and before the per-date loop begins — it exists specifically for this
      call site and the BACKGROUND section names it as one of the "three Check (A)/(B)/(C)... functions
      ... documented as reusable for this execution"; the spec's own per-date TESTING REQUIREMENTS only
      mandate (B) and (C), so this is a recommended defensive use of existing code, not new logic.
   3. **Per-date loop, ascending chronological order, over all 11 `INCIDENT_DATES`:** confirm no
      `ScannerRun` already exists for that date (STOP if one does) → Check (B)
      `check_identity_before_date`, require `ok: true` → `scanner.run_scan(session, asof, config)`
      called directly (never through `data_manager`'s backfill/ingest-finalize path, never through
      `warmup`/`forward_testing`) → Check (C) `check_identity_after_persist` on the newly persisted row,
      require `ok: true` before advancing. **STOP the whole attempt at the first failing check or unmet
      precondition — no further date attempted, no resume-from-next-date on any later retry** (TC-4,
      TC-5, TC-6).
   4. **Post-execution mutation accounting.** `j11_maintenance.capture_full_table_sweep` /
      `diff_full_table_sweeps` before/after, plus the whole-file mtime/size/WAL bracket captured at the
      true process start and true process end as the PRIMARY instrument (iter-12's lesson: mtime+WAL
      primary, corroborated — never replaced — by the narrower table sweep). Prove
      `changed_existing_tables` is a subset of exactly `{scanner_runs, scanner_results, sector_scores,
      theme_scores}` and that `next_session_manifests` (24 rows, the 4 incident-date rows byte-identical)
      and the 34 iteration-10-era + NULL-stamped rows are untouched, by live query, not by diff absence
      (TC-7, TC-12, TC-13, TC-16).

2. **New `--confirm`-gated CLI script**, `apps/backend/scripts/run_j11_stage_d_execute.py`, mirroring
   `run_j11_stage_c_bounded_clear.py`'s idiom exactly: zero database interaction of any kind (not even a
   read) without `--confirm`; `--evidence-dir` required, no implicit default; evidence persisted at every
   checkpoint BEFORE the destructive step; the completion/outcome marker written only after full
   post-execution verification passes (TC-10, TC-11).

3. **The confirmed live execution itself** — run the script once against
   `apps/backend/data/trendora.db`, backend/frontend OFF throughout, producing the full evidence set
   under `runs/goal-market-compass-iter-19/` and the exact DEFINITION OF DONE status lines. This is the
   one live write authorized this iteration; nothing else touches the file.

4. **Fixture-scoped unit/integration tests** for the new module and CLI script — never against the live
   database, reusing the isolated-engine pattern (`app.db.make_engine`) the sibling `test_j11_stage_d*`
   suites already use. Suggested new files (developer's call on exact names):
   `apps/backend/tests/test_j11_stage_d_execute.py` and
   `apps/backend/tests/test_j11_stage_d_execute_cli_script.py`, paralleling the existing
   `test_j11_stage_d.py` / `test_j11_stage_d_cli_scripts.py` naming. Cover every TC-1 through TC-18 in
   the spec's TESTING REQUIREMENTS (see Key Test Scenarios below).

5. **Dev handoff**, `docs/handoffs/goal-market-compass-iter-19-dev.md`, stating the outcome in the exact
   vocabulary DEFINITION OF DONE requires (see Key Test Scenarios, TC-14), plus the TC-17 J-01/J-04/J-10
   carry-forward proof (grep tracked+untracked changed files against `app/api/*`, `scoring.py`,
   `sectors.py`, `compass.py`, `data_manager.py`'s J-10 recovery code — zero matches expected, same
   method iteration 18's audit used) and the TC-18 network-call grep.

## Guardrails (binding — restated from OUT OF SCOPE / the owner ruling / maintenance isolation)

- **Maintenance isolation is ACTIVE for the whole iteration.** No application-service boot (backend or
  frontend), no browser-qa-agent dispatch, no replay lane, at any point, for any reason — including after
  a successful Stage D run. This binds developer, reviewer, and QA alike. `Frontend Present: no` must
  never be read as inviting an API-smoke-test pattern that boots anything.
- **Exactly one live write sequence is authorized**, in the order above (fresh preflight read-only →
  freeze identity → per-date write loop → mutation accounting), against
  `apps/backend/data/trendora.db`, only after fixture tests are green.
- **Whole-attempt, no-piecemeal-continuation.** Any failing check at any date stops the ENTIRE attempt.
  A future retry is a full Stage C→G restart for all eleven dates — never a resume from the next
  unfinished date. Do not build or leave behind any resume-from-checkpoint capability.
- **Do not deactivate, disarm, or clear** the `j11-incident-recovery` maintenance boundary — it stays
  `active=1` regardless of this iteration's outcome. Do not invoke
  `run_j11_maintenance_boundary_disarm.py`.
- **No write of any kind** to `daily_prices`, `data_provider_runs`, `watchlist`, `maintenance_boundaries`,
  `next_session_manifests`, or any table outside `scanner_runs`/`scanner_results`/`sector_scores`/
  `theme_scores`. No schema/DDL migration of any kind.
- **No restamping** of the 34 iteration-10-era `6261ca17…` runs or any NULL-stamped pre-stamping-era row.
- **No network/provider fetch of any kind** — AG-9's dated exceptions are exhausted; none applies here.
- **No re-running** `run_j11_avb_correction.py` (spent, verified intact) — only a fresh READ-ONLY
  re-derivation of the classification is in scope.
- **Do not touch** `app/api/*`, `scoring.py`, `sectors.py`, `compass.py`, `data_manager.py`'s write paths,
  or `scanner.resolve_run` — the two known ordinary-writer guard gaps are recorded-but-deferred to
  post-Stage-G hardening; isolation keeps them unreachable, and expanding scope to fix them now is
  explicitly forbidden by the ruling itself (ruling 5).
- **Exactly two honest terminal states, never a third**: `STAGE D EXECUTED: YES` (all 11 dates
  regenerated, one identity, proven by live query) or `STAGE D EXECUTED: NO` (stopped at the first
  failing check, full evidence preserved). Either way:
  `J-11 INCIDENT STATUS: NOT REPAIRED — ATTEMPT INCOMPLETE`, boundary stays `ACTIVE`. Never describe a
  `NO` outcome as partial progress; never invent an intermediate status.
- **Targeted pytest only** (the new test files, plus any directly-touched existing suite for regression
  confidence) — never the full backend suite, never two pytest processes concurrently (this host has
  frozen before under contention). Before running any command that writes temp files, export
  `TMPDIR`/`TMP`/`TEMP` to `/home/dennis-chan/.cache/iad/iad.goal-market--5a456287.3196427` as this run's
  environment note specifies.
- If the fresh preflight finds ANY drift from the certified baseline or a non-`AVB-A` classification, or
  if any lane finds live execution cannot proceed safely for a reason not anticipated above: STOP before
  any write, preserve evidence, report the exact blocker — do not reconcile, re-derive a new baseline, or
  force through.

## Agents Required

- developer: yes -- backend-only implementation: the new execution module (What to Build §1), the new
  CLI script (§2), running the one authorized live sequence (§3), fixture tests (§4), and the dev handoff
  (§5). One pass covers this; no design/review split needed beyond the standard pipeline.
- backend-data: yes -- every deliverable is backend/engine + scripts + fixture tests, plus the one
  live-database write sequence itself (the whole point of this iteration) under maintenance isolation.
- frontend-ux: no -- no frontend file is touched; maintenance isolation forbids any application-service,
  browser, or replay lane this iteration (see Guardrails).

## Frontend Present
no

Frontend Present: no — backend-only maintenance iteration (live database regeneration); no page, route,
or UI element changes; no application boot; no browser QA (see Guardrails above). J-11 carries a waived
walkthrough status in `docs/goal.md` and needs no UI surface of its own even once eventually repaired.

## Files to Create/Modify

New:
- `apps/backend/app/engine/j11_stage_d_execute.py` -- the execution orchestration module (What to
  Build §1).
- `apps/backend/scripts/run_j11_stage_d_execute.py` -- the confirm-gated CLI entrypoint (§2).
- `apps/backend/tests/test_j11_stage_d_execute.py` and `test_j11_stage_d_execute_cli_script.py` (exact
  names developer's call) -- fixture-scoped coverage of TC-1 through TC-18 (§4).
- `runs/goal-market-compass-iter-19/` evidence set, naming consistent with the iter-16/17/18 convention
  -- e.g. preflight/AVB re-derivation artifact, frozen-identity artifact, per-date check log, before/
  after mutation-accounting sweeps + diff, whole-file mtime/size/WAL bracket, completion/outcome marker.
  Exact filenames at the developer's discretion.
- `docs/handoffs/goal-market-compass-iter-19-dev.md` -- required dev handoff (§5).

Reused unchanged (do not reimplement, do not edit):
- `apps/backend/app/engine/j11_stage_d.py` -- every function named in What to Build §1 (readiness-only
  by design; a real execution module composes it, does not modify it).
- `apps/backend/app/engine/j11_maintenance.py` -- `INCIDENT_DATES`, `freeze_attempt_identity` (Stage D
  uses its own `freeze_stage_d_attempt_identity` wrapper, not this one directly),
  `check_attempt_identity_consistency`, `capture_full_table_sweep`, `diff_full_table_sweeps`.
- `apps/backend/app/engine/j11_preboot_guard.py` -- `evaluate_boundary_for_date_fail_closed` (iter-18)
  for the read-only boundary re-check.
- `apps/backend/app/engine/j11_avb_diagnostic.py` -- the full classification pipeline, called fresh,
  never reimplemented.
- `apps/backend/app/engine/scanner.py` -- `run_scan` / `persist_run_payload`, called directly.
- `apps/backend/scripts/run_j11_iter17_stage_d_readiness.py` -- the exact composition precedent for the
  preflight + AVB re-derivation step; read it before writing the new module's preflight gate.
- `apps/backend/scripts/run_j11_stage_c_bounded_clear.py` -- the exact CLI-idiom precedent for the new
  script.

Explicitly NOT touched: `apps/backend/app/api/*`, `scoring.py`, `sectors.py`, `compass.py`,
`data_manager.py`, `main.py`, any frontend file, `maintenance_boundaries` schema/rows, `daily_prices`.

## Key Test Scenarios

Map 1:1 to the phase spec's TC-1 through TC-18 (already fully enumerated there with exact given/when/
then — not re-derived here). Priority order for the developer:
1. TC-1, TC-2 -- the fresh live preflight gate (preflight comparison + AVB re-derivation + boundary/
   guard re-check) and its fail-closed zero-write stop. Get this right before anything else touches the
   database.
2. TC-3 -- fresh identity freeze, independently recomputed and honestly compared against every historical
   identity on disk.
3. TC-4, TC-5, TC-6, TC-9 -- the per-date loop (Check B → run_scan → Check C), whole-attempt stop-on-
   first-failure, and the out-of-scope vacuous-pass rule for dates outside `INCIDENT_DATES`. Entirely
   fixture-testable before any live run.
4. TC-8 -- the synthetic Stage-C-shaped fixture end-to-end run via `app.db.make_engine`, proving TC-4
   through TC-7's assertions without opening the real database file. Must be green before the live run.
5. TC-10, TC-11 -- CLI `--confirm` / `--evidence-dir` gating, mirroring the already-fixed
   `run_j11_stage_c_bounded_clear.py` footgun.
6. TC-7, TC-12, TC-13, TC-16 -- the live run's own proof obligations: manifest non-creation (24 rows,
   the 4 incident-date rows byte-identical), the mutation-accounting sweep subset check, the
   iteration-10-era/NULL rows byte-unchanged, and the four explicitly-out-of-scope tables at zero
   fingerprint change. Only after 1-5 are green; the one part of this iteration touching the real file.
7. TC-15, TC-18 -- maintenance-isolation refusal evidence (mirroring `iter-18/maintenance-isolation-
   refusals`) and the network-call grep across the new diff.
8. TC-17 -- the complete changed-file set (tracked and untracked together) excludes `app/api/*`,
   `scoring.py`, `sectors.py`, `compass.py`, `data_manager.py`'s J-10 recovery code (J-01/J-04/J-10
   carry forward unaffected).
9. TC-14 -- dev handoff states the exact required terminal vocabulary, written last, after every
   artifact above exists to cite.
