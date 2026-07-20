# Goal Iteration 5 — Whole-product page-load & boot-time performance measurement (J-06 capstone)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** ops-hardening
- **Iteration:** 5
- **Mode:** next
- **Depth:** full
- **Frontend Present:** yes
- **Target journeys:** J-06
- **Required-still-passing journeys:** J-01, J-03, J-04, J-05
- **Anti-goal reminders:**
  - **AG-1:** A score, ranking, or "edge" MUST NOT be presented as proven/confident unless it is backed by a
    **passing certified-claim entry** in the evidence ledger (out-of-sample, control-beating). Unbacked
    values MUST render a "not yet proven" state. *(critical)*
  - **AG-2 — Decision-quality only:** never present return promises, price targets, "buy/sell" signals, or alpha
    claims; never place or simulate orders. *(critical)*
  - **AG-3:** A journey passes ONLY if the **displayed numbers are correct** — they match the engine's computation
    for the same as-of date — not merely that the page renders. *(critical)*
  - **AG-4 — No overfit edges:** any pattern surfaced as "proven" must have survived the referee (sealed
    out-of-sample holdout + controls + multiple-testing correction), never in-sample fit alone. *(critical)*
  - **AG-5 — Preserve determinism and no-lookahead:** scoring uses bars ≤ as-of; forward returns use bars > as-of;
    never introduce lookahead anywhere. *(critical)*
  - **AG-6:** No iteration ships if its evidence-derived claims (if any) lack a passing referee verdict from the
    post-decompose gate. *(critical)*
  - **AG-7:** No hard-coded credentials, API keys, or tokens in source files. *(critical)*
  - **AG-8 — Resilience to data-shape and data-scale change:** widening the data basis (new nulls, broader pools, deeper history) must never crash an existing page or exhaust a service's memory — every
    existing consumer of a widened field is re-validated, the UI degrades gracefully (contained error
    boundary, honest "—"/NA placeholder, never a blank application-error page), and unbounded
    whole-table ORM loads are forbidden on the deep basis. *(critical)*
  - **AG-9 — Offline-deterministic ingest:** ingest jobs (fetch/backfill/rebuild) run only
    against the committed seed / local provider fixtures — no live external network calls or
    paid data services may be introduced without an explicit goal.md amendment. *(critical)*

## GOAL

Every nav-listed page in Trendora is measured to load only the data it needs — time-to-interactive and
on-load API latency committed to the single `reports/perf-budgets.md` file for all 11 pages named in J-06
plus a ≤5-second cold-boot floor — and any page found over budget shows an honest loading state instead of
a blank or frozen frame.

## BACKGROUND

J-06 ("Pages load only what they need") is the sole remaining failing Must-have journey: iter-4 closed J-05
(evaluator: "J-05 partial→passing"; iteration-state: "4 passing (J-01 J-03 J-04 J-05) · 1 failing (J-06)").
No journey is regressed and the last coherence verdict was PASS, so rules 1-2 of the priority rubric don't
apply and J-06 is the only candidate — this is also goal.md's own named "measurement capstone" and last item
in its suggested build order. Depth = **full**, citing **trigger 1 (structural/cross-cutting)**: this is the
FIRST iteration to drive all 11 nav-listed pages as one measurement pass, spanning interactions across
~9 backend modules no single prior journey's tests cover together. The evaluator's own note left room to
downgrade to lean "if J-06 is pure measurement with zero code change," but codebase inspection ahead of this
spec found two previously-unmeasured, plausibly-expensive request paths that make that downgrade
unconfirmable without live numbers: `/api/backtest`'s `evidence_by_horizon` calls
`compute_forward_aggregates` once per each of 5 configured horizons (`config.yaml` `walk_forward.horizons:
[1, 5, 10, 20, 60]`; `forward_testing.py:813-818` — `select(ForwardReturn).where(horizon==h)` then `.all()`,
against a table currently at ~1.5-1.7M rows per the last DB capacity snapshot), and `/api/runs` issues one
`ScannerResult` count query per stored run (`runs.py:33-36`, an N+1 pattern over ~180+ runs). Either could
plausibly exceed budget and need a fix touching a shared data-serving path — contingently also **trigger 2**
if the fix persists a new cache row. The iter-3 lesson applies directly here: "the FIRST iteration to drive
a realistic load pattern through the browser exposes latent trust-surface defects on shared components no
prior iteration exercised" — this iteration is exactly that, for the whole page set at once, so the raw
browser-qa `.llm.md` must be read directly rather than trusting a merged QA summary (iter-4 lesson:
`merge_ui_test_results.py` drops the `## Notes` section and mis-sums the header count).

## IN SCOPE

### Backend
- [ ] Extend the performance-measurement harness (`scripts/measure-perf.sh` or equivalent) to additionally
      capture: (a) backend cold-boot wall time from process start to the first `GET /api/health` HTTP 200
      on the warm committed-seed DB, and (b) each of the 7 not-yet-measured pages' backing endpoint(s):
      `GET /api/dashboard` (+ `/api/market-phase`, `/api/sectors`, `/api/themes` as fired by `/`),
      `GET /api/sectors`, `GET /api/themes`, `GET /api/runs`, `GET /api/backtest`, `GET /api/watchlist`,
      and the `/research/event-study` lab's backing endpoint.
- [ ] Run the full 11-page pass against `scripts/start-backend.sh` / `scripts/start-frontend.sh` (prod
      mode, never `dev.sh`) and append every measured number to `reports/perf-budgets.md` in one new dated
      section — the SAME single file every prior perf item used (no second budgets artifact anywhere).
- [ ] Perform the dev-handoff code-level audit: trace each of the 11 pages' backing endpoint(s) and record,
      per endpoint, whether it reads a persisted snapshot/cache/indexed-bounded query or performs a genuine
      unbounded `daily_prices` scan / uncached inventory-aggregate recompute — explicitly re-trace
      `/api/backtest`'s `compute_forward_aggregates` (5-horizon read) and `/api/runs`'s per-run count query
      (the two candidates flagged above).
- [ ] CONTINGENT (only if the audit or a live measurement finds a genuine violation): apply the minimal fix
      by persisting the value through an ingest-time warm cache following the EXISTING
      `coverage_snapshot` / `EventStudyCache` / `MarketPhaseCache` convention, wired through the value's
      EXISTING computing module and EXISTING serving endpoint — never a second producer — then re-measure
      to confirm the fix clears budget. If the needed fix does not fit this mechanical pattern, stop and
      hand back to a fresh decomposer iteration rather than expanding this one's scope.

### Frontend
- [ ] CONTINGENT (only if a page's measured latency exceeds its committed budget): add the minimal, honest
      loading/progress indicator to that page, reusing an existing loading-state pattern already
      established in the product (e.g., the existing `/data` job-progress pattern) — never a new visual
      language, never a blank or frozen frame.
- [ ] No page, nav, or route changes otherwise.

### New user-facing capability
None by default (measurement + audit only). Contingent: if any page's measured latency exceeds its
committed budget, the user gains an honest, visibly-distinct loading/progress indicator on that page
instead of a blank or frozen frame while the (already-existing) data finishes loading.

### New information displayed
None in the product UI. `reports/perf-budgets.md` gains a new dated section recording, for the first time,
TTI + on-load latencies for `/`, `/sectors`, `/themes`, `/scanner-runs`, `/backtest`, `/watchlist`, and one
`/research` lab, plus the ≤5s boot-to-health budget — an engineering artifact, not a UI surface.

### New user actions
None.

### UI surface changes
None expected. Contingent: a minimal loading/skeleton state on any page found to exceed budget, reusing an
existing loading-state pattern already used elsewhere in the product — never a new visual language.

### Product surface delta
No page, nav, or workflow changes. The product now carries a measured, committed performance floor for
every nav-listed page (not just the 4 already in `reports/perf-budgets.md`), closing goal.md's Success
Criteria "page loads stay within committed never-regress budgets" for the full page set, plus the
≤5-second cold-boot-to-health floor.

### Blueprint conformance
No new Information Architecture home. J-06's canonical artifact is `reports/perf-budgets.md` (already
registered in `blueprint.md`'s Data Contract as "Page performance budgets — N/A, a measurement artifact"),
and every page it measures already has its home in the existing nav skeleton (Dashboard, Stocks, Sectors,
Themes, Scanner Runs, Backtest, Research, Watchlist, Data Manager, Evidence). No
`blueprint.reapproval-requested` file is written this iteration.

### Data-contract additions
None anticipated — this iteration reads/measures values already registered in `blueprint.md`'s Data
Contract for all 11 pages; no new displayed value is introduced. CONTINGENT: if the audit finds a genuine
unbounded-scan/recompute violation (see BACKGROUND's two named candidates) and a fix is built, it must
persist through the affected value's EXISTING computing module + EXISTING serving endpoint — e.g., for
`/api/backtest`'s `evidence_by_horizon`, that is `app.engine.forward_testing.compute_forward_aggregates` /
`GET /api/backtest`, unchanged — and the fix amends that value's EXISTING blueprint.md row (not a new row,
not a second producer).

## OUT OF SCOPE

- No new pages, nav entries, or Information Architecture changes (blueprint IA is unchanged this cycle;
  goal.md's Non-Goal "not a rewrite" holds).
- No changes to `app/engine/readiness.py`'s servability logic, `health-badge.tsx`'s state rendering, or
  `_refresh_ingest_aggregates`'s `tick()` calls — B3/F1 are settled ("Do not redo" in iteration-state); this
  iteration re-verifies them only via the required-still-passing J-04 replay.
- No retirement of `ensure_latest_snapshot` or the boot warm-up loop's cadence bootstrap — left unchanged by
  design (iter-2 decomposer assumption), dormant vs. the offline seed; not re-litigated.
- No expansion of `scripts/start-backend.sh`'s enforced fields beyond the 3 already wired (`memory_cap_mb`,
  `malloc_arena_max`, logfile) — `limit_concurrency` / `timeout_keep_alive_seconds` /
  `graceful_timeout_seconds` stay unwired; Item L already showed zero non-200s/hangs on `/api/health` under
  a heavy rebuild, so no new evidence motivates wiring them now.
- No new Evidence Claims, proven-language, or referee/ledger changes (loop mechanics: J-01…J-06 carry no
  Evidence Claims; AG-1/AG-4/AG-6 still veto).
- No live network calls or paid data services (AG-9) — measurement runs against the committed offline seed
  only.
- The `[NEW]` `demo.sh ops-hardening --session-live` walkthrough bullet (for both J-05 and J-06) — stays
  deferred to session-closeout showcase artifacts, consistent with iter-4's precedent (see NOTES).
- Any fix whose scope exceeds "reuse the existing ingest-time-cache pattern through the value's existing
  computing module/endpoint" (e.g., a genuinely new architectural/schema decision) — hands back to a fresh
  decomposer iteration rather than growing this one open-endedly.

## DEFINITION OF DONE

- [ ] Target journey J-06 passes via browser-qa-agent
- [ ] Required-still-passing journeys J-01, J-03, J-04, J-05 remain green (deterministic replay + LLM
      fallback — mechanically verified at full depth)
- [ ] No anti-goal violation introduced
- [ ] Unit tests pass; no regressions
- [ ] Dev handoff written at `docs/handoffs/goal-ops-hardening-iter-5-dev.md`
- [ ] Backend boot (`scripts/start-backend.sh`, warm committed-seed DB) to first `GET /api/health` HTTP 200
      measured at ≤5s and recorded in `reports/perf-budgets.md`
- [ ] All 11 named pages' TTI + on-load API latencies measured and recorded in `reports/perf-budgets.md`,
      each within its committed (or newly-committed) budget
- [ ] Dev handoff contains a code-level audit naming, per page's backing endpoint(s), that no on-load call
      performs an unbounded `daily_prices` scan or recomputes an already-persisted inventory aggregate

## TESTING REQUIREMENTS

- Browser: J-06 (all 11 pages — `/`, `/stocks`, `/stocks/AAPL`, `/sectors`, `/themes`, `/data`,
  `/evidence`, `/scanner-runs`, `/backtest`, `/watchlist`, `/research/event-study`) + regression replay of
  J-01, J-03, J-04, J-05.
- Unit/integration: re-run the existing byte-identity suites unedited if no fix lands (`test_bar_cache.py`,
  `test_scoring_window.py`, `test_forward_testing.py`, `test_data_manager.py`, `test_health.py`,
  `test_api_engine.py`) to confirm zero regressions. IF a contingent fix lands (e.g., a new warm cache for
  `compute_forward_aggregates`), add unit tests proving: a zero-call invariant for the retired live-compute
  path (mirroring `test_get_data_overview_serves_coverage_from_storage_zero_prefill_calls`), byte-identity
  between the cached and live-computed value for the same as-of, the honest not-yet-computed sentinel on a
  cache miss, and cache refresh/invalidation on every ingest kind that changes the underlying data (the
  iter-2 B1 lesson). The extended perf-measurement harness's output must be captured verbatim into
  `reports/perf-budgets.md` — no separate ad hoc measurement path.
- Error cases: a page/endpoint queried before its backing aggregate/snapshot has ever been computed (cold,
  not-yet-ingested-once DB) must return the existing honest "not yet computed"/NA sentinel — never a 500,
  never a fabricated number. Any page whose live measurement exceeds its committed budget must show a
  visibly distinct loading/progress state — never a blank or silently frozen frame.

- TC-1: given a stopped backend, when `scripts/start-backend.sh` cold-starts against the warm
  committed-seed DB, then the first `GET /api/health` returns HTTP 200 within 5 seconds of process start,
  recorded in `reports/perf-budgets.md`.
- TC-2: given a warm backend+frontend in prod mode (`scripts/start-backend.sh` / `scripts/start-frontend.sh`,
  never `dev.sh`), when `/` (Dashboard) is loaded, then its TTI and each of its sequential on-load calls
  (`/api/dashboard`, `/api/market-phase`, `/api/sectors`, `/api/themes`, plus any indexes/regime-history
  calls the page fires) are individually recorded in `reports/perf-budgets.md`, with the page's overall TTI
  ≤3s.
- TC-3: given a warm backend+frontend, when `/stocks` is loaded, then its TTI and `GET /api/stocks` latency
  are re-measured, recorded, and remain within the existing ≤3s / ≤1.5s committed budgets.
- TC-4: given a warm backend+frontend, when `/stocks/AAPL` is loaded, then its TTI and
  `GET /api/stocks/AAPL` latency are re-measured and remain within the existing ≤3s / ≤0.3s committed
  budgets.
- TC-5: given a warm backend+frontend, when `/sectors` is loaded, then its TTI and `GET /api/sectors`
  latency are recorded in `reports/perf-budgets.md`, each within a newly-committed ≤3s / ≤1.5s budget.
- TC-6: given a warm backend+frontend, when `/themes` is loaded, then its TTI and `GET /api/themes` latency
  are recorded, each within a newly-committed ≤3s / ≤1.5s budget.
- TC-7: given a warm backend+frontend, when `/data` is loaded, then its TTI and `GET /api/data` latency are
  re-measured and remain within the existing ≤3s / ≤1.5s budgets, and the already-committed cold-`/api/data`
  ≤2.0s budget (Item J) is re-asserted in the same table.
- TC-8: given a warm backend+frontend, when `/evidence` is loaded, then its TTI and `GET /api/evidence`
  latency are re-measured and remain within the existing ≤3s budget (warm cache-hit path, per Item I).
- TC-9: given a warm backend+frontend, when `/scanner-runs` is loaded, then its TTI and `GET /api/runs`
  latency (including its per-run `ScannerResult` count queries) are recorded, each within a
  newly-committed ≤3s / ≤1.5s budget.
- TC-10: given a warm backend+frontend, when `/backtest` is loaded, then its TTI and `GET /api/backtest`
  latency — including all 5 configured horizons' `evidence_by_horizon` aggregation — are recorded in
  `reports/perf-budgets.md`, each within a newly-committed budget.
- TC-11: given a warm backend+frontend and at least one saved watchlist entry, when `/watchlist` is loaded,
  then its TTI and `GET /api/watchlist` latency (including the `xray` payload) are recorded, each within a
  newly-committed ≤3s / ≤1.5s budget.
- TC-12: given a warm backend+frontend, when the `/research/event-study` lab is loaded, then its TTI and
  its on-load API latency are recorded, each within a newly-committed ≤3s / ≤1.5s budget.
- TC-13: given the dev-handoff code audit, when each of the 11 pages' backing endpoint(s) is traced, then
  the handoff states, per endpoint, that it reads a persisted snapshot/cache/indexed-bounded query and
  names zero call sites performing an unbounded `daily_prices` whole-table scan or an uncached recompute of
  an already-registered inventory aggregate — or names exactly which call site violates this and what fix
  was applied.
- TC-14: given any page/endpoint whose live measurement exceeds its committed budget, when the page is
  loaded, then the UI shows a visibly distinct loading/progress element (not a blank or frozen frame) until
  the data arrives.
- TC-15: given the full 11-page + boot measurement pass is complete, when `reports/perf-budgets.md` is
  reviewed, then every new/re-measured number lives ONLY in that file — no second budgets artifact exists
  anywhere in the repo.
- TC-16: given J-01/J-03/J-04/J-05's existing browser journeys, when they are replayed this iteration
  (deterministic golden script, LLM fallback on a miss), then each still passes with zero regression
  attributable to this iteration's changes.
- TC-17 (contingent — only if a fix lands): given a lazy/cached value touched by this iteration's fix
  (e.g., a new warm cache for `compute_forward_aggregates`), when its served value is compared to the
  canonical live computation for the same as-of, then the two are byte-identical, asserted by a unit test.
- TC-18 (contingent — only if a fix lands): given a newly-added ingest-time warm cache queried for a
  not-yet-warmed key, then it serves the existing honest "not yet computed" sentinel (never a fabricated
  value, never a 500); and given any ingest kind that changes the underlying data the cache derives from,
  when that ingest completes, then the cache is refreshed or invalidated (never silently stale).
- TC-19: given this iteration's full set of changes (or the zero-diff case if no fix lands), when the
  relevant backend test suite is run, then it passes with zero new failures against the pre-iteration
  baseline count.
- TC-20: given the iteration's work is complete, when `docs/handoffs/goal-ops-hardening-iter-5-dev.md` is
  opened, then it contains TC-13's audit findings, a pointer to the exact `reports/perf-budgets.md`
  section this iteration added, and an explicit statement of whether any contingent fix was applied.

## NOTES

- **Lesson applied (iter-3):** "a tightly-scoped fix passing every other lane can still fail its target
  journey because the FIRST iteration to drive a realistic/new load pattern through the browser exposes
  latent shared-surface defects" — J-06 is exactly this, for the whole 11-page set at once. Cross-check the
  QA verdict against the RAW `reports/phase-goal-ops-hardening-iter-5-ui-test-results.llm.md`, not a merged
  summary, before scoring.
- **Lesson applied (iter-4):** `merge_ui_test_results.py` drops the raw `## Notes` section and mis-sums the
  header count — read the `.llm.md` sibling directly.
- **Lesson applied (iter-2):** if a contingent ingest-time cache is added, key it so a fingerprint-only
  invalidation cannot serve a false all-zero/empty sentinel on a fully-populated DB — verify the
  fetch-then-view path too, not just backfill-then-view (mirrors the iter-2 B1 root cause).
- **Closure-gate reminder (do not lose):** J-05's AND J-06's `[NEW]` `demo.sh ops-hardening --session-live`
  walkthrough bullets remain deferred showcase artifacts (see assumptions.md, iter-4 and iter-5 entries).
  Both should be produced — or the human should explicitly accept their deferral — before the eventual
  GOAL_ACHIEVED gate.
- If J-06 passes this iteration, all 5 Must-have journeys will be passing. The evaluator should weigh
  whether to declare GOAL_ACHIEVED next, factoring in the demo.sh closure-gate item above.
- Known specific risk flagged by this iteration's code inspection, not yet measured live: `/api/backtest`'s
  `evidence_by_horizon` calls `compute_forward_aggregates` once per configured horizon (5 horizons — 1, 5,
  10, 20, 60 days — per `config.yaml`), each reading `select(ForwardReturn).where(horizon==h)`
  (`forward_testing.py:813-818`) — a candidate for exceeding budget on the current ~1.5-1.7M-row
  `forward_returns` table; measure this page with extra attention. Secondary: `/api/runs` (`runs.py:33-36`)
  issues one `ScannerResult` count query per stored run (~180+ runs) — an N+1 pattern worth a latency check
  even though each individual query is index-bound.
- `/api/health`'s own `func.max(DailyPrice.date)` / `func.count(distinct(DailyPrice.symbol))`
  (`health.py:44-45`) is pre-existing, unaffected by this iteration, and has consistently measured
  ~0.09-0.099s against its own tight ≤0.1s budget across every prior measurement on file — re-confirm, do
  not "fix" it; it is not one of goal.md's "four offenders" and touching it risks the settled B3 readiness
  logic ("Do not redo").
