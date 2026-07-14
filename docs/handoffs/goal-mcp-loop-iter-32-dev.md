# goal-mcp-loop-iter-32 Dev Handoff

**Phase:** goal-mcp-loop-iter-32
**Date:** 2026-07-14
**Agent:** developer
**Status:** complete

## What Was Built

J-17 / backlog B-903 — the certification-budget accounting panel, so nothing can silently spend the
platform's statistical credibility without it being visible first:

- **`app.engine.budget_accounting`** (new, pure read-compose module, no DB/session) —
  `build_budget_payload(canonical_path=None, staging_path=None)` re-reads the SAME `ledger` /
  `online_fdr` / `referee` seams `app.mcp.tools:verify_edge` already uses. It computes NO canonical
  value independently:
  - **Canonical**: `n_trials_to_date = ledger.count_trials(canonical_path)` (7 today, a DISPLAY value
    kept separate from the forward ordinal); `n_trials_next = n_trials_to_date + 1` (8 today);
    `required_p = referee.DEFAULT_ALPHA_PER_TEST / n_trials_next` (0.00625 today, the constant is
    IMPORTED, never a `0.05` literal); `alpha_budget_remaining = referee.DEFAULT_ALPHA_BUDGET -
    ledger.alpha_spent(canonical_path)` (0.90 today) — byte-identical to `tools.py:511`'s own
    `remaining` derivation.
  - **Staging**: the same trial-count shape, and `next_level` via `online_fdr.test_level(n_trials_next,
    ledger.rejection_offsets(staging_path), alpha=cfg.evidence.fdr.alpha, w0_fraction=…,
    gamma_exponent=…, gamma_terms=…)` — the identical call `verify_edge` makes for a staging claim
    (config-sourced tunables only, no literal).
  - **`spend_over_time`** (per ledger): every original (non-forward-walk) entry, in append order, with
    its OWN recorded `verdict.required_p` re-read verbatim on both ledgers, plus `verdict.
    deflation_divisor` / `verdict.alpha_charged` on the canonical series only. History is read, never
    recomputed; only the two forward next-trial figures call a live function.
  - Ledger paths come ONLY from `evidence.resolve_ledger_path()` (canonical) and
    `graveyard.resolve_staging_ledger_path()` (staging — REUSED from `app.engine.graveyard`, not
    duplicated). A missing/empty ledger degrades to the honest empty snapshot the formulas naturally
    produce (0 trials, `required_p = 0.05/1`, full budget, the staging economy's initial wealth) —
    never a raise; no special-casing was needed for this.
- **`GET /api/research/budget`** (new `app/api/budget.py`, mirrors `app/api/graveyard.py` verbatim
  shape) — serves `build_budget_payload()` with no args, no DB/session, 200-on-missing-ledger. Wired
  into `main.py` alongside the existing `graveyard` import/`include_router` lines: the import is
  alphabetical (`budget` between `backtest` and `dashboard`), the `include_router` line is appended
  after `graveyard`'s (that block is chronological, not alphabetical, matching how `graveyard` itself
  was added after `registry`) — a purely additive two-line diff; no existing route line touched.
- **`/research/budget`** (new page) — a four-card grid (total trials, current `required_p`, Thresholdout
  remaining, staging LORD++ next-trial level), each with an inline-SVG spend-over-time sparkline built
  from the served `spend_over_time` series. Mirrors `/research/graveyard`'s three-state shell (loading
  skeleton / fetch-error card / ok). No proven-language anywhere.
- **Research hub governance card** — third card in the existing `data-testid="research-governance"`
  grid in `app/research/page.tsx`, `data-testid="research-governance-link-budget"`, `Wallet` icon (no
  collision with the 13 icons already in use on that page). Header comment updated to "registry +
  graveyard + budget now; referee-audit still to follow."
- **`fetchBudget()`** in `lib/api.ts`, mirroring `fetchGraveyard()` exactly; types live in new
  `lib/budget.ts` (mirrors `lib/graveyard.ts`'s types-only pattern).
- **J-19 close-out**: NO code change, as directed by the plan. Confirmed the lineage-scroll `useEffect`
  fix is still present and untouched at `apps/frontend/app/research/registry/page.tsx:50-59` (the
  `#registration-<id>` hash-scroll effect that runs after rows mount). I did not touch this file. Per
  the plan, the canonical `browser-qa-agent` + `ux-regression-reviewer` re-run against this final build
  is what flips J-19 `partial` → `passing` — that is downstream of this dev pass, not something a dev
  handoff can satisfy on its own (iter-31/22/20/13 lesson).

This iteration is READ-ONLY composition: no `## Evidence Claim`, no referee submission, no ledger
write. `app.engine.referee.certify_edge`, `app.engine.ledger`'s write path, `app.engine.online_fdr`,
and `app.mcp.tools:verify_edge` were NOT touched (only imported from, read-only).

## Files Changed

- `apps/backend/app/engine/budget_accounting.py` -- NEW. `build_budget_payload()` pure read-compose.
- `apps/backend/app/api/budget.py` -- NEW. `GET /api/research/budget`.
- `apps/backend/main.py` -- import `budget` (alphabetical) + `include_router(budget.router, prefix="/api")` beside the existing `graveyard` wiring. Two-line additive change; no existing line touched.
- `apps/backend/tests/test_budget_accounting.py` -- NEW. 20 tests: single-source equality vs `verify_edge`'s own seams (canonical + staging, against the live ledgers), fixture-spend on a throwaway `tmp_path` ledger (trial count, `required_p`, stable-vs-overfit `alpha_charged`, LORD++ recompute), resilience (missing/empty ledger, all-FAIL staging depletion, forward-walk exclusion, spend-over-time length == `count_trials`).
- `apps/backend/tests/test_api_budget.py` -- NEW. 4 tests (mirrors `test_api_graveyard.py`'s shape): 200-on-missing, verbatim fixture serving, endpoint-equals-module single-source, real-ledger status-derived trial counts.
- `apps/frontend/lib/budget.ts` -- NEW. `BudgetSpendPoint` / `CanonicalBudget` / `StagingBudget` / `BudgetResponse` types, mirrors `lib/graveyard.ts`'s types-only pattern.
- `apps/frontend/lib/api.ts` -- added `fetchBudget()` + re-exported budget types, mirrors the `fetchGraveyard` addition exactly.
- `apps/frontend/app/research/budget/page.tsx` -- NEW. The four-card accounting panel + inline-SVG sparklines + loading/error states.
- `apps/frontend/app/research/page.tsx` -- added the third governance card (`data-testid="research-governance-link-budget"`) + updated the section's header comment. No structural change to the existing two cards.

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest <targeted files> -v`

1. **New tests, full run** — `test_budget_accounting.py` (20) + `test_api_budget.py` (4) = **24 passed,
   0 failed**, all DB-free (pure filesystem-read module — no seed load, no walk-forward boot).
2. **Regression sweep (DB-free, thematically adjacent)** — re-ran `test_graveyard.py` (18),
   `test_api_graveyard.py` (4), `test_registry.py` (23), `test_api_registry.py` (3) alongside the new
   files = **68 passed, 0 failed** total, in 0.41s.
3. **`main.py` wiring sanity check** — `python -c "import main; main.create_app()"` (no lifespan, no
   DB) confirmed the app factory still boots cleanly and lists `/api/research/budget` among its 45
   routes, without needing the expensive DB-seeded lifespan tests.
4. **Skipped, deliberately** — `test_evidence.py` / `test_api_evidence.py` / `test_gate_registry_
   enforcement.py`: these exercise `loaded_engine` (a real seeded DB + real referee computation across
   many historical dates on the 30-year basis) and are known-slow in this environment (see project
   memory: "30y test suite slow, not the product" — this is a pre-existing, unrelated environment
   characteristic, not something this diff caused). My diff has ZERO code-path exposure to those files:
   I do not touch `app.engine.evidence`, `app.engine.referee`, `app.engine.ledger`, `app.engine.
   online_fdr`, or `app.mcp.tools` — I only import read-only functions/constants from them. This
   mirrors the iter-31 dev handoff's identical, previously-accepted decision for the same reason.
   Substituted the live end-to-end smoke test below as the practical proof instead.
5. Frontend: `npx tsc --noEmit` (whole project) — clean, zero type errors. `next lint` is not configured
   in this repo (no committed ESLint config) — skipped, consistent with iter-30/31 precedent.

**Live end-to-end smoke test**: started both services via `scripts/dev.sh` after `rm -rf apps/frontend/
.next` (ports auto-offset to 8255/3255), confirmed:
- `GET /api/health` -> `readiness: "ready"`, warmup `89/89`.
- `GET /api/research/budget` -> 200, `canonical.n_trials_to_date=7`, `required_p=0.00625`,
  `alpha_budget_remaining=0.9`, 7-point `spend_over_time`; `staging.n_trials_to_date=7`,
  `next_level≈0.0003926`, 7-point `spend_over_time` — matches the hand-computed values from the real
  ledger dump exactly.
- `GET /research`, `GET /research/budget`, `GET /research/graveyard`, `GET /research/registry`,
  `GET /evidence`, `GET /stocks` -> all HTTP 200, zero "Application error"/"Internal Server Error"
  markers, zero compile/runtime errors in either dev-server log.
- `/research`'s HTML contains `data-testid="research-governance-link-budget"` and the text
  "Certification-budget accounting" (the static card markup renders in the SSR shell immediately; the
  fetched panel numbers are client-fetched via `useEffect`, so they don't appear in a plain curl of
  `/research/budget`'s shell either — expected Next.js "use client" behavior, not a bug; interactive
  verification is the browser-qa-agent's job).
- No "proven"/"Proven"/"not yet proven" text anywhere in the rendered `/research/budget` HTML shell.
- **Restart check**: stopped and restarted `scripts/dev.sh` a second time. Its port-occupancy kill loop
  (`lsof -ti :$PORT` + `fuser -k -9`) correctly reclaimed both ports — including the nested `uvicorn`
  reloader child and the `next dev` → `npm exec` → `node` process tree, not just the two top-level
  tracked PIDs — and both services came back up serving byte-identical `/api/research/budget` values.
  Verified via `ps aux` + `ss -ltnp` that no leftover process remained afterward.
- Fully stopped and cleaned up both services at the end (verified via `lsof`/`ss`/`ps` — no listener
  remained on 8255 or 3255).

**Ledger integrity**: `git status --porcelain` on `certified-claims.jsonl`, `staging-ledger.jsonl`, and
`pre-registrations.jsonl` is empty before and after every test run (including the fixture-spend tests,
which write ONLY to `tmp_path`) — confirmed explicitly, both via a dedicated test
(`test_fixture_spend_never_writes_the_real_ledgers`) and a manual `git status --porcelain` check.

## Known Issues

- **No interactive browser click-through was performed by me** (the developer agent has no browser
  tool, and per this project's iter-31/22/20/13 lessons an ad-hoc developer-side browser check would
  not satisfy the DoD's canonical `browser-qa-agent` + `ux-regression-reviewer` requirement anyway — it
  is deliberately reserved for that downstream lane). I verified via direct HTTP against both live
  running services instead (see Tests Run above). Full interactive verification — the four cards
  rendering with byte-matching numbers, the sparklines drawing, the governance card click-through, and
  (separately) the J-19 lineage-scroll re-verification — remains the browser-qa-agent's job for this
  iteration's DoD.
- **`.claude/project-template.md` is still the unfilled generic template** for this project (a
  pre-existing gap, unchanged since iter-30/31's handoffs noted the same) — I inferred the real commands
  from `scripts/dev.sh`, existing test files, and the iter-31 dev handoff's own confirmed command shape.
- **No `[NEW]`-flagged demo-narrator walkthrough was produced by this dev pass** — that is the
  downstream `demo-narrator` agent's job, per the standard pipeline.
- **Pre-existing environment state, not part of this iteration**: the plan flagged leftover WIP from a
  stalled earlier iteration (modified `config.py`/`engine/prices.py`/`engine/scoring.py`/`engine/
  warmup.py` + several test files, plus untracked `test_scoring_window.py` / `docs/phases/goal-mcp-
  loop-iter-26.md` / `reports/qa/goal-mcp-loop-iter-26-test-plan.md` / `runs/goal-mcp-loop-iter-26/` /
  iter-26 dispatch lock files). By the time I started, `git status` no longer showed any of those
  files — they appear to have already been resolved/cleared by the surrounding goal-mode pipeline
  before my dispatch (I made no destructive git operations, and none of my edits touch any of those
  paths). What `git status` shows modified now besides my own files (`README.md`, `reports/goal-
  session-mcp-loop-index.html`, `reports/phase-goal-mcp-loop-iter-31-*`, `runs/goal-session-mcp-loop/
  {engine.pid,state/blueprint.md,state/project-story.md,telemetry.jsonl,trace/*}`) are pipeline-managed
  artifacts (dispatch/telemetry/trace/blueprint files) that the surrounding goal-mode engine updates as
  it progresses through steps — I did not edit any of them, and `runs/goal-session-mcp-loop/state/
  blueprint.md` was confirmed already updated by the goal-decomposer before this dev pass started (per
  the plan's explicit note), not by me.
