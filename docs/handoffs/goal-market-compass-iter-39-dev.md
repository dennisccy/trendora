# goal-market-compass-iter-39 Dev Handoff

**Phase:** goal-market-compass-iter-39
**Date:** 2026-09-02
**Agent:** developer
**Status:** complete

## What Was Built

Root-cause repair of the iter-38 AG-8 regression (Today page crashed on 21 of 23 historical
`as_of` dates because `apps/frontend/lib/api.ts` declared `selection.why_not_totals` and
`WhyNotEntry.reason`/`.cap_rank`/`.cap` as required TS fields, but `/api/compass` replays each
stored manifest's frozen `selection_json` verbatim and 34 of 36 stored rows predate the iter-38
`rule_version` bump and lack those fields). No backend code changed — `evaluate_selection` /
`_select_why_not_display` in `apps/backend/app/engine/compass.py` were confirmed correct and
untouched, per the spec's "Do not redo" instruction.

- **Widened TS optionality** (`apps/frontend/lib/api.ts`): `CompassSelection.why_not_totals` is
  now `why_not_totals?: WhyNotTotals`; `WhyNotEntry.reason`/`.cap_rank`/`.cap` are now
  `reason?: WhyNotReason`, `cap_rank?: number | null`, `cap?: number | null`. Doc comments on all
  four fields updated to state they are present only on manifests minted at/after the iter-38
  `rule_version` bump and absent (not null, `undefined`) on older stored rows.
- **New pure helper** `apps/frontend/lib/why-not-summary.ts` — `whyNotSummary()` extracts the
  "Not priority" disclosure summary string out of the component (mechanical extraction, matching
  the `basis-disclosure-label.ts` convention of a dependency-free local type rather than importing
  from `api.ts`, so it runs under plain `node lib/why-not-summary.test.ts`). Two branches:
  - `why_not_totals` present -> the pre-existing fully-counted string, byte-identical to iter-38's.
  - `why_not_totals` undefined -> the new degraded string:
    `` `Not priority (${N} shown — held-back counts unavailable for this manifest version)` ``
- **Guarded the render site** (`apps/frontend/components/compass-focus-section.tsx`): the "Not
  priority" `Disclosure` summary now calls `whyNotSummary({ why_not_count, why_not_totals })`
  instead of dereferencing `selection.why_not_totals.excluded_by_cap_uncapped` unguarded.
- **Reviewed, no code change**: `WhyNotLeadIn`'s existing guard at
  `compass-focus-section.tsx:115` (`entry.reason !== "excluded_by_cap" || entry.cap_rank === null
  || entry.cap === null`) — confirmed by direct read that it already degrades safely when
  `reason`/`cap_rank`/`cap` are `undefined`: `undefined !== "excluded_by_cap"` is `true`, so the
  `||` chain short-circuits and returns `null` (no lead-in sentence) before either `cap_rank` or
  `cap` is read. Added a doc-comment recording this review in place (no logic change), per the
  spec's own instruction not to re-derive this as a new defect.
- **New fixture test** `apps/frontend/lib/why-not-summary.test.ts` (TC-14) — 6 checks covering:
  `why_not_totals` undefined (explicit `undefined`, and the field simply omitted) -> degraded
  string, no throw, including a 0-shown edge case; `why_not_totals` present -> the existing
  fully-counted string, including explicit-zero-count edge cases (never a fabricated total).
- **Restored the four golden scripts** to byte-exact HEAD `ab3cca63`:
  `runs/goal-session-market-compass/journey-scripts/J-04.json`, `J-05.json`, `J-06.json`,
  `J-07.json` (`git checkout ab3cca63 -- <paths>`). Verified `git diff ab3cca63 -- <paths>`
  reports zero differences. This undoes the iter-38 same-day edits that had moved J-04's
  `/?asof=2026-07-23`/`2026-03-30` targets, dropped J-05/J-06's `available_at_utc` assertion and
  moved their target to a same-day-minted `2005-04-15` fixture, and cut J-07 from 7 steps to 3.
- **`blueprint.md`** already carried the additive iter-39 note (present in the working tree before
  this agent started — written upstream of dev dispatch, presumably by the orchestrator/goal-
  decomposer tooling); verified its content against the actual diff and it accurately describes
  this change (lines 404-420). No further edit needed.

## Files Changed

- `apps/frontend/lib/api.ts` — `WhyNotEntry.reason`/`.cap_rank`/`.cap` and
  `CompassSelection.why_not_totals` made optional; doc comments updated.
- `apps/frontend/components/compass-focus-section.tsx` — "Not priority" summary now calls the new
  `whyNotSummary()` helper instead of an unguarded template literal; added a review comment on
  `WhyNotLeadIn`'s existing safe guard (no logic change there).
- `apps/frontend/lib/why-not-summary.ts` (new) — pure `whyNotSummary()` function, dependency-free.
- `apps/frontend/lib/why-not-summary.test.ts` (new) — TC-14 fixture tests, 6 checks.
- `runs/goal-session-market-compass/journey-scripts/J-04.json`, `J-05.json`, `J-06.json`,
  `J-07.json` — restored byte-exact to HEAD `ab3cca63`.

## Tests Run

- **Frontend fixture test** (`why-not-summary.test.ts`, TC-14): this dev box's Node build
  (v22.22.1) lacks TypeScript type-stripping support (a pre-existing, documented environment
  limitation — see prior iterations' handoffs, e.g. `goal-mcp-loop-iter-3-dev.md`), so the
  documented `node lib/why-not-summary.test.ts` invocation throws `ERR_UNKNOWN_FILE_EXTENSION`. I
  transpiled with the project's own `tsc` 5.7.2 (`--rewriteRelativeImportExtensions --module
  nodenext --moduleResolution nodenext`) into a scratch dir and ran the emitted JS — the same
  documented fallback prior iterations use.
  Result: **6 passed, 0 failed**.
- **Frontend TypeScript build** (TC-15): `NEXT_DIST_DIR=.next-verify npx next build` — compiled
  successfully, zero type errors, all 30 static/dynamic routes generated. Also ran
  `npx tsc --noEmit -p tsconfig.json` standalone — zero errors.
- **Backend fixture re-run** (zero-drift confirmation, no live DB, no backend code touched):
  `cd apps/backend && .venv/bin/python -m pytest tests/test_manifest_invariants.py -k "why_not" -v`
  -> **2 passed** (`test_tc23_why_not_and_qualifier_changes_move_only_manifest_config_hash`,
  `test_tc23_why_not_cap_change_moves_only_display_length_not_totals_or_served_reasons`), confirming
  the untouched backend's why-not behavior is unchanged.
- **Golden-script restoration** (TC-13, developer-scope half only): `git diff ab3cca63 --
  runs/goal-session-market-compass/journey-scripts/J-0{4,5,6,7}.json` reports **zero differences**.
  Re-running the deterministic replay lane against the restored targets and recording PASS/FAIL in
  the merged results file is the browser-qa-agent's job per this project's established convention
  (golden replay is a downstream-agent responsibility — see `goal-market-compass-iter-37-dev.md`'s
  "Depth / process disclosure" section for the same precedent), not run by this agent.
- **Live, non-mocked verification** (backend + frontend both started via
  `scripts/start-backend.sh` / `scripts/start-frontend.sh`, no process was running on ports
  8255/3255 before this session, both stopped and confirmed dead afterward — `ps aux` clean):
  - `GET /api/compass?as_of=<date>` returned **HTTP 200 for all 21** previously-crashing dates
    (1996-01-02, 1996-02-01, 2001-04-17, 2005-04-01, 2018-11-20, 2019-03-01, 2020-01-02,
    2020-03-20, 2022-06-15, 2025-04-15, 2026-01-02, 2026-03-30, 2026-03-31, 2026-04-01,
    2026-07-01, 2026-07-23, 2026-08-01, 2026-08-03, 2026-08-05, 2026-08-10, 2026-08-11).
  - Confirmed via direct payload inspection: the 2026-08-11 row's `selection` object has NO
    `why_not_totals` key and its `why_not[]` entries have only `{ticker, failed_conditions}` (no
    `reason`/`cap_rank`/`cap`) — a genuine pre-iter-38 shape. The 2026-08-12 frontier row (v10) has
    `why_not_totals` present and every `why_not[]` entry carries `reason`/`cap_rank`/`cap`.
  - **Real browser** (Chrome DevTools Protocol via the `superpowers-chrome` skill), not just curl:
    - `/?asof=2026-08-11` (pre-iter-38 row): full page rendered — state band, summary, what-changed,
      rotation (honest "not recorded for this session" empty state), focus section, manifest strip
      — no error boundary. The "Not priority" summary read exactly `Not priority (20 shown — held-
      back counts unavailable for this manifest version)`.
    - `/?asof=1996-01-02` (oldest of the 21 dates): rendered without crash, "Not priority" text
      present.
    - `/?asof=2026-08-12` (frontier v10, post-iter-38 shape, unchanged this iteration): rendered
      without crash; the "Not priority" summary read the **unchanged** fully-counted string
      `Not priority (20 shown of 52 held back — 27 cap-excluded, 25 below-floor near-miss)`
      (matches the values already measured in `blueprint.md`'s iter-38 note: 27 / 25); expanding the
      disclosure confirmed a cap-excluded entry's "ranked #..." lead-in sentence still renders,
      confirming no regression on the path this iteration does not change.

## Known Issues

- **Deterministic replay lane / merged-results file**: not run by this agent (see "Tests Run"
  above) — downstream browser-qa-agent's job per established project convention. The file-level
  half of TC-13 (zero diff against `ab3cca63`) is done and verified.
- **The other 18 of the 21 previously-crashing dates and the seven target journeys (J-02, J-03,
  J-06, J-08, J-11, J-13, J-14) with their exact acceptance assertions (TC-4 through TC-12)** are
  browser-qa-agent's scope, not spot-checked individually by this agent beyond the sample above
  (2026-08-11, 1996-01-02, 2026-08-12) and the universal `GET /api/compass` 200-status sweep across
  all 21 dates.
- **`apps/frontend/.next-verify/`** is tracked in git (a pre-existing, spec-acknowledged carried
  issue — "should be gitignored instead ... none of these three block this repair") and picked up
  build-artifact diffs from the TC-15 verification build run in this session. Not addressed here,
  per the spec's own "Carried items, none blocking" note.
- No new dependency, no new env var, no schema/migration change, no external network call this
  iteration.
- Nothing found outside the `why_not_totals`/`reason`/`cap_rank`/`cap` guard that crashed any of
  the 21 dates — the spec's "if a second distinct crash cause appears, stop and surface it" branch
  was not triggered.
