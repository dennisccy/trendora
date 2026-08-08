# Iteration goal-ops-hardening-iter-53 — Coherence Audit

**Iteration:** goal-ops-hardening-iter-53
**Date:** 2026-08-08
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

---

## Scope note

`Frontend Present: no`, confirmed independently: `git diff 8f59adb2...` `--stat -- apps/frontend/` and
`git status --porcelain -- apps/frontend/` are both empty. The entire diff is four backend product files
(`apps/backend/app/engine/{data_manager,market_phase,universe_resolver}.py` + `_FAULT_INJECT_SITES`
wiring) and four test files, plus an append-only `reports/perf-budgets.md` addendum (204 insertions, 0
deletions — verified via `git diff --stat`). This iteration bounds GIL-holding, whole-history
`bars_asof(...)` fetches down to bounded-window fetches (`bars_asof_window`, `close_on`) inside two
already-registered finalize-tail phases (`coverage_membership_timeline_refresh`, `market_phase_warm`),
per the spec's own explicit license to apply "whichever chunked/bounded construct the profile actually
supports" if the GIL-hold source turned out not to be a `sorted()`/GC-pause shape (it didn't — profiling
found an unbounded fetch instead). No new page, route, nav entry, endpoint, computing module, or
displayed field.

## Data Contract check

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Regime score, market phase, realized forward-returns (`app.engine.market_phase`) | OK | `apps/backend/app/engine/market_phase.py:81` (`_latest_vix_on_or_before` now calls the pre-existing `close_on`), `:115` (`_severity_reading`'s benchmark window now calls the pre-existing `bars_asof_window`), `:142` (`_trailing_ma_reclaimed` same). Same module, same functions, same callers (`compute_market_phase`/`market_phase_cached`), no new endpoint, no new field. `bars_asof_window`/`close_on` are pre-existing (confirmed: `apps/backend/app/engine/prices.py` line 630/663, `grep` confirms both predate this diff — `prices.py` does not appear in `git diff` at all). |
| Coverage payload / Membership timeline (`app.engine.data_manager`, calling into `app.engine.universe_resolver`) | OK | `apps/backend/app/engine/universe_resolver.py:230` (`resolve_with_reasons` now calls `bars_asof_window` instead of `bars_asof`, passes the already-known `bar_count` through explicitly instead of re-deriving `len(bars)`), `apps/backend/app/engine/data_manager.py:4104-4110` (new `except MemoryError` branch inside `_refresh_ingest_aggregates`'s `coverage_membership_timeline_refresh` phase, mirroring the iter-8 pattern already applied to the sibling loops in the SAME function). Reached via the SAME chain (`refresh_coverage_snapshot` → `_compute_coverage_uncached` → `membership_timeline_cached` → `_excluded_counts_by_date` → `resolve_with_reasons`) this row and its sibling row already register; `universe_resolver.py` is a pre-existing helper `data_manager` calls into, not a second producer (matches the established precedent of iter-35/41/42 touching `app.engine.prices` under this SAME row without creating a second one). No new endpoint (`GET /api/data` unchanged), no new field. |
| No new displayed value / entity | OK | Spec's own "New information displayed: None" (`docs/phases/goal-ops-hardening-iter-53.md` "New information displayed" section) confirmed by the diff: `_FAULT_INJECT_SITES` gaining `"coverage_membership_timeline"`/`"market_phase"` (`data_manager.py:16`) is test-only wiring (`TRENDORA_FAULT_INJECT_MEMORY_ERROR` env-gated), not a served field; `resolve_candidate`'s new `bar_count` kwarg (`universe_resolver.py:164-166`) is an internal parameter, not a payload field; the new `except MemoryError` branch adds no field to `aggregates_refreshed`/`_run_detail()`. |

No duplicate computation and no non-canonical source found. Every touched function is the SAME
single canonical implementation the blueprint already registers under "Regime score, market phase,
realized forward-returns" and "Coverage payload" — bounded to a smaller read, not re-implemented
elsewhere. Byte-identity is asserted by 7 new unit tests across the two touched modules (3 in
`test_market_phase.py`, 4 across `test_universe_resolver.py`/`test_data_manager_membership_cache.py`)
plus 2 new fault-injection tests proving the existing MemoryError isolate-and-continue contract still
holds when the fault fires from inside the newly-bounded fetch itself.

## Information Architecture check

No new page, route, or feature this iteration (zero `apps/frontend/` changes, verified above) — nothing
to check against the IA table. Every touched backend value keeps its existing home per the spec's own
"Blueprint conformance" section (`/data` for Coverage payload / Membership timeline; the Dashboard/
research per-page endpoints for market phase) and the ui-surface-map's 0 "New pages/routes" / 0
"Modified components" / "no" navigation-changes summary.

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| (none — no new surface this iteration) | N/A | `apps/frontend/components/sidebar.tsx` unchanged (not in `git diff`); ui-surface-map confirms 0 new routes |

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- **Not a coherence issue, flagged for the next decomposer's blueprint hygiene only.** The iteration's
  own audit (`docs/handoffs/goal-ops-hardening-iter-53-audit.md`, finding B1, verdict `PASS_WITH_GAPS`)
  found — by execution, not reading — that `_severity_reading`'s and `_trailing_ma_reclaimed`'s bounded
  fetch (`market_phase.py:115`, `:142`) is off by one calendar day relative to the `>= start` filter it
  feeds (the filter admits `lookback_days + 1` calendar days inclusive; the fetch supplies only
  `lookback_days`), which the auditor demonstrated flips the served phase label on a constructed fixture
  (harmless at the live committed config only because real trading-day density leaves margin, per the
  auditor's own production-reachability check). This is a **correctness** finding (AG-3 territory, the
  auditor's domain), not a Data Contract violation under this skill's Part A rules — it is a bug inside
  the SAME single canonical function, not a second producer or a non-canonical source, so every consumer
  of `compute_market_phase` still agrees with every other consumer (no "numbers don't match" split
  between two surfaces). Per this iteration's own binding TC-9/DoD-5 sequencing rule, the audit correctly
  filed it as a note for iter-54 rather than applying a code-changing fix, so I am not re-litigating it as
  a coherence FAIL either — doing so would functionally re-trigger the exact post-lane-fix problem TC-9
  exists to prevent. Only actionable item for whoever closes B1: the blueprint's "Regime score, market
  phase, realized forward-returns" row (Data Contract, iter-53 entry) currently carries an unqualified
  "byte-identical" claim in the code comments this row's Notes reference — once B1 is fixed (or
  deliberately accepted as harmless-with-margin), the next decomposer should correct that claim's wording
  the same way the iter-53 decomposer already corrected iter-52's mechanism description in this same row.
- The blueprint's own "Membership timeline / research hot-key caches" row iter-53 entry still reads
  "targeted, not yet built" and describes the mechanism as the generic "cooperative-scheduling treatment"
  (chunked yield points) — the shipped mechanism turned out to be bounded-window fetching instead
  (profiling found a different bottleneck than iter-52's `sorted()`/GC-pause pair, exactly as the spec's
  own contingency clause anticipated). This is the SAME kind of after-the-fact mechanism correction
  iter-53's own decomposer already applied to iter-52's row this iteration ("iter-52 mechanism
  correction, filed by the iter-53 decomposer") — expected, established housekeeping for iter-54's
  decomposer to apply next, not a coherence defect in the current diff.
