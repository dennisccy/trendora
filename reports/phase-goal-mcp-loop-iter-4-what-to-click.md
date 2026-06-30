# Phase goal-mcp-loop-iter-4 — What to Click (Operator Verification Guide)

**Phase:** goal-mcp-loop-iter-4
**Time required:** ~5 minutes
**Written by:** ui-test-designer

---

## Prerequisites

- Frontend running at `http://localhost:3255`
- No login required — all changed surfaces are public read-only pages
- No seed data needed — the backend provides its own certified-claims ledger

---

## Verification Steps

1. Navigate to `http://localhost:3255/` in your browser.
   - **Expect:** The Dashboard loads. The Market Regime card is visible and shows the label "Risk-on" and the score "76.05". Below the component-breakdown disclosure area in that card, the link "See evidence proven in this regime →" is visible and clickable.
   - **Broken looks like:** The link text is absent, the card is blank, or you see an error message instead of the regime score.

2. Click "See evidence proven in this regime →" inside the Market Regime card.
   - **Expect:** The browser navigates to `http://localhost:3255/evidence`. The URL in the address bar changes to `/evidence`. Two claim rows are visible on the page.
   - **Broken looks like:** Clicking does nothing, or the browser goes to a 404 page, or navigates anywhere other than `/evidence`.

3. On the Evidence page, scroll down to the second claim row (below the first/leadership row).
   - **Expect:** The second row title reads "Breakout-watch setup". Directly beneath the title, a subtitle reads "Out-of-sample edge in the Risk-on regime". In the row header next to the green "PASS" verdict badge, a badge reads "Regime: Risk-on".
   - **Broken looks like:** The title reads "Unmapped signal", no subtitle is present, or no "Regime:" badge appears.

4. On the same Breakout-watch row, read the holdout edge and linkback text.
   - **Expect:** The edge value reads "+6.12%" and the comparison reads "vs SPY". The registration date reads "2026-06-30". The linkback line reads "Backs: Research event-study lab →".
   - **Broken looks like:** The linkback reads "Backs: Stocks leaderboard →", or the edge value is blank or shows a different number.

5. Click "Backs: Research event-study lab →" on the Breakout-watch row.
   - **Expect:** The browser navigates to `http://localhost:3255/research/event-study`. The URL in the address bar ends in `/research/event-study`.
   - **Broken looks like:** Browser navigates to `/stocks`, or stays on `/evidence`, or goes to a 404.

6. Press the browser Back button to return to `http://localhost:3255/evidence`. Scroll to the first claim row (the leadership row at the top of the page).
   - **Expect:** The first row has NO "Regime:" badge in its header. The linkback reads "Backs: Stocks leaderboard →". The edge value reads "+6.36%". The verdict badge reads "PASS". These values are byte-identical to iteration 3.
   - **Broken looks like:** A "Regime:" badge appears on the leadership row, or the linkback says "Research event-study lab", or the "+6.36%" value has changed.

7. Navigate to `http://localhost:3255/` and confirm the Market Regime card is intact.
   - **Expect:** The regime label still reads "Risk-on" and the score still reads "76.05". The "See evidence proven in this regime →" link is still present below the component breakdown. No layout breakage from the new link addition.
   - **Broken looks like:** The regime score or label is missing, blank, or changed; or the new link overlaps other card content.

---

## What "Working Correctly" Looks Like

- Dashboard Market Regime card shows both the regime data ("Risk-on", "76.05") AND the new "See evidence proven in this regime →" link below the component breakdown — two things coexisting in the same card
- Evidence page second row shows three new elements simultaneously: the "Regime: Risk-on" badge in the header, the "Breakout-watch setup" title with its "Out-of-sample edge in the Risk-on regime" subtitle, and the "Backs: Research event-study lab →" linkback pointing to `/research/event-study`
- Evidence page first row is visually identical to iteration 3 — no "Regime:" badge, same "+6.36%" edge, same "Backs: Stocks leaderboard →" linkback

## Common Issues

- **Evidence page shows "Unmapped signal"**: The frontend helper `claimSurface()` / `regimeLabel()` in `apps/frontend/lib/evidence.ts` may not have been rebuilt. Restart the frontend dev server.
- **"See evidence proven in this regime →" link missing from Dashboard**: The `RegimeGlanceCard` component in `apps/frontend/app/page.tsx` may not have hot-reloaded. Hard-refresh the browser (Ctrl+Shift+R or Cmd+Shift+R).
- **Blank evidence page or 500 error**: Check that the backend is running (`curl http://localhost:8000/api/evidence` should return a JSON object with a `claims` array of 2 entries).
- **Linkback still points to /stocks after clicking**: Verify you are clicking the second (Breakout-watch) row linkback, not the first (leadership) row linkback — both are on the same page.
