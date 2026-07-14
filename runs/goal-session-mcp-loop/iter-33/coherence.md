# Iteration 33 — Coherence Audit

**Iteration:** goal-mcp-loop-iter-33
**Date:** 2026-07-14
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

---

## Data Contract check

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Daily preflight verdict (`GO`/`DEGRADED`/`NO-GO` + reasons) — NEW this iteration (J-20/B-301) | OK | Computed once: `apps/backend/app/engine/readiness.py:210-312` (`compute_preflight`). Served: additive `preflight` field on the EXISTING `GET /api/health` — `apps/backend/app/api/health.py:46-71` (no new endpoint). ONE reader: `apps/frontend/components/preflight-banner.tsx` via `useReadiness()` → `apps/frontend/components/readiness-provider.tsx:58-68` (same poll cycle, no second `fetch`). |
| — servability input (reused, not recomputed) | OK | `readiness.py:256` calls `compute_readiness(...)["state"]` directly; `compute_readiness`'s own body (`readiness.py:~40-185`) is untouched by the diff — confirmed byte-identical shape by `test_readiness.py::test_compute_readiness_shape_unchanged_by_preflight_addition` and `test_readiness.py::test_preflight_servability_reuses_compute_readiness_verbatim`. |
| — integrity input (ledger/registry existence+parse) | OK | Imports the three EXISTING resolvers verbatim — `resolve_ledger_path` (`app/engine/evidence.py:47`), `resolve_staging_ledger_path` (`app/engine/graveyard.py:69`), `resolve_registry_path` (`app/engine/registry.py:40`) — `readiness.py:159-163,287-291`. No second path-resolution logic; only existence+parse is checked (content is never re-served), so no evidence/registry/graveyard contract value is re-derived. |
| — freshness input (latest bar age) | OK | `readiness.py:235` calls the existing `latest_data_date(session)` from `app.engine.prices` — the same utility other consumers use; no parallel date-resolution implementation. |
| Evidence status, 3 per-stock scores, regime, sector, theme, forward-return, research-lab cohorts, index vendor label, DB capacity, registry, graveyard, budget-accounting (all pre-existing contract rows) | OK — untouched | None of these files appear in the diff (`git diff <snapshot-sha>`); `compute_readiness`'s `state`/`warmup` output is asserted byte-identical (J-40 non-regression, per DoD). |
| Frontend: any client-side recompute of the verdict | OK — none found | `preflight-banner.tsx:19-61` only branches on `preflight.verdict` / `preflight.reasons` read verbatim from context; no derivation logic. `grep -ril "preflight" apps/frontend` returns exactly the 4 expected files (`readiness-provider.tsx`, `preflight-banner.tsx`, `lib/api.ts`, `layout.tsx`) plus two irrelevant `node_modules` type-declaration false positives. |
| Single fetch-path check | OK | `grep -rn "/api/health"` across `apps/frontend` returns exactly one call site: `lib/api.ts:153` (`fetchHealth`), invoked only from `readiness-provider.tsx`. No second poller. |

## Information Architecture check

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| `PreflightBanner` — cross-cutting layout chrome (no route of its own) | OK | Mounted once in the EXISTING single root shell `apps/frontend/app/layout.tsx:47` (between `<header>` and `<main>`); confirmed the only `layout.tsx` under `apps/frontend/app/` per the ui-impact-analyst's surface map. `apps/frontend/components/sidebar.tsx` — diffed against the snapshot SHA — is byte-identical (empty diff): no nav-skeleton change, no new top-level section, no new sub-route. Blueprint's IA table registers this exact home for J-20 ("app-shell layout banner ... cross-cutting chrome — no new nav section, no new page"), matching what was built. |
| Reachability | OK | Not applicable in the "N clicks" sense — chrome renders on every one of the 27 routes automatically (0 clicks), per the ui-surface-map's route enumeration. |
| Duplicate-home check | OK | No pre-existing "trust/safety verdict" surface exists to duplicate; the closest neighbor, `HealthBadge`, is untouched by this diff and displays a narrower, different value (raw ready/initializing/unavailable + warmup n/m) — `compute_preflight` composes over it as one input rather than re-deriving or replacing it (documented explicitly in the blueprint's iter-33 clarification and in `readiness.py`'s own docstring). |
| Parallel-shell check | OK | No new layout/provider tree was introduced — `ReadinessProvider` (existing) was extended in place, not duplicated. |

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- The `docs/phases/goal-mcp-loop-iter-33.md` NOTES section itself flags that the README preflight bullet is a deliberate carry-forward to the readme-maintainer showcase step (not bundled into this dev pass) — consistent with the current diff (README.md gained only the iter-32 budget-panel bullet so far). Not a coherence defect; noted only so the next showcase pass doesn't drop it.
- No other drift observed: `compute_readiness`'s body, `sidebar.tsx`, and every pre-existing Data Contract row are absent from the diff entirely, which is the cleanest possible evidence of "additive, not touched."
