# Goal Iteration 0 — Baseline: verify every evidence-layer journey against the current codebase

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** mcp-loop
- **Iteration:** 0
- **Mode:** baseline
- **Depth:** lean
- **Frontend Present:** yes
- **Target journeys:** J-01, J-02, J-03, J-04, J-05
- **Required-still-passing journeys:** none (baseline — nothing verified yet)
- **Anti-goal reminders** (verbatim from `docs/goal.md`):
  - A score, ranking, or "edge" MUST NOT be presented as proven/confident unless it is backed by a **passing certified-claim entry** in the evidence ledger (out-of-sample, control-beating). Unbacked values MUST render a "not yet proven" state. *(critical)*
  - **Decision-quality only:** never present return promises, price targets, "buy/sell" signals, or alpha claims; never place or simulate orders. *(critical)*
  - A journey passes ONLY if the **displayed numbers are correct** — they match the engine's computation for the same as-of date — not merely that the page renders. *(critical)*
  - **No overfit edges:** any pattern surfaced as "proven" must have survived the referee (sealed out-of-sample holdout + controls + multiple-testing correction), never in-sample fit alone. *(critical)*
  - **Preserve determinism and no-lookahead:** scoring uses bars ≤ as-of; forward returns use bars > as-of; never introduce lookahead anywhere. *(critical)*
  - No iteration ships if its evidence-derived claims (if any) lack a passing referee verdict from the post-decompose gate. *(critical)*
  - No hard-coded credentials, API keys, or tokens in source files. *(critical)*

## GOAL

Establish the starting line: run all five Must-have evidence-layer journeys (J-01..J-05) against the current Trendora codebase exactly as it stands, and record for each whether it already passes, fails, or is partial — with no code changes.

## BACKGROUND

This is a **baseline assessment, not a feature delivery** — iteration 0 of the `mcp-loop` goal session. The developer step is a deliberate no-op; the value comes entirely from the browser-QA step running every journey to distinguish "already implemented" from "yet to build". This session adds a decision-quality **evidence layer** on top of the existing (GOAL_ACHIEVED) Trendora product: every user-facing score/ranking/edge should carry a visible "Proven / Not yet proven" status sourced from an append-only certified-claims **ledger**, with drill-down to the backing out-of-sample test + controls + claim id/date.

A baseline file scan (recorded in `runs/goal-session-mcp-loop/state/blueprint.md`) shows the referee + ledger **plumbing already exists** (`app.engine.referee`, `app.engine.ledger`, `app.mcp.tools:verify_edge`, and the `project-extensions/` post-decompose gate), but the **user-facing evidence surface does not**: there is no `GET /api/evidence` endpoint, no "Proven / Not yet proven" badge on any score surface, no `/evidence` ledger page, and no certified-claims ledger file yet (`runs/goal-session-mcp-loop/state/certified-claims.jsonl` is absent ⇒ an empty ledger ⇒ no signal can legitimately read "Proven"). The expectation is therefore that J-01..J-05 fail at baseline — but the browser-QA agent determines that empirically and the goal-evaluator records the verdict. No lessons exist yet (first iteration).

## IN SCOPE

### Backend
- [ ] None — verify-only. No source files are created or modified this iteration.

### Frontend (if applicable)
- [ ] None — verify-only. No source files are created or modified this iteration.

### Verification work (the actual iteration output)
- [ ] Run each of J-01..J-05 against the running app and record the actual observed result (pass / fail / partial) with concrete evidence (what was on the page, what was missing).

### New user-facing capability
None. Baseline establishes which capabilities already exist.

### New information displayed
None.

### New user actions
None.

### UI surface changes
None.

### Product surface delta
None — the product is observed, not changed.

### Blueprint conformance
No new surfaces this iteration. The blueprint (`runs/goal-session-mcp-loop/state/blueprint.md`) is created alongside this spec and records the target Information Architecture (existing nav + the planned `[NEW] Evidence` section) and Data Contract (the planned single evidence-status/certified-claim source). Nothing here adds to either.

### Data-contract additions
None. The one new contract value (evidence status / certified-claim, served by a single `GET /api/evidence`) is registered as `[TARGET]` in the blueprint for iter-1+ to build; this iteration introduces no value.

## OUT OF SCOPE

- Any code change, migration, dependency install, or config edit.
- Building the evidence badge, the `/api/evidence` endpoint, the `/evidence` page, or seeding the certified-claims ledger — those are iter-1+.
- Proposing any `## Evidence Claim` (no edge is being shipped as "proven" this iteration, so the post-decompose gate passes through automatically).
- Marking any journey as passing/failing in `journey-history.json` — only the goal-evaluator does that.

## DEFINITION OF DONE

- [ ] Every Must-have journey (J-01..J-05) is verified against the current state and its actual result is recorded with evidence.
- [ ] No code, config, or dependency changes were made (verify-only).
- [ ] No anti-goal violation introduced (none possible — no changes).
- [ ] Browser-QA results recorded for the goal-evaluator to score and seed `journey-history.json`.
- [ ] Dev handoff written at `docs/handoffs/goal-mcp-loop-iter-0-dev.md` stating "baseline verify-only — no changes" and listing the per-journey observations.

## TESTING REQUIREMENTS

- **Browser:** verify each journey against the running app (backend + frontend up). For each, record the observed outcome vs. its acceptance criterion:
  - **J-01 — Every score shows an evidence status:** visit `/stocks`; for the leaderboard rows, check whether each row's score area shows a "Proven" / "Not yet proven" evidence badge, and whether any displayed score lacks a status. *(Acceptance: no score is shown without a visible evidence status.)*
  - **J-02 — Drill into the proof behind a score:** from `/stocks`, open a stock at `/stocks/{ticker}`; check whether a "Proven" score can be expanded to reveal the out-of-sample test result, the control comparison (vs SPY/QQQ/sector ETF/random), and the certified-claim id + registration date. *(Acceptance: the user can see WHY a score is proven.)*
  - **J-03 — Unproven / noise signals honestly marked:** find a score/edge whose claim is not certified (or failed out-of-sample); check whether the UI shows "Not yet proven" (and where applicable "did not beat controls out-of-sample") rather than a confident number. *(Acceptance: unvalidated/failed signals are visibly flagged, never shown as confident.)*
  - **J-04 — Regime-conditioned evidence:** note the current market regime/phase on the Dashboard, then open a research lab or the Evidence surface for a regime-conditioned claim; check whether the evidence shown is scoped to and labeled with the regime it applies to. *(Acceptance: evidence is regime-scoped and clearly labeled.)*
  - **J-05 — Audit the evidence ledger:** click "Evidence" in the nav; check whether a list of certified claims renders (each with hypothesis, out-of-sample verdict, control comparison, registration date, forward-walk score-to-date), and whether clicking a claim links back to the surface(s) its badge backs. *(Acceptance: the user can audit every "proven" claim end to end.)*
- **Unit/integration:** none required (no code paths changed this iteration).
- **Error cases:** none required (verify-only).

## NOTES

- Record any journey that cannot be exercised because the surface is entirely absent (e.g. no `/evidence` route, no badge component) as **FAIL with reason "surface not yet implemented"** — not as blocked/NA. These are buildable offline against the committed seed and drive iter-1+.
- For the goal-evaluator: J-01..J-05 are renumbered for THIS session and are distinct from any prior-session journey IDs. Seed `journey-history.json` with these five.
- Forward guidance for iter-1+ (not this iteration): the first feature iteration should stand up the read-side evidence path end to end — `GET /api/evidence` reading the certified-claims ledger via `app.engine.ledger`, the badge component, and the `/evidence` page — so that with an empty ledger every score honestly reads "Not yet proven" (satisfies J-01/J-03/J-05 structurally before any edge is certified). Only a LATER iteration that wants a "Proven" badge needs a `## Evidence Claim` block for the post-decompose gate to certify first.
- Services: the standard goal-mode harness starts backend + frontend (project run script `./scripts/dev.sh`); the browser-QA agent should ensure both are reachable before running the journeys.
