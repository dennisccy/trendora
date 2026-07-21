# Phase goal-ops-hardening-iter-7 — User-Visible Changes

**Phase:** goal-ops-hardening-iter-7
**Date:** 2026-07-21
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

- None. This iteration is a pure ingest-time warm fix closing J-06's last gap ("Pages load only what they
  need") — no new endpoint, no new page, no new button, form, or navigation entry was added anywhere in the
  product. Every value the Evidence page and every other J-06 page show was already visible before this
  iteration; only WHEN one background computation runs changed (moved from "the moment someone first opens
  `/evidence` after an ingest" to "the moment the data-update job itself finishes").

---

## What Changed in the Visible UI

- **Evidence Ledger (`/evidence`) loads its "expected drawdown" panels fast on the very first view after
  any data update, not only once someone else has already opened the page.** The page's layout, claim
  rows, and `expectations` sub-panels are byte-identical to before — same values, same fields, same
  skeleton/loading states — only the wait before they populate is now consistently short.
- **Data Manager (`/data`) — the "Refreshed:" summary line can show one new phrase, "drawdown
  expectations."** The Job progress panel (both the live in-session view and the persisted-run fallback
  view) and the Run History table already render a plain-language, comma-separated list of which internal
  data categories a backfill/rebuild job refreshed (e.g. "latest snapshot, coverage, membership timeline,
  market phase, forward aggregates, research hot keys"). That list is generated generically from a
  server-reported array (`aggregates_refreshed`) with no per-category frontend logic, so the moment the
  backend starts reporting a new category, the existing UI text automatically picks it up with no frontend
  code change. After this iteration, a backfill/rebuild job whose evidence ledger has at least one claim
  that can actually be scored will show "drawdown expectations" as an additional item in that list —
  previously this phrase never appeared, even though the same computation eventually happened later
  (lazily, on the first `/evidence` view after the job).

---

## What Old Behavior Changed

- **`/evidence` first view after an ingest job:** previously the FIRST person to open the Evidence page
  after any backfill/fetch/rebuild paid a one-time cold-compute wait for each claim's "expected drawdown"
  panel — measured at roughly 73 seconds on the project's grown live dataset (a number itself only
  established last iteration after an earlier, larger figure was found to be a measurement artifact and
  retracted). Now that computation runs automatically as part of the data-update job, so the first
  `/evidence` view after any ingest is fast — measured in the tens of milliseconds in this iteration's live
  verification, matching every subsequent (already-warm) view. Nobody has to "pay the warm-up" by being the
  first visitor anymore.
- **Data Manager job summary / run history "Refreshed:" line:** previously this line never included
  anything related to the Evidence page's drawdown figures, even on runs where that computation eventually
  happened. It can now include "drawdown expectations" for a qualifying backfill/rebuild run — an
  additive, informational change to an existing list of internal category names; no existing entry in that
  list was removed, renamed, or reordered.

---

## Not Visible Yet

- None. No new backend capability was introduced this iteration that lacks UI wiring — the new
  `aggregates_refreshed` list value automatically surfaces through the Data Manager's existing generic
  renderer, and the Evidence page's own render contract is completely unchanged.
