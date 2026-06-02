# Goal Iteration 9 — More detected patterns beyond VCP (J-28), forward-tested

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** i_can_see_the_wealthy_future_forever
- **Iteration:** 9
- **Mode:** next
- **Depth:** full
- **Frontend Present:** yes
- **Target journeys:** J-28
- **Required-still-passing journeys:** J-02, J-05, J-06, J-07, J-08, J-09, J-12, J-15, J-16
- **Anti-goal reminders (verbatim from `docs/goal.md`):**
  - **New patterns are patterns, not statuses.** Every new detected pattern MUST follow the VCP contract: config-driven thresholds, computed once with date ≤ D, price+volume only, riding alongside the setup status, never entering the setup-status enum, and never alone promoting a name to "Actionable". *(reaffirms VCP is a pattern, not a status)*
  - **VCP is a pattern, not a status.** VCP MUST NOT enter the mutually-exclusive setup-status enum and MUST NOT by itself promote a name to "Actionable"; it rides as a separate flag computed once per run, price+volume only, with date ≤ D (no-lookahead), and is part of the immutable snapshot. Its detection thresholds MUST come from config (no magic numbers). *(critical — protects Single source of truth + Risk-Off gating)*
  - **No lookahead.** Scoring for a snapshot dated D MUST use only price bars with date ≤ D; forward returns MUST use only bars with date > D. The walk-forward MUST be unit-tested to prove no future bar influences an as-of score. *(critical)*
  - **No magic numbers.** Every scoring weight, threshold, decision-rule cutoff, bucket edge, universe entry, and theme definition MUST come from the config file — no such literal in calculation code.
  - **Setup & pattern vocabulary is config-driven in the UI too.** The glossary and tooltips MUST be generated from the single config-backed catalog — no hard-coded per-entry copy or status/pattern list in the frontend — so a new status or pattern is explained automatically. *(extends No magic numbers)*
  - **Honest forward-test for partial windows.** The per-date forward-test scorecard and the VCP-vs-non-VCP breakdown MUST show NA/partial for horizons or cohorts lacking enough samples and MUST show sample size — never fabricate or extrapolate a return to fill a gap. *(extends No fabricated data)*
  - **No fabricated data.** On a data-provider failure the system MUST surface an explicit stale/unavailable state and MUST NOT synthesize prices or scores to force a green journey.
  - **Single source of truth.** Each of the six canonical scores (and the A–E bucket and setup status) MUST be computed exactly once by the scoring/regime engine and read identically by every page; the API and frontend MUST NOT recompute them.
  - **No recompute in the read path.** Read endpoints MUST serve canonical values from the persisted immutable snapshot for the resolved as-of date; they MUST NOT recompute scores/returns/buckets per request. *(extends Single source of truth)*
  - **Snapshots are immutable.** A persisted `scanner_run` and its result rows MUST never be updated or overwritten after creation; forward returns live in a separate append-only table keyed to the snapshot. *(critical)*
  - **Risk-Off must gate Actionable.** When the regime is Risk-Off, the scanner MUST mark zero stocks "Actionable" (watchlist-only). *(critical)*

## GOAL

Add **≥2 new config-driven detected price patterns beyond VCP** (target: `pullback_to_rising_dma` and `flat_base_breakout`) that ride alongside the setup status exactly like VCP — filterable on the Stock Leaderboard, documented on the Methodology/Glossary page from the config-backed catalog, and surfaced as a pattern-vs-non-pattern forward-return breakdown (with sample size / honest NA) on System Health.

## BACKGROUND

J-28 is the last fully-autonomous journey in the new wave. It is **compute-only over the already-stored seed** (no external fetch → it is NOT subject to the Yahoo-429 data wall that blocks J-22/J-23/J-24), and the goal's J-28 acceptance explicitly allows the pattern breakdown on "the Setup & Pattern Lab **(or System Health)**" — so it rides the **existing** `/stocks`, `/stocks/[ticker]`, `/methodology`, and `/system-health` homes and needs **no `/research` nav home and no blueprint re-approval** (iter-8 evaluator analysis; journey-history J-28 note). The pattern infrastructure is already built generically for this: `config.patterns` is a typed container (`PatternsCfg`, `extra="allow"`), `methodology.build_catalog` already asserts every `config.patterns` key has a `kind:"pattern"` catalog entry, the forward-test `_group_means` is grouping-key generic, and `/methodology` + the glossary frontend iterate the catalog. So a second/third pattern is an additive extension of the same seams VCP uses — not new architecture.

The iter-8 evaluator dispatched this at **full** depth: it crosses backend engine + config + data model (new mirror columns → DB regeneration) + forward-testing + API + frontend (filters + System Health panels) and requires a full new test suite mirroring the VCP contract tests.

This iteration ALSO front-loads the `/research` blueprint nav re-approval (see NOTES) so the compute-only labs (J-25–J-31) unblock cleanly in subsequent iterations — but that is a planning/approval action only; **iter-9 builds no `/research` code.**

## IN SCOPE

### Backend

- [ ] **Config (`config.yaml`):** add two new keys under the existing `patterns:` map — `pullback_to_rising_dma:` and `flat_base_breakout:` — each holding ALL of its detection thresholds (no magic numbers). Tune the threshold values against the **committed seed** so each pattern flags a *sensible, non-trivial set on the latest snapshot* (some, not all, not none) — never loosen a threshold to fabricate flags. Suggested (illustrative — developer finalizes against the seed, every value lives here):
  - `pullback_to_rising_dma`: `ma_period` (MUST be one of `indicators.ma_periods`, e.g. 50), `min_history_bars`, `trend_lookback_bars` + `min_dma_slope_pct` (the DMA must be *rising* over the lookback), `max_dist_above_dma_pct` (latest close within this % ABOVE the DMA — pulled back *to* it), `max_undercut_pct` (how far below the DMA still tolerated, may be 0), `max_pullback_depth_pct` (pullback from the recent high is a pullback, not a crash), optional `volume_window`.
  - `flat_base_breakout`: `lookback_bars`, `min_history_bars`, `base_window` (bars forming the base), `max_base_depth_pct` (base range is FLAT/shallow), `pivot_proximity_pct` (latest close within this % at/below the base high — breakout-ready), optional `volume_window` + `min_breakout_volume_ratio`.
- [ ] **Config catalog (`config.yaml` → `methodology.entries`):** add one `kind: pattern` entry for EACH new pattern, with a plain-language `meaning`, a worked `example`, and a `thresholds` list whose numeric rows are `ref:` paths into the new `patterns.<name>.*` keys (NEVER re-typed numbers — same `ref` mechanism as the VCP entry at `config.yaml:638-649`). `build_catalog` already fails the boot loudly if a `config.patterns` key has no matching catalog entry — so the catalog entry is mandatory, not optional.
- [ ] **Config model (`apps/backend/app/config.py`):** add a typed Pydantic sub-model for each new pattern (mirroring `VcpCfg`) and a field on `PatternsCfg` (`pullback_to_rising_dma: ...`, `flat_base_breakout: ...`), with `@model_validator` range checks (e.g. `ma_period ∈ indicators.ma_periods`, all windows/counts positive, ratios/percents in range). Boot fails loudly on an invalid value.
- [ ] **Detectors (`apps/backend/app/engine/patterns.py`):** add `detect_pullback_to_rising_dma(...)` and `detect_flat_base_breakout(...)` — pure, deterministic, **price+volume only**, NA-graceful, config-driven, reading ONLY the passed as-of series (date ≤ D) and ONLY `config.patterns.<name>` thresholds. Return the SAME contract dict shape as `detect_vcp` (`{flagged, reason, pivot, invalidation:{level,note}, ...detail}`) so every caller reads one contract. On insufficient history or no qualifying pattern → `flagged=False` with an honest reason and NO fabricated pivot/invalidation level. The only numeric literals allowed are structural (indexing/rounding/percent-unit).
- [ ] **Composition (`apps/backend/app/engine/scoring.py`):** at the existing VCP call site (~`scoring.py:335`, where bars are already read ≤ D for the VCP + invalidation MA), also call each new detector and attach its result to the row under its config key (`row["pullback_to_rising_dma"]`, `row["flat_base_breakout"]`). **Keep `row["vcp"]` exactly as-is** (J-16/J-06 read it). Recommended (not mandatory): drive the calls from a small registry keyed by the active `config.patterns` names so adding a future pattern stays config-driven. A detected pattern MUST NOT touch the `setup` field (pattern-not-status).
- [ ] **Persistence (`apps/backend/app/models.py` + `apps/backend/app/engine/scanner.py`):** add an indexed boolean mirror column to `ScannerResult` for each new pattern (`is_pullback_to_rising_dma`, `is_flat_base_breakout`) — exactly mirroring the existing `is_vcp` design — and write each in the single `ScannerResult(...)` construction in `scanner.py` from `row["<name>"]["flagged"]`. `record_json` already stores the full row losslessly (the new pattern blocks ride in it automatically); the mirror is only the denormalized flag for fast forward-test grouping. Snapshots stay append-only/immutable.
- [ ] **Forward-test breakdown (`apps/backend/app/engine/forward_testing.py`):** in `compute_forward_aggregates`, read the new stored mirrors onto each observation and add a `by_<name>` breakdown by calling the existing generic `_group_means(stock_obs, "is_<name>", "<name>", [True, False], pad=True)` for each new pattern — exactly like `by_vcp`. **Read the stored mirror verbatim — never re-detect.** Cohorts below `walk_forward.min_sample` show `n` + NA honestly; empty cohorts are NA-padded (both True/False rows always emitted).
- [ ] **DB regeneration (no fetch — offline/deterministic):** because new columns are added to `ScannerResult`, delete `apps/backend/data/trendora.db` and reboot so `bootstrap_runs` re-runs `scanner.run_scan` for every bootstrap date + latest, recomputing each immutable snapshot WITH the new pattern flags (and `backfill_run_forward_returns` re-derives the forward returns). This reads ONLY the committed seed — there is **no live fetch and no Yahoo dependency**. Risk-Off bootstrap dates and all J-01…J-21 values are unchanged by this (patterns ride alongside; they do not alter scores/setups/regime).

### Frontend

- [ ] **API types (`apps/frontend/lib/api.ts`):** add a typed interface per new pattern (mirroring `Vcp`) and extend `StockRow` with the new pattern fields (`pullback_to_rising_dma`, `flat_base_breakout`). Frontend re-displays server values only — never recomputes `flagged`.
- [ ] **Leaderboard filter (`apps/frontend/app/stocks/page.tsx`):** make each new pattern **independently filterable** (extend the existing VCP filter into a pattern selector that lists every detected pattern, or add one filter control per pattern). Flagged rows render the pattern's badge with its server-built `reason` + concrete `invalidation` level (verbatim, like the VCP badge/tooltip). The filter is pure client-side re-display of `row.<name>.flagged` — no recompute.
- [ ] **Glossary (`apps/frontend/app/methodology/page.tsx`):** confirm it renders the new pattern cards automatically from the config-backed catalog (`kind:"pattern"`) — it iterates `entries` generically today, so **no per-pattern frontend code should be needed**; if any pattern list/copy is hard-coded, generalize it (anti-goal: config-driven UI vocabulary).
- [ ] **System Health (`apps/frontend/app/system-health/page.tsx`):** render the new `by_<name>` pattern-vs-non-pattern breakdown panels alongside the existing `by_vcp` panel — pattern cohort vs non-pattern cohort mean forward return, each with `n` and honest NA below min-sample.

### New user-facing capability

The user can see, **filter by**, understand (glossary + inline tooltip), and read forward-tested evidence for **≥3 detected patterns (VCP + 2 new)** instead of just VCP — so they can judge whether each pattern adds value, with sample size and honest NA.

### New information displayed

- Two new pattern **badges** (with reason + invalidation level) on `/stocks` rows and `/stocks/[ticker]`.
- Two new **glossary entries** (meaning + config thresholds + worked example) on `/methodology`, plus matching inline tooltips on the leaderboard badges.
- Two new **pattern-vs-non-pattern forward-return breakdowns** (`by_pullback_to_rising_dma`, `by_flat_base_breakout`) with sample size `n` on `/system-health`.

### New user actions

- Filter the Stock Leaderboard to each new pattern (and back to "all").
- Hover/tap a new pattern badge to read its inline explanation.

### UI surface changes

`/stocks` leaderboard filter area gains the new pattern filter(s) + badges; `/methodology` gains two auto-rendered pattern cards; `/system-health` gains two new breakdown panels. **No new pages or routes.**

### Product surface delta

The product's pattern vocabulary grows from one detected pattern (VCP) to three, each held to the same honest, forward-tested, config-driven, pattern-not-status contract — strengthening the "prove its own usefulness" evidence layer.

### Blueprint conformance

**No new surfaces.** J-28 rides the existing homes already in `blueprint.md`: `/stocks` + `/stocks/[ticker]` (leaderboard filter + badges), `/methodology` (config-backed glossary), `/system-health` (pattern-vs-non-pattern breakdown). The `/research` entry added to the nav skeleton in `blueprint.md` this iteration is a **PLANNED** home for the future compute-only labs (J-25–J-31) with its approval **front-loaded** via `blueprint.reapproval-requested` — it is **NOT built this iteration** (see NOTES).

### Data-contract additions

Two new **Detected pattern** rows (each mirroring the existing VCP row), registered in `blueprint.md` this iteration:
- `pullback_to_rising_dma` flag (+ pivot/invalidation/reason): computed once by `app.engine.patterns:detect_pullback_to_rising_dma`, composed onto the row by `scoring:score_stocks` (price+volume, ≤ D), mirror col `scanner_results.is_pullback_to_rising_dma`; served on `GET /api/stocks` + `GET /api/stocks/{ticker}`; `by_pullback_to_rising_dma` breakdown on `GET /api/system-health`; catalog entry via `methodology:build_catalog`.
- `flat_base_breakout` flag (+ pivot/invalidation/reason): same path with `detect_flat_base_breakout` / `is_flat_base_breakout` / `by_flat_base_breakout`.

Both are NEW descriptive values (additive — they do NOT duplicate or recompute any existing score/return/bucket). Read-only in the API/UI: computed once per run, stored on the immutable snapshot, read verbatim everywhere (single source of truth; no recompute in the read path). The forward-return breakdowns read the stored mirror, never re-detect.

## OUT OF SCOPE

- **J-22 universe expansion / J-23 / J-24** — externally data-walled (Yahoo 429). Do NOT autonomously re-dispatch the J-22 fetch; it auto-heals via its committed finish runbook only on operator confirmation of a reachable no-key feed.
- **`/research` labs (J-25, J-26, J-27, J-29, J-30, J-31)** — not built this iteration. Only their nav home's approval is front-loaded (planning action). No `/research` route, page, endpoint, or lab code in this iteration's diff.
- A pattern **registry refactor** beyond what cleanly supports the two new patterns — keep the change additive; a full plugin registry is not required (a small config-keyed dispatch is welcome but optional).
- Any change to the six canonical scores, the A–E bucket logic, the setup-status enum, the regime engine, the as-of date control, or the watchlist.
- A third+ pattern beyond the two targeted (≥2 is the acceptance bar; more is scope creep this iteration).

## DEFINITION OF DONE

- [ ] Target journey **J-28** passes via browser-qa-agent: on `/stocks`, filtering by each new pattern shows only flagged rows (or an honest empty-state) with a badge + reason + concrete invalidation; each new pattern is documented on `/methodology` (meaning + config thresholds + example, auto-rendered from the catalog); System Health shows each new pattern's pattern-vs-non-pattern forward-return breakdown with `n` (NA below the min-sample threshold).
- [ ] ≥2 new patterns detected by config-driven rules — every detection threshold lives in `config.yaml` under `patterns.<name>` (no detector literal in code).
- [ ] **Pattern-not-status proven:** forcing a new pattern's flag changes NO setup status; no new pattern ever promotes a name to "Actionable"; Risk-Off still gates Actionable to zero (J-07 regression guard).
- [ ] **No-lookahead proven:** the new detectors are referenced only on the ≤ D snapshot path; a snapshot dated D uses only bars ≤ D for its pattern flags (source-seam + unit assertion, mirroring the VCP no-lookahead tests).
- [ ] Required-still-passing journeys remain green: **J-02, J-05, J-06, J-07, J-08, J-09, J-12, J-15, J-16** (VCP unchanged; glossary still renders all entries; leaderboard filters + score consistency intact; immutable runs + snapshot-served reads intact).
- [ ] No anti-goal violation introduced (verify the verbatim list above — especially pattern-not-status, no-lookahead, no-magic-numbers, config-driven UI vocabulary, honest NA/n, immutable snapshots).
- [ ] Backend unit tests pass (full suite once — see runtime caveat in NOTES); frontend builds (`npm run build` typechecks).
- [ ] Dev handoff written at `docs/handoffs/goal-i_can_see_the_wealthy_future_forever-iter-9-dev.md`.

## TESTING REQUIREMENTS

- **Browser (browser-qa-agent):** J-28 end-to-end — (1) `/stocks` filter by `pullback_to_rising_dma` → flagged rows show badge + reason + invalidation; (2) `/stocks` filter by `flat_base_breakout` → same; (3) open one flagged stock → detail shows the same pattern badge/invalidation; (4) `/methodology` → both new pattern entries render with thresholds + example; (5) `/system-health` → both new `by_<name>` breakdowns render numbers + `n` (NA where cohort < min-sample). Regression spot-checks: J-16 (VCP filter/badge/glossary/by_vcp still intact), J-12 (all 6 setups + 3 patterns in glossary), J-02 (sector + Actionable filter still work), J-07 (dashboard/Risk-off run Actionable = 0).
- **Unit/integration (mirror the VCP test seams for EACH new pattern):**
  - `tests/test_patterns.py`: a constructed positive series flags (correct pivot + invalidation), a wrong-shape series does not flag, short history → `flagged=False` + NA (no fabricated level), threshold change flips the flag (config-driven, not hard-coded), detector is deterministic.
  - `tests/test_scoring.py`: the new pattern flag never alters the setup status (force-flagged → no setup changes).
  - `tests/test_scanner.py`: `is_<name>` equals `json.loads(record_json)["<name>"]["flagged"]` for every stored result (immutable mirror).
  - `tests/test_forward_testing.py`: `by_<name>` groups observations exactly by the stored mirror; an empty cohort is NA-padded (both True/False rows present, n=0/mean=None).
  - `tests/test_api_system_health.py`: each `by_<name>` breakdown is present in the aggregates payload.
  - `tests/test_api_engine.py` (keystone): patch each new detector to raise — `/api/stocks` (list + detail) and `/api/system-health` `by_<name>` still work (read path serves stored values, never re-detects).
  - `tests/test_no_magic_numbers.py`: no new-pattern detection literal exists outside config; every threshold resolves from `cfg.patterns.<name>.*`.
  - catalog completeness: `build_catalog` still passes (every `config.patterns` key has a `kind:"pattern"` entry) — adding the pattern key without its catalog entry must fail the boot (guard already exists; confirm it fires).
- **Error cases:** insufficient history → `flagged=False`, no fabricated pivot/level (honest NA). Invalid config (e.g. `ma_period` not in `indicators.ma_periods`, a ratio/percent out of range) → `ConfigError`/validation failure at boot, not a silent default.

## NOTES

- **Front-loaded `/research` nav re-approval (planning action, not a build).** Per the iter-7 lesson and the iter-8 evaluator's explicit recommendation, this iteration adds a **PLANNED** `/research` entry to the `blueprint.md` nav skeleton (home for the compute-only labs J-25–J-31) and writes `runs/goal-session-i_can_see_the_wealthy_future_forever/state/blueprint.reapproval-requested`. **Why this iteration and not iter-10:** the reapproval marker pauses `run-goal.sh` at the *pre_decomposer* step of the **next** iteration (`run-goal.sh:804`), so writing it now means the human approves `/research` **before** iter-10's decomposer plans the first lab — i.e. before any code is built under the new nav home, which is exactly what the re-approval gate is for. Writing it now does NOT block iter-9's J-28 (iter-9's pre_decomposer check already passed). It also guarantees a data-feed outage can never fully stall the loop (the only autonomous work after J-28 is the `/research` labs). **iter-9 builds zero `/research` code** — if any `/research` route/page/endpoint appears in this iteration's diff, that is out of scope.
- **Apply iter-8 lesson (J-28 is the autonomous build).** J-28 escapes BOTH session blockers — it is compute-only over the stored seed (no fetch → not the J-22/23/24 data wall) AND its acceptance allows the pattern breakdown on System Health (not only a `/research` lab) → no nav home and no blueprint re-approval are needed for J-28 itself.
- **Apply iter-2/3/6 process lessons (for the reviewer/QA/evaluator).** Full-depth iters in this session have repeatedly finished WITHOUT a `status.json` or an `auditor` handoff, and QA reports have cited a `status.json` not on disk — do not block on or trust those artifacts; verify the critical anti-goal seams (pattern-not-status in `scoring.py`; detector referenced only on the ≤ D path; thresholds from `config.patterns.<name>`; mirror written once in `scanner.py`; `by_<name>` reads the stored mirror) directly in source. De-dup QA evidence by sha256 — at least two prior iters shipped byte-identical "before/after" screenshots; ground any before/after pattern-filter claim on distinct shots + a DOM assertion (filtered row count / badge presence), not a single screenshot pair.
- **Apply iter-6 lesson (browser concurrency).** If both the `qa` agent and the `browser-qa-agent` run Chrome-MCP checks, serialize browser access (one vacates before the other captures) and assert live DOM/URL state immediately before each capture — concurrent access to the shared single-tab Chrome silently corrupts captures.
- **Backend test runtime (project memory).** The full pytest suite takes ~14 minutes (heavy walk-forward boot); after the DB regeneration, run it ONCE and do not launch two pytest invocations concurrently.
- **DB is regenerated, not migrated.** `apps/backend/data/trendora.db` is gitignored and rebuilt on boot from the committed seed; deleting it and rebooting recomputes every immutable snapshot with the new pattern flags. This is offline/deterministic — no Yahoo fetch, no provider dependency. Confirm the Risk-Off bootstrap dates (`config.scanner.bootstrap_dates`) still label Risk-off and J-07/J-08 hold after regeneration.
- **Honest evidence cohorts.** With the quarterly walk-forward cadence, a new pattern that flags few names may yield a `by_<name>` cohort below `walk_forward.min_sample` (30) — that MUST show NA + `n`, never a fabricated number. Tune thresholds so the *latest snapshot* flags a non-trivial set for the leaderboard-filter demo, but do NOT loosen them to manufacture forward-test sample size.
