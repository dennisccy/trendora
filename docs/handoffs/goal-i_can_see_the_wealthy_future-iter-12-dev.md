# goal-i_can_see_the_wealthy_future-iter-12 Dev Handoff

**Phase:** goal-i_can_see_the_wealthy_future-iter-12
**Date:** 2026-05-31
**Agent:** developer
**Status:** complete

## What Was Built

**J-12 — Methodology / Glossary: a single config-backed catalog of every setup status + the VCP pattern, surfaced at `/methodology` AND as inline `/stocks` badge tooltips. The final Must-have.** Purely additive and read-only: ONE new computing module, ONE serving endpoint, a new page + tooltip + sidebar entry, and a catalog-sourced `/stocks` setup filter. No model/snapshot/score change.

- **`config.yaml` — new top-level `methodology:` section**: an `intro` + 7 ordered entries (the 6 setup statuses + the `vcp` pattern). Each entry carries plain-language `meaning` + `example` and `thresholds` rows that **reference** real config keys (`ref: decision_rules.actionable.leadership`, `patterns.vcp.min_contractions`, …) or pass a prose `text` rule. No threshold number is re-typed — they resolve live from the same config the engines read (the "matching config" keystone).
- **`config.py` — typed models + boot validator**: `MethodologyThreshold` (exactly one of `ref`/`text`), `MethodologyEntry` (`key`, `kind: Literal["setup","pattern"]`, `name`, `meaning`, `example`, `thresholds`), `MethodologyCfg` (`intro?`, `entries` min_length 1); `methodology` added as a **required** `Config` field. A generic `resolve_ref(config, "a.b.c")` (dotted-path lookup over pydantic attrs AND mappings) + a `@model_validator(mode="after")` that resolves EVERY entry `ref` at boot and raises `ConfigError` on any unresolvable path (never a silent/placeholder number).
- **NEW `app/engine/methodology.py` — `build_catalog(config) -> dict`**: resolves each `ref` to its live value (attaching `cmp`/`unit`), passes `text` rows verbatim, and **asserts completeness** — every `setups.ALL_STATUSES` status has a `kind:"setup"` entry and every `config.patterns` pattern has a `kind:"pattern"` entry (raises otherwise). Computes/stores NO score; contains NO threshold literal (added to the no-magic-numbers `CALC_FILES`).
- **NEW `app/api/methodology.py` — `GET /api/methodology`**: returns `build_catalog(get_config())` verbatim; registered in `main.py`. No DB/session.
- **Frontend** (Next.js 15, no new dependency): NEW `/methodology` page; NEW accessible `info-tooltip` (hover + keyboard-focus + tap/click, dismissible); `/stocks` setup + VCP badges expose the catalog definition; the `/stocks` Setup filter is now catalog-sourced (hard-coded `SETUP_STATUSES` removed) with graceful fallback to data statuses if the catalog fetch fails (protects J-02/J-15); sidebar gains "Methodology" after Watchlist; `lib/api.ts` adds `fetchMethodology` + types.

## Files Changed

- `config.yaml` — NEW `methodology:` section (intro + 6 setup entries + vcp; thresholds reference real keys).
- `apps/backend/app/config.py` — `MethodologyThreshold`/`MethodologyEntry`/`MethodologyCfg`; required `methodology` on `Config`; `resolve_ref` + `_node_keys`; boot `_methodology_refs_resolve` validator.
- `apps/backend/app/engine/methodology.py` — NEW `build_catalog` (resolve refs, completeness assertion, no score, no literal).
- `apps/backend/app/api/methodology.py` — NEW `GET /api/methodology`.
- `apps/backend/main.py` — import + register `methodology.router`.
- `apps/backend/tests/test_methodology.py` — NEW (shape, completeness, matching-config keystone, config-only-extra-entry, VCP-not-a-status, unresolvable-ref → ConfigError).
- `apps/backend/tests/test_api_methodology.py` — NEW (`GET /api/methodology` 200 + shape via an isolated router app — no walk-forward boot).
- `apps/backend/tests/test_config.py` / `test_config_engine.py` — minimal `methodology` added to the from-scratch fixtures; unresolvable-ref + ref-xor-text load-time tests.
- `apps/backend/tests/test_no_magic_numbers.py` — `methodology.py` added to `CALC_FILES`.
- `apps/frontend/lib/api.ts` — `fetchMethodology` + `MethodologyCatalog`/`MethodologyEntry`/`MethodologyThresholdRow`.
- `apps/frontend/app/methodology/page.tsx` — NEW glossary page.
- `apps/frontend/components/ui/info-tooltip.tsx` — NEW accessible tooltip.
- `apps/frontend/app/stocks/page.tsx` — catalog-sourced Setup filter + badge tooltips + graceful fallback.
- `apps/frontend/components/sidebar.tsx` — "Methodology" nav item.
- **Pre-existing engine/model/router files are byte-unchanged** (`models.py`, `scanner.py`, `scoring.py`, `setups.py`, `patterns.py`, `forward_testing.py`, all existing `app/api/*` routers) → J-01–J-11/J-13–J-16 cannot structurally regress (empty-diff guarantee).
- Blueprint (`state/blueprint.md` + `blueprint.reapproval-requested`) was written by the decomposer — NOT touched by the developer.

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -v`

- **Targeted fast suites (no seeded DB needed):** `test_methodology.py` + `test_api_methodology.py` + `test_no_magic_numbers.py` = **24 passed**; `test_config.py` + `test_config_engine.py` = **62 passed**. TDD: the new tests were written first and observed RED (`ImportError: resolve_ref`, missing endpoint) before implementation, then GREEN.
- **Full backend suite (`tests/`, walk-forward lifespan boot ≈ 15 min):** first run finished **246 passed, 2 failed**: `tests/test_sectors.py::test_min_history_bars_floor_reports_na_for_short_history` and `tests/test_themes.py::test_theme_with_no_member_history_degrades_to_na_not_crash`. Both failed with `ConfigError: methodology Field required`. Cause: each of those two test modules defines its OWN from-scratch `_SYNTH_CFG` dict (synthetic configs written to a temp file and `load_config`-ed); making `methodology` a required `Config` field meant those two fixtures no longer validated. This is the same "add the newly-required section to every from-scratch fixture" step done for `patterns` in iter-11 — I had updated `test_config.py`/`test_config_engine.py` but initially missed these two `_SYNTH_CFG` fixtures.
  - **Fix:** added a minimal valid `methodology` block (one entry whose single `ref` resolves to `decision_rules.actionable.leadership`) to `_SYNTH_CFG` in BOTH `apps/backend/tests/test_sectors.py` and `apps/backend/tests/test_themes.py`. No product/source change — fixtures only.
  - **Re-verified:** the two previously-failing tests pass, and a clean full-suite re-run confirms it: **`248 passed in 901.36 s (0:15:01)`, FINAL_EXIT=0 — zero failures.** The whole backend suite is green.
- **Anti-goal greps (clean):** no `order`/`broker`/brokerage/execution path, no secrets, and no `localStorage` token use in the new backend or frontend code.
- **Frontend:** `cd apps/frontend && npm run build` → **clean** (compiles + typechecks). App routes **11 → 12**; the new `○ /methodology` route is listed. No new dependency.

## Live Evidence (self-produced; see `runs/<phase>/evidence/`)

Because the dedicated browser-qa has chronically SKIPped, I self-produced live evidence (iter-7/iter-10 precedent). Backend launched on :8835 (`CORS_ORIGINS=http://localhost:3835`), frontend (`next dev`) on :3835 with `NEXT_PUBLIC_API_URL=http://localhost:8835`; Chrome driven against the live stack; **both dev servers were stopped by port afterwards**.

- `GET /api/methodology` (live) → **200** with the matching-config catalog: Actionable `Leadership ≥ 80, Entry ≥ 70, Risk ≤ 60`; VCP `Min contractions ≥ 2, Max base depth ≤ 35%, shrink ≤ 0.9, Final ≤ 12%, Within pivot ≤ 8%, Volume dry-up ≤ 0.9`. Saved: `evidence/api-methodology.json`, `evidence/api-health.json`.
- **Surface 1 — `/methodology`** (`evidence/iter12-methodology.png`, 1905×1810): renders all six setup statuses + the VCP pattern, each with meaning, config-matching thresholds, and example; "Methodology" is in the sidebar.
- **Surface 2 — `/stocks` setup-badge tooltip** (`evidence/iter12-stocks-tooltip.png`, 1920×870): clicking a setup badge's info button opened a `[role="tooltip"]` whose text — *"A strong leader whose entry is extended — too far from a low-risk entry to chase. Wait for a pullback rather than buying here."* — **exactly matches the `/methodology` meaning for "Extended"**.
- The two PNGs are **distinct** (different md5sums + dimensions), satisfying the two-surface evidence requirement.

## Known Issues

- The `/stocks` info tooltip is an absolutely-positioned pop-over inside the leaderboard table (which has `overflow-x-auto`); on the very last visible row it can extend slightly past the table's scroll area. The same definitions are always fully visible on the dedicated `/methodology` page, and the panel text mounts in the DOM as soon as it is opened. The setup-badge inline explanation is reachable via click/tap (not title-only), per spec.
- Out of scope (intentionally not done): refactoring `setups._REASONS` into config, a second detected pattern, a config-editing UI, and tooltips on pages other than `/stocks`.
- Anti-goal greps stay clean: no `order`/`broker`/capital-deployment path was added; the methodology surface adds no auth and no `localStorage` token use.

## Suggested Next Phase

This was the **goal-completing iteration**: with J-12 done, **16/16 Must-have journeys are now built**, so the next step is the goal evaluation itself — it should be able to legitimately reach GOAL_ACHIEVED (16/16) after the full 16-journey regression sweep + full-product coherence confirm no regression. No further feature phase is required for the goal; any follow-on would be the deferred nice-to-haves (paper portfolio, news/LLM enrichment, a config-editing UI) in a new session.
