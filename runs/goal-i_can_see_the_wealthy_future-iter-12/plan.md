# goal-i_can_see_the_wealthy_future-iter-12 Execution Plan

**J-12 — Methodology / Glossary: a config-backed catalog of every setup status + the VCP pattern, surfaced at `/methodology` AND as inline badge tooltips on `/stocks`. The FINAL Must-have → a clean pass yields 16/16 and a legitimate GOAL_ACHIEVED check next evaluation.**

The design is **purely additive and read-only**: ONE new computing module (`build_catalog`) that reads config (no score/return/bucket), ONE serving endpoint (`GET /api/methodology`), a new page + tooltip + sidebar entry, and a catalog-sourced `/stocks` setup filter. `models.py`, `scanner.py`, `scoring.py`, `setups.py`, `patterns.py`, `forward_testing.py`, and every existing read endpoint stay byte-unchanged → J-01–J-11/J-13–J-16 cannot structurally regress.

## What to Build

**Backend**
- `config.yaml`: a new top-level `methodology:` section — the single config-backed catalog. `intro` + an ordered `entries` list (the six setup statuses + the VCP pattern). Each entry carries human COPY (`meaning` + worked `example`) and `thresholds` rows that **reference** canonical config keys (`ref: "decision_rules.actionable.leadership"`, etc.) or pass plain `text` — the displayed numbers are NEVER re-typed, they resolve live from the engine's own config (so they always match).
- `config.py`: typed `MethodologyThreshold` (exactly one of `ref`/`text`), `MethodologyEntry` (`key`, `kind: Literal["setup","pattern"]`, `name`, `meaning`, `example`, `thresholds`), `MethodologyCfg` (`intro?`, `entries` min_length 1); add `methodology: MethodologyCfg` as a **required** field on `Config`. Add a generic `resolve_ref(config, "a.b.c")` (dotted-path lookup) and a `Config` `@model_validator(mode="after")` that resolves EVERY entry's `ref` and raises `ConfigError` on any unresolvable path (mirror `_invalidation_ma_period_is_an_indicator_period`, config.py:462).
- NEW `app/engine/methodology.py` — `build_catalog(config) -> dict`: resolve each `ref` to its live value (attach `cmp`/`unit`), pass `text` rows verbatim, emit `{intro, entries:[{key,kind,name,meaning,thresholds:[{label,cmp?,value?,unit?,text?}],example}]}`. **Assert completeness**: every `setups.ALL_STATUSES` status has a `kind:setup` entry and every `config.patterns` pattern (`vcp`) has a `kind:pattern` entry — else raise. Computes/stores NO score; contains NO threshold literal.
- NEW `app/api/methodology.py` — `GET /api/methodology` returns `build_catalog(get_config())` verbatim. Register in `main.py` (import on line 16; `app.include_router(methodology.router, prefix="/api")` after line 65). No DB/session.

**Frontend** (Next.js 15 App Router, TS, Tailwind, hand-rolled shadcn-style — NO new dependency)
- `lib/api.ts`: typed `fetchMethodology(signal?)` → `MethodologyCatalog` (`{intro?; entries: MethodologyEntry[]}`); throws on non-200 like the other fetchers (explicit "Backend unavailable", never fabricated copy).
- NEW `app/methodology/page.tsx`: fetch the catalog and render each entry — name + a `kind` chip (Setup/Pattern), the plain-language `meaning`, a compact thresholds list (`label cmp value unit`, or the `text` rule verbatim), and the worked `example`. Reuse the dense dark idiom (PageHeading/Card/palette tokens/monospace `num`) and the loading-skeleton / "Backend unavailable" / empty-state patterns from `app/stocks/page.tsx`. **No hard-coded per-entry copy or status/pattern list** — every entry comes from the fetched catalog.
- NEW `components/ui/info-tooltip.tsx`: accessible hand-rolled tooltip revealed on **hover AND keyboard-focus AND tap/click** (deterministically assertable on desktop + touch), dismissible, Card-like surface with palette tokens.
- `app/stocks/page.tsx`: remove the hard-coded `SETUP_STATUSES` array (line 36); fetch the catalog and (a) populate the Setup-filter options from the catalog's `kind:setup` entries in catalog order, (b) wire the info-tooltip to the setup badge (line 239) showing the catalog `meaning` for `row.setup.status`, (c) keep the VCP badge's per-row reason and additionally expose the catalog VCP `meaning`. **Graceful degradation (protect J-02):** if the catalog fetch fails, fall back to setup statuses present in the data so the leaderboard + filters still work. `setupVariant` (line 45, palette-token switch) stays — it is presentation, not copy.
- `components/sidebar.tsx`: add `{ href: "/methodology", label: "Methodology", icon: BookOpen }` to `NAV` **after Watchlist** (line 35); import `BookOpen` from lucide-react.

**Tests** — fast (the methodology surface needs no seeded DB): `test_methodology.py` (NEW: shape, completeness, matching-config keystone, config-only-extra-entry, "VCP"-not-a-status), `test_config*.py` (typed models validate; unresolvable `ref` → `ConfigError`; `MINIMAL_VALID` + minimal `methodology` still loads), `test_api_*.py` (`GET /api/methodology` 200 + shape via TestClient), `test_no_magic_numbers.py` (add `methodology.py` to `CALC_FILES`, line 19).

## Agents Required
- developer: **yes** — implements both backend (config + engine + API + tests) and frontend (page + tooltip + catalog-driven filter + nav).
- backend-data: **yes** — `config.yaml` methodology section, `config.py` typed models + `resolve_ref` + boot validator, `app/engine/methodology.py`, `app/api/methodology.py`, registration in `main.py`, backend tests.
- frontend-ux: **yes** — `/methodology` page, `info-tooltip` component, `/stocks` tooltip + catalog-sourced filter, sidebar nav entry.

## Frontend Present
yes

## Files to Create/Modify
- `config.yaml` — NEW top-level `methodology:` section (intro + 6 setup entries + vcp; thresholds `ref` real keys, never re-typed).
- `apps/backend/app/config.py` — typed `MethodologyThreshold`/`MethodologyEntry`/`MethodologyCfg`; required `methodology` on `Config`; `resolve_ref`; boot `model_validator` → `ConfigError` on unresolvable `ref`.
- `apps/backend/app/engine/methodology.py` — NEW `build_catalog(config)` (resolve refs to live values, completeness assertion, no score, no literal).
- `apps/backend/app/api/methodology.py` — NEW `GET /api/methodology`.
- `apps/backend/main.py` — import + register `methodology.router`.
- `apps/backend/tests/test_methodology.py` — NEW catalog unit tests.
- `apps/backend/tests/test_config.py` / `test_config_engine.py` — typed-model validation, unresolvable-`ref` `ConfigError`, `MINIMAL_VALID` + minimal `methodology`.
- `apps/backend/tests/test_api_*.py` — `GET /api/methodology` 200 + shape.
- `apps/backend/tests/test_no_magic_numbers.py` — add `methodology.py` to `CALC_FILES`.
- `apps/frontend/lib/api.ts` — `fetchMethodology` + `MethodologyCatalog`/`MethodologyEntry` types.
- `apps/frontend/app/methodology/page.tsx` — NEW glossary page.
- `apps/frontend/components/ui/info-tooltip.tsx` — NEW accessible tooltip.
- `apps/frontend/app/stocks/page.tsx` — remove `SETUP_STATUSES`; catalog-sourced filter; wire tooltip to setup/VCP badges; graceful fallback.
- `apps/frontend/components/sidebar.tsx` — add Methodology nav item after Watchlist.
- **Already written by the decomposer — do NOT duplicate:** `runs/goal-session-i_can_see_the_wealthy_future/state/blueprint.md` (Methodology IA row + feature-home row + Setup-&-pattern-catalog Data-Contract row + iter-12 serving note) and `runs/goal-session-.../state/blueprint.reapproval-requested`.

## UI Evolution (Frontend Present: yes)
- **New user-facing capability:** a dedicated Methodology / Glossary page explaining, from one config-backed source, what every setup status and the VCP pattern mean, the exact (config-matching) thresholds that define each, and a worked example — plus the same definition inline on every `/stocks` setup/VCP badge.
- **New information displayed:** the `/methodology` catalog (per entry: meaning + config-matching thresholds + worked example) and the inline badge definition tooltips on `/stocks`.
- **New user actions:** click "Methodology" in the sidebar; hover / tap / keyboard-focus a setup or VCP badge on `/stocks` to read its inline definition.
- **UI surface changes:** NEW `/methodology` page; NEW sidebar "Methodology" entry; NEW inline tooltip on `/stocks` setup + VCP badges; the `/stocks` Setup filter options now come from the catalog (same six statuses, now config-sourced).
- **Navigation changes:** sidebar gains "Methodology" after Watchlist — a nav-skeleton change. `blueprint.reapproval-requested` + the IA/feature-home/Data-Contract rows are **already written** (decomposer); no further blueprint edits required of the developer.

## Visual Requirements (Frontend Present: yes)
- **Component patterns:** `Card` per catalog entry; `Badge` for the `kind` chip (Setup / Pattern), reusing existing badge variants; monospace `num` for threshold values; the hand-rolled `info-tooltip` on a Card-like surface for inline badge definitions.
- **Layout:** app shell = persistent sidebar + main content (unchanged); `/methodology` is a vertical stack of entry Cards under a `PageHeading` — dense, dark, analytical; thresholds as a compact aligned list.
- **Key visual effects:** palette tokens only (`--accent` teal, `--pos`/`--neg`, `--surface`/`--surface-2`, `--border`); tooltip surface `--surface` + `--border`; numbers tabular/monospace; match the established dense-dark style of `/stocks`. No arbitrary hex/px.
- **States to handle:** loading skeleton, "Backend unavailable" error, and empty-state on `/methodology` — mirror `app/stocks/page.tsx`; tooltip must show on hover + focus + tap and be dismissible; `/stocks` filter degrades gracefully if the catalog fetch fails.

## Key Test Scenarios
- **J-12 (browser):** `/methodology` lists all six setup statuses + the VCP pattern, each with a plain-language meaning, config-matching thresholds (spot-check Actionable: Leadership ≥ `decision_rules.actionable.leadership`=80, Entry ≥ 70, Risk ≤ 60; VCP: its `patterns.vcp.*` thresholds + meaning + example), and a worked example; on `/stocks`, hover/tap/focus a setup badge → its inline definition appears and matches the `/methodology` meaning for that status.
- **Matching-config keystone (unit):** every displayed threshold `value` equals the LIVE config value its `ref` resolves to (no hard-coded copy, no drift) for the real config.
- **Config-driven (unit):** an alternate config with ONE extra catalog entry (referencing existing keys) renders via `build_catalog` / `GET /api/methodology` with **no** Python/TS change.
- **Completeness (unit):** the catalog covers every `setups.ALL_STATUSES` status (`kind:setup`) and every `config.patterns` pattern (`vcp`, `kind:pattern`); `"VCP"` is NOT among the setup entries / `ALL_STATUSES`.
- **Honest-failure (unit):** a catalog entry with an unresolvable `ref` raises `ConfigError` at load (never a silent default).
- **No magic numbers:** `methodology.py` in `CALC_FILES` and `test_engine_calc_code_has_no_magic_numbers` passes.
- **`MINIMAL_VALID` (unit):** updated with a minimal valid `methodology` section so the from-scratch config fixture still loads.
- **Regression — full 16-journey sweep + coherence (goal-completing):** J-02 filter still narrows rows; J-16 `/stocks` VCP filter + `/methodology` VCP entry present; `/`, `/stocks`, `/themes`, `/sectors`, `/scanner-runs` (+ Risk-off → 0 Actionable, J-07), `/system-health` (by-bucket/setup/regime/excess/control-group + by_vcp), `/backtest`, `/watchlist`, the global as-of switcher (J-13) all still render canonical values. Pre-existing engine/model/router files show an **empty diff**. Full backend suite passes; frontend `npm run build` clean (routes 11 → 12). Capture **distinct** PNGs per surface and `md5sum` them.

## Assumptions & Notes
- **Frontend Present = yes** (new page + nav + tooltips + filter change).
- **Per-row `setup.reason` (`setups._REASONS`) is NOT touched.** The catalog `meaning` is the *generic* status/pattern definition (config-backed, served by `/api/methodology`); the per-row `setup.reason` is a *different*, component-enriched value served on the stock row. The tooltip shows the catalog `meaning`. Refactoring `_REASONS` into config is OUT OF SCOPE (needless regression risk to J-02/J-05/J-06/J-07).
- **All recommended config `ref`s verified to exist:** `decision_rules.actionable.{leadership=80,entry=70,risk=60}`, `decision_rules.extended.{leadership=85,entry=50}`, `decision_rules.watch.leadership=75`, `decision_rules.avoid_risk=80` (scalar), `patterns.vcp.{min_contractions,max_base_depth_pct,contraction_shrink_ratio,max_last_contraction_pct,pivot_proximity_pct,volume_dryup_ratio}`, `buckets`. The boot validator will resolve them; `resolve_ref` must traverse BOTH Pydantic-model attributes AND mappings along the dotted path and resolve to a scalar (e.g. `decision_rules.avoid_risk` → 80).
- **Blueprint already updated by the decomposer** (IA + feature-home + Data-Contract rows + `blueprint.reapproval-requested`); the developer must NOT re-edit or duplicate it.
- **Testing strategy (iter-10 lesson — slow boot):** the methodology/config/api tests need no seeded DB → run them directly (fast). The full regression suite boots the walk-forward lifespan (~29 min in iter-11) → run it in the background and budget minutes (the foreground `sleep` guard blocks polling loops). Structural non-regression of J-01–J-11/J-13–J-16 rests on the **empty-diff** guarantee for the pre-existing engine/model/router files plus the deterministic value reproduction.
- **Runner-owner debt (NON-gating, chronic — runner-script scope, NOT product):** the dedicated browser-qa has SKIPped 10 consecutive iters (probes `GET /health` instead of `/api/health`; tears services down before browser-qa runs) and the audit handoff (`reports/audits/`) has been missing 10 full-depth iters. Spec text has proven ineffective across iters 3–11, so this is informational. The developer should be ready to **self-produce live evidence** (iter-7/iter-10 precedent): launch the backend with `CORS_ORIGINS=http://localhost:3835`, build the frontend with `NEXT_PUBLIC_API_URL=http://localhost:8835`, drive Chrome to `/methodology` and to a `/stocks` setup-badge tooltip, `await_text` on a row-only/entry value (never a filter/placeholder), and capture **distinct** md5-distinct PNGs per surface (J-12 spans two surfaces — one shot is not proof of two).
- **Evaluator/QA: confirm code presence first** (iter-9 silent-no-op lesson): `git status` (new `app/engine/methodology.py`, `app/api/methodology.py`, `app/methodology/page.tsx`, `components/ui/info-tooltip.tsx`), `grep -rln "methodology" apps/`, and the new tests — before scoring J-12. Distinguish "not built" from "built but un-verified".

## Scope / Goal Alignment
- **Aligned, no drift.** This implements Key Capability #16 and the `/methodology` Product Shape entry — the goal's last Must-have (J-12). The spec is explicitly tight; OUT OF SCOPE (no `_REASONS` refactor, no model/snapshot/score change, no second pattern, no config-edit UI) is respected and excluded.
- **Goal-completing iteration:** a clean J-12 + the full 16-journey regression sweep + full-product coherence takes the project to **16/16 Must-haves**, enabling a legitimate GOAL_ACHIEVED verdict at the next evaluation.
