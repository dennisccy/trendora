# Phase goal-mcp-loop-iter-25 — What to Click (Operator Verification Guide)

**Phase:** goal-mcp-loop-iter-25
**Time required:** ~5 minutes
**Written by:** ui-test-designer

---

## Prerequisites

- Frontend running at `http://localhost:3255`
- Backend running at `http://localhost:8255`
- Ability to fully stop and restart the backend process (ask your engineer for the restart command — e.g. `scripts/start-backend.sh` — if you don't run it yourself). This is required because this iteration's fix is specifically about what happens the moment the backend restarts; there is no way to verify it without an actual restart.
- No login and no special seed data required

---

## Verification Steps

1. Fully stop the backend service, then start it fresh (a cold restart, not a reload)
   - **Expect:** the old process exits and a new one starts listening again within a few seconds

2. Immediately open a **new** browser tab and go straight to `http://localhost:3255/data` — this must be the very first page you open against the freshly-restarted backend
   - **Expect:** within about 10 seconds, the "Data Manager" page fully loads, showing a "Dataset coverage" panel and a "Storage footprint" panel full of real numbers
   - **Broken looks like:** a blank white tab, a browser "can't reach this page" error, or the tab hanging far longer than 10 seconds with nothing appearing — this is the exact crash this iteration exists to fix

3. Open `http://localhost:3255/stocks` in the same or a new tab
   - **Expect:** the stock leaderboard loads normally with a full table of rows — this confirms the backend survived step 2 and is still serving other pages, not just the one you happened to load first

4. Repeat steps 1–3 one more time (restart the backend again, load `/data` first, then `/stocks`)
   - **Expect:** the exact same good result both times — no crash on either run

5. On the `/data` page, look at the "Storage footprint" panel
   - **Expect:** four values are shown — "Database file" (a size around "1.22 GB"), "Price bars", "Scanner rows", "Forward returns" — each a real number, never "—" or blank

6. Now stop the backend and leave it stopped, then reload `http://localhost:3255/data`
   - **Expect:** a single boxed message reading "Backend unavailable" with an explanation appears — not a blank page and not more than one error box
   - **Broken looks like:** a completely blank white page, or your browser's own generic error page instead of Trendora's styled error card

7. Restart the backend one final time so the app is left working, then click on any stock from the `/stocks` leaderboard (e.g. AAPL)
   - **Expect:** the stock detail page loads with a price chart — confirms ordinary navigation still works after the fix

8. On that stock's page, click the "Full" history toggle if visible, then click "Recent"
   - **Expect:** the chart extends to many years of history on "Full" and collapses back on "Recent," with no crash either way

---

## What "Working Correctly" Looks Like

- Restarting the backend and immediately opening `/data` never produces a blank page or a browser connection error — the Data Manager page loads with real coverage and storage numbers every time, on repeated restarts
- When the backend is genuinely down, `/data` shows exactly one clear, styled "Backend unavailable" message — never a blank crash page
- Every other page (`/stocks`, stock detail pages) keeps working normally after the restart — the fix did not disturb anything else

## Common Issues

- **Blank page / browser connection-error after restarting and loading `/data` first**: this is the regression iter-25 was meant to fix. Treat it as a FAIL and check that `config.yaml` still has `mmap_size_bytes: 0` around line 108.
- **Blank white page (instead of a "Backend unavailable" message) when the backend is stopped**: a separate anti-goal violation — report it even if step 2/4 passed.
- **`/stocks` or a stock detail page fails to load after the restart**: means the backend did not fully survive the cold `/data` request even if `/data` itself appeared to load — restart again and recheck.
