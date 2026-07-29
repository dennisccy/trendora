# Phase goal-ops-hardening-iter-33 — What to Click (Operator Verification Guide)

**Phase:** goal-ops-hardening-iter-33
**Time required:** ~5 minutes
**Written by:** ui-test-designer

---

## Prerequisites

- Frontend running at `http://localhost:3255`, started via `scripts/start-frontend.sh` (the
  launcher script this iteration fixed — NOT `scripts/dev.sh`, which is unchanged and still runs
  dev mode on purpose). If you're not sure which launcher started your instance, check the
  terminal that launched it for a `next build` step followed by `next start ... Ready in ...ms` —
  that confirms prod mode.
- Backend running and healthy (its own terminal should show a fast `GET /api/health` response).
- No login is required — this app has no auth.
- No new test data is required — this iteration changes only how the frontend is served, not any
  page's data.

---

## Verification Steps

1. Open `http://localhost:3255/` in your browser
   - **Expect:** The Dashboard loads with the heading "Dashboard" and subtitle "The daily snapshot
     at a glance". No blank page, no red error screen.

2. Open your browser's DevTools console (press F12, then click the "Console" tab) and look at the
   bottom corners of the page
   - **Expect:** No colored pill/badge button in a bottom corner of the page, and no full-screen
     overlay with a stack trace. This overlay is Next.js's dev-mode error indicator — it should
     never appear now that the launcher genuinely serves a production build. Its presence here
     means the fix did not take effect for this instance.

3. Click "Stocks" in the left sidebar
   - **Expect:** Page navigates to `http://localhost:3255/stocks`; heading "Stocks" is visible;
     the leaderboard table populates with ranked rows.

4. Type "AAPL" into the search box at the top of the leaderboard, then click the "AAPL" row
   - **Expect:** Page navigates to `http://localhost:3255/stocks/AAPL`; heading "AAPL" is visible;
     three score cards labeled "Leadership", "Entry Quality", and "Risk" render with values.

5. Click "Backtest" in the left sidebar
   - **Expect:** Page navigates to `http://localhost:3255/backtest`; heading "Backtest" is
     visible; the "As-of scan summary" section shows content (not blank).

6. Click "Data Manager" in the left sidebar, then scroll down to the "Run history" panel
   - **Expect:** Page navigates to `http://localhost:3255/data`; heading "Data Manager" is
     visible; the "Run history" panel renders (either past jobs listed, or the message "No fetch /
     backfill runs yet" — either is fine, a blank panel with no message is not).

7. Click "Research" in the left sidebar, then click the "Regime Lab" card
   - **Expect:** First click lands on `http://localhost:3255/research` with a card titled "Regime
     Lab" visible; second click navigates to `http://localhost:3255/research/regime-lab` with
     heading "Research — Regime Lab" visible. (Confirms the existing nav path still works
     unchanged — 2 clicks from Dashboard.)

8. Refresh the current page (press F5 or Cmd+R)
   - **Expect:** Page reloads cleanly with the same content as before the refresh — same heading,
     same table rows. Still no dev-mode overlay pill from step 2.

---

## What "Working Correctly" Looks Like

- Every page you visit loads with its real content — no blank screens, no red error boxes.
- You never see a colored pill/badge in a page corner or a full-screen stack-trace overlay — that
  overlay is the tell-tale sign of the old (broken) dev-mode launcher; its absence is the direct
  proof this iteration's fix took effect.
- Data (leaderboard rows, scores, backtest figures) looks exactly as populated and sensible as it
  did before — this iteration changed HOW the frontend is served, never WHAT data it shows.

## If Something Looks Wrong

- **A colored pill/badge appears in a page corner, or a full-screen error overlay with a stack
  trace**: the instance you're testing was started with `scripts/dev.sh` (dev mode), not
  `scripts/start-frontend.sh` (the fixed prod-mode launcher) — restart it with the correct script
  and retest.
- **Blank page / "Application error" screen**: check that the backend is running and healthy —
  open a new tab to its health endpoint (the backend's own startup terminal output shows the exact
  URL, typically `http://localhost:<port>/api/health`) and confirm it returns quickly with no
  error.
- **Page loads but a table/panel never finishes loading (infinite spinner)**: check the backend
  terminal for errors; this would indicate a backend problem, not something this iteration's
  launcher fix touches.
