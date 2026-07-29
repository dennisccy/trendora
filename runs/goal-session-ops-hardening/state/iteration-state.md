# Iteration State — ops-hardening

**After iteration:** 33 · **Date:** 2026-07-29 · **Verdict:** CONTINUE

## Journeys

7 passing (J-01 J-03 J-04 J-05 **J-06** J-08 J-09) · 1 partial (J-07) · 0 failing · 0 unknown — 8 total

## Active blockers

- **dev, ONLY TARGET — J-07's last two steps:** record `GET /api/health` LATENCY (not just its 200 rate) through a live warm and say plainly if it is in budget; then run step 4's induced-pressure drill (tight cap, throwaway process — warm aborts honestly while the SAME process keeps serving), deferred since iter-14. Launch via `scripts/start-backend.sh` ONLY so host caps apply: host reset #6 was today, `host-guard.env` tightened 14G→10G this morning.
- **dev, NEW (iter-33/g):** `/research/regime-lab`'s cold `view=pooled` blocks the request thread 60-90 s (`app/engine/research.py:3509-3559`, once per `dataset_version`, not per boot) and once returned HTTP 200 carrying the body "Internal Server Error", undiagnosed. Needs `/api/backtest`'s iter-32 background dispatch.
- **dev, NEW and cheap (iter-33/h):** `resolveLabLoadPanel` is wired into `RegimeLabPage` only; 4 sibling labs (`phase-severity-lab`, `regime-phase-factor`, `factor-lab`, `severity-velocity`) keep the bare unlabelled `LabSkeleton` and no Retry — the shape UT-11 just proved is a P1. Resolver is generic + exported: wiring only.
- **dev, carried AG-8, all minor, none firing today:** `warmup.py:194` (+ the badge wording after a permanently failed warm-up, 4 iterations unmade); `prices.py:141`, on J-07's warm path; iter-31/e; iter-32/f (WATCH only).
- **owner, non-blocking (iter-33/i):** should `start-frontend.sh` join `HOST_GUARD_MARKER_FILES` now it runs a full `next build` inside automated lanes? Measured: the build inherits mask `0-3,8-11` today.
- **framework:** regenerate `ui-surface-map.md` / `user-visible-changes.md` / the demo after any fix-mode round landing real UI (all three were pre-fix and wrong this run); `J-07.json`'s literal `n=8869` still brittle.

## Last 2 verdicts

- iter 33: CONTINUE — launcher genuinely serves `next start`; J-06's 11-page real-browser sweep, a 1.325 s fresh boot-to-health and step 3's code audit all landed, so **J-06 crossed to passing** (first status change in 5 iterations); the sweep's own P1 (Regime Lab cold stall) was fixed frontend-only inside the iteration.
- iter 32: CONTINUE — `stock_obs` bounded for real (981→170 MB, byte-identical payload); J-07 still partial on its own steps 2 and 4.

## Do not redo

- **`start-frontend.sh` is prod mode** (BUILD_ID staleness, `exit 1` on build failure, no `next dev` fallback, lines 1-27 byte-unchanged) — the dev-vs-prod decision is settled; do not reopen or amend goal.md.
- **J-06's sweep is DONE** — 11-page real-browser TTI + on-load latencies + boot-to-health (`reports/perf-budgets.md:4099-4270`) and step 3's per-endpoint audit (`...-iter-33-dev.md:151-186`).
- **`merge_ui_test_results.py` `_ROW_RE` → `(?:UT|TC)-` FIXED** with a RED-before test — 4 evaluators' ask, closed.
- **The UT-11 honest-wait fix is DONE for Regime Lab** (`lib/lab-load-panel.ts` + `_labs.tsx`) — extend to siblings (iter-33/h), never rewrite it.
- **`stock_obs` / `compute_forward_aggregates` / `resolved_forward_aggregate_evidence` bounded shape** — binding, untouched.
- **`/api/health` ≤0.1 s: 93.4 ms at rest (PASS), 97.8-207.7 ms under browser load (honest WARN)** — record it that way, no goal.md amendment. **AG-10 marker files zero diff** — never weaken.
