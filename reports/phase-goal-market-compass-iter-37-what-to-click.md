# Phase goal-market-compass-iter-37 — What to Click (Operator Verification Guide)

**Phase:** goal-market-compass-iter-37
**Time required:** ~5 minutes
**Written by:** ui-test-designer

---

## Prerequisites

- Frontend running at `http://localhost:3255`.
- Backend running against the current database — no login required.
- No new capability ships this iteration (a backend-only closing round: a test-fixture correction
  and an internal `assert`-to-`raise` guard conversion in `compass.py`, both invisible to a user).
  This guide instead re-checks the two things this closing round exists to prove: (1) the
  Leadership rotation panel genuinely renders both directions — the prior acceptance screenshot
  was confirmed blank — and (2) nothing else regressed across all twelve other Must-have journeys.

---

## Verification Steps

1. Open `http://localhost:3255/` (no `?asof` — the latest/frontier session, `2026-08-12`).
   - **Expect:** The page loads cleanly, top to bottom: market-state band, plain-English summary,
     "What changed," Leadership rotation, Next-session focus, manifest strip.

2. Scroll to the card titled "Leadership rotation" (just below "What changed").
   - **Expect:** This is the load-bearing check for this iteration. The card shows real content —
     not a blank or single-colour panel. Under "Sector rotation" you should see two side-by-side
     columns badged "Gaining" and "Losing," each listing at least one row like
     "Regional Banks (SPDR) 13 → 10 (-3) · improving" (a rank that fell = improving) on one side
     and "Home Construction (iShares) 21 → 25 (+4) · deteriorating" (a rank that rose = worsening)
     on the other. If a side is genuinely empty it shows text like "No sector gained ground beyond
     the threshold this session." — never a blank space.

3. Scroll a little further to the "Theme rotation" subsection directly below Sector rotation.
   - **Expect:** The same two-column "Gaining"/"Losing" layout, each row showing a signed delta
     (`+` or `-`) and a direction word (e.g. "improving," "deteriorating").

4. Scroll back up to the "What changed" card above Leadership rotation.
   - **Expect:** Its header names a specific prior session date and a day gap (never blank); the
     listed entries are unchanged from before — the rotation section below does not duplicate or
     alter this card's content.

5. Scroll down to "Next-session focus" and click into any one candidate card.
   - **Expect:** The card shows Leadership/Entry/Risk labels, an eligibility checklist (each row
     Pass/Miss/Supportive/Neutral/Unknown/NA), and a "what would change this" panel. If the Entry
     or Risk row shows "Miss," it should read as a caution, not as a reason the candidate is
     absent — only the leadership floor excludes a name from this list.

6. Scroll to the manifest strip at the very bottom of `/` and click the "Audit table — comparison
   cohort (…) + near-threshold shadow (…)" line to expand it.
   - **Expect:** A table appears with a Disposition column. No row shows a Leadership score at or
     above 80.0 labeled "below selection floor" — that combination was last iteration's bug and
     must not reappear.

7. Open `http://localhost:3255/?asof=2026-08-12` in the address bar directly (one of the two dates
   a prior incident deleted and a later recovery restored).
   - **Expect:** The page still loads cleanly with no 400/500 error and no blank screen — this is
     the highest-risk regression path this closing round guards against.

8. Navigate to `http://localhost:3255/stocks` and select "Unassigned" in the Sector filter.
   - **Expect:** The "Unassigned" count is at most 5% of total resolved members shown (never
     anywhere near 78%).

9. Click "Market" in the left sidebar.
   - **Expect:** Navigates to `http://localhost:3255/market`; "Today" is listed before "Market" in
     the sidebar; the glance cards, the regime × phase cross-view card, and all the breadth/sector/
     theme cards still render — nothing missing.

10. Open `reports/perf-budgets.md` and confirm the newest entry is still Addendum 45.
    - **Expect:** No new addendum and no deleted content — this iteration is not supposed to touch
      this file at all (memory work is out of scope this round). (This step is a file check, not a
      browser check.)

---

## What "Working Correctly" Looks Like

- The Leadership rotation card (step 2-3) shows real, multi-colour, readable content with a
  populated "Gaining" side and a populated "Losing" side, each row carrying a signed delta and a
  direction word — this is the single defect this iteration exists to close.
- `?asof=2026-08-12` (step 7) still loads without error — the incident-recovery arc from prior
  iterations has not regressed.
- Every Today-page section (summary, What changed, candidates, manifest strip) renders served
  values with no blank/placeholder text and no forecast or imperative wording.
- No comparison-cohort row shows a high Leadership score labeled "below selection floor" (step 6).
- `/market` still shows every card it showed before the relocation — nothing dropped.

## Common Issues

- **The Leadership rotation card looks blank, white, or shows only one colour**: this is exactly
  the defect this iteration exists to fix and measure — stop and escalate immediately; do not
  accept a screenshot of this state as evidence.
- **Only one of "Gaining" / "Losing" ever shows content, on every visit**: this could indicate the
  both-directions guarantee (TC-3) regressed — check whether the missing side's empty-state text
  ("No sector gained/lost ground beyond the threshold this session.") is present; if neither the
  rows nor the empty-state text appears, that is a hard fail.
- **`?asof=2026-08-12` shows a 400 or blank page**: this would indicate the J-10/J-11 incident
  recovery regressed — stop and escalate immediately.
- **A comparison-cohort row shows Leadership ≥ 80.0 with Disposition "below selection floor"**:
  this is the exact J-12 defect from two iterations ago reappearing — report immediately.
- **Blank Today page / error screen on `/`**: check the backend is running
  (`curl http://localhost:8000/api/health`).
