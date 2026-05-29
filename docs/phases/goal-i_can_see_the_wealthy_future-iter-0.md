# Goal Iteration 0 — Baseline verify (greenfield)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** i_can_see_the_wealthy_future
- **Iteration:** 0
- **Mode:** baseline
- **Depth:** lean
- **Frontend Present:** yes
- **Target journeys:** J-01, J-02, J-03, J-04, J-05, J-06, J-07, J-08, J-09, J-10, J-11
- **Required-still-passing journeys:** none (baseline — nothing is passing yet)
- **Anti-goal reminders** (verbatim from `docs/goal.md`; no code is written this iteration, but these
  govern every iteration that follows):
  - **No lookahead.** Scoring for a snapshot dated D MUST use only price bars with date ≤ D; forward
    returns MUST use only bars with date > D. The walk-forward MUST be unit-tested to prove no future
    bar influences an as-of score. *(critical)*
  - **Snapshots are immutable.** A persisted `scanner_run` and its result rows MUST never be updated or
    overwritten after creation; forward returns live in a separate append-only table keyed to the
    snapshot. *(critical)*
  - **Single source of truth.** Each of the six canonical scores (and the A–E bucket and setup status)
    MUST be computed exactly once by the scoring/regime engine and read identically by every page; the
    API and frontend MUST NOT recompute them. The same symbol's score MUST NOT differ between two views.
    *(critical)*
  - **No magic numbers.** Every scoring weight, threshold, decision-rule cutoff, bucket edge, universe
    entry, and theme definition MUST come from the config file — no such literal in calculation code.
  - **No fabricated data.** On a data-provider failure the system MUST surface an explicit stale/
    unavailable state and MUST NOT synthesize prices or scores to force a green journey.
  - **No order/execution path.** No brokerage, order-placement, or capital-deployment code may exist or
    be reachable; Trendora is research-only. *(critical)*
  - **No secrets in source.** No hard-coded credentials, API keys, or tokens anywhere; the default seed
    path requires none, and any live-provider key is read only from the environment.
  - **Risk-Off must gate Actionable.** When the regime is Risk-Off, the scanner MUST mark zero stocks
    "Actionable" (watchlist-only). *(critical)*
  - **Scores must be explainable.** Every displayed score MUST carry its named component breakdown — no
    score may be shown as a bare number with no reasons.
  - **Honest limitations surfaced.** Breadth and new-high/new-low metrics computed from the seed
    universe MUST be labelled "universe-relative" (not full-market internals), and walk-forward
    evidence MUST be labelled as carrying survivorship bias (current-membership universe) so results
    are never overstated.
  - The frontend MUST NOT store auth tokens in `localStorage` (applies only if auth is ever added; this
    version has no auth).

## GOAL

Establish the session baseline: attempt all 11 Must-have user journeys against the current codebase and
record, per journey, whether it passes, fails, or is partial — so subsequent iterations know exactly
what must be built. No code is written this iteration.

## BACKGROUND

This is the iteration-0 **baseline assessment**, not a feature delivery. The repository has been
verified to be **greenfield**: there is no `apps/` directory, no `apps/backend` / `apps/frontend`, no
root `config.yaml`, and no prior phase specs. Therefore every Must-have journey (J-01 … J-11) is
expected to **fail / be NOT-YET-IMPLEMENTED** — there is no running app to serve any page or API. The
value of this iteration is purely diagnostic: it gives the goal-evaluator a clean per-journey starting
line (all failing) against which future iterations are measured, and it produces the coherence
**blueprint** (`runs/goal-session-i_can_see_the_wealthy_future/state/blueprint.md`) for human review
before any feature is built. The developer step is a **no-op**; the recorded result comes from the
browser-QA pass attempting each journey.

The roadmap (in `.claude/project-template.md`) anticipates this order once building starts:
iter-1 foundation (FastAPI health + config loader + SQLModel + provider abstraction + SeedProvider +
**one-shot Stooq ingest → committed frozen seed spanning a risk-on AND a risk-off stretch** + Next.js
shell) → iter-2 indicators/regime/sectors → iter-3 themes + three stock scores + bucketing + leaderboards
→ iter-4 setups/reasons/invalidation + Stock Detail → iter-5 snapshots + Scanner Runs (immutability) →
iter-6 walk-forward + forward returns + System Health → iter-7 watchlist + polish.

## IN SCOPE

### Backend
- [ ] None — baseline iteration writes no backend code.

### Frontend (if applicable)
- [ ] None — baseline iteration writes no frontend code.

### New user-facing capability
None. This iteration only records the current (empty) state of every journey.

### New information displayed
None.

### New user actions
None.

### UI surface changes
None.

### Product surface delta
None — the product does not change. This is a measurement-only pass.

### Blueprint conformance
No new surfaces. This iteration **creates** the blueprint
(`runs/goal-session-i_can_see_the_wealthy_future/state/blueprint.md`) describing the intended
Information Architecture (sidebar nav: Dashboard / Stocks / Themes / Sectors / Scanner Runs / System
Health / Watchlist, with Stock Detail and Run Detail reached from rows) and the Data Contract (the six
canonical scores + A–E bucket + setup status + forward-return aggregates, each computed once and read
everywhere). The loop pauses for human approval of that file after this baseline.

### Data-contract additions
None added by code this iteration. The full initial Data Contract is drafted in `blueprint.md` for
human approval; iter-1+ will create the canonical modules/endpoints it names.

## OUT OF SCOPE

- Writing ANY backend or frontend code, config, seed data, or tests.
- Scaffolding `apps/`, installing dependencies, or creating `config.yaml`.
- Marking journeys as pass/fail — only the goal-evaluator records journey status.
- Any work from iter-1 onward (foundation, ingest, scoring, etc.).

## DEFINITION OF DONE

- [ ] Every Must-have journey (J-01 … J-11) is attempted against the current state and its result
      (pass / partial / fail / not-implemented) is recorded with a one-line reason.
- [ ] The expected outcome — all 11 journeys failing / not-yet-implemented because the app is not built
      — is confirmed and recorded (this is success for a greenfield baseline, not a defect).
- [ ] The coherence blueprint exists at
      `runs/goal-session-i_can_see_the_wealthy_future/state/blueprint.md` and is ready for human review.
- [ ] No code was written; the working tree contains only this spec and the blueprint.
- [ ] Dev handoff written at `docs/handoffs/goal-i_can_see_the_wealthy_future-iter-0-dev.md` stating the
      developer step was an intentional no-op for the baseline.

## TESTING REQUIREMENTS

- **Browser:** Attempt each of J-01 … J-11 by visiting its canonical route (`/`, `/stocks`, `/themes`,
  `/sectors`, `/scanner-runs`, `/system-health`, `/watchlist`, and a `/stocks/[ticker]` / `/scanner-runs/[runId]`
  detail). Since no app is built or running, record each as **NOT-IMPLEMENTED / fail** with the reason
  (e.g., "no frontend/back end exists yet — greenfield"). Do **not** spend effort debugging a
  non-existent app; a single confirmation that the app/route is absent is sufficient evidence per
  journey.
- **Unit/integration:** None — there is no code to test this iteration.
- **Error cases:** N/A this iteration.

## NOTES

- Baseline-mode rationale (from `.claude/agents/goal-decomposer.md`): depth is **lean** because the
  developer agent is a no-op and the diagnostic value comes from the browser-QA step running every
  journey. For an existing project this step distinguishes "already implemented" from "yet to build";
  here it confirms the latter for all 11.
- The seed is the keystone dependency: the journeys assert **relational / structural** properties (same
  value in two places, buckets ordered, zero Actionable in Risk-Off, a number renders, filters change
  rows) — never exact score numbers — so the iter-1 seed MUST contain real history spanning **both** a
  risk-on stretch (real Actionable candidates for J-02) and a risk-off stretch (a real Risk-Off run for
  J-07). Fabricating data to force a green journey violates the "No fabricated data" anti-goal.
- No lessons-learned entries exist yet (first iteration); none to apply.
- After this baseline, `run-goal.sh` pauses for the human to review/edit/approve `blueprint.md`; resume
  with `./scripts/automation/run-goal.sh --resume --session-id i_can_see_the_wealthy_future` (or pass
  `--auto-approve-blueprint` to skip the pause).
