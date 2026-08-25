# Iteration 14 — Coherence Audit

**Iteration:** goal-market-compass-iter-14
**Date:** 2026-08-25
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

<!-- COHERENCE-PASS: no objective violations; at most minor advisory notes -->

---

## Scope note

This iteration is entirely backend, read-only-against-the-live-DB maintenance/hardening tooling
(J-11 Stage D readiness): two new engine modules (`app/engine/j11_stage_d.py`,
`app/engine/j11_avb_diagnostic.py`), two new read-only CLI scripts, four new/extended test files, and
one hardening edit to `run_j11_stage_c_bounded_clear.py`'s `--evidence-dir` argument (adds a refusal
path; changes no destructive-sequence logic). `git status` confirms zero files under `apps/frontend/`
touched. No new endpoint, no new served/displayed value, no service booted, no browser/replay lane run
(maintenance isolation active, matching the iter spec's "Blueprint conformance: No new page, nav entry,
or IA change. No Data Contract row is touched, added, or reassigned"). Verified directly against the
diff (`git diff cabc026ca1e5fbd0b76c73b749a9f888acd8e885`) and `git status`, not just the spec's own
claim.

## Data Contract check

The only blueprint-registered value this iteration's new code path touches at all is **Engine
identity** (canonical source: `app.engine.engine_identity`). Everything else the new modules read
(scores, ADV, sector/regime data) is exercised only inside an internal, unserved diagnostic — never
displayed or served through any endpoint — so it does not create a second producer of a registered
value; it is a read-only counterfactual exploration using the real canonical functions as-is.

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Engine identity | OK | `apps/backend/app/engine/j11_stage_d.py:113` (`freeze_stage_d_attempt_identity` calls `j11_maintenance.freeze_attempt_identity`, itself a wrapper around `app.engine.engine_identity.compute_engine_identity`) and `j11_stage_d.py:247` (`capture_stage_d_preflight`'s Check-A independent re-derivation also calls `engine_identity.compute_engine_identity(cfg)` directly — same canonical function, second call for comparison, not a second implementation) |
| Stock leadership/entry/risk scores, buckets, setup status; ADV/liquidity | OK (not a new served value) | `apps/backend/app/engine/j11_avb_diagnostic.py:385` (`trace_scoring_and_selection_impact` calls the real `score_stocks(session, asof, cfg)` for representation A) and `:357-360` (calls the real `ur._adv_dollar`/`ur.resolve_candidate`) and `:404-448` (calls the real `scoring._avg_dollar_volume`, `scoring._neg`, `scoring._build_score`, `to_bucket`, `classify_setup`, `_qualifier_checks`) — representation B is built by substituting bars in-memory (`_build_bars_with_transformed_close`, `:323-333`) and re-running the SAME canonical functions, never a reimplementation. Confirmed by grep: no `def score_stocks\|def _adv_dollar\|def resolve_candidate\|def _build_score` etc. anywhere in the new files — only imports of the real ones. None of this is served via any API/UI (`GET /api/compass` is not called this iteration, per the spec and confirmed no frontend/route file changed) |
| Manifest DDL/dump comparison logic (`compare_stage_d_preflight_to_certified`) | OK (not a Data Contract row) | `j11_stage_d.py:317-373` duplicates the *shape* of several comparison expressions from `j11_stage_c.compare_preflight_to_certified` (`j11_stage_c.py:276-308`) rather than calling it — flagged for DRY by the iteration's own auditor (finding B4, `docs/handoffs/goal-market-compass-iter-14-audit.md`). This is an internal maintenance precondition-gate, not a registered "displayed value/entity" in the blueprint's Data Contract table, so it is not a Part-A violation; noted below as advisory only |

No new displayed value is introduced (confirmed: no frontend file changed, no new route, `GET
/api/compass` not called — matches the iter spec's own "New information displayed: None"), so there is
nothing to register or flag as unregistered.

## Information Architecture check

No new page, route, or feature exists this iteration to check — `apps/frontend/` is untouched
(`git status` / `git diff` both confirm zero frontend files in this diff), and the UI surface map
(`reports/phase-goal-market-compass-iter-14-ui-surface-map.md`) records "Not mapped this iteration —
maintenance isolation" with no surface opened. Nothing to place in the nav skeleton.

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| (none — no frontend change this iteration) | N/A | n/a |

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- The iteration's own auditor (`docs/handoffs/goal-market-compass-iter-14-audit.md`, finding B4)
  already flagged that `compare_stage_d_preflight_to_certified` (`j11_stage_d.py:317-373`) duplicates
  nine comparison expressions' *shape* from `j11_stage_c.compare_preflight_to_certified`
  (`j11_stage_c.py:276-308`) instead of calling it against a differently-shaped baseline. This is a
  code-DRY concern the auditor already tracks for the pre-Stage-D-authorization punch list — it is not
  a Data Contract violation (neither function computes a blueprint-registered displayed value; both are
  internal maintenance precondition gates) and does not affect this verdict.
- The auditor also flagged (B5) that `run_j11_stage_d_preflight.py` and
  `run_j11_avb_bridge_diagnostic.py` still carry an argparse `--evidence-dir` default pointing at a
  committed-but-currently-untracked directory (`runs/goal-market-compass-iter-14/`) — the same footgun
  class that corrupted iteration-13 evidence earlier in this iteration (fixed for the Stage C script,
  not yet applied to these two). This is a tooling-safety concern already tracked by the auditor
  (DoD item 10 / B5), not an IA or Data Contract matter, so it does not affect this verdict.
