# Iteration 2 — Coherence Audit

**Iteration:** goal-market-compass-iter-2
**Date:** 2026-08-20
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

---

## Data Contract check

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| `session_delta` (prior_as_of, gap_days, changes, suppressed, suppressed_count) — new this iteration | OK | Sole producer `apps/backend/app/engine/session_delta.py:1721` `compute_delta`, called only from `apps/backend/app/engine/compass.py:423` `build_manifest_payload`, called only from `apps/backend/app/api/compass.py:1094` `GET /api/compass`. Matches blueprint.md's registered CONTENT-block row exactly. |
| `narrative` (sentences[]) — new this iteration | OK | Sole producer `apps/backend/app/engine/compass.py:186` `build_narrative`, assembled by the same `build_manifest_payload` above, served by the same `GET /api/compass`. |
| `selection` (candidates, why_not, disposition_tally, candidates_empty_reason) — new this iteration | OK | Sole producer `apps/backend/app/engine/compass.py:323` `evaluate_selection`, assembled by the same `build_manifest_payload`, served by the same `GET /api/compass`. |
| `content_hash` | OK | Computed once, in `apps/backend/app/engine/compass.py:414-429` (`build_manifest_payload`), sha256 over sorted-key JSON of exactly the three blocks above; re-served verbatim from storage by `manifest_row_payload` (`compass.py:484-493`), never re-derived at serve time. |
| Regime label + score (pre-existing, registered → `GET /api/dashboard`) | OK | `compass.py:196` calls `dashboard_payload(current_run)` — the identical function `apps/backend/app/api/dashboard.py:32` calls for `GET /api/dashboard`. Same function, same call, not a second computation. |
| Market phase / severity / P(bear) (pre-existing, registered → `GET /api/market-phase`) | OK | `compass.py:197` calls `market_phase.market_phase_cached(session, current_run.asof_date, cfg)` — confirmed the same function backing `GET /api/market-phase` (`apps/backend/app/api/market_phase.py:53` comment: "payload is `market_phase_cached(...)` verbatim"). `_pbear_word` (`compass.py:53-62`) only maps the already-fetched `p_bear` float to a narrative word via config bands — a display re-format, not a recomputation of `p_bear` itself. |
| Breadth level (pre-existing, registered → `GET /api/dashboard`) | OK | `compass.py:126` (`_breadth_sentence`) reads `current_run.breadth_above_50dma` / `.breadth_above_200dma` directly off the same `ScannerRun` row object passed into `build_manifest_payload`. Confirmed `dashboard_payload` (`apps/backend/app/engine/snapshot_serving.py:193-195`) reads the identical two stored columns off the identical row shape — zero divergence risk, not an independent computation. |
| Stock leadership/entry/risk scores, buckets (pre-existing, registered → `GET /api/stocks`) | OK | `evaluate_selection` (`compass.py:329-341`) issues a column-projected `select(ScannerResult.leadership_score, .leadership_bucket, .entry_quality_score, .entry_quality_bucket, .risk_score, .risk_bucket)` — a verbatim read of the same stored `ScannerResult` columns `/api/stocks` serves; no recompute, no new blended score (candidate cards carry only these three numeric fields — verified by the diff's own `test_no_composite_score_field_anywhere`, `apps/backend/tests/test_compass.py:2101-2109`). |
| `record_json` (risk_budget.atr_pct, invalidation note) used for candidate cautions | OK | `_record_json_by_ticker` (`compass.py:217-229`) reads `ScannerResult.record_json` scoped to only the ≤`max_candidates` selected tickers (bounded, AG-8-compliant) — same stored blob `/api/stocks/{ticker}` rehydrates, not a second source. |
| New "Next-session focus" methodology disclosure (`compass_selection` prose + thresholds) | OK (not a Data Contract "value") | Config-driven static prose + `ref`-resolved thresholds off the already-registered `compass.selection.*` keys (`apps/backend/app/config.py:2550-2554`, `apps/backend/app/engine/methodology.py:358-367`), same non-computed-disclosure pattern as the existing, likewise-unregistered `sector_basis` card — no divergence risk. |

Both the ingest-finalize hook (`data_manager.py:4512-4544`, new "compass content" phase) and the API route (`apps/backend/app/api/compass.py:1094`) call the identical `compass.get_or_create_manifest` — one create-once/serve-from-storage function reached from two trigger points, exactly the architecture blueprint.md's Data Contract row describes ("computed once at ingest finalize (or once on first GET...) and served from storage thereafter"). No second producer, no duplicate table, no duplicate route.

## Information Architecture check

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| J-02 What-changed card → `/` | OK | Rendered inside `apps/frontend/app/page.tsx:709` (`<CompassWhatChangedCard compass={state.compass} />`), above the unmodified `DashboardBody`. `/` is the blueprint's registered canonical home for J-02 and is the existing landing route (0 clicks). No new route added. |
| J-03 Summary card → `/` | OK | `apps/frontend/app/page.tsx:709` (`<CompassSummaryCard .../>`), same page, same as above. |
| J-04 Next-session focus section → `/` | OK | `apps/frontend/app/page.tsx:711` (`<CompassFocusSection .../>`), same page, same as above. |
| J-04 "Next-session focus" disclosure → `/methodology` | OK | `apps/frontend/app/methodology/page.tsx:586-588` renders `CompassSelectionCard` as a sibling of the existing `SectorBasisCard`, inside the already-registered `/methodology` route (1 click from the persistent nav). Reuses the established disclosure-card pattern rather than inventing a new surface. |
| Sidebar / nav skeleton | OK — unchanged | No `sidebar.tsx` (or any nav/router component) appears in the 27-file changeset (confirmed against the full file list in `iter-diff.md`'s header and `git status`). Matches the iter-2 spec's explicit "No nav-skeleton change — the sidebar keeps its current 'Dashboard' label until J-08's swap." No parallel shell: all three new cards render inside the existing `DashboardPage` component in the existing app shell. |

No duplicate-home or undiscoverable-route findings: no new page/route was introduced this iteration (only a new API endpoint, `GET /api/compass`, and three new components inserted into the two already-registered pages).

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

None.
