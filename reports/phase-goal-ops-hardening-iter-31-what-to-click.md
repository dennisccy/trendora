# Phase goal-ops-hardening-iter-31 — What to Click

**Status:** N/A — Backend-only phase. No UI verification steps.

This iteration is a backend availability/concurrency hardening fix (bounding the Factor-Lab
return-value memory footprint and adding a single-flight guard to `factor_lab_all_cached`).
No route, component, label, or layout changed, and the response payload is byte-identical to
the pre-iteration reference for every `(factor, horizon, decile)` tuple — there is nothing new
for an operator to click.

If an operator wants a spot-check that the underlying crash is fixed, that is a functional/
backend verification (does `GET /research/factor-lab?all=true` return HTTP 200 instead of a
`MemoryError` 500) and belongs to the functional test plan at
`reports/qa/goal-ops-hardening-iter-31-test-plan.md`, not a UI click-path guide.
