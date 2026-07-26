# Iteration 24 — Coherence Audit

**Iteration:** goal-ops-hardening-iter-24
**Date:** 2026-07-26
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

---

## Data Contract check

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| `background_compute` (new field on "Backend readiness / boot phase + preflight verdict" row) | OK | Computed by `get_background_compute_status()`, `apps/backend/app/engine/forward_testing.py:1329-1352`, reading only the existing `_HIST_DISPATCH_LOCK`/`_HIST_DISPATCH_INFLIGHT` (extended, not duplicated) and the new `_HIST_RECENT_OUTCOMES` ring under that same lock (`forward_testing.py:1211-1213`). Composed into `compute_readiness`'s single return dict, `apps/backend/app/engine/readiness.py:225-235` (degrades to the honest empty shape on error, never a second producer). Served exclusively on `GET /api/health`, `apps/backend/app/api/health.py:35,69,109` — additive field on the SAME canonical endpoint, no new route. |
| `background_compute` — frontend consumption | OK | `readiness-provider.tsx:76` reads `data.background_compute` from the SAME `fetchHealth()` poll (`apps/frontend/lib/api.ts:212-214`) already used for `state`/`warmup`/`preflight` — no second fetch, no second poll. `HealthBadge` (`health-badge.tsx:753,766-776`) and `BackgroundComputePanel` (`apps/frontend/app/data/page.tsx:696-740`) both read it via `useReadiness()` only; confirmed by grep that no component fetches `/api/health` a second time for this value and no component recomputes `elapsed_ms`/`horizons_done` client-side (both come pre-computed from the server payload). `HealthBadge`'s pre-existing second `fetchHealth()` call (`health-badge.tsx:35`) is unrelated plumbing that predates this iteration (feeds only `detail`/provider-seed text) and is not touched by this diff. |
| `compute_forward_aggregates`, `resolved_forward_aggregate_evidence`, `ensure_historical_forward_aggregates_dispatched` keying/dispatch-decision | OK (confirmed unchanged) | `forward_testing.py:1307-1310` (`ensure_...`) keeps the identical "already-inflight -> no-op" check; only the value stored per key changed (`set` -> `dict` carrying bookkeeping), the decision logic itself is untouched. No hits for a second implementation of any of these three functions anywhere in the diff. |

No new value is displayed that isn't already registered; no duplicate computation of any existing blueprint row was introduced.

## Information Architecture check

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| Global readiness badge — new `background-compute-indicator` inline element | OK | `apps/frontend/components/health-badge.tsx:771-776`; no new route, mounted inside the existing `HealthBadge` component present on every page (unchanged mount point). |
| `/data` — new `BackgroundComputePanel` | OK | `apps/frontend/app/data/page.tsx:608-647` (renders the panel alongside the existing `RunHistoryPanel`); confirmed `apps/frontend/components/sidebar.tsx` and `apps/frontend/app/layout.tsx` show **no diff** against the iter-24 snapshot (`git diff 5bc546e2... --stat` for both paths returns nothing) — no nav entry was added or needed, `/data` already has its nav link and its own existing route. `PanelTitle`/`Card` are the SAME pre-existing local components `RunHistoryPanel`/`JobProgressPanel` already use (`page.tsx:621`), not a parallel shell. |

Both new UI surfaces land exactly in the homes the blueprint's iter-24-updated IA table already names for J-09 ("global readiness badge... + `/data`... same homes as J-04/J-07, no new page/route", `blueprint.md:319`) — reachable in 0 additional clicks (badge: every page already) and the existing 1-2 clicks to `/data`.

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- The blueprint's own Information Architecture (line 319) and Data Contract (line 333, appended Notes) rows were updated additively in the same diff to register `background_compute` and J-09's home — this is the decomposer/blueprint self-maintenance the framework expects, not a drift; verified the edit is purely additive (one new IA table row, one Notes-column append) with no nav-skeleton or existing-row change (`git diff 5bc546e2... -- runs/goal-session-ops-hardening/state/blueprint.md`).
- None beyond the above — this iteration is a clean, single-producer/single-endpoint instrumentation addition with no new page/route and no client-side derivation.
