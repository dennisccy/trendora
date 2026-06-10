# Phase goal-i_can_see_the_wealthy_future_forever-iter-28 — User-Visible Changes

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-28
**Date:** 2026-06-10
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

- Users can now see the true backend state at a glance from any page — the top-bar badge shows one of three honest states: **Ready** (green dot), **Initializing… history n/m** (amber animated dot with warm-up progress in monospace), or **Backend unavailable** (red dot), instead of the previous binary "Backend OK / Backend unavailable".
- Users can now use the core pages (Dashboard, Stocks, Sectors, Themes, Stock Detail) almost immediately after the server starts from a cold or fresh database — the server begins answering within the readiness budget (about one snapshot compute, ~30 s on a cold DB) instead of making every page unavailable for minutes during the full historical backfill.
- Users can now observe live warm-up progress in the badge — e.g. "Initializing… history 4/11" — so they know exactly how much historical evidence is still loading and can judge when analytics pages will be ready.
- Users can now see a clear, honest "Warming up — historical evidence still loading (n/m)" state on the Backtest page while the background warm-up is running, so they never mistake a missing or partial result for an error.
- Users can now see the same warming state on the Research — Factor Lab page (covering all three labs: Factor Lab, Combination Lab, Setup & Pattern event study) during background warm-up.
- Both the Backtest and Research pages automatically populate with full results the moment the warm-up finishes — no page refresh or manual action is needed.

---

## What Changed in the Visible UI

- The top-bar health badge now displays three states instead of two: it gains an "Initializing…" amber state with a live monospace "history n/m" progress counter and an animated pulse dot, in addition to the existing green "Ready" and red "Unavailable" states. The badge lives in the same position (next to the global as-of switcher in the header shell).
- The Backtest page (`/backtest`) now renders a "Warming up — historical evidence still loading (n/m)" card in place of the forward-test scorecard area whenever the backend warm-up is still in progress; the card is replaced automatically by the full scorecard once warm-up completes.
- The Research page (`/research`) now renders the same warming card in place of the Factor Lab, Combination Lab, and event study sections during warm-up; all three labs auto-populate when the badge flips to Ready.
- The initial badge load state now shows "Checking backend…" (a neutral default dot) while the first health poll is in flight, rather than immediately showing an error or an undefined state.

---

## What Old Behavior Changed

- **Top-bar health badge:** previously showed only "Backend OK" (green) or "Backend unavailable" (red) with no progress information. Now shows three states including a live Initializing state with warm-up progress.
- **Backend startup (cold/fresh database):** previously the server blocked all requests — including `/api/health` — until the full multi-year historical walk-forward backfill completed (~several minutes). Now the server starts answering within about one snapshot compute (~30 s on a cold DB) and runs the remainder in the background.
- **Backtest page on a warming backend:** previously the page would show the generic "Backend unavailable" error card if the analytics API had not yet warmed. Now it shows an explicit "Warming up (n/m)" state that is clearly not an error, and auto-populates rather than requiring a reload.
- **Research page on a warming backend:** same change as Backtest — the warming state replaces the error card during background warm-up and auto-populates on completion.
- **`GET /api/health` response:** now also returns a `readiness` field (`ready` / `initializing` / `unavailable`), a `warmup` object with `{done, total, status, message}`, and config-derived `poll_interval_seconds` / `poll_idle_interval_seconds`. All previous fields are unchanged.

---

## Not Visible Yet

- The pre-computed snapshot seed (an optional accelerator that would make even a fully cold first boot near-instant) was intentionally deferred and is not built. On a truly fresh database the single latest-snapshot compute before serving takes ~29 s — right at the 30 s readiness budget.
- A faster (memoized/vectorized) scan engine (Capability #33) that would shorten the per-date scan from ~12–40 s per date is deferred for a future iteration; the full background warm-up currently takes several minutes on a cold DB.
