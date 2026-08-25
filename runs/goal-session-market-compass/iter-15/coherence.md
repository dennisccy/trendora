# Iteration 15 — Coherence Audit

**Iteration:** goal-market-compass-iter-15
**Date:** 2026-08-25
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

---

## Scope note

This iteration is backend-diagnostic-only under active maintenance isolation: no frontend file
touched, no `apps/backend/app/api/*` route added or changed, no `apps/backend/app/models.py`
schema change, no application-service boot, no browser/replay lane. Confirmed directly from the
noise-excluded diff (`git diff 0f533c495b4af8a73b36804928f02f7117165ddc`, 13 files changed, 3056
insertions / 71 deletions): `apps/backend/app/engine/{j11_avb_diagnostic.py, j11_stage_d.py}`
(modified), `apps/backend/app/engine/j11_avb_provider_fetch.py` (new), five
`apps/backend/scripts/run_j11_*.py` CLI scripts (new/modified), four
`apps/backend/tests/test_j11_*.py` files, and `docs/phases/goal-market-compass-iter-15.md`. No
`diff --git` header touches `apps/frontend/`, `apps/backend/app/api/`, or
`apps/backend/app/models.py` — grep-verified against the full diff. The iteration spec's own
"Blueprint conformance" / "Data-contract additions: None" self-assessment matches the actual diff,
and `reports/phase-goal-market-compass-iter-15-ui-surface-map.md` independently confirms no
surface was opened this iteration (maintenance isolation). `runs/goal-session-market-compass/
state/blueprint.md` was not modified (not in `git status`) — correctly so, since nothing in this
iteration touches a registered value's computation or serving path, or the nav/IA.

Per the coordinator's specific request, I traced two things this iteration deliberately builds on
top of the blueprint's Data Contract:

1. **Engine identity.** The blueprint's Data Contract row states Engine identity is computed by
   `app.engine.engine_identity` and stamped at manifest build / `persist_run_payload`. This
   iteration's new `capture_readiness_time_identity_observation`
   (`apps/backend/app/engine/j11_stage_d.py`, new function per the diff) wraps the EXISTING
   `freeze_stage_d_attempt_identity` — left completely unchanged in this diff (only its call site
   swapped) — which in turn (pre-existing code, unmodified this iteration,
   `apps/backend/app/engine/j11_maintenance.py:206-215`) calls
   `app.engine.engine_identity.compute_engine_identity` directly. Grep across
   `apps/backend/app/engine/*.py` confirms `compute_engine_identity` has exactly one definition
   (`engine_identity.py:44`) and every call site — `compass.py:912` (the canonical
   `GET /api/compass` producer), `scanner.py:119` (`persist_run_payload`),
   `j11_maintenance.py:215`, and `j11_stage_d.py:315` (an independent re-derivation used only to
   *compare against* a stored value, not to mint a new canonical one) — calls the same function.
   No duplicate computation introduced.
2. **ADV / liquidity / Risk in the decision-impact trace.** `trace_universe_resolver_impact` and
   `trace_scoring_and_selection_impact` (`apps/backend/app/engine/j11_avb_diagnostic.py`) both
   gained an additive `volume_override` keyword-only parameter this iteration (threaded into
   `_build_bars_with_transformed_close`), but their bodies still call the real
   `ur._adv_dollar`/`ur.resolve_candidate` (imported `from app.engine import universe_resolver as
   ur`) and the real `score_stocks`/`scoring._avg_dollar_volume`/`_build_score`/`to_bucket`/
   `classify_setup`/`_qualifier_checks` (imported from `app.engine.scoring`, `app.engine.buckets`,
   `app.engine.setups`, `app.engine.compass` respectively — verified via the file's import block,
   `apps/backend/app/engine/j11_avb_diagnostic.py:60-70` — none of these six canonical names is
   locally redefined anywhere in the file). No second scoring/ADV implementation exists.

## Data Contract check

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Engine identity | OK — reused | `apps/backend/app/engine/j11_stage_d.py` new `capture_readiness_time_identity_observation` wraps unchanged `freeze_stage_d_attempt_identity`; canonical `compute_engine_identity` single definition at `apps/backend/app/engine/engine_identity.py:44` |
| Stock leadership/entry/risk scores, buckets, setup status (ADV/liquidity/Risk) | OK — reused | `apps/backend/app/engine/j11_avb_diagnostic.py:60-70` imports `universe_resolver as ur`, `scoring`, `buckets.to_bucket`, `setups.classify_setup`, `compass._qualifier_checks`; `trace_universe_resolver_impact`/`trace_scoring_and_selection_impact` call these directly, never reimplement |
| (no other registered row touched) | N/A | no API route, model, or frontend file in the diff |

No new displayed value is introduced (Frontend Present: no; `GET /api/compass` is never called this
iteration, per the spec and confirmed by the absence of any `app/api/*` diff). The AVB
counterfactual/diagnostic values (`compute_provider_comparison`, `classify_date_from_provider_
comparison`, `classify_local_convention_with_volume_evidence`, `compute_counterfactual_
representations`'s new `provider_evidence`-driven path) are internal J-11 diagnostic artifacts
persisted under `runs/goal-market-compass-iter-15/*.json` — never served through any endpoint, never
rendered in any UI — so they are not Data Contract candidates and register no violation. The
headline `AVB-C` / `ready: false` result in the freshly-produced
`runs/goal-market-compass-iter-15/j11-stage-d-readiness.json` (verified: matches the coordinator's
description) reflects a diagnosed, deliberately-unrepaired data condition in AVB's stored
`daily_prices`, not a UI-displayed value with divergent sources — out of this gate's scope by
design.

## Information Architecture check

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| (none — no frontend change this iteration) | N/A | grep of the full diff for `apps/frontend`, `.tsx`, `.jsx`, `sidebar`, `APIRouter`, `@router`, `FastAPI` returns zero matches |

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- None. This iteration's substantive delta is entirely internal diagnostic tooling (a new
  fetch-evidence module, an extended classifier, a committed readiness producer, hardened negative
  tests, and CLI-script safety guards) with no UI-facing or Data-Contract-facing surface, so there
  is nothing for Part C to flag beyond what is already noted above.
