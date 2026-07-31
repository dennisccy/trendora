# Phase goal-ops-hardening-iter-40 — What to Click

**Status:** N/A — Backend-only phase. No UI verification steps.

This iteration made no UI, route, or API-contract changes (see
`reports/phase-goal-ops-hardening-iter-40-user-visible-changes.md` and
`reports/phase-goal-ops-hardening-iter-40-ui-surface-map.md`). It closed J-07's last
standing blocker purely through backend work: streaming `_missing_data_diagnostic`'s
second query via `.yield_per(...)` instead of materializing ~3.3M rows whole-result in
memory (proven byte-identical output via a fixture test), correcting a stale in-code
comment, tightening the `/data` Run History checkpoint-write cadence from 10.0s to 1.0s
so a crashed job's persisted progress stays honest (proven via a unit test plus a live
`kill -9` drill: 1-date gap vs. the prior iteration's order-of-magnitude gap), re-running
the tightened-cap wedge-recurrence drill once post-fix (no recurrence — `GET /api/health`
answered 200 on all 28 polls, max gap 1.826s), correcting a report-doc retraction in
place, and teaching the QA-tooling merge script a `BLOCKED` verdict class. There is
nothing for an operator to click to verify this iteration.

If an operator wants to spot-check that the `/data` page's Run History panel and
Coverage panel still look right, that reads the same EXISTING, unchanged `/data` page —
neither panel's rendering, fields, or available actions changed this iteration; the
existing functional/browser test coverage for J-04, J-05, and J-07 from prior iterations
remains the correct reference, not a new UI click-path.
