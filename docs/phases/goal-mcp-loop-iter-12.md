# Goal Iteration 12 — Explore the pre-registered 2-factor combination candidate set into the STAGING ledger (J-08 enablement)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** mcp-loop
- **Iteration:** 12
- **Mode:** next
- **Depth:** full
- **Frontend Present:** no
- **Target journeys:** J-08 (enablement — does NOT flip this iteration; stays `unknown`; surfaced in iter-13)
- **Required-still-passing journeys:** J-01, J-02, J-03, J-04, J-05, J-06, J-07 (re-verified via the byte-identity / frozen-golden path — see DoD; no fresh browser lane, Frontend Present: no)
- **Anti-goal reminders (verbatim from `docs/goal.md`):**
  - A score, ranking, or "edge" MUST NOT be presented as proven/confident unless it is backed by a **passing certified-claim entry** in the evidence ledger (out-of-sample, control-beating). Unbacked values MUST render a "not yet proven" state. *(critical)*
  - **Decision-quality only:** never present return promises, price targets, "buy/sell" signals, or alpha claims; never place or simulate orders. *(critical)*
  - A journey passes ONLY if the **displayed numbers are correct** — they match the engine's computation for the same as-of date — not merely that the page renders. *(critical)*
  - **No overfit edges:** any pattern surfaced as "proven" must have survived the referee (sealed out-of-sample holdout + controls + multiple-testing correction), never in-sample fit alone. *(critical)*
  - **Preserve determinism and no-lookahead:** scoring uses bars ≤ as-of; forward returns use bars > as-of; never introduce lookahead anywhere. *(critical)*
  - No iteration ships if its evidence-derived claims (if any) lack a passing referee verdict from the post-decompose gate. *(critical)*
  - No hard-coded credentials, API keys, or tokens in source files. *(critical)*

## GOAL

Run a FIXED, pre-registered set of 2-factor **combination** hypotheses through the referee into the INTERNAL **staging** ledger (online-FDR economy), recording each composite cohort's block-bootstrap p-value — so iter-13 has a real, recorded basis on which to safely promote ONE winner to the canonical ledger and surface **J-08**. No user-facing change this iteration.

## BACKGROUND

J-08 is the sole remaining Must-have journey; it needs a curated 2-factor composite promoted to the canonical ledger and surfaced on `/research/factor-combination` + `/evidence`. The referee cert path **already** certifies a `kind:combination` claim (`assemble_claim_observations`→`drill_samples` parse the `condition` legs; `condition`/`cohort` are in `_CLAIM_SELECTOR_KEYS`), and the combination lab compute (`compute_factor_combination`) and route (`/research/factor-combination`) already exist. But **no combination has ever been run through the referee**: `config.triad.candidates`, `_staging_candidates`, and `explore_multi_horizon_staging` are single-factor-only (the staging ledger holds just the 4 single-factor multi-horizon entries from iter-10), and `proposer-guidance.md` §4.1 registers only single-factor candidates. So there is **no recorded staging p-value** for any combination.

The prior evaluator recommended "iter-12 (FULL) — promote a combination whose recorded raw p clears the divisor-6 bar (required_p ≈ 0.00833) with margin." That precondition cannot be met yet — nothing combination-shaped has a recorded p. A blind canonical combination submission is exactly the iter-8 `ma_stack` disaster (a FAIL permanently tightens the canonical Bonferroni bar AND blocks the iteration) and violates the iter-10 lesson ("promote only a candidate whose recorded raw p already clears required_p"). This iteration therefore performs the deferred **"combinations" half of goal.md Part B Phase 1** — build the economy/aperture, explore into staging — and iter-13 promotes the winner + surfaces J-08. This mirrors the proven iter-10 (discover into staging) → iter-11 (promote + surface J-07) arc, and respects goal.md's directive: "build the economy first, then widen the scan."

Lessons applied (see NOTES): iter-9 (byte-identity regression proof for a shared-engine change), iter-10 (record raw p; never blind-promote to canonical), iter-8 (never re-propose a closed FAIL — `ma_stack` excluded), and the anti-data-mining keystone (a fixed pre-registered set, never the cross-product).

## IN SCOPE

### Backend
- [ ] Register a **PRE-REGISTERED 2-factor combination candidate set** in a NEW config block `config.triad.combination_candidates` (parallel to the existing single-factor `config.triad.candidates`). Each entry carries two `condition` legs (`<factor_key>:<side>:<quantile_key>`), a `horizon`, `direction`, and a one-line **economic rationale**. Register exactly these three (all `direction: positive`, composite cohort, horizon 20 — the J-08 target horizon), each leg's `side` matching its factor-catalog `direction` (top = higher_better, bottom = lower_better):
  1. **`rs_spy_3m:top:quintile` + `atr_pct:bottom:tertile`** — momentum leadership that is NOT volatile/extended. *Anchor:* identical to the shipped `research.factor_lab.combination.default_conditions` and to the J-08 example; both legs individually evidenced (rs_spy_3m PASSED strongly OOS at h60; low-ATR% is the risk-factor low-volatility/quality filter). Signal-less composite → backs the combination lab only.
  2. **`leadership_score:top:quintile` + `atr_pct:bottom:tertile`** — the composite Leadership score concentrated to its low-volatility members; asks whether the system's strongest signal (p-floor solo) is even cleaner filtered to orderly, low-ATR names.
  3. **`rs_spy_3m:top:quintile` + `high_proximity:top:tertile`** — relative-strength leaders that are ALSO near their 52-week high (leaders in position / breakout-ready).
- [ ] Mirror the same set VERBATIM (each pair + horizon + rationale) into `project-extensions/proposer-guidance.md` as a new **§4.2 "Pre-registered 2-factor combination staging candidate set"** — the anti-data-mining keystone: the exploration iterates ONLY this fixed set, NEVER the full `factor × pair × horizon` cross-product.
- [ ] Add a **combination staging explorer** to `apps/backend/app/engine/triad_scan.py` (a sibling to `_staging_candidates`/`explore_multi_horizon_staging` — e.g. `_combination_staging_candidates(cfg)` + `explore_combination_staging(...)`, or extend the existing pair). It reads `config.triad.combination_candidates` VERBATIM, projects each into a claim `{"kind":"combination","cohort":"composite","horizon":<h>,"direction":"positive","condition":[<leg1>,<leg2>]}`, and certifies each through the referee via `app.mcp.tools:verify_edge(ledger="staging")` under the online-FDR (LORD++) economy — appending ONE verdict per candidate to the INTERNAL staging ledger (`runs/goal-session-mcp-loop/state/staging-ledger.jsonl`). REUSE the existing referee path (`assemble_claim_observations`/`drill_samples` already handle `kind:combination` — do NOT modify `verify_edge`'s cert logic). Keep `verify_edge` the SOLE ledger writer; keep the fail-closed guard that REFUSES to point the exploration at the canonical `evidence.ledger_path` (extend it to cover the combination explorer too).
- [ ] Ensure each recorded staging verdict carries the fields iter-13 will read to choose a promotable winner: `status`, block-bootstrap `p_value`, `holdout_edge`, `control_excess`, `cohort_n`, `control_n`, `deflation`, `required_p`, `horizon`, and the `condition` legs. (These already flow from `verify_edge`; the DoD asserts they are present for the combination cohort.)
- [ ] Reuse the existing FDR staging config (`evidence.fdr.enabled`, already activated in iter-10) and `evidence.staging_ledger_path`. No new economy, no new endpoint.

### Frontend (if applicable)
- None. Frontend Present: **no**. The staging exploration is INTERNAL-only — never served by `GET /api/evidence`, never displayed. (Surfacing J-08 on `/research/factor-combination` + `/evidence` is iter-13.)

### New user-facing capability
None this iteration. Internal discovery/enablement only (mirrors iter-9/iter-10). J-08 is surfaced in iter-13.

### New information displayed
None (the combination staging ledger is internal-only; no page reads it).

### New user actions
None.

### UI surface changes
None.

### Product surface delta
None visible to the user. Internally, the certification engine's aperture widens to 2-factor composites so a future iteration can surface a combination edge — completing the deferred "combinations" half of goal.md Part B Phase 1.

### Blueprint conformance
No new surfaces. J-08's canonical home is already registered in the blueprint Information Architecture (`/research/factor-combination` composite-cohort "Proven" badge + combination claim row on `/evidence`, both existing routes) — no nav-skeleton change. An additive **iter-12 clarification** is added to the blueprint Data Contract documenting that the combination staging exploration is internal-only machinery with NO new displayed value and NO new serving endpoint (mirrors the iter-9/iter-10 clarifications).

### Data-contract additions
**None.** The combination staging exploration introduces **no new displayed value and no new serving endpoint** — the staging ledger is internal-only (never read by any page, never served, never displayed). The canonical evidence-status contract value (`certified-claims.jsonl` → `GET /api/evidence` → `proven_signals`) stays BYTE-IDENTICAL. Do not add a second computation or endpoint for evidence status; the referee (`certify_edge` via `verify_edge`) remains the single computing source and the SOLE ledger writer.

## OUT OF SCOPE

- Any canonical `certified-claims.jsonl` write, and any `## Evidence Claim` carrying `"ledger":"canonical"`. **No promotion this iteration** — a blind canonical combination submission risks a permanent divisor-7 bar-tightening FAIL and blocks the iteration (iter-8/iter-10 lesson). Promotion waits for a recorded staging p (iter-13).
- Any `/evidence` combination claim row, any `/research/factor-combination` "Proven" badge, any read-side combination evidence matcher (`resolveCohortEvidence` combination branch), any `claimSurface` combination linkback — all iter-13.
- Any change to the canonical evidence-status contract value, `GET /api/evidence`, `proven_signals` (`{leadership_score}`), or the five existing canonical ledger entries — they MUST stay byte-identical.
- Any `/stocks` inline score-badge change (combination composites are signal-less; J-01/J-02/J-03 unaffected).
- The full `factor × pair × horizon` cross-product — ONLY the fixed pre-registered set of 3 runs (anti-data-mining keystone).
- `ma_stack` as a combination leg (a closed referee FAIL, iter-8) and any ad-hoc / data-mined pair not in the registered set.
- Widening `walk_forward`/regime/sector/score engines, or any new deflation policy (the online-FDR economy already exists from iter-9/iter-10).

## DEFINITION OF DONE

- [ ] The pre-registered 2-factor combination candidate set (the three pairs above) is registered in `config.triad.combination_candidates` AND mirrored VERBATIM into `project-extensions/proposer-guidance.md` §4.2, each pair carrying its economic rationale.
- [ ] `explore_combination_staging` (or the extended explorer) certifies each registered combination through the referee via `verify_edge(ledger="staging")` and appends ONE verdict per candidate to `runs/goal-session-mcp-loop/state/staging-ledger.jsonl`, each recording `status`, block-bootstrap `p_value`, `holdout_edge`, `control_excess`, `cohort_n`, `control_n`, `deflation`, `required_p`, `horizon`, and the `condition` legs (the data iter-13 reads to pick a promotable winner whose raw p clears required_p ≈ 0.00833 with margin).
- [ ] **J-08 remains `unknown`** — NOT claimed passing. This iteration is enablement/discovery only; surfacing is iter-13. (Only the goal-evaluator sets journey status.)
- [ ] Required-still-passing J-01..J-07 remain green, verified via the **byte-identity / frozen-golden path** (no fresh browser lane): `git diff HEAD` on `certified-claims.jsonl` is EMPTY (the five canonical entries byte-identical); `GET /api/evidence` + `proven_signals` byte-identical; the DO-NOT-EDIT default-path suites (`test_referee.py`, `test_forward_walk.py`, `test_evidence.py`) are UNEDITED and green (an edited expectation would itself be the regression signal — iter-9 lesson).
- [ ] The honesty fence holds unchanged: `use_fdr = (ledger == LEDGER_STAGING and evidence.fdr.enabled)` — canonical certification stays strict Bonferroni; the combination staging exploration lights NO badge and is never served (anti-goal #1/#4: FDR is weaker than family-wise control and is FENCED to staging).
- [ ] No anti-goal violation introduced (all seven upheld; `anti_goal_violations` stays `[]`). Secret scan + buy/sell/price-target/predict language scan of the diff = clean.
- [ ] Unit tests pass; no regressions (see TESTING REQUIREMENTS).
- [ ] Dev handoff written at `docs/handoffs/goal-mcp-loop-iter-12-dev.md`.

## TESTING REQUIREMENTS

- **Browser:** none. Frontend Present: `no` — there is no user-facing change; the browser QA lane is correctly N/A this iteration (mirrors iter-9/iter-10). Do NOT let an all-SKIP browser report be read as a verification gap: this iteration's DoD is byte-identity + unit tests, not journey pixels.
- **Unit/integration (backend):**
  - `explore_combination_staging` projects each `config.triad.combination_candidates` entry into the correct `{kind:"combination", cohort:"composite", horizon, direction, condition:[leg1,leg2]}` claim and certifies it via `verify_edge(ledger="staging")` — assert exact claim shape and that verdicts land in the STAGING file only.
  - The fail-closed guard REFUSES to run the combination exploration against the canonical ledger path (`ValueError`), same as the single-factor explorer.
  - **Determinism:** a `reset=True` re-run yields byte-identical staging verdicts (referee seed fixed; PURE given DB + config + `register_date`).
  - **Frozen-golden (no canonical drift):** the existing canonical test still asserts `certified-claims.jsonl` (five entries) + `proven_signals` are byte-identical; `test_referee.py`/`test_forward_walk.py`/`test_evidence.py` are UNEDITED and green.
- **Error cases:** an unknown factor key, a malformed `condition` string (not `<factor>:<side>:<quantile>`), or an out-of-range/invalid quantile in a combination candidate raises `ValueError` (surfaced loudly, never silently skipped); an unrecognized or misrouted ledger target is fail-closed (blocks, never a silent canonical write).

## NOTES

- **Deliberate sequencing correction (read before scoring this iteration).** The iter-11 evaluator recommended iter-12 promote a combination "whose recorded raw p clears divisor-6 required_p ≈ 0.00833 with margin." That recommendation assumed a combination staging exploration already existed (as the single-factor one did after iter-10). It does NOT — verified against `config.triad.candidates` (single-factor only), `_staging_candidates`/`explore_multi_horizon_staging` (single-factor only), the staging ledger (4 single-factor entries), and `proposer-guidance.md` §4.1 (single-factor only). No combination has ever been certified, so no recorded p exists. iter-12 supplies exactly that missing basis; iter-13 promotes + surfaces J-08. GOAL_ACHIEVED becomes reachable at iter-13.
- **Lessons applied:**
  - *iter-9 (Applies to shared-cert-engine changes):* the regression proof for touching the certification machinery is byte-identical canonical output + UNEDITED green default-path tests — NOT a browser pass. Made an explicit DoD item.
  - *iter-10 (Applies to any staging→canonical promotion):* the block-bootstrap p-floor (`p = 1/(B+1)`) saturates, so record `holdout_edge`/`control_excess` alongside `p_value` for iter-13's tiebreak; and NEVER blind-promote — a canonical PASS permanently tightens the Bonferroni divisor and a FAIL permanently tightens it for nothing. iter-12 records; iter-13 chooses.
  - *iter-9b (Applies to iter-13):* the gate defaults an omitted `"ledger"` key to `staging`; iter-13's promotion `## Evidence Claim` MUST set `"ledger":"canonical"` EXPLICITLY or the winner is silently re-staged and never surfaces. (iter-12 carries NO canonical claim.)
  - *iter-8 (Applies to candidate selection):* a documented referee FAIL is a closed hypothesis — `ma_stack` is excluded from every combination leg.
  - *iter-11 (Applies to iter-13's browser lane):* md5 the evidence PNGs and scroll each asserted badge/row into the viewport before capture (distinct screenshots, not one relabeled full-page frame). Not applicable to iter-12 (backend-only, no browser).
- **Honest-stop guard for iter-13.** If NONE of the three registered combinations clears the canonical divisor-6 bar (raw `p_value < 0.00833`) with margin in staging, the correct outcome is to honestly report it — the referee refusing to certify a thin/weak composite is anti-goal #1/#4 upheld, not a failure to engineer around. In that case J-08 needs the human to widen or revise the pre-registered set in `docs/goal.md`; iter-13 must NOT force an overfit promotion to make J-08 "pass."
- **No `## Evidence Claim` this iteration.** iter-12 surfaces nothing as "proven"; the staging exploration runs in built code via `verify_edge(ledger="staging")`, not via a spec-declared claim — so the post-decompose gate passes automatically (goal.md loop mechanics: pure discovery/enablement work needs no Evidence Claim).
