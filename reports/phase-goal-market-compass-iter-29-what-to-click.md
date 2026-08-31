# Phase goal-market-compass-iter-29 — What to Click (Operator Verification Guide)

**Time required:** ~5 minutes
**Written by:** ui-impact-analyst (combined mode)

---

## Prerequisites

- Frontend running at `http://localhost:3255`, backend at `http://localhost:8255` (start with
  `bash scripts/start-backend.sh` and `bash scripts/start-frontend.sh` from the repo root if nothing
  answers yet)
- No login required
- **Do not type or click any `?asof=` date other than `2026-08-03`, `2026-08-12`, `2025-04-15`, or no
  date at all.** This iteration froze exactly one new date on purpose; any other date would mint an
  unauthorized new permanent database row.

---

## Steps

1. Open `http://localhost:3255` in your browser
   - **Expect:** The "Today" page loads with subtitle "The ten-second read after the close", no error
     banner. The top-right date badge reads "Data as-of 2026-08-12".

2. In the top bar, click the "Latest" pill button (clock icon, next to the ◀ ▶ arrows)
   - **Expect:** A calendar popover opens, already showing "August 2026" — no need to page back a
     month.

3. Click the day cell numbered "3" in that calendar
   - **Expect:** The popover closes. The page URL becomes
     `http://localhost:3255/?asof=2026-08-03`. The top-bar pill turns amber and reads
     "Viewing as-of 2026-08-03 (historical)".

4. Look at the "Market state" card (first card on the page). Read the small pill badge next to the
   "Regime" score, the pill next to the "Market phase" severity score, and the pill on the right of the
   "Breadth ·" row
   - **Expect:** The three pills read, in order, **"improving"**, **"improving"**, and
     **"little changed"** — none of them says "NA".

5. Scroll down slightly to the "Summary" card and read its first sentence
   - **Expect:** It reads **"Conditions are improving since the prior session (+4.7 regime-score
     points)."** — the word "improving" here matches the Regime badge you just read in step 4.

6. Refresh the page (press F5 or Cmd+R)
   - **Expect:** The URL stays `?asof=2026-08-03` and all three badges from step 4 show the exact same
     words — confirms the data is permanently stored, not a fluke of that one page load.

7. Click the amber "Viewing as-of 2026-08-03 (historical)" pill again, then click "Latest" at the
   bottom of the calendar popover (or use the ◀/▶ arrows to step back to the most recent date)
   - **Expect:** The URL loses the `?asof=` param, the pill returns to plain "Latest", and all three
     direction badges in the Market state card revert to **"NA"** — proves the new real-word rendering
     is scoped to `2026-08-03` only and nothing else was changed.

---

## What "Working Correctly" Looks Like

- On `?asof=2026-08-03` specifically, all three "Market state" badges show plain-English words
  ("improving" / "improving" / "little changed"), never the placeholder "NA".
- The Summary card's first sentence and the Regime badge always agree on the same direction word.
- Every other date (Latest, or any date you reach without typing `2026-08-03`) still shows "NA" for all
  three badges, exactly as it did before this change.

## Common Issues

- **Blank page / "Backend unavailable" card**: confirm the backend is running —
  `curl http://localhost:8255/api/health` should return `"readiness": "ready"`.
- **Day "3" is greyed out / not clickable in the calendar**: the calendar only lists dates with a
  stored scanner run; if this happens, do not manually type `?asof=2026-08-03` into the URL bar as a
  workaround unless you are the developer verifying this exact iteration — ask the developer to confirm
  the date was actually minted before proceeding.
- **Badges still show "NA" after clicking day "3"**: hard-refresh (Cmd+Shift+R) once to rule out a
  stale cached fetch before treating it as a real failure.
