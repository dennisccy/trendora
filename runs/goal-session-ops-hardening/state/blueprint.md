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

iter-2 update: J-01/J-03's iter-1 `[TARGET]` fields are now built + evaluator-confirmed passing —
their tags are removed below. The Coverage payload and Membership-timeline/research-hot-key-cache
rows are retagged `[TARGET, iter-2 building]` (this iteration builds them); a new
`aggregates_refreshed` field is added to the Backfill run-summary contract row. No Information
Architecture change this iteration (no new page/nav; everything lives on the existing homes below).

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
└── Data Manager       /data                   — job form, live progress, persisted run/job history,
                                                  coverage panel (THIS + prior cycle's primary surface)
[global, all pages] Readiness badge (top bar) + Preflight banner (layout-level, conditional)
```

**Feature / journey homes** (each reachable in ≤2 clicks from the persistent nav):

| Feature / journey | Canonical home (route) | Nav section |
|---|---|---|
| J-01 — Backfill honors requested range, explains zero-work | `/data` (job form + persisted run-history panel) | Data Manager |
| J-03 — No per-run range cap (chunked, unrestricted) | `/data` (same job form; live chunk progress) | Data Manager |
| J-04 — Non-blocking boot, visible status | global readiness badge (top bar, every page) + preflight banner; interrupted-job state on `/data` | (global) / Data Manager |
| J-05 — Aggregates precomputed at ingest | `/data` (coverage payload + run-detail `aggregates_refreshed`), `/scanner-runs` (stored leaderboard), `/` (market phase card), `/research/*` (hot-key labs) — cross-cutting, no single new page | Data Manager / Scanner Runs / Dashboard / Research |
| J-06 — Pages load only what they need | cross-cutting measurement; canonical artifact is `reports/perf-budgets.md` (not a UI page) | (all pages, measured) |

## Data Contract

Every value below must read the same everywhere. `[TARGET]` marks a value whose canonical
module + endpoint are DECIDED by `docs/goal.md`'s Product Shape but not yet fully implemented —
the iteration that builds it must use exactly that module/endpoint, never a second one.

| Value / entity | Computed by (single module/function) | Served by (single endpoint) | Notes |
|---|---|---|---|
| Evidence status / certified-claim (signal, as-of) | `app.engine.referee` + `app.engine.ledger` | `GET /api/evidence` | Unchanged this cycle (mcp-loop legacy). |
| Leadership / Entry Quality / Risk scores | `app.engine.scoring` | `/api/stocks`, `/api/sectors`, `/api/themes`, dashboard endpoints | Unchanged this cycle. |
| Regime score, market phase, realized forward-returns | `app.engine.regime`, `app.engine.market_phase`, `app.engine.forward_testing` | per-page endpoints (dashboard/stocks/research) | `[TARGET, iter-2 building]` for the WARM TRIGGER only (the computation + `MarketPhaseCache` table + serving path — `market_phase_cached` — are unchanged, already restart-persistent). iter-2 moves the warm trigger for a newly-created snapshot's as-of from first-request-lazy to the ingest finalize hook (`_do_backfill`'s completion); byte-identical values either way. |
| Backend readiness / boot phase + preflight verdict | `app.engine.readiness.compute_readiness` / `compute_preflight` | `GET /api/health` | Already built (mcp-loop iter-28/iter-33). J-04 extends the SAME endpoint's evidence: persistent logfile (iter-2), honest crash/unreachable presentation, interrupted-job detection — no new computing module. |
| Job history & per-date exclusion reasons | data-manager job engine finalize (`app.engine.data_manager`, backfill/fetch/rebuild path) → `data_provider_runs` table | `GET /api/data` (persisted `runs` list, survives restart/reload) + `GET /api/data/jobs/{job_id}` (live in-session poll of the currently-running job) — same underlying `_run_detail()` shape, two read paths for two lifecycles, never a second computation | Base fields (status/message/dismissed/job_id) built pre-cycle; the iter-1 exclusion-reason breakdown is now built + evaluator-confirmed passing (tag removed). iter-2 adds `aggregates_refreshed` to the SAME `_run_detail()` JSON blob — see the Backfill run-summary contract row below. |
| Coverage payload (universe counts, per-symbol coverage, gaps, capacity) | `app.engine.data_manager` — the ingest finalize hook (`_do_backfill`/`_run_job` completion) computes + persists via the EXISTING `_compute_coverage_uncached` derivation (no second derivation); the background warm-up thread (`app.engine.warmup._run_warmup`) is a safety-net second writer of the SAME row for a not-yet-ingested-once DB, never a second computation | `GET /api/data` (reads the persisted `coverage_snapshot` row for the resolved `(asof_key, dataset_version)` key) | `[TARGET, iter-2 building]` — new `coverage_snapshot` table (`id, asof_key: str, dataset_version: str, payload_json: str, computed_at: datetime`, unique on `(asof_key, dataset_version)`, following the `MarketPhaseCache`/`EventStudyCache`/`MembershipTimelineCache` convention). Replaces the request-path call to `compute_coverage` (previously computed per-request via `_compute_coverage_uncached`'s whole-table prefill — the documented OOM source, only in-process cached, lost on restart). A missing row serves an honest "not yet computed" partial state — never a live whole-table compute on this serving path. |
| Backfill run-summary contract (`dates_total`, per-date exclusion breakdown, `aggregates_refreshed`) | data-manager job engine, backfill finalize (`_do_backfill` in `app.engine.data_manager`) | `GET /api/data` (persisted `runs` list) + `GET /api/data/jobs/{job_id}` (live poll) | Exact fields (present for `backfill`/`both`/`rebuild` kinds only, null for `fetch`/`expand` — matching the existing `dates_total` nullability): `dates_total: int>=0` (trading days in the requested range), `calendar_days: int>=0`, `non_trading_days: int>=0`, `already_snapshotted: int>=0`, `error_other: int>=0`, `snapshots_created: int>=0`. Invariants: `non_trading_days + dates_total = calendar_days`; `snapshots_created + already_snapshotted + error_other = dates_total`. Built + evaluator-confirmed passing (iter-1) — tag removed. **`[TARGET, iter-2 building]` — new field:** `aggregates_refreshed: list[str]` (subset of `["latest_snapshot", "coverage", "membership_timeline", "market_phase", "research_hot_keys"]`, `null` for kinds it doesn't apply to), gated on "actually computed" the same way `calendar_days` is (empty/null on an interrupted/not-yet-finalized row — never fabricated; AG-3). Reads the SAME `_run_detail()`/`JobProgress` mechanism — no new DB column, no second record. |
| Membership timeline / research hot-key caches | `membership_timeline_cache`, `event_study_cache` (existing tables) | `/data`, `/sectors`, `/themes`, `/research/*` first loads | `[TARGET, iter-2 building]` — tables and serving reads already exist (already restart-persistent, unlike coverage). iter-2 ADDS an ingest-finalize warm trigger (`_do_backfill`'s completion, reusing `membership_timeline_cached`/`event_study_cached` exactly as the boot warm-up thread already calls them) alongside the existing boot-time warm trigger — same tables, same serving path, byte-identical values; the boot trigger is retained (not removed) as the safety net for a not-yet-ingested-once DB. |
| Page performance budgets (never-regress measurements) | N/A — a measurement artifact, not a served runtime value | `reports/perf-budgets.md` | Existing table (mcp-loop legacy) carries forward. iter-2 appends a preliminary measured section for cold `GET /api/data` post-fix (evidence for J-05's own acceptance step); J-06 folds this into the FORMAL cross-page budget table alongside the ≤5s boot budget and every other page — no second budgets file either way. |

No shared value in this contract may gain a second computing module or a second serving endpoint;
an iteration that needs one of the `[TARGET]` values reads/writes through the module + endpoint
named above, and removes its `[TARGET]` tag here once built (and confirmed passing by the
goal-evaluator — the decomposer does not self-certify a value as built until the evaluator scores
the journey that depends on it).
