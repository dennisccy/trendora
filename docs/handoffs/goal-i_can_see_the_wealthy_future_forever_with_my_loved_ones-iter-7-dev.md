# goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-7 Dev Handoff

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-7
**Date:** 2026-06-12
**Agent:** developer
**Status:** complete
**Depth:** lean
**Target journeys:** J-51 (research sample-count drill-down), J-52 (sample-row → dated stock detail in a new tab)

## What Was Built

### Backend — `GET /api/research/samples` (a SELECT-only drill-down behind every published `N=`)

- **New engine module `apps/backend/app/engine/samples.py`** (`compute_samples`). It reproduces ONE
  published research cohort and lists its member observations — one row per observation: ticker, snapshot
  (as-of) date, the qualifying stored value(s), and the stored realized forward return at the stated
  horizon — plus a `total` that **EQUALS the published N by construction** (count-coherence keystone,
  invariant 13). Membership is derived through the SAME observation builders + the SAME slicing helpers the
  aggregates use — it recomputes NO factor, NO return, NO regime, NO membership rule:
  - **factor kind** → `research._factor_observations` (+ `_decile_member_slice` for a per-decile cohort; +
    the stored-`regime` filter for a by-regime cohort). Slices: `total` (== `n_total` == rank-IC n),
    `decile`, `regime`.
  - **combination kind** → `research._combination_observations` (+ `_combination_cohort_members` for the
    single/strict/composite index sets). Cohorts: `baseline`, `single` (by `single_index`), `composite`,
    `strict_overlap` (a valid n=0 returns an empty list + total 0).
  - **event-study kind** → `research._event_study_members` (+ the stored-`regime`/`sector` filter). Slices:
    `pooled` (== per-horizon n / n_total), `regime`, `sector`.
- **Shared-helper extraction in `apps/backend/app/engine/research.py`** so the samples endpoint and the
  aggregate **provably use one membership/slicing path** (the iter spec's blessed "extract a shared
  read-only helper" allowance — no change to the aggregate computations' outputs):
  - `_decile_member_slice(ordered, count, decile)` — the exact `ordered[lo:hi]` quantile slice; `_deciles`
    now calls it, and the samples decile cohort calls it (one quantile-edge definition).
  - `_combination_cohort_members(pool, resolved, comb)` — the single/strict/composite pool-index sets;
    `compute_factor_combination` now calls it (the inline block moved verbatim), and the samples
    combination cohort calls it (one membership-derivation path). **The aggregate's behaviour is
    byte-identical** (68 research engine tests + the full `-k samples` API suite confirm).
- **New API endpoint `GET /api/research/samples`** in `apps/backend/app/api/research.py`. Params fully
  reproduce a cohort: `kind` (factor|combination|event-study), `horizon`, factor-cohort selectors
  (`factor`/`slice`/`decile`/`regime`), combination selectors (repeatable `condition=<f>:<side>:<q>` /
  `cohort` / `single_index`), event-study selectors (`subject`/`slice`/`regime`/`sector`), and the optional
  `as_of` (the single global as-of, validated by the SHARED snapshot-served resolver — unparseable 422,
  future/before-history 400; J-32). **Invalid/unknown selectors → explicit 4xx (422)**; an empty 200 is
  reserved for a VALID n=0 cohort; `503` when no price data exists (mirrors the sibling research handlers).

### Frontend — `/research` chips become links + the new `/research/samples` page

- **Every published `N=` figure on `/research` is now a link** into `/research/samples` carrying the full
  cohort params (`apps/frontend/app/research/page.tsx`). All eight chip surfaces are wired: factor decile
  (mean + risk-adjusted cells), factor rank-IC (== n_total), factor by-regime, combination baseline/each
  single/composite/strict-overlap, event-study per-horizon, event-study by-regime, event-study by-sector.
  Chips clicked while in **As-of mode** carry the `scope=asof` cohort param; the global `?asof=D` is merged
  separately by the J-50 `useAsOfHref` helper (one author for the date param — no second date state).
- **New `apps/frontend/components/sample-link.tsx` (`SampleLink`)** — wraps the existing `SampleSize` chip
  (the single n-formatting source, so the displayed `n=…` + low-sample ⚠ is byte-identical) in a same-window
  `<Link>`. The header chips are SIBLINGS of any `TermInfo` info trigger, never nested (iter-5/iter-6
  lesson) — the chips live in the dedicated `n` column, structurally separate from the `TermInfo` markers
  in the column headers.
- **New `apps/frontend/lib/samples-link.ts`** — the ONE place the chip→drill-down param shape is defined
  (`buildSamplesHref` for the chips, `samplesFetchParams` for the page).
- **New page `apps/frontend/app/research/samples/page.tsx`** — deep-linkable + reload-safe (the params fully
  reproduce the cohort; behind a Suspense boundary for `useSearchParams`). Renders a cohort-description
  header (re-formatting the echoed cohort + scope + total), the survivorship-bias + descriptive caveat
  banner, and a samples table (ticker, snapshot date, qualifying stored value(s), realized forward return)
  whose displayed `total` equals the published N. **n=0 renders an explicit honest empty state**; column
  headers carry `TermInfo` tooltips reading the shared J-47 glossary (`as-of date`, `factor`/`setup status`,
  `forward return`). Dates render via the shared `formatIsoDate` (J-42).
- **J-52**: each row's ticker links to `/stocks/[ticker]?asof=<that row's snapshot date>` with
  `target="_blank"` + `rel="noopener noreferrer"` — the asof param is the ROW's snapshot date (NOT the
  page's global as-of), so the new tab restores that observation's own date through the one global control.
  All other links on the page stay same-window (the "Back to Research" link uses the J-50 `asofHref`).
- **New api client** in `apps/frontend/lib/api.ts`: `SamplesResponse`/`SampleRow`/`SampleCohort` types +
  `fetchSamples(params, asof, signal)` (repeated `condition` preserved; `as_of` appended via `withAsOf`
  only when a historical cutoff is active).

## Files Changed
- `apps/backend/app/engine/research.py` -- extracted `_decile_member_slice` + `_combination_cohort_members`
  (shared membership path); aggregates call them (outputs unchanged).
- `apps/backend/app/engine/samples.py` -- NEW: `compute_samples` + per-kind cohort reproducers (read-only).
- `apps/backend/app/api/research.py` -- NEW `GET /api/research/samples` endpoint (validation + 4xx/503/as_of).
- `apps/backend/tests/test_samples.py` -- NEW: 10 engine tests (count-coherence every chip kind/slice,
  value-identity, n=0 strict-overlap honest empty, as_of scoping, invalid-selector ValueError).
- `apps/backend/tests/test_api_research.py` -- +9 API tests (count-coherence vs the live aggregate
  endpoints, every chip kind; as_of echo+scope; 4xx invalid selectors; n=0 empty 200; 503 no data).
- `apps/frontend/lib/api.ts` -- samples types + `fetchSamples`.
- `apps/frontend/lib/samples-link.ts` -- NEW: `buildSamplesHref` / `samplesFetchParams` (the cohort param shape).
- `apps/frontend/components/sample-link.tsx` -- NEW: `SampleLink` (the linked `N=` chip).
- `apps/frontend/app/research/page.tsx` -- every `SampleSize` chip → `SampleLink` (8 surfaces); threads
  factor/subject/conditions/horizon/scope down; dropped the now-unused `SampleSize` import.
- `apps/frontend/app/research/samples/page.tsx` -- NEW: the deep-linkable drill-down page (J-51 + J-52).

## Tests Run
- **Backend engine** (`cd apps/backend && .venv/bin/python -m pytest tests/test_research.py tests/test_samples.py -q -p no:cacheprovider`):
  **78 passed** (68 research — the refactor is output-identical + 10 new samples).
- **Backend API — samples subset** (`... -m pytest tests/test_api_research.py -k samples -q -p no:cacheprovider`):
  **9 passed, 36 deselected** in 346.75s (real `loaded_engine` seed boot). Proves count-coherence at the
  endpoint level vs the live `/api/research/factor-lab` / `factor-combination` / `event-study` aggregates
  for every chip kind, the as_of echo+scope, the 4xx-on-invalid-selector contract, the n=0 empty-200 case,
  and the 503-no-data case.
- **Backend API — FULL `test_api_research.py` regression** (the `_combination_cohort_members` /
  `_decile_member_slice` extraction touches the aggregate path): run to completion in this dev turn —
  **45 passed in 542.30s (0:09:02), exit 0**. Confirms the shared-helper extraction did NOT regress any
  aggregate API behaviour (factor-lab / factor-combination / event-study) AND the 9 new samples API tests
  pass within it.
- **FULL backend pytest suite** (`cd apps/backend && .venv/bin/python -m pytest tests/ -q -p no:cacheprovider`):
  backend read endpoints were touched, so the full ~35–46-min suite is the gate. **Handed to the pump**
  (exceeds the subagent 10-min Bash cap; never run concurrently with another pytest; no backend server on
  :8835 during the run). Run by the **pump** to completion in a single background invocation: **710 passed,
  4 skipped, 0 failed** in 3878.92s (1:04:38); PYTEST_EXIT=0. Log: `/tmp/trendora-iter7-fullsuite.log`
  (START 2026-06-12T12:43:59Z → END 2026-06-12T13:48:40Z). +19 tests vs iter-6's 691 (the new
  `test_samples.py` engine tests + `/api/research/samples` API tests); aggregate outputs unchanged — the
  shared `_decile_member_slice` / `_combination_cohort_members` extraction introduced no regression. (An
  unrelated `tapeology` pytest shared CPU late in the run; separate project/DB — no interference.)
- **Frontend type-check** (`cd apps/frontend && npx tsc --noEmit`): **clean (exit 0)**. ESLint is not
  installed in apps/frontend — `tsc` is the frontend gate.

## Pre-handoff verification
- **Service startup**: not started by dev. The API tests use in-process `TestClient` (warm-seed
  `loaded_engine`), so no backend server was started on :8835 (per project memory — avoid the scanner-runs
  warm-up race). No dev server left running; ports 8835/3835 are free for the QA/browser agent. **A backend
  restart on :8835 is required for QA** so the new `/api/research/samples` route is served (serve-fast
  lifespan since iter-28 makes this safe on the warm DB; restart by killing the port's process only).
- **Live smoke** (in-process `TestClient` against the real seed): `GET /api/research/samples?kind=factor&
  factor=leadership_score&horizon=20&slice=total` → 200, `total` 20832, each row carrying ticker +
  ISO snapshot_date + the stored leadership value (read verbatim) + the realized forward return; cohort echo
  + survivorship label present.
- **External integrations / native deps**: none added (read-path only; no scraper/provider/dependency change).
- **No new config key** (a SELECT-only exposure needs none — confirmed; no inline test-config fixtures
  touched).

## Known Issues / Notes
- **A backend restart on :8835 is required for QA** so the new route is live (the iter spec flags this).
- **Payload size (no pagination, per spec)**: the largest chip is the factor `total` / rank-IC cohort
  (~20.8k rows on the full seed). The spec explicitly says serve the complete list and add virtualization
  ONLY if a real cohort demonstrably breaks rendering (and then page-size must come from config). Per-decile
  / per-regime / per-sector / combination slices are far smaller. The table renders plain rows; QA should
  spot-check that the largest cohort still renders (it is the worst case for the drill-down).
- **Count coherence is the veto line**: the drill-down `total` equals the published N by construction
  because membership flows through the SAME `_factor_observations` / `_combination_observations` /
  `_event_study_members` builders + the SAME `_decile_member_slice` / `_combination_cohort_members`
  helpers the aggregates now call — never a second membership rule, never a client-side recompute.
- **J-52 row date is the ROW's snapshot date**, not the page's global as-of — the new tab restores exactly
  the date that observation came from (verified by the as_of scoping test: every scoped row's snapshot_date
  ≤ the cutoff).
- **Glossary headers**: the samples table headers use real catalog terms (`as-of date`, `factor`,
  `setup status`, `forward return`); `TermInfo` degrades gracefully for any absent term (no crash, no
  marker). The `Ticker` header has no glossary entry, so it renders as plain text (no marker) by design.
