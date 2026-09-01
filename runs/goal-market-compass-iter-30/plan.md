# goal-market-compass-iter-30 Execution Plan

## What to Build
- Issue exactly ONE authorized live call, `POST /api/compass/regenerate?as_of=2026-08-12&confirm=true`,
  against the running canonical backend. This mints `next_session_manifests` version 7 for
  `as_of=2026-08-12` (the frontier / default-landing date) via the existing `regenerate_manifest`
  (`apps/backend/app/engine/compass.py:1185`), which calls the SAME `_freeze_manifest` writer as
  `build_manifest_payload` / `build_state_band` — so version 7 carries a non-null `state_band_json`
  (real words + deltas for regime/stress/breadth) and `prospective_eligible: false` (producer
  `"regenerate"` fails `_derive_prospective_eligible`'s `producer == "ingest_finalize"` check).
- Zero code change to `build_state_band`, `_severity_at`, `compass.vocabulary.direction_words`,
  `build_manifest_payload`, or `_derive_prospective_eligible` (binding "Do not redo" — same functions
  iter-28/iter-29 already proved correct on other dates).
- Add ONE new fixture-scoped unit test, isolated DB, asserting a regenerated version on a
  frontier-shaped as-of yields BOTH `state_band` populated with real words AND
  `prospective_eligible: false` from the same call (closes the auditor's iter-29 T1 gap: the 11
  existing `state_band` tests never exercised the regenerate path together with state_band). Natural
  location: `apps/backend/tests/test_manifest_invariants.py`, near the existing
  `regenerate_manifest` coverage at line ~825 — developer's call if `test_compass.py` fits better.
- Update `runs/goal-session-market-compass/journey-scripts/J-07.json`'s regression golden BEFORE the
  replay lane runs: assert the three `compass-state-band-{regime,stress,breadth}-direction` testids'
  rendered text at the default `/` view (no `asof` param). Today's step 4 asserts a `narrative`
  sentence at `?asof=2026-08-03`, which is NOT wired to `state_band` and gives the direction badges no
  durable regression guard (iter-29 audit finding T1). Confirmed testids already exist verbatim in
  `apps/frontend/components/compass-state-band-card.tsx` (lines 84/115/141) — no frontend change
  needed to make them assertable.
- Re-derive, AFTER every lane in this iteration finishes (dev, replay, browser-qa — never from an
  earlier snapshot): `as_of=2026-08-12` row count (must be 7, up from 6) and versions 1–6's complete
  column values (`id`, `content_hash`, `manifest_hash`, `prospective_eligible`, `available_at_utc`,
  every other column) byte-identical to their iter-29-recorded state — checked against the `.db` file
  AND any `-wal`/`-shm` sibling (iter-23b lesson; iter-29 already set the byte-identity precedent for
  this exact style of check).
- Re-run targeted, sequential (never concurrent) pytest: `test_manifest_invariants.py`, the 11 existing
  `state_band` tests in `test_compass.py`/`test_api_compass.py` (unchanged since iter-28), the new
  regenerate+state_band test, and `test_no_magic_numbers.py` (expect the SAME pre-existing red on
  `indicators.py`/`forward_testing.py`/`research.py` — carried, non-blocking, do not fix).
- Frontend: NO code changes. `apps/frontend/components/compass-state-band-card.tsx` already renders
  `state_band?.<band>.direction_word ?? "NA"` verbatim with no client-side word selection — once
  version 7 exists, loading `/` with no `asof` param will show real words instead of "NA" with zero
  frontend edits. Browser-qa lane verifies this live.
- Dev handoff at `docs/handoffs/goal-market-compass-iter-30-dev.md` citing exact before/after row
  counts and column values for `as_of=2026-08-12`, and — learning directly from the iter-29 audit's B1
  finding — the COMPLETE cross-lane ledger of every `as_of` value any lane (dev, replay, browser-qa)
  actually caused a NEW mint on. The declared safe set for NEW MINTS this iteration is exactly
  `{"2026-08-12"}` via the one regenerate call; replay/browser-qa may legitimately VISIT other
  already-manifested dates (revisiting is not minting) but must not cause a new row anywhere else — if
  one does, flag it explicitly in the handoff, do not silently absorb it (this is the exact gap the
  iter-29 auditor had to fix after the fact).

## Agents Required
- backend-data: yes -- issue the one authorized `POST /api/compass/regenerate` call; write and run the
  new regenerate+state_band unit test; update the `J-07.json` golden BEFORE replay runs; re-derive
  AG-12 byte-identity and row counts after every lane; re-run the targeted test suites; write the dev
  handoff with the complete cross-lane `as_of` ledger.
- frontend-ux: no -- binding "Do not redo": no code change is authorized to
  `compass-state-band-card.tsx` or any other frontend file this iteration. Verification that `/` (no
  `asof`) now renders real words is a browser-qa/regression-replay concern, not a frontend build lane.

## Frontend Present: yes

## Files to Create/Modify
- `apps/backend/tests/test_manifest_invariants.py` (or `test_compass.py`) -- add the new
  regenerate+state_band+prospective_eligible unit test (fixture-scoped, isolated DB).
- `runs/goal-session-market-compass/journey-scripts/J-07.json` -- replace/extend step 4 to assert the
  three `compass-state-band-*-direction` testids' text at the default `/` view (no `asof`); do this
  BEFORE the replay lane executes.
- `docs/handoffs/goal-market-compass-iter-30-dev.md` -- new dev handoff (before/after row counts,
  column values, complete `as_of` ledger, test results).
- No `apps/backend/app/engine/*.py`, `apps/backend/app/api/*.py`, `apps/frontend/**/*.tsx`, or
  `config.yaml` edits are in scope. The one live database write (via the regenerate endpoint) is a
  data change, not a code change.

## UI Evolution
- New user-facing capability: on the DEFAULT landing view (`/`, no `asof` param — the page every user
  actually lands on first), the three market-state direction badges (regime, stress, breadth) now show
  real words ("improving" / "deteriorating" / "little changed") instead of "NA", removing the
  contradiction where the Summary card one line below already stated a real session-over-session
  comparison. This closes J-07's last gap.
- New information displayed: none new — `state_band` has existed and rendered correctly on other
  dates since iter-28/29; this iteration only makes it observable on the frontier/default date.
- New user actions: none.
- UI surface changes: none — same `/` page, same components, no new page/panel/card.
- Navigation changes: none.

## Visual Requirements
- Component patterns: none new — reuses the existing `Badge` (`compass-state-band-card.tsx`'s
  `DirectionBadge`) already wired to render `state_band.<band>.direction_word ?? "NA"`.
- Layout: unchanged — existing Today (`/`) page, market-state band section at the top of the body.
- Key visual effects: none new.
- States to handle: already implemented and already tested (11 existing tests) — null/`NA` badge when
  `state_band` is absent, real word when present; no new state to add this iteration.

## Key Test Scenarios
- TC-1/TC-2 (backend): after the one `POST /api/compass/regenerate?as_of=2026-08-12&confirm=true`
  call, `next_session_manifests` holds exactly 28 rows total, with a new `as_of=2026-08-12, version=7`
  row whose `state_band_json` is non-null with three real `direction_word`/`delta` pairs.
- TC-3/TC-4 (browser-qa): `/` with no `asof` param shows all three direction badges as real words
  (never "NA"), byte-identical to `GET /api/compass`'s `state_band` field, and consistent with the
  Summary card's stated comparison on the same screen — the exact contradiction iter-28/29 evaluators
  flagged must not recur on the default view.
- TC-5 (AG-12): versions 1–6 of the `as_of=2026-08-12` manifest are byte-identical to their
  iter-29-recorded state, re-checked AFTER every lane finishes, against `.db` + `-wal`/`-shm`.
- TC-6 (AG-17): version 7's `prospective_eligible` is `false` (producer `"regenerate"`, not
  `"ingest_finalize"`) — proven by the new unit test in the SAME call that populates `state_band`.
- TC-7 (process control): the only `as_of` value any lane causes a NEW mint on this iteration is
  `2026-08-12`; any other new-mint event anywhere is a flagged process violation, not silently absorbed
  (directly incorporates the iter-29 auditor's B1 lesson).
- TC-8 (regression): deterministic replay for J-01, J-04, J-05, J-06, J-08, J-10, J-11 all PASS and
  mint zero additional manifest rows beyond the one TC-1 mint.
- TC-9 (golden coverage): the updated `J-07.json` golden PASSES against the post-mint database, and its
  mtime precedes the corresponding `J-07-verify.png` capture (golden written before replay, not after —
  iter-29b lesson).
- TC-10 (unit suite): `test_manifest_invariants.py`, the 11 existing `state_band` tests, and the new
  TC-6 test all pass with zero failures/skips beyond the documented `TRENDORA_MEMORY_PRESSURE` opt-in
  skip; `test_no_magic_numbers.py`'s pre-existing red (unrelated files, carried since before iter-28)
  is expected and non-blocking.

## Notes / Risks
- This is an operational-plus-test iteration, not a feature iteration: the only production-code-path
  exercised is an already-shipped, already-proven action endpoint (`POST /api/compass/regenerate`,
  shipped iter-3, proven live on `2025-04-15` at iter-26). The only NEW artifacts are one unit test and
  one golden-script update.
- iter-29's audit (B1) found that the cross-lane `as_of` ledger was assembled by only the dev lane and
  missed 3 out-of-set replay visits (harmlessly, since they were revisits not mints). This plan bakes
  the full ledger requirement into the dev handoff explicitly so it is not deferred to the auditor
  again.
- Services: start via `bash scripts/start-backend.sh` / `bash scripts/start-frontend.sh` only (HOST-GUARD
  caps); never run the full pytest suite; run test files sequentially, never concurrently
  (AG-10 / project-template.md resource contract). Shut down both process trees before handoff, per
  iter-29's precedent (uvicorn PID exits on parent kill; `next start`'s child chain needs an explicit
  kill).
