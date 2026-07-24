# Iteration 17 — Coherence Audit

**Iteration:** goal-ops-hardening-iter-17
**Date:** 2026-07-24
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

---

## Data Contract check

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| `evidence_asof` (new field, additive to the "Regime score, market phase, realized forward-returns" row) | OK | Computed only inside the single registered resolver `resolved_forward_aggregate_evidence` (`apps/backend/app/engine/forward_testing.py:1174`, extended in place — no new function). Both registered callers read it identically: `apps/backend/app/api/backtest.py:89,106` and `apps/backend/app/mcp/tools.py:219,223`. Frontend: `apps/frontend/lib/api.ts:1104` (type addition only, no new fetch — `fetchBacktest()` at `lib/api.ts:1110` remains the single call site, confirmed the only frontend caller via repo-wide grep) and `apps/frontend/app/backtest/page.tsx:246,260` (display-only consumption, no client recompute). Already registered in `runs/goal-session-ops-hardening/state/blueprint.md`'s Data Contract as `[TARGET, iter-17 building]` before this iteration ran — not an unregistered value. |
| `compute_forward_aggregates` (canonical producer, unchanged) | OK | Exactly one definition, `apps/backend/app/engine/forward_testing.py:782`, byte-unchanged this diff (no hunk touches it). Exactly one call site anywhere in `apps/backend/app`: `forward_aggregates_ingest_cached` at `forward_testing.py:1120` (confirmed via repo-wide grep of `compute_forward_aggregates(` across `apps/backend/app`) — matches the blueprint's binding "Do not redo" list. |
| `evidence_generated_at` (existing field, reformatted only) | OK — reformat, not a new source | New helper `_utc_isoformat` (`forward_testing.py:1160-1167`) attaches `timezone.utc` to the SAME already-computed, already-stored `created_at` value before serializing — a display/serialization fix (audit B3), not a second derivation. Used only inside the same `_serve()` closure both `evidence_status`/`evidence_asof` already come from. |
| Evidence-section "as-of" window label (`EvidenceAggregateSection`'s `asofDate` prop) | OK — coherence-positive correction | `apps/frontend/app/backtest/page.tsx:260`: `asofDate={backtest.evidence_asof ?? backtest.asof_date}`. `evidence-panels.tsx` uses this prop for display text only (`formatIsoDate(asofDate)` at three call sites, `apps/frontend/components/evidence-panels.tsx:237,241,263`) — never as a computation input; the numbers themselves come from the `evidence` prop (the server payload), unchanged. This binds the "≤ D" window claim to the as-of whose evidence is actually being served rather than the page's requested as-of, eliminating a would-be contradiction with the `refreshing` banner above it. |

## Information Architecture check

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| `/backtest` evidence section (banner text + empty-state copy + new field display) | OK | No new page/route/nav entry. `git diff <snapshot-sha> --stat` against `*sidebar*`/`*nav*`/`*Sidebar*`/`*Nav*` patterns returns zero changed files. Full diff stat (8 files: `README.md`, `apps/backend/app/api/backtest.py`, `apps/backend/app/engine/forward_testing.py`, `apps/backend/app/mcp/tools.py`, two backend test files, `apps/frontend/app/backtest/page.tsx`, `apps/frontend/lib/api.ts`) contains no layout/router/shell file. `reports/phase-goal-ops-hardening-iter-17-ui-surface-map.md` independently confirms exactly one frontend surface changed, zero new pages, zero navigation changes. `/backtest` already has its canonical home in `blueprint.md`'s IA table (J-06/J-07/J-08 rows) — this iteration extends what's already there. |

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- The `EvidenceAggregateSection` as-of binding fix (`backtest.evidence_asof ?? backtest.asof_date`, `page.tsx:260`) is a genuine single-source-of-truth improvement landed in this same diff — noting it as a positive precedent rather than a defect: it is exactly the kind of correction this gate exists to encourage (a displayed claim now traced to the value it actually describes).
- `evidence_asof`'s frontend display goes through the pre-existing canonical formatter (`formatIsoDate`/`formatIsoDateTime`, imported from `apps/frontend/lib/dates.ts`, already used elsewhere in the same file for `resolvedDate`) — no second date-formatting path was introduced for the new field.
- `README.md`'s "Backtest workspace" bullet was updated to add the new 11/68 ingest-window latency finding but does not narrate the cross-`asof_key` fallback / `evidence_asof` capability in user-facing prose. README accuracy is outside this gate's Data Contract / IA rules (it is neither a nav surface nor a served value), so this is not scored here — flagged only so the decomposer can pick it up as a documentation-completeness item if desired, not as a coherence defect.
- Backend-only, out-of-scope for this gate but confirmed non-issue in passing: the `browser-qa` FAIL verdict this iteration traces to an operator-side dev-server build-directory collision (`runs/goal-ops-hardening-iter-17/operator-next-build-collision.md`), which itself confirms via `git diff` that every readiness/health/API-base-URL file is untouched this iteration — an environment defect, not a product or IA regression, and already corrected.
