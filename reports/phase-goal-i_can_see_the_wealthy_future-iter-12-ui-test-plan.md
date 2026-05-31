# Phase goal-i_can_see_the_wealthy_future-iter-12 — UI Test Plan

**Phase:** goal-i_can_see_the_wealthy_future-iter-12
**Frontend URL:** http://localhost:3835
**Backend URL:** http://localhost:8835
**Date:** 2026-05-31
**Written by:** ui-test-designer

---

## Scope

This iteration adds a **Methodology / Glossary** capability:
- A new `/methodology` page that documents all six setup statuses + the VCP pattern (one config-backed catalog).
- A new **"Methodology"** sidebar nav item (book icon) after "Watchlist".
- Inline info (ⓘ) tooltips on the `/stocks` leaderboard's **setup** and **VCP** badges, showing the same catalog definitions.
- The `/stocks` **Setup filter** dropdown options are now sourced from the catalog (with a graceful fallback if the catalog fetch fails).

Surfaces under test: `/methodology`, `/stocks`, and the global Sidebar.

---

## Test Cases

### UT-01: Methodology page loads
**Type:** smoke
**Surface:** `/methodology`
**Preconditions:** Backend running at http://localhost:8835; frontend running at http://localhost:3835.

**Steps:**
1. Navigate to `http://localhost:3835/methodology`.
2. Wait for the page to finish loading (loading skeleton cards disappear).

**Expected Result:** Page renders with the heading **"Methodology"** and subtitle "How every setup status and the VCP pattern are defined — thresholds, meaning, and a worked example." No red error card. No browser console errors. The page does not stay stuck on the gray pulsing skeleton cards.

---

### UT-02: All seven catalog cards render
**Type:** happy-path
**Surface:** `/methodology`
**Preconditions:** Backend running; on `http://localhost:3835/methodology` (UT-01 passed).

**Steps:**
1. Scroll through the card grid below the heading.
2. Count the entry cards and read each card's title (the bold `h2` at the top-left of each card).

**Expected Result:** Exactly **7 entry cards** are present, with these titles: **Actionable**, **Breakout-watch**, **Pullback-watch**, **Extended**, **Avoid**, **Risk-off-watchlist**, and **VCP**. (Title wording may render with the catalog's display names; there must be six setup-status cards plus one VCP card — no more, no fewer.)

---

### UT-03: Setup vs Pattern chip classification
**Type:** happy-path
**Surface:** `/methodology`
**Preconditions:** On `http://localhost:3835/methodology` with all cards loaded.

**Steps:**
1. On each of the six status cards (Actionable, Breakout-watch, Pullback-watch, Extended, Avoid, Risk-off-watchlist), read the chip in the card's top-right corner.
2. On the VCP card, read the chip in its top-right corner.

**Expected Result:** The six status cards each show a chip reading **"Setup"** (neutral style). The **VCP** card shows a chip reading **"Pattern"** (info/blue style). VCP must NOT appear as a 7th "Setup" status.

---

### UT-04: Actionable card thresholds and content
**Type:** happy-path
**Surface:** `/methodology`
**Preconditions:** On `http://localhost:3835/methodology` with cards loaded.

**Steps:**
1. Locate the **Actionable** card.
2. Read its plain-language meaning paragraph.
3. Read the threshold rows (each row shows a label on the left and a monospace comparison/value on the right).
4. Read the worked example (italic text at the bottom of the card).

**Expected Result:** The Actionable card shows a non-empty meaning paragraph, threshold rows including **Leadership ≥ 80**, **Entry ≥ 70**, **Risk ≤ 60**, and a **Regime** text rule, plus a non-empty italic worked example. The numeric values are right-aligned in monospace.

---

### UT-05: VCP card thresholds and content
**Type:** happy-path
**Surface:** `/methodology`
**Preconditions:** On `http://localhost:3835/methodology` with cards loaded.

**Steps:**
1. Locate the **VCP** card (the one with the "Pattern" chip).
2. Read its threshold rows.

**Expected Result:** The VCP card shows threshold rows including **Min contractions ≥ 2**, **Max base depth ≤ 35%**, **shrink ≤ 0.9**, **Final ≤ 12%**, **Within pivot ≤ 8%**, and **Volume dry-up ≤ 0.9** (label wording may vary slightly but each rule must be present with its comparison and value). A meaning paragraph and worked example are also present.

---

### UT-06: Methodology backend-unavailable error state
**Type:** error
**Surface:** `/methodology`
**Preconditions:** Frontend running. Ability to stop the backend (http://localhost:8835).

**Steps:**
1. Stop the backend process (the FastAPI server on port 8835).
2. Navigate to (or hard-refresh) `http://localhost:3835/methodology`.

**Expected Result:** A red-bordered error card appears with a warning icon, a bold heading **"Backend unavailable"** and the body text **"The methodology glossary could not load from the API. No definitions are shown rather than fabricated copy. Confirm the backend is running and retry."** No blank page, no fabricated catalog content, no infinite skeleton. (Restart the backend afterward to continue testing.)

---

### UT-07: Methodology loading skeleton
**Type:** ux
**Surface:** `/methodology`
**Preconditions:** Backend running but slow/cold start, OR observe on first navigation before data arrives.

**Steps:**
1. Open a fresh browser tab and navigate to `http://localhost:3835/methodology`.
2. Observe the page during the brief moment before catalog data arrives.

**Expected Result:** While loading, a grid of gray pulsing skeleton cards is shown (no error text, no empty white space). Once data arrives, the skeletons are replaced by the real entry cards.

---

### UT-08: Methodology nav item appears in sidebar
**Type:** smoke
**Surface:** Sidebar (all pages)
**Preconditions:** Frontend running.

**Steps:**
1. Navigate to `http://localhost:3835/` (or any page).
2. Inspect the left sidebar navigation list.

**Expected Result:** A **"Methodology"** nav link with a **book icon** appears in the sidebar, positioned immediately **after the "Watchlist"** item. The sidebar now shows 9 top-level nav items.

---

### UT-09: Navigate to Methodology via sidebar
**Type:** happy-path
**Surface:** Sidebar → `/methodology`
**Preconditions:** Backend + frontend running; on `http://localhost:3835/`.

**Steps:**
1. Click the **"Methodology"** link in the left sidebar.

**Expected Result:** The browser navigates to `http://localhost:3835/methodology`, the Methodology page loads with its 7 cards, and the "Methodology" sidebar item shows the **active-state** highlight (the indicator other active nav items use).

---

### UT-10: Stocks setup badge info tooltip opens
**Type:** happy-path
**Surface:** `/stocks` — `InfoTooltip` on setup badge
**Preconditions:** Backend + frontend running; `http://localhost:3835/stocks` loaded with at least one row in the leaderboard.

**Steps:**
1. Navigate to `http://localhost:3835/stocks`.
2. On the first stock row, locate the colored **setup badge** (e.g. "Extended", "Actionable").
3. Click the small **ⓘ** info button immediately to the right of that setup badge.

**Expected Result:** A small popover panel (`role="tooltip"`) opens just below the badge, containing the catalog **definition text for that row's status**. For example, on an "Extended" row the panel text matches the **Extended** meaning shown on the `/methodology` page.

---

### UT-11: Setup tooltip text matches the Methodology page
**Type:** happy-path
**Surface:** `/stocks` ↔ `/methodology`
**Preconditions:** Both pages reachable; backend running.

**Steps:**
1. On `http://localhost:3835/stocks`, note the status label of the first row's setup badge (e.g. "Actionable").
2. Click the **ⓘ** next to that badge and read the tooltip text.
3. In another tab, open `http://localhost:3835/methodology` and read the meaning paragraph on the matching status card (e.g. the "Actionable" card).

**Expected Result:** The tooltip text on `/stocks` is the **same definition** as the meaning paragraph on the corresponding `/methodology` card (single source of truth — the catalog).

---

### UT-12: VCP badge info tooltip + native reason coexist
**Type:** happy-path
**Surface:** `/stocks` — `InfoTooltip` on VCP badge
**Preconditions:** `http://localhost:3835/stocks` loaded; at least one row flagged with a **VCP** badge (apply the VCP filter first if needed to find one).

**Steps:**
1. Locate a row showing a **VCP** badge.
2. Hover the mouse over the VCP badge text itself (not the ⓘ) and wait ~1 second for the browser's native tooltip.
3. Then click the **ⓘ** info button next to the VCP badge.

**Expected Result:** The native browser `title` tooltip (step 2) shows the **per-row VCP reason** for that specific stock. The ⓘ panel (step 3) shows the **generic catalog VCP definition** (same text as the VCP card on `/methodology`). The two are distinct and both work.

---

### UT-13: Info tooltip dismissal via Escape and outside-click
**Type:** validation
**Surface:** `/stocks` — `InfoTooltip` dismissal
**Preconditions:** `http://localhost:3835/stocks` loaded with at least one row.

**Steps:**
1. Click a setup badge's **ⓘ** button to pin the tooltip panel open.
2. Confirm the panel is visible.
3. Press the **Escape** key.
4. Re-open the panel by clicking the same **ⓘ** again.
5. Click anywhere on an empty part of the page **outside** the panel.

**Expected Result:** After step 3 the panel closes. After step 5 the panel closes again. The panel does not remain stuck open after Escape or an outside click.

---

### UT-14: Info tooltip keyboard focus accessibility
**Type:** ux
**Surface:** `/stocks` — `InfoTooltip`
**Preconditions:** `http://localhost:3835/stocks` loaded with at least one row.

**Steps:**
1. Click once on the page background, then press **Tab** repeatedly until keyboard focus lands on a setup badge's **ⓘ** button (its accessible label is "Definition of <status>", e.g. "Definition of Actionable"; the VCP one is "Definition of the VCP pattern").
2. Observe the panel while the button is focused.
3. Press **Tab** again to move focus away.

**Expected Result:** When the ⓘ button receives keyboard focus, the tooltip panel opens; when focus leaves, the panel closes. The button is reachable by keyboard and announces an accessible label.

---

### UT-15: Setup filter options sourced from catalog
**Type:** happy-path
**Surface:** `/stocks` — Setup filter dropdown
**Preconditions:** Backend + frontend running; `http://localhost:3835/stocks` loaded.

**Steps:**
1. Navigate to `http://localhost:3835/stocks`.
2. Open the **Setup** filter control (dropdown/select for setup status).
3. Read the list of options.

**Expected Result:** The Setup filter lists the **six** setup statuses (Actionable, Breakout-watch, Pullback-watch, Extended, Avoid, Risk-off-watchlist) in catalog order (plus any "All"/clear option that already existed). No VCP entry appears in the Setup status options.

---

### UT-16: Setup filter narrows the leaderboard (J-02)
**Type:** happy-path
**Surface:** `/stocks` — Setup filter
**Preconditions:** `http://localhost:3835/stocks` loaded with multiple rows of mixed statuses.

**Steps:**
1. Note the total number of rows currently shown.
2. Open the **Setup** dropdown (labeled "Setup", aria-label "Filter by setup status") and select **"Actionable"**.

**Expected Result:** The leaderboard updates to show **only rows whose setup badge reads "Actionable"**, and the `N / total` counter to the right of the filters drops to the Actionable count. Rows of other statuses are removed. The row count is less than or equal to the original count, and every visible row's setup badge is "Actionable".

---

### UT-17: VCP filter still works (regression J-16)
**Type:** regression
**Surface:** `/stocks` — VCP filter
**Preconditions:** `http://localhost:3835/stocks` loaded; backend running.

**Steps:**
1. Clear any active Setup filter (set the **Setup** dropdown to "All setups").
2. Open the **VCP** dropdown (labeled "VCP", aria-label "Filter by VCP pattern") and select **"VCP only"**.

**Expected Result:** The leaderboard narrows to **only rows flagged with a VCP badge**. The added catalog fetch does not break this filter — behavior is identical to before this iteration.

---

### UT-18: Setup filter graceful fallback when catalog fails
**Type:** error
**Surface:** `/stocks` — Setup filter fallback path
**Preconditions:** Stocks data available, but the methodology endpoint unavailable. To simulate: this requires the `/api/methodology` fetch to fail while `/api/stocks` succeeds (e.g. block the methodology request via browser devtools network throttling/blocking, or use a backend state where only that route errors).

**Steps:**
1. With the methodology fetch failing but stock data loaded, navigate to `http://localhost:3835/stocks`.
2. Confirm the leaderboard rows still render.
3. Open the **Setup** filter and read the options.
4. Select one of the listed statuses.

**Expected Result:** The leaderboard still loads and the Setup filter still lists the statuses **present in the loaded data** and still narrows rows when a status is selected. The page does not crash or go blank when the catalog fetch fails. (Tooltips may be unavailable in this degraded mode — that is acceptable; the core leaderboard + filters must keep working.)

---

### UT-19: Stocks leaderboard regression (warm load + existing filters)
**Type:** regression
**Surface:** `/stocks`
**Preconditions:** Backend + frontend running.

**Steps:**
1. Navigate to `http://localhost:3835/stocks` and wait for the leaderboard to load.
2. Confirm rows render with their existing columns (ticker, scores, setup badge, etc.).
3. Apply and then clear the Setup filter; set VCP to "VCP only" and then back to "All"; also exercise the existing **Sector** filter.

**Expected Result:** The leaderboard loads normally despite the new `/api/methodology` fetch. All existing columns render. Applying/clearing filters returns the leaderboard to the expected row sets. No new errors or blank states are introduced.

---

### UT-20: Methodology discoverability (UX)
**Type:** ux
**Surface:** Sidebar → `/methodology`
**Preconditions:** Backend + frontend running; start at `http://localhost:3835/`.

**Steps:**
1. As a new user, look at the sidebar and find where you would learn what "Extended" or "VCP" means.
2. Click the item you would intuitively choose.

**Expected Result:** The **"Methodology"** sidebar item is discoverable within one click from any page, its label clearly signals a glossary/definitions page, and clicking it lands on the documentation. The feature is reachable in ≤ 2 clicks from home.

---

## Coverage Summary

| Surface | Smoke | Happy | Validation | Error | Regression | UX |
|---------|-------|-------|------------|-------|------------|-----|
| `/methodology` | ✓ (UT-01) | ✓ (UT-02,03,04,05) | | ✓ (UT-06) | | ✓ (UT-07) |
| `/stocks` (tooltips) | | ✓ (UT-10,11,12) | ✓ (UT-13) | | | ✓ (UT-14) |
| `/stocks` (filters) | | ✓ (UT-15,16) | | ✓ (UT-18) | ✓ (UT-17,19) | |
| Sidebar | ✓ (UT-08) | ✓ (UT-09) | | | | ✓ (UT-20) |

**Priority:** P1 = UT-01, UT-02, UT-08, UT-09, UT-10, UT-15, UT-16 (smoke + core happy paths). P2 = UT-03, UT-04, UT-05, UT-06, UT-11, UT-12, UT-13, UT-17, UT-18, UT-19. P3 = UT-07, UT-14, UT-20.
