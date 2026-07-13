# Goal Iteration 29 — Confirm the owner's outcome-neutral re-scope: flip J-02/J-06/J-07/J-08/J-09 to passing (verify-only)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** mcp-loop
- **Iteration:** 29
- **Mode:** next
- **Depth:** lean
- **Frontend Present:** yes  (verification hinges on browser-qa of frontend evidence surfaces; no frontend code changes)
- **Target journeys:** J-02, J-06, J-07, J-08, J-09
- **Required-still-passing journeys:** J-01, J-03, J-04, J-05, J-10, J-11, J-12, J-13, J-14
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

On every evidence surface the user sees the honest, correct, RECORDED referee verdict for each of the five re-scoped cohorts (the current all-FAIL "Not yet proven" state), read from the single source `GET /api/evidence` — flipping J-02/J-06/J-07/J-08/J-09 from `partial` to `passing` under their new **outcome-neutral** acceptance, with zero code change.

## BACKGROUND

- **Prior verdict was STALLED (iter-28)**, not ESCALATE and not REGRESSION. The five evidence journeys had no promotable edge — the complete pre-registered candidate registry was empirically exhausted (7 canonical + 7 staging entries all FAIL), so the only unblock was human-owned. Last coherence verdict was COHERENCE-PASS (no consolidation debt).
- **The owner acted at the plateau (commit `eb19cee`)**, taking the iter-28 evaluator menu: (1) **re-scoped J-02/J-06/J-07/J-08/J-09 to OUTCOME-NEUTRAL acceptance** — each now passes in EITHER the "Proven" or the honest "Not yet proven" state, so long as the surfacing is honest + correct (the absence of a PASS is "the referee working," never a journey failure); (2) pulled nine no-spend backlog cards into new Must-have journeys **J-17..J-25** (governance / daily-ops / certifier-audit / risk-analytics) — future work, none carrying an Evidence Claim.
- goal.md's **"Evidence-frontier plateau" note** frames this exact iteration: *"Their re-verification is expected to be a lean, verify-only pass — iter-28 browser-qa already demonstrated every assertion live."* journey-history's notes for all five say the browser-qa lane already marked them PASS on the honest-status half; the iter-28 evaluator held them `partial` only under the OLD strict acceptance the owner has now removed.
- **Target selection (priority rubric):** no regressed journeys exist (rule 1 n/a); coherence PASS so no consolidation pass owed (rule 2 n/a); among tractable work the **smallest-spec win** (rule 4) is the verify-only flip of the five re-scoped partials — all read the same contract value on the same surface family, so bundling these *trivial* journeys is allowed (rule 5 permits several trivial journeys). The nine new J-17..J-25 are each a *risky* new surface (new page/endpoint/value) and are deferred to one-per-iteration future iterations (rule 5 forbids bundling risky work).
- **Depth = lean** (justified triggers): verify-only, zero code, narrow scope, single journey-relevant flow. Prior verdict was STALLED not ESCALATE (no forced full), and — unlike the iter-21/23/25 verify-only *recovery* passes — there is no failing gate (CLOSURE-FAIL / UX-REGRESSION-FAIL) to formally re-clear, so the full 11-step pipeline is unnecessary.
- **Why this first:** banking these five flips re-establishes a fully-green J-01..J-16 baseline before the session takes on nine new surfaces, so any regression the new-feature work introduces is caught against a clean baseline.

## IN SCOPE

### Backend
- [ ] None — zero backend source change. (`git diff` on `apps/backend/app` stays empty vs the iteration snapshot.)

### Frontend
- [ ] None — zero frontend source change. This iteration **verifies** the EXISTING honest-surfacing behavior; it does not modify any component. (Field is `yes` only so the browser-qa lane is treated as required.)

### New user-facing capability
None. This confirms that the EXISTING honest-surfacing behavior now satisfies the re-scoped (outcome-neutral) acceptance for the five journeys.

### New information displayed
None.

### New user actions
None.

### UI surface changes
None.

### Product surface delta
No change to what the product does or shows. The change is in the goal's **acceptance contract** (owner re-scope), not in the product; iter-29 verifies the product already meets it.

### Blueprint conformance
All five journeys live at their EXISTING Information-Architecture homes — no new surface: J-02 → `/stocks/{ticker}` (inline badge → honest "Not yet proven"); J-06/J-07/J-09 → `/research/factor-lab` + `/evidence`; J-08 → `/research/factor-combination` + `/evidence`. Matches the `blueprint.md` homes table. A one-line iter-29 clarification note is appended to `blueprint.md` (additive; no IA/nav change → no re-approval).

### Data-contract additions
**None.** All five journeys READ the already-registered **evidence-status / certified-claim** value — computed once by `app.engine.evidence:build_evidence_payload` over `app.engine.ledger:read_entries(certified-claims.jsonl)`, served by the single endpoint `GET /api/evidence`. No new computing module, no second endpoint, no client-side recompute. **No `## Evidence Claim` is registered** — the canonical Bonferroni divisor stays 8 and both ledgers stay byte-identical all-FAIL.

## OUT OF SCOPE

- Any `## Evidence Claim` / referee submission / candidate promotion. Staging is CLOSED (its LORD++ wealth is exhausted; next bar sits below the block-bootstrap p-floor) and the canonical bar stays at divisor 8; re-submitting any of the closed FAILs only tightens the divisor (8→9) for no possible gain (lessons iter-8/10/12). The anti-data-mining keystone reserves new candidate authorship to the human.
- Any of the nine new journeys **J-17..J-25** — future iterations, one risky feature at a time (rule 5).
- Any backend/frontend source edit, DB rebuild, `config.yaml` change, or ledger write.
- Any perf/memory re-measurement of J-15/J-16 — zero code change ⇒ no regression mechanism; they are carried on byte-identity this iteration.

## DEFINITION OF DONE

- [ ] **J-02** passes via browser-qa: on `/stocks/{ticker}`, each score's inline evidence-status element reads **"Not yet proven"**; its explanatory text names the Evidence ledger as the audit path (reachable via the persistent Evidence nav); NO proof panel or fabricated proof renders anywhere on the page; values are read from `GET /api/evidence`.
- [ ] **J-06** passes via browser-qa: `/evidence` shows the `vcp_contraction` top-decile (D10, h20) claim row badged **FAIL** with all standard fields, holdout number byte-matching `GET /api/evidence` (≈ −0.38% / −0.0037732…); `/research/factor-lab` `vcp_contraction` top-decile badge reads **"Not yet proven"** (`data-proven=false`).
- [ ] **J-07** passes via browser-qa: `/evidence` shows the `vcp_contraction` D10 **h60** (non-20 horizon) claim row badged **FAIL**, byte-matching (≈ −1.64% / −0.016363…); `/research/factor-lab` reads **"Not yet proven"** at EVERY horizon h1/h5/h10/h20/h60.
- [ ] **J-08** passes via browser-qa: `/evidence` shows the `rs_spy_3m:top:quintile × high_proximity:top:tertile` composite (h20) claim row badged **FAIL**, byte-matching (≈ +0.01% / +8.03e-05); `/research/factor-combination` composite badge reads **"Not yet proven"** and NO combination anywhere reads "Proven".
- [ ] **J-09** passes via browser-qa: `/evidence` shows the `rs_spy_3m` D10 **h60** claim row badged **FAIL**, byte-matching (≈ −1.42% / −0.014155…) with the retired +21.34% value rendering NOWHERE; `/research/factor-lab` `rs_spy_3m` reads **"Not yet proven"** at all horizons.
- [ ] Required-still-passing journeys (J-01, J-03, J-04, J-05, J-10, J-11, J-12, J-13, J-14) remain green via deterministic golden-script replay.
- [ ] No anti-goal violation introduced — specifically: #1 nothing reads "Proven" (0 PASS in either ledger); #3 every displayed number byte-matches the ledger on disk; #6 no `## Evidence Claim` registered (grep-verified), divisor stays 8.
- [ ] Zero product source diff — `git diff` on `apps/**`, `config.yaml`, `apps/backend/data/seed`, and both `*-ledger.jsonl` files is empty vs the iteration snapshot.
- [ ] Dev handoff written at `docs/handoffs/goal-mcp-loop-iter-29-dev.md` documenting the no-op (verify-only) nature and the zero-diff confirmation.

## TESTING REQUIREMENTS

- **Browser (fresh capture, target journeys):** J-02, J-06, J-07, J-08, J-09. Produce **md5-distinct** evidence PNGs — prefer full-page or element-clip captures for the below-the-fold `/evidence` claim rows and the factor-lab / factor-combination badges (iter-14 lesson: a scrolled-viewport capture can return a blank frame). Do NOT let one capture stand in for multiple UT ids, and md5-scan the evidence dir before accepting (iter-11/13/25 lesson: a reused or "Backend unavailable" frame invalidates its citation).
- **Browser (replay, required-still-passing):** J-01, J-03, J-04, J-05, J-10, J-11, J-12, J-13, J-14 via their golden scripts. Bring up BOTH prod-mode services and confirm reachability BEFORE dispatching browser-qa (`rm -rf apps/frontend/.next` first to dodge the stale-bundle stamp — iter-20 lesson).
- **Unit/integration:** none required (zero code). Do NOT pin a slow, rarely/never-completed backend test as a hard gate (iter-23 lesson).
- **Error cases:** N/A (no new code paths). The honest all-FAIL state IS the negative-path assertion — "Proven" is never shown without a PASS certified-claim (anti-goal #1).

## NOTES

- **Lessons applied:**
  - *iter-28* — a browser-qa PASS on the honest-status half was NOT full journey acceptance under the OLD strict contract; the owner re-scope makes the honest-status half the FULL, outcome-neutral acceptance, so that same evidence now legitimately flips these five to `passing`. This is the specific thing to verify, not re-litigate.
  - *iter-11 / iter-13 / iter-25* — always `md5sum` the evidence dir; a `-fail-`/error-card frame or a frame reused across UT ids cited under a PASS invalidates that citation.
  - *iter-27* — the deterministic `scan-report.md` flags planted fake secrets inside the vendored `incredible_auto_dev/tests/judgment/` framework subtree; those are self-test fixtures, NOT product anti-goal-#7 violations. Split findings by path prefix (only `apps/`, `config.yaml`, product `data/`/`scripts/` can be a product secret).
- **This is the last "old-scope" gap.** After iter-29 banks these five, GOAL_ACHIEVED depends ONLY on the nine new journeys J-17..J-25. Suggested iter-30+ sequencing (ONE risky journey per iteration, rule 5; each carries NO Evidence Claim; each registers its own new page/value/nav in `blueprint.md` at build time, and the `/research/*` sub-routes + panels will likely need a nav-skeleton edit + `blueprint.reapproval-requested`): governance keystone first — **J-18** registry-enforcement (B-901, the pre-registration gate that J-19 reads), then **J-17** budget panel (B-903) and **J-19** graveyard (B-902); then daily-ops **J-20** (B-301) / **J-21** (B-304); certifier-audit **J-22** (B-102); risk-analytics **J-24** (B-201) / **J-25** (B-205) / **J-23** (B-204). Read the binding backlog card in `docs/improvement-backlog.md` (its What / How / Config surface / ★ Canonical value / ★ Do NOT touch / Traps) before planning each — do NOT plan J-17..J-25 from the goal.md one-liner alone.
- **State confirmed on disk at planning time:** product paths + both ledgers are byte-identical to HEAD (`eb19cee`); canonical ledger = 7 entries, 0 PASS (all-FAIL). So the zero-diff DoD line is achievable and the "Not yet proven" assertions reflect the live data.
