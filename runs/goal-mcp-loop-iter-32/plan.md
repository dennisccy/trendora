# goal-mcp-loop-iter-32 Execution Plan

Certification-budget accounting panel (J-17, backlog B-903) + J-19 close-out re-verification.
Depth: full (new backend compose module + new endpoint + new page; correctness needs a backend
fixture test beyond browser smoke). No `## Evidence Claim` this iteration — the post-decompose
gate passes automatically.

## What to Build

- **`app.engine.budget_accounting:build_budget_payload`** (new, pure read-compose, sibling of
  `app.engine.graveyard`) — re-reads the certification-economy accounting `app.mcp.tools:verify_edge`
  already uses. Computes NO canonical value independently:
  - Canonical: `n_trials_next = ledger.count_trials(canonical_path) + 1`; display "total trials to
    date" = `ledger.count_trials(canonical_path)` (today 7) separately from the `required_p` formula
    input `n_trials_next` (today 8) — **do not conflate the two**; `required_p =
    referee.DEFAULT_ALPHA_PER_TEST / n_trials_next` (today `0.05/8 = 0.00625`, imported constant, no
    literal); Thresholdout remaining = `referee.DEFAULT_ALPHA_BUDGET - ledger.alpha_spent(canonical_path)`.
  - Staging: LORD++ next-trial level via `online_fdr.test_level(ledger.count_trials(staging_path) + 1,
    ledger.rejection_offsets(staging_path), alpha=cfg.evidence.fdr.alpha, w0_fraction=cfg.evidence.fdr.w0_fraction,
    gamma_exponent=cfg.evidence.fdr.gamma_exponent, gamma_terms=cfg.evidence.fdr.gamma_terms)` — the
    identical call `tools.py` makes for a staging claim (config-sourced tunables only).
  - Spend-over-time (per ledger): walk `ledger.read_entries(path)` in append order (skip
    `type == FORWARD_WALK_TYPE` entries, same exclusion `graveyard.py`/`evidence.py` already use);
    for each claim entry re-read its OWN persisted `verdict["required_p"]` /
    `verdict["deflation_divisor"]` / `verdict["alpha_charged"]` verbatim (canonical) and
    `verdict["required_p"]` (the recorded staging level at that trial) — **history is read from the
    ledger, never recomputed**; only the forward next-trial bar uses the live functions above.
  - Ledger paths ONLY from `evidence.resolve_ledger_path()` / `graveyard.resolve_staging_ledger_path()`
    (both already exist — reuse, don't duplicate). Missing/empty ledger → honest zero/empty snapshot
    (0 trials, `required_p = 0.05/1`, full budget, initial wealth), never a raise.
  - Verified field names against the real ledgers this session: sample entries confirm
    `verdict.required_p`, `verdict.deflation_divisor`, `verdict.alpha_charged`, `verdict.deflation`
    all exist exactly as named (canonical divisor 1, staging deflation `"lord++"`).
- **`GET /api/research/budget`** (new `app/api/budget.py`, mirror `app/api/graveyard.py` verbatim
  shape) — serves `build_budget_payload()` with no args, no DB/session, 200-on-missing-ledger. Wire
  in `main.py` alongside the existing `graveyard` import/`include_router` lines (alphabetical,
  purely additive two lines — do not touch any existing route line).
- **`/research/budget`** (new page, mirror `/research/graveyard/page.tsx`'s three-state shell:
  loading skeleton / fetch-error card / ok) — renders the four figures each with a spend-over-time
  view, reading only `GET /api/research/budget`. No proven-language anywhere.
- **Research hub governance card** — third card in the EXISTING `data-testid="research-governance"`
  grid in `app/research/page.tsx` (already `xl:grid-cols-3`, currently 2/3 full — registry,
  graveyard), `data-testid="research-governance-link-budget"`, pick an unused lucide icon (current
  file already uses `Archive, ArrowRight, BookMarked, Boxes, Gauge, GitCompareArrows, Layers,
  LineChart, Microscope, Thermometer, TrendingDown, TrendingUp, Waves` — avoid collisions, e.g.
  `Wallet`/`PiggyBank`/`Scale`).
- **`fetchBudget()`** in `lib/api.ts`, mirroring `fetchGraveyard()` exactly (types either inline or
  in a new `lib/budget.ts` mirroring `lib/graveyard.ts`).
- **J-19 close-out: re-verification only, NO code change.** The lineage-scroll `useEffect` fix
  (`apps/frontend/app/research/registry/page.tsx:43-58`) is already in the tree (confirmed present
  this session, applied during the iter-31 audit) — it must NOT be reopened. This iteration's job is
  to get a **canonical browser-qa-agent** run (+ `ux-regression-reviewer`) against the FINAL iter-32
  build to record a passing UT-07 frame (deep-link click → `scrollY > 0` on the target row), which is
  what flips J-19 from `partial` (journey-history.json, since iter-31) to `passing`. A `qa.md`
  TC-retest or an auditor self-check does NOT satisfy this per the iter-31/22/20/13 lessons.
- **Blueprint already updated — no dev action needed.** Confirmed this session:
  `runs/goal-session-mcp-loop/state/blueprint.md` already carries the J-17 IA row (line 85), the
  Certification-budget accounting Data Contract row (line 114), and the iter-32 clarification
  paragraph (line 254), written by the goal-decomposer when it authored the phase spec. Do not
  duplicate or re-edit this.

## Agents Required

- backend-data: yes -- new `app/engine/budget_accounting.py` + `app/api/budget.py` + `main.py`
  wiring + two new backend test files (single-source equality, fixture-spend on a throwaway ledger,
  resilience).
- frontend-ux: yes -- new `/research/budget` page, `fetchBudget` in `lib/api.ts`, third governance
  card in `app/research/page.tsx`. No backend-affecting frontend logic (pure display of the served
  payload).

(Single `developer` agent dispatch handles both backend-data and frontend-ux work per this
project's normal pattern — both streams are yes.)

## Frontend Present

Frontend Present: yes

## Files to Create/Modify

- `apps/backend/app/engine/budget_accounting.py` -- NEW. `build_budget_payload()` pure read-compose (no DB/session).
- `apps/backend/app/api/budget.py` -- NEW. `GET /api/research/budget`, mirrors `app/api/graveyard.py`.
- `apps/backend/main.py` -- import `budget` + `include_router(budget.router, prefix="/api")`, two-line additive change beside the existing `graveyard` wiring.
- `apps/backend/tests/test_budget_accounting.py` -- NEW. Single-source equality vs `verify_edge`'s own seams; fixture-spend on a throwaway `tmp_path` ledger; resilience (missing/empty/all-FAIL).
- `apps/backend/tests/test_api_budget.py` -- NEW. Endpoint 200-on-missing, verbatim serving, endpoint-equals-module (mirrors `test_api_graveyard.py`'s four-test shape).
- `apps/frontend/lib/budget.ts` -- NEW (optional; may inline into `lib/api.ts` instead, mirroring how graveyard types are structured). Response/entry types only, no logic.
- `apps/frontend/lib/api.ts` -- add `fetchBudget()` + type re-exports, mirrors the `fetchGraveyard` addition exactly.
- `apps/frontend/app/research/budget/page.tsx` -- NEW. Four-figure panel + spend-over-time views + loading/error/empty states.
- `apps/frontend/app/research/page.tsx` -- add third governance card (`data-testid="research-governance-link-budget"`); update the section header comment ("registry + graveyard + budget now; referee-audit still to follow").
- **Do NOT touch:** `apps/backend/app/engine/referee.py`, `apps/backend/app/engine/ledger.py`, `apps/backend/app/engine/online_fdr.py`, `apps/backend/app/mcp/tools.py`'s `verify_edge`, `apps/frontend/app/research/registry/page.tsx` (the J-19 fix is already correct in-tree — re-verify, don't reopen), `runs/goal-session-mcp-loop/state/blueprint.md` (already updated).

## UI Evolution

- New user-facing capability: the owner can see, before proposing any new scan, how much
  statistical-credibility budget has already been spent — a read-only accounting panel.
- New information displayed: total canonical trials (7 today), current canonical `required_p`
  (0.00625 = 0.05/8), Thresholdout alpha-budget remaining, staging LORD++ alpha-wealth/next-trial
  level — each with a per-trial spend-over-time trajectory, re-read verbatim from the recorded
  ledger/referee accounting.
- New user actions: none beyond navigation (read-only panel, no forms/mutations).
- UI surface changes: one new page `/research/budget`; the existing Research "Governance & process"
  grid gains its third of three planned cards (registry → graveyard → **budget**).
- Navigation changes: none to the persistent sidebar; reachable in ≤2 clicks (Research hub →
  Governance & process → Budget card). No nav-skeleton change, no `blueprint.reapproval-requested`
  needed (the grouping was already approved at iter-30).

## Visual Requirements

- Component patterns: reuse `PageHeading` + `Card`/`CardContent` exactly as
  `/research/graveyard/page.tsx` and `/research/registry/page.tsx` do; the new governance card
  copies the existing `Link` + icon + title + description block in `app/research/page.tsx` verbatim
  in structure.
- Layout: a simple content column (no sidebar) — e.g. a 2x2 or 1x4 grid of compact stat cards, one
  per figure (total trials, `required_p`, Thresholdout remaining, staging wealth), each card holding
  its spend-over-time view. Matches the plain, content-column layout of `/research/graveyard` and
  `/research/registry` (not the dashboard's denser grid).
- Key visual effects: minimal, matching the existing Research governance pages — `border-border
  bg-surface` cards, no glassmorphism/glow (this project's data-dense, evidence-first, "skeptical,
  rigorous, honest" mood per `docs/goal.md`'s Design Direction).
- Spend-over-time view: a compact per-metric mini-trend, not a primary interactive chart — either a
  small inline SVG sparkline or a `lightweight-charts` `LineSeries` (already a project dependency,
  used by `price-chart.tsx`/`index-regime-chart.tsx`); pick whichever is simpler to keep the panel
  lightweight for 4 small series.
- States to handle: loading skeleton (mirror `GraveyardSkeleton`); fetch-error card ("Backend
  unavailable", nav intact, mirror `graveyard/page.tsx`'s error `Card`); honest zero/empty snapshot
  when the payload reports 0 trials (never a blank/crash render) — this is a real possible state per
  the resilience requirement, not just a defensive stub.
- No badges: explicitly NO "Proven"/"Not yet proven" `Badge` anywhere on this page (anti-goal #1;
  spec OUT OF SCOPE). Numbers are descriptive accounting only.

## Key Test Scenarios

- **Single-source (backend):** `build_budget_payload()`'s trial counts / `required_p` / Thresholdout
  remaining / staging next-trial level equal values independently derived by calling the SAME
  `ledger` / `online_fdr` / `referee` seams `verify_edge` uses, against the live ledgers.
- **Fixture-spend (backend):** append one fixture claim to a THROWAWAY `tmp_path` ledger (never the
  real `certified-claims.jsonl`/`staging-ledger.jsonl`); assert trials `n → n+1`, `required_p =
  0.05/(n+1)`, a stable fixture charges `alpha_charged = 0` vs an overfit fixture charging the
  per-claim cost, staging level recomputes per LORD++. `git diff` on both real ledgers stays empty
  after the test run.
- **Resilience (backend):** missing/empty ledger → `GET /api/research/budget` returns 200 with an
  honest zero/empty snapshot (never 500); all-FAIL ledger → staging wealth depletes with no
  rejection replenishment; spend-over-time series length equals `count_trials` for that ledger.
- **Endpoint single-source (backend):** `GET /api/research/budget` serves `build_budget_payload()`
  verbatim (byte-equal, not just shape-equal).
- **J-17 (browser):** discover `/research/budget` in ≤2 clicks from the Research hub; the four
  figures render and byte-match the live `GET /api/research/budget` payload; no "Proven"/"Not yet
  proven" text anywhere on the page; a backend-down state shows one contained error card with nav
  intact (no blank app-error page).
- **J-19 (browser, canonical browser-qa-agent run against the FINAL build — not a self-check):**
  from `/research/graveyard`, click a row's lineage link; assert it lands on
  `/research/registry#registration-<id>` AND `window.scrollY > 0` (the target row scrolled into
  view). This is a re-verification of an already-in-tree fix, not new code.
- **Regression re-verify (browser or replay):** J-18 (`/research/registry` 11 rows/5 cols, `ma_stack`
  "closed"), J-05 (`/evidence` 7 FAIL cards byte-match the ledger), J-01 (`/stocks` leaderboard
  evidence badges render, no crash), J-06/J-08/J-09 (their `/evidence` claim rows FAIL, byte-matching
  the ledger).
- **Ledger integrity:** `certified-claims.jsonl`, `staging-ledger.jsonl`, `pre-registrations.jsonl`
  byte-identical before/after (`git diff` empty); canonical Bonferroni divisor stays 8; no
  `## Evidence Claim` submitted this iteration.

## Out of Scope (carried from the phase spec — do not implement)

- No edits to `referee.py`, `ledger.py`, `online_fdr.py`, or the `verify_edge` derivation — the
  panel only reads them.
- No reopening the J-19 graveyard/registry implementation — the `useEffect` fix is already correct.
- No per-family budget breakdown (future card B-404); no alerts/threshold-crossing notifications
  (future B-302) — global accounting only.
- No nav-skeleton change; no changes to `/evidence`, `proven_signals`, or the "Proven" badge; no new
  proven-language anywhere.
- No `## Evidence Claim` / no submission of any kind against the real ledgers.

## Pre-existing environment note (not part of this iteration's scope)

The working tree has uncommitted changes unrelated to iter-32: modified
`apps/backend/app/{config.py,engine/prices.py,engine/scoring.py,engine/warmup.py}` + several test
files, plus untracked `apps/backend/tests/test_scoring_window.py`,
`docs/phases/goal-mcp-loop-iter-26.md`, `reports/qa/goal-mcp-loop-iter-26-test-plan.md`,
`runs/goal-mcp-loop-iter-26/`, and dispatch lock files under
`runs/goal-session-mcp-loop/dispatch/`. This looks like leftover WIP from a stalled/parked earlier
iteration (the touched files match the goal.md "fast platform" performance direction, not anything
in this iteration's spec) and is unrelated to J-17/J-19. The developer should scope their diff/commit
strictly to the files listed above, leave this pre-existing state alone (no destructive git ops), and
flag it in the dev handoff rather than silently absorbing or discarding it.
