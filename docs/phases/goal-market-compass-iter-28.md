# Goal Iteration 28 — The Today page answers the ten-second read; Market page relocates intact

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** market-compass
- **Iteration:** 28
- **Mode:** next
- **Depth:** full
- **Full trigger:** 4 — brand-new full-stack journey: J-07 is a never-implemented target journey (failing
  since iter-0) requiring BOTH new backend engine work (a real Data-contract addition, `state_band`) AND
  new frontend work (page reorder, new sections, a new route). This matches the evaluator's own binding
  `full` recommendation for iter-28 — no escape condition needed because trigger and recommendation agree.
- **Target journeys:** J-07, J-08
- **Required-still-passing journeys:** J-01, J-02, J-03, J-04, J-05, J-06, J-10, J-11
- **Frontend Present:** yes
- **Anti-goal reminders:**
  - **AG-2 — Decision-quality only:** never present return promises, price targets, "buy/sell" signals, or alpha
    claims; never place or simulate orders. Candidate framing is "worth monitoring", never advice.
  - **AG-3:** A journey passes ONLY if the **displayed numbers are correct** — they match the engine's computation
    for the same as-of date — not merely that the page renders.
  - **AG-8 — Resilience to data-shape and data-scale change:** widening the data basis must never crash an existing
    page or exhaust memory — consumers of widened fields are re-validated, the UI degrades gracefully (contained
    error boundary, honest "—"/NA placeholder), and unbounded whole-table ORM loads are forbidden (the delta
    engine reads column-projected selects, never full record_json sweeps).
  - **AG-9 — Offline-deterministic ingest:** ingest jobs run only against the committed seed / local provider
    fixtures — no live external network calls or paid data services without an explicit goal.md amendment.
  - **AG-11 — No new composite candidate number:** no "fit", "conviction", "match", "probability of success",
    or any new blended score may be attached to candidates, the market, or the manifest; candidate presentation
    is limited to the existing three scores/buckets, config word maps, and structured reason/caution codes.
  - **AG-12 — Manifest immutability:** a stored `next_session_manifests` row and its exported file are never
    mutated or deleted by any later ingest, rebuild, data removal, config change, or code change; corrections
    happen only as new version rows; a historical view never substitutes a newer manifest.
  - **AG-13 — System-vs-market separation:** readiness/preflight vocabulary (Ready, Initializing, Backend
    unavailable, GO, DEGRADED, NO-GO) must never label market state, and regime/phase vocabulary must never
    label system state; the manifest's market and narrative blocks must contain no readiness tokens.

## GOAL

`/` becomes the real ten-second Today read (market-state band → summary → what-changed → leadership
rotation → next-session focus → manifest strip, chrome above) built entirely from served fields, and the
former full dashboard body relocates verbatim and unchanged to a new `/market` route so nothing is lost.

## BACKGROUND

J-06 closed at iter-27; the goal file's own build order and the iter-27 evaluator's next-step both name
J-07 then J-08 as the next work, and the depth recommendation for this iteration is binding `full`
(escalation-earned at iter-26, honored at iter-27, no reason to demote here). J-07 and J-08 are targeted
**together** as one iteration, which is a deliberate deviation from "1-3 journeys, prefer smallest spec" —
reasoned explicitly per the priority rubric: J-07's own Definition of Done requires the regime × phase
cross-view chart to be **absent from `/`** and its link-out to **navigate to `/market` where it renders**
(step 6) — that requires `/market` to exist. J-08's core mechanic is relocating the SAME already-built
`DashboardBody` (glance cards, cross-view card, More-detail section — `apps/frontend/app/page.tsx:161-`)
verbatim into a new `apps/frontend/app/market/page.tsx`, unchanged. Doing the extraction ONCE, atomically,
satisfies both journeys in the same commit and avoids a mid-cycle state where the chart is removed from
`/` with nowhere to land — which would itself trip the Success Criteria's "Nothing is removed" anti-goal.
J-08 itself is comparatively low-risk (a verbatim component move reusing already-tested code and already-
served endpoints, not a data-model change or new computation), so this is one risky journey (J-07, new
engine field + reorder) plus one low-risk companion required to keep the product coherent mid-iteration —
not two risky journeys (rubric item 5 respected in spirit).

Direct inspection of `apps/frontend/app/page.tsx` confirms the compass cards (`CompassSummaryCard`,
`CompassWhatChangedCard`, `CompassFocusSection`, `CompassManifestStrip`) and the legacy `DashboardBody`
(regime/phase glance cards, `PhaseCrossViewCard`, `MoreDetailSection`) are BOTH currently rendered,
stacked, on `/` — no `/market` route exists (`apps/frontend/app/market/` absent), and the sidebar
(`apps/frontend/components/sidebar.tsx:32`) still labels `/` "Dashboard", not "Today". `blueprint.md`'s
Information Architecture already declares both target states (`Today (/)` and `Market (/market)` rows,
tagged `[TARGET]`) from baseline — this iteration fulfills an already-planned nav skeleton, not a new one,
so no `blueprint.reapproval-requested` is needed.

J-07 step 3 requires three served **direction words** (regime, stress, breadth) that do not exist as a
field anywhere today — `app.engine.compass.build_narrative`'s existing `_direction_word` computes only ONE
word, from the regime-score delta, embedded inside a narrative sentence's `facts`, not as a standalone
served field, and nothing computes a severity-velocity or breadth-velocity word at all. This is a genuine,
new Data-Contract addition (`state_band`), computed once at freeze time inside the SAME
`build_manifest_payload` producer (compute-at-ingest, per the goal's own constraint), never at read.

**Lessons applied:** iter-24/iter-25 (`replay-lane.sh` journey-set parsing) — `Target journeys:` and
`Required-still-passing journeys:` each stay on ONE physical line with their `J-NN` tokens on that line,
enforced below. Iter-26's `basis`-reachability lesson (a passing unit test on an unreachable branch is not
coverage) applies directly to the vocabulary-separation and zero-producer-calls claims below — prove them
through the live route/page, not a unit test alone. Iter-27/27b's browser-QA-mints-a-manifest incident
drives the explicit safe-dates constraint in TESTING REQUIREMENTS below, required verbatim by the pump
coordinator note for this dispatch.

## IN SCOPE

### Backend
- [ ] New `state_band` computation (e.g. `app.engine.compass.build_state_band`, or an equivalently named
  function in `app/engine/compass.py`) producing three direction words — `regime`, `stress`, `breadth` —
  each with a signed delta, computed ONCE inside `build_manifest_payload` (compute-at-ingest / create-once,
  same producer as `session_delta` and `narrative`), never recomputed at read:
  - `regime` word/delta: current vs previous stored run's `regime_score` (may reuse the existing
    `_direction_word` helper/config edge — `compass.delta.velocity_flat_band` — unchanged).
  - `stress` word/delta: current vs previous stored run's market-phase `severity` (the "severity velocity"
    the goal text names) — NEW config-thresholded band under `compass.delta.*`; reuses the SAME
    `compass.vocabulary.direction_words` map, never a second word map.
  - `breadth` word/delta: current vs previous stored run's `breadth_above_50dma` — NEW or reused
    config-thresholded band under `compass.delta.*` (may reuse `breadth_min_change_pts`'s edge if that
    reading is sound; document the choice in the dev handoff).
  - No-prior-run case: all three fields render an explicit null/no-comparison state — never a fabricated
    word (mirrors `session_delta`'s and `narrative`'s existing no-prior-run handling).
  - Every new threshold lives in `config.yaml` under `compass.delta.*` (`test_no_magic_numbers.py`
    coverage — `compass.py` is already a `CALC_FILES` entry, no change needed there).
- [ ] Wire `state_band` into the manifest content JSON alongside `session_delta`/`narrative` (same
  `content_hash` scope as other derived-content blocks) and add it additively to
  `docs/handoffs/trendora-next-session-manifest-v1.schema.json` (loosely-typed `{"type": "object"}` entry,
  consistent with how `session_delta`/`narrative` are already declared — additive, not a new schema
  version, consistent with the iter-11/iter-12 precedent of additive field extensions).
- [ ] Fixture tests (`test_ingest_finalize_compass.py` / `test_api_compass.py` style, isolated DB only) for
  `build_state_band`: flat/up/down for each of the three words at and around their config edges, the
  no-prior-run null case, and a route-level test that `GET /api/compass` serves all three fields verbatim.
- [ ] Confirm (existing coverage, no new test needed unless a gap is found) that a warm `GET /api/compass`
  still performs zero producer calls with `state_band` added — it is read from storage like every other
  manifest field.

### Frontend
- [ ] New market-state band section/component on `/` (e.g. `compass-state-band-card.tsx`) rendering the
  regime tile (label + score from `GET /api/dashboard`, direction-word badge from `state_band.regime`) and
  the phase tile (phase + severity + P(bear) from `GET /api/market-phase`, direction-word badge from
  `state_band.stress`) plus the breadth direction word (`state_band.breadth`), each tile's breakdown
  disclosure reusing the existing `ComponentBreakdown` component against the canonical endpoint's
  `components` array (same pattern already used by `RegimeGlanceCard`/`PhaseGlanceCard` — a new component
  for `/`'s distinct band, not a rename of those, which relocate unchanged to `/market`).
- [ ] New "Leadership rotation" section/component reading the ALREADY-served `session_delta.changes` array
  (`GET /api/compass`, the existing Data-Contract row) filtered for display to `kind ∈ {sector, theme,
  stock}` — a presentational grouping, no new computed value, no client-side threshold or word selection.
- [ ] Reorder `/`'s body to: market-state band → summary → what-changed → leadership rotation →
  next-session focus → manifest strip (readiness badge / preflight strip stay in `layout.tsx` chrome,
  unchanged, above the body).
- [ ] Remove `DashboardBody` (and its `RegimeGlanceCard`/`PhaseGlanceCard`/`PhaseCrossViewCard`/
  `MoreDetailSection`) from `apps/frontend/app/page.tsx` and move it VERBATIM into a new
  `apps/frontend/app/market/page.tsx`, preserving the same components, same endpoints, and the same
  persisted `localStorage` keys (`trendora.dashboard.phaseCrossView`, `trendora.dashboard.moreDetail`).
- [ ] `/` stops fetching `/api/sectors` and `/api/themes` on load (only `/market` fetches them now); `/`
  keeps fetching `/api/dashboard`, `/api/market-phase`, `/api/compass`.
- [ ] Add a labelled link-out from `/`'s market-state band to `/market` (replacing the removed cross-view
  chart's on-page position) that navigates to `/market`, where the chart renders.
- [ ] `apps/frontend/components/sidebar.tsx`: rename the `/` nav entry from "Dashboard" to "Today"; add a
  new "Market" entry for `/market` immediately after it; keep every other entry's route/order/label
  unchanged; verify route-active highlighting works for both new/renamed entries.
- [ ] Confirm the global as-of provider (`?asof`) governs both `/` and `/market` unchanged — no second
  `?asof` owner introduced.

### New user-facing capability
A reader can read the whole "what kind of market is this, is it improving, what changed, where is
leadership rotating, what deserves attention next session" story from `/` alone in the goal's specified
top-to-bottom order, without navigating — and can still reach the full former dashboard body, intact, one
click away at `/market`.

### New information displayed
Three new direction words (regime/stress/breadth) with their signed deltas, each traceable to a config
rule and a stored run-over-run comparison; a focused "Leadership rotation" view of the already-served
what-changed entries.

### New user actions
A "Market" sidebar link; a link-out from the state band to `/market`; the existing as-of switcher now also
governs a second page.

### UI surface changes
`/` reordered and slimmed to the compass-only body; new `/market` route carrying the former `/` body
verbatim; sidebar renamed/extended.

### Product surface delta
`/` (Today) becomes the sole ten-second decision surface; `/market` becomes the deep-context page, both
reachable in ≤2 clicks from the persistent nav exactly as `blueprint.md`'s Information Architecture
already specifies.

### Blueprint conformance
Fulfills the already-registered `blueprint.md` Information Architecture rows "Today (/)" and "Market
(/market)" (both tagged `[TARGET]` since baseline) — no nav-skeleton change, no reapproval request.

### Data-contract additions
`state_band` — NEW field group inside the Next-session manifest CONTENT block (extends the
already-registered "Next-session manifest — CONTENT block" Data Contract row's field list; same producer,
same endpoint):
- `state_band.regime.direction_word: string` (one of `compass.vocabulary.direction_words` values) —
  `state_band.regime.delta: float | null` (current minus previous stored `regime_score`)
- `state_band.stress.direction_word: string` (same word map) — `state_band.stress.delta: float | null`
  (current minus previous stored market-phase `severity`)
- `state_band.breadth.direction_word: string` (same word map) — `state_band.breadth.delta: float | null`
  (current minus previous stored `breadth_above_50dma`)
- All three render `null`/no-comparison when no previous run exists (never fabricated).
- **Computed by:** `app.engine.compass.build_manifest_payload` (new `build_state_band`-style helper inside
  it) — the SAME single producer as `session_delta`/`narrative`.
- **Served by:** `GET /api/compass` (existing endpoint, additive response field — no new route).
- "Leadership rotation" introduces NO new value — it reads the already-registered `session_delta.changes`
  array verbatim, filtered client-side for display only.

## OUT OF SCOPE

- The live remove+backfill drill for J-05 step 1 / J-06 steps 1-3 — binding "Do not redo" (iter-26 ledger).
- Deleting manifest row id 26, or any manifest row (AG-12).
- Any J-09 (host resource-fit) work.
- Any change to J-01/J-02/J-03/J-04/J-05/J-06's underlying engine computation — this iteration touches only
  presentation (reorder, filtered display) plus the one new `state_band` addition; their existing computed
  values, endpoints, and stored data are unchanged.
- A new schema_version bump for the manifest schema file (additive field only, per the iter-11/12
  precedent for additive extensions).
- Any `POST /api/compass/regenerate` call, live or otherwise.
- Any live `?as_of` value outside the authorized safe set (see TESTING REQUIREMENTS) — no new manifest row
  may be minted this iteration.
- J-04's screenshot retake and J-05/J-06's walkthroughs remain passenger tasks (not a DoD item) — see NOTES
  for the free-ride opportunity.

## DEFINITION OF DONE

- [ ] J-07 passes via browser-qa-agent: `/` renders the six body sections in the specified order with
  chrome above; tile values, component breakdowns, and direction words all equal their canonical served
  fields; the cross-view chart is absent from `/` and its link-out reaches `/market`; `/` no longer fetches
  `/api/sectors`/`/api/themes`; a warm `GET /api/compass` performs zero producer calls; perf budget
  addendum recorded in `reports/perf-budgets.md`.
- [ ] J-08 passes via browser-qa-agent: `/market` renders the complete former dashboard inventory
  unchanged; sidebar lists Today then Market with correct active-highlighting; a historical `?asof=D`
  shows D's stored values on `/` with a retrospective-labeled manifest, and Latest clears the param.
- [ ] Required-still-passing journeys J-01, J-02, J-03, J-04, J-05, J-06, J-10, J-11 remain green
  (deterministic replay + LLM fallback where no golden exists).
- [ ] No anti-goal violation introduced (AG-2, AG-3, AG-8, AG-9, AG-11, AG-12, AG-13 specifically checked).
- [ ] Unit/fixture tests pass for `build_state_band` and the route-level `state_band` serving; no
  regressions in the targeted per-module backend test files (never the full suite).
- [ ] `blueprint.md`'s Data Contract carries the `state_band` addition (this spec registers it; confirm the
  dev handoff cites the actual field paths landed, in case they differ from this plan).
- [ ] Dev handoff written at `docs/handoffs/goal-market-compass-iter-28-dev.md`.
- [ ] Zero new `next_session_manifests` rows minted by this iteration's live testing (row count re-derived
  AFTER the browser-QA lane finishes, per the iter-27 lesson).

## TESTING REQUIREMENTS

- Browser: J-07 (all 7 steps), J-08 (all 6 steps) — see TC list below.
- Unit/integration: `build_state_band` (or equivalent) fixture tests for all three words × {up, down, flat,
  no-prior-run}; route-level `GET /api/compass` test asserting `state_band` present and value-consistent
  with the fixture's stored runs; targeted files only (never the full pytest suite — resource contract).
- Error cases: backend unreachable on `/` or `/market` renders the existing honest "Backend unavailable"
  state (unchanged pattern, no new fabrication); a missing/NA severity or breadth input renders each
  direction word as an explicit NA/no-comparison state, never a guessed word.

### BINDING LIVE-DATABASE SAFETY CONSTRAINT (read before any browser-qa/live call)

Any live `GET /api/compass?as_of=<D>` for a `D` that does NOT already carry a `next_session_manifests` row
permanently mints a new manifest row (create-once-on-GET) — this is how the browser-QA lane broke the
iter-27 plan's constraint and minted row id 26 (`as_of=2019-03-01`). This iteration authorizes **ZERO new
manifest mints**. Every live browser-qa / QA call this iteration MUST use `as_of` ONLY from this closed set:

- **SAFE:** no `?asof` param (Latest — the current frontier, 2026-08-12, already carries manifests v1-v6).
- **SAFE:** `?asof=2026-08-12` (the J-05/J-06 frontier date, already carries manifests — use for J-08 step 4).
- **SAFE:** `?asof=2025-04-15` (already carries manifests v1-v2, retrospective-labeled — use for J-08 steps
  3, 5, and the "pre-feature historical run date D" requirement).
- **FORBIDDEN — no other `as_of` value, live, this iteration.** In particular, the 7 manifest-less incident
  dates are absolutely off-limits: **2026-05-12, 2026-05-13, 2026-07-10, 2026-07-13, 2026-07-24, 2026-07-27,
  2026-08-03**.
- **FORBIDDEN:** any live call to `POST /api/compass/regenerate`.
- Row-count claims (`next_session_manifests` total) MUST be re-derived AFTER the browser-QA lane finishes,
  never assumed from a before-count (iter-27 lesson).
- Never delete or alter `apps/backend/data/trendora.db-wal`; no cleanup writes to restore prior state.

### Test-first contract

- TC-1: given the latest as-of has a stored previous run, when `GET /api/compass` is called, then the
  response's `state_band.regime.direction_word` is one of `compass.vocabulary.direction_words`' three
  values and `state_band.regime.delta` equals `current_run.regime_score - previous_run.regime_score`.
- TC-2: given the same as-of, when `state_band.stress.delta` is read, then it equals `current_severity -
  previous_severity` from the stored market-phase values, and `stress.direction_word` is the flat-band
  classification of that delta under its config threshold.
- TC-3: given the same as-of, when `state_band.breadth.delta` is read, then it equals
  `current_run.breadth_above_50dma - previous_run.breadth_above_50dma`, banded through its config threshold.
- TC-4: given the earliest stored run (no previous run), when `GET /api/compass` is called, then all three
  `state_band.*.direction_word` fields render an explicit null/no-comparison value, never a fabricated word.
- TC-5: given `/` is loaded at Latest (no `?asof`), when the page renders, then the body shows sections in
  order — market-state band, summary, What changed, Leadership rotation, Next-session focus, manifest
  strip — with the readiness badge and preflight strip present only in the layout chrome above the body.
- TC-6: given `/` is loaded, when the state band's regime tile is inspected, then its label and score equal
  `GET /api/dashboard`'s `regime.label`/`regime.score` for the same as-of, and its direction-word badge
  equals the served `state_band.regime.direction_word`.
- TC-7: given `/` is loaded, when the state band's phase tile is inspected, then phase/severity/P(bear)
  equal `GET /api/market-phase`'s fields, and its direction-word badge equals `state_band.stress.direction_word`.
- TC-8: given `/` is loaded, when the breadth direction word is inspected, then it equals the served
  `state_band.breadth.direction_word`.
- TC-9: given each state-band tile's breakdown disclosure is expanded, when component rows are read, then
  every name and contribution equals the canonical endpoint's `components` array entries verbatim.
- TC-10: given `/` is loaded, when its full rendered text is scanned, then readiness/preflight tokens
  ("Ready", "GO", "DEGRADED", "NO-GO") appear only inside the layout chrome elements and never inside the
  state-band/summary/what-changed/rotation/focus/manifest sections, and regime/phase tokens appear nowhere
  inside the chrome (AG-13).
- TC-11: given `/` is loaded, when the page is inspected, then the regime × phase cross-view chart is
  absent, and the named link-out element navigates to `/market`.
- TC-12: given `/market` is loaded (`?asof=2026-08-12`, SAFE), when the page is inspected, then the regime ×
  phase cross-view card renders with its hide toggle still keyed to `trendora.dashboard.phaseCrossView`.
- TC-13: given `/` loads at Latest, when network requests are captured, then no request to `/api/sectors`,
  `/api/themes`, or any full-history series endpoint fires, and a subsequent warm `GET /api/compass`
  performs zero producer calls (call-count instrumentation cited in the dev handoff).
- TC-14: given `/`'s time-to-interactive and each on-load API latency are measured, when compared to the
  committed budgets in `reports/perf-budgets.md`, then every measurement is within budget and a NEW dated
  addendum is appended (the prior figures are never overwritten).
- TC-15: given the "Leadership rotation" section is rendered, when its entries are inspected, then every
  entry is drawn verbatim from the already-served `session_delta.changes` array filtered to `kind ∈
  {sector, theme, stock}` — no new value, no client-computed word or threshold.
- TC-16: given `/market` is loaded (`?asof=2026-08-12`, SAFE), when its body is inspected, then it renders
  the two glance cards, the cross-view card, and the complete former More-detail inventory (three breadth
  cards, Top Sectors, Candidate Counts, Top Themes, the full Market Phase & Severity card), each reading the
  same endpoints as before the move — no card dropped.
- TC-17: given the sidebar is inspected, when the nav list renders, then "Today" (`/`) is first and
  "Market" (`/market`) is second, each with correct route-active highlighting on its own route.
- TC-18: given `?asof=2025-04-15` (SAFE, already-manifested, pre-feature historical date), when `/` is
  loaded, then the Today tiles show 2025-04-15's stored values, What-changed's header names 2025-04-15's
  predecessor run date, and the manifest strip serves a manifest whose as-of equals 2025-04-15 with a
  visible `retrospective` label.
- TC-19: given `?asof=2026-08-12` (SAFE, the J-05 frontier date), when `/` is loaded, then the manifest
  strip shows the frozen `at_ingest` version-1 stamps for that date.
- TC-20: given `/?asof=2025-04-15` (SAFE) is opened in a fresh tab, when the page first paints, then the
  rendered data is already 2025-04-15-scoped (no latest-then-repaint flash) and sidebar links carry
  `?asof=2025-04-15`.
- TC-21: given the as-of switcher is reset to Latest, when `/` re-renders, then the `?asof` parameter is
  gone from the URL and the strip shows the latest session's frozen (or explicit not-yet-frozen) state.
- TC-22 (safety, binding): given any live browser-qa call this iteration, when an `as_of` value is chosen,
  then it is one of `{no param, "2026-08-12", "2025-04-15"}` only, and no call to
  `POST /api/compass/regenerate` is made — verified by re-deriving the `next_session_manifests` row count
  AFTER the browser-qa lane finishes and confirming it is unchanged from before the lane ran.

## NOTES

- **Free-ride opportunity (non-blocking, do not let it expand scope):** since browser-qa visits `/` this
  iteration anyway, capture full-page screenshots that scroll to include the candidate/focus card — this
  retires J-04's now-10-iteration `evidence_makeup` debt at zero extra cost. Likewise, if the walkthrough
  recording captures all of J-07/J-08's steps cleanly, it may also satisfy J-05/J-06's still-owed
  walkthroughs (rule 7: piggyback evidence on real work, never plan evidence-only work).
- **Config key naming for the new `stress`/`breadth` velocity bands is left to the developer** — reuse an
  existing edge (e.g. `breadth_min_change_pts` for breadth) if the reading is sound, or add a new
  `compass.delta.*` key; either way it must be config-only (no magic numbers) and documented in the dev
  handoff with the exact field paths landed, so the blueprint's Data Contract note can be corrected if the
  shape differs from this plan's `state_band.<band>.direction_word`/`delta` naming.
- **Owner questions still open, non-blocking (carried, unchanged):** J-09's ~2.99 GB acceptability; J-06's
  "underlying run unavailable" wording; J-01's first two test steps; whether an empty "next-session focus"
  is acceptable; whether MNST joins the recovery list. `goal_gate.py`'s duplicate-journey-heading defect
  remains a standing framework note, to be closed before any GOAL_ACHIEVED certification.
- Per standing guidance, `CHAIN_REQUIRE_FULL_DEPTH` and `CHAIN_MAINTENANCE_ISOLATION` stay OFF; this spec
  does not set `Depth enforcement:` or `Maintenance isolation:` (operator-only lines).
