# Goal Iteration 2 — Session delta, plain-English summary, and next-session candidates (J-02, J-03, J-04)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** market-compass
- **Iteration:** 2
- **Mode:** next
- **Depth:** full
- **Full trigger:** 1 — Structural/cross-cutting: brand-new engine producer (session delta + narrative + selection trace), a new persisted table, a new ingest-finalize phase, a new API endpoint, and three new home-page cards — touches ≥3 modules (finalize hook, engine producer, API route, frontend `/`) whose interaction (threshold suppression, fact-citation, selection-trace reproducibility) is covered by no existing test. Independently matches goal.md's own loop-mechanics rule ("full when an iteration first lands user-visible UI changes") for J-02/J-03/J-04's first code, and is also the evaluator's own binding recommendation for this iteration (not a deviation).
- **Frontend Present:** yes
- **Target journeys:** J-02, J-03, J-04 (primary build); J-01 (passenger — evidence capture only, no code change)
- **Required-still-passing journeys:** none — no journey in this session has reached `passing` status yet. See NOTES for the shared ingest-finalize-tail regression check this iteration still runs (TC-31) even though it is not a tracked journey.
- **Anti-goal reminders:**
  - **AG-1:** A score, ranking, or "edge" MUST NOT be presented as proven/confident unless it is backed by a
    **passing certified-claim entry** in the evidence ledger (out-of-sample, control-beating). Unbacked
    values MUST render a "not yet proven" state. *(critical)*
  - **AG-2 — Decision-quality only:** never present return promises, price targets, "buy/sell" signals, or alpha
    claims; never place or simulate orders. Candidate framing is "worth monitoring", never advice. *(critical)*
  - **AG-3:** A journey passes ONLY if the **displayed numbers are correct** — they match the engine's computation
    for the same as-of date — not merely that the page renders. *(critical)*
  - **AG-5 — Preserve determinism and no-lookahead:** scoring uses bars ≤ as-of; forward returns use bars > as-of;
    the manifest for close D derives only from state stored at or before D; never introduce lookahead anywhere. *(critical)*
  - **AG-8 — Resilience to data-shape and data-scale change:** widening the data basis must never crash an existing
    page or exhaust memory — consumers of widened fields are re-validated, the UI degrades gracefully (contained
    error boundary, honest "—"/NA placeholder), and unbounded whole-table ORM loads are forbidden (the delta
    engine reads column-projected selects, never full record_json sweeps). *(critical)*
  - **AG-9 — Offline-deterministic ingest:** ingest jobs run only against the committed seed / local provider
    fixtures — no live external network calls or paid data services without an explicit goal.md amendment. *(critical)*
  - **AG-11 — No new composite candidate number:** no "fit", "conviction", "match", "probability of success",
    or any new blended score may be attached to candidates, the market, or the manifest; candidate presentation
    is limited to the existing three scores/buckets, config word maps, and structured reason/caution codes. *(critical)*
  - **AG-12 — Manifest immutability:** a stored `next_session_manifests` row and its exported file are never
    mutated or deleted by any later ingest, rebuild, data removal, config change, or code change; corrections
    happen only as new version rows; a historical view never substitutes a newer manifest. *(critical)*
  - **AG-13 — System-vs-market separation:** readiness/preflight vocabulary (Ready, Initializing, Backend
    unavailable, GO, DEGRADED, NO-GO) must never label market state, and regime/phase vocabulary must never
    label system state; the manifest's market and narrative blocks must contain no readiness tokens. *(critical)*
  - **AG-15 — No outcome-tuned selection:** the selection rule and its thresholds must not be chosen or revised
    from realized forward returns within this goal; no Evidence Claim is introduced for it; any future
    selection-edge claim goes through the pre-registration registry and referee. *(critical)*
  - **AG-16 — Cohorts are not controls:** the comparison cohort and the near-threshold shadow cohort are frozen
    non-selected pools, not matched or causal control groups; no surface, artifact, or narrative may present
    candidate-vs-cohort differences as causal, as expectancy, or as a certified edge; any incremental-value or
    threshold study over these cohorts requires its own pre-registered experiment (registry + referee) in a
    future goal, consuming only manifests with `prospective_eligible: true` — consumers must fail closed,
    treating anything other than `true` (including an absent field) as ineligible, verifying `manifest_hash`
    over the artifact bytes BEFORE trusting any field (a mismatch rejects the artifact for prospective use),
    and treating an individual downstream observation as prospective only when its event timestamp is
    strictly later than the manifest's `available_at_utc` — `prospective_eligible: true` is necessary but
    not sufficient per observation. *(critical)*

## GOAL

From `/`, without navigating away, the owner can now read what materially changed since the previous
session, a deterministic plain-English summary of the market state with cited facts, and the
next-session candidates each with structured reasons, cautions, and why-not context.

## BACKGROUND

Iteration 1 shipped J-01's sector fallback and methodology disclosure (verified live: 0/539
Unassigned on run 3081, DELL=Technology, GRMN=Consumer Discretionary), but J-01 stayed `partial` on a
pure evidence-capture gap — the browser lane died on a destructive precondition and ran against a
stale backend. The evaluator's binding recommendation for this iteration is full depth, targeting J-02
(What changed), J-03 (Plain-English summary), and J-04 (Next-session candidates) together, because
goal.md's own suggested build order groups them as one "engine cluster" sharing a single manifest
producer (`build_manifest_payload`) — building them as three separate iterations would mean standing
up the same delta/narrative/selection scaffolding three times (priority-rubric rules 3 and 4: they are
each other's unblocker and together form the smallest coherent spec, not three independent risky
changes). Per priority-rubric rule 6, J-01's one remaining human-blocked item — rewording the
destructive Remove+backfill precondition in `docs/goal.md` — is NOT re-planned here; only the
non-destructive evidence capture against the already-existing run 3081 rides along as a passenger
task, together with two small auditor-flagged housekeeping fixes (T1, B2 in
`docs/handoffs/goal-market-compass-iter-1-audit.md`), per priority-rubric rule 7's carry-along
exception (a real iteration is already running, so evidence/hygiene work rides it rather than getting
its own iteration).

Depth: full, matching the evaluator's binding recommendation and independently justified (see Full
trigger above) — this iteration introduces a brand-new engine producer, a new persisted table, a new
ingest-finalize phase, a new API endpoint, and three new cards on the home page. Consecutive lean
iterations dispatched is 0, so hardening cadence is not the reason; this is a genuine brand-new
full-stack journey.

Lessons applied from `lessons.md`: (1) "Browser QA tested a STALE backend" — restart backend and
frontend after dev/audit and before browser-qa, since this iteration adds a new endpoint
(`GET /api/compass`) that the running process must actually serve. (2) "A test that pytest.skip()s...
is not coverage" — assert every new field at the `GET /api/compass` response layer itself, never
behind a fixture-data gate that could silently skip the acceptance check. (3) "Absence-of-feature
claims need a text sweep or a code citation" — QA/audit verifying the pre-existing dashboard content
is undisturbed should use a DOM text sweep or a code diff, not a single screenshot. (4) J-01's
destructive-precondition lesson — none of this iteration's TC's instruct a Remove+backfill; every
as-of-switcher step (TC-6, TC-12, TC-13, TC-21) is read-only navigation over already-stored runs.

## IN SCOPE

### Backend

- [ ] New engine producer `app.engine.session_delta` — computes session-over-session deltas (market /
  breadth / sector / theme / stock) between the current stored run and the immediately preceding
  stored run, config-thresholded (`compass.delta.*`), ordered market → breadth → sectors → themes →
  stocks, with a suppressed-below-threshold list + count and an explicit no-prior-run state for the
  earliest stored run. Reads column-projected `ScannerResult`/`SectorScoreRow`/`ThemeScoreRow` selects
  only (AG-8) — never a full `record_json` sweep.
- [ ] New narrative sentence builder (inside `app.engine.compass`) — deterministic template sentences
  (state, direction, breadth, focus-count, no-comparison variant, NA-velocity variant, retrospective
  stamp), each carrying `{template_id, text, facts}`; word maps and thresholds live only in
  `compass.vocabulary.*` / `compass.delta.*`. Precedent: the `market_phase._recovery_turn_signal`
  reason-branch and `setups._REASONS` string-table shape.
- [ ] New selection trace `app.engine.compass.evaluate_selection` — the transparent candidate-selection
  rule over stored `ScannerResult` rows (`compass.selection.*`: `leadership_min_score`, qualifiers,
  `max_candidates`, deterministic order): candidates with reasons/cautions/checklist/what-would-change/
  invalidation; why-not entries for every non-candidate with failed-condition distances; a disposition
  tally (`below_selection_floor` / `excluded_by_cap`) that partitions member count minus candidate
  count exactly; an explicit `candidates_empty_reason` state when nothing clears the floor; the
  existing Risk-off → no-Actionable entry gate in `classify_setup` stays untouched. No new blended
  score is introduced anywhere in this trace (AG-11).
- [ ] `app.engine.compass.build_manifest_payload` — assembles the three blocks above into one content
  document and computes `content_hash` (sha256 over the sorted-key JSON of the content block only).
- [ ] New config namespaces in `config.yaml`: `compass.delta.*` (thresholds, `top_k`,
  `max_stock_items`), `compass.selection.*` (`rule_version`, `leadership_min_score`, `max_candidates`,
  qualifiers, why-not floor + cap, `shadow.min_score` — the key is reserved now even though the shadow
  cohort itself is not stored or rendered until J-05), `compass.vocabulary.*` (direction/level/score
  word maps). The three new engine modules join `CALC_FILES` in
  `apps/backend/tests/test_no_magic_numbers.py:19`.
- [ ] New table `next_session_manifests`, sized for this iteration only (`as_of`, the three content
  blocks, `content_hash`, `created_at`, a source-run reference) — follow the existing cache-table
  creation pattern (e.g. `MarketPhaseCache`, `apps/backend/app/models.py`) so a fresh DB carries it
  from `create_db_and_tables`. J-05/J-06 extend it with additive columns only (mode, version, frozen,
  provenance, hashes, cohort storage, `prospective_eligible`, `available_at_utc`) — never a schema
  change to the columns this iteration adds, and never an UPDATE path (AG-12 applies from day one).
- [ ] Ingest finalize hook: insert a "compass content" phase in `_refresh_ingest_aggregates`
  (`apps/backend/app/engine/data_manager.py`, between the market-phase warm and the forward-aggregates
  phase — see the ~:4509/:4528 region), computing and storing one row per newly produced frontier date
  if none exists yet; own try/except so a producer failure never blocks or crashes the rest of the
  finalize tail (mirrors the existing per-date isolate-and-continue pattern already in this function).
- [ ] New endpoint `GET /api/compass` (optional `?asof=`) — serves the stored row for the requested
  `as_of`; if none exists yet, computes and stores it once (create-once-on-GET), then serves from
  storage on every subsequent hit for that `as_of` — zero producer calls on a warm read. Reuses
  `snapshot_serving`'s as-of error mapping for a requested `as_of` with no stored run.
- [ ] Housekeeping (carried from iter-1's audit, not new scope): restore the `sector`/`record_json`
  values the TC-8 fixture mutates
  (`apps/backend/tests/test_scoring.py:578`,
  `test_historical_row_sector_not_rewritten_by_pool_fallback`, mutation at `:603-605`) in a `finally`,
  so the session-scoped `loaded_engine` fixture DB is not left polluted for later tests in the file
  sort order.
- [ ] Housekeeping: hoist the per-row `set(valid_sectors)` build in
  `apps/backend/app/engine/universe_screen.py:124` out of the per-row path — build the valid-sector set
  once per scan and pass the materialized set down to `resolve_pool_sector`.
- [ ] Fix the demo/walkthrough recorder's JSON parse error (see
  `reports/phase-goal-market-compass-iter-1-demo-results.md`) so `[NEW]`-flagged walkthroughs record
  successfully again.

### Frontend

- [ ] `/` gains three new sections, each reading only `GET /api/compass` (no client-side threshold
  comparison, delta computation, or word selection): a Summary card (state/direction/breadth/
  focus-count sentences + a "Show cited facts" disclosure), a What-changed card (ordered change list +
  suppressed-moves disclosure + no-prior-run empty state), and a Next-session focus section (candidate
  cards with why/cautions/checklist/what-would-change/invalidation, plus "Not priority" why-not entries
  with distances). Rendered above the existing, unmodified dashboard body on `/`; final section
  ordering and chrome placement (state band, readiness/preflight separation) is J-07's job, and
  removing the old dashboard body from `/` is J-08's job — neither is attempted this iteration.
- [ ] `/methodology`: add a short "Next-session focus" disclosure card referencing the live
  `compass.selection.*` keys plus TermInfo entries for the new words, reusing the existing
  disclosure-card pattern from J-01's `SectorBasisCard` (`apps/frontend/app/methodology/page.tsx`).

### New user-facing capability

From `/`, the owner reads (without navigating) what changed since the last session, a plain-English
read of current market state with cited facts, and a list of next-session candidates each with
structured reasons, cautions, and why-not context — before this iteration none of that existed on any
page.

### New information displayed

Prior-session date + day gap; ordered change entries with threshold/magnitude and a suppressed-moves
count; state/direction/breadth/focus-count narrative sentences with cited facts and template ids;
candidate cards (scores, reasons, cautions, eligibility checklist, invalidation, what-would-change);
"Not priority" why-not entries with failed-condition distances; the selection disposition tally.

### New user actions

Open the "Show cited facts" disclosure; open the "suppressed moves" disclosure; open a candidate
card's checklist / what-would-change panel; use the existing as-of switcher to view a historical or
no-prior-run/no-comparison state (no new navigation control is introduced).

### UI surface changes

`/` gains three new cards (Summary, What-changed, Next-session focus) above the existing, unmodified
dashboard body. `/methodology` gains one new disclosure card. No page is removed and no route is added.

### Product surface delta

`/` becomes materially more informative — a real "what happened, what does it mean, what's worth
watching next" read — while still carrying its full legacy dashboard content underneath, pending J-08's
relocation to `/market`.

### Blueprint conformance

Today section of the Information Architecture: `/` is the already-registered canonical home for J-02
(What-changed card), J-03 (summary card + cited-facts disclosure), and J-04 (Next-session focus
section) per `blueprint.md`'s Feature/journey homes table. No nav-skeleton change — the sidebar keeps
its current "Dashboard" label until J-08's swap.

### Data-contract additions

- `session_delta` object — embedded in `GET /api/compass` under `session_delta`; computed by
  `app.engine.session_delta.compute_delta` (new). Shape:
  `{ prior_as_of: string(date)|null, gap_days: int|null, changes: [{ kind: "market"|"breadth"|
  "sector"|"theme"|"stock", label: string, from: number|string, to: number|string, magnitude: number,
  threshold: number, drill_href: string }], suppressed: [{ kind: string, magnitude: number, threshold:
  number }], suppressed_count: int>=0 }`.
- `narrative` object — embedded in `GET /api/compass` under `narrative`; computed by the new narrative
  sentence builder inside `app.engine.compass`. Shape: `{ sentences: [{ template_id: string, text:
  string, facts: [{ name: string, value: any }] }] }`.
- `selection` object — embedded in `GET /api/compass` under `selection`; computed by
  `app.engine.compass.evaluate_selection` (new). Shape: `{ candidates: [{ ticker: string,
  leadership_word: string, leadership_score: number, entry_word: string, entry_quality_score: number,
  risk_word: string, risk_score: number, reasons: [string], cautions: [string], checklist: [{
  condition: string, threshold: number, actual: number, verdict: "Pass"|"Miss"|"Supportive"|"Neutral"|
  "Unknown"|"NA" }], what_would_change: [{ condition: string, threshold: number, actual: number, met:
  boolean }], invalidation: string }], why_not: [{ ticker: string, failed_conditions: [{ condition:
  string, threshold: number, actual: number, distance: number }] }], disposition_tally: {
  below_selection_floor: int>=0, excluded_by_cap: int>=0 }, candidates_empty_reason: string|null }`.
- `content_hash: string` (sha256 hex) — embedded in `GET /api/compass`; computed by
  `app.engine.compass.build_manifest_payload` over the three blocks above only (excludes any
  generation/provenance metadata, which does not exist yet).
- Storage: new table `next_session_manifests` (columns: `as_of`, the three content blocks,
  `content_hash`, `created_at`, source-run linkage) — minimal iter-2 shape; J-05/J-06 add mode/version/
  frozen/provenance/hash/cohort/export columns additively.

All four registered in `blueprint.md`'s Data Contract this iteration (the "Next-session manifest —
CONTENT block" row) — single computing module `app.engine.compass.build_manifest_payload`, single
serving endpoint `GET /api/compass`. The row is marked `[TARGET — iter-2 build]`, not yet built as of
this spec; it is the evaluator's job to confirm and flip it once verified.

## OUT OF SCOPE

- J-05/J-06's freeze/versioning/immutability apparatus: `mode`, `version`, `frozen`, `generation.*`,
  engine identity stamping, `candidate_rule_hash` / `cohort_rule_hash` / `manifest_config_hash`,
  dataset/universe provenance stamps, `manifest_hash`, `prospective_eligible`, `available_at_utc`, the
  frozen `comparison_cohort` / `near_threshold_shadow` STORAGE and their audit-view rendering, the
  export file writer, the committed JSON Schema
  (`docs/handoffs/trendora-next-session-manifest-v1.schema.json`), the confirm-gated regenerate
  action, and version 2+ handling.
- The manifest strip UI element on `/` (stamps, counts, expanded audit table) — not built this
  iteration; J-04's "shadow cohort appears nowhere in the focus section" assertion is scoped to the
  Next-session focus section only, not to an audit view that does not exist yet.
- J-07's final Today-page composition: market-state band positioning, readiness/preflight chrome
  separation, perf-budget instrumentation (`reports/perf-budgets.md`), and removing `/api/sectors` /
  `/api/themes` / full-history fetches from page load.
- J-08's `/market` route, dashboard-body relocation, and sidebar reordering ("Today" first, "Market"
  second) — the sidebar keeps its current "Dashboard" label this iteration.
- Any change to `universe.pool_sector_aliases` (J-01, settled — stays empty) or to J-01's destructive
  Remove+backfill precondition wording in `docs/goal.md` (pending the owner's decision per the iter-1
  evaluation; this iteration only captures evidence against the already-existing run 3081).
- Any new composite/blended candidate number (AG-11) — candidates present only the existing three
  scores/buckets, config word maps, and structured reason/caution codes.
- Any live network fetch or paid data service (AG-9) — everything reads the committed seed / already-
  stored runs.
- `docs/improvement-backlog.md` edits (marking B-306/B-802/B-804/B-1205) — informational provenance
  only, not part of this spec.

## DEFINITION OF DONE

- [ ] J-02 "What changed" passes via browser-qa-agent (TC-2..TC-7)
- [ ] J-03 "Plain-English summary" passes via browser-qa-agent (TC-8..TC-13)
- [ ] J-04 "Next-session candidates" passes via browser-qa-agent (TC-14..TC-22)
- [ ] J-01 evidence gap closed: `/stocks` screenshot + `[NEW]` walkthrough recorded against run 3081
  (TC-30), and the demo recorder no longer raises a JSON parse error (TC-29)
- [ ] `GET /api/compass` serves from storage with zero producer calls on a warm hit (TC-1)
- [ ] No anti-goal violation introduced — AG-5, AG-8, AG-9, AG-11 explicitly checked (TC-23..TC-26);
  AG-1/AG-2/AG-3/AG-12/AG-13/AG-15/AG-16 hold by construction (no proven-language or advice wording
  added, displayed values match stored rows, the new table has no UPDATE path, no readiness vocabulary
  appears in the new cards, selection thresholds are config-set not outcome-tuned, and no surface
  frames the disposition/why-not data as a causal control this iteration)
- [ ] Unit tests pass (file-scoped synthetic fixtures); no regression to the shared ingest
  finalize tail (TC-31) or to any pre-existing endpoint
- [ ] TC-8 fixture row restored after the test runs; valid-sector set built once per scan, not once per
  row (TC-27, TC-28)
- [ ] Dev handoff written at `docs/handoffs/goal-market-compass-iter-2-dev.md`, citing file:line
  evidence for every new module/table/endpoint and for both housekeeping fixes

## TESTING REQUIREMENTS

- Browser: J-02, J-03, J-04 (TC-2 through TC-22), plus J-01's evidence-only pass (TC-30) and an
  API-level check of the compute-once/serve-from-storage contract (TC-1).
- Unit/integration: `app.engine.session_delta.compute_delta` (threshold suppression, ordering,
  no-prior-run state, quiet-pair state, new-to-universe reporting); the narrative sentence builder
  (template selection, golden byte-identity, banned-language scan, no-comparison/NA-velocity variants,
  retrospective stamp); `app.engine.compass.evaluate_selection` (candidate/why-not partition,
  disposition tally, Risk-off caution branch, empty-candidates fixture); `content_hash` stability
  across rebuilds of identical inputs; the finalize-hook's try/except isolation; the create-once-on-GET
  path; the TC-8 fixture restore (T1); the hoisted valid-sector set (B2). New tests are file-scoped,
  synthetic-fixture — the full suite takes hours and is never run by pipeline agents.
- Error cases:
  - `GET /api/compass?asof=<date with no stored run>` returns an honest error/empty state (reusing
    `snapshot_serving`'s as-of error mapping), never a fabricated payload.
  - A producer exception during ingest finalize is caught by its own try/except and never blocks or
    crashes the rest of `_refresh_ingest_aggregates`.
  - A candidate row missing an expected field (e.g. no `risk_budget.atr_pct`) renders an honest NA / em
    dash for that caution, never a crash (AG-8 posture).
  - A missing required `compass.*` config key fails closed (raises) rather than silently falling back
    to an undeclared magic number.

Test-first contract: every DEFINITION OF DONE checkbox and every Data-contract addition above maps to
at least one concrete scenario line below.

- TC-1: given `GET /api/compass` is called twice in a row for the same `as_of` with the delta/
  narrative/selection producer functions instrumented, when the second call is compared to the first,
  then it returns byte-identical content and the instrumentation records zero additional producer
  calls.
- TC-2: given the latest as-of has a preceding stored run, when `/` loads, then the What-changed card
  header names that prior run's date and the day gap, matching the row immediately preceding the
  current as-of in `GET /api/runs`.
- TC-3: given a change entry's magnitude is at or above its kind's `compass.delta.*` threshold, when
  the What-changed card renders, then the entry appears in the order market → breadth → sectors →
  themes → stocks and its link carries the current `?asof` to its drill surface.
- TC-4: given a change entry's magnitude is below its kind's threshold, when the "suppressed moves"
  disclosure is opened, then that entry is listed there and the disclosed suppressed count equals the
  number of entries listed.
- TC-5: given a stored sector-rank move and a stored leadership-bucket crossing between the two as-of
  dates, when spot-checked against `GET /api/sectors` and `GET /api/stocks` for both dates, then the
  What-changed entries match those stored values exactly.
- TC-6: given the as-of switcher is stepped to the earliest stored run, when `/` loads, then the
  What-changed card renders the explicit no-prior-run state (no deltas, no direction words) with no
  fabricated comparison.
- TC-7: given a fixture pair of consecutive runs with no change above any threshold, when `/` loads for
  the later run, then the card renders the "no meaningful changes" sentence with its suppressed-count
  disclosure, and a symbol present only in the later run is reported as new-to-universe, never as a
  score change.
- TC-8: given the latest as-of, when `/` loads, then the summary card renders the state sentence plus
  the direction, breadth, and focus-count sentences as served text, with no client-composed wording.
- TC-9: given the "Show cited facts" disclosure is opened, when its two spot-checked facts are compared
  to `GET /api/dashboard`'s regime score and `GET /api/market-phase`'s severity for the same as-of,
  then the values match exactly and each sentence lists its `template_id`.
- TC-10: given the same stored run pair and config are built twice, when the golden test compares the
  two builds, then the sentence text and `content_hash` are byte-identical.
- TC-11: given the committed banned-language list (imperative trade verbs, forecast terms,
  causal-attribution phrases), when every rendered summary sentence is scanned, then no listed token
  appears.
- TC-12: given the earliest stored run and a fixture warm-up head with no velocity history, when the
  summary renders for each, then the no-comparison variant and the NA-velocity variant render
  respectively, with no fabricated direction word.
- TC-13: given a retrospective `?asof` on a pre-frontier historical date, when the summary renders,
  then a visible retrospective stamp states it was reconstructed under the current rule/config.
- TC-14: given the latest as-of, when the Next-session focus section renders, then its candidate count
  equals both `GET /api/compass`'s served count and the number named in the summary's focus sentence.
- TC-15: given one candidate card is opened, when its Leadership/Entry/Risk words and scores are
  compared to the `GET /api/stocks` row for that ticker at the same as-of, then the config word-map
  values and the scores/buckets match exactly.
- TC-16: given a candidate's ATR caution, when its value and percentile are compared to that row's
  `risk_budget.atr_pct`, then they match and the invalidation line renders the row's stored
  invalidation note verbatim.
- TC-17: given the eligibility checklist, when its rows are read, then each carries a verdict from the
  fixed set (Pass / Miss / Supportive / Neutral / Unknown / NA) with threshold and actual value, and
  the verdicts jointly reproduce the candidate's inclusion.
- TC-18: given the "what would change this" panel, when the frontend source is audited, then it
  renders only served threshold/current-value/met-unmet fields and no rule table exists in frontend
  code (cited by a code-audit note in the dev handoff).
- TC-19: given the non-candidate members of the same run, when the "Not priority" entries and
  disposition tally are read, then each entry names its failed condition(s) with distances, and
  `below_selection_floor + excluded_by_cap` equals member count minus candidate count for that as-of.
- TC-20: given the near-threshold shadow band members, when the Next-session focus section is
  inspected, then none of them appears as a card, a pick, or an ordering input anywhere in that
  section.
- TC-21: given a stored historical as-of whose regime label is Risk-off (via `GET /api/regime-history`,
  or a synthetic fixture if none exists), when the focus section renders, then every candidate carries
  the `REGIME_RISK_OFF` caution, the market band reads Risk-off, and no entry-advice wording appears.
- TC-22: given a fixture run where no member clears the selection floor, when the focus section
  renders, then it shows the explicit `candidates_empty_reason` state, never a bare empty list.
- TC-23: given the delta/narrative/selection producer code, when grepped for reads of
  `forward_returns` or any bar dated after the as_of, then no such read exists (AG-5).
- TC-24: given the delta and selection producers run over the full universe, when their DB access is
  inspected, then they use column-projected selects only (ticker/scores/buckets/setup), never a full
  `record_json` sweep (AG-8).
- TC-25: given the candidate cards and the served `GET /api/compass` payload, when scanned for a
  blended/composite score field, then none exists beyond the three existing scores/buckets (AG-11).
- TC-26: given the new engine modules and this iteration's diff, when grepped for
  `requests`/`httpx`/`urllib`/`http(s)://`, then no live network call is introduced (AG-9).
- TC-27: given `apps/backend/tests/test_scoring.py`'s
  `test_historical_row_sector_not_rewritten_by_pool_fallback` (TC-8) runs and mutates a `ScannerResult`
  row, when the test completes, then the original `sector` and `record_json` are restored (e.g. in a
  `finally`) and any test later in `loaded_engine`'s session-scoped sort order sees the unmutated row.
- TC-28: given a scan computes pool-sector fallbacks across many rows, when `resolve_pool_sector`'s
  valid-sector set is inspected, then it is built once per scan call, not once per row.
- TC-29: given the demo/walkthrough recorder runs against a `[NEW]`-flagged journey, when it completes,
  then it produces a parseable results file (no JSON parse error, matching the failure recorded in
  `reports/phase-goal-market-compass-iter-1-demo-results.md`).
- TC-30: given run 3081 already exists (as-of 2026-08-12, no data prep needed), when `/stocks`'s Sector
  filter's "Unassigned" option is inspected and a screenshot captured, then the Unassigned share is at
  most 5%, GRMN renders "Consumer Discretionary", and the `[NEW]`-flagged walkthrough records
  successfully.
- TC-31: given the new "compass content" finalize phase is inserted into `_refresh_ingest_aggregates`,
  when a normal backfill runs, then ingest still completes and every pre-existing "Refreshed:" phase
  (market phase warm, forward aggregates, etc.) still reports its prior counts unchanged.

## NOTES

- Restart backend and frontend after the dev/audit steps and before browser-qa — this iteration adds a
  new endpoint (`GET /api/compass`), and iter-1's QA run already hit a stale-process false negative on
  a new API field once this session.
- Assert every new field at the `GET /api/compass` response layer directly; never let an acceptance
  test skip on a fixture-data gate it is meant to prove independence from.
- QA/audit verifying the pre-existing dashboard content on `/` is undisturbed should use a DOM text
  sweep or a code diff, not a single screenshot, per the iter-0 evidence-quality lesson.
- The owner still owes a decision on rewording J-01's destructive Remove+backfill precondition step in
  `docs/goal.md`; this iteration does not depend on it and does not re-attempt the destructive steps.
  2026-08-13/14 bars remain permanently lost from iter-1's run; TC-6/TC-7's "earliest run" / "quiet
  pair" scenarios must use dates within the intact committed basis (seed through 2026-08-12) or
  synthetic fixtures — never a live re-fetch (AG-9).
- `docs/improvement-backlog.md` cards B-802 (rule distances) and B-804 (score diff) are directly
  realized by this iteration's `evaluate_selection` and `session_delta` work; no separate action is
  needed here.
- `blueprint.md`'s Data Contract was updated this iteration (additive): the "Next-session manifest" row
  is split into a CONTENT block (this iteration's build target) and a FREEZE/INTEGRITY block (J-05/
  J-06) — both remain fields of the SAME document from the SAME producer and endpoint, never a second
  computation path. The Stock sector label row was also corrected to reflect that J-01's pool-CSV
  fallback shipped live in iter-1 (it was previously left marked `[TARGET]` after shipping).
