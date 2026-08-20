# Phase goal-market-compass-iter-7 — What to Click (Operator Verification Guide)

**Phase:** goal-market-compass-iter-7
**Time required:** N/A
**Written by:** ui-impact-analyst (combined mode)

**Status:** No UI verification required. Backend-only phase.

---

## Why there are no steps

This iteration (J-10's Yahoo-vendor recovery retry, gated behind a new fail-closed
adjustment-convention check) touched only three backend files —
`apps/backend/app/engine/j10_recovery.py`, `apps/backend/app/data_providers/yahoo_provider.py`, and
`apps/backend/tests/test_j10_recovery.py`. No frontend file changed, and the phase spec itself waives
the walkthrough: J-10 "has no UI surface... data-layer repair with no UI surface change of its own."
There is no button, form, or page that is different from before this iteration for an operator to click
through.

**What actually happened, for context (not a click-through check):** the new convention-check gate
compared 88 sampled (symbol, date) pairs against Yahoo's adjusted-close series and found one ticker
(CVX) just outside the allowed tolerance (~0.865% observed vs. a 0.75% limit), so it correctly stopped
before writing anything. `daily_prices`, `scanner_runs`, and `data_provider_runs` are unchanged from
before this iteration, and `GET /api/compass?as_of=2026-08-12` still returns HTTP 400 — the same
response as before this iteration ran. That pre-existing 400 is not a new condition to verify; nothing
changed for a user to click through, and the affected journeys (J-01–J-04) are explicitly out of this
iteration's testing scope (deferred to iteration 8, regardless of this iteration's outcome, per the
phase spec's BACKGROUND). Per `docs/goal.md`'s lane gate and this report's own instructions, no browser
session was opened against the current dataset for this iteration, and none should be recommended here.

## If you want to confirm this iteration's actual result

Not a UI check — read `docs/handoffs/goal-market-compass-iter-7-dev.md`'s "READ THIS FIRST" section and
its Step 5 verification table, which record the convention-check's per-symbol deltas, the `mismatch`
verdict, and the zero-writes confirmation directly against the database (read-only SQL queries and two
direct `GET /api/compass` calls against a transiently started backend — not a browser session).

## Common Issues

Not applicable — no UI surface exists to click through this iteration. If a future iteration's recovery
retry succeeds (owner decision pending — see the dev handoff's "Recommendation for owner review"), that
iteration's `ui-impact-analyst`/`ui-test-designer` dispatch should produce a real click-through guide
for `GET /api/compass?as_of=2026-08-11` / `?as_of=2026-08-12` once the data and the J-01–J-04 browser
re-verification are actually in scope.
