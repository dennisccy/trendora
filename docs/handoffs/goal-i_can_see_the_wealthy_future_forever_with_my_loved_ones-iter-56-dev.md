# goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-56 Dev Handoff

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-56
**Date:** 2026-06-28
**Agent:** developer
**Status:** complete

## What Was Built

Two pure frontend presentation / information-architecture changes over already-served values — **zero backend diff**, every displayed figure byte-identical and read from its existing canonical source.

- **J-113 — Research hub reading-order reorder.** Extracted the ordered hub list into a new pure lib module `lib/research-labs.ts` (icons referenced by string key so the module stays dependency-free + unit-assertable). `app/research/page.tsx` now imports `RESEARCH_LABS` and resolves each icon key to its lucide component via a small `LAB_ICONS` registry. The `data-testid="research-hub"` grid renders the ten labs in exactly the spec order:
  Factor Lab → Regime Lab → Market Phase & Severity Lab → Regime × Phase × Factor → Regime × Setup × Pattern → Severity-velocity × Regime → Multi-factor combination → Setup & Pattern event study → Recovery-Turn Edge → Downtrend Opportunity.
  No lab added/removed/renamed (all ten still reachable + deep-linkable); routes, the `?asof` href-stamping (J-50), and per-lab lazy-load (J-104) are unchanged.
- **J-114 — de-interleave the four all-horizon labs' per-horizon columns.** New pure lib module `lib/research-lab-columns.ts` exports `groupedHorizonColumns(horizons)` → all forward-return column descriptors first (ascending horizon order), then all max-drawdown column descriptors (same horizon order); never interleaved. Matches the J-86 leaderboard grouping. Applied to all 16 per-horizon map sites (7 header rows + 9 body/rank-IC rows) across the four all-horizon labs in `app/research/_labs.tsx`:
  - Factor Lab all-factors table **and** its expandable per-factor decile grid (J-109)
  - Regime Lab by-label summary **and** regime-score-decile table + its rank-IC header row (J-110)
  - Market Phase & Severity Lab by-phase-label **and** severity-score-decile table + its rank-IC header row (J-111)
  - Regime × Phase × Factor combination table (J-112)
  Header cells, body cells, **and** the client-side sort-column key mapping (`fwd:${h}` / `mdd:${h}` via `FactorSortHeader` / `RegimeSortHeader` / `RpfSortHeader`) all follow the new grouped order. Colour-grading, the NA-honest predicate (`low_sample || n === 0 || value === null`), the As-of/All-history toggle (J-32), the J-112 30-rows pagination, and the `N=` chip drill-downs are untouched. The horizon set still comes from the config-driven payload `data.horizons` (no hardcoded `[1,5,10,20,60]`). The rank-IC header rows keep the rank-IC value on the (now-leading) forward-return columns and the dash placeholder on the (now-trailing) drawdown columns.

The now-unused `Fragment` import was removed from `_labs.tsx` (all 16 paired-Fragment sites became single-column maps).

## Files Changed

- `apps/frontend/lib/research-labs.ts` -- NEW. Pure ordered hub-list source (J-113); `RESEARCH_LABS` + `ResearchLabIcon`.
- `apps/frontend/lib/research-labs.test.ts` -- NEW. Asserts the exact hub reading order, ten distinct routes, known icon keys.
- `apps/frontend/lib/research-lab-columns.ts` -- NEW. Pure `groupedHorizonColumns()` + `horizonColumnKey()` (J-114).
- `apps/frontend/lib/research-lab-columns.test.ts` -- NEW. Asserts all-fwd-before-all-mdd, config-driven horizon set, 2×|horizons| count.
- `apps/frontend/app/research/page.tsx` -- imports `RESEARCH_LABS` + icon registry; maps the hub grid over it (J-113).
- `apps/frontend/app/research/_labs.tsx` -- all 16 per-horizon column sites use `groupedHorizonColumns(horizons)` (J-114); removed unused `Fragment` import.

## Tests Run

- **Frontend unit (node TS-strip convention `node lib/<name>.test.ts`):** This host's `node` build lacks the TS type-strip runtime (`ERR_NO_TYPESCRIPT` — a known limitation noted in iter-49), so the committed `.test.ts` files were verified by transpiling them with the repo's `tsc` 5.7.2 (`--rewriteRelativeImportExtensions`) and running the emitted JS:
  - `lib/research-lab-columns.test.ts` → **8 checks passed**
  - `lib/research-labs.test.ts` → **6 checks passed**
  The files are written in the exact committed convention and will run directly via `node lib/<name>.test.ts` on a node build with TS support.
- **Frontend typecheck:** `cd apps/frontend && node_modules/.bin/tsc --noEmit` → **EXIT 0** (whole project, including the two edited files + four new lib files).
- **Backend pytest (zero backend diff):** Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -q` launched nohup-async → `reports/qa/goal-...-iter-56-test.log`. In-flight at handoff time; expected byte-identical green (the iter-55 1210-passed / 4-skipped / 0-failed flush is the standing gate — no backend file changed). The next iteration's GOAL_ACHIEVED candidacy confirms the flushed `0 failed, EXIT 0` line.

## Live verification (servers via `./scripts/dev.sh`)

- Both servers started clean: backend `http://localhost:8255`, frontend `http://localhost:3255`.
- **J-113 verified live** — the rendered `/research` HTML lists `research-lab-link-*` in exactly the spec order (factor-lab, regime-lab, phase-severity-lab, regime-phase-factor, regime-setup-pattern, severity-velocity, factor-combination, event-study, recovery-turn-edge, downtrend-opportunity).
- **J-114 data confirmed servable** — all four lab endpoints return `horizons=[1,5,10,20,60]` with populated rows (`factor-lab?all=true` 11 factors, regime-lab 6 labels, phase-severity-lab 5 phases, regime-phase-factor 160 rows), so the client tables populate with the grouped columns. The definitive grouped-header live DOM capture is the browser-qa-agent's step.

## Known Issues

- **Servers intentionally left running** (backend :8255, frontend :3255) so the dedicated browser-qa-agent step does not skip on a torn-down frontend (iter-52 lesson). They were started detached via `nohup bash scripts/dev.sh`; the browser-qa / demo steps should reuse them (or `scripts/dev.sh` re-kills the ports and restarts cleanly). The full pytest suite is also still running nohup-async; both will exit on their own.
- The node TS type-strip convention cannot execute on this host's `node` build (`ERR_NO_TYPESCRIPT`); verified instead via `tsc` transpile (see Tests Run). No code defect — the tests pass and conform to the committed convention.
- J-114 live grouped-header DOM proof was not captured developer-side (no standalone Playwright/Chrome available without a heavyweight install; Chrome-MCP evidence capture is the browser-qa-agent's responsibility and is flagged in the spec for evidence-dir hygiene). Logic correctness is covered by the committed unit tests + the passing typecheck.
