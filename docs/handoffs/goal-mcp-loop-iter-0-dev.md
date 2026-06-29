# goal-mcp-loop-iter-0 Dev Handoff

**Phase:** goal-mcp-loop-iter-0
**Date:** 2026-06-29
**Agent:** developer
**Status:** complete

## Summary

**Baseline verify-only — no changes.** This is iteration 0 of the `mcp-loop` goal
session, a deliberate **no-op developer step**. Per the iter spec's IN SCOPE
(Backend: "None — verify-only"; Frontend: "None — verify-only") and OUT OF SCOPE
("Any code change, migration, dependency install, or config edit"), **no source
files were created or modified**. The iteration's value is the static baseline
recorded below plus the browser-QA step's empirical run of J-01..J-05.

## What Was Built

- Nothing. Zero source/config/dependency changes (verify-only baseline).
- Output of this step: a static code/file-scan baseline of the current Trendora
  codebase, distinguishing the **evidence plumbing that already exists** from the
  **user-facing evidence surface that does not** — to ground the per-journey
  observations the browser-QA agent confirms empirically.

## Files Changed

- None. `git status --porcelain` shows zero source diff. (The only untracked paths
  are `docs/phases/goal-mcp-loop-iter-0.md` and `runs/goal-session-mcp-loop/`,
  both authored by the goal-decomposer, not by this developer step.)

## Static baseline (code/file scan — read-only)

Confirms the spec's BACKGROUND and `blueprint.md` baseline file-scan:

**EXISTS — referee + ledger plumbing (not yet surfaced to users):**
- `apps/backend/app/engine/referee.py` — sealed temporal holdout + block-bootstrap
  p + multiple-testing deflation (`certify_edge`).
- `apps/backend/app/engine/ledger.py` — append-only certified-claims JSONL
  (`append_entry` / `read_entries`).
- `apps/backend/app/mcp/server.py` + `apps/backend/app/mcp/tools.py` — the read-only
  "window"; `verify_edge` is the only writer (writes only the ledger).
- `project-extensions/gates/post-decompose.sh` + `verify_claim.py` — post-decompose
  gate that certifies an iteration's `## Evidence Claim` through the referee before
  build (non-PASS blocks).

**MISSING — the user-facing evidence surface (what J-01..J-05 will build, iter-1+):**
- No certified-claims ledger file:
  `runs/goal-session-mcp-loop/state/certified-claims.jsonl` is **absent** ⇒ EMPTY
  ledger ⇒ no signal can legitimately read "Proven".
- No `GET /api/evidence` endpoint: `apps/backend/app/api/__init__.py` is empty of an
  evidence router; grep for `/api/evidence` across `apps/backend/app` returns nothing.
  (The backend "evidence" grep hits — `backtest.py`, `research.py`, `forward_testing.py`,
  `models.py` — are all the pre-existing *realized forward-return* evidence, not the
  new certified-claims layer.)
- No "Proven / Not yet proven" evidence badge. `apps/frontend/components/score-badge.tsx`
  is the existing **A–E colour-grade** badge (bucket letter + raw 0–100 score) for the
  three scores — it carries no evidence/proven status.
- No `/evidence` page. `apps/frontend/components/evidence-panels.tsx` is the existing
  **forward-tested return** panels (`compute_forward_aggregates`), not a certified-claims
  ledger surface (no "Proven/certified/ledger" strings).
- No "Evidence" nav entry. `apps/frontend/components/sidebar.tsx` `NAV` =
  Dashboard, Stocks, Themes, Sectors, Scanner Runs, Backtest, Research, Watchlist,
  Methodology, Data Manager — no Evidence section.

⇒ Static expectation: J-01..J-05 **FAIL at baseline, reason "surface not yet
implemented"** (consistent with the spec NOTES). The browser-QA step determines this
empirically against the running app; the goal-evaluator records the verdict and seeds
`journey-history.json`.

## Per-journey observations (developer static scan — to be confirmed by browser-QA)

> These are code/file-level findings, not a browser run. The browser-QA agent owns the
> empirical pass/fail against the live app; the observations below predict that outcome
> and explain *why* from the source.

- **J-01 — Every score shows an evidence status** (`/stocks` leaderboard rows):
  **Expect FAIL.** The only badge on score rows is `ScoreBadge` (A–E colour grade +
  raw score). There is no "Proven / Not yet proven" evidence badge component anywhere,
  so the displayed scores are presented without any evidence status. *Reason: surface
  not yet implemented.*

- **J-02 — Drill into the proof behind a score** (`/stocks/{ticker}`):
  **Expect FAIL.** No proof panel and no certified-claim drill-down exist; there is no
  "Proven" badge to expand, and no path to an out-of-sample test / control comparison /
  certified-claim id+date for a per-stock score. *Reason: surface not yet implemented.*

- **J-03 — Unproven / noise signals honestly marked** (cross-cutting):
  **Expect FAIL.** With no evidence-status surface at all, scores/edges are shown as
  confident numbers with no "Not yet proven" (nor "did not beat controls out-of-sample")
  marking. *Reason: surface not yet implemented* (and the ledger is empty, so honest
  baseline state would be "Not yet proven" everywhere once the surface exists).

- **J-04 — Regime-conditioned evidence** (Dashboard regime → regime-scoped evidence):
  **Expect FAIL.** The Dashboard already surfaces the market regime/phase (existing,
  unchanged), but there is no regime-scoped evidence surface labeled with the regime it
  applies to, and no `/evidence`. *Reason: surface not yet implemented.*

- **J-05 — Audit the evidence ledger** (click "Evidence" in nav):
  **Expect FAIL.** There is no "Evidence" nav entry, no `/evidence` route, and no claims
  list (hypothesis / out-of-sample verdict / control comparison / registration date /
  forward-walk score-to-date), so the journey cannot be entered. *Reason: surface not
  yet implemented* (and the certified-claims ledger file is absent ⇒ empty).

## Tests Run

Command: N/A — no unit/integration tests required this iteration (spec TESTING
REQUIREMENTS: "Unit/integration: none required (no code paths changed this iteration)").
Result: 0 code tests run, 0 source files changed. Verify-only integrity confirmed via
`git status --porcelain` (no source diff).

The required testing for this iteration is **browser-only** (run J-01..J-05 against the
running app) and is owned by the downstream browser-QA step, which per the spec NOTES
should ensure backend + frontend are reachable (`./scripts/dev.sh`) before running.

## Pre-handoff verification

- **Service startup:** Not started by this step, deliberately. No code, config, or
  dependency changed, so startup behaviour is unchanged from the prior GOAL_ACHIEVED
  product state; the spec design defers the live run to the browser-QA step (which
  brings up backend + frontend and confirms reachability). Starting servers here would
  add no signal and risk leftover processes blocking the pipeline — so they were not
  started, and none are left running.
- **External integrations:** N/A — no adapters, scrapers, or external API calls added.
- **Native dependency binaries:** N/A — no new dependency installed.

## Known Issues

- None introduced (no changes). The five "FAIL / surface not yet implemented" outcomes
  above are the **expected baseline**, not regressions — they are the starting line this
  iteration exists to record, and they drive iter-1+.
- The per-journey results above are a **static scan**, not a browser run. If the
  browser-QA agent observes anything different on the live app (e.g. a partially wired
  surface), its empirical result supersedes these predictions.
- **Forward guidance for iter-1+ (not this iteration):** stand up the read-side evidence
  path end to end — `GET /api/evidence` reading the certified-claims ledger via
  `app.engine.ledger`, the "Proven / Not yet proven" badge component, and the `/evidence`
  page in the nav — so that with an empty ledger every score honestly reads "Not yet
  proven" (satisfies J-01/J-03/J-05 structurally before any edge is certified). Only a
  later iteration that wants a "Proven" badge needs a `## Evidence Claim` block for the
  post-decompose gate to certify first.
