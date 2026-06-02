# Phase goal-i_can_see_the_wealthy_future_forever-iter-12 — What to Click (Operator Verification Guide)

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-12
**Time required:** ~5 minutes
**Written by:** ui-test-designer

---

## Prerequisites

- Frontend running at `http://localhost:3835`
- Backend running at `http://localhost:8000` with price/forward-return seed data present
- No login required

---

## Verification Steps

1. Open `http://localhost:3835/research` in your browser
   - **Expect:** The page loads with the heading "Research — Factor Lab"; no error page.

2. Scroll to the bottom of the page, below the "Factor effectiveness by market regime" table
   - **Expect:** A Card titled "Multi-factor combination cohort" is visible, with 2 condition rows (each: a "Factor" dropdown, a Top/Bottom "Side" toggle, a "Quantile" dropdown) and a comparison table beneath them.

3. Read the comparison table
   - **Expect:** Columns are "Cohort", "n", "Mean fwd return", "Median", "Hit-rate", "Risk-adjusted (downside)". Rows are: a Baseline (all names) row, two single-condition rows (e.g. "Relative strength vs SPY (3m) · top Quintile (20%)"), and a shaded **Combined (AND)** row at the bottom. Every cell shows a value or "NA" — never blank.

4. In the **first** condition row, open the "Factor" dropdown and pick a different factor
   - **Expect:** After ~1 second the table briefly dims then refreshes; the first single-condition row's label and numbers change to the new factor, and the Combined (AND) row re-computes.

5. Click the "Add condition" button
   - **Expect:** A 3rd condition row appears and the table grows to 3 single-condition rows. The "Add condition" button becomes greyed/disabled (max is 3). The Combined (AND) row's n is ≤ the smallest single-row n.

6. Click "Remove" on the 3rd condition row
   - **Expect:** The 3rd row disappears, the table reverts to 2 single rows, "Add condition" is enabled again, and both remaining "Remove" buttons are now greyed/disabled (min is 2).

7. Force a thin cohort: set condition 1 to a factor at "Top" of a narrow quantile (e.g. "Tertile"), and condition 2 to the **same factor** at "Bottom" of the same quantile
   - **Expect:** The Combined (AND) row shows a small "n" and its Mean / Median / Hit-rate / Risk-adjusted cells read "NA" (muted) — **not** a fabricated 0.00%. This proves the honest-NA behaviour.

8. In the top-right "Horizon" control, click a different horizon button (e.g. switch to a different "Nd")
   - **Expect:** The decile table, rank-IC, regime table, **and** the combination table all refresh for the new horizon; your two condition selections are preserved.

9. Change the global as-of date control (in the app header) to a historical date
   - **Expect:** All four `/research` tables — decile, rank-IC, regime, and combination — stay **identical**. The combination section has no date state, so toggling the date must not change any value.

---

## What "Working Correctly" Looks Like

- The "Multi-factor combination cohort" table always shows Baseline + each single + Combined (AND), with a populated "n" per row.
- Add/Remove respect the 2–3 bound: Add disabled at 3, Remove disabled at 2.
- Thin or empty cohorts honestly show "NA" with the real sample size — never a made-up number.
- Changing factor / side / quantile / horizon re-points the table within ~1 second.

## Common Issues

- **"Backend unavailable" red card inside the section**: The backend at `http://localhost:8000` is down or erroring — start it (`curl http://localhost:8000/health`), then adjust a condition to retry.
- **Permanent loading skeleton (animated grey bars never resolve)**: The combination request is hanging — check the browser Network panel for a failed/pending `GET /api/research/factor-combination` request.
- **Empty-state "No forward-tested observations…" message**: The chosen horizon/conditions have no stored data — pick a shorter horizon or a different factor. This is honest behaviour, not a bug.
- **As-of toggle changes the tables**: That is a J-18 regression — the combination section must add no date state.
