# Iteration 60 — Coherence Audit

**Iteration:** goal-ops-hardening-iter-60
**Date:** 2026-08-11
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

---

## Data Contract check

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Regime score, market phase, realized forward-returns (`by_horizon[].status`/`.n`/`.mean_return`, blueprint row "Regime score, market phase, realized forward-returns") | OK | `apps/backend/app/engine/research.py:4447-4477` — `compute_regime_lab`'s prologue (`horizons`/`labels`/`_run_position_index`) is wrapped in try/except; the except-arm calls the pre-existing `_degrade_regime_lab_horizon` helper (defined at `research.py:4361`, already the sole degrade producer used by the per-horizon loop body's own catch) — no second degrade/compute path introduced. Same function, same module, same endpoint (`GET /api/research/regime-lab`), consistent with the blueprint row's own iter-60 note. |
| Regime-Lab degraded-cell display (`status === "unavailable"`) | OK (re-format/consumption only) | `apps/frontend/lib/regime-cell-status.ts:16` — `isRegimeCellUnavailable(cell)` returns `cell.status === "unavailable"`, a pure predicate over the already-fetched, already-registered `by_horizon[].status` field (typed at `apps/frontend/lib/api.ts` per the iter spec's Data-contract-additions note: "None"). It does not fetch from a second endpoint or recompute the underlying value — only decides which of two existing renderings (`SampleLink` chip vs. an "Unavailable" indicator, `apps/frontend/components/sample-link.tsx:218-229`) to show. One call site (`apps/frontend/app/research/_labs.tsx:3958`); the sibling `<SampleLink>` call in `apps/frontend/app/research/severity-velocity/page.tsx:221` never passes the new optional `unavailable` prop, so it stays byte-unchanged, per the diff's own doc comment. |
| Target-journey replay coverage (test infrastructure, not a product Data Contract value) | N/A | `incredible_auto_dev/scripts/automation/lib/replay-lane.sh:264-297` (symlinked at `scripts/automation/lib/replay-lane.sh`) — this and its test (`incredible_auto_dev/tests/automation/test-replay-lane.sh`) are pipeline/CI plumbing, not a user-displayed value; outside the Data Contract's scope. |

No new displayed value was introduced this iteration (the iter spec's "Data-contract additions: None" claim holds — the "Unavailable" indicator is a rendering choice over an already-registered field, not a new value).

## Information Architecture check

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| `/research/regime-lab` (`RegimeReturnCell` degraded-cell rendering) | OK — existing home, no new route | `runs/goal-session-ops-hardening/state/blueprint.md:392` (Research nav entry, "index of 15 labs (event-study, factor-lab, regime-lab, …)"); iteration only edits `apps/frontend/app/research/_labs.tsx` and `apps/frontend/components/sample-link.tsx`, both already inside the existing Research page — no new file under `app/research/`, no new router entry. |
| `GET /api/research/regime-lab` (backend prologue hardening) | OK — same endpoint | No new route registered in `apps/backend` this diff; only `compute_regime_lab`'s internal body changed. |

No new page, route, or nav entry was added this iteration (confirmed against the diff's file list — `apps/backend/app/engine/research.py`, `apps/backend/tests/test_regime_lab.py`, `apps/frontend/app/research/_labs.tsx`, `apps/frontend/components/sample-link.tsx`, `apps/frontend/lib/regime-cell-status.ts` (+its test), `incredible_auto_dev/scripts/automation/lib/replay-lane.sh` (+its test) — 8 files total, matching `iter-diff.md`'s "Files changed: 8. Shown in full: 8." header and `git status`). This matches the iter spec's own "Blueprint conformance" and "Product surface delta" fields ("No nav or page-count change").

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- `scripts/automation/lib/replay-lane.sh` at the repo root is a symlink into `incredible_auto_dev/scripts/automation/lib/replay-lane.sh` (verified: `readlink -f` resolves there, byte-identical, and `git ls-files` shows only the symlink is tracked at the outer path). This is the project's existing neutral-asset-source pattern (per CLAUDE.md — "edit the neutral source"), not a duplicate implementation; noted only so a future auditor doesn't mistake the two paths in `git status` for two divergent copies.
- No formatting-drift or label-inconsistency issues observed on the touched surface: the new "Unavailable" indicator (`apps/frontend/components/sample-link.tsx:218-229`) uses the existing `text-text-faint` token and an `AlertTriangle` icon consistent with the app's established degraded-state styling elsewhere (readiness badge / preflight banner precedent named in the blueprint's Information Architecture section).
