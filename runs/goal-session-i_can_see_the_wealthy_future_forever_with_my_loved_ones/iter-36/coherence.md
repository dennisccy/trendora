**Verdict:** COHERENCE-PASS

## Coherence Audit — Iteration 36

**Session:** i_can_see_the_wealthy_future_forever_with_my_loved_ones
**Iteration index:** 36
**Iteration name:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-36
**Snapshot SHA:** 9a2f397140da5aad9efd67497bc30606f1e5ed1d

---

### Changed files (from diff)

Backend only — the UI surface map explicitly states "N/A — Backend-only phase (Frontend Present: no)":

- `apps/backend/app/engine/data_manager.py` — new `membership_timeline_cached()` function + warm `compute_coverage` update
- `apps/backend/app/engine/prices.py` — new `active_bar_cache()` helper + `_BarCache.trailing_count()` method
- `apps/backend/app/engine/universe_resolver.py` — resolver's history-gate prefilter uses `active_bar_cache()` when present
- `apps/backend/app/engine/warmup.py` — new `_warm_membership_timeline()` function called from `_run_warmup`
- `apps/backend/app/models.py` — new `MembershipTimelineCache` SQLModel (`table=True`)
- `apps/backend/tests/test_db.py` — `MEMBERSHIP_TIMELINE_CACHE_TABLES = {"membership_timeline_cache"}` added to expected-tables union

No frontend files changed. No new routes, pages, or nav links introduced.

---

### Step 1 — Data Contract check

**J-96 membership timeline (blueprint Data Contract row):**

The blueprint registers the canonical computing module as `data_manager._membership_timeline` → `compute_coverage`, and the canonical serving endpoint as the `membership_timeline` field on `GET /api/data`.

The diff introduces `membership_timeline_cached()` in `data_manager.py`. Inspecting the implementation:

- On a cache HIT it deserializes the stored payload (no recompute).
- On a MISS it calls `_membership_timeline(session, cfg, snapshot_dates)` — the SAME registered canonical function — persists the result under the current `_dataset_version` stamp, and returns it.
- `compute_coverage()` now calls `membership_timeline_cached(...)` instead of `_membership_timeline(...)` directly — the same module, same endpoint, same returned key in the coverage block.

This is a performance wrapper around the registered canonical function, not a new independent computation. The blueprint Data Contract row for J-96 was updated in this iteration's blueprint entry (line 337) to reflect exactly this cache pattern. No second computation path, no non-canonical source, no new displayed value.

**`_coverage_diagnostic_absent` optimization in `compute_coverage`:**

The diff conditionally reuses the already-resolved `resolved_admitted` set as `universe=absent_universe` when the requested as-of date equals the latest run date, eliminating a duplicate resolve call. The canonical computing module and endpoint (`GET /api/data` → `compute_coverage`) are unchanged; no value is recomputed by a second path.

**`active_bar_cache` / `trailing_count` in `prices.py` and `universe_resolver.py`:**

These are read-path helpers that source the trailing-bar count from an already-loaded in-memory series instead of issuing a per-date grouped-count DB query. The admission/exclusion logic (`resolve_with_reasons`) is byte-identical; no canonical score, return, or membership value is recomputed independently. The blueprint's "No recompute in the read path" anti-goal is not violated — this is an optimization of how a count is sourced, not a new derivation.

**New cache table (`MembershipTimelineCache`):**

Registered in `test_db.py` as `MEMBERSHIP_TIMELINE_CACHE_TABLES = {"membership_timeline_cache"}` exactly as the iter spec required. This is internal performance state (not a displayed value), mirrors the `EventStudyCache` / `MarketPhaseCache` precedent, and does not introduce a new endpoint or a second computation.

**Conclusion (Step 1): No Data Contract violation.** The canonical module and endpoint for every registered value are unchanged. The cache is a transparent performance layer behind the registered module+endpoint. No new displayed value is introduced; none of the existing registered values is computed or served via a second path.

---

### Step 2 — Information Architecture check

No new page, route, or navigation link was introduced in this iteration. The UI surface map confirms "No UI surfaces affected." The `/data` page itself is unchanged; it simply hydrates again because the endpoint now responds promptly.

No feature lacks a navigation path. No duplicate home. No parallel shell.

**Conclusion (Step 2): No Information Architecture violation.**

---

### Step 3 — Subjective observations (advisory)

None. This is a pure backend read-path performance fix with no user-visible layout, label, or formatting change.

---

### Summary

| Check | Result | Notes |
|-------|--------|-------|
| Data Contract — duplicate computation | PASS | `membership_timeline_cached` wraps `_membership_timeline`; not a second computation |
| Data Contract — non-canonical source | PASS | `GET /api/data` still serves `membership_timeline` from the same `compute_coverage` → `data_manager` path |
| Data Contract — new unregistered value | PASS | No new displayed value introduced |
| IA — navigation path | PASS | No new route or page |
| IA — reachability | PASS | No new surface |
| IA — duplicate home | PASS | No new surface |
| IA — parallel shell | PASS | No new surface |
