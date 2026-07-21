# App Blueprint — ops-hardening

<!--
Coherence contract for the ops-hardening goal session. Drafted at baseline (iter-0) from
docs/goal.md's Product Shape + Must-have journeys, cross-checked against the actual codebase
(apps/frontend/components/sidebar.tsx, apps/backend/app/engine/*, apps/backend/app/models.py).
Auto-approved per default run-goal.sh behavior; re-review any time with --require-blueprint-approval.

This session is layered on top of the prior `mcp-loop` goal session (GOAL_ACHIEVED 2026-07-16, 25/25
journeys, archived at docs/archive/goal-mcp-loop.md). Product Shape is explicit: this cycle is additive
ops/performance/correctness work, not a rewrite — the IA below is the SAME app shell, extended only where
J-01/J-03/J-04/J-05/J-06 require it.

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

iter-4 update: closes two pre-existing, out-of-scope trust-surface defects surfaced by iter-3's
first-ever real fetch/heavy-job browser exercise of J-05 — B3 (an ordinary fetch was flipping the
app-wide badge to the crash-identical false "Backend unavailable"/NO-GO state) and F1 (the
job-progress heartbeat froze during the aggregate-refresh finalize phase, showing a false "possibly
stalled" on a healthy job). The Backend readiness / boot phase + preflight verdict row's Notes
column now documents a fourth `state` value (`awaiting_snapshot`) and a new sibling `detail` field,
both served by the SAME `compute_readiness`/`compute_preflight` module and the SAME
`GET /api/health` endpoint — no second producer. F1's fix (added `tick()` calls in
`_refresh_ingest_aggregates`'s finalize loop) is a correctness fix to the existing Job history
row's already-covered `JobProgress` heartbeat mechanism, not a new contract value — no row change.
No Information Architecture change this iteration (no new page/nav; the fourth badge state renders
on the existing global badge, and the heartbeat fix surfaces on the existing `/data` job card).

iter-5 update: targets J-06 (the session's last failing Must-have journey and measurement
capstone) — a cross-cutting, first-ever whole-product page-load pass across all 11 nav-listed
pages named in goal.md's J-06 step 1, plus the ≤5s boot-to-health budget from Success Criteria. No
new page, route, or nav entry (every measured page already has its home in the Information
Architecture below) and no new Data Contract value is anticipated — this iteration reads/measures
rows already registered below. One contingent exception: IF the on-load code audit or a live
measurement finds a genuine unbounded-scan/recompute violation — candidates identified by codebase
inspection ahead of this iteration, not yet confirmed live: `/api/backtest`'s `evidence_by_horizon`
calls `compute_forward_aggregates` once per configured horizon (5, per `config.yaml`'s
`walk_forward.horizons`), each an unfiltered-by-default `ForwardReturn` table read; `/api/runs`
issues one `ScannerResult` count query per stored run (~180+ runs, an N+1 pattern) — any fix amends
that value's EXISTING row below (computing module + serving endpoint unchanged); it does not
create a second producer or a second budgets file. The "Page performance budgets" row's
forward-looking note (added iter-2) about J-06 folding in the boot budget + every page is what THIS
iteration executes.

iter-6 update: closes J-06's remaining gap — a real-browser-measured, non-computational latency
violation on `/api/indexes?full=true` (Dashboard) caused by Chrome's 6-connections-per-origin cap
queuing behind the page's 10-13 near-simultaneous same-origin on-load calls (iter-5's finding: curl
0.79-0.95s in-budget, real browser 1.68-2.19s over-budget), plus the identical root cause on
`GET /api/data/availability` (2.9-3.0s browser, previously unbudgeted). The fix is FRONTEND-ONLY
(fetch scheduling/staggering on the existing Dashboard cards and the Data Manager's availability
heatmap) — no new backend endpoint, no second computing module or serving path for any
already-registered Data Contract value (dashboard snapshot, market phase, sectors, themes, indexes,
regime history, and coverage/availability all keep their EXISTING single producer and single
endpoint; only request timing/ordering changes). `GET /api/data/availability` gains its first
committed budget row in the SAME `reports/perf-budgets.md` artifact — no second budgets file. Also
fixes a stale J-01 golden-script regression proxy (test infrastructure, not product code) per
iter-5's lesson. No Information Architecture change this iteration (no new page/nav/route; both
touched surfaces — `/`, `/data` — already have their homes below).

iter-7 update: closes J-06's LAST remaining gap — `/evidence`'s one-time cold-miss (~73s on the
accumulated live dev DB per iter-6 audit B1) because the ingest finalize hook warmed the
`event_study_cache`'s default research hot key but never the per-claim `drawdown_expectations` view
slot the SAME table reserves for the Evidence page. This iteration extends the EXISTING ingest
finalize hook (`_refresh_ingest_aggregates`, `app.engine.data_manager`) to also warm every ledger
claim's `drawdown_expectations` key via the EXISTING `compute_drawdown_expectations_cached`
(`app.engine.forward_testing`, already the sole call site `GET /api/evidence` uses) — no new
computing module, no new table (reuses `event_study_cache`'s reserved `drawdown_expectations` view
slot), no new endpoint. This is a value already displayed on `/evidence`; only its warm TIMING moves
from lazy-first-request to ingest-time, mirroring the existing `research_hot_keys` precedent (iter-2)
and the `forward_aggregates` precedent (iter-5) in the SAME function. The `aggregates_refreshed`
field's already-evolving enumerated value set (Data Contract row below) gains one more legal member,
`"drawdown_expectations"` — no new field, no second record. No Information Architecture change this
iteration (no new page/nav/route; `/evidence` already has its home below, under no dedicated journey
row previously — it is covered by the existing "Membership timeline / research hot-key caches" row,
whose "Served by" list now includes it).

iter-8 update (REGRESSION recovery): iter-7's evaluator verified J-05 (a required-still-passing journey, `passing` since iter-6) broke on its literal heavy-ingest health-responsiveness acceptance step -- a real back-to-back heavy ingest hit the enforced `memory_cap_mb=6144` `ulimit -v` ceiling, hanging `GET /api/health` for 7+ minutes (critical AG-8 finding). This iteration hardens the SAME `_refresh_ingest_aggregates` finalize hook's per-item warm loops (coverage/market-phase/forward-aggregates/drawdown-expectations) to catch `MemoryError` distinctly from their existing generic per-item exception handling -- stop attempting further items in that ONE loop and force `gc.collect()` on the first MemoryError, instead of continuing to hammer further large allocations under pressure. No new field, no new computing module, no new endpoint, no change to any warmed value's correctness (byte-identity untouched) -- a failure-handling/memory-profile change only, to the ALREADY-registered Job history row below. `app/api/health.py` / `app/engine/readiness.py` / `main.py` boot sequence are explicitly NOT touched (their existing exception handling already degrades honestly once the process has allocation headroom -- this iteration restores that headroom at the source). No Information Architecture change (no new page/nav/route).

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
| J-05 — Aggregates precomputed at ingest | `/data` (coverage payload + run-detail `aggregates_refreshed`), `/scanner-runs` (stored leaderboard), `/` (market phase card), `/research/*` (hot-key labs), `/evidence` (per-claim drawdown expectations, iter-7) — cross-cutting, no single new page | Data Manager / Scanner Runs / Dashboard / Research / Evidence |
| J-06 — Pages load only what they need | cross-cutting measurement; canonical artifact is `reports/perf-budgets.md` (not a UI page) | (all pages, measured) |

## Data Contract

Every value below must read the same everywhere. `[TARGET]` marks a value whose canonical
module + endpoint are DECIDED by `docs/goal.md`'s Product Shape but not yet fully implemented —
the iteration that builds it must use exactly that module/endpoint, never a second one.

| Value / entity | Computed by (single module/function) | Served by (single endpoint) | Notes |
|---|---|---|---|
| Evidence status / certified-claim (signal, as-of) | `app.engine.referee` + `app.engine.ledger` | `GET /api/evidence` | Unchanged this cycle (mcp-loop legacy). |
| Leadership / Entry Quality / Risk scores | `app.engine.scoring` | `/api/stocks`, `/api/sectors`, `/api/themes`, dashboard endpoints | Unchanged this cycle. |
| Regime score, market phase, realized forward-returns | `app.engine.regime`, `app.engine.market_phase`, `app.engine.forward_testing` | per-page endpoints (dashboard/stocks/research) | Built + evaluator-confirmed (iter-2): the WARM TRIGGER for a newly-created snapshot's as-of moved from first-request-lazy to the ingest finalize hook (`_run_job`'s completion); the computation + `MarketPhaseCache` table + serving path (`market_phase_cached`) are unchanged, already restart-persistent — byte-identical values either way (evaluator-confirmed via TC-04). Unaffected by iter-3 (fetch/expand never create new snapshot dates, so this trigger's own scope is unchanged). iter-5: `/api/backtest`'s `compute_forward_aggregates` read of `forward_returns` was confirmed a genuine violation (34.766s live) and fixed with a new ingest-time-warmed `ForwardAggregateCache` wrapper (`forward_aggregates_cached`) around the SAME unchanged `compute_forward_aggregates` — sole producer untouched, both existing call sites (`/api/backtest`, the MCP `query_backtest` tool) switched to the wrapper, byte-identical verified. iter-6 (measurement/scheduling only): this row's own endpoints (`/api/dashboard`, `/api/market-phase`, `/api/indexes`, `/api/regime-history`) are being re-timed under REAL BROWSER conditions as part of J-06's close-out; the fix is frontend fetch-scheduling only — no change to this row's module/endpoint/values. Unaffected by iter-7 (`/evidence`'s `drawdown_expectations` is a distinct value — see the Membership timeline / research hot-key row below). |
| Backend readiness / boot phase + preflight verdict | `app.engine.readiness.compute_readiness` / `compute_preflight` | `GET /api/health` | Already built (mcp-loop iter-28/iter-33). J-04 extends the SAME endpoint's evidence: persistent logfile (iter-2), honest crash/unreachable presentation, interrupted-job detection — no new computing module. iter-3 re-exercises this endpoint live (polled throughout a real heavy ingest job) as part of J-05's own step-4 measurement — no code change to this row's module/endpoint. iter-4 widened `compute_readiness`'s `state` enum with a fourth value, `awaiting_snapshot` (a servable last run exists but new benchmark data has landed past it, snapshot pending — distinct from `unavailable`'s true no-servable-snapshot case) plus a new sibling field `detail: string\|null` (populated only for the new state) on the SAME payload; narrows the servability comparison from the whole-table `latest_data_date` max to the benchmark symbol's (`cfg.etfs.index[0]`) own latest bar. Same computing module (`compute_readiness`/`compute_preflight`), same endpoint (`GET /api/health`) — no second producer. Closed defect B3 (an ordinary fetch was flipping the badge to the crash-identical false "Backend unavailable"/NO-GO) — evaluator-confirmed passing (iter-4). iter-5 (J-06): this endpoint's pre-existing `func.max(DailyPrice.date)`/`func.count(distinct(DailyPrice.symbol))` read (`health.py:44-45`, unrelated to the readiness computation itself) was re-measured against its existing ≤0.1s budget only — no code change ("Do not redo" — B3/F1 settled). iter-6: re-confirms the existing ≤5s boot-to-health budget only (TC-11); no code change to this row. Unaffected by iter-7 (this iteration's diff does not touch `readiness.py`/`main.py`'s boot sequence). iter-8 (J-05 regression recovery): also unaffected — the fix lives entirely in `_refresh_ingest_aggregates`'s per-item warm-loop error handling (Job history row above); this endpoint's own exception handling is unchanged, re-verified live throughout iter-8's back-to-back heavy-ingest health-poll test. |
| Job history & per-date exclusion reasons | data-manager job engine finalize (`app.engine.data_manager`, backfill/fetch/rebuild path) → `data_provider_runs` table | `GET /api/data` (persisted `runs` list, survives restart/reload) + `GET /api/data/jobs/{job_id}` (live in-session poll of the currently-running job) — same underlying `_run_detail()` shape, two read paths for two lifecycles, never a second computation | Base fields (status/message/dismissed/job_id) built pre-cycle; the iter-1 exclusion-reason breakdown is now built + evaluator-confirmed passing (tag removed). iter-2 added `aggregates_refreshed` to the SAME `_run_detail()` JSON blob — see the Backfill run-summary contract row below. Unaffected by iter-3. iter-4 fixed the existing heartbeat mechanism's correctness (F1: `_refresh_ingest_aggregates`'s finalize loop now ticks `JobProgress.last_progress_at`) — no new field, no second computation. Unaffected by iter-5 or iter-6 (iter-6 fixes a golden-script test artifact for J-01's own run-history read of this row, not the row itself). iter-7 extends the SAME finalize function with one more non-fatal warm step (drawdown expectations) — no new field, no second computation; see the Backfill run-summary contract row below for the `aggregates_refreshed` enumeration update. iter-8 (REGRESSION recovery, J-05): hardens the SAME per-item warm loops (coverage/market-phase/forward-aggregates/drawdown) to catch `MemoryError` distinctly from the existing generic per-item exception handling — on the first MemoryError in a loop, stop attempting further items in THAT loop and force `gc.collect()`, rather than continuing to hammer further allocations under memory pressure; no new field, no second computation, failure-handling change only, closing the critical AG-8 finding iter-7 introduced. |
| Coverage payload (universe counts, per-symbol coverage, gaps, capacity) | `app.engine.data_manager` — the ingest finalize hook (`_run_job` completion, for every kind whose bars/membership manifest actually changed — see iter-3 note below) computes + persists via the EXISTING `_compute_coverage_uncached` derivation (no second derivation); the background warm-up thread (`app.engine.warmup._run_warmup`) is a safety-net second writer of the SAME row for a not-yet-ingested-once DB, never a second computation | `GET /api/data` (reads the persisted `coverage_snapshot` row for the resolved `(asof_key, dataset_version)` key) | Table + `backfill`/`both`/`rebuild` finalize wiring built + evaluator-confirmed (iter-2): `coverage_snapshot(id, asof_key: str, dataset_version: str, payload_json: str, computed_at: datetime)`, unique on `(asof_key, dataset_version)`, following the `MarketPhaseCache`/`EventStudyCache`/`MembershipTimelineCache` convention; replaces the request-path call to `compute_coverage`. A missing row serves an honest "not yet computed" partial state — never a live whole-table compute on the DEFAULT (`as_of=None`) serving path. One narrow, reviewed exception: an EXPLICIT historical `?as_of=` that predates this table's rollout self-heals via one bounded, gated, one-time-per-date live compute (`coverage_from_storage`, guarded by `_scanner_run_exists`) — never fired on the default path (coherence advisory, iter-2, wording tightened here iter-3). Fetch/expand finalize trigger widening (audit B1) + stale-`dataset_version` row reclaim (audit B2) built + evaluator-confirmed (iter-3) — tags removed; unaffected by iter-4. iter-5 (J-06): `/data`'s coverage TTI/latency was re-measured (existing ≤3s/≤1.5s budgets held); no code change. iter-6: `GET /api/data/availability` (the coverage-heatmap-feeding sibling endpoint, unbudgeted before now) is being fixed for real-browser connection queuing via a frontend-only scheduling change and gains its first committed budget in `reports/perf-budgets.md` — no change to this row's module/endpoint. Unaffected by iter-7. |
| Backfill run-summary contract (`dates_total`, per-date exclusion breakdown, `aggregates_refreshed`) | data-manager job engine, backfill finalize (`_do_backfill` in `app.engine.data_manager`) | `GET /api/data` (persisted `runs` list) + `GET /api/data/jobs/{job_id}` (live poll) | Exact fields (present for `backfill`/`both`/`rebuild` kinds only, null for `fetch`/`expand` — matching the existing `dates_total` nullability): `dates_total: int>=0` (trading days in the requested range), `calendar_days: int>=0`, `non_trading_days: int>=0`, `already_snapshotted: int>=0`, `error_other: int>=0`, `snapshots_created: int>=0`. Invariants: `non_trading_days + dates_total = calendar_days`; `snapshots_created + already_snapshotted + error_other = dates_total`. Built + evaluator-confirmed passing (iter-1) — tag removed. `aggregates_refreshed: list[str]` (subset of `["latest_snapshot", "coverage", "membership_timeline", "market_phase", "research_hot_keys", "forward_aggregates"]` as of iter-5, gains `"drawdown_expectations"` as of iter-7 — see note below; `null` for kinds it doesn't apply to), gated on "actually computed" the same way `calendar_days` is (empty/null on an interrupted/not-yet-finalized row — never fabricated; AG-3) — built + evaluator-confirmed passing (iter-2), tag removed. Reads the SAME `_run_detail()`/`JobProgress` mechanism — no new DB column, no second record. iter-3's fetch/expand coverage-freshness fix (see Coverage payload row above) does NOT change this field's nullability contract: `aggregates_refreshed` stays `null` for `fetch`/`expand` kinds. iter-5 added `"forward_aggregates"` to the SAME existing list via the SAME finalize hook (no new field, no second record). iter-6 (test infra only): fixes J-01's golden-script step 6 to read this row's data (the submitted run's own `/data` history entry) instead of a stale, unrelated `/scanner-runs` proxy — no change to the field/contract itself. iter-7 adds `"drawdown_expectations"` to the SAME enumerated list via the SAME finalize hook (`_refresh_ingest_aggregates`), warming every evidence-ledger claim's `drawdown_expectations` key so `/evidence`'s first view after an ingest never pays the lazy cold-miss — no new field, no second record, gated on "actually warmed" the same way every other member of this list already is. |
| Membership timeline / research hot-key caches | `membership_timeline_cache`, `event_study_cache` (existing tables) | `/data`, `/sectors`, `/themes`, `/research/*`, `/evidence` (iter-7) first loads | Built + evaluator-confirmed (iter-2): the ingest-finalize warm trigger (`_run_job` completion for `backfill`/`both`/`rebuild`, reusing `membership_timeline_cached`/`event_study_cached` exactly as the boot warm-up thread already calls them) runs alongside the existing boot-time warm trigger — same tables, same serving path, byte-identical values; the boot trigger is retained (not removed) as the safety net for a not-yet-ingested-once DB. Unaffected by iter-3 (fetch/expand never create new snapshot dates, so this trigger's own scope is unchanged). Unaffected by iter-4. iter-5 (J-06): the `/research/event-study` lab's TTI/latency was measured for the first time against this row's existing warm-cache path — held budget, no code change. Unaffected by iter-6. iter-7 extends the SAME `_refresh_ingest_aggregates` finalize hook to ALSO warm `event_study_cache`'s reserved `drawdown_expectations` view slot for every claim in the evidence ledger, via the EXISTING `compute_drawdown_expectations_cached` (`app.engine.forward_testing`) — the SAME function `GET /api/evidence` already calls lazily; only the warm TIMING moves earlier (ingest finalize instead of first request), closing the ~73s first-view cold-miss (iter-6 audit B1) on the grown live basis. No new table, no new computing module, no new endpoint — `event_study_cache` and `compute_drawdown_expectations_cached` are both pre-existing and unchanged. |
| Page performance budgets (never-regress measurements) | N/A — a measurement artifact, not a served runtime value | `reports/perf-budgets.md` | Existing table (mcp-loop legacy) carries forward. iter-2 appended a preliminary measured section for cold `GET /api/data` post-fix (evidence for J-05's own acceptance step) plus the launch-script enforcement measurement. iter-3 appends one more dated section — J-05's step-4 live measurement (`GET /api/health` responsiveness + `VmPeak`/`VmSize` ceiling during a real heavy ingest job). iter-5 folded in the ≤5s boot-to-health budget plus TTI/latency rows for all 11 nav-listed pages, and confirmed (curl-measured) `/api/backtest`'s post-fix 0.138s; but iter-5's own CURL-based methodology under-reported `/api/indexes?full=true`'s real-browser latency (1.68-2.19s browser vs 0.79-0.95s curl) — the iter-5 lesson on record. iter-6 (this iteration): fixes that real-browser violation via a frontend-only fetch-scheduling change, re-measures with REAL BROWSER timing (not curl) for the affected endpoints, and commits `GET /api/data/availability`'s first budget row in this SAME file (previously unbudgeted, flagged iter-5) — still the one canonical budgets artifact, no second file. iter-6 also documented a measurement-contamination episode: a concurrent 84-minute pytest run inflated `/evidence`'s one-time cold-miss reading to 555.97s; the corrected idle reading is 73.3s, still an in-budget one-time cold miss per Item I's own clause, but flagged as the last J-06 residual to warm away. iter-7 closes that residual (ingest-time `drawdown_expectations` warm, see rows above) and re-measures `/evidence`'s FIRST VIEW post-warm on an idle host, plus reconfirms all 11 pages' budgets in the SAME file — no second budgets artifact, no loosened number. If a fix ever proves insufficient without a second endpoint, the plan is to stop and re-decompose, not to expand this row's producer/endpoint set. iter-8 extends Item L with a fresh back-to-back heavy-ingest VmPeak + `GET /api/health`-responsiveness measurement on the REGRESSION-recovery build — same file, no second artifact. |

No shared value in this contract may gain a second computing module or a second serving endpoint;
an iteration that needs one of the `[TARGET]` values reads/writes through the module + endpoint
named above, and removes its `[TARGET]` tag here once built (and confirmed passing by the
goal-evaluator — the decomposer does not self-certify a value as built until the evaluator scores
the journey that depends on it).
