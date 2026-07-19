# Phase goal-ops-hardening-iter-1 — User-Visible Changes

**Phase:** goal-ops-hardening-iter-1
**Date:** 2026-07-19
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

- Submit a backfill for **any explicit date range** on the `/data` page and have it actually process every trading day in that range — previously, a range that fell before the system's "keep it light on old history" snapshot cadence (e.g. any May-2026-only range, since the cadence's dense-daily coverage only starts 2026-06-01) would silently target **zero** dates and report success with nothing done, with no error and no explanation.
- Submit a backfill spanning **more than 370 calendar days** (e.g. a 412-day range) and have it accepted and start running — previously this exact submission was rejected outright at the form/API level with a "date range too large" error.
- Watch a large backfill's progress **chunk by chunk** using the same "chunk N/M" badge previously shown only for large fetch/download jobs — a backfill spanning many date-window chunks now advances visibly instead of appearing to run silently until it finishes.
- See an honest, visually distinct outcome when a backfill does **zero new work** — either because the exact range was already fully backfilled, or because the range contains no trading days at all (e.g. a weekend-only range) — rendered as a neutral "no new snapshots" badge with an explanatory note, instead of looking exactly like a normal successful run.
- Reload the `/data` page, or open it fresh in a new tab/session, and **immediately see the outcome of the most recent backfill/fetch run** even though no job was started in that particular browser session — previously the Job progress panel always showed the literal text "No job has been started this session," even when the Run history table right below it was full of completed runs.
- See a **detailed breakdown** for every completed backfill/rebuild run — how many calendar days were in the requested range, how many were non-trading days, how many were already snapshotted before this run, and how many failed — shown as inline text on both the Job progress panel and the Run history table row for that run.
- *(Consequential — no code change on this page, but new data now flows into it)* After completing a backfill for a previously-inaccessible range (e.g. 2026-05-02 → 2026-05-29), visiting the existing `/scanner-runs` page now shows entries for those dates (e.g. 2026-05-04, 2026-05-15, 2026-05-29) that would never have appeared before, since the backfill that should have created them used to silently do nothing.

---

## What Changed in the Visible UI

- The `/data` page's **Job progress panel**: when no job has been started this browser session but persisted run history exists, it now renders a "last run" summary card (status badge, run message, snapshot/trading-day counts, and the breakdown line) instead of the empty "No job has been started this session" text. That original text is still shown, unchanged, for the true empty-history case (no runs have ever completed).
- The `/data` page's **Job progress panel** (live job view) and **Run history table**: a `backfill`/`both`/`rebuild` run that finished `ok` but created **zero new snapshots** now shows a "no new snapshots" badge in the existing neutral/grey style (the same treatment already used for `interrupted` runs) instead of the plain green "ok" success badge used for a productive run.
- The `/data` page's **Job progress panel** gained a new explanatory note box, shown only for a zero-work outcome: "Zero-work outcome — every requested trading day already had a snapshot (or the range contains no trading days). No new computation was needed; this is not a failure."
- Both the **Job progress panel** and the **Run history table** now show a new inline line of text next to/under the existing snapshot count for any backfill/both/rebuild run: e.g. "28 calendar days · 0 already snapshotted · 9 non-trading" (and "· N errors" when errors occurred). This line does not render at all for a fetch/expand-only run — no fabricated zeros are shown where the concept doesn't apply.
- The existing "chunk N/M" progress badge (previously visible only on large fetch/download jobs) now also appears on backfill jobs whose date range spans multiple date-window chunks.
- The job submission form itself (kind selector, start/end date inputs, Start button) is visually and structurally **unchanged** — the difference is only in what it now accepts and how outcomes are reported afterward.

---

## What Old Behavior Changed

- **Backfill's cadence rule:** previously, an explicit backfill request for a date range covered by the system's background "keep it light on old history" cadence could silently target zero dates even though real trading days existed in that range, and no error or warning was ever shown — it looked like a normal, if uneventful, completed job. Now, an explicit backfill (or combined fetch-and-backfill) request always targets every trading day in the requested range, regardless of that background cadence. (The rare, manually-triggered "regenerate everything from scratch" rebuild action is unchanged — it still applies the old cadence-filtered selection, deliberately, since no day-to-day journey exercises it.)
- **What "total days" means in a backfill result:** previously, the reported total-days figure only counted dates that still needed work after filtering out already-covered dates. Now it always means "every trading day in the range you asked for," whether or not it needed new work. A re-run of the same range will now report a different total-days figure than it used to — this is intentional, and the new breakdown line (already-snapshotted / non-trading / error counts) exists specifically so this doesn't read as a silent, unexplained change.
- **Backfill/fetch request size limit:** previously, any request spanning more than 370 calendar days was rejected immediately with an error when submitted. That rejection no longer exists anywhere in the product — a request of any length is accepted, and progress is shown in date-window chunks instead.
- **`rebuild`-kind jobs:** which dates get targeted is unchanged (still governed by the same background cadence as before), but a rebuild's execution now advances through the same chunk-by-chunk progress mechanism backfill uses, so its chunk-progress badge will reflect date-window chunks in a way it did not previously.

---

## Not Visible Yet

- The new breakdown fields are technically served for `rebuild`-kind runs too (same API, same UI rendering), but the underlying "these counts always add up" guarantee is not exact for `rebuild`, since its unchanged cadence filtering can leave some in-range trading days uncounted in any of the three outcome buckets. This is a known, documented limitation of `rebuild` specifically (a rare, manually-triggered action) — it is not a gap in what the UI shows, and no current user journey exercises `rebuild` closely enough to expose it.
- Backend log persistence and memory-limit enforcement for the backend startup process (planned for a separate, already-scheduled effort) — not touched this iteration, no UI change.
- Automatic precomputation of heavier derived views (coverage numbers, market-phase status, etc.) at ingest time, and page-load-budget/lazy-loading improvements — both explicitly deferred to future iterations; no UI change this iteration. (This iteration's cadence fix does make a single-day backfill newly usable as a precondition for that future work, but does not itself build any of it.)
