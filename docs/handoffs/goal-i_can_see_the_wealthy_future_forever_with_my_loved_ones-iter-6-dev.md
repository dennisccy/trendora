# goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-6 Dev Handoff

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-6
**Date:** 2026-06-12
**Agent:** developer
**Status:** complete
**Depth:** lean
**Target journey:** J-49 (+ bundled `/stocks` nested-button fix)
**Chosen query-param name:** `full` (boolean; `?full=true`), used on BOTH `GET /api/indexes` and `GET /api/regime-history`.

## What Was Built

### J-49 — dashboard full-history market context + as-of marker (clamp-optional serving)
- **Backend, clamp-optional on `GET /api/indexes`** (`app/api/indexes.py` + `app/engine/indexes.py:compute_index_series`):
  added ONE optional boolean query param `full` (default `False`). When `full=true` the served upper
  bound widens from `bars_asof` (date ≤ resolved as-of) to `bars_through_latest` (the symbol's full
  stored path) — the post-as-of bars render as display-only market context. **Default (param absent /
  `full=false`) is byte-for-byte unchanged.** Same engine function, same range-start (lower bound), same
  rebase base (first in-range bar), same server-side normalization — only the upper bound moves, so the
  overlapping `≤ D` portion is value-identical between modes (no second compute path). The response still
  echoes the resolved `asof_date` (the client draws the marker from it). Unknown-range 422, invalid-`as_of`
  degradation, and honest omission of bar-less series (DIA) are all unchanged in both modes.
- **Backend, clamp-optional on `GET /api/regime-history`** (`app/api/regime_history.py` +
  `app/engine/regime_history.py:get_regime_history`): same `full` param. `full=true` returns the ENTIRE
  stored per-run regime series through the latest run (labels + scores read VERBATIM from immutable
  `scanner_runs` — nothing recomputed). Default stays clamped at `≤ resolved` (the stock-detail consumer
  keeps it — **J-45 not amended**).
- **Frontend `lib/api.ts`**: `fetchIndexes(...)` and `fetchRegimeHistory(...)` each gained a trailing
  `full = false` arg that appends `&full=true`. The stock-detail page calls them WITHOUT it → clamped (J-45).
- **Frontend `components/major-indexes-card.tsx`**: this surface always requests `full=true` from both
  endpoints regardless of the global as-of; it reads `isHistorical` from the as-of provider and passes it
  (plus the resolved `asof_date`) down to the chart. Range presets / toggle / legend behavior unchanged
  (re-normalization per J-44 still applies to the full-history series).
- **Frontend `components/index-regime-chart.tsx`**: for this surface it stops filtering regime points to
  `date ≤ asofDate` and feeds the shared `RegimeBandPrimitive` with `clip=null` → lines + step-function
  bands paint through the latest stored date. While `isHistorical`, it attaches a new
  `AsOfMarkerPrimitive` that draws a clearly visible vertical as-of divider line at D with an "as-of
  yyyy-MM-dd" label, reusing the J-20 `--warn` palette + label family from `price-chart.tsx` so the product
  reads as one design. No marker at the latest date. Hover tooltip (date + per-index % + stored regime
  label + score) and same-date band colors (shared `lib/regime.ts`) are unchanged.
- **Frontend `components/asof-marker-primitive.ts` (new)**: a small Lightweight-Charts series primitive
  that draws the full-height vertical as-of divider + label at D. Display-only chrome — it positions a line
  at the server-resolved date and computes nothing.
- **Stock-detail chart untouched**: `price-chart.tsx` and the detail page's regime-history request are not
  changed; the detail bands stay clamped at the as-of (J-45) and the J-20 forward region reads as before.

### Bundled iter-5 defect — `/stocks` nested-button fix
- **`app/stocks/page.tsx` `SortHeader`**: the `TermInfo` info affordance (which renders an `InfoTooltip`
  `<button>`) was previously rendered as the sort `<button>`'s children → an interactive `<button>` nested
  inside another `<button>` (invalid DOM, the source of iter-5's Next dev-overlay "1 error" badge). Fixed by
  restructuring: the sort button now contains ONLY the label text + sort indicator, and the term-definition
  info trigger renders as a SIBLING beside it (`<th>` → `<span>` wrapper → sort `<button>` + `<TermInfo
  term=… />`). Call sites pass `label` + `term` props instead of wrapping the label in `<TermInfo>` as
  children. Sort semantics intact: one visible indicator, `aria-sort`, `data-testid="sort-indicator"`,
  `#` restores stored rank (J-48 unaffected).
- **`components/ui/info-tooltip.tsx`**: the trigger's `onClick` now calls `event.stopPropagation()` before
  toggling — defensive belt-and-suspenders so clicking an info icon never bubbles into an enclosing control
  (e.g. triggers a sort), even if it is ever placed near one again.

## Files Changed
- `apps/backend/app/api/indexes.py` -- added optional `full` query param; forwards to engine.
- `apps/backend/app/api/regime_history.py` -- added optional `full` query param; forwards to engine.
- `apps/backend/app/engine/indexes.py` -- `compute_index_series(..., full=False)`; full mode uses
  `bars_through_latest`, default uses `bars_asof` (byte-identical to before).
- `apps/backend/app/engine/regime_history.py` -- `get_regime_history(..., full=False)`; full mode drops the
  `asof_date <= resolved` clamp, default keeps it (J-45).
- `apps/backend/tests/test_api_indexes.py` -- +6 API tests: `?full=` default byte-identity, through-latest +
  asof echo + overlap value-identity (indexes & regime), `?full=true` unknown-range still 422.
- `apps/backend/tests/test_indexes.py` -- +5 engine tests: full-mode through-latest, default byte-identity
  (regression pin), overlap value-identity, full-mode barless omission, full-mode unknown-range raises.
- `apps/backend/tests/test_regime_history.py` -- +3 engine tests: full-mode through-latest, default
  byte-identity, overlap value-identity.
- `apps/frontend/app/stocks/page.tsx` -- `SortHeader` un-nests the info affordance (sibling, not child);
  call sites use `label`+`term` props.
- `apps/frontend/components/asof-marker-primitive.ts` -- NEW: vertical as-of divider primitive (J-49 marker).
- `apps/frontend/components/index-regime-chart.tsx` -- full-history bands (no clip) + `isHistorical`
  vertical as-of marker; new `isHistorical` prop.
- `apps/frontend/components/major-indexes-card.tsx` -- requests `full=true`; passes `isHistorical` down.
- `apps/frontend/components/ui/info-tooltip.tsx` -- `onClick` `stopPropagation` (defensive).
- `apps/frontend/lib/api.ts` -- `fetchIndexes`/`fetchRegimeHistory` gained a `full` arg (`&full=true`).

Bookkeeping (already applied by the goal-decomposer, not by dev): the blueprint IA Dashboard line and the
two Data Contract rows ("Regime history series", "Normalized index display series") have their J-49 tags
flipped to "[TARGET — iter-6 in flight]" (additive, no re-approval — same convention iter-5 accepted).
**No data-contract additions** — same computing modules, same serving endpoints; the clamp simply becomes
optional per surface.

## git diff --stat
```
 apps/backend/app/api/indexes.py                   |  10 +-
 apps/backend/app/api/regime_history.py            |  17 ++-
 apps/backend/app/engine/indexes.py                |  26 +++-
 apps/backend/app/engine/regime_history.py         |  31 +++--
 apps/backend/tests/test_api_indexes.py            |  78 ++++++++++++
 apps/backend/tests/test_indexes.py                | 101 +++++++++++++++
 apps/backend/tests/test_regime_history.py         |  55 +++++++++
 apps/frontend/app/stocks/page.tsx                 | 100 +++++++++------
 apps/frontend/components/asof-marker-primitive.ts | 144 ++++++++++++++++++++++
 apps/frontend/components/index-regime-chart.tsx   |  46 +++++--
 apps/frontend/components/major-indexes-card.tsx   |  20 ++-
 apps/frontend/components/ui/info-tooltip.tsx      |   7 +-
 apps/frontend/lib/api.ts                          |  21 +++-
 13 files changed, 583 insertions(+), 73 deletions(-)
```

## Tests Run
- **New clamp-optional engine tests** (`cd apps/backend && .venv/bin/python -m pytest tests/test_indexes.py
  tests/test_regime_history.py -q`): **19 passed** in 0.67s.
- **New + existing API tests** (`cd apps/backend && .venv/bin/python -m pytest tests/test_api_indexes.py
  -q`): **11 passed** in 333.86s (warm-seed `loaded_engine` boot dominates) — includes the 6 new `?full=`
  API assertions (default byte-identity, through-latest + asof echo, overlapping-range value identity on
  both endpoints, `?full=true` unknown-range 422).
- **FULL backend pytest suite (the iteration gate — backend read endpoints touched)**:
  Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -q -p no:cacheprovider`
  Run to completion by the **pump** (the full ~45-min suite exceeds the subagent 10-min Bash cap; handed
  to the pump per the iter-2/iter-3 lessons) in a single background invocation; no concurrent pytest; no
  backend server running on :8835 during the run.
  Result: **691 passed, 4 skipped, 0 failed** in 2705.99s (45:05); PYTEST_EXIT=0. Log:
  `/tmp/trendora-iter6-fullsuite.log` (START 2026-06-12T10:03:08Z → END 2026-06-12T10:48:15Z). +13 tests vs
  iter-4's 678 (the new clamp-optional `?full=` indexes / regime-history tests); canonical outputs unchanged
  and the J-45 detail-chart clamp path untouched.
- **Frontend type-check**: `cd apps/frontend && npx tsc --noEmit` → clean (exit 0). (ESLint not installed —
  not a gate.)

## Pre-handoff verification
- **Service startup**: not started by dev (the running full pytest suite uses in-process `TestClient` /
  in-memory + warm-seed `loaded_engine`; per project memory I did NOT start a backend server on :8835 while
  pytest ran, to avoid the scanner-runs warm-up race). No dev server left running; ports 8835/3835 are free
  for the QA/browser agent to start cleanly. The `?full=` param is served by the existing endpoint code; QA
  must restart the backend on :8835 (kill by port only, never broad `pkill`) so the new param is live.
- **External integrations**: none added this iteration (read-path only; no scraper/provider change).
- **Native deps**: none added.

## Known Issues / Notes
- **A backend restart on :8835 is required for QA** so the new `?full=` param is served (the iter spec
  flags this). Safe on the warm DB (serve-fast lifespan since iter-28); restart by killing the port's
  process only.
- **Marker rendering**: the J-49 vertical as-of marker is drawn at D only while a historical date is
  selected (`isHistorical` true); at the latest date no marker is drawn and the full series == the clamped
  series, so the card reads exactly as J-44. The marker is a canvas primitive (not a DOM element), so
  browser-QA should assert it via a scrolled-to screenshot of the card (historical: data visible past D +
  visible vertical marker; latest: no marker), not via a DOM selector.
- **DIA** stays honestly omitted in full mode too (no stored bars) — J-49 is explicitly not gated on DIA.
- **No new config key** was added (presets/symbols already live in `config.index_chart`; the marker is
  positional at D, not a tunable) — so no inline test-config fixtures needed updating.
