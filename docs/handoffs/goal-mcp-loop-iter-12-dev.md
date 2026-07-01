# goal-mcp-loop-iter-12 Dev Handoff

**Phase:** goal-mcp-loop-iter-12
**Date:** 2026-07-01
**Agent:** developer
**Status:** complete

## What Was Built

Backend-only INTERNAL enablement (mirrors iter-9/iter-10) — completes the deferred "combinations" half of
`docs/goal.md` Part B Phase 1. Opens the certification aperture to 2-factor **composite** cohorts so iter-13
can promote a winner and surface **J-08**. No user-facing change; J-08 stays `unknown` this iteration.

- **Pre-registered 2-factor combination candidate set** — a NEW `config.triad.combination_candidates` block
  (parallel to the single-factor `triad.candidates`) holding a FIXED set of EXACTLY THREE composite-cohort
  hypotheses (each two `condition` legs `<factor>:<side>:<quantile>`, `horizon: 20`, `direction: positive`,
  plus a one-line economic rationale). Registered:
  1. `rs_spy_3m:top:quintile` + `atr_pct:bottom:tertile` (the shipped `default_conditions` / J-08 example)
  2. `leadership_score:top:quintile` + `atr_pct:bottom:tertile`
  3. `rs_spy_3m:top:quintile` + `high_proximity:top:tertile`
- **Verbatim mirror** of the same three pairs (each pair + horizon + rationale) into
  `project-extensions/proposer-guidance.md` §4.2 — the anti-data-mining keystone (iterate ONLY this fixed
  set, NEVER the full `factor × pair × horizon` cross-product).
- **Combination staging explorer** — `app.engine.triad_scan.explore_combination_staging` +
  `_combination_staging_candidates` (a sibling to `explore_multi_horizon_staging`/`_staging_candidates`).
  It reads `config.triad.combination_candidates` VERBATIM, projects each into a
  `{kind:"combination", cohort:"composite", horizon, direction, condition:[leg1, leg2]}` claim, and certifies
  each through the referee via `app.mcp.tools:verify_edge(ledger="staging")` under the online-FDR (LORD++)
  economy — appending ONE verdict per candidate to the INTERNAL staging ledger. The referee cert path is
  REUSED UNCHANGED (`assemble_claim_observations`→`drill_samples` already parse the `condition` legs and
  resolve the `composite` cohort; `condition`/`cohort` are already in `_CLAIM_SELECTOR_KEYS`). `verify_edge`
  is unmodified and stays the SOLE ledger writer.
- **Fail-closed guard extended** — the combination explorer REFUSES (raises `ValueError`) if pointed at the
  canonical `evidence.ledger_path`, exactly like the single-factor explorer. It is fenced to `ledger="staging"`
  only.
- **Ran the explorer against the real production DB** (`apps/backend/data/trendora.db`, 1377 runs) to APPEND
  the 3 combination verdicts to the committed staging ledger (4 → 7 entries). Recorded outcome:
  - #5 `rs_spy_3m + atr_pct` — **FAIL** (p≈0.727, holdout edge −0.0046: the low-ATR filter HURTS the momentum
    edge at h20)
  - #6 `leadership_score + atr_pct` — **FAIL** (p≈0.791, holdout edge −0.0067)
  - #7 `rs_spy_3m + high_proximity` — **PASS** (p≈0.0009995, holdout edge +0.0469), and its RAW block-bootstrap
    p clears even the canonical divisor-6 bar (`p < 0.05/6 ≈ 0.00833`) with margin — the real recorded basis
    iter-13 promotes to surface J-08.

## Files Changed

- `config.yaml` — added the `triad.combination_candidates` block (3 pairs + horizon + direction + rationale).
- `apps/backend/app/engine/triad_scan.py` — added `_combination_staging_candidates(cfg)` +
  `explore_combination_staging(...)` (sibling to the single-factor pair; fail-closed canonical-path guard).
  Added `KIND_COMBINATION` to the `app.engine.samples` import. `explore_multi_horizon_staging` left UNTOUCHED
  (deliberate — it writes the byte-frozen entries #1-4).
- `project-extensions/proposer-guidance.md` — added §4.2 (verbatim mirror of the 3 combination candidates +
  economic rationale + the iter-13 promotion guidance).
- `runs/goal-session-mcp-loop/state/staging-ledger.jsonl` — APPENDED 3 combination verdicts (4 → 7; the first
  4 single-factor lines are byte-identical, `git diff` shows +3/-0).
- `apps/backend/tests/test_staging_ledger_routing.py` — 4 new combination-explorer tests (claim shape +
  staging-only, determinism, canonical-refusal `ValueError`, malformed-candidate error cases); UPDATED the
  frozen-golden `test_committed_staging_ledger_is_the_frozen_multi_horizon_discovery` to the 7-entry reality
  (single-factor prefix unchanged + combination suffix + updated aggregates).

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/test_staging_ledger_routing.py tests/test_online_fdr.py tests/test_triad_scan.py tests/test_config.py tests/test_triad_screen.py tests/test_referee.py tests/test_forward_walk.py tests/test_evidence.py -q`

Result: **134 passed** (0 failed) in ~156s.

Verification highlights:
- The four NEW combination-explorer tests pass on the thin test fixture.
- The frozen-golden staging test passes against the committed 7-entry ledger (exact required_p levels for
  trials 5-7, statuses `[FAIL, FAIL, PASS]`, winner p clears divisor-6, `rejection_offsets == [2,3,4,7]`,
  `count_trials == 7`).
- **DO-NOT-EDIT suites UNEDITED and green:** `git diff HEAD` on `test_referee.py`, `test_forward_walk.py`,
  `test_evidence.py` is EMPTY; all pass.
- `test_online_fdr.py::test_test_level_matches_iter10_staging_exploration_sequence` still green (trials #1-4
  unchanged by appending #5-7).
- **Canonical byte-identity:** `git diff HEAD` on `certified-claims.jsonl` is EMPTY (5 entries unchanged);
  `app/engine/evidence.py`, `app/api/evidence.py`, `app/mcp/tools.py`, `app/engine/referee.py`,
  `app/engine/online_fdr.py` are UNTOUCHED — so `GET /api/evidence` + `proven_signals` (`{leadership_score}`)
  serve byte-identical output (same input file + unchanged read path).
- Anti-goal scans of the diff clean: no buy/sell/price-target/predict/return-promise language; no secrets.
- Import sanity: `app.config`, `app.engine.{samples,referee,online_fdr,evidence,triad_scan}`, `app.mcp.tools`,
  `app.api.evidence` all import cleanly (no import-time breakage).

## Reproducibility

The committed 7-entry staging ledger is a frozen artifact (like `certified-claims.jsonl`). To regenerate
byte-identically against the real DB: `explore_multi_horizon_staging(session, reset=True)` (rebuilds the 4
single-factor entries #1-4) followed by `explore_combination_staging(session)` (appends #5-7). Verified this
iteration: the regenerated entries #1-4 are byte-identical to the committed file before the append.

## Known Issues

- **The two "obvious" anchor combinations FAIL out-of-sample at h20** (negative holdout edge). This is the
  honest referee refusing a thin/weak composite (anti-goal #1/#4 upheld), NOT a defect. Only combination #3
  (`rs_spy_3m` leaders that are ALSO near their 52-week high) survives — and it clears the canonical
  divisor-6 bar with margin, so iter-13 has a real promotable winner. If iter-13 finds none cleared the bar,
  the correct outcome would be to honestly report it (do NOT force an overfit promotion).
- **Reproducing the committed ledger requires the daily app DB** (`apps/backend/data/trendora.db`, 1377 runs).
  The thin quarterly test fixture (`loaded_engine`, ~11 runs) has too few sealed-holdout dates, so on it every
  candidate records INSUFFICIENT — which is why the committed ledger is anchored by a frozen-golden test
  rather than recomputed in a fixture test (mirrors iter-10).
- **J-08 does NOT flip to passing this iteration** — it stays `unknown` by design (no UI built; no canonical
  claim). Surfacing J-08 on `/research/factor-combination` + `/evidence` is iter-13. (Only the goal-evaluator
  sets journey status.)
- No `## Evidence Claim` was declared this iteration (pure discovery/enablement runs in built code via
  `verify_edge(ledger="staging")`, writes NO canonical entry) — the post-decompose gate passes automatically.
