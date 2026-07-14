# Phase goal-mcp-loop-iter-33 — UI Surface Map

**Phase:** goal-mcp-loop-iter-33
**Date:** 2026-07-14
**Written by:** ui-impact-analyst

---

## File Classification

Per `.claude/skills/diff-to-ui-impact.md`. Files confirmed via `git diff`/`git status` against the dev
handoff's "Files Changed" list; the pre-existing unrelated iter-26 WIP noted in `plan.md` (`prices.py`,
`scoring.py`, `warmup.py`, `test_forward_testing.py`, `test_warmup.py`, `test_scoring_window.py`) is
confirmed absent from this diff and excluded below.

| File | Category | UI Impact | Explanation |
|------|----------|-----------|-------------|
| `apps/backend/app/engine/readiness.py` | backend-internal | indirect | New pure `compute_preflight` composer. No UI file itself, but its return value is the ONLY source of the `preflight` field served below — reaches the UI through `health.py`. |
| `apps/backend/app/api/health.py` | backend-api | direct | Existing `GET /api/health` endpoint (already polled by the frontend's `ReadinessProvider`) gains an additive `preflight` field. |
| `apps/backend/app/config.py` | config | indirect | New `ReadinessCfg` (freshness threshold + severity map). Not rendered anywhere itself, but its values determine what the banner shows and which verdict a breach maps to. |
| `config.yaml` | config | indirect | New `readiness:` block — the operator-facing values `ReadinessCfg` validates. Same indirect relationship as above. |
| `apps/backend/tests/test_readiness.py` (new) | backend-internal / test | none | Fixture-matrix and config-wiring tests. |
| `apps/backend/tests/test_health.py` | backend-internal / test | none | Additive-shape + single-source tests for the `/api/health` payload. |
| `apps/backend/tests/test_config.py` | backend-internal / test | none | Config-fixture update (`"readiness": {...}` block added, iter-28 precedent). |
| `apps/backend/tests/test_config_engine.py` | backend-internal / test | none | Same fixture update. |
| `apps/backend/tests/test_themes.py` | backend-internal / test | none | Same fixture update. |
| `apps/backend/tests/test_sectors.py` | backend-internal / test | none | Same fixture update. |
| `apps/backend/tests/test_indexes.py` | backend-internal / test | none | Same fixture update. |
| `apps/frontend/lib/api.ts` | frontend-direct (types only) | indirect / supporting | New `PreflightVerdict`/`PreflightComponent`/`PreflightStatus` types + `preflight` field on `HealthStatus`. Compile-time only — no visual element of its own, but required for the component below to read typed data. |
| `apps/frontend/components/readiness-provider.tsx` | frontend-direct | indirect / supporting | `ReadinessContextValue` extended to expose `preflight` from the SAME existing `/api/health` poll (confirmed by diff — no second `fetch` call added). Plumbing only; renders nothing itself. |
| `apps/frontend/components/preflight-banner.tsx` (new) | frontend-direct | direct | New component — the actual visible banner (4 states: loading / GO / DEGRADED / NO-GO). |
| `apps/frontend/app/layout.tsx` | frontend-direct | direct | Root layout (confirmed the ONLY `layout.tsx` in `apps/frontend/app/`, wrapping all 27 routes) — mounts `<PreflightBanner />` once, between `<header>` and `<main>`. |

**Overall classification: full-stack.** The change crosses backend engine → backend API → frontend types →
frontend provider → new frontend component → root layout mount, confirmed end-to-end by reading the
actual diffs (not just the handoff's description).

---

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/` (Dashboard) | `PreflightBanner` (`data-testid="preflight-banner"`, `data-verdict="GO"`) | New component | J-20/B-301: new cross-cutting daily preflight verdict, mounted once in `app/layout.tsx` | Load `/` with the backend running normally against the seed; confirm a thin strip renders directly below the header reading "GO — today's board is current." with a small green dot, and that the dashboard content below it is otherwise unaffected. |
| `/stocks` | `PreflightBanner` | New component | Same shared banner, inherited via the root layout — no per-page code | Navigate to `/stocks`; confirm the identical GO strip (same text, same `data-testid="preflight-banner"`) renders above the stocks table, and the table itself still loads and paginates normally beneath it. |
| `/stocks/[ticker]` (e.g. `/stocks/NVDA`) | `PreflightBanner` | New component | Same shared banner, inherited via the root layout | Navigate to `/stocks/NVDA`; confirm the GO strip renders above the stock detail header, and confirm the page's own "Not yet proven" evidence badges and score chart still render normally beneath it (no visual collision between the two systems). |
| `/watchlist` | `PreflightBanner` — DEGRADED state | Changed behavior (induced) | A freshness-component breach maps to `DEGRADED` per the default `readiness.severity` config | With `readiness.freshness_max_age_days` overridden to a negative value (e.g. a temporary `TRENDORA_CONFIG` alt-file — no seed data changes) and the backend restarted, reload `/watchlist`; confirm the strip switches to a full-width amber banner (`data-verdict="DEGRADED"`) with headline "DEGRADED — treat today's board with caution." and a bullet reading "Latest data (...) is 0 trading day(s) old, exceeding the configured maximum of -1 day(s)."; confirm the rest of the Watchlist page still renders normally beneath it; then restore the normal config and confirm GO returns. |
| `/evidence` | `PreflightBanner` | New component | Same shared banner, inherited via the root layout | Navigate to `/evidence`; confirm the GO strip renders above the evidence ledger table, and that the existing FAIL-status ledger entries in that table are unaffected. |
| `/research` and its 13 sub-pages (e.g. `/research/factor-lab`, `/research/budget`) | `PreflightBanner` | New component (inherited; not individually screenshotted in the dev handoff) | goal.md's "UI surface changes" explicitly names `/research`; inherited automatically via the shared root layout, but the dev handoff's live-verification log lists only `/`, `/evidence`, `/stocks`, `/stocks/NVDA`, `/watchlist` — `/research` was not independently confirmed | Navigate to `/research` and at least one sub-page (e.g. `/research/factor-lab`); confirm the identical GO strip renders in the same position as on `/`. This route has no independent screenshot evidence yet and should be confirmed directly. |
| Remaining routes: `/sectors`, `/themes`, `/backtest`, `/data`, `/methodology`, `/scanner-runs`, `/scanner-runs/[runId]` | `PreflightBanner` | New component (inherited) | Mounted once in the shared root layout — appears on every route with zero per-page code | Spot-check `/data` in particular (it already has its own pre-existing warning-style banner for an unrelated purpose); confirm the new `PreflightBanner` strip appears above `/data`'s own page content without visually overlapping or being confused with `/data`'s existing warning element. |
| Any route (reproduced on `/stocks/NVDA` in dev testing) | `PreflightBanner` — NO-GO state | Changed behavior (induced) | A DB/ledger-integrity breach maps to `NO-GO` per the default `readiness.severity` config | With a ledger/registry path environment override pointed at a nonexistent file (e.g. an alternate `TRENDORA_LEDGER_PATH`) and the backend restarted, reload any page; confirm the strip switches to a full-width red banner (`data-verdict="NO-GO"`) whose headline text is exactly "NO-GO — do not rely on today's board." with a bullet naming the specific missing/unparseable file; then restore the normal environment and confirm GO returns. |
| Any route | `PreflightBanner` — loading state | New component (state) | Must never fabricate a GO before the first `/api/health` poll resolves | Using browser devtools, throttle the network or intercept the first `/api/health` request; confirm that before it resolves, the strip shows a neutral gray placeholder reading "Checking board status…" rather than any colored GO/DEGRADED/NO-GO state. |
| Any route | `PreflightBanner` — backend-unreachable fallback | Changed behavior (error path) | A failed health poll must degrade honestly, never render blank | Stop the backend process while a page is open in the browser; after the next poll cycle, confirm the strip switches to the red NO-GO treatment with the exact reason text "Backend is unavailable — the preflight check could not run." instead of the page going blank or throwing a client error. |
| All routes | `app/layout.tsx` (root shell) | Updated layout | `<PreflightBanner />` mounted once, between `<header>` and `<main>` | Inspect the DOM on any page and confirm exactly one element with `data-testid="preflight-banner"` exists in the whole document (not a duplicate per page), positioned as a direct sibling between the `<header>` and `<main>` elements inside the content column. |
| N/A (API contract, consumed by every page via `ReadinessProvider`) | `preflight` field on `GET /api/health` | Changed behavior (additive API shape) | New composed verdict served on the existing single health/readiness endpoint — no new endpoint added | Call `GET /api/health` directly (curl or the browser Network tab) and confirm the JSON body contains a new `preflight` object (`verdict`/`reasons`/`components`/`as_of`/`reference` keys) while the pre-existing `status`, `db_ok`, `readiness`, and `warmup` keys are present with their previous shape, unchanged. |
| All routes | `ReadinessProvider` + `PreflightBanner` (single-source check) | Changed behavior (data plumbing) | B-301's named trap is a page computing its own "mini-readiness" — must be provably single-source | Open the browser Network tab on any page and watch one full poll cycle; confirm only ONE request fires to `/api/health` (no second/duplicate request originating from the banner itself), proving the banner has no independent fetch or compute path. |

<!-- Change Type key used above: New component | Updated layout | Changed behavior (induced/error path/additive/data plumbing) -->

---

## Backend-Only Changes (No UI Impact)

The following have no UI surface of their own. (Note: `app/engine/readiness.py`'s `compute_preflight` and
`app/api/health.py`'s additive `preflight` field DO have UI impact — via the `/api/health` API-contract row
in the table above — and are therefore not repeated here.)

- `apps/backend/app/config.py` (`ReadinessCfg`) — the `freshness_max_age_days` threshold and `severity`
  map are operator-facing configuration values, not rendered anywhere in the product UI itself. They
  control what the banner shows (exercised in the DEGRADED/NO-GO rows above) but the config file itself
  has no UI surface.
- `config.yaml`'s new `readiness:` block — same relationship as above; the values `ReadinessCfg` validates.
- The verdict-history writer (`resolve_verdict_history_path`, `record_verdict_transition` in
  `readiness.py`) and the new runtime log file it produces
  (`runs/goal-session-mcp-loop/state/preflight-verdict-history.jsonl`) — an append-only audit trail with
  no page in the product that reads or displays it.
- `apps/backend/tests/test_readiness.py` (new), `test_health.py`, `test_config.py`, `test_config_engine.py`,
  `test_themes.py`, `test_sectors.py`, `test_indexes.py` — test-only changes, no UI surface.
- `apps/frontend/lib/api.ts` — new TypeScript type declarations (`PreflightVerdict`, `PreflightComponent`,
  `PreflightStatus`). Compile-time only; supports the `PreflightBanner` component above but has no visual
  presence of its own. (Listed here because it is not itself a rendered surface, though it is a frontend
  file, not a backend one.)

---

## Summary

- **Frontend surfaces changed:** 27 routes (every page in the app receives the banner via one shared
  root-layout mount — confirmed by enumerating all `page.tsx` files under `apps/frontend/app/` and
  confirming `app/layout.tsx` is the only `layout.tsx` in the tree)
- **New pages/routes:** 0 (no new page or nav section — confirmed cross-cutting chrome only, per plan)
- **Modified components:** 4 (1 new: `PreflightBanner`; 2 modified: `ReadinessProvider`, root
  `layout.tsx`; 1 modified types-only supporting file: `lib/api.ts`)
- **Navigation changes:** no
- **Backend-only changes:** 9 source files (`config.py`, `config.yaml`, and 7 test files) + 1 generated
  runtime artifact (`preflight-verdict-history.jsonl`, no UI reader)
