# Phase goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-15 — What to Click (Operator Verification Guide)

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-15
**Time required:** ~5 minutes
**Written by:** ui-test-designer

---

## Prerequisites

- Frontend running at `http://localhost:3835`
- Backend running (check: `curl http://localhost:8835/health` should return 200)
- No special login required

---

## Verification Steps

1. Navigate to `http://localhost:3835/data` in your browser
   - **Expect:** The Data Manager page loads fully. You can see multiple panels — at least a heatmap or coverage section and a "Remove imported data" panel. No blank screen or "Something went wrong" error overlay.

2. Scroll to the "Remove imported data" panel and inspect its input fields
   - **Expect:** You see exactly two date fields labeled "From" and "To". There is NO text box for symbols or a "Symbols" label anywhere in the panel. The panel is compact — just the two date inputs and a "Preview removal" button.

3. While both date fields are empty, look at the "Preview removal" button
   - **Expect:** The button is disabled (grayed out). Clicking it does nothing — no modal appears.

4. Type `2025-02-01` into the "From" date field, leave "To" empty, then look at the "Preview removal" button
   - **Expect:** The button remains disabled. A single date is not enough to enable it.

5. Type `2025-02-28` into the "To" date field
   - **Expect:** The "Preview removal" button becomes enabled (it is no longer grayed out) immediately, without a page refresh.

6. Click the now-enabled "Preview removal" button
   - **Expect:** A confirmation modal appears. The modal body displays numeric count summaries — something like "45 bars across 3 symbols will be removed" and "2 snapshots will be cascaded away". No list of individual ticker symbols (AAPL, MSFT, etc.) appears anywhere in the modal body.

7. Without scrolling the modal, look at the bottom of the modal
   - **Expect:** A "Cancel" button and a "Remove" (or "Confirm") button are both visible in the footer row at the bottom of the modal. You do not need to scroll down inside the modal to find the Remove button.

8. Click the "Cancel" button in the modal footer
   - **Expect:** The modal closes immediately. You are back on the `/data` page. No removal job was started.

9. Scroll back up on the `/data` page and verify the heatmap or data coverage section is still visible and rendering
   - **Expect:** The heatmap or coverage panel shows a grid or tiles (or an empty-state message if there is no data). It does not show a blank panel or an error.

---

## What "Working Correctly" Looks Like

- The Remove panel has exactly two date fields ("From" and "To") and no symbols input — if you see a symbols text box, the old UI is still showing.
- The "Preview removal" button is disabled until both dates are filled with valid ISO dates (`yyyy-MM-dd`); filling one date alone is not enough.
- The confirmation modal body shows only counts (numbers), never a list of ticker symbols by name.
- The "Remove" button in the confirmation modal is always visible in the footer without scrolling — it is never pushed off the bottom of the screen.

## Common Issues

- **Blank page or "Checking backend..." spinner that never resolves:** The backend is not running or is still booting. Wait 30–60 seconds and refresh. If it persists, check that the backend process is running on port 8835.
- **Remove panel shows a "Symbols" text box:** The frontend may be serving a cached build. Hard-refresh with Ctrl+Shift+R (Windows/Linux) or Cmd+Shift+R (Mac) to clear the browser cache.
- **"Preview removal" button stays disabled even with both dates filled:** Check that both dates are in `yyyy-MM-dd` format (e.g., `2025-02-01`, not `02/01/2025`). Some browsers may pre-format date inputs in a locale-specific format — try typing the date directly in ISO format.
- **Modal shows a long list of symbol names:** The frontend is serving stale code. Hard-refresh the page and try again.
