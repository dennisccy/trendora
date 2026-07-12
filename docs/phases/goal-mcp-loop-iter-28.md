# Goal Iteration 28 — Evidence-frontier plateau assessment (honest-stop; no evidence claim)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** mcp-loop
- **Iteration:** 28
- **Mode:** next
- **Depth:** lean
- **Frontend Present:** no
- **Target journeys:** J-02, J-06, J-07, J-08, J-09  (the five sanctioned-partial evidence journeys — under assessment this iteration; see BACKGROUND for why none can flip to passing here)
- **Required-still-passing journeys:** J-01, J-03, J-04, J-05, J-11, J-10, J-13
- **Anti-goal reminders (verbatim from `docs/goal.md`):**
  - A score, ranking, or "edge" MUST NOT be presented as proven/confident unless it is backed by a **passing certified-claim entry** in the evidence ledger (out-of-sample, control-beating). Unbacked values MUST render a "not yet proven" state. *(critical)*
  - **Decision-quality only:** never present return promises, price targets, "buy/sell" signals, or alpha claims; never place or simulate orders. *(critical)*
  - A journey passes ONLY if the **displayed numbers are correct** — they match the engine's computation for the same as-of date — not merely that the page renders. *(critical)*
  - **No overfit edges:** any pattern surfaced as "proven" must have survived the referee (sealed out-of-sample holdout + controls + multiple-testing correction), never in-sample fit alone. *(critical)*
  - **Preserve determinism and no-lookahead:** scoring uses bars ≤ as-of; forward returns use bars > as-of; never introduce lookahead anywhere. *(critical)*
  - No iteration ships if its evidence-derived claims (if any) lack a passing referee verdict from the post-decompose gate. *(critical)*
  - No hard-coded credentials, API keys, or tokens in source files. *(critical)*
  - **Resilience to data-shape and data-scale change:** widening the data basis (new nulls, broader pools, deeper history) must never crash an existing page or exhaust a service's memory — every existing consumer of a widened field is re-validated, the UI degrades gracefully (contained error boundary, honest "—"/NA placeholder, never a blank application-error page), and unbounded whole-table ORM loads are forbidden on the deep basis. *(critical)*

## GOAL

Establish, with recorded referee evidence, whether the five sanctioned-partial evidence journeys (J-02, J-06, J-07, J-08, J-09) have a promotable edge on the 30-year basis — and, finding that the entire pre-registered candidate set is empirically exhausted (all FAIL), acknowledge the plateau honestly instead of manufacturing a hopeful claim that would self-defeat the certification economy.

## BACKGROUND

**Why these journeys, and why an assessment rather than a feature delivery.** J-02/J-06/J-07/J-08/J-09 are the only journeys not passing; all five depend on promoting a referee-certified edge to the canonical `certified-claims.jsonl` ledger. They have been sanctioned-partial since the iter-18 data-basis reset (5+ iterations), each iteration's evaluator recording the standing note "no staging winner clears the canonical Bonferroni divisor-8." The iter-27 evaluator raised an explicit skeptical flag: if a fresh exploration again surfaces nothing promotable, a genuine-plateau outcome (STALLED / a goal.md amendment) is more honest than indefinitely re-attempting the same un-clearing search.

**What I verified directly (both ledgers on disk, not handoffs).** The complete pre-registered candidate set (`project-extensions/proposer-guidance.md` §4.1 four multi-horizon singles + §4.2 three combinations) has already been re-run through the referee on the 30-year basis and **every member FAILS**:
- Canonical `certified-claims.jsonl` — 7 entries, register_date 2026-07-03, seed 20240601, **all FAIL**; divisor now 8 (`required_p = 0.05/8 = 0.00625`). Best p = 0.277 (`ma_stack` D10 h20); the other six have **wrong-direction (negative) holdout edges** — the patterns reversed out-of-sample.
- Staging `staging-ledger.jsonl` — 7 entries (the §4.1 + §4.2 set) under LORD++, **all FAIL**; the strongest (`rs_spy_3m:top:quintile × high_proximity:top:tertile` composite) holds a holdout edge of **+8.03e-05** — essentially zero — at p=0.494, orders of magnitude off divisor-8.

These are genuine out-of-sample non-edges (the deep basis spans dot-com/GFC/COVID/2021-26, so regime-fragile edges correctly fail the sealed holdout — exactly the goal.md-anticipated "fewer but more robust certified edges" outcome), not a multiple-testing-bar artifact that a looser economy could rescue. `proposer-guidance.md §4.2` names this exact case and its remedy: *"If NONE of the three clears the bar with margin, honestly report it… J-08 then needs the human to widen/revise the pre-registered set."* The anti-data-mining keystone (§4.1/§4.2) reserves candidate-set authorship to the human/goal.md registry — an autonomous agent may not fabricate a new hypothesis — and every re-submitted FAIL permanently tightens the divisor (8→9→…), making *all* future edges harder (lessons iter-8/iter-10/iter-12). So there is **no productive, in-scope, autonomous evidence move for iter-28**: re-submitting is self-defeating and forbidden (closed hypotheses), and authoring a new blind candidate violates the keystone and also self-defeats.

**Depth = lean (justified).** This iteration ships zero code, touches no data model, and registers no new "proven" claim — so none of the "full" triggers apply. The prior evaluator recommended FULL, but that recommendation was explicitly contingent on *shipping a referee-gated canonical claim that needs the audit/ux-regression/closure guards*; since the ledger evidence shows no claim is promotable without self-defeating bar-tightening, that contingency is void. The prior verdict was CONTINUE (not ESCALATE), so no forced-full applies. A verify-only / plateau-acknowledgement pass is a lean cycle (developer no-op → reviewer → deterministic replay of the regression set), matching the baseline-mode precedent for verify-only work.

## IN SCOPE

### Backend
- [ ] None. No source change. (`git diff HEAD` on `apps/backend/app/**` must stay empty.)

### Frontend (if applicable)
- [ ] None. No source change. (`git diff HEAD` on `apps/frontend/**` must stay empty.)

### Evidence / referee
- [ ] **No `## Evidence Claim` block is registered this iteration** — the post-decompose gate passes automatically; both ledgers stay byte-identical all-FAIL; the canonical Bonferroni divisor stays 8. This is deliberate and load-bearing: do NOT add a claim downstream.

### Assessment & documentation (the actual work product)
- [ ] Record the plateau finding in the dev handoff with the recorded referee evidence: quote the 7 canonical + 7 staging FAIL verdicts (factor/horizon, holdout_edge sign, p_value, required_p) and note that the complete §4.1/§4.2 pre-registered set is exhausted on the 30-year basis.
- [ ] Confirm (git diff) that both ledgers and all product source are byte-identical to HEAD — no accidental evidence work slipped in.

### New user-facing capability
None. No product surface changes this iteration.

### New information displayed
None.

### New user actions
None.

### UI surface changes
None. This is a zero-code assessment pass.

### Product surface delta
None. The `/evidence` ledger continues to render its honest all-FAIL state (every badge "Not yet proven"); no fabricated Proven badge appears anywhere. This is anti-goal #1 upheld, not a gap.

### Blueprint conformance
No new surfaces. No Information-Architecture change; every journey stays at its already-registered home. An additive iter-28 clarification paragraph is appended to `blueprint.md` recording that this is a zero-contract-change plateau-acknowledgement pass (no new value, no new module/endpoint, no nav change).

### Data-contract additions
None. No new displayed value. No value's computing module or serving endpoint changes. (Explicitly: the evidence-status / certified-claim value keeps its single source — `app.engine.evidence:build_evidence_payload` over `read_entries(certified-claims.jsonl)` → `GET /api/evidence` — unchanged and byte-identical.)

## OUT OF SCOPE

- **Any `## Evidence Claim` / referee submission** (canonical OR staging). Re-submitting a pre-registered candidate is a closed hypothesis and would tighten the divisor; authoring a new one violates the anti-data-mining keystone. Neither is permitted.
- **Any product source change** (`apps/backend/app/**`, `apps/frontend/**`, `config.yaml`, `data/seed/**`). This is a verify-only pass.
- **Re-touching iter-27's memory-hardening work** (config.py / prices.py / scoring.py / regime.py / data_manager.py / warmup.py). It is done, live-verified, and byte-identity-gated — leave it.
- **Non-blocking carry-forwards** (do NOT bundle): B1 `IndicatorsCfg._validate` `max_needed` guard hole; T1/F1 browser-qa backend-lifecycle permission; `rm -rf .pytest-tmp-iter27/` scratch. These are polish on already-passing journeys and out of scope for an assessment pass.
- **Editing `docs/goal.md` or `proposer-guidance.md`** to widen the candidate set. That is a human / goal-proposer action (the AUTO:journeys marker / the pre-registered registry are human-owned); the decomposer surfaces the option for the evaluator, it does not perform it.

## DEFINITION OF DONE

- [ ] No `## Evidence Claim` block appears in this spec or is submitted downstream (grep-verifiable); the post-decompose gate passes automatically.
- [ ] `git diff HEAD` is empty on `runs/goal-session-mcp-loop/state/certified-claims.jsonl` AND `runs/goal-session-mcp-loop/state/staging-ledger.jsonl` — both ledgers byte-identical all-FAIL; the canonical divisor stays 8.
- [ ] `git diff HEAD` is empty on `apps/backend/app/**`, `apps/frontend/**`, `config.yaml`, and `apps/backend/data/seed/**` — zero product source change.
- [ ] Required-still-passing journeys (J-01, J-03, J-04, J-05, J-11, J-10, J-13) replay green via the deterministic golden-script replay / browser-qa lane; the `/evidence` ledger renders all-FAIL with every badge reading "Not yet proven" (anti-goal #1 honest-status contract holds on the all-FAIL ledger).
- [ ] The two frozen-golden ledger tests pass unedited: `apps/backend/tests/test_evidence.py::test_canonical_ledger_frozen_golden` and the staging-ledger routing test in `apps/backend/tests/test_staging_ledger_routing.py` (targeted invocation only — see TESTING; do NOT run the full ~10-11h suite).
- [ ] The plateau finding (7 canonical + 7 staging FAIL; pre-registered set exhausted; escape-valve routes to a human candidate-set revision) is documented with recorded evidence in the dev handoff.
- [ ] Dev handoff written at `docs/handoffs/goal-mcp-loop-iter-28-dev.md`.

> Note on target journeys: J-02/J-06/J-07/J-08/J-09 CANNOT flip to passing this iteration and this DoD does not claim they will — no promotable edge exists on the current basis + pre-registered set (evidence above). The target-journey deliverable is the *assessment* that they are plateaued, handed to the evaluator; the evaluator (not this spec) decides the verdict.

## TESTING REQUIREMENTS

- **Browser / replay:** deterministic golden-script replay of J-01, J-03, J-04, J-05, J-11, J-10, J-13. The evidence-status readers (J-01 badges on `/stocks`, J-03 honest "Not yet proven" marking, J-04 regime-conditioned evidence, J-05 `/evidence` ledger audit, J-11 all-FAIL/no-stale-edge) all read the same `GET /api/evidence` all-FAIL payload — replaying them confirms no accidental change flipped any badge to "Proven" and that the honest-status contract holds. J-10/J-13 are the core-nav/data smoke.
- **Unit/integration:** run ONLY the two targeted frozen-golden ledger tests named in the DoD to prove the ledgers are unchanged (`pytest apps/backend/tests/test_evidence.py::test_canonical_ledger_frozen_golden` and the staging-routing test by node id). Do NOT run the full suite — at the 30-year basis it is ~10-11 hours and would fork-lock the host (host constraint).
- **Error cases:** none — no new inputs are accepted this iteration.

## NOTES

**Recorded referee evidence (the plateau, verbatim from the ledgers — read, do not recompute).** All register_date 2026-07-03, seed 20240601, decile 10 / direction positive unless noted.

Canonical `certified-claims.jsonl` (all FAIL; divisor now 8, `required_p=0.00625`):
| # | cohort | horizon | holdout_edge | p_value | note |
|---|--------|---------|--------------|---------|------|
| 1 | leadership_score | 20 | −0.000314 | 0.535 | wrong direction |
| 2 | event-study Breakout-watch / Risk-on | 20 | −0.006842 | 0.946 | wrong direction |
| 3 | ma_stack | 20 | +0.002062 | 0.277 | right dir, far from bar (closed FAIL, iter-8) |
| 4 | vcp_contraction | 20 | −0.003773 | 0.960 | wrong direction |
| 5 | vcp_contraction | 60 | −0.016364 | 0.9995 | wrong direction |
| 6 | combination rs_spy_3m×high_proximity | 20 | +8.03e-05 | 0.494 | ~zero edge |
| 7 | rs_spy_3m | 60 | −0.014155 | 0.905 | wrong direction |

Staging `staging-ledger.jsonl` (the complete §4.1 + §4.2 pre-registered set; all FAIL under LORD++): vcp_contraction h10 (−0.00266), vcp_contraction h60 (−0.01636), rs_spy_3m h60 (−0.01416), leadership_score h60 (−0.00388), combo rs_spy_3m×atr_pct (−0.00416), combo leadership_score×atr_pct (−0.00442), combo rs_spy_3m×high_proximity (+8.03e-05). Six of seven are wrong-direction; the one non-negative is ~zero.

**Menu for the evaluator (this spec does not choose the verdict).** With the pre-registered set empirically exhausted and no autonomous evidence move available, weigh:
1. **STALLED (honest plateau, human-owned unblock).** The only path to advance J-02/J-06/J-07/J-08/J-09 is a *human* revision of the pre-registered candidate registry (`docs/goal.md` §4.1/§4.2 / `proposer-guidance.md`) — e.g. opening the goal.md-deferred families (quantile spreads D10−D1, regime-conditioning, sector cohorts), which are explicitly "NOT this direction" and human-authored. This matches the iter-16 precedent (prefer STALLED-with-menu over CONTINUE-into-a-wall when the unblock is human-owned) and the §4.2 escape valve ("J-08 then needs the human to widen/revise the pre-registered set").
2. **goal.md amendment.** A human/goal-proposer edit that either widens the pre-registered set or re-scopes the five journeys to accept the honest all-FAIL ledger as their terminal contract (the UI already honestly shows no fabricated Proven badge — arguably the honest-status half of each journey is satisfied; what is absent is a *Proven* row to drill, which requires a real certified edge that does not exist on this basis).
3. **CONTINUE only if** the evaluator identifies genuinely productive non-evidence work within goal.md scope that advances a partial/failing journey — but note the five partials cannot advance without a certified edge, and further perf polish on the already-passing J-15/J-16 would be manufactured work (rubric: do not artificially manufacture work).

**Lessons applied (episodic memory).**
- iter-8 / iter-10 / iter-12: a canonical PASS *or FAIL* permanently appends to `certified-claims.jsonl` and tightens the user-facing Bonferroni divisor forever; a documented referee failure is a **closed hypothesis** — never re-propose ma_stack / hv / high_proximity / the failed multi-horizon or combination candidates. Over-proposing self-defeats.
- iter-16: when the only unblock is a human-owned action, exercise STALLED-with-menu early rather than scheduling an iteration into a wall; write the eval so the halt reads as loop-viability, not iteration failure.
- iter-17: the iter-18 sanctioned ledger reset was pre-authorized by goal.md's data-basis provision — the resulting all-FAIL ledger is the system working, not a regression; J-01..J-09 stay valid contracts (honest badges, correct numbers) while their specific retired-window edges do not reproduce.

**Coordinator note honored.** No `## Evidence Claim` is registered (a hopeful re-submission would self-defeat by tightening the divisor); a verify-only / plateau-acknowledgement pass is a legitimate iteration and is not manufacturing an evidence claim just to have one. Host constraints respected: no background-and-wait-across-turns instructions; a 000 on the heavy `/api/data` endpoint during warmup is not a down backend (cold start ~130s) — wait for readiness before dispatching the replay lane; the full pytest suite is NOT run (only the two targeted frozen-golden ledger tests).
