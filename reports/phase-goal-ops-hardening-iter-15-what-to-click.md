# Phase goal-ops-hardening-iter-15 — What to Click (Operator Verification Guide)

**Phase:** goal-ops-hardening-iter-15
**Time required:** ~5 minutes
**Written by:** ui-test-designer

---

## Prerequisites

- Frontend running at `http://localhost:3255`, backend at `http://localhost:8255`. No login required.
- **Do not restart either service to get started.** Both were left running warm after this iteration's
  own measurement pass specifically so this check wouldn't need a restart — restarting would cold-evict
  the backend's forward-aggregate cache and turn this quick check into a multi-minute one. If the
  frontend needs (re)starting, run `bash scripts/start-frontend.sh` only — not the combined
  `bash scripts/dev.sh`, which also restarts the backend.
- **This phase changes zero on-screen pixels.** Nothing will look different from before — you are
  confirming a backend timing fix (concurrent requests no longer pile up redundant work) that has no new
  button, page, or label of its own. The one thing you *can* observe is that `/backtest` keeps behaving
  normally.

---

## Verification Steps

1. Open `http://localhost:3255/backtest` in your browser
   - **Expect:** The page loads within a few seconds, showing the "Forward-test scorecard" table (rows
     `1d`/`5d`/`10d`/`20d`/`60d`), the "Leadership cohorts" section, and a "Viewing as-of ..." badge near
     the top. No red "Backend unavailable" box, no page stuck on gray pulsing placeholder cards.

2. Open a **second browser tab** and navigate to the exact same `http://localhost:3255/backtest` URL
   - **Expect:** The second tab loads just as fast (a couple of seconds) and shows the exact same numbers
     in the Forward-test scorecard table as the first tab — two people opening the page at once still get
     one consistent, correct answer.

3. Go to `http://localhost:3255/data`
   - **Expect:** Page loads with a "Start a fetch / backfill job" card at the top. The badge in the top
     bar reads "Ready" with a green dot.

4. Scroll to the "Run history" table at the very bottom of the page
   - **Expect:** Rows from prior runs are listed, each showing a Status (e.g. "ok"), a date Range, and a
     "Symbols ok/failed" count — confirms the page still reads persisted job history correctly through
     the same shared code path this iteration touched.

5. Click into any one run's row (or its linked detail page)
   - **Expect:** Its leaderboard/detail view renders populated values — not a blank page, not an error.

6. Compare everything you just saw against your memory of the app before this iteration (or against
   `reports/phase-goal-ops-hardening-iter-14-what-to-click.md`)
   - **Expect:** Everything looks exactly the same — same headings, same cards, same navigation. This
     iteration adds no new button, page, or label; the entire fix happens invisibly, behind the scenes.

---

## What "Working Correctly" Looks Like

- `/backtest` loads quickly and shows the same numbers whether you open it once or in two tabs at once.
- `/data`'s Run history still shows prior runs correctly, and clicking into one still works.
- Nothing on screen looks new, different, or missing compared to before this iteration.

## Common Issues

- **`/backtest` shows the red "Backend unavailable" card, or hangs for a long time**: if the backend's
  cache was recently cold-started (rather than left warm from a prior pass), a genuine first-time load can
  legitimately take minutes — this is a known, already-recorded, not-yet-closed finding (see
  `reports/perf-budgets.md`), not something to re-diagnose here. If it happens on a service that was
  supposedly left warm and running, report it plainly rather than assuming it will resolve itself.
- **The two `/backtest` tabs show different numbers**: report this immediately and verbatim — this would
  be a genuine regression in the exact code this iteration changed.
- **`/data` or `/scanner-runs` won't load, or the top-bar badge is stuck on "Checking backend…" / red
  "Backend unavailable"**: confirm the backend is actually up (`curl http://localhost:8255/api/health`)
  before assuming a UI problem.
- **Full crash/restart verification (J-04) is a separate, longer, operator-scheduled check** — it is not
  part of this 5-minute pass. See `reports/phase-goal-ops-hardening-iter-15-ui-test-plan.md` (UT-05) if
  that fuller check is specifically needed this iteration; carrying forward iter-14's already-closed live
  pass of that same journey is an acceptable substitute since this iteration does not touch its code.
