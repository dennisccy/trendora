# Phase goal-ops-hardening-iter-47 — UI Surface Map

**Phase:** goal-ops-hardening-iter-47
**Date:** 2026-08-04
**Written by:** ui-impact-analyst

---

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/evidence` | `DrawdownExpectationsPanel` (`apps/frontend/app/evidence/page.tsx:260-343`) | Changed behavior — additive UI state | Path B fix (`GET /api/evidence`'s cache-staleness handling, `forward_testing.py`/`evidence.py`) can now serve a claim's last-good prior generation instead of stalling on a cold recompute; the panel must disclose this honestly instead of looking identical to a fresh generation | On the Data Manager page (`/data`), read the second (later) date shown next to the "Price history" label, then start a backfill for the calendar day immediately after it (see UT-03 in the test plan for exact steps). Reload `/evidence` within ~8 minutes and verify the amber `Badge` reading "Refreshing" (`data-testid="evidence-expectations-refreshing"`) appears next to at least one claim's "Historical drawdown & dry-spell expectations (…-day hold)" heading, the table below it still shows real median/p90/n figures (never blank or a loading spinner), and the descriptive paragraph includes the added sentence "A newer version is computing in the background…" |
| `/evidence` | `CertifiedClaim.expectations_status` / `resolveDrawdownExpectationsPanelState` (`apps/frontend/lib/evidence.ts:75-330`) | Logic/type change (non-visual) | Widens the resolver's discriminated union with a 4th `"refreshing"` state distinct from `"present"`, so the panel component above can branch on it | Not independently clickable — verified indirectly through the same manual test as the row above: confirm the "Refreshing" badge appears ONLY on claims currently serving a stale generation and NEVER on a claim showing its current, freshly-computed generation (i.e. claims not touched by the triggered backfill keep rendering with no badge) |
| `/evidence` | Page-level response latency (no component change — `GET /api/evidence` serving path) | Changed behavior | Cache-key/staleness fix (`forward_testing.py:2461-2510`, new `compute_drawdown_expectations_cached_with_status`) prevents an unrelated ingest from forcing the whole page onto a multi-minute cold-recompute tail | With the backend idle (no backfill job running) navigate directly to `http://localhost:3255/evidence` and confirm all certified-claim panels render within a couple of seconds — no multi-second/multi-minute blank loading state beyond the normal initial page-load skeleton |
| `/evidence` | `EvidencePage`, other claim-card fields (verdict badge, hypothesis chips, "Unavailable" panel state) | Unchanged (regression check) | Same page as the above changes — must confirm nothing else on the claim card shifted | Navigate to `/evidence` and confirm every claim card still shows its verdict badge (e.g. "PASS"/"INSUFFICIENT"), hypothesis chips, "Out-of-sample verdict", "Registration date", and "Forward-walk score-to-date" fields exactly as before; if any claim currently shows "Unavailable — monitored and refreshed as new data arrives" instead of a table, confirm that text is unchanged |

---

## Backend-Only Changes (No UI Impact)

- `apps/backend/app/engine/research.py` (`_factor_decile_observations`) — a new bounded two-pass resolver
  for the decile-cohort branch of the Evidence page's underlying observation lookup. Byte-identical output
  to the pre-fix computation, verified by dedicated tests — no UI surface affected, values displayed do not
  change.
- `apps/backend/app/engine/samples.py` (`_factor_samples`'s decile branch) — now calls the bounded resolver
  above instead of materializing and sorting the whole observation history in memory. No UI surface
  affected.
- `apps/backend/app/engine/forward_testing.py` (`_drawdown_ticker_slice_map`'s new `snapshot_dates`
  filter) — narrows a ~8-million-row database read to only the dates each claim's evaluation window needs.
  Byte-identical `drawdown_expectations` output — no UI surface affected.
- `apps/backend/app/engine/warmup.py` (`_warm_drawdown_expectations`'s two exception handlers) — switches
  from a bare `logger.exception` call to the existing `_log_isolation_failure` degrade-to-marker
  convention. Affects only server log output during a severe-memory-pressure edge case — no UI surface
  affected.
- All changed/added test files (`test_forward_testing.py`, `test_research_streaming.py`,
  `test_samples_memory_pressure.py` (new), `test_warmup.py`, `test_evidence.py`,
  `apps/frontend/lib/evidence.test.ts`) and `reports/perf-budgets.md` — test/documentation artifacts, no
  UI surface affected.

---

## Summary

- **Frontend surfaces changed:** 1 (the Evidence page's `DrawdownExpectationsPanel`, plus its supporting
  resolver in `lib/evidence.ts`)
- **New pages/routes:** 0
- **Modified components:** 2 (`DrawdownExpectationsPanel` in `apps/frontend/app/evidence/page.tsx`;
  `resolveDrawdownExpectationsPanelState`/`CertifiedClaim` type in `apps/frontend/lib/evidence.ts`)
- **Navigation changes:** no
- **Backend-only changes:** 4 (`research.py`, `samples.py`, `forward_testing.py`'s slice-map date filter,
  `warmup.py`) — plus the cache-staleness fix in `forward_testing.py`/`evidence.py`, which IS visible (see
  surface rows above) since it is the direct cause of the "Refreshing" badge and the fixed page latency.
