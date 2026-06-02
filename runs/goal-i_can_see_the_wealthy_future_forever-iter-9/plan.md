# goal-i_can_see_the_wealthy_future_forever-iter-9 Execution Plan

**Target journey:** J-28 — ≥2 new config-driven detected patterns beyond VCP (`pullback_to_rising_dma`, `flat_base_breakout`), forward-tested.
**Depth:** full (backend engine + config + data model + forward-test + API + frontend + full test suite).
**Alignment:** Directly advances goal capability #28 / journey J-28. No drift — the spec scopes OUT the data-walled wave (J-22/23/24) and the `/research` labs, matching the goal's anti-goals. This is an **additive extension of the existing VCP seams**, not new architecture: every seam the spec names was verified present and correctly located (see Files).

## What to Build

Three detected patterns instead of one (VCP + 2 new), each held to the identical VCP "pattern-not-status" contract — config-driven thresholds, computed once with date ≤ D, price+volume only, riding alongside the setup status, never entering the setup-status enum, never alone making a name Actionable, stored on the immutable snapshot, read verbatim everywhere.

- **Config:** two new keys under `patterns:` (`pullback_to_rising_dma`, `flat_base_breakout`) holding ALL detection thresholds; one `kind: pattern` catalog entry per pattern under `methodology.entries` whose numeric rows are `ref:` paths into the new `patterns.<name>.*` keys (never re-typed numbers).
- **Config model:** a typed Pydantic sub-model per pattern (mirroring `VcpCfg`) added as fields on `PatternsCfg`, with `@model_validator` range checks; cross-field check `pullback_to_rising_dma.ma_period ∈ indicators.ma_periods` at the **top-level `Config` validator** (sub-models can't see `indicators` — same place VCP's invalidation `ma_period` is cross-checked).
- **Detectors:** `detect_pullback_to_rising_dma(...)` + `detect_flat_base_breakout(...)` — pure, deterministic, price+volume only, NA-graceful, returning the SAME contract dict shape as `detect_vcp` (`{flagged, reason, pivot, invalidation:{level,note}, …detail}`). Insufficient history / no pattern → `flagged=False` + honest reason, NO fabricated pivot/level.
- **Composition:** at the existing VCP call site in `scoring.py:335` also call each new detector on the same ≤ D bars and attach under its config key (`row["pullback_to_rising_dma"]`, `row["flat_base_breakout"]`). Leave `row["vcp"]` byte-identical. A small config-keyed dispatch driven by the active `config.patterns` names is welcome (optional).
- **Persistence:** add indexed boolean mirror columns `is_pullback_to_rising_dma`, `is_flat_base_breakout` to `ScannerResult` (mirroring `is_vcp`), written once in the single `ScannerResult(...)` construction in `scanner.py` from `row["<name>"]["flagged"]`. `record_json` already carries the full blocks losslessly.
- **Forward-test:** in `compute_forward_aggregates`, read the new mirrors onto each observation and add `by_pullback_to_rising_dma` + `by_flat_base_breakout` via the existing generic `_group_means(stock_obs, "is_<name>", "<name>", [True, False], pad=True)` — exactly like `by_vcp`. Read the stored mirror verbatim, never re-detect; both True/False cohorts always emitted; cohort < `walk_forward.min_sample` (30) shows `n`+NA.
- **DB regeneration (offline/deterministic — NO fetch):** delete `apps/backend/data/trendora.db` and reboot so `bootstrap_runs` recomputes every immutable snapshot WITH the new flags and re-derives forward returns over the **committed seed**. Confirm Risk-Off bootstrap dates still label Risk-Off and J-07/J-08 hold.
- **Frontend:** typed interface per pattern + `StockRow` fields in `api.ts`; each new pattern independently filterable on `/stocks` (generalize the existing VCP `<Select>` into per-pattern filters/selector) with badge + server `reason` + concrete `invalidation` rendered verbatim; confirm `/methodology` auto-renders the new cards from the catalog (no per-pattern code — it already maps `entries` generically); two new `by_<name>` breakdown panels on `/system-health` reusing the existing `BreakdownPanel`.

## Agents Required

- developer: **yes** — full-stack: backend (config + model + detectors + composition + persistence + forward-test + DB regen + tests) and frontend (types + leaderboard filters/badges + System Health panels).
  - backend-data: **yes** — patterns engine, config + config model, scoring composition, mirror columns, forward-test breakdown, DB regen, full backend test suite mirroring the VCP seams.
  - frontend-ux: **yes** — `api.ts` types; `/stocks` pattern filters + badges/tooltips; `/system-health` two new breakdown panels; confirm `/methodology` auto-renders (generalize only if any pattern list/copy is hard-coded).

Frontend Present: yes

## Files to Create/Modify

**Backend**
- `config.yaml` — add `patterns.pullback_to_rising_dma` + `patterns.flat_base_breakout` (all thresholds) and two `kind: pattern` entries under `methodology.entries` (numeric rows = `ref:` paths only). Tune values against the committed seed so the latest snapshot flags a non-trivial set (some/not all/not none); never loosen to fabricate flags or forward-test sample.
- `apps/backend/app/config.py` — `PullbackToRisingDmaCfg` + `FlatBaseBreakoutCfg` sub-models (mirror `VcpCfg`); add fields to `PatternsCfg`; cross-field `ma_period ∈ indicators.ma_periods` check on the top-level `Config` validator.
- `apps/backend/app/engine/patterns.py` — `detect_pullback_to_rising_dma`, `detect_flat_base_breakout` (same contract as `detect_vcp`; only structural numeric literals allowed).
- `apps/backend/app/engine/scoring.py` (~line 335) — call each new detector on the ≤ D bars; attach `row["<name>"]`; do NOT touch `setup` or `row["vcp"]`.
- `apps/backend/app/models.py` — `is_pullback_to_rising_dma`, `is_flat_base_breakout` indexed bool columns on `ScannerResult`.
- `apps/backend/app/engine/scanner.py` (~line 92-108) — write each new mirror from `row["<name>"]["flagged"]` in the single `ScannerResult(...)`.
- `apps/backend/app/engine/forward_testing.py` — read new mirrors onto observations (~line 552); add `by_pullback_to_rising_dma` + `by_flat_base_breakout` (~line 583-589 pattern).
- **Tests (extend existing files, do NOT create parallel suites):** `tests/test_patterns.py`, `tests/test_scoring.py`, `tests/test_scanner.py`, `tests/test_forward_testing.py`, `tests/test_api_system_health.py`, `tests/test_api_engine.py`, `tests/test_no_magic_numbers.py` (add distinctive threshold sentinels for the new patterns — the guard tokenizes `patterns.py` and asserts no detector literal exists outside config).

**Frontend**
- `apps/frontend/lib/api.ts` — `PullbackToRisingDma` + `FlatBaseBreakout` interfaces (mirror `Vcp`); extend `StockRow`; extend the System Health aggregates type with `by_pullback_to_rising_dma` / `by_flat_base_breakout` (`ForwardGroupRow`-shaped).
- `apps/frontend/app/stocks/page.tsx` — generalize the VCP filter into per-pattern filters/selector; render each flagged pattern's badge + server `reason`/`invalidation` verbatim (reuse the `vcpTitle` tooltip approach); empty-state copy stays honest.
- `apps/frontend/app/system-health/page.tsx` — two new `BreakdownPanel`s for `by_<name>` (mirror the `by_vcp` panel at ~line 199-203), each with `n` + honest NA below `min`.
- `apps/frontend/app/methodology/page.tsx` — **confirm** auto-render of the new cards (it maps `entries` generically); change ONLY if a pattern list/copy is found hard-coded.

**Do NOT touch (process artifacts already written by the decomposer / out of scope):**
- `runs/goal-session-…/state/blueprint.md` (already updated: both new pattern data-contract rows L140-141, `/research` PLANNED nav entry L67, coherence invariant #6 names both patterns) and `…/state/blueprint.reapproval-requested` (already written). These are NOT developer edits.
- **No `/research` route, page, endpoint, or lab code** anywhere in this diff — the `/research` nav entry is PLANNED/front-loaded only; iter-9 builds zero `/research` code. Any `/research` code is out of scope.
- No change to the six canonical scores, A–E buckets, setup-status enum, regime engine, as-of control, or watchlist. No third pattern beyond the two targeted.

## UI Evolution (Frontend Present: yes)

- **New user-facing capability:** filter the leaderboard by, read inline explanations of, and see forward-tested evidence for **3 detected patterns (VCP + 2 new)** instead of just VCP — judging each pattern's value with honest sample size / NA.
- **New information displayed:** two new pattern **badges** (reason + invalidation) on `/stocks` rows and `/stocks/[ticker]`; two new **glossary cards** (meaning + config thresholds + worked example) on `/methodology`; two new **pattern-vs-non-pattern forward-return breakdowns** (with `n`) on `/system-health`.
- **New user actions:** filter `/stocks` to each new pattern (and back to "all"); hover/tap a new badge for its inline explanation.
- **UI surface changes:** `/stocks` filter area gains the new pattern filter(s) + badges; `/methodology` gains two auto-rendered cards; `/system-health` gains two breakdown panels.
- **Navigation changes:** none. No new pages/routes. (`/research` is PLANNED in the skeleton but NOT built this iteration.)

## Visual Requirements (Frontend Present: yes)

- **Component patterns:** reuse existing — `Badge` for pattern flags, `Select` for the leaderboard pattern filter, `EntryCard` (auto) for glossary cards, `BreakdownPanel` for the System Health `by_<name>` panels. No new component families.
- **Layout:** unchanged — dense dark analytical workstation; sidebar + main content; leaderboard filter row stays compact; System Health panels sit alongside the existing `by_vcp` panel.
- **Key visual effects:** monospace/tabular-nums for all numbers; A–E / palette colour tokens only (`--accent` teal for patterns, `--pos`/`--neg` for returns, `--warn` for low-sample/NA). Pattern badges styled like the VCP badge (accent variant).
- **States to handle:** flagged vs not (badge shown only when `flagged`); empty filter result → honest empty-state (no fabricated rows); System Health cohort `n < min_sample` → NA with `n` shown (never a fabricated number); backend-unavailable → existing error card.

## Key Test Scenarios (must pass for the phase to be complete)

**Browser (browser-qa-agent), J-28 end-to-end:**
1. `/stocks` filter by `pullback_to_rising_dma` → only flagged rows, each with badge + reason + concrete invalidation (or honest empty-state).
2. `/stocks` filter by `flat_base_breakout` → same.
3. Open one flagged stock → `/stocks/[ticker]` shows the same pattern badge/invalidation.
4. `/methodology` → both new pattern cards render (meaning + config thresholds + example), auto-rendered from the catalog.
5. `/system-health` → both `by_<name>` breakdowns render numbers + `n` (NA where cohort < min-sample).
- Regression spot-checks: **J-16** (VCP filter/badge/glossary/`by_vcp` intact), **J-12** (6 setups + 3 patterns in glossary), **J-02** (sector + Actionable filter still work), **J-07** (Risk-off run → Actionable = 0).

**Unit/integration (mirror the VCP seams for EACH new pattern):**
- `test_patterns.py`: constructed positive series flags (correct pivot + invalidation); wrong-shape does not flag; short history → `flagged=False`+NA (no fabricated level); a threshold change flips the flag (config-driven); deterministic.
- `test_scoring.py`: force-flagging a new pattern alters NO setup status (pattern-not-status).
- `test_scanner.py`: `is_<name>` == `json.loads(record_json)["<name>"]["flagged"]` for every stored result (immutable mirror).
- `test_forward_testing.py`: `by_<name>` groups exactly by the stored mirror; empty cohort NA-padded (both rows, n=0/mean=None).
- `test_api_system_health.py`: each `by_<name>` present in the aggregates payload.
- `test_api_engine.py` (keystone): patch each new detector to raise → `/api/stocks` (list+detail) and `/api/system-health` `by_<name>` still serve (read path serves stored values, never re-detects).
- `test_no_magic_numbers.py`: no new-pattern detection literal outside config; every threshold resolves from `cfg.patterns.<name>.*`.
- Catalog completeness: `build_catalog` still passes (every `config.patterns` key has a `kind:"pattern"` entry); removing a catalog entry must fail boot (guard exists — confirm it fires).
- Config validation: invalid value (e.g. `ma_period` not in `indicators.ma_periods`, ratio/percent out of range) → `ConfigError`/validation failure at boot, not a silent default.

## Process Guardrails (apply iter-2/3/6/7/8 lessons — for dev/reviewer/QA/evaluator)

- **Run the full pytest suite ONCE after DB regen** (~14 min, heavy walk-forward boot — project memory); never launch two pytest invocations concurrently.
- **Verify anti-goal seams directly in source** (do not block on or trust a `status.json` or `auditor` handoff — prior full-depth iters finished without them): pattern-not-status in `scoring.py`; each detector referenced only on the ≤ D path; thresholds read from `config.patterns.<name>`; mirror written once in `scanner.py`; `by_<name>` reads the stored mirror (no re-detect).
- **Evidence integrity:** de-dup QA screenshots by sha256 (≥2 prior iters shipped byte-identical before/after shots); ground every before/after pattern-filter claim on **distinct** shots + a DOM assertion (filtered row count / badge presence), not one screenshot pair.
- **Browser concurrency:** if both `qa` and `browser-qa-agent` use Chrome-MCP, serialize access (one vacates before the other captures) and assert live DOM/URL immediately before each capture — the shared single-tab Chrome corrupts concurrent captures silently.
- **Confirm DB regen is offline/deterministic** — reads only the committed seed; no Yahoo/live fetch (J-28 is NOT subject to the J-22/23/24 429 data wall). All J-01…J-21 values unchanged (patterns ride alongside; they do not alter scores/setups/regime).

## Assumptions

- New-detector signatures follow `detect_vcp`'s style (`(closes, highs, lows, volumes, cfg.patterns.<name>)`), reading only the passed ≤ D series + their own config block; the developer finalizes the exact argument list against `scoring.py:335`.
- Threshold values in `config.yaml` are illustrative in the spec; the developer finalizes them against the committed seed so the latest snapshot flags a sensible non-trivial set — without loosening to fabricate flags or forward-test sample (honest `n`/NA below min-sample is correct, not a failure).
- The blueprint + re-approval marker are decomposer artifacts already on disk; the developer neither edits them nor builds `/research` code.

## Dev Handoff
Write to `docs/handoffs/goal-i_can_see_the_wealthy_future_forever-iter-9-dev.md` when complete.
