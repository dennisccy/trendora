# Goal Iteration 5 — Scanner snapshots + Scanner Runs (immutable as-of history)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** i_can_see_the_wealthy_future
- **Iteration:** 5
- **Mode:** next
- **Depth:** full
- **Frontend Present:** yes
- **Target journeys:** J-07, J-08
- **Required-still-passing journeys:** J-01, J-02, J-03, J-04, J-05, J-06
- **Anti-goal reminders (verbatim from `docs/goal.md`):**
  - **Snapshots are immutable.** A persisted `scanner_run` and its result rows MUST never be updated or overwritten after creation; forward returns live in a separate append-only table keyed to the snapshot. *(critical — FIRST REAL TEST this iteration)*
  - **No lookahead.** Scoring for a snapshot dated D MUST use only price bars with date ≤ D; forward returns MUST use only bars with date > D. The walk-forward MUST be unit-tested to prove no future bar influences an as-of score. *(critical)*
  - **Single source of truth.** Each of the six canonical scores (and the A–E bucket and setup status) MUST be computed exactly once by the scoring/regime engine and read identically by every page; the API and frontend MUST NOT recompute them. The same symbol's score MUST NOT differ between two views. *(critical)*
  - **Risk-Off must gate Actionable.** When the regime is Risk-Off, the scanner MUST mark zero stocks "Actionable" (watchlist-only). *(critical)*
  - **No fabricated data.** On a data-provider failure the system MUST surface an explicit stale/unavailable state and MUST NOT synthesize prices or scores to force a green journey.
  - **No magic numbers.** Every scoring weight, threshold, decision-rule cutoff, bucket edge, universe entry, and theme definition MUST come from the config file — no such literal in calculation code.
  - **No order/execution path.** No brokerage, order-placement, or capital-deployment code may exist or be reachable; Trendora is research-only. *(critical)*
  - **No secrets in source.** The default seed path requires none; any live-provider key is read only from the environment.
  - **Honest limitations surfaced.** Breadth / new-high-low are universe-relative; small samples labelled with `n`.

## GOAL

A user can open **`/scanner-runs`**, see a history of **multiple dated, immutable scan snapshots**, open the seeded **Risk-Off** run and confirm it shows regime "Risk-off" with **zero Actionable** stocks (J-07), and open an **older** run whose stored rankings/scores **differ from the latest** run — proving each snapshot is a frozen as-of view, not a recomputation of today (J-08).

## BACKGROUND

J-01–J-06 are green; the per-stock/regime/sector/theme engine is complete and serves canonical values on-request from the frozen seed. This iteration adds the **persistence spine** the product's whole thesis rests on: immutable `scanner_run` snapshots. It is the **first real exercise of the Snapshots-immutable critical anti-goal** and lays the no-lookahead, append-only groundwork that iter-6's forward-testing engine will read.

**Keystone feasibility is already verified against the committed seed** (read-only probe during planning, real EOD data — no fabrication):
- The regime engine labels real seed dates **exactly `"Risk-off"`**: e.g. **2025-04-04** (score 6.30) and **2022-10-07** (score 8.34). On both, `score_stocks` + `classify_setup` produce **0 Actionable** (all 122 stocks → `Risk-off-watchlist`) — J-07's gate fires end-to-end.
- Run rankings genuinely differ by date (2025-04-04 leaders KTOS/NOC/PLTR… vs 2022-10-07 HUBB/REGN/AXON… vs latest 2026-05-28 MU/ARM/MRVL…, regime Risk-on 74.32) — J-08's "older differs from latest" is real.

**Design stance (additive, regression-safe — protects the 6 green journeys):** the existing live endpoints (`/api/dashboard`, `/api/stocks`, `/api/sectors`, `/api/themes`, `/api/stocks/{ticker}/bars`) are **NOT re-pointed** this iteration — their data paths stay byte-identical, so J-01–J-06 cannot regress. The scanner **calls the existing canonical engine functions once per as-of date** (it does NOT reimplement any scoring math — honoring the iter-2 coherence lesson: *read the canonical source, never recompute*) and **persists** the result into new append-only snapshot tables. Historical runs are served by **new** `/api/runs` + `/api/runs/{run_id}` endpoints. A unit test proves the latest persisted snapshot is byte-identical to the live engine computation, so the snapshot store is a faithful single-source copy, not a second computation.

**Lessons applied (from `lessons.md`):**
- *iter-2 (critical for this iter):* the scanner's run-summary MUST **read** the canonical breadth (from `score_regime`) and candidate counts (from `setups:summarize_candidates`) — it MUST NOT recompute breadth/new-high-low/counts from setup statuses or any second formula. The whole reason `summarize_run` was re-attributed away from a recompute is to avoid the two-sources-for-one-number trap exactly here.
- *iters 1–4 (browser-qa flap, 4× running):* the dedicated browser-qa SKIPPED on a dead frontend every prior iteration while QA mode-2 self-healed; reconcile journeys from the on-disk evidence PNGs, and the orchestrator MUST make browser-qa own/self-heal its frontend this time (see NOTES).
- *iter-4:* the **audit handoff has been missing 4 full-depth iters running** — it is in this iteration's Definition of Done.

## IN SCOPE

### Backend

- [ ] **Snapshot data model (`app/models.py`) — append-only, never mutated.** Add the immutable snapshot tables (integer PK, engine-URL-from-config; no SQLite-only SQL):
  - `ScannerRun` — one row per (as-of) scan: `id`, `asof_date` (unique), `created_at`, `provider`, `benchmark`, `regime_score`, `regime_label`, `regime_components_json`, `breadth_above_50dma`, `breadth_above_200dma`, `new_high_low_json`, `candidate_counts_json`. (The regime/breadth/counts are **stored copies** of the canonical engine outputs — see serving note.)
  - `ScannerResult` — one row per (run, stock): `id`, `run_id` FK, `ticker`, `name`, `sector`, `leadership_score`, `leadership_bucket`, `entry_quality_score`, `entry_quality_bucket`, `risk_score`, `risk_bucket`, `setup_status`, `rank`, and `record_json` holding the **complete** canonical per-stock record (the exact `score_stocks` row dict: 3 score blocks with components, setup+reason, themes, invalidation). Typed columns for ordering/filtering/immutability checks; `record_json` for lossless detail.
  - `SectorScoreRow` — `id`, `run_id` FK, `ticker`, `kind`, `name`, `score`, `bucket`, `rs_vs_spy`, `dist_from_52w_high_pct`, `trend_label`, `components_json`, `rank` (stored copy of the `SectorRow` shape).
  - `ThemeScoreRow` — `id`, `run_id` FK, `slug`, `name`, `score`, `bucket`, `members_json`, `return_1m`, `return_3m`, `breadth_pct`, `breadth_label`, `trend_label`, `components_json`, `rank` (stored copy of the `ThemeRow` shape).
  - These are created by `SQLModel.metadata.create_all()` on startup (no Alembic). Keep `paper_portfolio*` and `forward_returns` **DESIGNED-but-not-created** (forward_returns lands iter-6 as a SEPARATE append-only table keyed to the snapshot — note it, do not create it).
- [ ] **`app/engine/scanner.py` — `run_scan(session, asof, cfg) -> ScannerRun`.** Calls the existing canonical engine functions **once** for `asof` (`score_regime`, `score_sectors`, `score_themes`, `score_stocks`, `setups:summarize_candidates`) — NO reimplementation of any scoring math — and persists ONE complete immutable snapshot (run + result/sector/theme child rows) in a single transaction. The run summary (regime, breadth, new-high-low, candidate counts) is **read from** those canonical outputs, never recomputed. **Idempotent + immutable:** if a `ScannerRun` already exists for `asof_date`, return it unchanged — never create a second run for that date, never UPDATE/overwrite existing rows.
- [ ] **`bootstrap_runs(session_or_engine, cfg)`** — ensures a persisted run exists for every date in `cfg.scanner.bootstrap_dates` **plus** `latest_data_date(session)` (the "current"/latest run). Idempotent (skips dates already persisted). Reads ONLY the committed frozen seed via `bars_asof` — it MUST NOT fetch live data (re-fetching makes the as-of evidence irreproducible).
- [ ] **`main.py` lifespan** — after `load_seed(...)`, call `bootstrap_runs(...)` (idempotent; uses the same process engine as `load_seed`).
- [ ] **`app/api/runs.py` — two new endpoints** (registered under `/api`):
  - `GET /api/runs` → list of persisted runs, **descending by `asof_date`**, each: `run_id`, `asof_date`, `created_at`, `regime` `{label, score}`, `candidate_counts`, `n_stocks`. (Lets the list show a dated, regime-labelled history so the Risk-Off row is identifiable.)
  - `GET /api/runs/{run_id}` → ONE run's full **stored** snapshot: the run's regime panel (label+score+components, as-of-that-date), breadth (`universe-relative`), candidate counts, and the **ranked stored stock results** (from `record_json` — the same `StockRow` shape the leaderboard uses, so the detail page can reuse the leaderboard row component). MUST read STORED rows for the run's date — NEVER call the live `score_stocks` (that would show today's numbers for an old date — the exact immutability bug J-08 guards against). `404` for an unknown `run_id` (honest — no fabricated run); `503` if no price data.
- [ ] **`config.yaml` — add a `scanner:` section** with `bootstrap_dates: ["2022-10-07", "2025-04-04"]` (both verified `"Risk-off"`; parsed via `date.fromisoformat`, not hard-coded in calc code). The latest seed date is added programmatically (not a literal). The developer MUST verify each configured date's label via the engine and ensure **≥1 is exactly `"Risk-off"`**. (Optional: add 1 verified Risk-on mid-date for a richer history — not required.)

### Frontend

- [ ] **`/scanner-runs` (replace the EmptyState stub)** — a dense, dark table of the runs from `GET /api/runs`: as-of date, **regime badge** (label + score, colour-graded; the Risk-off run clearly labelled), candidate counts (Actionable / Breakout-watch / Pullback-watch), and stock count. Each row links to `/scanner-runs/[runId]`. Honest "Backend unavailable" / empty state on fetch failure (never fabricate).
- [ ] **`/scanner-runs/[runId]` (replace the EmptyState stub)** — the **immutable as-of view** from `GET /api/runs/{run_id}`: a regime panel (label + 0–100 score + components) for that date, breadth (`universe-relative`), candidate counts, and a **ranked stored stock table** (ticker, Leadership / Entry Quality / Risk as A–E bucket + number, setup status, reason). Make it visually unmistakable that this is a *historical, frozen* snapshot dated `asof_date` (e.g. a header "Immutable snapshot — as of YYYY-MM-DD"). Honest unavailable/404 states.
- [ ] **`lib/api.ts`** — add `RunSummary`, `RunDetail` types + `fetchRuns()` / `fetchRun(runId)` fetchers (re-format only; throw on non-200 → explicit unavailable state). The run-detail stock rows reuse the existing `StockRow` shape.

### New user-facing capability

The user can browse the **history of immutable scan snapshots**, open any past run, and read **exactly what the scanner said on that date** — including a real **Risk-Off** day where the scanner correctly produced **zero Actionable / watchlist-only** labels, and confirm older runs differ from the latest (immutability made visible).

### New information displayed

A dated run list (regime badge + candidate counts per run); a per-run regime panel + ranked stored stock table showing as-of scores/setups; an explicit "immutable / as-of <date>" framing.

### New user actions

Click a run row → open its immutable detail; navigate back to the list. (No mutation actions — snapshots are read-only by design.)

### UI surface changes

`/scanner-runs` (list) and `/scanner-runs/[runId]` (detail) graduate from iter-1 EmptyState stubs to real pages. No nav-skeleton change — both already exist in the blueprint Information Architecture under **Scanner Runs** (Run Detail reached from a row, not the top nav).

### Product surface delta

Trendora gains its **evidence-tracking spine**: scans are now persisted as dated, immutable snapshots — the precondition for the forward-testing engine (iter-6) and the visible proof that the scanner's history is honest (no after-the-fact rewriting).

### Blueprint conformance

Both new pages live under the existing **Scanner Runs** Information-Architecture home (`/scanner-runs`, `/scanner-runs/[runId]`) — already in `blueprint.md`. **No nav-skeleton change → no `blueprint.reapproval-requested`.** The blueprint's Data Contract is updated additively (new "Scanner run snapshot" row + iter-5 serving note); see Data-contract additions.

### Data-contract additions

- **NEW entity — "Scanner run snapshot (list + detail)":** computed by **`app.engine.scanner:run_scan`** (which **calls** the canonical engine modules once per as-of date — it does NOT recompute any value), **stored** on the append-only `scanner_runs` + `scanner_results` (+ `sector_scores` + `theme_scores`) tables, **served** by `GET /api/runs` (list) and `GET /api/runs/{run_id}` (detail). To register in `blueprint.md`.
- **No second source for any existing contract value.** Regime / Leadership / Entry Quality / Risk / Sector / Theme / bucket / setup status are still each computed by their ONE canonical module; `/api/runs/{id}` serves a **stored copy** of those exact outputs for a historical run (the blueprint already attributes the regime + per-stock scores' iter-5 serving to `/api/runs/{run_id}`). The live latest-view endpoints are unchanged. A faithful-equality unit test proves the latest stored snapshot == the live engine output (one value, two read paths — never two computations).

## OUT OF SCOPE

- **Do NOT re-point** `/api/dashboard`, `/api/stocks`, `/api/stocks/{ticker}`, `/api/sectors`, `/api/themes`, or `/api/stocks/{ticker}/bars` to read snapshots — keep their live on-request paths byte-identical (protects J-01–J-06). (A future iteration may unify them onto the snapshot store.)
- **No walk-forward / forward-returns / System Health** (J-09, J-10 — iter-6). Do NOT create the `forward_returns` table; only note the design leaves room for it as a separate append-only table.
- **No Watchlist** (J-11 — iter-7).
- No live-provider fetch in the scan/bootstrap path; no scheduler/APScheduler wiring (on-demand bootstrap only).
- No new scoring weights/thresholds; no change to the regime/scoring/setup math.
- No `paper_portfolio*` tables; no order/execution code.

## DEFINITION OF DONE

- [ ] **J-07 passes** via browser-qa: open the seeded Risk-Off run from `/scanner-runs` → `/scanner-runs/[runId]`; its regime label is `Risk-off` and **no stock shows setup "Actionable"** (all watchlist-only).
- [ ] **J-08 passes** via browser-qa: `/scanner-runs` lists **≥2 dated runs**; opening an older run shows stored rankings/scores that **differ** from the latest run's.
- [ ] **Required-still-passing J-01–J-06 remain green** (re-verified, not merely carried — their endpoints are unchanged, so this is a no-regression confirmation).
- [ ] No anti-goal violation introduced — in particular the **Snapshots-immutable** (append-only, never mutated), **No-lookahead** (as-of), **Single-source** (faithful stored copy), and **Risk-Off-gates-Actionable** criticals are unit-proven.
- [ ] Backend unit tests pass (incl. the new snapshot tests below); frontend `npm run build` typechecks all routes; no regressions.
- [ ] Dev handoff written at `docs/handoffs/goal-i_can_see_the_wealthy_future-iter-5-dev.md`.
- [ ] **Audit handoff emitted** at `reports/audits/goal-i_can_see_the_wealthy_future-iter-5-audit.md` (owed 4 prior full-depth iters — see NOTES).

## TESTING REQUIREMENTS

- **Browser (browser-qa-agent):**
  - **J-07** — `/scanner-runs` → open the Risk-Off-labelled run → regime panel reads `Risk-off`; scan the stock table and confirm **zero "Actionable"** setups.
  - **J-08** — `/scanner-runs` shows ≥2 dated rows; open an older run, note its top tickers/scores; return and open the latest run; confirm the rankings/scores differ.
  - **Regression sweep** — re-shoot J-01 (dashboard), J-02 (stock leaderboard + filters), J-03 (themes), J-04 (sectors), J-05 (stock detail), J-06 (list==detail consistency) to confirm no regression.
- **Unit / integration (`apps/backend/tests/`):**
  - `test_scanner.py::test_run_scan_persists_complete_snapshot` — run + result/sector/theme child rows all written for an as-of date.
  - `...::test_run_scan_idempotent_and_immutable` — calling `run_scan` (or `bootstrap_runs`) twice for the same date yields exactly ONE run with the **same `id`/`created_at`** and **byte-identical** child rows (no duplicate, no mutation). *(Snapshots-immutable critical)*
  - `...::test_run_scan_no_lookahead` — a run dated D is unaffected by bars with date > D (e.g. equals the run computed against a DB truncated to ≤ D). *(No-lookahead critical)*
  - `...::test_latest_run_faithful_to_live_computation` — the latest persisted run's per-stock `record_json` == `score_stocks(latest)["rows"]` and `regime_*` == `score_regime(latest)`, field-by-field. *(Single-source critical — proves the stored snapshot is a faithful copy, no divergence)*
  - `...::test_risk_off_run_has_zero_actionable` — `run_scan` on a configured `"Risk-off"` date stores `regime_label == "Risk-off"` and **0** `scanner_results` with `setup_status == "Actionable"`. *(Risk-Off-gates-Actionable critical → J-07 at unit level)*
  - `...::test_runs_are_distinct_as_of_snapshots` — a common ticker's stored Leadership score differs between an older run and the latest run. *(J-08 at unit level)*
  - `test_api`: `GET /api/runs` lists ≥2 runs desc by date; `GET /api/runs/{id}` returns the stored snapshot; `GET /api/runs/{unknown}` → 404.
  - Extend `test_no_magic_numbers.py` — the scanner's bootstrap dates come from `config.scanner.bootstrap_dates` (no date literal in calc code); the scanner introduces no new scoring literal.
- **Error cases:** unknown `run_id` → 404 (no fabricated run); no price data → 503; a bootstrap date with insufficient history must degrade honestly (NA components, never fabricated) — do not silently skip a configured date without surfacing it.

## NOTES

- **Startup cost (flag for orchestrator):** `bootstrap_runs` scans ~3 dates × the full pipeline on first boot of a fresh DB (~1–2s/date measured during planning), added to the lifespan before the app serves. It is idempotent — subsequent boots skip already-persisted dates (and the session-scoped `loaded_engine` test fixture pays it only once). Account for this small extra in backend-readiness probing.
- **Recurring process fixes the evaluator asked to fold in (orchestrator/harness, not product code):**
  1. **Make the dedicated browser-qa own/self-heal its frontend** (start `next dev` if down, like QA mode-2 does) — the SKIP-on-HTTP-000 flap has recurred **4 consecutive iterations**; a spec-level "keep the server up" note did not fix it (iter-3 proved that). This is the structural fix.
  2. **Emit the audit handoff** (`reports/audits/...-iter-5-audit.md`) — missing 4 full-depth iters running.
- **Reconcile journeys from on-disk evidence** (standing lesson): if browser-qa and QA mode-2 disagree (SKIP vs PASS), trust the persisted evidence PNGs on disk, not a lone verdict; under a flaky/queuing tool harness a negative file-existence result is not trustworthy — re-confirm before lowering a verdict.
- **Immutability framing for the reviewer/auditor:** "immutable" here = append-only + never updated after creation. The DB file is gitignored/ephemeral; on a fresh DB the bootstrap deterministically re-creates identical runs from the frozen seed — that is reproducibility, not mutation. The guarantee under test is: once a `ScannerRun` row exists, no code path UPDATEs it or its children.
- **Single-source vigilance:** the one place to get this wrong is `run_scan`'s summary recomputing breadth/new-high-low/candidate-counts from a second formula. It MUST read them from `score_regime` / `setups:summarize_candidates` (the canonical sources) — this is the exact iter-2 coherence liability now coming due.
