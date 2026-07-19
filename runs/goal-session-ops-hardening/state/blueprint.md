# App Blueprint — ops-hardening

<!--
Coherence contract for the ops-hardening goal session. Drafted at baseline (iter-0) from
docs/goal.md's Product Shape + Must-have journeys, cross-checked against the actual codebase
(apps/frontend/components/sidebar.tsx, apps/backend/app/engine/*, apps/backend/app/models.py).
Auto-approved per default run-goal.sh behavior; re-review any time with --require-blueprint-approval.

This session is layered on top of the prior `mcp-loop` goal session (GOAL_ACHIEVED 2026-07-16,
25/25 journeys, archived at docs/archive/goal-mcp-loop.md). Product Shape is explicit: this cycle
is additive ops/performance/correctness work, not a rewrite — the IA below is the SAME app shell,
extended only where J-01/J-03/J-04/J-05/J-06 require it.

REVIEW CHECKLIST:
  1. Information Architecture — sensible nav, every ops-hardening journey has an obvious home?
  2. Data Contract — every shared value has exactly ONE source? [TARGET] rows mark values whose
     canonical module/endpoint is DECIDED (per goal.md Product Shape) but not yet fully built —
     iterations completing them must not invent a second source.
-->

## Information Architecture

**Layout shell:** persistent left sidebar (nav) + main content area; a global top-bar readiness
badge is present on every page (not a nav item); a layout-level preflight banner renders above
main content whenever the preflight verdict is `DEGRADED`/`NO-GO` (calm, factual, never blank).

**Navigation skeleton** (unchanged this cycle — confirmed against `sidebar.tsx`; goal.md's Product
Shape names 9 of these 11 explicitly as "existing nav unchanged," Scanner Runs and Methodology are
pre-existing items it doesn't re-list but which the Non-Goal "not a rewrite" bars removing):

```
Trendora
├── Dashboard          /                       — home card, market phase, major indexes
├── Stocks             /stocks                 — leaderboard (→ /stocks/{ticker} detail on row-click)
├── Themes             /themes
├── Sectors            /sectors
├── Scanner Runs       /scanner-runs           — run list (→ /scanner-runs/{runId} on row-click)
├── Backtest           /backtest
├── Research           /research               — index of 15 labs (event-study, factor-lab, regime-lab, …)
├── Evidence           /evidence                — certified-claims ledger
├── Watchlist          /watchlist
├── Methodology        /methodology
└── Data Manager       /data                   — THIS CYCLE'S PRIMARY SURFACE: job form, live
                                                  progress, persisted run/job history, coverage panel
[global, all pages] Readiness badge (top bar) + Preflight banner (layout-level, conditional)
```

**Feature / journey homes** (each reachable in ≤2 clicks from the persistent nav):

| Feature / journey | Canonical home (route) | Nav section |
|---|---|---|
| J-01 — Backfill honors requested range, explains zero-work | `/data` (job form + persisted run-history panel) | Data Manager |
| J-03 — No per-run range cap (chunked, unrestricted) | `/data` (same job form; live chunk progress) | Data Manager |
| J-04 — Non-blocking boot, visible status | global readiness badge (top bar, every page) + preflight banner; interrupted-job state on `/data` | (global) / Data Manager |
| J-05 — Aggregates precomputed at ingest | `/scanner-runs` (stored leaderboard), `/data` (coverage payload), `/` (market phase card) — cross-cutting, no single new page | Scanner Runs / Data Manager / Dashboard |
| J-06 — Pages load only what they need | cross-cutting measurement; canonical artifact is `reports/perf-budgets.md` (not a UI page) | (all pages, measured) |

## Data Contract

Every value below must read the same everywhere. `[TARGET]` marks a value whose canonical
module + endpoint are DECIDED by `docs/goal.md`'s Product Shape but not yet fully implemented —
the iteration that builds it must use exactly that module/endpoint, never a second one.

| Value / entity | Computed by (single module/function) | Served by (single endpoint) | Notes |
|---|---|---|---|
| Evidence status / certified-claim (signal, as-of) | `app.engine.referee` + `app.engine.ledger` | `GET /api/evidence` | Unchanged this cycle (mcp-loop legacy). |
| Leadership / Entry Quality / Risk scores | `app.engine.scoring` | `/api/stocks`, `/api/sectors`, `/api/themes`, dashboard endpoints | Unchanged this cycle. |
| Regime score, market phase, realized forward-returns | `app.engine.regime`, `app.engine.market_phase`, `app.engine.forward_testing` | per-page endpoints (dashboard/stocks/research) | Unchanged this cycle; J-05 moves the market-phase cache's warm trigger from boot to ingest finalize — same `market_phase_cache` table, same serving path, byte-identical values. |
| Backend readiness / boot phase + preflight verdict | `app.engine.readiness.compute_readiness` / `compute_preflight` | `GET /api/health` | Already built (mcp-loop iter-28/iter-33). J-04 extends the SAME endpoint's evidence: persistent logfile, honest crash/unreachable presentation, interrupted-job detection — no new computing module. |
| Job history & per-date exclusion reasons | data-manager job engine finalize (`app.engine.data_manager`, backfill/fetch/rebuild path) → `data_provider_runs` table | `GET /api/data` (persisted `runs` list, survives restart/reload) + `GET /api/data/jobs/{job_id}` (live in-session poll of the currently-running job) — same underlying `_run_detail()` shape, two read paths for two lifecycles, never a second computation | `[TARGET, iter-1 building]` — `DataProviderRun` exists (status/message/dismissed/job_id) but has no structured per-date exclusion-reason field yet; iter-1 extends the SAME `_run_detail()` JSON blob persisted in `data_provider_runs.message` (no new DB column — same mechanism `date_failures`/`stages`/`omitted` already use), read by the SAME two endpoints, never a second job-history store. (Corrected this iteration: previously mis-described as served only by "`/api/data/jobs*` endpoints" — the persisted list is actually `GET /api/data`.) |
| Coverage payload (universe counts, per-symbol coverage, gaps, capacity) | `app.engine.data_manager.compute_coverage` | `GET /api/data` | `[TARGET]` — today computed per-request via `_compute_coverage_uncached`'s whole-table prefill (the documented OOM source); J-05 persists it as a `coverage_snapshot` row refreshed at ingest-finalize time, served by the SAME `GET /api/data` endpoint — no second coverage source. |
| Backfill run-summary contract (`dates_total`, per-date exclusion breakdown) | data-manager job engine, backfill finalize (`_do_backfill` in `app.engine.data_manager`) | `GET /api/data` (persisted `runs` list) + `GET /api/data/jobs/{job_id}` (live poll) | `[TARGET, iter-1 building]` — persisted-record shape per goal.md Product Shape. Exact fields (present for `backfill`/`both`/`rebuild` kinds only, null for `fetch`/`expand` — matching the existing `dates_total` nullability): `dates_total: int>=0` (REDEFINED this iteration to mean trading days in the requested range, not the old post-cadence/already-snapshotted-filtered target count), `calendar_days: int>=0` (inclusive calendar span of `[start,end]`), `non_trading_days: int>=0`, `already_snapshotted: int>=0`, `error_other: int>=0` (mirrors `len(date_failures)`), `snapshots_created: int>=0` (existing, unchanged). Invariants: `non_trading_days + dates_total = calendar_days`; `snapshots_created + already_snapshotted + error_other = dates_total`. J-01 builds this; J-03's chunk progress (new `chunk_index`/`chunk_total` for the backfill stage, reusing the existing fetch-only fields + the frontend's existing dormant chunk-progress badge) reads the same record — no second record. |
| Membership timeline / research hot-key caches | `membership_timeline_cache`, `event_study_cache` (existing tables) | `/data`, `/sectors`, `/themes`, `/research/*` first loads | `[TARGET: trigger only]` — tables and serving reads already exist; J-05 moves the warm-from-boot trigger into ingest finalize (`_do_backfill`/rebuild), same tables, same serving path, byte-identical values. |
| Page performance budgets (never-regress measurements) | N/A — a measurement artifact, not a served runtime value | `reports/perf-budgets.md` | Existing table (mcp-loop legacy) carries forward; J-06 adds the ≤5s boot budget and the cold `/api/data` budget as new rows in the SAME file — no second budgets file. |

No shared value in this contract may gain a second computing module or a second serving endpoint;
an iteration that needs one of the `[TARGET]` values reads/writes through the module + endpoint
named above, and removes its `[TARGET]` tag here once built (and confirmed passing by the
goal-evaluator — the decomposer does not self-certify a value as built until the evaluator scores
the journey that depends on it).
