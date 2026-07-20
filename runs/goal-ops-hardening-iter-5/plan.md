# goal-ops-hardening-iter-5 Execution Plan

J-06 capstone: "Pages load only what they need." This is a **measurement + code-audit iteration**
with two explicitly CONTINGENT fix branches (backend cache, frontend loading state) — build the
contingent piece ONLY if live numbers or the audit actually show a violation. Required-still-passing:
J-01, J-03, J-04, J-05 (replay only, zero code changes expected there — see Out of Scope).

## What to Build

- Extend `scripts/measure-perf.sh` (already exists, iter-24-authored — append to it, do not fork a
  second script) to additionally capture: (a) backend cold-boot wall time, process start → first
  `GET /api/health` HTTP 200, on the warm committed-seed DB; (b) the 7 not-yet-measured
  endpoints/pages: `/` Dashboard (`/api/dashboard` + `/api/market-phase` + `/api/sectors` +
  `/api/themes`, likely also `/api/indexes?full=true` + `/api/regime-history?full=true` for the
  cross-view chart — confirm the exact on-load call set by reading `apps/frontend/app/page.tsx`),
  `/sectors` (`GET /api/sectors`), `/themes` (`GET /api/themes`), `/scanner-runs` (`GET /api/runs`),
  `/backtest` (`GET /api/backtest`, all 5 configured horizons), `/watchlist` (`GET /api/watchlist`
  incl. its `xray` field), and `/research/event-study` (`GET /research/event-study`).
- Run the full 11-page + boot pass against `scripts/start-backend.sh` / `scripts/start-frontend.sh`
  (prod mode, never `dev.sh`); append ONE new dated section to `reports/perf-budgets.md` (the SAME
  file every prior perf item used — no second budgets artifact anywhere in the repo).
- Code-level audit (dev-handoff deliverable, TC-13): for each of the 11 pages' backing endpoint(s),
  state explicitly whether it reads a persisted snapshot/cache/indexed-bounded query, or performs a
  genuine unbounded `daily_prices` scan / uncached inventory-aggregate recompute. Explicitly re-trace
  the two named candidates below.
- **CONTINGENT backend fix** (only if the audit or a live measurement finds a genuine violation):
  persist the value via an ingest-time warm cache following the EXISTING `CoverageSnapshot` /
  `EventStudyCache` / `MarketPhaseCache` convention (`app/models.py` — STANDALONE `create_all`-managed
  table, keyed by identity + `dataset_version` stamp) — wired through the value's EXISTING computing
  module and EXISTING serving endpoint (never a second producer). Re-measure to confirm the fix clears
  budget. **If a violation doesn't fit this mechanical pattern, STOP and hand back to a fresh
  decomposer iteration — do not expand this iteration's scope** (spec's own instruction).
- **CONTINGENT frontend fix** (only if a page's measured latency exceeds its committed budget): add
  the minimal honest loading indicator to that page, reusing the SAME per-family pattern already
  established (see Visual Requirements) — never a new visual language, never nav/route changes.
- Regression replay: J-01, J-03, J-04, J-05 must stay green (deterministic golden script + LLM
  fallback) with zero regression attributable to this iteration.
- Dev handoff at `docs/handoffs/goal-ops-hardening-iter-5-dev.md`: the TC-13 audit, a pointer to the
  exact `reports/perf-budgets.md` section this iteration added, and an explicit statement of whether
  any contingent fix was applied (and why, if not).

**Two named risk candidates (from the spec's own code inspection — confirmed by reading the code this
planning pass):**
1. `GET /api/backtest` (`apps/backend/app/api/backtest.py:68-71`) calls
   `compute_forward_aggregates(session, h, cfg, as_of=run.asof_date)` once per configured horizon (5
   horizons: 1/5/10/20/60 days). Each call (`forward_testing.py:813-818`) does
   `select(ForwardReturn).where(horizon==h).join(ScannerRun...).where(asof_date <= as_of).all()` —
   for the default (latest) as-of this is effectively the WHOLE horizon-partition of the
   `forward_returns` table (~1.5-1.7M rows / 5 horizons), materialized and looped in Python, **5
   times per request**. Highest-risk candidate — measure with extra attention.
2. `GET /api/runs` (`apps/backend/app/api/runs.py:33-36`) issues one `ScannerResult` count query
   PER stored run inside a Python `for run in run_rows` loop (~180+ runs) — a confirmed N+1 pattern.
   Each individual query is index-bound (`ScannerResult.run_id`), so likely lower-risk, but worth the
   latency check the spec calls for.
   Both `/api/dashboard`, `/api/sectors`, `/api/themes`, `/api/market-phase`, and `/api/watchlist`'s
   `xray` field were read this pass and are already snapshot-served / cached / bounded-window reads
   (iter-8 / J-72 / J-87 settled) — lower risk, but still must be measured for the first time (TC-2,
   TC-5, TC-6, TC-11).

## Agents Required

- **backend-data: yes** — extend `scripts/measure-perf.sh`; run the full measurement pass; write the
  TC-13 audit; apply the contingent minimal ingest-time-cache fix ONLY if a genuine violation is
  measured (most likely candidate: `compute_forward_aggregates`); add/update backend unit tests
  (byte-identity, zero-call invariant, honest-sentinel, cache-refresh-on-ingest if a fix lands).
- **frontend-ux: contingent yes** — ONLY if live measurement shows a specific page over its committed
  budget, add the minimal existing-pattern loading indicator to that page. If no page exceeds budget,
  no frontend code changes are needed this iteration (the browser-qa pass still exercises all 11 pages
  regardless — that's QA's job, not a code-change trigger by itself).

Frontend Present: yes

## Files to Create/Modify

- `scripts/measure-perf.sh` — extend with boot-to-health timing + the 7 new endpoint/page latency
  captures.
- `reports/perf-budgets.md` — append one new dated section (all new + re-measured numbers).
- `docs/handoffs/goal-ops-hardening-iter-5-dev.md` — dev handoff incl. TC-13 audit + contingent-fix
  statement.
- CONTINGENT, only if the backtest candidate (or another) proves a genuine violation:
  - `apps/backend/app/models.py` — new STANDALONE cache table mirroring `EventStudyCache` /
    `MarketPhaseCache`'s shape (keyed by horizon + as-of cutoff + `dataset_version`).
  - `apps/backend/app/engine/forward_testing.py` — `compute_forward_aggregates` becomes cache-first
    (stays the SOLE producer/computing module — no second computation path).
  - `apps/backend/app/engine/data_manager.py` — warm/refresh the new cache inside the EXISTING
    finalize hooks (`_refresh_ingest_aggregates` / `_do_backfill`), never a new ingest path.
  - `apps/backend/tests/test_forward_testing.py`, `test_data_manager.py` — byte-identity,
    zero-live-call-invariant (mirror `test_get_data_overview_serves_coverage_from_storage_zero_prefill_calls`),
    honest not-yet-computed sentinel, cache-refresh-on-every-relevant-ingest-kind tests.
  - Whichever page(s) actually measure over budget (most likely `apps/frontend/app/backtest/page.tsx`
    and/or `apps/frontend/app/scanner-runs/page.tsx`) — minimal loading-state addition only.

## UI Evolution (required if Frontend Present: yes)

- New user-facing capability: none by default (measurement + audit only). Contingent: an honest,
  visibly-distinct loading/progress indicator on any page whose live measurement exceeds its committed
  budget, in place of a blank/frozen frame, while the SAME already-existing data finishes loading.
- New information displayed: none in the product UI. `reports/perf-budgets.md` gains a new dated
  section (TTI + on-load latencies for the 7 newly-measured pages + the boot budget) — an engineering
  artifact, not a UI surface.
- New user actions: none.
- UI surface changes: none expected; contingent minimal skeleton/loading state on an over-budget page
  only.
- Navigation changes: none.

## Visual Requirements (required if Frontend Present: yes)

- Component patterns: this repo already has TWO established, page-family-specific loading idioms —
  reuse the matching one, never invent a third:
  1. Main data pages (`/stocks`, `/sectors`, `/themes`, `/scanner-runs`, `/backtest`, `/watchlist`,
     `/` dashboard) already use a `{ kind: "loading" }` state + a page-specific `<XSkeleton/>`
     component (e.g. `StocksSkeleton` in `apps/frontend/app/stocks/page.tsx`).
  2. Research labs (incl. `/research/event-study`, via `EventStudyLabPage` in
     `apps/frontend/app/research/_labs.tsx`) already route through `LabRouteShell`'s `warmingWhat`
     prop → `components/warming-state.tsx`.
  If a contingent fix is needed, extend the SAME idiom already on that exact page — do not port one
  family's pattern onto the other, and don't add a spinner/skeleton library that isn't already here.
- Layout: unchanged — no new pages, panels, or layout structure this iteration.
- Key visual effects: none new; match the existing skeleton/warming-state visual treatment already
  used on that same page.
- States to handle: loading (only via the existing idiom, only if contingently triggered). Every
  pre-existing empty/error treatment on each of the 11 pages is unchanged and must keep working
  exactly as today — this iteration must not regress any of them while measuring.

## Key Test Scenarios

- TC-1 (boot): `scripts/start-backend.sh` cold-start on the warm committed-seed DB → first
  `GET /api/health` HTTP 200 within 5 s, recorded in `reports/perf-budgets.md`.
- TC-2..TC-12: each of the 11 named pages loaded warm in prod mode — TTI + every on-load API latency
  measured and recorded, within its existing or newly-committed budget. Give `/backtest` (5-horizon
  `evidence_by_horizon`) and `/scanner-runs` (`/api/runs` N+1) extra attention per the risk candidates
  above.
- TC-13: dev handoff states, per page's backing endpoint(s), that it's persisted/cached/indexed-bounded
  — or names exactly which call site violates this and what fix was applied.
- TC-14: any page found over budget shows a visibly distinct loading/progress element — never blank or
  silently frozen.
- TC-15: every new/re-measured number lives ONLY in `reports/perf-budgets.md` — no second budgets
  artifact anywhere in the repo.
- TC-16: J-01/J-03/J-04/J-05 golden-script replay (+ LLM fallback on a miss) — each still passes, zero
  regression attributable to this iteration.
- TC-17/TC-18 (contingent, only if a fix lands): cached value byte-identical to the canonical live
  computation for the same as-of; a not-yet-warmed cache key serves the existing honest "not yet
  computed" sentinel (never fabricated, never a 500); the cache refreshes/invalidates on every ingest
  kind that changes its underlying data — verify BOTH the fetch-then-view AND backfill-then-view paths
  (iter-2 B1 lesson: a fingerprint-only invalidation must not serve a false all-zero sentinel on a
  fully-populated DB).
- TC-19: relevant backend test suite passes with zero new failures vs. the pre-iteration baseline.
- Cold/not-yet-ingested-once DB path: honest NA/"not yet computed" sentinel on any measured
  endpoint — never a 500, never a fabricated number.

## Out of Scope (restating the spec's own boundaries — do not drift)

- No changes to `app/engine/readiness.py`'s servability logic, `health-badge.tsx`'s state rendering,
  or `_refresh_ingest_aggregates`'s existing `tick()` calls — B3/F1 settled iter-4 ("Do not redo" in
  iteration-state.md); this iteration re-verifies them only via the J-04 replay.
- No retirement of `ensure_latest_snapshot` or the boot warm-up loop's cadence bootstrap — unchanged
  by design, dormant vs. the offline seed.
- No new pages, nav entries, or Information Architecture changes.
- No new Evidence Claims, proven-language, or referee/ledger changes (AG-1/AG-4/AG-6 still veto — J-01
  … J-06 carry no Evidence Claims per goal.md's own loop mechanics).
- No live network calls or paid data services (AG-9) — measurement runs against the committed offline
  seed only.
- If a measured violation's fix does not fit the mechanical "existing ingest-time cache, existing
  producer/endpoint" pattern (i.e. it would need a genuinely new architectural/schema decision): STOP,
  do not expand this iteration open-endedly — hand back to a fresh decomposer iteration instead.
- The `[NEW]` `demo.sh ops-hardening --session-live` walkthrough bullets (J-05 and J-06) stay deferred
  session-closeout showcase artifacts per `assumptions.md`'s iter-4/iter-5 entries — not part of this
  iteration's Definition of Done.

## Notes for downstream agents

- This is the FIRST iteration driving all 11 nav-listed pages as one measurement pass (structural
  depth trigger) — read the RAW `reports/phase-goal-ops-hardening-iter-5-ui-test-results.llm.md`
  directly, not the merged summary (`merge_ui_test_results.py` drops the `## Notes` section and
  mis-sums the header count — iter-3/iter-4 lesson, restated in the spec's own NOTES).
- Treat any new failure surfaced by this pass as a genuine latent defect on a shared surface, not
  flakiness (iter-3 lesson — the first realistic full-surface load pattern tends to expose exactly
  this).
- If J-06 passes this iteration, all 5 Must-have journeys are passing — the goal-evaluator should
  weigh GOAL_ACHIEVED next, factoring in the still-deferred `demo.sh --session-live` closure-gate item
  above.
