# Demo Script — goal-i_can_see_the_wealthy_future_forever-iter-18

**Mode:** record
**Date:** 2026-06-04
**Frontend URL:** http://localhost:3835
**Iteration:** 18

## Highlights

### Step 01 — The Combined cohort is finally populated  [NEW]

- **Narration:** Open Research → Factor Lab and look at the 'Multi-factor combination cohort' table. The headline 'Combined (composite rank-blend)' row now shows real figures — a genuine sample size with mean and median forward returns, hit-rate and a downside risk-adjusted number — instead of the empty 'NA' it always used to show.
- **Action:** Navigate to /research
- **Point out:** The emphasized 'Combined (composite rank-blend)' row near the bottom of the table is full of real numbers, sitting above a muted 'Strict overlap (AND)' row.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever-iter-18/step-01.png

### Step 04 — Add a factor to the blend  [NEW]

- **Narration:** Click 'Add condition' to fold another factor into the combination. The blend recomputes on the spot and the Combined row stays populated — adding factors no longer collapses it to 'NA'.
- **Action:** Click the "Add condition" button
- **Point out:** A fresh condition row appears in the editor and the 'Combined (composite rank-blend)' row keeps a real, non-zero sample size.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever-iter-18/step-04.png

### Step 05 — Scale up to the whole catalog  [NEW]

- **Narration:** Keep clicking 'Add condition' — the blend scales all the way to every one of the eleven catalog factors before the button finally switches off. The composite cohort stays full of real numbers the entire way.
- **Action:** Click the "Add condition" button
- **Point out:** Another condition row joins the list and the Combined row is still populated, proving the blend handles many factors at once.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever-iter-18/step-05.png

### Step 06 — The single-factor Factor Lab still works

- **Narration:** Scroll back up and pick a different horizon, like 60d. The decile sort (D1 through D10) and the Rank-IC card re-point to that horizon — the original Factor Lab is untouched by the new combination work.
- **Action:** Click the "60d" button
- **Point out:** The decile table and Rank-IC value update for the 60-day horizon, confirming the existing tools didn't regress.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever-iter-18/step-06.png

## Full tour (text only)

### Step 02 — An honest secondary 'Strict overlap' row  [NEW]

- **Narration:** Just below the blend sits the muted 'Strict overlap (AND)' row — the exact intersection of your selected factors. When that intersection is empty it honestly reads 'NA' with a count of zero, never a made-up 0%, while the composite blend stays populated beside it.
- **Action:** Click "[data-testid='combination-row-strict_overlap']"
- **Point out:** The secondary 'Strict overlap (AND)' row is de-emphasized and reports NA + n when the exact overlap is empty.

### Step 03 — Still just one date control

- **Narration:** The Factor Lab has no date picker of its own — it reads the single global 'View as-of date' control in the header. Switching that global date leaves these combination figures byte-for-byte identical, because the cohort pools observations across every date.
- **Action:** Navigate to /research
- **Point out:** Only the global 'View as-of date' selector in the header controls dates; nothing inside the lab does.
