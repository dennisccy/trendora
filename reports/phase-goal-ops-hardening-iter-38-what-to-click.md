# Phase goal-ops-hardening-iter-38 — What to Click

**Status:** N/A — Backend-only phase. No UI verification steps.

This iteration made no UI, route, or API-contract changes (see
`reports/phase-goal-ops-hardening-iter-38-user-visible-changes.md` and
`reports/phase-goal-ops-hardening-iter-38-ui-surface-map.md`). It closed J-07 purely through
backend measurement: a widened throwaway-DB drill proving the shared bar cache is genuinely held
resident across the finalize tail, a two-arm (live-cache vs. forced-fallback) VmPeak comparison, a
live-basis forward-aggregate warm triggered through the real ingest-finalize hook, a concurrent
`GET /api/health` poll, two strengthened/new unit tests, and two documentation hygiene fixes. There
is nothing for an operator to click to verify this iteration.

If an operator wants to spot-check the underlying journey (J-07) is still healthy, that is covered
by the existing functional/browser test plan at
`reports/qa/goal-ops-hardening-iter-38-test-plan.md`, not by a UI click-path — J-07's own surface
(the global readiness badge and `/backtest` page) is unchanged this iteration.
