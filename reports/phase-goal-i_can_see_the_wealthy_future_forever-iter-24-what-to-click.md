# Phase goal-i_can_see_the_wealthy_future_forever-iter-24 — What to Click (Operator Verification Guide)

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-24
**Time required:** ~5 minutes
**Written by:** ui-test-designer

---

## Prerequisites

- Frontend running at `http://localhost:3835`
- Backend running at `http://localhost:8835`
- Committed seed dataset loaded (the app ships with this — no extra setup needed)
- Do NOT perform step 8 on the live production database if it contains real user-added bars you cannot restore

---

## Verification Steps

1. Navigate to `http://localhost:3835/data`
   - **Expect:** Page loads fully; the "Dataset coverage" panel is visible; a "Remove imported data" panel is visible below the Resumable imports section; no red error banners appear

2. In the "Dataset coverage" panel, find the "Universe" figure and read the text directly below the number
   - **Expect:** A one-sentence plain-language definition appears below the number (e.g., "The config-screened, scored names...") — not just the label repeated. Repeat for "Symbols", "Trading days", "Snapshot dates", and "Backfill gaps" — each must have a definition sentence

3. Scroll down within the "Dataset coverage" panel to its bottom section
   - **Expect:** A prose sentence appears that names both "universe" and "symbols" and explains the difference between the two counts in plain language

4. Locate the per-symbol coverage table inside the "Dataset coverage" card; check that the column headers read "Symbol", "In universe", "Has data", "Date range", "Bars", "Flag"
   - **Expect:** The table is present with all six columns and at least one data row; a universe member row shows a badge or "yes" in the "In universe" column

5. Type "AAPL" in the "Filter symbol..." input above the per-symbol table
   - **Expect:** Only rows whose symbol contains "AAPL" remain visible; all other rows disappear while text is in the input. Then clear the input — all rows return.

6. Click the "Universe members only" toggle above the per-symbol table
   - **Expect:** Row count decreases; every remaining row has a positive "In universe" indicator; every remaining row shows either data (non-NA date range) or a "missing" badge in the Flag column — no member is silently absent

7. Scroll down to the "Remove imported data" panel; confirm it shows a symbols text field, a "From date" date input, a "To date" date input, and a "Preview removal" button with a red-border or destructive style; leave all fields empty and attempt to click "Preview removal"
   - **Expect:** The "Preview removal" button is disabled with all fields empty; nothing happens when clicked

8. Type "AAPL" in the symbols field of the "Remove imported data" panel, then click the now-enabled "Preview removal" button
   - **Expect:** A full-screen overlay modal appears containing three sections: (1) "Will be removed (user-added)" with a bar count and date range or "none/0" on seed-only host; (2) "Not removable — committed seed (protected)" listing per-symbol counts and the reason "committed seed"; (3) a "Cascade" section with snapshot and forward-return counts
   - **Broken looks like:** Modal does not open, or modal opens with no sections, or "Preview removal" stays disabled after typing

9. With the preview modal open and showing a seed-only scope (on the seed-only live host, AAPL has only seed bars), locate the "Remove N bars" button and the amber refusal message
   - **Expect:** The "Remove N bars" confirm button is disabled (gray, not clickable); an amber message containing "committed seed" is visible in the modal

10. Click the "Cancel" button in the modal footer
    - **Expect:** The modal closes; the per-symbol coverage table is unchanged (same rows and bar counts as before); a green success notice does NOT appear; no data was deleted

---

## What "Working Correctly" Looks Like

- Every metric in the Dataset coverage panel shows a number AND a plain-language definition sentence — no bare numbers
- The per-symbol table has six labeled columns, supports live symbol filtering, and correctly toggles between all-symbols and universe-members-only views
- The "Remove imported data" panel is present below Resumable imports, "Preview removal" is gated on having at least one input, and opening a preview for seed-only bars shows an amber refusal with the confirm button disabled

## Common Issues

- **Page stuck on "Checking backend..."**: The backend is not running. Start it with `bash scripts/start-backend.sh` (port 8835) and reload.
- **Per-symbol table is empty**: The coverage endpoint may not be returning `per_symbol` data. Check `GET http://localhost:8835/api/data` in the browser and confirm the response JSON includes a `per_symbol` array.
- **"Preview removal" button stays disabled after typing a symbol**: The frontend may have a rendering issue. Try a hard reload (Ctrl+Shift+R) to clear any stale Next.js cache.
- **Modal opens but shows no sections**: The preview endpoint (`POST /api/data/remove/preview`) may be returning an unexpected response shape. Check the browser Network tab for a non-200 response.
