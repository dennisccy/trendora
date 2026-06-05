# Phase goal-i_can_see_the_wealthy_future_forever-iter-21 — What to Click (Operator Verification Guide)

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-21 (J-33 — Import source picker)
**Time required:** ~5 minutes
**Written by:** ui-test-designer

---

## Prerequisites

- Frontend running at `http://localhost:3835`
- Backend running (the `/data` page reads `GET /api/data`)
- No login required
- No special seed data required (the coverage card and source catalog load from config)

> Use a real mouse/keyboard for this guide. (Automated runs only: Chrome MCP's `select` action does not trigger React on this frontend — use the native-setter + bubbling `change` pattern and assert the live DOM. Humans clicking the dropdown are unaffected.)

---

## Verification Steps

1. Open `http://localhost:3835/data` in your browser
   - **Expect:** The "Data Manager" heading loads, with a "Dataset coverage" card and a "Start a fetch / backfill job" card. No red "Backend unavailable" box.

2. Read the grey subtitle directly under "Data Manager"
   - **Expect:** It ends "…grow the **Backtest** evidence." The words "System Health evidence" do NOT appear.

3. In the "Start a fetch / backfill job" card, confirm "Job kind" reads "Backfill snapshots", then look at the form
   - **Expect:** There is NO "Import source" dropdown and NO "Session API key" field for a backfill job.

4. Change the "Job kind" dropdown to "Fetch EOD prices"
   - **Expect:** An "Import source" dropdown appears, pre-selected to "Yahoo · available". Its options are Yahoo · available, Stooq · needs key, Tiingo · needs key, Finnhub · needs key, Alpha Vantage · needs key.

5. With "Yahoo · available" selected, read the small availability line below the form row
   - **Expect:** It reads "Yahoo: available · <reason>" with "available" in green. No password field is shown (Yahoo needs no key).

6. Change "Import source" to "Tiingo · needs key"
   - **Expect:** The availability line changes to "Tiingo: needs key · set $TIINGO_API_KEY or paste a session key" (amber "needs key"), AND a masked "Session API key for Tiingo" password field appears with the caption "Held in memory for this run only — never written to disk…".

7. Leave the key field blank and click "Start"
   - **Expect:** A red inline alert (warning triangle) appears saying a key is required (naming the Tiingo key / env var). No job starts in the "Job progress" card.

8. Change "Import source" back to "Yahoo · available", confirm the Start/End dates are filled (e.g. `2024-01-01` → `2024-01-05`), then click "Start"
   - **Expect:** The "Job progress" card header reads `fetch job · yahoo · 2024-01-01 → 2024-01-05`. The job ends in "failed" or "partial" with an error box "N error(s) (no data fabricated)" and "0 new price bars" — an honest unavailable state, NOT a fabricated success. (Yahoo rate-limits this IP — see "If Something Looks Wrong".)

9. Switch "Job kind" back to "Backfill snapshots" and click "Start"
   - **Expect:** No source/key controls shown; the job runs offline, shows a "Snapshots backfilled" counter, and completes — old J-17 backfill still works.

10. Confirm there is still only ONE date dropdown app-wide
    - **Expect:** The only date `<select>` is the global header as-of switcher. The `/data` Start/End fields stay calendar `type="date"` inputs; the new Import source / Job kind selects are not date controls (J-18 intact).

---

## What "Working Correctly" Looks Like

- The "Import source" dropdown appears **only** for fetch-type jobs (steps 3–4) and lists config providers each tagged "available" or "needs key".
- Selecting a needs-key source (step 6) reveals a masked, never-pre-filled key field and a clear "held for this run only" caption.
- A failing fetch (step 8) shows an explicit error with "(no data fabricated)" and the chosen source id `yahoo` in the header — never invented price bars, never a key string on screen.
- Backfill (step 9) and the single date switcher (step 10) are unchanged.

## If Something Looks Wrong

- **Every page is a dead shell ("Checking backend…", or a 404 on `_next/static/chunks/main-app.js`)**: the dev server's `.next` cache was clobbered by a prod build — restart `next dev`; record browser checks as SKIPPED, not FAIL (MEMORY `browser-qa-dead-shell-next-cache`).
- **The fetch in step 8 succeeds with real bars**: that's even better — it means the provider was reachable. The honest-error path is expected here only because Yahoo rate-limits this IP (MEMORY `data-provider-access-constraints`).
- **No "Import source" dropdown after step 4**: confirm Job kind is "Fetch EOD prices" or "Fetch + backfill" (it is correctly hidden for "Backfill snapshots").
- **"Backend unavailable" red card on load**: backend not running — start it and reload (`curl http://localhost:8000/api/data`).
