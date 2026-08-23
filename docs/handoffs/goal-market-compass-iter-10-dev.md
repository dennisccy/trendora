# goal-market-compass-iter-10 Dev Handoff

**Phase:** goal-market-compass-iter-10
**Date:** 2026-08-23
**Agent:** developer
**Status:** complete

## What Was Built

This iteration is J-11 Stages B / B1 / B2 ONLY (read-only inventory capture, a schema-contract
clarification, and a frozen attempt-identity precondition). Stages C-G (the destructive derived-state
clear/regenerate) are explicitly OUT OF SCOPE and were not touched. No backend/frontend service was
started; no browser-QA or replay lane ran; `apps/backend/data/trendora.db` was opened for READ-ONLY
queries exactly once (via the new inventory script) and received zero writes (proof below).

- **Stage B1 — manifest↔ScannerRun schema contract**: dropped the live-enforced
  `foreign_key="scanner_runs.id"` declaration from `NextSessionManifest.source_run_id` in
  `apps/backend/app/models.py` (model-declaration only — no live-DB migration; the already-created live
  table's own DDL is untouched, per the additive-ALTER-only schema rule). Added the verbatim "Intended
  end state" contract from `docs/goal.md` J-11 step 11 as a code comment. `app.engine.compass.
  basis_disclosure` already resolves current-run identity by `as_of` + `source_run_created_at` (never by
  dereferencing `source_run_id`) and needed no change — confirmed by reading it, not modified.
- **New module `apps/backend/app/engine/j11_maintenance.py`**:
  - `capture_pre_reset_inventory(session)` (Stage B) — read-only inventory over the exact 11 incident
    dates: per-date `ScannerRun` presence/id/created_at/engine_identity, per-date
    `scanner_results`/`sector_scores`/`theme_scores`/`forward_returns` counts (both the "originated from
    this date's own run" population AND the "measured INTO this date" population — the defensive-sweep
    hole population on possibly-retained runs a later stage must repair), the per-date manifest list
    (version/mode/frozen/source_run_id/content_hash/manifest_hash/prospective_eligible/available_at_utc),
    `daily_prices` row count + date range + a cheap SQL-side aggregate fingerprint (never a full ORM
    hydration of the ~3.3M-row table), `data_provider_runs` row count, `watchlist` row count, and sha256
    of both the certified-claims and staging ledger files.
  - `freeze_attempt_identity(session, config)` (Stage B2) — freezes ONE `engine_identity` (via the SAME
    `app.engine.engine_identity.compute_engine_identity` function `scanner.persist_run_payload` already
    stamps onto new `ScannerRun` rows — reused, not reimplemented) plus a decomposed, human-auditable
    `config_subset`/`config_subset_hash` for this attempt.
  - `check_attempt_identity_consistency(frozen_identity, run_identity) -> bool` — the pure, per-run
    invariant helper a later stage will call once per rebuilt run. Fail-closed: a `None` run identity
    (pre-stamping era / not yet persisted) is never treated as consistent. No aggregate-only form exists
    (iter-9 lesson).
- **New read-only CLI `apps/backend/scripts/run_j11_pre_reset_inventory.py`**: wraps the two functions
  above against the LIVE `apps/backend/data/trendora.db` via the existing `app.db.get_engine()` helper
  (never `create_db_and_tables()`, never a raw file copy). Writes
  `runs/goal-market-compass-iter-10/j11-pre-reset-inventory.json` and
  `runs/goal-market-compass-iter-10/j11-frozen-identity.json`, and embeds a `zero_write_proof` block in
  the inventory artifact: an independent second `daily_prices` count/date-range/fingerprint re-query plus
  a before/after mtime check on the db file itself.
- **New tests `apps/backend/tests/test_j11_maintenance.py`** (fixture-DB-only, same pattern as
  `test_manifest_invariants.py` — fresh `sqlite://` engine, `SQLModel.metadata.create_all`, hand-built
  rows; never `loaded_engine`): TC-3 (FK-on delete, no violation, manifest untouched), TC-4 (rebuilt-same-
  `as_of`, `basis_disclosure` reports `rebuilt`, manifest fields unchanged), TC-5 (degenerate orphan — no
  replacement run at all — `basis_disclosure` reports `unavailable`, never raises, never fabricates), TC-6
  (id-reuse trap — same numeric id, later `created_at` — still `rebuilt`, never `original`), TC-7
  (`check_attempt_identity_consistency` matching AND mismatched cases, asserted as two separate tests, not
  one aggregate), plus two supporting tests (`freeze_attempt_identity` reproducibility/agreement with
  `compute_engine_identity`, and `capture_pre_reset_inventory` shape/counts on a small synthetic slice)
  and a literal-list guard test (`INCIDENT_DATES` matches the authoritative 11-date removal-audit list).

## Files Changed

- `apps/backend/app/models.py` — dropped the FK declaration from `NextSessionManifest.source_run_id`;
  added the Stage B1 "Intended end state" comment (verbatim from `docs/goal.md` J-11 step 11).
- `apps/backend/app/engine/j11_maintenance.py` — new: `capture_pre_reset_inventory`,
  `freeze_attempt_identity`, `check_attempt_identity_consistency`, `INCIDENT_DATES`.
- `apps/backend/scripts/run_j11_pre_reset_inventory.py` — new read-only CLI (see above).
- `apps/backend/tests/test_j11_maintenance.py` — new fixture-DB-only test file (9 tests, all passing).

## Tests Run

Targeted only, per the session's resource contract (never the full suite; never two pytest processes
concurrently):

1. `cd apps/backend && .venv/bin/python -m pytest tests/test_j11_maintenance.py -v`
   Result: **9 passed**, 0 failed, 0.78s.
2. `cd apps/backend && .venv/bin/python -m pytest tests/test_manifest_invariants.py -q` (regression —
   unmodified, the 12 named manifest invariants including TC-14..TC-25)
   Result: **37 passed**, 0 failed, 3.73s.
3. `cd apps/backend && .venv/bin/python -m pytest tests/test_j10_recovery.py -q` (regression — unmodified)
   Result: **50 passed**, 0 failed, 4.17s.
4. `cd apps/backend && .venv/bin/python -m pytest tests/test_no_magic_numbers.py -q` — ran to confirm
   `j11_maintenance.py` introduces no magic-number violation (it is correctly NOT added to `CALC_FILES`,
   for the same reason `j10_recovery.py` is excluded: nothing here is a scoring weight, band edge, or
   decision cutoff — `INCIDENT_DATES` is a literal historical fact, matching the `RECOVERY_DATES`
   precedent). Result: 1 of 2 tests in this file FAILS, but the failure is `test_engine_calc_code_has_
   no_magic_numbers` reporting PRE-EXISTING float literals in `indicators.py`/`forward_testing.py`/
   `research.py` — three files this iteration never touched (`git status` confirms; `git log` shows
   their last change predates this iteration). Not a regression introduced by this iteration's diff; not
   in scope to fix (touching those files would violate the "fix only the listed issues" / "don't touch
   code outside your task scope" rule — no report names this as this iteration's issue).
5. `apps/backend/.venv/bin/python scripts/run_j11_pre_reset_inventory.py` — the ONE authorized live-DB
   interaction this iteration (read-only). Ran successfully; see "Zero-Write Proof" and "Captured
   Inventory" below.

## Zero-Write Proof (TC-8)

`apps/backend/data/trendora.db` mtime + size, captured before ANY work this iteration and again after
everything above (including the live inventory script run):

```
before: mtime=1787482245 size=8365871104
after:  mtime=1787482245 size=8365871104   (identical)
```

The inventory script's own embedded `zero_write_proof` (an independent second `daily_prices`
count/date-range/fingerprint re-query, run inside the SAME invocation, plus its own before/after mtime
check around the capture):

```json
{
  "counts_match": true,
  "fingerprints_match": true,
  "mtime_unchanged": true,
  "mtime_before": 1787482245.3511636,
  "mtime_after": 1787482245.3511636
}
```

daily_prices fingerprint (both the capture and the independent spot-check): row_count=3310374,
min_date=1996-01-02, max_date=2026-08-12, fingerprint=`572691772b7313b893055a9ada984945292bbcd07686f4702193a03e9223451a`.

No other write path touched the file: no `start-backend.sh`/`start-frontend.sh` run, no
`create_db_and_tables()`/`metadata.create_all()` call anywhere in the new script (deliberately —
that path runs additive-ALTER/index-hygiene sweeps this script has no business triggering), no file copy.
All targeted-test runs (item 1-4 above) use isolated in-memory/temp-file fixture engines, never the live
DB — confirmed by `test_j10_recovery.py`/`test_manifest_invariants.py` using their own `engine`/
`loaded_engine`-free fixtures and by the mtime being identical across the whole session.

## Captured Inventory (from `runs/goal-market-compass-iter-10/j11-pre-reset-inventory.json`)

Per-incident-date state (11 dates; `sr_c`/`ss_c`/`ts_c` = scanner_results/sector_scores/theme_scores
counts; `fr_own`/`fr_into` = forward_returns originated-from-this-run / measured-into-this-date;
`manifests` = manifest count) — cross-validated against `docs/goal.md`'s own independently-recorded
2026-08-21 audit and found byte-for-byte consistent:

| date | run present | run_id | sr_c | ss_c | ts_c | fr_own | fr_into | manifests |
|---|---|---|---|---|---|---|---|---|
| 2026-05-12 | yes | 3149 | 542 | 31 | 11 | 2771 | 2770 | 0 |
| 2026-05-13 | no | — | 0 | 0 | 0 | 0 | 2771 | 0 |
| 2026-07-10 | no | — | 0 | 0 | 0 | 0 | 2769 | 0 |
| 2026-07-13 | no | — | 0 | 0 | 0 | 0 | 2217 | 0 |
| 2026-07-24 | no | — | 0 | 0 | 0 | 0 | 1660 | 0 |
| 2026-07-27 | no | — | 0 | 0 | 0 | 0 | 1660 | 0 |
| 2026-08-03 | no | — | 0 | 0 | 0 | 0 | 1662 | 0 |
| 2026-08-05 | no | — | 0 | 0 | 0 | 0 | 1660 | **2 (orphaned)** |
| 2026-08-10 | yes | 3114 | 539 | 31 | 11 | 20 | 124 | 1 |
| 2026-08-11 | yes | 3150 | 539 | 31 | 11 | 20 | 20 | 3 |
| 2026-08-12 | yes | 3148 | 539 | 31 | 11 | 0 | 20 | 6 |

This exactly matches `docs/goal.md`'s recorded "Verified current state (read-only, 2026-08-21)" line
(0/1/2/1/3/6 manifests in the same order) and its "orphaned manifests point at ids 3048, 3049, 3081, 3112"
claim (my capture shows those exact source_run_id values on 2026-08-10/11/12/05 respectively) and its "the
three highest ids in the whole table (3148, 3149, 3150) are all incident-date runs" claim (my capture
shows exactly those three ids on 2026-08-12/05-12/08-11).

Manifest hash list (content_hash/manifest_hash, first 12 hex chars, for the 4 incident dates carrying a
manifest):

- **2026-08-05** (source_run_id 3112, orphaned — 0 surviving run): v1 content=`d90138a6b5ed`
  manifest=`bcf122a2b19d`; v2 content=`d90138a6b5ed` manifest=`bd5fc089f872`
- **2026-08-10** (source_run_id 3048): v1 content=`f1b6d2bdeaba` manifest=`d0b1171cb867`
- **2026-08-11** (source_run_id 3049): v1 content=`273d91bfea09` manifest=`627efe339b98`; v2
  content=`273d91bfea09` manifest=`56dd84285330`; v3 content=`273d91bfea09` manifest=`212c5c0ebf61`
- **2026-08-12** (source_run_id 3081): v1 content=`8bb67cd69448` manifest=None (pre-freeze-era row); v2-v6
  content=`3aff17d15a91` manifest=`bff668ec8579`/`35f22104a26e`/`746c9c6f3cd7`/`6f05c7559e50`/`9bc08cfba04f`

Other captured counts: `data_provider_runs_count=549`, `watchlist_count=6`,
`certified_claims_ledger` sha256=`5d435cff51aff4e8a0072e466c50ad76c8063f8883a20fdbd78db8286135e721`
(7 entries per prior audits, unread/unmodified this iteration), `staging_ledger` sha256=
`3e85847e8d7424e3f473b758c18f83e5819db8c66904c5a4ec4b490c463f441a`.

`j11-frozen-identity.json` records `engine_identity=6261ca1791b59771f3b6b6829142e2cf7c0f33d0fa4ea00a2f1e2c8d1d6b3a6e`
(this attempt's frozen identity — computed from `app.engine.engine_identity.compute_engine_identity`,
the same function that stamps `ScannerRun.engine_identity`; NOT the identity a future Stage D attempt will
necessarily match, since code/config may change before that later iteration runs).

## Known Issues

- **`test_no_magic_numbers.py`'s `test_engine_calc_code_has_no_magic_numbers` fails independent of this
  iteration** (see "Tests Run" item 4) — pre-existing float literals in `indicators.py`, `forward_
  testing.py`, `research.py`. Flagging for reviewer/QA triage since it surfaced during my targeted run;
  not fixed here (out of this iteration's scope, and the files are untouched by this diff).
- Stage B2's `freeze_attempt_identity` currently freezes the identity as of THIS iteration's dev-time
  code/config state. `docs/goal.md` step 12 requires the LATER regeneration attempt (Stage C-G, a future
  iteration) to freeze its OWN identity fresh at that time and prove every rebuilt run matches it — this
  iteration's captured `j11-frozen-identity.json` is evidence of the mechanism working, not the identity
  Stage D will actually use (a future iteration must call `freeze_attempt_identity` again immediately
  before Stage C begins).
- `runs/goal-market-compass-iter-10/depth-dispatched` was not found in the run directory at the time of
  this handoff (checked; only `goal-slice-exec.md`, `plan.md`, `status.json`, and the two new artifacts
  from this iteration's own script exist). Per `scripts/automation/lib/common.sh`, that file is written
  by the automation harness/dispatcher, not by the developer agent — TC-9 is outside this agent's write
  scope; flagging so the reviewer/QA/auditor knows to check it at the harness level rather than expecting
  it in this diff.
