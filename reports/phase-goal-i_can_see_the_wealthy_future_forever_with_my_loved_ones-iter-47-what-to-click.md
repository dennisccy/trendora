# Phase goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-47 — What to Click (Operator Verification Guide)

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-47
**Time required:** ~5 minutes
**Written by:** ui-test-designer

---

## Prerequisites

- Frontend running at `http://localhost:3835`
- Backend running at `http://localhost:8835` and fully warmed — confirm by visiting `http://localhost:8835/api/health` and verifying the response contains `"status": "ready"` before starting
- Do NOT run more than one heavy Research lab at a time — wait for each page to fully load before navigating to the next
- No login required

---

## Verification Steps

1. Navigate to `http://localhost:3835/research/event-study` in your browser
   - **Expect:** Within 90 seconds, a matrix table appears showing multiple horizon rows (e.g., 1d, 5d, 10d, 20d, 60d). Each row shows numeric values in the mean_return and win-rate columns, and an "N=..." chip. The page must NOT show "Backend unavailable" or a permanently spinning skeleton.
   - **Broken looks like:** The page shows "Backend unavailable" or the skeleton never disappears after 90 seconds. This was the regression this iteration fixes — if you see it, the fix did not take effect.

2. Click any "N=..." chip visible in the event-study matrix (e.g., a chip labeled "N=142")
   - **Expect:** The browser navigates to a URL beginning with `http://localhost:3835/research/samples?...`. The samples page loads and displays a list or table of sample rows. The total count shown (or the number of rows) matches the integer from the chip you clicked (e.g., 142 rows for "N=142").
   - **Broken looks like:** The samples page loads but shows a different count than the chip, or shows an error.

3. Navigate to `http://localhost:3835/research` (Factor Lab)
   - **Expect:** Within 90 seconds (cold cache) or 30 seconds (warm cache), the Factor Lab decile table appears with 10 decile rows showing numeric mean_return values per decile and a rank-IC figure. No "Backend unavailable" message.
   - **Broken looks like:** An HTTP 500 error page or a permanently loading skeleton — this was also failing before this iteration's fix.

4. Navigate to `http://localhost:3835/research/regime-setup-pattern`
   - **Expect:** Within 90 seconds, the Regime x Setup x Pattern ranked table appears with at least one row showing a regime label, setup label, pattern label, numeric mean_return, and non-zero n_total. No "Backend unavailable" message.

5. Navigate to `http://localhost:3835/research/downtrend-opportunity`
   - **Expect:** Within 60 seconds, at least one row in the result table shows a numeric mean_return value and a non-zero n. No "Backend unavailable" message.

6. Navigate to `http://localhost:3835/stocks`
   - **Expect:** The stock leaderboard loads. Locate NVDA in the list and note its Leadership score. Click "NVDA" to open its detail page. Verify the Leadership score on the detail page is identical (digit for digit) to the score shown in the leaderboard row.
   - **Broken looks like:** The scores differ between the leaderboard and the detail page — this indicates the single-source-of-truth invariant has been broken.

---

## What "Working Correctly" Looks Like

- Each of the five Research labs (event-study, factor-lab on `/research`, regime-setup-pattern, downtrend-opportunity, and factor-combination) loads real numeric figures — no permanent "Backend unavailable" banner and no skeleton that never resolves
- Every N= chip on any lab page navigates to `/research/samples` and the sample count there equals the integer shown on the chip
- NVDA scores are identical between the `/stocks` leaderboard and the `/stocks/NVDA` detail page

## Common Issues

- **"Backend unavailable" on all Research labs:** The backend may not be fully warmed. Run `curl http://localhost:8835/api/health` and wait until the response contains `"status": "ready"` before retrying.
- **Labs time out / hang:** Only fetch one heavy Research lab at a time. If you navigate to two labs simultaneously, the backend connection pool may exhaust. Restart the backend (`kill $(lsof -ti:8835)`, then start it again) and retry one lab at a time.
- **Skeleton never resolves on a single lab:** A prior request may have left the backend in a saturated state. Restart the backend and retry that single lab alone.
- **N= count mismatch on /research/samples:** This would indicate a data coherence regression. Note which lab and which chip produced the mismatch and report it — do not retry a different chip, as the mismatch itself is the finding.
