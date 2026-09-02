# Goal Iteration 40 — J-15 "What changed" accounts for every stock-level crossing

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** market-compass
- **Iteration:** 40
- **Mode:** next
- **Depth:** full
- **Full trigger:** 4 — brand-new full-stack journey: J-15 is a never-built target journey with real
  backend (`apps/backend/app/engine/session_delta.py`) AND frontend
  (`apps/frontend/components/compass-whatchanged-card.tsx`, `apps/frontend/lib/api.ts`) Data-Contract
  additions. (Secondarily also satisfies trigger 1 — the fix changes shared computation
  (`_stock_changes`/`compute_delta`) consumed by the Today page, and by J-13's rotation accounting
  precedent, so its interaction surface is not covered by one journey's tests alone.) This matches the
  evaluator's binding `full` recommendation for this iteration directly — no escape condition needed.
- **Target journeys:** J-15
- **Required-still-passing journeys:** J-01, J-02, J-03, J-04, J-07, J-08, J-09, J-12, J-13, J-14
- **Anti-goal reminders:**
  - **AG-3:** A journey passes ONLY if the **displayed numbers are correct** — they match the engine's
    computation for the same as-of date — not merely that the page renders. *(critical)*
  - **AG-8 — Resilience to data-shape and data-scale change:** widening the data basis must never crash
    an existing page or exhaust memory — consumers of widened fields are re-validated, the UI degrades
    gracefully (contained error boundary, honest "—"/NA placeholder), and unbounded whole-table ORM
    loads are forbidden (the delta engine reads column-projected selects, never full record_json
    sweeps). *(critical)*
  - **AG-11 — No new composite candidate number:** no "fit", "conviction", "match", "probability of
    success", or any new blended score may be attached to candidates, the market, or the manifest;
    candidate presentation is limited to the existing three scores/buckets, config word maps, and
    structured reason/caution codes. *(critical)*
  - **AG-12 — Manifest immutability:** a stored `next_session_manifests` row and its exported file are
    never mutated or deleted by any later ingest, rebuild, data removal, config change, or code change;
    corrections happen only as new version rows; a historical view never substitutes a newer manifest.
    *(critical)*
  - **AG-15 — No outcome-tuned selection:** the selection rule and its thresholds must not be chosen or
    revised from realized forward returns within this goal; no Evidence Claim is introduced for it; any
    future selection-edge claim goes through the pre-registration registry and referee. *(critical)*

Frontend Present: yes

## GOAL

Build J-15: the What-changed card's stock-kind accounting becomes complete and honest — every
bucket-crossing the producer evaluates lands in exactly one of shown / suppressed / residual, the
"Suppressed moves" count stops omitting the stock kind, and an above-threshold mover held back by the
display cap is disclosed as a residual instead of vanishing uncounted.

## BACKGROUND

J-15 is the sole remaining GOAL_ACHIEVED blocker (14/15 journeys passing per iter-39's CONTINUE
verdict) and the highest-priority pick under rule 3 (unblocker) — no journey is regressed and the last
coherence verdict was COHERENCE-PASS, so no consolidation gate applies. It is a genuinely new,
never-built, fully measured, cited-defect journey (goal-proposer, 2026-09-01): on the stored frontier
pair 2026-08-11 → 2026-08-12, 57 stock-kind bucket crossings are evaluated, 14 clear
`compass.delta.stock_score_min_change` (8.0), but `_stock_changes` bounds to `max_stock_items` (10)
**before** classifying, so 4 above-threshold movers (TRV 8.66, SJM 8.48, ALL 8.33, TTWO 8.14) and 43
below-threshold crossings are never counted anywhere — "Suppressed moves (36)" already omits every one
of the 57 stock crossings. Confirmed live: `session_delta.py:261-264` slices `crossing_pairs` to
`bounded_crossings` and calls `_classify` only on that slice.

The iter-39 evaluator's next-step recommendation names four small passenger items to ride this round,
never as a round of their own: (1) the AG-8 minor — `WhyNotFailedCondition.gating` is still required in
`apps/frontend/lib/api.ts:1051` though absent on all 21 pre-iter-38 as-of dates, mislabeling 26 stored
leadership-floor misses "— advisory"; (2) repair the J-04 and J-14 golden scripts, **declared before
running them**; (3) capture the three still-missing walkthrough frames (J-05, J-06, J-12) plus retake
J-14's step-08 frame from the list with a `[NEW]` flag; (4) set the browser capture viewport to full
document height before screenshotting (the iter-36/37 blank-frame fix) so `UT-10` stops coming out
blank. All four are carried here as passengers alongside J-15's real scope, per that recommendation and
per rule 5 (only J-15 is a risky journey here — the other three are a one-line type fix, JSON-fixture
edits, and a capture-tooling setting).

Lessons applied directly: (a) iter-38's lesson — any field added to a payload rebuilt from a
stored/frozen row must be declared OPTIONAL in the TS interface, guarded on every read, and verified
against a row minted BEFORE the change, never one minted during the test — applies to the new
`session_delta.stock_accounting` field, which will be absent on every `next_session_manifests` row
frozen before this change ships; (b) iter-39's lesson — walk nested object/array element types, not
just top-level field names, when auditing a widened payload — applies to re-checking the `gating`
passenger fix does not introduce a second unguarded nested field; (c) the iter-38/iter-39 golden-tamper
lesson — a golden may never be edited after it fails without declaring the change in advance, and never
re-pointed at a same-day-minted date — the J-04/J-14 golden repairs below are declared here, before any
replay runs, and neither touches the as-of date (J-04 stays on `2026-07-23`, J-14's fix is a click-to-
expand step, not a date change); (d) iter-37's lesson — `set_viewport` to full document height before
any screenshot of `/` avoids the single-colour blank-frame failure mode.

## IN SCOPE

### Backend
- [ ] `apps/backend/app/engine/session_delta.py` `_stock_changes`: classify the FULL `crossing_pairs`
  list (via the existing `_classify` helper, unchanged threshold semantics) BEFORE applying the
  `max_stock_items` display bound, so every evaluated crossing lands in exactly one bucket: shown
  (top-magnitude, capped at the existing display bound), suppressed (below
  `compass.delta.stock_score_min_change`), or residual (meets the threshold but is bumped by the
  display cap). `max_stock_items` keeps its current value and stays the display cap only (AG-15 — no
  threshold value changes).
- [ ] `compute_delta`: add `session_delta.stock_accounting = {evaluated_count, shown_count,
  suppressed_count, residual_count}` (all `int >= 0`, summing to `evaluated_count`), computed once
  inside the existing pass over `crossing_pairs` — no new query, no second materialization of the
  crossing list (AG-8). The existing flat `session_delta.suppressed` list and `suppressed_count` now
  correctly include every below-threshold stock crossing (not just the pre-bound subset); the residual
  count is a COUNT only — no per-name residual list is added to the payload (AG-8's explicit
  no-per-name-residual-listing rule).
- [ ] No change to `_sector_changes`/`_theme_changes`/rotation accounting (J-13, iter-36 — "Do not
  redo"), to `evaluate_selection`/candidate membership (J-12/J-14 — "Do not redo"), or to any
  `compass.selection.*` value.
- [ ] `session_delta.py` stays a `test_no_magic_numbers.CALC_FILES` entry; no new literal — reuse the
  existing `compass.delta.stock_score_min_change` / `compass.delta.max_stock_items` keys only.
- [ ] No backend change for the AG-8 gating passenger fix below — the stored data was always optional;
  only the frontend type/render was wrong.

### Frontend
- [ ] `apps/frontend/lib/api.ts`: add `stock_accounting?: { evaluated_count: number; shown_count: number;
  suppressed_count: number; residual_count: number }` to the `SessionDelta` interface (line ~953) as
  OPTIONAL — every `next_session_manifests` row frozen before this change lacks the field.
- [ ] Passenger — AG-8 minor fix: `apps/frontend/lib/api.ts:1051` `WhyNotFailedCondition.gating` becomes
  `gating?: boolean`.
- [ ] `apps/frontend/components/compass-whatchanged-card.tsx`: when `session_delta.stock_accounting` is
  present, add a residual disclosure distinct from the existing "Suppressed moves (N)" line — e.g. "N
  more stock moves held back by the display cap" — using ONLY the count (no per-name list, AG-8). When
  `stock_accounting` is absent (older manifest), render nothing new — the existing "Suppressed moves"
  line and list continue to work exactly as before, no crash, no placeholder text implying stock
  coverage that manifest never had.
- [ ] Same component: when `stock_accounting.residual_count > 0` (the shown stock-change list is
  actually bounded this session), add one short disclosure line beside the stock entries — e.g. "showing
  the top N stock moves" — so the bounded list discloses its own bound instead of truncating silently
  (goal text step 4); omit this line entirely when `residual_count == 0` or when `stock_accounting` is
  absent.
- [ ] Passenger — AG-8 minor fix: `apps/frontend/components/compass-focus-section.tsx:151` — replace the
  truthiness read `{failed.gating ? "" : " — advisory"}` with a 3-state honest render:
  `failed.gating === undefined` → "— not recorded"; `failed.gating === true` → "" (gating, no
  suffix); `failed.gating === false` → " — advisory".

### Test golden repairs (declared in advance — JSON fixture edits only, no product code)
- [ ] `runs/goal-session-market-compass/journey-scripts/J-04.json` step 2: the click target is the stale
  literal `"Not priority (20)"` (the wording as of `ab3cca63`, before iter-38/39 changed the summary
  text). Update it to the current summary wording. Does NOT change the golden's `?asof=2026-07-23`
  target date.
- [ ] `runs/goal-session-market-compass/journey-scripts/J-14.json` step 3: currently re-navigates then
  asserts text inside a collapsed `<details>` element (`components/ui/disclosure.tsx` has no `open`
  attribute). Add a click step to expand the disclosure before the text assertion. Does NOT change the
  golden's target date.
- [ ] Both edits land BEFORE deterministic replay runs this iteration (never after a fail, per the
  iter-38/39 lesson); the developer handoff names both edits explicitly.

### New user-facing capability
The What-changed card on `/` now discloses the complete stock-level accounting for a fresh manifest:
every bucket-crossing evaluated is shown, counted as suppressed, or counted as residual — nothing is
silently dropped, and a reader can tell "this stock did not move enough" from "this stock moved enough
but is not in the shown list."

### New information displayed
- The "Suppressed moves" count on `/` now includes stock-kind crossings (today: 43 more).
- A new residual count near the stock section of the What-changed card, shown only on manifests minted
  after this change.
- A "showing top N" disclosure beside the shown stock entries, only when the display cap actually held
  something back this session.

### New user actions
None — this is a disclosure-completeness fix to an existing read-only card; no new interactive control.

### UI surface changes
`/` — What-changed card only (existing card, additive line/chip). No new page, no nav change.

### Product surface delta
The Today page's honesty guarantee extends from the sector/theme kinds (J-13) to the stock kind: every
number the delta engine evaluates for `/` is now accounted for somewhere on screen or in the disclosed
counts, never silently discarded past a display bound.

### Blueprint conformance
Lives under the existing **Today (`/`)** Information-Architecture home — same "What-changed" card slot
registered at baseline and extended by J-13 (iter-36). No new page, no new nav entry, no IA change.

### Data-contract additions
- `session_delta.stock_accounting.evaluated_count: int >= 0` — total stock-kind bucket crossings the
  producer evaluated for the pair.
- `session_delta.stock_accounting.shown_count: int >= 0` — crossings actually present in
  `session_delta.changes` (kind=stock), bounded by the existing `compass.delta.max_stock_items` display
  cap.
- `session_delta.stock_accounting.suppressed_count: int >= 0` — crossings below
  `compass.delta.stock_score_min_change` (now correctly counted; previously undercounted to 0 for the
  stock kind).
- `session_delta.stock_accounting.residual_count: int >= 0` — crossings that met the threshold but were
  bumped by the display cap; `evaluated_count == shown_count + suppressed_count + residual_count`.

  Computed by: `app.engine.session_delta.compute_delta` (specifically `_stock_changes`), invoked inside
  the SAME existing producer `app.engine.compass.build_manifest_payload`. Served by the SAME existing
  endpoint `GET /api/compass` — no new producer, no new route. `session_delta` is an open object in
  `docs/handoffs/trendora-next-session-manifest-v1.schema.json`, so this is additive with **no
  `schema_version` bump**, exactly as J-13's `rotation` fields (iter-36) and J-14's `why_not_totals`
  (iter-38) were registered. Field is OPTIONAL on the frontend type — absent on every
  `next_session_manifests` row frozen before this ships (AG-12: those rows are never rewritten to add
  it).

  No new value from the AG-8 passenger fix — `WhyNotFailedCondition.gating` is an ALREADY-REGISTERED
  field (iter-38); this iteration only corrects its TS optionality and render logic, per the iter-39
  finding. Nothing new to register for it.

## OUT OF SCOPE

- Any change to `compass.selection.*`, `evaluate_selection`, candidate membership, `comparison_cohort`,
  or `near_threshold_shadow` (J-12/J-14 — binding "Do not redo").
- Any change to `session_delta.rotation` or the sector/theme accounting (J-13 — binding "Do not redo").
- Any change to `max_stock_items`'s VALUE, `stock_score_min_change`'s VALUE, or any other
  `compass.delta.*` threshold value (AG-15 — display cap changes are out of scope; only its accounting
  changes).
- A per-name residual list in the served payload (AG-8 explicitly forbids it) — residual stays a count.
- The AG-8 crash fix, the four restored goldens, and J-14's backend logic — all DONE per iter-39's "Do
  not redo" list; not re-touched.
- A new round dedicated solely to the three missing walkthrough captures — they ride this round as
  passengers only (rule 7); if wall-clock forces a trim, the captures may be deferred again as
  `evidence_makeup`, never J-15 itself.
- Any live database write beyond the standard authorized `POST /api/compass/regenerate` call(s) needed
  to mint a manifest exercising the new fields on the frontier pair; no retroactive rewrite of any
  existing stored row or export (AG-12).

## DEFINITION OF DONE

- [ ] J-15 passes via browser-qa-agent
- [ ] Required-still-passing journeys (J-01, J-02, J-03, J-04, J-07, J-08, J-09, J-12, J-13, J-14)
  remain green (deterministic replay + LLM fallback)
- [ ] No anti-goal violation introduced (AG-3 correctness, AG-8 resilience + no-per-name-residual, AG-11
  no new composite score, AG-12 immutability, AG-15 no threshold retuned)
- [ ] Unit tests pass; no regressions
- [ ] Dev handoff written at `docs/handoffs/goal-market-compass-iter-40-dev.md`

## TESTING REQUIREMENTS

- Browser: J-15 (target); J-01, J-02, J-03, J-04, J-07, J-08, J-09, J-12, J-13, J-14 (required-still-
  passing, deterministic replay + LLM fallback)
- Unit/integration: `apps/backend/tests/test_manifest_invariants.py` / a session-delta fixture test
  covering the stock-kind classify-before-bound change with a fixture row for each of the three buckets
  (shown, suppressed, residual) plus the zero-crossings and more-crossings-than-cap cases named in the
  goal text steps 8(a)-(c); a frontend `apps/frontend/lib/*.test.ts` node script covering the optional
  `stock_accounting` guard on both an old (absent-field) and new (present-field) fixture payload.
- Error cases: a manifest whose `session_delta.stock_accounting` field is absent (pre-change row) must
  render the Today page fully, with no error boundary and no stock-accounting UI element.

Test-first contract:

- TC-1: given the stored frontier pair 2026-08-11 → 2026-08-12 has 57 stock-kind bucket crossings, when
  `GET /api/compass?as_of=2026-08-12` is called against a manifest regenerated after this change ships,
  then `session_delta.stock_accounting` reports `evaluated_count: 57`, and
  `evaluated_count == shown_count + suppressed_count + residual_count`.
- TC-2: given the same manifest, when the four named above-threshold movers (TRV 8.66, SJM 8.48, ALL
  8.33, TTWO 8.14) are checked against the served counts, then `residual_count` is exactly 4 and none of
  the four appears in `session_delta.changes` or `session_delta.suppressed`.
- TC-3: given a stock crossing below `compass.delta.stock_score_min_change` (8.0), when the manifest is
  built, then it is counted in `suppressed_count` (and appears in the `suppressed` list), never in
  `residual_count` or `shown_count`.
- TC-4: given the Today page (`/`) at the regenerated frontier as-of, when the What-changed card
  renders, then the "Suppressed moves" total displayed is 79 (sector 24 + theme 9 + breadth 2 + market 1
  + stock 43), and a separate residual disclosure shows count 4, using visibly different text from the
  suppressed line, with no per-name list attached to the residual count.
- TC-4b: given the same regenerated frontier manifest (`shown_count` 10, `residual_count` 4 > 0), when
  the What-changed card renders the stock entries, then a "showing the top N stock moves" (or
  equivalent) disclosure is visible beside them; given a manifest where `residual_count == 0`, when the
  same card renders, then no such disclosure line appears.
- TC-5: given an older stored manifest minted before this change ships (e.g. `as_of=2025-04-15`,
  pre-existing per iter-38/39 precedent — not a same-day-minted fixture), when
  `GET /api/compass?as_of=2025-04-15` is called, then the response's `session_delta` omits
  `stock_accounting`, the Today page returns HTTP 200 with a full render (no error boundary), and the
  "Suppressed moves" line renders using only its pre-existing sector/theme/breadth/market counts with no
  residual disclosure shown.
- TC-6: given the manifest-build query count measured before and after this change on the same as-of,
  when compared, then the count is unchanged, evidencing AG-8's no-new-query / no-unbounded-load limb.
- TC-7: given `session_delta.rotation` (J-13) and `selection.*` (J-04/J-12/J-14) fields on the same
  regenerated manifest, when compared to their pre-change values, then they are unchanged, and
  `candidate_rule_hash`/`cohort_rule_hash` are unchanged.
- TC-8: given the TRV crossing (a residual entry) at both as-of dates, when its from/to leadership bucket
  and score move are read from `GET /api/stocks` at each date, then they equal the values used to
  classify it as residual (bucket crossing present, magnitude 8.66 ≥ 8.0, beyond the display cap).
- TC-9 (AG-8 gating passenger): given a pre-iter-38 stored manifest (`as_of=2001-04-17`) whose
  `failed_conditions` entries lack the `gating` key, when the Today page's why-not block renders that
  row's `leadership_min_score` miss, then the label reads "— not recorded" (never "— advisory", never a
  crash).
- TC-10 (golden repair, declared above before running): given `journey-scripts/J-04.json` step 2 is
  updated to click the current "Not priority" summary wording, when deterministic replay executes J-04,
  then it exits PASS against the live `?asof=2026-07-23` page.
- TC-11 (golden repair, declared above before running): given `journey-scripts/J-14.json` step 3 is
  updated to expand the `<details>` disclosure before asserting text inside it, when deterministic
  replay executes J-14, then it exits PASS.
- TC-12 (walkthrough passengers): given the browser-QA capture step sets the viewport to full document
  height before each screenshot, when the J-05, J-06, J-12 walkthrough frames and J-14's retaken
  list-scrolled frame are captured, then each image is a genuine multi-colour capture (verified via
  `PIL.Image.getcolors()`, not a 1-colour blank), the new/retaken frames carry a `[NEW]` flag, and
  `UT-10` is no longer blank.

## NOTES

- Depth is `full` both because it matches the evaluator's binding recommendation for this iteration and
  because J-15 independently satisfies trigger 4 (brand-new full-stack journey) — no escape condition
  needed, no deviation from the recommendation.
- Per rule 5, only J-15 is a risky journey this round; the AG-8 gating fix, the golden repairs, and the
  viewport/capture setting are small, low-blast-radius passengers, consistent with the iter-39
  next-step's explicit "carry as passengers, never a round of their own" instruction.
- If wall-clock pressure forces a lane to be shed, shed the walkthrough-capture passengers first (rule 7
  — evidence-only work never blocks); J-15's own build, the AG-8 gating fix, and the two golden repairs
  should not be trimmed, since two of the three (goldens) are explicit repeat process gaps the last two
  evaluators flagged and the third (gating) is a named unresolved anti-goal ledger entry.
- Framework point carried forward unresolved from iter-39 (owner-visible, not this iteration's to fix):
  the reconciliation-footer escape hatch has converted deterministic-replay FAILs into merged PASSes in
  two consecutive prior rounds; this iteration's own golden edits are declared in advance specifically to
  avoid that pattern a third time — any reconciliation footer this round without a named, traced cause
  should be treated as an unresolved FAIL by the evaluator.
- Carried, non-blocking, not this iteration's scope: one pre-existing failing test on three untouched
  files; the 7.8 GB iteration-23 throwaway copy; `apps/frontend/.next-verify/` still tracked in git.
