# Phase goal-market-compass-iter-8 — What to Click (Operator Verification Guide)

**Phase:** goal-market-compass-iter-8
**Time required:** N/A
**Written by:** ui-impact-analyst (combined mode)

**Status:** No UI verification required. Backend-only phase.

---

## Why there are no steps

This iteration (J-10's redesigned per-symbol path-agreement + stable-multiplicative-bridge gate, plus
running the gated recovery for real) touched only four backend files —
`apps/backend/app/engine/j10_recovery.py`, `apps/backend/app/data_providers/yahoo_provider.py`,
`apps/backend/tests/test_j10_recovery.py`, and `apps/backend/tests/test_provider_clients.py`. No
frontend file changed, and the phase spec itself waives the walkthrough: J-10 "has no UI surface...
data-layer repair with no UI surface change of its own." There is no button, form, or page that is
different from before this iteration for an operator to click through.

**What actually happened, for context (not a click-through check):** the redesigned two-part gate
(path agreement + bridge dispersion, evaluated per symbol) ran for real against the live database on
a precommitted 20-symbol sample. All 20/20 sampled symbols passed, each with a measured bridge factor
of exactly 1.0 (0.0% dispersion, 0.0% path-agreement delta) — Stooq's stored close and Yahoo's raw
`get_daily` close were byte-identical for every sampled (symbol, date) pair over the comparison
window. Their two recovery-date bars (2026-08-11, 2026-08-12) were fetched and inserted, adding 40
rows to `daily_prices`. 567 of the 587 proven-missing symbols were never attempted (a deliberate,
precommitted scope choice, not a failure) — coverage is honestly 20/587 (3.4%). As an incidental
consequence, `GET /api/compass?as_of=2026-08-12` now returns HTTP 200 instead of 400, but this
reflects a partial, temporary recovery-era state (the 2026-08-11/12 `ScannerRun`s are documented as
pending clean regeneration under a separate, not-yet-run J-11), not a completed repair. Per
`docs/goal.md`'s lane gate, no browser session was opened against the current dataset for this
iteration, and none should be recommended here — that verification is unconditionally deferred to a
later iteration, gated behind J-11 Stage G.

## If you want to confirm this iteration's actual result

Not a UI check — read `docs/handoffs/goal-market-compass-iter-8-dev.md`'s "READ THIS FIRST" section,
its per-symbol verdict table, and its Step 5 verification table, which record the redesigned gate's
per-symbol path-agreement/dispersion metrics, the 20/20 "agree" verdicts, the 40 inserted rows, and
the honest partial-coverage state directly against the database (read-only SQL queries and direct
`GET /api/compass` calls against a transiently started backend — not a browser session). The full
per-pair evidence (symbol, date, stored value, fallback value, ratio) is in
`runs/goal-market-compass-iter-8/j10-convention-evidence.json`.

## Common Issues

Not applicable — no UI surface exists to click through this iteration. A future iteration's
`ui-impact-analyst`/`ui-test-designer` dispatch should produce a real click-through guide for
`GET /api/compass?as_of=2026-08-11` / `?as_of=2026-08-12` (or their frontend consumers) only once (a)
coverage for those two dates is judged sufficient by the owner or a further precommitted recovery
batch, (b) J-11's incident-bounded clean regeneration of derived state has run, and (c) J-11 Stage G's
repaired-state J-01/J-02/J-03 replay has actually passed — not merely because the raw endpoint now
returns 200.
