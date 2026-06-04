# Phase goal-i_can_see_the_wealthy_future_forever-iter-19 — What to Click (Operator Verification Guide)

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-19
**Time required:** ~5 minutes
**Written by:** ui-test-designer

---

## Prerequisites

- Frontend running at `http://localhost:3835`
- Backend running and reachable (the Research labs load real numbers, not a "Backend unavailable" card)
- No login required

---

## Verification Steps

<!-- Maximum 10 steps. Prioritize: 1) core new feature works, 2) old behaviour preserved, 3) anti-goal. -->

1. Open `http://localhost:3835/research` in your browser
   - **Expect:** Heading "Research — Factor Lab" loads. At the top, next to the Factor/Horizon selectors, you see an "Analysis mode" control with two buttons: **All history** (highlighted/active) and **As of date**. Below it a grey line reads "Pooling every snapshot — all history (the default cross-date aggregate)." The Decile table, Rank-IC card, Multi-factor combination cohort, and Setup & Pattern Lab all show numbers.

2. Note the current sample sizes: the "Observations:" number above the Decile table and the "Pooled occurrences (Nd):" number in the Setup & Pattern Lab
   - **Expect:** Both are non-zero numbers — this is the full-history sample you'll compare against.

3. Click the **As of date** button in the Analysis-mode control
   - **Expect:** "As of date" becomes the highlighted button. Because the top-bar date is still at the latest date, the context line now reads "As of the latest date — equals all history. Pick an earlier date in the top-bar as-of switcher to restrict the window." The figures do not change yet.

4. In the top header bar, open the global **as-of date** dropdown (the only date control on the page) and pick one of the **earliest** dates near the bottom of the list
   - **Expect:** The context line changes to "Point-in-time: pooling only snapshots dated ≤ <the date you picked> ..." with your chosen date shown in accent colour.

5. Re-read the "Observations:" number and the "Pooled occurrences" number
   - **Expect:** Both numbers are **smaller** than in step 2. Thin cells show **NA** (not a made-up number), and each still shows its small "n" count. The yellow "Survivorship bias · universe-relative · descriptive" banner is still visible.

6. Click the **All history** button again
   - **Expect:** "All history" highlights, the context line returns to "Pooling every snapshot — all history...", and the sample sizes jump back up to the larger numbers from step 2.

7. **Anti-goal check (J-15):** Stay in **All history** mode and change the top-bar as-of date to a different early date
   - **Expect:** Nothing in the Research figures changes — the sample sizes stay at the full-history numbers. In All-history mode the labs ignore the global date.

8. **Anti-goal check (J-18):** Scan the whole `/research` page for date controls
   - **Expect:** There is exactly **one** date dropdown, and it's in the top header bar. The "Analysis mode" toggle is a mode switch (two text buttons), not a second date picker. No calendar or extra date field anywhere in the page body.

---

## What "Working Correctly" Looks Like

- The "All history ⟷ As of date" toggle is visible at the top of `/research` and switching it changes the grey context line beneath it.
- In **As of date** mode at an early date, the labs' sample sizes shrink and low-sample cells read **NA** (never a fabricated number); switching back to **All history** restores the larger figures.
- The page has exactly one date control (in the header); changing it affects the labs **only** in As-of mode.

## Common Issues

- **"Backend unavailable" card / blank tables:** Backend is down or unreachable — confirm it is running (`curl http://localhost:8000/health`).
- **Every page is a dead shell ("Checking backend…", 404 on `_next/static/chunks/main-app.js`):** The dev server's `.next` cache was clobbered by a prod build — this is an environment problem, not a phase regression (MEMORY `browser-qa-dead-shell-next-cache`).
- **Picking a date in the dropdown doesn't update anything (in As-of mode):** The global as-of `<select>` is a React-controlled select — a script-driven `.value =` won't fire React's change handler; drive it with the native value setter + a bubbling `change` event (MEMORY `react-controlled-select-needs-native-setter`). When changed by a real human click it works normally.
