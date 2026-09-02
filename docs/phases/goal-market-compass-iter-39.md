# Goal Iteration 39 — Repair the AG-8 crash, restore six regressed journeys, close J-14

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** market-compass
- **Iteration:** 39
- **Mode:** next
- **Depth:** full
- **Full trigger:** 3 — prior verdict REGRESSION (iter-38, AG-8 critical violation regressed 6
  journeys); the dispatch's own binding depth recommendation groups "prior ESCALATE/REGRESSION
  verdict" as one escape condition. Independently reinforced by trigger 1 (structural/
  cross-cutting): the fix touches a shared TS payload contract (`CompassSelection`/`WhyNotEntry`
  in `apps/frontend/lib/api.ts`) and its sole renderer (`compass-focus-section.tsx`), exercised
  across 7 target journeys spanning 5 different UI cards (What-changed, summary, rotation,
  focus section, manifest strip) plus 4 restored golden scripts — no single journey's tests
  cover that interaction surface.
- **Target journeys:** J-02, J-03, J-06, J-08, J-11, J-13, J-14
- **Required-still-passing journeys:** J-01, J-04, J-05, J-07, J-09, J-10, J-12 (full regression
  sweep — see BACKGROUND)
- **Frontend Present:** yes
- **Anti-goal reminders:**
  - **AG-8 — Resilience to data-shape and data-scale change:** widening the data basis must never crash an existing
    page or exhaust memory — consumers of widened fields are re-validated, the UI degrades gracefully (contained
    error boundary, honest "—"/NA placeholder), and unbounded whole-table ORM loads are forbidden (the delta
    engine reads column-projected selects, never full record_json sweeps). *(critical)*
  - **AG-12 — Manifest immutability:** a stored `next_session_manifests` row and its exported file are never
    mutated or deleted by any later ingest, rebuild, data removal, config change, or code change; corrections
    happen only as new version rows; a historical view never substitutes a newer manifest. *(critical)*
  - **AG-17 — Repair never rewrites provenance (owner, 2026-08-20):** restoring deleted historical data MUST
    NOT retroactively change research provenance. A manifest that was retrospective or ineligible stays that
    way; **`prospective_eligible` is never upgraded merely because historical data was later repaired**;
    `available_at_utc`, manifest versions, `content_hash`/`manifest_hash`, and prior eligibility
    classifications remain immutable (AG-12 governs the rows and files themselves). *(critical)*
  - **AG-15 — No outcome-tuned selection:** the selection rule and its thresholds must not be chosen or revised
    from realized forward returns within this goal; no Evidence Claim is introduced for it; any future
    selection-edge claim goes through the pre-registration registry and referee. *(critical)*
  - **AG-11 — No new composite candidate number:** no "fit", "conviction", "match", "probability of success",
    or any new blended score may be attached to candidates, the market, or the manifest; candidate presentation
    is limited to the existing three scores/buckets, config word maps, and structured reason/caution codes. *(critical)*
  - **AG-3:** A journey passes ONLY if the **displayed numbers are correct** — they match the engine's computation
    for the same as-of date — not merely that the page renders. *(critical)*

## GOAL

Make the Today page load without crashing on every historical `as_of` date again, restoring the
six journeys iter-38 regressed and completing J-14's own non-regression requirement, without
touching the correct J-14 backend logic.

## BACKGROUND

Iter-38 landed a correct backend fix (J-14's why-not reasons) but declared the new
`selection.why_not_totals` field non-optional in `apps/frontend/lib/api.ts:1089` and dereferenced
it unguarded in `apps/frontend/components/compass-focus-section.tsx:192-197`. Because
`/api/compass` replays each stored manifest's frozen `selection_json` verbatim, 34 of 36 stored
rows (21 of 23 distinct as-of dates) lack that field and the whole Today page fell to its error
boundary — a direct AG-8 violation. This regressed J-02, J-03, J-06, J-08, J-11, J-13 and left
J-14 `partial` (its own step 8 — "pre-fix manifests remain readable exactly as they are" — failed
on the same data). The prior evaluator's next-step recommendation is followed verbatim: (1) make
the field optional and guard every read so old rows degrade honestly instead of crashing, then
visit all 21 previously-crashing dates, not one; (2) re-verify the six regressed journeys; (3)
restore the four golden scripts (`J-04.json`, `J-05.json`, `J-06.json`, `J-07.json`) that were
edited at 19:26 the same round — after their 18:41 replay FAIL — to point at same-day-minted
fixtures instead of pre-existing dates (confirmed still live in the working tree via
`git diff ab3cca63 -- runs/goal-session-market-compass/journey-scripts/J-0{4,5,6,7}.json`, which
is non-empty right now); (4) then close J-14 with a capture that actually shows the restored
near-miss names instead of cropping at entry #20.

**Depth and scope justification.** Depth `full` is the evaluator's own binding recommendation for
this iteration (prior verdict REGRESSION), reinforced independently by the cross-cutting blast
radius described above (trigger 1). **Target-journey count deviates from the usual 1-3 guidance
(7 journeys)** — this is a deliberate exception per the priority rubric's "never bundle two risky
journeys" framing: these are not seven independent risky changes, they are ONE root-cause fix
(a single optional-field guard in two files) whose correctness can only be demonstrated by
re-verifying every journey it broke, exactly as the evaluator's own next-step recommendation
bundles them. **Required-still-passing is widened to all 7 currently-passing journeys** (a full
regression sweep, not the usual ~8-12 relevance-scoped subset) because the prior verdict was
REGRESSION and because three of those seven (J-04, J-05, J-07) carry the same weakened-golden
defect that must be corrected this round regardless of their own passing status.

**Lessons applied (from `lessons.md`):**
- iter-38 (regression cause): "declare it OPTIONAL in the TS interface, guard every read, and
  verify against a row minted BEFORE the change, never one minted during the test run." Applied
  directly to `why_not_totals` — and, since they were added in the SAME iter-38 change to the SAME
  payload and are equally absent on pre-iter-38 rows, also to `WhyNotEntry.reason`/`cap_rank`/`cap`
  even though their current defensive read (`compass-focus-section.tsx:116`) does not crash — the
  TS interface still lies about their presence.
- iter-38 (golden tampering): "A golden replay script that is edited AFTER it fails ... is no
  longer regression evidence ... treat a golden whose target URL moved onto a same-day-minted
  fixture as a moved goalpost, not a false positive." Applied: all 4 goldens restore to real,
  pre-existing dates, never a date minted during this round's own testing.
- iter-36/iter-37 (screenshot measurement / full-page capture): any acceptance capture this round
  (especially J-14's) must be measured (`PIL.Image.getcolors()`), not credited from its filename,
  and must use `set_viewport` to the full document height so no blank-frame scroll artifact
  recurs.

## IN SCOPE

### Backend
- None. Per the binding "Do not redo" note: the J-14 backend fix (`evaluate_selection`,
  `_select_why_not_display` in `apps/backend/app/engine/compass.py`) is correct and unchanged.

### Frontend
- [ ] `apps/frontend/lib/api.ts`: change `CompassSelection.why_not_totals` from required to
  optional (`why_not_totals?: WhyNotTotals`); change `WhyNotEntry.reason`, `.cap_rank`, `.cap`
  from required to optional (`reason?: WhyNotReason`, `cap_rank?: number | null`,
  `cap?: number | null`). Update each field's doc-comment to state it is present only on
  manifests minted at/after the iter-38 `rule_version` bump; absent on older stored rows.
- [ ] `apps/frontend/components/compass-focus-section.tsx:192-197`: guard the "Not priority"
  `Disclosure` summary — when `selection.why_not_totals` is `undefined`, render
  `` `Not priority (${selection.why_not.length} shown — held-back counts unavailable for this manifest version)` ``
  instead of dereferencing the missing object; when present, render the existing fully-counted
  string unchanged (no behavior change on new rows).
- [ ] Review (no code change expected) `WhyNotList`'s existing guard at
  `compass-focus-section.tsx:116` (`entry.reason !== "excluded_by_cap" || ...`) — confirm it
  already degrades safely when `reason`/`cap_rank`/`cap` are `undefined`, and cite that review in
  the dev handoff rather than re-deriving it as a new defect.
- [ ] Add a frontend plain-node test under `apps/frontend/lib/*.test.ts` (per Constraints — no
  new test runner) covering both a pre-iter-38 fixture (missing `why_not_totals`/`reason`/
  `cap_rank`/`cap`) and a post-iter-38 fixture (all fields present), asserting the degraded vs.
  fully-counted strings respectively and asserting neither throws.

### Regression-evidence integrity (test infrastructure)
- [ ] Restore `runs/goal-session-market-compass/journey-scripts/J-04.json`, `J-05.json`,
  `J-06.json`, `J-07.json` to their exact HEAD `ab3cca63` content (verify with
  `git diff ab3cca63 -- runs/goal-session-market-compass/journey-scripts/J-0{4,5,6,7}.json`
  reporting zero differences) — undoing the 19:26 same-day edits recorded in iter-38's eval.
  This restores: J-04's `/?asof=2026-07-23`/`/?asof=2026-03-30` targets; J-05/J-06's
  `/?asof=2025-04-15` target and the deleted `available_at_utc` assertion
  (`2026-08-20T11:41:00.381102+00:00`); J-07's full 7 steps including the market-link click and
  the three direction-word assertions.
- [ ] Re-run the deterministic replay lane against the restored goldens and record the result in
  the merged results file with no reconciliation-footer override — if any of the four still fails
  post-fix, that is real regression evidence, not a script to edit again.

### New user-facing capability
None new. This iteration restores previously-working capability (the Today page loading any
historical `as_of` date without crashing) and completes visibility into J-14's already-shipped
why-not detail (near-miss names now provably visible in evidence, not new behavior).

### New information displayed
None new. The fix ensures information already shipped by J-14 (why-not reasons, cap rank/cap,
held-back totals) degrades honestly instead of crashing when a stored manifest predates that
field.

### New user actions
None.

### UI surface changes
`compass-focus-section.tsx`'s "Not priority" disclosure summary gains one degraded-state string
variant for pre-iter-38 manifests. No new component, panel, or page.

### Product surface delta
21 of 23 historical `as_of` dates go from a full-page crash back to rendering the Today page.
J-02, J-03, J-06, J-08, J-11, J-13 return to `passing`. J-14 moves from `partial` to `passing`
(its own non-regression requirement is now met).

### Blueprint conformance
No new surfaces. All touched pages already live under the Today (`/`) canonical home registered
in `blueprint.md`'s Information Architecture table (rows for J-02, J-03, J-04, J-05/J-06, J-07,
J-08, J-13). J-11's verification is non-UI (backend-state re-check via the same Today page render
path) and carries no separate IA row, consistent with existing blueprint precedent.

### Data-contract additions
None. `selection.why_not_totals` and `WhyNotEntry.reason`/`cap_rank`/`cap` were already
registered (iter-38 blueprint note) under the existing "Next-session manifest — CONTENT block"
row, computed by the existing `app.engine.compass.build_manifest_payload` / `evaluate_selection`
and served only by the existing `GET /api/compass`. This iteration corrects the FRONTEND TS
interface's optionality to match what was always true of the stored data — no new computing
module, no new serving endpoint, no new field. `blueprint.md` gets an additive iter-39 note
recording this correction (see below).

## OUT OF SCOPE

- J-15 (stock-level "Suppressed moves" undercount) — stays unbuilt and queued behind this repair
  round, per the binding "Do not redo" note.
- Any change to `evaluate_selection`'s gating logic, thresholds, or the `why_not` reason
  computation itself — the backend is correct and untouched.
- Re-auditing AG-12/AG-17 hash/cohort identities from scratch — already proven byte-identical at
  iter-38 and re-confirmed only via the standard per-journey AG-17 spot-check in TC-12, not a
  fresh full derivation.
- Re-litigating J-12's disposition-tally correctness — proven unmoved at iter-38, out of scope
  here.
- Building any new incident-regeneration, schema-migration, or cache-invalidation work under
  J-11's original Stage B/C scope — that work is already complete; this iteration only re-verifies
  that the SAME already-regenerated state renders without crashing.
- An evidence-only round — explicitly excluded per the binding "Do not redo: do not schedule an
  evidence-only round." The six still-owed walkthrough recordings (J-02, J-03, J-05, J-06, J-07,
  J-12) ride as passengers of this iteration's browser-qa captures, never a round of their own.

## DEFINITION OF DONE

- [ ] J-02, J-03, J-06, J-08, J-11, J-13 pass via browser-qa-agent on restored historical dates
- [ ] J-14 passes via browser-qa-agent, with step 8 ("pre-fix manifests remain readable exactly as
  they are") verified across all 21 previously-crashing dates
- [ ] Required-still-passing journeys (J-01, J-04, J-05, J-07, J-09, J-10, J-12) remain green
  (deterministic replay + LLM fallback — mechanically verified at both depths)
- [ ] No anti-goal violation introduced — AG-8 resolved (zero crashes across all 21 dates),
  AG-12/AG-17 stored-value immutability re-confirmed read-only
- [ ] Golden scripts J-04, J-05, J-06, J-07 restored byte-exact to HEAD `ab3cca63` and re-pass
  deterministic replay against their restored (pre-existing, never same-day-minted) targets
- [ ] Unit tests pass; no regressions — new frontend fixture tests green, frontend TypeScript
  build clean with zero new type errors
- [ ] Dev handoff written at `docs/handoffs/goal-market-compass-iter-39-dev.md`

## TESTING REQUIREMENTS

- Browser: J-02, J-03, J-06, J-08, J-11, J-13, J-14 (targets); J-01, J-04, J-05, J-07, J-09, J-10,
  J-12 (required-still-passing, full regression sweep)
- Unit/integration: frontend plain-node fixture tests for the optional-field guard
  (`apps/frontend/lib/*.test.ts`); frontend TypeScript build; backend
  `test_manifest_invariants.py`'s existing why-not fixtures re-run unchanged (fixture-only, no
  live DB) to confirm zero backend behavior change
- Error cases: a `selection` object missing `why_not_totals`/`reason`/`cap_rank`/`cap` must never
  throw and must render an honest degraded placeholder, never a fabricated count

Test-first contract:

- TC-1: given the stored 2026-08-11 manifest row (minted before the iter-38 `rule_version` bump,
  so it lacks `selection.why_not_totals`), when `/?asof=2026-08-11` loads, then the Today page
  renders full content (state band, summary, what-changed, rotation, focus section, manifest
  strip) with no React error boundary, and the "Not priority" `Disclosure` summary reads
  "Not priority (N shown — held-back counts unavailable for this manifest version)" instead of
  throwing on the missing object.
- TC-2: given the same 2026-08-11 row's `why_not` entries (each missing `reason`/`cap_rank`/
  `cap`), when `WhyNotList` renders them, then no cap-lead-in sentence appears for any entry, each
  entry's `failed_conditions` list (or its own empty state) still renders, and no exception is
  thrown.
- TC-3: given all 21 dates previously crashing per iter-38's eval (1996-01-02, 1996-02-01,
  2001-04-17, 2005-04-01, 2018-11-20, 2019-03-01, 2020-01-02, 2020-03-20, 2022-06-15, 2025-04-15,
  2026-01-02, 2026-03-30, 2026-03-31, 2026-04-01, 2026-07-01, 2026-07-23, 2026-08-01, 2026-08-03,
  2026-08-05, 2026-08-10, 2026-08-11), when each is loaded via `/?asof=<date>` in a scripted loop
  cited in the dev handoff (not sampled), then none renders the "Something went wrong on this
  page" error card and `GET /api/compass?as_of=<date>` returns HTTP 200 for all 21.
- TC-4: given J-02 at `/?asof=2026-08-11`, when the page loads, then the What-changed card header
  names the correct prior stored session date and entries are ordered market → breadth → sectors
  → themes → stocks with no entry throwing.
- TC-5: given J-03 at `/?asof=2026-08-01`, when the page loads, then the summary card renders the
  state/direction/breadth/focus-count sentences with the "Show cited facts" disclosure available,
  no crash.
- TC-6: given J-06's genuinely pre-existing manifest at `/?asof=2025-04-15` (its own former golden
  target, restored per the golden-restoration item above), when the basis-disclosure and version
  list are inspected, then the page renders without crash, the restored golden's
  `available_at_utc` assertion (`2026-08-20T11:41:00.381102+00:00`) passes, and no new version is
  minted merely by viewing it.
- TC-7: given J-07's golden script restored to its full 7 steps (including the market-link click
  and the three direction-word assertions) and pointed at `/?asof=2026-08-03` for step 7, when the
  deterministic replay lane executes it, then all 7 steps PASS and the page shows real content
  (not the crash page) at that as-of.
- TC-8: given J-08 at `/?asof=2026-08-10`, when the page loads, then `/market` still renders its
  full former inventory unchanged and the Today strip at that as-of shows a
  `retrospective`-labeled manifest matching D's stored values, no crash.
- TC-9: given J-11's incident-derived state (Stage C/G already complete, unchanged this iteration)
  at `/?asof=2026-08-05` (one of the 11 incident dates and one of the 21 crashing dates), when the
  page loads, then no crash occurs and the manifest strip content matches the stored row for that
  date.
- TC-10: given J-13's rotation section at `/?asof=1996-01-02`, when the page loads, then both
  gaining/losing sides render (or their honest empty state) with signed deltas and direction
  words, no crash — replacing iter-38's blank/crash capture at this same as-of with genuine
  content.
- TC-11: given J-14's frontier manifest (`2026-08-12`, v10, unchanged this iteration), when the
  "Not priority" disclosure is expanded and the capture covers the full scrolled list (not cropped
  at entry #20 as iter-38's capture was), then the screenshot shows at least one cap-excluded name
  (with its rank and cap) and at least one below-floor near-miss name (with the floor and
  distance), both visually present and measured (not credited from filename alone).
- TC-12: given J-14 acceptance step 8, when each of the 21 previously-crashing dates is loaded,
  then the page renders without crash AND that manifest's `selection_disposition`,
  `prospective_eligible`, `content_hash`, and `manifest_hash` values are read-only confirmed
  unchanged from their pre-iteration stored values, cited in the dev handoff.
- TC-13: given the four golden scripts restored, when
  `git diff ab3cca63 -- runs/goal-session-market-compass/journey-scripts/J-04.json runs/goal-session-market-compass/journey-scripts/J-05.json runs/goal-session-market-compass/journey-scripts/J-06.json runs/goal-session-market-compass/journey-scripts/J-07.json`
  is run, then it reports zero differences, and the deterministic replay lane then executes all
  four against their restored targets and records PASS in the merged results file with no
  reconciliation-footer override.
- TC-14: given a frontend plain-node test fixture representing a `selection` object without
  `why_not_totals`/`reason`/`cap_rank`/`cap` and a second fixture WITH all fields populated, when
  the focus-section render logic under test runs on each, then the first produces the degraded
  "held-back counts unavailable" string with no exception and the second produces the existing
  fully-counted string unchanged.
- TC-15: given `api.ts`'s `why_not_totals`, `WhyNotEntry.reason`, `.cap_rank`, `.cap` fields
  declared optional, when the frontend TypeScript build runs, then it completes with zero new
  type errors.

## NOTES

- **Owner acknowledgment gate.** `iteration-state.md` recorded a REGRESSION_HALT after iter-38
  ("Owner: halt acknowledged? Resume needs `--acknowledge-regression`."). This spec assumes the
  engine was resumed with that acknowledgment before dispatching iter-39 planning; if not, the
  engine/owner should confirm before this spec executes.
- **Carried items, none blocking this iteration:** one pre-existing failing test on three
  untouched files (fix or formally waive it — not scoped here); the 7.8 GB iteration-23 throwaway
  copy may be deleted; `apps/frontend/.next-verify/` is tracked in git and should be gitignored
  instead — none of these three block this repair and none is addressed by this spec.
- **Two framework points carried from iter-38's eval, for the owner, not actioned by this spec:**
  the depth ladder should re-read goal state when new Must-have journeys appear rather than using
  a stale prior verdict; a browser-QA step should not rewrite a check script whose contents it did
  not change.
- If, during implementation, any of the 21 dates fails for a reason OTHER than the
  `why_not_totals`/`reason`/`cap_rank`/`cap` guard (a second, distinct crash cause), stop and
  surface it — do not silently widen this spec's fix to cover an unrelated defect; report it for a
  follow-up iteration instead.
