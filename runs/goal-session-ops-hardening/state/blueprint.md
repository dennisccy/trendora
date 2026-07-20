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

iter-3 update: closes audit findings B1 (a `fetch`/`expand` that changes the bars manifest was not
refreshing `coverage_snapshot`, so the DEFAULT `/data` view could silently serve the honest-looking
but FALSE all-zero sentinel for a fully-ingested DB until an unrelated restart/backfill/rebuild) and
B2 (stale-`dataset_version` rows were never reclaimed) — both against the Coverage payload row,
retagged `[TARGET, iter-3 building]` below. Removes the `[TARGET, iter-2 building]` tags from the
`aggregates_refreshed` field, the market-phase warm-trigger row, and the membership-timeline/
research-hot-key row — all evaluator-confirmed built in iter-2 and unaffected by the iter-3 fix.
Also applies the iter-2 coherence auditor's advisory: the Coverage payload row's Notes column now
names the explicit-historical-`as_of` self-heal exception instead of an unqualified "never a live
compute." No Information Architecture change this iteration (no new page/nav; iter-3 is a backend
correctness fix plus one live measurement, both surfaced through the existing `/data` home).

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
| Regime score, market phase, realized forward-returns | `app.engine.regime`, `app.engine.market_phase`, `app.engine.forward_testing` | per-page endpoints (dashboard/stocks/research) | Built + evaluator-confirmed (iter-2): the WARM TRIGGER for a newly-created snapshot's as-of moved from first-request-lazy to the ingest finalize hook (`_run_job`'s completion); the computation + `MarketPhaseCache` table + serving path (`market_phase_cached`) are unchanged, already restart-persistent — byte-identical values either way (evaluator-confirmed via TC-04). Unaffected by iter-3 (fetch/expand never create new snapshot dates, so this trigger's own scope is unchanged). |
| Backend readiness / boot phase + preflight verdict | `app.engine.readiness.compute_readiness` / `compute_preflight` | `GET /api/health` | Already built (mcp-loop iter-28/iter-33). J-04 extends the SAME endpoint's evidence: persistent logfile (iter-2), honest crash/unreachable presentation, interrupted-job detection — no new computing module. iter-3 re-exercises this endpoint live (polled throughout a real heavy ingest job) as part of J-05's own step-4 measurement — no code change to this row's module/endpoint. |
| Job history & per-date exclusion reasons | data-manager job engine finalize (`app.engine.data_manager`, backfill/fetch/rebuild path) → `data_provider_runs` table | `GET /api/data` (persisted `runs` list, survives restart/reload) + `GET /api/data/jobs/{job_id}` (live in-session poll of the currently-running job) — same underlying `_run_detail()` shape, two read paths for two lifecycles, never a second computation | Base fields (status/message/dismissed/job_id) built pre-cycle; the iter-1 exclusion-reason breakdown is now built + evaluator-confirmed passing (tag removed). iter-2 added `aggregates_refreshed` to the SAME `_run_detail()` JSON blob — see the Backfill run-summary contract row below. Unaffected by iter-3. |
| Coverage payload (universe counts, per-symbol coverage, gaps, capacity) | `app.engine.data_manager` — the ingest finalize hook (`_run_job` completion, for every kind whose bars/membership manifest actually changed — see iter-3 note below) computes + persists via the EXISTING `_compute_coverage_uncached` derivation (no second derivation); the background warm-up thread (`app.engine.warmup._run_warmup`) is a safety-net second writer of the SAME row for a not-yet-ingested-once DB, never a second computation | `GET /api/data` (reads the persisted `coverage_snapshot` row for the resolved `(asof_key, dataset_version)` key) | Table + `backfill`/`both`/`rebuild` finalize wiring built + evaluator-confirmed (iter-2): `coverage_snapshot(id, asof_key: str, dataset_version: str, payload_json: str, computed_at: datetime)`, unique on `(asof_key, dataset_version)`, following the `MarketPhaseCache`/`EventStudyCache`/`MembershipTimelineCache` convention; replaces the request-path call to `compute_coverage`. A missing row serves an honest "not yet computed" partial state — never a live whole-table compute on the DEFAULT (`as_of=None`) serving path. One narrow, reviewed exception: an EXPLICIT historical `?as_of=` that predates this table's rollout self-heals via one bounded, gated, one-time-per-date live compute (`coverage_from_storage`, guarded by `_scanner_run_exists`) — never fired on the default path (coherence advisory, iter-2, wording tightened here iter-3). **`[TARGET, iter-3 building]`** — the finalize trigger widens to `fetch`/`expand` kinds too, gated to skip (zero extra compute, zero extra write) when `_membership_dataset_version` is unchanged from the current-stamp row (a zero-work offline fetch pays nothing) — closes audit finding B1 (a fetch that landed bars was serving the stale/false-zero sentinel on the default `/data` view until an unrelated restart or backfill/rebuild). iter-3 also reclaims stale-`dataset_version` rows left behind by a superseded stamp (audit finding B2) via one bounded delete, not a per-row scan. |
| Backfill run-summary contract (`dates_total`, per-date exclusion breakdown, `aggregates_refreshed`) | data-manager job engine, backfill finalize (`_do_backfill` in `app.engine.data_manager`) | `GET /api/data` (persisted `runs` list) + `GET /api/data/jobs/{job_id}` (live poll) | Exact fields (present for `backfill`/`both`/`rebuild` kinds only, null for `fetch`/`expand` — matching the existing `dates_total` nullability): `dates_total: int>=0` (trading days in the requested range), `calendar_days: int>=0`, `non_trading_days: int>=0`, `already_snapshotted: int>=0`, `error_other: int>=0`, `snapshots_created: int>=0`. Invariants: `non_trading_days + dates_total = calendar_days`; `snapshots_created + already_snapshotted + error_other = dates_total`. Built + evaluator-confirmed passing (iter-1) — tag removed. `aggregates_refreshed: list[str]` (subset of `["latest_snapshot", "coverage", "membership_timeline", "market_phase", "research_hot_keys"]`, `null` for kinds it doesn't apply to), gated on "actually computed" the same way `calendar_days` is (empty/null on an interrupted/not-yet-finalized row — never fabricated; AG-3) — built + evaluator-confirmed passing (iter-2), tag removed. Reads the SAME `_run_detail()`/`JobProgress` mechanism — no new DB column, no second record. iter-3's fetch/expand coverage-freshness fix (see Coverage payload row above) does NOT change this field's nullability contract: `aggregates_refreshed` stays `null` for `fetch`/`expand` kinds — the ingest-time coverage refresh those kinds now also trigger is silent from this field's transparency perspective. |
| Membership timeline / research hot-key caches | `membership_timeline_cache`, `event_study_cache` (existing tables) | `/data`, `/sectors`, `/themes`, `/research/*` first loads | Built + evaluator-confirmed (iter-2): the ingest-finalize warm trigger (`_run_job` completion for `backfill`/`both`/`rebuild`, reusing `membership_timeline_cached`/`event_study_cached` exactly as the boot warm-up thread already calls them) runs alongside the existing boot-time warm trigger — same tables, same serving path, byte-identical values; the boot trigger is retained (not removed) as the safety net for a not-yet-ingested-once DB. Unaffected by iter-3 (fetch/expand never create new snapshot dates, so this trigger's own scope is unchanged). |
| Page performance budgets (never-regress measurements) | N/A — a measurement artifact, not a served runtime value | `reports/perf-budgets.md` | Existing table (mcp-loop legacy) carries forward. iter-2 appended a preliminary measured section for cold `GET /api/data` post-fix (evidence for J-05's own acceptance step) plus the launch-script enforcement measurement. iter-3 appends one more dated section — J-05's step-4 live measurement (`GET /api/health` responsiveness + `VmPeak`/`VmSize` ceiling during a real heavy ingest job). J-06 folds all of these into the FORMAL cross-page budget table alongside the ≤5s boot budget and every other page — no second budgets file either way. |

No shared value in this contract may gain a second computing module or a second serving endpoint;
an iteration that needs one of the `[TARGET]` values reads/writes through the module + endpoint
named above, and removes its `[TARGET]` tag here once built (and confirmed passing by the
goal-evaluator — the decomposer does not self-certify a value as built until the evaluator scores
the journey that depends on it).
