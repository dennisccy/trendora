# Goal iter-49 — Implementation Summary

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-49
**Date:** 2026-06-26
**Written by:** developer

---

## Features Implemented

- **"Proximity to 52w high" column (J-106)**: The Stocks leaderboard now shows, for each stock, how far
  below its 52-week high it is trading (a percentage; `0.00%` means it is AT a fresh high). The column sits
  right after the Risk column, can be sorted by clicking its header, and has an info tooltip explaining the
  term. Stocks with too little price history show "NA" and always sort to the bottom.
- **Honest readiness badge everywhere (J-108)**: The small status badge at the top of every page now tells
  the truth about the backend — "Ready", "Initializing…" (with warm-up progress), or "Backend
  unavailable" — even when the app is opened using the machine's network (LAN) address rather than
  "localhost". Before this change it was stuck showing "Backend unavailable" on the LAN address.

---

## Changed Behavior

- **Stock Detail — Leadership breakdown**: The "Proximity to 52w high" line in a stock's Leadership score
  breakdown now shows the actual distance below the 52-week high (e.g. `-0.53%`) — the same number the new
  leaderboard column shows for that stock. Previously it showed an internal ranking figure ("pctl …"). All
  other breakdown lines are unchanged.
- **Readiness badge / all data loading on the LAN address**: Opening the app at the LAN address printed by
  the start script now loads data and shows a correct badge. Opening at "localhost" works exactly as
  before.

---

## Backend-Only Items

- None. Both changes are user-visible. The only backend change (a development-mode network/CORS allowance)
  exists solely to make the existing readiness badge work on the LAN address; it adds no new endpoint or
  served value.

---

## Incomplete Items

- None deferred from this iteration's scope. (J-107, the Factor Lab restructure, was explicitly out of
  scope for iter-49 and is planned for iter-50.)

---

## Config and Environment Changes

- `CORS_ORIGIN_REGEX` (backend, optional) — a development-only pattern that lets the backend accept
  requests from the machine's private network (LAN) address. Default: unset (production is unaffected and
  keeps its explicit allow-list). The start script `scripts/dev.sh` now sets this automatically for local
  development, and also adds the LAN address to the existing `CORS_ORIGINS` list.
- `NEXT_PUBLIC_API_PORT` (frontend) — already provided by `scripts/dev.sh`; now actually used by the
  frontend to find the backend when the page is opened on a non-localhost host. No new variable to set.
- No database migration.

---

## Known Limitations

- The full backend test suite is slow on this machine (a one-time data warm-up runs before the tests) and
  was launched to run in the background per the iteration plan; it is not a release-gating check for this
  iteration. The targeted health/CORS tests pass, and the full-suite result is recorded at the end of
  `reports/qa/goal-...-iter-49-test.log`.
- The frontend's tiny unit-test files (`lib/*.test.ts`) cannot be executed on this particular developer
  machine because its Node build lacks built-in TypeScript support; they run in the project's CI/QA
  environment. The new resolver's logic was verified locally with an equivalent plain-JavaScript copy (all
  checks passed) and the whole frontend type-checks cleanly.
- No stock in the current data set is missing 52-week history, so the "NA" appearance of the new column was
  verified by logic/tests rather than seen live this run.
- The readiness fix's network allowance is intentionally limited to local development; production behavior
  is unchanged.
