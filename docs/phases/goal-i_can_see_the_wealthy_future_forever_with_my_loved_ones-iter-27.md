# Goal Iteration 27 — Universe-rebuild + coverage diagnostic (J-85) and max-drawdown columns everywhere (J-86)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** i_can_see_the_wealthy_future_forever_with_my_loved_ones
- **Iteration:** 27
- **Mode:** next
- **Depth:** full
- **Frontend Present:** yes
- **Target journeys:** J-85, J-86
- **Required-still-passing journeys:** J-06, J-08, J-05, J-09, J-21, J-75, J-81, J-29, J-63, J-77, J-82, J-17, J-33, J-34, J-35, J-36, J-37, J-38, J-39, J-40, J-41, J-46, J-53, J-59, J-60, J-66, J-67, J-68, J-18
- **Anti-goal reminders:**
  - **No lookahead.** Scoring for a snapshot dated D MUST use only price bars with date ≤ D; forward returns MUST use only bars with date > D. The walk-forward MUST be unit-tested to prove no future bar influences an as-of score. *(critical)*
  - **Snapshots are immutable.** A persisted `scanner_run` and its result rows MUST never be updated or overwritten after creation; forward returns live in a separate append-only table keyed to the snapshot. A **wholesale regenerate-from-scratch of the entire snapshot set** (e.g. after a universe expansion — J-85) IS permitted as a deterministic, operator-triggered, confirm-gated **create-once rebuild** — every snapshot is cleared then recomputed reproducibly with strict no-lookahead — but an **existing snapshot MUST never be UPDATED or overwritten in place**, and the rebuild changes no canonical formula (only the universe membership it scans over). *(critical)*
  - **Single source of truth.** Each canonical score (and bucket and setup status) MUST be computed exactly once and read identically by every page; the API and frontend MUST NOT recompute them. *(critical)*
  - **No recompute in the read path.** Read endpoints MUST serve canonical values from the persisted immutable snapshot for the resolved as-of date; they MUST NOT recompute scores/returns/buckets per request. *(critical)*
  - **No fabricated data.** On a data-provider failure the system MUST surface an explicit stale/unavailable state and MUST NOT synthesize prices or scores to force a green journey. The committed PRICE seed is never deletable.
  - **Honest forward-test for partial windows.** Horizons or cohorts lacking enough samples MUST show NA/partial and the sample size — never fabricate or extrapolate a return (or a max-drawdown) to fill a gap. *(extends No fabricated data)*
  - **No magic numbers.** Every weight/threshold/cutoff/edge/universe/theme/horizon MUST come from config — no such literal in calculation code (the horizon set comes from `config.walk_forward.horizons`; no hardcoded `[1, 5, 10, 20, 60]`).

## GOAL

After expanding the universe, the operator can confirm-gate a from-scratch snapshot rebuild that makes the new members appear in every read surface (with an honest "N members absent from the latest snapshot" diagnostic), and every forward-return column on `/stocks`, `/themes`, `/sectors`, Stock Detail, Backtest, and Research now sits beside a paired max-drawdown read from the same stored data.

## BACKGROUND

J-85 and J-86 are the last two buildable Must-haves in `docs/goal.md` (commit e06b7a8, lines 2163/2172); both are explicitly **NOT data-dependent** (goal.md:2182-2185) and verifiable offline against the committed seed — neither may be recorded blocked-NA. The iter-26 evaluator (`CONTINUE`, full) recommended exactly this sequence: "Run J-85 at FULL depth … Then J-86 … After J-85/J-86 land green with the full suite GREEN, the next evaluation is a GOAL_ACHIEVED candidate." Both touch the backend snapshot/forward-returns layer and require the full ~862-test pytest gate, so depth is **full** (the prior verdict was CONTINUE at full depth; not ESCALATE). They are coupled: J-85's rebuild is the operation that (re)computes forward returns and thus repopulates J-86's new stored field, so building them together is coherent. After both pass green with a GREEN full suite, zero regressions, and COHERENCE-PASS, J-22/J-23/J-24 remain honestly blocked-NA (non-vetoing) and GOAL_ACHIEVED becomes the evaluator's call.

Coherence was COHERENCE-PASS at iter-26 — this is NOT a consolidation pass; new scope is permitted.

## IN SCOPE

### Backend

**J-85 — confirm-gated regenerate-from-scratch snapshot rebuild + coverage diagnostic**
- [ ] Add a NEW `kind="rebuild"` background job to the existing import-job runner (`apps/backend/app/engine/data_manager.py`) that REGENERATES-FROM-SCRATCH the snapshot layer for the current resolved universe: CLEAR the scanner snapshot set (`scanner_runs` / `scanner_results` / `*_scores` / `forward_returns`) then CREATE-ONCE recompute every covered trading date over `config.universe.symbols`, reusing the EXISTING J-53 parallel multi-date backfill + create-once `persist_run_payload` + `backfill_run_forward_returns` path and the J-66 fine-grained progress machinery. NEVER an in-place UPDATE/overwrite of a live snapshot row (wholesale rebuild only — *Snapshots immutable*). The committed PRICE seed (`bars` table / `apps/backend/data/seed/`) is NEVER deleted. Strict no-lookahead preserved (as-of-D uses bars ≤ D; forward returns use bars > D). Changes NO canonical formula — only the membership scanned over.
- [ ] Expose the rebuild via the EXISTING `POST /api/data/jobs` contract (a new `kind`), confirm-gated by the operator; record it in the EXISTING run-history (J-60) and surface its progress through the EXISTING J-66 progress surface — NO new endpoint, NO new stored column, NO second compute path.
- [ ] ADDITIVELY extend `data_manager:compute_coverage` to derive a read-only diagnostic: the count of resolved-universe members (`config.universe.symbols`) ABSENT from the latest scanner snapshot's scored set — a descriptive derivation over stored bars + the resolved universe (no canonical value recomputed). Serve it on the SAME `GET /api/data` `coverage` block (no new endpoint). 0 absent → no diagnostic.

**J-86 — max-drawdown stored once, surfaced everywhere**
- [ ] Add a NEW nullable `max_drawdown` column to the append-only `forward_returns` table (`apps/backend/app/models.py` `ForwardReturn`, `Optional[float] = Field(default=None)`), computed ONCE per `(run, symbol, horizon)` in the SAME `_insert_run_forward_returns` INSERT path (`forward_testing.py`) beside `realized_return`/`mae`/`mfe`, via a pure helper sharing the EXACT no-lookahead NA gate `forward_return`/`forward_excursions` use (a `max_drawdown` exists iff `realized_return` does — `< horizon` post-bars → NULL). Definition: `MDD = min over j of ( low_j / max(entry_close, high_1…high_j) − 1 )` over the FIRST `horizon` post-snapshot bars (date > D), ≤ 0, running peak seeded at the as-of-D close. Horizons from `config.walk_forward.horizons` (no hardcoded list).
- [ ] Register the new column in `apps/backend/app/db.py` `_ADDITIVE_COLUMNS` (`ALTER TABLE forward_returns ADD COLUMN max_drawdown <type>`, nullable) so an existing live DB gains it in place (the iter-12 `_ADDITIVE_COLUMNS` lesson). `test_db.py` SNAPSHOT_TABLES guard is unchanged since NO table is added; verify the existing `test_every_model_column_on_existing_table_is_covered_by_additive_registry` guard passes for `max_drawdown`.
- [ ] Surface five PAIRED max-drawdown columns/values, read VERBATIM from the stored `forward_returns.max_drawdown` (NO recompute in the read path), on: `GET /api/stocks` + `GET /api/stocks/{ticker}` rows (via `snapshot_serving:_forward_returns_for_row`, mirroring the J-75 `realized_return` pattern); and `GET /api/themes` + `GET /api/sectors` rows via the SAME `forward_testing:_leadership_returns` builder Backtest uses (theme = equal-weight member-basket drawdown; sector/industry = the ETF's own drawdown) — IDENTICAL to Backtest for the same date+horizon (J-06).
- [ ] Add an AGGREGATE mean-max-drawdown beside each return stat on the Backtest evidence aggregates (`GET /api/backtest`) and on the Research event-study + Regime×Setup×Pattern tables (`GET /api/research/*`), with the SAME `n` / min-sample / NA discipline the return aggregates use. Derived read-only over the stored values — recomputes no return/excursion.
- [ ] Update the `apps/backend/tests/test_api_engine.py` byte-equality guards (`test_api_stocks_equals_engine_output`, `test_api_themes_equals_engine_output`, `test_api_sectors_equals_engine_output`) for the additive `max_drawdown` served field IN THIS SAME ITERATION — strip ONLY the additive key before the canonical byte-equality, then separately assert the field + configured horizons exist (the recurring iter-20/23/24 lesson — a correct additive field MUST NOT leave the full suite red).

### Frontend (if applicable)
- [ ] `/data` (`apps/frontend/app/data/page.tsx` + components): render the J-85 coverage diagnostic banner ("N universe members absent from the latest snapshot — rebuild to include them"; no banner when N=0) and a **confirm-gated** "Rebuild snapshots for current universe" action that POSTs the `kind="rebuild"` job and shows its progress through the existing job-card/Unfinished-imports surfaces (J-66). The confirm modal must have a persistently visible Confirm button (the J-69 modal pattern). Dates remain job/action parameters — never a second global date control (J-18).
- [ ] `/stocks` (`apps/frontend/app/stocks/page.tsx`), Stock Detail (`apps/frontend/app/stocks/[ticker]/page.tsx`), `/themes`, `/sectors`: render five paired max-drawdown columns beside the existing forward-return columns, colour-graded by magnitude (≤ 0), client-side sortable under the J-48 view-transform contract (re-order only; recompute/refetch nothing), NA wherever the return is NA. Reuse/extend the shared `apps/frontend/components/forward-return.tsx` cell helper rather than authoring a second formatter.
- [ ] Backtest + Research tables: display the aggregate mean-MDD beside each return stat (read from the served aggregate; no client recompute).

### New user-facing capability
The operator can trigger a confirm-gated full snapshot rebuild so newly-expanded universe members appear in every read surface; and every forward-return figure is now paired with a max-drawdown read from the same stored data.

### New information displayed
A "/data" coverage diagnostic ("N members absent from the latest snapshot"); five max-drawdown columns on `/stocks`/`/themes`/`/sectors` and the Stock-Detail panel; aggregate mean-MDD on Backtest and Research tables.

### New user actions
A confirm-gated "Rebuild snapshots for current universe" button on `/data`; sortable max-drawdown column headers (J-48).

### UI surface changes
`/data` (diagnostic banner + rebuild action + its progress card); `/stocks`, `/stocks/[ticker]`, `/themes`, `/sectors` (paired MDD columns); `/backtest`, `/research` (aggregate mean-MDD cells).

### Product surface delta
The product now closes the universe-expansion loop (expand → diagnostic → confirm-gated rebuild → new members visible everywhere) and adds a downside-risk read (max-drawdown) beside every forward-return figure, all single-sourced and no-lookahead.

### Blueprint conformance
All work lands on EXISTING Information-Architecture homes — `/data` (Data Manager) for J-85; `/stocks` + Stock Detail + `/themes` + `/sectors` + Backtest + Research for J-86. NO new top-level nav section, NO new page. The nav skeleton is unchanged (additive `[TARGET iter-27]` annotations only) — no re-approval required.

### Data-contract additions
- **Max-drawdown per (run, symbol, horizon)** (J-86): computing module = `forward_testing` INSERT path (`_insert_run_forward_returns`, a new pure MDD helper, bars > D); stored once on the NEW nullable `forward_returns.max_drawdown` column; served VERBATIM on `GET /api/stocks`, `GET /api/stocks/{ticker}`, `GET /api/themes`, `GET /api/sectors` (via `_leadership_returns`), and as an aggregate on `GET /api/backtest` + `GET /api/research/*`. Registered in `blueprint.md` (new Data-Contract row + IA annotations) this iteration.
- **Universe-vs-latest-snapshot coverage diagnostic** (J-85): computing module = `data_manager:compute_coverage` (the EXISTING single coverage producer, additively); served on the SAME `GET /api/data` `coverage` block (no new endpoint). Registered in `blueprint.md` (Coverage row annotation) this iteration.
- No NEW computation or endpoint is introduced for any value already in the Data Contract — `realized_return`, `_leadership_returns`, the run-history (J-60), and the progress surface (J-66) are all read/reused from their registered canonical sources.

## OUT OF SCOPE

- Re-committing the regenerated snapshots into the optional Capability-34 snapshot seed (a deterministic-script step — goal.md J-85 note).
- Any change to the J-84 Yahoo cookie+crumb expand auth path (built/passing iter-26) beyond consuming its members.
- A real successful Yahoo ≥500-member screen (J-22) — data-walled, non-halting; not required for J-85/J-86.
- Any new canonical score/return formula; any in-place UPDATE of a snapshot row; any second global date control.
- J-22/J-23/J-24 (data-walled, non-vetoing).

## DEFINITION OF DONE

- [ ] Target journeys J-85, J-86 pass via browser-qa-agent (live `/data` rebuild + diagnostic; live MDD columns on `/stocks`/`/themes`/`/sectors`/detail + aggregate MDD on Backtest/Research).
- [ ] Required-still-passing journeys remain green (esp. J-06 single-source, J-08 immutability, J-75/J-81 forward-return columns unchanged, J-18 one date control).
- [ ] No anti-goal violation introduced (no in-place snapshot UPDATE; no read-path recompute; no fabricated MDD; no hardcoded horizon list; price seed never deleted; no magic-number float literal in CALC_FILES).
- [ ] FULL backend pytest suite GREEN (0 failed, EXIT_CODE=0) — the standing GOAL_ACHIEVED gate. Hand it to the pump nohup-async; gate the evaluator on the FLUSHED `0 failed` line, NEVER on the in-flight stream (iter-11 lesson).
- [ ] `tsc --noEmit` EXIT 0 (the frontend gate — ESLint is not installed here, iter-1 lesson).
- [ ] Dev handoff written at `docs/handoffs/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-27-dev.md`.

## TESTING REQUIREMENTS

- **Browser (by ID):**
  - J-85: on `/data`, the coverage diagnostic banner renders when members are absent (with the committed seed, exercise it by reading the served `coverage` absent-count; if 0 absent, source-corroborate the banner branch + assert the rebuild action and its confirm-gated modal exist and POST `kind="rebuild"`); trigger the rebuild, confirm live J-66 progress, and after completion the snapshot set is regenerated (run-history shows the rebuild record; `/stocks` still serves its rows). Verify the committed price seed is intact post-rebuild.
  - J-86: at a historical as-of D with post-D seed bars, `/stocks` shows five MDD columns beside the forward-return columns (≤ 0, colour-graded, sortable); the Stock-Detail panel shows the same five for that ticker (J-06 identity); `/themes` + `/sectors` show paired MDD columns matching Backtest for the same date+horizon; Backtest + Research tables show aggregate mean-MDD; at/near latest every MDD is NA (never fabricated).
- **Unit/integration:**
  - J-85: a test that drives the REAL rebuild orchestration over the committed seed and asserts (a) it CLEARS then CREATE-ONCE recomputes (no in-place UPDATE — assert via row identity/timestamps or a create-once guard), (b) determinism (a fresh recompute is byte-identical to itself — reuse the existing scanner/forward-test equality suites), (c) the price `bars`/seed table is untouched, (d) strict no-lookahead holds; plus a `compute_coverage` test for the absent-member count (correct N; 0 when full).
  - J-86: an MDD-math test (running-peak, ≤ 0, the no-lookahead tail-invariance the way `forward_return`/`forward_excursions` are tested); a test that `forward_returns.max_drawdown` is NULL exactly when `realized_return` is absent (same NA gate); the `db.py` `_ADDITIVE_COLUMNS` registry guard for `max_drawdown`; J-06 byte-identity of the served MDD to Backtest's `_leadership_returns` for themes/sectors; and the updated `test_api_*_equals_engine_output` guards (strip the additive `max_drawdown` key, assert config horizons) so the full suite stays GREEN.
- **Error cases:** the rebuild action MUST be confirm-gated (no destructive surprise); horizons with `< horizon` post-bars MUST yield NULL MDD (no fabricated 0); a config without `walk_forward.horizons` MUST be rejected (no hardcoded fallback list); the rebuild MUST refuse to delete the committed price seed.

## NOTES

- **Applied lessons (episodic memory):**
  - iter-12 / iter-20: a NEW column on an EXISTING table (`forward_returns.max_drawdown`) MUST be registered in `db.py` `_ADDITIVE_COLUMNS` (else live-DB reads 500 while fresh-DB tests stay green). Adding NO new `table=True` model means `test_db.py`'s expected-tables set is unchanged — but exercise a real (non-fresh) DB read of `/api/stocks` after the migration.
  - iter-20 / iter-23 / iter-24 (the recurring "correct additive feature trips a pre-existing blanket guard" full-suite-red): the additive `max_drawdown` served key WILL break `test_api_{stocks,themes,sectors}_equals_engine_output` byte-equality — update those guards (strip-the-additive-key + separately assert horizons) IN THIS ITERATION so the suite never goes red afterward. Also: any throwaway float sentinel in an engine CALC_FILE trips `test_no_magic_numbers.py` (the lone ever-recorded violation, iter-20) — source/structure any MDD constant, no inline `0.0`.
  - iter-2 / iter-11: the full ~862-test suite (~50-60 min) does NOT survive a dev-turn background run — hand it to the pump nohup-async and gate on the flushed `0 failed` line; NEVER block the evaluator dispatch on the in-flight suite (iter-11 aborted there).
  - iter-26: read `reports/phase-<iter>-ui-test-results.md` AND the browser-qa-agent report directly — a QA "deferred" note can hide live evidence the browser-qa-agent actually captured. Any `apps/backend/data/seed/` diff: verify direction-toward-honesty via coherence before flagging fabrication.
  - iter-3/7/10/13/15/18 (evidence hygiene): md5sum the evidence dir FIRST; the `/data` heatmap and below-the-fold surfaces degrade to blank/wrong-frame captures — scroll the target into view, capture full-viewport, and VIEW the pixels; corroborate any blank capture via the live backend + targeted tests. The new MDD columns sit to the RIGHT of the forward-return columns — capture wide/scrolled.
  - iter-16: J-85's rebuild edits the snapshot/immutability core and J-86 edits the no-lookahead forward-returns INSERT — the decisive checks are static (no in-place `UPDATE` of a snapshot row; the MDD helper shares the `bars_after` window and NA gate) plus the determinism/no-lookahead suites, not only a screenshot.
- These are the last two buildable Must-haves; on a GREEN full suite + COHERENCE-PASS + zero regression, the next evaluation is a GOAL_ACHIEVED candidate (J-22/J-23/J-24 stay honestly blocked-NA, non-vetoing per goal.md:2220-2235).
- Blueprint already updated this iteration: new "Max-drawdown per (run, symbol, horizon)" Data-Contract row + J-85 coverage-diagnostic + rebuild-job annotations + IA `[TARGET iter-27]` tags (additive only — no nav-skeleton change, no re-approval).
