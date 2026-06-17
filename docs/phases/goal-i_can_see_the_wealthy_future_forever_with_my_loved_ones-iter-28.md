# Goal Iteration 28 — Finish J-86: graduate the max-drawdown colour scale + confirm the MDD/forward-return column sort

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** i_can_see_the_wealthy_future_forever_with_my_loved_ones
- **Iteration:** 28
- **Mode:** next
- **Depth:** lean
- **Frontend Present:** yes
- **Target journeys:** J-86
- **Required-still-passing journeys:** J-48, J-75, J-81, J-06, J-05, J-18, J-70, J-74
- **Anti-goal reminders (verbatim from `docs/goal.md`):**
  - **Single source of truth** — six scores + bucket + setup computed once; read identically everywhere (J-06). A max-drawdown reads identically on a ticker's leaderboard row, its Stock-Detail panel, and Backtest for the same date + horizon.
  - **No recompute in the read path** — reads serve the persisted-snapshot value; the view never computes a drawdown client-side. The colour/sort are pure view transforms over the already-served `max_drawdown` figure.
  - **No magic numbers** — weights/thresholds/edges/universe/themes/providers/chunking/startup/range-presets/glossary and design tokens come from `config.yaml` / the design-token system, never hardcoded hex. The graduated drawdown colour MUST be expressed with design tokens (opacity steps of the existing `--neg` token), NOT new hardcoded hex.
  - **View transforms & drill-downs never recompute (J-48)** — leaderboard sorting re-orders the rendered list ONLY; each row's served values (including the five forward returns and five max-drawdowns) read exactly as served; the `#` column restores the scanner's stored rank.
  - **Exactly one date selector** — the global as-of control drives every date-scoped page; this iteration introduces NO date state and does not touch the as-of provider/switcher/calendar.
  - **No fabricated data; honest forward-test for partial windows** — max-drawdown is NA wherever the realized return is NA (insufficient post-D bars); NA must never be coloured as a real drawdown.

## GOAL

On every leaderboard (`/stocks`, `/themes`, `/sectors`) and the Stock-Detail panel, each row's five max-drawdown figures are colour-graded by magnitude (a deeper drawdown reads visibly more severe) using design tokens only, and all five MDD columns — plus the existing five forward-return columns — sort correctly (NA last) when their header is clicked.

## BACKGROUND

J-86 is the LONE remaining non-passing buildable journey (journey-history: 70 passing + 12 already_passing + J-86 `partial`; J-22/J-23/J-24 stay honestly blocked-NA, non-vetoing). Its data-correctness legs all passed in iter-27 (five MDD columns ≤ 0, NA-honest, byte-identical to Backtest, single-sourced from the stored `forward_returns.max_drawdown` via the canonical `forward_testing.max_drawdown` / `_leadership_returns`; full backend suite GREEN at 878 passed). Only two UI acceptance sub-legs failed:

1. **Colour grading is flat (genuine, source-confirmed defect).** `apps/frontend/components/forward-return.tsx` `mddClass()` returns a single flat `text-neg` for every negative value (lines 66–70), so a -1% and a -40% drawdown render the same red — goal.md J-86 step 1 explicitly requires "colour-graded by magnitude".
2. **MDD column sort "no-op" (most likely a selector false-negative, NOT a code defect).** The iter-27 browser-QA drove `//th//button[text()='5d']`, but the `SortHeader` button's label lives in a nested `<span>` (`stocks/page.tsx:951`) so XPath `text()` matches nothing. The sort code path is byte-unchanged from what passed in iter-20 (TC-09 /stocks) and iter-23 (themes/sectors): `comparatorFor` already handles `mdd_*` keys with NA-last semantics (`stocks/page.tsx:96–113`), and the button already exposes `aria-label="Sort by <label>…"` (line 948) and a `data-testid="sort-indicator"` (lines 954/956). This iteration must RE-VERIFY the sort with correct (aria-label) selectors and only fix it if genuinely broken.

Depth is **lean**: frontend-only, no backend change expected (the backend is done and the full suite is GREEN), low risk, one shared helper + a QA re-verification. After both legs are green with COHERENCE-PASS and the suite still GREEN, every buildable Must-have is passing and the next evaluation is a GOAL_ACHIEVED candidate.

**Lessons applied (from this session's ledger):**
- **iter-27:** A browser-QA "sort does not reorder" FAIL can be a selector false-negative — resolve sort buttons by their `aria-label` ("Sort by 5d", "Sort by 5d MDD"), never visible `text()`; and before calling a sort regression, check the git diff (here `onSort`/`SortHeader`/`comparatorFor`/the `sorted` memo are byte-unchanged, so a new sort failure is far more likely a test artifact). Colour-grading claims must be checked against the `*Class()` helper source, not a screenshot.
- **iter-16 / iter-18:** A static `className` map's correctness (e.g. the new graduated drawdown buckets) is provable at source level when the committed seed doesn't exercise every bucket — verify the unexercised magnitude bands by reading the helper, and DOM/computed-CSS extraction (live `rgb` per cell) may substitute for a degraded screenshot only when it carries render-only signal.
- **iter-70 / iter-74 token discipline:** colour scales are defined ONCE from the design-token system; no per-cell / per-magnitude hardcoded hex (anti-goal 10). Use opacity steps of the existing `--neg` token.
- **Evidence hygiene (iters 3/7/10/15/18/27):** md5sum the evidence dir FIRST; the MDD cells sit to the RIGHT of the forward-return columns — capture them full-viewport-wide and VIEW the pixels; reject blank / coverage-table / byte-shared frames.

## IN SCOPE

### Backend
- [ ] None. No backend change is expected. The stored `forward_returns.max_drawdown` value, its computation in `forward_testing.max_drawdown`, and the `_leadership_returns` builder are all done and suite-green — do NOT touch them.

### Frontend
- [ ] **Graduate `mddClass()` by magnitude (the single fix).** In `apps/frontend/components/forward-return.tsx`, replace the flat `text-neg`-for-all-negatives logic with a magnitude-graded scale that maps a more-negative drawdown to a visibly more-severe colour, using **design tokens only** — opacity steps of the existing `--neg` token (e.g. Tailwind utilities `text-neg/40`, `text-neg/60`, `text-neg/80`, `text-neg` from shallowest to deepest drawdown). Define the magnitude thresholds as named module constants (do NOT inline bare numeric literals beyond what the helper structurally needs; these are presentation tokens, but keep them named/commented). Exactly `0` and NA stay muted (`text-text-muted`) — never coloured as a real drawdown (honest partial-window discipline). NO new hex anywhere.
- [ ] Because `/stocks`, `/stocks/[ticker]`, `/themes`, and `/sectors` all import `mddClass` from this one shared module (confirmed: `stocks/page.tsx:10`, `stocks/[ticker]/page.tsx:10`, `themes/page.tsx:10`, `sectors/page.tsx:12`), the graduated colour flows to every MDD-displaying surface from this single edit — keep it that way (single source of truth; do NOT add a competing per-page colour helper).
- [ ] **Sort: re-verify, fix only if genuinely broken.** Do NOT pre-emptively rewrite the sort. `comparatorFor` (`stocks/page.tsx:96–113`) already handles `mdd_*` keys with NA-last in both directions; the `SortHeader` button already carries the `aria-label` and `data-testid="sort-indicator"`. Only if the aria-label-driven re-verification proves an actual regression should the developer touch `onSort`/`SortHeader`/`comparatorFor`/the `sorted` memo — and then minimally, preserving the J-48 contract (re-order only, never recompute; `#` restores the stored rank).

### New user-facing capability
The user can visually distinguish a shallow drawdown from a severe one at a glance on every leaderboard and the Stock-Detail panel, and can sort each leaderboard by any of the five max-drawdown columns (and the five forward-return columns) with NA values sorted last.

### New information displayed
No new value — the same already-served `max_drawdown` figures, now colour-graded by magnitude rather than a flat single red.

### New user actions
Clicking any of the five MDD column headers (or the five forward-return headers) sorts the leaderboard by that column. (The headers/sort already exist; this iteration only ensures they are visibly working and verified.)

### UI surface changes
`/stocks`, `/themes`, `/sectors` leaderboards and the `/stocks/[ticker]` Stock-Detail forward-return panel — the MDD figures change colour intensity by magnitude. No layout change, no new column, no new page.

### Product surface delta
The risk read on every leaderboard becomes legible at a glance (severity encoded by colour intensity), completing J-86's UI acceptance. No data, no endpoint, no navigation changes.

### Blueprint conformance
No new surfaces. All four edited surfaces already live on their existing Information-Architecture homes (Stocks `/stocks`, Stock Detail `/stocks/[ticker]`, Themes `/themes`, Sectors `/sectors`), and the J-86 rows are already registered in `blueprint.md`'s IA and Data Contract (the "Max-drawdown per (run, symbol, horizon)" row + the Per-stock-forward-returns row's J-86 annotation, both registered at iter-27). The graduated colour is a presentation property of the already-registered value — no blueprint edit required.

### Data-contract additions
None. The `max_drawdown` value is already registered (canonical computing module `forward_testing.max_drawdown`; served on `GET /api/stocks`, `GET /api/stocks/{ticker}`, `GET /api/themes`, `GET /api/sectors`, and the Backtest / Research aggregates). This iteration introduces no new value, no second computation, and no new endpoint — it only re-formats the already-served figure.

## OUT OF SCOPE

- Any backend change (`forward_testing.py`, `snapshot_serving.py`, `research.py`, `db.py`, models, endpoints, config) — the data legs and the full suite are already GREEN; touching them risks a needless suite re-run and the recurring "additive field trips a byte-equality guard" trap.
- The forward-return (`returnClass` / `fmtPct`) colour and formatting — unchanged.
- The coherence advisory WARN (three local `MaxDrawdownCell` wrappers using "NA" text vs the shared "—" em dash) — a presentational nicety, explicitly deferred; do NOT consolidate the wrappers this iteration (it would widen the diff beyond the lean scope). The colour fix flows through them already because they all call the shared `mddClass`.
- The as-of provider / switcher / calendar (`asof-provider.tsx`, `asof-switcher.tsx`, `asof-calendar.tsx`) — untouched (J-18 invariant).
- J-22 / J-23 / J-24 — data-walled, non-vetoing; no work.

## DEFINITION OF DONE

- [ ] Target journey J-86 passes via browser-qa-agent: on `/stocks` (and verified on `/themes`, `/sectors`, and the `/stocks/[ticker]` panel at a historical as-of) the five max-drawdown figures are colour-graded by magnitude (a deeper drawdown is visibly more severe; 0 / NA muted), using design tokens only.
- [ ] All five MDD columns sort (NA last) when their header is clicked, AND the five forward-return columns still sort — verified by resolving the `SortHeader` button via its `aria-label` ("Sort by 5d MDD", "Sort by 5d", etc.) and asserting the rendered row order changes and the `data-testid="sort-indicator"` flips.
- [ ] Required-still-passing journeys remain green: J-48 (forward-return + general column sort unregressed), J-75 (`/stocks` + detail forward returns), J-81 (`/themes` + `/sectors` forward + MDD columns), J-06 (a ticker's MDD reads identically on its leaderboard row and Stock-Detail panel for the same date), J-05, J-18 (no date-state change — as-of components not in the diff), J-70 / J-74 (heatmap token discipline unaffected).
- [ ] No anti-goal violation introduced — in particular NO new hardcoded hex in `mddClass` (grep the diff for `#` hex literals; design tokens / opacity utilities only) and NO client-side drawdown computation.
- [ ] `tsc --noEmit` is clean (the frontend gate — ESLint is genuinely not installed per the iter-1 lesson; do NOT add an `npm run lint` DoD line).
- [ ] No backend diff (`git diff --stat HEAD -- apps/backend` empty); the full backend suite is NOT re-run for a frontend-only change (it was GREEN at iter-27 and no backend file is touched).
- [ ] Dev handoff written at `docs/handoffs/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-28-dev.md`.

## TESTING REQUIREMENTS

- **Browser (by ID):**
  - **J-86** — at a historical as-of date D, on `/stocks`: confirm the five MDD figures render with magnitude-graded colour (capture full-viewport-wide so the MDD cells, which sit to the RIGHT of the forward-return columns, are visible; VIEW the pixels). Then click the "5d MDD" header (resolved by `aria-label`, e.g. `button[aria-label^="Sort by 5d MDD"]`) and assert the row order changes and the sort indicator appears; repeat for at least the 1d and 60d MDD columns; confirm NA rows sort last. Confirm the same five MDD values on a ticker's Stock-Detail panel match that ticker's leaderboard row (J-06). Spot-check `/themes` and `/sectors` show the graduated MDD columns and sort.
  - **J-48 / J-75** — re-verify the forward-return columns still sort (resolve by `aria-label="Sort by 5d"`, NOT visible text) — guard against a false "regression" from the iter-27 selector artifact.
  - Smoke: J-81 (themes/sectors columns intact), J-18 (no page-local date control appears; the single global as-of still drives the date).
- **Unit/integration:** no new backend tests (no backend change). Frontend gate is `tsc --noEmit` clean. If the developer adds a tiny frontend unit test for the graduated `mddClass` magnitude buckets, that is welcome but not required.
- **Error cases:** `mddClass(null)` / `mddClass(undefined)` / `mddClass(0)` must all return the muted token (`text-text-muted`), never a graded red — NA and exactly-flat are not "real drawdowns" (verify by reading the helper; the committed seed may not exercise every magnitude band, so corroborate the unexercised buckets at source per the iter-16/18 lesson).

## NOTES

- This is the final consolidation for the J-83..J-86 extension. After J-86 flips to `passing` with COHERENCE-PASS and no regression, every buildable Must-have is green and J-22/J-23/J-24 remain honestly blocked-NA (data-walled, non-vetoing per `goal.md` lines 2182–2192) — the evaluator should then weigh GOAL_ACHIEVED.
- The decisive checks here are STATIC and CHEAP: (1) grep the `mddClass` diff for hardcoded hex (must be none — design tokens / opacity utilities only); (2) confirm `comparatorFor` / `onSort` / `SortHeader` / the `sorted` memo are byte-unchanged unless a real sort regression is proven; (3) confirm no `apps/backend` file and no as-of component is in the diff. A genuinely magnitude-graded `mddClass` plus an aria-label-driven sort re-verification closes J-86.
- Evidence hygiene for QA: `md5sum` the evidence dir FIRST (iter-27 had `-cors-block` and byte-shared frames); resolve sort buttons by `aria-label`, never `text()`; capture the colour-graded MDD cells full-viewport-wide and VIEW each capture — a blank / coverage-table / byte-recycled frame is a rejected capture, not evidence.
