# goal-mcp-loop-iter-36 Execution Plan

Target journey: **J-22** ("The certifier itself is calibrated — placebo + tripwire audit", backlog
**B-102**). Depth: full. This is the 4th and final Research "Governance & process" surface — the
`/research` hub (`apps/frontend/app/research/page.tsx:80-81`) already has a comment reserving its card
("referee-audit still to follow"), and `runs/goal-session-mcp-loop/state/blueprint.md` (lines 90, 268)
already carries the iter-36 Data Contract + IA rows, written by the goal-decomposer. J-22 is verbatim
present in `docs/goal.md`'s Must-have journeys — no drift from the project goal, no scope creep.

## What to Build

- New isolated referee-calibration harness `app/engine/referee_audit.py`: a **seeded null-factor
  generator** (per-date permutation of a real factor's cross-section — kills signal, preserves
  distribution) plus **one lookahead-contaminated factor** (value = the realized forward return at
  `contaminated_factor_horizon`, the "perfect crime" a broken harness would certify instantly). Each
  candidate runs through the EXISTING referee (`app.engine.referee:certify_edge` /
  `app.mcp.tools:verify_edge`) against an **ISOLATED THROWAWAY `ledger_path`** and/or a fresh in-memory
  `RefereeState` — `verify_edge` already takes an explicit `ledger_path` (`tools.py:475-493`), so the
  real ledgers and the real Thresholdout budget are NEVER touched.
- Report builder: empirical false-pass count/rate + a **binomial CI vs the configured α** (import
  `referee.DEFAULT_ALPHA_PER_TEST`, never a literal), the contaminated-factor verdict tagged **"expected:
  rejected"**, run date, and run params (seed, `n_null_trials`, `contaminated_factor_horizon`).
- New typed config block `research.referee_audit` (`n_null_trials` 200 offline / ~20 for CI, `seed`,
  `contaminated_factor_horizon`, `report_path`), default-populated so a config predating this block still
  loads.
- Persistence + single reader: `resolve_referee_audit_path()` / `write_referee_audit_report()` /
  `read_referee_audit_report()` — mirror `resolve_drift_report_path()` (iter-35) /
  `evidence.resolve_ledger_path()` exactly; missing/unparseable ⇒ honest empty/`None`, never a raise.
- **A one-off OFFLINE invocation of the harness** (the real `n_null_trials=200` run against the committed
  seed/factors) to actually materialize the persisted artifact at `report_path` — nothing in this spec
  wires a UI action to trigger it (J-22 explicitly has no new user action), so the developer must run it
  themselves as a build step. Without this, browser-qa will only ever see the honest-empty-state, not the
  real fields the DoD requires.
- New endpoint `GET /api/research/referee-audit` (thin router `app/api/referee_audit.py`, mirrors
  `app/api/budget.py` / `graveyard.py` exactly): re-reads the artifact verbatim; missing/unparseable ⇒
  200 honest empty snapshot, never 500.
- Wire the router into `apps/backend/main.py` alongside the existing budget/graveyard/registry
  registrations.
- New frontend page `/research/referee-audit` (read-only): every artifact field; a **prominent RED
  tripwire failure state** if the contaminated factor is NOT rejected (never hidden); honest empty state;
  contained "Backend unavailable" card.
- New 4th "Referee audit" card in the EXISTING `/research` "Governance & process" grouping
  (`data-testid="research-governance-link-referee-audit"`) — additive only, no nav-skeleton change, no
  reapproval filing (pre-approved at iter-30).
- `fetchRefereeAudit` in `lib/api.ts` (mirrors `fetchBudget`/`fetchGraveyard`) + response types.
- Backend tests: harness determinism/isolation/CI-math/tripwire-caught (fast, tiny synthetic fixture,
  **never** the full 30-year seed) + endpoint verbatim/honest-empty tests.
- Live re-verify the required-still-passing set **J-01, J-03, J-05, J-11, J-17, J-18, J-19, J-20** via
  browser-qa (a FULL iter has no deterministic-replay lane — the iter-35 CLOSURE-PASS pattern).
- Dev handoff at `docs/handoffs/goal-mcp-loop-iter-36-dev.md`.

### Out of scope (flag, do not build)

- Any `## Evidence Claim` / evidence work — J-22 certifies nothing, it audits the certifier; the
  post-decompose gate passes automatically.
- Any change to the real `certified-claims.jsonl`, `staging-ledger.jsonl`, `pre-registrations.jsonl`, or
  the real Thresholdout budget accounting — the dominant failure mode; must stay byte-identical.
- Tuning any referee default constant (`DEFAULT_ALPHA_PER_TEST`, `DEFAULT_ALPHA_BUDGET`, noise scale,
  etc.) — auditing ≠ tuning.
- J-23/J-24/J-25 (risk-analytics cluster) — the next cluster, deferred one-risky-journey-per-iter.
- The deterministic-replay hygiene closeout — explicitly batched into a later lean pass.

## Agents Required

- developer: yes -- implements both backend and frontend (Trendora's actual agent catalog per CLAUDE.md
  has one unified `developer` agent; there is no separate backend-data/frontend-ux agent in this project)
- backend-data: yes -- `referee_audit.py` harness, `RefereeAuditCfg` + `config.yaml` block, the new
  endpoint + `main.py` wiring, backend tests, and the one-off offline harness run that materializes the
  real artifact
- frontend-ux: yes -- `/research/referee-audit` page, the 4th governance nav card, `api.ts` fetch helper
  + types

## Frontend Present
Frontend Present: yes

## Files to Create/Modify

**Backend (new):**
- `apps/backend/app/engine/referee_audit.py` -- pure module: null-factor generator, contaminated-factor
  generator, isolated harness runner, report builder, `resolve_referee_audit_path` /
  `write_referee_audit_report` / `read_referee_audit_report`.
- `apps/backend/app/api/referee_audit.py` -- thin `GET /research/referee-audit` router (mirrors
  `app/api/budget.py` / `graveyard.py` — no logic beyond calling the single reader).
- `apps/backend/tests/test_referee_audit.py` -- harness unit tests: null generator kills signal /
  preserves distribution; contaminated-factor construction; same-seed determinism; isolation (throwaway
  ledger written, the real 3 state files untouched); binomial-CI math; report shape.
- `apps/backend/tests/test_api_referee_audit.py` -- endpoint tests: verbatim serve of a fixture artifact;
  missing/unparseable artifact ⇒ 200 empty snapshot, never 500 (mirrors `test_api_budget.py` /
  `test_api_graveyard.py`).

**Backend (modify):**
- `apps/backend/app/config.py` -- new `RefereeAuditCfg` (`n_null_trials: int = 200` boot-validated
  `>= 1`, `seed: int`, `contaminated_factor_horizon: int`, `report_path: str`), nested as
  `ResearchCfg.referee_audit` (class at `:1261`), default-populated (mirror `DriftCfg` at `:2181-2210`
  exactly, including `model_config = ConfigDict(extra="allow")` + the `@model_validator` pattern).
- `config.yaml` -- new `research.referee_audit:` block (sibling to `research.read_batch_size` /
  `research.factor_lab`, ~`:859+`): `n_null_trials: 200`, `seed`, `contaminated_factor_horizon`,
  `report_path` (suggest a path under `runs/goal-session-mcp-loop/state/`, mirroring the drift-report /
  ledger artifacts already there). CI should override `n_null_trials` down to ~20 via env/test fixture,
  never by editing this committed default.
- `apps/backend/main.py` -- import `referee_audit` from `app.api`; add
  `application.include_router(referee_audit.router, prefix="/api")` immediately after the existing
  `budget.router` registration (`:142`), same one-line goal-mcp-loop comment style already used for
  registry/graveyard/budget.

**Frontend (new):**
- `apps/frontend/app/research/referee-audit/page.tsx` -- read-only page: null-trial count, false-pass
  rate + CI, configured α, contaminated-factor verdict ("expected: rejected"), run date, run params;
  prominent RED tripwire state if uncaught; honest empty state; contained "Backend unavailable" card.

**Frontend (modify):**
- `apps/frontend/app/research/page.tsx` (~`:80-140`) -- add the 4th governance card,
  `data-testid="research-governance-link-referee-audit"`, same Card/Link/Icon shape as the
  registry/graveyard/budget cards immediately above it.
- `apps/frontend/lib/api.ts` (~`:395-420`) -- add `RefereeAuditReport`-shaped response types +
  `fetchRefereeAudit(signal?)`, mirroring `fetchBudget` / `fetchGraveyard`.

**Confirmed — do NOT touch:**
- `runs/goal-session-mcp-loop/state/blueprint.md` -- the iter-36 Data Contract row (`:268`) and IA row
  (`:90`) are ALREADY written by the goal-decomposer (verified present) — no developer edit needed.
- `app/engine/referee.py`, `app/engine/ledger.py`, `app/mcp/tools.py` -- reused verbatim (`certify_edge` /
  `verify_edge` / `RefereeState` / `count_trials` / `read_entries`); the isolation guarantee depends on
  never modifying these.
- The real `certified-claims.jsonl`, `staging-ledger.jsonl`, `pre-registrations.jsonl`, and the real
  Thresholdout budget.

## UI Evolution

- New user-facing capability: the user can open `/research/referee-audit` and see the certifier's own
  measured false-pass rate against α, plus the lookahead-tripwire result — evidence the certifier itself
  is honest, or a loud, un-hideable signal that it is not.
- New information displayed: null-trial count; empirical false-pass rate + binomial CI; configured α;
  contaminated-factor verdict ("expected: rejected"); run date; run params (seed, horizon).
- New user actions: none (read-only; the audit runs as a config-seeded offline job, not a UI action). One
  new nav card/link on `/research`.
- UI surface changes: one new page (`/research/referee-audit`); one new card in the EXISTING "Governance
  & process" grouping (now complete at 4/4: registry, graveyard, budget, referee-audit).
- Navigation changes: one new card under the already-approved Research → Governance & process grouping;
  no nav-skeleton change, no reapproval filing (pre-approved at iter-30).

## Visual Requirements

- Component patterns: reuse the existing governance-page Card/PanelTitle shape (budget-page /
  graveyard-page precedent) for the report sections; reuse the existing hub Link/Card grouping
  (`research/page.tsx:84-140`) for the new nav card — same border/hover/focus classes as
  registry/graveyard/budget, no new visual pattern invented.
- Layout: single-column report page under the standard `PageHeading` + content shape every other
  `/research/*` sub-page already uses — a stat/summary row up top, then run-parameters + verdict detail
  below.
- Key visual effects: the tripwire failure state must be LOUD and impossible to miss (mirrors iter-35's
  drift-detected treatment: `border-warn`/danger styling, never the quiet clean-state treatment) — this is
  a correctness-critical signal, not decoration.
- States to handle: (1) honest empty (no artifact persisted yet), (2) normal/clean (contaminated factor
  correctly rejected — quiet, calm styling consistent with the rest of the evidence-status language),
  (3) tripwire failure (contaminated factor NOT rejected — prominent red, never hidden), (4)
  backend-unavailable (contained card, nav intact, mirrors the existing pattern other `/research/*` pages
  already use).

## Key Test Scenarios

- The real offline audit run (the committed `n_null_trials=200` config) has actually been executed and
  its artifact persisted at the configured `report_path` — required before any browser-qa check; the
  honest-empty-state path is a distinct, separately-tested case, not a stand-in for the real run.
- Backend unit: same seed ⇒ byte-identical false-pass rate (determinism); a THROWAWAY ledger_path is
  written and the harness never opens the real `certified-claims.jsonl` / `staging-ledger.jsonl` paths
  (isolation); the lookahead-contaminated factor is REJECTED by the referee (tripwire-caught); binomial CI
  matches a hand-computed value; the CI-sized variant (~20 trials, tiny synthetic price fixture) runs in
  seconds and never imports the full 30-year seed.
- Backend endpoint: `GET /api/research/referee-audit` re-serves a fixture artifact verbatim (no
  recompute); missing/unparseable artifact ⇒ 200 honest empty snapshot, never 500.
- Isolation regression proof (the dominant failure mode — run after the real offline audit executes):
  `git diff HEAD` is EMPTY on `certified-claims.jsonl`, `staging-ledger.jsonl`, and
  `pre-registrations.jsonl`; `GET /api/evidence` still shows 0 PASS / 7 FAIL, byte-identical to before the
  audit ran.
- Browser (J-22): `/research/referee-audit` shows null-trial count, false-pass rate + CI, configured α,
  the "expected: rejected" contaminated-factor verdict, run date, and run params — all traced to the
  persisted artifact; the 4th governance card appears on `/research` and navigates correctly; confirm
  `apps/frontend/.next/BUILD_ID` postdates the new page source before trusting any "missing" observation
  (the iter-20/21/35 stale-prod-build trap).
- Browser (required-still-passing, live re-verify): J-01, J-03, J-05, J-11, J-17, J-18, J-19, J-20 all
  still pass exactly as before — no regression from the new module/endpoint/page/config block.
- Anti-goal check: no proven-language anywhere on the new panel; no credentials; the harness is bounded
  (no whole-table ORM load; no unbounded loop without a config-sourced bound).
