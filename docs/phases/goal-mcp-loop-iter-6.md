# Goal Iteration 6 — Make the canonical browser-QA lane + auditor actually run (harness verification fix)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** mcp-loop
- **Iteration:** 6
- **Mode:** next
- **Depth:** full
- **Frontend Present:** yes
- **Target journeys:** J-04
- **Required-still-passing journeys:** J-01, J-02, J-03, J-05
- **Anti-goal reminders (verbatim from `docs/goal.md`):**
  - A score, ranking, or "edge" MUST NOT be presented as proven/confident unless it is backed by a **passing certified-claim entry** in the evidence ledger (out-of-sample, control-beating). Unbacked values MUST render a "not yet proven" state. *(critical)*
  - **Decision-quality only:** never present return promises, price targets, "buy/sell" signals, or alpha claims; never place or simulate orders. *(critical)*
  - A journey passes ONLY if the **displayed numbers are correct** — they match the engine's computation for the same as-of date — not merely that the page renders. *(critical)*
  - **No overfit edges:** any pattern surfaced as "proven" must have survived the referee (sealed out-of-sample holdout + controls + multiple-testing correction), never in-sample fit alone. *(critical)*
  - **Preserve determinism and no-lookahead:** scoring uses bars ≤ as-of; forward returns use bars > as-of; never introduce lookahead anywhere. *(critical)*
  - No iteration ships if its evidence-derived claims (if any) lack a passing referee verdict from the post-decompose gate. *(critical)*
  - No hard-coded credentials, API keys, or tokens in source files. *(critical)*

## GOAL

Repair the post-dev verification pipeline so the **canonical `browser-qa-agent` lane and the auditor actually run this iteration**, producing `reports/phase-goal-mcp-loop-iter-6-ui-test-results.md` (fresh canonical UT-* for all five journeys, **J-04 → passing**) and `docs/handoffs/goal-mcp-loop-iter-6-audit.md` — with **zero `apps/` diff**.

## BACKGROUND

Every Must-have journey's feature is already built and both evidence claims are referee-certified (ledger holds exactly 2 PASS entries: `leadership_score` factor + the signal-less Breakout-watch×Risk-on event-study). The ONLY thing blocking GOAL_ACHIEVED is that the **canonical browser-qa lane has not run for two straight iterations and the auditor has not run for three** — so J-04 is stuck `partial` and J-02/J-05 lack fresh canonical pixels. Per the iter-5 lesson, `engine.log` pinpoints exactly where the pipeline dies (not the port the iter-5 dev fixed): (1) `04:40:01` — `ui-impact-phase.sh` printed a static "Done. Reports:" and exited 0 **without writing** `…-user-visible-changes.md`, so `ui-test-design-phase.sh` correctly aborted Branch-UI and browser-qa/ux-regression/closure never ran; (2) `04:43:47` — `run-phase.sh:648` then called `update_status … post_dev_parallel_complete`, an invalid step (confirmed rc=1; whitelist has no such value), which aborted the whole run **before** the sequential retry blocks and the auditor could execute. This iteration fixes those harness defects only. Depth is **full** because the auditor runs only in the full 11-step pipeline, and this is the escalation-flagged verification hardening pass.

## IN SCOPE

### Backend (HARNESS ONLY — `scripts/automation/**`; ZERO `apps/` diff)

Fix the three defects that prevent the canonical lane + auditor from running. All edits are confined to `scripts/automation/` (including `scripts/automation/lib/`). The fix must make a clean full run produce the canonical `…-ui-test-results.md` and the `…-audit.md` handoff end-to-end.

- [ ] **`scripts/automation/ui-impact-phase.sh` (L96–109) — phantom success.** The "[ui-impact] Done. Reports:" message is a static echo of the *intended* paths, printed whenever the agent returns rc==0; it never verifies the artifacts exist, and the failed-stub fallback (L100–105) only fires on rc≠0. So an agent that exits 0 without writing `…-user-visible-changes.md` leaves the file **wholly absent** while the script reports success (engine.log 04:40:01). **Fix:** after the agent returns, when rc==0, assert that BOTH `$USER_VISIBLE` and `$UI_SURFACE_MAP` exist and are non-empty; if either is missing, write the failed-artifact stub (as L100–105 already does) and exit non-zero so the failure surfaces at its source instead of a phantom "Done."
- [ ] **`scripts/automation/ui-test-design-phase.sh` — mirror the same post-condition guard** for its own two outputs (`$UI_TEST_PLAN`, `$WHAT_TO_CLICK`): rc==0 but a missing artifact must become a real failure + stub, not a silent pass. (Defense-in-depth so the next stage never aborts on a phantom upstream success.)
- [ ] **`scripts/automation/run-phase.sh:648` — invalid-step abort.** `update_status "$PHASE" "in_progress" "post_dev_parallel_complete"` passes a step name absent from the `verdicts.py` whitelist, so `update_status` returns 1 and aborts the run (engine.log 04:43:47) before the sequential Step 4–7 retry blocks and the auditor run. **Fix:** advance the checkpoint with a VALID step (the whitelist includes `ui_impact_complete`, `ui_test_designed`, `browser_qa_complete`) — or register `post_dev_parallel_complete` in the `current_step` enum in `scripts/automation/lib/verdicts.py`. Either way the post-fanout status update must NOT abort the run. (Note: `verdicts.py` is invoked as a fresh subprocess each call, so a whitelist edit there takes effect **this run** even though `run-phase.sh` is mid-flight.)
- [ ] **`scripts/automation/run-phase.sh:645–647` — unconditional SKIP flips.** After the fanout these set `SKIP_UI_IMPACT/SKIP_UI_TEST_DESIGN/SKIP_BROWSER_QA=true` **unconditionally**, even when `fanout_rc≠0` (Branch-UI aborted mid-chain at L195–197, so browser-qa never ran and no `…-ui-test-results.md` exists). The comment claiming these steps "always write their artifacts (or N/A stubs) regardless" is false on early abort. **Fix:** gate each `SKIP_*=true` on the corresponding artifact actually existing (e.g., only set `SKIP_BROWSER_QA=true` when `reports/phase-${PHASE}-ui-test-results.md` exists), so a soft-failed fanout falls through to the sequential Step 4/5/6 retry blocks that re-run the missing steps — exactly what the L641 warning already promises.

### Frontend (NO `apps/frontend/**` change — FROZEN; exercised verbatim by the canonical lane)

- [ ] No frontend code change. The existing evidence UI is frozen and must be exercised **as-is** by the canonical `browser-qa-agent` lane: `/stocks` badges, `/stocks/{ticker}` proof-panel drill-down, `/evidence` ledger list + claim→backing-surface round-trip, and the Dashboard regime/phase + Evidence affordance. `Frontend Present: yes` is set so the browser-qa lane is NOT skipped — running that lane is the entire point of this iteration.

### New user-facing capability

None. This is a verification-integrity (harness) iteration. The capability the user *gains* is indirect: the five evidence journeys are now proven green through the session-standard canonical lane, and J-04 (regime-conditioned evidence) flips from `partial` to `passing`.

### New information displayed

None. No new UI surface, no new value. The canonical lane re-captures the already-shipped surfaces with fresh, in-frame pixels (J-02 expanded proof panel; J-04 regime-labeled claim; J-05 round-trip).

### New user actions

None.

### UI surface changes

None (frozen). Existing surfaces only.

### Product surface delta

No product change. The verification standard is restored: every Must-have journey is re-verified through the canonical `browser-qa-agent` lane (not the QA agent's parallel Chrome MCP lane, which the session standard disqualifies), and the auditor signs off.

### Blueprint conformance

No new surfaces. All five journeys already have canonical homes in `blueprint.md` (J-01/J-02/J-03 → `/stocks`, `/stocks/{ticker}`; J-04 → `/` + `/evidence`; J-05 → `/evidence`). Information Architecture and Data Contract are unchanged. No `blueprint.md` edit and no `blueprint.reapproval-requested` are warranted (pure harness/QA-tooling iteration; last coherence verdict was COHERENCE-PASS).

### Data-contract additions

None. No new displayed value. The evidence status / certified-claim value continues to be served by the single canonical `GET /api/evidence` over `app.engine.ledger:read_entries(certified-claims.jsonl)`; this iteration reads nothing new and recomputes nothing.

## OUT OF SCOPE

- Any change under `apps/backend/**` or `apps/frontend/**` — the `apps/`-frozen constraint from iter-4/iter-5 stands; **zero `apps/` diff** is mandatory (any `apps/` change is an automatic FAIL and would also break the determinism/no-lookahead verification baseline).
- Any new "proven" claim, factor, cohort, or ledger entry — the ledger stays at its current 2 PASS entries; no `## Evidence Claim` block is present, so the post-decompose gate auto-passes.
- Reverting or altering the iter-5 `scripts/start-frontend.sh` port-free fix — it is correct and must remain.
- New product features, copy, or nav changes — none.
- Broad refactors of the automation harness beyond the four named defects.

## DEFINITION OF DONE

- [ ] `reports/phase-goal-mcp-loop-iter-6-ui-test-results.md` exists, `browser_checks_run=true`, is **not** all-SKIP, and carries fresh **canonical** UT-* for all five journeys (produced by the `browser-qa-agent` lane, not the QA agent's parallel lane).
- [ ] **J-04 passes via the canonical lane:** Dashboard regime/phase observed, then the regime-conditioned Breakout-watch claim on `/evidence` shown **scoped to and labeled with its regime** ("Regime: Risk-on"), scrolled into frame.
- [ ] **J-02 captured correctly:** the **expanded** `/stocks/{ticker}` proof panel (out-of-sample test result + control comparison vs SPY/QQQ/sector-ETF/random + certified-claim id + registration date) scrolled into frame — not just the score cards (standing iter-3 below-the-fold lesson).
- [ ] **J-05 round-trip captured as a DISTINCT screenshot:** click a claim on `/evidence` → its linkback to the backing surface → and back — not a byte-duplicate of the `/evidence` list frame (iter-5 produced an md5-identical dup).
- [ ] J-01 and J-03 re-confirmed green on the canonical lane.
- [ ] `docs/handoffs/goal-mcp-loop-iter-6-audit.md` exists with **PASS** or **PASS_WITH_GAPS**.
- [ ] Target journey J-04 passes; required-still-passing J-01/J-02/J-03/J-05 remain green.
- [ ] No anti-goal violation introduced; displayed numbers byte-match the certified-claims ledger / engine for the same as-of date.
- [ ] **Zero `apps/` diff** (git-verified); the iter-5 port-free fix retained; harness edits confined to `scripts/automation/**`.
- [ ] Unit/harness tests pass; no regressions (`./scripts/automation/run-evals.sh` still green).
- [ ] Dev handoff written at `docs/handoffs/goal-mcp-loop-iter-6-dev.md`.

## TESTING REQUIREMENTS

- **Browser (canonical `browser-qa-agent` lane — this is the load-bearing requirement):** J-01, J-02, J-03, J-04, J-05, each with the capture specifics in DEFINITION OF DONE. The result file must be the canonical `reports/phase-goal-mcp-loop-iter-6-ui-test-results.md`; the QA agent's parallel Chrome MCP lane does NOT substitute (session standard).
- **Unit/integration (harness):**
  - After the fix, `ui-impact-phase.sh` (and `ui-test-design-phase.sh`) must **fail loudly** (non-zero + stub written) when the agent returns rc==0 but the expected artifact is missing/empty — never print a phantom "Done."
  - The post-fanout `update_status` call must advance the checkpoint with a whitelisted step and must NOT abort the run; `verdicts.py validate-step` must accept whatever step name `run-phase.sh` now passes.
  - A soft-failed fanout (`fanout_rc≠0`) must leave the relevant `SKIP_*` flags `false` so the sequential Step 4/5/6 retry blocks re-run the missing steps.
  - `./scripts/automation/run-evals.sh` (offline harness eval suite) remains green.
- **Error cases:** missing/empty `…-user-visible-changes.md` after a rc==0 agent run → surfaced as failure + stub (not silent pass); a genuinely invalid `update_status` step → still rejected, but the normal post-fanout checkpoint must be a valid step that does not abort the run.

## NOTES

- **Applied iter-5 lesson** (episodic memory): *"When a verification artifact is missing, read engine.log to find WHERE the pipeline actually died — don't assume the previously-hypothesised cause."* Done: the death points are `engine.log` `04:40:01` (ui-impact phantom "Done" → ui-test-design missing-file abort of Branch-UI) and `04:43:47` (`invalid step 'post_dev_parallel_complete'` aborts the run before the sequential retry blocks + auditor). The iter-5 port fix was two steps downstream of the real cause; this spec targets the real cause.
- **Same-run-effect caution (important for the developer):** `run-phase.sh` is the *running parent* of this very iteration; editing a running bash parent script is unreliable (bash tracks position by byte offset). The load-bearing fixes are therefore placed in components that are re-invoked as **fresh subprocesses each step** and take effect **this run**: the child scripts `ui-impact-phase.sh` / `ui-test-design-phase.sh` (defect #1/#2) and `lib/verdicts.py` (defect #3 step whitelist). The `run-phase.sh:645–648` conditional-skip change (defect #4) is correct and required, but treat it as robustness — its full effect may land on the next dispatch/resume; do not rely on a mid-run re-read of the parent. With defect #1 fixed, the fanout's own Branch-UI chain runs ui-impact → ui-test-design → browser-qa to completion in-fanout, producing the canonical `…-ui-test-results.md`; with defect #3 fixed, the post-fanout status update no longer aborts, so ux-regression → auditor → closure proceed.
- **No Evidence Claim by design:** this is pure verification/correctness/harness work with no new "proven" claim, so per `goal.md` loop mechanics and the blueprint LOOP RULE it carries no `## Evidence Claim` block and the post-decompose gate auto-passes. Ledger unchanged at 2 PASS entries.
- **ESCALATION FLAG (carried from the iter-5 evaluator):** this is the **2nd consecutive canonical-lane miss and the 3rd consecutive absent auditor**. If iter-6 ALSO fails to run the canonical `browser-qa-agent` lane + the auditor, the evaluator should treat the session as **STALLED** and hand the harness to a human for hands-on repair rather than loop again — do not re-attempt the same harness path a 4th time blind.
- Required-still-passing set is widened to the full passing set (J-01/J-02/J-03/J-05) because the prior depth was full with an escalation flag and the canonical lane re-captures all five this run anyway; this also refreshes the golden scripts.
