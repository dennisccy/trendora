# Iteration 13 — Coherence Audit

**Iteration:** goal-ops-hardening-iter-13
**Date:** 2026-07-23
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

---

## Data Contract check

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Index series (normalized-% major-indexes chart, J-44) | OK | Sole producer confirmed: `apps/backend/app/engine/indexes.py:194-247` (`index_series_cached_with_status`) computes via the unchanged `compute_index_series` (same file, pre-existing, lines 27-179) exactly once on a cache MISS, persists it into the new standalone `IndexSeriesCache` table (`apps/backend/app/models.py:562-624`), and on a HIT deserializes the stored payload with **zero** recompute (only `asof_date` is re-stamped via the pre-existing `resolve_as_of_date`, which is a re-format/re-derive of an echoed field, not a second computation of the series — matches the audit skill's "re-format is fine" rule). `apps/backend/app/api/indexes.py:41-51` routes only the exact unparameterized default hot key (`full=True`, `as_of is None`, `range in {None, default}`) through `index_series_cached`; every other combination still calls `compute_index_series` directly, byte-identical, confirmed by `test_api_indexes_non_hot_key_bypasses_cache_and_stays_byte_identical` (`apps/backend/tests/test_api_indexes.py:290-315`) and by a monkeypatched call-count assertion (`test_api_indexes_hot_key_second_request_hits_cache_without_recompute`, same file, asserts `compute_index_series` is called 0 times on the second hot-key request). `GET /api/indexes` remains the single endpoint (route/signature unchanged); no second endpoint, no client-side recomputation (no frontend files in the diff at all). |
| Backfill run-summary contract — `aggregates_refreshed` enum | OK | Same field, same `_run_detail()`/`JobProgress` record (`apps/backend/app/engine/data_manager.py:1886-1893`); `"index_series"` is appended in `_refresh_ingest_aggregates` (`apps/backend/app/engine/data_manager.py:3255-3287`) only when `index_series_cached_with_status`'s own `persisted` flag is `True` this run — no new field, no second record, gated identically to every other existing member (`test_finalize_hook_index_series_second_run_hit_not_reported_as_refreshed`, `apps/backend/tests/test_data_manager.py`). MemoryError is caught distinctly and isolated to this one step (mirrors the iter-8 convention already applied to every other warm loop in the same function), verified by `test_finalize_hook_index_series_memory_error_isolated_and_not_reported`. |

No new displayed value/entity was introduced this iteration outside the two blueprint-registered rows above (confirmed: `Data-contract additions` field in the iter spec, the blueprint's own iter-13 paragraph, and the diff itself — response shape of `GET /api/indexes` is unchanged).

## Information Architecture check

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| `/` (Dashboard) — `PhaseCrossViewCard`'s existing `GET /api/indexes?full=true` call | OK (no change) | No new route/page; `apps/frontend/` has zero changed files in this iteration's diff (`git diff --stat` against snapshot `e7b53447`). Confirmed also by the ui-impact-analyst's surface map (`reports/phase-goal-ops-hardening-iter-13-ui-surface-map.md`) and the ux-regression report, both of which independently confirm no navigation/sidebar/layout file is touched. |
| `/data` (Data Manager) — `IndexVendorPanel`'s existing `GET /api/indexes?full=true` call | OK (no change) | Same as above — pre-existing home, unchanged, latency-only effect. |

This iteration adds zero new pages, routes, nav entries, or UI components. No parallel shell, no duplicate home, no reachability regression is possible since nothing new was surfaced.

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- None. This iteration is a textbook example of the Data Contract's own "one canonical module, one canonical endpoint, cache is not a second producer" rule: the new `IndexSeriesCache` table is standalone (no `_ADDITIVE_COLUMNS` risk), keyed on a narrow, correctly-scoped `dataset_version` stamp, and both the developer's own tests and the ux-regression/ui-surface-map reports independently corroborate zero IA impact. The blueprint's iter-13 paragraph and the Data Contract table were updated in lockstep with the code (the `[TARGET, iter-13 building]` tag on the "Index series" row and the new `aggregates_refreshed` enum member both match what was actually built) — no bookkeeping drift to flag.
