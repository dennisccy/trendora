# Phase goal-i_can_see_the_wealthy_future-iter-12 — What to Click (Operator Verification Guide)

**Phase:** goal-i_can_see_the_wealthy_future-iter-12
**Time required:** ~5 minutes
**Frontend URL:** http://localhost:3835

---

**Prerequisites:**
- Backend running at http://localhost:8835
- Frontend running at http://localhost:3835
- No login required

## Steps

1. Open `http://localhost:3835/` in your browser and look at the left sidebar.
   - **Expect:** A **"Methodology"** link with a book icon appears right **after "Watchlist"**.

2. Click the **"Methodology"** sidebar link.
   - **Expect:** URL becomes `http://localhost:3835/methodology`; heading reads **"Methodology"**; the "Methodology" sidebar item is highlighted as active.

3. Scroll the card grid and count the cards; check each card's top-right chip.
   - **Expect:** Exactly **7 cards** — six with a **"Setup"** chip (Actionable, Breakout-watch, Pullback-watch, Extended, Avoid, Risk-off-watchlist) and one **VCP** card with a **"Pattern"** chip.

4. On the **Actionable** card, read the threshold rows.
   - **Expect:** Rows including **Leadership ≥ 80**, **Entry ≥ 70**, **Risk ≤ 60**, plus a meaning paragraph and an italic worked example.

5. Navigate to `http://localhost:3835/stocks` and wait for the leaderboard to load.
   - **Expect:** Rows render with setup badges; no blank page (the extra catalog fetch must not break the leaderboard).

6. On the first row, click the small **ⓘ** button next to the setup badge.
   - **Expect:** A small popover opens with that status's definition — matching the meaning text on the `/methodology` card for the same status.

7. Press the **Escape** key.
   - **Expect:** The ⓘ popover closes.

8. Open the **Setup** dropdown (labeled "Setup") and select **"Actionable"**.
   - **Expect:** The leaderboard narrows so every visible row's setup badge reads "Actionable"; the `N / total` counter beside the filters drops.

9. Set the **Setup** dropdown back to "All setups", then open the **VCP** dropdown and select **"VCP only"**.
   - **Expect:** The leaderboard narrows to only VCP-flagged rows (existing VCP behavior unchanged).

## If Something Looks Wrong

- **Methodology page shows a red "Backend unavailable" card** (body: "The methodology glossary could not load from the API…") **or stays on gray skeletons:** the backend on port 8835 is down or unreachable — start it and refresh.
- **`/stocks` is blank or the filters stop working:** that is a regression — the new `/api/methodology` fetch should be non-blocking; the leaderboard and Setup/VCP filters must keep working even if that fetch fails.
- **VCP appears as a 7th "Setup" status:** incorrect — VCP must be a separate **"Pattern"** card, not a setup status.
