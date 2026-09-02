# goal-market-compass-iter-39 Execution Plan

## Context (read, not re-litigated)

REGRESSION_HALT after iter-38 (verdict recorded in `runs/goal-session-market-compass/state/iteration-state.md`).
Root cause confirmed by direct code read: iter-38's J-14 backend fix
(`apps/backend/app/engine/compass.py::evaluate_selection`) is correct and untouched by this
iteration. The regression is confined to two frontend files:

- `apps/frontend/lib/api.ts:1069-1071,1089` — `WhyNotEntry.reason`/`.cap_rank`/`.cap` and
  `CompassSelection.why_not_totals` are declared **required**, but `/api/compass` replays each
  stored manifest's frozen `selection_json` verbatim, and 34/36 stored rows predate the iter-38
  `rule_version` bump and lack these fields.
- `apps/frontend/components/compass-focus-section.tsx:186-197` — the "Not priority" `Disclosure`
  summary dereferences `selection.why_not_totals.excluded_by_cap_uncapped` /
  `.below_floor_in_band_uncapped` unguarded → throws → React error boundary → full-page crash on
  21 of 23 historical `as_of` dates (AG-8 critical violation).

Confirmed by direct read that `WhyNotList`'s existing guard at
`compass-focus-section.tsx:116-120` (`entry.reason !== "excluded_by_cap" || entry.cap_rank === null
|| entry.cap === null`) already degrades safely when `reason`/`cap_rank`/`cap` are `undefined`
(returns `null`, i.e. no lead-in sentence) — this needs a TS-optionality fix only, no logic change,
per the spec's own instruction not to re-derive it as a new defect.

Confirmed by `git diff ab3cca63 -- runs/goal-session-market-compass/journey-scripts/J-0{4,5,6,7}.json`
that all four goldens are currently live-diverged from HEAD exactly as the spec describes (J-04's
`/?asof=2026-07-23`→`/`, J-05/J-06's `available_at_utc` assertion dropped and target moved to
`2005-04-15`, J-07 cut from 7 steps to 3) — this is the "weakened regression evidence" defect to
undo, verbatim per spec.

Frontend test convention confirmed (`apps/frontend/lib/mdd-color.test.ts`): plain Node TS
type-stripping via `node lib/<name>.test.ts` + `node:assert`, no test-runner framework installed —
the spec's "no new test runner" constraint maps directly onto this existing pattern.

This plan assumes the REGRESSION_HALT owner-acknowledgment gate was cleared upstream of this
phase dispatch (the spec's own NOTES section states this assumption; run-phase.sh would not have
been invoked for this phase otherwise). Not re-verified here — outside the orchestrator's role.

## What to Build

- Widen `apps/frontend/lib/api.ts` optionality: `CompassSelection.why_not_totals` →
  `why_not_totals?: WhyNotTotals`; `WhyNotEntry.reason?: WhyNotReason`, `.cap_rank?: number | null`,
  `.cap?: number | null`. Update the three doc-comments (lines ~1058-1065, ~1089) to state these
  fields are present only on manifests minted at/after the iter-38 `rule_version` bump and absent
  on older stored rows — replacing the current comment's unconditional phrasing.
- Guard `compass-focus-section.tsx`'s "Not priority" `Disclosure` summary (~line 192-197): when
  `selection.why_not_totals` is `undefined`, render
  `` `Not priority (${selection.why_not.length} shown — held-back counts unavailable for this manifest version)` ``;
  when present, keep the existing fully-counted string unchanged. No other behavior change.
- Confirm (comment/handoff note only, no code diff) that `WhyNotList`/`WhyNotLeadIn`'s existing
  guard at line ~116 already degrades safely for `undefined` `reason`/`cap_rank`/`cap` — cite this
  review in the dev handoff rather than re-deriving it as a defect.
- Add a new plain-node fixture test under `apps/frontend/lib/*.test.ts` (matching the
  `mdd-color.test.ts` pattern — no new framework) covering: (a) a pre-iter-38-shaped fixture
  missing `why_not_totals`/`reason`/`cap_rank`/`cap` → asserts the degraded string, no throw; (b) a
  post-iter-38 fixture with all fields present → asserts the existing fully-counted string,
  unchanged. If the render logic under test isn't already extracted into a pure/testable function,
  factor the minimum needed (e.g. a small pure helper producing the summary string) — do not
  restructure the component beyond that.
- Restore `runs/goal-session-market-compass/journey-scripts/J-04.json`, `J-05.json`, `J-06.json`,
  `J-07.json` to byte-exact HEAD `ab3cca63` content (`git checkout ab3cca63 --
  runs/goal-session-market-compass/journey-scripts/J-0{4,5,6,7}.json`, then verify
  `git diff ab3cca63 -- <those 4 paths>` is empty). Do not hand-retype — use the exact restore.
- Re-run the deterministic replay lane against the four restored goldens; record PASS/FAIL in the
  merged results file honestly, with no reconciliation-footer override — if one still fails
  post-fix that is real evidence to surface, not a script to re-edit.
- No backend code change (per spec: J-14's backend fix in `compass.py` is correct and out of
  scope). Backend `test_manifest_invariants.py`'s existing why-not fixtures should be re-run
  unchanged (fixture-only, no live DB) to confirm zero backend behavior drift, but this is
  verification, not a build item.
- Browser-qa must revisit all 21 previously-crashing `as_of` dates listed in TC-3 (not sampled) —
  loop cited in the dev handoff — confirming `GET /api/compass?as_of=<date>` returns 200 and no
  error-boundary card renders, plus the seven target journeys (J-02, J-03, J-06, J-08, J-11, J-13,
  J-14) and full regression sweep on the seven required-still-passing journeys (J-01, J-04, J-05,
  J-07, J-09, J-10, J-12).

## Out of Scope (per spec — do not build)

- Any change to `evaluate_selection` gating logic, thresholds, or why-not reason computation.
- J-15 (stays unbuilt, queued).
- Re-auditing AG-12/AG-17 hash/cohort identities from scratch (already proven byte-identical at
  iter-38; standard per-journey spot-check only).
- Re-litigating J-12's disposition-tally correctness.
- Any new incident-regeneration/schema-migration/cache-invalidation work under J-11.
- An evidence-only round (the six owed walkthroughs ride as passengers of this round's browser-qa
  captures only).

## Agents Required

- developer: yes — implements both build items above (frontend TS/component guard + new fixture
  test + journey-script restoration). This project's pipeline has one implementation agent
  (`developer`) covering both backend and frontend; there is no backend code change this
  iteration, so the developer's backend-facing work is limited to re-running existing fixture
  tests for confirmation.
  - backend-data: no (no backend source change; fixture-test re-run only, confirms zero drift)
  - frontend-ux: yes (`api.ts` optionality, `compass-focus-section.tsx` guard, new
    `apps/frontend/lib/*.test.ts` fixture test)

Frontend Present: yes

## Files to Create/Modify

- `apps/frontend/lib/api.ts` — lines ~1058-1071, ~1089: make `why_not_totals`/`reason`/`cap_rank`/
  `cap` optional; update doc-comments.
- `apps/frontend/components/compass-focus-section.tsx` — lines ~186-197: guard the "Not priority"
  `Disclosure` summary for `why_not_totals === undefined`.
- `apps/frontend/lib/<new-name>.test.ts` (new) — fixture tests for the degraded vs. fully-counted
  summary string (TC-14), following the `mdd-color.test.ts` plain-node pattern.
- `runs/goal-session-market-compass/journey-scripts/J-04.json`, `J-05.json`, `J-06.json`,
  `J-07.json` — restore to byte-exact HEAD `ab3cca63`.
- `runs/goal-session-market-compass/state/blueprint.md` — additive iter-39 note only (per spec:
  corrects the frontend TS interface's optionality to match what was always true of the stored
  data; no new field/module/endpoint).
- `docs/handoffs/goal-market-compass-iter-39-dev.md` (new) — dev handoff, required by Definition
  of Done.

## UI Evolution

- New user-facing capability: none new — this restores previously-working capability (Today page
  loads on every historical `as_of` date without crashing) and completes visibility into J-14's
  already-shipped why-not detail.
- New information displayed: none new. On pre-iter-38 manifests, the "Not priority" disclosure
  summary now reads an honest degraded count string instead of crashing the whole page.
- New user actions: none.
- UI surface changes: one string-variant change in `compass-focus-section.tsx`'s existing
  disclosure summary; no new component/panel/page.
- Navigation changes: none.

## Visual Requirements

- Component patterns: existing `Disclosure` and `Card` components only — no new component.
- Layout: unchanged (Today page `/` layout, existing focus-section card position).
- Key visual effects: none new — this is a text/guard fix, not a visual change.
- States to handle: the degraded-manifest state (pre-iter-38 row, `why_not_totals` absent) must
  render the honest placeholder string, never a blank/crashed section; the fully-counted state
  (post-iter-38 row) must render unchanged from today's behavior. Continue to honor the existing
  "backend not reachable" (`compass === null`) error card, unchanged.

## Key Test Scenarios

- TC-1/TC-2: `/?asof=2026-08-11` (pre-iter-38 row) renders full Today page content, no error
  boundary; "Not priority" summary reads the degraded string; `WhyNotList` entries render with no
  cap-lead-in sentence and no throw.
- TC-3: all 21 previously-crashing dates (full list in phase spec) load via `/?asof=<date>` with
  no error card and `GET /api/compass?as_of=<date>` returns 200 — looped, not sampled.
- TC-4 through TC-11: target journeys J-02, J-03, J-06, J-08, J-11, J-13, J-14 each pass per their
  spec-defined acceptance (see phase spec TC-4..TC-11 for exact assertions); J-14's capture must
  cover the full scrolled why-not list (not cropped at entry #20) and be measured via
  `PIL.Image.getcolors()`, not credited from filename.
- TC-12: for all 21 dates, `selection_disposition`, `prospective_eligible`, `content_hash`,
  `manifest_hash` are read-only confirmed unchanged from pre-iteration stored values.
- TC-13: restored goldens diff zero against `ab3cca63`; deterministic replay lane records PASS for
  all four with no reconciliation-footer override.
- TC-14: new fixture test — pre-iter-38 fixture produces degraded string, no exception; post-
  iter-38 fixture produces existing fully-counted string, unchanged.
- TC-15: frontend TypeScript build (`NEXT_DIST_DIR=.next-verify npx next build`, per this repo's
  build guard) completes with zero new type errors.
- Required-still-passing sweep: J-01, J-04, J-05, J-07, J-09, J-10, J-12 all remain green
  (deterministic replay + LLM fallback).
