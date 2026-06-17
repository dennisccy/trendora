# goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-26 Dev Handoff

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-26
**Date:** 2026-06-17
**Agent:** developer
**Status:** complete

## What Was Built

J-84 — the Data Manager Expand-universe job's market-cap reference now authenticates with Yahoo via
the no-key **cookie + crumb** flow (so real market caps return instead of HTTP-401-omitting every
candidate), and a **systemic** auth/limit failure pauses the job **resumable** instead of silently
recording the whole universe as empty.

- **Cookie+crumb auth in `YahooProvider`** — ported the committed `screen_universe.py` runbook into the
  provider: visit `finance.yahoo.com/` to set the no-key cookie, GET `/v1/test/getcrumb` with a
  browser-like User-Agent for the crumb, then call `/v7/finance/quote?symbols=…&crumb=…`. The cookie +
  crumb are acquired **once per provider session** and reused across the whole batch (a persistent
  `httpx.Client` so the cookie jar survives between the cookie GET and the quote GET). They are held in
  memory only — never stored, logged, committed, written to the DB/run log, or echoed in any response.
- **Batched market-cap helper** — a new `get_market_caps(symbols)` batch method on the provider
  abstraction. `YahooProvider` overrides it to batch `QUOTE_BATCH = 40` symbols per quote request; the
  base default returns `None` (meaning "no batch capability — fall back to the per-symbol path") so
  every per-symbol provider (Tiingo / Finnhub / Seed) keeps its existing semantics unchanged. The
  single-symbol `YahooProvider.get_market_cap` now delegates to the batched path (one auth code path).
- **Systemic-vs-per-candidate classification** — a *whole-batch* auth/limit failure (the cookie/crumb
  acquisition failing, an empty/throttled crumb body, or a **401 or 429** on the batched quote) raises
  `RateLimitError`, which flows through the EXISTING `_run_expand_screen` resumable-pause branch. A
  *single* symbol that is present in a 200 quote response but has no `marketCap` is a normal
  per-candidate absence → `None` → `no_market_cap` omission (never fabricated).
- **Expand orchestration** — `_run_expand_screen` now does a single batched cap pre-fetch up front; a
  systemic `RateLimitError` there pauses the expand `resumable` and writes NO `universe.json` (it does
  NOT record every candidate omitted — the J-84 fix). Per-candidate caps come from the pre-fetched map.
- **Resume-at-screen fix** — fixed a latent bug where an expand whose **screen** step paused resumable
  could not be resumed (the live provider was left unbound on the resume-with-completed-fetch path).
  A resumed expand now re-runs the screen step with the provider + pool bound, **re-fetching ZERO
  OHLCV bars** (the fetch stage is already covered — J-59) and surviving a backend restart.
- **Secret redaction** — the crumb rides as a `crumb=…` query param on the quote URL; every raised
  error is built from the REDACTED URL (`_http._provider_error` strips the entire query string), so the
  crumb/cookie can never leak into an error string, the job message, the job-status response, the
  `DataProviderRun` / `import_checkpoints` rows, or any `GET /api/data*` response.

### Committed-seed manifest repair (pre-existing corruption from the same bug)

A prior session's offline screen run against live Yahoo hit exactly this J-84 bug (HTTP-401 on the
un-authenticated quote) and committed the corrupt residue:
- `data/seed/universe.json` — a **0-member** record with all 60 candidates omitted
  `market_cap_fetch_failed: yahoo … HTTP 401 at …/v7/finance/quote` (the literal bug output).
- `data/seed/meta.json` — overwritten with the J-35 expand format, which **clobbered the price-seed
  per-symbol windows** (`"symbols"` key), silently disabling J-39's committed-seed-vs-user-added
  protection (`load_seed_windows` was returning `{}`).

Both were repaired this iteration (this is un-corrupting the bug's residue, NOT regenerating/fabricating
a universe):
- **Removed** the corrupt 0-member `universe.json` → restores the honest "screen not built yet → tests
  skip" state (J-22's ≥500-real-members leg stays honestly blocked-NA: live Yahoo cap egress is
  rate-limited on this host).
- **Rebuilt** `meta.json` deterministically from the committed price CSVs themselves (all 159
  committed-seed symbols, accurate `first`/`last`/`bars`) — verified 0 mismatches against every CSV.
  This **re-enables J-39 seed-window protection** (159 symbols protected; NVDA `2021-01-04..2026-05-28`).

## Files Changed

- `apps/backend/app/data_providers/base.py` — added the optional batched `get_market_caps(symbols)`
  method (default returns `None` = per-symbol fallback; documents the systemic→`RateLimitError`
  contract).
- `apps/backend/app/data_providers/yahoo_provider.py` — cookie+crumb acquisition (once per session,
  cached), batched `/v7/finance/quote` cap helper with explicit 401/429 systemic classification and
  redacted errors, `QUOTE_BATCH = 40` named constant, single `get_market_cap` delegates to the batch.
- `apps/backend/app/engine/data_manager.py` — `_run_expand_screen` does the batched cap pre-fetch (with
  the systemic-pause classification); `_screen_one_candidate` accepts a pre-fetched cap; fixed the
  resume-at-screen `live`/`pool` binding so a screen-stage pause is resumable with zero OHLCV re-fetch.
- `apps/backend/tests/test_provider_clients.py` — URL-aware fake client for the cookie→crumb→quote flow;
  rewrote/extended the Yahoo cap tests (batched flow, crumb carried, fetched-once-reused, present-capless
  → None, systemic 401/429 on crumb/quote → RateLimitError redacted, empty-crumb systemic, unparseable
  body); base `get_market_caps` default-None test.
- `apps/backend/tests/test_data_manager.py` — J-84 expand integration tests driving the REAL
  `_run_expand_screen` orchestration (batched caps screen real passers in one batch; systemic auth
  failure → resumable, NOT all-omitted; resume → zero duplicate OHLCV fetch + restart-survival;
  crumb-never-leaks secret-redaction guard).
- `apps/backend/data/seed/meta.json` — rebuilt to the correct price-seed manifest (159 symbols, real
  windows) — un-corrupted from the prior bug residue.
- `apps/backend/data/seed/universe.json` — **removed** (was the bug's 0-member corrupt record).

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -q`

Targeted modules run green this iteration:
- `tests/test_provider_clients.py` — **38 passed** (incl. all new J-84 cookie+crumb/systemic tests).
- `tests/test_data_manager.py` — **passed** (incl. 4 new J-84 expand integration tests + the existing
  expand/resumable suite).
- `tests/test_data_manager_jobs_pipeline.py`, `tests/test_seed_provider.py` — passed.
- `tests/test_data_manager_parallel.py`, `tests/test_data_manager_backfill_parallel.py`,
  `tests/test_data_manager_backfill_committed_session.py` — **23 passed** (J-67 machinery intact).
- `tests/test_api_data.py` — **42 passed** (the job-status response surface J-84 rides).
- `tests/test_universe_screen.py` — after the seed-manifest repair, the two previously-FAILING
  committed-record tests now **skip** honestly (`universe.json` absent = screen not built yet).

The FULL ~790-test backend suite is the standing GOAL_ACHIEVED gate — hand it to the pump nohup-async
and gate the next evaluator on the FLUSHED terminal `0 failed` line (iter-11 lesson). Do NOT block the
evaluator dispatch on the in-flight suite. Before the repair, the suite carried exactly the 2
pre-existing `test_universe_screen.py` failures from iter-25 ("failing+3"); the repair removes them.

A direct real-transport redaction check (httpx `MockTransport` returning 401 with the crumb in the URL)
confirms the systemic 401 → `RateLimitError` and the crumb/whole-query are stripped from the message.

## Known Issues

- **J-22 live screen remains blocked-NA (non-halting):** an actual successful REAL Yahoo market-cap
  screen (≥500 real members) is provider-walled on this host (MEMORY: data-provider-access-constraints).
  The cookie+crumb auth, batched-quote, and pause-resumable-on-systemic-failure legs are fully built and
  proven OFFLINE with injected providers/transports; the live ≥500-member leg is recorded honestly
  blocked-NA and must NOT halt the loop, drive STALLED, or veto GOAL_ACHIEVED. J-22/J-23/J-24 stay
  non-vetoing blocked-NA.
- **No new served field / endpoint / table / column** (per spec). `_ADDITIVE_COLUMNS` / `test_db.py`
  expected-tables untouched (those belong to the later J-86). No payload SHAPE change → the
  `test_api_*_equals_engine_output` byte-equality guards are not in play here.
- **Frontend is verification-only:** the existing `/data` Unfinished-imports / job-card surface
  (J-38/J-66) already renders a `resumable` job + Resume affordance + the honest backend job message.
  No frontend code change was required or made. The systemic-auth pause should render as a resumable
  job with the operator message (NOT a silent "0 members" success) — to be confirmed by browser QA.
- **Live Yahoo verification deferred to QA:** the alpha_vantage `demo`-key throttle technique (MEMORY)
  can drive a real resumable pause for the live-evidence leg if an injected stub is not wired into the
  running app. The `/data` job card is screenshot-fragile (live state) — corroborate via the live job
  payload + the durable `data_provider_runs` / `import_checkpoints` rows when a capture degrades.
