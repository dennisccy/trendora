# goal-mcp-loop-iter-12 Execution Plan

**Type:** backend-only INTERNAL enablement (mirrors iter-9/iter-10). No user-facing change.
**Goal alignment:** completes the deferred "combinations" half of `docs/goal.md` Part B Phase 1 —
opens the certification aperture to 2-factor composites so iter-13 can promote a winner and surface
**J-08**. J-08 is NOT flipped here; it stays `unknown`.

## What to Build
- Register a NEW `config.triad.combination_candidates` block in the repo-root `config.yaml`
  (parallel to the existing single-factor `triad.candidates` at ~line 1058) holding a FIXED,
  PRE-REGISTERED set of EXACTLY THREE 2-factor combination hypotheses — each with two `condition`
  legs (`<factor_key>:<side>:<quantile_key>`), `horizon: 20`, `direction: positive`, composite
  cohort, and a one-line economic rationale. Register exactly these (side matches each factor's
  catalog direction — top = higher_better, bottom = lower_better):
  1. `rs_spy_3m:top:quintile` + `atr_pct:bottom:tertile` — momentum leadership that is NOT
     volatile/extended (identical to the shipped `research.factor_lab.combination.default_conditions`
     and the J-08 example).
  2. `leadership_score:top:quintile` + `atr_pct:bottom:tertile` — the system's strongest signal
     concentrated to its orderly, low-ATR members.
  3. `rs_spy_3m:top:quintile` + `high_proximity:top:tertile` — RS leaders that are ALSO near their
     52-week high (leaders in position / breakout-ready).
- Mirror the SAME three pairs VERBATIM (each pair + horizon + rationale) into
  `project-extensions/proposer-guidance.md` as a new §4.2 "Pre-registered 2-factor combination
  staging candidate set" — the anti-data-mining keystone (iterate ONLY this fixed set, NEVER the
  full `factor × pair × horizon` cross-product).
- Add a combination staging explorer to `apps/backend/app/engine/triad_scan.py` — a sibling to the
  existing `_staging_candidates` / `explore_multi_horizon_staging` (e.g. `_combination_staging_candidates(cfg)`
  + `explore_combination_staging(...)`). It reads the new config block VERBATIM, projects each entry
  into a claim `{"kind":"combination","cohort":"composite","horizon":<h>,"direction":"positive","condition":[leg1,leg2]}`,
  and certifies each through the referee via `app.mcp.tools:verify_edge(ledger="staging")` under the
  online-FDR (LORD++) economy — APPENDING one verdict per candidate to the INTERNAL staging ledger.
- Extend the existing fail-closed guard (abspath equality vs `cfg.evidence.ledger_path`, raising
  `ValueError`) to cover the combination explorer, so it can NEVER write the canonical ledger.
- Run the explorer to APPEND the 3 combination verdicts to the committed staging ledger
  (`runs/goal-session-mcp-loop/state/staging-ledger.jsonl`: 4 single-factor → 7 total), each
  recording `status`, block-bootstrap `p_value`, `holdout_edge`, `control_excess`, `cohort_n`,
  `control_n`, `deflation`, `required_p`, `horizon`, and the `condition` legs (the fields iter-13
  reads to pick a promotable winner whose raw p clears required_p ≈ 0.00833 with margin).
- REUSE the referee cert path UNCHANGED: `drill_samples` (tools.py 332–346) already splits `condition`
  legs and `_CLAIM_SELECTOR_KEYS` already forwards `condition`+`cohort`; `samples.py` already resolves
  the `composite` cohort. Do NOT modify `verify_edge`'s cert logic — `verify_edge` stays the SOLE
  ledger writer.

## Agents Required
- backend-data: yes — implements the config candidate set, the `triad_scan.py` combination explorer,
  the proposer-guidance §4.2 mirror, the backend tests, and runs the explorer to append the 3 staging
  verdicts.
- frontend-ux: no — no user-facing change this iteration (surfacing J-08 is iter-13).
- developer: yes — this project's single implementer agent performs the backend-data work above.

## Frontend Present

Frontend Present: no

## Files to Create/Modify
- `config.yaml` (repo root, ~line 1058) — add `triad.combination_candidates` (3 pairs + horizon +
  direction + rationale), parallel to `triad.candidates`.
- `apps/backend/app/engine/triad_scan.py` — add `_combination_staging_candidates` +
  `explore_combination_staging` (sibling to the single-factor pair); extend the canonical-path
  fail-closed guard to the combination explorer.
- `project-extensions/proposer-guidance.md` — add §4.2 (verbatim mirror of the 3 combination
  candidates + economic rationale).
- `runs/goal-session-mcp-loop/state/staging-ledger.jsonl` — append 3 combination verdicts (runtime
  output of the explorer; 4 → 7 entries). APPEND — do NOT reset/truncate (preserve iter-10's 4
  single-factor entries).
- `apps/backend/tests/test_staging_ledger_routing.py` — add combination-exploration tests (claim
  shape, staging-only, canonical-refusal `ValueError`, determinism, error cases); UPDATE
  `test_committed_staging_ledger_is_the_frozen_multi_horizon_discovery` to the new 7-entry reality
  (or add a companion asserting the 3 appended combination entries).
- `docs/handoffs/goal-mcp-loop-iter-12-dev.md` — dev handoff.

## UI Evolution
N/A — Frontend Present: no. Internal discovery/enablement only; zero user-visible impact (never
served by `GET /api/evidence`, never displayed). J-08 is surfaced in iter-13.

## Visual Requirements
N/A — Frontend Present: no.

## Key Test Scenarios
- **Claim shape + routing:** `explore_combination_staging` projects each `config.triad.combination_candidates`
  entry into the exact `{kind:"combination", cohort:"composite", horizon:20, direction:"positive",
  condition:[leg1,leg2]}` claim and certifies via `verify_edge(ledger="staging")`; verdicts land in
  the STAGING file ONLY (canonical untouched).
- **Fail-closed:** the guard raises `ValueError` when the combination explorer is pointed at the
  canonical ledger path (same as the single-factor explorer).
- **Determinism:** a `reset=True` re-run against a controlled starting ledger state yields
  byte-identical combination verdicts (referee seed fixed; PURE given DB + config + `register_date`).
- **Error cases (raise `ValueError`, never silently skip):** unknown factor key; malformed
  `condition` string (not `<factor>:<side>:<quantile>`); out-of-range / invalid quantile; a
  misrouted ledger target is fail-closed.
- **Byte-identity / no canonical drift (the regression proof for a shared-cert-engine change):**
  `git diff HEAD` on `certified-claims.jsonl` (5 entries) is EMPTY; `GET /api/evidence` +
  `proven_signals` (`{leadership_score}`) byte-identical; the DO-NOT-EDIT suites `test_referee.py`,
  `test_forward_walk.py`, `test_evidence.py` are UNEDITED and green.
- **Honesty fence unchanged:** `use_fdr = ledger == LEDGER_STAGING and fdr_cfg.enabled` — canonical
  stays strict Bonferroni; the combination staging exploration lights NO badge and is never served.
- **J-08 remains `unknown`** — NOT claimed passing (enablement/discovery only; only the goal-evaluator
  sets journey status). J-01..J-07 remain green via the byte-identity / frozen-golden path (no browser).

## Notes, Assumptions & Landmines
- **No `## Evidence Claim` this iteration.** The exploration runs in built code via
  `verify_edge(ledger="staging")`, not via a spec-declared claim, and writes NO canonical entry — so
  the post-decompose gate passes automatically (goal.md loop mechanics: pure discovery/enablement
  needs no Evidence Claim). Adding one would be wrong (an omitted `"ledger"` key defaults to staging,
  but there is nothing to certify at the spec level here).
- **APPEND, don't reset (economy continuity).** The 3 combinations run as trials #5–7 in the
  continuous online-FDR economy that already counts iter-10's 4 single-factor trials; their recorded
  `required_p` reflects that. iter-13 reads the RAW block-bootstrap `p_value` (economy-independent) to
  gate canonical promotion, so this is safe. The `reset=True` determinism test operates on an
  isolated/temp ledger, not the committed file.
- **Expected (NOT a regression): the staging golden test changes.**
  `test_committed_staging_ledger_is_the_frozen_multi_horizon_discovery` currently pins the 4-entry
  staging ledger and MUST be updated to the 7-entry reality — this is an editable staging test, not
  one of the three DO-NOT-EDIT canonical suites. Reviewer/QA must distinguish this expected staging
  golden-value update from a canonical regression (mirrors how iter-11 re-pinned golden values).
  `test_online_fdr.py::test_test_level_matches_iter10_staging_exploration_sequence` pins the iter-10
  trials #1–4 sequence, which is UNCHANGED by appending #5–7 — verify it still passes; do not edit it
  unless the append demonstrably shifts trials 1–4 (it should not).
- **Blueprint conformance — already satisfied.** The additive iter-12 clarification is ALREADY present
  in `runs/goal-session-mcp-loop/state/blueprint.md` (Data Contract, iter-12 paragraph) documenting
  the internal-only combination staging machinery (no new displayed value, no new endpoint, no
  nav-skeleton change, canonical byte-identical). No blueprint edit is required — verify it is present.
- **No architecture docs to update.** `docs/architecture/` does not exist; the design overview is
  `docs/trendora-design.md` (no triad/referee/staging spec there — those live inline in `config.yaml`
  comments and per-iteration handoffs).
- **Config block shape (assumption).** Suggest each `combination_candidates` entry mirror the claim
  form — `condition: ["<leg1>", "<leg2>"]`, `horizon: 20`, `direction: positive`, `rationale: "..."` —
  with `cohort: "composite"` fixed in the projection code (all registered combinations are composite).
  The developer should keep the reader (`_combination_staging_candidates`) config-VERBATIM with no
  cohort/horizon/leg literal enumerated in code (the anti-data-mining keystone).
- **Excluded (out of scope, per spec — do NOT implement):** any canonical `certified-claims.jsonl`
  write or `"ledger":"canonical"` claim; any `/evidence` row, `/research/factor-combination` "Proven"
  badge, or read-side combination matcher; any `/stocks` badge change; the full cross-product;
  `ma_stack` as a leg (a closed referee FAIL); any new economy/endpoint/deflation policy. All of the
  above are iter-13 or explicitly forbidden.
- **Scope check:** fully aligned with `docs/goal.md` Part B Phase 1 (combinations half) and J-08
  enablement. No scope creep detected; no contradiction with the project goal or the seven anti-goals
  (FDR stays fenced to staging; canonical stays Bonferroni; deterministic; no secrets; no
  return/price/buy-sell language).
