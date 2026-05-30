# Goal Iteration 7 — Watchlist with persistence (J-11) + goal-completing 11-journey sweep

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** i_can_see_the_wealthy_future
- **Iteration:** 7
- **Mode:** next
- **Depth:** full
- **Frontend Present:** yes
- **Target journeys:** J-11
- **Required-still-passing journeys:** J-01, J-02, J-03, J-04, J-05, J-06, J-07, J-08, J-09, J-10
- **Anti-goal reminders (verbatim from `docs/goal.md`; the starred ones are the live risks this iter):**
  - ***Single source of truth.** Each of the six canonical scores (and the A–E bucket and setup status) MUST be computed exactly once by the scoring/regime engine and read identically by every page; the API and frontend MUST NOT recompute them. The same symbol's score MUST NOT differ between two views. (critical)* — **the watchlist is the first write surface that DISPLAYS canonical scores; it MUST READ them, never recompute or store-then-drift.**
  - ***No order/execution path.** No brokerage, order-placement, or capital-deployment code may exist or be reachable; Trendora is research-only. (critical)* — **a "watchlist" with an Add button is the closest the product comes to a portfolio; it MUST stay a research save-list — no quantity, position, entry-as-a-trade, P&L, or order verb.**
  - ***No fabricated data.** On a data-provider failure the system MUST surface an explicit stale/unavailable state and MUST NOT synthesize prices or scores to force a green journey.* — **unknown ticker → explicit rejection; price-since-added is an honest number (0.00% against the frozen seed is correct, not a defect).**
  - ***Snapshots are immutable.** A persisted `scanner_run` and its result rows MUST never be updated or overwritten after creation; forward returns live in a separate append-only table keyed to the snapshot. (critical)* — **the new mutable `watchlist` table MUST NOT touch any snapshot row.**
  - *No magic numbers.* Every scoring weight, threshold, decision-rule cutoff, bucket edge, universe entry, and theme definition MUST come from the config file — no such literal in calculation code.
  - *No lookahead.* Scoring for a snapshot dated D MUST use only price bars with date ≤ D; forward returns MUST use only bars with date > D. (critical)
  - *No secrets in source.* No hard-coded credentials, API keys, or tokens anywhere.
  - *Risk-Off must gate Actionable.* When the regime is Risk-Off, the scanner MUST mark zero stocks "Actionable" (watchlist-only). (critical)
  - *Scores must be explainable.* Every displayed score MUST carry its named component breakdown — no bare numbers.
  - *Honest limitations surfaced.* Breadth/new-high-low are universe-relative; walk-forward evidence carries survivorship bias.
  - *The frontend MUST NOT store auth tokens in `localStorage`* (no auth in this version).

## GOAL

A user can open `/watchlist`, add a stock with a free-text reason, and see it listed with its date-added, reason, **current** Leadership / Entry Quality / Risk (A–E + number) and setup status, a price-since-added figure, and an invalidation level — and the entry **survives a backend restart** because it is stored in the database. This is the last Must-have journey; delivering it (with J-01–J-10 held green) positions the next evaluation to legitimately reach GOAL_ACHIEVED.

## BACKGROUND

Nine of eleven journeys pass; only **J-11 (Watchlist with persistence)** remains (journey-history). The evaluator's iter-6 recommendation is explicit: add a persisted `watchlist` table + `POST`/`GET`/`DELETE /api/watchlist` (the product's **first user-write/mutation surface**), each entry carrying date-added, reason, current scores+setup (READ canonical — single source), price-since-added, and an invalidation level, and it **MUST survive a backend restart** (DB-backed, not in-memory). The blueprint already lists a `/watchlist` nav home and a Watchlist Data-Contract row, so this is **additive** — no nav-skeleton change. Full depth is warranted: it changes the data model, introduces the first mutation path, crosses backend+frontend, and is the goal-completing iteration (pair it with a full 11-journey regression sweep + full-product coherence).

**Lessons applied (from `lessons.md`):**
- *iter-2 (single-source on a new path):* a new code path that **displays** a value the Data Contract attributes to an existing engine MUST **read** the canonical source, never recompute. The watchlist's "current" scores/bucket/setup/invalidation read the SAME `score_stocks(asof=latest)` row that `/api/stocks` serves (→ J-06 extended to a write surface). Do not store the scores on the watchlist row (a stored copy would silently become a second, drifting source).
- *iter-6 (evidence hygiene):* distinct journey-named PNGs are not guaranteed distinct. J-11 has two crux sub-states — *entry present after add* and *entry still present after restart* — which MUST be captured as **two distinct (md5-distinct) screenshots**, not one reused page shot.
- *iter-1→iter-5 (runner-level gaps are NOT product scope):* the chronic dedicated-browser-qa HTTP-000 SKIP/PASS flap and the missing audit handoff are runner-script issues; spec/DoD text has demonstrably no effect, so they are deliberately **not** in this DoD (see NOTES). The evaluator must be ready to reconcile J-11 from on-disk evidence + the unit/API restart-persistence proof + direct source reads if the dedicated browser-qa SKIPs a 7th time.

## IN SCOPE

### Backend
- [ ] **New mutable `Watchlist` SQLModel table** in `apps/backend/app/models.py`. Store ONLY user/identity + entry-price-capture columns — **never** the scores:
  - `id` (PK), `ticker` (indexed, **unique** — one entry per ticker), `reason` (free text), `created_at` (wall-clock datetime — the "date added"), `asof_date_added` (the `latest_data_date()` at add time), `entry_close` (canonical close on `asof_date_added`, captured once via `app.engine.prices:close_on`).
  - This table is **user-mutable (INSERT + DELETE)** and is explicitly NOT a snapshot table — it MUST NOT be confused with, or write to, the append-only `scanner_runs`/`scanner_results`/`*_scores`/`forward_returns` tables (Snapshots-immutable anti-goal). Add a docstring stating this.
- [ ] **New router `apps/backend/app/api/watchlist.py`** (registered in `main.py` as `app.include_router(watchlist.router, prefix="/api")`):
  - `POST /api/watchlist` — body `{ "ticker": str, "reason": str }`. Validate `ticker` is in `config.universe.symbols` → `422`/`404` for an unknown ticker (no fabricated row). Capture `asof_date_added = latest_data_date()` and `entry_close = close_on(ticker, asof_date_added)`. Insert. Adding an already-watchlisted ticker MUST NOT create a duplicate (return `409`, or idempotently update the reason — developer's choice, but no duplicate row). Return the enriched entry (same shape as a GET row).
  - `GET /api/watchlist` — return every entry, each **enriched at serve time** by READING the canonical per-stock row from `score_stocks(session, latest_data_date(), config)` (the **same** computation `/api/stocks` serves) for the entry's ticker — its current Leadership/Entry/Risk `{score, bucket}`, setup `{status, reason}`, and `invalidation` are taken **verbatim** from that row (single source → J-06). Compute `price_since_added = close_on(ticker, latest_data_date()) / entry_close - 1` from the canonical price series (NA/honest when `entry_close` is null — never fabricated). Include `date_added`, `reason`. `503` when no price data exists.
  - `DELETE /api/watchlist/{id}` (or `/api/watchlist/{ticker}`) — remove the entry; `404` if absent.
- [ ] **Persistence is DB-backed** (SQLite via the existing engine/session helpers) — the J-11 crux. No in-memory store, no module-level dict.

### Frontend
- [ ] **Graduate `apps/frontend/app/watchlist/page.tsx`** from the EmptyState stub to a working page (dense-dark workstation style, reuse existing components):
  - An **Add** control: a ticker input (free text, upper-cased, or a select over the universe) + a free-text **reason** field + an **Add** button → `POST /api/watchlist`; on success the list refreshes; on `409`/`422`/`404` show an inline, honest error (no fabricated success).
  - A **table** of entries: ticker (links to `/stocks/[ticker]`), **date added**, **reason**, current **Leadership / Entry Quality / Risk** via the existing `ScoreBadge` (Risk uses `invert`), **setup status**, **price-since-added** (monospace `num`, signed %, palette pos/neg colour), and the **invalidation** note (rendered verbatim). A **Remove** button per row → `DELETE`.
  - Keep the existing **EmptyState** for the zero-entry case.
  - **Re-format only** — no score/bucket/return computed client-side.
- [ ] **`apps/frontend/lib/api.ts`:** add `WatchlistEntry` type + `fetchWatchlist()`, `addWatchlistEntry(ticker, reason)`, `removeWatchlistEntry(id|ticker)` (the first **mutating** client calls — POST/DELETE; still throw on non-2xx so the UI renders an explicit error, never a fabricated success).

### New user-facing capability
The user can save stocks to a persistent watchlist with their own reason, see each saved stock's live canonical scores/setup/invalidation and price-since-added at a glance, remove entries, and trust that the list is still there after the backend restarts.

### New information displayed
Per watchlist entry: date added, the user's reason, current Leadership/Entry/Risk (A–E + 0–100), setup status, price-since-added %, and the invalidation level/note — all server-computed.

### New user actions
Add-to-watchlist (ticker + reason form), Remove-from-watchlist (per-row button). These are the product's first write/mutation actions.

### UI surface changes
`/watchlist` graduates from a stub EmptyState to an add-form + entries table. No other page changes. Sidebar already links Watchlist (no nav change).

### Product surface delta
The product gains its first persisted, user-authored surface — a research save-list that foregrounds *current* evidence (scores, setup, invalidation) and an honest price-since-added, consistent with the "earn trust, discourage impulsive buying" mood. It remains decision-support: a save-list, never a position or order.

### Blueprint conformance
Lives under the existing **Watchlist** Information-Architecture home (`/watchlist`, already in the sidebar skeleton) — **no nav-skeleton change, so no `blueprint.reapproval-requested`**. The Watchlist Data-Contract row already exists and is refined (additively) this iter to name its exact canonical sources.

### Data-contract additions
No NEW canonical value is introduced. The watchlist **reads existing** Data-Contract values: current Leadership/Entry/Risk + bucket + setup + invalidation from `app.engine.scoring:score_stocks` (the same per-stock row as `GET /api/stocks`), served via `GET /api/watchlist`. `price_since_added` is a per-entry display derived from the canonical price series (`app.engine.prices:close_on`) — not one of the six canonical scores and not recomputed in the UI. The existing Watchlist row in `blueprint.md` is refined to state these sources (additive clarification; registered below).

## OUT OF SCOPE

- **Any order/position/portfolio concept** — no share quantity, cost basis as a "position", realized/unrealized P&L, buy/sell/order/broker verbs or fields. price-since-added is an *informational* price change only (No order/execution path, critical).
- **Storing or editing the scores on a watchlist row** — current scores/bucket/setup/invalidation are ALWAYS read live from the canonical `score_stocks` row; they are never persisted on the entry (would create a second, drifting source) and never user-editable.
- **Auth / per-user scoping / tokens** — single-user local app; the watchlist is global. No `localStorage` token (anti-goal).
- **Alerts/notifications, watchlist groups/tags, CSV export, reordering.**
- **Any change to the existing live endpoints/engines or the immutable snapshot/forward-return tables** — `/api/dashboard|stocks|sectors|themes|runs|system-health`, `/bars`, and `scanner.py`/`scoring.py`/`regime.py`/`sectors.py`/`themes.py`/`setups.py`/`buckets.py`/`forward_testing.py` stay byte-identical so J-01–J-10 cannot regress.
- The nice-to-haves (config-editor view, historical score charts).
- **Runner-script harness fixes** (dedicated browser-qa frontend self-heal; audit-handoff emission) — NOT product/developer scope (see NOTES).

## DEFINITION OF DONE

- [ ] **J-11 passes**: `/watchlist` lets a user add `ANET` with a reason and shows it with date-added, reason, current Leadership/Entry/Risk (A–E + number), setup status, a price-since-added figure, and an invalidation level; after a backend restart the entry is still present.
- [ ] **Restart persistence proven** — authoritatively by a unit/integration test (add via one session → dispose the engine → reopen against the **same on-disk SQLite file** → entry still present), and demonstrated in the browser sweep where the runner can orchestrate a restart.
- [ ] **Single-source guard passes** — the current Leadership/Entry/Risk score+bucket, setup status, and invalidation returned for a watchlisted ticker are **byte-identical** to that ticker's row from `GET /api/stocks` (J-06 extended to the write surface).
- [ ] **Required-still-passing journeys J-01–J-10 remain green** (full 11-journey regression sweep + full-product coherence).
- [ ] No anti-goal violation introduced — especially: no order/position path (grep clean), watchlist never writes a snapshot row, unknown ticker rejected, no new magic number, no secret.
- [ ] Unit tests pass (existing suite + new watchlist tests); frontend `npm run build` typechecks/compiles; app boots and serves `/watchlist` offline against the seed.
- [ ] Coherence is PASS (no duplicate computation / non-canonical source / new-route-without-home).
- [ ] Dev handoff written at `docs/handoffs/goal-i_can_see_the_wealthy_future-iter-7-dev.md`.

## TESTING REQUIREMENTS

- **Browser (this iter must verify):**
  - **J-11 (target)** — open `/watchlist` (empty state) → add `ANET` with reason "ANET — strong leader, watching pullback" → confirm the row shows date-added, the reason, current Leadership/Entry/Risk (A–E + number), setup status, a price-since-added figure, and an invalidation level; then the **restart-persistence** check (entry still present after a backend restart). **Two distinct (md5-distinct) captures required:** (1) entry-present-after-add, (2) entry-still-present-after-restart. Also capture a Remove → row disappears.
  - **Full regression sweep J-01–J-10** — re-confirm each still passes; **hash the evidence PNGs** so per-journey screenshots are not silently shared duplicates (iter-6 lesson). Where multiple journeys live on one page, note it rather than counting a shared shot as independent proof.
- **Unit/integration (code paths that must have tests):**
  - **Restart persistence (the crux):** use a temp **file-backed** SQLite DB (NOT `:memory:`, which would vanish on reopen) — add an entry, dispose/close the engine, recreate the engine against the same path, assert the entry is read back.
  - **Add/Get/Delete roundtrip** via FastAPI `TestClient`.
  - **Single-source equality:** for a watchlisted ticker, the GET-watchlist current scores/bucket/setup/invalidation equal that ticker's `/api/stocks` row exactly (extends the existing list==detail J-06 guard).
  - **price_since_added** reads the canonical price series and is honest (0.00% when entry_close == current close against the frozen seed; NA when no `entry_close`) — never fabricated.
  - **Immutability isolation:** adding/removing a watchlist entry performs no UPDATE/INSERT against any `scanner_runs`/`scanner_results`/`*_scores`/`forward_returns` row.
  - **No-magic-numbers guard** stays green (extend `CALC_FILES` to `api/watchlist.py` if needed; it must contain no scoring/threshold literal).
- **Error cases that must be rejected:**
  - Unknown ticker on POST → `422`/`404` (no fabricated row).
  - Duplicate ticker on POST → no duplicate row (`409` or idempotent reason-update).
  - DELETE of a missing entry → `404`.
  - No price data → `503` (explicit unavailable, not a fabricated entry).

## NOTES

- **This is the goal-completing iteration.** With J-11 passing and J-01–J-10 held green under a full regression sweep + full-product coherence, the subsequent evaluation is positioned to legitimately declare **GOAL_ACHIEVED**. The decomposer does not declare it — the goal-evaluator does.
- **price-since-added against a frozen seed is honestly ~0.00%.** The seed's latest date is `2026-05-28` and an entry added "now" has no post-add bars, so the figure is `0.00%` (entry_close == current close). That is the correct, non-fabricated value and satisfies the journey's "a price-since-added figure renders" acceptance — it is **not** a defect. If a live provider later advances the seed, the figure becomes the true realized change automatically.
- **Single-source is THE risk of this iteration.** The watchlist is the first surface that both *writes* (the entry) and *displays canonical scores*. Per the iter-2 lesson, the new code path MUST read the canonical `score_stocks` row, never recompute or persist-then-drift the scores. Storing only `{ticker, reason, created_at, asof_date_added, entry_close}` and reading everything else live is the way to keep J-06 intact (and is parallel to how `ForwardReturn` stores a captured `entry_close` without storing any score).
- **Order-path fence.** A watchlist superficially resembles a portfolio. Keep it a research save-list: no quantity, no position/cost-basis-as-trade, no P&L, no order/buy/sell/broker field or verb. A grep for an order/execution path must stay empty.
- **Runner-script gaps (route to whoever drives the runner — NOT product/developer scope, and deliberately NOT in the DoD per the iter-5 lesson that spec/DoD text has no effect here):** (1) the dedicated browser-qa has SKIPped on an HTTP-000 frontend flap for **6 consecutive iters** — the durable fix is making browser-qa own/await/self-heal its own `next dev` in `scripts/automation/*.sh`. Fixing it *before* this goal-completing iter would let GOAL_ACHIEVED rest on a clean live browser sweep instead of an evidence-reconcile. (2) `reports/audits/` has not existed for 6 full-depth iters — emit the audit handoff from the runner. Until fixed, the evaluator should reconcile J-11 from on-disk QA evidence PNGs + the unit/API restart-persistence proof + direct source reads, exactly as in iters 1–6.
- **Reference:** evaluator recommendation in `runs/goal-session-i_can_see_the_wealthy_future/iter-6/eval.md`; Watchlist Data-Contract row in `runs/goal-session-i_can_see_the_wealthy_future/state/blueprint.md`.
