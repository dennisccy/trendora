# goal-market-compass-iter-27 Execution Plan

## Alignment check

This iteration closes J-06's last unmet acceptance limb (`docs/goal.md` J-06 step 2: "assert `GET
/api/compass` still serves the manifest verbatim with a read-time basis disclosure showing the underlying
run is unavailable — never a 404, never a recompute"). The bug is the same one iter-3's audit (finding B2)
and iter-26's dev+reviewer+evaluator all re-confirmed live: `apps/backend/app/api/compass.py`'s `compass()`
route calls `resolved_run()` (which self-heals a missing `ScannerRun` via `run_scan`) BEFORE
`get_or_create_manifest`/`basis_disclosure` ever run, so `basis.status` can only ever observe `"available"`
or `"rebuilt"` — never `"unavailable"` — and a recompute has already happened, which J-06 step 2 forbids.
The spec's fix is narrowly scoped to the compass route's call ordering plus one new pure-read helper; it
does not touch `snapshot_serving.resolved_run` or `scanner.run_scan`, so every other route's self-heal
behavior (`/`, `/stocks`, `/sectors`, `/themes`, dashboard, market-phase) is untouched. No scope creep
identified — the spec's OUT OF SCOPE list is consistent with `docs/goal.md`'s anti-goals (AG-9 no live
fetch, AG-12 manifest immutability, AG-17 no provenance rewrite, AG-8 no unbounded loads) and this plan
does not add anything beyond it.

Verified directly against current code (not just the spec's description):
- `apps/backend/app/api/compass.py`'s `compass()` (lines ~54-67) calls `run = resolved_run(session, as_of)`
  first, then `get_or_create_manifest(session, run)`.
- `apps/backend/app/engine/compass.py`'s `get_or_create_manifest` (line 1042) has its own inline
  existing-row query at lines 1055-1059 (`select(NextSessionManifest).where(as_of ==
  current_run.asof_date).order_by(version.desc()).first()`) — this is the exact query the new
  `latest_manifest_for_date` helper must factor out and both call sites must share.
- `apps/backend/app/engine/snapshot_serving.py`'s `resolve_run` (scanner.py:338) literally calls
  `resolve_as_of_date` FIRST, then `run_scan` — i.e. `resolved_date(session, as_of)` (already imported in
  `api/compass.py`) raises the EXACT SAME `AsOfError`/status-code mapping as the first half of
  `resolved_run`, for the same as_of, with zero self-heal side effect. This confirms the spec's ordering
  (`resolved_date` → check manifest → only then `resolved_run`) preserves TC-9/TC-10's error behavior
  byte-for-byte on both the fast and slow branches — not an assumption, a structural fact of the existing
  code.

## What to Build

Backend only (no frontend change — `basis.status === "unavailable"` is an already-shipped, already-tested
rendered state in `apps/frontend/lib/basis-disclosure-label.ts`; this iteration only fixes when the backend
can honestly reach it):

- `apps/backend/app/engine/compass.py`: add a pure read-only helper
  `latest_manifest_for_date(session: Session, as_of: date) -> Optional[NextSessionManifest]` — the latest
  stored manifest version for a date, or `None`; no run lookup, no write. Refactor
  `get_or_create_manifest`'s existing inline query (lines 1055-1059) to call this helper instead of
  duplicating the query shape.
- `apps/backend/app/api/compass.py`, `compass()` route: reorder to
  1. `resolved = resolved_date(session, as_of)` (already-imported; validates/maps as-of errors, creates
     nothing, never self-heals) — preserves TC-9 (422 unparseable / 400 future) identically.
  2. `existing = latest_manifest_for_date(session, resolved)` (new import from `app.engine.compass`).
  3. If `existing is not None`: serve it directly via `manifest_row_payload(existing)` +
     `_read_time_additions(session, existing)` (whose `basis_disclosure` call is already a pure read-only
     `ScannerRun` SELECT) — WITHOUT ever calling `resolved_run`/`run_scan`. This is the branch that makes
     `basis.status == "unavailable"` reachable when the manifest's source run has been removed.
  4. Else: fall through to today's unchanged path — `run = resolved_run(session, as_of)` →
     `get_or_create_manifest(session, run)` (still the only branch that may create a `ScannerRun` or mint a
     manifest, exactly as today; preserves TC-5/TC-10's create-once/frontier-guard behavior).
  `POST /api/compass/regenerate` is untouched (already correct per iter-26 verification).
- `apps/backend/tests/test_api_compass.py::test_compass_route_never_404s_and_manifest_bytes_survive_a_removed_historical_run`:
  flip the final assertions to the FIXED behavior — `basis.status == "unavailable"` (not `"rebuilt"`), and
  the removed `ScannerRun` stays absent (`healed is None`, not `is not None`) after the `GET` — and rewrite
  the surrounding docstring/comment, which currently documents the bug as a structural route limitation.
- Same file, two new tests:
  - Restore-path: starting from the state left by the flipped test above (manifest still serving
    `"unavailable"`), re-create the `ScannerRun` for that as_of (a) with the SAME `created_at` the
    manifest's `generation.source_run_created_at` recorded → assert `basis.status` flips to `"available"`;
    (b) with a DIFFERENT `created_at` → assert `"rebuilt"`. In both cases assert the manifest's
    `manifest_hash`/`version`/full payload stay byte-identical to the pre-removal capture (J-06 step 3).
  - Warm-path regression: with an existing manifest and its run intact, two consecutive `GET` calls through
    the route function return byte-identical responses and add zero new `ScannerRun` rows — proves the new
    fast-path branch is inert on the common already-working case (TC-1/TC-6/TC-7 shape).
- Dev handoff: enumerate, via a read-only SQL query against the live canonical DB (never hardcoded), the
  manifest-less as-of dates inside the incident window from `next_session_manifests`/`scanner_runs`, and
  record that this iteration's own test/browser-qa plan never issues a `GET`/`POST` against any of them
  (TC-8) — these 7 dates must stay manifest-less per the binding `docs/goal.md` "OWNER RULING — J-11
  CLOSED".

## Agents Required
- developer: yes -- implements the route reorder, the new helper, the refactored existing-row check, the
  flipped test + two new tests, and the read-only incident-date enumeration for the handoff
- backend-data: yes -- read-only live-DB verification only (TC-6/TC-7/TC-8 before/after row counts on
  `next_session_manifests`, `scanner_runs`, `daily_prices`; the incident-date enumeration query); no
  schema change, no migration, no destructive/backfill action against the canonical DB
- frontend-ux: no -- zero frontend files touched this iteration

## Frontend Present
no

## Files to Create/Modify
- `apps/backend/app/engine/compass.py` -- add `latest_manifest_for_date(session, as_of)`; refactor
  `get_or_create_manifest`'s existing-row query (lines ~1055-1059) to call it
- `apps/backend/app/api/compass.py` -- reorder `compass()` to check `latest_manifest_for_date` (via
  `resolved_date`) before ever calling `resolved_run`/`run_scan`; add the new import; `compass_regenerate`
  untouched
- `apps/backend/tests/test_api_compass.py` -- flip
  `test_compass_route_never_404s_and_manifest_bytes_survive_a_removed_historical_run`'s assertions +
  docstring to the fixed behavior; add the restore-path test (same-`created_at` → available,
  different-`created_at` → rebuilt); add the warm-path zero-side-effect regression test
- `docs/handoffs/goal-market-compass-iter-27-dev.md` -- dev handoff: TC-1..TC-10 evidence, the read-only
  incident-date enumeration, before/after row counts, and citation of the existing J-06 test list (time
  safety, rebuild survival, reproducibility, create-once concurrency, cohort reproducibility,
  prospective-eligibility derivation, availability-fence conservatism, artifact tamper detection,
  hash-scope separation, identity-separation counter-tests, disposition partition, schema conformance) as
  re-run green, unmodified

Do NOT touch: `apps/backend/app/engine/snapshot_serving.py` (`resolved_run`), `apps/backend/app/engine/scanner.py`
(`run_scan`, `resolve_run`, `resolve_as_of_date`) -- the shared self-heal machinery every other route
depends on stays byte-identical; `compass_regenerate` in `api/compass.py`; any frontend file; the
`next_session_manifests` schema; `apps/backend/data/trendora.db-wal` (never delete/alter); the 7
manifest-less incident dates (never mint a manifest for them, per AG-17 / OWNER RULING J-11 CLOSED).

## Test commands (targeted only, per project-template.md NEVER list)
```
cd apps/backend && .venv/bin/python -m pytest tests/test_api_compass.py tests/test_manifest_invariants.py \
  tests/test_ingest_finalize_compass.py tests/test_compass.py -v
```
Never the full suite (`pytest tests/`, bare `pytest`, wide `-k`); never two pytest processes concurrently;
reuse a running backend/frontend on 8255/3255 if already up rather than starting a second instance.

## Key Test Scenarios
- TC-1: fixture DB, frozen manifest for as_of=D with intact `ScannerRun` -> `GET /api/compass?as_of=D`
  through the real route function returns 200, `basis.status == "available"`, `scanner_runs` row count
  unchanged.
- TC-2 (the core fix, flipped from the existing bug-documenting test): TC-1's `ScannerRun` deleted in the
  fixture, `GET` again -> 200 (never 404), `basis.status == "unavailable"`, `basis.detail` states the run
  is no longer stored, manifest bytes (`content_hash`/`manifest_hash`/`version`/full payload) byte-identical
  to TC-1, `scanner_runs` row count UNCHANGED (no self-heal fired) -- this is the assertion that flips from
  the current bug-proving state.
- TC-3: re-create the `ScannerRun` with the SAME `created_at` as recorded -> `basis.status == "available"`
  again, payload bytes unchanged from TC-1.
- TC-4: re-create with a DIFFERENT `created_at` -> `basis.status == "rebuilt"`, payload bytes unchanged from
  TC-1 (only read-time `basis` differs).
- TC-5: no manifest yet for historical as_of=E, two sequential `GET`s -> first mints exactly one row
  (`mode: retrospective`), second adds zero further rows (create-once path unmodified by the reorder).
- TC-6: live canonical DB, 2025-04-15 manifest (frozen iter-26, run intact), two `GET`s -> both 200,
  `"available"`, byte-identical responses; before/after row counts on `next_session_manifests`,
  `scanner_runs`, `daily_prices` identical (zero rows added/removed/changed) -- taken AFTER every lane
  finishes, per the iter-23b lesson (a `.db`/`-wal` checksum alone is not proof).
- TC-7: live canonical DB, 2026-08-12 frontier manifest (`at_ingest`, v1) -> 200, `mode`/`version`/
  `manifest_hash` unchanged; same before/after row-count discipline as TC-6.
- TC-8: read-only enumeration of the manifest-less incident-window dates; none of them is ever requested by
  this iteration's test/browser-qa plan via `GET /api/compass`, `?asof=` on `/`, or
  `POST /api/compass/regenerate`; `next_session_manifests` row count for those dates is identical (and
  zero) before and after.
- TC-9: `as_of=not-a-date` and `as_of=<future date>` -> unchanged status codes (422 / 400) on BOTH the fast
  (existing-manifest) and slow (create) branches -- structurally guaranteed since `resolved_date` is the
  first call in both, matching `resolve_run`'s own internal ordering.
- TC-10: current frontier as_of with no manifest minted yet, non-finalize `GET` -> still raises
  `ManifestNotYetFrozen` -> still HTTP 404 (the fast-path only fires when a manifest already exists, so this
  guard is structurally unaffected).
- J-06 DoD: browser-qa-agent live regression only (TC-6/TC-7 screenshot of "Basis: available" on an intact
  manifest+run pair) -- no live `ScannerRun` deletion is authorized this iteration, so the `"unavailable"`
  state itself is proven at the fixture/route level only (TC-1..TC-5, TC-9, TC-10), evaluated the same way
  J-05 was scored in iter-26.
- Required-still-passing (J-01, J-04, J-05, J-10, J-11) verified via the deterministic replay lane + LLM
  fallback; no production code outside `app/api/compass.py` / `app/engine/compass.py` is touched, so no
  regression is expected, but this must be confirmed by the replay lane, not assumed.
