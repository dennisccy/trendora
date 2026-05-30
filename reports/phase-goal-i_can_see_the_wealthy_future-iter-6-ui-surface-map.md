# Phase goal-i_can_see_the_wealthy_future-iter-6 — UI Surface Map

**Phase:** goal-i_can_see_the_wealthy_future-iter-6 — Walk-forward forward-testing engine + System Health evidence (J-09, J-10)
**Frontend Present:** yes
**Date:** 2026-05-30
**Analyst:** ui-impact-analyst

> Note: authored under a degraded tool harness (read/bash result channel went empty after the initial artifact reads — the "queuing/flaky tool harness" the spec anticipates). Derived from the fully-read phase spec, dev handoff, and frontend handoff.

---

## File classification (diff-to-ui-impact)

| File | Classification | UI impact |
|------|---------------|-----------|
| `apps/frontend/app/system-health/page.tsx` | **frontend-direct** | The entire `/system-health` page replaced; all surfaces below |
| `apps/frontend/lib/api.ts` | **frontend-direct** (data layer) | Adds `SystemHealthResponse` types + `fetchSystemHealth(horizon, signal)`; powers the page; throws on non-200 → unavailable state |
| `apps/backend/app/api/system_health.py` *(new)* | **backend-api** | `GET /api/system-health?horizon=` — consumed directly by the page → visible |
| `apps/backend/app/engine/forward_testing.py` *(new)* | **backend-internal** | aggregation/backfill engine; surfaced only via the API aggregates |
| `apps/backend/app/engine/prices.py` | **backend-internal** | `bars_after` / `close_on` no-lookahead accessors; no direct UI |
| `apps/backend/app/models.py` | **backend-internal** | `ForwardReturn` (`forward_returns` append-only table); no direct UI |
| `apps/backend/app/config.py` | **config** | `WalkForwardCfg` / `ControlGroupCfg`; effect visible via cohorts/horizons |
| `apps/backend/main.py` | **backend-api / wiring** | registers router; runs `backfill_forward_returns` in lifespan |
| `config.yaml` | **config** | `walk_forward.{asof_cadence, default_horizon, control_group}` |
| `apps/backend/tests/*` | **non-UI** (tests) | no UI impact |

---

## Surface map

| Route/Page | Component/Element | Change Type | Why Changed | What to Test |
|-----------|------------------|------------|-------------|--------------|
| `/system-health` | Page root (was EmptyState stub) | New feature (stub → full dashboard) | iter-6 populates the System Health evidence dashboard (J-09, J-10) | Load `/system-health`; confirm the old EmptyState placeholder is gone and multiple data panels render |
| `/system-health` | Horizon selector (segmented 1/5/10/20/60) | New feature | Lets user pick the forward-return horizon; default 20; options from payload | Click `5d` (then `60d`); confirm `aria-pressed` moves to the clicked button AND the bucket/excess/control numbers change |
| `/system-health` | Survivorship-bias banner | New feature | Honesty caveat required by anti-goals | Confirm a prominent warn-toned banner with the survivorship-bias sentence is visible near the top |
| `/system-health` | Forward-return by score bucket table (A–E) | New feature (J-09) | Shows mean realized return + `n` per grade bucket from walk-forward snapshots | Confirm rows A through E each show a numeric mean return and a numeric `n`; bucket badge is colour-graded |
| `/system-health` | Excess vs SPY panel | New feature (J-09) | Shows cohort excess over SPY | Confirm it shows a numeric cohort mean, SPY mean, an excess value, and `n` |
| `/system-health` | Excess vs QQQ panel | New feature (J-09) | Shows cohort excess over QQQ | Confirm it shows a numeric cohort mean, QQQ mean, an excess value, and `n` |
| `/system-health` | By-setup-type breakdown table | New feature (J-09) | Mean forward return per setup type | Confirm each setup row shows a numeric mean return and a numeric `n` |
| `/system-health` | By-market-regime breakdown table | New feature (J-09) | Mean forward return per regime | Confirm BOTH a Risk-on and a Risk-off row appear, each with a numeric mean return and `n` |
| `/system-health` | Control-group comparison panel | New feature (J-10) | Compares top-ranked vs random peers vs benchmarks | Confirm the panel shows top-ranked cohort (highlighted), random same-sector, SPY, QQQ, and sector-ETF — each with a numeric return and label, each with `n`, at the selected horizon |
| `/system-health` | Per-figure `n` + low-sample flag | New feature | Sample sizes shown; `n < min_sample` flagged | Find a low-sample figure (e.g. bucket A at 20d) and confirm it carries the `⚠` warn flag rather than being hidden |
| `/system-health` | Pos/neg return colouring | New feature | Positive returns use `--pos`, negative `--neg` | Confirm at least one positive figure renders green and one negative figure renders red (palette tokens) |
| `/system-health` | Summary strip | New feature | Shows snapshots contributing, as-of date range, overall mean, legend | Confirm it shows a snapshot count, a date range, an overall mean, and the `n < min_sample ⚠` legend |
| `/system-health` | Loading state | New feature | Skeleton while fetching | Hard-reload the page and confirm a skeleton panel grid appears before data |
| `/system-health` | Backend-unavailable state | New feature | Honest error, no fabricated numbers | With backend stopped/unready, load the page; confirm a styled red alert appears (no zeros/fabricated figures) |
| `/system-health` | No-evidence / empty state | New feature | Explicit empty rather than zeros when `n_runs === 0` | Select a horizon with no realized data (if any); confirm an explicit EmptyState shows rather than fabricated 0% values |
| `/scanner-runs` (existing) | Runs history list | Changed behavior (more rows) | Walk-forward backfill adds 8 cadence as-of snapshots (11 runs total) | Confirm the runs list now includes the added walk-forward as-of dates AND the pre-existing runs are unchanged (immutable history, not a regression) |
| (API) `GET /api/system-health?horizon=` | New endpoint | New backend-api (consumed by page) | Serves `compute_forward_aggregates` verbatim | `GET /api/system-health` returns by-bucket/setup/regime + excess + control groups each with `n` + survivorship label; `?horizon=20` (default) and a non-default horizon work; an out-of-range horizon → 422; no price data → 503 |

---

## Backend-only (no direct UI surface this phase)

- `forward_returns` append-only table (`app/models.py`) — surfaced only as aggregates.
- `app/engine/forward_testing.py` — `forward_return`, `walk_forward_asof_dates`, `backfill_forward_returns`, `compute_forward_aggregates`.
- `app/engine/prices.py` — `bars_after` (date > D), `close_on` (close ≤ D).
- `config.yaml` / `app/config.py` — `walk_forward` cadence, default horizon, control-group params.
- `main.py` — router registration + lifespan backfill wiring.

These have no dedicated UI; their effect is observed indirectly through the `/system-health` dashboard (aggregates) and the added `/scanner-runs` history rows.
