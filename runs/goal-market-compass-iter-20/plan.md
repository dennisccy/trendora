# goal-market-compass-iter-20 Execution Plan

## Alignment check

Verified directly against the live `docs/goal.md` (not trusted from the phase spec's paraphrase alone) —
read the full "OWNER RULING — J-11 Stage D through Stage G recovery execution AUTHORIZED" block
(lines 1750-1998, commit `5fe72f5c`, unchanged since iter-19's own Alignment check verified it). Ruling
item 7 authorizes Stage E "as already defined" the moment Stage D succeeds, with no further owner
sign-off; item 2 requires any engine/config identity drift before Stage G to make the whole attempt
incomplete; item 4 keeps maintenance isolation mandatory through Stage G; item 5 defers the two ordinary-
writer guard gaps; item 13 requires `CHAIN_MAINTENANCE_ISOLATION=true` / `CHAIN_REQUIRE_FULL_DEPTH=true`
as launch conditions, not ambient state; item 14 is the exact two-terminal-state vocabulary. The phase
spec's IN SCOPE/OUT OF SCOPE/DEFINITION OF DONE map onto these cleanly. **No drift found.**

**Ground-truth checks performed against the live repo (not trusted from the spec alone):**
- Independently confirmed the spec's central safety claim by reading `forward_testing._backfill()`
  myself (`apps/backend/app/engine/forward_testing.py:531-583`): it calls
  `walk_forward_asof_dates(session, cfg)` (a `quarterly`, 30-year cadence grid —
  `config.yaml:786-788`, `history_years: 30`) and, for every date the maintenance-boundary guard does
  NOT block, calls `run_scan(session, asof, cfg)` — a live `ScannerRun`-minting write. Only
  `backfill_forward_returns()` (line 593) reaches `_backfill()`; `backfill_run_forward_returns()`
  (line 2043, confirmed: create-once, INSERT-only, idempotent, "never UPDATEs a `scanner_runs` /
  `scanner_results` / `*_scores` row" per its own docstring) does not. The spec's exclusive-use
  requirement is therefore load-bearing, not defensive boilerplate — calling the wrong function is a
  live path to an out-of-boundary `ScannerRun`, which ruling item 7 explicitly forbids ("may not...
  broaden into unrelated historical cleanup").
- Confirmed `ForwardReturn` (`apps/backend/app/models.py:334`) carries no `engine_identity` column —
  supports the spec's instruction not to re-freeze or cite a new identity, only compare against Stage
  D's.
- Confirmed `apps/backend/app/engine/j11_stage_d_execute.py:117` — `recheck_maintenance_boundary_and_guard(session, incident_dates=INCIDENT_DATES, *, boundary_name=...)` —
  is generic (no Stage-D-specific coupling): it re-verifies boundary `active=1`, exact persisted
  date-set, and `j11_preboot_guard.evaluate_boundary_for_date_fail_closed` blocking all 11, read-only.
  **Reuse this function directly for Stage E's own boundary/guard re-check** rather than reimplementing
  it — it is exactly the check the spec's preflight bullet 1 describes.
- Confirmed `prices.prefilled_bar_cache(session, expected_symbols=None)` (`prices.py:563-578`) and
  `prices.bar_cache(session)` (line 528) signatures directly.
- Confirmed `engine_identity.compute_engine_identity(config)` (`engine_identity.py:44-66`) signature and
  read Stage D's frozen artifact directly:
  `runs/goal-market-compass-iter-19/j11-stage-d-execute-frozen-identity.json` →
  `engine_identity: "53d2ffd10cdbf89ef16681111bd900766e00e5809bc4ebc7d4b5f2bf1b7f6c55"`. This is the
  value Stage E's preflight must recompute-and-compare-equal, never copy.
- Confirmed via the iter-19 audit (PASS_WITH_GAPS) and dev handoff that Stage D's live end state is:
  `scanner_runs` ids **3148-3158** ↔ asof_dates 2026-05-12, 05-13, 07-10, 07-13, 07-24, 07-27, 08-03,
  08-05, 08-10, 08-11, 08-12, all stamped `53d2ffd1…`, `created_at` window 10:52:55.552946 →
  10:53:02.010362 UTC, each currently with **zero** `ForwardReturn` rows (audit-verified live query);
  `next_session_manifests` 24 rows unchanged, the 4 incident-date rows byte-identical. This is a
  reference point for the developer's own fresh, live re-derivation — never a substitute for it.
- Audit findings B3/B4 (iter-19, both GAP-class, not blocking) carry forward as design input for Stage E
  specifically: B3 recommends `prefilled_bar_cache(session, expected_symbols=pool_symbols)` over the
  lazy `bar_cache` Stage D used, since `forward_returns` is 6.8M rows and the lazy path's `list[Bar]`
  per-symbol shape is "~3.3x more bytes/row" than `prefilled_bar_cache`'s columnar `_SymbolColumns`
  shape (itself measured ~1.1 GB resident for the full pool, per `prices.py`'s own iter-43 note). B4
  recommends a hard assertion that any per-date/per-run loop only ever receives its intended row set.
- No `j11_stage_e*` file exists yet anywhere in `apps/backend/` — confirmed genuinely new work, no name
  collision.
- `git status --porcelain -uall`: only goal-mode session bookkeeping (session.json, assumptions.md,
  lessons.md, telemetry, trace, lock/dispatch files) plus this iteration's own new spec/status files are
  pending — no stray uncommitted engine change from a prior session.

**Environment check (an independently-observed operator fact, not a self-declaration):** per ruling item
13 and anti-pattern 25, `CHAIN_MAINTENANCE_ISOLATION=true` / `CHAIN_REQUIRE_FULL_DEPTH=true` must be
present in the *developer's own dispatch process environment*, re-checked independently — this plan's
observation is not a substitute for that check. If either is absent when the developer's process
actually runs, STOP immediately, write no code, touch no database, and report the unmet launch condition.

**Resource note — elevated caution vs. iter-19 (relayed by the coordinator, not independently verified
here):** a second, independent goal-mode engine is reportedly running concurrently on this same ~26.7 GB
host with the owner's knowledge; host-guard reportedly shows `engines=1/3` with contexts confined, but
memory headroom is described as materially tighter than during iter-19's Stage D run. This does not
relax or add any rule — the spec already requires a live peak-memory measurement against
`memory_cap_mb: 8192` / `HOST_GUARD_MEMORY_HIGH` (`config.yaml:1377`, AG-10) regardless of which
bar-loading path is chosen, and forbids any parallel writer — but it raises the stakes of the B3
recommendation above. Treat `prefilled_bar_cache` as the leading candidate (fewer queries, the more
memory-efficient shape per B3) but do not commit to it blindly: check current host memory headroom
read-only immediately before the live run, and let the live measurement — not this note, not iter-19's
figure — decide whether it fits the ceiling with this iteration's concurrent host load.

No scope creep found; IN SCOPE stays within ruling item 7 exactly, and Stages F/G are correctly deferred.

## What to Build

1. **New Stage E execution module**, `apps/backend/app/engine/j11_stage_e_execute.py` (new file):
   1. **Fresh, read-only preflight, before any write.** Compose existing functions only:
      `j11_stage_d_execute.recheck_maintenance_boundary_and_guard` (reuse directly, see Alignment check)
      for the boundary/guard re-verification; a fresh live query confirming all 11 of Stage D's
      `ScannerRun` rows are present, unrestamped (same id, `asof_date`, `created_at`) and each currently
      carries zero `ForwardReturn` rows; a fresh `engine_identity.compute_engine_identity(config)` call
      asserted **equal** to the value read from
      `runs/goal-market-compass-iter-19/j11-stage-d-execute-frozen-identity.json`; a fresh
      `next_session_manifests` count/byte-identity check (24 rows, the 4 incident-date rows unchanged).
      **Do not** freeze a new attempt identity and **do not** call `freeze_stage_d_attempt_identity` —
      only cite Stage D's frozen value for provenance (`ForwardReturn` has no `engine_identity` column).
      Gate: proceed only if every check agrees; otherwise STOP, zero writes, persist the exact blocking
      reason to the evidence directory, exit non-zero (TC-1, TC-2).
   2. **Per-run repair loop.** Iterate every row currently in `scanner_runs`, ascending `asof_date`, and
      call `forward_testing.backfill_run_forward_returns(session, run, config)` once per row — the
      create-once INSERT-only path. **Never call or import `forward_testing.backfill_forward_returns`**
      anywhere in this module or its CLI script (see Alignment check's independent `_backfill()`
      verification) — prove this by a static/import-level test, not code review alone (TC-3). Consider a
      B4-style hard assertion that the row set iterated is exactly the live `scanner_runs` table, never a
      caller-narrowed subset.
   3. **One shared bar-loading context, one `Session`, for the whole loop** — either
      `prices.prefilled_bar_cache(session, expected_symbols=<resolved pool>)` or the default lazy
      `bar_cache(session)` path (developer's call, informed by the Resource note above); measure and
      record live peak process memory (`VmPeak` from `/proc/<pid>/status`, the same method J-09 uses)
      either way, against `memory_cap_mb`/`HOST_GUARD_MEMORY_HIGH` (TC-11). No parallel writer.
   4. **Three-population reporting, by name, proven by live read-only query:** (a) forward returns newly
      inserted for the 11 Stage-D-rebuilt runs (ids 3148-3158); (b) forward returns newly filled on
      retained (non-incident) runs whose `measured_date` lands on one of the 11 incident dates — the
      defensive-sweep hole population Stage B originally sized; (c) genuinely not-yet-mature
      (run, symbol, horizon) combinations, which must remain absent (zero rows) — never fabricated
      (TC-5, TC-6, TC-8).
   5. **Post-execution mutation accounting.** `j11_maintenance.capture_full_table_sweep` /
      `diff_full_table_sweeps` before/after, plus the whole-file mtime/size/WAL bracket at true process
      start/end as the PRIMARY instrument (iter-12/13 precedent). Expect `changed_existing_tables` to be
      a subset of `{forward_returns}` only (TC-9). Cross-check `next_session_manifests` still 24 rows,
      the 4 incident-date rows byte/value-identical (TC-10), and the 8 named out-of-scope tables
      (`daily_prices`, `scanner_runs`, `scanner_results`, `sector_scores`, `theme_scores`,
      `data_provider_runs`, `watchlist`, `maintenance_boundaries`) at zero fingerprint change (TC-4,
      TC-18). Confirm `COUNT(*) FROM forward_returns` after minus before equals the loop's own
      self-reported inserted-row total exactly (TC-12). Sample pre-existing `ForwardReturn` rows outside
      the two hole populations and assert byte-identity (TC-7).

2. **New `--confirm`-gated CLI script**, `apps/backend/scripts/run_j11_stage_e_execute.py`, mirroring
   `run_j11_stage_d_execute.py`'s idiom exactly: zero database interaction of any kind (not even a read)
   without `--confirm` (TC-13); `--evidence-dir` required, no implicit default, refuses before any
   config/engine construction (TC-14); a collision guard against re-running into a populated directory;
   evidence persisted at every checkpoint before the write; the completion/outcome marker written only
   after full post-execution verification. A `--stage-d-identity-path` style argument (defaulting to
   `runs/goal-market-compass-iter-19/j11-stage-d-execute-frozen-identity.json`) is a reasonable way to
   supply the comparison value — developer's call on exact flag naming.

3. **The confirmed live execution itself** — run the script once against
   `apps/backend/data/trendora.db`, backend/frontend OFF throughout, producing the full evidence set
   under `runs/goal-market-compass-iter-20/` and the exact DEFINITION OF DONE status lines. This is
   additive-only (INSERT-only, no destructive delete anywhere in Stage E), which is a materially lower
   irreversibility profile than Stage D's clear-then-rebuild — but it still touches up to ~6.8M+ rows
   live, so the fixture tests must be green first and the resource note above still applies. The
   pre-Stage-D owner disaster-recovery snapshot
   (`/home/dennis-chan/trendora-db-snapshots/trendora-pre-j11-stage-d-20260826T100159Z.db`) remains the
   standing backstop; nothing in this iteration touches, restores from, or depends on it.

4. **Fixture-scoped unit/integration tests** — never against the live database, reusing the isolated
   `app.db.make_engine` pattern the sibling `test_j11_*` suites already use. Suggested new files
   (developer's call on exact names): `apps/backend/tests/test_j11_stage_e_execute.py` and
   `test_j11_stage_e_execute_cli_script.py`, paralleling the iter-19 naming. Cover TC-1 through TC-20 in
   full, including the TC-15 synthetic end-to-end fixture (Stage-D-shaped: 11 incident dates each with a
   zero-`ForwardReturn` `ScannerRun`, a retained run with an incident-dated hole, a genuinely-immature
   combination, an active `MaintenanceBoundary`) run through the real module via `app.db.make_engine`.

5. **Dev handoff**, `docs/handoffs/goal-market-compass-iter-20-dev.md`, stating the outcome in the exact
   vocabulary DEFINITION OF DONE / TC-16 require, which path was chosen for bar-loading and why (TC-11),
   the TC-19 J-01/J-04/J-10 carry-forward proof (grep the complete changed-file set — tracked and
   untracked together — against `app/api/*`, `scoring.py`, `sectors.py`, `compass.py`, `data_manager.py`'s
   J-10 recovery code; zero matches expected, same method iter-19 used), and the TC-20 network-call grep.

### New user-facing capability / information / actions / UI surface changes / Product surface delta
None — backend-only maintenance, per the spec. Matches `Frontend Present: no` below.

## Guardrails (binding — restated from OUT OF SCOPE / the owner ruling / maintenance isolation)

- **Maintenance isolation is ACTIVE for the whole iteration.** No application-service boot (backend or
  frontend), no browser-qa-agent dispatch, no replay lane, no Data Manager action, no ordinary API
  request, at any point. Binds developer, reviewer, and QA alike.
- **Exactly one authorized live write target: `forward_returns`.** No write of any kind to
  `daily_prices`, `scanner_runs`, `scanner_results`, `sector_scores`, `theme_scores`,
  `next_session_manifests`, `data_provider_runs`, `watchlist`, or `maintenance_boundaries`. No
  schema/DDL migration.
- **Stage E's own failure semantics are idempotent-retry, NOT a Stage C→G restart** — this differs from
  Stage D. Because the per-run loop is create-once/INSERT-only with no destructive delete, a stopped or
  failed attempt may simply be re-run; it naturally resumes correctly with zero duplicate rows (never
  "resume from the next unfinished run" as a special mechanism — plain idempotency already provides it).
  Do not describe a retry as requiring Stage C-onward restart; that rule is Stage D's, not Stage E's.
- **Never call or import `forward_testing.backfill_forward_returns`** (the whole-database entry point) —
  see Alignment check. Only `forward_testing.backfill_run_forward_returns`, once per row.
- **Do not modify** `forward_testing.py`, `scanner.py`, `prices.py`, `j11_maintenance.py`,
  `j11_stage_d.py`, or `j11_stage_d_execute.py` — Stage E composes their existing functions as-is.
- **Do not restamp** any `ScannerRun`, including the 11 Stage-D-rebuilt rows, the 34 iteration-10-era
  rows, or any NULL-stamped row. Do not freeze a new attempt identity.
- **Do not deactivate, disarm, or clear** the `j11-incident-recovery` maintenance boundary — it stays
  `active=1` regardless of this iteration's outcome.
- **No network/provider fetch of any kind** — AG-9's dated exceptions are exhausted; none applies here.
- **Do not touch** `app/api/*`, `scoring.py`, `sectors.py`, `compass.py`, `data_manager.py`'s write
  paths, or `scanner.resolve_run` — the two known ordinary-writer guard gaps stay recorded-but-deferred
  to post-Stage-G hardening (ruling item 5); expanding scope to fix them now is explicitly forbidden.
- **Do not modify anything under the goal-mode framework** (`.claude/`, `scripts/automation/`, the stall
  backstop / `--stall-window` override) — out of scope for this product-code iteration regardless.
- **Exactly two honest terminal states, never a third:** `J-11 STAGE E COMPLETE: YES` (all checks passed,
  three populations reported by name and proven live) or `NO` (stopped at the first failing check or
  mid-loop error, full evidence preserved). Either way, carried unchanged:
  `J-11 STAGE D EXECUTED: YES`, `J-11 STAGE F COMPLETE: NO`, `J-11 STAGE G VERIFIED: NO`,
  `J-11 INCIDENT STATUS: NOT REPAIRED — ATTEMPT INCOMPLETE`, `J-11 MAINTENANCE BOUNDARY: ACTIVE`,
  `J-11 LIVE PRE-BOOT GUARD: ARMED`. Never describe a `NO` outcome as partial progress.
- **Operational (coordinator note):** read-only `sqlite3 "file:<path>?mode=ro" "..."` is sanctioned for
  verification; never copy, move, or open-for-write `apps/backend/data/trendora.db`. Never run the full
  backend pytest suite; never two pytest processes concurrently. Any backgrounded process uses `setsid`
  and is polled within the same turn. Before any command that writes temp files, export
  `TMPDIR`/`TMP`/`TEMP` to `/home/dennis-chan/.cache/iad/iad.goal-market-c-7d3d149b.567578` per this run's
  environment note.
- If the fresh preflight finds ANY drift from Stage D's certified end state — most importantly an
  `engine_identity` mismatch — STOP before any write, preserve evidence, report the exact blocker. Do
  not proceed piecemeal under a different identity.

## Agents Required

- developer: yes -- backend-only implementation: the new execution module (What to Build §1), the new
  CLI script (§2), running the one authorized live sequence (§3), fixture tests (§4), and the dev handoff
  (§5). One pass covers this; no design/review split needed beyond the standard pipeline.
- backend-data: yes -- every deliverable is backend/engine + scripts + fixture tests, plus the one live
  additive-only database write sequence itself (the whole point of this iteration) under maintenance
  isolation.
- frontend-ux: no -- no frontend file is touched; maintenance isolation forbids any application-service,
  browser, or replay lane this iteration (see Guardrails).

## Frontend Present
no

Frontend Present: no — backend-only maintenance iteration (live, additive-only `forward_returns` repair);
no page, route, or UI element changes; no application boot; no browser QA (see Guardrails above). J-11
carries a waived walkthrough status in `docs/goal.md`.

## Files to Create/Modify

New:
- `apps/backend/app/engine/j11_stage_e_execute.py` -- the execution orchestration module (What to
  Build §1).
- `apps/backend/scripts/run_j11_stage_e_execute.py` -- the confirm-gated CLI entrypoint (§2).
- `apps/backend/tests/test_j11_stage_e_execute.py` and `test_j11_stage_e_execute_cli_script.py` (exact
  names developer's call) -- fixture-scoped coverage of TC-1 through TC-20 (§4).
- `runs/goal-market-compass-iter-20/` evidence set, naming consistent with the `j11-stage-d-execute-*`
  convention (e.g. `j11-stage-e-execute-preflight.json`, `-boundary-recheck.json`,
  `-identity-comparison.json`, `-population-report.json`, `-mutation-accounting.json`,
  `-db-file-true-start.json` / `-true-end.json`, `-outcome.json`). Exact filenames at the developer's
  discretion.
- `docs/handoffs/goal-market-compass-iter-20-dev.md` -- required dev handoff (§5).

Reused unchanged (do not reimplement, do not edit):
- `apps/backend/app/engine/forward_testing.py` -- `backfill_run_forward_returns` (the sole write path).
- `apps/backend/app/engine/j11_maintenance.py` -- `INCIDENT_DATES`, `capture_full_table_sweep`,
  `diff_full_table_sweeps`.
- `apps/backend/app/engine/j11_stage_d_execute.py` -- `recheck_maintenance_boundary_and_guard`, reused
  directly for Stage E's own boundary/guard re-check (see Alignment check).
- `apps/backend/app/engine/prices.py` -- `prefilled_bar_cache` and/or `bar_cache`.
- `apps/backend/app/engine/engine_identity.py` -- `compute_engine_identity`, called fresh and compared,
  never re-frozen.
- `runs/goal-market-compass-iter-19/j11-stage-d-execute-frozen-identity.json` -- the comparison value
  (read, never copied into a hardcoded string).

Explicitly NOT touched: `apps/backend/app/api/*`, `scoring.py`, `sectors.py`, `compass.py`,
`data_manager.py`, `main.py`, `scanner.py`, `j11_stage_d.py`, any frontend file, `daily_prices`,
`maintenance_boundaries` schema/rows, `next_session_manifests` schema/rows.

## Key Test Scenarios

Map 1:1 to the phase spec's TC-1 through TC-20 (fully enumerated there with exact given/when/then — not
re-derived here). Priority order for the developer:
1. TC-1, TC-2 -- the fresh preflight gate (boundary/guard re-check, all-11-present-unrestamped, all-11-
   zero-`ForwardReturn`, engine-identity equality, manifest unchanged) and its fail-closed zero-write
   stop. Get this right before anything else touches the database.
2. TC-3 -- the per-run loop's exclusive use of `backfill_run_forward_returns`; static/import-level proof
   that `backfill_forward_returns` is never imported or called.
3. TC-4, TC-7 -- `scanner_runs`/`scanner_results`/`sector_scores`/`theme_scores` byte-unchanged; sampled
   pre-existing `ForwardReturn` rows outside the two hole populations byte-identical.
4. TC-5, TC-6, TC-8 -- the three-population classification (rebuilt-run fill, retained-run hole fill,
   immature combinations stay absent). Entirely fixture-testable before any live run.
5. TC-15 -- the synthetic Stage-D-shaped fixture end-to-end run via `app.db.make_engine`, reproducing
   TC-3 through TC-8 without opening the real database file. Must be green before the live run.
6. TC-13, TC-14 -- CLI `--confirm` / `--evidence-dir` gating, mirroring the fixed
   `run_j11_stage_d_execute.py` footgun.
7. TC-9, TC-10, TC-18 -- mutation-accounting sweep + mtime/WAL bracket (subset of `{forward_returns}`
   only), manifest byte-identity, and the 8 named out-of-scope tables at zero fingerprint change.
8. TC-11 -- live peak process memory measured and recorded against `memory_cap_mb`/
   `HOST_GUARD_MEMORY_HIGH`, whichever bar-loading path is chosen (see Resource note).
9. TC-12 -- the loop's self-reported inserted-row total reconciles exactly with the live `COUNT(*)`
   delta. Only after 1-8 are green; the one part of this iteration touching the real file.
10. TC-17 -- maintenance-isolation refusal evidence for any other lane attempting to run.
11. TC-19 -- the complete changed-file set (tracked and untracked) excludes `app/api/*`, `scoring.py`,
    `sectors.py`, `compass.py`, `data_manager.py`'s J-10 recovery code (J-01/J-04/J-10 carry forward
    unaffected, per the spec's non-reverification method).
12. TC-20 -- network-call grep across the new diff; zero outbound requests recorded in evidence.
13. TC-16 -- dev handoff and evidence state the exact required terminal vocabulary, written last, after
    every artifact above exists to cite.
