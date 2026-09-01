# Phase goal-market-compass-iter-32 — User-Visible Changes

**Status:** N/A — Backend-only phase (Frontend Present: no)

No user-visible changes. All changes are internal backend/ops implementation:

- J-09 clean standing-warm VmPeak re-measurement, replacing the two prior evidence-gapped figures
  (iter-4's 3,439,100 kB and iter-25's unsupported 3,064,772 kB) with a durably-evidenced
  3,038,684 kB figure — raw sampler CSV saved to
  `runs/goal-market-compass-iter-32/j09-vmpeak-samples.csv` (80 samples, UTC timestamps). This is
  an internal ops measurement, not a UI-displayed value.
- A concurrent-load burst check (`server.limit_concurrency`=64) and an "original methodology"
  replica burst, both driven by new one-off scripts
  (`runs/goal-market-compass-iter-32/pool_pressure_burst.py`,
  `runs/goal-market-compass-iter-32/vmpeak_sampler.py`) — server-side load testing tools, not part
  of the Trendora product.
- A byte-identity spot-check of `GET /api/compass` and `GET /api/dashboard` at the three
  pre-authorized as-of values, confirming zero displayed value moved (raw before/after captures
  under `runs/goal-market-compass-iter-32/byte-identity/`). This is the mechanism that *proves* no
  UI-visible behavior changed, not a change itself.
- `reports/perf-budgets.md` gained one new dated addendum (Addendum 43) — an internal ops report,
  not served to or rendered by the frontend. Addenda 40/41/42 are untouched.
- `config.yaml`'s `database.pragmas.cache_size`/`pool_size`/`max_overflow` were inspected and
  confirmed unchanged (`-65536`/`24`/`44`) — no config edit landed this iteration.
- The deterministic replay lane re-verified all ten Required-still-passing journeys
  (J-01–J-08, J-10, J-11) still PASS via `demo_runner.py --mode verify`, including `J-02`/`J-03`
  actually executing for the first time since their iter-31 rewrite. This is a regression
  *verification* of already-shipped UI, not a change to it — results recorded in
  `reports/phase-goal-market-compass-iter-32-regression-replay-results.md` with screenshot
  evidence under `reports/qa/goal-market-compass-iter-32-evidence/`.

Verified independently (not solely from the dev handoff): `git status --porcelain -- apps/frontend
apps/backend/app` returns empty, and `git diff -- config.yaml` returns empty. No route, page,
component, form, table, chart, badge, or navigation element in the Trendora product changed this
iteration. The dev handoff (`docs/handoffs/goal-market-compass-iter-32-dev.md`) independently
states the same ("No files under `apps/frontend/` or `apps/backend/app/` were changed"), and no
`goal-market-compass-iter-32-frontend.md` handoff exists (frontend work not applicable this
iteration — the phase spec's own "Frontend" section reads "None").
