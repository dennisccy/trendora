# Goal Iteration 4 — J-47: ≥100-term config-backed Glossary on /methodology + inline term help on every dense surface

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** i_can_see_the_wealthy_future_forever_with_my_loved_ones
- **Iteration:** 4
- **Mode:** next
- **Depth:** lean
- **Frontend Present:** yes
- **Target journeys:** J-47
- **Required-still-passing journeys:** J-01, J-02, J-09, J-12, J-18, J-25, J-26, J-29, J-36
- **Anti-goal reminders:**
  - "**Glossary copy lives in one catalog.** Every glossary definition and term tooltip MUST come from the single config-backed catalog; no component may hardcode or duplicate a definition; the setup/pattern entries stay single-sourced (referenced or hosted by the same catalog, never re-described)."
  - "**Setup & pattern vocabulary is config-driven in the UI too.** The glossary and tooltips MUST be generated from the single config-backed catalog — no hard-coded per-entry copy or status/pattern list in the frontend — so a new status or pattern is explained automatically."
  - "**No magic numbers.** Every scoring weight, threshold, decision-rule cutoff, bucket edge, universe entry, and theme definition MUST come from the config file — no such literal in calculation code." (Any threshold a glossary entry cites uses the existing `ref` resolution — never a re-typed number.)
  - "**Single source of truth.** Each of the six canonical scores (and the A–E bucket and setup status) MUST be computed exactly once by the scoring/regime engine and read identically by every page; the API and frontend MUST NOT recompute them."

## GOAL

After this iteration the user finds a categorized, client-side-searchable Glossary of ≥100 genuine domain terms on `/methodology`, and every dense surface (Research tables, Backtest scorecard/attribution headers, Stocks leaderboard headers, Dashboard breadth/candidate cards, Data Manager coverage headers) carries info-tooltips that read the exact same catalog entries — no bare jargon anywhere in the UI.

## BACKGROUND

This is the FINAL buildable journey of the session. J-42–J-46 all pass (iter-3 verdict CONTINUE, recommendation lean, COHERENCE-PASS); only J-47 remains failing, with J-22/J-23/J-24 honestly blocked-NA and non-vetoing per `docs/goal.md`. Per the approved blueprint, J-47 EXTENDS the SAME single config-backed catalog mechanism that already exists — `config.yaml` `methodology:` → `methodology:build_catalog` → `GET /api/methodology` (no new endpoint) — currently serving 9 setup/pattern entries with `ref`-resolved thresholds. The frontend already has the building blocks: `apps/frontend/components/ui/info-tooltip.tsx` (accessible hover/focus/click affordance, QA-assertable) and a catalog-fetch pattern in `apps/frontend/app/stocks/page.tsx`. This iteration is UI-bearing frontend + config + a moderate backend catalog extension with no concurrency-critical surface — lean is appropriate. If J-47 lands clean and the required journeys hold, the next evaluation is a GOAL_ACHIEVED candidate.

Lessons honored (see NOTES for the full list): the ≥100 terms must be GENUINE and config-sourced with a verifiable count; browser-QA must md5-check fresh screenshots (iter-3 had 8 byte-identical blank captures) and corroborate against the served `/api/methodology` payload; a new required config field goes into ALL FIVE inline test config dicts; `tsc --noEmit` is the frontend gate; the full backend suite (~46 min) is run once by the pump, not repeatedly by the dev.

## IN SCOPE

### Backend

- [ ] Extend the existing `methodology:` section of `config.yaml` with a **glossary catalog**: an ordered `categories` list (at minimum the six J-47 groups — Scores & Buckets; Setups & Patterns; Regime & Breadth; Universe & Data; Forward-testing & Evidence; Factor Lab & Statistics) and a `terms` list. Each term entry carries: the **literal UI term** as shown on a page, its category key, a **plain-language definition**, and optionally where-it-appears and/or a config-threshold reference using the **existing `ref` mechanism** (a `ref` path resolved at boot — never a re-typed number).
- [ ] Author **≥100 genuine glossary terms** in config covering the inventoried UI vocabulary — every page's titles, column headers, dropdown options, badge/stat labels — and INCLUDING all J-47 step-3 spot-check terms: breadth > 50-DMA, DMA (50/200-DMA), rank-IC, universe (vs symbols), decile, MAE, MFE, expectancy, hit-rate, dispersion, walk-forward, survivorship bias, horizon, excess return, composite (rank-blend), quantile, ATR%, pivot, invalidation. Definitions must be real explanations (the product's skeptical, plain-language voice), not padded filler.
- [ ] **Single-sourcing of setups/patterns:** the Setups & Patterns glossary category is **derived by `build_catalog` from the existing `methodology.entries`** (key/name/meaning projected as glossary rows referencing the full entry) — the existing 9 entries are hosted/referenced by the same mechanism, never re-described. Boot validation rejects a config glossary term whose key collides with a setup/pattern entry key (no second copy can exist).
- [ ] Extend `methodology:build_catalog` (`apps/backend/app/engine/methodology.py`) to assemble the glossary (categories + terms, `ref`s resolved, setup/pattern category derived) into the **same `GET /api/methodology` payload**. No new endpoint; no change to any other read path.
- [ ] Typed config models + boot validation in `apps/backend/app/config.py`: unique term keys, non-empty definitions, every term's category key exists, every `ref` resolves (an unresolvable ref fails the boot loudly, matching the existing catalog behavior).
- [ ] Unit tests: served glossary has ≥100 entries (counted from the SERVED payload, so the count is verifiable); all step-3 spot-check terms present; setup/pattern entries appear exactly once (derived, not duplicated); a config-injected extra term appears in `build_catalog` output with **no code change** (proves the J-47 step-5 contract); category/ref validation failures raise at boot; `test_no_magic_numbers.py` stays green.

### Frontend

- [ ] **Glossary section on `/methodology`** (`apps/frontend/app/methodology/page.tsx`): renders the served glossary as categorized groups in catalog order, with a **client-side live search input** that filters entries as the user types (term + definition matching; e.g. typing "IC" narrows to rank-IC etc.). Each entry shows the literal UI term, its plain-language definition, and (where present) its where-it-appears note and resolved threshold reference. Honest empty state when the search matches nothing. The existing setup/pattern section remains; its entries appear in the glossary as references to the same data, not duplicated copy.
- [ ] **Shared term-help helper** (e.g. `apps/frontend/lib/glossary.ts` + a thin wrapper around the existing `InfoTooltip`): looks up a term key in the fetched `/api/methodology` catalog and renders the info marker with the SAME definition. One shared fetch/lookup path — no component may hardcode a definition or term list.
- [ ] Wire info-tooltips reading the catalog onto the dense surfaces, at minimum:
  - **Research** (`/research`): Factor Lab + Event Study table column headers / stat labels (Rank-IC, decile, expectancy, MAE, MFE, hit-rate, composite, regime slices, risk-adjusted ratios, n…)
  - **Backtest** (`/backtest`): scorecard + attribution headers (forward return, excess vs SPY/QQQ/sector, horizon, by-rank-band, dispersion, hit-rate, control group, n…)
  - **Stocks** (`/stocks`): leaderboard column headers (Leadership, Entry Quality, Risk, A–E bucket, setup, RS, ATR%, invalidation…)
  - **Dashboard** (`/`): breadth and candidate-count cards (breadth > 50-DMA, Actionable / Breakout-watch / Pullback-watch, net new-high/low…)
  - **Data Manager** (`/data`): coverage table headers / figures (universe vs symbols, in-universe, thin/missing, bar count, date range…)
- [ ] A term key missing from the catalog degrades gracefully (no marker or an honest "no definition" — never a crash, never a hardcoded fallback definition).
- [ ] Frontend gate: `tsc --noEmit` clean (no ESLint in this project).

### New user-facing capability

The user can look up ANY domain term the UI shows: browse or live-search a categorized ≥100-term Glossary on `/methodology`, or hover/tap/focus the info marker right next to a dense column header / stat label and read the same definition in place.

### New information displayed

Plain-language definitions (with where-it-appears and config-threshold references where applicable) for the full UI vocabulary — on `/methodology` and inline on Research, Backtest, Stocks, Dashboard, and Data Manager surfaces.

### New user actions

- Glossary search input on `/methodology` (live filter).
- Info-marker hover/tap/focus on dense column headers and stat labels across the five surfaces.

### UI surface changes

- `/methodology`: new categorized + searchable Glossary section (below/alongside the existing setup & pattern catalog).
- `/research`, `/backtest`, `/stocks`, `/` (dashboard cards), `/data` (coverage): info-tooltip markers added to existing headers/labels. No new page, no nav change.

### Product surface delta

The dense, dark analytical workstation stops assuming the reader already knows the jargon: every term is explained in place and in one reference page, from one config catalog — finishing the product's "explainable, skeptical, evidence-driven" promise. This completes the last buildable Must-have journey of the session.

### Blueprint conformance

No new pages or nav entries. The Glossary lives on the existing **Methodology** home (`/methodology` — already annotated "J-47 full Glossary [TARGET]" in `blueprint.md`); tooltips ride existing surfaces (Backtest, Research, Stocks, Dashboard, Data Manager — all annotated for J-47 tooltips in the IA). Sidebar untouched.

### Data-contract additions

None — no new endpoint and no new canonical numeric value. The glossary extends the EXISTING registered Data-Contract row "Setup & pattern catalog → `methodology:build_catalog(config)` → `GET /api/methodology`" exactly as its J-47 TARGET clause prescribes (annotation updated to "iter-4 in flight" in `blueprint.md`). Any number a glossary entry displays is a `ref`-resolved config threshold — never a recomputed or re-typed value. Tooltips and the Glossary page read the SAME served entries; no second catalog, no duplicated copy.

## OUT OF SCOPE

- Any new API endpoint (the glossary rides `GET /api/methodology`) or any change to scoring/regime/forward-testing/data-manager engines.
- J-22/J-23/J-24 data fetches — the session loop makes its single best-effort attempt on resume per `docs/goal.md`; not part of this iteration's dev work, and their blocked-NA status never vetoes.
- Nav/sidebar changes, new pages, or moving any feature's canonical home.
- Localization/i18n of definitions; markdown-rich glossary content beyond plain text + the existing threshold-row rendering.
- Tooltips on every minor label in the app — the five named dense surfaces are the J-47 minimum and this iteration's bound.
- Editing glossary entries from the UI (config-file-only, like all other tunables).

## DEFINITION OF DONE

- [ ] J-47 passes via browser-qa-agent: categorized Glossary renders on `/methodology`; live search filters (e.g. "IC"); all step-3 spot-check terms readable; tooltips verified on `/research` and `/backtest` headers plus at least one tooltip each on `/stocks`, `/`, and `/data`; tooltip text matches the glossary entry for the same term.
- [ ] Served catalog verifiably contains ≥100 glossary entries (corroborated via the live `/api/methodology` JSON, not screenshots alone).
- [ ] Config-added-entry contract proven: a unit test shows a config-injected term appears in the served catalog with no code change, and review confirms the frontend renders entirely from the fetched catalog (no hardcoded term/definition anywhere).
- [ ] Required-still-passing journeys remain green: J-01, J-02 (tooltip-bearing Dashboard/Stocks), J-09, J-18 (Backtest), J-12 (methodology page — setup/pattern catalog intact, single-sourced), J-25, J-26, J-29 (Research labels), J-36 (Data coverage).
- [ ] No anti-goal violation introduced (especially "Glossary copy lives in one catalog" and "No magic numbers").
- [ ] Targeted backend test modules green during dev; full backend suite (~46 min) run once by the pump and green; `tsc --noEmit` clean.
- [ ] Dev handoff written at `docs/handoffs/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-4-dev.md`.

## TESTING REQUIREMENTS

- **Browser (J-47, plus required-still-passing spot checks):**
  1. `/methodology`: Glossary section present with the six categories; type "IC" in the search and assert the list filters live (assert the live DOM, not just await_text); read the step-3 spot-check terms (breadth > 50-DMA, DMA, rank-IC, universe vs symbols, decile, MAE, MFE, expectancy, hit-rate, dispersion, walk-forward, survivorship bias, horizon, excess return, composite, quantile, ATR%, pivot, invalidation).
  2. `/research` and `/backtest`: open the info marker on at least two dense headers each (e.g. Rank-IC, Mean MAE; Hit-rate, Expectancy) and assert the revealed panel text equals the glossary definition for the same term.
  3. `/stocks`, `/` (dashboard cards), `/data` (coverage headers): at least one tooltip each, same-equality assertion.
  4. Corroborate independently: fetch `GET /api/methodology` and assert glossary entry count ≥100 and the spot-check terms present in the payload.
  5. Required-still-passing: J-12 (setup/pattern entries + badge tooltip still correct and single-sourced), J-01/J-02/J-09/J-18/J-25/J-26/J-29/J-36 quick re-verification on the touched surfaces.
  6. **Evidence integrity (iter-3 lesson):** capture FRESH per-surface screenshots and md5sum them — if any two captures are byte-identical or a capture is a blank dark rectangle, re-capture; never submit blank evidence. Where a screenshot is doubtful, the `/api/methodology` payload + live DOM assertions are the corroborating record.
- **Unit/integration (targeted modules during dev; full suite via the pump):**
  - `test_methodology.py` / `test_api_methodology.py`: ≥100-entry count from the served payload; spot-check terms; categories ordered; `ref` resolution; setup/pattern category derived from `methodology.entries` with no duplicate copy; key-collision boot rejection; config-injected extra entry appears with no code change.
  - `test_config.py` + boot validation paths: invalid category key, duplicate term key, unresolvable `ref` each fail loudly.
  - If a new REQUIRED config field is introduced, update ALL FIVE inline test config dicts — `test_config.py`, `test_config_engine.py`, `test_sectors.py`, `test_themes.py`, `test_indexes.py` — and grep the new key across `apps/backend/tests` to catch any fixture missed.
  - `test_no_magic_numbers.py` remains green (no threshold literal enters `methodology.py` or any frontend component).
  - Frontend: `tsc --noEmit`.
- **Error cases:**
  - Boot fails loudly on: duplicate glossary keys, a term referencing a nonexistent category, an unresolvable threshold `ref`, a glossary term colliding with a setup/pattern entry key.
  - `/methodology` API failure → the page's existing honest no-definitions state (never fabricated copy); a tooltip for a missing term key degrades gracefully (no crash, no hardcoded fallback).
  - Glossary search with no matches → explicit empty state.

## NOTES

- **GOAL_ACHIEVED candidacy:** after this iteration the only non-passing journeys are J-22/J-23/J-24, which `docs/goal.md` defines as blocked-NA and non-vetoing. The evaluator decides; this spec deliberately adds nothing beyond J-47.
- **Lessons applied (from session lessons.md):**
  - ≥100 terms must be GENUINE and config-sourced; the count is asserted against the served payload so it is verifiable, and review should reject filler definitions.
  - Iter-3 browser evidence defect: 8 PNGs were a byte-identical blank dark rectangle (md5 `23fe5583…`). QA must md5-check fresh captures and corroborate via the served `/api/methodology` payload + pinned-open tooltip DOM assertions.
  - New required config fields → ALL FIVE inline test config dicts (see TESTING REQUIREMENTS).
  - No ESLint in this project — `tsc --noEmit` is the frontend gate.
  - Full backend suite is ~46 min: the developer runs the targeted modules; the pump runs the full suite once.
  - Controlled-input gotcha (project memory): Chrome MCP events may not fire React `onChange` on this frontend — if typing in the glossary search does not filter, use the native-setter + bubbling event pattern in an eval, then assert the live DOM.
  - Dead-shell gotcha (project memory): if every page renders an un-hydrated shell with 404s on `_next/static` chunks, the dev server's `.next` was clobbered — record SKIPPED and restore the dev server, not FAIL.
- **InfoTooltip is QA-friendly by design:** a click pins the panel open and mounts the content in the DOM (`role="tooltip"`), so tooltip-equality assertions are deterministic.
- The J-47 step-5 "config-added entry, no code change" leg is proven by the unit test (config-injected entry served) plus reviewer confirmation that the frontend is fully catalog-driven; live-editing the committed `config.yaml` against the running :8835 backend during QA is unnecessary and discouraged (keeps the working tree clean for the release step).
- Blueprint updated this iteration (annotation-only, no nav change, no reapproval): J-46 flipped to built (iter-3); the catalog row's J-47 clause and the Methodology nav line marked "TARGET — iter-4 in flight".
