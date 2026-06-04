# goal-i_can_see_the_wealthy_future_forever-iter-17 Execution Plan

**Goal alignment:** Delivers J-09 + J-10 (must-have journeys in `docs/goal.md`) by (1) as-of-scoping the
forward-test evidence aggregate, (2) relocating its single serving home from `/api/system-health` to
`/api/backtest`, and (3) retiring `/system-health` so the evidence has exactly one home. Matches the
blueprint's iter-17 nav-skeleton change and Data-Contract relocation. **No drift / no scope creep
detected** — the spec is the operator's committed re-scope (`d723133`).

**Already in place (verify, do NOT recreate):** `state/blueprint.reapproval-requested` marker EXISTS and
`blueprint.md` IA + Data Contract are ALREADY edited for iter-17 (the decomposer wrote them). Dev's job is
to confirm they describe the shipped relocation, not to re-author them.

## What to Build

- **As-of-scope the aggregate (critical seam).** Add an optional keyword cutoff to
  `forward_testing.compute_forward_aggregates(session, horizon, config=None, *, as_of: Optional[date] = None)`.
  When `as_of` is set, restrict the observation pool to runs with `ScannerRun.asof_date <= as_of` — a
  **single membership filter** applied at the `fr_rows` / `runs_with_fr` step (`forward_testing.py:555–567`)
  so it also bounds `ret_by_run_symbol`, `results`, `run_rows`, and the SPY/QQQ benchmark lists (all derived
  from `runs_with_fr`). `as_of=None` keeps today's all-history path **byte-identical** (== latest-date case).
  The grouping / excess / control-group / attribution math is **untouched**.
- **Surface it on `/api/backtest`.** Extend the response with
  `evidence_by_horizon = { h: compute_forward_aggregates(session, h, cfg, as_of=run.asof_date) for h in cfg.walk_forward.horizons }`
  using the already-resolved `run.asof_date` (from `resolved_run`). All horizons in the **single fetch** →
  the client-side horizon selector needs **no refetch** (preserves J-15/J-18).
- **Retire System Health.** Delete `app/api/system_health.py` + its `main.py` router registration/import;
  delete the frontend page + nav entry + the `fetchSystemHealth` client and `SystemHealthResponse` usage.
  Keep `compute_forward_aggregates` (now the Backtest evidence source). Clean **all** `/system-health`
  references in `apps/` source (incl. doc/comment refs in `research.py`, `forward_testing.py`, the `main.py`
  router; `config.yaml` default_horizon comment optional) so grep is clean. `.next/` build artifacts do not
  count — they get wiped before browser QA (iter-15 lesson).
- **Backtest page — evidence-aggregate sections.** Render from `evidence_by_horizon[viewHorizon]` (already in
  the payload): forward return **by A–E bucket** (J-09 headline), **excess vs SPY & QQQ**, **by setup**, **by
  regime**, **VCP-vs-non-VCP** (J-16) + `by_pullback_to_rising_dma` / `by_flat_base_breakout` (J-28), and the
  **control-group comparison** (J-10) — each cell with sample size `n`, honest NA below `min_sample`, and the
  survivorship-bias / universe-relative label. Re-points on (a) global as-of change and (b) the existing
  client-side horizon selector (no refetch).

## Agents Required

- developer: **yes** — backend (the `as_of` seam + `/api/backtest` payload + System Health retirement +
  tests) and frontend (Backtest evidence sections + remove SH page/nav/client).
- backend-data: **yes**
- frontend-ux: **yes**

## Frontend Present

yes

## Files to Create/Modify

**Backend**
- `apps/backend/app/engine/forward_testing.py` — add `as_of` kwarg + single membership filter to
  `compute_forward_aggregates`; update docstring ("System Health" → Backtest evidence). The only logic change.
- `apps/backend/app/api/backtest.py` — add `evidence_by_horizon` (per config horizon, `as_of=run.asof_date`).
- `apps/backend/app/api/system_health.py` — **DELETE**.
- `apps/backend/main.py` — remove `system_health` import + `include_router` line.
- `apps/backend/app/api/research.py` — update `/system-health` comment ref → `/api/backtest` (it is a
  consistency-invariant comment, NOT an import — verify and leave the J-29 logic intact).
- `apps/backend/tests/test_api_system_health.py` — **DELETE**.
- `apps/backend/tests/test_forward_testing.py` — add: as-of scoping (only runs `asof_date <= D`; `n` at early
  D < `n` at latest); **no >D leak** (a run dated > D contributes 0 to every group); `as_of=None` ==
  `as_of=latest` == today's all-history result; **re-home the consistency-invariant test**
  (`attribution.distribution.mean == overall.mean_return`) onto the as-of-scoped aggregate — *move, do not
  delete* (iter-2 lesson).
- `apps/backend/tests/test_api_backtest.py` — assert `evidence_by_horizon` keys/shape at a historical
  `?as_of=`; assert `GET /api/system-health` is gone (404); unknown/short horizon → NA, not fabricated.
- (verify `apps/backend/tests/test_research.py` J-29 invariant stays green — it reads the all-history default,
  which is unchanged.)

**Frontend**
- `apps/frontend/app/backtest/page.tsx` — render the evidence-aggregate section inside `BacktestResults`
  (which owns the lifted `viewHorizon`), keyed off `evidence_by_horizon[viewHorizon]`. Reuse the panel
  components currently in the SH page (extract them to a shared module, e.g.
  `apps/frontend/components/evidence-panels.tsx`, before deleting the SH page).
- `apps/frontend/lib/api.ts` — repurpose `SystemHealthResponse` as the per-horizon `EvidenceAggregate` type;
  add `evidence_by_horizon: Record<number, EvidenceAggregate>` to `BacktestResponse`; **remove**
  `fetchSystemHealth`.
- `apps/frontend/app/system-health/page.tsx` — **DELETE** (after extracting shared panels).
- `apps/frontend/components/sidebar.tsx` — remove the `{ href: "/system-health", … }` NAV entry (line 37) and
  the now-unused `Activity` icon import.
- `apps/frontend/components/evidence-panels.tsx` *(new, optional)* — shared Bucket/Excess/Breakdown/
  ControlGroup panels used by the Backtest evidence section.

**Markers / handoff**
- `runs/goal-session-.../state/blueprint.md` + `blueprint.reapproval-requested` — **verify** consistency
  (both already present/edited). Do not duplicate.
- `docs/handoffs/goal-i_can_see_the_wealthy_future_forever-iter-17-dev.md` — dev handoff.

## UI Evolution

- **New user-facing capability:** at any historical as-of date D, `/backtest` shows the forward-tested track
  record built from **only** snapshots dated ≤ D (expanding window); moving the global date earlier shrinks
  the sample, latest equals the full all-history aggregate. One page, one date control.
- **New information displayed:** on `/backtest` — as-of-scoped forward-return-by-bucket (A–E),
  excess-vs-SPY/QQQ, by-setup, by-regime, VCP-vs-non-VCP + pattern breakdowns, and the control-group
  comparison, each with `n` and honest NA. (Previously lived on the now-retired date-blind `/system-health`.)
- **New user actions:** none new — the **existing** global as-of switcher and **existing** Backtest horizon
  selector now also drive the evidence aggregate.
- **UI surface changes:** `/backtest` gains the evidence-aggregate panel; `/system-health` page + sidebar
  entry are removed.
- **Navigation changes:** sidebar **loses** the "System Health" entry (nav-skeleton retirement — the coupled
  reason J-09 ships with the SH removal: one entity cannot have two homes, invariant #12).

## Visual Requirements

- **Component patterns:** reuse the existing dense table/panel components (Card + tabular-nums tables, the
  shared evidence panels). Numbers monospace; A–E buckets colour-graded green→red; `n` shown on every cell;
  low-sample cells render NA in the warn token, never a fabricated 0.
- **Layout:** the evidence-aggregate panel is a **clearly-labeled, visually distinct** block — labelled the
  **expanding-window aggregate ("evidence from every snapshot dated ≤ D")** — separated from the per-date
  scorecard ("what this date's cohort did") so the two are not confused. Carry the survivorship-bias /
  universe-relative banner.
- **Placement (J-21 ordering, hard constraint):** the three leadership lists (Top Sectors / Themes / Ranked
  Cohort) MUST remain **below** Return Attribution. Put the evidence panel at the **very bottom** (after the
  leadership lists) — recommended — or the very **top** (before the as-of scan summary). **Never** between the
  scorecard, attribution, and leadership lists.
- **No page-local date control of any kind** (J-18, principal risk). The horizon selector is a *view*
  selector, not a date selector. The page URL stays date-free; the cutoff is the resolved global as-of
  (`run.asof_date`) transmitted as the existing `?as_of=` on the snapshot-served read.
- **States:** loading skeleton; explicit backend-unavailable state (no fabricated figures); honest NA / empty
  cohorts with `n`.

## Key Test Scenarios

- **Backend (run full pytest ONCE — ~14 min; never two concurrent runs):**
  - `compute_forward_aggregates(..., as_of=D)` pools only runs with `asof_date <= D`; `as_of=None` is
    byte-identical to all-history and equals `as_of=latest`; a run dated > D contributes 0 to every group
    (no >D leak).
  - `GET /api/backtest?as_of=<historical>` returns `evidence_by_horizon` with the expected per-horizon keys;
    `GET /api/system-health` → 404 (route gone). Unknown/short horizon → NA, not fabricated.
  - Relocated consistency invariant: `attribution.distribution.mean == overall.mean_return` on the
    as-of-scoped aggregate (moved from the SH test, not deleted).
  - Critical invariants re-verified by source/behaviour (no scoring/scanner/regime/pattern change): J-06/J-07
    byte-identical; no DB regen.
- **Browser (Chrome MCP, on a clean hydrated build — stop `next dev` by port, `rm -rf apps/frontend/.next`,
  restart, confirm `GET /_next/static/chunks/main-app.js → 200` before driving; never `npm run build` against
  the live `.next`):**
  - **J-09:** on `/backtest` read the by-bucket A–E table + excess vs SPY/QQQ + by-setup + by-regime (each
    with `n`); move the global as-of switcher to an earlier date (in-app nav/click, **not** a hard reload) →
    evidence re-points and `n` drops (distinct before/after screenshots + DOM/network assertion, de-duped by
    sha256); return to latest → matches all-history.
  - **J-10:** read the control-group comparison (top-ranked vs random-same-sector vs SPY/QQQ/sector ETF) at a
    stated horizon — each numeric and labelled.
  - **J-18 (principal anti-goal):** `/backtest` exposes **no** page-local date dropdown; toggling the global
    switcher re-points BOTH the per-date scorecard AND the evidence aggregate; the page URL stays date-free;
    the single `/api/backtest?as_of=` call is the global date being read (not a second state).
  - **Regression spot-checks on `/backtest`:** J-14 scorecard renders, J-19 attribution renders, J-21
    leadership lists below Return Attribution, J-16/J-28 breakdowns present; J-13 global as-of still re-points
    other pages; J-15 horizon change does not refetch.

## Out-of-scope guards (exclude — flagged per spec)

- **J-26** (composite factor cohort) and **J-32** (Research as-of toggle) — later iterations; do not touch
  `compute_factor_combination` / `research.py` lab as-of params this iter.
- **J-22 / J-23 / J-24** — Yahoo-429 data-walled and **non-halting**; do **NOT** autonomously re-probe/retry.
- **No new caching/persistence table** for the aggregate (read-only live grouping over `forward_returns`,
  now filtered ≤ D); per-request memoization optional, not required. **No DB schema change, no DB regen, no
  new config scoring literal.**
