# goal-mcp-loop-iter-36 Dev Handoff

**Phase:** goal-mcp-loop-iter-36
**Date:** 2026-07-14
**Agent:** developer
**Status:** complete

## What Was Built

J-22 (backlog B-102) — the 4th and final Research "Governance & process" surface: a referee-calibration
harness that negatively controls the statistical certifier itself.

- **New PURE module `app/engine/referee_audit.py`**:
  - `permute_null_observations(cohort_obs, control_obs, *, rng)` — the seeded null-factor generator: a
    per-date random label-permutation of a real factor's cross-section. Preserves the exact multiset of
    observed values (nothing fabricated) while destroying any true relationship between group membership
    and value — the textbook permutation-test null.
  - `binomial_ci(successes, n)` — a numpy/scipy-free Wilson score confidence interval for the empirical
    false-pass rate (chosen over the naive Wald interval, which degenerates to `[0, 0]` at zero successes
    — misleading for this panel's typically near-zero counts).
  - `build_referee_audit_report(...)` — pure assembly of the report dict; derives `contaminated_caught`
    (`status != "PASS"`) from the actual verdict, and always carries the static
    `contaminated_expected_outcome: "rejected"` label.
  - `run_referee_audit(session=None, *, cfg=None, ledger_path=None, run_date=None, assemble_source=None,
    assemble_contaminated=None, ...)` — the orchestrator. Runs `n_null_trials` null certifications + one
    lookahead-contaminated-factor certification, each through the EXISTING `referee.certify_edge` against
    a FRESH `RefereeState(n_trials=1, ...)` (never derived from any ledger's accumulated count), appending
    every verdict to an explicit, isolated THROWAWAY `ledger_path` (freshly overwritten each call — never
    accumulates). `assemble_source` / `assemble_contaminated` are injectable, mirroring
    `app.engine.forward_walk`'s `Assembler` idiom exactly: omitted, they lazily pull REAL data (a real
    Factor-Lab claim's cohort via the SHARED `assemble_claim_observations` seam, and a lookahead-
    contaminated cross-section built from the stored `forward_returns` table); injected (every test),
    NO database is ever touched.
  - `resolve_referee_audit_path()` / `write_referee_audit_report()` / `read_referee_audit_report()` —
    mirror `app.engine.drift`'s resolver/writer/reader exactly (env override, temp-file-then-rename write,
    honest `None`-on-missing / `status: "unreadable"`-on-corrupt read, never a raise).
  - `_main()` — a CLI entry point (`python -m app.engine.referee_audit`, mirrors
    `app.engine.forward_walk._main`'s shape) — the config-seeded OFFLINE job that materializes the real
    artifact. **This was run once against the real committed seed DB as a build step** (see "Offline
    harness run" below) — nothing in the product wires a UI action to trigger it (J-22 is read-only).
- **Config**: new `RefereeAuditCfg` (`n_null_trials: int = 200`, `seed: int = 20240601`,
  `contaminated_factor_horizon: int = 5`, `report_path`), boot-validated (`n_null_trials >= 1`,
  `contaminated_factor_horizon >= 1`), nested as `ResearchCfg.referee_audit` — mirrors `DriftCfg`'s exact
  pattern (default-populated, `ConfigDict(extra="allow")`, `@model_validator`). `config.yaml` gained the
  matching `research.referee_audit:` block.
- **New endpoint `GET /api/research/referee-audit`** (`app/api/referee_audit.py`, mirrors `budget.py` /
  `graveyard.py` exactly): `{"report": read_referee_audit_report()}` — re-reads the persisted artifact
  verbatim, no recompute; a missing artifact yields `{"report": null}` (200, never 500). Wired into
  `main.py` immediately after the existing `budget.router` registration.
- **Offline harness run**: ran `python -m app.engine.referee_audit` once against the real committed seed
  DB (`data/trendora.db`, 322 scanner runs, ~597K forward returns). Result: **16/200 false-pass
  (rate=0.08, 95% CI [0.0498, 0.126]) against configured α=0.05**; the lookahead-contaminated factor
  (leadership_score's own 5-day forward return, top-decile-by-itself) **certified PASS**
  (`p=0.0004998`, the block-bootstrap's theoretical floor — a mathematically overwhelming "edge" since the
  ranking criterion IS the evaluation metric) — so **`contaminated_caught: false`, the tripwire fires**.
  This is an honest, real empirical finding, not a bug: the referee's sealed-holdout machinery has no way
  to detect a factor whose contamination is baked into every observation (in-sample AND holdout alike),
  and the panel's job is exactly to surface this loudly rather than hide it. I did **not** tune any
  referee constant to change this outcome (B-102's explicit trap: "auditing ≠ tuning").
- **Isolation verified**: `git diff HEAD` on `certified-claims.jsonl`, `staging-ledger.jsonl`, and
  `pre-registrations.jsonl` is EMPTY (MD5 checksums identical before/after the real run); live
  `GET /api/evidence` still shows exactly 7 FAIL claims, 0 PASS — byte-identical to the documented
  plateau state.
- **Frontend**: new read-only page `/research/referee-audit`; new 4th "Referee audit" card in the
  existing `/research` "Governance & process" grouping (now complete at 4/4) — see the frontend handoff.

## Files Changed

Backend (new):
- `apps/backend/app/engine/referee_audit.py` -- the harness (generator, CI, report builder, orchestrator,
  default DB-backed assemblers, persistence, CLI).
- `apps/backend/app/api/referee_audit.py` -- thin `GET /research/referee-audit` router.
- `apps/backend/tests/test_referee_audit.py` -- 41 tests: pure-function exactness (permutation preserves
  the value multiset / per-date group sizes / matches numpy's own permutation API / is deterministic;
  Wilson CI hand-computed / non-degenerate at 0 / bounded / honest at n=0); report-assembly logic
  (`contaminated_caught` true/false, static expected-outcome label); orchestration with injected
  assemblers (deterministic given the same seed; writes ONLY the throwaway ledger and leaves the real
  `certified-claims.jsonl` / `staging-ledger.jsonl` / `pre-registrations.jsonl` byte-identical; never
  overwrites accumulate; every null trial uses `required_p = alpha/1`, never Bonferroni-deflated by an
  accumulating count; the permutation strictly reduces the pass rate below the un-permuted baseline's 100%;
  the contaminated factor is deterministically FAIL when it carries no real edge and deterministically
  PASS — seed-invariant, since a zero-variance holdout series' bootstrap p-value never depends on which
  indices are drawn — when it is a noiseless "perfect crime"); config boot-validation; persistence
  round-trip + honest missing/unparseable degradation; the two default DB-backed assemblers against a
  TINY in-memory fixture (mirrors `test_regime_history.py`'s `make_engine(":memory:")` pattern) — never
  the full 30-year seed.
- `apps/backend/tests/test_api_referee_audit.py` -- 5 tests: 200-honest-empty on missing artifact,
  200-honest-unreadable on corrupt artifact (never 500), verbatim fixture serving, endpoint-equals-module
  single-source check, never-recomputes-beyond-the-artifact.

Backend (modified):
- `apps/backend/app/config.py` -- new `RefereeAuditCfg` + `_default_referee_audit()`, nested as
  `ResearchCfg.referee_audit`.
- `apps/backend/main.py` -- import + `include_router(referee_audit.router, prefix="/api")`.
- `config.yaml` -- new `research.referee_audit:` block (`n_null_trials: 200`, `seed: 20240601`,
  `contaminated_factor_horizon: 5`, `report_path`).

Frontend: see `docs/handoffs/goal-mcp-loop-iter-36-frontend.md`.

New runtime artifacts (git-untracked, produced by the offline run — not source):
- `runs/goal-session-mcp-loop/state/referee-audit-report.json` -- the real persisted report (the ONE
  value the Data Contract adds).
- `runs/goal-session-mcp-loop/state/referee-audit-throwaway-ledger.jsonl` -- the disposable 201-entry
  audit trail (200 null + 1 contaminated) from that run — inspectable, but never read by the endpoint and
  overwritten fresh on the next invocation.

Confirmed untouched (per the plan's explicit "Do NOT touch" list, verified by reading each in full):
`app/engine/referee.py`, `app/engine/ledger.py`, `app/mcp/tools.py`, and the real
`certified-claims.jsonl` / `staging-ledger.jsonl` / `pre-registrations.jsonl`.

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/test_referee_audit.py tests/test_api_referee_audit.py -v`
Result: **39 passed, 0 failed** (34 from test_referee_audit.py + 5 from test_api_referee_audit.py).

Command (regression, all touched + sibling files together): `cd apps/backend && .venv/bin/python -m pytest tests/test_referee_audit.py tests/test_api_referee_audit.py tests/test_config.py tests/test_config_engine.py tests/test_referee.py tests/test_forward_walk.py tests/test_budget_accounting.py tests/test_api_budget.py tests/test_graveyard.py tests/test_api_graveyard.py tests/test_registry.py tests/test_api_registry.py tests/test_drift.py -v`
Result: **251 passed, 0 failed** (4.2s total — confirms the whole suite here is genuinely DB-free/fast,
never touching the full 30-year seed).

Command: `cd apps/frontend && npx tsc --noEmit`
Result: clean, no errors.

Command: `cd apps/frontend && npx next build` (invoked by `scripts/start-frontend.sh`'s stamp-guarded
rebuild)
Result: **compiled successfully**, TypeScript validity check passed as part of the build,
`/research/referee-audit` listed as a real prerendered route (3.51 kB).

Did NOT run the full backend suite (per this session's standing pump lesson: never run the full/concurrent
pytest suite — it fork-locks the box and the 30-year-seed fixtures make it ~10-11h; the reviewer/QA stage
verifies the rest).

## Service startup / live verification

- `scripts/start-backend.sh` started cleanly on port 8255 (health 200s); killed, restarted cleanly again —
  no port conflicts on either cycle.
- `scripts/start-frontend.sh` initially served a **stale pre-built bundle** (`.next/BUILD_ID` predated
  this iteration's new page — the documented iter-20/21/35 stale-prod-build trap), giving a 404 on
  `/research/referee-audit` even though the source file existed. Fixed by removing the build stamp
  (`.next/.qa-serve-base`) and restarting, which forced `next build` to pick up the new route (confirmed:
  `BUILD_ID` mtime now postdates the page source mtime). **Flagging this because it will recur for the
  next iteration's developer too** if a stale `.next` is reused without a source-mtime check.
- Live-verified via a real Chrome session (not just curl): `/research/referee-audit` renders all 4 stat
  cards (null trials 200, false-pass rate 0.08 with its CI, α 0.05, run date + seed/horizon) and the
  **prominent red tripwire card** (exact expected treatment, since the real run's contaminated verdict is
  PASS); `/research` shows the new 4th "Referee audit" governance card; clicking it navigates correctly to
  the page. Screenshots taken during this session (not committed — verification artifacts, not source).
- Both servers killed cleanly at the end; confirmed via `ps aux` that no uvicorn/next-server processes
  remain.

## Known Issues

1. **The empirical false-pass rate (8%) sits slightly above the nominal α (5%)**, with the α value itself
   landing just inside the 95% CI's lower edge (`[0.0498, 0.126]`). This is the harness's genuine,
   honestly-disclosed finding on this data/seed — I did not investigate further or tune anything to change
   it (B-102's explicit trap: "using the sweep to pick friendlier referee settings... auditing ≠ tuning").
   Whether this is ordinary sampling noise at n=200 (borderline, ~1.9 SE) or worth a deeper look is an
   owner/reviewer judgment call, not a code defect.
2. **The lookahead-contaminated factor was NOT rejected** (verdict PASS, `contaminated_caught: false`).
   This is analytically expected, not a harness bug: the "value equals its own realized forward return"
   construction is tautological (the ranking criterion IS the evaluation metric), so the correlation is
   real and reproducible in-sample AND out-of-sample alike — no temporal-holdout scheme can catch this
   class of contamination. The DoD explicitly names this as an accepted outcome ("OR the panel renders a
   prominent red tripwire failure state") and the panel does exactly that, live-verified.
3. **The frontend page's server-rendered HTML (curl) always shows only the loading skeleton** — this is a
   `"use client"` component that fetches via `useEffect` after mount, identical to every other
   `/research/*` sub-page in this codebase (budget, graveyard, registry). Not a defect; confirmed via a
   real browser session that the fetched content renders correctly after hydration.
4. Per the plan's explicit scope, this iteration does **not** touch the risk-analytics cluster
   (J-23/J-24/J-25), the B-204 referee-settings sweep, any B-113 sentinel work, or the deterministic-replay
   hygiene closeout — all deferred as specified.
5. The required-still-passing set (J-01, J-03, J-05, J-11, J-17, J-18, J-19, J-20) was **not** re-verified
   by me beyond the sibling-endpoint spot-checks noted above (`/api/research/budget`,
   `/api/research/graveyard` returning 200; `/api/evidence` unchanged) — the plan explicitly assigns the
   full live re-verification of that set to the browser-qa lane, not the developer.
