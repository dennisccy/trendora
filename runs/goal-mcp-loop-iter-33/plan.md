# goal-mcp-loop-iter-33 Execution Plan

Journey: **J-20** — single daily preflight verdict (`GO`/`DEGRADED`/`NO-GO` + reasons), computed once,
rendered as an unmissable layout-level banner on every decision surface. Binding spec: backlog **B-301**
(`docs/improvement-backlog.md` line 1323). Depth = full (per iter-32 evaluator recommendation).

## What to Build

- **Backend composer** `app.engine.readiness:compute_preflight(session, config, ...)` — a new PURE
  function alongside the existing `compute_readiness` in `apps/backend/app/engine/readiness.py` (same
  module — B-301 says "extend `readiness.py`," not create a new one). Returns
  `{verdict: "GO"|"DEGRADED"|"NO-GO", reasons: [...], components: {<input>: {ok, severity, detail}}, as_of/reference}`.
  Composes over three inputs that exist now, recomputing none of them:
  - **servability** — reuse `compute_readiness`'s own liveness check (do not re-derive).
  - **freshness** — latest bar age vs a **deterministic, config/seed-resolved reference** (default = the
    seed's own latest available date, so a fully-loaded seed reads `GO`), counted in trading days via
    the SAME SPY calendar `readiness.py` already builds (`_cached_warmup_dates`/`_warmup_dates`) —
    **never `date.today()`** (anti-goal #5). Threshold: `readiness.freshness_max_age_days`.
  - **DB/ledger integrity** — DB reachable AND the canonical/staging/registry JSONL files exist and
    parse. Reuse the EXISTING path resolvers verbatim — `evidence.resolve_ledger_path()`,
    `graveyard.resolve_staging_ledger_path()`, `registry.resolve_registry_path()` (the exact seams
    iter-32's `budget_accounting.py` already reused) — never duplicate path logic. Tiny-file reads only,
    never a whole-table ORM load (anti-goal #8).
- **Config**: new `ReadinessCfg` in `apps/backend/app/config.py`, mirroring the existing `StartupCfg`
  pattern exactly (boot-validated `@model_validator`, `ConfigDict(extra="allow")`, no inline literals) —
  carries `freshness_max_age_days` + a component→severity map (which breached input forces `DEGRADED`
  vs `NO-GO`; must make BOTH states inducible for the fixture matrix). Wire `readiness: ReadinessCfg`
  into the `Config` aggregator. New top-level `readiness:` block in `config.yaml` (none exists yet —
  confirmed by grep) near the `startup:`/`evidence:` blocks.
- **Serving**: additive `preflight` field on the EXISTING `GET /api/health` (`apps/backend/app/api/health.py`)
  — call `compute_preflight` alongside the existing `compute_readiness` call. `compute_readiness`'s own
  `state`/`warmup` keys stay **byte-identical** (J-40 not regressed) — no new endpoint.
- **Verdict history**: small append-only log written **only on a verdict transition** (not every ~2s
  poll), config-resolved path — mirror the `resolve_*_path()` pattern above for testability (env-override
  seam, `tmp_path`-friendly tests).
- **Frontend provider**: extend `apps/frontend/components/readiness-provider.tsx`'s
  `ReadinessContextValue` to also expose `preflight`, read from the SAME single `/api/health` poll
  (`fetchHealth()` in `tick()`) — no second fetch. Add the `preflight` field's type to `HealthStatus` in
  `apps/frontend/lib/api.ts`.
- **`PreflightBanner` component** (new), mounted **once** in `apps/frontend/app/layout.tsx` (in the
  shell, above `<main>` — visible on every route with zero per-page code), reading only
  `useReadiness()`. No second client fetch, no per-page recompute.
- **Tests**: per-input-combination fixture matrix for `compute_preflight` (exact verdict per the
  configured severity map); severity/threshold config-wiring test (verdict changes with config, not a
  literal); `compute_readiness` byte-identity/snapshot test; health-payload additive-shape +
  single-source test; verdict-history append-on-transition test; error-case tests (DB unreachable,
  missing/unparseable ledger, stale freshness → each an honest mapped verdict, never a raise, never a
  fabricated `GO`).
- **J-11 dedicated golden replay**: `runs/goal-session-mcp-loop/journey-scripts/J-11.json` already
  exists on disk (4 steps, `/evidence` + `/stocks` + `/stocks/NVDA` assertions) but iter-32's replay only
  covered 6-of-7 required-still-passing journeys — investigate why J-11 didn't run in the deterministic
  replay lane (stale selectors / excluded from the replay set / never wired) and fix so it participates
  this iteration, closing the gap per the DoD.
- **Dev handoff** at `docs/handoffs/goal-mcp-loop-iter-33-dev.md`.

`runs/goal-session-mcp-loop/state/blueprint.md` is **already updated** by the goal-decomposer (confirmed
by reading it): the J-20 Information-Architecture row (line 88), the Data Contract row for the "Daily
preflight verdict" (line 116), and the "iter-33 clarification" paragraph (line 258) are all present
verbatim. **No developer action needed on blueprint.md** — this matches the iter-31/32 precedent where
the decomposer pre-stages the blueprint before dev starts.

## Agents Required

- **backend-data: yes** -- `compute_preflight` composer, `ReadinessCfg` + `config.yaml` wiring, additive
  `preflight` field on `GET /api/health`, verdict-history log, fixture-matrix + regression/byte-identity
  tests.
- **frontend-ux: yes** -- `PreflightBanner` component + `layout.tsx` mount, `ReadinessProvider`/`lib/api.ts`
  extension, GO/DEGRADED/NO-GO visual states per the design system.

## Frontend Present
Frontend Present: yes

## Files to Create/Modify

Backend:
- `apps/backend/app/engine/readiness.py` -- add `compute_preflight()`; reuse `latest_data_date`,
  `_cached_warmup_dates`, and the evidence/graveyard/registry path resolvers. Do not touch
  `compute_readiness`'s return shape.
- `apps/backend/app/config.py` -- add `ReadinessCfg` (mirrors `StartupCfg`, ~line 489) + wire
  `readiness: ReadinessCfg` into the `Config` aggregator (~line 2159, alongside `startup: StartupCfg`).
- `config.yaml` -- add top-level `readiness:` block (`freshness_max_age_days`, severity map).
- `apps/backend/app/api/health.py` -- add the additive `preflight` field to the response dict.
- `apps/backend/tests/test_readiness.py` (new, or extend `test_health.py`) -- fixture matrix, config
  wiring, byte-identity, additive-shape, single-source, verdict-history-on-transition, error cases.
- Verdict-history writer -- co-locate in `readiness.py` or a small sibling module; config-resolved path.

Frontend:
- `apps/frontend/components/readiness-provider.tsx` -- expose `preflight` in the context value.
- `apps/frontend/lib/api.ts` -- add `preflight` field type to `HealthStatus`.
- `apps/frontend/components/preflight-banner.tsx` (new) -- GO/DEGRADED/NO-GO rendering.
- `apps/frontend/app/layout.tsx` -- mount `<PreflightBanner />` once, in the shell above `<main>`.

Journey scripts / docs:
- `runs/goal-session-mcp-loop/journey-scripts/J-11.json` -- verify/refresh so the deterministic replay
  lane actually exercises it this iteration.
- `docs/handoffs/goal-mcp-loop-iter-33-dev.md` -- new dev handoff.
- `runs/goal-session-mcp-loop/state/blueprint.md` -- already current; no edit expected.

## UI Evolution

- New user-facing capability: every decision surface (dashboard, `/stocks`, stock detail, `/watchlist`,
  `/evidence`, research) now carries one canonical `GO`/`DEGRADED`/`NO-GO` trust verdict with reasons — a
  risk-officer kill-switch UX.
- New information displayed: the verdict + a plain-language reasons list, identical everywhere (one
  source). No new numbers, scores, or edges.
- New user actions: none — the banner is read-only status; no buttons/forms (anti-goal #2, gates trust
  not orders).
- UI surface changes: one new cross-cutting layout-level banner in the app shell (`app/layout.tsx`); no
  new page.
- Navigation changes: none — cross-cutting chrome, like the existing `HealthBadge`; no nav-skeleton
  change, no `blueprint.reapproval-requested`.

## Visual Requirements

- Component patterns: new `PreflightBanner` component (its own quiet-strip vs loud-banner treatment,
  distinct from the compact `Badge` pill `HealthBadge` uses); follow `HealthBadge`'s pattern of reading
  state from `useReadiness()` for consistency.
- Layout: within the existing shell — `Sidebar` + flex column with a sticky `header` + `<main>`. Mount
  the banner between the header and `<main>` (or spanning the content column) inside `app/layout.tsx` so
  it appears on every route automatically, with zero per-page code.
- Key visual effects / tokens: the project's actual CSS custom properties (`apps/frontend/app/globals.css`)
  are **`--pos`** (green, success), **`--warn`** (amber, caution/stale), **`--neg`** (red, danger/risk) —
  the phase spec's prose says "`--pos`/success, `--warning`, `--danger`" but those latter two token names
  don't exist verbatim; use `--warn` and `--neg`. `GO` = quiet, thin, non-intrusive strip (`--pos`) that
  does not push page content or disrupt existing layouts (protects the required-still-passing surfaces).
  `DEGRADED` = loud amber banner (`--warn`) listing concrete reasons. `NO-GO` = loud danger banner
  (`--neg`) listing reasons and containing the **exact phrase "do not rely on today's board"**.
- States to handle: first-poll/loading (no fabricated `GO` before the first payload resolves — mirror
  `HealthBadge`'s `loading` state); backend-down/`unavailable` → honest `DEGRADED`/`NO-GO` with the
  reason, never blank; each reasons list renders plainly (no proven-language, no buy/sell language).

## Key Test Scenarios

- **Browser (J-20, healthy):** on dashboard, `/stocks`, a stock detail, `/watchlist`, `/evidence` — the
  identical quiet `GO` banner is pixel-visible; one md5-distinct capture per surface.
- **Browser (J-20, induced):** after a controlled config/env override (lower
  `readiness.freshness_max_age_days` or pin the freshness reference forward — never mutate committed
  seed data), the identical `DEGRADED`/`NO-GO` banner with concrete reasons renders on every listed
  surface; `NO-GO` contains "do not rely on today's board"; frames are md5-distinct from the GO
  captures; healthy state is restored afterward.
- **Browser (J-20, single-source):** DOM/asserted — the verdict + reasons come from the ONE `/api/health`
  `preflight` field; no page computes its own.
- **Backend fixture matrix:** every `{servability, freshness, integrity}` input combination maps to the
  exact configured verdict per the severity map; both `DEGRADED` and `NO-GO` are inducible.
- **Backend byte-identity:** `compute_readiness`'s `state`/`warmup` output is unchanged before/after
  (J-40 not regressed).
- **Backend contract:** `GET /api/health` additive-shape test (existing keys unchanged + new `preflight`
  key); single-source test (`compute_preflight` is the only producer; the banner has no second
  read/compute path).
- **Backend:** verdict-history appends only on a verdict transition, not on every poll.
- **Backend error cases:** DB unreachable, missing/unparseable ledger file, freshness beyond max age →
  each yields the mapped honest `DEGRADED`/`NO-GO` with reason; the health probe never raises or blanks.
- **Required-still-passing replay:** J-01, J-02, J-04, J-05, J-11 (dedicated, refreshed golden script),
  J-13, J-18 all still pass; the quiet GO banner does not disrupt their existing assertions.
- **Regression:** no new backend test failures from the `config.py`/`config.yaml` changes (see risk note
  below on pre-existing uncommitted state in those exact files).

## Notes / Risks for the Developer

- **Pre-existing uncommitted state collides with this iteration's own target files.** At dispatch time,
  `apps/backend/app/config.py`, `config.yaml`, `apps/backend/app/engine/{prices,scoring,warmup}.py`, and
  several test files (`test_config.py`, `test_config_engine.py`, `test_forward_testing.py`,
  `test_indexes.py`, `test_sectors.py`, `test_themes.py`, `test_warmup.py`) are already modified but
  uncommitted, plus untracked `test_scoring_window.py` and `docs/phases/goal-mcp-loop-iter-26.md` /
  `reports/qa/goal-mcp-loop-iter-26-test-plan.md` / `runs/goal-mcp-loop-iter-26/`. This looks like
  leftover WIP from an abandoned iter-26 attempt (likely the goal.md fast-platform §F "window the
  scoring inputs" item, given `test_scoring_window.py`) — unrelated to J-20/B-301. **Both files this
  iteration must edit (`config.py`, `config.yaml`) are already dirty.** Before editing them, read the
  existing diff to understand what's there, so iter-33's `ReadinessCfg`/`readiness:` additions are
  clearly separable from the pre-existing changes (don't silently fold unrelated iter-26 WIP into this
  iteration's commit; don't destructively discard it without confirming it's safe to drop — it may be
  real, salvageable work).
- **`.claude/project-template.md` is still the unfilled generic template** (a known gap noted in the
  iter-30/31/32 handoffs) — infer real stack/test commands from `scripts/dev.sh` and existing test files,
  per precedent.
- **Post-lane fix discipline (iter-13/20/22/31 trap):** J-20 is a rendered surface. If review/audit
  applies any fix to the banner or verdict *after* the canonical browser-qa lane runs, a fresh
  browser-qa + ux-regression-reviewer re-run against the final build is required before closure — a
  stale browser-qa FAIL under a later-passing `qa.md` does NOT satisfy the DoD; J-20 would land
  `partial`, not `passing`.
- **Pre-QA hygiene (iter-20 lesson):** `rm -rf apps/frontend/.next` and confirm both prod-mode services
  are reachable before dispatching browser-qa — a layout-level change is exactly what a stale `.next`
  bundle hides.
- **Out of scope, confirmed no drift:** B-113 sentinel, B-304 drift (= future J-21), B-103 time-machine,
  B-302 alerting, B-307 digest are NOT built here — the composer only leaves a config-entry + one
  component-branch seam for them. No `## Evidence Claim` this iteration (N/A — must not introduce
  proven-language); `certified-claims.jsonl` / `staging-ledger.jsonl` / `pre-registrations.jsonl` stay
  byte-identical; canonical Bonferroni divisor stays 8. No change to `compute_readiness`'s existing
  contract; no new page or nav section. This all matches goal.md's anti-goals #1/#2/#3/#5/#8 — **no
  scope creep detected** relative to the phase spec.
