# Phase goal-mcp-loop-iter-19 — User-Visible Changes

**Phase:** goal-mcp-loop-iter-19
**Date:** 2026-07-07
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

- Users can again click the "Sector" column header on the `/stocks` leaderboard to sort ascending or descending — this used to crash the entire application (a blank "Application error" screen, nav included) the instant it was clicked, on any dataset containing a company with no mapped sector. It no longer crashes.
- Users can select "Unassigned" from the Sector filter dropdown on `/stocks` to isolate exactly the companies with no mapped GICS sector — currently 422 of 541 leaderboard rows (about 78%). This option did not exist before; there was no way to filter to this bucket.
- Users can open the `/data` Data Manager page for the first time right after a server restart (or at the same moment as several other people) without the backend hanging or crashing — it now reliably finishes loading in roughly 10-20 seconds under the same conditions that previously risked exhausting the server's memory and freezing the whole application.
- If any page hits an unexpected error while the user is on it, the user now sees a contained "Something went wrong on this page" card with a "Try again" button, and can still use the sidebar to navigate elsewhere — instead of the entire application going blank.

---

## What Changed in the Visible UI

- The `/stocks` leaderboard's Sector column now shows the word "Unassigned" (never a blank cell) for any company with no mapped industry sector.
- The `/stocks` leaderboard's Sector filter dropdown now lists an "Unassigned" option, positioned alphabetically among the real sector names (currently between "Technology" and "Utilities").
- The Stock Detail page (`/stocks/{ticker}`) now shows "Unassigned" in its sector chip for a company with no mapped sector, instead of a blank value; unaffected for companies with a real mapped sector (e.g., NVDA still reads "Technology").
- The Scanner Run detail page (`/scanner-runs/{runId}`) now shows "Unassigned" in its Sector column for the same unmapped companies, instead of a blank cell.
- A new contained error card can now appear in place of any page's content if that page throws an unexpected error, reading "Something went wrong on this page" with a "Try again" button — the sidebar navigation and header stay visible and usable around it.
- In the rare case where the outer application shell itself fails to render, a plain fallback page now appears ("Trendora hit an unexpected error" + "Try again") instead of a totally blank browser tab. This fallback intentionally has no sidebar or navigation, since it replaces the entire page shell.

---

## What Old Behavior Changed

- **Sorting `/stocks` by "Sector":** previously this crashed the entire page (including the sidebar nav) to a blank error screen whenever the dataset contained a company with no mapped sector — which is the majority of companies today (~78%). Now it sorts correctly every time, in both directions, and never crashes.
- **Filtering `/stocks` by sector:** previously there was no way to isolate the companies with no mapped sector — that bucket had no filter option. Now "Unassigned" is selectable exactly like any real sector name.
- **Opening `/data` shortly after a restart, or several people opening it at once:** previously this could exhaust the backend's memory and hang the whole application (the exact incident that blocked last iteration's verification). Now it reliably completes in about 10-20 seconds under the same conditions. The numbers and layout the page displays are unchanged — only how reliably the page gets there changed.
- **An uncaught error on any page:** previously any unexpected client-side error wiped out the entire application to a blank screen. Now it is contained to the page that failed, with a retry option, while the rest of the app (nav, header) keeps working.

---

## Not Visible Yet

- None — every change in this iteration restores or hardens something users can already reach; no new backend capability was added without a corresponding UI change. (This iteration was scoped as a fix-and-verify pass, not new-feature work — see `docs/phases/goal-mcp-loop-iter-19.md`'s "New user-facing capability: No net-new capability.")
