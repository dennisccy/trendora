# Phase goal-ops-hardening-iter-24 — What to Click (Operator Verification Guide)

**Phase:** goal-ops-hardening-iter-24
**Time required:** ~5 minutes (may take a couple of extra retries — see step 3)
**Written by:** ui-test-designer

---

## Prerequisites

- Frontend running at `http://localhost:3255`
- Backend running and reachable (no login required)
- At least a handful of historical snapshot dates already exist in the app (any normally-seeded instance
  has this)

**One thing to know before you start:** once the backend is warmed up, the top bar only re-checks itself
every 30 seconds (it slows down once things are "Ready" — this is normal, not a bug). Instead of waiting
and watching, **refresh the page (F5)** whenever a step below says to check for something — that forces an
immediate re-check instead of waiting up to 30 seconds.

---

## Steps

1. Open `http://localhost:3255/` in your browser
   - **Expect:** Dashboard loads. Top-right corner shows a pill reading "Ready" (or briefly
     "Initializing…" on a very fresh start). No error page.

2. Click "Backtest" in the left sidebar
   - **Expect:** Page loads at `http://localhost:3255/backtest`. Top-right shows a small "Latest" badge
     next to a calendar icon.

3. Click the "◀" left-arrow button just left of that calendar icon, once
   - **Expect:** The badge changes to "Viewing as-of `<some date>` (historical)" in amber. Wait 3 seconds,
     then press F5 to refresh. Look at the top-right corner again: you should see a NEW badge appear next
     to "Ready", reading "background compute running (1)". **If it doesn't appear**, click "◀" again to
     try an older date, wait 3 seconds, and refresh again — repeat up to ~5 times. (Some dates are already
     computed from earlier use and correctly won't trigger anything — that's expected, not broken.)

4. Once you see "background compute running (1)", immediately click "Data Manager" in the left sidebar
   - **Expect:** Page loads at `http://localhost:3255/data`. Scroll all the way down to the BOTTOM of the
     page — the new panel is the very last one. You should see a panel titled "Background compute" with a
     row showing "as-of `<the date you picked>`", an "elapsed …s" value, and a "horizons X/Y" value where
     X is less than Y.

5. Wait about 20-30 seconds, then refresh the page (F5) and scroll to the bottom again
   - **Expect:** The panel now shows "Last outcome" with a green "Completed" badge, the same as-of date,
     and a duration (e.g. "12.3s"). The row from step 4 is gone — the window finished.

6. Go back to `http://localhost:3255/` (or any page) and refresh
   - **Expect:** The "background compute running (N)" badge from step 3 is now GONE. Only the normal
     "Ready" pill remains — confirming the indicator disappears once the work is done.

7. On `/data`, scrolled to the bottom of the "Background compute" panel
   - **Expect:** A small gray sentence is visible: "Since the last backend restart — this history is
     process-lifetime only, never persisted." This line is always there, in every state of the panel.

8. Scroll up one panel from "Background compute" on `/data`
   - **Expect:** The panel directly above it is "Run History", showing its usual list of past data jobs —
     unchanged from before this update. Nothing above "Background compute" was removed or reordered.

---

## What "Working Correctly" Looks Like

- A "background compute running (N)" badge appears next to the existing readiness pill ONLY while a
  historical backtest is actively being computed in the background, and disappears once it's done.
- The "Background compute" panel at the bottom of `/data` shows live progress while a window is active,
  then flips to a "Completed" summary with a real duration once it finishes — never a made-up
  finish-time estimate or a percentage.
- Everything else on the site (the readiness pill's own states, every other panel on `/data`, the Backtest
  scorecard itself) looks and behaves exactly as it did before this update.

## Common Issues

- **Badge/panel never appears no matter which historical date you try:** confirm the backend is actually
  running (`curl http://localhost:8000/api/health` should return JSON, not a connection error). If the
  backend is up but truly every date you try is already cached, this is a timing/test-data limitation, not
  necessarily a broken feature — flag it for a developer to force-trigger one via the backend's
  test-only hook rather than concluding the UI is broken from this alone.
- **You saw the badge once but "lost" it:** remember the top bar only re-checks every 30 seconds once
  "Ready" — refresh the page (F5) instead of waiting and watching; don't conclude it's broken from one
  missed look.
- **The "Background compute" panel looks the same before/after in a screenshot:** it sits at the very
  bottom of a long `/data` page — make sure you actually scrolled down (or captured the full page) before
  comparing two screenshots; a screenshot of just the top of the page will look identical every time.
- **Blank page / error screen anywhere:** confirm the backend is running
  (`curl http://localhost:8000/api/health`).
