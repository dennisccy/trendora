# goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-4 Dev Handoff

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-4
**Date:** 2026-06-11
**Agent:** developer
**Status:** complete

## What Was Built

J-47 — a ≥100-term, config-backed terminology **Glossary** on `/methodology` plus inline term tooltips
on the five dense surfaces, all riding the SINGLE existing catalog mechanism (`config.yaml` `methodology:`
→ `methodology:build_catalog` → `GET /api/methodology`). No new endpoint, no second catalog, no
hardcoded definitions.

### Backend
- Extended the `methodology:` block of `config.yaml` with an ordered `categories` list (the six J-47
  groups) and a `terms` list of **111 authored terms** covering the inventoried UI vocabulary, including
  every J-47 step-3 spot-check term. Several terms cite config thresholds via the existing `ref`
  mechanism (resolved live — never a re-typed number).
- The **Setups & Patterns** glossary category is **derived by `build_catalog` from the existing
  `methodology.entries`** (9 setup/pattern rows projected as glossary terms referencing the full entry
  via `entry_key`) — single-sourced, never re-described. Served count = 111 authored + 9 derived =
  **120 terms** (verifiable from the served payload).
- New typed config models `GlossaryCategory` + `GlossaryTerm` in `app/config.py`, with boot validation:
  unique category keys, unique term keys, every term's `category` exists, non-blank definitions, and a
  **key-collision guard** (an authored term colliding with a setup/pattern entry `key`/`name` fails the
  boot loudly — no second copy of a setup/pattern can exist). Threshold `ref`s on terms are resolved at
  boot by the existing `_methodology_refs_resolve` validator.
- `resolve_ref` extended to support **sequence indices** (e.g. `regime.label_edges.0.min`) so a glossary
  term can cite a live list-element config value — purely additive; existing string-path resolution is
  unchanged.
- `build_catalog` now emits a `glossary` object (`{categories:[{key,label,terms:[…]}]}`) on the SAME
  `GET /api/methodology` payload, grouped in catalog order, derived setups/patterns leading their
  category. `methodology.py` still contains **no numeric literal** (`test_no_magic_numbers` green).

### Frontend
- `lib/glossary.tsx` — a `GlossaryProvider` (mounted in the app shell) that fetches `/api/methodology`
  ONCE and builds a `term → GlossaryTerm` lookup; `useGlossary` / `useGlossaryTerm` hooks. Single shared
  fetch/lookup path — no component hardcodes a definition or term list.
- `components/ui/term-info.tsx` — `<TermInfo term="rank-IC">…</TermInfo>`, a thin wrapper around the
  existing `InfoTooltip` that reads the SAME catalog entry. A missing term key (or not-yet-loaded /
  failed fetch) degrades gracefully: renders the children with no marker — never a crash, never a
  hardcoded fallback.
- `/methodology`: new categorized **Glossary section** below the existing setup/pattern catalog, with a
  **live client-side search** input (filters on term + definition; honest empty state on no match). The
  existing setup/pattern catalog is unchanged; the glossary's setup/pattern rows reference the same data.
- Inline info-tooltips wired onto the five dense surfaces (all reading the shared catalog):
  - **Research** (`/research`): Decile / Mean fwd return / Risk-adjusted; Rank-IC / n / long-short
    spread; the event-study horizon table (Horizon, Median, % Positive, Dispersion, Expectancy, Mean
    MAE, Mean MFE, Return/downside-dev, Return/MAE); combination table (Cohort→composite, Hit-rate).
  - **Backtest** (`/backtest`): scorecard table (Horizon, Cohort→forward return, vs SPY/QQQ/Sector→excess
    return, Random peers→control) + the Return Attribution panels (contributors & detractors, by-sector,
    by-rank-band, hit-rate, dispersion, median, n) via `components/return-attribution.tsx`.
  - **Stocks** (`/stocks`): leaderboard headers Leadership / Entry Quality / Risk / Setup / Reason.
  - **Dashboard** (`/`): Market Regime, the three breadth metric cards (breadth >50/200-DMA, net
    new-high/low), Candidate Counts (setup status) + each count label (Actionable / Breakout-watch /
    Pullback-watch, resolved from the derived setup rows).
  - **Data Manager** (`/data`): coverage figures Universe / Symbols; per-symbol table headers In universe
    / Date range / Bars / Flag (thin/missing).
- All 32 distinct `TermInfo` term keys used in the UI (incl. the three dashboard setup-name labels)
  verified to resolve in the served catalog — no silent missing markers.

## Files Changed
- `config.yaml` -- added `methodology.categories` (6) + `methodology.terms` (111 authored terms).
- `apps/backend/app/config.py` -- `GlossaryCategory`/`GlossaryTerm` models, glossary boot validation
  (unique keys, category existence, non-blank defs, setup/pattern collision guard), term-threshold ref
  resolution, and `resolve_ref` sequence-index support.
- `apps/backend/app/engine/methodology.py` -- `build_catalog` assembles the `glossary` payload (derived
  setups/patterns + authored terms grouped by category, refs resolved).
- `apps/backend/tests/test_glossary.py` -- NEW: 16 tests (≥100 served count, spot-check terms, categories
  ordered, derived single-sourcing, collision/duplicate/bad-category/unresolvable-ref boot rejections,
  config-injected-term-no-code-change, term ref resolves live).
- `apps/backend/tests/test_api_methodology.py` -- added 3 tests (served glossary ≥100, spot-check terms,
  setups/patterns single-sourced).
- `apps/frontend/lib/api.ts` -- `GlossaryTerm`/`GlossaryCategory`/`MethodologyGlossary` types; `glossary?`
  on `MethodologyCatalog`.
- `apps/frontend/lib/glossary.tsx` -- NEW: `GlossaryProvider` + `useGlossary`/`useGlossaryTerm`.
- `apps/frontend/components/ui/term-info.tsx` -- NEW: `<TermInfo>` wrapper around `InfoTooltip`.
- `apps/frontend/app/layout.tsx` -- mounted `GlossaryProvider` in the app shell.
- `apps/frontend/app/methodology/page.tsx` -- Glossary section + live search + empty state.
- `apps/frontend/app/stocks/page.tsx` -- leaderboard header tooltips.
- `apps/frontend/app/page.tsx` -- dashboard regime/breadth/candidate tooltips.
- `apps/frontend/app/research/page.tsx` -- factor-lab + event-study header tooltips.
- `apps/frontend/app/backtest/page.tsx` -- scorecard header tooltips.
- `apps/frontend/components/return-attribution.tsx` -- attribution panel tooltips.
- `apps/frontend/app/data/page.tsx` -- coverage figure + per-symbol header tooltips.

## Tests Run
Command (backend): `cd apps/backend && .venv/bin/python -m pytest tests/ -v`
- Targeted, run to completion in the foreground (fast path per session pytest discipline):
  - `test_glossary.py test_methodology.py test_api_methodology.py test_no_magic_numbers.py` →
    **38 passed, 0 failed**.
  - All five inline-config-dict modules `test_config.py test_config_engine.py test_sectors.py
    test_themes.py test_indexes.py` → **98 passed, 0 failed** (6m18s; heavy walk-forward boot in
    test_config_engine).
- **FULL SUITE GREEN — run by pump.** `cd apps/backend && .venv/bin/python -m pytest tests/ -q` to
  completion: **678 passed, 4 skipped, 0 failed in 2808.58s (0:46:48)** — +19 vs iter-3's 659 (the new
  glossary tests), zero failures, zero regressions. (Raw log: /tmp/trendora-iter4-fullsuite.log.)

Command (frontend gate): `cd apps/frontend && npx tsc --noEmit` → **clean (exit 0)**. (ESLint is not
installed in this project; `tsc --noEmit` is the frontend gate.)

## Known Issues
- **`config.yaml` schema additions are optional** (`categories`/`terms` default empty), so the five
  inline test config dicts did NOT need a new required key — confirmed by grepping `categories`/`terms`/
  `glossary` across `apps/backend/tests` (only the new glossary/api-methodology tests reference them).
  The ≥100 count is asserted against the committed real config (the SERVED payload), not the minimal
  fixtures.
- **Live `GET /api/methodology` on the already-running :8835 backend still serves the PRE-EDIT config**
  (it loads config once at boot; the running uvicorn pid 901695 predates this iteration). I did NOT
  restart :8835 (project memory: it carries user-added bars and has a slow walk-forward boot). The new
  glossary is proven via the `TestClient`-based unit/API tests, which read the committed `config.yaml`
  directly. The pump/QA's fresh backend start will serve the new glossary live.
- **`test_universe_screen.py` was not run by the dev** — it triggers a heavy walk-forward boot and
  exceeded the foreground timeout; it is part of the full suite the pump runs. The only production change
  it could touch is the additive `resolve_ref` sequence-index branch (existing string-path resolution is
  byte-identical), and the committed config loads cleanly.
- I started no servers; the pre-existing dev servers on :8835 (uvicorn) and :3835 (next) were left
  running and untouched.
