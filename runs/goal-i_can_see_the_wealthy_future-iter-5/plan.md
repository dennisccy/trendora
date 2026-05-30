# goal-i_can_see_the_wealthy_future-iter-5 Execution Plan

**Scanner snapshots + Scanner Runs pages (immutable as-of history) — J-07, J-08.**
Adds the persistence spine the product thesis rests on: append-only `scanner_run` snapshots,
served by new `/api/runs` endpoints and two real Scanner Runs pages. First real exercise of the
**Snapshots-immutable** critical anti-goal; lays the no-lookahead, append-only groundwork iter-6 reads.

Frontend Present: yes

## Goal Alignment / Drift Check

- **On-goal, on-roadmap.** Roadmap iter-5 = "Scanner snapshots + Scanner Runs pages (immutability);
  seed a Risk-Off historical run + ≥1 earlier run → J-07, J-08." Spec matches exactly.
- **Blueprint-conformant.** Both pages already live under the **Scanner Runs** IA home
  (`/scanner-runs`, `/scanner-runs/[runId]`); Run Detail is row-reached, not top-nav. **No
  nav-skeleton change → no `blueprint.reapproval-requested`.** Data Contract already attributes the
  "Scanner run snapshot" entity to `app.engine.scanner:run_scan` served by `/api/runs[/{id}]` (blueprint
  line 77 + iter-5 serving note) — this iteration realizes that existing contract row; no new contract value.
- **No drift / no scope creep.** Out-of-scope items (re-pointing live endpoints, walk-forward/forward_returns,
  System Health, Watchlist, scheduler, paper_portfolio, new scoring math) are excluded per spec. No anti-goal
  conflict. Nothing to flag.

## What to Build

**Backend — persistence spine + as-of read path (recomputes NOTHING):**
- Append-only snapshot tables in `app/models.py`: `ScannerRun` (one row per as-of date), `ScannerResult`
  (one row per run×stock), `SectorScoreRow`, `ThemeScoreRow`. Integer PK, ISO dates, JSON text columns;
  Postgres-ready (no SQLite-only SQL). Created by `create_all()` on startup. `paper_portfolio*` and
  `forward_returns` stay **DESIGNED-but-not-created** (forward_returns lands iter-6 as a *separate*
  append-only table keyed to the snapshot — note in a comment, do not create).
- `app/engine/scanner.py`:
  - `run_scan(session, asof, cfg) -> ScannerRun` — calls the existing canonical engine functions **once**
    for `asof` (`score_regime`, `score_sectors`, `score_themes`, `score_stocks`, `setups.summarize_candidates`)
    and persists ONE complete immutable snapshot (run + result/sector/theme child rows) in a single
    transaction. **Idempotent + immutable:** if a run already exists for `asof_date`, return it unchanged —
    never a second run, never an UPDATE.
  - `bootstrap_runs(session_or_engine, cfg)` — ensures a persisted run for every `cfg.scanner.bootstrap_dates`
    **plus** `latest_data_date(session)`. Idempotent (skips already-persisted dates). Reads ONLY the frozen
    seed via `bars_asof` — **never** fetches live data.
- `main.py` lifespan: after `load_seed(...)`, call `bootstrap_runs(...)` on the same process engine.
- `app/api/runs.py` (registered under `/api`):
  - `GET /api/runs` → persisted runs **descending by `asof_date`**; each `{run_id, asof_date, created_at,
    regime:{label,score}, candidate_counts, n_stocks}`.
  - `GET /api/runs/{run_id}` → ONE run's full **stored** snapshot: regime panel (label+score+components),
    breadth (universe-relative), candidate counts, and the **ranked stored stock results** rebuilt from
    `record_json` (the SAME `StockRow` shape the leaderboard uses). **Reads STORED rows — NEVER calls live
    `score_stocks`.** `404` unknown `run_id`; `503` if no price data.
- `config.yaml`: add a `scanner:` section with `bootstrap_dates: ["2022-10-07", "2025-04-04"]` (both verified
  `"Risk-off"`); latest seed date added **programmatically** (not a literal). Add `ScannerCfg` to `config.py`
  (parse dates via `date.fromisoformat`, not literals in calc code). Developer MUST verify each configured
  date's label via the engine and ensure **≥1 is exactly `"Risk-off"`**.

**Frontend — two real pages (re-format only, never recompute):**
- `/scanner-runs`: replace the EmptyState stub with a dense dark table from `GET /api/runs` — as-of date,
  regime badge (label + score, colour-graded; Risk-off clearly labelled), candidate counts
  (Actionable / Breakout-watch / Pullback-watch), stock count; each row links to `/scanner-runs/[runId]`.
  Honest "Backend unavailable" / empty states.
- `/scanner-runs/[runId]`: replace the EmptyState stub with the immutable as-of view from
  `GET /api/runs/{run_id}` — a clear **"Immutable snapshot — as of YYYY-MM-DD"** header, regime panel
  (label + 0–100 + components), breadth (universe-relative), candidate counts, and a ranked stored stock
  table (ticker, Leadership / Entry Quality / Risk as A–E bucket + number, setup status, reason). Reuse the
  existing leaderboard row rendering + `ScoreBadge`. Honest unavailable / 404 states.
- `lib/api.ts`: add `RunSummary`, `RunDetail` types + `fetchRuns()` / `fetchRun(runId)` (throw on non-200 →
  explicit unavailable state). Run-detail stock rows reuse the existing `StockRow` shape.

## Agents Required
- developer: **yes** — backend (models + scanner engine + bootstrap + `/api/runs` + config) **and** frontend
  (two pages + api client). Single developer agent handles both per project convention.
- backend-data: **yes**
- frontend-ux: **yes**

## Files to Create/Modify

**Backend**
- `apps/backend/app/models.py` — add `ScannerRun`, `ScannerResult`, `SectorScoreRow`, `ThemeScoreRow` (append-only)
- `apps/backend/app/engine/scanner.py` *(new)* — `run_scan` (idempotent/immutable) + `bootstrap_runs` (frozen-seed only)
- `apps/backend/app/api/runs.py` *(new)* — `GET /api/runs`, `GET /api/runs/{run_id}` (serve STORED rows)
- `apps/backend/main.py` — register `runs.router`; call `bootstrap_runs(...)` in lifespan after `load_seed`
- `apps/backend/app/config.py` — add `ScannerCfg { bootstrap_dates }` + validation (ISO dates)
- `config.yaml` — add `scanner: { bootstrap_dates: ["2022-10-07", "2025-04-04"] }`

**Backend tests** (`apps/backend/tests/`)
- `test_scanner.py` *(new)* — persists-complete-snapshot; idempotent-and-immutable; no-lookahead;
  latest-run-faithful-to-live; risk-off-run-zero-actionable; runs-are-distinct-as-of-snapshots
- `test_api_runs.py` *(new, or extend test_api_engine)* — `/api/runs` ≥2 desc by date; `/api/runs/{id}` stored
  snapshot; `/api/runs/{unknown}` → 404; no-data → 503
- `test_no_magic_numbers.py` — extend: scanner bootstrap dates come from config; scanner adds no scoring literal
- Update shared config fixtures if `ScannerCfg` becomes required (mirror the iter-4 invalidation-key pattern)

**Frontend**
- `apps/frontend/app/scanner-runs/page.tsx` — real run-list table (replaces stub)
- `apps/frontend/app/scanner-runs/[runId]/page.tsx` — real immutable as-of detail (replaces stub)
- `apps/frontend/lib/api.ts` — `RunSummary`/`RunDetail` types + `fetchRuns()`/`fetchRun(runId)`
- *(optional)* extract the leaderboard row into a shared component if reuse is cleaner than duplication

## Single-Source & Immutability Guardrails (the critical part — get these right)

- **THE iter-2 liability now coming due:** `run_scan`'s run summary MUST **read** breadth + net-new-high/low
  from `score_regime(...)`'s output and candidate counts from `setups.summarize_candidates(score_stocks rows)`.
  It MUST NOT recompute breadth / new-high-low / counts from a second formula or from stored setup statuses.
  This is the exact two-sources-for-one-number trap the single-source gate forbids (lessons iter-2).
- **Faithful copy, not a second computation:** the latest persisted run's per-stock `record_json` must equal
  `score_stocks(latest)["rows"]` and `regime_*` must equal `score_regime(latest)` field-by-field
  (unit-proven). `/api/runs/{id}` serves a stored COPY of canonical output for a historical date.
- **Immutable = append-only + never updated.** Once a `ScannerRun` row exists, no code path UPDATEs it or its
  children. The gitignored DB is ephemeral; on a fresh DB the idempotent bootstrap deterministically
  re-creates identical runs from the frozen seed — that is reproducibility, not mutation.
- **No-lookahead:** every scan reads bars via `bars_asof` (date ≤ asof) only. A run dated D must be unaffected
  by bars dated > D (unit-proven against a DB truncated to ≤ D).
- **Risk-Off gates Actionable:** a `"Risk-off"` bootstrap date stores `regime_label == "Risk-off"` and **0**
  `scanner_results` with `setup_status == "Actionable"` (unit-proven → J-07).
- **Live endpoints NOT re-pointed:** `/api/dashboard`, `/api/stocks`, `/api/stocks/{ticker}`, `/api/sectors`,
  `/api/themes`, `/api/stocks/{ticker}/bars` keep byte-identical on-request paths → J-01–J-06 cannot regress.
- **No fabrication:** unknown `run_id` → 404; no price data → 503; a bootstrap date with insufficient history
  degrades honestly (NA components) and must be surfaced — never silently skipped.

## UI Evolution
- **New user-facing capability:** browse the history of immutable scan snapshots; open any past run and read
  exactly what the scanner said on that date — including a real Risk-Off day with zero Actionable
  (watchlist-only) labels, and confirm an older run's rankings differ from the latest (immutability made visible).
- **New information displayed:** a dated run list (regime badge + candidate counts + stock count per run); a
  per-run regime panel + ranked stored stock table with as-of scores/setups; an explicit "immutable / as-of
  <date>" framing.
- **New user actions:** click a run row → open its immutable detail; navigate back to the list. (No mutation
  actions — snapshots are read-only by design.)
- **UI surface changes:** `/scanner-runs` (list) and `/scanner-runs/[runId]` (detail) graduate from iter-1
  EmptyState stubs to real pages.
- **Navigation changes:** none (Scanner Runs is already in the sidebar; Run Detail is row-reached).

## Visual Requirements
- **Component patterns:** shadcn `Card` for panels; an HTML `<table>` in a `Card` (matching the existing
  `/stocks` leaderboard) for both the run list and the stored stock table; `Badge` for regime label +
  setup status; reuse `ScoreBadge` for A–E bucket + raw number (Risk shown with `invert`); reuse
  `EmptyState` for empty/unavailable.
- **Layout:** persistent sidebar + main content (unchanged shell). List = compact metric table; detail =
  a header strip (immutable/as-of), a regime + breadth + counts panel row, then the ranked stock table.
- **Key visual effects:** colour-graded regime badge (green→red via palette tokens; Risk-off clearly amber/red);
  monospace tabular-nums for ALL numbers (dates, scores, counts); dense dark workstation aesthetic matching
  existing pages. Palette tokens only — no arbitrary hex.
- **States to handle:** loading skeleton; "Backend unavailable" (fetch failure, styled like `/stocks`);
  empty (no runs / run has no rows); 404 (unknown run id) — all explicit, never fabricated.

## Key Test Scenarios (must pass for the phase to be complete)
- **J-07 (browser):** `/scanner-runs` → open the Risk-Off-labelled run → regime panel reads `Risk-off`; scan
  the stock table and confirm **zero "Actionable"** setups (all watchlist-only).
- **J-08 (browser):** `/scanner-runs` lists **≥2 dated runs**; open an older run, note its top tickers/scores;
  open the latest run; confirm the rankings/scores **differ**.
- **Regression sweep (browser):** re-shoot J-01 (dashboard), J-02 (stocks + filters), J-03 (themes),
  J-04 (sectors), J-05 (stock detail chart), J-06 (list==detail consistency) — confirm no regression.
- **Unit/integration:** the six `test_scanner.py` cases above (each a named critical anti-goal proof) +
  `/api/runs` list/detail/404/503 + `test_no_magic_numbers` extension. Backend `pytest` all green;
  frontend `npm run build` typechecks all routes.

## Process & Harness Requirements (fold in — the evaluator asked for these; NOT product code)

> These are pipeline/harness items the spec explicitly assigns to the orchestrator/harness. They are
> **outside the orchestrator's planning-only mandate to *edit*** (framework files in the embedded dev-chain,
> with cross-project blast radius), so they are flagged here for the pipeline/human per `.claude/core.md`
> ("flag conflicts — do not silently skip or silently implement"). See my run summary for the one decision I surfaced.

1. **Browser-QA must own/self-heal its frontend — STRUCTURAL fix (recurred 4× running; a spec note alone has
   failed every time).** Root cause located this iteration: `browser-qa-phase.sh` *already* self-bootstraps
   (auto-start, port reconciliation, stale-kill, 90s cold-start budget), **but** the `browser-qa-agent.md`
   instruction still defaults to **SKIP on HTTP 000**, and — unlike QA mode-2 — the browser-qa step has **no
   `ensure_services_running` pre-retry hook** (`qa-phase.sh` sets `CHAIN_CLAUDE_PRE_RETRY_HOOK=ensure_services_running`;
   browser-qa does not). Fix = make browser-qa re-ensure/own the frontend on retry like QA mode-2 instead of
   precondition-skipping. Until applied, **reconcile journeys from the on-disk evidence PNGs** (QA mode-2
   persists them), not a lone SKIP/PASS verdict.
2. **Emit the audit handoff** at `reports/audits/goal-i_can_see_the_wealthy_future-iter-5-audit.md` — the
   `reports/audits/` directory is **empty**; the audit handoff has been missing **4 full-depth iters running**.
   It is in this iteration's Definition of Done. The audit step must actually run and write its report.
3. **Backend-readiness / startup cost:** `bootstrap_runs` scans ~3 dates × the full pipeline on first boot of
   a fresh DB (~1–2 s/date measured during planning) added to the lifespan **before** the app serves. It is
   idempotent (subsequent boots skip persisted dates; the session-scoped test fixture pays it once). Allow
   extra time in backend-readiness probing so a slow first boot is not misread as "backend down."
4. **Negative file-existence under a flaky harness is not trustworthy** (iter-4 lesson): re-confirm with
   `ls`/Glob/re-read before letting "missing evidence" lower a verdict; don't blind-retry appends. Treat
   demo-narrator Playwright soft-notes as non-gating capture artifacts, not QA failures.

## Assumptions (documented, not blocking)
- `bootstrap_dates` = the two spec-verified Risk-off dates; the latest seed date is appended in code. An
  optional risk-on mid-date is **not** added (spec: optional, not required) to keep the first boot lean.
- `ScannerResult` carries typed columns (`leadership_score`/`_bucket`, `entry_quality_*`, `risk_*`,
  `setup_status`, `rank`, `ticker`/`name`/`sector`) for ordering/immutability checks **plus** `record_json`
  holding the complete `score_stocks` row dict for lossless detail — the detail page rehydrates `StockRow`
  from `record_json`.
- The run-detail page reuses the `/stocks` leaderboard row rendering + `ScoreBadge` rather than inventing a
  second presentation, so a stock reads identically on the live leaderboard and a stored run.
- Developer writes the dev handoff to `docs/handoffs/goal-i_can_see_the_wealthy_future-iter-5-dev.md`.
