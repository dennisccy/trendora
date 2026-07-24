# goal-ops-hardening-iter-17 Frontend Handoff

**Phase:** goal-ops-hardening-iter-17
**Date:** 2026-07-24
**Agent:** developer
**Status:** complete

## What Was Built

- `RefreshingEvidenceBanner` (`/backtest`) now takes a new `evidenceAsof` prop and displays it: "The
  forward-tested evidence below is the last complete version — evidence as of `<date>`, generated
  `<timestamp>`". This makes J-08 step 2's promise literal — the banner now discloses WHICH as-of's
  evidence is being shown, not only when it was generated. `evidenceAsof` is formatted with the existing
  `formatIsoDate` helper (date-only), separate from `formatIsoDateTime` (used for the generation
  timestamp, unchanged).
- `evidence_asof: string | null` added to the `BacktestResponse` type (`lib/api.ts`) — the new field
  `GET /api/backtest` now serves alongside `evidence_status`/`evidence_generated_at`.
- The `not_yet_computed` `EmptyState` copy on `/backtest` was reworded (audit F2/F3 residual):
  - Old: "Backtest evidence not yet computed — run an ingest to populate the forward-tested evidence for
    this date. No numbers are fabricated in the meantime." (repeated the title verbatim, and told the
    user to "run an ingest" — a word that appears nowhere else in the UI, and a command that presumes the
    user hasn't already started one).
  - New: "No forward-tested evidence exists yet for this date. Backfilling or fetching data that covers
    it will compute this evidence — no numbers are fabricated in the meantime." — no longer repeats the
    title, uses the SAME vocabulary `/data`'s own labels use ("Backfill snapshots" / "Fetch EOD prices"),
    and describes what causes the state to resolve rather than commanding an action.
  - This state should now be rare in practice: the backend fix in the same iteration (cross-`asof_key`
    fallback, see the dev handoff) routes the single most common ingest shape — the latest trading day
    advancing while its forward-aggregate warm is still running — to `refreshing` instead, so this empty
    state is now reserved for the genuine fresh-install shape it was always meant to describe.

## Files Changed

- `apps/frontend/app/backtest/page.tsx` -- `RefreshingEvidenceBanner` gains the `evidenceAsof` prop
  (displayed alongside the existing generation timestamp); `not_yet_computed` `EmptyState` copy reworded
  (F2/F3); banner's own code comment updated to record the new invariant.
- `apps/frontend/lib/api.ts` -- `BacktestResponse.evidence_asof: string | null` added, with a doc comment
  matching the Data Contract (equal to `asof_date` when `ready`, an older date when `refreshing` crosses
  an as-of boundary, `null` when `not_yet_computed`).

**Auditor addendum (2026-07-24, finding F1 — one further change to `page.tsx` made after this handoff was
written):** the `EvidenceAggregateSection` call site now passes `asofDate={backtest.evidence_asof ??
backtest.asof_date}` instead of `backtest.asof_date`. That section's own copy states a factual window
("expanding window ≤ `<date>`", "every snapshot dated on or before `<date>`", "Snapshots contributing
(≤ `<date>`): n"), which becomes FALSE in exactly the state this iteration introduces — a `refreshing`
response whose fallback crossed an as-of boundary serves an aggregate whose window ends at the older
`evidence_asof`, so labeling it with the page's newer `asof_date` contradicted the banner directly above
it. Identical value in every other state (`ready` and same-key `refreshing` both have
`evidence_asof == asof_date`), so no other rendering changes. Verified: `tsc --noEmit` 0 errors; live
cross-boundary render (client-side response rewrite) shows banner and section both reading `2026-07-21`;
live `ready` render unchanged at `2026-07-22` with no banner and no console errors. See
`docs/handoffs/goal-ops-hardening-iter-17-audit.md` §2 (F1) and §4.

## Tests Run

This project has no frontend unit-test runner (no `test` script in `package.json`; the established
convention per prior iterations is a type-check only). Command:

```
cd apps/frontend && npx tsc --noEmit -p tsconfig.json
```

Result: **0 errors.**

No new dependency was added; no other file references `evidence_status`/`evidence_generated_at`/
`evidence_asof` outside `lib/api.ts` and `app/backtest/page.tsx` (confirmed by grep across
`apps/frontend`), so no other component needed a change.

## Known Issues

1. **Live browser evidence status as of this developer session's original pass: NOT captured.** The
   backend and frontend were not running (`curl :8255/api/health` and `:3255/` both refused at
   investigation time — no service was started or stopped to check this; agents cannot start/stop
   services this session). TC-8 (the as-of-advancing `refreshing` case, via a small backfill through the
   existing `/data` job form) and TC-9 (the `not_yet_computed` case on a disposable DB copy, operator-only
   regardless) both need a running instance.
   **UPDATE (2026-07-24, operator pass):** TC-9's `not_yet_computed` `EmptyState` WAS captured live —
   `http://127.0.0.1:13255/backtest` rendered HTTP 200 in an operator-reported 1.314 s against a throwaway
   backend whose backing DB was independently re-confirmed to hold zero forward-aggregate rows (see the dev
   handoff's "Operator Results (2026-07-24)" and `reports/perf-budgets.md` for the full write-up, including
   a process-identity finding about the throwaway backend's current launch state). TC-8's `refreshing`
   banner copy was NOT captured live — the operator found the live DB has no future trading day to backfill
   (`max(daily_prices.date)` = `max(scanner_runs.asof_date)` = the latest snapshotted date, re-verified), so
   the as-of-advancing shape is not reachable on this data; `evidenceAsof`'s display remains verified only
   by its type/plumbing and the backend's unit tests, not a live screenshot.
2. **The `refreshing` banner's "reload after the next ingest" instruction is unchanged** — this iteration
   did not build auto-refresh (audit B2, an explicit out-of-scope trade-off carried from iter-16); a page
   reload is still the only way to pick up a newly-completed version. Unaffected by this iteration's
   changes; noted for completeness since the banner's copy was touched.
