# goal-mcp-loop-iter-10 Execution Plan

Backend-only. **Part B Phase 1** of goal.md's engineering direction: open the certification
engine's scan aperture beyond the 20-day horizon and run a PRE-REGISTERED candidate set through
the referee into the INTERNAL **staging** ledger under the online-FDR economy. Discovery-first —
NO canonical claim, NO UI, NO journey flip. It produces the referee-scored candidate list iter-11
promotes to surface J-07. Builds directly on iter-9's staging economy (`online_fdr.py`,
`verify_edge` ledger routing, `FdrCfg`) — most plumbing already exists; this iteration mostly
*activates* it and runs the fixed exploration.

Aligns with goal.md "Improvement direction (engineering) — Part B Phase 1" (multi-horizon after
Part A's economy shipped in iter-9). No drift from the goal detected.

## What to Build
- **Open the multi-horizon aperture (config).** Add `triad.horizons: [1, 5, 10, 20, 60]` in
  `config.yaml`. The scan code already reads `triad.horizons` (`_triad_cfg`, currently absent ⇒
  defaults to `[walk_forward.default_horizon] = [20]`) and already accepts a `horizons=` param, so
  the aperture opens by adding the config key. `scan_factor_decile_cells` / `scan_product_triad`
  then enumerate one cell per `(factor, horizon, decile)` across all configured horizons. Reuses
  `compute_factor_lab` + the already-present `walk_forward.horizons` forward-return data.
- **Scale the multiple-testing haircut.** Raise `triad.top_k` (currently 20) and set the currently
  inert `triad.screen.haircut_coef` (currently 0.001) so the screen's haircut grows with the ~5×
  wider batch. Values consumed verbatim from config — no magic numbers in code. New values are the
  developer's call (consistent with the 5-horizon aperture); record them in the handoff.
- **Register the PRE-REGISTERED candidate set** (the anti-data-mining keystone): a FIXED,
  config-backed list mirrored into `project-extensions/proposer-guidance.md`, each carrying a
  one-line economic rationale. The 4 candidates (decile 10, direction positive):
  - `vcp_contraction` D10 @ **h10** — post-contraction expansion at a ~2-week hold (signal-less; cleanest J-07 candidate)
  - `vcp_contraction` D10 @ **h60** — does the edge persist/strengthen over a quarter? (signal-less)
  - `rs_spy_3m` D10 @ **h60** — 3-month RS leadership over a matched hold (signal-less; speculative member)
  - `leadership_score` D10 @ **h60** — the strongest signal (hit the p-floor at h20) probed longer; a high-probability ANCHOR (score-column ⇒ does not disturb J-01/J-02/J-03; fallback, not the preferred J-07 promotion)
  The exploration iterates ONLY this set — NEVER the full `factor × horizon × decile` cross-product.
  The developer may DROP a candidate only if infeasible on the committed seed, never ADD one. All
  three factor keys are confirmed valid (`config.yaml` factor_lab.factors; computed in `scoring.py`).
- **Run the multi-horizon staging exploration.** Add a NEW deterministic function in
  `app.engine.triad_scan` (optionally exposed as an MCP tool) that, for each pre-registered
  candidate, builds the cohort claim (selectors mirroring `/api/research/samples`) and calls
  `app.mcp.tools:verify_edge(ledger="staging", ledger_path=$STAGING_LEDGER_PATH)`, appending each
  referee verdict (holdout edge, block-bootstrap `p_value`, PASS/FAIL/INSUFFICIENT, `deflation`,
  `required_p`) to the staging ledger. `verify_edge` stays the SINGLE ledger writer; the scan stays
  READ-ONLY w.r.t. both ledgers and the snapshot DB.
- **Activate the online-FDR economy for staging.** Flip `evidence.fdr.enabled: true` in
  `config.yaml`. The honesty fence `use_fdr = (ledger == STAGING and fdr.enabled)` (already wired in
  `verify_edge`) keeps the canonical ledger strict Bonferroni and byte-identical; FDR stays fenced
  to staging only (it is weaker than family-wise control and MUST remain fenced).
- **Persist the populated staging ledger** to
  `runs/goal-session-mcp-loop/state/staging-ledger.jsonl` (does not exist yet — created on the first
  staging write; committed with the iteration) so iter-11's decomposer can read the recorded
  p-values and promote the winner.

## Agents Required
- developer: yes -- config edits, verify multi-horizon enumeration, the new staging-exploration function, run + persist the staging ledger, tests, dev handoff with per-candidate p-values
- backend-data: yes -- all work is backend certification-engine / data (config, triad_scan, referee / online-fdr wiring, ledger routing)
- frontend-ux: no -- zero `apps/frontend/**` diff; no UI, badge, `/evidence`, or nav change

(The pipeline also runs reviewer / QA / **auditor** automatically. The AUDITOR MUST run this
iteration — the missing audit was the recurring iter-3/4/5 gap — and verify the honesty fence +
canonical byte-identity. See Key Test Scenarios.)

## Frontend Present
Frontend Present: no

Backend-only certification-engine discovery. No `apps/frontend` diff, no UI/badge/route change, no
journey flip. Browser QA is N/A by design; J-01…J-06 non-regression is verified via the canonical
`GET /api/evidence` byte-identity path + the UNEDITED default-path unit suite (the iter-9 lesson) —
NOT browser pixels, NOT the dead `browser_checks_run` flag. (UI Evolution / Visual Requirements
sections intentionally omitted — no frontend this iteration.)

## Files to Create/Modify
- `/home/dennis-chan/Git/trendora/config.yaml` -- add `triad.horizons: [1,5,10,20,60]`; raise `triad.top_k`; set `triad.screen.haircut_coef`; add the pre-registered candidate set (config-backed, with rationales); flip `evidence.fdr.enabled: true`
- `/home/dennis-chan/Git/trendora/apps/backend/app/engine/triad_scan.py` -- NEW staging-exploration function (reads the pre-registered set, calls `verify_edge(ledger="staging")` per candidate); confirm `scan_factor_decile_cells` / `scan_product_triad` enumerate per `(factor,horizon,decile)` for all configured horizons. Scan stays read-only.
- `/home/dennis-chan/Git/trendora/project-extensions/proposer-guidance.md` -- mirror the pre-registered candidate set (new section) with the economic rationales
- `/home/dennis-chan/Git/trendora/runs/goal-session-mcp-loop/state/staging-ledger.jsonl` -- NEW; one referee verdict per candidate; committed with the iteration
- `/home/dennis-chan/Git/trendora/apps/backend/tests/test_triad_scan.py` -- multi-horizon enumeration (exact horizon set + per-horizon cell counts)
- `/home/dennis-chan/Git/trendora/apps/backend/tests/test_staging_ledger_routing.py` -- staging routing (append staging, never canonical; canonical divisor unchanged), honesty fence with `fdr.enabled=true`, INSUFFICIENT error path, deterministic per-candidate exploration verdicts
- `/home/dennis-chan/Git/trendora/apps/backend/tests/test_online_fdr.py` -- LORD++ level correctness (extend only if the exploration exercises new rejection ordinals)
- `/home/dennis-chan/Git/trendora/apps/backend/tests/test_config.py` -- update real-config assertions for `fdr.enabled=true` + new `triad.horizons` / candidate-set keys (LEGITIMATE change — enabling FDR is an explicit deliverable, NOT a default-path regression)
- `/home/dennis-chan/Git/trendora/docs/handoffs/goal-mcp-loop-iter-10-dev.md` -- NEW dev handoff; PER candidate: block-bootstrap `p_value` + whether it clears the divisor-5 bar (`p < 0.010`) — the explicit input to iter-11's promotion decision
- **DO NOT EDIT (editing = regression signal):** `test_referee.py`, `test_forward_walk.py`, `test_evidence.py` (default-path / frozen-golden reproduction)
- **DO NOT duplicate:** the blueprint iter-10 clarification is ALREADY present at `runs/goal-session-mcp-loop/state/blueprint.md` lines 171-193 (verify it's there; no nav-skeleton change ⇒ no re-approval)

## Key Test Scenarios
Phase is complete only when all pass; assert EXACT values and cover a failure path.
- **Multi-horizon enumeration:** `scan_factor_decile_cells` / `scan_product_triad` produce cells for every configured horizon — assert the exact horizon set `{1,5,10,20,60}` and the per-horizon cell counts.
- **Staging routing + isolation:** `verify_edge(ledger="staging")` appends to `staging-ledger.jsonl` and NEVER to canonical; `count_trials(canonical)` and the canonical Bonferroni divisor are unchanged by staging trials.
- **Online-FDR correctness + purity:** `online_fdr.test_level` returns the exact LORD++ levels for a known rejection-ordinal sequence (deterministic, no RNG/IO); FDR affects ONLY staging.
- **Honesty fence:** with `evidence.fdr.enabled=true`, a CANONICAL `certify_edge` / `verify_edge` reproduces `required_p = alpha_per_test / n_trials` (strict Bonferroni) byte-identically — canonical is never routed through FDR.
- **Default-path reproduction (regression proof):** `test_referee.py` / `test_forward_walk.py` / `test_evidence.py` stay UNEDITED and green (byte-identical canonical verdicts + frozen golden; `proven_signals == {leadership_score}`, the 4 canonical entries unchanged). Needing to edit them IS the regression signal.
- **No-lookahead per horizon:** at each of h1/h5/h10/h60 the cohort's forward returns come only from bars > as-of and the referee's sealed temporal holdout split is per-horizon correct.
- **Determinism:** the staging exploration against seed `20240601` persists one verdict per candidate; a re-run yields byte-identical verdicts.
- **Error path:** an infeasible candidate (a horizon lacking post-snapshot bars, or a cohort too thin for the block bootstrap) is recorded as `INSUFFICIENT` in staging — surfaced, not silently dropped and not crashing; an unrecognized ledger-routing value fails closed.
- **Canonical byte-identity:** `certified-claims.jsonl` git-UNMODIFIED; `GET /api/evidence` + `proven_signals` byte-identical; auditor confirms zero staging references reach `evidence.py` / the routers / `GET /api/evidence`.
- **Handoffs exist:** `docs/handoffs/goal-mcp-loop-iter-10-dev.md` (per-candidate `p_value` + clears-`p<0.010`) and `docs/handoffs/goal-mcp-loop-iter-10-audit.md` (honesty fence + canonical byte-identity verified).
- **NOT expected:** J-07 does NOT flip to passing (no UI is built) — it stays `unknown`. An absent J-07 badge is NOT a failure; the referee-scored staging candidates are the deliverable.

## Implementation Notes & Assumptions
- `verify_edge(session, claim, ledger_path, *, register_date, ledger="canonical")` already assembles
  cohort/control from the claim dict (`assemble_claim_observations`) and threads the economy. So the
  exploration builds a claim dict per candidate (e.g.
  `{"kind":"factor","factor":"vcp_contraction","slice_kind":"decile","decile":10,"horizon":10,"direction":"positive"}`)
  and passes `ledger="staging", ledger_path=$STAGING_LEDGER_PATH` — no need to duplicate
  `_assemble_cell_observations` (available if explicit observations are preferred).
- Pass a **deterministic** `register_date` per candidate so re-runs are byte-identical.
- The exploration is invoked directly (an entry function / test-invoked path), NOT through the
  post-decompose gate: this spec carries **NO `## Evidence Claim` block**, so the gate passes
  through (exit 0) and nothing can block the iteration or touch the canonical bar. (iter-11's
  promotion claim MUST set `"ledger":"canonical"` explicitly, or a winner is silently certified into
  staging.)
- Seed = `walk_forward.control_group.seed` = `20240601` (the `verify_edge` default).

## Out of Scope (excluded — no scope creep)
- Any canonical `## Evidence Claim` / write to `certified-claims.jsonl` (defer to iter-11; a blind canonical claim risks the iter-8 bar-tightening pitfall — ma_stack FAILED the referee and permanently tightened the bar).
- Any UI change for J-07 (no `/evidence` row, no factor-lab badge). Surfacing is iter-11.
- Multi-factor COMBINATION enumeration + `/research/factor-combination` (that is J-08).
- Re-proposing `ma_stack` / `hv` / `high_proximity` (blueprint iter-8 directive).
- Regime/sector cohort expansion, quantile spreads (D10−D1), scoped α-split families (goal.md defers to later phases).
- Touching / re-ordering the 4 existing canonical ledger entries or changing `proven_signals` (stays exactly `{leadership_score}`).
