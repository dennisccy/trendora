# goal-market-compass-iter-3 — UI Surface Map

**Phase:** goal-market-compass-iter-3
**Date:** 2026-08-20
**Written by:** ui-impact-analyst

---

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/` | `CompassManifestStrip` — badges + hash chips + dataset/universe stamps (`data-testid="compass-manifest-strip"`, `"compass-manifest-badges"`) | New card | J-05/J-06: proves each close's manifest was frozen, stamped, and identity-hashed, not just computed | Navigate to `http://localhost:3255/`, step the as-of switcher to a historical date (click the "◀" `data-testid="asof-step-prev"` button once), scroll to the "Manifest" card (below "Next-session focus"); verify a mode badge ("retrospective" or "at ingest"), a "version N" badge, a "frozen"/"not frozen" badge, a "prospective-eligible"/"not prospective-eligible" badge, a "Frozen …" timestamp line, and four hash chips labeled "Engine identity", "Candidate rule", "Cohort rule", "Manifest config" (each a short value ending in "…") all render |
| `/` | `CompassManifestStrip` basis-disclosure line (`data-testid="compass-manifest-basis"`) | New element | Read-time comparison of the frozen manifest's recorded source run vs. the CURRENT stored run for that as-of — never a mutation or recompute | On the Manifest card, verify a "Basis:" badge reading one of "Basis: available", "Basis: rebuilt", or "Basis: unavailable" is visible directly below the dataset/universe stamp line |
| `/` | `CompassManifestStrip` audit-table `Disclosure` (comparison cohort + near-threshold shadow, `data-testid="compass-manifest-cohort-semantics"`, `"compass-manifest-shadow-label"`) | New expandable table | J-05/J-06: full transparency into every non-selected member's frozen context and disposition, not just a count | Click the row whose summary text starts "Audit table — comparison cohort (" inside the Manifest card; verify it expands to a "Comparison cohort (non-selected pool)" table with a rightmost "Disposition" column reading "below selection floor" or "excluded by cap" per row, and — below it — a second table under the amber label "Near-threshold shadow — research-only substrate, not part of selection or display ranking" with no Disposition column |
| `/` | `CompassManifestStrip` "Regenerate manifest" button + `RegenerateConfirmModal` (`data-testid="compass-manifest-regenerate-button"`, `"compass-manifest-regenerate-confirm-modal"`, `"compass-manifest-regenerate-confirm-button"`) | New confirm-gated action | J-06: mint a labeled new, non-destructive version without ever touching the original | With the as-of switcher on a historical date, click the amber "Regenerate manifest" button on the Manifest card; in the modal titled "Confirm manifest regenerate" click the "Regenerate manifest" button in the modal footer; verify the modal closes and the card updates in place (no page reload) to a higher "version N" badge and a "not prospective-eligible" badge |
| `/` | `CompassManifestStrip` Versions list (`data-testid="compass-manifest-versions"`) | New element (conditional — renders only once >1 version exists) | J-06: both versions stay listed with their own stamps once a regenerate has happened | After regenerating once (row above), verify a "Versions" section appears on the Manifest card listing at least two rows ("v1", "v2", …), each showing its own mode, "eligible"/"not eligible", and a generated-at timestamp |
| `/` | `CompassManifestStrip` regenerate gating while on "Latest" (`data-testid="compass-manifest-regenerate-unavailable"`) | Changed/gated behavior | Regenerating the live-tracking frontier view has no stable target date (UI-only convenience gate) | With the as-of switcher showing "Latest" (its badge, `data-testid="asof-indicator"`, reads "Latest" not "Viewing as-of … (historical)"), verify the Manifest card shows the sentence "Regenerate is available only for a stored historical date — step the as-of switcher off "Latest" first." and shows NO clickable "Regenerate manifest" button |
| `/` | `CompassManifestStrip` pre-freeze-era state (`data-testid="compass-manifest-pre-freeze-era"`) | New honesty state | Legacy iter-2-era manifest rows carry no freeze/integrity block and must never be shown as if frozen | View an as-of date whose stored manifest predates iter-3 (`mode` is null — e.g. the live frontier date if no new ingest-finalize has run since deploy); verify the Manifest card shows ONLY the sentence "This manifest predates the freeze/integrity block — no stamps were recorded for it." with no badges, hash chips, or audit table |
| `/` | `CompassManifestStrip` unavailable state (`data-testid="compass-manifest-strip-unavailable"`) | New honest-degradation state | Matches the other three compass cards' existing "backend not reachable" precedent (AG-8 graceful degradation) | Stop the backend (or block the `/api/compass` request) and reload `/`; verify the Manifest card renders a red-bordered box reading "Manifest strip is unavailable — backend not reachable, or this session has not been frozen yet." instead of a blank space, spinner, or crash |
| `/` | `CompassSummaryCard` "Show cited facts" disclosure (existing component, `data-testid="compass-summary-card"`) | Changed display (bug fix, TC-36) | A cited fact could render a raw floating-point artifact (e.g. "-0.20000000000000284"); must display rounded | On `/`, expand "Show cited facts" under the Summary card; verify every numeric fact value (e.g. `regime_score_delta`) shows exactly 2 decimal places (e.g. "6.27"), never a long unrounded float |
| `/` | `CompassFocusSection` candidate card "Cautions" text (existing component, `data-testid="compass-candidate-<TICKER>"`) | Changed text (TC-34) | Caution text must state the fact only — no advice-sounding tail (AG-2) | On `/`, in "Next-session focus", open a candidate card whose Cautions list includes an entry starting "ATR_RISK_BUDGET:"; verify the sentence ends with "of universe)." and does NOT contain the phrase "sized risk accordingly" |
| `/data` | `BackfillBreakdown` "Refreshed:" line (existing component, `data-testid="aggregates-refreshed"`) | Changed text (TC-1) | The finalize phase name must read "next-session manifest" (hyphenated), matching J-05 step 1's disclosure wording exactly | After a snapshot job whose finalize tail runs the compass freeze (e.g. a "Backfill snapshots" job that completes successfully), find the "Refreshed:" line in the Job progress panel or a Run history row; verify it lists "next-session manifest" (hyphenated) — not "next session manifest" (no hyphen) |

<!-- Change Type options used above: New card | New element | New expandable table | New confirm-gated action | New honesty state | New honest-degradation state | Changed display | Changed text | Changed/gated behavior -->

---

## Backend-Only Changes (No UI Impact)

- `apps/backend/app/models.py` — `NextSessionManifest`'s additive freeze/integrity columns + the new
  composite `(as_of, version)` unique constraint; `ScannerRun.engine_identity` column — schema only; the
  values reach the UI exclusively through the already-mapped `GET /api/compass` fields listed above.
- `apps/backend/app/db.py` — `_ADDITIVE_COLUMNS` registrations + the `as_of` → `(as_of, version)` index
  swap — an idempotent schema migration, no UI surface.
- `apps/backend/app/engine/scanner.py` — stamps `ScannerRun.engine_identity` on newly created runs — a
  provenance-only column never displayed on any run-history view; the Manifest card's own "Engine
  identity" chip is independently recomputed at freeze time via the same function, not read from this
  column.
- `apps/backend/app/config.py`, `config.yaml` — new `compass.manifest.*` (`schema_version`,
  `export_dir`, `availability_margin_seconds`) and `provenance.*` (`engine_files`, `config_keys`) config
  blocks — server-side tunables, not user-configurable from the page.
- `.gitignore` — excludes the new export-file directory from source control — repo hygiene, no UI
  impact.
- `docs/handoffs/trendora-next-session-manifest-v1.schema.json` — the committed JSON Schema describing
  the exported artifact's shape (the Tapeology-facing contract) — a documentation/validation artifact,
  never rendered anywhere in Trendora's own UI.
- The export writer (`_write_export` in `apps/backend/app/engine/compass.py`) — writes the byte-identical
  JSON file to `compass.manifest.export_dir`; the resulting file's path is stored on the DB row but never
  served via the API or shown in the UI (see "Not Visible Yet" in the companion user-visible-changes
  report).
- `apps/backend/app/engine/compass.py`'s `_scan_selection_language` banned-language-guard extension —
  an internal assertion added before `evaluate_selection` returns; changes nothing visible today (no
  banned term is currently present in any candidate reason/caution/why-not string) — it is a safety net
  for future wording, not a new displayed field.
- Test files: `apps/backend/tests/test_engine_identity.py` (new), `test_manifest_invariants.py` (new),
  plus extensions to `test_compass.py` / `test_api_compass.py` / `test_ingest_finalize_compass.py` /
  `test_db.py` / `test_no_magic_numbers.py` — test-only, no UI impact.

---

## Summary

- **Frontend surfaces changed:** 11 (rows in the table above)
- **New pages/routes:** 0
- **Modified components:** 1 new (`CompassManifestStrip`, with 8 distinct testable states/sub-elements)
  + 3 existing components whose rendered output changed (`CompassSummaryCard`'s cited-facts formatting,
  `CompassFocusSection`'s candidate-card caution text, `/data`'s `BackfillBreakdown` refreshed-line text)
  + `apps/frontend/app/page.tsx` (wires the new card into the page)
- **Navigation changes:** no — no new route, no sidebar/nav change; the Manifest card is reached by
  scrolling the existing `/` page (per `blueprint.md`: "its expanded table IS the manifest audit view;
  no separate nav route exists for it")
- **Backend-only changes:** 9 (rows in the section above)
