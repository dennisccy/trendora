# Demo Script — goal-market-compass-iter-27

**Mode:** record
**Date:** 2026-08-28
**Frontend URL:** http://localhost:3255

## Highlights

### Step 01 — Open the Today page

- **Narration:** Let's start by opening the Today page, where the Manifest card displays the status of our market data.
- **Action:** Navigate to /
- **Point out:** The page loads with several cards below the compass summary, including a card titled 'Manifest' near the bottom.
- **Screenshot:** reports/demo/goal-market-compass-iter-27/step-01.png

### Step 02 — View an intact historical manifest (April 2025)

- **Narration:** When we look at data from April 2025, the Manifest card shows 'Basis: available' because both the frozen manifest and its underlying data source are intact and unchanged.
- **Action:** Navigate to /?asof=2025-04-15
- **Point out:** Inside the Manifest card, the green badge reads 'Basis: available' with no gray detail text beside it. The version badge shows 'version 2' and 'retrospective'.
- **Screenshot:** reports/demo/goal-market-compass-iter-27/step-02.png

### Step 05 — View the frontier manifest (August 2026)

- **Narration:** Now let's look at the most recent data from August 2026. Here the Manifest card shows 'Basis: rebuilt' because the underlying data source was recreated after this manifest was frozen.
- **Action:** Navigate to /?asof=2026-08-12
- **Point out:** Inside the Manifest card, the amber badge reads 'Basis: rebuilt' with gray detail text beside it saying 'the source scanner run was recreated after this manifest was frozen'. The version badge shows 'version 6' and 'at ingest'.
- **Screenshot:** reports/demo/goal-market-compass-iter-27/step-05.png

## Full tour (text only)

### Step 03 — Verify the regenerate control still works (cancel)

- **Narration:** The 'Regenerate manifest' button is available but gated by a confirmation modal. Let's click it to see the modal, then cancel to keep the data as it is.
- **Action:** Click "[data-testid="compass-manifest-regenerate-button"]"
- **Point out:** A modal titled 'Confirm manifest regenerate' opens. After clicking Cancel, the modal closes and the Manifest card remains unchanged with the same green 'Basis: available' badge.

### Step 04 — Close the confirm modal

- **Narration:** The confirmation modal is now open. We'll click Cancel to dismiss it without making any changes.
- **Action:** Click the "Cancel" button
- **Point out:** The modal closes and we're back to the Manifest card with all its badges unchanged.

### Step 06 — Refresh the page

- **Narration:** Let's refresh the page to confirm that the manifest status is stable and doesn't change on reload.
- **Action:** Click the "Refresh" button
- **Point out:** After refresh, the Manifest card still shows 'version 6' and the amber 'Basis: rebuilt' badge — nothing has changed.

### Step 07 — Understand the 'Basis: unavailable' state  [NEW]

- **Narration:** This iteration also enables a new 'Basis: unavailable' state for cases where a frozen manifest's underlying data has been removed. This state is proven by an automated backend test rather than shown here, because no date in the current database is in that specific state. The fix makes this honest reporting possible for the first time.
- **Action:** Navigate to /
- **Point out:** The backend now serves an existing manifest before attempting any self-healing, allowing it to honestly report when a source has been removed — a capability that was previously masked by automatic data recreation.
