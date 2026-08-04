# Iteration 47 — Coherence Audit

**Iteration:** goal-ops-hardening-iter-47
**Date:** 2026-08-04
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

---

## Data Contract check

All production changes land inside the already-registered "Membership timeline / research hot-key
caches" row (`blueprint.md` line 408) and its already-named contributing modules
(`app.engine.forward_testing`, `app.engine.research`, `app.engine.samples`, `app.engine.warmup`),
serving exclusively through the row's already-registered endpoint (`GET /api/evidence`). No API
router file (`apps/backend/app/api/*.py`) changed in this iteration's diff (`git diff
852b7f03b8...463a2 --stat`) — confirms no new endpoint was added.

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Per-claim `drawdown_expectations` (TC-1/2/3, cache-thrash fix) | OK — new `compute_drawdown_expectations_cached_with_status` (`apps/backend/app/engine/forward_testing.py:2694-2748`) is the sole new `/api/evidence` call site (`apps/backend/app/engine/evidence.py:22,26-28`), and on both HIT and cold-start-MISS paths returns exactly what the pre-existing canonical `compute_drawdown_expectations_cached`/`compute_drawdown_expectations` already computed — it delegates to `compute_drawdown_expectations_cached` for the cold-start case (`forward_testing.py:2748`) and never introduces a second `compute_drawdown_expectations`-equivalent. The stale-serve branch returns one whole `EventStudyCache.payload_json` row, never a merge of two generations. | `apps/backend/app/engine/forward_testing.py:2694-2748`, `apps/backend/app/engine/evidence.py:158-195` |
| New optional field `expectations_status: "refreshing"` | OK — registered CONDITIONAL in `blueprint.md`'s iter-47 paragraph (line 350) and Data Contract row (line 408) ahead of this dispatch; ships exactly as specified, additive-only, mirrors the already-registered `"unavailable"` (iter-29) and `/backtest`'s `evidence_status` (J-08) sibling patterns. Frontend reads it from the SAME already-fetched `GET /api/evidence` payload — no new fetch introduced (`apps/frontend/lib/evidence.ts:465-471` only adds a branch to the existing pure resolver; no `fetch(`/`axios`/route change anywhere in the frontend diff). | `apps/frontend/lib/evidence.ts:432-434,465-471`, `apps/frontend/app/evidence/page.tsx:375-397` |
| Factor-decile cohort members (feeds `compute_samples` → `compute_drawdown_expectations`, B3 bound) | OK — `_factor_decile_observations` is added to `app.engine.research`, already a named contributing module for this row since iter-29/iter-46. It replaces `samples.py`'s inline `sorted(_factor_observations(...))[lo:hi]` (the exact `samples.py:145`/`:156` lines the iter spec targeted) with a two-pass bounded-window equivalent, with a documented byte-identical fallback to the original unbounded computation if its own invariant is ever violated. Single call site swap in `_factor_samples`'s "decile" branch (`apps/backend/app/engine/samples.py:263-280`) — the `"total"`/`"regime"` branches still call the original unbounded `_factor_observations` unchanged. No second producer, no second endpoint. | `apps/backend/app/engine/research.py:329-566` (new), `apps/backend/app/engine/samples.py:263-280` |
| `_drawdown_ticker_slice_map` date-scoped read | OK — same function, same table (`ForwardReturn`), same two callers; adds an optional `dates_by_ticker` parameter that, when `None` (every other test/caller), preserves the pre-iter-47 unfiltered query byte-for-byte. Byte-identity is the explicit contract in the function's own docstring. | `apps/backend/app/engine/forward_testing.py:59-118, 2423-2439` |
| `warmup.py:205`/`:212` log-guard convention | OK — swaps a bare `logger.exception` for the SAME `_log_isolation_failure` degrade-to-marker convention already used at 19+ other sites (per blueprint's "Backend readiness" row precedent) — no new computation, no new field. | `apps/backend/app/engine/warmup.py:335-350` |

## Information Architecture check

UI surface map (`reports/phase-goal-ops-hardening-iter-47-ui-surface-map.md`) and the diff both
confirm zero new routes/pages and zero nav changes — `apps/frontend/components/sidebar.tsx` (or
equivalent nav/router files) does not appear anywhere in this iteration's changed-file list. The
sole frontend change is an additive `Badge` on the already-nav-listed `/evidence` page (1 click from
the persistent sidebar per `blueprint.md`'s Navigation skeleton, line 371), reusing the existing
`Badge` component and its `variant="warn"` styling already established on `/backtest`
(`apps/frontend/app/backtest/page.tsx:108`) for the analogous `evidence_status: "refreshing"` case —
same visual language, no parallel pattern invented.

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| `/evidence` "Refreshing" badge (`DrawdownExpectationsPanel`) | OK — existing home, no new component, 1-click reachable | `apps/frontend/app/evidence/page.tsx:375-397`; no sidebar/router file present in diff stat (confirms unchanged) |

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- `compute_drawdown_expectations_cached_with_status`'s current-version HIT-path query
  (`forward_testing.py:2718-2726`) re-states the identical five-column `EventStudyCache` WHERE clause
  that `compute_drawdown_expectations_cached`'s own HIT path already has (`forward_testing.py:2532-2540`)
  instead of delegating to it. Both hit the same table with the same key composition, so they cannot
  diverge in value — this is a code-duplication/DRY note, not a data-contract risk. Worth folding into
  a shared helper in a future cleanup pass, not required this iteration.
- The new single-flight background re-warm (`_spawn_drawdown_expectations_rewarm`,
  `forward_testing.py:207-273`) is a third invocation site of the canonical
  `warmup._warm_drawdown_expectations` → `compute_drawdown_expectations_cached` chain, alongside the
  existing boot-time trigger and the ingest-finalize trigger. It reuses the same producer (no second
  computation) and is described at the row-Notes level ("a background re-warm completes",
  `blueprint.md` line 350/408), but is not yet named by function name in the Data Contract row's Notes
  the way iter-46's boot-time trigger was retroactively named at iter-47. Suggest the iter-48
  decomposer name `_spawn_drawdown_expectations_rewarm` explicitly in that row for the same parity, as
  a documentation-only follow-up — not a violation.
