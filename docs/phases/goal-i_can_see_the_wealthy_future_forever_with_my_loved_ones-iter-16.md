# Goal Iteration 16 — Availability heatmap readability + keyboard as-of stepping

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** i_can_see_the_wealthy_future_forever_with_my_loved_ones
- **Iteration:** 16
- **Mode:** next
- **Depth:** lean
- **Frontend Present:** yes
- **Target journeys:** J-70, J-71
- **Required-still-passing journeys:** J-61 (availability heatmap reads `GET /api/data/availability`), J-62 (as-of calendar popover), J-43 (`?asof` URL serialization), J-13 (browse as-of past date), J-18 (one date control, no duplicate), J-42 (ISO `yyyy-MM-dd` everywhere)
- **Anti-goal reminders:**
  - **Single source of truth.** Each of the six canonical scores (and the A–E bucket and setup status) MUST be computed exactly once by the scoring/regime engine and read identically by every page; the API and frontend MUST NOT recompute them. The same symbol's score MUST NOT differ between two views. *(critical)*
  - **No magic numbers.** Every scoring weight, threshold, decision-rule cutoff, bucket edge, universe entry, and theme definition MUST come from the config file — no such literal in calculation code. *(J-70: the heatmap's day-number contrast MUST use existing design tokens — no hardcoded hex.)*
  - **No fabricated data.** On a data-provider failure the system MUST surface an explicit stale/unavailable state and MUST NOT synthesize prices or scores to force a green journey. *(J-70 stays a pure re-render of the same `GET /api/data/availability` payload — same density buckets, never a fabricated or omitted cell.)*
  - **No recompute in the read path.** Read endpoints MUST serve canonical values from the persisted immutable snapshot for the resolved as-of date; they MUST NOT recompute scores/returns/buckets per request.
  - **Exactly one date selector** (Anti-goal restatement, the J-18 invariant): the single global top-bar as-of switcher is the only date control; `?asof` (J-43) is its SERIALIZATION, never a second state. *(J-71: ArrowLeft/ArrowRight keyboard stepping MUST drive that SAME single global as-of state via the existing `onSelect`→`setAsOf`; it MUST introduce NO page-local or second date state and MUST NOT use a global `window` keydown listener — handling lives on the existing calendar dialog's `onKeyDown`.)*

## GOAL

Make the Data Manager per-date availability heatmap legible and compact (readable day numbers on every density cell, newest months first, two months per row) and let the user scrub the global as-of date with ArrowLeft/ArrowRight while the as-of calendar popover is open — both pure frontend polish on the committed seed, completing the appended J-68..J-71 scope.

## BACKGROUND

The iter-15 evaluator returned CONTINUE: J-68 and J-69 shipped and pass, leaving only the two explicitly-deferred frontend-polish Must-haves J-70 and J-71 (appended in commit aefc120) as the last tractable work before GOAL_ACHIEVED. Both are pure frontend on the committed seed (goal.md: "J-68 … J-71 are NOT data-dependent"), so depth is **lean** per the evaluator's recommendation. J-70 touches only `apps/frontend/components/availability-heatmap.tsx`; J-71 touches only `apps/frontend/components/asof-calendar.tsx`. The blueprint already registers both as `[TARGET iter-16]` rows on existing homes (`/data` and the cross-cutting as-of popover) with no new Data Contract value — coherence-clean by construction. Prior iter-15 coherence was COHERENCE-PASS (no consolidation pass owed).

**Lessons applied (from session lessons + evaluator):**
- **J-18 single-global-as-of invariant (iters 13/15):** `asof-provider.tsx` is the sole `?asof` owner and the only date state; `asof-calendar.tsx`'s only local state is the month-view cursor. J-71 MUST keep it that way — step the existing `onSelect`/`setAsOf` path, add NO second date state, and use NO global `window` keydown listener (handle on the dialog's existing `onKeyDown`).
- **Recurring blank / byte-identical close-up evidence (iters 3/7/10/13/15):** instruct browser-QA to `md5sum` the evidence dir first and re-capture any blank or byte-identical close-up as a full-viewport screenshot; both J-70 and J-71 are visually-verifiable surfaces that suffered this in prior iters.
- **No `npm run lint` in DoD (iter-1):** ESLint is not installed; gate the frontend with `npx tsc --noEmit` (typecheck), not lint.
- **Dev-server / port hygiene:** never broad-`pkill` `next dev`/`uvicorn` on this shared machine; kill by port only.

## IN SCOPE

### Backend
- [ ] None. This iteration is frontend-only. No endpoint, no schema, no engine change. `GET /api/data/availability` and the global as-of resolution are read verbatim.

### Frontend (if applicable)
- [ ] **J-70 — `apps/frontend/components/availability-heatmap.tsx` readability/layout polish (pure re-render of the same payload):**
  - Day-number text meets a **legible contrast on EVERY density bucket 0–5**. Today the cell text uses `bucket >= 4 ? "text-bg" : "text-text-muted"`, so the empty/low-density cells (buckets 0–3, on the muted `bg-surface-2` / faint `bg-accent/15`–`bg-accent/30` backgrounds) render dark-on-dark and the day number is barely readable. Choose a per-bucket text token (existing design tokens only — e.g. `text-text` / `text-text-muted` on the faint buckets and `text-bg` on the dark-text-on-bright high buckets) so the day number is clearly legible against its own cell background across all six buckets. **No hardcoded hex** (coherence invariant 10).
  - Month bands render in **descending order** (newest month first, top to bottom). Today `toMonthBands` emits ascending and the render maps them in that order; reverse the rendered band order (descending) while keeping each month's internal day order ascending (calendar reads left→right, top→bottom within a month).
  - Month bands lay out **two-up per row** on a normal-width viewport, **collapsing to one column on narrow screens** (use the responsive grid utilities already in the codebase, e.g. a `grid` with `md:grid-cols-2` / `grid-cols-1`), so more history is visible without excessive scrolling.
  - Cells still encode the **same density buckets** and read the **same `GET /api/data/availability` payload** — descriptive only, nothing recomputed. The hover readout, snapshot ring, legend, click/shift-click prefill (job parameters, never the global as-of — J-18), and the `data-testid`/`data-*` attributes browser-QA relies on (`availability-cell`, `data-bucket`, `data-date`, `data-symbols`, `data-total`, `data-snapshot`, `availability-month`) MUST be preserved.
- [ ] **J-71 — `apps/frontend/components/asof-calendar.tsx` keyboard stepping (drives the single global state):**
  - Extend the dialog's **existing `onKeyDown`** (which already handles `Escape`) to handle **ArrowLeft** and **ArrowRight**: ArrowLeft selects the previous (older) available snapshot date, ArrowRight the next (newer) one — stepping **only among the available snapshot dates** (`dates`, already passed in; use the existing `sortedAsc` ordering), never an arbitrary calendar ±1 day onto a non-snapshot day.
  - Each step calls the existing **`onSelect(...)`** (which the switcher wires to `setAsOf`) so it drives the **single global as-of control** and stays in sync with `?asof` (J-43). When the step lands on the latest available date, pass `null` (the existing "Latest" semantics), matching how the day buttons already compute `isLatest ? null : cell.iso`.
  - On a keyboard step the popover **stays open** (do NOT call `onClose()` — only Escape / a click / Enter on a day still close, exactly as today) so the user can keep scrubbing live.
  - Stepping is **bounded**: at the oldest available date ArrowLeft is a no-op; at the latest ArrowRight is a no-op (rests at Latest). Compute the current index from the current `asOf` (or treat `null`/latest as the newest index).
  - The **viewed month cursor follows the selection** — after a step, update the local `view` (the month-navigation cursor, the only local state, NOT an as-of value) to the month of the newly selected date so the selected day is visible.
  - Call `e.preventDefault()` on the handled Arrow keys so they don't scroll the popover/page. Do **NOT** add a global `window`/`document` keydown listener — keep it on the dialog `onKeyDown` (the dialog already receives focus on open via `data-autofocus`).
  - Introduce **NO new date state**: the only local state stays the month-view cursor; `asof-provider.tsx` remains the sole owner of the as-of value and its `?asof` serialization (J-18 critical invariant).

### New user-facing capability
- The Data Manager availability heatmap is readable at a glance (legible day numbers on every cell, newest months first, two months per row). With the as-of calendar popover open, the user can press ArrowLeft/ArrowRight to scrub the global as-of date one snapshot date at a time, live, with pages re-reading at the new date.

### New information displayed
- None new. Same `GET /api/data/availability` cells (re-styled/re-ordered) and the same available-snapshot-date list (now keyboard-steppable). No new value, no new figure.

### New user actions
- ArrowLeft / ArrowRight keyboard stepping on the open as-of calendar popover. (Heatmap interactions are unchanged.)

### UI surface changes
- `/data` — `availability-heatmap.tsx` restyled (contrast tokens) and relaid-out (descending months, two-up-per-row).
- Cross-cutting as-of calendar popover — `asof-calendar.tsx` gains ArrowLeft/ArrowRight handling on its existing `onKeyDown`. No new page, no new route, no nav change.

### Product surface delta
- The dataset's per-date availability is legible and compact; time-travelling the dashboard becomes a fast keyboard scrub instead of click-by-click. Both are presentation upgrades of existing, already-passing surfaces (J-61 heatmap, J-62 calendar) — the same single global state, presented better.

### Blueprint conformance
- No new surfaces. J-70 lands on the existing **Data Manager (`/data`)** home (sidebar item, one click). J-71 lands on the existing cross-cutting **as-of calendar popover** (top-bar switcher). Both are already pre-registered in `blueprint.md` as `[TARGET iter-16]` rows in the IA (`/data` line, the cross-cutting J-71 entry) and in the Data Contract (Per-date availability counts row → J-70; Resolved as-of date row → J-71). No nav-skeleton change, so no `blueprint.reapproval-requested`.

### Data-contract additions
- **none.** J-70 is a pure re-render of the already-registered "Per-date availability counts" value (`GET /api/data/availability`) — same density buckets, no recompute. J-71 drives the already-registered "Resolved as-of date + available dates (ONE global state)" value via the existing `setAsOf` — no new value, no new endpoint, no second compute path.

## OUT OF SCOPE

- Any backend change (endpoint, engine, schema, config). Frontend-only.
- Any change to `asof-provider.tsx`, `asof-switcher.tsx`, or the `?asof` serialization logic — J-71's handler stays inside `asof-calendar.tsx`'s existing `onKeyDown`, calling the already-wired `onSelect`.
- A global `window`/`document` keydown listener for as-of stepping (explicitly forbidden by J-71 and the J-18 invariant).
- Any second/page-local date state, or any new date control.
- Changing the density-bucket thresholds, the legend, the snapshot ring, or the click/shift-click prefill behaviour of the heatmap (those are J-61, already passing — preserve them).
- The data-walled journeys J-22 / J-23 / J-24 (honest NA, non-halting — untouched).

## DEFINITION OF DONE

- [ ] Target journeys J-70, J-71 pass via browser-qa-agent (against the committed seed; no provider needed).
- [ ] Required-still-passing journeys J-61, J-62, J-43, J-13, J-18, J-42 remain green (heatmap still reads the same endpoint + click prefills the job form; calendar still selects/Latest/Escape/click as before; single global as-of state intact; ISO dates everywhere).
- [ ] No anti-goal violation introduced — in particular no second date state, no global keydown listener, no hardcoded hex (design tokens only), no recompute in the read path.
- [ ] Frontend typechecks clean: `cd apps/frontend && npx tsc --noEmit` passes (NOT `npm run lint` — ESLint is not installed, iter-1 lesson).
- [ ] Dev handoff written at `docs/handoffs/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-16-dev.md`.

## TESTING REQUIREMENTS

- **Browser (named journeys this iteration must verify):**
  - **J-70:** On `/data`, open the Per-date availability heatmap. Assert (a) every cell's day number is legible against its background across density buckets 0–5 — verify by reading a low/empty (`data-bucket="0"`/`"1"`) cell's day number is rendered and not dark-on-dark (capture full-viewport, not a degraded close-up); (b) month bands render newest-first (the first rendered `availability-month` `data-month` is the most recent month, descending); (c) at a normal viewport width two month bands sit side-by-side per row, collapsing to one column at a narrow width. Confirm a cell click still prefills the job form Start/End (J-61 preserved) and never changes the global as-of (J-18).
  - **J-71:** Open the top-bar as-of switcher so the calendar popover (`asof-calendar`) shows. Press ArrowRight then ArrowLeft and assert the global as-of indicator (`asof-indicator`) and the `?asof` URL param step to the next/previous **available snapshot date** (not an arbitrary ±1 day), the popover stays open, and the viewed month (`asof-cal-month`) follows. Assert bounded behaviour: at the oldest date ArrowLeft is a no-op; at the latest ArrowRight rests at Latest (clean URL, "Latest" indicator). Confirm Escape still closes, a day click still selects+closes (J-62 preserved), and there is exactly one date control (J-18).
  - **Required-still-passing smoke:** J-61 heatmap still loads from `GET /api/data/availability`; J-13/J-43 historical as-of still survives a reload via `?asof`.
- **Unit/integration:** No backend tests required (frontend-only, no backend code path changed). If the project has any frontend component tests for these two components, extend them; otherwise the browser-QA journeys above are the required evidence per the framework's UI-visibility rules.
- **Error cases:** ArrowLeft at the oldest available date and ArrowRight at the latest must be safe no-ops (no out-of-bounds index, no console error, no second date state created). A keyboard step must never close the popover.

## NOTES

- **Evidence hygiene (recurring, iters 3/7/10/13/15):** browser-QA MUST `md5sum` the evidence directory before finalizing and re-capture any blank or byte-identical close-up as a full-viewport screenshot. The heatmap contrast (J-70) and the live as-of stepping (J-71) are exactly the kind of zoomed surfaces that previously degraded to blank 6830-byte captures — full-viewport captures + DOM-text/attribute extraction (`data-bucket`, `asof-indicator`, `asof-cal-month`, the URL `?asof`) are the durable evidence.
- After J-70 and J-71 pass, the appended J-68..J-71 scope is complete and 0 buildable Must-have journeys remain failing/unknown except the data-walled J-22/J-23/J-24 (honest NA, non-vetoing). The next evaluation is expected to be GOAL_ACHIEVED.
- Lean cycle (developer → reviewer → browser-qa) is sufficient: two isolated, low-risk frontend files, no backend, no data model, no cross-boundary change. Prior depth was full only because iter-15 touched a backend transaction boundary; this iteration does not.
