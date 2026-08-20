# Iteration 3 — Coherence Audit

**Iteration:** goal-market-compass-iter-3
**Date:** 2026-08-20
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

<!-- COHERENCE-PASS: no objective violations; at most minor advisory notes -->

---

## Data Contract check

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Next-session manifest — CONTENT block (`session_delta`, `narrative`, `selection.candidates`/`why_not`/`disposition_tally`, `content_hash`) | OK — unchanged scope/producer/endpoint | `apps/backend/app/engine/compass.py:380` (`build_manifest_payload`, unchanged contract); served only via `apps/backend/app/api/compass.py:57` |
| Next-session manifest — FREEZE/INTEGRITY block (`mode`,`version`,`frozen`,`generation.*`,3 hashes,`dataset`,`universe`,`comparison_cohort`,`near_threshold_shadow`,`caveats`,`prospective_eligible`,`available_at_utc`,`manifest_hash`,`export_path`) | OK — one writer (`_freeze_manifest`) behind all 3 producer paths; one read endpoint | `apps/backend/app/engine/compass.py:648-822` (`_freeze_manifest`, single sha256 site at line 803); called from `get_or_create_manifest` (858) and `regenerate_manifest` (885); served by `apps/backend/app/api/compass.py:57` (GET) and the confirm-gated action `apps/backend/app/api/compass.py:74` (`POST /compass/regenerate`, verified it calls the identical `regenerate_manifest` → `_freeze_manifest`, never a second assembler) |
| Engine identity | OK for its two intended read sites; blueprint's third planned site not yet wired (see Advisory) | Single definition: `apps/backend/app/engine/engine_identity.py:44` (`compute_engine_identity`). Exactly two call sites confirmed by repo-wide grep: `apps/backend/app/engine/compass.py:690` (freeze writer → `generation.engine_identity`) and `apps/backend/app/engine/scanner.py:117` (`persist_run_payload` → `ScannerRun.engine_identity`). No second implementation anywhere. |
| Evidence / certified-claim ledger status (composed into `caveats.evidence`) | OK — reads the same ledger, no second computation | `apps/backend/app/engine/compass.py:528-542` (`_evidence_caveat` calls `evidence.build_evidence_payload`, the same function the existing evidence chips use) |
| Stock-sector-label basis disclosure (composed into `caveats.sector_basis`) | OK (same source field), minor DRY note — see Advisory | `apps/backend/app/engine/compass.py:545-552` (`_sector_basis_caveat` reads `cfg.methodology.universe_selection.sector_basis` directly) vs. the pre-existing `apps/backend/app/engine/methodology.py:83-95` (`_sector_basis`, same field) |
| Dataset stamp | OK — reuses the single-sourced J-72 stamp, not duplicated | `apps/backend/app/engine/compass.py:717` calls `_dataset_version` imported from `app.engine.research` |
| `universe.member_count` | OK — reused from `evaluate_selection`'s own count, not re-queried | `apps/backend/app/engine/compass.py:682,718` ("one source, not two" per inline comment) |
| `comparison_cohort` / `near_threshold_shadow` row fields (scores, buckets, setup, sector, close, ATR%, gap, distance-to-invalidation, ADV) | OK — every field read from the run's already-stored `record_json`/`ScannerResult` columns; no new bar reads, no new blended score | `apps/backend/app/engine/compass.py:194-242` (`_cohort_row`) reusing `_record_json_by_ticker` (155-170) bounded to the one run's member set |
| Regime label+score, Market phase/severity/P(bear), Breadth, Sector/theme scores, Stock leadership/entry/risk scores, Coverage, Run summary, Readiness/preflight verdict | OK — all read-only via their existing canonical modules; only new read is `readiness.compute_preflight` for `generation.preflight_verdict`, explicitly kept off the market/narrative surface | `apps/backend/app/engine/compass.py:692-699`; frontend confirms non-rendering at `apps/frontend/components/compass-manifest-strip.tsx:97-99` (docstring: "deliberately never rendered here") |
| Frontend manifest strip data source | OK — reads only the `compass` prop (from the page's single `fetchCompass` call); the only new network call is the explicit user-triggered `POST /compass/regenerate` action, not a parallel read path; no client-side hash/derivation | `apps/frontend/app/page.tsx:97` (`fetchCompass`), `apps/frontend/components/compass-manifest-strip.tsx:11,131` (`regenerateManifest`, called only from `handleConfirm`) |

## Information Architecture check

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| Manifest strip card on `/` | OK — canonical home per blueprint, 0 additional clicks (already on the Today page), no new route, no parallel shell | `apps/frontend/components/sidebar.tsx` unchanged since before this iteration's snapshot (last touched at `eb3f1f12`, predates snapshot `b30d0912`); `apps/frontend/app/page.tsx` diff only inserts `<CompassManifestStrip .../>` between the existing focus section and `DashboardBody`, using the page's existing `Card`/`CardHeader`/`CardContent` primitives (no bespoke layout) |
| `POST /compass/regenerate` confirm control | OK — an inline confirm-gated button + co-located modal on the same card, not a navigable surface | `apps/frontend/components/compass-manifest-strip.tsx:240-276` (button + `RegenerateConfirmModal`, mirrors the existing `RebuildConfirmModal` pattern per its own comment) |
| No new routes/pages | OK | `git diff --stat` vs snapshot shows only `apps/frontend/app/page.tsx` modified under `apps/frontend/app/`; no new file added there |

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- **Engine identity — `GET /api/runs` exposure not yet wired.** The blueprint's Data Contract row for
  "Engine identity" lists two serving locations: `GET /api/compass` (`generation.engine_identity`, done
  this iteration) and `GET /api/runs` (`ScannerRun.engine_identity`, additive column). The column was
  added (`apps/backend/app/models.py:215-221`, `apps/backend/app/db.py:134`) and is stamped at persist
  time (`apps/backend/app/engine/scanner.py:117`), but `apps/backend/app/api/runs.py`'s `GET /runs`
  handler (lines 33-52) still hand-builds its response dict with the pre-iter-3 field set and does not
  include `engine_identity` — it is not exposed there yet. This is not a coherence drift (no duplicate
  computation, no wrong-endpoint serving — the field simply isn't read at that one site yet), and the
  blueprint's own iter-3 update note already keeps this row tagged `[TARGET — iter-3 build in progress]`
  rather than `[LIVE]`, so the gap is self-disclosed rather than silently claimed done. Iter-3's own IN
  SCOPE list and TC-6 only require the column + persist-time stamp, not the `/api/runs` exposure, so this
  reads as a deliberately deferred half of the row rather than a missed deliverable — flagging for the
  next iteration to close (add `engine_identity: run.engine_identity` to the `runs()`/`run_detail()`
  response dicts) if a journey ever needs it client-side.
- **`caveats.sector_basis` re-reads the config field directly instead of calling the existing
  `methodology._sector_basis(config)` helper.** Both resolve `cfg.methodology.universe_selection.
  sector_basis` — the same single source value, confirmed identical text — so this is not a duplicate
  *computation* of a different result. The new site (`apps/backend/app/engine/compass.py:545-552`) adds a
  defensive `None`/falsy fallback ("Sector label basis disclosure is not configured for this build.") that
  the original `methodology.py:83-95` helper does not have, a minor DRY inconsistency worth collapsing to
  one call site in a future tidy-up, not a coherence blocker.

No other advisory issues found. The regenerate action, the new hash/provenance fields, the cohort tables,
and the pre-freeze-era/unavailable degradation states were all traced to a single canonical producer and a
single serving endpoint, consistent with the blueprint's iter-3 update note.
