# Phase goal-market-compass-iter-34 — What to Click (Operator Verification Guide)

**Phase:** goal-market-compass-iter-34
**Time required:** ~5 minutes
**Written by:** ui-test-designer

---

## Prerequisites

- Frontend running at `http://localhost:3255`.
- Backend running against the current database — no login required.
- No new capability ships this iteration (backend-only closing/confirmation round: an extended
  J-09 memory re-measurement plus a goal-mode harness fix). This guide instead re-checks the
  regression risk this iteration actually carries — that none of the eleven Must-have journeys
  regressed, with special attention to the two previously-incident-affected dates the J-10/J-11
  recovery arc repaired.

---

## Verification Steps

1. Open `http://localhost:3255/?asof=2026-08-12` — one of the two dates the iter-5 drill deleted
   and J-10/J-11 recovered.
   - **Expect:** The page loads cleanly — no 400/500 error, no blank screen. Today's tiles show
     2026-08-12's data.

2. Scroll to the manifest strip at the bottom of that page.
   - **Expect:** The strip shows a basis disclosure reading "available" or "rebuilt" — never a
     blank or obviously stale claim. This is the single most likely regression point this
     iteration, since the whole J-10/J-11 arc exists to make this date serve cleanly again.

3. Open `http://localhost:3255/?asof=2026-08-05` — a second incident date whose manifest was
   previously orphaned (0 surviving source runs).
   - **Expect:** The page still renders without error, and the manifest strip shows an honest
     "unknown"/"not yet proven" basis state rather than a false "available" claim.

4. Return to the latest data: open `http://localhost:3255/` (no `?asof` in the URL).
   - **Expect:** Page renders top to bottom: market-state band, plain-English summary, "What
     changed," Leadership rotation, Next-session focus, and the manifest strip.

5. On the plain-English summary card, click "Show cited facts."
   - **Expect:** A disclosure opens listing a template id and cited facts for each sentence — no
     forecast or imperative-trade wording anywhere.

6. Read the "What changed" card's header line.
   - **Expect:** It names a specific prior session date (never blank) and the gap in days to today.

7. Click into one candidate card under "Next-session focus."
   - **Expect:** The card shows Leadership/Entry/Risk labels, an eligibility checklist, and a
     "what would change this" panel — not just a bare score.

8. Click "Market" in the left sidebar.
   - **Expect:** Navigates to `http://localhost:3255/market`; "Today" is listed before "Market" in
     the sidebar; the two glance cards, the regime × phase cross-view card, three breadth cards,
     Top Sectors, Candidate Counts, Top Themes, and Market Phase & Severity card all render.

9. Navigate to `http://localhost:3255/stocks` and select "Unassigned" in the Sector filter.
   - **Expect:** The "Unassigned" count is at most 5% of total resolved members shown (never
     anywhere near 78%).

10. Open `reports/perf-budgets.md` and scroll to the newest addendum (Addendum 45).
    - **Expect:** It records this iteration's two independent VmPeak re-measurements, both
      ≤ 2,621,440 kB (2.5 GB) — the J-09 confirmation this iteration exists to close. (This step
      is a file check, not a browser check — J-09 and J-10's own `docs/goal.md` Acceptance text
      waives their walkthrough as backend-only.)

---

## What "Working Correctly" Looks Like

- Both previously-incident-affected dates (`?asof=2026-08-12`, `?asof=2026-08-05`) load without
  error and show an honest manifest basis state — this is the load-bearing check for this
  iteration's closing-confirmation scope.
- Every Today-page section (summary, What changed, candidates, manifest strip) renders served
  values with no blank/placeholder text and no forecast or imperative wording.
- `/market` still shows every card it showed before the relocation — nothing dropped.
- Addendum 45 in `reports/perf-budgets.md` shows both re-measurements under the 2.5 GB bar.

## Common Issues

- **`?asof=2026-08-12` or `?asof=2026-08-05` shows a 400 or blank page**: this would indicate the
  J-10/J-11 incident recovery regressed — stop and escalate immediately, this is the highest-risk
  regression path this iteration guards against.
- **Manifest strip shows "available" on a date with no recorded generation data**: this is the
  fabricated-basis defect J-11's A4/A4-bis fix specifically closed — a regression here is a hard
  fail.
- **Blank Today page / error screen on `/`**: check the backend is running
  (`curl http://localhost:8000/api/health`).
- **Addendum 45 missing or the file shows deletions in `git diff --stat`**: the append-only
  requirement (TC-3) was violated — report immediately, do not proceed.
