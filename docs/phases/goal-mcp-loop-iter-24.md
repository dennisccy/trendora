# Goal Iteration 24 — Fast platform (mechanical backend pass) + storage-footprint card

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** mcp-loop
- **Iteration:** 24
- **Mode:** next
- **Depth:** full
- **Frontend Present:** yes
- **Target journeys:** J-15
- **Required-still-passing journeys:** J-01, J-03, J-04, J-05, J-10, J-12, J-13, J-14
- **Anti-goal reminders (verbatim from docs/goal.md):**
  - A score, ranking, or "edge" MUST NOT be presented as proven/confident unless it is backed by a **passing certified-claim entry** in the evidence ledger (out-of-sample, control-beating). Unbacked values MUST render a "not yet proven" state. *(critical)*
  - **Decision-quality only:** never present return promises, price targets, "buy/sell" signals, or alpha claims; never place or simulate orders. *(critical)*
  - A journey passes ONLY if the **displayed numbers are correct** — they match the engine's computation for the same as-of date — not merely that the page renders. *(critical)*
  - **No overfit edges:** any pattern surfaced as "proven" must have survived the referee (sealed out-of-sample holdout + controls + multiple-testing correction), never in-sample fit alone. *(critical)*
  - **Preserve determinism and no-lookahead:** scoring uses bars ≤ as-of; forward returns use bars > as-of; never introduce lookahead anywhere. *(critical)*
  - No iteration ships if its evidence-derived claims (if any) lack a passing referee verdict from the post-decompose gate. *(critical)*
  - No hard-coded credentials, API keys, or tokens in source files. *(critical)*
  - **Resilience to data-shape and data-scale change:** widening the data basis (new nulls, broader pools, deeper history) must never crash an existing page or exhaust a service's memory — every existing consumer of a widened field is re-validated, the UI degrades gracefully (contained error boundary, honest "—"/NA placeholder, never a blank application-error page), and unbounded whole-table ORM loads are forbidden on the deep basis. *(critical)*

## GOAL

Make Trendora's core pages and APIs measurably fast on the 30-year / 590-symbol basis and commit those latencies as never-regress budgets — landing goal.md's fast-platform **mechanical backend pass** (items B/C/D/G/H) under a strict byte-identity gate, adding the measurement harness (item K), and surfacing the platform's current storage footprint on the Data Manager.

## BACKGROUND

J-14 (the last near-done target) closed cleanly at iter-23; there are no regressions and iter-23 was COHERENCE-PASS, so no consolidation veto applies. The remaining incomplete Must-haves are J-02/J-06/J-07/J-08/J-09 (sanctioned-partial evidence re-certification — gated on a staging winner that clears the canonical Bonferroni divisor-8 bar; per the iter-23 eval + audit no staging winner clears it today, so that path is risky and may honestly find nothing to promote) and J-15/J-16 (fast-platform perf, unbuilt). Per the priority rubric this iteration takes the most tractable unblocked work: **J-15**, which the iter-23 evaluator ranked #1 and which maps to goal.md's pre-registered "mechanical backend pass" (step 2: items B/C/D/G/H) plus the item-K harness. J-15's committed budgets are achievable WITHOUT the risky byte-identity-gated scoring-window change (item F) — that item drives J-16's ≥30% job-time improvement, so **J-16 is deliberately deferred** to keep this iteration to one risky change (rubric rule 5 — never bundle two risky journeys; a joint failure is undiagnosable). Depth is **full** because item C is a data-model change (schema index drop/add + a guarded startup migration), the whole pass is a byte-identity-gated data-path change that needs the audit/ux-regression/closure guards, and it crosses backend+frontend (a new /data storage card). Item A (the /api/data OOM prefill fix) already landed in iter-19, so the backend survives the cold /api/data path this iteration must re-verify.

## IN SCOPE

### Backend
- [ ] **Item B — Tune SQLite (`app/db.py:make_engine`).** Add an `event.listen(engine, "connect")` pragma hook applied **only when the URL is sqlite** (keep it the ONE dialect-specific site), sourcing a new `database.pragmas` config block (no inline literals): `journal_mode=WAL`, `synchronous=NORMAL`, `busy_timeout=30000`, `cache_size=-262144` (256 MB), `mmap_size=1073741824`, `temp_store=MEMORY`; size the pool to the workers (`pool_size`/`max_overflow`, config-keyed). Document the WAL+NORMAL durability trade-off (last commit may be lost on power cut — acceptable for this single-host research app).
- [ ] **Item C — Index hygiene (schema + guarded startup migration; no alembic in this repo).** Remove the duplicate `Index("ix_daily_prices_symbol_date", ...)` (`models.py:86` — the `UniqueConstraint("symbol","date")` at `:85` already creates a unique index) and the redundant `forward_returns` prefix index(es) (`models.py:362` `ix_forward_returns_symbol`/`run_id`, prefixes of the `UNIQUE(run_id,symbol,horizon)` autoindex); `DROP INDEX IF EXISTS` them in a guarded post-`create_db_and_tables` startup step. **ADD** `Index("ix_daily_prices_date", "date")` (`CREATE INDEX IF NOT EXISTS` in the same hook) — `func.max(DailyPrice.date)` (`prices.py`, on ~every request) and the availability `group_by(date)` (`data_manager.py`) currently walk 3.27M rows without it. Verify with `EXPLAIN QUERY PLAN` that `bars_asof` still uses the unique index and `max(date)`/availability use the new one. Dropping a redundant index changes plans, never results.
- [ ] **Item D — Stop deserializing the whole leaderboard to serve one row.** `snapshot_serving:stock_detail_payload` (`:213`) and the watchlist canonical-rows path currently call `stored_stock_rows` (`:156`), which `json.loads`es all ~404 `record_json` blobs to return 1 (or a few) rows. Add a **filtered variant** — query `ScannerResult where(run_id==…, ticker==…)` (or `ticker IN (…)` for the watchlist) and deserialize only those rows. Same serializer, **byte-identical payload shape** (existing `/api/stocks/{ticker}` + watchlist API tests are the gate).
- [ ] **Item G — Make the readiness probe cheap (`readiness.py`).** Column-project the SPY warmup calendar (`select(DailyPrice.date).where(symbol=='SPY')` — date scalars, not ORM rows) and memoize it keyed on `(latest_date, cfg)`; replace the per-date `get_run_for_date` existence loop (`readiness.py:80`) with ONE `select(ScannerRun.asof_date).where(asof_date.in_(cadence_dates))` + a set-diff. Budget `/api/health` ≤ 0.1 s.
- [ ] **Item H — Kill the `/api/data` cold-path N+1 (`data_manager.py`).** Replace `_missing_data_diagnostic` (`:200`)'s one-`DailyPrice.date`-query-per-member (~590) with ONE grouped/windowed query (mirror the bulk `group_by` in the sibling `_per_symbol_coverage` at `:142`) or read from the active bar cache. Byte-identical diagnostic output.
- [ ] **Item K (backend) — DB capacity snapshot.** Add `compute_capacity` to `app.engine.data_manager` (DB file size + row counts for `daily_prices` / `scanner_results` / `forward_returns` — pure DB introspection over stored rows; presentation of stored footprint only, recomputes NO canonical value; serves an honest zero/empty snapshot on a cold DB). Serve it as an **additive `capacity` field** on the EXISTING `GET /api/data` `data_overview` payload (`api/data.py:94`) — no new endpoint. Fix the stale `server.memory_cap_mb` config comment if it still says "~1.3M-row" (real figure ~3.27M rows).
- [ ] **Item K (harness) — `scripts/measure-perf.sh`.** New committed ops script: curl-timed **warm** endpoint latencies (`GET /api/stocks`, `/api/stocks/{ticker}`, `/api/data`, `/api/health`) + one bounded K-date backfill timing via the jobs API + the DB capacity snapshot; appends measured rows to `reports/perf-budgets.md`. Runs against **prod mode** (`start-backend.sh`/`start-frontend.sh` — never `dev.sh`; its `--reload`/`next dev` per-route compile is not product latency). Any new loop over "all symbols"/"all dates" takes its bound/scope from config, never a literal.

### Frontend
- [ ] A small read-only **storage card** on `/data` (Data Manager) rendering the DB capacity snapshot (DB file size + the three row counts) from the additive `GET /api/data` `capacity` field. Honest zero/empty state on a cold DB; presentation of stored values only.

### New user-facing capability
Core pages and APIs load within committed budgets on the deep basis (a faster stock-detail page, a snappy health probe, a cold `/api/data` that completes without OOM), and the user can see the platform's current data-storage footprint (DB size + row counts) on the Data Manager.

### New information displayed
The **DB capacity snapshot** (DB file size; `daily_prices` / `scanner_results` / `forward_returns` row counts) on a `/data` storage card; and the committed before/after latency table in `reports/perf-budgets.md`.

### New user actions
None — the storage card is read-only and `scripts/measure-perf.sh` is an ops/measurement script (not a UI control).

### UI surface changes
One new read-only storage card on the EXISTING `/data` page. No new page, no nav change.

### Product surface delta
The Data Manager gains an honest storage-footprint card; core pages/APIs are measurably faster with byte-identical values; a committed budgets table makes latency a never-regress contract that later data-path iterations must re-assert.

### Blueprint conformance
The `/data` storage card lives under the EXISTING Data Manager home (`/data`) already in the Information Architecture — no new surface, no nav-skeleton change. J-15/J-16 home rows added to the homes table (additive; both under the existing Data Manager / cross-cutting).

### Data-contract additions
ONE new displayed value — the **DB capacity snapshot** (DB file size + row counts for `daily_prices` / `scanner_results` / `forward_returns`): computed once by `app.engine.data_manager:compute_capacity` (pure DB introspection — no canonical value recomputed), served as an additive `capacity` field on the EXISTING `GET /api/data` (`data_overview`) payload, ONE reader (the `/data` storage card). Registered in `blueprint.md`. **No other new value** — every optimized path (item D filtered fetch, items G/H cheaper queries, items B/C pragma/plan changes) re-serves BYTE-IDENTICAL stored values with no new computing module and no new serving endpoint. Never introduce a second computation or endpoint for any value already in the Data Contract.

## OUT OF SCOPE

- **J-16 (data-jobs perf) and item F (window the scoring inputs).** The ≥30% per-date backfill / warmup improvement is driven by the byte-identity-gated scoring-window change (item F) — a distinct risky change; it is its own iteration (goal.md step 4). Bundling it here would be a second risky journey in one diff (rubric rule 5).
- **Item E (lean leaderboard summary DTO) and item J (`record_json` shrink).** Item E sharpens `GET /api/stocks` to ≤ 0.5 s, but J-15's committed `/api/stocks` budget (≤ 1.5 s) is met without it; both are the later payload/storage pass (goal.md step 3/4).
- **Item I (frontend interaction costs — heatmap memo, leaderboard debounce, chart-instance reuse).** Step 3; a distinct frontend surface with no data-contract change; deferred.
- **Any `## Evidence Claim` / any change to either ledger / any evidence re-certification (J-02/J-06/J-07/J-08/J-09).** This iteration does zero evidence work.
- **Any change to displayed numbers.** All optimized paths are byte-identical; if an expectation test must be edited to pass, that is a regression signal — stop and diagnose.
- **Deleting the dead-duplicate dashboard components** (`index-regime-chart.tsx` / `major-indexes-card.tsx`, coherence-WARN). They are dashboard components unrelated to `/data` perf; deleting them here would muddy the byte-identity signal. Defer to a dedicated tidy iteration (iter-23's own rationale).
- Any work beyond goal.md's fast-platform items B/C/D/G/H/K.

## DEFINITION OF DONE

- [ ] `scripts/measure-perf.sh` is committed, runnable against prod mode, and produces warm endpoint latencies + one bounded K-date backfill timing + the DB capacity snapshot, appended to `reports/perf-budgets.md`.
- [ ] `reports/perf-budgets.md` records fresh before/after measurements for: page time-to-interactive of `/stocks`, `/stocks/AAPL` (incl. the Full-history toggle), `/data`, `/evidence`; and warm latency of `GET /api/stocks`, `/api/stocks/{ticker}`, `/api/data`, `/api/health`; plus the cold `/api/data` path.
- [ ] Budgets met (or, if a budget is proven infeasible without a correctness trade-off, the table sets a different value WITH the measurement attached — the table then IS the contract): pages interactive ≤ 3 s warm; `GET /api/stocks` ≤ 1.5 s; `/api/stocks/{ticker}` ≤ 0.3 s; `/api/data` ≤ 1.5 s warm AND its cold path completes ≤ 60 s without OOM under the 6144 MB cap; `/api/health` ≤ 0.1 s.
- [ ] Byte-identity verified for every optimized path: `GET /api/stocks`, `/api/stocks/{ticker}`, `/api/stocks/{ticker}/bars`, and `/api/data` return byte-identical values to the pre-change computation for the same as-of (a filter/cache/plan re-serves stored values, never recomputes). Existing `/api/stocks/{ticker}` + watchlist API tests stay green UNEDITED (item D); `EXPLAIN QUERY PLAN` confirms `bars_asof` uses the unique index and `max(date)`/availability use `ix_daily_prices_date` (item C).
- [ ] The `/data` storage card renders the DB capacity snapshot (file size + three row counts) matching `compute_capacity`; browser-verified.
- [ ] Target journey J-15 passes via browser-qa-agent (canonical lane, live, non-empty md5-distinct evidence dir).
- [ ] Required-still-passing journeys J-01, J-03, J-04, J-05, J-10, J-12, J-13, J-14 remain green (live replay).
- [ ] No anti-goal violation introduced (esp. #3 correct/byte-identical numbers; #5 determinism + no-lookahead; #8 no crash/OOM, no unbounded whole-table ORM load).
- [ ] Targeted unit/integration tests for the changed paths pass; no regressions. (NOT the full ~10 h 30-year suite — targeted tests + a bounded run only.)
- [ ] Dev handoff written at `docs/handoffs/goal-mcp-loop-iter-24-dev.md`.

## TESTING REQUIREMENTS

- **Browser:** J-15 — measure/verify `/stocks`, `/stocks/AAPL` (incl. Full-history toggle), `/data` (incl. the new storage card), `/evidence`: pages render and are interactive within budget, honest initializing/progress state if slow (never a blank/frozen/application-error frame), and the storage card shows the capacity snapshot. Live-replay J-01, J-03, J-04, J-05, J-10, J-12, J-13, J-14.
- **Unit/integration:**
  - Item B — a test asserting the sqlite `connect` hook applies the configured pragmas (`journal_mode=wal`, `synchronous`, `busy_timeout`) and that a non-sqlite URL is unaffected.
  - Item C — the duplicate `ix_daily_prices_symbol_date` and redundant `forward_returns` prefix index(es) are absent after startup, `ix_daily_prices_date` is present, and `EXPLAIN QUERY PLAN` uses the expected indexes for `bars_asof` and `max(date)`.
  - Item D — the ticker-filtered fetch returns a payload byte-identical to the prior full-deserialize path for `stock_detail_payload` and the watchlist path (existing API snapshot tests remain green unedited).
  - Item G — the readiness probe memoizes the SPY calendar and issues ONE grouped run-existence query; the readiness figure is unchanged.
  - Item H — `_missing_data_diagnostic` issues one grouped query and returns a byte-identical diagnostic vs the per-member N+1.
  - Item K — `compute_capacity` reports correct row counts + file size, is additive on `GET /api/data`, recomputes no canonical value, and serves a valid zero snapshot on an empty DB.
- **Error cases:** a cold `/api/data` completes ≤ 60 s without OOM under the 6144 MB cap; `/data` overview + storage card serve gracefully on an empty/cold DB (zero counts, null range, no 500); an invalid `as_of` on `/api/data` still falls back gracefully; the WAL pragma hook applies ONLY for sqlite URLs.

## NOTES

- **Frontend-Present verification hygiene (iter-2/4/13/20 lessons — recurring blanket-SKIP / stale-bundle failure mode).** Before dispatching browser-qa: `rm -rf apps/frontend/.next`; bring up BOTH prod-mode services (backend `:8255`, frontend `:3255`) and confirm HTTP-200 reachability. All measurements + journeys run in prod mode (`start-backend.sh`/`start-frontend.sh`, never `dev.sh`). Do NOT accept a QA/status "ready to ship" over an empty evidence dir or a `CLOSURE-FAIL` — J-15 flips to passing only on a clean canonical browser-qa lane with a non-empty md5-distinct evidence dir.
- **OOM guard (iter-18 addendum).** Keep the backend up for the whole browser lane; the cold `/api/data` path must complete ≤ 60 s without OOM (item A is in place from iter-19). Items G/H must NOT reintroduce a whole-table load; item C's new date index makes the coverage/date scans cheaper. New rule (goal.md item K): any new loop over "all symbols"/"all dates" takes its bound/batch/scope from config.
- **Byte-identity discipline (iter-9 lesson).** The regression proof for these shared-value optimizations is byte-identical canonical outputs + UNEDITED passing default-path tests. If the executor must edit an expectation test to make it pass, that is the regression signal — stop and diagnose, do not "refresh" the golden.
- **Slow-test trap (iter-23 lesson + operator memory).** Do NOT pin the full ~10 h 30-year pytest suite (or any never-completed slow fixture) as a hard DoD gate — target the specific new/affected tests + a bounded run. Clear `/tmp/pytest-of-*` before any test phase (the 30-year fixture exhausts `/tmp` temp every ~2-3 phases).
- **No canonical claim written.** This iteration carries no `## Evidence Claim` (pure performance/correctness — the post-decompose gate passes automatically) and touches neither ledger, so J-02/J-06/J-07/J-08/J-09 remain sanctioned-partial (not regressed) and the canonical Bonferroni divisor stays at 8 (no tightening — the iter-8/10/12/15 footgun is avoided).
- **Blueprint updated additively:** the DB capacity snapshot is registered in the Data Contract and J-15/J-16 home rows added; both are additive edits under the existing `/data` home (no nav-skeleton change, no re-approval).
- Non-blocking carry-forwards (do NOT reopen): capture the literal `test_api_indexes.py` "12 passed" line on an idle box (audit T1); the dead-duplicate dashboard components cleanup (coherence-WARN) in a dedicated tidy iteration.
