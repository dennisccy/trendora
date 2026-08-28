# goal-market-compass-iter-26 Dev Handoff

**Phase:** goal-market-compass-iter-26
**Date:** 2026-08-28
**Agent:** developer
**Status:** complete

## Mode note

This iteration is LEAN-dispatched (`iter-26/depth-dispatched` reads `lean`) despite the spec's own
`Depth: full`. Per the pump coordinator note, no independent reviewer/auditor/QA lane will check this
work before the evaluator. I have held myself to the full-depth bar throughout: every DoD item below is
backed by evidence I personally captured (test output, live API/DB reads, or a rendered-HTML grep),
never a tick without a citation, and I say plainly below what I could not fully verify.

## Central safety decision — honored, not undone

Per the spec's BACKGROUND and the pump note, I did **not** call `remove_data()` / `clear_snapshot_dates()`
/ any backfill against the canonical `apps/backend/data/trendora.db`, and did not touch
2026-08-05/08-10/08-11/08-12's `daily_prices`/`scanner_runs` rows. The destructive-drill portions of
J-05/J-06 are proven entirely against the isolated-engine fixture suite (test files below); the only
live canonical-DB action is the one authorized additive `POST /api/compass/regenerate?as_of=2025-04-15`
write, plus read-only GETs. `apps/backend/data/trendora.db-wal` was never opened for write by me directly
(only through the normal FastAPI/SQLAlchemy request path, which is how every prior iteration's live reads
worked too).

## What Was Built

### Backend test-gap closures (all in existing test files — no production code changed this iteration)

- **TC-1**: Narrowed `test_tc15_no_update_statement_targets_next_session_manifests`'s AST scanner
  (`apps/backend/tests/test_manifest_invariants.py`). The old scanner flagged ANY `.update(...)`
  attribute call in a module that merely mentions `next_session_manifests`/`NextSessionManifest` in text —
  false-positiving on 5 files (the spec named 3; I found 5 by direct execution:
  `j11_disposable_clone.py` [`digest.update(chunk)`], `j11_stage_d.py` [`observation.update({...})`],
  `j11_stage_e_execute.py` [`latest_run_check.update({...})`], `j11_avb_correction.py`
  [`h.update(repr(row).encode())`], `j11_stage_g_verify.py` [7× `entry.update({...})`] — all dict/hashlib
  calls, none touching the manifest table). The new scanner (factored into
  `_scan_source_for_manifest_update_offenders`, called by the test) flags only: the SQLAlchemy Core
  `update(NextSessionManifest)` construct (bare-name or module-attribute call), the ORM
  `<query-chain ending in .query(NextSessionManifest)>.update(...)` bulk-update idiom, and a raw SQL
  string literal containing both "update" and the table name. Added a companion mutation-kill test,
  `test_tc15_scanner_mutation_check_catches_a_real_manifest_update_statement`, that runs the scanner
  against synthetic source text (never against real `app/engine` code) proving it still catches all three
  real-UPDATE shapes, while confirming the exact false-positive shapes already in the codebase stay clean.
- **TC-2**: New fixture test `test_tc2_export_file_bytes_equal_served_payload_and_manifest_hash_reproduces`
  (audit finding B3, iter-3, closed this iteration): freezes a manifest on an isolated engine, asserts the
  on-disk export file's bytes equal `compass.manifest_row_payload(row)`'s canonical re-serialization
  byte-for-byte (the same shape `GET /api/compass` serves — not the in-memory write-time dict), and that
  recomputing `manifest_hash` over the exported bytes (with `manifest_hash` itself excluded, per the
  canonical rule) reproduces the embedded value. Also cross-checked via `compass.verify_manifest_hash`.
- **TC-7**: New fixture test
  `test_tc7_backfilling_a_separate_date_leaves_the_first_stored_manifest_unchanged`: freezes a manifest for
  one as_of, then freezes a SEPARATE manifest for an unrelated later date (mirroring what the finalize hook
  does per newly-processed date), then re-reads the first manifest and asserts its version and full
  `manifest_row_payload` are unchanged. This exact "another date's backfill" scenario was not previously
  its own assertion (the closest existing coverage — `test_tc15_clear_snapshot_set_and_remove_data_delete_zero_manifest_rows`
  and `test_tc14_time_safety_...` — prove ROW COUNT survival and SAME-as_of post-bar-perturbation
  hash-stability respectively, neither of which is "a separate date's own freeze").
- **TC-8/TC-9**: New route-level test in `test_api_compass.py`,
  `test_compass_route_never_404s_and_manifest_bytes_survive_a_removed_historical_run`. See "Re-verified
  finding (B2)" below — the literal TC-8 wording (`basis.status=="unavailable"` via the live route) is
  **not reachable** given current self-heal behavior, so this test proves the TRUE observed behavior
  instead of a false assertion: the route never 404s, the manifest's `manifest_hash`/`version` survive
  byte-identical across a historical run+bar removal, and the route-observed basis is `"rebuilt"`.
- **TC-3/TC-4** (confirm-and-cite, not rebuilt — existing coverage already proves both, re-run green):
  - TC-3 (at-ingest flagship): `test_api_compass.py::test_compass_route_serves_every_new_field_directly`
    (`mode=="at_ingest"`, `version==1`, `frozen is True`, `prospective_eligible is True`,
    `generation.producer=="ingest_finalize"`) + `test_manifest_invariants.py::test_tc21_available_at_utc_never_earlier_than_generated_at_plus_margin`
    (well-formed `available_at_utc` fence) + `test_manifest_invariants.py::test_tc18_no_later_bar_resolves_at_ingest_mode`
    (the underlying mode-resolution rule).
  - TC-4 (same-loop historical → retrospective): `test_compass.py::test_get_or_create_manifest_historical_asof_still_create_once_mints`
    (`row.mode=="retrospective"`, `row.prospective_eligible is False`) +
    `test_manifest_invariants.py::test_tc25_retrospective_manifest_validates` (mode=retrospective, schema
    validates) + `test_manifest_invariants.py::test_tc18_bar_dated_after_asof_forces_retrospective_mode`.
- **Other confirm-and-cite items** (all re-run green, none rebuilt):
  - Create-once idempotency: `test_compass.py::test_get_or_create_manifest_computes_once_then_serves_from_storage`,
    `test_api_compass.py::test_compass_route_computes_once_serves_from_storage_after`.
  - Retrospective create-once-on-GET: `test_compass.py::test_get_or_create_manifest_historical_asof_still_create_once_mints`.
  - Schema conformance both kinds: `test_manifest_invariants.py::test_tc25_frozen_at_ingest_manifest_validates`,
    `test_tc25_retrospective_manifest_validates`.

### TC-10 — the four orphaned export files (investigated, not deleted)

Investigated `2024-06-08_v1.json`, `2024-07-01_v1.json`, `2024-07-08_v1.json`, `2024-08-01_v1.json` under
`apps/backend/data/exports/next_session_manifests/`. **Finding: leftover test-fixture artifacts, not an
AG-12 concern.**
- All four decode as valid manifest documents with `mode: at_ingest`, `generation.producer:
  ingest_finalize`.
- `sqlite3 -readonly data/trendora.db "SELECT as_of, version FROM next_session_manifests WHERE as_of IN
  (...)"` returns **zero rows** for all four dates — no live DB row for any of them ever existed, so
  nothing was "mutated or deleted" (AG-12 is about a stored row/file being altered after the fact; here
  there never was a canonical row to begin with).
- All four dates are the exact synthetic as_of values used by existing isolated-fixture tests that call
  `compass.get_or_create_manifest(..., producer="ingest_finalize")` **without** setting
  `TRENDORA_COMPASS_EXPORT_DIR`: `2024-06-08` = `test_api_compass.py`'s `compass_engine` frontier date,
  `2024-07-01` = `test_manifest_invariants.py`'s `frontier_run` fixture date (used by many tests there),
  `2024-07-08` = `test_ingest_finalize_compass.py`'s `ASOF`, `2024-08-01` =
  `test_manifest_invariants.py::test_tc17_concurrent_requests_for_same_not_yet_computed_asof_yield_one_row`'s
  date. `_write_export` falls back to the real `compass.manifest.export_dir` (config default) whenever
  the env override isn't set — these tests use a throwaway SQLite engine for the DB but the REAL
  filesystem path for the export write, since `_write_export` has no session/engine-scoping.
- All four files share the same mtime (2026-08-20 12:10) — a single batch, consistent with an early
  (pre-incident) run of these three test files.
- **Not fixed this iteration** (out of scope — not an IN SCOPE bullet, and touching 3+ other test files'
  fixture setup is broader than "close backend test gaps"): flagged in Known Issues below as a genuine,
  minor test-isolation gap worth a follow-up. My OWN new tests (TC-2, TC-7, and the pre-existing
  `test_tc15_export_writer_never_rewrites_an_existing_artifact`) all set `TRENDORA_COMPASS_EXPORT_DIR` via
  `monkeypatch` + `tmp_path`, so none of my work added a fifth orphan. Confirmed via `ls -la
  data/exports/next_session_manifests/` before/after — mtimes unchanged, no new file.

### Re-verified finding (iter-3 audit's B2) — CONFIRMED STILL OPEN

The spec's NOTES asked me to re-verify (not merely re-cite) whether "opening the page quietly rebuilds a
deleted run's data before the basis check can see it is gone" is still true. **It is, empirically
confirmed via two isolated fixture experiments** (not guessed):

`GET /api/compass` calls `resolved_run(session, as_of)` (→ `scanner.resolve_run` → `scanner.run_scan`)
**before** `get_or_create_manifest`/`basis_disclosure` run. `run_scan` self-heals unconditionally: if the
requested `as_of` still resolves to a valid date (any earlier bar exists anywhere), a missing `ScannerRun`
is silently **recreated** right there — so by the time `basis_disclosure` looks up "the current run for
this as_of", it is never actually absent. Consequence: **`basis.status=="unavailable"` is real, correct,
unit-tested code (`test_basis_disclosure_reads_unavailable_when_the_source_run_is_gone`) that is
structurally UNREACHABLE through the live `GET /api/compass` route as currently wired** — a request can
only ever observe `"available"` or `"rebuilt"`. I proved this two ways:
1. A 2-date-only fixture (removing the manifest's own frontier date, no bar existing after it): the route
   raises `AsOfError("future")` → HTTP 400 (the removed date "un-resolves" entirely).
2. A 3-date fixture (a later date exists after the manifest's as_of, so it's historical at request time):
   removing that as_of's run+bar and calling `GET /api/compass?as_of=<it>` returns HTTP 200 with the
   manifest payload byte-unchanged and `basis.status=="rebuilt"` — self-heal silently recreated the run.

This is a **pre-existing finding, not a regression I introduced**, and fixing the self-heal ordering (so
the basis check runs against the pre-self-heal state) is a deliberate, cross-cutting change to
`resolved_run`/every endpoint that uses it — explicitly outside this iteration's IN SCOPE list ("Building
any new drill-isolation infrastructure... is out of scope" and no self-heal-ordering item is listed).
Recorded here for reviewer/auditor/evaluator visibility. What TC-8/TC-9 as actually testable DID prove and
matters most for AG-12: the route never 404s, never crashes, and the manifest's stored bytes/version stay
byte-identical across the self-heal.

## Live, safe, canonical-database verification (read-only unless noted)

All performed against the canonical `apps/backend/data/trendora.db` via the normal backend/frontend
services (`scripts/start-backend.sh` on port 8255, `scripts/start-frontend.sh` on port 3255 — this repo's
deterministic port offset), both stopped cleanly at the end (`kill -TERM` then verified dead; confirmed
`curl` to both ports now returns nothing / connection refused).

1. **Read-only spot-check, `GET /api/compass?as_of=2026-08-12`** (version 6, current `at_ingest` row):
   captured the live response, stripped the read-time-only `basis`/`versions` fields, re-serialized via
   `compass._canonical_dumps` and compared byte-for-byte against the on-disk export
   `data/exports/next_session_manifests/2026-08-12_v6.json` — **identical, 355,711 bytes both sides**.
   Recomputed `manifest_hash` over the exported bytes (hash field excluded) —
   `9bc08cfba04fc2dcab7eeb35f7b695834ef69da5ca3b6634acca4c605d5769c3` both recomputed and embedded, and
   `compass.verify_manifest_hash` returns `True` on both the export document and the served document.

2. **Read-only, `/?asof=2025-04-15` manifest strip vs `GET /api/compass?as_of=2025-04-15`**: loaded the
   live frontend via Chrome DevTools automation and diffed the rendered DOM against the API response.
   Verified verbatim: mode badge `"retrospective"`, `"version 1"`, `"frozen"`, `"not prospective-eligible"`
   badges; all 4 provenance hash chips (`engine_identity`, `candidate_rule_hash`, `cohort_rule_hash`,
   `manifest_config_hash`) match the API's values byte-for-byte (confirmed via each chip's `title=`
   attribute, which carries the full hash); dataset stamp `"r3112-f6761224"`; universe pool hash
   `4f7aeca5bed8532c...`; `"Members: 531"` == `universe.member_count`; 10 candidate cards rendered ==
   `len(selection.candidates)`; "Basis: available" == `basis.status`. **Audit table**: the disclosure's own
   header text reads `"Audit table — comparison cohort (521) + near-threshold shadow (28)"`, and I counted
   521 distinct `data-testid="compass-cohort-row-<TICKER>"` elements in the rendered DOM (not a truncated
   preview — every row is actually rendered) — `521 == universe.member_count (531) - candidate count
   (10)`, exactly the acceptance criterion. Shadow count 28 also matches `len(near_threshold_shadow)`.

3. **One additive live write — `POST /api/compass/regenerate?as_of=2025-04-15` via the UI's confirm-gated
   "Regenerate manifest" control** (clicked the button, confirmed the in-app modal
   `data-testid="compass-manifest-regenerate-confirm-modal"`, clicked
   `compass-manifest-regenerate-confirm-button" — never called the API directly, exercising the actual
   confirm gate end-to-end):
   - Minted version 2 (`sqlite3 -readonly` confirms `2025-04-15|1|retrospective` and
     `2025-04-15|2|retrospective` both present).
   - Version 1 verified byte-identical to its pre-regenerate capture: `content_hash`, `manifest_hash`,
     `prospective_eligible`, and the FULL `manifest_row_payload` dict (session_delta, selection,
     comparison_cohort, near_threshold_shadow, every field) compared equal via a direct DB read against my
     pre-regenerate JSON capture — `True` on every field.
   - Version 2: `mode=="retrospective"`, `prospective_eligible is False` (regenerate is never eligible, per
     `_derive_prospective_eligible`'s `producer=="ingest_finalize"`/`version==1` gates),
     `content_hash == v1.content_hash` (same underlying selection data), `manifest_hash != v1.manifest_hash`
     (different generation metadata) — exactly the TC-6 contract.
   - UI lists both versions with their own stamps: found
     `data-testid="compass-manifest-versions"` rendering `v1` (`2026-08-20T11:41:00.381102+00:00`,
     retrospective, not eligible) and `v2` (`2026-08-28T12:45:04.938308+00:00`, retrospective, not
     eligible) side by side.
   - No export file was written for the regenerate (correct — `_write_export` only runs when
     `mode=="at_ingest"`, and this manifest is `retrospective`); confirmed no new file appeared under
     `data/exports/next_session_manifests/`.

4. **Before/after row-count spot-check** (`sqlite3 -readonly`, immediately before starting the backend and
   immediately after stopping it):
   - `daily_prices`: 3,310,374 → 3,310,374 (unchanged)
   - `scanner_runs`: 3,128 → 3,128 (unchanged)
   - `next_session_manifests`: 24 → 25 (**exactly +1**, the authorized `as_of=2025-04-15, version=2` row)
   - `next_session_manifests` rows for `as_of=2025-04-15`: `{version 1, retrospective}`,
     `{version 2, retrospective}` — matches expectation exactly.
   - I did not capture a full row-by-row hash of all 24 pre-existing rows before the write, so I cannot
     show a literal per-row diff for the other 23 dates beyond the aggregate count. What I CAN state with
     certainty: (a) the aggregate count for `next_session_manifests` moved by exactly +1, which is
     impossible if any other row had also been inserted or deleted; (b) `daily_prices`/`scanner_runs`
     counts are bit-for-bit unchanged, so no run/bar was created or removed anywhere (including via
     self-heal — none of my three live reads hit a missing run); (c) TC-1's now-passing AST scan proves NO
     code path in the entire engine layer can even issue an UPDATE against the manifest table, so an
     in-place content change to another row is not just unobserved but structurally impossible via any
     code path this session exercised. I consider this a fully adequate proof of TC-12, but flag the exact
     scope of what was diffed directly vs. guaranteed by construction, per the "state evidence, don't tick"
     instruction.

## Files Changed

- `apps/backend/tests/test_manifest_invariants.py` — narrowed TC-15's AST scanner (factored into
  `_scan_source_for_manifest_update_offenders` + `_references_manifest_target`), added the TC-1
  mutation-kill test, TC-2 (export-byte-equality), and TC-7 (separate-date backfill leaves a manifest
  unchanged).
- `apps/backend/tests/test_api_compass.py` — added the TC-8/TC-9 route-level test proving the route never
  404s and the manifest survives byte-identical across a historical run+bar removal (with the honest
  `"rebuilt"`-not-`"unavailable"` finding documented in its docstring).
- `docs/handoffs/goal-market-compass-iter-26-dev.md` — this handoff.

No files under `apps/backend/app/` or `apps/frontend/` were changed — this iteration closed test gaps and
produced live evidence against already-correct production code; no bug required a code fix.

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/test_manifest_invariants.py
tests/test_ingest_finalize_compass.py tests/test_api_compass.py tests/test_compass.py
tests/test_session_delta.py -v`

Result: **103 passed, 0 failed** (per-file: `test_manifest_invariants.py` 51 [was 48 — +3: TC-1 mutation
check, TC-2, TC-7], `test_ingest_finalize_compass.py` 3 [unchanged], `test_api_compass.py` 9 [was 8 — +1:
TC-8/TC-9 route test], `test_compass.py` 28 [unchanged], `test_session_delta.py` 12 [unchanged]).

Zero new regressions beyond the one genuine pre-existing failure fixed this iteration
(`test_tc15_no_update_statement_targets_next_session_manifests`, now passing with a mutation-kill
companion proving the fix doesn't just paper over the assertion).

Per the resource contract, I did NOT run the full backend suite (`pytest tests/`) — only the targeted
files above, run one at a time / in the single combined invocation shown (never two pytest processes
concurrently), matching `.claude/project-template.md`'s TEST COMMANDS.

## Required-still-passing journeys (J-01, J-04, J-10, J-11)

No production code under `apps/backend/app/` or `apps/frontend/` was touched this iteration — the only
canonical-DB write was the one authorized, additive `next_session_manifests` version-2 INSERT for
`as_of=2025-04-15`, which by construction (proven above) touched no other row/table. I did not re-run
J-01/J-04/J-10/J-11's own test suites or golden-script replay myself (that's the replay lane's job per the
pipeline, and re-running J-10/J-11's recovery machinery is explicitly the binding "Do not redo" — see OUT
OF SCOPE). Given zero app-code diff and a proven-scoped single DB write, I have no reason to expect
regression, but I have not personally re-executed their fixture suites this iteration — flagging this
honestly rather than claiming verification I didn't do.

## Anti-goal re-check

- **AG-9** (offline-deterministic ingest): no live external network call anywhere this iteration; the one
  write was an in-app confirm-gated action, not an ingest job, and touched none of the incident-window
  dates.
- **AG-12** (manifest immutability): version 1 proven byte-identical across the regenerate (full payload
  dict equality, not just hash equality); version 2 is a new row, never a mutation; TC-1's AST scan proves
  no code path can even issue an UPDATE against the table.
- **AG-17** (repair never rewrites provenance): not touched — no repaired/incident-window data was read or
  written; the one write's `prospective_eligible` correctly stayed `False` (regenerate is never eligible
  regardless of anything else).
- **AG-18** (the authorized migration preserves everything): not applicable — no migration ran this
  iteration.

## Known Issues

1. **Test-fixture export-dir isolation gap (pre-existing, not fixed this iteration)**: several existing
   fixture tests across `test_manifest_invariants.py`, `test_ingest_finalize_compass.py`, and
   `test_api_compass.py` call `compass.get_or_create_manifest(..., producer="ingest_finalize")` on a
   throwaway SQLite engine WITHOUT setting `TRENDORA_COMPASS_EXPORT_DIR`, so `_write_export` falls back to
   the real default export directory and leaves a synthetic export file there (the TC-10 orphans). Not an
   AG-12 issue (no canonical DB row ever existed for those dates), but worth a follow-up: monkeypatch
   `TRENDORA_COMPASS_EXPORT_DIR` in those pre-existing tests too. Out of scope for this iteration (not an
   IN SCOPE bullet; touching 3 files' unrelated fixtures beyond the listed test gaps).
2. **iter-3 audit finding B2 — confirmed still open** (see "Re-verified finding" above): `basis.status ==
   "unavailable"` is real, unit-tested, correct code that is currently unreachable through the live
   `GET /api/compass` route because `resolved_run`'s self-heal always recreates a missing run first. Not
   a safety issue for AG-12 (the manifest's own bytes are always safe regardless), but it means an operator
   reading the live UI's basis disclosure will never actually see "unavailable" for a resolvable as_of —
   only "available" or "rebuilt". Flagging for owner/evaluator triage on whether a future iteration should
   change the check ordering (a cross-cutting change to `resolved_run`, out of this iteration's scope).
3. Did not personally re-run J-01/J-04/J-10/J-11's own fixture suites this iteration (see above) — no
   app-code changed, so no expected regression, but not independently re-verified by me.
