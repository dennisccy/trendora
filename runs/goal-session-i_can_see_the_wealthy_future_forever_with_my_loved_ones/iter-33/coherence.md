**Verdict:** COHERENCE-PASS

## Iteration 33 — Dynamic point-in-time universe (J-93/J-94/J-96/J-95)

Audited against blueprint at
`runs/goal-session-i_can_see_the_wealthy_future_forever_with_my_loved_ones/state/blueprint.md`
using `git diff HEAD` (all iter-33 changes are uncommitted working-tree modifications).

---

## Part A — Data Contract check

### Registered values inspected

**`universe_count` (blueprint line 335) — migration to as-of-dependence**

The blueprint registers `universe_count` as computed by `data_manager.compute_coverage` and served on
`GET /api/data`. Iter-33 migrates this value from a static `len(cfg.universe.symbols)` to the
point-in-time resolved count. The implementation:

- `data_manager.py`: `_resolved_universe(session, as_of, cfg)` calls
  `universe_resolver.resolve_with_reasons` ONCE per `compute_coverage` call.
- `compute_coverage` sets `"universe_count": len(resolved_admitted)` at line 575 — the SINGLE
  computation path (no second call to `universe_resolver`).
- `_coverage_diagnostic_absent` receives the already-resolved `universe` list from the caller
  (`compute_coverage` passes `universe=resolved_admitted`) — no second resolution at `data_manager.py:366`.
- No other endpoint or module independently computes the as-of-dependent `universe_count`.

**No duplicate computation. No non-canonical source. PASS.**

---

**`coverage + per-symbol + missing-data diagnostic` (blueprint line 336) — additive J-94 diagnostic**

The `universe_diagnostic` field is a READ-ONLY re-projection of the already-computed `resolved` dict
(`data_manager._universe_diagnostic(resolved, cfg)` at `data_manager.py:400`). It reads no new DB
rows and recomputes no canonical value. Served on the existing `GET /api/data` coverage block. The
`UniverseDiagnosticPanel` in `data/page.tsx:931` displays values from
`state.data.coverage.universe_diagnostic` — no client-side count recomputation.

**No duplicate computation. PASS.**

---

**`membership_timeline` (blueprint line 337) — new J-96 field on `GET /api/data`**

`_membership_timeline` in `data_manager.py` is a READ-ONLY derivation over the stored `ScannerResult`
membership sets + bars + config. It calls `universe_resolver.resolve_with_reasons` per snapshot date
to get excluded-by-reason counts (strictly causal). The `MembershipTimelinePanel` in `data/page.tsx:1020`
renders values from `state.data.coverage.membership_timeline` — no client-side membership computation.
Served on the existing `GET /api/data` coverage block as the `membership_timeline` additive field.
No new endpoint, no new route.

**No duplicate computation. PASS.**

---

**`methodology resolved_size` (blueprint line 335)**

After J-93, the blueprint specifies that `resolved_size` on `/methodology` reports the static
candidate-universe size (the full-pool denominator), while the date-dependent resolved count moves
to `GET /api/data universe_count`. `methodology.py:144` sets `candidate_size = len(config.universe.symbols)`
and returns it as both `resolved_size` and `candidate_pool_size`. The frontend methodology page reads
`selection.resolved_size` — this is now the static candidate-universe count, which matches the stated
migration in the blueprint. The as-of-dependent count is served exclusively by `GET /api/data`.

This is NOT a drift — it is the blueprint-specified migration. The two surfaces now serve different
(complementary) values under different labels. **PASS.**

---

**`forward_symbols_for_run` — new function in `forward_testing.py`**

`forward_symbols_for_run` at `forward_testing.py:105` computes the per-run symbol set as
`stored ScannerResult tickers ∪ benchmark_symbols`. This is NOT a new computation of any canonical
score or return value — it narrows the iterated symbol set; the forward return computation itself
(entry close on D, bars after D) is byte-identical. The function reads the stored `ScannerResult`
tickers (the single membership source) and is used at `forward_testing.py:390` and `:862` in place
of the global `forward_symbols(cfg)` superset. The original `forward_symbols` is preserved as a
back-compat superset for other callers.

**No duplicate computation. PASS.**

---

**`universe_resolver.py` — new engine module**

`universe_resolver.resolve_members` and `resolve_with_reasons` are the SINGLE canonical per-date
membership path. `scoring.score_stocks` imports `resolve_members` (from `scoring.py:48`) and calls
it ONCE at the top of the function (line 249). `data_manager._resolved_universe` calls
`resolve_with_reasons` once (line 334). No other module calls these functions (confirmed by grep).
The module carries no threshold literals (all reads from `cfg`) consistent with the
`test_no_magic_numbers` CALC_FILES requirement stated in the spec.

**Single membership path. PASS.**

---

### New displayed values not in prior contract

All new values (`universe_diagnostic`, `membership_timeline`, `candidate_pool_count`,
`candidate_universe_count`, `universe_asof`) are registered at blueprint lines 335-337 as part of
the J-93/J-94/J-96 data-contract additions. No unregistered values introduced.

---

## Part B — Information Architecture check

### New surfaces in this iteration (from UI surface map)

| Surface | Route | IA home |
|---------|-------|---------|
| `UniverseDiagnosticPanel` | `/data` | Data Manager (blueprint line 293) |
| `MembershipTimelinePanel` | `/data` | Data Manager (blueprint line 293) |
| `BackwardHistoryPanel` | `/data` | Data Manager (blueprint line 293) |
| Empty-state copy update | `/stocks` | Stocks (blueprint line 282) |
| Point-in-time row count change | `/stocks`, `/themes`, `/sectors`, `/scanner-runs` | Existing homes |

All three new panels are implemented inside `apps/frontend/app/data/page.tsx` — they are components
rendered within the existing `/data` page (no new `page.tsx` files, no new route directories).

**No new route added. All surfaces within their IA-canonical homes. PASS.**

### Navigation path check

No navigation files modified: only `app/data/page.tsx`, `app/stocks/page.tsx`, and `lib/api.ts` were
changed. The three new panels are reachable via the existing sidebar link to `/data` (1 click from
any page) — the panels are within the existing page content. The nav skeleton is unchanged.

**Reachable in ≤ 1 click from any page. PASS.**

### Duplicate home check

No new page for any existing entity. The `BackwardHistoryPanel` reuses the J-85 rebuild confirm
chrome within the `/data` Data Manager page — not a second page for the rebuild feature.

**No duplicate home. PASS.**

### Parallel shell check

No new layout or nav shell introduced.

**No parallel shell. PASS.**

---

## Part C — Advisory observations (WARN only)

**WARN: `UniverseSelection` TypeScript interface not updated for new backend fields.**

`methodology.py._universe_selection` now returns three new fields: `candidate_pool_size`,
`per_date_rule`, and `per_date_min_history_bars`. The frontend `UniverseSelection` interface in
`apps/frontend/lib/api.ts:942` does not declare these fields. The Methodology page
(`app/methodology/page.tsx:245`) will silently ignore them — the per-date rule prose will not appear
on `/methodology`.

This is NOT a data-contract violation (the values are genuinely new additions to the methodology
section, not duplicates of any registered value, and the existing `resolved_size` display is
unaffected). It is a UI-completeness gap: the new per-date rule documentation is produced by the
backend but not rendered. The decomposer should register these fields in the `UniverseSelection`
interface and surface them on the Methodology page in a future iteration.

Specific gap: `apps/frontend/lib/api.ts:942` — add `candidate_pool_size: number`,
`per_date_rule: string`, `per_date_min_history_bars: number` to `UniverseSelection`; then
`apps/frontend/app/methodology/page.tsx` can render the per-date rule prose.

---

## Summary

| Rule | Result |
|------|--------|
| Part A — `universe_count` single computation path | PASS |
| Part A — `universe_diagnostic` no duplicate computation | PASS |
| Part A — `membership_timeline` no duplicate computation | PASS |
| Part A — `universe_resolver` single membership path | PASS |
| Part A — `forward_symbols_for_run` not a duplicate computation | PASS |
| Part A — All new displayed values registered in blueprint | PASS |
| Part B — No new routes/pages | PASS |
| Part B — All surfaces within IA-canonical homes | PASS |
| Part B — Navigation path ≤ 1 click | PASS |
| Part B — No duplicate home | PASS |
| Part B — No parallel shell | PASS |
| Part C — `UniverseSelection` interface missing new methodology fields | WARN |
