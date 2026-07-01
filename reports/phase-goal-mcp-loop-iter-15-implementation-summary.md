# goal-mcp-loop-iter-15 — Implementation Summary

**Phase:** goal-mcp-loop-iter-15
**Date:** 2026-07-01
**Written by:** developer

---

## Features Implemented

- **A 7th proven edge on the Research factor lab + Evidence ledger**: the platform's 3-month
  relative-strength leadership factor (`rs_spy_3m`) now shows a **"Proven"** badge specifically at the
  **60-day hold** on `/research/factor-lab`, and a matching new row appears on the `/evidence` ledger. A user
  can now see — and audit end-to-end — that this factor carries a referee-certified, out-of-sample,
  SPY-control-beating edge at that one horizon. The badge deep-links to the ledger row that proves it.
- **Honest "not yet proven" on the same factor's other horizons**: the 1-, 5-, 10-, and 20-day holds of the
  same `rs_spy_3m` factor keep reading **"Not yet proven"** — proven-ness never leaks from the one certified
  horizon to the others.

The proof itself (the statistical certification) was produced by the pre-build referee gate before any code
was written; this iteration surfaces that already-certified result. It required essentially no new
application code — the display machinery was already general from earlier iterations.

---

## Changed Behavior

- **Evidence ledger count**: the `/evidence` ledger grew from **6 to 7** certified claims (the new
  `rs_spy_3m` 60-day row).
- **Factor lab, `rs_spy_3m` factor view**: its 60-day-horizon cell changed from "Not yet proven" to
  **"Proven"**. All other cells of that factor are unchanged (still "Not yet proven").
- **Everything else is unchanged.** The `/stocks` leaderboard and its inline score badges are untouched —
  this factor is not one of the three scored columns, so it cannot and does not light any per-stock badge.
  The three score signals proven set stays exactly `{leadership_score}`.

---

## Backend-Only Items

- None. Every change in this iteration is visible in the UI (the factor-lab badge and the Evidence row), and
  both are served by the existing `GET /api/evidence` endpoint. No new endpoint, model, or computing module
  was added.

---

## Incomplete Items

- None deferred from this iteration's spec. The single in-scope promotion (`rs_spy_3m` D10 @ h60) was
  certified (PASS) and surfaced.
- Explicitly out of scope (backlog only, not started): the `leadership_score` h60 score-column fallback and
  the speculative horizon-term-structure view.

---

## Config and Environment Changes

- None. No environment variables, config-file values, or database migrations were added or changed.
- Note for running the frontend unit test on this machine: the installed Node (v22.22.1) lacks a built-in
  TypeScript loader, so run the test with `npx --offline tsx lib/evidence.test.ts` (the `tsx` runner is
  already cached locally) rather than the documented plain `node lib/*.test.ts`.

---

## Known Limitations

- **The certified edge (+21.34% out-of-sample) is unusually large** and was flagged for scrutiny in an
  earlier iteration. It is shown as "Proven" ONLY because the referee re-certified it out-of-sample against
  the SPY control with a p-value far below the required bar. This is the deliberate audit focus of this
  iteration; it is honest to surface, but reviewers should scrutinize it rather than rubber-stamp it. Had the
  referee returned anything other than PASS, the iteration would have blocked (and reported), not forced the
  result.
- **Displayed-number correctness was verified at the data/API layer, not yet in the browser.** The
  `rs_spy_3m` 60-day row served by the API byte-matches the certified ledger entry (edge, p-value, SPY
  control, registration date, divisor). The live in-browser screenshot verification (the badge frame and the
  ledger row) is performed by the browser-QA step that runs after development.
- **Each new proven claim permanently tightens the statistical bar** (the Bonferroni divisor moved 6 → 7).
  This is intentional, honest history — but it means future proven claims face a stricter threshold.
