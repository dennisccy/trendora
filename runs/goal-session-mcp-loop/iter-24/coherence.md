# Iteration 24 — Coherence Audit

**Iteration:** goal-mcp-loop-iter-24
**Date:** 2026-07-09
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

---

## Summary

iter-24 is the fast-platform "mechanical backend pass" (items B/C/D/G/H) plus the item-K storage-footprint
card. Confirmed via `git diff adaaa8885839ab2383671ac4492a141dd3512561` (no bounded `iter-diff.md` existed,
so the full noise-excluded diff was read directly — 18 non-test/report/doc files, 854 insertions / 40
deletions) cross-checked against `reports/phase-goal-mcp-loop-iter-24-ui-surface-map.md`. Every optimized
path (items B/C/D/G/H) re-serves an EXISTING registered Data Contract value through its EXISTING computing
module/endpoint — only the query/plan/cache mechanics changed, each backed by an explicit byte-identity
test. Exactly ONE new displayed value is introduced (the DB capacity snapshot, item K), and it is already
registered in `blueprint.md`'s Data Contract with the correct single module/endpoint/reader. No new page,
route, or nav change.

## Data Contract check

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| **DB capacity snapshot** (`db_file_bytes`/`daily_prices_rows`/`scanner_results_rows`/`forward_returns_rows`) — NEW this iteration | OK | Computed once: `apps/backend/app/engine/data_manager.py:406-431` (`compute_capacity`, pure `select(func.count())` introspection + file `stat()`, no canonical recompute). Exactly one call site: `apps/backend/app/api/data.py:140` (additive `"capacity"` key on the EXISTING `GET /api/data` `data_overview` payload — confirmed no new `@router` added, `git diff --stat` shows `api/data.py \| 3 +` only). Exactly one frontend reader: `apps/frontend/app/data/page.tsx:440` (`<StorageCapacityPanel capacity={state.data.capacity} />`) — grepped the whole frontend tree for `capacity`; no second reader exists. Registered verbatim in `runs/goal-session-mcp-loop/state/blueprint.md` Data Contract table ("DB capacity snapshot" row, `[building iter-24 — J-15/item K]`) before this audit ran. |
| Three per-stock scores (Leadership/Entry/Risk) + stored forward returns — `scoring:score_stocks` → `GET /api/stocks`, `GET /api/stocks/{ticker}` | OK | Item D adds `filtered_stock_rows` (`apps/backend/app/engine/snapshot_serving.py:213-238`), used by `stock_detail_payload` (`:250`) and `watchlist._canonical_rows` (`apps/backend/app/api/watchlist.py:105-118`). Verified by reading the surrounding module: `filtered_stock_rows` calls the exact SAME `_forward_returns_by_symbol`/`_forward_returns_for_row` helpers (`snapshot_serving.py:57`/`:79`) that the canonical `stored_stock_rows` (`:169`) uses, and the same `json.loads(result.record_json)` rehydration — it only narrows the SQL `WHERE` clause (`ScannerResult.ticker` filter) instead of scanning the whole run in Python. No second computation. `test_filtered_stock_rows_byte_identical_to_full_scan_row` (`test_api_engine.py:206-216`) asserts row-for-row equality against the full-scan path. |
| Readiness/warm-up state — `readiness.compute_readiness` → `GET /api/health` | OK | Item G's `_cached_warmup_dates` (`apps/backend/app/engine/readiness.py:59-72`) memoizes the SAME `_warmup_dates` function (not a reimplementation) and the grouped `ScannerRun.asof_date.in_(cadence_dates)` existence query is mathematically equivalent to the former per-date loop (`ScannerRun.asof_date` is unique). `test_readiness_grouped_existence_query_matches_per_date_check` (`test_health.py:131-146`) proves the two sets match. No new value. |
| Missing-data diagnostic — `data_manager._missing_data_diagnostic` → `GET /api/data` | OK | Item H's bulk `own_dates_by_symbol` query (`apps/backend/app/engine/data_manager.py:240-252`) is bounded to `universe` (config-sized, not a whole-table scan) and feeds the pre-existing, unmodified gap-diff logic below it. `test_diagnostic_query_count_does_not_scale_with_universe_size` (`test_data_manager.py:791-806`) proves query-count independence from member count; the diagnostic's own output logic is untouched. No new value. |
| Every other registered Data Contract row (regime, sectors, themes, forward-return aggregates, research cohorts, evidence status, index/macro vendor labels) | OK — untouched | Not present in the diff at all (confirmed against `git diff --stat`); items B/C are pure SQLite engine/schema tuning with no data-shape effect. |

No new displayed value is introduced beyond the one already registered (DB capacity snapshot); no
duplicate-of-existing-concept value found; the "unregistered value" check (Part A.5) does not apply since
the one new value is registered.

## Information Architecture check

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| Storage-footprint card on `/data` | OK | `apps/frontend/components/sidebar.tsx:32-44` — `NAV` array unchanged, still lists `{ href: "/data", label: "Data Manager", ... }` as a top-level, always-visible, 1-click entry (file not present in the diff at all). The new `StorageCapacityPanel` (`apps/frontend/app/data/page.tsx:440`) is inserted inline immediately after the existing `<CoveragePanel>` on the SAME `/data` page — no new route, no parallel shell, no duplicate home. Matches `blueprint.md`'s homes table, which already carries J-15 (`... + \`/data\` (DB capacity storage card) ...`) and J-16 rows under the existing Data Manager section. |

`ui-surface-map.md`'s own summary confirms "New pages/routes: 0" / "Navigation changes: no." No other
new feature/page exists this iteration to evaluate for reachability or duplicate-home/parallel-shell.

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- **Carried-forward WARN (not new, not worsened by this iteration):** `apps/frontend/components/index-regime-chart.tsx`
  and `apps/frontend/components/major-indexes-card.tsx` remain dead code — grepped the whole `app/` tree;
  neither `IndexRegimeChart` nor `MajorIndexesCard` is imported into any live page. First flagged at
  iter-22, carried at iter-23, and this iteration's own spec explicitly keeps it out of scope ("Deleting
  the dead-duplicate dashboard components... Defer to a dedicated tidy iteration"). Still correctly
  deferred — does not block this iteration, but the next tidy-up iteration should finally delete them.
- No formatting-drift or inconsistent-label issues found on the new storage card: `fmtBytes()`
  (`apps/frontend/app/data/page.tsx:132-140`) is pure display formatting of the server-provided byte
  count (1024-based units), and the three row-count metrics use the page's existing `toLocaleString()`
  convention already used elsewhere on `/data` — consistent with the established style.
