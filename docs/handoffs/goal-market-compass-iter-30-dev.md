# goal-market-compass-iter-30 Dev Handoff

**Phase:** goal-market-compass-iter-30
**Date:** 2026-09-01
**Agent:** developer
**Status:** complete

## What Was Built

This is an operational-plus-test iteration, not a feature iteration — zero engine/API/frontend code
was changed. The one production-code-path exercised is the already-shipped, already-proven
`POST /api/compass/regenerate` action (shipped iter-3, proven live on `2025-04-15` at iter-26, proven
live again on `2026-08-03` at iter-29).

- **The one authorized live mint.** Issued exactly one
  `POST /api/compass/regenerate?as_of=2026-08-12&confirm=true` against the running canonical backend
  (port 8255, started via `bash scripts/start-backend.sh`). This minted `next_session_manifests`
  version 7 for `as_of=2026-08-12` (the frontier / default-landing date) via `regenerate_manifest`
  (`apps/backend/app/engine/compass.py:1185`), which calls the SAME `_freeze_manifest` writer as
  `build_manifest_payload` / `build_state_band` — zero code changed in either.
- **New unit test** closing the auditor's iter-29 T1 gap: a REGENERATED version on a frontier-shaped
  as-of now has explicit fixture-scoped coverage proving `state_band` comes out populated with real
  words AND `prospective_eligible: False` in the SAME call.
- **Updated `J-07.json` regression golden** so it asserts the three `compass-state-band-*-direction`
  testids' own rendered text at the DEFAULT `/` view (no `asof` param), scoped via a Playwright
  `:has-text()` CSS pseudo-selector per testid — not merely a page-wide text search, and not merely
  element-presence. Updated and self-verified BEFORE the pipeline's own replay lane runs.

## Files Changed

- `apps/backend/tests/test_manifest_invariants.py` -- added `MarketPhaseCache` / `market_phase_module`
  imports, a new `frontier_run_with_prior_and_phase` fixture (a `DailyPrice` bar dated at the later
  run's as-of + `MarketPhaseCache` seeded for both dates, so `build_state_band` has real severity
  inputs), and the new test
  `test_regenerate_on_frontier_yields_state_band_and_prospective_eligible_false`. Placed here (the
  plan's suggested natural location) rather than `test_compass.py` because it sits directly beside the
  existing `regenerate_manifest` / TC-20 / TC-23 coverage this test extends.
- `runs/goal-session-market-compass/journey-scripts/J-07.json` -- inserted three new steps (4, 5, 6)
  asserting `compass-state-band-regime-direction`, `-stress-direction`, `-breadth-direction` each show
  the real word "little changed" (the actual live value, read from the mint below) at the default `/`
  view; the prior step 4 (the `?asof=2026-08-03` narrative-sentence check) is preserved, renumbered to
  step 7 — extended, not discarded, since it still exercises a different, still-valid code path
  (narrative sentence text vs. `state_band` badge text) with no cost to keeping both.
- `docs/handoffs/goal-market-compass-iter-30-dev.md` -- this file.

No `apps/backend/app/engine/*.py`, `apps/backend/app/api/*.py`, `apps/frontend/**/*.tsx`, or
`config.yaml` files were touched — confirmed via `git status --short apps/frontend/` (empty) and
`git status --short apps/backend/` (only the one test file). The one live database write happened
through the already-shipped regenerate endpoint, not through a code change.

## Before/After: `next_session_manifests` for `as_of=2026-08-12`

**Pre-mint** (read-only `sqlite3 "file:trendora.db?mode=ro"`, before any write this iteration):
total table row count **27**; `as_of=2026-08-12` held versions **1–6** (ids 1, 9, 10, 11, 13, 23), every
one with `state_band_json` NULL and `prospective_eligible=0` — matching the spec's stated precondition
exactly.

**Negative control** (re-verified unchanged): `POST /api/compass/regenerate?as_of=2026-08-12` **without**
`confirm=true` → HTTP 400, body `{"detail":"regenerate requires confirm=true — no row was created"}`;
row count re-checked immediately after: still **27**.

**The one authorized mint** — `2026-09-01T00:12:07Z`,
`POST /api/compass/regenerate?as_of=2026-08-12&confirm=true` → HTTP 200:

```
as_of: 2026-08-12
version: 7  (id=28)
mode: at_ingest
generation.producer: regenerate
prospective_eligible: False
content_hash: d61eee2df21d9ec2456cf3e92e2b191a603211eac7458994cdfd891e6c182d84
manifest_hash: ab3fecf87dfea069734403320104dcdb542a7e1dc7ff3e623eb4d6ef29000d8b
state_band:
  regime:   {direction_word: "little changed", delta: -0.2599999999999909}
  stress:   {direction_word: "little changed", delta: -0.17999999999999972}
  breadth:  {direction_word: "little changed", delta: 2.460000000000001}
```

All three words are real (never "NA") because `compass.delta.velocity_flat_band` (2.0),
`stress_velocity_flat_band` (5.0), and `breadth_min_change_pts` (5.0, `config.yaml:1405/1410/1411`)
each exceed the observed deltas — the config-thresholded classification correctly reads this
particular close-pair as quiet, not "improving"/"deteriorating"; that is the honest word, not a defect.

**Post-mint:** total row count **28**; `as_of=2026-08-12` row count **7** (versions 1–7).

**Export artifact:** `apps/backend/data/exports/next_session_manifests/2026-08-12_v7.json` (355,700
bytes) — `compass.verify_manifest_hash()` on the exported document returns `True` (artifact integrity
self-verifies), and its bytes are byte-for-byte identical to `json.dumps(compass.manifest_row_payload(row),
sort_keys=True, default=str)` reconstructed fresh from the stored row (confirmed via a one-off script)
— the "export bytes equal the stored payload" contract holds for this mint.

## AG-12 byte-identity re-derivation (dev lane)

`runs/goal-market-compass-iter-29/evidence/manifests-pre-mint.csv` is iter-29's own committed,
full-column CSV dump of the 26 rows that existed before ITS mint — the "iter-29-recorded state" the
plan asks this iteration's rows to match. Field-by-field comparison (not a raw-text diff, which is
noisy across re-serializations; every column value compared individually):

- **Before my mint:** all 6 `as_of=2026-08-12` rows (versions 1–6, ids 1/9/10/11/13/23) in the live DB
  matched the iter-29 baseline on all 29 columns, exactly.
- **After my mint:** the SAME 6 rows, re-read from the live DB, still matched the iter-29 baseline on
  all 29 columns, exactly — proving my regenerate call did not mutate any prior version (AG-12 holds).
- **Whole-table check (stronger than the plan strictly required):** all 26 pre-iter-29 rows (ids 1–26)
  matched the iter-29 baseline field-by-field with zero mismatches; id=27 (iter-29's own mint,
  `as_of=2026-08-03`) is still present, unchanged (`version=1`, `prospective_eligible=0`, matching the
  iter-29 audit's recorded values). Total live rows after my action: 27 pre-existing + 1 new (id=28) =
  28.
- **WAL/SHM bracketing (iter-23b lesson):** all reads used `sqlite3 "file:trendora.db?mode=ro"`, which
  reads through the live WAL snapshot (confirmed: the new row was visible immediately after the mint,
  before any checkpoint) rather than sha256-ing the bare `.db` file, which would miss WAL-resident
  writes. `trendora.db-wal` / `-shm` were present and non-trivial throughout (383,192 / 32,768 bytes) —
  consistent with WAL mode, not a sign of anything wrong.
- Evidence files: `runs/goal-market-compass-iter-30/evidence/live-2026-08-12-pre-mint.csv`,
  `live-2026-08-12-post-mint-v1-6.csv`, `live-all-post-mint.csv`,
  `iter29-baseline-2026-08-12.csv`, `authorized-mint.log`, `regenerate-2026-08-12-result.json`,
  `regenerate-no-confirm.json`, `compass-2026-08-12-pre-mint.json`.

**This is the dev lane's own re-derivation only.** Per the iter-29 auditor's B1/B2 lesson, the plan
requires this check to be repeated AFTER every lane (dev, replay, browser-qa) finishes, never
delegated to an earlier snapshot — the replay and browser-qa lanes have not yet run as of this
handoff, so whichever lane runs last in this iteration's pipeline must re-run this exact check
(`SELECT * FROM next_session_manifests WHERE as_of='2026-08-12'`, compare against this handoff's
recorded values, not just against iter-29's) before the iteration can be considered closed.

## Cross-lane `as_of` ledger (TC-7) — dev lane only

Declared safe set for NEW MINTS this iteration: exactly `{"2026-08-12"}`, via exactly one
`POST /api/compass/regenerate?as_of=2026-08-12&confirm=true` call.

**Every `as_of` value any HTTP request this dev lane issued touched:**
- `GET /api/compass?as_of=2026-08-12` (pre-mint read) — revisit, no mint (version 6 was already latest).
- `POST /api/compass/regenerate?as_of=2026-08-12` (no `confirm`) — negative control, no row created.
- `POST /api/compass/regenerate?as_of=2026-08-12&confirm=true` — **the one authorized mint** (version 7).
- No other `as_of` value was requested by this lane. Zero out-of-set requests, zero exceptions.

**New mints caused by this dev lane:** exactly one — `as_of=2026-08-12`, version 7 (id=28). No other
row was created, anywhere, by this lane.

The replay lane (deterministic golden replay for J-01/J-04/J-05/J-06/J-08/J-10/J-11, and now J-07's
updated golden) and the browser-qa lane have not run yet as of this handoff. Per the iter-29 audit's
B1 finding, whichever agent runs those lanes MUST append its own `as_of` ledger to this file (or a
follow-up report) rather than letting the dev-lane's list stand in for the whole iteration — a lane
revisiting an already-manifested date (e.g. J-04's `2026-03-30`/`2026-07-23`, J-10/J-11's
`2026-08-11`) is legitimate (not a new mint) but must still be logged, not silently absorbed.

## New Unit Test (TC-1/TC-2/TC-6 closure)

`apps/backend/tests/test_manifest_invariants.py::test_regenerate_on_frontier_yields_state_band_and_prospective_eligible_false`

Fixture `frontier_run_with_prior_and_phase`: two `ScannerRun`s (2024-07-01 regime 50.0, 2024-07-08
regime 58.0, breadth unchanged at 55.0/60.0 defaults) with a `DailyPrice` bar dated exactly at the
later run's as-of (mirrors the existing `frontier_run` fixture's at-ingest convention) and
`MarketPhaseCache` seeded for both dates (severity 25.0 → 45.0, mirrors `test_compass.py`'s
`two_runs_with_phase`) so `build_state_band` has a real severity input for every band.

The test: mints version 1 via `get_or_create_manifest(..., producer="ingest_finalize")` (asserts
`mode == "at_ingest"`, confirming the fixture IS frontier-shaped, matching the live production
scenario), then calls `regenerate_manifest(...)` to mint version 2, then asserts in the SAME call:
`generation.producer == "regenerate"`, `prospective_eligible is False` (TC-6), and `state_band_json`
deserializes to three bands each with a non-null `direction_word` drawn from
`cfg.compass.vocabulary.direction_words` and a non-null float `delta` (TC-2) — the exact combination
the 11 pre-existing `state_band` tests (which only ever exercise `build_state_band` directly or the
`ingest_finalize` path) and the pre-existing regenerate test (`test_tc23_metadata_only_regeneration...`,
which seeds no prior-run phase data, so its `state_band_json` stays the no-prior-run null shape) never
together exercised.

## Regression golden: `J-07.json`

Steps 1–3 unchanged. New steps 4–6 (inserted at the position the plan calls "step 4"):

```json
{"n": 4, "action": {"type": "goto", "url": "/"}, "expect": {"target": {"css": "[data-testid=\"compass-state-band-regime-direction\"]:has-text(\"little changed\")"}}},
{"n": 5, "action": {"type": "goto", "url": "/"}, "expect": {"target": {"css": "[data-testid=\"compass-state-band-stress-direction\"]:has-text(\"little changed\")"}}},
{"n": 6, "action": {"type": "goto", "url": "/"}, "expect": {"target": {"css": "[data-testid=\"compass-state-band-breadth-direction\"]:has-text(\"little changed\")"}}}
```

**Why `css` + `:has-text()`, not the schema's `text` key:** `demo_runner.py`'s `_check_expect` only
supports two forms — `{"text": ...}` (a page-wide, unscoped `get_by_text` substring search across the
WHOLE page) or `{"target": ...}` (mere element-existence, no text check). Since `state_band`'s word
vocabulary is the SAME shared `compass.vocabulary.direction_words` map the narrative sentence also
draws from, a page-wide text search for a word like "improving" would ALSO match the Summary card's
prose sentence even if the badge itself still read "NA" — it would not have caught the exact iter-28/29
regression this golden exists to prevent. `[data-testid="..."]:has-text("...")` is a Playwright CSS
extension (`page.locator(css_string)`, already the `"css"` target kind `_locator_for` supports
unchanged) that scopes the text check to the ONE element carrying that testid — the badge itself, not
the whole page. Verified this actually resolves specifically (not by inspection alone — see below).

Old step 4 (the `?asof=2026-08-03` narrative-sentence check) is preserved as step 7 — kept, not
dropped, since it exercises different served content (`narrative` sentence text, not `state_band`
badge text) and costs nothing to keep alongside the new checks.

**Self-verified before handoff** (this is the dev lane's own check, not the pipeline's official replay
lane, which has not run yet): started both services (backend port 8255, frontend port 3255, same ports
`start-backend.sh`/`start-frontend.sh` compute deterministically for this repo path), ran
`python3 scripts/automation/lib/demo_runner.py --mode verify --scripts-dir
runs/goal-session-market-compass/journey-scripts --journeys J-07 --backend-health-url
http://localhost:8255/api/health --base-url http://localhost:3255 ...` against the POST-MINT database
→ **`1 journey(s), 0 failed (verdict: PASS)`**. Screenshot:
`runs/goal-market-compass-iter-30/evidence/j07-self-verify/J-07-verify.png`.

**Golden written before replay (TC-9):** `J-07.json` mtime `2026-09-01T01:14:16+01:00` precedes the
self-verify screenshot's capture time `2026-09-01T01:14:56+01:00` — golden edited, then exercised, in
that order. The official pipeline replay lane (which runs J-07 again as part of this iteration's
Target-journey verification, plus J-01/J-04/J-05/J-06/J-08/J-10/J-11 as Required-still-passing) will
exercise the SAME already-committed golden — its mtime will still precede that later capture too.

`python3 scripts/automation/lib/demo_runner.py --mode lint --scripts-dir
runs/goal-session-market-compass/journey-scripts --journeys J-07` → `J-07 ok`.

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/<file>.py -v` (sequential, never
concurrent, per the resource contract)

- `tests/test_manifest_invariants.py` — **52 passed** (51 pre-existing + 1 new), 0 failed.
- `tests/test_compass.py` — **37 passed**, 0 failed (the 11 existing `state_band` tests among them,
  unchanged since iter-28, all still green).
- `tests/test_api_compass.py` — **17 passed**, 0 failed.
- `tests/test_no_magic_numbers.py` — **1 passed, 1 failed** (`test_engine_calc_code_has_no_magic_numbers`).
  Pre-existing, non-blocking, unrelated to this iteration: offenders are `indicators.py` (`0.5`,
  `0.95`), `forward_testing.py` (`45.0`, `0.5`, `0.9`), `research.py` (`0.0` ×4) — the SAME offenders
  the iter-29 audit (B3) already verified pre-date iter-28/29 (`git log -1` on those three files
  returns `0c445647`, iter-18 era). `compass.py` is in the test's `CALC_FILES` and produces zero
  offenders — this iteration touched no engine file at all, so it cannot have introduced or worsened
  this failure. OUT OF SCOPE per the phase spec: "editing three engine modules would be scope creep."

Frontend: no code changed, so no `npm run build` re-verification was needed; confirmed via
`git status --short apps/frontend/` (empty) that nothing there changed.

## Known Issues

1. **TC-5's whole-iteration AG-12 re-derivation is not fully closeable by this agent.** This handoff
   closes it for the dev lane only (see "AG-12 byte-identity re-derivation" above, both before AND
   after my own mint, plus a whole-table 26/26 check). Per the plan's explicit instruction, whichever
   lane runs LAST in this iteration (replay or browser-qa) must re-run the SAME check one more time
   against the truly-final database state and record it — mirroring exactly how the iter-29 auditor
   closed this same gap after both the dev and replay lanes had finished (B2).
2. **TC-7's cross-lane ledger is dev-lane-only in this handoff.** The replay lane (J-01/J-04/J-05/J-06/
   J-08/J-10/J-11 plus J-07's updated golden) and the browser-qa lane have not run as of this writing.
   Whoever runs them must record which `as_of` values they visited (even harmless revisits) rather than
   letting this handoff's list stand in for the whole iteration — this is the exact process the iter-29
   audit had to retroactively fix (B1) after the dev handoff's list was treated as complete when it
   was dev-lane-only.
3. **`test_no_magic_numbers.py`'s pre-existing red is carried forward, unfixed** (documented above,
   explicitly out of scope this iteration per the phase spec).
4. **`J-07`'s new steps 4–6 all currently assert the SAME word ("little changed") for all three bands**
   — an artifact of `2026-08-11`→`2026-08-12` genuinely being a quiet pair of sessions (all three
   deltas fall below their respective flat-band thresholds), not a golden-authoring shortcut. A future
   iteration mint on a more eventful close-pair would produce different words per band; this golden
   will need re-deriving (not just re-running) whenever `as_of=2026-08-12`'s manifest is superseded by
   a NEWER frontier date becoming the default landing view, since AG-12 forbids ever mutating this
   specific version-7 row's content.
