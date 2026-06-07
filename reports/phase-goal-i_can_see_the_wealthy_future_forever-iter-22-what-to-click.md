# Phase goal-i_can_see_the_wealthy_future_forever-iter-22 — What to Click (Operator Verification Guide)

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-22
**Time required:** ~5 minutes
**Written by:** ui-test-designer

---

## Prerequisites

- Frontend running at `http://localhost:3835`
- Backend running on `:8000` (if the page shows a red **"Backend unavailable"** card, start the backend first)
- No login required
- For the rate-limit/Resume steps you need a provider that 429s (real Yahoo 429 is enough) **or** an
  injected scripted-429 provider. If neither is available, those steps are expected to show a normal
  `ok`/`failed` job instead — note "provider not rate-limited in this environment" and move on (this is
  the spec's expected offline outcome, not a bug).

---

## Verification Steps

1. Open `http://localhost:3835/data` in your browser
   - **Expect:** The **"Data Manager"** page loads. You see a **"Dataset coverage"** card, a **"Start a
     fetch / backfill job"** form, and a **"Job progress"** card. No red "Backend unavailable" box.

2. In the form, confirm **"Job kind"** is **"Backfill snapshots"**, leave the prefilled dates, and click **"Start"**
   - **Expect:** The button shows "Job running…", then the "Job progress" card reaches a green **`ok`**
     badge with "Snapshots backfilled N/N dates".
   - **Broken looks like:** the job card stays blank, or the header hint shows a `<source> ·` segment
     for this backfill (it must **not** — backfill jobs show no import source).

3. Change **"Job kind"** to **"Fetch EOD prices"**
   - **Expect:** An **"Import source"** dropdown appears, plus a small availability line ("available" in
     green or "needs key" in amber) below the form row.

4. In **"Import source"**, pick a source whose option ends in **"· needs key"**
   - **Expect:** A masked field labeled **"Session API key for &lt;source&gt;"** (a black-dots password
     box) appears, with helper text "Held in memory for this run only — never written to disk…".
     (If every source says "available", skip this step — no key field is expected.)

5. Type `SENupKEY123` into that key field, leave a multi-day date range, and click **"Start"**
   - **Expect:** The fetch starts. While it runs you should see a **"chunk X/N"** badge next to the
     status badge if the import spans multiple chunks, and the X advances as chunks finish.

6. Wait for the job to settle, then read the **"Job progress"** card status badge
   - **Expect (if the provider 429s):** An **amber "rate-limited — resumable"** badge (NOT red
     "failed"), an amber callout reading "Rate-limited — paused at chunk X/N… resume to continue", a
     "&lt;n&gt; done · &lt;m&gt; remaining" line, and an amber **"Resume"** button.

7. In the job-card error list and in the **"Run history"** table's **Summary** column, look for the key
   - **Expect:** The text `SENupKEY123` and any `?token=`/`?apikey=` string are **absent** from both
     the error list and run history — the key never appears in surfaced errors (security check).
   - **Broken looks like:** seeing `SENupKEY123` or a `?token=…` URL anywhere on screen → FAIL.

8. Click the amber **"Resume"** button (type any dummy key first if a resume key field is shown)
   - **Expect:** The job card re-enters a running/progress state for the same import, the chunk badge
     continues from where it paused (it does **not** reset to 0/N), and any key field clears to empty.

9. Restart the backend (by its port), then reload `http://localhost:3835/data`
   - **Expect:** A **"Resumable imports"** card appears below "Job progress", listing the paused import
     with an amber "chunk X/N" badge, its source, date range, "done / remaining / bars so far", and its
     own **"Resume"** button. (If nothing is paused, the panel is **absent** — that is correct.)

10. Spot-check that no new date dropdown was introduced
    - **Expect:** The Job form's Start/End dates are plain calendar (`type="date"`) inputs, and the only
      date **dropdown** anywhere is the global as-of switcher in the page header — the new chunk/Resume
      controls add no second date selector.

---

## What "Working Correctly" Looks Like

- A chunked fetch shows a **"chunk X/N"** badge that climbs as chunks complete.
- A rate-limited fetch ends in an **amber "rate-limited — resumable"** state with a working Resume
  button — clearly different from the red "failed" state.
- A paused import still appears under **"Resumable imports"** after the backend is restarted, and can
  be resumed from there.
- Backfill jobs show **no import-source** in the job-progress header.
- The pasted API key (`SENupKEY123`) never shows up in any error text or run-history row.

## Common Issues

- **Red "Backend unavailable" card**: backend is down — check `curl http://localhost:8000/health`.
- **Every page is a dead shell ("Checking backend…", 404 on `_next/static/chunks/main-app.js`)**: the
  dev server's `.next` was clobbered by a prod build — record SKIPPED, not FAIL (MEMORY
  `browser-qa-dead-shell-next-cache`).
- **No "rate-limited — resumable" state appears**: the provider returned data/`ok` or a plain
  `failed` instead of a 429 in this environment — expected offline; the machinery is proven by the
  API tests (TC-05/TC-06/TC-13). Not a UI defect.
- **"Resumable imports" panel never appears**: correct when no import is paused — the panel is hidden
  for an empty list by design.
