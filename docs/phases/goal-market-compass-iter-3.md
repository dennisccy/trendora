# Goal Iteration 3 — The freeze/integrity pair: a sealed, stamped, exportable next-session manifest (J-05, J-06)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** market-compass
- **Iteration:** 3
- **Mode:** next
- **Depth:** full
- **Full trigger:** 3 — Prior verdict was ESCALATE (mandatory, no exceptions). Independently also
  matches trigger 1 (structural/cross-cutting): this iteration extends one persisted table's write
  path across ≥4 modules — `app/models.py` + `app/db.py` (schema + the `as_of`-unique →
  `(as_of, version)`-unique index swap enabling multi-version rows), the freeze/regenerate engine
  functions (`app/engine/compass.py`, new `app/engine/engine_identity.py`), the ingest-finalize hook
  (`app/engine/data_manager.py`), and two API routes (`app/api/compass.py` read + new regenerate
  action) — whose joint interaction is covered by no existing test. Also the evaluator's own binding
  depth recommendation for this iteration (not a deviation).
- **Frontend Present:** yes
- **Target journeys:** J-05, J-06 (primary build — the freeze/integrity pair)
- **Required-still-passing journeys:** J-01, J-02, J-03, J-04 (also carry small passenger fixes this
  iteration — evidence capture and two wording fixes; no functional change to their own logic — see
  IN SCOPE and NOTES)
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
  - **AG-14 — No Tapeology coupling:** no imports from, network calls to, or writes into the tapeology
    repository or its services; the handoff is exclusively the local exported artifact and Trendora's own
    served API. *(critical)*
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

Each close now freezes its next-session manifest into a stamped, dual-hash-verified, three-cohort
record that a later rebuild, data removal, config change, or code change can never alter — visible on
`/` as a manifest strip with a full audit table, exported as a byte-identical local file, and safely
reproducible on demand as an explicit, never-overwriting new version.

## BACKGROUND

Iteration 2 ended in ESCALATE not because anything broke, but because the engine dispatched it LEAN
against its own `Depth: full` spec, so the auditor, ux-regression, and walkthrough lanes never ran on
the session's largest change — this iteration's `Depth: full` line and its `Full trigger` metadata must
actually be honored; confirm `iter-3/depth-dispatched` reads `full` before evaluating (lessons.md,
iter-2). The evaluator's binding next-step is to build J-05 and J-06 together at full depth: they are
one mechanism (freeze-and-stamp, then prove it never changes) examined from two acceptance angles, not
two independent risky bets — J-06's every step depends on a manifest J-05 already produced, so
splitting them would mean re-opening the same writer path twice for no isolation benefit (see the
assumption logged below on priority-rubric rule 5). The substrate is de-risked: iter-2 already shipped
the table, the endpoint, the compute-once writer, and — usefully — `evaluate_selection`'s existing
`non_qualifying` / `excluded_by_cap_pairs` partitions are already exactly the `below_selection_floor` /
`excluded_by_cap` disposition split the comparison cohort needs; this iteration mainly serializes full
rows for what was previously only counted.

Two structural risks are called out explicitly because they are easy to miss: (1) the current
`next_session_manifests.as_of` column is single-column UNIQUE (iter-2), which will reject a version-2
regenerate row for the same date unless the constraint becomes composite `(as_of, version)` — this
iteration must swap it using the existing idempotent `_INDEX_DROPS`/`_INDEX_ADDS` /
`_ensure_index_hygiene` pattern (`app/db.py`), not a destructive rewrite; (2) the comparison cohort
needs frozen context (ATR, gap, distance-to-invalidation, etc.) for every non-candidate member of a run
— up to ~530 rows today, versus the existing candidate-only fetch bounded to `max_candidates` — so it
must stay column-projected/bounded to the one run's member set, never a full-table or cross-run
`record_json` sweep (AG-8).

Lessons applied from `lessons.md`: restart backend + frontend after dev/audit and before browser-qa,
since this iteration adds new served fields and a new endpoint (iter-1 lesson — a stale process
previously produced a false "field absent" QA result); assert every new field at the `GET /api/compass`
response layer directly, never behind a fixture gate the acceptance check is meant to prove
independence from (iter-1 lesson); extend the runtime banned-language guard to cover
`evaluate_selection`'s candidate reason/caution/why-not strings, not just `build_narrative`'s sentences
— this is now urgent, not optional, because this iteration freezes and exports exactly those strings
into an immutable artifact (iter-2 lesson, directly "Applies to" this iteration's manifest work); and
preserve the free in-image AG-3 cross-check by keeping the manifest strip on the same `/` page as the
pre-existing tiles it echoes stamps from, since J-08 has not yet separated the two surfaces (iter-2
lesson). Per priority-rubric rule 6, the two owner-open items from the iter-2 evaluation (J-01's
destructive test-step wording; whether the empty next-session-focus list is an accepted honest result)
remain unresolved and are NOT re-planned here — J-05 step 1's own precondition is a *different*,
already seed-safe operation (goal.md marks it "(seed-safe)", and the committed seed now runs through
2026-08-14, so removing/backfilling "the last two trading days" no longer touches unrecoverable
user-added bars the way iter-1's J-01 precondition did), and the freeze mechanism must honestly wrap
whatever the selection yields — including zero candidates — without retuning thresholds (AG-15).

## IN SCOPE

### Backend

- [ ] New module `app.engine.engine_identity` — `compute_engine_identity(config)` hashing the
  config-listed `provenance.engine_files` file list + `provenance.config_keys` config subset; embedded
  in every manifest's `generation.engine_identity` and stamped on newly created `ScannerRun` rows only
  (via `scanner.persist_run_payload`).
- [ ] `ScannerRun.engine_identity` — additive nullable column via the SAME `_ADDITIVE_COLUMNS` pattern
  already used for `dismissed` / `job_id` / `max_drawdown` (`app/db.py`); old rows stay NULL
  ("pre-stamping era"), never backfilled.
- [ ] Extend `next_session_manifests` (`app/models.py`) with additive nullable/defaulted columns for
  the freeze/integrity block: `mode`, `version`, `frozen`, `generation` (JSON), `engine_identity`,
  `candidate_rule_hash` + its config-subset JSON, `cohort_rule_hash` + its config-subset JSON,
  `manifest_config_hash` + its config-subset JSON, `dataset` stamp JSON, `universe` block JSON,
  `comparison_cohort` JSON, `near_threshold_shadow` JSON, `caveats` JSON, `prospective_eligible`
  (typed bool column), `available_at_utc`, `manifest_hash`, `export_path` — via the `_ADDITIVE_COLUMNS`
  pattern. Existing pre-iter-3 rows backfill `version=1`, `mode`/`frozen`/hashes NULL/false — a
  "pre-freeze era" honesty marker, mirroring the `ScannerRun.engine_identity` NULL-legacy precedent —
  never retroactively marked frozen.
- [ ] Replace the single-column UNIQUE index on `next_session_manifests.as_of` with a composite UNIQUE
  `(as_of, version)` constraint (model-level `__table_args__`, precedent: `DailyPrice`'s
  `UniqueConstraint("symbol", "date")`), and add the matching idempotent DDL swap to `_INDEX_DROPS` /
  `_INDEX_ADDS` in `app/db.py` so an existing live DB upgrades cleanly — no destructive table rewrite,
  no existing row's stored values changed.
- [ ] Extend `evaluate_selection` (`app/engine/compass.py`) to serialize FULL frozen-context rows — not
  just counts — for every non-candidate member, reusing its existing `non_qualifying` /
  `excluded_by_cap_pairs` partitions as the `selection_disposition` split
  (`below_selection_floor` / `excluded_by_cap`); this becomes `comparison_cohort`.
  `near_threshold_shadow` is the leadership-banded `[shadow.min_score, leadership_min_score)` subset of
  the same trace (half-open — a name exactly at the floor is candidate-eligible, never shadow),
  deterministic order (leadership desc, ticker), uncapped. Both cohorts read the SAME bounded,
  column-projected + per-run `record_json` pattern `_record_json_by_ticker` already uses for
  candidates, scoped to the one run's member set (AG-8) — never a cross-run or whole-table sweep.
- [ ] Extend the freeze writer (extends `build_manifest_payload` / `get_or_create_manifest`) to compute,
  in one path: data-driven `mode` (`at_ingest` iff no bar dated later than the as-of exists at
  generation, `generation.frontier_bar_date` records the evidence, fails toward `retrospective`);
  `generation` block (`producer`, `frontier_bar_date`, `generated_at`, `preflight_verdict`);
  `candidate_rule_hash` (membership/ordering keys only), `cohort_rule_hash` (cohort-semantics keys,
  including the shared `leadership_min_score` band bound), `manifest_config_hash` (the full
  `compass.selection` subtree) — each stored with its own verbatim config subset; `dataset` stamp;
  `universe` block (pool hash, resolver gate values, member count, `profile: "core"` per goal.md's
  companion-universe forward-compat non-goal); `prospective_eligible` (derived ONCE at write, fail-closed:
  true iff mode `at_ingest` with `frontier_bar_date == based_on_close`, `producer == "ingest_finalize"`,
  `version == 1`, `frozen: true`, a well-formed `available_at_utc`, and complete provenance — never
  recomputed at read, absent field reads false); `available_at_utc` (canonical-serialization instant +
  `compass.manifest.availability_margin_seconds`, never back-dated/recomputed); `manifest_hash` (sha256
  over the canonical full-document serialization with only `manifest_hash` itself excluded, assembled
  pre-INSERT).
- [ ] Compose a `caveats` block once at freeze/regenerate time: the evidence "Not yet proven" caveat
  (sourced from the SAME `GET /api/evidence` ledger status the compass chips already read — never a
  second status), the existing survivorship/sector-basis disclosure text (sourced from the existing
  methodology disclosure module), and a new `cohort_semantics` sentence stating the comparison cohort
  is "a frozen non-selected comparison pool, not a matched or causal control group" plus the shadow
  cohort's near-floor (not near-selection-boundary) clarification.
- [ ] Split the create-once writer into its three producer paths through ONE underlying function: (a)
  ingest-finalize freeze — fires only when the frontier date is in `prog.new_snapshot_dates` and no
  manifest exists yet, mints version 1, `mode: at_ingest`, `frozen: true`; confirm the existing "compass
  content" finalize-phase disclosure / `refreshed.append(...)` entry reads as a "next-session manifest"
  phase per J-05 step 1 (rename the phase label if the humanized `refreshed` string does not already
  read that way); (b) on-demand GET for a non-frontier `as_of` with no row — unchanged create-once path,
  now explicitly `mode: retrospective`, `prospective_eligible: false`; (c) NEW confirm-gated regenerate
  — mints version N+1 for an existing `as_of`, ALWAYS `prospective_eligible: false` (write-once,
  version-shopping-proof: only version 1 minted by the finalize producer can ever be true), its own
  `generation`/`available_at_utc`/`manifest_hash`, version 1 stays untouched and byte-identical. The
  frontier date's manifest is NEVER minted by a plain GET — only (a) or an explicit (c).
- [ ] New action endpoint (e.g. `POST /api/compass/regenerate?as_of=<date>`, confirm-gated — a body/query
  flag, not a bare POST) — calls the SAME writer's regenerate path; returns the new version's payload.
  This is an action route, not a second read path: `GET /api/compass` remains the sole READ endpoint.
- [ ] Extend `GET /api/compass` to serve all new fields, plus a read-time basis disclosure comparing
  `source_run_created_at` + `engine_identity` against the CURRENT stored run for that `as_of` (never the
  dataset-version stamp alone, which a rebuild can reproduce byte-identically) — states available /
  unavailable (source run removed) / rebuilt (source run recreated) — a comparison only, never a
  mutation or a recompute of the frozen content.
- [ ] Export writer: serialize once (`json.dumps(sort_keys=True, default=str)`), store those exact
  bytes, write the SAME bytes to a file under `compass.manifest.export_dir`
  (`TRENDORA_COMPASS_EXPORT_DIR` test override, name only) — at-ingest mode only, per goal.md's
  `modes: at_ingest only` constraint. Own try/except (isolate-and-continue, mirroring the existing
  finalize-phase pattern) so an export I/O failure never blocks or crashes the rest of finalize, and
  never half-writes a row (the row's `export_path` stays NULL on failure — an honest gap, not silent
  corruption).
- [ ] Committed JSON Schema `docs/handoffs/trendora-next-session-manifest-v1.schema.json` (new file,
  versioned in lockstep with `compass.manifest.schema_version`) — required fields: mode, producer,
  the generation block, `available_at_utc`, `prospective_eligible`, `content_hash`, `manifest_hash`,
  engine/dataset/universe provenance, `candidate_rule_hash`, `cohort_rule_hash`, the three cohorts
  (including disposition and the matching-context field list), and the caveats block. A schema change
  is always a NEW versioned file, never an in-place edit.
- [ ] New config: `compass.manifest` (`schema_version`, `export_dir`, `availability_margin_seconds`
  default 60, the committed schema path), `provenance` (`engine_files` list, `config_keys` list); this
  iteration is the first to READ the already-reserved `compass.selection.shadow.min_score` (75.0,
  reserved by iter-2). `compass.py` and `session_delta.py` already joined `CALC_FILES`
  (`apps/backend/tests/test_no_magic_numbers.py`) in iter-2; add `engine_identity.py` too if it
  introduces any tunable numeric literal.
- [ ] Extend `_assert_no_banned_language` coverage (`app/engine/compass.py`) to also scan the candidate
  reason / caution / why-not strings `evaluate_selection` produces, not only `build_narrative`'s
  sentences — these strings are about to be frozen into an exported, immutable artifact.
- [ ] Reword the ATR caution (`compass.py`, currently ends "— sized risk accordingly") so it states the
  fact only, with no advice-sounding tail (AG-2 MINOR finding, iter-2 eval).
- [ ] Fix the summary card's float-display bug: a cited fact currently prints a raw float artifact
  (`-0.20000000000000284` instead of `-0.20`) — round for display only, never change the underlying
  stored/served value.

### Frontend

- [ ] New "manifest strip" section on `/` (last of the compass cards, per goal.md's Product Shape:
  "state band, summary, what-changed, rotation, next-session focus, manifest strip") reading ONLY the
  extended `GET /api/compass` payload — mode/version/frozen badge, freeze timestamp, engine identity +
  both rule-identity hashes (short form) + `manifest_config_hash`, dataset/universe stamps,
  `prospective_eligible` chip, and the basis-disclosure line (available / rebuilt / unavailable) when
  applicable.
- [ ] Expandable audit table inside the manifest strip: candidates (already rendered above), the
  comparison cohort (non-selected pool) with each row's frozen context + disposition, and the
  near-threshold shadow cohort under an explicit research-only label with the `cohort_semantics` caveat
  text visible. No client-side hash computation, disposition derivation, or cohort membership logic —
  every value is read, never re-derived.
- [ ] A confirm-gated "Regenerate manifest" control (actionable only for a stored, non-frontier `as_of`)
  that calls the new regenerate endpoint and then lists both versions with their stamps once more than
  one exists.

### New user-facing capability

From `/`, the owner can now see proof that each close's decision brief was frozen, stamped, and
exported unchanged — not merely computed and displayed — and can step to a historical date to see that
exact frozen content forever, even after a later rebuild, or explicitly mint a labeled new version
without ever touching the original.

### New information displayed

Manifest mode/version/frozen badge and freeze timestamp; engine identity and both rule-identity hash
chips; dataset/universe stamps; `prospective_eligible` chip; the basis-disclosure line
(available/rebuilt/unavailable); the comparison-cohort and near-threshold-shadow tables with each row's
frozen context and disposition; the manifest's caveats text.

### New user actions

Expand/collapse the manifest audit table; trigger the confirm-gated "Regenerate manifest" action for a
historical `as_of`.

### UI surface changes

`/` gains one new "manifest strip" card/section, the last of the compass cards, above the existing,
unmodified legacy dashboard body. No page removed, no route added.

### Product surface delta

Every frontier close's decision brief is now provably frozen and exportable, not just computed and
shown — the manifest strip and its audit table are the visible proof of the twelve invariants this
iteration's tests establish.

### Blueprint conformance

Today section of the Information Architecture: `/` is the already-registered canonical home for "J-05 /
J-06 manifest freeze + immutability" per `blueprint.md`'s Feature/journey homes table — "its expanded
table IS the manifest audit view... no separate nav route exists for it." No nav-skeleton change.

### Data-contract additions

All fields below are embedded in the SAME `GET /api/compass` document, computed by the SAME producer
(the extended `app.engine.compass` freeze writer, plus the new `app.engine.engine_identity` module for
the identity value), stored in the SAME `next_session_manifests` table via additive columns — completing
`blueprint.md`'s already-registered FREEZE/INTEGRITY block row (added at iter-2 as a forward-declared
target), never a second producer or a second read path:

- `mode: "at_ingest" | "retrospective"`, `version: int >= 1`, `frozen: bool`.
- `generation: { producer: "ingest_finalize"|"on_demand_get"|"regenerate", frontier_bar_date:
  string(date)|null, generated_at: string(datetime,UTC), preflight_verdict: string|null,
  engine_identity: string }`.
- `candidate_rule_hash: string` + its verbatim config subset; `cohort_rule_hash: string` + its verbatim
  config subset; `manifest_config_hash: string` + its verbatim config subset.
- `dataset: { stamp: string }`; `universe: { pool_hash: string, resolver_gate: object, member_count:
  int, profile: "core" }`.
- `comparison_cohort: [{ ticker: string, leadership_score: number, leadership_bucket: string,
  entry_quality_score: number, entry_quality_bucket: string, risk_score: number, risk_bucket: string,
  setup_status: string, rank_in_run: int, sector: string|null, theme_memberships: [{ theme: string,
  rank: int }], close: number, atr_pct: { value: number, percentile: number }, distance_from_52w_high:
  number, gap_p95: number, worst_20d: number, distance_to_invalidation: number, adv_dollars: number,
  selection_disposition: "below_selection_floor"|"excluded_by_cap" }]` — count equals member count
  minus candidate count; tallies partition exactly.
- `near_threshold_shadow: [{ ...same frozen context fields as comparison_cohort, minus
  selection_disposition }]` — leadership in `[shadow.min_score, leadership_min_score)`, deterministic
  order, uncapped, a subset of `comparison_cohort` by construction.
- `prospective_eligible: bool` (also a typed DB column for filtering) — fail-closed, write-once (only
  version 1 minted by `ingest_finalize` can ever be true).
- `available_at_utc: string (ISO datetime, UTC)` — never earlier than `generated_at +
  compass.manifest.availability_margin_seconds`.
- `manifest_hash: string` (sha256 hex) — whole-document integrity identity, distinct from the existing
  `content_hash` (research-content identity, unchanged scope).
- `caveats: { evidence: string, survivorship: string, sector_basis: string, cohort_semantics: string }`.
- Export file bytes (`compass.manifest.export_dir`, at-ingest mode only) == stored `payload_json`.
- NEW action endpoint `POST /api/compass/regenerate?as_of=<date>` (confirm-gated) — mints a new version
  through the identical writer; `GET /api/compass` remains the sole read path.

`blueprint.md` is updated this iteration (additive) with the concrete field list above under an
"iter-3 update" note; the row's `[TARGET]` tag flips to LIVE only once the evaluator confirms J-05/J-06
passing with evidence.

## OUT OF SCOPE

- J-07's final Today-page composition: market-state band positioning, readiness/preflight chrome
  separation, perf-budget instrumentation (`reports/perf-budgets.md`), and removing `/api/sectors` /
  `/api/themes` / full-history fetches from page load.
- J-08's `/market` route, dashboard-body relocation, and sidebar reordering — the sidebar keeps its
  current "Dashboard" label this iteration.
- Retuning `compass.selection.*` thresholds (`leadership_min_score` 80.0, `entry_min_score` 70.0,
  `risk_max_score` 60.0) — AG-15 forbids outcome-tuned changes; the owner's open question about the
  empty-focus-list acceptability stays open and unresolved by this iteration.
- Rewording J-01's destructive Remove+backfill test-step wording in `docs/goal.md` — still owner-blocked
  (priority-rubric rule 6), not touched.
- Any Tapeology import, network call, or write (AG-14) — the export writer only ever writes a local
  JSON file; nothing in this iteration consumes or reaches into the Tapeology repository.
- Cryptographic signing or PKI — `manifest_hash` stays a corruption/mutation detector only, never a
  signature; adversarial forgery is explicitly out of scope per goal.md.
- Any exchange-calendar subsystem or session-boundary determination — `available_at_utc` is a
  conservative fence only, never a session-prospectivity claim.
- The future incremental-value / prospective-observation study itself — this iteration only records the
  frozen substrate (candidates + comparison + shadow cohorts, `prospective_eligible`,
  `available_at_utc`).
- Any companion/small-mid-cap universe profile logic — `universe.profile` is a defaulted `"core"`
  forward-compat slot only, no new profile behavior.
- Any new composite/blended candidate or cohort-row score (AG-11) — cohort rows carry only the existing
  three scores/buckets plus the named structural context fields, nothing derived or blended.
- `docs/improvement-backlog.md` edits (B-306 engine-identity, B-1205 stamped exports are realized by
  this iteration's work; marking them is informational provenance only, not part of this spec).

## DEFINITION OF DONE

- [ ] J-05 "Each close freezes one provenance-stamped next-session manifest, exported
  byte-consistently" passes via browser-qa-agent (TC-1..TC-8)
- [ ] J-06 "A frozen manifest never changes" passes via browser-qa-agent (TC-9..TC-25, covering all
  twelve named manifest invariants)
- [ ] Required-still-passing journeys J-01, J-02, J-03, J-04 remain green (deterministic replay + LLM
  fallback — mechanically verified)
- [ ] No anti-goal violation introduced — AG-2 (TC-34, TC-35), AG-5 (TC-29), AG-8 (TC-30), AG-9 (TC-26),
  AG-11 (TC-28), AG-12 (TC-15, TC-17, TC-22), AG-13 (TC-31), AG-16 (TC-27) explicitly checked; AG-1 /
  AG-3 / AG-14 / AG-15 hold by construction (no proven-language touched, values re-read from the same
  stored rows/endpoints throughout, the export writes only a local file nothing consumes, selection
  thresholds stay at their unchanged iter-2 config values)
- [ ] Unit tests pass (file-scoped synthetic fixtures) covering all twelve named manifest invariants
  (TC-14..TC-25); no regression to the shared ingest finalize tail or any pre-existing endpoint
- [ ] J-01–J-04's `evidence_makeup` gap closed: `[NEW]` walkthroughs recorded for all four (TC-32) plus
  the Risk-off caution screenshot (TC-33)
- [ ] ATR caution reworded (TC-34) and the banned-language guard extended to cover candidate
  reason/caution/why-not strings before they are frozen into the manifest (TC-35)
- [ ] Summary card float-display bug fixed (TC-36)
- [ ] Dev handoff written at `docs/handoffs/goal-market-compass-iter-3-dev.md`, citing file:line
  evidence for every new column/module/endpoint and for each of the twelve named invariant tests

## TESTING REQUIREMENTS

- Browser: J-05, J-06 (TC-1..TC-13's UI/API-visible steps — the finalize disclosure, the manifest strip
  and its audit table, the basis disclosure, and the regenerate control), plus J-01–J-04's evidence-only
  walkthrough pass (TC-32) and the Risk-off screenshot (TC-33).
- Unit/integration: the extended `evaluate_selection` cohort/disposition rows; `engine_identity.
  compute_engine_identity`; the freeze writer's mode/version/frozen/`prospective_eligible`/
  `available_at_utc` derivation across all three producer paths; the three-hash computation and scope
  separation; the regenerate action; the read-time basis disclosure; the composite `(as_of, version)`
  unique-index swap on an existing populated DB; the committed JSON Schema validation; the exported-file
  byte-equality + tamper detection. New tests are file-scoped, synthetic-fixture — the full suite takes
  hours and is never run by pipeline agents.
- Error cases:
  - `POST /api/compass/regenerate` for an `as_of` with no existing manifest returns an honest 4xx, never
    fabricates a version.
  - `POST /api/compass/regenerate` called without its confirm flag is rejected; no row is created.
  - A manifest fixture missing any required eligibility/fence/hash field fails schema validation
    (TC-25), never silently passes.
  - An export-directory write failure during ingest finalize is caught by its own try/except, never
    blocks or crashes the rest of `_refresh_ingest_aggregates`, and leaves `export_path` NULL rather
    than a half-written file.
  - `GET /api/compass?asof=<date with no stored run>` still returns the existing honest error/empty
    state (unchanged from iter-2), never a fabricated payload.

Test-first contract: every DEFINITION OF DONE checkbox and every Data-contract addition above maps to
at least one concrete scenario line below.

- TC-1: given `/data` removes the last two trading days of snapshots (seed-safe — the committed seed
  runs through 2026-08-14) and backfills the same range, when the job's finalize tail runs, then it
  discloses a "next-session manifest" phase and the run record's "Refreshed:" line names it.
- TC-2: given the frontier date after that backfill, when `GET /api/compass` is called, then it serves
  `mode: at_ingest`, `version: 1`, `frozen: true`, `prospective_eligible: true`,
  `generation.producer: ingest_finalize`, a `generation.generated_at` timestamp, and a well-formed
  `available_at_utc` not earlier than that timestamp plus `compass.manifest.availability_margin_seconds`.
- TC-3: given the same response, when its provenance fields are read, then `generation.engine_identity`,
  `candidate_rule_hash`, `cohort_rule_hash`, and `manifest_config_hash` each appear with their own
  verbatim config subset, alongside the `dataset` stamp and the `universe` block (pool hash, resolver
  gate values, member count, `profile: "core"`).
- TC-4: given the configured export directory, when the exported file for that `as_of` is read, then
  its bytes equal the served `payload_json`, and recomputing `manifest_hash` over those bytes (with the
  hash field excluded per the canonical rule) reproduces the embedded value.
- TC-5: given the manifest strip on `/`, when its expanded table is opened, then it shows the same
  stamps/counts as the API, the comparison-cohort row count equals member count minus candidate count
  with each row carrying its frozen matching-context fields plus a disposition whose tallies partition
  the cohort exactly, and the near-threshold shadow cohort renders under an explicit research-only label
  with the `cohort_semantics` caveat visible.
- TC-6: given the `ScannerRun` created by the backfill, when its `engine_identity` is compared to an
  older, pre-iteration run's, then the new row carries a non-null stamp and the older row shows the
  pre-stamping NULL state.
- TC-7: given the identical backfill range is re-run, when the manifest for that `as_of` is re-read, then
  no new version is minted — it remains version 1 (create-once holds).
- TC-8: given `GET /api/compass` is requested for an old stored date with no manifest, when the response
  is read, then exactly one `retrospective` manifest is created whose `generation.frontier_bar_date`
  exceeds its `as_of` and which carries `prospective_eligible: false`; a repeat request mints no second
  row; and a plain GET on the current frontier date never mints its manifest (only the finalize freeze or
  an explicit regenerate can).
- TC-9: given J-05's frozen manifest is stored, when a further backfill runs on another, unrelated
  removed date, then the original manifest's payload bytes and version are unchanged, checked via both
  the API read and the export file.
- TC-10: given a seed-safe remove-data spans that manifest's `as_of`, when `GET /api/compass` is called
  afterward, then it still serves the manifest verbatim with a read-time basis disclosure stating the
  underlying run is unavailable — never a 404, never a recompute.
- TC-11: given the removed range is backfilled back, when `GET /api/compass` is called, then the basis
  disclosure flips to available (labeled rebuilt if the run's creation timestamp changed) while the
  manifest bytes stay byte-identical to before.
- TC-12: given the confirm-gated regenerate action is triggered for that `as_of`, when version 2 is
  created, then it carries its own `generation.generated_at`, `available_at_utc`, and `manifest_hash`,
  `prospective_eligible: false` even if its computed mode is `at_ingest`, version 1 remains readable and
  byte-identical with its `prospective_eligible` unchanged, and the UI lists both versions with their
  stamps.
- TC-13: given the regenerate control on `/`, when it is invoked without confirming, then no new version
  row is created.
- TC-14 (time-safety): given post-as-of bars are perturbed or deleted, when the manifest's content is
  rebuilt from the same `as_of`, then `content_hash` is unchanged.
- TC-15 (immutability): given a code audit of every `next_session_manifests` write path, when each is
  inspected, then no UPDATE statement exists anywhere, and `clear_snapshot_set` / the remove-data cascade
  both delete zero manifest rows.
- TC-16 (reproducibility): given two independent builds of the same stored inputs, when their
  `content_hash` values are compared, then they are identical.
- TC-17 (create-once concurrency): given two simultaneous requests for the same not-yet-computed `as_of`,
  when both resolve, then exactly one row is committed and both callers observe the same row.
- TC-18 (mode honesty): given generation-time evidence of a bar dated later than the `as_of`, when the
  mode is computed, then it reads `retrospective`, never `at_ingest`.
- TC-19 (cohort reproducibility): given the frozen rule config and the same stored run, when
  `comparison_cohort` and `near_threshold_shadow` membership are recomputed from a fixture, then both
  reproduce exactly.
- TC-20 (fail-closed prospective eligibility): given a fixture manifest missing, in turn, the
  `at_ingest` mode / `ingest_finalize` producer / version 1 / `frozen: true` / the `available_at_utc`
  fence / any provenance field, when `prospective_eligible` is evaluated for each, then each condition
  independently forces `false`.
- TC-21 (availability-fence conservatism): given a manifest's recorded `generation.generated_at`, when
  its `available_at_utc` is compared, then the fence is never earlier than `generated_at +
  availability_margin_seconds`.
- TC-22 (artifact integrity): given a copied export file, when any single byte is flipped — including
  inside `prospective_eligible` or a provenance field — and `manifest_hash` is recomputed, then
  verification fails.
- TC-23 (rule-identity separation): given four isolated config-only changes — (a) the why-not display
  cap or a caution qualifier, (b) `shadow.min_score` alone, (c) `leadership_min_score`, (d)
  `max_candidates` — when `candidate_rule_hash` and `cohort_rule_hash` are recomputed after each, then
  (a) moves neither (only `manifest_config_hash` moves), (b) moves only `cohort_rule_hash`, (c) moves
  both `candidate_rule_hash` and `cohort_rule_hash` (via the shared band bound), and (d) moves only
  `candidate_rule_hash`; separately, given a metadata-only regeneration of identical content (new
  timestamp, same inputs), then `content_hash` stays equal while `manifest_hash` changes.
- TC-24 (disposition partition): given every non-selected member of a run, when `selection_disposition`
  values are tallied, then every member carries exactly one closed-vocabulary value and the tallies sum
  to member count minus candidate count.
- TC-25 (schema conformance): given the committed schema at
  `docs/handoffs/trendora-next-session-manifest-v1.schema.json`, when a frozen at-ingest manifest, a
  retrospective manifest, and a manifest fixture missing a required eligibility/fence/hash field are
  each validated, then the first two pass and the third fails validation.
- TC-26 (AG-9): given the freeze/export/regenerate code paths, when grepped for
  `requests`/`httpx`/`urllib`/`http(s)://`, then no live network call is introduced.
- TC-27 (AG-16): given the manifest's `caveats.cohort_semantics` text and the frontend audit-view
  labels, when read, then the comparison cohort is labeled "a frozen non-selected comparison pool, not a
  matched or causal control group," the shadow cohort carries its near-floor (not near-selection)
  clarification, and no causal/expectancy wording appears anywhere on the surface.
- TC-28 (AG-11): given the comparison and shadow cohort rows, when scanned for a blended/composite score
  field, then none exists beyond the pre-existing scores/buckets/setup/context fields this spec names.
- TC-29 (AG-5): given the export writer and the regenerate action, when grepped for `forward_returns` or
  any bar dated after the `as_of`, then no such read exists.
- TC-30 (AG-8): given `comparison_cohort` construction over a full run's non-candidate members (up to
  ~530 rows), when its DB access is inspected, then it uses column-projected reads plus a
  per-run-bounded `record_json` fetch (never a cross-run or whole-table sweep), consistent with the
  existing candidate-only fetch pattern.
- TC-31 (AG-13): given the new manifest strip, when its rendered text is scanned, then no
  readiness/preflight token (Ready, Initializing, Backend unavailable, GO, DEGRADED, NO-GO) appears
  inside it, and no market/regime vocabulary appears inside the pre-existing readiness/preflight chrome.
- TC-32: given J-01 through J-04's existing acceptance states, when the `[NEW]`-flagged walkthrough
  recorder runs against each, then all four produce a parseable, viewable recording via `demo.sh
  market-compass --session-live`, closing the `evidence_makeup` gap in `journey-history.json`.
- TC-33: given a stored historical `as_of` with a Risk-off regime label (2026-03-30, or the nearest
  stored Risk-off date if unavailable), when the Next-session focus section renders, then a screenshot
  captures the Risk-off caution on every candidate card.
- TC-34: given the ATR caution string in `compass.py`, when its wording is read, then it no longer ends
  with an imperative/advice-sounding tail ("— sized risk accordingly") and states the fact only.
- TC-35: given `evaluate_selection`'s candidate reason/caution/why-not strings, when scanned by the SAME
  banned-language guard `build_narrative` already uses, then no listed token appears in any of them.
- TC-36: given the summary card's cited-fact float values, when a value like the regime-score delta
  renders, then it displays a rounded, human-readable figure (e.g. "-0.20") rather than a raw
  floating-point artifact ("-0.20000000000000284").

## NOTES

- Confirm `runs/goal-session-market-compass/iter-3/depth-dispatched` reads `full` before evaluating —
  the prior ESCALATE was specifically about this file diverging from the spec's own `Depth:` line
  (lessons.md, iter-2); treat a divergence as an ESCALATE trigger again, not just a note.
- Two items remain owner-blocked from the iter-2 evaluation and are intentionally NOT touched here:
  rewording J-01's destructive Remove+backfill test-step (steps 1-2), and whether the empty
  next-session-focus list on a frontier date with zero qualifying members is an accepted honest result
  (AG-15 forbids retuning the 80/70/60 thresholds from outcomes either way).
- `blueprint.md` is updated (additive) with an "iter-3 update" note listing the concrete FREEZE/INTEGRITY
  field set and clarifying that the new `POST /api/compass/regenerate` action endpoint does not create a
  second read path — `GET /api/compass` stays the sole canonical read. No nav-skeleton change, so no
  `blueprint.reapproval-requested` file is written.
- `docs/improvement-backlog.md` cards B-306 (engine-identity stamping) and B-1205 (stamped exports) are
  directly realized by this iteration's `engine_identity` module and export writer; no separate backlog
  edit is needed here.
- `compass.selection.shadow.min_score` (reserved at 75.0 since iter-2) is read by this iteration's
  shadow-cohort code for the first time — expected, not a violation of iter-2's "not read by any iter-2
  code" note, which only described iter-2's own state.
