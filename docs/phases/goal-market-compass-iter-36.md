# Goal Iteration 36 — Leadership rotation: served both-directions block, signed deltas, no duplication

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** market-compass
- **Iteration:** 36
- **Mode:** next
- **Depth:** full
- **Full trigger:** 1 — structural/cross-cutting: this iteration adds a served field to the shared
  `session_delta` producer (`app.engine.compass.build_manifest_payload` /
  `app.engine.session_delta.compute_delta`) that four already-passing journeys read (J-02 What-changed,
  J-05/J-06 manifest freeze+immutability, J-07 Today page), touches both the backend content shape and a
  frontend component rewrite (`compass-leadership-rotation-section.tsx`), and J-13's own Acceptance
  demands proof that the What-changed card comes out byte-for-byte unchanged — an interaction the single
  target journey's own test suite cannot certify alone.
- **Frontend Present:** yes
- **Target journeys:** J-13
- **Required-still-passing journeys:** J-02, J-04, J-05, J-06, J-07, J-08, J-12
- **Anti-goal reminders:**
  - **AG-1:** A score, ranking, or "edge" MUST NOT be presented as proven/confident unless it is backed by a **passing certified-claim entry** in the evidence ledger (out-of-sample, control-beating). Unbacked values MUST render a "not yet proven" state. *(critical)*
  - **AG-2 — Decision-quality only:** never present return promises, price targets, "buy/sell" signals, or alpha claims; never place or simulate orders. Candidate framing is "worth monitoring", never advice. *(critical)*
  - **AG-3:** A journey passes ONLY if the **displayed numbers are correct** — they match the engine's computation for the same as-of date — not merely that the page renders. *(critical)*
  - **AG-8 — Resilience to data-shape and data-scale change:** widening the data basis must never crash an existing page or exhaust memory — consumers of widened fields are re-validated, the UI degrades gracefully (contained error boundary, honest "—"/NA placeholder), and unbounded whole-table ORM loads are forbidden (the delta engine reads column-projected selects, never full record_json sweeps). *(critical)*
  - **AG-11 — No new composite candidate number:** no "fit", "conviction", "match", "probability of success", or any new blended score may be attached to candidates, the market, or the manifest; candidate presentation is limited to the existing three scores/buckets, config word maps, and structured reason/caution codes. *(critical)*
  - **AG-12 — Manifest immutability:** a stored `next_session_manifests` row and its exported file are never mutated or deleted by any later ingest, rebuild, data removal, config change, or code change; corrections happen only as new version rows; a historical view never substitutes a newer manifest. *(critical)*
  - **AG-15 — No outcome-tuned selection:** the selection rule and its thresholds must not be chosen or revised from realized forward returns within this goal; no Evidence Claim is introduced for it; any future selection-edge claim goes through the pre-registration registry and referee. *(critical)*
  - **AG-17 — Repair never rewrites provenance (owner, 2026-08-20):** restoring deleted historical data MUST NOT retroactively change research provenance. A manifest that was retrospective or ineligible stays that way; `prospective_eligible` is never upgraded merely because historical data was later repaired; `available_at_utc`, manifest versions, `content_hash`/`manifest_hash`, and prior eligibility classifications remain immutable (AG-12 governs the rows and files themselves). *(critical)*

## GOAL

Make the Today page's Leadership rotation section serve its own `session_delta.rotation` content —
two labelled, signed, both-directions sides per group kind (sector, theme) — instead of re-rendering a
client-side filter of the What-changed list above it, and stop silently dropping above-threshold movers
that fall beyond the display cap.

## BACKGROUND

J-13 is the sole blocking journey (`goal_gate.py journeys` exits 1, `blocking: ["J-13"]`) and the only
Must-have journey not yet built. The prior evaluator (iter-35) measured three defects directly against
the live frontier manifest and code, which I re-confirmed myself:
`apps/frontend/components/compass-leadership-rotation-section.tsx:38` renders
`session_delta.changes.filter(kind ∈ {sector,theme,stock})` — a client-side subset of the SAME array
`compass-whatchanged-card.tsx` already renders in full (17/17 rows duplicated on the frontier); change
entries carry an unsigned `magnitude` with no `delta`/`direction_word`; and
`_sector_changes`/`_theme_changes` (`apps/backend/app/engine/session_delta.py:105-162`) sort-then-slice
to `top_k` while returning only the BELOW-threshold `suppressed` list, so an above-threshold mover
beyond the cap is counted nowhere (measured: sector accounts for 29 of its 31 configured ETFs).

The iteration-state "Do not redo" block binds this round's depth to `full` explicitly ("shared
`session_delta` producer feeds J-02/J-05/J-06/J-07; J-13 must prove What-changed unchanged; real UI for
ux-regression. A drop to lean must be surfaced explicitly and marked unmet") and the dispatch's own
evaluator depth recommendation for this iteration is `full`, binding by default — this spec follows it
without deviation.

Applying iter-35's lesson (multi-condition gate fixtures must isolate each condition, or the suite is
green and blind): the rotation display has two independent gating conditions — `rank_move_min` (is this
a change at all) and the new `rotation_top_k` (is it inside the cap) — so this iteration's fixtures must
include a row that clears the first but is excluded by the second (see TC-8/TC-15), not reuse a fixture
where both conditions covary.

## IN SCOPE

### Backend
- [ ] `apps/backend/app/engine/session_delta.py`: extend `_sector_changes`/`_theme_changes` (or their
      shared caller) to retain a signed rank-delta per pair (not just `abs()` magnitude) and to disclose
      above-threshold pairs that clear `rank_move_min` but fall beyond the display cap, rather than
      dropping them.
- [ ] `apps/backend/app/engine/compass.py`: inside `build_manifest_payload`, build a new
      `session_delta.rotation` block from the SAME sector/theme rank pairs `compute_delta` already
      computes (no second computation) — two labelled sides (`gaining`, `losing`) per kind, each capped
      by a NEW config-only `compass.delta.rotation_top_k`, each entry still gated by the existing
      `compass.delta.rank_move_min`, plus a per-kind accounting object whose `shown + suppressed +
      residual` closes exactly against the configured group count (31 sector/industry, 11 theme). No
      stock-kind rows anywhere in `session_delta.rotation` (group-level only). Reuse the existing
      `_flat_band_word`/`compass.vocabulary.direction_words` classifier for `direction_word` (never a
      second word map); polarity resolved engine-side so a FALLING rank number is "improving" — mirror
      the `state_band.stress` sign-transform precedent (`compass.py:284-345`) rather than inventing a new
      pattern.
- [ ] Add the SAME signed `delta` + served `direction_word` fields to `session_delta.changes[]` entries
      of `kind ∈ {sector, theme}` (single computation, two placements — see assumptions ledger entry for
      why `market`/`breadth`/`stock` kinds are out of scope for this field addition).
- [ ] No-prior-run handling: `session_delta.rotation` renders the same explicit no-comparison state as
      `session_delta`'s own no-prior-run branch when `previous_run is None` — no deltas, no direction
      words, nothing fabricated.
- [ ] `config.yaml`: add `compass.delta.rotation_top_k` under the existing `compass.delta` block
      (config-only value; `session_delta.py`/`compass.py` stay `test_no_magic_numbers.CALC_FILES`
      entries — no literal in code).
- [ ] Do NOT touch `compass.selection.*`, `evaluate_selection`, candidate membership, either frozen
      cohort, or any existing threshold VALUE (`rank_move_min`, `top_k`, `market_score_min_change`,
      etc.) — J-12's "Do not redo" and AG-15 both stay binding.
- [ ] Verify manifests produced under this change still validate against
      `docs/handoffs/trendora-next-session-manifest-v1.schema.json` with NO `schema_version` bump
      (`session_delta` is an open object there).
- [ ] Verify all pre-existing `next_session_manifests` rows and their export files stay byte-identical
      (`content_hash`, `manifest_hash`, `payload_json`) — this change affects only manifests minted AFTER
      it ships (AG-12). If demonstrating the new fields on the default `/` view requires minting a fresh
      manifest version, do so via the existing `POST /api/compass/regenerate` action route on the
      frontier `as_of` — never a hand-picked historical date the default view does not show (iter-29's
      documented trap).

### Frontend
- [ ] `apps/frontend/lib/api.ts`: add types for the served `session_delta.rotation` shape (mirror the
      `CompassStateBand`/`CompassStateBandEntry` doc-comment pattern from iter-28) and extend
      `SessionDeltaChange` with the new optional `delta`/`direction_word` fields.
- [ ] `apps/frontend/components/compass-leadership-rotation-section.tsx`: rewrite to render the served
      `session_delta.rotation.{sector,theme}` block — two labelled sides per kind, signed delta text,
      served `direction_word` — instead of filtering `session_delta.changes`. No stock-kind rows. Each
      side's honest empty state (e.g. "no sector lost ground beyond the threshold this session") renders
      when that side is empty, never a blank. The component selects no word, computes no sign, applies no
      threshold — display only.
- [ ] `apps/frontend/components/compass-whatchanged-card.tsx`: NO behavioural or visual change — same
      entries, same order, same thresholds, same suppressed count (verify via the existing J-02 golden).

### New user-facing capability
On the Today page (`/`), a reader can see which sectors and themes are gaining vs. losing leadership
this session — both directions, each with a plain-English direction word — without re-reading the
What-changed list above it, and without any above-threshold mover silently vanishing from the count.

### New information displayed
`session_delta.rotation.{sector,theme}.{gaining,losing}` rows (label, from, to, signed delta, direction
word); each kind's accounting (`shown_count`, `suppressed_count`, `residual_count`, `configured_total`);
signed `delta`/`direction_word` on sector/theme `session_delta.changes` entries.

### New user actions
None new — existing drill-through links (`drill_href`) are reused verbatim.

### UI surface changes
The Leadership rotation section body on `/` (Today) is rewritten; no new page or route.

### Product surface delta
The Today page's Leadership rotation section stops being a duplicate of What-changed and becomes its own
served, both-directions, honestly-accounted view.

### Blueprint conformance
Lives under the existing Today home (`/` — Leadership rotation section), now explicitly registered as a
J-13 row in `state/blueprint.md`'s Feature/journey homes table. No nav-skeleton change.

### Data-contract additions
- `session_delta.rotation.{sector,theme}.gaining` / `.losing`: `list[{label: str, from: int, to: int,
  delta: int (signed), direction_word: str, drill_href: str}]`, each list length `<=
  compass.delta.rotation_top_k`.
- `session_delta.rotation.{sector,theme}.shown_count` / `.suppressed_count` / `.residual_count` /
  `.configured_total`: all `int >= 0`; `shown_count + suppressed_count + residual_count ==
  configured_total` (31 for sector, 11 for theme).
- `session_delta.changes[].delta: int (signed, sector/theme kind only)` and
  `session_delta.changes[].direction_word: str (sector/theme kind only)` — additive optional fields.

All four computed ONCE by `app.engine.compass.build_manifest_payload` (reusing
`app.engine.session_delta.compute_delta`'s sector/theme rank pairs) and served by the existing
`GET /api/compass` — no new producer, no new route. Registered in `state/blueprint.md` as an addition to
the ALREADY-REGISTERED "Next-session manifest — CONTENT block" Data Contract row (iter-36 note appended;
same pattern iter-28 used for `state_band`).

## OUT OF SCOPE

- Any change to `compass.selection.*`, `evaluate_selection`, candidate membership, why-not entries, or
  either frozen cohort (J-12 territory — binding "Do not redo").
- Any change to an existing `compass.delta.*` threshold VALUE (`rank_move_min`, `top_k`,
  `market_score_min_change`, `breadth_min_change_pts`, `stock_score_min_change`,
  `velocity_flat_band`/`stress_velocity_flat_band`) — only the new `rotation_top_k` is added (AG-15).
- Stock-kind rows inside `session_delta.rotation` (group-level only, per J-13 step 1's Non-Goal).
- Any `schema_version` bump or new versioned schema file.
- Any mutation of an existing stored `next_session_manifests` row or export file (AG-12/AG-17).
- Any change to `warmup.py`/`prices.py` (J-09 territory — binding "Do not redo").
- Any new nav route, page, or IA change.
- Re-taking J-04's screenshot or recording the six still-owed `[NEW]`-flagged walkthroughs
  (J-02/03/05/06/07/08/12) — evidence capture is never an iteration goal; these ride as passengers if the
  full pipeline's demo step naturally covers them, never as this iteration's purpose.
- The two small non-blocking repairs carried from iter-35 (the `test_manifest_invariants.py:933` risk
  fixture value; the two bare `assert` guards at `compass.py:462`/`:689`) — out of scope unless the
  developer is already touching those exact lines; do not go looking for them.

## DEFINITION OF DONE

- [ ] J-13 passes via browser-qa-agent (both-directions rotation section, signed deltas, honest empty
      sides, zero What-changed duplication, complete accounting)
- [ ] Required-still-passing journeys (J-02, J-04, J-05, J-06, J-07, J-08, J-12) remain green
      (deterministic replay + LLM fallback)
- [ ] No anti-goal violation introduced (AG-11 no new composite score; AG-12 all pre-existing manifests
      byte-identical; AG-15 no threshold VALUE changes; AG-8 no unbounded/whole-table reads)
- [ ] Unit tests pass; no regressions (`test_session_delta.py`, `test_compass.py`,
      `test_manifest_invariants.py`, `test_no_magic_numbers.py`, `test_api_compass.py` all green)
- [ ] Dev handoff written at `docs/handoffs/goal-market-compass-iter-36-dev.md`, citing both fixtures
      named in J-13 step 8 (empty-losing-side fixture; above-threshold-but-capped fixture) by file:line

## TESTING REQUIREMENTS

- Browser: J-13 (primary target); regression sweep of J-02, J-04, J-05, J-06, J-07, J-08, J-12
- Unit/integration: extend `test_session_delta.py` (signed delta, direction_word, rotation grouping,
  accounting closure, no-prior-run state), `test_compass.py`/`test_manifest_invariants.py` (rotation
  embedded in `build_manifest_payload`, schema validation, `content_hash` stability for pre-existing
  rows), `test_no_magic_numbers.py` (confirm `rotation_top_k` is config-only)
- Error cases: missing/None `previous_run` -> explicit no-comparison rotation state, never fabricated;
  zero above-threshold movers on one side -> that side's explicit empty state, other side unaffected; an
  above-threshold mover beyond `rotation_top_k` -> counted in `residual_count`, never dropped and never
  duplicated into `suppressed`

Test-first contract:

- TC-1: given the frontier manifest's `session_delta.changes` (5 sector, 2 theme, 10 stock entries),
  when `GET /api/compass` is called at the latest `as_of`, then the response includes a
  `session_delta.rotation` object with `sector` and `theme` keys and zero stock-kind rows anywhere
  inside it.
- TC-2: given `session_delta.rotation.sector`, when inspected, then it exposes two explicitly labelled
  sides (`gaining`, `losing`), each an array ordered most-moved-first by `|delta|` descending, each with
  length `<= config.compass.delta.rotation_top_k`.
- TC-3: given a sector/theme rank pair where `|cur_rank - prev_rank| < compass.delta.rank_move_min`,
  when the rotation block is built, then that pair appears in neither `gaining` nor `losing`.
- TC-4: given zero above-threshold sector rows on the losing side and at least one on the gaining side,
  when the rotation block is built, then `session_delta.rotation.sector.losing` is an empty array and
  the frontend renders the honest empty-state string for that side while the gaining side renders its
  rows normally (not blank on either side).
- TC-5: given a stored sector rank pair, when its rotation row is built, then `delta` is a signed number
  and `direction_word` is one of `compass.vocabulary.direction_words`' three values, with a FALLING rank
  number (`cur_rank < prev_rank`) always producing the "improving" word — spot-checked against the
  from/to values served by `GET /api/sectors` at both as-of dates (one gaining, one losing row) and one
  theme row against `GET /api/themes`.
- TC-6: given the same sector/theme change pairs computed for `session_delta.changes`, when
  `GET /api/compass` is called, then each sector/theme-kind entry inside `session_delta.changes` also
  carries the same signed `delta` and `direction_word` values as its corresponding rotation row.
- TC-7: given 31 configured sector/industry ETFs (`config.etfs.sector` 11 + `industry` 20) and 11
  configured themes, when the rotation block is built for an as-of with prior-run data, then for each
  kind `shown_count + suppressed_count + residual_count == configured_total` (31 for sector, 11 for
  theme) — reproducing this iteration's own measured gap (previously 29/31 for sector) as zero.
- TC-8: given a fixture where more sector rows clear `rank_move_min` than `rotation_top_k` allows on one
  side, when the rotation block is built, then the rows beyond the cap are counted in `residual_count`
  and are absent from both `gaining`/`losing` and `suppressed` — isolating the "capped by
  `rotation_top_k`" condition from the separate "fails `rank_move_min`" condition (iter-35 lesson: a
  multi-condition gate needs a fixture row that isolates each condition).
- TC-9: given the earliest stored run (`previous_run is None`), when `GET /api/compass` is called for
  that as-of, then `session_delta.rotation` renders its explicit no-prior-run state (no deltas, no
  direction words, no fabricated rows), consistent with `session_delta`'s own top-level no-prior-run
  branch.
- TC-10: given the frontier manifest before and after this change, when the existing J-02 What-changed
  browser assertions are re-run, then `session_delta.changes` retains the same entries, the same
  market -> breadth -> sectors -> themes -> stocks order, the same thresholds, and the same
  `suppressed_count` as before this change.
- TC-11: given `compass-leadership-rotation-section.tsx` rendered against a mocked `CompassResponse`
  containing `session_delta.rotation`, when the DOM is inspected, then it shows sector and theme rows
  split into two labelled sides with signed +/- delta text and the served `direction_word`, contains
  zero stock-kind rows, and the dev handoff cites the diff removing the `ROTATION_KINDS`/`.filter(...)`
  client-side logic.
- TC-12: given a manifest produced under this change, when validated against
  `docs/handoffs/trendora-next-session-manifest-v1.schema.json`, then validation passes with no
  `schema_version` bump.
- TC-13: given the pre-existing frozen `next_session_manifests` rows/export files (all versions minted
  before this change), when re-read after this iteration ships, then their stored `content_hash`,
  `manifest_hash`, and `payload_json` bytes are byte-identical to their pre-iteration values.
- TC-14: given the dev handoff's cited fixtures (J-13 step 8), when the extended
  `test_session_delta.py` is run, then (a) a fixture where every threshold-crossing sector mover is a
  gainer produces an explicit empty losing side with the gaining side unaffected, and (b) a fixture
  where an above-threshold mover falls beyond `rotation_top_k` produces a non-zero `residual_count`
  rather than a dropped row — both assertions pass.
- TC-15: given a config with `rotation_top_k` set below the number of `rank_move_min`-clearing sector
  rows, when the rotation gating fixture is authored, then at least one fixture row clears
  `rank_move_min` but is excluded solely by `rotation_top_k` (isolated from a separate row that fails
  `rank_move_min` outright) — preventing the exact confounding shape iter-35's lesson flagged in
  `test_manifest_invariants.py:933`.

## NOTES

- Applied lesson (iter-35): a multi-condition gate/filter needs a fixture row that isolates EACH
  condition — this spec's TC-8/TC-15 exist specifically so `rank_move_min` and the new `rotation_top_k`
  cap are never tested through a single covarying fixture row.
- Applied lesson (iter-29): a create-once/immutable-record feature must be demonstrated on the DEFAULT
  view's date, not a convenient historical one with no manifest — if showing `session_delta.rotation` on
  `/` requires a fresh manifest version, mint it via `POST /api/compass/regenerate` on the frontier
  `as_of`, and confirm the default (`/`, no `asof` param) view itself renders the new fields, not only a
  `?asof=` detour.
- Applied lesson (iter-29/30/31 family): any `journey-scripts/*.json` golden written or rewritten this
  round must have its replay lane re-run AFTERWARD and the real result reported — check mtimes before
  crediting a PASS row as coverage, for J-13's own new golden AND for J-02/J-05/J-06/J-07/J-08/J-12's
  existing goldens if the browser-qa lane touches any of them.
- Assumption logged to `state/assumptions.md` (iter-36 — goal-decomposer): the `delta`/`direction_word`
  addition to `session_delta.changes[]` is scoped to `kind ∈ {sector, theme}` only, not `market`/
  `breadth`/`stock` — see ledger entry for grounds; reversible, additive-only.
- Carried, non-blocking, explicitly out of scope this round (do not chase unless already touching the
  exact lines): `test_manifest_invariants.py:933`'s risk fixture value; the two bare `assert` guards at
  `compass.py:462`/`:689`; `test_no_magic_numbers.py` red on 3 untouched files; J-04's 17-round-owed
  screenshot crop; the six still-owed `[NEW]`-flagged walkthroughs; the iteration-23 throwaway copy
  (7.8 GB); `apps/frontend/.next-verify/` still tracked in git; J-01's automatic re-check asserting less
  than the journey claims; the five older owner questions (J-06 wording, J-01's first two test steps,
  empty "next-session focus" acceptability, MNST recovery-list membership, 12 August's "rebuilt" note);
  confirming the whole iteration lands in git at scoring time.
