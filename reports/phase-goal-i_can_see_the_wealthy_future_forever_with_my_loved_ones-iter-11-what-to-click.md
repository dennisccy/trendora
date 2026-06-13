# Phase goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-11 — What to Click (Operator Verification Guide)

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-11
**Time required:** ~5 minutes
**Written by:** ui-test-designer

---

## Prerequisites

- Frontend running at `http://localhost:3835`
- Backend running (verify with: `curl http://localhost:8835/health` — should return 200)
- At least one completed sectors scan (the ranked ETF table must show rows with scores)

---

## Verification Steps

1. Open `http://localhost:3835/sectors` in your browser
   - **Expect:** A ranked table of ETF rows loads with tickers (e.g., XLK, SMH, KRE) and numeric scores. No "Backend unavailable" banner or blank screen.

2. Locate the "SMH" row in the ranked table and click its expand toggle (chevron icon on the right of the row)
   - **Expect:** An expanded panel opens below the SMH row. The panel header shows a human-readable name such as "Semiconductors (VanEck)" — NOT the bare ticker "SMH". A plain-language description sentence appears below the header.

3. Scroll down within the expanded SMH panel to find the member chip list
   - **Expect:** Ticker chips (e.g., "NVDA", "AMD") are visible. The section heading above the chips reads "Members (config-defined)". If more than 6 chips exist, a "+N" button with a dashed border is visible.

4. Click the "+N" button in the SMH member list (if visible)
   - **Expect:** All member chips appear (the count grows beyond 6). A "Show fewer" button replaces the "+N" button. Click "Show fewer" — the list collapses back to 6 chips.

5. Locate the "KRE" row in the ranked table and click its expand toggle
   - **Expect:** The expanded panel header shows "Regional Banks (SPDR)" — NOT "KRE". The members section shows the message "No universe members are mapped to this ETF (config-defined)." with zero ticker chips. No fabricated tickers appear.

6. Navigate to `http://localhost:3835/sectors?asof=2026-05-15` (a historical snapshot date)
   - **Expect:** The table reloads showing data as of 2026-05-15. Expand any ETF row that has member chips. Hover over one of the chips (or right-click and copy the link) — the link URL should contain `?asof=2026-05-15`.

7. Locate the "XLK" row in the ranked table and click its expand toggle
   - **Expect:** The score-component breakdown (existing feature — RS vs SPY, distance from 52-week high) is still visible in the panel. The new member chips appear below the existing components without replacing them.

8. Scroll back to the top of the ranked table and verify the row ordering
   - **Expect:** ETF rows are ordered by score from highest (rank 1 at top) to lowest. The ordering matches what you saw before this iteration — no rows are out of place.

---

## What "Working Correctly" Looks Like

- Expanded industry ETF panels (SMH, KRE) display a human-readable name in the header — never just the ticker symbol
- The SMH description paragraph is visible and contains meaningful text (not blank or "null")
- KRE shows a clear empty-state message with zero chips — the most important check for data integrity (no fabricated names)
- Member chip clicks open the stock detail page in a NEW tab, not the same tab
- Historical `?asof=` navigation correctly passes the date through to member chip links

## Common Issues

- **Table shows "Backend unavailable" or no rows:** The backend is not running or the scan has not completed. Run `curl http://localhost:8835/health` to check.
- **Expand toggle does nothing / panel is blank:** Check the browser console (F12) for JavaScript errors. This may indicate a frontend build issue.
- **Chips show "null" or "undefined":** The backend may have started with an incomplete config migration. Restart the backend and verify `config.yaml` has the `etfs.industry` catalog format (ticker → `{name, description}`).
- **KRE panel shows fabricated member tickers:** This is a critical failure — the empty-state message is missing. File a bug immediately.
