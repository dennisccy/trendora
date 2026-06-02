# Demo Script — goal-i_can_see_the_wealthy_future_forever-iter-12

**Mode:** record
**Date:** 2026-06-02
**Frontend URL:** http://localhost:3835
**Iteration:** 12

## Highlights

### Step 01 — Open the Factor Lab

- **Narration:** We open the Factor Lab — a read-only research page that grades each stock signal against months of already-recorded forward returns, so nothing here is a guess or a prediction.
- **Action:** Navigate to /research
- **Point out:** The decile sort and rank-IC score at the top judge one factor at a time. The brand-new tool we are here to see sits at the very bottom of the page.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever-iter-12/step-01.png

### Step 02 — Compare a combined cohort against the baseline and each single factor  [NEW]

- **Narration:** At the bottom is the new Multi-factor combination cohort panel. Each condition is a factor set to the top or bottom of its range — here we switch the first one to the bottom, and the comparison recomputes on the spot.
- **Action:** Click the "Bottom" button
- **Point out:** Four rows to compare: the all-names baseline, one row per single factor, and the shaded Combined (AND) cohort — each with its sample size, mean and median forward return, hit-rate, and downside risk-adjusted return.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever-iter-12/step-02.png

### Step 03 — Stack a third condition  [NEW]

- **Narration:** We add a third condition, and the comparison grows to three single factors plus the cohort that satisfies all of them at once.
- **Action:** Click the "Add condition" button
- **Point out:** The combined cohort's sample size is never larger than the smallest single factor — stacking filters can only narrow the group. The Add condition button greys out once three conditions are in play.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever-iter-12/step-03.png

### Step 04 — Pare back to two conditions  [NEW]

- **Narration:** Removing a condition snaps the table back to two factors plus their combined cohort.
- **Action:** Click the "Remove condition 3" button
- **Point out:** Add condition is selectable again, and the Remove buttons grey out at two conditions — the tool never lets you drop below a real side-by-side comparison.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever-iter-12/step-04.png

## Full tour (text only)

### Step 05 — One shared horizon re-points every table

- **Narration:** One shared horizon control at the top of the page sets the holding period for everything at once — switch it and the decile sort, the regime table, and this new combination table all re-point together.
- **Action:** Click the "60d" button
- **Point out:** Your chosen conditions carry over unchanged across the horizon switch; only the numbers update.

### Step 06 — Honest NA instead of invented numbers  [NEW]

- **Narration:** Honesty is built in: set two conditions to opposite extremes and the combined group can genuinely run out of matching names. When that happens the cells simply read NA beside the real sample size.
- **Action:** Navigate to /research
- **Point out:** A thin or empty cohort shows NA with its true count — never an invented 0.00% return.

### Step 07 — One date control — the lab is a cross-date aggregate

- **Narration:** Finally, the global as-of date in the header never touches this page. The Factor Lab pools its evidence across every date, so changing that date leaves all of its tables exactly as they were.
- **Action:** Navigate to /research
- **Point out:** There is just one date control in the whole product — this research page deliberately adds none of its own.
