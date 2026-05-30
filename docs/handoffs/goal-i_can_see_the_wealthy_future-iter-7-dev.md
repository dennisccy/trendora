# goal-i_can_see_the_wealthy_future-iter-7 Dev Handoff

**Phase:** goal-i_can_see_the_wealthy_future-iter-7
**Date:** 2026-05-30
**Agent:** developer
**Status:** complete

## What Was Built

J-11 — **Watchlist with persistence**, the last Must-have journey and the product's **first
user-write/mutation surface**.

- **New user-mutable `Watchlist` SQLModel table** (`watchlist`) — INSERT on add, DELETE on remove.
  Stores ONLY `{id, ticker (unique, indexed), reason, created_at, asof_date_added, entry_close}` —
  **never** any score/bucket/setup/invalidation. DB-backed (SQLite via the existing engine), so an
  entry survives a backend restart (the J-11 crux). Docstring states it is NOT a snapshot table and
  NOT an order/position.
- **New router `app/api/watchlist.py`** (registered in `main.py` as `prefix="/api"`):
  - `POST /api/watchlist` `{ticker, reason}` — validates the (upper-cased) ticker against
    `config.universe.symbols` (`404` if unknown — no fabricated row), captures
    `asof_date_added = latest_data_date()` + canonical `entry_close = close_on(...)` **once**,
    rejects a duplicate (`409` — no duplicate row), and returns the enriched GET-shaped row.
    `503` when no price data.
  - `GET /api/watchlist` — every entry (newest first), each **enriched live** by reading that
    ticker's canonical row from `score_stocks(session, latest_data_date(), config)` — the SAME
    computation `GET /api/stocks` serves. Current Leadership/Entry/Risk `{score,bucket}`, setup, and
    invalidation are taken **verbatim** (single source → J-06 on a write surface). `price_since_added
    = close_on(ticker, latest) / entry_close − 1` from the canonical price series (honest `0.0` vs the
    frozen seed; `null`/NA when `entry_close` is null — never fabricated). `503` when no price data.
  - `DELETE /api/watchlist/{id}` — removes the entry; `404` if absent.
- **Frontend `/watchlist`** graduated from the EmptyState stub to a working **Add form**
  (free-text ticker + reason → POST, inline honest error on 404/409/503) + **entries table**
  (ticker links to `/stocks/[ticker]`, date-added, reason, current Leadership/Entry/Risk via
  `ScoreBadge` (Risk `invert`), setup, signed price-since-added in palette pos/neg, invalidation note
  verbatim, per-row Remove → DELETE). EmptyState kept for zero entries; loading + "Backend
  unavailable" states handled. Re-format only — no score/bucket/return computed client-side.
- **`lib/api.ts`** gained the `WatchlistEntry`/`WatchlistResponse` types, a `sendJSON` POST/DELETE
  helper (throws the backend's honest `detail` on non-2xx — never a fabricated success), and
  `fetchWatchlist()` / `addWatchlistEntry(ticker, reason)` / `removeWatchlistEntry(id)` (the first
  **mutating** client calls).

## Files Changed

- `apps/backend/app/models.py` — ADD `Watchlist(table=True)` (user-mutable; not a snapshot/order table).
- `apps/backend/app/api/watchlist.py` — *(new)* POST/GET/DELETE; reads `score_stocks` + `close_on` +
  `latest_data_date`; validates against `config.universe.symbols`. No scoring/threshold literal.
- `apps/backend/main.py` — import `watchlist`; `app.include_router(watchlist.router, prefix="/api")`.
- `apps/backend/tests/test_api_watchlist.py` — *(new)* 9 tests: roundtrip, single-source byte-equality
  vs `/api/stocks`, price-since-added honesty, lowercase canonicalization, unknown→404, duplicate→409
  (no dup row), delete-missing→404, immutability isolation (no snapshot/forward-return write), 503.
- `apps/backend/tests/test_watchlist_persistence.py` — *(new)* 2 tests: the restart crux (file-backed
  SQLite → add → dispose engine → reopen same path → entry read back) + snapshot-isolation on add.
- `apps/backend/tests/test_db.py` — expected-tables set now includes the additive `watchlist` table.
- `apps/frontend/app/watchlist/page.tsx` — stub EmptyState → Add form + entries table.
- `apps/frontend/lib/api.ts` — `WatchlistEntry` type + `sendJSON` + fetch/add/remove client calls.

## Tests Run

- **Backend:** `cd apps/backend && .venv/bin/python -m pytest tests/ -v`
  Result: **179 passed, 0 failed** (0:22:37 — the suite is inherently slow because several existing
  scanner/walk-forward tests build full seeded DBs; nothing new introduced the runtime). Includes the
  11 new watchlist tests and the full J-01–J-10 regression set (scoring/regime/sectors/themes/setups/
  buckets/runs/system-health/forward_testing/scanner) + `test_no_magic_numbers` — all green.
- **Frontend:** `cd apps/frontend && npm run build` → **passed**; all 10 routes compiled/typechecked
  (`/watchlist` 4.57 kB, static).
- **Live smoke test (real seed, port 8835):** booted the backend and ran the full roundtrip —
  empty GET (200, asof 2026-05-28); unknown `ZZZZ` → 404; add `ANET` → 200 (Leadership E/46.61,
  Entry E/57.69, Risk E/39.62, setup Avoid, **price_since_added 0.0**, invalidation "Invalid below the
  50-DMA at $148.38"); lowercase duplicate → 409; **single-source: leadership/entry_quality/risk/setup/
  invalidation all byte-identical to ANET's `/api/stocks` row**; delete → 200; delete-again → 404;
  final entries 0. Backend then killed; runtime DB left with 0 watchlist rows.

## Known Issues

- **None functional.** `price_since_added` is `0.00%` for a just-added entry against the frozen seed
  (latest data date 2026-05-28; no post-add bars, so `entry_close == current close`). Per the spec
  NOTES this is the correct, non-fabricated value — **not** a defect; it becomes the true realized
  change automatically if a live provider advances the seed.
- **Out of scope by design (unchanged):** no order/position/quantity/P&L path (order-path grep is
  clean — the only matches are negative-assertion prose in the docstring); no auth/per-user scoping
  (the watchlist is global, single-user local app); no alerts/groups/tags/CSV/reorder.
- **Pre-existing environment note:** a stale backend from a prior iteration was occupying port 8835
  without the new route; it was killed (by PID, leaving Chrome untouched) so the live smoke test ran
  against the new code. The backend is now stopped, so the browser-QA stage will boot a fresh one with
  this iteration's code.

## Suggested Next Phase

This is the **goal-completing iteration**: with J-11 delivered and J-01–J-10 held green under the full
regression sweep, the next evaluation is positioned to legitimately reach **GOAL_ACHIEVED** (the
goal-evaluator decides, not the developer). If continuing, the deferred nice-to-haves remain available
— a config-editor view (Key Capability #14) and historical per-stock score charts across snapshots
(#15) — both additive and non-blocking. The chronic runner-script gaps (dedicated browser-qa HTTP-000
SKIP/PASS flap; missing `reports/audits/` handoff) are harness, not product, scope.
