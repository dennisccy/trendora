# Phase goal-ops-hardening-iter-46 — UI Surface Map

**Status:** N/A — Backend-only phase (Frontend Present: no)

No UI surfaces affected.

## Note on the Evidence page and `/data` panels

`_combination_observations` and `compute_drawdown_expectations` are computation functions that feed
`GET /api/evidence` and the Combination Lab (`/research/*`), which the pre-existing Evidence page and
`/data` panels already render. This iteration's refactor is explicitly required to keep both functions'
returned output **byte-identical** to the pre-fix reference oracle (TC-3) — the served values, labels,
and layout of those existing pages/panels are unchanged. There is therefore no new/changed/removed UI
surface to enter into the map: the served response shape and values behind the existing Evidence page
and `/data` panels are asserted equal to before, not merely "not yet wired to a new capability." Manual
verification of the reliability fix itself (that `GET /api/evidence` no longer risks a MemoryError under
concurrent load) belongs to the browser-qa-agent's TC-4/TC-7/TC-8/TC-9 journey checks against the phase
spec's Definition of Done, not to a UI-surface test-plan entry, since no surface changed.
