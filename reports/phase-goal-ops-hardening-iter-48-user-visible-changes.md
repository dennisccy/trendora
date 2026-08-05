# Phase goal-ops-hardening-iter-48 — User-Visible Changes

**Phase:** goal-ops-hardening-iter-48
**Date:** 2026-08-04
**Written by:** ui-impact-analyst

---

## Context

`plan.md` and the phase spec both set `Frontend Present: no`, and the dev handoff confirms zero files
under `apps/frontend/` were touched (`git diff --stat` shows only `data_manager.py`, `research.py`,
`samples.py` and their test files, plus `reports/perf-budgets.md`, the J-05 journey script, and
`state/assumptions.md`). Despite that, the phase spec's own "New user-facing capability" and "Product
surface delta" sections (not "None") describe a real, observable change to two already-existing pages —
so this is scored as a genuine (if narrow) user-visible change, not a backend-only phase: the backend now
behaves differently over time on a request path the frontend already renders unchanged. No component, page,
label, or field was added or removed anywhere.

---

## What Users Can Now Do

- Users can start a **historical-day backfill** on `/data` (a date earlier than every date already
  scanned — e.g. `2012-06-15`, matching J-05's own golden target) and have its "Job progress" panel's
  status badge (`data-testid="job-status"`) actually reach a terminal state (`ok` / `no new snapshots` /
  `partial` / `failed at backfill` / `failed`) for the specific finalize step this iteration fixed, instead
  of spinning on `running` for well over an hour. Live-measured twice: 9.18s and 24.10s for that step,
  regardless of which historical date was targeted.
- Once such a backfill's snapshot-write and membership-timeline refresh finish, users can open
  `/scanner-runs`, find the new date as a clickable row in the "As of" column, and click through to
  `/scanner-runs/<runId>` to see the stored leaderboard rendered ("Immutable snapshot — as of 2012-06-15")
  — previously a historical-gap date's run effectively never became usable because the underlying job never
  left `running`.
- Users viewing `/research/factor-lab` or `/evidence`'s "Historical drawdown & dry-spell expectations"
  panels for a `total`- or `regime`-scoped cohort now do so with materially lower server-side peak memory
  (12.9%–15.5% VmPeak reduction, measured through the real `/api/evidence` serving path) — the numbers
  shown are byte-identical to before; the practical user benefit is a lower chance of that request failing
  under load, not a new number or a faster page.

---

## What Changed in the Visible UI

- The `/data` page's "Job progress" panel: for a **historical-gap backfill specifically**, the
  `job-status` badge now typically settles out of the spinning "running" state (for the fix's own scope)
  within roughly 10–25 seconds of the snapshot write, rather than staying on "running" indefinitely.
- The `/data` page's "Refreshed: …" line (`data-testid="aggregates-refreshed"`, part of
  `BackfillBreakdown`) now populates promptly for a historical-gap backfill, since the
  membership-timeline-refresh step it names finishes fast instead of hanging.
- `/scanner-runs`: a historical-gap date now reliably appears as a row (with a clickable "As of" date link)
  once its job settles, where before the job effectively never finished for that class of date.
- `/scanner-runs/<runId>`: opening a historical-gap date's run now renders the "Immutable snapshot — as of
  `<date>`" heading and a populated leaderboard table instead of the page being unreachable (the run row
  never existed) or stuck loading.
- No new page, panel, route, button, field, or label was added anywhere — every element above already
  existed before this iteration; only the timing/behavior of what they display for this one scenario
  changed.

---

## What Old Behavior Changed

- **Historical-day backfill finalize step** (`/data`, Backfill snapshots job kind, target date earlier
  than the latest cached membership-timeline date): previously, the coverage/membership-timeline-refresh
  finalize step alone extrapolated to well over an hour for a single such date (an O(dates × pool)
  unbatched resolver sweep over ~2,900 historical dates), so the job's status badge stayed on the spinning
  "running" state indefinitely and the date never became a usable `/scanner-runs` row. That specific step
  now completes in 9–24 seconds live, regardless of how far back the date is.
- **Caveat — the OVERALL job's terminal status is still not guaranteed within any fixed time on every
  run.** A separate, pre-existing finalize-tail step (`drawdown_expectations_warm`) that this iteration
  deliberately did NOT touch can itself run 11+ minutes and, on one live automated-test run, had not
  finished after 950+ seconds. So while the defect this iteration targeted is fixed and proven twice on
  real data, a historical-gap backfill's job card can still show "running" for longer than 20 minutes on an
  unlucky run — same as before, for that unrelated cost. Throughout every measurement, `GET /api/health`
  answered every 1-second poll with HTTP 200 (507/507 and 69/69 across the two live drills) — the app
  itself never freezes or becomes unresponsive while a job is finalizing, even when that job's own "done"
  marker takes a while.
- **`/research/factor-lab` and `/evidence`'s `total`/`regime` cohort reads**: no visible change in the
  numbers shown to users — this is a server-side memory-footprint reduction only (rows are now built in a
  single pass / filtered inline during the existing chunked read, instead of materializing the full
  population twice or filtering only after building it in full).

---

## Not Visible Yet

- The `total`/`regime` cohort memory bound has **no dedicated clickable UI element of its own**. It fires
  automatically whenever `/research/factor-lab` or `/evidence` renders a drawdown-expectations panel for a
  non-decile (whole-population or regime-conditioned) claim — there is currently no "N=" drill-down link in
  the UI for a factor `total`/`regime` slice (only the `decile` slice has one, in the Factor Lab); the
  `/research/samples` page supports `total`/`regime` for a factor cohort via a manually constructed URL
  (it is "deep-linkable" by design), but nothing in the current UI links to it for that slice/kind
  combination.
- The still-unbounded `drawdown_expectations_warm` finalize-tail step (out of this iteration's scope, a
  carried, disclosed gap from a prior iteration) has **no "still finishing" indicator** on the job card —
  it just keeps showing the spinning "running" badge for that unrelated cost, exactly as before this
  iteration. The phase spec's frontend section allowed adding such an indicator IF the investigation forced
  it; the developer's investigation did not force it (the fix target itself is fast), so it was not added.
- The new opt-in integration test
  (`test_start_backend_historical_gap_insert_reaches_terminal_status_within_bound`, only runs when
  `TRENDORA_RUN_HEAVY_INGEST_TEST=1` is set) is left **failing on purpose** in the codebase, as an honest,
  visible reminder that the literal 20-minute end-to-end bound is not yet guaranteed — this is a
  developer/CI-facing signal, not something a product user would ever see.
