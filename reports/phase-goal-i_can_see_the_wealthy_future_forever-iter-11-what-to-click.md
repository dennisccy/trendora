# Phase goal-i_can_see_the_wealthy_future_forever-iter-11 — What to Click (Operator Verification Guide)

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-11
**Time required:** ~5 minutes
**Written by:** ui-test-designer

---

## Prerequisites

- Frontend running at `http://localhost:3835`
- Backend running at `http://localhost:8000` (Factor Lab evidence loaded)
- No login required

---

## Verification Steps

1. Open `http://localhost:3835` in your browser, then click **"Research"** in the left sidebar
   - **Expect:** Page loads at `/research` with the heading **"Research — Factor Lab"** and an amber "Survivorship bias · universe-relative · descriptive" banner. No error card.

2. Scroll down past the "Decile sort" table and the "Rank-IC" card to the panel titled **"Factor effectiveness by market regime"**
   - **Expect:** A table with 7 columns — **Regime · n · Rank-IC · Top-decile mean · Bottom-decile mean · Spread (top − bottom) · Risk-adjusted spread** — and exactly 6 rows: **Strong risk-on, Risk-on, Narrow leadership, Choppy, Defensive, Risk-off** (in that order). Each row's `n` column shows `n=<number>`.

3. In the Horizon button group (top-right), click **"5d"**
   - **Expect:** The tables re-point. At least one regime row (e.g. **Risk-on**) shows an `n` chip ≥ 30 (no ⚠) with a signed numeric **Rank-IC** (e.g. `+0.12`) and a signed **Spread** (e.g. `+1.80%`) — real numbers, not "NA".

4. Click the **"60d"** Horizon button
   - **Expect:** Rows re-point with smaller `n` counts. At least one row (e.g. **Strong risk-on** or **Defensive**) now shows the muted text **"NA"** in its Rank-IC / Spread / Risk-adjusted spread cells, while its `n` chip still shows the honest count (e.g. `n=7 ⚠`). NA is never shown as `0`.

5. Open the **"Factor"** dropdown (top-right) and pick a different factor (e.g. "Risk score")
   - **Expect:** The regime table's numbers change (and the decile table + Rank-IC card above also change). A new factor was selected and the whole lab re-pointed.

6. In the top bar, open the **"View as-of date"** dropdown and select a historical date (not "Latest")
   - **Expect:** The top-bar badge changes to "Viewing as-of … (historical)", but the entire Factor Lab — decile table, Rank-IC card, AND the regime table — stays **exactly the same** (same numbers, same NA cells). `/research` ignores the as-of date by design (J-18).

7. Reload the page (press F5)
   - **Expect:** The Research page and the regime effectiveness table re-render with the same structure — 6 regime rows, 7 columns — no blank screen.

---

## What "Working Correctly" Looks Like

- The "Factor effectiveness by market regime" table sits below the decile/rank-IC grid with 6 regime rows and 7 columns.
- Short horizons (1d/5d) produce numeric Rank-IC/Spread values for high-sample regimes; long horizons (60d) flip sparse regimes to honest **"NA" + n** cells.
- Changing the Factor or Horizon re-points the regime table; changing the global as-of date does **not** touch it.

## Common Issues

- **Blank page / error screen**: Check the backend is running (`curl http://localhost:8000/health`).
- **Red "Backend unavailable" card with no tables**: Backend is down — expected behaviour is to show no numbers (never fabricated values); restart the backend.
- **Empty state "No forward-tested observations…"**: The chosen factor/horizon has zero observations; pick a shorter horizon or a different factor — the regime table is intentionally not rendered (not fabricated) when there is no data.
- **All regime cells show "NA"**: You are likely on a long horizon (60d) where most regimes are below the 30-sample minimum — switch to 5d to see numeric rows.
