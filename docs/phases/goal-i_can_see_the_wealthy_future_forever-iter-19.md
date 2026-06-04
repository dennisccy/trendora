# Goal Iteration 19 — Research point-in-time toggle (As-of ⟷ All-history) — the last buildable journey

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** i_can_see_the_wealthy_future_forever
- **Iteration:** 19
- **Mode:** next
- **Depth:** full
- **Frontend Present:** yes
- **Target journeys:** J-32
- **Required-still-passing journeys:** J-18 (principal anti-goal risk), J-25, J-26, J-27, J-29, J-30 (the five lab values — must render unchanged in the default All-history mode AND correctly re-point in As-of mode), J-15 (read path / no wasted refetch), J-31 (synthesis travel intact). J-06/J-07 carried structurally (no scoring/snapshot/DB change this iter).
- **Anti-goal reminders (verbatim from `docs/goal.md`):**
  - **Exactly one date selector.** "The frontend MUST NOT maintain a second, independent date state; every date-scoped page (including Backtest) reads the single global as-of control. The Stock-Detail chart **timeframe selector** (1D/1h/15m/5m) is NOT a date control — it changes bar granularity only, bounded by the resolved as-of date. **The Research all-history / as-of-date toggle is likewise a MODE, NOT a date control — its as-of mode reads the same single global as-of control (no second date state).** *(extends Single source of truth)*" — **THE principal risk this iteration.**
  - **Research lab is read-only, honest & not predictive.** "Every Factor-Lab and event-study figure … MUST be derived once from the stored per-observation forward returns + stored factor values + post-snapshot price path; the API and frontend MUST NOT recompute returns or factors to build them; low-sample cells show NA + n; results carry the survivorship-bias label. … the **as-of-date** mode merely FILTERS the stored observation set to snapshots dated ≤ the as-of date (it recomputes nothing). *(extends No recompute in the read path + No machine-learning price prediction)*"
  - **No recompute in the read path.** "Read endpoints MUST serve canonical values from the persisted immutable snapshot for the resolved as-of date; they MUST NOT recompute scores/returns/buckets per request."
  - **No lookahead.** "Scoring for a snapshot dated D MUST use only price bars with date ≤ D; forward returns MUST use only bars with date > D." — for J-32, the as-of mode MUST pool **only** snapshots with `ScannerRun.asof_date ≤ D`; no run dated > D may contribute. *(critical)*
  - **No fabricated data** / **Honest limitations surfaced.** Low-sample cells show NA + n; the survivorship-bias / universe-relative label persists in both modes — never fabricate a figure to fill an early-date gap.

## GOAL

Add an **All-history ⟷ As-of-date** analysis-mode toggle to the `/research` labs so the user can restrict every Factor-Lab and event-study figure to **only** the snapshots dated ≤ the global as-of date (a point-in-time / walk-forward view) — driven entirely by the existing single global as-of switcher, introducing **no second date state**.

## BACKGROUND

J-32 is the **last buildable must-have journey** (28/32 passing; J-22/J-23/J-24 are externally data-walled and **non-halting** per the re-scoped goal). The iter-18 evaluator recommended this exact target at **full** depth, and after it lands and nothing regresses **GOAL_ACHIEVED becomes reachable on the buildable set**.

The implementation reuses the **proven iter-17 seam** verbatim. `forward_testing.compute_forward_aggregates(…, as_of=D)` already scopes the Backtest evidence aggregate to an expanding window by joining each `ForwardReturn` to its run and filtering `ScannerRun.asof_date <= as_of` (`as_of=None` ⇒ byte-identical all-history). **All three `/research` observation builders open with the identical query** `select(ForwardReturn).where(ForwardReturn.horizon == horizon)` — verified in source this iteration:
- `research.py:_factor_observations` (`:171`) — feeds `compute_factor_lab` (J-25) + its `by_regime` split (J-27) + the volatility family (J-30).
- `research.py:_combination_observations` (`:337`) — feeds `compute_factor_combination` (J-26 composite + strict-overlap).
- `research.py:_event_study_members` (`:636`) — feeds `compute_event_study` (J-29).

So the same single membership filter ports into each builder, and `as_of=None` keeps all-history byte-identical.

The **principal anti-goal risk is J-18** (exactly one date selector). The toggle MUST be a **mode** (All-history vs As-of) that reads the EXISTING global `asOf` from `useAsOf()` — it MUST NOT add a date picker or any second date `useState`. **Crucial nuance for the reviewer/evaluator (MEMORY `j18-asof-on-stocks-fetch-is-correct`):** sending `?as_of=D` on the research fetch in As-of mode is **correct and expected** — it is the single global date being *transmitted* on a snapshot-served read, exactly like `/api/stocks?as_of=D`. It is NOT a J-18 violation. Judge J-18 by: the `/research` page holds no second date state and exposes no date control of its own; the as-of value is sourced solely from the global provider. Consequently the iter-18 test `test_factor_combination_no_date_control_present` (which asserts the endpoint has no `as_of`) must be **intentionally updated** to the new contract — this is a deliberate, J-32-driven acceptance change, **not** a regression (apply the iter-2 lesson: update the invariant test to the new truth, do not silently delete it).

## IN SCOPE

### Backend
- [ ] Thread a keyword-only `as_of: Optional[date] = None` parameter into the three public lab functions and their observation builders, mirroring `compute_forward_aggregates` exactly:
  - `compute_factor_lab(session, factor_key, horizon, config=None, *, as_of=None)` → pass `as_of` into `_factor_observations`.
  - `compute_factor_combination(session, conditions, horizon, config=None, *, as_of=None)` → pass `as_of` into `_combination_observations`.
  - `compute_event_study(session, subject, horizon, config=None, *, as_of=None)` → pass `as_of` into `_event_study_members`.
- [ ] In each of the three observation builders (`_factor_observations`, `_combination_observations`, `_event_study_members`), apply the **single membership filter** to the opening `fr_rows` query, identical to `forward_testing.py:579-583`:
  ```
  fr_stmt = select(ForwardReturn).where(ForwardReturn.horizon == horizon)
  if as_of is not None:
      fr_stmt = fr_stmt.join(ScannerRun, ScannerRun.id == ForwardReturn.run_id).where(
          ScannerRun.asof_date <= as_of
      )
  fr_rows = session.exec(fr_stmt).all()
  ```
  Because `runs_with_fr`, `results`, `run_rows`, and the regime map are all derived from `fr_rows`, this one clause scopes the whole pool. The cutoff MUST read the canonical `ScannerRun.asof_date` (not the denormalized `ForwardReturn.asof_date`). `as_of=None` adds **no clause** → byte-identical all-history.
- [ ] Add an optional `as_of` query parameter to the three endpoints in `api/research.py` (`/research/factor-lab`, `/research/factor-combination`, `/research/event-study`), parsed and validated **exactly like the existing snapshot-served reads** (`/api/stocks?as_of=`, `/api/backtest?as_of=`, `/bars?as_of=`): unparseable → **422**, a date after the latest available snapshot → **400** (mirror the established handler convention — do not fabricate a window). When `as_of` is omitted/null → all-history (the default). Pass the resolved cutoff into the compute function.
- [ ] Each endpoint payload, when scoped, SHOULD echo the **resolved cutoff** as `asof_date` (and `null`/absent in all-history mode), consistent with how every other read endpoint echoes `asof_date` — so the UI can label the point-in-time context and tests can assert the scoping. (The per-cell `n`/`n_total` already drop naturally; no other payload shape change.)
- [ ] Update the docstrings/header comment in `api/research.py` (currently "All three are cross-date all-history aggregates — NONE has an as-of/date control (J-18)") to the J-32 contract: each accepts the **single global as-of** as an optional point-in-time scoping cutoff (a mode, not a second date state); default remains all-history.

### Frontend
- [ ] Add a single page-level **analysis-mode toggle** to `ResearchPage` (`app/research/page.tsx`) — an `"all" | "asof"` segmented control (style it like the existing `HorizonSelector`/`SideToggle`), defaulting to **All history**. Label clearly: "All history" ⟷ "As of date". When in As-of mode, show the resolved as-of context inline (e.g. "As of {asof_date}") using the global provider's value.
- [ ] Thread the mode down to all three labs (`FactorLab`/`compute_factor_lab` driver, `CombinationLab`, `EventStudyLab`). Compute a single **resolved cutoff**: `const asofCutoff = mode === "asof" ? asOf : null;` where `asOf` comes from `useAsOf()`. (At the latest date `asOf` is already `null` ⇒ As-of mode at latest == all-history, which is correct and matches J-09's "latest equals the full aggregate".)
- [ ] Pass `asofCutoff` through the three fetch calls via the existing `withAsOf(...)` helper (so `?as_of=` is appended **only** when a historical cutoff is active). Add the `asof` argument to `fetchFactorLab`/`fetchFactorCombination`/`fetchEventStudy` in `lib/api.ts` (route through `withAsOf`), and add the optional `asof_date` field to their response types.
- [ ] Make each lab's fetch `useEffect` depend on the **resolved cutoff** (`asofCutoff`), NOT raw `asOf`. This guarantees: (a) toggling mode `asof→all` refetches (full sample returns — J-32 step 4); (b) while in **All-history mode, moving the global date does NOT refetch** the labs (cutoff stays `null`) — preserving the J-15 read-path discipline and the genuine cross-date nature of all-history mode.
- [ ] Keep the survivorship-bias / universe-relative / descriptive caveat banner visible in **both** modes (it already renders; do not gate it on mode).

### New user-facing capability
The user can switch the `/research` labs between **All history** (default — pools every snapshot) and **As of date** (pools only snapshots dated ≤ the global as-of date). In As-of mode, setting the global switcher to an earlier trading day re-points every decile / rank-IC / combination-cohort / event-study figure to that point-in-time walk-forward window (smaller n, more honest NA at early dates).

### New information displayed
A point-in-time view of all `/research` analytics: the same decile tables, rank-IC, regime splits, composite/strict-overlap cohorts, and event-study distributions — restricted to the snapshots available as of the chosen date, with reduced `n` and honest NA where the early-date sample is thin. The resolved as-of date is shown as the mode's context label.

### New user actions
A single **All history ⟷ As of date** mode toggle at the top of `/research`. No new date control — the existing global top-bar as-of switcher supplies the date.

### UI surface changes
`/research` page only — one additive mode toggle + an inline "As of {date}" context label. No new page, route, panel structure, or nav entry; the three lab sections are unchanged except that their figures re-point with the mode.

### Product surface delta
`/research` evidence becomes honestly point-in-time-aware: a user can ask "what did this factor/setup/pattern's evidence look like using only data available as of date D?" — the walk-forward discipline the rest of Trendora already applies to scoring and Backtest evidence now extends to the research labs, without adding a second date control anywhere.

### Blueprint conformance
Lives on the **EXISTING approved `/research` home** — additive mode, **no nav-skeleton change → no `blueprint.reapproval-requested` marker**. `blueprint.md` is updated with an iter-19 "NO skeleton change" note and the three lab Data-Contract rows are annotated with the optional `as_of` scoping parameter (a refinement of existing values, mirroring how iter-17 annotated `compute_forward_aggregates`).

### Data-contract additions
**None — no new canonical value.** The as-of mode merely FILTERS the observation set of the three EXISTING lab values (`compute_factor_lab` / `compute_factor_combination` / `compute_event_study`) to snapshots dated ≤ D — exactly as the goal's Data Contract already prescribes ("the Research all-history vs as-of-date mode only filters the observation set to snapshots ≤ the as-of date — it never recomputes a figure"). The three rows are annotated (not duplicated) with the new optional `as_of` cutoff; the SAME module + SAME endpoint serve the scoped value. No new endpoint, no second computation, no new config scoring value.

## OUT OF SCOPE

- **Do NOT autonomously re-probe or build J-22 / J-23 / J-24** — externally Yahoo-429 data-walled and **non-halting** per the re-scoped `docs/goal.md`; recorded honestly blocked (NA). They auto-heal via the committed runbook on operator confirmation of a reachable feed — no code change here.
- **No second date state / no date picker on `/research`** — the toggle is a mode; the date comes only from the global provider (J-18, the principal risk).
- No new page, route, nav entry, or blueprint re-approval.
- No change to `scoring.py` / `scanner.py` / `regime.py` / `patterns.py` / `buckets.py` / `forward_testing.py` storage / `snapshot_serving.py` / `asof-provider.tsx` / `stocks/page.tsx` / `backtest/page.tsx` — **no DB regen** (this is a read-only filter on the research read path + a new query param). J-06/J-07 stay byte-identical.
- No new scoring weight/threshold/cutoff/config value (a UI mode default is not a magic number). The cutoff is the existing global as-of date; horizons / `min_sample` already exist in config.
- Do NOT alter the per-date forward-test scorecard's as-of behavior (J-09/J-14 already deliver that on `/backtest`).

## DEFINITION OF DONE

- [ ] **J-32 passes via browser-qa-agent**: on `/research`, toggle to **As of date**, set the global switcher to an early trading day, and DOM-assert the decile / rank-IC / combination / event-study figures re-point with a **reduced n** (and honest NA at early dates); toggle back to **All history** and confirm the full-sample figures return; the survivorship label persists in both modes.
- [ ] **J-18 re-verified (principal anti-goal)**: `/research` exposes exactly **one** date control — the global top-bar switcher (no page-local date input/picker, no second date `useState`); the mode toggle is a mode, not a date control. The `?as_of=` on the research fetch in As-of mode is the single global date transmitted (expected, correct — not a violation). Verify in **source** (page reads `asOf` solely from `useAsOf()`) **and live** (exactly one date `<select>`, a descendant of `<header>` not `<main>`).
- [ ] **Required-still-passing remain green**: J-25/J-26/J-27/J-29/J-30 render unchanged in the **default All-history mode** AND correctly re-point in As-of mode; J-15 read-path preserved (All-history mode does not refetch on global-date change); J-31 synthesis travel intact; J-06/J-07 byte-identical (scoring/snapshot path git-verified untouched, no DB regen).
- [ ] **No anti-goal violation introduced** — verify in source: the as-of mode is a pure read-only FILTER (forbidden-call grep `run_scan`/`score_stocks`/`backfill*`/`forward_return`/`detect_*`/`score_regime` still hits only docstrings in `research.py`); `as_of=None` byte-identical to current all-history; no run dated > D contributes; low-sample NA + survivorship label persist.
- [ ] Unit/integration tests pass; backend suite green (run once — see MEMORY `backend-test-suite-runtime`, ~14 min); frontend typechecks/build clean.
- [ ] All 6 UI-visibility artifacts produced (implementation-summary, user-visible-changes, ui-surface-map, ui-test-plan, ui-test-results, what-to-click).
- [ ] Coherence COHERENCE-PASS; reviewer PASS/PASS_WITH_NOTES (no blocking notes); QA PASS; closure CLOSURE-PASS.
- [ ] Dev handoff written at `docs/handoffs/goal-i_can_see_the_wealthy_future_forever-iter-19-dev.md`.
- [ ] `blueprint.md` updated (iter-19 NO-skeleton-change note + the three lab rows annotated with the `as_of` cutoff). **No** `blueprint.reapproval-requested` marker.

## TESTING REQUIREMENTS

- **Browser (Chrome MCP)** — J-32 end-to-end and J-18:
  1. `/research` defaults to **All history**; capture the baseline decile/rank-IC + a combination cohort + an event-study table with their `n`.
  2. Toggle to **As of date**; set the global switcher to one of the **earliest** dates in the dropdown (bottom of the descending list) — per MEMORY/lesson iter-11, thin the sample by **date**, not by horizon. DOM-assert each lab's figures change and `n` **drops** (and early-date low-sample cells show NA + n, never a fabricated number). Use distinct sha256 screenshots + DOM/network assertions (not a single before/after pair — iter-6 lesson).
  3. Toggle back to **All history**; DOM-assert the full-sample figures (and the larger `n`) return.
  4. **J-18 live:** assert exactly one date `<select>` on the page (in `<header>`, not `<main>`); in As-of mode confirm the research fetch carries the single global `?as_of=` (expected) and that there is no page-local date input; in All-history mode, confirm moving the global date leaves the research figures unchanged with **no** research refetch (network-asserted).
  - If the mode toggle is implemented as a native `<select>`, drive it with the native-setter + bubbling change event and assert live DOM (MEMORY `react-controlled-select-needs-native-setter`); a segmented button control can be clicked directly. Ensure a clean hydrated build before driving UI (MEMORY `browser-qa-dead-shell-next-cache`: confirm `GET /_next/static/chunks/main-app.js` → 200 and the health badge clears; do not run `npm run build` against the live dev `.next`).
- **Unit/integration (backend)** — mirror the iter-17 as-of tests for **each** of the three lab functions/endpoints:
  - `as_of=None` == `as_of=latest` == the current all-history result (**byte-identical** — the all-history regression guard).
  - `as_of=D` for an early D pools **only** snapshots with `ScannerRun.asof_date ≤ D` → strictly smaller `n_total`/cell `n` than all-history; **no future-run leak** (a run dated > D contributes nothing — assert via a controlled fixture or by comparing pooled counts across two cutoffs).
  - Low-sample / NA at an early cutoff (the decile/cohort/regime cells with `n < walk_forward.min_sample` show NA + `n`, never fabricated).
  - Endpoint validation: `?as_of=` unparseable → **422**; future date (> latest) → **400**; valid historical date → scoped payload echoing the resolved `asof_date`.
  - **J-18 contract test (intentional update):** revise `test_factor_combination_no_date_control_present` to the J-32 truth — the endpoint now accepts the single global `as_of` as an optional scoping cutoff (not a second date state); the frontend holds no second date control. Document the change as a deliberate J-32 acceptance update (iter-2 lesson — update the invariant, don't delete it).
  - Read-only keystone: extend the existing patch-to-raise test so the scoped path also recomputes no return/factor/regime.
- **Error cases:** unparseable `as_of` (422); future `as_of` (400); an as-of date so early that a lab has zero contributing snapshots → honest empty/NA payload with `n=0`, never a fabricated row or a 500.

## NOTES

- **Why full depth:** critical read-only research path across three engine functions + their builders + three endpoints, the J-18 critical anti-goal surface, and new correctness tests (as-of scoping, none==latest==all-history, no future-run leak, early-date NA, 422/400 validation) → needs coherence + ux-regression + closure. The iter-18 evaluator explicitly recommended full.
- **Lessons applied:**
  - *iter-17 seam* — `compute_forward_aggregates(…, as_of=D)` (`forward_testing.py:579-583`) is the exact template; the three research builders share its opening query, so the port is mechanical and low-risk.
  - *MEMORY `j18-asof-on-stocks-fetch-is-correct`* — `?as_of=D` on a historical toggle is the single global date transmitted on a snapshot-served read, NOT a 2nd date state; judge J-18 on the page being date-control-free, not on the API call carrying `as_of`. Surface this to the reviewer/evaluator so the new `?as_of=` is not misread as a violation.
  - *iter-11 lesson* — in this seed `n` is nearly horizon-independent (1218@5d vs 1217@60d); you CANNOT thin the sample by lengthening the horizon. J-32 thins by **date** (an early as-of cutoff → few contributing snapshots → genuinely smaller n + NA) — design the NA/low-sample evidence around an early as-of date.
  - *iter-2 lesson* — when an acceptance bar changes, UPDATE the affected invariant test to the new truth (here `test_factor_combination_no_date_control_present`); do not silently delete it or treat its change as a regression.
  - *iter-6 / iter-15 / MEMORY `browser-qa-dead-shell-next-cache`* — serialize Chrome access if both qa + browser-qa run; de-dup evidence by sha256; ground before/after on distinct shots + DOM/network; ensure a hydrated build before driving UI.
  - *MEMORY `react-controlled-select-needs-native-setter`* — if the mode toggle is a `<select>`, Chrome MCP `select` won't fire React onChange; use the native-setter + bubbling change event and assert live DOM.
- **Process note (recurring full-depth gap):** prior full-depth iters produced no `-audit.md` handoff and wrote `status.json` to the PHASE-namespace path `runs/goal-i_can_see_the_wealthy_future_forever-iter-19/status.json` (NOT under `runs/goal-session-.../iter-19/`, which holds only `coherence.md` + `snapshot-sha`). The evaluator should verify the critical seams in source and check BOTH paths before declaring an artifact absent (lesson iter-10).
- **Watch-item (carry, not a blocker):** `apps/frontend/app/data/page.tsx:141` subtitle still reads "grow the System Health evidence" — stale post-retirement prose (no dangling route); tidy in a future touch, not this iter's scope.
- **Strategic:** after J-32 lands and nothing regresses → **GOAL_ACHIEVED is reachable** on the buildable set (29/32; J-22/J-23/J-24 honestly blocked NA, non-halting). Do NOT autonomously re-probe the data-walled three.
