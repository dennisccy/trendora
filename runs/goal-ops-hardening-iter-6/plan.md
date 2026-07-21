# goal-ops-hardening-iter-6 Execution Plan

## Context (read before building)

This is a **lean-scoped, frontend-only** iteration closing the ops-hardening session's last failing
Must-have journey, J-06 ("Pages load only what they need"). iter-5 fixed the one real backend violation
(`GET /api/backtest`, 34.77s → 0.138s via `ForwardAggregateCache`) and left every page passing on curl
measurement — but browser-qa then measured `GET /api/indexes?full=true` at 1.68–2.19s real-browser
(budget ≤1.5s) against curl's 0.79–0.95s, and separately flagged `GET /api/data/availability` at
2.9–3.0s browser vs ~1.0s curl (previously unbudgeted). Root cause (converged across QA/closure/
ux-regression/audit): Chrome's 6-connections-per-origin cap queues the page's near-simultaneous
same-origin on-load calls under HTTP/1.1 uvicorn — not a slow endpoint (curl's own baseline is
comfortably under budget). **The fix is request scheduling/timing only — no backend code, no new
endpoint, no computed-value change.**

Confirmed by reading the current code:
- `apps/frontend/app/page.tsx`'s own `useEffect` fires `fetchDashboard` first, then sequentially
  `await`s `fetchMarketPhase` → `fetchSectors` → `fetchThemes` inside the `.then` (already staggered,
  not a burst).
- `apps/frontend/components/phase-cross-view-card.tsx`'s `PhaseCrossViewCard` (mounted on `/` by
  `page.tsx`, below the fold) has its **own independent `useEffect`** that fires on mount **in parallel
  with** the page's own effect, running `Promise.all([fetchIndexes(...,true), fetchRegimeHistory(...,true),
  fetchMarketPhase(...,true)])` — 3 concurrent requests the instant the page mounts, competing with
  `fetchDashboard` and the initial Next.js JS/CSS chunk requests for the same 6-connection budget. This
  is the confirmed contention source for `/api/indexes?full=true`.
- `apps/frontend/components/major-indexes-card.tsx` exists but is **dead code** — confirmed via repo-wide
  grep, no import references it anywhere. It is NOT part of the Dashboard's current fetch fan-out and does
  not need to be touched (the phase spec lists it only as "as needed").
- `apps/frontend/app/data/page.tsx`'s `DataManagerPage` fires `loadOverview()` (→ `fetchDataCoverage`)
  and `loadAvailability()` (→ `fetchDataAvailability`, consumed by `availability-heatmap.tsx`, which takes
  `state` as a prop and does no fetching itself) **in the same `useEffect`, back-to-back, uncoordinated**
  — plus this page independently mounts `IndexVendorPanel` and `MacroFeedPanel`, each with their own
  fetch-on-mount. This is a wide on-load fan-out; `GET /api/data/availability` is the newly-flagged
  violator.

## What to Build

- **Dashboard contention fix**: defer/stagger `PhaseCrossViewCard`'s `Promise.all` fetch (indexes-full +
  regime-history-full + market-phase-full) relative to the page's own on-mount `fetchDashboard` call —
  e.g. a short deferral (microtask/rAF/small timeout) or gating the card's fetch on the page's own fetch
  starting/settling — so the initial same-origin connection burst (Next.js asset loads + `fetchDashboard`)
  clears before the card's 3 requests fire. Goal: `GET /api/indexes?full=true` real-browser response time
  ≤1.5s (3/3 reloads).
- **Data Manager contention fix**: apply the same staggering discipline to `DataManagerPage`'s
  `loadAvailability()` relative to `loadOverview()` (and any other on-mount panel fetches, e.g.
  `IndexVendorPanel`/`MacroFeedPanel`, if they measurably contend) so `GET /api/data/availability`'s
  real-browser response time falls within its newly-committed budget.
- **Preserve every existing loading/error/empty affordance unchanged** — `PhaseCrossViewCard`'s
  `"loading"`/`"error"`/`"empty"` states and the availability heatmap's own spinner/error/empty states
  must render identically; only WHEN/how the underlying fetch fires changes, never the component's render
  contract. An in-flight deferred fetch that gets aborted (e.g. a fast as-of toggle unmounting the effect)
  must still show the existing honest error/loading state, never a blank or frozen frame (TC-10).
- **Budgets artifact**: commit `GET /api/data/availability`'s first budget row (real-browser-measured)
  into `reports/perf-budgets.md` — the SAME single file, no second budgets artifact — at the generic
  ≤1.5s endpoint-budget class already used throughout the file, unless the live post-fix measurement
  requires a documented adjustment (state the reason inline if so).
- **Full re-measurement**: re-measure and record all 11 J-06 pages' TTI + on-load latencies in
  `reports/perf-budgets.md` using REAL BROWSER measurement (Network-tab timing, 3 reloads minimum) for
  at least the two previously-violating endpoints (`/api/indexes?full=true`, `/api/data/availability`).
  Curl alone is not sufficient evidence (iter-5 lesson).
- **Golden-script repair**: fix `runs/goal-session-ops-hardening/journey-scripts/J-01.json` step 6. It
  currently does `goto /scanner-runs` and asserts `"text": "2026-05-15"` — a fixed, unrelated historical
  date now buried past a 750-row unpaginated fold, with no connection to this script's own action (steps
  2–4 submit a weekend-only 2026-05-02→2026-05-03 backfill, which is zero-work and creates NO new
  `/scanner-runs` row at all). Rewrite step 6 to assert against `/data`'s own persisted run-history panel
  entry for the run this script's steps 2–4 submitted (e.g. re-assert on `/data` — or a targeted selector
  in the run-history list — for content this run itself produced: its date range and/or its zero-work
  "2 non-trading" outcome persisted in history), per the iter-5 lesson ("assert on data the journey's own
  action produces," not a fixed historical row). `J-03.json` is NOT touched (unchanged, already green).
- **Test run carried over from iter-5**: run `pytest tests/test_api_backtest.py tests/test_mcp_window.py -v`
  (TMPDIR set per the environment note below) to completion — the `loaded_engine`-dependent suite iter-5
  started but killed after ~9 minutes (background contention with its own perf measurement). Report full
  pass/fail results in the dev handoff.

## Explicitly OUT OF SCOPE (do not touch)

- Any new backend endpoint or second serving path for an already-registered Data Contract value. Every
  affected value (dashboard, market phase, sectors, themes, indexes, regime history, coverage/
  availability) keeps its existing single computing module + single serving endpoint — this is a
  frontend request-timing change only.
- HTTP/2 / TLS on the uvicorn launcher.
- `/api/runs`'s N+1 pattern (measured in-budget in iter-5, "do not redo").
- `readiness.py` / `health-badge.tsx` (B3/F1, iter-4 — settled, "do not redo").
- `ForwardAggregateCache` / `forward_aggregates_cached` (iter-5 — shippable as-is, "do not redo").
- `demo.sh ops-hardening --session-live` `[NEW]` walkthroughs for J-05/J-06 — deferred to session-closeout
  showcase artifacts, not this iteration's DoD.
- `max_range_days`, `snapshot_cadence`, or any other J-01/J-03 config/data-jobs surface — both journeys
  already pass; untouched.
- **If the live post-fix measurement shows the fetch-scheduling change alone is insufficient** to bring
  `/api/indexes?full=true` under 1.5s, do NOT fall back to a new/combined endpoint — stop and flag it in
  the dev handoff for a fresh decomposer pass rather than expanding scope (this session's established
  contingent-fix discipline).

## Agents Required

- backend-data: no — zero backend endpoint/model/computing-module changes are in scope this iteration;
  the only backend-adjacent action is *running* the existing `pytest tests/test_api_backtest.py
  tests/test_mcp_window.py -v` suite to completion (no backend source edit).
- frontend-ux: yes — `phase-cross-view-card.tsx` (fetch-timing change), `app/page.tsx` (coordination point
  if needed), `availability-heatmap.tsx`/`app/data/page.tsx` (fetch-timing change). No new UI surface, no
  new user-facing capability — purely fetch scheduling behind the existing render contract.

## Frontend Present: yes

## Files to Create/Modify

- `apps/frontend/components/phase-cross-view-card.tsx` — defer/stagger the `Promise.all` on-mount fetch
  relative to the Dashboard's own initial fetch burst; preserve `loading`/`ok`/`empty`/`error` states and
  `AbortController` cleanup on unmount/deps-change exactly as today.
- `apps/frontend/app/page.tsx` — touch ONLY if a coordination signal (e.g. a ready flag passed to
  `PhaseCrossViewCard`, or a small scheduling primitive) is needed to implement the stagger; otherwise
  leave unchanged (its own fetch chain is already sequential, not a burst).
- `apps/frontend/app/data/page.tsx` and/or `apps/frontend/components/availability-heatmap.tsx` — stagger
  `loadAvailability()` relative to `loadOverview()` (and any other measurably-contending on-mount fetch on
  this page); preserve the heatmap's existing loading/error/empty rendering untouched.
- `reports/perf-budgets.md` — new dated section(s): the first `GET /api/data/availability` budget row
  (real-browser-measured) + the full 11-page J-06 re-measurement pass (real-browser Network-tab timing,
  ≥3 reloads for the two previously-violating endpoints).
- `runs/goal-session-ops-hardening/journey-scripts/J-01.json` — rewrite step 6 to assert on the
  submitting run's own persisted `/data` history entry instead of a stale fixed `/scanner-runs` date.
- `docs/handoffs/goal-ops-hardening-iter-6-dev.md` — dev handoff (required by DoD): document the fix, the
  live browser measurements (pre/post if a real violation was found), the TC-9 pytest result, and an
  honest note if the frontend fix alone proved insufficient (see out-of-scope contingency above).

No backend Python file should appear in the diff except test-run evidence (no source edit expected).

## UI Evolution

- New user-facing capability: none — same Dashboard and Data Manager surfaces, same displayed values.
- New information displayed: none.
- New user actions: none.
- UI surface changes: none — only WHEN each on-load request fires changes; every card/panel keeps its
  existing appearance, content, and states (loading skeleton, error card, empty state).
- Navigation changes: none.

## Visual Requirements

- Component patterns: no new components; reuse the existing `Card`/skeleton (`animate-pulse`)/error-card
  patterns already in `phase-cross-view-card.tsx` and `availability-heatmap.tsx` verbatim.
- Layout: unchanged — Dashboard (`/`) and Data Manager (`/data`) keep their current page layout and card
  order.
- Key visual effects: none introduced; the existing `h-[28rem] animate-pulse` skeleton (cross-view chart)
  and the availability heatmap's `Loader2` spinner remain the loading affordance during any deferred fetch
  window — must never render as blank while a fetch is intentionally delayed.
- States to handle: loading (deferred period must still show the existing skeleton/spinner, never a blank
  gap before the fetch fires), error (unchanged messaging), empty (unchanged), and the new abort-mid-flight
  case (TC-10: a fast as-of toggle that unmounts/aborts a deferred or in-flight fetch must still resolve to
  the existing honest error/loading state, never a stuck frozen frame).

## Key Test Scenarios

- TC-1/TC-3: warm prod-mode (`scripts/start-backend.sh` / `scripts/start-frontend.sh`, never `dev.sh`),
  real Chrome, Dashboard (`/`) loaded/reloaded 3x — `GET /api/indexes?full=true` Network-tab timing ≤1500ms
  all 3 trials; all 11 J-06 pages' TTI + on-load latencies stay within their `reports/perf-budgets.md`
  budgets (no new violation introduced elsewhere by the scheduling change).
- TC-2/TC-4: Data Manager (`/data`) loaded/reloaded 3x — `GET /api/data/availability` within its newly
  committed budget all 3 trials; `reports/perf-budgets.md` gains exactly one new row for it (no second
  budgets file anywhere in the repo).
- TC-5: `/api/dashboard`, `/api/market-phase`, `/api/sectors`, `/api/themes`, `/api/indexes?full=true`,
  `/api/regime-history?full=true`, `/api/market-phase?full=true`, `/api/data/availability` — each payload
  byte-identical to its pre-fix response at a fixed as-of (timing/ordering changed only, never values).
- TC-6/TC-7: `J-01.json`'s rewritten step 6 replays deterministically (all 6 steps pass, zero manual
  adjudication); `J-03.json` unchanged and stays green.
- TC-8: J-04/J-05 (no golden script on file) pass via browser-qa's LLM fallback lane against their
  numbered acceptance steps in `docs/goal.md`, moving both out of `unknown`.
- TC-9: `pytest tests/test_api_backtest.py tests/test_mcp_window.py -v` (TMPDIR set) runs to completion,
  zero failures.
- TC-10: `PhaseCrossViewCard`'s deferred/staggered fetch, aborted mid-flight (fast as-of toggle unmounts
  the effect) — shows the existing honest error/loading state, never blank/frozen.
- TC-11: real backend restart via `scripts/start-backend.sh` — first `GET /api/health` 200 within 5s
  (confirms this frontend-only change does not affect the boot budget; expected trivially true since no
  boot-path file is touched).

## Environment Note (for the developer agent)

Before running any test or command that writes temp files, export:
```
export TMPDIR="/home/dennis-chan/.cache/iad/iad.goal-ops-harde-c41f8e4e.11312" TMP="/home/dennis-chan/.cache/iad/iad.goal-ops-harde-c41f8e4e.11312" TEMP="/home/dennis-chan/.cache/iad/iad.goal-ops-harde-c41f8e4e.11312"
```
Per project convention (`goal-mode-pump-dont-run-full-suite` lesson), do not run the full backend suite —
only the two named test files (TC-9) plus any targeted frontend/backend tests directly touching changed
code.
