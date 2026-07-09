# Phase goal-mcp-loop-iter-25 — UI Surface Map

**Phase:** goal-mcp-loop-iter-25
**Date:** 2026-07-09
**Written by:** ui-impact-analyst

---

## Context

This iteration shipped zero source changes (confirmed: `git diff HEAD --stat -- apps/backend apps/frontend config.yaml` is empty). The only substantive file change is `reports/perf-budgets.md` — an internal engineering measurement log, not a product UI surface (see Backend-Only section). Despite the empty diff, one existing surface — `/data`'s cold-boot request path — has a real, verification-worthy behavior change carried over from the previously-committed fix, so it and its constituent panels are mapped below with concrete re-validation steps rather than omitted.

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/data` | Whole page — cold-boot request path (first `GET /api/data` after a backend restart) | Changed behavior (regression fixed, no visual change) | The prior iteration's SQLite tuning (`mmap_size_bytes` = 1 GB × up to 30 pooled connections) exhausted the backend's 6144 MB memory cap and crashed the entire backend on the very first `/data` load after any restart. The already-applied `mmap_size_bytes: 0` fix removes that per-connection reservation; this iteration proved it holds via two live cold-restart HTTP tests (9.4–9.5 s, ~1.8 GB peak, HTTP 200, backend survived both times). | Fully stop the backend process, cold-start it (`scripts/start-backend.sh`), then immediately open `/data` in a fresh browser tab as the very first action against that instance. Confirm the page finishes loading (storage card and coverage panel populate, no blank or crashed tab) within roughly 10 seconds, then confirm `curl http://localhost:8255/api/health` still returns HTTP 200 afterward. Repeat the full stop → cold-start → load sequence a second time and confirm the identical result both times. |
| `/data` | `StorageCapacityPanel` (storage-footprint card: DB file size + 3 row counts) | No change — re-validation only | Introduced in the prior iteration; a crash on the cold path would have prevented this card from ever rendering, so its correctness must be re-confirmed now that the crash is fixed. | On the same freshly cold-started backend from the row above, once `/data` finishes rendering, read the four values shown on the storage card (file size and the `daily_prices` / `scanner_results` / `forward_returns` row counts). Independently call `GET /api/data` (browser Network tab or curl) and confirm all four displayed values match the response's `capacity` object exactly — expected file size ≈1.22 GB (1307414528 bytes), `daily_prices_rows` 3293160, `scanner_results_rows` 165755, `forward_returns_rows` 821054. |
| `/data` | `CoveragePanel` missing-data / gap diagnostic section | No change — re-validation only | Must still populate its diagnostic content (not a stuck loading state or blank section) on the same cold-start path that previously crashed the whole backend before this section could ever render. | On the same cold-started backend, once `/data` completes its first cold render, confirm the coverage/missing-data diagnostic section shows real gap content rather than a stuck loading skeleton or an empty panel. |
| `/data` | Backend-unavailable error card (existing error boundary) | No change — negative-path re-check | Anti-goal #8 requires exactly one contained error card (never a blank application-error page) when the backend is genuinely unreachable; this negative path must still hold now that the OOM cause has been removed from the positive path. | With the backend intentionally left stopped (do not restart it), load `/data` in a browser tab and confirm exactly one contained "backend unavailable"-style error card renders — not a blank white page, and not more than one stacked error element. |

<!-- Change Type key for this table: "Changed behavior" = the row's own runtime behavior differs from before, with no visual/markup edit; "No change — re-validation only" = the component's code and appearance are unmodified, but it must be exercised again because the previously-crashing path it lives on was not survivable long enough to reach it. -->

---

## Backend-Only Changes (No UI Impact)

- `reports/perf-budgets.md` — appended two new sections recording the live cold-restart HTTP measurements (wall time, peak memory) and a warm-budget re-confirmation. This is an internal engineering measurement log read by developers/auditors, not a page or file the Trendora product serves to end users — no UI surface affected.
- `config.yaml` (`database.pragmas.mmap_size_bytes: 0`) — confirmed present and unchanged this iteration; the fix itself was committed in the immediately preceding iteration. A SQLite engine-tuning value with no displayed field and no endpoint of its own — no direct UI surface, though it is the underlying cause of the `/data` behavior change captured in row 1 above.
- `runs/goal-session-mcp-loop/{session.json, summary.md, telemetry.jsonl, trace/*, state/blueprint.md}` and `reports/goal-session-mcp-loop-index.html` — goal-mode pipeline bookkeeping, telemetry, and the automation framework's own progress dashboard. These are artifacts of the development process itself, not part of the Trendora application's UI — no UI surface affected.
- Targeted backend test files re-run unedited this iteration (`test_bar_cache.py`, `test_api_engine.py`, `test_health.py`, `test_data_manager.py`, 123 passed) — test suites, not shipped code or UI — no UI surface affected.

---

## Summary

- **Frontend surfaces changed:** 0
- **New pages/routes:** 0
- **Modified components:** 0 (all four rows above are re-validation of existing, byte-identical surfaces — not new or edited UI)
- **Navigation changes:** no
- **Backend-only changes:** 4 (perf-budgets.md, config.yaml confirmation, goal-engine bookkeeping/dashboard, re-run test suites)
