# Goal Iteration 23 — Expand-universe job (pool → config screen → members) from the Data Manager

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** i_can_see_the_wealthy_future_forever
- **Iteration:** 23
- **Mode:** normal
- **Depth:** full
- **Frontend Present:** yes
- **Target journeys:** J-35
- **Required-still-passing journeys:** J-17, J-34, J-33, J-18, J-22
- **Anti-goal reminders (verbatim from `docs/goal.md`):**
  - **Universe screen is reproducible & honest.** Universe membership MUST come from the config-recorded screen (no hand-curated list masquerading as a screen); expansion MUST use real committed data only (no fabricated history); breadth and walk-forward labels stay "universe-relative" / survivorship-biased to current membership. *(extends No magic numbers + No fabricated data)*
  - **No fabricated data.** On a data-provider failure the system MUST surface an explicit stale/unavailable state and MUST NOT synthesize prices or scores to force a green journey.
  - **Live fetch is real-data-only.** The Data Manager MUST use the config-selected live provider to fetch real EOD bars; on a provider failure it MUST surface an explicit error and MUST NOT synthesize prices to fill a gap or force a successful run. *(extends No fabricated data)*
  - **Import keys are env-or-session, never persisted.** The import provider catalog and each provider's key-requirement + env-var name MUST come from config (no hardcoded provider list in code); a provider key MUST be read from the environment, or — if the user pastes one into the import UI — held **in memory for that run only**, **never written to disk, the run log, the DB, or any committed file, and never echoed back** in any response. The import's date inputs are **job parameters, not a second date control** (the single global as-of switcher stays the only date selector). *(extends Live fetch is real-data-only + Exactly one date selector)*
  - **No magic numbers.** Every scoring weight, threshold, decision-rule cutoff, bucket edge, universe entry, and theme definition MUST come from the config file — no such literal in calculation code.
  - **Snapshots are immutable.** A persisted `scanner_run` and its result rows MUST never be updated or overwritten after creation; forward returns live in a separate append-only table keyed to the snapshot. *(critical)*
  - **Exactly one date selector.** The frontend MUST NOT maintain a second, independent date state; every date-scoped page (including Backtest) reads the single global as-of control. *(extends Single source of truth)*
  - **No recompute in the read path.** Read endpoints MUST serve canonical values from the persisted immutable snapshot for the resolved as-of date; they MUST NOT recompute scores/returns/buckets per request.

## GOAL

A user can run an **Expand-universe** job from `/data` that reads the committed ~548-name candidate pool and the config screen, fetches real OHLCV + a market-cap reference through the existing chunked/resumable import, and grows the scored universe toward ~400–500 members — surfacing the selection methodology, each member's screen-pass, and every omitted candidate with its reason — while a provider that cannot supply market cap is not selectable and the live-expansion outcome is recorded honestly (NA / rate-limited) when the feed is walled.

## BACKGROUND

The iter-22 evaluator recommended **iter-23 = J-35 (Expand-universe)** — "the operator-facing path that auto-unblocks J-22, now buildable on the iter-22 J-33 (source) + J-34 (chunked/resumable) foundation." J-35 is confirmed unbuilt in source: `JOB_KINDS = ("fetch", "backfill", "both")` (`data_manager.py:54`) has no `expand` kind, and `JobCreate.kind` is `Literal["fetch","backfill","both"]` (`api/data.py:44`). The committed pool `apps/backend/data/seed/universe_pool.csv` (548 names) exists; the canonical screen rule `screen_universe.screen_reasons(...)` is a pure, importable, unit-tested predicate (the single source of the threshold rule); `supports_market_cap` is already declared per-provider in config (yahoo/tiingo/finnhub = true, alpha_vantage/stooq = false) and surfaced by `compute_provider_availability`. This is **full** depth: it crosses backend (new job kind + provider capability + screen orchestration + new tests) and frontend (expand option + eligibility gating + screen-result display), extends the provider abstraction and the universe artifact, and needs real unit/integration coverage beyond browser smoke. Per the goal (lines 1003–1012) and the J-22/J-35 non-halting contract, the job UI + screen logic + eligibility gate are **provable offline with an injected provider**; only the *live* market-cap expansion outcome is data-gated and is recorded NA / rate-limited when walled — it MUST NOT halt the loop, drive STALLED, or veto GOAL_ACHIEVED.

## IN SCOPE

### Backend
- [ ] Add an **`expand` job kind** end-to-end: extend `JOB_KINDS` in `app/engine/data_manager.py` and `JobCreate.kind` (`Literal[..., "expand"]`) in `app/api/data.py`. An unknown kind still → 422.
- [ ] Implement the **expand orchestration** in `app/engine/data_manager.py` (the canonical home; no parallel module). The `expand` job:
  - reads the committed pool `apps/backend/data/seed/universe_pool.csv` (548 names) and the config screen `config.universe.filters` (`min_market_cap`/`min_dollar_vol`/`min_price`);
  - runs as a **chunked, resumable import on the EXISTING J-34 engine** (reuse `_chunk_plan`, the `RateLimitError`→backoff→graceful `resumable` stop, the durable `import_checkpoints` checkpoint, and `resume_data_job`) over the selected source — symbol-batch / date-window / backoff tunables come from `config.data_manager.import_chunking` (No magic numbers);
  - fetches REAL OHLCV via the existing INSERT-new-only `DailyPrice` path (`_existing_dates` idempotency — a committed bar is never overwritten) **plus a real market-cap reference** for each candidate;
  - applies the screen by calling the EXISTING pure predicate `apps/backend/scripts/screen_universe.screen_reasons(reference_close, adv_dollar, market_cap, ...)` — **the single source of the threshold rule; do NOT re-implement it** (import it; if the import path needs a thin re-home into `app/`, move the pure function and keep ONE definition that both the script and the engine import);
  - writes only passers to the canonical universe artifact `apps/backend/data/seed/universe.json` + per-symbol CSVs + a refreshed `meta.json`, and records the **omitted-with-reason** list (a fetch-failed / data-missing / threshold-failed candidate is logged and omitted, **never fabricated**).
- [ ] Add an **optional market-cap-reference capability** to the `supports_market_cap` providers behind the existing `PriceProvider` abstraction (used ONLY by the expand path). `PriceProvider.get_daily` stays unchanged for every other journey. A provider with `supports_market_cap: false` MUST NOT be used for expand.
- [ ] **Expand-eligibility gate (backend):** reject an `expand` job whose `source` has `supports_market_cap: false` with an explicit typed error (422) — never a silent no-op, never a fabricated cap. Reuse the config `ProviderCatalogEntry.supports_market_cap` flag (already present).
- [ ] Surface the expand job's **live progress + final summary** (candidates done, passers, omitted-with-reason, failed) on `GET /api/data/jobs/{job_id}`, and record the `expand`-kind operational run on the append-only `DataProviderRun` audit log (the universe value itself is NOT a new endpoint — see Data-contract).
- [ ] **Opportunistic (carry-over nit from iter-22):** fix the stale `tests/test_db.py::test_create_all_produces_expected_tables` expected-tables set — add `'import_checkpoints'` (`... | WATCHLIST_TABLES | {'import_checkpoints'}`). This is the single RED test in the otherwise-green suite; a test-maintenance one-liner, not a product defect.

### Frontend
- [ ] Add an **Expand universe** option to the existing `/data` JobForm job-kind selector (`apps/frontend/app/data/page.tsx` — the `kind` control already exists with fetch/backfill/both; `DataJobKind` in `lib/api.ts` gains `"expand"`).
- [ ] **Eligibility gating (UI):** when the `expand` kind is selected, a source with `supports_market_cap: false` (alpha_vantage, stooq — read from the existing `sources` catalog field already served by `GET /api/data`) is shown **disabled with a plain-language reason** ("cannot supply market cap — not selectable for expand"); the user cannot start an expand job on an ineligible source.
- [ ] Show the **expand job's live progress + final summary** on the existing job card: candidates processed (chunk x/N via the reused J-34 chunk-progress UI), passers count, and the **omitted-with-reason** list (each omitted candidate + its reason). Reuse the existing async-job / chunk-progress / resumable affordances — do NOT add a parallel job UI.
- [ ] After a completed expand, the existing **Coverage** panel's `universe-count` (`data-testid="universe-count"`) reflects the grown universe, and the **Universe-Selection methodology** (served by `GET /api/methodology`) matches config — both reading the SAME resolved universe (no second universe display).

### New user-facing capability
The user can grow the scored universe from the committed candidate pool by running an Expand-universe job from the Data Manager — picking a market-cap-capable source, watching the chunked/resumable screen run, and reading exactly which candidates passed and which were omitted (with the reason).

### New information displayed
The per-candidate screen result — passers and **omitted-with-reason** (e.g. "market_cap … < …", "price … < …", "adv … < …", "no_market_cap", "fetch_failed") — plus the grown `universe-count`; the Expand option in the job-kind selector with ineligible sources visibly disabled and explained.

### New user actions
- Select the **Expand universe** job kind in the `/data` JobForm.
- Start an expand job over a `supports_market_cap` source (ineligible sources are disabled).
- Resume a rate-limited expand job (reuses the existing J-34 Resume affordance — no new control).

### UI surface changes
Additive within the existing `/data` page: a new option in the existing job-kind selector, source-eligibility disabling + reason, and a screen-result (passers + omitted-with-reason) block on the existing job card. No new page, route, or nav entry.

### Product surface delta
The Data Manager becomes the operator-facing path to expand the universe (the J-22 auto-unblock): the dataset's scored breadth can grow from the UI via the config screen, with full transparency into selection and omission, instead of only the offline dev runbook.

### Blueprint conformance
Lives entirely under the **existing approved `/data` (Data Manager)** Information-Architecture home (J-17) — additive only, **no nav-skeleton change, no `blueprint.reapproval-requested` marker** (confirmed absent). The blueprint's iter-23 nav note + J-35 Data-Contract row are already registered.

### Data-contract additions
The `expand` job introduces **NO new way to compute the J-22 universe value** — `universe.json` is the SAME canonical universe artifact already registered (Data-Contract J-22 row); `GET /api/methodology` (rule + thresholds + resolved size) and `GET /api/data` (`universe_count`) keep serving the SAME resolved universe (single source, no recompute). The screen rule stays the single, pre-existing `screen_universe.screen_reasons` predicate — never duplicated. The **NEW descriptive job-control values** registered in `blueprint.md` (J-35 Data-Contract row, this iteration): the expand job's per-candidate **screen result** (passers + omitted-with-reason, on the job's live progress / final summary) and the `expand`-kind operational run row on the append-only `DataProviderRun` — neither is a recompute of any canonical score/return/bucket. The optional provider **market-cap-reference capability** is a new fetch capability behind the existing abstraction, used only by the expand path.

## OUT OF SCOPE

- **J-36 / J-37 / J-38 / J-39** (the four post-iter-21 re-scope Data-Manager Must-haves) — do NOT build the coverage table, the missing-data diagnostic / pull-missing, the unified Unfinished-imports Retry/Remove, or the seed-safe Remove-data cascade here. They are sequenced for iter-24+ (smallest/most-deterministic first: J-36, J-39, J-38, J-37).
- **J-23 / J-24** (intraday multi-timeframe) — data-walled, unrelated.
- **Autonomously re-probing J-22 / J-23 / J-24** as a goal — the expand job's *live* outcome is data-gated/non-halting; do NOT add a retry loop or block the iteration on a reachable feed.
- **Any change to scoring / scanner / regime / patterns / buckets / forward_testing / research / snapshot_serving** or the `/stocks` · `/backtest` · `/research` pages — the expand job only adds committed bars (INSERT-new-only) + writes `universe.json`; no DB regen of existing immutable snapshots.
- **Re-implementing the screen threshold rule** — reuse `screen_universe.screen_reasons` (one definition).
- **Persisting any pasted key** — the session-only key stays request-only (the J-33/J-34 contract), even for an expand job over a needs-key source.

## DEFINITION OF DONE

- [ ] J-35 passes via browser-qa-agent at its **offline-provable** steps (the `expand` job kind selectable; an ineligible `supports_market_cap: false` source disabled with a reason; an expand run over an **injected provider** screens the pool and shows passers + omitted-with-reason + a grown `universe-count`); the **live market-cap-expansion outcome** is recorded honestly as NA / rate-limited if every provider is walled (non-halting — NOT a FAIL).
- [ ] Required-still-passing journeys remain green: **J-17** (existing fetch/backfill/both still run; a single-chunk backfill unchanged), **J-34** (the chunked/resumable engine is reused, not forked; Resume still works), **J-33** (source picker + session-only key unchanged; no key echoed), **J-18** (exactly one date `<select>` per page; the expand controls add NO date state — pool/source/range are job parameters), **J-22** (`/api/methodology` Universe-Selection rule + `/api/data` `universe_count` read the SAME resolved universe — single source, no second computation).
- [ ] No anti-goal violation introduced — in particular: no fabricated cap/price/bar (omit + log on failure); screen rule is the single `screen_reasons` source; an ineligible source is rejected (UI + backend), never silently expanded; thresholds + chunk/backoff tunables from config (No magic numbers); only `DailyPrice`/`universe.json`/CSVs written (immutable snapshots untouched, no DB regen).
- [ ] Unit + integration tests pass; no regressions. Backend suite green (including the fixed `test_db.py` expected-tables set).
- [ ] Dev handoff written at `docs/handoffs/goal-i_can_see_the_wealthy_future_forever-iter-23-dev.md` (+ a frontend handoff for the `/data` changes).

## TESTING REQUIREMENTS

- **Browser (by ID):** **J-35** — drive these offline-provable flows on `/data` with an injected provider (do NOT depend on a live feed):
  1. The job-kind selector offers **Expand universe**.
  2. With Expand selected, **alpha_vantage / stooq** (`supports_market_cap: false`) are **disabled with a reason**; a market-cap-capable source is selectable.
  3. Start an expand over the injected provider → the job runs as a chunked import (chunk x/N), completes, and the job card shows **passers + omitted-with-reason**; the Coverage `universe-count` grows.
  4. (If exercised) a rate-limited expand stops in the **resumable** state and **Resume** continues (reuse the J-34 path).
  5. Re-confirm **J-18** (exactly one date `<select>` per page — the expand controls add none) and **J-22** (the grown universe reads identically on `/data` `universe-count` and the `/methodology` Universe-Selection size).
  - Per the recurring environmental notes (MEMORY `browser-qa-dead-shell-next-cache`, `dev-server-cleanup-by-port`): ensure `GET /_next/static/chunks/main-app.js` → 200 and the health badge clears before driving UI; do NOT run a prod `npm run build` against the live dev `.next`; kill stray dev servers by port, never a broad `pkill`. A dead-shell SKIP is environmental, not a code FAIL.
- **Unit / integration (assert exact values, cover a failure path):**
  - `expand` job kind: a job over an **injected provider** (stub returning bars + a market-cap reference for K names, omitting/raising for the rest) screens the pool, writes `universe.json` with exactly the expected passers, and records the expected omitted-with-reason entries — assert the member set and the omission reasons by value.
  - **Eligibility gate:** an `expand` job whose `source` has `supports_market_cap: false` is rejected (422) at both the API and engine layer — never a silent no-op.
  - **Single screen source:** the engine's screen decision is produced by the SAME `screen_reasons` predicate the offline runbook + `test_universe_screen.py` use (assert one definition; a member's pass/omit matches the predicate for the same reference values).
  - **No fabrication:** a candidate whose injected fetch raises, returns empty, or lacks a market cap is **omitted with a reason** and contributes **no fabricated bar / cap / universe member**.
  - **Idempotency / immutability:** expand reuses the INSERT-new-only `DailyPrice` guard — a re-run over already-stored bars inserts no duplicate; no `scanner_runs`/`scanner_results`/`*_scores`/`forward_returns` row is written or mutated (no DB regen).
  - **No magic numbers:** the screen thresholds come from `config.universe.filters` and the chunk/backoff tunables from `config.data_manager.import_chunking`; a bad/missing config value → `ConfigError` at boot (extend the existing validation if needed).
  - **Single-source universe:** after an expand, `GET /api/data` `universe_count` == `GET /api/methodology` resolved universe size == `len(config.universe.symbols)` resolved from `universe.json` (the J-22 single-source invariant, re-asserted).
  - Fix + assert green: `tests/test_db.py::test_create_all_produces_expected_tables` includes `import_checkpoints`.
- **Error cases that must be rejected:** unknown job kind → 422; `expand` over a `supports_market_cap: false` source → 422 (explicit); a needs-key expand source with no env/pasted key → explicit rejection (reuse the J-33 path), never a silent expand; provider failure mid-expand → explicit omit-with-reason + (on persistent 429) graceful `resumable` stop, never a synthesized member.

## NOTES

- **Lesson — iter-7/iter-8 (probe-and-gate + auto-heal; data-wall is not a session stall).** The expand job's *live* market-cap fetch is the same externally-walled egress that gated J-22 (Yahoo 429, re-confirmed pointless iters 7–8). Build the **machinery to be offline-provable** (injected provider) and the **live outcome to auto-heal** — separate the committed/testable screen+job logic from the data step and gate the live result honestly (NA / rate-limited). Do NOT burn the iteration reproducing the 429; the offline-provable steps are the acceptance, the live expansion is non-halting. (Applies-to match: any iter performing a new bulk external fetch / an environmentally-blocked deliverable.)
- **Lesson — iter-21/iter-22 (real-error key-leak; key-in-URL).** The expand job threads the same session-only key through the same `_http.py` path. The iter-22 fix (redacted-URL error message + defense-in-depth scrub) covers it; any NEW error string the expand path surfaces (per-candidate omit reasons, market-cap-fetch errors) MUST also be key-safe — assert against a **real** provider error (key-in-URL via `httpx.MockTransport`), grep the live `GET /api/data/jobs/{id}` response + job card + run history for the sentinel, never a sanitized mock. (Applies-to: any iter extending an external HTTP client carrying a credential.)
- **Lesson — iter-13 (config-fixtures-need-new-required-keys, MEMORY).** If the expand path adds any new required config field (e.g. a market-cap source detail), add it to ALL inline test config dicts (MINIMAL_VALID, VALID, test_sectors, test_themes), not just the obvious two — a missing required key → `ValidationError` across the suite. Prefer reusing the existing `config.universe.filters` + `data_manager` blocks (already populated) to avoid new required keys.
- **Lesson — iter-20 (re-scope finalization trap).** GOAL_ACHIEVED is NOT reachable on this landing — the goal grew to 39 journeys; J-36/J-37/J-38/J-39 + the data-walled J-22/J-23/J-24 remain. Do NOT declare completion when J-35 lands; the evaluator continues to J-36+.
- **Process — full-depth audit gap (recurring iters 2/3/6/9-22).** Expect no `-audit.md` handoff and `status.json` at the PHASE-namespace path `runs/goal-i_can_see_the_wealthy_future_forever-iter-23/status.json` (not under `runs/goal-session-.../iter-23/`). The evaluator should verify critical seams in source, de-dup evidence by sha256, and read the authoritative `ui-test-results.md` directly rather than trusting a QA summary.
- **Architectural decision recorded (the iter-22 eval asked the decomposer to determine the market-cap path up front):** no provider currently exposes market cap (`PriceProvider` has only `get_daily`); the committed `screen_universe.py` fetches caps via Yahoo's quote API. The expand path therefore adds an **optional market-cap-reference capability** to the `supports_market_cap` providers behind the same abstraction, used only by expand, and gates expand to those sources — keeping the screen rule (`screen_reasons`) as the single source. The expand job WRITES committed bars + `universe.json` (no immutable-snapshot mutation, no DB regen), so the 31 carried journeys stay orthogonal and cannot regress.
