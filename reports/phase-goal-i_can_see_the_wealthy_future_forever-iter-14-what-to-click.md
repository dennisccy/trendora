# Phase goal-i_can_see_the_wealthy_future_forever-iter-14 — What to Click (Operator Verification Guide)

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-14
**Time required:** ~5 minutes
**Written by:** ui-test-designer

---

## Prerequisites

- Frontend running at `http://localhost:3835`
- Backend running and reachable from the frontend (DB regenerated from the committed seed)
- No login required

> **Heads up:** The event study opens on the **Actionable** subject by default, which is a *rare* setup (~2 occurrences in this seed) — so the default view honestly shows **NA + n=2**, not numbers. That is correct, not a bug. To see populated figures, pick **Breakout-watch** or **Pullback to a rising DMA** as instructed below.

---

## Verification Steps

1. Open `http://localhost:3835/research` in your browser
   - **Expect:** The "Research — Factor Lab" page loads, no error page. Scroll to the bottom.

2. Scroll down past the Factor Lab table and the "Multi-factor Combination Lab" section to the third section titled **"Setup & Pattern Lab — event study"**
   - **Expect:** A panel with a "Subject" dropdown, a "Per-horizon distribution & exit-horizon curve" table, a "By market regime" panel, and a "By sector" panel.

3. Open the **"Subject"** dropdown
   - **Expect:** Two groups — "Setups" (Actionable, Breakout-watch, Pullback-watch, Extended, Avoid, Risk-off-watchlist) and "Patterns" (VCP, Pullback to a rising DMA, Flat-base).

4. Select **"Breakout-watch"** from the "Setups" group
   - **Expect:** The per-horizon table fills with real numbers (one row per horizon: Mean, Median, % Positive, Dispersion, Expectancy, Mean MAE, Mean MFE, Return / downside-dev, Return / MAE, n) — NOT the text "NA".

5. Look at the Horizon column of that table
   - **Expect:** Exactly one row carries a "best exit" badge, and it matches the "Best exit-horizon: <N>d" value in the meta line above the table.

6. Select **"Actionable"** from the dropdown (the default, low-sample setup)
   - **Expect:** The value cells now read the literal "NA", while the "n" column still shows the honest count (e.g. n=2) with a warning chip — no fabricated numbers.

7. Re-select **"Breakout-watch"**, then read the **"By market regime (Xd)"** and **"By sector (Xd)"** panels
   - **Expect:** By-regime shows one row per configured regime (with at least one "NA"/n=0 empty regime); By-sector shows only sectors that actually have occurrences.

8. At the top-right of the page, in the **"Horizon"** button group, click a different horizon (e.g. click "60d")
   - **Expect:** The "By market regime (…d)" and "By sector (…d)" titles and the "Pooled occurrences (…d)" count update to the new horizon — the study reuses the page's shared horizon control.

9. In the top bar, open the **"View as-of date"** dropdown and pick any historical date (not "Latest")
   - **Expect:** The amber "Viewing as-of <date> (historical)" badge appears, but the event-study tables stay **identical** — the study is a cross-date aggregate and does not time-travel. Switch back to "Latest" when done.

10. Scroll back up and confirm the **Factor Lab** table and the **Multi-factor Combination Lab** section still render normally above the new section
    - **Expect:** Page order is Factor Lab → Combination Lab → Setup & Pattern Lab, all rendering without errors.

---

## What "Working Correctly" Looks Like

- Selecting **Breakout-watch** populates a full per-horizon table with exactly one "best exit" badge.
- Selecting **Actionable** shows honest "NA" cells with a real n=2 — the app never invents numbers for thin data.
- Changing the **Horizon** buttons re-points the by-regime / by-sector panels; changing the **as-of date** does NOT change the event-study tables.

## Common Issues

- **"Backend unavailable" red block in the section:** The backend isn't running — start it (`curl http://localhost:8000/health` should return ok), then reload.
- **Everything shows "NA":** You're likely still on the default **Actionable** subject — switch to **Breakout-watch** or **Pullback to a rising DMA**.
- **No "best exit" badge:** Expected only when the selected subject has enough non-low-sample horizons; on a low-sample subject the "Best exit-horizon" reads "NA" by design.
