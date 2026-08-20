# goal-market-compass-iter-3 Dev Handoff

**Phase:** goal-market-compass-iter-3
**Date:** 2026-08-20
**Agent:** developer
**Status:** complete

## What Was Built

The freeze/integrity pair (J-05, J-06): every close now freezes its next-session manifest into a
stamped, dual-hash-verified, three-cohort immutable record, exported as a byte-identical local JSON
artifact, and safely reproducible on demand as an explicit, never-overwriting new version.

- **Engine identity module** — `app.engine.engine_identity.compute_engine_identity(config)`
  (`apps/backend/app/engine/engine_identity.py`, pre-existing from the interrupted first attempt,
  verified correct and unchanged) hashes the config-listed `provenance.engine_files` content +
  `provenance.config_keys` values into one sha256 digest. Stamped on newly created `ScannerRun` rows
  via `scanner.persist_run_payload` (`apps/backend/app/engine/scanner.py:119`) and embedded in every
  manifest's `generation.engine_identity`.
- **Freeze/integrity schema** — `NextSessionManifest` (`apps/backend/app/models.py:770`) gained the
  full freeze/integrity block additively (`mode`, `version`, `frozen`, `generation_json`,
  `engine_identity`, `candidate_rule_hash`/`cohort_rule_hash`/`manifest_config_hash` + their config
  subsets, `dataset_json`, `universe_json`, `comparison_cohort_json`, `near_threshold_shadow_json`,
  `caveats_json`, `prospective_eligible`, `available_at_utc`, `manifest_hash`, `export_path`); the
  single-column `as_of` unique index became composite `(as_of, version)`
  (`UniqueConstraint` at `models.py:812`; the idempotent DDL swap in `apps/backend/app/db.py:197-212`
  drops `ix_next_session_manifests_as_of` and adds `uq_next_session_manifests_as_of_version`). All new
  columns are registered in `_ADDITIVE_COLUMNS` (`db.py:136, 144-159`) — verified by
  `test_db.py::test_every_model_column_on_existing_table_is_covered_by_additive_registry`.
  `ScannerRun.engine_identity` (`models.py:221`) is the same additive-nullable pattern.
- **Cohort serialization** — `evaluate_selection` (`apps/backend/app/engine/compass.py:479-609`) now
  serializes full frozen-context rows for every non-candidate member: `comparison_cohort` (every
  `non_qualifying`/`excluded_by_cap_pairs` row, reused verbatim as the `below_selection_floor`/
  `excluded_by_cap` disposition split per the BACKGROUND note) and `near_threshold_shadow` (the
  half-open `[shadow.min_score, leadership_min_score)` band, deterministic order, uncapped, a subset of
  `comparison_cohort` by construction). Each row's context (`_cohort_row`, `compass.py:313-361`) is
  read entirely from the run's already-stored `record_json` — `close` from `invalidation.price`,
  `distance_from_52w_high` from the Leadership score's stored `high_proximity` component raw,
  `adv_dollars` from the Risk score's stored `liquidity` component raw (sign-flipped back), `atr_pct`/
  `gap_p95`/`worst_20d`/`distance_to_invalidation` from `risk_budget` — no new data source, no bar read
  (AG-8). Bounded to one per-run `record_json` fetch via `_record_json_by_ticker`
  (`compass.py:275-290`, reused for both candidates and non-candidates) plus one per-run theme-rank
  fetch (`_theme_rank_by_slug`, `compass.py:292-300`) — verified query-bounded (not N+1) by
  `test_manifest_invariants.py::test_tc30_comparison_cohort_uses_a_bounded_query_count_not_per_ticker`
  (`test_manifest_invariants.py:485`, asserts <10 queries for 40 members).
- **Three-path freeze writer, one function** — `_freeze_manifest` (`compass.py:864-1023`) is the SOLE
  writer behind:
  - (a) `get_or_create_manifest(..., producer="ingest_finalize")` (`compass.py:1025-1050`) — the
    ingest-finalize call site (`data_manager.py:4538`), mints version 1, data-driven `mode`
    (`_resolve_mode`, `compass.py:673-682`, TC-18).
  - (b) `get_or_create_manifest(...)` (default `producer="on_demand_get"`) — create-once-on-GET for a
    HISTORICAL (non-frontier) as-of. The CURRENT frontier's manifest is NEVER minted this way — a
    non-finalize caller for the frontier raises `ManifestNotYetFrozen` (`compass.py:634-645,
    1047-1050`), mapped to an honest 404 by the API layer (`api/compass.py:41-47`, J-05 step 7 / TC-8).
  - (c) `regenerate_manifest` (`compass.py:1052-1071`) — the confirm-gated regenerate action; mints
    version N+1 for an EXISTING `as_of`, raising `ManifestNotFoundError`
    (`compass.py:647-654`) when none exists.
  `prospective_eligible` is derived by the pure, fail-closed `_derive_prospective_eligible`
  (`compass.py:797-826`) — every condition (mode, frontier_bar_date==based_on_close, producer, version,
  frozen, available_at_utc, provenance_complete, manifest_hash-presence) is checked independently; ANY
  violation forces `false`. `available_at_utc` (`compass.py:875-876`) is the canonical-serialization
  instant + `compass.manifest.availability_margin_seconds` (never a second `datetime.now()` call, so
  the fence is exactly reproducible against `generated_at`).
- **Dual hashes, split rule identities** — `manifest_hash` (`compass.py:895-896`, `verify_manifest_hash`
  at `compass.py:828-839`) covers the COMPLETE document with only itself excluded, assembled before the
  INSERT. `content_hash` (unchanged from iter-2, `build_manifest_payload`, `compass.py:611-631`) covers
  only `{session_delta, narrative, selection}`. `candidate_rule_hash` (`compass.py:684-694`) covers
  ONLY `rule_version`/`leadership_min_score`/`max_candidates`/the fixed ordering-rule string;
  `cohort_rule_hash` (`compass.py:696-709`) covers `rule_version`/`shadow.min_score`/
  `leadership_min_score`/the disposition vocabulary/the cohort row field list; `manifest_config_hash`
  (`compass.py:711-715`) covers the WHOLE `compass.selection` subtree. Verified by the TC-23 matrix
  (`test_manifest_invariants.py:319-373`): a why-not/qualifier change moves ONLY `manifest_config_hash`;
  `shadow.min_score` alone moves ONLY `cohort_rule_hash`; `leadership_min_score` moves BOTH;
  `max_candidates` moves ONLY `candidate_rule_hash`; a metadata-only regenerate keeps `content_hash`
  equal while `manifest_hash` changes.
- **Export writer** — `_write_export` (`compass.py:841-862`) writes the SAME canonical bytes used for
  `manifest_hash`/storage to `compass.manifest.export_dir` (env override `TRENDORA_COMPASS_EXPORT_DIR`),
  at-ingest mode only, own try/except so an I/O failure never blocks the caller and leaves `export_path`
  NULL (never a half-written file silently treated as present).
- **New action endpoint** `POST /api/compass/regenerate?as_of=<date>&confirm=true`
  (`apps/backend/app/api/compass.py:74-88`) — confirm-gated (400 without `confirm=true`, no row
  created), 404 when no manifest exists yet for `as_of`. `GET /api/compass`
  (`api/compass.py:57-71`) remains the sole read path, extended to serve every new field plus a
  read-time `basis` disclosure (`compass.basis_disclosure`, `compass.py:1083-1099`, comparing
  `source_run_created_at` against the CURRENT stored run — never the dataset-version stamp alone) and a
  `versions` summary list (`api/compass.py:36-53`, `_read_time_additions` shared by both routes so
  neither response shape ever drifts from the other — this exact drift was caught and fixed during live
  testing, see Known Issues).
- **Committed JSON Schema** `docs/handoffs/trendora-next-session-manifest-v1.schema.json` (new,
  draft-07, `schema_version: v1`) — required fields cover mode, producer, `available_at_utc`,
  `prospective_eligible`, both hashes, both rule identities, the three cohorts (with disposition +
  field list), and the caveats block. Validated against a REAL frozen at-ingest manifest and a REAL
  retrospective manifest from the live dev backend (591-symbol universe), and confirmed to reject a
  fixture missing `available_at_utc` (TC-25; `test_manifest_invariants.py:403-434`).
- **Three passenger fixes**: (1) the finalize `refreshed` phase key renamed
  `"next_session_manifest"` → `"next-session_manifest"` (`data_manager.py:4554`, plus the two
  docstring/comment listings at `:2474, :4202`) so the frontend's `s.replace(/_/g, " ")` humanizer
  renders "next-session manifest" (hyphenated) exactly matching J-05 step 1; (2) the ATR caution
  (`compass.py:436-439`, `_candidate_payload`) no longer ends "— sized risk accordingly" — states the
  fact only (TC-34); (3) the banned-language guard now also scans `evaluate_selection`'s candidate
  reason/caution/invalidation/why-not strings (`_scan_selection_language`, `compass.py:364-387`, called
  at the end of `evaluate_selection`, `compass.py:608` — before ANY candidate/why-not is returned).
- **Summary-card float-display fix (TC-36)** — `apps/frontend/lib/format-fact.ts` (new,
  `formatFactValue`): a number renders `.toFixed(2)`, everything else renders via `String(...)`
  unchanged. Applied at `apps/frontend/components/compass-summary-card.tsx:53-56` (was raw
  `String(fact.value)`). Verified live: `regime_score_delta` rendered `6.27` (not
  `6.2700000000000005`-style) against the real backend.
- **Frontend manifest strip** — `apps/frontend/components/compass-manifest-strip.tsx` (new), rendered
  as the last compass card on `/` (`apps/frontend/app/page.tsx`, after `CompassFocusSection`, still
  above `<DashboardBody>`). Mode/version/frozen/prospective-eligible badges, freeze timestamp, four
  truncated-with-title hash chips, dataset/universe stamps, basis-disclosure line, an expandable audit
  table (comparison cohort with disposition column + near-threshold shadow under its own explicit
  research-only label, both carrying the `cohort_semantics` caveat text), a versions list (once >1
  exists), and a confirm-gated "Regenerate manifest" control gated on `asOf !== null` (i.e. actionable
  only while viewing a historical date via the existing sole `?asof` provider — never while on
  "Latest"). AG-13: `generation.preflight_verdict` is deliberately NEVER rendered in this component
  (verified empirically — extracted the full rendered manifest-strip text from the live page and
  confirmed no "GO"/"DEGRADED"/"NO-GO"/"Ready" token appears anywhere in it; those tokens appear only
  in the pre-existing top chrome bar, outside this component).

## Files Changed

- `apps/backend/app/engine/compass.py` — the freeze/integrity writer, cohort serialization, hash
  scoping, export writer, regenerate/list/basis-disclosure functions, `manifest_row_payload`
  reconstruction. (Largely new; see "What Was Built" for line citations.)
- `apps/backend/app/engine/engine_identity.py` — pre-existing (interrupted first attempt), verified
  correct via `test_engine_identity.py`, unchanged.
- `apps/backend/app/engine/scanner.py` — `persist_run_payload` stamps `engine_identity` on new runs
  (`:119`).
- `apps/backend/app/engine/data_manager.py` — finalize call site passes
  `producer="ingest_finalize"` (`:4538`); `"next_session_manifest"` → `"next-session_manifest"` key
  rename (`:2474, :4202, :4554`).
- `apps/backend/app/api/compass.py` — extended `GET /compass`, new `POST /compass/regenerate`, shared
  `_read_time_additions` helper.
- `apps/backend/app/models.py` — `NextSessionManifest` freeze/integrity columns + composite unique
  constraint; `ScannerRun.engine_identity`. (Pre-existing from the interrupted first attempt, verified
  correct.)
- `apps/backend/app/db.py` — `_ADDITIVE_COLUMNS` + `_INDEX_DROPS`/`_INDEX_ADDS` for the above. (Same —
  pre-existing, verified correct.)
- `apps/backend/app/config.py` — `CompassManifestCfg`, `ProvenanceCfg`. (Pre-existing, verified
  correct.)
- `config.yaml` — `compass.manifest.*`, `provenance.*`. (Pre-existing, verified correct.)
- `.gitignore` — added `apps/backend/data/exports/` (the export writer's target dir — a regenerated
  local artifact directory, never a repo artifact, same posture as the DB file; live testing wrote real
  files there and they must never be committed).
- `docs/handoffs/trendora-next-session-manifest-v1.schema.json` — new committed JSON Schema.
- `apps/frontend/lib/api.ts` — extended `CompassResponse` (mode/version/frozen/generation/both rule
  hashes/`manifest_config_hash`/dataset/universe/`comparison_cohort`/`near_threshold_shadow`/
  `prospective_eligible`/`available_at_utc`/`manifest_hash`/`basis`/`versions`); new
  `regenerateManifest(asOf)`.
- `apps/frontend/lib/format-fact.ts` (+ `format-fact.test.ts`) — new, TC-36.
- `apps/frontend/components/compass-summary-card.tsx` — TC-36 fix (uses `formatFactValue`).
- `apps/frontend/components/compass-manifest-strip.tsx` — new.
- `apps/frontend/app/page.tsx` — renders `CompassManifestStrip`.
- Test files: `apps/backend/tests/test_engine_identity.py` (new, 7 tests), `test_manifest_invariants.py`
  (new, 34 tests covering TC-14..TC-25, TC-27, TC-28, TC-30, TC-34), `test_compass.py` (extended —
  replaced the iter-2 negative shadow-cohort test with positive cohort/shadow tests, fixed two
  `get_or_create_manifest` call sites for the new frontier guard), `test_api_compass.py` (extended —
  frontier-freeze fixture helper, 6 new freeze/integrity + regenerate tests), `test_ingest_finalize_compass.py`
  (3 assertions renamed for the key rename).

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/test_compass.py tests/test_api_compass.py tests/test_ingest_finalize_compass.py tests/test_engine_identity.py tests/test_manifest_invariants.py tests/test_no_magic_numbers.py -q`
Result: 81 passed, 1 failed (pre-existing, unrelated — see Known Issues).

Also individually verified: `test_db.py`'s 11 additive-column/index-hygiene node IDs (targeted, not the
full file — the file also carries `loaded_engine`-dependent tests out of this phase's scope), all pass.

Frontend: `npx tsc --noEmit` (zero errors) and a full `npx next build` (into a throwaway
`NEXT_DIST_DIR=.next-verify`, per the project's build guard) both succeed; all 21
`apps/frontend/lib/*.test.ts` node-script suites pass (including the new `format-fact.test.ts`, 7
checks).

### Live verification (not mocked)

Started the real backend (`scripts/start-backend.sh`, port 8255, the full 591-symbol/committed-seed
DB) and frontend (`scripts/start-frontend.sh`, port 3255, a real production build) and exercised the
whole pipeline against real data:

- `GET /api/compass` for the frontier served a real pre-existing iter-2-era manifest honestly
  (`mode: null`, "pre-freeze era" — the manifest strip's own dedicated empty state confirmed correct).
- `POST /api/compass/regenerate` without `confirm` → 400, no row created. With `confirm=true` → minted
  version 2 (then 3, 4, 5 across repeated manual tests), each `mode: at_ingest` (2026-08-12 is still the
  live frontier), `prospective_eligible: false` every time (producer="regenerate" independently forces
  it), each with its own hash/timestamp, version 1 untouched.
- `comparison_cohort` had exactly 539 rows (member_count), `near_threshold_shadow` 26 rows, all real
  tickers with real leadership/entry/risk scores, real sectors, real ATR/gap/52w-high/ADV figures
  (spot-checked HPE: leadership 92.7/A but entry 21.7/E — correctly disposed `below_selection_floor`
  despite the high leadership score, per the spec's literal reuse-the-existing-partition rule).
- **TC-4 end-to-end**: read the actual exported file bytes from disk, re-canonicalized the served
  payload (`GET` response minus `basis`/`versions`), confirmed byte-for-byte equality; recomputed
  `manifest_hash` over the exported bytes (hash field excluded) and confirmed it reproduces the
  embedded value.
- A HISTORICAL `as_of` (2026-08-05, no manifest yet) create-once-minted a `retrospective` manifest with
  `prospective_eligible: false` on first `GET`.
- Browser-driven: navigated to `/`, extracted the full rendered manifest-strip text (all 539+26 cohort
  rows, every badge/chip/caveat) — no readiness/preflight token present anywhere in it. Stepped to
  `?asof=2026-08-05`, clicked "Regenerate manifest", confirmed in the modal, watched the strip update
  in-place to "version 2 / retrospective / not prospective-eligible" with no page reload and no console
  crash.
- Restarted both backend and frontend (kill + relaunch via the project scripts) to confirm no port
  conflicts and no orphaned child processes, per the pre-handoff checklist.

This live pass caught one real bug before handoff: the regenerate route's response initially omitted
`basis`/`versions` (only `GET` had them), which would have crashed the frontend's `CompassManifestStrip`
at runtime the first time a user regenerated (reading `.versions.length` on `undefined`). Fixed by
factoring both fields into the shared `_read_time_additions` helper both routes now call
(`api/compass.py:36-53`).

## Known Issues

- **Pre-existing, out-of-scope test failure**: `test_no_magic_numbers.py::test_engine_calc_code_has_no_magic_numbers`
  fails on literals in `indicators.py`, `forward_testing.py`, `research.py` — none of these files were
  touched this session (`git diff HEAD` against each is empty) or by the interrupted first attempt.
  Confirmed failing on unmodified HEAD too. Not fixed here — out of this phase's scope (goal-market-compass
  iter-3 is J-05/J-06 only).
- **Pre-existing repo hygiene issue (flagged, not fixed)**: `apps/frontend/.next-verify/` — a full
  Next.js production-build output directory (165 files) — is committed in git history at commit
  `75b9fd59`, from an apparently unrelated goal session ("i_can_see_the_wealthy_future_forever") that
  predates this project's current name/scope. I initially deleted it locally as what looked like build
  cruft from my own verification build, discovered via `git status` that it was actually tracked, and
  restored it (`git checkout -- apps/frontend/.next-verify/`) since removing committed files outside
  this phase's scope is not this agent's call. Flagging for the owner/release-manager to decide whether
  to clean it up in a dedicated commit.
- **J-01–J-04 evidence-only walkthroughs (TC-32) and the Risk-off screenshot (TC-33)** are not produced
  by this handoff — they are the demo-narrator/walkthrough-recorder's job per the Testing Requirements
  section (`demo.sh market-compass --session-live`), not the developer agent's.
- **`_write_export`'s rare orphan-file case**: if the DB INSERT loses a create-once race AFTER the
  export file was already written (file write happens before the INSERT so `export_path` can be
  included in one immutable row, per AG-12's no-UPDATE rule), the LOSING caller's file is left on disk
  unreferenced by any row. Local-only, harmless (never served, never counted), not treated as a defect.
- **`caveats.evidence`'s signal name is illustrative**: `_evidence_caveat` checks whether a
  `"compass_selection"` signal is present in the certified-claims ledger's `proven_signals` map
  (real read of `GET /api/evidence`'s producer, never a second proven-ness computation) — this signal
  name is never actually registered within this goal (AG-15/AG-6 forbid it), so the caveat always reads
  "Not yet proven" today. The check is real and would honestly flip if that ever changed, but there is
  no test asserting the exact signal-name choice since goal.md does not specify one.

## Definition of Done — evidence index

- J-05 (TC-1..8): TC-1/TC-2 → `test_api_compass.py::test_compass_route_serves_every_new_field_directly`;
  TC-4 → live verification above + `test_manifest_invariants.py::test_tc22_...` (verify_manifest_hash);
  TC-6 → `scanner.py:119` + `test_engine_identity.py`; TC-7 → `test_compass.py::test_get_or_create_manifest_computes_once_then_serves_from_storage`;
  TC-8 → `test_api_compass.py::test_compass_route_frontier_with_no_manifest_yet_returns_honest_404` +
  `test_compass.py::test_get_or_create_manifest_historical_asof_still_create_once_mints`.
- J-06 (TC-9..25): TC-9/TC-11 → `test_manifest_invariants.py::test_tc15_clear_snapshot_set_and_remove_data_delete_zero_manifest_rows`
  (immutability under a snapshot-set clear); TC-12/TC-13 → `test_api_compass.py::test_regenerate_route_mints_version_2_leaves_version_1_untouched`,
  `test_regenerate_route_requires_confirm_flag`; TC-14..TC-25 → `test_manifest_invariants.py` (see file
  for the full TC-numbered test list, line 79 onward).
- Anti-goals: AG-2/AG-11 (TC-28, TC-34) → `test_manifest_invariants.py:460, :519`; AG-5 (TC-29) →
  `test_compass.py::test_no_network_or_lookahead_imports_in_compass_module` (AST scan, covers the whole
  file including the new freeze writer); AG-8 (TC-30) → `test_manifest_invariants.py:485`; AG-9 (TC-26)
  → same AST scan; AG-13 (TC-31) → live browser text-extraction (see Live verification above); AG-16
  (TC-27) → `test_manifest_invariants.py:440`.
