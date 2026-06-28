# Goal Iteration 56 — Research hub reorder (J-113) + de-interleave the four all-horizon lab columns (J-114)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** i_can_see_the_wealthy_future_forever_with_my_loved_ones
- **Iteration:** 56
- **Mode:** normal
- **Depth:** lean
- **Frontend Present:** yes
- **Target journeys:** J-113, J-114
- **Required-still-passing journeys:** J-109, J-110, J-111, J-112, J-107, J-104, J-51, J-48, J-50, J-06, J-18, J-07
- **Anti-goal reminders:**
  - **Single source of truth.** Each of the six canonical scores (and the A–E bucket and setup status) MUST be computed exactly once by the scoring/regime engine and read identically by every page; the API and frontend MUST NOT recompute them. The same symbol's score MUST NOT differ between two views. *(critical)*
  - **No recompute in the read path.** Read endpoints MUST serve canonical values from the persisted immutable snapshot for the resolved as-of date; they MUST NOT recompute scores/returns/buckets per request.
  - **No magic numbers.** Every scoring weight, threshold, decision-rule cutoff, bucket edge, universe entry, and theme definition MUST come from the config file — no such literal in calculation code.
  - **Honest forward-test for partial windows.** The per-date forward-test scorecard and the VCP-vs-non-VCP breakdown MUST show NA/partial for horizons or cohorts lacking enough samples and MUST show sample size — never fabricate or extrapolate a return to fill a gap. *(extends No fabricated data)*
  - **Risk-Off must gate Actionable.** When the regime is Risk-Off, the scanner MUST mark zero stocks "Actionable" (watchlist-only). *(critical)*
  - **No order/execution path.** No brokerage, order-placement, or capital-deployment code may exist or be reachable; Trendora is research-only. *(critical)*

## GOAL

Reorder the `/research` hub's lab cards so the regime/phase/factor labs lead the reading order (J-113), and de-interleave the four all-horizon Research labs' per-horizon columns to **all forward-return columns first, then all max-drawdown columns** to match the leaderboard order (J-114) — two pure frontend presentation/information-architecture changes with byte-identical figures.

## BACKGROUND

This is an in-place resume after the iter-55 GOAL_ACHIEVED; `docs/goal.md` was extended with two new Must-haves (J-113, J-114), and neither has a journey-history entry — so per the **iter-22 lesson** the every-buildable-Must-have gate is again unmet and the loop must CONTINUE. Both are the LAST two unbuilt buildable Must-haves, both explicitly **NOT data-dependent** (goal.md:2495) and both **pure frontend presentation / view-transform** changes over already-served values (zero backend diff, every figure byte-identical) — hence **lean** depth. After they land green on live evidence the next evaluation is a sound GOAL_ACHIEVED candidate (J-22/J-23/J-24 stay honestly blocked-NA, non-vetoing per goal.md:105-109).

## IN SCOPE

### Backend
- [ ] **None — zero backend diff.** Every figure stays byte-identical and is read from its existing canonical source (`forward_returns.realized_return` + the J-86 `forward_returns.max_drawdown`, served via the already-built lab endpoints). The iter-55 flushed-GREEN pytest suite (1210 passed, 4 skipped, 0 failed) remains the standing gate for the byte-unchanged backend.

### Frontend
- [ ] **J-113 — Research hub reading-order reorder.** In `apps/frontend/app/research/page.tsx`, reorder the `LABS` array (the single ordered source the `grid-cols-1 sm:grid-cols-2 xl:grid-cols-3` `data-testid="research-hub"` grid maps over) to exactly: **Factor Lab → Regime Lab → Market Phase & Severity Lab → Regime × Phase × Factor → Regime × Setup × Pattern → Severity-velocity × Regime → Multi-factor combination → Setup & Pattern event study → Recovery-Turn Edge → Downtrend Opportunity.** No lab added or removed (all ten remain reachable + deep-linkable — no orphan surface, no duplicate home, no canonical-home move); every route, the `?asof` href-stamping (`useAsOfHref` / J-50), and the per-lab lazy-load (J-104) behaviour are unchanged. Recommended: extract the ordered list into a pure lib module (e.g. `lib/research-labs.ts`) so the order is unit-assertable under the existing node TS-strip test convention, with `page.tsx` importing it.
- [ ] **J-114 — de-interleave per-horizon columns in the four all-horizon lab tables.** In `apps/frontend/app/research/_labs.tsx`, change the per-horizon column rendering in **all four** all-horizon labs — Factor Lab all-factors table **and** its expandable per-factor decile grid (J-109), Regime Lab by-label summary **and** regime-score-decile table (J-110), Market Phase & Severity Lab by-phase-label **and** severity-score-decile table (J-111), and the Regime × Phase × Factor combination table (J-112) — so that **all** `config.walk_forward.horizons` **forward-return** columns render first (ascending 1/5/10/20/60d), then **all** max-drawdown columns in the same horizon order — never interleaved (no `Fwd → MDD → Fwd` alternation). The header cells, the body cells, **and** the client-side sort-column mapping (the `FactorSortHeader`/`comparatorFor` col keys `fwd:${h}` / `mdd:${h}` and each lab's equivalent) must all follow the new grouped order while staying byte-identical in value. Colour-grading, the NA-honest cell predicate (`low_sample` OR `n === 0` OR value `null`), the As-of vs All-history toggle (J-32), the J-112 30-rows-per-page pagination, and the `N=` chip drill-downs are unchanged. The horizon set stays from `config.walk_forward.horizons` (no hardcoded `[1,5,10,20,60]`). Recommended: a single shared pure helper that, given the config horizons, returns the grouped column descriptors (all-fwd-then-all-mdd) used by all four tables, plus a node TS-strip test asserting all forward-return descriptors precede all max-drawdown descriptors.

### New user-facing capability
None new — the same labs and the same figures, presented in a clearer order.

### New information displayed
Nothing new (figures are byte-identical). Only the ordering of existing hub cards and existing lab columns changes.

### New user actions
None.

### UI surface changes
The `/research` hub card order; the column order on the four all-horizon lab tables (and the Factor Lab expandable decile grid).

### Product surface delta
The Research hub reads regime/phase/factor-first (the analysis themes the operator most often opens lead), and the four labs' columns match the `/stocks` / `/themes` / `/sectors` leaderboard grouping (J-86 — all forward-return columns, then all max-drawdown columns), making the labs consistent with the leaderboards and easier to scan.

### Blueprint conformance
No new surfaces. All ten labs keep their existing `/research` Information-Architecture homes; this is a pure reading-order (J-113) + column-order (J-114) presentation change. A SESSION EXTENSION note for J-113/J-114 is added to `blueprint.md` (additive documentation only — no nav-skeleton change, so no `blueprint.reapproval-requested` is owed).

### Data-contract additions
**None.** Every displayed figure is byte-identical and read from its already-registered canonical source (`forward_returns.realized_return` + the J-86 `forward_returns.max_drawdown`, served via the existing `/api/research/factor-lab`, `/api/research/regime-lab`, `/api/research/phase-severity-lab`, `/api/research/regime-phase-factor` endpoints). No new value, no new endpoint, no new computation, no second way to fetch any value already in the Data Contract.

## OUT OF SCOPE

- Any backend change (engine / API / config / db) — figures stay byte-identical; backend diff MUST be empty.
- The Stock-Detail per-horizon card grid, the `/backtest` evidence aggregates, and the Research event-study / Regime × Setup × Pattern tables — explicitly unchanged per J-114.
- Adding, removing, or renaming any lab or route; any nav-skeleton / top-level-section change; any move of a feature's canonical home.
- Any change to colour-grading, NA-honesty, the As-of toggle, pagination, the rank-IC / risk-adjusted columns, or the `N=` Research-Samples drill-downs (their counts must stay coherent).
- Re-sorting or re-grouping the actual data — this is a presentation/view-transform only; recompute nothing, refetch nothing.

## DEFINITION OF DONE

- [ ] Target journeys J-113, J-114 pass via browser-qa-agent on live evidence
- [ ] Required-still-passing journeys remain green (especially J-109/J-110/J-111/J-112 render byte-identical figures; J-48 sort still reorders; J-104 all ten tiles reachable; J-51 N= chips stay count-coherent)
- [ ] No anti-goal violation introduced (figures byte-identical; single source; no recompute; no magic number; NA-honesty preserved; no order/execution path)
- [ ] Committed frontend tests assert (a) the hub card order [J-113] inside the `research-hub` container and (b) all-forward-return-headers-before-all-max-drawdown-headers on each of the four labs' tables [J-114]; they pass under the existing node TS-strip convention (`node lib/<name>.test.ts`)
- [ ] Backend pytest suite unchanged and green (zero backend diff; the iter-55 1210-passed flush is the standing gate). Launch the full suite nohup-async so the next iteration's GOAL_ACHIEVED candidacy can confirm the flushed `0 failed, EXIT 0` line.
- [ ] Dev handoff written at `docs/handoffs/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-56-dev.md`

## TESTING REQUIREMENTS

- **Browser (load-bearing):**
  - **J-113** — visit `/research`; assert the `research-lab-link-*` order inside `data-testid="research-hub"` is exactly Factor Lab → Regime Lab → Phase & Severity → Regime × Phase × Factor → Regime × Setup × Pattern → Severity-velocity → Multi-factor combination → event study → Recovery-Turn → Downtrend; confirm every lab is still reachable + deep-linkable with `?asof` stamped on its href.
  - **J-114** — on EACH of the four labs (`/research/factor-lab`, `/research/regime-lab`, `/research/phase-severity-lab`, `/research/regime-phase-factor`): the header row shows all `Fwd Xd` columns first, then all `MDD Xd` columns (no interleave); expand a Factor Lab row → the decile grid uses the same grouped order; a sort on a forward-return column AND on a max-drawdown column still reorders the rows.
- **Required-still-passing live smoke:** J-109/J-110/J-111/J-112 (each lab still renders real, byte-identical figures — same numbers as iter-52/53/54/55, just re-columned), J-104 (all ten hub tiles present and each opens its lazy route), J-48 (column sort reorders the view), J-50 (`?asof` survives hub → lab navigation), J-06 / J-18 / J-07 (CRITICAL).
- **Unit/integration:** the two committed order tests above. Additionally assert that at least one forward-return column and one max-drawdown column remain client-side sortable (the `comparatorFor` / `FactorSortHeader` col-key mapping survives the reorder, NA-last in both directions).
- **Error cases:** a horizon whose forward return is NA still shows its max-drawdown NA too (no fabricated fill); low-sample / empty deciles still show NA + n. The reorder must not turn any honest NA into a fabricated 0.

## NOTES

- **iter-22 lesson (applies — in-place resume):** J-113/J-114 are queued buildable Must-haves with no journey-history entry; they drive CONTINUE, not GOAL_ACHIEVED, until built. After both land green, the next evaluation is a sound GOAL_ACHIEVED candidate; J-22/J-23/J-24 stay blocked-NA, NON-VETOING per goal.md:105-109.
- **iter-27 / iter-28b lesson (applies directly — J-114 re-arranges sortable columns):** browser-QA MUST resolve sort-header buttons by `aria-label` (e.g. "Sort by Fwd 5d" / "Sort by MDD 5d"), NEVER by visible `text()` — the `SortHeader` label lives in a nested `<span>`, so an XPath `text()` match resolves nothing and yields a false "sort broke" FAIL. Before recording any sort regression, confirm the `comparatorFor`/`onSort`/sorted-memo math is value-unchanged (J-114 only re-orders WHICH columns are emitted, not the comparator).
- **iter-40 lesson (applies directly — both journeys are order/differential changes):** `md5sum` the before/after frames; a byte-identical before/after pair proves nothing. Capture a byte-DISTINCT interleaved-vs-grouped header frame for J-114 and a byte-distinct hub-order frame for J-113 (or compare against a prior iteration's captured order).
- **iter-38/39/40/43 lesson:** Chrome MCP CDP has repeatedly emptied the evidence dir on this host — PLAN the Playwright fallback UP FRONT and `md5sum` the evidence dir FIRST, before any live render.
- **iter-52 lesson:** keep BOTH servers up THROUGH the dedicated browser-qa-agent step (it SKIPPED on a torn-down frontend in iter-52); cross-check the QA report's browser section AND the `-evidence/` dir before concluding "no live evidence."
- **iter-50 lesson:** even though there is zero backend diff, launch the full pytest suite nohup-async so the next iteration's GOAL_ACHIEVED candidacy can confirm the flushed `0 failed, EXIT 0` line; it stays byte-identical green (no backend change).
- **iter-53/54/55 lesson:** the auditor step has silently not run for three consecutive iters and lean depth does not dispatch the auditor — so the goal-evaluator must perform the substantive skeptical checks directly here: confirm zero backend diff (`git diff` over `apps/backend`/`scripts`/`config*.yaml` empty), the four labs' figures byte-identical to iter-52/53/54/55, no new endpoint/value/computation, and the J-48 sort survives. (Owner should fix the auditor dispatch in `run-goal.sh` before any future resume.)
- **Frontend test convention:** no test framework is installed in `apps/frontend`; committed tests run via Node TS type-stripping (`node lib/<name>.test.ts`, per `lib/membership-timeline-view.test.ts`). Extract the ordered hub list (J-113) and the grouped per-horizon column descriptor (J-114) into pure `lib/` modules so the order is unit-assertable in that convention, with `page.tsx` / `_labs.tsx` importing them.
- Start both servers via `./scripts/dev.sh` (host-aware base, J-108) before the browser-QA step.
