# Iteration 8 — Coherence Audit

**Iteration:** goal-market-compass-iter-8
**Date:** 2026-08-21
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

---

## Scope note

This iteration (J-10: redesigned per-symbol path-agreement + stable-bridge recovery gate) is
backend-only, no new displayed value, no new endpoint, no blueprint edit — matching the spec's own
"Blueprint conformance" / "Data-contract additions" claims of "None." Those claims were verified,
not assumed:

- `git diff 161fc4632c6f7b95406270d02a7585e8b3d2fb58 -- runs/goal-session-market-compass/state/blueprint.md`
  produces **zero** output — the blueprint file is byte-identical to before this iteration ran.
- `git diff 161fc4632c6f7b95406270d02a7585e8b3d2fb58 --stat` (noise-excluded) touches exactly two
  product code files plus two test files: `apps/backend/app/data_providers/yahoo_provider.py` (+8/-4,
  docstring only), `apps/backend/app/engine/j10_recovery.py` (705 lines, the redesigned gate),
  `apps/backend/tests/test_j10_recovery.py`, `apps/backend/tests/test_provider_clients.py`. No file
  under `apps/frontend/` or `apps/backend/app/api/` appears anywhere in the diff; no file under
  `apps/backend/app/models.py` / `apps/backend/app/db.py` appears either (no schema change).
- The product commit is exactly `47d50d04` ("iter 8 — J-10 bridge gate + first live recovery writes
  (20/587)"). Five later commits on `HEAD` (`b7b51aa1` … `51ae56d2`) touch **only** `docs/goal.md`
  (+ one quarantine-evidence md) — owner goal-contract amendments authoring J-11 and clarifying that
  20/587 does not close J-10, not implementation, per this session's established "goal.md-only, no
  direct implementation" pattern. One further commit (`046dd956`, "fail closed when Depth: full is
  required but only lean can be dispatched") touches only `incredible_auto_dev/scripts/automation/*`
  — the goal-mode pipeline framework, not the Trendora product; it is the fix for the forbidden-lane
  defect noted below, not new product surface. Current `git status` shows zero uncommitted changes
  under `apps/backend/` or `apps/frontend/`, so the diff above is iter-8's complete and final product
  footprint. `reports/phase-goal-market-compass-iter-8-ui-surface-map.md` independently corroborates
  all of this (0 frontend surfaces changed, 4 backend code files, no new route).

## Data Contract check

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| `daily_prices` raw input rows (not itself a Data Contract row, but the single write path it depends on IS in scope) | OK | `run_data_job` has exactly one definer: `apps/backend/app/engine/data_manager.py:6095`. Its only external caller is `apps/backend/app/engine/j10_recovery.py` (grep: `run_data_job\b` → `data_manager.py` + `j10_recovery.py`, matching iter-6's finding, unchanged). `j10_recovery.py`'s new `_BridgeApplyingProvider` (`j10_recovery.py:709-753`) is an in-memory `PriceProvider` wrapper injected via the existing `provider=` parameter of `run_bounded_recovery_fetch` (`j10_recovery.py:846-848`) — it transforms bar values *before* they reach the single existing `data_manager.run_data_job` insert call (`j10_recovery.py` inside `run_bounded_recovery_fetch`, unchanged call site at line ~696-699). No second insert path, no direct `session.add`/`INSERT` anywhere in the new code. |
| J-10 convention-check verdict / bridge factor (internal orchestration state) | OK — not a Data Contract row | `convention_evidence_to_dict` (`j10_recovery.py:612-646`) serializes to `runs/goal-market-compass-iter-8/j10-convention-evidence.json`, a run artifact under `runs/`, not served by any endpoint and not displayed to a user — matches the spec's own "Data-contract additions: None" framing and mirrors iter-7's coherence finding on the prior verdict object. |
| `GET /api/compass` (existing endpoint, Data Contract row) | OK | Endpoint code untouched (no diff under `apps/backend/app/api/`). Its *observed* response for `as_of=2026-08-11`/`2026-08-12` changed from 400→200 purely because underlying `daily_prices`/`ScannerRun` data changed — compass still reads the same stored data through the same code path, never recomputes; this is data changing under an unchanged read, not a contract violation. |
| Yahoo adjusted-close series (`get_adjusted_close`/`_parse_adjusted_close`) | OK | Stays in place, additive, now provably unused by the live gate (docstring updated at `yahoo_provider.py:14-19`; `j10_recovery.py`'s gate now calibrates on `get_daily`'s raw close instead — same series used for calibration and restoration, resolving audit finding B2). Not a second computation of any registered value; it computes nothing that's in the Data Contract. |
| New information displayed / new user-facing capability | OK — none introduced | Spec states "None this iteration" for New information displayed / New user actions / UI surface changes; confirmed true by the diff (no frontend files, no template/serializer changes visible to a user). |

No duplicate computation, no non-canonical source, no new unregistered displayed value.

## Information Architecture check

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| *(none — no new page/route/feature this iteration)* | OK | `apps/frontend/components/sidebar.tsx` not present in the diff at all; `git diff --stat` confirms zero files under `apps/frontend/`. Nothing to place in the nav, nothing to check for reachability. |

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- **Forbidden-lane replay recurrence (observation for the evaluator, not a coherence finding):** a
  deterministic replay lane ran against the still-damaged database twice (lean depth, then again at
  full depth on re-run), which `docs/goal.md`'s lane gate forbids. This is an orchestration/framework
  defect, not a product IA/Data Contract issue — it produced no database mutation
  (`trendora.db-wal` untouched since 01:44:51) and is fully quarantined at
  `reports/qa/goal-market-compass-iter-8-evidence/INVALID-forbidden-lane.md` (with a dated addendum
  covering the recurrence) plus the two `INVALID-rerun-*` screenshots left alongside it. The fix for
  the underlying depth-arbiter bug is already committed on `HEAD` (`046dd956`, touching only
  `incredible_auto_dev/scripts/automation/*`), outside this iteration's product surface. Flagging for
  the evaluator per the coordinator's framing; scoring it as neither a Data Contract nor an IA
  violation.
- **J-10 completion status is out of this audit's lane.** `docs/goal.md` was amended after iter-8's
  commit (`b7b51aa1`, "owner amendment — recovery population vs validation sample, depth enforcement")
  to state that 20/587 restored does not close J-10. That is a goal-achievement judgment for the
  goal-evaluator, not a coherence question — this audit only confirms the *mechanism* iter-8 built
  (the per-symbol gate, the single write path, the bridge transform) introduced no structural drift,
  which it did not.
- **J-11 is spec-only so far.** Five commits on `HEAD` after `47d50d04` add substantial J-11 text to
  `docs/goal.md` (incident-bounded clean regeneration of derived state, schema gate, frozen identity,
  restart semantics, breaking the J-10/J-11 circular dependency) but touch no code. Nothing to audit
  yet — flagging only so the next coherence pass knows to check whether J-11's eventual implementation
  needs a blueprint update (it may introduce a new "regeneration" concept worth registering, depending
  on what ships).
- Unregistered-but-new values: none found this iteration.
- Formatting/labeling drift: none found this iteration (no UI surface exists to drift).
