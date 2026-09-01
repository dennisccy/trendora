# Phase goal-market-compass-iter-32 — What to Click (Operator Verification Guide)

**Phase:** goal-market-compass-iter-32
**Time required:** ~5 minutes
**Written by:** ui-test-designer

---

## Prerequisites

- Frontend running at `http://localhost:3255`
- Backend running at `http://localhost:8255`
- No login required
- Do NOT use the `/data` page's Remove or Backfill controls during this check — this iteration is a
  read-only re-measurement pass and none of its authorized as-of values require new data

---

## Scope note

This iteration (`goal-market-compass-iter-32`) shipped **zero UI changes** — it re-measured the
backend's standing memory footprint (J-09) and re-verified that the ten other shipped journeys
(J-01–J-08, J-10, J-11) still pass. There is no new capability to click through, so this guide is
scoped to the same journeys instead of a "what's new" tour: the fastest way to catch a real
regression is to look at the same pages a real user already relies on. Only three `as_of` values are
safe to request this iteration — no `?asof` param (the frontier date, 2026-08-12), `?asof=2025-04-15`,
and `?asof=1996-02-01` — do not type in any other date.

---

## Verification Steps

1. Open `http://localhost:3255/` in your browser (no `?asof` in the URL)
   - **Expect:** The page loads with, top to bottom: a "Market state" card, a plain-English summary
     card, a "What changed" card, "Leadership rotation", "Next-session focus", and a "Manifest" card
     — no blank page, no crash, no "backend not reachable" message on any card

2. On the "What changed" card, click the "Suppressed moves (N)" disclosure to expand it
   - **Expect:** It expands to show exactly N entries (the number in its own header) — the card
     also names a specific prior session date and a day gap near the top

3. On the summary card, click "Show cited facts" to expand it
   - **Expect:** Every listed sentence shows a template id and its cited facts — never the "— no
     cited facts." fallback text for a normal run

4. Scroll to "Next-session focus", open the first candidate card, then click "Eligibility
   checklist" to expand it
   - **Expect:** Every checklist row shows a verdict from Pass / Miss / Supportive / Neutral /
     Unknown / NA, each with a threshold and an actual value — no blank rows

5. Scroll to the "Manifest" card
   - **Expect:** It shows a mode badge (e.g. "at ingest"), a "version" badge, and a "frozen" badge
     — not "not frozen" — plus a candidates table with real Leadership/Entry/Risk values

6. Click "Market" in the left sidebar (second item, right after "Today")
   - **Expect:** Navigate to `http://localhost:3255/market`; the page shows the two glance cards
     plus the full former dashboard inventory: three breadth cards, "Top Sectors", "Candidate
     Counts", "Top Themes", and "Market Phase & Severity" — nothing missing

7. Navigate to `http://localhost:3255/?asof=2025-04-15`
   - **Expect:** The Today tiles now show 2025-04-15's stored values, and the "Manifest" card shows
     a visible "retrospective" label instead of the frozen frontier stamps

8. Navigate to `http://localhost:3255/stocks`, open the "Sector" dropdown, and select "Unassigned"
   - **Expect:** The filtered row count is a small minority of the total (at most about 5%) — not
     the large majority it was before this fix; no row shows a blank or literal "null" sector

9. Open `http://localhost:8255/api/compass` in a new tab (no `as_of` param), reload it once more,
   and compare the two responses by eye (or Ctrl+F for the `"manifest_hash"` value in each)
   - **Expect:** Both fetches show the identical `manifest_hash` and `version` — nothing changed
     between requests, confirming the frozen manifest still hasn't moved

10. Open `reports/perf-budgets.md` in a text editor or GitHub and scroll to the newest addendum
    - **Expect:** A new "Addendum 43" entry exists below Addendum 42 (Addendum 40/41/42 text is
      unchanged), stating the freshly measured backend memory figure in kB, its comparison to the
      2.5 GB target, and a citation to a raw evidence file under
      `runs/goal-market-compass-iter-32/`

---

## What "Working Correctly" Looks Like

- Every page in steps 1, 6, 7, and 8 loads instantly with real data — no spinner stuck forever, no
  error boundary, no page that silently shows nothing
- Every disclosure you expand (steps 2, 3, 4) shows real content matching its own header count —
  never a mismatch between a header number and what's actually listed inside
- The two `GET /api/compass` fetches in step 9 are identical — if they differ, something moved that
  this iteration's spec says must not move

## If Something Looks Wrong

- **`/` or `/market` shows "backend not reachable"**: confirm the backend is actually running at
  `http://localhost:8255` — visit `http://localhost:8255/api/compass` directly; if that also fails,
  restart it with `bash scripts/start-backend.sh`
- **The Manifest card shows "not frozen" at the frontier date**: this would be a real regression —
  the frontier manifest was frozen by a prior iteration's ingest and this iteration performs no new
  freeze, so it should still read "frozen"
- **The two `GET /api/compass` fetches in step 9 differ**: stop and report it — this iteration's
  entire premise is that the `cache_size` re-verification moves zero displayed value; a diff here
  contradicts the perf-budgets.md Addendum 43 claim and should block sign-off
- **The Sector filter's "Unassigned" share looks close to 78% instead of a small minority**: this
  would mean J-01's sector-mapping regression, not this iteration's own work — report it separately
