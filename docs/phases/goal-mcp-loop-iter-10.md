# Goal Iteration 10 — Open the multi-horizon scan aperture + discover non-20-horizon edges in the staging economy (Part B Phase 1)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** mcp-loop
- **Iteration:** 10
- **Mode:** next
- **Depth:** full
- **Frontend Present:** no
- **Target journeys:** J-07 (discovery/enablement PREREQUISITE only — this iteration explores non-20-horizon candidates in the internal staging ledger; it does NOT surface a badge, so J-07 stays `unknown`. Surfacing the discovered winner is iter-11.)
- **Required-still-passing journeys:** J-01, J-02, J-03, J-04, J-05, J-06 (all read the single "Evidence status + certified-claim" Data-Contract value the certification engine computes; because this iteration modifies that shared engine — referee / online_fdr / triad_scan / ledger routing — every reader is re-verified. Frontend Present: no ⇒ re-verified by the canonical `/api/evidence` byte-identity path + the unedited default-path unit suite, NOT by browser pixels and NOT by the dead `browser_checks_run` flag — the iter-9 lesson.)
- **Anti-goal reminders (verbatim from `docs/goal.md`):**
  - "No overfit edges: any pattern surfaced as \"proven\" must have survived the referee (sealed out-of-sample holdout + controls + multiple-testing correction), never in-sample fit alone. *(critical)*"
  - "A score, ranking, or \"edge\" MUST NOT be presented as proven/confident unless it is backed by a passing certified-claim entry in the evidence ledger (out-of-sample, control-beating). Unbacked values MUST render a \"not yet proven\" state. *(critical)*"
  - "Preserve determinism and no-lookahead: scoring uses bars ≤ as-of; forward returns use bars > as-of; never introduce lookahead anywhere. *(critical)*"
  - "No iteration ships if its evidence-derived claims (if any) lack a passing referee verdict from the post-decompose gate. *(critical)*"
  - "Decision-quality only: never present return promises, price targets, \"buy/sell\" signals, or alpha claims; never place or simulate orders. *(critical)*"
  - "No hard-coded credentials, API keys, or tokens in source files. *(critical)*"

## GOAL

Open the certification engine's scan aperture beyond the 20-day horizon and run a PRE-REGISTERED set of multi-horizon single-factor hypotheses through the referee into the INTERNAL staging ledger under the online-FDR economy — discovering which non-20-horizon cohorts genuinely clear the out-of-sample bar, WITHOUT touching the user-facing canonical Bonferroni bar or displaying anything new. This produces the referee-scored candidate list iter-11 promotes to surface J-07.

## BACKGROUND

goal.md's engineering direction sequences the aperture work as "**build the economy first (Part A), then widen the scan (Part B)**." iter-9 shipped Part A (the injectable online-FDR / LORD++ staging economy, default-off, byte-identical canonical). This iteration is **Part B Phase 1**: multi-horizon — a `config.triad.horizons` edit reusing `compute_factor_lab`, plus raising `triad.top_k` and the currently-inert `triad.screen.haircut_coef`, then exploring a fixed hypothesis set in staging.

Why discovery-first instead of a direct J-07 canonical claim: the next canonical trial faces Bonferroni **divisor 5 → required_p = 0.010**, and there is **zero non-20-horizon referee evidence anywhere** (the triad snapshot is h20-only; the staging ledger is empty). The iter-8 lesson is decisive — a canonical claim proposed on a cheap triad-*screen* survivor (ma_stack) FAILED the stricter *referee* (p=0.0195), was written as a permanent FAIL entry that tightened the user-facing bar, and needed a human rescue. The iter-9 staging economy exists precisely so exploration is non-burning. So iter-10 spends staging trials (fenced, non-burning) to FIND a genuine block-bootstrap `p_value < 0.010` winner; iter-11 then promotes exactly that winner to canonical with high confidence (the recorded raw p-value already clears divisor 5). No journey flips this iteration — this mirrors iter-9's enablement-only milestone, which the evaluator scored as "real, load-bearing progress."

## IN SCOPE

### Backend
- [ ] **Open the multi-horizon aperture (config).** Add `horizons: [1, 5, 10, 20, 60]` to the `triad:` block in `config.yaml` so `app.engine.triad_scan:_triad_cfg` / `scan_factor_decile_cells` / `scan_product_triad` enumerate one cell per `(factor, horizon, decile)` across all configured horizons (today they default to `[walk_forward.default_horizon] = [20]`). Reuses the existing `compute_factor_lab` cohort machinery and the already-present `walk_forward.horizons: [1,5,10,20,60]` forward-return data.
- [ ] **Scale the multiple-testing haircut to the wider aperture.** Raise `triad.top_k` (only `ranked[:top_k]` are screened) and set the currently-inert `triad.screen.haircut_coef` so the screen's haircut grows with the larger batch (goal.md Part B Phase 1). Both consumed verbatim from config — no magic numbers in code.
- [ ] **Register the PRE-REGISTERED candidate set (the anti-data-mining keystone).** Add a FIXED, config-backed list of multi-horizon single-factor hypotheses (each carrying a one-line economic rationale), and mirror it into `project-extensions/proposer-guidance.md`. The exploration iterates ONLY this fixed set — NEVER the full `factor × horizon × decile` cross-product. Proposed set (decile 10, direction positive; see NOTES for rationales — the developer registers these and may DROP a candidate only if infeasible on the committed seed, never ADD an ad-hoc one):
  - `vcp_contraction` D10 @ **h10**
  - `vcp_contraction` D10 @ **h60**
  - `rs_spy_3m` D10 @ **h60**
  - `leadership_score` D10 @ **h60** (strong staging anchor; see NOTES)
- [ ] **Run the multi-horizon staging exploration.** Add a deterministic backend entry (a new function in `app.engine.triad_scan` and/or an MCP tool) that, for each pre-registered candidate, assembles the cohort's `(as_of_date, realized_return)` observations at that horizon (reusing the existing cohort assembly `_assemble_cell_observations` / the factor-lab reader) and calls `app.mcp.tools:verify_edge(ledger="staging", ledger_path=$STAGING_LEDGER_PATH)`, appending each referee verdict (holdout edge, block-bootstrap `p_value`, PASS/FAIL/INSUFFICIENT, `deflation`, `required_p`) to the staging ledger under the online-FDR (LORD++) economy. `verify_edge` stays the SINGLE ledger writer; `scan_product_triad` stays READ-ONLY w.r.t. both ledgers and the snapshot DB.
- [ ] **Activate the online-FDR economy for staging.** Enable the LORD++ economy so the wide staging search stays feasible (a strict-Bonferroni divisor over the whole candidate batch would crush it), while the **honesty fence** `use_fdr = (ledger == STAGING and evidence.fdr.enabled)` keeps the canonical ledger strict Bonferroni and byte-identical. FDR is weaker than family-wise control and MUST remain fenced to staging.
- [ ] **Persist the populated staging ledger** to `runs/goal-session-mcp-loop/state/staging-ledger.jsonl` in the session state dir (committed with the iteration) so iter-11's decomposer can read the recorded p-values and promote the winner.

### Frontend (if applicable)
- None. Zero `apps/frontend/**` diff (Frontend Present: no). No UI, no badge, no /evidence change this iteration.

### New user-facing capability
None. This is internal certification-engine discovery machinery — the direct successor to iter-9's Part A. Nothing on any user surface changes; it sets up iter-11 to surface J-07's non-20-horizon "Proven" badge + `/evidence` row.

### New information displayed
None. The staging ledger is internal-only — never served by `GET /api/evidence`, never displayed. Every user-facing number stays byte-identical.

### New user actions
None.

### UI surface changes
None.

### Product surface delta
None visible this iteration. The product experience is unchanged; the discovered staging candidates enable iter-11 to add the first evidence beyond the 20-day horizon (J-07).

### Blueprint conformance
No new surfaces. Backend-only certification-engine work — reuses the EXISTING `/research/factor-lab` + `/evidence` routes for J-07's eventual (iter-11) home, already registered in the blueprint IA table. An additive iter-10 clarification is appended to the Data Contract in `runs/goal-session-mcp-loop/state/blueprint.md` documenting that the multi-horizon staging exploration introduces no new displayed value, no new serving endpoint, and no nav change. No nav-skeleton change ⇒ no re-approval requested.

### Data-contract additions
None. The single "Evidence status + certified-claim" value (served by `GET /api/evidence`, computed by `referee:certify_edge` via `verify_edge`) is unchanged. The multi-horizon candidates are written ONLY to the internal staging ledger, which is already documented (iter-9 clarification) as never served and never displayed. No new shared value to register; no second computing module and no second endpoint are introduced (`verify_edge` remains the sole writer, merely routing to the staging file).

## OUT OF SCOPE

- **Any canonical `## Evidence Claim` / any write to `certified-claims.jsonl`.** A blind canonical claim would risk permanently tightening the user-facing Bonferroni bar (divisor 5 → 6) on unproven evidence — the exact iter-8 pitfall. Deferred to iter-11, which promotes a staging-proven `p_value < 0.010` winner.
- **Any UI change for J-07** — no `/evidence` row, no factor-lab badge, no linkback. Surfacing is iter-11.
- **Multi-factor COMBINATION enumeration + `/research/factor-combination`** (that is J-08; a later iteration). Keep iter-10 tight to multi-horizon single factors.
- **Re-proposing `ma_stack`, `hv`, or `high_proximity`** as candidates (blueprint iter-8 directive: do not re-propose these; ma_stack already FAILED the referee, hv/high_proximity are economically weak — see NOTES).
- Regime/sector cohort expansion, quantile spreads (D10−D1), scoped α-split families — goal.md defers these to later phases.
- Touching, rewriting, or re-ordering any of the 4 existing canonical ledger entries, or changing `proven_signals` (it stays exactly `{leadership_score}`).

## DEFINITION OF DONE

- [ ] `config.triad.horizons` includes the non-20 horizons and `top_k` / `screen.haircut_coef` are raised; `scan_factor_decile_cells` / `scan_product_triad` deterministically enumerate one cell per `(factor, horizon, decile)` for every configured horizon (unit-tested: exact horizons + cell counts).
- [ ] A FIXED, pre-registered candidate set of multi-horizon single-factor hypotheses (each with an economic rationale) is config-backed AND mirrored into `project-extensions/proposer-guidance.md`; the exploration iterates ONLY that set (no full cross-product).
- [ ] The multi-horizon staging exploration runs deterministically against the committed seed (seed=20240601) and persists one referee verdict per pre-registered candidate — recording holdout edge, block-bootstrap `p_value`, status, `deflation`, and `required_p` — to `runs/goal-session-mcp-loop/state/staging-ledger.jsonl`. `verify_edge` remains the sole ledger writer; a re-run yields byte-identical verdicts.
- [ ] **Honesty fence proven:** the canonical `certified-claims.jsonl` is git-UNMODIFIED; `GET /api/evidence` + `proven_signals` are byte-identical; `test_referee.py` / `test_forward_walk.py` / `test_evidence.py` default-path expectation tests are UNEDITED and green (the iter-9 regression proof that defaults reproduce byte-identically). The auditor confirms zero staging references reach `evidence.py`, the routers, or `GET /api/evidence`, and that a CANONICAL `certify_edge` call reproduces strict-Bonferroni `required_p` even with `fdr.enabled=true`.
- [ ] No-lookahead preserved at every horizon (forward returns use bars > as-of at each of h1/h5/h10/h60; the referee's sealed temporal holdout split is per-horizon correct); determinism preserved.
- [ ] J-01…J-06 non-regression confirmed via the canonical byte-identity path (browser QA is N/A by design — Frontend Present: no — and is NOT judged on the dead `browser_checks_run` flag).
- [ ] No anti-goal violation: nothing new reads "Proven"; nothing on `/evidence` changes; the FDR economy stays fenced to staging; no return/price/buy-sell language; secret scan of the diff clean.
- [ ] Dev handoff at `docs/handoffs/goal-mcp-loop-iter-10-dev.md` records, PER pre-registered candidate, its block-bootstrap `p_value` and whether it clears the canonical divisor-5 bar (`p < 0.010`) — the explicit input to iter-11's promotion decision.
- [ ] Post-QA audit handoff at `docs/handoffs/goal-mcp-loop-iter-10-audit.md` exists (the audit stage was the recurring iter-3/4/5 gap — it MUST run and verify the honesty fence + canonical byte-identity).
- [ ] **NOT expected:** J-07 does NOT flip to passing this iteration (no UI surface is built) — it stays `unknown`. Do not treat an absent J-07 badge as a failure; the discovered staging candidates are the deliverable.

## TESTING REQUIREMENTS

- **Browser:** N/A — Frontend Present: no; no UI or journey surface changes. J-01…J-06 non-regression is verified by the canonical `/api/evidence` byte-identity path (ledger git-unmodified + `build_evidence_payload` frozen-golden green), consistent with iter-9. No new journey is browser-verified this iteration.
- **Unit/integration (assert exact values, cover a failure path):**
  - Multi-horizon enumeration: `scan_factor_decile_cells` / `scan_product_triad` produce cells for every configured horizon (assert the exact horizon set and per-horizon cell counts).
  - Staging routing: `verify_edge(ledger="staging", ledger_path=…)` appends to the staging file and NEVER to canonical; `ledger.count_trials(canonical)` and the canonical Bonferroni divisor are unchanged by staging trials.
  - Online-FDR purity + correctness: `online_fdr.test_level` returns the exact LORD++ levels for a known rejection-ordinal sequence (deterministic; no RNG/IO), and FDR affects ONLY staging.
  - Honesty fence: with `evidence.fdr.enabled=true`, a CANONICAL `certify_edge` / `verify_edge` call reproduces `required_p = alpha_per_test / n_trials` (strict Bonferroni) byte-identically — canonical is never routed through FDR.
  - Default-path reproduction: `test_referee.py` unedited and green (byte-identical canonical verdicts) — if these expectation tests need editing, that itself is the regression signal (iter-9 lesson).
  - No-lookahead: at each new horizon the cohort's forward returns are drawn only from bars > as-of and the sealed-holdout split is temporally correct.
- **Error cases:** an infeasible candidate (a horizon lacking sufficient post-snapshot bars, or a cohort too thin for the block bootstrap) is recorded as `INSUFFICIENT` in staging — surfaced, not silently dropped and not crashing; an unrecognized ledger-routing value fails closed (existing gate behavior, unchanged).

## NOTES

- **Pre-registered candidate rationales (anti-data-mining keystone — a FIXED, reasoned hypothesis set, each drawn from a documented h20 screen survivor and re-registered at a NON-20 horizon, so each is a genuine "beyond the 20-day horizon" hypothesis for J-07):**
  1. `vcp_contraction` D10 @ **h10** — tight volatility contractions resolve into expansion; test whether the (h20-proven) edge already appears at a ~2-week hold. Signal-less (non-score) ⇒ the cleanest J-07 promotion candidate (backs the factor lab only, never a /stocks badge).
  2. `vcp_contraction` D10 @ **h60** — does the post-contraction expansion edge persist/strengthen over a quarter? Signal-less.
  3. `rs_spy_3m` D10 @ **h60** — 3-month relative-strength leadership over a hold matched to the factor's own 3-month lookback (a longer horizon is more natural for this factor than h20, where the cheap screen showed non-persistence). Signal-less; the speculative member of the set.
  4. `leadership_score` D10 @ **h60** — the system's strongest signal (hit the block-bootstrap p-floor 0.0004998 at h20) probed at a longer hold: a high-probability staging ANCHOR that confirms the multi-horizon machinery certifies a real edge end-to-end. It is a score-column factor, so it would NOT disturb J-01/J-02/J-03 (`leadership_score` is already in `proven_signals`); it is the FALLBACK, not the preferred J-07 promotion — iter-11 prefers a signal-less winner (#1–#3) if one clears `p < 0.010`.
- **Apply the iter-8 lesson (do not repeat the documented mistake):** the triad SCREEN (`holdout_edge > required`) is a WEAKER bar than the REFEREE (block-bootstrap p after deflation). ma_stack survived the screen yet the referee FAILED it and permanently tightened the canonical bar. Therefore: (a) never propose a CANONICAL claim on screen evidence alone — iter-10 explores in the non-burning staging economy first; (b) do NOT re-propose `ma_stack` / `hv` / `high_proximity` (blueprint iter-8 directive; hv is additionally excluded on economics — its edge is a volatility risk premium with weak rank-IC and the deepest drawdown, not a decision-quality signal).
- **Apply the iter-9 / iter-9b lessons:** for a shared-engine change the regression proof is canonical byte-identity + the UNEDITED default-path unit suite (not a browser pass, not the dead `browser_checks_run` flag). And the gate defaults an omitted `"ledger"` key to `"staging"` — so iter-10 carries **NO `## Evidence Claim`** (the gate passes through, exit 0; the staging referee runs are invoked directly via `verify_edge(ledger="staging")`, never through the blocking gate, so nothing can block the iteration and the canonical bar is untouched). iter-11's promotion claim MUST set `"ledger":"canonical"` EXPLICITLY or the winner is silently certified into staging and never surfaces.
- **Depth = full** because this modifies the shared certification engine (referee / online_fdr / triad_scan / ledger routing) and activates the FDR economy — structural backend work needing the full pipeline and, critically, the AUDITOR to verify the honesty fence (canonical strict-Bonferroni, byte-identical) and no-lookahead across the new horizons. iter-9 (the analogous Part A) was likewise dispatched full, and the prior evaluator recommended full.
- **Sets up iter-11 (surface J-07):** iter-11 reads `staging-ledger.jsonl`, picks the signal-less candidate with the smallest block-bootstrap `p_value < 0.010`, promotes it via a canonical `## Evidence Claim` (`"ledger":"canonical"`, certified at divisor 5 / required_p=0.010), and surfaces the `/evidence` row + factor-lab "Proven" badge + browser-verifies J-07. If NO candidate clears `p < 0.010`, that is an honest finding (single-factor non-20 cohorts do not clear the current bar) — iter-11 pivots to J-08 combinations or the human adjusts the candidate set; do NOT force a marginal canonical claim.
