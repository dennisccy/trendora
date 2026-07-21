# Goal Iteration 6 — Close out J-06: fix the Dashboard/Data-Manager real-browser latency budget

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** ops-hardening
- **Iteration:** 6
- **Mode:** next
- **Depth:** full
- **Frontend Present:** yes
- **Target journeys:** J-06
- **Required-still-passing journeys:** J-01, J-03, J-04, J-05
- **Anti-goal reminders:**
  - **AG-1:** A score, ranking, or "edge" MUST NOT be presented as proven/confident unless it is backed by a **passing certified-claim entry** in the evidence ledger (out-of-sample, control-beating). Unbacked values MUST render a "not yet proven" state. *(critical)*
  - **AG-2 — Decision-quality only:** never present return promises, price targets, "buy/sell" signals, or alpha claims; never place or simulate orders. *(critical)*
  - **AG-3:** A journey passes ONLY if the **displayed numbers are correct** — they match the engine's computation for the same as-of date — not merely that the page renders. *(critical)*
  - **AG-4 — No overfit edges:** any pattern surfaced as "proven" must have survived the referee (sealed out-of-sample holdout + controls + multiple-testing correction), never in-sample fit alone. *(critical)*
  - **AG-5 — Preserve determinism and no-lookahead:** scoring uses bars ≤ as-of; forward returns use bars > as-of; never introduce lookahead anywhere. *(critical)*
  - **AG-6:** No iteration ships if its evidence-derived claims (if any) lack a passing referee verdict from the post-decompose gate. *(critical)*
  - **AG-7:** No hard-coded credentials, API keys, or tokens in source files. *(critical)*
  - **AG-8 — Resilience to data-shape and data-scale change:** widening the data basis (new nulls, broader pools, deeper history) must never crash an existing page or exhaust a service's memory — every existing consumer of a widened field is re-validated, the UI degrades gracefully (contained error boundary, honest "—"/NA placeholder, never a blank application-error page), and unbounded whole-table ORM loads are forbidden on the deep basis. *(critical)*
  - **AG-9 — Offline-deterministic ingest:** ingest jobs (fetch/backfill/rebuild) run only against the committed seed / local provider fixtures — no live external network calls or paid data services may be introduced without an explicit goal.md amendment. *(critical)*

## GOAL

Every one of J-06's 11 named pages loads within its committed `reports/perf-budgets.md` budget under a
**real browser**, not just curl — closing the session's last failing Must-have journey by fixing the
Dashboard's/Data Manager's genuine browser-connection-queuing latency, not by loosening the numbers.

## BACKGROUND

Iter-5 delivered a real, verified backend win (`ForwardAggregateCache`, 34.77s→0.138s on `/api/backtest`)
but J-06 still FAILed: browser-qa measured `GET /api/indexes?full=true` at 1.68–2.19s (3/3 real-browser
reloads) against its ≤1.5s budget, while curl measured only 0.79–0.95s. QA/closure/ux-regression/audit all
converged on the same root cause — Chrome's 6-connections-per-origin cap queues the Dashboard's 10–13
near-simultaneous same-origin on-load calls under HTTP/1.1 uvicorn — and named the identical class on
`/data`'s `GET /api/data/availability` (2.9–3.0s browser vs ~1.0s curl, previously unbudgeted). Per the
priority rubric this iteration targets J-06 alone (rule 3, the only remaining failing journey and the
session's last one) with everything else carried as Required-still-passing (rule 4/5 — one risky change,
not two). **Depth is full**, citing trigger 1 (structural/cross-cutting): the fix spans the Dashboard
(`page.tsx` + `phase-cross-view-card.tsx` + sibling on-load cards) and Data Manager
(`availability-heatmap.tsx`/`data/page.tsx`) — ≥3 modules whose interaction (browser connection-pool
contention) is not covered by any single module's unit tests, only by a real-browser QA/closure/
ux-regression pass; this is also J-06's second attempt after a multi-lane FAIL last cycle, so the full
pipeline's independent verification lanes matter here specifically.

**Lessons applied** (per `lessons.md`): (iter-5) curl systematically under-reports real page latency —
this iteration's DoD requires REAL BROWSER measurement (3 reloads, Network-tab timing), not curl, for the
two previously-violating endpoints; a page's total on-load call fan-out is itself the risk. (iter-5)
deterministic golden-script assertions on a growing unpaginated list go stale silently — J-01's
`/scanner-runs` step 6 is fixed to assert on data the journey's own submitted run produces, not a fixed
historical row. (iter-3) always cross-check the merged QA verdict against the RAW
`ui-test-results.llm.md` browser-qa verdict before scoring J-06 clean — the merge script still drops the
`## Notes` section.

**Scope-selection deviation note:** the priority rubric's "unblockers next" (rule 3) would normally favor
the smallest/least-risky item first, but J-06 is the ONLY remaining failing journey — there is no smaller
failing item to defer to. J-04/J-05's `unknown` status (missing replay coverage, not failure) is addressed
via the Required-still-passing set rather than as a target, per the rubric's own distinction between
targets (failing/partial) and the regression set (everything else relevant).

## IN SCOPE

### Backend
- [ ] None. This iteration's latency fix is FRONTEND-ONLY (fetch scheduling/timing) — no backend
  endpoint, computing module, or Data Contract value is added or changed. (Explicit constraint: do NOT
  create a new aggregating/combined endpoint for Dashboard values — every affected value already has a
  registered single computing module + single serving endpoint in `blueprint.md`; a second endpoint for
  any of them is a coherence violation, not a fix.)

### Frontend
- [ ] Reduce the Dashboard's on-load same-origin connection contention (`apps/frontend/app/page.tsx`,
  `apps/frontend/components/phase-cross-view-card.tsx`, and sibling on-load cards
  `major-indexes-card.tsx` / `market-phase-card.tsx` as needed) so `GET /api/indexes?full=true`'s
  REAL-BROWSER response time falls within its committed ≤1.5s budget — e.g. stagger/defer the
  below-the-fold `PhaseCrossViewCard`'s `Promise.all` fetch relative to the above-the-fold cards' own
  on-mount fetches, or cap total concurrent same-origin on-load requests. No new endpoint; every value
  keeps its EXISTING single computing module and serving endpoint (only request timing/ordering changes).
- [ ] Apply the same connection-contention fix to the Data Manager page's `GET /api/data/availability`
  fetch (`apps/frontend/components/availability-heatmap.tsx`, `apps/frontend/app/data/page.tsx`) so its
  real-browser response time falls within its newly committed budget (see Test infrastructure below).
- [ ] Preserve every existing loading/error affordance untouched (`PhaseCrossViewCard`'s `"loading"`/
  `"error"`/`"empty"` states, the availability heatmap's own loading spinner) — the fix changes WHEN/how
  many requests fire, never the component's rendering contract.

### Test infrastructure & docs
- [ ] Commit `GET /api/data/availability`'s first budget row (real-browser-measured) into
  `reports/perf-budgets.md` — the SAME single budgets artifact, no second file — at the generic ≤1.5s
  endpoint-budget class used throughout the file, unless the live post-fix browser measurement requires a
  documented adjustment (state the reason inline if so).
- [ ] Re-measure and re-record, in `reports/perf-budgets.md`, all 11 J-06 pages' TTI + on-load latencies
  using REAL BROWSER measurement (Network-tab timing, 3 reloads) for at minimum the two
  previously-violating endpoints (`/api/indexes?full=true`, `/api/data/availability`) — curl alone is not
  sufficient evidence per the iter-5 lesson.
- [ ] Fix `runs/goal-session-ops-hardening/journey-scripts/J-01.json` step 6's stale regression proxy
  (hardcoded `"2026-05-15"` text assertion on the growing, unpaginated `/scanner-runs` list — now buried
  past a 750-row fold) to assert against `/data`'s own persisted run-history panel entry for the run this
  script's own steps 2–4 submit, per the iter-5 lesson ("assert on data the journey's own action
  produces").
- [ ] Run `pytest tests/test_api_backtest.py tests/test_mcp_window.py -v` (TMPDIR set) to completion —
  carried over from iter-5 (unrun there; the `loaded_engine` fixture suite takes several minutes).

### New user-facing capability
None — Dashboard and Data Manager already show the same information. This iteration only makes their
existing on-load data arrive within budget under real browser use, removing a multi-second stall on first
paint of the Phase Cross-View chart and the availability heatmap.

### New information displayed
None.

### New user actions
None.

### UI surface changes
None — same cards/panels, same content; only fetch timing/ordering changes. Existing loading skeletons
(`PhaseCrossViewCard`'s `animate-pulse`, the availability heatmap's own spinner) already cover the async
gap and are confirmed (iter-5 dev handoff) to never blank or freeze.

### Product surface delta
Dashboard and Data Manager first-loads feel materially snappier under real browser conditions — no value
removed or added, only queuing latency eliminated.

### Blueprint conformance
No new surfaces. Dashboard (`/`) and Data Manager (`/data`) are both existing Information Architecture
homes already registered in `blueprint.md` (J-05's row lists `/` "market phase card"; J-06's row is
"cross-cutting measurement; canonical artifact is `reports/perf-budgets.md`"). This iteration's fix and
its measurement artifact both live entirely within those existing homes — no nav/route change, so no
`blueprint.reapproval-requested` entry is written.

### Data-contract additions
None. `GET /api/data/availability`'s new budget row is a measurement-artifact entry in the
ALREADY-registered "Page performance budgets" row of `blueprint.md`'s Data Contract (canonical artifact
`reports/perf-budgets.md`, unchanged) — not a new displayed runtime value, not a new computing module, not
a new serving endpoint. `blueprint.md` is updated (additive note only) to record this.

## OUT OF SCOPE

- Any new backend endpoint or second serving path for an already-registered Data Contract value (Dashboard
  snapshot, market phase, sectors, themes, indexes, regime history, coverage/availability all keep their
  existing single producer + single endpoint).
- HTTP/2 / TLS on the uvicorn launcher — a viable alternative fix in principle, but out of scope this
  iteration: it requires certificate/deployment machinery disproportionate to a local-first, offline
  tool, and the frontend-only fetch-scheduling fix is sufficient given curl's own baseline (0.79–1.0s) is
  already comfortably under the 1.5s budget once queuing is removed.
- `/api/runs`'s N+1 pattern — measured in-budget (0.050–0.196s) in iter-5, left unfixed by design.
  "Do not redo."
- `readiness.py` / `health-badge.tsx` (B3/F1 fixes, iter-4) — settled, out of scope. "Do not redo."
- `ForwardAggregateCache` / `forward_aggregates_cached` — shippable as-is from iter-5, no further changes.
  "Do not redo."
- The `[NEW]`-flagged `demo.sh ops-hardening --session-live` walkthroughs for J-05 and J-06 — still
  deferred to session-closeout showcase artifacts per the iter-4/iter-5 assumption-ledger entries; not
  part of this iteration's Definition of Done.
- `max_range_days`, `snapshot_cadence`, or any other J-01/J-03 config/data-jobs surface — both journeys
  already pass; untouched this iteration.

## DEFINITION OF DONE

- [ ] Target journey J-06 passes via browser-qa-agent — all 11 named pages within their committed
  `reports/perf-budgets.md` budgets, verified by REAL BROWSER measurement (not curl) for the two
  previously-violating endpoints (TC-1, TC-2, TC-3, TC-4)
- [ ] Required-still-passing journeys J-01 (with its fixed golden script), J-03, J-04, J-05 remain green —
  deterministic replay where a golden script exists, LLM fallback lane otherwise (TC-6, TC-7, TC-8)
- [ ] No anti-goal violation introduced — every touched endpoint's payload stays byte-identical pre/post
  fix (AG-3); no new whole-table scan or lookahead introduced (AG-5/AG-8); abort/error paths stay honest,
  never a blank frame (TC-5, TC-10)
- [ ] Unit tests pass; no regressions; `pytest tests/test_api_backtest.py tests/test_mcp_window.py -v`
  runs to completion with zero failures (TC-9)
- [ ] The existing ≤5s boot-to-health budget is unaffected by this iteration's frontend-only change
  (TC-11)
- [ ] Dev handoff written at `docs/handoffs/goal-ops-hardening-iter-6-dev.md`

## TESTING REQUIREMENTS

- Browser: J-06 (all 11 named pages; 3 real-browser reloads each for `/api/indexes?full=true` and
  `/api/data/availability`); J-01 (deterministic replay of the fixed golden script); J-03 (deterministic
  replay, unchanged); J-04, J-05 (no golden script on file — LLM browser-qa fallback against their numbered
  acceptance steps in `docs/goal.md`)
- Unit/integration: `pytest tests/test_api_backtest.py tests/test_mcp_window.py -v` (TMPDIR set) run to
  completion; any changed frontend fetch-scheduling logic exercised by its existing component-level tests
  if present
- Error cases: an in-flight deferred/staggered fetch that gets aborted (e.g. a fast `as_of` toggle) must
  still show the existing honest error/loading state, never a blank or frozen frame

Test-first contract:

- TC-1: given a warm prod-mode backend+frontend (`scripts/start-backend.sh` / `scripts/start-frontend.sh`)
  and a real Chrome browser, when the Dashboard (`/`) is loaded and reloaded 3 times, then each reload's
  Network-tab timing for `GET /api/indexes?full=true` is ≤1500ms in all 3 trials.
- TC-2: given the same warm prod-mode session, when the Data Manager (`/data`) page is loaded and reloaded
  3 times, then each reload's Network-tab timing for `GET /api/data/availability` is within its newly
  committed `reports/perf-budgets.md` budget in all 3 trials.
- TC-3: given the same session, when all 11 J-06-named pages (`/`, `/stocks`, `/stocks/AAPL`, `/sectors`,
  `/themes`, `/data`, `/evidence`, `/scanner-runs`, `/backtest`, `/watchlist`, one `/research` lab) are
  loaded once each, then every page's TTI and every on-load endpoint's latency stays within its
  `reports/perf-budgets.md` budget (no new violation introduced anywhere else by the scheduling change).
- TC-4: given `reports/perf-budgets.md` has no `GET /api/data/availability` row before this iteration,
  when this iteration's measurement pass completes, then the file contains exactly one new row for it
  (same single artifact, no second budgets file created anywhere in the repo).
- TC-5: given the fetch-scheduling fix, when `/api/dashboard`, `/api/market-phase`, `/api/sectors`,
  `/api/themes`, `/api/indexes?full=true`, `/api/regime-history?full=true`, `/api/market-phase?full=true`,
  and `/api/data/availability` are each captured at a fixed `as_of`, then every payload is byte-identical
  to its pre-fix response (only request timing/ordering changed, not values).
- TC-6: given `runs/goal-session-ops-hardening/journey-scripts/J-01.json` step 6 is rewritten to assert on
  the submitted run's own `/data` run-history entry, when the script is replayed deterministically, then
  all 6 steps pass with zero manual adjudication needed.
- TC-7: given `runs/goal-session-ops-hardening/journey-scripts/J-03.json` is unchanged, when it is
  replayed deterministically, then all its steps pass (J-03 stays green).
- TC-8: given J-04 and J-05 have no golden script on file, when browser-qa-agent runs its LLM fallback
  lane against each journey's numbered acceptance steps from `docs/goal.md`, then each is scored
  `passing` with cited evidence, or an honestly reported non-passing result with evidence — moving both
  out of `unknown`.
- TC-9: given `apps/backend/tests/test_api_backtest.py` and `apps/backend/tests/test_mcp_window.py`'s
  `loaded_engine`-dependent suites, when run via `pytest tests/test_api_backtest.py
  tests/test_mcp_window.py -v` (TMPDIR set) to completion, then all tests pass with zero failures.
- TC-10: given `PhaseCrossViewCard`'s fetch is deferred/staggered and its `AbortController` fires mid-flight
  (e.g. a fast `as_of` toggle unmounts the effect), when the fetch is aborted, then the component shows
  its existing honest `"error"`/loading state, never a blank or frozen frame.
- TC-11: given a real backend restart via `scripts/start-backend.sh`, when `GET /api/health` is polled
  from process start, then the first HTTP 200 arrives within 5 seconds (confirms this frontend-only fix
  does not affect the existing boot budget).

## NOTES

- **Closure-gate reminder (restated from iter-4/iter-5):** BOTH J-05's and J-06's `[NEW]`-flagged
  `demo.sh ops-hardening --session-live` walkthroughs are still owed as session-closeout showcase
  artifacts — produce both, or have the human explicitly accept their deferral, before the eventual
  GOAL_ACHIEVED gate. Not part of this iteration's scope or DoD.
- **Evaluator reminder (iter-3/iter-4 lesson):** read the raw `reports/qa/goal-ops-hardening-iter-6-ui-test-results.llm.md`
  directly rather than trusting the merged `ui-test-results.md` alone — `merge_ui_test_results.py` is
  still known to drop the `## Notes` section that holds load-bearing caveats.
- If the live post-fix browser measurement shows the fetch-scheduling change alone is insufficient to
  bring `/api/indexes?full=true` under 1.5s (unexpected given curl's 0.79–0.95s baseline), do NOT fall
  back to creating a second/combined endpoint — stop and hand back to a fresh decomposer pass rather than
  expanding scope into a Data Contract change mid-iteration, per this session's own established
  contingent-fix discipline (iter-5 precedent).
- Two interpretation calls this iteration are logged to `runs/goal-session-ops-hardening/state/assumptions.md`
  (frontend-only fix choice over HTTP/2 or a combined endpoint; committing `/api/data/availability`'s
  first budget number rather than leaving it permanently unbudgeted).
