# goal-market-compass-iter-29 Execution Plan

## What to Build

This iteration ships **zero new code**. All production code for `state_band` (backend producer,
route wiring, schema, frontend card) already exists complete and correct in the working tree from
iter-28 (verified: `build_state_band`, `state_band_json` column, `_ADDITIVE_COLUMNS` ALTER,
`compass-state-band-card.tsx`, `compass-leadership-rotation-section.tsx` are all present and
uncommitted — iter-28 never got a git commit). iter-28's gap was purely observational: every
authorized live `as_of` already had a manifest row, so `state_band_json` was always `null` in every
live check. This iteration closes that gap with ONE operational action plus verification:

- Start backend + frontend via the project's canonical start scripts (nothing currently listening on
  8000/3000).
- Issue exactly ONE live request: `GET /api/compass?as_of=2026-08-03`. This date is confirmed
  manifest-less right now (`next_session_manifests` has 26 rows total, zero with `as_of=2026-08-03`;
  the nearest neighbor `2026-08-12` alone already carries 6 versions). Because `2026-08-03` is NOT the
  stored frontier (`2026-08-12` is), `GET /api/compass` for it takes the retrospective create-once path
  (`apps/backend/app/api/compass.py`) — it mints exactly one new `version=1` row, never a second one on
  repeat.
- No other `as_of` value may be requested by ANY lane (dev, replay, browser-qa) this iteration — the
  declared safe set is exactly `{no param (Latest), "2026-08-12", "2025-04-15", "2026-08-03"}`. Log
  every `as_of` value actually requested by every lane verbatim in the dev handoff (TC-6).
- Verify directly against the DB / API (read-only) that the new row's `state_band_json` is non-null
  and deserializes to three bands (`regime`, `stress`, `breadth`), each with a `direction_word` from
  `compass.vocabulary.direction_words` and a float-or-null `delta` (TC-1, TC-2).
- AFTER every lane in this iteration finishes (dev, replay, browser-qa — never an earlier snapshot),
  re-derive: (a) the full table row count (must be 27), and (b) the 26 pre-existing rows' complete
  column values, byte-identical to their iter-28-recorded state (TC-5, AG-12).
- Re-run `test_manifest_invariants.py` and the existing 11-test `state_band` route/fixture suite
  (`test_compass.py` + `test_api_compass.py`, unchanged since iter-28) against the post-mint database
  — must stay green with zero new failures/skips beyond the documented `TRENDORA_MEMORY_PRESSURE`
  opt-in skips (TC-8).
- Browser-qa verifies (no code change needed — component already built): loading `/?asof=2026-08-03`
  renders all three direction badges as real words (never "NA"), byte-identical to
  `GET /api/compass?as_of=2026-08-03`'s `state_band` field (TC-3), and that the regime badge word is
  consistent with the Summary card's regime-direction sentence on the same screen (TC-4 — the exact
  iter-28 finding must not recur).
- Deterministic replay covers the widened Required-still-passing set (J-01, J-04, J-05, J-06, J-08,
  J-10, J-11) and must mint zero additional manifest rows beyond the one TC-1 row (TC-7).
- Write `docs/handoffs/goal-market-compass-iter-29-dev.md` citing: the exact `as_of` used, the
  before/after row count (26 → 27), the byte-identity re-check result for the 26 pre-existing rows, and
  every `as_of` value any lane actually requested.

## Agents Required

- backend-data: yes -- perform the one authorized `GET /api/compass?as_of=2026-08-03` against the
  running canonical backend, verify the new row's `state_band_json` content and the 27-row count,
  re-run `test_manifest_invariants.py` + the 11 `state_band` tests post-mint, re-derive byte-identity
  on the 26 pre-existing rows AFTER every lane finishes, and write the dev handoff. No code edits are
  in scope — this is a verification/operational action, not an implementation task. If any check
  reveals the working tree has drifted from iter-28's described state (e.g. `build_state_band` missing
  or altered), STOP and surface it rather than silently re-implementing (binding "Do not redo" on
  `build_state_band`, `_severity_at`, and the vocabulary map).
- frontend-ux: no -- zero frontend code changes this iteration (binding "Do not redo" on
  `compass-state-band-card.tsx`). Only observation of the already-shipped component is required, done
  by the browser-qa lane, not a frontend implementation agent.

## Frontend Present: yes

## Files to Create/Modify

- `docs/handoffs/goal-market-compass-iter-29-dev.md` -- new dev handoff (the only new file this
  iteration produces).
- No other file should change. Explicitly OUT OF SCOPE for edits: `apps/backend/app/engine/compass.py`
  (`build_state_band`, `_severity_at`), `compass.vocabulary.direction_words` in `config.yaml`,
  `apps/frontend/components/compass-state-band-card.tsx`, and any other file already modified/added by
  iter-28's uncommitted work — that work should be left exactly as-is, only exercised.

## UI Evolution

- New user-facing capability: on the one now-frozen date `2026-08-03`, the Today page's three
  direction badges (regime, stress, breadth) show real words ("improving" / "deteriorating" / "little
  changed") instead of "NA" for the first time — the ten-second read J-07 promised becomes observable
  on real data.
- New information displayed: none new — the field and its rendering already shipped in iter-28; this
  iteration only makes the non-NA case observable.
- New user actions: none.
- UI surface changes: none — same `/` page, same components as iter-28, no new page/panel/card.
- Navigation changes: none.

## Visual Requirements

- Component patterns: none to build — reuse `compass-state-band-card.tsx` exactly as iter-28 shipped
  it (regime tile, phase tile, breadth line, each with a direction badge and breakdown disclosure).
- Layout: unchanged Today page body order (state band → summary → what-changed → leadership rotation →
  next-session focus → manifest strip).
- Key visual effects: none new.
- States to handle: confirm the previously-only-observable "NA" badge state still renders correctly
  elsewhere (e.g. any band with a null input), while `2026-08-03`'s bands show the happy-path real-word
  state — both must coexist correctly, nothing regressed.

## Key Test Scenarios

- TC-1/TC-2 (backend): the single `GET /api/compass?as_of=2026-08-03` produces exactly one new
  `version=1` row; its `state_band_json` is non-null with three well-formed bands.
- TC-3/TC-4 (browser-qa, J-07 step 3): `/?asof=2026-08-03` renders all three badges as real words, none
  reading "NA"; the regime badge and the Summary card's regime-direction sentence agree.
- TC-5 (AG-12, re-derived post-ALL-lanes): 26 pre-existing rows byte-identical to iter-28-recorded
  state; table has exactly 27 rows.
- TC-6 (process): every `as_of` any lane requested this iteration is a subset of `{no param, "2026-08-12",
  "2025-04-15", "2026-08-03"}` — zero exceptions, logged verbatim in the dev handoff.
- TC-7 (replay): J-01, J-04, J-05, J-06, J-08, J-10, J-11 all PASS and mint zero rows beyond TC-1's one.
- TC-8 (unit): `test_manifest_invariants.py` + the 11 `state_band` tests pass post-mint with zero new
  failures/skips.
- Full J-07 walkthrough (all 7 steps) passes live via browser-qa, with step 3 as the focal, previously-
  failing assertion.
