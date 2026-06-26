# Goal Iteration 50 — Factor Lab all-factors Rank-IC + risk-adjusted table (J-107)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** i_can_see_the_wealthy_future_forever_with_my_loved_ones
- **Iteration:** 50
- **Mode:** normal
- **Depth:** full
- **Frontend Present:** yes
- **Target journeys:** J-107
- **Required-still-passing journeys:** J-25, J-26, J-29, J-77, J-91, J-103, J-51, J-63, J-65, J-104, J-06, J-18, J-07, J-106, J-108
- **Anti-goal reminders:**
  - **Single source of truth.** Each of the six canonical scores (and the A–E bucket and setup status) MUST be computed exactly once by the scoring/regime engine and read identically by every page; the API and frontend MUST NOT recompute them. The same symbol's score MUST NOT differ between two views. *(critical)*
  - **No recompute in the read path.** Read endpoints MUST serve canonical values from the persisted immutable snapshot for the resolved as-of date; they MUST NOT recompute scores/returns/buckets per request.
  - **Research lab is read-only, honest & not predictive.** Every Factor-Lab and event-study figure (decile means, rank-IC, combination cohorts, regime slices, distribution, hit-rate, expectancy, MAE/MFE, exit-horizon, risk-adjusted ratios) MUST be derived once from the stored per-observation forward returns + stored factor values + post-snapshot price path; the API and frontend MUST NOT recompute returns or factors to build them; low-sample cells show NA + n; results carry the survivorship-bias label. The lab is descriptive evidence, not a fitted/ML predictive model; the as-of-date mode merely FILTERS the stored observation set to snapshots dated ≤ the as-of date (it recomputes nothing).
  - **Risk-adjusted reporting is honest & must not conflate up/down volatility.** Every risk-adjusted figure (return/vol, return/MAE, Sharpe-like, expectancy) MUST be derived once from the stored per-observation forward returns + post-snapshot price path; "risk" MUST use downside volatility / MAE / drawdown — never total volatility, which would penalise healthy upside moves; raw and risk-adjusted MUST be shown side by side; low-sample cells show NA + n.
  - **No magic numbers.** Every scoring weight, threshold, decision-rule cutoff, bucket edge, universe entry, and theme definition MUST come from the config file — no such literal in calculation code.
  - **No fabricated data.** On a data-provider failure the system MUST surface an explicit stale/unavailable state and MUST NOT synthesize prices or scores to force a green journey.
  - **No lookahead.** Scoring for a snapshot dated D MUST use only price bars with date ≤ D; forward returns MUST use only bars with date > D. *(critical)*
  - **Exactly one date selector.** The frontend MUST NOT maintain a second, independent date state; every date-scoped page reads the single global as-of control. The Research all-history / as-of-date toggle is a MODE, NOT a date control — its as-of mode reads the same single global as-of control (no second date state).
  - **Risk-Off must gate Actionable.** When the regime is Risk-Off, the scanner MUST mark zero stocks "Actionable" (watchlist-only). *(critical)*

## GOAL

On `/research/factor-lab`, replace the single-factor dropdown with an all-factors table — one row per config-catalog factor showing its family, Rank-IC (value + N), and a downside-risk-adjusted figure at the selected horizon — that is client-side sortable NA-last and whose rows expand in place to reveal that factor's D1–D10 decile sort, with each decile's `N=` chip still drilling into Research Samples.

## BACKGROUND

J-107 is the **last unbuilt buildable Must-have** (the goal.md J-106…J-108 extension; J-106 and J-108 landed passing in iter-49). The iter-49 evaluator recommended iter-50 FULL to build it, because it touches the cached-aggregate / streamed research read path — the iter-46/47/48 OOM-sensitive area — and because, once J-107 passes with a flushed-green suite + COHERENCE-PASS + zero regression, the next evaluation is a sound **GOAL_ACHIEVED candidate** (every buildable Must-have positive-evidenced; J-22/J-23/J-24 stay honestly blocked-NA, non-vetoing). Depth is **full**: the change crosses backend (research engine + API) and frontend, exercises the streamed read path, and gates GOAL_ACHIEVED candidacy on the full pytest suite.

This is an **in-place resume after an aborted iter-50** — the J-107 implementation already exists in the working tree from the aborted run (backend `apps/backend/app/engine/research.py` +199, `apps/backend/app/api/research.py` +43, new `apps/backend/tests/test_factor_lab_all.py`; frontend `apps/frontend/app/research/_labs.tsx` +593, `apps/frontend/lib/api.ts` +51). The aborted run's reviewer returned PASS_WITH_NOTES and its browser-QA returned 15/18: the one P1 "FAIL" (UT-03) is a **test-plan expectation bug, not a product defect** — the table defaults to descending Rank-IC, so the first header click correctly toggles to ascending (UT-04 confirms the toggle works and reverses on the second click). The developer should verify / finish the existing implementation and the reviewer/QA should re-score against the corrected sort acceptance below, not rebuild from scratch.

## IN SCOPE

### Backend
- [ ] Serve an **all-factors aggregate** on the EXISTING `GET /api/research/factor-lab` via an **additive flag** (e.g. `all=true`) — one entry per `config`-catalog factor (incl. the volatility family) carrying `family`, `rank_ic` (value + N), and a `risk_adjusted` (downside-only) figure at the selected horizon, plus that factor's D1–D10 decile rows. NO new endpoint.
- [ ] Produce every value from the **same canonical builders** the single-factor lab uses (`compute_factor_lab` / `_rank_ic` / risk-adjusted / decile builders) — one computation path, figures **byte-identical** to the single-factor view (Single source of truth; No recompute in the read path).
- [ ] Serve from a **derived-once cached aggregate** (the `EventStudyCache` + `_dataset_version` idiom; J-72 / J-104 perf contract) over **ONE shared streamed / column-projected observation pass** — `yield_per`-batched, batch size config-defined, NO unbounded `select(...).all()` over `ForwardReturn` OR `ScannerResult` (J-105). Order `ScannerResult` reads by `(run_id, id)`, not bare `id` (iter-48 temp-sort / disk-full lesson; host disk ~93% full).
- [ ] Add **no new `table=True` model** (reuse the `EventStudyCache` sentinel namespace) so the `test_db.py` expected-tables guard stays unchanged. Ensure any reused cache key distinguishes the all-factors payload (a payload-schema-distinct sentinel/namespace) so a pre-existing cache row is never served field-less (iter-38/39/44 cache-schema keystone).

### Frontend
- [ ] On `/research/factor-lab`, **remove the single-factor dropdown / `FactorSelector`** and render an **all-factors table**: one row per factor with Factor, Family, Rank-IC (value + N), Risk-adjusted (downside) columns at the selected horizon (the existing horizon selector remains).
- [ ] Make the table **client-side sortable NA-last** under the J-48 view-transform contract (re-orders only; recomputes/refetches nothing). Resolve sort headers with stable `aria-label`s.
- [ ] Each factor row is **click-to-expand in place** (the keyboard-accessible `aria-expanded` expandable-row pattern the Sectors page already uses) revealing that factor's D1–D10 **decile sort** (factor range, mean return, risk-adjusted, N, low-sample flag), **hidden by default**; click again to collapse.
- [ ] Each decile `N=` chip still **drills into Research Samples** in a new tab reproducing the exact cohort (J-51 / J-65 count-coherence).
- [ ] Honor the Research **As-of mode** as a pure observation-set filter on the single global as-of (J-32) — no second date state.
- [ ] **Retire the per-regime effectiveness table** and the separate single-factor Rank-IC card from THIS view (the `by_regime` slice remains the same derived-once canonical value, just no longer rendered here; the multi-factor composite lab on `/research/factor-combination` is untouched).
- [ ] Clean up the now-unused `fetchFactorLab` / `FactorLabResponse` export OR annotate it as intentionally retained for the single-factor backend contract (reviewer NOTE from the aborted run).

### New user-facing capability
A researcher can compare **every** catalog factor's predictive edge (Rank-IC + downside-risk-adjusted figure) at a chosen horizon in one sortable table, then expand any factor in place to inspect its full decile sort — without cycling a single-factor dropdown.

### New information displayed
A per-factor Rank-IC (value + N) and a downside-risk-adjusted figure for every catalog factor at the selected horizon, side by side, raw and risk-adjusted shown together.

### New user actions
Sort the all-factors table by any column (Rank-IC, N, risk-adjusted); click a factor row to expand/collapse its decile sort; click a decile `N=` chip to open that cohort in Research Samples (new tab); toggle horizon; toggle Research As-of mode.

### UI surface changes
`/research/factor-lab` only: dropdown replaced by an all-factors table with expandable decile panels; the per-regime effectiveness table and standalone Rank-IC card removed from this view.

### Product surface delta
The Factor Lab shifts from "inspect one factor at a time" to "rank all factors at a glance, drill into any one" — a strictly richer, byte-identical re-presentation of values the lab already computes.

### Blueprint conformance
No new surfaces and no nav-skeleton change. J-107 lives on the **existing** `/research/factor-lab` home (under the Research hub, reachable in ≤2 clicks from the persistent nav). The blueprint already carries the J-107 registration additively on the existing **Factor-Lab analytics** Data-Contract row (canonical module `research:compute_factor_lab`, existing serving endpoint `GET /api/research/factor-lab`). No `blueprint.reapproval-requested` is needed.

### Data-contract additions
None. The all-factors table re-presents the SAME canonical Factor-Lab values (Rank-IC, N, downside-risk-adjusted, deciles) already produced by `research:compute_factor_lab` and served on `GET /api/research/factor-lab`. No new computing module, no new endpoint, no new displayed value — figures are byte-identical to the single-factor view.

## OUT OF SCOPE

- The multi-factor **composite** combination lab on `/research/factor-combination` (untouched).
- The `by_regime` per-regime slice as a rendered Factor-Lab table (the canonical value stays; it is simply no longer surfaced in this view).
- Any change to canonical decile / IC / risk-adjusted math, the scoring/regime engine, the Risk-Off→Actionable gate, or the as-of contract.
- Any new `table=True` model / new endpoint / new stored column.
- The data-walled J-22 / J-23 / J-24 (stay blocked-NA, non-vetoing — do not attempt a real provider screen).

## DEFINITION OF DONE

- [ ] J-107 passes via browser-qa-agent on live, evaluator-viewable rendered evidence (all-factors table; sort reorders + toggles NA-last; row expands/collapses to D1–D10; decile `N=` chip opens a count-coherent Samples cohort; horizon + As-of mode update all rows together).
- [ ] Required-still-passing journeys remain green (J-25/J-26/J-29/J-77/J-91/J-103 labs; J-51/J-63/J-65 N= coherence; J-104 labs-load-reliably; J-06/J-18/J-07 CRITICAL; J-106/J-108).
- [ ] No anti-goal violation introduced (byte-identity asserted; downside-only risk; streamed bounded read; no second date state; no new magic number; no new table).
- [ ] Unit tests pass; no regressions. Backend tests prove: all-factors figures **byte-identical** to the single-factor builder; cache correctness against an **already-populated** cache row (not a fresh compute); the read path is bounded / streamed (no unbounded `.all()`); NA honesty for zero-N / low-sample factors.
- [ ] The **full pytest suite flushes `0 failed, EXIT 0`** (nohup-async via the pump; never block the evaluator on the in-flight suite) — this is the GOAL_ACHIEVED-candidacy gate.
- [ ] Dev handoff written at `docs/handoffs/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-50-dev.md`.

## TESTING REQUIREMENTS

- **Browser (by ID):** J-107 (primary). Re-verify on the rendered page: the all-factors table loads (one row per catalog factor, all columns); the sort acceptance below; row expand→D1–D10 then collapse; decile `N=` chip → Samples cohort with total == chip N; horizon change updates all rows; As-of mode reduces N globally via the single top-bar date control; honest "Backend unavailable" (no fabricated rows) when the backend is down. Also smoke J-06/J-18/J-07 (CRITICAL) and J-104 (a sibling lab still loads).
  - **Sort acceptance (corrects the aborted run's UT-03 false-negative):** the acceptance is that clicking a column header **reorders the table and toggles sort direction, with NA rows last in both directions** — it is **NOT** that the first click must be descending. The table **defaults to descending Rank-IC**, so the first header click correctly toggles to **ascending** and the second back to descending. Resolve the header by `aria-label`, capture **two byte-distinct** frames (md5-check the pair), and do not record a sort FAIL merely because the first-click direction differs from a naive expectation (iter-27 / iter-28b sort-selector false-negative lesson — confirm the `onSort` / comparator code path is byte-benign before calling any sort failure a regression).
- **Unit/integration:** byte-identity of every all-factors figure vs the single-factor `compute_factor_lab` / `_rank_ic` / risk-adjusted / decile builders (across horizons, all-history vs As-of, and zero-N cohorts); cache correctness seeded against an **already-populated** old/other-shape cache row (iter-38/39/44); the streamed read path materializes **no** unbounded full table (FR AND ScannerResult); `ScannerResult` ordered by `(run_id, id)`; decile `N=` cohort total equals the published n (J-51/J-65). Confirm `test_db.py` expected-tables is unchanged (no new table) and `test_no_magic_numbers` stays green (downside-risk / config-catalog literals sourced from config, not inline).
- **Error cases:** a zero-N or low-sample factor renders **NA + n** (never a fabricated number) and sorts last; an unrecognized / out-of-range horizon or factor never fabricates a row; backend-down shows the honest unavailable state, no placeholder figures.

## NOTES

- **GOAL_ACHIEVED gate.** J-107 is the last unbuilt buildable Must-have (iter-22 lesson: queued-but-unbuilt Must-haves are `unknown`, not done). After it lands green on live evidence with a **flushed-green full suite** + COHERENCE-PASS + zero regression, the next evaluation is a sound GOAL_ACHIEVED candidate. J-22/J-23/J-24 stay honestly blocked-NA (non-vetoing per goal.md:105-108) — do not attempt to build them.
- **Aborted-run state.** The J-107 code is already present in the working tree (review PASS_WITH_NOTES; browser-QA 15/18 with the lone P1 being the UT-03 test-plan expectation bug clarified above, plus two precondition SKIPs: UT-14 loading skeleton not captured, UT-15 no zero-N rows in the warm seed). Verify / finish the existing implementation; do not rebuild from scratch. Probe the **uncached** lab **cold** to prove the streaming fix (a cache hit masks an unstreamed `.all()` on a sibling — iter-47/48), and grep EVERY unbounded `.all()` in the touched builders (FR AND ScannerResult AND ScannerRun — iter-47).
- **Heavy-research evidence hygiene (this host).** PLAN the Playwright fallback **up front** (Chrome MCP CDP has emptied the evidence dir on iters 38/39/40/42); `md5sum` the evidence dir FIRST and reject blank/skeleton/"Backend unavailable"/byte-identical frames; resolve sort/decile/`N=` controls by `aria-label`, not visible `text()` (iter-27/28b). Run heavy-research browser-QA on a **freshly-restarted, warmed, single-fetch-at-a-time** backend, and **NEVER** run the full pytest suite concurrently with the heavy-lab probes (its RAM pressure exacerbated the iter-46/47 factor-lab OOM; pool-exhaustion lesson iter-45).
- **Suite gating.** On this daily-history host, split fast (no-boot) vs slow (seed-boot) tests for quick anti-goal verification, but gate GOAL_ACHIEVED candidacy on the **flushed** `0 failed, EXIT 0` line from a nohup-launched full suite via the pump (iter-11/29/37); re-run any isolated `test_warmup.py` / `test_data_manager_jobs_pipeline.py` / `test_watchlist_persistence.py` E/F before attributing it (the documented slow-boot / contention flake). Do NOT re-trigger the J-85 `kind:rebuild` (~11h destructive; data is correct).
