# goal-mcp-loop-iter-10 Dev Handoff

**Phase:** goal-mcp-loop-iter-10
**Date:** 2026-07-01
**Agent:** developer
**Status:** complete

## What Was Built

Backend-only **Part B Phase 1** of goal.md's engineering direction: opened the certification engine's
scan aperture beyond the 20-day horizon and ran a PRE-REGISTERED candidate set through the referee into
the INTERNAL **staging** ledger under the online-FDR (LORD++) economy. **Discovery-first** — NO canonical
claim, NO UI, NO journey flip. It produces the referee-scored candidate list iter-11 promotes to surface J-07.

- **Multi-horizon aperture opened (config):** `config.triad.horizons: [1, 5, 10, 20, 60]`. Both
  `scan_factor_decile_cells` and `scan_product_triad` now enumerate one cell per `(factor, horizon, decile)`
  across every configured horizon (was the single default h20). Reuses `compute_factor_lab` + the
  already-present `walk_forward.horizons` forward-return data.
- **Multiple-testing haircut scaled:** `triad.top_k` raised 20 → 50 (screen more of the ~5× wider field);
  `triad.screen.haircut_coef` raised 0.001 → 0.0025 (the near-inert coefficient now yields a meaningful,
  batch-scaled edge floor). Both consumed verbatim from config; these affect only `scan_product_triad`'s
  cheap proposer screen — NOT the staging exploration (which uses the full referee).
- **Pre-registered candidate set (anti-data-mining keystone):** a FIXED, config-backed list
  (`config.triad.candidates`) of 4 multi-horizon single-factor hypotheses, each with an economic rationale,
  mirrored into `project-extensions/proposer-guidance.md`. The exploration iterates ONLY this set.
- **Multi-horizon staging exploration:** new deterministic `app.engine.triad_scan.explore_multi_horizon_staging`
  runs each candidate through `app.mcp.tools:verify_edge(ledger="staging")`, appending each referee verdict
  to the staging ledger. `verify_edge` stays the SOLE ledger writer; the function is fail-closed against ever
  touching the canonical ledger path.
- **Online-FDR economy activated for staging:** `config.evidence.fdr.enabled: true`. The honesty fence
  (`use_fdr = ledger == STAGING and evidence.fdr.enabled`, already wired in `verify_edge`) keeps the canonical
  `/evidence` bar strict Bonferroni and byte-identical.
- **Committed staging ledger:** `runs/goal-session-mcp-loop/state/staging-ledger.jsonl` (new, 4 verdicts).

## Per-candidate referee results (the explicit input to iter-11's promotion decision)

Run against the app DB (`apps/backend/data/trendora.db`, 1377 daily runs — the same DB the canonical ledger
and the goal-mode gate use), seed `20240601`, register_date `2026-07-01`. **Deterministic** — a re-run yields
byte-identical verdicts.

| # | Candidate (D10, positive) | Horizon | Status | block-bootstrap `p_value` | `required_p` (LORD++) | holdout_edge | holdout_dates | **clears `p < 0.010`?** | Signal-less? |
|---|---------------------------|---------|--------|---------------------------|-----------------------|--------------|---------------|-------------------------|--------------|
| 1 | `vcp_contraction` | **h10** | **FAIL** | **0.056972** | 0.010937 | +0.01161 | 281 | **NO** | yes |
| 2 | `vcp_contraction` | **h60** | **PASS** | **0.00049975** | 0.003608 | +0.08910 | 243 | **YES** | yes |
| 3 | `rs_spy_3m` | **h60** | **PASS** | **0.00049975** | 0.012823 | +0.21344 | 187 | **YES** | yes |
| 4 | `leadership_score` | **h60** | **PASS** | **0.00049975** | 0.026673 | +0.18487 | 283 | **YES** | no (score column) |

Reading for iter-11:
- **Three candidates clear the canonical divisor-5 bar (`p < 0.010`)**, at the block-bootstrap floor
  `p = 0.00049975` (= `1 / (2000 + 1)`). Two of them are **signal-less** (#2 `vcp_contraction` h60, #3
  `rs_spy_3m` h60) — either is a clean J-07 promotion (backs the factor lab only, never a `/stocks` badge).
- **#1 `vcp_contraction` h10 FAILED** honestly (`p ≈ 0.057`): the h20-proven edge does NOT already appear at
  a ~2-week hold. Do NOT promote it (would repeat the iter-8 `ma_stack` pitfall on the canonical bar).
- **#4 `leadership_score` h60** is the score-column ANCHOR (already in `proven_signals`) — the fallback, not
  the preferred promotion (iter-11 prefers a signal-less winner so J-01/J-02/J-03 are undisturbed).
- The **online-FDR economy is visibly working**: after the two h60 discoveries the bar *loosens*
  (`required_p`: 0.0036 → 0.0128 → 0.0267) — LORD++ wealth replenishing (Bonferroni could only tighten).
  iter-11's promotion claim MUST set `"ledger":"canonical"` explicitly (an omitted key defaults to staging).

## Files Changed

- `config.yaml` — activated `evidence.fdr.enabled: true` (staging only, canonical fenced); opened
  `triad.horizons: [1,5,10,20,60]`; raised `triad.top_k: 50` + `triad.screen.haircut_coef: 0.0025`; added the
  pre-registered `triad.candidates` set (4 hypotheses, each with an economic rationale).
- `apps/backend/app/engine/triad_scan.py` — new `explore_multi_horizon_staging` (+ `_staging_candidates`,
  `_resolve_repo_path`, `DEFAULT_STAGING_REGISTER_DATE`); `scan_factor_decile_cells` now honors the configured
  `triad.horizons` aperture when no explicit horizons are passed.
- `project-extensions/proposer-guidance.md` — new §4.1 mirroring the pre-registered candidate set + rationales
  + the iter-10 referee outcome (which cleared, which failed; iter-11 promotion guidance).
- `runs/goal-session-mcp-loop/state/staging-ledger.jsonl` — NEW; one referee verdict per candidate (committed).
- `apps/backend/tests/test_triad_scan.py` — multi-horizon enumeration (exact horizon set {1,5,10,20,60} +
  per-horizon cell counts 22 ⇒ 110 total; explicit-horizons override preserved).
- `apps/backend/tests/test_staging_ledger_routing.py` — staging exploration determinism + staging-isolation;
  the thin-fixture INSUFFICIENT path (with `deflation == "lord++"` proving FDR active); the fail-closed
  canonical-path guard; the committed-ledger frozen golden (statuses, LORD++ `required_p`, rejection offsets,
  canonical byte-identity).
- `apps/backend/tests/test_online_fdr.py` — frozen LORD++ levels for the staging rejection sequence
  (ordinals (1,[]),(2,[]),(3,[2]),(4,[2,3])) matching the committed ledger's `required_p`.
- `apps/backend/tests/test_config.py` — real-config now asserts `fdr.enabled is True` (renamed
  `test_real_config_activates_fdr_for_staging_iter10`) + new `triad.horizons`/`top_k`/`haircut_coef`/candidate-set
  assertions. (The CODE default stays off — `test_fdr_and_staging_default_when_omitted` unchanged.)
- **NOT edited (regression proof):** `test_referee.py`, `test_forward_walk.py`, `test_evidence.py` — the
  default-path / frozen-golden reproduction suites; all green + byte-identical.

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/test_triad_scan.py tests/test_staging_ledger_routing.py tests/test_online_fdr.py tests/test_config.py tests/test_triad_screen.py tests/test_referee.py tests/test_forward_walk.py tests/test_evidence.py -q`
Result: 129 passed (the DO-NOT-EDIT default-path suites — `test_referee.py` / `test_forward_walk.py` /
`test_evidence.py` — stayed UNEDITED and green: canonical `certified-claims.jsonl` git-unmodified, `proven_signals == {leadership_score}`).

## Known Issues

- **Reproducibility of the committed staging ledger** requires the daily app DB
  (`apps/backend/data/trendora.db`, 1377 runs — the same provenance as the canonical ledger). The quarterly
  test fixture (`loaded_engine`, ~11 runs) has too few sealed-holdout dates, so on it every candidate is
  honestly recorded as INSUFFICIENT (this is exercised as the error-path test). The committed ledger is
  therefore treated as a frozen artifact (exactly like the committed `certified-claims.jsonl`), and a
  `test_committed_staging_ledger_is_the_frozen_multi_horizon_discovery` frozen-golden test anchors its
  contents + the canonical byte-identity. Regeneration: run `explore_multi_horizon_staging(session, reset=True)`
  against `trendora.db` — deterministic, byte-identical.
- J-07 does NOT flip to passing this iteration (no UI is built) — it stays `unknown` by design. The
  referee-scored staging candidates are the deliverable; iter-11 surfaces the winner.
