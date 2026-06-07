# goal-i_can_see_the_wealthy_future_forever-iter-23 Execution Plan

Target journey **J-35** (Expand-universe job from the Data Manager). Required-still-passing: J-17, J-34,
J-33, J-18, J-22. Full depth — backend (new job kind + provider market-cap capability + screen
orchestration + tests) and frontend (expand option + eligibility gating + screen-result display).
**Additive only** on the existing `/data` page — no new page/route/nav, no blueprint reapproval.

This is the operator-facing path that auto-unblocks J-22. Per the goal's non-halting contract (goal.md
1003–1012) the **machinery is offline-provable with an injected provider**; only the *live* market-cap
expansion outcome is data-gated and is recorded honestly as NA / rate-limited when walled — it MUST NOT
halt the loop, drive STALLED, or veto GOAL_ACHIEVED.

## What to Build

### Backend
- **New `expand` job kind, end-to-end.** Add `"expand"` to `JOB_KINDS` (`data_manager.py:54`) and to
  `JobCreate.kind` (`Literal[..., "expand"]`, `api/data.py:44`). An unknown kind still → 422.
- **Expand orchestration** in `app/engine/data_manager.py` (the canonical home — a new `_EXPAND_KINDS`
  branch inside the existing `_run_job`, NOT a parallel module). The `expand` job:
  - reads the committed pool `apps/backend/data/seed/universe_pool.csv` (548 names) and the config screen
    `config.universe.filters` (`min_market_cap` / `min_dollar_vol` / `min_price`);
  - runs as a **chunked, resumable import on the EXISTING J-34 engine** — reuse `_chunk_plan`,
    `_run_chunked_fetch`, the `RateLimitError`→backoff→graceful `resumable` stop, the durable
    `import_checkpoints` row, and `resume_data_job`. The chunk/backoff tunables come from
    `config.data_manager.import_chunking` (no new config; no magic numbers). The fetch symbol set for an
    expand job is the **pool symbols** (not `all_seed_symbols`) — this is the one substitution in the
    chunk-loop setup.
  - fetches REAL OHLCV via the existing INSERT-new-only `DailyPrice` path (`_existing_dates` idempotency)
    **plus a real market-cap reference** per candidate;
  - applies the screen by **importing the existing pure predicate `screen_universe.screen_reasons(...)`** —
    the single source of the threshold rule. Do NOT re-implement it. (If a clean import from
    `scripts/screen_universe.py` into `app/engine/` is awkward, re-home the *pure* `screen_reasons`
    function into `app/` and have BOTH the script and the engine import the one definition — never two
    copies. `tests/test_universe_screen.py:26` currently imports `from scripts.screen_universe import
    screen_reasons`; keep that import working.)
  - writes only passers to the canonical universe artifact `apps/backend/data/seed/universe.json` + the
    per-symbol price CSVs + a refreshed `meta.json`, and records the **omitted-with-reason** list (a
    fetch-failed / empty-series / threshold-failed / no-market-cap candidate is logged and omitted, NEVER
    fabricated). Match the existing `universe.json` member/omitted record shape written by
    `screen_universe.screen()` (members: symbol/sector/source/market_cap/reference_close/adv_dollar/bars/
    first/last; omitted: symbol/reason).
- **Make the grown universe visible (the J-22 single-source seam — see "Key design decision" below).**
- **Optional market-cap-reference capability** behind the existing `PriceProvider` abstraction, used ONLY
  by the expand path (e.g. an optional `get_market_cap(symbol) -> float | None` capability method on the
  `supports_market_cap` providers; `PriceProvider.get_daily` stays UNCHANGED for every other journey). A
  provider with `supports_market_cap: false` MUST NOT be used for expand.
- **Expand-eligibility gate (backend).** Extend `validate_job_request` to reject an `expand` job whose
  `source` has `supports_market_cap: false` with an explicit typed `ValueError` → 422 (reuse the existing
  `ProviderCatalogEntry.supports_market_cap` flag via `provider_by_id`). Never a silent no-op, never a
  fabricated cap. A needs-key expand source with no env/pasted key is still rejected via the existing J-33
  gate.
- **Surface expand progress + final summary** on `GET /api/data/jobs/{job_id}`: candidates done (chunk
  x/N via the reused J-34 fields), passers count, omitted-with-reason list, failed. Add the needed fields
  to `JobProgress` + `to_dict()` (e.g. `passers`, `omitted` as a bounded list of {symbol, reason}). Record
  the `expand`-kind operational run on the append-only `DataProviderRun` (extend `_persist_run` /
  `_final_summary` for the expand kind). The universe value itself is NOT a new endpoint.
- **Opportunistic carry-over (the single RED test):** fix
  `tests/test_db.py::test_create_all_produces_expected_tables` — add `'import_checkpoints'` to the
  expected-tables set (`... | WATCHLIST_TABLES | {'import_checkpoints'}`). Test-maintenance one-liner.

### Frontend (`/data` only — additive)
- **Add "Expand universe"** to the existing JobForm job-kind `<select>` (`app/data/page.tsx:372-374`,
  the `kind` control with backfill/fetch/both). `DataJobKind` in `lib/api.ts:1065` gains `"expand"`.
- **Eligibility gating (UI).** When the `expand` kind is selected, a source with
  `supports_market_cap: false` (alpha_vantage, stooq — read from the existing `sources` catalog already
  served by `GET /api/data`, field `supports_market_cap`) is shown **disabled with a plain-language
  reason** ("cannot supply market cap — not selectable for expand") in the Import-source `<select>`
  (`app/data/page.tsx:384-390`). The user cannot start an expand on an ineligible source (guard the
  Start button + the selected-source state).
- **Show expand progress + final summary** on the existing job card: candidates processed (reuse the
  `chunk-progress` chunk x/N badge), passers count, and the **omitted-with-reason** list (each omitted
  candidate + reason). Reuse the existing async-job / chunk-progress / resumable affordances — do NOT add
  a parallel job UI. Resume of a rate-limited expand reuses the existing `resume-button` path.
- After a completed expand, the existing **Coverage** `universe-count`
  (`data-testid="universe-count"`, `app/data/page.tsx:269`) reflects the grown universe, and the
  `/methodology` Universe-Selection size matches — both reading the SAME resolved universe.

## Key design decision (flag to developer — load-bearing, document the resolution)

`config.universe.symbols` is loaded **directly from `config.yaml`** (`config.py` `load_config` reads the
YAML; nothing bridges `universe.json` → `config.universe.symbols`). Both the `/data` `universe_count`
(`data_manager.py:103` = `len(cfg.universe.symbols)`) and the `/methodology` Universe-Selection size read
that same `len(cfg.universe.symbols)` — so they are **already single-source**, but the source is the
YAML `symbols` list, which the offline runbook grows by hand-commit, NOT `universe.json`.

Consequence: writing `universe.json` alone will NOT change `universe_count`, so the J-35 DOD browser step
"the Coverage universe-count grows" and the J-22 single-source re-assert would FAIL. The expand job must
make the grown passer set become what `config.universe.symbols` resolves to, WITHOUT introducing a second
universe source or a recompute. **Recommended approach:** have the loaded `Config` resolve
`universe.symbols` from the committed `universe.json` members when present (a thin merge at
`load_config`, falling back to the YAML list when `universe.json` is absent) — so `universe.json` becomes
the single canonical membership artifact that BOTH `universe_count` and `/methodology` already read via
`len(cfg.universe.symbols)`, and the expand write naturally flows through. This keeps ONE source (no
second computation), satisfies J-22's `universe_count == /methodology size == len(config.universe.symbols)`
invariant by construction, and is consistent with the goal's "universe membership comes from the
config-recorded screen" anti-goal. The developer MUST keep config-validation invariants intact (themes /
stock_sectors reference `universe.symbols`; if a grown member lacks a sector/theme mapping that validation
will reject it — the injected-provider test must use pool names that resolve cleanly, or the merge must
preserve the existing mapped set). Whatever resolution is chosen, **record it in the dev handoff** and
prove the three-way equality in a test. If this resolution proves to require touching scoring/theme
config beyond a thin membership merge, prefer the smallest change that makes `universe_count` and
`/methodology` reflect the grown set from one source — and note any residual gap honestly rather than
fabricating a count.

## Agents Required
- backend-data: yes -- new `expand` job kind + chunk-loop reuse over the pool, provider market-cap
  capability behind the abstraction, `screen_reasons` reuse (one definition), eligibility gate (API +
  engine), grown-universe single-source resolution, `universe.json`/CSV/`meta.json` write, progress/summary
  + `DataProviderRun` audit, the `test_db.py` expected-tables fix, and all unit/integration tests.
- frontend-ux: yes -- the Expand-universe job-kind option, source eligibility disabling + reason, and the
  expand screen-result (passers + omitted-with-reason) block on the existing job card; `DataJobKind` adds
  `"expand"`.

## Frontend Present: yes

## Files to Create/Modify
- `apps/backend/app/engine/data_manager.py` -- `expand` in `JOB_KINDS` + `_EXPAND_KINDS`; expand branch in
  `_run_job` (pool symbols → reused `_chunk_plan`/`_run_chunked_fetch` → market-cap fetch → `screen_reasons`
  → write `universe.json`/CSVs/`meta.json`); eligibility check in `validate_job_request`; passers/omitted
  on `JobProgress` + `to_dict()`; expand summary in `_final_summary`/`_persist_run`.
- `apps/backend/app/api/data.py` -- `JobCreate.kind` gains `"expand"`; unknown kind still 422; expand
  eligibility 422 surfaced (reuse the existing `ValueError`→4xx mapping).
- `apps/backend/app/data_providers/base.py` -- optional market-cap-reference capability hook (used only by
  expand); `get_daily` unchanged.
- `apps/backend/app/data_providers/<the supports_market_cap providers>.py` -- implement the market-cap
  reference for yahoo/tiingo/finnhub (whichever are `supports_market_cap: true` and reachable behind the
  abstraction); real data or raise — never fabricate.
- `apps/backend/scripts/screen_universe.py` and/or a new thin `app/` module -- keep ONE definition of the
  pure `screen_reasons`; if re-homed into `app/`, update the script + `tests/test_universe_screen.py` import
  to the single source.
- `apps/backend/app/config.py` -- ONLY if the grown-universe single-source resolution needs it (thin
  `universe.json`-members → `universe.symbols` merge at `load_config`, YAML fallback). No new REQUIRED
  config field if avoidable (reuse `universe.filters` + `data_manager.import_chunking`).
- `apps/frontend/lib/api.ts` -- `DataJobKind` adds `"expand"`; expand progress fields (passers, omitted) on
  `DataJob` if surfaced.
- `apps/frontend/app/data/page.tsx` -- Expand option in the job-kind `<select>`; source-eligibility disabling
  + reason for `supports_market_cap: false`; passers + omitted-with-reason block on the job card.
- `apps/backend/tests/test_data_manager.py` -- expand happy/omit/eligibility/idempotency/no-fabrication
  tests (injected provider).
- `apps/backend/tests/test_api_data.py` -- expand kind accepted; unknown kind 422; expand-over-ineligible
  422; expand job-status shape (passers + omitted).
- `apps/backend/tests/test_db.py` -- add `'import_checkpoints'` to the expected-tables set (the RED fix).
- `apps/backend/tests/test_config.py` (+ `test_config_engine.py`, `test_sectors.py`, `test_themes.py`)
  -- ONLY if a new required config field or a symbols-resolution change is introduced (then update ALL 4
  inline config fixtures — MEMORY config-fixtures-need-new-required-keys).
- `apps/backend/tests/test_universe_screen.py` -- update the `screen_reasons` import path only if re-homed;
  add an engine↔predicate single-source assertion if helpful.
- `docs/handoffs/goal-i_can_see_the_wealthy_future_forever-iter-23-dev.md` (+ a `-frontend.md` for `/data`).

## UI Evolution
- New user-facing capability: the user can **grow the scored universe** from the committed candidate pool
  by running an **Expand-universe** job from the Data Manager — pick a market-cap-capable source, watch the
  chunked/resumable screen run, and read exactly which candidates passed and which were omitted (with the
  reason).
- New information displayed: the per-candidate **screen result** (passers + omitted-with-reason, e.g.
  "market_cap … < …", "price … < …", "adv … < …", "no_market_cap", "fetch_failed"), the grown
  `universe-count`, and the Expand option in the job-kind selector with ineligible sources visibly
  disabled + explained.
- New user actions: select the **Expand universe** job kind; start an expand over a `supports_market_cap`
  source (ineligible sources disabled); **Resume** a rate-limited expand (reuses the existing J-34 Resume —
  no new control).
- UI surface changes: additive within `/data` — a new option in the existing job-kind selector,
  source-eligibility disabling + reason, and a screen-result (passers + omitted-with-reason) block on the
  existing job card. No new page, route, or nav entry.
- Navigation changes: none.

## Visual Requirements
- Component patterns: reuse the existing shadcn `Card` / `Badge` / field + `<select>` styles already on
  `/data` (JobForm, JobProgressPanel). The omitted-with-reason list = a compact list/table inside the job
  card (monospace `tabular-nums` `.num` for counts, matching the chunk/symbol counters). Disabled `<option>`
  for an ineligible source with its plain-language reason shown inline (mirror the existing
  `source-availability` reason line).
- Layout: unchanged `/data` page (form card + job card + coverage panel); the expand additions sit inside
  the existing JobForm and JobProgressPanel — no new layout region.
- Key visual effects: reuse the iter-22 status colour vocabulary — teal `--accent` running, **amber
  `--warn`** for `resumable` (distinct from red `--neg` `failed`); passers in success/neutral, omissions in
  muted/`--warn`. No new effects invented.
- States to handle: loading (existing skeleton); empty (no omissions → no list, or an explicit "all
  candidates passed"); error/ineligible (disabled source + reason; honest **NA / rate-limited** terminal
  state when the live market-cap feed is walled — surfaced like the existing resumable/failed states, never
  a fabricated success).

## Key Test Scenarios

### Browser (J-35, offline-provable with an injected provider — do NOT depend on a live feed)
1. The job-kind selector offers **Expand universe**.
2. With Expand selected, **alpha_vantage / stooq** (`supports_market_cap: false`) are **disabled with a
   reason**; a market-cap-capable source is selectable.
3. Start an expand over the injected provider → the job runs as a chunked import (chunk x/N), completes,
   and the job card shows **passers + omitted-with-reason**; the Coverage `universe-count` grows.
4. (If exercised) a rate-limited expand stops in the **resumable** state and **Resume** continues (reuse
   the J-34 `resume-button` path).
5. Re-confirm **J-18** (exactly one date `<select>` per page — the expand controls add NO date state;
   pool/source/range are job parameters) and **J-22** (the grown universe reads identically on `/data`
   `universe-count` and the `/methodology` Universe-Selection size).
   - Env note (MEMORY browser-qa-dead-shell-next-cache, dev-server-cleanup-by-port): ensure
     `GET /_next/static/chunks/main-app.js` → 200 and the health badge clears before driving UI; do NOT run
     a prod `npm run build` against the live dev `.next`; kill stray dev servers by port. A dead-shell SKIP
     is environmental, not a code FAIL.

### Unit / integration (assert exact values + a failure path)
- **Expand happy path:** an expand over an injected provider (stub returning bars + a market-cap reference
  for K names, omitting/raising for the rest) screens the pool, writes `universe.json` with exactly the
  expected passers, and records the expected omitted-with-reason entries — assert the member set and the
  omission reasons **by value**.
- **Eligibility gate:** an `expand` job whose `source` has `supports_market_cap: false` is rejected (422)
  at BOTH the API and the engine layer — never a silent no-op.
- **Single screen source:** the engine's screen decision is produced by the SAME `screen_reasons` predicate
  the offline runbook + `test_universe_screen.py` use (one definition; a member's pass/omit matches the
  predicate for the same reference values).
- **No fabrication:** a candidate whose injected fetch raises, returns empty, or lacks a market cap is
  omitted with a reason and contributes NO fabricated bar / cap / universe member.
- **Idempotency / immutability:** expand reuses the INSERT-new-only `DailyPrice` guard — a re-run over
  already-stored bars inserts no duplicate; assert NO `scanner_runs` / `scanner_results` / `*_scores` /
  `forward_returns` row is written or mutated (no DB regen).
- **No magic numbers:** the screen thresholds come from `config.universe.filters` and the chunk/backoff
  tunables from `config.data_manager.import_chunking`; a bad/missing config value → `ConfigError` at boot
  (extend the existing validation only if a new field is added).
- **Single-source universe:** after an expand, `GET /api/data` `universe_count` == `GET /api/methodology`
  resolved Universe-Selection size == `len(config.universe.symbols)` resolved from `universe.json` (the
  J-22 single-source invariant, re-asserted by value).
- **Key-safety (carry the iter-21/22 lesson):** any NEW error string the expand path surfaces (per-candidate
  omit reasons, market-cap-fetch errors) is key-safe — assert against a **real** provider error with the
  key in the request URL (`httpx.MockTransport`), and grep the live `GET /api/data/jobs/{id}` response + job
  card + run history for the sentinel; never rely on a sanitized mock.
- **RED fix:** `tests/test_db.py::test_create_all_produces_expected_tables` includes `import_checkpoints`
  and passes.

### Error cases that MUST be rejected
- Unknown job kind → 422.
- `expand` over a `supports_market_cap: false` source → 422 (explicit, API + engine).
- A needs-key expand source with no env/pasted key → explicit rejection (reuse the J-33 path), never a
  silent expand.
- Provider failure mid-expand → explicit omit-with-reason + (on persistent 429) graceful `resumable` stop,
  never a synthesized member.

## Required-still-passing (do not regress)
- **J-17** existing fetch/backfill/both still run (a single-chunk backfill unchanged).
- **J-34** the chunked/resumable engine is REUSED, not forked; Resume still works.
- **J-33** source picker + session-only key unchanged; no key echoed.
- **J-18** exactly one date `<select>` per page; the expand controls add NO date state.
- **J-22** `/api/methodology` Universe-Selection rule + `/api/data` `universe_count` read the SAME resolved
  universe — single source, no second computation.

## Out of scope (excluded — flag if a sub-agent drifts in)
- **J-36 / J-37 / J-38 / J-39** (coverage table, missing-data diagnostic / pull-missing, unified
  Unfinished-imports Retry/Remove, seed-safe Remove-data) — sequenced iter-24+. Do NOT build here.
- **J-23 / J-24** (intraday multi-timeframe) — data-walled, unrelated.
- **Autonomously re-probing J-22/J-23/J-24** as a goal — the expand job's *live* outcome is data-gated and
  non-halting; do NOT add a retry loop or block the iteration on a reachable feed.
- **Any change to scoring / scanner / regime / patterns / buckets / forward_testing / research /
  snapshot_serving** or the `/stocks` · `/backtest` · `/research` pages — expand only adds committed bars
  (INSERT-new-only) + writes `universe.json`; no DB regen of immutable snapshots.
- **Re-implementing the screen threshold rule** — reuse `screen_reasons` (one definition).
- **Persisting any pasted key** — the session-only key stays request-only even for an expand over a
  needs-key source.

## Notes / assumptions
- **GOAL_ACHIEVED is NOT reachable on this landing** (goal grew to 39 journeys; J-36–J-39 + data-walled
  J-22/J-23/J-24 remain). Do NOT declare completion when J-35 lands.
- **Live market-cap egress is externally walled** for this host (Yahoo 429 / Stooq/Tiingo key-gated, per
  the iter-22 handoff + MEMORY data-provider-access-constraints). Build the machinery offline-provable with
  an injected provider; record the live outcome honestly as NA / rate-limited. Do NOT burn the iteration
  reproducing the 429 — the offline-provable steps are the acceptance.
- **Backend suite runtime ~14–20 min** (MEMORY backend-test-suite-runtime); do not run two pytest
  invocations concurrently.
- Spec alignment with `docs/goal.md`: CONFIRMED — J-35 is capability #20/#25 and an explicit Must-have; the
  non-halting live outcome matches goal.md 1003–1012; no contradiction or drift found. The one design
  tension (grown `universe-count` visibility vs `universe.json`-only write) is surfaced above as a
  documented decision for the developer, not a spec contradiction.
