# Goal Iteration 52 — Factor Lab all-horizon paired (forward-return + max-drawdown) columns (J-109)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** i_can_see_the_wealthy_future_forever_with_my_loved_ones
- **Iteration:** 52
- **Mode:** normal
- **Depth:** full
- **Frontend Present:** yes
- **Target journeys:** J-109
- **Required-still-passing journeys:** J-25, J-26, J-29, J-107, J-104, J-105, J-86, J-51, J-65, J-06 (CRITICAL), J-18 (CRITICAL), J-07 (CRITICAL)
- **Anti-goal reminders (verbatim from `docs/goal.md`):**
  - **Single source of truth.** Each of the six canonical scores (and the A–E bucket and setup status) MUST be computed exactly once by the scoring/regime engine and read identically by every page; the API and frontend MUST NOT recompute them. The same symbol's score MUST NOT differ between two views. *(critical)*
  - **No recompute in the read path.** Read endpoints MUST serve canonical values from the persisted immutable snapshot for the resolved as-of date; they MUST NOT recompute scores/returns/buckets per request. … The relocated **as-of-scoped evidence aggregate** … is likewise derived once per resolved as-of date over the snapshots dated ≤ D, persisted/cached, and read from storage — never recomputed per request and never including a snapshot dated > D. *(extends Single source of truth)*
  - **No lookahead.** Scoring for a snapshot dated D MUST use only price bars with date ≤ D; forward returns MUST use only bars with date > D. The walk-forward MUST be unit-tested to prove no future bar influences an as-of score. *(critical)*
  - **No magic numbers.** Every scoring weight, threshold, decision-rule cutoff, bucket edge, universe entry, and theme definition MUST come from the config file — no such literal in calculation code.
  - **Honest forward-test for partial windows.** The per-date forward-test scorecard and the VCP-vs-non-VCP breakdown MUST show NA/partial for horizons or cohorts lacking enough samples and MUST show sample size — never fabricate or extrapolate a return to fill a gap. *(extends No fabricated data)*
  - **No fabricated data.** On a data-provider failure the system MUST surface an explicit stale/unavailable state and MUST NOT synthesize prices or scores to force a green journey.
  - **Honest limitations surfaced.** … walk-forward evidence MUST be labelled as carrying survivorship bias (current-membership universe) so results are never overstated.
  - **No order/execution path.** No brokerage, order-placement, or capital-deployment code may exist or be reachable; Trendora is research-only. *(critical)*
  - **Exactly one date selector** (coherence invariant 5): the global as-of control drives every date-scoped page; the Research as-of toggle is a MODE, never a second/page-local date state. *(critical)*

## GOAL

The Factor Lab (`/research/factor-lab`) drops its single-horizon selector and shows every configured horizon (1/5/10/20/60d) at once as paired forward-return + max-drawdown columns on both the all-factors table and each factor's expandable decile sort — so a user sees the holdable top-decile edge and its downside risk across all horizons in one view, with no number recomputed.

## BACKGROUND

iter-51 closed the prior goal at GOAL_ACHIEVED (105/105 buildable journeys positive-evidenced). `docs/goal.md` was then extended (commit ab7de8c) with FOUR new buildable Must-haves J-109..J-112 — none has a `journey-history.json` entry yet, so per the iter-22 lesson the standing "every buildable Must-have positive-evidenced" gate is again unmet and the loop must CONTINUE building them. This is the first iteration of that new cluster.

It targets **J-109 only**, at **full** depth. J-109 is a presentation + read-surface change on the EXISTING `/research/factor-lab` route (no new page, no nav-skeleton change), but it touches the **OOM-sensitive cached-aggregate / streamed factor-lab read path** — the exact area of the iter-46/47/48 MemoryError regression cluster — and it crosses backend (the all-horizons EventStudyCache key extension + a paired max-drawdown aggregate in the SAME factor observation builders) and frontend (selector removal + paired-column render + per-horizon decile drill-down). That risk profile, the byte-identity tests beyond browser smoke, and the cache-schema change all mandate full depth. J-110/J-111/J-112 (the three new cross-sectional labs) are deferred to later iterations (one heavy lab per iter — see NOTES).

Evaluator feedback driving scope: iter-51 verdict GOAL_ACHIEVED + the goal.md extension. The next GOAL_ACHIEVED candidacy is only sound after J-109..J-112 all land green with a flushed-GREEN suite + COHERENCE-PASS + zero regression, so iter-52 is NOT a GOAL_ACHIEVED candidate and its flushed suite is non-load-bearing (still launched nohup-async per the iter-50 lesson).

## IN SCOPE

### Backend
- [ ] Extend the Factor Lab all-factors aggregate (`research.compute_factor_lab_all` and the per-factor `compute_factor_lab` / `_deciles` builders, `apps/backend/app/engine/research.py`) to surface, per `config.walk_forward.horizons` horizon, the cohort **mean realized forward return AND a paired mean max-drawdown** read VERBATIM from the stored `forward_returns` table (`realized_return` + the J-86 `max_drawdown`) — for the all-factors table the **top-decile (D10)** cohort, for the decile sort each **decile's** members. Decile membership per horizon is the existing per-horizon factor sort (independent per horizon) — recompute no decile boundary, no return, no max-drawdown (Single source / No recompute in the read path).
- [ ] Each horizon column MUST be **byte-identical** to today's single-horizon `compute_factor_lab(factor, horizon, …)` output for the same `(factor, horizon, decile)` — assert with a committed deep-equality test across as-of/all-history and zero-N (the recurring "byte-identical figures" property; pair the value-equality assertion with the count-coherence assertion below).
- [ ] Serve the all-horizons + paired-MDD shape from the SAME `GET /api/research/factor-lab` endpoint (`apps/backend/app/api/research.py`, the existing `all=true` path) with its derived-once `EventStudyCache` + `_dataset_version` aggregate **key EXTENDED to the all-horizons view** (so a pre-iter-52 cached row that lacks the new shape is a MISS and recomputed once WITH the paired-MDD columns — fold a schema token into the cache key per the iter-38/39/44 stale-cache discipline; unit-test against an ALREADY-POPULATED old-schema cache row, never a fresh compute). Reuse the EXISTING `event_study_cache` table — NO new `table=True` model.
- [ ] Keep the heavy read path **bounded** per J-105: one shared `yield_per`/column-projected streamed observation pass (no unbounded `select(...).all()` over `ForwardReturn` or `ScannerResult`); order `ScannerResult` reads by `(run_id, id)` (iter-48 byte-identity + no-temp-sort lesson). Probe the UNCACHED cold path (Factor Lab is intentionally uncached cold — iter-47/48) to confirm no MemoryError on the full live `forward_returns`.
- [ ] Rank-IC + downside risk-adjusted figures REMAIN, computed at `config.walk_forward.default_horizon` (= 20, a fixed config default, labelled with that horizon — no longer a user selector). Horizon set from `config.walk_forward.horizons` (no hardcoded `[1,5,10,20,60]` literal — `test_no_magic_numbers`).
- [ ] Extend the Research Samples cohort selector (`apps/backend/app/engine/samples.py` / `GET /api/research/samples`) so every displayed `N=` chip drills into the exact `(factor, horizon, decile)` cohort without a 4xx, total == published n (J-51/J-65 count-coherence) in both As-of and All-history. NA where the return is NA; low-sample deciles show NA + n.

### Frontend
- [ ] `/research/factor-lab` (`apps/frontend/app/research/factor-lab/page.tsx` + `apps/frontend/app/research/_labs.tsx`): REMOVE the single-horizon selector; render all horizons at once as paired (forward-return, max-drawdown) columns on the all-factors table; expand a factor row to reveal its decile sort with the same five forward-return + five paired max-drawdown columns + per-decile `n` chip + factor range.
- [ ] Columns client-side sortable NA-last under the J-48 view-transform contract (re-orders the rendered rows ONLY — recomputes/refetches nothing); colour-graded via the existing design tokens (no hardcoded hex).
- [ ] The As-of vs All-history toggle (J-32) only FILTERS the observation set — it reads the single global as-of, never a second/page-local date state (J-18); resolve sort/expand/`N=` controls by `aria-label`, not visible `text()` (iter-27/28/50 selector lesson). Default table sort stays descending (the iter-50 UT-03 "FAIL" was a test-plan expectation bug, not a defect — pre-clarify in the test plan).
- [ ] Each decile's `N=` chip opens `/research/samples` in a new tab carrying the exact `(factor, horizon, decile)` cohort + `?asof`; the survivorship-bias / descriptive-evidence labels persist.

### New user-facing capability
A user can compare every catalog factor's top-decile forward-return edge AND its paired downside (max-drawdown) at all five horizons in a single table, then expand any factor to see the full D1…D10 decile return/drawdown grid — without ever picking a horizon.

### New information displayed
Five paired max-drawdown columns beside the five forward-return columns on both the all-factors table (top-decile D10 cohort) and the per-factor decile sort (per-decile), at all `config.walk_forward.horizons` horizons.

### New user actions
Sort any of the new per-horizon forward-return / max-drawdown columns (NA-last); expand a factor row to its all-horizon decile sort; click a decile's per-horizon `N=` chip to drill into the exact cohort. The horizon `<select>` is removed.

### UI surface changes
`/research/factor-lab` only — the all-factors table gains paired MDD columns at all horizons; the expandable decile sort gains all-horizon paired columns; the horizon selector disappears; the Rank-IC / risk-adjusted figures are relabelled with the fixed `default_horizon`.

### Product surface delta
The Factor Lab becomes an all-horizon, risk-aware factor screen: edge and downside are visible together across every horizon at a glance, with no horizon-picking step and no recomputed number.

### Blueprint conformance
Lands on the EXISTING Research home → `/research/factor-lab` route (the J-107 all-factors view). No new page, no new nav section, no nav-skeleton change → no `blueprint.reapproval-requested` filed. Information Architecture unchanged.

### Data-contract additions
No new canonical value. The displayed figures are aggregates computed by the SAME `research:compute_factor_lab` / `_deciles` / `_rank_ic` / `_risk_adjusted` builders over already-registered stored values (`forward_returns.realized_return` and the J-86 `forward_returns.max_drawdown`), served by the SAME `GET /api/research/factor-lab` endpoint. Registered this iteration as an **additive amendment to the existing "Factor-Lab analytics" Data Contract row** in `blueprint.md` (J-109 [TARGET iter-52]) — no second computing module, no second endpoint, no second way to compute/fetch any contract value.

## OUT OF SCOPE

- J-110 (`/research/regime-lab`), J-111 (`/research/phase-severity-lab`), J-112 (`/research/regime-phase-factor`) — deferred to iter-53/54/55 (one heavy cross-sectional lab per iter).
- Any change to the canonical factor decile / rank-IC / risk-adjusted **math** — J-109 re-presents existing outputs across horizons; the per-regime `by_regime` slice stays a derived-once canonical value (already unrendered in this view since J-107).
- Any new `table=True` model, new endpoint, new served field on `/api/stocks|themes|sectors`, or any second date state.
- Re-triggering the J-85 `kind:rebuild` (destructive; the data is correct).

## DEFINITION OF DONE

- [ ] J-109 passes via browser-qa-agent on a freshly-warmed, single-fetch-at-a-time backend (Playwright fallback pre-planned).
- [ ] Required-still-passing journeys (J-25, J-26, J-29, J-107, J-104, J-105, J-86, J-51, J-65, J-06, J-18, J-07) remain green (deterministic replay + live where rendered).
- [ ] No anti-goal violation introduced (byte-identity preserves Single source / No recompute; horizons + default_horizon config-sourced for No magic numbers; NA-honest forward-test; no order/execution path; the As-of toggle stays a mode — exactly one date selector).
- [ ] Unit/integration tests pass; full pytest suite launched nohup-async via the pump (flush `0 failed, EXIT 0` is owed before any GOAL_ACHIEVED candidacy, NON-load-bearing this iter — re-run any isolated `test_warmup.py` / `test_watchlist_persistence.py` / `test_data_manager_jobs_pipeline.py` E/F before attributing).
- [ ] Dev handoff written at `docs/handoffs/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-52-dev.md`.

## TESTING REQUIREMENTS

- **Browser (J-109):** on a quiet warmed backend — (1) the all-factors table renders the 11 catalog factors with five forward-return AND five paired max-drawdown columns at all horizons (no "Loading…"/"Backend unavailable"/skeleton frame; md5sum the evidence dir first — iter-40 lesson); (2) expand a factor → its D1…D10 decile sort shows the same all-horizon paired columns + per-decile `n`; (3) sort a per-horizon column → byte-DISTINCT before/after frames (md5sum the pair, NA sinks last); (4) a decile `N=` chip → `/research/samples` opens the exact `(factor, horizon, decile)` cohort, Total observations == chip n; (5) toggle As-of vs All-history → N values change globally via the single top-bar date (0 native `input[type=date]` — J-18). Resolve all controls by `aria-label`.
- **Unit/integration:** deep-equality byte-identity of each `(factor, horizon, decile)` all-horizons figure vs the existing single-horizon `compute_factor_lab` output (as-of, all-history, zero-N); the extended EventStudyCache key produces a MISS-then-populate against an ALREADY-POPULATED old-schema cache row (not a fresh compute); the bounded/streamed read path serves the full live dataset without MemoryError (cold uncached probe); `test_no_magic_numbers` + `test_db.py::test_create_all_produces_expected_tables` (expected-tables guard UNCHANGED — no new table); samples count-coherence for the new `(factor, horizon, decile)` cohort.
- **Error cases:** a horizon with insufficient post-D bars → NA forward-return AND NA max-drawdown (never fabricated); a low-sample decile → NA + n; an out-of-vocabulary samples cohort request → honest 4xx, never a fabricated row; the cold uncached factor-lab fetch must not OOM on the ~3M-row live `forward_returns`.

## NOTES

- **iter-22 lesson (why this iter exists):** after a prior GOAL_ACHIEVED, "every journey in journey-history is green" is NOT sufficient when goal.md queued new buildable Must-haves (here J-109..J-112) with no journey-history entry — they are `unknown` Must-haves that must drive CONTINUE.
- **iter-46/47/48 OOM lessons (load-bearing for this iter):** the factor-lab read path is the OOM-sensitive UNCACHED-cold site. Keep the J-105 streaming/column-projection (NO unbounded `select(...).all()` over `ForwardReturn` OR `ScannerResult`); order `ScannerResult` reads by `(run_id, id)` (rides `ix_scanner_results_run_id`, byte-identical order, no temp-sort spill — iter-48). Probe the lab COLD on a quiet backend; a warm cache masks a sibling cold-miss OOM (iter-47). Disk is ~253G free per iter-50, so disk-full is no longer the acute risk, but keep the `(run_id, id)` ordering.
- **iter-38/39/44 cache-schema lesson:** the all-horizons + paired-MDD shape is an additive change to a CACHED payload — fold a schema token into the EventStudyCache key (or it stays served field-less on every pre-iter-52 cached row); unit-test against an already-populated old-schema row, never a fresh compute that masks the staleness.
- **iter-23/24/32 guard lesson:** J-109 deliberately serves on the EXISTING `/api/research/factor-lab` (additive `all=true` shape, reused cache table) and adds NO field to `/api/stocks|themes|sectors|data`, so the `served == engine_output` / exact-`set(payload)==` blanket guards are not in play; still grep `apps/backend/tests` for any factor-lab shape assertion before claiming the suite green.
- **iter-27/28/50 selector + sort-default lesson:** resolve sortable/expand/`N=` controls by `aria-label`, not visible `text()` (labels live in nested `<span>`s); the all-factors table defaults DESCENDING, so a "sort does not reorder" browser-QA FAIL on the first click is a test-plan expectation artifact, not a regression — confirm the sort code path is the J-48 comparator before recording any regression.
- **iter-39/40/42/43 render-evidence lesson:** this is `Frontend Present: yes`, so browser-QA runs in-iteration — PLAN the Playwright fallback UP FRONT (Chrome MCP CDP has emptied the evidence dir on iters 38/39/40/42); md5sum the dir first; reject byte-identical "before/after" sort pairs and skeleton/"Backend unavailable" frames.
- **iter-45/48 contention lesson:** run heavy-lab browser-QA on a freshly-restarted, warmed, single-fetch-at-a-time backend; NEVER run the full pytest suite concurrently with the heavy-lab probes (its RAM pressure exacerbated the factor-lab OOM). Allow ~50-120s for the factor-lab cold compute before the first cache hit.
- **iter-50 lesson:** launch the full suite nohup-async via the pump so iter-53's evaluation can confirm the flushed `0 failed, EXIT 0`; do NOT block the evaluator on the in-flight suite.
- **GOAL_ACHIEVED gate:** iter-52 is NOT a candidate — J-110/J-111/J-112 remain unbuilt. Recommended forward decomposition: iter-53 = J-110 (Regime Lab), iter-54 = J-111 (Phase & Severity Lab), iter-55 = J-112 (Regime × Phase × Factor) — each FULL (a new study + endpoint + EventStudyCache cohort kind + samples cohort kind + a J-105 streamed cross-sectional observation builder; each a new tile + lazy sub-route ADDITIVELY UNDER the existing `/research` hub — a new page within an existing nav section, no top-level-nav change, no reapproval marker). J-22/J-23/J-24 stay honestly blocked-NA (non-vetoing per goal.md:105-108).
