# Phase goal-market-compass-iter-37 — UI Surface Map

**Status:** N/A — Backend-only phase (Frontend Present: no)

No UI surfaces affected.

## Basis for this classification

Both changed files this iteration are `backend-internal` per `.claude/skills/diff-to-ui-impact.md`:

| File | Classification | Reason |
|------|-----------------|--------|
| `apps/backend/tests/test_manifest_invariants.py` | backend-internal (test code) | Fixture correction + new unit test; no production code path, no API surface. |
| `apps/backend/app/engine/compass.py` (`_assert_disposition_predicate` only) | backend-internal | Internal correctness guard rewritten from bare `assert` to explicit `raise`; same condition/message/exception type; not a new or changed API endpoint, computed value, or served field. `compass.py`'s existing `/api/compass` route and payload shape are untouched — dev handoff confirms a live `GET /api/compass?asof=2026-08-12` round-trip returned the same manifest shape with no errors, and byte-identity (md5) of all stored manifest rows/exports was confirmed unchanged before vs. after. |

No `.tsx`, route, component, or `apps/frontend/lib/api.ts` fetcher was touched this iteration
(confirmed absent from "Files Changed" in the dev handoff). J-13's "Leadership rotation"
UI surface (`/` — Leadership rotation section) was built in a prior iteration and is
explicitly out of scope this round ("binding Do not redo"); this iteration's QA/browser lanes
only re-verify that already-shipped surface with a fresh screenshot — they do not change it.
That re-verification evidence, if produced, belongs in the QA/audit reports for this iteration,
not in a UI surface change map, since no surface changed.
