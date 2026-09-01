# App Blueprint — market-compass

<!--
Coherence contract for the `market-compass` goal session. Drafted at baseline (iter-0) from
docs/goal.md's Product Shape + Must-have journeys, cross-checked directly against the codebase
(apps/frontend/components/sidebar.tsx, apps/frontend/app/, apps/backend/app/engine/*,
apps/backend/app/api/*). This session is layered on top of the prior `ops-hardening` session
(GOAL_ACHIEVED 2026-08-14, 8/8 journeys) — the research platform underneath is unchanged; this
cycle adds a new decision surface (Today compass + next-session manifest) on top of it.

Baseline evidence (2026-08-19 @ 42167cf5): no `compass` engine module, no `next_session_manifests`
table, and no `/api/compass` route exist anywhere in the backend; no `/market` route exists in
`apps/frontend/app/`; `apps/frontend/components/sidebar.tsx`'s NAV array still starts with
`{ href: "/", label: "Dashboard" }` — none of this session's rows/pages are built yet. Rows below
tagged `[TARGET]` are the target state this session builds toward, not current state.
-->

## Information Architecture

**Layout shell:** existing app shell, unchanged — persistent left sidebar + main content area; the
existing global as-of provider remains the sole owner of `?asof` and governs every page below,
including the two new ones.

**Navigation skeleton:**

```
Trendora
├── Today (/)              [TARGET — replaces "Dashboard" as the default landing page]
├── Market (/market)       [TARGET — new route; receives the current "/" dashboard body verbatim]
├── Stocks (/stocks)
├── Themes (/themes)
├── Sectors (/sectors)
├── Scanner Runs (/scanner-runs)
├── Backtest (/backtest)
├── Research (/research)
├── Evidence (/evidence)
├── Watchlist (/watchlist)
├── Methodology (/methodology)
└── Data Manager (/data)
```

`/` is renamed in place from the legacy full dashboard to the new compass; a new `/market` page
receives the CURRENT `/` body verbatim (same components, same endpoints, same persisted
`localStorage` toggle keys `trendora.dashboard.phaseCrossView` / `trendora.dashboard.moreDetail`).
The other ten nav entries keep their route, order position, and content unchanged.

**Feature / journey homes** (each reachable in ≤2 clicks from the persistent nav):

| Feature / journey | Canonical home (route) | Nav section |
|---|---|---|
| J-01 sector attribution | `/stocks` (leaderboard Sector cell + "Unassigned" filter), stock detail header, `/methodology` (two-source disclosure) | Stocks / Methodology |
| J-02 what-changed | `/` — What-changed card | Today |
| J-03 plain-English summary | `/` — summary card + "Show cited facts" disclosure | Today |
| J-04 next-session candidates (why / why-not) | `/` — Next-session focus section | Today |
| J-05 / J-06 manifest freeze + immutability | `/` — manifest strip; its expanded table IS the manifest audit view (candidates + comparison cohort + near-threshold shadow) — no separate nav route exists for it | Today |
| J-07 Today page (ten-second read) | `/` — whole page, top to bottom, chrome (readiness/preflight) above the body | Today |
| J-08 market relocation + history-never-lies | `/market` (relocated body); `/?asof=<date>` (retrospective compass) | Market / Today |
| J-13 leadership rotation (gaining/losing, both directions) | `/` — Leadership rotation section (existing `compass-leadership-rotation-section.tsx` slot; no new route) | Today |

## Data Contract

| Value / entity | Computed by (single module/function) | Served by (single endpoint) | Notes |
|---|---|---|---|
| Next-session manifest — CONTENT block (`session_delta`, `narrative.sentences`, `state_band` **[TARGET — iter-28 build]**, `selection.candidates`, `selection.why_not`, `selection.disposition_tally`, `content_hash`) | `app.engine.compass.build_manifest_payload` (assembles `app.engine.session_delta.compute_delta`, the narrative sentence builder, and `app.engine.compass.evaluate_selection`) — **[LIVE — iter-2 build]** | `GET /api/compass` — **[LIVE — iter-2 build]** | stored in `next_session_manifests` (iter-2 schema: `as_of`, the three content blocks, `content_hash`, `created_at`, source-run link); computed once at ingest finalize (or once on first GET for a not-yet-computed `as_of`) and served from storage thereafter — zero producer calls on a warm hit |
| Next-session manifest — FREEZE/INTEGRITY block (`mode`, `version`, `frozen`, `generation.*`, engine identity, `candidate_rule_hash`, `cohort_rule_hash`, `manifest_config_hash`, dataset/universe stamps, `comparison_cohort` + `near_threshold_shadow` as frozen stored rows with full matching-context, `prospective_eligible`, `available_at_utc`, `manifest_hash`, `caveats`, exported file, `basis` read-time disclosure) | SAME `app.engine.compass.build_manifest_payload`/writer + `app.engine.engine_identity` for the identity value + `app.engine.compass.basis_disclosure` for the read-time `basis` field **[TARGET — iter-3 build in progress; `basis` fail-closed fix — iter-11]** | SAME `GET /api/compass` (additive response fields) — plus a NEW action endpoint `POST /api/compass/regenerate` that mints a new version through the identical writer (an action route, not a second read path) **[TARGET — iter-3 build in progress]** | additive columns onto `next_session_manifests` **[TARGET]**; the iter-2 single-column `as_of` UNIQUE index is replaced by a composite `(as_of, version)` UNIQUE index (constraint/index change only — no existing row's stored values change); export file bytes == stored `payload_json` (at-ingest mode only); validates against `docs/handoffs/trendora-next-session-manifest-v1.schema.json` **[TARGET]**; append-only, never UPDATEd (AG-12). `basis.status` is `"available" \| "unavailable" \| "rebuilt"` **[LIVE]**, extended to a 4th fail-closed unverifiable/unknown literal for the missing/malformed/incomplete-`generation_json` case **[TARGET — iter-11]** — same function, same endpoint, no new producer |
| Engine identity | `app.engine.engine_identity` **[TARGET — iter-3 build in progress]** | embedded in `GET /api/compass` (`generation.engine_identity`) and `GET /api/runs` (`ScannerRun.engine_identity`, additive nullable column) | stamped only at manifest build / `persist_run_payload`; pre-existing rows stay NULL ("pre-stamping era") |
| Stock sector label | `ScannerResult.sector`, stored once at scan time in `scoring.score_stocks` — `config.stock_sectors` first, pool-CSV fallback via `universe.pool_sector_aliases` second (**[LIVE — iter-1]**, `scoring.py:453-458`) | `GET /api/stocks`, `GET /api/stocks/{ticker}` | current-only basis (no point-in-time sector history — B-114 stays open); unknown serves `sector: null` → UI renders "Unassigned", never fabricated; new-run Unassigned coverage 0/539 as of run 3081 |
| Regime label + score | existing engine module (unchanged this session) | `GET /api/dashboard` | compass reads this value, never recomputes it |
| Market phase, severity, P(bear) | existing engine module (unchanged) | `GET /api/market-phase` | compass reads this value, never recomputes it |
| Breadth level + direction | existing engine module (unchanged) | `GET /api/dashboard` | compass reads this value, never recomputes it |
| Sector / theme scores + ranks | `sectors.score_sectors` (verified) / `themes.py` (unchanged) | `GET /api/sectors`, `GET /api/themes` | delta engine reads stored rank rows only (column-projected), never recomputes ranks (AG-8) |
| Stock leadership/entry/risk scores, buckets, setup status | existing scoring/setups modules (unchanged) | `GET /api/stocks` | candidate cards + why-not entries re-read these rows verbatim; no composite score is ever added (AG-11) |
| Evidence / certified-claim ledger status | existing evidence module (unchanged) | `GET /api/evidence` | today: 7 entries, all FAIL → every score reads "Not yet proven"; compass evidence chips read the same ledger, never a second status (AG-1); the manifest's `caveats.evidence` field (iter-3) composes this SAME status into the exported artifact, never a second computation |
| Coverage payload | `data_manager.coverage_from_storage` (unchanged, verified) | `GET /api/data` | compass narrative may cite coverage/staleness FACTS only, never readiness/preflight tokens (AG-13) |
| Run summary / scanner runs list | existing (unchanged, verified route at `runs.py:25`) | `GET /api/runs` | What-changed's prior-session anchor = the row immediately preceding the current as-of here |
| Readiness / preflight state | existing readiness module (unchanged) | dashboard/health chrome (layout, above the page body) | vocabulary (Ready / GO / DEGRADED / NO-GO) never appears inside market-state surfaces, and market/regime vocabulary never appears in chrome (AG-13) |

Rows marked **[TARGET]** are not yet built/verified as of this note — confirmed by direct search
across `apps/backend/app/engine/`, `apps/backend/app/api/`, and `apps/backend/app/models.py`. Rows
marked **[LIVE]** are built and evaluator-confirmed. All other rows are pre-existing canonical values
this session's new work must READ from their listed endpoint, never re-derive or re-fetch from a
second path.

**iter-2 update (2026-08-20):** the Next-session manifest row above is split into its CONTENT block
(this iteration's build target) and its FREEZE/INTEGRITY block (a later target, J-05/J-06) — both
blocks are fields of the SAME document, built by the SAME `build_manifest_payload` function and served
by the SAME `GET /api/compass` endpoint; the split records phased delivery, not a second producer or a
second endpoint. J-05/J-06 extend `next_session_manifests` with additive columns only (mode, version,
frozen, hashes, provenance, cohort storage, `prospective_eligible`, `available_at_utc`) — never a
schema change to the iter-2 columns. The Stock sector label row is updated to reflect J-01's pool-CSV
fallback, which shipped live in iter-1.

**iter-3 update (2026-08-20):** the FREEZE/INTEGRITY block row now has its concrete field set locked
for build: `mode`, `version`, `frozen`, `generation.{producer, frontier_bar_date, generated_at,
preflight_verdict, engine_identity}`, `candidate_rule_hash` + config subset, `cohort_rule_hash` +
config subset, `manifest_config_hash` + config subset, `dataset` stamp, `universe.{pool_hash,
resolver_gate, member_count, profile}`, `comparison_cohort[]` (every non-candidate member + frozen
matching-context + `selection_disposition`), `near_threshold_shadow[]` (same frozen context,
leadership-banded), `prospective_eligible`, `available_at_utc`, `manifest_hash`, `caveats.{evidence,
survivorship, sector_basis, cohort_semantics}` — still the SAME producer (the extended
`app.engine.compass` freeze writer, plus `app.engine.engine_identity` for the identity value alone)
and the SAME read endpoint `GET /api/compass`. A NEW action endpoint,
`POST /api/compass/regenerate?as_of=<date>` (confirm-gated), mints an explicit new version through the
IDENTICAL writer — this is an action route, not a second read path, so "one serving endpoint" still
holds for reads. Storage stays the SAME `next_session_manifests` table via additive columns; its
single-column `as_of` UNIQUE index is replaced by a composite `(as_of, version)` UNIQUE index via the
existing idempotent `_INDEX_DROPS`/`_INDEX_ADDS` pattern (`app/db.py`) so multiple versions per date can
coexist — a constraint/index change only, no existing row's stored VALUES change, so this stays
additive per goal.md's own framing of J-05/J-06 as extending iter-2's table. Existing pre-iter-3 rows
backfill `version=1` with `mode`/`frozen`/hashes NULL/false (a "pre-freeze era" marker, never
retroactively marked frozen), mirroring the `ScannerRun.engine_identity` NULL-legacy-row precedent.
`[TARGET]` tags on the FREEZE/INTEGRITY and Engine identity rows flip to `[LIVE]` only once the
goal-evaluator confirms J-05/J-06 passing with evidence — this note records the iter-3 PLAN, not a
delivered/verified state.

**iter-5 note (2026-08-20 — informational, no contract change):** direct read-only inspection of the
live DB found the production database's only possible manifest "frontier" date (2026-08-12, the
current `daily_prices`/`scanner_runs` max) already carries 5 `next_session_manifests` rows from prior
schema-migration and dev-testing activity, so the append-only, skip-if-exists writer can never mint a
fresh version-1 `at_ingest`/`prospective_eligible: true` row there again — this slot is permanently
burned independent of any future remove+backfill. Only 14 as-of dates total carry any manifest row;
every other scanner_run date remains untouched and safe to use for non-frontier steps. iter-5 routes
the flagship at-ingest-eligibility proof to the already-built fixture-scoped test suite
(`test_manifest_invariants.py`, `test_ingest_finalize_compass.py`, each using its own isolated DB via
`app.db.make_engine`) instead of a live drill against this burned slot. See
`docs/phases/goal-market-compass-iter-5.md` BACKGROUND and
`runs/goal-session-market-compass/state/assumptions.md` (iter-5 entry) for full detail. No Data
Contract row, endpoint, or IA entry changes as a result of this note.

**iter-11 update (2026-08-23 — additive, no IA change):** the FREEZE/INTEGRITY block row's computing
module gains `app.engine.compass.basis_disclosure` explicitly (it already existed and was already
served under this row; it was not previously named as its own contributor) and its `basis.status`
sub-field is documented as a 3-member literal union extending to 4 under the owner-authorized (ruling
A4, 2026-08-23) fail-closed fix for the case where a manifest's `generation_json` is missing, empty,
malformed, or omits `source_run_created_at` — the read path must never report `"available"` in that
case. Same function, same endpoint (`GET /api/compass`, `basis` field) — no new producer, no new route.
This iteration also performs an owner-authorized (ruling A1) mechanical live-schema rebuild of
`next_session_manifests` that removes the `source_run_id → scanner_runs.id` foreign-key constraint and
nothing else (AG-18) — a constraint-only change with all 24 rows' stored values preserved exactly; no
Data Contract row, endpoint, or IA entry changes as a result, since no computing module, serving
endpoint, or displayed field's identity moves. See `docs/phases/goal-market-compass-iter-11.md` and
`runs/goal-session-market-compass/state/assumptions.md` (iter-11 entry) for full detail.

**iter-12 update (2026-08-24 — additive, no IA change, no Data Contract row change):** the FREEZE/INTEGRITY
block row's `basis_disclosure` sub-contributor (named explicitly since the iter-11 update) is narrowed
further under owner ruling A4-bis (2026-08-24): the existing `unverifiable` literal (still the same
4-member `basis.status` union registered in iter-11 — `"available" | "unavailable" | "rebuilt" |
"unverifiable"`) now also covers a *recorded-but-invalid* `source_run_created_at` value (JSON `null`,
empty/unusable string, or an unparseable string), not only a missing/malformed `generation_json` block.
Same function, same endpoint (`GET /api/compass`, `basis` field) — no new literal, no new producer, no new
route. This iteration also fixes (fixture-only; never run against the live database) the `j11_schema_migration`
utility's shadow-table construction to derive from captured live DDL text rather than ORM metadata (ruling
A10, future-safety-only — no live schema change this iteration), and corrects a false provenance comment in
`app/models.py` (`source_run_id`) per ruling A8/A9's accepted four-item DDL residual. No Data Contract row,
endpoint, or IA entry changes as a result — the live `next_session_manifests` table itself is untouched this
iteration (zero live writes, proven read-only before/after). See `docs/phases/goal-market-compass-iter-12.md`
and `runs/goal-session-market-compass/state/assumptions.md` (iter-12 entry) for full detail.

**iter-23 note (2026-08-27 — informational, no IA change, no Data Contract row change):** J-11's
serving/replay verification (owner ruling, 2026-08-27) exercises the already-registered Today (`/`) and
Market (`/market`) homes and every already-registered Data Contract row that feeds them (Next-session
manifest CONTENT + FREEZE/INTEGRITY blocks, engine identity, stock sector label, regime/phase/breadth,
sector/theme scores, evidence ledger status) — read-only, against a disposable byte-faithful clone of the
canonical database, never the canonical database itself. No new page, nav entry, computing module, serving
endpoint, or displayed field is introduced. This note exists only to record that the long browser-QA/replay
isolation window (iters 9-22) ends this iteration for verification purposes, scoped to the disposable
clone.

**iter-25 note (2026-08-28 — informational, no IA change, no Data Contract row change):** J-09's re-run
(standing-warm VmPeak re-measurement, concurrent-load check, byte-identity spot check) touches no page,
nav entry, computing module, serving endpoint, or displayed field — its only artifact is a new dated
addendum in `reports/perf-budgets.md`, an internal ops report outside the Information Architecture and
Data Contract. The `replay_lane_spec_journeys` parser fix is Goal-mode harness automation
(`scripts/automation/lib/replay-lane.sh`), not Trendora product surface. Nothing in this iteration
changes any row above.

**iter-26 note (2026-08-28 — informational, no IA change, no Data Contract row change):** the J-05/J-06
make-up work exercises the already-registered "Next-session manifest" CONTENT + FREEZE/INTEGRITY rows
via their already-registered single producer (`app.engine.compass.build_manifest_payload` /
`basis_disclosure`) and single endpoints (`GET /api/compass`, `POST /api/compass/regenerate`) — no new
page, nav entry, computing module, serving endpoint, or displayed field. This iteration deliberately
does NOT run the literal live remove+backfill drill J-05/J-06's own goal.md steps describe (see
`docs/phases/goal-market-compass-iter-26.md` BACKGROUND and the `iter-26 — goal-decomposer` assumption
ledger entry): that drill's only unambiguous target today is 2026-08-11/2026-08-12, the exact dates
whose removal caused the iter-5 incident, so the destructive portions are proven against the existing
isolated-engine fixture suite instead, and the only live canonical-database write this iteration makes
is one additive, AG-12-safe `POST /api/compass/regenerate` call on a clean, non-incident historical
date (`as_of=2025-04-15`). Nothing in this iteration changes any row above.

**iter-27 note (2026-08-28 — informational, no IA change, no Data Contract row change):** J-06's last
unmet limb is fixed by reordering `GET /api/compass`'s internal read-time control flow only: the route now
checks for an already-frozen manifest at the resolved as-of BEFORE calling the shared
`snapshot_serving.resolved_run`/`scanner.run_scan` self-heal path, instead of after. This makes the
already-registered `basis.status: "unavailable"` literal (registered since the iter-11 note above)
reachable through the live route for the first time; no new computing module, serving endpoint, displayed
field, page, or nav entry is introduced, and `snapshot_serving.resolved_run`/`scanner.run_scan` themselves
are unmodified, so every OTHER page's self-heal behavior (`/`, `/stocks`, `/sectors`, `/themes`, dashboard,
market-phase) is unaffected. Nothing in this iteration changes any row above.


**iter-28 update (2026-08-28 — additive, no IA change):** the Next-session manifest CONTENT block row's
field list gains `state_band` — three served direction words (`regime`, `stress`, `breadth`), each with a
signed delta, computed ONCE inside the SAME `app.engine.compass.build_manifest_payload` producer (a new
`build_state_band`-style helper alongside the existing `session_delta`/`narrative` builders) and served by
the SAME `GET /api/compass` endpoint — no new producer, no new route. `state_band.<band>.direction_word`
reuses the existing `compass.vocabulary.direction_words` map (never a second word map);
`state_band.<band>.delta` is a signed float, `null` when no previous run exists. `regime` compares stored
`regime_score`, `stress` compares stored market-phase `severity` ("severity velocity"), `breadth` compares
stored `breadth_above_50dma`, each banded by a config-only threshold under `compass.delta.*`
(`test_no_magic_numbers.py` coverage — `compass.py` is already a `CALC_FILES` entry). Added additively to
`docs/handoffs/trendora-next-session-manifest-v1.schema.json` (loosely-typed object property, no
`schema_version` bump, consistent with the iter-11/iter-12 additive-extension precedent). This iteration
also fulfills the already-registered `[TARGET]` "Today (/)" and "Market (/market)" Information Architecture
rows from baseline (page reorder + verbatim relocation of the former dashboard body to a new `/market`
route + sidebar rename/addition) — no IA change, since both rows and their canonical homes were already
declared at baseline. See `docs/phases/goal-market-compass-iter-28.md` for full detail. The `[TARGET]` tag
on `state_band` and on the Today/Market IA rows flips to `[LIVE]` only once the goal-evaluator confirms
J-07/J-08 passing with evidence — this note records the iter-28 PLAN, not a delivered/verified state.

**iter-29 note (2026-08-31 — informational, no IA change, no Data Contract row change):** J-07's
`state_band` row (registered iter-28) is exercised through its already-registered single producer
(`app.engine.compass.build_manifest_payload` / `build_state_band`) and single endpoint
(`GET /api/compass`) via exactly one authorized create-once-on-GET call at `as_of=2026-08-03` — a
date chosen because it had zero prior manifest rows, letting the already-shipped `state_band` field
be observed with real words for the first time on live data. No new page, nav entry, computing
module, serving endpoint, or displayed field is introduced; `build_state_band` itself is unchanged
(binding "Do not redo"). The `[TARGET]` → `[LIVE]` flip on the `state_band` row remains the
goal-evaluator's call, pending its confirmation that J-07 passes with this iteration's evidence.

**iter-30 note (2026-09-01 — informational, no IA change, no Data Contract row change):** J-07's
`state_band` row (registered iter-28) is exercised at the DEFAULT landing view (`/`, no `asof` param
— the frontier, 2026-08-12) for the first time: exactly one authorized
`POST /api/compass/regenerate?as_of=2026-08-12&confirm=true` mints version 7 of the frontier manifest
through the already-registered single producer (`app.engine.compass.build_manifest_payload` /
`build_state_band`) and single action endpoint (`POST /api/compass/regenerate`, registered iter-3) —
versions 1-6 stay byte-identical (AG-12), version 7 is `prospective_eligible: false` (AG-17, since
`generation.producer == "regenerate"`, never `"ingest_finalize"`). No new page, nav entry, computing
module, serving endpoint, or displayed field is introduced; `build_state_band` itself is unchanged
(binding "Do not redo"). The `[TARGET]` → `[LIVE]` flip on the `state_band` row remains the
goal-evaluator's call, pending its confirmation that J-07 passes with this iteration's evidence at
the default `/` view.

**iter-31 note (2026-09-01 — informational, no IA change, no Data Contract row change):** J-02
"what-changed" and J-03 "plain-English summary" (both registered at baseline under the Today (`/`)
home) are re-verified live against the fully-recovered database (frontier `2026-08-12`, J-10/J-11
complete) for the first time since iter-6 downgraded them to `partial` mid-incident. Both rows'
already-registered single producer (`app.engine.compass.build_manifest_payload`, composing
`app.engine.session_delta.compute_delta` and the narrative sentence builder) and single serving
endpoint (`GET /api/compass`) are unchanged — this iteration reads them, it does not move or duplicate
either. No new page, nav entry, computing module, serving endpoint, or displayed field is introduced.
Live `/api/compass` calls this iteration are confined to three already-manifested `as_of` values
(frontier `2026-08-12`, `2025-04-15`, `1996-02-01` — the true earliest stored run) so zero new
`next_session_manifests` rows are expected; see `state/assumptions.md` (`iter-31 — goal-decomposer`).

**iter-32 note (2026-09-01 — informational, no IA change, no Data Contract row change):** J-09's
re-measurement (standing-warm VmPeak clean re-capture with durable raw evidence, concurrent-load
check, byte-identity spot check) touches no page, nav entry, computing module, serving endpoint, or
displayed field — its only artifacts are a new dated addendum in `reports/perf-budgets.md` and a
raw sample file under `runs/goal-market-compass-iter-32/` (internal ops evidence, outside the
Information Architecture and Data Contract). `config.yaml`'s `database.pragmas.cache_size` is
confirmed unchanged at `-65536` (set iter-4); no code path in `app.engine.compass` or any other
producer is touched. Required-still-passing journeys this iteration exercise only already-registered
Data Contract rows (Next-session manifest CONTENT + FREEZE/INTEGRITY blocks, engine identity, stock
sector label, regime/phase/breadth, sector/theme scores, evidence ledger status) through their
already-registered single producers and endpoints — this iteration reads them, it does not move or
duplicate any. Live `/api/compass` calls stay confined to the same three already-manifested `as_of`
values used at iter-31 (frontier `2026-08-12`, `2025-04-15`, `1996-02-01`), so zero new
`next_session_manifests` rows are expected.

**iter-33 note (2026-09-01 — informational, no IA change, no Data Contract row change):** J-09's
warm-up memory bound (Constraints (c) — bounding the cold cadence-date allocation
`apps/backend/app/engine/warmup.py:351`'s `with bar_cache(session):` block produces, via
`apps/backend/app/engine/prices.py`'s `_BarCache`/`bar_cache`/`prefill`) touches no page, nav
entry, computing module, serving endpoint, or displayed field — the new memory-budget key is a
performance-only tunable under `config.yaml` (`compass.*`/`startup.*`), not a Data Contract value,
matching the iter-4/25/32 precedent for J-09's other config-only changes. Artifacts are a new
`reports/perf-budgets.md` Addendum 44 plus a dated correction note on Addendum 43, both internal
ops reports outside the Information Architecture and Data Contract, and a raw sample file under
`runs/goal-market-compass-iter-33/`. This iteration's byte-identity spot-check exists specifically
to prove every already-registered Data Contract row (Next-session manifest CONTENT + FREEZE/
INTEGRITY blocks, engine identity, stock sector label, regime/phase/breadth, sector/theme scores,
evidence ledger status) is read unchanged through its already-registered single producer and
endpoint across the authorized 7-value as-of set — this iteration reads them, it does not move,
duplicate, or add to any.

**iter-34 note (2026-09-01 — informational, no IA change, no Data Contract row change):** J-09's
closing re-measurement (extended ≥360s standing-warm capture, taken twice — developer run plus an
independent auditor re-derivation from a fresh boot — with the settled `VmRSS_kB`/`VmSize_kB` plateau
reported beside the `VmPeak_kB` high-water mark) touches no page, nav entry, computing module, serving
endpoint, or displayed field — its only artifacts are a new dated Addendum 45 in
`reports/perf-budgets.md` and raw sampler CSVs under `runs/goal-market-compass-iter-34/`, both internal
ops evidence outside the Information Architecture and Data Contract, matching the iter-25/32/33
precedent for J-09's other measurement-only rounds. This iteration also patches the goal-mode harness
(`incredible_auto_dev/scripts/automation/lib/merge_ui_test_results.py`, and `goal_gate.py` if required)
so a journey whose `docs/goal.md` Acceptance carries the literal `**Walkthrough:** waived` marker can be
recorded as verified through cited non-UI evidence instead of forcing a `BLOCKED` headline for lacking a
browser row — pipeline tooling, not Trendora product surface; no new page, nav entry, computing module,
serving endpoint, or displayed field results from it either. Nothing in this iteration changes any row
above.

**iter-35 note (2026-09-01 — additive, no IA change, no new Data Contract row):** the goal-proposer's
newly-added J-12 (`docs/goal.md` AUTO block, 2026-09-01) targets a measured correctness defect inside
the ALREADY-REGISTERED "Next-session manifest — CONTENT block" row's `selection.candidates` /
`selection.disposition_tally` / `selection.why_not` fields: `app.engine.compass.evaluate_selection`
currently gates candidacy on all three qualifier checks (leadership, entry, risk) instead of leadership
alone (confirmed live at `apps/backend/app/engine/compass.py:602-703` — every row failing ANY check is
labeled `below_selection_floor`), mislabeling 37 of 539 `comparison_cohort` rows in the committed
frontier export (`2026-08-12_v7.json`) despite clearing the leadership floor (highest: HPE, 92.71). This
iteration plans a fix wholly inside the SAME producer (`app.engine.compass.evaluate_selection` /
`build_manifest_payload`) and SAME endpoint (`GET /api/compass`): `leadership_min_score` becomes the
sole inclusion gate; `entry_min_score`/`risk_max_score` become advisory qualifiers (cautions +
eligibility-checklist annotations only, never gating membership); `compass.selection.rule_version` bumps
so corrected-rule manifests are distinguishable from prior ones. No new producer, no new route, no new
Data Contract row or field, no schema-file version bump — the `selection_disposition` closed vocabulary
(`below_selection_floor` | `excluded_by_cap`) is unchanged, only which rows land in each bucket. All
pre-existing `next_session_manifests` rows and export files stay byte-identical (AG-12); pre-fix
mislabeled versions keep their original `selection_disposition`/`prospective_eligible` values exactly
(AG-17) — the correction applies only to manifests minted after the `rule_version` bump. This note
records the iter-35 PLAN; the `[TARGET]`→delivered status is the goal-evaluator's call pending J-12
evidence.

**iter-36 note (2026-09-01 — additive, no IA change, no new Data Contract row):** J-13 (goal-proposer
AUTO block, 2026-09-01) targets the ALREADY-REGISTERED "Next-session manifest — CONTENT block" row's
`session_delta` field. Confirmed live at `apps/frontend/components/compass-leadership-rotation-section.tsx:38`:
the Leadership rotation section is a client-side `session_delta.changes.filter(kind in {sector,theme,stock})`
over the SAME array `compass-whatchanged-card.tsx` already renders in full (0 market/breadth entries on the
frontier, so it duplicates all 17 What-changed rows verbatim); change entries carry only an unsigned
`magnitude` (no `delta`, no `direction_word`); and `_sector_changes`/`_theme_changes`
(`apps/backend/app/engine/session_delta.py:105-162`) sort+slice to `top_k` without disclosing movers that
clear `rank_move_min` but fall beyond the cap, so an above-threshold mover can vanish from both `changes`
and `suppressed` (measured: sector accounts for only 29 of its 31 configured ETFs on the frontier). This
iteration adds fields to the SAME producer (`app.engine.compass.build_manifest_payload`, reusing
`app.engine.session_delta.compute_delta`'s already-computed sector/theme rank pairs — no second
computation) and serves them via the SAME endpoint (`GET /api/compass`) — no new producer, no new route:
  - `session_delta.rotation.{sector,theme}` — each an object with two explicitly labeled sides
    (`gaining`, `losing`), each entry `{label, from, to, delta (signed), direction_word, drill_href}`,
    each side capped by a NEW config-only key `compass.delta.rotation_top_k` (added under the existing
    `compass.delta` block; both `session_delta.py` and `compass.py` stay `test_no_magic_numbers.CALC_FILES`
    entries, so no literal may appear in code) and gated by the EXISTING `compass.delta.rank_move_min`;
    plus a per-kind accounting object (`shown_count`, `suppressed_count`, `residual_count`,
    `configured_total`) that must close exactly against the configured group counts (31 sector/industry,
    11 theme). Group-level only — no stock-kind row (stock bucket crossings stay in `session_delta.changes`
    / What-changed only).
  - `session_delta.changes[]` entries of `kind ∈ {sector, theme}` additionally carry the SAME signed
    `delta` and served `direction_word` (single computation, two placements) — `market`/`breadth`/`stock`
    kind entries are unchanged by this addition.
  - `direction_word` reuses the EXISTING `compass.vocabulary.direction_words` map via the EXISTING
    `_flat_band_word` classifier (`apps/backend/app/engine/compass.py:134`) — never a second word map; the
    polarity is resolved engine-side (a FALLING rank number is "improving"), mirroring the `state_band.stress`
    sign-transform precedent (iter-28).
  - No `schema_version` bump: `session_delta` is an open object in
    `docs/handoffs/trendora-next-session-manifest-v1.schema.json`. No change to `compass.selection.*`,
    `evaluate_selection`, candidate membership, or either frozen cohort (J-12's "Do not redo" stays intact).
    All pre-existing `next_session_manifests` rows and export files stay byte-identical (AG-12) — this
    change affects only manifests minted AFTER it ships. This note records the iter-36 PLAN; the
    `[TARGET]`→delivered status is the goal-evaluator's call pending J-13 evidence.

**iter-37 note (2026-09-01 — informational, no IA change, no Data Contract row change):** this iteration
is a pure closing/hardening round on ALREADY-registered rows — no new page, nav entry, computing module,
serving endpoint, or displayed field is introduced. It (a) re-verifies J-13's already-registered
`session_delta.rotation` fields (registered iter-36) with a genuinely-run full-depth pipeline and a real,
measured acceptance screenshot, replacing iter-36's 100%-blank capture; (b) replays `journey-scripts/J-13.json`
for the first time (written after iter-36's replay window, so it had never executed); and (c) makes two
backend robustness repairs wholly internal to the ALREADY-registered "Next-session manifest — CONTENT block"
producer (`app.engine.compass.evaluate_selection` / `build_manifest_payload`): converting
`_assert_disposition_predicate`'s two bare `assert` statements (added iter-35 for J-12) to explicit raises so
the guard survives `-O`, and correcting a `test_manifest_invariants.py` TC-24 fixture value so it genuinely
isolates the risk qualifier. Neither repair changes the predicate's logic, any served field, or any stored
row/export file (AG-12) — this note records the iter-37 PLAN.

**iter-38 note (2026-09-01 — additive, no IA change, no new Data Contract row):** J-14 (goal-proposer
AUTO block, 2026-09-01) targets the ALREADY-REGISTERED "Next-session manifest — CONTENT block" row's
`selection.why_not` field (part of `selection.*`, produced by `app.engine.compass.evaluate_selection`
inside `app.engine.compass.build_manifest_payload`, served only by `GET /api/compass`). Measured against
the committed `2026-08-12_v9.json` export: all 20 served `why_not` entries carry an empty
`failed_conditions`, which `compass-focus-section.tsx:119-121` renders as "passed every qualifier, cut
only by the focus-list cap." — false for 20 of 20, since every one fails the advisory `entry_min_score`
qualifier (four also fail `risk_max_score`) per the same manifest's `comparison_cohort` rows; separately,
27 non-candidates clear the 80.0 leadership floor while 25 sit in the [75.0, 80.0) near-miss band, but the
pool is leadership-sorted before the `why_not_cap` (20) truncation so the visible list is made entirely of
cap-excluded names and no below-floor near-miss can ever appear. This iteration adds fields to the SAME
producer and serves them via the SAME endpoint — no new producer, no new route:
  - `selection.why_not[].reason: "excluded_by_cap" | "below_selection_floor"` — reuses the EXISTING
    `_DISPOSITION_EXCLUDED_BY_CAP` / `_DISPOSITION_BELOW_FLOOR` vocabulary already used by
    `comparison_cohort[].selection_disposition` — no new label set.
  - `selection.why_not[].failed_conditions[].gating: bool` — new field on the existing failed-condition
    shape, reusing the `gating` tag `_qualifier_checks` already produces per check.
  - `selection.why_not[].cap_rank: int >= 1 | null` and `.cap: int >= 1 | null` — the row's leadership
    rank among qualifying (above-floor) rows and the configured `compass.selection.max_candidates` value;
    both non-null only when `reason == "excluded_by_cap"`.
  - `selection.why_not_totals: { excluded_by_cap_uncapped: int >= 0, below_floor_in_band_uncapped: int >= 0 }`
    — the two full pool counts before the existing `why_not_cap` truncation (measured today: 27 and 25).
  No `schema_version` bump: `selection.why_not` is an unconstrained array in
  `docs/handoffs/trendora-next-session-manifest-v1.schema.json`, so every addition above is additive. No
  change to `leadership_min_score`/`entry_min_score`/`risk_max_score` VALUES, candidate membership,
  `disposition_tally`, `comparison_cohort` membership, or `near_threshold_shadow` (J-12's "Do not redo"
  stands; AG-15). All pre-existing `next_session_manifests` rows and export files stay byte-identical
  (AG-12) — this change affects only manifests minted AFTER it ships. This note records the iter-38 PLAN;
  the `[TARGET]`→delivered status is the goal-evaluator's call pending J-14 evidence. J-15 (stock-kind
  "Suppressed moves" undercount, `session_delta.py`, also goal-proposer 2026-09-01) is queued next and
  targets the same already-registered row's `session_delta` field — deliberately not bundled with J-14
  per the priority rubric's "never bundle two risky journeys" rule.
