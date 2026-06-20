# Goal Iteration 41 — Dynamic-universe membership timeline: pagination (10/page) + Year/Month filters (pure view transform)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** i_can_see_the_wealthy_future_forever_with_my_loved_ones
- **Iteration:** 41
- **Mode:** normal
- **Depth:** lean
- **Frontend Present:** yes
- **Target journeys:** J-99
- **Required-still-passing journeys:** J-96, J-94, J-93, J-36, J-37, J-39, J-18, J-07, J-06, J-87, J-88, J-89, J-90, J-97, J-98
- **Anti-goal reminders (verbatim from docs/goal.md):**
  - **Single source of truth.** Each of the six canonical scores (and the A–E bucket and setup status) MUST be computed exactly once by the scoring/regime engine and read identically by every page; the API and frontend MUST NOT recompute them. The same symbol's score MUST NOT differ between two views. *(critical)*
  - **No recompute in the read path.** Read endpoints MUST serve canonical values from the persisted immutable snapshot for the resolved as-of date; they MUST NOT recompute scores/returns/buckets per request. The scan is computed once per date (bootstrap, scheduled, or first view) and then read from storage.
  - **No fabricated data.** On a data-provider failure the system MUST surface an explicit stale/unavailable state and MUST NOT synthesize prices or scores to force a green journey.
  - **Coverage & missing-data are descriptive & honest.** The coverage figures, the per-symbol/per-universe-member table, and the insufficient-for-analysis diagnostic MUST be read-only metadata derived from the stored bars + config — they MUST NOT recompute or restate any canonical score, return, bucket, or setup.
  - **(Exactly one date selector — J-18, critical.)** The single global as-of switcher in the top bar is the ONLY date control. List/view controls (sort, search, filter, pagination) are view transforms over already-served rows and MUST NOT introduce a second or page-local date state.

## GOAL

On the Data Manager `/data` page, the dynamic-universe membership timeline (J-96) gains client-side pagination (10 rows per page, newest-first, prev/next + "Page x of N") and Year + Month dropdown filters — a pure view transform over the already-served `membership_timeline.points` that narrows/pages only the rendered rows and recomputes no per-date size, entry, exit, or excluded-by-reason count.

## BACKGROUND

J-99 is one of the two remaining unbuilt buildable Must-haves (the other, J-100, is sequenced as iter-42 FULL per the iter-40 evaluator recommendation). iter-40 closed J-97/J-98 to passing on live evidence and recommended: "iter-41 LEAN — build J-99 (frontend-only view transform: pagination/filter over the already-served membership_timeline.points; no new endpoint, no second date state)." J-99 is explicitly NOT data-dependent (goal.md:2321-2327) and is a pure client-side view transform of the same payload the J-96 panel already renders — exactly the J-48 / J-55 / J-56 / J-64 leaderboard view-transform contract. The work is fully contained in the existing `MembershipTimelinePanel` (`apps/frontend/app/data/page.tsx:1015-1173`), which today renders `timeline.points.slice().reverse().map(...)` (every snapshot date at once); the `Select` control is already imported (`page.tsx:25`) and the coverage table's `useMemo` filter idiom (`page.tsx:1663`) is the pattern to reuse. Depth is lean: one frontend component, zero backend diff, prior verdict CONTINUE (not ESCALATE).

## IN SCOPE

### Backend
- [ ] None — zero backend diff. The served `membership_timeline.points` payload (`data_manager._membership_timeline` → `compute_coverage` → `GET /api/data`) is unchanged. Do NOT add an endpoint, a query param, or a stored value; do NOT touch `data_manager.py`, `universe_resolver.py`, the `MembershipTimelineCache`, or any engine module.

### Frontend (if applicable)
- [ ] In `MembershipTimelinePanel` (`apps/frontend/app/data/page.tsx`), insert a pure client-side view-transform layer between the served `timeline.points` and the per-date `timeline-table` render:
  - [ ] **Year + Month dropdown filters** built with the already-imported `Select` control. Options are derived (via `useMemo`) from the dates actually present in `timeline.points` — the Year options are the distinct calendar years in the payload; the Month options are 01–12 (label them by name or `MM`), constrained to months present (or show all 12 with an "All" sentinel). Both default to an "All" sentinel that selects every date. The filters narrow only the rendered rows; they read no new value and never re-derive a per-date count.
  - [ ] **Pagination at 10 rows per page**, newest-first, over the *filtered* set: prev / next controls (disabled at the bounds) and a "Page x of N" readout. Page resets to 1 when a filter changes. The page size is a single named module constant (e.g. `MEMBERSHIP_TIMELINE_PAGE_SIZE = 10`) in this frontend file — NOT an inline literal scattered through the render (mirror the existing view-transform components).
  - [ ] **Honest "x of N dates" readout** stating how many dates the current filtered/paged view shows out of the total `timeline.points.length` — so the view stays honest about what it hides. The controls compose: Year + Month + page narrow the same set.
  - [ ] **Honest empty state** when a filter combination matches zero dates (a clear "No snapshot dates match this filter" message) — never a fabricated row. The honesty labels (survivorship / warm-up / universe-relative, `timeline-label-*`) and the step-function chart stay rendered above the controls, unchanged.
  - [ ] Keep the existing per-date table columns (Snapshot date / Size / Entries / Exits / Excl. hist·price·liq) and `data-testid` hooks (`membership-timeline-panel`, `timeline-table`, `timeline-row-${date}`) intact; the rows shown are now the filtered+paged slice rather than the full reversed list. Add `data-testid`/`aria-label` hooks on the new prev/next buttons, the Year/Month `Select`s, and the "x of N" / "Page x of N" readouts so browser-QA can resolve them by aria-label (iter-27/28 lesson — never by visible `text()`).

### New user-facing capability
The user can page through the membership-timeline dates 10 at a time and jump to a specific year/month instead of scrolling the entire ~1369-date list — making the per-date entries/exits/exclusion history navigable.

### New information displayed
No new *value* — the displayed per-date sizes, entries, exits, and excluded-by-reason counts are the same stored J-93/J-94 values read verbatim. New *chrome* only: a "Page x of N" readout, an "x of N dates" honesty readout, and Year/Month filter labels.

### New user actions
Year dropdown, Month dropdown, Prev page button, Next page button.

### UI surface changes
The `/data` Data Manager page's `MembershipTimelinePanel` (the J-96 timeline) only. No other page changes.

### Product surface delta
The membership timeline goes from a single long scroll of every snapshot date to a paged, filterable list — the same data, more navigable. No score, return, membership, gate, or date-state behaviour changes.

### Blueprint conformance
No new surfaces and no nav-skeleton change. The work lands on the existing **Data Manager `/data`** home (Information Architecture, blueprint line 341), inside the existing J-96 `MembershipTimelinePanel`. The blueprint's J-99 plan (SESSION EXTENSION 2026-06-20, lines 294-300; iter-38 TARGET note "J-99 follows LEAN (frontend-only view transform, zero backend diff)", lines 311-312) already places J-99 here.

### Data-contract additions
None. J-99 introduces NO new displayed value and NO new endpoint — it is a pure client-side view transform over the already-served `membership_timeline.points` (the canonical value registered on the existing J-96 Data-Contract row, blueprint line 385: computed once by `data_manager._membership_timeline` → `compute_coverage`, served by `GET /api/data`). The pagination/filter controls re-order and narrow the client-rendered rows only; they read the registered canonical source and never introduce a second computation or a second fetch path. An additive annotation noting the J-99 view-transform is being appended to that existing J-96 row in `blueprint.md` (no new row, no human re-approval needed).

## OUT OF SCOPE

- Any backend change (endpoint, query param, cache, stored value, engine math). J-99 is frontend-only.
- J-100 (bounded-resource backend hardening + concurrency load test) — that is the separate FULL-depth iter-42 per the iter-40 recommendation. Do NOT fold any J-100 perf/concurrency/memory-cap work into this lean iteration.
- Any change to the membership-timeline step-function chart, the J-94 coverage diagnostic, the J-36 per-symbol coverage table, the J-95 backward-history control, or the rebuild/diagnostic banner.
- Any new date state. The Year/Month filters are list controls, NOT the global as-of switcher; they must not write to `useAsOf()` / `setAsOf`, the `?asof` URL param, or any provider state (J-18, critical).
- Re-triggering the J-85 `kind:rebuild` (~11h destructive; the data is correct — MEMORY.md). The served payload is read as-is.

## DEFINITION OF DONE

- [ ] J-99 passes via browser-qa-agent on LIVE rendered evidence: the `/data` membership timeline shows 10 rows per page newest-first with a working Prev/Next + "Page x of N", the Year and Month dropdowns narrow the rendered rows, the "x of N dates" honesty readout is present, and an empty filter combination renders an honest empty state (no fabricated row).
- [ ] Required-still-passing journeys remain green — especially J-96 (the timeline still renders the same per-date sizes/entries/exits/exclusions, now paged), J-94 (the coverage diagnostic above it is untouched), J-18 (still 0 native `input[type=date]` on `/data`; the new filters add no date input and no second date state), J-06 (the served membership counts are unchanged — a page's rows are a verbatim slice of `timeline.points`).
- [ ] No anti-goal violation introduced (no recompute in the view; no fabricated row; no second date selector; the page-size constant is named, not an inline magic literal in the frontend view-transform code).
- [ ] Unit tests pass; no regressions. Frontend type-check (`tsc`) clean. No backend code changed, so the iter-39 SCHEMA_VERSION green-suite gate stands for the byte-unchanged backend (this lean iter is NOT a GOAL_ACHIEVED candidate — J-100 is still unbuilt — so a flushed full backend suite is not load-bearing here).
- [ ] Dev handoff written at `docs/handoffs/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-41-dev.md`.

## TESTING REQUIREMENTS

- **Browser (LIVE render evidence required):** J-99 on `/data`. Bring up backend `:8835` (WAIT for `GET /api/health` "ready" — a cold pre-warm `/api/data` pays the documented ~10-12s warm cost; load `/data` ONCE, sequentially, never concurrently probe `/api/data` — MEMORY.md pool-exhaustion lesson). Bring up frontend `:3835` and Chrome `:9222`. **PLAN the Playwright fallback UP FRONT** (the Chrome MCP CDP WebSocket timeout emptied the evidence dir on iter-38 and iter-39; iter-34/37/40 succeeded only because Playwright was pre-planned — iter-39/iter-40 lesson). `md5sum` the evidence dir FIRST and reject any blank/skeleton/byte-identical frame (iter-18/33 lesson). Capture, scrolling the below-the-fold membership-timeline panel into the viewport and VIEWING the pixels (the `/data` panels sit below the fold — iter-18): (1) page 1 = 10 rows newest-first + "Page x of N"; (2) a different page via Next (a byte-DISTINCT frame showing older dates — md5sum the before/after pair, reject identical — iter-40 differential-pair lesson); (3) a Year (and Year+Month) filter applied, narrowing the rows + the "x of N dates" readout updating; (4) an empty filter combination → honest empty state. Re-smoke the required-still-passing co-located surfaces: J-96 (same per-date values, now paged), J-94 (coverage diagnostic renders), J-36/J-37/J-39 (`/data` panels), J-18 (0 native `input[type=date]` on `/data`), and a cross-page J-07 (Risk-Off → 0 Actionable) / J-06 smoke.
- **Unit/integration:** a frontend unit test (or component test under this frontend's test setup) for the new view-transform helpers — assert (a) filtering by Year/Month selects exactly the dates whose ISO date matches; (b) pagination yields ≤10 rows/page newest-first and "Page x of N" is `ceil(filteredCount/10)`; (c) the filtered+paged rows are a verbatim subset of `timeline.points` (no recomputation of `size`/`entries`/`exits`/`excluded`); (d) an empty filter combination yields zero rows + the honest empty state, never a fabricated row. If this frontend has no JS unit harness, assert these via the deterministic browser-QA legs above and DOM-text extraction, and note it in the dev handoff.
- **Error cases:** an out-of-range page request never renders a fabricated/blank row (clamp to bounds, disable Prev at page 1 / Next at last page); a Year+Month combination present in the dropdowns but matching zero rows renders the honest empty state; changing a filter resets the page to 1 (no orphaned page index past the new last page).

## NOTES

- **Lessons applied (surface to dev/reviewer/QA):**
  - iter-27 / iter-28b: a browser-QA "control does not act" FAIL on this codebase is repeatedly a SELECTOR false-negative — resolve the new Prev/Next buttons and Year/Month `Select`s by `aria-label`, NOT visible `text()` (their labels can live in nested spans). Before recording a regression, confirm the new view-transform code is the only diff.
  - iter-40 / iter-39 / iter-38: on this host the Chrome MCP CDP WebSocket timeout empties the evidence dir — the browser-qa-agent MUST pre-plan the Playwright fallback, and any differential "before/after" pair (here the page-1 vs page-2 frames) MUST be `md5sum`-checked and re-captured until they differ (a byte-identical pair proves nothing).
  - iter-18: the `/data` membership-timeline panel sits BELOW the fold — scroll the colored step chart + the paged table explicitly into the viewport and capture full-viewport; a blank dark frame or the wrong panel is a rejected capture, not evidence.
  - iter-36: a backend-only "Frontend Present: no" auto-skips browser-QA. This iter has a real frontend diff, so `Frontend Present: yes` is set above to force the live render step in THIS iteration (no separate re-verify round-trip needed).
  - iter-20 (no-magic-numbers spirit): the `10`-per-page count must be a named frontend constant, not an inline literal repeated in the render — keep the view-transform code self-documenting like the existing J-48/J-64 controls.
- **Single-source / no-recompute invariant (the J-99 crux):** the rendered page must be a verbatim slice/filter of `timeline.points`. The dev/reviewer must confirm in the diff that no per-date `size`, `entries`, `exits`, or `excluded` value is re-derived, summed, or restated in the view — only `Array.prototype.filter`/`slice`/`reverse` over the served objects. This is the same contract that protects J-96 and J-06.
- **J-18 critical invariant:** grep the diff to confirm the new filters/pagination add NO new `useState` holding a date that is read as an as-of, NO `setAsOf` call, NO `?asof` write, and NO `window`/`document` keydown listener; the Year/Month `Select`s and the page index are local list-view state only (like the coverage table's filter `useMemo`), never the global date.
- **GOAL_ACHIEVED accounting:** after J-99 closes green, the only remaining unbuilt buildable Must-have is J-100 (FULL, iter-42 per iter-40); J-22/J-23/J-24 stay honestly blocked-NA / non-vetoing (goal.md:105-108). So iter-41 is NOT a GOAL_ACHIEVED candidate — do not block the evaluator on a full backend suite (iter-11/29 lesson); the backend is byte-unchanged and the iter-39 green-suite gate stands.
