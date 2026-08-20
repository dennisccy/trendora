# goal-market-compass-iter-2 Dev Handoff

**Phase:** goal-market-compass-iter-2
**Date:** 2026-08-20
**Agent:** developer
**Status:** complete

## What Was Built

The "engine cluster" for J-02 (What changed), J-03 (Plain-English summary), and J-04 (Next-session
candidates), sharing one manifest producer, plus J-01's evidence-capture unblocker (the demo recorder
fix) and two carried housekeeping fixes (T1, B2).

- **New engine module `app.engine.session_delta`** — `compute_delta(session, current_run, previous_run,
  config)` (`apps/backend/app/engine/session_delta.py:219`) builds the `session_delta` CONTENT block:
  market → breadth → sector → theme → stock changes, each gated by its kind's `compass.delta.*`
  threshold, plus a `suppressed` list and the explicit no-prior-run state (`prior_as_of`/`gap_days` both
  `null`) for the earliest stored run. `find_previous_run` (`session_delta.py:31`) resolves the
  immediately preceding stored run by `asof_date` (never by insertion order). Reads ONLY
  column-projected `ScannerResult`/`SectorScoreRow`/`ThemeScoreRow` selects (AG-8) — verified by a
  query-text guard test (`test_session_delta.py::test_column_projected_reads_only_no_full_record_json_sweep`)
  that asserts no issued SQL statement mentions `record_json`. Never reads `forward_returns` or a
  bars-after accessor — verified by an `ast`-based static scan of the module's actual code
  (`test_session_delta.py::test_no_forward_returns_or_lookahead_import`), not a naive docstring grep.
  Stock-kind entries are leadership-BUCKET crossings (bounded to `max_stock_items`, most-moved first) or
  new-to-universe members (reported unconditionally, distinctly labeled `"<TICKER> new to universe"`,
  `from: "new"` — never framed as a score change, per TC-7).

- **New narrative sentence builder, inside `app.engine.compass`** — `build_narrative(...)`
  (`apps/backend/app/engine/compass.py:186`) produces the `narrative` CONTENT block: `state`,
  `direction` (or its `direction_no_prior_run` / `direction_na_velocity` variants), `breadth`,
  `focus_count`, and a conditional `retrospective_stamp` (added when `_is_retrospective` finds a LATER
  stored run already exists — `compass.py:174`). Every sentence is `{template_id, text, facts}`; word
  maps/thresholds live only in `compass.vocabulary.*`/`compass.delta.*`. `state`'s facts are read
  directly from `snapshot_serving.dashboard_payload(current_run)` (regime score/label) and
  `market_phase.market_phase_cached(session, as_of, cfg)` (severity/phase/p_bear) — the SAME functions
  the canonical `/api/dashboard` and `/api/market-phase` endpoints call, so a cited fact byte-matches
  those endpoints for the same as-of by construction (TC-9). A `_assert_no_banned_language` runtime
  guard (`compass.py:181`) raises if any rendered sentence contains a `compass.vocabulary.banned_terms`
  token — a live safety net beyond the offline TC-11 scan test.

- **New selection trace `app.engine.compass.evaluate_selection`** (`compass.py:323`) — the transparent
  candidate rule: leadership/entry/risk qualifier checks (`_qualifier_checks`, `compass.py:266`) against
  `compass.selection.*`; `candidates` (checklist + what-would-change + reasons + cautions +
  invalidation, `_candidate_payload` at `compass.py:290`) ranked by leadership score, capped at
  `max_candidates`; `why_not` entries for near-miss non-qualifiers (leadership ≥ `why_not_floor`) and
  every cap-excluded qualifier (whose `failed_conditions` is honestly `[]` — it failed nothing, only the
  cap cut it), capped at `why_not_cap`; a `disposition_tally` that partitions member count minus
  candidate count exactly (`below_selection_floor + excluded_by_cap`); an explicit
  `candidates_empty_reason` when nothing clears the floor. Per-candidate `risk_budget`/`invalidation`
  detail is read via a NEW, self-contained targeted fetch (`_record_json_by_ticker`, `compass.py:216`) —
  deliberately NOT `snapshot_serving.filtered_stock_rows` (which additionally attaches
  `forward_returns`), so this module stays grep-clean of any post-as-of read. No new
  blended/composite score is ever introduced — verified by
  `test_compass.py::test_no_composite_score_field_anywhere` (asserts every numeric field on a candidate
  is one of the three existing scores). The shadow-cohort key (`compass.selection.shadow.min_score`) is
  declared in config but computed/rendered by no code this iteration —
  `test_compass.py::test_shadow_cohort_never_appears_in_selection_payload` proves the string `"shadow"`
  never appears anywhere in a served `selection` payload.

- **`app.engine.compass.build_manifest_payload`** (`compass.py:414`) — assembles the three blocks and
  computes `content_hash = sha256(json.dumps({session_delta, narrative, selection}, sort_keys=True,
  default=str))`. `test_compass.py::test_content_hash_stable_across_identical_rebuilds` proves
  byte-identical rebuilds (TC-10).

- **New config namespaces in `config.yaml`** — `compass.delta.*`, `compass.selection.*`,
  `compass.vocabulary.*` (`config.yaml:1387-1441`), typed/validated via `CompassDeltaCfg`
  (`apps/backend/app/config.py:2553`), `CompassSelectionCfg` (`config.py:2600`),
  `CompassVocabularyCfg` (`config.py:2643`), assembled into `CompassCfg` (`config.py:2672`) and wired
  onto `Config.compass` (`config.py:2805`, default-populated via `_default_compass()` so a config/inline
  fixture predating this block still loads). `session_delta.py`/`compass.py` joined `CALC_FILES` in
  `apps/backend/tests/test_no_magic_numbers.py:44-49` — both files independently confirmed to have ZERO
  float literals and zero forbidden tunable-int literals (see Tests Run below).

- **New table `next_session_manifests`** (`app.models.NextSessionManifest`, `apps/backend/app/models.py:763`)
  — `as_of` (unique), `source_run_id` (FK `scanner_runs.id`), `session_delta_json`, `narrative_json`,
  `selection_json`, `content_hash`, `created_at`. Sized for this iteration only; J-05/J-06 extend it with
  additive columns only, per the docstring. Registered automatically via `create_db_and_tables`
  (`app.models` import in `app/db.py`) — no fresh-DB wiring needed.

- **Ingest finalize hook** — a new "compass content" phase in `_refresh_ingest_aggregates`
  (`apps/backend/app/engine/data_manager.py:4523-4548`), inserted between the market-phase warm and the
  forward-aggregates phase (exactly as specified), mirroring the market-phase loop's own per-date
  isolate-and-continue pattern (`prog.enter_finalize_phase` → per-date `try`/`except MemoryError: break`
  / `except Exception: log+continue` → `logger.info("J-05 finalize-tail phase timing: ...")`). Own
  try/except means a producer failure here never blocks or crashes the rest of the finalize tail —
  proven by `test_ingest_finalize_compass.py::test_compass_content_failure_is_isolated_forward_aggregates_still_runs`
  (monkeypatches `compass.get_or_create_manifest` to raise, asserts `forward_aggregates` still ran and
  no partial row was written). `"next_session_manifest"` added to the `aggregates_refreshed` category
  enum in both docstring locations (`data_manager.py:2474`, `:4202`).

- **New endpoint `GET /api/compass`** (optional `?as_of=`) — `apps/backend/app/api/compass.py`, wired
  into `main.py` (`from app.api import ..., compass, ...` and
  `application.include_router(compass.router, prefix="/api")`). Reuses `snapshot_serving.resolved_run`
  for the SAME as-of error mapping every other endpoint uses (never a fabricated payload for an unknown
  `as_of`). Create-once-on-GET: `compass.get_or_create_manifest` (`compass.py:432`) checks for a stored
  row first; on a miss it computes via `build_manifest_payload` and persists with the SAME
  concurrency-safe IntegrityError-guard pattern `scanner.persist_run_payload` uses (losing concurrent
  INSERT rolls back and returns the already-committed row — never raises, never duplicates, never
  overwrites, satisfying AG-12 from day one even though `frozen`/`version` are J-05/J-06). Zero
  ADDITIONAL producer calls on a warm hit — proven at both the engine layer
  (`test_compass.py::test_get_or_create_manifest_computes_once_then_serves_from_storage`) and the API
  layer (`test_api_compass.py::test_compass_route_computes_once_serves_from_storage_after`, both via a
  monkeypatched call counter around `build_manifest_payload`).

- **`/methodology` "Next-session focus" disclosure** — mirrors J-01's `SectorBasisCard` sibling-key
  pattern exactly (a NEW `compass_selection` key, sibling of `universe_selection`, NOT nested inside it,
  so the J-22 honest-universe gate cannot hide it): `CompassSelectionBasisCfg`
  (`apps/backend/app/config.py:1811`), `MethodologyCfg.compass_selection`
  (`config.py:1883`), `_compass_selection(config)` + its `build_catalog` wiring
  (`apps/backend/app/engine/methodology.py:74-77, 100-108`), config prose + live-`ref` thresholds
  (`config.yaml:1421-1433`), frontend `CompassSelectionCard`
  (`apps/frontend/app/methodology/page.tsx`, rendered right after `SectorBasisCard`). Also added a new
  glossary category `today_compass` ("Today & Next-Session Focus") with four terms — session delta,
  next-session candidate, why-not, retrospective stamp (`config.yaml`, end of the `terms:` list) — the
  "TermInfo entries for the new words" half of the IN SCOPE bullet, discoverable via the SAME glossary
  search every other term uses (live-verified: searching "why-not" on `/methodology` returns exactly
  this new term under "TODAY & NEXT-SESSION FOCUS").

- **`/` gains three new sections** (`apps/frontend/app/page.tsx`), rendered above the existing,
  UNCHANGED `DashboardBody` (same props, same call site — a code diff shows `DashboardBody`'s own
  definition is byte-identical to before this iteration):
  - `CompassSummaryCard` (`apps/frontend/components/compass-summary-card.tsx`) — J-03. Renders
    `narrative.sentences` verbatim + a "Show cited facts" disclosure listing each sentence's facts.
  - `CompassWhatChangedCard` (`compass-whatchanged-card.tsx`) — J-02. Prior-session date + gap, the
    ordered change list (kind badge + label + from→to + drill link carrying `?asof`), the no-prior-run
    state, the quiet-pair "no meaningful changes" state, and a "Suppressed moves (N)" disclosure.
  - `CompassFocusSection` (`compass-focus-section.tsx`) — J-04. Candidate cards (words+scores, reasons,
    cautions, an "Eligibility checklist" disclosure, a "What would change this" disclosure, invalidation
    verbatim) plus a "Not priority (N)" why-not disclosure with per-condition distances. **Code-audit
    note for TC-18**: the checklist/what-would-change rows map ONLY over served
    `condition`/`threshold`/`actual`/`verdict`/`met` fields (`compass-focus-section.tsx:70-93`) — no
    threshold literal or rule table exists anywhere in this file.
  - All three call `fetchCompass` once, added as a fifth independently-tolerant fetch in
    `DashboardPage`'s existing effect (`page.tsx`, mirroring the SAME "critical dashboard + independently
    failable phase/sectors/themes" pattern already there) — each degrades to an honest "unavailable —
    backend not reachable" card (never fabricated) when `compass` is `null`.
  - Extracted the page's local `Disclosure` (native `<details>`) into a shared
    `apps/frontend/components/ui/disclosure.tsx` — it was about to be used a 3rd/4th time by the new
    cards, so this is a right-sized extraction, not new abstraction (rule of three). `page.tsx` now
    imports it; its two existing call sites (Market Regime / Market Phase glance cards) are unchanged.
  - `apps/frontend/lib/api.ts` — added `CompassResponse` + every nested type (`SessionDelta`,
    `SessionDeltaChange`, `Narrative`, `NarrativeSentence`, `CompassSelection`, `CompassCandidate`,
    `WhyNotEntry`, etc.) and `fetchCompass(asof?, signal?)`, following the exact `getJSON`/`withAsOf`
    pattern every other fetcher uses.

- **Demo/walkthrough recorder JSON-parse fix (TC-29)** — root cause per direct investigation: the
  demo-narrator agent emitted a bare JS/Playwright regex literal (`/Filter by sector/i`) as a `name`
  value, which is not valid JSON and broke `json.load` on the whole `phase-goal-market-compass-iter-1-demo.json`
  (line 37). Fixed at the source: added an explicit instruction to the demo-narrator agent's NEUTRAL
  source (`incredible_auto_dev/agents/demo-narrator/body.md`, right after the `target` mapping table)
  forbidding regex literals and requiring the shortest exact-substring quoted string instead, then
  re-rendered `.claude/agents/demo-narrator.md` via
  `python3 scripts/automation/sync-cli-assets.py --cli claude` (confirmed the rendered mirror picked up
  the change: `wrote 1` agent file). Also hand-fixed the already-broken iter-1 artifact
  (`reports/phase-goal-market-compass-iter-1-demo.json:37`, `"name": /Filter by sector/i` →
  `"name": "Filter by sector"`) — re-verified it now parses (`json.load` succeeds, 6 steps). Did NOT add
  a pipeline-level JSON-validation gate in `demo-phase.sh` (a defense-in-depth option considered and
  intentionally left out — the root-cause instruction fix is the actual fix; adding a second, unrequired
  layer would be scope creep for this iteration).

- **Housekeeping T1** (carried from `docs/handoffs/goal-market-compass-iter-1-audit.md`) —
  `apps/backend/tests/test_scoring.py::test_historical_row_sector_not_rewritten_by_pool_fallback`
  (`test_scoring.py:578`) now wraps its mutation in `try`/`finally`, restoring the target row's original
  `sector`/`record_json` and re-committing, so the session-scoped `loaded_engine` DB is never left
  polluted for later tests in the file sort order.

- **Housekeeping B2** (same audit) — `apps/backend/app/engine/universe_screen.py::pool_sector_map`
  (`universe_screen.py:127`) now builds `valid = set(valid_sectors)` ONCE before the per-row loop and
  passes the materialized set to `resolve_pool_sector`, instead of re-`set(...)`-ing inside
  `resolve_pool_sector` on every row. New regression test
  `test_universe_screen.py::test_pool_sector_map_builds_valid_set_once_survives_a_one_shot_iterable`
  passes a one-shot generator as `valid_sectors` and asserts ALL three synthetic pool rows resolve
  (proven to fail on the pre-fix logic via a standalone repro: the old code resolved only the first row
  and silently dropped the rest — see Tests Run).

## Files Changed

Backend:
- `apps/backend/app/engine/session_delta.py` -- new: session-over-session delta producer (J-02)
- `apps/backend/app/engine/compass.py` -- new: narrative builder + selection trace + manifest assembly/storage (J-03/J-04)
- `apps/backend/app/api/compass.py` -- new: `GET /api/compass`
- `apps/backend/main.py` -- register the compass router
- `apps/backend/app/models.py` -- new `NextSessionManifest` table
- `apps/backend/app/config.py` -- new `CompassCfg`/`CompassDeltaCfg`/`CompassSelectionCfg`/`CompassVocabularyCfg`/`CompassSelectionBasisCfg`, wired onto `Config` and `MethodologyCfg`
- `apps/backend/app/engine/data_manager.py` -- new "compass content" finalize phase; `aggregates_refreshed` docstring enum updated
- `apps/backend/app/engine/methodology.py` -- `_compass_selection` sibling-key disclosure
- `apps/backend/app/engine/universe_screen.py` -- B2 fix (hoisted valid-sector set)
- `config.yaml` -- new `compass:` namespace; `methodology.universe_selection.compass_selection` disclosure; new `today_compass` glossary category + 4 terms

Backend tests:
- `apps/backend/tests/test_session_delta.py` -- new, 12 tests
- `apps/backend/tests/test_compass.py` -- new, 21 tests
- `apps/backend/tests/test_api_compass.py` -- new, 4 tests
- `apps/backend/tests/test_ingest_finalize_compass.py` -- new, 3 tests
- `apps/backend/tests/test_scoring.py` -- T1 fix
- `apps/backend/tests/test_universe_screen.py` -- B2 regression test added
- `apps/backend/tests/test_no_magic_numbers.py` -- `session_delta.py`/`compass.py` added to `CALC_FILES`
- `apps/backend/tests/test_ingest_finalize_disclosure_and_split.py` -- `ESSENTIAL` category set extended with `next_session_manifest` (this test's own invariant is directly affected by the new phase living in the essential half)

Frontend:
- `apps/frontend/lib/api.ts` -- `CompassResponse` + nested types, `fetchCompass`; `CompassSelectionBasis` + `MethodologyCatalog.compass_selection`
- `apps/frontend/components/compass-summary-card.tsx` -- new (J-03)
- `apps/frontend/components/compass-whatchanged-card.tsx` -- new (J-02)
- `apps/frontend/components/compass-focus-section.tsx` -- new (J-04)
- `apps/frontend/components/ui/disclosure.tsx` -- new, extracted shared `Disclosure` component
- `apps/frontend/app/page.tsx` -- fetch `compass`; render the three new sections above the unmodified `DashboardBody`; import the shared `Disclosure`
- `apps/frontend/app/methodology/page.tsx` -- `CompassSelectionCard`, rendered after `SectorBasisCard`

Framework (goal-market-compass iter-2 IN SCOPE bullet, not product code):
- `incredible_auto_dev/agents/demo-narrator/body.md` -- neutral source: forbid regex literals in demo-script JSON
- `incredible_auto_dev/.claude/agents/demo-narrator.md` -- re-rendered mirror (via `sync-cli-assets.py`, never hand-edited)
- `reports/phase-goal-market-compass-iter-1-demo.json` -- fixed the already-broken artifact line 37

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/<file> -v` (per-file, never the full
suite, per project convention — the full suite is a multi-hour, 30-year-basis cost).

- `test_session_delta.py` -- 12 passed
- `test_compass.py` -- 21 passed
- `test_api_compass.py` -- 4 passed
- `test_ingest_finalize_compass.py` -- 3 passed
- `test_universe_screen.py -k "pool_sector or resolve_pool"` -- 9 passed (the file's other 10 tests need
  `loaded_engine`; not run, see Known Issues)
- `test_ingest_finalize_disclosure_and_split.py` + `test_ingest_finalize_fault_injection.py` +
  `test_ingest_finalize_availability_ordering.py` + `test_ingest_finalize_zero_work_coverage.py` -- 26
  passed (no regression from the new finalize phase)
- `test_ingest_finalize_memory_pressure.py` -- 12 passed (real `ulimit -v` test, ~82s, no regression)
- `test_config.py` + `test_config_engine.py` + `test_api_methodology.py` -- 133 passed
- Combined run of every fast new/touched file together -- **174 passed, 1 failed** (see Known Issues —
  the 1 failure is pre-existing and unrelated, confirmed via `git stash`)
- `session_delta.py`/`compass.py` magic-numbers check, scoped standalone (bypassing the file's own
  pre-existing unrelated failure) -- both **CLEAN** (zero float literals, zero forbidden int literals)
- `apps/backend/tests/test_scoring.py` (T1) -- **NOT executed** (needs `loaded_engine`, see Known Issues);
  syntax-checked (`python -m py_compile`) and logically reviewed; the fix is a mechanical
  try/finally wrap with no behavior change to the assertion itself

Frontend: `cd apps/frontend && node_modules/.bin/tsc --noEmit` -- **clean, zero errors**.

Live verification (both `./scripts/dev.sh` boots, backend 8255 / frontend 3255, real committed seed,
591 symbols, latest as-of 2026-08-12):
- `GET /api/compass` -- returns the full CONTENT shape with real computed values; second call served
  from storage (confirmed via the same manifest `content_hash` and via re-reading the DB: exactly one
  `next_session_manifests` row for that `as_of`).
- Browser check (`superpowers-chrome`) of `/`: all three new cards render correctly above the unchanged
  dashboard body, zero console errors; expanded "Show cited facts" (facts match the sentence text
  exactly) and "Not priority (20)" (each entry names its failed condition + distance) disclosures both
  render correctly.
- Browser check of `/methodology`: the new "Next-session focus" card renders with its four live-resolved
  thresholds (Leadership ≥ 80, Entry Quality ≥ 70, Risk ≤ 60, Focus list size ≤ 10); glossary search for
  "why-not" returns exactly the new term under "TODAY & NEXT-SESSION FOCUS".
- `./scripts/dev.sh` booted twice (stop → restart) with no port conflicts; all spawned child processes
  (uvicorn, npm → sh → node → next-server) correctly identified and killed both times; both ports
  confirmed free before the second boot and after final cleanup.

## Known Issues

1. **Zero candidates against the CURRENT real seed data (2026-08-12).** Live-verified: 37 stocks clear
   `leadership_min_score` (80.0) alone, but ZERO of those 37 also clear `entry_min_score` (70.0) — every
   current high-leadership name's Entry Quality score is in the 18-30 range (elite leaders are
   presently all extended/poor-entry, an economically real tension between the two scores, not a code
   bug). This means `disposition_tally.below_selection_floor == 539` (every member) and
   `candidates == []` with an honest `candidates_empty_reason` — exactly the state TC-22 requires and
   tests. I verified this is NOT a threshold-value bug on my part: `leadership_min_score`/
   `entry_min_score`/`risk_max_score` are used EXACTLY as prescribed verbatim in the iter spec's own
   "Improvement direction" appendix (80.0/70.0/60.0). That appendix's "ground truth" note only verified
   the leadership floor IN ISOLATION ("yields a full candidate list today") — it did not re-verify the
   combined three-qualifier AND, which is what actually zeroes out on this date. **Practical
   consequence for QA**: TC-15 through TC-18 and TC-21 (which need at least one real candidate card) will
   need to exercise the candidate-card UI via a synthetic/historical fixture rather than the live latest
   run — the spec's own TC-21 already anticipates exactly this ("a synthetic fixture if none exists").
   TC-22's empty-state itself IS fully verifiable live today. I did not loosen the qualifiers unilaterally
   since they are explicitly prescribed values, not placeholders — this is a product-quality question
   for review/audit/the evaluator to triage (accept the honest empty state as correct today, or flag a
   future config-amendment candidate).
2. **T1's own test was not executed**, only syntax-checked and logically reviewed — it requires the
   session-scoped `loaded_engine` fixture (a full committed-seed load + historical warm), which this
   project's own convention keeps out of pipeline-agent runs (multi-hour class cost). The fix is a
   mechanical `try/finally` wrap around the existing mutate-then-assert block with no change to the
   assertion itself, so the risk of a silent break is low, but a reviewer with budget for the full
   `loaded_engine` build should confirm.
3. **A pre-existing, unrelated test failure**: `test_no_magic_numbers.py::test_engine_calc_code_has_no_magic_numbers`
   fails on `indicators.py`, `forward_testing.py`, and `research.py` (float literals `0.5`/`0.95`/`45.0`/
   `0.9`/`0.0`×4) — confirmed via `git stash` against the base commit (`a58f2c2f`, before any of this
   iteration's changes) that this failure is IDENTICAL and predates this iteration; none of those three
   files were touched by me. I did not fix it (out of scope — not named anywhere in the iter-2 spec).
   My own two new files (`session_delta.py`, `compass.py`) are independently confirmed clean of this
   same check.
4. **Demo-narrator instruction fix is unverified by a real LLM run** — I fixed the neutral-source
   instructions and the specific already-broken artifact, and confirmed the re-render picked up the
   change, but the actual proof that a FUTURE demo-narrator invocation no longer emits a regex literal
   can only be observed empirically the next time that agent runs (this iteration's own showcase step,
   or a later one).
5. `runs/goal-session-market-compass/telemetry.jsonl` and
   `runs/goal-session-mcp-loop/state/preflight-verdict-history.jsonl` show as modified in `git status` —
   these are automatic operational-log side effects of running the dev servers for live verification
   (health/readiness polling), not manual edits; left as-is per the repo's own append-only-log
   convention.
