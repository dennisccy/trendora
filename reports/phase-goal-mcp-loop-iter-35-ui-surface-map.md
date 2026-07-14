# goal-mcp-loop-iter-35 — UI Surface Map

**Phase:** goal-mcp-loop-iter-35
**Date:** 2026-07-14
**Written by:** ui-impact-analyst

---

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/data` | `DriftReportPanel` — absent state (`data-testid="drift-status-absent"`) | New component | J-21/B-304: the card's initial state before any Fetch job has ever produced a drift artifact | Ensure no file exists at the configured drift-report path (default `runs/goal-session-mcp-loop/state/drift-report.json`, override via `TRENDORA_DRIFT_REPORT_PATH`) — **note: this repo currently has a leftover file there with `status:"clean"` from dev testing; delete/move it first or this state will show "clean" instead.** Load `/data` and confirm the "Live-vs-seed drift" card (`data-testid="drift-report-panel"`) shows the muted gray text "No fetch has run yet — nothing to compare against the committed seed." |
| `/data` | `DriftReportPanel` — clean state (`data-testid="drift-status-clean"`) | New component | Confirms a Fetch job's overlap window matched the committed seed | Run a Fetch job whose fetched bars agree with `data/seed/prices/{symbol}.csv` for the overlap window, reload `/data`, and confirm the card shows the green-dot line "The most recent fetch matched the committed seed over the last 20 common date(s)." (the "20" is `config.yaml`'s `data_quality.drift.overlap_days`, rendered verbatim). |
| `/data` | `DriftReportPanel` — drift state (`data-testid="drift-status-drift"`) | New component (core J-21 capability) | Names the exact symbol + dates of a detected "adjustment seam" | Run a Fetch job where one seeded symbol's provider-returned bars differ (even by one cent, in any OHLCV field) from `data/seed/prices/{symbol}.csv` within the last 20 overlap dates. Reload `/data` and confirm the amber box lists that exact ticker under `data-testid="drift-affected-{symbol}"`, shows its exact mismatching date(s), and shows the words "adjustment seam" — and confirm a genuinely clean symbol is NOT listed. |
| `/data` | `DriftReportPanel` — unreadable state (`data-testid="drift-status-unreadable"`) | New component / error handling | A corrupted artifact must degrade honestly, never crash the page | Overwrite the file at the configured drift-report path with invalid content (e.g. the literal text `not-json`), reload `/data`, and confirm the card shows the amber message "The drift report exists but could not be read. Re-run a Fetch job to regenerate it." — and confirm the rest of the page (coverage panel, storage footprint, job panels) still renders normally around it. |
| `/` and every page (layout-mounted) | `PreflightBanner` — new drift reason (component file itself unchanged; `data-testid="preflight-banner"`) | Changed behavior | Backend's `compute_preflight` gained a 4th "drift" input; the banner's already-generic `reasons` list can now surface a new reason string | After the drift-triggering Fetch above, reload any page (e.g. the dashboard `/`) WITHOUT visiting `/data`, and confirm the top banner flips from the quiet green GO strip to the amber banner (`data-verdict="DEGRADED"`) whose bulleted reasons list includes "Live-vs-seed drift detected (adjustment seam) for: `<TICKER>`." |
| `/` and every page (layout-mounted) | `PreflightBanner` — recovery to GO | Changed behavior | Confirms the banner is not "sticky" once a later clean fetch supersedes the drifted one | Run a second Fetch job whose overlap window is fully clean (overwriting the drift artifact with `status:"clean"`), reload any page, and confirm the banner returns to the quiet strip `data-verdict="GO"` reading "GO — today's board is current." |

<!-- Change Type key used above: New component | Changed behavior -->

---

## Backend-Only Changes (No UI Impact)

Unusually for this diff, almost none of the backend production code is genuinely "no UI impact" — every production file below is either directly served to the frontend or is the compute/trigger layer immediately behind one of the two UI surfaces in the table above. Listed here for completeness, with the feed-through made explicit rather than claiming isolation:

- `apps/backend/app/engine/drift.py` (NEW) — the pure comparator + artifact read/write. No UI file itself, but its output is the exact JSON both UI-facing readers below serve verbatim (single source, confirmed by reading the code: `read_drift_report()` is the only reader either caller calls).
- `apps/backend/app/engine/data_manager.py` — wires the comparator into the Fetch job (`_run_job` / `_run_chunked_fetch` / new `_check_drift` helper). This is the trigger event: running a Fetch is literally what produces the artifact the two UI surfaces above display. No UI file itself.
- `apps/backend/app/engine/readiness.py` — `compute_preflight` gained the 4th `drift` component (confirmed by reading the function: `_apply("drift", ok, detail)` after `integrity`). This is served on `GET /api/health` (confirmed: `app/api/health.py` calls `compute_preflight` and returns it as the `preflight` field), which is the exact payload `PreflightBanner` renders — so this file's change is what puts new text into an existing, already-consumed API response.
- `apps/backend/app/api/data.py` — adds `"drift": read_drift_report()` to `GET /api/data` (confirmed at line 145), the exact field `DriftReportPanel` reads. Directly UI-serving.
- `apps/backend/app/config.py` / `config.yaml` — new `DriftCfg`/`DataQualityCfg`, extended `ReadinessCfg._validate` required-component set, and the `data_quality.drift` block + `readiness.severity.drift: degraded` entries. Not a UI file, but two of its values are literally rendered: `overlap_days: 20` is the number shown in the clean-state card text ("last 20 common date(s)"), and `severity.drift: degraded` determines the banner renders amber `DEGRADED` styling rather than red `NO-GO` styling when drift fires (confirmed in `preflight-banner.tsx`: `isNoGo ? "border-neg..." : "border-warn..."`).

The following are genuinely backend-only with zero UI surface affected (test files only):
- `apps/backend/tests/test_drift.py` (new) — unit tests for the comparator/path-resolution.
- `apps/backend/tests/test_api_data.py`, `test_readiness.py`, `test_data_manager_jobs_pipeline.py`, `test_health.py` — extended assertions for the new field/component/wiring.
- `apps/backend/tests/test_themes.py`, `test_sectors.py`, `test_indexes.py`, `test_config.py`, `test_config_engine.py` — each carries an inline synthetic `readiness.severity` config dict for unrelated engine tests; each now includes `"drift": "degraded"` only so config construction doesn't break under the new required-component validation. No relation to those files' own test subjects.

---

## Summary

- **Frontend surfaces changed:** 2 (`DriftReportPanel` on `/data`, new; `PreflightBanner` content on every page, behavior-only — the component file itself is unchanged)
- **New pages/routes:** 0
- **Modified components:** 1 new component (`DriftReportPanel`), 1 page file wiring it in (`apps/frontend/app/data/page.tsx`), 1 typed API-client file extended (`apps/frontend/lib/api.ts` — `DriftReport`/`DriftAffectedSymbol` types + additive `drift` field)
- **Navigation changes:** no (no new route, no new nav entry — `/data` is J-13's already-registered Data Manager home; the card is additive within it)
- **Backend-only changes:** 10 test files (zero UI impact); all other backend production files feed one of the two UI surfaces above (see table above for the exact chain)
