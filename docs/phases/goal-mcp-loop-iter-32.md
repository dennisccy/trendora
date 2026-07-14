# Goal Iteration 32 — Certification-budget accounting panel (J-17, B-903) + J-19 close-out

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** mcp-loop
- **Iteration:** 32
- **Mode:** next
- **Depth:** full
- **Frontend Present:** yes
- **Target journeys:** J-17, J-19
- **Required-still-passing journeys:** J-18, J-05, J-11, J-01, J-06, J-08, J-09
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

Make the platform's statistical-credibility budget visible before it is spent: a read-only certification-budget panel at `/research/budget` that surfaces total trials to date, the current canonical `required_p`, the Thresholdout budget remaining, and the staging LORD++ alpha-wealth — each with a spend-over-time view — re-read verbatim from the same referee/ledger accounting the certifier uses. (Also folds in the J-19 close-out: re-verify the already-in-tree graveyard→registry lineage scroll fix so J-19 flips partial→passing.)

## BACKGROUND

The J-18/J-19 governance cluster is delivered; the iter-31 evaluator's named next target is **J-17** (backlog **B-903**), the last of the four Research governance/process surfaces the iter-30 blueprint clarification pre-committed (registry → graveyard → budget → referee-audit). The honesty machinery spends real budgets every trial — the Bonferroni divisor grows (now 8), the Thresholdout charge draws down the alpha budget, LORD++ spends staging wealth — but none of it is visible, so nothing stops a future model from quietly spending the year's credibility in a month (B-903's motivation). This iteration exposes that accounting as **one payload + one panel**, re-reading the exact seams `app.mcp.tools:verify_edge` already uses (`ledger.count_trials`/`alpha_spent`/`rejection_offsets`, `online_fdr.test_level`, the `referee` constants, `config.evidence.fdr`) — never a parallel computation (B-903's named failure mode is **UI-recompute**).

**Depth = full** by the "new `/research/*` served surface + endpoint" trigger (a new backend compose module + `GET /api/research/budget` + a new page) and because the correctness acceptance needs a backend fixture test beyond browser smoke. The prior verdict was CONTINUE (not ESCALATE), so full is by scope, not escalation.

**Rubric compliance:** no journey is regressed (rule 1 N/A); coherence was COHERENCE-PASS at iter-31 so no consolidation is owed (rule 2 N/A); this ships **one** risky new surface (J-17) plus the J-19 close-out, which is a near-free re-verification rider on an already-correct, in-tree `useEffect` fix (no code reopened) — this is rule 5's "one risky journey + trivial riders," exactly as the iter-31 evaluator prescribed, not two risky journeys.

**Lessons applied (see `lessons.md`):** iter-31/22/20/13 — an audit-fix on a *rendered* surface does NOT count until the **canonical browser-qa-agent** (and `ux-regression-reviewer`) re-run against the fixed build; a `qa.md` TC-retest or an auditor self-check is not the DoD-named lane. This is why J-19 was `partial` and why J-17 must be closed by a clean canonical browser-qa run against the FINAL build. iter-25/20 — the browser-qa lane has repeatedly fail-opened (blanket-SKIP / deferred browser tests graded PASS from the unit suite); bring BOTH prod services up (`rm -rf apps/frontend/.next` first) and confirm HTTP-200 BEFORE dispatching browser-qa, and md5-scan the evidence dir for reused frames.

## IN SCOPE

### Backend
- [ ] New PURE read-compose module `app.engine.budget_accounting:build_budget_payload` (sibling of `app.engine.graveyard`) that RE-READS the certification-economy accounting — it recomputes no divisor or wealth independently:
  - **Total trials + current canonical `required_p`:** `n_trials = ledger.count_trials(<canonical>) + 1`; `required_p = referee.DEFAULT_ALPHA_PER_TEST / n_trials` (the exact value `verify_edge` computes for the next claim — `0.05 / 8 = 0.00625` today). Import the constant from `app.engine.referee`; no `0.05`/`1.0` literal.
  - **Thresholdout budget remaining:** `referee.DEFAULT_ALPHA_BUDGET - ledger.alpha_spent(<canonical>)` (the identical `remaining` derivation at `tools.py:511`).
  - **Staging LORD++ alpha-wealth / next-trial level:** `online_fdr.test_level(ledger.count_trials(<staging>) + 1, ledger.rejection_offsets(<staging>), alpha=cfg.evidence.fdr.alpha, w0_fraction=…, gamma_exponent=…, gamma_terms=…)` — the identical call `verify_edge` makes for a staging claim (config-sourced tunables, no literal).
  - **Spend-over-time series (per ledger):** walk each ledger's entries in append order and, for each recorded claim entry, re-read its OWN persisted `verdict.required_p` / `verdict.deflation_divisor` / `verdict.alpha_charged` (canonical) and the recorded staging level (staging) — history comes from the recorded verdicts, never a recomputation; only the forward next-trial bar is computed via the shared functions above.
  - Ledger paths from the existing resolvers (`evidence.resolve_ledger_path()` / `resolve_staging_ledger_path()`), never a path literal. Missing/empty ledger ⇒ honest zero/empty snapshot (0 trials, `required_p = 0.05/1`, full budget, initial wealth), never a raise.
- [ ] New endpoint `GET /api/research/budget` in a new `app/api/budget.py` (mirror `app/api/graveyard.py` exactly): serves `build_budget_payload()` verbatim, no DB/session, 200-on-missing-ledger, wired via `main.py` `include_router(..., prefix="/api")`.
- [ ] Tests (`apps/backend/tests/`):
  - **Single-source:** the payload's `n_trials`/`required_p`/`budget_remaining`/staging level equal the values derived by calling `ledger`/`online_fdr`/`referee` through the SAME seams `verify_edge` uses on the live ledgers (proves no parallel bookkeeping).
  - **Correctness / fixture spend (J-17 step 2):** append a fixture claim to a **THROWAWAY** ledger (isolated temp path, the J-22 throwaway pattern) and assert the payload figures move exactly as hand-computed (trials `n → n+1`; `required_p = 0.05/(n+1)`; a stable vs an overfit fixture charges `alpha_charged = 0` vs the per-claim cost; staging `α_t` recomputes per LORD++). The REAL `certified-claims.jsonl` + `staging-ledger.jsonl` are never touched.
  - **Resilience:** missing ledger → 200 empty; all-FAIL ledger → staging wealth depletes with no rejection replenishment; spend-over-time length == `count_trials`.

### Frontend
- [ ] New page `apps/frontend/app/research/budget/page.tsx` (mirror `research/graveyard/page.tsx`'s shape — shared `PageHeading`/`Card`/`CardContent`, one root shell, no local `layout.tsx`): renders the four figures (total trials, current `required_p`, Thresholdout budget remaining, staging LORD++ wealth) each with a spend-over-time view, from `GET /api/research/budget` only. Loading / empty / backend-unavailable states are contained (honest "—", never a blank crash). NO proven-language, NO "Proven"/"Not yet proven" badge — descriptive accounting only.
- [ ] Add a third governance card (budget) + `data-testid="research-governance-link-budget"` to the EXISTING `data-testid="research-governance"` grid in `apps/frontend/app/research/page.tsx` (the grid is already `xl:grid-cols-3`, holding registry + graveyard — the third slot fits with no layout change). Add the client fetch to `apps/frontend/lib/api.ts` (new `fetchBudget`), mirroring `fetchGraveyard`.

### New user-facing capability
The owner can see, before proposing any scan, how much statistical-credibility budget has been spent: trials to date, the current canonical bar (`required_p`), the Thresholdout budget remaining, and the staging LORD++ wealth — each over time — so nothing silently spends the year's budget (B-903).

### New information displayed
Certification-budget accounting: total canonical trials (7 today), current `required_p` (0.00625 = 0.05/8), Thresholdout budget remaining, staging LORD++ alpha-wealth / next-trial level, and a per-trial spend-over-time trajectory for each — all re-read from the recorded ledger/referee accounting.

### New user actions
None beyond navigation (read-only panel). Discoverable in ≤2 clicks: Dashboard → sidebar "Research" → `/research` governance card → `/research/budget`.

### UI surface changes
One new page `/research/budget` and one new card in the existing Research "Governance & process" grid. No other surface changes.

### Product surface delta
The Research governance grouping completes its third of four planned surfaces (registry → graveyard → **budget** → referee-audit): the platform now discloses its own statistical-spend pressure, matching its "skeptical, rigorous, honest" evidence-first mood.

### Blueprint conformance
The page lives under the EXISTING Research top-level nav section's already-approved "Governance & process" grouping (approved at iter-30; the same hub-reached ≤2-click pattern as `/research/registry` and `/research/graveyard`) — an additive page, NOT a nav-skeleton change. No `blueprint.reapproval-requested` is filed. The blueprint IA homes table gains a J-17 row and the Data Contract gains the budget-accounting composition row (both edited in `runs/goal-session-mcp-loop/state/blueprint.md` alongside this spec).

### Data-contract additions
ONE new served value — **Certification-budget accounting composition** (canonical trials + current `required_p`, Thresholdout budget remaining, staging LORD++ wealth/next level, each with a spend-over-time series). Canonical computing module: `app.engine.budget_accounting:build_budget_payload` (PURE read-compose over `app.engine.ledger:{count_trials,alpha_spent,rejection_offsets,read_entries}`, `app.engine.online_fdr:test_level`, the `app.engine.referee:{DEFAULT_ALPHA_PER_TEST,DEFAULT_ALPHA_BUDGET}` constants, and `config.evidence.fdr` — the SAME accounting `verify_edge` uses; recomputes NO canonical value). Single serving endpoint: `GET /api/research/budget`. Registered in `blueprint.md` in the same change as this spec. This is a projection/composition of already-canonical accounting — it introduces no new canonical value and never a second way to compute the divisor or wealth.

## OUT OF SCOPE

- **No `## Evidence Claim`; no claim submission of any kind against the real ledgers.** `certified-claims.jsonl`, `staging-ledger.jsonl`, and `pre-registrations.jsonl` MUST be byte-identical after this iteration (git diff empty); the canonical Bonferroni divisor stays 8. The fixture-spend test writes ONLY to a throwaway temp ledger.
- **Do NOT touch the accounting itself** (B-903 "★ Do NOT touch"): no edit to `referee.py`, `ledger.py`, `online_fdr.py`, or the `verify_edge` derivation — the panel only READS them.
- **Do NOT reopen the J-19 graveyard implementation.** The lineage-scroll `useEffect` fix (`apps/frontend/app/research/registry/page.tsx:43-58`) is already in the tree; this iteration only re-verifies it via the canonical browser-qa lane.
- No per-family budget breakdown (B-404 is a future card) — show the global accounting only.
- No alerts / threshold-crossing notifications (B-302) — out of B-903's scope.
- No nav-skeleton change; no changes to `/evidence`, `proven_signals`, or the "Proven" badge; no new proven-language anywhere.

## DEFINITION OF DONE

- [ ] **J-17 passes via browser-qa-agent:** `/research/budget` renders total trials, current `required_p`, Thresholdout budget remaining, and staging LORD++ wealth, each with a spend-over-time view, and the displayed figures byte-match the payload from `GET /api/research/budget`.
- [ ] **J-19 flips partial→passing:** the canonical browser-qa lane records a passing UT-07 frame for the graveyard→registry lineage deep-link — the target registry row scrolls into view (scrollY > 0) on SPA navigation.
- [ ] Required-still-passing journeys J-18, J-05, J-11, J-01, J-06, J-08, J-09 remain green (replay / browser-qa; numbers byte-match the ledger read on disk).
- [ ] **Single-source (no UI-recompute):** a backend test asserts the payload's `n_trials`/`required_p`/`budget_remaining`/staging level equal the values `verify_edge`'s own seams produce on the live ledgers.
- [ ] **Correctness (fixture spend):** a backend test on a THROWAWAY ledger shows the figures move exactly as hand-computed after an appended fixture claim; the real ledgers are untouched.
- [ ] **Resilience:** `GET /api/research/budget` returns 200 with an honest zero/empty snapshot on a missing/empty ledger (never 500); a backend-down frontend shows one contained error card with nav intact (no blank app-error page); no unbounded whole-table ORM load introduced.
- [ ] Both real evidence ledgers + `pre-registrations.jsonl` are byte-identical (git diff empty); divisor stays 8; no `## Evidence Claim` (the post-decompose gate passes automatically).
- [ ] No proven-language on the budget panel (no "Proven"/"Not yet proven" badge; anti-goal #1 upheld).
- [ ] Unit/integration tests pass; no regressions in existing suites.
- [ ] Dev handoff written at `docs/handoffs/goal-mcp-loop-iter-32-dev.md`.

## TESTING REQUIREMENTS

- **Browser (named journeys by ID):**
  - **J-17** — `/research/budget`: the four figures render with values matching the served payload; discoverable in ≤2 clicks from the Research governance grid; no proven-language; backend-unavailable state is a contained card.
  - **J-19** — a passing UT-07 frame: from `/research/graveyard`, clicking a row's lineage link lands on `/research/registry#registration-<id>` AND scrolls the target row into view (scrollY > 0).
  - **Regression re-verify:** J-18 (`/research/registry` 11 rows / 5 cols, `ma_stack` "closed"), J-05 (`/evidence` 7 FAIL cards, numbers byte-match the ledger), J-01 (`/stocks` leaderboard evidence badges, no crash), J-06/J-08/J-09 (their `/evidence` claim rows FAIL, byte-matching the ledger).
- **Unit/integration (code paths):** `budget_accounting.build_budget_payload` — single-source equality vs `verify_edge`'s seams; fixture-spend on a throwaway ledger (trials `n→n+1`, `required_p = 0.05/(n+1)`, stable vs overfit `alpha_charged`, staging `α_t` per LORD++); spend-over-time series length == `count_trials` and each historical point re-reads the recorded verdict fields; missing/empty-ledger honest snapshot. `GET /api/research/budget` returns 200 verbatim.
- **Error cases (must be rejected / handled honestly):** missing ledger file (→ 200 zero snapshot, not 500); empty ledger (→ zero snapshot); all-FAIL ledger (staging wealth depletes, no replenishment); backend down (contained frontend error card, nav intact). The fixture test MUST NOT write to the real ledgers.

## NOTES

- **Single-source is the load-bearing acceptance.** B-903's failure mode is "UI-recompute": the panel must call the exact `ledger`/`online_fdr`/`referee` functions the referee uses, and read recorded verdict fields for history — never re-implement the divisor or LORD++ recursion. The single-source test is the guard.
- **The `partial`-trap discipline (iter-31/22/20/13 lessons):** if the auditor applies any fix to a rendered surface (the budget panel or the registry scroll), the canonical `browser-qa-agent` + `ux-regression-reviewer` MUST be re-run against the fixed build before closure — a `qa.md` TC-retest or an auditor self-check is not the DoD-named lane. Otherwise J-17 lands `partial` and iter-33 pays the re-verification tax.
- **Pre-empt the browser-qa fail-open (iter-25/20 lessons):** `rm -rf apps/frontend/.next`, bring BOTH prod-mode services up, confirm HTTP-200 BEFORE dispatching browser-qa; the lane must actually RUN (not blanket-SKIP or defer to the unit suite); md5-scan the evidence dir for reused/relabeled frames.
- **Scan-report path check (iter-27 lesson) for the evaluator:** any CRITICAL secret findings under the vendored `incredible_auto_dev/` subtree are planted framework test fixtures, not product anti-goal-#7 violations — only findings under `apps/`, `config.yaml`, `data/`, product `scripts/` can be a product secret.
- **Walkthrough (journey acceptance):** the showcase chain should produce a `[NEW]`-flagged budget-panel walkthrough viewable via `demo.sh mcp-loop --session-live` (demo-narrator, post-pipeline) — not a code deliverable, noted here so it is not missed.
- GOAL_ACHIEVED remains out of reach after this iteration: J-20, J-21, J-22, J-23, J-24, J-25 are still unbuilt (one risky surface per iter). Best next target after J-17: the daily-ops keystone **J-20** (single daily preflight verdict, B-301) or the certifier-audit **J-22** (B-102, the fourth governance surface).
