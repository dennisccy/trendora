# goal-market-compass-iter-10 Execution Plan

## What to Build

This iteration is J-11 Stages B / B1 / B2 only — read-only inventory capture, a schema-contract
clarification, and a frozen attempt-identity precondition. It is explicitly **not** the destructive
clear/regenerate (Stages C–G), which stay out of scope for a later iteration. Loop-mechanics in
`docs/goal.md` still forbids any dev/reviewer/QA/browser-QA/replay/evaluator/coherence lane from
running against the *derived* state as if it were clean — this iteration's own work sidesteps that by
touching only fixture DBs and running one read-only script against the live DB.

- Drop the live-enforced FK declaration on `NextSessionManifest.source_run_id` (model-declaration
  only — no live-DB migration, no `ALTER TABLE`) and document, in a code comment, that
  `source_run_id` is immutable historical provenance, never a durable live-FK identity; reconciliation
  after a delete/rebuild is done by `as_of` + `source_run_created_at` + engine identity via the
  existing (unchanged) `basis_disclosure`.
- Add `app/engine/j11_maintenance.py` with three pure/read-only pieces: a pre-reset inventory capture
  over the 11 incident dates, a frozen-attempt-identity capture (engine identity + config subset
  hash), and a pure per-run identity-consistency check (no aggregate-only form).
- Add a read-only CLI script that runs the above against the live `apps/backend/data/trendora.db` via
  existing `app.db` session helpers (never a raw file copy) and writes two JSON artifacts under
  `runs/goal-market-compass-iter-10/`, self-proving via a before/after row-count + fingerprint check
  that it performed zero writes.
- Add fixture-DB-only tests (`test_manifest_invariants.py`'s pattern: fresh `sqlite://` engine,
  `SQLModel.metadata.create_all`, hand-built rows) proving: FK deletion doesn't raise under an
  explicitly-issued `PRAGMA foreign_keys=ON`; the rebuilt-same-`as_of` case; the **degenerate orphan
  case** (no replacement run at all — must read "unavailable," never fabricate "rebuilt"/"available");
  the **id-reuse trap** (same numeric `source_run_id`, later `created_at` — must still read
  `rebuilt`); and the identity-consistency helper on both a matching and a **mismatched** run
  (per-run assertion, not an aggregate "all matched," per the iter-9 AVB lesson).
- Dev handoff citing the captured inventory counts, the manifest/hash list, and mtime + fingerprint
  proof of zero writes to `trendora.db`.

**Operational constraints (binding, not optional):**
- **No booting the backend or frontend application services this iteration**, and **no browser-QA or
  deterministic-replay lane** — `docs/goal.md` Loop-mechanics forbids these unconditionally until J-11
  Stage G passes (this exact recurrence already fired twice, iters 6 and 8, per the session's
  `lessons.md`). The reviewer and QA agents must validate this iteration via targeted pytest and the
  one read-only inventory script only — never via `start-backend.sh` / `start-frontend.sh`.
- **Zero writes to `apps/backend/data/trendora.db`.** Every check (TC-1/TC-2/TC-8) must be provable
  read-only: same mtime, same full row counts/date ranges, before and after.
- `Depth: full` is dispatched for this iteration (structural/cross-cutting trigger — the schema
  contract spans `app/models.py`, `app/db.py`, and `app/engine/compass.py`); do not let it silently
  demote to lean (session lesson: this has happened 3 times already, iters 2/6/8).

## Agents Required
- backend-data: yes -- implement the model-declaration change, `app/engine/j11_maintenance.py`, the
  read-only inventory script, and the fixture-DB tests described above.
- frontend-ux: no -- zero UI surface this iteration; J-11's walkthrough is waived by `docs/goal.md`.

## Frontend Present: no

## Files to Create/Modify
- `apps/backend/app/models.py` -- on `NextSessionManifest`, drop `foreign_key="scanner_runs.id"` from
  `source_run_id`; add the verbatim "intended end state" comment from goal.md J-11 step 11.
- `apps/backend/app/engine/j11_maintenance.py` -- new: `capture_pre_reset_inventory(session)`,
  `freeze_attempt_identity(session, cfg)`, `check_attempt_identity_consistency(frozen_identity,
  run_identity) -> bool`.
- `apps/backend/scripts/run_j11_pre_reset_inventory.py` -- new read-only CLI; writes
  `runs/goal-market-compass-iter-10/j11-pre-reset-inventory.json` and
  `runs/goal-market-compass-iter-10/j11-frozen-identity.json`.
- `apps/backend/tests/test_j11_maintenance.py` -- new fixture-DB-only test file (cases a–e per the
  spec: FK-off delete, rebuilt-same-as_of, degenerate orphan, id-reuse trap, identity match/mismatch).
- `docs/handoffs/goal-market-compass-iter-10-dev.md` -- dev handoff.
- Reference only, unchanged: `apps/backend/app/engine/compass.py` (`basis_disclosure`,
  `get_or_create_manifest`), `apps/backend/app/engine/engine_identity.py`
  (`compute_engine_identity`), `apps/backend/tests/test_manifest_invariants.py` (fixture pattern to
  mirror), `apps/backend/tests/test_j10_recovery.py` (re-run unmodified, must still pass).

## Key Test Scenarios
- TC-1/TC-2: the inventory script writes both artifacts with the required fields, and a second
  independent read-only `daily_prices` count/date-range query matches the artifact exactly (proves
  zero writes from the capture step itself).
- TC-3: fixture DB, `PRAGMA foreign_keys=ON` explicit, insert run + manifest referencing it, delete
  the run -- no FK violation, manifest row unchanged.
- TC-4: after TC-3, insert a NEW run for the same `as_of` -- `basis_disclosure` reports rebuilt via
  `as_of` + `source_run_created_at`; `source_run_id`/both hashes/`version`/`available_at_utc`/
  `prospective_eligible` all unchanged.
- TC-5 (degenerate/iter-7 lesson): after TC-3, NO replacement run at all -- `basis_disclosure` reports
  "underlying run unavailable" without raising and without fabricating available/rebuilt.
- TC-6 (id-reuse trap): manifest minted from run id N at T1; delete; recreate id N at T2 > T1 --
  `source_run_id` still N, bytes/hashes unchanged, `basis_disclosure` reports `rebuilt` (not
  `original`) because `source_run_created_at` differs.
- TC-7 (iter-9 lesson): `check_attempt_identity_consistency` -- a matching-identity run returns
  true/consistent AND a **mismatched**-identity run returns false/inconsistent, asserted as two
  distinct cases, not one aggregate.
- TC-8: `trendora.db` mtime + full row-count/date-range snapshot identical before and after this
  iteration's entire body of work.
- TC-9: `runs/goal-market-compass-iter-10/depth-dispatched` reads `full`.
- TC-10: no QA evidence directory or replay-results file dated to this iteration exists; journey-history
  status for J-01/J-02/J-03/J-04/J-10 is byte-identical to its pre-iteration value.
- Regression: `test_manifest_invariants.py` and `test_j10_recovery.py` re-run unmodified, still green.
