**Verdict:** COHERENCE-PASS

## Iteration 23 — Coherence Audit

**Session:** i_can_see_the_wealthy_future_forever_with_my_loved_ones
**Iteration index:** 23
**Iter name:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-23
**Target journeys:** J-81 (Themes/Sectors forward-return columns), J-82 (RSP table fixes)

---

## Step 1 — Data Contract

### J-81: Forward returns on /themes and /sectors

The new `_leadership_returns_by_horizon` function in `apps/backend/app/engine/snapshot_serving.py:87`
calls the SAME `forward_testing:_leadership_returns` builder (`apps/backend/app/engine/forward_testing.py:519`)
that Backtest's Top Themes / Top Sectors already use. It issues ONE `SELECT` from `forward_returns` per
run and builds a per-horizon index; `_forward_returns_from_projection` reads from that index per row.
No second computation, no second query path, no client-side recomputation.

The `ForwardReturnEntry` interface in `apps/frontend/lib/api.ts:265` is a unified type that replaces the
prior `StockForwardReturn` (which is now a type alias to `ForwardReturnEntry`). This is a re-naming
consolidation, not a parallel formatter or a new value type — no violation.

The "Per-stock forward returns" Data Contract row in the blueprint explicitly registers the J-81 themes
and sectors surfaces as `[TARGET iter-23]` and authorizes them as a new read surface of existing stored
data via the SAME `_leadership_returns` builder — the iteration promotes those TARGET rows to built,
consistent with the contract.

No new canonical value is introduced. `ThemeRow.forward_returns` and `SectorRow.forward_returns` are
additive payload fields reading verbatim from stored rows — no recompute, no second endpoint.

**Result: no Part A violation.**

### J-82: RSP samples validation

`apps/backend/app/engine/samples.py:360` now derives the accepted set from `_rsp_combination_members`
(the SAME observation builder the study groups by), replacing the prior static vocabulary cross-product
with a dynamic emitted-combination check. This is a serve-side reconciliation reusing the same builder
and predicate — it widens acceptance to emitted combinations only, does not disable validation, and
does not introduce a second grouping or recomputation.

The `test_j77_samples_invalid_selectors_raise` update in `apps/backend/tests/test_iter20_research_cluster.py:447`
adjusts the test contract to reflect that non-emitted combinations (including config-valid ones with no
study row) now correctly 4xx — consistent with the J-82(c) reconciliation.

No canonical value is changed; J-29/J-63 figures stay byte-identical per the spec.

**Result: no Part A violation.**

---

## Step 2 — Information Architecture

### New surfaces introduced

No new routes or top-level nav sections were added. All changes land on existing IA homes:

- `/themes` — top-level sidebar link (sidebar component, line 33). Five forward-return columns added
  to the existing leaderboard table. Reachable in 1 click. No duplicate home.
- `/sectors` — top-level sidebar link (sidebar component, line 34). Five forward-return columns added
  to the existing leaderboard table. Reachable in 1 click. No duplicate home.
- `/research` — top-level sidebar link (sidebar component, line 37). RSP table gains filter dropdowns,
  NA-last sorting, and Pooled default. Same existing page. No duplicate home.
- `/research/samples` — link-reached from RSP N= chips (already registered in blueprint as link-reached
  under Research). The J-82(c) backend fix makes every emitted combination's N= chip drill-down work
  without a 4xx. No new navigation change.

The blueprint IA section already registers J-81 under `/themes` and `/sectors` and J-82 under `/research`
and `/research/samples` as `[TARGET iter-23]`. The iteration delivers them on those exact homes.

**Result: no Part B violation.**

---

## Step 3 — Advisory observations

- The `fmtPct` alias in `apps/frontend/app/sectors/page.tsx:16` (aliased to `fmtFwdPct`) is a local
  collision-avoidance measure because the file already has a local `fmtPct` for the dist-from-high
  percentage. This is cosmetically inelegant but is not a data-contract violation — the shared
  `forward-return` component is used, not a parallel formatter. Advisory only.

---

## Summary

| Check | Status |
|---|---|
| Part A: Duplicate computation of a registered canonical value | None found |
| Part A: Non-canonical source for a registered value | None found |
| Part A: New value duplicating an existing registered concept | None found (J-81 read surfaces pre-registered) |
| Part B: New route with no nav path | None (no new routes) |
| Part B: Feature >2 clicks from nav | None |
| Part B: Duplicate home for an existing entity | None |
| Part B: Parallel shell | None |

**No objective violations. COHERENCE-PASS.**
