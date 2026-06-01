# Goal Iteration 1 — One date control: Backtest reads the global as-of switcher (delete its page-local picker)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** i_can_see_the_wealthy_future_forever
- **Iteration:** 1
- **Mode:** next
- **Depth:** lean
- **Frontend Present:** yes
- **Target journeys:** J-18, J-13
- **Required-still-passing journeys:** J-14, J-01, J-03, J-04, J-05
- **Anti-goal reminders:**
  - **Exactly one date selector.** The frontend MUST NOT maintain a second, independent date state; every date-scoped page (including Backtest) reads the single global as-of control. *(extends Single source of truth)*
  - **Single source of truth.** Each of the six canonical scores (and the A–E bucket and setup status) MUST be computed exactly once by the scoring/regime engine and read identically by every page; the API and frontend MUST NOT recompute them. The same symbol's score MUST NOT differ between two views. *(critical)*
  - **No recompute in the read path.** Read endpoints MUST serve canonical values from the persisted immutable snapshot for the resolved as-of date; they MUST NOT recompute scores/returns/buckets per request. *(extends Single source of truth)*
  - **No fabricated data.** On a data-provider failure the system MUST surface an explicit stale/unavailable state and MUST NOT synthesize prices or scores to force a green journey. *(the Backtest scorecard's NA/n honesty must remain intact)*

## GOAL

The user controls the Backtest page's date from the **one** global top-bar as-of switcher — the page has **no** date dropdown of its own, holds no independent date state, and its as-of scan + forward-test scorecard re-point to exactly the date every other page resolves.

## BACKGROUND

iter-0 (baseline) verified 10 journeys passing and recorded three genuine gaps (J-17, J-18, J-19) plus one **live anti-goal violation**: `apps/frontend/app/backtest/page.tsx` keeps its **own** date state (`selected`/`dates`/`latest`/`ready`) and renders a page-local `BacktestDatePicker` (`<Select aria-label="Backtest as-of date">`), independent of the global top-bar switcher — the duplicate date control J-18 and blueprint coherence invariant #5 forbid. Backtest is the **only** as-of-aware page that does not consume the global `useAsOf()` provider; `/`, `/stocks`, `/themes`, `/sectors`, and `/stocks/[ticker]` already do.

The evaluator recommended fixing J-18 first because it is the smallest change and clears the session's only live (critical-family) anti-goal violation. This iteration does exactly that as a **focused consolidation pass before any new feature scope (J-19, J-17) is added** — deliberately keeping J-19's attribution work, which also lands on Backtest, for a later iteration so it builds onto a Backtest that already reads the global date control. Depth is **lean**: this is a single-file frontend refactor that consumes an existing, proven provider (no backend, no data model, no new endpoint, no new contract value); the always-on coherence-auditor re-checks invariant #5 and browser-qa re-verifies the affected journeys.

The J-18 test flow (change the global switcher → confirm every page incl. Backtest re-points) is exactly J-13's acceptance extended to Backtest, so this iteration also **re-verifies J-13** (which was only "partial" in iter-0 due to a degraded browser tool layer, not a code gap — no code change is needed to convert it).

## IN SCOPE

### Backend
- [ ] None. No backend, API, config, data-model, or engine change. (`/api/backtest`, `/api/dashboard|sectors|themes|stocks?as_of=`, and `/api/runs` already accept/echo the as-of date and are unchanged.)

### Frontend
- [ ] In `apps/frontend/app/backtest/page.tsx`, consume the global as-of state: `import { useAsOf } from "@/components/asof-provider"` and read `const { asOf } = useAsOf();`, following the exact pattern already used by `app/stocks/page.tsx` (`fetchStocks(asOf ?? undefined, …)`, effect keyed on `[asOf]`).
- [ ] Drive every fetch from `asOf`: `fetchBacktest(asOf ?? undefined, signal)` and the scan-summary fetches (`fetchDashboard`/`fetchSectors`/`fetchThemes`/`fetchStocks` with `asOf ?? undefined`). Key the data effect on `[asOf]`.
- [ ] **Delete** the page-local date machinery: the `dates`/`latest`/`ready`/`selected` state, the `useEffect` that calls `fetchRuns()` to populate the page's own picker (page.tsx:62–78), the `<BacktestDatePicker …/>` usage in the header (page.tsx:112–118), and the `BacktestDatePicker` component definition itself (page.tsx:175–208). Remove the now-unused `fetchRuns` import.
- [ ] Re-derive the page's read-only "Viewing as-of D (historical|latest)" badge from the backtest response / global `asOf` (no longer from the deleted `selected`/`latest`). This badge is a **display indicator, not a control** — keeping it is fine (the global switcher's own indicator also shows in the top bar); do not reintroduce any `<Select>` or independent date state.
- [ ] Preserve all existing Backtest behavior otherwise: the as-of scan summary, the forward-test scorecard with per-horizon return / excess / control groups + sample size n, the survivorship banner, and the honest NA/empty states (J-14 must stay green).

### New user-facing capability
The user picks the Backtest date from the same global top-bar switcher that controls every other page — one control, one resolved date everywhere. Selecting a date on Backtest and navigating to `/stocks` (or vice-versa) keeps the same date (the provider lives in the app shell).

### New information displayed
None. (No new value, metric, or column. The resolved as-of date is the existing canonical value, now sourced from the single global control on Backtest too.)

### New user actions
None added; **one removed/consolidated** — the page-local "Backtest as-of date" dropdown is deleted; its function moves entirely to the existing global top-bar switcher.

### UI surface changes
`/backtest` only: the page-local "AS-OF DATE" dropdown is removed from the page header. No other page changes. No sidebar/nav change.

### Product surface delta
"Which date am I viewing" now has a single source on every page, including Backtest. No more divergent date state between the top bar and the Backtest page.

### Blueprint conformance
No blueprint change. Backtest stays at its existing canonical home `/backtest` under the existing nav skeleton. This iteration realizes the target the blueprint already prescribes: IA note "`/backtest` … page-local picker must be removed so the page reads only the global switcher," and coherence invariant #5 ("Exactly one date selector … currently violated by the Backtest page-local picker — must be removed"). No nav-skeleton edit → no `blueprint.reapproval-requested`.

### Data-contract additions
None. The resolved as-of date / available dates are already a registered canonical value (`app.engine.snapshot_serving` + as-of resolution in `scanner`; available dates from `GET /api/runs`; resolved `asof_date` echoed by every read endpoint). Backtest will read this existing source via the global provider instead of computing its own; no second computation or endpoint is introduced.

## OUT OF SCOPE

- **J-19 (return attribution)** — not this iteration. It also touches Backtest, but is deliberately deferred so it builds onto a Backtest already wired to the global date control. No attribution slices, per-stock contributors, by-sector/by-rank-band, or distribution/hit-rate work here.
- **J-17 (Data Manager `/data`)** — not this iteration. When built (iter-2+), its date inputs must likewise consume the global control, but `/data` does not exist yet and is untouched here.
- Any backend, API, config, engine, scoring, forward-testing, or data-model change.
- Any visual redesign of Backtest beyond removing the dropdown and rewiring the date source.
- Converting the other iter-0 partials (J-02 filters, J-06 leaderboard==detail, J-11 add+restart, J-15 warm-load, J-16 VCP filter) — only J-13 is re-verified here because it rides the same flow as J-18; the others are out of scope for this iteration.

## DEFINITION OF DONE

- [ ] **J-18 passes** via browser-qa: `/backtest` exposes **no** date selector of its own; the single global top-bar switcher drives the Backtest as-of scan summary AND the forward-test scorecard; the as-of date shown on Backtest matches the switcher and matches what another date-scoped page (e.g. `/stocks`) resolves for the same date.
- [ ] **J-13 re-verified** (no code change beyond the J-18 edit): selecting a past date in the global switcher re-points `/`, `/stocks`, `/themes`, `/sectors`, **and `/backtest`** to that date's stored snapshot; the "viewing as-of D (historical)" indicator is visible; returning to latest restores the current view. (If the browser tool layer is degraded and the interaction cannot be driven, record PARTIAL with the reason — it must not be reported as a failure, and J-18 verification against source still governs.)
- [ ] **J-14 remains green:** the Backtest forward-test scorecard still renders per-horizon return / excess-vs-SPY/QQQ/sector / control-group columns with sample size n, and still shows honest NA (n=0) for un-elapsed horizons — driven by the date chosen in the global switcher.
- [ ] **Required-still-passing journeys remain green:** J-01, J-03, J-04, J-05 (the other global-switcher consumers — untouched, but confirm the switcher still re-points them).
- [ ] **Coherence invariant #5 satisfied:** the frontend holds no second, independent date state; `app/backtest/page.tsx` imports and uses `useAsOf` and contains no `<Select>`/picker of its own. (Enables the evaluator to mark the journey-history `anti_goal_violations` entry for the date selector `resolved: true`.)
- [ ] No anti-goal violation introduced.
- [ ] Frontend builds: `cd apps/frontend && npm run build` passes (compiles + typechecks). Backend `pytest` suite remains green (no backend change; run as a guard).
- [ ] Dev handoff written at `docs/handoffs/goal-i_can_see_the_wealthy_future_forever-iter-1-dev.md`.

## TESTING REQUIREMENTS

- **Browser (primary — J-18):**
  1. Visit `/backtest`. Confirm there is **no** page-local date dropdown (the former `<Select aria-label="Backtest as-of date">` is gone).
  2. In the global top-bar switcher, select a historical date with enough post-snapshot bars.
  3. Confirm the Backtest as-of scan summary (regime, top sectors/themes, ranked cohort) **and** the forward-test scorecard re-point to that date, and the page's "viewing as-of D (historical)" indicator matches the switcher.
  4. Navigate to `/stocks` (date persists via the app-shell provider) and confirm it resolves the **same** date; navigate back to `/backtest` and confirm it still shows that date — one resolved date everywhere.
  5. Return the switcher to Latest and confirm Backtest restores the latest view.
- **Browser (re-verify — J-13):** with the same switcher interaction, confirm `/`, `/stocks`, `/themes`, `/sectors` re-point to the chosen date alongside `/backtest`; historical indicator visible; latest restores.
- **Browser (no-regression — J-14):** for a date with ≥60 elapsed bars the scorecard shows numeric horizons with n; for a recent/latest date the long horizons honestly show NA (n=0) — nothing fabricated.
- **Build/unit:** `cd apps/frontend && npm run build` must pass (TypeScript typecheck catches the deleted-state/removed-import rewiring). Backend `cd apps/backend && .venv/bin/python -m pytest tests/ -v` must stay green (guard; expected untouched at 248/0).
- **Error cases:** when `GET /api/runs` is unavailable the global switcher already degrades to latest-only (disabled control); confirm `/backtest` then renders the latest scorecard (or its existing honest error/empty state) and does **not** crash — i.e. the page no longer depends on its own `fetchRuns()` for graceful degradation.

## NOTES

- **Apply the iter-0 lesson (directly relevant — this iteration touches `apps/frontend/app/backtest/` and the `components/asof-*` surface):** *"When the Chrome-MCP tool layer is degraded, browser-QA's negative interaction findings are unreliable… Always confirm date-control / single-source-of-truth claims against frontend source, not just the browser-QA summary."* In iter-0 QA wrongly reported "no separate date dropdown" while the source clearly had a `BacktestDatePicker`. **Verification gate for J-18:** confirm against source that (a) `app/backtest/page.tsx` no longer defines or renders `BacktestDatePicker` and contains no `<Select>` for dates, (b) it imports `useAsOf` and keys its data effect on `asOf`, and (c) it no longer holds `selected`/independent date state — do not pass J-18 on a visual "no dropdown" screenshot alone.
- **Exact reference pattern for the developer:** mirror `apps/frontend/app/stocks/page.tsx` (`const { asOf } = useAsOf();` → `fetchStocks(asOf ?? undefined, controller.signal)`, effect deps `[asOf]`). The provider/switcher already exist and are mounted in `app/layout.tsx`; the available-dates source (`GET /api/runs`) is identical to what the page used, so the option list and default-latest behavior are unchanged.
- **Surgical-change discipline (core.md):** edit only `app/backtest/page.tsx`. Remove only the imports/state/components your change makes unused (`fetchRuns`, the date state, `BacktestDatePicker`). Do not touch the provider, the switcher, other pages, or the backend.
- **Why lean despite the evaluator's "full":** the evaluator's full-depth recommendation was scoped to the 3-feature batch (J-18+J-19+J-17) as "multi-surface features touching the data contract + IA." J-18 alone is a single frontend file consuming an existing provider — none of the full-depth triggers apply (no backend+frontend crossing, no data-model change, no new test type, prior verdict was CONTINUE not ESCALATE). The coherence-auditor (which hard-checks invariant #5) runs every iteration regardless of depth, and the lean cycle's browser-qa re-verifies J-18/J-13/J-14 — adequate coverage for this refactor.
- **Sequencing intent:** iter-2 → J-19 (return attribution on `/system-health` + `/backtest`, read-only from stored per-observation forward returns); iter-3 → J-17 (Data Manager). Doing J-18 first clears the live violation and gives J-19 a clean Backtest date source to build on.
