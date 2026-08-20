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

## Data Contract

| Value / entity | Computed by (single module/function) | Served by (single endpoint) | Notes |
|---|---|---|---|
| Next-session manifest — CONTENT block (`session_delta`, `narrative.sentences`, `selection.candidates`, `selection.why_not`, `selection.disposition_tally`, `content_hash`) | `app.engine.compass.build_manifest_payload` (assembles `app.engine.session_delta.compute_delta`, the narrative sentence builder, and `app.engine.compass.evaluate_selection`) — **[TARGET — iter-2 build]** | `GET /api/compass` — **[TARGET — iter-2 build]** | stored in `next_session_manifests` (iter-2 schema: `as_of`, the three content blocks, `content_hash`, `created_at`, source-run link); computed once at ingest finalize (or once on first GET for a not-yet-computed `as_of`) and served from storage thereafter — zero producer calls on a warm hit |
| Next-session manifest — FREEZE/INTEGRITY block (`mode`, `version`, `frozen`, `generation.*`, engine identity, `candidate_rule_hash`, `cohort_rule_hash`, `manifest_config_hash`, dataset/universe stamps, `comparison_cohort` + `near_threshold_shadow` as frozen stored rows with full matching-context, `prospective_eligible`, `available_at_utc`, `manifest_hash`, exported file) | SAME `app.engine.compass.build_manifest_payload` + `persist_manifest` **[TARGET — J-05/J-06]** | SAME `GET /api/compass` (additive response fields) **[TARGET — J-05/J-06]** | additive columns onto `next_session_manifests` **[TARGET]**; export file bytes == stored `payload_json`; validates against `docs/handoffs/trendora-next-session-manifest-v1.schema.json` **[TARGET]**; append-only, never UPDATEd (AG-12) |
| Engine identity | `app.engine.engine_identity` **[TARGET]** | embedded in `GET /api/compass` (`generation.engine_identity`) and `GET /api/runs` (`ScannerRun.engine_identity`, additive nullable column) | stamped only at manifest build / `persist_run_payload`; pre-existing rows stay NULL ("pre-stamping era") |
| Stock sector label | `ScannerResult.sector`, stored once at scan time in `scoring.score_stocks` — `config.stock_sectors` first, pool-CSV fallback via `universe.pool_sector_aliases` second (**[LIVE — iter-1]**, `scoring.py:453-458`) | `GET /api/stocks`, `GET /api/stocks/{ticker}` | current-only basis (no point-in-time sector history — B-114 stays open); unknown serves `sector: null` → UI renders "Unassigned", never fabricated; new-run Unassigned coverage 0/539 as of run 3081 |
| Regime label + score | existing engine module (unchanged this session) | `GET /api/dashboard` | compass reads this value, never recomputes it |
| Market phase, severity, P(bear) | existing engine module (unchanged) | `GET /api/market-phase` | compass reads this value, never recomputes it |
| Breadth level + direction | existing engine module (unchanged) | `GET /api/dashboard` | compass reads this value, never recomputes it |
| Sector / theme scores + ranks | `sectors.score_sectors` (verified) / `themes.py` (unchanged) | `GET /api/sectors`, `GET /api/themes` | delta engine reads stored rank rows only (column-projected), never recomputes ranks (AG-8) |
| Stock leadership/entry/risk scores, buckets, setup status | existing scoring/setups modules (unchanged) | `GET /api/stocks` | candidate cards + why-not entries re-read these rows verbatim; no composite score is ever added (AG-11) |
| Evidence / certified-claim ledger status | existing evidence module (unchanged) | `GET /api/evidence` | today: 7 entries, all FAIL → every score reads "Not yet proven"; compass evidence chips read the same ledger, never a second status (AG-1) |
| Coverage payload | `data_manager.coverage_from_storage` (unchanged, verified) | `GET /api/data` | compass narrative may cite coverage/staleness FACTS only, never readiness/preflight tokens (AG-13) |
| Run summary / scanner runs list | existing (unchanged, verified route at `runs.py:25`) | `GET /api/runs` | What-changed's prior-session anchor = the row immediately preceding the current as-of here |
| Readiness / preflight state | existing readiness module (unchanged) | dashboard/health chrome (layout, above the page body) | vocabulary (Ready / GO / DEGRADED / NO-GO) never appears inside market-state surfaces, and market/regime vocabulary never appears in chrome (AG-13) |

Rows marked **[TARGET]** do not exist yet as of this baseline — confirmed by direct search across
`apps/backend/app/engine/`, `apps/backend/app/api/`, and `apps/backend/app/models.py`. All other
rows are pre-existing canonical values this session's new work must READ from their listed
endpoint, never re-derive or re-fetch from a second path.

**iter-2 update (2026-08-20):** the Next-session manifest row above is split into its CONTENT block (this iteration's build target) and its FREEZE/INTEGRITY block (a later target, J-05/J-06) — both blocks are fields of the SAME document, built by the SAME `build_manifest_payload` function and served by the SAME `GET /api/compass` endpoint; the split records phased delivery, not a second producer or a second endpoint. J-05/J-06 extend `next_session_manifests` with additive columns only (mode, version, frozen, hashes, provenance, cohort storage, `prospective_eligible`, `available_at_utc`) — never a schema change to the iter-2 columns. The Stock sector label row is updated to reflect J-01's pool-CSV fallback, which shipped live in iter-1.
