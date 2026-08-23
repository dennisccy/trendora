# goal-market-compass-iter-11 Execution Plan

## What to Build

This iteration is **J-11 Stage B1-completion** — it closes the two Stage-C preconditions the iter-10
evaluator found false on the LIVE database (owner rulings A1-A7, `docs/goal.md` J-11 step 11, 2026-08-23).
It performs the authorized live-schema migration and the `basis_disclosure` fail-closed fix. It does
**not** begin Stage C (destructive derived-state clear) or anything after it.

- **Live schema migration (ruling A1, the sole authorized destructive-schema operation this whole
  goal)**: new script `apps/backend/scripts/run_j11_stage_b1_manifest_schema_migration.py` performs a
  mechanical, constraint-only rebuild of `next_session_manifests` against the LIVE
  `apps/backend/data/trendora.db`: create a constraint-free sibling table with the identical column set
  (the model in `app/models.py` already declares the FK-free shape since iter-10 — reuse
  `NextSessionManifest.__table__`/SQLModel metadata to generate it under a temp name, do not hand-write
  DDL) → `INSERT INTO ... SELECT * FROM next_session_manifests` → **prove full row/column equality
  against a persisted pre-migration dump BEFORE touching the original table** → only then drop the old
  table and rename the new one into place. The original constrained table must stay physically intact
  and queryable until equality is proven in the same run (this ordering IS the rollback mechanism —
  ruling A7: on any equality failure, abort before rename/drop, leave the original untouched, persist
  the evidence, STOP for owner review). One controlled writer; never wired into `app/db.py`'s startup
  ALTER path; touches no other table.
- **Evidence artifacts** under `runs/goal-market-compass-iter-11/`: full pre-migration dump (24 rows × every
  column), full post-migration dump, a per-row-per-column diff proving equality, and a full-database
  table-row-count + mtime snapshot taken immediately before and immediately after (proves no table other
  than `next_session_manifests` was written — A3.4/TC-7). Never a binary copy of the 7.8 GB file.
- **Re-prove the six Stage-C-precondition acceptance items** (goal.md J-11 step 11, items 1-6) directly
  against the migrated LIVE database — item 4 explicitly with `PRAGMA foreign_keys=ON` issued in the
  verifying session (not merely relying on it defaulting OFF). Persist the live `sqlite_master` DDL text
  (no `FOREIGN KEY` clause) and `pragma_foreign_key_check` output (zero rows) as evidence.
- **`basis_disclosure` fail-closed fix (ruling A4)** — `apps/backend/app/engine/compass.py:1108-1109`
  currently does `if not row.generation_json: return {"status": "available", "detail": None}`, which
  fabricates "basis intact" for a manifest with no recorded basis. Add an explicit new status literal
  (distinct from `"available"`/`"unavailable"`/`"rebuilt"` — implementer names it, document the choice in
  the dev handoff and in the frontend type) for: `generation_json` NULL, empty string, or malformed
  (non-JSON, must not raise) — OR well-formed JSON that omits `source_run_created_at`. The three
  already-correct branches (rebuilt / no-replacement-run-unavailable / id-reuse-still-rebuilt) must be
  unchanged.
- **Correct two stale "needs no change" claims** that the owner's 2026-08-23 correction withdraws:
  `apps/backend/app/engine/j11_maintenance.py` module docstring (the closing paragraph) and
  `apps/backend/app/models.py:845` comment on `NextSessionManifest.source_run_id` — both currently assert
  `basis_disclosure` "needs no change"; point both at the fail-closed fix instead.
- **Backend tests**: extend the existing `basis_disclosure` cluster (`test_manifest_invariants.py` already
  has two `basis_disclosure` assertions at lines ~182/204, or `test_j11_maintenance.py` — implementer's
  choice of ONE file, do not create a second parallel test surface) with the four degenerate-input cases;
  confirm the three already-correct branches unchanged. Add a NEW fixture-DB-only test file for the
  migration script's rebuild mechanics in isolation (row/column equality including a deliberately
  orphaned `source_run_id`, FK-check zero rows under `PRAGMA foreign_keys=ON` post-rebuild, abort-before-
  rename on a simulated equality mismatch) — never against a second copy of the live file.
- **Frontend (type + extraction only, no boot)**: `apps/frontend/lib/api.ts` — widen
  `CompassBasisDisclosure.status` from a 3-member to a 4-member string-literal union (exact string must
  match the backend literal). Extract the inline ternary in `compass-manifest-strip.tsx`'s `BasisLine`
  (lines 34-37: `variant`/`label` computed from `basis.status`) into a new pure function under
  `apps/frontend/lib/` (e.g. `basis-disclosure-label.ts`), covering all four statuses; the new status's
  label/variant must read visibly distinct from both "available" (ok/never a confident claim) and
  "unavailable" (danger/different fact — no basis was ever recorded, not "the run is gone"). Add a plain
  node-script test next to it (project convention: `node lib/<name>.test.ts` using `node:assert`, no test
  framework installed — see `apps/frontend/lib/api-base.test.ts` for the exact pattern). Update
  `BasisLine` to call the extracted function — mechanical refactor, no behavior change for the three
  existing statuses.
- **Dev handoff** at `docs/handoffs/goal-market-compass-iter-11-dev.md` citing: the independently
  re-derived exact live count of `generation_json` NULL/empty rows (do not copy "10" from goal.md, and
  do not blindly copy this plan's own "8" restated below — re-run the query yourself and cite the
  result); the six acceptance items' live re-verification results; the mutation-accounting diff; git
  commit confirmation for the script + evidence artifacts + fix + tests + doc corrections.

**Do NOT build (explicit non-goals this iteration):**
- Stage C onward (destructive derived-state clear, canonical regeneration, forward-return repair, cache
  invalidation, Stage G verification) — a later iteration, gated behind this one's reviewer/QA/auditor
  pass AND live read-only re-verification (ruling A6, hard gate).
- Any change to `source_run_id` VALUES on any row, including the four orphans (3048, 3049, 3081, 3112) —
  values are preserved exactly; only the FK constraint is removed.
- Any manifest regenerated/rebound/rehashed/upgraded/deleted/newly minted by or around the migration
  (AG-18).
- Any schema/data change to any table other than `next_session_manifests`.
- Any application-service boot, browser-QA run, or replay lane (maintenance isolation, ruling A5 — active
  session-level per the dispatching coordinator's confirmation).
- Any further live fetch / re-running J-10's recovery script — that exception is exhausted; J-10 is
  owner-closed at 585/587.

## Operational constraints (binding, not optional)

- **Maintenance isolation is ACTIVE for the whole iteration** (ruling A5, confirmed by the dispatching
  coordinator): no backend/frontend service boot, no browser-QA lane, no deterministic-replay lane. The
  reviewer, QA, and auditor must validate via targeted pytest, `tsc --noEmit`, the plain node-script test,
  and read-only live-DB queries only.
- **The migration script is the ONE authorized exception to "zero writes to `trendora.db`" this whole
  session**, bounded strictly to the `next_session_manifests` table. Every other interaction with the live
  file (dumps, DDL/PRAGMA checks, mutation-accounting snapshots) must be read-only. Never copy or
  open-for-write the 7.8 GB file for any other purpose.
- **Resource contract**: targeted test files only (never the full backend suite, never two pytest
  processes concurrently — it has frozen this host before). Long-running steps use
  `setsid nohup <cmd> > <logfile> 2>&1 &`, then poll the PID/log with bounded sleep loops.
- **A7 failure semantics**: if pre/post row equality (TC-4/TC-5) or mutation accounting (TC-7) fails, roll
  back to the pre-migration state (the original table must still be intact — that's why equality is
  proven before drop/rename), persist the evidence, and STOP for owner review. Do not proceed to a partial
  migration and do not attempt anything Stage-C-shaped from that state.
- **Test-name collision risk**: the phase spec's own Test-first-contract numbering (TC-1..TC-15) reuses
  the labels TC-3/TC-4/TC-5/TC-6 that `test_j11_maintenance.py` already uses for iter-10's DIFFERENT
  scenarios (FK-on delete / rebuilt-same-as_of / degenerate orphan / id-reuse). These are two independent
  numbering schemes (spec-level vs. an existing test file's literal function names) — do not let the
  developer overwrite or rename iter-10's existing TC-3..TC-6 tests; give this iteration's new tests their
  own distinct function names.

## Agents Required
- backend-data: yes -- migration script, evidence artifacts, six-acceptance-item live re-verification,
  `basis_disclosure` fail-closed fix, doc-comment corrections, fixture-DB migration test, extended
  `basis_disclosure` degenerate-input tests, dev handoff.
- frontend-ux: yes -- `CompassBasisDisclosure.status` type widening, extracted pure label/variant
  function + node-script test, mechanical `BasisLine` refactor. No boot, no browser, no visual
  verification this iteration (Stage G's job).

## Frontend Present: yes

(Per the phase spec's own Goal Mode Metadata declaration. No new page/route/user action — a served-field
type widening and a label/variant addition on the existing manifest strip. Not visually verifiable this
iteration because maintenance isolation forbids booting any service; QA validates via `tsc --noEmit` and
the plain node-script test only, never Chrome MCP, per the phase spec's own TESTING REQUIREMENTS
("Browser: none").)

## Files to Create/Modify

Backend:
- `apps/backend/scripts/run_j11_stage_b1_manifest_schema_migration.py` -- new; the single controlled
  writer performing the rebuild (see "What to Build").
- `apps/backend/app/engine/compass.py` -- `basis_disclosure` (lines ~1100-1115): fail-closed fix for
  NULL/empty/malformed `generation_json` and missing `source_run_created_at`.
- `apps/backend/app/engine/j11_maintenance.py` -- correct the module-docstring closing paragraph
  ("needs no change from this module").
- `apps/backend/app/models.py` -- correct the `source_run_id` field comment (~line 845, "needs NO change
  here").
- `apps/backend/tests/test_manifest_invariants.py` and/or `test_j11_maintenance.py` -- extend with the
  four degenerate-input `basis_disclosure` cases (pick ONE file; existing `basis_disclosure` assertions
  already live in `test_manifest_invariants.py` around lines 182/204).
- `apps/backend/tests/test_j11_stage_b1_migration.py` (or similar new name, naming convention follows
  `test_j11_maintenance.py`) -- new fixture-DB-only test for the migration script's rebuild mechanics.
- `runs/goal-market-compass-iter-11/` -- pre-migration dump, post-migration dump, equality diff,
  mutation-accounting snapshot (all JSON evidence artifacts; commit to git per iter-9's lesson).
- `docs/handoffs/goal-market-compass-iter-11-dev.md` -- dev handoff.

Frontend:
- `apps/frontend/lib/api.ts` -- widen `CompassBasisDisclosure.status` union (line ~1066) to 4 literals.
- `apps/frontend/lib/basis-disclosure-label.ts` -- new pure function (name flexible), extracted from
  `compass-manifest-strip.tsx` lines 34-37.
- `apps/frontend/lib/basis-disclosure-label.test.ts` -- new plain node-script test (pattern:
  `apps/frontend/lib/api-base.test.ts`).
- `apps/frontend/components/compass-manifest-strip.tsx` -- `BasisLine` (lines 34-44) calls the extracted
  function instead of its inline ternary.

Reference only, unchanged: `apps/backend/app/api/compass.py:43` (the one call site of
`basis_disclosure`), `apps/backend/app/db.py` (`get_engine()` — reuse, never a raw file copy or
`create_db_and_tables()`), `apps/backend/scripts/run_j11_pre_reset_inventory.py` (prior iteration's
read-only live-DB script — mirror its zero-write-proof pattern for reads, but this script is a writer).

## UI Evolution

- New user-facing capability: none.
- New information displayed: `basis.status` on the existing manifest strip (`/`) can now read a fourth,
  honest value instead of always collapsing an unrecorded basis to "available" -- not visible this
  iteration (no boot); confirmed only by type-check + unit test.
- New user actions: none.
- UI surface changes: none structural -- a label/variant addition on `compass-manifest-strip.tsx`; no new
  component, no new route.
- Navigation changes: none.

## Visual Requirements

- Component patterns: reuse the existing `Badge` component and its `variant` prop (`ok`/`warn`/`danger`
  today) -- the new status needs its own visibly-distinct variant/label pairing, not a reuse of
  `"warn"`/`"danger"` that would blur it into "rebuilt" or "unavailable"'s meaning.
- Layout: unchanged -- `BasisLine` renders inline inside the existing manifest strip card.
- Key visual effects: none new -- subtle-only per the design system; no new colors outside the existing
  `Badge` variant tokens.
- States to handle: the new unverifiable/unknown state must never render as, or be visually confusable
  with, "available" (AG-1: never a confident claim) or collapse into "unavailable"'s wording (a different
  fact -- no basis was ever recorded, vs. the source run is gone).

## Key Test Scenarios

- TC-1/TC-2 (fixture): rebuild logic on a fixture DB with the live table's exact current DDL (FK clause
  included) and an orphaned `source_run_id` -- resulting `sqlite_master` SQL has no `FOREIGN KEY` clause,
  row count unchanged, every column byte-identical including the orphan; `pragma_foreign_key_check` under
  explicit `PRAGMA foreign_keys=ON` returns zero rows despite the stored orphan.
- TC-3/TC-4/TC-5 (live DB): pre-migration dump of all 24 rows persisted read-only; migration executes as
  the single controlled writer; post-migration `sqlite_master` has no `FOREIGN KEY` clause, row count
  still 24; post-migration dump diffed row-by-row/column-by-column against the pre-migration artifact is
  identical, including the four orphaned `source_run_id` values (3048, 3049, 3081, 3112).
- TC-6 (live DB): `PRAGMA foreign_keys=ON` explicitly issued post-migration -- `pragma_foreign_key_check`
  still zero rows (proves by schema/contract, not by enforcement defaulting OFF).
- TC-7 (live DB): full-database table-row-count + mtime snapshot before vs. after -- every table except
  `next_session_manifests` byte-identical; `next_session_manifests` count 24 -> 24.
- TC-8 (fixture): deliberately-injected one-byte equality mismatch between pre-copy source and the new
  table -- migration aborts BEFORE rename/drop, original table remains intact with original values, an
  evidence note records the aborted attempt.
- TC-9/TC-10/TC-11/TC-12: `basis_disclosure` given NULL / empty-string / malformed-non-JSON /
  well-formed-but-missing-`source_run_created_at` `generation_json` -- each returns the new unverifiable
  status, never `"available"`, never raises.
- TC-13: the three existing correct branches (rebuilt / no-replacement-run-unavailable /
  id-reuse-still-rebuilt) unchanged after the fix.
- TC-14: node-script test on the extracted label/variant function -- the new status's label/variant is
  visibly distinct from both `"available"` (ok) and `"unavailable"` (danger).
- TC-15 (live DB): every independently-recounted row with missing/empty/malformed `generation_json`
  (re-derive the exact count live -- do not trust "8" or "10" without re-checking) reports the new status
  through the fixed function, never `"available"`.
- Regression: `test_j11_maintenance.py`, `test_manifest_invariants.py`, `test_compass.py`,
  `test_api_compass.py` re-run unmodified, still green; `tsc --noEmit` clean.
