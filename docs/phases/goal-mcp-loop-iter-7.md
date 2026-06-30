# Goal Iteration 7 — All journeys passing; re-confirm and declare GOAL_ACHIEVED

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** mcp-loop
- **Iteration:** 7
- **Mode:** next
- **Depth:** lean
- **Frontend Present:** no
- **Target journeys:** J-01, J-02, J-03, J-04, J-05
- **Required-still-passing journeys:** J-01, J-02, J-03, J-04, J-05
- **Anti-goal reminders:**
  - A score, ranking, or "edge" MUST NOT be presented as proven/confident unless it is backed by a **passing certified-claim entry** in the evidence ledger (out-of-sample, control-beating). Unbacked values MUST render a "not yet proven" state. *(critical)*
  - **Decision-quality only:** never present return promises, price targets, "buy/sell" signals, or alpha claims; never place or simulate orders. *(critical)*
  - A journey passes ONLY if the **displayed numbers are correct** — they match the engine's computation for the same as-of date — not merely that the page renders. *(critical)*
  - **No overfit edges:** any pattern surfaced as "proven" must have survived the referee (sealed out-of-sample holdout + controls + multiple-testing correction), never in-sample fit alone. *(critical)*
  - **Preserve determinism and no-lookahead:** scoring uses bars ≤ as-of; forward returns use bars > as-of; never introduce lookahead anywhere. *(critical)*
  - No iteration ships if its evidence-derived claims (if any) lack a passing referee verdict from the post-decompose gate. *(critical)*
  - No hard-coded credentials, API keys, or tokens in source files. *(critical)*

## GOAL

Re-confirm that all five Must-have journeys (J-01..J-05) remain green against the current codebase, with zero code changes, so the evaluator can declare GOAL_ACHIEVED.

## BACKGROUND

The prior iteration (iter-6) returned **GOAL_ACHIEVED**: all five Must-have journeys are `passing` on the canonical browser-qa lane, coherence is COHERENCE-PASS, the certified-claims ledger holds exactly 2 referee-certified PASS claims, and no anti-goal is violated. `journey-history.json` shows **zero FAILING and zero PARTIAL** journeys, and the `<!-- AUTO:journeys -->` block in `docs/goal.md` is **empty** — the continuous-improvement loop has not proposed any new Must-have journey, so there is no remaining or new scope to build. Per the goal-decomposer rule "if `journey-history.json` shows zero remaining FAILING journeys … do NOT artificially manufacture more work," this iteration is a **verify-only re-confirmation**, not a feature delivery. The two carry-forwards the iter-6 evaluator named — B2 (`browser_checks_run` is a dead status flag with no setter) and T1 (the J-02 expanded proof panel renders below the fold and was not scrolled into frame before capture) — are explicitly **non-blocking and NOT required for the goal**, so they are deliberately OUT OF SCOPE here; manufacturing a maintenance iteration for them would be exactly the "artificial work" the rule forbids.

## IN SCOPE

### Backend
- [ ] None — no code changes. This is a verify-only re-confirmation pass.

### Frontend (if applicable)
- [ ] None — no code changes.

### New user-facing capability
None. No new capability is delivered this iteration.

### New information displayed
None.

### New user actions
None.

### UI surface changes
None.

### Product surface delta
None — the product is unchanged. This iteration only re-verifies the already-shipped evidence layer (inline "Proven / Not yet proven" badges on `/stocks` and `/stocks/{ticker}`, the J-02 proof drill-down, the Dashboard regime affordance, and the `/evidence` ledger round-trip).

### Blueprint conformance
No new surfaces. All five journeys retain their existing canonical homes per `runs/goal-session-mcp-loop/state/blueprint.md` (Stocks `/stocks` + `/stocks/{ticker}`; Dashboard `/` + Evidence `/evidence`). No Information Architecture or nav-skeleton change.

### Data-contract additions
None. No new displayed value is introduced. Evidence status / certified-claim continues to be read from its single canonical source — the read-side resolver `app.engine.evidence:build_evidence_payload` over `app.engine.ledger:read_entries(certified-claims.jsonl)`, served by the single endpoint `GET /api/evidence`. No second computation or fetch path is introduced.

## OUT OF SCOPE

- Any `apps/` source change — the evidence layer is frozen; a zero `apps/` diff is expected and required.
- Carry-forward **B2** (wiring `browser_checks_run=true` when the fanout produces a non-SKIP `…-ui-test-results.md`) — non-blocking harness/QA cleanup, not required for the goal.
- Carry-forward **T1** (scrolling the J-02 expanded proof panel into frame before capture) — non-blocking visual-evidence framing, not required for the goal.
- Any new `## Evidence Claim` / new certified edge — no new "proven" signal is proposed, so no post-decompose claim is needed and the gate auto-passes.
- Any new feature, page, or scope beyond the five existing Must-have journeys.

## DEFINITION OF DONE

- [ ] Target journeys J-01, J-02, J-03, J-04, J-05 re-verified still green (deterministic replay of stored golden scripts; no per-journey model needed).
- [ ] Required-still-passing journeys remain green (same five).
- [ ] Zero `apps/` source diff (git-verified) — no regression possible to the frozen evidence layer.
- [ ] No anti-goal violation introduced; certified-claims ledger unchanged at exactly 2 PASS entries.
- [ ] Evaluator declares **GOAL_ACHIEVED** (all five Must-have journeys passing, no new scope, no open FAILING/PARTIAL journey).

## TESTING REQUIREMENTS

- Browser: re-verify J-01, J-02, J-03, J-04, J-05 by deterministic replay of the stored golden scripts (canonical `…-ui-test-results.md` lane). No new test code.
- Unit/integration: none new — no code path changes. The existing `proven_signals == {leadership_score}` invariant and the byte-match of displayed numbers to `certified-claims.jsonl` must still hold.
- Error cases: none new — no new inputs are accepted this iteration.

## NOTES

- This spec exists to satisfy the goal-decomposer rule: when `journey-history.json` shows zero remaining FAILING/PARTIAL journeys and `docs/goal.md`'s AUTO:journeys block is empty, write a minimal verify-only spec and let the evaluator decide the terminal state rather than fabricate work.
- **Recommendation to the evaluator:** declare **GOAL_ACHIEVED**. Every `goal.md` success criterion is already met and the two outstanding carry-forwards (B2, T1) are explicitly non-blocking — they do not gate the goal and are intentionally excluded here.
- **Lesson applied (iter-2 / iter-4 / iter-5 / iter-6, embedded for the executor + evaluator):** treat `browser_checks_run=false` as a **dead flag** (no harness path sets it true — iter-6 lesson) — do NOT gate on it; judge on the canonical `…-ui-test-results.md` + `engine.log`. If the canonical browser-qa lane SKIPs or its `…-ui-test-results.md` is absent, that is a HARD verification gap (journeys hold their prior status; the deterministic replay must actually run), never an inferred pass. Do NOT substitute the parallel QA-lane (`reports/qa/<iter>-qa.md`, TC-* screenshots) for the canonical lane.
- Since `apps/` is frozen (zero diff expected), no `## Evidence Claim` is proposed and the post-decompose gate auto-passes; coherence has no diff to fault (prior iter-6 = COHERENCE-PASS).
