# Phase goal-ops-hardening-iter-51 — User-Visible Changes

**Phase:** goal-ops-hardening-iter-51
**Date:** 2026-08-07
**Written by:** ui-impact-analyst

---

## Scope note (read before the sections below)

`runs/goal-ops-hardening-iter-51/plan.md` and the phase spec both mark **Frontend Present: no**, and
that is correct in the narrowest sense: `git diff --stat` for this iteration touches only
`apps/backend/app/engine/{data_manager,research}.py`, their tests, and `reports/perf-budgets.md` — zero
files under `apps/frontend/` changed. However, the phase spec's own **"New user-facing capability"** and
**"Product surface delta"** sections describe a real, deliberate, user-observable effect on two *existing*
pages, and this analyst independently confirmed that effect live against the running build (frontend
`http://localhost:3255`, backend `http://localhost:8255`) rather than only reading the source. Because a
flat "no user-visible changes" stub would be factually wrong here — and would leave the next lane
(browser-qa-agent's TC-3/TC-5/TC-6) without the concrete verification detail it needs — this report
documents the real, if narrow, impact instead of stubbing it out. No new page, component, button, or nav
entry exists; what changed is the **timing and completeness** of two pages that were already there.

---

## What Users Can Now Do

- Open `/research/factor-lab` (the "Factor Lab" tile on the `/research` hub) immediately after **any**
  data-loading job finishes and see the full all-factors comparison table in about a second, instead of
  sometimes waiting several minutes. Before this iteration, the first person to open that page after new
  data loaded triggered a live computation measured at 578–875 seconds; now that computation runs inside
  the data-loading job itself, so the page is already reading from a stored result by the time anyone
  visits it. **Confirmed live on this build just now:** `GET /api/research/factor-lab?all=true` answered
  in 0.008–0.043s (two consecutive calls), and the served table has 11 real factor rows (e.g. "Leadership
  score"), not placeholder/degraded data.
- On the Data Manager page (`/data`), get a more complete answer to "what did this job actually refresh?"
  — the existing "Refreshed: …" summary line can now include one more term, "factor lab all", whenever a
  job's finalize step successfully warmed the Factor Lab. **Confirmed live on this build:** the most
  recent completed run (a backfill of 2011-03-16) already lists `factor_lab_all` in its
  `aggregates_refreshed`, alongside `coverage`, `research_hot_keys`, and the other pre-existing terms; the
  prior run from before this iteration's code shipped does not have it.

## What Changed in the Visible UI

- `/research/factor-lab`: the amber "Still computing — Xs elapsed" warning card (which the page already
  shows whenever a fetch stays pending past a 3-second grace window) should now be rare-to-never seen on
  this view right after an ingest, because the data is typically already cached. It is not removed — a
  genuinely cold cache (e.g. right after a database reset with no ingest yet) still shows it, unchanged.
- `/data`: the existing "Refreshed: …" line (rendered in the "Job progress" card while/just after a job
  runs, in that card's persisted-history fallback when no job has started this browser session, and
  repeated on the matching Run History table row) can now contain one additional term, "factor lab all".
  Nothing about the line's location, styling, or the rest of its wording changed — only its possible
  content grew by one item.
- No page, route, button, form field, table column, chart, or navigation link was added, removed,
  renamed, or restyled anywhere in the product this iteration.

## What Old Behavior Changed

- **Fetch/backfill/rebuild jobs now take noticeably longer end-to-end.** The developer's own real,
  in-app measurement: a job that previously finished in about 12 minutes took about 18 minutes with this
  change, because the new warm step (measured at ~584s / ~9.7 minutes on its own) now runs unconditionally
  as part of every job's finalize step — even a job that creates zero new snapshot dates. It remains
  within the product's committed 20-minute ceiling for that job type, but an operator watching a job's
  live progress card will see it stay in "running" for materially longer than before this iteration.
  This is an explicitly disclosed, accepted trade-off (goal.md: "Budget tension, stated plainly"), not a
  bug.
- On `/research/factor-lab`, the SAME all-factors view that used to occasionally show a multi-minute
  "Still computing" wait (paid by the first visitor after any data change) now reads from a warmed cache
  instead — the numbers themselves are byte-identical (this iteration recomputes nothing, only moves
  *when* the computation happens), so nothing a user was relying on for correctness has changed, only the
  wait.

## Not Visible Yet

- **A newly-disclosed operational finding, with no UI indicator at all.** During the new warm step's own
  multi-minute window, the backend's health endpoint (`/api/health`) went briefly unresponsive at the
  connection level 9 times out of 653 checks over an 18-minute live run — even with **no** competing user
  request in flight. Nothing in the product's UI surfaces this to an operator (there is no "backend is
  momentarily overloaded" banner tied to this specific window); it is disclosed only in
  `reports/perf-budgets.md` Addendum 11 and the dev handoff's Known Issues, and it is explicitly not fixed
  this iteration.
- The Factor Lab payload has carried two "this couldn't be computed" degrade signals
  (`factors_status`, `by_horizon[].status`) since iter-50; the frontend still renders a degraded cell
  identically to an ordinary low-sample "NA" cell, with no distinct "temporarily unavailable" wording.
  This is a pre-existing, carried gap (documented in the phase spec's NOTES as a "Documentation catch-up,"
  registered in the blueprint this iteration) — not something this iteration changed, worsened, or fixed.
