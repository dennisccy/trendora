# Phase goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-35 — What to Click (Operator Verification Guide)

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-35
**Time required:** ~5 minutes
**Written by:** ui-test-designer

---

## What This Phase Did

The J-85 rebuild repopulated all stored stock snapshots with a genuine point-in-time universe. The UI did not change. What changed is the DATA the existing pages now serve: the stock universe on `/stocks` now slides with the date (empty before October 2021, ~544 members today) instead of always returning a flat 122 stocks regardless of date.

---

## Prerequisites

- Frontend running at `http://localhost:3835`
- Backend running at `http://localhost:8835`
- No action needed — the J-85 rebuild is already complete (job eb48cbf1, 1369/1369 dates)

---

## Verification Steps

1. Open `http://localhost:3835/stocks` in your browser
   - **Expect:** The stocks leaderboard loads and shows approximately 544 rows. If you see 122 rows, the rebuild data is not being served — check that the backend on port 8835 is running.

2. Set the global as-of date (the single date switcher at the top of the page) to `2021-01-04`
   - **Expect:** The leaderboard table becomes completely empty — 0 rows, with a "No stocks" or "No data" message. This is correct and expected: no stocks qualified for the universe on that early date. If you still see stock rows (especially 122 of them), the rebuild has not taken effect.

3. Set the global as-of date to `2022-02-01`
   - **Expect:** The leaderboard table now shows approximately 495–504 rows. The jump from 0 rows (step 2) to ~500 rows confirms the universe is dynamic and sliding with the date — not a fixed flat list.

4. Set the global as-of date back to `2026-06-16` (or the latest available date), then locate NVDA in the leaderboard table and note its three score values (Leadership, Entry, Risk). Then click on NVDA to open its detail page at `http://localhost:3835/stocks/NVDA`
   - **Expect:** The Leadership, Entry, and Risk scores on the NVDA detail page are identical to the values you saw on the leaderboard row. If they differ, the detail page is reading from a different snapshot than the list.

5. Navigate to `http://localhost:3835/data` and scroll down until the membership timeline panel is visible
   - **Expect:** The SIZE column in the timeline table shows different values across rows — near 0 for early dates (around October 2021) and approximately 544 for recent dates, forming an upward step shape. The Entries and Exits columns show real values (numbers or symbols) in multiple rows — not all dashes. The panel also contains the words "survivorship", "warm-up", and "universe-relative" somewhere in its labels. If the SIZE column shows a uniform 122 on every row, the timeline is still reading stale pre-rebuild data.

6. On the same `/data` page, find the per-date coverage diagnostic section (labelled something like "Universe Coverage" or "Admitted Members") and check the count for `2026-06-16`
   - **Expect:** The admitted-member count shown is approximately 544 — matching the row count you saw on `/stocks` in step 1. If the diagnostic shows 544 but `/stocks` shows 122, the reconciliation has failed.

---

## What "Working Correctly" Looks Like

- The stocks leaderboard is empty at `2021-01-04` and has approximately 544 rows at `2026-06-16` — the universe slides with the date
- The `/data` membership timeline SIZE column rises from near-zero in late 2021 to approximately 544 today — it is NOT a flat line at 122
- NVDA's scores are identical on the list view and the detail page at the same date

## Common Issues

- **Leaderboard still shows 122 rows at every date:** The backend may be running but serving cached or stale data. Confirm the backend on port 8835 is the rebuilt version: run `curl "http://localhost:8835/api/stocks?as_of=2021-01-04"` in a terminal — a working rebuild returns an empty array `[]`, not 122 items.
- **Page shows "Checking backend…" and never loads:** The frontend dev server on port 3835 cannot reach the backend on port 8835. Check that the backend is up (`curl http://localhost:8835/health`) and that CORS_ORIGINS in the backend config includes `:3835`.
- **Membership timeline shows a flat line:** The `/data` page may be loading but the timeline panel is using a different data source than the rebuilt snapshots. Confirm the backend is returning dynamic data by running `curl "http://localhost:8835/api/stocks?as_of=2021-10-25"` — you should get approximately 495 rows, not 122.
- **Do NOT trigger another rebuild:** The rebuild panel on `/data` is confirm-gated. Do not click through the confirmation — a new rebuild takes approximately 11 hours and will clear all snapshot data while running.
