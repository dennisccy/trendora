# Goal Iteration 24 — Coverage clarity (J-36), seed-safe data removal (J-39), and the J-35 expand browser capture

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** i_can_see_the_wealthy_future_forever
- **Iteration:** 24
- **Mode:** normal
- **Depth:** full
- **Frontend Present:** yes
- **Target journeys:** J-36, J-39, J-35
- **Required-still-passing journeys:** J-17, J-18, J-33, J-34, J-06, J-07, J-15, J-08, J-01–J-16, J-19–J-21, J-25–J-32
- **Anti-goal reminders (verbatim from `docs/goal.md`):**
  - **Coverage & missing-data are descriptive & honest.** The coverage figures, the per-symbol/per-universe-member table, and the insufficient-for-analysis diagnostic MUST be **read-only metadata derived from the stored bars + config** — they MUST NOT recompute or restate any canonical score, return, bucket, or setup. A universe member with no or thin history MUST be shown as **missing / thin (NA)**, never as a fabricated range, zero-bar-faked-as-present, or filled value; the **history threshold defining "thin/insufficient"** and the trading calendar defining an intra-series gap MUST come from config (`indicators.min_history_bars` and the benchmark-bar calendar) — **no magic number** in coverage/diagnostic code. The **universe-vs-symbols** distinction MUST be surfaced in plain language.
  - **Data removal is seed-safe & consistency-preserving.** Removal MUST target **only user-added bars** (data fetched beyond the committed seed, identified from the committed seed coverage manifest) — the committed seed is **never deletable from the UI**, and a wholly-seed removal MUST be refused with an explicit reason, never a silent partial. A **confirm-preview** MUST enumerate exactly what will be removed (bars + cascaded dependents) before anything is deleted. Deleting bars MUST **cascade-remove the snapshots and forward-returns derived solely from them**; this is a **whole-row deletion of a derived row together with its provenance — NOT an in-place mutation/overwrite of a retained snapshot**. Removal MUST **fabricate nothing** — it only deletes.
  - **Snapshots are immutable.** A persisted `scanner_run` and its result rows MUST never be updated or overwritten after creation; forward returns live in a separate append-only table keyed to the snapshot. *(critical)*
  - **No recompute in the read path.** Read endpoints MUST serve canonical values from the persisted immutable snapshot for the resolved as-of date; they MUST NOT recompute scores/returns/buckets per request. *(extends Single source of truth)*
  - **No magic numbers.** Every scoring weight, threshold, decision-rule cutoff, bucket edge, universe entry, and theme definition MUST come from the config file — no such literal in calculation code.
  - **No fabricated data.** On a data-provider failure the system MUST surface an explicit stale/unavailable state and MUST NOT synthesize prices or scores to force a green journey.
  - **Single source of truth.** Each of the six canonical scores (and the A–E bucket and setup status) MUST be computed exactly once by the scoring/regime engine and read identically by every page. *(critical)*
  - **Risk-Off must gate Actionable.** When the regime is Risk-Off, the scanner MUST mark zero stocks "Actionable" (watchlist-only). *(critical)*
  - **Exactly one date selector.** The frontend MUST NOT maintain a second, independent date state; every date-scoped page reads the single global as-of control. The coverage table adds no date state; the Remove-data date-range inputs are **action parameters, not a viewing-date control**.
  - **Import keys are env-or-session, never persisted** … never echoed back in any response. (Re-confirm held on every error/job surface this iter touches.)

## GOAL

Deliver the two fully-deterministic Data-Manager Must-haves — an honest, plain-language **Coverage** panel with a per-symbol/per-member table (J-36) and a **seed-safe Remove-data** confirm-preview + consistency-preserving cascade (J-39) — and capture the previously-uncaptured end-to-end **Expand-universe** browser flow so J-35 lifts partial → passing.

## BACKGROUND

The prior evaluator (iter-23) returned **CONTINUE** with an explicit **full**-depth recommendation: build the remaining buildable Data-Manager Must-haves smallest/most-deterministic first (J-36 then J-39), and re-capture the J-35 expand flow that was uncaptured at iter-23 for an environmental reason (the frontend dev server was down at dispatch — curl :3835 → HTTP 000, MEMORY `browser-qa-dead-shell-next-cache` / `dev-server-cleanup-by-port`). J-36 and J-39 are fully deterministic (no provider needed) and `docs/goal.md` expects them to go green offline. J-39 is the **session's first destructive data operation**, so its cascade boundary (delete only user-added rows + derived dependents, never touch a committed-seed bar, never overwrite a retained snapshot) is the principal review/audit focus — this justifies **full** depth even though the source work is largely already present in the working tree. J-37 (missing-data diagnostic + pull-missing) and J-38 (unified Unfinished-imports Retry/Remove) are **deferred to iter-25** (they reuse the J-34 chunked/resumable engine and carry data-dependent pull/retry semantics).

Applicable lessons (episodic memory):
- **iter-22** (`test_db` expected-tables): any iter adding a new `table=True` SQLModel must update `tests/test_db.py::test_create_all_produces_expected_tables`. J-39 adds no new table, but verify the suite is green (no stale schema-snapshot RED) before the QA gate concludes FAIL.
- **iter-15 / iter-23** (`browser-qa-dead-shell-next-cache`): bring the frontend up cleanly BEFORE driving any UI — stop strays **by port** (never broad pkill, MEMORY `dev-server-cleanup-by-port`), `rm -rf apps/frontend/.next`, restart `next dev`, confirm `GET /_next/static/chunks/main-app.js` → 200 and the health badge clears; do NOT run a prod `npm run build` against the live dev `.next`. A dead-shell / down-server browser SKIP is environmental, never a code FAIL.
- **iter-4 / iter-15 / iter-23** (multi-step capture): grant J-35 `passing` only when the **defining end-to-end flow** (run an injected-provider expand → passers + omitted-with-reason + grown universe-count) is actually captured. A render of surfaces in isolation is `partial`, not `passing`.
- **MEMORY `j39-live-host-has-user-added-nvda-bars`**: the live host is NOT user-bar-free (NVDA has 6 bars beyond seed; `trendora.db` is gitignored, no restore). To smoke-test J-39 live, use the **preview** endpoint (deletes nothing) — never run the destructive endpoint against a real symbol on the live host.
- **MEMORY `httpx-error-leaks-url-query-key`**: this iter touches no key-carrying provider path, but the J-39 removal error surface must carry no secret (re-confirm the iter-21/22 scrub holds on any new error string surfaced on `/data`).

## IN SCOPE

### Backend
- [ ] **J-36** — `app.engine.data_manager:compute_coverage` (the EXISTING single coverage producer, extended — no parallel module) returns, alongside the existing aggregate figures, a **per-symbol / per-universe-member table**: one row per stored `DailyPrice.symbol` AND one row per `config.universe.symbols` member, each with `in_universe` · `has_data` · first/last bar date · `bar_count` · `thin` · `missing`. `thin = (0 < bar_count < indicators.min_history_bars)` with the threshold **read from config** (no magic number); a member with no bars ⇒ `has_data=false` / `missing=true` / NA range (never a fabricated range or a zero-bar row faked as present). Recompute NO score/return/bucket/setup.
- [ ] **J-36** — the `coverage` payload also carries the plain-language **definitions** for every aggregate figure and the **universe-vs-symbols** + **backfill-gap** distinctions (served as data so the frontend re-formats, not hardcodes). Internal-consistency invariant: the table's distinct-symbol (has-data) row count == the `symbol_count` aggregate AND the in-universe row count == `universe_count` (same source — the panel can never present two drifting truths). Serve gracefully on an empty dataset (null range / zero counts / empty table) rather than erroring.
- [ ] **J-39** — `app.engine.data_manager`: a **seed-vs-user-added classifier** reading the committed seed manifest `apps/backend/data/seed/meta.json` (per-symbol `first`/`last`/`bars` windows) + a scope scan over stored `daily_prices`. A `(symbol, date)` inside a seed window is **protected** (not removable); a wholly-seed scope is **refused with an explicit reason**.
- [ ] **J-39** — a **read-only confirm-preview** (`POST /api/data/remove/preview`) that returns exactly what WOULD be removed — removable user-added bar count + range, the not-removable committed-seed breakdown with the reason "committed seed", and the cascade of dependent `scanner_runs`/`scanner_results`/`sector_scores`/`theme_scores`/`forward_returns` rows derived **solely** from the removed bars — and **deletes nothing**.
- [ ] **J-39** — a **destructive removal** (`POST /api/data/remove`) that whole-row-deletes ONLY user-added `DailyPrice` rows in scope and cascade-deletes ONLY the derived snapshot/forward-return rows that depended SOLELY on them (a retained snapshot that still has all its bars is UNTOUCHED — never overwritten in place); records the removal on the append-only `DataProviderRun` audit log; fabricates nothing. Reject an inverted range, an unknown symbol, an empty scope, and a wholly-seed scope (400).

### Frontend
- [ ] **J-36** — a **Coverage** panel on `/data`: each aggregate figure shown next to its one-line plain-language definition, the universe-vs-symbols distinction in prose, and a sortable/filterable **per-symbol coverage table** (sort/filter **UI-only** — the backend returns the canonical rows once; the page computes no coverage figure). A "universe members only" filter confirms every member either has data or is flagged missing/thin. `data-testid` hooks for the universe count, symbol count, and per-symbol table.
- [ ] **J-39** — a **Remove data** control on `/data`: choose scope (by symbol, by date range, or both) → a **confirm-preview** rendering the removable count + range, the protected committed-seed breakdown, and the dependent cascade → an explicit confirm that calls the destructive endpoint, then refreshes coverage + the per-symbol table + the global as-of switcher (removed-only dates drop out). A seed-only / seed-covered scope shows the refusal with reason; the seed is never deletable from the UI.

### New user-facing capability
The operator can now (a) **understand exactly what data is and isn't covered** — read plain-language definitions, see the universe-vs-symbols distinction, and inspect per-symbol/per-member coverage with thin/missing honesty; and (b) **safely remove user-added imported data** — preview precisely which bars and which derived snapshots/forward-returns would be deleted before confirming, with the committed seed protected and refused.

### New information displayed
- A coverage **definitions** block (every figure labelled) + the universe-vs-symbols + backfill-gap explanations.
- A **per-symbol / per-universe-member table**: in-universe · has-data · date range · bar count · thin/missing flag.
- A removal **confirm-preview**: removable bars (count + range), protected committed-seed breakdown, and the cascade of dependent rows.

### New user actions
- Sort / filter the per-symbol coverage table (UI-only); "universe members only" filter.
- Open Remove data → pick scope → read preview → confirm removal (or cancel).

### UI surface changes
All additive on the **existing `/data` (Data Manager)** page — a Coverage panel (extended) and a Remove-data panel. No new page, route, or nav entry.

### Product surface delta
The Data Manager graduates from a fetch/backfill/expand console into a full data-stewardship surface: the operator sees honest coverage and can curate the dataset (seed-safe removal) — closing the "understand + curate" half of capability #20.

### Blueprint conformance
All three targets home on the **existing approved `/data` (Data Manager)** section of the Information Architecture (sidebar entry `Data Manager → /data`). No nav-skeleton change; **no `blueprint.reapproval-requested` marker** is written. The iter-24 nav-skeleton update note already records this (`blueprint.md` "Nav-skeleton update (iter-24)").

### Data-contract additions
Both new values are **already registered** in `blueprint.md`'s Data Contract (additive rows, registered when the working-tree source was drafted against the blueprint) — no further blueprint edit is required this iter:
- **Per-symbol / per-universe-member coverage table + coverage definitions (J-36)** → computed once by `app.engine.data_manager:compute_coverage` (the EXISTING single producer, extended) → served on the EXISTING `GET /api/data` `coverage` payload. NOT a second universe computation (membership read from the SAME `config.universe.symbols` that `/api/methodology` resolved-size + `/api/data` `universe_count` already serve).
- **Data-removal preview + cascade action (J-39)** → computed once by `app.engine.data_manager` from `apps/backend/data/seed/meta.json` + a stored-data scope scan → read-only preview endpoint (`POST /api/data/remove/preview`) + destructive removal endpoint (`POST /api/data/remove`); recorded on the append-only `DataProviderRun`. Reads the SAME canonical universe membership; the cascade reaches no scoring/scanner code (deletes rows only).

No NEW displayed value duplicates an existing Data-Contract value: `universe_count` / `symbol_count` keep their single canonical source; the removal cascade computes no score/return/bucket.

## OUT OF SCOPE

- **J-37** (missing-data diagnostic + one-click pull-missing) — deferred to iter-25 (reuses the J-34 chunked/resumable engine; partly data-dependent/non-halting). Do NOT build the missing-data diagnostic or any "pull missing" action here.
- **J-38** (unified Unfinished-imports — Resume/Retry/Remove with state explanation) — deferred to iter-25 (builds on the J-34 ImportCheckpoint surface). The existing iter-22 Resumable-imports panel stays unchanged; do NOT generalize it to Retry/Remove here.
- **J-22 / J-23 / J-24** — externally Yahoo-429 data-walled, **non-halting / non-vetoing**. Do NOT autonomously re-probe any of them; do NOT run a live expand against a real provider on the live host.
- Any change to scoring / scanner / regime / patterns / buckets / forward-testing / research / snapshot-serving / the `/stocks`·`/backtest`·`/research` pages or the as-of provider — out of scope; touching them risks the carried journeys and a DB regen (none is needed).
- No new SQLModel `table=True` (and therefore no `tests/test_db.py` expected-tables change expected).

## DEFINITION OF DONE

- [ ] **J-36** passes via browser-qa-agent: the Coverage panel renders definitions + the universe-vs-symbols distinction + a per-symbol/per-member table (in-universe · has-data · range · count · thin/missing); the universe-members-only filter shows every member has-data-or-flagged; the table's distinct-symbol count == `symbol_count` and in-universe count == `universe_count` (no drift).
- [ ] **J-39** passes via browser-qa-agent: open Remove data → preview shows removable bars + range + protected committed-seed breakdown + the dependent cascade → confirm executes (proven against a fixture with user-added bars; on the committed-seed-only live host use the **preview** path only) → a seed-only/seed-covered scope is refused with reason; the committed seed is never deletable.
- [ ] **J-35** lifts partial → passing: the injected-provider expand happy-path is captured end-to-end on a clean hydrated build — select Expand → start over a market-cap-capable injected source → chunk x/N progress → completion → `expand-screen-result` passers badge + omitted-with-reason list → grown `universe-count` (and `/methodology` size matches). Machinery is integration-proven; only the browser capture was missing.
- [ ] Required-still-passing journeys remain green — especially **J-18** (exactly one date selector: the coverage table adds no date state; the Remove-data range inputs are action parameters), **J-06/J-07** (scoring/snapshot path untouched, no DB regen → byte-identical), **J-17/J-33/J-34** (existing fetch/backfill/expand/resume flows unchanged), **J-08** (immutable scanner-run history — the cascade is whole-row delete of derived rows, never an in-place snapshot overwrite).
- [ ] No anti-goal violation introduced — especially *Data removal is seed-safe & consistency-preserving*, *Snapshots are immutable* (whole-row delete, never in-place overwrite), *Coverage & missing-data are descriptive & honest*, *No magic numbers*, *No fabricated data*.
- [ ] Unit + integration tests pass; full backend suite green (no stale schema-snapshot RED); no regressions.
- [ ] Dev handoff written at `docs/handoffs/goal-i_can_see_the_wealthy_future_forever-iter-24-dev.md`.

## TESTING REQUIREMENTS

- **Browser (by ID):** J-36 (coverage definitions + per-symbol table + universe-members-only filter + the symbol-count/universe-count consistency), J-39 (Remove-data scope → confirm-preview → protected-seed refusal; destructive confirm only against a user-added-bar fixture, preview-only on the live host), J-35 (injected-provider expand end-to-end to grown universe-count), and a J-18 re-confirm (exactly one date `<select>` per page on `/data`; coverage + remove controls add no date state).
- **Unit/integration:**
  - J-36 coverage: per-symbol exact values; the consistency invariant (distinct-symbol rows == `symbol_count`, in-universe rows == `universe_count`); the thin threshold sourced from `indicators.min_history_bars` (config, not a literal); empty-dataset graceful serve (members-only rows, null range).
  - J-39 removal: preview deletes nothing; seed-only scope (and seed-only symbol) refused; cascade deletes ONLY rows derived SOLELY from removed bars (a retained snapshot keeps all its bars); the removal records an audit run; **no recompute** is invoked during removal (assert the scoring/scanner functions are not called); whole-row delete, never an in-place snapshot overwrite.
  - API error cases: remove preview/removal reject inverted range, unknown symbol, empty scope, wholly-seed scope (400); the removal error surface carries no secret.
- **Error cases to reject:** inverted date range; unknown symbol; empty removal scope; a wholly-committed-seed removal scope (refused, nothing deleted); coverage on an empty DB must serve null/zero/empty, never error or fabricate.

## NOTES

- **Working-tree state:** the J-36 and J-39 source (engine `compute_coverage` + `_per_symbol_coverage`, `preview_removal`, `remove_data`; `api/data.py` `/data/remove/preview` + `/data/remove`; `data/page.tsx` `CoveragePanel` / `PerSymbolCoverageTable` / `RemoveDataPanel`; and their tests) is already present in the uncommitted working tree. Treat iter-24 as delivering + verifying these to their DoD — the developer reconciles/completes any gaps, the reviewer/auditor scrutinize the J-39 cascade boundary, and the browser-qa-agent captures the defining flows. The evaluator (not the decomposer) records pass/fail.
- **Full depth justified** despite the source largely existing: J-39 is the session's first **destructive** data operation crossing backend + a destructive API + frontend, with an immutability-adjacent cascade boundary that warrants the full 11-step pipeline (review + post-QA audit), and the prior evaluator explicitly recommended full.
- **Recurring process facts** (carry, do not re-discover): full-depth iters in this session typically produce no `-audit.md` handoff and write `status.json` at the **phase-namespace** path `runs/goal-i_can_see_the_wealthy_future_forever-iter-24/status.json` (NOT under `runs/goal-session-.../iter-24/`, which holds only `coherence.md` + snapshot-sha). De-dup browser evidence by sha256. The full backend suite is ~14 min — run it once at the QA gate; do not launch two pytest invocations concurrently.
- **GOAL_ACHIEVED is NOT reachable this iter** — J-37 and J-38 remain unbuilt buildable Must-haves (deferred to iter-25). Do NOT declare completion on these import-journey landings (the iter-20 re-scope trap). After J-35 captures green and J-36/J-39 land green offline this iter, only J-37 + J-38 (iter-25) remain on the buildable set, with J-22/J-23/J-24/J-35 live-fetch outcomes recorded honestly as NA / non-halting.
