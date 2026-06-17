**Verdict:** COHERENCE-PASS

---

## Iteration 27 — Coherence Audit

**Session:** i_can_see_the_wealthy_future_forever_with_my_loved_ones
**Iteration index:** 27
**Iter name:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-27
**Snapshot SHA:** 55a050c65d045efd62794fe8d25dcb9bb0a21d6c
**Scope:** J-85 (universe-rebuild + coverage diagnostic) and J-86 (max-drawdown columns everywhere)

---

## Step 1 — Data Contract Check

### New values introduced

**J-86 — Max-drawdown per (run, symbol, horizon)**

- Registered in the blueprint this iteration (Data Contract, "Max-drawdown per (run, symbol, horizon)" row).
- Computed ONCE in `apps/backend/app/engine/forward_testing.py` at the `max_drawdown()` helper (line 151) called in `_insert_run_forward_returns` (line ~295). No other module defines a competing `max_drawdown` / drawdown computation function; grep across all engine files confirms the helper is exclusive to `forward_testing.py`.
- Read VERBATIM (no recompute) by:
  - `snapshot_serving.py:_forward_returns_by_symbol` — carries `fr.max_drawdown` from the stored row.
  - `snapshot_serving.py:_forward_returns_for_row` — reads from the stored map, no math.
  - `snapshot_serving.py:_leadership_returns_by_horizon` — passes `mdd_by_symbol` to the canonical `_leadership_returns` builder in `forward_testing.py`; no independent computation.
  - `research.py:_event_study_members` and `_event_study_members_by_horizon` — reads `fr.max_drawdown` verbatim for aggregate mean-MDD.
  - `forward_testing.py:_group_mdd` — groups stored drawdowns for aggregation; no computation of the raw drawdown.
- All frontend surfaces import formatting helpers (`fmtMdd`, `mddClass`) from the canonical shared module `apps/frontend/components/forward-return.tsx`. No client-side drawdown calculation found.
- Column registered in `apps/backend/app/db.py` `_ADDITIVE_COLUMNS` as `("forward_returns", "max_drawdown", "ALTER TABLE forward_returns ADD COLUMN max_drawdown FLOAT")`.

**J-85 — Universe-vs-latest-snapshot coverage diagnostic**

- Registered in the blueprint this iteration (Coverage row, `absent_from_latest_snapshot` annotation).
- Computed by `data_manager:_coverage_diagnostic_absent` (a private function in `apps/backend/app/engine/data_manager.py`), additively called from the existing single `compute_coverage` producer.
- Served on the same `GET /api/data` coverage block — no new endpoint.
- Frontend reads from `state.data.coverage.absent_from_latest_snapshot` which is the value from `GET /api/data`; no client-side recomputation.

**J-85 — Rebuild job (`kind="rebuild"`)**

- Extends the existing `POST /api/data/jobs` contract with a new `kind` literal; no new endpoint registered.
- The rebuild itself reuses the existing `_do_backfill` / `persist_run_payload` / `backfill_run_forward_returns` path and `_run_job` dispatcher — no second compute path for snapshots.

### Existing registered values

No new code path computes any previously registered value. In particular:
- `realized_return` is still inserted only in `forward_testing:_insert_run_forward_returns`.
- `_leadership_returns` (used for themes/sectors forward returns) is the same shared builder, now optionally extended with `mdd_by_symbol` — the pre-J-86 shape is byte-identical when `mdd_by_symbol=None`.
- `compute_event_study` / `compute_regime_setup_pattern_study` read stored drawdowns verbatim; no return/excursion is recomputed.

**Result: no Data Contract violation.**

---

## Step 2 — Information Architecture Check

### New routes / pages

The UI surface map confirms **0 new routes/pages**. All 10 changed UI surfaces land on existing IA homes:

| Surface | IA home | Status |
|---------|---------|--------|
| `/data` — RebuildPanel + coverage banner | Data Manager `/data` | Existing home |
| `/stocks` — MDD columns | Stocks `/stocks` | Existing home |
| `/stocks/[ticker]` — MDD in horizon cards | Stock Detail | Existing home |
| `/themes` — MDD columns | Themes `/themes` | Existing home |
| `/sectors` — MDD columns | Sectors `/sectors` | Existing home |
| `/backtest` — aggregate mean-MDD | Backtest `/backtest` | Existing home |
| `/research` — event-study + RSP mean-MDD | Research `/research` | Existing home |

No new top-level nav section, no new sidebar links, no new shell/layout — the nav/sidebar components are not in the diff.

**Result: no Information Architecture violation.**

---

## Step 3 — Advisory (WARN)

**WARN — Local `MaxDrawdownCell` wrapper defined in three page files**

`apps/frontend/app/stocks/page.tsx:755`, `apps/frontend/app/themes/page.tsx:306`, and `apps/frontend/app/sectors/page.tsx:150` each define a local `MaxDrawdownCell` function. All three import `fmtMdd`/`mddClass` from the shared `apps/frontend/components/forward-return.tsx` (no logic duplication), but they add a null branch that renders "NA" text with a tooltip rather than the shared component's "—" em dash. The value displayed (positive or NA) is identical; only the NA token differs across the `/stocks`/`/themes`/`/sectors` leaderboards versus the shared `MaxDrawdown` export. This is a presentational inconsistency, not a computation or source-of-truth violation.

Recommendation for a future iteration: replace the three local wrappers with the shared `MaxDrawdown` component extended to accept a `tooltip` prop, so NA presentation is consistent across all MDD-displaying surfaces.

---

## Summary

| Check | Result |
|-------|--------|
| Data Contract — new max-drawdown value | PASS — computed once in `forward_testing.py`, read verbatim everywhere |
| Data Contract — coverage diagnostic | PASS — computed once in `data_manager.compute_coverage`, no new endpoint |
| Data Contract — rebuild job | PASS — extends existing `POST /api/data/jobs`, no second compute path |
| Data Contract — existing values | PASS — no new code path for any registered value |
| IA — new routes/pages | PASS — 0 new routes; all surfaces on existing homes |
| IA — navigation reachability | PASS — all surfaces are ≤2 clicks from nav; nav is unchanged |
| IA — duplicate home | PASS — no entity gains a second home |
| Advisory — local MaxDrawdownCell wrappers | WARN — minor NA-display inconsistency (em dash vs "NA" text) |
