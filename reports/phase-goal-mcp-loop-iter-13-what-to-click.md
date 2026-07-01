# Phase goal-mcp-loop-iter-13 — What to Click (Operator Verification Guide)

**Phase:** goal-mcp-loop-iter-13
**Time required:** ~5 minutes
**Written by:** ui-test-designer

---

## Prerequisites

- Frontend running at `http://localhost:3255`
- Backend running at `http://localhost:8000`
- No login required
- No seed data needed — the evidence ledger is served from the backend automatically

---

## Verification Steps

1. Navigate to `http://localhost:3255/research/factor-combination` in your browser
   - **Expect:** The Multi-factor combination lab page loads, a combination table is visible with multiple cohort rows including a composite row near the bottom. No error banner.

2. Scroll down to the composite cohort row at the bottom of the table. Note the badge on that row with the default factor selection (rs_spy_3m × atr_pct).
   - **Expect:** The badge reads **"Not yet proven"** in a muted/grey style with no link. This is the correct default — the default combination is not certified.

3. Change the horizon selector to **20**, set Leg 1 to **rs_spy_3m / top / quintile**, and set Leg 2 to **high_proximity / top / tertile**. Then scroll back to the composite cohort row.
   - **Expect:** The badge immediately changes to **"Proven"** in an accented (non-grey) style with a ShieldCheck icon. A link is now present on or around the badge. No page reload is needed.

4. Click the **"Proven"** badge (the link inside it).
   - **Expect:** The browser navigates to `http://localhost:3255/evidence` and the page scrolls so the **6th claim row** (the combination row showing rs_spy_3m × high_proximity chips) is visible in the viewport. The URL shows the fragment `#combination-high_proximity-rs_spy_3m-h20`.

5. On the `/evidence` page, verify the 6th row contains the following visible values: chips for **rs_spy_3m:top:quintile** and **high_proximity:top:tertile**, a **"PASS"** verdict badge, holdout edge **"+4.69%"**, control vs. SPY **"+4.69%"**, registration date **"2026-07-01"**, forward-walk status **"Pending"**, and a linkback that reads **"Backs: Multi-factor combination lab →"**.
   - **Expect:** All six values are present on the 6th row. No cell shows the text "Unmapped signal".

6. Click the **"Backs: Multi-factor combination lab →"** link on the 6th evidence row.
   - **Expect:** The browser navigates back to `http://localhost:3255/research/factor-combination`. The page loads without errors.

7. Navigate to `http://localhost:3255/evidence` and count all the claim rows on the page.
   - **Expect:** Exactly **6 rows** are visible. The first 5 rows (leadership score, vcp_contraction at h20, vcp_contraction at h60, entry quality, risk score) each show their own hypothesis chips and linkbacks unchanged — none of them shows "Multi-factor combination lab" as the linkback.

8. Navigate to `http://localhost:3255/stocks` and look at the inline evidence badges on any stock in the list.
   - **Expect:** The Leadership Score badge reads **"Proven"**. Entry Quality and Risk badges read **"Not yet proven"**. No new badge labelled "Combination", "Composite", or "rs_spy_3m × high_proximity" appears anywhere on the stocks page. The badge set is identical to what it was before this iteration.

---

## What "Working Correctly" Looks Like

- On `/research/factor-combination`: the composite row badge flips between "Not yet proven" (muted, no link) and "Proven" (accented, with link) depending on the exact combination selected — only rs_spy_3m × high_proximity at horizon 20 triggers "Proven"
- On `/evidence`: 6 rows total, with the 6th row displaying both condition legs as chips, a PASS verdict, +4.69% edge, and a "Backs: Multi-factor combination lab →" linkback
- Navigation round-trip works in both directions: Proven badge → evidence anchor, and evidence linkback → combination lab

## Common Issues

- **Badge never shows "Proven" even with correct selection**: Verify the backend is running (`curl http://localhost:8000/api/evidence | jq '.claims | length'` should return 6) and that the horizon is set to exactly **20** (not 60 or other)
- **Evidence page shows 5 rows instead of 6**: The backend may be serving an old ledger. Check that `certified-claims.jsonl` has 6 lines in `runs/goal-session-mcp-loop/state/`
- **"Unmapped signal" appears on the 6th row**: The frontend `claimSurface` combination branch is not deployed — frontend may need to be rebuilt
- **Clicking "Proven" badge navigates to /evidence but no scrolling happens**: The anchor `#combination-high_proximity-rs_spy_3m-h20` may not match the row's `id` attribute — inspect the 6th row's `id` in the browser DevTools
