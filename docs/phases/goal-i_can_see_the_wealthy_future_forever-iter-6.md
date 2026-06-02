# Goal Iteration 6 — Full chart history through latest (display-only) + Backtest leadership cohorts with horizon-linked realized returns

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** i_can_see_the_wealthy_future_forever
- **Iteration:** 6
- **Mode:** next
- **Depth:** full
- **Frontend Present:** yes
- **Target journeys:** J-20, J-21
- **Required-still-passing journeys:** J-05, J-06, J-13, J-14, J-15, J-16, J-18, J-19
- **Anti-goal reminders (verbatim from `docs/goal.md`):**
  - **No lookahead.** Scoring for a snapshot dated D MUST use only price bars with date ≤ D; forward returns MUST use only bars with date > D. The walk-forward MUST be unit-tested to prove no future bar influences an as-of score. Chart **visualization** MAY render bars dated > D strictly as a labelled forward/after-as-of display; this display path MUST NOT feed any score, bucket, setup status, pattern flag, factor value, or ranking — all of which remain computed from bars with date ≤ D — and the moving-average lines drawn past D are visualization only, never as-of signals. *(critical)*
  - **Single source of truth.** Each of the six canonical scores (and the A–E bucket and setup status) MUST be computed exactly once by the scoring/regime engine and read identically by every page; the API and frontend MUST NOT recompute them. The same symbol's score MUST NOT differ between two views. *(critical)*
  - **No recompute in the read path.** Read endpoints MUST serve canonical values from the persisted immutable snapshot for the resolved as-of date; they MUST NOT recompute scores/returns/buckets per request. *(extends Single source of truth)*
  - **Attribution is read-only.** The forward-return attribution slices (per-stock contribution, by-sector, by-rank-band, distribution/hit-rate) MUST be derived from the stored per-observation forward returns; the API and frontend MUST NOT recompute returns to build them. *(extends No recompute in the read path)*
  - **Exactly one date selector.** The frontend MUST NOT maintain a second, independent date state; every date-scoped page (including Backtest) reads the single global as-of control. The Stock-Detail chart timeframe selector (1D/1h/15m/5m) is NOT a date control — it changes bar granularity only, bounded by the resolved as-of date. *(extends Single source of truth)*
  - **No fabricated data.** On a data-provider failure the system MUST surface an explicit stale/unavailable state and MUST NOT synthesize prices or scores to force a green journey.
  - **Honest forward-test for partial windows.** The per-date forward-test scorecard and the VCP-vs-non-VCP breakdown MUST show NA/partial for horizons or cohorts lacking enough samples and MUST show sample size — never fabricate or extrapolate a return to fill a gap. *(extends No fabricated data)*
  - **Snapshots are immutable.** A persisted `scanner_run` and its result rows MUST never be updated or overwritten after creation; forward returns live in a separate append-only table keyed to the snapshot. *(critical)*

## GOAL

Open the new-wave journeys on the two surfaces that already exist: when viewing a historical as-of date D, the Stock-Detail chart shows the **full price/MA/volume path through the latest seed date** with D clearly marked and the post-D region labelled forward/display-only (J-20); and the Backtest page moves **Top Sectors / Top Themes / Ranked Cohort below Return Attribution**, each carrying a **realized forward-return at the selected horizon** read from stored forward returns (J-21).

## BACKGROUND

The prior session reached **GOAL_ACHIEVED** on J-01…J-19 (all passing, iter-5). `docs/goal.md` was then extended with a next wave, **J-20…J-31** (Key Capabilities 23–31): chart-through-latest, backtest cohort returns, ~500-name universe, multi-timeframe bars + selector, a Factor Lab and a Setup & Pattern Lab on a new `/research` home, more detected patterns, a volatility factor family, and an end-to-end synthesis journey. A file-scan confirms none are built (`/research` does not exist; the chart endpoint serves only bars ≤ as-of; the backtest leadership lists carry no realized return).

This iteration deliberately starts with the **two lowest-risk, highest-coherence** members of the wave — J-20 and J-21 — because both *refine pages that already pass* (Stock Detail / Backtest), both build on already-green journeys (J-05, J-14, J-19), neither needs the heavy seed/infra work the rest of the wave requires (~500 universe, intraday bars, the labs), and neither introduces a new nav home. They share one discipline: **honestly displaying forward/realized returns without letting that data contaminate the as-of scores** — J-20 via a display-only chart extension, J-21 via a read-only projection of already-stored forward returns. Depth is **full** (the prior iters were lean verify passes) because the work crosses backend + frontend and carries two critical anti-goal seams that warrant the reviewer/coherence-auditor/QA full pipeline as the new wave begins.

The heavier wave members (J-22 universe expansion; J-23/J-24 multi-timeframe; J-25–J-31 the `/research` labs, more patterns, volatility family, synthesis) are explicitly **out of scope** here and sequenced for later iterations — the `/research` labs will introduce a new sidebar home and will require a blueprint nav re-approval when reached.

## IN SCOPE

### Backend
- [ ] **(J-20) Chart full-path-through-latest, display-only.** Add a `prices` helper (e.g. `bars_through_latest(session, symbol)`) returning the symbol's full ascending bar list **not** bounded by D (distinct from `bars_asof`). Extend `GET /api/stocks/{ticker}/bars` so the chart can render through the latest seed date for the resolved as-of D, exposing the **as-of boundary** so the frontend can split/label the forward region (the response already returns `asof_date`; add the latest date and/or a per-bar `is_forward`/boundary so the post-D region is identifiable). The `ma` map for the post-D region is computed over the full series **for display only**.
  - **Recommended mechanism:** gate the forward extension behind an explicit opt-in (e.g. `?through=latest`) so the endpoint's default contract stays ≤ D and the no-lookahead boundary is obvious; the Stock-Detail chart opts in. (Developer may choose always-full + marker instead, provided the no-lookahead seam below is preserved and tested.)
  - **CRITICAL no-lookahead:** the post-D bars and their MA values are **visualization only**. They MUST NOT feed any score, bucket, setup status, VCP flag, factor, or ranking — all of which continue to read the immutable snapshot row for D (bars ≤ D). In particular the Stock-Detail invalidation level and score-component MAs stay sourced from the snapshot row (the ≤ D value), **not** from the new full-path MA series. Do **not** route the full-path helper into `score_stocks` / `detect_vcp` / `run_scan`.
- [ ] **(J-21) Backtest leadership realized returns (read-only projection).** Add to the per-date backtest payload, for the resolved run and **each** horizon, the realized forward return of:
  - **(a) each sector** in Top Sectors = its **sector-ETF's** stored forward return at that horizon (sector→ETF via the existing `_sector_etf_by_name`);
  - **(b) each theme** in Top Themes = the **equal-weight mean** of its member stocks' stored forward returns at that horizon (members via the config theme map);
  - **(c) each cohort stock** in Ranked Cohort = its **own** stored forward return at that horizon.
  - Derive **once** from the stored `forward_returns` rows (the SAME per-observation data `compute_run_scorecard` / `_attribution_slices` already read) — **never recompute a return**. Expose keyed by horizon (e.g. add a `leadership_returns` object to each `scorecard.by_horizon[*]` entry, mirroring how `attribution` rides each entry). Return **null (NA)** honestly for any (row, horizon) lacking enough post-snapshot bars; fabricate nothing. Any tunable (e.g. how many rows to annotate) comes from config — no magic numbers.

### Frontend
- [ ] **(J-20) Stock-Detail chart.** Render the chart through the latest seed date; draw a visible **divider and/or shaded region at the as-of date D** and label the post-D region "forward / after-as-of (display only)". Thread the as-of boundary into `PriceChart`. The three scores, setup status, VCP flag, and invalidation note continue to read the detail payload (`fetchStock`) unchanged. At the latest as-of (no post-D bars) the chart is visually unchanged. Use design-system tokens for the divider/shaded region (no ad-hoc hex).
- [ ] **(J-21) Backtest page reorg.** Section order becomes: **as-of scan summary (regime + candidate counts) → forward-test scorecard → Return Attribution → Top Sectors, Top Themes, Ranked Cohort** (the three leadership lists move BELOW Return Attribution). Add a **realized forward-return column** to each of the three lists at the selected horizon, read from the new `leadership_returns` payload and joined onto the rows already fetched from `/api/sectors`, `/api/themes`, `/api/stocks`. **Lift the existing horizon view-selector** so the SAME selector re-points both Return Attribution and the three lists' return columns. Render NA ("—") honestly when a horizon lacks post-bars. The selector stays a **VIEW selector** (no refetch, no date param, no date state) — the single global as-of switcher still drives the date.

### New user-facing capability
- Viewing a historical as-of date, a user sees each stock's chart through the latest seed bar with the as-of point marked and the forward region labelled — they can see what happened after the snapshot without that future data contaminating the as-of scores.
- On Backtest, a user reads each top sector / top theme / ranked-cohort name's realized forward return at a chosen horizon, directly beneath the attribution that explains the aggregate — and flips the horizon to re-point every return at once.

### New information displayed
- J-20: post-as-of price/MA/volume bars (labelled forward/display-only) and an as-of boundary marker on the Stock-Detail chart.
- J-21: a realized forward-return column on Top Sectors, Top Themes, and Ranked Cohort (per selected horizon), read from stored forward returns, with honest NA.

### New user actions
- J-20: none new — the existing global as-of switcher drives it.
- J-21: the existing horizon selector now also re-points the three leadership lists' return columns (one selector, attribution + lists).

### UI surface changes
- `/stocks/[ticker]` — chart extends through latest with a labelled forward region + as-of divider; everything else unchanged.
- `/backtest` — the three leadership lists relocate below Return Attribution and each gains a horizon-linked realized-return column; one horizon selector drives attribution + all three.

### Product surface delta
- The product now shows "what happened after D" honestly on the chart and "which names/sectors/themes actually delivered the realized return" on Backtest — both display-only-or-stored, neither contaminating the as-of scores or introducing a second date control.

### Blueprint conformance
- **No new nav home and no nav-skeleton change.** J-20 lives on the existing `/stocks/[ticker]` (Stock Detail) home; J-21 lives on the existing `/backtest` home. Both are registered as additive rows in `blueprint.md` (journey-home table + Data Contract notes). No `blueprint.reapproval-requested` is written this iteration.

### Data-contract additions
- **J-20 — no new canonical value.** Extends the existing *Price / MA / volume series (per ticker, as-of)* row (`GET /api/stocks/{ticker}/bars`) with a **display-only forward extension through the latest seed date + an as-of boundary marker**; the post-D bars/MA are visualization, never a scored value. The blueprint note for that row is updated accordingly.
- **J-21 — no new canonical value, no new endpoint.** Adds a **read-only projection** of the existing stored `forward_returns` value (the per-date scorecard contract) onto the run's sector/theme/cohort rows, keyed by horizon, served by the EXISTING `GET /api/backtest`. Registered as a read-only slice (Attribution-is-read-only discipline) — **not** a second computation and **not** a second endpoint for an existing value.

## OUT OF SCOPE

- **J-22…J-31** — expanded ~500-name universe (J-22), multi-timeframe bars + chart timeframe selector (J-23/J-24), Factor Lab + multi-factor cohorts + regime-conditioning (J-25/J-26/J-27), more detected patterns (J-28), Setup & Pattern event-study lab (J-29), volatility factor family (J-30), end-to-end synthesis (J-31). All deferred to later iterations.
- The Stock-Detail **timeframe selector** (1D/1h/15m/5m, J-24). This iteration's chart change is the **daily** full-path extension only — no timeframe control is added.
- Any change to how scores / buckets / setups / VCP / regime / forward-return aggregates are **computed**. The chart extension is display-only; the leadership returns are a read-only projection of already-stored data.
- Any new top-nav page, the `/research` home, or any nav-skeleton change.
- Any live-data fetch / Data Manager change; any re-seed or universe change.

## DEFINITION OF DONE

- [ ] **J-20 passes via browser-qa-agent:** at a historical as-of D (set via the global switcher, reached by in-app nav), `/stocks/NVDA` (or another listed name) renders the chart **through the latest seed date** with a visible **as-of divider** and a **labelled forward/after-as-of region**; the three scores + setup status + VCP flag + invalidation note are unchanged from the ≤ D snapshot; at the **latest** as-of the chart shows no forward region.
- [ ] **J-21 passes via browser-qa-agent:** on `/backtest` for a historical D with post-bars, **Top Sectors / Top Themes / Ranked Cohort render BELOW Return Attribution**, each with a realized-return column at the selected horizon; **changing the horizon re-points every return column** (and the attribution); a recent date shows **NA** honestly on the columns; there is **no page-local date picker** — the global switcher drives the date.
- [ ] Required-still-passing journeys remain green: **J-05, J-06, J-13, J-14, J-15, J-16, J-18, J-19**.
- [ ] No anti-goal violation introduced — especially **No-lookahead** (chart display carve-out), **Attribution-read-only**, **Exactly-one-date-selector**, **No-fabricated-data**.
- [ ] Unit tests pass; no regressions (see TESTING REQUIREMENTS for the two new test areas).
- [ ] Dev handoff written at `docs/handoffs/goal-i_can_see_the_wealthy_future_forever-iter-6-dev.md`.

## TESTING REQUIREMENTS

- **Browser (full multi-step flows, not single-screenshot surface checks):**
  - **J-20** — set a historical as-of D via the global switcher; open `/stocks/NVDA`; capture a **legible** chart shot showing the **as-of divider** and the **post-D forward region** label; confirm the three score cards + setup + VCP badge match the ≤ D values; then switch to **latest** and confirm no forward region. Capture the defining artifact (the historical-as-of chart with the divider) — not just a page-load shot.
  - **J-21** — on `/backtest` at a historical D with post-bars, confirm the **section order** (scorecard → Return Attribution → the three leadership lists) and a realized-return column on each list; capture a **before/after** of a return column when the **horizon** is switched (the defining proof that one selector re-points the columns); confirm a recent date renders NA; confirm no page-local date dropdown.
  - Drive every date change via the **global switcher with in-app navigation** — the as-of provider is in-memory and resets to Latest on a hard reload (iter-1 lesson). Flush results **incrementally** and reconcile the evidence dir with the results file (iter-4 lesson: a timed-out browser-QA can leave a SKIPPED stub atop real screenshots).
- **Unit/integration** (`cd apps/backend && .venv/bin/python -m pytest tests/ -v`):
  - **(J-20) No-lookahead chart extension.** Assert the bars endpoint / `bars_through_latest` returns bars with date > D for a historical date AND marks D; AND assert the as-of-D **scores/VCP are unchanged by the forward extension** — the stored snapshot row for D (and `score_stocks` / `detect_vcp` output) is byte-identical whether or not post-D bars exist. Cover the **latest** as-of edge (no forward region) and the unknown-ticker / invalid `as_of` edges (still 404 / 4xx).
  - **(J-21) Read-only leadership returns.** Assert the derived sector / theme / cohort realized returns **equal a direct read** of stored `forward_returns` (sector = the ETF's row; theme = mean of member rows; cohort = the symbol's own row) at the horizon, recomputing no return; assert a (row, horizon) with insufficient post-bars yields **null/NA**, not a fabricated number. Assert consistency with the existing scorecard (same stored observations).
- **Error cases:** a recent as-of date with short/no post-bars → NA on the leadership-return columns and the all-NA chart-forward case; the latest as-of → no chart forward region; invalid `as_of` / unknown ticker on the bars endpoint still raises the existing explicit 4xx/404 (never a fabricated row).

## NOTES

**Lessons applied (from `lessons.md`):**
- **iter-0:** verify the **J-18 single-date-control** claim against frontend **source** (`apps/frontend/app/backtest/page.tsx` holds NO date state; the horizon control is a VIEW selector), not just the browser-QA summary. The horizon selector extended here MUST NOT become a second date state, and no `BacktestDatePicker`-style control may reappear.
- **iter-1:** the global as-of lives in an **in-memory provider** (`components/asof-provider.tsx`) — it survives client-side nav but **resets to Latest on a hard reload**. Browser-QA must set the historical date via the switcher and navigate **in-app** for J-20/J-21.
- **iter-2:** on `/backtest` the attribution **distribution mean** is over the FULL observed set and legitimately differs from the scorecard's **top-ranked-cohort mean** — do NOT "reconcile" them. The **new per-row cohort returns (J-21)** are per-**individual-name** realized returns — a different population again from both the distribution mean and the top-N cohort mean — so a reviewer must NOT flag the difference as an inconsistency. Also: a single screenshot proves a surface exists but not the multi-step acceptance; exercise the full flow.
- **iter-3 (process):** full-depth iters in this session have finished **without** a `status.json` / `auditor` handoff (and a QA report once cited a `status.json` not on disk). Downstream agents must verify the two critical seams **in source** — no-lookahead (scores read the snapshot row, not the chart bars endpoint) and read-only (leadership returns derive from stored `forward_returns`) — rather than trust a missing/absent artifact. De-dup evidence (no byte-identical screenshots).
- **iter-4:** browser-QA can time out (exit 124) and leave a **SKIPPED stub** atop a partial set of real screenshots — flush incrementally; convert a journey only if its **defining** step was captured.

**Structural seams (why this is low-risk):**
- **J-20:** scores/setup/VCP come from the immutable snapshot row served by `/api/stocks` + `/api/stocks/{ticker}` (`snapshot_serving`), which read bars ≤ D inside `run_scan`. The chart's `/api/stocks/{ticker}/bars` is a **separate** display series. Extending it forward cannot reach the scoring path — keep it that way (no shared full-path helper feeding `score_stocks`/`detect_vcp`).
- **J-21:** reuse the SAME stored `forward_returns` rows the scorecard + attribution already read; add only a read-only projection keyed by (sector-ETF / theme-members / cohort-symbol). No new endpoint; the global as-of switcher still owns the date; the horizon is the pre-existing VIEW selector lifted to drive the new columns too.

**Depth rationale:** **full** — crosses backend (`prices` + bars endpoint + `forward_testing` + `/api/backtest`) and frontend (two pages), carries two **critical** anti-goal seams (No-lookahead display carve-out; Attribution-read-only / Exactly-one-date-selector), and requires new unit tests beyond browser smoke. This is the first feature iteration of the new wave — the full pipeline lets the coherence-auditor, reviewer, and auditor catch drift early.

**Not GOAL_ACHIEVED after this iter:** J-22…J-31 remain unbuilt; this iteration only opens the two existing-page refinements of the new wave.
