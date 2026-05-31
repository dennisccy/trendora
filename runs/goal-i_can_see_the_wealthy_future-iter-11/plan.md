# goal-i_can_see_the_wealthy_future-iter-11 Execution Plan

**Journey:** J-16 — VCP (Volatility Contraction Pattern): the product's first **detected price pattern**,
surfaced as a config-driven flag that rides each stock's immutable snapshot row **alongside** (never
replacing) its setup status — filterable + explained + forward-tested.
**Mode:** full-depth. New detector engine + a leaderboard filter + a row/detail badge + a System Health
forward-return dimension + new unit tests + ONE append-only schema column.

**Goal alignment (no drift):** Directly delivers `docs/goal.md` Key Capability **#19** and Must-have
journey **J-16**, and honors the **critical** anti-goal *"VCP is a pattern, not a status"*. The design
rides existing seams (verified in source at plan time — see Files), so it composes onto `score_stocks`
exactly as `setup`/`invalidation`/`themes` already do. **Scope guard:** J-16 acceptance **step 4**
(`/methodology` VCP glossary entry) is **deferred to J-12 / next iteration by design** (it adds a nav
route → reapproval) — it MUST NOT be scored as a J-16 failure/regression this iter.

**Blueprint conformance:** All three surfaces (`/stocks`, `/stocks/[ticker]`, `/system-health`) are
**existing** IA homes → **NO nav-skeleton change → NO `blueprint.reapproval-requested` this iter.** The
blueprint already carries the iter-11 serving note + the two additive Data-Contract rows (VCP flag + the
`by_vcp` breakdown) — so **no contract value, computing module, or serving path changes**; the change is
purely additive.

**Guard against the iter-9 silent no-op:** the developer MUST actually create `app/engine/patterns.py`,
edit the 6 backend + 4 frontend files, write the tests, **rebuild the DB**, and write the dev handoff.
Verified absent at plan time: `grep -rln "vcp" apps/` empty; no `detect_vcp`; `ScannerResult` has no
`is_vcp`; `compute_forward_aggregates` has no `by_vcp`; `Config` has no `patterns`. Treat as greenfield.

## What to Build

### Backend
- **`config.yaml` → new `patterns.vcp` block** holding EVERY VCP threshold (no magic numbers): `lookback_bars`,
  `min_contractions`, `max_contractions`, `max_base_depth_pct`, `contraction_shrink_ratio` (in (0,1]),
  `max_last_contraction_pct`, `pivot_proximity_pct`, `volume_dryup_ratio`, `volume_window`, `min_history_bars`.
  Tune so the **latest** snapshot flags a sensible non-trivial set (some, not all, not none); honest empty-state if genuinely none.
- **`config.py` → typed `VcpCfg` + `PatternsCfg{vcp:VcpCfg}`**, add `patterns: PatternsCfg` to `Config`
  (model after `WalkForwardCfg`/`ControlGroupCfg` at `config.py:307-363`). `@model_validator`: all
  windows/counts positive, `0 < contraction_shrink_ratio <= 1`, all `*_pct > 0`. Do NOT lean on `extra="allow"` for consumed keys.
- **NEW `app/engine/patterns.py` → `detect_vcp(closes, highs, lows, volumes, cfg) -> dict`** — pure,
  deterministic, **price+volume only**, NA-graceful, config-driven (only structural `0/1/2/100` literals).
  Detects progressively-shallower pullbacks (contractions) + volume dry-up into a pivot near the highs from
  the passed series (caller derives them from `bars_asof`, date ≤ D — no-lookahead). Returns
  `{flagged, reason, pivot, invalidation:{level,note}, contractions, detail}`. `< min_history_bars` or no
  qualifying base → `flagged=false` with an honest reason; **never a fabricated pattern**. `note` is the
  server-built sentence the UI renders VERBATIM (e.g. "VCP invalid below the last-contraction low at $X").
- **`scoring.py` → compose `vcp` onto each row** in `score_stocks` pass-3 (`scoring.py:300-338`): materialize
  the as-of `bars` **once** per ticker (reuse the `bars_asof` already read for `inv_closes` at line 319 — no
  extra DB round-trip), call `detect_vcp(...)`, attach `row["vcp"]`. **Do NOT touch `classify_setup`, the
  `setup` block, or the setup vocabulary** — VCP is purely additive; every row's `setup_status` MUST stay byte-identical.
- **`setups.py` → UNCHANGED** (`ALL_STATUSES`/`classify_setup` gain no VCP entry — critical anti-goal).
- **`models.py` → ONE append-only column** on `ScannerResult` (after `record_json`, `models.py:156`):
  `is_vcp: bool = Field(default=False, index=True)` — the denormalized **mirror** of `record_json`'s
  `vcp.flagged` (same role as `setup_status`/`leadership_bucket`). No other column; full `vcp` block stays in `record_json`.
- **`scanner.py` → populate the mirror** in `run_scan` (`scanner.py:91-107`): `is_vcp=row["vcp"]["flagged"]`
  on each persisted `ScannerResult`. Recomputes nothing; introduces no scoring/date literal (keeps `test_scanner_has_no_scoring_or_date_literals` green).
- **`forward_testing.py` → add a `by_vcp` dimension** to `compute_forward_aggregates` (the SAME module — no
  new endpoint/formula): extend `stock_obs` (`forward_testing.py:413-422`) with `"is_vcp": res.is_vcp` (read
  VERBATIM from the column), and add `by_vcp` to the payload (after `by_regime`, line 463) — two cohorts
  `{vcp: "VCP"|"non-VCP", mean_return, n}`, both padded (NA `mean_return:null, n:0` when empty). Map the
  boolean→label via `_group_means(order=[True,False])` + relabel, or a thin helper — keep ONE grouping path.
  **`compute_run_scorecard` (J-14) stays UNCHANGED.**
- **`test_no_magic_numbers.py` → add `"patterns.py"` to `CALC_FILES`** (`:19-27`). **Also extend
  `FORBIDDEN_INT_LITERALS` with any genuinely-new VCP tunable integers** (e.g. `8`, `35`; `65` is already in
  the set) so the contract is *enforced*, not merely claimed — every threshold must read from `config.patterns.vcp`.

### Frontend (re-format only — never compute a flag client-side)
- **`lib/api.ts`** — add `Vcp` type + `vcp: Vcp` on `StockRow` (`:175-186`); add
  `ForwardVcpRow extends ForwardGroupRow { vcp: string }` + `by_vcp: ForwardVcpRow[]` on `SystemHealthResponse`
  (`:361-375`). No new fetcher (VCP rides `/api/stocks`, `/api/stocks/{ticker}`, `/api/system-health`).
- **`app/stocks/page.tsx`** — add a **third `Select`** "VCP: All / VCP only / Non-VCP" (parallel to the
  sector/setup filters at `:98-119`) filtering `visible` on `row.vcp.flagged` (`:78-84`, pure client-side
  re-display — no recompute/re-sort). Add a compact teal **VCP `Badge`** to each flagged row (Setup cell or a
  dedicated column in `StockTableRow` `:208-210`) whose `title` carries `row.vcp.reason` + pivot +
  `row.vcp.invalidation.note`. "VCP only" with zero matches → existing styled empty-state.
- **`app/stocks/[ticker]/page.tsx`** — render the VCP badge **+ pivot + invalidation level** when
  `row.vcp.flagged` (setup/header card or a small VCP card by the invalidation block). SAME stored row the
  leaderboard serves (J-06). Not flagged → render nothing / explicit "No VCP pattern detected" (no fabricated pivot).
- **`app/system-health/page.tsx`** — add a **"Forward return: VCP vs non-VCP"** panel reusing the existing
  `BreakdownPanel` (`:299-331`): `rows={data.by_vcp.map(r => ({ label: r.vcp, ...r }))}`, `min={min}`, honest
  `emptyLabel`. Place it alongside the by-setup / by-regime panels in the grid (`:182-197`). Reuses the shared `forward-return.tsx` `Return`/`SampleSize`.

## Agents Required

- developer: **yes** — backend-data: **yes** (new `patterns.py` detector + `config.py`/`config.yaml` typed VCP
  block + compose onto `scoring.py` + one append-only `models.py` column + `scanner.py` mirror + `forward_testing.py`
  `by_vcp` + `test_no_magic_numbers.py` membership + tests + **DB rebuild**); frontend-ux: **yes** (VCP filter +
  badge on `/stocks`, badge+pivot/invalidation on detail, `by_vcp` panel on `/system-health`, `lib/api.ts` types).

## Frontend Present

Frontend Present: yes

## Files to Create/Modify

- `config.yaml` — **new `patterns.vcp` block** (every VCP threshold; repo root).
- `apps/backend/app/config.py` — `VcpCfg` + `PatternsCfg`; `patterns: PatternsCfg` on `Config` + validators.
- `apps/backend/app/engine/patterns.py` — **NEW** `detect_vcp(...)` detector.
- `apps/backend/app/engine/scoring.py` — compose `vcp` block onto each `score_stocks` row (reuse as-of bars).
- `apps/backend/app/engine/setups.py` — **UNCHANGED** (asserted; VCP must not enter `ALL_STATUSES`).
- `apps/backend/app/models.py` — one append-only `ScannerResult.is_vcp` column.
- `apps/backend/app/engine/scanner.py` — set `is_vcp` mirror in `run_scan`.
- `apps/backend/app/engine/forward_testing.py` — `is_vcp` on `stock_obs` + `by_vcp` payload dimension.
- `apps/backend/tests/test_patterns.py` — **NEW** detector unit tests.
- `apps/backend/tests/test_no_magic_numbers.py` — add `patterns.py` to `CALC_FILES`; extend forbidden ints.
- `apps/backend/tests/{test_scoring,test_scanner,test_forward_testing,test_api_engine,test_api_system_health,test_config*}.py`
  — extend with VCP assertions (shape, mirror equality, keystone, `by_vcp`, config validation).
- `apps/frontend/lib/api.ts` — `Vcp` type + `vcp` on `StockRow`; `ForwardVcpRow` + `by_vcp` on `SystemHealthResponse`.
- `apps/frontend/app/stocks/page.tsx` — VCP filter `Select` + VCP badge.
- `apps/frontend/app/stocks/[ticker]/page.tsx` — VCP badge + pivot/invalidation.
- `apps/frontend/app/system-health/page.tsx` — `by_vcp` `BreakdownPanel`.
- `docs/handoffs/goal-i_can_see_the_wealthy_future-iter-11-dev.md` — **NEW** dev handoff.

## UI Evolution (Frontend Present: yes)

- **New user-facing capability:** identify **VCP-flagged leaders**, filter the leaderboard to them, read each
  flag's plain-language reason + concrete pivot/invalidation on leaderboard AND detail, and see **whether
  VCP-flagged names have out-/under-performed** non-VCP names (forward-tested, with `n`) on System Health.
- **New information displayed:** a **VCP badge** (reason + pivot + invalidation note) on flagged rows + detail;
  a **VCP vs non-VCP** forward-return breakdown (mean + `n`, ⚠ below `min_sample`).
- **New user actions:** a **VCP filter** (All / VCP only / Non-VCP) on `/stocks`.
- **UI surface changes:** `/stocks` (filter control + VCP badge/column); `/stocks/[ticker]` (badge +
  pivot/invalidation line); `/system-health` (one extra breakdown panel). No layout overhaul.
- **Navigation changes:** **none** (all three are existing IA homes — no sidebar change, no reapproval).

## Visual Requirements (Frontend Present: yes)

- **Component patterns:** shadcn `Select` for the filter (match the existing sector/setup `Select`s); `Badge`
  for the VCP flag (accent/teal `--accent #4fd1c5`, with native `title` tooltip — distinct from setup-status
  variants); reuse `BreakdownPanel` + `forward-return.tsx` (`Return`/`SampleSize`) for `by_vcp`.
- **Layout:** dense dark table style + palette tokens already in use; VCP badge sits in/next to the Setup cell;
  the `by_vcp` panel joins the existing System Health 2-col grid. Numbers monospace/tabular.
- **Key visual effects:** colour-grade only via palette tokens; the badge is a compact accent chip, NOT a hype
  banner — it reads as "explained + separate from the verdict". Low-sample `n < min_sample` flagged with `--warn`.
- **States to handle:** "VCP only" → styled empty-state when zero match; detail "No VCP pattern detected" when
  unflagged (no fabricated pivot); `by_vcp` cohort with no measurable return → honest NA / em-dash; backend-unavailable card unchanged.

## Key Test Scenarios

- **`test_patterns.py` (NEW):** a constructed **VCP series flags** (positive) with pivot ≈ base high and
  invalidation ≈ last-contraction low; a **non-VCP series does not flag** (steady uptrend / expanding
  volatility); **short-history → `flagged=false` / NA** (no fabricated pivot); thresholds read from a test config (no literal).
- **VCP-is-a-pattern-not-a-status (critical):** `"VCP" not in ALL_STATUSES`; `score_stocks` setup statuses are
  **byte-identical** with vs without the VCP block; a **Risk-off run's VCP-flagged rows are all
  `Risk-off-watchlist`** (never Actionable); VCP alone never promotes Actionable.
- **Keystone (patch-to-raise, per iter-8 lesson — NOT value-equality):** monkeypatch `detect_vcp` AND the
  `score_*` engines to **raise**; assert `/api/stocks`, `/api/stocks/{ticker}`, and
  `compute_forward_aggregates(...)["by_vcp"]` still serve the **stored** VCP flag/breakdown — proving no
  re-detection in the read path.
- **Faithful mirror + immutability:** assert `ScannerResult.is_vcp == json.loads(record_json)["vcp"]["flagged"]`;
  confirm `test_latest_run_faithful_to_live_computation`, `test_run_scan_no_lookahead`,
  `test_run_scan_idempotent_and_immutable`, `test_risk_off_run_has_zero_actionable` stay green with the new field.
- **`by_vcp`:** groups stored `is_vcp` verbatim; both cohorts present; empty cohort → `mean_return=None, n=0`;
  the iter-6/iter-10 forward-testing tests stay **byte-green** (additive only).
- **Config:** `test_config*.py` — `patterns.vcp` valid block loads; non-positive window / `contraction_shrink_ratio`
  outside (0,1] / non-positive `*_pct` → `ConfigError` (never a silent default).
- **No magic numbers:** `test_no_magic_numbers.py` passes with `patterns.py` in `CALC_FILES`.
- **Browser / live evidence (J-16):** on `/stocks` apply the VCP filter → only flagged rows (or explicit
  empty-state) + a badge with reason + invalidation; open one flagged stock → detail badge + pivot/invalidation;
  `/system-health` → VCP-vs-non-VCP breakdown (numbers + `n`). **Distinct** PNGs per surface
  (leaderboard-filtered, leaderboard-badge, detail-badge, system-health-by-vcp) + `md5sum` them (iter-6 lesson).
  **Regression guards:** J-02 (sector+setup filters still narrow; ranking unchanged), J-05/J-06 (detail
  scores/chart; leaderboard==detail), J-09/J-10 (existing panels unchanged), J-13 (as-of switcher still re-points).
- **Frontend `npm run build`** clean (typecheck passes with the new `vcp` field on `StockRow`).

## Notes / Assumptions / Risks

- **DB rebuild is REQUIRED (reproducibility, not mutation):** SQLModel `create_all` does NOT ALTER an existing
  table, so `scanner_results.is_vcp` only appears in a freshly-created DB. Dev/QA MUST delete the gitignored
  `apps/backend/data/trendora.db` so bootstrap re-creates all snapshots from the frozen seed with VCP populated.
  This is the documented ephemeral-DB path — immutability (never UPDATEing a persisted row) is preserved.
- **Slow tests (iter-10 lesson):** each forward-testing fixture boots a walk-forward lifespan (~230s targeted /
  ~885s full). Run the **targeted** files (`test_patterns`, `test_scoring`, `test_scanner`, `test_forward_testing`,
  `test_api_engine`, `test_api_system_health`, `test_no_magic_numbers`, `test_config*`), budget minutes, use a
  **background task** (the foreground `sleep` guard blocks polling loops). First boot (backfill) takes minutes.
- **Coherence pre-note (for the auditor):** `is_vcp` is a denormalized typed **mirror** of `record_json`'s
  `vcp.flagged`, written once in the same `run_scan` transaction — the SAME single `detect_vcp` computation,
  stored once, exactly as `leadership_bucket`/`setup_status` already mirror the record. **Not** a second source.
- **Browser-qa debt (non-gating, runner-owner — unchanged 9 iters):** the dedicated browser-qa has SKIPped 9
  consecutive iters and may produce no evidence. Per the iter-7/iter-10 precedent, **self-produce live evidence**:
  boot backend with `CORS_ORIGINS=http://localhost:3835`, build frontend with `NEXT_PUBLIC_API_URL=http://localhost:8835`,
  `PORT=3835 npm run start`, drive Chrome; `await_text` on a **row-only** value (a VCP badge reason / pivot),
  never a filter/form placeholder. Do NOT down-grade J-16 reflexively if browser-qa SKIPs.
- **Out of scope (exclude):** `/methodology` + the VCP glossary entry (J-12/next); any `classify_setup`/setup-enum
  change; `compute_run_scorecard`/`/api/backtest` (J-14) change; watchlist UI change; a second VCP endpoint /
  server-side VCP query param / any client-side recomputation; any new pattern beyond VCP; order/execution/provider/secrets.
- After a clean J-16 → **15/16** Must-haves; the final iteration (J-12) → 16/16 and a legitimate GOAL_ACHIEVED check.
```
