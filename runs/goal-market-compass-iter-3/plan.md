# goal-market-compass-iter-3 Execution Plan

_Scope check: this iteration is exactly goal.md's own suggested build order's third step ("the
freeze/integrity pair, J-05/J-06") and matches the spec's `Depth: full` line —
`runs/goal-session-market-compass/iter-3/depth-dispatched` already reads `full` (verified), so the
iter-2 ESCALATE root cause (LEAN dispatch against a `Depth: full` spec) does not recur. No drift from
`docs/goal.md`: every IN SCOPE item below traces to a named Data-contract addition, and OUT OF SCOPE
mirrors `docs/phases/goal-market-compass-iter-3.md` verbatim (J-07/J-08 composition, threshold
retuning, J-01 wording, Tapeology coupling, signing/PKI, exchange calendar, companion-universe
profile logic, new composite scores, backlog edits — none of these are touched). `blueprint.md`
(`runs/goal-session-market-compass/state/blueprint.md`) already carries its "iter-3 update" note
(written at spec time) — no orchestrator/developer action needed there, it is a goal-mode state file
not a product file._

## What to Build

- **Engine identity module** (`app.engine.engine_identity`) — `compute_engine_identity(config)`
  hashing the config-listed `provenance.engine_files` + `provenance.config_keys`; stamped on new
  `ScannerRun` rows only (old rows stay NULL) and embedded in every manifest's `generation.engine_identity`.
- **Freeze/integrity block** on `next_session_manifests` — additive columns for mode/version/frozen/
  generation/engine identity/three hashes (+ their verbatim config subsets)/dataset+universe
  stamps/three cohorts/caveats/`prospective_eligible`/`available_at_utc`/`manifest_hash`/`export_path`;
  the single-column `as_of` UNIQUE index becomes a composite `(as_of, version)` UNIQUE index.
- **Comparison cohort + near-threshold shadow** — `evaluate_selection` now serializes full frozen rows
  (not just counts) for every non-candidate member, reusing its existing `non_qualifying` /
  `excluded_by_cap_pairs` partitions as `selection_disposition`.
- **Three-path freeze writer** through one function: (a) ingest-finalize freeze → version 1,
  `mode: at_ingest`, `prospective_eligible` fail-closed-derived; (b) on-demand GET for a non-frontier
  date with no row → unchanged create-once path, now explicit `mode: retrospective`,
  `prospective_eligible: false`; (c) NEW confirm-gated regenerate → version N+1, ALWAYS
  `prospective_eligible: false`, version 1 untouched.
- **New action endpoint** `POST /api/compass/regenerate?as_of=<date>` (confirm-gated) — mints a new
  version through the identical writer; `GET /api/compass` stays the sole read path, extended to serve
  every new field plus a read-time basis disclosure (available/rebuilt/unavailable).
- **Export writer** — same-bytes JSON file under `compass.manifest.export_dir`, at-ingest mode only,
  isolated try/except so an I/O failure never blocks finalize.
- **Committed JSON Schema** `docs/handoffs/trendora-next-session-manifest-v1.schema.json` (new,
  versioned with `compass.manifest.schema_version`).
- **Three passenger fixes** (small, isolated): (1) rename the finalize `refreshed` phase key so its
  humanized "Refreshed:" text reads "next-session manifest" (currently renders "next session manifest"
  — missing hyphen); (2) reword the ATR caution to drop its advice-sounding tail; (3) extend the
  banned-language guard to also scan `evaluate_selection`'s reason/caution/why-not strings, not only
  `build_narrative`'s sentences.
- **Summary-card float-display fix** — a cited fact (e.g. regime-score delta) currently renders a raw
  unrounded float; format for display only, the served/stored value stays full precision.
- **Frontend manifest strip** — new last-of-the-compass-cards section on `/`: mode/version/frozen
  badge, freeze timestamp, identity/hash chips, dataset/universe stamps, `prospective_eligible` chip,
  basis-disclosure line; an expandable audit table (comparison cohort + near-threshold shadow, each
  research-only-labeled with `cohort_semantics` caveat text); a confirm-gated "Regenerate manifest"
  control for a stored non-frontier `as_of`, listing both versions once more than one exists.
- Unit/integration coverage for all twelve named manifest invariants (TC-14..TC-25) plus TC-1..TC-13,
  TC-26..TC-36; dev handoff at `docs/handoffs/goal-market-compass-iter-3-dev.md` citing file:line
  evidence per the Definition of Done.

**Out of scope (explicit, per spec):** J-07/J-08's Today-page final composition and `/market`
relocation; retuning `compass.selection.*` thresholds (AG-15); J-01's destructive test-step wording;
any Tapeology import/call/write (AG-14); cryptographic signing/PKI; any exchange-calendar subsystem;
the future incremental-value study itself; companion/small-mid-cap universe profile behavior; any new
composite/blended score (AG-11); `docs/improvement-backlog.md` edits.

## Agents Required

- developer: yes -- implements both the backend freeze/integrity writer and the frontend manifest
  strip in one pass (this project's roster has a single `developer` agent covering both; no separate
  backend-data/frontend-ux agents exist here) -- backend-data: yes, frontend-ux: yes.

Frontend Present: yes

## Files to Create/Modify

Backend (new):
- `apps/backend/app/engine/engine_identity.py` -- new; `compute_engine_identity(config)`. Add to
  `test_no_magic_numbers.CALC_FILES` (`apps/backend/tests/test_no_magic_numbers.py:57`, alongside
  `"session_delta.py", "compass.py"`) if it introduces any tunable numeric literal.
- `docs/handoffs/trendora-next-session-manifest-v1.schema.json` -- new committed JSON Schema.
- `apps/backend/tests/test_engine_identity.py` -- new.
- `apps/backend/tests/test_manifest_invariants.py` -- new (suggested home for the twelve
  time-safety/immutability/reproducibility/create-once/mode/cohort/eligibility/fence/integrity/
  identity-separation/disposition/schema-conformance tests, TC-14..TC-25); may instead extend
  `test_compass.py` if the developer prefers one file.

Backend (modify):
- `apps/backend/app/models.py` -- `NextSessionManifest` (currently lines 763-793): drop
  `unique=True` from `as_of` (`:787`), add `version`, freeze/integrity JSON+scalar columns per the
  spec's Data-contract list, add `__table_args__ = (UniqueConstraint("as_of", "version", ...),)`
  (precedent: `DailyPrice.__table_args__` at `:91-93`). `ScannerRun` (`:195-215`): add
  `engine_identity: Optional[str] = None`.
- `apps/backend/app/db.py` -- `_ADDITIVE_COLUMNS` (`:108-132`): add every new `next_session_manifests`
  column + `scanner_runs.engine_identity`. `_INDEX_DROPS`/`_INDEX_ADDS` (`:167-173`): drop
  `ix_next_session_manifests_as_of` (verified: currently `CREATE UNIQUE INDEX
  ix_next_session_manifests_as_of ON next_session_manifests (as_of)` in the live dev DB), add the new
  composite unique index, e.g. `CREATE UNIQUE INDEX IF NOT EXISTS
  uq_next_session_manifests_as_of_version ON next_session_manifests (as_of, version)` -- follow the
  idempotent guarded pattern exactly (`_ensure_index_hygiene`, `:176-184`); no destructive rewrite.
- `apps/backend/app/engine/compass.py` (493 lines today) --
  - `evaluate_selection` (`:323-408`): serialize `comparison_cohort` (every `non_qualifying` +
    `excluded_by_cap_pairs` row with frozen context + `selection_disposition`) and
    `near_threshold_shadow` (leadership in `[shadow.min_score, leadership_min_score)`, half-open,
    deterministic order, uncapped) using the SAME bounded `_record_json_by_ticker` pattern (`:217-229`)
    scoped to the one run.
  - `_assert_no_banned_language` (`:175-183`) is currently called only from `build_narrative` (`:208`)
    -- extend `evaluate_selection` to also scan candidate `reasons`/`cautions`/`why_not` strings before
    returning (TC-35; this is the exact gap `lessons.md` iter-2 flags).
  - ATR caution string (`:293-295`, ends "— sized risk accordingly") -- reword to state the fact only.
  - `build_manifest_payload` (`:414-429`) / `get_or_create_manifest` (`:432-481`) / `manifest_row_payload`
    (`:484-493`) -- extend into the three-path freeze writer + read-time basis disclosure described
    above; add the regenerate path.
- `apps/backend/app/engine/scanner.py` -- `persist_run_payload`'s `ScannerRun(...)` construction
  (`:104-116`) gains `engine_identity=engine_identity.compute_engine_identity(cfg)`; the two existing
  IntegrityError guards (`:118-130` flush, `:204-218` commit) are the precedent for the manifest
  writer's own concurrency handling.
- `apps/backend/app/engine/data_manager.py` -- the existing "compass content" finalize phase
  (`:4515-4548`) already calls `compass.get_or_create_manifest` and appends `"next_session_manifest"`
  to `refreshed` (`:4544`); the frontend humanizes this by `s.replace(/_/g, " ")`
  (`apps/frontend/app/data/page.tsx:2653`), which renders "next session manifest" (no hyphen) --
  rename the appended key to `"next-session_manifest"` so it humanizes to "next-session manifest"
  exactly matching J-05 step 1 / TC-1's disclosure text. Update the freeze call to use the new writer
  path. **Must also update** the 3 existing assertions in `test_ingest_finalize_compass.py` (`:69, :90,
  :107`, currently `assert "next_session_manifest" in refreshed`) to the new key string.
- `apps/backend/app/api/compass.py` (26 lines) -- extend `GET /api/compass` to serve new fields +
  basis disclosure; add `POST /api/compass/regenerate?as_of=<date>` (confirm flag required, 4xx on a
  missing manifest, mints via the same writer).
- `apps/backend/app/config.py` -- new `CompassManifestCfg` (schema_version, export_dir,
  availability_margin_seconds default 60, schema path) added as a field on `CompassCfg` (`:2672-2681`,
  pattern: `CompassSelectionShadowCfg`/`CompassSelectionCfg` at `:2591-2637`); update `_default_compass`
  (`:2684+`). New top-level `ProvenanceCfg` (`engine_files: list[str]`, `config_keys: list[str]`) wired
  as `provenance: ProvenanceCfg = Field(default_factory=_default_provenance)` right after
  `compass: CompassCfg = Field(...)` (`:2805`). `universe.resolver_gate` values read from the existing
  `cfg.universe.filters` + `cfg.indicators.min_history_bars` (verified: `universe_resolver.py:100-101,
  :215`) -- never re-typed. `member_count` reuses `evaluate_selection`'s already-computed
  `member_count` (`compass.py:342`) -- no second query. `pool_hash` is a new sha256 over
  `universe_screen.read_pool()`'s rows.
- `config.yaml` -- add `compass.manifest.*` and top-level `provenance.*` blocks (no existing blocks by
  these names today -- verified); `compass.selection.shadow.min_score` (already 75.0 since iter-2) is
  now read for the first time, unchanged.
- `apps/backend/tests/test_compass.py`, `test_api_compass.py`, `test_ingest_finalize_compass.py`,
  `test_db.py`, `test_no_magic_numbers.py` -- extend per TC-1..TC-13, TC-26..TC-36 as applicable to
  each file's existing scope.

Frontend (new):
- `apps/frontend/components/compass-manifest-strip.tsx` -- new. Mirrors the existing
  `compass-summary-card.tsx` / `compass-whatchanged-card.tsx` / `compass-focus-section.tsx` pattern
  (Card, reads only `GET /api/compass`, own honest "unavailable" state on a failed fetch). Uses the
  shared `Disclosure` (`apps/frontend/components/ui/disclosure.tsx`) for the comparison-cohort and
  near-threshold-shadow tables. The confirm-gated "Regenerate manifest" control should reuse the
  established **J-69-pattern confirm modal** (Card + fixed overlay, persistently-visible Confirm button
  outside any scroll region -- there is no Dialog primitive in this project; precedent:
  `RebuildConfirmModal`, `apps/frontend/app/data/page.tsx:1093-1108`), colocated in this same file the
  way `RebuildConfirmModal` is colocated with its caller.
- `apps/frontend/lib/format-fact.ts` (+ `format-fact.test.ts`) -- suggested extraction for the TC-36
  fix (see below) so it is covered by this project's plain-node-script frontend test convention
  (goal.md Constraints: "frontend logic tests are plain node scripts under `apps/frontend/lib/*.test.ts`").

Frontend (modify):
- `apps/frontend/lib/api.ts` -- extend `CompassResponse` with every new field (mode/version/frozen/
  generation/`candidate_rule_hash`/`cohort_rule_hash`/`manifest_config_hash`/dataset/universe/
  `comparison_cohort`/`near_threshold_shadow`/`prospective_eligible`/`available_at_utc`/
  `manifest_hash`/caveats/basis disclosure); add `regenerateManifest(as_of)` POST call following the
  existing `getJSON(withAsOf(...))` fetcher convention.
- `apps/frontend/app/page.tsx` -- render `CompassManifestStrip` as the LAST compass card, still above
  the unchanged `<DashboardBody .../>` (preserves the free in-image AG-3 cross-check `lessons.md`
  flags as worth keeping until J-08).
- `apps/frontend/components/compass-summary-card.tsx` -- **TC-36 fix**: line `:53`
  (`<span className="num text-text">{String(fact.value)}</span>`) is the ONLY call site in the compass
  cluster still doing unformatted `String(...)` on a fact value (verified: every sibling numeric render
  in `compass-focus-section.tsx` / `compass-whatchanged-card.tsx` already uses `.toFixed(1)`/`.toFixed(2)`).
  Replace with a type-aware formatter (number -> rounded display string via the new `lib/format-fact.ts`
  helper, e.g. 2 decimals matching the "-0.20" example; non-number -> `String(...)` unchanged). Do NOT
  change what `facts[].value` carries in the served/stored payload -- display-only.

## UI Evolution

- **New user-facing capability:** from `/`, the owner can see proof that each close's decision brief
  was frozen, stamped, and exported unchanged -- not merely computed and displayed -- and can step to a
  historical date to see that exact frozen content forever (even after a later rebuild), or explicitly
  mint a labeled new version without ever touching the original.
- **New information displayed:** manifest mode/version/frozen badge + freeze timestamp; engine identity
  + both rule-identity hash chips + `manifest_config_hash`; dataset/universe stamps;
  `prospective_eligible` chip; the basis-disclosure line (available/rebuilt/unavailable); the
  comparison-cohort and near-threshold-shadow tables with each row's frozen context + disposition; the
  manifest's caveats text.
- **New user actions:** expand/collapse the manifest audit table; trigger the confirm-gated
  "Regenerate manifest" action for a historical `as_of`.
- **UI surface changes:** `/` gains one new "manifest strip" card/section, the last of the compass
  cards, above the existing, unmodified legacy dashboard body. No page removed, no route added.
- **Navigation changes:** none -- per `blueprint.md`, the manifest strip's expanded table IS the
  manifest audit view; no separate nav route exists for it.

## Visual Requirements

- **Component patterns:** `Card` for the manifest strip (matching `compass-summary-card.tsx` /
  `compass-whatchanged-card.tsx` styling), `Badge` for the mode/version/frozen and
  `prospective_eligible` chips (matching the existing checklist-verdict `Badge` usage in
  `compass-focus-section.tsx`), the shared `Disclosure` component for the audit tables, and the J-69
  in-page confirm-modal pattern (`RebuildConfirmModal` precedent) for "Regenerate manifest" -- no new
  Dialog primitive.
- **Layout:** no new page or route; one additional card appended after the existing Next-session focus
  section, still above `<DashboardBody>`, consistent with the existing compass-card stack.
- **Key visual effects:** none new -- match the project's existing minimal, data-dense, dark styling;
  hash/identity chips are monospace/truncated-with-title (short form per the spec), not decorative.
- **States to handle:** own independent honest "unavailable" state on a failed `/api/compass` fetch
  (matching the other three compass cards' precedent); the basis-disclosure line's three states
  (available / rebuilt / unavailable) rendered distinctly; the audit table's near-threshold-shadow
  section always carries its research-only label + `cohort_semantics` caveat text visible, never
  collapsed into the comparison cohort silently; the confirm modal's pre-confirm and in-flight states.

## Key Test Scenarios

The spec's own TESTING REQUIREMENTS section enumerates TC-1..TC-36 in full with exact given/when/then
wording -- the dev handoff must cite file:line evidence against every one of them. Highest-risk /
easy-to-get-wrong ones to prioritize:

- TC-1/TC-2: finalize discloses a "next-session manifest" phase (hyphenated, per the rename above) and
  `GET /api/compass` serves `mode: at_ingest`, `version: 1`, `frozen: true`, `prospective_eligible:
  true`, a well-formed `available_at_utc`.
- TC-4/TC-22: exported file bytes equal stored `payload_json`; recomputing `manifest_hash` over the
  bytes (hash field excluded) reproduces the embedded value; flipping any byte (including inside
  `prospective_eligible`) fails verification.
- TC-7/TC-9/TC-17: create-once holds on a re-run (no new version minted); an unrelated later backfill
  never changes a stored manifest's bytes/version; two concurrent requests for the same not-yet-computed
  `as_of` yield exactly one committed row.
- TC-12/TC-13: the confirm-gated regenerate action mints version 2 with `prospective_eligible: false`
  even if its mode computes `at_ingest`; without confirming, no row is created; version 1 stays
  byte-identical.
- TC-20 (fail-closed eligibility): each of mode/producer/version/frozen/fence/provenance missing, in
  turn, independently forces `prospective_eligible: false`.
- TC-23 (identity separation): the 4-way config-change matrix (why-not/qualifier cap ->
  `manifest_config_hash` only; `shadow.min_score` -> `cohort_rule_hash` only; `leadership_min_score` ->
  both; `max_candidates` -> `candidate_rule_hash` only) plus metadata-only regeneration (`content_hash`
  stays equal, `manifest_hash` changes).
- TC-24 (disposition partition): every non-selected member carries exactly one closed-vocabulary
  disposition and tallies sum to member count minus candidate count.
- TC-25 (schema conformance): a frozen at-ingest manifest and a retrospective manifest validate against
  the committed schema; a fixture missing any required eligibility/fence/hash field fails validation
  (use the already-available `jsonschema` package, verified installed in the backend venv -- no new
  dependency needed).
- TC-30 (AG-8): `comparison_cohort` over up to ~530 non-candidate rows uses column-projected +
  per-run-bounded `record_json` reads, never a cross-run or whole-table sweep.
- TC-34/TC-35/TC-36: ATR caution reworded; banned-language guard now covers
  `evaluate_selection`'s reason/caution/why-not strings; summary-card float artifact fixed for display
  only.
- Browser (J-05, J-06 -- all UI/API-visible TC-1..TC-13 steps): the finalize disclosure, the manifest
  strip + its audit table, the basis disclosure across remove/backfill/regenerate, and the regenerate
  control -- via browser-qa-agent, with backend + frontend RESTARTED after dev/audit and before
  browser-qa (`lessons.md` iter-1: a stale process previously produced a false "field absent" result for
  exactly this kind of new-served-field change).
- Evidence-only pass (TC-32, TC-33): `[NEW]`-flagged walkthroughs recorded for J-01 through J-04
  (closing the `evidence_makeup` gap iter-2 left open) plus a Risk-off caution screenshot at a stored
  Risk-off `as_of` (2026-03-30, or the nearest stored Risk-off date).
