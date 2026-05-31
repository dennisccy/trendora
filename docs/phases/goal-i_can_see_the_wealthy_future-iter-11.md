# Goal Iteration 11 — VCP detection: a config-driven pattern flag riding the immutable snapshot, filterable + explained + forward-tested (J-16)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** i_can_see_the_wealthy_future
- **Iteration:** 11
- **Mode:** next
- **Depth:** full
- **Frontend Present:** yes
- **Target journeys:** J-16
- **Required-still-passing journeys:** J-02, J-05, J-06, J-07, J-08, J-09, J-10, J-13, J-15 (and J-01, J-03, J-04, J-11, J-14 — re-confirmed at the data level because the whole snapshot DB is rebuilt this iter)
- **Anti-goal reminders (verbatim from `docs/goal.md`):**
  - **VCP is a pattern, not a status.** VCP MUST NOT enter the mutually-exclusive setup-status enum and MUST NOT by itself promote a name to "Actionable"; it rides as a separate flag computed once per run, price+volume only, with date ≤ D (no-lookahead), and is part of the immutable snapshot. Its detection thresholds MUST come from config (no magic numbers). *(critical — protects Single source of truth + Risk-Off gating)*
  - **No lookahead.** Scoring for a snapshot dated D MUST use only price bars with date ≤ D; forward returns MUST use only bars with date > D. The walk-forward MUST be unit-tested to prove no future bar influences an as-of score. *(critical)*
  - **Snapshots are immutable.** A persisted `scanner_run` and its result rows MUST never be updated or overwritten after creation; forward returns live in a separate append-only table keyed to the snapshot. *(critical)*
  - **Single source of truth.** Each of the six canonical scores (and the A–E bucket and setup status) MUST be computed exactly once by the scoring/regime engine and read identically by every page; the API and frontend MUST NOT recompute them. The same symbol's score MUST NOT differ between two views. *(critical)*
  - **No recompute in the read path.** Read endpoints MUST serve canonical values from the persisted immutable snapshot for the resolved as-of date; they MUST NOT recompute scores/returns/buckets per request. The scan is computed once per date (bootstrap, scheduled, or first view) and then read from storage. *(extends Single source of truth)*
  - **On-demand snapshots stay immutable & lookahead-free.** Creating a snapshot for a newly selected date is create-once: an existing snapshot MUST be read, never overwritten; an as-of-D snapshot MUST use only bars with date ≤ D. *(critical)*
  - **Risk-Off must gate Actionable.** When the regime is Risk-Off, the scanner MUST mark zero stocks "Actionable" (watchlist-only). *(critical)*
  - **No magic numbers.** Every scoring weight, threshold, decision-rule cutoff, bucket edge, universe entry, and theme definition MUST come from the config file — no such literal in calculation code.
  - **Honest forward-test for partial windows.** The per-date forward-test scorecard and the VCP-vs-non-VCP breakdown MUST show NA/partial for horizons or cohorts lacking enough samples and MUST show sample size — never fabricate or extrapolate a return to fill a gap. *(extends No fabricated data)*
  - **No fabricated data.** On a data-provider failure the system MUST surface an explicit stale/unavailable state and MUST NOT synthesize prices or scores to force a green journey.
  - **Scores must be explainable.** Every displayed score MUST carry its named component breakdown — no score may be shown as a bare number with no reasons. *(the VCP badge carries a reason + pivot/invalidation — never a bare flag)*
  - **Honest limitations surfaced.** Breadth/new-high-low are universe-relative; walk-forward evidence MUST be labelled as carrying survivorship bias so results are never overstated.
  - **No order/execution path.** No brokerage, order-placement, or capital-deployment code may exist or be reachable; Trendora is research-only. *(critical)*
  - **No secrets in source.** No hard-coded credentials, API keys, or tokens anywhere.

## GOAL

A user sees **VCP (Volatility Contraction Pattern)** detected as a config-driven flag that rides each stock's immutable snapshot row **alongside** (never replacing) its setup status: on `/stocks` they can **filter to VCP-flagged names** and each flagged row shows a **VCP badge with a plain-language reason and a concrete invalidation level (pivot / last-contraction low)**; the same flag reads identically on the **Stock Detail** page; and **System Health** gains a **VCP-vs-non-VCP forward-return breakdown** (mean return + sample size `n`, NA below `min_sample`) so the user can judge whether VCP-flagged names actually outperform.

## BACKGROUND

iter-10 fixed the iter-9 silent dev no-op and landed **J-14**, so **14/16 Must-haves pass**. The two remaining are **J-16 (VCP)** and **J-12 (config-backed glossary / `/methodology`)**. Per the iter-10 evaluator recommendation, this iteration builds **J-16 first** — the detected-pattern engine + its UI surfaces + its forward-test dimension — and **J-12 is sequenced LAST (next iteration)** so the glossary can document the VCP catalog entry. A clean J-16 → 15/16; then J-12 → 16/16 and a legitimate GOAL_ACHIEVED check.

**Why full depth:** J-16 is a NEW detected-pattern engine computed on the snapshot row + a leaderboard filter + a row badge + a detail surface + a System Health forward-return breakdown + a new forward-test dimension + new unit tests, and it touches a **critical** anti-goal (VCP-is-a-pattern-not-a-status). It also makes the iter's one structural change to `models.py` since iter-7 (a single APPEND-only typed column on `scanner_results`). This is well beyond lean scope. Prior depth was full; prior verdict CONTINUE.

**The design rides existing seams, so risk is contained.** The VCP flag is composed onto each per-stock row by `score_stocks` (exactly as `setup`, `invalidation`, and `themes` already are), so it is automatically: (a) **stored** losslessly in the existing `scanner_results.record_json`; (b) **served** by the existing `GET /api/stocks` + `GET /api/stocks/{ticker}` with **no endpoint change** — the leaderboard list row and the detail row are the byte-identical stored row (J-06); and (c) covered by the existing snapshot invariants — `test_run_scan_no_lookahead` (full-DB vs truncated-to-≤D DB → byte-identical children) already proves the VCP flag is no-lookahead because it lives in `record_json`, and `test_latest_run_faithful_to_live_computation` (stored `record_json` == live `score_stocks`) already proves faithful storage. The ONLY new typed column is `scanner_results.is_vcp` — a denormalized **mirror** of `record_json`'s `vcp.flagged` written in the same `run_scan` transaction, exactly as `leadership_bucket` / `setup_status` already mirror the record — used only so the forward-test `by_vcp` grouping can read it verbatim like `by_setup`/`by_bucket`.

**Lessons applied (from `lessons.md`):**
- **iter-8 (explicitly names "J-16 VCP breakdown"):** prove "serves from storage, not recompute" with a **patch-the-compute-to-raise seam**, NOT served==stored value-equality. → see TESTING (keystone): patch `detect_vcp` (and the `score_*` engines) to **raise** and assert `/api/stocks`, `/api/stocks/{ticker}`, and the System Health `by_vcp` breakdown still serve the stored VCP flag — proving no re-detection in the read path. Prefer **append-only** changes to the canonical compute path (the only `models.py` change is one nullable/defaulted column).
- **iter-9:** a full-depth dispatch can reach the evaluator having produced **zero code** (silent dev no-op). → The developer MUST actually create `app/engine/patterns.py`, edit `scoring.py`/`models.py`/`scanner.py`/`forward_testing.py`/`config.py`/`config.yaml`, edit the four frontend files, write the tests, and write the dev handoff; the evaluator MUST confirm code presence from `git status` + filesystem + `grep -rln vcp apps/` before scoring J-16.
- **iter-10:** changes to `forward_testing.py` make the walk-forward boot slow (~230s+ for the targeted tests; ~885s full) because each fixture boots a walk-forward lifespan. → Run the **targeted** test files (`test_patterns.py`, `test_scoring.py`, `test_scanner.py`, `test_forward_testing.py`, `test_api_engine.py`, `test_api_system_health.py`, `test_no_magic_numbers.py`, `test_config*.py`), budget minutes, use a background task (the foreground `sleep` guard blocks polling loops). Also: the dedicated browser-qa has SKIPped 9 consecutive iters and may produce no evidence — be ready to **self-produce live evidence** (boot services + drive Chrome) per the iter-7/iter-10 precedent.
- **iter-7:** to verify a UI live, launch the backend with `CORS_ORIGINS=http://localhost:<frontend-port>` and build the frontend with `NEXT_PUBLIC_API_URL=http://localhost:8835`; `await_text` must target a row-only value (e.g. a VCP badge reason / pivot), never a form/filter placeholder.
- **iter-6:** the VCP surfaces span three pages (leaderboard, detail, System Health) — request **distinct** evidence captures per surface and `md5sum` them; do not count one full-page shot as proof of two surfaces.

## IN SCOPE

### Backend

- [ ] **Config — `config.yaml` gains a `patterns:` section with a `vcp:` block holding EVERY VCP threshold** (anti-goal: No magic numbers). Illustrative key set (the developer finalizes exact values against the committed seed; values are tunable hypotheses, not final):
  ```yaml
  patterns:
    vcp:
      lookback_bars: 65            # base window scanned for contractions (trading days)
      min_contractions: 2          # min number of progressively-shallower pullbacks in the base
      max_contractions: 4          # cap on contractions considered
      max_base_depth_pct: 35       # the first/deepest contraction must be <= this % (VCP bases are not deep crashes)
      contraction_shrink_ratio: 0.8  # each contraction must be <= prior * this (volatility CONTRACTING) — in (0,1]
      max_last_contraction_pct: 10 # the final (tightest) contraction must be <= this %
      pivot_proximity_pct: 8       # latest close must be within this % below the base high (near the pivot)
      volume_dryup_ratio: 0.85     # recent avg volume / base avg volume must be <= this (volume drying up)
      volume_window: 10            # bars for the "recent" volume average (vs the base average)
      min_history_bars: 65         # below this a symbol cannot be evaluated -> NA (flagged=false, never fabricated)
  ```
- [ ] **Config loader — `config.py` gains typed validation** for the new section: a `VcpCfg` (and `PatternsCfg { vcp: VcpCfg }`) BaseModel with a `@model_validator` asserting positivity of all windows/counts, `0 < contraction_shrink_ratio <= 1`, and `0 < *_pct` percentages; add `patterns: PatternsCfg` to `Config`. Do not rely on `extra="allow"` for the consumed keys — type and validate them like `WalkForwardCfg`/`ControlGroupCfg`. (Optional, recommended: a `@model_validator` asserting `vcp.min_history_bars <= ` the seed's typical length is NOT required — just positivity/range checks.)
- [ ] **New detector module `app/engine/patterns.py` — `detect_vcp(closes, highs, lows, volumes, cfg) -> dict`** (or take a `bars` list; the developer chooses the cleanest signature reusing `app.engine.prices` accessors). Pure, deterministic, **price+volume only**, NA-graceful, config-driven (NO numeric literal beyond structural 0/1/2/100 — see the no-magic-numbers requirement below). It detects progressively-shallower pullbacks (contractions) + volume dry-up into a pivot near the highs, using ONLY the passed series (which the caller derives from `bars_asof`, date ≤ D — no-lookahead). Returns:
  ```python
  {
    "flagged": bool,
    "reason": str,            # plain-language, server-built ("3 contractions tightening 18%→9%→5%, volume drying up, 4% below the $X pivot")
    "pivot": float | None,    # the breakout level = the base high
    "invalidation": {         # concrete level where the pattern is wrong (last-contraction low)
        "level": float | None,
        "note": str,          # server-built sentence, rendered VERBATIM by the UI ("VCP invalid below the last-contraction low at $X")
    },
    "contractions": list,     # the detected contraction depths (evidence; [] when not flagged)
    "detail": dict,           # n_contractions, volume_ratio, dist_from_pivot_pct — for explainability
  }
  ```
  Insufficient history (< `min_history_bars`) or no qualifying base → `flagged=false` with an honest reason; **never a fabricated pattern** (anti-goal: No fabricated data). Tune thresholds so the **latest** snapshot flags a sensible non-trivial set (some, not all, not none) so the badge/filter/detail are demonstrable live; if the seed genuinely yields none on a given snapshot the UI must show an explicit empty-state (acceptable per J-16 acceptance).
- [ ] **`app/engine/scoring.py` — compose the VCP flag onto each per-stock row.** In `score_stocks`, call `detect_vcp(...)` once per stock (reuse the series already materialized for invalidation/components — no extra DB round-trip) and attach a `"vcp"` block to the row dict alongside `setup`, `invalidation`, `themes`. **Do NOT touch `classify_setup`, the `setup` block, or the setup vocabulary** — VCP is purely additive on the row. The setup status of every row MUST be byte-identical to before this iter (unit-proven).
- [ ] **`app/engine/setups.py` — UNCHANGED.** `ALL_STATUSES` and `classify_setup` MUST NOT gain a VCP entry and MUST NOT consume the VCP flag (VCP-is-a-pattern-not-a-status critical). (This file stays in the no-magic-numbers `CALC_FILES` set unchanged.)
- [ ] **`app/models.py` — add ONE typed, indexed, defaulted column to `ScannerResult`:** `is_vcp: bool = Field(default=False, index=True)`. This is the denormalized **mirror** of `record_json`'s `vcp.flagged` (the same role `setup_status` / `leadership_bucket` play), used only for the forward-test `by_vcp` grouping + (optionally) server-side filtering. The full `vcp` block stays in `record_json` (no other column). This is an **APPEND-only schema addition** — no existing snapshot row is ever UPDATEd; the gitignored DB is rebuilt deterministically from the frozen seed (reproducibility, not mutation — see the `scanner.py` docstring). `forward_returns` stays a separate append-only table (Snapshots-immutable critical intact).
- [ ] **`app/engine/scanner.py` — populate the mirror in `run_scan`.** Set `is_vcp=row["vcp"]["flagged"]` on each persisted `ScannerResult`; `record_json=json.dumps(row)` already captures the full `vcp` block. `run_scan` still recomputes nothing — the VCP flag is a faithful copy of `score_stocks`'s output. No new ISO-date or scoring literal (the file stays clean for `test_scanner_has_no_scoring_or_date_literals`).
- [ ] **`app/engine/forward_testing.py` — add a `by_vcp` dimension to `compute_forward_aggregates` (the SAME single module — no new endpoint, no second formula).** Extend the per-stock `stock_obs` dict with `"is_vcp": res.is_vcp` (read **verbatim** from the stored `scanner_results` column, never re-detected). Add a `by_vcp` breakdown to the returned payload: two cohorts — VCP-flagged vs non-VCP — each `{vcp: <"VCP"|"non-VCP">, mean_return, n}`, NA (`mean_return: null`, `n: 0`) when empty; reuse the existing grouping helper (`_group_means` with a `[True, False]` order mapped to the labels, or an equivalent thin helper). The cell carries `n` so the UI flags `n < min_sample ⚠`; the existing `survivorship_bias` label/`min_sample` already ride the payload. `compute_run_scorecard` (J-14) is NOT required to add VCP (out of scope — keep it unchanged).
- [ ] **`apps/backend/tests/test_no_magic_numbers.py` — add `"patterns.py"` to `CALC_FILES`** so the new detector is held to the no-magic-numbers contract (every threshold from `config.patterns.vcp`; only structural 0/1/2/100 literals permitted; add any genuinely-new structural integer used by the detector to the allowed set ONLY if it is not a tunable). Keep `forward_testing.py`/`scoring.py` in the set (unchanged membership).

### Frontend

- [ ] **`apps/frontend/lib/api.ts`** — add a `Vcp` type (`{ flagged: boolean; reason: string; pivot: number | null; invalidation: { level: number | null; note: string }; contractions?: number[]; detail?: Record<string, number | null> }`) and `vcp: Vcp` on `StockRow`. Add a `ForwardVcpRow extends ForwardGroupRow { vcp: string }` and `by_vcp: ForwardVcpRow[]` on `SystemHealthResponse`. No new fetcher (VCP rides `/api/stocks`, `/api/stocks/{ticker}`, and `/api/system-health`). RE-FORMAT only — never compute a flag client-side.
- [ ] **`apps/frontend/app/stocks/page.tsx`** — add a **VCP filter** (a third `Select` "VCP: All / VCP only / Non-VCP") that filters the already-fetched rows client-side on `row.vcp.flagged` (parallel to the existing sector/setup filters — pure re-display, no recompute, no re-sort). Add a **VCP badge** to each flagged row (a compact accent/teal "VCP" `Badge`, in the Setup cell or a dedicated column) whose `title`/tooltip carries `row.vcp.reason` + pivot + `row.vcp.invalidation.note`. When "VCP only" matches nothing, show the existing styled empty-state.
- [ ] **`apps/frontend/app/stocks/[ticker]/page.tsx`** — render the **VCP badge** (when `row.vcp.flagged`) with its **pivot + invalidation level** (in the setup/header card or a small dedicated VCP card next to the invalidation block). The value is the SAME stored row the leaderboard serves (J-06 — identical). When not flagged, render nothing or an explicit "No VCP pattern detected" line (no fabricated pivot).
- [ ] **`apps/frontend/app/system-health/page.tsx`** — add a **"Forward return: VCP vs non-VCP"** breakdown panel rendering `data.by_vcp` (reuse the existing `BreakdownPanel` + the shared `forward-return.tsx` `Return`/`SampleSize`/`fmtPct` formatters — `n < min_sample` flagged ⚠, NA when `mean_return == null`). Place it alongside the existing by-setup / by-regime panels. Empty-label honestly when no VCP/non-VCP observation has a measurable return at the horizon.

### New user-facing capability
The user can identify **VCP-flagged leaders**, filter the leaderboard to them, read each flag's plain-language reason + concrete pivot/invalidation level on both the leaderboard and the detail page, and see **whether VCP-flagged names have historically out- or under-performed non-VCP names** (forward-tested, with sample size) on System Health.

### New information displayed
- A **VCP badge** (with reason + pivot + invalidation note) on flagged leaderboard rows and on the Stock Detail page.
- A **VCP vs non-VCP** forward-return breakdown (mean return + `n`, ⚠ below `min_sample`) on System Health.

### New user actions
- A **VCP filter** control on `/stocks` (All / VCP only / Non-VCP).

### UI surface changes
- `/stocks`: a new filter control + a VCP badge/column (no layout overhaul; matches the existing dense table style + palette tokens).
- `/stocks/[ticker]`: a VCP badge + pivot/invalidation line.
- `/system-health`: one additional breakdown panel.

### Product surface delta
Trendora gains its **first detected price pattern**, surfaced exactly the way the product's skeptical, evidence-driven philosophy demands: explained (reason + invalidation), separate from the actionability verdict (a name can be "Breakout-watch" AND VCP, and VCP alone never makes it "Actionable"), and **forward-tested** (does the pattern actually add edge?) — not a hype badge.

### Blueprint conformance
All three surfaces are **existing** Information-Architecture homes: `/stocks` (J-02), `/stocks/[ticker]` (J-05), `/system-health` (J-09/J-10). **No nav-skeleton change → NO `blueprint.reapproval-requested` this iter.** (J-12's `/methodology`, next iteration, WILL add a nav route and need reapproval.) The blueprint Data Contract is edited **additively** (two new value rows + an iter-11 serving note) — see below.

### Data-contract additions
Registered in `blueprint.md` this iteration (additive; no existing value gets a second source):
1. **Detected pattern — VCP flag (+ pivot / invalidation level / reason)** — computed **once per run** by `app.engine.patterns:detect_vcp` (called per stock by `app.engine.scoring:score_stocks` and composed onto the row like `setup`/`invalidation`); **stored** on the immutable snapshot as the full `vcp` block in the existing `scanner_results.record_json` PLUS the denormalized typed mirror `scanner_results.is_vcp`; **served** by the EXISTING `GET /api/stocks` (list) and `GET /api/stocks/{ticker}` (detail) — it rides the same per-stock row, so leaderboard and detail are byte-identical (J-06). The `/stocks` VCP filter is pure client-side re-display. NA → `flagged=false` (never fabricated). Computed price+volume only, date ≤ D (no-lookahead). SEPARATE from the setup status (never enters `ALL_STATUSES`, never promotes Actionable).
2. **VCP-vs-non-VCP forward-return breakdown (`by_vcp`)** — computed by the EXISTING `app.engine.forward_testing:compute_forward_aggregates` (the SAME single module; a new grouping dimension reading the stored `scanner_results.is_vcp` VERBATIM joined to stored `forward_returns`, exactly like `by_setup`/`by_bucket`); **served** by the EXISTING `GET /api/system-health`. Each cohort carries `n`; NA/⚠ below `min_sample`; survivorship label inherited. No new endpoint, no second computation.

## OUT OF SCOPE

- **`/methodology` glossary page and the VCP glossary entry (J-12).** Sequenced as the NEXT iteration (it adds a nav route → reapproval). J-16 acceptance step 4 ("On `/methodology`, read the VCP glossary entry") is delivered by J-12 — it MUST NOT be treated as a J-16 failure/regression this iter (the page does not exist yet by design). To make J-12 trivial, the VCP `reason`/`detail` and thresholds are config-backed so the glossary can render them with no code change.
- **No change to the setup-status enum / `classify_setup`** — VCP must NOT be added there (critical anti-goal).
- **No change to `compute_run_scorecard` / `/api/backtest` (J-14)** — the per-date scorecard does not gain a VCP dimension this iter (keep it unchanged; J-14 stays green).
- **No watchlist UI change** — the watchlist row may incidentally carry `vcp` (it reads the live `score_stocks` row) but J-11 requires no VCP display; do not add one.
- **No second VCP endpoint, no server-side VCP query param, no client-side recomputation** of any score/flag/return.
- **No new pattern beyond VCP** (the catalog is designed for more, but only VCP is built this session).
- No order/execution/portfolio path; no live-provider fetch; no secrets.

## DEFINITION OF DONE

- [ ] **Implementation actually present** (guard against the iter-9 no-op): `app/engine/patterns.py` exists; `git diff` shows edits to `scoring.py`, `models.py`, `scanner.py`, `forward_testing.py`, `config.py`, `config.yaml`, `lib/api.ts`, `stocks/page.tsx`, `stocks/[ticker]/page.tsx`, `system-health/page.tsx`; `grep -rln "vcp" apps/` is non-empty; `status.json` reaches `qa_complete`/`tests_run=true`; the dev handoff exists at `docs/handoffs/goal-i_can_see_the_wealthy_future-iter-11-dev.md`.
- [ ] **J-16 passes** (via browser-qa or self-produced live evidence): the VCP filter narrows the leaderboard to flagged names (or an explicit empty-state); a flagged row shows a VCP badge + reason + concrete invalidation level (pivot / last-contraction low); the same flag/pivot/invalidation render identically on the Stock Detail page; System Health shows a VCP-vs-non-VCP mean-forward-return breakdown with `n` (NA/⚠ below `min_sample`). *(The `/methodology` VCP entry is J-12/next iter — explicitly deferred, not a gap here.)*
- [ ] **VCP-is-a-pattern-not-a-status (critical) proven:** VCP never appears in `ALL_STATUSES`; adding the detector changes NO row's `setup_status`; a VCP-flagged row in a Risk-off run is still `Risk-off-watchlist` (not Actionable); a VCP-flagged row never becomes Actionable solely from the flag. *(unit-proven)*
- [ ] **No-lookahead (critical) proven:** the VCP flag for a run dated D is unaffected by bars with date > D (the existing `test_run_scan_no_lookahead` covers this because `vcp` rides `record_json`; confirm it still passes and, if useful, add a focused `detect_vcp` no-lookahead assertion).
- [ ] **Single-source / no-recompute-in-read-path (critical) proven** by a **patch-the-compute-to-raise** keystone (not value-equality): with `detect_vcp` (and `score_*`) patched to raise, `/api/stocks`, `/api/stocks/{ticker}`, and the System Health `by_vcp` breakdown still serve the stored VCP flag.
- [ ] **Snapshots-immutable (critical) intact:** `models.py` adds only the one APPEND-only `is_vcp` column; `run_scan` UPDATEs no existing row; `is_vcp` faithfully mirrors `record_json`'s `vcp.flagged` (assert equality); `forward_returns` stays separate/INSERT-only.
- [ ] **No magic numbers:** `test_no_magic_numbers.py` (with `patterns.py` added) passes; every VCP threshold comes from `config.patterns.vcp`.
- [ ] **Required-still-passing journeys remain green** (J-02, J-05, J-06, J-07, J-08, J-09, J-10, J-13, J-15; and J-01/J-03/J-04/J-11/J-14 re-confirmed after the DB rebuild). Frontend `npm run build` is clean (typecheck passes with the new `vcp` field on `StockRow`).
- [ ] **Unit tests pass; no regressions:** the faithful-equality, no-lookahead, idempotent/immutable, and risk-off scanner tests stay green; the new VCP tests pass; existing `score_stocks`-shape assertions are extended (not broken) to include `vcp`.
- [ ] **Dev handoff written** at `docs/handoffs/goal-i_can_see_the_wealthy_future-iter-11-dev.md`.

## TESTING REQUIREMENTS

- **Browser (by ID): J-16** — on `/stocks` apply the VCP filter and confirm only flagged rows remain (or an explicit empty-state); confirm a flagged row shows the VCP badge + reason + invalidation level; open one flagged stock and confirm the detail page shows the VCP badge with pivot/invalidation; on `/system-health` read the VCP-vs-non-VCP breakdown (numbers + `n`). **Regression guards:** J-02 (sector + setup filters still narrow rows; ranking unchanged), J-05/J-06 (detail scores/chart render; leaderboard==detail), J-09/J-10 (existing by-bucket/by-setup/by-regime/control-group panels unchanged), J-13 (as-of switcher still re-points). Capture **distinct** PNGs per surface (leaderboard-filtered, leaderboard-badge, detail-badge, system-health-by-vcp) and `md5sum` them (iter-6 lesson). *(Deferred, NOT tested this iter: J-16 step 4 `/methodology` — J-12/next.)*
- **Unit/integration (assert exact behavior, not just "runs"):**
  - `test_patterns.py` (NEW): a constructed/known **VCP series flags** (positive) with the expected pivot ≈ base high and invalidation ≈ last-contraction low; a **non-VCP series does not flag** (negative — e.g. a steady uptrend with no contraction, or expanding volatility); a **short-history series → `flagged=false` / NA** (never fabricated); thresholds read from a test config (no literal).
  - **VCP-not-status:** assert `"VCP" not in ALL_STATUSES`; assert that for the seed, `score_stocks` setup statuses are byte-identical with vs without the VCP block (the flag does not alter any status); assert a Risk-off run's VCP-flagged rows are all `Risk-off-watchlist`.
  - **Keystone (patch-to-raise):** monkeypatch `app.engine.patterns.detect_vcp` (and the `score_*` engines) to raise; assert `stocks_payload` / `stock_detail_payload` and `compute_forward_aggregates(...)["by_vcp"]` still return the stored VCP flag/breakdown from `scanner_results` — proving the read path recomputes nothing.
  - **Faithful mirror + no-lookahead + immutable:** confirm `test_latest_run_faithful_to_live_computation`, `test_run_scan_no_lookahead`, `test_run_scan_idempotent_and_immutable`, `test_risk_off_run_has_zero_actionable` stay green with the new field; add an assertion that `ScannerResult.is_vcp == json.loads(record_json)["vcp"]["flagged"]`.
  - **forward_testing `by_vcp`:** groups stored `is_vcp` verbatim; each cohort carries `n`; an empty cohort → `mean_return=None`, `n=0`; the iter-6/iter-10 forward-testing tests stay byte-green (the `by_vcp` addition is purely additive).
  - **config:** `test_config*.py` covers the new `patterns.vcp` typed validation (missing/invalid key → `ConfigError`; valid block loads).
- **Error cases:** insufficient history → `flagged=false` (no fabricated pivot); a config `patterns.vcp` with a non-positive window or `contraction_shrink_ratio` outside (0,1] → `ConfigError` (never a silent default); the `/stocks` "VCP only" filter with zero matches → explicit empty-state (no fabricated rows).

## NOTES

- **DB rebuild is required and is reproducibility, not mutation.** SQLModel `create_all` does NOT ALTER an existing table, so the new `scanner_results.is_vcp` column only appears in a freshly-created DB. The developer/QA MUST delete the gitignored `apps/backend/data/trendora.db` so the bootstrap re-creates all snapshots from the frozen seed with the VCP flag populated. This is the documented ephemeral-DB path (`scanner.py` docstring) — the immutability anti-goal is about never UPDATEing a persisted row, which is preserved. Expect the first boot (walk-forward backfill) to take minutes (iter-10 lesson).
- **Tune for a demonstrable, honest result.** Aim for the latest snapshot to flag a non-trivial set of VCP names (so the badge/filter/detail are live-demonstrable) and for the walk-forward snapshots to yield enough VCP observations that the `by_vcp` cells are meaningful — but if a snapshot honestly has none, the empty-state/NA path is correct and acceptable (never loosen thresholds to fabricate flags).
- **Coherence pre-note for the auditor:** `is_vcp` is a denormalized typed MIRROR of `record_json`'s `vcp.flagged`, written once in the same `run_scan` transaction — the SAME single computation (`detect_vcp` once per run), stored once, exactly as `leadership_bucket`/`setup_status` already mirror the record. It is NOT a second source/computation. The leaderboard/detail read the block from `record_json`; the forward-test reads the mirror column; both trace to one `detect_vcp` call.
- **Runner-owner debt (NON-gating, NOT product/spec scope; unchanged across iters 3–10; flagged, not re-litigated — iter-5 lesson: spec text cannot fix runner behaviour):** the dedicated browser-qa has SKIPped 9 consecutive iters and the audit handoff (`reports/audits/`) has been missing 9 full-depth iters. Durable fixes belong in `scripts/automation/*.sh` (own/await/self-heal the frontend with `CORS_ORIGINS` set to the frontend port; emit the audit handoff). If browser-qa SKIPs again, the evaluator should self-produce live evidence (boot services + drive Chrome) per the iter-7/iter-10 precedent rather than down-grade J-16 reflexively.
- After a clean J-16 → **15/16** Must-haves. Next (final) iteration: **J-12** (`/methodology` config-backed glossary incl. the VCP catalog entry; adds a nav route → `blueprint.reapproval-requested`) → 16/16 and a legitimate GOAL_ACHIEVED check.
