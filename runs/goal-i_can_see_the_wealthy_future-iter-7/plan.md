# goal-i_can_see_the_wealthy_future-iter-7 Execution Plan

**Goal-completing iteration.** Delivers **J-11 (Watchlist with persistence)** — the last Must-have
journey — and runs a full J-01–J-10 regression sweep + full-product coherence so the next evaluation
can legitimately reach GOAL_ACHIEVED. The decomposer does NOT declare done; the goal-evaluator does.

**Alignment check (no drift):** J-11 is explicit in `docs/goal.md` (Must-have journeys + Key
Capability #12) and is the iter-7 roadmap row. The blueprint already carries the `/watchlist` IA home
and the Watchlist Data-Contract row (refined additively this iter). This is **additive** — no
nav-skeleton change, so **no `blueprint.reapproval-requested`**.

## What to Build

- **New user-mutable `Watchlist` SQLModel table** — the product's FIRST write surface. Stores ONLY
  `{id, ticker (indexed, unique), reason, created_at, asof_date_added, entry_close}` — **never** any
  score/bucket/setup. Docstring must state it is NOT a snapshot table and never writes
  `scanner_runs`/`scanner_results`/`*_scores`/`forward_returns`.
- **New router `app/api/watchlist.py`** (registered `app.include_router(watchlist.router, prefix="/api")`):
  - `POST /api/watchlist` `{ticker, reason}` → validate ticker ∈ `config.universe.symbols` (else 422/404,
    no fabricated row); capture `asof_date_added = latest_data_date()` and `entry_close = close_on(...)`;
    INSERT; duplicate ticker → **no duplicate row** (409, or idempotent reason-update). Return the
    enriched GET-shaped row.
  - `GET /api/watchlist` → every entry, **enriched live** by READING the canonical per-stock row from
    `score_stocks(session, latest_data_date(), config)` (the SAME computation `/api/stocks` serves):
    current Leadership/Entry/Risk `{score,bucket}`, setup `{status,reason}`, `invalidation` taken
    **verbatim**. `price_since_added = close_on(ticker, latest) / entry_close - 1` from the canonical
    series (NA/honest when `entry_close` null). Plus `date_added`, `reason`, `id`. `503` when no price data.
  - `DELETE /api/watchlist/{id}` → remove; `404` if absent.
- **DB-backed persistence** (SQLite via existing engine/session helpers) — the J-11 crux. No in-memory
  store, no module-level dict.
- **Frontend `/watchlist`** graduates from the EmptyState stub to an Add-form + entries table.
- **`lib/api.ts`** gains the first **mutating** client calls (POST/DELETE).
- **Full J-01–J-10 regression sweep + full-product coherence** (verification, not new code).

## Agents Required

- **backend-data: yes** — new `Watchlist` model, `app/api/watchlist.py` (POST/GET/DELETE), router
  registration, and the unit/integration tests (restart-persistence crux, roundtrip, single-source
  equality, price-since-added honesty, error cases, immutability isolation).
- **frontend-ux: yes** — graduate `watchlist/page.tsx` to a working add-form + table; add the
  `WatchlistEntry` type + `fetchWatchlist`/`addWatchlistEntry`/`removeWatchlistEntry` to `lib/api.ts`.
- developer: yes — single developer agent owns both the backend and frontend work above (TDD).

## Frontend Present

Frontend Present: yes

## Files to Create/Modify

**Backend**
- `apps/backend/app/models.py` — ADD `Watchlist(SQLModel, table=True)` (`__tablename__ = "watchlist"`),
  user-mutable; columns `id` PK, `ticker` indexed+unique, `reason: str`, `created_at: datetime`,
  `asof_date_added: date`, `entry_close: Optional[float]`. Docstring: NOT a snapshot table.
- `apps/backend/app/api/watchlist.py` *(new)* — POST/GET/DELETE; reads `score_stocks` + `close_on` +
  `latest_data_date`; validates against `config.universe.symbols`. Contains **zero** scoring/threshold
  literals (reads everything canonical).
- `apps/backend/main.py` — import `watchlist`; `app.include_router(watchlist.router, prefix="/api")`.
- `apps/backend/tests/test_api_watchlist.py` *(new)* — TestClient roundtrip (add/get/delete),
  single-source equality vs `/api/stocks`, price-since-added honesty, error cases (422/404/409/503),
  immutability isolation (no write to snapshot tables).
- `apps/backend/tests/test_watchlist_persistence.py` *(new — the crux)* — file-backed SQLite restart
  proof: `make_engine("sqlite:///<tmp>")` → `create_db_and_tables(engine1)` → add via `Session(engine1)`
  → `engine1.dispose()` → `make_engine(same path)` → assert entry read back. **NOT `:memory:`.**
- `apps/backend/tests/test_no_magic_numbers.py` — *optional*: the guard's `CALC_FILES` resolve under
  `app/engine/`; `api/watchlist.py` lives in `app/api/`. The durable guarantee is that `watchlist.py`
  holds no scoring/threshold literal — extend the guard only if it can resolve the `app/api/` path
  (see Assumptions).

**Frontend**
- `apps/frontend/app/watchlist/page.tsx` — replace stub: Add control (ticker input/select over universe
  + free-text reason + Add button → POST; inline honest error on 409/422/404/503) and an entries table;
  keep `EmptyState` for zero entries. Re-format only.
- `apps/frontend/lib/api.ts` — ADD `WatchlistEntry` type (merges `StockRow`-style score blocks +
  `date_added`/`reason`/`price_since_added`/`id`) + `fetchWatchlist()`, `addWatchlistEntry(ticker, reason)`,
  `removeWatchlistEntry(id)`. POST/DELETE still throw on non-2xx (explicit error, never fabricated success).

## UI Evolution

- **New user-facing capability:** save stocks to a persistent watchlist with a free-text reason; see
  each saved stock's LIVE canonical scores/setup/invalidation + price-since-added; remove entries; the
  list survives a backend restart.
- **New information displayed:** per entry — date added, the user's reason, current
  Leadership/Entry/Risk (A–E + 0–100), setup status, price-since-added (signed %), invalidation note.
- **New user actions:** Add-to-watchlist (ticker + reason form) and Remove (per-row button) — the
  product's **first write/mutation actions**.
- **UI surface changes:** `/watchlist` goes from stub EmptyState → add-form + entries table. No other
  page changes.
- **Navigation changes:** none — the sidebar already links Watchlist.

## Visual Requirements

- **Component patterns:** reuse `ScoreBadge` (Risk uses `invert`) for the three scores — same as the
  `/stocks` leaderboard (`apps/frontend/app/stocks/page.tsx` is the table-render reference). Ticker cell
  links to `/stocks/[ticker]`. Reuse the existing form/select controls used by the `/stocks` filters for
  the Add form; reuse `EmptyState` (icon `Star`) for the zero-entry state. No new component library.
- **Layout:** dense-dark workstation — `PageHeading` + Add panel + entries table, consistent with
  existing leaderboard pages (sidebar + main content shell already global).
- **Key visual effects:** monospace/tabular `num` for ALL numbers; price-since-added uses palette
  `--pos`/`--neg` for sign; invalidation note rendered verbatim. Palette tokens only — no arbitrary hex.
- **States to handle:** empty (EmptyState), loading (skeleton/consistent with other pages), error
  (inline honest message on add failure; "Backend unavailable" on fetch failure — never a fabricated
  row), success (list refreshes after add/remove).

## Key Test Scenarios

- **J-11 (target, browser):** `/watchlist` empty → add `ANET` reason "ANET — strong leader, watching
  pullback" → row shows date-added, reason, current Leadership/Entry/Risk (A–E + number), setup status,
  a price-since-added figure, an invalidation level → restart backend → entry still present → Remove →
  row disappears. **Two md5-DISTINCT captures required:** (1) entry-present-after-add,
  (2) entry-still-present-after-restart (iter-6 evidence-hygiene lesson — not a reused page shot).
- **Restart persistence (unit, the crux):** file-backed temp SQLite; add → dispose engine → reopen same
  path → entry read back (proves not in-memory).
- **Single-source equality (unit):** for a watchlisted ticker, GET-watchlist current
  score+bucket/setup/invalidation are **byte-identical** to that ticker's `/api/stocks` row (J-06 on the
  write surface).
- **price_since_added honesty (unit):** reads the canonical series; `0.00%` when `entry_close == current
  close` against the frozen seed (correct, not a defect); NA when `entry_close` null — never fabricated.
- **Immutability isolation (unit):** add/remove performs NO UPDATE/INSERT against any
  `scanner_runs`/`scanner_results`/`*_scores`/`forward_returns` row.
- **Error cases:** unknown ticker → 422/404; duplicate → no duplicate row (409 or idempotent); DELETE
  missing → 404; no price data → 503.
- **No-magic-numbers guard** stays green; **order-path grep** stays empty.
- **Full regression:** existing pytest suite green; `npm run build` typechecks all routes; app boots and
  serves `/watchlist` offline on the seed; browser re-confirm J-01–J-10 (hash evidence PNGs; note shared
  pages rather than counting a shared shot as independent proof).

## Anti-goal Guardrails (the live risks this iter — must hold)

1. **Single source (THE risk):** the watchlist both writes (the entry) and displays canonical scores.
   It MUST **read** `score_stocks(latest)` verbatim and **never** store-then-drift or recompute the
   scores/bucket/setup/invalidation. Store only `{ticker, reason, created_at, asof_date_added,
   entry_close}` (parallel to how `ForwardReturn` stores a captured `entry_close` with no score).
2. **No order/execution path:** research save-list only — no quantity, position, cost-basis-as-trade,
   P&L, or buy/sell/order/broker field or verb. An order-path grep MUST stay empty.
3. **No fabricated data:** unknown ticker rejected; price-since-added is an honest number (0.00% vs the
   frozen seed is correct); 503 when no price data — never a synthesized row.
4. **Snapshots immutable:** the new mutable `watchlist` table MUST NOT touch any snapshot/forward-return
   row.
5. **No magic numbers / no secrets:** `watchlist.py` carries no scoring/threshold literal and no secret.
6. **J-01–J-10 must not regress:** `/api/dashboard|stocks|sectors|themes|runs|system-health`, `/bars`,
   and the engine modules stay byte-identical (additive-only changes).

## Assumptions (documented, not blocking)

- **Duplicate-POST behavior:** recommend `409 Conflict` (explicit, simplest); idempotent reason-update is
  equally acceptable per spec. Either way the unique `ticker` constraint guarantees no duplicate row.
- **DELETE key:** recommend `DELETE /api/watchlist/{id}` (matches the `id` carried on the GET row);
  `/{ticker}` is acceptable per spec.
- **price-since-added against the frozen seed (latest `2026-05-28`)** is honestly ~`0.00%` for a
  just-added entry (no post-add bars; `entry_close == current close`). This satisfies "a price-since-added
  figure renders" — it is the correct non-fabricated value, **not** a defect.
- **Restart-persistence test** uses `app.db.make_engine`/`set_engine` + `create_db_and_tables(engine)`
  against a temp **file** path (`tmp_path`), never `:memory:` (which vanishes on reopen).
- **No-magic guard scope:** `test_no_magic_numbers.py` resolves `CALC_FILES` under `app/engine/`;
  `api/watchlist.py` is in `app/api/`. Primary guarantee = keep `watchlist.py` literal-free by reading
  everything canonical. Extending the guard to the `app/api/` path is optional polish, not required.

## Out of Scope / Scope Flags

- Any order/position/portfolio concept; storing or editing scores on a watchlist row; auth/per-user
  scoping/tokens; alerts, groups/tags, CSV export, reordering; the config-editor and historical-score
  nice-to-haves; any change to existing live endpoints/engines or the immutable snapshot/forward-return
  tables.
- **Runner-script harness gaps are NOT product/developer scope** (deliberately not in the DoD per the
  iter-5 lesson that spec/DoD text has no effect there): (1) the dedicated browser-qa HTTP-000 frontend
  SKIP/PASS flap (6 consecutive iters) — durable fix is making browser-qa own/await/self-heal its own
  `next dev`; (2) the missing `reports/audits/` audit handoff — emit from the runner. Until fixed, the
  evaluator reconciles J-11 from on-disk QA evidence PNGs + the unit/API restart-persistence proof +
  direct source reads, exactly as in iters 1–6.

## Definition of Done (from spec)

J-11 passes (add ANET → shows all required fields → survives restart); restart-persistence proven by a
file-backed unit/integration test; single-source guard passes (watchlist current scores == `/api/stocks`
row, byte-identical); J-01–J-10 remain green (full sweep + coherence); no anti-goal violation
(order-path grep clean, no snapshot write, unknown ticker rejected, no new magic number, no secret);
unit tests pass + `npm run build` compiles + app serves `/watchlist` offline on the seed; coherence is
PASS; dev handoff at `docs/handoffs/goal-i_can_see_the_wealthy_future-iter-7-dev.md`.
