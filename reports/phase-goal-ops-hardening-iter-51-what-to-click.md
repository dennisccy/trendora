# Phase goal-ops-hardening-iter-51 — What to Click (Operator Verification Guide)

**Phase:** goal-ops-hardening-iter-51
**Time required:** ~5 minutes
**Written by:** ui-impact-analyst (combined mode — standing in for ui-test-designer)

---

## Prerequisites

- Frontend running at `http://localhost:3255`; backend running at `http://localhost:8255`
- No login required — no authentication gate exists in this codebase (confirmed: both
  `curl http://localhost:3255/data` and `curl http://localhost:3255/research/factor-lab` returned `200`
  with no redirect)
- No special setup needed. This guide reads state that **already exists** on a build that has completed
  at least one backfill — true on this build right now (a 2011-03-16 backfill already has `factor_lab_all`
  in its `aggregates_refreshed`). It does **not** require you to trigger a fresh ingest job — see the note
  at the end if you want to verify end-to-end from scratch.

---

## Verification Steps

1. Open `http://localhost:3255/research/factor-lab`
   - **Expect:** within 2–3 seconds the page shows the heading "Research — Factor Lab" and a sortable
     table with multiple factor rows (e.g. "Leadership score"). The amber "Still computing — Xs elapsed"
     card must **not** appear — that card used to be the norm on this exact page right after any data
     load, before this iteration.

2. Open a terminal and run:
   `curl -s -o /dev/null -w "%{http_code} %{time_total}s\n" "http://localhost:8255/api/research/factor-lab?all=true"`
   - **Expect:** `200` and a time under 1 second (confirmed `0.008s`–`0.043s` on this build). This exact
     call used to take **578–875 seconds** on the request path before this iteration — that is the number
     this whole iteration exists to fix.

3. Open `http://localhost:3255/data`
   - **Expect:** page loads; the "Job progress" card shows the most recent run's status badge reading
     "ok" (or similar — a completed, non-failed state).

4. In that same card, find the small grey line starting "Refreshed:"
   - **Expect:** the comma-separated list includes "factor lab all" among the other terms (e.g.
     "coverage", "research hot keys"). This exact term did not exist in any run's list before this
     iteration's code shipped.

5. Scroll down to the "Run History" table and find the same run's row
   - **Expect:** the identical "Refreshed: … factor lab all …" line repeats there.

6. Back on `http://localhost:3255/research/factor-lab`, click the "N" column header
   - **Expect:** rows re-order immediately — no page reload, no error.

7. Click anywhere on the first row of the table
   - **Expect:** it expands in place to show a D1…D10 decile grid beneath it — no error.

8. Navigate to `http://localhost:3255/research` (the Research hub)
   - **Expect:** a tile titled "Factor Lab" is present; clicking it returns you to step 1's page.

---

## What "Working Correctly" Looks Like

- `/research/factor-lab` shows real numbers within a couple of seconds, every time — never a multi-minute
  spinner or an unlabeled blank wait.
- `/data`'s "Refreshed: …" line names "factor lab all" for any run whose finalize tail warmed it
  successfully — one more honest entry in an already-existing audit trail, not a new UI element.

## Common Issues

- **Blank page / error screen:** confirm both servers are up —
  `curl http://localhost:8255/api/health` should return `200`, and `curl http://localhost:3255` should
  return `200`.
- **"Still computing" notice appears and stays for minutes:** check `logs/backend.log` for
  `"J-05 finalize-tail phase timing: ... phase=factor_lab_all_warm ..."`. If the most recent run's
  "Refreshed:" line on `/data` does not include "factor lab all", the warm either hasn't run yet (a job
  is still mid-flight) or degraded (see the dev handoff's "Known Issues" for the disclosed
  memory-pressure-isolation path). The page falling back to a live compute in that case is the
  **pre-existing** fallback behavior, not new breakage.
- **"Refreshed:" line missing entirely:** this line only appears when `aggregates_refreshed` is non-empty
  for that run — a fetch-only job with no backfill/rebuild work legitimately has nothing to show here;
  check the run's job kind first.
- **Want to verify end-to-end from a brand-new job instead of reading the already-completed run?** A
  freshly-triggered job now takes roughly **15–20 minutes** to reach "ok" (up from ~12 minutes before this
  iteration), because the new warm step (measured ~584s / ~9.7 min on this host) always runs as part of
  every job's finalize step. This is a disclosed, accepted trade-off — not a hang — but it will not fit
  inside this 5-minute guide; budget it separately (see UT-03/UT-08 in the full UI test plan).
