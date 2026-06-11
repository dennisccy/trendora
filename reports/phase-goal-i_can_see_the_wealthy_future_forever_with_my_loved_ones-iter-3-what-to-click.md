# Phase goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-3 — What to Click (Operator Verification Guide)

**Phase:** J-46 — Parallel bounded-worker fetch, per-chunk transactional writes, load-bars-once backfill cache
**Time required:** ~8 minutes (includes ~3-minute throttle wait for rate-limit trigger)
**Written by:** ui-test-designer

---

## Prerequisites

- Frontend running at `http://localhost:3835`
- Backend running at `http://localhost:8835` — confirm with: `curl http://localhost:8835/health` (expect `200 OK`)
- Seed data loaded (NVDA must appear on the `/stocks` page)
- No API key needed for most steps; the alpha_vantage `demo` key is used in steps 3–6 (type it literally: `demo`)

---

## Verification Steps

1. Navigate to `http://localhost:3835/stocks` in your browser
   - **Expect:** The stock list page loads with at least one row visible. NVDA appears with three numeric scores and a letter bucket (A, B, C, D, or E).
   - **Broken looks like:** Blank page, "Checking backend…" spinner that never resolves, or NVDA row showing empty/zero scores.

2. Click the NVDA row to open the detail page
   - **Expect:** Browser navigates to `http://localhost:3835/stocks/NVDA`. The same three scores and the same bucket letter shown on the list page are displayed on this detail page — values are identical.
   - **Broken looks like:** Different score values on the detail page versus the list page, or an error page.

3. Navigate to `http://localhost:3835/data`
   - **Expect:** The Data Manager page loads. An import/fetch form or "Start New Import" section is visible. No "Checking backend…" spinner that never resolves.

4. In the fetch form, select source `alpha_vantage`, type `demo` into the API key field, select at least 3 symbols (e.g., AAPL, MSFT, NVDA), then click the "Start" (or "Fetch" or "Import") button
   - **Expect:** A job card appears showing the job in a running/in-progress state. A progress counter in the format "X / Y symbols" is visible on the card. The X value starts at 0 or 1 and increases over time.
   - **Broken looks like:** No job card appears, the counter immediately shows a value higher than the total Y, or the page crashes.

5. Watch the job card's "X / Y symbols" counter for 60 seconds
   - **Expect:** The counter increases monotonically. The X value never exceeds the Y total (e.g., you never see "6 / 5"). Counts reflect only durably committed fetches.
   - **Broken looks like:** Counter shows X > Y at any point, or counter jumps erratically backward.

6. Continue watching the job card until the alpha_vantage demo key triggers a rate limit (approximately 2–4 minutes after starting the job)
   - **Expect:** The job card transitions to an amber-highlighted state with a label containing "rate-limited" or "resumable" text. A "Resume" button appears on the card. The card does NOT show "failed" or "error".
   - **Broken looks like:** Job card shows "failed" instead of a resumable state, or the Resume button does not appear.

7. Click the "Resume" button on the amber job card
   - **Expect:** The job card immediately transitions back to a running/in-progress state. The symbols counter continues incrementing from approximately where it left off — it does not reset to 0.
   - **Broken looks like:** Clicking Resume has no effect, the page errors, or the counter resets to 0 and re-fetches already-committed symbols.

---

## What "Working Correctly" Looks Like

- NVDA shows identical three-score values on both `/stocks` and `/stocks/NVDA` — scores are identical to the decimal shown
- The Data Manager job progress counter never displays a fetched-symbol count higher than the job's declared total
- An alpha_vantage demo-key job transitions to amber "resumable" (not "failed") when rate-limited, and the Resume button restarts the job from the checkpoint

## Common Issues

- **"Checking backend…" that never resolves / dead page shell:** The `.next` folder may be stale from a prior production build. Stop the frontend dev server, delete the `.next` folder in `apps/frontend/`, and restart with `bash scripts/start-frontend.sh`. Do not run browser QA until this is resolved.
- **Backend not responding:** Run `curl http://localhost:8835/health`. If it times out, the backend may still be doing its initial warm-up scan (can take 30–60 seconds on first boot after a clean database). Wait and retry.
- **NVDA not in the stocks list:** The seed data may not be loaded. Check with the development team — do not attempt to fetch live data to fix this during a QA session.
- **Rate limit never triggers in step 6:** The alpha_vantage demo key throttles within ~3 minutes for multi-symbol batches. If more than 6 minutes pass without the amber state, the job may have completed fully (all symbols committed before the limit). In that case, steps 6 and 7 cannot be verified in this session — note them as "not triggered" rather than failed.
