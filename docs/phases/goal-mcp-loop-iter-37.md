# Goal Iteration 37 — Deterministic regression-replay closeout (close the iter-36 CLOSURE-FAIL replay gap; fold in J-21/J-22 goldens)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** mcp-loop
- **Iteration:** 37
- **Mode:** next
- **Depth:** lean
- **Frontend Present:** yes
- **Target journeys:** J-05, J-11
- **Required-still-passing journeys:** J-01, J-02, J-03, J-04, J-06, J-07, J-08, J-09, J-10, J-12, J-13, J-14, J-17, J-18, J-19, J-20, J-21, J-22
- **Anti-goal reminders:**
  - A score, ranking, or "edge" MUST NOT be presented as proven/confident unless it is backed by a **passing certified-claim entry** in the evidence ledger (out-of-sample, control-beating). Unbacked values MUST render a "not yet proven" state. *(critical)*
  - **Decision-quality only:** never present return promises, price targets, "buy/sell" signals, or alpha claims; never place or simulate orders. *(critical)*
  - A journey passes ONLY if the **displayed numbers are correct** — they match the engine's computation for the same as-of date — not merely that the page renders. *(critical)*
  - **No overfit edges:** any pattern surfaced as "proven" must have survived the referee (sealed out-of-sample holdout + controls + multiple-testing correction), never in-sample fit alone. *(critical)*
  - **Preserve determinism and no-lookahead:** scoring uses bars ≤ as-of; forward returns use bars > as-of; never introduce lookahead anywhere. *(critical)*
  - No iteration ships if its evidence-derived claims (if any) lack a passing referee verdict from the post-decompose gate. *(critical)*
  - No hard-coded credentials, API keys, or tokens in source files. *(critical)*
  - **Resilience to data-shape and data-scale change:** widening the data basis (new nulls, broader pools, deeper history) must never crash an existing page or exhaust a service's memory — every existing consumer of a widened field is re-validated, the UI degrades gracefully (contained error boundary, honest "—"/NA placeholder, never a blank application-error page), and unbounded whole-table ORM loads are forbidden on the deep basis. *(critical)*

## GOAL

No new user-visible change: run the deterministic golden-script regression replay that iter-36's full-pipeline path structurally skipped, formally re-verifying that all 20 built, golden-scripted journeys are still green — and fold in the two accumulated goldens (J-21.json from iter-35, J-22.json from iter-36) — closing the iter-36 CLOSURE-FAIL replay gap with **zero** product change before J-23 feature work begins.

## BACKGROUND

iter-36 was CONTINUE (J-22 delivered clean, browser-qa PASS 13/13 on the final build) but ended **CLOSURE-FAIL** on a single, narrow Definition-of-Done line: the required-still-passing journeys were not deterministically replayed. The closure auditor named **J-05 and J-11** as the two unverified rows (QA over-claimed "all live-verified" with unevidenced TC-19/TC-20 conclusions, no screenshot), and the canonical browser-qa lane transparently excluded the required set from its dispatched plan. The iter-36 evaluator marked J-05/J-11 re-verified on its own personal evidence walk (frames it opened), but explicitly recorded that **the dedicated per-journey golden replay is still formally open and is the mandated next lean-closeout step**.

This is the exact iter-33→iter-34 pattern: a FULL iteration routes through `run-phase.sh`, which has **zero** deterministic-replay-lane machinery — that lane lives **only** in `goal-iter-lean.sh` (the lean path). The gap has now CLOSURE-FAILed **twice** (iter-33, iter-36), and replay debt has **accumulated across two iterations**: J-21.json (iter-35, whose closure passed via live browser re-verification, deferring the replay) and J-22.json (iter-36). This lean pass pays the whole debt down at once.

**Why this over going straight to FULL J-23** (priority rubric): no journey regressed (rule 1 clear); coherence PASSED at iter-36 so no coherence-consolidation is owed, but the closure gate is currently **red** and the honest move is to green it and re-baseline the full built set before the final 3-journey risk-analytics cluster (J-23/J-24/J-25) — each of which needs a clean, fully-replayed regression baseline to detect breakage against. Adding J-23 now would deepen the debt to a third un-folded golden and pile new scope on an unclosed gate. This is the iter-36 evaluator's preferred recommendation ("paying it down first is preferred"). Smallest spec wins the tie (rule 4).

**Depth is `lean`, and lean is MANDATORY here** (not merely allowed): the deterministic-replay lane exists only in `goal-iter-lean.sh`; a `full` iter would re-route through `run-phase.sh` (0 replay-lane refs) and re-skip the replay, re-creating the exact iter-33/iter-36 gap. This is a verification-only pass — the developer step is a no-op (no code), and the value comes from the browser-qa step's replay lane. Prior verdict was CONTINUE (not ESCALATE), so no forced-full applies.

**Applied lessons.** iter-33 + iter-36 lessons (directly): a FULL iteration's "required-still-passing deterministic replay" DoD line is structurally *unsatisfiable* — confirm `regression-replay-results.md` actually exists rather than trusting the checkbox; this pass produces exactly that artifact. iter-23 lesson: do NOT pin an unsatisfiable/never-completed slow test as a DoD gate — the lean cycle skips phase-closure-auditor, so this spec's DoD is the artifacts the lean cycle actually writes (the merged `ui-test-results.md` the goal-evaluator reads), never a "CLOSURE-PASS" step. iter-21 lesson: a golden that fails lint/replay from selector drift is a test-plan defect to refresh (self-heal via the LLM lane), NOT a `passing→failing`. iter-36 lesson (for whoever reads J-22's replay frame): the `/research/referee-audit` **red tripwire is a PERMANENT honest state by construction** (a tautological lookahead-contaminated factor no temporal holdout can reject) — do NOT misread the loud-red tripwire as a defect; the panel is honest (throwaway ledger, real ledgers byte-identical).

## IN SCOPE

This iteration changes **no source code**. "In scope" is the verification actions the lean browser-qa step performs.

### Backend
- [ ] None — no backend source change.

### Frontend (if applicable)
- [ ] None — no frontend source change.

### Verification actions (the lean browser-qa step)
- [ ] Deterministic golden-script replay (`demo_runner.py --mode verify`) of **all 20 built, golden-scripted journeys** against `runs/goal-session-mcp-loop/journey-scripts/*.json` — the Target set (J-05, J-11) plus the Required-still-passing set — writing `reports/phase-goal-mcp-loop-iter-37-regression-replay-results.md`. This **folds in** the two accumulated goldens J-21.json (iter-35) and J-22.json (iter-36), which have never yet been run through the deterministic-replay lane.
- [ ] Merge the replay results into `reports/phase-goal-mcp-loop-iter-37-ui-test-results.md` (the single file the goal-evaluator reads).

### New user-facing capability
None — verification-only. The product is byte-identical; this pass proves the existing product still satisfies all 20 built, golden-scripted journeys.

### New information displayed
None.

### New user actions
None.

### UI surface changes
None.

### Product surface delta
None — `git diff HEAD` is empty on all product source. The only new artifacts are the per-iteration test reports and the deterministic replay evidence.

### Blueprint conformance
No new surfaces — no page added, moved, or renamed; no nav-skeleton change. A one-line **iter-37 verification-only clarification** is added to `blueprint.md` (additive documentation, no re-approval, consistent with the iter-23/25/28/29/34 verify-only clarifications).

### Data-contract additions
None. This iteration introduces no new displayed value; every registered Data Contract value keeps its single computing module and single serving endpoint unchanged, and both ledgers stay byte-identical all-FAIL (canonical Bonferroni divisor stays 8).

## OUT OF SCOPE

- **J-23 feature work** (backlog B-204 watchlist concentration X-ray) — that is iter-38, FULL. No unbuilt-journey work this pass; J-24 (B-201) and J-25 (B-205) follow it.
- **Any product source change** — `apps/backend/app/**`, `apps/frontend/**`, `config.yaml`, `apps/backend/data/seed/**`, `certified-claims.jsonl`, `staging-ledger.jsonl`, `pre-registrations.jsonl` all stay byte-identical.
- **Any new `## Evidence Claim`** — zero evidence work; the divisor stays 8; never re-submit a closed FAIL.
- **J-15 / J-16 browser verification** — no golden scripts exist (perf journeys); their engine/perf paths are git-untouched, so they are carried on byte-identity (verified via `reports/perf-budgets.md` measurements, not browser replay).
- **The QA + ux-regression report-template correction** (the recurring false "the replay lane runs in the next phase step" claim) — those agents do not even run in the lean cycle, and their templates are framework files; this is a framework-maintenance follow-up, NOT this lean product cycle's dev work (see NOTES).
- **The iter-36 non-blocking carry-forwards** (audit B1 git-add `referee-audit-report.json` at the showcase step; F1 tripwire prose / catchable temporal-leak deferred to the B-204 referee-settings sweep; B2 push the contaminated assembler's cohort-date bound into SQL; the stale wording fixes in dev-handoff / what-to-click / ui-test-plan) — carry-forwards for a future FULL iter, do NOT bundle here.
- **Running the slow 30-year backend pytest fixture** — no code changed, so there is no unit-test regression to catch; the fixture is hours-long and fork-locks the box (iter-23 / iter-30 lesson).

## DEFINITION OF DONE

- [ ] `reports/phase-goal-mcp-loop-iter-37-regression-replay-results.md` exists (the artifact iter-36's full path never wrote) and records a deterministic replay row for **every** Target and Required-still-passing journey (all 20 golden-scripted journeys), including the newly-folded J-21 and J-22.
- [ ] Every one of the 20 golden-scripted journeys — J-01, J-02, J-03, J-04, J-05, J-06, J-07, J-08, J-09, J-10, J-11, J-12, J-13, J-14, J-17, J-18, J-19, J-20, J-21, J-22 — shows PASS in the merged results. (A golden that fails lint/replay from selector drift is quarantined and re-confirmed PASS by the LLM lane — self-healing + golden refresh, NOT a regression; iter-21 lesson.)
- [ ] Target journeys J-05 and J-11 have a fresh, dedicated deterministic-replay row (the specific rows the iter-36 closure named as unverified are now formally closed).
- [ ] `reports/phase-goal-mcp-loop-iter-37-ui-test-results.md` records the merged replay results (the single file the goal-evaluator reads).
- [ ] `git diff HEAD` is empty on `apps/backend/app/**`, `apps/frontend/**`, `config.yaml`, `apps/backend/data/seed/**`, and both ledgers (`certified-claims.jsonl` + `staging-ledger.jsonl`) — verification-only; canonical Bonferroni divisor stays 8.
- [ ] No anti-goal violation introduced (all 8 upheld; both ledgers byte-identical all-FAIL).
- [ ] Dev handoff written at `docs/handoffs/goal-mcp-loop-iter-37-dev.md` documenting the no-code verification pass and the pre-replay service-readiness confirmation.

## TESTING REQUIREMENTS

- **Precondition (iter-20 + iter-35 lesson — do this BEFORE the browser-qa step):** `rm -rf apps/frontend/.next`, bring up BOTH prod-mode services (`scripts/start-backend.sh` / `scripts/start-frontend.sh`), and confirm each returns HTTP 200 before dispatching the replay lane — never run the lane against a down or stale-bundle stack (an empty evidence dir over a live stack, or a `.next/BUILD_ID` predating the source, is the anti-pattern). No source changed this iter, so the stale-bundle risk is low, but the `rm -rf .next` + rebuild + 200-probe precondition is cheap insurance against the recurring iter-20/21/35 stale-frontend trap.
- **Browser (deterministic replay lane):** all 20 golden-scripted journeys — J-01, J-02, J-03, J-04, J-05, J-06, J-07, J-08, J-09, J-10, J-11, J-12, J-13, J-14, J-17, J-18, J-19, J-20, J-21, J-22 — via `demo_runner.py --mode verify` against their on-disk golden scripts.
- **Unit/integration:** none required — zero product source diff, no code path changed. Do NOT run the slow 30-year backend fixture.
- **Error cases:** the replay lane's own self-healing must not falsely halt — a golden that fails lint is routed to the LLM lane, and a replay FAIL is re-confirmed by the LLM before it may be treated as a regression; verify any replay FAIL against the journey's OWN golden script (a stale selector is a golden/test-plan defect to refresh, not a `passing→failing` — iter-21). For J-22 specifically: the `/research/referee-audit` red tripwire is the correct, honest, permanent state — a replay assertion expecting the loud-red "expected: rejected" tripwire is PASS, not FAIL (iter-36 lesson).

## NOTES

- **Depth lean is mandatory, not optional.** The deterministic-replay lane exists only in `goal-iter-lean.sh`. A `full` iter routes through `run-phase.sh` (0 replay-lane refs) and would re-skip the replay, re-creating the iter-33/iter-36 gap. This is the evaluator's explicit reasoning and the iter-33 + iter-36 lessons.
- **This pass produces the missing artifact and pays down two iters of debt.** iter-36's `regression-replay-results.md` never existed; the goldens J-21.json (iter-35) and J-22.json (iter-36) have never run through the deterministic lane. The single deliverable that closes the CLOSURE-FAIL is that file, populated by the deterministic replay of all 20 golden-scripted journeys. The goal-evaluator (not a phase-closure step, which lean mode skips) is the effective gate and reads the merged `ui-test-results.md`.
- **Widen to a full regression (rationale, per agent instructions).** The lean cap is ~8–12, but this is the periodic "full regression of all passing journeys" moment: iters 35–36 were FULL feature iters whose required sets were only byte-identity- or live-carried (never deterministically replayed), and two new goldens accumulated un-folded. This verify-only pass is model-free/cheap, refreshes every golden, and catches selector drift accumulated across the iter-34→36 UI evolution (the new drift `/data` section and the `/research/referee-audit` governance page). So the replay set is widened to **every built journey that has a golden script** (all 20), not just the 2 the CLOSURE-FAIL named.
- **For the evaluator reading the merged evidence (iter-29 lesson):** md5-collisions among the deterministic `-verify.png` replay frames are BENIGN when journeys legitimately share an endpoint — many of these 20 end on `/evidence` or `/research/*`, so several frames will be byte-identical. Open one to confirm it is a real page (not a shared ERROR frame); don't panic at the dup-md5 scan. Replay PASS is assertion-driven, not screenshot-driven.
- **SYSTEMIC / framework flag (for the human or framework maintainer — NOT this lean cycle's dev scope):** the "required-still-passing deterministic replay" DoD line is structurally unsatisfiable by any FULL iter (`run-phase.sh` has no replay lane) and has now CLOSURE-FAILed on it TWICE (iter-33, iter-36); the QA + ux-regression report templates additionally bake a false "the replay lane runs in the next phase step" claim. Durable fixes: (a) always follow a full feature iter with a lean verify pass — what iter-34 and this iter-37 are; (b) run the closure one-liner replay explicitly inside full iters; or (c) add the replay lane to `run-phase.sh` / the full path of `run-goal.sh`. Recorded, not attempted here.
- **Next iteration:** iter-38 = FULL J-23 (backlog **B-204** watchlist concentration X-ray — pairwise correlation view, cluster groupings, sector/theme concentration, headline "effective independent bets" with its window; the ENB helper is the SAME module the evidence correlation audit uses — single source; NA over fabrication for insufficient overlap; NO Evidence Claim, divisor stays 8). Read the binding B-204 card in `docs/improvement-backlog.md` before planning. Per the systemic flag above, iter-38 should either run the replay one-liner inline or be followed by a lean verify pass so this gap does not reopen. Three journeys remain (J-23 → J-24/J-25) — a tractable path, then GOAL_ACHIEVED becomes reachable.
