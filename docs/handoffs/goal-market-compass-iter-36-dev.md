# goal-market-compass-iter-36 Dev Handoff

**Phase:** goal-market-compass-iter-36
**Date:** 2026-09-01
**Agent:** developer
**Status:** complete

## What Was Built

J-13 — the Leadership rotation section now serves its own `session_delta.rotation` block (two labelled,
signed, both-directions sides per group kind — sector, theme) instead of re-rendering a client-side
`kind ∈ {sector,theme,stock}` filter of the What-changed list, and the accounting no longer silently
drops above-threshold movers beyond the display cap.

- `app.engine.session_delta`: `_sector_changes`/`_theme_changes` refactored into two public,
  DB-querying pair builders — `sector_rank_pairs(session, current, previous, config)` and
  `theme_rank_pairs(...)` — that return EVERY comparable sector/theme rank pair (uncapped, no
  `rank_move_min` gate applied yet), each entry carrying a NEW signed `delta` (`cur_rank - prev_rank`)
  alongside the existing `magnitude`/`from`/`to`/`drill_href` shape. `compute_delta` now accepts optional
  `sector_pairs`/`theme_pairs` kwargs — when a caller (namely `build_manifest_payload`) already computed
  them, they are reused verbatim (object identity preserved into `session_delta.changes`) instead of a
  second DB query; omitted, the old internal-computation behavior is unchanged (backward compatible for
  every other caller/test).
- `app.engine.compass`: new `build_rotation(previous_run, sector_pairs, theme_pairs, cfg)` builds the
  `session_delta.rotation.{sector,theme}` block from the SAME pairs `build_manifest_payload` passes to
  `compute_delta` — two labelled sides (`gaining` = improving/rank fell, `losing` = deteriorating/rank
  rose), each capped by the new `compass.delta.rotation_top_k`, each entry still gated by the existing
  `compass.delta.rank_move_min`, plus a per-kind accounting object (`shown_count`, `suppressed_count`,
  `residual_count`, `configured_total`) whose four values sum exactly to the configured group count (31
  sector/industry = `len(config.etfs.sector) + len(config.etfs.industry)`, 11 theme =
  `len(config.themes)`). An above-threshold pair beyond the cap lands in `residual_count` — never dropped
  uncounted, the exact defect measured in the BACKGROUND (previously 29/31 for sector; now closes to
  31/31). No stock-kind row anywhere in `rotation` (group-level only, by construction — rotation rows
  carry no `kind` field at all). Direction word reuses the EXISTING `_flat_band_word`/
  `compass.vocabulary.direction_words` classifier (`_rank_direction_word`, `compass.py`) — polarity
  resolved by negating the rank delta before classifying, mirroring the `state_band.stress` sign-transform
  precedent; `flat_band` reuses `compass.delta.rank_move_min` itself (every displayed row already cleared
  that gate, so the word is never "flat" — no new/retuned threshold, AG-15). A NEW
  `_attach_rank_direction_words` mutates sector/theme-kind entries of `session_delta.changes` in place,
  adding the SAME `direction_word` their rotation-row counterpart carries (the `delta` field already rides
  those entries via `session_delta.py`'s `_entry` — single computation, two placements).
  `build_manifest_payload` computes `sector_pairs`/`theme_pairs` ONCE (only when `previous_run` exists),
  passes them into both `compute_delta` and `build_rotation`, and sets `delta["rotation"] = build_rotation(...)`
  before assembling `content` — `session_delta.rotation` therefore rides the SAME `session_delta_json`
  storage column every other `session_delta` field already uses; NO new DB column, NO schema/model change.
- `config.yaml` / `app.config`: new `compass.delta.rotation_top_k` (value `5`, matching the existing
  "top 5" convention) under the existing `compass.delta` block; `CompassDeltaCfg` gained the typed field
  + a `> 0` validator; `_default_compass()`'s built-in default kept in sync. No existing `compass.delta.*`
  threshold VALUE was changed (AG-15).
- `apps/frontend/lib/api.ts`: `SessionDeltaChange` gained optional `delta?`/`direction_word?` (sector/theme
  kind only, documented as such); new `CompassRotationRow`/`CompassRotationKind`/`CompassRotation` types;
  `SessionDelta.rotation` — CORRECTED in the fix round below to `rotation?: CompassRotation` (OPTIONAL):
  every manifest built by this iteration's code populates it, but rows minted BEFORE this iteration are
  served verbatim without the key, so the field is optional on the wire (see Fix Notes).
- `apps/frontend/components/compass-leadership-rotation-section.tsx`: full rewrite. Renders
  `session_delta.rotation.{sector,theme}` directly — two labelled sides (`Gaining`/`Losing`) per kind,
  most-moved-first, signed `+N`/`-N` delta text plus the served `direction_word`, each side's own honest
  empty-state string when that side is empty (e.g. "No sector lost ground beyond the threshold this
  session"), and a per-kind accounting line ("N of M shown · N below threshold · N beyond the display
  cap."). The top-level no-prior-run state (`session_delta.prior_as_of === null`) renders one message for
  the whole section, matching the What-changed card's own no-prior wording. The component selects no word,
  computes no sign, and applies no threshold — every value is a served field, re-formatted only.
  `apps/frontend/components/compass-whatchanged-card.tsx` was NOT touched at all (`git diff` on that file
  is empty) — same entries, same order, same thresholds, same suppressed count, per the spec's explicit
  requirement.

## TC-11 diff citation (removed client-side filter logic)

The prior implementation's client-side selection logic, now removed:

```tsx
const ROTATION_KINDS: readonly SessionDeltaChange["kind"][] = ["sector", "theme", "stock"];
...
const entries = compass.session_delta.changes.filter((change) => ROTATION_KINDS.includes(change.kind));
```

was at `apps/frontend/components/compass-leadership-rotation-section.tsx:10` and `:38` on the pre-iter-36
version of the file. The rewrite reads `compass.session_delta.rotation.sector` / `.theme` directly — no
`.filter(...)` over `session_delta.changes` exists anywhere in the new file.

## J-13 step 8 fixture citations

- **Empty-losing-side fixture**: `all_gainers_sector_run_pair`
  (`apps/backend/tests/test_compass.py:841`) — every threshold-crossing sector mover is a gainer (XLK
  5→1, XLE 4→2), plus one suppressed row (XLF 3→3). Exercised by
  `test_rotation_empty_losing_side_when_every_mover_is_a_gainer`
  (`apps/backend/tests/test_compass.py:941`), which asserts `sector["losing"] == []` while `gaining`
  carries both movers unaffected, and the suppressed row is distinct from the empty-losing state.
- **Above-threshold-but-capped fixture**: `full_universe_rotation_runs`
  (`apps/backend/tests/test_compass.py:861`) — the FULL configured sector/industry (31) and theme (11)
  universe on both runs, ranks reversed between runs (`prev = N + 1 - cur`), which for the real config
  (`rank_move_min` 2, `rotation_top_k` 5) yields exactly one exact-middle delta-0 pair per kind (fails
  `rank_move_min` outright — suppressed) and 15 (sector) / 5 (theme) above-threshold movers per side.
  Exercised by `test_rotation_full_universe_closure_and_residual_isolation`
  (`apps/backend/tests/test_compass.py:1018`), which asserts sector `residual_count == 20` (10 gainers +
  10 losers cleared `rank_move_min` but are excluded SOLELY by `rotation_top_k`, isolated from the single
  middle row that fails the threshold outright) and the full `shown_count + suppressed_count +
  residual_count == configured_total` closure for both kinds — reproducing this iteration's own measured
  gap (previously 29/31 for sector) as exactly 31/31 and 11/11.

## Files Changed
- `apps/backend/app/engine/session_delta.py` -- public `sector_rank_pairs`/`theme_rank_pairs`, signed
  `delta` on sector/theme entries, `compute_delta` accepts optional precomputed pairs.
- `apps/backend/app/engine/compass.py` -- `build_rotation` + `_rotation_kind`/`_rotation_row`/
  `_rank_direction_word`/`_attach_rank_direction_words`; wired into `build_manifest_payload`.
- `apps/backend/app/config.py` -- `CompassDeltaCfg.rotation_top_k` (+ validator, + default).
- `config.yaml` -- `compass.delta.rotation_top_k: 5`.
- `apps/backend/tests/test_session_delta.py` -- 5 new tests (signed delta, full pair builders,
  precomputed-pairs reuse, backward-compat default).
- `apps/backend/tests/test_compass.py` -- 3 new fixtures (`rotation_run_pair`,
  `all_gainers_sector_run_pair`, `full_universe_rotation_runs`) + 11 new tests (TC-1 through TC-9,
  AG-11, config-driven cap).
- `apps/backend/tests/test_manifest_invariants.py` -- 1 new fixture (`frontier_run_with_rotation`) + 2 new
  tests (TC-12 schema validation with rotation populated; legacy pre-iter-36 row honest-absence proof).
- `apps/backend/tests/test_api_compass.py` -- extended the existing "serves every new field directly"
  test with rotation-block assertions.
- `apps/frontend/lib/api.ts` -- `CompassRotationRow`/`CompassRotationKind`/`CompassRotation` types,
  `SessionDelta.rotation`, `SessionDeltaChange.delta`/`.direction_word`.
- `apps/frontend/components/compass-leadership-rotation-section.tsx` -- full rewrite (served rotation
  block, no client-side filter/threshold/word logic).

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/<file>.py -v` (targeted, per-file, per
project-template.md)

- `test_session_delta.py`: 17 passed
- `test_compass.py`: 50 passed
- `test_manifest_invariants.py`: 55 passed
- `test_api_compass.py`: 18 passed
- `test_no_magic_numbers.py`: 1 pre-existing failure, unrelated to this iteration (see Known Issues)
- `test_config.py` + `test_config_engine.py` (config-shape regression check): 125 passed

Frontend: `cd apps/frontend && NEXT_DIST_DIR=.next-verify NEXT_PUBLIC_API_URL=http://localhost:8000 npx next build`
— compiled successfully, typecheck passed, 30/30 static pages generated. Throwaway `.next-verify` dir
removed after the check (never committed). `npm run lint` could not run — see Known Issues (pre-existing,
unrelated).

## Live production verification

Started backend (`scripts/start-backend.sh`, port 8255) and frontend (`scripts/start-frontend.sh`, port
3255) against the live 30-year seed database, both host-guard capped, both started cleanly with no
errors.

1. Confirmed AG-12 directly on the live DB (read-only query): the frontier's (`as_of=2026-08-12`) 8
   pre-existing `next_session_manifests` rows (versions 1-8) all serve `session_delta` WITHOUT a
   `rotation` key at all (pre-iter-36 shape, honestly absent — never fabricated), and each row's stored
   `content_hash`/`manifest_hash` is exactly what was already on disk before this session's code ran.
2. Minted version 9 via `POST /api/compass/regenerate?as_of=2026-08-12&confirm=true` (the frontier's own
   as-of — never a hand-picked historical date, per the iter-29 trap this spec's NOTES cite). Verified:
   - `session_delta.rotation.sector`: `gaining` 5, `losing` 2, `shown_count` 7, `suppressed_count` 24,
     `residual_count` 0 — sums to 31 (the full `config.etfs.sector` 11 + `config.etfs.industry` 20).
   - `session_delta.rotation.theme`: `gaining` 1, `losing` 1, `shown_count` 2, `suppressed_count` 9,
     `residual_count` 0 — sums to 11 (`config.themes`).
   - `session_delta.changes` sector/theme entries carry the SAME `delta`/`direction_word` as their
     rotation-row counterpart (e.g. "Home Construction (iShares)" 21→25, `delta: 4`,
     `direction_word: "deteriorating"` in both places).
   - Document validates against `docs/handoffs/trendora-next-session-manifest-v1.schema.json`;
     `compass.manifest.schema_version` unchanged (`v1`).
   - Export file `apps/backend/data/exports/next_session_manifests/2026-08-12_v9.json` written (bytes
     equal the served/stored payload, per the existing export-writer contract this iteration did not
     touch).
3. Browser-driven check (Chrome DevTools Protocol) of the DEFAULT `/` view (no `?asof`): the Leadership
   rotation section renders "Regional Banks (SPDR) 13 → 10 (-3) · improving" and "Home Construction
   (iShares) 21 → 25 (+4) · deteriorating" side by side, correctly disambiguated (the exact pair goal.md's
   own BACKGROUND cited as visually identical under the old unsigned `magnitude`). Accounting line reads
   "7 of 31 shown · 24 below threshold · 0 beyond the display cap." for sector, "2 of 11 shown · 9 below
   threshold · 0 beyond the display cap." for theme. The What-changed card above it renders unchanged (17
   entries, market→breadth→sectors→themes→stocks order, "Suppressed moves (36)" disclosure).
4. Stepped the as-of switcher to the earliest stored run (`1996-02-01`): the rotation section renders "This
   is the earliest stored session — there is no prior session to compare rotation against." — the honest
   no-prior-run state, no fabricated rows.
5. Stopped the frontend mid-session and restarted it via `scripts/start-frontend.sh` again — confirmed
   `session_delta.rotation` still present after the restart (see Known Issues for a script gap found
   during this step, unrelated to this iteration's product code).

Both services were killed before finishing (`pkill -f uvicorn`, explicit PID kill of the `next-server`
child — see Known Issues).

## Known Issues

- **Pre-existing, unrelated, explicitly carried out of scope** (iter spec NOTES): `test_no_magic_numbers.py`
  fails on `indicators.py`/`forward_testing.py`/`research.py` float literals — none of those files were
  touched this iteration; `session_delta.py`/`compass.py` (the two files this iteration DID touch) are
  clean.
- **`scripts/start-frontend.sh` does not reliably kill a lingering `next-server` child on re-invocation**:
  re-running the script while a previous frontend instance was still up threw `EADDRINUSE` on port 3255 —
  the parent `npm exec`/`sh -c next start` processes were gone but the `next-server` grandchild survived
  and kept holding the port. I killed it by explicit PID (`kill -9`) and the script then started cleanly.
  This is a pre-existing script gap (I did not touch `scripts/start-frontend.sh`), matching the developer
  agent's own pre-handoff checklist note about verifying child-process handling — flagging it here rather
  than silently working around it every time, since it will bite any future agent that re-invokes the
  script without first confirming the port is actually free.
- `npm run lint` could not be exercised: this frontend has no committed ESLint config, so `next lint`
  drops into an interactive first-run setup prompt (`next.config.mjs`'s own build guard also refuses a
  build into the live `.next` dir without `NEXT_PUBLIC_API_URL`, which I worked around with the
  documented `NEXT_DIST_DIR=.next-verify` throwaway-dir pattern for the build/typecheck check). Both are
  pre-existing environment gaps, not something this iteration's scope covers.
- `rotation_top_k` was set to `5` (the same value as the existing `top_k`), matching the "mirrors the
  existing Top-Sectors/Top-Themes 'top 5' convention" language in the iter spec's IN SCOPE section — this
  is a display-cap CHOICE within the developer's discretion (not a threshold value carried over from
  research/outcomes, AG-15-safe), not something the spec pinned to a specific number.
- The live sector/theme data for the frontier date (2026-08-12) happened to have `residual_count == 0` on
  both kinds (every above-threshold mover fit within the cap) — the `residual_count > 0` disclosure path
  is proven correct by the synthetic `full_universe_rotation_runs` fixture (see the J-13 step 8 citation
  above), not by live data, since production data does not currently exercise that branch.

---

## Fix Notes (round 2 — review FAIL, `reports/reviews/goal-market-compass-iter-36-review.md`)

Both listed issues fixed; nothing else touched. The reviewer's CRITICAL was correct and my first-round
live verification did miss it: I exercised only the freshly-regenerated frontier (v9, has `rotation`) and
the one date with `prior_as_of === null` — the exact two cases that avoid the crash.

### CRITICAL — unguarded `session_delta.rotation` deref crashed the Today page on as-of navigation

Re-confirmed the reviewer's finding independently, first read-only against the live DB
(`apps/backend/data/trendora.db`, `next_session_manifests`): 18 distinct stored as-of dates, and every
one except the frontier's v9 stores a `session_delta` blob with NO `rotation` key while carrying a
NON-NULL `prior_as_of` (e.g. `2026-08-11` v3 → `prior_as_of: "2026-08-10"`, no `rotation`). Then live
through the route itself: `GET /api/compass?as_of=2026-08-11` on the running backend returns
`prior_as_of: "2026-08-10"`, `"rotation" in session_delta == False`, 17 `changes` — the exact shape the
old component dereferenced unguarded.

Two fixes:

1. `apps/frontend/lib/api.ts` — `SessionDelta.rotation` is now `rotation?: CompassRotation` (was
   required), with a comment stating why (the key is added INSIDE the existing `session_delta` blob and
   a frozen row is never backfilled — AG-12 — so `manifest_row_payload` serves legacy rows without it).
   `CompassRotation`'s own doc comment now names this as a THIRD state, distinct from both no-prior-run
   and an empty side.
2. `apps/frontend/components/compass-leadership-rotation-section.tsx` — explicit third branch. The
   component reads `const rotation = session_delta.rotation ?? null;` (nullish-coalesced, so a `null` on
   the wire degrades identically to an absent key — same posture as `compass?.state_band ?? null` in
   `compass-state-band-card.tsx`) and renders, in order: no-prior-run (`prior_as_of === null`) →
   rotation-absent (`rotation === null`, `data-testid="compass-leadership-rotation-not-recorded"`) →
   the served block. The new placeholder text is deliberately DISTINCT from the no-prior-run message and
   honest about why nothing is shown: "Rotation detail was not recorded for this session — its stored
   manifest predates this section, and a frozen manifest is never rewritten, so nothing is shown here
   rather than recomputed. The What changed card above still lists this session's moves."

### MINOR — covering test for the legacy (rotation-absent) response shape

This frontend has no component-test runner (no jest/vitest/testing-library in
`apps/frontend/package.json`), and `.claude/project-template.md` defines the frontend test as the
production compile + typecheck — adding a test framework would be scope creep this iteration cannot
justify. The path is therefore covered two ways, both actually executable here:

- **Type-enforced at the frontend's own sanctioned test layer.** With `rotation?:`, the previously
  crashing code is now a compile error, so the guard cannot be silently removed again. Proven by
  temporarily reverting the guard and re-running the typecheck:

  ```
  components/compass-leadership-rotation-section.tsx(131,53): error TS18048: 'session_delta.rotation' is possibly 'undefined'.
  components/compass-leadership-rotation-section.tsx(132,52): error TS18048: 'session_delta.rotation' is possibly 'undefined'.
  ```

  (guard restored immediately; `npx tsc --noEmit` exits 0 with the guard in place).
- **A runnable route-layer test for the exact served shape**:
  `test_compass_route_serves_legacy_pre_iter36_row_without_rotation_key`
  (`apps/backend/tests/test_api_compass.py:141`) freezes a manifest, strips the `rotation` key from the
  stored `session_delta_json` (byte-for-byte the shape of every pre-iter-36 row), and asserts that
  `GET /api/compass` then serves `prior_as_of == "2024-06-01"` (a REAL prior session — not the
  no-prior-run state) together with an absent `rotation`, while every other `session_delta` key is
  unchanged. This is asserted at the ROUTE layer, not just `manifest_row_payload` — the existing
  `test_rotation_absent_key_on_legacy_pre_iter36_row_never_fabricated`
  (`apps/backend/tests/test_manifest_invariants.py:1135`) stops one layer short of what the frontend
  actually consumes.

### Fix-round tests run

- `cd apps/backend && .venv/bin/python -m pytest tests/test_api_compass.py -v` → **19 passed** (18 pre-
  existing + the new legacy-shape test). No backend product code changed in this round, so no other
  backend module's tests were re-run.
- `cd apps/frontend && npx tsc --noEmit` → exit 0 (and exit 2 with the guard removed, above).
- `bash scripts/start-frontend.sh` production build → compiled successfully, 30/30 pages, `Ready in 265ms`.

### Fix-round live verification (the case the first round missed)

Backend (8255) + frontend (3255) started against the live 30-year seed DB, host-guard capped. Headless
Chromium (Playwright) loaded four as-of states and collected `pageerror`/console-error events on each:

| View | Rendered | `pageerror` / console errors |
|---|---|---|
| `/?asof=2026-08-11` (legacy row, `prior_as_of` non-null, no `rotation`) | `compass-leadership-rotation-not-recorded` placeholder, What-changed card still present | none |
| `/?asof=2020-03-20` (second legacy row) | same placeholder | none |
| `/` (default frontier, v9) | full block — Sector: 5 gaining / 2 losing, "7 of 31 shown · 24 below threshold · 0 beyond the display cap."; Theme: 1/1, "2 of 11 shown · 9 below threshold · 0 …" | none |
| `/?asof=1996-02-01` (earliest run) | `compass-leadership-rotation-no-prior` message | none |

No "Application error"/"client-side exception" text on any view — the app-level `error.tsx` fallback was
never reached. Screenshot evidence:
`reports/qa/goal-market-compass-iter-36-evidence/J-13-legacy-asof-rotation-not-recorded.png` (whole Today
page at `?asof=2026-08-11`: What changed card above, rotation placeholder, Next-session focus + manifest
strip below — all intact).

Both services were stopped afterwards; both ports (8255/3255) confirmed free. The lingering `next-server`
grandchild reported in Known Issues above recurred and again needed an explicit `kill -9` by PID — same
pre-existing `scripts/start-frontend.sh` gap, still untouched by this iteration.

### Files changed in this round
- `apps/frontend/lib/api.ts` -- `SessionDelta.rotation` made optional + doc comments for the legacy state.
- `apps/frontend/components/compass-leadership-rotation-section.tsx` -- third branch (rotation absent) with
  its own honest placeholder; `?? null` read; section doc comment lists all three states.
- `apps/backend/tests/test_api_compass.py` -- new
  `test_compass_route_serves_legacy_pre_iter36_row_without_rotation_key`.
- `reports/qa/goal-market-compass-iter-36-evidence/J-13-legacy-asof-rotation-not-recorded.png` -- new
  evidence screenshot.

No backend product code, no config, no `compass-whatchanged-card.tsx`, and no threshold value was touched
in this round.

### New issues found while fixing (NOT fixed — for reviewer/auditor triage)
- None beyond the already-documented `scripts/start-frontend.sh` child-process gap, which recurred
  exactly as described.
