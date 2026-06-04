# Phase goal-i_can_see_the_wealthy_future_forever-iter-18 — What to Click (Operator Verification Guide)

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-18
**Time required:** ~5 minutes
**Written by:** ui-test-designer

---

## Prerequisites

- Frontend running at `http://localhost:3835`
- Backend running (so the Factor Lab evidence loads — otherwise you'll see "Backend unavailable")
- No login required

---

## Verification Steps

1. Open `http://localhost:3835/research` in your browser
   - **Expect:** Page loads with heading "Research — Factor Lab"; no error page. Scroll down to the panel titled **"Multi-factor combination cohort"**.

2. In the "Multi-factor combination cohort" table, find the highlighted/bold row labelled **"Combined (composite rank-blend)"**
   - **Expect:** Its **n** is a real number ≥ 30 and its **Mean fwd return**, **Median**, **Hit-rate**, and **Risk-adjusted (downside)** cells all show numbers — **not the word "NA"**. (This is the core fix: the headline Combined row is now populated.)
   - **Broken looks like:** the Combined row showing "NA" across the cells, or n = 0.

3. Look at the row directly below it, labelled **"Strict overlap (AND)"**
   - **Expect:** A muted (non-bold) secondary row. It shows either numbers or an honest "NA" with an **n** chip — never blank.

4. Read the table top-to-bottom and confirm the row order
   - **Expect:** **Baseline (all names)** → one or more **single-factor** rows → **Combined (composite rank-blend)** (highlighted) → **Strict overlap (AND)** (muted, last). There is no old "Combined (AND)"-only row.

5. Read the small grey hint under the panel title "Multi-factor combination cohort"
   - **Expect:** It mentions "composite rank-blend", a quantile label (e.g. "Quintile (20%)"), a weighting scheme (e.g. "equal"), and the words "NOT a fitted/ML model".

6. Click the **"Add condition"** button (with the + icon) repeatedly until it stops responding
   - **Expect:** You can add condition rows up to **11 total**, at which point the button becomes greyed-out/disabled. It does **not** stop at 3. After each add, the "Combined (composite rank-blend)" row stays populated (n > 0).

7. Make the strict intersection empty: in condition row 1 pick any factor with Side = **Top**; in condition row 2 pick the **same factor** with Side = **Bottom**
   - **Expect:** The "Combined (composite rank-blend)" row stays **populated** (n > 0, numeric), while the "Strict overlap (AND)" row shows **"NA" with n = 0** — the honest empty-intersection signal.

8. Scroll up and confirm the single-factor **Factor Lab** still works: change the top "Factor" dropdown and click a different "Horizon" button (e.g. "63d")
   - **Expect:** The Decile sort table (D1…D10) and the Rank-IC card update — confirms the existing feature didn't regress.

---

## What "Working Correctly" Looks Like

- The **"Combined (composite rank-blend)"** row is the visually emphasized headline row and is full of real numbers.
- A separate, muted **"Strict overlap (AND)"** row sits just below it and honestly shows NA + n when the exact intersection is empty.
- "Add condition" scales to 11 factors, and the composite row never collapses to NA just from adding factors.

## Common Issues

- **"Backend unavailable" card inside the section**: the backend isn't running — start it (`curl http://localhost:8000/health` to confirm), then reload.
- **Combined row shows "NA"**: this is the exact bug this iteration fixed — if you see it on the default load, the fix did not land (FAIL).
- **"Add condition" disables at 3**: the `max_conditions: 11` config/payload change didn't take effect (FAIL).
- **A date/calendar picker appears inside `/research`**: out of scope for this iteration (J-18 anti-goal) — the page should only have Factor / Horizon / per-condition / Subject controls, no date control of its own.
