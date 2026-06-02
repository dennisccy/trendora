# Phase goal-i_can_see_the_wealthy_future_forever-iter-10 — What to Click (Operator Verification Guide)

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-10
**Time required:** ~5 minutes
**Written by:** ui-test-designer

---

## Prerequisites

- Frontend running at `http://localhost:3835`
- Backend running at `http://localhost:8000` with the seeded DB (factor + forward-return data present)
- No login required

---

## Verification Steps

1. Open `http://localhost:3835/` in your browser
   - **Expect:** Dashboard loads, no error page; a left sidebar is visible.

2. In the left sidebar, find the "Research" item (microscope icon) between "System Health" and "Watchlist", and click it
   - **Expect:** URL becomes `http://localhost:3835/research`; the heading "Research — Factor Lab" appears.
   - **Broken looks like:** No "Research" entry in the sidebar, or clicking it 404s.

3. Wait for the loading bars to resolve, then look at the page body
   - **Expect:** A warning-coloured banner "Survivorship bias · universe-relative · descriptive", a decile table with rows D1–D10, and a "Rank-IC" card with a big signed number.

4. Check the decile table column headers
   - **Expect:** Headers read "Decile", "Factor range", "Mean fwd return", and "Risk-adjusted (downside)". The 4th header must say "(downside)" — not "(volatility)".

5. Confirm the factor dropdown shows "Leadership score" and the highlighted horizon button is "20d"
   - **Expect:** Dropdown selected value = "Leadership score"; the "20d" button is filled/highlighted among 1d / 5d / 10d / 20d / 60d.

6. Open the factor dropdown and select "ATR % (volatility level)"
   - **Expect:** The table values change and the metadata line updates to "Factor: ATR % (volatility level) (volatility · lower better)". The Rank-IC sentence now mentions "ATR % (volatility level)".
   - **Broken looks like:** Table values are identical to before (no re-point), or values look invented.

7. Click the "60d" horizon button
   - **Expect:** "60d" becomes highlighted, "Horizon: 60d" shows in the metadata line, and at least one "Mean fwd return" value changes.

8. Scan the whole `/research` page for any date picker / calendar / "as-of" control
   - **Expect:** There is NONE. The only controls are the factor dropdown and the horizon buttons. (A date control here would be a J-18 regression.)

9. Click "System Health" in the sidebar, then click "Research" again
   - **Expect:** System Health renders its existing content normally; returning to Research reloads the Factor Lab without errors — confirms no regression.

---

## What "Working Correctly" Looks Like

- The decile table shows 10 rows (D1–D10), each with a colour-graded percentage (green positive / red negative), a downside risk-adjusted ratio, and an `n` count.
- Changing the factor or horizon visibly re-points the table and the Rank-IC value (values come from the server, not invented client-side).
- The honesty caveat banner is always visible, and no date/as-of selector exists.

## Common Issues

- **"Backend unavailable" red card on `/research`:** The backend isn't running. Start it (`:8000`) and reload — this is the correct honest behaviour, not a crash.
- **Dropdown stuck on "Loading…":** The catalog request failed; check the backend is reachable at `http://localhost:8000/api/research/factor-lab`.
- **Cells showing "NA":** Expected only on low-sample deciles; on the committed seed every decile has enough samples, so "NA" should not normally appear. If it does, the `n` badge beside it explains why — this is honest, not a bug.
</content>
