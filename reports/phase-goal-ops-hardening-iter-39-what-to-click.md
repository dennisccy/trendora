# Phase goal-ops-hardening-iter-39 — What to Click

**Status:** N/A — Backend-only phase. No UI verification steps.

This iteration made no UI, route, or API-contract changes (see
`reports/phase-goal-ops-hardening-iter-39-user-visible-changes.md` and
`reports/phase-goal-ops-hardening-iter-39-ui-surface-map.md`). It closed J-07's remaining step
purely through backend work: a throwaway-DB induced-pressure drill that raises a `MemoryError`
inside the aggregate-warm stage (caught by the existing per-item isolation handler, while
`GET /api/health` and a cached `GET /api/backtest` read both keep answering HTTP 200), a
deterministic replay-lane repair (new `BLOCKED` verdict class, backend-health pre-probe, a
reconciliation-footer fix), an env-toggle truthy guard for `TRENDORA_FORCE_LEGACY_BAR_CACHE`, a
root-logger configuration fix for `apps/backend`, an in-situ `read_pool()` wall-clock
re-measurement, and a genuine live `kill -9` + restart re-verification of J-04 and J-05 step 3.
There is nothing for an operator to click to verify this iteration.

If an operator wants to spot-check that J-04 (interrupted-run status truth on restart) and J-05
(cold-boot coverage-from-storage) still look right, that reads the same EXISTING, unchanged
`/data` page — specifically the Run History panel and the Coverage payload panel — and the global
readiness badge. None of those panels' rendering, fields, or available actions changed this
iteration; the existing functional/browser test coverage for J-04, J-05, and J-07 from prior
iterations remains the correct reference, not a new UI click-path.
