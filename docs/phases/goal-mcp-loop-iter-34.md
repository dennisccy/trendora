# Goal Iteration 34 — Deterministic regression-replay closeout (close the iter-33 CLOSURE-FAIL replay gap)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** mcp-loop
- **Iteration:** 34
- **Mode:** next
- **Depth:** lean
- **Frontend Present:** yes
- **Target journeys:** J-20
- **Required-still-passing journeys:** J-01, J-02, J-03, J-04, J-05, J-06, J-07, J-08, J-09, J-10, J-11, J-12, J-13, J-14, J-17, J-18, J-19
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

No new user-visible change: run the deterministic golden-script regression replay that iter-33's full-pipeline path structurally skipped, re-verifying that all 17 built, golden-scripted journeys are still green — closing the iter-33 CLOSURE-FAIL replay gap with **zero** product change before J-21 feature work resumes.

## BACKGROUND

iter-33 was CONTINUE but ended **CLOSURE-FAIL** on a single, narrow Definition-of-Done line: 6 of the 7 required-still-passing journeys (J-01/J-02/J-04/J-05/J-13/J-18) were never deterministically replayed — they were only byte-identity-carried — because a **FULL** iteration routes through `run-phase.sh`, which has **zero** replay-lane machinery. That lane lives **only** in `goal-iter-lean.sh` (the lean path). Confirmed on disk: `reports/phase-goal-mcp-loop-iter-33-regression-replay-results.md` does not exist. J-20's own evidence was clean, so it flipped to `passing`; the replay gap is a low-risk process/evidence gap a cheap lean pass closes. This is exactly what the iter-33 evaluator recommended for iter-34.

**Depth is `lean`, and lean is MANDATORY here** (not merely allowed): the deterministic-replay lane exists only in `goal-iter-lean.sh`; a `full` iter would re-route through `run-phase.sh` (0 replay-lane refs) and re-skip the replay, re-creating the exact iter-33 gap (the evaluator's explicit reasoning). This is a verification-only pass — the developer step is a no-op (no code), and the value comes from the browser-qa step's replay lane. Prior verdict was CONTINUE (not ESCALATE), so no forced-full applies.

**Applied lessons.** iter-33 lesson (directly): a FULL iteration's "required-still-passing deterministic replay" DoD line is structurally *unsatisfiable* — confirm `regression-replay-results.md` actually exists rather than trusting the checkbox; this pass produces exactly that artifact. iter-23 lesson: do NOT pin an unsatisfiable DoD gate — the lean cycle skips phase-closure-auditor, so this spec's DoD is the artifacts the lean cycle actually writes (the merged `ui-test-results.md` the goal-evaluator reads), never a "CLOSURE-PASS" step.

**Widen to a full regression (rationale, per agent instructions).** The lean cap is ~8–12, but iters 30–33 were four consecutive FULL iters whose required sets were all only byte-identity-carried (never deterministically replayed). This verify-only pass is the periodic "full regression of all passing journeys" moment: it is model-free/cheap, and it refreshes every golden and catches selector drift accumulated across the iter-22→33 UI evolution (new layout-level preflight banner, budget/graveyard/registry pages, availability-legend changes). So the Required-still-passing set is widened to **every built journey that has a golden script** (all 17), not just the 6 the CLOSURE-FAIL named.

## IN SCOPE

This iteration changes **no source code**. "In scope" is the verification actions the lean browser-qa step performs.

### Backend
- [ ] None — no backend source change.

### Frontend (if applicable)
- [ ] None — no frontend source change.

### Verification actions (the lean browser-qa step)
- [ ] Deterministic golden-script replay (`demo_runner.py --mode verify`) of the 17 Required-still-passing journeys against `runs/goal-session-mcp-loop/journey-scripts/*.json`, writing `reports/phase-goal-mcp-loop-iter-34-regression-replay-results.md`.
- [ ] LLM browser-qa re-confirmation of the single Target journey J-20 (the cross-cutting preflight banner) on the final/merged tree.
- [ ] Merge replay + LLM results into `reports/phase-goal-mcp-loop-iter-34-ui-test-results.md` (the single file the goal-evaluator reads).

### New user-facing capability
None — verification-only. The product is byte-identical; this pass proves the existing product still satisfies all 17 built journeys.

### New information displayed
None.

### New user actions
None.

### UI surface changes
None.

### Product surface delta
None — `git diff HEAD` is empty on all product source. The only new artifacts are the per-iteration test reports and the deterministic replay evidence.

### Blueprint conformance
No new surfaces — no page added, moved, or renamed; no nav-skeleton change. A one-line **iter-34 verification-only clarification** is added to `blueprint.md` (additive documentation, no re-approval, consistent with the iter-23/25/28/29 verify-only clarifications).

### Data-contract additions
None. This iteration introduces no new displayed value; every registered Data Contract value keeps its single computing module and single serving endpoint unchanged, and both ledgers stay byte-identical all-FAIL (canonical Bonferroni divisor stays 8).

## OUT OF SCOPE

- **J-21 feature work** (backlog B-304 live-vs-seed drift monitor) — that is iter-35, FULL. No unbuilt-journey work this pass.
- **Any product source change** — `apps/backend/app/**`, `apps/frontend/**`, `config.yaml`, `apps/backend/data/seed/**`, `certified-claims.jsonl`, `staging-ledger.jsonl`, `pre-registrations.jsonl` all stay byte-identical.
- **Any new `## Evidence Claim`** — zero evidence work; the divisor stays 8; never re-submit a closed FAIL.
- **The QA + ux-regression report-template correction** (the false "the replay lane runs in the next phase step" claim) — those agents do not even run in the lean cycle, and their templates are framework files; this is a framework-maintenance follow-up, NOT this lean product cycle's dev work (see NOTES).
- **J-15 / J-16 browser verification** — no golden scripts exist (perf journeys); their engine/perf paths are git-untouched, so they are carried on byte-identity (verified via `reports/perf-budgets.md` measurements, not browser replay).
- **Running the slow 30-year backend pytest fixture** — no code changed, so there is no unit-test regression to catch; the fixture is hours-long and fork-locks the box (iter-23 / iter-30 lesson).

## DEFINITION OF DONE

- [ ] `reports/phase-goal-mcp-loop-iter-34-regression-replay-results.md` exists (the artifact absent in iter-33) and records a deterministic replay row for every Required-still-passing journey.
- [ ] Every Required-still-passing journey — J-01, J-02, J-03, J-04, J-05, J-06, J-07, J-08, J-09, J-10, J-11, J-12, J-13, J-14, J-17, J-18, J-19 — shows PASS in the merged results. (A golden that fails lint/replay from selector drift is quarantined and re-confirmed PASS by the LLM lane — self-healing + golden refresh, NOT a regression; iter-21 lesson.)
- [ ] Target journey J-20 re-confirmed `passing` via browser-qa on the final tree: the GO preflight banner renders and content is not obscured; no regression of the cross-cutting chrome.
- [ ] `reports/phase-goal-mcp-loop-iter-34-ui-test-results.md` merges the replay + LLM results (the single file the goal-evaluator reads).
- [ ] `git diff HEAD` is empty on `apps/backend/app/**`, `apps/frontend/**`, `config.yaml`, `apps/backend/data/seed/**`, and both ledgers (`certified-claims.jsonl` + `staging-ledger.jsonl`) — verification-only; canonical Bonferroni divisor stays 8.
- [ ] No anti-goal violation introduced (all 8 upheld; both ledgers byte-identical all-FAIL).
- [ ] Dev handoff written at `docs/handoffs/goal-mcp-loop-iter-34-dev.md` documenting the no-code verification pass and the pre-replay service-readiness confirmation.

## TESTING REQUIREMENTS

- **Precondition (iter-20 lesson — do this BEFORE the browser-qa step):** `rm -rf apps/frontend/.next`, bring up BOTH prod-mode services (`scripts/start-backend.sh` / `scripts/start-frontend.sh`), and confirm each returns HTTP 200 before dispatching the replay/LLM lanes — never run the lane against a down or stale-bundle stack (empty evidence dir over a live stack is the anti-pattern).
- **Browser (deterministic replay lane):** J-01, J-02, J-03, J-04, J-05, J-06, J-07, J-08, J-09, J-10, J-11, J-12, J-13, J-14, J-17, J-18, J-19 via `demo_runner.py --mode verify` against their on-disk golden scripts.
- **Browser (LLM lane):** J-20 — the preflight banner (GO quiet green; DEGRADED/NO-GO loud with reasons; NO-GO states "do not rely on today's board") on the merged tree, single-source (one `/api/health` poll, no per-page recompute).
- **Unit/integration:** none required — zero product source diff, no code path changed. Do NOT run the slow 30-year backend fixture.
- **Error cases:** the replay lane's own self-healing must not falsely halt — a golden that fails lint is routed to the LLM lane, and a replay FAIL is re-confirmed by the LLM before it may be treated as a regression; verify any replay FAIL against the journey's OWN golden script (a stale selector is a golden/test-plan defect to refresh, not a `passing→failing`).

## NOTES

- **Depth lean is mandatory, not optional.** The deterministic-replay lane exists only in `goal-iter-lean.sh`. A `full` iter routes through `run-phase.sh` (0 replay-lane refs) and would re-skip the replay, re-creating the iter-33 gap. This is the evaluator's explicit reasoning and the iter-33 lesson.
- **This pass produces the missing artifact.** iter-33's `regression-replay-results.md` never existed (confirmed absent). The single deliverable that closes the CLOSURE-FAIL is that file, populated by the deterministic replay of the Required-still-passing set. The goal-evaluator (not a phase-closure step, which lean mode skips) is the effective gate and reads the merged `ui-test-results.md`.
- **SYSTEMIC / framework flag (for the human or framework maintainer — NOT this lean cycle's dev scope):** (1) the QA + ux-regression report templates bake a false "the replay lane runs in the next phase step" claim; (2) the "required-still-passing deterministic replay" DoD line is structurally unsatisfiable by any FULL iter (`run-phase.sh` has no replay lane). Durable fixes: (a) always follow a full feature iter with a lean verify pass — what iter-34 is; (b) run the closure one-liner replay explicitly inside full iters; or (c) add the replay lane to `run-phase.sh` / the full path of `run-goal.sh`. Recorded, not attempted here.
- **For the evaluator reading the merged evidence (iter-29 lesson):** md5-collisions among the deterministic `-verify.png` replay frames are BENIGN when journeys legitimately share an endpoint — many of these 17 end on `/evidence` or `/research/*`, so several frames will be byte-identical. Open one to confirm it is a real page (not a shared ERROR frame); don't panic at the dup-md5 scan. Replay PASS is assertion-driven, not screenshot-driven.
- **Next iteration:** iter-35 = FULL J-21 (backlog B-304 live-vs-seed drift monitor), which feeds the J-20 preflight verdict via the `compute_preflight` `_apply(...)` extensibility seam. Per the systemic flag above, iter-35 should either run the replay one-liner inline or be followed by a lean verify pass so this gap does not reopen. ~5 one-surface iterations (J-21 → J-22 → J-23/J-24/J-25) then close the goal.
- **Non-blocking carry-forwards from iter-33 (do NOT bundle into this verify pass — they belong to a future FULL iter):** audit B1 (autouse `conftest.py` `READINESS_VERDICT_HISTORY_PATH` redirect so suite runs stop appending to the untracked `preflight-verdict-history.jsonl`); B2 (thread the already-computed readiness dict into `compute_preflight` — drop the redundant second `compute_readiness` on the ~2 s poll); T1 (background `pytest tests/test_readiness.py tests/test_health.py -v` to put the preflight correctness matrix on-record); readme-maintainer preflight + budget-panel bullets.
