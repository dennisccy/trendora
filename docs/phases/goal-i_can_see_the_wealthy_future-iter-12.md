# Goal Iteration 12 — Methodology / Glossary: a config-backed catalog of every setup status + detected pattern, surfaced as `/methodology` AND inline badge tooltips (J-12) — the final Must-have

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** i_can_see_the_wealthy_future
- **Iteration:** 12
- **Mode:** next
- **Depth:** full
- **Frontend Present:** yes
- **Target journeys:** J-12
- **Required-still-passing journeys:** ALL fifteen others — J-01, J-02, J-03, J-04, J-05, J-06, J-07, J-08, J-09, J-10, J-11, J-13, J-14, J-15, J-16. This is the **goal-completing iteration**: pair J-12 with a **full 16-journey regression sweep + full-product coherence** so the next evaluation can legitimately reach GOAL_ACHIEVED (16/16). Highest regression attention: **J-02** (the `/stocks` setup-filter vocabulary now reads the catalog), **J-15** (an extra small catalog fetch on `/stocks` must not break warm load), **J-16** (its acceptance step 4 — the VCP glossary entry — is delivered HERE).
- **Anti-goal reminders (verbatim from `docs/goal.md`):**
  - **Setup & pattern vocabulary is config-driven in the UI too.** The glossary and tooltips MUST be generated from the single config-backed catalog — no hard-coded per-entry copy or status/pattern list in the frontend — so a new status or pattern is explained automatically. *(extends No magic numbers — THE central anti-goal this iteration)*
  - **No magic numbers.** Every scoring weight, threshold, decision-rule cutoff, bucket edge, universe entry, and theme definition MUST come from the config file — no such literal in calculation code.
  - **Single source of truth.** Each of the six canonical scores (and the A–E bucket and setup status) MUST be computed exactly once by the scoring/regime engine and read identically by every page; the API and frontend MUST NOT recompute them. The same symbol's score MUST NOT differ between two views. *(critical)*
  - **No recompute in the read path.** Read endpoints MUST serve canonical values from the persisted immutable snapshot for the resolved as-of date; they MUST NOT recompute scores/returns/buckets per request. *(extends Single source of truth)*
  - **No fabricated data.** On a data-provider failure the system MUST surface an explicit stale/unavailable state and MUST NOT synthesize prices or scores to force a green journey. *(here: a glossary threshold reference that cannot be resolved from config MUST raise an explicit error at boot — never a silent/placeholder number)*
  - **VCP is a pattern, not a status.** VCP MUST NOT enter the mutually-exclusive setup-status enum and MUST NOT by itself promote a name to "Actionable". *(critical — here: the catalog lists VCP as a `pattern` entry, NEVER as a 7th setup status)*
  - **Scores must be explainable.** Every displayed score MUST carry its named component breakdown — no score may be shown as a bare number with no reasons.
  - **Honest limitations surfaced.** Breadth and new-high/new-low metrics are universe-relative; walk-forward evidence MUST be labelled as carrying survivorship bias. *(standing — must remain true across the regression sweep)*
  - **Snapshots are immutable.** A persisted `scanner_run` and its result rows MUST never be updated or overwritten after creation. *(standing — this iteration writes NO snapshot/model change)*
  - **No order/execution path.** No brokerage, order-placement, or capital-deployment code may exist or be reachable; Trendora is research-only. *(critical)*
  - **No secrets in source.** No hard-coded credentials, API keys, or tokens anywhere.
  - The frontend MUST NOT store auth tokens in `localStorage` (no auth exists; the methodology fetch adds none).

## GOAL

A user can open a new **Methodology / Glossary** page (`/methodology`) and read, for **all six setup statuses** (Actionable, Breakout-watch, Pullback-watch, Extended, Avoid, Risk-off-watchlist) **and the VCP pattern**, each entry's **plain-language meaning**, **the exact config thresholds that define it (matching config)**, and a **worked example** — and on `/stocks` they can **hover/tap/focus any setup (and VCP) badge** to read that same definition inline. The list is generated from a **single config-backed catalog**, so adding an entry in `config.yaml` makes it appear on the page AND in the tooltips with **no code change**.

## BACKGROUND

iter-11 landed **J-16 (VCP)** cleanly → **15/16 Must-haves pass**. The only journey still `failing` is **J-12** (`/methodology` glossary + inline tooltips), unbuilt **by design**: it was sequenced LAST so the catalog can document the VCP pattern entry that landed in iter-11 (whose reason/thresholds were deliberately kept config-backed to make this trivial). This iteration builds J-12 → a clean pass yields **16/16** and a legitimate GOAL_ACHIEVED check next evaluation.

**Why full depth:** a NEW config section + typed loader models + a boot-time ref-resolution validator + a new backend engine module + a new API endpoint + a new frontend route + a new IA home (→ `blueprint.reapproval-requested`) + a new accessible tooltip component + a change to the `/stocks` filter vocabulary + new tests, **paired with a full 16-journey regression sweep + full-product coherence** to reach the goal. This is well beyond lean scope. Prior depth was full; prior verdict CONTINUE.

**The design is purely additive and read-only — no model/snapshot change, no score/return recompute.** The methodology catalog is a NEW displayed value with ONE computing module (`app.engine.methodology:build_catalog`) and ONE serving endpoint (`GET /api/methodology`); it computes/stores no score — it reads the config-backed copy (meaning + example + which config keys to surface) and resolves the **live threshold values from the canonical config blocks** (`decision_rules.*`, `patterns.vcp.*`, `buckets.*`). Because the displayed thresholds are resolved by reference from the SAME config the engines read, they cannot drift ("matching config"). `models.py`, the scanner, scoring, setups, patterns, and every existing read endpoint are **untouched** — so J-01–J-11, J-13–J-16 cannot structurally regress.

**Why the per-row reason is NOT touched.** `setups._REASONS` produces each stock's *per-row*, component-enriched `setup.reason` (e.g. "Strong leader at a constructive entry… Driven by Moving-average stack…"). The catalog `meaning` is the *generic* definition of a status (e.g. what "Actionable" means in general). These are **different displayed values** with different sources; the tooltip shows the catalog `meaning` (the glossary definition), NOT the per-row reason. Do **not** refactor `_REASONS` into config — that is out of scope and a needless regression risk to J-02/J-05/J-06/J-07.

**Lessons applied (from `lessons.md`):**
- **iter-11 (additivity):** to prove a NEW additive surface perturbs no existing canonical value, ride existing seams and keep the existing files byte-unchanged. Here `models.py`/`scanner.py`/`scoring.py`/`setups.py`/`patterns.py`/the existing read endpoints have an **empty diff**; the only backend additions are `config.yaml` (+`methodology` section), `config.py` (+typed models + resolver + validator), a NEW `app/engine/methodology.py`, a NEW `app/api/methodology.py`, and its registration in `main.py`. The matching-config keystone is the additivity dual: assert each displayed threshold **equals the live config value it references** (no hard-coded copy, no drift).
- **iter-9 (silent dev no-op):** a full-depth dispatch can reach the evaluator having produced **zero code**. The developer MUST actually create the new files, edit the listed files, write the tests, and write the dev handoff; the evaluator MUST confirm code presence from `git status` + filesystem + `grep -rln "methodology" apps/` before scoring J-12.
- **iter-10 (slow boot):** any test that boots a walk-forward lifespan is slow (~230s+ targeted, ~885s full). The methodology endpoint needs NO seeded DB (it reads config only), so its own tests are fast — run them directly. For the regression sweep, run the **targeted** suites and budget minutes (background task; the foreground `sleep` guard blocks polling loops).
- **iter-3/5/8/11 (chronic runner debt) + iter-7 (live verify):** the dedicated browser-qa has SKIPped **10 consecutive** iters and the audit handoff has been missing 10 — both are **runner-script** gaps, NOT product. Be ready to **self-produce live evidence**: launch the backend with `CORS_ORIGINS=http://localhost:3835`, build the frontend with `NEXT_PUBLIC_API_URL=http://localhost:8835`, drive Chrome to `/methodology` and to a `/stocks` badge tooltip; `await_text` on a row-only / entry value, never a filter/placeholder.
- **iter-6 (distinct evidence):** J-12 spans two surfaces (the `/methodology` page and a `/stocks` badge tooltip). Capture **distinct** PNGs per surface and `md5sum` them — one full-page shot is not proof of two surfaces.

## IN SCOPE

### Backend

- [ ] **`config.yaml` — add a new top-level `methodology:` section: the single config-backed catalog.** An ordered list of entries (the six setup statuses + the VCP pattern). Each entry carries the human COPY (meaning + worked example) and **references** to the config keys that define its thresholds — the displayed numbers are NEVER re-typed here, they are resolved live from the canonical config blocks so they always match the engine. Recommended shape (developer finalizes the exact copy; thresholds must reference real keys):
  ```yaml
  methodology:
    intro: "How Trendora classifies every stock. Each name gets exactly one setup status (from its three scores + the market regime) plus any detected price pattern that rides alongside it. Thresholds below are read live from config — they always match the scanner."
    entries:
      - key: Actionable
        kind: setup            # setup | pattern
        name: Actionable
        meaning: "A strong leader at a constructive entry with contained risk — the only status the scanner treats as a fresh buy candidate, and only while the market regime is risk-on."
        thresholds:
          - { label: "Leadership", cmp: ">=", ref: "decision_rules.actionable.leadership" }
          - { label: "Entry Quality", cmp: ">=", ref: "decision_rules.actionable.entry" }
          - { label: "Risk (danger)", cmp: "<=", ref: "decision_rules.actionable.risk" }
          - { label: "Regime", text: "Never produced when the regime is Risk-off (the Risk-off gate forces watchlist-only)." }
        example: "Leadership 92 (A), Entry 74 (C), Risk 48 in a Risk-on regime → Actionable."
      # ... Breakout-watch, Pullback-watch (ref decision_rules.watch.leadership + a text row distinguishing entry >= / < decision_rules.actionable.entry),
      #     Extended (ref decision_rules.extended.leadership + decision_rules.extended.entry),
      #     Avoid (ref decision_rules.avoid_risk + a text row for the too-weak-leadership path),
      #     Risk-off-watchlist (a text row: applies to every name when the regime label is Risk-off),
      - key: vcp
        kind: pattern
        name: "VCP — Volatility Contraction Pattern"
        meaning: "A price+volume base of progressively shallower pullbacks with volume drying up into a pivot near the highs. A detected PATTERN that rides alongside the setup status — it never by itself makes a name Actionable."
        thresholds:
          - { label: "Min contractions", cmp: ">=", ref: "patterns.vcp.min_contractions" }
          - { label: "Max base depth", cmp: "<=", ref: "patterns.vcp.max_base_depth_pct", unit: "%" }
          - { label: "Each contraction vs prior", cmp: "<=", ref: "patterns.vcp.contraction_shrink_ratio" }
          - { label: "Final contraction", cmp: "<=", ref: "patterns.vcp.max_last_contraction_pct", unit: "%" }
          - { label: "Within pivot", cmp: "<=", ref: "patterns.vcp.pivot_proximity_pct", unit: "%" }
          - { label: "Volume dry-up", cmp: "<=", ref: "patterns.vcp.volume_dryup_ratio" }
        example: "3 contractions tightening 18%→9%→5%, volume at 80% of the base, 3% below the pivot → VCP."
  ```
- [ ] **`config.py` — type + validate the new section, and resolve every threshold `ref` at boot.**
  - Add typed models: `MethodologyThreshold` (a row is EITHER `{label, ref, cmp?, unit?}` OR `{label, text}` — exactly one of `ref`/`text` present), `MethodologyEntry` (`key`, `kind: Literal["setup","pattern"]`, `name`, `meaning`, `example`, `thresholds: list[MethodologyThreshold]`), `MethodologyCfg` (`intro?`, `entries: list[MethodologyEntry]` min_length 1). Add `methodology: MethodologyCfg` as a **required** field on `Config` (consistent with `patterns`/`scanner`).
  - Add a small generic resolver `resolve_ref(config, "decision_rules.actionable.leadership") -> value` (dotted-path attribute/key lookup against the loaded `Config`).
  - Add a `Config` `model_validator(mode="after")` that resolves EVERY entry's threshold `ref` against the tree and raises `ValueError` (→ `ConfigError`) on any unresolvable path — an unresolved reference fails the boot loudly (anti-goal: No fabricated data — never a silent/placeholder threshold). Mirror the existing `_invalidation_ma_period_is_an_indicator_period` validator style.
- [ ] **NEW `app/engine/methodology.py` — `build_catalog(config) -> dict`: the single canonical catalog assembler.** Resolves each entry's threshold `ref` to its **live config value** (attaching `cmp`/`unit`), passes `text` rows through verbatim, and emits the served payload (`{intro, entries:[{key, kind, name, meaning, thresholds:[{label, cmp?, value?, unit?, text?}], example}]}`). It also **asserts completeness**: every `app.engine.setups.ALL_STATUSES` status has a `kind:setup` entry and every detected pattern in `config.patterns` (i.e. `vcp`) has a `kind:pattern` entry — raise an explicit error if a canonical status/pattern is undocumented (the glossary can never silently drop one). Computes/stores NO score. Add `methodology.py` to the no-magic-numbers `CALC_FILES` — it must contain **no threshold literal** (every number is resolved from config).
- [ ] **NEW `app/api/methodology.py` — `GET /api/methodology`** returns `build_catalog(get_config())` verbatim (re-formats config only; recomputes nothing). Register the router in `main.py` (`app.include_router(methodology.router, prefix="/api")`). No DB/session needed.

### Frontend (Next.js 15, App Router, TS, Tailwind — hand-rolled shadcn-style UI; NO new dependency)

- [ ] **`lib/api.ts` — add typed `fetchMethodology(signal?)` → `MethodologyCatalog`** (`{ intro?: string; entries: MethodologyEntry[] }`, with `MethodologyEntry = { key; kind: "setup" | "pattern"; name; meaning; thresholds: { label: string; cmp?: string; value?: number; unit?: string; text?: string }[]; example: string }`). Throws on non-200 like the other fetchers (explicit "Backend unavailable" — never fabricated copy).
- [ ] **NEW `app/methodology/page.tsx` — the Methodology / Glossary page.** Fetches `GET /api/methodology` and renders each entry: name + a `kind` chip (Setup / Pattern), the plain-language `meaning`, a compact **thresholds** list (each row: `label cmp value unit`, or the `text` rule verbatim), and the worked `example`. Match the dense dark analytical style (reuse `PageHeading`, `Card`, palette tokens, monospace `num` for the numbers) and the existing loading-skeleton / "Backend unavailable" error / empty-state idioms (mirror `app/stocks/page.tsx`). **No hard-coded per-entry copy or status/pattern list** — every entry comes from the fetched catalog (anti-goal: config-driven UI).
- [ ] **NEW accessible inline tooltip (hand-rolled, no new dep) + wire it to the setup/VCP badges on `/stocks`.** Add a small `components/ui/info-tooltip.tsx` (or similar) — an info affordance whose content is revealed on **hover AND keyboard-focus AND tap/click** (so "hover/tap a badge" works on desktop and touch, and is deterministically assertable by browser-QA), dismissible, styled with palette tokens on a `Card`-like surface. On `/stocks`, the setup badge gains this tooltip showing the **catalog `meaning` for `row.setup.status`** (looked up from the fetched catalog — the SAME definition `/methodology` shows). The VCP badge keeps its existing per-row reason and additionally exposes the catalog VCP `meaning` (so J-16 step 4's definition is reachable inline too). A plain native `title` is an acceptable minimal fallback ONLY for non-essential text, but the setup-badge inline explanation MUST be reachable via click/tap, not title-only.
- [ ] **`app/stocks/page.tsx` — drive the setup-filter vocabulary from the catalog (remove the hard-coded `SETUP_STATUSES` array).** The page already must fetch the catalog for the tooltips; reuse it to populate the Setup filter's options from the catalog's `kind:setup` entries (in catalog order) and to look up each badge's definition. **Graceful degradation (protect J-02):** if the catalog fetch fails, fall back to the setup statuses present in the data so the leaderboard + its existing Sector/Setup/VCP filters still work — a catalog hiccup must NOT break J-02. The status→colour mapping (`setupVariant`) is pure presentation and stays in the frontend (it is not "per-entry copy" — it is a palette-token switch).
- [ ] **`components/sidebar.tsx` — add a new top-level nav item** `{ href: "/methodology", label: "Methodology", icon: BookOpen }` (a lucide book icon), placed **after Watchlist** (matches the goal.md IA ordering). This is the iteration's nav-skeleton change.

### New user-facing capability
A dedicated **Methodology / Glossary** page that explains, from a single config-backed source, what every setup status and the VCP pattern mean, the exact (config-matching) thresholds that define each, and a worked example — plus the same definition inline on every `/stocks` setup/VCP badge.

### New information displayed
The `/methodology` catalog (per entry: meaning + config-matching thresholds + worked example) and the inline badge definition tooltips on `/stocks`.

### New user actions
Navigate to **Methodology** in the sidebar; hover / tap / keyboard-focus a setup or VCP badge on `/stocks` to read its inline definition.

### UI surface changes
NEW page `/methodology`; NEW sidebar entry "Methodology"; NEW inline tooltip on `/stocks` setup + VCP badges; the `/stocks` Setup filter options now come from the catalog (same six statuses, now config-sourced).

### Product surface delta
The product graduates from showing statuses/patterns to **explaining** them from one config-backed catalog — closing the last Must-have. Tuning a threshold in `config.yaml` updates both the glossary and the engine together (single source); adding a catalog entry surfaces it everywhere with no code change.

### Blueprint conformance
NEW top-level **Methodology** section (`/methodology`) added to the Information Architecture as the canonical home for J-12 — this is a **nav-skeleton change**, so `blueprint.reapproval-requested` is written this iteration (and the IA skeleton + feature-home table in `blueprint.md` are updated to add the Methodology row). All other surfaces (the `/stocks` tooltips + filter vocabulary) live under the existing Stocks home.

### Data-contract additions
ONE new value: **Setup & pattern catalog** (per entry: plain-language meaning + the config thresholds that define it + a worked example). Single computing module `app.engine.methodology:build_catalog(config)` (reads the `config.methodology` copy + resolves threshold values live from the canonical config blocks `decision_rules.*` / `patterns.vcp.*` / `buckets.*`); single serving endpoint `GET /api/methodology`. It is the ONE source for BOTH the `/methodology` page AND every inline tooltip AND the `/stocks` setup-filter vocabulary — registered in `blueprint.md` this iteration. It introduces NO second computation of any existing contract value (it reads config, not scores), and the per-row `setup.reason` remains a separate, unchanged value.

## OUT OF SCOPE

- **Refactoring `setups._REASONS` (the per-row reason) into config** — it is a different value (per-stock, component-enriched) and stays exactly as-is. The catalog `meaning` is the generic definition only.
- Any change to `models.py`, the scanner, scoring, setups, patterns, forward-testing, or any existing read endpoint — this iteration adds a read-only catalog surface and changes no canonical computation. (`app/stocks/page.tsx` changes are display-only: tooltip + filter-source, no recompute.)
- A second detected pattern, new setup statuses, or new scoring logic.
- Inline tooltips on pages other than `/stocks` (the Stock Detail badge is a nice-to-have, not required by J-12; keep scope tight). Adding the catalog tooltip to `/stocks/[ticker]` is acceptable if trivial, but not required.
- Charts/visualisation of thresholds; a config-editing UI (nice-to-have #14, deferred).
- Auth, persistence, or any mutation — the methodology endpoint is read-only.

## DEFINITION OF DONE

- [ ] **J-12 passes** via browser evidence: `/methodology` lists all six setup statuses + the VCP pattern, each with a plain-language meaning, config-matching thresholds, and a worked example; on `/stocks`, hovering/tapping a setup badge reveals the same definition inline; the list is generated from the config-backed catalog.
- [ ] **Config-driven proof:** a unit test loads an alternate config with ONE EXTRA catalog entry (referencing existing config keys) and asserts `build_catalog` / `GET /api/methodology` includes it — with NO change to Python/TS code (anti-goal: config-driven UI; "entry added in config renders with no code change").
- [ ] **Matching-config keystone:** a unit test asserts every displayed threshold `value` equals the LIVE config value its `ref` resolves to (no hard-coded copy, no drift) for the real config.
- [ ] **Completeness:** a test asserts the catalog covers every `setups.ALL_STATUSES` status (as `kind:setup`) and every `config.patterns` pattern (`vcp`, as `kind:pattern`), and that `"VCP"` is NOT among the setup entries / `ALL_STATUSES` (anti-goal: VCP is a pattern, not a status).
- [ ] **Honest-failure:** a test asserts a catalog entry with an unresolvable `ref` raises `ConfigError` at load (never a silent default).
- [ ] **No magic numbers:** `methodology.py` is in `CALC_FILES` and `test_engine_calc_code_has_no_magic_numbers` passes (no threshold literal in the assembler).
- [ ] **`test_config.py::MINIMAL_VALID` updated** to include a minimal valid `methodology` section (so the from-scratch config fixture still loads — the established pattern for every newly-required section, iter-2/3/5/6/11).
- [ ] **Full 16-journey regression sweep + full-product coherence:** all fifteen other journeys remain green (re-verified live where feasible; at minimum re-confirmed at source/test level + the deterministic value reproduction). J-02's filters still work; J-16's `/methodology` VCP entry is present.
- [ ] No anti-goal violation introduced; backend `order`/`broker`/secret greps stay empty.
- [ ] Unit tests pass (full backend suite); frontend `npm run build` is clean (typechecks + compiles; the new `/methodology` route appears → 11 → 12 app routes).
- [ ] Dev handoff written at `docs/handoffs/goal-i_can_see_the_wealthy_future-iter-12-dev.md`.

## TESTING REQUIREMENTS

- **Browser (J-12, + regression):**
  - `/methodology` renders all six setup statuses + the VCP pattern; spot-check one setup (e.g. Actionable shows Leadership ≥ `decision_rules.actionable.leadership`, Entry ≥ …, Risk ≤ …) and the VCP entry (its config thresholds + meaning + example).
  - On `/stocks`, hover/tap/focus a setup badge → its inline definition appears and matches the `/methodology` meaning for that status; the Setup filter still narrows rows (J-02), and the VCP filter still narrows to flagged names (J-16).
  - Regression: `/`, `/stocks`, `/themes`, `/sectors`, `/scanner-runs` (+ a Risk-off run → 0 Actionable, J-07), `/system-health` (by-bucket/setup/regime/excess/control-group + by_vcp), `/backtest`, `/watchlist`, the global as-of switcher (J-13) — all still render their canonical values. Capture **distinct** PNGs per surface and `md5sum` them.
- **Unit/integration (fast — the methodology endpoint needs no seeded DB):**
  - `test_methodology.py` (new): `build_catalog` shape + completeness (all `ALL_STATUSES` + `vcp`); matching-config keystone (displayed value == resolved live config value); config-only-extra-entry renders (no code change); `"VCP"` not a setup status.
  - `test_config*.py`: the new typed models validate; an unresolvable `ref` raises `ConfigError`; `MINIMAL_VALID` (+ minimal `methodology`) still loads.
  - `test_api_*.py`: `GET /api/methodology` returns 200 with the catalog (TestClient — no walk-forward boot needed); shape matches `build_catalog`.
  - `test_no_magic_numbers.py`: `methodology.py` added to `CALC_FILES` and passes.
  - **Regression:** run the targeted backend suites and confirm the pre-existing files (`models.py`, `scanner.py`, `scoring.py`, `setups.py`, `patterns.py`, `forward_testing.py`, the existing routers) have an **empty diff**, so J-01–J-11/J-13–J-16 cannot structurally regress; the full suite passes.
- **Error cases:** unresolvable threshold `ref` → `ConfigError` at boot; `/api/methodology` while the backend is down → the page renders an explicit "Backend unavailable" (never fabricated copy); an undocumented setup status/pattern → `build_catalog` raises (completeness).

## NOTES

- **This is the goal-completing iteration.** After a clean J-12, 16/16 Must-haves pass and the next evaluation can legitimately reach GOAL_ACHIEVED — hence the paired full 16-journey regression sweep + full-product coherence in this spec, not just the single target.
- **The central anti-goal is "Setup & pattern vocabulary is config-driven in the UI too."** The frontend must hold NO hard-coded per-entry copy or status/pattern list — the `/methodology` page, the badge tooltips, AND the `/stocks` setup-filter options all read the one catalog endpoint. The matching-config keystone + the config-only-entry test are the proofs.
- **Coherence note for the auditor:** the catalog `meaning` (generic status/pattern definition, config-backed, served by `/api/methodology`) and the per-row `setup.reason` (per-stock, component-enriched, from `setups._REASONS`, served on the stock row) are **distinct displayed values**, not two sources of one value — the tooltip shows the catalog `meaning`. The catalog reads config; it recomputes no score/return/bucket. The only new nav home is `/methodology` (J-12) with `blueprint.reapproval-requested` written.
- **Runner-owner debt (NON-gating, chronic — runner-script scope, NOT product; spec text has proven ineffective across iters 3–11, so this is informational for the evaluator, not a fix request in the spec):** (1) the dedicated browser-qa has SKIPped 10 consecutive iters (probes `GET /health` instead of `/api/health`, and tears services down before browser-qa runs); (2) the audit handoff (`reports/audits/`) has been missing 10 full-depth iters. Durable fixes belong in `scripts/automation/*.sh`. The evaluator should be ready to reconcile from on-disk evidence + unit/API proofs + source reads, and to self-produce live evidence if needed (iter-7/iter-10 precedent).
- **Evaluator: confirm code presence first** (iter-9 lesson): `git status` (new `app/engine/methodology.py`, `app/api/methodology.py`, `app/methodology/page.tsx`, `components/ui/info-tooltip.tsx`), `grep -rln "methodology" apps/`, and the new tests — before scoring J-12. Distinguish "not built" from "built but un-verified".
